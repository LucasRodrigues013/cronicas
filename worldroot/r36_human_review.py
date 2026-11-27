"""Human preference contract, not evidence of human identity or approval."""
from .r36_evaluation import compare_pair,reverse_pair
from .r36_calibration import comparison_context
from .r36_trust import require,authenticate
from .semantic_queue import seal

def record(pair,reverse,forward_vote,reverse_vote,author_vote,key):
    comparison=compare_pair(pair,reverse,forward_vote,reverse_vote)
    require(isinstance(author_vote,dict) and set(author_vote)=={"packet_id","winner","reviewer","reason","evidence","limitations"},"Invalid human review")
    require(author_vote["packet_id"]==pair.packet["packet_id"] and author_vote["winner"] in set(pair.mapping)|{"TIE","ABSTAIN"},"Wrong human choice")
    require(all(isinstance(author_vote[k],str) and bool(author_vote[k].strip()) for k in ("reviewer","reason","limitations")),"Missing human rationale")
    candidates={c["id"]:c["text"] for c in pair.packet["candidates"]}
    evidence=author_vote["evidence"]
    require(isinstance(evidence,list) and (bool(evidence) or author_vote["winner"]=="ABSTAIN"),"Human evidence required")
    for e in evidence:
        require(isinstance(e,dict) and set(e)=={"candidate_id","quote"} and e["candidate_id"] in candidates
                and isinstance(e["quote"],str) and bool(e["quote"].strip()) and e["quote"] in candidates[e["candidate_id"]],"Unbound human quote")
    human=pair.mapping.get(author_vote["winner"],author_vote["winner"])
    agreement=comparison["winner"]==human and human not in ("ABSTAIN","INCONCLUSIVE")
    values=list(candidates.values())
    payload={"schema":"r36-e7-human-review-v1","packet_id":pair.packet["packet_id"],"reverse_id":reverse["packet_id"],
             "votes_sha256":seal([forward_vote,reverse_vote]),"author_vote":author_vote,
             "model_comparison":comparison,"human_preference":human,"agreement":agreement,
             "length_diagnostic":comparison_context(*values),"human_identity_verified":False,
             "semantic_certification":False,"production_hold":True}
    return authenticate("human-review",payload,key)
