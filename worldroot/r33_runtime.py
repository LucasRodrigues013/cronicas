"""R33 immutable preparation contract, inspired by engineering patterns only.
No author choice creation, canon promotion, or narrative generation.
"""
from __future__ import annotations
import json,hashlib,os,tempfile,re
from pathlib import Path
from .git_cycle import canonical,sha,check_id,verify_episode
from .editorial_guard import POLICY_PATH, load_policy
from .editorial_receipt import prepare_editorial_receipt, verify_editorial_receipt, _digest as editorial_digest
from .memory_continuity import DOMAINS,review_creation
from .r32_release import release_review

REVIEWS=("continuity","causality","identity_voice","relationships","power_inventory","world_agency","sensory_wonder","arc_payoff","choice_parity","visual_design","knowledge_location")
def read(path):
    if not path.is_file() or path.is_symlink():raise ValueError("Missing or unsafe source")
    return json.loads(path.read_text(encoding="utf-8"))
def digest(obj):return sha(canonical(obj))
def author_context(root,head):
    root=Path(root)
    if read(root/"canon/HEAD.json")!=head:raise ValueError("Stale HEAD")
    ident=head["episode_id"];check_id(ident)
    closure=read(root/"canon/episodes"/(ident+".json"))
    if closure.get("episode_id")!=ident or digest(closure)!=head.get("closure_sha256"):raise ValueError("Closure mismatch")
    if closure.get("ratification_kind")=="R36_EXPLICIT_RATIFICATION_NO_CONTINUATION":
        from .r36_authority import continuation
        from .git_cycle import _journal
        chain=list(_journal(root))
        if not chain or chain[-1][1]!=head:raise ValueError("Journal HEAD mismatch")
        later=continuation(root,ident)
        if later["choice"] is None:raise ValueError("Explicit continuation choice required")
        choice=later["choice"]
        draft,manifest=verify_episode(root,ident)
        if manifest["original_readback_sha256"]!=head.get("source_sha256"):raise ValueError("Draft source mismatch")
        return {"choice":choice,"choice_sha256":digest(choice),"menu_sha256":sha((root/"episodes"/ident/"draft/opcoes.json").read_bytes()),"closure_sha256":digest(closure),"policy_sha256":sha(POLICY_PATH.read_bytes())}
    option=closure.get("chosen_option")
    if type(option) is not int or option not in range(1,6):raise ValueError("Explicit normal choice required; exceptional ratifications use legacy flow")
    path=root/"choices"/ident/f"option-{option}.json"
    choice=read(path)
    if choice.get("schema")!="worldroot-author-choice-v1" or choice.get("author_source")!="USER_MESSAGE" or choice.get("episode_id")!=ident or choice.get("option")!=option or digest(choice)!=closure.get("choice_sha256"):raise ValueError("Author choice not bound to closed HEAD")
    draft,manifest=verify_episode(root,ident)
    if manifest["original_readback_sha256"]!=head.get("source_sha256"):raise ValueError("Draft source mismatch")
    return {"choice":choice,"choice_sha256":digest(choice),"menu_sha256":sha((root/"episodes"/ident/"draft/opcoes.json").read_bytes()),"closure_sha256":digest(closure),"policy_sha256":sha(POLICY_PATH.read_bytes())}
EDITORIAL_BUDGET = 1700


def preparation_required(root, ident, payload=None):
    """Persisted preparation/request/receipt outranks opt-in inbox fields."""
    check_id(ident)
    root = Path(root)
    paths = (root/"requests"/(ident+".json"), root/"preparations"/(ident+".json"),
             root/"episodes"/ident/"review/preparation_r33.json")
    if any(p.exists() or p.is_symlink() for p in paths):
        return True
    payload = payload or {}
    return (payload.get("metadata", {}).get("worldroot_revision") in (33,34,35)
            or any(k in payload for k in ("r33_review","r34_review","r35_review")))


