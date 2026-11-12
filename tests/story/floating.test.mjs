// node --test tests/story/floating.test.mjs : nothing in the slice floats (owner playtest: "floating props", worst in
// the Gut). every prop in all 80 chunks is checked by its model's own shape (public/models/story/s_<id>.glb bounds):
//   floor things (base at y 0: chairs, cones, wrecks, lumps)  ground under the middle, and under 2+ of its 4 corners
//   wall things (back flat at z 0: signs, dishes, the wall growth)  a wall, a mast or flesh right behind the back
//   fixtures (a logo, a floodlight, a handrail, the gate's clock)  touching what they're fixed to
//   line things (washing, bulbs, vein cables)  a line or a tube over them
// ground = the highest drawn surface: boxes, the shaped ground (fields), the deck's road quads, flesh blobs. a thing
// sunk into the ground (the hills' hug) is fine. and the Gut's floor has no holes into the void round the Big Stomach.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { buildChunk } from '../../shared/city/chunk.js';
import { SLICE } from '../../shared/city/slice.js';

const MODELS = new URL('../../public/models/', import.meta.url);
const chunks = []; for (let cx = -5; cx < 5; cx++) for (let cz = -4; cz < 4; cz++) chunks.push(buildChunk('slice', cx, cz));
const HIDE = 2, TER = 64;

// ---- a model's bounding box, from its .glb (every mesh's POSITION min / max through its node transforms)
const mul = (a, b) => { const o = new Array(16).fill(0); for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) for (let k = 0; k < 4; k++) o[j * 4 + i] += a[k * 4 + i] * b[j * 4 + k]; return o; };
function trs(n) {
  if (n.matrix) return n.matrix;
  const [x, y, z, w] = n.rotation || [0, 0, 0, 1], [sx, sy, sz] = n.scale || [1, 1, 1], [tx, ty, tz] = n.translation || [0, 0, 0];
  return [(1 - 2 * (y * y + z * z)) * sx, 2 * (x * y + z * w) * sx, 2 * (x * z - y * w) * sx, 0, 2 * (x * y - z * w) * sy, (1 - 2 * (x * x + z * z)) * sy, 2 * (y * z + x * w) * sy, 0, 2 * (x * z + y * w) * sz, 2 * (y * z - x * w) * sz, (1 - 2 * (x * x + y * y)) * sz, 0, tx, ty, tz, 1];
}
function glbBox(file) {
  const b = fs.readFileSync(file), len = b.readUInt32LE(12), J = JSON.parse(b.subarray(20, 20 + len).toString());
  const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
  const walk = (ni, M) => { const n = J.nodes[ni], W = mul(M, trs(n));
    if (n.mesh != null) for (const p of J.meshes[n.mesh].primitives) { const a = J.accessors[p.attributes.POSITION]; if (!a.min) continue;
      for (let c = 0; c < 8; c++) { const v = [c & 1 ? a.max[0] : a.min[0], c & 2 ? a.max[1] : a.min[1], c & 4 ? a.max[2] : a.min[2]]; for (let k = 0; k < 3; k++) { const w = W[k] * v[0] + W[4 + k] * v[1] + W[8 + k] * v[2] + W[12 + k]; lo[k] = Math.min(lo[k], w); hi[k] = Math.max(hi[k], w); } } }
    for (const c of n.children || []) walk(c, W); };
  for (const r of J.scenes[J.scene || 0].nodes) walk(r, [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]);
  return { lo, hi };
}
const BOX = {}; const boxOf = (id) => BOX[id] ||= glbBox(new URL(fs.existsSync(new URL(`story/s_${id}.glb`, MODELS)) ? `story/s_${id}.glb` : `p_${id}.glb`, MODELS));

