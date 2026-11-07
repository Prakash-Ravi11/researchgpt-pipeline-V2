# Phase2 recovery and real-paper validation

Recovery started at clean integration branch `12d11040a4b30841440610f0eb388c1d3c6da5bb`; closeout uses client date 2026-11-07. No source-repository writes, global package changes, push, merge, PR, paid-provider call or 60-paper rerun.

| Milestone | Result |
|---|---|
| Native/runtime recovery | COMPLETE: real CUDA math, BGE GPU embeddings and Chroma queries |
| Actual-paper integration | COMPLETE for the documented bounded diagnostic configuration |
| Independently validated numerical correctness | NOT ESTABLISHED; zero verified numerical tuples |
| Overall Phase2 | PARTIAL: default generation still truncates; scientific correctness remains unresolved |

## Diagnosed native failure and correction

Old `.venv` inherits conda Python 3.10.18/system packages. Isolated torch import and the documented smoke (only database/project redirected to fresh storage) both exit **3**, stderr OpenMP Error #15, before CUDA work. NumPy alone succeeds. A native termination emits no Python traceback; exact argv, stderr, return codes and DLL hashes are captured in `outputs/recovery/legacy-diagnosis-01/`.

Two distinct libiomp5md.dll files exist in conda Library/bin and torch/lib. Old torch's Windows loader explicitly adds the conda base Library/bin through `os.add_dll_directory`, explaining why trimming PATH did not isolate it. The fix is a standard-Python, non-inheriting venv; no DLL deletion or KMP_DUPLICATE_LIB_OK override. Co-installed old ONNX CPU/GPU packages were observed, but not blamed for an isolated torch import failure.

Exact replacement path: `C:\Users\Praka\Downloads\research IQ  V2\researchgpt-pipeline-V2\.venv-gpu`. Existing `.venv` preserved; `.venv-gpu/` ignored. CPython 3.13.6, torch 2.8.0+cu126, NumPy 2.2.6, sentence-transformers 5.1.1, transformers 4.55.2, tokenizers 0.21.4, Chroma 1.1.1, ONNX CPU 1.31.1. No FlagEmbedding or ONNX GPU dependency required. All 108 distributions pinned in `requirements-gpu.lock`; reproducible commands, official wheel hash and complete diagnosis in ENVIRONMENT.md. `pip check` passes; actual CUDA matrix product passes on RTX 3050 / driver 581.86 / compute capability 8.6. Loaded OpenMP runtime/stub paths belong to the new environment.

## Actual paper and connected execution

Attention Is All You Need, canonical `arxiv:1706.03762`, SHA-256 `bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697`. Reused validated local acquisition cache, verified hash, then reran identity/content checks. PDF: 15 pages, 39,498 text characters, 432 stable blocks/chunks. No network paper reacquisition or synthetic document substitution.

BGE-M3 `BAAI/bge-m3@5617a9f61b028005a4858fdac845db406aefb181`, actual cached CLS pooling, CUDA fp16 model, normalized vectors, max_seq_length 1024. Real document output **432 x 1024**, finite; norms 0.999756–1.000463. Five query embeddings use that same encoder/model. BGE token distribution: min 3, median 7, p95 101.45, max 256, mean 25.30. Zero chunks exceed the embedding limit; no embedding-token truncation is demonstrated.

Each attempt has a new database, starts at count 0, verifies count 432 and complete IDs/metadata, and checks a separate empty isolation-control collection. Successful collection: `rgpt_v2_13d597623a469d64fce2e90d`; database `outputs/recovery/gpu-current-03-bounded/fresh-chroma`. No existing research collection deleted/reused.

Five-query baseline retrieves union 134 chunks. Current context delivers 67, drops 67, and partially includes `arxiv:1706.03762:156#0`; content budget 2500 words. All IDs remain canonical through storage/retrieval/context. A valid ID alone does not prove model attribution.

| Actual attempt | Generation configuration | Actual prompt / generated tokens | Result |
|---|---|---:|---|
| gpu-current-01 | 768 output, uncapped arrays, context8192 | 5451 / 768 | length; explicit EXTRACTION_FAILED |
| gpu-current-02-output2048 | 2048 output, uncapped arrays, context8192 | 5451 / 2048 | length; explicit EXTRACTION_FAILED |
| gpu-current-03-bounded | 2048 output, one candidate/field, context8192 | 5471 / 1849 | stop; PARTIAL structured output, no runtime errors |

Measured long quotation arrays justify the optional per-field generation bound. Its failing regression preceded implementation; default remains uncapped/768. No verifier, model, retrieval baseline or scoring criterion was relaxed. Incomplete packets remain rejected whole; no predictions are invented from partially generated JSON.

Successful GPU encoding including loading/measurement: **14.467s**; indexing 14.954s; retrieval 0.206s; extraction including instrumentation 135.624s; Ollama server total 129.323s; wrapper with cache revalidation/monitoring/cleanup **166.941s**. This is not a controlled performance comparison or a clean cold-start benchmark.

## Memory measurements and release

