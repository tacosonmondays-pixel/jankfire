#!/usr/bin/env node
// Ship the owner's map edits: node tools/mapedits.mjs add jankfire-edits-<map>.json [more.json ...]
// Checks the file, appends its ops to shared/mapedits/<map>.js (creating it and registering it in index.js), then
// replays every shipped edit on a fresh build and prints what applied and what's stale.
//   node tools/mapedits.mjs check     just the replay report
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..'), DIR = path.join(ROOT, 'shared/mapedits');
const { validEdits } = await import('../shared/mapedit.js');
const [cmd, ...files] = process.argv.slice(2);
if (cmd === 'add') {
  for (const f of files) {
    const e = JSON.parse(fs.readFileSync(f, 'utf8'));
    if (!validEdits(e) || !/^[a-z0-9_]+$/.test(e.map)) { console.error(f, ': not a valid edit file'); process.exit(1); }
    const file = path.join(DIR, e.map + '.js');
    let cur = { map: e.map, v: 1, ops: [] };
    if (fs.existsSync(file)) cur = (await import(file + '?t=' + Date.now())).default;
    cur.ops.push(...e.ops);
    fs.writeFileSync(file, `// ${e.map}: the owner's edits from the map editor (tools/mapedits.mjs add). replayed by shared/mapedits/apply.js\nexport default {\n  map: ${JSON.stringify(cur.map)}, v: 1,\n  ops: [\n${cur.ops.map((o) => '    ' + JSON.stringify(o) + ',').join('\n')}\n  ],\n};\n`);
    const idx = path.join(DIR, 'index.js');
    let src = fs.readFileSync(idx, 'utf8');
    const name = 'e_' + e.map;
    if (!src.includes(`'./${e.map}.js'`)) {
      src = src.replace('export const EDITS = {', `import ${name} from './${e.map}.js';\nexport const EDITS = {\n  ${e.map}: ${name},`);
      fs.writeFileSync(idx, src);
    }
    console.log(`${f}: ${e.ops.length} ops added to shared/mapedits/${e.map}.js (${cur.ops.length} in all)`);
  }
} else if (cmd !== 'check') { console.log('usage: node tools/mapedits.mjs add <file.json> ... | check'); process.exit(1); }
const { EDIT_REPORT } = await import('../shared/mapedits/apply.js');
for (const [id, r] of Object.entries(EDIT_REPORT)) console.log(`${id}: ${r.ops} ops, ${r.stale} stale`);
if (!Object.keys(EDIT_REPORT).length) console.log('no shipped map edits');
