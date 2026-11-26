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

def audit_and_enrich(packets,rows,sources,records):
    """Revalidate every ledger link and recover registered mentions. Never assign roles."""
    from .live_codex import norm
    from .semantic_queue import aerun_reference_hint
    by={r["original_id"]:r for r in rows}
    if len(by)!=len(rows):raise ValueError("Duplicate historical ID")
    names=defaultdict(set);known={}
    for r in records:
        ident=r["id"]
        if ident in known:raise ValueError("Duplicate registry identity")
        known[ident]=r.get("scope","UNKNOWN")
        # Exclude unobserved spell catalogue and school proposals from historical mention matching.
        if known[ident] in ("GRIMOIRE_PROPOSAL_NOT_PERSONAL_REPERTOIRE","TRADITION_DESIGN_NOT_OBSERVED"):continue
        for name in [r["name"],*r.get("aliases",[])]:
            key=norm(name)
            if len(key)>=3:names[key].add(ident)
    import re
    pattern=re.compile(r"(?<!\w)(?:"+"|".join(re.escape(k) for k in sorted(names,key=lambda x:(-len(x),x)))+r")(?!\w)") if names else None
    def matches(text):
        # Lookahead on token starts avoids suppressing shorter overlapping aliases.
        if not pattern:return set()
        t=norm(text);found=set()
        for m in re.finditer(r"(?<!\w)\w",t):
            match=pattern.match(t,m.start())
            if match:found.add(match.group())
        return found
    result=[];seen=set();count=Counter()
    for p in packets:
        ident=p["event_id"]
        if ident in seen or seal({k:v for k,v in p.items() if k!="packet_sha256"})!=p["packet_sha256"]:raise ValueError("Invalid event packet")
        seen.add(ident);key="episode:"+p["episode"];digest,lines,status=sources[key]
        if p["source_sha256"]!=digest or p["source_status"]!=status:raise ValueError("Changed source")
        n=p["line"]
        if not 1<=n<=len(lines) or p["anchor"] not in lines[n-1]:raise ValueError("Changed event anchor")
        context=p["context"];line_ids=[x["line"] for x in context]
        if not line_ids or line_ids!=list(range(line_ids[0],line_ids[-1]+1)) or n not in line_ids:raise ValueError("Invalid context window")
        if any(not 1<=x["line"]<=len(lines) or lines[x["line"]-1]!=x["text"] for x in context):raise ValueError("Changed event context")
        checked=set()
        for c in p["candidate_rows"]:
            rid=c["original_id"];r=by.get(rid)
            if rid in checked or r is None:raise ValueError("Missing or duplicate candidate")
            checked.add(rid)
            if r["source"]!=key or r["source_sha256"]!=digest or r["line"] not in line_ids or any(r[k]!=c[k] for k in ("entity_id","field","line","anchor_sha256")) or c["distance"]!=abs(n-r["line"]):raise ValueError("Candidate provenance mismatch")
            exact=r["line"]==n and p["anchor"] in r["anchor"]
            if c["match"]!=("EXACT_BASELINE" if exact else "CONTEXT_ONLY"):raise ValueError("Candidate classification mismatch")
            count["ledger_links_verified"]+=1
            if r["entity_id"] not in known:count["ledger_links_unknown_registry_id"]+=1
        summary=matches(p["summary_candidate"]);anchor=matches(p["anchor"]);mentions=defaultdict(list)
        for x in context:
            for name in matches(x["text"]):mentions[name].append(x["line"])
        candidates=[]
        for name in sorted(summary|set(mentions)):
            ids=sorted(names[name]);locations=mentions.get(name,[])
            # A mention in the event summary is not source evidence.
            tier="ANCHOR" if name in anchor else "SUMMARY_AND_CONTEXT" if name in summary and locations else "CONTEXT_ONLY" if locations else "SUMMARY_ONLY"
            candidates.append({"normalized_alias":name,"candidate_ids":ids,"scopes":[known[i] for i in ids],"source_lines":locations,"tier":tier,"ambiguous":len(ids)>1})
        source_candidates=[c for c in candidates if c["source_lines"]]
        # A chapter/scene heading may itself be the immutable event anchor.
        # R06 bounded windows can then contain the preceding scene and stop
        # at the immediately following day/time marker. Do not use that
        # previous scene for entity recovery; inspect the actual next scene.
        if not checked and lines[n-1].strip().startswith(("## ","# ")):
            mentions=defaultdict(list)
            hi=min(len(lines),n+32)
            day_header_seen=False;body_seen=False
            for i in range(n,hi+1):
                t=lines[i-1].strip()
                if i>n and (t.startswith(("## ","# ")) or t in ("---","***")):break
                if i>n and t.startswith(("**DIA ","**Dia ")):
                    if day_header_seen or body_seen:break
                    day_header_seen=True
                elif i>n and t:body_seen=True
                for name in matches(lines[i-1]):mentions[name].append(i)
            candidates=[]
            for name in sorted(summary|set(mentions)):
                ids=sorted(names[name]);locations=mentions.get(name,[])
                tier="ANCHOR" if name in anchor else "SUMMARY_AND_CONTEXT" if name in summary and locations else "CONTEXT_ONLY" if locations else "SUMMARY_ONLY"
                candidates.append({"normalized_alias":name,"candidate_ids":ids,"scopes":[known[i] for i in ids],"source_lines":locations,"tier":tier,"ambiguous":len(ids)>1})
            source_candidates=[c for c in candidates if c["source_lines"]]
            count["heading_anchor_windows_corrected"]+=1
        if not checked:
            count["previously_open_events"]+=1
            if source_candidates:count["open_events_with_source_mentions"]+=1
            else:count["still_open_events"]+=1
        # Plot IDs index editorial fronts, not competing individual identities.
        # Preserve the original group and all IDs; classification is only a
        # routing decision, never proof that the remaining identity acted.
        for candidate in candidates:
            ids=candidate["candidate_ids"]
            entities=[i for i in ids if not i.startswith("plot:")]
            plots=[i for i in ids if i.startswith("plot:")]
            if candidate["normalized_alias"]=="aerun" and {"aerun-instituto","aerun-guardiao"}<=set(entities):
                hints=[{"line":i,**aerun_reference_hint(lines[i-1])} for i in candidate["source_lines"]]
                candidate["author_reference_hints"]=hints
                explicit={x for h in hints for x in h["candidate_ids"]}
                if len(explicit)==1:count["aerun_explicit_candidate_groups"]+=1
                elif len(explicit)>1:count["aerun_mixed_candidate_groups"]+=1
                else:count["aerun_context_required_groups"]+=1
            candidate["entity_candidate_ids"]=entities
            candidate["plot_reference_ids"]=plots
            if len(entities)>1:
                candidate["identity_route"]="MULTIPLE_ENTITY_IDS_REVIEW_REQUIRED"
                count["multiple_entity_groups"]+=1
            elif len(entities)==1 and plots:
                candidate["identity_route"]="ENTITY_AND_PLOT_DISTINCT_REVIEW_REQUIRED"
                count["entity_plot_groups"]+=1
            elif len(entities)==1:
                candidate["identity_route"]="SINGLE_ENTITY_CANDIDATE"
            else:
                candidate["identity_route"]="PLOT_REFERENCE_ONLY"
            if candidate["ambiguous"] and not entities:count["multiple_plot_only_groups"]+=1
        count["registry_mention_groups"]+=len(candidates)
        count["ambiguous_mention_groups"]+=sum(x["ambiguous"] for x in candidates)
        route="LEDGER_AND_REGISTRY_REVIEW" if checked else "REGISTRY_MENTION_REVIEW" if source_candidates else "OPEN_ENTITY_REVIEW_REQUIRED"
        value={"event_id":ident,"packet_sha256":p["packet_sha256"],"source_sha256":digest,"source_status":status,"visibility":p["visibility"],"ledger_links_verified":len(checked),"registry_mentions":candidates,"route":route,"semantic_certification":False,"canon_promotion":False}
        result.append({**value,"receipt_sha256":seal(value)})
    count["events_audited"]=len(result)
    count["semantic_certified"]=0;count["canon_promotions"]=0
    return result,dict(count)
