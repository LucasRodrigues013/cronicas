"""Mutation checks: deliberately restore each specific defect in a disposable copy."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
MUTATIONS=[
("semantic_queue.py",'    if not isinstance(job,dict) or job.get("schema")!=SCHEMA or job.get("job_id")!=seal({k:v for k,v in job.items() if k!="job_id"}):raise ValueError("Invalid semantic job seal")\n',"","test_sealed_job"),
("semantic_queue.py",'("context","source_sha256","source_status","day","anchor")','("context","source_sha256")',"test_conflicting_group"),
("r36_benchmark.py",'bool(x) and x==x.strip()','bool(x.strip())',"test_metadata_whitespace"),
("r36_experiment.py",' and a[k]["author_total"]==b[k]["author_total"]','',"test_paired_author_denominator"),
]
class OmegaMutationTests(unittest.TestCase):
    def test_four_targeted_mutants(self):
        for filename,needle,replacement,method in MUTATIONS:
            with self.subTest(mutation=method),tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                shutil.copytree(ROOT/"worldroot",root/"worldroot",ignore=shutil.ignore_patterns("__pycache__"))
                shutil.copy2(ROOT/"tests/test_omega_cycle1.py",root/"test_omega_cycle1.py")
                path=root/"worldroot"/filename
                source=path.read_text(encoding="utf-8")
                self.assertEqual(source.count(needle),1)
                path.write_text(source.replace(needle,replacement),encoding="utf-8")
                env={**os.environ,"PYTHONPATH":str(root)}
                run=subprocess.run([sys.executable,"-m","unittest","test_omega_cycle1.OmegaRegression."+method],cwd=root,env=env,capture_output=True,text=True,timeout=15)
                self.assertEqual(run.returncode,1,run.stderr)
                self.assertIn("FAIL:",run.stderr)
                self.assertIn("AssertionError: ValueError not raised",run.stderr)
                self.assertNotIn("ERROR:",run.stderr)
                self.assertNotIn("ImportError",run.stderr)
