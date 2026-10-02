import type { Project } from '../../model/src/types';
import { resolveId } from './resolve';
import { transformString } from './transform';

/** A concrete element ready to assemble: references resolved to DOM nodes. */
export type FlatElement =
  | { id: string; kind: 'text'; text: string; styleId: string; x: number; y: number; transform: string }
  | { id: string; kind: 'source'; source: string; elements: Element[]; transform: string };

export interface FlatSheet {
  id: string;
  title: string;
  width: number;
  height: number;
  elements: FlatElement[];
}

export interface FlattenError {
  path: string;
  message: string;
}

/** Compiler link step: resolve source component ids (and asset references) into
 *  concrete DOM nodes. No layout decisions are made here. */
export function flatten(
  project: Project,
  sourceDoc: Document,
): { sheets: FlatSheet[]; errors: FlattenError[] } {
  const errors: FlattenError[] = [];
  const assets = new Map(project.assets.map((a) => [a.id, a]));

  const sheets: FlatSheet[] = project.sheets.map((sheet, si) => {
    const path = `sheets[${si}]`;
    const elements: FlatElement[] = [];

    for (const [ei, el] of sheet.elements.entries()) {
      const ep = `${path}.elements[${ei}]`;
      if (el.kind === 'text') {
        elements.push({
          id: el.id,
          kind: 'text',
          text: el.text,
          styleId: el.styleId ?? 'label',
          x: el.position.x,
          y: el.position.y,
          transform: transformString(el.position, [el.transform]),
        });
      } else if (el.kind === 'source') {
        const found = resolveId(sourceDoc, el.source);
        if (!found) {
          errors.push({ path: `${ep}.source`, message: `unknown source id ${JSON.stringify(el.source)}` });
          continue;
        }
        elements.push({
          id: el.id,
          kind: 'source',
          source: el.source,
          elements: [found],
          transform: transformString(el.position, [el.transform]),
        });
      } else {
        const asset = assets.get(el.assetId);
        if (!asset) {
          errors.push({ path: `${ep}.assetId`, message: `unknown asset ${JSON.stringify(el.assetId)}` });
          continue;
        }
        const found = resolveId(sourceDoc, asset.source);
        if (!found) {
          errors.push({ path: `${ep}.source`, message: `asset ${JSON.stringify(el.assetId)} references unknown source id ${JSON.stringify(asset.source)}` });
          continue;
        }
        elements.push({
          id: el.id,
          kind: 'source',
          source: asset.source,
          elements: [found],
          transform: transformString(el.position, [el.transform, asset.baseTransform]),
        });
      }
    }

    return {
      id: sheet.id,
      title: sheet.title,
      width: sheet.dimensions.width,
      height: sheet.dimensions.height,
      elements,
    };
  });

  return { sheets, errors };
}
