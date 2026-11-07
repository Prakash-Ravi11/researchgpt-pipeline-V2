"""Named opt-in local generation settings; production defaults stay in the client."""
from pipeline.extraction.clients import OllamaClient


def local_client(profile: str = "default", **kwargs) -> OllamaClient:
    if profile not in ("default", "bounded"):
        raise ValueError("unknown generation profile")
    if profile == "bounded":
        protected = {"num_ctx": 8192, "output_tokens": 2048, "max_candidates_per_field": 1}
        if set(protected) & set(kwargs):
            raise ValueError("named profile settings cannot be overridden")
        kwargs.update(protected)
        kwargs.setdefault("timeout", 180)
    client = OllamaClient(**kwargs)
    client.generation_profile = profile
    return client
