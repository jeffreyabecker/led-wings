import { useEffect, useMemo, useRef, useState } from 'react';
import type { Element as ModelElement, Project, Sheet, Transform, Vec2 } from '../../packages/model/src/types';
import { validateProject } from '../../packages/model/src/validate';
import { parseCss } from '../../packages/model/src/css';
import { assembleProject, cssToText, flatten, type FlatSheet } from '../../packages/assembler/src/index';
import { buildPaletteTree, renderElementPreview, renderSheetBody, sourceDocs, type PaletteNode } from './lib';
import { exportContactSheet, exportPdf, exportSvgs } from './export';

interface DragState {
  eid: string;
  startX: number;
  startY: number;
  scale: number;
  origX: number;
  origY: number;
}

function NumField(props: {
  label: string;
  value: number;
  onChange: (n: number) => void;
  step?: number;
}) {
  const v = Number.isFinite(props.value) ? props.value : 0;
  return (
    <label>
      {props.label}
      <input
        type="number"
        step={props.step ?? 0.1}
        value={v}
        onChange={(e) => props.onChange(Number(e.target.value))}
      />
    </label>
  );
}

function PaletteNodeView({ node, depth, onAdd, onHover }: {
  node: PaletteNode;
  depth: number;
  onAdd: (sourceId: string, selector: string) => void;
  onHover: (sourceId: string, selector: string) => void;
}) {
  const [open, setOpen] = useState(depth < 2);
  const hasChildren = node.children.length > 0;
  return (
    <div className="tree-node">
      <div className="tree-row" style={{ paddingLeft: depth * 14 }} onMouseEnter={() => onHover(node.sourceId, node.selector)}>
        <span className={'tree-toggle' + (hasChildren ? '' : ' leaf')} onClick={() => hasChildren && setOpen(!open)}>
          {hasChildren ? (open ? '\u25BE' : '\u25B8') : '\u00B7'}
        </span>
        <button className="tree-label" title={node.selector} onClick={() => onAdd(node.sourceId, node.selector)}>
          {node.label}
        </button>
      </div>
      {hasChildren && open && node.children.map((c, i) => (
        <PaletteNodeView key={c.selector + '-' + i} node={c} depth={depth + 1} onAdd={onAdd} onHover={onHover} />
      ))}
    </div>
  );
}

