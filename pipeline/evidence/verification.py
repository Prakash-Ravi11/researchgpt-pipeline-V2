"""Validated legacy gate plus conservative source-quote and complete-tuple checks."""
from __future__ import annotations

import re

from shared.schemas import Chunk, FieldValue, Paper
from src.evidence.gate import _gate_value
from pipeline.evidence.quotes import resolve_quote


def _contains_number(text: str, number: str) -> bool:
    return bool(re.search(r"(?<![\w.])" + re.escape(number) + r"(?!\w|\.\d)", text))


def verify_candidate(field: str, candidate, paper: Paper, delivered: list[Chunk], corpus: list[Chunk]) -> FieldValue:
    value = candidate.get("value") if isinstance(candidate, dict) else str(candidate)
    item = FieldValue(field=field, value=value, status="ABSTAINED", evidence_status="UNSUPPORTED")

    def reject(reason):
        item.abstain_reason = reason
        return item

    if not isinstance(candidate, dict) or not isinstance(value, str) or not value.strip():
        return reject("invalid_candidate")
    if field in ("datasets", "metrics", "results") and paper.acquisition_status != "FULL_TEXT":
        return reject("no_validated_full_text")
    hit = next((c for c in delivered if c.chunk_id == candidate.get("chunk_id")), None)
    if hit is None or hit.paper_id != paper.paper_id:
        return reject("source_chunk_not_delivered")
    quote = candidate.get("evidence_span")
    if not isinstance(quote, str) or not quote.strip():
        return reject("quote_not_in_delivered_chunk")
    delivered_match, error = resolve_quote(hit.text, quote)
    if error:
        if error == "ambiguous":
            item.status = "AMBIGUOUS"
        return reject("ambiguous_quote" if error == "ambiguous" else "quote_not_in_delivered_chunk")
    original = next((c for c in corpus if c.chunk_id == hit.chunk_id), None)
    if original is None or original.paper_id != paper.paper_id:
        return reject("quote_not_in_original_source_chunk")
    source_match, error = resolve_quote(original.text, quote)
    if error:
        if error == "ambiguous":
            item.status = "AMBIGUOUS"
        return reject("ambiguous_quote" if error == "ambiguous" else "quote_not_in_original_source_chunk")
    if original.char_start + source_match.start != hit.char_start + delivered_match.start:
        return reject("source_offset_disagrees")
    # An unrelated real quote cannot support an invented paraphrase.
    value_match, error = resolve_quote(source_match.text, value)
    if error:
        if error == "ambiguous":
            item.status = "AMBIGUOUS"
        return reject("ambiguous_value" if error == "ambiguous" else "value_not_in_source_quote")
    item.proposed_value = value
    item.proposed_evidence_span = quote
    value, quote = value_match.text, source_match.text
    item.value = value
    if not quote:
        return reject("value_not_in_source_quote")
    ref = original.reference()
    offset = source_match.start
    refs = [ref.model_copy(update={"char_start": ref.char_start + offset,
                                  "char_end": ref.char_start + offset + len(quote)})]
    quantitative = field in ("results", "metrics", "key_findings") and bool(re.search(r"\d", value))
    if field in ("datasets", "metrics", "results") or quantitative:
        check_field = "results" if quantitative else field
        evidence = _gate_value(check_field, value, [c.model_dump() for c in corpus], [])
        item.legacy_verdict = evidence
        if evidence["final"] != "RETURNED":
            return reject(evidence.get("abstain_reason") or "legacy_gate_rejected")
    if quantitative:
        tup = candidate.get("scientific_tuple")
        required = ("subject", "dataset", "metric", "value")
        if not isinstance(tup, dict) or not all(isinstance(tup.get(k), str) and tup[k].strip() for k in required):
            return reject("incomplete_scientific_tuple")
        if not _contains_number(value, tup["value"]):
            return reject("tuple_value_not_in_claim")
        from src.evidence.anchors import anchor_values
        # A single tuple cannot license extra measurements in the same claim.
        anchors = anchor_values(value)
        labels = " ".join(tup[k] for k in ("subject", "dataset", "metric"))
        if anchors - anchor_values(labels) - anchor_values(tup["value"]):
            return reject("additional_measurements_require_separate_tuples")
        # Each relationship must come from ONE cell and its own caption, not a
        # model in one experiment and a number in another experiment/table.
        matches = []
        for c in corpus:
            for cell in c.table_cells:
                same = (tup["subject"].casefold() == cell.get("row_label", "").casefold()
                        and tup["metric"].casefold() == cell.get("column_header", "").casefold()
                        and _contains_number(str(cell.get("value", "")), tup["value"]))
                scope = cell.get("caption", "")
                legacy_cell = evidence.get("structural_binding", {}).get("cell", {})
                agrees = (legacy_cell.get("row") == cell.get("row_label")
                          and legacy_cell.get("col") == cell.get("column_header")
                          and legacy_cell.get("caption") == cell.get("caption"))
                if same and agrees and tup["dataset"].casefold() in scope.casefold():
                    if tup.get("setting") and tup["setting"].casefold() not in scope.casefold():
                        continue
                    matches.append(c)
        if len({c.block_id for c in matches}) != 1:
            return reject("tuple_scope_unverified_or_ambiguous")
        if matches[0].chunk_id != hit.chunk_id:
            refs.append(matches[0].reference())
        item.scientific_tuple = tup
    return FieldValue(**{**item.model_dump(), "final": "RETURNED", "status": "VERIFIED",
        "evidence_status": "EXPLICIT", "provenance_valid": True, "confidence": 0.8,
        "evidence_span": quote, "source_refs": refs, "abstain_reason": None})
