"""Synthetic regression scenarios; never import private chapter material."""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace
from worldroot.memory import NarrativeMemory
from worldroot.narrative import Choice
from worldroot.story_qa import Scene, FactUsage, Generation, validate_generation, clock_minutes
from worldroot.ledger import GateError


def choices():
    return (Choice(1,'Investigate','Advantage and downside'),
            Choice(2,'Discuss','Change the pace'),
            Choice(3,'Explore','Learn more'),
            Choice(4,'SPECIAL','Wider view, uncertain result',is_special=True),
            Choice(5,'Free action','',is_free=True))


def sample():
    return Generation(generation_id='QA-SYNTH-0001',book='LIVRO V',chapter=15,part='II',
          status='SIMULADO',last_canon_day=528,last_canon_clock='23h06',
          scenes=(Scene('S1',529,'06h41','HOUSE','Morning dialogue.'),
                  Scene('S2',529,'13h18','GALLERY','No instant world news.'),
                  Scene('S3',529,'21h07','HOUSE','An intimate close.')),
          choices=choices(),closing_text='FIM DA PARTE — SIMULAÇÃO NÃO CANÔNICA',
          min_scenes=3,forbidden_markers=('OTHER_UNIVERSE',))


class SampleRegressionTest(unittest.TestCase):
    def test_three_scene_dawn_midday_night(self):
        r=validate_generation(sample());self.assertTrue(r['ok'],r)
        self.assertEqual(r['scene_count'],3)
        self.assertEqual(r['save_label'],'SALVAMENTO EXTERNO PENDENTE')
    def test_open_book_cannot_end(self):
        x=replace(sample(),closing_text='FIM DO LIVRO V — SIMULAÇÃO')
        self.assertFalse(validate_generation(x)['ok'])
    def test_book_close_requires_author_approval(self):
        x=replace(sample(),book_closed=True,closing_text='FIM DO LIVRO V',author_approved=False)
        self.assertFalse(validate_generation(x)['ok'])
    def test_clock_reverse(self):
        x=sample();scenes=list(x.scenes);scenes[1]=replace(scenes[1],hour='04h08')
        self.assertFalse(validate_generation(replace(x,scenes=tuple(scenes)))['ok'])
    def test_invalid_clock(self):
        x=sample();scenes=list(x.scenes);scenes[0]=replace(scenes[0],hour='29h92')
        self.assertFalse(validate_generation(replace(x,scenes=tuple(scenes)))['ok'])
    def test_future_unauthorized_narration(self):
        self.assertFalse(validate_generation(replace(sample(),status='NARRADO',author_approved=False))['ok'])
    def test_foreign_universe_leak(self):
        x=sample();scenes=list(x.scenes);scenes[1]=replace(scenes[1],prose='Fiction from OTHER_UNIVERSE')
        self.assertFalse(validate_generation(replace(x,scenes=tuple(scenes)))['ok'])
    def test_fake_storage_badge(self):
        x=sample();scenes=list(x.scenes);scenes[2]=replace(scenes[2],prose='Continuidade registrada e conferida no Google Drive.')
        self.assertFalse(validate_generation(replace(x,scenes=tuple(scenes)))['ok'])
    def test_fake_external_receipt(self):
        x=replace(sample(),external_receipt={'verification':'google_drive_get_media','file_id':'fake'})
        self.assertFalse(validate_generation(x)['ok'])
    def test_invalid_choice_order(self):
        x=replace(sample(),choices=choices()[:4])
        self.assertFalse(validate_generation(x)['ok'])
    def test_missing_scene(self):
        x=replace(sample(),scenes=sample().scenes[:1])
        self.assertFalse(validate_generation(x)['ok'])
    def test_duplicate_scene_id(self):
        x=sample();scenes=list(x.scenes);scenes[2]=replace(scenes[2],scene_id='S1')
        self.assertFalse(validate_generation(replace(x,scenes=tuple(scenes)))['ok'])
    def test_previous_checkpoint_not_overwritten(self):
        x=sample();scenes=list(x.scenes);scenes[0]=replace(scenes[0],day=528,hour='23h05')
        self.assertFalse(validate_generation(replace(x,scenes=tuple(scenes)))['ok'])


class MinuteKnowledgeTest(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.memory=NarrativeMemory(Path(tmp.name)/'memory.sqlite')
        self.memory.register_person('ACTOR-X','Person X')
        self.memory.register_person('ACTOR-Y','Person Y')
        self.memory.add_fact(fact_id='FACT-X',subject_id='ACTOR-X',predicate='observed',value={'x':1},
                 day=529,minute=1180,source_id='SYNTHETIC',source_line=8,visibility='BASTIDORES',
                 status='NARRADO',semantic_review=True)
    def test_knowledge_follows_message_delay(self):
        m=self.memory
        m.learn(person_id='ACTOR-Y',fact_id='FACT-X',learned_day=529,learned_minute=1210,
                channel='messenger',source_id='SYNTHETIC',line=9,confirmed=True)
        self.assertEqual(m.known_by('ACTOR-Y',529,1209),[])
        self.assertEqual(len(m.known_by('ACTOR-Y',529,1210)),1)
        self.assertEqual(m.viewed_by_reader(529,1179),[])
        self.assertEqual(len(m.viewed_by_reader(529,1180)),1)
    def test_same_day_early_leak_fails_in_generation(self):
        m=self.memory
        m.learn(person_id='ACTOR-Y',fact_id='FACT-X',learned_day=529,learned_minute=1210,
                channel='messenger',source_id='SYNTHETIC',line=9,confirmed=True)
        x=sample();scenes=list(x.scenes)
        scenes[2]=replace(scenes[2],hour='20h00',claimed_knowledge=(FactUsage('FACT-X','ACTOR-Y'),))
        self.assertFalse(validate_generation(replace(x,scenes=tuple(scenes)),memory=m)['ok'])
        scenes[2]=replace(scenes[2],hour='20h30',claimed_knowledge=(FactUsage('FACT-X','ACTOR-Y'),))
        self.assertTrue(validate_generation(replace(x,scenes=tuple(scenes)),memory=m)['ok'])
    def test_same_day_unknown_time_is_conservative(self):
        self.memory.learn(person_id='ACTOR-Y',fact_id='FACT-X',learned_day=529,
                channel='unknown delivery time',source_id='SYNTHETIC',line=9,confirmed=True)
        self.assertEqual(self.memory.known_by('ACTOR-Y',529,1439),[])
        self.assertEqual(len(self.memory.known_by('ACTOR-Y',530,0)),1)
    def test_knowledge_cannot_predate_fact(self):
        with self.assertRaises(GateError):
            self.memory.learn(person_id='ACTOR-Y',fact_id='FACT-X',learned_day=529,learned_minute=1179,
                channel='letter',source_id='SYNTHETIC',line=9,confirmed=True)
    def test_reader_can_know_but_character_cannot(self):
        x=sample();scenes=list(x.scenes)
        scenes[2]=replace(scenes[2],claimed_knowledge=(FactUsage('FACT-X','ACTOR-Y'),))
        self.assertFalse(validate_generation(replace(x,scenes=tuple(scenes)),memory=self.memory)['ok'])
    def test_no_fabricated_future_hour(self):
        with self.assertRaises(ValueError):clock_minutes('26h99')

if __name__ == '__main__': unittest.main()
