"""Read-only P1-A2 normalized claim overlay; preserves P1-A targets and review seals."""
import argparse,json
from pathlib import Path
from collections import Counter
from . import omega_global_p1a as base, omega_global_p0 as p0, live_codex as codex, semantic_queue as queue, r36_chat_review as chat
from .omega_hybrid_receipt import ROOT, read
from .omega_turbo_recovery import SourceCache,anchor,digest,require
CP="2ebe2e525f235f997aba6f9d5778faa6ed4eebf6"
EVIDENCE="1abca997e7d0860ef43aae5ae1c0608e46d24189"
NORMAL="8a5dbe12210e317dcc5645958665d1e664f46c01"
GAPS="e238ff0871b3e68624d2282baca77ead846000eb"
# State changes are explicit and local. The remaining targets are observations,
# assertions, proposals or questions, never fabricated before/after transitions.
TRANSITIONS={
(982,"self_chosen_name"):(None,"VARO","first localized self-naming; prior name unknown"),
(1453,"self_chosen_name"):(None,"KAEL","first localized self-naming"),
(700,"helmet_removed"):("worn","removed","scene"),
(1303,"restraint_loosened"):("restrained","partially_loosened","custody retained"),
(1303,"water_given_and_drunk"):(None,"water_drunk","ordered earlier; delivery now observed"),
(1072,"three_teams_of_four"):("not_released",{"teams":3,"per_team":4},"earlier report 890; dispatch 1074"),
(1561,"one_returns_injured"):({"no_contact":4},{"returned_injured":1,"no_contact":3},"earlier report 1177; outcome 1593"),
(1421,"person_manifested"):(None,"manifested","person first appears in this localized creation")}
COMPOUND={"initial_game_directions","experimental_prologue","reported_prior_campaign","creation_initial_constraint","reconnaissance_and_preservation_direction","defeat_demeanor","arrival_witness_report","gray_banner_violence_report","supply_capacity_unknown","created_people_reflection","victory_attribution","created_count_and_inspection","initial_aptitudes_report","intelligence_network_proposal","orc_combat_assessment","gray_banner_conditional","prisoner_care_order","three_envoys_dispatched","defense_inspection_state","armor_recovery_low_creation","realism_report_direction","camp_inspection_order","recon_avoid_combat_order","military_knowledge_self_report","no_prior_memory_self_report","camp_site_selection","temporary_defenses","water_food_rest_test_plan","recon_routes","independent_return_order","possible_river_crossing","messenger_departure_report","horse_appearance","equipment","strategic_assessment","vulnerability_assessment","risk_hypotheses","priority_recommendations","civil_specialists_needed","time_location","created_people_subjectivity","multiracial_nation_aspiration","coexistence_project","strategic_adviser_creation_request","desired_adviser_aptitudes","creation_resistance_pain","localized_blue_manifestation","self_reported_aptitudes","service_offer","humor_reaction","physical_weakness","armor_no_energy_replenishment","initial_aptitudes_panel","future_rights_duties_proposal","territory_food_security_needs","provisional_military_role","provisional_adviser_role","no_formal_institution_or_claim","one_returns_injured","separation_report","covered_cart_unknown_report","waiting_and_reaction_report","conscious_exhausted_armor_active","one_returned_three_no_contact"}
PROFILE={"hair":"hair","eye_color":"eyes","apparent_age":"age_apparent","apparent_youth":"age_apparent","facial_marks":"face","armor_design":"wardrobe","black_armor":"wardrobe","relative_height":"height_cm","height_estimate":"height_cm","identity":"identity","self_chosen_name":"identity","skill_name":"skills","equipment_dimensional_bag":"inventory","equipment_regenerative_armor":"equipment","origin_self_assertion":"origin","no_prior_memory_self_report":"history","world_knowledge_unknown":"knowledge","partial_orc_translation":"languages"}
def scope(modality):
    return {"NARRATED":"LOCAL_NARRATION","REPORT":"ATTRIBUTED_TESTIMONY_NOT_EXTERNAL_FACT","SUMMARY":"HISTORICAL_PANEL_OR_RECAP","PLAN":"INTENT_NOT_EXECUTION","HYPOTHESIS":"CONDITIONAL_NOT_CONFIRMED","OPTION":"PROPOSED_NOT_EXECUTED","META":"AUTHOR_OR_EDITORIAL_NOT_EVENT","DRAFT":"EXPERIMENTAL_NOT_CANON"}[modality]
