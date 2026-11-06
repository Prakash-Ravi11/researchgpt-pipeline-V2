"""Local Ollama and hosted compatible chat adapters with actual usage counters."""
from __future__ import annotations

import json
import os
import re
import time

import requests

from shared.schemas import LLMResponse
from pipeline.extraction.prompt import FIELDS


def extraction_schema(user: str) -> dict:
    """Constrain complete source IDs; never repair shorthand IDs after generation.

    Ollama accepts a JSON Schema in format (official structured-outputs docs).
    Evidence wording still needs host verification; schema compliance is not truth.
    """
    ids = sorted(set(re.findall(r"^\[([^\]\n]+)\]\s*$", user, re.M)))
    if not ids:
        raise ValueError("extraction context has no source IDs")
    tuple_schema = {"type": "object", "properties": {
        k: {"type": "string"} for k in ("subject", "dataset", "metric", "value")}}
    tuple_schema["properties"]["setting"] = {"type": ["string", "null"]}
    tuple_schema.update(required=["subject", "dataset", "metric", "value", "setting"], additionalProperties=False)
    candidate = {"type": "object", "properties": {"value": {"type": "string"},
        "evidence_span": {"type": "string", "description": "Verbatim source text, never an ID or citation"},
        "chunk_id": {"type": "string", "enum": ids}, "scientific_tuple": tuple_schema},
        "required": ["value", "evidence_span", "chunk_id"], "additionalProperties": False}
    return {"type": "object", "properties": {f: {"type": "array", "items": candidate} for f in FIELDS},
            "required": list(FIELDS), "additionalProperties": False}


def parse_object(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    result = json.loads(text)
    if not isinstance(result, dict):
        raise ValueError("model output is not a JSON object")
    return result


class OllamaClient:
    def __init__(self, model: str = "qwen2.5:7b", base_url: str = "http://localhost:11434",
                 num_ctx: int = 8192, output_tokens: int = 768, timeout: float = 120, observer=None):
        self.model, self.base_url, self.num_ctx = model, base_url.rstrip("/"), num_ctx
        self.output_tokens, self.timeout = output_tokens, timeout
        self.observer = observer

    def complete(self, system: str, user: str) -> LLMResponse:
        started = time.perf_counter()
        payload = {"model": self.model, "stream": False,
            "format": extraction_schema(user), "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "options": {"temperature": 0, "seed": 42, "num_ctx": self.num_ctx, "num_predict": self.output_tokens}}
        if self.observer:
            self.observer("request", payload)
        r = requests.post(self.base_url + "/api/chat", json=payload, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        if self.observer:
            self.observer("response", data)
        if not data.get("done") or data.get("done_reason") == "length":
            raise ValueError("incomplete model output")
        return LLMResponse(content=parse_object(data["message"]["content"]), provider="ollama", model=self.model,
            prompt_tokens=data.get("prompt_eval_count"), completion_tokens=data.get("eval_count"),
            finish_reason=data.get("done_reason"), latency_ms=(time.perf_counter() - started) * 1000)


class HostedClient:
    def __init__(self, model: str, base_url: str, key_env: str = "LLM_API_KEY", output_tokens: int = 768):
        self.model, self.base_url, self.key_env, self.output_tokens = model, base_url.rstrip("/"), key_env, output_tokens

    def complete(self, system: str, user: str) -> LLMResponse:
        key = os.environ.get(self.key_env)
        if not key:
            raise RuntimeError(f"missing hosted credential environment variable {self.key_env}")
        started = time.perf_counter()
        r = requests.post(self.base_url + "/chat/completions", headers={"Authorization": f"Bearer {key}"},
            json={"model": self.model, "temperature": 0, "max_tokens": self.output_tokens,
                  "response_format": {"type": "json_object"},
                  "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}, timeout=120)
        r.raise_for_status()
        data = r.json()
        choice = data["choices"][0]
        if choice.get("finish_reason") != "stop":
            raise ValueError("incomplete hosted model output")
        return LLMResponse(content=parse_object(choice["message"]["content"]), provider="hosted", model=self.model,
            prompt_tokens=data.get("usage", {}).get("prompt_tokens"), completion_tokens=data.get("usage", {}).get("completion_tokens"),
            finish_reason=choice.get("finish_reason"), latency_ms=(time.perf_counter() - started) * 1000)
