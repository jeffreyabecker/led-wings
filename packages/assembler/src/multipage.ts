import { CSS2 } from './emit';
import type { EnginePage } from './engine';
import { esc, fmt } from './util';

/** Emit the assembled pages as a single Inkscape multipage SVG document.
 *
 *  Inkscape's multipage support (see `templates/multipage-example.svg`) stores
 *  one `<inkscape:page>` element per physical page inside the
 *  `<sodipodi:namedview>`, with the page content laid out side by side in
 *  document coordinates. This emits pages in a single horizontal row. */

export interface MultipageOptions {
  /** Gap between pages in mm. Defaults to 10. */
  gap?: number;
  /** Per-page `inkscape:label`; defaults to the sheet title (plus tile info). */
  label?: (page: EnginePage, index: number) => string;
  /** Value for `sodipodi:docname`. Defaults to `sheets-multipage.svg`. */
  docName?: string;
}

const INKSCAPE_VERSION = '1.4 (86a8ad7, 2024-10-11)';

const NAMESPACES = [
  'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"',
  'xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"',
  'xmlns="http://www.w3.org/2000/svg"',
  'xmlns:svg="http://www.w3.org/2000/svg"',
].join('\n   ');

function defaultLabel(page: EnginePage): string {
  if (page.cols === 1 && page.rows === 1) return page.sheetTitle;
  return `${page.sheetTitle} \u00b7 tile ${page.tileIndex}/${page.cols * page.rows}`;
}

export function emitMultipageSvg(
  pages: EnginePage[],
  trim: { width: number; height: number },
  styleCss: string,
  opts: MultipageOptions = {},
): string {
  const gap = opts.gap ?? 10;
  const n = pages.length;
  const totalW = n * trim.width + (n - 1) * gap;
  const totalH = trim.height;

  const pageDefs: string[] = [];
  const pageGroups: string[] = [];

  pages.forEach((page, i) => {
    const x = i * (trim.width + gap);
    const y = 0;
    const label = opts.label ? opts.label(page, i) : defaultLabel(page);
    pageDefs.push(
      `    <inkscape:page\n`
      + `       x="${fmt(x)}"\n`
      + `       y="${fmt(y)}"\n`
      + `       width="${fmt(trim.width)}"\n`
      + `       height="${fmt(trim.height)}"\n`
      + `       id="page${i + 1}"\n`
      + `       margin="5"\n`
      + `       bleed="0"\n`
      + `       inkscape:label="${esc(label)}" />`,
    );
    pageGroups.push(
      `  <g transform="translate(${fmt(x)} ${fmt(y)})">\n`
      + `    <rect x="0" y="0" width="${fmt(trim.width)}" height="${fmt(trim.height)}" fill="#ffffff"/>\n`
      + `${page.body}\n`
      + `  </g>`,
    );
  });

  const docName = opts.docName ?? 'sheets-multipage.svg';

  return `<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n`
    + `<!-- Created with Inkscape (http://www.inkscape.org/) -->\n\n`
    + `<svg\n`
    + `   width="${fmt(totalW)}mm"\n`
    + `   height="${fmt(totalH)}mm"\n`
    + `   viewBox="0 0 ${fmt(totalW)} ${fmt(totalH)}"\n`
    + `   version="1.1"\n`
    + `   id="svg1"\n`
    + `   inkscape:version="${INKSCAPE_VERSION}"\n`
    + `   sodipodi:docname="${esc(docName)}"\n`
    + `   ${NAMESPACES}>\n`
    + `  <sodipodi:namedview\n`
    + `     id="namedview1"\n`
    + `     pagecolor="#ffffff"\n`
    + `     bordercolor="#666666"\n`
    + `     borderopacity="1.0"\n`
    + `     inkscape:showpageshadow="2"\n`
    + `     inkscape:pageopacity="0.0"\n`
    + `     inkscape:pagecheckerboard="false"\n`
    + `     inkscape:deskcolor="#d1d1d1"\n`
    + `     inkscape:document-units="mm"\n`
    + `     showborder="true">\n`
    + pageDefs.join('\n') + `\n`
    + `  </sodipodi:namedview>\n`
    + `  <defs\n`
    + `     id="defs1" />\n`
    + `  <style type="text/css">${styleCss}${CSS2}</style>\n`
    + pageGroups.join('\n') + `\n`
    + `</svg>\n`;
}
