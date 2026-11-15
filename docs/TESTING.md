# Executed validation and limits

Saved Kaggle recovery: **173 passed**,0 failed/skipped,24.61s, one existing
dependency deprecation warning. Exact executed interpreter/command/per-test
scope is docs/evidence/kaggle_recovery_tests.json. Actual1583-byte raw response
and exact schema replay yield12 expected validation errors across10 fields;
actual failed archive import is rejected. CPU regressions include .bin transport
integrity/staging/path safety, retained manifests, runtime/dependency guards,
failure diagnostics, pre-weight prompt-budget rejection and strict API/tuple
verification.41 earlier targeted checks overlap; do not add counts as unique.
Eight Linux/Python3.13 wheels and their direct requirements were inspected only.
Clean Kaggle preflight, GPU NF4 and new Qwen inference remain NOT EXECUTED.

```powershell
$env:PYTHONPATH = (Resolve-Path outputs/qwen-contract/validation-deps).Path
& '.\.venv-gpu\Scripts\python.exe' -X utf8 -B -m pytest -p no:cacheprovider tests -q --tb=short --junitxml=outputs/kaggle-recovery/full-pytest.xml
```

Qwen3 contract correction (2026-11-09): one complete suite **156 passed**,0
failed/skipped,47.31s, one dependency warning. Exact interpreter/command and
per-test results: docs/evidence/qwen_contract_tests.json. New tests use the real
pinned decoder, a character-tokenizer double, an injected CPU runner model,
the exact user-reported metrics excerpt and the existing source-backed gate
fixture. No Qwen model weights/inference or independent gold claim.

Separate CPU checks with Qwen3-8B's actual pinned tokenizer accept valid ID/empty
proposals, reject the reported labels and measure3676 prompt tokens +2048 output
within8192. Full uncompressed schema text was first rejected at7365 prompt
tokens; $defs/$ref compression preserves all constraints/IDs and evidence.
See qwen_contract_tokenizer.json. Decoder pins were installed only in ignored
outputs/qwen-contract/validation-deps; neither Python environment/global install
nor requirements-gpu.lock was changed. For the executed suite:

```powershell
$env:PYTHONPATH = (Resolve-Path outputs/qwen-contract/validation-deps).Path
& '.\.venv-gpu\Scripts\python.exe' -X utf8 -B -m pytest -p no:cacheprovider tests -q --tb=short --junitxml=outputs/qwen-contract/full-pytest.xml
```

New environments can install the inference extra (or the two decoder pins from
kaggle/requirements-extraction.txt) in isolation before these tests.

Private-notebook handoff validation: .venv-gpu Python 3.13.6 parsed all 6 code
cells in kaggle/semantic_inference.ipynb, confirmed empty execution counts/outputs,
and executed configuration/bootstrap against a temporary copy of the actual
five-file package. Input discovery, retained SHA validation and code extraction
passed; missing/duplicate matching manifests were rejected. Evidence:
docs/evidence/kaggle_notebook_validation.json. Remote installation, GPU preflight,
model loading/generation and download remain NOT EXECUTED. No full-suite or
evaluation repeat was needed for this notebook/documentation handoff.

Current semantic sprint: one full144-test suite passes in7.11s; one later33-test
targeted batch passes in3.09s after a reproduced model-size/benchmark ambiguity.
0 failures/skips in those final batches, one dependency warning each. Executed
JUnit is under outputs/semantic; compact per-test evidence is semantic_tests.json
and semantic_scope_tests.json. Frozen A/B/C/D metrics/hashes are unchanged.
Controlled actual-source API and registered-import fixtures pass without real
model generation. No new expensive local inference or live Kaggle run. Human
review remains pending. See SEMANTIC_OFFLOAD_REPORT.md for exact distinctions.

Accuracy-v1: one110-test consolidation passed (8.85s), then20 overlapping
targeted post-fix checks passed (5.21s), with a separate3-test timeout/lifecycle
check (4.67s). All use the exact .venv-gpu interpreter; no second full suite.
Evidence: accuracy_tests.json, accuracy_targeted_tests.json and
accuracy_timeout_tests.json under docs/evidence. New physical PDFs and selector
fixtures are synthetic; they do not supply independent scientific gold.
Actual GPU/API source processing reaches a Qwen ReadTimeout, not a completed
prediction set. See ACCURACY_REPORT.md; earlier test reports below are retained.

