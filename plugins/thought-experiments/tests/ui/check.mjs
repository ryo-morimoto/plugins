// 地図の画面（map.html）を veriss で、横方向と縦方向の両方について検査する。使い方と前提は README.md。
//
// 環境変数:
//   VERISS     veriss の packages/veriss（src/ と node_modules/ を持つディレクトリ）
//   FONT_JP    Noto Sans JP のフォントファイル（可変、OFL）
//   FONT_MONO  Noto Sans Mono のフォントファイル（可変、OFL）
//   CHROME     使う Chromium（省略時は Playwright が持つもの）
//   MAP        検査する map.html（既定: fixture/maps/all-states/map.html。先に thought_map.py render で生成する）
//
// 終了コード: 許していない指摘が 1 つでもあれば 1。
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';

const here = path.dirname(fileURLToPath(import.meta.url));
const V = path.resolve(process.env.VERISS);
const {analyzeHTML} = await import(pathToFileURL(path.join(V, 'src/html.mjs')));
const {loadTextMetrics} = await import(pathToFileURL(path.join(V, 'src/text-node.mjs')));
const {chromium} = createRequire(path.join(V, 'package.json'))('playwright');
const MAP = path.resolve(process.env.MAP ?? path.join(here, 'fixture/maps/all-states/map.html'));

const metrics = await loadTextMetrics({fonts: {
  'Noto Sans JP': {file: process.env.FONT_JP},
  'Noto Sans Mono': {file: process.env.FONT_MONO},
}});

// 1. ブラウザで描画し、文字を持つ箱ごとに、計算済みのフォントと表示される文字列を集めて id を付ける
async function snapshot(state) {
  const browser = await chromium.launch(process.env.CHROME ? {executablePath: process.env.CHROME} : {});
  const page = await browser.newPage({viewport: {width: 1400, height: 1000}});
  await page.goto(pathToFileURL(MAP).href + state);
  await page.waitForTimeout(300);
  const leaves = await page.evaluate(() => {
    const out = []; let n = 0;
    const hasText = el => [...el.childNodes].some(c => c.nodeType === 3 && c.textContent.trim());
    for (const el of document.body.querySelectorAll('*')) {
      if (['SCRIPT', 'STYLE'].includes(el.tagName) || !hasText(el)) continue;
      const cs = getComputedStyle(el);
      // 文の中の行内の要素（リンクなど）は、親の文字の一部として測る
      if (cs.display === 'inline' && el.parentElement && hasText(el.parentElement)) continue;
      if (!el.id) el.id = `vt-${++n}`;
      out.push({id: el.id, content: el.textContent.replace(/\s+/g, ' ').trim(), nowrap: cs.whiteSpace === 'nowrap',
        font: {family: cs.fontFamily.split(',')[0].trim().replace(/^["']|["']$/g, ''), size: parseFloat(cs.fontSize),
          lineHeight: parseFloat(cs.lineHeight), weight: parseInt(cs.fontWeight, 10)}});
    }
    return out;
  });
  const dom = await page.evaluate(() => document.documentElement.outerHTML);
  await browser.close();
  return {leaves, dom};
}

// 2. veriss に渡す断片を作る（<script> を除き、style 属性は id の規則に移し、<code> は表示の同じ <span> にする）
function fragment(dom, part) {
  let css = [...dom.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)].map(m => m[1]).join('\n');
  let body = dom.match(/<body[^>]*>([\s\S]*)<\/body>/)[1].replace(/<script[\s\S]*?<\/script>/g, '');
  body = body.replace(/<code(\s|>)/g, '<span data-was="code"$1').replace(/<\/code>/g, '</span>');
  let n = 0;
  body = body.replace(/<([a-z0-9]+)([^>]*?)\sstyle="([^"]*)"([^>]*)>/g, (all, tag, a1, style, a2) => {
    const attrs = a1 + a2, m = / id="([^"]+)"/.exec(attrs), id = m ? m[1] : `vs-inline-${++n}`;
    css += `\n#${id} { ${style.replace(/&quot;/g, '"')} }`;
    return `<${tag}${attrs}${m ? '' : ` id="${id}"`}>`;
  });
  // 部品に分ける: main の列の幅は中身に依存しないので、もう片方の欄を空の箱にしても幅は変わらない。
  // 地図の欄の中は、軸の札と表を縦に並べているだけ。
  const h0 = body.indexOf('<header'), h1 = body.indexOf('</header>') + 9, m0 = body.indexOf('<main'), m1 = body.lastIndexOf('</main>') + 7;
  const main = body.slice(m0, m1), open = main.slice(0, main.indexOf('>') + 1);
  const p1 = main.indexOf('<section class="panel"'), p2 = main.indexOf('<section class="panel"', p1 + 1), end = main.lastIndexOf('</main>');
  const left = main.slice(p1, p2), right = main.slice(p2, end), empty = '<section class="panel"></section>';
  const g0 = left.indexOf('<section class="grid"'), g1 = left.indexOf('</section>', g0) + 10, a0 = left.indexOf('<div id="axes">');
  const leftPart = part === 'axes' ? left.slice(0, g0) + left.slice(g1) : left.slice(0, a0) + left.slice(g0);
  body = part === 'header' ? body.slice(h0, h1) : open + (part === 'cands' ? empty + right : leftPart + empty) + '</main>';
  return {html: `<div class="veriss-root">${body.trim()}</div>`, css};
}

