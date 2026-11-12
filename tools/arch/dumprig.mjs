// Dump a rig map's rails and stairs (shared/map.js rail() / rigStair(), noted in boxes.rigkit) for
// tools/blender/arch/make_rigrails.py, in world space: each rail's runs, each stair's steps and its handrails' sides,
// plus every solid box (what the model's AO is cast by).
// usage: node tools/arch/dumprig.mjs <map> [out.json]
import fs from 'fs';
import { MAPS } from '../../shared/map.js';
const [mapId, out] = process.argv.slice(2);
const m = MAPS[mapId]; if (!m || !m.boxes.rigkit) throw new Error('no rig kit on ' + mapId);
const r3 = (v) => Math.round(v * 1000) / 1000;
const A = (b, ax) => (ax ? [b.min[0], b.max[0]] : [b.min[2], b.max[2]]); // along
const C = (b, ax) => (ax ? [b.min[2], b.max[2]] : [b.min[0], b.max[0]]); // across
const rails = [], stairs = [];
for (const rec of m.boxes.rigkit) {
  const bs = m.boxes.slice(rec.b[0], rec.b[1]), ax = rec.alongX;
  if (rec.k === 'rail') {
    if (!bs.length) continue;
    const c = (C(bs[0], ax)[0] + C(bs[0], ax)[1]) / 2;
    rails.push({ ax, c: r3(c), y: r3(rec.y), runs: bs.map((b) => A(b, ax).map(r3)) });
  } else {
    const treads = bs.filter((b) => b.mat !== 'rigyellow'), tops = bs.filter((b) => b.mat === 'rigyellow');
    const [lo, hi] = C(treads[0], ax);
    const sides = rec.rails.map((s) => { const e = s > 0 ? hi : lo; return { s, e: r3(e), segs: tops.filter((b) => Math.abs((C(b, ax)[0] + C(b, ax)[1]) / 2 - e) < 0.01).map((b) => [...A(b, ax).map(r3), r3(b.min[1] - 0.98)]) }; });
    stairs.push({ ax, thin: rec.thin, ya: r3(rec.ya), yb: r3(rec.yb), mat: treads[0].mat, lo: r3(lo), hi: r3(hi), steps: treads.map((b) => [...A(b, ax).map(r3), r3(b.min[1]), r3(b.max[1])]), sides });
  }
}
const solids = m.boxes.map((b) => [b.min.map(r3), b.max.map(r3)]);
const json = JSON.stringify({ map: mapId, id: 'rigrails_' + mapId, rails, stairs, solids });
console.error(`${mapId}: ${rails.length} rails (${rails.reduce((n, r) => n + r.runs.length, 0)} runs), ${stairs.length} stairs (${stairs.reduce((n, s) => n + s.steps.length, 0)} steps)`);
if (out) fs.writeFileSync(out, json); else console.log(json);
