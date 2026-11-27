"""Private experimental feedback staging. Never changes editorial policy or canon."""
from collections import defaultdict
from datetime import date
from hashlib import sha256
from .r36_trust import require,digest,authenticate,verify
from .semantic_queue import seal

VERSION="r36-e7-adaptive-v1"
KINDS={"factual","narrative","aesthetic","character_development","author_decision","technical"}
ORIGINS={"author_feedback","production_observation","development","synthetic"}
SCOPES={"global","contextual","point"}
FIELDS={"kind","origin","scope","target","context","entity","direction","severity","confidence",
        "observed_on","expires_on","engine_revision","source_sha256","source_start","source_end","quote","episode"}
TRANSITIONS={"OBSERVATION":{"PROPOSED","REJECTED"},"PROPOSED":{"EXPERIMENTED","REJECTED","SUPERSEDED"},
 "EXPERIMENTED":{"EVALUATED","REJECTED"},"EVALUATED":{"APPROVED","REJECTED"},
 "APPROVED":{"STAGED","REJECTED","SUPERSEDED"},"STAGED":{"ROLLED_BACK","SUPERSEDED"},
 "REJECTED":set(),"SUPERSEDED":set(),"ROLLED_BACK":set()}
PROTECTED={"canon","world_fact","power","agency","character_identity","author_policy"}
def text(x):return isinstance(x,str) and bool(x.strip())
def day(x):
    require(isinstance(x,str),"Date required")
    d=date.fromisoformat(x);require(d.isoformat()==x,"Canonical ISO date required");return d

def observation(meta,raw,origin_key):
    """Source authority and origin must be checked by trusted custodian."""
    require(isinstance(meta,dict) and set(meta)==FIELDS,"Unexpected feedback fields")
    require(meta["kind"] in KINDS and meta["origin"] in ORIGINS and meta["scope"] in SCOPES,"Unsupported origin, scope or kind")
    require(meta["direction"] in ("preserve","improve","avoid","correct") and meta["severity"] in ("critical","major","minor"),"Invalid direction/severity")
    require(type(meta["confidence"]) in (int,float) and 0<=meta["confidence"]<=1,"Invalid confidence")
    require(all(text(meta[k]) for k in ("target","context","entity","episode")) and digest(meta["engine_revision"]),"Missing context or revision")
    require(meta["scope"]!="global" or meta["context"]=="GLOBAL","Global scope must be explicit")
    require(meta["scope"]!="point" or meta["context"]==meta["episode"],"Point must be episode-bound")
    observed=day(meta["observed_on"])
    if meta["expires_on"] is not None:require(day(meta["expires_on"])>=observed,"Invalid expiry")
    require(isinstance(raw,bytes) and 0<len(raw)<=2_000_000 and sha256(raw).hexdigest()==meta["source_sha256"],"Source bytes mismatch")
    lines=raw.decode("utf-8").splitlines();lo,hi=meta["source_start"],meta["source_end"]
    require(type(lo) is int and type(hi) is int and 1<=lo<=hi<=len(lines),"Invalid source range")
    require(text(meta["quote"]) and meta["quote"] in "\n".join(lines[lo-1:hi]),"Quote not literal")
    return authenticate("feedback-observation",{"schema":VERSION,"observation_id":seal(meta),"meta":meta},origin_key)

