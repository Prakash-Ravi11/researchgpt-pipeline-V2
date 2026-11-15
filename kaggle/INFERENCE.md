# Private Kaggle recovery v4

**Experimental recovery template.** Local bootstrap and CPU regressions cover
the committed version. Clean Kaggle environment/GPU execution, end-to-end
inference and scientific validation remain pending. Later experimental/audited
notebook changes require repository review and tests before integration. The
private packages referenced below stay local and require separate preparation
for another teammate's checkout. See the [review status](../docs/REVIEW_STATUS.md).

The actual second Qwen3-8B run generated349 tokens/EOS but failed the source-ID
schema in all ten fields. See [the artifact/audit report](../docs/KAGGLE_RECOVERY_REPORT.md).
The v4 corrected inference is **NOT EXECUTED**. Original v2/v3 inputs, manifests,
notebooks and both historical attempts must be preserved.

## Prepared files and exact cell code

Canonical input: `outputs/kaggle-recovery/offload-package-v4`.
Transport download: `outputs/kaggle-recovery/inference-input-v4.zip`.
Notebook: [semantic_inference_recovery_v4.ipynb](semantic_inference_recovery_v4.ipynb).
Complete replacement cells: [KAGGLE_RECOVERY_CELLS.md](../docs/KAGGLE_RECOVERY_CELLS.md).
Actual package ID, code commit and retained manifest SHA:
`docs/evidence/kaggle_recovery_package.json`; the notebook embeds the same SHA.

Upload exactly these five files as a **new private dataset version**:

| File | Purpose |
|---|---|
| packet.json | Unchanged selected source blocks, IDs, relations and provenance |
| request.json | Exact schema-bound messages and output/decoder contract |
| runtime.json | Pinned model, generation, quantization and cu130 environment profile |
| input-manifest.json | Exact input identities, byte sizes and hashes |
| code.zip.bin | Byte-identical transport copy of the newly generated code.zip |

The canonical directory also retains code.zip for local verification. The
transport archive contains the five upload files above. The manifest deliberately
still describes code.zip, not code.zip.bin. Integrated staging restores its
original name and verifies the exact bytes before any packaged code runs. An
expanded mounted code/ directory is ignored; its files are never re-zipped.

Use the user-provided private dataset `idealwizard007/researchgpt-v2-inference-input`.
The previous mount was `/kaggle/input/datasets/idealwizard007/researchgpt-v2-inference-input/`.
The bootstrap discovers the actual matching manifest under `/kaggle/input` and
prints the real mounted/staged paths. Attach the new version, not an old one.
No upload, publication or remote notebook mutation was performed locally.

## Execution order and stop rules

Before ending an existing session, use the archival-only cell in the exact-cell
guide to save/download attempts01/02. `/kaggle/working` is ephemeral; only the
local downloaded02 archive has been verified. Preserve the old notebook/version.
Then import the new notebook as a fresh private copy/session. T4x2 is two separate
GPUs; choose physical0 and enable Internet. Follow six code cells in order:

1. Configuration with actual retained SHA and attempt03.
2. Integrated manifest discovery, verified bin staging and safe source extraction.
3. Existing interpreter plus private working-directory overlay and GPU preflight.
4. Display actual GPUs and pinned configuration.
5. One inference to `/kaggle/working/rgpt-result-03`.
6. Preserve/debug ZIP and download through the Output browser.

Remove no historical files. Disable old exploratory staging/base-install cells
in an edited copy as the guide specifies. No later cell may reset rgpt_input to
the mounted directory. Existing staging/setup/result03 paths cause a stop, never
a delete or overwrite. After bootstrap/setup failure, run only the diagnostics
cell manually; do not advance to inference or loop through environment fixes.

