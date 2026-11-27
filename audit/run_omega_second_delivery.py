"""Actual second R36 draft, explicit source-grounded controller reviews.
Never promote canon. Native validators, no mocks, no bypasses.
"""
import argparse,hashlib,json,re,shutil,tempfile,time
from pathlib import Path
from audit.run_omega_second_trial import make_request,load
from audit.resolve_omega_second_trial import ID,SCOPES
from worldroot.git_cycle import canonical
from worldroot.r33_runtime import prepare_from_request,verify_submission,verify_history,digest
from worldroot.live_codex import sync,load_registry,all_records,aliases
from worldroot.r34_experience import render_opening,validate_delivery as r34
from worldroot.r35_longform import volume_check,validate_delivery as r35,scene_texts
from worldroot.experience_quality import render_choices
from worldroot.presentation_guard import presentation_preflight
from worldroot.r32_release import release_review
from worldroot.r35_refinement import rhythm_signals
from worldroot.draft_inbox import archive_inbox
from worldroot.delivery_gate import audit_release
FIXTURE=Path(__file__).parent/"omega-second-draft"
PREP="f6642079fbcf0646ab97491db8748b6fbec643edf137eb0adaac1469191e6920"
REQ="7b5e92a696c2e6ed68e98a88991ad5c2b4bea650e72acfe6e39a82303082ad58"
HASH="053c155aef2194760f59b352fc132da366149965679858f09d9a4edd7e231b76"
SEGMENTS=["ea7d4f432244db1a271d6df5d48dd3909d41b091dd407666eb534172255e97c1","5d182df50f6abe1b7310186c732f0bb90a913ac46b5dd2c5c62e182ad5e0d0f9","5bbccc5c7595728678aaf570c59d93f00fde7f8c7b94e52fc60be1b58542b367","d999238b6d8a910f0db080dd36a97b79211c173ad39037290b136e32679adbde"]
def sha(t):return hashlib.sha256(t.encode()).hexdigest()
def step(name,start,**kw):print(json.dumps({"trial_stage":name,"seconds":round(time.perf_counter()-start,6),**kw},ensure_ascii=False,sort_keys=True),flush=True)
def option(n,track,arc,title,promise,reward,risk,nxt,other):
    return dict(number=n,track=track,arc_id=arc,title=title,promise=promise,reward=reward,risk=risk,next_link=nxt,unselected_progress=other,guaranteed_success=False,combines_all=False)
