import unittest
from worldroot.omega_turbo_v3 import prepare_one


class Cache:
    def __init__(self):
        self.lines = ['## Response:'] + ['Gênese']*10 + ['## Prompt:', 'Opção 4', '## Response:', 'Fim']
        self.roles = ['Response']*11 + ['Prompt']*2 + ['Response']*2
    def get(self, name):
        return self.lines, self.roles, (), 'source-hash'


class Tests(unittest.TestCase):
    def setUp(self):
        self.c = Cache()
        self.m = dict(id='a', source='s', start=1, end=15, lines=15, unit_seal='official')
    def plan(self):
        return prepare_one(self.c, self.m, 1, target=8, dense_target=3, context=2)
    def test_coverage_and_role(self):
        p = self.plan()
        self.assertEqual([n for u in p['units'] for n in range(u['start'], u['end']+1)], list(range(1,16)))
        self.assertTrue(all(self.c.roles[u['start']-1:u['end']].count(u['role']) == u['end']-u['start']+1 for u in p['units']))
    def test_dense_and_stable_ids(self):
        a,b = self.plan(),self.plan()
        self.assertEqual(a['units'], b['units'])
        self.assertTrue(any(u['risk_hint']=='dense' and u['end']-u['start']+1<=3 for u in a['units']))
        self.assertEqual(a['official_unit_seal'], 'official')
    def test_context_isolation(self):
        for u in self.plan()['units']:
            self.assertTrue(all(r == u['role'] for r in self.c.roles[u['context_start']-1:u['context_end']]))
    def test_cursor_and_bounds(self):
        for m,c in [(self.m,2),(dict(self.m,end=16,lines=16),1),(dict(self.m,lines=14),1)]:
            with self.assertRaises(ValueError):
                prepare_one(self.c,m,c)
    def test_no_authority(self):
        p=self.plan()
        self.assertFalse(p['canon_changed'] or p['promotion'] or p['semantic_certification'])


if __name__=='__main__': unittest.main()
