#!/usr/bin/env python3
"""pr-tour の JSON 書き出し v1 のコメントを、records.md の書式の finding として store に取り込む。"""

import argparse
import hashlib
import json
import re
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

PR_URL = re.compile(r"https://github\.com/([A-Za-z0-9][A-Za-z0-9-]*)/([A-Za-z0-9._-]+)/pull/([1-9][0-9]*)")
SHA = re.compile(r"[0-9a-f]{40}")
SIDES = ("left", "right")
TITLE_LIMIT = 120
ID_ATTEMPTS = 100


class InputError(Exception):
    pass


def require_text(obj, key, where):
    value = obj.get(key)
    if not isinstance(value, str) or not value:
        raise InputError(f"{where}: `{key}` が、空でない文字列ではありません")
    return value


def require_line(obj, key, where):
    value = obj.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise InputError(f"{where}: `{key}` が、1 以上の整数ではありません")
    return value


def finding_title(body):
    for line in body.splitlines():
        if line.strip():
            return line.strip()[:TITLE_LIMIT]
    raise InputError("本文に、空でない行がありません")


def validate_comment(comment, index):
    where = f"comments[{index}]"
    if not isinstance(comment, dict):
        raise InputError(f"{where}: オブジェクトではありません")
    for key in ("id", "path", "body", "createdAt"):
        require_text(comment, key, where)
    if comment.get("side") not in SIDES:
        raise InputError(f"{where}: `side` が left か right ではありません")
    start = require_line(comment, "startLine", where)
    end = require_line(comment, "endLine", where)
    if start > end:
        raise InputError(f"{where}: `startLine` が `endLine` より大きい")
    try:
        finding_title(comment["body"])
    except InputError as error:
        raise InputError(f"{where}: {error}") from error


def validate_export(data):
    if not isinstance(data, dict):
        raise InputError("書き出しが、JSON のオブジェクトではありません")
    if data.get("schemaVersion") != 1 or isinstance(data.get("schemaVersion"), bool):
        raise InputError("`schemaVersion` が 1 ではありません")
    if data.get("kind") != "pr-tour-review":
        raise InputError("`kind` が pr-tour-review ではありません")
    pr_url = require_text(data, "prUrl", "書き出し")
    if parse_pr_url(pr_url) is None:
        raise InputError("`prUrl` が、PR の URL（https://github.com/OWNER/REPO/pull/N）ではありません")
    head = data.get("head")
    if not isinstance(head, str) or not SHA.fullmatch(head):
        raise InputError("`head` が、40 桁の 16 進ではありません")
    base = data.get("base")
    if base is not None and (not isinstance(base, str) or not SHA.fullmatch(base)):
        raise InputError("`base` が、40 桁の 16 進ではありません")
    comments = data.get("comments")
    if not isinstance(comments, list):
        raise InputError("`comments` が、配列ではありません")
    for index, comment in enumerate(comments):
        validate_comment(comment, index)
    ids = [comment["id"] for comment in comments]
    if len(set(ids)) != len(ids):
        raise InputError("`comments` に、同じ `id` が複数あります")


def parse_pr_url(url):
    match = PR_URL.fullmatch(url)
    if match is None or match.group(2) in (".", ".."):
        return None
    return match.group(1), match.group(2), int(match.group(3))


