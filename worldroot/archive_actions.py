"""Restricted GitHub Actions hook: verify GitHub draft & mirror identical artifacts to Drive.

This adapter is intentionally independent of the persistent WorldrootStore: each
GitHub runner is ephemeral. It never updates HEAD, Base Viva or Atlas and never
promotes an episode merely because the mirror succeeded.

The archive branch's `tools/validate_episode_archive.py` is the integrity gate;
that code must have been reviewed and checked out separately by the workflow.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from .drive_bridge import GoogleAPITransport
from .episode_pipeline import VerifiedArtifactPublisher
from .ledger import GateError

ALL_FILES = (
    'narrativa_integral.md', 'opcoes.json', 'eventos_e_consequencias.json',
    'checkpoint_candidato.json', 'episode_draft.json', 'manifesto_imutavel.json',
)


def mirror_archive(root: Path, folder_id: str, publisher=None):
    """Synchronize only complete immutable DRAFT packages, never canon."""
    if not folder_id or '/' in folder_id:
        raise GateError('A real Drive folder ID is required')
    tools = root / 'tools'
    if not (tools/'validate_episode_archive.py').is_file():
        raise GateError('Archive validator is missing: no sync permitted')
    sys.path.insert(0, str(tools.resolve()))
    from validate_episode_archive import verify_tree

    verified = verify_tree(root)
    if not verified:
        raise GateError('No complete draft manifest found; avoid false green sync')
    if publisher is None:
        publisher = VerifiedArtifactPublisher(GoogleAPITransport.from_adc(), folder_id)
    receipts = []
    for item in verified:
        episode_id = item['episode_id']
        directory = root/'episodes'/episode_id/'draft'
        synced = []
        for name in ALL_FILES:
            blob = (directory/name).read_bytes()
            artifact_id = f"{episode_id}-{hashlib.sha256(name.encode()).hexdigest()[:12]}"
            receipt = publisher.sync_file(artifact_id, name, blob)
            if (receipt.get('verification') != 'google_drive_get_media'
                    or receipt.get('sha256') != hashlib.sha256(blob).hexdigest()
                    or receipt.get('bytes') != len(blob)):
                raise GateError('Remote Drive confirmation invalid for '+name)
            synced.append({'name':name,'file_id':receipt['file_id'],'sha256':receipt['sha256']})
        receipts.append({'episode_id':episode_id,'status':'RASCUNHO_DRIVE_ESPELHADO',
                         'files':synced,'canon':False,'head_changed':False})
    return receipts


def main():
    ap=argparse.ArgumentParser(description='WORLDROOT: mirror immutable archive drafts to Drive')
    ap.add_argument('--archive-root',type=Path,required=True)
    ap.add_argument('--drive-folder',default=os.environ.get('WORLDROOT_DRAFTS_FOLDER_ID',''))
    args=ap.parse_args()
    try:
        receipts=mirror_archive(args.archive_root,args.drive_folder)
    except Exception as exc:
        print('WORLDROOT MIRROR FAILED: '+type(exc).__name__+': '+str(exc)[:300],file=sys.stderr)
        return 1
    print(json.dumps(receipts,ensure_ascii=False,sort_keys=True))
    print('DRAFT FILES VERIFIED ON DRIVE. HEAD/BASE/ATLAS NOT UPDATED.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
