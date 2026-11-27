"""Native validators on a genuinely generated, non-canonical development draft.
The literal text was drafted in one controller turn; no model calls here.
The review is self-authored, not independent; incomplete Codex is NOT fabricated.
"""
import argparse
import copy
import hashlib
import json
import shutil
import tempfile
import time
from pathlib import Path

from worldroot.git_cycle import canonical
from worldroot.editorial_guard import quick_preflight
from worldroot.experience_quality import render_choices
from worldroot.presentation_guard import presentation_preflight
from worldroot.r34_experience import render_opening, validate_delivery as r34
from worldroot.r35_longform import validate_delivery as r35, volume_check
from worldroot.r33_runtime import prepare_from_request, verify_submission
from worldroot.r32_release import release_review
from worldroot.reader_experience import preview_reader_review
from worldroot.r35_refinement import rhythm_signals

FIXTURE=Path(__file__).resolve().parent/"omega-generation-trial"
def load(path):
    return json.loads(path.read_text(encoding="utf-8"))
def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()
def output(stage, started, **values):
    print(json.dumps({"trial_stage":stage,"seconds":round(time.perf_counter()-started,6),**values},ensure_ascii=False),flush=True)
def stage(name, fn):
    t=time.perf_counter()
    try:
        v=fn()
        output(name,t,status="PASS",**v)
        return True
    except Exception as e:
        # Fixed, non-sensitive classifications only.
        message=str(e)
        known=("Missing Codex delta","Missing coherence review","Scene Codex Sync required",
               "R35_DEPTH","R35 refinement","R35 opportunity","R34 evidence","R34/R35 design",
               "R34 physical","R33","R32","Editorial preparation receipt")
        output(name,t,status="BLOCKED",error_type=type(e).__name__,
               reason_code=next((x for x in known if x in message),"UNCLASSIFIED_VALIDATION_ERROR"))
        return False

def option(n,track,arc,title,promise,reward,risk,next_link,unselected):
    return dict(number=n,track=track,arc_id=arc,title=title,promise=promise,reward=reward,risk=risk,
                next_link=next_link,unselected_progress=unselected,guaranteed_success=False,combines_all=False)

ARC={"options":[
    option(1,"main","continental-reception","A carta que abre uma estrada",
      "Miren, Astra, Kael e Lysa encaminham o termo da recepção a Thalor e avançam a preparação da plenária, conforme as respostas reais.",
      "Uma etapa de cooperação civil executável e novos contatos.", "Autorizações e interesses podem divergir.",
      "Plenária D585 e recepção autorizada.", "Os terminais locais seguem em uso."),
    option(2,"secondary","local-network","A cidade que conversa consigo mesma",
      "Lucas, a Forja e os operadores desenvolvem a primeira malha física de dados, começando pelas ligações entre setores de Três Arcos.",
      "Serviços conectados e novas possibilidades para os moradores.", "Integração exige medições e respeito aos dados de origem.",
      "Expansão da rede e Eixo Aurora.", "Os representantes continuam seus encaminhamentos."),
    option(3,"secondary","old-foundries","O segredo das paredes",
      "Bressa e Tharvek procuram os registros de ocupação do setor e comparam as alterações do edifício com as evidências disponíveis.",
      "Uma pista material ou documental sobre os antigos ofícios.", "A origem das seis marcas pode permanecer desconhecida.",
      "Terceiro Fole e trajetória dos artefatos.", "As demais equipes trabalham em seus próprios prazos."),
    option(4,"secondary","horizon-experience","ESPECIAL — O bilhete encontra um caminho",
      "Lucas e Miren procuram uma oportunidade de conhecer o corredor do Horizonte como viajantes, acompanhados de quem desejar participar, sem abandonar a conferência.",
      "Uma experiência de descoberta, amizade e tempo compartilhado.", "A viagem precisa caber na disponibilidade do casal e na operação da ferrovia.",
      "Vínculo do casal, vida civil e exploração.", "A Forja continua os ensaios sob suas próprias decisões.")
    ],"free_action":True,"author_choice_recorded":False}

OPENING={"book_title":"LIVRO VI — AS COROAS PARTIDAS","chapter_title":"O QUE OS CAMINHOS CARREGAM",
         "episode_title":"A LUZ QUE PASSAVA DE MÃO EM MÃO",
         "epigraph":"O futuro começa quando uma descoberta encontra alguém capaz de fazer algo novo com ela.",
         "calendar":"Dia 580 · Ano II · M08 · D05","location":"Torre do Criador",
         "fronts":"Três Arcos · Forja · Campo Aurora · AERÚN · Thalor · Halvern · Renshar · Vale · Serevan"}