ARC={"options":[
option(1,"main","continental","A estrada desenhada por duas mãos","Miren, Kael, Lysa e Astra avançam a troca autorizada de informações e a recepção das representações rumo à plenária.","Novos compromissos concretos entre povos.","Mandatos e respostas de cada povo permanecem independentes.","Conferência D585.","Operadores mantêm os instrumentos em uso."),
option(2,"secondary","network","A cidade de mil luzes","Lucas e os amigos exploram os setores de Três Arcos para escolher e instalar os primeiros enlaces entre computadores com os operadores.","Malha física em funcionamento e novos serviços.","Cada enlace depende de validação física, acesso e autorização.","Expansão da rede e Eixo Aurora.","A conferência continua por seus representantes."),
option(3,"secondary","mystery","A parede que mudou de lugar","Bressa e Tharvek procuram registros das divisões do Terceiro Fole e novos testemunhos dos antigos ofícios.","Pista material que pode mudar a leitura da construção.","A configuração do edifício não identifica automaticamente a técnica ou autor.","Investigação das seis marcas.","As outras frentes continuam em seus próprios ritmos."),
option(4,"secondary","life","ESPECIAL — Um bilhete sem destino","Lucas e Miren procuram uma ocasião real de utilizar o bilhete de passeio e conhecer o mundo sem converter cada parada em missão.","Descoberta, amizade e tempo compartilhado.","A viagem depende de horários e disponibilidade reais.","Vida vivida e novas paisagens.","As equipes mantêm a cooperação e pesquisa independentemente.")
],"free_action":True,"author_choice_recorded":False}
OPEN={"book_title":"LIVRO VI — AS COROAS PARTIDAS","chapter_title":"O QUE OS CAMINHOS CARREGAM","episode_title":"A LUZ QUE ENCONTROU OUTRA LUZ","epigraph":"Uma luz pode mostrar uma estrada. Só as pessoas podem escolher percorrê-la.","calendar":"Dia 580 · Ano II · M08 · D05","location":"Torre do Criador","fronts":"Três Arcos · Forja · Campo Aurora · AERÚN · Thalor · Halvern · Pedras Claras · Renshar · Vale · Serevan"}
BEATS=[
("uma névoa espessa havia subido das regiões baixas","Miren soltou uma risada tão repentina","A ferramenta que junta esses pedaços"), # overridden literal below
("Era diferente da luz das lâmpadas da Forja.","Seis pares idênticos dos Olhos do Criador repousavam em estojos individuais sobre a bancada.","A peça não precisava ser refeita."),
("Varo chegou alguns minutos depois.","Prefiro enxergar uma pessoa antes de enxergar informações sobre ela.","O trabalhador retirou as alças removíveis conforme a orientação do responsável"),
("Lysa escolheu os documentos de uma remessa civil.","Não eram dois materiais.","Agora podemos confirmar a remessa sem manter duas reservas para a mesma coisa."),
("A GÊNESE manifestou a Mesa dos Horizontes diante das representações.","O visitante de Thalor aproximou-se devagar.","Kael assinou o compromisso de fornecimento das informações autorizadas pela Cidade Livre."),
("A carta lacrada de Ordan continuava sob a responsabilidade do posto.","Acredito que precisam poder sair.","As seis marcas ainda não tinham sido encontradas naquela construção."),
("Rumo aproximou-se do grupo.","Uma indicação luminosa apareceu no condutor.","A estação local continuou executando suas operações."),
("Miren chegou à Torre alguns minutos depois de Lucas.","Mas quero lembrar também das vezes em que uma ideia sua serviu para nós dois.","As luzes de Três Arcos permaneciam acesas abaixo deles.")
]
BEATS[0]=("uma névoa espessa havia subido das regiões baixas","Miren soltou uma risada tão repentina","Lucas desceu da Torre com uma ideia que crescia a cada andar.")
BEATS[3]=("Ela escolheu os documentos de uma remessa civil.","Não eram dois materiais.","Agora podemos confirmar a remessa sem manter duas reservas para a mesma coisa.")
# Each moment is an authored, literal anchor tied to a specific editorial assessment.
OP={
"daily_life":[(1,"Roubaram a nossa cidade.","Humor doméstico nasce de um acontecimento observável."),(8,"Quero escolher o destino daquele passeio quando tivermos tempo de viajar sem levar uma missão junto.","Miren preserva o prazer de viajar por escolha.")],
"appearance":[(1,"Os cabelos escuros estavam presos de qualquer maneira","Traço histórico confirmado, penteado circunstancial."),(5,"A mulher colocou seu par dos Olhos do Criador, ajustou a armação","A interação com o instrumento torna gesto e postura observáveis.")],
"relationships":[(1,"Miren o puxou de volta pelo braço e lhe deu um beijo de verdade.","Reciprocidade afetuosa e iniciativa da esposa."),(8,"Mas quero lembrar também das vezes em que uma ideia sua serviu para nós dois.","A relação não se reduz ao trabalho do Criador.")],
"cast":[(2,"Os mestres preferiram repetir o ensaio em vez de aceitar a primeira indicação.","Decisão independente dos mestres sobre repetir o ensaio."),(3,"Prefiro enxergar uma pessoa antes de enxergar informações sobre ela.","Varo define limites e valores pessoais.")],
"wonder":[(2,"Seis pares idênticos dos Olhos do Criador repousavam em estojos individuais sobre a bancada.","Criação sensorial e consequência material."),(5,"O visitante de Thalor aproximou-se devagar.","Reação autônoma à maravilha manifestada.")],
"rhythm":[(4,"Lysa refez a soma de uma parte da relação no papel.","A verificação antecede a reação, não simples anúncio."),(8,"Durante algum tempo, não falaram de nada importante.","Pausa que deixa o cotidiano respirar.")]
}
OP["daily_life"][0]=(1,"Eu seria perfeitamente capaz de esquecer uma cidade dentro de um bolso.","Humor doméstico nasce de um acontecimento observável.")
OP["rhythm"][0]=(4,"Lysa refez a soma de uma parte da relação no papel.","A verificação antecede a reação, não simples anúncio.")
ASSESS={"daily_life":"Café, bilhete e varanda deixam o dia existir além do trabalho.","appearance":"Cabelo recuperado e gesto contextual sem novas medidas corporais.","relationships":"Casal divide vivências próprias, humor e promessa de passeio.","cast":"Mestres e Varo decidem como utilizar instrumentos e manter valores.","wonder":"Manifestação visual provoca descoberta e escolhas verificáveis.","rhythm":"Variação de pausas, experimentação, negociação e convivência."}
REF={
"cadence":("couple-style",[(1,"Miren fechou o livro sobre o indicador e veio até ele.","Pausa física e mudança de atenção."),(8,"Durante algum tempo, não falaram de nada importante.","A cena termina em convivência sem urgência.")],"Mais pausas e alternância que no primeiro ensaio, sem quota.","D568 contém um café íntimo; D580 liga percepção sensorial e descoberta."),
"voice_identity":("forja-voices",[(2,"A peça não precisava ser refeita.","Dorek enfatiza a consequência comprovada."),(3,"Prefiro enxergar uma pessoa antes de enxergar informações sobre ela.","Varo distingue segurança de vigilância.")],"Dorek e Varo preservam motivações distintas; Lysa conserva verificação.","D570 fundamenta a precisão dos mestres; D575 fundamenta o comandante."),
"emotion_adult":("couple-style",[(1,"Miren o puxou de volta pelo braço e lhe deu um beijo de verdade.","Iniciativa mútua do casal no gesto de afeto."),(8,"Mas quero lembrar também das vezes em que uma ideia sua serviu para nós dois.","Afeto e desejo de tempo compartilhado.")],"Carinho recíproco sem inventar medidas, idade histórica ou sexualização.","D568 oferece a referência cotidiana do casal em outro contexto."),
"wonder_payoff":("genese-proof",[(2,"Seis pares idênticos dos Olhos do Criador repousavam em estojos individuais sobre a bancada.","Manifestação completa de seis instrumentos para distribuição pessoal."),(5,"O visitante de Thalor aproximou-se devagar.","A maravilha é vivida por uma pessoa externa.")],"GÊNESE plena e reação sensorial, sem reduzir capacidade.","D578 apresenta ponte e ferrovia; D580 instrumentos e mapa."),
"exposition":("kael-voice",[(3,"A caixa passou.","O uso altera uma operação física."),(4,"Agora podemos confirmar a remessa sem manter duas reservas para a mesma coisa.","Uma decisão financeira substitui discurso.")],"As informações produzem ação, com exposição técnica ainda presente.","D571 mostra escuta de moradores; D580 muda operação e compromissos.")
}
REF["exposition"][1][0]=(3,"O trabalhador retirou as alças removíveis conforme a orientação do responsável","A operação física é ajustada em vez de apenas descrita.")
def moments(xs):return [dict(scene=n,evidence=a,effect=e) for n,a,e in xs]
def literal(prose,phrase):
    hits=[(i,l) for i,l in enumerate(prose.splitlines(),1) if phrase in l]
    if len(hits)!=1:raise ValueError("Anchor not unique: "+phrase[:100]+" ("+str(len(hits))+")")
    return hits[0]
