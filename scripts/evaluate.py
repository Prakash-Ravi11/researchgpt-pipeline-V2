"""Controlled four-arm fixture/replay evaluation, no dense-model accuracy claim.

python -m scripts.evaluate --output outputs/fixture_evaluation.json
Working hybrid dependency is required for B/D; never silently substitutes A/C.
"""
import argparse
import hashlib
import importlib.util
import json
import time
import tracemalloc
import xml.etree.ElementTree as ET
from pathlib import Path

from pipeline.diagnostics import trace_fact
from pipeline.evaluation import score_tuples
from pipeline.extraction.context import current_context, revised_context
from pipeline.parsing.documents import process
from pipeline.retrieval.index import ChromaIndex
from pipeline.retrieval.retrievers import FiveQueryRetriever, HybridRetriever
from pipeline.evidence.verification import verify_candidate
from tests.helpers import fixture_document, TinyEncoder


def evaluate(annotation_path=Path("tests/fixtures/annotations.json"), store=Path("outputs/eval-index")):
    frozen = annotation_path.read_bytes()
    labels = json.loads(frozen)
    document = fixture_document()
    root = ET.fromstring(document.data)
    sec = ET.Element("sec")
    ET.SubElement(sec, "title").text = "Introduction"
    ET.SubElement(sec, "p").text = " ".join(["background"] * 300)
    root.find("body").insert(0, sec)
    document.data = ET.tostring(root)
    parsed, chunks = process(document)
    index = ChromaIndex("four-arm-synthetic-fixture", store, TinyEncoder())
    index.replace_paper(document.paper.paper_id, chunks)
    report = {"annotation_sha256": hashlib.sha256(frozen).hexdigest(),
        "document_sha256": hashlib.sha256(document.data).hexdigest(),
        "chunk_corpus_sha256": hashlib.sha256("\n".join(c.model_dump_json() for c in chunks).encode()).hexdigest(),
        "scope": "synthetic fixture / deterministic candidate replay", "dense_encoder": TinyEncoder.signature,
        "model": "none; controlled candidates injected only when source quote delivered", "real_llm_accuracy": "NOT MEASURED",
        "independent_real_annotations": False, "rules": labels["rules"], "configurations": {}}
    cfg = labels["configuration"]
    for arm, retrieval, assembly in [("A", "five_query", "current"), ("B", "hybrid", "current"),
                                     ("C", "five_query", "revised"), ("D", "hybrid", "revised")]:
        if retrieval == "hybrid" and importlib.util.find_spec("rank_bm25") is None:
            report["configurations"][arm] = {"status": "UNAVAILABLE", "reason": "rank_bm25 missing"}
            continue
        tracemalloc.start()
        started = time.perf_counter()
        retriever = FiveQueryRetriever(index, cfg["per_query_dense"]) if retrieval == "five_query" else HybridRetriever(index, cfg["hybrid_top_k"])
        retrieved = retriever.retrieve(document.paper.paper_id, chunks)
        context = current_context(retrieved, cfg["max_words"]) if assembly == "current" else revised_context(
            retrieved, cfg["max_words"], cfg["revised_budget_utf8_bytes"])
        candidates, traces, delivered = [], [], 0
        for fact in labels["facts"]:
            hit = next((c for c in context.chunks if fact["quote"] in c.text), None)
            visible = hit is not None and fact["quote"] in context.text
            delivered += visible
            accepted = False
            if visible:
                candidate = {"value": fact["quote"], "evidence_span": fact["quote"], "chunk_id": hit.chunk_id,
                             "scientific_tuple": fact["scientific_tuple"]}
                item = verify_candidate("results", candidate, document.paper, context.chunks, chunks)
                candidates.append(item)
                accepted = item.final == "RETURNED"
            traces.append(trace_fact(fact, document, parsed, chunks, retrieved, context, extracted=visible, verified=accepted))
        # Fixed unsupported control. A genuine source ID/quote cannot license 99.9.
        if context.chunks:
            hit = context.chunks[0]
            candidates.append(verify_candidate("results", {"value": "Our Dice score is 99.9%.",
                "evidence_span": hit.text, "chunk_id": hit.chunk_id}, document.paper, context.chunks, chunks))
        returned = [i for i in candidates if i.final == "RETURNED"]
        predicted = [i.scientific_tuple for i in returned]
        metrics = score_tuples([f["scientific_tuple"] for f in labels["facts"]], predicted)
        metrics.update(evidence_delivery_recall=delivered / len(labels["facts"]),
            complete_tuple_delivery_recall=sum(all(token in context.text for token in [
                "row=" + f["scientific_tuple"]["subject"] + " | column=" + f["scientific_tuple"]["metric"] + " | value=" + f["scientific_tuple"]["value"],
                f["scientific_tuple"]["dataset"], f["scientific_tuple"]["setting"]]) for f in labels["facts"]) / len(labels["facts"]),
            abstained_candidates=sum(i.final == "ABSTAINED" for i in candidates), attempted_candidates=len(candidates),
            provenance_preservation=(sum(bool(i.source_refs) and all(r.chunk_id in {c.chunk_id for c in chunks}
                and r.paper_id == document.paper.paper_id for r in i.source_refs) for i in returned) / len(returned)) if returned else None)
        elapsed = (time.perf_counter() - started) * 1000
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        report["configurations"][arm] = {"status": "EXECUTED", "retrieval": retrieval, "context": assembly,
            "metrics": metrics, "latency_ms": elapsed, "python_peak_allocated_bytes": peak,
            "actual_model_tokens": None, "delivery_trace": context.trace, "fact_traces": traces}
    if annotation_path.read_bytes() != frozen:
        raise RuntimeError("annotations changed during evaluation")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("outputs/fixture_evaluation.json"))
    args = parser.parse_args()
    report = evaluate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({arm: value.get("metrics", value) for arm, value in report["configurations"].items()}, indent=2))


if __name__ == "__main__":
    main()
