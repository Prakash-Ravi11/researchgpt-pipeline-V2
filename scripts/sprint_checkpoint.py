"""Replay saved *actual* predictions and prepare an explicitly unreviewed queue.

No model call, new predictions, gold labels or scoring changes. The source PDF
is local, hash-checked, and never copied into tracked review artifacts.
"""
import argparse
import hashlib
import json
from pathlib import Path

from pipeline.acquisition.source import from_bytes
from pipeline.evidence.verification import verify_candidate
from pipeline.parsing.documents import process
from shared.schemas import Chunk, Paper


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, default=Path("outputs/recovery/gpu-current-03-bounded"))
    parser.add_argument("--output", type=Path, default=Path("outputs/sprint/checkpoint"))
    args = parser.parse_args()
    read = lambda path: json.loads(path.read_text(encoding="utf-8"))
    paper = Paper.model_validate(read(Path("data/live/paper.json")))
    data = Path("data/live/document.pdf").read_bytes()
    assert hashlib.sha256(data).hexdigest() == paper.document_sha256
    document = from_bytes(paper, data, "pdf", "arxiv")
    parsed, enriched = process(document, "table_context_v1")
    source = {c.chunk_id: c for c in enriched}
    original = [Chunk(**c) for c in read(args.run / "chunks.json")]
    delivered = [Chunk(**c) for c in read(args.run / "context.json")["delivered_chunks"]]
    raw = read(args.run / "ollama_response.json")
    assert raw["done_reason"] == "stop"
    candidates = json.loads(raw["message"]["content"])
    old = read(args.run / "structured_output.json")
    rows = []
    for field, values in candidates.items():
        for i, candidate in enumerate(values):
            out = verify_candidate(field, candidate, document.paper, delivered, original)
            before = old["fields"][field][i]
            rows.append(dict(candidate_id=f"{field}:{i}", chunk_id=candidate["chunk_id"],
                before=before["final"], before_reason=before.get("abstain_reason"), after=out.final,
                after_reason=out.abstain_reason, status=out.status,
                refs=[r.model_dump() for r in out.source_refs], typed_tuple=bool(candidate.get("scientific_tuple"))))
    summary = dict(scope="replay of saved actual Qwen predictions; no new model calls or independent gold",
        source_run=str(args.run), source_sha256=paper.document_sha256,
        candidates=len(rows), before_returned=sum(r["before"] == "RETURNED" for r in rows),
        after_returned=sum(r["after"] == "RETURNED" for r in rows),
        recovered=sum(r["before"] != "RETURNED" and r["after"] == "RETURNED" for r in rows),
        verified_numeric=sum(r["typed_tuple"] and r["after"] == "RETURNED" for r in rows), rows=rows)
    write(args.output / "quote_replay.json", summary)
    write(args.output / "table_inspection.json", {k: v for k, v in parsed.items() if k != "blocks"})
    # Agent-proposed review entries, intentionally separate from frozen scoring.
    # These select source locations for a human; they are never generation hints.
    proposals = [
        (119, "results", "Transformer (big)", "English-to-German newstest2014", "BLEU", "28.4", "BLEU", "Table 2; header alignment needs human review"),
        (119, "results", "Transformer (big)", "English-to-French newstest2014", "BLEU", "41.8", "BLEU", "Table 2; distinct from prose 41.0"),
        (125, "results", "Transformer (big)", "WMT 2014 English-to-French", "BLEU", "41.0", "BLEU", "Section 6.1 prose; distinct from Table 2"),
        (35, "method", "Transformer encoder", None, "layers", "6", "layers", "Encoder stack"),
        (36, "method", "Transformer decoder", None, "layers", "6", "layers", "Decoder stack"),
        (35, "method", "Transformer base", None, "model dimension", "512", "dimensions", "dmodel; base architecture"),
        (65, "method", "Transformer base", None, "attention heads", "8", "heads", "h; not the big configuration"),
        (74, "method", "Transformer base", None, "feed-forward inner dimension", "2048", "dimensions", "dff"),
        (120, "method", "Transformer base", None, "residual dropout", "0.1", "probability", "Base model only; big EN-FR exception is separate"),
        (100, "method", "Transformer training", None, "hardware", "8", "NVIDIA P100 GPUs", "One machine"),
        (100, "method", "Transformer big", None, "training duration", "3.5", "days", "300,000 steps; separate from base 12 hours"),
        (119, "results", "Transformer (big)", "EN-DE / EN-FR table shared cost region", "training cost", "2.3e19", "FLOPs", "Printed exponent 19; cost spans language columns; attribution unresolved"),
    ]
    entries = []
    for i, (block, field, model, dataset, metric, value, unit, setting) in enumerate(proposals, 1):
        c = source[f"{paper.paper_id}:{block}#0"]
        entries.append(dict(annotation_id=f"attention-v7-{i:02}", paper_id=paper.paper_id,
            document_sha256=paper.document_sha256, source_version="arXiv:1706.03762v7 [cs.CL], 2 Aug 2023",
            source_pdf="data/live/document.pdf", field=field, experiment_or_model=model, dataset=dataset,
            metric=metric, value=value, unit=unit, setting=setting, exact_evidence_quote=c.text,
            page=c.page_or_node, section=c.section, chunk_id=c.chunk_id, block_id=c.block_id,
            table_id=getattr(c, "table_id", None), original_char_start=c.char_start, original_char_end=c.char_end,
            offset_basis=c.offset_basis, bbox=getattr(c, "source_bbox", None), bbox_scope="native PDF text block",
            table_source_parts=getattr(c, "table_context", {}).get("parts", []),
            confidence="agent source inspection only; not independent validation",
            status="needs_human_review", reviewer="", reviewed_at="", verdict=""))
    write(args.output / "annotations.template.json", dict(schema_version="review_queue_v1",
        evaluation_use="PROHIBITED until independent human review and a separately frozen evaluation design",
        annotations=entries))
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
