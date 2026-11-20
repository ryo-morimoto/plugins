#!/usr/bin/env python3
"""Check character limits and reference links for this skill.

Usage: python scripts/check_limits.py [skill_dir]
Exit code 0 when every check passes, 1 otherwise.
"""
import sys
import tomllib
from pathlib import Path

# SKILL.md loads on every trigger, so it gets the tighter budget.
SKILL_MD_LIMIT = 1000
# Reference, script and eval files load one at a time on demand.
OTHER_LIMIT = 2000
# Generated content, not part of the authored skill.
SKIP_DIRS = {"__pycache__", ".git", "results"}
# te's code and data are run, not read: the model sees only what te prints.
# So their file size is free, and the printed texts get limits instead.
RUN_NOT_READ = ("scripts/", "data/")
SHOW_LIMIT = 600      # one instruction te next prints
LENS_LIMIT = 400      # one reviewer lens in a brief
MESSAGE_LIMIT = 300   # one rule message
STAGE_LIMIT = 1600    # all instructions te next prints for one stage


def check_te(root: Path) -> bool:
    """Limits on the texts te prints. Returns True when any fails."""
    data = root / "data"
    if not (data / "rules.toml").is_file():
        return False
    rules = tomllib.loads((data / "rules.toml").read_text(encoding="utf-8"))
    instr = tomllib.loads((data / "instructions.toml").read_text(encoding="utf-8"))
    checks = [(f"show.{k}", v, SHOW_LIMIT) for k, v in instr["show"].items()]
    checks += [(f"lens.{x['id']}", x["text"], LENS_LIMIT) for x in instr["lens"]]
    for st in rules["stage"]:
        checks += [(f"stage {st['id']} requires", r["message"], MESSAGE_LIMIT) for r in st["requires"]]
        shown = "".join(instr["show"].get(k, "") for k in st.get("show", []))
        checks.append((f"stage {st['id']} shown", shown, STAGE_LIMIT))
        for k in st.get("show", []):
            if k not in instr["show"]:
                print(f"FAIL  stage {st['id']} shows unknown instruction {k!r}")
                checks.append(("", "x", 0))
    for sec in ("invariant", "warning"):
        checks += [(f"{sec}.{x['id']}", x["message"], MESSAGE_LIMIT) for x in rules.get(sec, [])]
    failed = False
    for name, text, limit in checks:
        if not name:
            failed = True
            continue
        ok = len(text) <= limit
        failed |= not ok
        print(f"{'ok  ' if ok else 'FAIL'}  {len(text):>5}/{limit}  te {name}")
    return failed


def main() -> int:
    default = Path(__file__).resolve().parent.parent
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else default
    skill_md = root / "SKILL.md"
    if not skill_md.is_file():
        print(f"FAIL  no SKILL.md in {root}")
        return 1

    failed = False
    files = sorted(p for p in root.rglob("*") if p.is_file()
                   and not SKIP_DIRS & set(p.relative_to(root).parts))
    for path in files:
        rel = path.relative_to(root).as_posix()
        if rel.startswith(RUN_NOT_READ):
            continue
        limit = SKILL_MD_LIMIT if path == skill_md else OTHER_LIMIT
        try:
            # Code points, not bytes, so non-ASCII text counts fairly.
            count = len(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            print(f"FAIL  {rel}: not UTF-8 text")
            failed = True
            continue
        ok = count <= limit
        failed |= not ok
        note = "" if ok else f"  (over by {count - limit})"
        print(f"{'ok  ' if ok else 'FAIL'}  {count:>5}/{limit}  {rel}{note}")

    # Unlinked references are never discovered by the model.
    body = skill_md.read_text(encoding="utf-8")
    for ref in sorted((root / "references").glob("*.md")):
        link = f"references/{ref.name}"
        if link not in body:
            print(f"FAIL  {link} is not linked from SKILL.md")
            failed = True

    failed |= check_te(root)

    print("FAILED" if failed else "All checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