def codex(root,prose):
    data,_=load_registry(root);rows=list(all_records(data));ids={x["id"] for x in rows}
    def pick(name,domain=None):
        if name in ids:return name
        matches=aliases(rows,name,domain=domain)
        if len(matches)!=1:raise ValueError("Unresolved record: "+name+" ("+str(len(matches))+")")
        return matches[0]["id"]
    city=pick("Três Arcos","Atlas mundial")
    valley=pick("Vale dos Ofícios Baixos","Atlas mundial")
    torre=pick("torre-criador");campo=pick("campo-aurora");inst=pick("aerun-instituto")
    events=[];new=[];inter=[];unresolved=[]
    def ev(who,kind,value,phrase,loc=None,scope="WORLD"):
        line,anchor=literal(prose,phrase)
        events.append(dict(entity_id=who,kind=kind,value=value,day=580,clock=None,scope=scope,location_id=loc,line=line,anchor=anchor))
    def at(who,loc,phrase):ev(pick(who,"Personagens"),"APPEARANCE",{"location_id":loc},phrase,loc)
    def item(key,name,phrase):
        line,anchor=literal(prose,phrase)
        ident="trial2:"+key;new.append(dict(id=ident,name=name,aliases=[],domains=["Tecnologia"],line=line,anchor=anchor));return ident
    def acquisition(item,phrase,loc):
        ev("lucas","ACQUIRE",dict(item_id=item,ownership_transfer=False),phrase,loc)
    def store(who,item,phrase,loc):
        ev(who,"STORE",dict(item_id=item,location_id=loc),phrase,loc)
    def transfer(item,who,phrase,loc,owned=True):
        ev("lucas","TRANSFER",dict(item_id=item,to_id=who,ownership_transfer=owned),phrase,loc)
    def use(who,item,phrase,loc,method):
        ev(who,"USE_ITEM",dict(item_id=item,method=method),phrase,loc)
        line,anchor=literal(prose,phrase)
        inter.append(dict(actor=who,target=item,kind="ITEM",disposition="SUPPORTED",reason=method,line=line,anchor=anchor))
    def knowledge(who,field,value,phrase,loc=None,scope="PRIVATE_CHARACTER"):
        ev(who,"KNOW",dict(field=field,value=value),phrase,loc,scope)
    def attribute(who,field,value,phrase,loc=None):
        ev(who,"ATTRIBUTE",dict(field=field,value=value),phrase,loc)
    def magic(phrase,loc):
        ev("lucas","CAST",{"spell_id":"genese"},phrase,loc)
        line,anchor=literal(prose,phrase)
        inter.append(dict(actor="lucas",target="genese",kind="MAGIC",disposition="SUPPORTED",reason="Manifestação própria do Criador, sem atribuição a outro personagem.",line=line,anchor=anchor))
    at("lucas",torre,"Ele parou diante da janela com a caneca na mão.")
    at("miren",torre,"Miren fechou o livro sobre o indicador")
    knowledge("nox","conceito_olhos","Origem dos registros é necessária; participa voluntariamente.","Posso participar da concepção, caso você queira.",torre)
    knowledge("miren","conceito_olhos","Instrumentos não transformam hipótese em fato.","Uma ferramenta que junta esses pedaços não transforma uma hipótese em fato.",torre)
    at("lucas",city,"O som dos martelos recebeu Lucas")
    at("brannik",city,"Brannik viu Lucas primeiro.")
    at("dorek",city,"Dorek, que examinava uma peça junto à bancada")
    at("astra",city,"Astra estava presente por outro motivo")
    magic("GÊNESE — AUTORIDADE DO CRIADOR.",city)
    eyes={}
    creation="Seis pares idênticos dos Olhos do Criador repousavam em estojos individuais sobre a bancada."
    for who in ("lucas","miren","astra","varo","kael","lysa"):
        eyes[who]=item("olhos-"+who,"Olhos do Criador — exemplar de "+who.title()+" D580",creation)
        acquisition(eyes[who],creation,city)
    transfer(eyes["astra"],"astra","Astra pegou seu estojo e retirou o par.",city)
    use("astra",eyes["astra"],"A lente indicou a distância estimada até a superfície",city,"Observação local dimensional e térmica conferida com instrumento convencional.")
    collection=item("forja-colecao","Coleção especializada dos Olhos — Forja D580","Lucas manifestou a coleção especializada completa da Forja")
    acquisition(collection,"Lucas manifestou a coleção especializada completa da Forja",city)
    store("lucas",collection,"Os mestres escolheriam o que serviria a cada ofício.",city)
    computer=item("forja-computador","Computador arcano da Forja — estação D580","A primeira estação de computador arcano da Forja tomou forma")
    acquisition(computer,"A primeira estação de computador arcano da Forja tomou forma",city)
    store("lucas",computer,"A primeira estação de computador arcano da Forja tomou forma",city)
    use("brannik",computer,"Brannik ligou uma entrada de instrumento sob orientação de Astra.",city,"Entrada do instrumento e registro da medida na estação.")
    attribute("dorek","ensaio_D580","Desgaste do apoio identificado; repetição com outro apoio voltou à faixa esperada.","A peça não precisava ser refeita.",city)
    # Physical units manifested at Forja before transport, then handed to Varo.
    for key,label in [("legiao","Legião"),("sombras","Sombras")]:
        ident=item(key+"-computador","Computador arcano — "+label+" D580","computadores transportáveis destinados à Legião e aos Sombras")
        acquisition(ident,"computadores transportáveis destinados à Legião e aos Sombras",city)
        transfer(ident,"varo","Os computadores destinados à Legião e aos Sombras foram entregues a Varo",campo,False)
    at("lucas",campo,"O terminal que ajudara a criar dois dias antes")
    at("naira",campo,"Ela vinha da área de controle")
    at("varo",campo,"Varo chegou alguns minutos depois.")
    transfer(eyes["varo"],"varo","Lucas abriu o estojo destinado a Varo.",campo)
    use("varo",eyes["varo"],"Usou os Olhos para estimar as dimensões externas",campo,"Estima dimensões externas; equipe confere compartimento e alças reais.")
    attribute("naira","decisao_carga_D580","A equipe reorganiza a movimentação após identificar a interferência das alças.","A caixa passou.",campo)
    cp=item("campo-computador","Computador arcano do Campo Aurora — estação civil D580","E criou o primeiro computador arcano do Campo Aurora")
    acquisition(cp,"E criou o primeiro computador arcano do Campo Aurora",campo);store("lucas",cp,"E criou o primeiro computador arcano do Campo Aurora",campo)
    knowledge("varo","separacao_registros","Registros da Legião separados do setor civil.","E os registros da Legião não serão misturados a esse conjunto.",campo)
    at("lucas",city,"Lysa tinha duas folhas abertas quando Lucas chegou.")
    at("lysa",city,"Lysa tinha duas folhas abertas quando Lucas chegou.")
    at("kael",city,"Kael estava diante de uma relação de solicitações")
    for who in ("lysa","kael"):
        transfer(eyes[who],who,"Lucas entregou os pares pessoais dos Olhos do Criador a Lysa e Kael.",city)
    use("lysa",eyes["lysa"],"Lysa experimentou a sua, observou a posição das folhas",city,"Leitura simples e seleção de registro.")
    use("kael",eyes["kael"],"Kael fez um teste semelhante e desligou as indicações",city,"Teste e seleção pessoal de informações.")
    lc=item("lysa-computador","Computador arcano — gabinete de Lysa D580","O computador arcano do gabinete de Lysa surgiu diante dela.")
    acquisition(lc,"O computador arcano do gabinete de Lysa surgiu diante dela.",city);transfer(lc,"lysa","Ela escolheu os documentos de uma remessa civil.",city,False)
    use("lysa",lc,"Lysa refez a soma de uma parte da relação no papel.",city,"Conciliação de previsão e confirmação, verificada em papel.")
    attribute("lysa","correcao_reserva_D580","Registros vinculados sem exclusão; reserva indevida deixa de contar como obrigação.","Agora podemos confirmar a remessa sem manter duas reservas para a mesma coisa.",city)
    kc=item("kael-computador","Computador arcano — gabinete de Kael D580","Lucas materializou o computador arcano destinado ao gabinete de Kael")
    acquisition(kc,"Lucas materializou o computador arcano destinado ao gabinete de Kael",city)
    transfer(kc,"kael","Kael escolheu que a primeira utilização fosse a organização das solicitações",city,False)
    at("miren",inst,"Miren chegou ao auditório")
    at("astra",inst,"Astra estava perto de uma mesa lateral")
    at("lucas",inst,"Quando Lucas apareceu, ela estava conversando")
    transfer(eyes["miren"],"miren","Lucas entregou o último estojo a Miren.",inst)
    use("miren",eyes["miren"],"Escolheu a leitura geométrica.",inst,"Comparação geométrica de reprodução; não confunde desenho com objeto.")
    ac=item("aerun-computador","Computador arcano — Instituto AERÚN D580","O computador arcano do Instituto AERÚN foi manifestado")
    acquisition(ac,"O computador arcano do Instituto AERÚN foi manifestado",inst);store("lucas",ac,"O computador arcano do Instituto AERÚN foi manifestado",inst)
    at("kael",inst,"Kael encontrou-os na entrada do auditório.")
    at("lysa",inst,"Lysa conferiu as credenciais")
    magic("A GÊNESE manifestou a Mesa dos Horizontes diante das representações.",inst)
    mesa=item("mesa","Mesa dos Horizontes — exemplar D580","A GÊNESE manifestou a Mesa dos Horizontes diante das representações.")
    acquisition(mesa,"A GÊNESE manifestou a Mesa dos Horizontes diante das representações.",inst)
    store("lucas",mesa,"A GÊNESE manifestou a Mesa dos Horizontes diante das representações.",inst)
    use("astra",mesa,"Podemos mudar a escala.",inst,"Muda escala de representação sem transformar relatos em medição.")
    attribute("kael","compromisso_thalor_D580","Fornecimento de informações autorizadas; recebimento e encaminhamento no mandato, sem tratado geral.","Kael assinou o compromisso de fornecimento",inst)
    # The independent fronts are separately reviewed; no knowledge is attributed to Lucas.
    # Source-attested name but absent from bound registry: keep explicit pending identity.
    def pending(name,phrase):
        line,anchor=literal(prose,phrase)
        unresolved.append(dict(name=name,line=line,anchor=anchor,reason="Pessoa narrada com identidade ainda não vinculada ao registro; não criar ID canônico por suposição."))
    pending("Osvan","Osvan recebeu dois viajantes")
    at("avelna","renshar","Avelna observava uma mulher discutir")
    if aliases(rows,"Orelia",domain="Personagens"):
        at("Orelia","renshar","Orelia chegou com os registros")
    else:pending("Orelia","Orelia chegou com os registros")
    at("velkar","renshar","Orelia levou o documento a Velkar.")
    attribute("velkar","retirada_comercial_D580","Solicita orientação consistente com acordo existente, sem exigência militar nova.","Pediu a Orelia que verificasse","renshar")
    at("bressa",valley,"Bressa apoiou a lanterna")
    at("tharvek",valley,"Tharvek trouxe a planta")
    knowledge("bressa","seis_marcas","Diferença de configuração não prova autoria ou mecanismo.","As seis marcas ainda não tinham sido encontradas",valley)
    at("varkhess","serevan","Varkhess acompanhou a entrega")
    at("serina","serevan","Serina colocou duas folhas lado a lado.")
    knowledge("serina","busca_mar","Região candidata; nenhum desaparecido encontrado.","Nenhum desaparecido havia sido encontrado.","serevan")
    at("astra",inst,"Astra encontrou Rumo examinando")
    at("rumo",inst,"Astra encontrou Rumo examinando")
    at("lucas",inst,"Lucas chegou acompanhado dos mestres da Forja")
    at("dorek",inst,"Dorek trazia uma relação de observações")
    at("brannik",inst,"Brannik carregava um estojo")
    use("lucas",eyes["lucas"],"Tirou seu par dos Olhos do Criador do estojo e colocou-o.",inst,"Seleciona apenas fontes com ligação disponível.")
    link=item("enlace","Enlace local de computadores — ensaio AERÚN D580","Então o Criador manifestou os componentes do novo enlace.")
    acquisition(link,"Então o Criador manifestou os componentes do novo enlace.",inst);store("lucas",link,"havia um caminho material entre as duas estações de ensaio.",inst)
    use("rumo",link,"Rumo desligou a conexão de teste.",inst,"Teste deliberado de isolamento local; operação da estação continua.")
    knowledge("lucas","implantacao_sombras","Recebe confirmação de instalação, não conteúdo restrito.","A mensagem não trazia o conteúdo daqueles registros",inst)
    at("lucas",torre,"Encontrou-o junto à varanda")
    at("miren",torre,"Miren chegou à Torre alguns minutos depois de Lucas.")
    store("miren",eyes["miren"],"Miren apoiou o próprio par dos Olhos do Criador ao lado do livro.",torre)
    store("lucas",eyes["lucas"],"Lucas deixou o seu sobre a outra extremidade da mesa.",torre)
    # Explicit material coherence: measured fit was adapted, not a claim of an
    # unverified dimensional capacity. No cross-entity combat occurred.
    line,anchor=literal(prose,"A caixa passou.")
    inter.append(dict(actor="varo",target=eyes["varo"],kind="ITEM",disposition="SUPPORTED",reason="Equipe verificou dimensões, alças e reorganizou a operação, não afirma que uma abertura medida no papel basta.",line=line,anchor=anchor))
    for phrase in ["Ele beijou-lhe a testa.","Miren o puxou de volta pelo braço","Lucas puxou-a para perto e a abraçou."]:
        line,anchor=literal(prose,phrase);inter.append(dict(actor="lucas",target="miren",kind="TOUCH",disposition="SUPPORTED",reason="Contato consensual narrado sem medida corporal ou atributo não confirmado.",line=line,anchor=anchor))
    delta=dict(schema="worldroot-codex-delta-v1",episode=ID,prose_sha256=sha(prose),events=events,new_entities=new,unresolved=unresolved)
    # Every event is assigned to the literal scene. Every named speaker receives
    # an explicit identity via events above. Other narrated entities and plot
    # references are dispositions, not fabricated presence.
    lines=prose.splitlines()
    starts=[i for i,l in enumerate(lines,1) if re.match(r"^## [IVX]+ — ",l)]
    starts[0]=1
    ends=starts[1:]+[len(lines)+1]
    scene_sync=[]
    for st,en in zip(starts,ends):
        ords=[j for j,e in enumerate(events) if st<=e["line"]<en]
        mentions=[dict(disposition="IDENTIFIED",id=events[j]["entity_id"],line=events[j]["line"],anchor=events[j]["anchor"]) for j in ords]
        mentions += [dict(disposition="IDENTIFIED",id=n["id"],line=n["line"],anchor=n["anchor"]) for n in new if st<=n["line"]<en]
        mentions += [dict(disposition="UNRESOLVED",name=u["name"],line=u["line"],anchor=u["anchor"]) for u in unresolved if st<=u["line"]<en]
        scene_sync.append(dict(start_line=st,end_line=en-1,mentions=mentions,event_ordinals=ords,cross_checks=[dict(status="OK",reason="Evidências explicitamente anotadas; sem pretensão de inferência semântica automática.")],hooks=[]))
    return delta,dict(schema="worldroot-coherence-review-v1",interactions=inter,coverage_reason="Revisão manual das manifestações, posse, uso, toque e operação material; medidas históricas não substituídas."),dict(schema="worldroot-scene-codex-sync-v1",scenes=scene_sync)
