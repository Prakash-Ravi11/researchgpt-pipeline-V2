# Blockers and limitations

## Confirmed runtime blockers

- **Real BGE-M3 execution blocked by installed native runtime**: live paper acquisition and parsing succeeded, then importing torch terminated the process with OpenMP Error #15 (duplicate libiomp5md.dll). Confirmed with isolated `import torch` before other imports. Scoped `MKL_THREADING_LAYER=SEQUENTIAL` and process-local removal of conda PATH entries did not fix it. Two bounded fixes exhausted; no unsafe KMP_DUPLICATE_LIB_OK, package replacement, DLL deletion or global environment change applied. Continue deterministic/API/evaluation work. Need a clean compatible torch/native-library environment before full default-model E2E can be established.
- **Semantic Scholar live metadata**: HTTP 429 for one paper lookup. arXiv fallback acquired the paper successfully; no repeated full-corpus experiment. Live S2 discovery success remains unverified.
- **Independent annotations/corpora**: source reports include machine-assisted labels and manifest metadata, but original physical corpora are absent in these source checkouts. V2 uses explicitly synthetic fixtures for scoring validation. No independent extraction-accuracy or general performance improvement claim is justified.

## Environment issues resolved or isolated

- Pytest mode-0700 temporary directories are denied inside Windows sandbox, including workspace basetemp. Same suite executed successfully outside sandbox. Keep tests under V2.
- Sandbox package index unavailable; rank-bm25==0.2.2 installed into ignored local .venv using approved network execution. Venv reuses existing system dependencies; no global install/upgrade.
- Real HTTP test exposed Chroma DB initialization error inside sandbox. Added explicit data directory creation and sanitized configuration-error HTTP 503 handling; acquisition-invalid uploads now fail before model/index initialization. Recheck passed: HTTP 200 with ACQUISITION_FAILED; health/OpenAPI 200.

Hosted provider, real cross-encoder reranking and independently annotated real-paper tuple accuracy are not yet validated. No paid API run, source repository writes, push, merge or 60-paper rerun performed.

## Remaining implementation / teammate responsibilities

- Environment owner: prepare a clean compatible torch/native runtime, then rerun the existing one-paper smoke before any larger experiment.
- Teammate/frontend: map project-scoped discover/process/job routes to their client, handle uppercase Job/status vocabulary and FieldValue arrays, display only RETURNED values as findings, preserve citation IDs and expose abstention/error states. No claim of drop-in frontend compatibility.
- Research team: provide a small independently reviewed real-paper tuple set with immutable PDF/XML hashes and experimental conditions; authorize any larger run separately.
- Teammate/maintainers: clarify licensing before copying additional teammate code; hosted credentials/provider policy and real reranker evaluation remain optional work.
- Parser limits: complex JATS rowspan/multirow headers conservatively preserve raw text without fabricated cells; borderless/mixed-layout PDFs remain partially unbindable; LaTeX acquisition remains opt-in.
- Model quality: constrained local fixture output fixes source-ID failure but yields zero verified numerical results. Missing/ambiguous scientific tuples cause safe abstention. General extraction accuracy remains unmeasured.
