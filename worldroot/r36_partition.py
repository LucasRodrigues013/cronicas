"""Private metadata-only connected component feasibility; no corpus or labels."""
from collections import Counter
from .r36_benchmark import FIELDS,TARGETS,SPLITS,validate_inventory,require

def feasibility(rows, *, development_ids=None):
    """Check structural split capacity with optional fixed development cases.

    The caller supplies IDs of all known/exposed cases. A connected component
    containing any such case may only be assigned to development. Omission of
    the argument preserves the legacy unconstrained capacity check; neither
    mode authenticates source lineage or reserved custody.
    """
    if development_ids is not None:
        require(isinstance(development_ids,list) and all(
            isinstance(x,str) and bool(x) and x==x.strip() for x in development_ids
        ),"Invalid fixed development IDs")
        require(len(set(development_ids))==len(development_ids),"Duplicate fixed development ID")
    fixed=set(development_ids or [])
    require(isinstance(rows,list) and 0<len(rows)<=60,"Pilot inventory must contain 1..60 cases")
    parent=list(range(len(rows)));owners={};ids=set()
    def find(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,r in enumerate(rows):
        require(isinstance(r,dict) and set(r)==FIELDS-{"split"},"Use unsplit metadata only")
        validate_inventory([{**r,"split":"development"}],exact=False)
        require(r["id"] not in ids,"Duplicate case");ids.add(r["id"])
        tags=[("family",r["family"]),*(("episode",e) for e in r["episodes"]),
              *(("entity",e) for e in r["entities"]),*(("source",e) for e in r["source_pins"])]
        for tag in tags:
            j=owners.setdefault(tag,i);parent[find(i)]=find(j)
    require(fixed<=ids,"Unknown fixed development ID")
    counts=Counter(find(i) for i in range(len(rows)))
    forced={find(i) for i,r in enumerate(rows) if r["id"] in fixed}
    components=sorted(((size,root in forced) for root,size in counts.items()),reverse=True)
    sizes=[size for size,_ in components]
    # Exact bounded dynamic programming: state is counts in dev/val/reserved.
    reachable={(0,0,0)};limits=tuple(SPLITS.values())
    for size,development_only in components:
        nxt=set()
        for state in reachable:
            for k in ((0,) if development_only else range(3)):
                v=list(state);v[k]+=size
                if v[k]<=limits[k]:nxt.add(tuple(v))
        reachable=nxt
        if not reachable:break
    exact_categories=dict(Counter(r["category"] for r in rows))==TARGETS
    full=len(rows)==60
    return {"cases":len(rows),"components":len(sizes),"component_sizes":sizes,
            "capacity_feasible":bool(reachable),"exact_60_feasible":full and exact_categories and limits in reachable,
            "complete":full,"category_totals_match":exact_categories,
            "semantic_tags_verified":False,"semantic_certification":False}
