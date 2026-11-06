import pytest

from pipeline.parsing.documents import process
from pipeline.retrieval.index import ChromaIndex
from pipeline.service import EvidencePipeline
from pipeline.evidence.verification import verify_candidate
from pipeline.acquisition.source import from_bytes
from shared.interfaces import AcquiredDocument
from shared.schemas import Paper
from tests.helpers import fixture_document, TinyEncoder, QuotedFixtureLLM

pytestmark = pytest.mark.integration


def test_jats_and_chroma_round_trip_and_connected_verification(tmp_path):
    doc = fixture_document()
    _, chunks = process(doc)
    index = ChromaIndex("fixture-project", tmp_path / "index", encoder=TinyEncoder())
    result = EvidencePipeline(None, index, QuotedFixtureLLM()).run(doc.paper, doc)
    assert result.status == "PARTIAL"
    evidence = result.fields["results"][0]
    assert evidence.status == "VERIFIED" and evidence.scientific_tuple["value"] == "91.4"
    assert all(c.paper_id == "SYN" for c in index.all_chunks("SYN"))
    assert index.all_chunks("SYN") == chunks
    assert len(evidence.source_refs) == 2  # prose quote and binding table
    assert process(doc)[1] == chunks


def test_unsupported_value_and_wrong_dataset_rejected():
    doc = fixture_document()
    _, chunks = process(doc)
    c = next(c for c in chunks if "Our method achieves" in c.text)
    candidate = {"value": c.text, "evidence_span": c.text, "chunk_id": c.chunk_id,
        "scientific_tuple": {"subject": "Ours", "dataset": "OtherSet", "metric": "Dice (%)", "value": "91.4"}}
    assert verify_candidate("results", candidate, doc.paper, chunks, chunks).final == "ABSTAINED"
    candidate["value"] = c.text.replace("91.4", "99.9")
    assert verify_candidate("results", candidate, doc.paper, chunks, chunks).abstain_reason == "value_not_in_source_quote"
    candidate.update(value=c.text, chunk_id="bm25_0")
    assert verify_candidate("results", candidate, doc.paper, chunks, chunks).abstain_reason == "source_chunk_not_delivered"


def test_missing_full_text_is_distinct_from_failed_extraction(tmp_path):
    paper = Paper(paper_id="abstract", abstract="We investigate segmentation methods.",
                  acquisition_status="ABSTRACT_ONLY", representation_type="abstract")
    class UnavailableModel:
        def complete(self, *args):
            raise ConnectionError("model unavailable")
    result = EvidencePipeline(None, ChromaIndex("abstract", tmp_path / "idx", TinyEncoder()), UnavailableModel()).run(paper, AcquiredDocument(paper, None))
    assert result.acquisition_status == "ABSTRACT_ONLY"
    assert result.status == "EXTRACTION_FAILED"
    no_text = Paper(paper_id="no-access", acquisition_status="NO_ACCESSIBLE_FULL_TEXT")
    result = EvidencePipeline(None, None, None).run(no_text, AcquiredDocument(no_text, None))
    assert result.status == "ABSTAINED" and not result.errors


def test_identity_and_content_validation_reject_wrong_or_thin_document():
    doc = fixture_document()
    result = from_bytes(Paper(paper_id="real-id", title="A completely unrelated paper"), doc.data, "jats_xml")
    assert result.paper.acquisition_status == "FAILED" and result.data is None
    assert not result.paper.identity_validation["passed"]


def test_project_collection_and_paper_replacement_are_isolated(tmp_path):
    doc = fixture_document()
    _, chunks = process(doc)
    one, two = (ChromaIndex(p, tmp_path / "store", TinyEncoder()) for p in ("one", "two"))
    one.replace_paper("SYN", chunks)
    two.replace_paper("SYN", chunks[:1])
    one.replace_paper("SYN", chunks[-1:])
    assert one.all_chunks("SYN") == chunks[-1:]
    assert two.all_chunks("SYN") == chunks[:1]