def verify_preparation_editorial(packet, payload, head, *, historical=False):
    """Verify a trusted preparation pin, not a receipt supplied by the inbox."""
    receipt = packet.get("editorial_receipt")
    pin = packet.get("editorial_receipt_sha256")
    review = payload.get("r33_review")
    revision = 35 if "r35_plan" in packet else 34 if "r34_intent" in packet else 33
    if (packet.get("head") != head or not isinstance(receipt, dict)
            or not isinstance(pin, str) or not isinstance(review, dict)
            or review.get("preparation_sha256") != packet.get("preparation_sha256")
            or review.get("editorial_receipt_sha256") != pin
            or payload.get("metadata", {}).get("worldroot_revision") != revision):
        raise ValueError("Editorial preparation receipt missing, stale or downgraded")
    if historical:
        # Historical bytes are checked against their immutable pin, not
        # regenerated with a later policy or renderer.
        body = dict(receipt)
        seal = body.pop("receipt_sha256", None)
        if (seal != pin or editorial_digest(body) != pin
                or receipt.get("schema") != "worldroot-editorial-receipt-v1"
                or receipt.get("head_sha256") != editorial_digest(head)
                or receipt.get("budget_chars") != EDITORIAL_BUDGET
                or receipt.get("semantic_certification") is not False):
            raise ValueError("Historic editorial preparation receipt mismatch")
        result = {"integrity_verified": True, "semantic_certification": False,
                  "generation_evaluated": False}
    else:
        result = verify_editorial_receipt(receipt, head, load_policy(), pin,
                                          expected_budget=EDITORIAL_BUDGET)
    return {**result, "receipt_sha256": pin}


def preparation(root,head,delivery_id,requirements,reviewed,domain_review,scene_plan):
    check_id(delivery_id)
    if delivery_id==head["episode_id"]:raise ValueError("Cannot prepare already closed episode")
    if (Path(root)/"episodes"/delivery_id/"draft/manifesto_imutavel.json").exists():raise ValueError("Cannot prepare archived draft")
    auth=author_context(root,head)
    if not isinstance(requirements,list) or not 1<=len(requirements)<=80 or not all(isinstance(r,dict) for r in requirements):raise ValueError("Invalid requirements")
    ids=[r["id"] for r in requirements]
    if len(ids)!=len(set(ids)) or not any(r.get("critical") is True for r in requirements):raise ValueError("Require unique IDs and critical facts")
    if any(not isinstance(r.get("query"),str) or not r["query"].strip() for r in requirements):raise ValueError("Empty query")
    if not isinstance(domain_review,dict) or set(domain_review)!=set(DOMAINS):raise ValueError("Review all domains")
    for k,v in domain_review.items():
        if not isinstance(v,dict) or type(v.get("applicable")) is not bool or not isinstance(v.get("reason"),str) or not v["reason"].strip() or v["applicable"]!=any(r["domain"]==k for r in requirements):raise ValueError("Invalid domain justification")
    if not isinstance(scene_plan,list) or not 1<=len(scene_plan)<=30:raise ValueError("Missing scene plan")
    covered=set()
    for i,p in enumerate(scene_plan,1):
        if not isinstance(p,dict) or p.get("scene")!=i or not isinstance(p.get("purpose"),str) or not p["purpose"].strip() or not isinstance(p.get("ids"),list) or not p["ids"] or not set(p["ids"])<=set(ids):raise ValueError("Invalid scene plan")
        covered.update(p["ids"])
    if covered!=set(ids):raise ValueError("Unmapped requirements")
    report=review_creation(root,head,requirements,reviewed)
    if report["status"]!="REVIEWED_EVIDENCE_THRESHOLD_MET":raise ValueError("Memory threshold or critical evidence failed")
    result={"schema":"worldroot-r33-preparation-v1","project":"CRONICAS_DE_UM_NOVO_MUNDO","delivery_id":delivery_id,"head":head,"authority":auth,"requirements":requirements,"reviewed":reviewed,"domain_review":domain_review,"scene_plan":scene_plan,"memory":report,"canon_changed":False,"semantic_certification":False}
    editorial = prepare_editorial_receipt(head, load_policy(), EDITORIAL_BUDGET)
    result["editorial_receipt"] = editorial
    result["editorial_receipt_sha256"] = editorial["receipt_sha256"]
    result["preparation_sha256"]=digest(result)
    return result
