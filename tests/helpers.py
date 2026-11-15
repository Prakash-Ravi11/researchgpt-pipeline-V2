from pathlib import Path

from shared.interfaces import AcquiredDocument
from shared.schemas import Paper, LLMResponse


def fixture_document():
    # Synthetic fixture bypasses acquisition on purpose; not a live-paper validation.
    paper = Paper(paper_id="SYN", title="Synthetic segmentation evidence fixture", acquisition_status="FULL_TEXT",
        has_full_text=True, representation_type="jats_xml", identity_validation={"passed": True, "test_fixture": True},
        content_validation={"passed": True, "test_fixture": True}, pdf_source="synthetic_fixture")
    return AcquiredDocument(paper, (Path(__file__).parent / "fixtures/scientific.xml").read_bytes())


class TinyEncoder:
    """Deterministic test double; never scientific dense retrieval evidence."""
    signature = "TEST-ONLY-tiny-encoder"

    def encode(self, texts):
        return [[float("result" in t.lower()), float("method" in t.lower()), 1.0] for t in texts]


class QuotedFixtureLLM:
    """Controlled candidate injection to test connected verification, not extraction accuracy."""
    def complete(self, system, user):
        import re
        chunks = re.findall(r"\[([^\]]+)\]\n([^\[]+)", user)
        claim = "Our method achieves a Dice score of 91.4% on the ExampleSet test set."
        cid = next(cid for cid, text in chunks if claim in text)
        return LLMResponse(content={"results": [{"value": claim, "evidence_span": claim, "chunk_id": cid,
            "scientific_tuple": {"subject": "Ours", "dataset": "ExampleSet", "metric": "Dice (%)", "value": "91.4", "setting": "test set"}}]},
            provider="test-double", model="injected-quotation", latency_ms=0)
