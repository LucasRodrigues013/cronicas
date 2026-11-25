"""Private local dense retrieval: unsupervised LSA, plus optional multilingual E5.
No story text is sent to a remote inference service. No model is fine-tuned on test labels.
"""
from __future__ import annotations
import sqlite3,hashlib,json
from pathlib import Path
from .deep_recovery import tokens,STOP
from .memory_continuity import fusion

class DenseIndex:
    def __init__(self,db,backend="lsa",revision=None):
        import numpy as np
        self.np=np;self.db=Path(db);self.backend=backend
        with sqlite3.connect(self.db.resolve().as_uri()+"?mode=ro",uri=True) as c:
            c.row_factory=sqlite3.Row
            rows=c.execute("SELECT id,role,anchor,source,line_start,line_end FROM evidence WHERE role IN ('Prompt','Response') ORDER BY id").fetchall()
        self.rows=[dict(r) for r in rows]
        docs=[r["anchor"] for r in self.rows]
        if backend=="lsa":
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.decomposition import TruncatedSVD
            from sklearn.preprocessing import normalize
            self.vectorizer=TfidfVectorizer(strip_accents="unicode",ngram_range=(1,2),min_df=2,max_features=45000,sublinear_tf=True,dtype=np.float32)
            x=self.vectorizer.fit_transform(docs)
            self.model=TruncatedSVD(n_components=min(96,x.shape[1]-1,x.shape[0]-1),n_iter=5,random_state=42)
            self.vectors=normalize(self.model.fit_transform(x))
            self.components=self.model.components_
        elif backend=="e5":
            if not revision or len(revision)!=40:raise ValueError("Pin E5 model commit")
            from sentence_transformers import SentenceTransformer
            self.model=SentenceTransformer("intfloat/multilingual-e5-small",revision=revision,trust_remote_code=False)
            self.vectors=self.model.encode(["passage: "+s for s in docs],normalize_embeddings=True,batch_size=32,show_progress_bar=False)
        else:raise ValueError("Unknown backend")
    def save_lsa(self,folder):
        if self.backend!="lsa":raise ValueError("Only LSA projection supported")
        folder=Path(folder);folder.mkdir(parents=True,exist_ok=False)
        self.np.savez_compressed(folder/"vectors.npz",vectors=self.vectors,components=self.components,idf=self.vectorizer.idf_,ids=self.np.asarray([r["id"] for r in self.rows]))
        meta={"schema":"worldroot-lsa-v1","db_sha256":hashlib.sha256(self.db.read_bytes()).hexdigest(),"arrays_sha256":hashlib.sha256((folder/"vectors.npz").read_bytes()).hexdigest(),"vocabulary":self.vectorizer.vocabulary_}
        (folder/"manifest.json").write_text(json.dumps(meta,sort_keys=True),encoding="utf-8")

    @classmethod
    def load_lsa(cls,db,folder):
        import numpy as np
        from sklearn.feature_extraction.text import TfidfVectorizer
        obj=cls.__new__(cls);obj.np=np;obj.db=Path(db);obj.backend="lsa"
        folder=Path(folder);meta=json.loads((folder/"manifest.json").read_text())
        if meta.get("schema")!="worldroot-lsa-v1" or meta.get("db_sha256")!=hashlib.sha256(obj.db.read_bytes()).hexdigest() or meta.get("arrays_sha256")!=hashlib.sha256((folder/"vectors.npz").read_bytes()).hexdigest():raise ValueError("Stale or corrupt vector projection")
        with sqlite3.connect(obj.db.resolve().as_uri()+"?mode=ro",uri=True) as c:
            c.row_factory=sqlite3.Row
            obj.rows=[dict(r) for r in c.execute("SELECT id,role,anchor,source,line_start,line_end FROM evidence WHERE role IN ('Prompt','Response') ORDER BY id")]
        with np.load(folder/"vectors.npz",allow_pickle=False) as arrays:
            if arrays["ids"].tolist()!=[r["id"] for r in obj.rows]:raise ValueError("Vector row mismatch")
            obj.vectors=arrays["vectors"];obj.components=arrays["components"];idf=arrays["idf"]
        vocab=meta["vocabulary"]
        if obj.vectors.shape!=(len(obj.rows),obj.components.shape[0]) or obj.components.shape[1]!=len(vocab) or idf.shape!=(len(vocab),) or not all(np.isfinite(a).all() for a in (obj.vectors,obj.components,idf)):raise ValueError("Invalid vector shape")
        obj.vectorizer=TfidfVectorizer(strip_accents="unicode",ngram_range=(1,2),sublinear_tf=True,dtype=np.float32,vocabulary=vocab)
        obj.vectorizer.idf_=idf
        return obj

    def search(self,query,role=None,limit=80):
        if not query.strip() or not 1<=limit<=200:raise ValueError("Invalid query")
        if self.backend=="lsa":
            from sklearn.preprocessing import normalize
            x=self.vectorizer.transform([query])
            if not x.nnz:return []
            vector=normalize(x@self.components.T)[0]
        else:vector=self.model.encode(["query: "+query],normalize_embeddings=True,show_progress_bar=False)[0]
        scores=self.vectors@vector
        ranks=self.np.argsort(-scores,kind="stable")
        out=[]
        for i in ranks:
            r=self.rows[int(i)]
            if role and r["role"]!=role:continue
            if scores[i]<=0:continue
            if any(r["source"]==h["source"] and min(r["line_end"],h["line_end"])-max(r["line_start"],h["line_start"])+1>=9 for h in out):continue
            out.append({**r,"dense_score":float(scores[i])})
            if len(out)==limit:break
        return out
    def combined(self,query,entity=None,role=None,limit=80):
        """Balanced round robin preserves unique candidates from both retrievers."""
        a=fusion(self.db,query,entity=entity,role=role,limit=80)["hits"]
        b=self.search(query,role,80)
        out=[];seen=set()
        for i in range(max(len(a),len(b))):
            for arr in (a,b):
                if i>=len(arr):continue
                h=arr[i]
                if h["id"] in seen:continue
                seen.add(h["id"]);out.append(h)
                if len(out)==limit:return out
        return out
