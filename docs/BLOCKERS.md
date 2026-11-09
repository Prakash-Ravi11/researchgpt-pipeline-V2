# Blockers and limitations

## Saved Kaggle run02 and prepared recovery — current

Actual debug02 archive is now located and hash-verified. Full raw replay has12
schema violations across all10 fields; the original FAILED archive is rejected
by local import. Torch2.11.0+cu130/bnb0.50.2 are recorded, but Python version was
not recorded. Earlier unavailable-artifact/NOT EXECUTED notes below are historical.
Attempt01's binary failure remains user-reported without its local artifact.

173 local tests pass. New v4 staging and cu130 dependency overlay avoid old ZIP
auto-extraction/venv failures and bind the prepared profile to the manifest.
Clean Kaggle overlay/GPU NF4 preflight and corrected inference are NOT EXECUTED.
Do not claim universal environment compatibility or independently verified
scientific accuracy. Preserve/download01/02 before ending an ephemeral session.
Exact next cells and stop conditions: docs/KAGGLE_RECOVERY_CELLS.md.

## Qwen3 contract correction — current

The user reports Qwen3-8B loaded and generated 349 tokens/EOS on Kaggle, followed
by schema failure for metrics labels. The reported response is invalid, not
verified. The full raw/result artifact has not been supplied locally. A
deterministic regression retains its exact reported metrics excerpt without
assigning IDs to labels. Earlier NOT EXECUTED sections describe prior snapshots.

The HF generation adapter now enforces the source-ID schema at token selection,
with unchanged independent schema/provenance/numerical verification. 156 local
tests and actual pinned-tokenizer checks pass. The corrected remote job remains
NOT EXECUTED; no claim of a successful new model response. Independent human
review is still pending. New private export/setup: kaggle/INFERENCE.md.

## Semantic/offload current limits

The selected Table2 relationship now passes source-backed deterministic
verification with benchmark newstest2014 and condition English-to-French
separated. Its ground-truth status remains needs_human_review; the existing12
proposals remain unreviewed. No independent extraction accuracy is established.
Other unsupported caption grammars, unknown language aliases, ambiguous header/
benchmark relationships and merged cost cells abstain or retain raw fallback.

Kaggle is NOT EXECUTED: the user confirmed no private notebook has been created
or confirmed; no URL, identifier or individual input mount exists yet. The exact
five-file upload checklist and unexecuted T4 notebook are in kaggle/INFERENCE.md
and kaggle/semantic_inference.ipynb. Bootstrap discovers the actual mounted input
by its retained local manifest SHA. A legitimate private GPU session is needed
for a live test; do not send credentials or publish source text publicly. Candidate remote
installation/model execution remains unvalidated. No local expensive retry.

Saved logs prove the3m deadline/cancellation and CPU offload, not GPU OOM.
Startup took43.835s; post-load prefill/generation phase timings remain unknown.
Frontend/deployment and independent review remain pending; backend compatibility
and controlled package/source/API paths are tested. Older blocker sections below
describe preserved historical profiles, including accuracy_v1's unresolved scope.

## Accuracy-v1 current blockers

- Real new API selection run ended at the180s Qwen client deadline:
  EXTRACTION_FAILED/ReadTimeout, no completed model output or measured tokens.
  BGE/index/parser/context succeeded. Only3057MiB free before Qwen, with a
  separate measured4.27GB Ollama GPU footprint and severe host RAM pressure.
  No CUDA OOM/OpenMP error was observed; timeout cause is not proven.
- Fixed completed-bundle loss on the failure path, with an injected-timeout
  regression. Original failed response is preserved; no real-model retry or
  successful new selection inference is claimed.
- Table2 geometry aligns15 BLEU cell/header/row bundles, but EN-DE/EN-FR are
  column conditions, not complete benchmark names. Dataset identity is marked
  unresolved; reviewed caption-to-benchmark/condition mapping is needed before
  these can become complete scientific tuples. Training-cost products and
  unsupported merged/continuation layouts remain unresolved too.
- All12 annotation proposals remain unreviewed. Required research action:
  independently verify source/version/tuple scope, record reviewer/date/verdict
  and explicit dataset aliases/conditions. No real accuracy score until then.
- No Kaggle connector/CLI/credentials configured here. Required compute action:
  open a private GPU notebook, verify source redistribution rights, mount the
  exact private PDF/packet and execute the prepared isolated jobs. Do not send
  credentials or upload protected content publicly. Remote parsers/models
  remain unexecuted candidates, not accuracy improvements.
- Teammate must connect frontend search/process/job polling/citation/status
  navigation and deployment. Backend contracts and synthetic API examples are
  ready; full application integration and scientific novelty remain unproved.

See ACCURACY_REPORT.md for outcomes and kaggle/README.md for executable setup.
Earlier sprint limits below are historical and retained.

## Current sprint limits — 2026-11-07

- Quote formatting and linked Table2 delivery are operational; actual saved
  candidates recover3 qualitative/dataset excerpts. Wrong IDs, ambiguous
  locations and scientific mutations remain rejected.
- The final bounded/table-aware real run completes transport/schema/runtime but
  returns **zero findings**: all10 generated candidates are withheld (7 source
  quote mismatches, 3 nonliteral values). This is a source-grounding/model-output
  limitation, not GPU OOM or OpenMP failure. No further Qwen run in this sprint.
- Table2 remains explicitly unstructured: caption, headers, row119 and word/
  block geometry survive together, but merged/multi-level column bindings are
  not independently established. The numerical gate is not weakened to return
  these values. EN-FR41.8 table and41.0 prose stay distinct.
- The 6000-byte opt-in context delivers all12 Table2 blocks but only32 chunks
  overall, dropping result prose124/125 previously delivered by the larger
  baseline context. Do not promote it as a general extraction-quality gain.
- Full-rank diagnostics request432 neighbors then apply the top50 cutoff;
  historical n=50 ANN unions need not be identical. Report actual ranks and
  within-run delivery, not historical rank improvement or controlled accuracy.
- The12 source-backed annotation proposals are still `needs_human_review`.
  Independent scientific accuracy and evaluation readiness remain blocked on
  independent review, not on a missing test framework.
- Teammate frontend/client mapping, citation/status rendering and deployment
  remain outside the validated backend fixture path. Optional hybrid is
  available/tested; actual cross-encoder and hosted calls remain unvalidated.

Sequential CUDA execution succeeds on6GB; BGE release/weakref and separate
Ollama memory are measured. Host RAM pressure makes CPU co-residency unsuitable
for this run; no CPU model was loaded and no unrelated process was closed.

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
