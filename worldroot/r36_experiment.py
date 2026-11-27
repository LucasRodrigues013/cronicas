"""Paired experiment metadata and descriptive metrics, never a release gate."""
from statistics import median
from .r36_trust import require,digest
from .semantic_queue import seal
from .r36_evaluation import blind_pair,reverse_pair
from .r36_calibration import comparison_context

VERSION="r36-e7-experiment-v1"
PINS={"input_sha","source_sha","policy_sha","rubric_sha","dataset_sha","case_ids","split"}
def freeze(champion,challenger,common,configuration_diff):
    require(digest(champion) and digest(challenger) and champion!=challenger,"Distinct version pins required")
    require(isinstance(common,dict) and set(common)==PINS,"Invalid frozen inputs")
    require(all(digest(common[k]) for k in PINS-{"case_ids","split"}),"Missing pins")
    require(common["split"] in ("development","validation","reserved"),"Invalid split")
    ids=common["case_ids"]
    require(isinstance(ids,list) and bool(ids) and all(isinstance(x,str) and bool(x.strip()) for x in ids) and len(set(ids))==len(ids),"Invalid case IDs")
    require(isinstance(configuration_diff,dict) and bool(configuration_diff),"Declare configuration differences")
    p={"schema":VERSION,"champion":champion,"challenger":challenger,"common":{**common,"case_ids":sorted(ids)},
       "configuration_diff":configuration_diff}
    return {**p,"experiment_id":seal(p)}

def blind_experiment(experiment,case_id,first,second,judge):
    require(experiment["experiment_id"]==seal({k:v for k,v in experiment.items() if k!="experiment_id"}),"Experiment changed")
    require(case_id in experiment["common"]["case_ids"],"Unbound case")
    pair=blind_pair(first,second,judge)
    return pair,reverse_pair(pair.packet),comparison_context(first,second)

FIELDS={"case_id","input_sha","critical","correct","retrieved","expected","evidence_bound","evidence_total",
        "recurrence","author_agree","author_total","latency_ns","context_bytes","outcome"}
def paired_metrics(experiment,champion,challenger):
    require(experiment["experiment_id"]==seal({k:v for k,v in experiment.items() if k!="experiment_id"}),"Experiment changed")
    def collect(rows):
        data={}
        for r in rows:
            require(set(r)==FIELDS and r["case_id"] not in data and digest(r["input_sha"]),"Invalid or duplicate result")
            for k in FIELDS-{"case_id","input_sha","outcome"}:
                require(type(r[k]) is int and r[k]>=0,"Invalid count")
            require(r["correct"]<=1 and r["retrieved"]<=r["expected"] and r["evidence_bound"]<=r["evidence_total"]
                    and r["author_agree"]<=r["author_total"] and r["outcome"] in ("DECISIVE","ABSTAIN","INCONCLUSIVE"),"Invalid metric values")
            require(r["outcome"]=="DECISIVE" or r["correct"]==0,"Abstention cannot be correct")
            data[r["case_id"]]=r
        require(set(data)==set(experiment["common"]["case_ids"]),"Missing or extra paired cases")
        return data
    a,b=collect(champion),collect(challenger)
    require(all(a[k]["input_sha"]==b[k]["input_sha"] and a[k]["expected"]==b[k]["expected"] and a[k]["author_total"]==b[k]["author_total"] for k in a),"Non-equivalent case inputs")
    def ratio(n,d):return n/d if d else None
    def totals(data):
        v=list(data.values());n=len(v)
        s=lambda k:sum(x[k] for x in v)
        return {"n":n,"critical":s("critical"),"accuracy_all":s("correct")/n,"retrieval":ratio(s("retrieved"),s("expected")),
                "evidence":ratio(s("evidence_bound"),s("evidence_total")),"author_agreement":ratio(s("author_agree"),s("author_total")),
                "coverage":sum(x["outcome"]=="DECISIVE" for x in v)/n,"recurrence":s("recurrence"),
                "median_latency_ns":median(x["latency_ns"] for x in v),"median_context_bytes":median(x["context_bytes"] for x in v)}
    x,y=totals(a),totals(b)
    reduction=lambda k:ratio(x[k]-y[k],x[k])
    return {"champion":x,"challenger":y,"critical_regression_cases":sum(b[k]["critical"]>a[k]["critical"] for k in a),
            "recurrence_reduction":reduction("recurrence"),"latency_reduction":reduction("median_latency_ns"),
            "context_reduction":reduction("median_context_bytes"),
            "feedback_eligible":False,"measurement_attested":False,"production_hold":True,"semantic_certification":False}
