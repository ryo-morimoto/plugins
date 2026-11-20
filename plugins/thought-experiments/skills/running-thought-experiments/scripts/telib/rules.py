"""Predicates named by data/rules.toml, and the two functions that evaluate them.

Every predicate is pure. It receives a context dict built by the I/O layer:
  state    folded state (core.fold)
  sources  {source id: record from sources.toml}
  files    {repo-relative path inside the experiment: sha256} for briefs/ and outputs/
  rerun    None when scripts were not re-run, else a list of mismatch messages
Stage predicates return a list of unmet details (empty = met). Invariants and warnings return
a list of violation messages (empty = holds).
"""

from __future__ import annotations

from typing import Callable

from . import core

Ctx = dict


# ---------- stage predicates ----------

def _events(ctx: Ctx, kind: str) -> list[dict]:
    return [e for e in ctx["state"]["events"] if e["kind"] == kind]


def p_has(ctx: Ctx, kind: str, **_) -> list[str]:
    return [] if _events(ctx, kind) else [f"no {kind} event"]


def p_count(ctx: Ctx, kind: str, min: int, **_) -> list[str]:  # noqa: A002
    n = len(_events(ctx, kind))
    return [] if n >= min else [f"{n} {kind} event(s), need {min}"]


def p_any(ctx: Ctx, kind: str, field: str, equals, **_) -> list[str]:
    return [] if any(e.get(field) == equals for e in _events(ctx, kind)) else [f"no {kind} with {field} = {equals!r}"]


def _obtained(ctx: Ctx, sid: str) -> bool:
    src = ctx["sources"].get(sid)
    return bool(src) and src.get("obtained") in ("fetch", "user") and bool(src.get("sha256"))


def p_prior_answer_evidence(ctx: Ctx, **_) -> list[str]:
    events = _events(ctx, "prior_answer")
    if not events:
        return ["no prior_answer event"]
    for e in events:
        if e.get("sources") and all(_obtained(ctx, s) for s in e["sources"]):
            return []
        if e.get("searched") and e.get("found") is False:
            return []
    return ["prior_answer needs sources obtained with te source add (sha256), or searched queries with found = false"]


def _artifact_ok(ctx: Ctx, art: dict | None) -> bool:
    return bool(art) and ctx["files"].get(art["file"]) == art["sha256"]


def p_fresh_attack_with_artifacts(ctx: Ctx, **_) -> list[str]:
    """A fresh attack with matching files, or a self attack the user explicitly accepted
    (a decision event by the user with accepts = the attack's id), for hosts without subagents."""
    accepted = {e["accepts"] for e in _events(ctx, "decision") if e["author"] == "user" and "accepts" in e}
    for e in _events(ctx, "attack"):
        if e["reviewer"] == "fresh" and _artifact_ok(ctx, e.get("brief")) and _artifact_ok(ctx, e.get("response")):
            return []
        if e["reviewer"] == "self" and e["id"] in accepted:
            return []
    return ["no attack by a fresh reviewer whose brief and response files match their sha256 (or a self attack the user accepted)"]


def p_objections_answered(ctx: Ctx, **_) -> list[str]:
    out = []
    for e in _events(ctx, "attack"):
        for i, o in enumerate(e["objections"]):
            lacks = [f for f in ("response", "reason") if not o.get(f)]
            if lacks:
                out.append(f"event {e['id']} objection {i + 1} has no {' or '.join(lacks)}")
    return out


def p_user_chose(ctx: Ctx, **_) -> list[str]:
    c = ctx["state"]["conclusion"]
    if not c:
        return ["no conclusion yet"]
    if any(e["author"] == "user" and e["id"] > c["id"] for e in _events(ctx, "decision")):
        return []
    return [f"no decision by the user after conclusion event {c['id']}"]


# ---------- invariants ----------

