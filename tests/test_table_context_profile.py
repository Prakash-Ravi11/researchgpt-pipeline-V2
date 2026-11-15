import pytest

from pipeline.parsing.documents import process
from pipeline.parsing.table_context import enrich_pdf
from pipeline.retrieval.retrievers import TableAwareRetriever
from pipeline.extraction.context import table_aware_context
from shared.schemas import Chunk
from src.evidence.chunker import chunk_document
from src.evidence.represent import build_document
from tests.test_pdf_table_cells import _pdf, _results_page


def _unstructured(page):
    page.insert_text((72, 80), "Table 7: Measurements on test set.", fontsize=10)
    for y in (95, 115, 145):
        page.draw_line((72, y), (500, y))
    page.insert_text((80, 108), "Model       Score       Cost", fontsize=10)
    page.insert_text((80, 133), "Example       7.3       200", fontsize=10)
    page.insert_text((72, 190), "Unrelated prose 8.4 stays outside the table.", fontsize=10)


@pytest.mark.parametrize("draw,representation", [(_results_page, "structured_table"),
                                                (_unstructured, "unstructured_table_text")])
def test_linked_table_keeps_native_text_offsets_and_grid_status(draw, representation):
    data = _pdf(draw)
    doc = build_document({"paper_id": "SYN", "source": "test", "representation_type": "pdf"}, data)
    before = [(b["block_id"], b["text"], b["char_start"], b["char_end"]) for b in doc["blocks"]]
    enrich_pdf(doc, data)
    assert before == [(b["block_id"], b["text"], b["char_start"], b["char_end"]) for b in doc["blocks"]]
    table = doc["linked_tables"][0]
    assert table["representation"] == representation
    assert table["cell_binding_verified"] == (representation == "structured_table")
    assert all("Unrelated" not in p["text"] for p in table["parts"])
    chunks = [Chunk(**c, chunk_index=i) for i, c in enumerate(chunk_document(doc))]
    linked = [c for c in chunks if getattr(c, "table_id", None)]
    assert linked and all(c.source_bbox and c.source_words for c in linked)
    assert linked[0].reference().table_id == table["table_id"]
    if representation == "unstructured_table_text":
        assert all(not c.table_cells for c in linked)
        assert any("Score" in p["text"] for p in table["parts"])
        assert any("Example" in p["text"] for p in table["parts"])
    class CaptionOnlyIndex:
        def search(self, query, pid, n):
            return [linked[0]]
    retriever = TableAwareRetriever(CaptionOnlyIndex())
    retrieved = retriever.retrieve("SYN", chunks)
    assert {c.chunk_id for c in retrieved} == {c.chunk_id for c in linked}
    context = table_aware_context(retrieved, budget=20000)
    assert context.chunks == retrieved
    assert not table_aware_context(retrieved, budget=20).chunks  # atomic group


def test_profile_rejects_unknown_and_baseline_stays_unchanged():
    from tests.helpers import fixture_document
    doc = fixture_document()
    assert process(doc) == process(doc, "baseline")
    with pytest.raises(ValueError):
        process(doc, "other")