def persist(path,packet):
    """Atomic no-clobber publication; concurrent exact retries are idempotent."""
    path=Path(path)
    if path.is_symlink():raise ValueError("Unsafe preparation path")
    path.parent.mkdir(parents=True,exist_ok=True)
    body=canonical(packet)
    fd,tmp=tempfile.mkstemp(dir=path.parent,prefix=".r33-")
    try:
        with os.fdopen(fd,"wb") as f:
            f.write(body);f.flush();os.fsync(f.fileno())
        try:os.link(tmp,path)
        except FileExistsError:
            if path.is_symlink() or path.read_bytes()!=body:raise ValueError("Conflicting immutable preparation")
            return "IDEMPOTENT"
        return "CREATED"
    finally:os.unlink(tmp)
def prepare_from_request(root,request):
    if request.get("schema")!="worldroot-r33-request-v1" or request.get("project")!="CRONICAS_DE_UM_NOVO_MUNDO":raise ValueError("Invalid request/project")
    ident=request["delivery_id"];check_id(ident)
    if read(Path(root)/"requests"/(ident+".json"))!=request:raise ValueError("Request must be persisted before preparation")
    packet=preparation(root,request["head"],ident,request["requirements"],request["reviewed"],request["domain_review"],request["scene_plan"])
    if packet["authority"]["choice_sha256"]!=request.get("choice_sha256"):raise ValueError("Request choice differs")
    if "r34_intent" in request:
        from .r34_experience import validate_intent
        packet["r34_intent"] = request["r34_intent"]
        packet["r34_intent_structure"] = validate_intent(request)
    if "r35_plan" in request:
        from .r35_longform import validate_plan
        if "r34_intent" not in packet:raise ValueError("R35 requires R34 intent")
        packet["r35_plan"]=request["r35_plan"]
        packet["r35_plan_structure"]=validate_plan(request,packet["authority"]["choice"])
    from .character_design import bind_request
    design=bind_request(root,request)
    if design is not None:packet["character_design"]=design
    from .live_codex import bind_request as bind_codex
    codex=bind_codex(root,request)
    if codex is not None:packet["universal_codex"]=codex
    packet.pop("preparation_sha256")
    packet["request_sha256"]=digest(request)
    packet["preparation_sha256"]=digest(packet)
    return {"result":persist(Path(root)/"preparations"/(ident+".json"),packet),"preparation_sha256":packet["preparation_sha256"],"delivery_id":ident,"editorial_receipt_sha256":packet["editorial_receipt_sha256"],"canon_changed":False}
