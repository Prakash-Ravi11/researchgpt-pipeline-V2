"""Replaceable parser boundary and conservative, native-text table reconstruction.

This route supports repeated leaf headers under unique metric parents, within
caption-linked horizontal rules. Shared/merged numeric cells are not split.
All anchors map to original chunks; no reconstructed Markdown becomes source.
"""
from __future__ import annotations

import hashlib
import re
from typing import Protocol

from shared.schemas import Chunk, EvidenceBundle, EvidenceSpan


class StructuralParser(Protocol):
    identity: str
    def reconstruct(self, document, doc: dict, chunks: list[Chunk]) -> list[EvidenceBundle]: ...


def _center(box):
    return ((box[0]+box[2])/2, (box[1]+box[3])/2)


def source_span(chunks, text, role, *, bbox=None, page=None, table_id=None):
    """Map native text plus geometry to an exact original slice, including repeats."""
    matches = []
    for c in chunks:
        if page and c.page_or_node != f"p{page}":
            continue
        if table_id and getattr(c, "table_id", None) != table_id:
            continue
        found = [m.start() for m in re.finditer(re.escape(text), c.text)]
        if not found:
            continue
        if bbox is not None:
            words = [w for w in getattr(c, "source_words", []) if w["text"] == text]
            positions = [i for i, w in enumerate(words) if all(abs(a-b)<.5 for a,b in zip(w["bbox"],bbox))]
            if positions:
                if len(words) != len(found) or len(positions) != 1:
                    continue
                found = [found[positions[0]]]
            elif len(found) != 1:
                continue
            elif not getattr(c, "source_bbox", None) or not (
                c.source_bbox[0]-.5 <= bbox[0] and c.source_bbox[2]+.5 >= bbox[2]
                and c.source_bbox[1]-.5 <= bbox[1] and c.source_bbox[3]+.5 >= bbox[3]):
                continue
        for start in found:
            ref = c.reference().model_copy(update={"char_start":c.char_start+start,
                                                   "char_end":c.char_start+start+len(text)})
            sid = f"{c.chunk_id}@{start}:{start+len(text)}:{role}"
            matches.append(EvidenceSpan(span_id=sid, role=role,text=text,reference=ref,bbox=bbox))
    return matches[0] if len(matches)==1 else None


