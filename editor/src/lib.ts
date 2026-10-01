import {
  cssToText,
  elementBBox,
  esc,
  fmt,
  parseSvg,
  resolve,
  serialize,
} from '../../packages/assembler/src/index';
import type { FlatSheet } from '../../packages/assembler/src/flatten';
import type { CssDecl, Project } from '../../packages/model/src/types';

// Cache parsed source docs by id so drag/edits don't re-parse the source SVG.
const docCache = new Map<string, Document>();

export function sourceDocs(project: Project): Map<string, Document> {
  const map = new Map<string, Document>();
  for (const s of project.sources) {
    let doc = docCache.get(s.id);
    if (!doc) {
      doc = parseSvg(s.svg);
      docCache.set(s.id, doc);
    }
    map.set(s.id, doc);
  }
  return map;
}

/** A node in the collapsible source-element tree. */
export interface PaletteNode {
  sourceId: string;
  tag: string;
  id: string | null;
  label: string;
  selector: string;
  children: PaletteNode[];
}

const SHAPE_TAGS = new Set(['path', 'line', 'circle', 'ellipse', 'rect', 'polygon', 'polyline', 'text']);
const SKIP_TAGS = new Set(['defs', 'style', 'title', 'namedview', 'metadata']);

function buildNode(el: Element, sourceId: string, parentSelector: string | null): PaletteNode | null {
  const tag = el.localName;
  if (SKIP_TAGS.has(tag)) return null;
  const id = el.getAttribute('id');
  const selector = id
    ? `//${tag}[@id="${id}"]`
    : parentSelector
      ? `${parentSelector}/${tag}`
      : `//${tag}`;

  const node: PaletteNode = { sourceId, tag, id, label: id ?? tag, selector, children: [] };
  if (tag !== 'g') return node;

  // Nested groups become child nodes; distinct direct shape tags become one
  // aggregated leaf each (a selector like /path resolves to every path child).
  const childTags = new Set<string>();
  for (const child of Array.from(el.children)) {
    if (child.localName === 'g') {
      const sub = buildNode(child, sourceId, selector);
      if (sub) node.children.push(sub);
    } else if (SHAPE_TAGS.has(child.localName)) {
      childTags.add(child.localName);
    }
  }
  for (const t of childTags) {
    node.children.push({ sourceId, tag: t, id: null, label: t, selector: `${selector}/${t}`, children: [] });
  }
  return node;
}

/** Build the source SVG's element hierarchy as a collapsible tree. */
export function buildPaletteTree(project: Project): PaletteNode[] {
  const roots: PaletteNode[] = [];
  for (const src of project.sources) {
    const svgEl = parseSvg(src.svg).documentElement;
    if (!svgEl) continue;
    for (const child of Array.from(svgEl.children)) {
      const node = buildNode(child, src.id, null);
      if (node) roots.push(node);
    }
  }
  return roots;
}

/** Render a small self-contained SVG preview of a source selector (scaled to fit). */
export function renderElementPreview(project: Project, sourceId: string, selector: string): string | null {
  const doc = sourceDocs(project).get(sourceId);
  if (!doc) return null;
  const els = resolve(doc, selector);
  if (els.length === 0) return null;
  const bbox = elementBBox('', els);
  if (!bbox) return null;
  const [x0, y0, x1, y1] = bbox;
  const w = x1 - x0;
  const h = y1 - y0;
  if (w < 1e-6 || h < 1e-6) return null;
  const pad = Math.max(w, h) * 0.05;
  const style = doc.querySelector('style')?.textContent ?? '';
  const inner = els.map((e) => serialize(e)).join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${fmt(x0 - pad)} ${fmt(y0 - pad)} ${fmt(w + 2 * pad)} ${fmt(h + 2 * pad)}">`
    + `<style>${style}</style>${inner}</svg>`;
}

/** Build the inner SVG for a sheet's drawing area. Elements get data-eid hit
 *  targets; the selected element is marked data-sel for the CSS selection outline. */
export function renderSheetBody(
  sheet: FlatSheet,
  styles: Record<string, CssDecl>,
  selectedId: string | null,
): string {
  const parts: string[] = [`<style>${cssToText(styles)}</style>`];
  parts.push(
    `<rect x="0" y="0" width="${fmt(sheet.width)}" height="${fmt(sheet.height)}" fill="#ffffff" stroke="#999" stroke-width="0.3"/>`,
  );
  for (const el of sheet.elements) {
    const sel = el.id === selectedId ? ' data-sel="1"' : '';
    if (el.kind === 'text') {
      parts.push(
        `<g data-eid="${el.id}"${sel} transform="${esc(el.transform)}"><text x="0" y="0" class="${esc(el.styleId)}">${esc(el.text)}</text></g>`,
      );
    } else {
      const inner = el.elements.map((e) => serialize(e)).join('');
      parts.push(`<g data-eid="${el.id}"${sel} transform="${esc(el.transform)}">${inner}</g>`);
    }
  }
  return parts.join('\n');
}
