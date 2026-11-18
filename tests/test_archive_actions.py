"""Synthetic tests; no live Google credentials and no user's story data."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from worldroot.archive_actions import ALL_FILES,mirror_archive
from worldroot.ledger import GateError


def j(a):return (json.dumps(a,sort_keys=True,ensure_ascii=False,separators=(',',':'))+'\n').encode()

class FakePublisher:
    def __init__(self):self.store={};self.calls=0
    def sync_file(self,artifact_id,filename,blob):
        self.calls+=1
        old=self.store.setdefault(artifact_id,blob)
        if old!=blob:raise GateError('conflict')
        return {'verification':'google_drive_get_media','file_id':artifact_id,
                'sha256':hashlib.sha256(blob).hexdigest(),'bytes':len(blob)}

class MirrorTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)
        tools=self.root/'tools';tools.mkdir()
        # The complete package validator has its own regression suite on
        # story-archive; this fixture exercises only the mirror contract.
        (tools/'validate_episode_archive.py').write_text(
            'def verify_tree(root):\n    return []\n', encoding='utf-8')

    def test_reject_folder_url(self):
        with self.assertRaises(GateError):mirror_archive(self.root,'https://google.com',FakePublisher())

    def test_refuse_missing_manifest(self):
        with self.assertRaises(GateError):mirror_archive(self.root,'TEST-FOLDER-ID',FakePublisher())

if __name__=='__main__': unittest.main()