def summarize(envelopes,key,as_of):
    today=day(as_of);seen=set();groups=defaultdict(list);expired=duplicates=0
    for env in envelopes:
        p=verify(env,"feedback-observation",key)
        require(p["schema"]==VERSION and p["observation_id"]==seal(p["meta"]),"Bad observation binding")
        m=p["meta"];require(m["origin"] in ORIGINS,"Reserved/unknown origin")
        if day(m["observed_on"])>today or (m["expires_on"] is not None and day(m["expires_on"])<today):
            expired+=1;continue
        identity=tuple(m[k] for k in ("source_sha256","source_start","source_end","target","entity","scope","context","direction","origin"))
        if identity in seen:duplicates+=1;continue
        seen.add(identity)
        groups[(m["target"],m["entity"],m["scope"],m["context"],m["origin"]=="synthetic")].append(p)
    result=[]
    for k,items in sorted(groups.items()):
        positive=[p for p in items if p["meta"]["direction"]=="preserve"]
        negative=[p for p in items if p["meta"]["direction"]!="preserve"]
        # Maximum independent matching of source/episode pairs, not raw observation count.
        edges=defaultdict(set)
        for p in negative:edges[p["meta"]["source_sha256"]].add(p["meta"]["episode"])
        matches={}
        def augment(source,visited):
            for episode in sorted(edges[source]):
                if episode in visited:continue
                visited.add(episode)
                if episode not in matches or augment(matches[episode],visited):
                    matches[episode]=source;return True
            return False
        count=sum(augment(s,set()) for s in sorted(edges))
        cross=any(other[:2]==k[:2] and other[4]==k[4] and other!=k and
                  (other[2]=="global" or k[2]=="global") and
                  any((x["meta"]["direction"]=="preserve") != (y["meta"]["direction"]=="preserve")
                      for x in items for y in others) for other,others in groups.items())
        result.append({"target":k[0],"entity":k[1],"scope":k[2],"context":k[3],"synthetic":k[4],
                       "observation_ids":sorted(p["observation_id"] for p in items),
                       "preserve_ids":sorted(p["observation_id"] for p in positive),
                       "recurrence_lower_bound":count,"conflict":bool(positive and negative) or cross,"review_required":True})
    return {"groups":result,"duplicates":duplicates,"expired_or_future":expired,"policy_changed":False}

def proposal(envelopes,origin_key,as_of,group_index,baseline_sha,policy_sha,hypothesis):
    require(digest(baseline_sha) and digest(policy_sha) and text(hypothesis),"Proposal pins/hypothesis required")
    groups=summarize(envelopes,origin_key,as_of)["groups"]
    require(type(group_index) is int and 0<=group_index<len(groups),"Unknown group")
    group=groups[group_index]
    payload={"schema":VERSION,"group":group,"baseline_sha":baseline_sha,"policy_sha":policy_sha,
             "hypothesis":hypothesis,"protected_target":group["target"] in PROTECTED,
             "state":"OBSERVATION","production_hold":True}
    return authenticate("feedback-proposal",{**payload,"proposal_id":seal(payload)},origin_key)

def replay(prop,history,key,approval_key=None):
    p=verify(prop,"feedback-proposal",key)
    require(p["proposal_id"]==seal({k:v for k,v in p.items() if k!="proposal_id"}) and p["state"]=="OBSERVATION","Bad proposal")
    state="OBSERVATION";previous=p["proposal_id"]
    for i,env in enumerate(history,1):
        e=verify(env,"feedback-event",key)
        require(e["proposal_id"]==p["proposal_id"] and e["policy_sha"]==p["policy_sha"]
                and e["index"]==i and e["previous"]==previous and e["state"] in TRANSITIONS[state],"Invalid event chain")
        if e["state"] in ("APPROVED","STAGED"):
            require(not p["group"]["synthetic"] and approval_key is not None and approval_key!=key,"Invalid approval custody")
            verify(e["approval"],"feedback-approval",approval_key,{k:e[k] for k in ("proposal_id","state","policy_sha","evidence_sha")})
        state=e["state"];previous=seal(env)
    return state

def event(prop,history,state,evidence_sha,reason,key,approval=None,approval_key=None):
    p=verify(prop,"feedback-proposal",key)
    prior=replay(prop,history,key,approval_key)
    require(state in TRANSITIONS[prior],"Invalid transition")
    require(digest(evidence_sha) and text(reason),"Evidence and rationale required")
    expected={"proposal_id":p["proposal_id"],"state":state,"policy_sha":p["policy_sha"],"evidence_sha":evidence_sha}
    if state in ("APPROVED","STAGED"):
        require(not p["group"]["synthetic"],"Synthetic observations cannot authorize changes")
        require(approval_key is not None and approval_key!=key,"Separate approval key required")
        verify(approval,"feedback-approval",approval_key,expected)
    else:require(approval is None,"Unexpected approval")
    body={**expected,"reason":reason,"index":len(history)+1,
          "previous":seal(history[-1]) if history else p["proposal_id"],"approval":approval}
    return authenticate("feedback-event",body,key)

def staging_status(prop,history,key,approval_key=None):
    return {"state":replay(prop,history,key,approval_key),"policy_changed":False,"canon_changed":False,
            "incorporation_executed":False,"production_hold":True,"semantic_certification":False}
