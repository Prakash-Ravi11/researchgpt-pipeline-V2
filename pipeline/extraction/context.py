"""Context assembly with an explicit evidence delivery trace."""
from dataclasses import dataclass, field
import re

from shared.schemas import Chunk


@dataclass
class Context:
    text: str
    chunks: list[Chunk]
    trace: dict = field(default_factory=dict)


def current_context(chunks: list[Chunk], max_words: int = 2500) -> Context:
    """Original source-order, word-prefix assembly; added headers identify sources."""
    used, parts, delivered, partial = 0, [], [], []
    for c in chunks:
        words = c.text.split()
        take = words[:max(0, max_words - used)]
        if not take:
            break
        end = list(re.finditer(r"\S+", c.text))[len(take) - 1].end()
        text = c.text[:end]
        copy = c.model_copy(update={"text": text, "char_end": c.char_start + end})
        delivered.append(copy)
        parts.append(f"[{c.chunk_id}]\n{text}")
        used += len(take)
        if len(take) < len(words):
            partial.append(c.chunk_id)
    return Context("\n\n".join(parts), delivered, {
        "mode": "current", "max_words": max_words,
        "retrieved_chunk_ids": [c.chunk_id for c in chunks],
        "delivered_chunk_ids": [c.chunk_id for c in delivered], "partial_chunk_ids": partial,
        "dropped_chunk_ids": [c.chunk_id for c in chunks if c.chunk_id not in {d.chunk_id for d in delivered}],
        "content_words": used, "token_count": None, "token_count_method": "unmeasured"})


def render_chunk(chunk: Chunk) -> str:
    """Explicit relationships, never a detached bag of table numbers."""
    if not chunk.table_cells:
        return chunk.text
    rows = [chunk.text, "Table caption: " + chunk.table_caption]
    for cell in chunk.table_cells:
        rows.append(f"row={cell.get('row_label', '')} | column={cell.get('column_header', '')} | "
                    f"value={cell.get('value', '')}")
    return "\n".join(rows)


def revised_context(chunks: list[Chunk], max_words: int = 2500, budget: int = 6000,
                    token_counter=None, counter_name: str | None = None) -> Context:
    """Evidence-first whole chunks, explicit tables, and observable budget decisions.

    A configured model tokenizer may supply exact counts. Without one, budget
    units are UTF-8 bytes (a conservative proxy), explicitly NOT token counts.
    The 8192 local window reserves 768 output plus 1424 units for wrappers.
    Model-service prompt_eval_count remains the actual observed usage.
    """
    counter = token_counter or (lambda text: len(text.encode("utf-8")))
    method = counter_name or ("provided_tokenizer" if token_counter else "utf8_bytes_proxy")
    def priority(c):
        return (0 if c.table_cells else 1 if c.section == "results" else
                2 if c.section in ("experimental_setup", "method") else
                3 if c.section in ("limitations", "conclusion", "discussion") else 4, c.chunk_index)
    parts, delivered, skipped = [], [], []
    table_blocks = set()
    for c in sorted(chunks, key=priority):
        if c.table_cells and c.block_id in table_blocks:
            skipped.append({"chunk_id": c.chunk_id, "reason": "same_table_block_already_delivered"})
            continue
        rendered = render_chunk(c)
        part = f"[{c.chunk_id}]\n{rendered}"
        candidate = "\n\n".join(parts + [part])
        if counter(candidate) > budget or len(candidate.split()) > max_words:
            skipped.append({"chunk_id": c.chunk_id, "reason": "whole_chunk_exceeds_remaining_budget"})
            continue
        parts.append(part)
        # Original text/offsets remain intact; rendered context is recorded
        # separately, so a generated table label is never presented as a quote.
        delivered.append(c)
        if c.table_cells:
            table_blocks.add(c.block_id)
    text = "\n\n".join(parts)
    return Context(text, delivered, {"mode": "revised", "max_words": max_words,
        "budget": budget, "budget_units_used": counter(text), "budget_method": method,
        "token_count": counter(text) if token_counter else None,
        "token_count_method": method if token_counter else "unmeasured",
        "retrieved_chunk_ids": [c.chunk_id for c in chunks],
        "delivered_chunk_ids": [c.chunk_id for c in delivered], "partial_chunk_ids": [],
        "dropped_chunk_ids": [s["chunk_id"] for s in skipped], "drop_reasons": skipped,
        "structured_tables_delivered": len(table_blocks), "content_words": len(text.split())})


def table_aware_context(chunks: list[Chunk], max_words: int = 2500, budget: int = 6000) -> Context:
    """Deliver linked source blocks atomically; keep uncertain tables unstructured.

    The conservative UTF-8-byte budget is not a model token measurement. Every
    linked header/caption/row retains its own original ID and quoting boundary.
    """
    groups = {}
    for c in chunks:
        key = getattr(c, "table_id", None) or c.chunk_id
        groups.setdefault(key, []).append(c)
    def priority(group):
        return (0 if getattr(group[0], "table_id", None) else
                1 if group[0].section == "results" else 2, group[0].chunk_index)
    delivered, parts, skipped = [], [], []
    for group in sorted(groups.values(), key=priority):
        part = "\n\n".join(f"[{c.chunk_id}]\n{render_chunk(c)}" for c in group)
        text = "\n\n".join(parts + [part])
        if len(text.encode("utf-8")) > budget or len(text.split()) > max_words:
            skipped.extend({"chunk_id": c.chunk_id, "reason": "whole_evidence_group_exceeds_budget"} for c in group)
            continue
        delivered.extend(group)
        parts.append(part)
    text = "\n\n".join(parts)
    return Context(text, delivered, {"mode": "table_aware_v1", "budget": budget, "max_words": max_words,
        "budget_method": "utf8_bytes_proxy", "budget_units_used": len(text.encode("utf-8")),
        "token_count": None, "token_count_method": "unmeasured", "content_words": len(text.split()),
        "retrieved_chunk_ids": [c.chunk_id for c in chunks], "delivered_chunk_ids": [c.chunk_id for c in delivered],
        "partial_chunk_ids": [], "dropped_chunk_ids": [s["chunk_id"] for s in skipped], "drop_reasons": skipped,
        "delivered_table_ids": sorted({c.table_id for c in delivered if getattr(c, "table_id", None)})})
