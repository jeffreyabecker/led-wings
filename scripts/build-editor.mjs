import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { join } from 'node:path';

// Bundle the React editor with the native esbuild binary directly (spawned with
// inherited stdio), because esbuild's JS API spawns a piped service process that
// is blocked in this environment.
const platform = process.platform;
const arch = process.arch === 'x64' ? 'x64' : process.arch === 'arm64' ? 'arm64' : process.arch;
const binName = platform === 'win32' ? 'esbuild.exe' : 'esbuild';
const bin = join(process.cwd(), 'node_modules', `@esbuild/${platform}-${arch}`, binName);

if (!existsSync(bin)) {
  console.error(`esbuild binary not found at ${bin}. Run: npm install`);
  process.exit(1);
}

const args = [
  'editor/src/main.tsx',
  '--bundle',
  '--outfile=dist/editor.js',
  '--loader:.tsx=tsx',
  '--loader:.ts=ts',
  '--loader:.json=json',
  '--jsx=automatic',
  '--format=iife',
  '--define:process.env.NODE_ENV="development"',
  '--sourcemap',
];

const r = spawnSync(bin, args, { stdio: 'inherit', cwd: process.cwd() });
process.exit(r.status ?? 1);
