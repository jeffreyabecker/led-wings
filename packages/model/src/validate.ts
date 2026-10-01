import type { Project, Transform, Vec2 } from './types';

export interface ValidationIssue {
  path: string;
  message: string;
}

const fin = (n: unknown): n is number => typeof n === 'number' && Number.isFinite(n);

function checkVec(path: string, v: Vec2 | undefined, issues: ValidationIssue[]): void {
  if (!v) {
    issues.push({ path, message: 'missing position' });
    return;
  }
  if (!fin(v.x)) issues.push({ path: `${path}.x`, message: 'x must be a finite number' });
  if (!fin(v.y)) issues.push({ path: `${path}.y`, message: 'y must be a finite number' });
}

function checkTransform(path: string, t: Transform | undefined, issues: ValidationIssue[]): void {
  if (!t) return;
  if (t.rotate !== undefined && !fin(t.rotate)) {
    issues.push({ path: `${path}.rotate`, message: 'rotate must be a finite number' });
  }
  if (t.scale !== undefined) {
    if (!fin(t.scale.x)) issues.push({ path: `${path}.scale.x`, message: 'scale.x must be a finite number' });
    if (!fin(t.scale.y)) issues.push({ path: `${path}.scale.y`, message: 'scale.y must be a finite number' });
  }
}

function checkSize(
  path: string,
  s: { width: number; height: number } | undefined,
  issues: ValidationIssue[],
): void {
  if (!s) {
    issues.push({ path, message: 'missing dimensions' });
    return;
  }
  for (const k of ['width', 'height'] as const) {
    if (!fin(s[k])) issues.push({ path: `${path}.${k}`, message: `${k} must be a finite number` });
    else if (s[k] <= 0) issues.push({ path: `${path}.${k}`, message: `${k} must be positive` });
  }
}

export function validateProject(p: Project): ValidationIssue[] {
  const issues: ValidationIssue[] = [];

  if (!p.meta?.name) issues.push({ path: 'meta.name', message: 'project needs a name' });
  if (p.meta?.units !== 'mm') issues.push({ path: 'meta.units', message: 'units must be "mm"' });

  const sourceIds = new Set<string>();
  const src = p.source;
  if (!src) {
    issues.push({ path: 'source', message: 'project needs a source' });
  } else {
    if (!src.id) issues.push({ path: 'source.id', message: 'source needs an id' });
    else sourceIds.add(src.id);
    if (!src.svg) issues.push({ path: 'source.svg', message: 'source svg is empty' });
  }

  const assetIds = new Set<string>();
  for (const [i, a] of (p.assets ?? []).entries()) {
    const path = `assets[${i}]`;
    if (!a.id) issues.push({ path: `${path}.id`, message: 'asset needs an id' });
    else if (assetIds.has(a.id)) issues.push({ path: `${path}.id`, message: `duplicate asset id ${JSON.stringify(a.id)}` });
    else assetIds.add(a.id);
    if (a.sourceId && !sourceIds.has(a.sourceId)) {
      issues.push({ path: `${path}.sourceId`, message: `asset references unknown source ${JSON.stringify(a.sourceId)}` });
    }
    if (!a.sourceSelector) issues.push({ path: `${path}.sourceSelector`, message: 'asset needs a sourceSelector' });
    checkTransform(`${path}.baseTransform`, a.baseTransform, issues);
  }

  const paperIds = new Set<string>();
  for (const [i, pp] of (p.papers ?? []).entries()) {
    const path = `papers[${i}]`;
    if (!pp.id) issues.push({ path: `${path}.id`, message: 'paper needs an id' });
    else if (paperIds.has(pp.id)) issues.push({ path: `${path}.id`, message: `duplicate paper id ${JSON.stringify(pp.id)}` });
    else paperIds.add(pp.id);
    checkSize(`${path}.trim`, pp.trim, issues);
    checkSize(`${path}.safeArea`, pp.safeArea, issues);
    const ov = typeof pp.overlap === 'number' ? { x: pp.overlap, y: pp.overlap } : pp.overlap;
    if (!ov || !fin(ov.x) || !fin(ov.y) || ov.x < 0 || ov.y < 0) {
      issues.push({ path: `${path}.overlap`, message: 'overlap must be a non-negative number or {x,y}' });
    }
  }

  const sheetIds = new Set<string>();
  const titles = new Set<string>();
  for (const [i, s] of (p.sheets ?? []).entries()) {
    const path = `sheets[${i}]`;
    if (!s.id) issues.push({ path: `${path}.id`, message: 'sheet needs an id' });
    else if (sheetIds.has(s.id)) issues.push({ path: `${path}.id`, message: `duplicate sheet id ${JSON.stringify(s.id)}` });
    else sheetIds.add(s.id);
    if (!s.title) issues.push({ path: `${path}.title`, message: 'sheet needs a title' });
    else if (titles.has(s.title)) issues.push({ path: `${path}.title`, message: `duplicate sheet title ${JSON.stringify(s.title)}` });
    else titles.add(s.title);
    checkSize(`${path}.dimensions`, s.dimensions, issues);

    const elIds = new Set<string>();
    for (const [j, el] of (s.elements ?? []).entries()) {
      const ep = `${path}.elements[${j}]`;
      if (!el.id) issues.push({ path: `${ep}.id`, message: 'element needs an id' });
      else if (elIds.has(el.id)) issues.push({ path: `${ep}.id`, message: `duplicate element id ${JSON.stringify(el.id)}` });
      else elIds.add(el.id);
      checkVec(`${ep}.position`, el.position, issues);
      if (el.kind === 'instance') {
        checkTransform(`${ep}.transform`, el.transform, issues);
        if (el.assetId && !assetIds.has(el.assetId)) {
          issues.push({ path: `${ep}.assetId`, message: `instance references unknown asset ${JSON.stringify(el.assetId)}` });
        }
      } else if (el.kind === 'source') {
        checkTransform(`${ep}.transform`, el.transform, issues);
        if (el.sourceId && !sourceIds.has(el.sourceId)) {
          issues.push({ path: `${ep}.sourceId`, message: `source references unknown source ${JSON.stringify(el.sourceId)}` });
        }
        if (!el.sourceSelector) issues.push({ path: `${ep}.sourceSelector`, message: 'source needs a sourceSelector' });
      } else if (el.kind === 'text') {
        checkTransform(`${ep}.transform`, el.transform, issues);
      } else {
        issues.push({ path: ep, message: 'unknown element kind' });
      }
    }

    for (const [k, ly] of (s.layers ?? []).entries()) {
      const lp = `${path}.layers[${k}]`;
      for (const eid of ly.elementIds ?? []) {
        if (!elIds.has(eid)) {
          issues.push({ path: `${lp}.elementIds`, message: `layer references unknown element id ${JSON.stringify(eid)}` });
        }
      }
    }
  }

  for (const [i, o] of (p.outputs ?? []).entries()) {
    const path = `outputs[${i}]`;
    if (o.paperId && !paperIds.has(o.paperId)) {
      issues.push({ path: `${path}.paperId`, message: `output references unknown paper ${JSON.stringify(o.paperId)}` });
    }
    if (o.format && !['svg', 'pdf', 'contact-sheet'].includes(o.format)) {
      issues.push({ path: `${path}.format`, message: `unknown format ${JSON.stringify(o.format)}` });
    }
    for (const sid of o.sheetIds ?? []) {
      if (!sheetIds.has(sid)) {
        issues.push({ path: `${path}.sheetIds`, message: `output references unknown sheet ${JSON.stringify(sid)}` });
      }
    }
  }

  return issues;
}
