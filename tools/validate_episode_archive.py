"""WORLDROOT story-archive validator (stdlib only, never prints narrative).

A completed episode draft is announced by manifesto_imutavel.json, committed
AFTER the other five artifacts. This program does not write to Google Drive,
change HEAD, declare a draft canonical, or infer story semantics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REQUIRED = (
    'narrativa_integral.md',
    'opcoes.json',
    'eventos_e_consequencias.json',
    'checkpoint_candidato.json',
    'episode_draft.json',
)

class ArchiveInvalid(ValueError):
    pass


def _json(blob: bytes, where: str):
    try:
        return json.loads(blob.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ArchiveInvalid(f'{where}: invalid UTF-8 JSON') from exc


def verify_one(manifest_path: Path) -> dict:
    folder = manifest_path.parent
    if folder.name != 'draft' or folder.parent.parent.name != 'episodes':
        raise ArchiveInvalid('manifest is outside episodes/<id>/draft')
    episode_id = folder.parent.name
    if not episode_id.isascii() or not episode_id or not all(c.isalnum() or c in '-_' for c in episode_id):
        raise ArchiveInvalid('unsafe episode identifier')
    if manifest_path.is_symlink():
        raise ArchiveInvalid('manifest cannot be a symbolic link')
    manifest = _json(manifest_path.read_bytes(), 'manifest')
    if (manifest.get('schema') != 'worldroot-episode-package-v1'
            or manifest.get('delivery_id') != episode_id
            or manifest.get('canon_status') != 'RASCUNHO'):
        raise ArchiveInvalid('manifest identity or draft state mismatch')
    artifacts = manifest.get('artifacts')
    if not isinstance(artifacts, dict) or set(artifacts) != set(REQUIRED):
        raise ArchiveInvalid('manifest has missing/unexpected artifacts')
    raw = {}
    for name in REQUIRED:
        path = folder / name
        if not path.is_file() or path.is_symlink():
            raise ArchiveInvalid(f'{name}: missing or symbolic link')
        blob = path.read_bytes()
        record = artifacts[name]
        if (not isinstance(record, dict) or record.get('sha256') != hashlib.sha256(blob).hexdigest()
                or type(record.get('bytes')) is not int or record['bytes'] != len(blob)):
            raise ArchiveInvalid(f'{name}: sha256/length mismatch')
        raw[name] = blob
    literal = raw['narrativa_integral.md']
    if manifest.get('original_readback_sha256') != hashlib.sha256(literal).hexdigest():
        raise ArchiveInvalid('original full text hash differs')
    try:
        text = literal.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ArchiveInvalid('narrative is not UTF-8') from exc
    draft = _json(raw['episode_draft.json'], 'episode_draft')
    if draft.get('delivery_id') != episode_id or draft.get('full_text') != text:
        raise ArchiveInvalid('episode JSON and literal narrative differ')
    prose = draft.get('prose')
    if not isinstance(prose, str) or len(prose.strip()) < 50 or not text.startswith(prose):
        raise ArchiveInvalid('prose is truncated or not the exact prefix')
    metadata = _json(raw['checkpoint_candidato.json'], 'checkpoint')
    if draft.get('metadata') != metadata or metadata.get('canon_status') != 'RASCUNHO':
        raise ArchiveInvalid('checkpoint differs or wrongly declares canon')
    choices = _json(raw['opcoes.json'], 'choices')
    if not isinstance(choices, list) or len(choices) != 5 or draft.get('choices') != choices:
        raise ArchiveInvalid('the five choices were not preserved')
    for idx, choice in enumerate(choices, start=1):
        if (not isinstance(choice, dict) or type(choice.get('number')) is not int
                or choice.get('number') != idx or not isinstance(choice.get('title'), str)
                or choice['title'] not in text):
            raise ArchiveInvalid(f'option {idx} is invalid or absent from source')
    if choices[3].get('is_special') is not True or choices[4].get('is_free') is not True:
        raise ArchiveInvalid('options 4 and 5 lost their semantics')
    events = _json(raw['eventos_e_consequencias.json'], 'events')
    if draft.get('events') != events or not isinstance(events, list):
        raise ArchiveInvalid('events sidecar differs')
    if draft.get('book_closed') is True:
        # Legacy metadata flag cannot establish author approval. This archive
        # has its own immutable author request, choice and canonical receipt.
        # Verify all four by content without mutating the original chapter.
        root = folder.parent.parent.parent
        book = metadata.get('book')
        journal_path = root/'canon'/'episodes'/(episode_id+'.json')
        approval_path = root/'author-approvals'/(episode_id+'.json')
        request_path = root/'canon'/'BOOK_END_REQUEST.json'
        if not all(p.is_file() and not p.is_symlink()
                   for p in (journal_path, approval_path, request_path)):
            raise ArchiveInvalid('book cannot close without source-backed author approval')
        journal = _json(journal_path.read_bytes(), 'book_end_journal')
        approval = _json(approval_path.read_bytes(), 'author_approval')
        request = _json(request_path.read_bytes(), 'book_end_request')
        previous = journal.get('previous_episode_id')
        if (journal.get('status') != 'FECHADO_GITHUB'
                or journal.get('book_closed') is not True
                or journal.get('episode_id') != episode_id
                or journal.get('story_sha256') != hashlib.sha256(literal).hexdigest()
                or journal.get('metadata', {}).get('book') != book
                or not isinstance(previous, str)
                or not previous.isascii()
                or not all(c.isalnum() or c in '-_' for c in previous)
                or approval.get('schema') != 'worldroot-author-book-end-v1'
                or approval.get('approved') is not True
                or approval.get('author_source') != 'USER_MESSAGE'
                or approval.get('episode_id') != episode_id
                or approval.get('book') != book
                or approval.get('previous_episode_id') != previous
                or approval.get('new_book_opened') is not False
                or not isinstance(approval.get('author_quote'), str)
                or not approval['author_quote'].strip()
                or request.get('schema') != 'worldroot-book-end-request-v1'
                or request.get('episode_id') != episode_id
                or request.get('book') != book
                or request.get('previous_episode_id') != previous
                or request.get('approval_path') != 'author-approvals/'+episode_id+'.json'
                or request.get('archived_story_sha256') != journal.get('story_sha256')
                or request.get('new_book_opened') is not False):
            raise ArchiveInvalid('book closure record inconsistent with author approval')
        choice_path = approval.get('choice_path')
        prefix = 'choices/' + previous + '/'
        if (not isinstance(choice_path, str)
                or not choice_path.startswith(prefix)
                or choice_path[len(prefix):] not in
                   {f'option-{i}.json' for i in range(1, 6)}):
            raise ArchiveInvalid('book closure approval references unsafe author choice')
        full_choice_path = root / choice_path
        if not full_choice_path.is_file() or full_choice_path.is_symlink():
            raise ArchiveInvalid('book closure original author choice missing')
        choice = _json(full_choice_path.read_bytes(), 'author_choice')
        if (choice.get('schema') != 'worldroot-author-choice-v1'
                or choice.get('episode_id') != previous
                or choice.get('free_text') != approval['author_quote']
                or choice.get('author_source') != 'USER_MESSAGE'):
            raise ArchiveInvalid('book closure author choice differs from approval')
    return {'episode_id': episode_id, 'sha256': hashlib.sha256(literal).hexdigest(),
            'bytes': len(literal), 'state': 'RASCUNHO_VALIDADO_LOCALMENTE'}


def verify_tree(root: Path) -> list[dict]:
    manifests = sorted((root/'episodes').glob('*/draft/manifesto_imutavel.json'))
    return [verify_one(p) for p in manifests]


def main():
    parser=argparse.ArgumentParser(description='Validate complete WORLDROOT GitHub draft packages')
    parser.add_argument('--root',type=Path,default=Path('.'))
    a=parser.parse_args()
    try:
        valid=verify_tree(a.root)
    except (ArchiveInvalid, OSError) as exc:
        print('WORLDROOT INVALID PACKAGE: '+str(exc))
        return 1
    print(f'WORLDROOT VALIDATED {len(valid)} complete draft package(s). Does not certify Drive sync or canon.')
    for record in valid:
        print(f"DRAFT {record['episode_id']}: verified, {record['bytes']} UTF-8 bytes, sha256={record['sha256'][:16]}…")
    return 0


if __name__=='__main__':
    raise SystemExit(main())
