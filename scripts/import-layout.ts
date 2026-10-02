import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { importLayoutYaml } from '../packages/model/src/yaml-import';

// One-time migration: templates/layout.yaml + its source SVG -> templates/project.json.
const root = process.cwd();
const yamlText = readFileSync(resolve(root, 'templates/layout.yaml'), 'utf8');

const project = importLayoutYaml(yamlText);
const out = resolve(root, 'templates/project.json');
writeFileSync(out, JSON.stringify(project, null, 2) + '\n', 'utf8');

console.log(
  `wrote ${out} — ${project.sheets.length} sheets, ` +
  `${Object.keys(project.styles).length} styles, ${project.papers.length} paper(s)`,
);
