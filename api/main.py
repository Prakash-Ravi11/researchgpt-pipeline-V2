"""Single FastAPI backend. Run uvicorn api.main:app --host 127.0.0.1 --port 8000."""
from __future__ import annotations

import base64
import binascii
import os
import threading
import uuid
from functools import lru_cache
from typing import Literal

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from pipeline.acquisition.source import LiteratureSource, from_bytes
from pipeline.extraction.clients import HostedClient, OllamaClient
from pipeline.extraction.context import revised_context, table_aware_context
from pipeline.extraction.profiles import local_client
from pipeline.retrieval.index import BGEEncoder, ChromaIndex
from pipeline.service import EvidencePipeline
from shared.schemas import ExtractedPaper, Job, Paper


class ProcessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: str = Field(min_length=1, max_length=200)
    paper: Paper
    retrieval: Literal["five_query", "hybrid", "table_aware_v1"] = "five_query"
    context_mode: Literal["current", "revised", "table_aware_v1"] = "current"
    representation_profile: Literal["baseline", "table_context_v1"] = "baseline"
    generation_profile: Literal["default", "bounded"] = "default"
    representation: Literal["pdf", "jats_xml"] | None = None
    document_base64: str | None = Field(default=None, max_length=53_333_336)


class DiscoverRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=5, ge=1, le=20)
    start_year: int = Field(default=1900, ge=1600)
    end_year: int = Field(default=2026, le=2100)


@lru_cache(maxsize=1)
def shared_encoder():
    return BGEEncoder(device=os.getenv("RGPT_EMBEDDING_DEVICE", "cpu"),
                      local_only=os.getenv("RGPT_ALLOW_MODEL_DOWNLOAD", "0") != "1")


def default_pipeline(req: ProcessRequest):
    provider = os.getenv("RGPT_LLM_PROVIDER", "ollama")
    if provider == "ollama":
        llm = local_client(req.generation_profile, model=os.getenv("RGPT_LLM_MODEL", "qwen2.5:7b"),
                          base_url=os.getenv("RGPT_OLLAMA_URL", "http://localhost:11434"))
    elif provider == "hosted":
        if req.generation_profile != "default":
            raise ValueError("bounded profile requires local Ollama")
        llm = HostedClient(model=os.environ["RGPT_LLM_MODEL"], base_url=os.environ["RGPT_LLM_BASE_URL"])
    else:
        raise ValueError("unknown LLM provider")
    return EvidencePipeline(LiteratureSource(), ChromaIndex(req.project_id, encoder=shared_encoder()), llm,
                            retrieval=req.retrieval, context_mode=req.context_mode,
                            representation_profile=req.representation_profile,
                            context_builder={"revised": revised_context, "table_aware_v1": table_aware_context}.get(req.context_mode))


def create_app(pipeline_factory=default_pipeline) -> FastAPI:
    app = FastAPI(title="ResearchGPT V2", version="0.1.0")
    jobs: dict[str, Job] = {}
    job_lock, execution_lock = threading.Lock(), threading.Lock()

    @app.get("/health")
    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "researchgpt-v2", "port": 8000,
                "inference_readiness": "not_probed", "job_storage": "process_local"}

    @app.post("/api/papers/discover", response_model=list[Paper])
    def discover(req: DiscoverRequest):
        if req.start_year > req.end_year:
            raise HTTPException(422, "start_year exceeds end_year")
        try:
            return LiteratureSource().discover(req.query, req.limit, (req.start_year, req.end_year))
        except Exception as exc:
            raise HTTPException(502, {"stage": "discovery", "code": type(exc).__name__}) from exc

    def validate_request(req):
        if (req.document_base64 is None) != (req.representation is None):
            raise HTTPException(422, "document_base64 and representation must be supplied together")
        if req.document_base64 is not None:
            try:
                data = base64.b64decode(req.document_base64, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise HTTPException(422, "invalid base64 document") from exc
            if len(data) > 40_000_000:
                raise HTTPException(413, "document exceeds 40 MB")
            return data
        return None

    def execute(req, data):
        with execution_lock:
            document = from_bytes(req.paper, data, req.representation) if data is not None else None
            if document is not None and document.paper.acquisition_status == "FAILED":
                return ExtractedPaper(paper_id=req.paper.paper_id, acquisition_status="FAILED", status="ACQUISITION_FAILED",
                    errors=[{"stage": "acquisition", "code": "document_not_validated"}])
            try:
                pipeline = pipeline_factory(req)
            except Exception as exc:
                raise HTTPException(503, {"stage": "configuration", "code": type(exc).__name__}) from exc
            return pipeline.run(req.paper, document)

    @app.post("/api/papers/process", response_model=ExtractedPaper)
    def process_paper(req: ProcessRequest):
        return execute(req, validate_request(req))

    def work(job_id, req, data):
        with job_lock:
            jobs[job_id] = jobs[job_id].model_copy(update={"status": "RUNNING"})
        try:
            result = execute(req, data)
            status = "FAILED" if result.status.endswith("FAILED") else (
                "COMPLETE" if result.status == "COMPLETE" else "PARTIAL")
            with job_lock:
                jobs[job_id] = jobs[job_id].model_copy(update={"status": status, "result": result})
        except Exception as exc:
            with job_lock:
                jobs[job_id] = jobs[job_id].model_copy(update={"status": "FAILED", "error": type(exc).__name__})

    @app.post("/api/jobs", response_model=Job, status_code=202)
    def start_job(req: ProcessRequest, background: BackgroundTasks):
        data = validate_request(req)
        job = Job(job_id=uuid.uuid4().hex, project_id=req.project_id)
        with job_lock:
            if len(jobs) >= 100:
                removable = next((j for j, value in jobs.items() if value.status not in ("QUEUED", "RUNNING")), None)
                if removable:
                    del jobs[removable]
                else:
                    raise HTTPException(429, "job queue is full")
            jobs[job.job_id] = job
        background.add_task(work, job.job_id, req, data)
        return job

    @app.get("/api/jobs/{job_id}", response_model=Job)
    def get_job(job_id: str):
        with job_lock:
            job = jobs.get(job_id)
        if job is None:
            raise HTTPException(404, "job not found")
        return job

    return app


app = create_app()
