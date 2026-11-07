"""Representation boundary. Source locations are normalized-document offsets."""
from shared.interfaces import AcquiredDocument
from shared.schemas import Chunk
from src.evidence.chunker import chunk_document
from src.evidence.latex_parity import check_parity
from src.evidence.represent import build_document


def process(document: AcquiredDocument, representation_profile: str = "baseline", *, structural_parser=None) -> tuple[dict, list[Chunk]]:
    if representation_profile not in ("baseline", "table_context_v1", "accuracy_v1"):
        raise ValueError("unknown representation profile")
    paper = document.paper
    acq = {"paper_id": paper.paper_id, "source": getattr(paper, "pdf_source", None) or "semantic_scholar",
           "representation_type": paper.representation_type}
    if document.pdf_fallback:
        acq["latex_pdf_fallback_bytes"] = document.pdf_fallback
    doc = build_document(acq, document.data, fallback_abstract=paper.abstract)
    if paper.representation_type == "latex" and document.data and document.pdf_fallback:
        pdf_doc = build_document({**acq, "representation_type": "pdf"}, document.pdf_fallback)
        parity = check_parity(document.data.decode("utf-8", "replace"), doc["blocks"], pdf_doc["blocks"], 0.0)
        if not parity["passed"]:
            doc = pdf_doc
            doc["latex_parity_fallback"] = parity
    if representation_profile in ("table_context_v1", "accuracy_v1") and doc["representation"] == "pdf":
        from pipeline.parsing.table_context import enrich_pdf
        enrich_pdf(doc, document.data)
    chunks = [Chunk.model_validate({**c, "chunk_index": i}) for i, c in enumerate(chunk_document(doc))]
    if representation_profile == "accuracy_v1":
        from pipeline.parsing.accuracy import reconstruct
        bundles=reconstruct(document,doc,chunks,structural_parser)
        from pipeline.evidence.bundles import attest
        attest(bundles,chunks)
        doc["evidence_bundles"]=[b.model_dump() for b in bundles]
    return doc, chunks
