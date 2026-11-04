// All maps are lists of axis-aligned boxes. Shared by server (physics, bots) and client (rendering).
// Maps are generated deterministically so server and client always match.
// Rule of thumb for builders: never let two different surfaces sit in the same plane (that flickers).
import { buildNav, navPath, navLocate, navClear } from './nav.js';

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
  // a local frame: origin (ox, oy, oz), rotated rot*90deg. local -z is "the front".
  const local = (ox, oz, rot = 0, oy = 0) => {
    const T = (x, z) => [[x, z], [-z, x], [-x, -z], [z, -x]][rot & 3];
    const L = (x0, y0, z0, x1, y1, z1, mat, extra) => {
      const [ax, az] = T(x0, z0), [bx, bz] = T(x1, z1);
      if (extra && extra.pad) { const [px, pz] = T(extra.pad[0], extra.pad[2]); extra = { ...extra, pad: [px, extra.pad[1], pz] }; }
      add(ox + ax, oy + y0, oz + az, ox + bx, oy + y1, oz + bz, mat, extra);
    };
    L.B = (cx, cy, cz, sx, sy, sz, mat, extra) => L(cx - sx / 2, cy - sy / 2, cz - sz / 2, cx + sx / 2, cy + sy / 2, cz + sz / 2, mat, extra);
    return L;
  };
  return { boxes, add, box, local };
}

// a wall with holes cut in it. axis 'x' = runs along x at z=fixed, 'z' = runs along z at x=fixed.
// openings: [{ a, b, y0, y1 }] measured along the wall
function wall(L, axis, fixed, a0, a1, y0, y1, t, mat, openings = []) {
  const ops = openings.filter((o) => o.b > a0 && o.a < a1).sort((p, q) => p.a - q.a);
  const seg = (s0, s1, yy0, yy1) => {
    if (s1 - s0 < 0.02 || yy1 - yy0 < 0.02) return;
    if (axis === 'x') L(s0, yy0, fixed - t / 2, s1, yy1, fixed + t / 2, mat);
    else L(fixed - t / 2, yy0, s0, fixed + t / 2, yy1, s1, mat);
  };
  let cur = a0;
  for (const o of ops) {
    const a = Math.max(a0, o.a), b = Math.min(a1, o.b);
    seg(cur, a, y0, y1);
    seg(a, b, y0, Math.max(y0, o.y0));
    seg(a, b, Math.min(y1, o.y1), y1);
    cur = b;
  }
  seg(cur, a1, y0, y1);
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
    if (arriving && !isRoof) L(lane[1] + 0.05, y1 + 0.25, sz0 - 0.6, lane[1] + 0.15, y1 + 1.25, hd - 0.35, 'wood'); // railing
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
  if (along === 'x') { L.B(x - 4, y + 3, z, 0.4, 6, 0.4, 'metal'); L.B(x + 4, y + 3, z, 0.4, 6, 0.4, 'metal'); L.B(x, y + 7.5, z, w, 5, 0.4, 'billboard'); L.B(x, y + 4.9, z - 0.6, w, 0.2, 1.0, 'grid'); }
  else { L.B(x, y + 3, z - 4, 0.4, 6, 0.4, 'metal'); L.B(x, y + 3, z + 4, 0.4, 6, 0.4, 'metal'); L.B(x, y + 7.5, z, 0.4, 5, w, 'billboard'); L.B(x - 0.6, y + 4.9, z, 1.0, 0.2, w, 'grid'); }
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

const SKY_SUNSET = { top: 0x2b1d6b, mid: 0xff8fb8, bot: 0x14051a, fog: 0xf7a1c4 };

// ------------------------------------------------------------ CRATE: tiny on purpose, pure chaos
function crate() {
  const B = builder();
  const { box } = B;
  box(0, -1.5, 0, 30, 3, 30, 'grass');
  box(0, -5, 0, 20, 4, 20, 'dirt');
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) { box(8 * sx, 1, 8 * sz, 2, 2, 2, 'crate'); box(8 * sx + 1.6 * sx, 0.5, 8 * sz, 1.2, 1, 1.2, 'crate'); }
  box(0, 1, 10, 5, 2, 1, 'crate');
  box(0, 1, -10, 5, 2, 1, 'crate');
  box(0, 1.5, 0, 5, 3, 5, 'stone');
  box(0, 3.25, 0, 7, 0.5, 7, 'wood');
  box(-5, 0.15, 0, 1.8, 0.3, 1.8, 'pad', { pad: [4, 14, 0] });
  box(5, 0.15, 0, 1.8, 0.3, 1.8, 'pad', { pad: [-4, 14, 0] });
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) box(12 * sx, 15, 12 * sz, 2.5, 1, 2.5, 'pink');
  box(0, 21, 0, 3, 1, 3, 'gold');
  return { name: 'Crate', size: 'tiny', boxes: B.boxes, killY: -30, sky: SKY_SUNSET, fogNear: 50, fogFar: 200,
    spawns: [[-11, 0.1, -11], [11, 0.1, 11], [-11, 0.1, 11], [11, 0.1, -11]] };
}

