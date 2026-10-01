/** Source-SVG parsing and selector resolution.
 *
 *  Selectors are the legacy `source-id` XPath expressions (`//g[@id="P1"]/path`).
 *  We resolve them namespace-agnostically (matching localName and attributes),
 *  which mirrors the legacy engine's `strip_ns` and avoids any dependence on a
 *  browser/jsdóm XPath implementation (jsdom has none). */

export function parseSvg(markup: string): Document {
  const doc = new DOMParser().parseFromString(markup, 'application/xml');
  if (doc.getElementsByTagName('parsererror').length > 0) {
    throw new Error('source SVG failed to parse');
  }
  return doc;
}

interface Pred {
  attr: string;
  value?: string;
}

interface Step {
  tag: string;
  preds: Pred[];
}

function parseStep(text: string): Step {
  const tagMatch = text.match(/^([^\[]*)/);
  const tag = (tagMatch?.[1] ?? '').trim() || '*';
  const preds: Pred[] = [];
  const predRe = /\[\s*@?([\w:.-]+)\s*(?:=\s*(?:"([^"]*)"|'([^']*)'))?\s*\]/g;
  let m: RegExpExecArray | null;
  while ((m = predRe.exec(text))) {
    preds.push({ attr: m[1], value: m[2] ?? m[3] ?? undefined });
  }
  return { tag, preds };
}

function parseSelector(selector: string): { kind: 'desc' | 'child'; steps: Step[] } {
  let s = selector.trim();
  let kind: 'desc' | 'child';
  if (s.startsWith('//')) {
    kind = 'desc';
    s = s.slice(2);
  } else if (s.startsWith('.//')) {
    kind = 'desc';
    s = s.slice(3);
  } else if (s.startsWith('/')) {
    kind = 'child';
    s = s.slice(1);
  } else {
    kind = 'child';
  }
  const steps = s.split('/').filter((p) => p.trim().length > 0).map(parseStep);
  return { kind, steps };
}

function matches(el: Element, step: Step): boolean {
  if (step.tag !== '*' && el.localName !== step.tag) return false;
  for (const p of step.preds) {
    const v = el.getAttribute(p.attr);
    if (v === null) return false;
    if (p.value !== undefined && v !== p.value) return false;
  }
  return true;
}

function descendants(root: Element): Element[] {
  const out: Element[] = [];
  const walk = (el: Element) => {
    for (const child of Array.from(el.children)) {
      out.push(child);
      walk(child);
    }
  };
  walk(root);
  return out;
}

/** Resolve a legacy `source-id` selector against a parsed source document.
 *  Returns the matched elements in document order. */
export function resolve(root: Document, selector: string): Element[] {
  const docEl = root.documentElement;
  if (!docEl) return [];
  const { kind, steps } = parseSelector(selector);
  if (steps.length === 0) return [];
  const [first, ...rest] = steps;
  let nodes: Element[] = kind === 'desc'
    ? descendants(docEl).filter((e) => matches(e, first))
    : Array.from(docEl.children).filter((e) => matches(e, first));
  for (const step of rest) {
    const next: Element[] = [];
    for (const n of nodes) {
      for (const child of Array.from(n.children)) {
        if (matches(child, step)) next.push(child);
      }
    }
    nodes = next;
  }
  return nodes;
}

/** Deep-copy an element, drop every `id` attribute (the legacy engine strips
 *  ids from copied geometry so ids don't collide on a sheet), and serialize. */
export function serialize(el: Element): string {
  const clone = el.cloneNode(true) as Element;
  const strip = (n: Element) => {
    n.removeAttribute('id');
    for (const child of Array.from(n.children)) strip(child);
  };
  strip(clone);
  return new XMLSerializer().serializeToString(clone);
}
