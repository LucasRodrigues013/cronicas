"""Private-only GitHub story archiver. No narrative bytes can reach a public repo.

The GitHub REST adapter authenticates using a fine-grained token provided by an
external trusted runtime. NEVER place the token in files, logs or prompts.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .ledger import ConflictError, GateError, digest


class GitHubREST:
    def __init__(self, repo: str, branch: str = 'story-archive', token: str | None = None):
        if '/' not in repo or any(not x for x in repo.split('/')):
            raise ValueError('Repository must be OWNER/NAME')
        if not branch or branch == 'main':
            raise ValueError('Dedicated archive branch required')
        self.repo, self.branch = repo, branch
        self._token = token or os.environ.get('WORLDROOT_GITHUB_TOKEN')
        if not self._token:
            raise GateError('WORLDROOT_GITHUB_TOKEN not configured')

    def _request(self, verb: str, suffix: str, payload: dict | None = None):
        url = f'https://api.github.com/repos/{self.repo}{suffix}'
        data = json.dumps(payload).encode() if payload is not None else None
        headers = {'Accept':'application/vnd.github+json',
                   'X-GitHub-Api-Version':'2022-11-28',
                   'Authorization':'Bearer '+self._token}
        if data is not None: headers['Content-Type'] = 'application/json'
        req = Request(url, data=data, headers=headers, method=verb)
        try:
            with urlopen(req, timeout=40) as response:
                raw = response.read()
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            if exc.code == 404: return None
            # Never render authentication headers or body in exceptions.
            raise GateError(f'GitHub API {verb} failed with HTTP {exc.code}') from None

    def metadata(self):
        return self._request('GET','')

    def get(self, path: str):
        suffix='/contents/'+quote(path,safe='/')+'?ref='+quote(self.branch,safe='')
        result=self._request('GET',suffix)
        if result is None:return None
        if result.get('type')!='file' or result.get('encoding')!='base64':
            raise GateError('GitHub returned a non-file or unsupported content format')
        return {'bytes':base64.b64decode(result['content']),'sha':result['sha']}

    def create(self, path: str, body: bytes):
        suffix='/contents/'+quote(path,safe='/')
        payload={'message':'archive(worldroot): immutable episode artifact '+hashlib.sha256(path.encode()).hexdigest()[:14],
                 'content':base64.b64encode(body).decode(), 'branch':self.branch}
        result=self._request('PUT',suffix,payload)
        if not result or not result.get('commit',{}).get('sha'):
            raise GateError('GitHub create did not return a commit SHA')
        return result['commit']['sha']


class PrivateGitHubArchive:
    """Fail-closed immutable GitHub publisher with independent readback.

    All archives are versioned under the dedicated branch. The gate is checked
    on every upload, so converting the repository back to public stops writes.
    """
    def __init__(self, api, *, allow_fake_for_tests: bool = False):
        if not isinstance(api, GitHubREST) and not allow_fake_for_tests:
            raise GateError('A real GitHub REST adapter is required in production')
        self.api = api

    def _require_private(self):
        m=self.api.metadata()
        if not m or m.get('private') is not True or m.get('visibility') != 'private':
            raise GateError('Repository is not verified PRIVATE; story bytes cannot be uploaded')
        if (m.get('permissions') or {}).get('push') is False:
            raise GateError('Authenticated GitHub account has no repository write access')

    def put_immutable(self, path: str, body: bytes) -> dict:
        if not isinstance(body,bytes):raise TypeError('UTF-8 bytes required')
        if not path.startswith('episodes/') or '..' in path.split('/'):
            raise GateError('Narrative artifacts must stay under episodes/')
        self._require_private()
        previous=self.api.get(path)
        commit=None
        if previous is not None:
            if previous['bytes'] != body:
                raise ConflictError('Immutable GitHub episode path reused with different bytes')
        else:
            try:commit=self.api.create(path,body)
            except GateError:
                # Crash after a successful commit or a racing writer: reconcile
                # exclusively by fetching the exact same path and bytes.
                present=self.api.get(path)
                if present is None or present['bytes']!=body:raise
        self._require_private()
        fetched=self.api.get(path)
        if not fetched or fetched['bytes']!=body:
            raise GateError('GitHub readback differs from source bytes')
        return {'path':path,'sha256':digest(body),'bytes':len(body),
                'verification':'github_private_contents_readback','commit':commit,
                'repository':self.api.repo,'branch':self.api.branch}

    def stage_package(self, episode_id: str, package_dir) -> dict:
        from pathlib import Path
        directory=Path(package_dir)
        names=('narrativa_integral.md','opcoes.json','eventos_e_consequencias.json',
               'checkpoint_candidato.json','episode_draft.json','manifesto_imutavel.json')
        # Check privacy BEFORE opening story bytes for transfer.
        self._require_private()
        return {name:self.put_immutable(f'episodes/{episode_id}/draft/{name}',
                    (directory/name).read_bytes()) for name in names}

    def recover_draft(self, episode_id: str):
        """Recover ALL private sidecars, validate manifest and restore literal draft."""
        from .episode_pipeline import EpisodeDraft
        self._require_private()
        prefix = f'episodes/{episode_id}/draft/'
        names = ('narrativa_integral.md', 'opcoes.json',
                 'eventos_e_consequencias.json', 'checkpoint_candidato.json',
                 'episode_draft.json')
        manifest = self.api.get(prefix + 'manifesto_imutavel.json')
        if not manifest:
            raise GateError('Immutable archive manifest is missing')
        try:
            proof = json.loads(manifest['bytes'].decode('utf-8'))
        except (UnicodeError, ValueError, TypeError):
            raise GateError('Archived GitHub manifest is invalid JSON') from None
        if (proof.get('schema') != 'worldroot-episode-package-v1'
                or proof.get('canon_status') != 'RASCUNHO'):
            raise GateError('Archive manifest schema/status is invalid')
        if proof.get('delivery_id') != episode_id:
            raise ConflictError('Recovered manifest episode identity mismatch')
        records = proof.get('artifacts')
        if not isinstance(records, dict) or set(records) != set(names):
            raise GateError('Manifest must enumerate all five draft sidecars')

        recovered = {}
        for name in names:
            remote = self.api.get(prefix + name)
            if not remote or not isinstance(remote.get('bytes'), bytes):
                raise GateError('Complete archived draft not present in private GitHub')
            body = remote['bytes']
            expected = records[name]
            if (not isinstance(expected, dict)
                    or expected.get('sha256') != digest(body)
                    or type(expected.get('bytes')) is not int
                    or expected['bytes'] != len(body)):
                raise GateError('GitHub recovered artifact failed manifest checksum: ' + name)
            recovered[name] = body

        if proof.get('original_readback_sha256') != digest(recovered['narrativa_integral.md']):
            raise GateError('Manifest original text hash mismatch')
        try:
            archive = json.loads(recovered['episode_draft.json'].decode('utf-8'))
            choices = json.loads(recovered['opcoes.json'].decode('utf-8'))
            events = json.loads(recovered['eventos_e_consequencias.json'].decode('utf-8'))
            checkpoint = json.loads(recovered['checkpoint_candidato.json'].decode('utf-8'))
            if archive.get('delivery_id') != episode_id:
                raise ConflictError('Recovered episode identity mismatch')
            if (archive.get('choices') != choices
                    or archive.get('events') != events
                    or archive.get('metadata') != checkpoint
                    or checkpoint.get('canon_status') != 'RASCUNHO'):
                raise GateError('Recovered sidecars disagree with episode JSON')
            draft = EpisodeDraft.from_dict(archive)
        except (UnicodeError, ValueError, TypeError, KeyError):
            raise GateError('Recovered draft payload cannot be decoded') from None
        if draft.full_text.encode('utf-8') != recovered['narrativa_integral.md']:
            raise ConflictError('Full literal differs from recovered draft JSON')
        draft.validate()
        return draft
