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
  parseSvg,
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
 *  source SVG (instead of inlining their geometry). Text stays inline. */
function assembleUseBody(sheet: FlatSheet): string {
  const parts: string[] = [];
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

const pages: EnginePage[] = [];
let n = 0;
let sheetIdx = 0;
for (const sheet of sheets) {
  sheetIdx += 1;
  const result = tile(sheet.title, sheet.width, sheet.height, assembleUseBody(sheet), paper, `clip-s${sheetIdx}`);
  for (const page of result.pages) {
    n += 1;
    pages.push({
      fileName: `sheet-${String(n).padStart(3, '0')}.svg`,
      svg: '', // not used by emitMultipageSvg (only .body + page metadata are)
      body: page.body,
      sheetId: sheet.id,
      sheetTitle: sheet.title,
      tileIndex: page.tileIndex,
      cols: page.cols,
      rows: page.rows,
      transform: page.transform,
    });
  }
}

const outPath = pathResolve(root, 'templates/multipage-use.svg');
writeFileSync(outPath, emitMultipageSvg(pages, paper.trim, styleCss), 'utf8');
console.log(`wrote ${outPath} — ${pages.length} pages from ${sheets.length} sheets`);
