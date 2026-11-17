"""Non-destructive editorial preflight for new parts (not a prose generator)."""
from __future__ import annotations
import re
from dataclasses import dataclass
from .ledger import GateError

ENDING_BOOK = re.compile(r'FIM\s+DO\s+LIVRO\s+[IVX]+',re.I)
ENDING_PART = re.compile(r'FIM\s+DA\s+PARTE',re.I)

@dataclass(frozen=True)
class Choice:
    number: int
    title: str
    description: str
    is_special: bool=False
    is_free: bool=False


def validate_interface(*, prose: str, book_closed: bool, chapter: int, part: str,
                       choices: list[Choice], actual_save_receipt: dict | None,
                       perspective: str='CHARACTER', trusted_receipt_verifier=None):
    errors=[];notices=[]
    if ENDING_BOOK.search(prose) and not book_closed:
        errors.append('Cannot render FIM DO LIVRO without approved book-close event')
    if book_closed and not ENDING_BOOK.search(prose):
        notices.append('Book closure has no end marker; author review')
    if chapter<1 or not part:errors.append('Missing chapter/part')
    if [c.number for c in choices]!=[1,2,3,4,5]:errors.append('Five numbered choices (including free) required')
    elif not (choices[3].is_special and choices[4].is_free):
        errors.append('Fourth special and fifth free action must remain distinct')
    if any(not x.title or (not x.description and not x.is_free) for x in choices):
        errors.append('Choices require meaningful nonempty descriptions')
    if perspective not in ('CHARACTER','READER','EDITORIAL'):
        errors.append('Unknown audience context')
    verified_remote=False
    if actual_save_receipt:
        if (actual_save_receipt.get('verification')!='google_drive_get_media'
                or not actual_save_receipt.get('file_id') or not actual_save_receipt.get('sha256')):
            errors.append('Unverified receipt must not be rendered as saved')
        elif trusted_receipt_verifier is None:
            errors.append('Caller-provided receipt alone is not proof of remote readback')
        else:
            try:
                verified_remote=bool(trusted_receipt_verifier(actual_save_receipt))
            except Exception:
                verified_remote=False
            if not verified_remote:
                errors.append('Trusted receipt verification failed')
    repetitive={}
    for phrase in ('começou a rir','uma pausa.','um silêncio.','então sorriu'):
        total=len(re.findall(re.escape(phrase),prose,re.I));words=max(1,len(prose.split()))
        rate=total/(words/10000)
        if rate>12 and total>=3:
            repetitive[phrase]={'count':total,'per_10000_words':round(rate,1)}
    if repetitive:notices.append('Review repeated stock expressions: '+', '.join(repetitive))
    return {'ok':not errors,'errors':errors,'notices':notices,
            'save_label':('DRIVE CONFERIDO' if verified_remote and not errors else 'SALVAMENTO EXTERNO PENDENTE'),
            'repetitions':repetitive}


def narrator_policy():
    """Machine-readable rules applied by preflight prompts, never forced outcomes."""
    return {
      'reaction':{'w0':'local', 'w1':'neighbors', 'w2':'regional', 'w3':'national',
                  'w4':'continental', 'w5':'transcontinental',
                  'require':['witness','sender','route','propagation_delay','interest','reaction_uncertainty'],
                  'prohibition':'no instant omniscient world reactions'},
      'antagonists':{'tiers':list(range(8)),'no_genesis_nerf':True,
                     'valid_axes':['legitimacy','information','time','agency','scale','trade'],
                     'prohibition':'no forced return/revival/escape after canonical defeat'},
      'choices':{'numbers':[1,2,3,4,5],'fourth_special':True,'fifth_free':True,
                 'honest_consequences':True,'no_automatic_punishment_for_fourth':True},
      'mystery':{'progress_modes':['new_evidence','contradiction','effect','reveal','negative_result'],
                 'do_not_force_every_scene':True},
      'voice':{'allow_humor':True,'retain_romance':True,'autonomous_npcs':True,
                'no_mechanical_repetition':True},
      'canon':{'planned_is_not_narrated':True,'end_book_author_approval':True,
                 'next_day_requires_choice':True}
    }
