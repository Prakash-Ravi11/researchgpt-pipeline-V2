# Engineering sprint results — 2026-11-07

The sprint improves formatting-safe quotation resolution and Table2 evidence
delivery. It does **not** establish improved real extraction accuracy: the
single final Qwen run completes but all10 candidates are withheld. Production
defaults, scientific tuple acceptance and frozen evaluation remain preserved.

## Workstreams and executed engineering checks

| Workstream | Implementation/files | Actual validation and operational limit |
|---|---|---|
| Quote resolution | pipeline/evidence/quotes.py, verification.py; shared/schemas.py |13 new formatting/mutation/ambiguity/ID/offset/boundary tests pass. Original source slices/offsets returned; wrong IDs never repaired. Saved actual output recovers3 candidates, not numerical tuples. |
| Scientific tables | pipeline/parsing/table_context.py, documents.py; src/evidence/chunker.py |3 new physical-PDF/profile tests pass, including structured and unstructured fixtures. Table2 has12 linked source blocks, native block/word boxes and explicit unstructured fallback. No invented cells; general borderless/scanned layouts are not claimed. |
| Retrieval/context | pipeline/retrieval/index.py, retrievers.py; pipeline/extraction/context.py | Existing context/identity/BM25 regressions and new link/atomic-group checks pass. Scores/strategies and source IDs survive; baseline policy remains available. Target row delivered through links, with other context losses recorded. |
| Generation | pipeline/extraction/profiles.py; scripts/validate_real_paper.py | Named bounded profile and defaults tested; actual local response finishes stop at3332/1137 tokens. Same FieldValue/gate/ExtractedPaper path. Unsupported values remain withheld. |
| Backend/teammate | shared/schemas.py RetrievalHit; pipeline/service.py; api/main.py; docs/RETRIEVAL_INTEGRATION.md |3 new profile/adapter/API tests pass. Existing process/job fixture flow passes. Canonical text/source/table/score contract is available; teammate frontend, hosted provider and real reranker remain unvalidated. |
| Review queue | scripts/sprint_checkpoint.py; docs/annotations/REVIEW_QUEUE.md and annotations.template.json |12 exact-source proposals validated for IDs/offsets/hash and empty reviewer/time/verdict. All needs_human_review; excluded from accuracy and prompts. |

The connected engineering checkpoint passed38 tests. The single consolidated
suite then passed **94 tests**,0 failed/skipped, one Starlette/AnyIO dependency
deprecation warning,7.11s. The19 new tests are included in94, not additional
independent extraction cases. Actual interpreter for all sprint Python commands:
`C:\Users\Praka\Downloads\research IQ  V2\researchgpt-pipeline-V2\.venv-gpu\Scripts\python.exe`.
See docs/evidence/sprint_tests.json and ENVIRONMENT.md for exact commands.

## Scientific evidence before and after

Saved completed actual Qwen output (outputs/recovery/gpu-current-03-bounded)
has9 candidates:1 returned,8 withheld. Formatting-only resolver replay returns
4 and withholds5: **3 recovered** (problem_statement, research_gap, datasets).
Objective/method still cite the wrong valid chunk; metrics/key_findings lack
complete tuples; results includes additional measurements beyond its single
tuple. Zero numerical tuples pass before or after. See
docs/evidence/sprint_quote_replay.json. This is a verifier replay, not a new
model output or independent scientific accuracy measurement.

The exact PDF is *Attention Is All You Need*, printed
`arXiv:1706.03762v7 [cs.CL], 2 Aug 2023`,15 pages,
SHA-256 `bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697`.
It is digitally readable. Table2 is mixed/horizontally ruled, with multi-level
headers and shared cost columns. Baseline omitted validated cells and table
links; its chunker separated caption/header/row. The optional representation
preserves their native text/geometry and common table ID without changing
original text, offsets or embedding strings. See TABLE_CONTEXT.md.

Table2 row119 preserves Transformer(big),28.4,41.8 and training-cost text;
header/caption parts108–111 remain accessible. `unstructured_table_text` is
explicit: row/column binding is **not** independently verified. EN-DE28.4,
table EN-FR41.8 and prose EN-FR41.0 (block125) are distinct source observations,
never merged or substituted. None is claimed as an independently validated
numerical finding of this system.

Actual full-corpus dense ranks and cosine similarities for the unchanged
query strings (in TARGET_QUERIES order):

| Query | Caption108 rank / similarity | Big-row119 rank / similarity | Seed115 rank / similarity |
|---|---|---|---|
| problem statement research gap motivation background |69 / .390075 |368 / .303835 |168 / .348869 |
| method approach study design procedure participants sample |217 / .371037 |375 / .319984 |227 / .367425 |
| results findings outcomes performance evaluation |61 / .476465 |400 / .346349 |148 / .441763 |
| dataset survey data collection measures instruments |82 / .408355 |118 / .397941 |45 / .427293 |
| limitations discussion conclusion implications future work |197 / .410289 |420 / .298580 |239 / .394607 |

