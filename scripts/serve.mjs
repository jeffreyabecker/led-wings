import { createServer } from 'node:http';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, extname, resolve, sep } from 'node:path';

// Dependency-free static file server with `Cache-Control: no-store`, plus a
// POST /api/save endpoint that writes a file into the working directory.
const root = process.cwd();
const PORT = Number(process.env.PORT) || 8000;

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml; charset=utf-8',
  '.png': 'image/png',
  '.map': 'application/json; charset=utf-8',
};

const rootPrefix = root.endsWith(sep) ? root : root + sep;

function readBody(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', (chunk) => {
      data += chunk;
      if (data.length > 10_000_000) {
        reject(new Error('body too large'));
        req.destroy();
      }
    });
    req.on('end', () => resolve(data));
    req.on('error', reject);
  });
}

function json(res, status, obj) {
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(obj));
}

createServer(async (req, res) => {
  try {
    const url = new URL(req.url, 'http://localhost');
    const pathname = decodeURIComponent(url.pathname);

    if (req.method === 'POST' && pathname === '/api/save') {
      const body = await readBody(req);
      let payload;
      try {
        payload = JSON.parse(body);
      } catch {
        json(res, 400, { ok: false, error: 'invalid JSON body' });
        return;
      }
      const { path, content } = payload ?? {};
      if (typeof path !== 'string' || typeof content !== 'string') {
        json(res, 400, { ok: false, error: 'expected { path, content }' });
        return;
      }
      const rel = path.replace(/^[\\/]+/, '');
      if (!rel || rel.endsWith('/') || rel.endsWith('\\')) {
        json(res, 400, { ok: false, error: 'invalid path' });
        return;
      }
      const target = resolve(root, rel);
      if (target !== root && !target.startsWith(rootPrefix)) {
        json(res, 403, { ok: false, error: 'path outside working directory' });
        return;
      }
      await mkdir(dirname(target), { recursive: true });
      await writeFile(target, content, 'utf8');
      json(res, 200, { ok: true, path: rel });
      return;
    }

    if (req.method !== 'GET' && req.method !== 'HEAD') {
      res.writeHead(405);
      res.end('method not allowed');
      return;
    }

    const file = resolve(root, '.' + (pathname === '/' ? '/index.html' : pathname));
    if (file !== root && !file.startsWith(rootPrefix)) {
      res.writeHead(403);
      res.end('forbidden');
      return;
    }
    const data = await readFile(file);
    res.writeHead(200, {
      'Content-Type': MIME[extname(file).toLowerCase()] || 'application/octet-stream',
      'Cache-Control': 'no-store',
    });
    res.end(data);
  } catch (err) {
    if (err && err.code === 'ENOENT') {
      res.writeHead(404);
      res.end('not found');
    } else {
      res.writeHead(500);
      res.end(String(err));
    }
  }
}).listen(PORT, () => {
  console.log(`serving ${root} at http://127.0.0.1:${PORT}`);
});
