# Semantic table binding and inference offload results

Delivered the three requested engineering components: semantic relation building,
a source-backed complete-tuple verifier fixture, and a versioned Kaggle export/
local-import workflow. **No new real-model inference was run. Kaggle is NOT
EXECUTED; independent extraction accuracy remains unmeasured.**

## Binding and selected tuple

The opt-in semantic_v1 route reuses native geometry and the existing parser/
bundle/gate pipeline. It separates benchmark identity from column condition:
explicit caption identifiers or labels establish the benchmark; a closed
language vocabulary links the printed header code to an actual caption phrase.
It never infers a benchmark from a nearby number or recognizes expected result
values. Direct named dataset columns are also supported. Multiple possible
benchmarks/conditions abstain rather than being guessed. A reproduced model-size
case also stays unresolved: caption mentions of base/big cannot become benchmark
identities without an explicit benchmark cue. 33 targeted checks pass after that
correction, separately from the 144-test full consolidation.

Typed edges link caption→benchmark, caption/header→condition, metric→column,
column/row→value, optional metric→printed unit, and an explicit same-table prose
mention for ownership. Original text, offsets, document hash, page, coordinates,
parser identity and canonical source IDs survive. Host attestations and a fresh
relation rebuild reject edits or unrelated scopes. The original accuracy_v1,
single-span gate and unstructured_table_text fallback remain available.

Selected proposed tuple from *Attention Is All You Need*:

| Attribute | Literal/source-backed value |
|---|---|
| Version | arXiv:1706.03762v7 [cs.CL], 2 Aug 2023 |
| SHA256 | bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697 |
| Table/page | arxiv:1706.03762:108:table / page 8 |
| Model | Transformer (big) |
| Benchmark/test set | newstest2014 |
| Condition | English-to-French, linked to EN-FR |
| Metric/value | BLEU / 41.8 |
| Unit/extra setting | null; not invented |
| Machine verdict | VERIFIED/RETURNED by semantic_table_v1 |
| Independent ground truth | needs_human_review |

Nine original spans and seven explicit relations support this tuple. The
separate 41.0 prose statement is not substituted or merged. WMT 2014 in prose is
not silently substituted for the caption's named test set. The minimal source
fixture is tests/fixtures/semantic_attention_v7.json; review material is
docs/annotations/SELECTED_TUPLE_REVIEW.md and selected_tuple_review.json, alongside
the retained actual page 8 rendering. All review fields remain empty; the prior
12-item queue and frozen annotations are unchanged.

Positive source verification passes; changing value/model/benchmark/condition/
metric/unit, header/row refs, relation edges, source availability or document
version fails. Generic physical PDFs cover a different benchmark identifier,
hierarchical/merged parent headers, printed units and ambiguous benchmark scope.
This demonstrates verifier behavior, not autonomous extraction accuracy.

## Connected extraction/backend behavior

Source-ID selection displays the canonical semantic binding and original
anchors. Complete units are selected alongside result prose; exact row mentions
in selected experimental prose improve semantic bundle priority without adding
answer terms to retrieval. Existing five-query vocabulary/BGE baseline and
optional hybrid remain preserved.

A controlled real-PDF ASGI fixture exercised acquisition→parser→bundles→
retrieval→candidate→gate→API. It uses a TEST-ONLY encoder, preserved actual BGE
retrieval IDs and an injected selector: HTTP 200/PARTIAL, the selected 41.8 tuple,
nine refs and needs_human_review. The initial TinyEncoder-only retrieval fixture
missed the table seed; that failure is retained, then the fixture was corrected
to replay actual retrieval IDs. Neither attempt is a new real-model experiment.

POST /api/inference/import accepts a result archive only against an input
registered locally with TrustedInputStore. It returns the existing ExtractedPaper
shape with benchmark/condition fields, source locations and distinct verification
states. The realistic controlled example in docs/examples/semantic_import_response.json
shows a machine-verified tuple and a WITHHELD numerical prose selection. Existing
process/discover/jobs endpoints and port 8000 remain. Frontend/auth/deployment
infrastructure was not rebuilt or claimed integrated.

## Timeout diagnosis from existing evidence

Matched saved server.log to the prior failed run. Startup-to-ready was 43.835s;
24/29 layers were offloaded to GPU, with a 969.10 MiB CPU model buffer and 80 MiB
CPU KV buffer. The server scheduled 1811 prompt tokens, then returned HTTP 500
after 3 minutes and cancelled the task, matching the client's ReadTimeout.

The established limiting condition is the request deadline/cancellation.
Prompt-evaluation duration, generation duration and generated-token count are
absent; the post-load slow/stalled phase cannot be separated from these logs.
CPU/RAM offloading and severe memory pressure were present. There is no logged
CUDA OOM or OpenMP conflict establishing a GPU failure. No expensive local retry,
timeout increase or evidence reduction was used. Raw history was not rewritten;
new evidence is docs/evidence/semantic_timeout_diagnosis.json.

