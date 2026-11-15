"""Adapter around audited S2 discovery and validated fallback acquisition."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from shared.interfaces import AcquiredDocument
from shared.schemas import Paper
from src.collection.semantic_scholar import download_open_access_pdfs, fetch_candidates
from src.evidence.acquire import content_validate, identity_validate, sha256_bytes


class LiteratureSource:
    def __init__(self, work_dir: str | Path = "data/acquisition", *, latex: bool = False):
        self.work_dir = Path(work_dir)
        self.latex = latex

    def discover(self, query: str, limit: int = 5, years: tuple[int, int] = (1900, 2026)) -> list[Paper]:
        records = fetch_candidates(query, years, limit, os.getenv("S2_API_KEY"))
        return [Paper.model_validate(p) for p in records]

    def acquire(self, paper: Paper) -> AcquiredDocument:
        self.work_dir.mkdir(parents=True, exist_ok=True)
        # Legacy writer uses paperId as a filename; never use an untrusted ID as a path.
        rec = paper.legacy_record()
        rec["paperId"] = hashlib.sha256(paper.paper_id.encode()).hexdigest()
        rec["has_full_text"] = False
        with TemporaryDirectory(dir=self.work_dir) as tmp:
            download_open_access_pdfs([rec], tmp, validate=True,
                                      use_extra_sources=True, latex_ingestion=self.latex)
            data = Path(rec["pdf_path"]).read_bytes() if rec.get("has_full_text") else None
            fallback = Path(rec["latex_pdf_fallback_path"]).read_bytes() if rec.get("latex_pdf_fallback_path") else None
        for key in ("paperId", "paper_id", "pdf_path", "latex_pdf_fallback_path"):
            rec.pop(key, None)
        if not data:
            rec.update(has_full_text=False, acquisition_status="ABSTRACT_ONLY" if paper.abstract else "NO_ACCESSIBLE_FULL_TEXT",
                       representation_type="abstract" if paper.abstract else "none")
        updated = Paper.model_validate({**rec, "paper_id": paper.paper_id})
        return AcquiredDocument(updated, data, fallback)


def from_bytes(paper: Paper, data: bytes, representation: str, source: str = "local_upload") -> AcquiredDocument:
    if representation not in ("pdf", "jats_xml"):
        raise ValueError("uploads support pdf or jats_xml; LaTeX requires independently validated paired PDF identity")
    content = content_validate(representation, data)
    identity = identity_validate(paper.legacy_record(), representation, data)
    accepted = content["passed"] and identity["passed"]
    rec = paper.model_dump()
    rec.update(has_full_text=bool(accepted), acquisition_status="FULL_TEXT" if accepted else "FAILED",
               representation_type=representation if accepted else "none",
               identity_validation=identity, content_validation=content, pdf_source=source,
               document_sha256=sha256_bytes(data),
               provenance={"source": source, "document_sha256": sha256_bytes(data)},
               failure_reason=None if accepted else "identity_or_content_validation_failed")
    return AcquiredDocument(Paper.model_validate(rec), data if accepted else None)
