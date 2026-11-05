// All maps are lists of axis-aligned boxes. Shared by server (physics, bots) and client (rendering).
// Maps are generated deterministically so server and client always match.
// Rule of thumb for builders: never let two different surfaces sit in the same plane (that flickers).
import { buildNav, navPath, navLocate, navClear } from './nav.js';
import { outOfBounds } from './bounds.js';

function rng(seed) { // mulberry32
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function builder() {
  const boxes = [];
  const add = (x0, y0, z0, x1, y1, z1, mat = 'stone', extra) => {
    if (x1 < x0) [x0, x1] = [x1, x0];
    if (y1 < y0) [y0, y1] = [y1, y0];
    if (z1 < z0) [z0, z1] = [z1, z0];
    if (x1 - x0 < 0.01 || y1 - y0 < 0.01 || z1 - z0 < 0.01) return;
    boxes.push(Object.assign({ min: [x0, y0, z0], max: [x1, y1, z1], mat }, extra || {}));
  };
  const box = (cx, cy, cz, sx, sy, sz, mat, extra) => add(cx - sx / 2, cy - sy / 2, cz - sz / 2, cx + sx / 2, cy + sy / 2, cz + sz / 2, mat, extra);
  // a box turned yaw radians round its centre: RENDER-ONLY builders (map.deco) only, physics and bots never see these
  const obb = (cx, cy, cz, sx, sy, sz, yaw, mat, extra) => { if (sx > 0.01 && sy > 0.01 && sz > 0.01) boxes.push(Object.assign({ min: [cx - sx / 2, cy - sy / 2, cz - sz / 2], max: [cx + sx / 2, cy + sy / 2, cz + sz / 2], mat, rot: yaw }, extra || {})); };
  // a local frame: origin (ox, oy, oz), rotated rot*90deg. local -z is "the front".
  const local = (ox, oz, rot = 0, oy = 0) => {
    const T = (x, z) => [[x, z], [-z, x], [-x, -z], [z, -x]][rot & 3];
    const L = (x0, y0, z0, x1, y1, z1, mat, extra) => {
      const [ax, az] = T(x0, z0), [bx, bz] = T(x1, z1);
      if (extra && extra.pad) { const [px, pz] = T(extra.pad[0], extra.pad[2]); extra = { ...extra, pad: [px, extra.pad[1], pz] }; }
      add(ox + ax, oy + y0, oz + az, ox + bx, oy + y1, oz + bz, mat, extra);
    };
    L.B = (cx, cy, cz, sx, sy, sz, mat, extra) => L(cx - sx / 2, cy - sy / 2, cz - sz / 2, cx + sx / 2, cy + sy / 2, cz + sz / 2, mat, extra);
    L.P = (x, y, z) => { const [ax, az] = T(x, z); return [ox + ax, oy + y, oz + az]; }; // a local point in world space
    return L;
  };
  return { boxes, add, box, local, obb };
}

// a wall with holes cut in it. axis 'x' = runs along x at z=fixed, 'z' = runs along z at x=fixed.
// openings: [{ a, b, y0, y1 }] measured along the wall. they may overlap (a door under a balcony door), so the wall
// is cut at every opening edge and each piece keeps only the heights no opening covers
function wall(L, axis, fixed, a0, a1, y0, y1, t, mat, openings = []) {
  const ops = openings.filter((o) => o.b > a0 && o.a < a1);
  const seg = (s0, s1, yy0, yy1) => {
    if (s1 - s0 < 0.02 || yy1 - yy0 < 0.02) return;
    if (axis === 'x') L(s0, yy0, fixed - t / 2, s1, yy1, fixed + t / 2, mat);
    else L(fixed - t / 2, yy0, s0, fixed + t / 2, yy1, s1, mat);
  };
  const cuts = [...new Set([a0, a1, ...ops.flatMap((o) => [Math.max(a0, o.a), Math.min(a1, o.b)])])].sort((p, q) => p - q);
  for (let i = 0; i < cuts.length - 1; i++) {
    const s0 = cuts[i], s1 = cuts[i + 1], m = (s0 + s1) / 2;
    let y = y0;
    for (const o of ops.filter((o) => o.a < m && o.b > m).sort((p, q) => p.y0 - q.y0)) {
      seg(s0, s1, y, Math.min(y1, o.y0));
      y = Math.max(y, o.y1);
    }
    seg(s0, s1, y, y1);
  }
}

// slab with a rectangular hole (for stairwells)
function slab(L, x0, z0, x1, z1, y0, y1, mat, hole) {
  if (!hole) { L(x0, y0, z0, x1, y1, z1, mat); return; }
  const [hx0, hz0, hx1, hz1] = hole;
  L(x0, y0, z0, x1, y1, hz0, mat);
  L(x0, y0, hz1, x1, y1, z1, mat);
  L(x0, y0, hz0, hx0, y1, hz1, mat);
  L(hx1, y0, hz0, x1, y1, hz1, mat);
}

// a flight of solid steps from (x0..x1) starting at z0 going toward dir (+1/-1) along z, from height ya to yb
function stairs(L, x0, x1, z0, dir, ya, yb, mat = 'wood', run = 0.5) {
  const n = Math.max(1, Math.ceil((yb - ya) / 0.45));
  const h = (yb - ya) / n;
  for (let i = 1; i <= n; i++) {
    const za = z0 + dir * (i - 1) * run, zb = z0 + dir * i * run;
    L(x0, ya, za, x1, ya + i * h, zb, mat);
  }
  return z0 + dir * n * run;
}

// windows spread along a wall of length len (centred on 0), sill/top relative to y0
function windows(len, y0, sill = 1.0, top = 2.2, spacing = 4, skipCenter = 0) {
  const out = [];
  const n = Math.max(1, Math.floor(len / spacing));
  for (let i = 0; i < n; i++) {
    const c = -len / 2 + (i + 0.5) * (len / n);
    if (skipCenter && Math.abs(c) < skipCenter) continue;
    out.push({ a: c - 0.75, b: c + 0.75, y0: y0 + sill, y1: y0 + top });
  }
  return out;
}

// hollow multi-floor building in a local frame: footprint x[-w/2,w/2] z[-d/2,d/2], front door at -z.
// switchback stairs in the back-left corner, optional stairs onto the roof.
function shell(L, w, d, floors, F, mat, o = {}) {
  const t = 0.3, hw = w / 2, hd = d / 2;
  const floorMat = o.floor || 'wood';
  const laneA = [-hw + 0.25, -hw + 1.75], laneB = [-hw + 1.85, -hw + 3.35];
  const run = 0.5, sz0 = hd - 0.4 - 4.6; // flights live in z [sz0, hd-0.4]
  L(-hw, 0, -hd, hw, 0.12, hd, floorMat); // ground floor
  const flights = floors - 1 + (o.roofAccess ? 1 : 0);
  for (let f = 0; f < floors; f++) {
    const y0 = f * F, y1 = (f + 1) * F, base = f === 0 ? 0.12 : y0 + 0.25;
    const winsF = windows(w, base, 1.0, 2.2, o.winSpacing || 4, f === 0 ? 1.6 : 0);
    if (f === 0) winsF.push({ a: -1, b: 1, y0: 0, y1: 2.5 });
    if (f === 0 && o.backDoor) winsF.length && null;
    wall(L, 'x', -hd, -hw, hw, y0, y1, t, mat, winsF);
    wall(L, 'x', hd, -hw, hw, y0, y1, t, mat, o.backDoor && f === 0 ? [{ a: 1.5, b: 3.1, y0: 0, y1: 2.5 }, ...windows(w, base, 1, 2.2, 5, 3.2)] : windows(w, base, 1, 2.2, 5));
    wall(L, 'z', -hw, -hd, hd, y0, y1, t, mat, windows(d, base, 1, 2.2, 4.5).filter((x) => x.b < sz0 - 0.2));
    wall(L, 'z', hw, -hd, hd, y0, y1, t, mat, o.sideDoor && f === 0 ? [{ a: o.sideDoor[0], b: o.sideDoor[1], y0: 0, y1: 2.5 }] : windows(d, base, 1, 2.2, 4.5));
    // stairs from this floor up
    if (f < flights) {
      const lane = f % 2 === 0 ? laneA : laneB;
      const ya = f === 0 ? 0.12 : y0 + 0.25, yb = y1 + 0.25;
      if (f % 2 === 0) stairs(L, lane[0], lane[1], sz0, 1, ya, yb, floorMat, run);
      else stairs(L, lane[0], lane[1], hd - 0.4, -1, ya, yb, floorMat, run);
    }
    // slab above this floor (with the hole for the flight that arrives through it)
    const arriving = f < flights;
    const lane = f % 2 === 0 ? laneA : laneB;
    const hole = arriving ? [lane[0] - 0.05, sz0 - 0.6, lane[1] + 0.05, hd - 0.35] : null;
    const isRoof = f === floors - 1;
    if (isRoof && o.noRoof) continue;
    slab(L, -hw, -hd, hw, hd, y1, y1 + (isRoof ? 0.3 : 0.25), isRoof ? (o.roof || 'concrete') : floorMat, hole);
    // railing, with a gap at the end the flight arrives at so you can step off the top (it used to box you in: jump or nothing)
    if (arriving && !isRoof) L(lane[1] + 0.05, y1 + 0.25, sz0 - 0.6 + (f % 2 ? 1.6 : 0), lane[1] + 0.15, y1 + 1.25, hd - 0.35 - (f % 2 ? 0 : 1.6), 'wood');
  }
  if (!o.noRoof && o.parapet !== false) { // parapet round the roof
    const y = floors * F + 0.3;
    L(-hw, y, -hd, hw, y + 0.8, -hd + 0.3, mat); L(-hw, y, hd - 0.3, hw, y + 0.8, hd, mat);
    L(-hw, y, -hd + 0.3, -hw + 0.3, y + 0.8, hd - 0.3, mat); L(hw - 0.3, y, -hd + 0.3, hw, y + 0.8, hd - 0.3, mat);
  }
  return { top: floors * F + 0.3 };
}

// ------------------------------------------------------------ props
function car(L, x, z, rot, color = 'carred') {
  const C = (lx0, y0, lz0, lx1, y1, lz1, m) => (rot ? L(x + lz0, y0, z + lx0, x + lz1, y1, z + lx1, m) : L(x + lx0, y0, z + lz0, x + lx1, y1, z + lz1, m));
  C(-2.2, 0.32, -0.92, 2.2, 0.95, 0.92, color); // body
  C(-2.3, 0.3, -0.9, -2.2, 0.55, 0.9, 'chrome'); C(2.2, 0.3, -0.9, 2.3, 0.55, 0.9, 'chrome'); // bumpers
  C(-1.1, 0.95, -0.8, 0.9, 1.5, 0.8, 'glass'); // cabin glass
  C(-1.15, 1.5, -0.82, 0.95, 1.6, 0.82, color); // roof
  C(-0.15, 0.95, -0.83, 0.05, 1.5, -0.79, color); C(-0.15, 0.95, 0.79, 0.05, 1.5, 0.83, color); // B pillars
  for (const sx of [-1.45, 1.35]) for (const sz of [-0.95, 0.95]) C(sx - 0.34, 0, sz - 0.14, sx + 0.34, 0.66, sz + 0.14, 'tire');
  C(2.2, 0.62, -0.8, 2.26, 0.82, -0.45, 'light'); C(2.2, 0.62, 0.45, 2.26, 0.82, 0.8, 'light');
  C(-2.26, 0.62, -0.8, -2.2, 0.8, -0.5, 'tail'); C(-2.26, 0.62, 0.5, -2.2, 0.8, 0.8, 'tail');
}
function tree(L, x, z, h = 4.5) {
  L.B(x, h / 2, z, 0.6, h, 0.6, 'wood');
  L.B(x, h + 0.9, z, 3.6, 1.8, 3.6, 'leaves');
  L.B(x, h + 2.2, z, 2.4, 1.0, 2.4, 'leaves');
}
function streetlight(L, x, z, armDir = 1) {
  L.B(x, 3, z, 0.25, 6, 0.25, 'metal');
  L(x, 5.8, z - 0.12, x + armDir * 1.6, 6.0, z + 0.12, 'metal');
  L.B(x + armDir * 1.6, 5.8, z, 0.6, 0.25, 0.4, 'light');
}
function acUnit(L, x, z, y) { L.B(x, y + 0.7, z, 2, 1.4, 1.4, 'metal'); L.B(x, y + 1.45, z, 1.2, 0.1, 1.2, 'grid'); }
function waterTower(L, x, z, y) {
  for (const ox of [-1.3, 1.3]) for (const oz of [-1.3, 1.3]) L.B(x + ox, y + 2.5, z + oz, 0.3, 5, 0.3, 'wood');
  L.B(x, y + 5.2, z, 3.6, 0.3, 3.6, 'wood');
  L.B(x, y + 7, z, 3.2, 3.4, 3.2, 'wood');
  L.B(x, y + 8.9, z, 2.4, 0.4, 2.4, 'roofg');
}
function billboard(L, x, z, y, along = 'x') {
  const w = 12;
  if (along === 'x') { L.B(x - 4, y + 3, z, 0.3, 6, 0.3, 'metal'); L.B(x + 4, y + 3, z, 0.3, 6, 0.3, 'metal'); L.B(x, y + 7.5, z, w, 5, 0.4, 'billboard', { fit: 1 }); L.B(x, y + 4.9, z - 0.6, w, 0.2, 1.0, 'grid'); }
  else { L.B(x, y + 3, z - 4, 0.3, 6, 0.3, 'metal'); L.B(x, y + 3, z + 4, 0.3, 6, 0.3, 'metal'); L.B(x, y + 7.5, z, 0.4, 5, w, 'billboard', { fit: 1 }); L.B(x - 0.6, y + 4.9, z, 1.0, 0.2, w, 'grid'); }
}

// a skyscraper: tiers with setbacks, cornices, parapets and roof stuff. returns roof top height
function tower(B, x, z, w, d, h, o = {}) {
  const r = o.r || Math.random;
  const base = o.base ?? -110;
  const tiers = o.tiers || 1;
  let y0 = base, cw = w, cd = d;
  const tops = [];
  for (let i = 0; i < tiers; i++) {
    const y1 = i === tiers - 1 ? h : base + (h - base) * ((i + 1) / tiers) * (0.82 + 0.06 * i);
    const top = Math.round(y1);
    B.box(x, (y0 + top) / 2, z, cw, top - y0, cd, o.facade || 'office');
    B.box(x, top + 0.25, z, cw + 0.8, 0.5, cd + 0.8, 'concrete'); // cornice / terrace floor
    if (i < tiers - 1) { // terrace railing
      const hw = (cw + 0.8) / 2, hd = (cd + 0.8) / 2;
      B.add(x - hw, top + 0.5, z - hd, x + hw, top + 1.4, z - hd + 0.25, 'metal');
      B.add(x - hw, top + 0.5, z + hd - 0.25, x + hw, top + 1.4, z + hd, 'metal');
      B.add(x - hw, top + 0.5, z - hd + 0.25, x - hw + 0.25, top + 1.4, z + hd - 0.25, 'metal');
      B.add(x + hw - 0.25, top + 0.5, z - hd + 0.25, x + hw, top + 1.4, z + hd - 0.25, 'metal');
    }
    tops.push({ y: top + 0.5, w: cw, d: cd });
    y0 = top + 0.5;
    cw = Math.max(10, cw - 8); cd = Math.max(10, cd - 8);
  }
  const roof = tops[tops.length - 1];
  const ry = roof.y, hw = roof.w / 2, hd = roof.d / 2;
  // parapet
  B.add(x - hw, ry, z - hd, x + hw, ry + 1, z - hd + 0.4, 'concrete'); B.add(x - hw, ry, z + hd - 0.4, x + hw, ry + 1, z + hd, 'concrete');
  B.add(x - hw, ry, z - hd + 0.4, x - hw + 0.4, ry + 1, z + hd - 0.4, 'concrete'); B.add(x + hw - 0.4, ry, z - hd + 0.4, x + hw, ry + 1, z + hd - 0.4, 'concrete');
  const L = B.local(x, z, 0, ry);
  // stairwell / elevator housing with a door
  L(-hw + 1, 0, -hd + 1, -hw + 6, 3.6, -hd + 5, 'concrete');
  L(-hw + 2.8, 0, -hd + 5, -hw + 4.2, 2.3, -hd + 5.1, 'metal');
  L(-hw + 0.8, 3.6, -hd + 0.8, -hw + 6.2, 3.9, -hd + 5.2, 'roofg');
  const kind = o.roof || ['ac', 'tank', 'antenna', 'billboard', 'helipad', 'garden'][(r() * 6) | 0];
  if (kind === 'ac' || r() < 0.5) for (let i = 0; i < 3; i++) acUnit(L, hw - 3, -hd + 3 + i * 2.6, 0);
  if (kind === 'tank') waterTower(L, hw - 5, hd - 5, 0);
  if (kind === 'antenna') { L.B(2, 9, 2, 0.5, 18, 0.5, 'metal'); L.B(2, 18.4, 2, 3, 0.6, 3, 'pink'); }
  if (kind === 'billboard') billboard(L, 0, hd - 2, 0, 'x');
  if (kind === 'helipad') L(-5.5, 0, -5.5 + 2, 5.5, 0.15, 5.5 + 2, 'helipad');
  if (kind === 'garden') {
    L(-hw + 0.5, 0, 0, hw - 0.5, 0.3, hd - 0.5, 'grass');
    tree(L, -3, hd - 4, 3); tree(L, 3, hd - 5, 3.5);
    L(-hw + 1, 0.3, 1, -hw + 7, 1.1, 1.6, 'hedge');
  }
  if (r() < 0.4) L(-2, 0, -2, 2, 0.6, 4, 'glassblock'); // skylight
  if (o.pad) L(hw - 4, 0, hd - 4, hw - 1.5, 0.3, hd - 1.5, 'pad', { pad: o.pad });
  return ry;
}

// cut the region [x0..x1, y0..y1, z0..z1] out of every box it touches (doorways through parapets): each box keeps
// up to six pieces around the hole. only boxes passing keep(b) are cut
function carve(B, x0, y0, z0, x1, y1, z1, keep = () => true) {
  const out = [];
  for (const b of B.boxes) {
    const [a, c] = [b.min, b.max];
    if (!keep(b) || a[0] >= x1 || c[0] <= x0 || a[1] >= y1 || c[1] <= y0 || a[2] >= z1 || c[2] <= z0) { out.push(b); continue; }
    const piece = (p0, p1) => { if (p1[0] - p0[0] > 0.01 && p1[1] - p0[1] > 0.01 && p1[2] - p0[2] > 0.01) out.push({ ...b, min: p0, max: p1 }); };
    const cx0 = Math.max(a[0], x0), cx1 = Math.min(c[0], x1), cy0 = Math.max(a[1], y0), cy1 = Math.min(c[1], y1);
    piece([a[0], a[1], a[2]], [x0, c[1], c[2]]); piece([x1, a[1], a[2]], [c[0], c[1], c[2]]); // either side on x
    piece([cx0, a[1], a[2]], [cx1, y0, c[2]]); piece([cx0, y1, a[2]], [cx1, c[1], c[2]]); // below / above
    piece([cx0, cy0, a[2]], [cx1, cy1, z0]); piece([cx0, cy0, z1], [cx1, cy1, c[2]]); // either side on z
  }
  B.boxes.length = 0; B.boxes.push(...out);
}

// the street level far below a city map (render-only, D = a deco builder): wet neon roads on a grid, crossings, parked
// and abandoned cars, streetlights, shopfronts with neon and ads round the foot of every tower, little parks. falling
// still kills you before you get here, but now you see where you were going. towers: [{ x, z, w, d }],
// roads: { xs: [x of each road running along z], zs: [z of each road running along x], w: width }, S: half size
function streetLevel(D, y, towers, roads, S, r) {
  const W = roads.w || 16, half = W / 2;
  D.add(-S, y - 1, -S, S, y, S, 'sidewalk'); // pavement everywhere, roads on top
  const ads = ['adcity1', 'adcity2', 'adcity3', 'adcity4', 'adcity5', 'adcity6'], neons = ['neonbar', 'neonnoodle', 'neonhotel', 'neonwork'];
  const strip = ['neonpink', 'neoncyan', 'neonyellow', 'neongreen'];
  const pick = (a) => a[(r() * a.length) | 0];
  // roads (x-runs split at the z-roads so the two never overlap in one plane), crossings at every junction
  const cuts = (list, a) => [-S, ...list.flatMap((v) => [v - half, v + half]), S].filter((v, i, l) => i === 0 || v > l[i - 1]);
  for (const z of roads.zs) { const c = cuts(roads.xs); for (let i = 0; i + 1 < c.length; i += 2) D.add(c[i], y, z - half, c[i + 1], y + 0.08, z + half, 'wetroad'); }
  for (const x of roads.xs) { D.add(x - half, y, -S, x + half, y + 0.08, S, 'wetroadz'); }
  for (const x of roads.xs) for (const z of roads.zs) { D.add(x - half, y + 0.08, z - half - 3, x + half, y + 0.1, z - half, 'crosswalk'); D.add(x - half, y + 0.08, z + half, x + half, y + 0.1, z + half + 3, 'crosswalk'); }
  const L = D.local(0, 0, 0, y + 0.08);
  const inTower = (x, z, m = 1) => towers.some((t) => Math.abs(x - t.x) < t.w / 2 + m && Math.abs(z - t.z) < t.d / 2 + m);
  // cars: parked along the kerbs, a few stopped dead in the middle (nobody drives here any more)
  const cols = ['carred', 'carblue', 'carwhite', 'carblack', 'cargreen', 'caryellow', 'burnt'];
  for (const z of roads.zs) for (let x = -S + 8; x < S - 8; x += 9 + r() * 14) { if (roads.xs.some((v) => Math.abs(x - v) < half + 4)) continue; car(L, x, z + (r() < 0.5 ? -1 : 1) * (r() < 0.75 ? half - 1.3 : 2.2), 0, pick(cols)); }
  for (const x of roads.xs) for (let z = -S + 8; z < S - 8; z += 9 + r() * 14) { if (roads.zs.some((v) => Math.abs(z - v) < half + 4)) continue; car(L, x + (r() < 0.5 ? -1 : 1) * (r() < 0.75 ? half - 1.3 : 2.2), z, 1, pick(cols)); }
  // streetlights and the odd bus shelter down both sides of every road
  for (const z of roads.zs) for (let x = -S + 6; x < S; x += 18) for (const s of [-1, 1]) if (!roads.xs.some((v) => Math.abs(x - v) < half + 2) && !inTower(x, z + s * (half + 1.2))) streetlight(L, x, z + s * (half + 1.2), 1);
  for (const x of roads.xs) for (let z = -S + 6; z < S; z += 18) for (const s of [-1, 1]) if (!roads.zs.some((v) => Math.abs(z - v) < half + 2) && !inTower(x + s * (half + 1.2), z)) streetlight(L, x + s * (half + 1.2), z, 1);
  // shopfronts round the foot of every tower: an awning, a neon sign, an ad, a glowing strip
  for (const t of towers) for (const [nx, nz] of [[0, -1], [0, 1], [-1, 0], [1, 0]]) {
    const len = nx ? t.d : t.w, cx = t.x + nx * (t.w / 2), cz = t.z + nz * (t.d / 2);
    for (let k = -len / 2 + 3; k < len / 2 - 5; k += 7 + r() * 3) {
      const px = nx ? cx : t.x + k + 2, pz = nz ? cz : t.z + k + 2, along = nx ? 'z' : 'x';
      const box = (o0, u0, a0, o1, u1, a1, m, ex) => { // o = out from the wall, u = up, a = along it
        const [ox0, ox1] = [o0 * (nx || nz), o1 * (nx || nz)].sort((p, q) => p - q);
        if (along === 'x') D.add(px + a0, y + u0, pz + ox0, px + a1, y + u1, pz + ox1, m, ex); else D.add(px + ox0, y + u0, pz + a0, px + ox1, y + u1, pz + a1, m, ex);
      };
      box(0.02, 0, -2, 0.12, 3.2, 2, 'window');
      box(0, 3.4, -2.4, 2.2, 3.6, 2.4, pick(['toypink', 'toyteal', 'toyyellow', 'toypurple', 'cloth']));
      if (r() < 0.6) box(0.05, 4.0, -2, 0.3, 5.0, 2, pick(neons), { fit: 1 }); else box(0.05, 4.0, -2.2, 0.3, 6.8, 2.2, pick(ads), { fit: 1 });
      box(0.02, 7.2, -2.5, 0.2, 7.4, 2.5, pick(strip));
    }
    // a vertical neon sign up the corner of some towers
    if (r() < 0.6) D.add(t.x + t.w / 2, y + 9, t.z - t.d / 2 - 0.3, t.x + t.w / 2 + 0.3, y + 30, t.z - t.d / 2 + 2.4, pick(strip));
  }
  // pocket parks in some of the leftover corners, and cables strung across the streets with ads hanging off them
  for (const x of roads.xs) for (const z of roads.zs) if (r() < 0.5) {
    const px = x + half + 6, pz = z + half + 6;
    if (inTower(px, pz, 4)) continue;
    D.add(px - 3, y, pz - 3, px + 3, y + 0.5, pz + 3, 'stone'); D.add(px - 2.6, y + 0.5, pz - 2.6, px + 2.6, y + 0.6, pz + 2.6, 'lawn');
    lollipop(D.local(px, pz, 0, y + 0.6), 0, 0, 3, r);
  }
}

// neon crowns, facade ads and cables with hanging ads for a grid of towers (plan rows: [x, z, w, d, h, tiers])
function cityDress(D, plan, roofs, base, r) {
  const strip = ['neonpink', 'neoncyan', 'neonyellow', 'neongreen'], ads = ['adcity1', 'adcity2', 'adcity3', 'adcity4', 'adcity5', 'adcity6'];
  const pick = (a) => a[(r() * a.length) | 0];
  const firstTop = (h, tiers) => (tiers > 1 ? base + (h - base) * (1 / tiers) * 0.82 : h);
  for (const [x, z, w, d, h, tiers] of plan) {
    const ry = roofs[`${x},${z}`], cw = Math.max(10, w - 8 * (tiers - 1)) / 2, cd = Math.max(10, d - 8 * (tiers - 1)) / 2;
    const c = pick(strip); // a glowing band round the crown, and another lower down
    D.add(x - cw - 0.06, ry - 2.4, z - cd - 0.06, x + cw + 0.06, ry - 1.9, z + cd + 0.06, c);
    const by = Math.min(base + 70, firstTop(h, tiers) - 3); // on the lowest tier, or it floats outside a narrower one
    D.add(x - w / 2 - 0.06, by, z - d / 2 - 0.06, x + w / 2 + 0.06, by + 0.6, z + d / 2 + 0.06, pick(strip));
    // a huge ad up one face of the lowest tier
    const t0 = firstTop(h, tiers), ay = base + 40 + r() * Math.max(1, t0 - base - 70), side = (r() * 4) | 0;
    if (t0 - ay > 20) {
      if (side < 2) { const fz = z + (side ? d / 2 : -d / 2), s = side ? 1 : -1; D.add(x - 7, ay, Math.min(fz, fz + s * 0.3), x + 7, ay + 9, Math.max(fz, fz + s * 0.3), pick(ads), { fit: 1 }); }
      else { const fx = x + (side > 2 ? w / 2 : -w / 2), s = side > 2 ? 1 : -1; D.add(Math.min(fx, fx + s * 0.3), ay, z - 7, Math.max(fx, fx + s * 0.3), ay + 9, z + 7, pick(ads), { fit: 1 }); }
    }
  }
  // cables between neighbours on the grid, with an ad and a neon strip hanging off the middle
  for (const a of plan) for (const b of plan) {
    const dx = b[0] - a[0], dz = b[1] - a[1];
    if (!((dx > 0 && dz === 0 && dx < 80) || (dz > 0 && dx === 0 && dz < 80))) continue;
    const top = Math.min(firstTop(a[4], a[5]), firstTop(b[4], b[5])) - 6, y = base + 30 + r() * Math.max(5, top - base - 40);
    if (y > top) continue;
    if (dz === 0) {
      const x0 = a[0] + a[2] / 2, x1 = b[0] - b[2] / 2, z = a[1] + (r() - 0.5) * 8, m = (x0 + x1) / 2;
      D.add(x0, y, z - 0.05, x1, y + 0.1, z + 0.05, 'tire'); D.add(x0, y - 3, z + 1.95, x1, y - 2.9, z + 2.05, 'tire');
      D.add(m - 5, y - 6, z - 0.15, m + 5, y - 0.6, z + 0.15, pick(ads), { fit: 1 }); D.add(m - 5, y - 6.4, z - 0.2, m + 5, y - 6, z + 0.2, pick(strip));
    } else {
      const z0 = a[1] + a[3] / 2, z1 = b[1] - b[3] / 2, x = a[0] + (r() - 0.5) * 8, m = (z0 + z1) / 2;
      D.add(x - 0.05, y, z0, x + 0.05, y + 0.1, z1, 'tire'); D.add(x + 1.95, y - 3, z0, x + 2.05, y - 2.9, z1, 'tire');
      D.add(x - 0.15, y - 6, m - 5, x + 0.15, y - 0.6, m + 5, pick(ads), { fit: 1 }); D.add(x - 0.2, y - 6.4, m - 5, x + 0.2, y - 6, m + 5, pick(strip));
    }
  }
}

// The rest of the city, out to the fog: the mess of a real old downtown instead of a grid. Districts each run their own
// street grid at their own angle (the old town's blocks small, narrow and crooked, the newer ones big and square), a few
// long avenues cut across them on the diagonal, and the land ends at a waterfront: a park, a promenade, a sea wall and
// piers with boats. Render-only. Near the towers it stays under the kill line, so a fall never passes through a roof;
// further out it climbs, but never as tall as the towers you fight on. y: street level, S: half size of the street grid
// round the towers, R: how far out, o: { kill (y), cap (y), shore (z of the coast), avenues: [[x, z, angle], ...] }
function cityBeyond(D, y, S, R, r, o) {
  const shore = (x) => o.shore + 38 * Math.sin(x / 150 + 1) + 18 * Math.sin(x / 47), park = (x) => shore(x) - 34;
  const pick = (a) => a[(r() * a.length) | 0];
  // ---- the ground (dark wet asphalt: the streets are the gaps between blocks), the park strip, the promenade, the sea
  for (let x = -R; x < R; x += 20) {
    const zp = park(x + 10);
    if (x + 20 <= -S || x >= S) D.add(x, y - 1, -R, x + 20, y, zp, 'asphaltn');
    else { // a strip that runs into the street grid's square: above it, below it, and the bits beside it
      D.add(x, y - 1, -R, x + 20, y, -S, 'asphaltn'); if (zp > S) D.add(x, y - 1, S, x + 20, y, zp, 'asphaltn');
      if (x < -S) D.add(x, y - 1, -S, -S, y, S, 'asphaltn');
      if (x + 20 > S) D.add(S, y - 1, -S, x + 20, y, S, 'asphaltn');
    }
    D.add(x, y - 1, zp, x + 20, y + 0.25, zp + 24, 'lawn');
    D.add(x, y - 1, zp + 24, x + 20, y + 0.3, zp + 33, 'sidewalk');
    D.add(x, y - 8, zp + 33, x + 20, y + 0.9, zp + 33.6, 'stone'); // the sea wall
    if (((x / 20) | 0) % 3 === 0) lollipop(D.local(x + 6 + r() * 8, zp + 6 + r() * 12, 0, y + 0.25), 0, 0, 3.5 + r() * 2, r);
    if (((x / 20) | 0) % 4 === 1) { D.add(x + 8, y + 0.3, zp + 25, x + 11, y + 0.75, zp + 25.8, 'wood'); streetlight(D.local(0, 0, 0, y + 0.3), x + 3, zp + 31, 1); }
  }
  D.add(-R - 600, y - 4.2, o.shore - 80, R + 600, y - 3.8, R + 700, 'seawater');
  // piers out into the water, sheds and crates on them, boats tied up
  for (let x = -R + 40; x < R - 40; x += 55 + r() * 30) {
    const z0 = park(x) + 33.6, len = 40 + r() * 30;
    D.add(x - 3.5, y - 0.2, z0, x + 3.5, y + 0.3, z0 + len, 'wood');
    for (let z = z0 + 4; z < z0 + len; z += 6) for (const px of [x - 3.2, x + 2.9]) D.add(px, y - 4.2, z, px + 0.3, y - 0.2, z + 0.3, 'wood');
    if (r() < 0.6) { D.add(x - 2.6, y + 0.3, z0 + len - 14, x + 2.6, y + 3.6, z0 + len - 4, pick(['containerb', 'brick', 'sidelemon', 'containerr'])); D.add(x - 2.9, y + 3.6, z0 + len - 14.3, x + 2.9, y + 4, z0 + len - 3.7, 'roofg'); }
    for (let k = 0; k < 3; k++) D.add(x - 2 + k * 1.3, y + 0.3, z0 + 6, x - 1 + k * 1.3, y + 1.3, z0 + 7, 'crate');
    if (r() < 0.55) { const bx = x + 4.5 + r(), bz = z0 + 8 + r() * (len - 30), m = pick(['toyred', 'toyblue', 'toyyellow', 'white']);
      D.add(bx, y - 4.4, bz, bx + 4.2, y - 2.4, bz + 16, m); D.add(bx + 0.6, y - 2.4, bz + 6, bx + 3.6, y + 0.2, bz + 12, 'white'); D.add(bx + 0.7, y - 1.3, bz + 6.1, bx + 3.5, y - 0.4, bz + 11.9, 'glass'); }
  }
  // ---- long avenues on the diagonal (each a little higher than the last, so crossings never share a plane)
  const aves = (o.avenues || []).map(([ax, az, a], k) => ({ ax, az, ux: Math.cos(a), uz: Math.sin(a), a, k }));
  const aveDist = (x, z) => Math.min(1e9, ...aves.map((v) => Math.abs((x - v.ax) * v.uz - (z - v.az) * v.ux)));
  const onLand = (x, z, m = 0) => Math.abs(x) < R - m && Math.abs(z) < R - m && z < park(x) - m && !(Math.abs(x) < S + m && Math.abs(z) < S + m);
  for (const v of aves) {
    let run = null;
    const flush = (t) => { if (run === null) return; const t0 = run, len = t - t0; if (len > 12) { const tm = (t0 + t) / 2, cx = v.ax + v.ux * tm, cz = v.az + v.uz * tm;
      D.obb(cx, y + 0.04 + v.k * 0.01, cz, len, 0.08, 16, -v.a, 'wetroad');
      for (const s2 of [-1, 1]) D.obb(cx - v.uz * s2 * 9.5, y + 0.1 + v.k * 0.01, cz + v.ux * s2 * 9.5, len, 0.2, 3, -v.a, 'sidewalk'); } run = null; };
    for (let t = -R * 1.5; t <= R * 1.5; t += 6) { const x = v.ax + v.ux * t, z = v.az + v.uz * t; if (onLand(x, z, 4)) { if (run === null) run = t; } else flush(t); }
    flush(R * 1.5);
  }
  // ---- districts: angular slices round the middle, each with its own grid
  const K = 7, cuts = [], hash = new Map(), HC = 40;
  let acc = r() * Math.PI * 2;
  for (let k = 0; k < K; k++) { cuts.push(acc); acc += (Math.PI * 2 / K) * (0.7 + r() * 0.6); }
  const sector = (x, z) => { let a = Math.atan2(z, x); for (let k = K - 1; k >= 0; k--) { let d = a - cuts[k]; while (d < 0) d += Math.PI * 2; let w = (k + 1 < K ? cuts[k + 1] : cuts[0] + Math.PI * 2) - cuts[k]; while (w <= 0) w += Math.PI * 2; if (d < w) return k; } return 0; };
  // blocks from neighbouring districts can collide along the seam (inside one district the grid keeps them apart)
  const near = (x, z, rad, k) => { for (let i = Math.floor((x - rad) / HC) - 1; i <= Math.floor((x + rad) / HC) + 1; i++) for (let j = Math.floor((z - rad) / HC) - 1; j <= Math.floor((z + rad) / HC) + 1; j++) for (const q of hash.get(i * 9973 + j) || []) if (q[3] !== k && Math.hypot(q[0] - x, q[1] - z) < (q[2] + rad) * 0.9) return true; return false; };
  const keep = (x, z, rad, k) => { const i = Math.floor(x / HC), j = Math.floor(z / HC), key = i * 9973 + j; if (!hash.has(key)) hash.set(key, []); hash.get(key).push([x, z, rad, k]); };
  const old = (r() * K) | 0; // the old town: small, narrow, crooked
  const facadesLow = ['brick', 'tenement', 'concrete', 'sidepink', 'sidemint', 'sideorange', 'tenement'], facadesHigh = ['office', 'window', 'tenement', 'glassblock', 'office'];
  const strips = ['neonpink', 'neoncyan', 'neonyellow', 'neongreen'];
  const thetas = [];
  for (let k = 0; k < K; k++) {
    const isOld = k === old, th = thetas[k] = r() * Math.PI, ux = Math.cos(th), uz = Math.sin(th), vx = -uz, vz = ux;
    const bw = isOld ? 20 + r() * 8 : 38 + r() * 34, bd = isOld ? 16 + r() * 8 : 26 + r() * 26, sw = isOld ? 6 + r() * 2 : 11 + r() * 6;
    const ox = (r() - 0.5) * 40, oz = (r() - 0.5) * 40, n = Math.ceil((R * 1.5) / Math.min(bw + sw, bd + sw));
    for (let i = -n; i <= n; i++) for (let j = -n; j <= n; j++) {
      const cx = ox + i * (bw + sw) * ux + j * (bd + sw) * vx, cz = oz + i * (bw + sw) * uz + j * (bd + sw) * vz;
      if (sector(cx, cz) !== k) continue;
      const w = bw * (0.8 + r() * 0.35), d = bd * (0.8 + r() * 0.35), rad = Math.hypot(w, d) / 2;
      if (!onLand(cx, cz, rad * 0.7) || aveDist(cx, cz) < 10.5 + rad * 0.6 || near(cx, cz, rad, k)) continue;
      keep(cx, cz, rad, k);
      const yaw = -(th + (r() - 0.5) * (isOld ? 0.24 : 0.06)), cy = Math.cos(-yaw), sy = Math.sin(-yaw);
      D.obb(cx, y + 0.12 + r() * 0.06, cz, w, 0.24 + r() * 0.06, d, yaw, 'sidewalk'); // the block's kerb
      // buildings along the block's long side, heights by how far out it is
      const far = Math.max(Math.abs(cx), Math.abs(cz)) - S, lots = isOld ? 2 + ((r() * 3) | 0) : 1 + ((r() * 3) | 0);
      for (let l = 0; l < lots; l++) {
        const lw = w / lots, off = -w / 2 + lw * (l + 0.5), bx = cx + cy * off, bz = cz + sy * off;
        const fw = lw - 1.6 - r() * 1.5, fd = d - 2.4 - r() * 3;
        let h;
        if (far < 110) h = 3 + r() * Math.max(1, o.kill - y - 4); // under the kill line
        else if (far < 260) h = 8 + r() * Math.min(45, o.cap - y - 10) * Math.min(1, (far - 110) / 150);
        else h = 14 + r() * (o.cap - y - 14) * (r() < 0.25 ? 1 : 0.55);
        if (far > 260 && r() < 0.04) h = o.cap - y - r() * 6; // the odd landmark tower
        h = Math.max(3, Math.min(h, o.cap - y));
        const mat = h < 24 ? pick(facadesLow) : pick(facadesHigh);
        D.obb(bx, y + 0.3 + h / 2, bz, fw, h, fd, yaw, mat);
        D.obb(bx, y + 0.3 + h + 0.2, bz, fw - 0.5, 0.4, fd - 0.5, yaw, 'roofg');
        if (r() < 0.22) D.obb(bx, y + 0.3 + h - 2.5, bz, fw + 0.12, 0.5, fd + 0.12, yaw, pick(strips)); // a glowing band near the top
        if (h > 20 && r() < 0.15) D.obb(bx + cy * (fw / 2 + 0.2), y + 0.3 + h * 0.6, bz + sy * (fw / 2 + 0.2), 0.3, Math.min(14, h * 0.3), Math.min(10, fd * 0.6), yaw, pick(['adcity1', 'adcity2', 'adcity3', 'adcity4', 'adcity5', 'adcity6']), { fit: 1 });
        if (r() < 0.3) D.obb(bx - sy * fd * 0.2, y + 0.3 + h + 0.9, bz + cy * fd * 0.2, 2.4, 1.2, 2.4, yaw, 'metal'); // an AC box
      }
    }
  }
  // infill: the odd lots left along the seams between districts get small blocks, turned to fit their district (roughly)
  for (let t = 0; t < 2600; t++) {
    const cx = (r() * 2 - 1) * R, cz = (r() * 2 - 1) * R, w = 12 + r() * 16, d = 10 + r() * 14, rad = Math.hypot(w, d) / 2;
    if (!onLand(cx, cz, rad * 0.7) || aveDist(cx, cz) < 10.5 + rad * 0.6 || near(cx, cz, rad * 1.05, -1)) continue;
    keep(cx, cz, rad, -1);
    const far = Math.max(Math.abs(cx), Math.abs(cz)) - S, yaw = -(thetas[sector(cx, cz)] + (r() - 0.5) * 0.5);
    const h = Math.max(3, Math.min(o.cap - y, far < 110 ? 3 + r() * Math.max(1, o.kill - y - 4) : 6 + r() * 26));
    D.obb(cx, y + 0.12 + r() * 0.06, cz, w, 0.25, d, yaw, 'sidewalk');
    D.obb(cx, y + 0.3 + h / 2, cz, w - 2, h, d - 2, yaw, pick(facadesLow));
    D.obb(cx, y + 0.5 + h, cz, w - 2.5, 0.4, d - 2.5, yaw, 'roofg');
  }
}

const SKY_SUNSET = { top: 0x2b1d6b, mid: 0xff8fb8, bot: 0x14051a, fog: 0xf7a1c4 };

// render-only ground from the edge of a map's real ground [x0, z0, x1, z1] out to the horizon (R), so the ground carries on
// past where you can walk without a floor plane that would cap every pit and canyon
function horizon(D, x0, z0, x1, z1, R, mat, y = 0) {
  D.add(-R, y - 2, -R, R, y, z0, mat); D.add(-R, y - 2, z1, R, y, R, mat);
  D.add(-R, y - 2, z0, x0, y, z1, mat); D.add(x1, y - 2, z0, R, y, z1, mat);
}

// ------------------------------------------------------------ CRATE: tiny on purpose, pure chaos
function crate() {
  const B = builder();
  const { box } = B;
  box(0, -1.5, 0, 30, 3, 30, 'rubber'); // a toy box floating in the sky: confetti rubber
  box(0, -5, 0, 20, 4, 20, 'dirt');
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) { box(8 * sx, 1, 8 * sz, 2, 2, 2, 'crate'); box(8 * sx + 1.6 * sx, 0.5, 8 * sz, 1.2, 1, 1.2, sx * sz > 0 ? 'toyred' : 'toyblue'); }
  box(0, 1, 10, 5, 2, 1, 'crate');
  box(0, 1, -10, 5, 2, 1, 'crate');
  box(0, 1.5, 0, 5, 3, 5, 'toyface', { fit: 1 });
  box(0, 3.25, 0, 7, 0.5, 7, 'toyteal');
  box(-5, 0.15, 0, 1.8, 0.3, 1.8, 'pad', { pad: [4, 14, 0] });
  box(5, 0.15, 0, 1.8, 0.3, 1.8, 'pad', { pad: [-4, 14, 0] });
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) box(12 * sx, 15, 12 * sz, 2.5, 1, 2.5, 'toypink');
  box(0, 21, 0, 3, 1, 3, 'gold');
  // it's a toy box on top of a tower of giant toy blocks, in a giant kid's playroom (render-only). fall off: you die long
  // before the carpet
  const D = builder(), F = -90; // the floor
  D.box(0, -18, 0, 26, 22, 26, 'toyface', { fit: 1 }); D.box(2, -48, -1, 32, 38, 32, 'toyface2', { fit: 1 }); D.box(-1, -78, 1, 36, 24, 36, 'toyface', { fit: 1 });
  D.add(-420, F - 2, -420, 420, F, 420, 'rubber');
  D.add(-420, F, -422, 420, 300, -420, 'wallkid'); D.add(-420, F, 420, 420, 300, 422, 'wallkid'); D.add(-422, F, -420, -420, 300, 420, 'wallkid'); D.add(420, F, -420, 422, 300, 420, 'wallkid');
  D.add(-420, 300, -420, 420, 304, 420, 'plaster'); D.add(-50, 290, -50, 50, 300, 50, 'lamp'); D.add(-2, 296, -2, 2, 300, 2, 'chrome');
  D.add(-160, 40, -419.9, 160, 230, -419.5, 'skypane', { fit: 1 }); D.add(-170, 30, -419.5, 170, 40, -415, 'white'); // the window
  D.add(-380, F, 120, -120, F + 70, 380, 'cloth'); D.add(-380, F + 70, 120, -120, F + 90, 380, 'white'); D.add(-380, F + 90, 300, -120, F + 120, 380, 'toyteal'); // the bed
  D.add(180, F, 140, 300, F + 120, 260, 'toyred'); // a giant ball (well, a giant cube)
  for (const [x, z, m] of [[140, -160, 'toyblue'], [170, -140, 'toygreen'], [200, -170, 'toyyellow']]) D.add(x, F, z, x + 18, F + 18, z + 160, m); // crayons
  D.add(-260, F, -220, -200, F + 60, -160, 'toyface2', { fit: 1 }); D.add(-250, F + 60, -210, -210, F + 100, -170, 'toyface', { fit: 1 });
  D.add(60, F, -330, 260, F + 8, -320, 'toypink'); D.add(60, F, -250, 260, F + 8, -240, 'toypink'); // a toy train track
  for (let x = 66; x < 260; x += 14) D.add(x, F, -320, x + 4, F + 4, -250, 'wood');
  D.add(100, F + 8, -305, 150, F + 40, -265, 'toyred'); D.add(150, F + 8, -305, 180, F + 30, -265, 'toyyellow'); // the engine
  return { name: 'Crate', size: 'tiny', boxes: B.boxes, deco: D.boxes, killY: -30, sky: { top: 0xffd6ec, mid: 0xffd6ec, bot: 0xffd6ec, fog: 0xffd6ec }, fogNear: 90, fogFar: 700,
    sealed: true, light: { hemi: [0xfff0f6, 0xc09ab0, 1.4], sun: [0xfff6e8, 1.0] },
    spawns: [[-11, 0.1, -11], [11, 0.1, 11], [-11, 0.1, 11], [11, 0.1, -11]] };
}

