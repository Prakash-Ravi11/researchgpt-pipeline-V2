# Diagnostic trace

Accuracy-v1 update: see ACCURACY_REPORT.md and docs/evidence/accuracy_real_summary.json.
One real PDF ->432 genuine GPU BGE vectors ->fresh isolated Chroma ->15 parsed
source-aligned bundles ->15 prose anchors plus5 compact bundles ->real Qwen
request through the API's in-process HTTP/ASGI route. Prose124/125 reaches the
catalog; source/row/header/version checks remain separate from generation.
Qwen client reaches180s ReadTimeout, with no completed candidate/token packet.
This is EXTRACTION_FAILED, not an all-withheld prediction set or a scored miss.
Original response lost top-level bundles but retained15 in trace; a subsequent
controlled-timeout test proves the failure-preservation correction. No second
real-model run. Latest gate also explicitly withholds Table2 dataset identity
until benchmark and language condition are mapped under reviewed provenance.

## Sprint connected trace — 2026-11-07

Detailed evidence: SPRINT_REPORT.md and docs/evidence/sprint_real_summary.json;
raw trace directory outputs/sprint/gpu-bounded-table-v1. Fulltext acquisition
hash/version verified;432 unchanged chunk IDs/texts,432x1024 real normalized
BGE-M3 embeddings, fresh Chroma metadata/ID/control isolation checked. No
mock encoder/LLM in this run.

Earliest Table2 structural loss was parser relationship omission, then chunk
fragmentation. Opt-in geometry links retain12 caption/header/row blocks with
original provenance but deliberately do not invent cells. Dense caption ranks
69/217/61/82/197 and target-row ranks368/375/400/118/420 miss all top50 lists.
Ordinary table source115 ranks45 for the unchanged dataset query and seeds
link expansion. Union134 ->153; delivered67 baseline ->32 table-aware, including
all12 Table2 parts. Row119 and caption108 move from undelivered to delivered;
dense ranks are unchanged. Prose124/125 is retrieved but dropped by the6000-byte
table-focused context. This remaining context loss is explicit.

Diagnostic full-rank searches request432 neighbors then cut at50; historical
ANN n=50 membership differs and is not an exact historical counterfactual.
Queries, BGE model/revision, source strings and production retriever are
preserved. Do not claim a dense-ranking improvement.

Qwen finishes stop,3332 prompt/1137 generated tokens;10 candidates. Seven
quotes fail declared-source support and three values are not in their matched
source quote. All withheld, no runtime errors, no verified numerical tuples.
Do not conflate a completed structured response with a verified extraction.

Recovery update: native GPU runtime and a bounded real-paper run now work. Earlier blocked statements below describe the initial checkpoint; current complete evidence is in RECOVERY_REPORT.md and docs/evidence/recovery_summary.json.

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
| Model output / citations | Actual Qwen fixture response used shortened IDs and citation labels as quotation text | JSON Schema enum restricts chunk_id to complete context IDs; explicit quote/example instructions. No after-the-fact ID remapping | Transport test passes; actual constrained follow-up uses complete IDs; 5 of 9 source-grounded field excerpts returned, zero numerical results |

Initial diagnostic command `.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests/test_diagnostics.py -q --tb=short`: **3 failed, 2 passed** after adding the merged-row-label probe. After the isolated parser fix: **2 failed, 3 passed**. After acquisition/offset fixes: **5 passed**. Full suite after adapters/context/client tests: **65 passed in 3.76s**. These are synthetic regression results, not measured real-paper accuracy gains.

## Real-document and model boundaries

