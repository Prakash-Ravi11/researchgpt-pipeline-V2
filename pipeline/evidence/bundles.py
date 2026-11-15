"""Host-only multi-span verification, extending rather than bypassing the gate.

Bundles are constructed by the parser, never accepted from model JSON. Original
span integrity, row/header geometry, document identity, range and attribution
are independent checks. Human annotation status is not an accuracy claim.
"""
import hashlib
import re

from shared.schemas import EvidenceBundle, FieldValue
from src.evidence.attribute import attribute_claim
from src.evidence.gate import metric_range_check, classify_table


def verify_bundle(field, candidate, paper, delivered, corpus, bundles):
    item=FieldValue(field=field,status="ABSTAINED",evidence_status="UNSUPPORTED",verification_state="WITHHELD")
    def reject(reason,state="WITHHELD"):
        item.abstain_reason=reason
        if state=="UNAVAILABLE": item.status="MISSING"
        item.verification_state=state
        if state=="AMBIGUOUS": item.status="AMBIGUOUS"
        return item
    if paper.acquisition_status!="FULL_TEXT":
        return reject("no_validated_full_text","UNAVAILABLE")
    if field not in ("results","metrics","key_findings"):
        return reject("bundle_field_not_supported")
    bundle=next((b for b in bundles if b.bundle_id==candidate.get("evidence_id")),None)
    if bundle is None:
        return reject("unknown_evidence_bundle")
    item.evidence_bundle_id=bundle.bundle_id
    if bundle.paper_id!=paper.paper_id or bundle.document_sha256!=getattr(paper,"document_sha256",None):
        return reject("document_identity_or_version_mismatch")
    if bundle.linkage!="native_header_geometry_v1" or bundle.structural_status!="SOURCE_ALIGNED":
        return reject("unresolved_structural_linkage","UNAVAILABLE")
    if bundle.semantic and bundle.semantic.status!="RESOLVED":
        return reject(bundle.semantic.reason or "semantic_binding_unresolved",
                      "AMBIGUOUS" if bundle.semantic.status=="AMBIGUOUS" else "UNAVAILABLE")
    if "dataset_identity_requires_review" in bundle.unresolved:
        return reject("dataset_identity_unresolved","UNAVAILABLE")
    roles={s.role:s for s in bundle.spans}
    if any(sum(s.role==role for s in bundle.spans)!=1 for role in ("caption","subject","dataset","metric","value")):
        return reject("incomplete_or_ambiguous_bundle","AMBIGUOUS")
    source={c.chunk_id:c for c in corpus}
    shown={c.chunk_id:c for c in delivered}
    for s in bundle.spans:
        c=source.get(s.reference.chunk_id)
        d=shown.get(s.reference.chunk_id)
        if c is None or d is None or c.paper_id!=paper.paper_id:
            return reject("bundle_span_not_delivered")
        linked_ownership=bundle.semantic is not None and s.role=="ownership"
        if (not linked_ownership and getattr(c,"table_id",None)!=bundle.table_id) or s.reference.block_id!=c.block_id:
            return reject("unrelated_source_region")
        start,end=s.reference.char_start-c.char_start,s.reference.char_end-c.char_start
        if start<0 or end>len(c.text) or c.text[start:end]!=s.text:
            return reject("bundle_source_span_changed")
        ds,de=s.reference.char_start-d.char_start,s.reference.char_end-d.char_start
        if ds<0 or de>len(d.text) or d.text[ds:de]!=s.text:
            return reject("bundle_span_not_delivered")
    tup={k:roles[r].text for k,r in (("subject","subject"),("dataset","dataset"),("metric","metric"),("value","value"))}
    if bundle.semantic:
        semantic=bundle.semantic
        tup.update(dataset=semantic.benchmark,benchmark=semantic.benchmark,condition=semantic.condition,unit=semantic.unit)
    # A geometrically aligned column label may be a language pair, model size,
    # or condition rather than a dataset. No silent aliases or semantic upgrade.
    if not re.search(r"(?<!\w)"+re.escape(tup['dataset'])+r"(?!\w)",roles['caption'].text):
        return reject("dataset_identity_unresolved","UNAVAILABLE")
    # Optional explicit model proposal must agree with all canonical anchors.
    proposed=candidate.get("scientific_tuple")
    if proposed is not None:
        required=("subject","metric","value")
        agrees=all(proposed.get(k)==tup[k] for k in required)
        agrees=agrees and proposed.get("benchmark",proposed.get("dataset"))==tup["dataset"]
        if "dataset" in proposed:agrees=agrees and proposed["dataset"]==tup["dataset"]
        agrees=agrees and proposed.get("condition")==tup.get("condition") and proposed.get("unit")==tup.get("unit")
        if not agrees or proposed.get("setting"):return reject("scientific_tuple_disagrees_with_bundle")
    # Recompute structural attestation ID from coordinates/anchors captured by
    # the host parser. A model cannot mix spans from two pre-existing bundles.
    key=f"{bundle.document_sha256}:{bundle.table_id}:{bundle.row}:{bundle.column}:{tup['value']}"
    if bundle.bundle_id!="bundle:"+hashlib.sha256(key.encode()).hexdigest()[:24]:
        return reject("bundle_identity_changed")
    row=source[roles["value"].reference.chunk_id]
    if roles["subject"].reference.chunk_id!=row.chunk_id:
        return reject("wrong_model_row")
    vb,db,mb=roles["value"].bbox,roles["dataset"].bbox,roles["metric"].bbox
    if not all((vb,db,mb)) or not db[0]-2<=(vb[0]+vb[2])/2<=db[2]+2 or vb[1]<=db[3]:
        return reject("wrong_column_geometry")
    # Re-attest membership against the original native table, including parent
    # hierarchy; public parser proposals never get verification by a flag.
    known=getattr(row,"validated_bundle_spans",{})
    if known.get(bundle.bundle_id)!=[s.model_dump() for s in bundle.spans]:
        return reject("parser_attestation_missing_or_changed")
    if bundle.semantic:
        if getattr(row,"validated_semantic_bindings",{}).get(bundle.bundle_id)!=bundle.semantic.model_dump():
            return reject("semantic_attestation_missing_or_changed")
        # Rebuild from the original geometric anchors, not from model claims.
        from pipeline.parsing.semantic import bind_bundle
        raw=bundle.model_copy(update={"semantic":None,"spans":[s for s in bundle.spans
                                    if s.role in ("caption","subject","dataset","metric","value")]})
        rebuilt=bind_bundle(raw,corpus)
        if rebuilt.semantic!=bundle.semantic or rebuilt.spans!=bundle.spans:
            return reject("semantic_relation_disagrees_with_source")
    claim=f"{tup['subject']} achieves {tup['metric']} {tup['value']} on {tup['dataset']}"
    table_type=classify_table(roles["caption"].text,{tup["metric"]},{tup["subject"]})
    if table_type!="results":
        return reject(f"bound_to_{table_type}_table")
    if metric_range_check(claim) is not None:
        return reject("metric_value_out_of_range")
    section_context=(" ".join(s.text for s in bundle.spans if s.role=="ownership") if bundle.semantic else
                     " ".join(c.text for c in corpus if c.section==row.section)[:6000])
    attr=attribute_claim(row.text,tup["value"],block_type="table",section=row.section,
                         section_context=section_context,own_author_surnames=[])
    item.attribution=attr
    if attr["attribution"]!="OWN_PAPER":
        return reject("attributed_to_cited_work" if attr["attribution"]=="CITED_PAPER" else "ownership_unverified")
    return FieldValue(**{**item.model_dump(),"value":tup["value"],"scientific_tuple":{**tup,"unit":tup.get("unit"),"setting":None},
        "final":"RETURNED","status":"VERIFIED","verification_state":"VERIFIED","evidence_status":"EXPLICIT",
        "evidence_span":roles["value"].text,"source_refs":[s.reference for s in bundle.spans],
        "provenance_valid":True,"confidence":.8,"abstain_reason":None,
        "review_status":bundle.review_status,"verification_route":"semantic_table_v1" if bundle.semantic else "linked_native_table_v1"})


def attest(bundles, chunks):
    """Attach host attestations to canonical chunks, outside model proposals."""
    by_id={c.chunk_id:c for c in chunks}
    for b in bundles:
        c=by_id[next(s.reference.chunk_id for s in b.spans if s.role=="value")]
        data=dict(getattr(c,"validated_bundle_spans",{}))
        data[b.bundle_id]=[s.model_dump() for s in b.spans]
        c.validated_bundle_spans=data
        if b.semantic:
            bindings=dict(getattr(c,"validated_semantic_bindings",{}))
            bindings[b.bundle_id]=b.semantic.model_dump()
            c.validated_semantic_bindings=bindings
