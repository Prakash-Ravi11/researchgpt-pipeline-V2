# Kaggle inference debugging and safe recovery — 2026-11-09

## A. Confirmed root cause and artifact integrity

Located the actual download at
`C:\Users\Praka\Downloads\rgpt-codex-debug-02.zip`.
It is 23680 bytes, SHA256
`48819f0182ed641129f5b5714a44dd408aba760704a1ca329b9ee5d39da45065`.
Outer and nested ZIP CRC checks pass. The nested result.zip and four loose files
contain byte-identical copies. All output-manifest file sizes/hashes validate.

| Original member | Bytes |
|---|---:|
| result.zip | 11880 |
| execution.json | 29520 |
| raw_response.txt | 1583 |
| candidates.json | 1668 |
| output-manifest.json | 708 |

Full SHA256 values and validation paths are recorded in
docs/evidence/kaggle_recovery_artifacts.json. The original raw response SHA is
`842dcf34f28772df33624991c0f76084160e1772576a2cd6436ed822459f4b39`.
Its exact bytes are copied into a deterministic fixture; neither the download nor
its raw/normalized artifacts are rewritten. Parsed raw equals saved candidates.

**All ten fields contain strings where evidence-ID objects are required.**
Full validation against the exact saved input schema yields 12 errors: 11 wrong
item types and one metrics maxItems violation. The metrics list has two labels,
but even a single label would remain invalid. The complete response is rejected;
no strings are mapped to IDs or silently removed. Cardinality one is the existing
bounded selection request, stated in both prompt and schema, not a request for
an exhaustive list of metric names. Missing/uncertain evidence can remain [].

The saved run confirms FAILED/ValidationError, 1776 prompt tokens, 349 generated,
EOS, 47.6566s loading, 34.9885s generation and 88.6949s total. It was not a token
limit or timeout failure. The original runner performed unconstrained HF greedy
generation and only then validated JSON Schema. Prompt/schema agree; the parser
faithfully preserves the generated strings. The mismatch originated during
generation. The local schema-constrained fix in c34420e was not in this run's
87e44b4 source snapshot and is retained, rather than rewritten.

The importer correctly rejects the actual failed result as
EXTRACTION_FAILED/remote_inference_not_completed even though result.zip exists.
Rejected candidates.json remains diagnostic data, not verified output. A replay
claiming COMPLETED still fails full schema validation. No scientific correctness
or independent extraction accuracy is established by these runs/fixtures.

Attempt01's CUDA130 binary error and ~120.84s runtime are user-reported; that
first-run artifact is not in the local download. They are not independently
verified here. Its reported native binary failure is separate from run02's
confirmed generation-format failure, GPU OOM and the older OpenMP import issue.
Sampling/TF warnings were nonfatal in the recorded generation and do not explain
the wrong JSON types. Greedy do_sample=False is explicit; no sampling profile
change was used. Child processes disable unused TF/Flax discovery.

## B. Existing changes and source reconciliation

Verified actual cwd, origin and feature/evidence-pipeline-integration. Started
clean at d581bcf (26 commits ahead of the local origin tracking ref): no unstaged
or staged changes, no unrelated work to overwrite. No remote fetch/assumption,
push, reset, merge or reference-repository write occurred.

| Layer | Evidence/state before this recovery |
|---|---|
| Original v2 package | ff00931a… manifest; code commit87e44b4; ID-only schema, unconstrained HF generate, bnb0.47.0 requirements |
| Original source notebook | Independently retained ff00931a…; direct code.zip read, venv/ensurepip, result01; no integrated bin staging |
| Prior local commits | c34420e adds schema-derived grammar/prompt, strict post-validation/import metadata; d581bcf adds tested v3 package/notebook handoff |
| Prior v3 notebook | Correct schema package SHA, but still direct ZIP access, venv/ensurepip and result01; runtime fixes absent |
| Hosted manual changes | User-described integrated bin staging, current interpreter, bnb0.50.2 upgrade and result02; exact hosted .ipynb not supplied |
| Saved run02 corroboration | Old code/input IDs, Torch2.11.0+cu130, bnb0.50.2, full raw/normalized failure and actual timings |