// ------------------------------------------------------------ PLATFORM: one big flat gray slab
function platform() {
  const B = builder();
  B.box(0, -1, 0, 90, 2, 90, 'grid');
  B.box(0, -5, 0, 76, 6, 76, 'concrete');
  const D = builder();
  D.add(-45.06, -0.6, -45.06, 45.06, -0.3, 45.06, 'neonpink'); D.add(-38.06, -4, -38.06, 38.06, -3.7, 38.06, 'neoncyan');
  // it's an offshore rig: four legs down into the sea, braces, a lower deck with containers, a crane, a flare burning
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) { D.box(sx * 30, -20.5, sz * 30, 6, 25, 6, 'rust'); D.box(sx * 30, -32.7, sz * 30, 9, 1, 9, 'white'); }
  for (const y of [-14, -25]) for (const s2 of [-1, 1]) { D.add(-27, y - 0.6, s2 * 30 - 0.6, 27, y + 0.6, s2 * 30 + 0.6, 'hazard'); D.add(s2 * 30 - 0.6, y - 0.6, -27, s2 * 30 + 0.6, y + 0.6, 27, 'hazard'); }
  D.add(-27, -20, -27, 0, -19, 0, 'grid'); for (const [x, z, m] of [[-24, -24, 'containerr'], [-24, -12, 'containerb'], [-12, -24, 'containerg']]) D.add(x, -19, z, x + 6, -16.4, z + 2.5, m);
  D.box(38, -9, 20, 2, 18, 2, 'hazard'); D.add(36, 0, 19, 70, 1.2, 21, 'hazard'); D.box(67, -8, 20, 0.2, 16, 0.2, 'metal'); // the crane, a hook hanging
  D.add(44, -3, -2, 78, -1.6, 2, 'metal'); D.add(76, -1.6, -1.4, 79, 3, 1.4, 'rust'); D.add(76.4, 3, -1, 78.6, 6.5, 1, 'neonyellow'); D.add(76.9, 6.5, -0.5, 78.1, 8.6, 0.5, 'neonred'); // the flare
  for (const [x, z] of [[-520, -360], [610, 240], [-200, 640]]) { for (const sx of [-1, 1]) for (const sz of [-1, 1]) D.box(x + sx * 14, -18, z + sz * 14, 4, 30, 4, 'rust'); D.add(x - 22, -3, z - 22, x + 22, 0, z + 22, 'grid'); D.box(x + 18, 6, z, 2, 12, 2, 'neonyellow'); } // the other rigs
  D.add(260, -33.6, -120, 330, -27, -104, 'toyred'); D.add(306, -27, -118, 324, -20, -106, 'white'); D.add(307, -24, -118.1, 323, -22, -105.9, 'glass'); // a ship going past
  for (const [x, z, al, ad] of [[0, -50, 'x', 'adcity2'], [0, 50, 'x', 'adcity4'], [-50, 0, 'z', 'adcity1'], [50, 0, 'z', 'adcity6']]) adBoard(D, x, z, -14, al, ad, 30, 12);
  return { name: 'Platform', size: 'small', boxes: B.boxes, deco: D.boxes, killY: -30, floorY: -33,
    sky: { top: 0x5a6070, mid: 0xb8bcc8, bot: 0x2a2c33, fog: 0xb8bcc8 }, fogNear: 80, fogFar: 320,
    spawns: [[-35, 0.1, -35], [35, 0.1, 35], [-35, 0.1, 35], [35, 0.1, -35], [0, 0.1, -35], [0, 0.1, 35], [-35, 0.1, 0], [35, 0.1, 0]] };
}

