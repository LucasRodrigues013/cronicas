"""Read-only R35 regression replay on the complete 40-part Livro VI corpus.
Do not import or reproduce private narrative into main, logs contain metrics only.
"""
import argparse,json,hashlib
from pathlib import Path
from statistics import mean
from worldroot.git_cycle import verify_episode
from worldroot.r35_longform import volume_check

def run(root):
    head=json.loads((root/"canon/HEAD.json").read_text())
    resume=json.loads((root/"ops/RESUME.json").read_text())
    ident=head["episode_id"];ids=[];closures={}
    while ident.startswith("LVI-"):
        j=json.loads((root/"canon/episodes"/(ident+".json")).read_text())
        closures[ident]=j;ids.append(ident);ident=j["previous_episode_id"]
    ids.reverse()
    pending=resume.get("latest_unclosed_draft")
    if pending and pending["episode_id"].startswith("LVI-"):ids.append(pending["episode_id"])
    rows=[];before={}
    for ident in ids:
        draft,manifest=verify_episode(root,ident)
        meta=draft.metadata
        if meta["chapter"]>8:continue
        prior=closures.get(ident,{}).get("previous_episode_id")
        if not prior:
            index=ids.index(ident);prior=ids[index-1] if index else None
        option=closures.get(prior,{}).get("chosen_option",1)
        if type(option) is not int or option not in range(1,6):option=1
        result=volume_check(draft.prose,meta["part"],option)
        folder=root/"episodes"/ident/"draft"
        for n in manifest["artifacts"]:before[folder/n]=hashlib.sha256((folder/n).read_bytes()).hexdigest()
        rows.append({"id":ident,"chapter":meta["chapter"],"part":meta["part"],"day":meta["day"],"revision":meta.get("worldroot_revision"),**result})
    assert len(rows)==40, f"Expected 40 selected Livro VI parts, found {len(rows)}"
    late=[x for x in rows if 572<=x["day"]<=578]
    assert len(late)==7 and all("R35_DEPTH" in " ".join(x["issues"]) for x in late),"Shortening regression not detected"
    for day in (568,571):
        match=next(x for x in rows if x["day"]==day)
        assert not any("R35_DEPTH" in i for i in match["issues"]),f"Historical long reference {day} falsely fails depth"
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==v for p,v in before.items()),"Historical source mutated"
    assert json.loads((root/"canon/HEAD.json").read_text())==head and json.loads((root/"ops/RESUME.json").read_text())==resume,"HEAD or resume changed"
    chapters=[{"chapter":i,"parts":5,"words":sum(x["words"] for x in rows if x["chapter"]==i),"paragraphs":sum(x["paragraphs"] for x in rows if x["chapter"]==i)} for i in range(1,9)]
    return {"status":"READ_ONLY_CORPUS_REPLAY_OK","episodes":len(rows),"source_files_verified":len(before),"chapter_totals":chapters,"short_parts_detected":len(late),"pre_break_mean":round(mean(x["words"] for x in rows if x["day"]<572),1),"r34_mean":round(mean(x["words"] for x in rows if x["revision"]==34),1),"legacy_reference_results":[x for x in rows if x["day"] in (568,571)],"late_parts":[{k:x[k] for k in ("id","words","floor","issues")} for x in late],"canon_changed":False,"semantic_certification":False}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--archive-root",type=Path,required=True);a=p.parse_args();print(json.dumps(run(a.archive_root),ensure_ascii=False))
