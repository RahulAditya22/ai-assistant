import pytest
from docagent.document_service import chunk_pages
from docagent.nlp_pipeline import preprocess,NGramLM,cyk
from docagent.reasoning import extract_edges,KnowledgeGraph,forward_chain,backward_chain,graph_search,weighted_search

def test_preprocess():
 p=preprocess("The quick brown fox is running.");assert "quick" in p["filtered"] and p["bigrams"]
def test_ngram_smoothed_perplexity():
 assert NGramLM(3,.5).fit("the cat sat on the mat").perplexity("the cat sat")>0
def test_chunking():
 cs=chunk_pages([{"page":2,"text":"word "*500}]);assert len(cs)>1 and cs[0]["page"]==2
def test_reasoning_path():
 edges=extract_edges("Python is a prerequisite for Machine Learning. Machine Learning is a prerequisite for NLP.");assert KnowledgeGraph(edges).path("Python","NLP")==["python","machine learning","nlp"]
def test_search_and_logic():
 edges=[{"subject":"a","object":"b"},{"subject":"b","object":"c"}];assert graph_search(edges,"a","c","bfs")[0]==["a","b","c"];assert weighted_search(edges,"a","c","ucs")[0]==["a","b","c"]
 rules=[({"a","b"},"c"),({"c"},"d")];assert "d" in forward_chain({"a","b"},rules);assert backward_chain("d",{"a","b"},rules)
def test_cyk():
 g={("S",("NP","VP")):['S'],("NP",("DET","N")):['NP'],("VP",("V","NP")):['VP'],("DET",("the",)):['DET'],("N",("cat",)):['N'],("V",("sees",)):['V']};assert cyk(["the","cat","sees","the","cat"],g)