def i_refs_exist(ctx: Ctx, **_) -> list[str]:
    st = ctx["state"]
    out: list[str] = []
    rids = set(st["rivals"])
    ids = {e["id"] for e in st["all_events"]}
    for e in st["all_events"]:
        where = f"event {e['id']} ({e['kind']})"
        if e["kind"] == "holder" and e["rival"] not in rids:
            out.append(f"{where}: unknown rival {e['rival']!r}")
        if e["kind"] == "prediction":
            out += [f"{where}: unknown rival {r!r}" for r in e["distribution"] if r not in rids]
        for rid in e.get("verdicts", {}):
            if rid not in rids:
                out.append(f"{where}: verdict for unknown rival {rid!r}")
        if e["kind"] == "conclusion":
            ar = e.get("answer_rival")
            if ar and ar not in rids:
                out.append(f"{where}: answer_rival {ar!r} is not a rival")
            for p in e["premises"]:
                for c in p.get("citations", []):
                    for sid in [c["source"], c.get("primary_of")]:
                        if sid and sid not in ctx["sources"]:
                            out.append(f"{where}: premise {p['pid']} cites unknown source {sid!r}")
                for f in p.get("outputs", []):
                    if f not in ctx["files"]:
                        out.append(f"{where}: premise {p['pid']} cites missing {f}")
        for item in e.get("sources", []) if isinstance(e.get("sources"), list) else []:
            for sid in ([item] if isinstance(item, str) else [item["source"], item.get("primary_of")]):
                if sid and sid not in ctx["sources"]:
                    out.append(f"{where}: unknown source {sid!r}")
        for f in e.get("outputs", []):
            if f not in ctx["files"]:
                out.append(f"{where}: missing {f}")
        if e["kind"] == "decision" and "accepts" in e and e["accepts"] not in ids:
            out.append(f"{where}: accepts event {e['accepts']} which does not exist")
        if e["kind"] == "supersede" and e["target"] not in ids:
            out.append(f"{where}: target event {e['target']} does not exist")
        if e["kind"] in ("frame", "conclusion") and "supersedes" in e and e["supersedes"] not in ids:
            out.append(f"{where}: supersedes event {e['supersedes']} which does not exist")
        if e["kind"] == "correction":
            t = e["target"]
            if "event" in t and t["event"] not in ids:
                out.append(f"{where}: target event {t['event']} does not exist")
            if "source" in t and t["source"] not in ctx["sources"]:
                out.append(f"{where}: target source {t['source']!r} does not exist")
        if e["kind"] == "attack":
            for o in e["objections"]:
                if "ref" in o and o["ref"] not in ids:
                    out.append(f"{where}: objection refers to missing event {o['ref']}")
    return out


def _premises(ctx: Ctx) -> list[dict]:
    c = ctx["state"]["conclusion"]
    return c["premises"] if c else []


def i_checked_needs_primary(ctx: Ctx, **_) -> list[str]:
    out = []
    for p in _premises(ctx):
        if p["label"] != "empirical-checked":
            continue
        cits = p.get("citations", [])
        if not cits:
            # An absence ("no such record exists") is checked by searching, not by citing.
            if not p.get("searched"):
                out.append(f"premise {p['pid']}: empirical-checked without citations (for an absence, record the searches in searched)")
            continue
        for c in cits:
            if c["level"] == "primary":
                if not _obtained(ctx, c["source"]):
                    out.append(f"premise {p['pid']}: primary source {c['source']!r} has no sha256 or was not obtained")
            else:
                po = c.get("primary_of")
                if not po:
                    out.append(f"premise {p['pid']}: secondary source {c['source']!r} without primary_of")
                elif not _obtained(ctx, po):
                    out.append(f"premise {p['pid']}: primary_of {po!r} has no sha256 or was not obtained")
    return out


def i_unobtainable_is_unverified(ctx: Ctx, **_) -> list[str]:
    out = []
    for p in _premises(ctx):
        if p["label"] != "empirical-checked":
            continue
        for c in p.get("citations", []):
            src = ctx["sources"].get(c["source"], {})
            if src.get("obtained") == "none":
                out.append(f"premise {p['pid']}: cites {c['source']!r}, which could not be obtained")
    return out


def i_no_post_hoc_prediction(ctx: Ctx, **_) -> list[str]:
    st = ctx["state"]
    ops = st["operations"]
    if not ops:
        return []
    first = min(e["id"] for e in ops)
    return [f"prediction event {e['id']} comes after the first operation (event {first})"
            for e in st["predictions"] if e["id"] > first]


def i_prediction_sums_to_one(ctx: Ctx, **_) -> list[str]:
    return [f"prediction event {e['id']} sums to {sum(e['distribution'].values()):.4f}"
            for e in ctx["state"]["predictions"] if abs(sum(e["distribution"].values()) - 1.0) > 1e-6]


def i_eliminate_needs_holder(ctx: Ctx, **_) -> list[str]:
    st = ctx["state"]
    out = []
    for rid in core.attacked_rivals(st):
        h = st["rivals"][rid]["holder"]
        if h is None:
            out.append(f"rival {rid} is weakened or eliminated but has no holder event")
        elif not h.get("strawman") and not (h.get("sources") and all(_obtained(ctx, s) for s in h["sources"])):
            out.append(f"rival {rid}: holder cites no obtained source and is not flagged as a strawman")
    return out


def i_answer_rival_survives(ctx: Ctx, **_) -> list[str]:
    c = ctx["state"]["conclusion"]
    if not c or not c.get("answer_rival"):
        return []
    r = ctx["state"]["rivals"].get(c["answer_rival"])
    return [f"answer_rival {c['answer_rival']} is eliminated"] if r and r["status"] == "eliminated" else []


def i_artifacts_match(ctx: Ctx, **_) -> list[str]:
    out = []
    for e in _events(ctx, "attack"):
        for key in ("brief", "response"):
            art = e.get(key)
            if art and not _artifact_ok(ctx, art):
                got = ctx["files"].get(art["file"])
                out.append(f"event {e['id']}: {key} {art['file']} " + ("is missing" if got is None else "does not match its sha256"))
    return out