def verify_submission(root,head,payload):
    ident=payload["delivery_id"];check_id(ident)
    packet=read(Path(root)/"preparations"/(ident+".json"))
    copy=dict(packet);recorded=copy.pop("preparation_sha256",None)
    if recorded!=digest(copy) or packet.get("delivery_id")!=ident or packet.get("head")!=head or packet.get("project")!="CRONICAS_DE_UM_NOVO_MUNDO":raise ValueError("Invalid or stale preparation")
    if author_context(root,head)!=packet["authority"]:raise ValueError("Changed source authority")
    request=read(Path(root)/"requests"/(ident+".json"))
    if digest(request)!=packet.get("request_sha256"):raise ValueError("Preparation request changed")
    review=payload.get("r33_review")
    if not isinstance(review,dict) or review.get("preparation_sha256")!=recorded:raise ValueError("Preparation not bound to submission")
    editorial = verify_preparation_editorial(packet, payload, head)
    r32=payload["r32_review"]
    for key in ("requirements","reviewed","domain_review"):
        if r32.get(key)!=packet[key]:raise ValueError("Preparation changed: "+key)
    if r32.get("scene_requirements")!=[{"scene":p["scene"],"ids":p["ids"]} for p in packet["scene_plan"]]:
        if not isinstance(review.get("scene_plan_revision_reason"),str) or len(review["scene_plan_revision_reason"].split())<4:raise ValueError("Explain organic scene plan adjustment; requirements must remain intact")
    for option,stored in zip(r32["arc_packet"]["options"],payload["choices"][:4]):
        if stored.get("description")!=option["promise"]:raise ValueError("Stored choice intent differs from displayed promise")
    reviews=review.get("reviews")
    if not isinstance(reviews,dict) or set(reviews)!=set(REVIEWS):raise ValueError("Review all eleven dimensions")
    prose=payload["prose"]
    for k,v in reviews.items():
        if not isinstance(v,dict) or v.get("status") not in ("applied","held") or not isinstance(v.get("reason"),str) or len(v["reason"].split())<4:raise ValueError("Invalid literary review: "+k)
        if v["status"]=="applied" and (not isinstance(v.get("evidence"),str) or len(v["evidence"].split())<4 or v["evidence"] not in prose):raise ValueError("Missing literal literary evidence: "+k)
    from .character_design import verify_binding
    design=verify_binding(root,request,packet)
    r=release_review(root,head,payload)
    extra={"editorial": editorial}
    from .live_codex import validate_submission as validate_codex_submission
    codex=validate_codex_submission(root,request,packet,payload)
    if codex is not None:extra.update(codex)
    if design is not None:extra["character_design_sha256"]=design["sha256"]
    if payload.get("metadata",{}).get("worldroot_revision") in (34,35) or "r34_review" in payload:
        if payload.get("metadata",{}).get("worldroot_revision") not in (34,35):raise ValueError("R34 review requires revision 34 or 35 metadata")
        from .r34_experience import validate_intent,validate_delivery
        if "r34_intent" not in packet or packet["r34_intent"]!=request.get("r34_intent"):raise ValueError("R34 intent must be bound before prose")
        validate_intent(request)
        extra["r34"] = validate_delivery(request,payload)
    elif "r34_intent" in packet:raise ValueError("R34 preparation requires R34 delivery")
    if payload.get("metadata",{}).get("worldroot_revision")==35 or "r35_review" in payload:
        from .r35_longform import validate_plan,validate_delivery
        if payload.get("metadata",{}).get("worldroot_revision")!=35 or "r35_plan" not in packet or packet["r35_plan"]!=request.get("r35_plan"):raise ValueError("R35 plan must be bound before prose")
        validate_plan(request,packet["authority"]["choice"])
        extra["r35"]=validate_delivery(root,request,payload,packet["authority"]["choice"])
    elif "r35_plan" in packet:raise ValueError("R35 preparation requires R35 delivery")
    return {**extra,"schema":"worldroot-r33-receipt-v1","preparation_sha256":recorded,"request_sha256":packet["request_sha256"],"source_head_sha256":digest(head),"choice_sha256":packet["authority"]["choice_sha256"],"prose_sha256":hashlib.sha256(prose.encode()).hexdigest(),"r32":r,"reviews":reviews,"canon_changed":False,"semantic_certification":False}
