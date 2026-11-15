import pytest
from fastapi.testclient import TestClient

from api.main import ProcessRequest, create_app
from pipeline.extraction.profiles import local_client
from pipeline.extraction.clients import extraction_schema
from pipeline.extraction.context import table_aware_context
from pipeline.retrieval.index import ChromaIndex
from pipeline.service import EvidencePipeline
from tests.helpers import fixture_document, TinyEncoder, QuotedFixtureLLM


def test_named_bounded_profile_preserves_default():
    default, bounded = local_client(), local_client("bounded")
    assert (default.output_tokens, default.num_ctx, default.max_candidates_per_field) == (768, 8192, None)
    assert (bounded.output_tokens, bounded.num_ctx, bounded.max_candidates_per_field) == (2048, 8192, 1)
    assert bounded.timeout == 180 and default.timeout == 120
    assert all(p["maxItems"] == 1 for p in extraction_schema("[SYN:0#0]\ntext", bounded.max_candidates_per_field)["properties"].values())
    with pytest.raises(ValueError):
        local_client("bounded", output_tokens=5)
    req = ProcessRequest(project_id="x", paper={"paper_id": "x"})
    assert req.generation_profile == "default" and req.representation_profile == "baseline"


def test_scored_adapter_keeps_source_and_separates_expansion_score():
    from pipeline.retrieval.retrievers import scored_records
    from pipeline.parsing.documents import process
    from shared.schemas import RetrievalHit
    _, chunks = process(fixture_document())
    one = chunks[0].model_copy(update={"table_id": "SYN:T", "source_bbox": [0, 1, 2, 3]})
    queries = [{"query": "results", "hits": [{"chunk_id": one.chunk_id, "score": .7}]}]
    record = scored_records([one], "five_query", queries)[0]
    assert record.score == .7 and record.score_kind == "cosine_similarity"
    assert RetrievalHit.model_validate_json(record.model_dump_json()).chunk == one
    expanded = scored_records([one], "table_aware_v1", queries, [{"chunk_id": one.chunk_id}])[0]
    assert expanded.score is None and expanded.score_kind == "unscored_link"
    assert expanded.chunk.reference().source_bbox == [0, 1, 2, 3]


@pytest.mark.integration
def test_optional_profiles_complete_fixture_api_flow(tmp_path):
    document = fixture_document()
    class FixtureSource:
        def acquire(self, paper):
            return document
    def factory(req):
        llm = QuotedFixtureLLM()
        llm.generation_profile = req.generation_profile  # no real generation claimed
        return EvidencePipeline(FixtureSource(), ChromaIndex(req.project_id, tmp_path / "db", TinyEncoder()), llm,
            retrieval=req.retrieval, context_mode=req.context_mode, context_builder=table_aware_context,
            representation_profile=req.representation_profile)
    with TestClient(create_app(factory)) as client:
        req = dict(project_id="profile", paper={"paper_id": "SYN"}, generation_profile="bounded",
                   retrieval="table_aware_v1", context_mode="table_aware_v1", representation_profile="table_context_v1")
        response = client.post("/api/papers/process", json=req)
        assert response.status_code == 200
        result = response.json()
        assert result["trace"]["generation_profile"] == "bounded"
        assert result["fields"]["results"][0]["status"] == "VERIFIED"
        assert result["trace"]["retrieval_queries"][0]["hits"][0]["score_kind"] == "cosine_similarity"
        ref = result["fields"]["results"][0]["source_refs"][0]
        assert ref["paper_id"] == "SYN" and ref["chunk_id"]
