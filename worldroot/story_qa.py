"""Pre-publication narrative package regression gates.

Static and metadata-based checks only. They cannot infer full literary meaning
or prove unseen model generations. Use a human reviewer for semantics and voice.
No narrative data or private story canon is stored in this code.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from .narrative import Choice, validate_interface

CLOCK = re.compile(r'^(?:[01]\d|2[0-3])h[0-5]\d$')
ENDING_PART = re.compile(r'FIM\s+DA\s+PARTE\b', re.IGNORECASE)
SAVED_CLAIMS = re.compile(r'\b(?:salvo\s+no\s+drive|continuidade\s+registrada\s+e\s+conferida|c[aâ]none\s+publicado)\b',re.I)
SIMULATED = {'SIMULADO','RASCUNHO'}


def clock_minutes(value: str) -> int:
    if not isinstance(value,str) or not CLOCK.fullmatch(value):
        raise ValueError(f'Invalid canonical clock {value!r}; expected HHhMM')
    hour, minute = value.split('h')
    return 60 * int(hour) + int(minute)


@dataclass(frozen=True)
class FactUsage:
    fact_id: str
    speaker_id: str
    # Speaker reports the knowledge as their own. Narrator/reader-only shots
    # should not create speaker claims.


@dataclass(frozen=True)
class Scene:
    scene_id: str
    day: int
    hour: str
    place: str
    prose: str
    viewpoint: str = 'CHARACTER'
    claimed_knowledge: tuple[FactUsage, ...] = ()


@dataclass(frozen=True)
class Generation:
    generation_id: str
    book: str
    chapter: int
    part: str
    status: str
    scenes: tuple[Scene, ...]
    choices: tuple[Choice, ...]
    closing_text: str
    last_canon_day: int
    last_canon_clock: str
    book_closed: bool = False
    author_approved: bool = False
    external_receipt: dict | None = None
    forbidden_markers: tuple[str, ...] = ()
    min_scenes: int = 1


def validate_generation(g: Generation, memory=None) -> dict:
    """Fails closed for time, known SPOILERS and storage misrepresentation.

    `claimed_knowledge` annotations are explicit evidence; not extracted from free
    text automatically, and therefore NOT semantic completeness certification.
    """
    errors, warnings, assertions = [], [], []
    if not g.generation_id or not g.book or g.chapter<1 or not g.part:
        errors.append('Missing stable generation/book/chapter/part identity')
    if g.status not in ('SIMULADO','RASCUNHO','NARRADO'):
        errors.append('Invalid generation status')
    if g.status=='NARRADO' and not g.author_approved:
        errors.append('NARRADO requires explicit author approval')
    if g.book_closed and not g.author_approved:
        errors.append('Closing a book requires explicit author approval')
    if g.status in SIMULATED and g.author_approved:
        warnings.append('Author approval attached to non-narrated simulation: verify intent')
    if len(g.scenes)<g.min_scenes:
        errors.append('Insufficient scene count for this QA profile')
    if not g.scenes:
        errors.append('No narrative scenes supplied')
    try:
        last_key=(g.last_canon_day,clock_minutes(g.last_canon_clock))
    except (TypeError,ValueError) as e:
        errors.append(str(e));last_key=None
    keys=[];scene_ids=set();body=[]
    for scene in g.scenes:
        if not scene.scene_id or scene.scene_id in scene_ids:
            errors.append('Missing or duplicate scene ID')
        scene_ids.add(scene.scene_id)
        if not scene.place or not scene.prose.strip():
            errors.append(f'{scene.scene_id}: scene must have place and full text')
        if scene.viewpoint not in ('CHARACTER','READER','EDITORIAL'):
            errors.append(f'{scene.scene_id}: invalid viewpoint')
        try:
            current=(scene.day,clock_minutes(scene.hour))
            keys.append(current)
            if last_key and current < last_key:
                errors.append(f'{scene.scene_id}: retrograde relative to canon checkpoint')
            if last_key and current[0]>last_key[0]+1 and g.status=='NARRADO':
                errors.append(f'{scene.scene_id}: uncontrolled time jump from canonical head')
        except (TypeError,ValueError) as e:
            errors.append(f'{scene.scene_id}: {e}')
        for claim in scene.claimed_knowledge:
            if memory is None:
                warnings.append(f'{scene.scene_id}: knowledge claim not checked; no memory adapter')
                continue
            if claim.speaker_id=='READER':
                # The reader can know things characters cannot, but the text's
                # perspective must be explicitly reader/editorial.
                if scene.viewpoint not in ('READER','EDITORIAL'):
                    errors.append(f'{scene.scene_id}: reader-only fact in character viewpoint')
                continue
            if scene.day<1 or not CLOCK.fullmatch(scene.hour):
                continue
            # A minute-specific asof prevents same-day late learning leaking into
            # earlier scenes. Older memory adapters accept only day: fail closed.
            try:
                known={v['fact_id'] for v in memory.known_by(claim.speaker_id,scene.day,clock_minutes(scene.hour))}
            except TypeError:
                errors.append(f'{scene.scene_id}: memory adapter lacks minute-specific knowledge checks')
                continue
            if claim.fact_id not in known:
                errors.append(f'{scene.scene_id}: character {claim.speaker_id} cannot cite unknown fact {claim.fact_id}')
        body.append(scene.prose)
    if keys!=sorted(keys):
        errors.append('Scene order has day/time reversal')
    if g.status=='NARRADO' and not g.book_closed and len(g.scenes)>0:
        # Time may proceed organically, but author cannot be pushed into next day
        # without selecting the new part.
        warnings.append('Check that the chosen branch and transition are recorded')
    prose='\n\n'.join(body+[g.closing_text])
    for marker in g.forbidden_markers:
        if marker.strip() and re.search(r'(?i)(?<!\w)'+re.escape(marker)+r'(?!\w)',prose):
            errors.append(f'Forbidden universe/secret marker found: {marker}')
    if g.status in SIMULATED and SAVED_CLAIMS.search(prose):
        errors.append('Simulation falsely claims external save or canon publication')
    if g.status in SIMULATED and g.external_receipt is not None:
        errors.append('Simulated prose must not carry a canonical Drive receipt')
    if not g.book_closed and not ENDING_PART.search(g.closing_text):
        errors.append('Open book should end with explicit FIM DA PARTE')
    ui=validate_interface(prose=prose,book_closed=g.book_closed,chapter=g.chapter,
                          part=g.part,choices=list(g.choices),actual_save_receipt=g.external_receipt)
    errors.extend(ui['errors'])
    warnings.extend(ui['notices'])
    # A literal line asserting real persistence is never proof of a Drive receipt.
    if SAVED_CLAIMS.search(prose) and g.external_receipt is None:
        errors.append('Text declares persistence without verified receipt')
    assertions.append('Human literary review required: tone, pacing, autonomy, dialogue, world reaction, Genesis')
    assertions.append('Fact annotations must be independently checked against the actual dialogue')
    return {'ok':not errors,'errors':errors,'warnings':warnings,
            'assertions':assertions,'scene_count':len(g.scenes),'words':sum(len(x.split()) for x in body),
            'save_label':'SALVAMENTO EXTERNO PENDENTE' if g.status in SIMULATED else ui['save_label']}
