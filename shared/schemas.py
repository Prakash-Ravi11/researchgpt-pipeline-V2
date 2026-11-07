"""JSON-first contracts; legacy provenance keys remain available without renaming."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

AcquisitionStatus = Literal["FULL_TEXT", "ABSTRACT_ONLY", "METADATA_ONLY", "NO_ACCESSIBLE_FULL_TEXT", "FAILED", "BLOCKED"]
Representation = Literal["pdf", "jats_xml", "latex", "abstract", "none"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="allow", validate_assignment=True)


def canonical_paper_id(record: dict[str, Any]) -> str:
    """Existing S2 IDs are canonical; fallback IDs are namespace-qualified."""
    pid, legacy = record.get("paper_id"), record.get("paperId")
    if pid and legacy and pid != legacy:
        raise ValueError("paper_id and paperId disagree")
    if pid or legacy:
        return str(pid or legacy).strip()
    ids = record.get("externalIds") or {}
    if ids.get("DOI"):
        doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", ids["DOI"], flags=re.I)
        return "doi:" + doi.strip().lower()
    if ids.get("ArXiv"):
        return "arxiv:" + re.sub(r"v\d+$", "", ids["ArXiv"].strip())
    raise ValueError("paper requires a persistent identifier; titles are not identifiers")


class Paper(Contract):
    paper_id: str = Field(min_length=1)
    title: str = ""
    abstract: str | None = None
    year: int | None = None
    venue: str | None = None
    authors: list[dict[str, Any]] = Field(default_factory=list)
    externalIds: dict[str, str] = Field(default_factory=dict)
    acquisition_status: AcquisitionStatus = "METADATA_ONLY"
    representation_type: Representation = "none"
    has_full_text: bool = False
    identity_validation: dict[str, Any] = Field(default_factory=dict)
    content_validation: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def identity_alias(cls, value):
        if isinstance(value, dict):
            value = dict(value)
            value["paper_id"] = canonical_paper_id(value)
            value.pop("paperId", None)
        return value

    @model_validator(mode="after")
    def coherent_full_text(self):
        if self.acquisition_status == "FULL_TEXT":
            if not self.has_full_text or self.representation_type not in ("pdf", "jats_xml", "latex"):
                raise ValueError("FULL_TEXT requires a full-text representation")
            if not self.identity_validation.get("passed") or not self.content_validation.get("passed"):
                raise ValueError("FULL_TEXT requires identity and content validation")
            if self.representation_type == "latex" and self.identity_validation.get("signals", {}).get("identity_source") not in ("arxiv_pdf", "semantic_scholar"):
                raise ValueError("LaTeX content requires independently established PDF/S2 identity")
        elif self.has_full_text:
            raise ValueError("has_full_text requires FULL_TEXT status")
        return self

    def legacy_record(self) -> dict[str, Any]:
        return {**self.model_dump(mode="json"), "paperId": self.paper_id}


class SourceReference(Contract):
    paper_id: str
    chunk_id: str
    block_id: str
    source: str
    representation: Representation
    section: str | None = None
    page_or_node: str
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)
    offset_basis: str = "normalized_document"

    @model_validator(mode="after")
    def ordered_offsets(self):
        if self.char_end < self.char_start:
            raise ValueError("char_end precedes char_start")
        return self


class Chunk(SourceReference):
    text: str = Field(min_length=1)
    block_type: str
    chunk_index: int = Field(default=0, ge=0)
    table_cells: list[dict[str, Any]] = Field(default_factory=list)
    table_caption: str = ""

    def reference(self) -> SourceReference:
        record = {k: getattr(self, k) for k in SourceReference.model_fields}
        for key in ("source_bbox", "source_words", "table_id", "table_representation", "table_context"):
            if key in (self.model_extra or {}):
                record[key] = self.model_extra[key]
        return SourceReference.model_validate(record)


class RetrievalHit(Contract):
    """Teammate adapter boundary: intact canonical source plus explicit score type."""
    chunk: Chunk
    rank: int = Field(ge=1)
    score: float | None = None
    score_kind: str
    strategy: str
    query: str | None = None


class FieldValue(Contract):
    field: str
    value: str | None = None
    final: Literal["RETURNED", "ABSTAINED"] = "ABSTAINED"
    evidence_status: Literal["EXPLICIT", "MISSING", "INFERRED", "UNSUPPORTED"] = "MISSING"
    status: Literal["VERIFIED", "ABSTAINED", "AMBIGUOUS", "FAILED", "MISSING"] = "MISSING"
    abstain_reason: str | None = None
    evidence_span: str | None = None
    source_refs: list[SourceReference] = Field(default_factory=list)
    confidence: float = Field(default=0, ge=0, le=1)
    provenance_valid: bool = False

    @model_validator(mode="after")
    def verified_has_evidence(self):
        if self.final == "RETURNED" or self.status == "VERIFIED":
            if not (self.final == "RETURNED" and self.status == "VERIFIED" and self.value
                    and self.evidence_status == "EXPLICIT" and self.provenance_valid and self.source_refs):
                raise ValueError("returned values require explicit evidence and source references")
        return self


class ExtractedPaper(Contract):
    paper_id: str
    acquisition_status: AcquisitionStatus
    status: Literal["COMPLETE", "PARTIAL", "ABSTAINED", "EXTRACTION_FAILED", "ACQUISITION_FAILED", "PARSING_FAILED", "INDEXING_FAILED"]
    fields: dict[str, list[FieldValue]] = Field(default_factory=dict)
    trace: dict[str, Any] = Field(default_factory=dict)
    errors: list[dict[str, str]] = Field(default_factory=list)

    @model_validator(mode="after")
    def references_belong_to_paper(self):
        for name, values in self.fields.items():
            for value in values:
                if value.field != name:
                    raise ValueError("field key disagrees with field value")
                if any(ref.paper_id != self.paper_id for ref in value.source_refs):
                    raise ValueError("cross-paper evidence reference")
        return self


class Job(Contract):
    job_id: str
    project_id: str
    status: Literal["QUEUED", "RUNNING", "COMPLETE", "PARTIAL", "FAILED"] = "QUEUED"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    result: ExtractedPaper | None = None
    error: str | None = None


class LLMResponse(Contract):
    content: dict[str, Any]
    provider: str
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_ms: float
    finish_reason: str | None = None
