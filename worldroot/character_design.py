"""Versioned author visual direction; never reinterpret historical prose or imply age."""
from __future__ import annotations
import json,hashlib,re,unicodedata
from pathlib import Path
REGISTRY="editorial/registries/female-character-design-d580-v2.json"
FIELDS=("name","age","face","eyes","hair","build","bust","hips","legs","wardrobe","role_and_presence","effect_on_others","skin")
IDS=("miren","astra","lyra","thalor-althea","ilva","maelis","lysa","elyrien","serenna","yra","seris","naira","bressa","adela","serina","orelia","avelna","talis","enna","reva","ivena")
ALIASES={"lyra":["Lira","Lyra","Lira Selen","Lira Selen Vareth"],"lysa":["Lysa","Lisa"],"seris":["Serís","Seris","Serís Daum"],"serenna":["Serenna","Serenna Vareth"],"thalor-althea":["Althea"],"talis":["Talis","Talis Elvenar"]}
def norm(s):
    return " ".join(re.findall(r"[^\W_]+",unicodedata.normalize("NFKD",str(s)).encode("ascii","ignore").decode().casefold()))
def load_design(root):
    path=Path(root)/REGISTRY
    if not path.exists():return None
    if path.is_symlink() or not path.is_file():raise ValueError("Unsafe character design source")
    body=path.read_bytes();data=json.loads(body)
    if data.get("schema")!="worldroot-female-character-design-v2" or data.get("project")!="CRONICAS_DE_UM_NOVO_MUNDO" or data.get("status")!="ACTIVE_EDITORIAL_VISUAL_DIRECTION":raise ValueError("Invalid design authority")
    rows=data.get("profiles")
    if not isinstance(rows,list) or len(rows)!=len(IDS) or set(p.get("id") for p in rows)!=set(IDS):raise ValueError("Incomplete female design registry")
    for p in rows:
        if any(k not in p for k in FIELDS) or any(not isinstance(p[k],str) or not p[k].strip() for k in FIELDS if k!="age"):raise ValueError("Incomplete character design fields")
        age=p["age"]
        if not isinstance(age,dict) or (age.get("years") is not None and (type(age["years"]) is not int or age["years"]<=0)) or age.get("status") not in ("AUTHOR_DEFINED","ADULT_CONFIRMED_NUMERIC_DESIGN_PROPOSAL","UNRESOLVED","DESIGN_PROPOSAL_PENDING_HISTORICAL_CONCILIATION"):raise ValueError("Invalid age status")
    by={p["id"]:p for p in rows}
    if by["lyra"]["age"]!={"years":18,"status":"AUTHOR_DEFINED"} or by["miren"]["skin"]!="Clara, sem sardas":raise ValueError("Missing explicit author correction")
    return {"path":REGISTRY,"sha256":hashlib.sha256(body).hexdigest(),"profiles":rows,"status":"AUTHOR_VISUAL_DIRECTION_NOT_HISTORICAL_REWRITE"}
def matches(p,query="",entity=None,exact=False):
    if entity==p["id"]:return True
    names=[p["name"],p["id"],*ALIASES.get(p["id"],[])]
    q=norm(query)
    return any(q==norm(n) if exact else bool(re.search(r"(?<!\w)"+re.escape(norm(n))+r"(?!\w)",q)) for n in names if norm(n))
def selected_design(root,names):
    data=load_design(root)
    if data is None:return None
    return {"path":data["path"],"sha256":data["sha256"],"profiles":[p for p in data["profiles"] if any(matches(p,n,exact=True) for n in names)],"status":data["status"]}
def source_bodies(data):
    """Separate design evidence from narrative, with an explicit age source only when known."""
    out={}
    if data is None:return out
    for p in data["profiles"]:
        source="AUTHOR_DESIGN:"+p["id"]+":appearance"
        value={k:p[k] for k in ("name","face","eyes","hair","skin","build","wardrobe","hips","legs")}
        value["height_cm_design"]=p.get("height_cm")
        value["authority"]="Prospective author visual direction; reconcile historical traits, no age or romantic inference."
        if p["age"]["status"] in ("AUTHOR_DEFINED","ADULT_CONFIRMED_NUMERIC_DESIGN_PROPOSAL"):value["bust"]=p["bust"]
        out[source]=json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
        a=p["age"]
        if a["status"]=="AUTHOR_DEFINED" and a["years"]>=18:
            out["AUTHOR_DESIGN:"+p["id"]+":age"]=json.dumps({"name":p["name"],"age_years":a["years"],"status":"AUTHOR_DEFINED_CURRENT_DESIGN"},ensure_ascii=False,indent=2)+"\n"
        elif a["status"]=="ADULT_CONFIRMED_NUMERIC_DESIGN_PROPOSAL":
            out["AUTHOR_DESIGN:"+p["id"]+":age"]=json.dumps({"name":p["name"],"adult":True,"age_years":None,"status":"ADULT_CONFIRMED_NUMERIC_UNKNOWN"},ensure_ascii=False,indent=2)+"\n"
    return out
def candidate_sources(data,query="",entity=None):
    bodies=source_bodies(data)
    if data is None:return []
    return [{"profile":p,"sources":[{"source":s,"line_start":1,"line_end":len(t.splitlines()),"anchor_sha":hashlib.sha256(t.encode()).hexdigest(),"anchor":t,"role":"AuthorDesign"} for s,t in bodies.items() if s.startswith("AUTHOR_DESIGN:"+p["id"]+":")]} for p in data["profiles"] if matches(p,query,entity)]
def valid_requirement(req,review,data):
    if data is None or req.get("domain")!="identity" or req.get("role")!="AuthorDesign":return False
    field=req.get("design_field")
    if field not in ("appearance","age"):return False
    return any(review.get("source")=="AUTHOR_DESIGN:"+p["id"]+":"+field and req.get("entity")==p["id"] for p in data["profiles"])
def design_requirement_matches_card(req,review,name,field):
    ident=req.get("entity")
    if ident not in IDS or req.get("design_field")!=field or review.get("source")!="AUTHOR_DESIGN:"+ident+":"+field:return False
    names=[ident,*ALIASES.get(ident,[])]
    return norm(name) in {norm(n) for n in names}
def bind_request(root,request):
    names=[c["name"] for c in request.get("r34_intent",{}).get("characters",[])]
    return selected_design(root,names)
def verify_binding(root,request,packet):
    saved=packet.get("character_design")
    if saved is not None and bind_request(root,request)!=saved:raise ValueError("Character design changed after preparation; recover current design")
    return saved
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--archive-root",type=Path,required=True);p.add_argument("--character",action="append",default=[])
    a=p.parse_args();data=selected_design(a.archive_root,a.character) if a.character else load_design(a.archive_root)
    if data is None:raise SystemExit("No design registry")
    print(json.dumps(data,ensure_ascii=False,indent=2))
