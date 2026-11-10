// Gameplay fingerprint of every map: boxes (minus the look-only Blender tags), spawns, team spawns, sites, bounds, the
// nav graph... everything physics, bots and hits read. The Blender architecture must leave it identical.
// usage: node tools/arch/gamehash.mjs [checkout dir, default .] > hashes.txt   (diff two of these: they must match)
import { createHash } from 'crypto';
import path from 'path';
import { pathToFileURL } from 'url';
const dir = path.resolve(process.argv[2] || '.');
const { MAPS } = await import(pathToFileURL(path.join(dir, 'shared/map.js')).href);
const LOOK = new Set(['av', 'ai', 'arch', 'props', 'deco']); // look-only: Blender tags and lists, render-only boxes
const clean = (k, v) => (LOOK.has(k) || typeof v === 'function' ? undefined : v);
const h = (o) => createHash('sha1').update(JSON.stringify(o, clean) || '').digest('hex').slice(0, 12);
for (const id of Object.keys(MAPS).sort()) {
  const m = MAPS[id];
  const boxes = m.boxes.map((b) => ({ ...b }));
  const rest = Object.fromEntries(Object.entries(m).filter(([k]) => !['boxes', 'graph'].includes(k)));
  let g = '-';
  try { const gr = m.graph; g = gr ? h(gr) : '-'; } catch (e) { g = 'ERR ' + e.message; }
  console.log(id.padEnd(14), 'boxes', String(boxes.length).padStart(5), h(boxes), 'rest', h(rest), 'nav', g);
}
