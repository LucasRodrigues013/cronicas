"""Second R36 trial: fresh source-backed request and Codex before drafting.
No old request or preparation read; only frozen closed narrative and author choice.
All writes occur in disposable workspace. This is a development trial, not canon.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil, tempfile, time
from pathlib import Path
from worldroot.git_cycle import canonical, verify_episode
from worldroot.r33_runtime import author_context, prepare_from_request, digest
from worldroot.memory_continuity import DOMAINS, narrative_evidence, creation_packet
from worldroot.deep_recovery import build as build_index
from worldroot.live_codex import sync
from worldroot.editorial_guard import POLICY_PATH, load_policy
from worldroot.r34_experience import DIMENSIONS
from worldroot.r35_longform import FOCUS
from worldroot.turn_continuity import audit_turn_handoff

ID="LVI-C09-PII-D580-OMEGA-SECOND-TRIAL"
ARCHIVE_PIN="9dd632fb0bcd84dfce5b631013fdc67d7492ac5d"
A="LVI-C09-PI-D579-AUTHOR-SOURCE"
B="LVI-C08-PV-D578-AUTHOR-SOURCE"
C="LVI-C07-PII-D570-AUTHOR-SOURCE"
D="LVI-C04-PV-D558-AUTHOR-SOURCE"
E="LVI-C06-PV-D568-AUTHOR-SOURCE"
F="LVI-C07-PIII-D571-AUTHOR-SOURCE"
G="LVI-C08-PIII-D576-AUTHOR-SOURCE"
H="LVI-C08-PII-D575-AUTHOR-SOURCE"
# Independently selected, inspected source windows. Claim scope is deliberately narrow.
# Reuse the canonical source, never the first experiment or old request/plan.
FACTS=[
 ("opening","relationship","bilhete Miren Lucas passeio trem",A,32,94,"Miren guardou o bilhete de passeio dado pelo marido; humor e afeto recíprocos.",True),
 ("shelf","inventory","pássaro maquete ARGOS gravetos",A,2261,2319,"O brinquedo do ARGOS está na prateleira perto da maquete e do pássaro; NÓX regula iluminação.",True),
 ("miren-identity","identity","Miren cabelos escuros travesseiro",B,31,65,"Cabelos escuros narrados; Miren conduz brincadeira conjugal com iniciativa.",True),
 ("couple-style","identity","Miren Lucas bandeja café cheiro",E,44,100,"Lucas expressivo e brincalhão; Miren escolheu o café e conduz o diálogo.",False),
 ("genese-proof","power","GÊNESE ponte quilômetros energia",B,201,249,"GÊNESE criou ponte e infraestrutura de 31,6 km; energia não depende do corpo de Lucas.",True),
 ("forja-voices","identity","Dorek repetibilidade Brannik cadência",C,872,920,"Dorek exige repetibilidade e proteção; Brannik celebra e cria nomes.",True),
 ("network-boundary","world","Rumo NÓX sistemas não conscientes comunicação",C,1948,1974,"Rumo e NÓX participam voluntariamente; controle local e enlaces verificáveis, sem alcance remoto presumido.",True),
 ("conference","event","Thalor confirmação plenária Kael Miren",B,105,135,"Confirmação por carta, não presença; plenária D585 condicionada; Miren propõe início sem esperar todos.",True),
 ("mandate","promise","Edrik Kael acordo cooperação civil",B,459,503,"Acordo dos postos de Halvern em vigor; autonomia, dados de pacientes protegidos e Campo Aurora autorizado.",True),
 ("lysa-proof","identity","Lysa recibo confirmação carta Ordan",A,1230,1271,"Lysa confere recibo e separa confirmação intermediária de entrega final.",True),
 ("astra-voice","identity","Astra trabalho descoberta comissão",B,343,385,"Astra quer autonomia e diálogo, não possui pretendente específico apresentado.",True),
 ("kael-voice","identity","Kael Lucas mercado pergunta árvores",F,215,277,"Kael escuta moradores e corrige Lucas com humor; estradas dependem da conversa local.",False),
 ("naira","identity","Naira Edris autorização pouso Thalor",D,596,648,"Naira é piloto e pede autorização local; Edris concedeu pouso de visita D558, não autorização permanente.",True),
 ("varo-role","identity","Varo levar auxílio nenhum fica",H,104,114,"Varo orienta legionários a levar auxílio, proteger receptores e equipe; lema da Legião.",True),
 ("varo-location","location","Varo Campo Aurora assistiu saída",G,130,142,"Varo foi visto no Campo Aurora D576; D580 localização exige confirmação, não teleporte.",True),
 ("halvern","location","Ivena Edrik permanecer Halvern Sella",A,1839,1875,"Ivena e Edrik ficaram em Halvern; Sella retornaria no ARGOS.",True),
 ("letter","knowledge","carta original permanece Pedras Claras",A,1243,1271,"Carta de Ordan está nas Pedras Claras, irmã não localizada, nenhuma entrega final.",True),
 ("ren-shar","event","Velkar Avelna comunidade acesso comercial",A,1532,1605,"Segunda comunidade recebe acesso comercial limitado, não incorporação; discordância política permanece.",True),
 ("foundry","knowledge","Bressa Tharvek parede planta seis marcas",A,1647,1695,"Bressa e Tharvek localizaram setor com associação documental; não viram seis marcas; cópia depende de autorização.",True),
 ("sea","knowledge","Varkhess Serina correspondência possível Serevan",A,1741,1775,"Região candidata, nenhum desaparecido encontrado; navio retorna a Serevan.",True),
 ("friends","relationship","Ordan Brannik Dorek brinquedo jardim",A,2095,2130,"Amigos encontram-se no Jardim Branco; brincadeira sobre brinquedo e suas modificações.",False),
]
# A new eight-scene composition, not a copied old R35 plan.
SCENES=[
 ("Torre do Criador: Lucas e Miren descobrem a diferença entre perceber e compreender; NÓX escolhe participar. O bilhete e a prateleira entram na cena como vida vivida.",
  ["opening","shelf","miren-identity","couple-style","friends"],1250,
  "Um problema pequeno é visto por duas pessoas de maneira distinta.","Miren investiga e Lucas formula a ideia em vez de recapitular.","A primeira pergunta dos Olhos surge de um acontecimento real."),
 ("Forja: Lucas, Astra, Dorek e Brannik criam seis pares idênticos e instrumentos especializados. GÊNESE manifesta; comparar medida física, dado local e hipótese.",
  ["genese-proof","forja-voices","network-boundary","astra-voice"],1650,
  "Uma peça e um ambiente mostram o que os sentidos não percebem.","Os mestres experimentam, erram, discutem e escolhem uma aplicação.","Seis pares e coleção funcional, com resultado observável na oficina."),
 ("Campo Aurora: Naira e Varo são localizados por confirmação de mensagem; demonstração de olhos e computadores para logística, Sombras e serviços em setores próprios.",
  ["varo-role","varo-location","naira","halvern","network-boundary"],1350,
  "Uma entrega em andamento oferece um caso humano e operacional.","Varo e Naira impõem suas próprias condições de utilização.","Equipamentos chegam a usuários reais sem exigir presença presumida."),
 ("Gabinete da Cidade Livre: Lysa e Kael experimentam computador arcano com registros reais; um desacordo de dados é resolvido pelos responsáveis.",
  ["lysa-proof","kael-voice","mandate","letter"],1300,
  "Dois documentos aparentemente iguais produzem leituras distintas.","Lysa verifica origem, Kael ouve as pessoas afetadas.","A decisão orçamentária ou logística é executada, não apenas prometida."),
 ("AERÚN: Miren, Astra, Kael e Lysa conduzem a sessão. A Mesa dos Horizontes nasce de uma necessidade das representações; Thalor só comparece após transporte ou confirmação narrada.",
  ["conference","mandate","naira","genese-proof","kael-voice"],1650,
  "Uma dificuldade de comunicação ganha forma sensorial na Mesa.","Representantes fazem perguntas e defendem limites de seus mandatos.","Uma cooperação concretamente autorizada ou um documento encaminhado."),
 ("Frentes autônomas: carta de Ordan em Pedras Claras, Bressa e Tharvek no Vale, Velkar e Avelna em Renshar, retorno de Varkhess e Serina a Serevan.",
  ["letter","foundry","ren-shar","sea","halvern"],1100,
  "Pessoas distantes tomam decisões por evidências próprias.","Cada reação preserva ignorância dos fatos ainda não recebidos.","Progresso independente e mistérios abertos, sem informação instantânea."),
 ("AERÚN e Forja: Astra, Rumo, Lucas e operadores executam um primeiro enlace local; projetos de expansão surgem de experiências e não de discursos.",
  ["network-boundary","forja-voices","genese-proof","friends"],1200,
  "Um resultado que aparece longe do terminal original surpreende os participantes.","A equipe testa limites e demonstra controle local voluntário.","Primeiro enlace material, alcance limitado e futuro realmente visível."),
 ("Torre: Lucas e Miren reencontram-se após atividades próprias, lembram o passeio e contemplam as consequências do dia; cinco escolhas distintas.",
  ["opening","shelf","couple-style","miren-identity","friends"],1050,
  "Uma pausa íntima e bem-humorada devolve escala humana ao dia.","Miren e Lucas compartilham o que realmente viveram.","Fecho emocional e caminhos futuros sem escolher pelo autor.")
]
DIM_SCENES={"daily_life":[1,8],"appearance":[1],"relationships":[1,8],"cast":[2,3,5],
            "wonder":[2,5,7],"rhythm":[4,5,8],"design":[8]}
CHARACTERS=[
 ("Lucas",[1,2,3,5,7,8],"couple-style","opening"),
 ("Miren",[1,5,8],"miren-identity","opening"),
 ("Astra",[2,5,7],"astra-voice",None),
 ("Dorek",[2,7],"forja-voices",None),
 ("Brannik",[2,7],"forja-voices",None),
 ("Varo",[3],"varo-role",None),
 ("Naira",[3,5],"naira",None),
 ("Lysa",[4,5],"lysa-proof",None),
 ("Kael",[4,5],"kael-voice",None),
]
def stamp(stage,start,**x):
    print(json.dumps(dict(stage=stage,elapsed_seconds=round(time.perf_counter()-start,6),**x),ensure_ascii=False,sort_keys=True),flush=True)
def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))
def hash_text(t):
    return hashlib.sha256(t.encode("utf-8")).hexdigest()
def make_request(root):
    head=load(root/"canon/HEAD.json")
    assert head["episode_id"]==A
    auth=author_context(root,head)
    assert auth["choice"]["option"]==1
    supplement=load(root/"planning/book-vi/D580-REVOLUCAO-TECNOLOGICA-AUTHOR-DIRECTION.json")
    assert supplement["author_source"]=="USER_MESSAGE" and len(supplement["requirements"])==5
    requirements=[]; reviewed={}; bodies={}
    for rid,domain,query,source,lo,hi,claim,critical in FACTS:
        if source not in bodies:
            draft,_=verify_episode(root,source)
            bodies[source]=narrative_evidence(draft.full_text).splitlines(keepends=True)
        anchor="".join(bodies[source][lo-1:hi]);assert anchor.strip()
        requirements.append(dict(id=rid,domain=domain,query=query,role="Response",critical=critical))
        reviewed[rid]=dict(source=source,line_start=lo,line_end=hi,anchor_sha=hash_text(anchor),claim=claim,status="REVIEWED_SUPPORTED")
    policy_text=POLICY_PATH.read_text(encoding="utf-8")
    policy=load_policy()
    rules={r["id"]:r for r in policy["rules"] if r["active"]}
    assert len(rules)==130
    plines=policy_text.splitlines(keepends=True)
    dims={}
    for name,rule in DIMENSIONS.items():
        start=next(i for i,l in enumerate(plines) if '"id": "'+rule+'"' in l)
        end=next(i for i in range(start,len(plines)) if '"directive"' in plines[i])
        rid="policy-"+rule
        requirements.append(dict(id=rid,domain="author_rule",query=rule+" "+rules[rule]["title"],role="AuthorPolicy",critical=True))
        reviewed[rid]=dict(source="AUTHOR_POLICY",line_start=start+1,line_end=end+1,anchor_sha=hash_text("".join(plines[start:end+1])),claim=rules[rule]["directive"],status="REVIEWED_SUPPORTED")
        dims[name]=dict(rule=rule,requirement_id=rid,status="planned",reason="Aplicar de forma contextual na cena prevista, sem forçar acontecimentos.",scenes=DIM_SCENES[name])
    scene_plan=[];cards=[]
    for n,(purpose,ids,budget,experience,reaction,payoff) in enumerate(SCENES,1):
        ids=ids+[dims[k]["requirement_id"] for k in dims if n in DIM_SCENES[k]]
        scene_plan.append(dict(scene=n,purpose=purpose,ids=list(dict.fromkeys(ids))))
        cards.append(dict(scene=n,word_budget=budget,experience=experience,reaction=reaction,payoff=payoff,focus=[k for k in FOCUS if n in DIM_SCENES[k]]))
    people=[]
    def sourced(rid,reason):
        return dict(status="sourced",requirement_ids=[rid],reason=reason)
    def unknown(reason):
        return dict(status="unknown",reason=reason)
    for name,sc,voice,relation in CHARACTERS:
        # Voice/relation evidence must enter each person's actual scene context.
        for rid in [voice,relation]:
            if rid and not any(rid in scene_plan[n-1]["ids"] for n in sc):
                scene_plan[sc[0]-1]["ids"].append(rid)
        fields={"voice":sourced(voice,"Voz e iniciativa recuperadas de um momento narrado."),
                "appearance":sourced("miren-identity","Traço físico histórico explicitamente narrado em D578.") if name=="Miren" else unknown("Não preencher aparência histórica que não foi confirmada neste recorte."),
                "relationship":sourced(relation,"Vínculo e iniciativa recíproca demonstrados na fonte.") if relation else unknown("Não inferir relações íntimas a partir de menções ou proximidade."),
                "age":unknown("Não inferir idade explícita por papel social; consultar design aprovado separadamente.")}
        people.append(dict(name=name,scenes=sc,fields=fields))
    intent=dict(schema="worldroot-r34-intent-v1",dimensions=dims,characters=people,
                comparison=dict(requirement_id="couple-style",reason="Comparar respiração e humor com D568, além da experiência pública D571."))
    refs=["couple-style","kael-voice","forja-voices","genese-proof"]
    axes={
      "cadence":dict(aim="Recuperar pausas e reações antes de cada avanço técnico.",reference_id="couple-style",scenes=[1,2,8]),
      "voice_identity":dict(aim="Distinguir precisão de Dorek, entusiasmo de Brannik, autonomia de Varo e Lysa.",reference_id="forja-voices",scenes=[2,3,4]),
      "emotion_adult":dict(aim="Dar espaço a afeto recíproco e vida própria, sem inventar dados íntimos.",reference_id="couple-style",scenes=[1,8]),
      "wonder_payoff":dict(aim="Fazer a criação tocar sentidos e resultar em transformação humana.",reference_id="genese-proof",scenes=[2,5,7]),
      "exposition":dict(aim="Trocar explicações duplicadas por experiências, escolhas e consequências.",reference_id="kael-voice",scenes=[3,4,5,7])
    }
    plan=dict(schema="worldroot-r35-plan-v1",part="II",profile="regular",scene_cards=cards,references=refs,
              cadence_intent="Alternar falas, silêncio, movimento e imagens sensoriais, sem quota de parágrafos.",
              adult_opportunity="Preservar afeto não gráfico e autonomia, sem obrigar intimidade não fundamentada.",
              epic_payoff="Criações manifestadas e utilizadas; implantação, cooperação e enlace concreto.",
              adult_focus={k:dict(status="held",reason="Não há idade narrativa explicitamente recuperada neste recorte; afeto cotidiano preservado.",characters=[],scenes=[]) for k in ("body_identity","adult_conversation","reciprocal_attraction")},
              refinement=dict(schema="worldroot-r35-refinement-v1",axes=axes,identity_recovery=[dict(character=x["name"],source_review="Fonte literal revisada; consultar ficha vinculada e conflitos.",voice_direction=x["fields"]["voice"]["reason"],trait_gaps="Traços não confirmados continuam indeterminados; não presumir presença.") for x in people]))
    domains={d:dict(applicable=any(r["domain"]==d for r in requirements),reason="Revisão de relevância para esta composição de teste, com fontes vinculadas quando aplicável.") for d in DOMAINS}
    return dict(schema="worldroot-r33-request-v1",project="CRONICAS_DE_UM_NOVO_MUNDO",delivery_id=ID,head=head,choice_sha256=auth["choice_sha256"],requirements=requirements,reviewed=reviewed,domain_review=domains,scene_plan=scene_plan,r34_intent=intent,r35_plan=plan)
def main(root,out):
    started=time.perf_counter();root=root.resolve()
    out.mkdir(parents=True,exist_ok=True)
    old={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/"canon/HEAD.json",root/"ops/RESUME.json")}
    with tempfile.TemporaryDirectory() as t:
        w=Path(t)/"archive";now=time.perf_counter()
        shutil.copytree(root,w,ignore=shutil.ignore_patterns(".git"))
        head=load(w/"canon/HEAD.json");resume=load(w/"ops/RESUME.json")
        handoff=audit_turn_handoff(w,resume["latest_unclosed_draft"]["episode_id"],expected_head_id=head["episode_id"])
        stamp("source_handoff",now,checks=handoff.get("checks",{}),head=head["day"],pending=resume["latest_unclosed_draft"]["episode_id"])
        # Existing D580 remains the pending official draft; this separate ID is a trial only.
        now=time.perf_counter();g=sync(w)
        stamp("r36_graph_rebuild",now,records=g["records"],events=g["events"],temporal=g["temporal"],registry_sha=g["registry_sha"])
        now=time.perf_counter();req=make_request(w)
        stamp("fresh_request_authored",now,requirements=len(req["requirements"]),scenes=len(req["scene_plan"]),focal=len(req["r34_intent"]["characters"]),planned_words=sum(c["word_budget"] for c in req["r35_plan"]["scene_cards"]),request_sha256=digest(req),reused_previous_request=False)
        now=time.perf_counter();db=Path(t)/"historical.sqlite";index=build_index(w,db)
        stamp("fresh_historical_projection",now,windows=sum(r["windows"] for r in index["coverage"]),sources=len(index["coverage"]))
        now=time.perf_counter()
        result=creation_packet(w,db,req["requirements"],head=head,candidate_limit=20,graph_db=None,deep=False)
        # Report actual retrieval separately from pre-inspected source anchors.
        count=recent_hit=graph_hit=0; misses=[]
        for x in result["items"]:
            rid=x["requirement"]["id"]
            if x["requirement"]["role"]!="Response":continue
            count+=1;v=req["reviewed"][rid]
            rr=x.get("recent_canon_candidates",[])
            hit=any(h.get("source")==v["source"] and min(h.get("line_end",0),v["line_end"])-max(h.get("line_start",0),v["line_start"])+1>=3 for h in rr)
            recent_hit+=hit;graph_hit+=bool(x.get("graph_candidates"))
            if not hit:misses.append(rid)
        stamp("fresh_context_retrieval",now,probes=count,reviewed_window_in_recent_candidates=recent_hit,graph_candidate_requirements=graph_hit,misses=misses,semantic_certification=False)
        now=time.perf_counter()
        (w/"requests").mkdir(exist_ok=True);(w/"requests"/(ID+".json")).write_bytes(canonical(req))
        p=prepare_from_request(w,req);packet=load(w/"preparations"/(ID+".json"))
        assert p["preparation_sha256"]==packet["preparation_sha256"]
        assert p["result"]=="CREATED" and prepare_from_request(w,req)["result"]=="IDEMPOTENT"
        c=packet["universal_codex"];stream=c.get("scene_context",{}).get("scenes",[])
        stamp("fresh_preparation_readback",now,preparation_sha256=p["preparation_sha256"],editorial_receipt_sha256=p["editorial_receipt_sha256"],required=packet["memory"]["required"],verified=packet["memory"]["verified"],critical_missing=packet["memory"]["critical_missing"],represented=len(packet["editorial_receipt"]["coverage"]["represented_rule_ids"]),focal=c["focal"],coherence_required=c["coherence_required"],scene_context=[dict(scene=s["scene"],direct_ids=s["direct_ids"],records=len(s["records"]),ambiguities=s["ambiguities"],status=s["source_status"]) for s in stream],world_fronts_status=c.get("world_fronts",{}).get("status"),semantic_certification=False)
        # Exact preparation is made available for the controller; do not publish withheld benchmark answers.
        (out/"request.json").write_bytes(canonical(req))
        (out/"preparation.json").write_bytes(canonical(packet))
        (out/"summary.json").write_text(json.dumps({"stage":"READY_FOR_CONTROLLER_DRAFT","preparation_sha256":p["preparation_sha256"],"request_sha256":digest(req),"generation_executed":False,"canon_changed":False,"semantic_certification":False},indent=2),encoding="utf-8")
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==h for p,h in old.items())
    stamp("second_trial_preparation_total",started,status="READY_FOR_CONTROLLER_DRAFT",generation_executed=False,canon_changed=False)
if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--archive-root",type=Path,required=True);a.add_argument("--output",type=Path,required=True);n=a.parse_args();main(n.archive_root,n.output)
