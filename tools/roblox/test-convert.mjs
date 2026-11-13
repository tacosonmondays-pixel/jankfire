// the converter keeps the map exactly: every box of shared/map.js is a Part (x3 studs, same place, size, turn,
// material), pads keep their launch, spawns land on their spots, every Blender model placement has a marker and a
// Roblox-ready file. run: node tools/roblox/test-convert.mjs [map=rooftop]
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { convert, S } from './convert.mjs';
const HERE = path.dirname(fileURLToPath(import.meta.url)), ROOT = path.join(HERE, '..', '..');
const mapId = process.argv[2] || 'rooftop';
let fails = 0, passes = 0;
const check = (ok, what) => { if (ok) passes++; else { fails++; console.log('FAIL:', what); } };
const near = (a, b, t = 0.002) => Math.abs(a - b) <= t;

const r = convert(mapId), def = r.def, boxes = [...def.boxes, ...def.deco];
// walk the boxes in order: one part each, or several equal pieces (the >2048-stud ones) that add back up to it
let k = 0, bad = 0, pieces = 0;
for (const b of boxes) {
  const size = [0, 1, 2].map((i) => (b.max[i] - b.min[i]) * S), c = [0, 1, 2].map((i) => ((b.min[i] + b.max[i]) / 2) * S);
  const n = size.reduce((m, x) => m * Math.max(1, Math.ceil(x / 2000)), 1);
  const ps = r.parts.slice(k, k + n); k += n; if (n > 1) pieces += n;
  const vol = ps.reduce((m, p) => m + p.size[0] * p.size[1] * p.size[2], 0), mid = [0, 1, 2].map((i) => ps.reduce((m, p) => m + p.pos[i], 0) / n);
  const ok = ps.length === n && ps.every((p) => p.mat === b.mat && near(p.yaw, b.rot || 0, 1e-3) && Math.max(...p.size) <= 2048) &&
    (n === 1 || near(vol, size[0] * size[1] * size[2], vol * 1e-3)) && mid.every((x, i) => near(x, c[i], 0.01)) && (n > 1 || ps[0].size.every((x, i) => near(x, size[i])));
  if (!ok) bad++;
}
check(k === r.parts.length, `one part (or pieces) per box: ${boxes.length} boxes -> ${r.parts.length} parts`);
check(bad === 0, `every part matches its box (x${S}, place, size, turn, material): ${bad} off`);
console.log(`  ${boxes.length} boxes, ${pieces} pieces from long boxes split under Roblox's 2048-stud cap`);
// the whole map's bounds, x3
const bb = (list, f) => { const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity]; for (const x of list) { const [a, b] = f(x); for (let i = 0; i < 3; i++) { lo[i] = Math.min(lo[i], a[i]); hi[i] = Math.max(hi[i], b[i]); } } return [lo, hi]; };
const [jl, jh] = bb(def.boxes, (b) => [b.min, b.max]);
const [rl, rh] = bb(r.parts.filter((p) => p.kind === 'solid' || p.kind === 'pad'), (p) => [p.pos.map((x, i) => x - p.size[i] / 2), p.pos.map((x, i) => x + p.size[i] / 2)]);
check([0, 1, 2].every((i) => near(rl[i], jl[i] * S, 0.01) && near(rh[i], jh[i] * S, 0.01)), `playable bounds x3: ${jl.map((x) => x * S)} .. ${jh.map((x) => x * S)}`);
// pads, spawns
const pads = def.boxes.filter((b) => b.pad), rp = r.parts.filter((p) => p.kind === 'pad');
check(pads.length === rp.length && pads.every((b, i) => b.pad.every((v, j) => near(rp[i].attrs.Pad.Vector3[j], v * S))), `${pads.length} jump pads keep their launch (x${S})`);
check(r.spawns.length === def.spawns.length && def.spawns.every((s, i) => s.every((v, j) => near(r.spawns[i][j], v * S))), `${def.spawns.length} spawns`);
// solid boxes collide, deco doesn't (built into the model json)
const flat = (m) => (m.Children || []).flatMap((c) => [c, ...flat(c)]);
const all = flat(r.model), F = (n) => r.model.Children.find((c) => c.Name === n).Children;
check(F('Solid').every((p) => p.Properties.CanCollide && p.Properties.CanQuery) && F('Deco').every((p) => !p.Properties.CanCollide && !p.Properties.CanQuery) && F('City').every((p) => !p.Properties.CanCollide), 'solid boxes collide, look-only ones don\'t');
check(all.filter((c) => c.ClassName === 'SpawnLocation').length === def.spawns.length, 'SpawnLocations');
// Blender models: a marker per placement, a Roblox-ready file per model
const nPl = (def.boxes.props || []).length + (def.deco.props || []).length + (def.boxes.arch || []).length;
check(r.markers.length === nPl, `a marker for every Blender model placement (${r.markers.length} of ${nPl})`);
const dir = path.join(ROOT, 'roblox', 'assets', mapId), files = [...new Set(r.markers.map((m) => m.model))];
const missing = files.filter((f) => !fs.existsSync(path.join(dir, f + '.glb')));
check(missing.length === 0, `every model has its Roblox file in roblox/assets/${mapId}/ (missing: ${missing.join(', ') || 'none'})`);
const rep = fs.existsSync(path.join(dir, 'export_report.json')) ? JSON.parse(fs.readFileSync(path.join(dir, 'export_report.json'), 'utf8')) : {};
const over = Object.entries(rep).flatMap(([f, x]) => x.pieces.filter((p) => p.tris > 20000).map((p) => f + '/' + p.name));
check(over.length === 0, 'every mesh piece under Roblox\'s 20k-triangle cap');
// a prop's marker is its boxes' extent where the model is fitted onto them (acunit: one box, fitted exactly)
const ac = (def.boxes.props || []).find((p) => p.id === 'acunit');
if (ac) { const m = r.markers.find((x) => x.id === 'acunit'); check(m && [0, 1, 2].every((i) => near(m.size[i], (ac.hi[i] - ac.lo[i]) * S, 0.01)), 'a fitted prop fills its boxes'); }
console.log(`${passes} passed, ${fails} failed`);
process.exit(fails ? 1 : 0);
