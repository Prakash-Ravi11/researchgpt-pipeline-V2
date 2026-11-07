"""One connected acquisition-to-verified-record service, independent of HTTP."""
from __future__ import annotations

import time

from shared.interfaces import AcquiredDocument
from shared.schemas import ExtractedPaper, FieldValue, Paper, EvidenceBundle
from pipeline.evidence.verification import verify_candidate
from pipeline.extraction.context import current_context
from pipeline.extraction.prompt import FIELDS, SYSTEM
from pipeline.parsing.documents import process
from pipeline.retrieval.retrievers import FiveQueryRetriever, HybridRetriever, TableAwareRetriever, scored_records


class EvidencePipeline:
    def __init__(self, source, index, llm, *, retrieval: str = "five_query", context_mode: str = "current",
                 max_words: int = 2500, context_builder=None, representation_profile: str = "baseline",
                 extraction_mode: str = "quotation"):
        if retrieval not in ("five_query", "hybrid", "table_aware_v1"):
            raise ValueError("unknown retrieval mode")
        if context_mode != "current" and context_builder is None and context_mode!="relationship_v1":
            raise ValueError("context configuration unavailable")
        self.source, self.index, self.llm = source, index, llm
        self.retriever = {"five_query": FiveQueryRetriever, "hybrid": HybridRetriever,
                          "table_aware_v1": TableAwareRetriever}[retrieval](index)
        self.context_builder = context_builder or (lambda cs: current_context(cs, max_words))
        self.context_mode, self.retrieval = context_mode, retrieval
        self.representation_profile = representation_profile
        if extraction_mode not in ("quotation","selection_v1"):
            raise ValueError("unknown extraction mode")
        if (context_mode=="relationship_v1") != (extraction_mode=="selection_v1"):
            raise ValueError("relationship context requires source selection")
        self.extraction_mode=extraction_mode

    def run(self, paper: Paper, document: AcquiredDocument | None = None) -> ExtractedPaper:
        trace = {"retrieval": self.retrieval, "context_mode": self.context_mode, "stage_ms": {},
                 "representation_profile": self.representation_profile,
                 "extraction_mode":self.extraction_mode,
                 "generation_profile": getattr(self.llm, "generation_profile", "custom_or_default")}
        started = time.perf_counter()
        stage = "acquisition"
        encoder_released = False
        def release_encoder():
            nonlocal encoder_released
            if not encoder_released:
                release = getattr(self.index, "release_encoder", None)
                if release:
                    trace["embedding_release"] = release()
                encoder_released = True
        try:
            t = time.perf_counter()
            requested_id = paper.paper_id
            document = document or self.source.acquire(paper)
            if document.paper.paper_id != requested_id:
                raise ValueError("source changed paper identity")
            paper = document.paper
            trace["stage_ms"][stage] = (time.perf_counter() - t) * 1000
            trace["acquisition"] = {"status": paper.acquisition_status, "representation": paper.representation_type,
                "document_sha256": getattr(paper, "document_sha256", None),
                "identity_validation": paper.identity_validation, "content_validation": paper.content_validation}
            if paper.acquisition_status in ("FAILED", "BLOCKED"):
                return ExtractedPaper(paper_id=paper.paper_id, acquisition_status=paper.acquisition_status,
                    status="ACQUISITION_FAILED", trace=trace, errors=[{"stage": stage, "code": "document_not_validated"}])
            stage, t = "parsing", time.perf_counter()
            doc, chunks = process(document, self.representation_profile)
            bundles=[EvidenceBundle.model_validate(b) for b in doc.get("evidence_bundles",[])]
            trace["stage_ms"][stage] = (time.perf_counter() - t) * 1000
            trace["document"] = {k: v for k, v in doc.items() if k != "blocks"}
            trace["chunk_ids"] = [c.chunk_id for c in chunks]
            if not chunks:
                return ExtractedPaper(paper_id=paper.paper_id, acquisition_status=paper.acquisition_status,
                    status="ABSTAINED", fields={f: [FieldValue(field=f, abstain_reason="no_accessible_text")] for f in FIELDS}, trace=trace)
            stage, t = "indexing", time.perf_counter()
            self.index.replace_paper(paper.paper_id, chunks)
            trace["stage_ms"][stage] = (time.perf_counter() - t) * 1000
            stage, t = "retrieval", time.perf_counter()
            retrieved = self.retriever.retrieve(paper.paper_id, chunks)
            trace["retrieval_queries"] = list(getattr(self.index, "query_trace", []))[-5:]
            trace["retrieval_expansion"] = getattr(self.retriever, "expansion_trace", [])
            records = scored_records(retrieved, self.retrieval, trace["retrieval_queries"], trace["retrieval_expansion"])
            trace["retrieval_records"] = [{**r.model_dump(exclude={"chunk"}), "chunk_id": r.chunk.chunk_id,
                                          "source_ref": r.chunk.reference().model_dump()} for r in records]
            trace["stage_ms"][stage] = (time.perf_counter() - t) * 1000
            stage, t = "context", time.perf_counter()
            if self.extraction_mode=="selection_v1":
                from pipeline.extraction.selection import relationship_context
                context=relationship_context(retrieved,bundles)
            else:
                context = self.context_builder(retrieved)
            trace["context"] = context.trace
            trace["stage_ms"][stage] = (time.perf_counter() - t) * 1000
            # Indexing and all query embeddings are complete. Do not retain BGE
            # GPU weights while Ollama separately loads its extraction model.
            release_encoder()
            if not context.chunks:
                return ExtractedPaper(paper_id=paper.paper_id, acquisition_status=paper.acquisition_status, status="ABSTAINED",
                    fields={f: [FieldValue(field=f, abstain_reason="no_evidence_within_context_budget")] for f in FIELDS}, trace=trace)
            stage, t = "extraction", time.perf_counter()
            if self.extraction_mode=="selection_v1":
                from pipeline.extraction.selection import SYSTEM as selection_system
            else:
                selection_system=SYSTEM
            response = self.llm.complete(selection_system, f"Paper: {paper.title}\nAcquisition: {paper.acquisition_status}\n\n{context.text}")
            trace["model"] = response.model_dump(exclude={"content"})
            trace["stage_ms"][stage] = (time.perf_counter() - t) * 1000
            parsed = response.content
            if not any(key in parsed for key in FIELDS) or any(not isinstance(parsed.get(k, []), list) for k in FIELDS):
                raise ValueError("extraction response does not follow field-array schema")
            stage, t = "verification", time.perf_counter()
            fields = {}
            for name in FIELDS:
                candidates = parsed.get(name, [])
                if self.extraction_mode=="selection_v1":
                    from pipeline.extraction.selection import verify_selection
                    fields[name]=[verify_selection(name,c,paper,context,chunks,bundles) for c in candidates]
                else:
                    fields[name]=[verify_candidate(name,c,paper,context.chunks,chunks) for c in candidates]
                fields[name]=fields[name] or [FieldValue(field=name,abstain_reason="missing_evidence",verification_state="UNAVAILABLE")]
            trace["stage_ms"][stage] = (time.perf_counter() - t) * 1000
            trace["total_ms"] = (time.perf_counter() - started) * 1000
            values = [v for vs in fields.values() for v in vs]
            status = "COMPLETE" if all(v.final == "RETURNED" for v in values) else (
                "PARTIAL" if any(v.final == "RETURNED" for v in values) else "ABSTAINED")
            return ExtractedPaper(paper_id=paper.paper_id, acquisition_status=paper.acquisition_status,
                                  status=status, fields=fields, trace=trace,evidence_bundles=bundles)
        except Exception as exc:
            trace["total_ms"] = (time.perf_counter() - started) * 1000
            statuses = {"acquisition": "ACQUISITION_FAILED", "parsing": "PARSING_FAILED",
                        "indexing": "INDEXING_FAILED", "retrieval": "INDEXING_FAILED"}
            # Never reflect raw HTTP errors/credentials or arbitrary provider text.
            return ExtractedPaper(paper_id=paper.paper_id, acquisition_status=paper.acquisition_status,
                status=statuses.get(stage, "EXTRACTION_FAILED"), trace=trace,
                fields={f: [FieldValue(field=f, status="FAILED", abstain_reason="stage_failed")] for f in FIELDS},
                errors=[{"stage": stage, "code": type(exc).__name__}])
        finally:
            try:
                release_encoder()
            except Exception as exc:
                trace["embedding_release_error"] = type(exc).__name__
