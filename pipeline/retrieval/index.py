"""Shared BGE-M3 encoder and lossless per-project Chroma storage.

Batching/normalization follows original src/embedding/build_index.py; destructive
whole-collection rebuilds are replaced by paper-scoped replacement.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from shared.schemas import Chunk

MODEL = "BAAI/bge-m3"
MODEL_REVISION = "5617a9f61b028005a4858fdac845db406aefb181"


class BGEEncoder:
    def __init__(self, device: str = "cpu", local_only: bool = True):
        self.device, self.local_only = device, local_only
        self._model = None

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(MODEL, revision=MODEL_REVISION, device=self.device,
                                               local_files_only=self.local_only)
            self._model.max_seq_length = 1024
            if self.device.startswith("cuda"):
                self._model.half()
        return self._model

    def encode(self, texts: list[str]):
        return self.model.encode(texts, batch_size=16, normalize_embeddings=True,
                                 show_progress_bar=False, convert_to_numpy=True).tolist()


class ChromaIndex:
    def __init__(self, project_id: str, path: str | Path = "data/chroma", encoder=None, client=None):
        import chromadb
        self.encoder = encoder or BGEEncoder()
        Path(path).mkdir(parents=True, exist_ok=True)
        self.client = client or chromadb.PersistentClient(path=str(path))
        name = "rgpt_v2_" + hashlib.sha256(project_id.encode()).hexdigest()[:24]
        signature = getattr(self.encoder, "signature", f"{MODEL}@{MODEL_REVISION}:1024:normalized")
        self.collection = self.client.get_or_create_collection(name=name, embedding_function=None,
            metadata={"hnsw:space": "cosine", "embedding_signature": signature})
        if self.collection.metadata.get("embedding_signature") != signature:
            raise ValueError("collection embedding configuration mismatch")

    def replace_paper(self, paper_id: str, chunks: list[Chunk]):
        if any(c.paper_id != paper_id for c in chunks):
            raise ValueError("cannot index chunks from a different paper")
        if len({c.chunk_id for c in chunks}) != len(chunks):
            raise ValueError("duplicate chunk_id")
        vectors = self.encoder.encode([c.text for c in chunks]) if chunks else []
        # Encode before mutation, so an unavailable model does not erase a good index.
        old = set(self.collection.get(where={"paper_id": paper_id})["ids"])
        for start in range(0, len(chunks), 500):
            batch = chunks[start:start + 500]
            self.collection.upsert(ids=[c.chunk_id for c in batch], documents=[c.text for c in batch],
                embeddings=vectors[start:start + 500], metadatas=[{"paper_id": c.paper_id,
                    "chunk_json": c.model_dump_json()} for c in batch])
        stale = old - {c.chunk_id for c in chunks}
        if stale:
            self.collection.delete(ids=sorted(stale))

    def all_chunks(self, paper_id: str) -> list[Chunk]:
        result = self.collection.get(where={"paper_id": paper_id}, include=["metadatas"])
        return sorted([Chunk.model_validate_json(m["chunk_json"]) for m in result["metadatas"]],
                      key=lambda c: c.chunk_index)

    def search(self, query: str, paper_id: str, n: int = 50) -> list[Chunk]:
        count = len(self.collection.get(where={"paper_id": paper_id})["ids"])
        if not count:
            return []
        result = self.collection.query(query_embeddings=self.encoder.encode([query]),
            where={"paper_id": paper_id}, n_results=min(n, count), include=["metadatas"])
        return [Chunk.model_validate_json(m["chunk_json"]) for m in result["metadatas"][0]]
