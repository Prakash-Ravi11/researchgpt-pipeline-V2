import base64
import copy
import json

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from pipeline.extraction.prompt import FIELDS
from pipeline.extraction.selection import relationship_context,SYSTEM
from pipeline.inference.packages import (minimal_packet,create_input,validate_input,create_result,import_result,
    result_archive,unpack_result,TrustedInputStore,PackageError,digest)
from tests.test_semantic_binding import source_fixture,synthetic
from shared.schemas import EvidenceBundle
from pipeline.parsing.documents import process


def package(tmp_path,*,custom=None):
    if custom:
        p,bs,cs=custom
    else:
        f,p,b,cs=source_fixture();bs=[b]
    ctx=relationship_context(cs,bs,input_budget=7000)
    packet=minimal_packet(p,cs,bs,ctx,code_commit='a'*40,scope='controlled_round_trip_fixture')
    messages=[{'role':'system','content':SYSTEM},{'role':'user','content':ctx.text}]
    runtime={'requested_model':{'model':'Qwen/Qwen3-8B','revision':'b'*40,'minimum_free_bytes':9_000_000_000},
        'generation':{'context_window':8192,'max_new_tokens':2048,'do_sample':False,'seed':42,'enable_thinking':False},
        'quantization':{'method':'bitsandbytes_nf4','compute_dtype':'float16','double_quant':True},
        'baseline_configuration':{'model':'qwen2.5:7b','quantization':'Q4_K_M'}}
    path=tmp_path/'input'
    manifest=create_input(path,packet,messages,runtime)
    return path,manifest,packet,runtime,bs


def result(tmp_path,input_path,runtime,eid,*,mutation=None):
    data={f:[] for f in FIELDS};data['results']=[{'evidence_id':eid}]
    execution={'status':'COMPLETED','execution_kind':'controlled_round_trip_fixture',
        'requested_model':runtime['requested_model'],'generation':runtime['generation'],'quantization':runtime['quantization'],
        'finish_reason':'eos','prompt_tokens':111,'generated_tokens':22,'runtime_seconds':1.0,
        'claimed_verdict':'VERIFIED'}
    raw_data=copy.deepcopy(data)
    if mutation=='unknown_id':data['results'][0]['evidence_id']='nonexistent';raw_data=copy.deepcopy(data)
    if mutation=='fabricated_value':data['results'][0]['scientific_tuple']={'value':'99.9'};raw_data=copy.deepcopy(data)
    if mutation=='model':execution['requested_model']={**runtime['requested_model'],'revision':'c'*40}
    if mutation=='thinking':execution['generation']={**runtime['generation'],'enable_thinking':True}
    if mutation=='failed':execution['status']='FAILED'
    if mutation=='normalized':data['results']=[]
    path=tmp_path/'remote'
    create_result(path,input_path,json.dumps(raw_data),data,execution)
    return path


def test_source_backed_export_import_roundtrip_retains_raw_and_full_tuple(tmp_path):
    inp,m,p,r,bs=package(tmp_path)
    remote=result(tmp_path,inp,r,bs[0].bundle_id)
    out=import_result(inp,remote,output_root=tmp_path/'imported')
    value=out.fields['results'][0]
    assert value.final=='RETURNED' and value.scientific_tuple['value']=='41.8'
    assert value.scientific_tuple['benchmark']=='newstest2014'
    assert value.scientific_tuple['condition']=='English-to-French'
    assert value.review_status=='needs_human_review' and out.trace['independent_human_accuracy'] is None
    assert (tmp_path/'imported/raw_response.txt').read_bytes()==(remote/'raw_response.txt').read_bytes()
    assert len(p['chunks'])==5 and len(p['bundles'])==1
    assert all('table_context' not in c for c in p['chunks'])
    assert all(len(c.get('validated_bundle_spans',{}))<=1 for c in p['chunks'])
    assert out.fields['objective'][0].verification_state=='UNAVAILABLE'


@pytest.mark.parametrize('mutation,code',[
    ('unknown_id','remote_output_schema_invalid'),('fabricated_value','remote_output_schema_invalid'),
    ('model','remote_model_mismatch'),('thinking','remote_configuration_mismatch'),
    ('failed','remote_inference_not_completed'),('normalized','normalized_output_differs_from_raw'),
    ('raw_tamper','package_file_integrity_mismatch'),('document','remote_document_mismatch'),
    ('manifest','remote_input_identity_mismatch')])
