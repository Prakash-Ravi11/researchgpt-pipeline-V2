# Diagnostic trace

## Scope

New V2 diagnostics use authored synthetic JATS/PDF/LaTeX fixtures, an actual acquired public PDF, and one actual local-model fixture response. Source historical corpus measurements remain separate; human-independent real-paper fact annotations are unavailable. `pipeline/diagnostics.py` records the earliest observed failing stage and unknown prior stages; unknown is never treated as passing. `scripts/evaluate.py` traces each frozen synthetic fact across all eight stages.

## Confirmed failures and isolated fixes

| Earliest stage | Reproduction before fix | Narrow change | Executed regression |
|---|---|---|---|
| Acquisition validation | 600-word JATS paragraph repeated by each ancestor's itertext was accepted as >=1,500 body words | Count body.itertext once in `src/evidence/acquire.py` | `test_jats_content_length_does_not_count_nested_text_repeatedly` failed then passed |
| Parsing / scientific binding | A colspan=2 row label made Dice 91.4 attach to HD95, because span advancement happened twice | Advance one slot per already-expanded sequence item; preserve raw text and withhold unsupported rowspan/multirow-header cells | `test_jats_colspan_row_label_does_not_shift_values_into_wrong_metric` failed then passed |
| Chunking provenance | Tabs/newlines were collapsed while offsets were computed in the collapsed stream; source slice did not equal chunk text | Regex word positions slice original block text; chunk numbering unchanged | `test_chunk_offsets_point_into_exact_source_whitespace` failed then passed |
| Context | Result quote present in retrieved set but absent after prefix word cap; ordinary table text did not explicitly deliver row/column links | Separate `revised` context: prioritize result/table chunks, render relationships, retain whole chunks or report skipped IDs; current policy retained | `test_context_trace_exposes_retrieved_but_undelivered_result`, context/table tests pass |
| Retrieval identity (source inspection + regression) | Teammate BM25 creates bm25_idx IDs and merges distinct evidence with same first 100 characters | New optional adapter uses actual IDs through dense/BM25 fusion/reranking | Real rank_bm25 fusion with same-prefix chunks passes; reranker is a deterministic double |
| Verification/binding | Isolated matching number is insufficient to establish dataset/condition/model | Original gate plus exact source quote, delivered chunk ID, single-table subject/metric/value/caption/dataset/setting agreement; extra measurements require separate tuples | Wrong-value, wrong-dataset, temporary-ID and physical-PDF wrong-row controls reject |
| Model output / citations | Actual Qwen fixture response used shortened IDs and citation labels as quotation text | JSON Schema enum restricts chunk_id to complete context IDs; explicit quote/example instructions. No after-the-fact ID remapping | Transport unit test passes; bounded actual constrained follow-up pending |

Initial diagnostic command `.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests/test_diagnostics.py -q --tb=short`: **3 failed, 2 passed** after adding the merged-row-label probe. After the isolated parser fix: **2 failed, 3 passed**. After acquisition/offset fixes: **5 passed**. Full suite after adapters/context/client tests: **65 passed in 3.76s**. These are synthetic regression results, not measured real-paper accuracy gains.

## Real-document and model boundaries

- Live arXiv fallback acquired Attention Is All You Need, SHA-256 `bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697`: 15 pages, 39,498 parsed characters, 432 blocks/chunks, one structured ruled table. Stable IDs confirmed by repeated parsing. This establishes acquisition/parsing, not table completeness. Other scientific tables remain without proven cell binding; no OCR/vision replacement was introduced.
- Full default-model run stops at torch import (duplicate OpenMP library). Two bounded environment fixes failed; no global repair or unsafe duplicate-runtime override. BGE-M3 retrieval and complete default-model E2E remain unverified.
- Actual local Qwen synthetic-text call (no retrieval) finished in 114,056.58 ms, `prompt_eval_count=392`, `eval_count=754`, finish_reason=stop, configured num_ctx=8192/num_predict=768. These are actual service counters, not words-to-tokens estimates. Model digest is recorded in PROGRESS.md. All 11 candidates were rejected as source_chunk_not_delivered; zero findings returned. This proves safe rejection of that output, not good extraction quality.

## Unresolved limits

No complete independent real-paper annotations; complex PDF layouts/borderless tables and complex JATS headers/rowspans can remain unbindable. Partial scientific conditions/uncertainty types are not inferred. Revised context uses explicit UTF-8 byte proxy budgeting by default, NOT exact Qwen tokenization; an exact model tokenizer counter may be injected. Actual model counters are reported when available. The controlled fixture harness will report text delivery separately from complete tuple delivery and supported output.