// ------------------------------------------------------------ PLATFORM: one big flat gray slab
function platform() {
  const B = builder();
  B.box(0, -1, 0, 90, 2, 90, 'grid');
  B.box(0, -5, 0, 76, 6, 76, 'concrete');
  return { name: 'Platform', size: 'small', boxes: B.boxes, killY: -30,
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
  for (const [x, z, h, w, t] of [[0, -95, -2, 36, 2], [-95, 0, 8, 30, 1], [95, 6, -8, 40, 2], [6, 98, 12, 32, 1], [-85, -85, 24, 26, 3], [88, 88, -4, 30, 2], [-90, 90, 4, 34, 1], [92, -92, 16, 28, 2]]) {
    const ry = tower(B, x, z, w, w, h, { tiers: t, base: -152, r });
    spawns.push([x + 3, ry + 0.1, z + 3]);
  }
  return { name: 'Rooftop', size: 'medium', boxes: B.boxes, killY: -130,
    sky: { top: 0x05051a, mid: 0x4a2a7a, bot: 0x000005, fog: 0x2a2050 }, fogNear: 110, fogFar: 480, spawns };
}

// ------------------------------------------------------------ SUBURB: a whole neighbourhood with real houses
function house(B, ox, oz, rot, siding, carColor, r) {
  const L = B.local(ox, oz, rot);
  const F = 3.4;
  // main house: 2 floors, rooms, stairs, roof
  shell(L, 14, 12, 2, F, siding, { roof: 'roof', backDoor: true, sideDoor: [1, 2.6] });
  // ground floor rooms: wall splits kitchen (left) from living room, and living room from the laundry at the back
  wall(L, 'z', -1, -6, 6, 0.12, F, 0.2, 'plaster', [{ a: -4, b: -2.4, y0: 0, y1: 2.4 }]);
  wall(L, 'x', 1.5, -1, 7, 0.12, F, 0.2, 'plaster', [{ a: 2, b: 3.4, y0: 0, y1: 2.4 }]);
  // upstairs: two bedrooms + bathroom
  wall(L, 'x', 1, -1.6, 7, F + 0.25, 2 * F, 0.2, 'plaster', [{ a: 0, b: 1.4, y0: F + 0.25, y1: F + 2.6 }]);
  wall(L, 'z', 2.5, 1, 6, F + 0.25, 2 * F, 0.2, 'plaster', [{ a: 2, b: 3.3, y0: F + 0.25, y1: F + 2.6 }]);
  wall(L, 'z', -1.6, -6, 1, F + 0.25, 2 * F, 0.2, 'plaster', [{ a: -3.5, b: -2, y0: F + 0.25, y1: F + 2.6 }]);
  // furniture
  L(-6.8, 0.12, -5.8, -5.8, 1.0, -2.4, 'white'); // kitchen counter
  L(-6.8, 0.12, -2.3, -6.0, 2.1, -1.5, 'chrome'); // fridge
  L(-4.6, 0.12, -1, -2.6, 0.9, 1, 'wood'); // dining table
  L(2, 0.12, -1.6, 6.6, 0.75, -0.6, 'cloth'); L(2, 0.75, -1, 6.6, 1.3, -0.6, 'cloth'); // couch
  L(3, 0.12, -5.8, 6, 0.6, -5.3, 'wood'); L(3.5, 0.6, -5.75, 5.5, 1.7, -5.65, 'glass'); // tv
  L(3, F + 0.25, 3.5, 6.6, F + 0.8, 5.8, 'carpet'); L(3, F + 0.8, 5.2, 6.6, F + 1.1, 5.8, 'white'); // bed 1
  L(-1.3, F + 0.25, -5.8, 2.2, F + 0.8, -3.6, 'carpet'); // bed 2
  L(-1.4, F + 0.25, 4.2, 1.2, F + 0.85, 5.8, 'tile'); // bathtub
  // stepped roof cap
  L(-6, 2 * F + 0.3, -5, 6, 2 * F + 0.7, 5, 'roof'); L(-4, 2 * F + 0.7, -3, 4, 2 * F + 1.1, 3, 'roof');
  // porch
  L(-3, 0, -7.6, 3, 0.25, -6, 'wood');
  L(-2.9, 0.25, -7.5, -2.6, 3.0, -7.2, 'wood'); L(2.6, 0.25, -7.5, 2.9, 3.0, -7.2, 'wood');
  L(-3.2, 3.0, -7.8, 3.2, 3.25, -6.15, 'roof');
  // garage: open front, flat roof you can climb onto (bin -> crate -> roof), window from the roof into the bedroom
  wall(L, 'z', 13, -6, 1.2, 0, 3.2, 0.3, 'brick');
  wall(L, 'x', 1.2, 7.15, 13, 0, 3.2, 0.3, 'brick');
  wall(L, 'x', -6, 7.15, 13, 0, 3.2, 0.3, 'brick', [{ a: 7.6, b: 12.6, y0: 0, y1: 2.7 }]);
  L(7.15, 0, -6, 13, 0.1, 1.2, 'concrete');
  L(7, 3.2, -6.2, 13.2, 3.5, 1.4, 'roofg');
  L(13.2, 0, -2.2, 14.3, 1.2, -1.1, 'metal'); // bin
  L(13.2, 0, -1.05, 14.6, 2.4, 0.4, 'crate');
  car(L, 10.1, -2.4, 1, carColor);
  // driveway + front path + mailbox
  L(7.4, 0, -17, 12.8, 0.12, -6.05, 'sidewalk');
  L(-1, 0, -17, 1, 0.12, -7.65, 'sidewalk');
  L.B(2.2, 0.6, -15.5, 0.15, 1.2, 0.15, 'wood'); L.B(2.2, 1.35, -15.5, 0.5, 0.35, 0.8, 'carblue');
  // backyard: fence, tree, trampoline onto the roof, shed
  const fy = 1.3;
  L(-8, 0, 13.9, 14, fy, 14.1, 'white');
  L(-8.1, 0, 6.2, -7.9, fy, 13.9, 'white');
  L(13.9, 0, 1.4, 14.1, fy, 11, 'white');
  tree(L, -4, 11, 4 + r() * 2);
  L(2.5, 0, 8.5, 5, 0.25, 11, 'pad', { pad: [0, 21, -4] });
  L(8, 0, 9, 12, 2.6, 13, 'wood'); L(7.8, 2.6, 8.8, 12.2, 2.8, 13.2, 'roofg');
  if (r() < 0.5) { // above-ground pool
    L(-6.5, 0, 7, -1.5, 1.1, 7.2, 'tile'); L(-6.5, 0, 11.6, -1.5, 1.1, 11.8, 'tile');
    L(-6.5, 0, 7.2, -6.3, 1.1, 11.6, 'tile'); L(-1.7, 0, 7.2, -1.5, 1.1, 11.6, 'tile');
    L(-6.3, 0, 7.2, -1.7, 0.85, 11.6, 'water');
  }
  return B.local(ox, oz, rot);
}

function suburb() {
  // compact neighbourhood, ~140 x 120 m: one main street with a side street off it (a T), houses close together,
  // a corner store, a little park and back alleys behind both rows of houses for flanking
  const B = builder();
  const r = rng(4242);
  const SX = 70, SZ = 60;
  B.add(-SX, -3, -SZ, SX, 0, SZ, 'grass');
  B.add(-SX + 8, -12, -SZ + 8, SX - 8, -3, SZ - 8, 'dirt');
  // main street along x, side street running north from it
  B.add(-SX, 0, -6, -2, 0.1, 6, 'roadx'); B.add(10, 0, -6, SX, 0.1, 6, 'roadx');
  B.add(-2, 0, -6, 10, 0.1, 6, 'road');
  B.add(-2, 0, 6, 10, 0.1, SZ - 4, 'roadz');
  // sidewalks (0.25 curbs, steppable)
  B.add(-SX, 0, -9, SX, 0.25, -6, 'sidewalk');
  B.add(-SX, 0, 6, -5, 0.25, 9, 'sidewalk'); B.add(13, 0, 6, SX, 0.25, 9, 'sidewalk');
  B.add(-5, 0, 9, -2, 0.25, SZ - 4, 'sidewalk'); B.add(10, 0, 9, 13, 0.25, SZ - 4, 'sidewalk');
  B.add(-5, 0, 6, -2, 0.25, 9, 'sidewalk'); B.add(10, 0, 6, 13, 0.25, 9, 'sidewalk');
  const W = B.local(0, 0, 0);
  for (let x = -60; x <= 60; x += 24) { streetlight(W, x, 8, -1); streetlight(W, x + 12, -8, 1); }
  for (const z of [22, 44]) { streetlight(W, -4, z, 1); streetlight(W, 12, z + 11, 1); }
  // side street dead-ends in sawhorses + a dumpster
  for (let x = -1; x <= 9; x += 2.5) { W(x - 0.9, 0.1, SZ - 5.5, x + 0.9, 1.1, SZ - 5.3, 'hazard'); W(x - 0.8, 0.1, SZ - 5.6, x - 0.7, 0.9, SZ - 5.2, 'wood'); W(x + 0.7, 0.1, SZ - 5.6, x + 0.8, 0.9, SZ - 5.2, 'wood'); }
  W(6, 0.1, SZ - 9, 9.5, 1.6, SZ - 7, 'containerg');
  // houses: rot 2 faces +z (south row, across from the north row), rot 0 faces -z (north row)
  const sidings = ['white', 'blue', 'yellow', 'mint', 'white'];
  const colors = ['carred', 'carblue', 'carwhite', 'carblack', 'cargreen'];
  const spots = [[-50, -24, 2], [-22, -24, 2], [6, -24, 2], [-48, 24, 0], [-21, 24, 0]];
  const spawns = [];
  spots.forEach(([x, z, rot], i) => {
    house(B, x, z, rot, sidings[i], colors[i], r);
    spawns.push([x + (rot ? -3 : 3), 0.3, z + (rot ? 3 : -3)]);
  });
  // corner store with a parking lot (south-east). flat roof, ladder-crates round the back
  const C = B.local(44, -30, 2);
  shell(C, 18, 12, 1, 4.2, 'brick', { roof: 'roofg', roofAccess: true, backDoor: true });
  C(-8.5, 0.12, -5.5, -1, 1.1, -4.6, 'wood'); C(1, 0.12, -5.5, 8.5, 1.1, -4.6, 'wood'); // counter + shelves
  for (const x of [-6, -2, 2, 6]) C(x - 0.4, 0.12, -1.5, x + 0.4, 1.9, 3.5, 'crate');
  C(-9, 3.3, -6.6, 9, 4.6, -6.15, 'billboard');
  C(-9.4, 0, 6.2, -7.4, 1.2, 8.2, 'crate'); C(-9.4, 1.2, 6.2, -8.4, 2.4, 7.2, 'crate'); C(-9.4, 2.4, 6.2, -8.9, 3.6, 6.7, 'crate');
  B.add(28, 0, -20, 62, 0.12, -9, 'concrete');
  for (let x = 30; x < 62; x += 4.5) B.add(x, 0.12, -19.8, x + 0.15, 0.13, -14, 'white');
  car(W, 32.2, -16.5, 1, 'carred'); car(W, 45.7, -16.5, 1, 'caryellow'); car(W, 54.7, -16.5, 1, 'carwhite');
  // parked along the street + one abandoned in the side street
  for (const [x, z, c] of [[-60, 4, 'carblue'], [-34, -4, 'carwhite'], [-8, 4, 'carblack'], [24, 4, 'cargreen'], [58, -4, 'carred']]) car(W, x, z, 0, c);
  car(W, 1.5, 30, 1, 'carwhite');
  // little park + playground in the north-east block
  const P = B.local(42, 34, 0);
  P(-26, 0, -22, 26, 0.12, 22, 'concrete');
  P(-25, 0.12, -21, 25, 0.2, 21, 'grass');
  P(-22, 0.2, -19, -2, 0.32, -4, 'sidewalk'); // half court
  P.B(-12, 2.1, -18.5, 0.3, 4, 0.3, 'metal'); P.B(-12, 3.6, -18, 1.8, 1.2, 0.15, 'white');
  P(6, 0.2, 4, 12, 3, 10, 'wood'); P(5.8, 3, 3.8, 12.2, 3.2, 10.2, 'pink');
  stairs(P, 6.5, 6, 3.9, -1, 0.2, 3, 'wood');
  for (let i = 0; i < 5; i++) P(12, 0.2, 5 + i * 0.01, 12 + (i + 1) * 1.2, 3 - i * 0.6, 7, 'caryellow');
  for (let i = 0; i < 6; i++) P.B(-4 + i * 1.6, 2.6, 15, 0.15, 0.15, 3, 'metal');
  for (const [x, z] of [[-4, 13.5], [-4, 16.5], [5, 13.5], [5, 16.5]]) P.B(x, 1.3, z, 0.2, 2.6, 0.2, 'metal');
  P(14, 0.2, 12, 21, 0.45, 19, 'sand');
  P(-10, 0.2, 4, -3, 0.9, 11, 'concrete'); P(-9.5, 0.2, 4.5, -3.5, 0.8, 10.5, 'water'); P.B(-6.5, 2, 7.5, 0.8, 3, 0.8, 'concrete');
  for (const [x, z] of [[19, -16], [-20, 16], [21, 0], [-24, 2]]) tree(P, x, z, 5);
  P(-26, 0, 21.5, 26, 1.4, 22, 'hedge');
  // back alleys behind both rows: fences, bins, a shed you can climb
  B.add(-SX, 0, -SZ + 2, 22, 0.12, -SZ + 9, 'concrete');
  B.add(-SX, 0, SZ - 9, -4, 0.12, SZ - 2, 'concrete');
  for (const [x, z] of [[-60, -SZ + 4], [-30, -SZ + 6.5], [-2, -SZ + 4], [-62, SZ - 4], [-36, SZ - 6.5], [-14, SZ - 4]]) { W(x, 0.12, z - 1, x + 2.4, 1.5, z + 1, 'containerb'); }
  W(14, 0.12, -SZ + 2.5, 20, 3, -SZ + 7.5, 'wood'); W(13.8, 3, -SZ + 2.3, 20.2, 3.3, -SZ + 7.7, 'roofg'); W(12.4, 0.12, -SZ + 4, 13.8, 1.5, -SZ + 5.4, 'crate');
  // map edge: low hedges with gaps so you can still fall off if you're dumb
  for (const sz of [-1, 1]) for (let x = -SX; x < SX; x += 20) B.add(x, 0, sz * SZ - (sz > 0 ? 0.6 : 0), x + 14, 1.2, sz * SZ + (sz < 0 ? 0.6 : 0), 'hedge');
  for (let i = 0; i < 8; i++) tree(W, -SX + 4 + r() * 2 * (SX - 4), (r() < 0.5 ? -1 : 1) * (SZ - 3 - r() * 2), 4 + r() * 3);
  spawns.push([42, 0.4, 34], [30, 0.4, 20], [4, 0.2, 45], [44, 0.3, -21], [-40, 0.2, -SZ + 5], [-40, 0.2, SZ - 5], [-60, 0.3, 0], [60, 0.3, 0]);
  return { name: 'Suburb', size: 'medium', boxes: B.boxes, killY: -40,
    sky: { top: 0x3f8fe0, mid: 0xcfe9ff, bot: 0x2a4060, fog: 0xcfe9ff }, fogNear: 90, fogFar: 300, spawns };
}

// ------------------------------------------------------------ WAREHOUSE: big indoor hall, offices, loading yard
function warehouse() {
  const B = builder();
  const { add, box } = B;
  const X = 60, Z = 40, H = 16;
  // floor with three pits into the void
  const pits = [[-30, -6, -22, 6], [-4, 18, 4, 30], [26, -26, 34, -16]];
  // build the floor as strips around the pits
  add(-X, -1, -Z, X, 0, -6, 'concrete'); add(-X, -1, 6, X, 0, Z, 'concrete');
  add(-X, -1, -6, -30, 0, 6, 'concrete'); add(-22, -1, -6, X, 0, 6, 'concrete');
  // (pit 2 and 3 are carved by leaving out squares)
  B.boxes.splice(0, 2);
  add(-X, -1, -Z, X, 0, -26, 'concrete');
  add(-X, -1, -16, X, 0, -6, 'concrete');
  add(-X, -1, -26, 26, 0, -16, 'concrete'); add(34, -1, -26, X, 0, -16, 'concrete');
  add(-X, -1, 6, X, 0, 18, 'concrete');
  add(-X, -1, 30, X, 0, Z, 'concrete');
  add(-X, -1, 18, -4, 0, 30, 'concrete'); add(4, -1, 18, X, 0, 30, 'concrete');
  for (const [x0, z0, x1, z1] of pits) { add(x0, -0.4, z0 - 0.3, x1, 0.6, z0, 'hazard'); add(x0, -0.4, z1, x1, 0.6, z1 + 0.3, 'hazard'); }
  // walls with big roll-up doors on the east side to the loading yard
  const W = B.local(0, 0, 0);
  wall(W, 'x', -Z, -X, X, 0, H, 0.6, 'metal', windows(2 * X, 8, 1, 3, 10));
  wall(W, 'x', Z, -X, X, 0, H, 0.6, 'metal', windows(2 * X, 8, 1, 3, 10));
  wall(W, 'z', -X, -Z, Z, 0, H, 0.6, 'metal', windows(2 * Z, 8, 1, 3, 10));
  wall(W, 'z', X, -Z, Z, 0, H, 0.6, 'metal', [{ a: -28, b: -18, y0: 0, y1: 6 }, { a: -6, b: 4, y0: 0, y1: 6 }, { a: 16, b: 26, y0: 0, y1: 6 }]);
  // roof with skylight strip and rafters
  add(-X, H, -Z, -6, H + 0.6, Z, 'roofg'); add(6, H, -Z, X, H + 0.6, Z, 'roofg');
  for (let z = -32; z <= 32; z += 8) add(-X, H - 1.6, z - 0.3, X, H - 1, z + 0.3, 'wood');
  // catwalks round three sides at y 7 + stairs up
  add(-X + 0.3, 7, -Z + 0.3, X - 0.3, 7.3, -Z + 3, 'grid');
  add(-X + 0.3, 7, Z - 3, X - 0.3, 7.3, Z - 0.3, 'grid');
  add(-X + 0.3, 7, -Z + 3, -X + 3, 7.3, Z - 3, 'grid');
  for (const z of [-Z + 3, Z - 3.3]) { add(-X + 3, 7.3, z, X - 0.3, 8.3, z + 0.3, 'metal'); }
  stairs(W, -40, -37, -Z + 3.2, 1, 0, 7.3, 'grid');
  stairs(W, 37, 40, Z - 3.2, -1, 0, 7.3, 'grid');
  // pallet racks: three levels you can climb
  for (const x of [-44, -14, 14]) for (const z of [-30, 24]) {
    for (const lvl of [0, 2.4, 4.8]) add(x, lvl + 2, z - 1.2, x + 18, lvl + 2.25, z + 1.2, 'wood');
    for (const px of [x, x + 6, x + 12, x + 18]) for (const pz of [z - 1.2, z + 1]) add(px - 0.1, 0, pz, px + 0.1, 7.3, pz + 0.2, 'hazard');
    for (let i = 0; i < 5; i++) box(x + 2 + i * 3.4, 0.6, z, 2, 1.2, 1.6, 'crate');
    box(x + 4, 3.0, z, 2, 1.2, 1.6, 'crate'); box(x + 12, 5.4, z, 2, 1.2, 1.6, 'crate');
  }
  // two-floor office block in the north-west corner
  const O = B.local(-46, 12, 2);
  shell(O, 16, 12, 2, 3.6, 'plaster', { floor: 'carpet', roof: 'roofg', roofAccess: true });
  O(-6, 0.12, -1, -2, 0.85, 1, 'wood'); O(2, 0.12, -1, 6, 0.85, 1, 'wood'); O(-6, 3.85, -1, -2, 4.6, 1, 'wood');
  // forklift + pallets + barrels inside
  const Fk = B.local(-4, -10, 0);
  Fk(-1.2, 0, -0.8, 1.2, 1.4, 0.8, 'caryellow'); Fk(-0.9, 1.4, -0.7, 0.4, 2.4, 0.7, 'glass'); Fk(1.2, 0, -0.4, 2.6, 0.2, 0.4, 'metal'); Fk(1.2, 0, -0.6, 1.4, 3, 0.6, 'metal');
  for (let i = 0; i < 6; i++) box(-10 + (i % 3) * 1.1, 0.6, 10 + Math.floor(i / 3) * 1.1, 0.9, 1.2, 0.9, 'containerb');
  // outdoor loading yard: containers, trucks
  add(X, -1, -Z - 10, X + 50, 0, Z + 10, 'concrete');
  add(X, 0, -Z - 10, X + 50, 0.1, -Z - 9.7, 'hazard');
  const Y = B.local(X + 25, 0, 0);
  const cont = (x, z, y, rot, m) => (rot ? Y(x - 1.25, y, z - 6, x + 1.25, y + 2.6, z + 6, m) : Y(x - 6, y, z - 1.25, x + 6, y + 2.6, z + 1.25, m));
  cont(-10, -30, 0, 0, 'containerr'); cont(-10, -30, 2.6, 0, 'containerb'); cont(4, -30, 0, 0, 'containerg');
  cont(-10, 30, 0, 0, 'containerb'); cont(4, 30, 0, 0, 'containerr'); cont(4, 30, 2.6, 0, 'containerg');
  cont(18, 0, 0, 1, 'containerr'); cont(18, 0, 2.6, 1, 'containerg'); cont(21, -14, 0, 1, 'containerb');
  for (const [x, z] of [[-12, -18], [-12, 10]]) { // trucks backed up to the doors
    Y(x - 6, 0.6, z - 1.3, x + 6, 3.8, z + 1.3, 'white');
    Y(x + 6.3, 0, z - 1.2, x + 9.3, 2.6, z + 1.2, 'carred'); Y(x + 6.4, 2.6, z - 1.1, x + 8.6, 3.4, z + 1.1, 'glass');
    for (const wx of [x - 4, x + 3, x + 8]) for (const wz of [z - 1.35, z + 1.05]) Y(wx - 0.5, 0, wz, wx + 0.5, 1, wz + 0.3, 'tire');
  }
  Y(-24, 0, -6, -20, 1.2, 6, 'concrete'); // loading dock lip
  Y(22, 0, 18, 24, 1.3, 20, 'crate'); Y(22, 1.3, 18, 24, 2.6, 20, 'crate');
  return { name: 'Warehouse', size: 'large', boxes: B.boxes, killY: -25,
    sky: { top: 0x101018, mid: 0x3a3048, bot: 0x050508, fog: 0x2a2433 }, fogNear: 60, fogFar: 220,
    spawns: [[-52, 0.1, -34], [52, 0.1, 34], [-52, 0.1, 34], [52, 0.1, -34], [0, 0.1, -12], [0, 0.1, 12], [84, 0.1, 0], [-46, 0.2, 12]] };
}

// ------------------------------------------------------------ DESERT: big sand town split by a canyon
function desert() {
  const B = builder();
  const r = rng(909);
  const S = 100;
  B.add(-S, -2, -S, -7, 0, S, 'sand'); B.add(7, -2, -S, S, 0, S, 'sand');
  B.add(-S + 10, -10, -S + 10, -9, -2, S - 10, 'dirt'); B.add(9, -10, -S + 10, S - 10, -2, S - 10, 'dirt');
  for (const z of [-55, 0, 55]) { B.box(0, -0.25, z, 14.2, 0.5, 4.5, 'wood'); B.add(-7.1, 0, z - 2.25, 7.1, 1, z - 2.05, 'wood'); B.add(-7.1, 0, z + 2.05, 7.1, 1, z + 2.25, 'wood'); }
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
  const roofs = [];
  for (const [x, z, rot, w, d, n] of blds) {
    const L = B.local(x, z, rot);
    const { top } = shell(L, w, d, n, 3.6, 'adobe', { floor: 'wood', roof: 'adobe', roofAccess: true, backDoor: r() < 0.6 });
    L(-w / 2 - 0.5, 2.6, -d / 2 - 2.2, w / 2 + 0.5, 2.8, -d / 2, 'cloth'); // awning
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
      M.B(cx, 3.1, 0, 5, 0.2, 4, 'cloth');
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
  return { name: 'Desert', size: 'large', boxes: B.boxes, killY: -30,
    sky: { top: 0x3f7fd0, mid: 0xf2d9a0, bot: 0x6a4a28, fog: 0xead6a6 }, fogNear: 110, fogFar: 400, spawns };
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
    box(Math.cos(a) * 48, 30 + (i % 2) * 9, Math.sin(a) * 48, 4, 2, 4, 'pink');
  }
  box(0, 42, 0, 12, 1.5, 12, 'missing');
  box(0, 70, 0, 5, 2, 5, 'gold');
  box(60, 55, -60, 6, 2, 6, 'pink');
  box(-60, 55, 60, 6, 2, 6, 'pink');
  return { name: 'Islands', size: 'large', boxes, killY: -45, sky: SKY_SUNSET, fogNear: 90, fogFar: 330,
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
    spawns.push([cx, 0.6, cz], [cx + 5, 4 * F + 0.6, cz + 5]);
  }
  // sky bridges between equal-height neighbours (enclosed glass tubes)
  const bridge = (x0, z0, x1, z1, y) => {
    if (z0 === z1) {
      B.add(x0, y - 0.3, z0 - 2, x1, y, z0 + 2, 'concrete');
      B.add(x0, y, z0 - 2, x1, y + 2.6, z0 - 1.8, 'glassblock'); B.add(x0, y, z0 + 1.8, x1, y + 2.6, z0 + 2, 'glassblock');
      B.add(x0, y + 2.6, z0 - 2, x1, y + 2.9, z0 + 2, 'roofg');
    } else {
      B.add(x0 - 2, y - 0.3, z0, x0 + 2, y, z1, 'concrete');
      B.add(x0 - 2, y, z0, x0 - 1.8, y + 2.6, z1, 'glassblock'); B.add(x0 + 1.8, y, z0, x0 + 2, y + 2.6, z1, 'glassblock');
      B.add(x0 - 2, y + 2.6, z0, x0 + 2, y + 2.9, z1, 'roofg');
    }
  };
  bridge(-35 + 15.4, -35, 35 - 15.4, -35, roofs['-35,-35']);
  bridge(35 + 18.4, 35, 100 - 15.4, 35, roofs['35,35']);
  // openings in the parapets where bridges arrive
  B.boxes.splice(0, 0);
  // window washer platforms and ledges to grapple
  for (let i = 0; i < 18; i++) {
    const [x, z, w, d, h] = plan[(r() * plan.length) | 0];
    const side = (r() * 4) | 0, y = base + 60 + r() * (h - base - 70);
    const off = [[0, -d / 2 - 1], [0, d / 2 + 1], [-w / 2 - 1, 0], [w / 2 + 1, 0]][side];
    B.box(x + off[0], y, z + off[1], side < 2 ? 6 : 1.6, 0.4, side < 2 ? 1.6 : 6, 'metal');
  }
  for (let k = 0; k < 10; k++) B.box((r() - 0.5) * 300, 140 + r() * 40, (r() - 0.5) * 300, 5, 1.5, 5, 'gold');
  return { name: 'Skyline', size: 'huge', boxes: B.boxes, killY: -80,
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
      for (const dz of [-1.4, 1.4]) B.box(x + sx * -1.8, 1.3, z + dz, 0.15, 2.6, 0.15, 'wood');
      B.add(x - 2.4, 2.6, z - 1.9, x + 2.4, 2.75, z + 1.9, (z / 8) % 2 ? 'cloth' : 'pink');
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
  B.add(20, 3.4, -29.6, 20.4, 4.4, -16, 'adobe'); B.add(20, 3.4, -8.4, 20.4, 4.4, -2.4, 'adobe');
  B.add(33.6, 3.4, -26, 34, 4.4, -2.4, 'adobe'); // east parapet, gap at the A end so you can drop onto the terrace
  for (const z of [-24, -18, -12, -6]) B.box(27, 3.4 + 0.5, z, 1.2, 1, 1.2, 'crate');
  // a crate staircase in A's approach: hop up and over the parapet onto the Bridge
  B.add(37.4, 0, -15, 38.6, 1.2, -13.8, 'crate');
  B.add(36.2, 0, -15, 37.4, 2.4, -13.8, 'crate');
  B.add(34, 0, -15, 36.2, 3.6, -13.8, 'crate');

  // ---- A LONG: Canal Street. long sightline, a sunken canal you can drop into as a lower lane
  B.add(50, -1.6, -6, 56, -1.2, 70, 'water');
  B.add(49.6, -1.2, -6, 50, -0.4, 70, 'adobe');
  B.add(50, -1.6, -6.5, 56, 0, -6, 'adobe'); B.add(50, -1.6, 70, 56, 0, 70.4, 'adobe');
  for (const z of [44, 14]) stairs(W, 50.2, 52.2, z, 1, -1.2, 0, 'stone', 0.6);
  for (const [x, z, s2] of [[38, 44, 2], [44, 26, 2], [38, 8, 1.6]]) { B.box(x, s2 / 2, z, s2, s2, s2, 'crate'); }
  B.box(44, 2.4, 26, 1.4, 1.4, 1.4, 'crate');
  for (const [x, z] of [[36, 60], [47, 30], [36, 2]]) tree(W, x, z, 5 + r() * 1.5);
  // upper long: a walkway along the west wall, stairs up at the south end, drop off at the north end
  stairs(W, 34.2, 36.8, 44.4, -1, 0, 3.2, 'wood', 0.5);
  B.add(34, 2.95, 10, 37, 3.2, 40.8, 'wood');
  B.add(36.8, 3.2, 10, 37, 4.1, 40.8, 'wood'); // rail
  for (let z = 12; z <= 40; z += 7) B.box(36.6, 1.5, z, 0.3, 2.95, 0.3, 'wood');
  B.add(34, 3.2, 9.8, 37, 4.1, 10, 'wood');
  // the Gate: chokepoint into A, with a hole up high you can jump through
  wall(W, 'x', -6, 34, 56, 0, 6, 1, 'brick', [{ a: 40, b: 46, y0: 0, y1: 4 }, { a: 51, b: 53.5, y0: 1.9, y1: 3.1 }]);

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
  block(-30, -52, -20, -30, 7);
  for (let x = -62; x <= -34; x += 4) B.box(x, 2.5, -53, 0.9, 5, 0.9, 'stone');
  B.add(-63, 5, -55, -33, 5.6, -51, 'roof');
  for (const [x, h] of [[-61.6, 1.2], [-61.6, 2.4], [-61.6, 3.6], [-61.6, 4.8]]) B.add(x - 0.6, 0, -56 - h * 0.85 - 0.6, x + 0.6, h, -56 - h * 0.85 + 0.6, 'crate');
  B.add(-64, 0, -52, -30, 0.05, -24, 'stone'); // paving
  // fountain (octagon-ish basin), the middle of B
  const fx = -46, fz = -38;
  for (let i = 0; i < 8; i++) { const a = (i / 8) * Math.PI * 2; B.box(fx + Math.cos(a) * 3, 0.45, fz + Math.sin(a) * 3, 2.6, 0.8, 2.6, 'stone'); }
  B.add(fx - 2, 0.05, fz - 2, fx + 2, 0.5, fz + 2, 'water');
  B.box(fx, 1.6, fz, 0.8, 2.2, 0.8, 'stone');
  B.box(-56, 0.6, -46, 1.2, 1.2, 1.2, 'crate'); B.box(-36, 0.6, -32, 2, 1.2, 1.2, 'crate'); B.box(-38, 1.6, -45, 2.4, 3.2, 1.2, 'wood');
  B.add(-64, 0, -52, -63.7, 6, -24, 'blue'); // painted wall: B is cool

  // ---- the Spice House: two floors between mid plaza and B. door from the plaza, door + upstairs window onto B
  const SX0 = -30, SX1 = -20, SZ0 = -30, SZ1 = -6, F = 3.6;
  B.add(SX0, 0, SZ0, SX1, 0.12, SZ1, 'wood');
  wall(W, 'z', SX1, SZ0, SZ1, 0, 2 * F, 0.4, 'plaster', [{ a: -18, b: -15, y0: 0, y1: 2.8 }, { a: -11, b: -9, y0: F + 1, y1: F + 2.2 }]);
  wall(W, 'z', SX0, SZ0, SZ1, 0, 2 * F, 0.4, 'plaster', [{ a: -28, b: -25.5, y0: 0, y1: 2.8 }, { a: -29.4, b: -26.6, y0: F + 0.25, y1: F + 2.7 }]);
  // balcony over B: walk upstairs, out the door, look down on the site (or drop in)
  B.add(-34, F, -30, -30.2, F + 0.25, -24, 'wood');
  B.add(-34, F + 0.25, -30, -33.8, F + 1.15, -24, 'wood'); B.add(-33.8, F + 0.25, -30, -30.2, F + 1.15, -29.8, 'wood');
  B.box(-33.8, F / 2, -24.3, 0.3, F, 0.3, 'wood'); B.box(-33.8, F / 2, -29.7, 0.3, F, 0.3, 'wood');
  wall(W, 'x', SZ0, SX0, SX1, 0, 2 * F, 0.4, 'plaster');
  wall(W, 'x', SZ1, SX0, SX1, 0, 2 * F, 0.4, 'plaster');
  slab(W, SX0, SZ0, SX1, SZ1, F, F + 0.25, 'wood', [-23, -12, -21, -6.4]);
  stairs(W, -23, -21, -12, 1, 0.12, F + 0.25, 'wood', 0.6);
  B.add(SX0, 2 * F, SZ0, SX1, 2 * F + 0.3, SZ1, 'roof');
  for (const [x, z] of [[-27, -20], [-24, -9]]) B.box(x, 0.6, z, 1.2, 1.2, 1.2, 'crate');
  B.add(-29.5, F + 0.25, -24, -28, F + 1.1, -14, 'cloth'); // sacks of spice upstairs
  block(-30, -6, -20, -2, 7);

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
  B.add(-58, -3.9, 18, -50.4, -3.5, 30, 'stone');
  B.add(-58.4, -3.5, 18, -58, -0.4, 30, 'stone'); B.add(-58, -3.5, 17.6, -50.4, -0.4, 18, 'stone'); B.add(-58, -3.5, 30, -50.4, -0.4, 30.4, 'stone');
  B.add(-56, -3.5, 21, -52, -3.45, 27, 'water');
  for (const z of [44, 30, 14, 2]) B.box(-45, -1.95, z, 1, 3.1, 1, 'stone');
  for (const z of [40, 20, 0]) B.box(-49.7, -1.6, z, 0.2, 0.4, 0.6, 'light');

  const att = [[-12, 0.1, 66], [-6, 0.1, 70], [0, 0.1, 63], [6, 0.1, 70], [12, 0.1, 66], [-16, 0.1, 58], [16, 0.1, 58]];
  const def = [[-12, 0.1, -70], [-6, 0.1, -63], [0, 0.1, -61], [6, 0.1, -63], [12, 0.1, -70], [-16, 0.1, -62], [16, 0.1, -62]];
  const spawns = [...att, ...def, [0, 0.1, 20], [42, 0.1, 30], [-45, -3.4, 20], [46, 1.7, -40], [-50, 0.1, -32], [8, 0.1, -12], [27, 3.5, -16], [40, 0.1, -60], [-41, 0.1, -60], [-25, 0.2, -16]];
  return {
    name: 'Bazaar', size: 'large', boxes: B.boxes, killY: -30,
    sky: { top: 0x4a8fd8, mid: 0xf2dcae, bot: 0x8a6a40, fog: 0xf0d8a8 }, fogNear: 90, fogFar: 320,
    spawns, teamSpawns: { att, def },
    // bot routes along the real lanes, [x, z] points ending on each site
    nav: {
      A: [
        [[16, 62], [28, 62], [42, 62], [42, 30], [43, 6], [43, -3], [43, -10], [47, -21], [47, -27], [46, -38]], // canal street
        [[0, 56], [0, 30], [0, 2], [8, -3], [18, -2.5], [18, -10], [18, -14], [24, -20], [31, -27.5], [37, -28.5], [44, -38]], // hall -> bridge
        [[8, -64], [22, -62], [32, -58], [39, -57], [39, -52], [41, -47], [46, -40]], // defenders' garden
      ],
      B: [
        [[-16, 62], [-30, 61], [-43, 60], [-43, 57], [-43, 52], [-43, 44], [-43, 30], [-43, 8], [-46, -2], [-46, -9], [-46, -18], [-46, -25], [-44, -31]], // cistern
        [[0, 56], [0, 30], [0, 2], [-8, -8], [-17, -16.5], [-21.5, -16.5], [-25, -21], [-26, -26.7], [-31, -26.7], [-35, -28], [-40, -33]], // hall -> spice house
        [[-8, -64], [-22, -62], [-32, -58], [-40, -56], [-44, -50], [-52, -45]], // defenders' arcade
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
  return { name: 'Range', size: 'training', boxes, killY: -40,
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
