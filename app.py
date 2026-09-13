import logging,os,tempfile
from pathlib import Path
from flask import Flask,jsonify,render_template,request
from werkzeug.utils import secure_filename
from docagent.config import MAX_UPLOAD_MB
from docagent.database import init_db,add_document,list_documents,get_chunks,get_edges
from docagent.document_service import allowed,extract,chunk_pages,hash_file
from docagent.nlp_pipeline import preprocess,NGramLM,rule_pos,HMMTagger,cyk
from docagent.reasoning import extract_edges,KnowledgeGraph,weighted_search,forward_chain,backward_chain
from docagent.retrieval import HybridRetriever
from docagent.qa_service import answer,classify
from docagent.ai_baselines import QueryDecisionTree,cluster_chunks
logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO"),format="%(asctime)s %(levelname)s %(name)s %(message)s");log=logging.getLogger("docagent")
app=Flask(__name__);app.config["MAX_CONTENT_LENGTH"]=MAX_UPLOAD_MB*1024*1024;init_db()
@app.get("/")
def index():return render_template("index.html")
@app.get("/health")
def health():return jsonify(status="ok",database="sqlite",documents=len(list_documents()))
@app.get("/api/documents")
def documents():return jsonify(list_documents())
@app.post("/api/upload")
def upload():
 f=request.files.get("file")
 if not f or not f.filename:return jsonify(error="Please choose a PDF, TXT, or DOCX file."),400
 name=secure_filename(f.filename)
 if not allowed(name):return jsonify(error="Unsupported file type. Use PDF, TXT, or DOCX."),415
 tmp=None
 try:
  suffix=Path(name).suffix.lower()
  with tempfile.NamedTemporaryFile(delete=False,suffix=suffix) as t:f.save(t);tmp=t.name
  pages=extract(tmp,suffix[1:]);text="\n".join(p["text"] for p in pages).strip()
  if len(text)<20:return jsonify(error="The document appears empty or contains too little extractable text."),422
  chunks=chunk_pages(pages);edges=[]
  for c in chunks:edges.extend(extract_edges(c["text"],c["chunk_index"]))
  doc_id=add_document(name,hash_file(tmp),suffix[1:],len(pages),len(text),chunks,edges)
  return jsonify(id=doc_id,name=name,chunks=len(chunks),pages=len(pages),edges=len(edges),status="processed"),201
 except Exception:
  log.exception("upload failed");return jsonify(error="The document could not be processed. Please try another file."),500
 finally:
  if tmp:
   try:os.unlink(tmp)
   except OSError:pass
@app.post("/api/ask")
def ask():
 data=request.get_json(silent=True) or {};q=(data.get("question") or "").strip();ids=data.get("document_ids")
 if not q:return jsonify(error="Please enter a question."),400
 if len(q)>1000:return jsonify(error="Question is too long."),413
 chunks=get_chunks(ids);edges=get_edges(ids)
 if not chunks:return jsonify(error="Upload at least one document before asking a question."),400
 try:return jsonify(question=q,classification=classify(q),**answer(q,HybridRetriever(chunks),edges))
 except Exception:log.exception("qa failed");return jsonify(error="The question could not be processed safely."),500
@app.get("/api/graph")
def graph():
 ids=request.args.getlist("document_id",type=int);edges=get_edges(ids or None);nodes=sorted({x for e in edges for x in (e["subject"],e["object"])});return jsonify(nodes=nodes,edges=edges)
@app.post("/api/experimental")
def experimental():
 data=request.get_json(silent=True) or {};text=data.get("text","")[:10000];op=data.get("operation","preprocess")
 if not text.strip():return jsonify(error="Text is required."),400
 p=preprocess(text)
 if op=="preprocess":return jsonify(p)
 if op=="lm":
  lm=NGramLM(3,.5).fit(text);return jsonify(perplexity=lm.perplexity(text),vocabulary=len(lm.vocab),smoothing="add-k")
 if op=="pos":return jsonify(tokens=rule_pos(p["tokens"]))
 if op=="hmm":
  tagger=HMMTagger().fit([[('the','DT'),('cat','NN'),('runs','VB')],[('a','DT'),('dog','NN'),('runs','VB')]]);return jsonify(tokens=tagger.tag(p["tokens"]))
 if op=="cyk":
  g={("S",("NP","VP")):['S'],("NP",("DET","N")):['NP'],("VP",("V","NP")):['VP'],("DET",("the",)):['DET'],("N",("cat",)):['N'],("V",("sees",)):['V']};return jsonify(accepted=cyk([x.lower() for x in p["tokens"]],g),grammar="tiny CNF example")
 if op=="search":
  edges=get_edges();path,cost,explored=weighted_search(edges,data.get("start","").lower(),data.get("goal","").lower(),data.get("method","ucs"));return jsonify(path=path,cost=cost,nodes_explored=explored,algorithm=data.get("method","ucs"))
 if op=="logic":
  facts=set(data.get("facts",[]));rules=[(set(r["if"]),r["then"]) for r in data.get("rules",[])];goal=data.get("goal","");return jsonify(forward=goal in forward_chain(facts,rules),backward=backward_chain(goal,facts,rules))
 if op=="classify":return jsonify(prediction=QueryDecisionTree().predict(text))
 if op=="cluster":return jsonify(clusters=cluster_chunks([x["text"] for x in get_chunks()]))
 return jsonify(error="Unknown experimental operation."),400
if __name__=="__main__":app.run(host="0.0.0.0",port=int(os.getenv("PORT",5000)),debug=False)
