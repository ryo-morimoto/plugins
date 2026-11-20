#!/usr/bin/env python3
"""下書きの Markdown を、文や語句にコメントを付けられる、1 つの HTML ファイルにする。

コメントは「Copy for AI」で、Markdown として書き出せる。外部のサーバーには何も送らない。
"""

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path

SENTENCE_END = "。！？"
CLOSERS = "）」』"
INLINE = re.compile(r"(`[^`]+`)|(\*\*[^*]+\*\*)|(\[[^\]]+\]\([^)\s]+\))")
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
LIST_ITEM = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.*)$")
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
SUMMARY = re.compile(r"^<summary>(.*)</summary>$")


def esc(text):
    return html.escape(text, quote=True)


def inline(text):
    out = []
    position = 0
    for match in INLINE.finditer(text):
        out.append(esc(text[position : match.start()]))
        token = match.group(0)
        if token.startswith("`"):
            out.append(f"<code>{esc(token[1:-1])}</code>")
        elif token.startswith("**"):
            out.append(f"<strong>{inline(token[2:-2])}</strong>")
        else:
            label, url = LINK.fullmatch(token).groups()
            if re.match(r"https?://", url):
                out.append(f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{inline(label)}</a>')
            else:
                out.append(esc(token))
        position = match.end()
    out.append(esc(text[position:]))
    return "".join(out)


def split_sentences(text):
    sentences = []
    start = 0
    in_code = False
    depth = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char == "`":
            in_code = not in_code
        elif not in_code:
            if char == "[":
                depth += 1
            elif char == "]":
                depth = max(0, depth - 1)
        index += 1
        if char in SENTENCE_END and not in_code and depth == 0:
            while index < len(text) and text[index] in CLOSERS:
                index += 1
            sentences.append(text[start:index])
            start = index
    if text[start:].strip():
        sentences.append(text[start:])
    return sentences


def commentable(text, line):
    parts = []
    for sentence in split_sentences(text):
        body = sentence.strip()
        if not body:
            parts.append(esc(sentence))
            continue
        lead = sentence[: len(sentence) - len(sentence.lstrip())]
        parts.append(f'{esc(lead)}<span class="s" data-line="{line}" data-raw="{esc(body)}">{inline(body)}</span>')
    return "".join(parts)


def render_blocks(lines, first_line):
    out = []
    paragraph = []
    paragraph_line = first_line
    stack = []

    def flush_paragraph():
        if paragraph:
            out.append(f"<p>{commentable(' '.join(paragraph), paragraph_line)}</p>")
            paragraph.clear()

    def close_lists(to_depth=0):
        while len(stack) > to_depth:
            out.append(f"</li></{stack.pop()[1]}>")

    for offset, raw in enumerate(lines):
        number = first_line + offset
        stripped = raw.strip()
        if not stripped:
            flush_paragraph()
            close_lists()
            continue
        if stripped == "<details>":
            flush_paragraph()
            close_lists()
            out.append("<details open>")
            continue
        if stripped == "</details>":
            flush_paragraph()
            close_lists()
            out.append("</details>")
            continue
        summary = SUMMARY.match(stripped)
        if summary:
            flush_paragraph()
            close_lists()
            out.append(f"<summary>{commentable(summary.group(1), number)}</summary>")
            continue
        item = LIST_ITEM.match(raw)
        if item:
            flush_paragraph()
            indent = len(item.group(1).expandtabs(2))
            tag = "ol" if item.group(2)[0].isdigit() else "ul"
            while stack and stack[-1][0] > indent:
                out.append(f"</li></{stack.pop()[1]}>")
            if stack and stack[-1][0] == indent:
                out.append("</li><li>")
            else:
                out.append(f"<{tag}><li>")
                stack.append((indent, tag))
            out.append(commentable(item.group(3), number))
            continue
        if stack and raw.startswith(" "):
            out.append(" " + commentable(stripped, number))
            continue
        close_lists()
        heading = HEADING.match(stripped)
        if heading:
            flush_paragraph()
            level = min(len(heading.group(1)) + 1, 6)
            out.append(f"<h{level}>{commentable(heading.group(2), number)}</h{level}>")
            continue
        if not paragraph:
            paragraph_line = number
        paragraph.append(stripped)
    flush_paragraph()
    close_lists()
    return "\n".join(out)


def strip_front_matter(lines):
    if lines and lines[0] == "---" and "---" in lines[1:]:
        end = lines.index("---", 1)
        return [""] * (end + 1) + lines[end + 1 :]
    return lines


def split_drafts(lines, fallback_title):
    """`## ` の見出しごとに分ける。見出しが 1 つも無ければ、全体を 1 つの下書きとする。"""
    starts = [index for index, line in enumerate(lines) if line.startswith("## ")]
    if not starts:
        return [(fallback_title, 0, lines)]
    drafts = []
    if any(line.strip() for line in lines[: starts[0]]):
        drafts.append((fallback_title, 0, lines[: starts[0]]))
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        drafts.append((lines[start][3:].strip(), start + 1, lines[start + 1 : end]))
    return drafts


def render_page(source, file_name, title):
    lines = strip_front_matter(source.split("\n"))
    sections = []
    for index, (heading, first_index, body) in enumerate(split_drafts(lines, file_name), start=1):
        sections.append(
            f'<section class="draft" data-draft="{index}" data-title="{esc(heading)}">'
            f'<h2><span class="s" data-line="{first_index}" data-raw="{esc(heading)}">{inline(heading)}</span></h2>\n'
            f"{render_blocks(body, first_index + 1)}\n</section>"
        )
    meta = json.dumps(
        {"file": file_name, "hash": hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]},
        ensure_ascii=False,
    ).replace("<", "\\u003c")
    return (
        PAGE.replace("__TITLE__", esc(title))
        .replace("__FILE__", esc(file_name))
        .replace("__META__", meta)
        .replace("__DRAFTS__", "\n".join(sections))
    )


