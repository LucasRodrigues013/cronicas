"""Authenticated Google Drive/Docs adapter, fail-closed.

Do not use a locally supplied locator or a serialized client-side receipt as
proof. The production transport uses Google Application Default Credentials.
Tests use a synthetic in-memory API implementation, never the user's files.
This module is additive and does not modify the historical v4.3 index.
"""
from __future__ import annotations
import hashlib
import io
import re
from datetime import datetime, timezone
from typing import Protocol, Any
from .ledger import WorldrootStore, GateError, ConflictError, digest


class BlobTransport(Protocol):
    def find(self, folder_id: str, delivery_id: str): ...
    def create(self, folder_id: str, filename: str, delivery_id: str, sha256: str, body: bytes): ...
    def info(self, file_id: str): ...
    def download(self, file_id: str) -> bytes: ...


class GoogleAPITransport:
    """Google Drive v3 API; requires authenticated Application Default Credentials.

    Initialize only in a trusted runtime, not in GitHub Actions with story data.
    No user credentials or tokens are serialized into the narrative ledger.
    """
    def __init__(self, service):
        self.service = service

    @classmethod
    def from_adc(cls):
        try:
            import google.auth
            from googleapiclient.discovery import build
        except ImportError as e:
            raise RuntimeError('Install optional extra: pip install .[drive]') from e
        credentials, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/drive.file'])
        if not credentials:
            raise RuntimeError('Google ADC credentials unavailable')
        return cls(build('drive', 'v3', credentials=credentials, cache_discovery=False))

    def find(self, folder_id, delivery_id):
        safe_folder = folder_id.replace("'", "\\'")
        safe_delivery = delivery_id.replace("'", "\\'")
        q = (f"'{safe_folder}' in parents and trashed=false and "
             f"appProperties has {{key='worldroot_delivery' and value='{safe_delivery}'}}")
        result = self.service.files().list(q=q, spaces='drive', fields='nextPageToken,files(id,name,size,md5Checksum,version,parents,appProperties,mimeType)', page_size=100).execute()
        if result.get('nextPageToken'):
            raise GateError('Unexpected pagination for same delivery; investigate duplicates')
        return result.get('files', [])

    def create(self, folder_id, filename, delivery_id, sha256, body):
        from googleapiclient.http import MediaIoBaseUpload
        media = MediaIoBaseUpload(io.BytesIO(body), mimetype='text/plain; charset=utf-8', resumable=True)
        metadata={'name':filename,'parents':[folder_id],'mimeType':'text/plain',
                  'appProperties':{'worldroot_delivery':delivery_id,'worldroot_sha256':sha256}}
        return self.service.files().create(body=metadata, media_body=media,
                    fields='id,name,size,md5Checksum,version,parents,appProperties,mimeType').execute()

    def info(self, file_id):
        return self.service.files().get(fileId=file_id,
                    fields='id,name,size,md5Checksum,version,parents,appProperties,mimeType').execute()

    def download(self, file_id):
        # This returns blob bytes. Native Google Docs are NOT chapter blob files.
        from googleapiclient.http import MediaIoBaseDownload
        stream=io.BytesIO()
        request=self.service.files().get_media(fileId=file_id)
        downloader=MediaIoBaseDownload(stream, request)
        done=False
        while not done:
            _, done=downloader.next_chunk()
        return stream.getvalue()


class GoogleDriveSynchronizer:
    def __init__(self, transport: BlobTransport, folder_id: str, *, allow_synthetic_test_transport: bool = False):
        if not folder_id or '/' in folder_id:
            raise ValueError('A real Drive folder ID is required, not a path/URL')
        if not isinstance(transport,GoogleAPITransport) and not allow_synthetic_test_transport:
            raise GateError('A Google ADC-backed transport is required; synthetic transport only in explicit tests')
        self.transport=transport
        self.folder_id=folder_id

    def sync(self, store: WorldrootStore, delivery_id: str):
        """Idempotent create-or-find, authenticated re-download and byte check.

        A real runtime must instantiate `transport=GoogleAPITransport.from_adc()`.
        Fail closed on metadata collision, hash mismatch, or missing version.
        """
        r=store.receipt(delivery_id)
        if r['state'] not in ('CONFERIDO','CONFIRMADO'):
            raise GateError('Local literal must be independently verified before upload')
        data=store.chapters.joinpath(delivery_id+'.txt').read_bytes()
        if digest(data)!=r['sha256'] or len(data)!=r['bytes']:
            raise GateError('Local literal changed after verification')
        store.outbox_update(delivery_id,'DRIVE_LITERAL',status='PENDING')
        try:
            return self._sync_verified(store,delivery_id,r,data)
        except Exception as exc:
            store.outbox_update(delivery_id,'DRIVE_LITERAL',status='FAILED',error=str(exc)[:500])
            raise

    def _sync_verified(self, store, delivery_id, r, data):
        existing=self.transport.find(self.folder_id, delivery_id)
        if len(existing)>1:
            raise ConflictError('Duplicate Drive uploads for the same delivery; manual review')
        filename=f'{delivery_id}-{r["sha256"][:16]}.txt'
        remote=existing[0] if existing else self.transport.create(self.folder_id, filename, delivery_id, r['sha256'],data)
        remote_id=remote.get('id')
        if not remote_id:
            raise GateError('Drive did not return a real file ID')
        # Independent metadata read, independent blob download: not returned upload bytes.
        meta=self.transport.info(remote_id)
        props=meta.get('appProperties') or {}
        if (meta.get('id')!=remote_id or props.get('worldroot_delivery')!=delivery_id
                or props.get('worldroot_sha256')!=r['sha256'] or self.folder_id not in meta.get('parents',[])
                or meta.get('mimeType')!='text/plain'
                or meta.get('name')!=filename or not meta.get('version')):
            raise GateError('Drive metadata/provenance did not match expected delivery')
        if int(meta.get('size',-1))!=len(data):
            raise GateError('Remote size does not match local UTF-8 bytes')
        expected_md5=hashlib.md5(data).hexdigest()  # Drive provides MD5 of blob; SHA256 remains our integrity proof.
        if meta.get('md5Checksum')!=expected_md5:
            raise GateError('Remote Drive MD5 metadata disagrees')
        independent_download=self.transport.download(remote_id)
        if digest(independent_download)!=r['sha256'] or len(independent_download)!=len(data):
            raise GateError('Independently downloaded Drive bytes differ')
        receipt={'provider':'google_drive','verification':'google_drive_get_media',
                'file_id':remote_id,'folder_id':self.folder_id,'delivery_id':delivery_id,
                'remote_version':str(meta['version']),'sha256':r['sha256'],
                'bytes':len(data),'md5':expected_md5,
                'verified_at':datetime.now(timezone.utc).isoformat(),
                'url':f'https://drive.google.com/file/d/{remote_id}/view'}
        # Private hook; the *trusted orchestrator* must be responsible for
        # supplying a genuinely authenticated service. This is NOT an HSM.
        result=store._record_gateway_receipt(delivery_id,receipt)
        store.outbox_update(delivery_id,'DRIVE_LITERAL',status='DONE')
        return result


