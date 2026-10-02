import type { Paper } from '../../model/src/types';
import { esc, fmt } from './util';

const CROP_INSET = 5.0;

export interface TiledPage {
  body: string;
  transform: string;
  tileIndex: number;
  cols: number;
  rows: number;
}

export interface TileResult {
  pages: TiledPage[];
  cols: number;
  rows: number;
  offset: [number, number] | null;
}

function overlapPair(overlap: Paper['overlap']): [number, number] {
  if (typeof overlap === 'number') return [overlap, overlap];
  return [overlap.x, overlap.y];
}

function cornerTicks(marginX: number, marginY: number, safeW: number, safeH: number): string {
  const L = 5.0;
  const loX = marginX + CROP_INSET;
  const hiX = marginX + safeW - CROP_INSET;
  const loY = marginY + CROP_INSET;
  const hiY = marginY + safeH - CROP_INSET;
  const segs: string[] = [];
  for (const cx of [loX, hiX]) {
    for (const cy of [loY, hiY]) {
      const sx = cx === loX ? 1.0 : -1.0;
      const sy = cy === loY ? 1.0 : -1.0;
      segs.push(`<line class="crop" x1="${fmt(cx)}" y1="${fmt(cy)}" x2="${fmt(cx + sx * L)}" y2="${fmt(cy)}"/>`);
      segs.push(`<line class="crop" x1="${fmt(cx)}" y1="${fmt(cy)}" x2="${fmt(cx)}" y2="${fmt(cy + sy * L)}"/>`);
    }
  }
  return '<g>' + segs.join('') + '</g>';
}

function overlapMarks(
  c: number, r: number, cols: number, rows: number,
  marginX: number, marginY: number, safeW: number, safeH: number,
  overlapX: number, overlapY: number,
): string {
  const segs: string[] = [];
  if (c < cols - 1) {
    const x = marginX + safeW - overlapX;
    segs.push(`<line class="overlap" x1="${fmt(x)}" y1="${fmt(marginY)}" x2="${fmt(x)}" y2="${fmt(marginY + safeH)}"/>`);
  }
  if (c > 0) {
    const x = marginX + overlapX;
    segs.push(`<line class="overlap" x1="${fmt(x)}" y1="${fmt(marginY)}" x2="${fmt(x)}" y2="${fmt(marginY + safeH)}"/>`);
  }
  if (r < rows - 1) {
    const y = marginY + safeH - overlapY;
    segs.push(`<line class="overlap" x1="${fmt(marginX)}" y1="${fmt(y)}" x2="${fmt(marginX + safeW)}" y2="${fmt(y)}"/>`);
  }
  if (r > 0) {
    const y = marginY + overlapY;
    segs.push(`<line class="overlap" x1="${fmt(marginX)}" y1="${fmt(y)}" x2="${fmt(marginX + safeW)}" y2="${fmt(y)}"/>`);
  }
  return segs.length ? '<g>' + segs.join('') + '</g>' : '';
}

/** Map a sheet's logical drawing area onto physical pages: one centered page
 *  when it fits the safe area, else a cols x rows grid with overlap marks. */
export function tile(title: string, W: number, H: number, body: string, paper: Paper, idPrefix = 'clip'): TileResult {
  const trimW = paper.trim.width;
  const trimH = paper.trim.height;
  const safeW = paper.safeArea.width;
  const safeH = paper.safeArea.height;
  const [overlapX, overlapY] = overlapPair(paper.overlap);
  const marginX = (trimW - safeW) / 2;
  const marginY = (trimH - safeH) / 2;
  const strideX = safeW - overlapX;
  const strideY = safeH - overlapY;
  if (strideX <= 0 || strideY <= 0) throw new Error('overlap must be smaller than the safe area');

  const cols = W <= safeW ? 1 : Math.ceil((W - safeW) / strideX) + 1;
  const rows = H <= safeH ? 1 : Math.ceil((H - safeH) / strideY) + 1;

  const pages: TiledPage[] = [];
  if (cols === 1 && rows === 1) {
    const ox = marginX + (safeW - W) / 2;
    const oy = marginY + (safeH - H) / 2;
    const tr = `translate(${fmt(ox)} ${fmt(oy)})`;
    pages.push({ body: `<g transform="${tr}">${body}</g>`, transform: tr, tileIndex: 1, cols: 1, rows: 1 });
    return { pages, cols, rows, offset: [ox, oy] };
  }

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const tx = marginX - c * strideX;
      const ty = marginY - r * strideY;
      const tr = `translate(${fmt(tx)} ${fmt(ty)})`;
      const idx = r * cols + c + 1;
      const clipId = `${idPrefix}-${idx}`;
      const clip = `<defs><clipPath id="${clipId}"><rect x="${fmt(marginX)}" y="${fmt(marginY)}" width="${fmt(safeW)}" height="${fmt(safeH)}"/></clipPath></defs>`;
      const parts = [
        clip,
        `<g clip-path="url(#${clipId})">`,
        `<g transform="${tr}">${body}</g>`,
        '</g>',
        cornerTicks(marginX, marginY, safeW, safeH),
        overlapMarks(c, r, cols, rows, marginX, marginY, safeW, safeH, overlapX, overlapY),
        `<text class="note" x="${fmt(trimW / 2)}" y="${fmt(trimH - 2.5)}">${esc(title)} \u00b7 tile ${idx}/${cols * rows} \u00b7 ${cols}x${rows}</text>`,
      ];
      pages.push({ body: parts.join('\n'), transform: tr, tileIndex: idx, cols, rows });
    }
  }
  return { pages, cols, rows, offset: null };
}
