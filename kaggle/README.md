# Private, reproducible accuracy jobs

**Experimental development setup.** Clean Kaggle end-to-end inference and
scientific validation remain pending. Later experimental/audited notebook
changes require repository review and tests before integration. See the
[teammate review status](../docs/REVIEW_STATUS.md).

Current recovery: [INFERENCE.md](INFERENCE.md), [actual artifact report](../docs/KAGGLE_RECOVERY_REPORT.md)
and [complete next cell code](../docs/KAGGLE_RECOVERY_CELLS.md). Use the prepared
semantic_inference_recovery_v4.ipynb and its new private manifest/bin transport.
The actual run02 failed schema validation after generation; v4 has not run on
Kaggle. Original/v3 notebooks and the commands/status below are retained as
historical pre-run configurations, not current execution status.

**Prepared, not executed on Kaggle.** This session has no Kaggle connector,
CLI module, credential file or credential environment configuration. No data
was uploaded. Windows `.venv-gpu`, the old `.venv` and global Python are intact.

Generate inputs locally with the exact repository interpreter:

```powershell
& '.\.venv-gpu\Scripts\python.exe' -X utf8 -B -m scripts.prepare_accuracy_job --retrieval-run outputs/accuracy/gpu-api-selection-v1/execution.json --output outputs/accuracy/matched-reviewed-scope-package
```

The exporter makes code.zip, packet.json, input-manifest.json and SHA256s.
The matched export reuses the actual API run's query IDs/table links without
another embedding or model call. Its messages are checked against the retained
API request before comparison. An export without --retrieval-run is explicitly
labeled an all-source development packet and is not a matched local baseline.
No PDF, weight, database, credential or virtual environment enters code.zip.
**packet.json contains source text**, so keep it private just like the source.
Review redistribution rights before any transfer; this script neither uploads
nor creates a public dataset. The PDF must be separately mounted privately as
`/kaggle/input/rgpt-private-papers/document.pdf` with the manifest's exact hash.
The previously inspected Attention paper is development data, never held-out.

Use a private notebook with a supported NVIDIA GPU and internet for public
package/model downloads, or privately mounted immutable model assets. Start in
the extracted repository. Keep parser and model environments separate:

```bash
python3 -m venv /kaggle/working/rgpt-parser
/kaggle/working/rgpt-parser/bin/python -m pip install torch==2.8.0+cu126 --index-url https://download.pytorch.org/whl/cu126
/kaggle/working/rgpt-parser/bin/python -m pip install -r kaggle/requirements-parser.txt
/kaggle/working/rgpt-parser/bin/python -m pip check
/kaggle/working/rgpt-parser/bin/python -m kaggle.run_accuracy parser --manifest /kaggle/input/rgpt-private-code/input-manifest.json --device 0 --output /kaggle/working/parser-run-01
```

Docling 2.148.0 / TableFormer ACCURATE / native-cell matching is the selected
remote parser **candidate**. It preserves exported table/header/cell/bbox JSON
as EXTERNAL_PROPOSAL, not trusted source quotations. OCR is enabled only when
native page text is missing/sparse; no VLM is silently enabled. Baseline and
native geometry run on identical hash-checked input. Model asset SHA256s,
actual dependencies, GPU and errors are recorded. Retain parser-assets with
its manifest for replay. Independent structural accuracy stays null until
review. This dependency set is pinned but not remotely installation-tested.

```bash
python3 -m venv /kaggle/working/rgpt-extract
/kaggle/working/rgpt-extract/bin/python -m pip install torch==2.8.0+cu126 --index-url https://download.pytorch.org/whl/cu126
/kaggle/working/rgpt-extract/bin/python -m pip install -r kaggle/requirements-extraction.txt
/kaggle/working/rgpt-extract/bin/python -m pip check
/kaggle/working/rgpt-extract/bin/python -m kaggle.run_accuracy extractor --packet /kaggle/input/rgpt-private-code/packet.json --model qwen3-8b --device 0 --output /kaggle/working/qwen3-8b-run-01
# Optional second candidate, sequentially after the first process exits:
/kaggle/working/rgpt-extract/bin/python -m kaggle.run_accuracy extractor --packet /kaggle/input/rgpt-private-code/packet.json --model qwen3-14b --device 0 --output /kaggle/working/qwen3-14b-run-01
```

Qwen3 candidates are Apache-2.0, pinned to the model commits in models.json,
NF4 double quantization with FP16 compute, non-thinking, greedy, seed42,
8192 window and2048 output cap. Both consume the **same immutable packet**,
prompt and selection schema; actual prompt token counts vary by tokenizer.
T4s are separate16GB devices: the runner masks exactly one physical device,
never treats two T4s as a32GB pool and never automatically shards. Free-memory
guards9/12GB are planning minima, not promises of fit. OOM/config/schema/length
errors fail explicitly. This is a model/configuration comparison, not proof
that either beats local Qwen2.5 Q4_K_M. Different quantizers are recorded.

Export execution.json, raw_response.txt, candidates.json, parser proposal JSON,
package/asset manifests and hashes. Preserve failures too. Verify package and
model artifacts before reuse. Reapply the host gate locally using the trusted
**local** packet and its locally recorded SHA, not a packet modified remotely:

```powershell
& '.\.venv-gpu\Scripts\python.exe' -X utf8 -B -m scripts.replay_accuracy_packet outputs/accuracy/matched-reviewed-scope-package/packet.json downloaded-candidates.json --expected-packet-sha256 TRUSTED_LOCAL_PACKET_SHA256 --output outputs/accuracy/replayed-result.json
```

The same bundle/span/source/version verifier runs on replay. Raw generation,
schema compliance, source alignment and independent tuple accuracy are separate
outcomes. The12 existing annotations need independent review (reviewer, date,
verdict, source/scope confirmation); they remain outside scoring until then.
In the current packet EN-DE/EN-FR are unresolved dataset/condition labels.
No larger model can promote those IDs to a verified complete tuple without a
source-supported, reviewed benchmark/condition mapping; do not use an LLM
selection success as a substitute for that engineering and review step.
No larger evaluation or public artifact publication is triggered by these jobs.
