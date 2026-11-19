"""WORLDROOT literary advisory: reproducible signal, never automated taste approval."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from validate_episode_archive import verify_one, ArchiveInvalid

LUCAS=re.compile(r"^\s*(?:\*\*)?LUCAS\s*[—–-](?:\*\*)?\s*(.*)$",re.I)
def _dialogue(t):
    result=[]
    for i,line in enumerate(t.splitlines(),1):
        m=LUCAS.match(line)
        if m:
            result.append((i,m.group(1).replace("**","").strip()))
    return result
def metrics(raw):
    lines=_dialogue(raw)
    enough=[(i,t) for i,t in lines if sum(ch.isalpha() for ch in t)>=6]
    loud=[i for i,t in enough if any(ch.isalpha() for ch in t) and
          t==t.upper()]
    return {
        "lucas_dialogue_lines":len(lines),
        "lucas_substantial_dialogue_lines":len(enough),
        "lucas_all_caps_lines":len(loud),
        "all_caps_share_of_substantial_lucas_lines":round(len(loud)/len(enough),3) if enough else None,
        "tenderness_and_intent_not_mechanically_testable":True,
    }
def review(root:Path,eid:str,reference="LV-C15-PII-D529-AUTHOR-SOURCE",*,write=False):
    path=root/"episodes"/eid/"draft/narrativa_integral.md"
    rpath=root/"episodes"/reference/"draft/narrativa_integral.md"
    if not path.is_file() or not rpath.is_file():
        raise ArchiveInvalid("Missing original for character voice comparison")
    actual=path.read_bytes()
    saved=verify_one(path.parent/"manifesto_imutavel.json")
    if saved["sha256"]!=hashlib.sha256(actual).hexdigest():
        raise ArchiveInvalid("Narrative changed since immutable package")
    current=metrics(actual.decode("utf-8"))
    prior=metrics(rpath.read_text(encoding="utf-8"))
    item={
        "schema":"worldroot-advisory-character-voice-v1",
        "episode_id":eid,"source_sha256":saved["sha256"],
        "reference_episode_id":reference,
        "current":current,"baseline":prior,
        "critic_source":"editorial/feedback/2026-11-19-lucas-carisma-strong-kind-loving.json",
        "status":"REQUIRES_HUMAN_LITERARY_REVIEW",
        "human_review_prompts":[
            "Lucas remains strong, creative, generous, charming, friendly and deeply loving, not rude",
            "Jokes should bond friends, not humiliate or dictate their choices",
            "Read the interactions with Miren: warmth, independent agency, affection, emotional growth",
            "Use shouting/caps to punctuate real moments, not every reaction",
            "Listen before assigning others office or demanding their compliance",
            "Preserve his expressive voice, GÊNESE and existing story: no nerf or retcon"
        ],
        "measurement_limitations":[
            "Uppercase ratio is an imperfect text-only signal, not a pass/fail quality score",
            "Reference D529 uses rich DIL/Markdown; D539-540 may use export text",
            "No unseen UI fidelity or actual human compassion can be proven by regex"
        ]
    }
    if write:
        p=root/"editorial/audits"/(eid+"-voice.json")
        p.parent.mkdir(parents=True,exist_ok=True)
        raw=(json.dumps(item,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n").encode()
        if p.exists() and p.read_bytes()!=raw:
            raise ArchiveInvalid("Immutable editorial audit already differs")
        p.write_bytes(raw)
    return item
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive-root",type=Path,default=Path("."))
    p.add_argument("--episode-id",required=True)
    p.add_argument("--write",action="store_true")
    a=p.parse_args()
    try:
        res=review(a.archive_root,a.episode_id,write=a.write)
        print(json.dumps(res,ensure_ascii=False,sort_keys=True))
    except (ArchiveInvalid,OSError,ValueError,TypeError,KeyError) as exc:
        print("WORLDROOT_VOICE_AUDIT_BLOCKED:",str(exc),file=sys.stderr)
        raise SystemExit(1)
if __name__=="__main__":
    main()
