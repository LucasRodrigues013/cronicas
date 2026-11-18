"""SQLite consistent online backups with actual restore drill; no raw copy of WAL db."""
import hashlib
import json
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def backup_and_verify(db_path: str | Path, destination: str | Path):
    src=Path(db_path).resolve();dst=Path(destination).resolve()
    if not src.is_file() or src==dst:
        raise ValueError('Source must exist and output must be a distinct file')
    dst.parent.mkdir(parents=True,exist_ok=True)
    # SQLite online backup ensures one consistent snapshot even under WAL.
    with sqlite3.connect(f'file:{src}?mode=ro',uri=True) as source:
        with sqlite3.connect(dst) as target:
            source.backup(target, pages=512, sleep=0.05)
    datahash=hashlib.sha256(dst.read_bytes()).hexdigest()
    # Restore to a brand-new db and verify integrity of the restored database.
    with tempfile.TemporaryDirectory() as temp:
        restored=Path(temp)/'restored.sqlite'
        with sqlite3.connect(f'file:{dst}?mode=ro',uri=True) as bak:
            with sqlite3.connect(restored) as tgt:
                bak.backup(tgt)
        with sqlite3.connect(restored) as check:
            integrity=check.execute('PRAGMA integrity_check').fetchone()[0]
            foreign=check.execute('PRAGMA foreign_key_check').fetchall()
            tables=[x[0] for x in check.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        if integrity!='ok' or foreign:
            raise RuntimeError('Restore drill failed SQLite integrity/foreign key checks')
    manifest={'source':str(src),'backup':str(dst),'sha256':datahash,'bytes':dst.stat().st_size,
              'restored_integrity':integrity,'foreign_key_violations':len(foreign),
              'table_count':len(tables),'verified_at':datetime.now(timezone.utc).isoformat()}
    return manifest
