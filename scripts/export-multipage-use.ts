import { readFileSync, writeFileSync } from 'node:fs';
import { resolve as pathResolve } from 'node:path';
import { JSDOM } from 'jsdom';

// The assembler uses DOM APIs (DOMParser/XMLSerializer); provide them under Node.
const dom = new JSDOM('<!doctype html><html><body></body></html>');
(globalThis as Record<string, unknown>).DOMParser = dom.window.DOMParser;
(globalThis as Record<string, unknown>).XMLSerializer = dom.window.XMLSerializer;

import type { Project } from '../packages/model/src/types';
import {
  cssToText,
  emitMultipageSvg,
  esc,
  flatten,
  fmt,
  parseSvg,
  slug,
  tile,
  type EnginePage,
  type FlatSheet,
} from '../packages/assembler/src/index';

const root = process.cwd();
const project = JSON.parse(readFileSync(pathResolve(root, 'templates/project.json'), 'utf8')) as Project;

const doc = parseSvg(readFileSync(pathResolve(root, 'templates', project.source.href), 'utf8'));
// Encode the filename for the <use> href (handles the space in the filename).
const srcHref = encodeURI(project.source.href);

/** Build a sheet body where source components are `<use>` references into the
 *  source SVG (instead of inlining their geometry). Text stays inline. A white
 *  background rect (sheet width × height) is drawn first, behind everything. */
function assembleUseBody(sheet: FlatSheet): string {
  const parts: string[] = [
    `<rect x="0" y="0" width="${fmt(sheet.width)}" height="${fmt(sheet.height)}" fill="#ffffff" stroke="none"/>`,
  ];
  for (const el of sheet.elements) {
    if (el.kind === 'text') {
      parts.push(
        `<g transform="${esc(el.transform)}"><text x="0" y="0" class="${esc(el.styleId)}">${esc(el.text)}</text></g>`,
      );
    } else {
      parts.push(`<use href="${esc(`${srcHref}#${el.source}`)}" transform="${esc(el.transform)}"/>`);
    }
  }
  return parts.join('\n');
}

const { sheets, errors } = flatten(project, doc);
if (errors.length) {
  console.error('flatten errors:', JSON.stringify(errors, null, 2));
  process.exit(1);
}

const paper = project.papers.find((p) => p.id === (project.meta.defaultPaper ?? project.papers[0]?.id))
  ?? project.papers[0];
if (!paper) {
  console.error('no paper defined');
  process.exit(1);
}

// Component classes come from the source stylesheet; sheet-text classes come
// from project.styles. Source first so the project's `.outline` (solid) wins.
const sourceStyle = doc.querySelector('style')?.textContent ?? '';
const styleCss = `${sourceStyle}\n${cssToText(project.styles)}`;

const marginX = (paper.trim.width - paper.safeArea.width) / 2;
const marginY = (paper.trim.height - paper.safeArea.height) / 2;

const sheetGap = 20; // spacing between the off-canvas sheet definitions
const sheetRowY = paper.trim.height + 40; // below the pages → outside any page/view box
let sheetX = 0; // sheet definitions laid out left-to-right
const sheetGroups: string[] = [];

const pages: EnginePage[] = [];
let n = 0;
let hasClip = false;
let cropTicks: string | null = null;

for (const [sheetIndex, sheet] of sheets.entries()) {
  const sheetBody = assembleUseBody(sheet);
  const sheetGroupId = `sheet-${slug(sheet.title) || sheet.id}`;
  const sheetWrapId = `${sheetGroupId}-container`;

  // Off-canvas sheet definition: an editable <g id="sheet-<title>"> that the
  // pages <use>. The outer container positions it below the pages/view box; the
  // inner group carries no transform, so <use href="#…"> stays at sheet coords.
  // data-sort-order records the project's sheet order for the tile-sheets CLI.
  sheetGroups.push(
    `  <g id="${esc(sheetWrapId)}" transform="translate(${fmt(sheetX)} ${fmt(sheetRowY)})">\n    <g id="${esc(sheetGroupId)}" data-sort-order="${sheetIndex}">${sheetBody}</g>\n  </g>`,
  );
  sheetX += sheet.width + sheetGap;

  const result = tile(sheet.title, sheet.width, sheet.height, sheetBody, paper, 'clip');
  for (const page of result.pages) {
    n += 1;
    // Swap the inlined sheet body for a <use> of the off-canvas sheet group.
    let body = page.body.replace(
      `<g transform="${page.transform}">${sheetBody}</g>`,
      `<use href="#${esc(sheetGroupId)}" transform="${page.transform}"/>`,
    );
    // Don't emit the per-page clipPath def (identical on every tiled page):
    // reference a single shared `#clip` defined once below.
    if (body.includes('<clipPath')) {
      hasClip = true;
      body = body
        .replace(/<defs><clipPath id="clip-[^"]+"><rect [^>]*\/><\/clipPath><\/defs>\n?/, '')
        .replace(/clip-path="url\(#clip-[^)]*\)"/, 'clip-path="url(#clip)"');
    }
    // Same for the per-page corner-crop ticks: reference a shared `#crop-ticks`.
    body = body.replace(/<g>((?:<line class="crop" [^>]*\/>)+)<\/g>/, (_m, inner: string) => {
      cropTicks = cropTicks ?? inner;
      return '<use href="#crop-ticks"/>';
    });
    pages.push({
      fileName: `sheet-${String(n).padStart(3, '0')}.svg`,
      svg: '', // not used by emitMultipageSvg (only .body + page metadata are)
      body,
      sheetId: sheet.id,
      sheetTitle: sheet.title,
      tileIndex: page.tileIndex,
      cols: page.cols,
      rows: page.rows,
      transform: page.transform,
    });
  }
}

// Shared defs emitted once (instead of once per tiled page).
const defs: string[] = [];
if (hasClip) {
  defs.push(
    `      <clipPath id="clip"><rect x="${fmt(marginX)}" y="${fmt(marginY)}" width="${fmt(paper.safeArea.width)}" height="${fmt(paper.safeArea.height)}"/></clipPath>`,
  );
}
if (cropTicks) {
  defs.push(`      <g id="crop-ticks">${cropTicks}</g>`);
}

const outPath = pathResolve(root, 'templates/multipage-use.svg');
let svg = emitMultipageSvg(pages, paper.trim, styleCss);
if (defs.length) {
  svg = svg.replace('<defs\n     id="defs1" />', `<defs\n     id="defs1">\n${defs.join('\n')}\n    </defs>`);
}
// Insert the off-canvas sheet definitions after the style, before the pages.
const sheetsXml = sheetGroups.join('\n').split('\n').map((l) => (l ? '  ' + l : l)).join('\n');
svg = svg.replace('</style>\n', `</style>\n\n  <g id="sheets">\n${sheetsXml}\n  </g>\n`);
writeFileSync(outPath, svg, 'utf8');
console.log(`wrote ${outPath} — ${pages.length} pages from ${sheets.length} sheets`);
