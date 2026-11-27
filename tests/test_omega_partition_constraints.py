"""Synthetic regression: known cases and all connected neighbors stay in development."""
import hashlib
import unittest

from worldroot.r36_benchmark import TARGETS
from worldroot.r36_partition import feasibility


def cases(n=60):
    categories=[name for name,count in TARGETS.items() for _ in range(count)]
    return [dict(id=f"case-{i}",category=categories[i],family=f"family-{i}",
                 episodes=[f"episode-{i}"],entities=[f"entity-{i}"],
                 source_pins=[hashlib.sha256(str(i).encode()).hexdigest()],
                 severity="major") for i in range(n)]


class FixedDevelopmentPartition(unittest.TestCase):
    def test_legacy_and_exact_capacity(self):
        rows=cases()
        self.assertTrue(feasibility(rows)["exact_60_feasible"])
        self.assertEqual(feasibility(rows),feasibility(rows,development_ids=[]))
        self.assertTrue(feasibility(rows,development_ids=[r["id"] for r in rows[:36]])["exact_60_feasible"])
        blocked=feasibility(rows,development_ids=[r["id"] for r in rows[:37]])
        self.assertFalse(blocked["capacity_feasible"])
        self.assertFalse(blocked["exact_60_feasible"])

    def test_transitive_development_component(self):
        rows=cases(37)
        # One fixed case links through two different dimensions.
        rows[35]["entities"]=rows[34]["entities"][:]
        rows[36]["episodes"]=rows[35]["episodes"][:]
        fixed=[r["id"] for r in rows[:35]]
        self.assertTrue(feasibility(rows)["capacity_feasible"])
        blocked=feasibility(rows,development_ids=fixed)
        self.assertEqual(blocked["component_sizes"][0],3)
        self.assertFalse(blocked["capacity_feasible"])

    def test_unknown_duplicate_and_invalid_fixed_ids(self):
        rows=cases(2)
        for bad in (["missing"],["case-0","case-0"],[" case-0"],[1],"case-0"):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                feasibility(rows,development_ids=bad)

    def test_partial_not_certification(self):
        result=feasibility(cases(3),development_ids=["case-0"])
        self.assertTrue(result["capacity_feasible"])
        self.assertFalse(result["complete"])
        self.assertFalse(result["exact_60_feasible"])
        self.assertFalse(result["semantic_certification"])
