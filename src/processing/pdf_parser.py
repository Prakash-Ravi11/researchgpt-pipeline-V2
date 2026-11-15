"""Grounded processor migrated from original src/processing/pdf_parser.py.
See docs/SOURCE_MANIFEST.json for source attribution.
"""
from pathlib import Path

def process_paper_grounded(paper: dict, latex_parity_tolerance: float | None = None) -> list[dict]:
    """Provenance-bearing chunking (FINAL_REPORT.md §O change 3).

    Parses the validated PDF or JATS/XML into section/page/node-anchored blocks,
    then chunks WITHIN blocks so every chunk keeps section + page/node + char
    span. Returns the same superset schema as ``process_paper`` PLUS the
    provenance fields, so Stage 3 / retrieval / the evidence gate can consume it
    while nothing that reads the legacy fields breaks.

    LaTeX parity gate: a paper acquired as LaTeX is kept ONLY if verbatim survival
    of its ground-truth numeric values is at least as good as the paired PDF's
    (`latex_parity_tolerance`, default strict). Otherwise it falls back to the PDF
    representation and the two survival figures are recorded on every chunk's
    `latex_parity_fallback`.
    """
    from src.evidence.represent import build_document
    from src.evidence.chunker import chunk_document

    pid = paper["paperId"]
    rep = paper.get("representation_type") or ("pdf" if paper.get("has_full_text") else "abstract")
    acq = {"paper_id": pid, "source": paper.get("pdf_source") or "semantic_scholar",
           "representation_type": rep, "status": paper.get("acquisition_status", "")}

    data = None
    if paper.get("has_full_text") and paper.get("pdf_path"):
        p = Path(paper["pdf_path"])
        if p.exists():
            data = p.read_bytes()
    parity_fallback = None
    # LaTeX representation: `pdf_path` is the .tex; also load the paired arXiv PDF
    # so build_document can fall back to it PER TABLE when a tabular env won't parse.
    if rep == "latex" and paper.get("latex_pdf_fallback_path"):
        fb = Path(paper["latex_pdf_fallback_path"])
        if fb.exists():
            acq["latex_pdf_fallback_bytes"] = fb.read_bytes()

    doc = build_document(acq, data, fallback_abstract=paper.get("abstract"))

    if rep == "latex" and data is not None and acq.get("latex_pdf_fallback_bytes"):
        from src.evidence.latex_parity import check_parity, DEFAULT_PARITY_TOLERANCE
        tol = DEFAULT_PARITY_TOLERANCE if latex_parity_tolerance is None else latex_parity_tolerance
        pdf_acq = {**acq, "representation_type": "pdf"}
        pdf_doc = build_document(pdf_acq, acq["latex_pdf_fallback_bytes"],
                                 fallback_abstract=paper.get("abstract"))
        par = check_parity(data.decode("utf-8", "replace"), doc["blocks"], pdf_doc["blocks"], tol)
        if not par["passed"]:
            doc = pdf_doc                       # PARITY GATE: never worse than baseline
            parity_fallback = par

    ev_chunks = chunk_document(doc)

    legacy_source = ("full_text" if doc["representation"] in ("pdf", "jats_xml", "latex")
                     else "abstract_only")
    records = []
    for i, c in enumerate(ev_chunks):
        records.append({
            "chunk_id": c["chunk_id"],
            "paper_id": pid,
            "title": paper.get("title", ""),
            "year": paper.get("year"),
            "venue": paper.get("venue", ""),
            "has_full_text": paper.get("has_full_text", False),
            "source": legacy_source,
            "chunk_index": i,
            "text": c["text"],
            # provenance (§O)
            "representation": c["representation"],
            "section": c["section"],
            "page_or_node": c["page_or_node"],
            "block_id": c["block_id"],
            "block_type": c["block_type"],
            "char_start": c["char_start"],
            "char_end": c["char_end"],
            # Phase 4a structural table cells, carried into chunks.json so Stage 5
            # can bind a quantitative claim to the actual (row, column) cell.
            **({"table_cells": c["table_cells"], "table_caption": c.get("table_caption", "")}
               if c.get("table_cells") else {}),
            **({"latex_parity_fallback": parity_fallback} if parity_fallback else {}),
        })
    return records

