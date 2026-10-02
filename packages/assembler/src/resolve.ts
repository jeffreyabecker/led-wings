/** Source-SVG parsing and id-based component resolution.
 *
 *  Source components are referenced by their `id` attribute in the source SVG
 *  (e.g. `P1-outline`, `B-align`, `calibration`). Lookup is namespace-agnostic:
 *  we match the plain `id` attribute wherever it appears. */

export function parseSvg(markup: string): Document {
  const doc = new DOMParser().parseFromString(markup, 'application/xml');
  if (doc.getElementsByTagName('parsererror').length > 0) {
    throw new Error('source SVG failed to parse');
  }
  return doc;
}

/** Resolve a source component by its `id` attribute. Ids are expected to be
 *  unique; the first match in document order wins. */
export function resolveId(root: Document, id: string): Element | null {
  const docEl = root.documentElement;
  if (!docEl) return null;
  if (docEl.getAttribute('id') === id) return docEl;
  const stack: Element[] = Array.from(docEl.children);
  while (stack.length) {
    const el = stack.pop()!;
    if (el.getAttribute('id') === id) return el;
    for (const child of Array.from(el.children)) stack.push(child);
  }
  return null;
}

/** Deep-copy an element, drop every `id` attribute (copied geometry must not
 *  collide with ids on a sheet), and serialize. */
export function serialize(el: Element): string {
  const clone = el.cloneNode(true) as Element;
  const strip = (n: Element) => {
    n.removeAttribute('id');
    for (const child of Array.from(n.children)) strip(child);
  };
  strip(clone);
  return new XMLSerializer().serializeToString(clone);
}
