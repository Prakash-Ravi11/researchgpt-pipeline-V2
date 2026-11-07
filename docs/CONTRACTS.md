# Contracts

## Semantic binding and offload-v1

The opt-in semantic_v1 profile adds SemanticBinding and EvidenceRelation:
benchmark and condition are separate; condition_label retains the printed header.
Caption/header/row/column/value/unit/ownership edges retain original span IDs,
table identity, PDF boxes, document SHA and parser identity. Unsupported or
ambiguous scope remains explicit. Machine verification does not set human review.
FieldValue.scientific_tuple exposes benchmark, condition and the compatibility
dataset alias (benchmark), with nullable unit/setting and all supporting refs.

Versioned input/result manifests cover file hashes, exact schema/messages,
model/config/source identities and completion metadata. Only locally registered
inputs authorize source verification. POST /api/inference/import takes project_id,
package_id and result_archive_base64; replacement trusted packets are forbidden.
Response remains ExtractedPaper, with accepted/withheld/ambiguous/failed states.
See kaggle/INFERENCE.md and docs/examples/semantic_import_response.json.

## Accuracy-v1 additive contract

`EvidenceSpan` identifies exact text plus an original SourceReference and optional
native bbox. `EvidenceBundle` links caption/subject/dataset/metric/value spans,
document SHA256, table ID, parser/version, parser row/column positions,
structural state and independent review state. Source-aligned structure is
different from human review. Unresolved model cells never become source text.

`ExtractedPaper.evidence_bundles` exposes the typed structures. FieldValue adds
verification_state (VERIFIED/WITHHELD/FAILED/AMBIGUOUS/UNAVAILABLE) while keeping
the existing final/status vocabulary. Returned bundle fields additionally carry
scientific_tuple, evidence_bundle_id, verification_route and review_status.
The numeric value quote remains literal; the full relationship is supported
by all linked refs rather than a fabricated combined quotation.

`selection_v1` proposals contain only an authorized evidence_id. The host
materializes source anchors and verifies original offsets, hashes, structure,
range, attribution and delivery. Wrong IDs/versions/headers/rows/datasets/units
remain rejected. The original single-span route remains supported.
See RETRIEVAL_INTEGRATION.md and kaggle/README.md for request and replay use.

## Sprint additive contracts

`RetrievalHit` carries the complete shared Chunk, rank, nullable score,
score_kind, strategy and optional query. `FieldValue.status` additionally
supports AMBIGUOUS (final remains ABSTAINED). SourceReference preserves optional
PDF block/word boxes and linked-table provenance. Existing fields and defaults
remain compatible. See [RETRIEVAL_INTEGRATION.md](RETRIEVAL_INTEGRATION.md) for
the executable adapter and API request/response mapping.

Implemented in `shared/schemas.py` and `shared/interfaces.py` using Pydantic 2 and runtime-checkable Protocols.

- Paper accepts `paperId` on input; serialized canonical key is `paper_id`. `legacy_record()` supplies both for migrated discovery/acquisition. Conflicts are errors. Preserve S2 IDs unchanged; DOI/arXiv fallback IDs use namespaces, never titles. FULL_TEXT requires passed identity/content checks and a full-text representation.
- Chunk retains `chunk_id`, `paper_id`, `source`, `representation`, `section`, `page_or_node`, `block_id`, `block_type`, `char_start`, `char_end`, `chunk_index`, text and structured cells. SourceReference is a projection with IDs and locations. Offset basis is explicit; normalized-document offsets are not original PDF byte offsets.
- Nested JATS `section_path` and `subsection` survive as additional chunk metadata. Exact whitespace/source slices and overlapping offsets are regression-tested. LaTeX FULL_TEXT additionally requires identity_source=arxiv_pdf or semantic_scholar.
- FieldValue retains original `value`, `final`, `evidence_status`, `abstain_reason`, `evidence_span`, confidence and provenance_valid. Adds status and source_refs. RETURNED/VERIFIED requires explicit evidence and references. Withheld candidate values stay visible as ABSTAINED and must not be used as findings.
- ExtractedPaper uses original field names inside `fields`, including datasets/metrics/results, plus objective/future_scope. All references must belong to its paper. Acquisition, parsing, indexing and extraction failures are distinct.
- Job retains job_id/status/result/error polling shape, adds project_id and UTC creation time. Jobs are initially process-local, not durable.
- DocumentSource returns AcquiredDocument (Paper, bytes, optional paired PDF); bytes are not API schema fields. Retriever returns original Chunk objects. LLMClient returns LLMResponse with content, model/provider, actual token counters when supplied, finish reason and latency.

Compatibility changes are deliberate: no full-text flag without validation, no synthetic title identity, explicit evidence wrappers instead of unchecked strings, source/provider preserved rather than overwritten by `full_text`. Extra source metadata survives serialization.

Validation: `python -B -m pytest -p no:cacheprovider tests/test_contracts.py -q` => **4 passed** on Python 3.10.18 / Pydantic 2.12.5. CONTRACT, no mocks; no model/accuracy claims.

Final suite contains a fifth CONTRACT test for independent LaTeX identity; all five pass in the recorded 70-test run. Field source references narrow char offsets to the actual quote where possible, while table-binding references identify the supporting source block.
