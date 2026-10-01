import { deepStrictEqual, ok, strictEqual } from 'node:assert';
import { readFileSync } from 'node:fs';
import { resolve as pathResolve } from 'node:path';
import { JSDOM } from 'jsdom';

// The engine uses DOM APIs (DOMParser/XMLSerializer); provide them under Node.
const dom = new JSDOM('<!doctype html><html><body></body></html>');
(globalThis as Record<string, unknown>).DOMParser = dom.window.DOMParser;
(globalThis as Record<string, unknown>).XMLSerializer = dom.window.XMLSerializer;

import { importLayoutYaml, parseCss } from '../packages/model/src/index';
import {
  applyMatrix,
  assembleProject,
  flatten,
  parseSvg,
  pathPoints,
  resolve,
  transformMatrix,
  transformString,
} from '../packages/assembler/src/index';
import {
  buildPalette,
  computeHandles,
  renderSheetBody,
  resizeTransform,
  type ResizeHandle,
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

  // Migration
  const root = process.cwd();
  const yamlText = readFileSync(pathResolve(root, 'templates/layout.yaml'), 'utf8');
  const svgText = readFileSync(pathResolve(root, 'templates/feathers-aggregate.svg'), 'utf8');
  const project = importLayoutYaml(yamlText, { 'feathers-aggregate.svg': svgText });

  strictEqual(project.sheets.length, 35);
  strictEqual(Object.keys(project.styles).length, 12);
  strictEqual(project.papers.length, 1);
  strictEqual(project.sheets[0].title, 'cover');

  const p1 = project.sheets.find((s) => s.title === 'P1');
  ok(p1, 'P1 sheet present');
  const firstEl = p1.elements[0];
  ok(firstEl.kind === 'source', 'first P1 element is a source');
  if (firstEl.kind === 'source') {
    strictEqual(firstEl.sourceSelector, '//g[@id="P1"]/path');
    deepStrictEqual(firstEl.transform, { scale: { x: -1, y: 1 } });
  }

  // Selector resolution (namespace-agnostic, mirrors legacy strip_ns)
  const doc = parseSvg(svgText);
  strictEqual(resolve(doc, '//g[@id="P1"]/path').length, 1);
  strictEqual(resolve(doc, '//g[@id="assembly-template"]/g').length, 1);
  strictEqual(resolve(doc, '//g[@id="calibration-ruler-metric"]').length, 1);
  strictEqual(resolve(doc, '//g[@id="does-not-exist"]').length, 0);

  // Editor palette + sheet rendering (non-UI editor logic)
  const palette = buildPalette(project);
  ok(palette.some((p) => p.selector === '//g[@id="P1"]/path'), 'palette offers the P1/path selector');
  ok(palette.some((p) => p.selector === '//g[@id="calibration-ruler-metric"]'), 'palette offers a group selector');
  const sourcesMap = new Map(project.sources.map((s) => [s.id, parseSvg(s.svg)]));
  const flatSheets = flatten(project, sourcesMap).sheets;
  const coverFlat = flatSheets.find((s) => s.title === 'cover');
  ok(coverFlat, 'cover flat sheet present');
  const body = renderSheetBody(coverFlat, project.styles, null);
  ok(body.includes('data-eid='), 'rendered sheet body has hit targets');
  ok(body.includes('<line'), 'rendered body includes copied source geometry');

  const p1Flat = flatSheets.find((s) => s.title === 'P1');
  ok(p1Flat, 'P1 flat sheet present');
  const srcEl = p1Flat.elements.find((e) => e.kind === 'source');
  ok(srcEl, 'P1 has a source element');
  if (srcEl) {
    const selBody = renderSheetBody(p1Flat, project.styles, srcEl.id);
    ok(selBody.includes('data-handle='), 'selected source element renders resize handles');
  }

  // Calibration ruler is a <g> of <line>s — its bbox must be walkable, so it gets handles.
  const ruler = coverFlat.elements.find((e) => e.kind === 'source' && e.selector.includes('calibration-ruler-metric'));
  ok(ruler, 'metric ruler source element present');
  if (ruler) {
    const rh = computeHandles(ruler, project.styles);
    ok(rh && rh.length === 4, 'ruler (group of lines) computes 4 handles');
  }

  // Text elements get resize handles too.
  const titleText = coverFlat.elements.find((e) => e.kind === 'text');
  ok(titleText, 'cover has a text element');
  if (titleText) {
    const th = computeHandles(titleText, project.styles);
    ok(th && th.length === 4, 'text element computes 4 handles');
    const tbody = renderSheetBody(coverFlat, project.styles, titleText.id);
    ok(tbody.includes('data-handle='), 'selected text renders resize handles');
  }

  // Resize math: drag the br corner of a 10x10 element (anchor at origin) to 20,20.
  const h: ResizeHandle = { key: 'br', x: 10, y: 10, dlx: 10, dly: 10, alx: 0, aly: 0, ax: 0, ay: 0 };
  const r1 = resizeTransform(h, { x: 20, y: 20 }, 0, { x: 1, y: 1 }, false);
  deepStrictEqual(r1.position, { x: 0, y: 0 });
  deepStrictEqual(r1.scale, { x: 2, y: 2 });
  const r2 = resizeTransform(h, { x: 20, y: 20 }, 0, { x: 1, y: 1 }, true);
  ok(Math.abs(r2.scale.x - 2) < 1e-9 && Math.abs(r2.scale.y - 2) < 1e-9, 'uniform resize keeps aspect');
  deepStrictEqual(r2.position, { x: 0, y: 0 });

  // Full assembly
  const result = assembleProject(project);
  strictEqual(result.errors.length, 0, `errors: ${JSON.stringify(result.errors)}`);
  strictEqual(result.sheetCount, 35);
  const p1Pages = result.pages.filter((p) => p.sheetTitle === 'P1');
  strictEqual(p1Pages.length, 2, 'P1 tiles into 2 physical pages');
  strictEqual(p1Pages[0].cols, 1);
  strictEqual(p1Pages[0].rows, 2);
  // A fitting sheet stays on one page.
  const cover = result.pages.find((p) => p.sheetTitle === 'cover');
  ok(cover, 'cover page present');
  strictEqual(cover.cols, 1);
  strictEqual(cover.rows, 1);
  // Tiled pages carry the clipPath defs (correct clipping, unlike the legacy bug).
  ok(p1Pages[0].svg.includes('<clipPath id="clip">'), 'tiled page emits clip defs');

  console.log('ALL CHECKS PASSED');
  console.log(
    `sheets=${result.sheetCount} pages=${result.pages.length} tiledSheets=${result.tiledPages} warnings=${result.warnings.length}`,
  );
  for (const w of result.warnings.slice(0, 8)) console.log('  warn:', w.message);
  if (result.warnings.length > 8) console.log(`  ... and ${result.warnings.length - 8} more`);
}

main();
