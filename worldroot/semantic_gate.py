"""Evidence-first guard on author-approved episode event publication.

This checks that every proposed canonical event cites an exact anchored line
of the immutable episode. It does NOT certify the semantic truth of a summary
or replace NPC-knowledge review; those still require editorial analysis.
"""
from __future__ import annotations

from hashlib import sha256
from .ledger import GateError, ConflictError, IDENTIFIER

ALLOWED_VISIBILITY = frozenset(('PUBLICO', 'PRIVADO_PERSONAGEM', 'BASTIDORES'))


def require_reviewed_event_evidence(draft, reviewed_events):
    if not isinstance(reviewed_events, list) or not reviewed_events:
        raise GateError('A canonical closure requires non-empty reviewed events')
    literal = draft.full_text
    sha = sha256(literal.encode('utf-8')).hexdigest()
    lines = literal.splitlines()
    seen = set()
    for event in reviewed_events:
        if not isinstance(event, dict):
            raise GateError('Event must be a structured object')
        event_id = event.get('event_id')
        if not isinstance(event_id, str) or not IDENTIFIER.fullmatch(event_id):
            raise GateError('Stable event identity required')
        if event_id in seen:
            raise ConflictError('Duplicate reviewed event identity')
        seen.add(event_id)
        if event.get('canon_status') != 'NARRADO':
            raise GateError('Cannot promote unreviewed or merely planned event')
        if event.get('visibility') not in ALLOWED_VISIBILITY:
            raise GateError('Every event needs a validated knowledge/visibility layer')
        source = event.get('source')
        if not isinstance(source, dict) or source.get('sha256') != sha:
            raise GateError('Event must cite the exact current episode SHA256')
        line = source.get('line')
        anchor = source.get('literal_anchor')
        if type(line) is not int or not (1 <= line <= len(lines)):
            raise GateError('Event source line is missing/out of bounds')
        if not isinstance(anchor, str) or len(anchor.strip()) < 8 or anchor not in lines[line - 1]:
            raise GateError('Event source literal anchor does not match the cited line')
        if not isinstance(event.get('summary_candidato'), str) or len(event['summary_candidato'].strip()) < 15:
            raise GateError('Event statement is missing; cannot approve an empty event')
    return {'verified_evidence_anchors': len(seen), 'episode_sha256': sha,
            'note': 'Literal provenance verified; semantic meaning and NPC knowledge still require editorial judgment'}
