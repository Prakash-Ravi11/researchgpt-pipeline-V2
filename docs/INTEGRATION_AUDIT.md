# Integration audit

## Source snapshots

| Repository | Branch | Commit |
|---|---|---|
| Destination | feature/evidence-pipeline-integration | 6b3dc716eb0a3010efb3757d3ac30fe10cb29bda |
| Original | claude-code-verification | 2d61f3ca6dbdce959381fb891850ad94b52553af |
| Teammate | main | 55d399eefed56e2f231cf434c5f0a5677ea615e1 |

All three verified clean before implementation. Source repositories remain read-only. Assessments below distinguish recorded source evidence from V2 validation, which is recorded in PROGRESS.md.

## Component decisions

`O` below denotes original `claude-code-verification@2d61f3ca6dbdce959381fb891850ad94b52553af`; `T` denotes teammate `main@55d399eefed56e2f231cf434c5f0a5677ea615e1`. VALIDATED means supported by source tests/records, not independently established extraction accuracy.

| Component / source path | Snapshot | Assessment | Evidence and decision |
|---|---|---|---|
| Semantic Scholar discovery `src/collection/semantic_scholar.py:fetch_candidates` | O | VALIDATED | Pagination dedupe, retry/backoff and source run manifests; reuse with bounded API adapter |
| Acquisition fallbacks same file `_candidate_pdf_urls`, `download_open_access_pdfs`; `src/evidence/acquire.py` | O | VALIDATED | Identity/content checks; JATS > optional LaTeX > PDF; historical MEDICAL_REACQUIRE_REPORT and manifests; reuse |
| arXiv discovery `src/collection/arxiv_fallback.py` | O | EXPERIMENTAL | Standalone CLI fallback, not necessary to replace S2; retain fallback candidate resolution |
| JATS/PDF/LaTeX representation `src/evidence/represent.py`, `latex_tables.py`, `latex_source.py`, `latex_parity.py` | O | VALIDATED | `tests/test_pdf_table_cells.py`, extraction fidelity and LaTeX reports; reuse, preserve default LaTeX off |
| Scientific ruled PDF tables `represent.py:_attach_pdf_table_cells` | O | VALIDATED | Physical generated-PDF regressions; real-paper claim-cell report has machine-assisted labels; reuse with limits |
| Borderless consensus `src/evidence/borderless.py` | O | EXPERIMENTAL | Phase09A/09B report; default reverted off at freeze. Do not enable or add general Docling/VLM dependency |
| Provenance chunker `src/evidence/chunker.py` | O | VALIDATED | Source table propagation tests; reuse then regress exact offsets and table delivery |
| BGE-M3 / Chroma `src/embedding/build_index.py` | O | VALIDATED | Executable batched normalized embeddings, manifests and historical pipeline runs. Adapt lifecycle to isolated project collections and preserve full chunk JSON |
| Five queries `src/summarization/retrieval_aware.py:_select_legacy`, `_assemble` | O | VALIDATED | Executable code uses **50/query**, source-order union then 2,500-word prefix. Older reports/comments use 3/query. Preserve current executable behavior and expose parameter explicitly |
| Content-aware selection same file | O | EXPERIMENTAL | Historical selector control supports a scoped result, not a general V2 gain; defer automatic promotion |
| Hybrid/BM25/reranking `rag_new/src/retrieval/retriever.py` | T | INCOMPLETE | `bm25_{idx}` IDs, text[:100] merge, `get_all_chunks` discards source IDs. No backend retrieval unit tests. Implement narrow optional adapter; no HyDE default |
| Teammate vector store `rag_new/src/embedding/vector_store.py` | T | INCOMPLETE | Defaults BGE-base instead of M3; Chroma <1 conflicts with installed 1.1.1. Replace backend boundary with shared M3 adapter |
| Context construction `retrieval_aware.py:_assemble`, `summarize.py:estimate_num_ctx`; teammate `llm_client.py` | O/T | INCOMPLETE | Partial chunks lose attribution; O words*1.4 and T chars/token are estimates. Instrument delivered IDs, dropped IDs, prompt counters and exact local tokenizer where available |
| Extraction `src/summarization/summarize.py` | O | VALIDATED | Actual historical model artifacts but not universal correctness. Reuse field vocabulary and deterministic gate; narrow interface replaces file orchestration; add objective/future_scope and explicit failure |
| Gate `src/evidence/gate.py`, `attribute.py`, `anchors.py` | O | VALIDATED | `test_anchors.py`, `test_fallthrough_guard.py`, PDF gate regression, adversarial records; reuse, keep table_value_guard. Known incomplete dataset/condition binding requires conservative V2 tuple check |
| Coverage verifier `src/evidence/verifier.py` | O | OBSOLETE | Lexical coverage is not scientific tuple verification; do not use as sole acceptance gate |
| Evaluations `src/evaluation/bottleneck_diagnosis`, `experiments/document_evidence_pipeline`, `reproducibility` | O | VALIDATED | Preserve history by reference and source SHA; large corpora/PDFs absent from checkout. Do not relabel machine-assisted gold as independent annotations |
| Backend `rag_new/api/main.py`, `schemas.py`, `jobs.py` | T | INCOMPLETE | Thread jobs, `/api/jobs/{id}`, generate/survey routes; React tests use mock API. Reuse polling shape through narrow adapter, no frontend/auth/export migration |

## Other branch inspection (read via git show, no checkout)

- `origin/exp/phase10-binder@050f8de76b8eabf04bb46fd863beee152a760975` and `origin/exp/phase11-binder@43296724502fb3e640aa90d3f94e20e77297c411`: binder development and guarded regression. Phase11 report: S1 FAIL, S2 FAIL, S3 PASS; legacy remains default. Defer binder_v2 promotion.
- `origin/exp/evidence-first-v2@18af9febca88e122b05f6baef7ecbca0068eca4d`: includes October prose attribution experiments. Scope larger than narrow integration; defer.
- `origin/phase-12-new-implementation@5938af3602e5a85f7ce279a756f708ec060d1e94`: `docs/phase12/RESULTS.md` explicitly calls it experimental, disabled, independently unmeasured, with 29/30 v2 document timeouts in the frozen comparison. No validated reason to replace baseline with it.
- `origin/exp/phase09b-fallthrough` equals O; `origin/exp/phase09a-borderless@92c85e36dd2e5522e15ceaa53238b2eef76e42ed` supplies historical borderless work, superseded by off-at-freeze policy.

## Prior findings and their limits

`PROJECT_STATE.md`, `CLAIM_LEDGER.md`, `PHASE1_DELIVERY_GAP.md`, `PHASE7_PORTABILITY.md`, `EXTRACTION_FIDELITY_REPORT.md`, `LATEX_ACQUISITION_REPORT.md`, `CONTEXT_BUDGET_REPORT.md`, and `postfix_claim_cell_report.md` inspected. They distinguish numeric survival from context binding, answer-aware retrieval recall from production delivery, context loss from acquisition coverage, and abstention from extraction failures. Historical 0.940 recall vs 0.090 delivery uses synthesized anchor-aware queries and an older 3/query policy; it is not a V2 expected improvement. Source corpus manifests are present, physical corpus files are not in this checkout. Independent human annotations are not established.

## Attribution

Neither source Git tree contains a LICENSE file. User explicitly authorized migration from their original project. Retain original module docstrings, source SHA/path/hash in `docs/SOURCE_MANIFEST.json`, and notices here. Teammate code is inspected but not copied wholesale; the V2 adapter implements the documented boundary and records conceptual attribution. Distribution license clarification for any future teammate code migration remains a teammate responsibility.
