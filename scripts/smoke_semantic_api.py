"""Real PDF/parser/API with explicit test-only encoder and injected selector.

This checks the connected source-to-response path, never real LLM accuracy.
"""
import argparse
import base64
import json
from pathlib import Path
import re

from fastapi.testclient import TestClient
from api.main import create_app
from pipeline.retrieval.index import ChromaIndex
from pipeline.service import EvidencePipeline
from shared.schemas import Paper,LLMResponse
from tests.helpers import TinyEncoder


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    class FixtureSelector:
        def complete(self,system,user):
            candidates=[]
            for match in re.finditer(r'\[(bundle:[^\]\n]+)\]\n([^\n]+)',user):
                item=json.loads(match[2])
                if item.get('semantic_binding',{}).get('condition')=='English-to-French':candidates.append(match[1])
            if len(candidates)!=1:raise ValueError('fixture requires one source-supported condition')
            return LLMResponse(content={'results':[{'evidence_id':candidates[0]}]},provider='controlled_fixture',
                model='injected_source_id_not_a_real_model',latency_ms=0)
    recorded=json.loads(Path('outputs/accuracy/gpu-api-selection-v1/execution.json').read_text(encoding='utf-8'))
    by_query={q['query']:{h['chunk_id'] for h in q['hits']} for q in recorded['query_trace']}
    class RecordedRetrievalIndex(ChromaIndex):
        def search(self,query,pid,n=50):
            return [c for c in self.all_chunks(pid) if c.chunk_id in by_query[query]]
    def factory(req):
        return EvidencePipeline(None,RecordedRetrievalIndex(req.project_id,args.output/'fixture-chroma',TinyEncoder()),FixtureSelector(),
            representation_profile=req.representation_profile,retrieval=req.retrieval,context_mode=req.context_mode,
            extraction_mode=req.extraction_mode)
    paper=Paper.model_validate_json(Path('data/live/paper.json').read_text(encoding='utf-8'))
    assert paper.document_sha256==recorded['document_sha256']
    with TestClient(create_app(factory)) as client:
        response=client.post('/api/papers/process',json={'project_id':args.output.name,'paper':paper.model_dump(mode='json'),
            'document_base64':base64.b64encode(Path('data/live/document.pdf').read_bytes()).decode(),'representation':'pdf',
            'representation_profile':'semantic_v1','retrieval':'table_aware_v1','context_mode':'relationship_v1',
            'generation_profile':'bounded','extraction_mode':'selection_v1'})
    response.raise_for_status();data=response.json()
    (args.output/'response.json').write_text(json.dumps({'scope':'real source and connected modules; TEST-ONLY encoder, recorded real retrieval IDs, injected selection',
        'real_model_inference':False,'independent_accuracy':None,'response':data},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    out=data['fields']['results'][0]
    assert out['final']=='RETURNED' and out['scientific_tuple']['value']=='41.8'
    assert out['review_status']=='needs_human_review'
    print(json.dumps({'http_status':response.status_code,'status':data['status'],'scientific_tuple':out['scientific_tuple'],
        'real_model_inference':False,'review_status':out['review_status']}))


if __name__=='__main__':main()
