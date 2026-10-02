import { readFileSync, writeFileSync } from 'node:fs';
import { basename, resolve as pathResolve } from 'node:path';
import { JSDOM } from 'jsdom';

// Node has no DOMParser/XMLSerializer; provide them via jsdom.
const dom = new JSDOM('<!doctype html><html><body></body></html>');
(globalThis as Record<string, unknown>).DOMParser = dom.window.DOMParser;
(globalThis as Record<string, unknown>).XMLSerializer = dom.window.XMLSerializer;

// ---------------------------------------------------------------------------
// Vendored from packages/assembler/src (util.ts, resolve.ts, emit.ts, tile.ts,
// multipage.ts) so this script is fully self-contained.
// ---------------------------------------------------------------------------

/** Format a number: up to 6 decimals, trailing zeros/dot stripped. */
function fmt(x: number): string {
  let s = x.toFixed(6);
  if (s.includes('.')) s = s.replace(/0+$/, '').replace(/\.$/, '');
  return s;
}

/** XML-escape text interpolated into an attribute or text node. */
function esc(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/** Slugify a title for an SVG id: keep `[A-Za-z0-9_-]`, collapse other runs to
 *  `-`, trim leading/trailing dashes. Returns '' when nothing survives. */
function slug(s: string): string {
  return s.trim().replace(/[^A-Za-z0-9_-]+/g, '-').replace(/^-+|-+$/g, '');
}

/** Parse SVG markup into a DOM Document. */
function parseSvg(markup: string): Document {
  const doc = new DOMParser().parseFromString(markup, 'application/xml');
  if (doc.getElementsByTagName('parsererror').length > 0) {
    throw new Error('source SVG failed to parse');
  }
  return doc;
}

interface Size {
  width: number;
  height: number;
}

interface Vec2 {
  x: number;
  y: number;
}

type Overlap = number | Vec2;

interface Paper {
  id: string;
  name: string;
  trim: Size;
  safeArea: Size;
  overlap: Overlap;
}

interface EnginePage {
  fileName: string;
  svg: string;
  body: string;
  sheetId: string;
  sheetTitle: string;
  tileIndex: number;
  cols: number;
  rows: number;
  transform: string;
}

// Physical-sheet CSS appended to the carried-over stylesheet on every page.
const CSS2 = '\n.crop { stroke: #999999; stroke-width: 0.25; }\n'
  + '.overlap { stroke: #999999; stroke-width: 0.15; stroke-dasharray: 2 2; fill: none; }\n'
  + '.note { font-family: sans-serif; fill: #555555; font-size: 4; text-anchor: middle; }\n';

const CROP_INSET = 5.0;

interface TiledPage {
  body: string;
  transform: string;
  tileIndex: number;
  cols: number;
  rows: number;
}

interface TileResult {
  pages: TiledPage[];
  cols: number;
  rows: number;
  offset: [number, number] | null;
}

function overlapPair(overlap: Paper['overlap']): [number, number] {
  if (typeof overlap === 'number') return [overlap, overlap];
  return [overlap.x, overlap.y];
}

function cornerTicks(marginX: number, marginY: number, safeW: number, safeH: number): string {
  const L = 5.0;
  const loX = marginX + CROP_INSET;
  const hiX = marginX + safeW - CROP_INSET;
  const loY = marginY + CROP_INSET;
  const hiY = marginY + safeH - CROP_INSET;
  const segs: string[] = [];
  for (const cx of [loX, hiX]) {
    for (const cy of [loY, hiY]) {
      const sx = cx === loX ? 1.0 : -1.0;
      const sy = cy === loY ? 1.0 : -1.0;
      segs.push(`<line class="crop" x1="${fmt(cx)}" y1="${fmt(cy)}" x2="${fmt(cx + sx * L)}" y2="${fmt(cy)}"/>`);
      segs.push(`<line class="crop" x1="${fmt(cx)}" y1="${fmt(cy)}" x2="${fmt(cx)}" y2="${fmt(cy + sy * L)}"/>`);
    }
  }
  return '<g>' + segs.join('') + '</g>';
}

function overlapMarks(
  c: number, r: number, cols: number, rows: number,
  marginX: number, marginY: number, safeW: number, safeH: number,
  overlapX: number, overlapY: number,
): string {
  const segs: string[] = [];
  if (c < cols - 1) {
    const x = marginX + safeW - overlapX;
    segs.push(`<line class="overlap" x1="${fmt(x)}" y1="${fmt(marginY)}" x2="${fmt(x)}" y2="${fmt(marginY + safeH)}"/>`);
  }
  if (c > 0) {
    const x = marginX + overlapX;
    segs.push(`<line class="overlap" x1="${fmt(x)}" y1="${fmt(marginY)}" x2="${fmt(x)}" y2="${fmt(marginY + safeH)}"/>`);
  }
  if (r < rows - 1) {
    const y = marginY + safeH - overlapY;
    segs.push(`<line class="overlap" x1="${fmt(marginX)}" y1="${fmt(y)}" x2="${fmt(marginX + safeW)}" y2="${fmt(y)}"/>`);
  }
  if (r > 0) {
    const y = marginY + overlapY;
    segs.push(`<line class="overlap" x1="${fmt(marginX)}" y1="${fmt(y)}" x2="${fmt(marginX + safeW)}" y2="${fmt(y)}"/>`);
  }
  return segs.length ? '<g>' + segs.join('') + '</g>' : '';
}

/** Map a sheet's logical area onto physical pages: one centered page when it
 *  fits the safe area, else a cols x rows grid with overlap marks. */
function tile(title: string, W: number, H: number, body: string, paper: Paper, idPrefix = 'clip'): TileResult {
  const trimW = paper.trim.width;
  const trimH = paper.trim.height;
  const safeW = paper.safeArea.width;
  const safeH = paper.safeArea.height;
  const [overlapX, overlapY] = overlapPair(paper.overlap);
  const marginX = (trimW - safeW) / 2;
  const marginY = (trimH - safeH) / 2;
  const strideX = safeW - overlapX;
  const strideY = safeH - overlapY;
  if (strideX <= 0 || strideY <= 0) throw new Error('overlap must be smaller than the safe area');

  const cols = W <= safeW ? 1 : Math.ceil((W - safeW) / strideX) + 1;
  const rows = H <= safeH ? 1 : Math.ceil((H - safeH) / strideY) + 1;

  const pages: TiledPage[] = [];
  if (cols === 1 && rows === 1) {
    const ox = marginX + (safeW - W) / 2;
    const oy = marginY + (safeH - H) / 2;
    const tr = `translate(${fmt(ox)} ${fmt(oy)})`;
    pages.push({ body: `<g transform="${tr}">${body}</g>`, transform: tr, tileIndex: 1, cols: 1, rows: 1 });
    return { pages, cols, rows, offset: [ox, oy] };
  }

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const tx = marginX - c * strideX;
      const ty = marginY - r * strideY;
      const tr = `translate(${fmt(tx)} ${fmt(ty)})`;
      const idx = r * cols + c + 1;
      const clipId = `${idPrefix}-${idx}`;
      const clip = `<defs><clipPath id="${clipId}"><rect x="${fmt(marginX)}" y="${fmt(marginY)}" width="${fmt(safeW)}" height="${fmt(safeH)}"/></clipPath></defs>`;
      const parts = [
        clip,
        `<g clip-path="url(#${clipId})">`,
        `<g transform="${tr}">${body}</g>`,
        '</g>',
        cornerTicks(marginX, marginY, safeW, safeH),
        overlapMarks(c, r, cols, rows, marginX, marginY, safeW, safeH, overlapX, overlapY),
        `<text class="note" x="${fmt(trimW / 2)}" y="${fmt(trimH - 2.5)}">${esc(title)} \u00b7 tile ${idx}/${cols * rows} \u00b7 ${cols}x${rows}</text>`,
      ];
      pages.push({ body: parts.join('\n'), transform: tr, tileIndex: idx, cols, rows });
    }
  }
  return { pages, cols, rows, offset: null };
}