class NativeHeaderParser:
    identity = "native_header_geometry_v1"

    def reconstruct(self, document, doc, chunks):
        import pymupdf
        output = []
        digest = hashlib.sha256(document.data).hexdigest()
        with pymupdf.open(stream=document.data,filetype="pdf") as pdf:
            for table in doc.get("linked_tables", []):
                page = pdf[table["page"]-1]
                box = table["bbox"]
                rules = sorted({round(d["rect"].y0,2) for d in page.get_drawings()
                    if abs(d["rect"].height)<1 and abs(d["rect"].x0-(box[0]+2))<3
                    and abs(d["rect"].x1-(box[2]-2))<3 and box[1]-.1<=d["rect"].y0<=box[3]+.1})
                if len(rules)<3:
                    continue
                # First complete rule below the top separates header from body.
                header_bottom = rules[1]
                words = [w for w in page.get_text("words") if box[0]<=w[0] and w[2]<=box[2]
                         and box[1]-1<=w[1] and w[3]<=box[3]+1]
                headers = [w for w in words if w[3]<=header_bottom+1]
                groups = {}
                for w in headers:
                    groups.setdefault((w[5],w[6]),[]).append(w)
                lines = []
                for ws in groups.values():
                    ws.sort(key=lambda w:w[0])
                    lines.append((" ".join(w[4] for w in ws),
                                  [min(w[0] for w in ws),min(w[1] for w in ws),
                                   max(w[2] for w in ws),max(w[3] for w in ws)]))
                if not lines:
                    continue
                bottom_y = max(_center(b)[1] for _,b in lines)
                leaves = [(t,b) for t,b in lines if abs(_center(b)[1]-bottom_y)<2]
                parents = [(t,b) for t,b in lines if _center(b)[1]<bottom_y-5]
                # A hierarchy must be demonstrated by repeated leaf labels.
                if len(leaves)<2 or len({t for t,_ in leaves})==len(leaves) or len(parents)<2:
                    continue
                parents.sort(key=lambda x:_center(x[1])[0])
                columns = []
                for leaf,lb in leaves:
                    nearest = sorted(parents,key=lambda p:abs(_center(p[1])[0]-_center(lb)[0]))
                    if len(nearest)>1 and abs(abs(_center(nearest[0][1])[0]-_center(lb)[0])-
                                             abs(_center(nearest[1][1])[0]-_center(lb)[0]))<3:
                        continue
                    parent,pb=nearest[0]
                    # A merged parent must have at least two distinct children.
                    siblings=[l for l,b in leaves if min(parents,key=lambda p:abs(_center(p[1])[0]-_center(b)[0]))[0]==parent]
                    if len(siblings)<2 or len(set(siblings))!=len(siblings):
                        continue
                    columns.append((leaf,lb,parent,pb))
                if not columns:
                    continue
                first_column = min(b[0] for _,b,_,_ in columns)
                caption = source_span(chunks,table["caption"],"caption",page=table["page"],table_id=table["table_id"])
                rows = [p for p in table["parts"] if p["bbox"][1]>=header_bottom-1]
                for ri,row in enumerate(rows):
                    rw=[w for w in words if row["bbox"][1]-.5<=w[1] and w[3]<=row["bbox"][3]+.5]
                    labels=[w for w in rw if w[2]<first_column-3]
                    label=" ".join(w[4] for w in labels)
                    if not label or not caption:
                        continue
                    model=source_span(chunks,label,"subject",page=table["page"],table_id=table["table_id"])
                    if not model:
                        continue
                    for ci,(dataset,lb,metric,pb) in enumerate(columns):
                        family=[b for _,b,m,_ in columns if m==metric]
                        family_words=[w for w in rw if min(b[0] for b in family)-4<=_center(w[:4])[0]
                                      <=max(b[2] for b in family)+4]
                        if any(re.search(r"[·×^±]|\d[eE][+-]?\d",w[4]) for w in family_words):
                            continue  # scientific products/merged values stay unresolved
                        candidates=[w for w in rw if re.fullmatch(r"\d+(?:\.\d+)?",w[4])
                                    and lb[0]-2<=_center(w[:4])[0]<=lb[2]+2]
                        # No shared cost cell, multiple values or inferred exponent.
                        if len(candidates)!=1:
                            continue
                        w=candidates[0]
                        value=source_span(chunks,w[4],"value",bbox=list(w[:4]),page=table["page"],table_id=table["table_id"])
                        ds=source_span(chunks,dataset,"dataset",bbox=lb,page=table["page"],table_id=table["table_id"])
                        met=source_span(chunks,metric,"metric",bbox=pb,page=table["page"],table_id=table["table_id"])
                        if not all((value,ds,met)):
                            continue
                        key=f"{digest}:{table['table_id']}:{ri}:{ci}:{w[4]}"
                        output.append(EvidenceBundle(bundle_id="bundle:"+hashlib.sha256(key.encode()).hexdigest()[:24],
                            paper_id=document.paper.paper_id,document_sha256=digest,table_id=table["table_id"],
                            parser=self.identity,parser_revision=pymupdf.VersionBind,linkage=self.identity,
                            structural_status="SOURCE_ALIGNED",row=ri,column=ci,spans=[caption,model,ds,met,value]))
        return output


def reconstruct(document, doc, chunks, parser: StructuralParser | None=None):
    if doc["representation"]!="pdf":
        doc["accuracy_route"]={"parser":"native_structured_source", "status":"baseline_structure_preserved"}
        return []
    parser=parser or NativeHeaderParser()
    bundles=parser.reconstruct(document,doc,chunks)
    doc["accuracy_route"]={"parser":parser.identity,"source_aligned_bundles":len(bundles),
        "escalations":[{"table_id":t["table_id"],"reason":"unresolved_header_or_cell_relationships",
                        "candidate_backend":"docling_tableformer_accurate"}
                       for t in doc.get("linked_tables",[]) if not t.get("cell_binding_verified")]}
    return bundles
