"""Context assembly with an explicit evidence delivery trace."""
from dataclasses import dataclass, field

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
        text = " ".join(take)
        copy = c.model_copy(update={"text": text})
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
