"""Classify actual completed response candidates without inventing/replaying any."""
import argparse
import json
import re
from pathlib import Path


def norm(s):
    return " ".join(s.split())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    raw = json.loads((args.run / "ollama_response.json").read_text(encoding="utf-8"))
    if raw.get("done_reason") != "stop":
        raise ValueError("incomplete packets are not converted into candidate predictions")
    generated = json.loads(raw["message"]["content"])
    execution = json.loads((args.run / "execution.json").read_text(encoding="utf-8"))
    chunks = json.loads((args.run / "chunks.json").read_text(encoding="utf-8"))
    context = json.loads((args.run / "context.json").read_text(encoding="utf-8"))
    by_id = {c["chunk_id"]: c for c in chunks}
    delivered = {c["chunk_id"]: c for c in context["delivered_chunks"]}
    rows = []
    for field, candidates in generated.items():
        for i, candidate in enumerate(candidates):
            quote, cid = candidate.get("evidence_span", ""), candidate.get("chunk_id")
            source = by_id.get(cid, {})
            shown = delivered.get(cid, {})
            verdict = execution["candidate_verdicts"][field][i]
            literal = bool(quote and quote in shown.get("text", ""))
            normalized = bool(quote and norm(quote) in norm(shown.get("text", "")))
            alternatives = [c["chunk_id"] for c in chunks if quote and norm(quote) in norm(c["text"])]
            if not shown:
                category = "invalid_or_undelivered_chunk_id"
            elif not literal and normalized:
                category = "model_changed_quote_whitespace"
            elif not literal and alternatives:
                category = "model_attributed_quote_to_wrong_chunk"
            elif not literal:
                category = "model_quote_not_literal_in_source_or_delivered_span"
            elif verdict["final"] == "ABSTAINED":
                category = "withheld_by_evidence_contract_" + str(verdict.get("abstain_reason"))
            else:
                category = "source_quote_verified_under_current_contract"
            rows.append({"candidate_id": f"{field}:{i}", "field": field, "chunk_id": cid,
                "page_or_node": source.get("page_or_node"), "block_id": source.get("block_id"),
                "char_start": source.get("char_start"), "char_end": source.get("char_end"),
                "contains_digits": bool(re.search(r"\d", candidate.get("value", ""))),
                "numerical_tokens": re.findall(r"\d+(?:\.\d+)?", candidate.get("value", "")),
                "scientific_tuple": candidate.get("scientific_tuple"), "literal_quote_delivered": literal,
                "normalized_quote_delivered": normalized, "normalized_source_matches": alternatives,
                "earliest_supported_candidate_failure": None if verdict["final"] == "RETURNED" else "extraction/source_attribution",
                "classification": category, "final": verdict["final"], "abstain_reason": verdict.get("abstain_reason"),
                "source_reference_count": len(verdict.get("source_refs", []))})
    summary = {"scope": "actual completed local model output; no simulated candidates", "candidate_count": len(rows),
        "returned": sum(r["final"] == "RETURNED" for r in rows),
        "withheld_generated": sum(r["final"] == "ABSTAINED" for r in rows),
        "numerical_mention_count": sum(r["contains_digits"] for r in rows),
        "typed_numerical_tuple_count": sum(bool(r["scientific_tuple"]) for r in rows),
        "verified_numerical_tuples": sum(bool(r["scientific_tuple"]) and r["final"] == "RETURNED" for r in rows),
        "independent_scientific_accuracy": "NOT ESTABLISHED", "candidates": rows}
    (args.run / "candidate_classification.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
