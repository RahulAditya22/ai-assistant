import hashlib,re
from pathlib import Path
from pypdf import PdfReader
from docx import Document as DocxDocument
from .config import CHUNK_SIZE,CHUNK_OVERLAP,ALLOWED_EXTENSIONS

def allowed(name): return "." in name and name.rsplit(".",1)[1].lower() in ALLOWED_EXTENSIONS

def extract(path,ext):
    if ext.lower()=="pdf":
        reader=PdfReader(path); return [{"page":i,"text":(p.extract_text() or "").strip()} for i,p in enumerate(reader.pages,1)]
    if ext.lower()=="docx":
        d=DocxDocument(path); return [{"page":None,"text":"\n".join(p.text.strip() for p in d.paragraphs if p.text.strip())}]
    return [{"page":None,"text":Path(path).read_text(encoding="utf-8",errors="replace").strip()}]

def chunk_pages(pages):
    chunks=[]; idx=0
    for page in pages:
        text=re.sub(r"\s+"," ",page.get("text","")).strip()
        if not text: continue
        start=0
        while start<len(text):
            end=min(len(text),start+CHUNK_SIZE)
            if end<len(text):
                cut=text.rfind(" ",start,end)
                if cut>start+200:end=cut
            part=text[start:end].strip()
            if part: chunks.append({"chunk_index":idx,"page":page.get("page"),"section":None,"text":part}); idx+=1
            if end>=len(text):break
            start=max(end-CHUNK_OVERLAP,start+1)
    return chunks

def hash_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
