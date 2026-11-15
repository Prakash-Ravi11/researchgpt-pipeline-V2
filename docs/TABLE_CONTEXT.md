# Readable scientific table context, version 1

Inspected the exact local *Attention Is All You Need* PDF, 15 readable text
pages, SHA-256
`bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697`.
Page1 prints `arXiv:1706.03762v7 [cs.CL], 2 Aug 2023`; metadata creation is
2024-04-10. No OCR or new parser package was installed. Page8 was visually
checked using the retained PyMuPDF render `outputs/recovery/attention-page8.png`.

The baseline PyMuPDF block stream preserves numerical characters and text
reading order but omits native block/word coordinates from its shared chunks.
Its ruled-grid detector does not produce validated Table2 cells. Table2 is
mixed: horizontal table/group/subheader rules, no vertical grid; BLEU and cost
have language subheaders, and the Transformer training-cost region spans
language columns. One native block combines language headers and early rows.
Treating newline order as a rectangular cell array would assert unproved
relationships.

`table_context_v1` maps exact native block text back to PDF block/word boxes.
For caption-linked horizontal-rule layouts it preserves a region and all
contained text parts under a common table ID. Text, normalized-document
offsets, block/chunk IDs and embedding strings remain untouched. It uses no
document-specific model names, values, page numbers or special cases. Caption
layouts without supported rule boundaries are recorded as unresolved and keep
baseline raw text. Scanned pages and genuinely borderless regions are not
claimed as supported by this version.

Table2 has ID `arxiv:1706.03762:108:table`, caption block108, header/source
parts109–111 and subsequent rows through119. The inferred region is approximately
`[128.69,94.52,483.31,243.61]` PDF points (top-left origin), beneath caption
`[107.69,71.20,504.00,92.07]`. Full-width shared rules occur near y=94.52,
124.86,181.69,216.40,243.61. Native row119 bbox is approximately
`[136.67,229.08,447.96,240.55]`. Word boxes retain native block/line/word IDs;
individual character boxes are **not** added. No synthetic cell positions or
exact character bboxes are claimed.

Its representation is explicitly `unstructured_table_text`, with
`cell_binding_verified:false`, the original caption/header/row texts and their
provenance. The row's first line is `Transformer (big)` followed by original
28.4 / 41.8 / flattened cost text. These relationships are accessible together
to reviewers and context assembly, but row/column bindings remain unverified
by the numerical gate. Separate prose block125 reports EN-FR41.0 and is never
rewritten or merged with the table's41.8.

`table_aware_v1` expands parser links only after one table source part appears
in the unchanged five-query top50 union. Atomic context selection delivers all
linked source parts or drops the complete group with an explicit budget reason.
Every original block keeps its own citation header; no generated caption or
row label is presented as a source quote. Baseline retrieval/context remain
available. The correction repairs link fragmentation and delivery, not dense
ranking. Final real-query ranks/scores are recorded in SPRINT_REPORT.md.

Tests build physical synthetic PDFs for both a validated ruled table and an
unstructured horizontal-rule table. They check intact text/offsets, no invented
fallback cells, outside-prose exclusion, source references, expansion and
all-or-none delivery. Existing grid/row/column/mutation tests also pass.

Later conditional experiment: reconstruct multi-level headers from the native
word geometry on a separately reviewed layout fixture set, validate merged
cost columns, and continue to fall back whenever alignment is ambiguous. This
does not require OCR on this readable PDF. No such cell-reconstruction or
independent-accuracy result is claimed in this sprint.
