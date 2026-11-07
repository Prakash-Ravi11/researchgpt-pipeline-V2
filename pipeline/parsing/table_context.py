"""Opt-in readable-PDF table context; never infer cells from an uncertain grid.

Horizontal rules with a shared extent delimit a region beneath a caption.
Unchanged native text blocks are linked, including mixed header/row blocks.
Coordinates are PDF points, top-left origin. Words retain native block/line IDs.
"""
import re


PROFILE = "table_context_v1"


def enrich_pdf(doc: dict, data: bytes) -> None:
    import pymupdf
    tables, unresolved = [], []
    with pymupdf.open(stream=data, filetype="pdf") as pdf:
        for pno, page in enumerate(pdf, 1):
            blocks = [b for b in doc["blocks"] if b["page_or_node"] == f"p{pno}"]
            native = page.get_text("blocks")
            words = page.get_text("words")
            for b in blocks:
                matches = ([pb for pb in native if b["text"] == pb[4].strip()]
                           or [pb for pb in native if b["text"] in pb[4]])
                if len(matches) == 1:
                    pb = matches[0]
                    b["source_bbox"] = list(pb[:4])
                    b["source_words"] = [dict(text=w[4], bbox=list(w[:4]), native_block=w[5],
                                               line=w[6], word=w[7]) for w in words if w[5] == pb[5]]
            lines = [list(d["rect"]) for d in page.get_drawings()
                     if abs(d["rect"].height) < 1 and d["rect"].width > page.rect.width * .3]
            for cap in blocks:
                if not re.match(r"^Table\s+\S+", cap["text"]) or "source_bbox" not in cap:
                    continue
                cb = cap["source_bbox"]
                tops = sorted([ln for ln in lines if cb[3] - 2 <= ln[1] <= cb[3] + 40], key=lambda x: x[1])
                if not tops:
                    unresolved.append({"caption_block_id": cap["block_id"], "reason": "no_supported_rule_boundary"})
                    continue
                top = tops[0]
                rules = sorted([ln for ln in lines if abs(ln[0]-top[0]) < 3 and abs(ln[2]-top[2]) < 3
                                and top[1] <= ln[1] <= top[1]+400], key=lambda x: x[1])
                # Stop at a large gap, rather than absorbing another table/footnote.
                group = [rules[0]]
                for ln in rules[1:]:
                    if ln[1] - group[-1][1] > 100:
                        break
                    group.append(ln)
                if len(group) < 2:
                    unresolved.append({"caption_block_id": cap["block_id"], "reason": "no_supported_bottom_boundary"})
                    continue
                region = [top[0]-2, top[1], top[2]+2, group[-1][1]]
                members = [b for b in blocks if b is not cap and "source_bbox" in b
                           and b["source_bbox"][0] >= region[0]-3 and b["source_bbox"][2] <= region[2]+3
                           and b["source_bbox"][1] >= region[1]-2 and b["source_bbox"][3] <= region[3]+2]
                if not members:
                    continue
                members.sort(key=lambda b: (b["source_bbox"][1], b["source_bbox"][0]))
                tid = cap["block_id"] + ":table"
                parts = [{"block_id": b["block_id"], "text": b["text"], "bbox": b["source_bbox"],
                          "char_start": b["char_start"], "char_end": b["char_end"],
                          "role": "caption" if b is cap else "header_or_row_text"} for b in [cap]+members]
                table = {"table_id": tid, "representation": "structured_table" if cap.get("table_cells")
                         else "unstructured_table_text", "caption": cap["text"], "page": pno,
                         "bbox": region, "parts": parts, "cell_binding_verified": bool(cap.get("table_cells")),
                         "layout_method": "caption_shared_horizontal_rules_v1"}
                for b in [cap]+members:
                    b.update(table_id=tid, table_representation=table["representation"], table_context=table)
                tables.append(table)
    doc.update(representation_profile=PROFILE, linked_tables=tables, unresolved_table_captions=unresolved)