def polarity(field,value):
    if value is None:return "UNKNOWN_NOT_NEGATIVE"
    if field in {"no_cavalry","no_pursuit_order","kingdom_not_founded","no_formal_institution_or_claim","confirmed_deaths","no_death_witnessed","no_prior_memory_self_report","not_permanent_fortress","armor_no_energy_replenishment","recon_not_released","diplomacy_no_meeting","specialists_not_automatic","road_origin_unknown","non_invincibility_assessment","armor_not_all_impacts","fallibility_acknowledged","trust_not_automatic","external_claims_unverified","casualty_count_unknown"}:return "EXPLICIT_SCOPED_NEGATION_OR_ZERO"
    return "AFFIRMATIVE_DESCRIPTION_NOT_CANON"
def apply(root,archive,consumer=None):
    root=Path(root);archive=Path(archive)
    cp=read(root,ROOT+"global-p1-a-checkpoint-v1.json",CP)
    ev=read(root,cp["native_evidence_path"],EVIDENCE)
    norm=read(root,ROOT+"global-p1-a2-normalization-overlay-v1.json",NORMAL)
    gap=read(root,ROOT+"global-p1-a2-gap-adjudication-v1.json",GAPS)
    raw=read(root,cp["target_path"],cp["target_blob"])
    got={}
    def collect(atoms,parts,packets):got.update(atoms=atoms,parts=parts,packets=packets)
    prior=base.build(root,archive,consumer=collect)
    require(prior["atom_sha256"]==cp["atom_sha256"]==norm["base_atom_sha256"] and prior["gap_sha256"]==cp["gap"]["sha256"]==gap["base_gap_sha256"] and prior["packet_manifest"]==ev["aggregate"]["packet_manifest"],"immutable prior seals")
    specs=[s for group in raw["groups"] for s in group.split(";")]+raw["gap_additions"]
    require(len(specs)==len(norm["rows"])==len(got["atoms"])==304,"normalization count")
    require([r["target"] for r in norm["rows"]]==specs,"target order changed")
    require(norm["semantic_certification"] is False and norm["promotion"] is False and gap["promotion"] is False,"promotion guard")
    source=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")).get(base.SOURCE)
    # Existing full registry and natural overlays, without SQLite or graph writes.
    data,registry_binding=codex.load_registry(archive)
    records=list(codex.all_records(data));byid={r["id"]:r for r in records}
    require(len(byid)==len(records),"registry duplicate")
    claims=[]
    for a,row,spec in zip(got["atoms"],norm["rows"],specs):
        lo,hi,entity,field,modality,verdict=base.parse(spec)
        require(a["interval"]==[lo,hi] and a["entity"]==entity and a["field"]==field and a["modality"]==modality and a["anchor"]==anchor(source,lo,hi),"source/target binding")
        require(a["literal_evidence"]=="\n".join(source[0][lo-1:hi]),"literal evidence")
        v=row["value"];reason=row["unknown_reason"]
        require((v is None)==bool(reason) and (v is None or v!=""),"explicit unknown/value")
        # Exact historic states must not be converted to current attributes.
        if field=="creation_reserve_estimate":
            require(v in ([5,5],[1,2]),"reserve")
            v={"percent_interval":v,"approximate":True}
        if field=="apparent_age":
            v={"years":v,"approximate":True,"age_kind":"apparent","biological_age":None}
        if field=="prior_enemy_count_recollection":
            v={"reported_count":v,"independent_count":False}
        if field=="count_estimate":
            v={"estimated_count":v,"exact_count":None}
        # Match actual registry domain/profile field, not a current value merge.
        matches=codex.aliases(records,entity)
        profile_field=PROFILE.get(field)
        candidates=[x["id"] for x in matches]
        profile_routes=[x["id"] for x in matches if profile_field in x.get("natural_profile",{}).get("fields",{})] if profile_field else []
        change=TRANSITIONS.get((lo,field))
        # Report/summary/plan cannot be an applied transition; these remain scoped values.
        require(change is None or modality=="NARRATED","non-narrated transition")
        subject=entity
        predicate={"kingdom_not_founded":"kingdom_founded","no_cavalry":"cavalry_count","no_pursuit_order":"pursuit_authorized"}.get(field,field)
        status="UNKNOWN_EXPLICIT" if v is None else "VALUE_NORMALIZED_COMPOUND_REVIEW" if field in COMPOUND else "VALUE_NORMALIZED"
        claims.append(dict(id=a["id"],target_id=a["target_id"],parent_id=a["parent_id"],source=a["source"],source_sha256=a["source_sha256"],physical_blobs=a["physical_blobs"],interval=a["interval"],anchor=a["anchor"],source_role=a["role"],authority=a["authority"],subject=subject,predicate=predicate,original_field=field,value=v,unknown_reason=reason,modality=modality,scope=scope(modality),polarity=polarity(field,v),condition={"status":"CONDITIONAL_OR_HYPOTHETICAL","description":v} if modality=="HYPOTHESIS" else {"status":"NOT_EXECUTED"} if modality in ("PLAN","OPTION","DRAFT") else None,day=a["day"],time={"source_line":lo,"current_state":False,"clock":None,"day_authority":"ORIGINAL_GROUP_HINT"},state_before=change[0] if change else None,state_after=change[1] if change else None,transition_basis=change[2] if change else "NO_EXPLICIT_TRANSITION_ASSERTED",visibility=a["visibility"],knowledge_injection=False,registry_candidates=candidates,profile_field_candidate=profile_field,profile_field_routes=profile_routes,identity_resolved=False,field_compatibility="PROFILE_FIELD_EXISTS_CANDIDATE_ONLY" if profile_routes else "NO_EXACT_PROFILE_FIELD_ROUTE",normalization_status=status,preliminary_verdict=verdict,independent_review=False,promotion=False))
    require([a["id"] for a in got["atoms"]]==[c["id"] for c in claims],"original IDs lost")
    # All 54 lines reviewed one by one; preserve broader partition and exact anchors.
    pending={n for g in got["parts"] if g["category"]=="RELEVANT_OR_REPETITION" for n in range(g["start"],g["end"]+1)}
    require(len(pending)==54 and set(x["line"] for x in gap["rows"])==pending and len(gap["rows"])==54,"gap adjudication coverage")
    adjudicated=[];new=[];targets=[]
    for g in gap["rows"]:
        n=g["line"];c=g["candidate"];r=g["repeat_reference_line"]
        require(source[1][n-1]=="Response" and source[0][n-1].strip(),"gap source")
        require(g["category"] in gap["definitions"] and (g["category"]=="NEW_CANDIDATE")==bool(c),"gap category")
        require((g["category"]=="REPETITION")==bool(r) and (r is None or 1<=r<=1679 and source[0][r-1].strip()),"repeat locator")
        adjudicated.append({**g,"anchor":anchor(source,n,n),"source":base.SOURCE,"promotion":False})
        if c:
            lo,hi=c["context"]
            require(lo<=n<=hi and all(x=="Response" for x in source[1][lo-1:hi]),"new context bounds")
            ident="P1A2-"+digest(p0.stable([base.SOURCE,n,c["entity"],c["field"]]))[:24]
            num=int(digest(ident)[:13],16)
            new.append(dict(id=ident,target_id=num,source=base.SOURCE,source_sha256=source[3],physical_blobs=sorted({p[2] for p in source[2] if p[0]<=n<=p[1]}),line=n,anchor=anchor(source,n,n),context_interval=[lo,hi],subject=c["entity"],predicate=c["field"],value=c["value"],modality=c["modality"],scope=scope(c["modality"]),day=1,source_role="Response",visibility="EDITORIAL_ONLY_NO_CHARACTER_INJECTION",authority="HISTORICAL_RESPONSE_NOT_CANON_CERTIFIED",independent_review=False,promotion=False))
            targets.append(dict(original_id=num,entity_id=c["entity"],field=c["field"],source=base.SOURCE,source_sha256=source[3],source_status="HISTORICAL_TRANSCRIPT_NOT_CANON_CERTIFIED",day=1,line=n,anchor=source[0][n-1],anchor_sha256=digest(source[0][n-1]),context=[dict(line=i,text=source[0][i-1]) for i in range(lo,hi+1)]))
    require(len(new)==10 and len({x["target_id"] for x in new+claims})==314,"new target collisions")
    jobs=list(queue.jobs(targets));packets=[]
    controller=queue.seal({"p1a":CP,"gap":GAPS,"scope":"supplemental-only"})
    for start in range(0,len(jobs),6):
        batch=jobs[start:start+6];ids=[j["job_id"] for j in batch];n=len(packets)+1
        a=chat.prepare_history(batch,ids,controller,"omega-p1-a2-extra-%03d-A"%n)
        b=chat.prepare_history(batch,ids,controller,"omega-p1-a2-extra-%03d-B"%n)
        require(chat.validate_history(a,a["batch_id"])==chat.validate_history(b,b["batch_id"]) and a["batch_id"]!=b["batch_id"],"extra seal")
        packets.append((a,b))
    # Targeted exact-source regressions. Distinguish reports, estimates and elapsed history.
    by=lambda n,f:next(c for c in claims if c["interval"][0]==n and c["original_field"]==f)
    require(sum(by(n,f)["value"] for n,f in [(1026,"fit_count"),(1030,"lightly_wounded_count"),(1034,"temporarily_unfit_count")])==by(1024,"alive_count")["value"]==300 and by(1038,"confirmed_deaths")["value"]==0 and by(265,"casualty_count_unknown")["value"] is None,"casualty chronology")
    require(by(259,"creation_reserve_estimate")["value"]["percent_interval"]==[5,5] and by(1485,"creation_reserve_estimate")["value"]["percent_interval"]==[1,2],"reserve chronology")
    require(by(982,"self_chosen_name")["value"]=="VARO" and by(1453,"self_chosen_name")["value"]=="KAEL" and by(704,"apparent_age")["value"]["biological_age"] is None,"name and age")
    require(by(527,"gray_banner_attribution")["scope"]=="ATTRIBUTED_TESTIMONY_NOT_EXTERNAL_FACT" and by(806,"identity_unknown")["value"] is None and by(1177,"four_missing_report")["value"]==4 and by(1593,"three_missing")["value"]==3,"knowledge and missing")
    require(by(151,"experimental_prologue")["scope"]=="EXPERIMENTAL_NOT_CANON" and by(1545,"no_formal_institution_or_claim")["value"]=={"formal_institution_established":False,"territorial_claim":False},"non event")
    require(all(not x["promotion"] and not x["independent_review"] for x in claims+new),"staging")
    if consumer:consumer(claims,adjudicated,new,packets)
    manifest=[dict(batch=i+1,jobs=len(a["jobs"]),targets=sum(len(j["targets"]) for j in a["jobs"]),A=a["batch_id"],B=b["batch_id"]) for i,(a,b) in enumerate(packets)]
    return dict(status="P1_A2_NORMALIZATION_OVERLAY_PASS_COMPOUND_AND_INDEPENDENT_HOLD",original_targets=len(claims),known_values=sum(c["value"] is not None for c in claims),unknown_values=sum(c["value"] is None for c in claims),normalization_status=dict(Counter(c["normalization_status"] for c in claims)),explicit_local_transitions=sum(c["transition_basis"]!="NO_EXPLICIT_TRANSITION_ASSERTED" for c in claims),gap_lines=len(adjudicated),gap_categories=dict(Counter(x["category"] for x in adjudicated)),new_targets=len(new),total_targets=len(claims)+len(new),original_packets_preserved=90,extra_packets=2*len(packets),extra_manifest=manifest,extra_controller=controller,registry_binding=registry_binding,registry_records=len(records),registry_alias_counts=dict(Counter("NONE" if not c["registry_candidates"] else "SINGLE" if len(c["registry_candidates"])==1 else "AMBIGUOUS" for c in claims)),profile_field_routes=sum(bool(c["profile_field_routes"]) for c in claims),identity_resolved=0,compound_fields=sorted({c["original_field"] for c in claims if c["normalization_status"]=="VALUE_NORMALIZED_COMPOUND_REVIEW"}),claims_sha256=digest(p0.stable(claims)),gaps_sha256=digest(p0.stable(adjudicated)),new_sha256=digest(p0.stable(new)),base_atom_sha256=prior["atom_sha256"],base_gap_sha256=prior["gap_sha256"],p0_inventory_sha256=prior["p0_inventory_sha256"],cumulative_status=prior["cumulative_status"],review_returns=0,semantic_certification=False,independent_review=False,typed_projection=False,production_gate="HOLD",canon_changed=False)
def main():
    p=argparse.ArgumentParser();p.add_argument("--engine-root",default=".");p.add_argument("--archive-root",required=True)
    a=p.parse_args();print(json.dumps(apply(a.engine_root,a.archive_root),sort_keys=True))
if __name__=="__main__":main()
