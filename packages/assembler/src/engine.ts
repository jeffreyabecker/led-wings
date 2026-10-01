import type { Paper, Project } from '../../model/src/types';
import { validateProject, type ValidationIssue } from '../../model/src/validate';
import { assembleBody } from './assemble';
import { cssToText, sheetSvg } from './emit';
import { flatten, type FlattenError } from './flatten';
import { parseSvg } from './resolve';
import { tile } from './tile';
import { checkBounds, type Warning } from './verify';

export interface EnginePage {
  fileName: string;
  svg: string;
  sheetId: string;
  sheetTitle: string;
  tileIndex: number;
  cols: number;
  rows: number;
  transform: string;
}

export interface EngineResult {
  pages: EnginePage[];
  warnings: Warning[];
  errors: (ValidationIssue | FlattenError)[];
  sheetCount: number;
  tiledPages: number;
}

export function defaultPaper(project: Project): Paper | undefined {
  const id = project.meta.defaultPaper ?? project.papers[0]?.id;
  return project.papers.find((p) => p.id === id);
}

/** Run the assembler over a project: validate, flatten, assemble, tile, verify,
 *  and emit per-physical-page SVGs in print order. */
export function assembleProject(
  project: Project,
  opts?: { sheetIds?: string[]; paperId?: string },
): EngineResult {
  const validation = validateProject(project);
  if (validation.length) {
    return { pages: [], warnings: [], errors: validation, sheetCount: 0, tiledPages: 0 };
  }

  const paperId = opts?.paperId ?? project.meta.defaultPaper ?? project.papers[0]?.id;
  const paper = project.papers.find((p) => p.id === paperId);
  if (!paper) {
    return { pages: [], warnings: [], errors: [{ path: 'papers', message: 'no paper defined' }], sheetCount: 0, tiledPages: 0 };
  }

  const sources = new Map([[project.source.id, parseSvg(project.source.svg)]]);
  const { sheets, errors } = flatten(project, sources);
  if (errors.length) {
    return { pages: [], warnings: [], errors, sheetCount: 0, tiledPages: 0 };
  }

  const wanted = opts?.sheetIds ? new Set(opts.sheetIds) : null;
  const styleCss = cssToText(project.styles);
  const warnings: Warning[] = [];
  const pages: EnginePage[] = [];
  let n = 0;
  let tiledPages = 0;

  for (const sheet of sheets) {
    if (wanted && !wanted.has(sheet.id)) continue;
    checkBounds(sheet, warnings);
    const body = assembleBody(sheet);
    const result = tile(sheet.title, sheet.width, sheet.height, body, paper);
    for (const page of result.pages) {
      n += 1;
      pages.push({
        fileName: `sheet-${String(n).padStart(3, '0')}.svg`,
        svg: sheetSvg(styleCss, '', page.body, paper.trim.width, paper.trim.height),
        sheetId: sheet.id,
        sheetTitle: sheet.title,
        tileIndex: page.tileIndex,
        cols: page.cols,
        rows: page.rows,
        transform: page.transform,
      });
    }
    if (result.cols !== 1 || result.rows !== 1) tiledPages += 1;
  }

  const sheetCount = sheets.filter((s) => !wanted || wanted.has(s.id)).length;
  return { pages, warnings, errors: [], sheetCount, tiledPages };
}
