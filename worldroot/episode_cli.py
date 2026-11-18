"""Explicit single-turn entrypoint for draft archival and next-choice closure.

Requires a trusted Python executor and secret credentials. ChatGPT text-only
conversation does not automatically invoke this module after rendering options.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .ledger import WorldrootStore, GateError
from .episode_pipeline import (EpisodeDraft, EpisodeClosure,
       EpisodePublicationCoordinator, VerifiedArtifactPublisher)
from .episode_handoff import (EpisodeHandoff, AuthorSelection,
       VerifiedCanonCommitter, PrivateCanonicalGitHubPublisher)
from .drive_bridge import (GoogleDriveSynchronizer,GoogleAPITransport,GoogleDocsHeadPublisher)
from .private_github import GitHubREST,PrivateGitHubArchive
from .sheets_index import GoogleSheetsEpisodeIndex


def _read(path):return json.loads(Path(path).read_text(encoding='utf-8'))

def main(argv=None):
    ap=argparse.ArgumentParser(description='WORLDROOT — explicit closure, no background watcher')
    ap.add_argument('--root',default='',help='Existing PRIVATE runtime with canonical HEAD')
    sub=ap.add_subparsers(dest='command',required=True)
    cmd=sub.add_parser('status');cmd.add_argument('--id',required=True)
    check=sub.add_parser('check-private');check.add_argument('--repo',required=True)
    check.add_argument('--archive-branch',default='story-archive')
    recover=sub.add_parser('recover')
    recover.add_argument('--repo',required=True);recover.add_argument('--archive-branch',default='story-archive')
    recover.add_argument('--id',required=True);recover.add_argument('--output',required=True)
    stage=sub.add_parser('stage-after-options')
    stage.add_argument('--draft',required=True);stage.add_argument('--drive-folder',required=True)
    stage.add_argument('--repo',required=True);stage.add_argument('--archive-branch',default='story-archive')
    close=sub.add_parser('choose-and-close')
    close.add_argument('--draft',required=True);close.add_argument('--reviewed-events',required=True)
    close.add_argument('--choice',type=int,required=True);close.add_argument('--free-text',default='')
    close.add_argument('--expected-release',required=True);close.add_argument('--expected-day',type=int,required=True)
    close.add_argument('--head-revision',required=True);close.add_argument('--head-doc',required=True)
    close.add_argument('--drive-folder',required=True);close.add_argument('--repo',required=True)
    close.add_argument('--archive-branch',default='story-archive')
    close.add_argument('--base-sheet',required=True);close.add_argument('--atlas-sheet',required=True)
    args=ap.parse_args(argv)
    if args.command=='check-private':
        m=GitHubREST(args.repo,args.archive_branch).metadata()
        result={'repository':args.repo,'private':m is not None and m.get('private') is True,
                'visibility':m.get('visibility') if m else None}
        print(json.dumps(result,ensure_ascii=False));return 0 if result['private'] else 2
    if args.command=='recover':
        git=PrivateGitHubArchive(GitHubREST(args.repo,args.archive_branch))
        episode=git.recover_draft(args.id)
        target=Path(args.output)
        if target.exists():
            if _read(target)['full_text']!=episode.full_text:
                raise GateError('Recovery target contains different narrative')
        else:
            target.parent.mkdir(parents=True,exist_ok=True)
            from .episode_pipeline import atomic_immutable,json_bytes
            atomic_immutable(target,json_bytes({'delivery_id':episode.delivery_id,
                 'prose':episode.prose,'full_text':episode.full_text,
                 'metadata':episode.metadata,'choices':[vars(c) for c in episode.choices],
                 'events':episode.events,'book_closed':episode.book_closed,
                 'editorial_visibility':episode.editorial_visibility}))
        print(json.dumps({'id':episode.delivery_id,'recovered':True,'output':str(target)},ensure_ascii=False))
        return 0
    if not args.root:
        raise GateError('--root is required for stage, status and canonical closure')
    store=WorldrootStore(args.root)
    head=store.status()['head']
    if head is None:raise GateError('Import and verify the last canon HEAD before staging')
    flow=EpisodeHandoff(EpisodeClosure(store))
    if args.command=='status':
        print(json.dumps(flow.status(args.id),ensure_ascii=False,default=str));return 0
    draft=EpisodeDraft.from_dict(_read(args.draft))
    transport=GoogleAPITransport.from_adc()
    drive=GoogleDriveSynchronizer(transport,args.drive_folder)
    github=PrivateGitHubArchive(GitHubREST(args.repo,args.archive_branch))
    if args.command=='stage-after-options':
        r=flow.stage_after_options(draft,drive_sync=drive,github_private=github)
        print(json.dumps({'episode_id':draft.delivery_id,'status':r['status'],
             'remote_draft_verified':r['status']=='RASCUNHO_ARQUIVADO',
             'head_day':head['day'],'head_release':head['release']},ensure_ascii=False))
        return 0 if r['status']=='RASCUNHO_ARQUIVADO' else 3
    # Choose-and-close is only called by a trusted adapter after an actual
    # author message. All real services must read back before the HEAD moves.
    if head['release']!=args.expected_release or head['day']!=args.expected_day:
        raise GateError('HEAD changed since author selected previous episode')
    canonical=EpisodePublicationCoordinator(flow.closure,drive_sync=drive,
       artifact_sync=VerifiedArtifactPublisher(transport,args.drive_folder),
       github=PrivateCanonicalGitHubPublisher(github,store.private),
       base_index=GoogleSheetsEpisodeIndex.from_adc(args.base_sheet),
       atlas_index=GoogleSheetsEpisodeIndex.from_adc(args.atlas_sheet),
       head_publisher=GoogleDocsHeadPublisher.from_adc(args.head_doc))
    finalizer=VerifiedCanonCommitter(canonical,expected_head_revision=args.head_revision)
    selected=AuthorSelection(draft.delivery_id,args.choice,args.free_text)
    r=flow.on_next_choice(draft,selected,reviewed_events=_read(args.reviewed_events),
       expected_head={'day':args.expected_day,'release':args.expected_release},
       trusted_committer=finalizer)
    print(json.dumps({'episode_id':draft.delivery_id,'closed':True,
         'next_generation_allowed':r['next_generation_allowed'],
         'head':r['head']['new_head'] if 'new_head' in r['head'] else r['head']},
         ensure_ascii=False,default=str))
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:
        print(json.dumps({'status':'PENDENTE','error_type':type(e).__name__,
                 'message':str(e)[:350]},ensure_ascii=False),file=sys.stderr)
        sys.exit(1)