The machine has 6144 MiB GPU memory and 15.715 GiB host RAM. Before successful BGE load: **5361 MiB free**. Model weak reference is gone after release; gc and CUDA empty_cache run before Qwen. Remaining PyTorch allocated/reserved **8,519,680 / 16,777,216 bytes**, explicitly not zero. Free GPU then **5236 MiB**, and **1054 MiB** while Qwen runs. Weights are released; a small allocator/context footprint remains.

PyTorch peak allocated/reserved **2,783,155,200 / 2,814,377,984 bytes**. Separate Ollama process reports peak size_vram **4,270,619,360 bytes**. Sampled global GPU peak **4949 MiB**, including other applications; WDDM per-process nvidia-smi memory is unavailable. Peak Python process working set **4.111 GiB**. Raw per-phase snapshots/samples preserve all units and timing. Sampling may miss brief global peaks; PyTorch counters exclude Ollama.

Simultaneous residency is unnecessary and those model allocations exceed practical shared headroom. CPU BGE with GPU Qwen was explicitly considered but NOT executed: only **1.132 GiB host RAM** available with Qwen in the successful run (0.44 GiB in first run), below the 4GB loader guard. Do not label this CPU success. No unrelated applications closed or global settings changed. No GPU OOM was observed; neither output truncation nor host-memory pressure is mislabeled as the old OpenMP conflict. Qwen is unloaded after each run.

## Every generated numerical candidate

The completed response contains **9 candidates**, **1 returned qualitative future_scope excerpt**, **8 withheld generated candidates**, plus one missing limitations placeholder. Five candidates contain digits; citation IDs and dataset counts are included below and are not five independent result predictions. Only results carries a typed numerical tuple.

| Generated entry | Source | Actual contents / type | Earliest supported candidate failure | Verdict |
|---|---|---|---|---|
| problem_statement:0 | p2, block21#0, chars2852–3268 | Citation identifiers | Model normalized whitespace; quote not literal | ABSTAINED |
| datasets:0 | p7, block98#0, chars19771–20362 | WMT year, sample/vocabulary counts | Model quotation is not literal, even after whitespace normalization | ABSTAINED |
| metrics:0 | p8, block124#0, chars22520–23035 | BLEU28.4 plus year/delta/training quantities | Model normalized whitespace; quote not literal | ABSTAINED |
| results:0 | p8, block124#0, same chars | Typed big-transformer/WMT EN-DE/BLEU/28.4 tuple; training setting | Model normalized whitespace; quote not literal | ABSTAINED |
| key_findings:0 | p8, block124#0, same chars | Same quantitative paragraph, no typed tuple | Model normalized whitespace; quote not literal | ABSTAINED |

Character offsets above use the canonical normalized document, not PDF byte offsets. Candidate IDs above abbreviate the shared paper prefix `arxiv:1706.03762:`. All full IDs, actual quotes, raw tuple, locations and verifier verdicts remain in ignored execution artifacts. Compact metadata/diagnostic flags are in docs/evidence/recovery_summary.json. Other candidates: objective and method cite wrong valid block15 instead of block16; research_gap changes whitespace; future_scope is an exact source quote and returns. Normalization is diagnosis ONLY, never acceptance. No proved incorrect numerical gate rejection is claimed; policy rejection is not proof the underlying facts are false.

## Earlier source and evidence-delivery limits

Frozen pre-model source probes: Table2 page8 Transformer(big), BLEU EN-DE28.4 and EN-FR41.8, with native PDF coordinates and immutable document hash. They are agent-source-checked, NOT independently human-validated gold. Values survive in abstract block16 and table-row block119; no matching structured cells survive for these rows. Baseline retrieval misses row119 but delivers abstract16 with both values. Body result124 is also delivered. Thus table structure/retrieval are limitations, while context assembly did NOT discard these probe numbers in this run.

Visual page8 inspection confirms Table2 EN-FR41.8 and nearby prose EN-FR41.0. Do not silently harmonize them or label a source-backed 41.0 mention invented. Independent review must establish intended experimental scope before accuracy scoring. Existing parser frameworks/borderless policy remain unchanged; no OCR/VLM/general replacement was introduced.

## Tests, evaluation and checkpoint

Final exact `.venv-gpu` interpreter: **75 passed, 0 failed, 0 skipped**, 1 Starlette/AnyIO deprecation warning, **4.16s**. Per-test category/mocks/command/versions: docs/evidence/recovery_tests.json. Lifecycle, response tracing, optional generation bound and scientific-Unicode reporting regressions were observed failing before correction and passing after. No warning-only library upgrade.

All A/B/C/D fixture/replay configurations execute in a fresh test DB; annotation hash and metric dictionaries exactly match original preserved baseline. A/B deliver 0/1, C/D 1/1; this remains deterministic test encoding/candidate replay, not real-paper accuracy. Raw and compact reports preserved separately. No full 60-paper rerun or altered gold.

Code checkpoints: `32e1ea4` (model release/raw tracing), `6fd68b9` (isolated CUDA validation, optional generation budget, UTF-8 reporting and lock). Final documentation/evidence checkpoint follows. Complete recovery file inventory: RECOVERY_FILES.md.

**Next action:** independently review a small source-span/complete-tuple annotation set, including the Table2/prose difference, then use those fixed regressions to address quotation generation/binding before default promotion or larger evaluation. Runtime recovery is achieved; numerical scientific correctness is not established.
