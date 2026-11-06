import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from pipeline.service import EvidencePipeline
from pipeline.retrieval.index import ChromaIndex
from tests.helpers import fixture_document, TinyEncoder, QuotedFixtureLLM

pytestmark = pytest.mark.integration


def test_health_schema_and_fixture_job(tmp_path):
    document = fixture_document()
    class FixtureSource:
        def acquire(self, paper):
            return document
    def factory(req):
        return EvidencePipeline(FixtureSource(), ChromaIndex(req.project_id, tmp_path / "db", TinyEncoder()), QuotedFixtureLLM())
    with TestClient(create_app(factory)) as client:
        assert client.get("/health").json()["inference_readiness"] == "not_probed"
        req = {"project_id": "fixture", "paper": {"paper_id": "SYN"}}
        response = client.post("/api/papers/process", json=req)
        assert response.status_code == 200
        assert response.json()["fields"]["results"][0]["status"] == "VERIFIED"
        queued = client.post("/api/jobs", json=req)
        assert queued.status_code == 202
        job = client.get("/api/jobs/" + queued.json()["job_id"]).json()
        assert job["status"] == "PARTIAL" and job["result"]["paper_id"] == "SYN"
        assert client.get("/api/jobs/missing").status_code == 404
        assert client.post("/api/papers/process", json={**req, "document_base64": "invalid"}).status_code == 422
        assert client.post("/api/papers/process", json={**req, "retrieval": "unknown"}).status_code == 422


def test_bad_configuration_and_failed_jobs_are_explicit():
    def unavailable(req):
        raise ImportError("missing optional dependency")
    client = TestClient(create_app(unavailable))
    req = {"project_id": "x", "paper": {"paper_id": "x"}}
    assert client.post("/api/papers/process", json=req).status_code == 503
    job_id = client.post("/api/jobs", json=req).json()["job_id"]
    assert client.get("/api/jobs/" + job_id).json()["status"] == "FAILED"
