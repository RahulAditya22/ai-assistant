# DocReason — Intelligent Document Reasoning & Question Answering Agent

DocReason is a document-grounded AI/NLP application for PDF, TXT and DOCX files. It combines classical information retrieval, corpus-trained Word2Vec semantic retrieval, explainable knowledge-graph reasoning and extractive QA. No external LLM is required for the core path.

## Core principle

Uploaded documents are the source of truth. Answers are selected from retrieved passages, while multi-hop relationship answers expose the graph path used for inference. If evidence is weak, the system returns an explicit insufficient-evidence response rather than inventing facts.

## Features

- PDF/TXT/DOCX extraction with page metadata where available
- SQLite document/chunk/relationship store
- Tokenization, sentence segmentation, normalization, stopword handling, stemming, lemmatization and n-grams
- Smoothed trigram language model and perplexity
- Rule POS and HMM POS educational baselines
- CFG/CYK educational parser
- TF-IDF + bigram retrieval
- Corpus-trained Word2Vec semantic retrieval
- Latent semantic vectors via SVD
- Explainable knowledge graph and multi-hop prerequisite reasoning
- BFS/DFS/UCS/A*/greedy-style weighted search utilities
- Forward/backward chaining
- Decision-tree query-classification and KMeans clustering baselines
- Evidence, source metadata, retrieval scores and confidence
- Extractive summarization
- Responsive presentation-ready UI
- Unit/API/integration tests and deterministic evaluation fixture

## Architecture

See `docs/architecture.md`.

```text
Upload → Extract → NLP preprocess → Chunk → SQLite
                                      ↓
                    TF-IDF + SVD + Word2Vec retrieval
                                      ↓
                       Query classification / routing
                         ↙          ↓           ↘
                    Evidence   Graph reasoning  Summary
                         ↘          ↓           ↙
                         Grounded answer + evidence
```

## Syllabus mapping

NLP: tokenization, sentence segmentation, normalization, stopwords, stemming/lemmatization, n-grams, smoothing, perplexity, POS, HMM, CFG/CYK, TF-IDF, cosine similarity, Word2Vec, embeddings, semantic similarity, conservative relation extraction, extractive summarization and semantic search.

AI: intelligent-agent routing, state-space search, BFS/DFS/UCS/A*/heuristics, knowledge representation, propositional-style forward/backward chaining, bounded FOL-style subject/relation/object representation, supervised decision-tree classification, unsupervised KMeans clustering and optimization-ready retrieval evaluation. Features that do not improve grounded QA are isolated rather than forced into production.

## Local setup

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Testing and evaluation

```bash
pytest -q
python scripts/evaluate.py
```

Evaluation output must be regenerated after meaningful changes. Do not present stale metrics as current benchmarks.

## API

- `GET /health`
- `GET /api/documents`
- `POST /api/upload` — multipart field `file`
- `POST /api/ask` — `{ "question": "...", "document_ids": [1,2] }`
- `GET /api/graph`
- `POST /api/experimental`

## Deployment

Render is configured in `render.yaml` with Gunicorn and `/health`. Docker support is also included.

SQLite is suitable for a free single-instance demo but is not durable across every Render lifecycle event. A scaled production deployment should replace it with managed Postgres/object storage without changing the service interfaces.

## Reliability/security

Upload allow-list, request-size limits, secure temporary files, SHA-256 duplicate detection, parameterized SQL, friendly production errors, no source-control secrets, and explicit unsupported-question handling are included.

## Limitations / future work

Scanned PDFs require OCR; tables are not structurally parsed; relation extraction is conservative; Word2Vec quality depends on corpus size; SQLite is not suitable for horizontal scaling. Future work can add OCR, table extraction, managed vector storage, stronger relation extraction and optional evidence-constrained LLM phrasing.