// ------------------------------------------------------------ ROOFTOP: the top of a skyscraper with a glass penthouse
function rooftop() {
  const B = builder();
  const r = rng(77);
  B.box(0, -76, 0, 64, 152, 64, 'office');
  B.box(0, 0.25, 0, 64.8, 0.5, 64.8, 'concrete'); // roof deck, top at 0.5
  const top = 0.5;
  B.add(-32.4, top, -32.4, 32.4, top + 1.1, -32, 'concrete'); B.add(-32.4, top, 32, 32.4, top + 1.1, 32.4, 'concrete');
  B.add(-32.4, top, -32, -32, top + 1.1, 32, 'concrete'); B.add(32, top, -32, 32.4, top + 1.1, 32, 'concrete');
  const L = B.local(0, 0, 0, top);
  // helipad on a raised steel deck with stairs
  L(10, 0, 10, 30, 3, 30, 'metal');
  L(10.5, 3, 10.5, 29.5, 3.15, 29.5, 'helipad');
  stairs(L, 6, 9.8, 10.5, 1, 0, 3, 'grid');
  // glass penthouse bar you can walk into
  const P = B.local(-14, -14, 0, top);
  shell(P, 18, 14, 1, 3.6, 'glassblock', { floor: 'tile', roof: 'roofg', backDoor: true, roofAccess: true, winSpacing: 3 });
  P(-6, 0.12, -3, 4, 1.1, -2, 'wood'); P(-6, 0.12, -2, -5, 1.1, 3, 'wood'); // bar counter
  for (let i = 0; i < 4; i++) P.B(-2 + i * 2.2, 0.55, 2, 0.6, 0.9, 0.6, 'metal'); // stools
  // stairwell housings, AC rows, water tank, antenna, billboard, skylights
  L(16, 0, -28, 22, 3.8, -22, 'concrete'); L(18, 0, -22, 20, 2.4, -21.9, 'metal');
  L(-28, 0, 16, -22, 3.8, 22, 'concrete'); L(-22, 0, 18, -21.9, 2.4, 20, 'metal');
  for (let i = 0; i < 4; i++) { acUnit(L, -2 + i * 3, 4, 0); acUnit(L, -2 + i * 3, 7, 0); }
  waterTower(L, 26, -12, 0);
  L.B(-26, 11, -26, 0.6, 22, 0.6, 'metal'); L.B(-26, 22.4, -26, 3.5, 0.6, 3.5, 'pink');
  billboard(L, 0, -29, 0, 'x');
  L(2, 0, -18, 8, 0.6, -10, 'glassblock'); L(-6, 0, 18, 2, 0.6, 24, 'glassblock');
  L(-8, 0, 26, -4, 0.15, 30, 'pad', { pad: [0, 22, 34] });
  L(26, 0, 0, 30, 0.15, 4, 'pad', { pad: [34, 22, 0] });
  L(-30, 0, -2, -26, 0.15, 2, 'pad', { pad: [-34, 22, 0] });
  L(-2, 0, -26, 2, 0.15, -22, 'pad', { pad: [0, 22, -34] });
  // neighbouring towers to grapple / bhop to
  const spawns = [[0, top + 0.1, 0], [20, 3.3 + top, 20], [-14, 0.3 + top, -14], [-20, top + 0.1, 20], [24, top + 0.1, -4]];
  const plan = [[0, 0, 64, 64, 0, 1]], roofs = { '0,0': top };
  for (const [x, z, h, w, t] of [[0, -95, -2, 36, 2], [-95, 0, 8, 30, 1], [95, 6, -8, 40, 2], [6, 98, 12, 32, 1], [-85, -85, 24, 26, 3], [88, 88, -4, 30, 2], [-90, 90, 4, 34, 1], [92, -92, 16, 28, 2]]) {
    const ry = tower(B, x, z, w, w, h, { tiers: t, base: -152, r });
    spawns.push([x + 3, ry + 0.1, z + 3]);
    plan.push([x, z, w, w, h, t]); roofs[`${x},${z}`] = ry;
  }
  // the look (render-only): a street far below instead of the void, neon crowns, cables with ads, a sign on our roof
  const D = builder();
  streetLevel(D, -142, plan.map(([x, z, w, d]) => ({ x, z, w, d })), { xs: [-140, -55, 55, 140], zs: [-140, -55, 55, 140], w: 18 }, 180, r);
  cityDress(D, plan, roofs, -152, r);
  cityBeyond(D, -142, 180, 520, rng(5151), { kill: -130, cap: -14, shore: 340, avenues: [[0, -260, 0.62], [260, 0, -0.95], [-240, 60, 1.4], [-200, -300, 2.6]] });
  return { name: 'Rooftop', size: 'medium', boxes: B.boxes, deco: D.boxes, killY: -130, floorY: -150, cityR: 520, cityCap: -14,
    sky: { top: 0x05051a, mid: 0x4a2a7a, bot: 0x000005, fog: 0x2a2050 }, fogNear: 110, fogFar: 480, spawns };
}

// ------------------------------------------------------------ SUBURB: a megacorp show-home cul-de-sac
// two rows of candy-coloured houses face each other across one long street, a bus and a box truck stuck in the middle
// of it as cover, fenced backyards with gates, back lanes behind both rows for flanking, a turnaround with a statue at
// the east end, a corner store and a building site at the west end. the ground runs out flat in every direction and a
// ring of trees marks the edge: walk out through them and you get the RETURN TO THE MAP countdown
function home(B, ox, oz, rot, o, r) {
  const L = B.local(ox, oz, rot), F = 3.4;
  shell(L, 14, 12, 2, F, o.siding, { roof: o.roof, backDoor: true, sideDoor: [1, 2.6] });
  // ground floor: a wall splits the kitchen (left) from the living room, and the living room from the laundry at the back
  wall(L, 'z', -1, -6, 6, 0.12, F, 0.2, 'plaster', [{ a: -4, b: -2.4, y0: 0, y1: 2.4 }]);
  wall(L, 'x', 1.5, -1, 7, 0.12, F, 0.2, 'plaster', [{ a: 2, b: 3.4, y0: 0, y1: 2.4 }]);
  // upstairs: two bedrooms + a bathroom
  wall(L, 'x', 1, -1.6, 7, F + 0.25, 2 * F, 0.2, 'plaster', [{ a: 0, b: 1.4, y0: F + 0.25, y1: F + 2.6 }]);
  wall(L, 'z', 2.5, 1, 6, F + 0.25, 2 * F, 0.2, 'plaster', [{ a: 2, b: 3.3, y0: F + 0.25, y1: F + 2.6 }]);
  wall(L, 'z', -1.6, -6, 1, F + 0.25, 2 * F, 0.2, 'plaster', [{ a: -3.5, b: -2, y0: F + 0.25, y1: F + 2.6 }]);
  // furniture (the fridge is chrome, the couch is the colour of a hospital waiting room, the tv shows static)
  L(-6.8, 0.12, -5.8, -5.8, 1.0, -2.4, 'white');
  L(-6.8, 0.12, -2.3, -6.0, 2.1, -1.5, 'chrome');
  L(-4.6, 0.12, -1, -2.6, 0.9, 1, 'wood');
  L(2, 0.12, -1.6, 6.6, 0.75, -0.6, 'cloth'); L(2, 0.75, -1, 6.6, 1.3, -0.6, 'cloth');
  L(3, 0.12, -5.8, 6, 0.6, -5.3, 'wood'); L(3.5, 0.6, -5.75, 5.5, 1.7, -5.65, 'tvstatic');
  L(3, F + 0.25, 3.5, 6.6, F + 0.8, 5.8, 'carpet'); L(3, F + 0.8, 5.2, 6.6, F + 1.1, 5.8, 'white');
  L(-1.3, F + 0.25, -5.8, 2.2, F + 0.8, -3.6, 'carpet');
  L(-1.4, F + 0.25, 4.2, 1.2, F + 0.85, 5.8, 'tile');
  // a stepped toy roof with a chimney
  L(-6.3, 2 * F + 0.3, -5.3, 6.3, 2 * F + 0.75, 5.3, o.roof); L(-4.6, 2 * F + 0.75, -3.8, 4.6, 2 * F + 1.2, 3.8, o.roof);
  L(-2.8, 2 * F + 1.2, -2.2, 2.8, 2 * F + 1.65, 2.2, o.roof); L(3.4, 2 * F + 0.75, 1.5, 4.4, 2 * F + 2.6, 2.5, 'brick');
  // porch with a neon OPEN HOUSE sign over the door
  L(-3, 0, -7.6, 3, 0.25, -6, 'wood');
  L(-2.9, 0.25, -7.5, -2.6, 3.0, -7.2, 'wood'); L(2.6, 0.25, -7.5, 2.9, 3.0, -7.2, 'wood');
  L(-3.2, 3.0, -7.8, 3.2, 3.25, -6.15, o.roof);
  L(-1.4, 2.62, -6.45, 1.4, 3.0, -6.17, 'signopen', { fit: 1 });
  // garage: open front, flat roof you can climb onto (bin -> crate -> roof), window from the roof into the bedroom
  wall(L, 'z', 13, -6, 1.2, 0, 3.2, 0.3, 'brick');
  wall(L, 'x', 1.2, 7.15, 13, 0, 3.2, 0.3, 'brick');
  wall(L, 'x', -6, 7.15, 13, 0, 3.2, 0.3, 'brick', [{ a: 7.6, b: 12.6, y0: 0, y1: 2.7 }]);
  L(7.2, 0, -6, 13, 0.1, 1.2, 'concrete');
  L(7, 3.2, -6.2, 13.2, 3.5, 1.4, 'roofg');
  L(13.2, 0, -2.2, 14.3, 1.2, -1.1, 'metal');
  L(13.2, 0, -1.05, 14.6, 2.4, 0.4, 'crate');
  car(L, 10.1, -2.4, 1, o.car);
  // driveway, front path, mailbox
  L(7.4, 0, -17, 12.8, 0.12, -6, 'sidewalk');
  L(-1, 0, -17, 1, 0.12, -7.65, 'sidewalk');
  L.B(2.2, 0.6, -15.5, 0.15, 1.2, 0.15, 'wood'); L.B(2.2, 1.35, -15.5, 0.5, 0.35, 0.8, 'toyblue');
  // backyard: picket fence with a gate onto the back lane, a tree, a trampoline onto the roof, a shed
  const fy = 1.3;
  L(-8, 0, 13.9, -1.2, fy, 14.1, 'picket'); L(1.2, 0, 13.9, 14, fy, 14.1, 'picket');
  L(-8.1, 0, 6.2, -7.9, fy, 13.9, 'picket');
  L(13.9, 0, 1.4, 14.1, fy, 11, 'picket');
  lollipop(L, -4, 12.8, 4 + r() * 2, r);
  L(2.5, 0, 8.5, 5, 0.25, 11, 'pad', { pad: [0, 21, -4] });
  L(8, 0, 9, 12, 2.6, 13, 'wood'); L(7.8, 2.6, 8.8, 12.2, 2.8, 13.2, 'roofg');
  if (o.yard === 'pool') { // above-ground pool
    L(-6.5, 0, 7, -1.5, 1.1, 7.2, 'tile'); L(-6.5, 0, 11.6, -1.5, 1.1, 11.8, 'tile');
    L(-6.5, 0, 7.2, -6.3, 1.1, 11.6, 'tile'); L(-1.7, 0, 7.2, -1.5, 1.1, 11.6, 'tile');
    L(-6.3, 0, 7.2, -1.7, 0.85, 11.6, 'water');
  } else if (o.yard === 'toy') { // a giant glossy googly toy, like the yard grew it
    L(-6.4, 0, 7.4, -3.4, 3, 10.4, 'toyface', { fit: 1 });
  } else { // a hot tub and a grill
    L(-6.6, 0, 7.2, -3.8, 0.9, 10, 'toyteal'); L(-6.3, 0.9, 7.5, -4.1, 0.95, 9.7, 'water');
    L(-1.8, 0, 8, -0.8, 1.0, 8.8, 'tire');
  }
}

// a lollipop tree: trunk and a few chunky stacked canopies, now and then in a colour no tree should be
function lollipop(L, x, z, h, r) {
  const leaf = r() < 0.12 ? 'blossom' : r() < 0.35 ? 'leaves2' : 'leaves';
  L.B(x, h / 2, z, 0.6, h, 0.6, 'wood');
  L.B(x, h + 0.9, z, 3.6, 1.8, 3.6, leaf);
  L.B(x, h + 2.2, z, 2.4, 1.0, 2.4, leaf);
}
function conifer(L, x, z, h, r) {
  L.B(x, 1, z, 0.5, 2, 0.5, 'wood');
  for (let i = 0; i < 4; i++) L.B(x, 2 + (i + 0.5) * h / 4, z, 4.2 - i * 0.95, h / 4, 4.2 - i * 0.95, i % 2 ? 'leaves2' : 'hedge');
}

// a stubby transit bus along +x (front at x0 + 12): you can get in by the door, shoot out through the window gaps
function bus(B, x0, z0) {
  const z1 = z0 + 2.6, X = x0 + 12;
  for (const wx of [x0 + 2.2, x0 + 9.4]) for (const [a, b] of [[z0 - 0.08, z0 + 0.4], [z1 - 0.4, z1 + 0.08]]) B.add(wx - 0.55, 0, a, wx + 0.55, 1.1, b, 'tire');
  B.add(x0, 0.45, z0, X, 0.9, z1, 'busyellow'); // chassis, the floor inside is its top
  B.add(x0, 0.9, z0, X - 0.15, 1.7, z0 + 0.15, 'busyellow');
  B.add(x0, 0.9, z1 - 0.15, x0 + 9.8, 1.7, z1, 'busyellow'); B.add(x0 + 11.1, 0.9, z1 - 0.15, X - 0.15, 1.7, z1, 'busyellow'); // door gap
  for (let x = x0; x < x0 + 11.5; x += 1.55) { // window pillars (the windows are long gone)
    B.add(x, 1.7, z0, x + 0.22, 2.8, z0 + 0.15, 'busyellow');
    if (x + 0.22 < x0 + 9.8 || x > x0 + 11.1) B.add(x, 1.7, z1 - 0.15, x + 0.22, 2.8, z1, 'busyellow');
  }
  B.add(x0 + 9.8, 1.7, z1 - 0.15, x0 + 9.95, 2.8, z1, 'busyellow'); B.add(x0 + 11.1, 1.7, z1 - 0.15, x0 + 11.3, 2.8, z1, 'busyellow');
  B.add(x0, 0.9, z0 + 0.15, x0 + 0.15, 1.75, z1 - 0.15, 'busyellow'); B.add(x0, 2.45, z0 + 0.15, x0 + 0.15, 2.8, z1 - 0.15, 'busyellow'); // back, with the emergency window out
  B.add(X - 0.15, 0.9, z0, X, 1.7, z1, 'busyellow'); B.add(X - 0.12, 1.7, z0 + 0.15, X - 0.02, 2.8, z1 - 0.15, 'glass'); // front + windscreen
  B.add(x0 - 0.06, 2.8, z0 - 0.06, X + 0.06, 3.1, z1 + 0.06, 'busyellow'); // roof
  B.add(x0 + 1.5, 1.0, z0 - 0.03, x0 + 9.5, 1.6, z0, 'adbus', { fit: 1 }); // livery
  B.add(X, 0.6, z0 + 0.2, X + 0.05, 0.85, z0 + 0.6, 'light'); B.add(X, 0.6, z1 - 0.6, X + 0.05, 0.85, z1 - 0.2, 'light');
  B.add(x0 - 0.05, 1.0, z0 + 0.2, x0, 1.3, z0 + 0.5, 'tail'); B.add(x0 - 0.05, 1.0, z1 - 0.5, x0, 1.3, z1 - 0.2, 'tail');
  B.add(x0 + 9.85, 0.2, z1, x0 + 11.05, 0.45, z1 + 0.5, 'metal'); // step up to the door
  for (let i = 0; i < 6; i++) { const x = x0 + 1 + i * 1.5; B.add(x, 0.9, z0 + 0.15, x + 0.9, 1.35, z0 + 1.05, 'seat'); B.add(x + 0.8, 1.35, z0 + 0.15, x + 0.95, 2.0, z0 + 1.05, 'seat'); }
}
// a box truck along +x, cab at the front: the back is open (roller door up) and a crate gets you in
function truck(B, x0, z0, livery = 'adtruck') {
  const z1 = z0 + 2.5;
  for (const wx of [x0 + 1.4, x0 + 5.6, x0 + 8.9]) for (const [a, b] of [[z0 - 0.08, z0 + 0.4], [z1 - 0.4, z1 + 0.08]]) B.add(wx - 0.5, 0, a, wx + 0.5, 1.0, b, 'tire');
  B.add(x0 + 0.3, 0.5, z0 + 0.3, x0 + 9.9, 0.95, z1 - 0.3, 'metal');
  B.add(x0, 0.95, z0, x0 + 7.4, 1.1, z1, 'wood'); // box floor
  B.add(x0, 1.1, z0, x0 + 7.4, 3.8, z0 + 0.12, 'truckbox'); B.add(x0, 1.1, z1 - 0.12, x0 + 7.4, 3.8, z1, 'truckbox');
  B.add(x0 + 7.28, 1.1, z0 + 0.12, x0 + 7.4, 3.8, z1 - 0.12, 'truckbox');
  B.add(x0, 3.8, z0, x0 + 7.4, 3.95, z1, 'truckbox');
  B.add(x0 + 0.05, 3.3, z0 + 0.12, x0 + 0.3, 3.8, z1 - 0.12, 'metal'); // the roller door, rolled up
  B.add(x0 + 1, 1.15, z0 - 0.03, x0 + 6.6, 3.3, z0, livery, { fit: 1 }); B.add(x0 + 1, 1.15, z1, x0 + 6.6, 3.3, z1 + 0.03, livery, { fit: 1 });
  B.add(x0 - 1.1, 0, z0 + 0.5, x0, 0.55, z1 - 0.5, 'crate'); // step in
  B.add(x0 + 7.5, 0.95, z0, x0 + 10, 2.0, z1, 'carred'); // cab
  B.add(x0 + 7.6, 2.0, z0 + 0.1, x0 + 9.4, 2.9, z1 - 0.1, 'glass'); B.add(x0 + 7.5, 2.9, z0, x0 + 9.5, 3.05, z1, 'carred');
  B.add(x0 + 10, 1.2, z0 + 0.2, x0 + 10.05, 1.5, z0 + 0.6, 'light'); B.add(x0 + 10, 1.2, z1 - 0.6, x0 + 10.05, 1.5, z1 - 0.2, 'light');
}
// a flat billboard on two legs, the ad drawn once across its face
function adBoard(B, x, z, y, along, ad, w = 12, h = 5) {
  const L = B.local(x, z, along === 'x' ? 0 : 1, y);
  L.B(-w / 3, 3, 0, 0.4, 6, 0.4, 'metal'); L.B(w / 3, 3, 0, 0.4, 6, 0.4, 'metal');
  L.B(0, 6 + h / 2, 0, w + 0.4, h + 0.4, 0.3, 'metal');
  L.B(0, 6 + h / 2, 0, w, h, 0.5, ad, { fit: 1 });
  L.B(0, 5.9, -0.7, w, 0.2, 1.0, 'grid');
}

