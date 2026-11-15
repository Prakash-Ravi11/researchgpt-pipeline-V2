# Initial implementation checkpoint

This records the initial 12d1104 checkpoint. Later native recovery and actual-paper validation are documented in RECOVERY_REPORT.md; historical measurements here are preserved.

Only V2 was modified, on feature/evidence-pipeline-integration. All source working trees were clean on initial inspection. No push/merge/PR/full-corpus rerun authorized or performed.

| Phase | Final status | Evidence |
|---|---|---|
| 0 Audit | COMPLETE | Both source trees, relevant branches, exact SHAs, tests/reports and reuse decisions |
| 1 Contracts | COMPLETE | 5 CONTRACT tests; nested provenance/identity round trips |
| 2 Evidence pipeline | PARTIAL | Migrated/connected fixtures pass; actual acquisition/parsing pass; real BGE-M3 execution blocked on torch native import |
| 3 Backend | COMPLETE | Real Uvicorn startup/HTTP checks; connected fixture processing/job tests; default real-model path still limited by phase 2 |
| 4 Diagnostics | COMPLETE | Three source defects reproduced/fixed, exact offsets/hierarchy, context trace/alternative and binding controls; independent accuracy unmeasured |
| 5 Evaluation | COMPLETE | Four frozen fixture/replay arms, no real dense/model accuracy claim |

## Main files and migrations

Complete file inventory: FILES_CHANGED.md. Public contracts: shared/schemas.py, interfaces.py. Service/API: pipeline/service.py, api/main.py. Acquisition/parsing/retrieval/extraction/evidence adapters under pipeline/. Original reusable code remains under src/ to preserve working imports. Tests, fixtures, scripts and the required tracking documents accompany the implementation.

Original source `Prakash-Ravi11/researchgpt-pipeline`, branch claude-code-verification, commit **2d61f3ca6dbdce959381fb891850ad94b52553af**:

- src/collection/semantic_scholar.py and src/config.py: discovery and validated fallback acquisition.
- src/evidence/{acquire,represent,schema,chunker,gate,attribute,anchors,latex_source,latex_tables,latex_parity,borderless}.py: identity/content validation, PDF/JATS/LaTeX, structured cells, provenance, evidence verification/abstention. Borderless is a transitive opt-in dependency, disabled.
- src/processing/pdf_parser.py: grounded processor function only; source anchor/PDF tests migrated.
- src/embedding/build_index.py and src/summarization/retrieval_aware.py inform narrow shared-index/five-query adapters; full modules not copied. Baseline preserves actual 50/query behavior, not stale 3/query commentary.

Teammate `lakshminarasimmann/ResearchGPT`, main, **55d399eefed56e2f231cf434c5f0a5677ea615e1**: inspected rag_new API/jobs/retrieval/vector/LLM boundaries; no wholesale code migration. New optional hybrid adapter preserves actual source IDs through BM25/fusion/reranking. Frontend integration/licensing remain teammate responsibilities. SOURCE_MANIFEST.json records paths and source hashes.

## What actually works

- 70 executed tests pass; per-test classifications, doubles and dependency versions in docs/evidence/test_results.json. Hosted transport and reranker are mocked, not claimed live.
- Real Attention Is All You Need acquired via arXiv fallback after S2 429, validated and parsed: 15 pages, 432 stable chunks, one structured table; identity/content checks pass.
- IDs, source references, exact normalized-source offsets, nested JATS hierarchy and table payloads survive parsing/serialization/real Chroma retrieval. Unsupported/wrong-row/wrong-dataset values abstain.
- API health/OpenAPI and failure responses work; fixture pipeline/jobs connect real modules using explicit encoder/model doubles.
- Actual local model fixture follow-up returns five grounded field excerpts but zero numerical results. This is not independently established scientific accuracy.
- Fixture A/B lose the authored fact in context; C/D deliver it and pass its replayed tuple. No broader retrieval/performance claim.

## Limits and next action

Torch import terminates the installed environment due to duplicate OpenMP runtime. Two bounded scoped fixes failed; no unsafe override or global package repair. Thus full default BGE-M3/Chroma/Qwen E2E is **not established**. Complex/borderless table parsing, independent real annotations, live hosted/reranker validation and frontend mapping remain open; see BLOCKERS.md.

Next: prepare a clean compatible native/torch environment and rerun `python -m scripts.smoke_live --model` on the one cached/validated paper. Keep the 60-paper experiment and publication actions gated on explicit approval.
