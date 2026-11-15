# Proposed complete tuple — independent review pending

**Ground truth: needs_human_review.** Reviewer, review time and verdict remain
empty in [selected_tuple_review.json](selected_tuple_review.json). The existing
12-item queue and frozen annotations are unchanged. Passing a deterministic
gate test does not turn this proposal into independent extraction gold.

| Attribute | Proposed source-backed interpretation |
|---|---|
| Paper | Attention Is All You Need, arXiv:1706.03762v7 [cs.CL], 2 Aug 2023 |
| Document SHA256 | bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697 |
| Table / page | arxiv:1706.03762:108:table / page8 |
| Exact model row | Transformer (big) |
| Benchmark/test set | newstest2014, literally named by the caption |
| Language condition | English-to-French, caption phrase linked to EN-FR header |
| Metric / value | BLEU /41.8 |
| Unit | null; no extra unit or experimental setting invented |
| Machine check | accepted by semantic_table_v1; not a real-model prediction |

Open the [exact source PDF](../../data/live/document.pdf) at page8. Its caption,
BLEU parent header, EN-FR leaf header, Transformer(big) row and41.8 cell support
separate linked spans. The paragraph beginning “Table 2 summarizes our results”
provides a same-table ownership reference. Full IDs, original offsets, native
word/block boxes and relation edges are in the JSON and minimal regression
fixture tests/fixtures/semantic_attention_v7.json.

The caption names newstest2014. WMT2014 appears in experimental prose; it is
not silently substituted as the caption benchmark. The separate41.0 EN-FR
prose statement is retained and is not used as the41.8 cell value.

![Exact page8 source rendering](../../outputs/semantic/attention-v7-page8.png)

Reviewer action: inspect the row/header hierarchy and benchmark/condition
interpretation against this exact PDF, then independently record reviewer,
timestamp and accepted/rejected/ambiguous verdict. Do not infer approval from
the machine-check result. Keep the document hash fixed when reviewing.
