/** Parse a CSS block of single-class rules (`.name { decls }`) into a map of
 *  class name -> declarations. Comments and multi-selector rules are ignored.
 *  Lives in its own module so the browser bundle doesn't pull in `yaml`. */
export function parseCss(css: string): Record<string, Record<string, string>> {
  const out: Record<string, Record<string, string>> = {};
  const text = (css ?? '').replace(/\/\*[\s\S]*?\*\//g, '');
  const ruleRe = /([^{}]+)\{([^{}]*)\}/g;
  let m: RegExpExecArray | null;
  while ((m = ruleRe.exec(text))) {
    const selector = m[1].trim();
    const cls = selector.match(/^\.([\w-]+)$/);
    if (!cls) continue;
    const decls: Record<string, string> = {};
    for (const part of m[2].split(';')) {
      const t = part.trim();
      if (!t) continue;
      const i = t.indexOf(':');
      if (i < 0) continue;
      const prop = t.slice(0, i).trim();
      const val = t.slice(i + 1).trim();
      if (prop && val) decls[prop] = val;
    }
    out[cls[1]] = decls;
  }
  return out;
}
