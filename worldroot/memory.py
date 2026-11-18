"""Evidence-first, temporal narrative memory. No automatic canon from heuristics.

A person's knowledge is not the reader's knowledge. Character aliases are
NOT automatically merged. Planned content is never returned as narrated fact.
"""
from __future__ import annotations
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .ledger import ConflictError, GateError, encoded, utcnow

STATUSES={'NARRADO','PLANEJADO','RASCUNHO','SIMULADO','PENDENTE_APROVACAO'}
SCOPES={'PUBLICO','PRIVADO_PERSONAGEM','BASTIDORES'}


class NarrativeMemory:
    def __init__(self, path: str | Path):
        self.path=Path(path).resolve();self.path.parent.mkdir(parents=True,exist_ok=True)
        with self._db() as db:
            db.executescript('''
              PRAGMA foreign_keys=ON;
              CREATE TABLE IF NOT EXISTS entities (
                entity_id TEXT PRIMARY KEY, name TEXT NOT NULL, identity_status TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS aliases (
                entity_id TEXT NOT NULL REFERENCES entities(entity_id), alias TEXT NOT NULL,
                evidence_source TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('CANDIDATE','VERIFIED')),
                PRIMARY KEY(entity_id,alias));
              CREATE TABLE IF NOT EXISTS facts (
                fact_id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, predicate TEXT NOT NULL,
                object_json TEXT NOT NULL, day INTEGER NOT NULL, minute INTEGER,
                source_id TEXT NOT NULL, source_line INTEGER NOT NULL,
                visibility TEXT NOT NULL CHECK(visibility IN ('PUBLICO','PRIVADO_PERSONAGEM','BASTIDORES')),
                canon_status TEXT NOT NULL, semantic_review INTEGER NOT NULL,
                confidence TEXT NOT NULL, recorded_at TEXT NOT NULL);
              CREATE INDEX IF NOT EXISTS idx_facts_day ON facts(day,subject_id);
              CREATE TABLE IF NOT EXISTS knowledge (
                person_id TEXT NOT NULL REFERENCES entities(entity_id),fact_id TEXT NOT NULL REFERENCES facts(fact_id),
                learned_day INTEGER NOT NULL, learned_minute INTEGER,channel TEXT NOT NULL,
                narrator_source TEXT NOT NULL, narrator_line INTEGER NOT NULL,
                confirmed INTEGER NOT NULL,
                PRIMARY KEY(person_id,fact_id,learned_day));
              CREATE INDEX IF NOT EXISTS idx_knowledge_lookup ON knowledge(person_id,learned_day);
              CREATE TABLE IF NOT EXISTS relationship_events (
                relation_event_id TEXT PRIMARY KEY, from_id TEXT NOT NULL REFERENCES entities(entity_id),
                to_id TEXT NOT NULL REFERENCES entities(entity_id), relation TEXT NOT NULL,
                state TEXT NOT NULL, since_day INTEGER NOT NULL, evidence_source TEXT NOT NULL,
                evidence_line INTEGER NOT NULL, canon_status TEXT NOT NULL,reviewed INTEGER NOT NULL);
              CREATE TABLE IF NOT EXISTS open_threads (
                thread_id TEXT PRIMARY KEY, kind TEXT NOT NULL, title TEXT NOT NULL,
                status TEXT NOT NULL, last_narrated_day INTEGER, visibility TEXT NOT NULL,
                hypothesis_json TEXT NOT NULL, source_id TEXT, source_line INTEGER);
              CREATE TABLE IF NOT EXISTS chronology (
                story_day INTEGER PRIMARY KEY CHECK(story_day >= 1),
                kind TEXT NOT NULL CHECK(kind IN ('HEADER','ELIPSE','MENCAO','NAO_CERTIFICADO')),
                primary_anchor TEXT, review_state TEXT NOT NULL,
                editorial_note TEXT NOT NULL);
            ''')

    @contextmanager
    def _db(self):
        db=sqlite3.connect(self.path)
        db.execute('PRAGMA foreign_keys=ON')
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def register_person(self, entity_id, name, identity_status='CANDIDATE', notes=''):
        if not entity_id or not name:raise ValueError('Stable ID and name required')
        with self._db() as db:
            old=db.execute('SELECT name FROM entities WHERE entity_id=?',(entity_id,)).fetchone()
            if old:
                if old[0]!=name:raise ConflictError('Stable identity ID cannot silently change name')
                return
            db.execute('INSERT INTO entities VALUES(?,?,?,?,?)',(entity_id,name,identity_status,notes,utcnow()))

    def propose_alias(self, entity_id, alias, evidence_source, status='CANDIDATE'):
        if status not in ('CANDIDATE','VERIFIED') or not evidence_source:raise ValueError('Evidence mandatory')
        with self._db() as db:
            db.execute('INSERT OR IGNORE INTO aliases VALUES(?,?,?,?)',(entity_id,alias,evidence_source,status))

    def add_fact(self, *, fact_id, subject_id, predicate, value, day, source_id, source_line,
                 visibility='BASTIDORES', status='PENDENTE_APROVACAO', semantic_review=False,
                 confidence='NAO_CERTIFICADO', minute=None):
        if status not in STATUSES or visibility not in SCOPES:raise ValueError('Invalid fact state')
        if day<1 or source_line<1 or not source_id:raise ValueError('Evidence day/line required')
        if status=='NARRADO' and not semantic_review:raise GateError('Narrated fact requires semantic review')
        if minute is not None and not 0<=minute<1440:raise ValueError('minute outside 24h')
        payload=encoded(value)
        entry=(fact_id,subject_id,predicate,payload,day,minute,source_id,source_line,visibility,status,int(semantic_review),confidence,utcnow())
        with self._db() as db:
            prior=db.execute('SELECT subject_id,predicate,object_json,day,source_id,source_line,visibility,canon_status,semantic_review FROM facts WHERE fact_id=?',(fact_id,)).fetchone()
            subset=(subject_id,predicate,payload,day,source_id,source_line,visibility,status,int(semantic_review))
            if prior:
                if tuple(prior)!=subset:raise ConflictError('Fact ID reused for incompatible assertion')
                return
            db.execute('INSERT INTO facts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',entry)

    def learn(self, *, person_id, fact_id, learned_day, channel, source_id, line, confirmed,
              learned_minute=None):
        """Record narrated transfer. Without a minute, same-day knowledge is uncertain.

        For minute-specific story queries, uncertain same-day transfers are
        conservatively unavailable until the following day. Older day-only
        queries remain backward compatible with the original schema.
        """
        if not confirmed or not source_id or line<1 or not channel:
            raise GateError('Learning requires narrated provenance')
        if not isinstance(learned_day,int) or isinstance(learned_day,bool) or learned_day<1:
            raise ValueError('Learning day must be positive')
        if learned_minute is not None and (not isinstance(learned_minute,int)
                or isinstance(learned_minute,bool) or not 0<=learned_minute<1440):
            raise ValueError('Learning minute outside 24h')
        with self._db() as db:
            fact=db.execute('SELECT day,minute,canon_status,semantic_review FROM facts WHERE fact_id=?',(fact_id,)).fetchone()
            if not fact:raise ValueError('Unknown fact')
            if fact[2]!='NARRADO' or not fact[3]:
                raise GateError('Planned/uncertified fact cannot become known canon')
            if learned_day<fact[0]:
                raise GateError('Cannot know future fact without established in-world cause')
            if learned_day==fact[0] and learned_minute is not None and fact[1] is not None and learned_minute<fact[1]:
                raise GateError('Cannot learn a fact earlier than its narration')
            old=db.execute('SELECT learned_minute,channel,narrator_source,narrator_line FROM knowledge WHERE person_id=? AND fact_id=? AND learned_day=?',
                           (person_id,fact_id,learned_day)).fetchone()
            if old:
                if tuple(old)!=(learned_minute,channel,source_id,line):
                    raise ConflictError('Knowledge arrival cannot silently change: add a new source event')
                return
            db.execute('INSERT INTO knowledge VALUES(?,?,?,?,?,?,?,?)',
                       (person_id,fact_id,learned_day,learned_minute,channel,source_id,line,1))

    def known_by(self, person_id, asof_day, asof_minute=None):
        if asof_minute is not None and (not isinstance(asof_minute,int) or not 0<=asof_minute<1440):
            raise ValueError('asof_minute outside 24h')
        # No future events can enter a character's knowledge due to same-day
        # arrivals later than the current scene. Unknown time is treated as
        # unknown until tomorrow, rather than inventing an early arrival.
        time_clause = """AND (k.learned_day<? OR
                 (k.learned_day=? AND k.learned_minute IS NOT NULL AND k.learned_minute<=?))
                 AND (f.day<? OR (f.day=? AND (f.minute IS NULL OR f.minute<=?)))"""
        if asof_minute is None:
            time_clause = 'AND k.learned_day<=? AND f.day<=?'
            args=(person_id,asof_day,asof_day)
        else:
            args=(person_id,asof_day,asof_day,asof_minute,asof_day,asof_day,asof_minute)
        with self._db() as db:
            rows=db.execute("""SELECT f.fact_id,f.subject_id,f.predicate,f.object_json,k.learned_day,k.learned_minute,k.channel,
                            f.source_id,f.source_line FROM knowledge k JOIN facts f USING(fact_id)
                            WHERE k.person_id=? AND k.confirmed=1
                            """+time_clause+""" AND f.canon_status='NARRADO' AND f.semantic_review=1
                            ORDER BY k.learned_day,k.learned_minute,f.fact_id""",args).fetchall()
        return [dict(zip(('fact_id','subject_id','predicate','value','learned_day','learned_minute','channel','source_id','line'),
                         (r[0],r[1],r[2],json.loads(r[3]),r[4],r[5],r[6],r[7],r[8]))) for r in rows]

    def viewed_by_reader(self, asof_day, asof_minute=None):
        if asof_minute is not None and (not isinstance(asof_minute,int) or not 0<=asof_minute<1440):
            raise ValueError('asof_minute outside 24h')
        sql="SELECT fact_id,subject_id,predicate,object_json FROM facts WHERE canon_status='NARRADO' AND semantic_review=1 "
        if asof_minute is None:
            sql+="AND day<=? ORDER BY day,minute";args=(asof_day,)
        else:
            sql+="AND (day<? OR (day=? AND minute IS NOT NULL AND minute<=?)) ORDER BY day,minute"
            args=(asof_day,asof_day,asof_minute)
        with self._db() as db:rows=db.execute(sql,args).fetchall()
        return [{'fact_id':r[0],'subject_id':r[1],'predicate':r[2],'value':json.loads(r[3])} for r in rows]

    def record_relationship(self, *, relation_event_id, from_id, to_id, relation, state,
                            since_day, source_id, source_line, canon_status='PENDENTE_APROVACAO',
                            reviewed=False):
        if canon_status not in STATUSES or not source_id or source_line<1 or since_day<1:
            raise ValueError('Relationship requires status and chronological evidence')
        if canon_status=='NARRADO' and not reviewed:
            raise GateError('Cannot canonize relationships by similarity or heuristics')
        with self._db() as db:
            old=db.execute('SELECT from_id,to_id,relation,state,since_day,evidence_source,evidence_line,canon_status,reviewed FROM relationship_events WHERE relation_event_id=?',(relation_event_id,)).fetchone()
            entry=(from_id,to_id,relation,state,since_day,source_id,source_line,canon_status,int(reviewed))
            if old:
                if tuple(old)!=entry:raise ConflictError('Relationship event ID cannot be silently altered')
                return
            db.execute('INSERT INTO relationship_events VALUES(?,?,?,?,?,?,?,?,?,?)',(relation_event_id,*entry))

    def open_thread(self, *, thread_id, kind, title, status, last_narrated_day=None,
                    visibility='BASTIDORES', hypotheses=None, source_id=None, source_line=None):
        if visibility not in SCOPES or not thread_id or not kind or not title:
            raise ValueError('Invalid thread information')
        if status=='NARRADO' and not source_id:
            raise GateError('Narrated thread requires primary evidence')
        with self._db() as db:
            old=db.execute('SELECT thread_id FROM open_threads WHERE thread_id=?',(thread_id,)).fetchone()
            if old:raise ConflictError('Thread version is immutable; record a new event/version')
            db.execute('INSERT INTO open_threads VALUES(?,?,?,?,?,?,?,?,?)',(thread_id,kind,title,status,
                       last_narrated_day,visibility,encoded(hypotheses or {}),source_id,source_line))

    def relationship_state(self, entity_id, asof_day):
        """Return only reviewed narrated relationships, not proposals or duplicates."""
        with self._db() as db:
            rows=db.execute("""SELECT relation_event_id,from_id,to_id,relation,state,since_day
                       FROM relationship_events WHERE (from_id=? OR to_id=?) AND since_day<=?
                       AND reviewed=1 AND canon_status='NARRADO' ORDER BY since_day""",
                       (entity_id,entity_id,asof_day)).fetchall()
        return [dict(zip(('event_id','from_id','to_id','relation','state','day'),row)) for row in rows]

    def stage_chronology(self, classifications):
        with self._db() as db:
            for item in classifications:
                day=int(item['day'])
                if day<1 or item['kind'] not in ('HEADER','ELIPSE','MENCAO','NAO_CERTIFICADO'):
                    raise ValueError('Invalid day classification')
                db.execute('INSERT OR REPLACE INTO chronology VALUES(?,?,?,?,?)',
                           (day,item['kind'],item.get('anchor'),item.get('review_state','PENDENTE'),item.get('note','')))

    def can_publish_public(self, fact_id):
        with self._db() as db:
            r=db.execute('SELECT visibility,canon_status,semantic_review FROM facts WHERE fact_id=?',(fact_id,)).fetchone()
        return bool(r and r[0]=='PUBLICO' and r[1]=='NARRADO' and r[2]==1)

    def summary(self):
        with self._db() as db:
            counts=dict(db.execute('SELECT identity_status,COUNT(*) FROM entities GROUP BY identity_status').fetchall())
            fact_counts=dict(db.execute('SELECT canon_status,COUNT(*) FROM facts GROUP BY canon_status').fetchall())
            days=dict(db.execute('SELECT kind,COUNT(*) FROM chronology GROUP BY kind').fetchall())
        return {'entities':counts,'facts':fact_counts,'days':days}
