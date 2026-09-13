import json,sys,time
sys.path.insert(0,'.')
from docagent.retrieval import precision_at_k,recall_at_k,reciprocal_rank,HybridRetriever
from docagent.reasoning import extract_edges,KnowledgeGraph

def main():
 chunks=[{"id":1,"document_id":1,"document_name":"sample.txt","text":"Python is a prerequisite for Machine Learning."},{"id":2,"document_id":1,"document_name":"sample.txt","text":"Machine Learning is a prerequisite for NLP."},{"id":3,"document_id":1,"document_name":"sample.txt","text":"NLP analyzes language using computational methods."},{"id":4,"document_id":2,"document_name":"other.txt","text":"Databases store structured records and support applications."}]
 r=HybridRetriever(chunks);q="Python prerequisite Machine Learning";rel=[1];out={}
 for method,rs in r.rank_methods(q,3).items():out[method]={"precision@3":precision_at_k(rs,rel,3),"recall@3":recall_at_k(rs,rel,3),"MRR":reciprocal_rank(rs,rel)}
 t=time.perf_counter();path=KnowledgeGraph(extract_edges(chunks[0]["text"])+extract_edges(chunks[1]["text"])).path("Python","NLP");out["reasoning"]={"path_found":path==["python","machine learning","nlp"],"nodes_explored":len(path or []),"latency_ms":(time.perf_counter()-t)*1000};print(json.dumps(out,indent=2))
if __name__=='__main__':main()