function suburb() {
  const B = builder(), D = builder(); // D: render-only (the far rows of the tree ring)
  const r = rng(4242);
  const W = B.local(0, 0, 0);
  const bounds = [-114, -54, 116, 54];
  // the ground: flat lawn a long way out in every direction (no more cliff). past the trees it's just more nothing
  B.add(-260, -3, -200, 260, 0, 200, 'lawn');
  // the street (out west it keeps going, past the barricade, into the out of bounds), the turnaround in the east
  B.add(-260, 0, -7, 44, 0.1, 7, 'roadx');
  B.add(44, 0, -12, 80, 0.1, 12, 'road');
  for (const s of [-1, 1]) { B.add(48, 0, s * 12, 76, 0.1, s * 16, 'road'); B.add(52, 0, s * 16, 72, 0.1, s * 18, 'road'); }
  // sidewalks (0.25 curbs, steppable)
  B.add(-260, 0, -10, 44, 0.25, -7, 'sidewalk'); B.add(-260, 0, 7, 44, 0.25, 10, 'sidewalk');
  for (let x = -104; x <= 40; x += 24) { streetlight(W, x, 9, -1); streetlight(W, x + 12, -9, 1); }
  for (const [x, z, d] of [[46, -15, 1], [78, 15, -1], [46, 15, 1], [78, -15, -1]]) streetlight(W, x, z, d);
  // houses: rot 2 faces +z (the north row, across from the south row), rot 0 faces -z
  const homes = [
    [-60, -27, 2, { siding: 'sidepink', roof: 'roofteal', car: 'carblue', yard: 'pool' }],
    [-24, -27, 2, { siding: 'sidelemon', roof: 'roofpink', car: 'carred', yard: 'toy' }],
    [12, -27, 2, { siding: 'sidelilac', roof: 'roof', car: 'cargreen', yard: 'tub' }],
    [-66, 27, 0, { siding: 'sidemint', roof: 'roof', car: 'carwhite', yard: 'tub' }],
    [-30, 27, 0, { siding: 'sideorange', roof: 'roofteal', car: 'carblack', yard: 'pool' }],
    [6, 27, 0, { siding: 'blue', roof: 'roofpink', car: 'caryellow', yard: 'toy' }],
    [94, 3, 3, { siding: 'sidemint', roof: 'roofpink', car: 'carred', yard: 'pool' }], // the one at the end of the cul-de-sac
  ];
  const spawns = [];
  for (const [x, z, rot, o] of homes) {
    home(B, x, z, rot, o, r);
    const L = B.local(x, z, rot);
    spawns.push(L.P(3.5, 0.3, -3.5), L.P(0, 0.3, 10)); // the living room and the backyard
  }
  // the middle of the street: a bus, a box truck, cars parked along the curbs (one crashed into the bus)
  bus(B, -32, -4.4);
  truck(B, -6, 1.6);
  car(W, -17.6, -2.9, 0, 'carwhite');
  for (const [x, z, c] of [[-84, 5.2, 'carblue'], [-46, -5.2, 'carblack'], [-40, 5.2, 'cargreen'], [24, -5.2, 'carred'], [30, 5.2, 'caryellow']]) car(W, x, z, 0, c);
  // the turnaround: a planter with a statue of the founder (a big glossy googly toy) on a plinth
  B.add(57, 0.1, -5, 67, 0.6, 5, 'stone'); B.add(57.5, 0.6, -4.5, 66.5, 0.7, 4.5, 'lawn');
  B.add(60.6, 0.7, -1.4, 63.4, 2.6, 1.4, 'chrome');
  B.add(60.2, 2.6, -1.8, 63.8, 6.2, 1.8, 'toyface', { fit: 1 });
  B.add(61.2, 1.1, -1.43, 62.8, 1.9, -1.4, 'plaque', { fit: 1 });
  for (const [x, z] of [[58.5, -3.5], [65.5, 3.5], [58.5, 3.5], [65.5, -3.5]]) W.B(x, 1.3, z, 1.2, 1.2, 1.2, 'hedge');

  // ---- west end: the corner store (north) and a building site (south), then the barricade where the road goes nowhere
  const C = B.local(-94, -24, 2);
  shell(C, 18, 12, 1, 4.2, 'brick', { roof: 'roofg', roofAccess: true, backDoor: true });
  C(-8.5, 0.12, -5.5, -1, 1.1, -4.6, 'wood'); C(1, 0.12, -5.5, 8.5, 1.1, -4.6, 'wood');
  for (const x of [-6, -2, 2, 6]) C(x - 0.4, 0.12, -1.5, x + 0.4, 1.9, 3.5, 'shelfstock');
  C(-8, 3.0, -6.55, 8, 4.4, -6.16, 'adstore', { fit: 1 });
  C(-9.4, 0, 6.2, -7.4, 1.2, 8.2, 'crate'); C(-9.4, 1.2, 6.2, -8.4, 2.4, 7.2, 'crate'); C(-9.4, 2.4, 6.2, -8.9, 3.6, 6.7, 'crate');
  B.add(-102.9, 0, -18, -85.1, 0.12, -10, 'concrete');
  for (let x = -101; x < -86; x += 4) B.add(x, 0.12, -17.6, x + 0.15, 0.13, -13, 'white');
  car(W, -98.9, -15, 1, 'cargreen'); car(W, -90.9, -15, 1, 'carwhite');
  adBoard(B, -99, -40, 0, 'x', 'adbig1');
  { // the building site: a slab, a half-framed house, a scaffold, sand, a mixer, the portable toilet
    B.add(-104, 0, 14, -82, 0.3, 36, 'concrete');
    for (let x = -101; x <= -86; x += 1.5) for (const z of [17, 31]) if (Math.abs(x + 93.5) > 1.6) B.box(x, 1.95, z, 0.15, 3.3, 0.15, 'plywood');
    for (let z = 18.5; z < 31; z += 1.5) for (const x of [-101, -86]) if (Math.abs(z - 24) > 1.6) B.box(x, 1.95, z, 0.15, 3.3, 0.15, 'plywood');
    B.add(-101.1, 3.6, 16.9, -85.9, 3.75, 17.1, 'plywood'); B.add(-101.1, 3.6, 30.9, -85.9, 3.75, 31.1, 'plywood');
    B.add(-101.1, 3.6, 17.1, -100.9, 3.75, 30.9, 'plywood'); B.add(-86.1, 3.6, 17.1, -85.9, 3.75, 30.9, 'plywood');
    B.add(-100.9, 3.75, 24, -86.1, 3.95, 30.9, 'plywood'); // half an upstairs
    stairs(W, -99.5, -98, 19.05, 1, 0.3, 3.95, 'plywood', 0.55);
    for (const [x, z] of [[-80.5, 20], [-80.5, 26], [-77.5, 20], [-77.5, 26]]) W.B(x, 2.9, z, 0.2, 5.8, 0.2, 'hazard');
    B.add(-81, 2.8, 19.5, -77, 3, 26.5, 'grid'); B.add(-81, 5.8, 19.5, -77, 6, 26.5, 'grid');
    for (let i = 0; i < 4; i++) B.add(-95 + i * 0.6, 0.3, 32.5 + i * 0.4, -91 - i * 0.6, 0.65 + i * 0.35, 35.8 - i * 0.3, 'sand');
    B.add(-90, 0.3, 21, -88.6, 1.2, 22.4, 'metal'); B.add(-90.2, 1.2, 20.8, -88.4, 2.4, 22.6, 'toyorange');
    B.add(-83.5, 0.3, 33, -82.2, 2.6, 34.3, 'toyblue');
  }
  // the barricade: jersey barriers with gaps, a sign, and the road carrying on into the nothing
  for (let z = -9.5; z < 9.5; z += 3.4) B.add(-110, 0.1, z, -109, 1.1, z + 2.2, 'jersey');
  adBoard(B, -110, -14, 0, 'z', 'adclosed', 8, 3.5);

  // ---- east corners: the fun zone (north) and the HOA office (south)
  { const P = B.local(33, -28, 0);
    P(-11, 0, -14, 11, 0.12, 14, 'rubber'); // the noisiest floor money can buy
    P(-11.2, 0, -14, 11.2, 0.6, -13.8, 'toyred'); P(-11.2, 0, 14, -1.5, 0.6, 14.2, 'toyred'); P(1.5, 0, 14, 11.2, 0.6, 14.2, 'toyred');
    P(-11.2, 0, -14, -11, 0.6, 14, 'toyred'); P(11, 0, -14, 11.2, 0.6, 14, 'toyred');
    // a climbing frame with a slide off the top
    for (const [x, z] of [[-7, -9], [-3, -9], [-7, -5], [-3, -5]]) P.B(x, 2.7, z, 0.3, 5.4, 0.3, 'toyblue');
    P(-7.3, 2.9, -9.3, -2.7, 3.2, -4.7, 'toygreen'); P(-7.3, 5.4, -9.3, -2.7, 5.7, -4.7, 'toyred');
    stairs(P, -6.5, -5, -1.2, -1, 0.12, 3.2, 'toyorange', 0.5);
    for (let i = 0; i < 8; i++) P(-2.7 + i * 0.7, 0.12, -8.2, -2 + i * 0.7, 3.2 - i * 0.38, -5.8, 'toyteal');
    // the ball pit: low walls round a pit of glossy cubes
    P(2, 0.12, 2, 9, 1.0, 2.3, 'toyblue'); P(2, 0.12, 8.7, 9, 1.0, 9, 'toyblue'); P(2, 0.12, 2.3, 2.3, 1.0, 8.7, 'toyblue'); P(8.7, 0.12, 2.3, 9, 1.0, 8.7, 'toyblue');
    const balls = ['toyred', 'toygreen', 'toyorange', 'toyteal', 'toypink'];
    for (let i = 0; i < 5; i++) for (let j = 0; j < 5; j++) P.B(3.1 + i * 1.3, 0.35 + ((i + j) % 2) * 0.12, 3.1 + j * 1.3, 0.9, 0.5 + ((i * j) % 3) * 0.08, 0.9, balls[(i * 3 + j) % 5]);
    P(-9, 0.12, 6, -5, 4.12, 10, 'toyface', { fit: 1 });
    P.B(6, 2.6, -11, 0.3, 5.2, 0.3, 'toyred'); P.B(-1, 2.6, -11, 0.3, 5.2, 0.3, 'toyred'); P(-1.2, 5.2, -11.2, 6.2, 5.5, -10.8, 'toyred'); // swings
    for (const x of [0.5, 2.5, 4.5]) { P.B(x, 3.6, -11, 0.05, 3.2, 0.05, 'chrome'); P.B(x, 1.85, -11, 0.7, 0.12, 0.4, 'toyteal'); }
    adBoard(B, 33, -45, 0, 'x', 'adfun');
  }
  { const H = B.local(33, 28, 0);
    shell(H, 10, 8, 1, 3.6, 'sidelilac', { roof: 'roofpink', floor: 'tile', backDoor: true });
    H(-4, 0.12, -1, 0, 1.0, 0, 'wood'); H.B(-2, 1.4, -0.5, 0.8, 0.6, 0.1, 'tvstatic');
    H(-6.5, 3.0, -4.6, 6.5, 4.3, -4.21, 'adhoa', { fit: 1 });
    H.B(7, 4, -6, 0.2, 8, 0.2, 'chrome'); H(7.1, 6, -6.1, 9.5, 7.6, -5.9, 'flagcorp', { fit: 1 });
    for (let i = 0; i < 4; i++) H(-5 + i * 1.3, 0, -9, -4 + i * 1.3, 1.4, -8.3, i % 2 ? 'toyteal' : 'toypink'); // mailbox cluster
    // a bus stop shelter at the curb
    H(1, 0, -17.4, 7, 0.35, -15.6, 'concrete'); H(1, 0.35, -15.8, 7, 2.6, -15.6, 'glass'); H(0.8, 2.6, -17.6, 7.2, 2.8, -15.4, 'toyteal');
    H(1, 0.35, -17.4, 1.15, 2.6, -15.8, 'chrome'); H(6.85, 0.35, -17.4, 7, 2.6, -15.8, 'chrome'); H(2, 0.35, -16.2, 6, 0.8, -15.8, 'seat');
  }
  // ---- back lanes behind both rows: dumpsters, a camper van, a burnt-out car, a shed you can climb
  B.add(-114, 0, -50, 108, 0.08, -42, 'asphalt'); B.add(-114, 0, 42, 108, 0.08, 50, 'asphalt');
  for (const [x, z, m] of [[-86, -47, 'containerg'], [-40, -44.5, 'containerb'], [-6, -47, 'toypink'], [-78, 44.5, 'containerb'], [-46, 47.5, 'containerg'], [-12, 44.5, 'containerg'], [60, 47, 'toypink']]) W(x, 0.08, z - 1, x + 2.6, 1.5, z + 1, m);
  { const V = B.local(20, -46, 0); V(-3.2, 0.45, -1.2, 3.2, 3.0, 1.2, 'carwhite'); V(1.8, 1.5, -1.25, 3.25, 2.6, 1.25, 'glass'); V(-3.3, 3.0, -1.3, 2, 3.4, 1.3, 'toyorange'); for (const x of [-2, 2]) for (const z of [-1.25, 1.05]) V(x - 0.4, 0, z, x + 0.4, 0.8, z + 0.2, 'tire'); }
  car(W, -64, 46, 0, 'burnt');
  W(-26, 0.08, 44, -20, 3, 49, 'wood'); W(-26.2, 3, 43.8, -19.8, 3.3, 49.2, 'roofg'); W(-27.4, 0.08, 45, -26, 1.5, 46.4, 'crate');
  W(44, 0.08, -50, 52, 2.4, -48.6, 'brick'); // a garden wall to peek over at the fun zone
  // side yards between the houses: hedges and junk, never a full wall
  for (const [x, z, s] of [[-45, -22, -1], [-9, -22, -1], [-45, 22, 1], [-8.5, 22, 1]]) { // s: toward the back lane
    W(x - 4, 0, z - 0.5, x + 1, 1.4, z + 0.5, 'hedge');
    W(x + 2, 0, z + s * 6, x + 3.2, 1.1, z + s * 6 + 1.2, 'metal');
    lollipop(W, x - 1, z + s * 12, 5, r);
  }
  W(-46, 0, 30, -43, 0.5, 33, 'toyteal'); W(-45.7, 0.5, 30.3, -43.3, 0.55, 32.7, 'water'); // a kiddie pool
  W(-6, 0, -34, -3.6, 1.6, -31.6, 'wood'); W(-6.2, 1.6, -34.2, -3.4, 2.0, -31.4, 'roof'); // a doghouse

  // ---- the tree ring: one row you bump into right on the edge, then rows that only exist to look at
  const ring = (T, x0, z0, x1, z1, step, jit) => {
    for (let x = x0; x <= x1; x += step) for (const z of [z0, z1]) (r() < 0.4 ? conifer : lollipop)(T, x + (r() - 0.5) * jit, z + (r() - 0.5) * jit, 5 + r() * 3, r);
    for (let z = z0 + step; z < z1; z += step) for (const x of [x0, x1]) (r() < 0.4 ? conifer : lollipop)(T, x + (r() - 0.5) * jit, z + (r() - 0.5) * jit, 5 + r() * 3, r);
  };
  ring(W, -117, -57, 119, 57, 6.5, 2);
  const Dw = D.local(0, 0, 0);
  ring(Dw, -124, -64, 126, 64, 5.5, 3); ring(Dw, -131, -71, 133, 71, 6, 4);
  for (let i = 0; i < 70; i++) { const a = r() * Math.PI * 2, d = 150 + r() * 90; (r() < 0.5 ? conifer : lollipop)(Dw, Math.cos(a) * d * 1.3, Math.sin(a) * d, 6 + r() * 4, r); }
  for (let x = -250; x < -130; x += 30) streetlight(Dw, x, 9, -1); // the road out west: streetlights to nowhere
  horizon(D, -260, -200, 260, 200, 1500, 'sand'); D.add(-1500, 0, -7, -260, 0.1, 7, 'roadx'); // the lawns stop, the desert and the road carry on

  spawns.push([33, 0.3, -28], [33, 0.3, 26], [-94, 0.3, -24], [-93, 0.5, 24], [-60, 0.2, -46], [-30, 0.2, 46], [40, 0.2, -46], [40, 0.2, 46], [62, 0.2, -10], [-30, 3.3, -3.1]);
  const att = [[-102, 0.2, -3], [-102, 0.2, 3], [-96, 0.2, 0], [-106, 0.2, 0], [-98, 0.35, 8.5], [-98, 0.35, -8.5], [-92, 0.2, -4]];
  const def = [[66, 0.2, -8], [66, 0.2, 8], [72, 0.2, 0], [56, 0.2, -10], [56, 0.2, 10], [74, 0.2, -10], [74, 0.2, 10]];
  spawns.push(...att.slice(0, 3), ...def.slice(0, 3));
  let graph = null;
  const map = {
    name: 'Suburb', size: 'large', boxes: B.boxes, deco: D.boxes, killY: -40, bounds, floorY: -4,
    sky: { top: 0x2f7cf0, mid: 0xffd3ec, bot: 0x7a4a6a, fog: 0xffd3ec }, fogNear: 110, fogFar: 430,
    spawns, teamSpawns: { att, def },
    // bots: a walk graph over the ground (1 m cells): round the houses, through the side yards and gates
    get graph() { return graph || (graph = buildNav(B.boxes, { x0: bounds[0], z0: bounds[1], n: bounds[2] - bounds[0], cell: 1, levels: [0], band: 0.5, keep: (x, z) => !outOfBounds(map, [x, 0, z]) })); },
  };
  return map;
}

// ------------------------------------------------------------ WAREHOUSE: big indoor hall, offices, a fenced yard round it
// inside: rows of blue racking full of boxes, stacked pallets, forklifts, barrels, three shredder shafts in the floor,
// catwalks round the walls. outside: a chain-link fence round a big yard (containers, trailers, trucks, a parking lot,
// a smaller shed, a water tower); go over the fence and you get the RETURN TO THE MAP countdown
function rack(B, x0, z, len, r) { // blue racking with orange beams, three decks you can climb, boxes on every level
  for (let x = x0; x <= x0 + len + 0.01; x += 3) for (const pz of [z - 1.3, z + 1.1]) B.add(x - 0.1, 0, pz, x + 0.1, 7.3, pz + 0.2, 'shelf'); // posts stand proud of the beams (no faces in one plane)
  for (const lvl of [0, 2.4, 4.8]) {
    B.add(x0, lvl + 2, z - 1.2, x0 + len, lvl + 2.25, z + 1.2, 'pallet');
    B.add(x0, lvl + 1.75, z - 1.25, x0 + len, lvl + 2, z - 1.2, 'toyorange'); B.add(x0, lvl + 1.75, z + 1.2, x0 + len, lvl + 2, z + 1.25, 'toyorange');
  }
  for (let x = x0 + 0.3; x + 1.3 < x0 + len; x += 1.5) {
    for (const lvl of [2.25, 4.65, 7.05]) if (r() < 0.7) { const h = 0.6 + r() * 0.9; B.add(x, lvl, z - 0.9 + r() * 0.3, x + 1 + r() * 0.3, lvl + h, z + 0.6 + r() * 0.3, r() < 0.85 ? 'cardboard' : 'shelfstock'); }
    if (Math.floor((x - x0) / 3) % 2 === 0 && r() < 0.8) { B.add(x, 0, z - 0.9, x + 1.2, 0.15, z + 0.7, 'pallet'); B.add(x + 0.05, 0.15, z - 0.85, x + 1.15, 0.15 + 0.6 + r() * 0.8, z + 0.65, 'cardboard'); }
  }
}
function pallets(B, x, z, n, r, top = true) { // a stack of empty pallets, now and then with boxes on top
  for (let i = 0; i < n; i++) B.add(x, i * 0.16, z, x + 1.2, i * 0.16 + 0.15, z + 1.0, 'pallet');
  if (top && r() < 0.6) B.add(x + 0.05, n * 0.16, z + 0.05, x + 1.15, n * 0.16 + 0.5 + r() * 0.7, z + 0.95, 'cardboard');
}
function forklift(B, x, z, rot, lift = 0) {
  const L = B.local(x, z, rot);
  L(-0.9, 0.25, -0.62, 0.7, 1.25, 0.62, 'toyyellow'); L(0.7, 0.25, -0.62, 1.15, 1.55, 0.62, 'toyorange'); // body + counterweight
  for (const [px, pz] of [[-0.85, -0.55], [-0.85, 0.47], [0.45, -0.55], [0.45, 0.47]]) L(px, 1.25, pz, px + 0.08, 2.25, pz + 0.08, 'metal');
  L(-0.9, 2.25, -0.62, 0.55, 2.33, 0.62, 'grid'); L(-0.1, 1.25, -0.35, 0.35, 1.75, 0.35, 'seat');
  for (const pz of [-0.5, 0.36]) L(-1.12, 0.1, pz, -0.98, 2.9, pz + 0.14, 'metal'); // mast
  for (const pz of [-0.42, 0.24]) L(-2.25, 0.15 + lift, pz, -1.12, 0.25 + lift, pz + 0.18, 'metal'); // forks
  if (lift) { L(-2.3, 0.25 + lift, -0.55, -1.15, 0.4 + lift, 0.55, 'pallet'); L(-2.25, 0.4 + lift, -0.5, -1.2, 1.2 + lift, 0.5, 'cardboard'); }
  for (const [px, pz] of [[-0.55, -0.72], [-0.55, 0.52], [0.8, -0.72], [0.8, 0.52]]) L(px - 0.3, 0, pz, px + 0.3, 0.6, pz + 0.2, 'tire');
}
function trailer(B, x0, z0, livery) { // a semi trailer along x on its landing legs (no cab)
  const z1 = z0 + 2.6;
  B.add(x0, 1.3, z0, x0 + 12.5, 4.1, z1, 'truckbox');
  B.add(x0 + 1, 1.5, z0 - 0.03, x0 + 11.5, 3.9, z0, livery, { fit: 1 }); B.add(x0 + 1, 1.5, z1, x0 + 11.5, 3.9, z1 + 0.03, livery, { fit: 1 });
  for (const wx of [x0 + 0.9, x0 + 2.1]) for (const [a, b] of [[z0 + 0.1, z0 + 0.5], [z1 - 0.5, z1 - 0.1]]) B.add(wx - 0.5, 0, a, wx + 0.5, 1.0, b, 'tire');
  B.add(x0 + 0.45, 0.95, z0 + 0.3, x0 + 2.6, 1.3, z1 - 0.3, 'metal');
  for (const pz of [z0 + 0.3, z1 - 0.5]) B.add(x0 + 9.4, 0, pz, x0 + 9.6, 1.3, pz + 0.2, 'metal');
}

// a semi: trailer + cab in a local frame, rear of the trailer at local z = 0 (back it up to a dock), cab toward +z
function semi(B, x, z, rot, livery, cab = true) {
  const L = B.local(x, z, rot);
  L(-1.3, 1.3, 0, 1.3, 4.1, 12.5, 'truckbox');
  L(-1.33, 1.5, 1, -1.3, 3.9, 11.5, livery, { fit: 1 }); L(1.3, 1.5, 1, 1.33, 3.9, 11.5, livery, { fit: 1 });
  L(-1.25, 1.25, -0.05, 1.25, 1.35, 0, 'tail'); // the rear light bar
  for (const wz of [1.2, 2.4]) for (const [a, b] of [[-1.2, -0.8], [0.8, 1.2]]) L(a, 0, wz - 0.5, b, 1.0, wz + 0.5, 'tire');
  L(-1.0, 0.95, 0.6, 1.0, 1.3, 3.0, 'metal');
  for (const px of [-1.0, 0.8]) L(px, 0, 9.4, px + 0.2, 1.3, 9.6, 'metal'); // landing legs
  if (!cab) return;
  L(-1.25, 0.6, 12.7, 1.25, 1.1, 16.6, 'metal'); // chassis under the cab
  L(-1.25, 1.1, 13.6, 1.25, 3.3, 16.4, 'carred'); L(-1.15, 2.2, 16.4, 1.15, 3.1, 16.45, 'glass'); // cab + windscreen
  L(-1.2, 1.1, 16.4, 1.2, 2.2, 16.9, 'carred'); L(-1.0, 1.4, 16.9, 1.0, 2.0, 16.95, 'chrome'); // nose + grille
  L(-1.27, 2.3, 14.2, -1.25, 3.0, 15.9, 'glass'); L(1.25, 2.3, 14.2, 1.27, 3.0, 15.9, 'glass');
  for (const px of [-1.1, 0.95]) L(px, 3.3, 13.6, px + 0.15, 4.6, 13.75, 'chrome'); // exhaust stacks
  for (const wz of [13.4, 16]) for (const [a, b] of [[-1.3, -0.85], [0.85, 1.3]]) L(a, 0, wz - 0.55, b, 1.1, wz + 0.55, 'tire');
  L(-1.25, 1.6, 16.95, -0.8, 1.9, 17, 'light'); L(0.8, 1.6, 16.95, 1.25, 1.9, 17, 'light');
}
function cratePile(B, x, z, n, r) { // crates stacked into a rough pyramid
  for (let i = 0; i < n; i++) { const lvl = i < n * 0.55 ? 0 : i < n * 0.85 ? 1 : 2, s = 1.1 + r() * 0.3; B.add(x + (i % 3) * 1.25 + lvl * 0.6, lvl * 1.25, z + ((i / 3) | 0) % 2 * 1.3, x + (i % 3) * 1.25 + lvl * 0.6 + s, lvl * 1.25 + s, z + ((i / 3) | 0) % 2 * 1.3 + s, 'crate'); }
}

