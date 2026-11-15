import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from pipeline.extraction.selection import relationship_context
from scripts.replay_accuracy_packet import replay
from tests.test_accuracy_evidence import parsed


def test_same_packet_schema_and_host_verifier_support_remote_replay():
    a,d,chunks,bundles=parsed();ctx=relationship_context(chunks,bundles,input_budget=4000)
    packet=dict(paper=a.paper.model_dump(),document_sha256=a.paper.document_sha256,
        chunks=[c.model_dump() for c in chunks],bundles=[b.model_dump() for b in bundles],context_trace=ctx.trace,
        catalog={k:dict(kind='span' if hasattr(v,'span_id') else 'bundle',item=v.model_dump()) for k,v in ctx.catalog.items()})
    first=next(k for k in ctx.catalog if k.startswith('bundle:'))
    good=replay(packet,{'results':[{'evidence_id':first}]})
    bad=replay(packet,{'results':[{'evidence_id':'invented'}]})
    assert good.fields['results'][0].final=='RETURNED'
    assert bad.fields['results'][0].final=='ABSTAINED'
    assert good.trace['independent_human_accuracy'] is None
    packet['document_sha256']='0'*64
    with pytest.raises(ValueError):replay(packet,{})


def test_private_input_manifest_path_and_hash_guards(tmp_path):
    spec=importlib.util.spec_from_file_location('accuracy_remote',Path('kaggle/run_accuracy.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    data=b'fixture';(tmp_path/'document.pdf').write_bytes(data)
    entry={'relative_path':'document.pdf','document_sha256':hashlib.sha256(data).hexdigest()}
    assert module.checked_document(entry,tmp_path)[1]==data
    with pytest.raises(ValueError):module.checked_document({**entry,'relative_path':'../outside.pdf'},tmp_path)
    with pytest.raises(ValueError):module.checked_document({**entry,'document_sha256':'0'*64},tmp_path)
