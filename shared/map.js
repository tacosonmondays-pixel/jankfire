// All maps are lists of axis-aligned boxes. Shared by server (physics, bots) and client (rendering).
// Maps are generated deterministically so server and client always match.
// Rule of thumb for builders: never let two different surfaces sit in the same plane (that flickers).
import { buildNav, navPath, navLocate, navClear } from './nav.js';
import { outOfBounds } from './bounds.js';
import { prop } from './props.js';
export { prop, PROPS } from './props.js';

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
  boxes.props = []; // Blender props to draw (shared/props.js), visual only
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
    L.pt = (x, y, z) => { const [ax, az] = T(x, z); return [ox + ax, oy + y, oz + az]; }; // a local point in world space
    // a prop model at local (x, z), turned r more quarter turns. returns the tag for the boxes it stands in for
    L.P = (id, x, z, r = 0, o = {}) => {
      const [ax, az] = T(x, z);
      boxes.props.push({ id, p: [ox + ax, oy + (o.y || 0), oz + az], r: (rot + r) & 3, v: o.v, color: o.color, s: o.s });
      return { pv: id };
    };
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
    wall(L, 'x', hd, -hw, hw, y0, y1, t, mat, o.backDoor && f === 0 ? [{ a: Math.min(1.5, hw - 1.9), b: Math.min(3.1, hw - 0.3), y0: 0, y1: 2.5 }, ...windows(w, base, 1, 2.2, 5, 3.2)] : windows(w, base, 1, 2.2, 5)); // (a small hut's back door stays off its corner)
    wall(L, 'z', -hw, -hd, hd, y0, y1, t, mat, windows(d, base, 1, 2.2, 4.5).filter((x) => x.b < sz0 - 0.2));
    wall(L, 'z', hw, -hd, hd, y0, y1, t, mat, o.sideDoor && f === 0 ? [{ a: o.sideDoor[0], b: o.sideDoor[1], y0: 0, y1: 2.5 }] : windows(d, base, 1, 2.2, 4.5));
    // stairs from this floor up
    if (f < flights) {
      const lane = f % 2 === 0 ? laneA : laneB;
      const ya = f === 0 ? 0.12 : y0 + 0.25, yb = y1 + 0.25, rr = Math.min(run, 4.6 / Math.max(1, Math.ceil((yb - ya) / 0.45))); // a tall storey's steps get shorter so the flight fits the stairwell
      if (f % 2 === 0) stairs(L, lane[0], lane[1], sz0, 1, ya, yb, floorMat, rr);
      else stairs(L, lane[0], lane[1], hd - 0.4, -1, ya, yb, floorMat, rr);
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
  const pv = L.P && L.P('car', x, z, rot ? 1 : 0, { color }); // the Blender car, when it's loaded, stands in for these boxes
  const C = (lx0, y0, lz0, lx1, y1, lz1, m) => (rot ? L(x + lz0, y0, z + lx0, x + lz1, y1, z + lx1, m, pv) : L(x + lx0, y0, z + lz0, x + lx1, y1, z + lz1, m, pv));
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
  const pv = L.P && L.P('streetlight', x, z, armDir < 0 ? 2 : 0);
  L.B(x, 3, z, 0.25, 6, 0.25, 'metal', pv);
  L(x, 5.8, z - 0.12, x + armDir * 1.6, 6.0, z + 0.12, 'metal', pv);
  L.B(x + armDir * 1.6, 5.8, z, 0.6, 0.25, 0.4, 'light', pv);
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
  D.add(-S, y - 1, -S, S, y, S, 'asphaltn'); // the same wet street surface as the rest of the city, blocks and roads on top
  // the blocks between the roads: kerbed pavement. the ones past the outermost roads stop short, so there's no pale rim round
  // the edge of the grid (it used to sit on one big light-grey plate that ended in a hard edge)
  const cellsOf = (list) => { const l = [...list].sort((a, b) => a - b), out = []; for (let i = 0; i <= l.length; i++) { const a = i ? l[i - 1] + half : l[0] - half - 36, b = i < l.length ? l[i] - half : l[l.length - 1] + half + 36; if (b - a > 4) out.push([Math.max(-S, a), Math.min(S, b)]); } return out; };
  for (const [x0, x1] of cellsOf(roads.xs)) for (const [z0, z1] of cellsOf(roads.zs)) D.add(x0, y, z0, x1, y + 0.2, z1, 'pavecity');
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
// the street grid round the towers, carried on outward: north/east/west for L metres, south all the way to the water
const gridOut = (xs, zs, S, L) => [...xs.flatMap((x) => [[x, -S - L, x, -S], [x, S, x, S + 5000]]), ...zs.flatMap((z) => [[-S - L, z, -S, z], [S, z, S + L, z]])];
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
    D.add(x, y - 1, zp + 24, x + 20, y + 0.3, zp + 33, 'pavecity'); // the promenade: the city's own pavement, not a pale strip
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
  // the tower grid's own roads, carried on out of the grid into the city ([x0, z0, x1, z1] along one axis; south ones run
  // down to the waterfront), so no road just stops at the edge of the grid. same texture in world space: the lines run on
  const streets = (o.streets || []).map(([x0, z0, x1, z1]) => (x0 === x1
    ? { x0: x0 - 9, x1: x0 + 9, z0: Math.max(-R, Math.min(z0, z1)), z1: Math.min(Math.max(z0, z1), park(x0) - 1), alongZ: true }
    : { x0: Math.max(-R, Math.min(x0, x1)), x1: Math.min(R, Math.max(x0, x1)), z0: z0 - 9, z1: z0 + 9, alongZ: false }));
  for (const q of streets) {
    if (q.x1 - q.x0 < 1 || q.z1 - q.z0 < 1) continue;
    D.add(q.x0, y, q.z0, q.x1, y + 0.08, q.z1, q.alongZ ? 'wetroadz' : 'wetroad');
    if (q.alongZ) { D.add(q.x0 - 3, y, q.z0, q.x0, y + 0.19, q.z1, 'pavecity'); D.add(q.x1, y, q.z0, q.x1 + 3, y + 0.19, q.z1, 'pavecity'); }
    else { D.add(q.x0, y, q.z0 - 3, q.x1, y + 0.19, q.z0, 'pavecity'); D.add(q.x0, y, q.z1, q.x1, y + 0.19, q.z1 + 3, 'pavecity'); }
  }
  const onLand = (x, z, m = 0) => Math.abs(x) < R - m && Math.abs(z) < R - m && z < park(x) - m && !(Math.abs(x) < S + m && Math.abs(z) < S + m);
  for (const v of aves) {
    let run = null;
    const flush = (t) => { if (run === null) return; const t0 = run, len = t - t0; if (len > 12) { const tm = (t0 + t) / 2, cx = v.ax + v.ux * tm, cz = v.az + v.uz * tm;
      D.obb(cx, y + 0.05 + v.k * 0.01, cz, len, 0.08, 16, -v.a, 'wetroad'); // (always above the grid's roads where they cross)
      for (const s2 of [-1, 1]) D.obb(cx - v.uz * s2 * 9.5, y + 0.11 + v.k * 0.01, cz + v.ux * s2 * 9.5, len, 0.2, 3, -v.a, 'pavecity'); } run = null; };
    for (let t = -R * 1.5; t <= R * 1.5; t += 6) { const x = v.ax + v.ux * t, z = v.az + v.uz * t; if (onLand(x, z, 4)) { if (run === null) run = t; } else flush(t); }
    flush(R * 1.5);
  }
  // ---- districts: angular slices round the middle, each with its own grid
  const K = 7, cuts = [], hash = new Map(), HC = 40;
  let acc = r() * Math.PI * 2;
  for (let k = 0; k < K; k++) { cuts.push(acc); acc += (Math.PI * 2 / K) * (0.7 + r() * 0.6); }
  const sector = (x, z) => { let a = Math.atan2(z, x); for (let k = K - 1; k >= 0; k--) { let d = a - cuts[k]; while (d < 0) d += Math.PI * 2; let w = (k + 1 < K ? cuts[k + 1] : cuts[0] + Math.PI * 2) - cuts[k]; while (w <= 0) w += Math.PI * 2; if (d < w) return k; } return 0; };
  // exact tests on a block's real (turned) footprint b = { cx, cz, hw, hd, ux, uz }: it must stay clear of every avenue
  // and street with its sidewalks, of the other blocks, and keep all four corners on land. (checking from the middle
  // alone let big or turned blocks poke 10+ m out over the roads)
  const ext = (b, nx, nz) => b.hw * Math.abs(b.ux * nx + b.uz * nz) + b.hd * Math.abs(-b.uz * nx + b.ux * nz); // half its width along a direction
  const clearOfRoads = (b) => {
    for (const v of aves) { const nx = -v.uz, nz = v.ux; if (Math.abs((b.cx - v.ax) * nx + (b.cz - v.az) * nz) - ext(b, nx, nz) < 12) return false; }
    for (const q of streets) { // separating axes: world x, world z, the block's own two
      const x0 = q.x0 - 4, x1 = q.x1 + 4, z0 = q.z0 - 4, z1 = q.z1 + 4, rcx = (x0 + x1) / 2, rcz = (z0 + z1) / 2, rhx = (x1 - x0) / 2, rhz = (z1 - z0) / 2;
      if (Math.abs(b.cx - rcx) > rhx + ext(b, 1, 0) || Math.abs(b.cz - rcz) > rhz + ext(b, 0, 1)) continue;
      if (Math.abs((rcx - b.cx) * b.ux + (rcz - b.cz) * b.uz) > b.hw + rhx * Math.abs(b.ux) + rhz * Math.abs(b.uz)) continue;
      if (Math.abs(-(rcx - b.cx) * b.uz + (rcz - b.cz) * b.ux) > b.hd + rhx * Math.abs(b.uz) + rhz * Math.abs(b.ux)) continue;
      return false;
    }
    for (const [sx, sz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) if (!onLand(b.cx + sx * b.hw * b.ux - sz * b.hd * b.uz, b.cz + sx * b.hw * b.uz + sz * b.hd * b.ux, 1)) return false;
    return true;
  };
  const overlaps = (a, b, m) => [[a.ux, a.uz], [-a.uz, a.ux], [b.ux, b.uz], [-b.uz, b.ux]].every(([nx, nz]) => Math.abs((a.cx - b.cx) * nx + (a.cz - b.cz) * nz) < ext(a, nx, nz) + ext(b, nx, nz) + m);
  const hitsBlock = (b) => { const rad = Math.hypot(b.hw, b.hd) + 2; for (let i = Math.floor((b.cx - rad) / HC) - 2; i <= Math.floor((b.cx + rad) / HC) + 2; i++) for (let j = Math.floor((b.cz - rad) / HC) - 2; j <= Math.floor((b.cz + rad) / HC) + 2; j++) for (const q of hash.get(i * 9973 + j) || []) if (overlaps(b, q, 1.5)) return true; return false; };
  const keepBlock = (b) => { const key = Math.floor(b.cx / HC) * 9973 + Math.floor(b.cz / HC); if (!hash.has(key)) hash.set(key, []); hash.get(key).push(b); };
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
      const w = bw * (0.8 + r() * 0.35), d = bd * (0.8 + r() * 0.35);
      const yaw = -(th + (r() - 0.5) * (isOld ? 0.24 : 0.06)), cy = Math.cos(-yaw), sy = Math.sin(-yaw);
      const blk = { cx, cz, hw: w / 2, hd: d / 2, ux: cy, uz: sy };
      if (!onLand(cx, cz, 0) || !clearOfRoads(blk) || hitsBlock(blk)) continue;
      keepBlock(blk);
      D.obb(cx, y + 0.12 + r() * 0.06, cz, w, 0.24 + r() * 0.06, d, yaw, 'pavecity'); // the block's kerb
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
  for (let t = 0; t < 7000; t++) {
    const cx = (r() * 2 - 1) * R, cz = (r() * 2 - 1) * R, w = 10 + r() * 16, d = 9 + r() * 14;
    if (!onLand(cx, cz, 0)) continue;
    const yaw = -(thetas[sector(cx, cz)] + (r() - 0.5) * 0.5), blk = { cx, cz, hw: w / 2, hd: d / 2, ux: Math.cos(-yaw), uz: Math.sin(-yaw) };
    if (!clearOfRoads(blk) || hitsBlock(blk)) continue;
    keepBlock(blk);
    const far = Math.max(Math.abs(cx), Math.abs(cz)) - S;
    const h = Math.max(3, Math.min(o.cap - y, far < 110 ? 3 + r() * Math.max(1, o.kill - y - 4) : 6 + r() * 26));
    D.obb(cx, y + 0.12 + r() * 0.06, cz, w, 0.25, d, yaw, 'pavecity');
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
  D.box(0, -18, 0, 26, 22, 26, 'toyface', { fit: 1 }); D.obb(0.5, -48, -0.5, 24, 38, 24, 0.2, 'toyface2', { fit: 1 }); D.box(-1, -78, 1, 36, 24, 36, 'toyface', { fit: 1 });
  // (the middle block is turned a little and no wider than the crate: a fall off any edge never passes through it)
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
  return { name: 'Crate', size: 'tiny', boxes: B.boxes, deco: D.boxes, killY: -50, sky: { top: 0xffd6ec, mid: 0xffd6ec, bot: 0xffd6ec, fog: 0xffd6ec }, fogNear: 90, fogFar: 700,
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
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) { D.box(sx * 30, -30.5, sz * 30, 6, 45, 6, 'rust'); D.box(sx * 30, -52.7, sz * 30, 9, 1, 9, 'white'); }
  for (const y of [-14, -27, -40]) for (const s2 of [-1, 1]) { D.add(-27, y - 0.6, s2 * 30 - 0.6, 27, y + 0.6, s2 * 30 + 0.6, 'hazard'); D.add(s2 * 30 - 0.6, y - 0.6, -27, s2 * 30 + 0.6, y + 0.6, 27, 'hazard'); }
  D.add(-27, -20, -27, 0, -19, 0, 'grid'); for (const [x, z, m] of [[-24, -24, 'containerr'], [-24, -12, 'containerb'], [-12, -24, 'containerg']]) D.add(x, -19, z, x + 6, -16.4, z + 2.5, m);
  D.box(38, -9, 20, 2, 18, 2, 'hazard'); D.add(36, 0, 19, 70, 1.2, 21, 'hazard'); D.box(67, -8, 20, 0.2, 16, 0.2, 'metal'); // the crane, a hook hanging
  D.add(44, -3, -2, 78, -1.6, 2, 'metal'); D.add(76, -1.6, -1.4, 79, 3, 1.4, 'rust'); D.add(76.4, 3, -1, 78.6, 6.5, 1, 'neonyellow'); D.add(76.9, 6.5, -0.5, 78.1, 8.6, 0.5, 'neonred'); // the flare
  for (const [x, z] of [[-520, -360], [610, 240], [-200, 640]]) { for (const sx of [-1, 1]) for (const sz of [-1, 1]) D.box(x + sx * 14, -28, z + sz * 14, 4, 50, 4, 'rust'); D.add(x - 22, -3, z - 22, x + 22, 0, z + 22, 'grid'); D.box(x + 18, 6, z, 2, 12, 2, 'neonyellow'); } // the other rigs
  D.add(260, -53.6, -120, 330, -47, -104, 'toyred'); D.add(306, -47, -118, 324, -40, -106, 'white'); D.add(307, -44, -118.1, 323, -42, -105.9, 'glass'); // a ship going past
  for (const [x, z, al, ad] of [[0, -50, 'x', 'adcity2'], [0, 50, 'x', 'adcity4'], [-50, 0, 'z', 'adcity1'], [50, 0, 'z', 'adcity6']]) adBoard(D, x, z, -14, al, ad, 30, 12);
  return { name: 'Platform', size: 'small', boxes: B.boxes, deco: D.boxes, killY: -50, floorY: -53,
    sky: { top: 0x5a6070, mid: 0xb8bcc8, bot: 0x2a2c33, fog: 0xb8bcc8 }, fogNear: 80, fogFar: 320,
    spawns: [[-35, 0.1, -35], [35, 0.1, 35], [-35, 0.1, 35], [35, 0.1, -35], [0, 0.1, -35], [0, 0.1, 35], [-35, 0.1, 0], [35, 0.1, 0]] };
}

// ------------------------------------------------------------ ROOFTOP: the top of a skyscraper with a glass penthouse
function rooftop() {
  const B = builder();
  const r = rng(77);
  B.box(0, -86, 0, 64, 172, 64, 'office');
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
    B.box(x, -162, z, w, 20, w, 'office'); // a foundation down to the (lowered) street
    spawns.push([x + 3, ry + 0.1, z + 3]);
    plan.push([x, z, w, w, h, t]); roofs[`${x},${z}`] = ry;
  }
  // the look (render-only): a street far below instead of the void, neon crowns, cables with ads, a sign on our roof
  const D = builder();
  streetLevel(D, -162, plan.map(([x, z, w, d]) => ({ x, z, w, d })), { xs: [-140, -55, 55, 140], zs: [-140, -55, 55, 140], w: 18 }, 180, r);
  cityDress(D, plan, roofs, -152, r);
  cityBeyond(D, -162, 180, 520, rng(5151), { kill: -150, cap: -14, shore: 340, avenues: [[0, -260, 0.62], [260, 0, -0.95], [-240, 60, 1.4], [-200, -300, 2.6]], streets: gridOut([-140, -55, 55, 140], [-140, -55, 55, 140], 180, 200) });
  return { name: 'Rooftop', size: 'medium', boxes: B.boxes, deco: D.boxes, killY: -150, floorY: -170, cityR: 520, cityCap: -14,
    haze: { k: 0.92, top: -25, bottom: -162, dist: 95, color: 0x6a5c9c }, // look down: the city lights through a night smog
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
  L(7.15, 0, -6, 13, 0.1, 1.05, 'concrete'); // (wall face to wall face: no grass slot, no face shared with a wall end)
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
  if (!o.noFence) {
    L(-8, 0, 13.9, -1.2, fy, 14.1, 'picket'); L(1.2, 0, 13.9, 14, fy, 14.1, 'picket');
    L(-8.1, 0, 6.2, -7.9, fy, 13.9, 'picket');
    L(13.9, 0, 1.4, 14.1, fy, 11, 'picket');
  }
  lollipop(L, -4, 12.8, 4 + r() * 2, r);
  if (!o.noPad) L(2.5, 0, 8.5, 5, 0.25, 11, 'pad', { pad: [0, 21, -4] });
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
  const y0 = 2 + ((h * 7.31) % 0.4); // each tree's lowest branches at their own height (neighbours' undersides never in one plane)
  L.B(x, y0 / 2, z, 0.5, y0, 0.5, 'wood');
  for (let i = 0; i < 4; i++) L.B(x, y0 + (i + 0.5) * h / 4, z, 4.2 - i * 0.95, h / 4, 4.2 - i * 0.95, i % 2 ? 'leaves2' : 'hedge');
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
function truck(B, x0, z0, livery = 'adtruck', step = true) { // (step: the crate to climb in by; not when it's backed onto a dock)
  const z1 = z0 + 2.5;
  for (const wx of [x0 + 1.4, x0 + 5.6, x0 + 8.9]) for (const [a, b] of [[z0 - 0.08, z0 + 0.4], [z1 - 0.4, z1 + 0.08]]) B.add(wx - 0.5, 0, a, wx + 0.5, 1.0, b, 'tire');
  B.add(x0 + 0.3, 0.5, z0 + 0.3, x0 + 9.9, 0.95, z1 - 0.3, 'metal');
  B.add(x0, 0.95, z0, x0 + 7.4, 1.1, z1, 'wood'); // box floor
  B.add(x0, 1.1, z0, x0 + 7.4, 3.8, z0 + 0.12, 'truckbox'); B.add(x0, 1.1, z1 - 0.12, x0 + 7.4, 3.8, z1, 'truckbox');
  B.add(x0 + 7.28, 1.1, z0 + 0.12, x0 + 7.4, 3.8, z1 - 0.12, 'truckbox');
  B.add(x0, 3.8, z0, x0 + 7.4, 3.95, z1, 'truckbox');
  B.add(x0 + 0.05, 3.3, z0 + 0.12, x0 + 0.3, 3.8, z1 - 0.12, 'metal'); // the roller door, rolled up
  B.add(x0 + 1, 1.15, z0 - 0.03, x0 + 6.6, 3.3, z0, livery, { fit: 1 }); B.add(x0 + 1, 1.15, z1, x0 + 6.6, 3.3, z1 + 0.03, livery, { fit: 1 });
  if (step) B.add(x0 - 1.1, 0, z0 + 0.5, x0, 0.55, z1 - 0.5, 'crate'); // step in
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

// ---- the suburb kit (both Suburb layouts)
// a show home you can't go into (the S&D layout keeps its lanes clean): solid, with painted-on windows and door, the
// stepped toy roof, porch, garage, the car on the drive, and its own fences down both sides to the back of the lot
function facadeHouse(B, D, ox, oz, rot, o, r) {
  const L = B.local(ox, oz, rot), Ld = D.local(ox, oz, rot);
  L(-7, 0, -6, 7, 6.8, 6, o.siding);
  L(-7.2, 6.8, -6.2, 7.2, 7.1, 6.2, o.roof); L(-6.3, 7.1, -5.3, 6.3, 7.55, 5.3, o.roof); L(-4.6, 7.55, -3.8, 4.6, 8.0, 3.8, o.roof);
  L(-2.8, 8.0, -2.2, 2.8, 8.45, 2.2, o.roof); L(3.4, 7.55, 1.5, 4.4, 9.4, 2.5, 'brick');
  for (const y of [1.1, 4.5]) for (const x of [-5, -2.2, 2.2, 5]) if (!(y < 2 && Math.abs(x) < 3)) { Ld(x - 0.75, y, -6.05, x + 0.75, y + 1.2, -6.0, 'glass'); Ld(x - 0.75, y, 6.0, x + 0.75, y + 1.2, 6.05, 'glass'); }
  for (const y of [1.1, 4.5]) for (const z of [-3, 3]) { Ld(-7.05, y, z - 0.75, -7.0, y + 1.2, z + 0.75, 'glass'); Ld(7.0, y, z - 0.75, 7.05, y + 1.2, z + 0.75, 'glass'); }
  Ld(-1, 0.25, -6.06, 1, 2.6, -6.0, 'wood'); Ld(-1.4, 2.62, -6.12, 1.4, 3.0, -6.06, 'signopen', { fit: 1 });
  L(-3, 0, -7.6, 3, 0.25, -6, 'wood'); L(-2.9, 0.25, -7.5, -2.6, 3.0, -7.2, 'wood'); L(2.6, 0.25, -7.5, 2.9, 3.0, -7.2, 'wood'); L(-3.2, 3.0, -7.8, 3.2, 3.25, -6.15, o.roof);
  L(7, 0, -6, 13, 3.2, 1.2, 'brick'); L(6.8, 3.2, -6.2, 13.2, 3.5, 1.4, 'roofg'); Ld(7.6, 0.1, -6.06, 12.4, 2.7, -6.0, 'metal');
  L(7.4, 0, -17, 12.8, 0.12, -6, 'sidewalk'); car(L, 10.1, -11.5, 1, o.car);
  L(-1, 0, -17, 1, 0.12, -7.65, 'sidewalk'); L.B(2.2, 0.6, -15.5, 0.15, 1.2, 0.15, 'wood'); L.B(2.2, 1.35, -15.5, 0.5, 0.35, 0.8, 'toyblue');
  L(-8.1, 0, -6, -7.9, 2.2, 14, 'wood'); L(13.9, 0, -6, 14.1, 2.2, 14, 'wood'); L(13, 0, 1.2, 13.9, 2.2, 1.4, 'wood'); // the lot's side fences
  lollipop(L, -3.5, 10.5, 4.2 + r() * 1.5, r); if (o.yard === 'toy') L(1.5, 0, 8, 4.5, 3, 11, 'toyface', { fit: 1 });
}
// a tall wooden privacy fence along x (z fixed) or z (x fixed), with gaps: gates [[a, b], ...] along it
function woodFence(B, axis, fixed, a0, a1, gates = [], h = 2.2, side = 0) { // side +-1: the posts stand proud on that side only (the other face is flat: nothing to snag on)
  const cuts = [a0, ...gates.flat(), a1], p0 = side > 0 ? 0.09 : 0.16, p1 = side < 0 ? 0.09 : 0.16;
  for (let i = 0; i + 1 < cuts.length; i += 2) {
    const s0 = cuts[i], s1 = cuts[i + 1]; if (s1 - s0 < 0.05) continue;
    if (axis === 'x') B.add(s0, 0, fixed - 0.1, s1, h, fixed + 0.1, 'wood'); else B.add(fixed - 0.1, 0, s0, fixed + 0.1, h, s1, 'wood');
    for (let t = s0; t <= s1 + 0.01; t += 2.4) { if (axis === 'x') B.add(t - 0.08, 0, fixed - p0, t + 0.08, h + 0.15, fixed + p1, 'wood'); else B.add(fixed - p0, 0, t - 0.08, fixed + p1, h + 0.15, t + 0.08, 'wood'); }
  }
}
// round the play area bx = [x0, z0, x1, z1]: a ring of trees you bump into right on the edge, rows past it that only exist
// to look at, then a forest that thins into the fog, green hills, the water tower, a power line, and the roads out west
// (roads: [{ z, hw }], the middle of each and its half width) through gaps in the trees, on out past the fog
function suburbOutside(B, D, r, bx, roads = [], clear = []) {
  const [x0, z0, x1, z1] = bx, W = B.local(0, 0, 0), Dw = D.local(0, 0, 0);
  const onRoad = (x, z) => (x < x0 + 2 && roads.some((q) => Math.abs(z - q.z) < q.hw + 4)) || clear.some((c) => Math.hypot(x - c[0], z - c[1]) < 5); // (and out of the fence's gateways)
  const ring = (T, a0, b0, a1, b1, step, jit) => {
    const t = (x, z) => { if (!onRoad(x, z)) (r() < 0.4 ? conifer : lollipop)(T, x, z, 5 + r() * 3, r); };
    for (let x = a0; x <= a1; x += step) for (const z of [b0, b1]) t(x + (r() - 0.5) * jit, z + (r() - 0.5) * jit);
    for (let z = b0 + step; z < b1; z += step) for (const x of [a0, a1]) t(x + (r() - 0.5) * jit, z + (r() - 0.5) * jit);
  };
  ring(W, x0 - 3, z0 - 3, x1 + 3, z1 + 3, 6.5, 2);
  ring(Dw, x0 - 10, z0 - 10, x1 + 10, z1 + 10, 5.5, 3); ring(Dw, x0 - 17, z0 - 17, x1 + 17, z1 + 17, 6, 4);
  const fr = rng(4343), pylonZ = z0 - 100;
  const ftree = (x, z, h, y = 0) => { const L2 = D.local(x, z, 0, y), m = fr() < 0.5 ? 'leaves' : fr() < 0.6 ? 'hedge' : 'leaves2';
    if (fr() < 0.5) { L2.B(0, h / 2, 0, 0.6, h, 0.6, 'wood'); L2.B(0, h + 0.8, 0, 3.4 + fr(), 2.2, 3.4 + fr(), m); L2.B(0, h + 2.4, 0, 2.2, 1.2, 2.2, m); }
    else { const y0 = 1.7 + ((h * 7.31) % 0.6); L2.B(0, y0 / 2, 0, 0.5, y0, 0.5, 'wood'); L2.B(0, y0 + h * 0.3, 0, 4.4, h * 0.6, 4.4, m); L2.B(0, y0 + h * 0.75, 0, 2.6, h * 0.5, 2.6, m); } }; // (canopy bottoms at their own heights)
  for (let x = x0 - 220; x <= x1 + 220; x += 8) for (let z = z0 - 220; z <= z1 + 220; z += 8) {
    const e = Math.max(x0 - 20 - x, x - x1 - 20, z0 - 20 - z, z - z1 - 20); // how far past the ring
    if (e < 0 || (x < x0 && roads.some((q) => Math.abs(z - q.z) < q.hw + 8)) || Math.abs(z - pylonZ) < 11) continue;
    if (fr() < (e < 40 ? 0.85 : e < 110 ? 0.5 : 0.24)) ftree(x + (fr() - 0.5) * 6, z + (fr() - 0.5) * 6, 5 + fr() * 5);
  }
  for (const [x, z, w, h] of [[-250, -200, 90, 18], [230, 190, 110, 24], [300, -60, 70, 14], [-310, 120, 80, 20], [60, 250, 100, 16], [-120, 240, 70, 12]]) {
    for (let i = 0; i < 4; i++) { const k = 1 - i * 0.22; D.box(x + i * 3, (h / 4) * (i + 0.5), z - i * 2, w * k, h / 4, w * 0.7 * k, 'grass'); }
    for (let t = 0; t < 7; t++) ftree(x + (fr() - 0.5) * w * 0.4, z + (fr() - 0.5) * w * 0.3, 5 + fr() * 4, h);
  }
  { const T = D.local(205, -175, 0); // the water tower
    for (const sx of [-1, 1]) for (const sz of [-1, 1]) T.B(sx * 4, 13, sz * 4, 0.7, 26, 0.7, 'metal');
    for (const y of [8, 17]) { T(-4, y, -4.1, 4, y + 0.3, -3.9, 'metal'); T(-4, y, 3.9, 4, y + 0.3, 4.1, 'metal'); T(-4.1, y, -4, -3.9, y + 0.3, 4, 'metal'); T(3.9, y, -4, 4.1, y + 0.3, 4, 'metal'); }
    T(-6, 26, -6, 6, 34, 6, 'toyteal'); T(-4.5, 34, -4.5, 4.5, 36, 4.5, 'toyteal'); T(-0.6, 36, -0.6, 0.6, 38, 0.6, 'metal');
    T(-5, 28.5, -6.15, 5, 32.5, -6.02, 'adwater', { fit: 1 }); T(-6.6, 25.6, -6.6, 6.6, 26, 6.6, 'grid');
  }
  for (let x = -330; x <= 330; x += 66) { // a power line on pylons
    const P = D.local(x, pylonZ, 0);
    P.B(0, 7, 0, 3.6, 14, 3.6, 'metal'); P.B(0, 20, 0, 2.2, 12, 2.2, 'metal'); P.B(0, 29, 0, 1.2, 6, 1.2, 'metal');
    P.B(0, 22, 0, 0.4, 0.4, 13, 'metal'); P.B(0, 28, 0, 0.4, 0.4, 10, 'metal');
    if (x + 66 <= 330) for (const [y, dz] of [[21.4, -6.2], [21.4, 6.2], [27.4, -4.7], [27.4, 4.7]]) D.add(x, y, pylonZ + dz - 0.05, x + 66, y + 0.08, pylonZ + dz + 0.05, 'tire');
  }
  horizon(D, -260, -200, 260, 200, 1500, 'grass');
  for (const q of roads) { for (let x = -250; x < x0 - 20; x += 30) streetlight(Dw, x, q.z + q.hw + 2, -1); D.add(-1500, 0, q.z - q.hw, -260, 0.1, q.z + q.hw, 'roadx'); }
}

// ------------------------------------------------------------ SUBURB S&D: plant & defuse on HOA election night.
// an original layout on the bomb-map rules, in the show-home suburb. attackers get off the bus at the entrance (west),
// defenders hold the far end from the HOA clubhouse (east), which hides their spawn from the street. three lanes:
//   north: the back alley behind the north row (bins, sheds, a camper van), ends in A main: the building site's gate
//   mid:   the main street (a planted median, the truck, parked cars) into the cul-de-sac, which joins both sites
//   south: the creek path behind the south row, ends at the mini-mart's side door: B main
// one open house in each row runs from the street to its lane (the rest are shut), so mid can split either way.
// A = the building site (frames, scaffold, a digger, plywood hoarding), B = the MEGA-MART EXPRESS (inside, aisles)
function suburbSD() {
  const B = builder(), D = builder();
  const { add, box } = B;
  const r = rng(4747), W = B.local(0, 0, 0), Dw = D.local(0, 0, 0);
  const bounds = [-84, -60, 82, 60];
  add(-260, -3, -200, 260, 0, 200, 'grass');
  suburbOutside(B, D, r, bounds, [{ z: 0, hw: 7 }]);
  // ---- the main street (on west through the trees to nowhere), sidewalks, the cul-de-sac at the east end
  add(-140, 0, -7, 14, 0.1, 7, 'roadx');
  add(-140, 0, -10, 14, 0.25, -7, 'sidewalk'); add(-140, 0, 7, 14, 0.25, 10, 'sidewalk');
  add(14, 0, -17.6, 56, 0.1, 17.6, 'road');
  for (let x = -50; x <= 2; x += 13) { add(x - 2.5, 0.1, -1, x + 2.5, 0.5, 1, 'stone'); add(x - 2.3, 0.5, -0.8, x + 2.3, 1.45, 0.8, 'hedge'); } // the median: planters you can duck behind
  for (const x of [-56, -30, -4]) lollipop(W, x, 0, 5.5, r);
  for (let x = -70; x <= 10; x += 20) { streetlight(W, x, 8.9, -1); streetlight(W, x + 10, -8.9, 1); }
  truck(B, -24, 2.2, 'adtruck2'); // the box truck, back open (a crate to climb in)
  for (const [x, z, c] of [[-44, 5.3, 'carblue'], [-12, -5.3, 'carblack'], [6, 5.3, 'cargreen'], [-36, -5.3, 'carwhite']]) car(W, x, z, 0, c);
  // the cul-de-sac: the founder's statue on its planter (a big googly toy), hedges, the mailboxes
  add(29, 0.1, -5, 39, 0.6, 5, 'stone'); add(29.5, 0.6, -4.5, 38.5, 0.7, 4.5, 'lawn');
  add(32.6, 0.7, -1.4, 35.4, 2.6, 1.4, 'chrome'); add(32.2, 2.6, -1.8, 35.8, 6.2, 1.8, 'toyface', { fit: 1 });
  for (const [x, z] of [[30.5, -3.5], [37.5, 3.5], [30.5, 3.5], [37.5, -3.5]]) W.B(x, 1.3, z, 1.2, 1.2, 1.2, 'hedge');
  for (let i = 0; i < 4; i++) add(44 + i * 1.3, 0.1, -12.5, 45 + i * 1.3, 1.5, -11.8, i % 2 ? 'toyteal' : 'toypink');
  W(46, 0.1, 9, 50, 1.2, 11.5, 'hedge');
  // the HOA gate where the street meets the cul-de-sac: two gatehouses leave one 8 m way through (mid's choke), the
  // statue right behind it (no straight look in), the booms stuck up
  for (const [z0, z1] of [[-17.8, -4], [4, 17.8]]) {
    add(13.4, 0, z0, 17.4, 3.4, z1, 'sidelilac'); add(13.2, 3.4, z0 - 0.2, 17.6, 3.7, z1 + 0.2, 'roofpink');
    D.add(13.36, 1.2, (z0 + z1) / 2 - 1.5, 13.4, 2.4, (z0 + z1) / 2 + 1.5, 'glass');
  }
  D.add(15.2, 3.7, -4.2, 15.6, 8.2, -3.8, 'hazard'); D.add(15.2, 3.7, 3.8, 15.6, 8.2, 4.2, 'hazard');
  D.add(13.3, 2.6, -3.6, 13.36, 3.3, 3.6, 'adhoa', { fit: 1 });

  // ---- the house rows: north (facing south) and south (facing north). the middle north house and the east south house
  // are open (front door -> back door -> a gate in the fence behind): the ways from the street to the alley and the creek
  const look = [
    { siding: 'sidepink', roof: 'roofteal', car: 'carblue', yard: 'toy' }, { siding: 'sidelemon', roof: 'roofpink', car: 'carred' },
    { siding: 'sidelilac', roof: 'roof', car: 'cargreen' }, { siding: 'sidemint', roof: 'roof', car: 'carwhite' },
    { siding: 'sideorange', roof: 'roofteal', car: 'carblack', yard: 'toy' }, { siding: 'blue', roof: 'roofpink', car: 'caryellow' },
  ];
  const openN = -19.4, openS = -2.8;
  [-42, openN, 3.2].forEach((x, i) => (x === openN ? home(B, x, -27, 2, { ...look[i], yard: 'tub', noPad: true, noFence: true }, r) : facadeHouse(B, D, x, -27, 2, look[i], r)));
  [-48, -25.4, openS].forEach((x, i) => (x === openS ? home(B, x, 27, 0, { ...look[i + 3], yard: 'pool', noPad: true, noFence: true }, r) : facadeHouse(B, D, x, 27, 0, look[i + 3], r)));
  for (const [x, rot] of [[openN, 2], [openS, 0]]) { const L = B.local(x, rot ? -27 : 27, rot); L(-8.1, 0, -6, -7.9, 2.2, 14, 'wood'); L(13.9, 0, -6, 14.1, 2.2, 14, 'wood'); L(13, 0, 1.2, 13.9, 2.2, 1.4, 'wood'); }
  woodFence(B, 'x', -41.3, -60, 13.2, [[-24.2, -20.2]]); // the backs of the north lots, a gate behind the open house
  woodFence(B, 'x', 41.3, -60, 13.2, [[-2.3, 1.7]]); // the south lots
  woodFence(B, 'z', 13.1, -41.2, -10.3); woodFence(B, 'z', 13.1, 10.3, 41.2); // the rows' east ends: no way round
  // ---- ATTACKERS' SPAWN: the bus stop at the entrance. the bus they came on screens the street
  prop(B.local(-63, 0, 1), 'bus', 0, 0, 0); // (the Blender bus over its two boxes, broadside across the road)
  barrier(B, -56, -8.5, true, 2.6); barrier(B, -56, 8.5, true, 2.6); // (the ways out either side of the bus stay 4 m wide)
  const SH = B.local(-74, -13, 0); // the bus shelter
  SH(-3, 0, -0.9, 3, 0.3, 0.9, 'concrete'); SH(-3, 0.3, 0.7, 3, 2.6, 0.9, 'glass'); SH(-3.2, 2.6, -1.1, 3.2, 2.8, 1.1, 'toyteal');
  SH(-3, 0.3, -0.9, -2.85, 2.6, 0.7, 'chrome'); SH(2.85, 0.3, -0.9, 3, 2.6, 0.7, 'chrome'); SH(-2, 0.3, 0.3, 2, 0.75, 0.7, 'seat');
  adBoard(B, -76, 18, 0, 'x', 'adbig1'); for (let z = -9.5; z < 9.5; z += 3.4) add(-86, 0.1, z, -85, 1.1, z + 2.2, 'jersey');
  const att = [[-78, 0.2, -5], [-78, 0.2, 0], [-78, 0.2, 5], [-71, 0.2, -6], [-71, 0.2, -1.5], [-71, 0.2, 3], [-71, 0.2, 7]];
  // the west ends of both lanes, round the corner from the spawn: a shed, the bins
  W(-70, 0, -34, -64, 2.6, -29, 'wood'); W(-70.2, 2.6, -34.2, -63.8, 2.9, -28.8, 'roofg'); W(-68, 0, 26, -65.4, 1.5, 28, 'containerg');

  // ---- NORTH: the back alley, A long
  add(-84, 0, -58, 14, 0.08, -41.4, 'asphalt');
  for (const [x, z, m] of [[-54, -47, 'containerg'], [-36, -55, 'containerb'], [-8, -46, 'toypink'], [2, -55, 'containerg']]) W(x, 0.08, z - 1, x + 2.6, 1.5, z + 1, m); // bins
  { const V = B.local(-24, -51, 0); V(-3.2, 0.45, -1.2, 3.2, 3.0, 1.2, 'carwhite'); V(1.8, 1.5, -1.25, 3.25, 2.6, 1.25, 'glass'); V(-3.3, 3.0, -1.3, 2, 3.4, 1.3, 'toyorange'); for (const x of [-2, 2]) for (const z of [-1.25, 1.05]) V(x - 0.4, 0, z, x + 0.4, 0.8, z + 0.2, 'tire'); } // the camper van
  car(W, -44, -52, 0, 'burnt'); W(-14, 0.08, -57, -9, 2.8, -53, 'wood'); W(-14.2, 2.8, -57.2, -8.8, 3.1, -52.8, 'roofg'); // a burnt-out car, a shed
  for (const x of [-62, -30, 8]) { W(x, 0.08, -42.3, x + 0.9, 1.0, -41.5, 'barrel'); }

  // ---- A: the building site (plywood hoarding, a frame going up, a scaffold, a digger, sand)
  add(13.3, 0, -57.95, 13.5, 2.4, -54.5, 'plywood'); add(13.3, 0, -44.5, 13.5, 2.4, -41.2, 'plywood'); // west: A main, the site gate (from the alley)
  add(13.3, 0, -41.2, 56, 2.4, -41.0, 'plywood'); // (the hoarding runs on behind the last north house)
  add(13.3, 0, -18.2, 28, 2.4, -18.0, 'plywood'); add(33, 0, -18.2, 56, 2.4, -18.0, 'plywood'); // south: the gate from the cul-de-sac
  add(55.8, 0, -58, 56, 2.4, -38, 'plywood'); add(55.8, 0, -32, 56, 2.4, -18.2, 'plywood'); // east: the defenders' gate
  for (const [x, z, a] of [[20, -18.3, 'adbig1'], [46, -18.3, 'adfun']]) add(x - 5, 0.6, z - 0.06, x + 5, 2.2, z, a, { fit: 1 });
  add(13.5, 0, -57.9, 55.8, 0.03, -18.2, 'dirt'); add(20, 0, -36, 42, 0.3, -24, 'concrete'); // churned-up dirt, the slab
  for (let x = 21; x <= 41; x += 2) for (const z of [-35, -25]) if (Math.abs(x - 31) > 2) box(x, 1.95, z, 0.15, 3.3, 0.15, 'plywood'); // a frame going up
  for (let z = -33; z <= -27; z += 2) for (const x of [21, 41]) box(x, 1.95, z, 0.15, 3.3, 0.15, 'plywood');
  add(20.9, 3.6, -35.1, 41.1, 3.75, -34.9, 'plywood'); add(20.9, 3.6, -25.1, 41.1, 3.75, -24.9, 'plywood');
  add(20.9, 3.6, -34.9, 21.1, 3.75, -25.1, 'plywood'); add(40.9, 3.6, -34.9, 41.1, 3.75, -25.1, 'plywood');
  add(21.1, 3.75, -34.9, 31, 3.95, -25.1, 'plywood'); stairs(W, 22.5, 24, -26.2, -1, 0.3, 3.95, 'plywood', 0.55); // half an upstairs
  for (const [x, z] of [[46, -50], [46, -44], [50, -50], [50, -44]]) W.B(x, 2.9, z, 0.2, 5.8, 0.2, 'hazard'); // the scaffold tower
  add(45.6, 2.8, -50.4, 50.4, 3, -43.6, 'grid'); add(45.6, 5.8, -50.4, 50.4, 6, -43.6, 'grid');
  excavator(B, 30, -50, 1); for (let i = 0; i < 4; i++) add(38 + i * 0.6, 0.1, -55 + i * 0.4, 44 - i * 0.6, 0.45 + i * 0.35, -51 - i * 0.3, 'sand');
  add(51, 0, -30, 53.4, 2.6, -27.6, 'toyblue'); palletLoad(B, 47, -24, 1); palletLoad(B, 18, -30); W(15, 0, -50, 18, 1.2, -47, 'crate');
  add(18, 0, -38, 21, 1.6, -36.6, 'containerg'); // a skip
  siteBoard(D, 33.5, 3.2, -57.7, 'x', 'sitea', 4); siteBoard(D, 30.5, 2.6, -17.92, 'x', 'sitea', 2);

  // ---- the turnaround is the defenders' side: the HOA clubhouse hides their spawn from the street
  add(56, 0, -12, 61, 7.2, 12, 'sidelilac'); add(55.6, 7.2, -12.4, 61.4, 7.6, 12.4, 'roofpink');
  for (let z = -9; z <= 9; z += 4.5) for (const y of [1.2, 4.4]) { D.add(55.94, y, z - 1, 55.98, y + 1.8, z + 1, 'glass'); D.add(61.02, y, z - 1, 61.06, y + 1.8, z + 1, 'glass'); }
  D.add(55.9, 3.0, -5, 55.95, 4.3, 5, 'adhoa', { fit: 1 });
  W.B(64, 4, -14, 0.2, 8, 0.2, 'chrome'); W(64.1, 6, -14.1, 66.5, 7.6, -13.9, 'flagcorp', { fit: 1 });
  add(64, 0, -12, 80, 0.06, 12, 'asphalt'); for (let z = -10; z <= 10; z += 4) add(66, 0.06, z, 80, 0.07, z + 0.15, 'white');
  for (const [z, c] of [[-10, 'carred'], [-2, 'carblue'], [6, 'caryellow']]) car(W, 77, z, 1, c);
  const def = [[66, 0.2, -8], [66, 0.2, -3], [66, 0.2, 2], [66, 0.2, 7], [71, 0.2, -6], [71, 0.2, 0], [71, 0.2, 6]];
  // the paths round the clubhouse: north to A's back gate, south to the mini-mart's back door
  W(68, 0, -32, 70.6, 1.5, -30, 'containerb'); W(66, 0, -46, 70, 1.2, -44, 'hedge'); lollipop(W, 74, -50, 5, r);
  W(68, 0, 30, 70.6, 1.5, 32, 'containerg'); W(66, 0, 46, 70, 1.2, 48, 'hedge'); lollipop(W, 74, 50, 5, r);

  // ---- B: the MEGA-MART EXPRESS (inside: aisles, the tills, the fridges, the stockroom), its car park
  const SX0 = 24, SX1 = 50, SZ0 = 30, SZ1 = 54, SH2 = 7.2;
  wall(W, 'x', SZ0, SX0 - 0.25, SX1 + 0.25, 0, SH2, 0.5, 'brick', [{ a: 33, b: 38, y0: 0, y1: 3.2 }, { a: 26, b: 31, y0: 1, y1: 2.6 }, { a: 40, b: 47, y0: 1, y1: 2.6 }]); // front: doors + big windows
  wall(W, 'x', SZ1, SX0 - 0.25, SX1 + 0.25, 0, SH2, 0.5, 'brick');
  wall(W, 'z', SX0, SZ0 + 0.25, SZ1 - 0.25, 0, SH2, 0.5, 'brick', [{ a: 43, b: 47.5, y0: 0, y1: 3.2 }]); // west: B main, the side door
  wall(W, 'z', SX1, SZ0 + 0.25, SZ1 - 0.25, 0, SH2, 0.5, 'brick', [{ a: 36, b: 40, y0: 0, y1: 3.2 }]); // east: the loading door
  add(SX0 - 0.25, SH2, SZ0 - 0.25, SX1 + 0.25, SH2 + 0.4, SZ1 + 0.25, 'roofg');
  add(SX0 + 0.25, 0, SZ0 + 0.25, SX1 - 0.25, 0.03, SZ1 - 0.25, 'floorcyan');
  D.add(27, 3.6, SZ0 - 0.31, 47, 6, SZ0 - 0.27, 'adstore', { fit: 1 });
  for (const x of [29, 34, 39, 44]) add(x - 0.5, 0.03, 38, x + 0.5, 1.9, 48, 'shelfstock'); // aisles
  add(26, 0.03, 32, 31, 1.1, 33.2, 'wood'); add(40, 0.03, 32, 45, 1.1, 33.2, 'wood'); // the tills
  add(25, 0.03, 52.4, 49, 2.4, 53.7, 'chrome'); for (let x = 25.5; x < 49; x += 3) D.add(x, 0.3, 52.36, x + 2.4, 2.1, 52.4, 'glass'); // the fridges
  add(44, 0.03, 48.6, 49.6, 2.6, 49, 'brick'); add(44, 0.03, 49, 44.4, 2.6, 52.3, 'brick'); // the stockroom corner
  cratePile(B, 45, 49.6, 5, r); palletLoad(B, 27, 49);
  siteBoard(D, 37, 3.4, SZ1 - 0.33, 'x', 'siteb', 3.4); siteBoard(D, SX0 - 0.33, 3.8, 45.2, 'z', 'siteb', 2.2);
  for (let x = 28; x <= 46; x += 6) { D.add(x - 0.8, SH2 - 0.6, 43 - 0.3, x + 0.8, SH2 - 0.45, 43 + 0.3, 'lamp'); }
  add(14, 0, 17.6, 56, 0.12, 29.7, 'asphalt'); for (let x = 16; x <= 52; x += 4) add(x, 0.12, 22, x + 0.15, 0.13, 28, 'white'); // the car park
  for (const [x, c] of [[19, 'carred'], [31, 'carwhite'], [43, 'cargreen']]) car(W, x, 25, 1, c);
  for (let i = 0; i < 3; i++) W(51 + i * 0.75, 0.12, 20, 51.6 + i * 0.75, 1.1, 21.2, 'chrome'); // trolleys
  W(52.3, 0.12, 25, 54.9, 1.6, 27, 'containerg');

  // ---- SOUTH: the creek path, B long
  add(-84, 0, 47, 24, 0.02, 50, 'sand'); add(-84, 0.02, 47.6, 24, 0.05, 49.4, 'water'); // a little creek you splash through
  for (const [x, z] of [[-60, 44], [-40, 54], [-18, 45], [-2, 54], [16, 44]]) { W.B(x, 0.7, z, 2.4, 1.4, 1.6, 'hedge'); W.B(x + 1.6, 0.4, z + 0.6, 1.1, 0.8, 1, 'rock'); } // reeds, rocks
  W(-50, 0, 51.5, -44, 0.9, 52.6, 'wood'); W(-28, 0, 43, -26, 1.1, 46, 'rock'); W(6, 0, 51, 9, 1.4, 53, 'wood'); // a log, a boulder, a bench
  W(18, 0, 50.5, 20, 2.2, 56, 'wood'); W(20, 0, 41.4, 23.8, 1.2, 42.9, 'containerg'); // by the mini-mart's side door
  woodFence(B, 'x', 34, 13.2, 23.75); // the side yard by the store is a dead end to its door, not a way round to the car park

  const spawns = [[-50, 0.2, -48], [-20, 0.2, -45], [4, 0.2, -50], [-40, 0.3, 4], [-6, 0.3, -4], [24, 0.2, 10], [-40, 0.2, 52], [-12, 0.2, 48],
    [10, 0.2, 54], [34, 0.4, -30], [44, 0.2, -10], [38, 0.2, 42], [72, 0.2, -36], [72, 0.2, 38], [-74, 0.2, 34], [-74, 0.2, -40]];
  let graph = null;
  const map = {
    name: 'Suburb', size: 'large', boxes: B.boxes, deco: D.boxes, killY: -60, bounds, ceiling: 7, floorY: -4,
    sky: { top: 0x2f7cf0, mid: 0xffd3ec, bot: 0x7a4a6a, fog: 0xffd3ec }, fogNear: 110, fogFar: 430,
    spawns, teamSpawns: { att, def },
    nav: {
      A: [
        [[-70, -16], [-70, -48], [-50, -50], [-30, -46], [-10, -50], [6, -48], [14, -49], [24, -46], [32, -42]], // the alley
        [[-66, -8], [-58, -7.5], [-40, -4], [-20, -4], [-19.4, -14], [-19.4, -19], [-19.4, -25], [-21.7, -31], [-21.7, -36], [-22.2, -44], [-10, -48], [14, -49], [24, -46], [32, -42]], // the street, the open house
        [[-66, -8], [-58, -7.5], [-40, -4], [-10, -3], [8, 0], [15.4, 0], [22, -12], [30.5, -15], [30.5, -21], [32, -30]], // the street, the HOA gate, the cul-de-sac
      ],
      B: [
        [[-70, 16], [-70, 46], [-50, 48], [-30, 50], [-10, 49], [10, 48], [20, 46], [26, 45], [32, 44]], // the creek path
        [[-66, 8], [-58, 7.5], [-40, 4], [-10, 4], [-2.8, 14], [-2.8, 19], [-2.8, 25], [-0.5, 31], [-0.5, 36], [-0.3, 44], [12, 47], [20, 46], [26, 45], [32, 44]], // the street, the open house
        [[-66, 8], [-58, 7.5], [-40, 4], [-10, 3], [8, 0], [15.4, 0], [22, 12], [35.5, 22], [35.5, 28], [35.5, 34], [36, 40]], // the street, the HOA gate, the car park, the front door
      ],
    },
    sites: [{ id: 'A', min: [16, 0, -56], max: [54, 0, -20] }, { id: 'B', min: [25, 0, 31], max: [49, 0, 52] }],
    get graph() { return graph || (graph = buildNav(B.boxes, { x0: bounds[0] - 1, z0: bounds[1] - 1, n: bounds[2] - bounds[0] + 2, cell: 1, levels: [0], band: 0.5, keep: (x, z) => !outOfBounds(map, [x, 0, z]) })); },
  };
  return map;
}

// ------------------------------------------------------------ SUBURB: the show-home suburb for every mode but Plant & Defuse.
// built for flow: a loop street round the park, and everything loops round it. the park in the middle is the arena (the
// playground's climbing frame, the pond with its footbridge, the gazebo, the founder's statue); five houses face it from
// each side (every one open: front door, back door, garage, a trampoline onto the roof), the back lanes run behind them,
// and the two ends are the team sides: the corner store (west) and the building site (east)
function suburb() {
  const B = builder(), D = builder();
  const { add, box } = B;
  const r = rng(4242), W = B.local(0, 0, 0), Dw = D.local(0, 0, 0);
  const bounds = [-82, -62, 82, 62];
  add(-260, -3, -200, 260, 0, 200, 'grass');
  // the back fence's gaps (garden gates every 30-40 m, the lane ends, the two streets out): [along a, along b] per side
  // (each one clear inside: not behind a bin, the bleachers, the dock or the site office)
  const FN = [[-43.5, -40.5], [-1.5, 1.5], [28.5, 31.5]], FW = [[-62, -57.2], [-37, -34], [-26, -12], [12, 26], [50.5, 53.5], [57.2, 62]];
  const FE = [[-62, -57.2], [-43.5, -40.5], [-27, -24], [24, 27], [40.5, 43.5], [57.2, 62]];
  const gates = [ // [outside x, z, inside x, z] through the middle of each gap
    ...FN.flatMap(([a, b]) => [[(a + b) / 2, -66, (a + b) / 2, -58], [(a + b) / 2, 66, (a + b) / 2, 58]]),
    ...FW.map(([a, b]) => [-86, (Math.max(a, -60) + Math.min(b, 60)) / 2, -78, (Math.max(a, -60) + Math.min(b, 60)) / 2]),
    ...FE.map(([a, b]) => [86, (Math.max(a, -60) + Math.min(b, 60)) / 2, 78, (Math.max(a, -60) + Math.min(b, 60)) / 2]),
  ];
  suburbOutside(B, D, r, bounds, [{ z: -19, hw: 5 }, { z: 19, hw: 5 }], gates.map((g) => [g[0], g[1]]));
  // ---- the loop street (north and south run on out west through the trees: that's where the traffic comes from), kerbs
  add(-260, 0, -24, 58, 0.1, -14, 'roadx'); add(-260, 0, 14, 58, 0.1, 24, 'roadx'); // north + south
  add(-58, 0, -14, -46, 0.1, 14, 'roadz'); add(46, 0, -14, 58, 0.1, 14, 'roadz'); // west + east
  add(-140, 0, -26, 60, 0.25, -24, 'sidewalk'); add(-140, 0, 24, 60, 0.25, 26, 'sidewalk');
  add(-140, 0, -14, -58, 0.25, -12, 'sidewalk'); add(-140, 0, 12, -58, 0.25, 14, 'sidewalk');
  add(-60, 0, -12, -58, 0.25, 12, 'sidewalk'); add(58, 0, -24, 60, 0.25, 24, 'sidewalk');
  add(-46, 0, -14, 46, 0.25, -12, 'sidewalk'); add(-46, 0, 12, 46, 0.25, 14, 'sidewalk'); add(-46, 0, -12, -44, 0.25, 12, 'sidewalk'); add(44, 0, -12, 46, 0.25, 12, 'sidewalk');
  for (let x = -48; x <= 48; x += 24) { streetlight(W, x, -25.1, 1); streetlight(W, x + 12, 25.1, -1); }
  // cars parked along the outer kerbs, out of the traffic's way (it drives the two lanes inside them)
  for (const [x, z, c] of [[-44, -22.9, 'carblue'], [36, -22.9, 'carred'], [-8, -22.9, 'carwhite'], [-36, 22.9, 'cargreen'], [32, 22.9, 'caryellow'], [-6, 22.9, 'carblack']]) car(W, x, z, 0, c);
  // ---- the houses: five a side, all open (a trampoline in every yard throws you onto the roof)
  const looks = [
    ['sidepink', 'roofteal', 'carblue', 'pool'], ['sidelemon', 'roofpink', 'carred', 'toy'], ['sidelilac', 'roof', 'cargreen', 'tub'], ['sidemint', 'roofpink', 'carwhite', 'pool'], ['sideorange', 'roofteal', 'carblack', 'toy'],
    ['blue', 'roofpink', 'caryellow', 'tub'], ['sidepink', 'roof', 'carred', 'toy'], ['sidemint', 'roofteal', 'carblue', 'pool'], ['sidelemon', 'roof', 'cargreen', 'tub'], ['sidelilac', 'roofpink', 'carwhite', 'pool'],
  ].map(([siding, roof, car, yard]) => ({ siding, roof, car, yard }));
  const spawns = [];
  [-41.9, -19.3, 3.3, 25.9, 48.5].forEach((x, i) => { home(B, x, -43, 2, looks[i], r); const L = B.local(x, -43, 2); spawns.push(L.pt(3.5, 0.3, -3.5)); if (i % 2) spawns.push(L.pt(0, 0.3, 10)); });
  [-48.5, -25.9, -3.3, 19.3, 41.9].forEach((x, i) => { home(B, x, 43, 0, looks[i + 5], r); const L = B.local(x, 43, 0); spawns.push(L.pt(3.5, 0.3, -3.5)); if (i % 2 === 0) spawns.push(L.pt(0, 0.3, 10)); });
  // the back lanes behind both rows: bins, a camper van, a shed, a burnt-out car
  add(-82, 0, -62, 82, 0.08, -57.2, 'asphalt'); add(-82, 0, 57.2, 82, 0.08, 62, 'asphalt');
  for (const [x, z, m] of [[-50, -60, 'containerg'], [-6, -60, 'toypink'], [40, -60, 'containerb'], [-30, 59.6, 'containerb'], [14, 59.6, 'containerg']]) W(x, 0.08, z - 1, x + 2.6, 1.5, z + 1, m);
  { const V = B.local(20, -59.6, 0); V(-3.2, 0.45, -1.2, 3.2, 3.0, 1.2, 'carwhite'); V(1.8, 1.5, -1.25, 3.25, 2.6, 1.25, 'glass'); V(-3.3, 3.0, -1.3, 2, 3.4, 1.3, 'toyorange'); for (const x of [-2, 2]) for (const z of [-1.25, 1.05]) V(x - 0.4, 0, z, x + 0.4, 0.8, z + 0.2, 'tire'); }
  car(W, -54, 59.6, 0, 'burnt'); W(52, 0.08, 58, 57, 2.6, 61.4, 'wood'); W(51.8, 2.6, 57.8, 57.2, 2.9, 61.6, 'roofg');
  // the back fence round the whole estate (just outside the bounds: the trees are past it), with its gaps (FN/FW/FE up
  // top): knocked over it, there's usually a way back in before the countdown; a Jank Royale drop outside walks in.
  // the building site's end is plywood hoarding
  woodFence(B, 'x', -62.1, -82.2, 82.2, FN, 2.2, 1); woodFence(B, 'x', 62.1, -82.2, 82.2, FN, 2.2, -1); // (posts on the inside)
  woodFence(B, 'z', -82.1, -62, 62, FW, 2.2, 1);
  woodFence(B, 'z', 82.1, -62, -24, FE.slice(0, 3), 2.2, -1); woodFence(B, 'z', 82.1, 24, 62, FE.slice(3), 2.2, -1); add(82, 0, -24, 82.2, 2.4, 24, 'plywood');

  // ---- the park: the playground (west), the founder's plaza (middle), the pond with a footbridge and the gazebo (east)
  { const P = B.local(-24, 0, 0);
    P(-15, 0, -10, 15, 0.12, 10, 'rubber'); // the noisiest floor money can buy
    P(-15.2, 0, -10.2, 15.2, 0.6, -10, 'toyred'); P(-15.2, 0, 10, -2, 0.6, 10.2, 'toyred'); P(2, 0, 10, 15.2, 0.6, 10.2, 'toyred'); P(-15.2, 0, -10, -15, 0.6, 10, 'toyred');
    for (const [x, z] of [[-11, -6], [-7, -6], [-11, -2], [-7, -2]]) P.B(x, 2.7, z, 0.3, 5.4, 0.3, 'toyblue'); // a climbing frame with a slide off it
    P(-11.3, 2.9, -6.3, -6.7, 3.2, -1.7, 'toygreen'); P(-11.3, 5.4, -6.3, -6.7, 5.7, -1.7, 'toyred');
    stairs(P, -10.5, -9, 1.8, -1, 0.12, 3.2, 'toyorange', 0.5);
    for (let i = 0; i < 8; i++) P(-6.7 + i * 0.7, 0.12, -5.2, -6 + i * 0.7, 3.2 - i * 0.38, -2.8, 'toyteal');
    P(2, 0.12, 2, 9, 1.0, 2.3, 'toyblue'); P(2, 0.12, 8.7, 9, 1.0, 9, 'toyblue'); P(2, 0.12, 2.3, 2.3, 1.0, 8.7, 'toyblue'); P(8.7, 0.12, 2.3, 9, 1.0, 8.7, 'toyblue'); // the ball pit
    const balls = ['toyred', 'toygreen', 'toyorange', 'toyteal', 'toypink'];
    for (let i = 0; i < 5; i++) for (let j = 0; j < 5; j++) P.B(3.1 + i * 1.3, 0.35 + ((i + j) % 2) * 0.12, 3.1 + j * 1.3, 0.9, 0.5 + ((i * j) % 3) * 0.08, 0.9, balls[(i * 3 + j) % 5]);
    P(-13, 0.12, 3, -9, 4.12, 7, 'toyface', { fit: 1 });
    P.B(10, 2.6, -7, 0.3, 5.2, 0.3, 'toyred'); P.B(3, 2.6, -7, 0.3, 5.2, 0.3, 'toyred'); P(2.8, 5.2, -7.2, 10.2, 5.5, -6.8, 'toyred'); // swings
    for (const x of [4.5, 6.5, 8.5]) { P.B(x, 3.6, -7, 0.05, 3.2, 0.05, 'chrome'); P.B(x, 1.85, -7, 0.7, 0.12, 0.4, 'toyteal'); }
  }
  add(-5, 0, -5, 5, 0.4, 5, 'stone'); add(-4.5, 0.4, -4.5, 4.5, 0.5, 4.5, 'lawn'); // the founder's plaza
  add(-1.4, 0.5, -1.4, 1.4, 2.4, 1.4, 'chrome'); add(-1.8, 2.4, -1.8, 1.8, 6, 1.8, 'toyface', { fit: 1 }); add(-0.8, 0.9, -1.43, 0.8, 1.7, -1.4, 'plaque', { fit: 1 });
  for (const [x, z] of [[-3.5, -3.5], [3.5, 3.5], [-3.5, 3.5], [3.5, -3.5]]) W.B(x, 1.1, z, 1.2, 1.2, 1.2, 'hedge');
  add(8, -0.4, -9, 26, 0.02, 9, 'sand'); add(8.4, 0.02, -8.6, 25.6, 0.06, 8.6, 'water'); // the pond (ankle deep)
  add(15, 0.06, -9.4, 19, 0.6, 9.4, 'wood'); for (const s of [-1, 1]) add(15, 0.6, s * 9.4 - (s > 0 ? 0.15 : 0), 19, 1.5, s * 9.4 + (s > 0 ? 0 : 0.15), 'wood'); // the footbridge (low rails)
  for (const [x, z] of [[11, -5], [22, 6], [24, -3]]) W.B(x, 0.5, z, 1.4, 1, 1.2, 'rock');
  { const G = B.local(35, 0, 0); // the gazebo: posts, a rail, a stepped roof
    G(-4, 0, -4, 4, 0.4, 4, 'wood');
    for (const [x, z] of [[-3.7, -3.7], [3.7, -3.7], [-3.7, 3.7], [3.7, 3.7], [0, -3.7], [0, 3.7], [-3.7, 0], [3.7, 0]]) G.B(x, 1.9, z, 0.3, 3, 0.3, 'white');
    G(-4, 0.4, -4, 4, 1.3, -3.8, 'white'); G(-4, 0.4, 3.8, 4, 1.3, 4, 'white'); G(-4, 0.4, -3.8, -3.8, 1.3, -1.2, 'white'); G(3.8, 0.4, 1.2, 4, 1.3, 3.8, 'white');
    G(-4.4, 3.4, -4.4, 4.4, 3.7, 4.4, 'roofpink'); G(-3, 3.7, -3, 3, 4.2, 3, 'roofpink'); G(-1.5, 4.2, -1.5, 1.5, 4.7, 1.5, 'roofpink');
  }
  for (const [x, z] of [[-40, -8], [-40, 8], [40, -9], [40, 9], [4, -10], [-4, 10], [28, -10]]) lollipop(W, x, z, 5 + r() * 2, r);
  for (const [x, z, l] of [[-6, -9, 4], [6, 9, 4], [28, 9.5, 3]]) W(x - l / 2, 0, z - 0.6, x + l / 2, 1.3, z + 0.6, 'hedge');
  for (const x of [-43.6, 42.2]) add(x, 0, -7.5, x + 1.4, 2.6, 7.5, 'hedge'); // tall hedges at the park's ends: in from the corners and the long streets
  for (const [x, z] of [[-8, -11], [8, 11]]) { W(x - 1.2, 0, z - 0.35, x + 1.2, 0.5, z + 0.35, 'wood'); W(x - 1.2, 0.5, z + 0.2, x + 1.2, 1.0, z + 0.35, 'wood'); } // benches

  // ---- west end (team 1): the corner store, its car park, the bus stop
  const C = B.local(-71, 0, 1); // front (local -z) faces east, onto the street
  shell(C, 18, 12, 1, 4.2, 'brick', { roof: 'roofg', roofAccess: true, backDoor: true });
  C(-8.5, 0.12, -5.5, -1, 1.1, -4.6, 'wood'); C(1, 0.12, -5.5, 8.5, 1.1, -4.6, 'wood');
  for (const x of [-6, -2, 2, 6]) C(x - 0.4, 0.12, -1.5, x + 0.4, 1.9, 3.5, 'shelfstock');
  C(-8, 3.0, -6.55, 8, 4.4, -6.16, 'adstore', { fit: 1 });
  add(-65, 0, -11.6, -60, 0.1, 11.6, 'asphalt'); for (let z = -10; z <= 10; z += 4) add(-64.4, 0.1, z, -60.2, 0.11, z + 0.15, 'white');
  car(W, -62.3, -8, 1, 'cargreen'); car(W, -62.3, 8, 1, 'carwhite');
  { const H = B.local(-70, -10.9, 2); H(-3, 0, -0.9, 3, 0.3, 0.9, 'concrete'); H(-3, 0.3, 0.7, 3, 2.6, 0.9, 'glass'); H(-3.2, 2.6, -1.1, 3.2, 2.8, 1.1, 'toyteal'); H(-2, 0.3, 0.3, 2, 0.75, 0.7, 'seat'); } // the bus stop, by the road out
  bus(B, -81, 9.6); // the shuttle, parked up by the store (get in, shoot out the windows)
  adBoard(B, -74, 30, 0, 'x', 'adbig1'); W(-80, 0, -9, -77.4, 1.5, -7.6, 'containerg');
  const west = [[-79.5, 0.2, -6], [-79.5, 0.2, -2], [-79.5, 0.2, 2], [-79.5, 0.2, 6], [-74, 0.3, -6.5], [-74, 0.3, 6.5], [-81, 0.2, 0]]; // behind the store, inside it off the door's line
  // ---- east end (team 2): the building site: a frame going up, a scaffold, a digger, the site office
  add(60, 0, -24, 82, 0.03, 24, 'dirt'); add(64, 0, -9, 78, 0.3, 9, 'concrete');
  for (let x = 65; x <= 77; x += 2) for (const z of [-8, 8]) if (Math.abs(x - 71) > 2) box(x, 1.95, z, 0.15, 3.3, 0.15, 'plywood');
  for (let z = -6; z <= 6; z += 2) for (const x of [65, 77]) if (Math.abs(z) > 1.5) box(x, 1.95, z, 0.15, 3.3, 0.15, 'plywood');
  add(64.9, 3.6, -8.1, 77.1, 3.75, -7.9, 'plywood'); add(64.9, 3.6, 7.9, 77.1, 3.75, 8.1, 'plywood'); add(64.9, 3.6, -7.9, 65.1, 3.75, 7.9, 'plywood'); add(76.9, 3.6, -7.9, 77.1, 3.75, 7.9, 'plywood');
  add(65.1, 3.75, 0, 76.9, 3.95, 7.9, 'plywood'); stairs(W, 66.2, 67.7, 1, 1, 0.3, 3.95, 'plywood', 0.55);
  for (const [x, z] of [[63, -20], [63, -15], [67, -20], [67, -15]]) W.B(x, 2.9, z, 0.2, 5.8, 0.2, 'hazard');
  add(62.6, 2.8, -20.4, 67.4, 3, -14.6, 'grid'); add(62.6, 5.8, -20.4, 67.4, 6, -14.6, 'grid');
  excavator(B, 74, -18, 0); for (let i = 0; i < 4; i++) add(69.6 + i * 0.6, 0.03, 15.2 + i * 0.4, 75.6 - i * 0.6, 0.4 + i * 0.35, 19 - i * 0.3, 'sand');
  const SO = B.local(78, 19, 1); shell(SO, 8, 4.2, 1, 3, 'containerb', { roof: 'roofg', floor: 'carpet', parapet: false }); SO(-3.5, 3.3, -2.5, 3.5, 4.2, -2.25, 'adoffice', { fit: 1 });
  add(62, 0.03, 18, 64.4, 2.6, 20.4, 'toyblue'); palletLoad(B, 70, 12); palletLoad(B, 61, 4, 1);
  add(77.3, 0, -9.3, 77.5, 2.4, 9.3, 'plywood'); for (const [z, a] of [[-4.5, 'adbig1'], [4.5, 'adfun']]) D.add(77.5, 0.5, z - 4, 77.56, 2.2, z + 4, a, { fit: 1 }); // hoarding on the frame's far side
  const east = [[79.5, 0.2, -6], [79.5, 0.2, -2], [79.5, 0.2, 2], [79.5, 0.2, 6], [70, 0.4, -5.5], [70, 0.4, 5.5], [81, 0.2, 0]]; // behind the hoarding, inside the frame

  // ---- the four corner lots (each past the end of a row of houses, between the street and the back lane)
  { // south-west: the half-court. bleachers to stand on, the hoop, somebody's cooler
    add(-79.2, 0, 33.4, -60.4, 0.05, 54.4, 'asphalt2');
    D.add(-78, 0.05, 37.8, -62, 0.065, 53, 'toyteal'); // the painted court (look only, like its lines: 2 cm, the builder drops anything thinner than 1)
    const CL = (x0, z0, x1, z1) => D.add(x0, 0.05, z0, x1, 0.075, z1, 'white');
    CL(-77.5, 38.4, -62.5, 38.5); CL(-77.5, 52.3, -62.5, 52.4); CL(-77.5, 38.5, -77.4, 52.3); CL(-62.6, 38.5, -62.5, 52.3); // half-court line, baseline, sides
    CL(-72.45, 46.5, -67.55, 46.6); CL(-72.45, 46.6, -72.35, 52.3); CL(-67.65, 46.6, -67.55, 52.3); D.add(-72.35, 0.05, 46.6, -67.65, 0.07, 52.3, 'toypink'); // the key
    for (let i = 0; i < 9; i++) { const a = -Math.PI / 2 + (i + 0.5) * Math.PI / 9, R = 6.75; D.obb(-70 + Math.sin(a) * R, 0.0625, 50.8 - Math.cos(a) * R, 2.36, 0.025, 0.1, -a, 'white'); } // the three-point arc
    add(-70.15, 0.05, 53.0, -69.85, 3.95, 53.3, 'metal'); add(-70.1, 3.55, 51.35, -69.9, 3.7, 53.0, 'metal'); add(-70.9, 2.9, 51.2, -69.1, 3.95, 51.35, 'white'); // post, arm, backboard
    D.add(-70.3, 3.15, 51.17, -69.7, 3.55, 51.2, 'toyred');
    for (const [x0, z0, x1, z1] of [[-70.25, 50.55, -69.75, 50.6], [-70.25, 51.0, -69.75, 51.05], [-70.25, 50.6, -70.2, 51.0], [-69.8, 50.6, -69.75, 51.0], [-70.05, 51.05, -69.95, 51.17]]) D.add(x0, 3.03, z0, x1, 3.07, z1, 'toyorange'); // the rim
    D.add(-70.18, 2.7, 50.62, -69.82, 3.02, 50.98, 'grid'); D.box(-66.4, 0.17, 44.2, 0.24, 0.24, 0.24, 'toyorange'); // the net, the ball nobody took home
    for (let i = 0; i < 3; i++) add(-80.1 - i * 0.75, 0, 37, -79.35 - i * 0.75, 0.45 * (i + 1), 49, 'wood'); // bleachers (stand on the top row: over the fence)
    add(-62.4, 0.05, 53.3, -61.2, 0.7, 54.1, 'toyblue'); add(-62.45, 0.7, 53.25, -61.15, 0.78, 54.15, 'white'); // the cooler
    W(-60.3, 0, 40, -59.6, 0.5, 46, 'wood');
  }
  { // south-east: the community garden. raised beds, the prize pumpkins (cover, and they know it), a scarecrow, the shed
    add(58.5, 0, 26.9, 68.5, 1.1, 27.05, 'picket'); add(71.5, 0, 26.9, 81.5, 1.1, 27.05, 'picket'); // a low fence with the gate
    for (const x of [60.5, 64.8, 69.1]) for (const z of [30.5, 35, 39.5]) {
      add(x, 0, z, x + 3.2, 0.45, z + 1.5, 'wood'); D.add(x + 0.12, 0.45, z + 0.12, x + 3.08, 0.47, z + 1.38, 'dirt');
      for (let k = 0; k < 3; k++) D.box(x + 0.6 + k * 1.0, 0.64, z + 0.75, 0.42, 0.34, 0.42, (k + x) % 2 ? 'hedge' : 'leaves2');
    }
    for (const [x, z, sz] of [[77, 31, 1.6], [79.6, 33.4, 1.1], [75.6, 38.4, 2.5]]) {
      W.B(x, sz / 2, z, sz, sz, sz * 0.9, 'toyorange'); W.B(x, sz + 0.15, z, 0.22, 0.3, 0.22, 'leaves');
      D.box(x, sz * 0.5, z, sz * 1.12, sz * 0.7, sz * 0.75, 'toyorange'); D.box(x, sz * 0.5, z, sz * 0.75, sz * 0.7, sz * 1.02, 'toyorange'); // the bulge round its middle (look only)
    }
    D.add(74.2, 1.6, 37.1, 74.9, 2.3, 37.14, 'toyblue'); // the 1st-prize rosette on the big one
    W.B(66, 1.2, 46, 0.16, 2.4, 0.16, 'wood'); W.B(66, 1.85, 46, 1.6, 0.12, 0.12, 'wood'); W.B(66, 1.55, 46, 0.8, 0.8, 0.36, 'cloth'); W.B(66, 2.32, 46, 0.5, 0.5, 0.5, 'toyface', { fit: 1 }); // the scarecrow
    W(76, 0, 46, 80, 2.4, 49.5, 'wood'); W(75.8, 2.4, 45.8, 80.2, 2.7, 49.7, 'roofg'); D.add(77.3, 0, 45.96, 78.7, 2.0, 46, 'metal'); // the shed
    W.B(75.3, 0.6, 50.4, 0.8, 1.2, 0.8, 'toyblue'); W(60, 0, 52, 61.3, 1.1, 53.3, 'pallet'); W(61.6, 0, 52, 62.9, 1.1, 53.3, 'pallet'); // water butt, compost bins
  }
  { // north-west: the store's stock yard. a loading dock with the delivery truck backed onto it, the stockroom, the bins
    add(-81.6, 0, -56.6, -74.4, 4.4, -50.2, 'brick'); add(-81.8, 4.4, -56.8, -74.2, 4.7, -50.0, 'roofg'); // the stockroom (shut)
    D.add(-79.5, 1.1, -50.2, -76.5, 3.8, -50.16, 'metal'); // its roller door, down
    add(-80, 0, -50.2, -73.9, 1.1, -40, 'concrete'); stairs(W, -79.8, -78.3, -38.5, -1, 0, 1.1, 'concrete', 0.5); // the dock, steps up
    truck(B, -73.9, -46, 'adtruck2', false);
    W(-70.5, 0, -56.7, -67.9, 1.3, -55.3, 'containerg'); W(-66.9, 0, -56.7, -64.3, 1.3, -55.3, 'containerb'); // bins
    pallets(B, -62.5, -50.5, 6, r); pallets(B, -61, -50.5, 3, r); cratePile(B, -66, -34, 6, r);
  }
  { // north-east: PLOT 12, the next show home. a slab with the frame going up, roof trusses, a skip, the portaloo
    add(62, 0, -40, 74, 0.25, -30, 'concrete');
    for (let k = 0; k <= 6; k++) for (const z of [-39.9, -30.1]) if (z < -35 || k !== 3) W.B(62.1 + k * 11.8 / 6, 1.6, z, 0.15, 2.7, 0.15, 'wood'); // studs (a gap for the front door)
    for (const x of [62.1, 73.9]) for (let z = -37.925; z < -30.5; z += 1.975) if (x > 70 || Math.abs(z + 35) > 1.2) W.B(x, 1.6, z, 0.15, 2.7, 0.15, 'wood');
    add(62.025, 2.95, -39.975, 73.975, 3.1, -39.825, 'wood'); add(62.025, 2.95, -30.175, 73.975, 3.1, -30.025, 'wood');
    add(62.025, 2.95, -39.825, 62.175, 3.1, -30.175, 'wood'); add(73.825, 2.95, -39.825, 73.975, 3.1, -30.175, 'wood'); // top plates
    add(61.95, 0, -40.06, 74.05, 2.95, -40.0, 'plywood'); add(74.0, 0, -40.0, 74.06, 2.95, -34, 'plywood'); // sheathing on the back wall
    add(75.4, 0, -38.5, 76.8, 0.9, -30.5, 'wood'); add(77.6, 0, -37.5, 79, 1.35, -31.5, 'wood'); // roof trusses, stacked flat
    for (const y of [0.3, 0.6]) D.add(75.38, y, -38.52, 76.82, y + 0.03, -30.48, 'plywood'); for (const y of [0.45, 0.9]) D.add(77.58, y, -37.52, 79.02, y + 0.03, -31.48, 'plywood');
    add(66, 0, -55.6, 70, 1.5, -55.48, 'containerr'); add(66, 0, -53.72, 70, 1.5, -53.6, 'containerr'); add(66, 0, -55.48, 66.12, 1.5, -53.72, 'containerr'); add(69.88, 0, -55.48, 70, 1.5, -53.72, 'containerr');
    add(66.12, 0, -55.48, 69.88, 1.0, -53.72, 'dirt'); W.B(67.1, 1.2, -54.7, 1.0, 0.4, 0.8, 'rock'); W.B(68.7, 1.15, -54.4, 0.9, 0.3, 0.7, 'brick'); // the skip, full
    add(79.4, 0, -29.6, 80.6, 2.3, -28.4, 'toyblue'); add(79.35, 2.3, -29.65, 80.65, 2.42, -28.35, 'white'); D.add(79.7, 1.9, -28.4, 80.3, 2.1, -28.36, 'white'); // the portaloo
    for (const x of [63, 64.6]) { add(x, 0, -51, x + 1.2, 0.15, -50, 'pallet'); add(x + 0.05, 0.15, -50.95, x + 1.15, 1.0, -50.05, 'brick'); } // bricks on pallets
    pipeStack(B, 60.6, -46, false); generatorTower(B, 79.6, -45, 0); cones(B, 62, -28.2, 72, -28.2, 6);
  }

  spawns.push(...west.slice(0, 2), ...east.slice(0, 2), [-30, 0.2, -5], [-18, 0.2, 6], [10, 0.2, -10], [30, 0.2, 9], [35, 0.5, 0], [0, 0.6, -7],
    [-70, 0.2, -50], [70, 0.2, -50], [-70, 0.2, 50], [70, 0.2, 50], [-71, 0.3, 0], [0, 0.2, -59.5], [0, 0.2, 59.5]);
  let graph = null;
  const map = {
    name: 'Suburb', size: 'large', boxes: B.boxes, deco: D.boxes, killY: -60, bounds, floorY: -4,
    sky: { top: 0x2f7cf0, mid: 0xffd3ec, bot: 0x7a4a6a, fog: 0xffd3ec }, fogNear: 110, fogFar: 430,
    spawns, teamSpawns: { att: west, def: east },
    gates, // the gaps in the back fence: [outside, inside] (a bot out past it heads for the nearest)
    // traffic (shared/traffic.js): in from the woods on the north street's inner lane, round the far end, out on the south
    // street's; the other way round on the two outer lanes. the parked cars are on the kerbs outside them
    traffic: { routes: [{ pts: [[-430, -16.5], [49.5, -16.5], [49.5, 16.5], [-430, 16.5]], v: [8, 13], r: 6 }, { pts: [[-430, 20], [53, 20], [53, -20], [-430, -20]], v: [8, 13], r: 6 }] },
    get graph() { return graph || (graph = buildNav(B.boxes, { x0: bounds[0] - 1, z0: bounds[1] - 1, n: bounds[2] - bounds[0] + 2, cell: 1, levels: [0], band: 0.5, keep: (x, z) => !outOfBounds(map, [x, 0, z]) })); },
  };
  return map;
}

// ---- the warehouse kit (racking, pallets, forklifts, trailers, semis, crates, building-site machinery): Warehouse, Suburb
function rack(B, x0, z, len, r) { // blue racking with orange beams, three decks you can climb, boxes on every level
  // in 6 m bays: the Blender rack (shared/props.js) draws the uprights, beams and wire decks over these boxes (same heights)
  len = Math.max(6, Math.round(len / 6) * 6);
  const L = B.local(0, 0, 0), rk = { pv: 'rack' };
  for (let x = x0; x < x0 + len - 0.01; x += 6) L.P('rack', x, z, 0, { v: 'bay' });
  L.P('rack', x0 + len, z, 0, { v: 'frame' });
  for (let x = x0; x <= x0 + len + 0.01; x += 6) for (const pz of [z - 1.3, z + 1.1]) B.add(x - 0.1, 0, pz, x + 0.1, 7.3, pz + 0.2, 'shelf', rk); // posts stand proud of the beams (no faces in one plane)
  for (const lvl of [0, 2.4, 4.8]) {
    B.add(x0, lvl + 2, z - 1.2, x0 + len, lvl + 2.25, z + 1.2, 'pallet', rk);
    B.add(x0, lvl + 1.75, z - 1.25, x0 + len, lvl + 2, z - 1.2, 'toyorange', rk); B.add(x0, lvl + 1.75, z + 1.2, x0 + len, lvl + 2, z + 1.25, 'toyorange', rk);
  }
  B.add(x0, 0, z + 0.75, x0 + len, 2, z + 0.8, 'grid'); // mesh backing up to the first deck: a row is a wall at body height (no heads showing through)
  for (let bx = x0; bx < x0 + len - 0.01; bx += 6) for (const off of [0.3, 1.75, 3.2, 4.65]) { // four lots a bay, clear of the uprights
    const x = bx + off;
    for (const lvl of [2.25, 4.65, 7.05]) if (r() < 0.7) { const h = 0.6 + r() * 0.9; B.add(x, lvl, z - 0.9 + r() * 0.3, x + 0.9 + r() * 0.3, lvl + h, z + 0.6 + r() * 0.3, r() < 0.85 ? 'cardboard' : 'shelfstock'); }
    // every bay on the floor is stocked (with the backing behind it, an empty one would be a pocket you walk into and stick)
    B.add(x, 0, z - 0.9, x + 1.2, 0.15, z + 0.7, 'pallet'); B.add(x + 0.05, 0.15, z - 0.85, x + 1.15, 0.15 + 0.85 + r() * 0.65, z + 0.65, 'cardboard');
  }
}
function pallets(B, x, z, n, r, top = true) { // a stack of empty pallets, now and then with boxes on top
  for (let i = 0; i < n; i++) B.add(x, i * 0.16, z, x + 1.2, i * 0.16 + 0.15, z + 1.0, 'pallet');
  if (top && r() < 0.6) B.add(x + 0.05, n * 0.16, z + 0.05, x + 1.15, n * 0.16 + 0.5 + r() * 0.7, z + 0.95, 'cardboard');
}
// the Blender forklift over its collision boxes (shared/props.js). forks toward local -x; lift: it's carrying a load
function forklift(B, x, z, rot, lift = 0) {
  const L = B.local(x, z, rot);
  prop(L, 'forklift', 0, 0, 2);
  if (lift) prop(L, 'pallet_load', -1.95, 0, 0, { y: 0.2 });
}
// a pallet with a load strapped on (the Blender one): small cover
function palletLoad(B, x, z, rot = 0) { prop(B.local(x, z, rot), 'pallet_load', 0, 0, 0); }
function trailer(B, x0, z0, livery) { // a semi trailer along x on its landing legs (no cab)
  const z1 = z0 + 2.6;
  B.add(x0, 1.3, z0, x0 + 12.5, 4.1, z1, 'truckbox');
  B.add(x0 + 1, 1.5, z0 - 0.03, x0 + 11.5, 3.9, z0, livery, { fit: 1 }); B.add(x0 + 1, 1.5, z1, x0 + 11.5, 3.9, z1 + 0.03, livery, { fit: 1 });
  for (const wx of [x0 + 0.9, x0 + 2.1]) for (const [a, b] of [[z0 + 0.1, z0 + 0.5], [z1 - 0.5, z1 - 0.1]]) B.add(wx - 0.5, 0, a, wx + 0.5, 1.0, b, 'tire');
  B.add(x0 + 0.45, 0.95, z0 + 0.3, x0 + 2.55, 1.3, z1 - 0.3, 'metal'); // (the axle stops short of the tyres' faces)
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
  L(-1.25, 0.6, 12.7, 1.25, 1.08, 16.6, 'metal'); // chassis under the cab
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

// ---- construction machinery (each takes a builder, B for things you bump into or D for render-only, and its own frame).
// local -z is the front
function excavator(Bd, x, z, rot) {
  const L = Bd.local(x, z, rot);
  L(-1.7, 0, -1.9, -0.9, 0.9, 1.9, 'tire'); L(0.9, 0, -1.9, 1.7, 0.9, 1.9, 'tire'); L(-0.9, 0.25, -1.4, 0.9, 0.9, 1.4, 'metal'); // tracks
  L(-1.5, 0.9, -1.3, 1.5, 2.1, 1.6, 'toyyellow'); L(-1.5, 0.9, 1.6, 1.5, 2.0, 2.3, 'hazard'); // the house, the counterweight
  L(-1.45, 2.1, -1.3, -0.15, 3.5, 0.4, 'toyyellow'); L(-1.47, 2.45, -1.32, -0.13, 3.3, -1.28, 'glass'); L(-1.47, 2.45, -1.0, -1.43, 3.3, 0.2, 'glass');
  L(0.2, 2.0, -1.4, 0.95, 2.7, -3.4, 'toyyellow'); L(0.2, 2.7, -3.4, 0.95, 3.5, -5.0, 'toyyellow'); L(0.2, 3.5, -5.0, 0.95, 4.1, -6.1, 'toyyellow'); // the boom
  L(0.28, 1.3, -6.1, 0.87, 4.1, -6.7, 'toyyellow'); L(0.05, 0.25, -7.1, 1.1, 1.3, -5.9, 'metal'); L(0.05, 0, -7.3, 1.1, 0.25, -6.9, 'metal'); // stick, bucket, teeth
}
function bulldozer(Bd, x, z, rot) {
  const L = Bd.local(x, z, rot);
  L(-1.6, 0, -1.6, -0.9, 1.0, 1.8, 'tire'); L(0.9, 0, -1.6, 1.6, 1.0, 1.8, 'tire');
  L(-0.9, 0.3, -1.6, 0.9, 1.8, 1.8, 'toyyellow'); L(-0.8, 1.8, -1.5, 0.8, 2.2, 0.2, 'toyyellow'); // body, engine hood
  L(-0.9, 1.8, 0.2, 0.9, 3.3, 1.7, 'toyyellow'); L(-0.92, 2.2, 0.25, 0.92, 3.1, 1.65, 'glass'); L(-0.2, 2.2, -1.2, 0.0, 3.0, -1.0, 'chrome'); // cab, exhaust
  L(-2.0, 0, -3.1, 2.0, 1.5, -2.7, 'metal'); for (const sx of [-1.3, 1.1]) L(sx, 0.5, -2.7, sx + 0.2, 0.8, -1.4, 'metal'); // the blade
  L(-0.15, 0, 1.8, 0.15, 0.8, 2.8, 'metal'); // ripper
}
function mixerTruck(Bd, x, z, rot) {
  const L = Bd.local(x, z, rot);
  for (const wz of [-2.6, 1.4, 2.8]) for (const sx of [-1.25, 0.85]) L(sx, 0, wz - 0.5, sx + 0.4, 1.0, wz + 0.5, 'tire');
  L(-1.2, 0.6, -3.6, 1.2, 1.1, 3.8, 'metal'); L(-1.2, 1.1, -3.9, 1.2, 3.0, -1.9, 'toyred'); L(-1.1, 2.0, -3.92, 1.1, 2.8, -3.88, 'glass'); // chassis, cab
  for (let i = 0; i < 4; i++) { const w = 1.1 - Math.abs(i - 1.4) * 0.22; L(-w, 2.4 - w, -1.4 + i * 1.2, w, 2.4 + w, -0.2 + i * 1.2, i % 2 ? 'toyorange' : 'white'); } // the drum, striped
  L(-0.3, 2.6, 3.4, 0.3, 3.0, 4.4, 'metal'); // the chute
}
function roller(Bd, x, z, rot) {
  const L = Bd.local(x, z, rot);
  L(-1.1, 0, -2.6, 1.1, 1.3, -1.4, 'metal'); L(-1.15, 0.5, -2.2, 1.15, 0.8, -1.8, 'hazard'); // the drum
  L(-0.9, 0.4, -1.4, 0.9, 1.6, 1.6, 'toyyellow'); for (const sx of [-1.1, 0.7]) L(sx, 0, 0.6, sx + 0.4, 1.0, 1.55, 'tire');
  for (const [px, pz] of [[-0.8, -0.6], [0.7, -0.6], [-0.8, 1.2], [0.7, 1.2]]) L(px, 1.6, pz, px + 0.1, 3.0, pz + 0.1, 'metal');
  L(-0.95, 3.0, -0.7, 0.95, 3.15, 1.4, 'toyyellow'); L(-0.3, 1.6, 0.1, 0.3, 2.1, 0.7, 'seat');
}
function generatorTower(Bd, x, z, rot) { // a generator trailer with a fold-up light mast, lamps on
  const L = Bd.local(x, z, rot);
  L(-1.1, 0.35, -1.6, 1.1, 1.9, 1.6, 'containerg'); L(-1.12, 0.9, -1.2, 1.12, 1.6, 1.2, 'grid'); L(0.4, 1.9, 0.6, 0.7, 2.6, 0.9, 'chrome');
  for (const sx of [-0.9, 0.6]) L(sx, 0, -0.4, sx + 0.3, 0.7, 0.4, 'tire');
  L(-0.12, 1.9, -1.3, 0.12, 8.5, -1.06, 'metal'); L(-1.2, 8.5, -1.4, 1.2, 9.3, -1.0, 'metal');
  for (const sx of [-1.1, -0.25, 0.6]) L(sx, 8.6, -1.45, sx + 0.5, 9.2, -1.4, 'lamp');
}
function pipeStack(Bd, x, z, alongZ) { // big pipes stacked in a pyramid
  const L = Bd.local(x, z, alongZ ? 1 : 0);
  for (let row = 0; row < 3; row++) for (let i = 0; i < 3 - row; i++) L.B((i - (2 - row) / 2) * 0.95, 0.45 + row * 0.82, 0, 0.85, 0.85, 7 - row * 0.3, row % 2 ? 'rust' : 'metal'); // (each row a bit shorter: no ends in one plane)
}
function gravelPile(Bd, x, z, s, m = 'sand') {
  for (let i = 0; i < 4; i++) { const k = 1 - i * 0.24; Bd.box(x + i * 0.2, (i + 0.5) * s * 0.18, z - i * 0.1, s * k, s * 0.18, s * 0.8 * k, m); }
}
function cones(Bd, x0, z0, x1, z1, n) {
  for (let i = 0; i < n; i++) { const t = n > 1 ? i / (n - 1) : 0, x = x0 + (x1 - x0) * t, z = z0 + (z1 - z0) * t; Bd.box(x, 0.06, z, 0.6, 0.12, 0.6, 'tire'); Bd.box(x, 0.45, z, 0.38, 0.7, 0.38, 'toyorange'); Bd.box(x, 0.5, z, 0.42, 0.14, 0.42, 'white'); }
}

// ------------------------------------------------------------ WAREHOUSE: the depot for every mode but Plant & Defuse.
// built for flow: no dead ends, everything loops. the hall in the middle is a grid of racking aisles (long aisles, cross
// aisles, an end aisle at each end) with the foreman's two-floor office in one corner (its roof looks over the floor, and
// everyone can see you up there) and a shredder pit to keep you honest. north of it the container yard (a small maze, a
// crane), south the truck dock (four dock doors into the hall, trailers to fight round), and the two team sides at the
// ends: the gate (west) and the staff car park (east). the hall stands between those two, so no team spawn sees the other
function warehouse() {
  const B = builder(), D = builder();
  const { add, box } = B;
  const r = rng(616), W = B.local(0, 0, 0);
  const trailerS = (x0, z0, liv) => { trailer(B, x0, z0, liv); add(x0 + 0.3, 0, z0 + 0.55, x0 + 12.2, 1.3, z0 + 2.05, 'metal'); };
  const semiS = (x, z, rot, liv, cab) => { semi(B, x, z, rot, liv, cab); B.local(x, z, rot)(-0.75, 0, 0.3, 0.75, 1.3, 12.2, 'metal'); };
  const FX = 75, FZ = 55, F = { x0: -FX, z0: -FZ, x1: FX, z1: FZ }, bounds = [-FX, -FZ, FX, FZ];
  const HX = 32, HZ = 18, H = 10; // the hall
  // ---- the ground (a hole for the shredder), asphalt where the trucks go, paint
  const pit = [-28, 11.5, -24, 15.5]; // (far enough off the wall that the strip behind it isn't a trap for bots)
  groundHoles(B, -FX, -FZ, FX, FZ, -1, 0, 'concrete', [pit]);
  add(-FX, 0, -FZ, FX, 0.03, -HZ - 0.4, 'asphalt2'); // the container yard
  add(-FX, 0, HZ + 0.4, FX, 0.03, FZ, 'asphalt2'); // the truck dock
  add(HX + 0.4, 0, -HZ - 0.4, FX, 0.03, HZ + 0.4, 'asphalt2'); // the staff car park
  for (let x = 52; x <= 70; x += 4.5) add(x, 0.03, 6, x + 0.15, 0.045, 16, 'white');
  for (const z of [-HZ - 1.2, HZ + 1.2]) add(-HX + 2, 0.03, z - 0.1, HX - 2, 0.045, z + 0.1, 'neonyellow');
  // ---- the fence (the gate's shut), the world outside, light masts
  chainFence(B, D, -FX, -FZ, FX, -FZ); chainFence(B, D, -FX, FZ, FX, FZ); chainFence(B, D, FX, -FZ, FX, FZ);
  chainFence(B, D, -FX, -FZ, -FX, -6); chainFence(B, D, -FX, 6, -FX, FZ);
  add(-FX - 0.3, 0.05, -5.9, -FX - 0.15, 4.2, 5.9, 'fence');
  depotOutside(B, D, r, F);
  for (const [x, z] of [[-71, -51], [-71, 51], [71, -51], [71, 51], [0, -51], [0, 51]]) { box(x, 7, z, 0.5, 14, 0.5, 'metal'); D.box(x, 14.2, z, 2.6, 0.5, 1, 'lamp'); }

  // ---- the hall: doors on every side (the west and east ones off the same line), racking in a grid of aisles
  const dock = [-24, -8, 8, 24]; // dock doors along the south wall
  wall(W, 'x', -HZ, -HX - 0.3, HX + 0.3, 0, H, 0.6, 'metal', [{ a: -18, b: -13, y0: 0, y1: 4 }, { a: 10, b: 15, y0: 0, y1: 4 }, ...windows(2 * HX, 6, 0, 2, 8)]);
  wall(W, 'x', HZ, -HX - 0.3, HX + 0.3, 0, H, 0.6, 'metal', [...dock.map((x) => ({ a: x - 2.5, b: x + 2.5, y0: 0, y1: 4.2 })), ...windows(2 * HX, 6, 0, 2, 8)]);
  wall(W, 'z', -HX, -HZ + 0.3, HZ - 0.3, 0, H, 0.6, 'metal', [{ a: 3, b: 10, y0: 0, y1: 5 }]);
  wall(W, 'z', HX, -HZ + 0.3, HZ - 0.3, 0, H, 0.6, 'metal', [{ a: -10, b: -3, y0: 0, y1: 5 }]);
  add(-HX - 0.3, H, -HZ - 0.3, HX + 0.3, H + 0.5, HZ + 0.3, 'roofblue');
  for (const x of dock) { D.add(x - 2.7, 4.3, HZ + 0.31, x + 2.7, 4.5, HZ + 0.35, 'hazard'); D.add(x - 1, 4.7, HZ + 0.31, x + 1, 5.7, HZ + 0.36, 'neonyellow'); }
  D.add(-HX - 0.5, 6.2, 3.5, -HX - 0.36, 8.4, 9.5, 'adware', { fit: 1 }); D.add(HX + 0.36, 6.2, -9.5, HX + 0.5, 8.4, -3.5, 'neonwork', { fit: 1 });
  add(-6, 9.4, -HZ - 0.5, 6, 11.4, -HZ - 0.35, 'adtruck2', { fit: 1 }); // the company, over the yard doors
  for (let z = -15; z <= 15; z += 6) {
    add(-HX, H - 1.4, z - 0.25, HX, H - 0.9, z + 0.25, 'wood');
    for (let x = -24; x <= 24; x += 12) if (!(x > 18 && z < -8)) { D.add(x - 0.03, H - 3.6, z - 0.03, x + 0.03, H - 1.4, z + 0.03, 'tire'); D.add(x - 0.6, H - 3.9, z - 0.6, x + 0.6, H - 3.6, z + 0.6, 'metal'); D.add(x - 0.45, H - 3.96, z - 0.45, x + 0.45, H - 3.9, z + 0.45, 'lamp'); }
  }
  rack(B, -26, -9, 18, r); rack(B, 7, -9, 12, r); // three rows, each broken by a cross aisle (and the office in the corner)
  rack(B, -21, 0, 18, r); rack(B, 6, 0, 12, r);
  rack(B, -26, 9, 18, r); rack(B, 8, 9, 18, r);
  for (const x of [-7, 6.5]) add(x - 0.08, 0, -HZ + 0.5, x + 0.08, 0.02, HZ - 0.5, 'neonyellow');
  // the foreman's office: two floors and stairs to the roof, in the north-east corner
  const O = B.local(26, -13.5, 0);
  shell(O, 11, 8.4, 2, 3.6, 'magenta', { floor: 'leopard', roof: 'roofg', roofAccess: true, backDoor: true });
  O(-4.5, 0.12, -1.5, -1.5, 0.85, 0.5, 'wood'); O(1.5, 3.85, -1.5, 4.5, 4.6, 0.5, 'wood'); O.B(-3, 1.15, -0.5, 0.9, 0.6, 0.1, 'tvstatic'); O.B(3, 4.9, -0.5, 0.9, 0.6, 0.1, 'tvstatic');
  // the shredder (into the void) by the west door: rails on two sides, a sign
  const [px0, pz0, px1, pz1] = pit;
  add(px0, 0, pz0 - 0.3, px1, 0.6, pz0, 'hazard'); add(px0, 0, pz1, px1, 0.6, pz1 + 0.3, 'hazard');
  add(px0 - 0.3, -48, pz0 - 0.3, px0, -1, pz1 + 0.3, 'rust'); add(px1, -48, pz0 - 0.3, px1 + 0.3, -1, pz1 + 0.3, 'rust');
  add(px0, -48, pz0 - 0.3, px1, -1, pz0, 'rust'); add(px0, -48, pz1, px1, -1, pz1 + 0.3, 'rust');
  // (the machine itself, two toothed drums turning 2-3 m down with a red glow under them, is drawn by the client:
  // public/js/shredpit.js, from map.shredders below. its teeth kill: shared/shredpit.js)
  add((px0 + px1) / 2 - 2, 0, pz0 - 0.62, (px0 + px1) / 2 + 2, 0.6, pz0 - 0.32, 'adshred', { fit: 1 });
  forklift(B, -1, -4.5, 1, 1.4); forklift(B, -12, 14, 0); forklift(B, 21, 4.5, 3, 2.2);
  pallets(B, -2, 12, 6, r); pallets(B, -0.6, 12, 4, r); pallets(B, 16, -14, 7, r); pallets(B, -29, -14, 5, r); pallets(B, -27.6, -14, 3, r);
  cratePile(B, -16, -16, 6, r); cratePile(B, 26, 13, 5, r); palletLoad(B, -2, -14); palletLoad(B, 14, 14, 1);
  for (let i = 0; i < 6; i++) box(-30.5 + (i % 3) * 0.85, 0.6, -6 + Math.floor(i / 3) * 0.85, 0.75, 1.2, 0.75, i % 2 ? 'barrelr' : 'barrel');

  // ---- north: the container yard. stacks in two staggered rows (a little maze), a crane over the middle
  for (const [x, z, alongZ, n, ms, len] of [
    [-56, -40, true, 2, ['containerg', 'containerr']], [-40, -28, false, 1, ['containerb']], [-24, -46, false, 2, ['containerr', 'containerb']],
    [-6, -31, true, 1, ['containerg'], 8], [10, -45, false, 2, ['containerb', 'containerg']], [28, -30, false, 1, ['containerr']],
    [44, -44, true, 2, ['containerg', 'containerr']], [60, -30, false, 1, ['containerb'], 8], [-62, -26, false, 1, ['containerr'], 8], [60, -50, false, 1, ['containerg'], 10]]) container(B, x, z, alongZ, n, ms, len);
  cratePile(B, -12, -52, 6, r); cratePile(B, 30, -50, 5, r); pallets(B, -32, -38, 6, r); pallets(B, -30.6, -38, 4, r); pallets(B, 20, -36, 5, r);
  cratePile(B, -68, -50, 6, r); pallets(B, -46, -24, 5, r); pallets(B, 50, -24, 6, r); pallets(B, 51.4, -24, 4, r); cratePile(B, 66, -38, 5, r); barrier(B, -64, -34, false); barrier(B, 70, -24, true);
  forklift(B, -18, -24, 0, 1.2); forklift(B, 35, -52, 2);
  barrier(B, -48, -36, true); barrier(B, 2, -40, false); barrier(B, 36, -36, true);
  for (const x of [-30, 30]) box(x, 5, -36, 0.9, 10, 0.9, 'toyorange');
  D.add(-30.5, 10, -36.5, 30.5, 11, -35.5, 'toyorange'); D.add(-3, 8.6, -36.7, 0, 10, -35.3, 'hazard'); D.add(-1.6, 4.2, -36.05, -1.4, 8.6, -35.95, 'tire'); D.add(-2.4, 3.4, -36.7, -0.6, 4.2, -35.3, 'metal');

  // ---- south: the truck dock. two semis backed up beside the dock doors, a row of trailers further out
  semiS(-16, HZ + 1.5, 0, 'adtruck', true); semiS(16, HZ + 1.5, 0, 'adtruck2', true);
  for (const [x, liv] of [[-58, 'adtruck2'], [-36, 'adtruck'], [8, 'adtruck2'], [34, 'adtruck']]) trailerS(x, 42, liv);
  for (const [x, z] of [[-48, 28], [40, 28], [-4, 47]]) { add(x, 0, z, x + 2.6, 1.5, z + 1.6, 'containerg'); add(x - 0.05, 1.5, z - 0.05, x + 2.65, 1.62, z + 1.65, 'metal'); }
  forklift(B, -30, 30, 1, 1.2); forklift(B, 30, 34, 3); pallets(B, -8, 30, 6, r); pallets(B, -6.6, 30, 4, r); pallets(B, 52, 30, 7, r); cratePile(B, -64, 32, 6, r);
  barrier(B, 0, 37, false); barrier(B, -24, 37, false); barrier(B, 24, 37, false);
  cratePile(B, -44, 50, 5, r); cratePile(B, 22, 50, 6, r); palletLoad(B, -40, 34); palletLoad(B, 4, 32, 1); palletLoad(B, 40, 46); palletLoad(B, -44, -46); palletLoad(B, 24, -40, 1); pallets(B, -60, 26, 6, r); pallets(B, 64, 24, 5, r); barrier(B, -36, 26, true); barrier(B, 46, 40, true);
  for (let i = 0; i < 6; i++) for (let k = 0; k <= i % 3; k++) box(48 + i * 1.1, 0.15 + k * 0.3, 50, 1, 0.3, 1, 'tire');

  // ---- west: the gate side (team 1). the truck that came in, the guard booth
  semiS(-66, -36, 0, 'adtruck2', true); // (parked up the side, out of the spawn's way)
  const GB = B.local(-68, 14, 2);
  shell(GB, 4, 3.4, 1, 2.8, 'toyteal', { roof: 'toyred', floor: 'tile', parapet: false });
  GB(-1.6, 0.12, 0.4, 1.6, 0.95, 1.4, 'wood'); GB.B(0.8, 1.2, 0.9, 0.7, 0.45, 0.1, 'tvstatic');
  barrier(B, -50, -8, true); barrier(B, -46, 12, true); cratePile(B, -54, 2, 5, r);
  const west = [[-70, 0.1, -6], [-70, 0.1, 0], [-70, 0.1, 6], [-62, 0.1, -9], [-62, 0.1, -2], [-62, 0.1, 5], [-62, 0.1, 11]];
  // ---- east: the staff car park (team 2). the site office, cars
  const SO = B.local(52, -10, 0);
  shell(SO, 10, 4.2, 1, 3, 'containerb', { roof: 'roofg', floor: 'carpet', parapet: false });
  SO(-4, 3.3, -2.5, 4, 4.2, -2.25, 'adoffice', { fit: 1 }); SO(-4.5, 0.12, 0.6, -1.5, 0.85, 1.9, 'wood'); SO(1.5, 0.12, 0.6, 4.5, 0.85, 1.9, 'wood');
  for (const [x, c] of [[54.3, 'carred'], [58.8, 'carblue'], [63.3, 'caryellow'], [67.8, 'cargreen']]) car(W, x, 11, 1, c); // nose-in, one to a bay
  barrier(B, 44, 2, true); barrier(B, 46, -16, false);
  const east = [[70, 0.1, -6], [70, 0.1, 0], [70, 0.1, 4], [62, 0.1, -14], [62, 0.1, -2], [62, 0.1, 2], [70, 0.1, -12]];

  const spawns = [...west.slice(0, 3), ...east.slice(0, 3),
    [-50, 0.1, -46], [-14, 0.1, -38], [20, 0.1, -50], [52, 0.1, -36], [-66, 0.1, -40], [66, 0.1, -42],
    [-22, 0.1, -13.5], [0, 0.1, 4.5], [22, 0.1, 13.5], [-12, 0.1, 4.5],
    [-44, 0.1, 30], [-10, 0.1, 40], [24, 0.1, 30], [60, 0.1, 40], [-66, 0.1, 46], [0, 0.1, 52]];
  let graph = null;
  const map = {
    name: 'Warehouse', size: 'large', boxes: B.boxes, deco: D.boxes, killY: -45, bounds, ceiling: 9, floorY: -50,
    sky: { top: 0x0a0a20, mid: 0x5a2a6a, bot: 0x050508, fog: 0x3a2448 }, fogNear: 70, fogFar: 300,
    spawns, teamSpawns: { att: west, def: east },
    shredders: [{ box: pit.slice(), y: -1.9, axis: 'z' }], // the shredder: drums along z, the tips of the teeth at y
    get graph() { return graph || (graph = buildNav(B.boxes, { x0: bounds[0] - 1, z0: bounds[1] - 1, n: bounds[2] - bounds[0] + 2, cell: 1, levels: [0], band: 0.5, keep: (x, z) => !outOfBounds(map, [x, 0, z]) })); },
  };
  return map;
}

// ---- the depot kit (both Warehouse layouts)
// a chain-link fence on posts with barbed wire on top (solid: you can't walk through it, you can see out)
function chainFence(B, D, x0, z0, x1, z1) {
  const alongX = z0 === z1, len = alongX ? x1 - x0 : z1 - z0;
  if (alongX) B.add(x0, 0, z0 - 0.04, x1, 4.2, z0 + 0.04, 'fence'); else B.add(x0 - 0.04, 0, z0, x0 + 0.04, 4.2, z1, 'fence');
  for (let t = 0; t <= len + 0.01; t += 6) { const px = alongX ? x0 + t : x0, pz = alongX ? z0 : z0 + t; B.box(px, 2.25, pz, 0.14, 4.5, 0.14, 'metal'); }
  if (alongX) { D.add(x0, 4.5, z0 - 0.02, x1, 4.53, z0 + 0.02, 'tire'); D.add(x0, 4.75, z0 - 0.02, x1, 4.78, z0 + 0.02, 'tire'); }
  else { D.add(x0 - 0.02, 4.5, z0, x0 + 0.02, 4.53, z1, 'tire'); D.add(x0 - 0.02, 4.75, z0, x0 + 0.02, 4.78, z1, 'tire'); }
}
// a shipping container (12 m, or len) along x or z, n high
function container(B, x, z, alongZ, n, mats, len = 12) {
  for (let k = 0; k < n; k++) {
    const m = mats[k % mats.length], y = k * 2.6;
    if (alongZ) B.add(x - 1.25, y, z - len / 2, x + 1.25, y + 2.6, z + len / 2, m); else B.add(x - len / 2, y, z - 1.25, x + len / 2, y + 2.6, z + 1.25, m);
  }
}
// a concrete jersey barrier: waist-high cover you can vault
function barrier(B, x, z, alongZ, len = 3) {
  if (alongZ) B.add(x - 0.35, 0, z - len / 2, x + 0.35, 1.05, z + len / 2, 'concrete'); else B.add(x - len / 2, 0, z - 0.35, x + len / 2, 1.05, z + 0.35, 'concrete');
}
// a bomb site board (render-only): the letter, s wide, its face toward +-x ('x') or +-z ('z'), a hair off the wall
function siteBoard(D, x, y, z, along, mat, s = 4) {
  if (along === 'x') D.add(x - s / 2, y, z - 0.08, x + s / 2, y + s, z + 0.08, mat, { fit: 1 }); else D.add(x - 0.08, y, z - s / 2, x + 0.08, y + s, z + s / 2, mat, { fit: 1 });
}
// the world outside the fence F: the fence is the edge of the play area. the ground just past it is real (get over the
// fence and you land on grass with the countdown going, not in an invisible void), everything else is render-only: grass
// to the horizon, a wood round the fence, the road past the gate (west) with streetlights, a machine yard across it,
// billboards. the scenery adds the city on the horizon
function depotOutside(B, D, r, F) {
  const { x0, z0, x1, z1 } = F, RX0 = x0 - 30, RX1 = x0 - 18, R = 170;
  const Dw = D.local(0, 0, 0);
  groundHoles(B, x0 - 40, z0 - 40, x1 + 40, z1 + 40, -1, 0, 'grass', [[x0, z0, x1, z1], [x0 - 18, -6, x0, 6], [RX0, z0 - 40, RX1, z1 + 40]]);
  groundHoles(D, x0 - R, z0 - R, x1 + R, z1 + R, -1, 0, 'grass', [[x0 - 40, z0 - 40, x1 + 40, z1 + 40], [RX0, z0 - R, RX1, z1 + R]]);
  horizon(D, x0 - R, z0 - R, x1 + R, z1 + R, 1500, 'grass');
  B.add(x0 - 18, -1, -6, x0, 0.04, 6, 'concrete'); // the drive from the road to the gate
  B.add(RX0, -1, z0 - 40, RX1, 0.06, z1 + 40, 'roadz'); D.add(RX0, -1, -900, RX1, 0.06, z0 - 40, 'roadz'); D.add(RX0, -1, z1 + 40, RX1, 0.06, 900, 'roadz');
  for (const x of [RX0 + 0.4, RX1 - 0.6]) D.add(x, 0.06, z0 - R, x + 0.2, 0.07, z1 + R, 'white');
  for (let z = -870; z <= 870; z += 36) streetlight(Dw, RX0 - 1, z, 1);
  const tree = (x, z, h) => { if (x > RX0 - 5 && x < RX1 + 5) return; if (x > x0 - 20 && x < x0 && Math.abs(z) < 12) return; (r() < 0.45 ? conifer : lollipop)(Dw, x, z, h, r); };
  for (let k = 0; k < 5; k++) { // a woodland belt round the fence, five rows deep (none across the road or the drive)
    for (let x = x0 - 10; x < x1 + 40; x += 6.5) for (const sz of [-1, 1]) if (r() < 0.85) tree(x + (r() - 0.5) * 3, (sz < 0 ? z0 - 6 - k * 7 : z1 + 6 + k * 7) + (r() - 0.5) * 3, 5 + r() * 3.5);
    for (let z = z0 - 40; z <= z1 + 40; z += 6.5) if (r() < 0.85) tree(x1 + 6 + k * 7 + (r() - 0.5) * 3, z + (r() - 0.5) * 3, 5 + r() * 3.5);
    for (let z = z0 - 160; z <= z1 + 160; z += 6.5) if (r() < 0.85) tree(RX0 - 12 - k * 7 + (r() - 0.5) * 3, z + (r() - 0.5) * 3, 5 + r() * 3.5); // across the road
  }
  for (let i = 0; i < 260; i++) { const a = r() * Math.PI * 2, d = 130 + r() * 220, x = (x0 + x1) / 2 + Math.cos(a) * d * 1.2, z = Math.sin(a) * d; if (x > x0 - 40 && x < x1 + 40 && z > z0 - 40 && z < z1 + 40) continue; tree(x, z, 6 + r() * 5); }
  // machinery between the fence and the road, and a machine yard across it
  excavator(D, x0 - 8, z0 + 18, 3); bulldozer(D, x0 - 8, z1 - 22, 1); generatorTower(D, x0 - 7.5, z1 - 10, 1); pipeStack(D, x0 - 8.5, -24, true); gravelPile(D, x0 - 8, 26, 7);
  cones(D, x0 - 16, -7.5, x0 - 3, -7.5, 5); cones(D, x0 - 16, 7.5, x0 - 3, 7.5, 5);
  mixerTruck(D, RX0 - 14, -30, 1); roller(D, RX0 - 12, 26, 2); excavator(D, RX0 - 24, 40, 0); bulldozer(D, RX0 - 28, -48, 1); mixerTruck(D, RX0 - 32, 18, 3);
  gravelPile(D, RX0 - 22, -14, 12, 'dirt'); gravelPile(D, RX0 - 10, 52, 9); gravelPile(D, RX0 - 34, -24, 10, 'sand');
  adBoard(D, RX0 - 8, 0, 0, 'z', 'adcity2', 26, 10); // JANK COLA, across the road from the gate
  adBoard(D, RX0 - 10, -260, 0, 'z', 'adcity1', 22, 9); adBoard(D, RX0 - 10, 300, 0, 'z', 'adcity3', 22, 9);
}

// ------------------------------------------------------------ WAREHOUSE S&D: plant & defuse at a depot on the night shift.
// an original layout on the bomb-map rules. attackers come in at the west gate, defenders hold the east end, and the hall
// stands between the two spawns (neither can see the other). three lanes:
//   north: the container yard, long and open (sightlines for the long guns), ends in the A main choke between two stacks
//   mid:   the hall: racking down both sides, the foreman's office in the middle (no straight line through), a door north
//          to the end of the container yard, a door south to the trailer park, and the east door into the courtyard
//   south: the trailer park, tight (rows of trailers to weave through), ends at B's roller door
// the courtyard behind the hall joins both sites on the defenders' side: they rotate through it in ~5 s, attackers go back
// round through the hall. A = the container dock (outside, red), B = the parcel shed (inside, cyan), 3 ways into each
function warehouseSD() {
  const B = builder(), D = builder();
  const { add, box } = B;
  const r = rng(6161), W = B.local(0, 0, 0);
  // trailers here get side skirts down to the ground: no shooting under them (the tight lanes stay tight)
  const trailerS = (x0, z0, liv) => { trailer(B, x0, z0, liv); add(x0 + 0.3, 0, z0 + 0.55, x0 + 12.2, 1.3, z0 + 2.05, 'metal'); };
  const semiS = (x, z, rot, liv, cab) => { semi(B, x, z, rot, liv, cab); B.local(x, z, rot)(-0.75, 0, 0.3, 0.75, 1.3, 12.2, 'metal'); };
  const FX = 80, FZ = 58, F = { x0: -FX, z0: -FZ, x1: FX, z1: FZ }, bounds = [-FX, -FZ, FX, FZ];
  const HX = 24, HZ = 22, H = 9; // the hall
  // ---- the ground: one concrete slab, asphalt where the trucks go, paint
  add(-FX, -1, -FZ, FX, 0, FZ, 'concrete');
  add(-FX, 0, -FZ, 24, 0.03, -HZ - 0.4, 'asphalt2'); // the container yard
  add(-FX, 0, HZ + 0.4, 24.2, 0.03, FZ, 'asphalt2'); // the trailer park
  add(-FX, 0, -HZ - 0.4, -HX - 0.4, 0.03, HZ + 0.4, 'asphalt2'); // the apron in front of the hall and the gate
  add(61.2, 0, -FZ, FX, 0.03, FZ, 'asphalt2'); // the staff car park and the paths round the staff block
  for (let x = 66; x <= 78; x += 4) add(x, 0.03, -16, x + 0.15, 0.045, 16, 'white'); // parking bays
  for (const z of [-HZ - 1.2, HZ + 1.2]) add(-60, 0.03, z - 0.1, 22, 0.045, z + 0.1, 'neonyellow'); // walkway lines along the hall
  // ---- the fence (the gate in the west side is shut behind the attackers' truck)
  chainFence(B, D, -FX, -FZ, FX, -FZ); chainFence(B, D, -FX, FZ, FX, FZ); chainFence(B, D, FX, -FZ, FX, FZ);
  chainFence(B, D, -FX, -FZ, -FX, -6); chainFence(B, D, -FX, 6, -FX, FZ);
  add(-FX - 0.3, 0.05, -5.9, -FX - 0.15, 4.2, 5.9, 'fence'); // the sliding gate, shut
  depotOutside(B, D, r, F);
  for (const [x, z] of [[-76, -54], [-76, 54], [76, -54], [76, 54], [0, -54], [0, 54], [44, -12]]) { box(x, 7, z, 0.5, 14, 0.5, 'metal'); D.box(x, 14.2, z, 2.6, 0.5, 1, 'lamp'); } // light masts

  // ---- ATTACKERS' SPAWN: inside the gate, behind their trailers
  semiS(-61, -15, 0, 'adtruck', false); semiS(-61, 2.5, 0, 'adtruck2', false); // two trailers screen it (a gap between them)
  semiS(-76.5, 9, 0, 'adtruck2', true); // the truck that brought them
  const GB = B.local(-75, -13, 0); // the guard booth (nobody home)
  shell(GB, 4, 3.4, 1, 2.8, 'toyteal', { roof: 'toyred', floor: 'tile', parapet: false });
  GB(-1.6, 0.12, 0.4, 1.6, 0.95, 1.4, 'wood'); GB.B(0.8, 1.2, 0.9, 0.7, 0.45, 0.1, 'tvstatic');
  barrier(B, -66, -20, false); barrier(B, -66, 20, false);
  const att = [[-73, 0.1, -6], [-73, 0.1, 0], [-73, 0.1, 5], [-67, 0.1, -9], [-67, 0.1, -3], [-67, 0.1, 3], [-67, 0.1, 9]];

  // ---- the apron (between the attackers and the hall's west door): a little cover, the way into mid
  forklift(B, -44, -10, 1); container(B, -40, 14, true, 1, ['containerg']); barrier(B, -34, -4, true); barrier(B, -50, 4, true);
  pallets(B, -30, 17, 5, r); pallets(B, -28.6, 17, 3, r); cratePile(B, -54, -16, 5, r); palletLoad(B, -46, 16);

  // ---- MID: the hall
  wall(W, 'x', -HZ, -HX - 0.3, HX + 0.3, 0, H, 0.6, 'metal', [{ a: 8, b: 13, y0: 0, y1: 3.6 }, ...windows(2 * HX, 5.5, 0, 2, 8)]); // north: the door to the container yard
  wall(W, 'x', HZ, -HX - 0.3, HX + 0.3, 0, H, 0.6, 'metal', [{ a: -4, b: 1, y0: 0, y1: 3.6 }, ...windows(2 * HX, 5.5, 0, 2, 8)]); // south: to the trailer park
  wall(W, 'z', -HX, -HZ + 0.3, HZ - 0.3, 0, H, 0.6, 'metal', [{ a: 2, b: 10, y0: 0, y1: 5 }]); // west: the big roller door
  wall(W, 'z', HX, -HZ + 0.3, HZ - 0.3, 0, H, 0.6, 'metal', [{ a: -10, b: -3, y0: 0, y1: 4.5 }]); // east: to the courtyard
  add(-HX - 0.3, H, -HZ - 0.3, HX + 0.3, H + 0.5, HZ + 0.3, 'roofblue');
  D.add(-HX - 0.35, 5.2, 0.5, -HX - 0.31, 5.9, 11.5, 'hazard'); D.add(-HX - 0.5, 6.2, 2, -HX - 0.36, 8.2, 10, 'adware', { fit: 1 }); // over the roller door
  for (let z = -18; z <= 18; z += 6) {
    add(-HX, H - 1.4, z - 0.25, HX, H - 0.9, z + 0.25, 'wood'); // rafters
    for (let x = -18; x <= 18; x += 12) { D.add(x - 0.03, H - 3.6, z - 0.03, x + 0.03, H - 1.4, z + 0.03, 'tire'); D.add(x - 0.6, H - 3.9, z - 0.6, x + 0.6, H - 3.6, z + 0.6, 'metal'); D.add(x - 0.45, H - 3.96, z - 0.45, x + 0.45, H - 3.9, z + 0.45, 'lamp'); }
  }
  for (const z of [-7.4, 7.2]) add(-20, 0, z - 0.06, 20, 0.02, z + 0.06, 'neonyellow'); // the aisle lines
  rack(B, -18, -9, 18, r); rack(B, 0, 9, 18, r); // racking: north side in the west half, south side in the east half
  const O = B.local(6, 0, 1); // the foreman's office in the middle of the floor (doors west and east, windows all round)
  shell(O, 8, 10, 1, 3.2, 'magenta', { floor: 'leopard', roof: 'roofg', parapet: false, backDoor: true });
  O(-3, 0.12, -1, -1, 0.85, 3, 'wood'); O(1.5, 0.12, -1, 3.5, 0.85, 3, 'wood'); O.B(-2, 1.15, 1, 0.9, 0.6, 0.1, 'tvstatic'); O.B(2.5, 1.15, 1, 0.9, 0.6, 0.1, 'tvstatic');
  forklift(B, -12, 15, 0, 1.4); forklift(B, 17, -15, 3);
  pallets(B, -21, -18, 6, r); pallets(B, -19.6, -18, 4, r); pallets(B, 18, 16, 7, r); pallets(B, 19.4, 16, 5, r);
  cratePile(B, -8, -17, 6, r);
  for (let i = 0; i < 5; i++) box(20 + (i % 3) * 0.85, 0.6, -19 + Math.floor(i / 3) * 0.85, 0.75, 1.2, 0.75, i % 2 ? 'barrelr' : 'barrel');

  // ---- NORTH: the container yard, A long
  container(B, -50, -46, false, 2, ['containerg', 'containerr']);
  container(B, -34, -32, true, 1, ['containerb']);
  container(B, -20, -52, false, 1, ['containerr']); cratePile(B, -12, -55, 5, r);
  container(B, -6, -40, false, 2, ['containerb', 'containerg']);
  container(B, 16, -32, false, 1, ['containerg']);
  pallets(B, -40, -55, 6, r); pallets(B, 4, -50, 5, r); pallets(B, 5.4, -50, 3, r);
  container(B, 26.75, -54, true, 2, ['containerr', 'containerb'], 8); // A main: between this stack...
  container(B, 26.75, -32.15, true, 2, ['containerg', 'containerr'], 15.7); // ...and this one
  add(24.3, 0, -24.3, 25.5, 2.6, -21.7, 'concrete'); // (the corner by the hall: no way through to the courtyard)

  // ---- A: the container dock (outside, red)
  add(24, 0, -24.3, 40, 3.4, -23.7, 'concrete'); add(46, 0, -24.3, 61, 3.4, -23.7, 'concrete'); // its wall to the courtyard (the A gate between)
  add(60.4, 0, -FZ, 61, 3.4, -38, 'concrete'); add(60.4, 0, -32, 61, 3.4, -24.3, 'concrete'); // to the staff path (the back way in)
  add(28, 0.03, -57.9, 60.4, 0.05, -24.3, 'dockred');
  container(B, 45, -44, false, 2, ['containerr', 'containerr']); // the A box
  container(B, 54.75, -33, true, 1, ['containerg'], 6);
  cratePile(B, 32, -33, 6, r); pallets(B, 36, -51, 4, r); pallets(B, 37.4, -51, 6, r); forklift(B, 55, -49, 1, 1.2);
  barrier(B, 46, -28.5, false); palletLoad(B, 36, -46); palletLoad(B, 51, -38, 1);
  for (const x of [31.5, 57.5]) box(x, 5, -55.5, 0.9, 10, 0.9, 'toyorange'); // a gantry crane over the dock
  D.add(31, 10, -56, 58, 11, -55, 'toyorange'); D.add(43, 8.6, -56.2, 46, 10, -54.8, 'hazard'); D.add(44.4, 4.2, -55.55, 44.6, 8.6, -55.45, 'tire'); D.add(43.6, 3.4, -56.2, 45.4, 4.2, -54.8, 'metal');
  siteBoard(D, 45, 4.6, -57.85, 'x', 'sitea', 5); siteBoard(D, 51, 0.6, -24.38, 'x', 'sitea', 2.6);

  // ---- the courtyard: the defenders' side, between the hall's east door and both sites
  const DB = B.local(40, -4, 1); // the dispatch booth (in the line from the hall's east door)
  shell(DB, 6, 4.4, 1, 2.9, 'toyteal', { roof: 'toyred', floor: 'tile', parapet: false, backDoor: true });
  DB.B(0, 1.15, 1.8, 0.9, 0.6, 0.1, 'tvstatic');
  forklift(B, 33, 12, 0); pallets(B, 48, 14, 6, r); pallets(B, 49.4, 14, 4, r); barrier(B, 31, -16, true); barrier(B, 52, -14, false);
  trailerS(30, 17, 'adtruck'); palletLoad(B, 36, 4); palletLoad(B, 52, 18, 1);
  for (let i = 0; i < 4; i++) box(54 + (i % 2) * 0.85, 0.6, 6 + Math.floor(i / 2) * 0.85, 0.75, 1.2, 0.75, i % 2 ? 'barrel' : 'barrelr');
  add(24.3, 0, 21.7, 30.25, 2.4, 27.75, 'wood'); // the bin store in the corner (no way through to the trailer park)
  // the staff block: the defenders spawn behind it, it hides them from the courtyard
  add(58, 0, -18, 63, 7.2, 18, 'magenta'); add(57.6, 7.2, -18.4, 63.4, 7.6, 18.4, 'roofg'); // (its roof is over the ceiling: no perch over the spawn)
  for (let z = -14; z <= 14; z += 4) for (const y of [1.2, 4.4]) { D.add(57.96, y, z - 1, 57.98, y + 1.8, z + 1, 'glass'); D.add(63.02, y, z - 1, 63.04, y + 1.8, z + 1, 'glass'); }
  D.add(57.9, 3.3, -6, 57.95, 4.2, 6, 'neonwork', { fit: 1 });

  // ---- DEFENDERS' SPAWN: the staff car park
  for (const [z, c] of [[-12, 'carred'], [-4, 'carblue'], [4, 'caryellow'], [12, 'cargreen']]) car(W, 77, z, 1, c);
  const def = [[67, 0.1, -9], [67, 0.1, -3], [67, 0.1, 3], [67, 0.1, 9], [72, 0.1, -6], [72, 0.1, 0], [72, 0.1, 6]];
  // the staff paths round the block: north to A's back way, south to B's back door
  container(B, 70, -42, true, 1, ['containerb']); pallets(B, 74, -28, 5, r); barrier(B, 66, -24, false);
  container(B, 70, 44, true, 1, ['containerr']); pallets(B, 74, 26, 6, r); barrier(B, 66, 24, false);

  // ---- B: the parcel shed (inside, cyan)
  const BX0 = 30, BX1 = 58, BZ0 = 28, BZ1 = 56, BH = 7.5;
  wall(W, 'x', BZ0, BX0 - 0.25, BX1 + 0.25, 0, BH, 0.5, 'containerb', [{ a: 40, b: 45, y0: 0, y1: 3.4 }]); // north: from the courtyard
  wall(W, 'x', BZ1, BX0 - 0.25, BX1 + 0.25, 0, BH, 0.5, 'containerb');
  wall(W, 'z', BX0, BZ0 + 0.25, BZ1 - 0.25, 0, BH, 0.5, 'containerb', [{ a: 38, b: 46, y0: 0, y1: 4.5 }]); // west: B main, the roller door
  wall(W, 'z', BX1, BZ0 + 0.25, BZ1 - 0.25, 0, BH, 0.5, 'containerb', [{ a: 32, b: 37, y0: 0, y1: 3.4 }]); // east: the defenders' back door
  add(BX0 - 0.25, BH, BZ0 - 0.25, BX1 + 0.25, BH + 0.5, BZ1 + 0.25, 'roofblue');
  add(BX0 + 0.25, 0, BZ0 + 0.25, BX1 - 0.25, 0.03, BZ1 - 0.25, 'floorcyan');
  add(34, 0, 44.5, 50, 1.0, 45.7, 'metal'); add(34, 1.0, 44.6, 50, 1.06, 45.6, 'tire'); // the sorting belt
  for (let x = 35; x < 49; x += 2.6) add(x, 1.06, 44.75, x + 0.7 + r() * 0.4, 1.5 + r() * 0.4, 45.45, 'cardboard');
  add(44, 0, 33, 48, 2.6, 37, 'toyteal'); add(43.9, 1.1, 32.9, 48.1, 1.5, 37.1, 'hazard'); // the sorter
  for (const [x, z] of [[36, 32], [52, 34], [53, 50], [35, 51], [41, 50]]) { add(x, 0, z, x + 1.4, 1.8, z + 1.4, 'grid'); add(x + 0.15, 0, z + 0.15, x + 1.25, 1.1, z + 1.25, 'cardboard'); } // parcel cages
  pallets(B, 51, 41, 5, r); pallets(B, 52.4, 41, 3, r); cratePile(B, 36, 37, 5, r);
  for (let x = 34; x <= 54; x += 10) { D.add(x - 0.6, BH - 1.2, 42 - 0.6, x + 0.6, BH - 0.9, 42 + 0.6, 'metal'); D.add(x - 0.45, BH - 1.26, 42 - 0.45, x + 0.45, BH - 1.2, 42 + 0.45, 'lamp'); }
  siteBoard(D, 44, 3.2, BZ1 - 0.33, 'x', 'siteb', 3.4); siteBoard(D, BX0 - 0.33, 4.8, 42, 'z', 'siteb', 2.6);
  D.add(BX0 + 0.26, 4.6, 38, BX0 + 0.3, 4.75, 46, 'neoncyan'); D.add(BX0 - 0.3, 4.6, 38, BX0 - 0.26, 4.75, 46, 'neoncyan');

  // ---- SOUTH: the trailer park, B long. three rows of trailers to weave through, the B yard at the end
  for (const x of [-52, -30, -8]) trailerS(x, 29, x === -30 ? 'adtruck2' : 'adtruck');
  for (const x of [-41, -19, 3]) trailerS(x, 40, x === -19 ? 'adtruck' : 'adtruck2');
  for (const x of [-52, -30, -8]) trailerS(x, 51, x === -8 ? 'adtruck2' : 'adtruck');
  for (const [x, z] of [[-60, 36], [-20, 47], [10, 34]]) { add(x, 0, z, x + 2.6, 1.5, z + 1.6, 'containerg'); add(x - 0.05, 1.5, z - 0.05, x + 2.65, 1.62, z + 1.65, 'metal'); } // dumpsters
  pallets(B, 18, 48, 6, r); pallets(B, 19.4, 48, 4, r); forklift(B, 22, 38, 2, 1.2); barrier(B, 25, 47, true); palletLoad(B, -36, 47); palletLoad(B, 12, 46, 1);
  for (let i = 0; i < 5; i++) for (let k = 0; k <= i % 3; k++) box(-46 + i * 1.1, 0.15 + k * 0.3, 46, 1, 0.3, 1, 'tire');

  const spawns = [[-50, 0.1, -36], [-22, 0.1, -45], [6, 0.1, -30], [-42, 0.1, 0], [-12, 0.1, -14], [13, 0.1, 15], [-30, 0.1, 35], [0, 0.1, 47],
    [20, 0.1, 33], [40, 0.1, -40], [46, 0.1, 6], [44, 0.1, 42], [70, 0.1, -36], [70, 0.1, 36], [-70, 0.1, 30], [-70, 0.1, -30]];
  let graph = null;
  const map = {
    name: 'Warehouse', size: 'large', boxes: B.boxes, deco: D.boxes, killY: -45, bounds, ceiling: 7, floorY: -50,
    sky: { top: 0x0a0a20, mid: 0x5a2a6a, bot: 0x050508, fog: 0x3a2448 }, fogNear: 70, fogFar: 300,
    spawns, teamSpawns: { att, def },
    // bot routes down the three lanes (each leg walked through the walk graph)
    nav: {
      A: [
        [[-64, -18], [-56, -30], [-40, -38], [-26, -46], [-6, -47], [12, -45], [22, -45], [30, -45], [38, -38]], // the container yard
        [[-60, 0], [-40, 6], [-24, 6], [-14, 6], [-1, 0], [0, -6], [10.5, -15], [10.5, -27], [20, -40], [30, -45], [40, -38]], // the hall, north door
        [[-60, 0], [-40, 6], [-24, 6], [-10, 6], [14, 6], [20, -6.5], [30, -6.5], [36, -14], [43, -20], [43, -28], [43, -34]], // the hall, the courtyard
      ],
      B: [
        [[-64, 18], [-56, 26], [-45, 36], [-25, 36], [-2, 36], [18, 36], [26, 42], [34, 42], [42, 42]], // the trailer park
        [[-60, 0], [-40, 6], [-24, 6], [-14, 6], [-8, 14], [-1.5, 16], [-1.5, 26], [10, 36], [26, 42], [36, 42]], // the hall, south door
        [[-60, 0], [-40, 6], [-24, 6], [-10, 6], [14, 6], [20, -6.5], [30, -6.5], [34, 6], [42.5, 22], [42.5, 31], [42.5, 38]], // the hall, the courtyard
      ],
    },
    sites: [{ id: 'A', min: [31, 0, -54], max: [58, 0, -27] }, { id: 'B', min: [32, 0, 30], max: [56, 0, 54] }],
    get graph() { return graph || (graph = buildNav(B.boxes, { x0: bounds[0] - 1, z0: bounds[1] - 1, n: bounds[2] - bounds[0] + 2, cell: 1, levels: [0], band: 0.5, keep: (x, z) => !outOfBounds(map, [x, 0, z]) })); },
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
  D.add(-9, -66, -284, -7, -2, 284, 'rock'); D.add(7, -66, -284, 9, -2, 284, 'rock');
  for (const sz of [-1, 1]) D.add(-9, -66, sz > 0 ? 284 : -288, 9, -2, sz > 0 ? 288 : -284, 'rock');
  D.add(-7, -67, -284, 7, -66, 284, 'sand'); D.add(-3.5, -66, -284, 3.5, -65.8, 284, 'water');
  for (const z of [-180, -40, 20, 130, 220]) D.add(-5 + rv() * 3, -65.8, z, -1 + rv() * 3, -64.6 + rv(), z + 2 + rv() * 3, 'rock');
  D.add(-4, -65.8, 66, 4, -65.3, 68.5, 'wood'); // somebody's old bridge
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
  const map = { name: 'Desert', size: 'large', boxes: B.boxes, deco: D.boxes, killY: -50, bounds, floorY: -69,
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
  const stack = (x, z, w, top) => { D.box(x, (top - 64) / 2, z, w, top + 64, w, 'rock'); D.box(x + w * 0.1, -56.5, z - w * 0.08, w * 1.35, 15, w * 1.3, 'rock'); D.box(x, -61.9, z, w * 1.5, 0.3, w * 1.45, 'white'); };
  stack(0, 0, 22, -19); stack(0, -88, 18, -10); stack(0, 88, 18, -10); stack(88, 0, 18, -10); stack(-88, 0, 18, -10);
  for (let i = 0; i < 9; i++) { const a = (i / 9) * Math.PI * 2 + 0.3, d = 130 + (i % 3) * 40; D.box(Math.cos(a) * d, -50 + (i % 2) * 8, Math.sin(a) * d, 8 + (i % 3) * 4, 28 + (i % 2) * 16, 8 + (i % 2) * 5, 'rock'); } // lonely rocks offshore
  return { name: 'Islands', size: 'large', boxes, deco: D.boxes, killY: -65, floorY: -62, sky: SKY_SUNSET, fogNear: 90, fogFar: 330,
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
    B.box(x, base - 10, z, w, 20, d, 'office'); // a foundation down to the (lowered) street
    roofs[`${x},${z}`] = ry;
    spawns.push([x + 4, ry + 0.1, z + 4]);
  }
  // construction site: open floors, columns, a crane
  {
    const cx = 35, cz = -100, w = 30, F = 4.5;
    B.box(cx, (base + 0) / 2, cz, w, 0 - base, w, 'concrete'); B.box(cx, base - 10, cz, w, 20, w, 'concrete');
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
  streetLevel(D, -120, towers, { xs: [-135, -67.5, 0, 67.5, 135], zs: [-135, -67.5, 0, 67.5, 135], w: 18 }, 190, r);
  cityDress(D, plan, roofs, base, r);
  cityBeyond(D, -120, 190, 680, rng(4040), { kill: -108, cap: 30, shore: 470, avenues: [[-60, -230, 0.42], [230, 40, -1.05], [-300, 120, 1.25], [80, -420, 0.06], [-250, -250, 2.35]], streets: gridOut([-135, -67.5, 0, 67.5, 135], [-135, -67.5, 0, 67.5, 135], 190, 230) });
  return { name: 'Skyline', size: 'huge', boxes: B.boxes, deco: D.boxes, killY: -108, floorY: -128, cityR: 680, cityCap: 30,
    haze: { k: 0.88, top: 15, bottom: -120, dist: 120, color: 0xc89aa4 }, // look down: the city through a dusk haze
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
    name: 'Bazaar', size: 'large', boxes: B.boxes, deco: D.boxes, killY: -50, floorY: -6, bounds: [X0 - 1.5, Z0 - 1.5, X1 + 1.5, Z1 + 1.5],
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
  const N = 60, U = 4, O = -120, H = 4.2, HH = 9, PY = -4.5, T = 0.2; // grid cells, cell size, map edge, ceilings (raised: more room to jump and grapple), pool floor, wall thickness
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
    name: 'Backrooms', size: 'extra large', boxes: B.boxes, deco: D.boxes, killY: -50,
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
  horizon(D, -220, -280, 220, 160, 1500, 'grass'); // the same grass as the field you stand on
  D.add(-60, 0, -175, 60, 12, -160, 'dirt'); D.add(-50, 12, -172, 50, 16, -163, 'dirt'); // the berm the bullets end up in
  for (let x = -18; x <= 18; x += 3.2) D.add(x, 0, 6.4, x + 3, 0.8, 7.4, 'sand'); // sandbags on the firing line
  for (const [x, z] of [[-30, 20], [30, 20]]) { for (const sx of [-1, 1]) for (const sz of [-1, 1]) D.box(x + sx * 1.6, 4, z + sz * 1.6, 0.3, 8, 0.3, 'wood'); D.add(x - 2.2, 8, z - 2.2, x + 2.2, 8.3, z + 2.2, 'wood'); D.add(x - 2.4, 10.5, z - 2.4, x + 2.4, 10.8, z + 2.4, 'roofg'); } // watchtowers
  for (let z = 30; z > -260; z -= 10) for (const x of [-90, 90]) { D.box(x, 1, z, 0.15, 2, 0.15, 'metal'); D.add(x - 0.03, 1.6, z, x + 0.03, 1.65, z + 10, 'tire'); }
  for (let i = 0; i < 30; i++) { const rr = rng(400 + i), a = rr() * Math.PI * 2, d = 150 + rr() * 150; (rr() < 0.5 ? conifer : lollipop)(D.local(0, 0, 0), Math.cos(a) * d, -60 + Math.sin(a) * d, 6 + rr() * 4, rr); }
  adBoard(D, -26, -70, 0, 'z', 'adcity6', 14, 6); adBoard(D, -26, -110, 0, 'z', 'adcity3', 14, 6); adBoard(D, 0, -130, 0, 'x', 'adcity2', 24, 9);
  return { name: 'Range', size: 'training', boxes, deco: D.boxes, killY: -60, floorY: -4, bounds: [-90, -175, 90, 40],
    sky: { top: 0x3a7bd5, mid: 0xbfe3ff, bot: 0x203040, fog: 0xbfe3ff }, fogNear: 120, fogFar: 420,
    spawns: [[0, 0.1, 10], [5, 0.1, 10], [-5, 0.1, 10]],
    dummies: [
      { p: [0, 0, -10] }, { p: [-8, 0, -25] }, { p: [8, 0, -25], move: 4 }, { p: [0, 0, -50], move: 6 },
      { p: [-10, 0, -100] }, { p: [10, 0, -100], move: 8 }, { p: [-28, 0, -35] }, { p: [-28, 0, -45], move: 3 },
    ] };
}

// ------------------------------------------------------------ SCARY FOREST: a pine forest at night, in the fog, by a lake
// a dark pine wood (trunks are cover, the canopies are only drawn), a clearing with a stone circle and an office chair
// nobody can explain, an abandoned cabin (site A), a campsite with a dead campfire, a fire lookout tower to climb, a dirt
// road with a broken-down car that ends at a boat ramp, a lake with a dock, and a radio mast blinking red over its fenced
// yard (site B). the woods carry on past the property line into the fog in every direction but east, where the lake is.
// Plant & Defuse: attackers start at the trailhead (south-west), defenders at the ranger lot (north).
// The Tall Guy From HR walks these woods (server/hrguy.js): map.hr says where he may stand and where he sends people
const FOREST = { bounds: [-100, -84, 100, 84], shore: 72 };
function pine(B, D, x, z, h, r) { // a pine: a trunk you bump into, a stack of turned tiers you only see
  const tw = 0.26 + r() * 0.16;
  B.add(x - tw, 0, z - tw, x + tw, h * 0.94, z + tw, r() < 0.15 ? 'bark2' : 'bark');
  const n = 5 + ((r() * 2) | 0), base = h * (0.3 + r() * 0.08), span = h - base, w0 = 3.4 + r() * 1.6, yaw = r() * 3;
  for (let i = 0; i < n; i++) {
    const k = i / n, w = w0 * (1 - k * 0.82), y = base + k * span;
    D.obb(x, y + span / n * 0.62, z, w, span / n * 1.3, w * (0.82 + r() * 0.3), yaw + i * 0.7 + r() * 0.3, (i + ((x * 7) | 0)) % 3 ? 'pine' : 'pine2');
  }
  D.obb(x, h + 0.45, z, 0.5, 1.1, 0.5, yaw, 'pine2');
}
function deadTree(B, D, x, z, h, r) { // bare, grey, too many elbows
  B.add(x - 0.3, 0, z - 0.3, x + 0.3, h, z + 0.3, 'deadbark');
  for (let i = 0; i < 5; i++) {
    const y = h * (0.4 + i * 0.12), l = 1.2 + r() * 1.8 * (1 - i * 0.12), a = r() * 6.3;
    D.obb(x + Math.cos(a) * l / 2, y, z + Math.sin(a) * l / 2, l, 0.16, 0.16, -a, 'deadbark');
    D.obb(x + Math.cos(a) * l, y + 0.45, z + Math.sin(a) * l, 0.12, 0.9, 0.12, -a, 'deadbark'); // the elbow up at the end
  }
}
function birch(B, D, x, z, h, r) { // white trunks: they catch the flashlight, so you think something is standing there
  B.add(x - 0.2, 0, z - 0.2, x + 0.2, h, z + 0.2, 'birch');
  for (let i = 0; i < 3; i++) D.obb(x + (r() - 0.5) * 0.8, h * (0.62 + i * 0.13), z + (r() - 0.5) * 0.8, 2.4 - i * 0.5, 1.1, 2.0 - i * 0.4, r() * 3, 'birchleaf');
}
function log(B, x0, z0, x1, z1, rr = 0.42) { // a fallen log along x or z (with a lighter cut end)
  const ax = Math.abs(x1 - x0) > Math.abs(z1 - z0);
  if (ax) { B.add(x0, 0, z0 - rr, x1, rr * 2, z0 + rr, 'logside'); B.add(x1, 0.02, z0 - rr + 0.04, x1 + 0.06, rr * 2 - 0.04, z0 + rr - 0.04, 'logend'); }
  else { B.add(x0 - rr, 0, z0, x0 + rr, rr * 2, z1, 'logside'); B.add(x0 - rr + 0.04, 0.02, z1, x0 + rr - 0.04, rr * 2 - 0.04, z1 + 0.06, 'logend'); }
}
function boulder(B, x, z, s, r) { // a rock: a big block and a couple of smaller ones shoved into it
  B.add(x - s, 0, z - s * 0.8, x + s, s * 1.1, z + s * 0.8, 'rockf');
  B.add(x - s * 0.7, s * 1.1, z - s * 0.5, x + s * 0.5, s * 1.5, z + s * 0.6, 'rockf');
  if (r() < 0.6) B.add(x + s * 0.7, 0, z + s * 0.4, x + s * 1.5, s * 0.7, z + s * 1.2, 'rockmoss');
}
// a wrecked sedan facing +x: hood up, driver door hanging open, a flat at the front, hazards still blinking
function brokenCar(B, D, x, z) {
  B.add(x - 2.3, 0.35, z - 0.95, x + 2.3, 1.0, z + 0.95, 'carrust');
  B.add(x - 1.2, 1.0, z - 0.85, x + 0.8, 1.55, z + 0.85, 'glassdark'); B.add(x - 1.25, 1.55, z - 0.87, x + 0.85, 1.65, z + 0.87, 'carrust');
  B.add(x - 0.25, 1.0, z - 0.88, x - 0.1, 1.55, z - 0.84, 'carrust'); B.add(x - 0.25, 1.0, z + 0.84, x - 0.1, 1.55, z + 0.88, 'carrust');
  for (const [sx, sz, flat] of [[-1.5, -1, 0], [-1.5, 1, 0], [1.4, -1, 1], [1.4, 1, 0]]) B.add(x + sx - 0.36, 0, z + sz * 0.95 - 0.15, x + sx + 0.36, flat ? 0.42 : 0.7, z + sz * 0.95 + 0.15, 'tire');
  B.add(x + 0.95, 1.0, z - 0.85, x + 1.05, 2.25, z + 0.85, 'carrust'); // the hood, propped up
  B.add(x + 1.3, 0.9, z - 0.6, x + 2.1, 1.25, z + 0.6, 'metal'); // the engine nobody fixed
  B.add(x - 0.1, 0.4, z + 0.95, x + 0.04, 1.4, z + 2.1, 'carrust'); // the driver door, hanging open (wrong side: it's that kind of night)
  B.add(x + 2.3, 0.62, z - 0.8, x + 2.36, 0.82, z - 0.45, 'hazard2'); B.add(x + 2.3, 0.62, z + 0.45, x + 2.36, 0.82, z + 0.8, 'hazard2');
  B.add(x - 2.36, 0.62, z - 0.8, x - 2.3, 0.82, z - 0.45, 'hazard2'); B.add(x - 2.36, 0.62, z + 0.45, x - 2.3, 0.82, z + 0.8, 'hazard2');
  B.add(x - 2.4, 0.3, z - 0.9, x - 2.3, 0.55, z + 0.9, 'chrome'); B.add(x + 2.3, 0.3, z - 0.9, x + 2.4, 0.55, z + 0.9, 'chrome');
  D.obb(x - 7, 0.35, z - 0.4, 0.9, 0.7, 0.08, 0.3, 'warnsign'); // a warning triangle (a square, it's a budget triangle)
}
function forest() {
  const B = builder(), D = builder();
  const r = rng(6660);
  const W = B.local(0, 0, 0);
  const [bx0, bz0, bx1, bz1] = FOREST.bounds, SH = FOREST.shore;
  // ---- the ground: forest floor out a long way (past the lake shore it's mud under water), a dirt road
  B.add(-260, -3, -220, SH, 0, 220, 'needles');
  B.add(SH, -3, -220, SH + 4, -0.22, 220, 'mud'); B.add(SH + 4, -3, -220, SH + 9, -0.48, 220, 'mud'); B.add(SH + 9, -3, -220, 260, -0.7, 220, 'mud'); // the lake bed shelves away
  horizon(D, -260, -220, 260, 220, 1500, 'needles', 0);
  D.add(SH, -0.36, -1500, 1500, -0.3, 1500, 'lakewater'); // the lake, all the way out
  const RZ0 = 52, RZ1 = 60; // the dirt road, west to east, gone into the fog one way and into the lake the other
  B.add(-260, 0, RZ0, SH - 2, 0.06, RZ1, 'dirtroad'); D.add(-1500, 0, RZ0, -260, 0.06, RZ1, 'dirtroad');
  for (let i = 0; i < 4; i++) B.add(SH - 2 + i * 2, -0.1 - i * 0.12, RZ0 + 1, SH + i * 2, 0.08 - i * 0.12, RZ1 - 1, 'planks'); // the boat ramp
  // ---- trails: drawn on the floor (render only, each a hair higher than the last so no two share a plane)
  const trails = [];
  const trail = (pts, w = 2.6) => { for (let i = 0; i + 1 < pts.length; i++) trails.push([pts[i], pts[i + 1], w]); };
  const TH = [-78, 68], CAMP = [-30, 30], CLR = [0, -10], CAB = [-50, -24], TWR = [24, -50], DEF = [21, -72], MAST = [52, 4], DOCK = [SH, -32];
  trail([TH, [-62, 46], [-44, 36], CAMP]); trail([CAMP, [-12, 10], CLR]); trail([CLR, [-28, -12], [CAB[0], -16]]);
  trail([[CAB[0], -32], [-42, -54], [-6, -68], DEF]); trail([CLR, [10, -30], [TWR[0], -46]]); trail([[TWR[0], -56], DEF]);
  trail([CLR, [26, -2], [41, 4]]); trail([[62, -4], [64, -22], [SH + 4, -32]]); trail([CAMP, [-30, RZ0]]); trail([[52, 14], [50, 34], [50, RZ0]]);
  trail([DEF, [48, -64], [62, -44], [SH - 2, -36]]); trail([TH, [-84, 30], [-78, -2], [-62, -20]]); trail([[-6, RZ0], [-4, 30], [-12, 10]]);
  trails.forEach(([a, b, w], i) => { const dx = b[0] - a[0], dz = b[1] - a[1], l = Math.hypot(dx, dz); D.obb((a[0] + b[0]) / 2, 0.012 + (i % 9) * 0.003, (a[1] + b[1]) / 2, l + w, 0.02, w, -Math.atan2(dz, dx), 'trail'); });
  const segD = (x, z, a, b) => { const dx = b[0] - a[0], dz = b[1] - a[1], l2 = dx * dx + dz * dz || 1, t = Math.max(0, Math.min(1, ((x - a[0]) * dx + (z - a[1]) * dz) / l2)); return Math.hypot(x - a[0] - dx * t, z - a[1] - dz * t); };
  // places trees keep out of: [x, z, radius] and [x0, z0, x1, z1]
  const holes = [[CLR[0], CLR[1], 17], [CAMP[0], CAMP[1], 12], [TWR[0], TWR[1], 9], [-48, -24, 11], [-60, -16, 5], [TH[0], TH[1] - 1, 13], [DEF[0], DEF[1] + 2, 13], [-74, -52, 5], [-6, 56, 6]];
  const rects = [[41, -7, 64, 16], [-260, RZ0 - 2.5, SH, RZ1 + 2.5], [SH - 3, -220, 260, 220], [SH - 6, -36, SH + 20, -28]];
  const free = (x, z, pad = 0) => !holes.some(([hx, hz, hr]) => Math.hypot(x - hx, z - hz) < hr + pad) && !rects.some(([a, b, c, d]) => x > a - pad && x < c + pad && z > b - pad && z < d + pad) && !trails.some(([a, b, w]) => segD(x, z, a, b) < w / 2 + 0.9 + pad);
  const inPlay = (x, z) => x > bx0 - 2 && x < bx1 + 2 && z > bz0 - 2 && z < bz1 + 2;

  // free-for-all spawns all over the woods (trees keep off them)
  const spawns = [
    [CAB[0] + 2.5, 0.5, CAB[1] - 1], [CAB[0] - 4, 0.5, CAB[1] - 2.5], [CAMP[0] + 3, 0.2, CAMP[1] + 2], [CAMP[0] - 6, 0.2, CAMP[1] + 4],
    [TWR[0] + 4.5, 0.2, TWR[1] + 4.5], [TWR[0] + 1.5, 13.4, TWR[1] + 1.5], [MAST[0] - 5, 0.4, MAST[1] - 1], [MAST[0] + 6, 0.2, MAST[1] + 6], [SH + 8, 0.5, -32],
    [CLR[0] - 12, 0.2, CLR[1] - 3], [CLR[0] + 13, 0.2, CLR[1] + 6], [CLR[0], 0.2, CLR[1] + 13], [-8, 0.2, 53], [20, 0.2, 57], [48, 0.2, 56],
    [-78, 0.2, -10], [-86, 0.2, 40], [-60, 0.2, 10], [-20, 0.2, -44], [0, 0.2, -66], [40, 0.2, -30], [60, 0.2, 30], [10, 0.2, 30], [-74, 4.2, -52], [-30, 0.2, -70], [62, 0.2, -60],
  ];
  for (const p of spawns) holes.push([p[0], p[2], 2.2]);
  holes.push([CAMP[0] - 12, CAMP[1] + 9, 3]);

  // ---- the woods: a jittered grid, thicker in the deep parts, some dead ones, some birches. outside the property
  // line it's just more woods (render only past the first row: you can look, the RETURN countdown says not to go)
  const deep = (x, z) => 0.55 + 0.45 * Math.max(0, Math.sin(x * 0.045 + 1.3) * Math.cos(z * 0.05 - 0.4)); // thick and thin patches
  const plant = (T, x, z) => { const k = r(), h = 9 + r() * 7; if (k < 0.07) deadTree(T, D, x, z, 6 + r() * 4, r); else if (k < 0.16) birch(T, D, x, z, 7 + r() * 4, r); else pine(T, D, x, z, h, r); };
  const S = 4.2;
  for (let x = bx0 - 72; x < SH; x += S) for (let z = bz0 - 70; z < bz1 + 70; z += S) {
    const px = x + r() * S * 0.8, pz = z + r() * S * 0.8;
    if (px > SH - 3) continue;
    const near = inPlay(px, pz), edge = !near && px > bx0 - 9 && px < bx1 + 9 && pz > bz0 - 9 && pz < bz1 + 9;
    if (near ? r() > deep(px, pz) * 0.95 : r() > 0.6) continue;
    if (!free(px, pz)) continue;
    if (near || edge) plant(B, px, pz); else pine(D, D, px, pz, 9 + r() * 8, r);
  }
  // the far shore across the lake: a dark line of trees in the fog
  for (let z = -300; z < 300; z += 5) for (let k = 0; k < 3; k++) pine(D, D, 230 + k * 6 + r() * 5, z + r() * 4, 10 + r() * 8, r);
  // undergrowth: ferns and bushes (only drawn: bullets go through, eyes don't)
  for (let i = 0; i < 520; i++) { const x = bx0 - 20 + r() * (bx1 - bx0 + 40), z = bz0 - 20 + r() * (bz1 - bz0 + 40); if (x > SH - 2 || !free(x, z, -0.5)) continue; const s = 0.6 + r() * 0.8, a = r() * 3; if (r() < 0.55) { for (let k = 0; k < 3; k++) D.obb(x, s * 0.28, z, s * 1.5, s * 0.56, 0.07, a + k * 1.05, 'fern'); } else { D.obb(x, s * 0.3, z, s * 1.1, s * 0.6, s * 0.9, a, 'bush'); D.obb(x + 0.2, s * 0.75, z - 0.1, s * 0.7, s * 0.4, s * 0.6, a + 0.8, 'bush'); } } // ferns: three crossed fronds. bushes: a clump
  for (let i = 0; i < 70; i++) { const x = bx0 + r() * (bx1 - bx0), z = bz0 + r() * (bz1 - bz0); if (x > SH - 4 || !free(x, z, 1)) continue; if (r() < 0.55) { const l = 3 + r() * 4; r() < 0.5 ? log(B, x, z, x + l, z) : log(B, x, z, x, z + l); } else if (r() < 0.6) boulder(B, x, z, 0.6 + r() * 0.9, r); else B.add(x - 0.35, 0, z - 0.35, x + 0.35, 0.5 + r() * 0.4, z + 0.35, 'logend'); }

  // ---- the clearing: a ring of standing stones, one dead tree, and an office chair facing away from you
  for (let i = 0; i < 7; i++) { const a = (i / 7) * Math.PI * 2 + 0.3, x = CLR[0] + Math.cos(a) * 9.5, z = CLR[1] + Math.sin(a) * 9.5, tall = 1.8 + (i % 3) * 0.6; B.add(x - 0.6, 0, z - 0.45, x + 0.6, tall, z + 0.45, i % 2 ? 'rockf' : 'rockmoss'); }
  deadTree(B, D, CLR[0] + 3, CLR[1] - 2, 8.5, r);
  W(CLR[0] - 2.4, 0, CLR[1] + 1.7, CLR[0] - 1.8, 0.08, CLR[1] + 2.3, 'metal'); W(CLR[0] - 2.15, 0.08, CLR[1] + 1.95, CLR[0] - 2.05, 0.55, CLR[1] + 2.05, 'chrome'); // the office chair: base, stem
  W(CLR[0] - 2.45, 0.55, CLR[1] + 1.7, CLR[0] - 1.75, 0.68, CLR[1] + 2.4, 'officechair'); W(CLR[0] - 2.45, 0.68, CLR[1] + 2.32, CLR[0] - 1.75, 1.45, CLR[1] + 2.42, 'officechair');
  W(CLR[0] + 6, 0, CLR[1] + 4, CLR[0] + 6.6, 1.25, CLR[1] + 4.6, 'white'); W(CLR[0] + 6.05, 1.25, CLR[1] + 4.05, CLR[0] + 6.55, 1.75, CLR[1] + 4.55, 'coolerwater'); // a water cooler. in the woods. for whom
  log(B, CLR[0] - 12, CLR[1] + 8, CLR[0] - 6, CLR[1] + 8); boulder(B, CLR[0] + 11, CLR[1] - 8, 1.0, r);

  // ---- the cabin (site A): log walls, a porch, a door front and back, a stepped roof, a stone chimney
  { const L = B.local(CAB[0], CAB[1], 0);
    const hw = 6.5, hd = 4.5, t = 0.35, Hh = 3.1, F = 0.35;
    L(-hw - 0.4, 0, -hd - 0.4, hw + 0.4, F, hd + 0.4, 'stonebase'); L(-hw + t, F, -hd + t, hw - t, F + 0.05, hd - t, 'planks');
    // doors 2 m wide on the 1 m grid, so bots' walk graph gets through them
    const front = [{ a: 0, b: 2.0, y0: F, y1: F + 2.3 }, { a: -4.6, b: -3.0, y0: F + 1.0, y1: F + 2.1 }, { a: 2.8, b: 4.4, y0: F + 1.0, y1: F + 2.1 }];
    wall(L, 'x', hd, -hw, hw, F, F + Hh, t, 'logwall', front); // the front, facing the porch (+z, south)
    wall(L, 'x', -hd, -hw, hw, F, F + Hh, t, 'logwall', [{ a: 3.0, b: 5.0, y0: F, y1: F + 2.3 }, { a: -3.6, b: -2.2, y0: F + 1.0, y1: F + 2.1 }]); // the back door
    wall(L, 'z', -hw, -hd + t / 2, hd - t / 2, F, F + Hh, t, 'logwall', [{ a: -0.8, b: 0.8, y0: F + 1.0, y1: F + 2.1 }]);
    wall(L, 'z', hw, -hd + t / 2, hd - t / 2, F, F + Hh, t, 'logwall', [{ a: 1.4, b: 2.6, y0: F + 1.0, y1: F + 2.1 }]);
    L(-1.2, F, -hd + t / 2, -0.9, F + 2.6, 0.5, 'planks'); // a thin wall splits off the bedroom (west), with a 2 m doorway (bots fit)
    L(-1.2, F, 2.5, -0.9, F + 2.6, hd - t / 2, 'planks'); L(-1.2, F + 2.3, 0.5, -0.9, F + 2.6, 2.5, 'planks');
    // the roof: stepped slabs to a ridge along x, a little overhang, then a ridge beam
    const top = F + Hh;
    for (let i = 0; i < 5; i++) L(-hw - 0.5, top + i * 0.42, -hd - 0.7 + i * 1.05, hw + 0.5, top + i * 0.42 + 0.42, hd + 0.7 - i * 1.05, i % 2 ? 'cabinroof2' : 'cabinroof');
    L(-hw - 0.6, top + 2.1, -0.35, hw + 0.6, top + 2.3, 0.35, 'logside');
    L(hw - 0.4, 0, -1.4, hw + 0.9, top + 3.2, 0.2, 'stonebase'); // the chimney up the east wall
    // the porch: boards, posts, a roof, steps down, a rocking chair, junk
    L(-hw, 0, hd + 0.4, hw, F - 0.03, hd + 3.0, 'planks');
    for (const x of [-hw + 0.2, -2, 2, hw - 0.2]) L(x - 0.11, 0, hd + 2.69, x + 0.11, F + 2.7, hd + 2.91, 'logside');
    L(-hw - 0.3, F + 2.7, hd + 0.2, hw + 0.3, F + 2.9, hd + 3.2, 'cabinroof2');
    L(-1.4, 0, hd + 3.0, 1.4, 0.17, hd + 3.6, 'planks');
    L(3.2, F, hd + 0.8, 4.0, F + 0.5, hd + 1.6, 'logside'); L(3.2, F + 0.5, hd + 0.8, 4.0, F + 1.4, hd + 0.92, 'logside');
    L(-5.8, F, hd + 0.7, -4.6, F + 1.1, hd + 1.9, 'crate'); L(-5.6, F + 1.1, hd + 0.9, -4.9, F + 1.7, hd + 1.6, 'crate');
    // inside: table, chairs, a bed, the stove, a corkboard of HR memos, an old TV still on
    L(1.6, F, -0.8, 3.6, F + 0.85, 0.6, 'planks'); L(1.7, F, -1.5, 2.3, F + 0.5, -0.9, 'planks'); L(2.9, F, 0.7, 3.5, F + 0.5, 1.3, 'planks');
    L(-6.0, F, -3.9, -3.6, F + 0.6, -1.9, 'bedsheet'); L(-6.1, F, -4.1, -5.8, F + 1.1, -1.7, 'planks');
    L(hw - t - 1.0, F, -1.2, hw - t, F + 1.3, 0.0, 'stonebase'); L(hw - t - 0.9, F + 0.2, -1.05, hw - t - 0.1, F + 0.9, -0.15, 'ash');
    L(0.4, F + 1.1, -hd + t / 2, 2.6, F + 2.3, -hd + t / 2 + 0.06, 'hrboard', { fit: 1 });
    L(-0.6, F, -3.9, 0.4, F + 0.7, -3.3, 'planks'); L(-0.5, F + 0.7, -3.85, 0.3, F + 1.3, -3.35, 'tvstatic');
    // the woodshed and the axe stump round the side
    const S2 = B.local(CAB[0] - 10.5, CAB[1] + 7, 0);
    S2(-1.6, 0, -1.2, 1.6, 2.5, -1.0, 'planks'); S2(-1.8, 2.5, -1.4, 1.8, 2.7, 1.4, 'cabinroof2');
    S2.B(-1.5, 1.25, 1.2, 0.18, 2.5, 0.18, 'logside'); S2.B(1.5, 1.25, 1.2, 0.18, 2.5, 0.18, 'logside');
    for (let i = 0; i < 4; i++) S2(-1.4, i * 0.4, -0.9, 1.4, i * 0.4 + 0.4, -0.1 - i * 0.12, 'logend');
    W(CAB[0] - 7, 0, CAB[1] + 12, CAB[0] - 6.3, 0.6, CAB[1] + 12.7, 'logend');
  }

  // ---- the campsite: a dead campfire in a ring of stones, log benches, two tents, a picnic table, the outhouse
  { const [cx, cz] = CAMP;
    for (let i = 0; i < 9; i++) { const a = (i / 9) * Math.PI * 2; B.box(cx + Math.cos(a) * 1.2, 0.18, cz + Math.sin(a) * 1.2, 0.45, 0.36, 0.45, 'rockf'); }
    B.add(cx - 0.8, 0, cz - 0.8, cx + 0.8, 0.1, cz + 0.8, 'ash');
    D.obb(cx, 0.22, cz, 1.4, 0.2, 0.22, 0.5, 'charcoal'); D.obb(cx, 0.32, cz, 1.2, 0.2, 0.2, 2.1, 'charcoal'); D.obb(cx + 0.1, 0.42, cz, 0.9, 0.16, 0.16, 1.2, 'charcoal');
    log(B, cx - 2.2, cz - 4, cx + 2.2, cz - 4, 0.3); log(B, cx - 2.2, cz + 3.8, cx + 2.2, cz + 3.8, 0.3); log(B, cx + 4, cz - 1.8, cx + 4, cz + 2.2, 0.3);
    const tent = (x, z, alongX, mat) => { // an A-frame tent, stepped (it's a jank tent)
      for (let i = 0; i < 4; i++) { const w = 1.4 - i * 0.33, y = i * 0.42; if (alongX) B.add(x - 1.6, y, z - w, x + 1.6, y + 0.42, z + w, mat); else B.add(x - w, y, z - 1.6, x + w, y + 0.42, z + 1.6, mat); }
      if (alongX) B.add(x + 1.6, 0, z - 0.4, x + 1.64, 1.1, z + 0.4, 'tentdark'); else B.add(x - 0.4, 0, z + 1.6, x + 0.4, 1.1, z + 1.64, 'tentdark');
    };
    tent(cx - 7, cz - 5, true, 'tentorange'); tent(cx + 6.5, cz - 6, false, 'tentgreen');
    B.add(cx + 3, 0, cz + 6, cx + 6, 0.75, cz + 7, 'planks'); B.add(cx + 3, 0, cz + 5.1, cx + 6, 0.42, cz + 5.5, 'planks'); B.add(cx + 3, 0, cz + 7.5, cx + 6, 0.42, cz + 7.9, 'planks');
    B.add(cx - 4.4, 0, cz + 5.5, cx - 3.4, 0.6, cz + 6.2, 'cooler'); B.add(cx - 4.45, 0.6, cz + 5.45, cx - 3.35, 0.68, cz + 6.25, 'white');
    B.box(cx - 3, 1.1, cz + 3.4, 0.12, 2.2, 0.12, 'metal'); B.box(cx - 3, 2.0, cz + 3.4, 0.3, 0.4, 0.3, 'lantern'); // a lantern on a pole, almost dead
    const O = B.local(cx - 12, cz + 9, 0); // the outhouse: one door, one moon cut in it, a seat
    O(-0.9, 0, -0.9, 0.9, 0.15, 0.9, 'planks'); O(-0.9, 0.15, -0.9, 0.9, 2.4, -0.75, 'planks'); O(-0.9, 0.15, -0.75, -0.75, 2.4, 0.9, 'planks'); O(0.75, 0.15, -0.75, 0.9, 2.4, 0.9, 'planks');
    O(-0.9, 0.15, 0.75, -0.35, 2.4, 0.9, 'planks'); O(0.35, 0.15, 0.75, 0.9, 2.4, 0.9, 'planks'); O(-0.35, 2.1, 0.75, 0.35, 2.4, 0.9, 'planks');
    O(-1.0, 2.4, -1.0, 1.0, 2.55, 1.0, 'cabinroof2'); O(-0.6, 0.15, -0.75, 0.6, 0.6, -0.15, 'planks');
  }

  // ---- the fire lookout tower: four legs, five flights of switchback stairs inside them, a glassless cab up top
  { const L = B.local(TWR[0], TWR[1], 0), R = 2.64, top = 5 * R;
    for (const sx of [-3.1, 3.1]) for (const sz of [-3.1, 3.1]) L.B(sx, top / 2, sz, 0.34, top, 0.34, 'towerwood');
    for (let k = 1; k <= 4; k++) for (const s of [-3.1, 3.1]) { L(-2.93, k * R - 0.3, s - 0.08, 2.93, k * R - 0.16, s + 0.08, 'towerwood'); L(s - 0.08, k * R - 0.6, -2.93, s + 0.08, k * R - 0.46, 2.93, 'towerwood'); } // girts, above head height
    const A = [-2.9, -1.5], Bl = [-1.45, -0.05];
    for (let k = 0; k < 5; k++) {
      const ya = k * R, yb = (k + 1) * R;
      if (k % 2 === 0) stairs(L, A[0], A[1], -1.5, 1, ya, yb, 'towerwood', 0.5); else stairs(L, Bl[0], Bl[1], 1.5, -1, ya, yb, 'towerwood', 0.5);
      if (k < 4) { if (k % 2 === 0) L(A[0], yb - 0.22, 1.5, Bl[1], yb, 2.9, 'towerwood'); else L(A[0], yb - 0.22, -2.9, Bl[1], yb, -1.5, 'towerwood'); }
    }
    slab(L, -3.4, -3.4, 3.4, 3.4, top - 0.2, top, 'towerwood', [A[0] - 0.05, -1.55, A[1] + 0.05, 1.5]);
    const cy = top, wins = (len) => [{ a: -len / 2 + 0.3, b: len / 2 - 0.3, y0: cy + 0.95, y1: cy + 2.15 }];
    wall(L, 'x', -3.3, -3.4, 3.4, cy, cy + 2.5, 0.16, 'towerwood', wins(6.8)); wall(L, 'x', 3.3, -3.4, 3.4, cy, cy + 2.5, 0.16, 'towerwood', wins(6.8));
    wall(L, 'z', -3.3, -3.22, 3.22, cy, cy + 2.5, 0.16, 'towerwood', wins(6.44)); wall(L, 'z', 3.3, -3.22, 3.22, cy, cy + 2.5, 0.16, 'towerwood', wins(6.44));
    L(-3.7, cy + 2.5, -3.7, 3.7, cy + 2.7, 3.7, 'cabinroof'); L(-2.6, cy + 2.7, -2.6, 2.6, cy + 3.1, 2.6, 'cabinroof2'); L(-1.3, cy + 3.1, -1.3, 1.3, cy + 3.5, 1.3, 'cabinroof');
    L(1.0, cy, -0.6, 2.4, cy + 0.9, 0.6, 'planks'); L(1.2, cy + 0.9, -0.4, 2.2, cy + 0.95, 0.4, 'mapsheet'); // the fire finder table, with a map on it
    B.box(TWR[0] + 0.0, cy + 3.9, TWR[1], 0.1, 0.8, 0.1, 'metal');
    adSign(B, TWR[0] - 4.6, TWR[1] + 4.2, 'signtower');
  }

  // ---- the radio mast yard (site B): a low chain-link fence, the mast blinking red, a shed full of radio, a generator
  { const [mx, mz] = MAST, x0 = 42, x1 = 62, z0 = -5, z1 = 13, FH = 1.25;
    const fence = (axis, fixed, a0, a1, gaps) => {
      const cuts = [a0, ...gaps.flat(), a1];
      for (let i = 0; i < cuts.length; i += 2) {
        const s0 = cuts[i], s1 = cuts[i + 1];
        if (axis === 'x') B.add(s0, 0, fixed - 0.04, s1, FH, fixed + 0.04, 'chainlink'); else B.add(fixed - 0.04, 0, s0, fixed + 0.04, FH, s1, 'chainlink');
        for (let s = s0; s <= s1 + 0.01; s += Math.max(1.5, (s1 - s0) / Math.max(1, Math.round((s1 - s0) / 2.5)))) axis === 'x' ? B.box(s, FH / 2 + 0.1, fixed, 0.12, FH + 0.2, 0.12, 'metal') : B.box(fixed, FH / 2 + 0.1, s, 0.12, FH + 0.2, 0.12, 'metal');
      }
    };
    fence('x', z0, x0, x1, [[48, 52]]); fence('x', z1, x0, x1, [[50, 54]]); fence('z', x0, z0 + 0.1, z1 - 0.1, [[2, 6]]); fence('z', x1, z0 + 0.1, z1 - 0.1, [[-1, 2]]);
    B.add(x0 + 0.3, 0, z0 + 0.3, x1 - 0.3, 0.04, z1 - 0.3, 'gravel');
    // the mast: a 2 m lattice, 48 m tall, red and white bands, red lights that blink
    const H = 48, ax = mx + 4, az = mz + 4;
    for (const sx of [-1, 1]) for (const sz of [-1, 1]) for (let y = 0; y < H; y += 6) B.add(ax + sx * 1 - 0.1, y, az + sz * 1 - 0.1, ax + sx * 1 + 0.1, Math.min(H, y + 6), az + sz * 1 + 0.1, (y / 6) % 2 ? 'mastwhite' : 'mastred');
    for (let y = 1.5; y < H; y += 2) { B.add(ax - 1, y, az - 1.08, ax + 1, y + 0.08, az - 0.92, 'metal'); B.add(ax - 1, y, az + 0.92, ax + 1, y + 0.08, az + 1.08, 'metal'); B.add(ax - 1.08, y + 1, az - 0.92, ax - 0.92, y + 1.08, az + 0.92, 'metal'); B.add(ax + 0.92, y + 1, az - 0.92, ax + 1.08, y + 1.08, az + 0.92, 'metal'); }
    B.add(ax - 1.4, H, az - 1.4, ax + 1.4, H + 0.2, az + 1.4, 'metal'); B.box(ax, H + 1.4, az, 0.2, 2.4, 0.2, 'metal');
    B.box(ax, H + 2.8, az, 0.5, 0.5, 0.5, 'mastlight'); for (const y of [16, 32]) for (const s of [-1, 1]) B.box(ax + s * 1.2, y, az, 0.3, 0.3, 0.3, 'mastlight');
    B.add(ax - 1.6, 0, az - 1.6, ax + 1.6, 0.35, az + 1.6, 'concrete');
    // the shed: radio gear on a desk, a door west, a window south
    const Sd = B.local(mx - 5, mz - 1, 0);
    Sd(-2.5, 0, -2, 2.5, 0.2, 2, 'concrete');
    wall(Sd, 'x', -2, -2.5, 2.5, 0.2, 2.9, 0.2, 'shedmetal', []); wall(Sd, 'x', 2, -2.5, 2.5, 0.2, 2.9, 0.2, 'shedmetal', [{ a: -1.6, b: 0, y0: 1.1, y1: 2.0 }]);
    wall(Sd, 'z', -2.5, -1.9, 1.9, 0.2, 2.9, 0.2, 'shedmetal', [{ a: -1.0, b: 1.0, y0: 0.2, y1: 2.4 }]); wall(Sd, 'z', 2.5, -1.9, 1.9, 0.2, 2.9, 0.2, 'shedmetal', []);
    Sd(-2.7, 2.9, -2.2, 2.7, 3.1, 2.2, 'roofg');
    Sd(0.6, 0.2, -1.85, 2.35, 1.0, -0.9, 'metal'); Sd(0.8, 1.0, -1.85, 2.2, 1.8, -1.7, 'radiopanel', { fit: 1 }); Sd(-1.0, 0.2, 1.0, -0.2, 0.7, 1.7, 'officechair');
    B.add(mx + 7, 0, mz - 8, mx + 9.4, 1.3, mz - 6.6, 'generator'); B.add(mx + 7.2, 1.3, mz - 7.9, mx + 7.5, 2.1, mz - 7.6, 'metal');
    for (const [x, z] of [[mx - 6, mz + 6], [mx + 3, mz - 5]]) { B.add(x - 0.8, 0, z - 0.6, x + 0.8, 1.4, z - 0.45, 'logend'); B.add(x - 0.8, 0, z + 0.45, x + 0.8, 1.4, z + 0.6, 'logend'); B.add(x - 0.5, 0.3, z - 0.45, x + 0.5, 1.1, z + 0.45, 'cable'); } // cable drums
    adSign(B, x0 - 0.6, 8.5, 'signmast', 'z');
  }

  // ---- the lake edge: a dock, a rowboat tied to it, a canoe on the shore, reeds
  { const z0 = -33.4, z1 = -30.6;
    B.add(SH - 4, 0.15, z0, SH + 18, 0.35, z1, 'planks');
    for (let x = SH - 3; x <= SH + 18; x += 3) for (const z of [z0 + 0.15, z1 - 0.15]) B.box(x, -0.3, z, 0.25, 1.4, 0.25, 'logside');
    B.add(SH + 17, 0.35, z0, SH + 18, 0.85, z1, 'crate');
    const bt = (x, z, l, w, mat) => { B.add(x - l / 2, -0.32, z - w / 2, x + l / 2, 0.3, z - w / 2 + 0.12, mat); B.add(x - l / 2, -0.32, z + w / 2 - 0.12, x + l / 2, 0.3, z + w / 2, mat); B.add(x - l / 2, -0.32, z - w / 2, x - l / 2 + 0.12, 0.3, z + w / 2, mat); B.add(x + l / 2 - 0.12, -0.32, z - w / 2, x + l / 2, 0.3, z + w / 2, mat); B.add(x - l / 2, -0.36, z - w / 2, x + l / 2, -0.32, z + w / 2, mat); };
    bt(SH + 11, z1 + 1.1, 3.6, 1.4, 'boatwood');
    B.add(SH - 6, 0, 20, SH - 1.5, 0.45, 20.8, 'canoe');
    for (let i = 0; i < 90; i++) { const z = bz0 - 30 + r() * (bz1 - bz0 + 60), x = SH - 1 + r() * 7; if (z > RZ0 - 3 && z < RZ1 + 3) continue; if (z > z0 - 2 && z < z1 + 2) continue; D.obb(x, 0.4, z, 0.1, 1.4 + r() * 0.8, 0.1, r() * 3, 'reed'); }
  }

  // ---- the road: the broken-down car, a fallen tree across the lanes, power poles, a trailhead lot with a sign
  brokenCar(B, D, -8, 56.2);
  B.add(33, 0, RZ0 - 3, 34.2, 1.1, RZ1 + 1, 'logside'); B.add(32.6, 0, RZ1 + 1, 34.8, 2.6, RZ1 + 2.2, 'rootball'); // it came down in a storm. or something pushed it
  for (let x = -250; x < SH; x += 26) { (Math.abs(x) < 110 ? B : D).box(x, 4.5, RZ0 - 1.8, 0.32, 9, 0.32, 'deadbark'); (Math.abs(x) < 110 ? B : D).add(x - 1.2, 8.3, RZ0 - 1.95, x + 1.2, 8.45, RZ0 - 1.65, 'deadbark'); }
  for (const s of [-1, 1]) D.add(-250, 8.2, RZ0 - 1.8 + s * 0.9 - 0.02, SH - 20, 8.24, RZ0 - 1.8 + s * 0.9 + 0.02, 'tire'); // the wires
  B.add(TH[0] - 14, 0, TH[1] - 7, TH[0] + 14, 0.05, TH[1] + 7, 'gravel'); // the trailhead lot
  adSign(B, TH[0] + 6, TH[1] - 7.5, 'signtrail');
  B.add(TH[0] - 12, 0.05, TH[1] + 2, TH[0] - 10, 2.5, TH[1] + 4, 'toyblue'); B.add(TH[0] - 12.1, 2.5, TH[1] + 1.9, TH[0] - 9.9, 2.65, TH[1] + 4.1, 'white'); // a portable toilet. locked
  B.add(TH[0] + 2, 0.05, TH[1] + 3, TH[0] + 4.4, 1.6, TH[1] + 4.2, 'containerg'); // a bear-proof bin
  // the ranger lot (defenders): a gravel pull-off on a fire road, a ranger pickup, a notice board
  B.add(DEF[0] - 14, 0, DEF[1] - 8, DEF[0] + 14, 0.05, DEF[1] + 8, 'gravel'); D.add(DEF[0] - 3, 0.005, -260, DEF[0] + 3, 0.035, DEF[1] - 8, 'dirtroad');
  { const x = DEF[0] + 7, z = DEF[1] - 2; B.add(x - 1, 0.4, z - 2.6, x + 1, 1.1, z + 2.6, 'rangergreen'); B.add(x - 0.95, 1.1, z - 2.4, x + 0.95, 1.9, z - 0.6, 'glassdark'); B.add(x - 1, 1.9, z - 2.45, x + 1, 2.0, z - 0.55, 'rangergreen'); B.add(x - 1, 1.1, z - 0.5, x + 1, 1.5, z + 2.6, 'rangergreen'); for (const sx of [-1, 1]) for (const sz of [-1.6, 1.6]) B.add(x + sx - 0.15, 0, z + sz - 0.38, x + sx + 0.15, 0.75, z + sz + 0.38, 'tire'); B.add(x - 0.6, 2.0, z - 1.8, x + 0.6, 2.12, z - 1.4, 'hazard2'); }
  adSign(B, DEF[0] - 6, DEF[1] + 7.6, 'signranger');
  // the hunting stand in the west woods: a platform on legs, a ladder of steps
  { const x = -74, z = -52; for (const sx of [-1, 1]) for (const sz of [-1, 1]) B.box(x + sx * 1.1, 2, z + sz * 1.1, 0.2, 4, 0.2, 'towerwood'); B.add(x - 1.4, 3.8, z - 1.4, x + 1.4, 4.0, z + 1.4, 'planks'); B.add(x - 1.4, 4.0, z - 1.4, x + 1.4, 4.9, z - 1.25, 'planks'); B.add(x - 1.4, 4.0, z - 1.25, x - 1.25, 4.9, z + 1.4, 'planks'); B.add(x + 1.25, 4.0, z - 1.25, x + 1.4, 4.9, z + 1.4, 'planks'); stairs(W, x - 0.6, x + 0.6, z + 6.3, -1, 0, 4.0, 'towerwood', 0.55); }
  // ---- the property line: orange-topped stakes and the odd sign, so you know where the woods stop being yours
  const stake = (x, z) => { B.box(x, 0.6, z, 0.14, 1.2, 0.14, 'logside'); B.box(x, 1.3, z, 0.16, 0.2, 0.16, 'toyorange'); };
  for (let x = bx0; x < SH - 2; x += 11) { stake(x, bz0 + 1); stake(x, bz1 - 1); }
  for (let z = bz0 + 11; z < bz1; z += 11) if (z < RZ0 - 3 || z > RZ1 + 3) stake(bx0 + 1, z);
  adSign(B, bx0 + 1.5, 20, 'signturn', 'z'); adSign(B, -30, bz0 + 1.6, 'signturn'); adSign(B, 40, bz1 - 1.6, 'signturn');

  // ---- spawns, teams, sites, bots
  const att = [[TH[0] - 4, 0.2, TH[1] - 2], [TH[0], 0.2, TH[1] - 2], [TH[0] + 4, 0.2, TH[1] - 2], [TH[0] - 4, 0.2, TH[1] + 2], [TH[0], 0.2, TH[1] + 2], [TH[0] + 4, 0.2, TH[1] + 2], [TH[0] + 8, 0.2, TH[1]]];
  const def = [[DEF[0] - 6, 0.2, DEF[1] - 2], [DEF[0] - 2, 0.2, DEF[1] - 2], [DEF[0] + 2, 0.2, DEF[1] + 2], [DEF[0] - 6, 0.2, DEF[1] + 2], [DEF[0] - 2, 0.2, DEF[1] + 2], [DEF[0] - 10, 0.2, DEF[1]], [DEF[0] + 1, 0.2, DEF[1] - 5]];
  const sites = [{ id: 'A', min: [CAB[0] - 6.2, 0, CAB[1] - 4.2], max: [CAB[0] + 6.2, 0, CAB[1] + 7.4] }, { id: 'B', min: [42.4, 0, -4.6], max: [61.6, 0, 12.6] }];
  let graph = null, nav = null;
  const N = 210, gx0 = -105, gz0 = -105;
  const navGraph = () => graph || (graph = buildNav(B.boxes, { x0: gx0, z0: gz0, n: N, cell: 1, levels: [0], band: 0.5, keep: (x, z) => x > bx0 && x < bx1 && z > bz0 && z < bz1 }));
  const route = (...via) => { // A* through the via points, then keep only the corners (as in the Backrooms). points are [x, 0, z]
    const g = navGraph(), ks = [];
    for (let v = 0; v + 1 < via.length; v++) for (const k of navPath(g, navLocate(g, via[v]), navLocate(g, via[v + 1])) || []) if (ks[ks.length - 1] !== k) ks.push(k);
    if (!ks.length) return via.map((p) => [p[0], p[2]]);
    const out = [ks[0]];
    for (let k = 1; k < ks.length; k++) { const a = g.nodes[out[out.length - 1]], b = g.nodes[ks[k + 1]]; if (b && navClear(g, 0, a[0], a[2], b[0], b[2])) continue; out.push(ks[k]); }
    return out.map((k) => [g.nodes[k][0], g.nodes[k][2]]);
  };
  const P = (p) => [p[0], 0, p[1]];
  const sA = [CAB[0] + 1.5, 0, CAB[1] + 1], sB = [MAST[0] + 1, 0, MAST[1] + 2];
  const lanes = () => nav || (nav = {
    A: [route(P(TH), [-84, 0, 30], [-78, 0, -2], [-62, 0, -20], sA), route(P(TH), P(CAMP), [-12, 0, 10], P(CLR), [-28, 0, -12], [CAB[0], 0, -16], sA), route(P(DEF), [-6, 0, -68], [-42, 0, -54], [CAB[0] + 3, 0, CAB[1] - 6], sA)],
    B: [route(P(TH), P(CAMP), [-30, 0, 48], [20, 0, 50], [50, 0, 34], [52, 0, 15], sB), route(P(TH), P(CAMP), [-12, 0, 10], P(CLR), [26, 0, -2], [40, 0, 4], sB), route(P(DEF), [48, 0, -64], [62, 0, -44], [64, 0, -22], [62, 0, 0], sB)],
  });
  const map = {
    name: 'Scary Forest', size: 'large', boxes: B.boxes, deco: D.boxes, killY: -40, floorY: -4, bounds: FOREST.bounds,
    sky: { top: 0x04060e, mid: 0x22304a, bot: 0x0c1018, fog: 0x1c2840 }, fogNear: 4, fogFar: 86,
    light: { hemi: [0x7890c4, 0x161a24, 0.85], sun: [0xa4baff, 0.6] }, moon: true, night: true, flashlights: true,
    chunk: 40, spawns, spawnSafe: 50, teamSpawns: { att, def }, teamSpawnsBomb: true, roundTime: 130, sites,
    menuCam: [30, 9, -0.22],
    // the Tall Guy From HR (server/hrguy.js): where he can't stand, and the awful places he transfers people to
    hr: { keepOut: [[41, -7, 64, 16], [CAB[0] - 7, CAB[1] - 5, CAB[0] + 7, CAB[1] + 8]], awful: [
      { p: [CAMP[0] - 12, 0.3, CAMP[1] + 9], name: 'THE OUTHOUSE' }, { p: [MAST[0] + 4.9, 48.3, MAST[1] + 4.9], name: 'THE TOP OF THE RADIO MAST' },
      { p: [SH + 20, -0.6, 10], name: 'THE LAKE' }, { p: [CLR[0] - 2.1, 0.75, CLR[1] + 2], name: 'A MEETING (THE CHAIR)' }] },
    get nav() { return lanes(); }, get graph() { return navGraph(); },
  };
  return map;
}
function adSign(B, x, z, mat, along = 'x') { // a wooden sign on two posts, the words drawn once across it
  const L = B.local(x, z, along === 'x' ? 0 : 1);
  L.B(-1.1, 0.9, 0, 0.16, 1.8, 0.16, 'logside'); L.B(1.1, 0.9, 0, 0.16, 1.8, 0.16, 'logside');
  L.B(0, 1.75, 0, 2.8, 1.1, 0.12, 'planks'); L.B(0, 1.75, 0, 2.6, 0.95, 0.16, mat, { fit: 1 });
}

// ------------------------------------------------------------ DEAD MALL: the zombies map. a closed-down mall on one floor.
// six areas in a ring round the atrium (so you can run loops and drag a crowd behind you), the start in the entrance
// hall, everything else behind roller shutters you buy open. low ceilings everywhere and nothing tall to stand on, so
// there's no perch the zombies can't swipe you off. every area has boarded windows onto little back alleys: that's
// where zombies climb in (only open areas spawn them). the extras (`zm`) are read by the zombies mode on both sides.
function deadmall() {
  const B = builder();
  const W = B.local(0, 0, 0);
  const H = 4; // ceiling height
  const X0 = -37, X1 = 37, Z0 = -30, Z1 = 28;
  const areas = [
    { id: 'hall', name: 'Entrance Hall', r: [-11, 12, 11, 28], floor: 'tile', ceil: 'plaster' },
    { id: 'food', name: 'Food Court', r: [-37, 4, -11, 28], floor: 'tile', ceil: 'plaster' },
    { id: 'toys', name: 'Toy Store', r: [11, 4, 37, 28], floor: 'wood', ceil: 'plaster' },
    { id: 'atrium', name: 'Atrium', r: [-11, -30, 11, 12], floor: 'stone', ceil: 'plaster' },
    { id: 'arcade', name: 'Arcade', r: [-37, -30, -11, 4], floor: 'carpet', ceil: 'roofg' },
    { id: 'dock', name: 'Loading Dock', r: [11, -30, 37, 4], floor: 'concrete', ceil: 'grid' },
  ];
  for (const a of areas) { const [x0, z0, x1, z1] = a.r; B.add(x0, -0.4, z0, x1, 0, z1, a.floor); B.add(x0, H, z0, x1, H + 0.4, z1, a.ceil); }

  // ---- windows: an opening in the outside wall (sill 0.9 m) onto a boarded-up back alley the zombies come from
  const holes = { w: [], e: [], n: [], s: [] }, windows = [];
  const win = (side, c, area) => {
    holes[side].push({ a: c - 1, b: c + 1, y0: 0.9, y1: 2.9 });
    const [ox, oz] = { w: [-1, 0], e: [1, 0], n: [0, -1], s: [0, 1] }[side];
    const face = side === 'w' ? X0 - 0.6 : side === 'e' ? X1 + 0.6 : side === 'n' ? Z0 - 0.6 : Z1 + 0.6; // outer face of the wall
    const P = (d, l) => (ox ? [face + ox * d, l] : [l, face + oz * d]); // d metres out, l along the wall
    const box = (d0, d1, l0, l1, y0, y1, mat) => { const [ax, az] = P(d0, l0), [bx, bz] = P(d1, l1); B.add(ax, y0, az, bx, y1, bz, mat); };
    box(0, 3, c - 1.8, c + 1.8, -0.4, 0, 'road'); // alley floor
    box(0, 3.3, c - 2.1, c + 2.1, 3.2, 3.5, 'roofg'); // a lid on it (nobody leaves this way)
    box(3, 3.3, c - 2.1, c + 2.1, -0.4, 3.2, 'brick');
    box(0, 3, c - 2.1, c - 1.8, -0.4, 3.2, 'brick'); box(0, 3, c + 1.8, c + 2.1, -0.4, 3.2, 'brick');
    box(2.2, 2.9, c + 0.6, c + 1.6, 0, 0.5, 'tire'); // bin bags
    const out = P(1.5, c), inn = P(-1.6, c), at = P(-0.3, c);
    windows.push({ area, out: [out[0], 0, out[1]], in: [inn[0], 0, inn[1]], at: [at[0], 1.9, at[1]], yaw: Math.atan2(ox, oz), n: [-ox, 0, -oz] });
  };
  win('s', -6, 'hall'); win('s', 6, 'hall');
  win('w', 10, 'food'); win('w', 22, 'food'); win('s', -24, 'food');
  win('e', 10, 'toys'); win('e', 22, 'toys'); win('s', 24, 'toys');
  win('n', -6, 'atrium'); win('n', 6, 'atrium');
  win('w', -22, 'arcade'); win('w', -6, 'arcade'); win('n', -24, 'arcade');
  win('e', -22, 'dock'); win('e', -6, 'dock'); win('n', 24, 'dock');
  // outside walls: plaster inside, brick outside, both with the window holes
  for (const [mat, t0] of [['plaster', 0], ['brick', 0.3]]) {
    wall(W, 'z', X0 - 0.15 - t0, Z0 - 0.6, Z1 + 0.6, -0.4, H + 0.4, 0.3, mat, holes.w);
    wall(W, 'z', X1 + 0.15 + t0, Z0 - 0.6, Z1 + 0.6, -0.4, H + 0.4, 0.3, mat, holes.e);
    wall(W, 'x', Z0 - 0.15 - t0, X0, X1, -0.4, H + 0.4, 0.3, mat, holes.n);
    wall(W, 'x', Z1 + 0.15 + t0, X0, X1, -0.4, H + 0.4, 0.3, mat, holes.s);
  }

  // ---- doors: roller shutters in the inside walls. they're not map boxes: the mode adds the closed ones to the room
  const doors = [];
  const gap = (c) => ({ a: c - 2, b: c + 2, y0: 0, y1: 3 });
  const door = (axis, fixed, c, a, b, price) => {
    const box = axis === 'z' ? { min: [fixed - 0.15, 0, c - 2], max: [fixed + 0.15, 3, c + 2], mat: 'metal' } : { min: [c - 2, 0, fixed - 0.15], max: [c + 2, 3, fixed + 0.15], mat: 'metal' };
    doors.push({ a, b, price, name: areas.find((x) => x.id === b).name, box, at: axis === 'z' ? [fixed, 1.5, c] : [c, 1.5, fixed] });
    return gap(c);
  };
  const dHF = door('z', -11, 20, 'hall', 'food', 750), dHT = door('z', 11, 20, 'hall', 'toys', 750);
  const dHA = door('x', 12, 0, 'hall', 'atrium', 1000);
  const dFA = door('x', 4, -24, 'food', 'arcade', 1000), dTD = door('x', 4, 24, 'toys', 'dock', 1000);
  const dAA = door('z', -11, -12, 'atrium', 'arcade', 1250), dAD = door('z', 11, -12, 'atrium', 'dock', 1250);
  wall(W, 'z', -11, Z0, Z1, 0, H, 0.4, 'plaster', [dHF, dAA]);
  wall(W, 'z', 11, Z0, Z1, 0, H, 0.4, 'plaster', [dHT, dAD]);
  wall(W, 'x', 12, -10.8, 10.8, 0, H, 0.4, 'plaster', [dHA]);
  wall(W, 'x', 4, X0, -11.2, 0, H, 0.4, 'plaster', [dFA]);
  wall(W, 'x', 4, 11.2, X1, 0, H, 0.4, 'plaster', [dTD]);
  for (const { box: { min, max } } of doors) { // the shutter's housing, striped, sticking out of the wall over the doorway
    const ex = max[0] - min[0] < 1 ? 0.11 : 0.1, ez = max[2] - min[2] < 1 ? 0.11 : 0.1;
    B.add(min[0] - ex, 2.95, min[2] - ez, max[0] + ex, 3.3, max[2] + ez, 'hazard');
  }

  // ---- ENTRANCE HALL (start): an info kiosk to run round, two pillars, benches under the boarded entrance
  B.add(-2.6, 0, 18.6, 2.6, 1.1, 21.4, 'wood'); B.add(-2.8, 1.1, 18.4, 2.8, 1.2, 21.6, 'tile');
  B.add(-0.5, 1.2, 19.5, 0.5, H, 20.5, 'plaster'); // the sign post holds the ceiling up (and stops kiosk camping)
  for (const x of [-6, 6]) B.add(x - 0.4, 0, 15.1, x + 0.4, H, 15.9, 'plaster');
  B.add(-1.6, 0, 26.3, 1.6, 0.45, 26.9, 'wood');
  for (const x of [-9.6, 9.6]) B.add(x - 0.8, 0, 26.4, x + 0.8, 0.7, 27.6, 'hedge');
  // ---- FOOD COURT: tables in a 3x3 grid (lanes between them), a burger counter in the corner
  for (const x of [-31, -24, -17]) for (const z of [10, 16, 22]) B.box(x, 0.375, z, 1.6, 0.75, 1.6, 'wood');
  B.add(-36.6, 0, 25.6, -29.5, 1.05, 27.2, 'tile'); B.add(-36.6, 1.05, 25.4, -29.3, 1.15, 27.4, 'carred');
  // ---- TOY STORE: three full-height shelves = three loops
  for (const [z, mat] of [[10, 'pink'], [16, 'blue'], [22, 'yellow']]) B.add(17, 0, z - 0.4, 31, H, z + 0.4, mat);
  for (const [x, z, m] of [[14, 25, 'pink'], [14.8, 25.4, 'mint'], [34, 7, 'mint'], [33.4, 6.4, 'yellow'], [34.5, 13, 'blue']]) B.box(x, 0.25, z, 0.5, 0.5, 0.5, m);
  // ---- ATRIUM: the elevator core in the middle (the big loop), planters, the mystery crate on the north stage
  B.add(-3.5, 0, -10, 3.5, H, -2, 'glassblock');
  for (const x of [-7, 7]) for (const z of [-19, 5]) B.box(x, 0.35, z, 2, 0.7, 2, 'hedge');
  for (const z of [-15, 1]) B.add(-1.5, 0, z - 0.3, 1.5, 0.45, z + 0.3, 'wood');
  const crate = { at: [0, 0, -28.55], price: 950 };
  B.add(-0.9, 0, -29, 0.9, 0.9, -28.1, 'crate');
  const cola = { at: [-10.4, 0, -24], n: [1, 0, 0] };
  B.add(-10.8, 0, -24.6, -10.0, 2.1, -23.4, 'containerr');
  // ---- ARCADE: three rows of back-to-back cabinets (gaps halfway down), screens glowing on both sides
  for (const x of [-31, -24, -17]) for (const [z0, z1] of [[-24, -15], [-13, -4]]) {
    B.add(x - 0.9, 0, z0, x + 0.9, 1.9, z1, x === -24 ? 'containerr' : 'containerb');
    B.add(x - 0.96, 1.15, z0 + 0.3, x - 0.9, 1.65, z1 - 0.3, 'light'); B.add(x + 0.9, 1.15, z0 + 0.3, x + 0.96, 1.65, z1 - 0.3, 'light');
  }
  // ---- LOADING DOCK: crates, pallets, a forklift, the power switch on the east wall
  for (const [x, z, n] of [[16, -24, 2], [17.3, -24, 1], [29, -18, 2], [21, -8, 1], [32, -27, 1], [15.2, -1.5, 1]]) for (let k = 0; k < n; k++) B.box(x, 0.6 + k * 1.2, z, 1.2, 1.2, 1.2, 'crate');
  B.add(23, 0, -15, 26, 0.25, -12, 'wood'); B.add(30, 0, -6, 31.4, 1.4, -4, 'caryellow'); B.add(30.2, 1.4, -5.8, 31.2, 2.2, -4.6, 'glass');
  const power = { at: [36.7, 1.6, -14], n: [-1, 0, 0] };
  B.add(36.6, 1.0, -14.5, 37, 2.2, -13.5, 'metal');

  // ---- wall guns: an outline on the wall + its price. look at it and hold F (ammo is half price)
  const buys = [
    { w: 'revolver', price: 300, at: [-7, 1.55, 12.21], n: [0, 0, 1] },
    { w: 'smg', price: 900, at: [7, 1.55, 12.21], n: [0, 0, 1] },
    { w: 'bread', price: 600, at: [-32, 1.55, 4.21], n: [0, 0, 1] },
    { w: 'banana', price: 750, at: [-36.99, 1.55, 16], n: [1, 0, 0] },
    { w: 'shotgun', price: 1200, at: [16, 1.55, 4.21], n: [0, 0, 1] },
    { w: 'bow', price: 1000, at: [32, 1.55, 4.21], n: [0, 0, 1] },
    { w: 'ar', price: 1200, at: [10.79, 1.55, 0], n: [-1, 0, 0] },
    { w: 'sniper', price: 1500, at: [-36.99, 1.55, -14], n: [1, 0, 0] },
    { w: 'katana', price: 2000, at: [11.21, 1.55, -24], n: [1, 0, 0] },
  ];
  const spawns = [[-4, 0.1, 24], [4, 0.1, 24], [-7, 0.1, 17.5], [7, 0.1, 17.5], [0, 0.1, 25], [-8, 0.1, 22], [8, 0.1, 22], [0, 0.1, 15]];
  return {
    name: 'Dead Mall', size: 'medium', boxes: B.boxes, killY: -20,
    sky: { top: 0x06050c, mid: 0x1a1220, bot: 0x05040a, fog: 0x140e18 }, fogNear: 16, fogFar: 80, spawns,
    zm: { bounds: [X0 - 4, Z0 - 4, X1 + 4, Z1 + 4], H, start: 'hall', areas, doors, windows, buys, crate, power, cola },
  };
}

export const MAPS = {
  crate: crate(), platform: platform(), rooftop: rooftop(), suburb: suburb(), suburb_sd: suburbSD(), warehouse: warehouse(), warehouse_sd: warehouseSD(),
  desert: desert(), islands: islands(), skyline: skyline(), bazaar: bazaar(), range: range(), backrooms: backrooms(), forest: forest(),
  deadmall: deadmall(),
};
// maps with an S&D version: '<id>_sd' is its own layout on the bomb-map rules, the one Plant & Defuse plays; '<id>' is
// the one every other mode plays. switching mode swaps between them (modes.js mapForGame, the server's setGame)
for (const [id, m] of Object.entries(MAPS)) if (id.endsWith('_sd') && MAPS[id.slice(0, -3)]) { m.sd = true; m.base = id.slice(0, -3); MAPS[m.base].sdMap = id; }
// a spawn whose body would start inside a box (a column, a roof garden, a helipad) gets lifted onto whatever it's in
function unstick(boxes, list) {
  for (const p of list) for (let k = 0; k < 3; k++) {
    const b = boxes.find((q) => p[0] + 0.4 > q.min[0] && p[0] - 0.4 < q.max[0] && p[2] + 0.4 > q.min[2] && p[2] - 0.4 < q.max[2] && p[1] + 1.8 > q.min[1] && p[1] < q.max[1]);
    if (!b) break;
    p[1] = b.max[1] + 0.1;
  }
}
for (const m of Object.values(MAPS)) unstick(m.boxes, [...m.spawns, ...(m.teamSpawns ? [...m.teamSpawns.att, ...m.teamSpawns.def] : [])]);
export const MAP_ORDER = ['crate', 'platform', 'rooftop', 'suburb', 'warehouse', 'desert', 'bazaar', 'islands', 'skyline', 'backrooms', 'forest', 'deadmall'].flatMap((id) => (MAPS[id + '_sd'] ? [id, id + '_sd'] : [id]));

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
// the building kit, for maps built in their own files (shared/jankburg.js)
export { builder, rng, wall, slab, stairs, windows, shell, car, tree, streetlight, billboard, tower, carve, horizon, home, lollipop, conifer, adBoard, stall, pot, cart, tent, palm, pallets, forklift, groundHoles, unstick };
