import {
  cssToText,
  elementBBox,
  esc,
  fmt,
  resolveId,
  serialize,
} from '../../packages/assembler/src/index';
import type { FlatSheet } from '../../packages/assembler/src/flatten';
import type { CssDecl } from '../../packages/model/src/types';

/** A node in the collapsible source-component tree (keyed by element id). */
export interface PaletteNode {
  id: string;
  label: string;
  children: PaletteNode[];
}

const SKIP_TAGS = new Set(['defs', 'style', 'title', 'namedview', 'metadata']);

function buildNode(el: Element): PaletteNode | null {
  if (SKIP_TAGS.has(el.localName) || SKIP_TAGS.has(el.tagName)) return null;
  const id = el.getAttribute('id');
  if (!id) return null;
  const children: PaletteNode[] = [];
  for (const child of Array.from(el.children)) {
    const sub = buildNode(child);
    if (sub) children.push(sub);
  }
  return { id, label: id, children };
}

/** Build the source SVG's id-addressed components as a collapsible tree. */
export function buildPaletteTree(doc: Document): PaletteNode[] {
  const roots: PaletteNode[] = [];
  const docEl = doc.documentElement;
  if (docEl) {
    for (const child of Array.from(docEl.children)) {
      const node = buildNode(child);
      if (node) roots.push(node);
    }
  }
  return roots;
}

/** Render a small self-contained SVG preview of a source component (scaled to fit). */
export function renderElementPreview(id: string, doc: Document): string | null {
  const el = resolveId(doc, id);
  if (!el) return null;
  const bbox = elementBBox('', [el]);
  if (!bbox) return null;
  const [x0, y0, x1, y1] = bbox;
  const w = x1 - x0;
  const h = y1 - y0;
  if (w < 1e-6 || h < 1e-6) return null;
  const pad = Math.max(w, h) * 0.05;
  const style = doc.querySelector('style')?.textContent ?? '';
  const inner = serialize(el);
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