def test_remote_output_tampering_and_unapproved_proposals_fail(tmp_path,mutation,code):
    inp,m,p,r,bs=package(tmp_path);remote=result(tmp_path,inp,r,bs[0].bundle_id,mutation=mutation)
    if mutation=='raw_tamper':(remote/'raw_response.txt').write_text('changed',encoding='utf-8')
    if mutation in ('document','manifest'):
        data=json.loads((remote/'output-manifest.json').read_text())
        data['document_sha256' if mutation=='document' else 'input_manifest_sha256']='0'*64
        (remote/'output-manifest.json').write_text(json.dumps(data))
    out=import_result(inp,remote,output_root=tmp_path/'preserved')
    assert out.status=='EXTRACTION_FAILED' and out.errors[0]['code']==code
    assert out.fields['results'][0].verification_state=='FAILED'
    assert (tmp_path/'preserved/raw_response.txt').exists()


def test_trusted_input_manifest_source_hash_and_zip_members_are_checked(tmp_path):
    inp,m,p,r,bs=package(tmp_path)
    with pytest.raises(PackageError):validate_input(inp,'0'*64)
    original=(inp/'packet.json').read_bytes();(inp/'packet.json').write_bytes(original+b' ')
    with pytest.raises(PackageError):validate_input(inp)
    (inp/'packet.json').write_bytes(original)
    import io,zipfile
    data=io.BytesIO()
    with zipfile.ZipFile(data,'w') as z:z.writestr('../escape.txt','wrong')
    with pytest.raises(PackageError):unpack_result(data.getvalue(),tmp_path/'unsafe')
    assert not (tmp_path/'escape.txt').exists()


def test_valid_source_ids_can_still_be_withheld_or_ambiguous(tmp_path):
    from tests.test_accuracy_evidence import parsed
    a,d,cs,bs=parsed();peer=next(b for b in bs if any(s.text=='Prior [7]' for s in b.spans))
    inp,m,p,r,chosen=package(tmp_path,custom=(a.paper,[peer],cs))
    remote=result(tmp_path,inp,r,peer.bundle_id)
    out=import_result(inp,remote)
    assert out.fields['results'][0].verification_state=='WITHHELD'
    assert out.fields['results'][0].abstain_reason=='attributed_to_cited_work'
    assert out.trace['remote_execution_metadata']['claimed_verdict']=='VERIFIED' # deliberately ignored


def test_ambiguous_semantics_survives_remote_roundtrip(tmp_path):
    a=synthetic('Table 7: English-to-French and English-to-German Corpus42 tests and Other99 tests.')
    d,cs=process(a,'semantic_v1');bs=[EvidenceBundle(**b) for b in d['evidence_bundles']]
    inp,m,p,r,_=package(tmp_path,custom=(a.paper,bs,cs))
    out=import_result(inp,result(tmp_path,inp,r,bs[0].bundle_id))
    assert out.fields['results'][0].verification_state=='AMBIGUOUS'


@pytest.mark.integration
def test_backend_import_uses_registered_input_and_exposes_semantic_tuple(tmp_path):
    inp,m,p,r,bs=package(tmp_path)
    trusted=tmp_path/'trusted';pid=TrustedInputStore(trusted).register(inp)
    remote=result(tmp_path,inp,r,bs[0].bundle_id)
    archive=base64.b64encode(result_archive(remote)).decode()
    with TestClient(create_app(inference_input_root=trusted,inference_result_root=tmp_path/'results')) as client:
        response=client.post('/api/inference/import',json={'project_id':'demo','package_id':pid,'result_archive_base64':archive})
        assert response.status_code==200
        out=response.json();value=out['fields']['results'][0]
        assert value['status']=='VERIFIED' and value['scientific_tuple']['condition']=='English-to-French'
        assert out['evidence_bundles'][0]['semantic']['benchmark']=='newstest2014'
        assert len(value['source_refs'])==9 and out['trace']['import_id']
        assert client.post('/api/inference/import',json={'project_id':'demo','package_id':'rgpt_'+'0'*24,'result_archive_base64':archive}).status_code==404
        assert client.post('/api/inference/import',json={'project_id':'demo','package_id':pid,'result_archive_base64':'invalid'}).status_code==422