- Live arXiv fallback acquired Attention Is All You Need, SHA-256 `bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697`: 15 pages, 39,498 parsed characters, 432 blocks/chunks, one structured ruled table. Of 5 caption-like table blocks, 2 report no_ruled_table_beside_caption, 1 reports that plus stacked_records rejection, and 1 has no attached cell metadata. This is parser output, not an independent census of all real tables. Stable IDs confirmed by repeated parsing. This establishes acquisition/parsing, not table completeness; no OCR/vision replacement was introduced.
- Full default-model run stops at torch import (duplicate OpenMP library). Two bounded environment fixes failed; no global repair or unsafe duplicate-runtime override. BGE-M3 retrieval and complete default-model E2E remain unverified.
- Actual local Qwen synthetic-text call (no retrieval) finished in 114,056.58 ms, `prompt_eval_count=392`, `eval_count=754`, finish_reason=stop, configured num_ctx=8192/num_predict=768. These are actual service counters, not words-to-tokens estimates. Model digest is recorded in PROGRESS.md. All 11 candidates were rejected as source_chunk_not_delivered; zero findings returned. This proves safe rejection of that output, not good extraction quality.
- Constrained follow-up: 35,247.67 ms, 498 prompt / 631 generated tokens, stop. All 9 candidates use complete IDs; 5 source-grounded fields returned (objective, datasets, metrics, limitations, future_scope). Three candidates withheld for incomplete_scientific_tuple, one for binding_wrong_cell. Numerical result return count remains **0**. Raw outputs and host verdicts are preserved, not silently repaired or relabeled. Timing is not comparable as a controlled performance result.

Final suite: **70 passed in 7.47s**, no skips, with per-test category and mock usage recorded in `docs/evidence/test_results.json`. Final refinements retain nested JATS section paths, reject ambiguous merged measurement cells, check overlapping long-chunk source slices, and require independent LaTeX identity. Four fixture arms execute under frozen rules: A/B earliest loss=context; C/D no observed loss for the single authored fact. See EVALUATION.md for scope.

## Unresolved limits

No complete independent real-paper annotations; complex PDF layouts/borderless tables and complex JATS headers/rowspans can remain unbindable. Partial scientific conditions/uncertainty types are not inferred. Revised context uses explicit UTF-8 byte proxy budgeting by default, NOT exact Qwen tokenization; an exact model tokenizer counter may be injected. Actual model counters are reported when available. The controlled fixture harness will report text delivery separately from complete tuple delivery and supported output.

## Real-paper recovery: distinct losses

- Native import: old inherited conda/.venv exits 3 before CUDA work. Standard-Python .venv-gpu removes the mixed DLL search path; actual CUDA math and real BGE GPU vectors pass.
- Parsing: page8 Table2 values 28.4/41.8 survive in block119 but no complete matching structured cells exist. Visual source inspection confirms the BLEU subheaders/row associations. No general parser replacement was added.
- Retrieval/context: five real queries return union 134; 67 reach current 2500-word context, one partially. Row119 is missed by retrieval; abstract16 containing both probe values is retrieved AND delivered. Body result124 is also delivered. Numeric survival is not complete table evidence.
- Generation: uncapped 768/2048 packets truncate. No complete-packet candidates are invented from them. One-per-field cap with 2048 output completes at 5471 prompt / 1849 generated tokens.
- Completed response: 9 actual candidates; 1 future_scope quote returned, 8 withheld. Five changed whitespace, two point to the wrong valid source chunk, one has another nonliteral dataset quote. All five entries containing digits (including citation IDs/counts) fail literal quote checks; only results carries a typed numerical tuple. Its 28.4 BLEU quote has whitespace-normalized support in page8 block124 but is not verbatim. This is contract rejection, not proof of factual falsity or a verifier bug.
- Source detail: Table2/abstract EN-FR 41.8 differs from nearby prose 41.0. No value is rewritten to match frozen probes; independent review is needed.

Full actual candidate IDs, block/character locations, literal/normalized diagnostics and verdicts are in outputs/recovery/gpu-current-03-bounded/candidate_classification.json. Normalization is diagnostic ONLY; the verifier remains exact. A Windows locale/UTF-8 reporter defect was caught by a failing scientific-Unicode regression and fixed; it was distinct from native/CUDA/model failures.
