# Accuracy options and research claim ledger

Checked official documentation/model metadata on2026-11-07. Focused Exa review:
31 requested result slots across parser, model and competing-method angles;
primary pages fetched for consequential claims. This is a bounded literature
review, not an exhaustive novelty search. No remote experiment was executed.

## Parser comparison and decision

| Candidate | Documented capability/runtime/licensing | Actual status and choice |
|---|---|---|
| Existing PyMuPDF / structured sources | Native PDF text, validated ruled grids, JATS/LaTeX, stable offsets; existing baseline | Executed locally. Table2 lacks cell relationships; retained as fallback. |
| Native header geometry v1 | Added conservative repeated-leaf/metric-parent alignment, exact source spans, unresolved products/merged cells | Executed on physical synthetic fixtures and inspected arXiv PDF.15 BLEU bundles source-aligned; source review is not independent accuracy. Selected local overlay. |
| Docling / TableFormer ACCURATE | Explicit structure mode and native-cell matching; CPU/CUDA supported. Code MIT; model repository lists CDLA-permissive2.0/Apache2.0, asset-specific terms still apply | First remote comparison candidate, replaceable lazy adapter.2.148.0 pinned; no Windows installation or claimed structural accuracy. Export model cells as proposals until source/structure review. |
| PaddleOCR PP-StructureV3 | Layout, wired/wireless structure recognition, OCR/formulas, dedicated Paddle runtime; code Apache2.0 | Technically relevant second candidate if Docling fails reviewed cases. Not installed/run; model-specific terms/assets require review. |
| MinerU current backend | Official current docs describe basic/standard/advanced tiers, ONNX/Torch and llama.cpp/vLLM engines; higher tiers require adequate RAM/VRAM | Not installed/run. Current4.x interface differs from older pipeline/hybrid recipes; conditional MinerU license includes service attribution/threshold terms. More integration surface, no local evidence of benefit. |

