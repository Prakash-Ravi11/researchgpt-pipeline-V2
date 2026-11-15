import pytest

from src.evidence.chunker import chunk_document
from src.evidence.represent import blocks_from_jats
from src.evidence.acquire import content_validate
from pipeline.extraction.context import current_context
from tests.helpers import fixture_document
from pipeline.parsing.documents import process

pytestmark = pytest.mark.unit


def test_chunk_offsets_point_into_exact_source_whitespace():
    text = "Alpha\tbeta\n gamma   delta"
    block = {"paper_id": "S", "block_id": "S:0", "source": "test", "representation": "pdf",
        "section": "results", "page_or_node": "p1", "block_type": "paragraph", "char_start": 100,
        "char_end": 100 + len(text), "text": text}
    for c in chunk_document({"blocks": [block]}):
        assert text[c["char_start"] - 100:c["char_end"] - 100] == c["text"]


def test_jats_colspan_header_preserves_metric_column():
    xml = b'''<article><body><sec><title>Results</title><table-wrap><caption>Results on ExampleSet test set</caption>
    <table><thead><tr><th colspan="2">Model group</th><th>Dice (%)</th></tr></thead>
    <tbody><tr><td>Ours</td><td>Large</td><td>91.4</td></tr><tr><td>Baseline</td><td>Small</td><td>85.1</td></tr></tbody>
    </table></table-wrap></sec></body></article>'''
    table = next(b for b in blocks_from_jats(xml, "S", "test") if b["block_type"] == "table")
    cells = [c for c in table["table_cells"] if c["value"] == "91.4"]
    assert len(cells) == 1 and cells[0]["column_header"] == "Dice (%)"


def test_jats_content_length_does_not_count_nested_text_repeatedly():
    para = " ".join(["word"] * 600)
    xml = f'<article><front><article-title>Thin text</article-title></front><body><sec><title>Methods</title><p>{para}</p></sec><sec><title>Results</title><p>Thin.</p></sec></body></article>'.encode()
    validation = content_validate("jats_xml", xml)
    assert not validation["passed"]
    assert validation["metrics"]["body_words"] < 700


def test_jats_colspan_row_label_does_not_shift_values_into_wrong_metric():
    xml = b'''<article><body><table-wrap><caption>Results on ExampleSet</caption><table>
    <tr><th>Model</th><th>Variant</th><th>Dice (%)</th><th>HD95 (mm)</th></tr>
    <tr><td colspan="2">Ours</td><td>91.4</td><td>4.3</td></tr>
    </table></table-wrap></body></article>'''
    table = blocks_from_jats(xml, "S", "test")[0]
    cell = next(c for c in table["table_cells"] if c["value"] == "91.4")
    assert cell["column_header"] == "Dice (%)"


def test_context_trace_exposes_retrieved_but_undelivered_result():
    _, chunks = process(fixture_document())
    context = current_context(chunks, max_words=5)
    target = next(c for c in chunks if "Our method achieves" in c.text)
    assert target.chunk_id in context.trace["retrieved_chunk_ids"]
    assert target.chunk_id in context.trace["dropped_chunk_ids"]
    assert "91.4" not in context.text


def test_ambiguous_merged_measurement_is_preserved_but_not_bound():
    xml = b'''<article><body><table-wrap><caption>Results on ExampleSet</caption><table>
    <tr><th>Model</th><th>Dice</th><th>Accuracy</th></tr>
    <tr><td>Ours</td><td colspan="2">91.4</td></tr></table></table-wrap></body></article>'''
    block = blocks_from_jats(xml, "S", "test")[0]
    assert "91.4" in block["text"] and not block["table_cells"]


def test_overlapping_long_chunks_keep_exact_source_offsets():
    text = "\n\t".join(f"word{i}" for i in range(500))
    block = {"paper_id": "S", "block_id": "S:0", "source": "test", "representation": "pdf",
        "section": "results", "page_or_node": "p1", "block_type": "paragraph", "char_start": 37,
        "char_end": 37 + len(text), "text": text}
    chunks = chunk_document({"blocks": [block]})
    assert len(chunks) == 3
    for c in chunks:
        assert text[c["char_start"] - 37:c["char_end"] - 37] == c["text"]


def test_jats_nested_section_hierarchy_survives_chunking():
    xml = b'<article><body><sec><title>Methods</title><sec><title>Training protocol</title><p>We train the model on ExampleSet.</p></sec></sec></body></article>'
    blocks = blocks_from_jats(xml, "S", "test")
    c = chunk_document({"blocks": blocks})[0]
    assert c["section"] == "method"
    assert c["section_path"] == ["Methods", "Training protocol"]
    assert c["subsection"] == "Training protocol"
