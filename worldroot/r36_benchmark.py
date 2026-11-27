"""Experimental benchmark metadata validation. No story cases, prompts or gold.
Partitioning uses caller-supplied private metadata; never export reserved labels.
"""
from collections import Counter
from .semantic_queue import seal
from .r36_evaluation import HEX

TARGETS = {"memory":12,"identity":9,"canon_time":9,"literary":6,
           "world":6,"powers":6,"agency":6,"adversarial":6}
SPLITS = {"development":36,"validation":12,"reserved":12}
FIELDS = {"id","category","family","episodes","entities","source_pins","split","severity"}
SEVERITIES = {"critical","major","minor"}

def require(ok,msg):
    if not ok:raise ValueError(msg)
def digest(x):
    return isinstance(x,str) and HEX.fullmatch(x) is not None
def token(x):
    return isinstance(x,str) and bool(x) and x==x.strip()
def tokens(xs):
    return isinstance(xs,list) and bool(xs) and all(token(x) for x in xs) and len(xs)==len(set(xs))
def validate_inventory(rows, exact=True):
    """Reject group leakage, including indirect connections through shared tags.
    The caller must assign meaningful entity/episode/family tags; no semantic inference.
    source_pins bind raw source identifiers only; raw-file verification is separate.
    """
    require(isinstance(rows,list) and bool(rows),"Empty inventory")
    ids=set();groups={};counts=Counter();splits=Counter()
    for r in rows:
        require(isinstance(r,dict) and set(r)==FIELDS,"Invalid or secret-bearing metadata")
        require(token(r["id"]) and r["id"] not in ids,"Duplicate/invalid case")
        ids.add(r["id"])
        require(r["category"] in TARGETS and r["split"] in SPLITS and r["severity"] in SEVERITIES,"Invalid classification")
        require(token(r["family"]),"Missing family")
        require(tokens(r["episodes"]) and tokens(r["entities"]),"Missing group tags")
        require(isinstance(r["source_pins"],list) and bool(r["source_pins"]) and all(digest(p) for p in r["source_pins"]) and len(set(r["source_pins"]))==len(r["source_pins"]),"Invalid source pins")
        for tag in [("family",r["family"]),*(("episode",e) for e in r["episodes"]),*(("entity",e) for e in r["entities"]),*(("source",p) for p in r["source_pins"])]:
            require(groups.setdefault(tag,r["split"])==r["split"],"Cross-split group leakage")
        counts[r["category"]]+=1;splits[r["split"]]+=1
    if exact:
        require(dict(counts)==TARGETS and dict(splits)==SPLITS,"Target distribution mismatch")
    else:
        require(all(v<=TARGETS[k] for k,v in counts.items()) and all(v<=SPLITS[k] for k,v in splits.items()),"Target capacity exceeded")
    return {"cases":len(rows),"categories":dict(counts),"splits":dict(splits),
            "inventory_sha256":seal(sorted(rows,key=lambda r:r["id"])),
            "structural_only":True,"semantic_certification":False}

def generation_case(meta,prompt):
    """Strict projection: only case id and prompt; never pass labels or metadata.
    Reserved generation requires an external authorized blinded executor.
    Caller must separately verify prompt has no answer or identifying clues.
    """
    require(isinstance(meta,dict) and set(meta)==FIELDS,"Invalid metadata")
    require(meta["split"] in ("development","validation"),"Reserved case requires separate custody")
    require(isinstance(prompt,str) and bool(prompt.strip()),"Missing prompt")
    return {"case_id":meta["id"],"prompt":prompt}

def factual_metrics(outcomes):
    require(isinstance(outcomes,list) and bool(outcomes),"Missing outcomes")
    allowed={"CORRECT","INCORRECT","ABSTAIN","INCONCLUSIVE"}
    require(all(isinstance(x,str) and x in allowed for x in outcomes),"Invalid outcome")
    c=Counter(outcomes);n=len(outcomes);decisive=c["CORRECT"]+c["INCORRECT"]
    return {"n":n,"counts":{k:c[k] for k in sorted(allowed)},
            "accuracy_all":c["CORRECT"]/n,"coverage":decisive/n,
            "accuracy_decisive":c["CORRECT"]/decisive if decisive else None,
            "semantic_certification":False}