interface MultipageOptions {
  gap?: number;
  label?: (page: EnginePage, index: number) => string;
  docName?: string;
}

const INKSCAPE_VERSION = '1.4 (86a8ad7, 2024-10-11)';

const NAMESPACES = [
  'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"',
  'xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"',
  'xmlns="http://www.w3.org/2000/svg"',
  'xmlns:svg="http://www.w3.org/2000/svg"',
].join('\n   ');

function defaultLabel(page: EnginePage): string {
  if (page.cols === 1 && page.rows === 1) return page.sheetTitle;
  return `${page.sheetTitle} \u00b7 tile ${page.tileIndex}/${page.cols * page.rows}`;
}

function pageId(page: EnginePage): string {
  const name = slug(page.sheetTitle) || page.sheetId;
  return page.cols === 1 && page.rows === 1
    ? `page-${name}`
    : `page-${name}-tile-${page.tileIndex}`;
}

/** Emit tiled pages as a single Inkscape multipage SVG document (pages laid out
 *  side by side; one `<inkscape:page>` per physical page). */
function emitMultipageSvg(
  pages: EnginePage[],
  trim: Size,
  styleCss: string,
  opts: MultipageOptions = {},
): string {
  const gap = opts.gap ?? 10;
  const n = pages.length;
  const totalW = n * trim.width + (n - 1) * gap;
  const totalH = trim.height;

  const pageDefs: string[] = [];
  const pageGroups: string[] = [];

  pages.forEach((page, i) => {
    const x = i * (trim.width + gap);
    const y = 0;
    const label = opts.label ? opts.label(page, i) : defaultLabel(page);
    pageDefs.push(
      `    <inkscape:page\n`
      + `       x="${fmt(x)}"\n`
      + `       y="${fmt(y)}"\n`
      + `       width="${fmt(trim.width)}"\n`
      + `       height="${fmt(trim.height)}"\n`
      + `       id="page${i + 1}"\n`
      + `       margin="5"\n`
      + `       bleed="0"\n`
      + `       inkscape:label="${esc(label)}" />`,
    );
    pageGroups.push(
      `  <g id="${esc(pageId(page))}" transform="translate(${fmt(x)} ${fmt(y)})">\n`
      + `    <rect x="0" y="0" width="${fmt(trim.width)}" height="${fmt(trim.height)}" fill="#ffffff"/>\n`
      + `${page.body}\n`
      + `  </g>`,
    );
  });

  const docName = opts.docName ?? 'sheets-multipage.svg';

  return `<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n`
    + `<!-- Created with Inkscape (http://www.inkscape.org/) -->\n\n`
    + `<svg\n`
    + `   width="${fmt(totalW)}mm"\n`
    + `   height="${fmt(totalH)}mm"\n`
    + `   viewBox="0 0 ${fmt(totalW)} ${fmt(totalH)}"\n`
    + `   version="1.1"\n`
    + `   id="svg1"\n`
    + `   inkscape:version="${INKSCAPE_VERSION}"\n`
    + `   sodipodi:docname="${esc(docName)}"\n`
    + `   ${NAMESPACES}>\n`
    + `  <sodipodi:namedview\n`
    + `     id="namedview1"\n`
    + `     pagecolor="#ffffff"\n`
    + `     bordercolor="#666666"\n`
    + `     borderopacity="1.0"\n`
    + `     inkscape:showpageshadow="2"\n`
    + `     inkscape:pageopacity="0.0"\n`
    + `     inkscape:pagecheckerboard="false"\n`
    + `     inkscape:deskcolor="#d1d1d1"\n`
    + `     inkscape:document-units="mm"\n`
    + `     showborder="true">\n`
    + pageDefs.join('\n') + `\n`
    + `  </sodipodi:namedview>\n`
    + `  <defs\n`
    + `     id="defs1" />\n`
    + `  <style type="text/css">${styleCss}${CSS2}</style>\n`
    + `  <g id="pages">\n`
    + pageGroups.join('\n').split('\n').map((l) => (l ? '  ' + l : l)).join('\n') + `\n`
    + `  </g>\n`
    + `</svg>\n`;
}

