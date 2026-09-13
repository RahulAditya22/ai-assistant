# Architecture

The production path is deterministic and document-first.

1. Flask validates upload/query input.
2. PDF/TXT/DOCX extraction produces page-aware text where possible.
3. Text is normalized, tokenized, stopword-filtered, stemmed/lemmatized and chunked.
4. SQLite persists documents, chunks and extracted relationships.
5. Retrieval combines TF-IDF bigrams, latent semantic vectors and corpus-trained Word2Vec averages.
6. A conservative query router selects retrieval, summarization or relationship reasoning.
7. The knowledge graph supports explainable multi-hop traversal.
8. Answers are extractive: answer text comes from retrieved evidence; reasoning answers expose their path.
9. Weak retrieval results trigger an insufficient-evidence response.

Classical AI/NLP algorithms are isolated as educational endpoints so they can be demonstrated without destabilizing the core application.
