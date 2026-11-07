import json
import pytest
from scripts.analyze_real_paper import main

pytestmark = pytest.mark.unit


def test_analysis_preserves_utf8_scientific_source_quotes(tmp_path, monkeypatch):
    text = "The error is α = 0.5."
    candidate = {"value": text, "evidence_span": text, "chunk_id": "S:0#0"}
    response = {"done_reason": "stop", "message": {"content": json.dumps({"results": [candidate]})}}
    chunk = {"chunk_id": "S:0#0", "block_id": "S:0", "text": text, "page_or_node": "p1", "char_start": 0, "char_end": len(text)}
    payloads = {"ollama_response.json": response, "execution.json": {"candidate_verdicts": {"results": [{"final": "RETURNED", "source_refs": []}]}},
                "chunks.json": [chunk], "context.json": {"delivered_chunks": [chunk]}}
    for name, data in payloads.items():
        (tmp_path / name).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["analyze_real_paper", str(tmp_path)])
    main()
    result = json.loads((tmp_path / "candidate_classification.json").read_text(encoding="utf-8"))
    assert result["candidates"][0]["literal_quote_delivered"] is True
