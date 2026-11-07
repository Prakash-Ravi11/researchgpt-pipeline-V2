import hashlib
import json

import pymupdf
import pytest
from fastapi.testclient import TestClient

from shared.interfaces import AcquiredDocument
from shared.schemas import Paper, EvidenceBundle, LLMResponse
from pipeline.parsing.documents import process
from pipeline.evidence.bundles import verify_bundle
from pipeline.extraction.selection import relationship_context, verify_selection, schema
from pipeline.retrieval.index import ChromaIndex
from pipeline.service import EvidencePipeline
from api.main import create_app
from tests.helpers import TinyEncoder


def document():
    pdf=pymupdf.open();p=pdf.new_page()
    p.insert_text((72,80),"Table 1: Performance on held-out test sets.",fontsize=10)
    for y in (95,135,180):p.draw_line((72,y),(520,y))
    for x,y,t in [(80,120,"Model"),(300,108,"BLEU"),(425,108,"Cost"),
                  (275,125,"SetA"),(335,125,"SetB"),(395,125,"SetA"),(455,125,"SetB"),
                  (80,153,"Ours"),(280,153,"91.4"),(340,153,"92.1"),(400,153,"2.3"),(425,153,"·"),(450,153,"1019"),
                  (80,170,"Prior [7]"),(280,170,"85.2"),(340,170,"86.0")]:p.insert_text((x,y),t,fontsize=10)
    p.insert_text((72,220),"4 Results",fontsize=12)
    p.insert_text((72,245),"Our method achieves BLEU 91.4 on SetA and 92.1 on SetB.",fontsize=10)
    data=pdf.tobytes();pdf.close()
    paper=Paper(paper_id="SYN",title="Synthetic table evidence",acquisition_status="FULL_TEXT",
        representation_type="pdf",has_full_text=True,identity_validation={"passed":True,"test_fixture":True},
        content_validation={"passed":True,"test_fixture":True},document_sha256=hashlib.sha256(data).hexdigest())
    return AcquiredDocument(paper,data)


def parsed():
    a=document();d,c=process(a,"accuracy_v1")
    return a,d,c,[EvidenceBundle(**b) for b in d["evidence_bundles"]]


def test_native_hierarchy_preserves_multispans_and_does_not_split_cost():
    a,d,c,bs=parsed()
    assert len(bs)==4
    assert {next(s.text for s in b.spans if s.role=="metric") for b in bs}=={"BLEU"}
    baseline,old=process(a)
    assert [(x.chunk_id,x.text,x.char_start,x.char_end) for x in old]==[(x.chunk_id,x.text,x.char_start,x.char_end) for x in c]
    for b in bs:
        for s in b.spans:
            src=next(x for x in c if x.chunk_id==s.reference.chunk_id)
            assert src.text[s.reference.char_start-src.char_start:s.reference.char_end-src.char_start]==s.text
    own=next(b for b in bs if any(s.text=="Ours" for s in b.spans))
    out=verify_bundle("results",{"evidence_id":own.bundle_id},a.paper,c,c,bs)
    assert out.final=="RETURNED" and len(out.source_refs)==5
    assert out.review_status=="needs_human_review"  # synthetic source support, not independent gold
    prior=next(b for b in bs if any(s.text=="Prior [7]" for s in b.spans))
    assert verify_bundle("results",{"evidence_id":prior.bundle_id},a.paper,c,c,bs).abstain_reason=="attributed_to_cited_work"


@pytest.mark.parametrize("change",["dataset","subject","metric","value","version","region","undelivered","attestation","unit"])
def test_invalid_bundle_links_are_withheld(change):
    a,d,c,bs=parsed();b=next(x for x in bs if any(s.text=="Ours" for s in x.spans))
    candidate={"evidence_id":b.bundle_id}
    if change in ("dataset","subject","metric","value","unit"):
        tup={s.role:s.text for s in b.spans if s.role in ("subject","dataset","metric","value")}
        tup[change]="mutated"
        candidate["scientific_tuple"]=tup
    elif change=="version":b.document_sha256="0"*64
    elif change=="region":b.table_id="another table"
    elif change=="undelivered":c=c[:1]
    elif change=="attestation":
        next(s for s in b.spans if s.role=="dataset").text="SetB"
    out=verify_bundle("results",candidate,a.paper,c,c,bs)
    assert out.final=="ABSTAINED" and out.verification_state in ("WITHHELD","UNAVAILABLE")


