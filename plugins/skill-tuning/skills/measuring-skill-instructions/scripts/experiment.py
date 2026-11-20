#!/usr/bin/env python3
"""experiment.py - prepare, check and score a with/without-skill experiment.

Usage: experiment.py <prepare|missing|score|compare|reproduce> <experiment.json> [--root DIR]
`score` also saves results.json; `reproduce` rescoring must equal that file.
The config format is described in references/config.md.
"""
import argparse, glob, json, os, re, sys


def load(path):
    cfg = json.load(open(path))
    cfg.setdefault("layout", "{trial}/{task}/{cond}/{file}")
    cfg.setdefault("preamble", "Before anything else, read {skill}/SKILL.md and the "
                   "files it points to that fit this task, and apply that skill.")
    cfg.setdefault("footer", "Use only Read, read-only Bash and Write. Never call any "
                   "scheduling, trigger, repository-listing or other tool.")
    for c in cfg["conditions"]:
        c.setdefault("dirs", [c["name"]])
        c.setdefault("skill", None)
    for t in cfg["tasks"]:
        t.setdefault("group", "")
        t.setdefault("measures", [])
    return cfg


def out_dir(cfg, root, trial, task, dirname):
    p = cfg["layout"].format(trial=trial, group=task["group"], task=task["name"],
                             cond=dirname, file="")
    return os.path.normpath(os.path.join(root, p))


def find(cfg, root, trial, task, cond, pattern):
    """First existing file for this run, trying each directory name of the condition."""
    for d in cond["dirs"]:
        hits = sorted(glob.glob(os.path.join(out_dir(cfg, root, trial, task, d), pattern)))
        if hits:
            return hits[0]
    return None


# ---------- measures ----------

def clj_bindings(src):
    """Count binding pairs in let-like forms of Clojure source."""
    total = 0
    for m in re.finditer(r"\((?:let|when-let|if-let|loop)\s*\[", src):
        j, depth, toks, start = m.end(), 1, 0, m.end()
        while j < len(src) and depth > 0:
            c = src[j]
            if c in "([{":
                if depth == 1:
                    toks += 1
                depth += 1
            elif c in ")]}":
                depth -= 1
            elif depth == 1 and not c.isspace() and (j == start or src[j - 1] in " \n\t,"):
                toks += 1
            j += 1
        total += toks // 2
    return total


BUILTIN = {"builtin:clj-bindings": clj_bindings}


def measure(spec, path, task):
    """Return a number for one output file, or None if it cannot be read."""
    kind = spec["type"]
    try:
        if kind == "occurrences":
            src = open(path).read()
            pats = spec["patterns"].get(path.rsplit(".", 1)[-1])
            if pats is None:
                return None
            if isinstance(pats, str):
                return BUILTIN[pats](src)
            return sum(len(re.findall(p, src, re.M)) for p in pats)
        data = json.load(open(path))
        if kind == "decision":
            return int(data[spec.get("field", "decision")] == task["expect"])
        if kind == "value-length":
            return sum(len(str(v)) for v in data.values())
        if kind == "value-matches":
            keys = spec.get("keys") or list(data)
            return sum(bool(re.search(spec["regex"], str(data[k]))) for k in keys if k in data)
        if kind == "value-differs":
            return int(data[spec["key"]] != spec["value"])
    except Exception:
        return None
    raise SystemExit(f"unknown measure type: {kind}")


def collect(cfg, root):
    """results[measure][condition] = one total per trial (None where nothing was found).
    by_task[measure][condition][task] = per-trial values, kept for decision measures."""
    results, by_task, missing = {}, {}, []
    for name, spec in cfg["measures"].items():
        if not any(name in t["measures"] for t in cfg["tasks"]):
            continue
        for cond in cfg["conditions"]:
            totals = []
            for trial in cfg["trials"]:
                vals = []
                for task in cfg["tasks"]:
                    if name not in task["measures"]:
                        continue
                    path = find(cfg, root, trial, task, cond, spec["file"])
                    v = measure(spec, path, task) if path else None
                    if v is None:
                        missing.append((trial, task["name"], cond["name"], spec["file"]))
                    else:
                        vals.append(v)
                    if spec["type"] == "decision":
                        by_task.setdefault(name, {}).setdefault(cond["name"], {}) \
                             .setdefault(task["name"], []).append(v)
                totals.append(sum(vals) if vals else None)
            results.setdefault(name, {})[cond["name"]] = totals
            if spec["type"] == "decision":
                for cls in sorted({t.get("expect") for t in cfg["tasks"] if name in t["measures"]}):
                    sub = []
                    for i, trial in enumerate(cfg["trials"]):
                        got = [by_task[name][cond["name"]][t["name"]][i] for t in cfg["tasks"]
                               if name in t["measures"] and t.get("expect") == cls]
                        got = [g for g in got if g is not None]
                        sub.append(sum(got) if got else None)
                    results.setdefault(f"{name}[{cls}]", {})[cond["name"]] = sub
    return results, by_task, sorted(set(missing))


def fmt(vals):
    return " / ".join("-" if v is None else str(v) for v in vals)


