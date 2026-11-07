// node tools/city/gta_index.mjs [--check] [-v]
// Checks the slice's road net and pavements against the real collision and writes what's drivable / walkable:
//   shared/city/slice_gta.js   { roads, walks, park }  (chunks clip it: roads.js gtaInto)
//   shared/city/marks_slice.js { marks }               (every chunk mark, for marksNear without building geometry)
// A road is driven with a car-sized box (2.2 m wide, 2.4 long, from 0.45 m over the road to 2 m): anything in that
// box, a step over 0.45 m, or no ground at all blocks it. The clear runs (10 m or more) are kept, heights fitted to
// the ground. Kerbside parking: every 8 m each side, where a parked car fits, isn't on another road or a pavement.
// Pavements: a walker (0.7 m) with the same rules, runs of 6 m or more. --check: fail if the files are stale.
import fs from 'node:fs';
import { buildChunk, packChunk, chunkBoxes } from '../../shared/city/chunk.js';
import { ChunkWorld } from '../../shared/city/world.js';
import { CHUNK, CITIES, hash2 } from '../../shared/city/plan.js';
import { RAW, NODRIVE } from '../../shared/city/roads.js';
import '../../shared/city/gens.js';

const args = process.argv.slice(2), V = args.includes('-v');
const C = CITIES.slice, [X0, Z0, X1, Z1] = [-320, -256, 320, 256];
const W = new ChunkWorld([]), marks = [];
for (let cx = Math.floor(X0 / CHUNK); cx < Math.ceil(X1 / CHUNK); cx++) for (let cz = Math.floor(Z0 / CHUNK); cz < Math.ceil(Z1 / CHUNK); cz++) {
  const p = packChunk(buildChunk('slice', cx, cz));
  W.set(cx + ':' + cz, chunkBoxes(p));
  for (const m of p.marks) if (!(m.id === 'park' && m.road)) marks.push(m); // (road parking is re-derived below)
}
W.sync();
void C;
const q = [];
// the ground under (x, z) near height y: the highest box top within [y - 1.5, y + 0.6]
function ground(x, z, y) {
  let best = null;
  for (const b of W.query(x - 0.05, z - 0.05, x + 0.05, z + 0.05, q)) {
    if (x < b.min[0] || x > b.max[0] || z < b.min[2] || z > b.max[2]) continue;
    const t = b.max[1];
    if (t >= y - 1.5 && t <= y + 0.6 && (best === null || t > best)) best = t;
  }
  return best;
}
// is a box of half-size (hx, hz) at (x, z) clear from g + lo to g + hi?
function clear(x, z, g, hx, hz, lo = 0.45, hi = 2) {
  for (const b of W.query(x - hx, z - hz, x + hx, z + hz, q)) {
    if (b.max[0] <= x - hx || b.min[0] >= x + hx || b.max[2] <= z - hz || b.min[2] >= z + hz) continue;
    if (b.max[1] > g + lo && b.min[1] < g + hi) return false;
  }
  return true;
}
const aabb = (dx, dz, along, across) => { const L = Math.hypot(dx, dz) || 1, c = Math.abs(dx / L), s = Math.abs(dz / L); return [c * along + s * across, s * along + c * across]; };

