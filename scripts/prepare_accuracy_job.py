"""Export code and an immutable comparison packet; never copy PDFs or credentials."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

from pipeline.acquisition.source import from_bytes
from pipeline.parsing.documents import process
from pipeline.extraction.selection import relationship_context,SYSTEM
from shared.schemas import Paper,EvidenceBundle


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    paper=Paper.model_validate_json(Path('data/live/paper.json').read_text(encoding='utf-8'))
    data=Path('data/live/document.pdf').read_bytes()
    if hashlib.sha256(data).hexdigest()!=paper.document_sha256:raise ValueError('source hash mismatch')
    acquired=from_bytes(paper,data,'pdf','arxiv')
    doc,chunks=process(acquired,'accuracy_v1')
    bundles=[EvidenceBundle(**b) for b in doc['evidence_bundles']]
    context=relationship_context(chunks,bundles)
    packet=dict(paper=acquired.paper.model_dump(mode='json'),document_sha256=paper.document_sha256,
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        messages=[dict(role='system',content=SYSTEM),dict(role='user',content=f'Paper: {paper.title}\nAcquisition: FULL_TEXT\n\n{context.text}')],
        chunks=[c.model_dump() for c in chunks],bundles=[b.model_dump() for b in bundles],
        catalog={k:dict(kind='span' if hasattr(v,'span_id') else 'bundle',item=v.model_dump()) for k,v in context.catalog.items()},
        context_trace=context.trace,split='development_previously_inspected',independent_gold=False)
    manifest=dict(documents=[dict(paper_id=paper.paper_id,title=paper.title,externalIds=paper.externalIds,
        relative_path='document.pdf',document_sha256=paper.document_sha256,version='arXiv v7, 2 Aug 2023',
        split='development_previously_inspected',redistribution_status='private_mount_requires_user_rights_review')])
    for name,value in [('packet.json',packet),('input-manifest.json',manifest)]:
        (args.output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    allowed=[Path('pyproject.toml'),Path('docs/SOURCE_MANIFEST.json')]
    for root in ('shared','pipeline','src','configs','kaggle','scripts'):
        allowed += [x for x in Path(root).rglob('*') if x.is_file() and x.suffix in ('.py','.json','.yaml','.txt','.toml','.md')
                    and '__pycache__' not in x.parts]
    with zipfile.ZipFile(args.output/'code.zip','w',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(set(allowed)):
            info=zipfile.ZipInfo(path.as_posix(),(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,path.read_bytes())
    (args.output/'artifact-sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest()
        for p in args.output.iterdir() if p.is_file()},indent=2)+'\n')
    print(json.dumps(dict(output=str(args.output),pdf_copied=False,uploaded=False,bundle_count=len(bundles))))


if __name__=='__main__':main()
