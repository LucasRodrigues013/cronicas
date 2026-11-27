"""Read-only source indexing for the R36 author gate; no semantic certification."""
import hashlib
import json
import re
from pathlib import Path
from .natural_codex import CHAR_FIELDS, validate_fields, git_blob, public_fields

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def verify_native_candidates(doc, source):
    lines = source.decode("utf-8").split("\n")
    assert sha(source) == doc["source_sha256"]
    assert doc["canon_changed"] is False and doc["production_activated"] is False
    assert doc["semantic_certification"] is False
    ids, recovered, pending, anchors = set(), 0, 0, 0
    for card in doc["characters"] + doc["records"]:
        assert card["id"] not in ids and card["status"] == "AUTHOR_GATE_PENDING"
        ids.add(card["id"])
        fields = validate_fields(card["fields"], CHAR_FIELDS if card in doc["characters"] else ())
        assert not public_fields(fields)
        for value in fields.values():
            assert value["scope"] == "AUTHOR_ONLY"
            if value["status"] == "PENDENTE_FONTE":
                pending += 1
                continue
            assert value["status"] == "RECUPERADO"
            recovered += 1
            assert isinstance(value["origin"], list) and value["origin"]
            for row in value["origin"]:
                line = row["line"]
                assert type(line) is int and 1 <= line <= len(lines)
                assert lines[line-1] == row["anchor"] and row["anchor"].strip(), (card["id"], line)
                assert row.get("source_sha256", sha(source)) == sha(source) if "source_sha256" in row else True
                anchors += 1
    return {"cards":len(ids),"recovered":recovered,"pending":pending,"anchor_checks":anchors}

def index_corpus(ar, stage):
    inventory = json.loads((stage/"r36-multidimensional-lot-02-inventory.json").read_bytes())
    reg = ar/"editorial/registries"
    chars = json.loads((reg/"r35-natural-completion-d579-v14.json").read_bytes())["characters"]
    world = json.loads((reg/"r35-world-completion-d579-v12.json").read_bytes())["records"]
    sources, first = [], []
    for entry in inventory["source_inventory"]:
        raw = (ar/entry["path"]).read_bytes()
        assert git_blob(raw) == entry["blob"]
        if ".part-" in entry["path"]: first.append(raw)
        else: sources.append((entry["path"],raw,None))
    first = b"".join(first)
    assert sha(first) == "bb43d493ef3c28391345af7cd319e62af2f99f4f51b417bebb129fad6786cc4b"
    sources.insert(0,("D001-D383", first,None))
    bootstrap = ar/"episodes/bootstrap/LV-C15-PI-D528/fonte_literal_drive_D528.txt"
    raw = bootstrap.read_bytes()
    assert git_blob(raw) == "d7016b84eb7477b0341904da616e06035292d8f3"
    sources.append((str(bootstrap.relative_to(ar)),raw,None))
    for entry in inventory["closed_episode_inventory"]:
        receipt = (ar/"canon/episodes"/(entry["episode"]+".json")).read_bytes()
        raw = (ar/entry["source_path"]).read_bytes()
        assert git_blob(receipt) == entry["receipt_blob"]
        assert git_blob(raw) == entry["source_blob"]
        assert sha(raw) == json.loads(receipt)["story_sha256"], entry["episode"]
        sources.append((entry["episode"],raw,True))
    candidate_results = {}
    for suffix in ("04-native-candidates","05-discoveries"):
        doc = json.loads((stage/("r36-multidimensional-lot-"+suffix+".json")).read_bytes())
        candidate_results[suffix] = verify_native_candidates(doc,first)
    names, profiles = {}, {}
    for row in chars+world:
        ident = row["id"]
        profiles[ident] = {"mentions":0,"sources":{},"semantic_review_pending":True}
        name = row.get("name") or row.get("display_name") or row["fields"].get("identity",{}).get("value")
        if isinstance(name,str) and 2 <= len(name) <= 100:
            names.setdefault(name.casefold(),[]).append(ident)
    pattern = re.compile(r"(?<!\w)(?:"+"|".join(re.escape(n) for n in sorted(names,key=len,reverse=True))+r")(?!\w)",re.I)
    reports, unknown = [], {}
    heading = re.compile(r"^\s*(?:[#*>|]+\s*)?(?:DIA\s+|D)(\d{1,3})(?!\d)", re.I)
    speaker = re.compile(r"^\s*(?:>\s*)?\*\*([A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ0-9 '-]{1,50})\s*—\*\*")
    for label,raw,closed in sources:
        day, scene, chapter = None, None, None
        lines = raw.decode("utf-8").split("\n")
        for n,line in enumerate(lines,1):
            m=heading.match(line)
            if m and 1 <= int(m[1]) <= 579: day,scene=int(m[1]),n
            if re.match(r"^\s*#{1,5}\s+.*(?:CAPÍTULO|CAPITULO|CHAPTER)",line,re.I): chapter=n
            for name in set(x.group().casefold() for x in pattern.finditer(line)):
                ids=names.get(name,[])
                if len(ids)!=1: continue
                p=profiles[ids[0]]
                p["mentions"]+=1
                s=p["sources"].setdefault(label,{"count":0,"first_line":n,"first_anchor_sha256":sha(line.encode()),"days":[],"chapter_heading_lines":[],"scene_heading_lines":[]})
                s["count"]+=1
                s["last_line"]=n
                if day and day not in s["days"]: s["days"].append(day)
                if chapter and chapter not in s["chapter_heading_lines"]: s["chapter_heading_lines"].append(chapter)
                if scene and scene not in s["scene_heading_lines"]: s["scene_heading_lines"].append(scene)
            m=speaker.match(line)
            if m:
                name=m[1].strip().casefold()
                if name not in names and not re.fullmatch(r"[ivxlcdm]+",name):
                    u=unknown.setdefault(name,{"count":0,"first_source":label,"first_line":n,"first_anchor_sha256":sha(line.encode()),"status":"UNRESOLVED_LEXICAL_LABEL"})
                    u["count"]+=1
        reports.append({"source":label,"sha256":sha(raw),"lines":len(lines),"closed_receipt_verified":closed})
    return {"schema":"worldroot-r36-corpus-index-v1","archive":inventory["archive"],"sources":reports,"profiles":profiles,"unresolved_speaker_labels":unknown,"candidate_validation":candidate_results,"counts":{"logical_sources":len(reports),"closed_receipts":sum(x["closed_receipt_verified"] is True for x in reports),"lines":sum(x["lines"] for x in reports),"profiles":len(profiles),"profiles_with_name_hits":sum(x["mentions"]>0 for x in profiles.values()),"unresolved_speaker_labels":len(unknown)},"production_hold":True,"canon_changed":False,"semantic_certification":False}

if __name__ == "__main__":
    import sys
    archive, stage = map(Path, sys.argv[1:3])
    report = index_corpus(archive,stage)
    out=stage/"r36-multidimensional-lot-06-corpus-index.json"
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("R36_CORPUS_RESULT",json.dumps({"counts":report["counts"],"candidate_validation":report["candidate_validation"],"sha256":sha(out.read_bytes())},sort_keys=True))