class GoogleDocsHeadPublisher:
    """A narrow CAS operation for a native Google Doc, never a generic overwrite.

    Caller must complete dependent Base/Atlas updates and readbacks BEFORE
    this call. HEAD is the LAST external publication step.
    """
    def __init__(self, docs_service, document_id: str):
        self.docs=docs_service
        self.document_id=document_id

    @classmethod
    def from_adc(cls, document_id: str):
        try:
            import google.auth
            from googleapiclient.discovery import build
        except ImportError as e:
            raise RuntimeError('Install optional extra: pip install .[drive]') from e
        credentials,_ = google.auth.default(scopes=['https://www.googleapis.com/auth/documents'])
        if not credentials:
            raise RuntimeError('Google Docs ADC credentials unavailable')
        return cls(build('docs','v1',credentials=credentials,cache_discovery=False),document_id)

    def publish(self, store: WorldrootStore, delivery_id: str, *, expected_revision: str,
                expected_local_release: str, prerequisites_verified: bool, author_approved: bool = False):
        if not author_approved:
            raise GateError('Author approval required before Google Docs HEAD write')
        if not prerequisites_verified:
            raise GateError('Base/Atlas/other dependency readbacks must precede HEAD write')
        r=store.receipt(delivery_id)
        if r['state']!='CONFIRMADO':
            raise GateError('Literal must be confirmed in Drive before HEAD update')
        if not r['events'] or any(e.get('canon_status')!='NARRADO' for e in r['events']):
            raise GateError('HEAD cannot be written for planned/empty/unreviewed event deltas')
        if not expected_revision or not expected_local_release:
            raise GateError('Expected Docs revision and local release are required')
        current=store.status()['head']
        if not current or current['release']!=expected_local_release:
            raise GateError('Local HEAD release has changed; refuse stale write')
        store.outbox_update(delivery_id,'GOOGLE_DOCS_HEAD',status='PENDING')
        meta=r['metadata']
        # Last writer wins is forbidden: the new authoritative HEAD pointer is
        # always the FIRST paragraph of the document, with explicit story state.
        marker=(f"WORLDROOT HEAD CANÔNICO | {meta['book']} | "
                f"Capítulo {meta['chapter']} | Parte {meta['part']} | "
                f"Dia {meta['day']} | {meta['hour']} | {meta['location']} | "
                f"ID {delivery_id} | SHA256 {r['sha256']}\n")
        def text_of(document):
            return ''.join(part.get('textRun',{}).get('content','') for entry in
                document.get('body',{}).get('content',[]) for part in
                entry.get('paragraph',{}).get('elements',[]))
        doc=self.docs.documents().get(documentId=self.document_id,
                fields='documentId,revisionId,body').execute()
        if doc.get('documentId')!=self.document_id:
            raise GateError('Wrong HEAD document ID')
        if text_of(doc).lstrip('\ufeff').startswith(marker):
            # Recovery after remote write succeeded but the client lost the ACK.
            # Do not insert a duplicate marker. Require a changed revision.
            after=doc
        else:
            if doc.get('revisionId')!=expected_revision:
                raise ConflictError('Remote Google Docs revision changed: manual reconciliation required')
            self.docs.documents().batchUpdate(documentId=self.document_id,body={
                'writeControl':{'requiredRevisionId':expected_revision},
                'requests':[{'insertText':{'location':{'index':1},'text':marker}}]}).execute()
            after=self.docs.documents().get(documentId=self.document_id,
                     fields='documentId,revisionId,body').execute()
        if (after.get('revisionId')==expected_revision
                or not text_of(after).lstrip('\ufeff').startswith(marker)
                or after.get('documentId')!=self.document_id):
            raise GateError('HEAD document readback or revision proof failed')
        proof={'provider':'google_docs','verification':'required_revision_id_readback',
               'delivery_id':delivery_id,'sha256':r['sha256'],'document_id':self.document_id,
               'prior_revision':expected_revision,'new_revision':after['revisionId'],
               'expected_local_release':expected_local_release}
        result=store._record_head_receipt(delivery_id,receipt=proof)
        store.outbox_update(delivery_id,'GOOGLE_DOCS_HEAD',status='DONE')
        return result
