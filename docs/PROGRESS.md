# Progress

Started 2026-11-06 (Asia/Calcutta). Sole implementation agent. No push or merge authorized.

## Verified starting state

- Destination: `Prakash-Ravi11/researchgpt-pipeline-V2`, clean integration branch, initial HEAD `6b3dc716eb0a3010efb3757d3ac30fe10cb29bda`.
- Original: local read-only `../researchgpt-pipeline`, `claude-code-verification`, HEAD `2d61f3ca6dbdce959381fb891850ad94b52553af`, clean.
- Teammate: local read-only `../ResearchGPT`, `main`, HEAD `55d399eefed56e2f231cf434c5f0a5677ea615e1`, clean.
- Runtime: `python --version` => Python 3.10.18. Dependencies not yet checked.

| Phase | Status | Next acceptance check |
|---|---|---|
| 0 Source audit | COMPLETE | Source assessment and branch selection recorded |
| 1 Contracts | COMPLETE | Four executed CONTRACT tests pass |
| 2 Evidence pipeline | PARTIAL | Runtime and bounded real-paper E2E recovered; default generation/numerical correctness remain unresolved |
| 3 Backend | COMPLETE | Real server health + explicit failure response, 50 regression checks pass |
| 4 Diagnostics | COMPLETE | Three source defects reproduced/fixed; loss instrumentation and context alternative tested; independent accuracy limited |
| 5 Evaluation | COMPLETE | Four fixture/replay arms executed; real-model accuracy explicitly unmeasured |

## Activity / test record

Initial inspection: `git status --short --branch`, `git remote -v`, `git rev-parse HEAD`, `git branch --all` in all three repositories. Completed successfully; no source writes. Source tests not yet executed. No performance or extraction-accuracy claims established.

Files added: `AGENTS.md` and the eight required tracking documents. Latest previously completed commit: `6b3dc716eb0a3010efb3757d3ac30fe10cb29bda`.

Phase 0 complete: inspected original/teammate implementations, source tests, reports and relevant remote branch snapshots with read-only `git show`/`git for-each-ref`. Modified tracking files and AGENTS.md only. No source evaluation rerun. Latest previously completed commit: initial HEAD above.

Runtime probe: Python 3.10.18; Pydantic 2.12.5, FastAPI 0.116.1, httpx 0.28.1, Chroma 1.1.1, sentence-transformers 5.1.1, PyMuPDF 1.28.2, torch 2.5.1, pytest 8.4.2 installed. rank_bm25 absent. BGE-M3/cross-encoder caches listed (usability not yet tested). Ollama `/api/tags` HTTP 200, qwen2.5:7b present, digest `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`.

Phase 1 complete: added `shared/{schemas,interfaces}.py`, contract tests, pyproject.toml, .gitignore and .gitattributes; updated CONTRACTS.md. Executed `python -B -m pytest -p no:cacheprovider tests/test_contracts.py -q`: **4 passed**, no mocks. Previous completed commit `55c4021`. No blockers for phase 2.

Phase 2 complete: migrated 16 minimal modules/tests (SOURCE_MANIFEST.json), acquisition/parsing adapters, shared M3/Chroma index, five-query/hybrid retrievers, local/hosted clients, context/prompt, scoped evidence verification and connected service. Added synthetic JATS fixture and connected tests. Current source IDs and provider provenance round-trip through real Chroma. New source-quote/tuple checks reject wrong values, wrong datasets and temporary IDs.

Executed `python -B -m pytest -p no:cacheprovider tests/test_contracts.py tests/test_anchors.py tests/test_pdf_table_cells.py tests/test_pipeline_integration.py -q` outside sandbox => **48 passed in 5.16s**. Synthetic PDF/JATS, real PyMuPDF/Chroma, deterministic encoder/model doubles; no extraction-accuracy claim. Initial sandbox attempts: 41 passed + 2 temp-directory setup errors; a missing basetemp parent then Windows mode-0700 directory denial prevented completion. Unsandboxed test execution resolved environment issue; tests unchanged. Optional rank-bm25==0.2.2 installed successfully into local .venv after sandbox package-index failure. Venv bootstrap ensurepip failed in sandbox; environment reuse is being completed. Previous completed commit `7a75092`.