// ---------------------------------------------------------------------------
// Tiler
// ---------------------------------------------------------------------------

// usage: node dist/scripts/tile-sheets.js <sheets.svg> [trimWxH] [safeWxH] [overlap] [gap] [--out <path>]
//   trimWxH   e.g. "215.9x279.4" or "8.5x11in"   (default 215.9x279.4, portrait)
//   safeWxH   e.g. "205.9x269.4" or "8.1x10.6in" (default 205.9x269.4, portrait)
//   overlap   e.g. "12" or "0.5in"               (default 12)
//   gap       e.g. "10" or "0.4in"               (default 10)
//   Page size is always portrait; sheets are rotated 90° when that tiles better.
//   Units default to mm; "in" is converted to mm.
const argv = process.argv.slice(2);

// Separate positional arguments from --flags (and their values).
const positional: string[] = [];
const flags: Record<string, string | undefined> = {};
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a.startsWith('--')) {
    const name = a.slice(2);
    const val = argv[i + 1];
    if (val !== undefined && !val.startsWith('--')) {
      flags[name] = val;
      i += 1;
    } else {
      flags[name] = undefined;
    }
  } else {
    positional.push(a);
  }
}

const input = positional[0];
if (!input) {
  console.error('usage: node dist/scripts/tile-sheets.js <sheets.svg> [trimWxH] [safeWxH] [overlap] [gap] [--out <path>]');
  process.exit(1);
}