// ---- the surfaces
const drawn = [], bodies = [], fields = [], quads = [], blobs = [], fleshy = [], tubes = [];
for (const o of chunks) {
  for (const b of o.boxes) { if (!(b[7] & HIDE)) drawn.push(b); if (!(b[7] & TER)) bodies.push(b); }
  for (const s of o.shapes) {
    if (s.kind === 'field') fields.push(s); else if (s.kind === 'quad') quads.push(s);
    else if (s.kind === 'blob' && Array.isArray(s.c)) { blobs.push(s); fleshy.push({ c: s.c, r: Array.isArray(s.r) ? Math.max(...s.r) : s.r }); }
    else if (s.kind === 'tube') for (const p of s.pts) { fleshy.push({ c: p, r: (Array.isArray(s.r) ? Math.max(...s.r) : s.r || 0.1) + 0.1 }); tubes.push(p); }
  }
}
const G = 8, bucket = (list, x0, z0, x1, z1, b, m) => { for (let i = Math.floor(x0 / G); i <= Math.floor(x1 / G); i++) for (let j = Math.floor(z0 / G); j <= Math.floor(z1 / G); j++) { const k = i * 100000 + j; if (!m.has(k)) m.set(k, []); m.get(k).push(b); } };
const gD = new Map(), gB = new Map(), gS = new Map();
for (const b of drawn) bucket(drawn, b[0], b[2], b[3], b[5], b, gD);
for (const b of bodies) bucket(bodies, b[0], b[2], b[3], b[5], b, gB);
for (const s of quads) { const xs = s.q.map((p) => p[0]), zs = s.q.map((p) => p[2]); bucket(quads, Math.min(...xs), Math.min(...zs), Math.max(...xs), Math.max(...zs), s, gS); }
for (const s of blobs) { const r = Array.isArray(s.r) ? s.r : [s.r, s.r, s.r]; bucket(blobs, s.c[0] - r[0], s.c[2] - r[2], s.c[0] + r[0], s.c[2] + r[2], s, gS); }
const at = (m, x, z) => m.get(Math.floor(x / G) * 100000 + Math.floor(z / G)) || [];
function fieldAt(f, x, z) {
  const fx = (x - f.x0) / f.cell, fz = (z - f.z0) / f.cell; if (fx < 0 || fz < 0 || fx > f.nx || fz > f.nz) return null;
  const i = Math.min(f.nx - 1, Math.floor(fx)), j = Math.min(f.nz - 1, Math.floor(fz)); if (f.ok && !f.ok[i * f.nz + j]) return null;
  const u = fx - i, v = fz - j, vz = f.nz + 1, H = f.H;
  return H[i * vz + j] * (1 - u) * (1 - v) + H[(i + 1) * vz + j] * u * (1 - v) + H[i * vz + j + 1] * (1 - u) * v + H[(i + 1) * vz + j + 1] * u * v;
}
function triY(a, b, c, x, z) {
  const d = (b[2] - c[2]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[2] - c[2]); if (Math.abs(d) < 1e-6) return null;
  const l1 = ((b[2] - c[2]) * (x - c[0]) + (c[0] - b[0]) * (z - c[2])) / d, l2 = ((c[2] - a[2]) * (x - c[0]) + (a[0] - c[0]) * (z - c[2])) / d, l3 = 1 - l1 - l2;
  return l1 < -1e-4 || l2 < -1e-4 || l3 < -1e-4 ? null : l1 * a[1] + l2 * b[1] + l3 * c[1];
}
const shapeY = (s, x, z) => { if (s.q) return triY(s.q[0], s.q[1], s.q[2], x, z) ?? triY(s.q[0], s.q[2], s.q[3], x, z); const r = Array.isArray(s.r) ? s.r : [s.r, s.r, s.r], dx = (x - s.c[0]) / r[0], dz = (z - s.c[2]) / r[2], k = 1 - dx * dx - dz * dz; return k <= 0 ? null : s.c[1] + r[1] * Math.sqrt(k); };
// the highest drawn surface at (x, z) no higher than y + up
function ground(x, z, y, up = 0.12) {
  let g = -Infinity;
  for (const b of at(gD, x, z)) if (x >= b[0] && x <= b[3] && z >= b[2] && z <= b[5] && b[4] <= y + up && b[4] > g) g = b[4];
  for (const f of fields) { const h = fieldAt(f, x, z); if (h != null && h <= y + up && h > g) g = h; }
  for (const s of at(gS, x, z)) { const h = shapeY(s, x, z); if (h != null && h <= y + up && h > g) g = h; }
  return g;
}
// base minus the surface under it (negative: sunk into it on purpose; 99: nothing at all)
function gapAt(x, z, y) { const over = ground(x, z, y + 3, 0); if (over > y + 0.12) return y - over; const g = ground(x, z, y); return g === -Infinity ? 99 : y - g; }
const near = (m, x, z, pad) => { const out = new Set(); for (const dx of [-pad, 0, pad]) for (const dz of [-pad, 0, pad]) for (const b of at(m, x + dx, z + dz)) out.add(b); return out; }; // (a padded look reaches into the next bucket)
const solid = (x, y, z, pad = 0) => [...near(gD, x, z, pad)].some((b) => x >= b[0] - pad && x <= b[3] + pad && y >= b[1] - pad && y <= b[4] + pad && z >= b[2] - pad && z <= b[5] + pad);
const inFlesh = (x, y, z, pad) => fleshy.some((f) => Math.abs(f.c[0] - x) < f.r + pad && Math.abs(f.c[2] - z) < f.r + pad && Math.hypot(f.c[0] - x, f.c[1] - y, f.c[2] - z) < f.r + pad);
const rot = (lx, lz, yaw) => [lx * Math.cos(yaw) + lz * Math.sin(yaw), -lx * Math.sin(yaw) + lz * Math.cos(yaw)];

