# Decisions

## Accepted project constraints

One FastAPI backend on port 8000. Shared BGE-M3 embeddings and ChromaDB, isolated per project. Canonical paper IDs and stable chunk IDs. Reuse provenance-aware chunking and evidence gate. Preserve five-query retrieval as baseline; hybrid is optional pending controlled measurement. Local and hosted LLMs use one interface. Extraction includes objective and future_scope. Do not replace parsers with a new general framework or copy the whole teammate app.

Implementation and compatibility decisions will be recorded after source inspection.
