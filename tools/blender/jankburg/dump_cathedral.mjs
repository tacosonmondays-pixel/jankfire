// the cathedral's boxes in its own frame (x across, y up, the front at -z) -> cathedral.json next to this file,
// for make_jb_cathedral.py. run from the repo root: node tools/blender/jankburg/dump_cathedral.mjs
import fs from 'fs';
const { MAPS } = await import(process.cwd() + '/shared/map.js'); await import(process.cwd() + '/shared/royale.js');
const J = MAPS.jankburg, p = [...J.boxes.props, ...J.deco.props].find((q) => q.id === 'jb_cathedral');
const c = Math.cos(p.y), s = Math.sin(p.y), out = [];
for (const [list, kind] of [[J.boxes, 'B'], [J.deco, 'D']]) for (const b of list) {
  if (b.pv !== 'jb_cathedral' && !(b.fit && Math.abs((b.min[0] + b.max[0]) / 2 - p.a[0]) < 20 && Math.abs((b.min[2] + b.max[2]) / 2 - p.a[2]) < 26 && b.max[1] < 20)) continue;
  const pts = [];
  for (const x of [b.min[0], b.max[0]]) for (const z of [b.min[2], b.max[2]]) { const px = x - p.a[0], pz = z - p.a[2]; pts.push([px * c - pz * s, px * s + pz * c]); }
  const lx = pts.map((q) => q[0]), lz = pts.map((q) => q[1]);
  const r = (v) => Math.round(v * 1000) / 1000;
  out.push({ k: kind, mat: b.mat, keep: !!b.fit, min: [r(Math.min(...lx)), r(b.min[1]), r(Math.min(...lz))], max: [r(Math.max(...lx)), r(b.max[1]), r(Math.max(...lz))], rot: b.rot || 0 });
}
fs.writeFileSync(process.argv[2] || new URL('./cathedral.json', import.meta.url).pathname, JSON.stringify({ placement: p, boxes: out }, null, 0));
console.log(JSON.stringify(p), out.length, 'boxes', out.filter((b) => b.keep).length, 'kept', out.filter((b) => b.rot).length, 'turned');
