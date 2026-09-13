import re
from .nlp_pipeline import sentences,tokenize
from .reasoning import KnowledgeGraph
from .config import MIN_RETRIEVAL_SCORE

def classify(q):
 ql=q.lower()
 if any(x in ql for x in ["summarize","summary","overview","key points"]):return "summarization"
 if any(x in ql for x in ["prerequisite","depends on","indirectly","relationship","related to"]):return "reasoning"
 if any(x in ql for x in ["compare","difference","versus","vs"]):return "comparison"
 return "retrieval"
def extractive_summary(text,max_sentences=4):
 ss=sentences(text)
 if len(ss)<=max_sentences:return ss
 words=tokenize(text);freq={w:words.count(w) for w in set(words)};ranked=[]
 for i,s in enumerate(ss):
  sw=tokenize(s);ranked.append((sum(freq.get(w,0) for w in sw)/max(len(sw),1),i,s))
 return [s for _,_,s in sorted(ranked,reverse=True)[:max_sentences]]
def answer(question,retriever,edges):
 kind=classify(question);results=retriever.search(question,5)
 if kind=="reasoning":
  ents=re.findall(r"\b[A-Z][A-Za-z0-9-]*(?:\s+[A-Z][A-Za-z0-9-]*)*\b",question)
  if len(ents)>=2:
   ans=KnowledgeGraph(edges).relation_answer(ents[0],ents[-1])
   if ans:
    evidence=[e for e in edges if e.get("subject") in [x.lower() for x in ans["path"][:-1]]]
    return {"type":"reasoning",**ans,"evidence":evidence,"results":results,"confidence":min(.98,.72+.05*len(ans["path"]))}
 strong=[r for r in results if r["score"]>=MIN_RETRIEVAL_SCORE]
 if not strong:return {"type":kind,"answer":"Insufficient evidence. I could not find enough information in the uploaded documents to answer this question reliably.","evidence":[],"results":results,"confidence":0.0}
 if kind=="summarization":
  s=extractive_summary(" ".join(r["text"] for r in strong[:3]));return {"type":"summarization","answer":" ".join(s),"evidence":strong[:3],"results":results,"confidence":min(.95,.55+strong[0]["score"]*.4)}
 qterms=set(tokenize(question));cand=[]
 for r in strong[:3]:
  for s in sentences(r["text"]):cand.append((len(qterms&set(tokenize(s)))/max(len(qterms),1),s,r))
 cand.sort(reverse=True,key=lambda x:x[0]);best=cand[0]
 return {"type":kind,"answer":best[1],"evidence":[best[2]],"results":results,"confidence":min(.92,.45+best[0]*.45+best[2]["score"]*.1)}