def verify_archived_preparation(root, ident, payload=None, *, current_head=None):
    """Read one archived preparation without rewriting historical records."""
    root=Path(root);check_id(ident)
    receipt=read(root/"episodes"/ident/"review/preparation_r33.json");request=read(root/"requests"/(ident+".json"));prep=read(root/"preparations"/(ident+".json"))
    value=dict(prep);seal=value.pop("preparation_sha256",None)
    if not seal or digest(value)!=seal or digest(request)!=prep.get("request_sha256"):raise ValueError("Historic request/preparation mismatch")
    if receipt.get("preparation_sha256")!=seal or receipt.get("request_sha256")!=digest(request) or receipt.get("source_head_sha256")!=digest(prep["head"]) or receipt.get("choice_sha256")!=prep["authority"]["choice_sha256"]:raise ValueError("Historic receipt mismatch")
    draft,manifest=verify_episode(root,ident)
    if receipt.get("source_sha256")!=manifest["original_readback_sha256"] or receipt.get("prose_sha256")!=hashlib.sha256(draft.prose.encode()).hexdigest():raise ValueError("Historic prose mismatch")
    if "r34" in receipt:
        inbox=read(root/"inbox"/(ident+".json"))
        if inbox.get("metadata",{}).get("worldroot_revision") not in (34,35) or receipt.get("r34_input_sha256")!=digest(inbox.get("r34_review")) or prep.get("r34_intent")!=request.get("r34_intent"):
            raise ValueError("Historic R34 intent/review mismatch")
    if "r35" in receipt:
        from .longform_segments import verify_longform_segments
        inbox=read(root/"inbox"/(ident+".json"))
        if inbox.get("metadata",{}).get("worldroot_revision")!=35 or receipt.get("r35_input_sha256")!=digest(inbox.get("r35_review")) or prep.get("r35_plan")!=request.get("r35_plan") or not verify_longform_segments(root,ident,inbox)["verified"]:
            raise ValueError("Historic R35 plan/review/segments mismatch")
    if "character_design" in prep and receipt.get("character_design_sha256")!=prep["character_design"]["sha256"]:raise ValueError("Historic character design binding mismatch")

    marker = manifest.get("editorial_preparation")
    new_contract = ("editorial_receipt" in prep or "editorial_receipt_sha256" in prep
                    or "editorial" in receipt or "editorial_preparation" in manifest)
    if new_contract:
        inbox = read(root/"inbox"/(ident+".json"))
        if payload is not None and inbox != payload:
            raise ValueError("Archived inbox differs")
        if current_head is not None and current_head != prep["head"]:
            raise ValueError("Stale editorial source HEAD")
        editorial = verify_preparation_editorial(prep, inbox, prep["head"], historical=True)
        expected_marker = {"preparation_sha256": seal,
                           "receipt_sha256": editorial["receipt_sha256"],
                           "review_sha256": digest(receipt)}
        if (marker != expected_marker or receipt.get("editorial") != editorial
                or receipt.get("review_input_sha256") != digest(inbox.get("r33_review"))
                or draft.metadata != inbox.get("metadata")
                or ("r34_intent" in prep and "r34" not in receipt)
                or ("r35_plan" in prep and "r35" not in receipt)):
            raise ValueError("Archived editorial preparation binding mismatch")
    return {"receipt": receipt, "manifest": manifest, "editorial_verified": new_contract}


def verify_history(root):
    """Read back all R33 receipts and archived preparations, including missing-sidecar detection."""
    root=Path(root);ids=set()
    for file in (root/"episodes").glob("*/review/preparation_r33.json"):
        ids.add(file.parent.parent.name)
    for file in (root/"episodes").glob("*/draft/manifesto_imutavel.json"):
        ident=file.parent.parent.name
        manifest=read(file)
        if "editorial_preparation" in manifest or preparation_required(root,ident):
            ids.add(ident)
    for ident in sorted(ids):
        verify_archived_preparation(root,ident)
    return {"verified_r33_receipts":len(ids),"canon_changed":False}

def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--archive-root",type=Path,required=True);p.add_argument("--request",type=Path);p.add_argument("--verify-history",action="store_true");a=p.parse_args()
    if bool(a.request)==a.verify_history:p.error("Choose --request or --verify-history")
    result=verify_history(a.archive_root) if a.verify_history else prepare_from_request(a.archive_root,read(a.request))
    print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
