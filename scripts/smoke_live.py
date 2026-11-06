"""Bounded real-paper smoke; generated document/index/model outputs stay ignored.

Run from repository root: python -m scripts.smoke_live [--model]
Not an accuracy evaluation; no independent annotations.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path

import requests

from shared.schemas import Paper
from shared.interfaces import AcquiredDocument
from pipeline.acquisition.source import LiteratureSource
from pipeline.parsing.documents import process
from pipeline.retrieval.index import BGEEncoder, ChromaIndex
from pipeline.extraction.clients import OllamaClient
from pipeline.service import EvidencePipeline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", action="store_true")
    args = parser.parse_args()
    root = Path("data/live")
    root.mkdir(parents=True, exist_ok=True)
    summary = {"test_class": "END-TO-END" if args.model else "INTEGRATION", "mocks": False,
               "independent_accuracy_annotations": False, "paper": "Attention Is All You Need"}
    if (root / "paper.json").exists():
        paper = Paper.model_validate_json((root / "paper.json").read_text())
        data = (root / "document.pdf").read_bytes()
        if hashlib.sha256(data).hexdigest() != paper.document_sha256:
            raise ValueError("cached document hash changed")
        document = AcquiredDocument(paper, data)
        summary["acquisition_run"] = "validated local reuse from prior acquisition"
    else:
        metadata = requests.get("https://api.semanticscholar.org/graph/v1/paper/ARXIV:1706.03762",
            params={"fields": "title,abstract,year,venue,authors,externalIds,openAccessPdf"}, timeout=25)
        summary["s2_metadata_http"] = metadata.status_code
        paper = Paper.model_validate(metadata.json()) if metadata.ok else Paper(
            externalIds={"ArXiv": "1706.03762"}, title="Attention Is All You Need")
        document = LiteratureSource(root / "acquisition").acquire(paper)
        summary["acquisition_run"] = "live fallback resolver"
        if document.data and document.paper.has_full_text:
            (root / "paper.json").write_text(document.paper.model_dump_json(indent=2))
            (root / "document.pdf").write_bytes(document.data)
    doc, chunks = process(document)
    summary.update(paper_id=document.paper.paper_id, acquisition_status=document.paper.acquisition_status,
        representation=document.paper.representation_type, document_sha256=getattr(document.paper, "document_sha256", None),
        identity_validation=document.paper.identity_validation, content_validation=document.paper.content_validation,
        n_blocks=doc["n_blocks"], n_chunks=len(chunks), n_structured_tables=doc["n_tables_structured"],
        stable_chunk_ids=chunks == process(document)[1])
    print(json.dumps(summary, indent=2), flush=True)
    if args.model and chunks:
        started = time.perf_counter()
        pipeline = EvidencePipeline(None, ChromaIndex("live-smoke-attention", root / "chroma", BGEEncoder()),
                                    OllamaClient(timeout=120))
        result = pipeline.run(document.paper, document)
        (root / "result.json").write_text(result.model_dump_json(indent=2))
        summary.update(pipeline_status=result.status, errors=result.errors, latency_seconds=time.perf_counter() - started,
            model=result.trace.get("model"), context=result.trace.get("context"),
            verified_by_field={f: sum(v.final == "RETURNED" for v in vs) for f, vs in result.fields.items()},
            stage_ms=result.trace.get("stage_ms"))
        print(json.dumps({"pipeline_status": result.status, "errors": result.errors, "model": summary["model"]}, indent=2), flush=True)
    (root / "smoke_summary.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
