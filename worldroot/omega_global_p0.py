"""OMEGA P0: read-only global inventory; no semantic promotion or public corpus export."""
import argparse, json, re, subprocess
from pathlib import Path
from collections import Counter, defaultdict
from .omega_hybrid_receipt import ROOT, ARCHIVE, read
from .omega_turbo_recovery import SourceCache, anchor, git_blob, require, digest
from .omega_book_iv_macro31 import verify_book_vi_116
from .git_cycle import verify_episode, _journal, review_deltas
from .live_codex import norm

BASE="75b7929ce081e9a3e2b57dab7b2b2ed30afa760f"
QUEUE="e5a5f9e358d20acf8559f6313c2da24b64665f48"
CHECKPOINT="646366e51791243b4e387fd6dd0faf144f4dc9ab"
PROJECT="CRONICAS_DE_UM_NOVO_MUNDO"
PREFIX="audit/omega008-c/"
REGISTRY_PINS={
"universal-codex-design-d580-v1.json":"3f004e6209a46b42a35291bb40fee8386bc7d6ca",
"r35-living-overlay-manifest.json":"02525c88956350aebfc2ef4d05e039b784593c75",
"r35-natural-completion-d579-v14.json":"db6190d652c35e87ad8c6f670de077e3b13b816e",
"r35-world-completion-d579-v12.json":"7eabe936795808d65a6a2f8c12a742475a9a3605",
"r35-legacy-name-reconciliation-v10.json":"baffe1ae35556394a8cbdc788197e741b88e269f",
"female-character-design-d580-v2.json":"df2504b0721cc08ebc038f11070e793ef770d7d6"}
def stable(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
def paths_for(root,n):
    if n==1:return [PREFIX+"book-I/lote-0001.json",PREFIX+"book-I/lote-0002.json"]
    if n==2:return [PREFIX+"bulk-pilot-semantic-sample.json",PREFIX+"bulk-semantic-macro-0002.json"]
    if n<=22:return [PREFIX+"bulk-semantic-macro-%04d.json"%n]
    if n<=24:return [PREFIX+"turbo-v2/pilot-macro-%04d.json"%n]
    if n<=29:return [ROOT+"macro-%04d-complete.json"%n]
    return [str(x.relative_to(root)) for x in sorted((root/ROOT).glob("partial-macro-%04d-*.json"%n))]
def inspect(root,archive,*, inventory_consumer=None):
    root=Path(root).resolve();archive=Path(archive).resolve()
    require(subprocess.check_output(["git","-C",str(archive),"rev-parse","HEAD"],text=True).strip()==ARCHIVE,"archive pin")
    require(not subprocess.check_output(["git","-C",str(archive),"status","--porcelain"],text=True).strip(),"archive dirty")
    cp=read(root,ROOT+"recovery-checkpoint-0116-validated.json",CHECKPOINT)
    readiness=read(root,ROOT+"global-readiness-d579-v1.json","c90842d763953693ab749b36349497e2eb60b9d0")
    evidence=read(root,cp["native_evidence_path"],"d379a430c2107020d7c6cfd68e7dbff4331c9113")
    require(evidence["jobs"][1]["aggregate"]["status"]=="PASS_NATIVE_BOOK_VI_0116_QUEUE_COMPLETE" and evidence["workflow_conclusion"]=="success","terminal receipt")
    prior=verify_book_vi_116(root,archive)
    require(prior["queue_exhausted"] and prior["journal_prefix_verified"]==50,"cumulative recovery")
    q=read(root,PREFIX+"bulk-macro-queue.json",QUEUE)["macros"]
    require(len(q)==116 and all(m["previous_macro"]==(q[i-1]["id"] if i else None) for i,m in enumerate(q)),"queue chain")
    manifest=read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")
    cache=SourceCache(archive,manifest)
    baseline=read(root,ROOT+"hybrid-approved-baseline.json","30358c0192d501d4d9995b355b1106a35aa9a832")
    corrections={x["record_id"]:x["axis"] for x in baseline["prior_audit"]["correction_operations"][1]["records"]}
    legacy_alias=set(baseline["prior_audit"]["legacy_authority"]["records"])
    registry_files={p:read(archive,"editorial/registries/"+p,sha) for p,sha in REGISTRY_PINS.items()}
    registry=registry_files["universal-codex-design-d580-v1.json"]
    regrows=registry["records"]+registry["species"]+registry["arcane"]["schools"]+registry["arcane"]["index"]
    idx=defaultdict(set)
    for row in regrows:
        for label in [row["id"],row["name"],*row.get("aliases",[])]:idx[norm(label)].add(row["id"])
    require(len({r["id"] for r in regrows})==len(regrows),"registry unique ids")
    scope_overlay=read(root,ROOT+"global-p0-dream-scope-overlay-v1.json","0d339ef0f6e954f72907f6854c05192db533a24b")
    scope_rows={x["id"]:x for x in scope_overlay["rows"]}
    require(len(scope_rows)==2 and scope_overlay["production_gate"]=="HOLD" and scope_overlay["semantic_certification"] is False,"scope overlay")
    used_scope=set()
    inventory=[]; ids=set(); keys=Counter(); issues=Counter(); blocks=Counter(); group_rows=[]; receipt_pins=[]; scope_findings=[]; legacy_partition=[]
    authorities=Counter(); books=Counter(); scopes=Counter(); roles=Counter(); kinds=Counter(); axes=Counter(); dispositions=Counter(); labels=set()
    total_lines=covered_lines=0; original_events=original_knowledge=0; prior_ends={}
    journal=list(_journal(archive));require(len(journal)==50,"journal count")
    for i,m in enumerate(q,1):
        lo,hi=m["start"],m["end"]
        require(lo==prior_ends.get(m["source"],0)+1 and hi-lo+1==m["lines"],"queue geometry")
        prior_ends[m["source"]]=hi
        total_lines+=m["lines"]
        if i<=66:source=cache.get(m["source"])
        else:
            d,_=verify_episode(archive,m["source"]);L=tuple(d.prose.splitlines())
            p=archive/"episodes"/m["source"]/"draft"/"episode_draft.json"
            source=(L,("Response",)*len(L),((1,len(L),git_blob(p.read_bytes())),),digest(d.prose))
            ev,kn=review_deltas(archive,m["source"],d)
            original_events+=len(ev);original_knowledge+=len(kn)
        ps=paths_for(root,i);require(bool(ps),"missing receipt files")
        at=lo;num=0;covlines=0;spans=[]
        header_pins={42:"df70aebc309db67f24a5be40ddd3b76303851a09",45:"4b07608e05ae3b5ebc20d133ba0d96765e5832d9",53:"619e519afcc45bf7f6da92e956dd204b20a05853",57:"c32e350ab924e2c58784bc7946df897991543be4"}
        if i in header_pins:
            path=ROOT+"macro-%04d-source-header-metadata.json"%i
            h=read(root,path,header_pins[i])
            require(h["source"]==m["source"] and h["range"]==[1,8] and lo==1 and h["source_sha256"]==source[3] and h["promotion"] is False,"header authority")
            require(h["span_sha256_utf8"]==anchor(source,1,8) and all(v=="Metadata" for v in source[1][:8]) and h["blob_sha1"] in {p[2] for p in source[2] if p[0]<=8 and p[1]>=1},"header provenance")
            require(h.get("role","Metadata")=="Metadata" and (h.get("disposition")=="NON_NARRATIVE_EXPORT_METADATA" or h.get("authority")=="METADATA_NOT_EVENT"),"header metadata")
            at=9;covlines=8
            issues["separate_export_headers"]+=1
            receipt_pins.append([path,header_pins[i],digest((root/path).read_bytes())])
        for path in ps:
            raw=(root/path).read_bytes();r=json.loads(raw);receipt_blob=git_blob(raw)
            receipt_pins.append([path,receipt_blob,digest(raw)])
            require(r.get("project",PROJECT)==PROJECT and r.get("archive_pin",r.get("source_archive",ARCHIVE))==ARCHIVE,"receipt project")
            require(r.get("macro_id",m["id"])==m["id"] and r.get("previous_macro_id",m["previous_macro"])==m["previous_macro"],"receipt chain")
            require(not any(r.get(k,False) for k in ("canon_changed","promotion","semantic_certification","independent_review","official_checkpoint_changed")),"false authority")
            bounds=r.get("range",r.get("reviewed_sample_range"))
            require(bounds and bounds[0]==at and bounds[1]<=hi,f"receipt interval macro {i}: expected {at}..{hi}, got {bounds}")
            at=bounds[1]+1
            axes25={x["id"]:x["axes"] for x in r.get("axis_overlay_original_partial",[])}
            current={}
            def check_span(e,role,start,end,h):
                require(bounds[0]<=start<=end<=bounds[1],"span range")
                require(anchor(source,start,end)==h,"anchor mismatch")
                require(all(t==role for t in source[1][start-1:end]),"role mismatch")
                if e:
                    actual={p[2] for p in source[2] if p[0]<=end and p[1]>=start}
                    given=set(e.get("blob_sha1_parts",e.get("source_blob_sha1s",[e.get("blob_sha1")])))
                    if given!=actual or (e.get("blob_sha1") not in actual and not(e.get("blob_sha1") is None and len(actual)>1)):
                        blocks["physical_blob_mismatch"]+=1
            for rec in r["records"]:
                rid=rec["id"];e=rec["evidence"];a,z=e["line_start"],e["line_end"];role=e["role"]
                require(rid not in ids and rec["promotion"] is False,"record uniqueness/promotion")
                require(e["source"]==m["source"] and e["source_sha256_manifest"]==source[3],"source identity")
                check_span(e,role,a,z,e["span_sha256_utf8"])
                au=rec["authority"];vis=rec["visibility"];typ=rec["type"]
                require("NO_CHARACTER_INJECTION" in vis,"visibility")
                if au=="AUTHOR_REQUEST_OR_CHOICE":
                    require(rid in legacy_alias,"unexpected legacy alias")
                    au="AUTHOR_DIRECTION_NOT_EVENT"
                if role=="Prompt" and au!="AUTHOR_DIRECTION_NOT_EVENT":blocks["prompt_authority"]+=1
                if role=="Metadata" and au!="METADATA_NOT_EVENT":blocks["metadata_authority"]+=1
                original_vis=vis
                if rid in scope_rows:
                    patch=scope_rows[rid]
                    require(patch["macro"]==i and patch["receipt_blob"]==receipt_blob and patch["anchor"]==e["span_sha256_utf8"] and patch["interval"]==[a,z] and patch["original_visibility"]==vis and typ=="dream" and patch["promotion"] is False,"scope patch binding")
                    markers=patch["literal_markers"]
                    require(all(a<=k<=z for k in markers),"scope markers bounds")
                    marker_text=[source[0][k-1].lower() for k in markers]
                    require(("sonho" in marker_text[0] and "profecia" in marker_text[1]) or ("pesadelo" in marker_text[0] and "acordou" in marker_text[1]),"literal dream separation")
                    vis=patch["effective_visibility"];require(vis=="READER_ONLY_NO_CHARACTER_INJECTION","scope restriction")
                    used_scope.add(rid)
                    scope_findings.append(dict(id=rid,macro=i,type=typ,visibility=original_vis,effective_visibility=vis,authority=au,receipt_blob=receipt_blob,status="RESTRICTED_PENDING_ATOMIC_SPLIT"))
                if typ in ("reader-only","reader-perspectives","reader_scene","reader_perspective","reader_lore","private_knowledge","private_strategy","private_lore","dream","variant") and not vis.startswith("READER_ONLY"):
                    blocks["reader_scope"]+=1
                    scope_findings.append(dict(id=rid,macro=i,type=typ,visibility=vis,authority=au,receipt_blob=receipt_blob))
                effective=set(rec.get("axes",axes25.get(rid,[])))
                if rid in corrections:effective.add(corrections[rid])
                require(effective and effective<=set(range(1,31)),"axes")
                disposition="PENDING_ATOMIC_SCOPE_SPLIT" if rid in scope_rows else "PENDING_ATOMIC_REVIEW" if au=="HISTORICAL_RESPONSE_NOT_CANON_CERTIFIED" else "NON_EVENT_OR_GAP_REVIEW"
                row=dict(id=rid,macro=i,receipt_path=path,receipt_blob=receipt_blob,source=m["source"],source_sha256=source[3],physical_blobs=sorted({p[2] for p in source[2] if p[0]<=z and p[1]>=a}),interval=[a,z],anchor=e["span_sha256_utf8"],role=role,original_authority=rec["authority"],authority=au,book=rec.get("book"),day=rec.get("day"),entities=rec.get("entities",[]),original_visibility=original_vis,visibility=vis,classification=typ,axes=sorted(effective),review_state=rec.get("verification","GROUPED_CANDIDATE"),disposition=disposition,semantic_verdict=None,promotion=False)
                inventory.append(row);ids.add(rid);current[rid]=e;num+=1
                keys[(m["source"],a,z,e["span_sha256_utf8"])]+=1
                authorities[au]+=1;books[str(row["book"])]+=1;scopes[vis]+=1;roles[role]+=1;kinds[typ]+=1;axes.update(effective);dispositions[disposition]+=1
                labels.update(rec.get("entities",[]))
            coverage=r.get("coverage")
            if coverage is None:
                issues["legacy_receipts_without_explicit_coverage"]+=1
                issues["legacy_lines_without_explicit_coverage"]+=bounds[1]-bounds[0]+1
                # Partition missing documentation by exact role and existing record membership.
                # Unannotated text is explicitly pending, never deemed recovered semantic facts.
                chunks=[];last=None
                for pos in range(bounds[0],bounds[1]+1):
                    member=sorted(rid for rid,e in current.items() if e["line_start"]<=pos<=e["line_end"])
                    role=source[1][pos-1]
                    key=(role,tuple(member))
                    if last==key:chunks[-1]["end"]=pos
                    else:
                        chunks.append(dict(macro=i,receipt_blob=receipt_blob,source=m["source"],start=pos,end=pos,role=role,record_ids=member,disposition="EXISTING_ANCHOR_NOT_SEMANTIC_CERTIFIED" if member else "METADATA_NOT_EVENT" if role=="Metadata" else "UNANNOTATED_PENDING_P1"))
                    last=key
                for chunk in chunks:
                    chunk["sha256"]=anchor(source,chunk["start"],chunk["end"])
                require(sum(c["end"]-c["start"]+1 for c in chunks)==bounds[1]-bounds[0]+1,"legacy partition")
                legacy_partition.extend(chunks)
            else:
                cursor=bounds[0];seen=set()
                for c in coverage:
                    a,z=c["start"],c["end"]
                    require(a==cursor,f"coverage gap macro {i}: expected {cursor}, got {a}")
                    check_span(None,c["role"],a,z,c["span_sha256_utf8"])
                    for rid in c["record_ids"]:
                        require(rid in current and rid not in seen,"coverage membership")
                        e=current[rid];require(a<=e["line_start"]<=e["line_end"]<=z and e["role"]==c["role"],"coverage anchor membership")
                        seen.add(rid)
                    if not c["record_ids"]:issues["empty_record_metadata_spans"]+=1
                    cursor=z+1;covlines+=z-a+1
                require(cursor==bounds[1]+1 and seen==set(current),"coverage completion")
        require(at==hi+1,f"macro receipt coverage {i}: {at} vs {hi+1}")
        group_rows.append(dict(macro=i,records=num,lines=m["lines"],explicit_coverage_lines=covlines,receipts=len(ps)))
        covered_lines+=covlines
    # The partial 0025 is an immutable predecessor, not an additional receipt.
    partial=read(root,ROOT+"partial-macro-0025-01.json","b58cf20bb7b245ad10a5e9840b5c3a9746f330aa")
    complete=read(root,ROOT+"macro-0025-complete.json","d512cbf56ca3a0562df2dc98da0e24c857101634")
    byid={x["id"]:x for x in complete["records"]}
    require(all(x==byid[x["id"]] for x in partial["records"]),"partial overlap differs")
    require(len(ids)==len(inventory),"duplicate IDs")
    duplicate_spans=sum(v-1 for v in keys.values() if v>1)
    label_counts=Counter("UNMATCHED" if not idx[norm(x)] else "AMBIGUOUS" if len(idx[norm(x)])>1 else "SINGLE_CANDIDATE" for x in labels)
    # Preserve all labels, never assign identity from a lexical match.
    registry_metrics={p:{"top_level_arrays":{k:len(v) for k,v in data.items() if isinstance(v,list)},"top_level_object_sizes":{k:len(v) for k,v in data.items() if isinstance(v,dict)}} for p,data in registry_files.items()}
    require(sum(x["lines"] for x in group_rows)==706293 and len(group_rows)==116 and len(prior_ends)==56,"global queue totals")
    policy=read(root,"worldroot/editorial_policy.json","615151fc89228ddb222ea01613c23e977f8c418b")
    require(policy["version"]==22 and len(policy["rules"])==130,"editorial policy")
    require(not subprocess.check_output(["git","-C",str(archive),"status","--porcelain"],text=True).strip(),"archive changed")
    require(len(inventory)==cp["staging_records"] and used_scope==set(scope_rows),"terminal record count/scope overlay")
    legacy_counts=Counter()
    for c in legacy_partition:legacy_counts[c["disposition"]]+=c["end"]-c["start"]+1
    require(sum(legacy_counts.values())==1679 and covered_lines+sum(legacy_counts.values())==total_lines,"legacy disposition coverage")
    p1_groups=[]
    for i in range(1,117):
        rows=[row for row in inventory if row["macro"]==i]
        p1_groups.append(dict(macro=i,records=len(rows),atomic_review_candidates=sum(row["disposition"] in ("PENDING_ATOMIC_REVIEW","PENDING_ATOMIC_SCOPE_SPLIT") for row in rows),non_event_or_gap=sum(row["disposition"]=="NON_EVENT_OR_GAP_REVIEW" for row in rows),sha256=digest(stable(rows))))
    if inventory_consumer is not None:
        inventory_consumer(inventory,p1_groups,legacy_partition)
    return {"legacy_partition_sha256":digest(stable(legacy_partition)),"legacy_partition_spans":len(legacy_partition),"legacy_partition_lines":dict(legacy_counts),"structural_disposition_lines":covered_lines+sum(legacy_counts.values()),"scope_findings":scope_findings,"p1_groups_sha256":digest(stable(p1_groups)),"p1_group_count":len(p1_groups),"status":"P0_INVENTORY_STRUCTURAL_PASS" if not blocks else "P0_INVENTORY_BLOCKED", "macros":len(group_rows),"records":len(inventory),"expected_records":cp["staging_records"],"record_count_matches":len(inventory)==cp["staging_records"],"legacy_records":sum(x["records"] for x in group_rows[:22]),"queue_lines":total_lines,"explicit_coverage_lines":covered_lines,"unique_ids":len(ids),"duplicate_exact_spans_additional":duplicate_spans,"receipt_files":len(receipt_pins),"excluded_duplicate_partial_records":len(partial["records"]),"authority":dict(authorities),"book":dict(books),"role":dict(roles),"visibility":dict(scopes),"types":dict(kinds),"effective_axes":dict(axes),"dispositions":dict(dispositions),"label_counts":dict(label_counts),"unique_entity_labels":len(labels),"registry_ids":len(regrows),"registry_files":registry_metrics,"original_closed_events":original_events,"original_closed_knowledge":original_knowledge,"macro_metrics":group_rows,"issues":dict(issues),"blockers":dict(blocks),"inventory_sha256":digest(stable(inventory)),"receipt_manifest_sha256":digest(stable(receipt_pins)),"queue_unresolved":sum(m["book_hint"]=="V_OR_VI_UNRESOLVED" for m in q),"cumulative_status":prior["status"],"atomic_claims_certified":0,"independent_review":False,"typed_projection":False,"production_gate":"HOLD","canon_changed":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--engine-root",default=".");p.add_argument("--archive-root",required=True)
    a=p.parse_args()
    print(json.dumps(inspect(a.engine_root,a.archive_root),sort_keys=True))
if __name__=="__main__":main()