def run(root,out):
    start=time.perf_counter();out.mkdir(parents=True,exist_ok=True)
    chunks=[(FIXTURE/f"{i:02d}.md").read_text(encoding="utf-8") for i in range(1,5)]
    assert [sha(s) for s in chunks]==SEGMENTS and sha("".join(chunks))==HASH
    meta=dict(book="Livro VI",chapter=9,part="II",day=580,hour="22h31",location="Torre do Criador; frentes independentes",canon_status="RASCUNHO",worldroot_revision=35)
    choices=render_choices(ARC,ID,revision=35)
    opening=render_opening(meta,OPEN)
    chunks[0]=choices["body_declaration"]+"\n"+opening+"\n<caption>Motor R36 Evolution 7 + OMEGA · contrato narrativo R35 · ensaio não canônico</caption>\n\n---\n\n"+chunks[0]
    prose="".join(chunks)
    checkpoint='<box border radius="lg" padding={3} gap={2}>\n  <caption>WORLDROOT · CHECKPOINT NARRATIVO</caption>\n  <grid columns={2} gap={2}>\n    <grid-item><caption>Criações</caption>**Seis pares pessoais, Forja, computadores, Mesa e enlace local.**</grid-item>\n    <grid-item><caption>Frentes</caption>**Carta em Pedras Claras; seis marcas e busca marítima em aberto; cooperação civil avança.**</grid-item>\n    <grid-item><caption>Próximo marco</caption>**D581 · Parte III · Plenária D585.**</grid-item>\n  </grid>\n</box>'
    full=prose+"\n---\n\n"+checkpoint+"\n\n"+choices["markup"]
    volume=volume_check(prose,"II",1);step("actual_prose_readback",start,volume=volume,signals=rhythm_signals(prose),presentation=presentation_preflight(full)["checks"],generation_seconds=256.999,semantic_certification=False)
    with tempfile.TemporaryDirectory() as d:
        w=Path(d)/"archive";shutil.copytree(root,w,ignore=shutil.ignore_patterns(".git"));sync(w)
        req=make_request(w);req["delivery_id"]=ID;req["world_scope"]=SCOPES
        assert digest(req)==REQ
        (w/"requests"/(ID+".json")).write_bytes(canonical(req));p=prepare_from_request(w,req);assert p["preparation_sha256"]==PREP
        packet=load(w/"preparations"/(ID+".json"))
        seg=[]
        for i,s in enumerate(chunks,1):
            path=f"production/{ID}/segments/{i:02d}.md";q=w/path;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(s.encode());seg.append(dict(part=i,path=path,sha256=sha(s)))
        dims={k:dict(status="applied",reason=ASSESS[k],scene=xs[0][0],evidence=xs[0][1]) for k,xs in OP.items()}
        dims["appearance"].update(character="Miren",concrete_detail="cabelos escuros")
        dims["design"]=dict(status="applied",reason="Renderizador nativo e identificação explícita da versão de engenharia.",evidence="CRÔNICAS DE UM NOVO MUNDO · WORLDROOT R35")
        review34=dict(schema="worldroot-r34-review-v1",opening=OPEN,dimensions=dims,comparison_result="Comparação contextual com D568, D570, D571 e D578; pausas, ação, reações e decisões observáveis.",no_forced_scenes=True,no_unsupported_traits=True)
        review35=dict(schema="worldroot-r35-review-v1",scenes=[dict(scene=i,planned_scene=i,beats=dict(zip(("experience","reaction","payoff"),b)),assessment="A experiência, reação e resultado aparecem em trechos distintos.") for i,b in enumerate(BEATS,1)],opportunities={k:dict(status="applied",assessment=ASSESS[k],moments=moments(xs)) for k,xs in OP.items()},comparison={k:dict(reference_id=ref,assessment=note,result="contextual_difference") for k,ref,note in [("cadence","couple-style","Alterna pausa, diálogo e reação em composição distinta."),("emotion","couple-style","Preserva humor e relação com iniciativas dos dois."),("adventure","genese-proof","A criação traz descoberta física e horizonte futuro."),("character","forja-voices","Dorek e Brannik conservam contrastes de voz."),("design","kael-voice","Interface nativa com escolhas distintas e ação livre.")]},no_padding=True,no_condensed_key_events=True,adult_focus={k:dict(status="held",assessment="Afeto cotidiano não gráfico e agência preservados.",context="Plano não recuperou idade narrativa explícita para esta oportunidade.") for k in req["r35_plan"]["adult_focus"]},refinement=dict(schema="worldroot-r35-refinement-review-v1",axes={k:dict(reference_id=ref,result="contextual_difference",assessment=a,contrast=c,moments=moments(xs),density_response="Densidade ainda menor que D568; preservar variação natural, não fragmentar artificialmente.") for k,(ref,xs,a,c) in REF.items()},no_artificial_fragmentation=True,no_administrative_padding=True,no_forced_conflict_or_romance=True))
        menu=[dict(number=o["number"],title=o["title"],description=o["promise"],is_special=o["number"]==4,is_free=False) for o in ARC["options"]]+[dict(number=5,title="AÇÃO LIVRE",description="Ação livre para continuação experimental, sem efeito canônico.",is_special=False,is_free=True)]
        review33={k:dict(status="applied",evidence=a,reason=b) for k,a,b in [
          ("continuity","O pássaro de madeira de Ordan permanecia perto da pequena aeronave de gravetos","Objetos preservados conforme D579."),
          ("causality","A peça não precisava ser refeita.","Mestres conferem ensaio e corrigem apoio."),
          ("identity_voice","Prefiro enxergar uma pessoa antes de enxergar informações sobre ela.","Varo decide como utilizar a novidade."),
          ("relationships","Miren o puxou de volta pelo braço e lhe deu um beijo de verdade.","Aproximação voluntária e recíproca."),
          ("power_inventory","Seis pares idênticos dos Olhos do Criador repousavam em estojos individuais sobre a bancada.","Criação e distribuição com GÊNESE plena."),
          ("world_agency","Acredito que precisam poder sair.","Avelna defende autonomia diante de Velkar."),
          ("sensory_wonder","A GÊNESE manifestou a Mesa dos Horizontes diante das representações.","Maravilha sensorial vivida pelos presentes."),
          ("arc_payoff","Agora podemos confirmar a remessa sem manter duas reservas para a mesma coisa.","Ferramenta produz decisão concreta."),
          ("choice_parity","O futuro precisa chegar.","Rede é uma rota distinta e não engloba todas."),
          ("visual_design","Naquela manhã, Três Arcos desapareceu.","O texto mantém narrativa dominante, sem imagens."),
          ("knowledge_location","Nenhuma mensagem de uma máquina distante lhes trouxe o brilho da Mesa dos Horizontes.","Limite causal de conhecimento remoto.")
        ]}
        payload=dict(schema="worldroot-draft-inbox-v3",delivery_id=ID,metadata=meta,prose=prose,full_text=full,choices=menu,book_closed=False,editorial_visibility="PRIVADO",longform_segments=seg,r34_review=review34,r35_review=review35,r32_review=dict(head=req["head"],prose_sha256=sha(prose),**{k:req[k] for k in ("requirements","reviewed","domain_review")},scene_requirements=[dict(scene=x["scene"],ids=x["ids"]) for x in req["scene_plan"]],arc_packet=ARC,editorial_parity_reviewed=True),r33_review=dict(preparation_sha256=PREP,editorial_receipt_sha256=packet["editorial_receipt_sha256"],reviews=review33))
        t=time.perf_counter();release_review(w,req["head"],payload);r34(req,payload);rr=r35(w,req,payload,packet["authority"]["choice"]);step("native_r32_r34_r35",t,passed=True,words=rr["volume"]["words"],segments=rr["segments"]["verified"],axes=len(rr["refinement"]["axes"]))
        t=time.perf_counter();delta,coherence,scene=codex(w,prose);payload["r33_review"].update(codex_delta=delta,world_coherence=coherence,codex_sync=scene)
        step("explicit_typed_review",t,events=len(delta["events"]),new_entities=len(delta["new_entities"]),interactions=len(coherence["interactions"]),scenes=len(scene["scenes"]),semantic_certification=False)
        t=time.perf_counter();r=verify_submission(w,req["head"],payload);step("native_r36_submission",t,passed=True,editorial_integrity=r["editorial"]["integrity_verified"],codex_events=len(r["codex_delta"]["events"]),scene_sync=r["codex_sync_result"],coherence=r["world_coherence_result"],semantic_certification=False)
        # Historical event and NPC knowledge sidecars are a separate contract.
        # Only concrete narrated outcomes, with unique evidence and visibility.
        evs=[];kn=[]
        for i,(phrase,summary,who,know) in enumerate([
          ("Seis pares idênticos dos Olhos do Criador repousavam","Lucas manifesta seis pares idênticos para distribuição pessoal.","Astra","Seis pares pessoais foram manifestados."),
          ("A peça não precisava ser refeita.","O ensaio da Forja identificou desgaste do apoio, e a repetição corrigiu a leitura.","Dorek","O apoio, não a peça, motivou a leitura observada."),
          ("A caixa passou.","Operadores ajustaram a movimentação depois de conferir alças e espaço.","Varo","As medidas externas não bastam sem considerar movimentação."),
          ("Agora podemos confirmar a remessa sem manter duas reservas","Lysa confirmou remessa após identificar dupla reserva da mesma operação.","Lysa","Previsão e confirmação representam a mesma operação."),
          ("A GÊNESE manifestou a Mesa dos Horizontes","Lucas materializou a Mesa para compartilhar dados locais e representações.","Miren","A Mesa permite comparar mapas de origens distintas."),
          ("Kael assinou o compromisso de fornecimento","Kael assinou fornecimento de dados autorizados, sem tratado geral.","Kael","O compromisso respeita os mandatos das representações."),
          ("A carta continuou lacrada nas Pedras Claras.","A carta de Ordan continua sob custódia do posto; consulta ainda pendente.","Osvan","Não há confirmação de entrega além de Pedras Claras."),
          ("Pediu a Orelia que verificasse","Velkar pediu verificação das condições de retirada comercial.","Velkar","A segunda comunidade solicita condições de retirada."),
          ("As seis marcas ainda não tinham sido encontradas","Bressa e Tharvek encontram diferenças de configuração, sem autoria confirmada.","Bressa","Não há prova das seis marcas naquele edifício."),
          ("Nenhum desaparecido havia sido encontrado.","A expedição retorna sem identificação definitiva ou desaparecidos localizados.","Serina","A formação permanece candidata e a busca continua."),
          ("A estação local continuou executando suas operações.","Enlace local demonstrado; desconexão preservou funcionamento local.","Rumo","Estação funciona mesmo após desligamento do enlace."),
          ("Miren apoiou o próprio par dos Olhos do Criador ao lado do livro.","Lucas e Miren mantêm pares pessoais na Torre e preservam passeio futuro.","Miren","O passeio continua sem destino definido.")
        ],1):
            line,anchor=literal(full,phrase);eid="LVI-C09-PII-D580-OMEGA2-E%02d"%i;visibility="PRIVADO_PERSONAGEM" if i in (7,9,10,12) else "PUBLICO"
            evs.append(dict(event_id=eid,event_type="EVENT",canon_status="NARRADO",occurred_day=580,clock=None,visibility=visibility,source=dict(line=line,literal_anchor=anchor,sha256=sha(full)),summary_candidato=summary))
            kn.append(dict(person=who,knowledge=know,source_event=eid,acquired_day=580,clock=None,visibility="PRIVADO_PERSONAGEM"))
        payload["reviewed_events"]=evs;payload["reviewed_knowledge"]=kn
        payload["narrative_direction"]=dict(schema="worldroot-narrative-direction-v1",source_episode_id=req["head"]["episode_id"],author_choice="Reprodução experimental da opção 1 real e do suplemento D580, sem nova escolha.",reader_promise="Descoberta tecnológica vivida por pessoas, com resultados, reações e decisões próprias.",lucas_lived_focus="Humor, afeto, amizade e entusiasmo de Lucas com GÊNESE plena.",central_change="Seis pares, ferramentas, computadores, Mesa e enlace local materializados e utilizados.",independent_world=["Miren, Astra, Lysa e Kael conduzem a conferência e decisões civis.","Varo, Naira e os mestres definem aplicações e limites próprios.","Renshar, Pedras Claras, Vale e Serevan seguem sem conhecimento remoto."],unknowns_preserved=["Carta não entregue à irmã de Ordan; Talis desaparecida.","Seis marcas e identificação da formação marítima permanecem pendentes.","Não há rede continental, tratado geral ou adesão política presumida."],does_not_choose_for_lucas=True)
        romans=["I","II","III","IV","V","VI","VII","VIII"]
        payload["reader_review"]=dict(schema="worldroot-r25-reader-review-v1",decision="REVISADO_COM_EVIDENCIAS",scene_evidence=[dict(scene=romans[i],literal_anchor=b[0],felt_experience="A personagem vive a situação concreta em vez de apenas receber um relatório.",scene_turn="A cena muda com a reação narrada: "+b[1],lasting_consequence="Resultado explícito: "+b[2]) for i,b in enumerate(BEATS)],pacing_decision="Variação entre cotidiano, descoberta, trabalho, diplomacia, frentes independentes e pausa afetiva; sem quota de cenas.")
        payload["fantasy_review"]=dict(schema="worldroot-r26-fantasy-review-v1",source_episode_id=req["head"]["episode_id"],cannot_choose_for_author=True,genese_unrestricted=True,backstage_invisible=True,combat=dict(mode="SEM_COMBATE"),wonder=dict(mode="DESCOBERTA",encounters=[dict(literal_anchor="Seis pares idênticos dos Olhos do Criador repousavam em estojos individuais sobre a bancada.",sensory_difference="Filamentos dourados e lentes de cristal surgem sobre a bancada.",character_reaction="Astra testa as medidas e os mestres repetem a leitura.",world_independence="Cada usuário decide o que observar e confere a fonte."),dict(literal_anchor="A GÊNESE manifestou a Mesa dos Horizontes diante das representações.",sensory_difference="Relevo luminoso com regiões conhecidas e contornos incompletos.",character_reaction="Visitante aproxima a mão e procura estradas familiares.",world_independence="As delegações escolhem os dados e respeitam seus mandatos.")]),spell_uses=[],summon_uses=[],moments=[dict(scene="II",first_anchor="Seis pares idênticos dos Olhos do Criador repousavam em estojos individuais sobre a bancada.",reaction_anchor="Astra pegou seu estojo e retirou o par.",dramatic_promise="Criação de instrumentos que os amigos utilizam por escolha.",sensory_change="As lentes mostram dimensões, calor e fontes locais.",lasting_consequence="O ensaio identifica desgaste do apoio e corrige a operação.",not_just_reported=True),dict(scene="V",first_anchor="A GÊNESE manifestou a Mesa dos Horizontes diante das representações.",reaction_anchor="O visitante de Thalor aproximou-se devagar.",dramatic_promise="Uma superfície compartilhada transforma a conversa das representações.",sensory_change="Mapa luminoso com relevo, estradas e lacunas diferenciadas.",lasting_consequence="Representação recebe informações autorizadas sem tratado geral.",not_just_reported=True)],character_evolution=[dict(name="Varo",literal_anchor="Prefiro enxergar uma pessoa antes de enxergar informações sobre ela.",decision_or_reaction="Varo escolhe desligar indicações e usa medida para ajustar carga.",emotional_or_relational_delta="Mantém responsabilidade e respeito à autonomia das pessoas."),dict(name="Lysa",literal_anchor="Agora podemos confirmar a remessa sem manter duas reservas para a mesma coisa.",decision_or_reaction="Concilia documentos e confere cálculo antes de executar decisão.",emotional_or_relational_delta="A ferramenta amplia a competência sem substituir seu julgamento.")],variation_decision="Cotidiano, criação, ensaio, negociação, frentes paralelas e afetos alternam função.",pacing_justification="Os resultados são vividos em cenas; a manifestação tem reação, teste e consequência verificável. Não se força combate nem conflito romântico.")
        payload["character_preflight"]=[dict(name=x["name"],last_physical_appearance_source=("Ver preparação: varo-role (D575); presença posterior D576 a confirmar" if x["name"]=="Varo" else "Último estado recuperado na preparação, consultar evidência individual"),location_at_scene="Conforme aparições anotadas e evidências mais recentes",affiliation_at_scene="Revisão vinculada ao Codex",knowledge_at_scene="Apenas percepção local ou comunicação narrada") for x in req["r34_intent"]["characters"]]
        payload["editorial_tags"]=[]
        # Recheck entire final payload, not pre-sidecar bytes.
        verify_submission(w,req["head"],payload)
        (w/"inbox"/(ID+".json")).write_bytes(canonical(payload))
        t=time.perf_counter();a=archive_inbox(w,w/"inbox"/(ID+".json"));step("disposable_native_archive",t,status=a["status"],files=a["changed_file_count"],events=a["events"],knowledge=a["knowledge"])
        t=time.perf_counter();gate=audit_release(w,ID);step("disposable_native_delivery",t,allowed=gate["release_allowed"],checks=gate["checks"],errors=gate["errors"],semantic_certification=False)
        assert gate["release_allowed"]
        h=verify_history(w);again=archive_inbox(w,w/"inbox"/(ID+".json"));assert again["changed_file_count"]==0
        step("disposable_history_readback",t,history=h,idempotent=True,canon_changed=False)
        (out/"episode.md").write_text(full,encoding="utf-8")
        (out/"submission.json").write_bytes(canonical(payload))
        (out/"receipt.json").write_bytes(canonical(gate))
        step("second_full_trial",start,passed=True,canon_changed=False,semantic_certification=False,independent=False)
if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--archive-root",type=Path,required=True);a.add_argument("--output",type=Path,required=True);n=a.parse_args();run(n.archive_root,n.output)