// drive / walk a polyline at 1 m steps: [{ p: [x, y, z], ok }]
function sweep(pts, half, len, step = 0.45, no = []) {
  const out = [];
  let prev = null;
  for (let i = 0; i + 1 < pts.length; i++) {
    const a = pts[i], b = pts[i + 1], L = Math.hypot(b[0] - a[0], b[2] - a[2]), n = Math.max(1, Math.round(L));
    const [hx, hz] = aabb(b[0] - a[0], b[2] - a[2], len, half);
    for (let k = i ? 1 : 0; k <= n; k++) {
      const t = k / n, x = a[0] + (b[0] - a[0]) * t, z = a[2] + (b[2] - a[2]) * t, yh = prev ?? a[1] + (b[1] - a[1]) * t;
      const g = ground(x, z, yh);
      const ok = g !== null && (prev === null || Math.abs(g - prev) <= step) && clear(x, z, g, hx, hz) && !no.some((q) => x > q[0] && x < q[2] && z > q[1] && z < q[3]);
      out.push({ p: [x, g ?? yh, z], ok });
      prev = ok ? g : null;
    }
  }
  return out;
}
// clear runs of at least min m, thinned to a point every ~6 m (always keeping the ends)
function runs(samples, min) {
  const out = [];
  let cur = [];
  const flush = () => { if (cur.length > min) out.push(cur.filter((_, i) => i % 6 === 0 || i === cur.length - 1).map((s) => s.p.map((v) => +v.toFixed(2)))); cur = []; };
  for (const s of samples) { if (s.ok) cur.push(s); else flush(); }
  flush();
  return out;
}
const { roads: rawRoads, walks: rawWalks } = RAW();
const roads = [], walks = [], park = [], report = [];
for (const r of rawRoads) {
  const sm = sweep(r.pts, 1.1, 1.2, 0.45, NODRIVE), rs = runs(sm, 10), ok = sm.filter((s) => s.ok).length;
  rs.forEach((pts, i) => roads.push({ id: rs.length > 1 ? r.id + '#' + (i + 1) : r.id, w: r.w, dir: r.dir, pts }));
  const spans = []; let st = null;
  sm.forEach((x, i) => { if (!x.ok && !st) st = x; if ((x.ok || i === sm.length - 1) && st) { spans.push([st.p, sm[Math.max(0, i - 1)].p]); st = null; } });
  report.push([r.id, Math.round(100 * ok / sm.length), rs.length, spans]);
}
for (const r of rawWalks) {
  const sm = sweep(r.pts, 0.35, 0.35), rs = runs(sm, 6);
  rs.forEach((pts, i) => walks.push({ id: rs.length > 1 ? r.id + '#' + (i + 1) : r.id, w: r.w, pts }));
}
// kerbside parking
const near = (list, x, z, d, skip) => list.some((l) => l !== skip && l.pts.some((p, i) => { const b = l.pts[i + 1]; if (!b) return false; const dx = b[0] - p[0], dz = b[2] - p[2], L2 = dx * dx + dz * dz || 1, t = Math.max(0, Math.min(1, ((x - p[0]) * dx + (z - p[2]) * dz) / L2)); return Math.hypot(x - p[0] - dx * t, z - p[2] - dz * t) < d + (l.w || 1) / 2; }));
for (const r of roads) for (let i = 0; i + 1 < r.pts.length; i++) {
  const a = r.pts[i], b = r.pts[i + 1], dx = b[0] - a[0], dz = b[2] - a[2], L = Math.hypot(dx, dz) || 1, nx = -dz / L, nz = dx / L;
  for (let s = 4; s < L; s += 8) for (const side of [-1, 1]) {
    const off = r.w / 2 + 1.3, x = a[0] + dx * s / L + nx * off * side, z = a[2] + dz * s / L + nz * off * side, y = a[1] + (b[1] - a[1]) * s / L;
    if (((hash2(Math.round(x), Math.round(z), 0x9a4c) % 100)) > 55) continue; // not every spot: some gaps
    const g = ground(x, z, y);
    if (g === null || Math.abs(g - y) > 0.3) continue;
    const [hx, hz] = aabb(dx, dz, 2.4, 1.1);
    if (!clear(x, z, g, hx, hz, 0.3)) continue;
    if (near(roads, x, z, 1.6, r) || near(walks, x, z, 0.9)) continue;
    park.push({ p: [+x.toFixed(2), +g.toFixed(2), +z.toFixed(2)], yaw: +Math.atan2(-dx, -dz).toFixed(3), road: r.id });
  }
}
const km = (l) => l.reduce((a, r) => a + r.pts.reduce((s, p, i) => s + (i ? Math.hypot(p[0] - r.pts[i - 1][0], p[2] - r.pts[i - 1][2]) : 0), 0), 0) / 1000;
// which pieces connect (touch or cross at the same height): the drivable components, biggest first
const segD = (x, z, l) => { let d = Infinity; for (let i = 0; i + 1 < l.pts.length; i++) { const p = l.pts[i], b = l.pts[i + 1], dx = b[0] - p[0], dz = b[2] - p[2], L2 = dx * dx + dz * dz || 1, t = Math.max(0, Math.min(1, ((x - p[0]) * dx + (z - p[2]) * dz) / L2)); if (Math.abs(p[1] + (b[1] - p[1]) * t - (p[1] + b[1]) / 2) < 99) d = Math.min(d, Math.hypot(x - p[0] - dx * t, z - p[2] - dz * t) + (Math.abs((p[1] + (b[1] - p[1]) * t)) > 9e9 ? 1 : 0)); } return d; };
const yAt = (l, x, z) => { let best = null, bd = Infinity; for (const p of l.pts) { const d = Math.hypot(p[0] - x, p[2] - z); if (d < bd) { bd = d; best = p[1]; } } return best; };
const link = roads.map(() => []);
for (let i = 0; i < roads.length; i++) for (let j = i + 1; j < roads.length; j++) {
  const a = roads[i], b = roads[j];
  if (a.pts.some((p) => segD(p[0], p[2], b) < (a.w + b.w) / 2 + 0.5 && Math.abs(yAt(b, p[0], p[2]) - p[1]) < 1) || b.pts.some((p) => segD(p[0], p[2], a) < (a.w + b.w) / 2 + 0.5 && Math.abs(yAt(a, p[0], p[2]) - p[1]) < 1)) { link[i].push(j); link[j].push(i); }
}
const comp = new Array(roads.length).fill(-1), comps = [];
for (let i = 0; i < roads.length; i++) if (comp[i] < 0) { const st = [i], c = []; comp[i] = comps.length; while (st.length) { const k = st.pop(); c.push(k); for (const n of link[k]) if (comp[n] < 0) { comp[n] = comps.length; st.push(n); } } comps.push(c); }
comps.sort((a, b) => km(b.map((i) => roads[i])) - km(a.map((i) => roads[i])));
for (const r of roads) r.net = comps.findIndex((c) => c.includes(roads.indexOf(r))); // which connected net it's on (0 = the biggest)
if (V) comps.slice(0, 8).forEach((c, k) => console.log(`  net ${k}: ${km(c.map((i) => roads[i])).toFixed(2)} km · ${c.map((i) => roads[i].id).join(' ')}`));
// every mark (with the new parking) for marksNear
const allMarks = [...marks, ...park.map((k) => ({ id: 'park', ...k }))].map((m) => JSON.parse(JSON.stringify(m, (k, v) => (typeof v === 'number' ? +v.toFixed(2) : v))));
const gta = '// generated by tools/city/gta_index.mjs: the slice\'s checked road net, pavements and kerbside parking. don\'t edit\nexport default ' + JSON.stringify({ roads, walks, park }) + ';\n';
const mk = '// generated by tools/city/gta_index.mjs: every mark in the slice (marks.js marksNear). don\'t edit\nexport default ' + JSON.stringify({ marks: allMarks }) + ';\n';
const F1 = new URL('../../shared/city/slice_gta.js', import.meta.url), F2 = new URL('../../shared/city/marks_slice.js', import.meta.url);
console.log(`roads ${roads.length} pieces (${km(roads).toFixed(2)} km) · walks ${walks.length} (${km(walks).toFixed(2)} km) · parking ${park.length} · marks ${allMarks.length} (${(mk.length / 1024).toFixed(0)} KB)`);
if (V) for (const [id, pct, n, spans] of report) console.log(`  ${id.padEnd(18)} ${String(pct).padStart(3)}% clear, ${n} piece${n === 1 ? '' : 's'}` + (args.includes('-vv') ? '  blocked: ' + spans.map(([a, b]) => `${a[0].toFixed(0)},${a[2].toFixed(0)}..${b[0].toFixed(0)},${b[2].toFixed(0)}`).join(' ') : ''));
if (args.includes('--check')) {
  const stale = [[F1, gta], [F2, mk]].filter(([f, s]) => !fs.existsSync(f) || fs.readFileSync(f, 'utf8') !== s);
  if (stale.length) { console.log('STALE: run node tools/city/gta_index.mjs (' + stale.map(([f]) => f.pathname.split('/').pop()).join(', ') + ')'); process.exit(1); }
  console.log('up to date'); process.exit(0);
}
fs.writeFileSync(F1, gta); fs.writeFileSync(F2, mk);
