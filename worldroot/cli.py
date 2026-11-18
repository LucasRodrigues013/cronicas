"""Command-line harness, no network credentials and no automatic canon promotions."""
import argparse
import json
from pathlib import Path
from .ledger import WorldrootStore

def main():
    p=argparse.ArgumentParser(description='WORLDROOT private event ledger')
    p.add_argument('--root',default='./runtime')
    sub=p.add_subparsers(dest='action',required=True)
    sub.add_parser('status')
    s=sub.add_parser('prepare')
    s.add_argument('--id',required=True)
    s.add_argument('--literal',required=True)
    s.add_argument('--metadata',required=True)
    s.add_argument('--events')
    for action in ['validate','write','verify','confirm','receipt']:
        s=sub.add_parser(action);s.add_argument('--id',required=True)
        if action=='write':s.add_argument('--literal',required=True)
    s=sub.add_parser('sync-drive')
    s.add_argument('--id',required=True)
    s.add_argument('--folder-id',required=True)
    s=sub.add_parser('backup')
    s.add_argument('--destination',required=True)
    s=sub.add_parser('memory-status')
    s=sub.add_parser('query-legacy')
    s.add_argument('--db',required=True)
    s.add_argument('--query',required=True)
    a=p.parse_args();store=WorldrootStore(Path(a.root))
    if a.action=='status':o=store.status()
    elif a.action=='prepare':
        text=Path(a.literal).read_text(encoding='utf-8')
        meta=json.loads(Path(a.metadata).read_text(encoding='utf-8'))
        events=json.loads(Path(a.events).read_text(encoding='utf-8')) if a.events else []
        o=store.prepare(a.id,text,meta,events)
    elif a.action=='validate':o=store.validate(a.id)
    elif a.action=='write':o=store.write_literal(a.id,Path(a.literal).read_text(encoding='utf-8'))
    elif a.action=='verify':o=store.verify_local(a.id)
    elif a.action=='confirm':o=store.confirm(a.id)
    elif a.action=='sync-drive':
        from .drive_bridge import GoogleAPITransport,GoogleDriveSynchronizer
        o=GoogleDriveSynchronizer(GoogleAPITransport.from_adc(),a.folder_id).sync(store,a.id)
    elif a.action=='backup':
        from .backup import backup_and_verify
        o=backup_and_verify(store.db_path,Path(a.destination))
    elif a.action=='memory-status':
        from .memory import NarrativeMemory
        o=NarrativeMemory(Path(a.root)/'private'/'memory.sqlite').summary()
    elif a.action=='query-legacy':
        from .legacy import LegacyLiteralIndex
        o=LegacyLiteralIndex(a.db).query(a.query)
    else:o=store.receipt(a.id)
    print(json.dumps(o,ensure_ascii=False,indent=2,default=str))
if __name__=='__main__':main()