def load_export(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise InputError(f"{path} を読めません: {error}") from error
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise InputError(f"{path} が JSON として読めません: {error}") from error
    validate_export(data)
    return data


def json_value(value):
    text = json.dumps(value, ensure_ascii=False)
    return text.replace("\x85", "\\u0085").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def render_record(meta, body=""):
    lines = ["---"] + [f"{key}: {json_value(value)}" for key, value in meta.items()] + ["---"]
    text = "\n".join(lines) + "\n"
    return text + body + "\n" if body else text


def parse_record(text):
    lines = text.split("\n")
    if lines[0] != "---" or "---" not in lines[1:]:
        raise InputError("front matter がありません")
    end = lines.index("---", 1)
    meta = {}
    for line in lines[1:end]:
        key, separator, raw = line.partition(": ")
        if not separator or not key:
            raise InputError(f"front matter の行が `キー: 値` ではありません: {line}")
        try:
            meta[key] = json.loads(raw)
        except json.JSONDecodeError as error:
            raise InputError(f"front matter の値が JSON ではありません: {line}") from error
    return meta, "\n".join(lines[end + 1 :]).strip("\r\n")


def timestamp(moment):
    return moment.strftime("%Y%m%dT%H%M%SZ")


def new_finding_id(moment, taken):
    for _ in range(ID_ATTEMPTS):
        candidate = f"{timestamp(moment)}-{secrets.token_hex(3)}"
        if candidate not in taken:
            taken.add(candidate)
            return candidate
    raise InputError("衝突しない id を作れませんでした")


def read_existing_findings(findings_dir):
    by_origin_ref = {}
    taken = set()
    if not findings_dir.is_dir():
        return by_origin_ref, taken
    for directory in sorted(findings_dir.iterdir()):
        taken.add(directory.name)
        record = directory / "finding.md"
        if not record.is_file():
            continue
        try:
            meta, body = parse_record(record.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, InputError) as error:
            raise InputError(f"既存の記録 {record} を読めません: {error}") from error
        origin_ref = meta.get("origin_ref")
        if isinstance(origin_ref, str):
            by_origin_ref.setdefault(origin_ref, (directory.name, body))
    return by_origin_ref, taken


def build_plan(export, pull_dir, series, created_by, moment):
    owner, repo, number = parse_pr_url(export["prUrl"])
    pull_id = f"{owner}/{repo}#{number}"
    head = export["head"]
    snapshot_id = f"{pull_id}@{head[:7]}"
    fetched_at = moment.strftime("%Y-%m-%dT%H:%M:%SZ")

    pull_path = pull_dir / "pull.md"
    pull_meta = {
        "type": "pull",
        "schema": 1,
        "id": pull_id,
        "url": export["prUrl"],
        "series": series,
        "title": None,
        "author": None,
        "fetched_at": fetched_at,
    }
    snapshot_path = pull_dir / "snapshots" / f"{head[:7]}.md"
    snapshot_meta = {
        "type": "snapshot",
        "schema": 1,
        "id": snapshot_id,
        "pull_id": pull_id,
        "head_sha": head,
        "base_sha": export.get("base"),
        "fetched_at": fetched_at,
    }

    existing, taken = read_existing_findings(pull_dir / "findings")
    findings = []
    for comment in export["comments"]:
        body = comment["body"].strip("\r\n")
        known = existing.get(comment["id"])
        if known is not None:
            action = "skip" if known[1] == body else "conflict"
            findings.append({"action": action, "origin_ref": comment["id"], "id": known[0], "title": finding_title(body)})
            continue
        finding_id = new_finding_id(moment, taken)
        meta = {
            "type": "finding",
            "schema": 1,
            "id": finding_id,
            "pull_id": pull_id,
            "snapshot_id": snapshot_id,
            "run_id": None,
            "origin": "human",
            "origin_ref": comment["id"],
            "title": finding_title(body),
            "body_hash": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "location": {
                "path": comment["path"],
                "start_line": comment["startLine"],
                "end_line": comment["endLine"],
                "side": comment["side"],
            },
            "confidence": "unknown",
            "theme_key": None,
            "norm_gap": None,
            "norm_ref": None,
            "dismissed_reason": None,
            "created_by": created_by,
            "created_at": comment["createdAt"],
        }
        findings.append(
            {
                "action": "create",
                "origin_ref": comment["id"],
                "id": finding_id,
                "title": meta["title"],
                "path": pull_dir / "findings" / finding_id / "finding.md",
                "text": render_record(meta, body),
            }
        )

    return {
        "pull_id": pull_id,
        "pull": {"path": pull_path, "text": render_record(pull_meta), "create": not pull_path.exists()},
        "snapshot": {"path": snapshot_path, "text": render_record(snapshot_meta), "create": not snapshot_path.exists()},
        "findings": findings,
    }


def write_new(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def apply_plan(plan):
    for key in ("pull", "snapshot"):
        if plan[key]["create"]:
            write_new(plan[key]["path"], plan[key]["text"])
    for finding in plan["findings"]:
        if finding["action"] == "create":
            write_new(finding["path"], finding["text"])


def report(plan, store, dry_run):
    verbs = {"create": "作成", "skip": "スキップ", "conflict": "衝突"}
    if dry_run:
        print("（dry-run）何も書きません。作る予定は次のとおりです。")
    print(f"PR  {plan['pull_id']}")
    for label, key in (("pull.md", "pull"), ("snapshot", "snapshot")):
        state = "作成" if plan[key]["create"] else "既存（変更しません）"
        print(f"{label}  {state}  {plan[key]['path'].relative_to(store)}")
    for finding in plan["findings"]:
        detail = f"{finding['id']}  {finding['origin_ref']}  {finding['title']}"
        if finding["action"] == "conflict":
            detail += "  既存の本文と違うため上書きしません"
        print(f"finding  {verbs[finding['action']]}  {detail}")
    counts = {action: sum(1 for f in plan["findings"] if f["action"] == action) for action in verbs}
    print(f"合計  作成 {counts['create']} 件 / スキップ {counts['skip']} 件 / 衝突 {counts['conflict']} 件")
    return counts["conflict"]


def main(argv=None):
    parser = argparse.ArgumentParser(description="pr-tour の JSON 書き出し v1 を、finding の記録として取り込みます。")
    parser.add_argument("--store", required=True, type=Path, help="記録の置き場所の根")
    parser.add_argument("--from", dest="source", required=True, help="pr-tour の JSON 書き出し")
    parser.add_argument("--series", default=None, help="pull の series（同じ取り組みのまとまり）")
    parser.add_argument("--created-by", default="unknown", help="finding の created_by")
    parser.add_argument("--dry-run", action="store_true", help="何も書かず、作る予定を表示する")
    args = parser.parse_args(argv)

    moment = datetime.now(timezone.utc)
    try:
        export = load_export(args.source)
        owner, repo, number = parse_pr_url(export["prUrl"])
        pull_dir = args.store / "pulls" / owner / repo / str(number)
        plan = build_plan(export, pull_dir, args.series, args.created_by, moment)
    except InputError as error:
        print(f"エラー: {error}", file=sys.stderr)
        return 2

    if not args.dry_run:
        apply_plan(plan)
    conflicts = report(plan, args.store, args.dry_run)
    return 1 if conflicts else 0


if __name__ == "__main__":
    sys.exit(main())
