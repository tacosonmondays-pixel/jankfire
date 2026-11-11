// Round 4 prop inventory: every Blender prop placement the maps make (shared/propcap.js), per map, and what each
// model costs (triangles near / far, materials) read straight from public/models/p_<id>.glb.
// usage: node tools/blender/props_r4.mjs [--md]      (--md: a markdown table, as in tools/blender/compare/r4_inventory.md)
import fs from 'fs';
import path from 'path';
import url from 'url';

const ROOT = path.resolve(path.dirname(url.fileURLToPath(import.meta.url)), '../..');
const { MAPS } = await import(url.pathToFileURL(path.join(ROOT, 'shared/map.js')).href);
await import(url.pathToFileURL(path.join(ROOT, 'shared/royale.js')).href); // (registers Jankburg)
const md = process.argv.includes('--md');

// a glb's JSON chunk: triangles per LOD (nodes under one named lod1 = far), materials per LOD
function glbStats(file) {
  if (!fs.existsSync(file)) return null;
  const b = fs.readFileSync(file), len = b.readUInt32LE(12), j = JSON.parse(b.subarray(20, 20 + len).toString('utf8'));
  const parent = new Map();
  (j.nodes || []).forEach((n, i) => (n.children || []).forEach((c) => parent.set(c, i)));
  const isFar = (i) => { for (let p = i; p !== undefined; p = parent.get(p)) if (/^lod1(\.\d+)?$/.test(j.nodes[p].name || '')) return true; return false; };
  const out = { tris: [0, 0], mats: [new Set(), new Set()] };
  (j.nodes || []).forEach((n, i) => {
    if (n.mesh === undefined) return;
    const L = isFar(i) ? 1 : 0;
    for (const pr of j.meshes[n.mesh].primitives) {
      const a = j.accessors[pr.indices !== undefined ? pr.indices : pr.attributes.POSITION];
      out.tris[L] += Math.round(a.count / 3);
      if (pr.material !== undefined) out.mats[L].add((j.materials[pr.material].name || '').replace(/\.\d+$/, ''));
    }
  });
  return { lod0: out.tris[0], lod1: out.tris[1], m0: [...out.mats[0]].join('+'), m1: [...out.mats[1]].join('+'), kb: Math.round(b.length / 1024) };
}

const by = {}, maps = {};
for (const [mid, m] of Object.entries(MAPS)) for (const l of [m.boxes.props, m.deco && m.deco.props]) for (const p of l || []) {
  const id = p.a ? p.id : p.id + ' (round 1)';
  (by[id] ||= { n: 0, maps: {} }).n++;
  by[id].maps[mid] = (by[id].maps[mid] || 0) + 1;
  (maps[mid] ||= {})[id] = (maps[mid][id] || 0) + 1;
}
const model = (id) => (id === 'car' ? 'p_car_sedan / p_car_hatch / p_car_taxi (p_car)' : 'p_' + id.replace(' (round 1)', ''));
const rows = Object.entries(by).sort((a, b) => b[1].n - a[1].n).map(([id, r]) => {
  const f = id === 'car' ? 'p_car_sedan' : 'p_' + id.replace(' (round 1)', '');
  return { id, n: r.n, maps: Object.entries(r.maps).sort((a, b) => b[1] - a[1]).map(([m, n]) => `${m} ${n}`).join(', '), file: model(id), s: glbStats(path.join(ROOT, 'public/models', f + '.glb')) };
});
if (md) {
  console.log('| prop | copies | model | lod0 / lod1 tris | materials (near / far) | kB | maps |');
  console.log('|---|---|---|---|---|---|---|');
  for (const r of rows) console.log(`| ${r.id} | ${r.n} | \`${r.file}\` | ${r.s ? `${r.s.lod0} / ${r.s.lod1 || '-'}` : 'missing (boxes)'} | ${r.s ? `${r.s.m0} / ${r.s.m1 || '-'}` : ''} | ${r.s ? r.s.kb : ''} | ${r.maps} |`);
} else {
  for (const r of rows) console.log(`${r.id.padEnd(22)} ${String(r.n).padStart(5)}  ${(r.s ? `${r.s.lod0}/${r.s.lod1} tris, ${r.s.kb} kB, ${r.s.m0} | ${r.s.m1}` : 'no model yet').padEnd(60)}  ${r.maps}`);
  console.log('\nper map:', JSON.stringify(Object.fromEntries(Object.entries(maps).map(([m, c]) => [m, Object.values(c).reduce((a, b) => a + b, 0)]))));
}
