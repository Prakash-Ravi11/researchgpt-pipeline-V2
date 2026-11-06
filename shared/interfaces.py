"""Narrow interfaces; concrete implementations do not depend on API routes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .schemas import Chunk, LLMResponse, Paper


@dataclass
class AcquiredDocument:
    paper: Paper
    data: bytes | None
    pdf_fallback: bytes | None = None


@runtime_checkable
class DocumentSource(Protocol):
    def acquire(self, paper: Paper) -> AcquiredDocument: ...


@runtime_checkable
class Retriever(Protocol):
    def retrieve(self, paper_id: str, chunks: list[Chunk]) -> list[Chunk]: ...


@runtime_checkable
class LLMClient(Protocol):
    def complete(self, system: str, user: str) -> LLMResponse: ...
