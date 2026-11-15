"""Frozen synthetic tuple scoring. Does not infer annotations from model output."""
def tuple_key(tup):
    return tuple(str(tup.get(k) or "").strip().casefold() for k in ("subject", "dataset", "metric", "value", "setting"))


def score_tuples(expected: list[dict], predicted: list[dict]):
    gold = {tuple_key(t) for t in expected}
    output = {tuple_key(t) for t in predicted}
    tp, fp, fn = len(gold & output), len(output - gold), len(gold - output)
    return {"correct_complete_tuples": tp, "false_positive_tuples": fp, "missed_tuples": fn,
            "tuple_precision": tp / (tp + fp) if tp + fp else None,
            "tuple_recall": tp / (tp + fn) if tp + fn else None,
            "unsupported_claim_rate": fp / len(output) if output else None}
