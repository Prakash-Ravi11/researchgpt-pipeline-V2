# Phase 2 recovery environment

Semantic/offload uses the exact same local .venv-gpu interpreter and validated
requirements-gpu.lock. No global/old-environment changes or framework installs.
Already installed jsonschema4.26.0 is now a direct project dependency.144-test
consolidation,33 targeted scope checks and pip check pass separately.
Versioned export/import commands and isolated remote installation are in
kaggle/INFERENCE.md. The final private portable archive is
outputs/semantic/inference-input-v2.zip; no PDF/model/index/credential is included.
Remote model/environment execution remains NOT EXECUTED, not locally validated.

Accuracy-v1 uses the same local `.venv-gpu` and unchanged validated lock.
No new Windows framework/global installation. Local consolidated tests110 pass;
post-fix targeted20 pass separately. Actual new API run fails at the bounded
Qwen deadline; do not describe it as successful extraction. See ACCURACY_REPORT.md.

Remote isolated parser/extractor setup, exact candidate requirements/model
commits, private input mounts and local replay are in `kaggle/README.md`.
Prepared artifacts: `outputs/accuracy/matched-reviewed-scope-package` (code.zip,
packet.json, input-manifest.json, artifact-sha256.json). This is local export,
not Kaggle execution; source text in the packet requires private handling.

## Sprint profiles (2026-11-07)

No additional dependencies, global changes or model downloads are required.
Use the same exact isolated interpreter and validated `requirements-gpu.lock`.
`bounded` is opt-in: Qwen2.5:7b, num_ctx=8192, num_predict=2048,
maxItems=1 per field, temperature=0, seed=42, local timeout=180s.
Default client remains 768 output tokens, uncapped arrays and timeout=120s.

From the repository root in PowerShell, the consolidated reproduction commands
are:

```powershell
& '.\.venv-gpu\Scripts\python.exe' -X utf8 -B -m pytest -p no:cacheprovider tests -q --tb=short --junitxml=outputs/sprint/final-pytest.xml
& '.\.venv-gpu\Scripts\python.exe' -X utf8 -B -m scripts.record_tests outputs/sprint/final-pytest.xml --output docs/evidence/sprint_tests.json
& '.\.venv-gpu\Scripts\python.exe' -X utf8 -B -m scripts.evaluate --output outputs/sprint/fixture_evaluation.json
& '.\.venv-gpu\Scripts\python.exe' -X utf8 -B -m scripts.sprint_checkpoint --output outputs/sprint/checkpoint
& '.\.venv-gpu\Scripts\python.exe' -X utf8 -B -m scripts.validate_real_paper --output outputs/sprint/gpu-bounded-table-v1 --device cuda --generation-profile bounded --representation-profile table_context_v1 --retrieval table_aware_v1 --context table_aware_v1 --full-rank-trace
```

The real runner refuses an existing output directory. For a separately
authorized rerun, choose a new output name rather than deleting an old index.
It measures free VRAM before each model stage, unloads only the task's Qwen,
releases BGE references/cache and verifies weakref disappearance, then samples
Ollama separately. Full-rank diagnostics score all 432 chunks with the same
five query embeddings but return only the baseline top50 to the retriever.
This is not an additional query policy or a second inference experiment.

Recovery started from clean integration branch at `12d11040a4b30841440610f0eb388c1d3c6da5bb` on 2026-11-06. Existing `.venv` and global Python are preserved. Replacement path is exactly:

`C:\Users\Praka\Downloads\research IQ  V2\researchgpt-pipeline-V2\.venv-gpu`

Native recovery and a bounded actual-paper end-to-end run are validated; scientific numerical correctness remains unestablished. Initial observed GPU: RTX 3050 6GB Laptop, driver 581.86; nvidia-smi reports 6,144 MiB total, 579 MiB used and 5,424 MiB free. This includes display/background usage; per-process WDDM memory is unavailable from nvidia-smi and will be reported separately from Ollama's size_vram.

Old environment: conda Python 3.10.18, `.venv` includes system site-packages, torch 2.5.1, NumPy 2.2.6, sentence-transformers 5.1.1, transformers 4.55.2, tokenizers 0.21.4, Chroma 1.1.1, onnxruntime 1.23.1 and onnxruntime-gpu 1.17.0 both present; FlagEmbedding absent. Conda metadata identifies MKL 2023.1.0 and intel-openmp 2023.1.0. Two distinct libiomp5md.dll files exist in conda Library/bin and torch/lib. Reproduction logs will establish the failing operation, not infer OOM from these files alone.