function warehouse() {
  const B = builder(), D = builder(); // D: render-only (lamps, trusses, barbed wire)
  const { add, box } = B;
  const r = rng(616);
  const X = 60, Z = 40, H = 16;
  const FX0 = -90, FX1 = 140, FZ = 75; // the fence
  const RX0 = -114, RX1 = -102; // the road past the gate, running left-right to the horizon (centred on the texture's line)
  const bounds = [RX0 - 1, -FZ - 2, FX1 + 2, FZ + 2]; // the fence, and on the gate side the far edge of the road
  // hall floor with three shredder shafts into the void
  const pits = [[-30, -6, -22, 6], [-4, 18, 4, 30], [26, -26, 34, -16]];
  add(-X, -1, -Z, X, 0, -26, 'concrete');
  add(-X, -1, -16, X, 0, -6, 'concrete');
  add(-X, -1, -26, 26, 0, -16, 'concrete'); add(34, -1, -26, X, 0, -16, 'concrete');
  add(-X, -1, -6, -30, 0, 6, 'concrete'); add(-22, -1, -6, X, 0, 6, 'concrete');
  add(-X, -1, 6, X, 0, 18, 'concrete');
  add(-X, -1, 30, X, 0, Z, 'concrete');
  add(-X, -1, 18, -4, 0, 30, 'concrete'); add(4, -1, 18, X, 0, 30, 'concrete');
  for (const [x0, z0, x1, z1] of pits) {
    add(x0, 0, z0 - 0.3, x1, 0.6, z0, 'hazard'); add(x0, 0, z1, x1, 0.6, z1 + 0.3, 'hazard');
    // the shaft: walls going down into the dark, a sign, and teeth at the bottom (you never get that far)
    add(x0 - 0.3, -24, z0 - 0.3, x0, -1, z1 + 0.3, 'rust'); add(x1, -24, z0 - 0.3, x1 + 0.3, -1, z1 + 0.3, 'rust');
    add(x0, -24, z0 - 0.3, x1, -1, z0, 'rust'); add(x0, -24, z1, x1, -1, z1 + 0.3, 'rust');
    for (let x = x0 + 0.5; x < x1; x += 1.4) D.add(x, -22, z0, x + 0.6, -20.5, z1, 'metal');
    D.add(x0 + 1, -20, z0 + 0.05, x1 - 1, -19.7, z1 - 0.05, 'neonred');
    add(x0 + (x1 - x0) / 2 - 2, 0, z0 - 0.62, x0 + (x1 - x0) / 2 + 2, 0.6, z0 - 0.32, 'adshred', { fit: 1 });
  }
  // painted walkways on the hall floor
  for (const z of [-34, 34]) add(-56, 0, z - 0.08, 56, 0.02, z + 0.08, 'neonyellow');
  for (const x of [-30, 8, 40]) add(x - 0.08, 0, -26, x + 0.08, 0.02, -20, 'neonyellow');
  // walls: roller doors on the east side to the loading yard (the middle one half down, somebody tagged it), a door in
  // the west wall and one in the north wall to the yard
  const W = B.local(0, 0, 0);
  wall(W, 'x', -Z, -X, X, 0, H, 0.6, 'metal', [...windows(2 * X, 8, 1, 3, 10), { a: 20, b: 26, y0: 0, y1: 4.5 }]);
  wall(W, 'x', Z, -X, X, 0, H, 0.6, 'metal', [...windows(2 * X, 8, 1, 3, 10), { a: -34, b: -28, y0: 0, y1: 4.5 }]);
  wall(W, 'z', -X, -Z, Z, 0, H, 0.6, 'metal', [...windows(2 * Z, 8, 1, 3, 10), { a: -3, b: 3, y0: 0, y1: 5 }]);
  wall(W, 'z', X, -Z, Z, 0, H, 0.6, 'metal', [{ a: -28, b: -18, y0: 0, y1: 6 }, { a: -6, b: 4, y0: 0, y1: 6 }, { a: 16, b: 26, y0: 0, y1: 6 }]);
  add(X - 0.25, 3.2, -6, X + 0.25, 6, 4, 'graffiti');
  add(X + 0.3, 6.4, -9, X + 0.45, 9.4, 7, 'adware', { fit: 1 });
  add(-6, 9, -Z - 0.45, 6, 12, -Z - 0.3, 'neonwork', { fit: 1 });
  // roof (blue, corrugated) with a skylight strip, rafters, and render-only trusses and hanging lamps
  add(-X, H, -Z, -6, H + 0.6, Z, 'roofblue'); add(6, H, -Z, X, H + 0.6, Z, 'roofblue');
  for (let z = -32; z <= 32; z += 8) {
    add(-X, H - 1.6, z - 0.3, X, H - 1, z + 0.3, 'wood');
    for (let x = -54; x <= 54; x += 6) D.add(x - 0.12, H - 1, z - 0.12, x + 0.12, H, z + 0.12, 'metal');
    for (let x = -48; x <= 48; x += 16) { D.add(x - 0.03, H - 4, z - 0.03, x + 0.03, H - 1.6, z + 0.03, 'tire'); D.add(x - 0.6, H - 4.3, z - 0.6, x + 0.6, H - 4, z + 0.6, 'metal'); D.add(x - 0.45, H - 4.36, z - 0.45, x + 0.45, H - 4.3, z + 0.45, 'lamp'); }
  }
  // catwalks round three walls at 7.3, stairs up at both ends that actually arrive at them (with a gap in the rail)
  add(-X + 0.3, 7, -Z + 0.3, X - 0.3, 7.3, -Z + 3, 'grid');
  add(-X + 0.3, 7, Z - 3, X - 0.3, 7.3, Z - 0.3, 'grid');
  add(-X + 0.3, 7, -Z + 3, -X + 3, 7.3, Z - 3, 'grid');
  add(-X + 3, 7.3, -Z + 3, -24.2, 8.3, -Z + 3.3, 'metal'); add(-20.8, 7.3, -Z + 3, X - 0.3, 8.3, -Z + 3.3, 'metal');
  add(-X + 3, 7.3, Z - 3.3, 36.8, 8.3, Z - 3, 'metal'); add(40.2, 7.3, Z - 3.3, X - 0.3, 8.3, Z - 3, 'metal');
  stairs(W, -24, -21, -Z + 3 + 17 * 0.5, -1, 0, 7.3, 'grid');
  stairs(W, 37, 40, Z - 3 - 17 * 0.5, 1, 0, 7.3, 'grid');
  // racking: the old rows, plus two more rows across the middle
  for (const x of [-44, -14, 14]) for (const z of [-30, 24]) rack(B, x, z, 18, r);
  rack(B, -56, -20, 15, r); rack(B, -10, -20, 30, r); rack(B, 8, 10, 15, r); rack(B, 32, 10, 21, r);
  // two-floor office block in the north-west corner: magenta walls, leopard carpet (nobody asked)
  const O = B.local(-46, 12, 2);
  shell(O, 16, 12, 2, 3.6, 'magenta', { floor: 'leopard', roof: 'roofg', roofAccess: true });
  O(-6, 0.12, -1, -2, 0.85, 1, 'wood'); O(2, 0.12, -1, 6, 0.85, 1, 'wood'); O(-6, 3.85, -1, -2, 4.6, 1, 'wood');
  O.B(-4, 1.15, 0, 0.9, 0.6, 0.1, 'tvstatic'); O.B(4, 1.15, 0, 0.9, 0.6, 0.1, 'tvstatic');
  // floor clutter: forklifts, pallet stacks, barrels, tyres
  forklift(B, -4, -10, 0, 1.4); forklift(B, 20, -4, 1); forklift(B, -40, 32, 2, 2.2); forklift(B, 46, -34, 3);
  for (const [x, z, n] of [[-10, 10, 6], [-8.6, 10, 3], [-10, 11.2, 4], [44, 2, 7], [45.4, 2, 5], [-50, -34, 4], [-34, -10, 8], [22, 32, 5], [-20, 33, 6]]) pallets(B, x, z, n, r);
  for (let i = 0; i < 7; i++) box(-12 + (i % 4) * 0.85, 0.6, -14 + Math.floor(i / 4) * 0.85, 0.75, 1.2, 0.75, i % 3 ? 'barrel' : 'barrelr');
  for (let i = 0; i < 5; i++) box(52 + (i % 3) * 0.85, 0.6, 20 + Math.floor(i / 3) * 0.85, 0.75, 1.2, 0.75, i % 2 ? 'barrelr' : 'barrel');
  for (let i = 0; i < 4; i++) box(50, 0.15 + i * 0.3, -2, 1, 0.3, 1, 'tire'); for (let i = 0; i < 3; i++) box(51.1, 0.15 + i * 0.3, -2, 1, 0.3, 1, 'tire');

  // ---- outside: the ground, the yard, the fence
  groundHoles(B, -230, -190, 260, 190, -1, 0, 'asphalt', [[-X, -Z, X, Z], [X, -50, 110, 50]]);
  add(X, -1, -50, 110, 0, 50, 'concrete'); // the loading yard
  add(X, 0, -50, 110, 0.04, -49.7, 'hazard');
  add(RX0, 0, -190, RX1, 0.06, 190, 'roadz'); add(RX1, 0, -6, FX0, 0.05, 6, 'concrete'); // the road, and the drive in to the gate
  for (const x of [RX0 + 0.4, RX1 - 0.6]) add(x, 0.06, -190, x + 0.2, 0.07, 190, 'white');
  for (const s2 of [-1, 1]) D.add(RX0, 0, s2 > 0 ? 190 : -900, RX1, 0.06, s2 > 0 ? 900 : -190, 'roadz'); // ...on out past the fog both ways
  for (let z = -180; z <= 180; z += 30) { streetlight(W, RX0 - 1, z, 1); }
  for (let z = -870; z <= 870; z += 45) if (Math.abs(z) > 190) streetlight(D.local(0, 0, 0), RX0 - 1, z, 1);
  const Y = B.local(X + 25, 0, 0);
  const cont = (x, z, y, rot, m) => (rot ? Y(x - 1.25, y, z - 6, x + 1.25, y + 2.6, z + 6, m) : Y(x - 6, y, z - 1.25, x + 6, y + 2.6, z + 1.25, m));
  cont(-10, -30, 0, 0, 'containerr'); cont(-10, -30, 2.6, 0, 'containerb'); cont(4, -30, 0, 0, 'containerg');
  cont(-10, 30, 0, 0, 'containerb'); cont(4, 30, 0, 0, 'containerr'); cont(4, 30, 2.6, 0, 'containerg');
  cont(18, 0, 0, 1, 'containerr'); cont(18, 0, 2.6, 1, 'containerg'); cont(21, -14, 0, 1, 'containerb');
  for (const [x, z] of [[-12, -18], [-12, 10]]) { // trucks backed up to the doors
    Y(x - 6, 0.6, z - 1.3, x + 6, 3.8, z + 1.3, 'white');
    Y(x - 5, 0.9, z - 1.33, x + 5, 3.5, z - 1.3, 'adtruck2', { fit: 1 });
    Y(x + 6.3, 0, z - 1.2, x + 9.3, 2.6, z + 1.2, 'carred'); Y(x + 6.4, 2.6, z - 1.1, x + 8.6, 3.4, z + 1.1, 'glass');
    for (const wx of [x - 4, x + 3, x + 8]) for (const wz of [z - 1.35, z + 1.05]) Y(wx - 0.5, 0, wz, wx + 0.5, 1, wz + 0.3, 'tire');
  }
  Y(-24, 0, -6, -20, 1.2, 6, 'concrete');
  Y(22, 0, 18, 24, 1.3, 20, 'crate'); Y(22, 1.3, 18, 24, 2.6, 20, 'crate');
  // east yard beyond the loading yard: more container stacks (a little maze), a trailer, a forklift
  for (const [x, z, h, rot, ms] of [[118, -40, 2, 0, ['containerg', 'containerr']], [118, -22, 1, 0, ['containerb']], [130, -30, 3, 1, ['containerr', 'containerb', 'containerg']], [118, 22, 2, 0, ['containerb', 'containerg']], [132, 30, 1, 1, ['toypink']], [120, 44, 2, 0, ['containerr', 'containerb']]]) {
    for (let k = 0; k < h; k++) { const m = ms[k % ms.length]; if (rot) add(x - 1.25, k * 2.6, z - 6, x + 1.25, (k + 1) * 2.6, z + 6, m); else add(x - 6, k * 2.6, z - 1.25, x + 6, (k + 1) * 2.6, z + 1.25, m); }
  }
  trailer(B, 112, 4, 'adtruck'); forklift(B, 128, 8, 1, 2);
  // north yard: a smaller shed with a blue roof, a parking lot, light masts
  const S2 = B.local(-60, -60, 0);
  shell(S2, 24, 14, 1, 5, 'containerb', { roof: 'roofblue', floor: 'concrete', roofAccess: true, backDoor: true, winSpacing: 6 });
  for (const x of [-9, -3, 3]) rack(B, -60 + x, -60 + 2.5, 3, r);
  add(-20, 0, -66, 50, 0.04, -50, 'asphalt2');
  for (let x = -18; x < 50; x += 4.5) add(x, 0.04, -65, x + 0.15, 0.05, -60, 'white');
  for (const [x, c] of [[-14, 'carred'], [-5, 'caryellow'], [9, 'carblue'], [18, 'burnt'], [36, 'cargreen']]) car(W, x + 1.2, -62.5, 1, c);
  // south yard: trailers in a row, pallets and tyres piled up
  add(-58, 0, 40.3, -38, 1.2, 44, 'concrete'); add(-24, 0, 40.3, 26, 1.2, 44, 'concrete'); // the loading dock (the door at -34..-28 stays)
  for (const [a, b] of [[-58, -38], [-24, 26]]) { add(a, 1.2, 43.9, b, 1.24, 44, 'hazard'); for (let x = a + 1.5; x < b - 1; x += 4) add(x, 0.3, 44, x + 0.5, 1.1, 44.35, 'tire'); add(b, 0, 41, b + 1.2, 0.6, 43.5, 'crate'); }
  for (const [x, door] of [[-53, 'metal'], [-43, 'graffiti'], [-18, 'metal'], [-6, 'metal'], [6, 'graffiti'], [18, 'metal']]) D.add(x - 2.8, 1.2, 40.3, x + 2.8, 5.2, 40.36, door); // dock doors (shut)
  semi(B, -53, 44.4, 0, 'adtruck2'); semi(B, -6, 44.4, 0, 'adtruck'); semi(B, 18, 44.4, 0, 'adtruck2', false);
  forklift(B, -43, 47, 1, 1.2); forklift(B, 6, 48, 3);
  for (const [x, z, n] of [[24, 50, 9], [25.3, 50, 6], [24, 51.1, 3], [40, 60, 8], [-70, 50, 5], [-71.3, 50, 7]]) pallets(B, x, z, n, r, false);
  for (let i = 0; i < 6; i++) for (let k = 0; k <= i % 3; k++) box(52 + i * 1.1, 0.15 + k * 0.3, 62, 1, 0.3, 1, 'tire');
  forklift(B, 34, 66, 0);
  for (const [x, z, n] of [[-30, 62, 9], [48, 50, 7], [-80, 40, 8], [-70, -44, 6], [70, -62, 9], [100, -62, 5], [100, 62, 8]]) cratePile(B, x, z, n, r);
  for (const [x, z] of [[-60, 58], [-58.6, 58], [-60, 59.2], [-46, 66], [-44.6, 66], [80, 66], [81.4, 66], [80, 67.2], [-82, 46], [-82, 47.2], [64, -58], [65.4, -58]]) pallets(B, x, z, 3 + ((x * 7 + z) & 3), r, true);
  forklift(B, -76, 52, 2, 1.6); forklift(B, 90, -60, 0);
  for (const [x, z, m] of [[-86, -36, 'containerr'], [-86, -62, 'containerb']]) add(x, 0, z, x + 2.5, 2.6, z + 12, m);
  // west yard: the gate (open, the sliding panel parked beside it) with a guard booth, a water tower to grapple
  waterTower(W, -76, 30, 0);
  const GB = B.local(-84, 10.9, 0); // the guard booth by the gate, a boom barrier (up: they gave up)
  shell(GB, 4, 3.4, 1, 2.8, 'toyteal', { roof: 'toyred', floor: 'tile', parapet: false });
  GB(-1.6, 0.12, 0.4, 1.6, 0.95, 1.4, 'wood'); GB.B(0.8, 1.2, 0.9, 0.7, 0.45, 0.1, 'tvstatic');
  add(-88, 0, 6.6, -87.4, 1.1, 7.2, 'hazard'); add(-87.78, 1.1, 6.83, -87.62, 5.1, 6.97, 'hazard');
  const SO = B.local(-80, -16, 1); // the site office: a portacabin
  shell(SO, 10, 4.2, 1, 3, 'containerb', { roof: 'roofg', floor: 'carpet', parapet: false });
  SO(-4, 3.3, -2.5, 4, 4.2, -2.25, 'adoffice', { fit: 1 }); SO(-1.2, 0, -3.2, 1.2, 0.12, -2.1, 'grid');
  SO(-4.5, 0.12, 0.6, -1.5, 0.85, 1.9, 'wood'); SO(1.5, 0.12, 0.6, 4.5, 0.85, 1.9, 'wood');
  adBoard(B, -124, 0, 0, 'z', 'adcity2', 26, 10); // JANK COLA, by the road, facing the gate
  adBoard(D, -128, -260, 0, 'z', 'adcity1', 22, 9); adBoard(D, -128, 300, 0, 'z', 'adcity3', 22, 9);
  for (const [x, z] of [[-70, -30], [-80, -50], [-74, 60]]) { add(x, 0, z, x + 2.6, 1.5, z + 1.6, 'containerg'); }
  // light masts
  for (const [x, z] of [[-84, -70], [134, -70], [-84, 70], [134, 70], [30, -70], [30, 70]]) { box(x, 7, z, 0.5, 14, 0.5, 'metal'); box(x, 14.2, z, 2.6, 0.5, 1, 'lamp'); }
  // the fence: chain link on posts with barbed wire on top, gate in the west side
  const fence = (x0, z0, x1, z1) => {
    const alongX = z0 === z1, len = alongX ? x1 - x0 : z1 - z0;
    if (alongX) add(x0, 0, z0 - 0.04, x1, 4.2, z0 + 0.04, 'fence'); else add(x0 - 0.04, 0, z0, x0 + 0.04, 4.2, z1, 'fence');
    for (let t = 0; t <= len + 0.01; t += 6) { const px = alongX ? x0 + t : x0, pz = alongX ? z0 : z0 + t; box(px, 2.25, pz, 0.14, 4.5, 0.14, 'metal'); }
    if (alongX) { D.add(x0, 4.5, z0 - 0.02, x1, 4.53, z0 + 0.02, 'tire'); D.add(x0, 4.75, z0 - 0.02, x1, 4.78, z0 + 0.02, 'tire'); }
    else { D.add(x0 - 0.02, 4.5, z0, x0 + 0.02, 4.53, z1, 'tire'); D.add(x0 - 0.02, 4.75, z0, x0 + 0.02, 4.78, z1, 'tire'); }
  };
  fence(FX0, -FZ, FX1, -FZ); fence(FX0, FZ, FX1, FZ); fence(FX1, -FZ, FX1, FZ);
  fence(FX0, -FZ, FX0, -6); fence(FX0, 6, FX0, FZ);
  add(FX0 - 0.3, 0, 6.2, FX0 - 0.15, 4.2, 18, 'fence'); // the sliding gate, open
  // the world outside (render-only): trees just outside the fence (none in the yard: it's a yard), then scattered ones
  const Dw = D.local(0, 0, 0);
  for (let x = FX0 + 4; x < FX1 + 8; x += 7) for (const z of [-FZ - 7, FZ + 7, -FZ - 15, FZ + 15]) if (r() < 0.8) (r() < 0.5 ? conifer : lollipop)(Dw, x + (r() - 0.5) * 3, z + (r() - 0.5) * 3, 5 + r() * 3, r);
  for (let z = -FZ - 10; z <= FZ + 10; z += 7) for (const x of [FX1 + 7, FX1 + 15]) if (r() < 0.8) (r() < 0.5 ? conifer : lollipop)(Dw, x + (r() - 0.5) * 3, z + (r() - 0.5) * 3, 5 + r() * 3, r);
  for (let z = -180; z <= 180; z += 8) if (Math.abs(z) > 12 && r() < 0.6) (r() < 0.5 ? conifer : lollipop)(Dw, RX0 - 8 - r() * 10, z, 5 + r() * 3, r); // across the road
  horizon(D, -230, -190, 260, 190, 1500, 'dirt');
  for (let i = 0; i < 50; i++) { const a = r() * Math.PI * 2, d = 120 + r() * 90; const x = 25 + Math.cos(a) * d * 1.2, z = Math.sin(a) * d; if (x > FX0 - 6 && x < FX1 + 6 && Math.abs(z) < FZ + 6) continue; (r() < 0.5 ? conifer : lollipop)(Dw, x, z, 6 + r() * 4, r); }
  const spawns = [[-52, 0.1, -34], [52, 0.1, 34], [-52, 0.1, 34], [52, 0.1, -34], [0, 0.1, -12], [0, 0.1, 12], [84, 0.1, 0], [-46, 0.2, 12],
    [-75, 0.1, 0], [-60, 0.2, -60], [10, 0.1, -58], [126, 0.1, -10], [10, 0.1, 66], [-46, 1.3, 42], [100, 0.1, 40], [-30, 7.4, -38.5]];
  let graph = null;
  const map = {
    name: 'Warehouse', size: 'large', boxes: B.boxes, deco: D.boxes, killY: -25, bounds, floorY: -27,
    sky: { top: 0x0a0a20, mid: 0x5a2a6a, bot: 0x050508, fog: 0x3a2448 }, fogNear: 70, fogFar: 300,
    spawns,
    // bots: a walk graph over the floor and the catwalks, joined by the two stairs
    get graph() {
      return graph || (graph = buildNav(B.boxes, { x0: bounds[0], z0: bounds[1], n: bounds[2] - bounds[0], cell: 1, levels: [0, 7.3], band: 0.5, keep: (x, z) => !outOfBounds(map, [x, 0, z]),
        stairs: [{ bot: [-22.5, 0, -27.5], top: [-22.5, 7.3, -38.5] }, { bot: [38.5, 0, 27.5], top: [38.5, 7.3, 38.5] }] }));
    },
  };
  return map;
}

