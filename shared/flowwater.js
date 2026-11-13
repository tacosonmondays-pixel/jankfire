// Flowing water, the plain-data half (public/js/flowwater.js draws it): which model parts are water, where the streams
// land, the jets a box fountain gets, and the splash particles' ring buffer. no three.js here, so node tests can poke it.
// look only: nothing in here touches collision or gameplay.

// a part (or material) named *_water is a stream (jets, spouts, waterfalls), *_pool still water (basins, ponds).
// Blender keeps names unique with .001: that tail doesn't count
export function waterTag(name) {
  const s = String(name || '').toLowerCase().replace(/\.\d+$/, '');
  if (/_pool(_|$)/.test(s)) return 'pool';
  if (/_water(_|$)/.test(s)) return 'stream';
  return null;
}

// particles per preset (Potato, Crusty, Mid, Too HD): Potato gets none
export const PARTICLE_CAP = [0, 300, 450, 800];
export const capFor = (q) => PARTICLE_CAP[Math.max(0, Math.min(3, q | 0))] ?? 240;

// a jet: a parabola from p0 to p1 bowing up by lift (m), n segments. [[x, y, z]...]
export function jetPath(p0, p1, lift, n = 12) {
  const out = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n;
    out.push([p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t + 4 * lift * t * (1 - t), p0[2] + (p1[2] - p0[2]) * t]);
  }
  return out;
}

// where streams hit the water: stream vertices low enough (near the pool's surface, or the stream's own bottom when
// there's no pool) bunched into spots. pos = flat [x, y, z, ...]. -> [{ x, y, z, w, s }] (w = how much splash, s = how big its
// drops are: a drinking fountain's trickle gets a dribble, the Smiling Fountain's jet a crown)
export function landSpots(pos, poolTop = null, cell = 1.2) {
  let lo = Infinity, hi = -Infinity;
  for (let i = 1; i < pos.length; i += 3) { lo = Math.min(lo, pos[i]); hi = Math.max(hi, pos[i]); }
  if (!Number.isFinite(lo)) return [];
  const pool = poolTop !== null && Number.isFinite(poolTop);
  const y0 = pool ? poolTop : lo, cut = pool ? poolTop + 0.35 : lo + Math.min(0.35, (hi - lo) * 0.2); // (no pool: just the stream's bottom end)
  const bins = new Map();
  for (let i = 0; i < pos.length; i += 3) {
    if (pos[i + 1] > cut) continue;
    const k = Math.round(pos[i] / cell) + ',' + Math.round(pos[i + 2] / cell);
    const b = bins.get(k) || { x: 0, z: 0, n: 0, x0: 1e9, x1: -1e9, z0: 1e9, z1: -1e9 };
    b.x += pos[i]; b.z += pos[i + 2]; b.n++;
    b.x0 = Math.min(b.x0, pos[i]); b.x1 = Math.max(b.x1, pos[i]); b.z0 = Math.min(b.z0, pos[i + 2]); b.z1 = Math.max(b.z1, pos[i + 2]);
    bins.set(k, b);
  }
  // neighbouring cells that split one splash: merged
  const spots = [...bins.values()].map((b) => ({ x: b.x / b.n, z: b.z / b.n, n: b.n, r: Math.max(b.x1 - b.x0, b.z1 - b.z0) / 2 }));
  for (let i = 0; i < spots.length; i++) for (let j = spots.length - 1; j > i; j--) {
    const a = spots[i], b = spots[j];
    if (Math.hypot(a.x - b.x, a.z - b.z) > cell) continue;
    const n = a.n + b.n; a.x = (a.x * a.n + b.x * b.n) / n; a.z = (a.z * a.n + b.z * b.n) / n; a.r = Math.max(a.r, b.r); a.n = n; spots.splice(j, 1);
  }
  return spots.map((s) => ({ x: s.x, y: y0, z: s.z, w: Math.max(0.3, Math.min(1.5, s.r / 0.35)), s: Math.max(0.06, Math.min(1.5, s.r / 0.3)) }));
}

