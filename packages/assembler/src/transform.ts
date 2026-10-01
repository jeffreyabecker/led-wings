import type { Transform, Vec2 } from '../../model/src/types';
import { fmt } from './util';

// Affine matrix [a b c d e f], matching the SVG / legacy engine convention:
//   x' = a*x + c*y + e
//   y' = b*x + d*y + f
export type Matrix = [number, number, number, number, number, number];

export const IDENT: Matrix = [1, 0, 0, 1, 0, 0];

export function mul(A: Matrix, B: Matrix): Matrix {
  const [a1, b1, c1, d1, e1, f1] = A;
  const [a2, b2, c2, d2, e2, f2] = B;
  return [
    a1 * a2 + c1 * b2,
    b1 * a2 + d1 * b2,
    a1 * c2 + c1 * d2,
    b1 * c2 + d1 * d2,
    a1 * e2 + c1 * f2 + e1,
    b1 * e2 + d1 * f2 + f1,
  ];
}

export function applyMatrix(m: Matrix, x: number, y: number): [number, number] {
  const [a, b, c, d, e, f] = m;
  return [a * x + c * y + e, b * x + d * y + f];
}

interface Op {
  kind: 'matrix' | 'translate' | 'scale';
  vals: number[];
}

/** Parse an SVG `transform` attribute string into ordered ops. rotate/skew are
 *  pre-folded into matrix ops, mirroring the legacy engine's `_ops`. */
export function parseOps(tstr: string): Op[] {
  const out: Op[] = [];
  const re = /([a-zA-Z]+)\s*\(([^)]*)\)/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(tstr))) {
    const kind = m[1];
    const args = m[2].trim().split(/[\s,]+/).filter(Boolean).map(Number);
    if (kind === 'matrix') {
      out.push({ kind: 'matrix', vals: args });
    } else if (kind === 'translate') {
      out.push({ kind: 'translate', vals: [args[0] ?? 0, args[1] ?? 0] });
    } else if (kind === 'scale') {
      out.push({ kind: 'scale', vals: args.length === 1 ? [args[0], args[0]] : [args[0], args[1]] });
    } else if (kind === 'rotate') {
      const a = (args[0] ?? 0) * Math.PI / 180;
      const cos = Math.cos(a);
      const sin = Math.sin(a);
      const cx = args.length >= 3 ? args[1] : 0;
      const cy = args.length >= 3 ? args[2] : 0;
      out.push({ kind: 'matrix', vals: [cos, sin, -sin, cos, cx - cos * cx + sin * cy, cy - sin * cx - cos * cy] });
    } else if (kind === 'skewX') {
      out.push({ kind: 'matrix', vals: [1, 0, Math.tan((args[0] ?? 0) * Math.PI / 180), 1, 0, 0] });
    } else if (kind === 'skewY') {
      out.push({ kind: 'matrix', vals: [1, Math.tan((args[0] ?? 0) * Math.PI / 180), 0, 1, 0, 0] });
    }
    // Unknown transform kinds are ignored rather than failing the whole build.
  }
  return out;
}

/** Compose one or more SVG transform strings (each parsed via parseOps). */
export function transformMatrix(...tstrs: (string | undefined | null)[]): Matrix {
  let m: Matrix = IDENT;
  for (const tstr of tstrs) {
    if (!tstr) continue;
    for (const op of parseOps(tstr)) {
      if (op.kind === 'matrix') {
        const v = op.vals;
        m = mul(m, [v[0] ?? 1, v[1] ?? 0, v[2] ?? 0, v[3] ?? 1, v[4] ?? 0, v[5] ?? 0]);
      } else if (op.kind === 'translate') {
        m = mul(m, [1, 0, 0, 1, op.vals[0], op.vals[1]]);
      } else if (op.kind === 'scale') {
        m = mul(m, [op.vals[0], 0, 0, op.vals[1], 0, 0]);
      }
    }
  }
  return m;
}

/** Build the emitted transform string: `translate(pos) [rotate][scale]...`.
 *  `position` is outermost; later entries are applied to the geometry first
 *  (innermost). For an instance, pass `[instance.transform, asset.baseTransform]`. */
export function transformString(position: Vec2, transforms: (Transform | undefined)[]): string {
  const parts = [`translate(${fmt(position.x)} ${fmt(position.y)})`];
  for (const t of transforms) {
    if (!t) continue;
    if (t.rotate !== undefined) parts.push(`rotate(${fmt(t.rotate)})`);
    if (t.scale) parts.push(`scale(${fmt(t.scale.x)} ${fmt(t.scale.y)})`);
  }
  return parts.join(' ');
}

