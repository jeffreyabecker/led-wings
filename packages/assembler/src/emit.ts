import type { CssDecl } from '../../model/src/types';
import { fmt } from './util';

// Physical-sheet CSS appended to the user's styles on every page.
export const CSS2 = '\n.crop { stroke: #999999; stroke-width: 0.25; }\n'
  + '.overlap { stroke: #999999; stroke-width: 0.15; stroke-dasharray: 2 2; fill: none; }\n'
  + '.note { font-family: sans-serif; fill: #555555; font-size: 4; text-anchor: middle; }\n';

/** Reconstruct CSS text from the structured styles map (insertion order kept). */
export function cssToText(styles: Record<string, CssDecl>): string {
  const parts: string[] = [];
  for (const [name, decls] of Object.entries(styles)) {
    const body = Object.entries(decls).map(([p, v]) => `${p}: ${v};`).join(' ');
    parts.push(`.${name} { ${body} }`);
  }
  return parts.join('\n');
}

/** Wrap a page body in the final sheet SVG. */
export function sheetSvg(styleCss: string, defs: string, body: string, trimW: number, trimH: number): string {
  return `<svg xmlns="http://www.w3.org/2000/svg" `
    + `width="${fmt(trimW)}mm" height="${fmt(trimH)}mm" `
    + `viewBox="0 0 ${fmt(trimW)} ${fmt(trimH)}">\n`
    + `<style type="text/css">${styleCss}${CSS2}</style>\n`
    + defs
    + `<rect x="0" y="0" width="${fmt(trimW)}" height="${fmt(trimH)}" fill="#ffffff"/>\n`
    + body
    + '\n</svg>\n';
}
