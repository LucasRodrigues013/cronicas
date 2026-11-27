"""Thin opt-in bridge for existing evaluation components. Never generates story or writes canon."""
from collections import Counter
from . import r36_recovery as recovery
from .r36_benchmark import validate_inventory,generation_case
from .r36_trust import authenticate,verify,require,digest
from .semantic_queue import seal

VERSION="r36-e7-operational-v1"
def run_case(inventory,inventory_sha,case_id,prompt,preparation_sha,policy_sha,summary_key,**kwargs):
    """Accept a supplied candidate, not a generated one. Prep and policy pins
    are declarations, not proof of R33 execution. Reserved cases are excluded.
    Summary stays private, never feeds adaptation automatically.
    """
    checked=validate_inventory(inventory,exact=False)
    require(checked["inventory_sha256"]==inventory_sha,"Inventory pin mismatch")
    matches=[r for r in inventory if r["id"]==case_id]
    require(len(matches)==1,"Unknown case")
    meta=matches[0]
    projected=generation_case(meta,prompt)
    require(digest(preparation_sha) and digest(policy_sha),"Preparation/policy pins required")
    require(summary_key not in (kwargs["authority_key"],kwargs["receipt_key"]),"Separate summary key required")
    # Verify caller-approved source manifest, then recovery verifies raw bytes.
    approved=verify(kwargs["authority"],"source-authority",kwargs["authority_key"])
    require(set(meta["source_pins"])=={s["raw_sha256"] for s in approved["manifest"]["sources"]},"Case source pins mismatch")
    require(isinstance(kwargs["run_nonce"],str) and 16<=len(kwargs["run_nonce"])<=128,"Run nonce required")
    binding={"schema":VERSION,"inventory_sha":inventory_sha,"case_id":case_id,"split":meta["split"],
             "preparation_sha":preparation_sha,"policy_sha":policy_sha,"input_sha":seal(projected),
             "candidate_sha":seal(kwargs["candidate"]),"judge":kwargs["judge"],
             "engine_revision":kwargs["scope"]["engine_revision"],"nonce":kwargs["run_nonce"]}
    result=recovery.run(**{**kwargs,"run_nonce":seal(binding)})
    payload={"binding":binding,"result":result,"generation_executed":False,
             "preparation_execution_verified":False,"feedback_eligible":False,
             "production_hold":True,"semantic_certification":False}
    return authenticate("operational-summary",payload,summary_key)

def longitudinal(summaries,key,expected,inventory_sha,policy_sha,engine_revision):
    """Ordered series of local summaries; never labels PASS as factual correctness.
    Expected plan consists of unique (case_id, judge) pairs, predeclared by caller.
    """
    require(isinstance(expected,list) and bool(expected) and all(isinstance(x,(tuple,list)) and len(x)==2 and all(isinstance(v,str) and v for v in x) for x in expected),"Missing ordered plan")
    plan=[tuple(x) for x in expected]
    require(len(set(plan))==len(plan),"Duplicate planned step")
    require(isinstance(summaries,list) and len(summaries)<=len(plan),"Invalid series size")
    counts=Counter();transports=Counter();run_ids=set();elapsed=0;completed=0
    for i,env in enumerate(summaries):
        p=verify(env,"operational-summary",key);b=p["binding"];r=p["result"]
        require(b["schema"]==VERSION and (b["case_id"],b["judge"])==plan[i],"Out of order or unexpected case")
        require((b["inventory_sha"],b["policy_sha"],b["engine_revision"])==(inventory_sha,policy_sha,engine_revision),"Series pin mismatch")
        require(b["split"] in ("development","validation") and p["feedback_eligible"] is False
                and p["production_hold"] is True and p["semantic_certification"] is False,"Unexpected summary authority")
        require(r["run_id"] not in run_ids,"Duplicate run");run_ids.add(r["run_id"])
        if r["status"]=="LOCAL_RECEIPTS_AUTHENTICATED":
            require(r["result"] in ("PASS","FAIL","ABSTAIN","INCONCLUSIVE"),"Invalid verdict")
            counts[r["result"]]+=1;transports[r["transport"]]+=1
            elapsed+=r["receipt_metrics"]["elapsed_ns_total"];completed+=1
        else:counts[r["status"]]+=1
    return {"planned":len(plan),"observed":len(summaries),"completed":completed,"outcomes":dict(counts),
            "transports":dict(transports),"recorded_review_ns":elapsed,
            "series_complete":completed==len(plan),"historical_certification":False,
            "accuracy":None,"independence_verified":False,"production_hold":True}
