"""R35 additive regression: no production canon or author choices changed.
Synthetic fixtures and literal historical excerpts kept strictly separate.
"""
import hashlib
import json
import sqlite3
import unittest
from worldroot.live_codex import SCHEMA, initialize, apply_delta, current, graph_rows, aliases, jsonstr

class CodexEvolutionTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:")
        initialize(self.db)
        self.seed("lucas","Lucas",["Personagens"])
        self.seed("kael-canon","Kael",["Personagens"],["Estrategista"])
        self.seed("miren","Miren",["Personagens"])
        self.db.commit()
        self.seq=0

    def tearDown(self):
        self.db.close()

    def seed(self,ident,name,domains,aliases_=None):
        self.db.execute("INSERT INTO records VALUES(?,?,?)",("assets",ident,jsonstr({"id":ident,"name":name,"domains":domains,"aliases":aliases_ or []})))

    def apply(self,prose,events=(),new=(),unresolved=(),ep=None,day=580,sequence=None):
        if sequence is None:
            self.seq+=1
            sequence=self.seq
        ep=ep or "fixture"+str(sequence)
        sha=hashlib.sha256(prose.encode()).hexdigest()
        d={"schema":SCHEMA,"episode":ep,"prose_sha256":sha,"events":list(events),"new_entities":list(new),"unresolved":list(unresolved)}
        return apply_delta(self.db,d,prose,sequence,day,sha,{"genese","spell"})

    def new(self,ident,name,domain,anchor,**extra):
        return {"id":ident,"name":name,"domains":[domain],"line":1,"anchor":anchor,**extra}

    def ev(self,kind,ident,anchor,value,line=1,scope="WORLD",day=580):
        return {"kind":kind,"entity_id":ident,"value":value,"day":day,"clock":"10h00","scope":scope,"line":line,"anchor":anchor}

    def pending(self,pid):
        return self.db.execute("SELECT status,category,body,last_event FROM codex_pending WHERE pending_id=?",(pid,)).fetchone()

    def test_multidomain_synthetic_6_entities_without_invented_fields(self):
        p="Lucas encontrou um dragão negro, uma ruína submersa, um planador, Mara, um ferreiro chamado Kael e Vespera."
        entries=[self.new("dragon","Dragão negro","Bestiário",p),self.new("ruin","Ruína submersa","Ambientes",p),self.new("glider","Planador","Tecnologia",p),self.new("mara","Mara","Personagens",p),self.new("kael-smith","Kael","Personagens",p,identity_resolution={"kind":"DISTINCT_HOMONYM","distinct_from":["kael-canon"],"reason":"fixture distinguishes the blacksmith from the strategist"}),self.new("vespera","Vespera","Personagens",p)]
        events=[self.ev("RELATION","lucas",p,{"target_id":x["id"],"relation":"mentioned_encounter","value":True}) for x in entries]
        self.assertEqual(self.apply(p,events,entries),"APPLIED")
        self.assertEqual(self.db.execute("SELECT count(*) FROM records").fetchone()[0],9)
        self.assertEqual(self.db.execute("SELECT count(*) FROM codex_events").fetchone()[0],6)
        row=next(r for r in graph_rows(self.db) if r["id"]=="dragon")
        self.assertNotIn("origin",row)
        self.assertNotIn("powers",row)

    def test_alias_same_identity_preserves_history(self):
        p="Mara chegou."
        self.apply(p,new=[self.new("mara","Mara","Personagens",p)])
        q="Mara apresentou-se como Olho-de-Bruma."
        self.apply(q,[self.ev("ALIAS","mara",q,{"alias":"Mara, a Olho-de-Bruma"})])
        self.assertEqual([r["id"] for r in aliases(graph_rows(self.db),"Mara, a Olho-de-Bruma")],["mara"])
        self.assertEqual(self.db.execute("SELECT count(*) FROM records").fetchone()[0],4)

    def test_duplicate_existing_name_rejected(self):
        p="Kael chegou."
        with self.assertRaisesRegex(ValueError,"collision"):
            self.apply(p,new=[self.new("fake-kael","Kael","Personagens",p)])
        self.assertEqual(self.db.execute("SELECT count(*) FROM records").fetchone()[0],3)

    def test_duplicate_existing_alias_rejected(self):
        p="O Estrategista chegou."
        with self.assertRaisesRegex(ValueError,"collision"):
            self.apply(p,new=[self.new("fake","Estrategista","Personagens",p)])

    def test_homonym_requires_complete_distinction(self):
        p="Kael, um ferreiro, encontrou Kael, o estrategista."
        with self.assertRaisesRegex(ValueError,"collision"):
            self.apply(p,new=[self.new("kael-smith","Kael","Personagens",p,identity_resolution={"kind":"DISTINCT_HOMONYM","distinct_from":[],"reason":"incomplete"})])

    def test_two_homonyms_same_episode_not_silently_merged(self):
        p="Kael, o ferreiro, encontrou outro Kael, o mensageiro."
        a=self.new("kael-smith","Kael","Personagens",p,identity_resolution={"kind":"DISTINCT_HOMONYM","distinct_from":["kael-canon"],"reason":"different profession in fixture"})
        b=self.new("kael-messenger","Kael","Personagens",p,identity_resolution={"kind":"DISTINCT_HOMONYM","distinct_from":["kael-canon","kael-smith"],"reason":"explicit second individual in fixture"})
        self.apply(p,new=[a,b])
        self.assertEqual(len(aliases(graph_rows(self.db),"Kael")),3)

    def test_pending_open_resolve_preserve_original_evidence(self):
        p="A origem do viajante continuava desconhecida."
        self.apply(p,[self.ev("PENDING_OPEN","lucas",p,{"pending_id":"p-origin","category":"ATTRIBUTE_UNKNOWN","reason":"origem desconhecida"})])
        self.assertEqual(self.pending("p-origin")[0],"OPEN")
        q="O viajante revelou sua origem."
        self.apply(q,[self.ev("PENDING_RESOLVE","lucas",q,{"pending_id":"p-origin","reason":"origem explicitada no cenário"})])
        self.assertEqual(self.pending("p-origin")[0],"RESOLVED")
        self.assertEqual(self.db.execute("SELECT anchor FROM codex_pending WHERE pending_id='p-origin'").fetchone()[0],p)
        self.assertEqual(self.db.execute("SELECT count(*) FROM codex_events").fetchone()[0],2)

    def test_pending_wrong_subject_rolls_back(self):
        p="Origem desconhecida."
        self.apply(p,[self.ev("PENDING_OPEN","lucas",p,{"pending_id":"p","category":"UNKNOWN","reason":"fixture"})])
        with self.assertRaisesRegex(ValueError,"another entity"):
            self.apply(p,[self.ev("PENDING_RESOLVE","miren",p,{"pending_id":"p","reason":"wrong subject"})])
        self.assertEqual(self.pending("p")[0],"OPEN")

    def test_unresolved_persisted_and_retry_idempotent(self):
        p="Uma viajante não identificada chegou."
        u={"name":"viajante","reason":"identidade desconhecida","line":1,"anchor":p}
        self.assertEqual(self.apply(p,unresolved=[u],ep="x",sequence=1),"APPLIED")
        self.assertEqual(self.apply(p,unresolved=[u],ep="x",sequence=1),"IDEMPOTENT")
        self.assertEqual(self.pending("candidate:x:0")[0],"OPEN")
        self.assertEqual(self.db.execute("SELECT count(*) FROM codex_pending").fetchone()[0],1)

    def test_pending_escalation_stops_repeated_loop(self):
        p="A dúvida permaneceu."
        self.apply(p,[self.ev("PENDING_OPEN","lucas",p,{"pending_id":"p","category":"UNKNOWN","reason":"fixture"})])
        v={"pending_id":"p","reason":"não há nova evidência"}
        self.apply(p,[self.ev("PENDING_ESCALATE","lucas",p,v)])
        with self.assertRaisesRegex(ValueError,"Repeated escalation"):
            self.apply(p,[self.ev("PENDING_ESCALATE","lucas",p,v)])
        self.assertEqual(self.pending("p")[0],"REQUIRES_AUTHOR_REVIEW")

    def test_conflicting_reports_never_choose_death(self):
        self.seed("dragon","Dragão","Bestiário".split("|"));self.db.commit()
        p="Uma carta afirmou que o dragão morreu no dia anterior.\nUm vigia afirmou que o dragão voava no mesmo dia."
        a,b=p.splitlines()
        evs=[self.ev("REPORT","dragon",a,{"field":"life_status","value":"DEAD","reporter":"carta anônima","about_day":579}),self.ev("REPORT","dragon",b,{"field":"life_status","value":"ALIVE","reporter":"vigia","about_day":579},line=2)]
        self.apply(p,evs,ep="reports")
        self.assertIsNone(current(self.db,"dragon","attribute:life_status"))
        self.assertEqual(self.pending("report:reports:1")[0],"REQUIRES_AUTHOR_REVIEW")
        self.assertEqual(self.db.execute("SELECT count(*) FROM codex_events WHERE kind='REPORT'").fetchone()[0],2)

    def test_reports_different_dates_not_automatic_conflict(self):
        p="Um relato indicava vida. Outro relato indicava morte posterior."
        evs=[self.ev("REPORT","lucas",p,{"field":"life_status","value":"ALIVE","reporter":"A","about_day":578}),self.ev("REPORT","lucas",p,{"field":"life_status","value":"DEAD","reporter":"B","about_day":579})]
        self.apply(p,evs)
        self.assertEqual(self.db.execute("SELECT count(*) FROM codex_pending").fetchone()[0],0)

    def test_private_alias_not_in_public_lookup(self):
        p="Um título secreto foi revelado."
        self.apply(p,[self.ev("ALIAS","lucas",p,{"alias":"Título secreto"},scope="BACKSTAGE")])
        self.assertEqual(aliases(graph_rows(self.db),"Título secreto"),[])
        self.assertEqual(len(aliases(graph_rows(self.db,public=False),"Título secreto")),1)

    def test_bad_evidence_no_pending_committed(self):
        p="Texto original."
        e=self.ev("PENDING_OPEN","lucas","Texto inventado.",{"pending_id":"p","category":"UNKNOWN","reason":"fixture"})
        with self.assertRaisesRegex(ValueError,"Literal evidence mismatch"):
            self.apply(p,[e])
        self.assertIsNone(self.pending("p"))

    # Literal historical snippets supplied by the project, projected into scratch DB only.
    def test_canon_tessa_homonym_d519(self):
        p="Não era a mesma Tessa envolvida nos trabalhos modulares de Dorek; tratava-se de uma profissional distinta, conhecida naquele distrito pelo trabalho com moradores de diferentes idades."
        self.seed("tessa-dorek","Tessa",["Personagens"]);self.db.commit()
        n=self.new("tessa-maren","Tessa Maren","Personagens",p,aliases=["Tessa"],identity_resolution={"kind":"DISTINCT_HOMONYM","distinct_from":["tessa-dorek"],"reason":"literal source explicitly distinguishes both"})
        self.apply(p,new=[n],day=519)
        self.assertEqual(len(aliases(graph_rows(self.db),"Tessa")),2)

    def test_canon_hz1_hypothesis_not_origin_d504(self):
        p="Nada permitia ainda atribuir uma data, uma cultura ou uma função."
        n=self.new("hz1-stones","Pedras de HZ-1","Ambientes",p)
        self.apply(p,[self.ev("PENDING_OPEN","hz1-stones",p,{"pending_id":"hz1-origin","category":"ATTRIBUTE_UNKNOWN","reason":"data, cultura e função não confirmadas"},day=504)],new=[n],day=504)
        self.assertEqual(self.pending("hz1-origin")[0],"OPEN")
        self.assertIsNone(current(self.db,"hz1-stones","attribute:origin"))

    def test_canon_argos_not_free_flight_d503(self):
        p="O projeto ainda não possuía voo livre confirmado."
        n=self.new("argos","ARGOS","Tecnologia",p)
        self.apply(p,[self.ev("ATTRIBUTE","argos",p,{"field":"free_flight_confirmed","value":False},day=503)],new=[n],day=503)
        self.assertIs(current(self.db,"argos","attribute:free_flight_confirmed"),False)

    def test_canon_d504_avenue_not_aerun_extension(self):
        p="960 metros de trechos existentes da Grande Avenida haviam sido modernizados e reabertos."
        n=self.new("avenue","Grande Avenida","Ambientes",p)
        self.apply(p,[self.ev("ATTRIBUTE","avenue",p,{"field":"modernized_m","value":960},day=504)],new=[n],day=504)
        self.assertEqual(current(self.db,"avenue","attribute:modernized_m"),960)
        self.assertIsNone(current(self.db,"avenue","attribute:aerun_extension_m"))

    def test_canon_genese_choice_not_nerf_d519(self):
        p="Não era uma lei que restringia GÊNESE."
        self.apply(p,[self.ev("ATTRIBUTE","lucas",p,{"field":"gym_voluntary_nonuse","value":True},day=519)],day=519)
        self.assertIs(current(self.db,"lucas","attribute:gym_voluntary_nonuse"),True)
        self.assertIsNone(current(self.db,"lucas","attribute:power_limit"))

    def test_canon_talis_no_confirmed_location_d495(self):
        p="Não havia confirmação nova do paradeiro de sua irmã."
        n=self.new("talis","Talis","Personagens",p)
        self.apply(p,[self.ev("PENDING_OPEN","talis",p,{"pending_id":"talis-location","category":"LOCATION_UNKNOWN","reason":"paradeiro não confirmado"},day=495)],new=[n],day=495)
        self.assertIsNone(current(self.db,"talis","last_observed_location"))
        self.assertEqual(self.pending("talis-location")[0],"OPEN")

if __name__=="__main__":
    unittest.main()
