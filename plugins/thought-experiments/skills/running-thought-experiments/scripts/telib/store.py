"""File, network and process I/O for te. Everything else in telib is pure.

Layout of one experiment directory:
  experiment.toml   identity only (id, created)
  events.jsonl      append-only; written only by append_event
  sources.toml      cited documents
  sources/raw/      fetched originals (git-ignored: third-party works, only their hashes are public)
  notes/ briefs/ scripts/ outputs/
"""

from __future__ import annotations

import datetime as dt
import filecmp
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2]
DATA = SKILL / "data"
USER_AGENT = "te/1 (thought-experiments plugin; +https://github.com/ryo-morimoto/plugins)"


# ---------- data shipped with the skill ----------

def load_rules() -> dict:
    return tomllib.loads((DATA / "rules.toml").read_text(encoding="utf-8"))


def load_instructions() -> dict:
    return tomllib.loads((DATA / "instructions.toml").read_text(encoding="utf-8"))


def load_schema(version: int = 1) -> dict:
    return json.loads((DATA / "schema" / f"v{version}.json").read_text(encoding="utf-8"))


# ---------- experiment directory ----------

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(p.read_bytes())


def init(d: Path, exp_id: str) -> None:
    if (d / "experiment.toml").exists():
        raise SystemExit(f"{d} already has experiment.toml")
    for sub in ("notes", "briefs", "scripts", "outputs", "sources/raw"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    (d / "sources/raw/.gitignore").write_text("# fetched originals are third-party works; only their sha256 is published\n*\n!.gitignore\n", encoding="utf-8")
    (d / "experiment.toml").write_text(f'id = {json.dumps(exp_id, ensure_ascii=False)}\ncreated = {dt.date.today().isoformat()}\n', encoding="utf-8")
    (d / "events.jsonl").write_text("", encoding="utf-8")
    (d / "sources.toml").write_text("", encoding="utf-8")


def load_experiment(d: Path) -> dict:
    p = d / "experiment.toml"
    if not p.exists():
        raise SystemExit(f"{d} is not a te experiment (no experiment.toml). Run te init first.")
    return tomllib.loads(p.read_text(encoding="utf-8"))


def read_events(d: Path) -> tuple[list[dict], list[str]]:
    """Events and parse errors. A truncated last line is reported, not silently dropped."""
    events, errs = [], []
    p = d / "events.jsonl"
    text = p.read_text(encoding="utf-8") if p.exists() else ""
    if text and not text.endswith("\n"):
        errs.append("events.jsonl: last line has no newline (truncated write?)")
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as e:
            errs.append(f"events.jsonl:{n}: not valid JSON ({e.msg})")
    return events, errs


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def append_event(d: Path, event: dict) -> None:
    line = json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
    with (d / "events.jsonl").open("a", encoding="utf-8") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())


def read_sources(d: Path) -> dict:
    p = d / "sources.toml"
    if not p.exists() or not p.read_text(encoding="utf-8").strip():
        return {}
    return tomllib.loads(p.read_text(encoding="utf-8")).get("src", {})


