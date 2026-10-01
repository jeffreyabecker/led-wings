import {
  applyMatrix,
  cssToText,
  elementBBox,
  esc,
  fmt,
  parseSvg,
  resolve,
  serialize,
  transformMatrix,
  type Matrix,
} from '../../packages/assembler/src/index';
import type { FlatElement, FlatSheet } from '../../packages/assembler/src/flatten';
import type { CssDecl, Project, Vec2 } from '../../packages/model/src/types';

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

export type HandleKey = 'tl' | 'tr' | 'bl' | 'br';

/** One resize handle: its current sheet-space position, the local-space corner
 *  it drags, and the diagonally-opposite corner (the fixed anchor). */
export interface ResizeHandle {
  key: HandleKey;
  x: number;
  y: number;
  dlx: number;
  dly: number;
  alx: number;
  aly: number;
  ax: number;
  ay: number;
}

function apply(m: Matrix, x: number, y: number): Vec2 {
  const [px, py] = applyMatrix(m, x, y);
  return { x: px, y: py };
}

/** Estimate a text element's local bbox (centered at the origin), from its
 *  style's font-size. Approximate — good enough for resize handles. */
function textLocalBBox(
  text: string,
  styleId: string,
  styles: Record<string, CssDecl>,
): [number, number, number, number] | null {
  const fs = parseFloat(styles[styleId]?.['font-size'] ?? '5');
  if (!Number.isFinite(fs) || fs <= 0) return null;
  const h = fs;
  const w = text.length * fs * 0.55;
  return [-w / 2, -h / 2, w / 2, h / 2];
}

function localBBoxFor(
  el: FlatElement,
  styles: Record<string, CssDecl>,
): [number, number, number, number] | null {
  if (el.kind === 'source') return elementBBox('', el.elements);
  return textLocalBBox(el.text, el.styleId, styles);
}

function transformedBBox(
  local: [number, number, number, number],
  m: Matrix,
): [number, number, number, number] {
  const [lx0, ly0, lx1, ly1] = local;
  const pts = [apply(m, lx0, ly0), apply(m, lx1, ly0), apply(m, lx0, ly1), apply(m, lx1, ly1)];
  const xs = pts.map((p) => p.x);
  const ys = pts.map((p) => p.y);
  return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
}

/** Compute the four corner resize handles, always placed at the corners of the
 *  selection box (the axis-aligned bbox of the transformed geometry). Each handle
 *  also records the nearest local corner so resize keeps the opposite corner fixed. */
export function computeHandles(el: FlatElement, styles: Record<string, CssDecl>): ResizeHandle[] | null {
  const local = localBBoxFor(el, styles);
  if (!local) return null;
  const [lx0, ly0, lx1, ly1] = local;
  if (Math.abs(lx1 - lx0) < 1e-6 || Math.abs(ly1 - ly0) < 1e-6) return null;

  const m = transformMatrix(el.transform);
  const localCorners = [
    { lx: lx0, ly: ly0, p: apply(m, lx0, ly0) },
    { lx: lx1, ly: ly0, p: apply(m, lx1, ly0) },
    { lx: lx0, ly: ly1, p: apply(m, lx0, ly1) },
    { lx: lx1, ly: ly1, p: apply(m, lx1, ly1) },
  ];
  const xs = localCorners.map((c) => c.p.x);
  const ys = localCorners.map((c) => c.p.y);

  // Selection box corners (same box the selection highlight uses).
  const box: Record<HandleKey, Vec2> = {
    tl: { x: Math.min(...xs), y: Math.min(...ys) },
    tr: { x: Math.max(...xs), y: Math.min(...ys) },
    bl: { x: Math.min(...xs), y: Math.max(...ys) },
    br: { x: Math.max(...xs), y: Math.max(...ys) },
  };
  const opposite: Record<HandleKey, HandleKey> = { tl: 'br', tr: 'bl', bl: 'tr', br: 'tl' };

  const nearest = (p: Vec2) =>
    localCorners.reduce((best, c) =>
      Math.hypot(c.p.x - p.x, c.p.y - p.y) < Math.hypot(best.p.x - p.x, best.p.y - p.y) ? c : best,
    );

  return (Object.keys(box) as HandleKey[]).map((key) => {
    const pos = box[key];
    const anchorPos = box[opposite[key]];
    const dragged = nearest(pos);
    const anchor = nearest(anchorPos);
    return {
      key,
      x: pos.x,
      y: pos.y,
      dlx: dragged.lx,
      dly: dragged.ly,
      alx: anchor.lx,
      aly: anchor.ly,
      ax: anchorPos.x,
      ay: anchorPos.y,
    };
  });
}

