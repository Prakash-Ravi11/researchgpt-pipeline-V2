# Decisions

## Sprint decisions — 2026-11-07

17. Match formatting deterministically inside the declared original chunk and
    retain a source-character map. Collapse whitespace/drop soft hyphens;
    remove a line-break word hyphen only with an unbroken attestation in that
    same source. Never fuzzy-match, change scientific text, search another ID
    to repair attribution, or accept ambiguous spans. Return original slices.
18. Preserve the legacy scientific gate and complete tuple requirements. A
    sentence-final full stop is punctuation, not a decimal continuation;
    longer numeric tokens and extra measurements remain rejected.
19. Add optional table_context_v1 with native text/word geometry and shared
    caption/rule links. Keep uncertain grids unstructured; do not infer cells
    from newline order. No OCR/model/framework/dependency replacement.
20. Add optional table_aware_v1 expansion and atomic source-group delivery.
    The five query strings and baseline retriever stay unchanged; no expected
    values enter queries. Dense query ranks remain distinct from source-order
    union ranks and unscored linked additions.
21. Name the existing successful local generation settings bounded:2048
    output, one candidate/field,8192 context. Preserve defaults. Use180s timeout
    for this opt-in profile based on measured prior129s server runtime.
22. Export RetrievalHit with intact canonical Chunk and explicit score type,
    strategy and order. Keep hybrid/RRF optional and record the actual source
    reference in backend traces; frontend adaptation remains teammate work.
23. Stop after one consolidated94-test suite, frozen A/B/C/D replay and one
    completed real bounded run. Final all-withheld output is retained as a
    negative scientific result. No policy relaxation, extra model retry,
    accuracy claim, auto-approved annotation or full-corpus run follows.

## Accepted project constraints

One FastAPI backend on port 8000. Shared BGE-M3 embeddings and ChromaDB, isolated per project. Canonical paper IDs and stable chunk IDs. Reuse provenance-aware chunking and evidence gate. Preserve five-query retrieval as baseline; hybrid is optional pending controlled measurement. Local and hosted LLMs use one interface. Extraction includes objective and future_scope. Do not replace parsers with a new general framework or copy the whole teammate app.

## Integration decisions

1. Keep required original modules under `src/evidence` and `src/collection` to preserve imports. Public adapters live under `pipeline`, contracts in `shared`, HTTP in `api`. Source hashes and paths are in SOURCE_MANIFEST.json.
2. Preserve current executable five-query policy (50/query, source-order union, 2,500 words). The historical 3/query report is a different configuration. Do not silently label it equivalent.
3. Shared M3 encoder uses original pinned revision and normalized vectors with max length 1024 for documents and queries. Chroma 1.1 API is adapted directly; do not downgrade to teammate's <1 pin. Full Chunk JSON is stored in metadata to retain table cells and references.
4. Replace papers within hashed project collections; never delete global collections. Encoder identity is recorded and mismatches rejected.
5. Hybrid is an optional new adapter using rank_bm25 and reciprocal rank fusion. It preserves source IDs and supports injected reranker objects. It is not the teammate's exact min-max/prefix merge and carries no accuracy claim. HyDE/decomposition deferred.
6. Reuse legacy gate unchanged at migration, with table_value_guard/on and borderless/off. Add strict quote/source-ID checks and complete subject/dataset/metric/value binding to a single table scope. Missing dataset or ambiguous conditions cause abstention. This intentionally favors conservative source quotations; it is not general semantic entailment.
7. Both LLM providers implement the same interface, with actual usage counters and explicit incomplete-output errors. Hosted code is implemented but no credentials/calls are needed for local validation.
8. Current context gains source headers and delivery instrumentation only. Content selection and word truncation remain baseline. Revised selection must be separately evaluated.
9. Actual Qwen output exposed shortened chunk IDs. Ollama's format JSON Schema now restricts IDs to the delivered-context enum; no post-generation ID repair is allowed. The API capability is documented in the [official Ollama structured output documentation](https://github.com/ollama/ollama/blob/main/docs/capabilities/structured-outputs.mdx). Actual follow-up fixed ID shape but established no numerical accuracy gain.
10. Final phase 2 status is PARTIAL: implementation/fixture acceptance is complete, but the installed torch runtime blocks real BGE-M3 execution. Keep that distinction visible rather than treating cached weights/import metadata as a successful model test.
11. Recovery uses standard CPython 3.13.6 and repository-local .venv-gpu with no inherited site-packages. Existing conda/.venv stay unchanged; official torch 2.8.0+cu126 is an execution dependency change, not an embedding/LLM model change. Final tested freeze will pin transitive packages.
12. BGE ownership ends after all document/query embeddings and context selection, before local Qwen inference; cleanup also runs on failure. PyTorch allocator statistics do not account for Ollama. Actual free VRAM and Ollama size_vram are measured separately by the real-paper runner.
13. Local transport tracing observes raw requests/responses before parsing/rejection, including incomplete output and actual token counters. This adds evidence, not acceptance: length-limited or unsupported model output remains rejected.

14. Measured uncapped generation truncates at 768 and 2048. Optional max_candidates_per_field is tested to reject excess entries while preserving the default. Successful smoke uses maxItems=1, output=2048, num_ctx=8192; no model/verifier/scoring change or default promotion.
15. Retain sequential GPU execution. Model reference release and separate PyTorch/global/Ollama memory are verified. CPU-alternative loading is explicitly unavailable under measured host-RAM pressure; no unrelated applications or global settings are changed.
16. Overall Phase2 remains PARTIAL despite runtime and bounded E2E recovery: default profile truncates, numerical tuples remain withheld, and independent scientific accuracy is absent. Source-checked probes are diagnostic observations, not new independent gold.