const LINE = new Set(['laundry_a', 'laundry_b', 'stringlights', 'veincable']);
const FIXTURE = new Set(['gristlelogo', 'punchclock_big', 'floodlight', 'longrail', 'longrail_b', 'longpole', 'longpole_b']);
const props = chunks.flatMap((o) => o.props);
const kindOf = (id) => { const { lo, hi } = boxOf(id); return LINE.has(id) ? 'line' : FIXTURE.has(id) ? 'fixture' : Math.abs(hi[2]) < 0.06 && lo[2] < -0.1 ? 'wall' : 'floor'; };
function touches(id, x, y, z, yaw, s) { // the model's box (grown 15 cm) meets a body, flesh or a big prop
  const { lo, hi } = boxOf(id), c = []; for (const a of [lo[0], hi[0]]) for (const b of [lo[2], hi[2]]) c.push(rot(a * s, b * s, yaw));
  const x0 = x + Math.min(...c.map((q) => q[0])) - 0.15, x1 = x + Math.max(...c.map((q) => q[0])) + 0.15, z0 = z + Math.min(...c.map((q) => q[1])) - 0.15, z1 = z + Math.max(...c.map((q) => q[1])) + 0.15, y0 = y + lo[1] * s - 0.15, y1 = y + hi[1] * s + 0.15;
  for (let gx = Math.floor(x0 / G); gx <= Math.floor(x1 / G); gx++) for (let gz = Math.floor(z0 / G); gz <= Math.floor(z1 / G); gz++) for (const b of gB.get(gx * 100000 + gz) || []) if (b[0] < x1 && b[3] > x0 && b[1] < y1 && b[4] > y0 && b[2] < z1 && b[5] > z0) return true;
  for (const q of props) if (q[0] !== id) { const B2 = boxOf(q[0]), s2 = q[5] || 1, R2 = Math.max(...[B2.lo[0], B2.hi[0], B2.lo[2], B2.hi[2]].map(Math.abs)) * s2; if (R2 > 2 && Math.abs(q[1] - x) < R2 + 0.15 && Math.abs(q[3] - z) < R2 + 0.15 && q[2] + B2.lo[1] * s2 < y1 && q[2] + B2.hi[1] * s2 > y0) return true; }
  return fleshy.some((f) => f.c[0] > x0 - f.r && f.c[0] < x1 + f.r && f.c[2] > z0 - f.r && f.c[2] < z1 + f.r && f.c[1] > y0 - f.r && f.c[1] < y1 + f.r);
}
function floats(p) {
  const [id, x, y, z, yaw, s0] = p, s = s0 || 1, { lo, hi } = boxOf(id), k = kindOf(id);
  if (k === 'line') { // both ends tied to something: a wall, a post, flesh, a line's tube (washing hangs off line())
    const tied = (lx) => { const [dx, dz] = rot(lx * s, 0, yaw), ex = x + dx, ez = z + dz;
      return tubes.some((t) => Math.hypot(t[0] - ex, t[2] - ez) < 2.5 && Math.abs(t[1] - y) < 1.5) || solid(ex, y, ez, 0.6) || inFlesh(ex, y, ez, 0.6) || [...near(gB, ex, ez, 0.6)].some((b) => ex >= b[0] - 0.6 && ex <= b[3] + 0.6 && ez >= b[2] - 0.6 && ez <= b[5] + 0.6 && y >= b[1] - 0.6 && y <= b[4] + 0.6); };
    const a = tied(lo[0]), b = tied(hi[0]);
    return a && b ? null : `${a || b ? 'one end' : 'both ends'} tied to nothing`;
  }
  if (k === 'fixture') return touches(id, x, y, z, yaw, s) ? null : 'touches nothing';
  if (k === 'wall') {
    for (const fx of [0, -0.35, 0.35]) for (const fy of [0.5, 0.25, 0.75]) { const lx = (lo[0] + (hi[0] - lo[0]) * (0.5 + fx)) * s, ly = (lo[1] + (hi[1] - lo[1]) * fy) * s;
      for (const d of [0.05, 0.2, 0.4]) { const [dx, dz] = rot(lx, d, yaw); if (solid(x + dx, y + ly, z + dz) || inFlesh(x + dx, y + ly, z + dz, 0.1)) return null; } }
    return 'no wall behind';
  }
  const base = y + lo[1] * s, pts = [[0, 0]]; for (const [a, b] of [[lo[0], lo[2]], [hi[0], lo[2]], [hi[0], hi[2]], [lo[0], hi[2]]]) pts.push([a * 0.7 * s, b * 0.7 * s]);
  const gaps = pts.map(([lx, lz]) => { const [dx, dz] = rot(lx, lz, yaw), g = gapAt(x + dx, z + dz, base); return g > 0.05 && (solid(x + dx, base - 0.02, z + dz, 0.02) || inFlesh(x + dx, base, z + dz, 0.15)) ? 0 : g; });
  if (gaps[0] > 0.05 && !inFlesh(x, base + (hi[1] - lo[1]) * s * 0.3, z, 0.1)) return `${gaps[0] >= 99 ? 'nothing' : gaps[0].toFixed(2) + ' m'} under it`;
  if (gaps.slice(1).filter((g) => g > 0.3).length >= 3) return 'over a drop';
  return null;
}