def test_balanced_catalog_preserves_prose_and_structure_with_budget():
    a,d,c,bs=parsed();ctx=relationship_context(c,bs,input_budget=4000)
    assert ctx.trace["bundle_units"]>=2 and ctx.trace["prose_units"]>=1
    assert ctx.trace["budget_units_used"]<=4000
    assert "Our method achieves BLEU" in ctx.text
    own=next(b for b in bs if any(s.text=="Ours" for s in b.spans))
    out=verify_selection("results",{"evidence_id":own.bundle_id},a.paper,ctx,c,bs)
    assert out.final=="RETURNED"
    assert verify_selection("results",{"evidence_id":"invented"},a.paper,ctx,c,bs).final=="ABSTAINED"
    assert schema(ctx.text)["properties"]["results"]["items"]["properties"]["evidence_id"]["enum"]


def test_missing_pdf_text_requests_ocr_without_inventing_source():
    a=document();pdf=pymupdf.open();pdf.new_page();data=pdf.tobytes();pdf.close()
    a=AcquiredDocument(a.paper.model_copy(update={"document_sha256":hashlib.sha256(data).hexdigest()}),data)
    doc,chunks=process(a,'accuracy_v1')
    assert not chunks and not doc['evidence_bundles']
    assert doc['accuracy_route']['status']=='UNAVAILABLE'
    assert doc['accuracy_route']['escalations'][0]['candidate_backend']=='docling_with_ocr'


def test_public_verification_states_remain_distinct():
    from shared.schemas import FieldValue
    assert FieldValue(field='x').verification_state=='UNAVAILABLE'
    assert FieldValue(field='x',status='FAILED').verification_state=='FAILED'
    assert FieldValue(field='x',status='AMBIGUOUS').verification_state=='AMBIGUOUS'
    assert FieldValue(field='x',status='ABSTAINED').verification_state=='WITHHELD'


@pytest.mark.integration
def test_accuracy_backend_exposes_bundle_and_verified_source_refs(tmp_path):
    a=document()
    class FixtureSource:
        def acquire(self,paper):return a
    class SelectionFixtureLLM:
        def complete(self,system,user):
            import re
            match=re.search(r"\[(bundle:[^\]]+)\]\n([^\n]+)",user)
            assert match
            return LLMResponse(content={"results":[{"evidence_id":match[1]}]},provider="fixture",model="selection-double",latency_ms=0)
    def factory(req):
        return EvidencePipeline(FixtureSource(),ChromaIndex(req.project_id,tmp_path/'db',TinyEncoder()),SelectionFixtureLLM(),
            retrieval="table_aware_v1",context_mode="relationship_v1",representation_profile="accuracy_v1",extraction_mode="selection_v1")
    with TestClient(create_app(factory)) as client:
        r=client.post('/api/papers/process',json={"project_id":"accuracy","paper":{"paper_id":"SYN"}})
        assert r.status_code==200
        out=r.json()
        assert out['evidence_bundles']
        assert out['fields']['results'][0]['final']=='RETURNED'
        assert out['fields']['results'][0]['verification_state']=='VERIFIED'
        assert len(out['fields']['results'][0]['source_refs'])==5
        assert client.post('/api/papers/process',json={"project_id":"bad","paper":{"paper_id":"SYN"},
                           "extraction_mode":"selection_v1"}).status_code==422


@pytest.mark.integration
def test_completed_structure_survives_model_timeout(tmp_path):
    import requests
    a=document()
    class FixtureSource:
        def acquire(self,paper):return a
    class TimeoutLLM:
        def complete(self,system,user):raise requests.exceptions.ReadTimeout('controlled fixture timeout')
    pipeline=EvidencePipeline(FixtureSource(),ChromaIndex('timeout',tmp_path/'db',TinyEncoder()),TimeoutLLM(),
        retrieval='table_aware_v1',context_mode='relationship_v1',representation_profile='accuracy_v1',extraction_mode='selection_v1')
    out=pipeline.run(a.paper)
    assert out.status=='EXTRACTION_FAILED'
    assert len(out.evidence_bundles)==4
    assert all(v.verification_state=='FAILED' for vs in out.fields.values() for v in vs)
    assert out.errors==[{'stage':'extraction','code':'ReadTimeout'}]
