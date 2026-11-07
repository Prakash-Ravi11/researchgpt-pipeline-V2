"""One fresh real-model API execution. In-process HTTP/ASGI, not mocked models."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys
import time
import weakref

import numpy as np
import requests
import torch
from fastapi.testclient import TestClient

from api.main import create_app
from pipeline.extraction.profiles import local_client
from pipeline.extraction.selection import schema
from pipeline.retrieval.index import BGEEncoder,ChromaIndex
from pipeline.service import EvidencePipeline
from scripts.validate_real_paper import Monitor,snapshot,save
from shared.schemas import Paper


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if Path(sys.prefix).resolve()!=(Path.cwd()/'.venv-gpu').resolve():raise RuntimeError('wrong interpreter')
    args.output.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter()
    report=dict(interpreter=sys.executable,python=sys.version,scope='real PDF, BGE, Chroma and Qwen through HTTP ASGI route',
        independent_human_accuracy=None,snapshots=[snapshot('before_any_model')],mock_models=False)
    initial=report['snapshots'][0]['ollama_models']
    if isinstance(initial,list) and any(m.get('name')=='qwen2.5:7b' for m in initial):
        requests.post('http://localhost:11434/api/generate',json={'model':'qwen2.5:7b','keep_alive':0},timeout=30).raise_for_status()
    report['snapshots'].append(snapshot('before_bge'))
    torch.cuda.reset_peak_memory_stats()
    class Encoder(BGEEncoder):
        ref=None
        def encode(self,texts):
            if self._model is None:self.ref=weakref.ref(self.model)
            return super().encode(texts)
        def release(self):
            result=super().release();result['model_weakref_gone']=self.ref is None or self.ref() is None
            report['release']=result;report['snapshots'].append(snapshot('after_bge_release'))
            return result
    encoder=Encoder('cuda')
    class Index(ChromaIndex):
        def replace_paper(self,pid,cs):
            assert self.collection.count()==0
            super().replace_paper(pid,cs)
            assert self.all_chunks(pid)==cs
            data=self.collection.get(include=['embeddings'])
            vectors=np.asarray(data['embeddings'])
            assert vectors.shape==(len(cs),1024) and np.isfinite(vectors).all()
            assert np.allclose(np.linalg.norm(vectors,axis=1),1,atol=.005)
            control=ChromaIndex('control-'+args.output.name,args.output/'fresh-chroma',encoder)
            assert control.collection.count()==0
            report['index']=dict(collection=self.collection.name,count=self.collection.count(),
                initial_count=0,ids_metadata_roundtrip=True,finite_normalized_embeddings=True,
                shape=list(vectors.shape),configuration=self.collection.metadata,empty_control=control.collection.name)
    index=Index('accuracy-'+args.output.name,args.output/'fresh-chroma',encoder)
    def observe(event,payload):
        save(args.output/('ollama_'+event+'.json'),payload)
        if event=='request':
            assert encoder._model is None
            report['snapshots'].append(snapshot('immediately_before_qwen'))
    llm=local_client('bounded',schema_factory=schema,observer=observe)
    def factory(req):
        return EvidencePipeline(None,index,llm,retrieval=req.retrieval,context_mode=req.context_mode,
            representation_profile=req.representation_profile,extraction_mode=req.extraction_mode)
    monitor=Monitor(args.output);monitor.thread.start()
    try:
        paper=Paper.model_validate_json(Path('data/live/paper.json').read_text(encoding='utf-8'))
        pdf=Path('data/live/document.pdf').read_bytes()
        assert hashlib.sha256(pdf).hexdigest()==paper.document_sha256
        with TestClient(create_app(factory)) as client:
            result=client.post('/api/papers/process',json=dict(project_id='accuracy-'+args.output.name,
                paper=paper.model_dump(mode='json'),document_base64=base64.b64encode(pdf).decode(),representation='pdf',
                representation_profile='accuracy_v1',retrieval='table_aware_v1',context_mode='relationship_v1',
                generation_profile='bounded',extraction_mode='selection_v1'))
        report['http_status']=result.status_code
        result.raise_for_status()
        response=result.json();save(args.output/'api_response.json',response)
        report.update(status=response['status'],errors=response['errors'],document_sha256=paper.document_sha256,
            context=response['trace'].get('context'),model=response['trace'].get('model'),
            bundles=len(response['evidence_bundles']),stage_ms=response['trace']['stage_ms'],
            fields=response['fields'],source='arXiv v7, previously inspected development document')
        report['snapshots'].append(snapshot('after_qwen'))
        report['query_trace']=index.query_trace
    finally:
        if encoder._model is not None:encoder.release()
        report['torch_peak_allocated_bytes']=torch.cuda.max_memory_allocated()
        report['torch_peak_reserved_bytes']=torch.cuda.max_memory_reserved()
        requests.post('http://localhost:11434/api/generate',json={'model':'qwen2.5:7b','keep_alive':0},timeout=30).raise_for_status()
        report['snapshots'].append(snapshot('after_qwen_unload'));monitor.stop()
        report['global_gpu_peak_used_mib']=max((s['gpu'].get('used_mib',0) for s in monitor.samples),default=None)
        report['ollama_peak_size_vram_bytes']=max((m.get('size_vram',0) for s in monitor.samples
            for m in s['ollama_models'] if isinstance(s['ollama_models'],list)),default=None)
        report['total_seconds']=time.perf_counter()-started
        save(args.output/'execution.json',report)
    print(json.dumps({k:report.get(k) for k in ('status','http_status','errors','bundles','model','total_seconds')},indent=2))
    if report['errors']:raise SystemExit(2)


if __name__=='__main__':main()