Current sprint: `.venv-gpu/Scripts/python.exe -X utf8 -B -m pytest -p
no:cacheprovider tests -q --tb=short --junitxml=outputs/sprint/final-pytest.xml`
executed once after engineering consolidation: **94 passed**,0 failed/skipped,
one dependency deprecation warning,7.11s. Per-test evidence is
`docs/evidence/sprint_tests.json`. Historical reports below are preserved.
The single actual GPU run is separate from pytest; it completes with10
withheld candidates and zero verified numerical tuples. See SPRINT_REPORT.md.

Full executed command and every test's PASS/FAIL, category, duration and mock/double usage are in `docs/evidence/test_results.json`, generated from actual JUnit XML. Environment versions are embedded in that artifact and direct pins in `requirements-tested.txt`. Source SHA attribution is in SOURCE_MANIFEST.json.

| Test file | Classification | Inputs/dependencies | Mocks / limits |
|---|---|---|---|
| test_contracts.py | CONTRACT | Pydantic 2, nested JSON/source references | No mocks; validation only |
| test_anchors.py | UNIT | Migrated anchor regex and neutrality fixture | No mocks; inherited source semantics |
| test_pdf_table_cells.py | INTEGRATION | Physical PDFs generated by PyMuPDF -> parser -> chunker -> gate | Two parser monkeypatch negative controls; no LLM/index; synthetic documents, not acquired papers |
| test_pipeline_integration.py | INTEGRATION | JATS fixture -> parsing -> real Chroma -> retrieval -> verification | TinyEncoder and injected response for connected path; real-document/model accuracy not established |
| test_api.py | INTEGRATION | TestClient -> app/routes/jobs -> connected fixture pipeline | Source/encoder/model doubles; HTTP contracts are real |
| test_diagnostics.py | UNIT | Exact source slices, body counts, merged cells, context trace and hierarchy | Synthetic authored examples, no model |
| test_context_and_retrieval.py | UNIT | Current/revised assembly; actual rank_bm25 | Index/reranker doubles in retrieval tests; no cross-encoder model inference |
| test_clients_and_dispatch.py | UNIT | Provider payloads/usage/incomplete responses; LaTeX/abstract dispatch | HTTP transports mocked; LaTeX identity marked as synthetic fixture |
| test_evaluation.py | UNIT | Complete-tuple scoring and earliest-loss unknowns | No mocks; authored facts, no model accuracy inference |

Historical V2 commands: 4 contract tests passed; 48 migrated/connected tests passed; 50 backend tests passed; 65 after diagnostics/provider tests passed; final full suite recorded separately. Initial sandbox temp-directory setup failures and a too-small context test budget were reported and corrected, not counted as passing runs. Original source corpus experiment suites were not rerun.

Managed Windows sandbox creates inaccessible mode-0700 pytest/temp-package directories. The completed full-suite commands ran outside that sandbox, with generated test data confined to V2. No source repository writes, package upgrades, unsafe duplicate-OpenMP override or hidden provider calls were used.

Other executed checks:

- Real `uvicorn api.main:app --host 127.0.0.1 --port 8000` startup; actual HTTP health/OpenAPI 200; invalid-content response ACQUISITION_FAILED; missing job 404. Server was stopped after checks. No frontend/browser user flow was migrated.
- Real arXiv acquisition/parsing via `scripts.smoke_live --model`; metadata 429 fallback successful; full-model boundary failed on torch native import. Treat as INTEGRATION acquisition/parsing success plus failed END-TO-END attempt, never successful E2E.
- `scripts.smoke_llm` and constrained follow-up: actual local Qwen on synthetic source text, no retrieval, actual token counters; full outputs and host verification saved in docs/evidence. No independently annotated extraction-accuracy claims.
- `scripts.evaluate`: four implemented fixture/replay configurations; scoring frozen in commit 4e07561 before execution. Large corpus/model experiment not run.

## Recovered environment checkpoint

The exact .venv-gpu CPython 3.13.6 interpreter passed 75 tests, 0 failures/skips, one Starlette/AnyIO deprecation warning, in 4.16s. Recovery metadata is separate in docs/evidence/recovery_tests.json; the original 70-test report is preserved. New lifecycle, raw-response, optional-candidate-budget and UTF-8-source regressions failed before their changes and pass afterwards. Actual GPU BGE/Chroma/Qwen execution is outside pytest and recorded separately, with no mock/replay classification. No warning-only dependency upgrade was made.
