# Architecture

Semantic/offload path: validated source -> native geometry -> semantic_v1
caption/header relations -> selected evidence catalog -> portable inference
package -> optional Kaggle generation -> locally registered input + returned
artifact -> integrity/schema checks -> existing local evidence gate -> API.
Remote metadata/verdicts do not authorize facts. Registry/result storage is local;
the single backend on8000 and existing process/discover/job routes are retained.
No frontend/auth/container/deployment rebuild. The original parsing/retrieval/
quotation routes remain defaults; semantic inference is opt-in.

Accuracy-v1 is an optional overlay: validated acquisition -> baseline IR/native
text -> replaceable StructuralParser -> typed source-aligned bundles -> unchanged
BGE retrieval plus optional table links -> balanced authorized span/bundle
catalog -> selection-only LLM -> source/geometry/range/attribution gate -> the
same ExtractedPaper/API. It preserves IDs, original offsets and baseline paths.
The local parser supports a demonstrated multi-header subset. Sparse text and
unresolved relationships emit explicit escalation requests. A lazy Docling
adapter exports external proposals; it does not silently promote them to
trusted cells. Native JATS/LaTeX structures stay supported.

High-capacity execution is separated into private, versioned parser/extractor
jobs under kaggle/. Both remote model candidates consume a hashed matched
packet; local replay applies the same host verifier. No credentials, public
dataset transfer, distributed pooling or framework installation is implied by
that interface. Remote execution remains unvalidated until actually run.

The opt-in sprint path adds `table_context_v1` to PDF dispatch, scored retriever
records, `table_aware_v1` link expansion/atomic context and the named local
`bounded` client profile. It uses the same pipeline, gate and API. Defaults and
legacy source text streams are preserved. See RETRIEVAL_INTEGRATION.md for
metadata, score semantics, request fields and teammate dependencies.

`api.main` -> `pipeline.service.EvidencePipeline` -> source -> representation -> provenance chunks -> project Chroma -> retriever -> context -> LLMClient -> legacy gate plus scoped verifier -> ExtractedPaper.

- `shared`: serialized contracts and Protocols, no framework/model imports.
- `src/collection/semantic_scholar.py`: audited discovery/fallback acquisition. `pipeline/acquisition/source.py` translates canonical identity into safe temporary filenames; returns bytes, not private local paths.
- `src/evidence`: audited parsers, table metadata, chunking, anchors, attribution and gate. Optional borderless implementation is preserved only as a transitive dependency and stays off. No Docling/OCR/vision model added to requirements.
- `pipeline/parsing`: representation dispatch and LaTeX numeric parity fallback. Identity remains S2/PDF-derived for LaTeX.
- `pipeline/retrieval`: lazy shared BGE-M3; Chroma serialized Chunk payload; project collection hash, paper-scoped replacements; fixed-query baseline and optional BM25 fusion.
- `pipeline/extraction`: context/delivery trace, quotation-oriented prompt, Ollama and hosted clients. Returned candidate IDs must refer to delivered chunks. Source documents are data, not instructions.
- `pipeline/evidence`: legacy gate and strict complete scientific relationship/quotation validation. Withheld values are explicit candidates with ABSTAINED final state. Only RETURNED values are findings.
- Failures return stage-specific status and sanitized error type. Missing full text is acquisition state, not extraction failure. Missing evidence causes abstention, not invented numbers.

One ASGI application runs on port 8000. Model loading is lazy so health/API startup does not require inference availability. Work is serialized within the process to avoid shared GPU/index races; jobs are process-local polling records, not a durable queue. Frontend/auth/export/deployment remain outside scope.

`current` context keeps the audited prefix policy with source headers and explicit delivery/drop IDs. `revised` separately orders evidence-bearing whole chunks, renders structured table relationships and records budget rejections. Default proxy units are UTF-8 bytes, explicitly not actual Qwen tokens; a counter may be injected. Actual model token counters are recorded in LLMResponse. Local generation constrains full chunk IDs via JSON Schema, then source quotation and scientific binding are checked independently.