# ---------- commands ----------

def cmd_prepare(cfg, root):
    n = 0
    for trial in cfg["trials"]:
        rundir = os.path.join(root, trial, "run")
        os.makedirs(rundir, exist_ok=True)
        k, manifest = 0, []
        for task in cfg["tasks"]:
            for cond in cfg["conditions"]:
                k += 1
                out = out_dir(cfg, root, trial, task, cond["dirs"][0])
                os.makedirs(out, exist_ok=True)
                parts = []
                if cond["skill"]:
                    parts.append(cfg["preamble"].replace("{skill}", cond["skill"]))
                parts.append(task["prompt"].replace("{out}", os.path.abspath(out)))
                parts.append(cfg["footer"])
                open(os.path.join(rundir, f"{k:03d}.md"), "w").write("\n\n".join(parts))
                manifest.append({"run": f"{k:03d}", "task": task["name"], "condition": cond["name"]})
        json.dump(manifest, open(os.path.join(rundir, "manifest.json"), "w"), indent=1)
        n += k
    print(f"{n} run files written ({len(cfg['trials'])} trials). Launch one isolated agent "
          f"per file with: Read <file> and do exactly what it says. Reply only 'done'.")


def cmd_missing(cfg, root):
    _, _, missing = collect(cfg, root)
    for m in missing:
        print("MISSING", *m)
    print(f"{len(missing)} missing or unreadable outputs")
    return 1 if missing else 0


def cmd_score(cfg, root, save=True):
    results, by_task, missing = collect(cfg, root)
    print(f"trials: {', '.join(cfg['trials'])}")
    for name, by_cond in results.items():
        print(name)
        for cond, vals in by_cond.items():
            print(f"  {cond:<16} {fmt(vals)}")
    if missing:
        print(f"note: {len(missing)} outputs missing; run `missing` for the list")
    if save:
        json.dump({"results": results, "by_task": by_task},
                  open(os.path.join(root, "results.json"), "w"), indent=1)
    return results, by_task


def cmd_compare(cfg, root):
    results, by_task = cmd_score(cfg, root, save=False)
    base = cfg["conditions"][0]["name"]
    print(f"\nrange test against `{base}` (an effect needs ranges that do not overlap)")
    for name, by_cond in results.items():
        a = [v for v in by_cond[base] if v is not None]
        for cond, vals in by_cond.items():
            b = [v for v in vals if v is not None]
            if cond == base or not a or not b:
                continue
            if min(a) > max(b) or max(a) < min(b):
                verdict = "SEPARATED"
            elif a == b or (min(a) == max(a) == min(b) == max(b)):
                verdict = "identical"
            else:
                verdict = "overlap"
            few = "" if min(len(a), len(b)) >= 3 else "  (fewer than 3 trials)"
            print(f"  {name:<22} {base} {min(a)}..{max(a)}  vs  {cond} {min(b)}..{max(b)}  {verdict}{few}")
    for name, by_cond in by_task.items():
        def wins(cond, task):
            v = [x for x in by_cond[cond][task] if x is not None]
            return sum(v), len(v)
        for cond in by_cond:
            if cond == base:
                continue
            fixed, broken, never = [], [], []
            for task in by_cond[base]:
                (wa, na), (wb, nb) = wins(base, task), wins(cond, task)
                if not na or not nb:
                    continue
                if wa * 2 > na and wb * 2 <= nb:
                    fixed.append(task)
                elif wb * 2 > nb and wa * 2 <= na:
                    broken.append(task)
                if wa == 0 and wb == 0:
                    never.append(task)
            print(f"\n{name}: `{base}` vs `{cond}` by task (majority of trials)")
            print(f"  right only with {base}: {len(fixed)}  {fixed}")
            print(f"  right only with {cond}: {len(broken)}  {broken}")
            print(f"  wrong in every trial under both: {len(never)}  {never}")


def cmd_reproduce(cfg, root):
    path = os.path.join(root, "results.json")
    if not os.path.exists(path):
        raise SystemExit("no results.json to reproduce; run `score` first")
    old = json.load(open(path))["results"]
    new, _, _ = collect(cfg, root)
    diffs = [(m, c, old.get(m, {}).get(c), new[m][c]) for m in new for c in new[m]
             if old.get(m, {}).get(c) != new[m][c]]
    for m, c, o, n in diffs:
        print(f"CHANGED {m} / {c}: saved {o} -> now {n}")
    print("reproduced" if not diffs else f"{len(diffs)} values differ: find out why before comparing")
    return 1 if diffs else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["prepare", "missing", "score", "compare", "reproduce"])
    ap.add_argument("config")
    ap.add_argument("--root", help="workspace directory (default: the config's directory)")
    a = ap.parse_args()
    cfg = load(a.config)
    root = a.root or os.path.dirname(os.path.abspath(a.config))
    rc = {"prepare": cmd_prepare, "missing": cmd_missing, "score": cmd_score,
          "compare": cmd_compare, "reproduce": cmd_reproduce}[a.command](cfg, root)
    sys.exit(rc if isinstance(rc, int) else 0)


if __name__ == "__main__":
    main()