Phase 3 implementation: one FastAPI app with discover/process/job/health routes, explicit configuration/validation/failure states and bounded process-local jobs. `.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests -q` => **50 passed in 3.90s**, fixture API uses encoder/model doubles but real Chroma. Runtime reuse completed; local rank_bm25 installed. Previous completed commit `b89e4c4`.

Live smoke `.venv/Scripts/python.exe -B -m scripts.smoke_live --model`: S2 metadata 429; arXiv acquired Attention Is All You Need. Identity title similarity 1.0; content validation 39,498 characters / 15 nonempty pages; SHA-256 `bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697`; 432 blocks/chunks, one structured table, repeated parsing yields identical IDs. Torch import then terminated process with duplicate OpenMP runtime (no extraction result). Scoped native-runtime fixes failed twice; stop repair loop, document blocker. Actual Qwen service/model exists but full default-model E2E is unverified.

Real Uvicorn startup and HTTP GET /health and /openapi.json => 200. Initial invalid-document POST exposed Chroma configuration exception; narrow directory/error-path fix implemented. No frontend migrated or browser-rendering claim. Verification story: API request -> acquisition -> parsing -> index/retrieval -> model -> verified schema; first failed real boundary is embedding native import. Continue independent diagnostics/evaluation, not model-accuracy claims.

Phase 3 complete: real Uvicorn on 127.0.0.1:8000 started; GET /health 200; OpenAPI 200; invalid-content POST 200 with ACQUISITION_FAILED and document_not_validated; missing job 404. Final phase regression `.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests -q`: **50 passed**. Fixture HTTP flow is real connected modules with injected model/encoder, not real model E2E. Real paper acquisition/parsing established separately; default embedding blocked as above. Modified API/service/index error paths, tests and smoke script. Previous completed commit `b89e4c4`.

Phase 4 complete within available annotations: acquisition body-length inflation, colspan metric shift and whitespace offset defects reproduced before isolated changes and passing afterwards. Added unknown-aware eight-stage tracing, whole-chunk relationship-preserving revised context, identity-preserving BM25/reranking regression and scoped verification. Actual local model fixture returned malformed provenance IDs; gate rejected all 11 candidates. Added constrained full-ID schema decoding and clearer quotation instructions; follow-up real model is bounded and separate from evaluation. No claims of independently measured real-paper accuracy improvements. Tests `.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests -q --tb=short` => **65 passed in 3.76s** outside sandbox. One sandbox rerun could not read the elevated-installed optional package; unsandboxed suite succeeds. Modified migrated acquire/chunker/represent (only V2), context/verifier/client, diagnostic code/tests and docs. Previous completed commit `da5e973`.

Phase 5 setup: authored synthetic annotations and scoring rules in tests/fixtures/annotations.json, explicit test-only dense encoder and no-model candidate replay; real BM25/Chroma. Scoring and annotations will be committed before first four-arm execution. Other unavailable configurations/resources must be marked explicitly. No 60-paper run.

Phase 5 complete: scoring/annotations frozen in `4e07561` before first run. All A/B/C/D executed with identical synthetic corpus, actual Chroma/BM25, explicit test-only dense encoder and no-model candidate replay. A/B quote delivery 0/1 and earliest loss=context; C/D delivery 1/1, supported tuples 1/1, unsupported control abstained and source references preserved. No hybrid-vs-baseline accuracy gain, general performance gain, real M3/Qwen accuracy or independent real annotation result is claimed. Initial report retained; final report refreshed after section hierarchy metadata changed, with the same annotation hash and rules.

Actual constrained local Qwen follow-up: complete IDs, 498 prompt / 631 generated tokens, 35,247.67 ms, 9 candidates; 5 grounded field excerpts returned and 4 withheld; **zero verified numerical results**. Baseline/follow-up raw outputs and host verdicts are in docs/evidence. No model retry after this diagnostic follow-up.

