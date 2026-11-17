import tempfile
import unittest
from pathlib import Path
from worldroot.memory import NarrativeMemory
from worldroot.narrative import Choice,validate_interface,narrator_policy
from worldroot.backup import backup_and_verify
from worldroot.ledger import GateError,ConflictError,WorldrootStore

class MemoryTest(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name)
  self.db=NarrativeMemory(self.root/'private'/'memory.sqlite')
  self.db.register_person('CHAR_A','Personagem A')
  self.db.register_person('CHAR_B','Personagem B')
 def direct_fact(self,day=12,visibility='BASTIDORES',status='NARRADO',review=True):
  return self.db.add_fact(fact_id='FACT-0001',subject_id='CHAR_A',predicate='discovered',value={'object':'new place'},
           day=day,source_id='TXT-PRIMARY',source_line=42,visibility=visibility,status=status,semantic_review=review)
 def test_unknown_until_evidence_transfer(self):
  self.direct_fact()
  self.assertEqual(self.db.known_by('CHAR_B',14),[])
  self.db.learn(person_id='CHAR_B',fact_id='FACT-0001',learned_day=16,channel='confirmed messenger',source_id='TXT-PRIMARY',line=88,confirmed=True)
  self.assertEqual(self.db.known_by('CHAR_B',14),[])
  self.assertEqual(len(self.db.known_by('CHAR_B',16)),1)
 def test_offstage_reader_sees_without_characters_knowing(self):
  self.direct_fact()
  self.assertEqual(len(self.db.viewed_by_reader(12)),1)
  self.assertEqual(self.db.known_by('CHAR_B',100),[])
 def test_facts_cannot_have_unreviewed_narrated(self):
  with self.assertRaises(GateError):self.direct_fact(review=False)
 def test_planned_fact_not_canon_or_public(self):
  self.direct_fact(status='PLANEJADO',review=False,visibility='PUBLICO')
  self.assertFalse(self.db.can_publish_public('FACT-0001'))
  with self.assertRaises(GateError):self.db.learn(person_id='CHAR_B',fact_id='FACT-0001',learned_day=15,channel='letter',source_id='TXT-PRIMARY',line=95,confirmed=True)
 def test_future_learning_forbidden(self):
  self.direct_fact(day=15)
  with self.assertRaises(GateError):self.db.learn(person_id='CHAR_A',fact_id='FACT-0001',learned_day=14,channel='messenger',source_id='TXT-PRIMARY',line=99,confirmed=True)
 def test_evidence_missing_forbidden(self):
  with self.assertRaises(ValueError):self.db.add_fact(fact_id='FACT-0001',subject_id='CHAR_A',predicate='x',value='x',day=15,source_id='',source_line=0)
 def test_rename_identity_forbidden(self):
  with self.assertRaises(ConflictError):self.db.register_person('CHAR_A','Other')
 def test_alias_candidates_not_merged(self):
  self.db.propose_alias('CHAR_A','Alias', 'S01:55')
  self.db.propose_alias('CHAR_B','Alias', 'S02:66')
  self.assertEqual(self.db.summary()['entities']['CANDIDATE'],2)
 def test_relationship_requires_review_for_canon(self):
  with self.assertRaises(GateError):
   self.db.record_relationship(relation_event_id='REL-01',from_id='CHAR_A',to_id='CHAR_B',relation='allies',state='active',since_day=14,source_id='TXT',source_line=12,canon_status='NARRADO',reviewed=False)
 def test_staged_relationship_not_character_fact(self):
  self.db.record_relationship(relation_event_id='REL-01',from_id='CHAR_A',to_id='CHAR_B',relation='allies',state='proposed',since_day=14,source_id='TXT',source_line=12)
  self.assertEqual(self.db.relationship_state('CHAR_A',528),[])
 def test_thread_hypothesis_cannot_auto_canonize(self):
  self.db.open_thread(thread_id='HYP-001',kind='MYSTERY',title='Unproven theory',status='PLANEJADO',hypotheses={'not_canon':True})
  with self.assertRaises(ConflictError):self.db.open_thread(thread_id='HYP-001',kind='MYSTERY',title='Unproven theory',status='NARRADO',source_id='TXT')
 def test_future_day_can_be_staged_without_story_generation(self):
  # Engine must remain usable after the last audited day without pre-narrating it.
  self.db.add_fact(fact_id='FACT-FUTURE',subject_id='CHAR_A',predicate='hypothesis',value='not narrated',day=529,source_id='SYNTHETIC_ONLY',source_line=1,status='PLANEJADO',semantic_review=False)
  self.assertEqual(self.db.viewed_by_reader(529),[])
  self.db.stage_chronology([{'day':529,'kind':'NAO_CERTIFICADO','note':'future checkpoint not yet narrated'}])
  self.assertEqual(self.db.summary()['days']['NAO_CERTIFICADO'],1)
 def test_reviewed_public_only(self):
  self.direct_fact(visibility='PUBLICO')
  self.assertTrue(self.db.can_publish_public('FACT-0001'))
 def test_chronology_stage(self):
  self.db.stage_chronology([{'day':1,'kind':'HEADER','anchor':'S01:5'}, {'day':2,'kind':'ELIPSE','review_state':'PENDENTE'}])
  self.assertEqual(self.db.summary()['days'],{'ELIPSE':1,'HEADER':1})
 def test_backup_restore_memory(self):
  self.direct_fact();m=backup_and_verify(self.db.path,self.root/'backup.sqlite')
  self.assertEqual(m['restored_integrity'],'ok')
  self.assertGreater(m['bytes'],0)

class NarrativeTest(unittest.TestCase):
 def choices(self):
  return [Choice(1,'Option 1','One'),Choice(2,'Option 2','Two'),Choice(3,'Option 3','Three'),
          Choice(4,'SPECIAL','Four',is_special=True),Choice(5,'Free action','',is_free=True)]
 def run_check(self,**kwargs):
  return validate_interface(prose='Synthetic narrative without spoilers.',book_closed=False,chapter=15,part='I',
                             choices=self.choices(),actual_save_receipt=None,**kwargs)
 def test_five_usable_choices(self):self.assertTrue(self.run_check()['ok'])
 def test_book_end_wrong_label_rejected(self):
  r=validate_interface(prose='FIM DO LIVRO V',book_closed=False,chapter=15,part='I',choices=self.choices(),actual_save_receipt=None)
  self.assertFalse(r['ok'])
 def test_no_saved_claim_without_receipt(self):self.assertEqual(self.run_check()['save_label'],'SALVAMENTO EXTERNO PENDENTE')
 def test_forged_save_receipt_rejected(self):
  r=validate_interface(prose='scene',book_closed=False,chapter=15,part='I',choices=self.choices(),actual_save_receipt={'verified':True,'file_id':'fake'})
  self.assertFalse(r['ok'])
 def test_invalid_choice_count_rejected(self):
  r=validate_interface(prose='scene',book_closed=False,chapter=15,part='I',choices=self.choices()[:4],actual_save_receipt=None)
  self.assertFalse(r['ok'])
 def test_no_arbitrary_nerf_policy(self):self.assertTrue(narrator_policy()['antagonists']['no_genesis_nerf'])
 def test_nonmechanical_mystery(self):self.assertTrue(narrator_policy()['mystery']['do_not_force_every_scene'])
 def test_backup_restore_ledger(self):
  with tempfile.TemporaryDirectory() as t:
   store=WorldrootStore(Path(t))
   m=backup_and_verify(store.db_path,Path(t)/'backup.sqlite')
   self.assertEqual(m['restored_integrity'],'ok')

if __name__=='__main__':unittest.main()
