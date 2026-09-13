from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.tree import DecisionTreeClassifier
TRAIN=[("summarize the document","summarization"),("give me a summary","summarization"),("key points","summarization"),("is python a prerequisite for nlp","reasoning"),("does x depend on y","reasoning"),("what is related to machine learning","reasoning"),("compare the two methods","comparison"),("what is the difference","comparison"),("who is the author","retrieval"),("what does the document say about python","retrieval")]
class QueryDecisionTree:
 def __init__(self):
  self.v=TfidfVectorizer(ngram_range=(1,2));self.model=DecisionTreeClassifier(max_depth=4,random_state=42).fit(self.v.fit_transform([x for x,_ in TRAIN]),[y for _,y in TRAIN])
 def predict(self,q):return self.model.predict(self.v.transform([q]))[0]
def cluster_chunks(texts,k=3):
 if len(texts)<2:return [0]*len(texts)
 k=min(k,len(texts));x=TfidfVectorizer(ngram_range=(1,2)).fit_transform(texts);return KMeans(n_clusters=k,n_init=10,random_state=42).fit_predict(x).tolist()
