"""Private offline ML-assisted routing; predictions are not semantic decisions.
A grouped evaluation of first-pass labels prevents duplicate anchor leakage.
No remote inference, dependencies, canonical writes or automatic promotions.
"""
import collections,hashlib,json,math,re,sys,time,unicodedata
from pathlib import Path

def read(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):return "".join(c for c in unicodedata.normalize("NFKD",s.casefold()) if not unicodedata.combining(c))
def features(row):
    words=re.findall(r"[a-z0-9]+",norm(row["anchor"]))
    f=collections.Counter(words+["_"+a+"_"+b for a,b in zip(words,words[1:])])
    f["field:"+row["field"]]+=2
    for flag in row["flags"]:f["flag:"+flag]+=1
    return f
def vector(f,idf):
    v={k:(1+math.log(n))*idf[k] for k,n in f.items() if k in idf}
    length=math.sqrt(sum(x*x for x in v.values()))
    return {k:x/length for k,x in v.items()} if length else {}
def train(rows,labels):
    feats=[features(r) for r in rows];df=collections.Counter(k for f in feats for k in f)
    idf={k:math.log((1+len(rows))/(1+n))+1 for k,n in df.items()}
    return idf,[(vector(f,idf),labels[r["original_id"]],r["anchor_sha256"]) for r,f in zip(rows,feats)]
def predict(row,model):
    idf,examples=model;v=vector(features(row),idf)
    ranked=sorted(((sum(x*w.get(k,0) for k,x in v.items()),label) for w,label,_ in examples),reverse=True)[:5]
    votes=collections.Counter()
    for score,label in ranked:
        if score>0:votes[label]+=score
    if not votes:return None,0.0
    label,score=votes.most_common(1)[0]
    return label,round(score/sum(votes.values()),4)
def rule(row):
    if row["route"]=="DRAFT_NOT_CANON":return "DRAFT_ISOLATED"
    a=norm(row["anchor"].strip())
    if re.match(r"^(?:estou (?:preparando|organizando|estruturando|continuando|retomando|evitando|garantindo|alinhando|transformando|avancando|ligando|fixando)|vou (?:pesquisar|continuar|retomar|seguir|preservar|consolidar))\b",a):return "POSSIBLE_EDITORIAL_METATEXT"
    if "POSSIBLE_NON_NARRATIVE" in row["flags"]:return "POSSIBLE_HEADING_OR_OPTION"
    if "NEGATION_OR_MODALITY" in row["flags"]:return "MODALITY_REVIEW"
    if "REPORTED_KNOWLEDGE" in row["flags"]:return "REPORT_ATTRIBUTION_REVIEW"
    if "SHORT_ANCHOR" in row["flags"]:return "NEEDS_WIDER_CONTEXT"
    return "ENTITY_FIELD_ATTRIBUTION_REVIEW"
def run(root,labels_path):
    start=time.perf_counter();ledger=root/"editorial/codex-staging/results/exact-context-ledger-v1";summary=read(ledger/"summary.json")
    rows=[r for p in sorted(ledger.glob("batch-*.json")) for r in read(p)]
    if len(rows)!=9229 or len({r["original_id"] for r in rows})!=9229:raise ValueError("Original queue mismatch")
    actual={r["original_id"]:r for r in rows};manual=read(labels_path)
    labels={}
    for r in manual["rows"]:
        orig=actual[r["original_id"]]
        if r["anchor_sha256"]!=orig["anchor_sha256"] or r["entity_id"]!=orig["entity_id"] or r["field"]!=orig["field"]:raise ValueError("Label evidence mismatch")
        labels[r["original_id"]]=r["first_pass"]
    labeled=[r for r in rows if r["original_id"] in labels]
    groups=sorted({r["anchor_sha256"] for r in labeled})
    predictions=[];confusion=collections.Counter()
    for group in groups:
        fit=[r for r in labeled if r["anchor_sha256"]!=group]
        model=train(fit,labels)
        for r in labeled:
            if r["anchor_sha256"]==group:
                guess,confidence=predict(r,model);truth=labels[r["original_id"]]
                predictions.append(guess==truth);confusion[(truth,guess or "ABSTAIN")]+=1
    model=train(labeled,labels)
    out=root/"editorial/codex-staging/results/semantic-triage-v1"
    out.mkdir(parents=True,exist_ok=False);routes=collections.Counter();ml=collections.Counter();batch=[]
    for i,r in enumerate(rows,1):
        guess,confidence=predict(r,model);routing=rule(r);routes[routing]+=1;ml[guess or "ABSTAIN"]+=1
        batch.append({"original_id":r["original_id"],"anchor_sha256":r["anchor_sha256"],"route":routing,"ml_suggestion":guess,"relative_vote_share_not_calibrated":confidence,"first_pass_status":"REVIEWED" if r["original_id"] in labels else "PENDING","independent_review":"PENDING","canon_promotion":False})
        if i%100==0 or i==len(rows):
            (out/("batch-%03d.json"%((i+99)//100))).write_text(json.dumps(batch,ensure_ascii=False,separators=(",",":")),encoding="utf-8");batch=[]
    report={"schema":"worldroot-r35-semantic-triage-v1","original_db_sha256":summary["original_db_sha256"],"ledger_summary_sha256":sha(ledger/"summary.json"),"labels_sha256":sha(labels_path),"total":len(rows),"machine_routed":len(rows),"manual_first_pass":len(labels),"independent_semantic_review":0,"training_anchor_groups":len(groups),"evaluation":"leave-one-anchor-group-out; all labels from first historical lot; not independent or representative held-out source validation","accuracy_against_first_pass":sum(predictions)/len(predictions),"confusion":[{"truth":a,"prediction":b,"n":n} for (a,b),n in sorted(confusion.items())],"routes":dict(routes),"ml_suggestions":dict(ml),"seconds":round(time.perf_counter()-start,3),"backend":"offline TF-IDF + weighted 5-nearest-neighbor","automatic_canon_promotion":False,"note":"Predictions merely prioritize human/model semantic interpretation; confidence is not calibrated probability. Never substitute for claim entailment."}
    (out/"summary.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8");print(json.dumps(report,ensure_ascii=False))
if __name__=="__main__":run(Path(sys.argv[1]),Path(sys.argv[2]))
