"""APEX 9+ shadow ranking. Pure source-locator selection, not semantic adjudication.
No I/O, canon writes, identity resolution or authority elevation.
"""
from collections import Counter,defaultdict
from math import log

MODAL=frozenset(("REPORT_OR_DIALOGUE","HYPOTHESIS_CUE","INTENTION_CUE","NEGATION_CUE"))
def select(index_rows,q,ids,alias_enabled,mode="fusion",limit=3):
    if mode not in ("fusion","coverage") or type(limit) is not int or not 1<=limit<=10:
        raise ValueError("Invalid shadow ranking bounds")
    if not q:return []
    q=set(q);ids=set(ids)
    df=Counter(w for _,_,terms in index_rows for w in q&terms)
    total=len(index_rows)
    weights={w:1+log((total+1)/(df[w]+1)) for w in q}
    def weight(ts):return sum(weights[w] for w in sorted(ts))
    rows=[]
    for r,loc,terms in index_rows:
        hits=q&terms
        if not hits:continue
        match=bool(ids&set(r["candidate_ids"])) if alias_enabled else False
        best=max(loc,key=lambda x:(weight(q&x[1]),len(q&x[1]),"NARRATIVE_CANDIDATE" in x[2],-x[0]))
        hit=q&best[1]
        if not hit:continue
        # Negations and reports are material evidence too; never remove them for being modal.
        rows.append((r,best,hit,hits,match))
    def key(x):return (-x[0]["macro"],x[0]["id"],x[1][0])
    streams=(
        sorted(rows,key=lambda x:(-weight(x[2]),-len(x[2]),key(x))),
        sorted(rows,key=lambda x:(-weight(x[3]),-weight(x[2]),key(x))),
        sorted(rows,key=lambda x:(-int(x[4]),-weight(x[2]),-weight(x[3]),key(x))),
        sorted(rows,key=lambda x:(-len(x[2]),-len(x[3]),-int(x[4]),key(x))),
    )
    scores=defaultdict(float);pool={}
    for stream,w in zip(streams,(1.5,1.0,0.75,1.0)):
        for rank,row in enumerate(stream[:80],1):
            ident=row[0]["id"];pool[ident]=row;scores[ident]+=w/(12+rank)
    ranked=sorted(pool.values(),key=lambda x:(-scores[x[0]["id"]],key(x)))
    chosen=[];covered=set()
    def overlaps(x,y):
        a,b=x[0],y[0]
        if a["source"]!=b["source"]:return False
        lo,hi=a["interval"];l,h=b["interval"]
        return max(0,min(hi,h)-max(lo,l)+1)*2>=min(hi-lo+1,h-l+1)
    while ranked and len(chosen)<limit:
        if mode=="coverage":
            ranked.sort(key=lambda x:(-(scores[x[0]["id"]]+.06*weight(x[2]-covered)/max(1,weight(q))),key(x)))
        row=ranked.pop(0)
        if any(overlaps(row,x) for x in chosen):continue
        chosen.append(row);covered.update(row[2])
    return [(r,best) for r,best,*_ in chosen]
