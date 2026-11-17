"""Append-only, idempotent narrative ledger. Standard library; SQLite is private/local.

The database never contains implicit ChatGPT/Drive credentials. Connector sync is
an explicit, externally verified step. Do not commit runtime files to Git.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1
STATES = ('PREPARADO', 'VALIDADO', 'GRAVADO', 'CONFERIDO', 'CONFIRMADO')
EVENT_STATES = ('NARRADO', 'CANONICO', 'RASCUNHO', 'SIMULADO', 'PLANEJADO', 'PENDENTE_APROVACAO')
IDENTIFIER = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{2,127}$')

class ConflictError(ValueError):
    """Stable ID reused with different content or changed version."""

class GateError(RuntimeError):
    """A promotion condition has not been satisfied."""

class InvalidStateError(RuntimeError):
    """Invalid state transition."""


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def encoded(data) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


class WorldrootStore:
    """Ledger + local literal archive. A Drive write must be separately confirmed.

    Sequence: prepare -> validate -> write -> verify -> confirm -> promote.
    `confirm` can complete local persistence; `promote` additionally requires a
    verified external Drive receipt and explicit author approval.
    """
    def __init__(self, directory: Path | str):
        self.root = Path(directory).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.private = self.root / 'private'
        self.chapters = self.private / 'chapters'
        self.chapters.mkdir(parents=True, exist_ok=True)
        self.db_path = self.private / 'event_ledger.sqlite'
        self._initialize()

    def _connection(self):
        c = sqlite3.connect(self.db_path, timeout=20)
        c.row_factory = sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON')
        c.execute('PRAGMA busy_timeout=20000')
        return c

    def _initialize(self):
        c = self._connection()
        try:
            c.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS deliveries (
                id TEXT PRIMARY KEY, sha256 TEXT NOT NULL, bytes INTEGER NOT NULL,
                metadata_json TEXT NOT NULL, events_json TEXT NOT NULL,
                state TEXT NOT NULL CHECK (state IN ('PREPARADO','VALIDADO','GRAVADO','CONFERIDO','CONFIRMADO')),
                local_path TEXT, local_verified_at TEXT, remote_receipt_json TEXT,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS transitions (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT, delivery_id TEXT NOT NULL REFERENCES deliveries(id),
                from_state TEXT, to_state TEXT NOT NULL, at TEXT NOT NULL, detail TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY, delivery_id TEXT NOT NULL REFERENCES deliveries(id),
                event_type TEXT NOT NULL, body_json TEXT NOT NULL, visibility TEXT NOT NULL,
                canon_status TEXT NOT NULL, recorded_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS canon_head (
                singleton INTEGER PRIMARY KEY CHECK (singleton=1), release TEXT NOT NULL,
                day INTEGER NOT NULL, book TEXT NOT NULL, chapter INTEGER NOT NULL,
                part TEXT NOT NULL, hour TEXT NOT NULL, location TEXT NOT NULL,
                delivery_id TEXT, release_record_json TEXT NOT NULL, changed_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS releases (
                release TEXT PRIMARY KEY, release_record_json TEXT NOT NULL, state TEXT NOT NULL,
                approved_by_author INTEGER NOT NULL, documented_debt_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            ''')
            c.commit()
        finally:
            c.close()

    def prepare(self, delivery_id: str, text: str, metadata: dict, events: list[dict] | None = None):
        if not IDENTIFIER.fullmatch(delivery_id):
            raise ValueError('Delivery ID needs a stable ASCII ID (3-128 chars)')
        if not isinstance(text, str) or not text.strip():
            raise ValueError('An intact, nonempty UTF-8 narrative text is required')
        for key in ('day', 'book', 'chapter', 'part', 'hour', 'location', 'choice'):
            if key not in metadata or metadata[key] in ('', None):
                raise ValueError(f'Missing required metadata: {key}')
        if (not isinstance(metadata['day'], int) or isinstance(metadata['day'], bool)
                or not isinstance(metadata['chapter'], int) or isinstance(metadata['chapter'], bool)
                or metadata['day'] < 1 or metadata['chapter'] < 1):
            raise ValueError('day and chapter must be positive integers')
        events = events or []
        ids = set()
        for event in events:
            eid = event.get('event_id')
            if not isinstance(eid, str) or not IDENTIFIER.fullmatch(eid):
                raise ValueError('Every event must have a stable event_id')
            if eid in ids:
                raise ConflictError('Duplicate event IDs in a delivery')
            ids.add(eid)
            if event.get('canon_status', 'PENDENTE_APROVACAO') not in EVENT_STATES:
                raise ValueError('Invalid event canon status')
            if event.get('visibility') not in ('PUBLICO','PRIVADO_PERSONAGEM','BASTIDORES'):
                raise ValueError('Invalid knowledge layer')
        payload = text.encode('utf-8')
        sha = digest(payload)
        mjson = encoded(metadata)
        ejson = encoded(events)
        c = self._connection()
        try:
            c.execute('BEGIN IMMEDIATE')
            existing = c.execute('SELECT * FROM deliveries WHERE id=?', (delivery_id,)).fetchone()
            if not existing:
                for proposed_id in ids:
                    prior_event = c.execute('SELECT delivery_id FROM events WHERE event_id=?', (proposed_id,)).fetchone()
                    if prior_event and prior_event['delivery_id'] != delivery_id:
                        raise ConflictError('Event ID already recorded by another delivery')
                # Also reserve event IDs against other pending deliveries to prevent
                # an eventual first-confirmed-wins collision.
                pending = c.execute('SELECT id,events_json FROM deliveries WHERE id<>?', (delivery_id,)).fetchall()
                for row in pending:
                    occupied = {event['event_id'] for event in json.loads(row['events_json'])}
                    if ids & occupied:
                        raise ConflictError('Event ID already reserved by another delivery')
            if existing:
                if (existing['sha256'], existing['metadata_json'], existing['events_json']) != (sha, mjson, ejson):
                    raise ConflictError('Delivery ID already exists with different text/metadata/events')
                c.commit()
                return self.receipt(delivery_id)
            now = utcnow()
            c.execute('INSERT INTO deliveries (id,sha256,bytes,metadata_json,events_json,state,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)',
                      (delivery_id, sha, len(payload), mjson, ejson, 'PREPARADO', now, now))
            self._transition(c, delivery_id, None, 'PREPARADO', 'Immutable digest registered')
            c.commit()
            return self.receipt(delivery_id)
        except Exception:
            c.rollback()
            raise
        finally:
            c.close()

    @staticmethod
    def _transition(c, delivery_id, old, new, detail):
        c.execute('INSERT INTO transitions(delivery_id,from_state,to_state,at,detail) VALUES (?,?,?,?,?)',
                  (delivery_id,old,new,utcnow(),detail))

    def _advance(self, delivery_id, expected, state, detail, **changes):
        c = self._connection()
        try:
            c.execute('BEGIN IMMEDIATE')
            row = c.execute('SELECT state FROM deliveries WHERE id=?', (delivery_id,)).fetchone()
            if row is None:
                raise KeyError(delivery_id)
            if row['state'] == state or STATES.index(row['state']) > STATES.index(state):
                c.commit()
                return self.receipt(delivery_id)
            if row['state'] != expected:
                raise InvalidStateError(f'Expected {expected}, found {row["state"]}')
            assignments=', '.join(['state=?','updated_at=?']+[f'{k}=?' for k in changes])
            c.execute('UPDATE deliveries SET '+assignments+' WHERE id=?',
                      (state,utcnow(),*changes.values(),delivery_id))
            self._transition(c,delivery_id,expected,state,detail)
            c.commit()
            return self.receipt(delivery_id)
        except Exception:
            c.rollback()
            raise
        finally:
            c.close()

    def validate(self, delivery_id):
        r = self.receipt(delivery_id)
        if r['state'] != 'PREPARADO':
            return r
        meta=r['metadata']
        c=self._connection()
        try:
            head=c.execute('SELECT * FROM canon_head WHERE singleton=1').fetchone()
            if head and meta['day'] < head['day']:
                raise GateError('Cannot travel backward from canon head')
            if head and meta['day'] > head['day']+1:
                raise GateError('Chronology leap requires independent editorial approval')
        finally:
            c.close()
        return self._advance(delivery_id,'PREPARADO','VALIDADO','Metadata and chronology checked (not semantic certification)')

    def write_literal(self, delivery_id, text: str):
        r=self.receipt(delivery_id)
        if digest(text.encode('utf-8')) != r['sha256']:
            raise ConflictError('Literal input digest differs from prepared item')
        if STATES.index(r['state']) >= STATES.index('GRAVADO'):
            return self.receipt(delivery_id)
        if r['state']!='VALIDADO':
            raise InvalidStateError('validate before write')
        path=self.chapters/(delivery_id+'.txt')
        if path.exists():
            if digest(path.read_bytes())!=r['sha256']:
                raise ConflictError('Archive path exists with different content')
        else:
            tmp=None
            try:
                with tempfile.NamedTemporaryFile('wb',dir=self.chapters,delete=False,prefix='.writing_') as f:
                    tmp=Path(f.name)
                    f.write(text.encode('utf-8'))
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp,path)
            finally:
                if tmp is not None and tmp.exists():
                    tmp.unlink()
        return self._advance(delivery_id,'VALIDADO','GRAVADO','Literal archived atomically on local filesystem',local_path=str(path))

    def verify_local(self, delivery_id):
        r=self.receipt(delivery_id)
        if STATES.index(r['state']) >= STATES.index('CONFERIDO'):
            return r
        if r['state']!='GRAVADO':
            raise InvalidStateError('write before verify')
        path=Path(r['local_path'])
        data=path.read_bytes()
        if digest(data)!=r['sha256'] or len(data)!=r['bytes']:
            raise GateError('Readback failed digest/length check')
        return self._advance(delivery_id,'GRAVADO','CONFERIDO','Local readback SHA256 and byte count verified',local_verified_at=utcnow())

    def record_external_readback(self, delivery_id, *, provider, locator, returned_bytes: bytes):
        if provider != 'google_drive':
            raise ValueError('External source of truth is currently Google Drive')
        r=self.receipt(delivery_id)
        if r['state'] not in ('CONFERIDO','CONFIRMADO'):
            raise InvalidStateError('Local readback first')
        if not locator or not isinstance(locator,str):
            raise ValueError('A grounded, nonempty external file locator is required')
        sha=digest(returned_bytes)
        if sha!=r['sha256'] or len(returned_bytes)!=r['bytes']:
            raise GateError('External bytes do not match literal SHA256')
        receipt={'provider':provider,'locator':locator,'sha256':sha,'bytes':len(returned_bytes),'checked_at':utcnow(),'verified':True}
        c=self._connection()
        try:
            c.execute('BEGIN IMMEDIATE')
            current=c.execute('SELECT remote_receipt_json FROM deliveries WHERE id=?',(delivery_id,)).fetchone()
            if current['remote_receipt_json']:
                if json.loads(current['remote_receipt_json'])['locator']!=locator:
                    raise ConflictError('Delivery already has a different external receipt')
                c.commit()
                return self.receipt(delivery_id)
            c.execute('UPDATE deliveries SET remote_receipt_json=?,updated_at=? WHERE id=?',(encoded(receipt),utcnow(),delivery_id))
            c.commit()
        except Exception:
            c.rollback()
            raise
        finally:
            c.close()
        return self.receipt(delivery_id)

    def confirm(self, delivery_id):
        r=self.receipt(delivery_id)
        if r['state']=='CONFIRMADO':
            return r
        if r['state']!='CONFERIDO':
            raise InvalidStateError('verify local before confirm')
        if not r['external'] or not r['external'].get('verified'):
            raise GateError('CONFIRMADO requires independent Drive readback (never local-only)')
        c=self._connection()
        try:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute('SELECT state,events_json,remote_receipt_json FROM deliveries WHERE id=?',(delivery_id,)).fetchone()
            if not row['remote_receipt_json'] or not json.loads(row['remote_receipt_json']).get('verified'):
                raise GateError('External Drive receipt disappeared or is not verified')
            if row['state']!='CONFERIDO':
                if row['state']=='CONFIRMADO':
                    c.commit(); return self.receipt(delivery_id)
                raise InvalidStateError('Concurrent state transition')
            for event in json.loads(row['events_json']):
                eid=event['event_id']
                existing=c.execute('SELECT delivery_id,body_json FROM events WHERE event_id=?',(eid,)).fetchone()
                if existing:
                    if existing['delivery_id'] != delivery_id or existing['body_json']!=encoded(event):
                        raise ConflictError('Event ID already belongs to a different fact')
                    continue
                c.execute('INSERT INTO events(event_id,delivery_id,event_type,body_json,visibility,canon_status,recorded_at) VALUES (?,?,?,?,?,?,?)',
                          (eid,delivery_id,event.get('event_type','EVENT'),encoded(event),event['visibility'],event.get('canon_status','PENDENTE_APROVACAO'),utcnow()))
            c.execute('UPDATE deliveries SET state=?,updated_at=? WHERE id=?',('CONFIRMADO',utcnow(),delivery_id))
            self._transition(c,delivery_id,'CONFERIDO','CONFIRMADO','Local and external Drive readbacks verified; event ledger finalized')
            c.commit()
        except Exception:
            c.rollback();raise
        finally:
            c.close()
        return self.receipt(delivery_id)

    def baseline(self, *, release, day, book, chapter, part, hour, location, debts, approved_by_author: bool):
        """Record D528 baseline. Not a claim of complete semantic certification."""
        if not approved_by_author:
            raise GateError('Explicit author approval is required')
        if not debts or not isinstance(debts,list):
            raise GateError('Known semantic debt must be documented; cannot silently certify')
        info={'release':release,'day':day,'book':book,'chapter':chapter,'part':part,'hour':hour,'location':location,
              'semantic_completeness':'NOT_CERTIFIED','event_stream_full_replay':'NOT_CERTIFIED','approval':'AUTHOR_APPROVED_WITH_KNOWN_DEBT'}
        c=self._connection()
        try:
            c.execute('BEGIN IMMEDIATE')
            existing=c.execute('SELECT * FROM releases WHERE release=?',(release,)).fetchone()
            if existing:
                if existing['release_record_json'] != encoded(info) or existing['documented_debt_json'] != encoded(debts):
                    raise ConflictError('Existing baseline immutable; choose a new release ID for changes')
                c.commit();return info
            c.execute('INSERT INTO releases(release,release_record_json,state,approved_by_author,documented_debt_json,created_at) VALUES (?,?,?,?,?,?)',
                      (release,encoded(info),'BASELINE_WITH_DEBT',1,encoded(debts),utcnow()))
            head=c.execute('SELECT * FROM canon_head WHERE singleton=1').fetchone()
            if head and (head['day']>day or (head['day']==day and head['release']!=release)):
                raise GateError('Existing head differs; no automatic retcon')
            if not head:
                c.execute('INSERT INTO canon_head(singleton,release,day,book,chapter,part,hour,location,delivery_id,release_record_json,changed_at) VALUES (1,?,?,?,?,?,?,?,?,?,?)',
                          (release,day,book,chapter,part,hour,location,None,encoded(info),utcnow()))
            c.commit();return info
        except Exception:
            c.rollback();raise
        finally:
            c.close()

    def promote(self, delivery_id, *, author_approved: bool, expected_head_day: int):
        if not author_approved:
            raise GateError('Author did not approve publication')
        r=self.receipt(delivery_id)
        if r['state']!='CONFIRMADO':
            raise GateError('Delivery not confirmed')
        if not r['external'] or not r['external'].get('verified'):
            raise GateError('No externally verified Drive literal receipt')
        if not r['events']:
            raise GateError('A reviewed event/continuity delta is required for canon promotion')
        if any(x.get('canon_status','PENDENTE_APROVACAO')!='NARRADO' for x in r['events']):
            raise GateError('Event states must be reviewed individually before promotion')
        meta=r['metadata']
        c=self._connection()
        try:
            c.execute('BEGIN IMMEDIATE')
            head=c.execute('SELECT * FROM canon_head WHERE singleton=1').fetchone()
            if not head or head['day']!=expected_head_day:
                raise GateError('Stale expected_head_day; manual reconciliation required')
            if int(meta['day'])<head['day'] or int(meta['day'])>head['day']+1:
                raise GateError('Invalid chronological advancement')
            new_release=f"{head['release']}+{delivery_id}"
            new_info={'release':new_release,'day':meta['day'],'book':meta['book'],'chapter':meta['chapter'],
                'part':meta['part'],'hour':meta['hour'],'location':meta['location'],'delivery_id':delivery_id,
                'hash':r['sha256'],'readback':r['external']['locator'],'approved':True}
            c.execute('UPDATE canon_head SET release=?,day=?,book=?,chapter=?,part=?,hour=?,location=?,delivery_id=?,release_record_json=?,changed_at=? WHERE singleton=1',
                (new_release,int(meta['day']),meta['book'],int(meta['chapter']),meta['part'],meta['hour'],meta['location'],delivery_id,encoded(new_info),utcnow()))
            c.execute('INSERT INTO releases(release,release_record_json,state,approved_by_author,documented_debt_json,created_at) VALUES (?,?,?,?,?,?)',
                (new_release,encoded(new_info),'CANON_PROMOTED',1,encoded([]),utcnow()))
            c.commit();return new_info
        except Exception:
            c.rollback();raise
        finally:
            c.close()

    def receipt(self, delivery_id):
        c=self._connection()
        try:
            r=c.execute('SELECT * FROM deliveries WHERE id=?',(delivery_id,)).fetchone()
            if not r:
                raise KeyError(delivery_id)
            d=dict(r)
            return {'delivery_id':delivery_id,'sha256':d['sha256'],'bytes':d['bytes'],'state':d['state'],
                'metadata':json.loads(d['metadata_json']),'events':json.loads(d['events_json']),
                'local_path':d['local_path'],'local_verified_at':d['local_verified_at'],
                'external':json.loads(d['remote_receipt_json']) if d['remote_receipt_json'] else None}
        finally:
            c.close()

    def status(self):
        c=self._connection()
        try:
            head=c.execute('SELECT * FROM canon_head WHERE singleton=1').fetchone()
            counts=dict(c.execute('SELECT state,count(*) FROM deliveries GROUP BY state').fetchall())
            return {'head':dict(head) if head else None,'deliveries_by_state':counts,
                    'event_count':c.execute('SELECT count(*) FROM events').fetchone()[0],
                    'db_integrity':c.execute('PRAGMA integrity_check').fetchone()[0]}
        finally:c.close()
