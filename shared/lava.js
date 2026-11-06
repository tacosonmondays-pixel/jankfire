// Floor Is Lava (and Duck Rain targeting): which surfaces of a map are its ground floor, which are safe,
// and where people can spawn. Worked out from the boxes alone, so the server and the client agree and new maps just work.
import { raycast, query, playerOverlap, PH } from './physics.js';

// lava: damage per touch, seconds it keeps burning, min seconds between touches, how hard it bounces you
export const LAVA = { dmg: 20, burn: 1.4, burnDmg: 4, every: 0.4, hop: 11.5 };

const cache = new WeakMap();
const down = [0, -1, 0];
const near = [];

// exposed tops: every box top you could stand on (nothing on top of it within a body height), sampled on a grid
export function surfaces(map) {
  let s = cache.get(map);
  if (s) return s;
  const boxes = map.boxes, tops = [];
  let total = 0;
  for (const b of boxes) {
    if (b.pad) continue; // jump pads launch you, they're never floor
    const sx = b.max[0] - b.min[0], sz = b.max[2] - b.min[2], top = b.max[1];
    const nx = Math.max(1, Math.min(10, Math.ceil(sx / 2.5))), nz = Math.max(1, Math.min(10, Math.ceil(sz / 2.5)));
    const cell = (sx * sz) / (nx * nz);
    let area = 0;
    for (let i = 0; i < nx; i++) for (let j = 0; j < nz; j++) {
      const h = raycast([b.min[0] + ((i + 0.5) * sx) / nx, top + 2.2, b.min[2] + ((j + 0.5) * sz) / nz], down, 2.25, boxes);
      if (h && Math.abs(h.point[1] - top) < 0.02) area += cell;
    }
    if (area > 0) { tops.push({ b, top, area }); total += area; }
  }
  // the ground floor = the lowest height that holds at least half as much floor as the biggest one
  // (so a huge flat roof or a sunken tunnel can't win), plus anything you'd just walk up onto (curbs, sidewalks)
  const bins = new Map();
  for (const t of tops) { const k = Math.round(t.top * 10); bins.set(k, (bins.get(k) || 0) + t.area); }
  const maxA = Math.max(0, ...bins.values());
  const baseK = [...bins.keys()].sort((a, b) => a - b).find((k) => bins.get(k) >= maxA * 0.5);
  const base = (baseK ?? 0) / 10, lavaTop = base + 0.5;
  const lava = new Set();
  let lavaA = 0, floorA = 0, safeA = 0, maxTop = -1e9;
  for (const b of boxes) { if (!b.pad && b.max[1] <= lavaTop) lava.add(b); maxTop = Math.max(maxTop, b.max[1]); }
  for (const t of tops) {
    if (lava.has(t.b)) { lavaA += t.area; if (t.top >= base - 0.05) floorA += t.area; } else safeA += t.area;
  }
  s = { base, lavaTop, lava, tops, total, maxTop, spawns: null, spots: null };
  s.spots = safeSpots(map, s);
  s.spawns = pickSpawns(map, s.spots);
  // a real floor (not just one of many rooftops), enough safe stuff to stand on and places to spawn
  s.ok = total > 0 && floorA / total >= 0.2 && safeA >= 100 && s.spawns.length >= 4;
  cache.set(map, s);
  return s;
}
export const lavaOk = (map) => !!map && surfaces(map).ok;

// points on safe surfaces where a whole player fits: supported under every corner, room to stand, not silly high
function safeSpots(map, s) {
  const boxes = map.boxes, out = [], hw = PH.halfW;
  for (const t of s.tops) {
    if (s.lava.has(t.b) || t.top > s.base + 30) continue;
    const b = t.b, x0 = b.min[0] + hw, x1 = b.max[0] - hw, z0 = b.min[2] + hw, z1 = b.max[2] - hw;
    if (x1 < x0 || z1 < z0) continue;
    const nx = Math.max(1, Math.min(12, Math.ceil((x1 - x0) / 1.5))), nz = Math.max(1, Math.min(12, Math.ceil((z1 - z0) / 1.5)));
    const c = hw - 0.05; // corners just inside the body, so a rail or wall touching the edge doesn't count
    for (let i = 0; i < nx; i++) for (let j = 0; j < nz; j++) {
      const x = x0 + ((x1 - x0) * (i + 0.5)) / nx, z = z0 + ((z1 - z0) * (j + 0.5)) / nz;
      const y = t.top;
      let ok = true;
      for (const [dx, dz] of [[0, 0], [-c, -c], [c, -c], [-c, c], [c, c]]) {
        const h = raycast([x + dx, y + 0.5, z + dz], down, 0.6, boxes);
        if (!h || Math.abs(h.point[1] - y) > 0.05 || s.lava.has(h.box)) { ok = false; break; }
      }
      if (ok && !playerOverlap([x, y + 0.02, z], boxes) && !playerOverlap([x, y + 0.6, z], boxes)) out.push([x, y + 0.1, z]);
    }
  }
  return out;
}

// the map's own spawns, each moved to the nearest safe spot (so they stay spread out like the map intended)
function pickSpawns(map, spots) {
  const used = new Set(), out = [];
  const crowded = (c) => out.some((o) => Math.hypot(c[0] - o[0], c[1] - o[1], c[2] - o[2]) < 4);
  for (const sp of map.spawns || []) {
    let best = -1, bd = 40;
    spots.forEach((c, i) => {
      if (used.has(i) || crowded(c)) return;
      const d = Math.hypot(c[0] - sp[0], (c[1] - sp[1]) * 0.8, c[2] - sp[2]);
      if (d < bd) { bd = d; best = i; }
    });
    if (best >= 0) { used.add(best); out.push(spots[best]); }
  }
  // not enough near the old spawns: spread the rest out over every safe spot (farthest first)
  while (out.length < 6 && used.size < spots.length) {
    let best = -1, bd = -1;
    spots.forEach((c, i) => {
      if (used.has(i)) return;
      let d = 1e9;
      for (const o of out) d = Math.min(d, Math.hypot(c[0] - o[0], c[1] - o[1], c[2] - o[2]));
      if (d > bd) { bd = d; best = i; }
    });
    used.add(best); out.push(spots[best]);
  }
  return out;
}

// feet on a lava top right now? (pos = feet, like everywhere else)
export function onLava(s, boxes, pos, tol = 0.06) {
  const hw = PH.halfW;
  for (const b of query(boxes, pos[0] - hw, pos[2] - hw, pos[0] + hw, pos[2] + hw, near)) {
    if (!s.lava.has(b) || Math.abs(pos[1] - b.max[1]) > tol) continue;
    if (pos[0] + hw > b.min[0] && pos[0] - hw < b.max[0] && pos[2] + hw > b.min[2] && pos[2] - hw < b.max[2]) return b;
  }
  return null;
}
// first thing below a point is lava (bots look before they step, the client checks before believing a touch)
export function lavaBelow(s, boxes, p, depth = 8) {
  const h = raycast(p, down, depth, boxes);
  return !!h && s.lava.has(h.box);
}
// nearest safe spot (bots grapple toward it when they're standing in lava)
export function nearestSafe(s, p, maxD = 40) {
  let best = null, bd = maxD;
  for (const c of s.spots) { const d = Math.hypot(c[0] - p[0], c[1] - p[1], c[2] - p[2]); if (d < bd) { bd = d; best = c; } }
  return best;
}
