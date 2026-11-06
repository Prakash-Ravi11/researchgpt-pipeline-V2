# Decisions

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