The environment requires the saved base Torch2.11.0+cu130/CUDA13.0. It does not
install or replace Torch or NumPy and does not invoke venv/ensurepip. Eight exact
binary-wheel pins are installed only into `rgpt-runtime-deps-03`, with --no-deps.
The new requirements-kaggle-cu130.txt/profile includes bnb0.50.2 and schema decoder
pins. Active overlay paths/versions, transitive requirements, interpreter, GPU
matrix operation, actual NF4 CUDA roundtrip and free VRAM after release must pass.
This profile is prepared from the saved environment, not universally compatible
or clean-runtime tested. A different base stops for review without PyTorch changes.

Qwen3-8B/revision b968826d9c46dd6066d109eabc6255188de91218, NF4/FP16/double-quant,
non-thinking, seed42,8192 context and2048 output cap remain. The full prompt is
validated before weights; no evidence or output is truncated/repaired. Existing
schema-derived token constraints and independent schema/local evidence checks
remain. Generation/EOS/schema success is not independent scientific accuracy.

Download the printed `rgpt-codex-debug-03.zip` from Output, including failures,
then stop the GPU session. FileLink is not required. It includes available raw
result files unchanged, the original nested result.zip and setup/input-identity
diagnostics. Missing result.zip after setup failure is explicitly not success.

## Reproduce export/build locally, only when needed

Choose fresh destinations if these paths already exist; never overwrite history.
The supplied ready artifacts do not require another export.

```powershell
& '.\.venv-gpu\Scripts\python.exe' -X utf8 -B -m scripts.inference_package export --retrieval-run outputs/accuracy/gpu-api-selection-v1/execution.json --model qwen3-8b --environment-profile kaggle-t4-cu130-v1 --output outputs/kaggle-recovery/offload-package-v4
& '.\.venv-gpu\Scripts\python.exe' -X utf8 -B -m scripts.build_recovery_notebook --input outputs/kaggle-recovery/offload-package-v4 --notebook kaggle/semantic_inference_recovery_v4.ipynb --instructions docs/KAGGLE_RECOVERY_CELLS.md --attempt 03
```

Code changes require a newly committed/tested source snapshot, new archive,
coherent JSON/manifest set, bin copy and actual-SHA notebook. Neither ff00931a...
(v2) nor f4364f63... (v3) authorizes v4. Hashes establish byte integrity, not remote
authorship. Keep all inputs/results private and share only permitted source text.

## Import the actual returned result locally

Use the original retained local v4 input. The future download path is not known;
Read-Host asks for its actual path instead of inventing one. Fresh output paths
below are created by the tools and must not already exist.

```powershell
$rgptRecovery = Get-Content docs/evidence/kaggle_recovery_package.json -Raw | ConvertFrom-Json
$rgptDownloadedDebug = Read-Host 'Full local path to downloaded rgpt-codex-debug-03.zip'
& '.\.venv-gpu\Scripts\python.exe' -X utf8 -B -c "import sys,zipfile; from pathlib import Path; from pipeline.inference.packages import unpack_result,MAX_RESULT_BYTES; z=zipfile.ZipFile(sys.argv[1]); assert z.getinfo('result.zip').file_size<=MAX_RESULT_BYTES; unpack_result(z.read('result.zip'),Path(sys.argv[2])); z.close()" $rgptDownloadedDebug outputs/kaggle-recovery/downloaded-result-03
& '.\.venv-gpu\Scripts\python.exe' -X utf8 -B -m scripts.inference_package import outputs/kaggle-recovery/offload-package-v4 outputs/kaggle-recovery/downloaded-result-03 --expected-input-sha256 $rgptRecovery.input_manifest_sha256 --output outputs/kaggle-recovery/verified-result-03
```

If result.zip is absent, retain setup diagnostics and stop. Import checks both
manifests, exact requested model/config/decoder/environment identity, completion,
raw-normalized equality and authorized IDs, then the existing trusted local
source/semantic/range/ownership gate. Read its structured status and withheld/
ambiguous reasons. A remote claim of VERIFIED is ignored; failed/mismatched
archives remain EXTRACTION_FAILED. Accepted source tuples still need human review.
The registered-input FastAPI import endpoint remains compatible on port8000.
