# ResearchGPT V2

A single FastAPI backend integrating the audited research acquisition, structural parsing, provenance chunking and abstaining evidence gate with shared contracts, isolated Chroma collections and optional hybrid retrieval.

**Current validation:** `.venv-gpu` passes94 tests. Formatting-safe source resolution recovers3 previously withheld candidates in saved-output replay. Optional linked table parsing/retrieval/context delivers all12 Table2 source blocks with provenance; uncertain cells remain unstructured. The single final real BGE-M3/Qwen bounded run completes, but all10 generated candidates are withheld and zero numerical tuples verified. Defaults remain unchanged; independent accuracy is unestablished. See the [sprint report](docs/SPRINT_REPORT.md), [teammate contract](docs/RETRIEVAL_INTEGRATION.md), [unreviewed source queue](docs/annotations/REVIEW_QUEUE.md), historical [recovery report](docs/RECOVERY_REPORT.md) and [exact environment setup](docs/ENVIRONMENT.md). Existing `.venv`/global Python remain unchanged.

Read [progress](docs/PROGRESS.md), [audit](docs/INTEGRATION_AUDIT.md), [blockers](docs/BLOCKERS.md), [diagnostics](docs/DIAGNOSTIC_TRACE.md) and [evaluation](docs/EVALUATION.md). Source attribution and exact hashes are in [SOURCE_MANIFEST.json](docs/SOURCE_MANIFEST.json).

## Setup

Python 3.10+; select a compatible PyTorch build for your hardware first. Use a clean environment to avoid the native-library conflict recorded above.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e '.[retrieval,hybrid,test]'
```

`requirements-tested.txt` records directly tested dependency versions, not a complete transitive lock or proof of clean-environment reproduction. This session reused existing system packages plus a local rank-bm25 install. No global upgrades were made.

BGE-M3 uses `BAAI/bge-m3` revision `5617a9f61b028005a4858fdac845db406aefb181`, max length 1024, normalized vectors. Cached weights are used by default. Set `RGPT_ALLOW_MODEL_DOWNLOAD=1` only when you intend to download missing weights. Local inference defaults to existing Ollama `qwen2.5:7b`, context 8192, output cap 768. No weights or indexes belong in Git.

```powershell
.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

`GET /health` reports server liveness and explicitly does not assert inference readiness. Interactive API docs are at `http://127.0.0.1:8000/docs`.

## API

- `POST /api/papers/discover`: query, limit, start_year, end_year; audited Semantic Scholar discovery. S2 may rate-limit; optional `S2_API_KEY` is read from the environment.
- `POST /api/papers/process`: project_id, paper, retrieval (`five_query` default or `hybrid`), context_mode (`current` default or `revised`). Omit document fields for fallback acquisition, or provide document_base64 plus representation (`pdf` or `jats_xml`). Uploads must pass identity and content checks.
- `POST /api/jobs`: same request, returns job_id with HTTP 202. `GET /api/jobs/{job_id}` polls status/result/error. Jobs are bounded and process-local, lost on restart. One worker process serializes model/index work.

Example acquisition request body:

```json
{"project_id":"demo","paper":{"paper_id":"arxiv:1706.03762","title":"Attention Is All You Need","externalIds":{"ArXiv":"1706.03762"}},"retrieval":"five_query","context_mode":"current"}
```

Output uses `ExtractedPaper.fields`: original field names plus objective/future_scope. Each value has explicit RETURNED/ABSTAINED final state, status, evidence_span and source_refs. **Only RETURNED values are findings**. Missing full text, failed model calls and unsupported evidence are distinct statuses. Strict numerical verification requires a complete subject/dataset/metric/value relationship and unambiguous experimental scope. Source quotations are deliberately conservative.

Hosted compatible chat endpoints are supported by setting `RGPT_LLM_PROVIDER=hosted`, `RGPT_LLM_BASE_URL`, `RGPT_LLM_MODEL`, and `LLM_API_KEY`. Hosted transport is unit-tested with mocks; no paid/hosted request was executed. Other settings: `RGPT_OLLAMA_URL`, `RGPT_EMBEDDING_DEVICE` (cpu default). Secrets never belong in config commits.

## Verification

```powershell
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests -q --junitxml=outputs/pytest.xml
.venv\Scripts\python.exe -B -m scripts.record_tests outputs/pytest.xml
.venv\Scripts\python.exe -B -m scripts.evaluate --output outputs/fixture_evaluation.json
```

Tests include real generated-PDF parsing, synthetic JATS/LaTeX, real Chroma/BM25 and explicitly recorded encoder/model/reranker doubles. Windows managed sandbox permissions may require test execution outside the sandbox; see TESTING.md. The four-arm harness uses frozen synthetic annotations and deterministic candidate replay, **not real dense/model accuracy**. It marks missing hybrid dependencies unavailable rather than substituting another configuration.

Optional bounded live checks (network/model required):

```powershell
.venv\Scripts\python.exe -B -m scripts.smoke_live
.venv\Scripts\python.exe -B -m scripts.smoke_live --model
.venv\Scripts\python.exe -B -m scripts.smoke_llm --name local_fixture_check
```

Generated documents, indexes and raw outputs stay in ignored `data/` or `outputs/`. Do not rerun the original 60-paper experiment without approval. No frontend, authentication, Docker, deployment, synthesis/export system or entire teammate app was migrated.
