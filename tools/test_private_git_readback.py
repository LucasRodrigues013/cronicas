"""Regression for GitHub-only private remote SHA readback (no token leakage)."""
from __future__ import annotations
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
WORKFLOWS=(
    ".github/workflows/git-canon-cycle.yml",
    ".github/workflows/worldroot-draft-inbox.yml",
    ".github/workflows/worldroot-three-cycle-bootstrap.yml",
)

class AuthenticatedReadbackTests(unittest.TestCase):
    def test_every_private_ref_readback_is_authenticated(self):
        total=0
        for filename in WORKFLOWS:
            content=(ROOT/filename).read_text(encoding="utf-8")
            lines=content.splitlines()
            fetch_lines=[i for i,line in enumerate(lines)
                         if "fetch -q origin refs/heads/story-archive:" in line]
            self.assertTrue(fetch_lines,filename)
            for i in fetch_lines:
                total+=1
                self.assertIn('http.extraheader=AUTHORIZATION: basic $auth_header',lines[i],filename)
                context="\n".join(lines[max(0,i-5):i])
                self.assertIn("push origin HEAD:refs/heads/story-archive",context,filename)
                self.assertNotIn("unset auth_header",context,filename)
                self.assertIn("unset auth_header","\n".join(lines[i+1:i+4]),filename)
        self.assertEqual(total,4)

    def test_single_story_writer_concurrency_group(self):
        groups=[]
        for filename in WORKFLOWS:
            content=(ROOT/filename).read_text(encoding="utf-8")
            self.assertIn("cancel-in-progress: false",content,filename)
            self.assertIn("group: worldroot-story-write",content,filename)
            groups.append(content)
        self.assertEqual(len(groups),3)

if __name__=="__main__":
    unittest.main()