// 3. 文字の箱ごとに text の宣言を作る。veriss がフォントから幅と高さを導く。測れない文字列は宣言を外し、数える
function boxesFor(leaves, html) {
  // 地図の表は横にスクロールする。縦方向の検査では veriss が CSS（overflow-x: auto）から自分で扱うので、宣言は横方向のときだけ
  const boxes = html.includes(' id="grid"') && process.env.BLOCK === '0' ? {'#grid': {overflow: 'scroll'}} : {}, unmeasured = [], oneLine = [];
  for (const leaf of leaves) {
    if (!html.includes(` id="${leaf.id}"`)) continue;
    const text = {font: leaf.font, content: leaf.content};
    if (leaf.nowrap) {  // 折り返さないラベルは 1 行の幅で測る。収まらない幅は veriss が誤りにする
      try { metrics.measureText({font: leaf.font, text: leaf.content}); boxes[`#${leaf.id}`] = {wrap: 'nowrap', text}; }
      catch (e) { unmeasured.push(`#${leaf.id} ${JSON.stringify(leaf.content.slice(0, 40))}: ${e.message.slice(0, 120)}`); }
      continue;
    }
    try { metrics.breakLines({font: leaf.font, text: leaf.content, overflowWrap: 'anywhere'}); boxes[`#${leaf.id}`] = {wrap: 'anywhere', text}; continue; }
    catch (e) {
      // 行分割のモデルが扱わない文字（記号など）は、1 行に収まることを要求して測る。収まらない幅は veriss が誤りにする
      try { metrics.measureText({font: leaf.font, text: leaf.content}); boxes[`#${leaf.id}`] = {wrap: 'one-line', text}; oneLine.push(leaf.content); }
      catch (e2) { unmeasured.push(`#${leaf.id} ${JSON.stringify(leaf.content.slice(0, 40))}: ${e.message.slice(0, 100)} / ${e2.message.slice(0, 100)}`); }
    }
  }
  return {boxes, unmeasured, oneLine};
}

