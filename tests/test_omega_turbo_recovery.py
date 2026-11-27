import copy
import tempfile
import unittest
from pathlib import Path
from worldroot.omega_turbo_recovery import SourceCache, anchor, digest, git_blob, prepare_pair, validate_receipt

class TurboTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name);self.raw='## Response:\nAção\nLira\n## Prompt:\nEscolho 4\n## Response:\nFim'.encode()
        cut=self.raw.index('ç'.encode())+1;parts=[self.raw[:cut],self.raw[cut:]]
        meta=[]
        for i,part in enumerate(parts):
            name=f'p{i}';(root/name).write_bytes(part);meta.append(dict(path=name,bytes=len(part),git_blob_sha1=git_blob(part)))
        self.manifest=dict(sources=[dict(source_name='s',sha256=digest(self.raw),utf8_bytes=len(self.raw),parts=meta)])
        self.cache=SourceCache(root,self.manifest);self.src=self.cache.get('s')
        self.a=dict(id='a',start=2,end=3,lines=2,source='s');self.b=dict(id='b',start=4,end=7,lines=4,source='s',previous_macro='a')
        blobs=[x['git_blob_sha1'] for x in meta]
        e=dict(source='s',source_sha256_manifest=self.src[3],blob_sha1=blobs[0],blob_sha1_parts=blobs,line_start=2,line_end=3,role='Response',span_sha256_utf8=anchor(self.src,2,3))
        self.r=dict(project='p',archive_pin='pin',macro_id='a',range=[2,3],next_line=4,source='s',source_sha256=self.src[3],canon_changed=False,semantic_certification=False,records=[dict(id='r',promotion=False,evidence=e,axes=[4],visibility='EDITORIAL_ONLY_NO_CHARACTER_INJECTION',authority='HISTORICAL_RESPONSE_NOT_CANON_CERTIFIED',type='character')],coverage=[dict(start=2,end=3,role='Response',span_sha256_utf8=anchor(self.src,2,3),record_ids=['r'])],axis_coverage=dict(assessed=list(range(1,31)),represented=[4]))
    def check(self,r):return validate_receipt(r,self.a,self.src,'p','pin')
    def test_cache_and_split_utf8(self):
        self.assertEqual(self.src[0][1],'Ação');self.assertIs(self.src,self.cache.get('s'));self.assertEqual(self.cache.loads,1)
    def test_pair(self):
        p=prepare_pair(self.cache,[self.a,self.b],2);self.assertEqual(sum(x['lines'] for x in p),6);self.assertEqual(len(p[1]['units']),2);self.assertEqual(self.cache.loads,1)
    def test_valid_open_response(self):self.assertEqual(self.check(self.r)['records'],1)
    def test_invalid_receipts(self):
        mutations=[lambda r:r.update(canon_changed=True),lambda r:r['records'][0]['evidence'].update(span_sha256_utf8='bad'),lambda r:r['records'][0]['evidence'].update(role='Prompt'),lambda r:r['records'][0]['evidence'].pop('blob_sha1_parts'),lambda r:r['coverage'][0].update(start=3),lambda r:r['axis_coverage'].update(represented=[6]),lambda r:r['records'][0].update(type='reader-perspectives'),lambda r:r['records'].append(copy.deepcopy(r['records'][0]))]
        for mutate in mutations:
            r=copy.deepcopy(self.r);mutate(r)
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):self.check(r)
    def test_bad_chain(self):
        with self.assertRaises(ValueError):prepare_pair(self.cache,[self.a,dict(self.b,previous_macro='wrong')],2)
    def test_bad_source(self):
        Path(self.tmp.name,'p0').write_bytes(b'changed')
        with self.assertRaises(ValueError):SourceCache(self.tmp.name,self.manifest).get('s')

if __name__=='__main__':unittest.main()
