from collections import defaultdict,deque
import re,heapq

def canonical(s):return re.sub(r"\s+"," ",s.strip().lower())
def extract_edges(text,chunk_index=0):
 out=[]
 patterns=[(r"([A-Z][A-Za-z0-9 -]{1,50}?)\s+(?:is|are)\s+(?:an?\s+)?prerequisite\s+for\s+([A-Z][A-Za-z0-9 -]{1,50})","prerequisite"),(r"([A-Z][A-Za-z0-9 -]{1,50}?)\s+(?:is|are)\s+required\s+for\s+([A-Z][A-Za-z0-9 -]{1,50})","requires"),(r"([A-Z][A-Za-z0-9 -]{1,50}?)\s+depends\s+on\s+([A-Z][A-Za-z0-9 -]{1,50})","depends_on"),(r"([A-Z][A-Za-z0-9 -]{1,50}?)\s+(?:is|are)\s+(?:a\s+)?part\s+of\s+([A-Z][A-Za-z0-9 -]{1,50})","part_of")]
 for pat,rel in patterns:
  for a,b in re.findall(pat,text):out.append({"subject":canonical(a),"relation":rel,"object":canonical(b),"chunk_index":chunk_index})
 for a,b in re.findall(r"([A-Za-z][A-Za-z0-9 _-]{1,40})\s*[-→]\s*([A-Za-z][A-Za-z0-9 _-]{1,40})",text):out.append({"subject":canonical(a),"relation":"prerequisite","object":canonical(b),"chunk_index":chunk_index})
 return out
class KnowledgeGraph:
 def __init__(self,edges):self.edges=edges;self.adj=defaultdict(list);[self.adj[e["subject"]].append(e) for e in edges]
 def path(self,start,goal,max_depth=6):
  start,goal=canonical(start),canonical(goal);q=deque([(start,[start])]);seen={start}
  while q:
   node,p=q.popleft()
   if node==goal:return p
   if len(p)-1>=max_depth:continue
   for e in self.adj.get(node,[]):
    nxt=e["object"]
    if nxt not in seen:seen.add(nxt);q.append((nxt,p+[nxt]))
  return None
 def relation_answer(self,start,goal):
  p=self.path(start,goal)
  if not p:return None
  return {"answer":f"Yes. {start} reaches {goal} through an indirect relationship." if len(p)>2 else f"Yes. {start} is directly related to {goal}.","path":p,"inference":"transitive closure via graph traversal" if len(p)>2 else "direct document relationship"}
def graph_search(edges,start,goal,method="bfs"):
 adj=defaultdict(list)
 for e in edges:adj[e["subject"]].append(e["object"])
 frontier=[[start]] if method=="dfs" else deque([[start]]);seen={start};explored=0
 while frontier:
  p=frontier.pop() if method=="dfs" else frontier.popleft();explored+=1;n=p[-1]
  if n==goal:return p,explored
  for nxt in adj[n]:
   if nxt not in seen:seen.add(nxt);frontier.append(p+[nxt])
 return None,explored
def weighted_search(edges,start,goal,method="ucs"):
 adj=defaultdict(list)
 for e in edges:adj[e["subject"]].append((e["object"],float(e.get("cost",1))))
 def h(n):return 0 if method=="ucs" else (0 if n==goal else 1)
 heap=[(h(start),0,start,[start])];best={start:0};explored=0
 while heap:
  _,cost,node,path=heapq.heappop(heap);explored+=1
  if node==goal:return path,cost,explored
  if cost>best.get(node,1e99):continue
  for nxt,w in adj[node]:
   nc=cost+w
   if nc<best.get(nxt,1e99):best[nxt]=nc;heapq.heappush(heap,(nc+h(nxt),nc,nxt,path+[nxt]))
 return None,None,explored
def forward_chain(facts,rules):
 known=set(facts);changed=True
 while changed:
  changed=False
  for premises,c in rules:
   if set(premises)<=known and c not in known:known.add(c);changed=True
 return known
def backward_chain(goal,facts,rules,seen=None):
 seen=seen or set()
 if goal in facts:return True
 if goal in seen:return False
 seen.add(goal);return any(all(backward_chain(p,facts,rules,seen) for p in premises) for premises,c in rules if c==goal)