Final regression command `.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests -q --junitxml=outputs/pytest.xml`: **70 passed in 7.47s**, 0 failed/skipped. `.venv/Scripts/python.exe -B -m scripts.record_tests outputs/pytest.xml` generated per-test categories/mocks/outcomes and exact environment metadata. `scripts.evaluate --output outputs/fixture_evaluation.json` completed all four arms. See EVALUATION.md and TESTING.md. Previous completed commit `4e07561`.

Final documentation/artifacts: README, tested dependency snapshot, TESTING.md, complete source attribution, initial/final fixture reports, both actual model outputs, test results, file inventory and implementation summary. Reclassified phase 2 from its implementation checkpoint COMPLETE to final PARTIAL because actual default embedding remains blocked. All independent work is complete. No source writes, branch changes, global upgrades, push, merge, PR or full 60-paper rerun.

Final closeout checks: 57 Python files parse with AST; ASGI app imports; git diff --check passes. Both read-only source repositories remain clean on their original branches/SHAs. `scripts.smoke_live` rerun without model uses the hash-verified acquired PDF and confirms 432 stable chunks; evidence saved in docs/evidence/real_acquisition_parsing.json. Acquisition/parsing evidence is now saved before native model initialization so a process-level failure cannot erase completed-stage results. Latest previously completed local checkpoint: `c933c69c14f599112cf8b9a4d5586a0adb423d12`. Final documentation/evaluation artifact commit follows.

Recommended next action: create a clean compatible PyTorch/native-library environment and rerun the existing one-paper smoke before expanding evaluation. Independently reviewed tuple annotations and teammate client adaptation follow that check.

## Phase 2 recovery — 2026-11-06

User authorized isolated environment recovery and one actual-paper validation, including GPU memory measurements, sequential model use and fresh Chroma. Starting branch/HEAD verified clean at `12d11040a4b30841440610f0eb388c1d3c6da5bb`. Existing .venv and source repositories remain untouched.

- Task 1 diagnosis: reproduced documented smoke with only its database/project redirected to a fresh output directory; both smoke and isolated torch import exit **3** with OpenMP Error #15. NumPy alone exits 0. Raw logs/commands/DLL hashes in outputs/recovery/legacy-diagnosis-01. No Python traceback exists for the native termination; stderr and exit code captured. This is an import failure before CUDA allocation, not demonstrated OOM.
- New `.venv-gpu` created at the exact requested path with standard CPython 3.13.6, include-system-site-packages=false. `.venv-gpu/` ignored; old .venv preserved. Official torch 2.8.0+cu126 wheel installation in progress. Target dependencies preserve the existing project versions where compatible; final validated freeze pending.
- Initial VRAM: RTX 3050 6GB, driver 581.86, 5,424 MiB free. Separate GPU and Ollama snapshots will precede each model load; BGE references/cache must be released and measured before Qwen inference.

Next action: complete isolated dependency installation, validate native/CUDA imports, then execute real BGE/index/retrieval on a unique fresh one-paper database. No baseline/scoring changes or full 60-paper run.

Recovery implementation checkpoint: two lifecycle tests failed before correction (model owned at extraction and after index failure); both pass after explicit encoder release before Qwen and in failure cleanup. Added a raw-local-response observer; its regression failed before the hook and passed afterwards. Rejection policy/output budget remain unchanged. Existing interpreter `.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests -q --junitxml=outputs/recovery/legacy-regression-after-lifecycle.xml`: **73 passed in 4.90s**. This is not recovered-environment validation; the full suite must also run in .venv-gpu. Actual VRAM release verification remains pending real model execution.

The single-stream official CUDA wheel transfer stalled and was interrupted; a range downloader now obtains the same official wheel and will check its SHA-256 against the official index. Non-torch pinned project dependencies install separately in .venv-gpu. No replacement of scientific models or global packages.

