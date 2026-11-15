"""Executable five-query baseline and optional identity-preserving hybrid adapter."""
from __future__ import annotations

import re

from shared.schemas import Chunk, RetrievalHit

# Verbatim query vocabulary from original retrieval_aware.py at audited SHA.
TARGET_QUERIES = [
    "problem statement research gap motivation background",
    "method approach study design procedure participants sample",
    "results findings outcomes performance evaluation",
    "dataset survey data collection measures instruments",
    "limitations discussion conclusion implications future work",
]


class FiveQueryRetriever:
    def __init__(self, index, per_query: int = 50):
        self.index, self.per_query = index, per_query

    def retrieve(self, paper_id: str, chunks: list[Chunk]) -> list[Chunk]:
        ids = {c.chunk_id for q in TARGET_QUERIES for c in self.index.search(q, paper_id, self.per_query)}
        # Match executable original: source-order union, fallback to all if empty.
        return sorted([c for c in chunks if c.chunk_id in ids] or list(chunks), key=lambda c: c.chunk_index)


class HybridRetriever:
    """BM25 + vector rank fusion, optional cross-encoder; actual chunk IDs throughout.

    Conceptual boundary follows teammate HybridRetriever. This is a narrow new
    adapter, not a claim to reproduce its prefix-based score normalization.
    """
    def __init__(self, index, top_k: int = 50, reranker=None):
        from rank_bm25 import BM25Okapi
        self.bm25_class = BM25Okapi
        self.index, self.top_k, self.reranker = index, top_k, reranker

    def retrieve(self, paper_id: str, chunks: list[Chunk]) -> list[Chunk]:
        corpus = [c for c in chunks if c.paper_id == paper_id]
        if not corpus:
            return []
        tokenize = lambda s: re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", s.lower())
        bm25 = self.bm25_class([tokenize(c.text) for c in corpus])
        scores, by_id = {}, {c.chunk_id: c for c in corpus}
        for query in TARGET_QUERIES:
            sparse_scores = bm25.get_scores(tokenize(query))
            sparse = [corpus[i] for i in sorted(range(len(corpus)), key=lambda i: (-sparse_scores[i], corpus[i].chunk_id))
                      if sparse_scores[i] > 0][:self.top_k]
            dense = self.index.search(query, paper_id, self.top_k)
            for ranking in (dense, sparse):
                for rank, c in enumerate(ranking, 1):
                    if c.chunk_id not in by_id or c.paper_id != paper_id:
                        raise ValueError("retriever returned unknown chunk identity")
                    scores[c.chunk_id] = scores.get(c.chunk_id, 0) + 1 / (60 + rank)
        selected = [by_id[cid] for cid in sorted(scores, key=lambda k: (-scores[k], k))[:self.top_k]]
        if self.reranker and selected:
            values = self.reranker.predict([[" ".join(TARGET_QUERIES), c.text] for c in selected])
            if len(values) != len(selected):
                raise ValueError("reranker score count differs from candidates")
            selected = [c for _, c in sorted(zip(values, selected), key=lambda pair: (-float(pair[0]), pair[1].chunk_id))]
        return [c.model_copy(update={"retrieval_score": scores[c.chunk_id], "retrieval_rank": rank,
                                    "retrieval_strategy": "hybrid_rrf_v1", "score_kind": "rrf",
                                    "reranked": self.reranker is not None})
                for rank, c in enumerate(selected, 1)]


class TableAwareRetriever(FiveQueryRetriever):
    """Versioned caption/header/row link expansion of the unchanged five queries.

    A table must first be found through ordinary retrieval. Expansion uses only
    parser links and canonical IDs, never answer values or extra query terms.
    """
    def retrieve(self, paper_id: str, chunks: list[Chunk]) -> list[Chunk]:
        baseline = super().retrieve(paper_id, chunks)
        seeds = {getattr(c, "table_id", None) for c in baseline} - {None}
        by_id = {c.chunk_id: c for c in baseline}
        self.expansion_trace = []
        for c in chunks:
            if c.paper_id == paper_id and getattr(c, "table_id", None) in seeds and c.chunk_id not in by_id:
                by_id[c.chunk_id] = c
                self.expansion_trace.append({"chunk_id": c.chunk_id, "table_id": c.table_id,
                                             "strategy": "table_link_expansion_v1", "score": None})
        return sorted(by_id.values(), key=lambda c: c.chunk_index)


def scored_records(chunks: list[Chunk], strategy: str, queries: list[dict], expansion=()) -> list[RetrievalHit]:
    """Export source-preserving retrieval records without mixing score scales.

    Dense union score is the best observed cosine similarity across the five
    queries, not a new ranking. Expanded rows have no fabricated dense score.
    Hybrid score is RRF before optional reranking; rank is final returned order.
    """
    best = {}
    for query in queries:
        for hit in query.get("hits", []):
            if hit["chunk_id"] not in best or hit["score"] > best[hit["chunk_id"]]["score"]:
                best[hit["chunk_id"]] = {**hit, "query": query["query"]}
    expanded = {e["chunk_id"] for e in expansion}
    records = []
    for rank, c in enumerate(chunks, 1):
        observed = best.get(c.chunk_id, {})
        is_expanded = c.chunk_id in expanded
        score = getattr(c, "retrieval_score", observed.get("score"))
        records.append(RetrievalHit(chunk=c, rank=rank, score=None if is_expanded else score,
            score_kind="unscored_link" if is_expanded else getattr(c, "score_kind", "cosine_similarity"),
            strategy="table_link_expansion_v1" if is_expanded else strategy,
            query=observed.get("query") if not is_expanded else None))
    return records