# Exact literal spans, not generic generated placeholders.
BEATS={
1:("O pequeno ARGOS de gravetos havia perdido uma hélice.","Miren riu de um jeito tão inesperado que precisou afastar o livro da xícara.","Eu quero experimentar isso."),
2:("Lucas pegou um pedaço de madeira encontrado junto às sobras de uma bancada","Quando a claridade se dissipou, seis armações perfeitamente iguais repousavam em seis estojos abertos.","Isto vai mudar o modo como examino algumas peças."),
3:("O problema não havia surgido numa máquina em circulação.","Dorek conferiu as medidas, pediu outra repetição","A fixação estava contribuindo para a deformação."),
4:("Lysa escolheu um pequeno conjunto de documentos da próxima remessa civil.","Ela pegou a caneta, conferiu parte das parcelas no papel","O valor reservado permanece este."),
5:("A primeira estação foi instalada no lugar indicado pela equipe.","O homem escolheu o estado correspondente e chamou uma colega","Uma pequena parte das informações da jornada já havia sido transferida"),
6:("Miren havia conseguido uma coisa importante","O primeiro visitante se levantou devagar.","Quando os participantes terminaram de examinar as condições, havia um texto concreto sobre a mesa."),
7:("Osvan pediu que ele desenhasse o trecho.","O menino começou a fazer perguntas sobre os desenhos.","A nova observação poderia ser acrescentada sem apagar a posição"),
8:("Astra solicitou a abertura a partir da segunda estação.","Lucas fez uma pequena dança de vitória tão despropositada que a artesã começou a rir.","A passagem de trem continuava dentro do livro.")
}
# Some shorter phrases are expanded to exact sentences where needed.
OPPORTUNITIES={
 "daily_life":[(1,"O pequeno ARGOS de gravetos havia perdido uma hélice.","O presente e o reparo dão peso afetivo a uma ação pequena."),(8,"Rumo havia terminado a experiência com as folhas aromáticas","O companheiro mantém uma curiosidade e atividade próprias.")],
 "appearance":[(1,"com os cabelos escuros ainda soltos e uma das pernas dobrada sobre o assento","A apresentação se ancora no cabelo escuro e numa postura circunstancial."),(5,"Miren ajeitou os cabelos que haviam escapado de sua presilha","O vento afeta a aparência durante a chegada da aeronave.")],
 "relationships":[(8,"Miren apoiou a mão em seu braço e inclinou-se, beijando-lhe a face.","O agradecimento e o gesto partem da personagem."),(1,"Ela voltou com a colher, inclinou-se sobre ele e beijou-lhe a boca.","A proximidade do casal surge naturalmente durante o café.")],
 "cast":[(3,"Dorek conferiu as medidas, pediu outra repetição","O mestre atua segundo o próprio padrão de precisão."),(4,"Sentou-se, abriu uma nova relação e chamou outra pessoa da equipe.","Lysa transforma a novidade em ação por iniciativa própria.")],
 "wonder":[(2,"Quando a claridade se dissipou, seis armações perfeitamente iguais repousavam em seis estojos abertos.","A criação manifesta os objetos e a igualdade dos exemplares."),(6,"As montanhas se ergueram sobre a superfície.","A cartografia ganha presença visual diante dos visitantes.")],
 "rhythm":[(6,"O primeiro visitante se levantou devagar.","A pausa deixa espaço para o impacto da manifestação."),(8,"Lucas fez uma pequena dança de vitória tão despropositada que a artesã começou a rir.","A reação distende a sequência de experimentos.")]
}
ASSESS={
 "daily_life":"O reparo e a infusão preservam cotidiano e curiosidade sem obrigatoriedade de crise.",
 "appearance":"A identidade recuperada de Miren aparece com cabelo, roupa e gesto, sem inventar anatomia histórica.",
 "relationships":"O casal demonstra atração afetiva recíproca e interesse no trabalho individual.",
 "cast":"Dorek, Astra, Lysa e os operadores decidem como aplicar as criações.",
 "wonder":"A manifestação e a surpresa diante de mapas e sensores têm efeitos observáveis.",
 "rhythm":"A reação dos visitantes e o humor dão pausa entre decisões da sessão."
}
REFINEMENT={
 "cadence":("cadence",[(1,"Miren riu de um jeito tão inesperado que precisou afastar o livro da xícara.","O humor doméstico tem reação física e pausa."),(8,"Dessa vez, deixou-a como estava.","A volta ao brinquedo muda o gesto do início.")],
  "O episódio alterna manifestação, diálogo, interlúdios e repouso doméstico.",
  "A referência de D568 tem contexto cotidiano diferente; este capítulo concentra uma descoberta tecnológica."),
 "voice_identity":("forjaprecision",[(3,"A fixação estava contribuindo para a deformação.","Dorek limita a conclusão ao caso observado."),(4,"Quero experimentar com os documentos que chegaram esta manhã.","Lysa demonstra entusiasmo mediante trabalho autônomo.")],
  "As vozes contrastam precisão técnica, entusiasmo expansivo e prática financeira.",
  "O ensaio anterior da Forja oferece comparação de precisão, não obriga as mesmas falas."),
 "emotion_adult":("cadence",[(1,"Ela voltou com a colher, inclinou-se sobre ele e beijou-lhe a boca.","Miren inicia um gesto afetivo no café."),(8,"Miren apoiou a mão em seu braço e inclinou-se, beijando-lhe a face.","O agradecimento retorna depois do trabalho independente.")],
  "A intimidade permanece afetuosa e recíproca, sem inventar idade ou traços físicos.",
  "O contexto do casal permanece distinto de uma avaliação de oportunidade adulta específica."),
 "wonder_payoff":("friend",[(2,"Quando a claridade se dissipou, seis armações perfeitamente iguais repousavam em seis estojos abertos.","A escala da criação é pequena, mas visualmente extraordinária."),(6,"As montanhas se ergueram sobre a superfície.","O mapa dá forma visível a uma negociação e à curiosidade.")],
  "Criações apresentam forma material e efeitos para outras pessoas, além do anúncio do Criador.",
  "A referência de colaboração anterior oferece uma dinâmica humana diferente dos instrumentos."),
 "exposition":("citizen",[(4,"O total anterior estava incluindo a previsão e a confirmação como se fossem duas despesas.","A aplicação do computador revela uma consequência financeira específica."),(6,"Kael assinou pela Cidade Livre o que estava autorizado a assumir","A discussão resulta num compromisso concreto dentro dos mandatos.")],
  "A exposição tecnológica é dramatizada por descobertas e decisões, embora alguns trechos permaneçam técnicos.",
  "O diálogo com moradores de D571 oferece experiência civil distinta do gabinete e da conferência.")
}
def moments(rows):
    return [{"scene":n,"evidence":a,"effect":effect} for n,a,effect in rows]