### Recovery closeout — 2026-11-07 client date

- Runtime recovery COMPLETE: isolated CPython 3.13.6 / torch 2.8.0+cu126; actual CUDA matrix operation passes, only local torch runtime/stub DLLs loaded. Real GPU BGE-M3 produces 432 x 1024 finite normalized embeddings and performs all five real query embeddings/Chroma similarity searches. IDs, metadata and a separate empty control collection verified in a new database on each attempt.
- Real-paper integration COMPLETE under bounded diagnostic configuration: successful fresh collection `rgpt_v2_13d597623a469d64fce2e90d`; cached hash-verified Attention Is All You Need -> current parsing/chunking -> GPU BGE -> fresh Chroma -> five-query retrieval -> current 2500-word context -> real Qwen -> unchanged verifier -> shared schema. 432 chunks; union 134 retrieved, 67 delivered (one partial), 67 dropped. BGE tokens min/median/p95/max 3/7/101.45/256; none exceed 1024.
- Generation: original 768 and diagnostic 2048 uncapped attempts both finish_reason=length, rejected with explicit EXTRACTION_FAILED and raw traces retained. Unbounded quotation arrays confirmed. Added optional max_candidates_per_field with regression: failed before correction, then passed; uncapped default preserved. Successful diagnostic uses maxItems=1, output=2048, num_ctx=8192, same Qwen/model/queries/verifier. Actual prompt/generated tokens 5471/1849, stop, no runtime errors, PARTIAL structured result.
- Successful wrapper 166.94 seconds; BGE encode including load/measurement 14.467 seconds, Ollama server total 129.323 seconds. PyTorch peak allocated/reserved 2,783,155,200/2,814,377,984 bytes. Model weakref gone before Qwen; remaining allocated/reserved 8,519,680/16,777,216 bytes. Free VRAM 5361 MiB before BGE, 5236 MiB after release, 1054 MiB during Qwen. Separate Ollama size_vram 4,270,619,360 bytes; sampled global GPU peak 4949 MiB. Process peak working set 4.111 GiB. No GPU OOM observed.
- CPU alternative explicitly UNAVAILABLE: only 1.132 GiB host RAM available with Qwen resident in the completed run (0.44 GiB in first attempt), below the 4GB load guard. No CPU success claimed; no unrelated applications closed.
- Scientific validation PARTIAL: actual completed output has 9 candidates, 1 qualitative future_scope returned, 8 withheld, 0 verified numerical tuples. Five numerical mentions include citations/counts; one typed result tuple (28.4 BLEU) withheld at exact quote check. Diagnostic normalization finds five whitespace-altered quotes, two wrong source IDs, one other nonliteral quote. Verifier unchanged; no post-hoc quote repair. Table 2 row values survive text but have no matching structured cells; raw row chunk119 is not retrieved, while abstract16 with both probe values is delivered. Source Table2/prose differ on EN-FR values (41.8/41.0); neither is silently overwritten. Probes are agent-checked, not independent human gold.
- Final recovered interpreter `.venv-gpu/Scripts/python.exe -B -m pytest -p no:cacheprovider tests -q --junitxml=outputs/recovery/recovered-pytest.xml`: **75 passed, 0 failed, 0 skipped, 1 dependency deprecation warning, 4.16s**. New UTF-8 analysis regression failed before fix and passes after explicit UTF-8 reads. All A/B/C/D fixture/replay configurations execute in a separate fresh test DB; annotation SHA and metric dictionaries equal preserved baseline. See docs/evidence/recovery_*.json. Full lock: requirements-gpu.lock, 108 distributions; pip check passes. Latest prior checkpoint `32e1ea4`.

Phase 2 remains PARTIAL overall: runtime and real bounded integration milestones are achieved, but default unbounded 768-token extraction still truncates and independently validated numerical correctness is not established. Do not promote diagnostic settings or claim accuracy gains. Next: independently review a small source-span/tuple set, including Table2/prose scope differences, before changing quotation generation/binding or expanding evaluation.
