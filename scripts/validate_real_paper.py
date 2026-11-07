"""Measured one-paper real BGE/Chroma/Qwen execution in a fresh database.

Raw requests, responses, metadata and resource samples remain in ignored outputs.
No fixture encoder, replay response or verifier relaxation is used.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
import traceback
import weakref
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import psutil
import requests
import torch

from shared.schemas import Paper, ExtractedPaper
from pipeline.acquisition.source import from_bytes
from pipeline.extraction.clients import OllamaClient
from pipeline.extraction.context import current_context, revised_context
from pipeline.parsing.documents import process
from pipeline.retrieval.index import BGEEncoder, ChromaIndex, MODEL, MODEL_REVISION
from pipeline.service import EvidencePipeline


def save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def gpu_state():
    r = subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version,memory.total,memory.used,memory.free", "--format=csv,noheader,nounits"],
                       capture_output=True, text=True, timeout=10)
    if r.returncode:
        return {"error": r.stderr, "returncode": r.returncode}
    name, driver, total, used, free = next(csv.reader(r.stdout.splitlines(), skipinitialspace=True))
    return {"name": name, "driver": driver, "total_mib": int(total), "used_mib": int(used), "free_mib": int(free)}


def snapshot(label):
    try:
        models = requests.get("http://localhost:11434/api/ps", timeout=5).json().get("models", [])
    except Exception as exc:
        models = {"error": type(exc).__name__}
    mem = psutil.Process().memory_info()
    host = psutil.virtual_memory()
    return {"label": label, "utc": datetime.now(timezone.utc).isoformat(), "gpu": gpu_state(),
            "process_rss_bytes": mem.rss, "process_peak_wset_bytes": getattr(mem, "peak_wset", None),
            "host_available_bytes": host.available, "host_total_bytes": host.total,
            "ollama_models": models,
            "torch_allocated_bytes": torch.cuda.memory_allocated() if torch.cuda.is_available() else None,
            "torch_reserved_bytes": torch.cuda.memory_reserved() if torch.cuda.is_available() else None}


class Monitor:
    def __init__(self, folder):
        self.folder, self.samples, self.stop_event = folder, [], threading.Event()
        self.thread = threading.Thread(target=self.loop, daemon=True)
    def loop(self):
        with (self.folder / "resource_samples.jsonl").open("w", encoding="utf-8") as f:
            while not self.stop_event.is_set():
                sample = snapshot("periodic")
                self.samples.append(sample)
                f.write(json.dumps(sample) + "\n"); f.flush()
                self.stop_event.wait(1)
    def stop(self):
        self.stop_event.set(); self.thread.join(timeout=15)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", choices=["cuda", "cpu"], default="cuda")
    parser.add_argument("--context", choices=["current", "revised"], default="current")
    parser.add_argument("--output-tokens", type=int, default=768)
    parser.add_argument("--cpu-check", action="store_true", help="two genuine CPU embeddings while Qwen remains resident")
    parser.add_argument("--max-candidates", type=int, default=None)
    args = parser.parse_args()
    if Path(sys.prefix).resolve() != (Path.cwd() / ".venv-gpu").resolve():
        raise RuntimeError("run this validation with the exact V2 .venv-gpu interpreter")
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    report = {"interpreter": sys.executable, "python": sys.version, "device": args.device,
        "torch": torch.__version__, "torch_cuda_build": torch.version.cuda, "cuda_available": torch.cuda.is_available(),
        "model": MODEL, "model_revision": MODEL_REVISION, "embedding_max_seq_length": 1024,
        "mock_embeddings": False, "mock_llm": False, "independent_human_annotations": False,
        "snapshots": [], "encode_calls": [], "queries": []}
    frozen_probes = Path("outputs/recovery/expected_source_facts.json").read_bytes()
    source_facts = json.loads(frozen_probes)
    report["expected_source_probes_sha256"] = hashlib.sha256(frozen_probes).hexdigest()
    report["snapshots"].append(snapshot("before_any_model_load"))
    save(args.output / "execution.json", report)
    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable; run explicit --device cpu for a separately labeled fallback")
    if args.device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    # Unload only this task's Qwen model, and verify Ollama's separate ownership.
    initial = report["snapshots"][0]["ollama_models"]
    if isinstance(initial, list) and any(m.get("name") == "qwen2.5:7b" for m in initial):
        requests.post("http://localhost:11434/api/generate", json={"model": "qwen2.5:7b", "keep_alive": 0}, timeout=30).raise_for_status()
    report["snapshots"].append(snapshot("before_bge_load_after_qwen_unload"))
    paper = Paper.model_validate_json(Path("data/live/paper.json").read_text())
    data = Path("data/live/document.pdf").read_bytes()
    if hashlib.sha256(data).hexdigest() != paper.document_sha256:
        raise ValueError("validated cache hash mismatch")
    acq_started = time.perf_counter()
    document = from_bytes(paper, data, "pdf", getattr(paper, "pdf_source", "arxiv"))
    report["acquisition_ms"] = (time.perf_counter() - acq_started) * 1000
    parsed, chunks = process(document)
    save(args.output / "paper.json", document.paper.model_dump(mode="json"))
    save(args.output / "parsed_document.json", parsed)
    save(args.output / "chunks.json", [c.model_dump(mode="json") for c in chunks])
    report.update(paper_id=paper.paper_id, document_sha256=paper.document_sha256, chunk_count=len(chunks),
                  stable_chunk_ids=chunks == process(document)[1], acquisition_status=document.paper.acquisition_status)

    class Encoder(BGEEncoder):
        model_ref = None
        def encode(self, texts):
            t = time.perf_counter()
            if self._model is None:
                report["snapshots"].append(snapshot("immediately_before_bge_loading"))
            model = self.model
            self.model_ref = weakref.ref(model)
            if "embedding_token_lengths" not in report:
                lengths = [len(ids) for ids in model.tokenizer(texts, truncation=False)["input_ids"]]
                report["embedding_token_lengths"] = {"tokenizer": MODEL, "min": min(lengths), "max": max(lengths),
                    "p50": float(np.percentile(lengths, 50)), "p95": float(np.percentile(lengths, 95)),
                    "over_max_seq_length": sum(n > 1024 for n in lengths), "all": lengths}
            del model
            try:
                vectors = super().encode(texts)
            except BaseException:
                (args.output / "embedding_error.txt").write_text(traceback.format_exc(), encoding="utf-8")
                raise
            arr = np.asarray(vectors, dtype=np.float32)
            norms = np.linalg.norm(arr, axis=1)
            if arr.shape != (len(texts), 1024) or not np.isfinite(arr).all() or not np.allclose(norms, 1, atol=.005):
                raise ValueError("invalid actual embedding shape/values/norms")
            report["encode_calls"].append({"count": len(texts), "shape": list(arr.shape),
                "finite": True, "norm_min": float(norms.min()), "norm_max": float(norms.max()),
                "sha256_float32": hashlib.sha256(arr.tobytes()).hexdigest(), "milliseconds": (time.perf_counter()-t)*1000})
            return vectors
        def release(self):
            result = super().release()
            result["model_weakref_gone"] = self.model_ref is None or self.model_ref() is None
            report["snapshots"].append(snapshot("after_bge_release"))
            report["release"] = result
            return result

    class Index(ChromaIndex):
        def replace_paper(self, pid, cs):
            assert self.collection.count() == 0, "smoke must start with an empty unique collection"
            super().replace_paper(pid, cs)
            assert self.all_chunks(pid) == cs, "stored IDs or provenance changed"
            stored = self.collection.get(include=["metadatas", "documents", "embeddings"])
            assert set(stored["ids"]) == {c.chunk_id for c in cs}
            report["index"] = {"collection": self.collection.name, "database": str((args.output / "fresh-chroma").resolve()),
                "initial_count": 0, "count": self.collection.count(), "ids_verified": True,
                "metadata_roundtrip_verified": True, "stored_vector_shape": list(np.asarray(stored["embeddings"]).shape),
                "configuration": self.collection.metadata}
            save(args.output / "index_payload.json", {k: v for k,v in stored.items() if k != "embeddings"})
            neighbor = ChromaIndex("isolation-control-" + args.output.name, args.output / "fresh-chroma", self.encoder)
            assert neighbor.collection.count() == 0
            report["index"]["separate_collection_empty"] = True
            report["index"]["isolation_control_collection"] = neighbor.collection.name
        def search(self, query, pid, n=50):
            found = super().search(query, pid, n)
            report["queries"].append({"query": query, "paper_id": pid, "requested_hits": n,
                "ids": [c.chunk_id for c in found], "actual_embedding_model": MODEL})
            return found

    encoder = Encoder(args.device)
    index = Index("recovery-" + args.output.name, args.output / "fresh-chroma", encoder)
    captured = {}
    def context_builder(cs):
        context = current_context(cs) if args.context == "current" else revised_context(cs)
        captured.update(retrieved=cs, context=context)
        save(args.output / "context.json", {"text": context.text, "trace": context.trace,
            "delivered_chunks": [c.model_dump(mode="json") for c in context.chunks]})
        return context
    def observe(event, payload):
        save(args.output / ("ollama_" + event + ".json"), payload)
        if event == "request":
            assert encoder._model is None, "BGE must be released before Qwen"
            report["snapshots"].append(snapshot("immediately_before_qwen_request"))
        else:
            report["snapshots"].append(snapshot("after_qwen_response"))
    llm = OllamaClient(output_tokens=args.output_tokens, timeout=180, observer=observe,
                       max_candidates_per_field=args.max_candidates)
    monitor = Monitor(args.output); monitor.thread.start()
    try:
        result = EvidencePipeline(None, index, llm, context_mode=args.context, context_builder=context_builder).run(document.paper, document)
        save(args.output / "structured_output.json", result.model_dump(mode="json"))
        assert ExtractedPaper.model_validate_json(result.model_dump_json()) == result
        report["status"] = result.status
        report["errors"] = result.errors
        report["stage_trace"] = result.trace
        report["candidate_verdicts"] = {f: [v.model_dump(mode="json") for v in vs] for f,vs in result.fields.items()}
        report["verified_numeric_tuples"] = [v.model_dump(mode="json") for vs in result.fields.values() for v in vs
            if v.final == "RETURNED" and getattr(v, "scientific_tuple", None)]
        report["runtime_recovered"] = bool(report.get("index", {}).get("count") == len(chunks) and report["queries"])
        report["integration_completed"] = result.status in ("COMPLETE", "PARTIAL", "ABSTAINED")
        # Source-checked probes frozen independently of model output. They are
        # not human-independent gold and never fed into the extraction prompt.
        probes = []
        for fact in source_facts["facts"]:
            value, task = fact["value"], fact["dataset"]
            has = lambda text: bool(re.search(r"(?<![\d.])" + re.escape(value) + r"(?![\d.])", text))
            cs = [c for c in chunks if has(c.text)]
            probes.append({"value": value, "metric": "BLEU", "source_task": task, "annotation_status": "source-checked agent probe; not independently human validated",
                "parsed_locations": [{"block_id": b["block_id"], "page_or_node": b["page_or_node"], "text": b["text"],
                                      "table_parse_status": b.get("table_parse_status"), "table_fallback": b.get("table_fallback")} for b in parsed["blocks"] if has(b["text"])],
                "chunk_ids": [c.chunk_id for c in cs],
                "retrieved_ids": [c.chunk_id for c in captured.get("retrieved", []) if has(c.text)],
                "context_ids": [c.chunk_id for c in captured["context"].chunks if has(c.text)] if "context" in captured else [],
                "complete_matching_cells": [cell for c in chunks for cell in c.table_cells if has(str(cell.get("value", "")))]})
        save(args.output / "expected_fact_trace.json", probes)
        report["expected_fact_trace_file"] = "expected_fact_trace.json"
        if args.cpu_check:
            before_cpu = snapshot("before_cpu_bge_with_qwen_resident")
            report["snapshots"].append(before_cpu)
            if psutil.virtual_memory().available < 4_000_000_000:
                report["cpu_check"] = {"status": "UNAVAILABLE", "reason": "less_than_4GB_available_host_memory"}
            else:
                cpu = BGEEncoder("cpu")
                cpu_started = time.perf_counter()
                cpu_vectors = np.asarray(cpu.encode([chunks[0].text, chunks[-1].text]), dtype=np.float32)
                cpu_device = str(next(cpu.model.parameters()).device)
                assert cpu_device == "cpu" and cpu_vectors.shape == (2, 1024) and np.isfinite(cpu_vectors).all()
                report["cpu_check"] = {"status": "EXECUTED", "device": cpu_device, "shape": list(cpu_vectors.shape),
                    "finite": True, "milliseconds": (time.perf_counter() - cpu_started)*1000,
                    "norms": np.linalg.norm(cpu_vectors, axis=1).tolist(),
                    "ollama_size_vram_before_bytes": sum(m.get("size_vram",0) for m in before_cpu["ollama_models"] if isinstance(before_cpu["ollama_models"],list)),
                    "scope": "two genuine CPU embeddings, not full-paper CPU end-to-end"}
                cpu.release()
                report["snapshots"].append(snapshot("after_cpu_bge_release_qwen_still_resident"))
    except BaseException:
        (args.output / "unhandled_error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        raise
    finally:
        if encoder._model is not None:
            encoder.release()
        report["torch_peak_allocated_bytes"] = torch.cuda.max_memory_allocated() if torch.cuda.is_available() else None
        report["torch_peak_reserved_bytes"] = torch.cuda.max_memory_reserved() if torch.cuda.is_available() else None
        requests.post("http://localhost:11434/api/generate", json={"model": "qwen2.5:7b", "keep_alive": 0}, timeout=30).raise_for_status()
        report["snapshots"].append(snapshot("after_qwen_unload"))
        monitor.stop()
        report["sampled_global_gpu_peak_used_mib"] = max((s["gpu"].get("used_mib", 0) for s in monitor.samples), default=None)
        report["sampled_ollama_peak_size_vram_bytes"] = max((m.get("size_vram", 0) for s in monitor.samples for m in s["ollama_models"] if isinstance(s["ollama_models"], list)), default=None)
        report["total_seconds"] = time.perf_counter() - started
        save(args.output / "execution.json", report)
    print(json.dumps({k: report.get(k) for k in ["interpreter", "device", "status", "errors", "runtime_recovered", "integration_completed", "chunk_count", "index", "release", "total_seconds"]}, indent=2))
    if not report["integration_completed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
