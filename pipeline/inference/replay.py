"""Replay untrusted selections against the locally trusted source catalog."""
from types import SimpleNamespace
from pipeline.extraction.prompt import FIELDS
from pipeline.extraction.selection import verify_selection
from shared.schemas import Paper,Chunk,EvidenceBundle,EvidenceSpan,FieldValue,ExtractedPaper


def replay(packet,candidates):
    paper=Paper.model_validate(packet['paper'])
    if paper.document_sha256!=packet['document_sha256']:raise ValueError('packet document version mismatch')
    chunks=[Chunk(**c) for c in packet['chunks']]
    bundles=[EvidenceBundle(**b) for b in packet['bundles']]
    catalog={k:(EvidenceSpan if v['kind']=='span' else EvidenceBundle)(**v['item']) for k,v in packet['catalog'].items()}
    delivered=set(packet['context_trace']['delivered_chunk_ids'])
    context=SimpleNamespace(catalog=catalog,chunks=[c for c in chunks if c.chunk_id in delivered])
    if any(not isinstance(candidates.get(f,[]),list) for f in FIELDS):raise ValueError('invalid field arrays')
    fields={f:([verify_selection(f,c,paper,context,chunks,bundles) for c in candidates.get(f,[])]
               or [FieldValue(field=f,abstain_reason='missing_evidence')]) for f in FIELDS}
    status='PARTIAL' if any(v.final=='RETURNED' for vs in fields.values() for v in vs) else 'ABSTAINED'
    return ExtractedPaper(paper_id=paper.paper_id,acquisition_status=paper.acquisition_status,status=status,
        fields=fields,evidence_bundles=bundles,trace={'execution':'remote_proposals_local_host_verifier',
        'independent_human_accuracy':None,'reviewed_benchmark':'UNAVAILABLE'})
