/** Format a number the way the legacy engine did: up to 6 decimals, trailing
 *  zeros and a trailing dot stripped. Keeps emitted coordinates compact. */
export function fmt(x: number): string {
  let s = x.toFixed(6);
  if (s.includes('.')) s = s.replace(/0+$/, '').replace(/\.$/, '');
  return s;
}

/** XML-escape text that will be interpolated into an attribute or text node. */
export function esc(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/** Slugify a title for use as an SVG id: keep `[A-Za-z0-9_-]`, collapse any
 *  other run (spaces, punctuation) to a single `-`, and trim leading/trailing
 *  dashes. Returns `''` when nothing survives. */
export function slug(s: string): string {
  return s.trim().replace(/[^A-Za-z0-9_-]+/g, '-').replace(/^-+|-+$/g, '');
}
