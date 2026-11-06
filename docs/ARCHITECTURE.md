# Architecture

`api.main` -> `pipeline.service.EvidencePipeline` -> source -> representation -> provenance chunks -> project Chroma -> retriever -> context -> LLMClient -> legacy gate plus scoped verifier -> ExtractedPaper.

- `shared`: serialized contracts and Protocols, no framework/model imports.
- `src/collection/semantic_scholar.py`: audited discovery/fallback acquisition. `pipeline/acquisition/source.py` translates canonical identity into safe temporary filenames; returns bytes, not private local paths.
- `src/evidence`: audited parsers, table metadata, chunking, anchors, attribution and gate. Optional borderless implementation is preserved only as a transitive dependency and stays off. No Docling/OCR/vision model added to requirements.
- `pipeline/parsing`: representation dispatch and LaTeX numeric parity fallback. Identity remains S2/PDF-derived for LaTeX.
- `pipeline/retrieval`: lazy shared BGE-M3; Chroma serialized Chunk payload; project collection hash, paper-scoped replacements; fixed-query baseline and optional BM25 fusion.
- `pipeline/extraction`: context/delivery trace, quotation-oriented prompt, Ollama and hosted clients. Returned candidate IDs must refer to delivered chunks. Source documents are data, not instructions.
- `pipeline/evidence`: legacy gate and strict complete scientific relationship/quotation validation. Withheld values are explicit candidates with ABSTAINED final state. Only RETURNED values are findings.
- Failures return stage-specific status and sanitized error type. Missing full text is acquisition state, not extraction failure. Missing evidence causes abstention, not invented numbers.

One ASGI application will run on port 8000. Model loading is lazy so health/API startup does not require inference availability. Work is serialized within the process to avoid shared GPU/index races; jobs are process-local polling records, not a durable queue. Frontend/auth/export/deployment remain outside scope.
