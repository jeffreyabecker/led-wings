import { PDFDocument } from 'pdf-lib';
import type { EnginePage } from '../../packages/assembler/src/engine';

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}

export function downloadText(text: string, filename: string, mime = 'application/octet-stream'): void {
  downloadBlob(new Blob([text], { type: mime }), filename);
}

function svgToCanvas(svg: string, scale: number): Promise<HTMLCanvasElement> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(new Blob([svg], { type: 'image/svg+xml;charset=utf-8' }));
    const img = new Image();
    img.onload = () => {
      const w = Math.max(1, img.naturalWidth || img.width);
      const h = Math.max(1, img.naturalHeight || img.height);
      const canvas = document.createElement('canvas');
      canvas.width = Math.round(w * scale);
      canvas.height = Math.round(h * scale);
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        URL.revokeObjectURL(url);
        reject(new Error('no 2d context'));
        return;
      }
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.scale(scale, scale);
      ctx.drawImage(img, 0, 0);
      URL.revokeObjectURL(url);
      resolve(canvas);
    };
    img.onerror = (e) => {
      URL.revokeObjectURL(url);
      reject(e);
    };
    img.src = url;
  });
}

async function canvasToPngBytes(canvas: HTMLCanvasElement): Promise<Uint8Array> {
  const blob = await new Promise<Blob>((res, rej) => {
    canvas.toBlob((b) => (b ? res(b) : rej(new Error('toBlob failed'))), 'image/png');
  });
  return new Uint8Array(await blob.arrayBuffer());
}

function mmToPt(mm: number): number {
  return (mm * 72) / 25.4;
}

/** Render every page to a high-DPI PNG and embed into a single PDF (raster). */
export async function exportPdf(
  trim: { width: number; height: number },
  pages: EnginePage[],
  onProgress?: (done: number, total: number) => void,
): Promise<void> {
  const pdf = await PDFDocument.create();
  const w = mmToPt(trim.width);
  const h = mmToPt(trim.height);
  let i = 0;
  for (const page of pages) {
    const png = await svgToCanvas(page.svg, 3);
    const bytes = await canvasToPngBytes(png);
    const img = await pdf.embedPng(bytes);
    const p = pdf.addPage([w, h]);
    p.drawImage(img, { x: 0, y: 0, width: w, height: h });
    i += 1;
    onProgress?.(i, pages.length);
  }
  const out = await pdf.save();
  downloadBlob(new Blob([out as unknown as BlobPart], { type: 'application/pdf' }), 'sheets.pdf');
}

export function exportSvgs(pages: EnginePage[]): void {
  pages.forEach((p, i) => setTimeout(() => downloadText(p.svg, p.fileName, 'image/svg+xml'), i * 150));
}

export async function exportContactSheet(pages: EnginePage[], cols = 5): Promise<void> {
  const canvases = await Promise.all(pages.map((p) => svgToCanvas(p.svg, 0.25)));
  const tw = canvases[0]?.width ?? 1;
  const th = canvases[0]?.height ?? 1;
  const rows = Math.ceil(canvases.length / cols);
  const canvas = document.createElement('canvas');
  canvas.width = cols * tw;
  canvas.height = rows * th;
  const ctx = canvas.getContext('2d')!;
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  canvases.forEach((c, i) => {
    const r = Math.floor(i / cols);
    const col = i % cols;
    ctx.drawImage(c, col * tw, r * th);
  });
  const blob = await new Promise<Blob>((res, rej) => {
    canvas.toBlob((b) => (b ? res(b) : rej(new Error('toBlob failed'))), 'image/png');
  });
  downloadBlob(blob, 'contact-sheet.png');
}
