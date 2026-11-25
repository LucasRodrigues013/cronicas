"""R33 curated retrieval route: reuse approved, verified registries, not benchmark answers."""
from __future__ import annotations
from .literary_experience import source_registry
from .deep_recovery import tokens,STOP,expand_groups
from .history_index import read_verified_sources
from pathlib import Path

def build_cards(root):
    root=Path(root);reg=source_registry(root)
    _,raw=read_verified_sources(root);bodies={m["source_name"]:t for m,t in raw}
    cards=[]
    def add(name,meta,source):
        body=bodies.get(source.get("source_name"))
        a=source.get("anchor")
        if not body or not a or body.count(a)!=1:return
        pos=body.index(a);lo=body[:pos].count("\n")+1
        cards.append({"card":name,"source":source["source_name"],"line_start":lo,"line_end":lo+a.count("\n"),"role":source.get("role","Response"),"anchor":a,"metadata":meta,"status":"CURATED_REFERENCE_NOT_CANON"})
    for x in reg["scenes"]:
        if x.get("proof"):add("scene:"+x["id"],x["title"]+" "+x["why"]+" "+str(x["day"]),x["source"])
    for p in reg["characters"]:
        for i,o in enumerate(p["observations"]):
            if o.get("proof"):add("identity:"+p["id"]+":"+str(i),p["name"]+" "+" ".join(p.get("aliases",[]))+" "+o["field"]+" "+o["value"],o["source"])
    return cards
def search_cards(cards,query,role=None,limit=5):
    if type(limit) is not int or not 1<=limit<=10:raise ValueError("Card limit")
    terms=set(tokens(query))-STOP
    if not terms:return []
    expanded=expand_groups(terms)
    scored=[]
    for c in cards:
        if role and c["role"]!=role:continue
        meta=set(tokens(c["metadata"]));body=set(tokens(c["anchor"]))
        direct=len(terms&meta)*3+len(terms&body)
        extra=sum(bool((expanded.get(t,set())&(meta|body))) for t in terms-(meta|body))
        if direct or extra:scored.append((direct+.25*extra,c))
    return [c for _,c in sorted(scored,key=lambda pair:(-pair[0],pair[1]["card"]))[:limit]]