PAGE = r"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root { --bg:#fbfbfa; --fg:#1f2328; --muted:#656d76; --line:#d0d7de; --panel:#f3f4f2; --accent:#0b6bcb; --hover:#fff4cc; --mark:#ffe58a; --btn:#0b6bcb; --btnfg:#fff; --code:#eceeed; }
@media (prefers-color-scheme: dark) { :root { --bg:#16181b; --fg:#e6e8ea; --muted:#98a1ab; --line:#30363d; --panel:#1d2024; --accent:#6cb2ff; --hover:#3a3320; --mark:#6b5a12; --btn:#2f81f7; --btnfg:#fff; --code:#262a2e; } }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font:16px/1.75 -apple-system,BlinkMacSystemFont,"Hiragino Sans","Noto Sans JP",sans-serif; }
header { position:sticky; top:0; z-index:5; display:flex; flex-wrap:wrap; gap:8px 16px; align-items:center; padding:10px 16px; background:var(--bg); border-bottom:1px solid var(--line); }
header h1 { font-size:16px; margin:0; }
header .file { color:var(--muted); font-size:13px; }
header .spacer { flex:1; }
button { font:inherit; cursor:pointer; }
.btn { border:1px solid var(--line); background:var(--panel); color:var(--fg); border-radius:6px; padding:4px 12px; font-size:14px; }
.btn.primary { background:var(--btn); color:var(--btnfg); border-color:var(--btn); }
.layout { display:grid; grid-template-columns:minmax(0,1fr) 340px; gap:24px; max-width:1200px; margin:0 auto; padding:16px; }
@media (max-width: 860px) { .layout { grid-template-columns:1fr; } }
.draft { margin:0 0 32px; padding:8px 0 8px 36px; border-bottom:1px solid var(--line); }
.draft h2 { font-size:17px; margin:8px 0 12px; color:var(--muted); }
.draft p { margin:12px 0; }
.draft ul, .draft ol { margin:8px 0; padding-left:24px; }
.draft summary { cursor:pointer; font-weight:600; margin:8px 0; }
.draft details { margin:12px 0; padding:0 12px; border:1px solid var(--line); border-radius:6px; }
code { background:var(--code); padding:1px 5px; border-radius:4px; font:0.9em ui-monospace,SFMono-Regular,Menlo,monospace; }
a { color:var(--accent); }
.s { border-radius:3px; }
.s.focus { background:var(--hover); }
.s.has-c { background:var(--hover); box-shadow:0 1px 0 var(--mark); }
.s.has-c::after { content:" [" attr(data-n) "]"; font-size:12px; color:var(--accent); user-select:none; }
.s.flash { outline:2px solid var(--accent); }
::highlight(rv-sel) { background:var(--mark); }
#hoverbtn, #selbtn { position:fixed; z-index:10; border:0; border-radius:14px; background:var(--btn); color:var(--btnfg); font-size:13px; padding:3px 10px; box-shadow:0 1px 4px rgba(0,0,0,.3); }
#hoverbtn { width:28px; height:28px; padding:0; border-radius:50%; font-size:15px; }
#editor { position:fixed; z-index:20; width:min(420px, calc(100vw - 24px)); background:var(--bg); border:1px solid var(--line); border-radius:8px; padding:12px; box-shadow:0 6px 24px rgba(0,0,0,.35); }
#editor .quote { margin:0 0 8px; padding:4px 8px; border-left:3px solid var(--accent); color:var(--muted); font-size:13px; max-height:7em; overflow:auto; white-space:pre-wrap; }
#editor textarea { width:100%; min-height:90px; font:inherit; font-size:15px; background:var(--panel); color:var(--fg); border:1px solid var(--line); border-radius:6px; padding:6px 8px; resize:vertical; }
#editor .row { display:flex; gap:8px; justify-content:flex-end; margin-top:8px; }
#panel { position:sticky; top:64px; align-self:start; max-height:calc(100vh - 80px); overflow:auto; }
#panel h2 { font-size:15px; margin:8px 0; }
.c { margin:0 0 12px; padding:8px 10px; border:1px solid var(--line); border-radius:8px; background:var(--panel); }
.c .head { display:flex; justify-content:space-between; gap:8px; font-size:12px; color:var(--muted); cursor:pointer; }
.c blockquote { margin:6px 0; padding:2px 8px; border-left:3px solid var(--accent); font-size:13px; color:var(--muted); white-space:pre-wrap; }
.c textarea { width:100%; min-height:60px; font:inherit; font-size:14px; background:var(--bg); color:var(--fg); border:1px solid var(--line); border-radius:6px; padding:4px 6px; resize:vertical; }
.c .del { border:0; background:none; color:var(--muted); font-size:12px; text-decoration:underline; }
.empty { color:var(--muted); font-size:14px; }
#outwrap { max-width:1200px; margin:0 auto; padding:0 16px 32px; }
#out { width:100%; min-height:240px; font:13px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace; background:var(--panel); color:var(--fg); border:1px solid var(--line); border-radius:6px; padding:8px; }
#toast { position:fixed; right:16px; bottom:16px; z-index:30; background:var(--fg); color:var(--bg); padding:8px 14px; border-radius:6px; font-size:14px; }
.hint { color:var(--muted); font-size:13px; }
[hidden] { display:none !important; }
</style>
</head>
<body>
<header>
  <h1>下書きのレビュー</h1>
  <span class="file">__FILE__</span>
  <span class="hint">文にカーソルを合わせて 💬、文をクリック、または語句を選んでコメントします</span>
  <span class="spacer"></span>
  <span id="count" class="hint">コメント 0 件</span>
  <button class="btn" id="toggleout" type="button">出力を表示</button>
  <button class="btn primary" id="copy" type="button">Copy for AI</button>
</header>
<div class="layout">
  <main id="drafts">
__DRAFTS__
  </main>
  <aside id="panel"><h2>コメント</h2><div id="list"></div></aside>
</div>
<div id="outwrap" hidden><textarea id="out" readonly></textarea></div>
<button id="hoverbtn" type="button" hidden aria-label="この文にコメント">💬</button>
<button id="selbtn" type="button" hidden>選んだ語句にコメント</button>
<div id="editor" hidden>
  <div class="quote" id="eq"></div>
  <textarea id="et" placeholder="コメント（Cmd/Ctrl + Enter で保存、Esc で取り消し）"></textarea>
  <div class="row"><button class="btn" id="ecancel" type="button">取り消し</button><button class="btn primary" id="esave" type="button">保存</button></div>
</div>
<div id="toast" hidden></div>
<script type="application/json" id="meta">__META__</script>
<script>
(() => {
  const meta = JSON.parse(document.getElementById('meta').textContent);
  const KEY = 'draft-review:' + meta.hash;
  const $ = (id) => document.getElementById(id);
  const sentences = [...document.querySelectorAll('.s')];
  sentences.forEach((el, i) => { el.dataset.sid = String(i); });
  let comments = [];
  let editing = null;
  let hovered = null;
  let hideTimer = null;
  let switchTimer = null;

  const load = () => { try { const v = JSON.parse(localStorage.getItem(KEY) || '[]'); return Array.isArray(v) ? v : []; } catch (e) { return []; } };
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(comments)); } catch (e) { /* 保存できなくても、画面の動きは変えない */ } };
  const draftOf = (el) => el.closest('.draft');
  const byId = (sid) => sentences[Number(sid)];
  const order = (a, b) => (Number(a.sid) - Number(b.sid)) || (a.start - b.start);

  function rangeOf(el, quote) {
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    const nodes = []; let text = '';
    for (let n = walker.nextNode(); n; n = walker.nextNode()) { nodes.push([n, text.length]); text += n.nodeValue; }
    const at = text.indexOf(quote);
    if (at < 0) return null;
    const find = (pos) => { for (let i = nodes.length - 1; i >= 0; i--) { if (nodes[i][1] <= pos) return [nodes[i][0], pos - nodes[i][1]]; } return null; };
    const a = find(at), b = find(at + quote.length - (quote.length ? 1 : 0));
    if (!a || !b) return null;
    const r = document.createRange();
    r.setStart(a[0], a[1]); r.setEnd(b[0], b[1] + 1);
    return r;
  }

  function paint() {
    sentences.forEach((el) => { el.classList.remove('has-c'); el.removeAttribute('data-n'); });
    const sorted = [...comments].sort(order);
    sorted.forEach((c, i) => {
      c.n = i + 1;
      const el = byId(c.sid);
      if (!el) return;
      el.classList.add('has-c');
      el.dataset.n = (el.dataset.n ? el.dataset.n + ',' : '') + c.n;
    });
    if (window.CSS && CSS.highlights && window.Highlight) {
      const ranges = sorted.filter((c) => c.quote !== c.sentence).map((c) => { const el = byId(c.sid); return el ? rangeOf(el, c.quote) : null; }).filter(Boolean);
      CSS.highlights.set('rv-sel', new Highlight(...ranges));
    }
    $('count').textContent = 'コメント ' + comments.length + ' 件';
    renderList(sorted);
    $('out').value = buildMarkdown(sorted);
  }

  function renderList(sorted) {
    const list = $('list');
    list.textContent = '';
    if (!sorted.length) { const p = document.createElement('p'); p.className = 'empty'; p.textContent = 'まだコメントはありません。'; list.append(p); return; }
    sorted.forEach((c) => {
      const box = document.createElement('div'); box.className = 'c';
      const head = document.createElement('div'); head.className = 'head';
      const left = document.createElement('span'); left.textContent = '[' + c.n + '] ' + c.draftTitle;
      const del = document.createElement('button'); del.className = 'del'; del.type = 'button'; del.textContent = '削除';
      del.addEventListener('click', (e) => { e.stopPropagation(); comments = comments.filter((x) => x.id !== c.id); save(); paint(); });
      head.append(left, del);
      head.addEventListener('click', () => { const el = byId(c.sid); if (!el) return; el.scrollIntoView({ block: 'center', behavior: 'smooth' }); el.classList.add('flash'); setTimeout(() => el.classList.remove('flash'), 1200); });
      const q = document.createElement('blockquote'); q.textContent = c.quote;
      const t = document.createElement('textarea'); t.value = c.text;
      t.addEventListener('input', () => { c.text = t.value; save(); $('out').value = buildMarkdown([...comments].sort(order)); });
      box.append(head, q, t); list.append(box);
    });
  }

  function buildMarkdown(sorted) {
    const out = ['# 下書きへのレビューコメント', '', '対象のファイル: ' + meta.file, '各コメントは、対象（下書きの文、または選んだ語句）と、コメントの組です。「元の行」は、対象のファイルの行番号です。', ''];
    if (!sorted.length) { out.push('（コメントはありません）'); return out.join('\n'); }
    let current = null;
    sorted.forEach((c) => {
      if (c.draft !== current) { current = c.draft; out.push('## ' + c.draftTitle, ''); }
      out.push('### [' + c.n + '] 元の行 ' + c.line, '');
      out.push('対象の文:', ...c.sentence.split('\n').map((l) => '> ' + l), '');
      if (c.quote !== c.sentence) out.push('選んだ語句:', ...c.quote.split('\n').map((l) => '> ' + l), '');
      out.push('コメント:', c.text.trim() ? c.text.trim() : '（未記入）', '');
    });
    return out.join('\n').replace(/\n+$/, '\n');
  }

  function place(el, x, y) {
    const w = el.offsetWidth, h = el.offsetHeight;
    el.style.left = Math.max(8, Math.min(x, innerWidth - w - 8)) + 'px';
    el.style.top = Math.max(8, Math.min(y, innerHeight - h - 8)) + 'px';
  }

  function openEditor(target, quote, rect) {
    editing = { sid: target.dataset.sid, quote, sentence: target.dataset.raw, line: Number(target.dataset.line) };
    $('eq').textContent = quote;
    $('et').value = '';
    if (hovered !== target) { clearFocus(); hovered = target; target.classList.add('focus'); }
    $('editor').hidden = false;
    place($('editor'), rect.left, rect.bottom + 8);
    $('et').focus();
    $('hoverbtn').hidden = true; $('selbtn').hidden = true;
  }

  function commit() {
    if (!editing) return;
    const text = $('et').value.trim();
    if (text) {
      const d = draftOf(byId(editing.sid));
      const el = byId(editing.sid);
      const start = el.textContent.indexOf(editing.quote);
      comments.push({ id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6), sid: editing.sid, start: Math.max(0, start), draft: d.dataset.draft, draftTitle: d.dataset.title, line: editing.line, sentence: editing.sentence, quote: editing.quote, text });
      save(); paint();
    }
    closeEditor();
  }
  function closeEditor() { editing = null; $('editor').hidden = true; clearFocus(); }

  const SWITCH_DELAY = 200;
  const NEAR = 80;
  let mouse = { x: -1, y: -1 };
  let hold = null;
  const inside = (r, x, y) => !!r && x >= r.left && x <= r.right && y >= r.top && y <= r.bottom;
  const near = (r, x, y) => !!r && Math.max(r.left - x, 0, x - r.right) <= NEAR && Math.max(r.top - y, 0, y - r.bottom) <= NEAR;

  function clearFocus() {
    clearTimeout(hideTimer); clearTimeout(switchTimer);
    if (hovered) hovered.classList.remove('focus');
    hovered = null; hold = null;
    $('hoverbtn').hidden = true;
  }

  function focusOn(el) {
    if (hovered === el) return;
    if (hovered) hovered.classList.remove('focus');
    hovered = el; el.classList.add('focus');
    const rects = el.getClientRects();
    const last = rects[rects.length - 1];
    const b = $('hoverbtn'); b.hidden = false;
    place(b, last.right - b.offsetWidth / 2, last.top - b.offsetHeight - 2);
    const br = b.getBoundingClientRect();
    const pad = 6;
    const tail = Math.max(last.left, last.right - 40);
    hold = {
      left: Math.min(tail, br.left) - pad, right: Math.max(last.right, br.right) + pad,
      top: Math.min(last.top, br.top) - pad, bottom: Math.max(last.bottom, br.bottom) + pad,
    };
  }

  document.addEventListener('mousemove', (e) => { mouse = { x: e.clientX, y: e.clientY }; });
  document.addEventListener('mouseover', (e) => {
    mouse = { x: e.clientX, y: e.clientY };
    if (!$('editor').hidden) return;
    if (inside(hold, e.clientX, e.clientY)) { clearTimeout(hideTimer); clearTimeout(switchTimer); return; }
    const el = e.target.closest && e.target.closest('.s');
    if (!el) return;
    clearTimeout(hideTimer); clearTimeout(switchTimer);
    if (!hovered) { focusOn(el); return; }
    if (el === hovered) return;
    if (!near(hold, e.clientX, e.clientY)) { focusOn(el); return; }
    switchTimer = setTimeout(() => {
      if (!$('editor').hidden || inside(hold, mouse.x, mouse.y)) return;
      const at = document.elementFromPoint(mouse.x, mouse.y);
      const now = at && at.closest && at.closest('.s');
      if (now) focusOn(now);
    }, SWITCH_DELAY);
  });
  document.addEventListener('mouseout', () => {
    if (!$('editor').hidden) return;
    clearTimeout(hideTimer);
    hideTimer = setTimeout(() => { if (!inside(hold, mouse.x, mouse.y)) clearFocus(); }, 300);
  });
  addEventListener('scroll', () => { if ($('editor').hidden) clearFocus(); }, { passive: true });
  addEventListener('resize', () => { if ($('editor').hidden) clearFocus(); });
  $('hoverbtn').addEventListener('click', () => {
    if (!hovered) return;
    openEditor(hovered, hovered.dataset.raw, hovered.getBoundingClientRect());
  });
  document.addEventListener('click', (e) => {
    if (!$('editor').hidden) return;
    const t = e.target;
    if (!t.closest || t.closest('a, button, summary, textarea, header, #panel, #editor')) return;
    const el = t.closest('.s');
    const sel = getSelection();
    if (!el || (sel && !sel.isCollapsed)) return;
    openEditor(el, el.dataset.raw, el.getBoundingClientRect());
  });

  function selectionTarget() {
    const sel = getSelection();
    if (!sel || sel.isCollapsed || !sel.rangeCount) return null;
    const range = sel.getRangeAt(0);
    const start = range.startContainer.parentElement && range.startContainer.parentElement.closest('.s');
    const end = range.endContainer.parentElement && range.endContainer.parentElement.closest('.s');
    if (!start || start !== end) return null;
    const quote = sel.toString().trim();
    return quote ? { el: start, quote, rect: range.getBoundingClientRect() } : null;
  }
  document.addEventListener('mouseup', () => setTimeout(() => {
    if (!$('editor').hidden) return;
    const t = selectionTarget();
    const b = $('selbtn');
    if (!t) { b.hidden = true; return; }
    b.hidden = false; b._t = t;
    place(b, t.rect.left, t.rect.bottom + 6);
  }, 0));
  $('selbtn').addEventListener('mousedown', (e) => e.preventDefault());
  $('selbtn').addEventListener('click', () => { const t = $('selbtn')._t; if (t) openEditor(t.el, t.quote, t.rect); });

  $('esave').addEventListener('click', commit);
  $('ecancel').addEventListener('click', closeEditor);
  $('et').addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeEditor();
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); commit(); }
  });

  const toast = (msg) => { const t = $('toast'); t.textContent = msg; t.hidden = false; setTimeout(() => { t.hidden = true; }, 2200); };
  $('copy').addEventListener('click', async () => {
    const text = $('out').value;
    try { await navigator.clipboard.writeText(text); toast('コピーしました'); return; } catch (e) { /* 次の方法へ */ }
    $('outwrap').hidden = false; $('out').select();
    try { toast(document.execCommand('copy') ? 'コピーしました' : '下の欄から、コピーしてください'); } catch (e) { toast('下の欄から、コピーしてください'); }
  });
  $('toggleout').addEventListener('click', () => { const w = $('outwrap'); w.hidden = !w.hidden; $('toggleout').textContent = w.hidden ? '出力を表示' : '出力を隠す'; });

  comments = load().filter((c) => byId(c.sid) && byId(c.sid).dataset.raw === c.sentence);
  paint();
})();
</script>
</body>
</html>
"""


def main(argv=None):
    parser = argparse.ArgumentParser(description="下書きの Markdown から、文や語句にコメントできる HTML を作ります。")
    parser.add_argument("source", type=Path, help="下書きの Markdown（`## 下書き N` で区切ったファイル、または rev-NNN.md）")
    parser.add_argument("--out", required=True, type=Path, help="書き出す HTML のパス")
    parser.add_argument("--title", default="下書きのレビュー", help="HTML のタイトル")
    args = parser.parse_args(argv)
    try:
        source = args.source.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        print(f"エラー: {args.source} を読めません: {error}", file=sys.stderr)
        return 2
    page = render_page(source, args.source.name, args.title)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(page)
    print(f"書き出しました: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