def _toml_value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, dt.date):
        return v.isoformat()
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return "[" + ", ".join(_toml_value(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{ " + ", ".join(f"{k} = {_toml_value(x)}" for k, x in v.items()) + " }"
    raise TypeError(f"cannot write {type(v).__name__} to TOML")


def write_sources(d: Path, sources: dict) -> None:
    out = ["# Written by te source add. Edit through te so hashes stay consistent.", ""]
    for sid in sorted(sources):
        out.append(f"[src.{json.dumps(sid)}]")
        out += [f"{k} = {_toml_value(v)}" for k, v in sources[sid].items()]
        out.append("")
    (d / "sources.toml").write_text("\n".join(out), encoding="utf-8")


def tracked_files(d: Path) -> dict:
    """sha256 of every file under briefs/ and outputs/, keyed by experiment-relative path."""
    out = {}
    for sub in ("briefs", "outputs"):
        base = d / sub
        if base.is_dir():
            for p in sorted(base.iterdir()):
                if p.is_file() and not p.name.startswith("."):
                    out[f"{sub}/{p.name}"] = sha256_file(p)
    return out


# ---------- sources ----------

def _normalise(s: str) -> str:
    return re.sub(r"\s+", "", html.unescape(s)).lower()


def extract_text(raw: bytes, content_type: str = "", name: str = "") -> str | None:
    """Plain text of a fetched document, or None when it cannot be extracted here."""
    if raw[:5] == b"%PDF-" or name.lower().endswith(".pdf"):
        if not shutil.which("pdftotext"):
            return None
        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
            tmp.write(raw)
            tmp.flush()
            r = subprocess.run(["pdftotext", "-enc", "UTF-8", "-layout", tmp.name, "-"], capture_output=True)
            return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else None
    for enc in ("utf-8", "cp932", "euc_jp", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if "html" in content_type or text.lstrip()[:15].lower().startswith(("<!doctype", "<html")):
        text = re.sub(r"(?is)<(script|style).*?</\1>", " ", text)
        text = re.sub(r"<[^>]+>", " ", text)
    return text


def verify_quotes(text: str | None, quotes: list[dict]) -> list[dict]:
    out = []
    for q in quotes:
        q = dict(q)
        q["verified"] = None if text is None else _normalise(q["text"]) in _normalise(text)
        out.append(q)
    return out


def fetch(url: str, timeout: int = 60) -> tuple[bytes, str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", ""), r.url


def source_add(d: Path, sid: str, url: str | None, file: Path | None, title: str | None,
               quotes: list[dict]) -> dict:
    sources = read_sources(d)
    rec = dict(sources.get(sid, {}))
    if title:
        rec["title"] = title
    if url:
        rec["url"] = url
    rec["retrieved"] = dt.date.today()
    try:
        if file is not None:
            raw, ctype, name = file.read_bytes(), "", file.name
            rec["obtained"] = "user"
        else:
            raw, ctype, final = fetch(url)
            name = final.rsplit("/", 1)[-1]
            rec["obtained"] = "fetch"
            if final != url:
                rec["final_url"] = final
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        rec["obtained"] = "none"
        rec.setdefault("attempts", []).append(f"{dt.date.today().isoformat()} {url}: {e}")
        rec.pop("sha256", None)
        sources[sid] = rec
        write_sources(d, sources)
        return rec
    rec["sha256"] = sha256_bytes(raw)
    raw_dir = d / "sources/raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    if not (raw_dir / ".gitignore").exists():
        (raw_dir / ".gitignore").write_text("*\n!.gitignore\n", encoding="utf-8")
    ext = Path(name).suffix or (".pdf" if raw[:5] == b"%PDF-" else ".html" if "html" in ctype else ".bin")
    (raw_dir / f"{sid}{ext}").write_bytes(raw)
    text = extract_text(raw, ctype, name)
    if quotes or rec.get("quotes"):
        rec["quotes"] = verify_quotes(text, (rec.get("quotes", []) if not quotes else []) + quotes)
    sources[sid] = rec
    write_sources(d, sources)
    return rec


# ---------- scripts and outputs ----------

def _scripts(d: Path) -> list[Path]:
    return sorted(p for p in (d / "scripts").glob("*.py")) if (d / "scripts").is_dir() else []


def run_scripts(d: Path, out_dir: Path) -> list[str]:
    """Run each scripts/*.py with TE_OUTPUTS pointing at out_dir. Returns failure messages."""
    out_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, TE_OUTPUTS=str(out_dir), PYTHONHASHSEED="0")
    fails = []
    for s in _scripts(d):
        r = subprocess.run([sys.executable, "-I", str(s)], cwd=d, env=env, capture_output=True, text=True)
        if r.returncode != 0:
            fails.append(f"{s.relative_to(d)} exited {r.returncode}: {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else ''}")
    return fails


def rerun_outputs(d: Path) -> list[str]:
    """Re-run scripts into a temporary directory and compare with outputs/ byte for byte."""
    if not _scripts(d):
        return []
    with tempfile.TemporaryDirectory() as tmp:
        fresh = Path(tmp)
        fails = run_scripts(d, fresh)
        committed = d / "outputs"
        names = {p.name for p in fresh.iterdir()} | ({p.name for p in committed.iterdir() if not p.name.startswith(".")} if committed.is_dir() else set())
        for n in sorted(names):
            a, b = committed / n, fresh / n
            if not a.exists():
                fails.append(f"outputs/{n} is produced by scripts/ but not committed (run te run)")
            elif not b.exists():
                fails.append(f"outputs/{n} is committed but no script produces it")
            elif not filecmp.cmp(a, b, shallow=False):
                fails.append(f"outputs/{n} differs from what scripts/ produce now")
        return fails


# ---------- te's own version ----------

def bundle_files() -> list[Path]:
    files = [SKILL / "scripts/te.py"] + sorted((SKILL / "scripts/telib").glob("*.py")) + sorted(DATA.rglob("*.*"))
    return [p for p in files if p.is_file()]


def bundle_sha256() -> str:
    h = hashlib.sha256()
    for p in bundle_files():
        h.update(str(p.relative_to(SKILL)).encode() + b"\0" + p.read_bytes() + b"\0")
    return h.hexdigest()


def git_commit() -> str | None:
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=SKILL, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else os.environ.get("TE_COMMIT")


def read_lock(p: Path) -> dict:
    return tomllib.loads(p.read_text(encoding="utf-8"))


def write_lock(p: Path, repo: str) -> dict:
    lock = {"repo": repo, "commit": git_commit() or "", "path": str(SKILL.relative_to(SKILL.parents[3])) if len(SKILL.parents) > 3 else "",
            "bundle_sha256": bundle_sha256()}
    p.write_text("# te version pin. CI fetches this commit and checks bundle_sha256 before running te check.\n"
                 + "".join(f"{k} = {_toml_value(v)}\n" for k, v in lock.items()), encoding="utf-8")
    return lock