def run(root):
    start=time.perf_counter()
    m=load(FIXTURE/"manifest.json"); ident=m["case_id"]
    chunks=[(FIXTURE/f"{i:02d}.md").read_text(encoding="utf-8") for i in range(1,5)]
    assert [sha(s) for s in chunks]==m["segment_sha256"]
    assert sha("".join(chunks))==m["pure_prose_sha256"]
    meta=dict(book="Livro VI",chapter=9,part="II",day=580,hour="22h31",
              location="Torre do Criador e frentes regionais",canon_status="RASCUNHO",worldroot_revision=35)
    choice_render=render_choices(ARC,ident,revision=35)
    opening=render_opening(meta,OPENING)
    chunks[0]=choice_render["body_declaration"]+"\n"+opening+"\n\n---\n\n"+chunks[0]
    prose="".join(chunks)
    checkpoint=('<box border radius="lg" padding={3} gap={2}>\n'
                '  <caption>WORLDROOT · CHECKPOINT NARRATIVO — ENSAIO NÃO CANÔNICO</caption>\n'
                '  <grid columns={2} gap={2}>\n'
                '    <grid-item><caption>Criações</caption>**Seis pares pessoais; Forja, computadores e Mesa dos Horizontes.**</grid-item>\n'
                '    <grid-item><caption>Frentes</caption>**A carta continua em Pedras Claras; investigação e cooperação seguem.**</grid-item>\n'
                '  </grid>\n</box>')
    full=prose+"\n\n---\n\n"+checkpoint+"\n\n"+choice_render["markup"]
    choices=[{"number":o["number"],"title":o["title"],"description":o["promise"],
              "is_special":o["number"]==4,"is_free":False} for o in ARC["options"]]
    choices.append({"number":5,"title":"AÇÃO LIVRE","description":"Ação experimental, sem escolha canônica.","is_special":False,"is_free":True})
    output("literal_generation_readback",start,status="PASS",words=volume_check(prose,"II",1)["words"],
           scenes=volume_check(prose,"II",1)["scenes"],segments=len(chunks),
           pure_prose_sha256=m["pure_prose_sha256"],duplicate_word_share=volume_check(prose,"II",1)["duplicate_word_share"],
           draft_elapsed_seconds=m["generation"]["draft_elapsed_seconds"],semantic_certification=False)
    def structural():
        a=presentation_preflight(full)
        b=quick_preflight(prose,head=load(root/"canon/HEAD.json"))
        assert not a["errors"] and not b["errors"]
        return {"presentation_checks":a["checks"],"policy_evaluated":b["evaluated_rule_ids"],
                "cadence":rhythm_signals(prose),"reader_advisory":preview_reader_review(prose),
                "screen_rendered":False,"semantic_certification":False}
    structure=stage("native_presentation_and_editorial",structural)
    with tempfile.TemporaryDirectory() as d:
        work=Path(d)/"archive";shutil.copytree(root,work,ignore=shutil.ignore_patterns(".git"))
        req=load(work/"requests"/(m["source_request"]+".json"))
        req["delivery_id"]=ident
        (work/"requests"/(ident+".json")).write_bytes(canonical(req))
        def prep():
            r=prepare_from_request(work,req)
            return {"created":r["result"],"literal_requirements":len(req["requirements"]),"semantic_certification":False}
        if not stage("native_generation_preparation",prep):
            return 1
        packet=load(work/"preparations"/(ident+".json"))
        segs=[]
        for i,s in enumerate(chunks,1):
            path=f"production/{ident}/segments/{i:02d}.md"
            p=work/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(s.encode())
            segs.append(dict(part=i,path=path,sha256=sha(s)))
        dims={}
        for k,rows in OPPORTUNITIES.items():
            n,a,effect=rows[0]
            dims[k]=dict(status="applied",reason=ASSESS[k],scene=n,evidence=a)
        dims["appearance"].update(character="Miren",concrete_detail="cabelos escuros")
        dims["design"]={"status":"applied","reason":"A abertura e as cinco rotas preservam a hierarquia visual aprovada.","evidence":"CRÔNICAS DE UM NOVO MUNDO · WORLDROOT R35"}
        r34_review={"schema":"worldroot-r34-review-v1","opening":OPENING,"dimensions":dims,
                    "comparison_result":"A manifestação, o cotidiano e as decisões apresentam efeitos concretos em contexto diferente do original.",
                    "no_forced_scenes":True,"no_unsupported_traits":True}
        r35_review={"schema":"worldroot-r35-review-v1",
                    "scenes":[dict(scene=n,planned_scene=n,beats=dict(zip(("experience","reaction","payoff"),anchors)),
                                   assessment="A cena desenvolve uma experiência própria e uma consequência observável.") for n,anchors in BEATS.items()],
                    "opportunities":{k:{"status":"applied","assessment":ASSESS[k],"moments":moments(rows)} for k,rows in OPPORTUNITIES.items()},
                    "comparison":{k:{"reference_id":v,"assessment":a,"result":"contextual_difference"} for k,v,a in [
                        ("cadence","cadence","Comparação contextual de diálogo, pausas e extensão de parágrafos."),
                        ("emotion","cadence","A relação é cotidiana, com retorno ao gesto inicial."),
                        ("adventure","friend","Descoberta tecnológica substitui combate neste comando específico."),
                        ("character","forjaprecision","As pessoas preservam iniciativa, humor e interesses distintos."),
                        ("design","citizen","O cabeçalho e os controles foram renderizados pelo contrato vigente.")]},
                    "no_padding":True,"no_condensed_key_events":True,
                    "adult_focus":{k:{"status":"held","assessment":"O ensaio mantém afeto cotidiano e não inventa anatomia ou idade.","context":"A preparação histórica marcou idade explícita como desconhecida."} for k in req["r35_plan"]["adult_focus"]},
                    "refinement":{"schema":"worldroot-r35-refinement-review-v1",
                                  "axes":{k:{"reference_id":ref,"result":"contextual_difference","assessment":a,"contrast":c,
                                             "moments":moments(rows),"density_response":"A cena técnica utiliza parágrafos mais densos; o autor ainda deve comparar a respiração."}
                                          for k,(ref,rows,a,c) in REFINEMENT.items()},
                                  "no_artificial_fragmentation":True,"no_administrative_padding":True,"no_forced_conflict_or_romance":True}}
        # Explicit self-review, not a claim of complete semantic or Codex coverage.
        reviews={
          "continuity":("A passagem de trem continuava dentro do livro.","Recupera o objeto apresentado na parte anterior."),
          "causality":("A fixação estava contribuindo para a deformação.","A repetição do ensaio antecede a conclusão técnica."),
          "identity_voice":("Quero experimentar com os documentos que chegaram esta manhã.","Lysa transforma o interesse em trabalho próprio."),
          "relationships":("Miren apoiou a mão em seu braço e inclinou-se, beijando-lhe a face.","O vínculo possui iniciativa recíproca e concreta."),
          "power_inventory":("Quando a claridade se dissipou, seis armações perfeitamente iguais repousavam em seis estojos abertos.","GÊNESE manifesta seis objetos sem nerf introduzido."),
          "world_agency":("O envelope permaneceria onde estava enquanto a possibilidade não fosse esclarecida.","A frente remota preserva decisão e cautela próprias."),
          "sensory_wonder":("As montanhas se ergueram sobre a superfície.","O relevo ganha uma manifestação sensorial observável."),
          "arc_payoff":("O total anterior estava incluindo a previsão e a confirmação como se fossem duas despesas.","A criação produz consequência além da demonstração."),
          "choice_parity":("A rede tem que crescer.","A rede permanece como frente distinta das escolhas futuras."),
          "visual_design":("O pequeno ARGOS de gravetos havia perdido uma hélice.","A abertura dá lugar à prosa e experiência cotidiana."),
          "knowledge_location":("As seis marcas ainda não tinham um autor conhecido.","A investigação não promove hipótese a fato conhecido.")
        }
        p={"delivery_id":ident,"metadata":meta,"prose":prose,"full_text":full,"choices":choices,
           "longform_segments":segs,"r34_review":r34_review,"r35_review":r35_review,
           "r32_review":{"head":req["head"],"prose_sha256":sha(prose),
                        **{k:req[k] for k in ("requirements","reviewed","domain_review")},
                        "scene_requirements":[{"scene":x["scene"],"ids":x["ids"]} for x in req["scene_plan"]],
                        "arc_packet":ARC,"editorial_parity_reviewed":True},
           "r33_review":{"preparation_sha256":packet["preparation_sha256"],
                         "editorial_receipt_sha256":packet["editorial_receipt_sha256"],
                         "reviews":{k:{"status":"applied","evidence":e,"reason":reason} for k,(e,reason) in reviews.items()}}}
        def memory():
            out=release_review(work,req["head"],p)
            return {"memory":out["memory"]["coverage"],"semantic_certification":False}
        def r34check():
            out=r34(req,p);return {"dimensions":len(out["dimensions"]),"semantic_certification":False}
        def r35check():
            out=r35(work,req,p,packet["authority"]["choice"])
            return {"words":out["volume"]["words"],"floor":out["volume"]["floor"],
                    "segment_verified":out["segments"]["verified"],"scene_reviews":out["scene_reviews"],
                    "refinement_axes":len(out["refinement"]["axes"]),"semantic_certification":False}
        checks=[stage("native_r32_memory",memory),stage("native_r34_delivery",r34check),stage("native_r35_delivery",r35check)]
        # The controller does not fabricate a full typed Codex/event review.
        # Attempt the actual gate to expose the missing producer handoff.
        def submit():
            rr=verify_submission(work,req["head"],p)
            return {"integrity":rr["editorial"]["integrity_verified"],"semantic_certification":False}
        submitted=stage("native_r36_complete_submission_attempt",submit)
        output("generation_trial_summary",start,status="INCOMPLETE_FULL_HOMOLOGATION",
               structural_checks_passed=all(checks) and structure,
               submission_accepted=submitted,missing_full_codex_review=True,
               actual_generation=True,independent_review=False,canon_changed=False)
    return 0 if all(checks) and structure and not submitted else 1

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--archive-root",type=Path,required=True)
    raise SystemExit(run(parser.parse_args().archive_root))
