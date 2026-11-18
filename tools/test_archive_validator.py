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
    def test_rejects_wrong_option_number(self):
        file=self.folder/'opcoes.json'
        data=json.loads(file.read_text());data[1]['number']=3
        file.write_bytes(blob(data))
        self.manifest['artifacts']['opcoes.json']['sha256']=hashlib.sha256(file.read_bytes()).hexdigest()
        self.manifest['artifacts']['opcoes.json']['bytes']=file.stat().st_size
        self.update_manifest()
        with self.assertRaises(ArchiveInvalid): verify_one(self.folder/'manifesto_imutavel.json')

if __name__=='__main__': unittest.main()
