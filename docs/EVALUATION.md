# Evaluation

## Engineering sprint consolidation — 2026-11-07

Executed the full suite once after the connected engineering checkpoint:
**94 passed, 0 failed, 0 skipped**, one Starlette/AnyIO dependency deprecation
warning, 7.11s. Interpreter was the exact repository `.venv-gpu/Scripts/python.exe`
(CPython3.13.6). Executed test classifications, doubles, durations and package
versions are in `docs/evidence/sprint_tests.json`; JUnit is retained at
`outputs/sprint/final-pytest.xml`. These are unit/contract/connected synthetic
tests, not 94 independently validated scientific extraction cases.

Unchanged frozen A/B/C/D fixture/replay ran in a separate temporary Chroma
database. All four metric dictionaries equal the recovery baseline: A/B
complete tuples0/1 and delivery0/1; C/D1/1, unsupported control withheld,
provenance1.0. Annotation, document, chunk-corpus hashes and scoring rules equal
the preserved baseline. Dense encoder is the explicit TinyEncoder test double;
candidate response is deterministic replay; Chroma and BM25 are real modules.
No general hybrid or extraction accuracy gain is claimed.

Replay of nine saved **actual** Qwen predictions under the new formatting-only
resolver returns4 instead of1. Three recovered candidates are problem_statement,
research_gap and datasets. Two wrong-ID candidates remain rejected, metrics and
key_findings lack complete tuples, and the result paragraph contains additional
measurements beyond its single tuple. Zero numerical tuples pass. This is a
host-verifier replay, not a new model run. Exact verdicts and mapped original
offsets are in `docs/evidence/sprint_quote_replay.json`.

The separately executed final real-model run and per-query ranks/scores are
recorded in SPRINT_REPORT.md and `docs/evidence/sprint_real_summary.json`.
Twelve agent-proposed source facts in docs/annotations remain unreviewed and
are excluded from every accuracy calculation. No independent real-paper
accuracy, gold labels or 60-paper result is established.

## Frozen configuration and scope

Implemented arms: A five-query/current, B optional hybrid/current, C five-query/revised, D optional hybrid/revised. `scripts/evaluate.py` marks B/D UNAVAILABLE if rank_bm25 is missing; it never substitutes five-query. Actual cross-encoder inference is optional and was not used.

Scoring/annotations committed **before first execution** in `4e07561`. Annotation SHA-256: `f436549bdf5d2b65965655fde8597af153bfbea0e36d3851288336da78e660e1`. Same synthetic JATS paper with 300-word background paragraph, same parsed chunks, real project-isolated Chroma, explicitly test-only deterministic encoder, same 50-hit limits and 250-word allowance. Revised context additionally caps 6,000 UTF-8 bytes, renders table relationships and retains whole chunks. This intentionally small budget reproduces context loss; production default remains 2,500 words/current context.

No LLM is used in scoring runs: controlled candidate replay emits the authored candidate only when its exact quote reaches context, plus one fixed unsupported control. This validates evaluation plumbing, source delivery and gate behavior. **It does not measure real BGE-M3 retrieval or model extraction accuracy.** Full default-model evaluation is unavailable until the native runtime blocker is fixed. Source annotations are not independently validated real-paper ground truth.

## Actual fixture results

Command: `.venv/Scripts/python.exe -B -m scripts.evaluate --output outputs/fixture_evaluation.json`. Raw report, source/corpus hashes, trace, latency and Python allocation peaks are in `docs/evidence/fixture_evaluation.json`. The initial run is preserved in `fixture_evaluation_initial.json`; a final run after adding section hierarchy metadata uses unchanged annotations/scoring and records the current corpus hash.

| Arm | Exact quote delivery | Complete tuple delivery | Correct tuples / gold | Tuple precision | Tuple recall | Unsupported rate | Abstained controls | Provenance |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 0/1 | 0/1 | 0/1 | n/a | 0 | n/a | 1/1 | n/a |
| B | 0/1 | 0/1 | 0/1 | n/a | 0 | n/a | 1/1 | n/a |
| C | 1/1 | 1/1 | 1/1 | 1 | 1 | 0 | 1/1 | 1 |
| D | 1/1 | 1/1 | 1/1 | 1 | 1 | 0 | 1/1 | 1 |

Earliest loss in A/B: **context**, after acquired/represented/parsed/chunked/retrieved evidence survived. C/D carry the quote and explicit row/column/value/caption and pass source verification. Wrong-data controls are withheld. This is a single designed regression, **not a statistically supported improvement or evidence that hybrid beats the baseline**. No policy promoted to default.

Precision/unsupported rate/provenance are null when no claims are returned, not fabricated zeros or perfect scores. Full tuple matching includes subject, dataset, metric, exact value and setting. Ground truth/scoring were not adjusted after observing results.

`perf_counter` timings and tracemalloc peaks describe these executions only, exclude GPU/native/LLM service memory, and are affected by import/cache/order effects. No speed/resource improvement is claimed. Exact Qwen tokenization is unavailable for context assembly; proxy budgets are labeled, actual local-model prompt/generated counters are separate.

## Actual model checks, separate from scoring

Two local synthetic-text Qwen calls were executed. Initial: 392 prompt / 754 generated tokens, 114,056.58 ms, 11 candidates, all rejected for shortened IDs. Constrained follow-up: 498 / 631 tokens, 35,247.67 ms, 9 candidates, 5 source-grounded qualitative/field excerpts returned; **0 verified numerical results**. The remaining candidates abstain on incomplete tuple or wrong binding. Different prompts/decoding and warm state mean these times are not a controlled speed comparison.

These are actual model responses, but not independent scientific-accuracy validation. Full outputs, counters and host verdicts are preserved under docs/evidence/llm_smoke*.json. No hosted/paid run, full 60-paper run, changed original evaluation history or relabeled machine-assisted gold.

## Phase2 recovery validation

The recovered .venv-gpu interpreter executed all A/B/C/D fixture/replay arms in another fresh test database after runtime recovery. Exact annotation hash and all metric dictionaries match the preserved baseline: A/B quote delivery 0/1 and correct tuples 0/1; C/D 1/1 and 1/1. Raw final report: outputs/recovery/fixture-evaluation-final.json; compact copy: docs/evidence/recovery_fixture_evaluation.json. No fixture criteria, original results or 60-paper history changed. This remains test-only dense encoding/candidate replay, not real-model accuracy.

Separately, three REAL paper runs used actual GPU BGE and Qwen, fresh Chroma each time:

| Run | Output cap / candidate cap | Actual prompt/generated | Finish / integration |
|---|---|---|---|
| gpu-current-01 | 768 / uncapped | 5451 / 768 | length; explicit extraction failure |
| gpu-current-02-output2048 | 2048 / uncapped | 5451 / 2048 | length; explicit extraction failure |
| gpu-current-03-bounded | 2048 / 1 per field | 5471 / 1849 | stop; PARTIAL structured output, no runtime errors |

Final run returned 1 qualitative excerpt, withheld 8 generated candidates, verified 0 numerical tuples. Five digit-containing entries include citations/data counts; only one typed numerical result was generated. Its quote fails the exact-span contract. Do not score these as five independent experimental predictions or infer a numerical precision/recall estimate without independent annotations. No post-hoc candidate repair or verifier relaxation.

Full recovered suite: 75 passed, 0 failed, 0 skipped, one dependency deprecation warning, 4.16s. Exact interpreter, command, per-test mocks/categories and environment are in docs/evidence/recovery_tests.json. Three small real-paper attempts are explained by newly measured failures; no full-corpus rerun. All resource/timing measurements and scope limits are in RECOVERY_REPORT.md.
