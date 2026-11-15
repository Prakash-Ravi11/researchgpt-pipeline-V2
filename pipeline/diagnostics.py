"""Explicit per-fact survival; absent observations stay unknown, never pass."""
STAGES = ("acquisition", "representation", "parsing", "chunking", "retrieval", "context", "extraction", "verification")


def earliest_loss(observations: dict[str, bool | None]) -> dict:
    unknown = []
    for stage in STAGES:
        survived = observations.get(stage)
        if survived is None:
            unknown.append(stage)
        elif not survived:
            return {"earliest_confirmed_loss": stage, "unknown_prior_stages": unknown,
                    "causal_earliest_established": not unknown, "observations": observations}
    return {"earliest_confirmed_loss": None, "unknown_prior_stages": unknown,
            "causal_earliest_established": not unknown, "observations": observations}


def trace_fact(fact, document, parsed, chunks, retrieved, context, extracted: bool | None = None,
               verified: bool | None = None):
    quote = fact["quote"]
    return earliest_loss({
        "acquisition": document.paper.acquisition_status == "FULL_TEXT" and document.data is not None,
        "representation": parsed["representation"] in ("pdf", "jats_xml", "latex"),
        "parsing": any(quote in b["text"] for b in parsed["blocks"]),
        "chunking": any(quote in c.text for c in chunks),
        "retrieval": any(quote in c.text for c in retrieved),
        "context": quote in context.text,
        "extraction": extracted,
        "verification": verified,
    })
