# Teammate retrieval and backend contract

The implementation is operational through the existing FastAPI process/job
routes and the fixture HTTP flow. No teammate frontend migration is included.
Use the isolated `.venv-gpu` interpreter; dependencies and BGE-M3 are unchanged.

An opt-in local request uses the existing paper/project/upload fields plus:

```json
{
  "project_id": "a-new-review-project",
  "paper": {"paper_id": "arxiv:1706.03762", "title": "Attention Is All You Need"},
  "generation_profile": "bounded",
  "representation_profile": "table_context_v1",
  "retrieval": "table_aware_v1",
  "context_mode": "table_aware_v1"
}
```

POST to `/api/papers/process`, or POST `/api/jobs` and poll
`/api/jobs/{job_id}`. Supply `document_base64` and `representation:"pdf"` for
an upload. Network acquisition still depends on the source provider. No new
service, endpoint, auth system or frontend dependency is required. Defaults
remain five_query/current/baseline/default. `bounded` is local Ollama only;
hosted requests cannot silently substitute another generation policy.

`shared.schemas.RetrievalHit` is the executable retriever boundary:

| Field | Meaning |
|---|---|
| chunk | Complete shared Chunk; canonical paper/chunk/block IDs and original text |
| rank | Order returned by the adapter, starting at 1 |
| score, score_kind | Cosine similarity, RRF, or null/unscored_link; never mix scales |
| strategy | five_query, hybrid, or table_link_expansion_v1 |
| query | Query responsible for the best observed dense score, when applicable |

`pipeline.retrieval.retrievers.scored_records` converts returned chunks and
observed query traces into this contract without changing text or IDs.
Source metadata includes representation, source, page/node, section/path,
offset basis and ranges. Optional PDF metadata includes `source_bbox`,
`source_words` (native block/line/word IDs and PDF-point boxes), `table_id`,
`table_representation`, and `table_context.parts`. These survive Chroma JSON
round trips and SourceReference projection. Native block boxes may enclose
more than a split chunk: do not display them as exact cell/character boxes.

Five-query union order is source order, so its returned rank is **not** a dense
query rank. Dense union scores are the best observed similarity across the
unchanged five queries. Per-query ranks/distances/scores are separately exposed
in `trace.retrieval_queries`. Hybrid scores are RRF before optional reranking;
its returned rank follows the reranker when injected. Reranking is optional and
has no real-model accuracy validation. The existing rank-bm25 adapter is tested;
teammate code using `bm25_N` IDs or prefix-based deduplication must translate to
canonical source IDs before this boundary. Do not replace BGE-M3 with BGE-base.

`trace.retrieval_records` contains score/strategy/rank plus source references;
`trace.retrieval_expansion` identifies linked additions. Expanded rows do not
receive invented retrieval scores. `trace.context` reports delivered, partial,
dropped IDs, budget units and reasons. Proxy byte budgets are not actual model
tokens; actual usage comes from `trace.model`.

Table-context representation is additive and versioned. Baseline text,
offsets, block/chunk IDs and embedding input strings remain unchanged. Only
tables already reached through ordinary dense retrieval are expanded; all
linked caption/header/row chunks fit together or the whole group is withheld
from table-aware context. Unsupported layouts retain raw text. Table 2's
`unstructured_table_text` does not authorize cell binding or numerical tuples.

Only FieldValues with `final:"RETURNED"`, `status:"VERIFIED"`, explicit
evidence and valid source references are findings. Display `ABSTAINED`,
`AMBIGUOUS`, `MISSING` and `FAILED` as distinct states, together with acquisition
status and abstention/error reasons. `AMBIGUOUS` still has final ABSTAINED.
Never promote a withheld value or an annotation-queue proposal into a finding.
Quotes returned by the resolver are exact original source slices; proposed
model wording is retained separately. Wrong IDs are never remapped.

Validated integration: real parsing/Chroma/BM25 modules and deterministic
test-only encoder/LLM in HTTP tests, plus a separately recorded actual GPU
paper run. Remaining teammate work is client mapping, citation rendering,
uppercase job/status handling and durable/authenticated deployment if needed.
