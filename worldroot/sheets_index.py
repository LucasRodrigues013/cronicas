"""Google Sheets episode pointer index with readback, for Drive-authoritative canon.

This is NOT a multi-service atomic transaction. Operate with one trusted writer;
if the HEAD update fails the previous canonical HEAD remains authoritative.
"""
from __future__ import annotations
import json
from .ledger import GateError, ConflictError, digest

HEADERS=['episode_id','sha256','day','book','chapter','part','hour','drive_folder_manifest','status']

class GoogleSheetsEpisodeIndex:
    def __init__(self, service, spreadsheet_id: str, tab: str = 'WR_EPISODES_CANON'):
        self.service, self.spreadsheet_id, self.tab = service, spreadsheet_id, tab
        if not tab or any(ch in tab for ch in "!'\\"):
            raise ValueError('Unsupported tab name')

    @classmethod
    def from_adc(cls, spreadsheet_id: str, tab: str = 'WR_EPISODES_CANON'):
        try:
            import google.auth
            from googleapiclient.discovery import build
        except ImportError as e:
            raise RuntimeError('Install: pip install .[drive]') from e
        creds,_=google.auth.default(scopes=['https://www.googleapis.com/auth/spreadsheets'])
        if not creds:raise RuntimeError('Google Sheets ADC unavailable')
        return cls(build('sheets','v4',credentials=creds,cache_discovery=False),spreadsheet_id,tab)

    def _rows(self):
        r=self.service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id,
                range=f"'{self.tab}'!A1:I10000", valueRenderOption='UNFORMATTED_VALUE').execute()
        return r.get('values',[])

    def _ensure_sheet(self):
        meta=self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id,
                         fields='spreadsheetId,sheets(properties(title))').execute()
        if not any(s.get('properties',{}).get('title')==self.tab for s in meta.get('sheets',[])):
            self.service.spreadsheets().batchUpdate(spreadsheetId=self.spreadsheet_id,body={
                 'requests':[{'addSheet':{'properties':{'title':self.tab}}}]}).execute()
        rows=self._rows()
        if not rows:
            self.service.spreadsheets().values().update(spreadsheetId=self.spreadsheet_id,
                range=f"'{self.tab}'!A1:I1",valueInputOption='RAW',body={'values':[HEADERS]}).execute()
            rows=self._rows()
        if not rows or rows[0][:len(HEADERS)]!=HEADERS:
            raise GateError('Native Sheet has unexpected header schema')

    def record(self, delivery_id: str, manifest: dict, sidecars: dict):
        self._ensure_sheet()
        # Complete, independently checked Drive sidecars are required.
        if not sidecars or not all(x.get('verification')=='google_drive_get_media'
                    for x in sidecars.values()):
            raise GateError('Base/Atlas cannot record unverified Drive sidecars')
        # The canonical delivery ID is the ID in the append-only ledger.
        sha=manifest.get('original_readback_sha256')
        if not sha or len(sha)!=64:raise GateError('Invalid literal SHA256 in manifest')
        # The record is a pointer only. Detailed facts remain in the private
        # episode JSON sidecars, and must be separately materialized/reviewed.
        row=[delivery_id,sha,'','','','','',
             json.dumps({k:v['file_id'] for k,v in sidecars.items()},sort_keys=True), 'CONFIRMADO']
        before=self._rows()
        matches=[r for r in before[1:] if r and r[0]==delivery_id]
        if matches:
            if len(matches)>1 or matches[0][:len(row)]!=row:
                raise ConflictError('Sheet contains conflicting canonical episode pointer')
        else:
            self.service.spreadsheets().values().append(spreadsheetId=self.spreadsheet_id,
                range=f"'{self.tab}'!A:I",valueInputOption='RAW',insertDataOption='INSERT_ROWS',
                body={'values':[row]}).execute()
        after=self._rows()
        matches=[r for r in after[1:] if r and r[0]==delivery_id]
        if len(matches)!=1 or matches[0][:len(row)]!=row:
            raise GateError('Native Sheets readback did not prove one exact pointer')
        return {'verified':True,'spreadsheet_id':self.spreadsheet_id,
                'tab':self.tab,'delivery_id':delivery_id,'sha256':sha,
                'verification':'sheets_values_readback'}
