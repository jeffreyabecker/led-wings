import { elementBBox, esc, fmt, parseSvg, serialize } from '../../packages/assembler/src/index';
import type { FlatSheet } from '../../packages/assembler/src/flatten';
import type { Project } from '../../packages/model/src/types';

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

/** Build the inner SVG for a sheet's drawing area, with data-eid hit targets
 *  and a selection bbox overlay. */
export function renderSheetBody(sheet: FlatSheet, stylesCss: string, selectedId: string | null): string {
  const parts: string[] = [`<style>${stylesCss}</style>`];
  parts.push(
    `<rect x="0" y="0" width="${fmt(sheet.width)}" height="${fmt(sheet.height)}" fill="#ffffff" stroke="#999" stroke-width="0.3"/>`,
  );
  for (const el of sheet.elements) {
    const sel = el.id === selectedId ? ' data-sel="1"' : '';
    if (el.kind === 'text') {
      parts.push(
        `<text data-eid="${el.id}"${sel} class="${esc(el.styleId)}" x="${fmt(el.x)}" y="${fmt(el.y)}">${esc(el.text)}</text>`,
      );
    } else {
      const inner = el.elements.map((e) => serialize(e)).join('');
      parts.push(`<g data-eid="${el.id}"${sel} transform="${esc(el.transform)}">${inner}</g>`);
    }
  }
  if (selectedId) {
    const el = sheet.elements.find((e) => e.id === selectedId);
    if (el && el.kind === 'source') {
      const box = elementBBox(el.transform, el.elements);
      if (box) {
        const [x0, y0, x1, y1] = box;
        parts.push(
          `<rect data-eid="${selectedId}" data-sel="1" x="${fmt(x0)}" y="${fmt(y0)}" width="${fmt(x1 - x0)}" `
          + `height="${fmt(y1 - y0)}" fill="none" stroke="#2563eb" stroke-width="0.5" stroke-dasharray="2 2" pointer-events="none"/>`,
        );
      }
    }
  }
  return parts.join('\n');
}
