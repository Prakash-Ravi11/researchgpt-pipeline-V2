import pytest

from pipeline.evidence.quotes import resolve_quote
from pipeline.evidence.verification import verify_candidate
from shared.schemas import Chunk, Paper


@pytest.mark.parametrize("source,quote", [
    ("two   words", "two words"), ("two words", "two   words"),
    ("two\nwords", "two words"), ("two\twords", "two words"),
    ("trans\u00adformer", "transformer"),
    ("A trans-\nformer, another transformer.", "A transformer"),
    ("English-\nto-German", "English-to-German"),
])
def test_formatting_maps_original_offsets(source, quote):
    match, error = resolve_quote(source, quote)
    assert error is None
    assert source[match.start:match.end] == match.text
    assert match.start == 0


@pytest.mark.parametrize("quote", ["28.5 BLEU", "28.4 ms", "28.4 accuracy"])
def test_scientific_mutations_fail(quote):
    assert resolve_quote("28.4 BLEU", quote) == (None, "missing")


def test_ambiguous_and_unsafe_hyphenation():
    assert resolve_quote("same text; same\ntext", "same text")[1] == "ambiguous"
    assert resolve_quote("re-\ncover", "recover")[1] == "missing"


def test_measurement_at_sentence_end_is_not_a_different_decimal():
    from pipeline.evidence.verification import _contains_number
    assert _contains_number("BLEU score of 28.4.", "28.4")
    assert not _contains_number("BLEU score of 28.40.", "28.4")
    assert not _contains_number("BLEU score of 128.4.", "28.4")


def test_verifier_preserves_id_and_original_offset():
    paper = Paper(paper_id="arxiv:1706.03762", title="Example")
    chunk = Chunk(paper_id=paper.paper_id, chunk_id="block#0", block_id="block",
                  source="fixture", representation="pdf", section="method", page_or_node="2",
                  char_start=100, char_end=124, text="Before. two\nwords. After.", chunk_index=0, block_type="paragraph")
    candidate = dict(value="two words", evidence_span="two words", chunk_id=chunk.chunk_id)
    out = verify_candidate("method", candidate, paper, [chunk], [chunk])
    assert out.final == "RETURNED"
    assert out.evidence_span == "two\nwords"
    assert out.source_refs[0].char_start == 108
    assert out.source_refs[0].char_end == 117
    assert verify_candidate("method", {**candidate, "chunk_id": "other"}, paper, [chunk], [chunk]).final == "ABSTAINED"
    repeated = chunk.model_copy(update={"text": "two words; two words"})
    assert verify_candidate("method", candidate, paper, [repeated], [repeated]).status == "AMBIGUOUS"