docs/evidence/kaggle_recovery_audit.json records every embedded-file comparison
against the original/v3 recorded Git snapshots, sanitized origin, initial status
and prior commits. Each archive has15 byte differences in migrated files, all
strictly CRLF/LF line endings; normalized contents match the recorded commit.
Inference runner bytes match exactly. Archive hashes cover their actual bytes;
no blanket byte-identical-Git claim is made. The earlier19-file c34420e/d581bcf inventory remains
in docs/QWEN_CONTRACT_FIX.md. This recovery preserves those commits and changes
only the missing staging/runtime/diagnostic workflow and focused regressions.

## C. Permanent corrections

- kaggle/bootstrap.py integrates exact manifest discovery, code.zip.bin transport
  restoration to code.zip, byte-length/SHA validation, fresh staging and safe
  archive extraction. A stale expanded code/ tree is never executable input.
  Both readable transports, if present, must match. Traversal, drive paths,
  symlinks, duplicate members and oversized payloads fail closed. No re-zipping
  of mounted source or historical manifest editing is used.
- kaggle/environment.py and the dedicated cu130 requirements/profile use
  Kaggle's interpreter with --target/--no-deps binary-wheel installation in a
  fresh working directory. Base Torch/NumPy are never installed or replaced.
  Active overlay versions/paths and transitive requirements are checked, with
  actual interpreter/CUDA records, GPU tensor and CUDA NF4 roundtrip checks,
  tensor release and measured free VRAM. Unsupported bases/overrides stop.
- The runner validates the complete tokenizer budget before model weights,
  records actual interpreter and active package versions, and checks a requested
  environment profile. Failed runs retain diagnostics/raw candidates. Missing
  package-inventory metadata cannot suppress the result artifact. The importer
  requires the requested profile metadata for new profiled inputs.
- scripts/build_recovery_notebook.py creates six ordered code cells from the
  validated packaged bootstrap and generates complete, identical cell replacement
  instructions. It uses attempt03, separate logs/reports, Output-browser debug
  ZIP downloads and no automatic reruns/deletion. Partial old venvs remain intact.
- scripts/inference_package.py adds the explicit kaggle-t4-cu130-v1 export
  profile and binds requirements hashes into runtime.json. The original cu126
  requirements stay available as historical configuration, clearly labeled.

The source-ID schema, semantic/numerical gate, offsets/version identity, model
revision/precision and frozen retrieval baseline are preserved. 28.4 EN-DE,
41.8 EN-FR Table2 and 41.0 EN-FR prose remain distinct. Human review is pending.
The exact recovery file inventory is recorded in the final handoff evidence.

## D. Executed tests and remaining limits

One complete checkpoint: **173 passed, 0 failed/skipped, 24.61s**, one existing
Starlette/AnyIO deprecation warning. Earlier overlapping targeted batch:41 passed
in21.92s. Exact per-test scope/interpreter: docs/evidence/kaggle_recovery_tests.json.

```powershell
$env:PYTHONPATH = (Resolve-Path outputs/qwen-contract/validation-deps).Path
& '.\.venv-gpu\Scripts\python.exe' -X utf8 -B -m pytest -p no:cacheprovider tests -q --tb=short --junitxml=outputs/kaggle-recovery/full-pytest.xml
```

Coverage includes the complete actual raw response/exact schema, valid metrics
ID proposal, strings, cardinality, foreign IDs, abstention/ambiguity, wrong
source/version/row/condition, raw preservation, failed/mismatched imports,
ZIP/bin staging/hash/path checks, environment guards/diagnostics, pre-weight
budget failure, generated notebook and existing downstream API/tuple tests.
Test doubles and source-backed fixtures are not live Qwen accuracy measurements.

All eight pinned overlay wheels were downloaded only and their default
requirements checked against saved run02 base plus the overlay under Linux/
Python3.13 markers. No dependency conflict found. Binary availability is not
clean-runtime GPU validation. No new inference, full60-paper run or frozen
evaluation rerun occurred. The new clean Kaggle preflight/model run is untested.

## E. Dependency environment and compatibility scope

