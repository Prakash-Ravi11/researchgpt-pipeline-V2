"""Transport trace preserves actual usage even when incomplete output is rejected."""
import pytest
from pipeline.extraction.clients import OllamaClient

pytestmark = pytest.mark.unit


def test_raw_incomplete_model_response_is_observable(monkeypatch):
    events = []
    class Response:
        def raise_for_status(self): pass
        def json(self):
            return {"done": True, "done_reason": "length", "prompt_eval_count": 321, "eval_count": 768,
                    "message": {"content": '{"results":['}}
    monkeypatch.setattr("pipeline.extraction.clients.requests.post", lambda *a, **kw: Response())
    with pytest.raises(ValueError, match="incomplete"):
        OllamaClient(observer=lambda event, data: events.append((event, data))).complete("sys", "[S:0#0]\nSource")
    assert [e[0] for e in events] == ["request", "response"]
    assert events[-1][1]["prompt_eval_count"] == 321


def test_optional_candidate_budget_rejects_excess_without_changing_default(monkeypatch):
    from jsonschema import validate, ValidationError
    from pipeline.extraction.prompt import FIELDS
    captured = []
    class Response:
        def raise_for_status(self): pass
        def json(self): return {"done": True, "done_reason": "stop", "message": {"content": '{"results":[]}'}}
    def post(url, **kwargs):
        captured.append(kwargs["json"])
        return Response()
    monkeypatch.setattr("pipeline.extraction.clients.requests.post", post)
    source = "[S:0#0]\nA complete source quotation."
    OllamaClient(max_candidates_per_field=1).complete("sys", source)
    candidate = {"value": "A complete source quotation.", "evidence_span": "A complete source quotation.", "chunk_id": "S:0#0"}
    packet = {field: [] for field in FIELDS}
    packet["method"] = [candidate, candidate]
    with pytest.raises(ValidationError): validate(packet, captured[0]["format"])
    OllamaClient().complete("sys", source)
    validate(packet, captured[1]["format"])