// ------------------------------------------------------------ DESERT: big sand town split by a canyon
// ---- desert props (shared by Desert and Bazaar's outskirts)
function stall(L, x, z, rot, rv) { // a market stall: posts, a loud awning, a counter piled with goods, sometimes a rug
  const T = (lx, lz) => [[lx, lz], [-lz, lx], [-lx, -lz], [lz, -lx]][rot & 3];
  const P = (x0, y0, z0, x1, y1, z1, m, ex) => { const [ax, az] = T(x0, z0), [bx, bz] = T(x1, z1); L(x + ax, y0, z + az, x + bx, y1, z + bz, m, ex); };
  for (const [px, pz] of [[-1.9, -1.4], [1.7, -1.4], [-1.9, 1.2], [1.7, 1.2]]) P(px, 0, pz, px + 0.2, 2.9, pz + 0.2, 'wood');
  P(-2.3, 2.9, -1.8, 2.3, 3.05, 1.8, ['cloth', 'toypink', 'toyteal', 'toyyellow', 'leopard', 'camo'][(rv() * 6) | 0]);
  P(-1.6, 0, -1.0, 1.6, 0.95, -0.3, 'wood');
  const goods = ['toyorange', 'toygreen', 'toyred', 'pottery', 'shelfstock', 'cloth'];
  for (let i = 0; i < 4; i++) { const gx = -1.4 + i * 0.75, h = 0.2 + rv() * 0.35; P(gx, 0.95, -0.95, gx + 0.6, 0.95 + h, -0.4, goods[(rv() * goods.length) | 0]); }
  if (rv() < 0.6) P(-1.6, 0.6, 1.25, 1.6, 2.6, 1.3, ['leopard', 'camo', 'cloth', 'magenta'][(rv() * 4) | 0]); // a rug hung at the back
  if (rv() < 0.7) pot(L, x + T(2.6, -1.2)[0], z + T(2.6, -1.2)[1], 0.8 + rv() * 0.4);
}
function pot(L, x, z, s = 1) { // a big clay pot
  L.B(x, 0.25 * s, z, 0.7 * s, 0.5 * s, 0.7 * s, 'pottery'); L.B(x, 0.7 * s, z, 0.9 * s, 0.4 * s, 0.9 * s, 'pottery'); L.B(x, 1.02 * s, z, 0.45 * s, 0.25 * s, 0.45 * s, 'pottery');
}
function cart(L, x, z, alongX) { // a wooden hand cart, tipped forward on its handles
  if (alongX) { L(x - 1.2, 0.6, z - 0.8, x + 1.2, 1.3, z + 0.8, 'wood'); for (const s of [-1, 1]) L(x - 0.45, 0, z + s * 0.85 - 0.1, x + 0.45, 0.9, z + s * 0.85 + 0.1, 'tire'); L(x + 1.2, 0.3, z - 0.6, x + 2.6, 0.45, z - 0.45, 'wood'); L(x + 1.2, 0.3, z + 0.45, x + 2.6, 0.45, z + 0.6, 'wood'); }
  else { L(x - 0.8, 0.6, z - 1.2, x + 0.8, 1.3, z + 1.2, 'wood'); for (const s of [-1, 1]) L(x + s * 0.85 - 0.1, 0, z - 0.45, x + s * 0.85 + 0.1, 0.9, z + 0.45, 'tire'); L(x - 0.6, 0.3, z + 1.2, x - 0.45, 0.45, z + 2.6, 'wood'); L(x + 0.45, 0.3, z + 1.2, x + 0.6, 0.45, z + 2.6, 'wood'); }
  L(x - 0.6, 1.3, z - 0.6, x + 0.6, 1.8, z + 0.6, ['crate', 'pottery', 'cloth', 'toyorange'][Math.abs((x * 3 + z) | 0) % 4]);
}
function tent(L, x, z, c) { // a cloth tent on poles (the Bazaar camp's kind)
  L(x - 3, 0, z - 2, x + 3, 0.05, z + 2, 'cloth');
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) L.B(x + sx * 2.8, 1.4, z + sz * 1.8, 0.2, 2.8, 0.2, 'wood');
  L(x - 3.2, 2.8, z - 2.2, x + 3.2, 3.0, z + 2.2, c); L(x - 2.2, 3.0, z - 1.4, x + 2.2, 3.5, z + 1.4, c);
}
function palm(L, x, z, h, r) { // a palm: a trunk that leans a little as it goes up, a crown of fronds
  const lx = (r() - 0.5) * 0.5, lz = (r() - 0.5) * 0.5, n = Math.max(3, Math.round(h / 1.4));
  for (let i = 0; i < n; i++) L.B(x + lx * i, (i + 0.5) * (h / n), z + lz * i, 0.55 - i * 0.02, h / n + 0.02, 0.55 - i * 0.02, i % 2 ? 'wood' : 'plywood');
  const tx = x + lx * n, tz = z + lz * n;
  L.B(tx, h + 0.1, tz, 1.4, 0.6, 1.4, 'leaves');
  for (const [dx, dz] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { L.B(tx + dx * 1.9, h, tz + dz * 1.9, dx ? 3 : 0.9, 0.35, dz ? 3 : 0.9, 'leaves2'); L.B(tx + dx * 3.3, h - 0.5, tz + dz * 3.3, dx ? 1.4 : 0.8, 0.3, dz ? 1.4 : 0.8, 'leaves'); }
}
function camel(L, x, z, alongX) { // a very boxy camel. it judges you
  const B2 = (cx, cy, cz, sx, sy, sz, m) => (alongX ? L.B(x + cx, cy, z + cz, sx, sy, sz, m) : L.B(x + cz, cy, z + cx, sz, sy, sx, m));
  B2(0, 1.9, 0, 2.6, 1.0, 1.0, 'camel'); B2(0.1, 2.6, 0, 1.0, 0.5, 0.8, 'camel'); // body + hump
  for (const [lx, lz] of [[-1, -0.35], [-1, 0.35], [1, -0.35], [1, 0.35]]) B2(lx, 0.7, lz, 0.25, 1.4, 0.25, 'camel');
  B2(1.55, 2.5, 0, 0.35, 1.3, 0.35, 'camel'); B2(1.85, 3.15, 0, 0.8, 0.4, 0.4, 'camel'); // neck + head
  B2(2.2, 3.25, -0.21, 0.12, 0.12, 0.05, 'tire'); B2(2.2, 3.25, 0.21, 0.12, 0.12, 0.05, 'tire'); // eyes
  B2(0, 2.45, 0, 1.4, 0.12, 1.1, ['cloth', 'leopard', 'toypink'][Math.abs((x + z) | 0) % 3]); // a blanket
}
function dune(D, x, z, w, d, h) { // a dune: flattened layers of sand, smaller as they go up
  for (let i = 0; i < 4; i++) { const k = 1 - i * 0.24; D.box(x + i * w * 0.04, (h / 4) * (i + 0.5) - 0.05, z, w * k, h / 4, d * k, 'sand'); }
}
function rocks(D, x, z, s, r) { // a rock formation: a banded mesa with a few blocks stacked off it
  const h = s * (1.1 + r() * 0.8);
  D.box(x, h / 2, z, s * 1.6, h, s, 'rock');
  D.box(x + s * 0.2, h + s * 0.12, z - s * 0.1, s * 1.1, s * 0.24, s * 0.7, 'rock');
  if (r() < 0.6) D.box(x - s * 0.9, h * 0.3, z + s * 0.3, s * 0.7, h * 0.6, s * 0.7, 'rock');
  if (r() < 0.5) D.box(x + s * 1.1, h * 0.2, z - s * 0.4, s * 0.5, h * 0.4, s * 0.6, 'rock');
}

function desert() {
  const B = builder();
  const r = rng(909);
  const S = 100;
  B.add(-S, -2, -S, -7, 0, S, 'sand'); B.add(7, -2, -S, S, 0, S, 'sand');
  B.add(-S + 10, -10, -S + 10, -9, -2, S - 10, 'dirt'); B.add(9, -10, -S + 10, S - 10, -2, S - 10, 'dirt');
  for (const z of [-55, 0, 55]) { B.box(0, -0.25, z, 14, 0.5, 4.5, 'wood'); B.add(-7.1, 0, z - 2.25, 7.1, 1, z - 2.05, 'wood'); B.add(-7.1, 0, z + 2.05, 7.1, 1, z + 2.25, 'wood'); }
  // town walls
  for (const s of [-1, 1]) { B.add(-S, 0, s * S - 0.6, S, 9, s * S + 0.6, 'adobe'); B.add(s * S - 0.6, 0, -S, s * S + 0.6, 9, S, 'adobe'); }
  const spawns = [];
  // buildings: [x, z, rot, w, d, floors]
  const blds = [
    [-70, -70, 0, 16, 12, 2], [-42, -74, 0, 12, 10, 1], [-20, -66, 1, 14, 12, 3], [-75, -35, 1, 12, 14, 2], [-40, -30, 2, 18, 12, 2],
    [-70, 10, 1, 14, 12, 1], [-40, 26, 3, 16, 12, 3], [-72, 46, 0, 12, 12, 2], [-30, 70, 2, 18, 14, 2], [-62, 76, 2, 12, 10, 1],
    [70, 70, 2, 16, 12, 2], [42, 74, 2, 12, 10, 1], [20, 66, 3, 14, 12, 3], [75, 35, 3, 12, 14, 2], [40, 30, 0, 18, 12, 2],
    [70, -10, 3, 14, 12, 1], [40, -26, 1, 16, 12, 3], [72, -46, 2, 12, 12, 2], [30, -70, 0, 18, 14, 2], [62, -76, 0, 12, 10, 1],
  ];
  const roofs = [], D = builder(), rv = rng(9090); // rv: the look's own dice, so nothing you collide with moves
  for (const [x, z, rot, w, d, n] of blds) {
    const L = B.local(x, z, rot), Ld = D.local(x, z, rot);
    const paint = ['adobe', 'adobe', 'adobe', 'magenta', 'sideorange', 'sidemint', 'sidelemon'][(rv() * 7) | 0];
    const { top } = shell(L, w, d, n, 3.6, paint, { floor: 'wood', roof: 'adobe', roofAccess: true, backDoor: r() < 0.6 });
    L(-w / 2 - 0.5, 2.6, -d / 2 - 2.2, w / 2 + 0.5, 2.8, -d / 2, ['cloth', 'toypink', 'toyteal', 'toyyellow'][(rv() * 4) | 0]); // awning
    if (rv() < 0.5) Ld(-2.2, 2.95, -d / 2 - 0.4, 2.2, 3.75, -d / 2 - 0.16, ['neonbar', 'neonnoodle', 'neonhotel', 'neonwork'][(rv() * 4) | 0], { fit: 1 });
    if (n >= 2 && rv() < 0.4) adBoard(D, x, z, n * 3.6 + 0.3, rot % 2 ? 'z' : 'x', ['adcity1', 'adcity2', 'adcity3', 'adcity4', 'adcity5', 'adcity6'][(rv() * 6) | 0], 8, 3.5);
    L(-w / 2 - 0.3, 0, -d / 2 - 2.0, -w / 2, 2.6, -d / 2 - 1.8, 'wood'); L(w / 2, 0, -d / 2 - 2.0, w / 2 + 0.3, 2.6, -d / 2 - 1.8, 'wood');
    roofs.push({ x, z, top });
    spawns.push([x, 0.2, z]);
  }
  // planks between some neighbouring roofs
  for (let i = 0; i < roofs.length; i++) for (let j = i + 1; j < roofs.length; j++) {
    const a = roofs[i], b = roofs[j];
    if (Math.abs(a.top - b.top) > 0.1 || Math.hypot(a.x - b.x, a.z - b.z) > 34 || r() < 0.4) continue;
    const y = a.top + 0.85;
    if (Math.abs(a.x - b.x) > Math.abs(a.z - b.z)) B.add(Math.min(a.x, b.x) + 6, y, a.z - 0.9, Math.max(a.x, b.x) - 6, y + 0.3, a.z + 0.9, 'wood');
    else B.add(a.x - 0.9, y, Math.min(a.z, b.z) + 5, a.x + 0.9, y + 0.3, Math.max(a.z, b.z) - 5, 'wood');
  }
  // market square with stalls on each side
  for (const sx of [-1, 1]) {
    const M = B.local(sx * 36, 0, sx > 0 ? 3 : 1);
    for (let i = 0; i < 4; i++) {
      const cx = -12 + i * 8;
      for (const ox of [-2, 2]) for (const oz of [-1.5, 1.5]) M.B(cx + ox, 1.5, oz, 0.25, 3, 0.25, 'wood');
      M.B(cx, 3.1, 0, 5, 0.2, 4, ['cloth', 'toypink', 'toyteal', 'leopard'][i]);
      M.B(cx, 0.5, 0, 3.5, 1, 1.2, 'crate');
    }
    // water tower to grapple
    for (const ox of [-1.5, 1.5]) for (const oz of [-1.5, 1.5]) M.B(ox, 8, 20 + oz, 0.4, 16, 0.4, 'wood');
    M.B(0, 17, 20, 5, 4, 5, 'wood');
  }
  // palms
  for (let i = 0; i < 24; i++) {
    const x = (r() < 0.5 ? -1 : 1) * (14 + r() * 80), z = -90 + r() * 180;
    B.box(x, 3.5, z, 0.5, 7, 0.5, 'wood'); B.box(x, 7.3, z, 4, 0.5, 1, 'leaves'); B.box(x, 7.3, z, 1, 0.5, 4, 'leaves');
  }
  B.box(-12, 0.15, 26, 2.5, 0.3, 2.5, 'pad', { pad: [26, 18, 0] });
  B.box(12, 0.15, -26, 2.5, 0.3, 2.5, 'pad', { pad: [-26, 18, 0] });

  // ---- the town wall: gates east and west (a road runs through both), gate towers, corner towers, battlements
  for (const sx of [-1, 1]) {
    carve(B, sx * S - 1, 0, -6, sx * S + 1, 6, 6, (q) => q.mat === 'adobe' && q.min[0] < sx * S + 0.7 && q.max[0] > sx * S - 0.7 && q.max[2] - q.min[2] > 100);
    for (const sz of [-1, 1]) B.add(sx * S - 3, 0, sz > 0 ? 6.5 : -10.5, sx * S + 3, 12, sz > 0 ? 10.5 : -6.5, 'adobe');
    for (const sz of [-1, 1]) B.box(sx * S, 6.75, sz * S, 7, 13.5, 7, 'adobe');
  }
  for (let t = -S + 6; t <= S - 6; t += 3) { // merlons on the outer edge of the wall top
    for (const sz of [-1, 1]) B.add(t - 0.6, 9, sz * (S + 0.6) - (sz > 0 ? 0.5 : 0), t + 0.6, 10, sz * (S + 0.6) + (sz > 0 ? 0 : 0.5), 'adobe');
    if (Math.abs(t) > 12) for (const sx of [-1, 1]) B.add(sx * (S + 0.6) - (sx > 0 ? 0.5 : 0), 9, t - 0.6, sx * (S + 0.6) + (sx > 0 ? 0 : 0.5), 10, t + 0.6, 'adobe');
  }
  // ---- outside: sand all the way out (no cliff), the canyon running on as a ravine with a river at the bottom
  groundHoles(B, -300, -300, 300, 300, -2, 0, 'sand', [[-S, -S, S, S], [-7, -284, 7, -S], [-7, S, 7, 284]]);
  D.add(-9, -46, -284, -7, -2, 284, 'rock'); D.add(7, -46, -284, 9, -2, 284, 'rock');
  for (const sz of [-1, 1]) D.add(-9, -46, sz > 0 ? 284 : -288, 9, -2, sz > 0 ? 288 : -284, 'rock');
  D.add(-7, -47, -284, 7, -46, 284, 'sand'); D.add(-3.5, -46, -284, 3.5, -45.8, 284, 'water');
  for (const z of [-180, -40, 20, 130, 220]) D.add(-5 + rv() * 3, -45.8, z, -1 + rv() * 3, -44.6 + rv(), z + 2 + rv() * 3, 'rock');
  D.add(-4, -45.8, 66, 4, -45.3, 68.5, 'wood'); // somebody's old bridge
  // ---- dirt roads: one through both gates and over the middle bridge, two over the other bridges, two north-south
  B.add(-300, 0, -3, -7, 0.03, 3, 'dirtroad'); B.add(7, 0, -3, 300, 0.03, 3, 'dirtroad');
  for (const sx of [-1, 1]) D.add(sx > 0 ? 300 : -760, 0, -3, sx > 0 ? 760 : -300, 0.03, 3, 'dirtroad');
  for (const z of [-55, 55]) { B.add(-95, 0, z - 3, -7, 0.03, z + 3, 'dirtroad'); B.add(7, 0, z - 3, 95, 0.03, z + 3, 'dirtroad'); }
  for (const x of [-54, 54]) B.add(x - 3, 0, -60, x + 3, 0.045, 60, 'dirtroad');
  // ---- markets along the road by both gates, a camp by the north wall, clutter everywhere
  const W = B.local(0, 0, 0);
  for (const x of [-92, -85, -78, -71]) stall(W, x, -6, 2, rv);
  for (const x of [-92, -85]) stall(W, x, 6, 0, rv);
  for (const x of [85, 92]) stall(W, x, -6, 2, rv);
  for (const x of [64, 71, 78, 85, 92]) stall(W, x, 6, 0, rv);
  for (const [x, z, c] of [[-20, -92, 'cloth'], [-12, -92, 'toypink'], [16, 92, 'toyteal'], [24, 92, 'cloth']]) tent(W, x, z, c);
  for (const [x, z] of [[-96, -14], [-96, 14], [96, 14], [-96, 40], [96, -40], [-60, 96], [60, -96], [-30, 96], [30, -96], [-97, -70], [97, 70], [-48, -4], [48, 4]]) pot(W, x, z, 0.8 + rv() * 0.5);
  for (const [x, z, ax] of [[-66, -5.5, true], [78.5, -5.5, true], [-58, 30, false], [58, -30, false], [-15, 40, true]]) cart(W, x, z, ax);
  for (const [x, z, n] of [[-95, -30, 6], [92, 22, 7], [-30, -95, 5], [40, 95, 6]]) cratePile(B, x, z, n, rv);
  for (const [x, z] of [[-90, -12], [-90, 12], [90, -12], [90, 12], [-54, -64], [-54, 64], [54, -64], [54, 64], [-25, 3.8], [25, -3.8]]) palm(W, x, z, 6 + rv() * 3, rv);
  // ---- the desert round the town (render-only): dunes, rock formations, a caravan camped outside the east gate, more palms
  const Dw = D.local(0, 0, 0);
  for (let i = 0; i < 46; i++) { const a = rv() * Math.PI * 2, d = 130 + rv() * 230, x = Math.cos(a) * d, z = Math.sin(a) * d; if (Math.abs(x) < 26 || Math.abs(z) < 14) continue; dune(D, x, z, 30 + rv() * 60, 18 + rv() * 36, 5 + rv() * 12); }
  for (let i = 0; i < 16; i++) { const a = rv() * Math.PI * 2, d = 190 + rv() * 220, x = Math.cos(a) * d, z = Math.sin(a) * d; if (Math.abs(x) < 30 || Math.abs(z) < 20) continue; rocks(D, x, z, 12 + rv() * 20, rv); }
  for (const [x, z, c] of [[124, -14, 'cloth'], [134, 10, 'toyyellow'], [146, -6, 'leopard']]) tent(Dw, x, z, c);
  for (const [x, z, ax] of [[118, 18, true], [128, 22, false], [142, 16, true], [152, 0, false]]) camel(Dw, x, z, ax);
  Dw(132, 0, -2, 134, 0.4, 0, 'stone'); Dw(132.5, 0.4, -1.5, 133.5, 1.0, -0.5, 'neonred'); // the campfire
  for (let i = 0; i < 30; i++) { const a = rv() * Math.PI * 2, d = 110 + rv() * 120, x = Math.cos(a) * d, z = Math.sin(a) * d; if (Math.abs(x) < 20 || Math.abs(z) < 10) continue; palm(Dw, x, z, 6 + rv() * 4, rv); }
  D.add(-260, 0, -210, -230, 26, -180, 'toyface', { fit: 1 }); // something enormous, half buried, smiling
  horizon(D, -300, -300, 300, 300, 1500, 'sand');

  const bounds = [-S - 1, -S - 1, S + 1, S + 1];
  let graph = null;
  const map = { name: 'Desert', size: 'large', boxes: B.boxes, deco: D.boxes, killY: -30, bounds, floorY: -49,
    sky: { top: 0x3f7fd0, mid: 0xf2d9a0, bot: 0x6a4a28, fog: 0xead6a6 }, fogNear: 130, fogFar: 520, spawns,
    // bots: a walk graph over the town (1 m cells), across the bridges, round the stalls
    get graph() { return graph || (graph = buildNav(B.boxes, { x0: bounds[0], z0: bounds[1], n: bounds[2] - bounds[0], cell: 1, levels: [0], band: 0.5, keep: (x, z) => !outOfBounds(map, [x, 0, z]) })); },
  };
  return map;
}

// ------------------------------------------------------------ ISLANDS: large, the original
function islands() {
  const { boxes, box } = builder();
  box(0, -2, 0, 64, 4, 64, 'grass');
  box(0, -7, 0, 46, 6, 46, 'dirt');
  box(0, -12.5, 0, 26, 5, 26, 'dirt');
  box(0, -17, 0, 10, 4, 10, 'dirt');
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
    box(22 * sx, 9, 22 * sz, 4, 18, 4, 'stone');
    box(22 * sx, 18.5, 22 * sz, 9, 1, 9, 'wood');
  }
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) box(6 * sx, 2.5, 6 * sz, 1, 5, 1, 'wood');
  box(0, 5.5, 0, 14, 1, 14, 'missing');
  box(0, 0.75, -6, 8, 1.5, 0.5, 'wood');
  box(0, 0.75, 6, 8, 1.5, 0.5, 'wood');
  box(2, 0.6, 1, 1.2, 1.2, 1.2, 'crate');
  box(14, 1, 4, 2, 2, 2, 'crate');
  box(15.6, 0.5, 6.2, 1, 1, 1, 'crate');
  box(-13, 1, -9, 3, 2, 3, 'crate');
  box(9, 1.5, -17, 7, 3, 1, 'stone');
  box(-9, 1.5, 17, 1, 3, 7, 'stone');
  box(-18, 1, 5, 2, 2, 2, 'crate');
  box(19, 1, -12, 2, 2, 2, 'crate');
  box(5, 0.5, 14, 1, 1, 1, 'crate');
  box(-4, 0.5, -20, 1, 1, 1, 'crate');
  box(0, 0.15, 27, 3.5, 0.3, 3.5, 'pad', { pad: [0, 26, 26] });
  box(0, 0.15, -27, 3.5, 0.3, 3.5, 'pad', { pad: [0, 26, -26] });
  box(27, 0.15, 0, 3.5, 0.3, 3.5, 'pad', { pad: [26, 26, 0] });
  box(-27, 0.15, 0, 3.5, 0.3, 3.5, 'pad', { pad: [-26, 26, 0] });
  box(0, 0.15, -13, 3, 0.3, 3, 'pad', { pad: [0, 44, 0] });
  box(0, -2, -88, 36, 4, 36, 'grass');
  box(0, -7, -88, 24, 6, 24, 'dirt');
  box(-6, 4, -88, 1.5, 8, 1.5, 'stone');
  box(6, 4, -88, 1.5, 8, 1.5, 'stone');
  box(0, 8.5, -88, 14, 1, 1.5, 'stone');
  box(8, 1, -80, 2, 2, 2, 'crate');
  box(-9, 1, -95, 2, 2, 2, 'crate');
  box(0, 0.15, -73, 3.5, 0.3, 3.5, 'pad', { pad: [0, 26, 26] });
  box(0, -2, 88, 36, 4, 36, 'grass');
  box(0, -7, 88, 24, 6, 24, 'dirt');
  box(0, 0.25, 88, 12, 0.5, 12, 'stone');
  box(0, 0.75, 88, 9, 0.5, 9, 'stone');
  box(0, 1.25, 88, 6, 0.5, 6, 'stone');
  box(0, 1.75, 88, 3, 0.5, 3, 'gold');
  box(0, 0.15, 73, 3.5, 0.3, 3.5, 'pad', { pad: [0, 26, -26] });
  box(0, -0.25, 51, 2, 0.5, 38, 'wood');
  box(88, -2, 0, 36, 4, 36, 'grass');
  box(88, -7, 0, 24, 6, 24, 'dirt');
  box(88, 14, 0, 4, 28, 4, 'stone');
  box(88, 28.5, 0, 7, 1, 7, 'wood');
  box(80, 1, 9, 2, 2, 2, 'crate');
  box(73, 0.15, 0, 3.5, 0.3, 3.5, 'pad', { pad: [-26, 26, 0] });
  box(-88, -2, 0, 36, 4, 36, 'grass');
  box(-88, -7, 0, 24, 6, 24, 'dirt');
  box(-88, 6, 0, 2, 12, 6, 'missing');
  box(-80, 1, -9, 2, 2, 2, 'crate');
  box(-73, 0.15, 0, 3.5, 0.3, 3.5, 'pad', { pad: [26, 26, 0] });
  for (let i = 0; i < 8; i++) {
    const a = (i / 8) * Math.PI * 2 + Math.PI / 8;
    box(Math.cos(a) * 48, 30 + (i % 2) * 9, Math.sin(a) * 48, 4, 2, 4, i % 2 ? 'toypink' : 'toyteal');
  }
  box(0, 42, 0, 12, 1.5, 12, 'missing');
  box(0, 70, 0, 5, 2, 5, 'gold');
  box(60, 55, -60, 6, 2, 6, 'toypink');
  box(-60, 55, 60, 6, 2, 6, 'toypink');
  const D = builder(); D.add(140, 60, -260, 200, 120, -200, 'toyface', { fit: 1 }); // the sun has a face now
  // the islands are sea stacks: rock columns rising out of the ocean, surf round their feet (render-only)
  const stack = (x, z, w, top) => { D.box(x, (top - 44) / 2, z, w, top + 44, w, 'rock'); D.box(x + w * 0.1, -36.5, z - w * 0.08, w * 1.35, 15, w * 1.3, 'rock'); D.box(x, -41.9, z, w * 1.5, 0.3, w * 1.45, 'white'); };
  stack(0, 0, 22, -19); stack(0, -88, 18, -10); stack(0, 88, 18, -10); stack(88, 0, 18, -10); stack(-88, 0, 18, -10);
  for (let i = 0; i < 9; i++) { const a = (i / 9) * Math.PI * 2 + 0.3, d = 130 + (i % 3) * 40; D.box(Math.cos(a) * d, -30 + (i % 2) * 8, Math.sin(a) * d, 8 + (i % 3) * 4, 28 + (i % 2) * 16, 8 + (i % 2) * 5, 'rock'); } // lonely rocks offshore
  return { name: 'Islands', size: 'large', boxes, deco: D.boxes, killY: -45, floorY: -42, sky: SKY_SUNSET, fogNear: 90, fogFar: 330,
    spawns: [[10, 0.1, 10], [-10, 0.1, -10], [10, 0.1, -10], [-10, 0.1, 10], [8, 0.1, -88], [8, 0.1, 82], [88, 0.1, 8], [-88, 0.1, 8]] };
}

// ------------------------------------------------------------ SKYLINE: huge, a real downtown of skyscrapers
function skyline() {
  const B = builder();
  const r = rng(1337);
  const base = -120;
  // [x, z, w, d, height, tiers, roof]
  const plan = [
    [-100, -100, 30, 30, 60, 2, 'tank'], [-35, -100, 34, 30, 96, 3, 'antenna'], [100, -100, 28, 28, 50, 1, 'ac'],
    [-100, -35, 32, 32, 75, 2, 'billboard'], [-35, -35, 30, 30, 55, 1, 'helipad'], [35, -35, 30, 30, 55, 1, 'ac'], [100, -35, 30, 30, 110, 3, 'antenna'],
    [-100, 35, 34, 34, 45, 1, 'garden'], [-35, 35, 30, 30, 80, 2, 'tank'], [35, 35, 36, 36, 65, 2, 'helipad'], [100, 35, 30, 30, 65, 1, 'billboard'],
    [-100, 100, 28, 28, 100, 3, 'antenna'], [-35, 100, 32, 32, 50, 1, 'garden'], [35, 100, 30, 30, 85, 2, 'ac'], [100, 100, 34, 34, 40, 1, 'tank'],
  ];
  const spawns = [];
  const roofs = {};
  for (const [x, z, w, d, h, tiers, roof] of plan) {
    const ry = tower(B, x, z, w, d, h, { base, tiers, roof, r, pad: r() < 0.5 ? [(r() - 0.5) * 40, 30, (r() - 0.5) * 40] : null });
    roofs[`${x},${z}`] = ry;
    spawns.push([x + 4, ry + 0.1, z + 4]);
  }
  // construction site: open floors, columns, a crane
  {
    const cx = 35, cz = -100, w = 30, F = 4.5;
    B.box(cx, (base + 0) / 2, cz, w, 0 - base, w, 'concrete');
    for (let f = 0; f < 12; f++) {
      const y = f * F;
      if (f % 4 !== 3) B.box(cx, y + 0.25, cz, w, 0.5, w, 'concrete');
      else { B.add(cx - w / 2, y, cz - w / 2, cx + 4, y + 0.5, cz + w / 2, 'concrete'); } // some floors only half done
      for (const ox of [-w / 2 + 0.5, 0, w / 2 - 0.5]) for (const oz of [-w / 2 + 0.5, 0, w / 2 - 0.5]) B.box(cx + ox, y + 0.5 + (F - 0.5) / 2, cz + oz, 0.8, F - 0.5, 0.8, 'metal');
      if (f % 2 === 0) B.add(cx - w / 2, y + 0.5, cz - w / 2, cx + w / 2, y + 1.6, cz - w / 2 + 0.2, 'hazard');
    }
    // stairs up the open floors along one edge
    const L = B.local(cx, cz, 0);
    for (let f = 0; f < 11; f++) {
      const y = f * F + 0.5;
      if (f % 2 === 0) stairs(L, w / 2 - 3, w / 2 - 1, -8, 1, y, y + F, 'grid', 0.5);
      else stairs(L, w / 2 - 6, w / 2 - 4, 2, -1, y, y + F, 'grid', 0.5);
    }
    roofs[`${cx},${cz}`] = 11 * F + 0.5;
    // crane
    B.box(cx - 8, 11 * F + 20, cz - 8, 2, 40, 2, 'hazard');
    B.box(cx - 8 + 12, 11 * F + 40.5, cz - 8, 50, 1.2, 1.6, 'hazard');
    B.box(cx - 8 - 12, 11 * F + 39, cz - 8, 6, 3, 3, 'concrete');
    B.box(cx - 8 + 30, 11 * F + 34, cz - 8, 0.2, 12, 0.2, 'metal');
    B.box(cx - 8 + 30, 11 * F + 27.5, cz - 8, 3, 1, 3, 'pink');
    spawns.push([cx + 5, 0.6, cz + 5], [cx + 5, 4 * F + 0.6, cz + 5]); // (the first one used to be inside the middle column)
  }
  // sky bridges between equal-height neighbours (enclosed glass tubes), roof edge to roof edge, with a doorway cut
  // through the parapet at both ends. ax/bx: where each roof's edge really is (the top tier, not the base: one of them
  // used to start at the lower tier's edge and stick out 4 m into the air past the roof it was meant to reach)
  const edge = (w, tiers) => Math.max(10, w - 8 * (tiers - 1)) / 2 + 0.4;
  const bridge = (ta, tb, z, y) => {
    const ax = ta[0] + edge(ta[2], ta[5]), bx = tb[0] - edge(tb[2], tb[5]);
    B.add(ax, y - 0.3, z - 2, bx, y, z + 2, 'concrete');
    B.add(ax, y, z - 2, bx, y + 2.6, z - 1.8, 'glassblock'); B.add(ax, y, z + 1.8, bx, y + 2.6, z + 2, 'glassblock');
    B.add(ax, y + 2.6, z - 2, bx, y + 2.9, z + 2, 'roofg');
    B.add(ax, y + 2.3, z - 1.8, bx, y + 2.4, z - 1.7, 'neoncyan'); B.add(ax, y + 2.3, z + 1.7, bx, y + 2.4, z + 1.8, 'neoncyan');
    for (const x of [ax, bx]) carve(B, x - 1, y + 0.001, z - 1.8, x + 0.001, y + 1.2, z + 1.8, (q) => q.mat === 'concrete' && q.min[1] >= y - 0.01);
  };
  const T = (x, z) => plan.find((q) => q[0] === x && q[1] === z);
  bridge(T(-35, -35), T(35, -35), -35, roofs['-35,-35']);
  bridge(T(35, 35), T(100, 35), 35, roofs['35,35']);
  // window washer platforms and ledges to grapple
  for (let i = 0; i < 18; i++) {
    const [x, z, w, d, h] = plan[(r() * plan.length) | 0];
    const side = (r() * 4) | 0, y = base + 60 + r() * (h - base - 70);
    const off = [[0, -d / 2 - 1], [0, d / 2 + 1], [-w / 2 - 1, 0], [w / 2 + 1, 0]][side];
    B.box(x + off[0], y, z + off[1], side < 2 ? 6 : 1.6, 0.4, side < 2 ? 1.6 : 6, 'metal');
  }
  for (let k = 0; k < 10; k++) B.box((r() - 0.5) * 300, 140 + r() * 40, (r() - 0.5) * 300, 5, 1.5, 5, 'gold');
  // ---- the look (all render-only): the street far below, a neon band round every crown, cables with ads between towers
  const D = builder(), towers = [...plan.map(([x, z, w, d]) => ({ x, z, w, d })), { x: 35, z: -100, w: 30, d: 30 }];
  streetLevel(D, -100, towers, { xs: [-135, -67.5, 0, 67.5, 135], zs: [-135, -67.5, 0, 67.5, 135], w: 18 }, 190, r);
  cityDress(D, plan, roofs, base, r);
  cityBeyond(D, -100, 190, 680, rng(4040), { kill: -88, cap: 30, shore: 470, avenues: [[-60, -230, 0.42], [230, 40, -1.05], [-300, 120, 1.25], [80, -420, 0.06], [-250, -250, 2.35]] });
  return { name: 'Skyline', size: 'huge', boxes: B.boxes, deco: D.boxes, killY: -88, floorY: -108, cityR: 680, cityCap: 30,
    sky: { top: 0x1a2a5a, mid: 0xff9a5a, bot: 0x0a0a1a, fog: 0xd98a6a }, fogNear: 160, fogFar: 700, spawns };
}

