"""Export, register and import portable inference jobs without GPU/model calls."""
import argparse
import json
from pathlib import Path
import subprocess
import zipfile

from pipeline.acquisition.source import from_bytes
from pipeline.parsing.documents import process
from pipeline.extraction.selection import relationship_context,SYSTEM
from pipeline.inference.packages import minimal_packet,create_input,validate_input,TrustedInputStore,import_result,digest
from shared.schemas import Paper,EvidenceBundle


def export(args):
    paper=Paper.model_validate_json(args.paper.read_text(encoding='utf-8'))
    data=args.pdf.read_bytes()
    if digest(data)!=paper.document_sha256:raise ValueError('PDF version mismatch')
    acquired=from_bytes(paper,data,'pdf','arxiv')
    doc,chunks=process(acquired,'semantic_v1')
    bundles=[EvidenceBundle(**b) for b in doc['evidence_bundles']]
    retrieved=chunks
    if args.retrieval_run:
        from pipeline.retrieval.retrievers import TableAwareRetriever
        recorded=json.loads(args.retrieval_run.read_text(encoding='utf-8'))
        if recorded['document_sha256']!=paper.document_sha256:raise ValueError('retrieval source mismatch')
        hits={q['query']:{h['chunk_id'] for h in q['hits']} for q in recorded['query_trace']}
        class RecordedIndex:
            def search(self,q,pid,n):return [c for c in chunks if c.chunk_id in hits[q]]
        retrieved=TableAwareRetriever(RecordedIndex()).retrieve(paper.paper_id,chunks)
    context=relationship_context(retrieved,bundles)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    packet=minimal_packet(acquired.paper,chunks,bundles,context,code_commit=commit,scope='previously_inspected_development_source')
    model=json.loads(Path('kaggle/models.json').read_text())[args.model]
    runtime={'requested_model':model,'model_key':args.model,
        'quantization':{'method':'bitsandbytes_nf4','compute_dtype':'float16','double_quant':True},
        'generation':{'context_window':8192,'max_new_tokens':2048,'do_sample':False,'seed':42,'enable_thinking':False},
        'baseline_configuration':{'model':'qwen2.5:7b','digest':'845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e',
                                  'quantization':'Q4_K_M','decoder':'ollama_json_schema','num_ctx':8192,'num_predict':2048,
                                  'temperature':0,'seed':42,'max_candidates_per_field':1,'client_timeout_seconds':180}}
    messages=[{'role':'system','content':SYSTEM},{'role':'user','content':f'Paper: {paper.title}\nAcquisition: FULL_TEXT\n\n{context.text}'}]
    manifest=create_input(args.output,packet,messages,runtime)
    # Portable code uses the same allowlist as the previous exporter; no input
    # corpus, secrets, checkpoints, databases or environments are archived.
    files=[Path('pyproject.toml'),Path('docs/SOURCE_MANIFEST.json')]
    for root in ('shared','pipeline','src','configs','kaggle','scripts'):
        files.extend(p for p in Path(root).rglob('*') if p.is_file() and p.suffix in ('.py','.json','.yaml','.txt','.toml','.md') and '__pycache__' not in p.parts)
    with zipfile.ZipFile(args.output/'code.zip','w',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(set(files)):
            info=zipfile.ZipInfo(path.as_posix(),(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,path.read_bytes())
    blob=(args.output/'code.zip').read_bytes()
    manifest['files']['code.zip']={'sha256':digest(blob),'bytes':len(blob)}
    from pipeline.inference.packages import write_json
    write_json(args.output/'input-manifest.json',manifest)
    validate_input(args.output)
    print(json.dumps({'package_id':manifest['package_id'],'input_manifest_sha256':digest((args.output/'input-manifest.json').read_bytes()),
        'output':str(args.output),'source_chunks':len(packet['chunks']),'bundles':len(packet['bundles']),'uploaded':False}))


def main():
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('export');p.add_argument('--pdf',type=Path,default=Path('data/live/document.pdf'))
    p.add_argument('--paper',type=Path,default=Path('data/live/paper.json'));p.add_argument('--retrieval-run',type=Path)
    p.add_argument('--model',choices=['qwen3-8b','qwen3-14b'],default='qwen3-8b');p.add_argument('--output',type=Path,required=True)
    p=sub.add_parser('register');p.add_argument('input',type=Path);p.add_argument('--store',type=Path,default=Path('data/inference-inputs'))
    p=sub.add_parser('import');p.add_argument('input',type=Path);p.add_argument('result',type=Path)
    p.add_argument('--expected-input-sha256',required=True);p.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.command=='export':export(args)
    elif args.command=='register':print(TrustedInputStore(args.store).register(args.input))
    else:
        validate_input(args.input,args.expected_input_sha256)
        result=import_result(args.input,args.result,output_root=args.output)
        print(json.dumps({'status':result.status,'errors':result.errors,'output':str(args.output)}))


if __name__=='__main__':main()
