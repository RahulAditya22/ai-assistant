import re,time,numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
try: from gensim.models import Word2Vec
except Exception: Word2Vec=None
class HybridRetriever:
 def __init__(self,chunks):
  self.chunks=chunks;self.texts=[c["text"] for c in chunks];self.tfidf=TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True,min_df=1);self.X=self.tfidf.fit_transform(self.texts) if self.texts else None;self.w2v=None
  if Word2Vec and self.texts:
   corpus=[re.findall(r"[a-z0-9]+",t.lower()) for t in self.texts];corpus=[x for x in corpus if x]
   if corpus:self.w2v=Word2Vec(sentences=corpus,vector_size=64,window=5,min_count=1,workers=1,epochs=60,seed=42)
  self.svd=None;self.semantic_X=None
  if self.X is not None and self.X.shape[1]>=2:
   k=min(64,self.X.shape[1]-1);self.svd=TruncatedSVD(n_components=k,random_state=42) if k>=1 else None;self.semantic_X=self.svd.fit_transform(self.X) if self.svd else None
 def _w2v_vec(self,text):
  if not self.w2v:return None
  toks=re.findall(r"[a-z0-9]+",text.lower());v=[self.w2v.wv[t] for t in toks if t in self.w2v.wv];return np.mean(v,axis=0) if v else np.zeros(self.w2v.vector_size)
 def rank_methods(self,q,k=5):
  if not self.chunks:return {"tfidf":[],"semantic":[],"word2vec":[]}
  qx=self.tfidf.transform([q]);lex=cosine_similarity(qx,self.X)[0];qsem=self.svd.transform(qx)[0] if self.svd else None;sem=cosine_similarity([qsem],self.semantic_X)[0] if qsem is not None else np.zeros(len(self.chunks));qv=self._w2v_vec(q)
  if qv is not None:
   mat=np.vstack([self._w2v_vec(c["text"]) for c in self.chunks]);den=np.linalg.norm(qv)*np.linalg.norm(mat,axis=1);wv=np.divide(np.dot(mat,qv),den,out=np.zeros(len(self.chunks)),where=den>0)
  else:wv=np.zeros(len(self.chunks))
  def pack(vals):return [{**self.chunks[i],"score":float(vals[i])} for i in np.argsort(-vals)[:k]]
  return {"tfidf":pack(lex),"semantic":pack(sem),"word2vec":pack(wv)}
 def search(self,q,k=5):
  if not self.chunks:return []
  t0=time.perf_counter();m=self.rank_methods(q,k);a={r["id"]:r for r in m["tfidf"]};b={r["id"]:r for r in m["semantic"]};c={r["id"]:r for r in m["word2vec"]};ids=[x["id"] for x in self.chunks];scores=[]
  for i in ids:scores.append((.45*a.get(i,{"score":0})["score"]+.30*b.get(i,{"score":0})["score"]+.25*c.get(i,{"score":0})["score"],i))
  out=[];elapsed=(time.perf_counter()-t0)*1000
  for score,i in sorted(scores,reverse=True)[:k]:
   base=next(x for x in self.chunks if x["id"]==i);out.append({**base,"score":float(score),"tfidf_score":a.get(i,{"score":0})["score"],"semantic_score":b.get(i,{"score":0})["score"],"word2vec_score":c.get(i,{"score":0})["score"],"latency_ms":elapsed})
  return out
def precision_at_k(results,relevant,k):return len({r["id"] for r in results[:k]}&set(relevant))/k if k else 0
def recall_at_k(results,relevant,k):return len({r["id"] for r in results[:k]}&set(relevant))/len(set(relevant)) if relevant else 0
def reciprocal_rank(results,relevant):
 for i,r in enumerate(results,1):
  if r["id"] in set(relevant):return 1/i
 return 0
