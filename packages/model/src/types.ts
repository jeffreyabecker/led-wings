// Project model — the typed JSON document the editor owns. This is the source
// of truth. The legacy layout.yaml is imported into this shape and then retired.

export interface Vec2 {
  x: number;
  y: number;
}

export interface Size {
  width: number;
  height: number;
}

/** Element transform: `translate(position) rotate(rotate) scale(scale.x scale.y)`.
 *  Negative scale is the mirror operator. Position is applied outermost. */
export interface Transform {
  rotate?: number;
  scale?: Vec2;
}

/** Tiling overlap: a single number (same x and y) or `{x, y}`. */
export type Overlap = number | Vec2;

export interface ProjectMeta {
  name: string;
  units: 'mm';
  defaultPaper?: string;
}

/** A source SVG, referenced by href and resolved to content at load time. */
export interface Source {
  name: string;
  href: string;
}

/** A reusable, named source component: an element id in the source SVG plus an
 *  optional base transform. Instances reference assets; edit the asset once and
 *  every instance follows. */
export interface Asset {
  id: string;
  name: string;
  source: string;
  baseTransform?: Transform;
}

/** Structured CSS declaration block: property -> value. */
export type CssDecl = Record<string, string>;

/** A physical paper definition. */
export interface Paper {
  id: string;
  name: string;
  trim: Size;
  safeArea: Size;
  overlap: Overlap;
}

export type Element =
  | { id: string; kind: 'instance'; assetId: string; position: Vec2; transform?: Transform }
  | { id: string; kind: 'source'; source: string; position: Vec2; transform?: Transform }
  | { id: string; kind: 'text'; text: string; position: Vec2; styleId?: string; transform?: Transform };

/** Editor presentation grouping. Elements stay on the sheet; a layer references
 *  element ids for show/hide/lock. The assembler ignores layers. */
export interface Layer {
  id: string;
  name: string;
  visible: boolean;
  locked: boolean;
  elementIds: string[];
}

export interface Sheet {
  id: string;
  title: string;
  dimensions: Size;
  elements: Element[];
  layers?: Layer[];
}

export interface Output {
  id: string;
  name: string;
  sheetIds?: string[];
  paperId: string;
  format: 'svg' | 'pdf' | 'contact-sheet';
}

export interface Project {
  meta: ProjectMeta;
  source: Source;
  assets: Asset[];
  styles: Record<string, CssDecl>;
  papers: Paper[];
  sheets: Sheet[];
  outputs: Output[];
}
