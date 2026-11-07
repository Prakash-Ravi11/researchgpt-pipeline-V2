import hashlib
import json
from pathlib import Path

import pymupdf
import pytest

from shared.schemas import Paper,Chunk,EvidenceBundle
from shared.interfaces import AcquiredDocument
from pipeline.evidence.bundles import attest,verify_bundle
from pipeline.parsing.documents import process
from pipeline.extraction.selection import relationship_context,verify_selection


def source_fixture():
    f=json.loads(Path('tests/fixtures/semantic_attention_v7.json').read_text(encoding='utf-8'))
    p=Paper(**f['paper']);b=EvidenceBundle(**f['bundle']);cs=[Chunk(**c) for c in f['chunks']]
    attest([b],cs)
    return f,p,b,cs


def test_real_source_fixture_complete_tuple_is_machine_verified_not_human_gold():
    f,p,b,cs=source_fixture()
    out=verify_bundle('results',{'evidence_id':b.bundle_id,'scientific_tuple':f['expected_tuple']},p,cs,cs,[b])
    assert out.final=='RETURNED' and out.scientific_tuple==f['expected_tuple']
    assert out.review_status==f['ground_truth_status']=='needs_human_review'
    assert not any(f[k] for k in ('reviewer','reviewed_at','verdict'))
    assert len(b.spans)==9 and len(b.semantic.relations)==7
    for span in b.spans:
        c=next(c for c in cs if c.chunk_id==span.reference.chunk_id)
        assert c.text[span.reference.char_start-c.char_start:span.reference.char_end-c.char_start]==span.text
        assert span.bbox and span.reference.page_or_node=='p8'
    assert b.semantic.benchmark=='newstest2014' and b.semantic.condition=='English-to-French'
    assert b.semantic.condition_label=='EN-FR'


@pytest.mark.parametrize('field,replacement',[
    ('value','41.0'),('subject','Transformer (base model)'),('benchmark','WrongBenchmark'),
    ('dataset','EN-FR'),('condition','English-to-German'),('metric','Accuracy'),('unit','%')])
def test_complete_tuple_mutations_fail(field,replacement):
    f,p,b,cs=source_fixture()
    proposed={**f['expected_tuple'],field:replacement}
    out=verify_bundle('results',{'evidence_id':b.bundle_id,'scientific_tuple':proposed},p,cs,cs,[b])
    assert out.final=='ABSTAINED' and out.abstain_reason=='scientific_tuple_disagrees_with_bundle'


@pytest.mark.parametrize('mutation',['header_ref','row_ref','version','table_relation','condition_relation','unavailable_span'])
def test_reference_and_relationship_mutations_fail(mutation):
    f,p,b,cs=source_fixture()
    if mutation=='header_ref':
        s=next(s for s in b.spans if s.role=='dataset')
        s.reference=s.reference.model_copy(update={'char_start':s.reference.char_start+6,'char_end':s.reference.char_end+6})
    elif mutation=='row_ref':next(s for s in b.spans if s.role=='subject').reference.chunk_id='arxiv:1706.03762:118#0'
    elif mutation=='version':b.document_sha256='0'*64
    elif mutation=='table_relation':b.semantic.relations[0].table_id='another table'
    elif mutation=='condition_relation':b.semantic.condition='English-to-German'
    elif mutation=='unavailable_span':cs=cs[:-1]
    out=verify_bundle('results',{'evidence_id':b.bundle_id},p,cs,cs,[b])
    assert out.final=='ABSTAINED'


def synthetic(caption,metric='BLEU'):
    doc=pymupdf.open();p=doc.new_page()
    p.insert_text((72,80),caption,fontsize=9)
    for y in (95,135,165):p.draw_line((72,y),(520,y))
    for x,y,t in [(80,120,'Model'),(300,108,metric),(425,108,'Cost'),(275,125,'EN-FR'),
                  (335,125,'EN-DE'),(395,125,'EN-FR'),(455,125,'EN-DE'),
                  (80,153,'Ours'),(280,153,'37.2'),(340,153,'36.1')]:p.insert_text((x,y),t,fontsize=9)
    data=doc.tobytes();doc.close()
    paper=Paper(paper_id='SEM-SYN',title='Synthetic semantic fixture',acquisition_status='FULL_TEXT',
        representation_type='pdf',has_full_text=True,identity_validation={'passed':True,'fixture':True},
        content_validation={'passed':True,'fixture':True},document_sha256=hashlib.sha256(data).hexdigest())
    return AcquiredDocument(paper,data)


def test_generic_caption_benchmark_hierarchical_header_and_language_binding():
    a=synthetic('Table 7: Performance on English-to-French and English-to-German Corpus42 tests.')
    d,cs=process(a,'semantic_v1');bs=[EvidenceBundle(**b) for b in d['evidence_bundles']]
    assert len(bs)==2 and all(b.semantic.benchmark=='Corpus42' for b in bs)
    assert {b.semantic.condition for b in bs}=={'English-to-French','English-to-German'}
    assert all(b.semantic.metric=='BLEU' for b in bs)
    assert all(verify_bundle('results',{'evidence_id':b.bundle_id},a.paper,cs,cs,bs).final=='RETURNED' for b in bs)


def test_multiple_benchmarks_abstain_without_nearby_number_guess():
    a=synthetic('Table 7: English-to-French and English-to-German Corpus42 tests and Other99 tests.')
    d,cs=process(a,'semantic_v1');bs=[EvidenceBundle(**b) for b in d['evidence_bundles']]
    assert bs and all(b.semantic.status=='AMBIGUOUS' for b in bs)
    assert all(verify_bundle('results',{'evidence_id':b.bundle_id},a.paper,cs,cs,bs).verification_state=='AMBIGUOUS' for b in bs)


def test_printed_metric_unit_remains_source_backed():
    a=synthetic('Table 7: Performance on English-to-French and English-to-German Corpus42 tests.','Accuracy (%)')
    d,cs=process(a,'semantic_v1');bs=[EvidenceBundle(**b) for b in d['evidence_bundles']]
    assert bs and all(b.semantic.unit=='%' for b in bs)
    for b in bs:
        unit=next(s for s in b.spans if s.role=='unit')
        assert unit.text=='%' and unit.reference.char_end-unit.reference.char_start==1
        out=verify_bundle('results',{'evidence_id':b.bundle_id},a.paper,cs,cs,bs)
        assert out.final=='RETURNED' and out.scientific_tuple['unit']=='%'


def test_validated_semantics_connects_source_id_selection_path():
    f,p,b,cs=source_fixture();ctx=relationship_context(cs,[b],input_budget=6000)
    out=verify_selection('results',{'evidence_id':b.bundle_id},p,ctx,cs,[b])
    assert out.final=='RETURNED' and out.scientific_tuple['benchmark']=='newstest2014'
    assert 'semantic_binding' in ctx.text and b.bundle_id in ctx.catalog
