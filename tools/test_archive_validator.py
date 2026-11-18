import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from validate_episode_archive import verify_one, ArchiveInvalid, REQUIRED


def blob(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')


class DraftValidation(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name)/'episodes'/'UNIT-TEST-001'/'draft'; self.folder.mkdir(parents=True)
        choices=[{'number':i,'title':f'Escolha de teste {i}',
                  'description':'caminho de teste','is_special':i==4,'is_free':i==5}
                 for i in range(1,6)]
        prose='Uma passagem fictícia para testar a integridade do motor narrativo e sua recuperação integral.\n'
        full=prose+'\n'.join(c['title'] for c in choices)
        metadata={'canon_status':'RASCUNHO','day':10,'hour':'20h42'}
        ev=[{'event_id':'TEST-EVT','canon_status':'PENDENTE'}]
        draft={'delivery_id':'UNIT-TEST-001','prose':prose,'full_text':full,
               'metadata':metadata,'choices':choices,'events':ev,'book_closed':False}
        payloads={'narrativa_integral.md':full.encode('utf-8'),'opcoes.json':blob(choices),
                  'eventos_e_consequencias.json':blob(ev),'checkpoint_candidato.json':blob(metadata),
                  'episode_draft.json':blob(draft)}
        self.manifest={'schema':'worldroot-episode-package-v1','delivery_id':'UNIT-TEST-001',
                       'canon_status':'RASCUNHO','original_readback_sha256':hashlib.sha256(payloads['narrativa_integral.md']).hexdigest(),
                       'artifacts':{n:{'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)} for n,b in payloads.items()}}
        for n,b in payloads.items(): (self.folder/n).write_bytes(b)
        self.update_manifest()
    def update_manifest(self):
        (self.folder/'manifesto_imutavel.json').write_bytes(blob(self.manifest))
    def test_complete_is_valid(self):
        self.assertEqual(verify_one(self.folder/'manifesto_imutavel.json')['episode_id'],'UNIT-TEST-001')
    def test_rejects_modified_literal(self):
        with (self.folder/'narrativa_integral.md').open('ab') as f: f.write(b'CHANGED')
        with self.assertRaises(ArchiveInvalid): verify_one(self.folder/'manifesto_imutavel.json')
    def test_rejects_missing_sidecar(self):
        (self.folder/'opcoes.json').unlink()
        with self.assertRaises(ArchiveInvalid): verify_one(self.folder/'manifesto_imutavel.json')
    def test_rejects_canon_without_approval(self):
        self.manifest['canon_status']='NARRADO';self.update_manifest()
        with self.assertRaises(ArchiveInvalid): verify_one(self.folder/'manifesto_imutavel.json')
    def setup_book_close(self):
        """Create a synthetic author-approved closed-book archive package."""
        root = self.folder.parent.parent.parent
        draft_path = self.folder/'episode_draft.json'
        draft = json.loads(draft_path.read_text(encoding='utf-8'))
        meta = dict(draft['metadata'], book='Livro V')
        draft['metadata'] = meta
        draft['book_closed'] = True
        (self.folder/'checkpoint_candidato.json').write_bytes(blob(meta))
        draft_path.write_bytes(blob(draft))
        for name in ('checkpoint_candidato.json', 'episode_draft.json'):
            bits = (self.folder/name).read_bytes()
            self.manifest['artifacts'][name] = {
                'sha256': hashlib.sha256(bits).hexdigest(),
                'bytes': len(bits)}
        self.update_manifest()
        story_sha = self.manifest['original_readback_sha256']
        previous = 'LV-C16-PIV-D537-AUTHOR-SOURCE'
        ep = self.folder.parent.name
        quote = 'Vamos finalizar o livro, autorizado pelo autor.'
        approval = {
            'schema': 'worldroot-author-book-end-v1', 'episode_id': ep,
            'book': 'Livro V', 'approved': True, 'author_source': 'USER_MESSAGE',
            'author_quote': quote, 'previous_episode_id': previous,
            'choice_path': f'choices/{previous}/option-5.json',
            'new_book_opened': False
        }
        choice = {
            'schema': 'worldroot-author-choice-v1', 'episode_id': previous,
            'option': 5, 'free_text': quote, 'author_source': 'USER_MESSAGE'
        }
        request = {
            'schema': 'worldroot-book-end-request-v1', 'episode_id': ep,
            'previous_episode_id': previous, 'book': 'Livro V',
            'approval_path': f'author-approvals/{ep}.json',
            'archived_story_sha256': story_sha, 'new_book_opened': False
        }
        journal = {
            'episode_id': ep, 'previous_episode_id': previous, 'book_closed': True,
            'status': 'FECHADO_GITHUB', 'story_sha256': story_sha,
            'metadata': {'book': 'Livro V'}
        }
        for relpath, body in (
                (f'author-approvals/{ep}.json', approval),
                (f'choices/{previous}/option-5.json', choice),
                ('canon/BOOK_END_REQUEST.json', request),
                (f'canon/episodes/{ep}.json', journal)):
            target = root/relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(blob(body))
        return root

    def test_book_closure_requires_real_evidence(self):
        root = self.setup_book_close()
        self.assertEqual(
            verify_one(self.folder/'manifesto_imutavel.json')['episode_id'],
            self.folder.parent.name)
        (root/'canon'/'BOOK_END_REQUEST.json').unlink()
        with self.assertRaises(ArchiveInvalid):
            verify_one(self.folder/'manifesto_imutavel.json')

    def test_book_closure_rejects_mismatched_approval(self):
        root = self.setup_book_close()
        approval = root/'author-approvals'/(self.folder.parent.name+'.json')
        data = json.loads(approval.read_text(encoding='utf-8'))
        data['author_quote'] = 'Texto alterado e não aprovado.'
        approval.write_bytes(blob(data))
        with self.assertRaises(ArchiveInvalid):
            verify_one(self.folder/'manifesto_imutavel.json')

    def test_rejects_wrong_option_number(self):
        file=self.folder/'opcoes.json'
        data=json.loads(file.read_text());data[1]['number']=3
        file.write_bytes(blob(data))
        self.manifest['artifacts']['opcoes.json']['sha256']=hashlib.sha256(file.read_bytes()).hexdigest()
        self.manifest['artifacts']['opcoes.json']['bytes']=file.stat().st_size
        self.update_manifest()
        with self.assertRaises(ArchiveInvalid): verify_one(self.folder/'manifesto_imutavel.json')

if __name__=='__main__': unittest.main()