| Component | Local executed tests | Saved run02 | Prepared next Kaggle profile |
|---|---|---|---|
| Python |3.13.6, exact .venv-gpu|Not recorded;3.13 user-reported|Actual interpreter recorded; compatible binary wheels required |
| Torch |2.8.0+cu126|2.11.0+cu130|Keep2.11.0+cu130 base; stop if different |
| Torch CUDA |12.6; no GPU test this task|13.0 in user report/build|Require13.0 and actual GPU/NF4 preflight |
| Transformers |4.55.2|4.55.2|4.55.2 overlay |
| bitsandbytes |Not installed|0.50.2|0.50.2 overlay |
| NumPy |2.2.6|1.26.4 metadata|Keep compatible base; do not replace |

The old execution did not record Python or torch.version.cuda explicitly; new
reports do. Package metadata alone does not prove a Python ABI or clean runtime.
The official Linux bnb0.50.2 wheel was inspected without installation: it contains
libbitsandbytes_cuda130.so, requires Python>=3.10, torch>=2.4,<3 and numpy>=1.17.
Its SHA/metadata are in kaggle_recovery_wheel.json; all eight wheel hashes and
requirement checks are in kaggle_recovery_overlay.json.
[Official v0.50.2 installation matrix](https://huggingface.co/docs/bitsandbytes/v0.50.2/en/installation)
includes CUDA13 and SM75/T4. The proposed overlay remains prepared, not proven on
every Kaggle base. Exact Torch/CUDA, dependency closure, loaded overlay paths,
actual free VRAM and GPU NF4 behavior must pass in the new session. There is no
blind torch downgrade/upgrade or local Windows environment change.

## F. Packaging decision

**A new coherent package and private dataset version are required.** Archived
source, runtime profile and requirements changed. Old v2/v3 ZIP/bin bytes and
JSON sets remain historical; their SHAs cannot authorize the new source. The
new canonical code.zip is copied byte-for-byte to code.zip.bin. Its manifest
continues describing code.zip; staging restores that name and verifies the same
bytes. The transport name alone never changes the archive or its hash.

After the tested code checkpoint, export to outputs/kaggle-recovery/offload-package-v4
and build kaggle/semantic_inference_recovery_v4.ipynb with its **actual generated
manifest SHA**, plus docs/KAGGLE_RECOVERY_CELLS.md. Final identities, preservation
hashes and a local bootstrap smoke are in docs/evidence/kaggle_recovery_package.json.
No package is patched in place. New remote execution remains NOT EXECUTED.

## G. Exact notebook update procedure

Follow **docs/KAGGLE_RECOVERY_CELLS.md**. It includes complete code and recognizable
old first lines for every cell, REPLACE/ADD instructions, immediate placement,
execution order, success signals and stop conditions. It is generated from the
same cells as the new notebook, with the retained actual SHA, not a placeholder.

Before restarting an existing session, run its provided archival-only cell and
download attempt01/02 if not already saved. /kaggle/working is ephemeral; only
the downloaded02 archive has been verified locally. Preserve the original
hosted notebook/version. Prefer importing the new notebook as a private copy
instead of mixing exploratory cells into the corrected flow. If editing a copy,
disable the old standalone staging and base bnb upgrade cells as instructed.

Upload exactly packet.json, request.json, runtime.json, input-manifest.json and
**code.zip.bin** from v4 as a new private version of the user-provided dataset
idealwizard007/researchgpt-v2-inference-input. Attach that version to the private
notebook. The known mount is user-provided; the bootstrap discovers the actual
matching path under /kaggle/input rather than assuming a version/mount layout.
No remote upload, notebook mutation or publication is performed by this task.

## H. One controlled next attempt and trusted local import

Select T4 x2, physical0 and Internet. Run configuration, integrated staging,
overlay/preflight, inspection, then inference once. READY is required before
inference. The result path is /kaggle/working/rgpt-result-03. On any setup/native/
schema error, stop and use only the diagnostics cell; do not repair/retry Qwen.
Download rgpt-codex-debug-03.zip via Output browser, then stop the GPU session.
The debug archive retains original result bytes and selected setup/input identity
reports. An archive or EOS alone never proves inference/schema/scientific success.

The final handoff records the actual new manifest SHA and commands to unpack the
returned nested result.zip into a fresh local directory, validate against the
retained local input and run scripts.inference_package import. A COMPLETED remote
proposal may still become WITHHELD/AMBIGUOUS/UNAVAILABLE locally. Accepted source
tuples remain needs_human_review. No independent accuracy claim is made.
