#!/usr/bin/env python3
"""テキスト中の GitHub 固定リンクを、ローカルの git リポジトリで解決し、行の存在と本文を示す。"""

import argparse
import json
import re
import subprocess
import sys
from urllib.parse import unquote

NOTE = "関連性は確認していません。行の存在と本文だけを示します"

CANDIDATE = re.compile(r"https://github\.com/[A-Za-z0-9\-._~:/?#\[\]@!$&()*+,;=%]+")
BLOB = re.compile(
    r"https://github\.com/(?P<owner>[^/#?]+)/(?P<repo>[^/#?]+)/blob/(?P<ref>[^/#?]+)/(?P<path>[^#?]+)"
    r"(?:\?[^#]*)?(?:#(?P<fragment>.*))?"
)
FRAGMENT = re.compile(r"L(\d+)(?:C\d+)?(?:-L(\d+)(?:C\d+)?)?")
FULL_SHA = re.compile(r"[0-9a-fA-F]{40}")


def trim_url(url):
    while url:
        last = url[-1]
        if last in ".,;:!?*":
            url = url[:-1]
        elif last == ")" and url.count(")") > url.count("("):
            url = url[:-1]
        elif last == "]" and url.count("]") > url.count("["):
            url = url[:-1]
        else:
            break
    return url


def extract_links(text):
    links = []
    seen = set()
    for match in CANDIDATE.finditer(text):
        url = trim_url(match.group(0))
        if url in seen:
            continue
        blob = BLOB.fullmatch(url)
        if blob is None:
            continue
        seen.add(url)
        start = end = None
        valid_range = True
        fragment = blob.group("fragment")
        if fragment is not None:
            parsed = FRAGMENT.fullmatch(fragment)
            if parsed is None:
                valid_range = False
            else:
                start = int(parsed.group(1))
                end = int(parsed.group(2)) if parsed.group(2) else start
        links.append(
            {
                "url": url,
                "owner": blob.group("owner"),
                "repo": blob.group("repo"),
                "ref": blob.group("ref"),
                "path": unquote(blob.group("path")),
                "start": start,
                "end": end,
                "valid_range": valid_range,
            }
        )
    return links


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True)


def is_git_repository(repo):
    return git(repo, "rev-parse", "--git-dir").returncode == 0


def file_lines_at(repo, sha, path):
    result = git(repo, "cat-file", "-t", f"{sha}:{path}")
    if result.returncode != 0 or result.stdout.strip() != b"blob":
        return None
    content = git(repo, "show", f"{sha}:{path}")
    if content.returncode != 0:
        return None
    lines = content.stdout.decode("utf-8", errors="replace").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return [line.rstrip("\r") for line in lines]


def resolve(link, repo, expect, max_lines):
    result = {
        "url": link["url"],
        "owner": link["owner"],
        "repo": link["repo"],
        "ref": link["ref"],
        "path": link["path"],
        "start": link["start"],
        "end": link["end"],
        "status": "ok",
        "file_lines": None,
        "lines": [],
        "truncated": False,
    }
    if expect is not None and f"{link['owner']}/{link['repo']}".lower() != expect.lower():
        result["status"] = "repo_mismatch"
        return result
    if not FULL_SHA.fullmatch(link["ref"]):
        result["status"] = "not_pinned"
        return result
    sha = link["ref"].lower()
    if git(repo, "cat-file", "-e", f"{sha}^{{commit}}").returncode != 0:
        result["status"] = "commit_missing"
        return result
    lines = file_lines_at(repo, sha, link["path"])
    if lines is None:
        result["status"] = "path_missing"
        return result
    result["file_lines"] = len(lines)
    start, end = link["start"], link["end"]
    if not link["valid_range"]:
        result["status"] = "range_out_of_bounds"
        return result
    if start is None:
        return result
    if start < 1 or start > end or end > len(lines):
        result["status"] = "range_out_of_bounds"
        return result
    selected = lines[start - 1 : end]
    if len(selected) > max_lines:
        selected = selected[:max_lines]
        result["truncated"] = True
    result["lines"] = selected
    return result


def format_text(results, summary):
    out = [NOTE, ""]
    if summary["total"] == 0:
        out.append("固定リンクは見つかりませんでした。")
        return "\n".join(out) + "\n"
    for item in results:
        out.append(f"[{item['status']}] {item['url']}")
        location = item["path"]
        if item["start"] is not None:
            location += f":{item['start']}" if item["start"] == item["end"] else f":{item['start']}-{item['end']}"
        out.append(f"  {item['owner']}/{item['repo']}@{item['ref'][:7]} {location}")
        if item["file_lines"] is not None:
            out.append(f"  ファイルの行数 {item['file_lines']}")
        for offset, line in enumerate(item["lines"]):
            out.append(f"  {item['start'] + offset:>5} | {line}")
        if item["truncated"]:
            out.append(f"  （先頭 {len(item['lines'])} 行だけを表示）")
        out.append("")
    out.append(f"合計 {summary['total']} 件、ok {summary['ok']} 件、問題あり {summary['problems']} 件")
    return "\n".join(out) + "\n"


def read_inputs(files):
    if not files:
        files = ["-"]
    parts = []
    for name in files:
        if name == "-":
            parts.append(sys.stdin.buffer.read().decode("utf-8"))
        else:
            with open(name, "rb") as handle:
                parts.append(handle.read().decode("utf-8"))
    return "\n".join(parts)


def positive_int(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("1 以上の整数を指定してください")
    return number


def owner_repo(value):
    if not re.fullmatch(r"[^/\s]+/[^/\s]+", value):
        raise argparse.ArgumentTypeError("OWNER/REPO の形で指定してください")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description="GitHub の固定リンクをローカルの git で解決する")
    parser.add_argument("--repo", required=True, help="解決に使う git リポジトリのディレクトリ")
    parser.add_argument("--expect", type=owner_repo, help="期待する OWNER/REPO")
    parser.add_argument("--max-lines", type=positive_int, default=8, help="本文として示す最大の行数")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("files", nargs="*", metavar="FILE")
    args = parser.parse_args(argv)

    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    if not is_git_repository(args.repo):
        print(f"エラー: --repo {args.repo} は git リポジトリではありません", file=sys.stderr)
        return 2
    try:
        text = read_inputs(args.files)
    except OSError as error:
        print(f"エラー: 入力を読めません: {error}", file=sys.stderr)
        return 2
    except UnicodeDecodeError as error:
        print(f"エラー: 入力が UTF-8 ではありません: {error}", file=sys.stderr)
        return 2

    results = [resolve(link, args.repo, args.expect, args.max_lines) for link in extract_links(text)]
    ok = sum(1 for item in results if item["status"] == "ok")
    summary = {"total": len(results), "ok": ok, "problems": len(results) - ok}

    if args.format == "json":
        print(json.dumps({"note": NOTE, "links": results, "summary": summary}, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(format_text(results, summary))
    return 1 if summary["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
