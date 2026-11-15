"""Sequential model lifecycle regression; doubles isolate ownership, not GPU memory."""
import pytest

from pipeline.service import EvidencePipeline
from tests.helpers import fixture_document, QuotedFixtureLLM

pytestmark = pytest.mark.integration


def test_embedding_owner_releases_before_llm_extraction():
    document = fixture_document()
    class Index:
        released = False
        def replace_paper(self, pid, chunks): self.chunks = chunks
        def search(self, *args): return self.chunks
        def release_encoder(self): self.released = True
    index = Index()
    class LLM(QuotedFixtureLLM):
        def complete(self, *args):
            assert index.released, "embedding model still owned when extraction starts"
            return super().complete(*args)
    result = EvidencePipeline(None, index, LLM()).run(document.paper, document)
    assert result.status == "PARTIAL"
    assert index.released


def test_failed_indexing_releases_owned_model():
    document = fixture_document()
    class Index:
        released = False
        def replace_paper(self, *args): raise RuntimeError("index failure")
        def release_encoder(self): self.released = True
    index = Index()
    result = EvidencePipeline(None, index, None).run(document.paper, document)
    assert result.status == "INDEXING_FAILED" and index.released