// ------------------------------------------------------------ RANGE: training room
// ground slab with rectangular holes cut out (stairwells, canals). holes: [x0, z0, x1, z1]
function groundHoles(B, x0, z0, x1, z1, y0, y1, mat, holes) {
  const uniq = (a) => [...new Set(a)].sort((p, q) => p - q);
  const xs = uniq([x0, x1, ...holes.flatMap((h) => [h[0], h[2]])].filter((v) => v >= x0 && v <= x1));
  const zs = uniq([z0, z1, ...holes.flatMap((h) => [h[1], h[3]])].filter((v) => v >= z0 && v <= z1));
  const inHole = (x, z) => holes.some((h) => x > h[0] && x < h[2] && z > h[1] && z < h[3]);
  for (let i = 0; i < xs.length - 1; i++) {
    let start = null;
    for (let j = 0; j <= zs.length - 1; j++) {
      const open = j < zs.length - 1 && !inHole((xs[i] + xs[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2);
      if (open && start === null) start = zs[j];
      if (!open && start !== null) { B.add(xs[i], y0, start, xs[i + 1], y1, zs[j], mat); start = null; }
    }
  }
}

// ------------------------------------------------------------ BAZAAR: plant & defuse. original layout built on the
// classic bomb-map rules: three lanes (a long street to A, a covered market hall in the middle, an underground cistern to B),
// defenders spawn ~2.5x closer to both sites than attackers, every lane ends in a chokepoint, sites have 3 ways in for retakes,
// sightlines go long (canal street) / mixed (hall) / close (cistern), and each site has its own colours as a landmark.
function bazaar() {
  const B = builder();
  const W = B.local(0, 0, 0);
  const r = rng(777);
  const X0 = -64, X1 = 57, Z0 = -76, Z1 = 76;
  // ground (with the two cistern stairwells and the canal cut out) + the void below it
  groundHoles(B, X0, Z0, X1, Z1, -0.4, 0, 'sand', [[-46, 52, -40, 56], [-50, -8, -42, -4], [50, -6, 56, 70]]);
  // boundary walls
  B.add(X0 - 1, -4, Z0 - 1, X0, 12, Z1 + 1, 'adobe'); B.add(X1, -4, Z0 - 1, X1 + 1, 12, Z1 + 1, 'adobe');
  B.add(X0, -4, Z0 - 1, X1, 12, Z0, 'adobe'); B.add(X0, -4, Z1, X1, 12, Z1 + 1, 'adobe');
  const block = (x0, z0, x1, z1, h, mat = 'adobe') => { B.add(x0, 0, z0, x1, h, z1, mat); B.add(x0 + 0.4, h, z0 + 0.4, x1 - 0.4, h + 0.5, z1 - 0.4, 'roof'); };

  // ---- attacker spawn (south): an encampment with three exits (west -> cistern, north -> hall, east -> canal street)
  wall(W, 'x', 52, -22, 22, 0, 8, 0.8, 'adobe', [{ a: -6, b: 6, y0: 0, y1: 4.5 }]);
  wall(W, 'z', -22, 52, 76, 0, 8, 0.8, 'adobe', [{ a: 58, b: 66, y0: 0, y1: 4 }]);
  wall(W, 'z', 22, 52, 76, 0, 8, 0.8, 'adobe', [{ a: 58, b: 66, y0: 0, y1: 4 }]);
  for (const [x, z, c] of [[-14, 70, 'cloth'], [14, 70, 'cloth'], [0, 73, 'pink']]) { // tents
    B.add(x - 3, 0, z - 2, x + 3, 0.1, z + 2, 'cloth');
    for (const sx of [-1, 1]) for (const sz of [-1, 1]) B.box(x + sx * 2.8, 1.4, z + sz * 1.8, 0.2, 2.8, 0.2, 'wood');
    B.add(x - 3.2, 2.8, z - 2.2, x + 3.2, 3.0, z + 2.2, c);
  }
  B.box(-10, 0.6, 60, 1.2, 1.2, 1.2, 'crate'); B.box(10, 0.6, 61, 1.2, 1.2, 1.2, 'crate'); B.box(10, 1.8, 61, 1.1, 1.1, 1.1, 'crate');
  // ---- west corridor -> cistern stairs
  block(-40, 52, -22, 56, 8); block(-46, 66, -22, 76, 9); block(X0, 52, -46, 76, 9);
  // ---- east corridor -> canal street
  block(22, 52, 34, 58, 8); block(22, 66, 34, 70, 9); block(22, 70, X1, 76, 9);

  // ---- MID: the market hall (covered, stalls for cover, banners that hide your head but not your feet)
  block(X0, -2, -9, 52, 8, 'adobe');
  block(9, -2, 34, 52, 8, 'adobe');
  for (const [z0, z1] of [[-2, 8], [13, 28], [33, 52]]) B.add(-9, 7, z0, 9, 7.4, z1, 'roofg'); // roof with two skylights
  for (let z = 4; z < 48; z += 8) {
    for (const sx of [-1, 1]) { // stalls along both walls
      const x = sx * 6.5;
      B.add(x - 2, 0, z - 1.5, x + 2, 1.1, z + 1.5, 'wood');
      for (const dz of [-1.4, 1.4]) B.box(x + sx * -1.8, 1.5, z + dz, 0.15, 3, 0.15, 'wood');
      // awning high enough (counter + 1.9) that you can jump onto the counter and walk over it, under the gallery (3.15)
      B.add(x - 2.4, 3, z - 1.9, x + 2.4, 3.1, z + 1.9, (z / 8) % 2 ? 'cloth' : 'pink');
    }
  }
  for (const z of [18, 38]) B.add(-4, 3.2, z - 0.05, 4, 7, z + 0.05, 'cloth'); // hanging banners
  // upper mid: a wooden gallery along the west wall, over the stalls, so mid fights on two levels
  stairs(W, -9, -7, -1.5, 1, 0, 3.4, 'wood', 0.5);
  B.add(-9, 3.15, 2.5, -6.6, 3.4, 46, 'wood');
  for (const [z0, z1] of [[2.5, 14], [18, 30], [34, 46]]) B.add(-6.6, 3.4, z0, -6.4, 4.3, z1, 'wood'); // railing with gaps to drop
  B.box(0, 0.5, 26, 2, 1, 1.2, 'crate');

  // ---- mid plaza: the hall opens here. east = stairs up to the Bridge (rooftop over A's approach),
  // west = the Spice House (door through to B), north = the narrow passage to the defenders
  B.box(0, 0.4, -12, 3, 0.8, 3, 'stone'); B.box(0, 1.5, -12, 1, 1.4, 1, 'stone'); // a well
  stairs(W, 16, 20, -4, -1, 0, 3.4, 'adobe', 0.55);
  B.add(16, 0, -16, 20, 3.4, -8.4, 'adobe'); // landing
  // Stable: its roof is the Bridge
  B.add(20, 0, -30, 34, 3.4, -2, 'adobe');
  B.add(20, 3.4, -30, 34, 4.4, -29.6, 'adobe'); B.add(20, 3.4, -2.4, 34, 4.4, -2, 'adobe');
  B.add(20, 3.4, -29.6, 20.4, 4.4, -22, 'adobe'); B.add(20, 3.4, -8.4, 20.4, 4.4, -2.4, 'adobe');
  // the plaza corner north of the landing climbs onto the Bridge too (it was a dead end that walled in anyone heading for the roof)
  for (let i = 0; i < 8; i++) B.add(16 + i * 0.5, 0, -22, 16.5 + i * 0.5, (i + 1) * 0.425, -16, 'adobe');
  B.add(33.6, 3.4, -26, 34, 4.4, -2.4, 'adobe'); // east parapet, gap at the A end so you can drop onto the terrace
  for (const z of [-24, -18, -12, -6]) B.box(27, 3.4 + 0.5, z, 1.2, 1, 1.2, 'crate');
  // a crate staircase in A's approach: hop up and over the parapet onto the Bridge
  B.add(37.4, 0, -15, 38.6, 1.2, -13.8, 'crate');
  B.add(36.2, 0, -15, 37.4, 2.4, -13.8, 'crate');
  B.add(34, 0, -15, 36.2, 3.6, -13.8, 'crate');

  // ---- A LONG: Canal Street. long sightline, a sunken canal you can drop into as a lower lane
  B.add(50, -1.6, -6, 56, -1.2, 70, 'water');
  B.add(49.6, -1.2, -6, 50, -0.4, 70, 'adobe');
  B.add(50, -1.6, -6.5, 56, -0.4, -6, 'adobe'); B.add(50, -1.6, 70, 56, -0.4, 70.4, 'adobe');
  for (const z of [44, 14]) stairs(W, 50, 52.2, z, 1, -1.2, 0, 'stone', 0.6);
  for (const [x, z, s2] of [[38, 44, 2], [44, 26, 2], [38, 8, 1.6]]) { B.box(x, s2 / 2, z, s2, s2, s2, 'crate'); }
  B.box(44, 2.4, 26, 1.4, 1.4, 1.4, 'crate');
  for (const [x, z] of [[36, 60], [47, 30], [36, 2]]) tree(W, x, z, 5 + r() * 1.5);
  // upper long: a walkway along the west wall, stairs up at the south end, drop off at the north end
  stairs(W, 34.2, 36.8, 44.4, -1, 0, 3.2, 'wood', 0.5);
  B.add(34, 2.95, 10, 37, 3.2, 40.8, 'wood');
  B.add(36.8, 3.2, 10, 37, 4.1, 40.8, 'wood'); // rail
  for (let z = 12; z <= 40; z += 7) B.box(36.6, 1.5, z, 0.3, 2.95, 0.3, 'wood');
  B.add(34, 3.2, 9.8, 37, 4.1, 10, 'wood');
  // the Gate: chokepoint into A, with a hole up high you can jump through (sill 1.2 = one jump from A's side,
  // 2.2 tall so you fit on the 1 m sill). from the canal you get up via the crate standing in the water under it
  wall(W, 'x', -6, 34, 56, 0, 6, 1, 'brick', [{ a: 40, b: 46, y0: 0, y1: 4 }, { a: 51, b: 53.5, y0: 1.2, y1: 3.4 }]);
  B.add(51.1, -1.6, -5.5, 53.4, 0, -4.2, 'crate');

  // ---- SITE A: the terrace. raised, tiled, orange canopies. ways in: gate ramp (south), Bridge drop (west), garden stairs (north)
  B.add(34, 0, -50, 56, 1.6, -28, 'tile');
  stairs(W, 44, 50, -24, -1, 0, 1.6, 'adobe', 1.0);
  stairs(W, 36, 42, -54, 1, 0, 1.6, 'adobe', 1.0);
  B.box(40, 2.6, -36, 2, 2, 2, 'crate'); B.box(50, 2.6, -44, 2, 2, 2, 'crate'); B.box(50, 4.4, -44, 1.6, 1.6, 1.6, 'crate');
  B.add(45, 1.6, -33, 50, 2.6, -32, 'sand'); // sandbags
  for (const [x, z] of [[44, -48], [54, -48], [44, -40], [54, -40]]) B.box(x, 3.5, z, 0.3, 3.8, 0.3, 'wood');
  B.add(43.5, 5.4, -48.5, 54.5, 5.6, -39.5, 'pink'); // canopy
  B.add(56 - 0.3, 1.6, -50, 56, 4.5, -28, 'yellow'); // painted wall: A is warm

  // ---- defender garden east (CT side of A)
  block(3, -58, 20, -22, 7);
  block(20, -50, 34, -30, 7);
  block(20, Z0, X1, -66, 9);
  for (const x of [26, 46]) tree(W, x, -60, 5);
  B.box(30, 0.5, -55, 3, 1, 1, 'hedge');

  // ---- defender spawn (north): palace plaza
  for (const x of [-14, -7, 7, 14]) B.box(x, 3, -74.5, 1.2, 6, 1.2, 'stone'); // colonnade on the palace front
  B.add(-16, 6, -76, 16, 7, -73, 'stone');
  B.box(0, 0.4, -67, 4, 0.8, 4, 'stone'); B.box(0, 2.4, -67, 1.2, 3.2, 1.2, 'gold'); // statue

  // ---- west: garden + SITE B (fountain court, blue walls, an arcade along the north side)
  block(X0, Z0, -20, -66, 9);
  block(-20, -58, -3, -22, 7);
  block(-30, -52, -20, -30.2, 7);
  for (let x = -62; x <= -34; x += 4) B.box(x, 2.5, -53, 0.9, 5, 0.9, 'stone');
  B.add(-63, 5, -55, -33, 5.6, -51, 'roof');
  for (const [x, h] of [[-61.6, 1.2], [-61.6, 2.4], [-61.6, 3.6], [-61.6, 4.8]]) B.add(x - 0.6, 0, -56 - h * 0.85 - 0.6, x + 0.6, h, -56 - h * 0.85 + 0.6, 'crate');
  B.add(-63.7, 0, -52, -30, 0.05, -24, 'stone'); // paving
  // fountain (octagon-ish basin), the middle of B
  const fx = -46, fz = -38;
  for (let i = 0; i < 8; i++) { const a = (i / 8) * Math.PI * 2; B.box(fx + Math.cos(a) * 3, 0.45, fz + Math.sin(a) * 3, 2.6, 0.8, 2.6, 'stone'); }
  B.add(fx - 2, 0.05, fz - 2, fx + 2, 0.5, fz + 2, 'water');
  B.box(fx, 1.6, fz, 0.8, 2.2, 0.8, 'stone');
  B.box(-56, 0.6, -46, 1.2, 1.2, 1.2, 'crate'); B.box(-36, 0.6, -32, 2, 1.2, 1.2, 'crate'); B.box(-38, 1.6, -45, 2.4, 3.2, 1.2, 'wood');
  B.add(-64, 0, -52, -63.7, 6, -24, 'blue'); // painted wall: B is cool

  // ---- the Spice House: two floors between mid plaza and B. door from the plaza, a door onto B with the balcony door right above it
  const SX0 = -30, SX1 = -20, SZ0 = -30, SZ1 = -6, F = 3.6;
  B.add(SX0, 0, SZ0, SX1, 0.12, SZ1, 'wood');
  wall(W, 'z', SX1, SZ0, SZ1, 0, 2 * F, 0.4, 'plaster', [{ a: -18, b: -15, y0: 0, y1: 2.8 }, { a: -11, b: -9, y0: F + 1, y1: F + 2.2 }]);
  wall(W, 'z', SX0, SZ0, SZ1, 0, 2 * F, 0.4, 'plaster', [{ a: -28, b: -25.5, y0: 0, y1: 2.8 }, { a: -28.15, b: -25.35, y0: F + 0.25, y1: F + 2.7 }]);
  // balcony over B: walk upstairs, out the door, look down on the site (or drop in through the gap in the rail)
  B.add(-34, F, -30, -30.2, F + 0.25, -24, 'wood');
  B.add(-34, F + 0.25, -30, -33.8, F + 1.15, -28.25, 'wood'); B.add(-34, F + 0.25, -25.25, -33.8, F + 1.15, -24, 'wood');
  B.add(-33.8, F + 0.25, -30, -30.2, F + 1.15, -29.8, 'wood');
  B.box(-33.8, F / 2, -24.3, 0.3, F, 0.3, 'wood'); B.box(-33.8, F / 2, -29.7, 0.3, F, 0.3, 'wood');
  wall(W, 'x', SZ0, SX0, SX1, 0, 2 * F, 0.4, 'plaster');
  wall(W, 'x', SZ1, SX0, SX1, 0, 2 * F, 0.4, 'plaster');
  slab(W, SX0 + 0.2, SZ0, SX1, SZ1, F, F + 0.25, 'wood', [-23, -12, -21, -6.4]);
  stairs(W, -23, -21, -12, 1, 0.12, F + 0.25, 'wood', 0.6);
  B.add(SX0, 2 * F, SZ0, SX1, 2 * F + 0.3, SZ1, 'roof');
  for (const [x, z] of [[-27, -20], [-24, -9]]) B.box(x, 0.6, z, 1.2, 1.2, 1.2, 'crate');
  B.add(-29.5, F + 0.25, -24, -28, F + 1.1, -14, 'cloth'); // sacks of spice upstairs
  block(-30, -5.8, -20, -2, 7);

  // ---- B gate: the cistern comes up here, then an arch (chokepoint) into B
  block(X0, -24, -52, -2, 8); block(-40, -24, -30, -2, 8);
  wall(W, 'x', -24, -52, -40, 0, 6, 1, 'adobe', [{ a: -48, b: -44, y0: 0, y1: 3.2 }]);

  // ---- the CISTERN: underground tunnel from the attacker side to B. close quarters, pillars, a flooded side chamber
  B.add(-50, -3.9, -8, -40, -3.5, 56, 'stone');
  wall(W, 'z', -50.2, -8, 56, -3.5, -0.4, 0.4, 'stone', [{ a: 20, b: 28, y0: -3.5, y1: -0.4 }]);
  B.add(-40, -3.5, -8, -39.6, -0.4, 56, 'stone');
  B.add(-50, -3.5, -8.4, -40, -0.4, -8, 'stone'); B.add(-50, -3.5, 56, -40, -0.4, 56.4, 'stone');
  stairs(W, -50, -42, -4, -1, -3.5, 0, 'stone', 0.5);
  stairs(W, -46, -40, 52, 1, -3.5, 0, 'stone', 0.5);
  B.add(-58, -3.9, 18, -50, -3.5, 30, 'stone'); // floor runs right through the doorway (it stopped 0.4 short: a slot into the void)
  B.add(-58.4, -3.5, 18, -58, -0.4, 30, 'stone'); B.add(-58, -3.5, 17.6, -50.4, -0.4, 18, 'stone'); B.add(-58, -3.5, 30, -50.4, -0.4, 30.4, 'stone');
  B.add(-56, -3.5, 21, -52, -3.45, 27, 'water');
  for (const z of [44, 30, 14, 2]) B.box(-45, -1.95, z, 1, 3.1, 1, 'stone');
  for (const z of [40, 20, 0]) B.box(-49.7, -1.6, z, 0.2, 0.4, 0.6, 'light');

  const att = [[-12, 0.1, 66], [-6, 0.1, 70], [0, 0.1, 63], [6, 0.1, 70], [12, 0.1, 66], [-16, 0.1, 58], [16, 0.1, 58]];
  const def = [[-12, 0.1, -70], [-6, 0.1, -63], [0, 0.1, -61], [6, 0.1, -63], [12, 0.1, -70], [-16, 0.1, -62], [16, 0.1, -62]];
  const spawns = [...att, ...def, [0, 0.1, 20], [42, 0.1, 30], [-45, -3.4, 20], [46, 1.7, -40], [-50, 0.1, -32], [8, 0.1, -12], [27, 3.5, -16], [40, 0.1, -60], [-41, 0.1, -60], [-25, 0.2, -16]];
  // outside the walls: real sand in every direction (go over a wall: RETURN TO THE MAP), the desert to the horizon
  groundHoles(B, -260, -260, 260, 260, -2, 0, 'sand', [[X0 - 1, Z0 - 1, X1 + 1, Z1 + 1]]);
  const D = builder(), neons = ['neonnoodle', 'neonbar', 'neonhotel', 'neonwork'], rv = rng(7171);
  horizon(D, -260, -260, 260, 260, 1500, 'sand');
  const Dw = D.local(0, 0, 0);
  for (let i = 0; i < 40; i++) { const a = rv() * Math.PI * 2, d = 120 + rv() * 220, x = Math.cos(a) * d, z = Math.sin(a) * d; if (Math.abs(z) < 12 && x < 0) continue; dune(D, x, z, 30 + rv() * 60, 18 + rv() * 36, 5 + rv() * 12); }
  for (let i = 0; i < 12; i++) { const a = rv() * Math.PI * 2, d = 200 + rv() * 220; rocks(D, Math.cos(a) * d, Math.sin(a) * d, 12 + rv() * 20, rv); }
  // a camp outside the attackers' wall, a dirt track off into the dunes, an oasis to the east, a town on the horizon
  for (const [x, z, c] of [[-22, 92, 'cloth'], [-8, 96, 'toypink'], [10, 92, 'cloth'], [26, 97, 'toyteal']]) tent(Dw, x, z, c);
  for (const [x, z, ax] of [[-34, 98, true], [40, 90, false]]) camel(Dw, x, z, ax);
  D.add(-3, 0, 78, 3, 0.03, 400, 'dirtroad');
  D.add(130, 0, -40, 170, 0.2, -10, 'lawn'); D.add(136, 0.2, -34, 164, 0.3, -16, 'water');
  for (const [x, z] of [[132, -42], [168, -38], [128, -20], [172, -14], [150, -8], [146, -44]]) palm(Dw, x, z, 6 + rv() * 3, rv);
  for (let i = 0; i < 26; i++) { // the next town over: flat roofs, a few domes, a water tower
    const x = -330 + (rv() - 0.5) * 120, z = -180 + (rv() - 0.5) * 140, w = 8 + rv() * 10, h = 4 + rv() * 9;
    D.add(x - w / 2, 0, z - w / 2, x + w / 2, h, z + w / 2, rv() < 0.7 ? 'adobe' : ['sidepink', 'sidelemon', 'sidemint'][(rv() * 3) | 0]);
    if (rv() < 0.25) { D.add(x - w * 0.3, h, z - w * 0.3, x + w * 0.3, h + w * 0.25, z + w * 0.3, 'adobe'); D.add(x - w * 0.18, h + w * 0.25, z - w * 0.18, x + w * 0.18, h + w * 0.4, z + w * 0.18, 'adobe'); }
  }
  // the look (render-only): neon over the market stalls, ads on the attackers' wall, strips under the hall roof
  for (let z = 8, i = 0; z <= 40; z += 16, i++) { D.add(8.7, 4.2, z - 2, 8.98, 5.0, z + 2, neons[i % 4], { fit: 1 }); D.add(-8.98, 4.6, z + 6, -8.7, 5.4, z + 10, neons[(i + 2) % 4], { fit: 1 }); }
  D.add(8.9, 6.6, -2, 8.98, 6.75, 52, 'neonpink'); D.add(-8.98, 6.6, -2, -8.9, 6.75, 52, 'neoncyan');
  D.add(-15, 4.5, 52.42, -7, 7.5, 52.6, 'adcity4', { fit: 1 }); D.add(7, 4.5, 52.42, 15, 7.5, 52.6, 'adcity1', { fit: 1 });
  return {
    name: 'Bazaar', size: 'large', boxes: B.boxes, deco: D.boxes, killY: -30, floorY: -6, bounds: [X0 - 1.5, Z0 - 1.5, X1 + 1.5, Z1 + 1.5],
    sky: { top: 0x4a8fd8, mid: 0xf2dcae, bot: 0x8a6a40, fog: 0xf0d8a8 }, fogNear: 90, fogFar: 320,
    spawns, teamSpawns: { att, def },
    // bot routes along the real lanes, [x, z] points ending on each site. bots walk straight from point to point and
    // count a point as reached 2.6 m away, so: every leg is clear of props, doors get a point on their centreline more
    // than 2.6 m in on each side, and the hall lanes (and the plaza point after them, off the well's line) keep to the
    // middle so a bot shoved behind a stall slides back out
    nav: {
      A: [
        [[16, 62], [28, 62], [42, 62], [42, 30], [43, 6], [43, -3], [43, -10], [47, -21], [47, -27], [46.5, -30.8], [43.5, -31], [42, -38]], // canal street
        [[0, 56], [2.5, 32], [2.5, 16], [2.5, -1], [3, -4], [18, -2.5], [18, -10], [18, -14], [27, -21], [31, -27.5], [37, -28.5], [44, -38]], // hall -> bridge
        [[0, -62], [8, -64], [22, -63], [32, -58], [39, -57], [39, -52], [41, -47], [46, -40]], // defenders' garden
      ],
      B: [
        [[-16, 62], [-30, 61], [-43, 60], [-43, 57], [-43, 52], [-43, 44], [-43, 30], [-43, 8], [-43, -1], [-44, -9], [-46, -18], [-46, -25], [-44, -31]], // cistern
        [[0, 56], [-2.5, 32], [-2.5, 16], [-2.5, -1], [-3, -4], [-17, -16.5], [-23, -16.5], [-25, -21], [-26, -26.75], [-33, -26.75], [-37, -28.5], [-41, -33]], // hall -> spice house
        [[0, -62], [-8, -64], [-22, -62], [-32, -58], [-40, -56], [-40, -50], [-52, -45]], // defenders' arcade
      ],
    },
    sites: [{ id: 'A', min: [36, 1.6, -50], max: [56, 1.6, -30] }, { id: 'B', min: [-60, 0, -50], max: [-34, 0, -28] }],
  };
}

// ------------------------------------------------------------ BACKROOMS: extra large liminal maze, after the "Level 0" internet legend.
// 240 x 240 m of mono-yellow rooms on a 4 m grid (the biggest map by far) around a huge open hall in the middle (64 x 64 m,
// 7.5 m ceiling, sparse pillars: long fights across it). Around it: irregular rooms of every size with doorways, long
// straight halls, pillar rooms, a few dead-end alcoves, and a hole down into flooded pool rooms one level below.
// Plant & Defuse: A (the Office) north-east of the hall, B (the Wet Room) north-west of it, defenders spawn at the north end,
// attackers at the south end. Sealed: no sky, no scenery. Bots get a walk graph (shared/nav.js) to find their way.
function backrooms() {
  const B = builder(), D = builder(); // D = render-only boxes: light overlays, pool water, tiles on the pool ceiling
  const W = B.local(0, 0, 0);
  const r = rng(1777);
  const N = 60, U = 4, O = -120, H = 3, HH = 7.5, PY = -4.5, T = 0.2; // grid cells, cell size, map edge, ceilings, pool floor, wall thickness
  const gx = (i) => O + i * U, mid = (i) => O + (i + 0.5) * U;
  const pick = (a) => a[(r() * a.length) | 0];

  // ---- the plan: every grid cell belongs to a room. the big set pieces first, random rooms fill the rest
  const ids = new Int32Array(N * N).fill(-1), rooms = [];
  const id = (i, j) => (i < 0 || j < 0 || i >= N || j >= N ? -2 : ids[i * N + j]);
  const room = (i0, j0, i1, j1, kind = 'room', o = {}) => {
    const rm = { k: rooms.length, i0, j0, i1, j1, kind, deg: 0, ...o };
    rooms.push(rm);
    for (let i = i0; i < i1; i++) for (let j = j0; j < j1; j++) ids[i * N + j] = rm.k;
    return rm;
  };
  const hall = room(22, 22, 38, 38, 'hall'); // x, z in [-32, 32]
  const def = room(25, 1, 35, 5, 'lobby'), att = room(25, 55, 35, 59, 'lobby'); // spawns at the north and south ends
  const siteA = room(41, 15, 48, 21, 'office'), siteB = room(12, 15, 19, 21, 'wet');
  room(12, 50, 18, 55, 'drop'); room(12, 35, 17, 40, 'stairs');
  room(6, 9, 54, 10, 'long'); room(51, 14, 52, 54, 'long'); room(8, 24, 9, 50, 'long'); room(10, 47, 50, 48, 'long'); // long straight halls
  room(2, 25, 8, 32, 'pillars', { step: 1 }); room(53, 28, 59, 35, 'pillars', { step: 2 }); room(39, 39, 46, 45, 'pillars', { step: 1 });
  room(40, 2, 47, 8, 'pillars', { step: 2 }); room(8, 1, 14, 7, 'pillars', { step: 2 });
  const sizes = [1, 2, 2, 2, 3, 3, 3, 4, 4, 5, 6];
  for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) {
    if (ids[i * N + j] !== -1) continue;
    let w = pick(sizes), h = pick(sizes);
    if (r() < 0.2) { const l = 3 + ((r() * 6) | 0); if (r() < 0.5) { w = 1; h = l; } else { w = l; h = 1; } } // a corridor
    let ww = 0, hh = 0;
    while (ww < w && i + ww < N && ids[(i + ww) * N + j] === -1) ww++;
    const rowFree = (jj) => { for (let a = 0; a < ww; a++) if (ids[(i + a) * N + jj] !== -1) return false; return true; };
    while (hh < h && j + hh < N && rowFree(j + hh)) hh++;
    room(i, j, i + ww, j + hh, ww * hh >= 16 && Math.min(ww, hh) >= 4 && r() < 0.3 ? 'pillars' : 'room', { step: 2 });
  }

  // ---- doorways: a random spanning tree so everything connects, then lots of extra ones (the place is full of loops)
  const pairs = new Map();
  const edge = (a, b, e) => {
    if (a < 0 || b < 0 || a === b) return;
    const key = Math.min(a, b) * 10000 + Math.max(a, b);
    if (!pairs.has(key)) pairs.set(key, { a: Math.min(a, b), b: Math.max(a, b), edges: [], open: 0 });
    pairs.get(key).edges.push(e);
  };
  for (let j = 1; j < N; j++) for (let i = 0; i < N; i++) edge(id(i, j - 1), id(i, j), { ax: 'x', line: j, k: i });
  for (let i = 1; i < N; i++) for (let j = 0; j < N; j++) edge(id(i - 1, j), id(i, j), { ax: 'z', line: i, k: j });
  const opens = new Map();
  const addOpen = (ops, ax, line, o) => { const k = ax + line; if (!ops.has(k)) ops.set(k, []); ops.get(k).push(o); };
  const door = (p, wide) => {
    const es = p.edges, free = es.filter((e) => !e.used);
    if (!free.length) return;
    if (wide && !p.open) { // open up most of the shared wall, leaving stubs at the ends
      const a = gx(es[0].k), b = gx(es[es.length - 1].k + 1), stub = es.length > 1 ? 0.6 + r() * 1.4 : 0.35;
      addOpen(opens, es[0].ax, es[0].line, { a: a + stub, b: b - stub, y0: 0, y1: H + 0.2 });
      for (const e of es) e.used = true;
    } else {
      const e = pick(free.length > 2 ? free.slice(1, -1) : free), c = mid(e.k), w = 1.5 + r() * 0.7; // not right in a corner
      addOpen(opens, e.ax, e.line, { a: c - w / 2, b: c + w / 2, y0: 0, y1: r() < 0.55 ? 2.25 + r() * 0.3 : H + 0.2 }); // full height ones cut the wall's top too (it goes up into the ceiling)
      e.used = true;
    }
    if (!p.open) { rooms[p.a].deg++; rooms[p.b].deg++; }
    p.open++;
  };
  const list = [...pairs.values()];
  for (let i = list.length - 1; i > 0; i--) { const j = (r() * (i + 1)) | 0; [list[i], list[j]] = [list[j], list[i]]; }
  const par = rooms.map((_, i) => i), find = (x) => (par[x] === x ? x : (par[x] = find(par[x])));
  const wideP = (p) => r() < (rooms[p.a].kind !== 'room' || rooms[p.b].kind !== 'room' ? 0.04 : 0.17);
  for (const p of list) { const a = find(p.a), b = find(p.b); if (a !== b) { par[a] = b; door(p, wideP(p)); } }
  for (const p of list) {
    const ka = rooms[p.a].kind, kb = rooms[p.b].kind;
    if (p.open) { if (p.edges.length >= 6 && r() < 0.4) door(p, false); continue; }
    if (r() < (ka === 'long' || kb === 'long' ? 0.7 : ka === 'hall' || kb === 'hall' ? 0.65 : 0.4)) door(p, wideP(p));
  }
  const byRoom = rooms.map(() => []); // each room's neighbours, in the same (shuffled) order as list
  for (const p of list) { byRoom[p.a].push(p); byRoom[p.b].push(p); }
  const more = (rm, n) => { // make sure a room has at least n ways in
    const ps = byRoom[rm.k].filter((p) => !p.open);
    while (rm.deg < n && ps.length) door(ps.splice((r() * ps.length) | 0, 1)[0], false);
  };
  for (const rm of [siteA, siteB, def, att]) more(rm, 4);
  more(hall, 18);
  let alcoves = 0; // dead ends: keep a handful of little alcoves, open the rest up
  for (const rm of rooms) if (rm.deg === 1) { if ((rm.i1 - rm.i0) * (rm.j1 - rm.j0) <= 2 && alcoves < 8) alcoves++; else more(rm, 2); }

  // ---- walls along the grid lines between rooms, in runs with the doorways cut out. the hall's go all the way up
  const walls = (idf, y0, top, mat, ops) => {
    const run = (ax, line, at2) => {
      let s = -1, sh = 0;
      for (let k = 0; k <= N; k++) {
        const [a, b] = k < N ? at2(k) : [0, 0], h = a !== b ? top(a, b) : 0;
        if (s >= 0 && h !== sh) { wall(W, ax, gx(line), gx(s) - T / 2, gx(k) + T / 2, y0, sh, T, mat, ops.get(ax + line) || []); s = -1; }
        if (h && s < 0) { s = k; sh = h; }
      }
    };
    for (let j = 0; j <= N; j++) run('x', j, (i) => [idf(i, j - 1), idf(i, j)]);
    for (let i = 0; i <= N; i++) run('z', i, (j) => [idf(i - 1, j), idf(i, j)]);
  };
  walls(id, 0, (a, b) => (a === hall.k || b === hall.k ? HH : H) + 0.2, 'wallpaper', opens); // up into the ceiling slab, so no seam and no lintel flush with the ceiling

  // ---- stairs down to the pools (a flight in grid column col: top landing in row jt, the hole in rows jt+1 and jt+2,
  // bottom landing in row jt+3 on the pool level), and the hole you just fall through
  const holes = [], stairsNav = [], drops = [];
  const flight = (col, jt) => {
    const z0 = gx(jt + 1), zb = gx(jt + 3);
    stairs(W, gx(col), gx(col + 1), zb, -1, PY, 0, 'pooltile', (zb - z0) / Math.ceil(-PY / 0.45)); // fills the hole edge to edge: no slot to drop the bomb through
    B.add(gx(col) - 0.12, 0, z0, gx(col), 1.05, zb + 0.12, 'metal'); B.add(gx(col + 1), 0, z0, gx(col + 1) + 0.12, 1.05, zb + 0.12, 'metal'); // rails
    B.add(gx(col), 0, zb, gx(col + 1), 1.05, zb + 0.12, 'metal');
    holes.push([gx(col), z0, gx(col + 1), zb]);
    stairsNav.push({ top: [mid(col), 0, mid(jt)], bot: [mid(col), PY, mid(jt + 3)] });
  };
  flight(13, 17); // up into B
  flight(14, 36); // up into a room west of the hall
  flight(16, 51); // back up, next to the hole
  holes.push([gx(13), gx(51), gx(14), gx(53)]); // the hole
  for (const j of [51, 52]) for (const [fi, fj] of [[12, j], [14, j], [13, j === 51 ? 50 : 53]]) drops.push({ from: [mid(fi), 0, mid(fj)], to: [mid(13), PY, mid(j)] });

  // ---- floors: old damp carpet on a concrete slab. the Office has its own carpet, the Wet Room is tiled
  const rect = (rm) => [gx(rm.i0), gx(rm.j0), gx(rm.i1), gx(rm.j1)];
  groundHoles(B, O, O, -O, -O, -0.05, 0, 'carpetb', [...holes, rect(siteA), rect(siteB)]);
  groundHoles(B, O, O, -O, -O, -0.6, -0.05, 'concrete', holes);
  B.add(gx(siteA.i0), -0.05, gx(siteA.j0), gx(siteA.i1), 0, gx(siteA.j1), 'officecarpet');
  groundHoles(B, ...rect(siteB), -0.05, 0, 'pooltile', holes);
  // ---- ceilings: a low drop ceiling everywhere, the hall's way up high. the light panels are part of the tile texture
  slab(W, O, O, -O, -O, H, H + 0.3, 'ceiltile', rect(hall));
  B.add(gx(hall.i0) - T, HH, gx(hall.j0) - T, gx(hall.i1) + T, HH + 0.3, gx(hall.j1) + T, 'ceiltile');
  const plain = rooms.filter((rm) => rm.kind === 'room' && (rm.i1 - rm.i0) * (rm.j1 - rm.j0) >= 2);
  for (let n = 0; n < 26; n++) { // some rooms' lights flicker, some are dead
    const rm = plain.splice((r() * plain.length) | 0, 1)[0];
    D.add(gx(rm.i0), H - 0.03, gx(rm.j0), gx(rm.i1), H, gx(rm.j1), n < 14 ? ['ceilflick', 'ceilflick2', 'ceilflick3'][n % 3] : 'ceildark'); // three of them, each dying on its own
  }
  D.add(gx(8), H - 0.03, gx(30), gx(9), H, gx(41), 'ceildark'); // a long dark stretch of the west hall
  D.add(gx(20), H - 0.03, gx(9), gx(31), H, gx(10), 'ceilflick2');

  // ---- the big hall: sparse pillars, a few freestanding walls (one has a doorway to nowhere), low walls for cover
  for (const [x, z] of [[-16, -16], [16, -16], [-16, 16], [16, 16], [0, -24], [0, 24], [-24, 0], [24, 0]]) B.box(x, HH / 2, z, 1.6, HH, 1.6, 'wallpaper');
  wall(W, 'z', -8, -12, -4, 0, H, T, 'wallpaper', [{ a: -8.9, b: -7.1, y0: 0, y1: 2.3 }]);
  wall(W, 'x', 8, 4, 12, 0, H, T, 'wallpaper');
  wall(W, 'z', 20, 8, 16, 0, H, T, 'wallpaper');
  wall(W, 'x', -20, -24, -16, 0, H, T, 'wallpaper');
  B.add(-28, 0, 3.9, -20, 1.2, 4.1, 'wallpaper'); B.add(12, 0, -24.1, 20, 1.2, -23.9, 'wallpaper'); B.add(23.9, 0, 20, 24.1, 1.2, 28, 'wallpaper');
  // a second ring of cover between the pillars, so crossing the hall is a choice and not a death sentence. all on grid
  // lines (4 m), so they never touch a cell's middle, where spawns and bot nav nodes are
  wall(W, 'x', 20, -14, -6, 0, H, T, 'wallpaper', [{ a: -11, b: -9, y0: 1.2, y1: 2.1 }]); // with a window to peek through
  wall(W, 'z', 8, -24, -14, 0, H, T, 'wallpaper');
  wall(W, 'x', -8, 20, 28, 0, H, T, 'wallpaper');
  B.add(-6, 0, 11.9, 0, 1.2, 12.1, 'wallpaper'); B.add(3.9, 0, -12, 4.1, 1.2, -4, 'wallpaper'); B.add(-20.1, 0, 10, -19.9, 1.2, 16, 'wallpaper');
  B.add(-28.1, 0, -12, -27.9, 1.2, -6, 'wallpaper'); B.add(6, 0, 15.9, 12, 1.2, 16.1, 'wallpaper'); B.add(27.9, 0, -24, 28.1, 1.2, -16, 'wallpaper');
  // ---- pillar rooms
  for (const rm of rooms) if (rm.kind === 'pillars') for (let i = rm.i0 + 1; i < rm.i1; i += rm.step) for (let j = rm.j0 + 1; j < rm.j1; j += rm.step) B.box(gx(i), H / 2, gx(j), 0.7, H, 0.7, 'wallpaper');

  // ---- SITE A, the Office: grey-blue carpet, cubicles either side of a + shaped aisle, desks, a water cooler
  const cube = (i0, j0, i1, j1, open) => { // partitions on the inner grid lines, open toward the aisle (open = -1 north, 1 south)
    const z0 = gx(j0), z1 = gx(j1), back = open > 0 ? z0 : z1, s = open > 0 ? 1 : -1;
    for (let i = i0 + 1; i < i1; i++) B.add(gx(i) - 0.05, 0, open < 0 ? z0 + 1.2 : z0, gx(i) + 0.05, 1.4, open < 0 ? z1 : z1 - 1.2, 'cubicle');
    for (let i = i0; i < i1; i++) { // a desk against the back of every cubicle, most with a monitor
      B.add(mid(i) - 1.3, 0, Math.min(back + s * 0.12, back + s * 0.85), mid(i) + 1.3, 0.75, Math.max(back + s * 0.12, back + s * 0.85), 'plaster');
      if (r() < 0.7) B.add(mid(i) - 0.3, 0.75, Math.min(back + s * 0.3, back + s * 0.36), mid(i) + 0.3, 1.15, Math.max(back + s * 0.3, back + s * 0.36), 'glass');
    }
  };
  cube(41, 15, 44, 17, 1); cube(45, 15, 48, 17, 1); cube(41, 18, 44, 21, -1); cube(45, 18, 48, 21, -1);
  B.add(57.7, 0, -59.85, 58.3, 1.1, -59.25, 'white'); B.add(57.75, 1.1, -59.8, 58.25, 1.55, -59.3, 'water'); // water cooler

  // ---- SITE B, the Wet Room: white tiles, the stairs up from the pools, tiled half walls, a couple of pillars, puddles
  B.add(-60, 0, -52.1, -52, 1.2, -51.9, 'pooltile'); B.add(-48.1, 0, -48, -47.9, 1.2, -40, 'pooltile'); B.add(-68, 0, -56.1, -62, 1.2, -55.9, 'pooltile');
  B.box(-56, H / 2, -44, 1, H, 1, 'pooltile'); B.box(-48, H / 2, -56, 1, H, 1, 'pooltile');
  for (const [x, z, s] of [[-58, -46, 3], [-52, -57, 2], [-62, -53, 2.5]]) D.add(x - s / 2, 0.005, z - s / 2.6, x + s / 2, 0.02, z + s / 2.6, 'poolwater');
  // ---- spawn lobbies: a row of pillars down the middle
  for (const rm of [def, att]) for (const x of [-12, -4, 4, 12]) B.box(x, H / 2, (gx(rm.j0) + gx(rm.j1)) / 2, 0.8, H, 0.8, 'wallpaper');

  // ---- the pool rooms: flooded, white tiles everywhere, under the west side of the map
  const pids = new Int32Array(N * N).fill(-1), prooms = [], pops = new Map();
  const pid = (i, j) => (i < 0 || j < 0 || i >= N || j >= N ? -2 : pids[i * N + j]);
  for (const [i0, j0, i1, j1] of [[11, 48, 18, 56], [13, 24, 16, 48], [11, 17, 18, 24], [10, 28, 13, 38], [16, 30, 20, 44]]) {
    for (let i = i0; i < i1; i++) for (let j = j0; j < j1; j++) pids[i * N + j] = prooms.length;
    prooms.push([gx(i0), gx(j0), gx(i1), gx(j1)]);
  }
  for (const j of [48, 24]) addOpen(pops, 'x', j, { a: gx(13) + 0.6, b: gx(16) - 0.6, y0: PY, y1: -0.6 });
  for (const [i, j] of [[13, 30], [13, 35], [16, 32], [16, 41]]) addOpen(pops, 'z', i, { a: mid(j) - 1, b: mid(j) + 1, y0: PY, y1: PY + 2.6 });
  walls(pid, PY, () => -0.3, 'pooltile', pops); // up into the concrete, past the tiles on the pool ceiling (no seam where they meet)
  for (const pr of prooms) {
    B.add(pr[0], PY - 0.5, pr[1], pr[2], PY, pr[3], 'pooltile');
    D.add(pr[0], PY, pr[1], pr[2], PY + 0.45, pr[3], 'poolwater');
    groundHoles(D, ...pr, -0.63, -0.6, 'pooltile', holes);
  }
  for (let j = 26; j < 48; j += 2) if (j < 36 || j > 39) for (const i of [14, 15]) B.box(gx(i), (PY - 0.3) / 2, gx(j), 0.6, -0.3 - PY, 0.6, 'pooltile');
  for (const [i, j] of [[12, 50], [15, 50], [12, 54], [15, 55]]) B.box(gx(i), (PY - 0.3) / 2, gx(j), 0.8, -0.3 - PY, 0.8, 'pooltile');

  // ---- bots: a walk graph over both levels, and routes along the lanes for Plant & Defuse. only the server's bots use
  // them, so they're built the first time something asks (the browser never pays for it)
  let graph = null, nav = null;
  const navGraph = () => graph || (graph = buildNav(B.boxes, { x0: O, z0: O, n: N, cell: U, levels: [0, PY], stairs: stairsNav, drops }));
  const route = (...via) => { // A* through the via points, then keep only the corners. points are [x, z, y]
    const graph = navGraph(), ks = [];
    for (let v = 0; v + 1 < via.length; v++) for (const k of navPath(graph, navLocate(graph, via[v]), navLocate(graph, via[v + 1])) || []) if (ks[ks.length - 1] !== k) ks.push(k);
    const out = [ks[0]];
    for (let k = 1; k < ks.length; k++) {
      const a = graph.nodes[out[out.length - 1]], lv = graph.lvl[out[out.length - 1]], b = graph.nodes[ks[k + 1]];
      if (b && graph.lvl[ks[k]] === lv && graph.lvl[ks[k + 1]] === lv && navClear(graph, lv, a[0], a[2], b[0], b[2])) continue;
      out.push(ks[k]);
    }
    return out.map((k) => [graph.nodes[k][0], graph.nodes[k][2], graph.nodes[k][1]]);
  };
  const A = [58, 0, -46], Bc = [-56, 0, -50];
  const lanes = () => nav || (nav = {
    A: [route([16, 0, 108], [86, 0, 90], [86, 0, -40], A), route([0, 0, 102], [0, 0, 28], [28, 0, -8], A), route([16, 0, -108], [60, 0, -82], A)],
    B: [route([-16, 0, 108], [-62, 0, 90], [mid(13), PY, mid(51)], [mid(14), PY, 0], [mid(13), PY, mid(20)], Bc), route([0, 0, 102], [0, 0, 28], [-28, 0, -8], Bc), route([-16, 0, -108], [-60, 0, -82], Bc)],
  });
  // free-for-all spawns spread all over: farthest-point picks from the cells of the roomier rooms (a cell's middle is
  // never in a wall, a pillar or a desk: they all sit on grid lines), plus two in the pools
  const cand = [];
  for (const rm of rooms) if (rm.kind !== 'lobby' && rm.i1 - rm.i0 >= 2 && rm.j1 - rm.j0 >= 2) for (let i = rm.i0; i < rm.i1; i++) for (let j = rm.j0; j < rm.j1; j++) {
    const x = mid(i), z = mid(j);
    if (!holes.some((h) => x > h[0] && x < h[2] && z > h[1] && z < h[3])) cand.push([x, z]);
  }
  const far = new Float64Array(cand.length).fill(1e9), spawns = [];
  for (let n = 0, k = (r() * cand.length) | 0; n < 30; n++) {
    const p = cand[k];
    spawns.push([p[0], 0.1, p[1]]);
    cand.forEach((c, i) => { far[i] = Math.min(far[i], Math.hypot(c[0] - p[0], c[1] - p[1])); });
    k = 0;
    for (let i = 1; i < cand.length; i++) if (far[i] + r() * 6 > far[k]) k = i;
  }
  spawns.push([mid(14), PY + 0.1, mid(30)], [mid(15), PY + 0.1, mid(45)]);
  const att2 = [[-16, 0.1, 113], [-8, 0.1, 113], [0, 0.1, 113], [8, 0.1, 113], [16, 0.1, 113], [-8, 0.1, 103], [8, 0.1, 103]];
  const def2 = att2.map(([x, y, z]) => [x, y, -z]);
  const HZ = 0xb4a35a; // the haze
  return {
    name: 'Backrooms', size: 'extra large', boxes: B.boxes, deco: D.boxes, killY: -30,
    sky: { top: HZ, mid: HZ, bot: HZ, fog: HZ }, fogNear: 6, fogFar: 105,
    light: { hemi: [0xfff3cc, 0xb2a476, 1.35], sun: [0xffe7a6, 0.5] }, // flat fluorescent light from everywhere
    chunk: 48, sealed: true, menuCam: [13, 3.4, -0.08], // big: drawn in chunks. sealed: no sky, and the menu orbits inside the hall
    spawns, spawnSafe: 45, teamSpawns: { att: att2, def: def2 }, teamSpawnsBomb: true, roundTime: 150, // lobbies only for Plant & Defuse (they're 226 m apart); rounds are longer, it's a long walk
     get nav() { return lanes(); }, get graph() { return navGraph(); },
    sites: [{ id: 'A', min: [gx(siteA.i0) + 0.5, 0, gx(siteA.j0) + 0.5], max: [gx(siteA.i1) - 0.5, 0, gx(siteA.j1) - 0.5] },
      { id: 'B', min: [gx(siteB.i0) + 0.5, 0, gx(siteB.j0) + 0.5], max: [gx(siteB.i1) - 0.5, 0, gx(siteB.j1) - 0.5] }],
  };
}

function range() {
  const { boxes, box } = builder();
  box(0, -1, -60, 40, 2, 150, 'grass');
  box(0, -6, -60, 30, 8, 130, 'dirt');
  box(0, 0.4, 5, 40, 0.8, 1, 'wood');
  for (const z of [-10, -25, -50, -100]) box(-17, 0.6, z, 4, 1.2, 0.4, 'wood');
  box(32, -1, -40, 20, 2, 40, 'grass');
  box(28, 0.15, -25, 2.5, 0.3, 2.5, 'pad', { pad: [0, 30, 0] });
  box(36, 0.15, -35, 2.5, 0.3, 2.5, 'pad', { pad: [0, 22, -22] });
  for (let i = 0; i < 6; i++) box(32 + (i % 2 ? 6 : -6), 20 + i * 4, -30 - i * 14, 3, 1, 3, 'pink');
  box(32, 9, -55, 3, 18, 3, 'stone');
  box(-32, -1, -40, 16, 2, 30, 'stone');
  box(-38, 1, -40, 1, 2, 30, 'missing');
  groundHoles({ add: (...a) => boxes.push({ min: [a[0], a[1], a[2]], max: [a[3], a[4], a[5]], mat: a[6] }) }, -220, -280, 220, 160, -2, 0, 'grass', [[-20, -135, 20, 15], [22, -60, 42, -20], [-40, -55, -24, -25]]);
  const D = builder();
  horizon(D, -220, -280, 220, 160, 1500, 'lawn');
  D.add(-60, 0, -175, 60, 12, -160, 'dirt'); D.add(-50, 12, -172, 50, 16, -163, 'dirt'); // the berm the bullets end up in
  for (let x = -18; x <= 18; x += 3.2) D.add(x, 0, 6.4, x + 3, 0.8, 7.4, 'sand'); // sandbags on the firing line
  for (const [x, z] of [[-30, 20], [30, 20]]) { for (const sx of [-1, 1]) for (const sz of [-1, 1]) D.box(x + sx * 1.6, 4, z + sz * 1.6, 0.3, 8, 0.3, 'wood'); D.add(x - 2.2, 8, z - 2.2, x + 2.2, 8.3, z + 2.2, 'wood'); D.add(x - 2.4, 10.5, z - 2.4, x + 2.4, 10.8, z + 2.4, 'roofg'); } // watchtowers
  for (let z = 30; z > -260; z -= 10) for (const x of [-90, 90]) { D.box(x, 1, z, 0.15, 2, 0.15, 'metal'); D.add(x - 0.03, 1.6, z, x + 0.03, 1.65, z + 10, 'tire'); }
  for (let i = 0; i < 30; i++) { const rr = rng(400 + i), a = rr() * Math.PI * 2, d = 150 + rr() * 150; (rr() < 0.5 ? conifer : lollipop)(D.local(0, 0, 0), Math.cos(a) * d, -60 + Math.sin(a) * d, 6 + rr() * 4, rr); }
  adBoard(D, -26, -70, 0, 'z', 'adcity6', 14, 6); adBoard(D, -26, -110, 0, 'z', 'adcity3', 14, 6); adBoard(D, 0, -130, 0, 'x', 'adcity2', 24, 9);
  return { name: 'Range', size: 'training', boxes, deco: D.boxes, killY: -40, floorY: -4, bounds: [-90, -175, 90, 40],
    sky: { top: 0x3a7bd5, mid: 0xbfe3ff, bot: 0x203040, fog: 0xbfe3ff }, fogNear: 120, fogFar: 420,
    spawns: [[0, 0.1, 10], [5, 0.1, 10], [-5, 0.1, 10]],
    dummies: [
      { p: [0, 0, -10] }, { p: [-8, 0, -25] }, { p: [8, 0, -25], move: 4 }, { p: [0, 0, -50], move: 6 },
      { p: [-10, 0, -100] }, { p: [10, 0, -100], move: 8 }, { p: [-28, 0, -35] }, { p: [-28, 0, -45], move: 3 },
    ] };
}

export const MAPS = {
  crate: crate(), platform: platform(), rooftop: rooftop(), suburb: suburb(), warehouse: warehouse(),
  desert: desert(), islands: islands(), skyline: skyline(), bazaar: bazaar(), range: range(), backrooms: backrooms(),
};
// a spawn whose body would start inside a box (a column, a roof garden, a helipad) gets lifted onto whatever it's in
function unstick(boxes, list) {
  for (const p of list) for (let k = 0; k < 3; k++) {
    const b = boxes.find((q) => p[0] + 0.4 > q.min[0] && p[0] - 0.4 < q.max[0] && p[2] + 0.4 > q.min[2] && p[2] - 0.4 < q.max[2] && p[1] + 1.8 > q.min[1] && p[1] < q.max[1]);
    if (!b) break;
    p[1] = b.max[1] + 0.1;
  }
}
for (const m of Object.values(MAPS)) unstick(m.boxes, [...m.spawns, ...(m.teamSpawns ? [...m.teamSpawns.att, ...m.teamSpawns.def] : [])]);
export const MAP_ORDER = ['crate', 'platform', 'rooftop', 'suburb', 'warehouse', 'desert', 'bazaar', 'islands', 'skyline', 'backrooms'];

// Client convenience: "the current map". These arrays/objects are mutated in place by setMap,
// so every module that imported them sees the new map.
export const BOXES = [];
export const SPAWNS = [];
export const MAP = { id: '', name: '', killY: -45, sky: SKY_SUNSET, fogNear: 90, fogFar: 330 };
export function setMap(id) {
  const m = MAPS[id] || MAPS.islands;
  BOXES.length = 0; BOXES.push(...m.boxes);
  SPAWNS.length = 0; SPAWNS.push(...m.spawns);
  Object.assign(MAP, { id: MAPS[id] ? id : 'islands', name: m.name, killY: m.killY, sky: m.sky, fogNear: m.fogNear, fogFar: m.fogFar, size: m.size });
}
setMap('islands');
