import pytest
from pydantic import ValidationError

from shared.schemas import Chunk, ExtractedPaper, FieldValue, Job, Paper

pytestmark = pytest.mark.contract


def chunk():
    return Chunk(paper_id="abc", chunk_id="abc:0#0", block_id="abc:0", source="europepmc",
                 representation="jats_xml", section="results", page_or_node="body/sec[0]/p[1]",
                 char_start=0, char_end=20, text="Our F1 score is 91.4.", block_type="paragraph",
                 table_cells=[{"value": "91.4", "row_label": "Ours", "column_header": "F1"}])


def test_nested_round_trip_keeps_identity_and_provenance():
    c = chunk()
    fv = FieldValue(field="results", value=c.text, final="RETURNED", status="VERIFIED",
                    evidence_status="EXPLICIT", provenance_valid=True, source_refs=[c.reference()])
    result = ExtractedPaper(paper_id="abc", acquisition_status="FULL_TEXT", status="COMPLETE",
                            fields={"results": [fv]})
    j = Job(job_id="one", project_id="p", status="COMPLETE", result=result)
    assert Job.model_validate_json(j.model_dump_json()) == j
    assert Chunk.model_validate_json(c.model_dump_json()) == c
    assert j.result.fields["results"][0].source_refs[0].chunk_id == "abc:0#0"


def test_identity_alias_and_fallbacks():
    p = Paper(paperId="abc", title="Real paper", externalIds={"DOI": "10.1/X"})
    assert p.paper_id == p.legacy_record()["paperId"] == "abc"
    assert Paper(externalIds={"DOI": "https://doi.org/10.1/X"}).paper_id == "doi:10.1/x"
    assert Paper(externalIds={"ArXiv": "1234.56789v2"}).paper_id == "arxiv:1234.56789"
    for rec in [{"title": "not an identifier"}, {"paper_id": "a", "paperId": "b"}]:
        with pytest.raises(ValidationError):
            Paper(**rec)


def test_unvalidated_full_text_and_unsupported_returns_rejected():
    with pytest.raises(ValidationError):
        Paper(paper_id="abc", has_full_text=True, acquisition_status="FULL_TEXT", representation_type="pdf")
    with pytest.raises(ValidationError):
        FieldValue(field="results", value="Accuracy 99%", final="RETURNED")
    with pytest.raises(ValidationError):
        Chunk(**{**chunk().model_dump(), "char_end": -1})


def test_cross_paper_reference_rejected():
    fv = FieldValue(field="results", source_refs=[chunk().reference()])
    with pytest.raises(ValidationError):
        ExtractedPaper(paper_id="different", acquisition_status="ABSTRACT_ONLY", status="PARTIAL",
                       fields={"results": [fv]})
