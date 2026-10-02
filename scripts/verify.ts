import { deepStrictEqual, ok, strictEqual } from 'node:assert';
import { readFileSync } from 'node:fs';
import { resolve as pathResolve } from 'node:path';
import { JSDOM } from 'jsdom';

// The engine uses DOM APIs (DOMParser/XMLSerializer); provide them under Node.
const dom = new JSDOM('<!doctype html><html><body></body></html>');
(globalThis as Record<string, unknown>).DOMParser = dom.window.DOMParser;
(globalThis as Record<string, unknown>).XMLSerializer = dom.window.XMLSerializer;

import { parseCss, type Project } from '../packages/model/src/index';
import {
  applyMatrix,
  assembleProject,
  cssToText,
  emitMultipageSvg,
  flatten,
  parseSvg,
  pathPoints,
  resolveId,
  transformMatrix,
  transformString,
} from '../packages/assembler/src/index';
import {
  buildPaletteTree,
  renderElementPreview,
  renderSheetBody,
  type PaletteNode,
} from '../editor/src/lib';

function main(): void {
  // CSS parsing
  deepStrictEqual(
    parseCss('.a { stroke: #000; fill: none; }\n.b { font-size: 5; }'),
    { a: { stroke: '#000', fill: 'none' }, b: { 'font-size': '5' } },
  );

  // Transform string order: translate -> rotate -> scale (position outermost)
  strictEqual(
    transformString({ x: 125, y: 0 }, [{ scale: { x: -1, y: 1 } }]),
    'translate(125 0) scale(-1 1)',
  );
  strictEqual(
    transformString({ x: 10, y: 20 }, [{ rotate: 90 }, { scale: { x: -1, y: 1 } }]),
    'translate(10 20) rotate(90) scale(-1 1)',
  );

  // Transform matrix + mirror (negative scale flips x)
  deepStrictEqual(applyMatrix(transformMatrix('scale(-1 1)'), 5, 3), [-5, 3]);

  // Path point extraction
  deepStrictEqual(pathPoints('M 0 0 L 10 0 L 10 10 Z'), [[0, 0], [10, 0], [10, 10]]);

  // Current project + source (source components referenced by id).
  const root = process.cwd();
  const project = JSON.parse(readFileSync(pathResolve(root, 'templates/project.json'), 'utf8')) as Project;
  const svgText = readFileSync(pathResolve(root, 'templates', project.source.href), 'utf8');
  const doc = parseSvg(svgText);

  strictEqual(project.source.href, 'feathers-elongated copy.svg');
  strictEqual(project.sheets.length, 35);

  // Id-based component resolution (namespace-agnostic).
  ok(resolveId(doc, 'P1-outline'), 'P1-outline resolves');
  ok(resolveId(doc, 'calibration'), 'calibration resolves');
  ok(resolveId(doc, 'B-align'), 'B-align resolves');
  strictEqual(resolveId(doc, 'does-not-exist'), null);

  // Editor palette exposes id-addressed components.
  const flattenPalette = (nodes: PaletteNode[]): PaletteNode[] =>
    nodes.flatMap((n) => [n, ...flattenPalette(n.children)]);
  const flatPalette = flattenPalette(buildPaletteTree(doc));
  ok(flatPalette.some((p) => p.id === 'P1-outline'), 'palette offers P1-outline');
  ok(flatPalette.some((p) => p.id === 'calibration'), 'palette offers calibration');

  // Preview renders the referenced component.
  const preview = renderElementPreview('P1-outline', doc);
  ok(preview && preview.includes('<svg') && preview.includes('<path'), 'element preview renders an svg');

  // Flatten resolves every referenced id.
  const flat = flatten(project, doc);
  strictEqual(flat.errors.length, 0, `flatten errors: ${JSON.stringify(flat.errors)}`);
  strictEqual(flat.sheets.length, 35);
  const coverFlat = flat.sheets.find((s) => s.title === 'cover');
  ok(coverFlat, 'cover flat sheet present');
  const body = renderSheetBody(coverFlat, project.styles, null);
  ok(body.includes('data-eid='), 'rendered sheet body has hit targets');

  // Full assembly
  const result = assembleProject(project, { doc });
  strictEqual(result.errors.length, 0, `errors: ${JSON.stringify(result.errors)}`);
  strictEqual(result.sheetCount, 35);
  ok(result.pages.length > 0, 'assembly produces pages');

  // Inkscape multipage SVG: one <inkscape:page> per physical page.
  const multi = emitMultipageSvg(result.pages, project.papers[0].trim, cssToText(project.styles));
  const pageDefs = multi.match(/<inkscape:page\b/g) ?? [];
  strictEqual(pageDefs.length, result.pages.length, 'one inkscape:page per physical page');

  console.log('ALL CHECKS PASSED');
  console.log(
    `sheets=${result.sheetCount} pages=${result.pages.length} tiledSheets=${result.tiledPages} warnings=${result.warnings.length}`,
  );
  for (const w of result.warnings.slice(0, 8)) console.log('  warn:', w.message);
  if (result.warnings.length > 8) console.log(`  ... and ${result.warnings.length - 8} more`);
}

main();
