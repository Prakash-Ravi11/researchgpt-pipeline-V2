# Proposed source facts awaiting independent review

These 12 entries in [annotations.template.json](annotations.template.json) are
agent-proposed review material, **not gold annotations, approved findings or
accuracy labels**. Every entry has status `needs_human_review`; reviewer,
reviewed_at and verdict are empty. Nothing here is supplied to the model or
used by the frozen A/B/C/D scoring. Do not auto-approve entries.

Source: *Attention Is All You Need*, visible PDF identifier
`arXiv:1706.03762v7 [cs.CL], 2 Aug 2023`, 15 pages. The PDF metadata creation
date is 2024-04-10; it does not replace the printed arXiv version.
SHA-256: `bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697`.
Local source: `data/live/document.pdf` (ignored, not committed).

| Entry | Proposed fact | Original location | Review concern |
|---|---|---|---|
| 01 | Transformer big, EN-DE, BLEU 28.4 | p8 Table 2, block119 | Multi-level header alignment |
| 02 | Transformer big, EN-FR, BLEU 41.8 | p8 Table 2, block119 | Keep distinct from prose 41.0 |
| 03 | Big model, EN-FR, BLEU 41.0 | p8 section6.1, block125 | Separate source statement |
| 04 | Encoder stack: 6 layers | p3 block35 | Architecture scope |
| 05 | Decoder stack: 6 layers | p3 block36 | Architecture scope |
| 06 | Base model dimension: 512 | p3 block35 | Base versus big |
| 07 | Base attention: 8 heads | p5 block65 | Base versus big |
| 08 | Feed-forward inner dimension: 2048 | p5 block74 | Base architecture |
| 09 | Base residual dropout: 0.1 | p8 block120 | Different big-model settings exist |
| 10 | One training machine: 8 NVIDIA P100 GPUs | p7 block100 | Hardware versus experiment scope |
| 11 | Big-model training: 3.5 days | p7 block100 | 300,000 steps, not base 12 hours |
| 12 | Big-model training cost: 2.3 × 10^19 FLOPs | p8 Table 2, block119 | Shared cost columns; flattened exponent |

Each JSON entry includes the exact original chunk quotation, normalized-document
character offsets, native PDF block bbox, source IDs, field/experiment/dataset/
metric/value/unit/setting and linked table source parts when applicable. Offsets
index the parser's untouched block stream, **not raw PDF bytes**. Bboxes identify
whole native text blocks, not a fabricated exact numeric cell. Table 2 remains
`unstructured_table_text`; proposed interpretations above require human review.

Review the actual PDF and linked headers/caption, confirm scope and original
quote, then independently record reviewer, time and verdict. Preserve rejected
entries and reasons. Any future accuracy evaluation requires a separately
frozen review set and protocol; editing this queue alone does not create one.
