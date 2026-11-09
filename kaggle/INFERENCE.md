# Semantic inference export, Kaggle execution and trusted local import

Current contract-fix artifact: outputs/qwen-contract/inference-input-v3.zip,
unpacking to outputs/qwen-contract/offload-package-v3. It is private input, not
a Kaggle execution result. docs/evidence/qwen_contract_package.json records its
trusted manifest SHA and code commit. The commands
below reproduce it; choose a fresh output name if the directory already exists.

Status: the user reports the original Qwen3-8B job generated 349 tokens/EOS but
failed schema validation. **The corrected job is NOT EXECUTED on Kaggle.** The
full failed output has not been supplied locally. No remote notebook URL/ID is
invented. See [the diagnosis and tests](../docs/QWEN_CONTRACT_FIX.md). Original
v2 input files/manifest/archive and the older notebook are preserved.

## Upload checklist for the prepared package

Upload these five files from `outputs/qwen-contract/offload-package-v3`
as one **private Kaggle dataset**, preserving the file names:

| File | Purpose |
|---|---|
| packet.json | Selected evidence, source IDs, locations and relations |
| request.json | Exact messages, schema and schema-decoding contract |
| runtime.json | Pinned model, generation, quantization and baseline |
| code.zip | Required source code and dependency pins |
| input-manifest.json | Input version, identity, hashes and exact sizes |

Separately, import [semantic_inference_contract_v3.ipynb](semantic_inference_contract_v3.ipynb) as the
notebook. It is not a dataset input and has no executed cells or saved outputs.
The convenience archive `outputs/qwen-contract/inference-input-v3.zip` contains the
five dataset files; extract it locally if using that download. No PDF, weights,
database, credentials, full repository or other output directories are needed.

The package ID and retained local input-manifest SHA256 are in
docs/evidence/qwen_contract_package.json. The new notebook embeds that retained
value. A fresh export requires updating it
from the trusted local exporter; do not replace it with a remotely computed hash.

## 1. Export locally

From the V2 repository root with the exact isolated interpreter:

```powershell
& '.\.venv-gpu\Scripts\python.exe' -X utf8 -B -m scripts.inference_package export --retrieval-run outputs/accuracy/gpu-api-selection-v1/execution.json --model qwen3-8b --output outputs/qwen-contract/offload-package-v3
```

Choose a new output directory on every export. The optional retrieval-run
reuses the saved actual five-query IDs/table links without embedding/inference.
The exporter prints package_id and **input_manifest_sha256**; retain both locally.
Qwen3-14B is another explicit export choice, with its pinned revision and higher
free-memory requirement. Do not silently substitute models after export.

Files: packet.json (selected evidence, source IDs/locations/relationships),
request.json (exact messages/output schema), runtime.json (model revision,
NF4/FP16, non-thinking/generation and original Qwen2.5 baseline configuration),
code.zip, input-manifest.json (file sizes/SHA256, document SHA and V2 commit).
Only selected source blocks and necessary verification context are included;
full corpus, PDF, model files, credentials and vector database are excluded.
The packet still contains source text: use only legitimately shareable material
and keep the Kaggle dataset/notebook private. There is no automatic upload.

## 2. Create and run the private T4 notebook

1. Create a private dataset containing the five files above. Confirm its privacy.
2. Create a Python notebook and import `kaggle/semantic_inference_contract_v3.ipynb`. Confirm
   the notebook is private independently of the dataset. Attach the private dataset.
3. Under **Settings > Accelerator**, select **GPU T4 x2** if available. Enable
   Internet for the pinned public package/model downloads. If the account cannot
   start a T4 session, keep execution marked NOT EXECUTED and retain that blocker.
4. Run cells in order. The bootstrap searches the actual `/kaggle/input` tree for
   exactly one manifest matching the retained local SHA and prints its real path.
   No dataset slug, individual mount path, notebook URL or notebook ID is assumed.
   It rejects missing/duplicate matching inputs or modified files before extracting
   code. Work directories are created by the notebook under `/kaggle/working`.
5. The setup cell creates an isolated environment, installs torch 2.8.0+cu126
   and the existing pinned requirements-extraction.txt, and runs pip check.
   Those pins are prepared but have not been remotely installation-tested.
6. Inspect the displayed physical GPUs, actual memory and requested configuration.
   The inference cell invokes the packaged runner once with physical device 0,
   the discovered input path and retained SHA. Preserve errors and outputs; the
   notebook refuses to overwrite an existing result directory.
7. Download the resulting `result.zip` from the notebook Output browser, retain
   the actual execution status, and stop the GPU session. Setup failures before
   the runner starts may produce only a notebook error, not an archive.

Current UI references: [Kaggle notebook documentation](https://www.kaggle.com/docs/notebooks),
[dataset privacy documentation](https://www.kaggle.com/docs/datasets), and
[NVIDIA's Kaggle GPU setup](https://docs.nvidia.com/datascience/deployment/latest/platforms/kaggle/).
Availability and quota depend on the account; no remote resource has been created.

T4x2 means two separate 16 GB devices. The runner masks **one** physical GPU and
checks its actual free memory (9/12 GB planning guards for the prepared 8B/14B
configurations). No automatic pooling, CPU fallback, input truncation or model
change. Qwen model ID/revision, NF4 double quantization/FP16 compute,
enable_thinking=false, seed 42, 8192 window and 2048 output cap are recorded.
The supplied message content is unchanged; the model's chat template wraps it.

The original Ollama baseline is retained in runtime.json. The corrected runner
uses schema-derived token-prefix constraints with pinned lm-format-enforcer and
independent JSON Schema post-validation. It never converts labels to IDs or
truncates invalid candidates. Record this decoder change; no pure model-only
comparison is claimed. Full evidence fits the pinned tokenizer budget: 3676
prompt tokens plus the unchanged 2048 output cap within the 8192-token window.

## 3. Return results, including failures

Download `result.zip`. It contains raw_response.txt, candidates.json,
execution.json and output-manifest.json. Actual token counts, finish state,
load/generation/runtime, device/memory and package versions are recorded when
available. Failure artifacts are retained; incomplete/schema-invalid generation
does not become a successful candidate set. The notebook performs inference,
**never scientific verification**. No automatic public publication.

## 4. Verify locally

Unpack result.zip into a new local directory, preserving the raw bytes. Import
using the original trusted input and the retained local input-manifest SHA:

```powershell
& '.\.venv-gpu\Scripts\python.exe' -X utf8 -B -m scripts.inference_package import outputs/qwen-contract/offload-package-v3 outputs/qwen-contract/downloaded-result-v3 --expected-input-sha256 TRUSTED_LOCAL_MANIFEST_SHA --output outputs/qwen-contract/imported-result-v3
```

The importer checks input/output manifests, model/config/document identity,
schema/source-ID authorization and raw/normalized equality, then applies the
trusted local source/semantic/range/ownership gate. Raw output is copied unchanged
into the new import directory. A remote claimed verdict has no authority.
Hashes detect changes; they do not authenticate the remote author's identity.

For the FastAPI endpoint, register the trusted local input first:

```powershell
& '.\.venv-gpu\Scripts\python.exe' -X utf8 -B -m scripts.inference_package register outputs/qwen-contract/offload-package-v3 --store data/inference-inputs
```

POST `/api/inference/import` with project_id, returned package_id and
result_archive_base64 containing result.zip. The server reads only its registered
input, retains the uploaded result under data/inference-results, and returns the
normal ExtractedPaper contract. It never accepts a replacement trusted packet
from the remote response. Accepted/withheld/ambiguous/unavailable/failed states
and source refs are exposed; human_review remains independent.