const PATH_NUMS: Record<string, number> = { m: 2, l: 2, h: 1, v: 1, c: 6, s: 4, q: 4, t: 2, a: 7, z: 0 };
const NUMBER = /[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?|[A-Za-z]/g;

/** Control/end points a path `d` passes through, in the path's own frame.
 *  Ported from the legacy engine's `_path_points`. */
export function pathPoints(d: string | null): [number, number][] {
  const toks = (d ?? '').match(NUMBER) ?? [];
  const pts: [number, number][] = [];
  let i = 0;
  let letter: string | null = null;
  let x = 0;
  let y = 0;
  let start: [number, number] = [0, 0];

  while (i < toks.length) {
    const t = toks[i];
    if (/^[A-Za-z]$/.test(t)) {
      letter = t;
      i += 1;
      if (t === 'z' || t === 'Z') {
        x = start[0];
        y = start[1];
        continue;
      }
    } else if (letter === null) {
      throw new Error(`path data without a command: ${JSON.stringify(d)}`);
    }
    const ch: string = letter as string;
    const c = ch.toLowerCase();
    const rel = ch === c;
    const k = PATH_NUMS[c];
    if (k === 0) continue;
    const v = toks.slice(i, i + k).map(Number);
    i += k;
    if (v.length === 0) break;
    if (c === 'h') {
      x = rel ? x + v[0] : v[0];
      pts.push([x, y]);
    } else if (c === 'v') {
      y = rel ? y + v[0] : v[0];
      pts.push([x, y]);
    } else if (c === 'a') {
      const ex = v[5];
      const ey = v[6];
      x = rel ? x + ex : ex;
      y = rel ? y + ey : ey;
      pts.push([x, y]);
    } else {
      let pairs: [number, number][] = [];
      for (let j = 0; j < v.length; j += 2) pairs.push([v[j], v[j + 1]]);
      if (rel) pairs = pairs.map(([px, py]) => [x + px, y + py] as [number, number]);
      pts.push(...pairs);
      const last = pairs[pairs.length - 1];
      x = last[0];
      y = last[1];
      if (c === 'm') start = [x, y];
    }
    if (c === 'm' || c === 'l') letter = rel ? 'l' : 'L';
  }
  return pts;
}

/** Control points of one shape element in its own frame, or null if it is not a
 *  recognized shape. Groups are walked by their caller; only leaves contribute. */
function shapePoints(el: Element): [number, number][] | null {
  const n = (s: string | null): number => (s === null ? NaN : Number(s));
  switch (el.localName) {
    case 'path':
      return pathPoints(el.getAttribute('d'));
    case 'line':
      return [
        [n(el.getAttribute('x1')), n(el.getAttribute('y1'))],
        [n(el.getAttribute('x2')), n(el.getAttribute('y2'))],
      ];
    case 'rect': {
      const x = n(el.getAttribute('x'));
      const y = n(el.getAttribute('y'));
      const w = n(el.getAttribute('width'));
      const h = n(el.getAttribute('height'));
      return [[x, y], [x + w, y], [x, y + h], [x + w, y + h]];
    }
    case 'circle': {
      const cx = n(el.getAttribute('cx'));
      const cy = n(el.getAttribute('cy'));
      const r = n(el.getAttribute('r'));
      return [[cx - r, cy - r], [cx + r, cy - r], [cx - r, cy + r], [cx + r, cy + r]];
    }
    case 'ellipse': {
      const cx = n(el.getAttribute('cx'));
      const cy = n(el.getAttribute('cy'));
      const rx = n(el.getAttribute('rx'));
      const ry = n(el.getAttribute('ry'));
      return [[cx - rx, cy - ry], [cx + rx, cy - ry], [cx - rx, cy + ry], [cx + rx, cy + ry]];
    }
    case 'polyline':
    case 'polygon': {
      const pts: [number, number][] = [];
      const points = el.getAttribute('points');
      if (points) {
        const nums = points.split(/[\s,]+/).filter(Boolean).map(Number);
        for (let i = 0; i + 1 < nums.length; i += 2) pts.push([nums[i], nums[i + 1]]);
      }
      return pts;
    }
    default:
      return null;
  }
}

/** Walk an element tree (including groups), applying transforms, and collect
 *  control points from every recognized shape leaf. */
export function walkPts(el: Element, matrix: Matrix, out: [number, number][]): void {
  const m = mul(matrix, transformMatrix(el.getAttribute('transform')));
  const pts = shapePoints(el);
  if (pts) {
    for (const [x, y] of pts) out.push(applyMatrix(m, x, y));
  }
  for (const child of Array.from(el.children)) {
    walkPts(child, m, out);
  }
}

/** Ink bbox of resolved source elements under a combined transform string. */
export function elementBBox(transform: string, els: Element[]): [number, number, number, number] | null {
  const pts: [number, number][] = [];
  const m = transformMatrix(transform);
  for (const e of els) walkPts(e, m, pts);
  const finite = pts.filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y));
  if (finite.length === 0) return null;
  const xs = finite.map((p) => p[0]);
  const ys = finite.map((p) => p[1]);
  return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
}
