"""Versioned, hash-checked offload packages. Hashes detect changes, not authorship.

Only the locally registered input is trusted. Remote verdicts never authorize a
fact; raw/normalized output consistency and the local source gate are mandatory.
"""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import zipfile

import jsonschema

from pipeline.evidence.bundles import attest
from pipeline.extraction.clients import parse_object
from pipeline.extraction.prompt import FIELDS
from pipeline.extraction.selection import schema
from pipeline.inference.structured import contract_messages,response_contract,validate_contract
from shared.schemas import Paper,Chunk,EvidenceSpan,EvidenceBundle,FieldValue,ExtractedPaper,SourceReference

INPUT_FILES={'packet.json','request.json','runtime.json'}
RESULT_FILES={'raw_response.txt','candidates.json','execution.json'}
INPUT_VERSION='rgpt-inference-input-v1'
OUTPUT_VERSION='rgpt-inference-result-v1'
MAX_RESULT_BYTES=8_000_000


class PackageError(ValueError):
    pass


def digest(data):return hashlib.sha256(data).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
def read_json(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def write_json(path,value):Path(path).write_bytes(json.dumps(value,indent=2,ensure_ascii=False).encode('utf-8')+b'\n')


def _files(root,names):
    result={}
    for name in names:
        path=root/name
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
            raise PackageError('missing_or_unsafe_package_file')
        data=path.read_bytes()
        result[name]={'sha256':digest(data),'bytes':len(data)}
    return result


def _check_files(root,manifest,names):
    if set(manifest.get('files',{}))!=names:raise PackageError('unexpected_manifest_files')
    if _files(root,names)!=manifest['files']:raise PackageError('package_file_integrity_mismatch')


def minimal_packet(paper,chunks,bundles,context,*,code_commit,scope='development'):
    refs=set(SourceReference.model_fields)|{'table_id','source_bbox','source_words'}
    needed_words={s.text for v in context.catalog.values() if isinstance(v,EvidenceBundle)
                  for s in v.spans if s.role in ('benchmark','condition','unit')}
    def reference(d):
        out={k:v for k,v in d.items() if k in refs}
        if 'source_words' in out:out['source_words']=[w for w in out['source_words'] if w['text'] in needed_words]
        return out
    def item(value):
        data=value.model_dump()
        if isinstance(value,EvidenceSpan):data['reference']=reference(data['reference'])
        else:
            for s in data['spans']:s['reference']=reference(s['reference'])
        return data
    catalog={k:{'kind':'span' if isinstance(v,EvidenceSpan) else 'bundle','item':item(v)} for k,v in context.catalog.items()}
    selected=[EvidenceBundle(**v['item']) for v in catalog.values() if v['kind']=='bundle']
    needed={s['reference']['chunk_id'] for v in catalog.values()
            for s in ([v['item']] if v['kind']=='span' else v['item']['spans'])}
    cs=[]
    for c in chunks:
        if c.chunk_id in needed:
            cs.append(Chunk(**{**reference(c.model_dump()),'text':c.text,'block_type':c.block_type,'chunk_index':c.chunk_index}))
    if needed!={c.chunk_id for c in cs}:raise PackageError('catalog_source_missing')
    attest(selected,cs)
    trace={**context.trace,'delivered_chunk_ids':[c.chunk_id for c in cs]}
    # Only selected sources and their necessary original-block context, not the corpus.
    return {'schema_version':INPUT_VERSION,'paper':paper.model_dump(mode='json'),
        'document_sha256':paper.document_sha256,'code_commit':code_commit,'chunks':[c.model_dump() for c in cs],
        'bundles':[b.model_dump() for b in selected],'catalog':catalog,'context_trace':trace,
        'scope':scope,'independent_gold':False}


def create_input(root,packet,messages,runtime):
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    output_schema=schema(messages[-1]['content'])
    request={'messages':contract_messages(messages,output_schema),'output_schema':output_schema,
             'generation_profile':runtime['generation'],'response_contract':response_contract(output_schema)}
    for name,data in [('packet.json',packet),('request.json',request),('runtime.json',runtime)]:write_json(root/name,data)
    identity=digest(canonical([packet,request,runtime]))
    manifest={'format':INPUT_VERSION,'package_id':'rgpt_'+identity[:24],
        'document_sha256':packet['document_sha256'],'code_commit':packet['code_commit'],'files':_files(root,INPUT_FILES)}
    write_json(root/'input-manifest.json',manifest)
    validate_input(root)
    return manifest


def validate_input(root,expected_manifest_sha256=None):
    root=Path(root)
    if expected_manifest_sha256 and digest((root/'input-manifest.json').read_bytes())!=expected_manifest_sha256:
        raise PackageError('input_manifest_integrity_mismatch')
    manifest=read_json(root/'input-manifest.json')
    if manifest.get('format')!=INPUT_VERSION:raise PackageError('unsupported_input_version')
    names=set(manifest.get('files',{}))
    if names not in (INPUT_FILES,INPUT_FILES|{'code.zip'}):raise PackageError('unexpected_manifest_files')
    _check_files(root,manifest,names)
    packet,request,runtime=[read_json(root/n) for n in ('packet.json','request.json','runtime.json')]
    identity='rgpt_'+digest(canonical([packet,request,runtime]))[:24]
    if manifest['package_id']!=identity:raise PackageError('input_identity_mismatch')
    paper=Paper(**packet['paper'])
    if paper.document_sha256!=manifest['document_sha256'] or paper.document_sha256!=packet['document_sha256']:
        raise PackageError('input_document_mismatch')
    if packet['code_commit']!=manifest['code_commit'] or not re.fullmatch(r'[a-f0-9]{40}',manifest['code_commit']):
        raise PackageError('input_code_commit_mismatch')
    if request['output_schema']!=schema(request['messages'][-1]['content']):raise PackageError('output_schema_changed')
    try:validate_contract(request)
    except ValueError:raise PackageError('selection_contract_mismatch') from None
    if request['generation_profile']!=runtime['generation']:raise PackageError('generation_profile_mismatch')
    if not re.fullmatch(r'[a-f0-9]{40}',runtime['requested_model']['revision']):raise PackageError('model_revision_not_pinned')
    chunks={c['chunk_id']:Chunk(**c) for c in packet['chunks']}
    if len(chunks)!=len(packet['chunks']):raise PackageError('duplicate_source_ids')
    bundle_by_id={b['bundle_id']:EvidenceBundle(**b) for b in packet['bundles']}
    if any(c.paper_id!=paper.paper_id for c in chunks.values()):raise PackageError('cross_paper_source')
    for eid,value in packet['catalog'].items():
        obj=(EvidenceSpan if value['kind']=='span' else EvidenceBundle)(**value['item'])
        if eid!=(obj.span_id if isinstance(obj,EvidenceSpan) else obj.bundle_id):raise PackageError('catalog_id_mismatch')
        spans=[obj] if isinstance(obj,EvidenceSpan) else obj.spans
        if isinstance(obj,EvidenceBundle) and bundle_by_id.get(eid)!=obj:raise PackageError('catalog_bundle_mismatch')
        if f'[{eid}]' not in request['messages'][-1]['content']:raise PackageError('catalog_not_in_prompt')
        for s in spans:
            c=chunks.get(s.reference.chunk_id)
            if c is None:raise PackageError('unauthorized_source_id')
            a,b=s.reference.char_start-c.char_start,s.reference.char_end-c.char_start
            if a<0 or b>len(c.text) or c.text[a:b]!=s.text:raise PackageError('source_span_mismatch')
    for field in request['output_schema']['properties'].values():
        for eid in field['items']['properties']['evidence_id']['enum']:
            if eid!='UNAVAILABLE' and eid not in packet['catalog']:raise PackageError('schema_unauthorized_id')
    return manifest,packet,request,runtime


def create_result(root,input_root,raw,candidates,execution):
    manifest,packet,request,runtime=validate_input(input_root)
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    if any((root/n).exists() for n in RESULT_FILES|{'output-manifest.json'}):raise PackageError('result_would_overwrite')
    (root/'raw_response.txt').write_bytes(raw.encode('utf-8') if isinstance(raw,str) else raw)
    write_json(root/'candidates.json',candidates)
    write_json(root/'execution.json',execution)
    output={'format':OUTPUT_VERSION,'input_package_id':manifest['package_id'],
        'input_manifest_sha256':digest((Path(input_root)/'input-manifest.json').read_bytes()),
        'document_sha256':packet['document_sha256'],'files':_files(root,RESULT_FILES)}
    write_json(root/'output-manifest.json',output)
    return output


def result_archive(root):
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
        for name in sorted(RESULT_FILES|{'output-manifest.json'}):z.writestr(name,(Path(root)/name).read_bytes())
    return buf.getvalue()


def unpack_result(data,root):
    if len(data)>MAX_RESULT_BYTES:raise PackageError('result_archive_too_large')
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        infos=z.infolist();names=[x.filename for x in infos]
        if len(names)!=4 or set(names)!=RESULT_FILES|{'output-manifest.json'}:raise PackageError('unsafe_result_archive_members')
        if sum(i.file_size for i in infos)>MAX_RESULT_BYTES:raise PackageError('result_archive_too_large')
        for info in infos:(root/info.filename).write_bytes(z.read(info))


def import_result(input_root,result_root,*,output_root=None):
    manifest,packet,request,runtime=validate_input(input_root)
    paper=Paper(**packet['paper']);result_root=Path(result_root)
    if output_root:
        output_root=Path(output_root);output_root.mkdir(parents=True,exist_ok=False)
        for name in RESULT_FILES|{'output-manifest.json'}:
            path=result_root/name
            if path.is_file() and not path.is_symlink():shutil.copyfile(path,output_root/name)
    def failed(code):
        return ExtractedPaper(paper_id=paper.paper_id,acquisition_status=paper.acquisition_status,status='EXTRACTION_FAILED',
            evidence_bundles=[EvidenceBundle(**b) for b in packet['bundles']],
            fields={f:[FieldValue(field=f,status='FAILED',abstain_reason=code)] for f in FIELDS},
            errors=[{'stage':'remote_import','code':code}],trace={'remote_metadata_is_untrusted':True})
    try:
        remote=read_json(result_root/'output-manifest.json')
        if remote.get('format')!=OUTPUT_VERSION:raise PackageError('unsupported_result_version')
        _check_files(result_root,remote,RESULT_FILES)
        if remote.get('input_package_id')!=manifest['package_id'] or remote.get('input_manifest_sha256')!=digest((Path(input_root)/'input-manifest.json').read_bytes()):
            raise PackageError('remote_input_identity_mismatch')
        if remote.get('document_sha256')!=paper.document_sha256:raise PackageError('remote_document_mismatch')
        execution=read_json(result_root/'execution.json')
        if execution.get('requested_model')!=runtime['requested_model']:raise PackageError('remote_model_mismatch')
        if execution.get('status')!='COMPLETED':raise PackageError('remote_inference_not_completed')
        if execution.get('generation')!=runtime['generation'] or execution.get('quantization')!=runtime['quantization']:
            raise PackageError('remote_configuration_mismatch')
        if 'response_contract' in request and execution.get('response_contract')!=request['response_contract']:
            raise PackageError('remote_response_contract_mismatch')
        if execution.get('finish_reason') not in ('eos','stop') or any(type(execution.get(k)) is not int or execution[k]<0
            for k in ('prompt_tokens','generated_tokens')) or not isinstance(execution.get('runtime_seconds'),(int,float)):
            raise PackageError('remote_completion_metadata_missing')
        raw=(result_root/'raw_response.txt').read_bytes()
        normalized=parse_object(raw.decode('utf-8'))
        candidates=read_json(result_root/'candidates.json')
        if normalized!=candidates:raise PackageError('normalized_output_differs_from_raw')
        try:jsonschema.validate(candidates,request['output_schema'])
        except jsonschema.ValidationError:raise PackageError('remote_output_schema_invalid') from None
        from pipeline.inference.replay import replay
        result=replay(packet,candidates)
        result.trace.update(input_package_id=manifest['package_id'],raw_response_sha256=digest(raw),
            remote_execution_metadata=execution,remote_metadata_is_untrusted=True,
            verification='trusted_local_source_gate',independent_human_accuracy=None)
    except (ValueError,KeyError,OSError,TypeError) as exc:
        result=failed(str(exc) if isinstance(exc,PackageError) else 'malformed_remote_artifact')
    if output_root:write_json(output_root/'verified-result.json',result.model_dump(mode='json'))
    return result


class TrustedInputStore:
    def __init__(self,root):self.root=Path(root)

    def register(self,source):
        manifest,*_=validate_input(source)
        target=self.root/manifest['package_id'];target.mkdir(parents=True,exist_ok=False)
        for name in set(manifest['files'])|{'input-manifest.json'}:shutil.copyfile(Path(source)/name,target/name)
        return manifest['package_id']

    def get(self,package_id):
        if not re.fullmatch(r'rgpt_[a-f0-9]{24}',package_id):raise PackageError('invalid_registered_package_id')
        root=self.root/package_id
        if not root.is_dir():raise FileNotFoundError('registered inference input not found')
        validate_input(root)
        return root