test('no prop in the slice floats', () => {
  const bad = [];
  for (const p of props) {
    const why = floats(p);
    if (!why) continue;
    if (props.some((q) => q !== p && q[0] === p[0] && Math.hypot(q[1] - p[1], q[3] - p[3]) < 1.2 && q[2] < p[2] - 0.3 && q[2] > p[2] - 3)) continue; // (a pile: the car wrecks stacked at the camp)
    bad.push(`${p[0]} at ${p.slice(1, 4).map((v) => v.toFixed(1))}: ${why}`);
  }
  assert.ok(props.length > 15000, 'the slice lost its props: ' + props.length);
  assert.deepEqual(bad, [], `${bad.length} floating:\n${bad.slice(0, 40).join('\n')}`);
});

test("the Gut's floor has no holes round the Big Stomach", () => {
  const S = SLICE.stomach, holes = [];
  for (let a = 0; a < 360; a += 1) for (let d = S.r - 8; d <= S.r + 12; d += 0.5) {
    const x = S.x + Math.cos(a * Math.PI / 180) * d, z = S.z + Math.sin(a * Math.PI / 180) * d;
    if (!(ground(x, z, 60, 0) > S.floor - 1)) holes.push(`${x.toFixed(1)},${z.toFixed(1)}`);
  }
  assert.deepEqual(holes.slice(0, 20), [], `${holes.length} spots with no floor`);
});

test('nowhere in the slice can you see (or fall) through the floor into the void', () => {
  const holes = new Map();
  for (let x = SLICE.x0 + 0.5; x < SLICE.x1; x += 1) for (let z = SLICE.z0 + 0.5; z < SLICE.z1; z += 1) if (!(ground(x, z, 500, 0) > -3.9)) { const k = Math.floor(x / 16) * 16 + ',' + Math.floor(z / 16) * 16; holes.set(k, (holes.get(k) || 0) + 1); }
  assert.deepEqual([...holes], [], 'm² with nothing under them, by 16 m tile');
});
