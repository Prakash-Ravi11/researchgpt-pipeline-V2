# Contracts

Implemented in `shared/schemas.py` and `shared/interfaces.py` using Pydantic 2 and runtime-checkable Protocols.

- Paper accepts `paperId` on input; serialized canonical key is `paper_id`. `legacy_record()` supplies both for migrated discovery/acquisition. Conflicts are errors. Preserve S2 IDs unchanged; DOI/arXiv fallback IDs use namespaces, never titles. FULL_TEXT requires passed identity/content checks and a full-text representation.
- Chunk retains `chunk_id`, `paper_id`, `source`, `representation`, `section`, `page_or_node`, `block_id`, `block_type`, `char_start`, `char_end`, `chunk_index`, text and structured cells. SourceReference is a projection with IDs and locations. Offset basis is explicit; normalized-document offsets are not original PDF byte offsets.
- FieldValue retains original `value`, `final`, `evidence_status`, `abstain_reason`, `evidence_span`, confidence and provenance_valid. Adds status and source_refs. RETURNED/VERIFIED requires explicit evidence and references. Withheld candidate values stay visible as ABSTAINED and must not be used as findings.
- ExtractedPaper uses original field names inside `fields`, including datasets/metrics/results, plus objective/future_scope. All references must belong to its paper. Acquisition, parsing, indexing and extraction failures are distinct.
- Job retains job_id/status/result/error polling shape, adds project_id and UTC creation time. Jobs are initially process-local, not durable.
- DocumentSource returns AcquiredDocument (Paper, bytes, optional paired PDF); bytes are not API schema fields. Retriever returns original Chunk objects. LLMClient returns LLMResponse with content, model/provider, actual token counters when supplied, finish reason and latency.

Compatibility changes are deliberate: no full-text flag without validation, no synthetic title identity, explicit evidence wrappers instead of unchecked strings, source/provider preserved rather than overwritten by `full_text`. Extra source metadata survives serialization.

Validation: `python -B -m pytest -p no:cacheprovider tests/test_contracts.py -q` => **4 passed** on Python 3.10.18 / Pydantic 2.12.5. CONTRACT, no mocks; no model/accuracy claims.
