# Qwen3 selection contract correction — 2026-11-09

The user reported a completed Qwen3-8B Kaggle generation (349 generated tokens,
EOS) whose metrics field was `["BLEU score", "training cost"]`. Generation
completion is distinct from schema compliance and scientific verification.
The reported response remains invalid and is never converted to evidence IDs.

## Diagnosis

- The saved v2 input's selection prompt and schema agree: at most one object
  containing only an authorized evidence_id per field. The schema is correct.
- `parse_object` preserves the reported strings. It neither created the mismatch
  nor mapped the labels to IDs. Reproduction yields maxItems and item-type errors.
- The Hugging Face adapter only supplied messages to `model.generate`; it did
  not consume output_schema during generation. JSON Schema was applied afterward.
  This was unconstrained greedy generation, despite the structured selection
  contract used on the Ollama path. The prompt did not include the exact schema.
- The direct failure is model noncompliance. The engineering gap is missing
  schema-aware generation in the adapter, rather than a permissive parser or a
  reason to weaken the schema/gate. EOS cannot establish a valid response.

The complete failed raw response/result package was not located in the supplied
workspace. `tests/fixtures/qwen3_metrics_contract_failure.json` records the exact
user-reported metrics excerpt and explicitly labels the other test fields as
empty-array scaffolding. The reported token count is not independently measured
here. The original v2 inputs and archive are hashed before/after and untouched;
no saved failed output is edited or substituted.

## Correction

`pipeline/inference/structured.py` derives an explicit prompt contract and a
token-prefix grammar from the unchanged source-selection JSON Schema. The
grammar permits only the required fields, empty arrays or single ID objects,
and the exact field-specific authorized IDs. JSON member order is fixed to the
schema order, a valid subset of the schema. Unsupported schema shapes fail
closed; no unconstrained fallback or output repair exists.

The pinned LM Format Enforcer 0.11.3 Transformers integration supplies token
filtering through prefix_allowed_tokens_fn. A deterministic test exposed its
JsonSchemaParser maxItems=0 first-item edge case. This implementation compiles
the small finite selection schema to its RegexParser instead, including explicit
empty-only arrays. No installed library files are patched.

The exact schema appears in the system prompt with repeated enum definitions
deduplicated through JSON Schema $defs/$ref. Expanding those references produces
the original schema exactly. This preserves complete source evidence and IDs
while fitting the existing context/output budgets. An initial uncompressed
prompt measured 7365 tokens and was rejected before export; no truncation or
budget increase was used. Model/revision, quantization, seed and non-thinking
configuration remain the prepared Qwen3-8B baseline for this offload route.

New requests record response_contract with the full schema hash, decoder version
and grammar identity. Validation checks prompt/schema agreement; returned
execution metadata must match that contract before local import. That metadata
remains untrusted and never authorizes scientific facts. Immutable legacy inputs
remain readable. Newly exported input manifests cover the new request/code.

The runner still preserves raw output and schema-invalid normalized candidates
with FAILED status. Even a test generator deliberately ignoring the mask cannot
turn invalid EOS output into a successful result. Independent post-validation
and the existing local provenance/numerical gate remain mandatory and unchanged.
No label-to-ID lookup, fabricated ID, candidate truncation, retry or random
association is performed. Chat-template text is tokenized with
add_special_tokens=False as required for already formatted messages.

## Validation and artifacts

The local decoder dependencies were installed only into the ignored
outputs/qwen-contract/validation-deps directory, not either virtual environment
or global Python. Reproduce deterministic checks with the exact .venv-gpu Python
and that directory on PYTHONPATH, or install the project's inference extra in
an isolated test environment. Remote pins are in kaggle/requirements-extraction.txt.

Tests cover the reported labels, a single plain string, two valid IDs, unknown
IDs, extra values, wrong field IDs, empty-only fields, incomplete responses,
unsupported schema shapes, prompt/schema equivalence, metadata mismatch, an
actual-runner CPU fixture and a source-backed positive import/gate fixture.
Positive acceptance remains needs_human_review, not independent accuracy.

One complete suite: **156 passed, 0 failed/skipped, 47.31 seconds**, one dependency
deprecation warning. 44 overlapping targeted checks passed before prompt enum
compression. Exact per-test evidence is docs/evidence/qwen_contract_tests.json.
The pinned actual Qwen tokenizer measures **3676 prompt tokens + 2048 output**
within the unchanged 8192-token window. Its token-prefix callback accepts empty
and source-backed ID fixtures and rejects the reported label response. Evidence:
docs/evidence/qwen_contract_tokenizer.json. No weights were loaded or GPU used.

After validated fix commit c34420e669eff47f631e62932dd53f4a17c591ce, exported
separate private package rgpt_be863f4321b004cdccc7f102 to
outputs/qwen-contract/offload-package-v3, with convenience archive
outputs/qwen-contract/inference-input-v3.zip. The handoff notebook is
kaggle/semantic_inference_contract_v3.ipynb. Exact package/code/manifest identities
and original-input preservation checks are in docs/evidence/qwen_contract_package.json.
The retained input-manifest SHA256 is
f4364f63743f927be904025b3c404045a3fa56a2e89e14e6fa408bbd7e72980f.
Upload only its packet.json, request.json, runtime.json, code.zip and
input-manifest.json as private inputs, and import the new notebook separately.
See kaggle/INFERENCE.md. The original v2 manifest SHA remains
ff00931afc4c49ccb7f684dd0674027fb0bfac9178f3cf08797537b6d4f5f3ff.

No fixed model inference, remote retry, upload, publication, push or full-corpus
evaluation is performed. The next controlled Kaggle run must report its actual
outcome; an output passing the schema still requires the local evidence gate.

## Exact changed files relative to 7c5f531

- README.md
- docs/BLOCKERS.md
- docs/PROGRESS.md
- docs/QWEN_CONTRACT_FIX.md
- docs/TESTING.md
- docs/evidence/qwen_contract_package.json
- docs/evidence/qwen_contract_tests.json
- docs/evidence/qwen_contract_tokenizer.json
- kaggle/INFERENCE.md
- kaggle/requirements-extraction.txt
- kaggle/run_inference.py
- kaggle/semantic_inference_contract_v3.ipynb
- pipeline/extraction/selection.py
- pipeline/inference/packages.py
- pipeline/inference/structured.py
- pyproject.toml
- tests/fixtures/qwen3_metrics_contract_failure.json
- tests/test_inference_packages.py
- tests/test_qwen_structured_contract.py

The private generated files under outputs/qwen-contract are ignored, not committed.

Primary implementation references: [Transformers prefix constraints](https://huggingface.co/docs/transformers/v4.55.2/en/main_classes/text_generation),
[LM Format Enforcer](https://github.com/noamgat/lm-format-enforcer), and
[chat-template tokenization](https://huggingface.co/docs/transformers/v4.55.2/en/chat_templating).
