# Blockers and limitations

## Initial checkpoint blockers (historical)

**Recovery update:** the OpenMP blocker is RESOLVED in isolated .venv-gpu. Real GPU BGE/Chroma and bounded actual-paper Qwen/evidence execution complete. See ENVIRONMENT.md and RECOVERY_REPORT.md. The old .venv remains unchanged.

- **Real BGE-M3 execution blocked by installed native runtime**: live paper acquisition and parsing succeeded, then importing torch terminated the process with OpenMP Error #15 (duplicate libiomp5md.dll). Confirmed with isolated `import torch` before other imports. Scoped `MKL_THREADING_LAYER=SEQUENTIAL` and process-local removal of conda PATH entries did not fix it. Two bounded fixes exhausted; no unsafe KMP_DUPLICATE_LIB_OK, package replacement, DLL deletion or global environment change applied. Continue deterministic/API/evaluation work. Need a clean compatible torch/native-library environment before full default-model E2E can be established.
- **Semantic Scholar live metadata**: HTTP 429 for one paper lookup. arXiv fallback acquired the paper successfully; no repeated full-corpus experiment. Live S2 discovery success remains unverified.
- **Independent annotations/corpora**: source reports include machine-assisted labels and manifest metadata, but original physical corpora are absent in these source checkouts. V2 uses explicitly synthetic fixtures for scoring validation. No independent extraction-accuracy or general performance improvement claim is justified.

## Environment issues resolved or isolated

- Pytest mode-0700 temporary directories are denied inside Windows sandbox, including workspace basetemp. Same suite executed successfully outside sandbox. Keep tests under V2.
- Sandbox package index unavailable; rank-bm25==0.2.2 installed into ignored local .venv using approved network execution. Venv reuses existing system dependencies; no global install/upgrade.
- Real HTTP test exposed Chroma DB initialization error inside sandbox. Added explicit data directory creation and sanitized configuration-error HTTP 503 handling; acquisition-invalid uploads now fail before model/index initialization. Recheck passed: HTTP 200 with ACQUISITION_FAILED; health/OpenAPI 200.

Hosted provider, real cross-encoder reranking and independently annotated real-paper tuple accuracy are not yet validated. No paid API run, source repository writes, push, merge or 60-paper rerun performed.

## Remaining implementation / teammate responsibilities

- Environment owner: use the validated .venv-gpu and requirements-gpu.lock. Native recovery and the bounded actual-paper smoke are complete; do not return to the inherited .venv for GPU execution.
- Teammate/frontend: map project-scoped discover/process/job routes to their client, handle uppercase Job/status vocabulary and FieldValue arrays, display only RETURNED values as findings, preserve citation IDs and expose abstention/error states. No claim of drop-in frontend compatibility.
- Research team: provide a small independently reviewed real-paper tuple set with immutable PDF/XML hashes and experimental conditions; authorize any larger run separately.
- Teammate/maintainers: clarify licensing before copying additional teammate code; hosted credentials/provider policy and real reranker evaluation remain optional work.
- Parser limits: complex JATS rowspan/multirow headers conservatively preserve raw text without fabricated cells; borderless/mixed-layout PDFs remain partially unbindable; LaTeX acquisition remains opt-in.
- Model quality: constrained local fixture output fixes source-ID failure but yields zero verified numerical results. Missing/ambiguous scientific tuples cause safe abstention. General extraction accuracy remains unmeasured.

## Current recovery limits

- Default uncapped/768 and diagnostic uncapped/2048 generation truncate on this paper. The successful diagnostic uses one candidate/field and 2048 output tokens at the same 8192 context. Defaults are preserved, not promoted.
- Actual completed output: 9 candidates, 1 qualitative future_scope returned, 8 withheld; 0 verified numerical tuples. Five whitespace-altered quotes, two quotations assigned to the wrong valid chunk, and one other nonliteral quote fail the unchanged contract. No proved incorrect numerical gate rejection or independent accuracy result.
- Table2 row lacks structured cells and row chunk119 is missed by baseline retrieval. Abstract16 with both probe numbers is delivered, so those values are not lost at context assembly. Table2/prose use different EN-FR values (41.8/41.0); retain this for independent review.
- CPU BGE with GPU Qwen was NOT executed: host RAM available 0.44 GiB in first run / 1.132 GiB in completed run, below the 4GB load guard. Sequential GPU BGE then Qwen works. No unrelated applications closed, no observed GPU OOM.
- Independently validated numerical correctness and production/default-profile extraction remain unestablished. Review source spans/tuples before policy promotion or larger evaluation.
