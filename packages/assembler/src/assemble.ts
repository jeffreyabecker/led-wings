import type { FlatSheet } from './flatten';
import { serialize } from './resolve';
import { esc, fmt } from './util';

/** Build a sheet's drawing-area body: text nodes and transformed source copies. */
export function assembleBody(sheet: FlatSheet): string {
  const parts: string[] = [];
  for (const el of sheet.elements) {
    if (el.kind === 'text') {
      parts.push(`<text class="${esc(el.styleId)}" x="${fmt(el.x)}" y="${fmt(el.y)}">${esc(el.text)}</text>`);
    } else {
      for (const e of el.elements) {
        parts.push(`<g transform="${esc(el.transform)}">${serialize(e)}</g>`);
      }
    }
  }
  return parts.join('\n');
}