Selected: standard CPython 3.13.6 (non-free-threaded), isolated venv without system site packages, official torch 2.8.0 CUDA 12.6 wheel, minimal existing project dependencies. [Official PyTorch wheel commands](https://pytorch.org/get-started/previous-versions/) and [NVIDIA CUDA 12.6 driver requirements](https://docs.nvidia.com/cuda/archive/12.6.3/cuda-toolkit-release-notes/) support this choice; driver 581.86 exceeds the documented Windows requirement. Successful CUDA operations, not the wheel label alone, must validate compatibility.

No unsafe OpenMP override, DLL deletion, global install, model change, research collection deletion or source repository modification is authorized or needed.

## Reproduced diagnosis

`.venv/Scripts/python.exe -B -c "import torch"` and the existing real-paper smoke (redirecting only Chroma storage/project to a fresh isolated database) both terminate with **native exit 3**, stderr OpenMP Error #15. NumPy alone exits 0. No Python traceback is emitted because the native runtime terminates the process before CUDA allocation; this is not observed GPU OOM. Logs and exact subprocess argv: `outputs/recovery/legacy-diagnosis-01/diagnosis.json`.

Conflicting runtime candidates are distinct binaries:

| Path | Bytes | SHA-256 |
|---|---:|---|
| conda `Library/bin/libiomp5md.dll` | 2,047,000 | 0ad71f466d115d353dce94ba32b63e288f48198e89f551d46dcce461fedbd195 |
| conda `Lib/site-packages/torch/lib/libiomp5md.dll` | 1,613,680 | d9d66ed25f1a0ea725fa3a41b22cfd5d182c19dbe4771d9c90ca02ad7466f6a1 |

Old `torch/__init__.py` lines 155–218 explicitly add `sys.base_exec_prefix/Library/bin` through `os.add_dll_directory` alongside torch/lib. Thus trimming PATH did not isolate the DLL search. The inherited conda/native-wheel mixture is removed by using a standard-Python base and no system site-packages, without changing/deleting either old DLL. Co-installed ONNX CPU/GPU distributions are recorded, but not blamed for an isolated torch import that fails before Chroma/ONNX operations.

## Executed installation commands

All commands run from the V2 root; quotes preserve the exact path with spaces.

```powershell
& 'C:\Users\Praka\AppData\Local\Programs\Python\Python313\python.exe' -m venv 'C:\Users\Praka\Downloads\research IQ  V2\researchgpt-pipeline-V2\.venv-gpu'
.venv-gpu\Scripts\python.exe -m pip install -r requirements-recovery.in --index-url https://pypi.org/simple
.venv-gpu\Scripts\python.exe -m pip install sentence-transformers==5.1.1 --no-deps --index-url https://pypi.org/simple
```

The initial direct official-index torch download stalled and was interrupted. The optional checked-range downloader fetched exactly the same official CPython 3.13/Windows CUDA wheel; 2,915,433,376 bytes, expected/actual SHA-256 both `3aa7da5cc6b7df0e8c0754dea339bd31cd21b5620e84f53b2ac4be47e8bb2179`.

```powershell
.venv-gpu\Scripts\python.exe -B -m scripts.download_recovery_wheel
.venv-gpu\Scripts\python.exe -m pip install 'outputs/recovery/wheels/torch-2.8.0+cu126-cp313-cp313-win_amd64.whl' --index-url https://pypi.org/simple
```

Only .venv-gpu is written by these installers; downloaded wheels/logs stay ignored. The final validated full freeze and CUDA/BGE results are recorded below. The original .venv configuration remains unchanged.

## Validated native and embedding results

- `pip check`: no broken requirements. `scripts.probe_recovered_environment` imports NumPy, torch, sentence-transformers, ONNX and Chroma, and verifies an actual CUDA matrix product on RTX 3050 compute capability 8.6. CUDA build 12.6, driver 581.86. Loaded OpenMP runtime/stub paths belong only to .venv-gpu/torch/lib; no conda site-package inheritance. Probe's first reporting attempt used NumPy mode `dict` instead of installed API's `dicts`; corrected reporting-only error, then CUDA probe passed. This was neither OpenMP nor OOM.
- Runtime packages: torch 2.8.0+cu126; NumPy 2.2.6; sentence-transformers 5.1.1; transformers 4.55.2; tokenizers 0.21.4; Chroma 1.1.1; ONNX Runtime CPU 1.31.1. FlagEmbedding, MKL-service and ONNX Runtime GPU are not installed/required in this environment. `requirements-gpu.lock` pins all 108 installed distributions and official CUDA index.
- Cached BGE revision is unchanged (`5617a9f61b028005a4858fdac845db406aefb181`), with CLS pooling from its actual 1_Pooling/config.json, normalized embeddings, max_seq_length=1024. No new weights downloaded.
- First actual paper run: GPU embeddings **432 x 1024**, finite, norms 0.999756–1.000463; document encode including load/measurement 16,617.43 ms. Five actual query embeddings use the same model/encoder, each 1 x 1024. Fresh Chroma count 432, IDs and full metadata round-trip exact; separate control collection stays empty.
- First run collection `rgpt_v2_ca0fed38ca118dd985685839`, database `outputs/recovery/gpu-current-01/fresh-chroma`. No existing research collection was touched.
- BGE weak model reference becomes unreachable before Qwen. Exact PyTorch peak allocated/reserved: 2,783,155,200 / 2,814,377,984 bytes. After release: 8,519,680 / 16,777,216 bytes remain, not falsely reported as zero. Free GPU memory before BGE 5,351 MiB, after release/before Qwen 5,241 MiB. Remaining context/cache overhead and other applications are included in global nvidia-smi memory.
- Qwen's separate process reports size_vram 4,270,619,360 bytes; global sampled memory is reported separately. First Qwen response used 5,451 prompt tokens and exhausted 768 generated tokens (finish_reason=length). This is a new output-budget failure, not runtime conflict or GPU OOM. Raw response preserved and still rejected. A fresh run uses output_tokens=2048, with the same num_ctx=8192, model, retrieval and verifier; 5451+2048 fits the measured context window. Production default 768 remains unchanged.
- Genuine CPU BGE + GPU Qwen micro-check is guarded against insufficient host memory. First run measured only **0.44 GiB available host RAM** with Qwen resident; CPU loading was therefore marked UNAVAILABLE rather than attempting a multi-gigabyte allocation. Sequential GPU execution is the practical measured path. No unrelated applications were closed or global memory settings changed.

Raw snapshots, actual provider request/response, index IDs/metadata, and per-phase resources: `outputs/recovery/gpu-current-01/`. Later attempts use different fresh databases and collections; the final bounded attempt completes as recorded below.


## Successful final real-paper run

Command (exact recovered interpreter verified inside the runner):

```powershell
.venv-gpu\Scripts\python.exe -B -m scripts.validate_real_paper --output outputs/recovery/gpu-current-03-bounded --device cuda --context current --output-tokens 2048 --max-candidates 1 --cpu-check
```

The second uncapped 2048-token attempt also ended in length truncation, so the tested optional candidate-volume bound was added. Its JSON-schema regression failed before implementation and passes afterwards; default generation remains uncapped/768. The bounded diagnostic completed with stop: **5471 prompt / 1849 generated tokens**, same 8192 context window, no runtime errors, PARTIAL structured output. Raw actual candidates are verified without replay or repair. All attempted runs and failed packets are retained under outputs/recovery.

Final run: 432 x 1024 GPU embeddings; five actual query embeddings; new collection `rgpt_v2_13d597623a469d64fce2e90d` in `outputs/recovery/gpu-current-03-bounded/fresh-chroma`; initial count 0 -> 432; IDs, metadata and empty isolation control pass. GPU model weakref gone before Qwen; PyTorch live/reserved memory after release 8,519,680/16,777,216 bytes. Free GPU 5361 MiB before BGE, 5236 MiB after release, 1054 MiB with Qwen. PyTorch peak allocated/reserved 2,783,155,200/2,814,377,984 bytes. Ollama separate peak size_vram 4,270,619,360 bytes; global GPU sampled peak 4949 MiB (includes other processes). Process peak working set 4.111 GiB; host total 15.715 GiB. CPU micro-check remains UNAVAILABLE: only 1.132 GiB host memory available while Qwen is resident. No CPU BGE success or GPU OOM is claimed.

BGE encode including load/measurement 14.467 seconds; indexing 14.954 seconds; Ollama server 129.323 seconds; observed extraction stage including instrumentation 135.624 seconds; wrapper including revalidation, monitoring and cleanup 166.941 seconds. These are execution measurements, not a controlled speed comparison. Sampling can miss short global peaks; PyTorch peak counters exclude Ollama.

Actual BGE token lengths: min 3, median 7, p95 101.45, max 256, mean 25.30; none clipped at embedding limit 1024. These are BGE-tokenizer lengths, not estimates of Qwen tokens. Retrieval union 134 chunks; 67 delivered, 67 dropped, one partial. Context 2500 words. Actual Qwen usage is supplied by the service above.

Nine generated candidates: one qualitative future_scope excerpt returned; eight withheld, zero verified numerical tuples. Independently validated scientific accuracy is NOT established. Full classification and limitations: RECOVERY_REPORT.md.

## Reproduce from the validated lock

`requirements-gpu.lock` pins all 108 distributions in the tested Windows/CPython 3.13.6 environment. It includes the official CUDA wheel index and exact torch build; wheel hash above is independently checked by the optional downloader. Standard setup after creating the exact venv:

```powershell
.venv-gpu\Scripts\python.exe -m pip install -r requirements-gpu.lock
.venv-gpu\Scripts\python.exe -m pip check
.venv-gpu\Scripts\python.exe -B -m scripts.probe_recovered_environment
.venv-gpu\Scripts\python.exe -B -m pytest -p no:cacheprovider tests -q --junitxml=outputs/recovery/recovered-pytest.xml
```

If the single-stream CUDA transfer stalls, first use the checked-range downloader and install its verified wheel, then install the lock (the exact torch version is already satisfied). Scientific model files remain outside Git in the existing cache. Never use the original .venv for the recovered GPU path or a global pip command.

Final full suite: **75 passed, 0 failed, 0 skipped, 1 Starlette/AnyIO deprecation warning in 4.16s**. No dependency changes were made merely to suppress that warning. Both `.venv` and global Python remain unchanged. Raw execution/probe/install/test traces stay in ignored outputs; compact evidence is in docs/evidence/recovery_*.json. No push, merge, PR or 60-paper rerun.
