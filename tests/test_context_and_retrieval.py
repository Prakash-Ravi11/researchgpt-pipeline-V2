import pytest

from pipeline.extraction.context import current_context, revised_context
from pipeline.retrieval.retrievers import FiveQueryRetriever, HybridRetriever, TARGET_QUERIES
from pipeline.parsing.documents import process
from tests.helpers import fixture_document

pytestmark = pytest.mark.unit


def test_revised_context_delivers_tail_evidence_and_structured_relationships():
    _, cs = process(fixture_document())
    distractor = cs[0].model_copy(update={"chunk_id": "SYN:extra#0", "block_id": "SYN:extra", "chunk_index": -1,
        "text": "background " * 250, "section": "introduction_related_work"})
    current = current_context([distractor] + cs, max_words=250)
    revised = revised_context([distractor] + cs, max_words=250, budget=6000)
    assert "91.4" not in current.text
    assert "Our method achieves" in revised.text
    assert "row=Ours | column=Dice (%) | value=91.4" in revised.text
    assert not revised.trace["partial_chunk_ids"]
    assert revised.trace["token_count"] is None


def test_revised_exact_counter_and_whole_chunk_limit():
    _, cs = process(fixture_document())
    ctx = revised_context(cs, budget=50, token_counter=lambda s: len(s.split()), counter_name="test_whitespace")
    assert ctx.trace["token_count"] <= 50
    assert ctx.trace["drop_reasons"]
    assert ctx.trace["token_count_method"] == "test_whitespace"


def test_five_query_baseline_preserves_executable_parameters():
    _, cs = process(fixture_document())
    class Index:
        calls = []
        def search(self, q, pid, n):
            self.calls.append((q, pid, n))
            return cs
    index = Index()
    assert FiveQueryRetriever(index).retrieve("SYN", cs) == cs
    assert index.calls == [(q, "SYN", 50) for q in TARGET_QUERIES]


def test_real_bm25_fusion_preserves_identity_and_duplicate_prefixes():
    pytest.importorskip("rank_bm25")
    _, cs = process(fixture_document())
    # Distinct source blocks can share the same 100-character prefix.
    same = "results findings evaluation " * 6
    one = cs[1].model_copy(update={"text": same + "one"})
    two = cs[2].model_copy(update={"text": same + "two"})
    class Index:
        def search(self, q, pid, n):
            return [one, two]
    class Reranker:
        def predict(self, pairs):
            return list(range(len(pairs)))
    out = HybridRetriever(Index(), reranker=Reranker()).retrieve("SYN", [one, two, cs[-1]])
    assert {c.chunk_id for c in out} >= {one.chunk_id, two.chunk_id}
    assert all(not c.chunk_id.startswith("bm25_") for c in out)
    assert len({c.chunk_id for c in out}) == len(out)
