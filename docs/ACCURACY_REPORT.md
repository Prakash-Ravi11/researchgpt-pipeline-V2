# Accuracy-first engineering results

Implemented source-aligned multi-span evidence, a balanced selection catalog,
compatible backend integration and reproducible remote jobs. **Independent real
extraction accuracy remains unestablished.** The single new real API run reached
the Qwen client deadline; no completed prediction or token count exists.

## Implemented and tested

| Area | Result and principal files |
|---|---|
| Parsing | `pipeline/parsing/accuracy.py` defines a replaceable StructuralParser and conservative native multi-header reconstruction. `documents.py` adds accuracy_v1; baseline/JATS/LaTeX remain.15 BLEU column bundles align on the inspected PDF. Unsupported merged costs/continuations remain unresolved. |
| Stronger parser interface | `docling_backend.py` lazily produces Docling/TableFormer ACCURATE external proposals without replacing original text. Framework comparison/licensing/model review is in ACCURACY_RESEARCH.md. Docling/PaddleOCR/MinerU were investigated; none executed here. |
| Typed evidence | `shared/schemas.py` adds EvidenceSpan/EvidenceBundle with document hash, table/source IDs, exact offsets/bboxes, parser identity, row/column positions, structural and review states. SOURCE_ALIGNED is not human approval or complete scientific interpretation. |
| Verification | `pipeline/evidence/bundles.py` checks source/delivery/identity/version/attestation, row/header geometry, proposed tuple agreement, range, table type and ownership. Wrong rows/metrics/datasets/units/versions fail. Existing single-span/legacy gate remains supported. |
| Extractive selection | `pipeline/extraction/selection.py` exposes host-authored IDs; the model selects authorized spans/bundles instead of reproducing quotes/numbers. Missing evidence remains explicit. A match alone does not verify a scientific relation. |
| Context | relationship_v1 reserves prose budget then adds compact complete bundles. On actual retrieved evidence it retains prose124/125 and5 bundles within4565 content bytes. No answer-specific model names/values enter retrieval. |
| Backend | API options and additive verification_state are compatible. Typed bundles/source refs are exposed. Completed bundles now survive extraction failures; status remains FAILED. Process/jobs/search endpoints preserved; frontend not integrated. |
| Remote execution | `kaggle/`, prepare_accuracy_job.py and replay_accuracy_packet.py provide isolated pinned jobs, private/hash-checked inputs, matched source/prompt export, actual runtime/asset records and the same local verifier. No credentials/PDFs uploaded or frameworks installed locally. |

Local changes are on feature/evidence-pipeline-integration. Source repositories,
old .venv, global Python, local dependency lock, frozen annotations and historical
reports are preserved. No push/merge/PR/60-paper run or paid service.

## Structural and scientific scope

Source: *Attention Is All You Need*, printed arXiv:1706.03762v7 [cs.CL],2 Aug2023,
15 readable pages; SHA256
`bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697`.
The native route aligns the BLEU parent, repeated language headers, model rows
and literal cells using coordinates and original chunk spans. Scientific-cost
products are not split into fictitious values. Text, chunk/block identity and
normalized-document offsets remain unchanged; no OCR/VLM gain is claimed.

28.4 and41.8 stay in the big-model table row;41.0 stays in separate prose.
**EN-DE/EN-FR are column conditions, not complete dataset names.** All15 real
bundles currently carry dataset_identity_requires_review. The host refuses
complete numerical verification until a reviewed source-supported mapping
separates the caption benchmark from language/task conditions. Two deterministic
injected big-row probes are UNAVAILABLE/dataset_identity_unresolved; they are
not model predictions. Do not report geometry alignment as complete tuple recall.

Physical synthetic PDFs explicitly name SetA/SetB and demonstrate a supported
five-span numerical tuple passing through the API with an injected selector.
Nine invalid-link mutations and additional missing-text/state/timeout/scope
checks fail safely. This is fixture correctness, not a human-reviewed real example.
All12 existing annotations remain needs_human_review with empty review fields.
The requested human-reviewed numerical acceptance milestone is therefore unmet.

## Retrieval and real-model execution

Same real BGE-M3 revision5617a9f61b028005a4858fdac845db406aefb181,
normalized432x1024 CUDA embeddings, unchanged five top50 queries, optional
table-link expansion. Fresh collection rgpt_v2_b0336189a9c4f3731774c2bb starts0,
stores432; vectors finite/normalized, IDs/metadata round-trip and separate empty
control collection verified. Balanced context contains15 prose anchors and5
bundles, including both result prose124/125; the previous table-focused context
dropped those paragraphs. Budget is an explicit content byte-BPE upper bound,
with wrapper/output reserves, not an observed model token count.

