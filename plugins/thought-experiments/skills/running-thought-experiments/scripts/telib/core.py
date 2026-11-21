"""Pure functions over te data: upcast, fold, score. No file or network access.

State is a plain dict built by folding the event log in id order. Events are never edited:
`correction` events overlay new field values onto their target, `supersede` events (and
`frame.supersedes`) take their target out of the current state. The raw log stays as written.
"""

from __future__ import annotations

import copy
from typing import Any

CURRENT_VERSION = 1
VERDICT_KINDS = ("probe", "operation", "attack")


def upcast(event: dict) -> dict:
    """Bring an event to CURRENT_VERSION. Version 1 is the first, so this is the identity;
    later versions add a step here, never by rewriting stored events."""
    v = event.get("v")
    if v == CURRENT_VERSION:
        return event
    raise ValueError(f"event {event.get('id')}: unsupported schema version {v!r}")


def fold(events: list[dict], experiment: dict | None = None) -> dict:
    """Event log -> current state."""
    events = [upcast(e) for e in events]
    by_id = {e["id"]: e for e in events}

    superseded: set[int] = set()
    replaced: dict[int, dict] = {}
    corrections: dict[str, list[dict]] = {}
    for e in events:
        if e["kind"] == "supersede":
            superseded.add(e["target"])
        if e["kind"] in ("frame", "conclusion") and "supersedes" in e:
            superseded.add(e["supersedes"])
        if e["kind"] == "correction":
            t = e["target"]
            key = f"event:{t['event']}" if "event" in t else f"source:{t['source']}"
            corrections.setdefault(key, []).append(e)
            if "event" in t and isinstance(e.get("replace"), dict):
                replaced.setdefault(t["event"], {}).update(e["replace"])

    def effective(e: dict) -> dict:
        if e["id"] in replaced:
            e = copy.deepcopy(e)
            e.update(replaced[e["id"]])
        return e

    active = [effective(e) for e in events if e["id"] not in superseded]
    of = lambda kind: [e for e in active if e["kind"] == kind]  # noqa: E731

    rivals: dict[str, dict] = {}
    for e in of("rival"):
        rivals[e["rid"]] = {"rid": e["rid"], "text": e["text"], "is_opposite": e.get("is_opposite", False),
                            "would_reject_if": e.get("would_reject_if", ""), "event": e["id"],
                            "status": "open", "verdicts": [], "holder": None}
    for e in of("holder"):
        if e["rival"] in rivals:
            rivals[e["rival"]]["holder"] = e
    for e in active:
        if e["kind"] in VERDICT_KINDS:
            for rid, v in e.get("verdicts", {}).items():
                if rid in rivals:
                    rivals[rid]["verdicts"].append({"event": e["id"], **v})
                    if v["status"] != "unchanged":
                        rivals[rid]["status"] = v["status"]

    conclusions = of("conclusion")
    frames = of("frame")
    closes = of("close")
    return {
        "experiment": experiment or {},
        "events": active,
        "all_events": events,
        "by_id": by_id,
        "superseded": sorted(superseded),
        "corrections": corrections,
        "frame": frames[-1] if frames else None,
        "frames": frames,
        "rivals": rivals,
        "prior_answers": of("prior_answer"),
        "holders": of("holder"),
        "predictions": of("prediction"),
        "probes": of("probe"),
        "operations": of("operation"),
        "attacks": of("attack"),
        "conclusion": conclusions[-1] if conclusions else None,
        "reviews": of("review"),
        "decisions": of("decision"),
        "branches": of("branch"),
        "closed": closes[-1]["state"] if closes else None,
    }


def surviving(state: dict) -> list[str]:
    return [rid for rid, r in state["rivals"].items() if r["status"] != "eliminated"]


def score(state: dict) -> dict | None:
    """Multi-class Brier score of the first prediction against the adopted rival.

    Brier = sum over rivals of (p_i - o_i)^2, where o_i is 1 for the adopted rival and 0 for the
    others: 0 is a perfect forecast, 2 the worst. Returns None when there is no prediction or
    the conclusion adopts no rival, because there is then nothing to score against."""
    if not state["predictions"] or not state["conclusion"]:
        return None
    answer = state["conclusion"].get("answer_rival")
    if not answer:
        return None
    pred = state["predictions"][0]
    dist = pred["distribution"]
    rids = sorted(set(dist) | set(state["rivals"]))
    brier = sum((dist.get(r, 0.0) - (1.0 if r == answer else 0.0)) ** 2 for r in rids)
    return {"prediction": pred["id"], "answer_rival": answer, "brier": round(brier, 4),
            "p_answer": round(dist.get(answer, 0.0), 4), "by_whom": pred.get("by_whom")}


def attacked_rivals(state: dict) -> list[str]:
    return [rid for rid, r in state["rivals"].items()
            if any(v["status"] in ("eliminated", "weakened") for v in r["verdicts"])]


def as_jsonable(state: dict) -> dict[str, Any]:
    """State without the raw event index, for --json output."""
    return {k: v for k, v in state.items() if k not in ("by_id", "all_events")}