// box fountains: a flat pool of water with a narrow column standing in it (the Bazaar's plazas, the rooftop garden)
// get jets off the column's top, arcing out into the pool. boxes = [{ min, max, mat }] (map boxes + deco).
// -> [{ from: [x, y, z], to: [x, y, z], lift, r }]
const POOLS = new Set(['water', 'poolwater']);
export function boxFountains(boxes) {
  const out = [];
  const list = boxes.filter((b) => b && Array.isArray(b.min) && Array.isArray(b.max));
  for (const w of list) {
    if (!POOLS.has(w.mat)) continue;
    const sx = w.max[0] - w.min[0], sz = w.max[2] - w.min[2], sy = w.max[1] - w.min[1];
    if (Math.min(sx, sz) < 1.5 || sx * sz > 60 || sy > 1.2) continue; // fountain-sized, flat
    const top = w.max[1];
    // narrow boxes standing in it, rising well clear of the water
    const col = list.filter((b) => b !== w && !POOLS.has(b.mat) && b.max[1] > top + 0.8 && b.min[1] < top + 2.6
      && Math.max(b.max[0] - b.min[0], b.max[2] - b.min[2]) <= 1.3
      && (b.min[0] + b.max[0]) / 2 > w.min[0] && (b.min[0] + b.max[0]) / 2 < w.max[0] && (b.min[2] + b.max[2]) / 2 > w.min[2] && (b.min[2] + b.max[2]) / 2 < w.max[2]);
    if (!col.length) continue;
    const cx = col.reduce((a, b) => a + (b.min[0] + b.max[0]) / 2, 0) / col.length, cz = col.reduce((a, b) => a + (b.min[2] + b.max[2]) / 2, 0) / col.length;
    // only boxes over the column's own footing (a cap on it, not a lamp post next to it)
    const stack = col.filter((b) => Math.abs((b.min[0] + b.max[0]) / 2 - cx) < 0.3 && Math.abs((b.min[2] + b.max[2]) / 2 - cz) < 0.3);
    if (!stack.length) continue;
    const ct = Math.max(...stack.map((b) => b.max[1])), hw = Math.max(...stack.map((b) => Math.max(b.max[0] - b.min[0], b.max[2] - b.min[2]))) / 2;
    if (out.some((f) => Math.hypot(f.from[0] - cx, f.from[2] - cz) < 1)) continue; // (a pool split in several boxes: one fountain)
    // four arcs out to the pool, as far as the pool goes (a ring of them round the column)
    const reach = Math.max(hw + 0.5, Math.min(cx - w.min[0], w.max[0] - cx, cz - w.min[2], w.max[2] - cz) - 0.35);
    for (let k = 0; k < 4; k++) {
      const a = k * Math.PI / 2 + Math.PI / 4, dx = Math.cos(a), dz = Math.sin(a);
      out.push({ from: [cx + dx * (hw * 0.7), ct + 0.06, cz + dz * (hw * 0.7)], to: [cx + dx * reach, top, cz + dz * reach], lift: 0.35 + 0.12 * (ct - top), r: [0.07, 0.11] });
    }
  }
  return out;
}

// the splash particles' ring buffer: a fixed number of slots, new ones write over the oldest. what each slot holds lives
// in the arrays (start position, velocity, birth time / life / kind), so the GPU flies them and the CPU only writes spawns
export class DropRing {
  constructor(cap) {
    this.cap = Math.max(0, cap | 0);
    this.p = new Float32Array(this.cap * 3); this.v = new Float32Array(this.cap * 3); this.t = new Float32Array(this.cap * 3).fill(-1e9);
    this.head = 0; this.spawned = 0; this.dirty = false;
  }
  spawn(x, y, z, vx, vy, vz, now, life, kind, size = 1) {
    if (!this.cap) return -1;
    const i = this.head;
    this.p[i * 3] = x; this.p[i * 3 + 1] = y; this.p[i * 3 + 2] = z;
    this.v[i * 3] = vx; this.v[i * 3 + 1] = vy; this.v[i * 3 + 2] = vz;
    this.t[i * 3] = now; this.t[i * 3 + 1] = life; this.t[i * 3 + 2] = kind * 10 + Math.max(0.01, Math.min(9.99, size)); // (kind and size in one float: the shader splits them)
    this.head = (i + 1) % this.cap; this.spawned++; this.dirty = true;
    return i;
  }
  live(now) { let n = 0; for (let i = 0; i < this.cap; i++) { const a = now - this.t[i * 3]; if (a >= 0 && a <= this.t[i * 3 + 1]) n++; } return n; }
}
