"""R36 contextual candidate packets; private staging, never graph promotion."""
from collections import defaultdict,Counter
from .r36_reconciliation import sha
from .semantic_queue import seal

def expand(closures,rows,sources,baseline,radius=32):
    if type(radius) is not int or not 1<=radius<=64:raise ValueError("Invalid radius")
    by=defaultdict(list)
    for r in rows:by[(r["source"],r["source_sha256"])].append(r)
    prior={r["event_id"]:r for r in baseline}
    if len(prior)!=len(baseline):raise ValueError("Duplicate baseline")
    result=[]
    for c in sorted(closures,key=lambda x:x["sequence"]):
        key="episode:"+c["episode_id"]
        digest,lines,status=sources[key]
        if digest!=c["story_sha256"]:raise ValueError("Source changed")
        for e in c["events"]:
            ident=e["event_id"];s=e["source"];n=s["line"]
            if s["sha256"]!=digest or type(n) is not int or not 1<=n<=len(lines) or s["literal_anchor"] not in lines[n-1]:raise ValueError("Invalid event anchor")
            old=prior.pop(ident)
            if old["episode"]!=c["episode_id"] or old["source_sha256"]!=digest or old["line"]!=n or old["visibility"]!=e["visibility"]:raise ValueError("Changed baseline")
            lo=max(1,n-radius);hi=min(len(lines),n+radius)
            # Do not expand into author menus or another explicit scene header.
            def boundary(line):
                t=line.strip()
                return t.startswith(("## ","# ","**DIA ","**Dia ","<text color=\"secondary\" size=\"xs\" weight=\"medium\">DIA"))
            for j in range(n-1,lo-1,-1):
                if boundary(lines[j-1]):lo=j;break
            for j in range(n+1,hi+1):
                if boundary(lines[j-1]):hi=j-1;break
            candidates=[r for r in by[(key,digest)] if lo<=r["line"]<=hi]
            ids={r["original_id"] for r in candidates}
            if not set(old["candidate_ids"])<=ids:raise ValueError("Lost exact candidate")
            evidence=[{"original_id":r["original_id"],"entity_id":r["entity_id"],"field":r["field"],"line":r["line"],"anchor_sha256":r["anchor_sha256"],"distance":abs(n-r["line"]),"match":"EXACT_BASELINE" if r["original_id"] in old["candidate_ids"] else "CONTEXT_ONLY"} for r in sorted(candidates,key=lambda r:(abs(n-r["line"]),r["original_id"]))]
            packet={"schema":"worldroot-r36-event-review-packet-v1","event_id":ident,"episode":c["episode_id"],"sequence":c["sequence"],"source_sha256":digest,"source_status":status,"visibility":e["visibility"],"event_type":e.get("event_type","NARRADO"),"summary_candidate":e["summary_candidato"],"line":n,"anchor":s["literal_anchor"],"context":[{"line":i,"text":lines[i-1]} for i in range(lo,hi+1)],"candidate_rows":evidence,"route":"EXACT_REVIEW_REQUIRED" if old["candidate_ids"] else "CONTEXT_REVIEW_REQUIRED" if candidates else "OPEN_ENTITY_REVIEW_REQUIRED","canon_promotion":False,"semantic_certification":False}
            result.append({**packet,"packet_sha256":seal(packet)})
    if prior:raise ValueError("Missing baseline event")
    return result

def metrics(packets):
    routes=Counter(p["route"] for p in packets)
    return {"event_packets":len(packets),"routes":dict(routes),"exact_links_preserved":sum(r["match"]=="EXACT_BASELINE" for p in packets for r in p["candidate_rows"]),"context_links":sum(r["match"]=="CONTEXT_ONLY" for p in packets for r in p["candidate_rows"]),"semantic_certified":0,"canon_promotions":0}