Caption and target row miss every top50 cutoff. Ordinary source115 seeds the
versioned table-link expansion. Within this run, union134 ->153, delivered67
under current context ->32 under table-aware context,121 dropped, no partial
chunks. Caption108 and row119 are now retrieved/delivered with all12 Table2
parts. Source-order union positions47/58 are **not** improved dense ranks.
Metadata/IDs round-trip through Chroma. The6000-byte budget uses5996 bytes/
936 whitespace words; it is a conservative proxy, not6000 model tokens.

Remaining context loss is material: EN-DE prose124 and EN-FR prose125 are
retrieved but dropped in the smaller table-focused context, whereas current
context delivers them. Dense full-rank diagnostics request432 neighbors and
then take50, unlike the historical ANN request of50; one union member differs
(267 replaces411). Comparisons are within this run, not an exact historical
counterfactual. No ranking or general extraction gain is inferred.

## Single final real-paper execution

Fresh persistent DB: outputs/sprint/gpu-bounded-table-v1/fresh-chroma;
collection `rgpt_v2_2f825358797f56bc0ebb2ff8`. Initial0, final432; IDs,
documents, full metadata and separate empty control collection verified.
Same real BAAI/bge-m3 revision
`5617a9f61b028005a4858fdac845db406aefb181` indexes and queries;1024-dimensional
normalized vectors, max sequence1024, GPUfp16. Document token min/median/p95/max
3/7/101.45/256; no clipping. Five queries unchanged, no expected values injected.

Real local Qwen2.5:7b Q4_K_M digest
`845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`;
bounded profile2048 output/one candidate/8192 context, seed42, temperature0.
Actual3332 prompt/1137 generated tokens, stop,83.107s Ollama total
(12.113s load),89.461s client latency. Wrapper204.433s; BGE encode including
load/measurement88.078s. Host RAM pressure was observed; no causal speedup or
repeat-run timing claim is made.

PyTorch peak allocated/reserved2,783,155,200/2,814,377,984 bytes. Free VRAM
5184MiB before BGE,5159MiB after verified reference/cache release,882MiB after
Qwen response. Post-release allocated/reserved8,519,680/16,777,216 bytes,
weakref gone. Separate Ollama GPU4,270,619,360 bytes; sampled global GPU peak
5123MiB. Process peak working set4,348,059,648 bytes (~4.05GiB). Qwen was
unloaded after the run; no GPU OOM or OpenMP runtime error. No CPU model load
under host-RAM pressure and no unrelated process shutdown.

Actual result: ABSTAINED, no runtime errors,10 generated/0 returned/10 withheld,
one proposed numerical tuple, zero verified numerical tuples:

| Candidate fields | Earliest rejection |
|---|---|
| problem_statement, objective, research_gap, method, results | Quote unsupported in declared delivered source |
| limitations, future_scope | Quote attributed to wrong valid chunk (140 versus source148); not repaired |
| datasets, metrics, key_findings | Proposed value is a paraphrase, absent from its uniquely resolved source quote |

The result candidate discusses base-model27.3/38.1, not the requested big-row
pair; it fails quotation support before tuple checks. Completed generation is
not scientific verification. Raw requests/responses and full resource/query
traces remain under the ignored run directory; compact evidence is
docs/evidence/sprint_real_summary.json. No further real-model run was made.

## Integration and evaluation milestones

| Milestone | State and evidence |
|---|---|
| Engineering foundation | Met for this scope: isolated native GPU runtime, shared schema, fresh indexes, bounded generation, backend fixture and94 regressions. |
| Evidence extraction reliability | Partial:3 saved candidates recovered; Table2 links delivered. Real final run has0 verified findings; safe cell binding and reliable extractive output remain unresolved. |
| Teammate application integration | Backend/adapter contract met; actual teammate client/frontend migration and deployment remain pending. |
| Research evaluation readiness | Synthetic harness and history preserved.12 proposed facts await independent review; real-paper accuracy and larger evaluation remain unestablished. |

Frozen A/B/C/D fixture replay completed: A/B0 of1 complete tuples/delivery;
C/D1 of1, unsupported control withheld, provenance preserved. All metric
dictionaries, annotation/document/chunk hashes and scoring rules match the
preserved recovery baseline. Dense encoder/candidate replay are explicit test
doubles; Chroma and BM25 are real. New table profiles are not silently relabeled
as frozen C/D. Evidence: docs/evidence/sprint_fixture_evaluation.json.

Local implementation checkpoint2a03ead; review queue checkpointd86fc95.
Final documentation/evidence commit follows. Both source repositories remain
clean at their original branches/SHAs; old .venv, global Python and dependency
lock are unchanged. No push, merge, PR, full60-paper experiment or approval of
annotations occurred.

## One next engineering action

Implement and fixture-test an opt-in extractive span-selection mode that
constructs candidates from validated original source offsets, retaining the
unchanged scientific tuple gate. The final failures are source-grounding
failures even after table delivery; this addresses the next observed blocker.