const MM_PER_IN = 25.4;

/** Round to 6 decimal places so inch→mm conversions yield clean mm values. */
function round6(x: number): number {
  return Math.round(x * 1e6) / 1e6;
}

/** Parse a distance like "12", "12mm", or "0.5in" → millimetres. */
function dist(text: string): number {
  const m = text.trim().match(/^([-+]?(?:\d+\.?\d*|\.\d+))\s*(mm|in)?$/i);
  if (!m) throw new Error(`bad distance "${text}" (expected a number with optional mm/in)`);
  const value = Number(m[1]);
  const unit = (m[2] ?? 'mm').toLowerCase();
  return round6(unit === 'in' ? value * MM_PER_IN : value);
}

/** Parse "WxH" with an optional trailing unit ("mm" default; "in" → mm). */
function size(text: string): Size {
  const t = text.trim();
  const unitMatch = t.match(/(mm|in)$/i);
  const unit = (unitMatch?.[1] ?? 'mm').toLowerCase();
  const dimsText = (unitMatch ? t.slice(0, -unitMatch[1].length) : t).trim();
  const parts = dimsText.split(/[x×]/i);
  if (parts.length !== 2) throw new Error(`bad size "${text}" (expected WxH with optional mm/in)`);
  const w = Number(parts[0]);
  const h = Number(parts[1]);
  if (!Number.isFinite(w) || !Number.isFinite(h)) throw new Error(`bad size "${text}" (expected WxH with optional mm/in)`);
  const factor = unit === 'in' ? MM_PER_IN : 1;
  return { width: round6(w * factor), height: round6(h * factor) };
}

const root = process.cwd();
const inPath = pathResolve(root, input);
const trim = size(positional[1] ?? '215.9x279.4');
const safeArea = size(positional[2] ?? '205.9x269.4');
const overlap = dist(positional[3] ?? '12');
const gap = dist(positional[4] ?? '10');
const outPath = pathResolve(root, flags['out'] ?? input.replace(/\.svg$/i, '') + '-multipage.svg');

const paper: Paper = { id: 'paper', name: 'paper', trim, safeArea, overlap };

// --- read sheet definitions from the input SVG ---
const doc = parseSvg(readFileSync(inPath, 'utf8'));
// Sheets are referenced relative to the output file (assumed co-located).
const href = encodeURI(basename(inPath));

interface SheetDef {
  id: string;
  width: number;
  height: number;
}

/** Find `<g id="sheet-…">` groups carrying a background `<rect>` (sheet bounds).
 *  Container/wrapper groups have no direct rect child and are skipped. Sheets
 *  are ordered by their `data-sort-order` attribute (ascending); sheets without
 *  one come last in document order. */