## Portable export / inference / trusted import

The final package is outputs/semantic/offload-package-v2, with convenience archive
outputs/semantic/inference-input-v2.zip. It contains 12 selected source blocks and
two big-model bundles (~140 KB packet), exact messages/output schema, model ID/
revision, NF4/FP16/thinking/generation parameters, original Qwen2.5 baseline
configuration, document/code hashes and a manifest covering all input files,
including code.zip. No PDF, full corpus, model weights, database or credentials.
Selected source text still requires private handling and legitimate sharing rights.

Package ID: rgpt_d03e8fa2bfe3dc4baa48c121; code commit 87e44b4.
Trusted input-manifest SHA256:
ff00931afc4c49ccb7f684dd0674027fb0bfac9178f3cf08797537b6d4f5f3ff.

The Kaggle script validates that retained SHA, inspects actual free memory on
one selected physical GPU, loads the requested pinned model and executes the
exact supplied messages through its chat template. T4x2 is not pooled memory.
It records actual counts/completion/runtime when available and exports raw
text, normalized JSON, execution metadata and output-manifest.json in result.zip.
Failures retain artifacts; no silent model substitution or source truncation.

Local import validates both manifests, model/config/document identity, output
schema, authorized source IDs and equality of normalized candidates to the raw
response, then applies the existing local source/semantic/range/ownership gate.
It preserves raw bytes. Remote claimed verdicts are ignored. Hashes provide
integrity, not proof of the remote author's identity or claimed compute usage.
Round-trip tests cover accepted, withheld, ambiguous and failed outcomes,
tampering, wrong model/condition/document, fabricated fields and unsafe archives.

The user confirmed that no private Kaggle notebook, URL/identifier or mounted
input path exists yet. Execution status is **NOT EXECUTED**, not a successful
remote result. kaggle/semantic_inference.ipynb is an unexecuted uploadable T4
notebook that discovers the actual input mount by the retained local manifest
SHA. The exact five-file upload checklist, setup steps, local commands, pins
and backend registration are in kaggle/INFERENCE.md. The older runner and
original export are preserved. Remote dependency installation remains unvalidated.

The later notebook handoff was checked locally with the exact .venv-gpu Python:
all six code cells parse and have no saved executions/outputs. Configuration and
bootstrap ran against a temporary copy of the actual package; actual-directory
discovery and code extraction passed, while missing/duplicate matching manifests
were rejected. No install, GPU preflight, generation or download cell was run.
See docs/evidence/kaggle_notebook_validation.json. This does not add model accuracy
results or repeat the full suite/frozen evaluation.

## Consolidated validation and milestones

- One full suite: 144 passed, 0 failed/skipped, 7.11s; one dependency deprecation
  warning. Exact interpreter/per-test categories/doubles are in semantic_tests.json.
- A subsequent concrete model-size ambiguity correction passes 33 targeted
  semantic/package tests in 3.09s. These overlap the 144; no second full suite.
- One unchanged frozen A/B/C/D replay: A/B 0 of 1 complete tuples/delivery;
  C/D 1 of 1, unsupported control withheld. Annotation/document/chunk hashes,
  rules and metric dictionaries exactly equal historical results. These are
  synthetic/test-encoder/replay results, not real extraction scores.
- Additional controlled source/API and final registered-package import commands
  pass; no real LLM or GPU inference occurred. pip check passes; 94 Python files
  parse. jsonschema 4.26.0 was already installed and is now an explicit dependency.

Local interpreter: C:\Users\Praka\Downloads\research IQ  V2\researchgpt-pipeline-V2\.venv-gpu\Scripts\python.exe.
Core files: pipeline/parsing/semantic.py, pipeline/evidence/bundles.py,
shared/schemas.py, pipeline/inference/{packages,replay}.py, scripts/inference_package.py,
kaggle/run_inference.py, api/main.py and the semantic/package regression fixtures.
Commits: ca59d22 (semantic fixture/binding), 3132f3b (offload/backend), 57d2071
(runnable guide), 87e44b4 (benchmark ambiguity guard); final docs commit follows. Working branch
is feature/evidence-pipeline-integration. Sources/old environments/historical
results are preserved; no push/merge/PR/full 60-paper/paid/public-upload action.

Engineering success criteria for this sprint are met locally. Remaining blockers
are independent human confirmation, an actual controlled remote inference run,
remote environment validation and teammate client/deployment integration.
No independent scientific accuracy or complete-product claim is made.

## One highest-priority next action

Run this exported package once on a private Kaggle GPU and import result.zip
through the trusted local workflow, retaining the actual outcome and artifacts.