export function App() {
  const [project, setProject] = useState<Project | null>(null);
  const [selectedSheetId, setSelectedSheetId] = useState<string | null>(null);
  const [selectedElementId, setSelectedElementId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('');
  const [preview, setPreview] = useState<{ sourceId: string; selector: string } | null>(null);
  const [styleText, setStyleText] = useState('');
  const stylesReady = useRef(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const dragRef = useRef<DragState | null>(null);
  const [tab, setTab] = useState<'element' | 'sheets' | 'styles' | 'output'>('element');

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/templates/project.json');
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = (await res.json()) as Project;
        stylesReady.current = true;
        setProject(data);
        setSelectedSheetId(data.sheets[0]?.id ?? null);
        setStyleText(cssToText(data.styles));
      } catch (e) {
        setStatus('Could not load the default project: ' + (e as Error).message + '. Use Open to load a project.json.');
      }
    })();
  }, []);

  // Parse the style textarea back into the structured styles map (debounced).
  useEffect(() => {
    if (!stylesReady.current) return;
    const id = setTimeout(() => {
      setProject((p) => (p ? { ...p, styles: parseCss(styleText) } : p));
    }, 250);
    return () => clearTimeout(id);
  }, [styleText]);

  const flat = useMemo(() => (project ? flatten(project, sourceDocs(project)) : null), [project]);
  const validation = useMemo(() => (project ? validateProject(project) : []), [project]);
  const palette = useMemo(() => (project ? buildPaletteTree(project) : []), [project?.source]);

  // Full assembly (tiling + warnings) is debounced so drag/typing stays responsive.
  const [engine, setEngine] = useState<ReturnType<typeof assembleProject> | null>(null);
  useEffect(() => {
    if (!project) {
      setEngine(null);
      return;
    }
    const id = setTimeout(() => setEngine(assembleProject(project)), 200);
    return () => clearTimeout(id);
  }, [project]);

  const sheet = project?.sheets.find((s) => s.id === selectedSheetId) ?? null;
  const flatSheet: FlatSheet | null = flat?.sheets.find((s) => s.id === selectedSheetId) ?? null;
  const selectedElement = sheet?.elements.find((e) => e.id === selectedElementId) ?? null;
  const paper = project?.papers[0];
  const previewSvg = preview && project ? renderElementPreview(project, preview.sourceId, preview.selector) : null;

  function updateSheet(next: Sheet) {
    if (!project) return;
    setProject({ ...project, sheets: project.sheets.map((s) => (s.id === next.id ? next : s)) });
  }

  function updateElement(sheetId: string, next: ModelElement) {
    if (!project) return;
    setProject({
      ...project,
      sheets: project.sheets.map((s) =>
        s.id === sheetId ? { ...s, elements: s.elements.map((e) => (e.id === next.id ? next : e)) } : s,
      ),
    });
  }

  function setPosition(el: ModelElement, position: Vec2): ModelElement {
    return { ...el, position } as ModelElement;
  }

  function setTransform(el: ModelElement, patch: Partial<Transform>): ModelElement {
    const cur = el.transform ?? {};
    return { ...el, transform: { ...cur, ...patch } } as ModelElement;
  }

  function addElement(sheetId: string, el: ModelElement) {
    if (!project) return;
    setProject({
      ...project,
      sheets: project.sheets.map((s) =>
        s.id === sheetId ? { ...s, elements: [...s.elements, el] } : s,
      ),
    });
  }

  function addSource(sheetId: string, sourceId: string, selector: string) {
    const id = `el-${Math.random().toString(36).slice(2, 9)}`;
    addElement(sheetId, { id, kind: 'source', sourceId, sourceSelector: selector, position: { x: 10, y: 10 } });
    setSelectedElementId(id);
  }

  function addText(sheetId: string) {
    const id = `el-${Math.random().toString(36).slice(2, 9)}`;
    addElement(sheetId, { id, kind: 'text', text: 'Label', position: { x: 20, y: 20 }, styleId: 'label' });
    setSelectedElementId(id);
  }

  function mirrorElement() {
    if (!project || !selectedSheetId || !selectedElement || selectedElement.kind === 'text') return;
    const src = selectedElement;
    const sx = src.transform?.scale?.x ?? 1;
    const sy = src.transform?.scale?.y ?? 1;
    const mirrored: ModelElement = {
      ...src,
      id: `el-${Math.random().toString(36).slice(2, 9)}`,
      transform: { ...(src.transform ?? {}), scale: { x: -sx, y: sy } },
    } as ModelElement;
    addElement(selectedSheetId, mirrored);
    setSelectedElementId(mirrored.id);
  }

  function addSheet() {
    if (!project) return;
    const id = `sheet-${project.sheets.length + 1}-${Math.random().toString(36).slice(2, 7)}`;
    const s: Sheet = { id, title: `Sheet ${project.sheets.length + 1}`, dimensions: { width: 260, height: 200 }, elements: [] };
    setProject({ ...project, sheets: [...project.sheets, s] });
    setSelectedSheetId(id);
    setSelectedElementId(null);
  }

  function duplicateSheet(id: string) {
    if (!project) return;
    const src = project.sheets.find((s) => s.id === id);
    if (!src) return;
    const copy: Sheet = {
      ...src,
      id: `sheet-${Math.random().toString(36).slice(2, 9)}`,
      title: src.title + ' (copy)',
      elements: src.elements.map((e) => ({ ...e, id: `el-${Math.random().toString(36).slice(2, 9)}` })),
      layers: src.layers
        ? src.layers.map((l) => ({ ...l, id: `layer-${Math.random().toString(36).slice(2, 9)}` }))
        : undefined,
    };
    setProject({ ...project, sheets: [...project.sheets, copy] });
    setSelectedSheetId(copy.id);
    setSelectedElementId(null);
  }

  function deleteSheet(id: string) {
    if (!project) return;
    const sheets = project.sheets.filter((s) => s.id !== id);
    setProject({ ...project, sheets });
    if (selectedSheetId === id) setSelectedSheetId(sheets[0]?.id ?? null);
  }



  function onPointerDown(e: React.PointerEvent<SVGSVGElement>) {
    const target = (e.target as Element).closest?.('[data-eid]');
    if (!target) {
      setSelectedElementId(null);
      return;
    }
    const eid = target.getAttribute('data-eid');
    if (!eid) return;
    setSelectedElementId(eid);
    const el = sheet?.elements.find((x) => x.id === eid);
    if (!el || !flatSheet) return;
    const ctm = e.currentTarget.getScreenCTM();
    if (!ctm) return;
    dragRef.current = {
      eid,
      startX: e.clientX,
      startY: e.clientY,
      scale: ctm.a || 1,
      origX: el.position.x,
      origY: el.position.y,
    };
    e.currentTarget.setPointerCapture(e.pointerId);
  }

  function onPointerMove(e: React.PointerEvent<SVGSVGElement>) {
    const d = dragRef.current;
    if (!d || !project || !selectedSheetId) return;
    const dx = (e.clientX - d.startX) / d.scale;
    const dy = (e.clientY - d.startY) / d.scale;
    const el = sheet?.elements.find((x) => x.id === d.eid);
    if (!el) return;
    updateElement(selectedSheetId, setPosition(el, { x: d.origX + dx, y: d.origY + dy }));
  }

  function onPointerUp(e: React.PointerEvent<SVGSVGElement>) {
    dragRef.current = null;
    if (e.currentTarget.hasPointerCapture(e.pointerId)) e.currentTarget.releasePointerCapture(e.pointerId);
  }

  function openFile() {
    fileRef.current?.click();
  }

  function onOpenFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const data = JSON.parse(reader.result as string) as Project;
        stylesReady.current = true;
        setProject(data);
        setSelectedSheetId(data.sheets[0]?.id ?? null);
        setSelectedElementId(null);
        setStyleText(cssToText(data.styles));
        setStatus('Loaded ' + f.name);
      } catch (err) {
        setStatus('Failed to parse project: ' + (err as Error).message);
      }
    };
    reader.readAsText(f);
    e.target.value = '';
  }

  async function saveProject() {
    if (!project) return;
    try {
      const res = await fetch('/api/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: 'templates/project.json', content: JSON.stringify(project, null, 2) + '\n' }),
      });
      if (!res.ok) throw new Error('HTTP ' + res.status + ': ' + (await res.text()));
      setStatus('Saved templates/project.json');
    } catch (err) {
      setStatus('Save failed: ' + (err as Error).message);
    }
  }

  return (
    <div className="app">
      <div className="topbar">
        <span className="title">Sheet Layout Editor</span>
        <span className="muted">{status || project?.meta.name || ''}</span>
        <input ref={fileRef} type="file" accept=".json,application/json" style={{ display: 'none' }} onChange={onOpenFile} />
        <button onClick={openFile}>Open…</button>
        <button onClick={saveProject} disabled={!project}>Save</button>
        <button onClick={() => engine && exportSvgs(engine.pages)} disabled={!engine?.pages.length}>SVGs</button>
        <button
          disabled={!engine?.pages.length}
          onClick={() => {
            if (!engine || !paper) return;
            setStatus('Exporting PDF…');
            exportPdf(paper.trim, engine.pages, (done, total) => setStatus(`Exporting PDF (${done}/${total})…`))
              .then(() => setStatus('PDF downloaded'))
              .catch((e) => setStatus('PDF export failed: ' + ((e as Error)?.message ?? String(e))));
          }}
        >
          PDF
        </button>
        <button
          disabled={!engine?.pages.length}
          onClick={() => {
            if (!engine) return;
            setStatus('Building contact sheet…');
            exportContactSheet(engine.pages)
              .then(() => setStatus('Contact sheet downloaded'))
              .catch((e) => setStatus('Contact sheet failed: ' + ((e as Error)?.message ?? String(e))));
          }}
        >
          Contact sheet
        </button>
      </div>

      <div className="main">
        <div className="panel panel-left">
          <h2>Elements</h2>
          <button className="palette-item" onClick={() => selectedSheetId && addText(selectedSheetId)}>+ Text label</button>
          <div className="tree-scroll">
            {palette.map((n, i) => (
              <PaletteNodeView
                key={n.selector + '-' + i}
                node={n}
                depth={0}
                onAdd={(sid, sel) => selectedSheetId && addSource(selectedSheetId, sid, sel)}
                onHover={(sid, sel) => setPreview({ sourceId: sid, selector: sel })}
              />
            ))}
          </div>
          <div className="preview-box">
            {previewSvg ? (
              <div dangerouslySetInnerHTML={{ __html: previewSvg }} />
            ) : (
              <span className="muted">Hover an element to preview</span>
            )}
          </div>
        </div>

        <div className="center">
          <div className="canvas-wrap">
            {flatSheet ? (
              <svg
                className="canvas-svg"
                viewBox={`0 0 ${flatSheet.width} ${flatSheet.height}`}
                onPointerDown={onPointerDown}
                onPointerMove={onPointerMove}
                onPointerUp={onPointerUp}
                dangerouslySetInnerHTML={{ __html: renderSheetBody(flatSheet, project?.styles ?? {}, selectedElementId) }}
              />
            ) : (
              <span className="muted">No sheet selected.</span>
            )}
          </div>
        </div>

        <div className="panel inspector">
          <div className="tab-bar">
            <button className={'tab' + (tab === 'element' ? ' active' : '')} onClick={() => setTab('element')}>Element</button>
            <button className={'tab' + (tab === 'sheets' ? ' active' : '')} onClick={() => setTab('sheets')}>Sheets</button>
            <button className={'tab' + (tab === 'styles' ? ' active' : '')} onClick={() => setTab('styles')}>Styles</button>
            <button className={'tab' + (tab === 'output' ? ' active' : '')} onClick={() => setTab('output')}>Output</button>
          </div>

          {tab === 'element' && (selectedElement ? (
            <>
              <p className="muted">{selectedElement.kind} · {selectedElement.id}</p>
              <NumField label="X" value={selectedElement.position.x} onChange={(n) => selectedSheetId && updateElement(selectedSheetId, setPosition(selectedElement, { x: n, y: selectedElement.position.y }))} />
              <NumField label="Y" value={selectedElement.position.y} onChange={(n) => selectedSheetId && updateElement(selectedSheetId, setPosition(selectedElement, { x: selectedElement.position.x, y: n }))} />
              {selectedElement.kind === 'text' && (
                <>
                  <label>
                    Text
                    <input value={selectedElement.text} onChange={(e) => updateElement(selectedSheetId!, { ...selectedElement, text: e.target.value } as ModelElement)} />
                  </label>
                  <label>
                    Style
                    <select
                      value={selectedElement.styleId ?? 'label'}
                      onChange={(e) => updateElement(selectedSheetId!, { ...selectedElement, styleId: e.target.value } as ModelElement)}
                    >
                      {project ? Object.keys(project.styles).map((k) => <option key={k} value={k}>{k}</option>) : null}
                    </select>
                  </label>
                </>
              )}
              <NumField label="Rotate (°)" step={1} value={selectedElement.transform?.rotate ?? 0} onChange={(n) => updateElement(selectedSheetId!, setTransform(selectedElement, { rotate: n }))} />
              <div className="row">
                <NumField label="Scale X" value={selectedElement.transform?.scale?.x ?? 1} onChange={(n) => updateElement(selectedSheetId!, setTransform(selectedElement, { scale: { x: n, y: selectedElement.transform?.scale?.y ?? 1 } }))} />
                <NumField label="Scale Y" value={selectedElement.transform?.scale?.y ?? 1} onChange={(n) => updateElement(selectedSheetId!, setTransform(selectedElement, { scale: { x: selectedElement.transform?.scale?.x ?? 1, y: n } }))} />
              </div>
              {selectedElement.kind !== 'text' && (
                <>
                  <p className="muted">{selectedElement.kind === 'source' ? selectedElement.sourceSelector : 'instance of ' + selectedElement.assetId}</p>
                  <button className="palette-item" style={{ marginTop: 8 }} onClick={mirrorElement}>Mirror (copy)</button>
                </>
              )}
              <button className="palette-item" style={{ marginTop: 8 }} onClick={() => { setSelectedElementId(null); }}>Deselect</button>
            </>
          ) : (
            <p className="muted">Select an element on the canvas.</p>
          ))}

          {tab === 'sheets' && (
            <>
              {sheet && (
                <>
                  <h2>Sheet</h2>
                  <label>
                    Title
                    <input value={sheet.title} onChange={(e) => updateSheet({ ...sheet, title: e.target.value })} />
                  </label>
                  <div className="row">
                    <NumField label="Width" value={sheet.dimensions.width} onChange={(n) => updateSheet({ ...sheet, dimensions: { ...sheet.dimensions, width: n } })} />
                    <NumField label="Height" value={sheet.dimensions.height} onChange={(n) => updateSheet({ ...sheet, dimensions: { ...sheet.dimensions, height: n } })} />
                  </div>
                </>
              )}
              <div className="sheet-list">
                {project?.sheets.map((s) => (
                  <button
                    key={s.id}
                    className={'sheet-row' + (s.id === selectedSheetId ? ' active' : '')}
                    onClick={() => {
                      setSelectedSheetId(s.id);
                      setSelectedElementId(null);
                    }}
                  >
                    {s.title}
                  </button>
                ))}
              </div>
              <div className="sheet-actions">
                <button onClick={addSheet}>+ Sheet</button>
                <button disabled={!selectedSheetId} onClick={() => selectedSheetId && duplicateSheet(selectedSheetId)}>Duplicate</button>
                <button disabled={!selectedSheetId} onClick={() => selectedSheetId && deleteSheet(selectedSheetId)}>Delete</button>
              </div>
            </>
          )}

          {tab === 'styles' && (
            <>
              <h2>Styles (CSS)</h2>
              <textarea
                className="style-text"
                value={styleText}
                onChange={(e) => setStyleText(e.target.value)}
                spellCheck={false}
              />
            </>
          )}

          {tab === 'output' && (
            <>
              <h2>Paper</h2>
              {paper && project ? (
                <>
                  <div className="row">
                    <NumField label="Trim W" value={paper.trim.width} onChange={(n) => setProject({ ...project, papers: project.papers.map((p, i) => (i === 0 ? { ...p, trim: { ...p.trim, width: n } } : p)) })} />
                    <NumField label="Trim H" value={paper.trim.height} onChange={(n) => setProject({ ...project, papers: project.papers.map((p, i) => (i === 0 ? { ...p, trim: { ...p.trim, height: n } } : p)) })} />
                  </div>
                  <div className="row">
                    <NumField label="Safe W" value={paper.safeArea.width} onChange={(n) => setProject({ ...project, papers: project.papers.map((p, i) => (i === 0 ? { ...p, safeArea: { ...p.safeArea, width: n } } : p)) })} />
                    <NumField label="Safe H" value={paper.safeArea.height} onChange={(n) => setProject({ ...project, papers: project.papers.map((p, i) => (i === 0 ? { ...p, safeArea: { ...p.safeArea, height: n } } : p)) })} />
                  </div>
                  <NumField label="Overlap" value={typeof paper.overlap === 'number' ? paper.overlap : paper.overlap.x} onChange={(n) => setProject({ ...project, papers: project.papers.map((p, i) => (i === 0 ? { ...p, overlap: n } : p)) })} />
                </>
              ) : null}

              <h2 style={{ marginTop: 16 }}>Output</h2>
              <p className="muted">
                {engine ? `${engine.sheetCount} sheets → ${engine.pages.length} pages (${engine.tiledPages} tiled)` : ''}
              </p>
              {validation.map((v, i) => (
                <p key={i} className="error">{v.path}: {v.message}</p>
              ))}
              {engine?.warnings.map((w, i) => (
                <p key={i} className="warn">{w.sheet}: {w.message}</p>
              ))}
              {status ? <p className="muted">{status}</p> : null}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