function findSheets(rootDoc: Document): SheetDef[] {
  const raw: { id: string; width: number; height: number; order: number; index: number }[] = [];
  for (const g of Array.from(rootDoc.querySelectorAll('g[id^="sheet-"]'))) {
    const rect = Array.from(g.children).find((c) => c.localName === 'rect');
    if (!rect) continue;
    const w = Number(rect.getAttribute('width'));
    const h = Number(rect.getAttribute('height'));
    if (!Number.isFinite(w) || !Number.isFinite(h)) continue;
    const orderAttr = g.getAttribute('data-sort-order');
    const parsed = orderAttr === null ? Number.POSITIVE_INFINITY : Number(orderAttr);
    raw.push({
      id: g.getAttribute('id')!,
      width: w,
      height: h,
      order: Number.isFinite(parsed) ? parsed : Number.POSITIVE_INFINITY,
      index: raw.length,
    });
  }
  raw.sort((a, b) => (a.order - b.order) || (a.index - b.index));
  return raw.map(({ id, width, height }) => ({ id, width, height }));
}

const sheets = findSheets(doc);
if (sheets.length === 0) {
  console.error(`no <g id="sheet-…"> groups (with a <rect> child) found in ${inPath}`);
  process.exit(1);
}

// Carry the sheets' own stylesheet over so their classes resolve in the output
// (CSS does not cascade across an external <use> reference).
const styleCss = doc.querySelector('style')?.textContent ?? '';

// --- tile each sheet into pages that <use> the external sheet group ---
const marginX = (trim.width - safeArea.width) / 2;
const marginY = (trim.height - safeArea.height) / 2;

const pages: EnginePage[] = [];
let n = 0;
let hasClip = false;
let cropTicks: string | null = null;

for (const sheet of sheets) {
  const title = sheet.id.replace(/^sheet-/, '');
  const useRef = `<use href="${esc(`${href}#${sheet.id}`)}"/>`;

  // Try both orientations; rotate the sheet 90° if the portrait page tiles better that way.
  const normal = tile(title, sheet.width, sheet.height, useRef, paper, 'clip');
  const rotatedBody = `<g transform="translate(${fmt(sheet.height)} 0) rotate(90)">${useRef}</g>`;
  const rotated = tile(title, sheet.height, sheet.width, rotatedBody, paper, 'clip');
  const result = rotated.pages.length < normal.pages.length ? rotated : normal;

  for (const page of result.pages) {
    n += 1;
    let pageBody = page.body;
    if (pageBody.includes('<clipPath')) {
      hasClip = true;
      pageBody = pageBody
        .replace(/<defs><clipPath id="clip-[^"]+"><rect [^>]*\/><\/clipPath><\/defs>\n?/, '')
        .replace(/clip-path="url\(#clip-[^)]*\)"/, 'clip-path="url(#clip)"');
    }
    pageBody = pageBody.replace(/<g>((?:<line class="crop" [^>]*\/>)+)<\/g>/, (_m, inner: string) => {
      cropTicks = cropTicks ?? inner;
      return '<use href="#crop-ticks"/>';
    });
    pages.push({
      fileName: `sheet-${String(n).padStart(3, '0')}.svg`,
      svg: '',
      body: pageBody,
      sheetId: sheet.id,
      sheetTitle: title,
      tileIndex: page.tileIndex,
      cols: page.cols,
      rows: page.rows,
      transform: page.transform,
    });
  }
}

// --- emit ---
const defs: string[] = [];
if (hasClip) {
  defs.push(
    `      <clipPath id="clip"><rect x="${fmt(marginX)}" y="${fmt(marginY)}" width="${fmt(safeArea.width)}" height="${fmt(safeArea.height)}"/></clipPath>`,
  );
}
if (cropTicks) {
  defs.push(`      <g id="crop-ticks">${cropTicks}</g>`);
}

let svg = emitMultipageSvg(pages, trim, styleCss, { gap });
if (defs.length) {
  svg = svg.replace('<defs\n     id="defs1" />', `<defs\n     id="defs1">\n${defs.join('\n')}\n    </defs>`);
}
writeFileSync(outPath, svg, 'utf8');
console.log(`wrote ${outPath} — ${pages.length} pages from ${sheets.length} sheets`);
