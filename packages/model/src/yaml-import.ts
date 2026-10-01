import { parse } from 'yaml';
import type { Element, Overlap, Project, Source, Transform } from './types';

// Loose shapes of the legacy layout.yaml (the previous system's artifact).
interface LegacyTextEl {
  text: string;
  position: { x: number; y: number };
  class?: string;
}
interface LegacySourceEl {
  'source-id': string;
  position: { x: number; y: number };
  transform?: { rotate?: number; scale?: [number, number] };
}
type LegacyElement = LegacyTextEl | LegacySourceEl;

interface LegacySheet {
  title?: string;
  dimensions?: { width: number; height: number };
  elements?: LegacyElement[];
}

interface LegacyLayout {
  'source-file'?: string;
  paper?: {
    trim?: { width: number; height: number };
    'safe-area'?: { width: number; height: number };
    overlap?: number | { x: number; y: number };
  };
  'output-style'?: string;
  sheets?: LegacySheet[];
}

/** Parse the legacy output-style CSS block into structured class -> declarations. */
export function parseCss(css: string): Record<string, Record<string, string>> {
  const out: Record<string, Record<string, string>> = {};
  const text = (css ?? '').replace(/\/\*[\s\S]*?\*\//g, '');
  const ruleRe = /([^{}]+)\{([^{}]*)\}/g;
  let m: RegExpExecArray | null;
  while ((m = ruleRe.exec(text))) {
    const selector = m[1].trim();
    const cls = selector.match(/^\.([\w-]+)$/);
    if (!cls) continue; // legacy output-style uses single-class rules only
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

function mapTransform(t?: LegacySourceEl['transform']): Transform | undefined {
  if (!t) return undefined;
  const out: Transform = {};
  if (t.rotate !== undefined) out.rotate = t.rotate;
  if (t.scale !== undefined) out.scale = { x: t.scale[0], y: t.scale[1] };
  return out;
}

function mapOverlap(o: LegacyLayout['paper'] extends infer _ ? number | { x: number; y: number } | undefined : never): Overlap {
  if (o === undefined) return 0;
  if (typeof o === 'number') return o;
  return { x: o.x, y: o.y };
}

/**
 * One-time migration: convert a legacy layout.yaml (plus the source SVG it names)
 * into the richer Project model. No byte fidelity — only feature/data preservation.
 */
export function importLayoutYaml(
  yamlText: string,
  sourceFiles: Record<string, string>,
): Project {
  const raw = parse(yamlText) as LegacyLayout;

  const sourceFileName = raw['source-file'] ?? '';
  const sourceId = 'source-1';
  const sources: Source[] = [{
    id: sourceId,
    name: sourceFileName,
    svg: sourceFiles[sourceFileName] ?? '',
  }];

  const paper = raw.paper;
  const papers: Project['papers'] = paper
    ? [{
        id: 'paper-1',
        name: 'Letter landscape',
        trim: { width: paper.trim?.width ?? 0, height: paper.trim?.height ?? 0 },
        safeArea: { width: paper['safe-area']?.width ?? 0, height: paper['safe-area']?.height ?? 0 },
        overlap: mapOverlap(paper.overlap),
      }]
    : [];

  const styles = parseCss(raw['output-style'] ?? '');

  const sheets: Project['sheets'] = (raw.sheets ?? []).map((s, si) => {
    const sheetId = `sheet-${si + 1}`;
    const elements: Element[] = (s.elements ?? []).map((el, ei): Element => {
      const id = `${sheetId}-el-${ei + 1}`;
      const position = { x: el.position?.x ?? 0, y: el.position?.y ?? 0 };
      if ('text' in el) {
        return { id, kind: 'text', text: el.text, position, styleId: el.class ?? 'label' };
      }
      return {
        id,
        kind: 'source',
        sourceId,
        sourceSelector: el['source-id'],
        position,
        transform: mapTransform(el.transform),
      };
    });
    return {
      id: sheetId,
      title: s.title ?? sheetId,
      dimensions: { width: s.dimensions?.width ?? 0, height: s.dimensions?.height ?? 0 },
      elements,
    };
  });

  const outputs: Project['outputs'] = papers.length
    ? [{
        id: 'output-1',
        name: 'Print all sheets',
        sheetIds: sheets.map((s) => s.id),
        paperId: papers[0].id,
        format: 'svg',
      }]
    : [];

  return {
    meta: {
      name: sourceFileName.replace(/\.svg$/i, '') || 'Imported layout',
      units: 'mm',
      defaultPaper: papers[0]?.id,
      defaultSource: sources[0]?.id,
    },
    sources,
    assets: [],
    styles,
    papers,
    sheets,
    outputs,
  };
}
