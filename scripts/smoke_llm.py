"""Actual local model on synthetic source text; no dense-retrieval accuracy claim."""
import json
import argparse
from pathlib import Path

from pipeline.extraction.clients import OllamaClient
from pipeline.extraction.context import current_context
from pipeline.extraction.prompt import SYSTEM
from pipeline.parsing.documents import process
from tests.helpers import fixture_document


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="llm_smoke")
    args = parser.parse_args()
    if not args.name.replace("_", "").isalnum():
        raise ValueError("name must be an alphanumeric label")
    _, chunks = process(fixture_document())
    context = current_context(chunks)
    summary = {"class": "INTEGRATION", "document": "synthetic JATS fixture", "mock_model": False,
               "retrieval": "not exercised", "independent_accuracy_annotations": False}
    try:
        response = OllamaClient().complete(SYSTEM, context.text)
        summary.update(status="RESPONSE_RECEIVED", model=response.model_dump())
    except Exception as exc:
        summary.update(status="FAILED", error=type(exc).__name__, reason=str(exc)[:200])
    out = Path("data/live")
    out.mkdir(parents=True, exist_ok=True)
    (out / (args.name + ".json")).write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