The single actual PDF/BGE/Chroma/Qwen request used the FastAPI HTTP/ASGI route
via TestClient with **real models**, not a network deployment test or mocked
extraction. Qwen2.5:7b Q4_K_M, existing digest845dbda0...697e,8192 context,
2048 configured output, max1 candidate/field, temperature0/seed42,180s deadline.
HTTP200 returns EXTRACTION_FAILED with extraction/ReadTimeout. **No completed
response, actual token counts, generated candidate set or numerical result**
is claimed. Do not score transport failure as a set of missed/withheld predictions.

Total242.672s; parsing1.800s, indexing38.269s, retrieval1.279s, context.027s.
GPU free3104MiB before BGE,3057MiB after verified model release/before Qwen;
only203MiB after the timeout. Peak PyTorch allocated/reserved
2,783,155,200/2,814,377,984 bytes; after release8,519,680/16,777,216 bytes and
weakref gone. Separate Ollama GPU4,270,619,360 bytes, sampled global peak5804MiB.
Host RAM248,721,408 bytes after timeout. Observed pressure is substantial;
there is no CUDA OOM or OpenMP error proving a specific cause. Qwen unloaded
afterward. No timeout increase, second inference or reduced-quality model.

The original failed response omitted top-level bundles (15 remained in trace).
dd7276d fixes that independent failure-path defect; controlled regression proves
completed structure survives with FAILED field status. The original response
was retained and no successful post-fix real-model rerun is implied.

## Local, remote and reproducibility status

Local interpreter throughout:
`C:\Users\Praka\Downloads\research IQ  V2\researchgpt-pipeline-V2\.venv-gpu\Scripts\python.exe`.
One consolidated suite: **110 passed**,0 failed/skipped,8.85s. After two bounded
corrections, **20 targeted checks passed**,5.21s, covering the changed paths;
these overlap the110 and are not130 independent tests. A separate timeout/
lifecycle check passed3 tests in4.67s. One dependency deprecation warning per
batch. Exact executed categories/doubles/versions are in accuracy_*tests.json.

Unchanged A/B/C/D replay ran once: A/B0 of1 complete tuples/delivery, C/D1 of1,
unsupported control withheld. All historical metric dictionaries, annotation,
document/corpus hashes and rules equal the preserved baseline. Test-only dense
encoder/candidate replay and real Chroma/BM25 remain explicitly distinguished.

No Kaggle connector/CLI/credential is configured in this execution environment.
Docling2.148.0 and pinned Qwen3-8B/14B NF4 non-thinking are prepared candidates,
not remotely validated installs or accuracy winners. One physical T4 per job;
no assumed pooled32GB. Native missing/sparse text triggers the OCR proposal;
no OCR/VLM job ran. See kaggle/README.md for rights review/private mounts,
isolated requirements, preflight, asset hashes, failure artifacts and replay.

Final local export: outputs/accuracy/matched-reviewed-scope-package, code commit
4919678; code.zip contains69 allowed source/config files, no PDF/weights/index/
environment. Packet messages exactly equal the retained actual Qwen request.
Packet SHA256:
`c5aa0b11898f632f2cc5e39baf8942382f45c85825d5ad0d6c9a511df40d7487`.
The packet contains text and must stay private. Both remote models use this
identical source/prompt/schema; local replay still refuses unresolved scope.
No additional local model call is required to prepare or replay it.

## Research, application readiness and remaining milestones

ACCURACY_RESEARCH.md records official parser/model checks and the focused Exa
literature review. AxCell, SciREX, TELIN, PubTables/Table Transformer,
SEM-TAB-FACTS, FEVEROUS and SciTab already cover substantial components.
RAG/OCR/linked spans/review queues alone are not novel. The proposed matched-
budget provenance/delivery/verification contribution remains an unproved
hypothesis requiring independently reviewed tuple/structure/attribution metrics.

Engineering contracts, parser fallback, source selection, synthetic linked
verification and failure-aware backend are implemented. Remaining milestones:
reviewed benchmark/condition mappings and annotations; completed real selection
inference on adequate compute; reviewed stronger-parser comparison and safe
promotion if useful; matched controlled evaluation on separate held-out data;
teammate client/citation/status integration, auth/durable jobs/deployment.
Previously inspected papers must not be called held-out. Product release and
proven scientific novelty are not claimed.

Required user actions: independently review the12 proposed facts (reviewer,
date/verdict and experimental scope); provide legitimate private Kaggle GPU
execution with permitted input mounts if remote jobs are to run. Do not send
credentials or publish protected documents. See BLOCKERS.md for exact limits.

Code checkpoints:4c8dfca (bundles/selection),77e1d01 (remote/API package),
dd7276d (failure preservation),4919678 (dataset-scope guard). Final docs/evidence
commit follows. Compact real trace: docs/evidence/accuracy_real_summary.json.

## Exactly one next engineering action

Implement a reviewed caption-to-column mapping that keeps benchmark identity
and language/task condition as separate linked attributes, and validate one
human-reviewed numerical tuple through the existing bundle gate. A larger
decoder alone cannot resolve the current semantic acceptance blocker.
