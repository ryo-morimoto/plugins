// 地図の画面（map.html を描画したあとの DOM）を veriss にかける。
// usage: VERISS=<veriss の clone>/packages/veriss/src node veriss_map.mjs <dom.html> <part> <min> <max>
// part: header | axes | grid | cands（ページを部品に分ける。main の列の幅は中身に依存しないので、
//       もう片方の欄を空の箱にしても幅は変わらない。地図の欄の軸の札と表も、縦に並べているだけ）
// 出力: 1 行目に status と件数、続けて指摘の種類ごとの件数（JSON、--json）。
import fs from 'node:fs';
const V = process.env.VERISS.replace(/\/?$/, '/');
const {analyzeHTML} = await import(V + 'html.mjs');
const [file, part, min, max] = process.argv.slice(2);
const dom = fs.readFileSync(file, 'utf8');
let css = [...dom.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)].map(m => m[1]).join('\n');
let body = dom.match(/<body[^>]*>([\s\S]*)<\/body>/)[1].replace(/<script[\s\S]*?<\/script>/g, '');
// veriss の HTML の読み込みが扱わないものを、表示の同じものに置き換える（検査のためだけ）
body = body.replace(/<code(\s|>)/g, '<span data-was="code"$1').replace(/<\/code>/g, '</span>');
let n = 0;
body = body.replace(/<([a-z0-9]+)([^>]*?)\sstyle="([^"]*)"/g, (all, tag, attrs, style) => {
  const id = `vs-inline-${++n}`;
  css += `\n#${id} { ${style.replace(/&quot;/g, '"')} }`;
  return attrs.includes(' id="') ? all : `<${tag}${attrs} id="${id}"`;
});
const h0 = body.indexOf('<header'), h1 = body.indexOf('</header>') + 9, m0 = body.indexOf('<main'), m1 = body.lastIndexOf('</main>') + 7;
const main = body.slice(m0, m1), open = main.slice(0, main.indexOf('>') + 1);
const p1 = main.indexOf('<section class="panel"'), p2 = main.indexOf('<section class="panel"', p1 + 1), end = main.lastIndexOf('</main>');
const left = main.slice(p1, p2), right = main.slice(p2, end), empty = '<section class="panel"></section>';
const g0 = left.indexOf('<section class="grid"'), g1 = left.indexOf('</section>', g0) + 10, a0 = left.indexOf('<div id="axes">');
const leftPart = part === 'axes' ? left.slice(0, g0) + left.slice(g1) : left.slice(0, a0) + left.slice(g0);
body = part === 'header' ? body.slice(h0, h1) : open + (part === 'cands' ? empty + right : leftPart + empty) + '</main>';
const html = `<div class="veriss-root">${body.trim()}</div>`;
// 前提（信頼する内容の大きさ）: body の overflow-wrap: anywhere により、文字の箱はどこでも折り返せる。
// そのときの最小幅は最も幅の広い 1 文字で、ページで最大の文字（24px）以下。veriss は wrap と CSS の一致を自分で確かめる。
const text = {wrap: 'anywhere', minInlineSize: 24};
const boxes = Object.fromEntries(['div', 'span', 'h1', 'h2', 'h3', 'p', 'b', 'li', 'a', 'button'].map(t => [t, text]));
boxes['#grid'] = {overflow: 'scroll'};
let report;
for (;;) {
  try {
    report = analyzeHTML(html, {name: 'MapPage', css, viewport: {min: +min, max: +max}, boxes,
      scrollbars: [{name: 'overlay', inlineSize: 0, blockSize: 0}, {name: 'classic', inlineSize: 17, blockSize: 17}],
      ancestors: [{tag: 'html', lang: 'ja'}, {tag: 'body'}], accessibility: {contrast: 'AA'}, integrity: true});
    break;
  } catch (e) {
    const m = /does not match a box: (\S+)/.exec(e.message);
    if (!m) throw e;
    delete boxes[m[1]];  // 箱として存在しない要素の種類（親の文字に含まれる b, a など）は前提から外す
  }
}
const rows = [...(report.diagnostics ?? []), ...(report.integrity?.warnings ?? []), ...(report.accessibility?.warnings ?? [])];
const byCode = {};
for (const r of rows) byCode[r.code ?? r.rule ?? '?'] = (byCode[r.code ?? r.rule ?? '?'] ?? 0) + 1;
const sample = rows.find(r => r.code !== 'U_A11Y_TARGET_SIZE');
console.log(JSON.stringify({status: report.status, byCode, sample: sample ? `${sample.code} ${sample.path ?? ''} ${sample.message ?? ''}`.slice(0, 240) : null}));
