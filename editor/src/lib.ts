import {
  applyMatrix,
  cssToText,
  elementBBox,
  esc,
  fmt,
  parseSvg,
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

export interface PaletteEntry {
  sourceId: string;
  selector: string;
  label: string;
}

function shortLabel(sel: string): string {
  const m = sel.match(/^\/\/g\[@id="([^"]+)"\](.*)$/);
  return m ? m[1] + m[2] : sel;
}

/** Enumerate addressable source groups (and their /path and /g variants) for
 *  the palette, mirroring the selector shapes the legacy spec used. */
export function buildPalette(project: Project): PaletteEntry[] {
  const entries: PaletteEntry[] = [];
  const seen = new Set<string>();
  for (const src of project.sources) {
    const doc = parseSvg(src.svg);
    for (const g of Array.from(doc.querySelectorAll('g[id]'))) {
      const id = g.getAttribute('id')!;
      const base = `//g[@id="${id}"]`;
      const hasPath = Array.from(g.children).some((c) => c.localName === 'path');
      const hasG = Array.from(g.children).some((c) => c.localName === 'g');
      const variants = [base];
      if (hasPath) variants.push(`${base}/path`);
      if (hasG) variants.push(`${base}/g`);
      for (const v of variants) {
        const key = `${src.id}::${v}`;
        if (seen.has(key)) continue;
        seen.add(key);
        entries.push({ sourceId: src.id, selector: v, label: shortLabel(v) });
      }
    }
  }
  entries.sort((a, b) => a.label.localeCompare(b.label));
  return entries;
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
