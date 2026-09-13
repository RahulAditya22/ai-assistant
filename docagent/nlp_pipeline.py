import math,re
from collections import Counter,defaultdict
from nltk.stem import PorterStemmer
STOPWORDS=set("a an the and or but if then is are was were be been being to of in on for with from by as at this that these those it its into about than can could should would may might will shall do does did not no yes we you your our their they he she his her them i me my mine".split()); STEMMER=PorterStemmer()
def normalize(text):return re.sub(r"\s+"," ",text.lower()).strip()
def tokenize(text):return re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z]+)?",normalize(text))
def sentences(text):return [s.strip() for s in re.split(r"(?<=[.!?])\s+",text.strip()) if s.strip()]
def remove_stopwords(tokens):return [t for t in tokens if t not in STOPWORDS]
def lemmatize(tokens):
 out=[]
 for t in tokens:
  if t.endswith("ies") and len(t)>4:t=t[:-3]+"y"
  elif t.endswith("ing") and len(t)>5:t=t[:-3]
  elif t.endswith("ed") and len(t)>4:t=t[:-2]
  elif t.endswith("s") and len(t)>3:t=t[:-1]
  out.append(t)
 return out
def stem(tokens):return [STEMMER.stem(t) for t in tokens]
def ngrams(tokens,n):return [tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1)]
def preprocess(text):
 toks=tokenize(text); f=remove_stopwords(toks); return {"tokens":toks,"filtered":f,"lemmas":lemmatize(f),"stems":stem(f),"bigrams":ngrams(f,2),"trigrams":ngrams(f,3)}
class NGramLM:
 def __init__(self,n=3,k=.5):self.n=n;self.k=k;self.counts=Counter();self.context=Counter();self.vocab=set()
 def fit(self,text):
  toks=["<s>"]*(self.n-1)+tokenize(text)+["</s>"];self.vocab=set(toks)
  for i in range(self.n-1,len(toks)):
   g=tuple(toks[i-self.n+1:i+1]);self.counts[g]+=1;self.context[g[:-1]]+=1
  return self
 def prob(self,g):return (self.counts[tuple(g)]+self.k)/(self.context[tuple(g[:-1])]+self.k*max(len(self.vocab),1))
 def perplexity(self,text):
  toks=tokenize(text)
  if not toks:return float("inf")
  p=["<s>"]*(self.n-1)+toks; lp=sum(math.log(max(self.prob(p[i-self.n+1:i+1]),1e-12)) for i in range(self.n-1,len(p)));return math.exp(-lp/len(toks))
def rule_pos(tokens):
 out=[]
 for t in tokens:
  tag="CD" if t.isdigit() else "VBG" if t.endswith("ing") else "VBD" if t.endswith("ed") else "VB" if t in {"is","are","was","were","be","am","do","does","did"} else "DT" if t in {"a","an","the"} else "IN" if t in STOPWORDS else "RB" if t.endswith("ly") else "JJ" if t.endswith(("ous","ive")) else "NN";out.append((t,tag))
 return out
class HMMTagger:
 def __init__(self):self.emit=defaultdict(Counter);self.trans=defaultdict(Counter);self.tags=Counter()
 def fit(self,sents):
  for sent in sents:
   prev="<s>"
   for w,t in sent:self.trans[prev][t]+=1;self.emit[t][w]+=1;self.tags[t]+=1;prev=t
  return self
 def tag(self,tokens):
  tags=list(self.tags) or ["NN"];out=[]
  for tok in tokens:
   prev=out[-1][1] if out else "<s>";best=max(tags,key=lambda t:self.emit[t][tok]+self.trans[prev][t]);out.append((tok,best))
  return out
def cyk(tokens,grammar,start="S"):
 n=len(tokens)
 if not n:return False
 table=[[set() for _ in range(n)] for _ in range(n)]
 for i,t in enumerate(tokens):
  for (_,rhs),parents in grammar.items():
   if len(rhs)==1 and rhs[0]==t:table[i][i].update(parents)
 for span in range(2,n+1):
  for i in range(n-span+1):
   j=i+span-1
   for k in range(i,j):
    for (_,rhs),parents in grammar.items():
     if len(rhs)==2 and rhs[0] in table[i][k] and rhs[1] in table[k+1][j]:table[i][j].update(parents)
 return start in table[0][n-1]
