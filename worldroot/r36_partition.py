"""Private metadata-only connected component feasibility; no corpus or labels."""
from collections import Counter
from .r36_benchmark import FIELDS,TARGETS,SPLITS,validate_inventory,require

def feasibility(rows):
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
    sizes=sorted(Counter(find(i) for i in range(len(rows))).values(),reverse=True)
    # Exact bounded dynamic programming: state is counts in dev/val/reserved.
    reachable={(0,0,0)};limits=tuple(SPLITS.values())
    for size in sizes:
        nxt=set()
        for state in reachable:
            for k in range(3):
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