/** Solve a new `scale` + `position` so that, keeping the current rotation, the
 *  dragged corner lands at `target` and the opposite (anchor) corner stays put.
 *  Handles rotation and negative scale; `uniform` keeps the current aspect ratio. */
export function resizeTransform(
  handle: ResizeHandle,
  target: Vec2,
  rotateDeg: number,
  scale: Vec2,
  uniform: boolean,
): { position: Vec2; scale: Vec2 } {
  const r = (rotateDeg * Math.PI) / 180;
  const cos = Math.cos(r);
  const sin = Math.sin(r);
  const vx = handle.dlx - handle.alx;
  const vy = handle.dly - handle.aly;
  const wx = target.x - handle.ax;
  const wy = target.y - handle.ay;

  let sx: number;
  let sy: number;
  if (uniform) {
    const initDiag = Math.hypot(handle.x - handle.ax, handle.y - handle.ay);
    const newDiag = Math.hypot(wx, wy);
    const f = initDiag > 1e-9 ? newDiag / initDiag : 1;
    sx = scale.x * f;
    sy = scale.y * f;
  } else {
    sx = (wx * cos + wy * sin) / vx;
    sy = (wy * cos - wx * sin) / vy;
  }

  // Keep the anchor corner fixed: translate so R·S·anchor + position = anchorSheet.
  const px = handle.ax - (cos * sx * handle.alx - sin * sy * handle.aly);
  const py = handle.ay - (sin * sx * handle.alx + cos * sy * handle.aly);
  return { position: { x: px, y: py }, scale: { x: sx, y: sy } };
}

function handleSvg(eid: string, h: ResizeHandle): string {
  const HS = 4; // visible handle half-size (mm)
  const HIT = 8; // comfortable hit area half-size (mm)
  return `<g data-eid="${eid}" data-handle="${h.key}" pointer-events="all">`
    + `<rect x="${fmt(h.x - HIT)}" y="${fmt(h.y - HIT)}" width="${HIT * 2}" height="${HIT * 2}" fill="rgba(255,255,255,0.001)"/>`
    + `<rect x="${fmt(h.x - HS)}" y="${fmt(h.y - HS)}" width="${HS * 2}" height="${HS * 2}" fill="#ffffff" stroke="#2563eb" stroke-width="0.5"/>`
    + `</g>`;
}

/** Build the inner SVG for a sheet's drawing area, with data-eid hit targets,
 *  a selection bbox, and resize handles for the selected element. */
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
  if (selectedId) {
    const el = sheet.elements.find((e) => e.id === selectedId);
    if (el) {
      const local = localBBoxFor(el, styles);
      if (local) {
        const [x0, y0, x1, y1] = transformedBBox(local, transformMatrix(el.transform));
        parts.push(
          `<rect data-eid="${selectedId}" data-sel="1" x="${fmt(x0)}" y="${fmt(y0)}" width="${fmt(x1 - x0)}" `
          + `height="${fmt(y1 - y0)}" fill="none" stroke="#2563eb" stroke-width="0.5" stroke-dasharray="2 2" pointer-events="none"/>`,
        );
      }
      const handles = computeHandles(el, styles);
      if (handles) for (const h of handles) parts.push(handleSvg(selectedId, h));
    }
  }
  return parts.join('\n');
}
