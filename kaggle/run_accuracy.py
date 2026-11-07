"""Remote-only controlled parser/extractor jobs. No publishing or credentials.

Imports heavy dependencies only for the selected job. Failures retain a typed
report; an unavailable backend never becomes a baseline substitution.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


def checked_document(entry,input_root):
    root=Path(input_root).resolve()
    path=(root/entry["relative_path"]).resolve()
    if not path.is_relative_to(root):raise ValueError("document escapes private input root")
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=entry["document_sha256"]:raise ValueError("document hash mismatch")
    return path,data


def parse(args,report):
    from pipeline.acquisition.source import from_bytes
    from pipeline.parsing.documents import process
    from shared.schemas import Paper
    from pipeline.parsing.docling_backend import DoclingProposalParser
    import pymupdf
    import torch
    if not torch.cuda.is_available():raise RuntimeError("requested parser GPU unavailable")
    report["gpu"]=torch.cuda.get_device_name(0)
    report["docling_version"]=importlib.metadata.version("docling")
    if report["docling_version"]!="2.148.0":raise RuntimeError("parser version differs from candidate lock")
    assets=args.output/'parser-assets'
    # Isolated runtime assets; their exact bytes become part of the exported run.
    subprocess.run([str(Path(sys.executable).with_name('docling-tools')),'models','download',
                    'layout','tableformer','rapidocr','--output-dir',str(assets)],check=True)
    report["asset_sha256"]={str(p.relative_to(assets)):hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in assets.rglob('*') if p.is_file()}
    manifest=json.loads(args.manifest.read_text(encoding='utf-8'))
    results=[]
    for i,entry in enumerate(manifest['documents']):
        path,data=checked_document(entry,args.input_root)
        paper=Paper(paper_id=entry['paper_id'],title=entry['title'],externalIds=entry.get('externalIds',{}))
        acquired=from_bytes(paper,data,'pdf','private_manifest')
        if acquired.paper.acquisition_status!='FULL_TEXT':raise ValueError('document identity/content validation failed')
        base,bc=process(acquired)
        native,nc=process(acquired,'accuracy_v1')
        with pymupdf.open(stream=data,filetype='pdf') as pdf:
            text_missing=any(len(p.get_text().strip())<20 for p in pdf)
        started=time.perf_counter()
        proposed,_=process(acquired,'accuracy_v1',structural_parser=DoclingProposalParser(path,assets,text_missing))
        export=proposed['external_structure_proposal']['document']
        write(args.output/f'document-{i}-docling-proposal.json',dict(paper_id=entry['paper_id'],
            document_sha256=entry['document_sha256'],parser='docling_tableformer_accurate',
            parser_version=report['docling_version'],status='EXTERNAL_PROPOSAL',document=export))
        # JSON is intentionally a proposal: no markdown or predicted number is
        # inserted into the trusted original source stream or auto-verified.
        results.append(dict(paper_id=entry['paper_id'],split=entry['split'],ocr_enabled=text_missing,
            baseline_structured_tables=base['n_tables_structured'],native_bundles=len(native['evidence_bundles']),
            docling_table_proposals=len(export.get('tables',[])),seconds=time.perf_counter()-started,
            independent_structural_accuracy=None,review_required=True))
    report['documents']=results


def extract(args,report):
    import torch
    import jsonschema
    from transformers import AutoModelForCausalLM,AutoTokenizer,BitsAndBytesConfig
    from pipeline.extraction.clients import parse_object
    from pipeline.extraction.selection import schema
    configs=json.loads((Path(__file__).parent/'models.json').read_text())
    config=configs[args.model]
    if not torch.cuda.is_available():raise RuntimeError('requested extraction GPU unavailable')
    free,total=torch.cuda.mem_get_info(0)
    if free<config['minimum_free_bytes']:raise RuntimeError('insufficient free VRAM for selected candidate')
    report.update(model_config=config,gpu=torch.cuda.get_device_name(0),free_before_load=free,
                  quantization='bitsandbytes NF4 double-quant, FP16 compute',enable_thinking=False)
    packet=json.loads(args.packet.read_text(encoding='utf-8'))
    report['packet_sha256']=hashlib.sha256(args.packet.read_bytes()).hexdigest()
    tokenizer=AutoTokenizer.from_pretrained(config['model'],revision=config['revision'])
    model=AutoModelForCausalLM.from_pretrained(config['model'],revision=config['revision'],
        device_map={'':0},torch_dtype=torch.float16,quantization_config=BitsAndBytesConfig(load_in_4bit=True,
            bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.float16))
    text=tokenizer.apply_chat_template(packet['messages'],tokenize=False,add_generation_prompt=True,enable_thinking=False)
    inputs=tokenizer(text,return_tensors='pt').to('cuda:0')
    if inputs.input_ids.shape[1]+2048>8192:raise ValueError('complete evidence exceeds context budget; no silent truncation')
    torch.manual_seed(42);torch.cuda.reset_peak_memory_stats()
    started=time.perf_counter()
    with torch.inference_mode():output=model.generate(**inputs,max_new_tokens=2048,do_sample=False)
    ids=output[0,inputs.input_ids.shape[1]:]
    content=tokenizer.decode(ids,skip_special_tokens=True)
    (args.output/'raw_response.txt').write_text(content,encoding='utf-8')
    if len(ids)>=2048 and ids[-1].item()!=tokenizer.eos_token_id:raise ValueError('incomplete model output')
    parsed=parse_object(content)
    jsonschema.validate(parsed,schema(packet['messages'][-1]['content']))
    write(args.output/'candidates.json',parsed)
    report.update(prompt_tokens=int(inputs.input_ids.shape[1]),generated_tokens=len(ids),
        seconds=time.perf_counter()-started,torch_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
        scientific_accuracy=None,verification='requires local immutable packet replay; generated proposals only')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('job',choices=['parser','extractor'])
    p.add_argument('--manifest',type=Path)
    p.add_argument('--input-root',type=Path,default=Path('/kaggle/input/rgpt-private-papers'))
    p.add_argument('--packet',type=Path)
    p.add_argument('--model',choices=['qwen3-8b','qwen3-14b'],default='qwen3-8b')
    p.add_argument('--device',type=int,choices=[0,1],default=0)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']=str(args.device) # one physical GPU, never pool two T4s
    args.output.mkdir(parents=True,exist_ok=False)
    report=dict(status='RUNNING',job=args.job,physical_gpu_requested=args.device,interpreter=sys.executable,
                python=sys.version,independent_human_accuracy=None)
    try:
        (parse if args.job=='parser' else extract)(args,report)
        report['status']='EXECUTED'
    except Exception as exc:
        report.update(status='FAILED',error_type=type(exc).__name__,error=str(exc))
        raise
    finally:
        report['packages']=dict((d.metadata['Name'],d.version) for d in importlib.metadata.distributions())
        write(args.output/'execution.json',report)


if __name__=='__main__':main()