const want = (name, value) => !process.env[name] || process.env[name].split(',').includes(String(value));
// 幅の帯（既定は画面の切り替わり 600px、1000px と、その間で分ける）。BANDS=320-399,400-599 のように細かくできる
const BANDS = (process.env.BANDS ?? '320-599,600-999,1000-1299,1300-1600').split(',').map(b => b.split('-').map(Number));
// 画面の高さの範囲（既定 480–1200px）と、スクロールバーの太さ（既定は 0px と 17px の両方）
const [hMin, hMax = hMin] = (process.env.HEIGHT ?? '480-1200').split('-').map(Number);
const HEIGHT = {min: hMin, max: hMax};
const SCROLLBARS = [{name: 'overlay', inlineSize: 0, blockSize: 0}, {name: 'classic', inlineSize: 17, blockSize: 17}].filter(p => want('SCROLLBARS', p.name));
const ALLOWED = new Set(process.env.ALLOW ? process.env.ALLOW.split(',') : []);
let failed = false;
// 一部だけ回す: STATES=1,4,5 PARTS=header,axes,grid,cands RANGES=320,600,1000,1300
const pick = (name, all) => all.filter(x => want(name, x));
for (const state of ['', '#4', '#5'].filter(s => want('STATES', s ? s.slice(1) : '1'))) {
  const {leaves, dom} = await snapshot(state);
  for (const part of pick('PARTS', ['header', 'axes', 'grid', 'cands'])) {
    const {html, css} = fragment(dom, part);
    if (process.env.DUMP) fs.writeFileSync(`${process.env.DUMP}/${(state || '#1').slice(1)}-${part}.html`, html);
    const {boxes, unmeasured} = boxesFor(leaves, html);
    // フォントからの寸法は幅の帯によらないので、部品ごとに 1 回だけ導く
    const t1 = Date.now(); const resolvedBoxes = metrics.resolveBoxes(boxes);
    if (process.env.PROGRESS) console.error(`  ${state || '#1'} ${part} resolveBoxes ${Date.now() - t1}ms (${Object.keys(boxes).length} boxes)`);
    // BLOCK=0 なら横方向だけを検査する（速い。押せる範囲の大きさは判定不能になる）
    const analyze = (min, max) => analyzeHTML(html, {name: 'MapPage', css, boxes: resolvedBoxes,
      ...(process.env.BLOCK === '0' ? {viewport: {min, max}} : {block: true, viewport: {min, max, height: HEIGHT}}), scrollbars: SCROLLBARS,
      ancestors: [{tag: 'html', lang: 'ja'}, {tag: 'body'}], ...(process.env.A11Y === '0' ? {} : {accessibility: {contrast: 'AA', ...(process.env.A11Y ? {profile: process.env.A11Y} : {})}}), ...(process.env.INTEGRITY === '0' ? {} : {integrity: true})});
    for (const [min, max] of BANDS.filter(([a]) => want('RANGES', a))) {
      const label = `${state || '#1'} ${part} ${min}-${max}`;
      const queue = [[min, max]], counts = {}, bad = [], statuses = new Set(); let pieces = 0;
      try {
        while (queue.length) {
          const [a, b] = queue.shift(); const t0 = Date.now(); const report = analyze(a, b);
          if (process.env.PROGRESS) console.error(`  ${label} [${a}, ${b}] ${report.status} ${Date.now() - t0}ms`);
          const rows = [...(report.diagnostics ?? []), ...(report.integrity?.warnings ?? []), ...(report.accessibility?.warnings ?? [])];
          if (rows.some(r => r.code === 'U_LAYOUT_LIMIT') && b - a >= 2) {  // 作業量の上限: 帯を半分にして検査し直す（ほかの指摘は分けた帯で出し直す）
            const mid = Math.floor((a + b) / 2); queue.push([a, mid], [mid + 1, b]); continue;
          }
          pieces++; statuses.add(report.status);
          for (const r of rows) { counts[r.code ?? r.rule] = (counts[r.code ?? r.rule] ?? 0) + 1; if (!ALLOWED.has(r.code ?? r.rule)) bad.push(r); }
        }
      } catch (e) { console.log(`ERROR ${label}: ${e.message.slice(0, 200)}`); failed = true; continue; }
      const summary = `${[...statuses].join('/')} (${pieces} 帯)${Object.keys(counts).length ? ' ' + JSON.stringify(counts) : ''}`;
      if (bad.length || unmeasured.length) {
        failed = true; console.log(`NG ${label}: ${summary}`);
        for (const r of bad.slice(0, 3)) console.log(`   ${r.code ?? r.rule} ${r.path ?? ''} ${(r.message ?? '').slice(0, 200)}`);
        for (const u of unmeasured.slice(0, 3)) console.log(`   unmeasured ${u}`);
      } else console.log(`ok ${label}: ${summary}`);
    }
  }
}
process.exit(failed ? 1 : 0);