Sources: [Docling options](https://docling-project.github.io/docling/usage/advanced_options/),
[model catalog](https://docling-project.github.io/docling/usage/model_catalog/),
[code license](https://github.com/docling-project/docling/blob/main/LICENSE),
[model terms](https://huggingface.co/docling-project/docling-models/blob/2199320848bb9a8a519d22e4b528185a4f9a6f64/README.md),
[PP-StructureV3](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/pipeline_usage/PP-StructureV3.en.md),
[Paddle installation](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/installation.en.md),
[Paddle license](https://github.com/PaddlePaddle/PaddleOCR/blob/main/LICENSE),
[MinerU runtime](https://opendatalab.github.io/MinerU/usage/tiers/),
[MinerU license](https://github.com/opendatalab/MinerU/blob/master/LICENSE.md).

No OCR/VLM accuracy gain is claimed: neither was run. The actual readable PDF
does not need OCR to recover its present digits. Multi-column reading order,
truly borderless tables, page continuations, arbitrary merged cells and equation
semantics remain outside the local geometry route's demonstrated coverage.
JATS/LaTeX structure and independent identity validation remain supported.
Sparse/missing text explicitly requests an OCR-capable route; unresolved table
relationships request specialized structure recognition. Uncertainty is not a
license to fabricate a cell or trust a VLM number.

Source-aligned header geometry is also not dataset semantics. In this PDF the
leaf EN-DE/EN-FR codes describe column conditions; resolving the caption's
benchmark as a separate linked attribute requires reviewed mapping. Current
bundles explicitly mark this unresolved and cannot become verified complete
tuples solely because a stronger model selects their IDs.

## Extraction candidates

[Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B) and
[Qwen3-14B](https://huggingface.co/Qwen/Qwen3-14B) are selected as reproducible
remote candidates, not promoted accuracy improvements. Official cards specify
Apache2.0,8.2B/14.8B parameters and Transformers>=4.51. The prepared candidate
runtime pins4.55.2 and model commits in kaggle/models.json. NF4/FP16 compute and
one T4 per process are explicit.9/12GB free-memory guards allow overhead but
require actual runtime measurement; no32GB pooling assumption. Non-thinking
is switched off explicitly, greedy decoding is the controlled experimental
choice rather than a claim of optimal sampling. Local Qwen2.5:7b stays baseline.

All models receive the same packet/schema/source evidence. Host-authored
anchor/bundle IDs eliminate a requirement to regenerate a quote. A selection
still requires source identity/offset/structure/range/ownership verification.
Raw generation, schema validity, host acceptance and independent accuracy are
reported separately. Larger model size is not evidence of correctness.

## Closest methods and claim ledger

| Prior method | Already demonstrated | Proposed distinction / evidence still required |
|---|---|---|
| [AxCell (2020)](https://aclanthology.org/2020.emnlp-main.692/) | Result extraction using table segmentation and cell/table/caption/mention/paper context, leaderboard linking | Strong direct overlap. Need demonstrate source/version-safe bundles plus budgeted delivery improve complete verified tuples beyond an AxCell-style context baseline. |
| [SciREX (2020)](https://aclanthology.org/2020.acl-main.670/) | Document-level salient entities and N-ary scientific relations | Document-level relations are not novel. Its [repository](https://github.com/allenai/SciREX/) notes discarded-table entity coverage limitations; evaluation must not silently remove difficult missing-evidence cases. |
| [TELIN (2022)](https://aclanthology.org/2022.wiesp-1.3/) | PDF-based task/model/dataset/metric linking with uncertainty-driven human feedback | PDF integration and review queues are not novel. Compare annotation effort, linked source correctness and complete numeric tuple precision/recall. |
| [PubTables-1M/Table Transformer (2022)](https://openaccess.thecvf.com/content/CVPR2022/html/Smock_PubTables-1M_Towards_Comprehensive_Table_Extraction_From_Unstructured_Documents_CVPR_2022_paper.html) | Large scientific table dataset, detailed headers/locations, detection/structure/functional analysis | Multi-level structure recovery needs established structure baselines and reviewed geometry, not prettier Markdown. |
| [SEM-TAB-FACTS (2021)](https://aclanthology.org/2021.semeval-1.39/) | Scientific-table claim verification and supporting-cell evidence finding | Supporting-cell verification is not novel. Need measure attributable complete extraction, wrong-cell controls and calibrated abstention. |
| [FEVEROUS (2021)](https://datasets-benchmarks-proceedings.neurips.cc/paper_files/paper/2021/file/68d30a9594728bc39aa24be94b319d21-Paper-round1.pdf) | Verification using combined sentence/table-cell evidence and multi-level headers | Linked multi-span evidence alone is not novel. Proposed focus is immutable scientific document provenance and failure-aware delivery; needs direct ablations. |
| [SciTab (2023)](https://aclanthology.org/2023.emnlp-main.483/) | Expert-verified scientific-table claims with compositional reasoning/ambiguity | Exact extractive verification does not solve comparative/compositional scientific claims; assess that limit rather than imply general scientific reasoning. |
| [Scientific Table Generation (2026)](https://aclanthology.org/2026.wasp-1.25/) | Related structured scientific information/table generation | Additional close recent work; no claim that our table extraction direction is unaddressed. |

**Testable hypothesis, not established novelty:** under matched source documents,
model and context budget, typed source-aligned bundles plus source selection
increase independently reviewed complete-tuple delivery/correctness and reduce
unsupported attribution, compared with flat chunks and whole-table expansion.

Required baselines: preserved dense/current, optional BM25/RRF, whole-table
context, one reviewed stronger parser, identical-model free quotation versus
selection, with/without linked verification. Limit to motivated ablations;
do not run every combination. Freeze scoring before final evaluation.

Threats: previously inspected single-paper development data; authored synthetic
fixtures; no independently reviewed numerical benchmark yet; parser/model
training leakage; dataset alias ambiguity; conservative abstention lowering
recall; different prompt budgets/quantizers; structural predicates missing
compositional meaning; and opaque third-party parser errors. Current results
cannot substantiate a research contribution or release-level accuracy.
