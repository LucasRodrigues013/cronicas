"""OMEGA-008 C bulk: deterministic evidence queue, not a semantic judge.
No API calls, production writes, raw prose export, or automatic canon promotion.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import time
from collections import Counter
from pathlib import Path
from .history_index import read_verified_sources
from .deep_recovery import sections, norm
from .omega_historical_recovery import alias_index, matcher
from .live_codex import load_registry
from .git_cycle import load, verify_episode

SCHEMA = "worldroot-omega008-c-bulk-v1"
AXES = {
 1:r"\bdia\b|ano|capitulo|livro|cronolog", 2:r"\b\d{1,2}h\d{2}\b|hora|minuto|manha|tarde|noite",
 3:r"acontec|chegou|partiu|retorn|criou|encontr|decid|ocorreu", 4:r"personag|soldado|comandante|cavaleiro|protagonista|nome",
 5:r"chamad|chamar|nome|identidade|alias|alcunha", 6:r"cabel|olhos|rosto|idade|estatura|pele|especie|aparencia|orc|elfo",
 7:r"personalidade|temperamento|autonomi|coragem|disciplin|prudencia|teimos|generos", 8:r"respondeu|perguntou|sussurr|gritou|ironia|humor|dialogo",
 9:r"amizade|companheir|confianca|esposa|irma|familia|relacion|aliad", 10:r"medo|alegria|dor|triste|raiva|culpa|emoc|entusiasm|amor",
 11:r"poder|habilidade|magia|mana|reserva|capacidade", 12:r"genese|creation|canal soberano|limiar|matriz germinal",
 13:r"inventario|mochila|armadura|equipamento|arma|anel|utensilio", 14:r"criacao|criou|criado|automato|manifestacao",
 15:r"tecnologia|maquina|motor|fabrica|engenhari|automato|artefato", 16:r"vale|estrada|rio|montanha|cidade|territorio|mapa|porto|regiao",
 17:r"arquitetura|muralha|torre|fortaleza|casa|edificio|acampamento|ponte", 18:r"cultura|tradicao|religiao|deus|costume|raca|povo|idioma|lingua",
 19:r"legiao|conselho|ordem|guilda|exercito|institui|reino|comando", 20:r"comercio|moeda|preco|suprimento|alimento|logistica|mercador",
 21:r"dungeon|masmorra|ruina|labirinto|caverna|cripta", 22:r"bestiario|criatura|monstro|dragao|fera|orc|animal",
 23:r"ameaca|inimigo|antagon|bandeira cinzenta|sabot|hostil|embosc", 24:r"batalha|combate|ataque|ferid|duelo|defesa|guerra",
 25:r"promess|juramento|compromisso|ordena|recomenda|missao", 26:r"misterio|desconhecid|segredo|desaparecid|incert|pista",
 27:r"conhec|relat|inform|testemunh|hipotese|confirm|verific", 28:r"opcao|escolh|decisao|escolha",
 29:r"narrativa|realismo|prefiro|quero|estilo|regra|autonomi|ritmo", 30:r"capitulo|arco|climax|narrativa|prosa|dialogo|epic|fantasia"
}
PATTERNS = {n:re.compile(p) for n,p in AXES.items()}
def digest_bytes(b): return hashlib.sha256(b).hexdigest()
def digest_text(s): return digest_bytes(s.encode("utf-8"))
def seal(obj): return digest_text(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",",":")))
def require(ok, message):
    if not ok: raise ValueError(message)
def axis_hits(text):
    text=norm(text)
    return [n for n,p in PATTERNS.items() if p.search(text)]
def source_regions(index, n, cursor):
    # Only explicitly evidenced boundaries. Export order is not event chronology.
    if index==1:
        require(n>=268704 and 1<=cursor<=40849,"Unexpected historical boundary")
        return [(1,cursor-1,"I","CONTROLLER_REVIEWED_PREFIX"),(cursor,40848,"I","PENDING"),
                (40849,135470,"II","PENDING"),(135471,268703,"III","PENDING"),
                (268704,n,"IV","PENDING")]
    if index==2: return [(1,n,"IV","PENDING")]
    if index==3:
        require(n>=8936,"Unexpected IV/V boundary")
        return [(1,8935,"IV","PENDING"),(8936,n,"V","PENDING")]
    return [(1,n,"V_OR_VI_UNRESOLVED","PENDING")]
def build_units(source, source_sha, body, regions, pattern, idx, max_lines=300, max_chars=24000, closed=False):
    require(1<=max_lines<=600 and max_chars>=100,"Invalid geometry")
    src_lines=body.splitlines(keepends=True)
    require(bool(src_lines),"Empty source")
    sects=[("CLOSED_NARRATIVE",1,src_lines)] if closed else list(sections(body))
    out=[]; ri=0
    regions=[r for r in regions if r[0]<=r[1]]
    for role,start,buf in sects:
        end=start+len(buf)-1
        at=start
        while at<=end:
            while ri<len(regions) and at>regions[ri][1]: ri+=1
            require(ri<len(regions),"Unmapped source line")
            lo,hi,book,status=regions[ri]
            require(lo<=at<=hi,"Region gap")
            cap=min(end,hi,at+max_lines-1)
            stop=at; size=0
            while stop<=cap:
                length=len(src_lines[stop-1])
                if stop>at and size+length>max_chars: break
                size+=length; stop+=1
            last=stop-1
            text="".join(src_lines[at-1:last])
            context_start=max(start,lo,at-12)
            context_end=min(end,hi,last+12)
            axes=axis_hits(text)
            aliases={x.group() for x in pattern.finditer(norm(text))}
            # Never export found raw strings, unregistered speakers or literal text.
            entity_ids={eid for key in aliases for eid in idx[key]}
            anchor=digest_text(text)
            unit_id=seal([source,source_sha,role,at,last,anchor])
            out.append(dict(id=unit_id,source=source,source_sha=source_sha,role=role,
                start=at,end=last,book_hint=book,status=status,anchor_sha256=anchor,
                context_start=context_start,context_end=context_end,
                context_sha256=digest_text("".join(src_lines[context_start-1:context_end])),
                axes=axes,entity_candidate_count=len(entity_ids),
                ambiguous_alias_count=sum(len(idx[k])>1 for k in aliases),
                oversized_line=size>max_chars,authority="AUTHOR_DIRECTION_NOT_EVENT" if role=="Prompt" else
                "NARRATIVE_UNREVIEWED" if role in ("Response","CLOSED_NARRATIVE") else "METADATA_NOT_EVENT",
                promotion=False))
            at=stop
    require(sum(u["end"]-u["start"]+1 for u in out)==len(src_lines),"Coverage mismatch")
    require(out[0]["start"]==1 and out[-1]["end"]==len(src_lines),"Endpoint mismatch")
    require(all(a["end"]+1==b["start"] for a,b in zip(out,out[1:])),"Overlap or gap")
    return out

def pack(units):
    """Sequential consolidation order; independent extraction may run in parallel.
    Stable 10–20k targets based on lexical density, bounded by source/book.
    Final remainder and prior reviewed prefix can be shorter.
    """
    macros=[]; group=[]; count=0
    def flush():
        nonlocal group,count
        if not group:return
        first,last=group[0],group[-1]
        mid=seal([first["source"],first["book_hint"],first["start"],last["end"],[u["id"] for u in group]])
        macros.append(dict(id=mid,source=first["source"],book_hint=first["book_hint"],
            status=first["status"],start=first["start"],end=last["end"],lines=count,
            units=len(group),unit_seal=seal(group),
            axes=sorted({i for u in group for i in u["axes"]}),
            previous_macro=macros[-1]["id"] if macros else None,
            order_scope="SOURCE_ORDER_NOT_EVENT_TIME"))
        group=[];count=0
    for u in units:
        n=u["end"]-u["start"]+1
        if group:
            g=group[0]
            density=sum(len(x["axes"]) for x in group)/len(group)
            target=10000 if density>=12 else 15000 if density>=6 else 19000
            if (u["source"],u["book_hint"],u["status"])!=(g["source"],g["book_hint"],g["status"]) or count+n>20000 or count>=target:
                flush()
        group.append(u);count+=n
    flush()
    require(sum(x["lines"] for x in macros)==sum(u["end"]-u["start"]+1 for u in units),"Macro coverage")
    require(len({m["id"] for m in macros})==len(macros),"Duplicate macro ID")
    return macros

def verify_reviewed(engine, cp, source_meta, body):
    """Existing lots are immutable. Check hashes, ranges, roles and prior anchors."""
    lines=body.split("\n")
    role_ranges={n:role for role,start,ls in sections(body) for n in range(start,start+len(ls)) if n<=cp["last_verified_line"]}
    seen=set();cursor=1;records=0;hit=0;axis_total=0;axis_found=0
    for entry in cp["lots"]:
        raw=(engine/entry["path"]).read_bytes()
        require(digest_bytes(raw)==entry["sha256_utf8"],"Prior lot hash mismatch")
        lot=json.loads(raw)
        require(lot["range"]==entry["range"] and entry["range"][0]==cursor,"Prior range gap")
        cursor=entry["range"][1]+1
        require(len(lot["records"])==entry["records"],"Prior record count")
        for rec in lot["records"]:
            e=rec["evidence"];lo,hi=e["line_start"],e["line_end"]
            require(rec["id"] not in seen and rec["promotion"] is False,"Prior ID or promotion")
            require(e["source"]==source_meta["source_name"] and e["source_sha256_manifest"]==source_meta["sha256"],"Prior source mismatch")
            require(entry["range"][0]<=lo<=hi<=entry["range"][1] and all(role_ranges.get(n)==e["role"] for n in range(lo,hi+1)),"Prior role or range")
            span="\n".join(lines[lo-1:hi])
            require(digest_text(span)==e["span_sha256_utf8"],"Prior anchor mismatch")
            hits=set(axis_hits(span));expected=set(rec["axes"])
            hit+=bool(hits&expected);axis_total+=len(expected);axis_found+=len(hits&expected)
            seen.add(rec["id"]);records+=1
    require(cursor==cp["last_verified_line"]+1==cp["next"]["start_line"],"Resume mismatch")
    require(records==cp["records_controller_reviewed"],"Checkpoint count mismatch")
    return dict(records_verified=records,records_with_matching_axis_hint=hit,axis_labels=axis_total,
                matching_axis_labels=axis_found,scope="DEVELOPMENT_HINT_OVERLAP_NOT_PRECISION_OR_INDEPENDENT_RECALL")
def run(archive,engine,output):
    t=time.perf_counter()
    archive=Path(archive).resolve();engine=Path(engine).resolve();output=Path(output).resolve()
    require(not output.is_relative_to(archive) and not output.is_relative_to(engine),"Output must be external disposable path")
    require(not output.exists(),"Use a fresh output")
    cp=load(engine/"docs/omega008-c-checkpoint.json")
    require(cp["project"]=="CRONICAS_DE_UM_NOVO_MUNDO" and cp["source_archive"]=="9dd632fb0bcd84dfce5b631013fdc67d7492ac5d","Wrong project or pin")
    head=load(archive/"canon/HEAD.json")
    require(head["day"]==579 and head["sequence"]==50,"Archive head changed")
    manifest,sources=read_verified_sources(archive)
    prior=verify_reviewed(engine,cp,*sources[0])
    reg=load_registry(archive)
    require(reg is not None,"Missing registry")
    idx=alias_index(reg[0]["records"],probes=())
    pattern=matcher(idx)
    units=[];source_counts=[]
    for index,(meta,body) in enumerate(sources,1):
        n=len(body.splitlines())
        require(n==cp["inventory"]["source_lines"][index-1],"Line convention mismatch")
        part=build_units(meta["source_name"],meta["sha256"],body,source_regions(index,n,cp["next"]["start_line"]),pattern,idx)
        units.extend(part);source_counts.append(dict(index=index,lines=n,units=len(part)))
    transcript_units=len(units);transcript_lines=sum(x["lines"] for x in source_counts)
    closures=sorted((load(p) for p in (archive/"canon/episodes").glob("*.json")),key=lambda x:x["sequence"])
    require([c["sequence"] for c in closures]==list(range(1,head["sequence"]+1)),"Closure sequence mismatch")
    closed_lines=0
    for c in closures:
        d,m=verify_episode(archive,c["episode_id"])
        require(m["original_readback_sha256"]==c["story_sha256"] and d.full_text.startswith(d.prose),"Closed prose mismatch")
        n=len(d.prose.splitlines());closed_lines+=n
        book="V" if c["sequence"]<=9 else "VI"
        units.extend(build_units(c["episode_id"],c["story_sha256"],d.prose,[(1,n,book,"PENDING_CLOSED_PROSE")],pattern,idx,closed=True))
    require(len({u["id"] for u in units})==len(units),"Duplicate coordinate ID")
    duplicates=Counter(u["anchor_sha256"] for u in units)
    # Identical bytes are a review hint, not permission to remove repeated events.
    macros=pack(units)
    pilot=next(m for m in macros if m["source"]==sources[0][0]["source_name"] and m["start"]==cp["next"]["start_line"])
    pilot_units=[u for u in units if u["source"]==pilot["source"] and pilot["start"]<=u["start"]<=pilot["end"]]
    require(seal(pilot_units)==pilot["unit_seal"],"Pilot seal mismatch")
    result=dict(schema=SCHEMA,scope="STRUCTURAL_AND_LEXICAL_ONLY",archive_pin=cp["source_archive"],
        transcript_lines=transcript_lines,transcript_units=transcript_units,closed_lines=closed_lines,closed_episodes=len(closures),
        total_units=len(units),macro_count=len(macros),source_counts=source_counts,registry_alias_keys=len(idx),
        exact_duplicate_anchor_groups=sum(v>1 for v in duplicates.values()),exact_duplicate_additional_units=sum(v-1 for v in duplicates.values() if v>1),
        axis_hints=sorted({n for u in units for n in u["axes"]}),prior=prior,pilot=pilot,
        pilot_tagged_units=sum(bool(u["axes"]) for u in pilot_units),pilot_ambiguous_units=sum(bool(u["ambiguous_alias_count"]) for u in pilot_units),
        queue_sha256=seal(units),macro_sha256=seal(macros),semantic_cursor=cp["next"]["start_line"],
        semantic_reviewed_new=0,semantic_certification=False,canon_changed=False,elapsed_seconds=round(time.perf_counter()-t,6))
    output.mkdir(parents=True)
    # Metadata only. No names, literal excerpts, prompt text, or held-out answers.
    for name,obj in (("summary.json",result),("macros.json",macros),("units.json",units),("pilot.json",pilot_units)):
        (output/name).write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    print("BULK_RESULT "+json.dumps(result,sort_keys=True),flush=True)
    for macro in macros:
        print("BULK_MACRO "+json.dumps(macro,sort_keys=True,separators=(",",":")),flush=True)
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive-root",required=True,type=Path)
    p.add_argument("--engine-root",default=Path("."),type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args();run(a.archive_root,a.engine_root,a.output)
if __name__=="__main__":main()