def i_outputs_reproduce(ctx: Ctx, **_) -> list[str]:
    return list(ctx["rerun"] or [])


# ---------- warnings ----------

def w_one_variable(ctx: Ctx, **_) -> list[str]:
    return [f"operation event {e['id']} varies {len(e['varied'])} conditions"
            for e in ctx["state"]["operations"] if len(e["varied"]) > 1]


def w_diagnostic(ctx: Ctx, **_) -> list[str]:
    return [f"operation event {e['id']} changed no rival's status"
            for e in ctx["state"]["operations"]
            if all(v["status"] == "unchanged" for v in e["verdicts"].values())]


def w_operation_secondhand(ctx: Ctx, **_) -> list[str]:
    """Operations feed numbers into results, so a secondhand value there breaks the result
    even when no premise cites it. Found by migrating a real record: a value taken from a
    secondary document whose primary was never obtained drove two operations."""
    out = []
    for e in ctx["state"]["probes"] + ctx["state"]["operations"]:
        for item in e.get("sources", []):
            if isinstance(item, dict) and item["level"] == "secondary":
                po = item.get("primary_of")
                if not po or not _obtained(ctx, po):
                    out.append(f"{e['kind']} event {e['id']}: secondary source {item['source']!r} "
                               + (f"whose primary {po!r} was not obtained" if po else "without primary_of"))
    return out


def w_strawman(ctx: Ctx, **_) -> list[str]:
    return [f"rival {e['rival']} is flagged as a strawman" for e in ctx["state"]["holders"] if e.get("strawman")]


def w_quotes(ctx: Ctx, **_) -> list[str]:
    out = []
    for sid, src in ctx["sources"].items():
        for q in src.get("quotes", []):
            if q.get("verified") is False:
                out.append(f"source {sid}: quote on page {q.get('page', '?')} not found in the fetched text")
    return out


def w_self_attack(ctx: Ctx, **_) -> list[str]:
    return [f"attack event {e['id']} was made by the author" for e in _events(ctx, "attack") if e["reviewer"] == "self"]


PREDICATES: dict[str, Callable[..., list[str]]] = {
    "has": p_has, "count": p_count, "any": p_any,
    "prior_answer_evidence": p_prior_answer_evidence,
    "fresh_attack_with_artifacts": p_fresh_attack_with_artifacts,
    "objections_answered": p_objections_answered,
    "user_chose": p_user_chose,
    "refs_exist": i_refs_exist,
    "checked_needs_primary": i_checked_needs_primary,
    "unobtainable_is_unverified": i_unobtainable_is_unverified,
    "no_post_hoc_prediction": i_no_post_hoc_prediction,
    "prediction_sums_to_one": i_prediction_sums_to_one,
    "eliminate_needs_holder": i_eliminate_needs_holder,
    "answer_rival_survives": i_answer_rival_survives,
    "artifacts_match": i_artifacts_match,
    "outputs_reproduce": i_outputs_reproduce,
    "one_variable_per_operation": w_one_variable,
    "operation_is_diagnostic": w_diagnostic,
    "operation_secondhand": w_operation_secondhand,
    "strawman_flagged": w_strawman,
    "quotes_verified": w_quotes,
    "no_self_attack": w_self_attack,
}


def _call(entry: dict, ctx: Ctx) -> list[str]:
    args = {k: v for k, v in entry.items() if k not in ("pred", "message", "id")}
    try:
        fn = PREDICATES[entry["pred"]]
    except KeyError:
        raise ValueError(f"rules.toml names an unknown predicate {entry['pred']!r}") from None
    return fn(ctx, **args)


def next_step(rules: dict, ctx: Ctx) -> dict:
    """First stage with an unmet requirement, what is missing, and which instructions to show."""
    stages = rules["stage"]
    for stage in stages:
        missing = []
        for req in stage["requires"]:
            details = _call(req, ctx)
            if details:
                missing.append({"message": req["message"], "details": details})
        if missing:
            return {"stage": stage["id"], "name": stage["name"], "missing": missing, "show": stage.get("show", [])}
    return {"stage": "done", "name": "closed", "missing": [], "show": []}


def all_steps(rules: dict, ctx: Ctx) -> list[dict]:
    """Unmet requirements of every stage, not only the first: for auditing an existing record."""
    out = []
    for stage in rules["stage"]:
        missing = [{"message": r["message"], "details": d} for r in stage["requires"] if (d := _call(r, ctx))]
        out.append({"stage": stage["id"], "name": stage["name"], "missing": missing})
    return out


def check(rules: dict, ctx: Ctx) -> dict:
    """Invariant violations (errors) and warnings."""
    errors, warnings = [], []
    for inv in rules.get("invariant", []):
        for msg in _call(inv, ctx):
            errors.append({"id": inv["id"], "rule": inv["message"], "detail": msg})
    for w in rules.get("warning", []):
        for msg in _call(w, ctx):
            warnings.append({"id": w["id"], "rule": w["message"], "detail": msg})
    return {"errors": errors, "warnings": warnings}
