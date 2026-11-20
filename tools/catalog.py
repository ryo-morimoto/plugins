#!/usr/bin/env python3
"""plugin の一覧（catalog）を、元データから生成して検査する。依存は標準ライブラリだけ（Python 3.11+）。

元データは 2 つだけで、ほかは生成物:
    plugins/<name>/plugin.json         Agent Plugins 1.0 の manifest。名前・版・説明・ライセンス・キーワード
    .claude-plugin/marketplace.json    一覧。分類と、一覧に出す短い説明
生成物:
    plugins/<name>/.claude-plugin/plugin.json   Claude Code の manifest
    README.md の <!-- plugins:start --> 〜 <!-- plugins:end -->  の表

使い方:
    python3 tools/catalog.py render   # 生成物を書き直す
    python3 tools/catalog.py check    # 元データの検査と、生成物が最新かの検査（CI）
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUTHOR = "Ryo Morimoto"
SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
# Agent Skills の frontmatter（agentskills.io）。これ以外のキーは claude.ai と Skills API で拒否される
SKILL_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
SEMVER = re.compile(r"\d+\.\d+\.\d+([-+][0-9A-Za-z.-]+)?")
README_START, README_END = "<!-- plugins:start -->", "<!-- plugins:end -->"


def read_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def dump_json(d: dict) -> str:
    return json.dumps(d, ensure_ascii=False, indent=2) + "\n"


def frontmatter(skill_md: Path) -> dict:
    m = re.match(r"^---\n(.*?)\n---", skill_md.read_text(encoding="utf-8"), re.S)
    if not m:
        return {}
    return {k: v.strip().strip('"') for k, v in re.findall(r"^([A-Za-z_-]+):\s*(.*)$", m.group(1), re.M)}


def claude_manifest(std: dict) -> str:
    return dump_json({
        "name": std["name"], "version": std["version"], "description": std["description"],
        "author": {"name": AUTHOR}, "keywords": std.get("keywords", []), "license": std["license"],
    })


def readme_table(market: dict) -> str:
    rows = [f"| [{p['name']}](plugins/{p['name']}/README.md) | {p['description']} |" for p in market["plugins"]]
    return "\n".join([README_START, "| plugin | 内容 |", "| --- | --- |", *rows, README_END])


def generated() -> dict[Path, str]:
    market = read_json(ROOT / ".claude-plugin/marketplace.json")
    out = {}
    for p in market["plugins"]:
        d = ROOT / "plugins" / p["name"]
        out[d / ".claude-plugin/plugin.json"] = claude_manifest(read_json(d / "plugin.json"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    block = re.compile(re.escape(README_START) + ".*?" + re.escape(README_END), re.S)
    out[ROOT / "README.md"] = block.sub(lambda _: readme_table(market), readme)
    return out


def problems() -> tuple[list[str], list[str]]:
    """（誤り, 一覧のコストの報告）"""
    errs, costs = [], []
    market = read_json(ROOT / ".claude-plugin/marketplace.json")
    listed = {p["name"] for p in market["plugins"]}
    dirs = {d.name for d in (ROOT / "plugins").iterdir() if d.is_dir()}
    for n in sorted(dirs - listed):
        errs.append(f"plugins/{n}: marketplace.json に載っていない")
    for n in sorted(listed - dirs):
        errs.append(f"marketplace.json の {n}: plugins/{n} がない")
    if README_START not in (ROOT / "README.md").read_text(encoding="utf-8"):
        errs.append(f"README.md: {README_START} 〜 {README_END} の区間がない")
    for p in market["plugins"]:
        n, where = p["name"], f"plugins/{p['name']}"
        if p.get("source") != f"./plugins/{n}":
            errs.append(f"marketplace.json の {n}: source は ./plugins/{n}")
        if not (ROOT / where / "plugin.json").exists():
            continue
        std = read_json(ROOT / where / "plugin.json")
        if std.get("$schema") != SCHEMA:
            errs.append(f"{where}/plugin.json: $schema は {SCHEMA}")
        if std.get("name") != n:
            errs.append(f"{where}/plugin.json: name がディレクトリ名 {n} と違う")
        if not SEMVER.fullmatch(str(std.get("version", ""))):
            errs.append(f"{where}/plugin.json: version が semver でない")
        for k in ("description", "license"):
            if not std.get(k):
                errs.append(f"{where}/plugin.json: {k} がない")
        chars = 0
        for md in sorted((ROOT / where / "skills").glob("*/SKILL.md")):
            fm, s = frontmatter(md), md.parent.name
            if extra := set(fm) - SKILL_KEYS:
                errs.append(f"{where}/skills/{s}: 標準外の frontmatter {sorted(extra)}（claude.ai で拒否される）")
            if fm.get("name") != s or not NAME.fullmatch(s) or len(s) > 64:
                errs.append(f"{where}/skills/{s}: name はディレクトリ名と同じで、小文字・数字・ハイフンの 64 字以内")
            desc = fm.get("description", "")
            if not desc or len(desc) > 1024:
                errs.append(f"{where}/skills/{s}: description は 1〜1024 字（今 {len(desc)} 字）")
            chars += len(desc)
        costs.append(f"{n}: skill {len(list((ROOT / where / 'skills').glob('*/SKILL.md')))} 個、説明 {chars} 字")
    return errs, costs


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd not in ("render", "check"):
        print(__doc__, file=sys.stderr)
        return 2
    errs, costs = problems()
    if not errs:
        for path, text in generated().items():
            rel = path.relative_to(ROOT)
            if cmd == "render":
                if not path.exists() or path.read_text(encoding="utf-8") != text:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(text, encoding="utf-8")
                    print(f"書き出し: {rel}")
            elif not path.exists() or path.read_text(encoding="utf-8") != text:
                errs.append(f"{rel} が元データと一致しない。python3 tools/catalog.py render を実行する")
    if errs:
        print("\n".join(errs), file=sys.stderr)
        return 1
    if cmd == "check":
        print("一覧のコスト（skill の説明は、入れると毎ターン読み込まれる）:")
        print("\n".join("  " + c for c in costs))
        print(f"plugin {len(costs)} 個: 問題なし")
    return 0


if __name__ == "__main__":
    sys.exit(main())
