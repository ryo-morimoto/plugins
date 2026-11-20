#!/usr/bin/env python3
"""te: run a thought experiment as data. Standard library only (Python 3.11+).

The one command to remember is `te next <dir>`: it reads the record, says which stage you are
in, what is missing, and shows the short instructions for that stage.

  te init <dir> --id <id>                         start a record
  te next <dir> [--json] [--all] [--lang ja]      stage, what is missing, instructions, score
  te add <dir> <kind> --json '{...}' [--author A] [--note-file F]
                                                  append an event (validated; the only writer)
  te source add <dir> <id> (--url U | --file F) [--title T] [--quote TEXT --page N]...
                                                  fetch or read a source, record sha256, verify quotes
  te brief <dir> --lens <lens>                    save a reviewer brief to briefs/, print its sha256
  te brief <dir> --record-response <brief> <file> save a reviewer's reply next to its brief
  te run <dir>                                    run scripts/*.py into outputs/ (TE_OUTPUTS)
  te render <dir> [--write] [--argdown] [--reply] [--lang ja]
  te score <dir>                                  Brier score of the stage A prediction
  te check <dir> [--lock te.lock] [--no-rerun]    invariants and warnings; exit 1 on errors
  te version [--verify te.lock] | te lock <file> --repo <url>
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from telib import core, rules, schema, store, views  # noqa: E402

KINDS = ["frame", "prior_answer", "holder", "prediction", "rival", "probe", "operation", "attack",
         "conclusion", "review", "correction", "supersede", "decision", "branch", "close"]


def _load(d: Path, rerun: bool = False) -> tuple[dict, dict, list[str]]:
    """Folded state, the rules context, and structural errors (parse, schema, ids)."""
    exp = store.load_experiment(d)
    events, errs = store.read_events(d)
    sch = store.load_schema()
    valid = []
    for i, e in enumerate(events, 1):
        problems = schema.validate(e, sch)
        if problems:
            errs += [f"event #{i} (id {e.get('id')}): {p}" for p in problems]
        else:
            valid.append(e)
    ids = [e["id"] for e in valid]
    if ids != list(range(1, len(ids) + 1)):
        errs.append(f"event ids must be 1..n in order; found {ids}")
    state = core.fold(valid, exp)
    ctx = {"state": state, "sources": store.read_sources(d), "files": store.tracked_files(d),
           "rerun": store.rerun_outputs(d) if rerun else None}
    return state, ctx, errs


def cmd_init(a) -> int:
    d = Path(a.dir)
    d.mkdir(parents=True, exist_ok=True)
    store.init(d, a.id)
    print(f"initialised {d}. Next: te next {d}")
    return 0


def cmd_add(a) -> int:
    d = Path(a.dir)
    store.load_experiment(d)
    events, errs = store.read_events(d)
    if errs:
        print("\n".join(errs), file=sys.stderr)
        return 1
    payload = json.loads(a.json)
    if not isinstance(payload, dict):
        print("--json must be an object", file=sys.stderr)
        return 2
    reserved = {"id", "v", "at", "kind", "author"} & set(payload)
    if reserved:
        print(f"do not set {sorted(reserved)}; te assigns them", file=sys.stderr)
        return 2
    event = {"id": len(events) + 1, "v": core.CURRENT_VERSION, "at": store.now(), "kind": a.kind,
             "author": a.author, **payload}
    problems = schema.validate(event, store.load_schema())
    if problems:
        print("rejected:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    state = core.fold(events + [event], store.load_experiment(d))
    ctx = {"state": state, "sources": store.read_sources(d), "files": store.tracked_files(d), "rerun": None}
    own = [m for m in rules.i_refs_exist(ctx) if m.startswith(f"event {event['id']} ")]
    if own:
        print("rejected:\n  " + "\n  ".join(own), file=sys.stderr)
        return 1
    if a.note_file:
        (d / "notes").mkdir(exist_ok=True)
        shutil.copyfile(a.note_file, d / "notes" / f"{event['id']}.md")
    store.append_event(d, event)
    print(f"added event {event['id']} ({a.kind})")
    return 0


def _print_step(step: dict, instr: dict) -> None:
    print(f"stage {step['stage']}: {step['name']}")
    for m in step["missing"]:
        print(f"  missing: {m['message']}")
        for det in m["details"]:
            print(f"    - {det}")
    for sid in step["show"]:
        print(f"\n[{sid}] {instr['show'][sid]}")


def cmd_next(a) -> int:
    d = Path(a.dir)
    state, ctx, errs = _load(d)
    rl, instr = store.load_rules(), store.load_instructions()
    if a.all:
        for st in rules.all_steps(rl, ctx):
            print(f"stage {st['stage']} ({st['name']}): " + ("met" if not st["missing"] else ""))
            for m in st["missing"]:
                print(f"  missing: {m['message']}")
                for det in m["details"]:
                    print(f"    - {det}")
        return 0
    step = rules.next_step(rl, ctx)
    chk = rules.check(rl, ctx)
    scored = core.score(state)
    if a.json:
        print(json.dumps({"step": step, "errors": errs + [e["detail"] for e in chk["errors"]],
                          "warnings": [w["detail"] for w in chk["warnings"]], "score": scored}, ensure_ascii=False, indent=1))
        return 0
    _print_step(step, instr)
    problems = errs + [f"{e['id']}: {e['detail']}" for e in chk["errors"]]
    if problems:
        print("\nfix before going on (te check for details):")
        print("\n".join(f"  ! {p}" for p in problems[:10]))
    if scored:
        print(f"\nprediction score: Brier {scored['brier']} (p={scored['p_answer']} on {scored['answer_rival']})")
    print("\n" + views.reply_skeleton(state, step, scored, a.lang))
    return 0


def cmd_source(a) -> int:
    d = Path(a.dir)
    store.load_experiment(d)
    if bool(a.url) == bool(a.file) and not (a.url and a.file):
        print("give --url, or --file (a copy the user obtained); --url with --file records both", file=sys.stderr)
        return 2
    pages = a.page or []
    quotes = [{"text": q, **({"page": pages[i]} if i < len(pages) else {})} for i, q in enumerate(a.quote or [])]
    rec = store.source_add(d, a.id, a.url, Path(a.file) if a.file else None, a.title, quotes)
    print(f"source {a.id}: obtained={rec['obtained']}" + (f" sha256={rec['sha256']}" if rec.get("sha256") else ""))
    for q in rec.get("quotes", []):
        mark = {True: "found", False: "NOT FOUND", None: "not checked (no text)"}[q["verified"]]
        print(f"  quote p{q.get('page', '?')}: {mark}")
    if rec["obtained"] == "none":
        print(f"  could not obtain: {rec['attempts'][-1]}\n  premises citing it cannot be empirical-checked")
        return 1
    return 0


def cmd_brief(a) -> int:
    d = Path(a.dir)
    state, _, _ = _load(d)
    (d / "briefs").mkdir(exist_ok=True)
    if a.record_response:
        brief_name, src = a.record_response
        bp = d / "briefs" / Path(brief_name).name
        if not bp.exists():
            print(f"no brief {bp}", file=sys.stderr)
            return 1
        rp = bp.with_name(bp.stem + ".response.md")
        shutil.copyfile(src, rp)
        b, r = store.sha256_file(bp), store.sha256_file(rp)
        print(f"saved {rp.relative_to(d)} sha256={r}")
        print("record the attack with, for example:")
        print("  te add " + str(d) + " attack --author reviewer:" + bp.stem.split("-", 1)[-1] + " --json '" + json.dumps(
            {"reviewer": "fresh", "lens": bp.stem.split("-", 1)[-1],
             "brief": {"file": f"briefs/{bp.name}", "sha256": b}, "response": {"file": f"briefs/{rp.name}", "sha256": r},
             "objections": [{"text": "…", "target": "premise", "response": "…", "reason": "…"}]}, ensure_ascii=False) + "'")
        return 0
    lenses = {l["id"]: l for l in store.load_instructions()["lens"]}
    if a.lens not in lenses:
        print(f"unknown lens {a.lens!r}; choose from {sorted(lenses)}", file=sys.stderr)
        return 2
    n = len([p for p in (d / "briefs").glob("*.md") if not p.name.endswith(".response.md")]) + 1
    bp = d / "briefs" / f"{n:02d}-{a.lens}.md"
    bp.write_text(views.brief(state, lenses[a.lens]), encoding="utf-8")
    print(f"saved {bp.relative_to(d)} sha256={store.sha256_file(bp)}")
    print("give this file, and nothing else from the history, to a fresh subagent (not a fork).")
    print(f"then: te brief {d} --record-response {bp.name} <reply-file>")
    return 0


def cmd_run(a) -> int:
    d = Path(a.dir)
    fails = store.run_scripts(d, d / "outputs")
    for f in fails:
        print(f"! {f}", file=sys.stderr)
    for p in sorted((d / "outputs").iterdir()):
        if p.is_file():
            print(f"outputs/{p.name} sha256={store.sha256_file(p)}")
    return 1 if fails else 0


def cmd_render(a) -> int:
    d = Path(a.dir)
    state, ctx, _ = _load(d)
    scored = core.score(state)
    if a.argdown:
        sys.stdout.write(views.argdown(state))
    elif a.reply:
        sys.stdout.write(views.reply_skeleton(state, rules.next_step(store.load_rules(), ctx), scored, a.lang))
    else:
        text = views.render(state, ctx["sources"], a.lang, scored)
        if a.write:
            (d / "README.md").write_text(text, encoding="utf-8")
            print(f"wrote {d / 'README.md'}")
        else:
            sys.stdout.write(text)
    return 0


def cmd_score(a) -> int:
    state, _, _ = _load(Path(a.dir))
    s = core.score(state)
    print(json.dumps(s, ensure_ascii=False) if s else "no score: needs a prediction and a conclusion with answer_rival")
    return 0


def _version_line() -> str:
    return f"te commit={store.git_commit() or 'unknown'} bundle_sha256={store.bundle_sha256()}"


def _verify_lock(path: Path) -> str | None:
    lock = store.read_lock(path)
    have = store.bundle_sha256()
    if lock.get("bundle_sha256") != have:
        return f"{path}: bundle_sha256 {lock.get('bundle_sha256')} does not match this te ({have})"
    return None


def cmd_check(a) -> int:
    d = Path(a.dir)
    print(_version_line())
    lock_err = _verify_lock(Path(a.lock)) if a.lock else None
    state, ctx, errs = _load(d, rerun=not a.no_rerun)
    res = rules.check(store.load_rules(), ctx)
    for e in ([lock_err] if lock_err else []) + errs:
        print(f"ERROR {e}")
    for e in res["errors"]:
        print(f"ERROR [{e['id']}] {e['detail']}\n      {e['rule']}")
    for w in res["warnings"]:
        print(f"warn  [{w['id']}] {w['detail']}")
    n = len(res["errors"]) + len(errs) + (1 if lock_err else 0)
    print(f"{n} error(s), {len(res['warnings'])} warning(s)")
    return 1 if n else 0


def cmd_version(a) -> int:
    print(_version_line())
    if a.verify:
        err = _verify_lock(Path(a.verify))
        if err:
            print(err, file=sys.stderr)
            return 1
        print(f"{a.verify}: matches")
    return 0


def cmd_lock(a) -> int:
    lock = store.write_lock(Path(a.file), a.repo)
    print(f"wrote {a.file}: commit={lock['commit']} bundle_sha256={lock['bundle_sha256']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="te", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("init"); s.add_argument("dir"); s.add_argument("--id", required=True); s.set_defaults(fn=cmd_init)
    s = sub.add_parser("next"); s.add_argument("dir"); s.add_argument("--json", action="store_true"); s.add_argument("--all", action="store_true", help="unmet requirements of every stage (audit)"); s.add_argument("--lang", default="en", choices=["en", "ja"]); s.set_defaults(fn=cmd_next)
    s = sub.add_parser("add"); s.add_argument("dir"); s.add_argument("kind", choices=KINDS); s.add_argument("--json", required=True)
    s.add_argument("--author", default="claude"); s.add_argument("--note-file"); s.set_defaults(fn=cmd_add)
    src = sub.add_parser("source").add_subparsers(dest="sub", required=True).add_parser("add")
    src.add_argument("dir"); src.add_argument("id"); src.add_argument("--url"); src.add_argument("--file"); src.add_argument("--title")
    src.add_argument("--quote", action="append"); src.add_argument("--page", action="append", type=int); src.set_defaults(fn=cmd_source)
    s = sub.add_parser("brief"); s.add_argument("dir"); s.add_argument("--lens"); s.add_argument("--record-response", nargs=2, metavar=("BRIEF", "FILE"))
    s.set_defaults(fn=cmd_brief)
    s = sub.add_parser("run"); s.add_argument("dir"); s.set_defaults(fn=cmd_run)
    s = sub.add_parser("render"); s.add_argument("dir"); s.add_argument("--write", action="store_true"); s.add_argument("--argdown", action="store_true")
    s.add_argument("--reply", action="store_true"); s.add_argument("--lang", default="en", choices=["en", "ja"]); s.set_defaults(fn=cmd_render)
    s = sub.add_parser("score"); s.add_argument("dir"); s.set_defaults(fn=cmd_score)
    s = sub.add_parser("check"); s.add_argument("dir"); s.add_argument("--lock"); s.add_argument("--no-rerun", action="store_true"); s.set_defaults(fn=cmd_check)
    s = sub.add_parser("version"); s.add_argument("--verify"); s.set_defaults(fn=cmd_version)
    s = sub.add_parser("lock"); s.add_argument("file"); s.add_argument("--repo", required=True); s.set_defaults(fn=cmd_lock)
    a = p.parse_args(argv)
    if a.cmd == "brief" and not a.lens and not a.record_response:
        p.error("brief needs --lens or --record-response")
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
