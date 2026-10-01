import type { Project } from '../../model/src/types';
import { resolve } from './resolve';
import { transformString } from './transform';

/** A concrete element ready to assemble: references resolved to DOM nodes. */
export type FlatElement =
  | { id: string; kind: 'text'; text: string; styleId: string; x: number; y: number; transform: string }
  | { id: string; kind: 'source'; sourceId: string; selector: string; elements: Element[]; transform: string };

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

/** Compiler link step: resolve asset/instance references and selectors into
 *  concrete elements. No layout decisions are made here. */
export function flatten(
  project: Project,
  sources: Map<string, Document>,
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
        const doc = sources.get(el.sourceId);
        if (!doc) {
          errors.push({ path: `${ep}.sourceId`, message: `unknown source ${JSON.stringify(el.sourceId)}` });
          continue;
        }
        const found = resolve(doc, el.sourceSelector);
        if (found.length === 0) {
          errors.push({ path: `${ep}.sourceSelector`, message: `selector resolves to nothing: ${JSON.stringify(el.sourceSelector)}` });
          continue;
        }
        elements.push({
          id: el.id,
          kind: 'source',
          sourceId: el.sourceId,
          selector: el.sourceSelector,
          elements: found,
          transform: transformString(el.position, [el.transform]),
        });
      } else {
        const asset = assets.get(el.assetId);
        if (!asset) {
          errors.push({ path: `${ep}.assetId`, message: `unknown asset ${JSON.stringify(el.assetId)}` });
          continue;
        }
        const doc = sources.get(asset.sourceId);
        if (!doc) {
          errors.push({ path: `${ep}.sourceId`, message: `asset ${JSON.stringify(el.assetId)} references unknown source ${JSON.stringify(asset.sourceId)}` });
          continue;
        }
        const found = resolve(doc, asset.sourceSelector);
        if (found.length === 0) {
          errors.push({ path: `${ep}.sourceSelector`, message: `asset selector resolves to nothing: ${JSON.stringify(asset.sourceSelector)}` });
          continue;
        }
        elements.push({
          id: el.id,
          kind: 'source',
          sourceId: asset.sourceId,
          selector: asset.sourceSelector,
          elements: found,
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
