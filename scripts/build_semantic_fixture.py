"""Prepare a minimal source-backed review/regression fixture, never human gold."""
import argparse
import hashlib
import json
from pathlib import Path

from pipeline.acquisition.source import from_bytes
from pipeline.parsing.documents import process
from shared.schemas import Paper, EvidenceBundle, SourceReference, Chunk


def build(subject,condition):
    data=Path('data/live/document.pdf').read_bytes()
    paper=Paper.model_validate_json(Path('data/live/paper.json').read_text(encoding='utf-8'))
    if hashlib.sha256(data).hexdigest()!=paper.document_sha256:raise ValueError('PDF version mismatch')
    acquired=from_bytes(paper,data,'pdf','arxiv')
    doc,chunks=process(acquired,'semantic_v1')
    candidates=[EvidenceBundle(**b) for b in doc['evidence_bundles'] if b['semantic']['status']=='RESOLVED'
        and b['semantic']['condition']==condition and next(s['text'] for s in b['spans'] if s['role']=='subject')==subject]
    if len(candidates)!=1:raise ValueError('selected source relationship is not unique')
    bundle=candidates[0]
    needed={s.reference.chunk_id for s in bundle.spans}
    words={bundle.semantic.benchmark,bundle.semantic.condition}
    keep=set(SourceReference.model_fields)|{'table_id','source_bbox','source_words'}
    def trim(record):
        out={k:v for k,v in record.items() if k in keep}
        if 'source_words' in out:out['source_words']=[w for w in out['source_words'] if w['text'] in words]
        return out
    raw=bundle.model_dump()
    for span in raw['spans']:span['reference']=trim(span['reference'])
    cs=[]
    for c in chunks:
        if c.chunk_id not in needed:continue
        item=trim(c.model_dump())
        item.update(text=c.text,block_type=c.block_type,chunk_index=c.chunk_index)
        cs.append(item)
    return dict(scope='source-backed deterministic verifier fixture; not independent extraction gold',
        ground_truth_status='needs_human_review',reviewer='',reviewed_at='',verdict='',
        source_version='arXiv:1706.03762v7 [cs.CL], 2 Aug 2023',source_pdf='data/live/document.pdf',
        paper=acquired.paper.model_dump(mode='json',include={'paper_id','title','acquisition_status','representation_type',
            'has_full_text','identity_validation','content_validation','document_sha256'}),
        bundle=raw,chunks=cs,expected_tuple=dict(subject=subject,benchmark=bundle.semantic.benchmark,
            dataset=bundle.semantic.benchmark,condition=condition,metric=bundle.semantic.metric,
            value=next(s.text for s in bundle.spans if s.role=='value'),unit=bundle.semantic.unit,setting=None))


def main():
    p=argparse.ArgumentParser();p.add_argument('--subject',required=True);p.add_argument('--condition',required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(build(args.subject,args.condition),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
