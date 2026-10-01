import type { FlatSheet } from './flatten';
import { transformMatrix, walkPts } from './transform';

export interface Warning {
  sheet: string;
  message: string;
}

/** Ink-bounds check: warn (never silently clip) when an element's geometry
 *  pokes outside the sheet's logical drawing area. */
export function checkBounds(sheet: FlatSheet, warnings: Warning[], tol = 0.5): void {
  const W = sheet.width;
  const H = sheet.height;
  for (const el of sheet.elements) {
    if (el.kind === 'text') {
      if (!Number.isFinite(el.x) || !Number.isFinite(el.y)) {
        throw new Error(`${sheet.title}: text ${JSON.stringify(el.text)} has a non-finite position`);
      }
      continue;
    }
    const pts: [number, number][] = [];
    const m = transformMatrix(el.transform);
    for (const e of el.elements) walkPts(e, m, pts);
    if (pts.length === 0) continue;
    const xs = pts.map((p) => p[0]);
    const ys = pts.map((p) => p[1]);
    const x0 = Math.min(...xs);
    const y0 = Math.min(...ys);
    const x1 = Math.max(...xs);
    const y1 = Math.max(...ys);
    if (x0 < -tol || y0 < -tol || x1 > W + tol || y1 > H + tol) {
      warnings.push({
        sheet: sheet.title,
        message: `${sheet.title}: ${JSON.stringify(el.selector)} ink bbox (${x0.toFixed(2)},${y0.toFixed(2)},${x1.toFixed(2)},${y1.toFixed(2)}) extends outside drawing area ${W}x${H}`,
      });
    }
  }
}
