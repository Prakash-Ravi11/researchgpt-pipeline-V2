# Semantic inference export → Kaggle → trusted local import

Status in this sprint: **NOT EXECUTED on Kaggle**. The export/import/HTTP path
passes controlled round-trip tests; no connected notebook or credentials were
supplied. No expensive local inference was repeated. The older experimental
runner remains available; use this versioned workflow for semantic bundles.

## 1. Export locally

From the V2 repository root with the exact isolated interpreter:

```powershell
& '.\.venv-gpu\Scripts\python.exe' -X utf8 -B -m scripts.inference_package export --retrieval-run outputs/accuracy/gpu-api-selection-v1/execution.json --model qwen3-8b --output outputs/semantic/offload-package
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

## 2. Bootstrap a private Kaggle GPU notebook

Mount those five files privately under `/kaggle/input/rgpt-inference`. Enable
a supported GPU and internet for public package/model downloads, or mount
permitted immutable dependencies/models. Copy the **trusted local manifest
SHA** into the bootstrap cell, rather than obtaining a replacement SHA remotely:

```python
from pathlib import Path
import hashlib, json, zipfile

rgpt_input = Path('/kaggle/input/rgpt-inference')
rgpt_expected_sha = 'PASTE_THE_TRUSTED_LOCAL_INPUT_MANIFEST_SHA256'
assert hashlib.sha256((rgpt_input/'input-manifest.json').read_bytes()).hexdigest() == rgpt_expected_sha
rgpt_manifest = json.loads((rgpt_input/'input-manifest.json').read_text())
assert set(rgpt_manifest['files']) == {'packet.json','request.json','runtime.json','code.zip'}
for name, entry in rgpt_manifest['files'].items():
    content = (rgpt_input/name).read_bytes()
    assert len(content) == entry['bytes']
    assert hashlib.sha256(content).hexdigest() == entry['sha256']
rgpt_code = Path('/kaggle/working/rgpt')
with zipfile.ZipFile(rgpt_input/'code.zip') as archive:
    assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in archive.namelist())
    archive.extractall(rgpt_code)
```

In notebook shell cells, create a separate environment (do not alter the base
Kaggle Python). The candidate pins are prepared, not remotely installation-tested:

```bash
python3 -m venv /kaggle/working/rgpt-inference-env
/kaggle/working/rgpt-inference-env/bin/python -m pip install torch==2.8.0+cu126 --index-url https://download.pytorch.org/whl/cu126
/kaggle/working/rgpt-inference-env/bin/python -m pip install -r /kaggle/working/rgpt/kaggle/requirements-extraction.txt
/kaggle/working/rgpt-inference-env/bin/python -m pip check
cd /kaggle/working/rgpt
/kaggle/working/rgpt-inference-env/bin/python -m kaggle.run_inference --input /kaggle/input/rgpt-inference --expected-input-sha256 TRUSTED_LOCAL_MANIFEST_SHA --device 0 --output /kaggle/working/rgpt-result-01
```

T4x2 means two separate16GB devices. The runner masks **one** physical GPU and
checks its actual free memory (9/12GB planning guards for the prepared8B/14B
configurations). No automatic pooling, CPU fallback, input truncation or model
change. Qwen model ID/revision, NF4 double quantization/FP16 compute,
enable_thinking=false, seed42,8192 window and2048 output cap are recorded.
The supplied message content is unchanged; the model's chat template wraps it.

The original Ollama baseline is retained in runtime.json. Remote Transformers
greedy generation with schema post-validation differs from Ollama's constrained
decoder; record that configuration difference rather than claiming a pure
model-only comparison. Complete evidence must fit the actual tokenizer budget.

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
& '.\.venv-gpu\Scripts\python.exe' -X utf8 -B -m scripts.inference_package import outputs/semantic/offload-package outputs/semantic/downloaded-result --expected-input-sha256 TRUSTED_LOCAL_MANIFEST_SHA --output outputs/semantic/imported-result
```

The importer checks input/output manifests, model/config/document identity,
schema/source-ID authorization and raw/normalized equality, then applies the
trusted local source/semantic/range/ownership gate. Raw output is copied unchanged
into the new import directory. A remote claimed verdict has no authority.
Hashes detect changes; they do not authenticate the remote author's identity.

For the FastAPI endpoint, register the trusted local input first:

```powershell
& '.\.venv-gpu\Scripts\python.exe' -X utf8 -B -m scripts.inference_package register outputs/semantic/offload-package --store data/inference-inputs
```

POST `/api/inference/import` with project_id, returned package_id and
result_archive_base64 containing result.zip. The server reads only its registered
input, retains the uploaded result under data/inference-results, and returns the
normal ExtractedPaper contract. It never accepts a replacement trusted packet
from the remote response. Accepted/withheld/ambiguous/unavailable/failed states
and source refs are exposed; human_review remains independent.
