import unittest
from worldroot.narrative import Choice, validate_interface
class VoiceLintTest(unittest.TestCase):
 def choices(self):
  return [Choice(i,f'{i}',f'Route {i}',is_special=i==4,is_free=i==5) for i in range(1,6)]
 def test_bare_dash_warns_without_hard_failure(self):
  r=validate_interface(prose='Scene\n— Bare dialogue without speaker name.',book_closed=False,chapter=1,part='I',choices=self.choices(),actual_save_receipt=None)
  self.assertTrue(r['ok'])
  self.assertTrue(any('unlabeled dialogue' in x for x in r['notices']))
 def test_named_dialogue_is_not_flagged(self):
  r=validate_interface(prose='Scene\nMIREN — A natural dialogue sentence.',book_closed=False,chapter=1,part='I',choices=self.choices(),actual_save_receipt=None)
  self.assertFalse(any('unlabeled dialogue' in x for x in r['notices']))
if __name__=='__main__':unittest.main()
