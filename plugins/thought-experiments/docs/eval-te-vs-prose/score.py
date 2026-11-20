"""Deterministic metrics for the prose vs te evaluation. Usage: python3 -I score.py <eval-dir>

For every run: replies (count, length). For te runs additionally: te calls by subcommand,
whether `te next` ran before each reply (call time within the gap since the previous reply),
and the final te check / stage of the record.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

E = Path(sys.argv[1]).resolve()
JA_BUDGET, EVAL_CAP = 1500, 2000
rows = []
for run in sorted((E / "runs").iterdir()):
    work = run / "work"
    replies = sorted(work.glob("reply-*.md"))
    lens = [len(p.read_text(encoding="utf-8")) for p in replies]
    row = {"run": run.name, "replies": len(replies), "len": lens,
           "over_budget": sum(n > JA_BUDGET for n in lens), "over_cap": sum(n > EVAL_CAP for n in lens),
           "urls_in_first": len(re.findall(r"https?://", replies[0].read_text(encoding="utf-8"))) if replies else 0}
    log = run / "skill" / "calls.jsonl"
    if log.exists() and not run.name.startswith("prose"):
        calls = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
        sub = {}
        for c in calls:
            k = c["argv"][0] if c["argv"] else "?"
            if k == "source" and len(c["argv"]) > 1:
                k = "source " + c["argv"][1]
            sub[k] = sub.get(k, 0) + 1
        row["calls"] = sub
        times = [p.stat().st_mtime for p in replies]
        nexts = [c["t"] for c in calls if c["argv"][:1] == ["next"]]
        before = []
        for i, t in enumerate(times):
            lo = times[i - 1] if i else 0
            before.append(any(lo < n <= t for n in nexts))
        row["next_before_reply"] = before
        exps = [p.parent for p in work.rglob("experiment.toml")]
        if exps:
            d = exps[0]
            te = run / "skill/scripts/te_real.py"
            chk = subprocess.run([sys.executable, "-I", str(te), "check", str(d), "--no-rerun"], capture_output=True, text=True).stdout
            row["check"] = chk.strip().splitlines()[-1]
            row["check_ids"] = sorted(set(re.findall(r"^(?:ERROR|warn ) \[([a-z-]+)\]", chk, re.M)))
            nxt = json.loads(subprocess.run([sys.executable, "-I", str(te), "next", str(d), "--json"], capture_output=True, text=True).stdout)
            row["stage"] = nxt["step"]["stage"]
            row["score"] = nxt["score"]
            ev = [json.loads(l) for l in (d / "events.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
            kinds = {}
            for e in ev:
                kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
            row["events"] = kinds
            row["attack_reviewers"] = [e.get("reviewer") + ("+files" if e.get("brief") else "") for e in ev if e["kind"] == "attack"]
            src = (d / "sources.toml").read_text(encoding="utf-8")
            row["sources"] = {k: src.count(f'obtained = "{k}"') for k in ("fetch", "user", "none")}
        else:
            row["record"] = "no experiment.toml"
    rows.append(row)
print(json.dumps(rows, ensure_ascii=False, indent=1))
