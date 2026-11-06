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
