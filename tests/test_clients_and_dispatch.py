import pytest

from pipeline.extraction.clients import OllamaClient, HostedClient, extraction_schema, parse_object
from pipeline.parsing.documents import process
from shared.interfaces import AcquiredDocument
from shared.schemas import Paper

pytestmark = pytest.mark.unit


def test_local_client_sends_full_id_enum_and_retains_actual_usage(monkeypatch):
    class Response:
        def raise_for_status(self): pass
        def json(self):
            return {"done": True, "done_reason": "stop", "message": {"content": '{"results":[]}'},
                    "prompt_eval_count": 123, "eval_count": 10}
    def post(url, **kw):
        assert kw["json"]["format"]["properties"]["results"]["items"]["properties"]["chunk_id"]["enum"] == ["S:2#0"]
        assert kw["json"]["options"]["num_predict"] == 768
        return Response()
    monkeypatch.setattr("pipeline.extraction.clients.requests.post", post)
    response = OllamaClient().complete("system", "[S:2#0]\nEvidence")
    assert response.prompt_tokens == 123 and response.completion_tokens == 10


def test_bad_json_and_incomplete_output_fail_explicitly(monkeypatch):
    for value in ("[]", "broken"):
        with pytest.raises(ValueError): parse_object(value)
    class Response:
        def raise_for_status(self): pass
        def json(self): return {"done": True, "done_reason": "length"}
    monkeypatch.setattr("pipeline.extraction.clients.requests.post", lambda *a, **kw: Response())
    with pytest.raises(ValueError, match="incomplete"):
        OllamaClient().complete("system", "[S:0#0]\nEvidence")


def test_hosted_transport_contract_without_network_or_credentials(monkeypatch):
    monkeypatch.setenv("TEST_LLM_KEY", "test-placeholder")
    class Response:
        def raise_for_status(self): pass
        def json(self): return {"choices": [{"finish_reason": "stop", "message": {"content": '{"results":[]}'}}],
                                "usage": {"prompt_tokens": 10, "completion_tokens": 3}}
    def post(url, **kw):
        assert url == "https://provider.invalid/v1/chat/completions"
        assert kw["headers"]["Authorization"] == "Bearer test-placeholder"
        return Response()
    monkeypatch.setattr("pipeline.extraction.clients.requests.post", post)
    out = HostedClient("test-model", "https://provider.invalid/v1", "TEST_LLM_KEY").complete("sys", "text")
    assert out.provider == "hosted" and out.prompt_tokens == 10


def test_latex_and_abstract_dispatch_preserve_identity_and_structure():
    paper = Paper(paper_id="ARX", acquisition_status="FULL_TEXT", has_full_text=True, representation_type="latex",
                  identity_validation={"passed": True, "signals": {"identity_source": "arxiv_pdf"}},
                  content_validation={"passed": True})
    tex = br'''\documentclass{article}\begin{document}\section{Results}
    Our Dice score is 91.4.\begin{table}\caption{Results on ExampleSet test set}
    \begin{tabular}{lr}Model & Dice (\%) \\ Ours & 91.4 \\ Baseline & 85.1 \\
    \end{tabular}\end{table}\end{document}'''
    doc, cs = process(AcquiredDocument(paper, tex))
    assert doc["representation"] == "latex" and all(c.paper_id == "ARX" for c in cs)
    assert any(c.table_cells for c in cs)
    abstract = Paper(paper_id="ABS", abstract="A real abstract text.", representation_type="abstract", acquisition_status="ABSTRACT_ONLY")
    doc, cs = process(AcquiredDocument(abstract, None))
    assert doc["representation"] == "abstract" and cs[0].page_or_node == "metadata/abstract"
