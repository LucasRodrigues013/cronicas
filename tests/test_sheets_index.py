import json
import unittest
from worldroot.sheets_index import GoogleSheetsEpisodeIndex,HEADERS
from worldroot.ledger import GateError,ConflictError

class Result:
    def __init__(self,fn):self.fn=fn
    def execute(self):return self.fn()

class FakeSheetsAPI:
    def __init__(self):self.title=None;self.rows=[];self.appends=0;self.tamper=False
    def spreadsheets(self):return self
    def values(self):return self
    def get(self,spreadsheetId,**kwargs):
        if 'range' in kwargs:
            return Result(lambda:{'values': ([list(r) for r in self.rows[:-1]] + [self.rows[-1][:-1]+['TAMPERED']] if self.tamper and self.rows else [list(r) for r in self.rows])})
        return Result(lambda:{'spreadsheetId':spreadsheetId,'sheets':[{'properties':{'title':self.title}}] if self.title else []})
    def batchUpdate(self,spreadsheetId,body):
        return Result(lambda:self._add(body['requests'][0]['addSheet']['properties']['title']))
    def _add(self,title):self.title=title;return {'spreadsheetId':'fake'}
    def update(self,spreadsheetId,range,valueInputOption,body):
        return Result(lambda:self._set_header(body['values'][0]))
    def _set_header(self,row):self.rows=[list(row)];return {'updatedCells':len(row)}
    def append(self,spreadsheetId,range,valueInputOption,insertDataOption,body):
        return Result(lambda:self._append(body['values'][0]))
    def _append(self,row):self.rows.append(list(row));self.appends+=1;return {'updates':{'updatedRows':1}}

class SheetTest(unittest.TestCase):
    def setUp(self):
        self.api=FakeSheetsAPI();self.index=GoogleSheetsEpisodeIndex(self.api,'SYNTH-SHEET')
        self.manifest={'original_readback_sha256':'1'*64}
        self.sidecars={'meta':{'verification':'google_drive_get_media','file_id':'SYNTHETIC-DRIVE-ID'}}
    def test_append_and_readback(self):
        p=self.index.record('SYNTH-EVENT-001',self.manifest,self.sidecars)
        self.assertTrue(p['verified']);self.assertEqual(self.api.rows[0],HEADERS)
    def test_idempotent(self):
        self.index.record('SYNTH-EVENT-001',self.manifest,self.sidecars)
        self.index.record('SYNTH-EVENT-001',self.manifest,self.sidecars)
        self.assertEqual(self.api.appends,1)
    def test_forbid_unverified_sidecars(self):
        with self.assertRaises(GateError):self.index.record('SYNTH-EVENT-001',self.manifest,{'bad':{'file_id':'x'}})
    def test_wrong_hash_conflict(self):
        self.index.record('SYNTH-EVENT-001',self.manifest,self.sidecars)
        with self.assertRaises(ConflictError):self.index.record('SYNTH-EVENT-001',{'original_readback_sha256':'2'*64},self.sidecars)
    def test_readback_mutation_blocked(self):
        self.index.record('SYNTH-EVENT-001',self.manifest,self.sidecars)
        self.api.tamper=True
        with self.assertRaises(ConflictError):self.index.record('SYNTH-EVENT-001',self.manifest,self.sidecars)

if __name__=='__main__':unittest.main()
