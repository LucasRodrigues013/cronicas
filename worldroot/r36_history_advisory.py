"""Controlled director-only FC retrieval. Inspired by epistemic retrieval and shadow release.
Reuses the existing R33 preparation and immutable archive; never creates typed facts.
"""
import hashlib,json,os,re
from collections import Counter,defaultdict
from pathlib import Path
from . import git_cycle as g, live_codex as codex
from .deep_recovery import tokens,STOP
from .history_index import read_verified_sources
from .scene_context import index,candidates
PROJECT="CRONICAS_DE_UM_NOVO_MUNDO"
BASE_ARCHIVE="9dd632fb0bcd84dfce5b631013fdc67d7492ac5d"
BASE_CLOSURE="687e0515763105921f04f3b4d9df8e16799e6fb9"
MAP="a85dc433290b7f9cd1b4fb0a44a9cd0fa06f19420838de8387e931ee54be7144"
INVENTORY="af78ceb90191dc0b204be3c21bc505e5011e7f94cd54f1cf8084f0632063cecc"
BINDING="f2301e1723f4ba352f4c75ce5d4e1c3baecf7e7e5bd4779ecdc453bc68f05d30"
def need(ok,msg):
    if not ok:raise ValueError(msg)
def seal(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def blob(raw):return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def words(s):return set(tokens(s))-STOP
def cues(line):
    """Signals for cautious reading, not propositions or truth classification."""
    f=codex.norm(line);s=line.strip()
    if not s:return ("STRUCTURAL",)
    if s.startswith("#") or s in ("---","***") or re.match(r"^\d{1,2}/\d{1,2}/\d{4}",s):return ("STRUCTURAL",)
    if re.match(r"^(estou (?:estruturando|organizando|mantendo|ajustando|preparando|planejando|revisando)|vou (?:apresentar|estruturar|organizar|manter)|nota editorial|rascunho narrativo|revisao base|encerramento narrativo)\b",f):return ("META",)
    if re.match(r"^(?:opcao|escolha|acao livre)\b",f):return ("OPTION",)
    result=[]
    if s.startswith(("—","–")) or re.search(r"\b(segundo|rumor\w*|ouviu falar|disseram|contaram|relatou)\b",f):result.append("REPORT_OR_DIALOGUE")
    if re.search(r"\b(talvez|poderia\w*|possibilidade\w*|parecia|suspeit\w*|hipotese\w*)\b",f):result.append("HYPOTHESIS_CUE")
    if re.search(r"\b(pretend\w*|planej\w*|queria|desejava|prometeu|seria|faria)\b",f):result.append("INTENTION_CUE")
    if re.search(r"\b(nao|nunca|jamais|nem)\b",f):result.append("NEGATION_CUE")
    if s.startswith("*") and s.endswith("*") and not s.startswith("**"):result.append("PRIVATE_THOUGHT_CUE")
    return tuple(result or ["NARRATIVE_CANDIDATE"])
def eligible_lines(lines,roles):
    menu=False
    for i,(line,role) in enumerate(zip(lines,roles),1):
        s=line.strip();f=codex.norm(s)
        if s in ("## Prompt:","## Response:"):menu=False
        elif re.match(r"^#{1,6}\s+",s):
            if re.match(r"^(?:as )?(?:cinco |quatro |tres )?(?:portas|escolhas|opcoes|alternativas|proximos caminhos)\b",f):menu=True
            elif re.match(r"^#{1,2}\s+",s):menu=False
        flags=cues(line)
        if role=="Response" and not menu and not set(flags)&{"STRUCTURAL","META","OPTION","PRIVATE_THOUGHT_CUE"}:
            yield i,flags
def load_pack(path,expected):
    p=Path(path);need(p.is_file() and not p.is_symlink(),"FC pack missing or unsafe")
    pack=json.loads(p.read_text());body={k:v for k,v in pack.items() if k!="pack_sha256"}
    need(pack.get("pack_sha256")==expected==seal(body),"FC pack seal")
    need(pack.get("schema")=="worldroot-fc-operational-locators-v1" and pack.get("project")==PROJECT and pack.get("archive_pin")==BASE_ARCHIVE and pack.get("inventory_sha256")==INVENTORY and pack.get("map_sha256")==MAP and pack.get("registry_binding")==BINDING,"FC pack authority")
    rows=pack["groups"];need(len(rows)==3387 and len({r["id"] for r in rows})==3387,"FC denominator")
    return pack
def source_data(root,rows):
    _,history=read_verified_sources(root);sources={};private=defaultdict(set)
    for m,text in history:
        lines=text.split("\n");roles=[];role="Metadata"
        for s in lines:
            role={"## Prompt:":"Prompt","## Response:":"Response"}.get(s.strip(),role);roles.append(role)
        sources[m["source_name"]]=(lines,roles,m["sha256"])
    for name in sorted({r["source"] for r in rows}-set(sources)):
        d,m=g.verify_episode(root,name);c=g.load(root/"canon/episodes"/(name+".json"))
        need(c["episode_id"]==name and c["story_sha256"]==m["original_readback_sha256"] and c["sequence"]<=50,"FC closed source authority")
        lines=d.prose.splitlines()
        sources[name]=(lines,["Response"]*len(lines),sha(d.prose))
        for e in c["events"]:
            if e["visibility"]!="PUBLICO":private[name].add(e["source"]["line"])
    return sources,private
def retrieve(root,request,pack):
    root=Path(root);head=request["head"]
    need(request.get("project")==PROJECT and g.load(root/"canon/HEAD.json")==head and head["sequence"]>=50,"FC live HEAD")
    need(blob((root/"canon/episodes/LVI-C09-PI-D579-AUTHOR-SOURCE.json").read_bytes())==BASE_CLOSURE,"FC baseline closure changed")
    g.verify_db(root,head)
    reg,binding=codex.load_registry(root);records=list(codex.all_records(reg));by_id,aliases=index(records)
    rows=pack["groups"];sources,private=source_data(root,rows)
    safe={name:dict(eligible_lines(lines,roles)) for name,(lines,roles,_) in sources.items()}
    index_rows=[];blocked=Counter()
    for r in rows:
        lines,roles,source_sha=sources[r["source"]];a,z=r["interval"]
        need(r["authority"]=="HISTORICAL_RESPONSE_NOT_CANON_CERTIFIED" and r["visibility"]=="EDITORIAL_ONLY_NO_CHARACTER_INJECTION" and r["role"]=="Response","FC source scope")
        need(1<=a<=z<=len(lines) and r["source_sha256"]==source_sha and sha("\n".join(lines[a-1:z]))==r["anchor"] and all(x=="Response" for x in roles[a-1:z]),"FC source changed")
        if any(a<=n<=z for n in private[r["source"]]):blocked["closed_nonpublic_anchor"]+=1;continue
        loc=[(n,words(lines[n-1]),safe[r["source"]][n]) for n in range(a,z+1) if n in safe[r["source"]]]
        if not loc:blocked["no_eligible_line"]+=1;continue
        terms=set().union(*(v for _,v,_ in loc))
        index_rows.append((r,loc,terms))
    results=[];count=0;critical_missing=0
    for req in request["requirements"]:
        if req.get("role","Response")!="Response":continue
        q=words(req["query"]);ids={req["entity"]} if req.get("entity") in by_id else set()
        for _,found in candidates(req["query"],aliases):ids.update(found)
        ranked=[]
        for r,loc,terms in index_rows:
            hits=q&terms
            if not hits:continue
            matches=ids&set(r["candidate_ids"]) if binding==BINDING else set()
            best=max(loc,key=lambda x:(len(q&x[1]),"NARRATIVE_CANDIDATE" in x[2],-x[0]))
            coverage=len(q&best[1])
            if not coverage:continue
            # Exact literal matching + entity candidate channel, no identity resolution.
            score=4*coverage+len(hits)+2*bool(matches)
            ranked.append((score,coverage,r,best))
        ranked.sort(key=lambda x:(-x[0],-x[1],-x[2]["macro"],x[2]["id"]))
        selected=[];seen=set()
        for score,coverage,r,(line,_,flags) in ranked:
            if r["source"] in seen and len(ranked)>3:continue
            seen.add(r["source"])
            selected.append({"group_id":r["id"],"source":r["source"],"source_sha256":r["source_sha256"],"group_interval":r["interval"],"group_anchor":r["anchor"],"line":line,"line_sha256":sha(sources[r["source"]][0][line-1]),"signals":list(flags),"identity_status":"CANDIDATE_ONLY","knowledge_injection":False})
            if len(selected)==3:break
        if not selected and req["critical"]:critical_missing+=1
        count+=len(selected);results.append({"requirement_id":req["id"],"status":"EDITORIAL_CANDIDATES" if selected else "NOT_RECOVERED_BY_ADVISORY","locators":selected})
    out={"schema":"worldroot-r36-fc-advisory-v1","project":PROJECT,"head_sha256":g.sha(g.canonical(head)),"request_sha256":g.sha(g.canonical(request)),"pack_sha256":pack["pack_sha256"],"registry_binding":binding,"baseline_alias_links_active":binding==BINDING,"indexed_groups":len(index_rows),"blocked_groups":dict(blocked),"requirements":results,"locator_count":count,"critical_without_advisory":critical_missing,"scope":"DIRECTOR_ONLY_CANDIDATES_NOT_FACTS","knowledge_injection":False,"semantic_certification":False,"canon_changed":False}
    return {**out,"advisory_sha256":seal(out)}
def configured(root,request):
    path=Path(root)/"ops/ENGINE_PUBLISHING_POLICY.json"
    if not path.is_file():return None
    c=json.loads(path.read_text()).get("r36_convergence")
    if c is None:return None
    need(c.get("mode")=="CONTROLLED_EDITORIAL_ADVISORY" and c.get("independent_certification") is False and c.get("canon_promotion") is False,"FC policy")
    p=os.environ.get("WORLDROOT_FC_INDEX");need(bool(p),"FC index required by active policy")
    return retrieve(root,request,load_pack(p,c["pack_sha256"]))
def check_binding(request,advisory):
    if advisory is None:return
    need(advisory.get("advisory_sha256")==seal({k:v for k,v in advisory.items() if k!="advisory_sha256"}) and advisory.get("request_sha256")==g.sha(g.canonical(request)) and advisory.get("head_sha256")==g.sha(g.canonical(request["head"])) and advisory.get("knowledge_injection") is False and advisory.get("canon_changed") is False and advisory.get("semantic_certification") is False,"FC advisory binding")
