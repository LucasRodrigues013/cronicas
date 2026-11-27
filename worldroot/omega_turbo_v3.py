"""Read-only adaptive work planner; never advances the official checkpoint."""
from hashlib import sha256
from time import perf_counter_ns
import json
import re

RISK = re.compile(r'\b(?:dia\s+\d+|gênese|creation|sistema|escolha|opção|cânone|morte|morreu|retcon|segredo)\b', re.I)
ROLES = {"## Prompt:": "Prompt", "## Response:": "Response"}


def _hash(text):
    return sha256(text.encode('utf-8')).hexdigest()


def prepare_one(cache, macro, cursor, target=300, dense_target=150, context=12):
    """Reuse V2 verified SourceCache; preserve the queue's macro geometry."""
    started = perf_counter_ns()
    lo, hi = macro['start'], macro['end']
    if any(type(x) is not int for x in (lo, hi, cursor, target, dense_target, context)):
        raise ValueError('integer geometry required')
    if not (1 <= lo == cursor <= hi and hi-lo+1 == macro['lines'] and 1 <= dense_target <= target <= 600 and 0 <= context <= 50):
        raise ValueError('invalid cursor or geometry')
    lines, roles, _, source_hash = cache.get(macro['source'])
    if hi > len(lines) or len(lines) != len(roles):
        raise ValueError('source bounds')
    units = []
    at = lo
    while at <= hi:
        role = roles[at-1]
        stop = min(at+target-1, hi)
        for n in range(at+1, stop+1):
            if roles[n-1] != role or lines[n-1].strip() in ROLES:
                stop = n-1
                break
        probe = lines[at-1:stop]
        dense = role == 'Prompt' or sum(bool(RISK.search(line)) for line in probe) >= 5
        if dense:
            stop = min(stop, at+dense_target-1)
        left, right = at, stop
        while left > max(1, at-context) and roles[left-2] == role and lines[left-1].strip() not in ROLES:
            left -= 1
        while right < min(len(lines), stop+context) and roles[right] == role and lines[right].strip() not in ROLES:
            right += 1
        core = _hash('\n'.join(lines[at-1:stop]))
        window = _hash('\n'.join(lines[left-1:right]))
        key = _hash(json.dumps(['OMEGA_TURBO_V3', macro['id'], source_hash, at, stop, role, core, left, right, window], ensure_ascii=False, separators=(',', ':')))
        units.append(dict(id=key, start=at, end=stop, role=role, sha256=core, context_start=left, context_end=right, context_sha256=window, risk_hint='dense' if dense else 'standard'))
        at = stop+1
    if sum(u['end']-u['start']+1 for u in units) != macro['lines']:
        raise ValueError('coverage mismatch')
    return dict(macro_id=macro['id'], source_sha256=source_hash, range=[lo, hi], units=units, official_unit_seal=macro.get('unit_seal'), elapsed_ns=perf_counter_ns()-started, status='PREPARATION_ONLY', canon_changed=False, semantic_certification=False, promotion=False)
