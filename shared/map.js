// All maps are lists of axis-aligned boxes. Shared by server (physics, bots) and client (rendering).
// Maps are generated deterministically so server and client always match.
// Rule of thumb for builders: never let two different surfaces sit in the same plane (that flickers).
import { buildNav, navPath, navLocate, navClear } from './nav.js';
import { outOfBounds } from './bounds.js';
import { shapeGround } from './terrain.js';
import { SKULL, skullSolid } from './skullshape.js';
import { prop } from './props.js';
import { seen, propOf, spinAt } from './propcap.js'; // round 4: which boxes a Blender prop draws instead (look-only)
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
    seen(boxes[boxes.length - 1], boxes); // (a kit prop's box, or a crate / barrel / container on its own: propcap.js)
  };
  const box = (cx, cy, cz, sx, sy, sz, mat, extra) => add(cx - sx / 2, cy - sy / 2, cz - sz / 2, cx + sx / 2, cy + sy / 2, cz + sz / 2, mat, extra);
  // a box turned yaw radians round its centre: RENDER-ONLY builders (map.deco) only, physics and bots never see these
  const obb = (cx, cy, cz, sx, sy, sz, yaw, mat, extra) => { if (sx > 0.01 && sy > 0.01 && sz > 0.01) { boxes.push(Object.assign({ min: [cx - sx / 2, cy - sy / 2, cz - sz / 2], max: [cx + sx / 2, cy + sy / 2, cz + sz / 2], mat, rot: yaw }, extra || {})); seen(boxes[boxes.length - 1], boxes); } };
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
    L.yaw = -(rot & 3) * Math.PI / 2; // the frame's turn as three's rotation.y (Blender props' placements)
    // a prop model at local (x, z), turned r more quarter turns. returns the tag for the boxes it stands in for
    L.P = (id, x, z, r = 0, o = {}) => {
      const [ax, az] = T(x, z);
      boxes.props.push({ id, p: [ox + ax, oy + (o.y || 0), oz + az], r: (rot + r) & 3, v: o.v, color: o.color, s: o.s });
      return { pv: id };
    };
    return L;
  };
  // a Blender building (public/models/arch/<id>.glb, public/js/archfield.js) placed like local(): the returned frame tags
  // every box drawn through it { av: id }, and the client skips those boxes while the model is loaded. visual only:
  // the boxes stay exactly as they were for physics, bots and hits. o: paint (map material keys for its painted parts)
  boxes.arch = [];
  const arch = (id, ox, oz, rot = 0, oy = 0, o = {}) => {
    boxes.arch.push({ id, p: [ox, oy, oz], r: rot & 3, ...o });
    const L = local(ox, oz, rot, oy), tag = { av: id, ai: boxes.arch.length - 1 }; // (ai: which placement)
    const A = (x0, y0, z0, x1, y1, z1, mat, extra) => L(x0, y0, z0, x1, y1, z1, mat, extra ? { ...extra, ...tag } : tag);
    A.B = (cx, cy, cz, sx, sy, sz, mat, extra) => A(cx - sx / 2, cy - sy / 2, cz - sz / 2, cx + sx / 2, cy + sy / 2, cz + sz / 2, mat, extra);
    A.pt = L.pt; A.P = L.P; A.plain = L; // (plain: the same frame without the tag, for the furniture inside)
    return A;
  };
  // the same for boxes a helper already added (roofTop() and friends): everything from boxes[n0] on gets the tag
  const archSince = (n0, id, ox, oz, rot = 0, oy = 0, o = {}) => { boxes.arch.push({ id, p: [ox, oy, oz], r: rot & 3, ...o }); for (let i = n0; i < boxes.length; i++) Object.assign(boxes[i], { av: id, ai: boxes.arch.length - 1 }); };
  return { boxes, add, box, local, obb, arch, archSince };
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
function slab(L, x0, z0, x1, z1, y0, y1, mat, hole, e) {
  if (!hole) { L(x0, y0, z0, x1, y1, z1, mat, e); return; }
  const [hx0, hz0, hx1, hz1] = hole;
  L(x0, y0, z0, x1, y1, hz0, mat, e);
  L(x0, y0, hz1, x1, y1, z1, mat, e);
  L(x0, y0, hz0, hx0, y1, hz1, mat, e);
  L(hx1, y0, hz0, x1, y1, hz1, mat, e);
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
function car(L, x, z, rot, color = 'carred') { propOf('car', L.pt(x, 0, z), L.yaw + (rot ? -Math.PI / 2 : 0), () => carBoxes(L, x, z, rot, color), { t: color }); } // (the Blender car stands in for the boxes)
function carBoxes(L, x, z, rot, color) {
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
const quarter = (L, x, z) => { const [ax, , az] = L.pt(x, 0, z); return L.yaw + Math.floor(spinAt(ax, az) / (Math.PI / 2)) * Math.PI / 2; };
function tree(L, x, z, h = 4.5) {
  propOf('lollipop', L.pt(x, 0, z), quarter(L, x, z), () => {
    L.B(x, h / 2, z, 0.6, h, 0.6, 'wood');
    L.B(x, h + 0.9, z, 3.6, 1.8, 3.6, 'leaves');
    L.B(x, h + 2.2, z, 2.4, 1.0, 2.4, 'leaves');
  }, { t: 'leaves' });
}
function streetlight(L, x, z, armDir = 1) {
  propOf('streetlight', L.pt(x, 0, z), L.yaw + (armDir < 0 ? Math.PI : 0), () => {
    L.B(x, 3, z, 0.25, 6, 0.25, 'metal');
    L(x, 5.8, z - 0.12, x + armDir * 1.6, 6.0, z + 0.12, 'metal');
    L.B(x + armDir * 1.6, 5.8, z, 0.6, 0.25, 0.4, 'light');
  });
}
function acUnit(L, x, z, y) { propOf('acunit', L.pt(x, y, z), L.yaw, () => { L.B(x, y + 0.7, z, 2, 1.4, 1.4, 'metal'); L.B(x, y + 1.45, z, 1.2, 0.1, 1.2, 'grid'); }); }
function waterTower(L, x, z, y) {
  propOf('watertower', L.pt(x, y, z), L.yaw, () => {
    for (const ox of [-1.3, 1.3]) for (const oz of [-1.3, 1.3]) L.B(x + ox, y + 2.5, z + oz, 0.3, 5, 0.3, 'wood');
    L.B(x, y + 5.2, z, 3.6, 0.3, 3.6, 'wood');
    L.B(x, y + 7, z, 3.2, 3.4, 3.2, 'wood');
    L.B(x, y + 8.9, z, 2.4, 0.4, 2.4, 'roofg');
  });
}
// billboards: the face (frame, catwalk, lamps; the picture stays a box) and each post are their own Blender props, so
// every size of board fits (the posts are always 6 m, the faces aren't)
const bbPost = (L, x, y, z, sx, sz) => propOf('billboard_post', L.pt(x, y, z), L.yaw, () => L.B(x, y + 3, z, sx, 6, sz, 'metal'));
const bbPicture = { keep: (b) => !!b.fit };
function billboard(L, x, z, y, along = 'x') {
  const w = 12;
  if (along === 'x') { bbPost(L, x - 4, y, z, 0.3, 0.3); bbPost(L, x + 4, y, z, 0.3, 0.3); propOf('billboard', L.pt(x, y, z), L.yaw, () => { L.B(x, y + 7.5, z, w, 5, 0.4, 'billboard', { fit: 1 }); L.B(x, y + 4.9, z - 0.6, w, 0.2, 1.0, 'grid'); }, bbPicture); }
  else { bbPost(L, x, y, z - 4, 0.3, 0.3); bbPost(L, x, y, z + 4, 0.3, 0.3); propOf('billboard', L.pt(x, y, z), L.yaw + Math.PI / 2, () => { L.B(x, y + 7.5, z, 0.4, 5, w, 'billboard', { fit: 1 }); L.B(x - 0.6, y + 4.9, z, 1.0, 0.2, w, 'grid'); }, bbPicture); }
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
  if (kind === 'helipad') L(-5.5, 0, -5.5 + 2, 5.5, 0.15, 5.5 + 2, 'helipad', { fit: 1 });
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
    // a vertical neon sign up the corner of some towers (once a tower: this runs per face, and four strips in one spot flickered)
    if (r() < 0.6 && nx === 1) D.add(t.x + t.w / 2, y + 9, t.z - t.d / 2 - 0.3, t.x + t.w / 2 + 0.3, y + 30, t.z - t.d / 2 + 2.4, pick(strip));
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
    D.add(x - 3.5, y - 0.2, z0, x + 3.5, y + 0.34, z0 + len, 'wood'); // (a hair over the promenade: a pier can reach over the next stretch's)
    for (let z = z0 + 4; z < z0 + len; z += 6) for (const px of [x - 3.2, x + 2.9]) D.add(px, y - 4.2, z, px + 0.3, y - 0.2, z + 0.3, 'wood');
    if (r() < 0.6) { D.add(x - 2.6, y + 0.34, z0 + len - 14, x + 2.6, y + 3.6, z0 + len - 4, pick(['containerb', 'brick', 'sidelemon', 'containerr'])); D.add(x - 2.9, y + 3.6, z0 + len - 14.3, x + 2.9, y + 4, z0 + len - 3.7, 'roofg'); }
    for (let k = 0; k < 3; k++) D.add(x - 2 + k * 1.3, y + 0.34, z0 + 6, x - 1 + k * 1.3, y + 1.34, z0 + 7, 'crate');
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
  propOf('toysorter', [0, 0, 0], 0, () => { box(0, 1.5, 0, 5, 3, 5, 'toyface', { fit: 1 }); box(0, 3.25, 0, 7, 0.5, 7, 'toyteal'); }); // the middle: a shape sorter (Blender: p_toysorter)
  box(-5, 0.15, 0, 1.8, 0.3, 1.8, 'pad', { pad: [4, 14, 0] });
  box(5, 0.15, 0, 1.8, 0.3, 1.8, 'pad', { pad: [-4, 14, 0] });
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) box(12 * sx, 15, 12 * sz, 2.5, 1, 2.5, 'toypink');
  box(0, 21, 0, 3, 1, 3, 'gold');
  // it's a toy box on top of a tower of giant toy blocks, in a giant kid's playroom (render-only). fall off: you die long
  // before the carpet
  const D = builder(), F = -90; // the floor
  propOf('toytower', [0, 0, 0], 0, () => { D.box(0, -18, 0, 26, 22, 26, 'toyface', { fit: 1 }); D.obb(0.5, -48, -0.5, 24, 38, 24, 0.2, 'toyface2', { fit: 1 }); D.box(-1, -78, 1, 36, 24, 36, 'toyface', { fit: 1 }); }); // (Blender: p_toytower, giant wooden ABC blocks)
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

// ------------------------------------------------------------ the rig kit (Platform, Platform S&D)
// GLUG OIL's rig out in the North Sea. its decks: the cellar deck (-7.2, open grating with the sea under it), the main deck
// (0), the mezzanine (3.6: the pipe rack's walkway, the living quarters' 1st floor), the drill floor and the LQ's 2nd floor
// (7.2), the LQ roof and the helideck (10.8). the sea is 14 m down, the supply boat's deck 2 m above it
const RIG = { CD: -7.2, M1: 3.6, M2: 7.2, M3: 10.8, SEA: -14, BOAT: -12 };
const rigP = (alongX, bx) => (p0, y0, q0, p1, y1, q1, m, e) => (alongX ? bx.add(p0, y0, q0, p1, y1, q1, m, e) : bx.add(q0, y0, p0, q1, y1, p1, m, e));
// a handrail along x (alongX) or z, a0..a1 on the line c, on a deck at y. the top rail is the physics (1.1 up: you can't
// walk off or duck under it, a big enough hit still throws you over it); the posts and the knee rail are only to look at.
// gaps: [[a, b]] left open (stairs, gangways)
function rail(B, D, alongX, a0, a1, c, y, gaps = []) {
  const P = rigP(alongX, B), Q = rigP(alongX, D), cuts = [a0, ...gaps.flat(), a1];
  for (let i = 0; i + 1 < cuts.length; i += 2) {
    const s0 = cuts[i], s1 = cuts[i + 1]; if (s1 - s0 < 0.25) continue;
    P(s0, y + 0.98, c - 0.05, s1, y + 1.1, c + 0.05, 'rigyellow');
    Q(s0 + 0.08, y + 0.48, c - 0.03, s1 - 0.08, y + 0.54, c + 0.03, 'rigyellow');
    const n = Math.max(1, Math.round((s1 - s0) / 2.2));
    for (let k = 0; k <= n; k++) { const p = s0 + 0.04 + (s1 - s0 - 0.08) * k / n; Q(p - 0.04, y, c - 0.04, p + 0.04, y + 0.98, c + 0.04, 'rigyellow'); }
  }
}
// rails round a deck's edge (x0..x1, z0..z1 at y); g = { n, s, w, e: [[a, b]] } gaps along each side
function railBox(B, D, x0, z0, x1, z1, y, g = {}) {
  rail(B, D, true, x0, x1, z0 + 0.05, y, g.n); rail(B, D, true, x0, x1, z1 - 0.05, y, g.s);
  rail(B, D, false, z0 + 0.1, z1 - 0.1, x0 + 0.05, y, g.w); rail(B, D, false, z0 + 0.1, z1 - 0.1, x1 - 0.05, y, g.e);
}
// a steel stair along x (alongX) or z from a0 (its foot, at ya) to a1 (its head, yb), c0..c1 across: grating treads
// (o.thin: each a 0.3 slab, open underneath; otherwise solid steps), a handrail up each side (o.rails: which, -1 / 1).
// returns { bot, top } for the walk graph (the foot 1.3 m clear of the first step, the head 0.7 m onto the landing)
function rigStair(B, D, alongX, a0, a1, c0, c1, ya, yb, o = {}) {
  const n = Math.max(1, Math.ceil((yb - ya) / 0.45 - 1e-9)), h = (yb - ya) / n, run = (a1 - a0) / n, s = Math.sign(run), cm = (c0 + c1) / 2;
  const P = rigP(alongX, B), Q = rigP(alongX, D), lo = Math.min(c0, c1), hi = Math.max(c0, c1);
  for (let i = 1; i <= n; i++) {
    const p0 = a0 + (i - 1) * run, p1 = a0 + i * run, y = ya + i * h, pm = (p0 + p1) / 2;
    P(p0, o.thin ? y - 0.3 : ya, lo, p1, y, hi, o.mat || 'grating');
    for (const sd of o.rails || [-1, 1]) {
      const e = sd > 0 ? hi : lo;
      P(p0, y + 0.98, e - 0.05, p1, y + 1.1, e + 0.05, 'rigyellow');
      if (i % 2) Q(pm - 0.04, y, e - 0.04, pm + 0.04, y + 0.98, e + 0.04, 'rigyellow');
    }
  }
  return { bot: alongX ? [a0 - s * 1.3, ya, cm] : [cm, ya, a0 - s * 1.3], top: alongX ? [a1 + s * 0.7, yb, cm] : [cm, yb, a1 + s * 0.7] };
}
// a separator: a horizontal pressure vessel along x (x0..x1) round z = c, 3.4 across: an octagon in section (three boxes),
// its rounded ends, two yellow saddles, a manway, valves and pipes off its back, a level gauge. cover on the deck, and its
// back (4.0) is a step up onto the pipe rack
function separator(B, D, x0, x1, c, y = 0) {
  const r = 1.7, k = 0.7, y0 = y + 0.6;
  B.add(x0 + 0.6, y0, c - r + k, x1 - 0.6, y0 + 2 * r, c + r - k, 'rigsteel');
  B.add(x0 + 0.6, y0 + k, c - r, x1 - 0.6, y0 + 2 * r - k, c - r + k, 'rigsteel'); B.add(x0 + 0.6, y0 + k, c + r - k, x1 - 0.6, y0 + 2 * r - k, c + r, 'rigsteel');
  B.add(x0, y0 + k, c - r + k, x0 + 0.6, y0 + 2 * r - k, c + r - k, 'rigsteel'); B.add(x1 - 0.6, y0 + k, c - r + k, x1, y0 + 2 * r - k, c + r - k, 'rigsteel'); // the ends
  for (const x of [x0 + 1.8, x1 - 1.8]) B.add(x - 0.45, y, c - 1.35, x + 0.45, y0 + 0.5, c + 1.35, 'rigyellow'); // saddles
  D.add(x0 - 0.12, y0 + 1.1, c - 0.5, x0, y0 + 2.3, c + 0.5, 'rigyellow'); // the manway in its end
  for (const x of [x0 + 3.5, (x0 + x1) / 2, x1 - 3.5]) { D.add(x - 0.25, y0 + 2 * r, c - 0.25, x + 0.25, y0 + 2 * r + 0.5, c + 0.25, 'rigred'); D.add(x - 0.4, y0 + 2 * r + 0.5, c - 0.06, x + 0.4, y0 + 2 * r + 0.56, c + 0.06, 'rigyellow'); } // nozzles, handwheels
  D.add((x0 + x1) / 2 - 1.4, y0 + 0.9, c - r - 0.08, (x0 + x1) / 2 + 1.4, y0 + 1.3, c - r, 'glass'); // the level gauge
}
// the pipe rack along x (x0..x1) round z = c: steel frames every 5 m, the walkway on top (3.6, grating, 2.2 wide) between
// two bundles of pipes, cable trays slung under it. gap: [a, b] where a stair comes up through the pipes on its +z side
function pipeRack(B, D, x0, x1, c, gap = null) {
  const y = RIG.M1;
  B.add(x0, y - 0.3, c - 1.1, x1, y, c + 1.1, 'grating');
  for (let x = x0 + 0.3; x < x1; x += 5) { B.add(x - 0.18, 0, c - 3.05, x + 0.18, y - 0.6, c - 2.7, 'rigsteel'); B.add(x - 0.18, 0, c + 2.7, x + 0.18, y - 0.6, c + 3.05, 'rigsteel'); B.add(x - 0.18, y - 0.6, c - 3.05, x + 0.18, y - 0.3, c + 3.05, 'rigsteel'); }
  for (const s of [-1, 1]) for (const [q0, q1, m] of [[1.2, 1.7, 'pipe'], [1.8, 2.3, 'rigyellow'], [2.4, 2.95, 'pipe']]) {
    const z0 = c + s * q0, z1 = c + s * q1;
    if (s > 0 && gap) { B.add(x0, y - 0.3, z0, gap[0], y + 0.25, z1, m); B.add(gap[1], y - 0.3, z0, x1, y + 0.25, z1, m); } else B.add(x0, y - 0.3, z0, x1, y + 0.25, z1, m);
  }
  for (const s of [-1, 1]) D.add(x0 + 0.5, y - 1.15, c + s * 0.5, x1 - 0.5, y - 1.05, c + s * 1.0, 'grating'); // cable trays
}
// the living quarters (x 18..34, z -14..14): the galley on the ground floor, bunks on the 1st (3.6), the control room on
// the 2nd (7.2), the roof (10.8) and the helideck off its east side; a steel stair tower up its north side to every floor and
// the roof; the lifeboats in their davits off the deck's north edge, the muster point. the pipe rack comes in at the 1st
// floor's west door
function livingQuarters(B0, D0, dx, dz, st, o = {}) {
  const { B, D, add, W, up } = isPiece(B0, D0, dx, dz, st);
  const X0 = 18, X1 = 34, Z0 = -14, Z1 = 14, t = 0.3, op = (a, b, y0, y1) => ({ a, b, y0, y1 });
  const win = (list, y) => list.map(([a, b]) => op(a, b, y + 1.0, y + 2.3));
  add(X0 + t, 0, Z0 + t, X1 - t, 0.15, Z1 - t, 'tile'); const g0 = 0.15; // the galley's floor (lino on a raised floor: the furniture stands on it)
  add(X0, 3.3, Z0, X1, 3.6, Z1, 'rigsteel'); add(X0, 6.9, Z0, X1, 7.2, Z1, 'rigsteel'); add(X0, 10.5, Z0, X1, 10.8, Z1, 'rigsteel');
  for (const [y0, y1, f] of [[0, 3.3, 0], [3.6, 6.9, 1], [7.2, 10.5, 2]]) {
    const wW = f === 0 ? [op(-11, -9, 0, 2.4), op(9, 11, 0, 2.4)] : f === 1 ? [op(-1.1, 1.1, 3.6, 5.9), ...win([[-9, -6], [6, 9]], y0)] : win([[-11, -7], [-5, -1], [1, 5], [7, 11]], y0);
    const wE = win(f === 2 ? [[-11, -7], [-5, -1], [1, 5], [7, 11]] : [[-10, -8], [-4, -2], [2, 4], [8, 10]], y0);
    const wN = f === 0 ? [op(27.5, 29.5, 0, 2.4), ...win([[31, 32.6]], y0)] : f === 1 ? [op(24.6, 26.4, 3.6, 5.9), ...win([[29, 32]], y0)] : [op(18.6, 21.2, 7.2, 9.5), ...win([[23, 27], [29, 32.5]], y0)];
    const wS = f === 0 ? [op(23.5, 25.5, 0, 2.4), ...win([[19.5, 21.5], [28, 30], [31.5, 33]], y0)] : win(f === 2 ? [[19.5, 23], [25, 29], [30.5, 33]] : [[19.5, 21.5], [24, 26], [28.5, 30.5]], y0);
    wall(W, 'z', X0 + t / 2, Z0 + t, Z1 - t, y0, y1, t, 'rigwhite', wW);
    wall(W, 'z', X1 - t / 2, Z0 + t, Z1 - t, y0, y1, t, 'rigwhite', wE);
    wall(W, 'x', Z0 + t / 2, X0, X1, y0, y1, t, 'rigwhite', wN);
    wall(W, 'x', Z1 - t / 2, X0, X1, y0, y1, t, 'rigwhite', wS);
  }
  for (const yc of [3.3, 6.9, 10.5]) for (const z of [-9, -3, 3, 9]) for (const x of [22, 29]) D.add(x - 1.2, yc - 0.06, z - 0.2, x + 1.2, yc, z + 0.2, 'lamp'); // ceiling lights
  // the galley: tables and benches, the serving counter, Jank Cola, the telly, the signs
  for (const z of [-9, -3, 3, 9]) for (const x0 of [20.5, 26]) { add(x0, g0, z - 0.6, x0 + 3.6, g0 + 0.78, z + 0.6, 'wood'); add(x0 + 0.2, g0, z - 1.35, x0 + 3.4, g0 + 0.45, z - 0.95, 'toyteal'); add(x0 + 0.2, g0, z + 0.95, x0 + 3.4, g0 + 0.45, z + 1.35, 'toyteal'); }
  add(31.6, g0, -6, 33.7, g0 + 1.05, 6, 'rigsteel'); D.add(31.5, g0 + 1.05, -6.1, 33.7, g0 + 1.12, 6.1, 'chrome'); // the serving counter (back to the east wall)
  add(32.6, g0, 8, 33.7, g0 + 2.0, 9.4, 'toyred'); D.add(32.55, g0 + 0.6, 8.15, 32.6, g0 + 1.8, 9.25, 'adcity2', { fit: 1 }); // the cola machine (JANK COLA)
  D.add(18.3, 1.4, -2, 18.36, 2.4, 2, 'tvstatic'); D.add(18.3, 2.5, -3, 18.36, 3.1, 3, 'adgalley', { fit: 1 });
  D.add(33.64, 2.3, -3.5, 33.7, 3.0, 3.5, 'addays', { fit: 1 });
  // the 1st floor: bunks along the east and south walls, lockers, a corridor down the middle
  for (const z of [-11.5, -7.5, 4.5, 8.5]) { add(30.6, 3.6, z - 1.0, 33.7, 4.15, z + 1.0, 'rigblue'); D.add(30.6, 5.0, z - 1.0, 33.7, 5.12, z + 1.0, 'rigblue'); for (const zz of [z - 0.95, z + 0.9]) D.add(30.65, 4.15, zz, 30.75, 5.0, zz + 0.05, 'metal'); D.add(30.7, 4.15, z - 0.9, 33.6, 4.3, z + 0.9, 'bedsheet'); }
  for (const x of [21, 24.5]) { add(x, 3.6, 12.6, x + 2.4, 4.15, 13.7, 'rigblue'); D.add(x, 4.15, 12.7, x + 2.3, 4.3, 13.6, 'bedsheet'); }
  for (const z0 of [-5.4, 1.6]) for (let k = 0; k < 5; k++) add(18.3, 3.6, z0 + k * 0.76, 18.8, 5.6, z0 + k * 0.76 + 0.7, 'metal'); // lockers (the west wall, either side of the door)
  // the 2nd floor: the control room. consoles under the windows looking over the deck, the big red button
  add(18.3, 7.2, -11, 19.4, 8.1, -1.5, 'rigsteel'); add(18.3, 7.2, 1.5, 19.4, 8.1, 11, 'rigsteel');
  D.add(18.6, 8.1, -10.5, 19.3, 8.16, -2, 'radiopanel'); D.add(18.6, 8.1, 2, 19.3, 8.16, 10.5, 'radiopanel');
  add(25, 7.2, -2, 28, 8.0, 2, 'rigsteel'); D.add(26.1, 8.0, -0.4, 26.9, 8.25, 0.4, 'toyred'); // the big red button
  D.add(33.64, 9.0, -4, 33.7, 9.8, 4, 'adcontrol', { fit: 1 });
  // the roof: rails, aerials, the big sign over the deck; the stair tower comes up at its north-west corner
  railBox(B, D, X0, Z0, X1, Z1, RIG.M3, { n: [[24.1, 26.7]], e: [[-9.1, 9.1]] });
  D.add(19.2, RIG.M3, -11.6, 19.5, RIG.M3 + 7, -11.3, 'metal'); D.add(19.2, RIG.M3 + 6, -12.4, 19.5, RIG.M3 + 6.2, -10.5, 'metal'); D.add(30, RIG.M3, 10, 32, RIG.M3 + 1.4, 12, 'rigsteel');
  D.add(17.9, 11.9, -7, 17.96, 14.9, 7, 'adglug', { fit: 1 }); D.add(17.96, 11.9, -7.1, 18.2, 14.9, -6.95, 'rigsteel'); D.add(17.96, 11.9, 6.95, 18.2, 14.9, 7.1, 'rigsteel');
  // the stair tower (north of it): ground -> 1st (east), 1st -> 2nd (west), 2nd -> roof (east), a landing at each floor
  up({ ...rigStair(B, D, true, 19.4, 24.2, -19.6, -18.2, 0, RIG.M1, { thin: true }), top: [25.6, RIG.M1, -18.9] }); // (the head's right by the rails' ends)
  add(24.2, 3.3, -19.8, 26.6, 3.6, -14, 'grating');
  up(rigStair(B, D, true, 24.2, 20.0, -17.8, -16.4, RIG.M1, RIG.M2, { thin: true }));
  add(17.6, 6.9, -19.8, 20.0, 7.2, -14, 'grating'); add(20.0, 6.9, -16.4, 21.6, 7.2, -14, 'grating'); // (the 2nd floor's landing runs on round to its door)
  up({ ...rigStair(B, D, true, 20.0, 24.2, -19.6, -18.2, RIG.M2, RIG.M3, { thin: true }), top: [25.6, RIG.M3, -19.0] });
  add(24.2, 10.5, -19.8, 26.6, 10.8, -14, 'grating');
  for (const y of [RIG.M1, RIG.M3]) { rail(B, D, true, 24.2, 26.6, -19.75, y); rail(B, D, false, -19.7, -14.05, 26.55, y); rail(B, D, false, y === RIG.M1 ? -16.3 : -18.1, -14.05, 24.25, y); }
  rail(B, D, true, 17.6, 20.0, -19.75, RIG.M2); rail(B, D, false, -19.7, -14.05, 17.65, RIG.M2); rail(B, D, false, -16.3, -14.05, 21.55, RIG.M2);
  for (const [x, z] of [[17.35, -20.05], [26.6, -20.05]]) add(x, 0, z, x + 0.25, 11.9, z + 0.25, 'rigyellow'); // the tower's corner posts
  // the lifeboats off the north edge, in their davits over the sea; the muster point
  for (const x of [20.5, 28]) {
    add(x, 0.7, -28.7, x + 6.2, 2.1, -26.5, 'lifeboat'); add(x + 0.6, 2.1, -28.4, x + 5.6, 3.3, -26.8, 'lifeboat');
    D.add(x + 2.2, 2.4, -26.8, x + 3.2, 2.9, -26.74, 'glass'); D.add(x + 1.6, 1.3, -26.5, x + 4.6, 1.9, -26.44, 'adlifeboat', { fit: 1 });
    for (const k of [0.5, 5.5]) { D.add(x + k, 0, -26.32, x + k + 0.22, 4.2, -26.1, 'rigyellow'); D.add(x + k, 4.0, -27.8, x + k + 0.22, 4.22, -26.1, 'rigyellow'); D.add(x + k + 0.09, 3.3, -27.7, x + k + 0.13, 4.0, -27.66, 'tire'); }
  }
  D.add(30.2, 1.0, -14.06, 33.6, 1.9, -14, 'admuster', { fit: 1 });
  // the helideck: off the roof's east side, its net round the three open sides, the H, lights, a windsock, the chopper
  add(X1, 10.5, -9, 52, 10.8, 9, 'rigsteel'); D.add(34.3, 10.8, -8.7, 51.7, 10.83, 8.7, 'helipad', { fit: 1 });
  add(52, 10.05, -10.5, 53.5, 10.2, 10.5, 'net'); add(X1, 10.05, -10.5, 52, 10.2, -9, 'net'); add(X1, 10.05, 9, 52, 10.2, 10.5, 'net');
  rail(B, D, true, X1 + 0.3, 53.5, -10.45, 10.2); rail(B, D, true, X1 + 0.3, 53.5, 10.45, 10.2); rail(B, D, false, -10.35, 10.35, 53.45, 10.2); // the net's lip (half a metre over the deck: it catches you, mostly)
  for (let x = 35; x < 52; x += 4) for (const z of [-8.9, 8.75]) D.add(x, 10.8, z, x + 0.15, 10.9, z + 0.15, 'neongreen');
  D.add(52.6, 10.2, -10.3, 52.75, 14, -10.15, 'metal'); D.add(52.75, 13.2, -10.35, 54.2, 13.7, -10.1, 'lifeboat');
  if (!o.noChopper) chopper(B, D, 45.5, RIG.M3 + 0.03, 0.5, 'toyred'); // (on the H)
  D.add(34, 8.1, -9, 46, 10.5, 9, 'truss'); D.add(34, 5, -9, 40, 8.1, 9, 'truss'); // the cantilever under it
  D.add(X1 + 0.02, 9.6, -3.5, X1 + 0.08, 10.4, 3.5, 'adhelideck', { fit: 1 });
}
// the drilling side (round x -34..-14, z -10..10): the drill floor (7.2) on its red substructure, the derrick on it (30 m of
// lattice, the monkey board half way up, the crown on top, the racked pipe), the doghouse, the drawworks; under it the
// blowout preventer down through the deck to the cellar deck, the mud pumps and tanks; the V-door ramp up from the pipe
// deck (east), a stair up each of the south and north sides
function drillSide(B0, D0, dx, dz, st, o = {}) {
  const { B, D, add, up } = isPiece(B0, D0, dx, dz, st);
  const X0 = -34, X1 = -14, Z0 = -10, Z1 = 10, y = RIG.M2;
  add(X0, y - 0.4, Z0, X1, y, Z1, 'deckplate');
  for (const x of [X0, -24.5, X1 - 1]) for (const z of [Z0, Z1 - 1]) add(x, 0, z, x + 1, y - 0.4, z + 1, 'rigred'); // the substructure's legs
  for (const z of [Z0 + 0.3, Z1 - 0.7]) D.add(X0 + 1, 3.3, z, X1 - 1, 3.7, z + 0.4, 'rigred'); for (const x of [X0 + 0.3, X1 - 0.7]) D.add(x, 3.3, Z0 + 1, x + 0.4, 3.7, Z1 - 1, 'rigred'); // its girders
  // under the drill floor: the BOP (down through the deck), the mud pumps and tanks
  add(-25.3, 0, -1.3, -22.7, 4.6, 1.3, 'bop'); add(-24.7, 4.6, -0.7, -23.3, y - 0.4, 0.7, 'rigsteel'); add(-24.9, RIG.CD, -0.9, -23.1, -0.5, 0.9, 'bop'); // (the deck plate covers it from -0.5 up)
  for (const s of [-1, 1]) D.add(-25.36, 1.2 + s * 0.6 + 0.6, -1.36, -22.64, 1.6 + s * 0.6 + 0.6, 1.36, 'rigyellow');
  D.add(-22.64, 2.6, -1.0, -22.58, 3.5, 1.0, 'adbop', { fit: 1 });
  add(X0 + 0.2, 0, -8, -31.4, 3.2, 8, 'rigblue'); D.add(-31.4, 1.8, -2, -31.34, 2.8, 2, 'admud', { fit: 1 }); // the mud tanks
  for (const s of [-1, 1]) { add(-22, 0, s * 6.5 - 1, -18, 2.2, s * 6.5 + 1, 'rigred'); D.add(-21.6, 2.2, s * 6.5 - 0.5, -18.4, 2.6, s * 6.5 + 0.5, 'rigsteel'); } // the mud pumps
  // the derrick: four legs stepping in as they go up, X-braced lattice on each face, girts, the crown, a beacon
  const H = 30, segs = 5, b0 = 4, b1 = 1.5, cx = -24, cz = 0;
  // (one Blender model over all of it, the GLUG board too: p_derrick, tools/blender/make_derrick.py. look-only)
  propOf('derrick', [cx + dx, y, cz + dz], 0, () => {
  for (let i = 0; i < segs; i++) {
    const ya = y + (i * H) / segs, yb = y + ((i + 1) * H) / segs, hw = b0 - ((b0 - b1) * i) / segs, leg = i === 0 ? B : D;
    for (const sx of [-1, 1]) for (const sz of [-1, 1]) leg.add(cx + sx * hw - (sx > 0 ? 0.6 : 0), ya, cz + sz * hw - (sz > 0 ? 0.6 : 0), cx + sx * hw + (sx < 0 ? 0.6 : 0), yb, cz + sz * hw + (sz < 0 ? 0.6 : 0), 'rigred');
    const hi = hw - 0.6;
    for (const s of [-1, 1]) { D.add(cx - hi, ya + 0.2, cz + s * (hw - 0.3) - 0.03, cx + hi, yb, cz + s * (hw - 0.3) + 0.03, 'trussred'); D.add(cx + s * (hw - 0.3) - 0.03, ya + 0.2, cz - hi, cx + s * (hw - 0.3) + 0.03, yb, cz + hi, 'trussred'); }
    if (i) for (const s of [-1, 1]) { D.add(cx - hi, ya - 0.1, cz + s * (hw - 0.3) - 0.12, cx + hi, ya + 0.1, cz + s * (hw - 0.3) + 0.12, 'rigred'); D.add(cx + s * (hw - 0.3) - 0.12, ya - 0.1, cz - hi, cx + s * (hw - 0.3) + 0.12, ya + 0.1, cz + hi, 'rigred'); }
  }
  D.add(cx - 2.2, y + H, cz - 2.2, cx + 2.2, y + H + 1.4, cz + 2.2, 'rigred'); D.add(cx - 0.3, y + H + 1.4, cz - 0.3, cx + 0.3, y + H + 2.0, cz + 0.3, 'neonred'); // the crown, its beacon
  D.add(cx - 0.9, y + 14, cz - 0.7, cx + 0.9, y + 16.5, cz + 0.7, 'rigyellow'); D.add(cx - 0.05, y + 16.5, cz - 0.05, cx + 0.05, y + H, cz + 0.05, 'tire'); // the top drive on its line
  for (let k = 0; k < 10; k++) D.add(cx - 2.0 + (k % 5) * 0.3, y, cz - 1.6 + (k > 4 ? 0.45 : 0), cx - 1.88 + (k % 5) * 0.3, y + 22, cz - 1.48 + (k > 4 ? 0.45 : 0), 'rigsteel'); // racked pipe
  add(cx + 3, y + 15, cz - 1.5, cx + 5, y + 15.3, cz + 1.5, 'grating'); // the monkey board, off the east face half way up (grapple up)
  rail(B, D, false, cz - 1.5, cz + 1.5, cx + 4.95, y + 15.3); for (const s of [-1, 1]) rail(B, D, true, cx + 3, cx + 4.9, cz + s * 1.45, y + 15.3);
  D.add(cx + 3.52, y + 9, cz - 2.8, cx + 3.58, y + 12, cz + 2.8, 'adglug', { fit: 1 });
  });
  D.add(cx - 1, y, cz - 1, cx + 1, y + 0.05, cz + 1, 'rigsteel'); // the rotary table
  add(-31.4, y, -2, -28.8, y + 1.6, 2, 'rigred'); D.add(-31.2, y + 1.6, -1.6, -29, y + 2.0, 1.6, 'tire'); // the drawworks and its drum
  // the doghouse (the driller's cabin), south-east corner
  add(-18.5, y, 5.6, -14.3, y + 2.8, 9.7, 'rigblue'); D.add(-18.56, y + 1.2, 6.2, -18.5, y + 2.2, 9.1, 'glass'); D.add(-17.8, y + 2.8, 6.2, -15, y + 3.0, 9.1, 'rigsteel');
  // the ways up: the V-door ramp from the pipe deck (east), the south and north stairs; rails round the edge
  up(rigStair(B, D, true, -4, X1, -1.4, 1.4, 0, y, { mat: 'deckplate' }));
  up(rigStair(B, D, false, 18, Z1, -31, -29.6, 0, y));
  up(rigStair(B, D, false, -18, Z0, -17, -15.6, 0, y));
  railBox(B, D, X0, Z0, X1, Z1, y, { s: [[-31.15, -29.45]], n: [[-17.15, -15.45]], e: [[-1.55, 1.55]] });
}
// a pedestal crane at (x, z): the yellow pedestal (9 m), the slewing deck and cab, the boom along +x (alongX) or +z out to
// len, at the height of the cab's roof (walkable: grapple up and stroll out on it), a hook on its end
function pedCrane(B, D, x, z, alongX, len, o = {}) {
  const y = 9;
  B.add(x - 1.3, 0, z - 1.3, x + 1.3, y, z + 1.3, 'rigyellow');
  for (let k = 1; k < 9; k++) D.add(x + 1.3, k, z - 0.3, x + 1.36, k + 0.06, z + 0.3, 'rigsteel'); // the ladder's rungs
  B.add(x - 2.2, y, z - 2.2, x + 2.2, y + 0.3, z + 2.2, 'grating');
  const P = rigP(alongX, B), Q = rigP(alongX, D), a = alongX ? x : z, c = alongX ? z : x;
  P(a - 1.6, y + 0.3, c - 1.1, a + 0.4, y + 2.6, c + 1.1, 'rigwhite'); Q(a + 0.4, y + 1.3, c - 0.9, a + 0.46, y + 2.3, c + 0.9, 'glass'); // the cab (it turns with its boom)
  P(a - 2.2, y + 0.3, c - 1.9, a - 1.6, y + 1.6, c + 1.9, 'concrete'); // the counterweight
  P(a + 0.4, y + 1.4, c - 0.7, a + len, y + 2.6, c + 0.7, 'truss'); // the boom
  Q(a + len - 0.06, y - 2.5, c - 0.03, a + len - 0.0, y + 1.4, c + 0.03, 'tire'); Q(a + len - 0.4, y - 3.4, c - 0.35, a + len + 0.3, y - 2.5, c + 0.35, 'rigred'); // the hook
  if (o.rest) B.add(o.rest[0] - 0.4, o.rest[1], o.rest[2] - 0.4, o.rest[0] + 0.4, y + 1.4, o.rest[2] + 0.4, 'rigyellow'); // its rest
}
// a christmas tree (the wellhead's valve stack, real name) dressed for christmas: valve blocks, wing valves, handwheels,
// baubles, tinsel, a star on top. on a deck at y
// (each one a Blender prop, p_xmastree: tools/blender/make_xmastree.py, look-only)
function xmasTree(B, D, x, z, y, r) { propOf('xmastree', [x, y, z], 0, () => {
  B.add(x - 0.4, y, z - 0.4, x + 0.4, y + 2.3, z + 0.4, 'rigred');
  B.add(x - 1.0, y + 1.0, z - 0.25, x + 1.0, y + 1.5, z + 0.25, 'rigred');
  for (const s of [-1, 1]) D.add(x + s * 1.0 - (s > 0 ? 0 : 0.08), y + 0.85, z - 0.4, x + s * 1.0 + (s > 0 ? 0.08 : 0), y + 1.65, z + 0.4, 'rigyellow');
  D.add(x - 0.45, y + 2.3, z - 0.45, x + 0.45, y + 2.45, z + 0.45, 'rigyellow'); D.add(x - 0.18, y + 2.45, z - 0.18, x + 0.18, y + 2.8, z + 0.18, 'neonyellow'); // the star
  for (let k = 0; k < 6; k++) { const a = r() * Math.PI * 2, h = 0.3 + r() * 1.9; D.box(x + Math.cos(a) * 0.46, y + h, z + Math.max(-0.38, Math.min(0.38, Math.sin(a) * 0.46)), 0.14, 0.14, 0.14, ['toypink', 'toyteal', 'toyyellow'][k % 3]); } // (within the cap's width: every tree the same outline)
  D.add(x - 0.42, y + 1.7, z - 0.42, x + 0.42, y + 1.76, z + 0.42, 'neongreen'); D.add(x - 0.43, y + 0.6, z - 0.43, x + 0.43, y + 0.66, z + 0.43, 'neonpink'); // tinsel
}); }
// THE SNACK RUN, a supply boat moored along the rig's south side: its open cargo deck (-12: containers, pipe, snacks),
// bulwarks, the bridge forward (east), the boat landing on the jacket beside it and the stair up to the cellar deck
function snackRun(B0, D0, dx, dz, st, r) {
  const { B, D, add, up } = isPiece(B0, D0, dx, dz, st), y = RIG.BOAT;
  add(-12, y - 0.4, 24, 8, y, 31, 'grating'); // the boat landing
  for (const x of [-11, -3, 5]) D.add(x, y - 2.4, 24.2, x + 0.6, y - 0.4, 24.8, 'rigyellow');
  up(rigStair(B, D, false, 29.5, 24, -8.4, -7, y, RIG.CD));
  rail(B, D, false, 24.1, 31, -11.95, y); rail(B, D, false, 24.1, 31, 7.95, y); rail(B, D, true, -11.9, 7.9, 24.05, y, [[-8.5, -6.9]]);
  // the hull, its deck, the bulwarks (open along the landing), the bow
  add(-24, y - 4, 31, 14, y - 0.4, 43.5, 'rigred'); add(-24, y - 0.4, 31, 14, y, 43.5, 'deckplate');
  add(14, y - 4, 31.8, 20, y, 42.7, 'rigred'); add(20, y - 4, 33.5, 23, y, 41, 'rigred'); add(23, y - 3, 35.5, 25, y, 39, 'rigred');
  // (the cargo deck's crash barriers: 2.2 m, like a real supply boat's. they keep you on board as well as the cargo)
  add(-24, y, 31, -12, y + 2.2, 31.3, 'rigred'); add(8, y, 31, 14, y + 2.2, 31.3, 'rigred'); add(-24, y, 43.2, 14, y + 2.2, 43.5, 'rigred'); add(-24, y, 31.3, -23.7, y + 2.2, 43.2, 'rigred');
  for (let x = -22; x < 13; x += 3) for (const z of [31.3, 43.14]) D.add(x, y + 0.2, z, x + 0.12, y + 2.2, z + 0.06, 'rigsteel'); // their stiffeners
  D.add(-24, y - 2.6, 30.94, 14, y - 2.2, 31, 'rigwhite'); D.add(-24, y - 2.6, 43.5, 14, y - 2.2, 43.56, 'rigwhite'); // its stripe
  for (const [x0, x1] of [[-10, -2], [2, 10]]) D.add(x0, y - 0.6, 30.95, x1, y - 0.2, 31.0, 'tire'); // fenders
  // the bridge (forward): three decks of white, the wheelhouse on top (its windows), the name, mast and radar
  add(14, y, 31.8, 20, y + 7.2, 42.7, 'rigwhite'); add(14.5, y + 7.2, 32.6, 19.5, y + 9.4, 41.9, 'rigwhite');
  D.add(19.5, y + 8.0, 33.2, 19.56, y + 9.0, 41.3, 'glass'); D.add(14.44, y + 8.0, 33.2, 14.5, y + 9.0, 41.3, 'glass');
  D.add(13.94, y + 4.2, 33.2, 14, y + 6.4, 41.3, 'adsnack', { fit: 1 }); D.add(-6, y - 3.4, 43.56, 8, y - 2.7, 43.62, 'adsnack', { fit: 1 });
  D.add(16.8, y + 9.4, 37, 17.2, y + 13.5, 37.4, 'metal'); D.add(15.8, y + 12.2, 36.9, 18.2, y + 12.4, 37.5, 'metal'); D.add(16.9, y + 13.5, 37.1, 17.1, y + 13.8, 37.3, 'neonred');
  // the cargo: two containers, the snacks, pipe, crates (a step up onto the containers)
  for (const [x0, z0, m] of [[-21, 37.5, 'containerb'], [-8, 37.5, 'containerg']]) add(x0, y, z0, x0 + 12, y + 2.6, z0 + 2.5, m);
  add(-21, y + 2.6, 37.5, -9, y + 5.2, 40, 'containerr');
  add(5, y, 34, 7.5, y + 2.6, 42, 'pink'); D.add(4.94, y + 0.7, 35.5, 5, y + 1.9, 40.5, 'adsnacks', { fit: 1 }); D.add(7.5, y + 0.7, 35.5, 7.56, y + 1.9, 40.5, 'adsnacks', { fit: 1 });
  for (const [x, z] of [[-9.5, 41.2], [-22, 41.8], [10, 34.5]]) B.box(x, y + 0.6, z, 1.2, 1.2, 1.2, 'crate');
  for (let k = 0; k < 3; k++) add(-20 + k * 0.01, y + k * 0.5, 34 + k * 0.4, -10, y + 0.5 + k * 0.5, 35.8 - k * 0.4, 'pipe'); // a bundle of pipe
  // its mooring lines to the jacket
  D.add(-24, y + 0.6, 30.7, -20, y + 0.7, 30.9, 'tire'); D.add(18, y + 0.6, 31.4, 21, y + 0.7, 31.6, 'tire');
}
// the compressor house (x -2..14, z -24..-15, moved dz): blue steel walls, a roller door on its south side and a door on its
// west, the two compressors inside, louvres, its sign; the crane's boom rests on its roof (5)
function compressorHouse(B0, D0, dz) {
  const { B, D, add, W } = isPiece(B0, D0, 0, dz, []), X0 = -2, X1 = 14, Z0 = -24, Z1 = -15, h = 5, t = 0.3;
  wall(W, 'x', Z1 - t / 2, X0, X1, 0, h - 0.3, t, 'rigblue', [{ a: 4, b: 8, y0: 0, y1: 3.2 }]);
  wall(W, 'x', Z0 + t / 2, X0, X1, 0, h - 0.3, t, 'rigblue');
  wall(W, 'z', X0 + t / 2, Z0 + t, Z1 - t, 0, h - 0.3, t, 'rigblue', [{ a: -21, b: -18, y0: 0, y1: 2.6 }]);
  wall(W, 'z', X1 - t / 2, Z0 + t, Z1 - t, 0, h - 0.3, t, 'rigblue');
  add(X0, h - 0.3, Z0, X1, h, Z1, 'rigsteel');
  for (const x0 of [0, 8.5]) { add(x0, 0, -22, x0 + 4, 2.4, -17.6, 'rigyellow'); D.add(x0 + 0.4, 2.4, -21.6, x0 + 3.6, 2.9, -18, 'rigsteel'); D.add(x0 + 1.6, 2.9, -20.2, x0 + 2.4, 4.7, -19.4, 'pipe'); } // the compressors
  for (const x of [-1, 9.5, 12.5]) D.add(x, 2.2, Z1, x + 1.2, 3.8, Z1 + 0.06, 'grid'); // louvres
  D.add(8.6, 3.4, Z1 + 0.06, 13.6, 4.4, Z1 + 0.12, 'adcompress', { fit: 1 });
}
// the jacket: legs from the cellar deck down into the sea (spreading as they go), braces, X-bracing on the outside faces,
// foam round the legs at the waterline. xs / zs: the legs' lines. render-only
function jacket(D, xs, zs, top = RIG.CD - 0.4) {
  const segs = [[top, -24, 0], [-24, -40, 0.8], [-40, -62, 1.6]], ox = (x, k) => (x < 0 ? -k : x > 0 ? k : 0);
  for (const x of xs) for (const z of zs) {
    for (const [y0, y1, k] of segs) D.add(x + ox(x, k) - 1.2, y1, z + ox(z, k) - 1.2, x + ox(x, k) + 1.2, y0, z + ox(z, k) + 1.2, 'rigyellow');
    D.add(x - 1.7, RIG.SEA, z - 1.7, x + 1.7, RIG.SEA + 0.03, z + 1.7, 'foam');
  }
  const [xa, xb] = [xs[0], xs[xs.length - 1]], [za, zb] = [zs[0], zs[zs.length - 1]];
  for (const y of [-15.6, -30, -48]) {
    for (const z of zs) D.add(xa + 1.2, y, z - 0.35, xb - 1.2, y + 0.7, z + 0.35, 'rigyellow');
    for (const x of xs) D.add(x - 0.35, y, za + 1.2, x + 0.35, y + 0.7, zb - 1.2, 'rigyellow');
  }
  for (const z of [za, zb]) D.add(xa + 1.3, -46, z - 0.04, xb - 1.3, top, z + 0.04, 'truss');
  for (const x of [xa, xb]) D.add(x - 0.04, -46, za + 1.3, x + 0.04, top, zb - 1.3, 'truss');
}
// another rig out on the horizon (render-only): legs, a deck, a derrick, its flare
function farRig(D, x, z, s = 1) {
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) D.box(x + sx * 14 * s, RIG.SEA - 10, z + sz * 12 * s, 3 * s, 60, 3 * s, 'rigyellow');
  D.add(x - 22 * s, 18, z - 18 * s, x + 22 * s, 21, z + 18 * s, 'rigsteel'); D.add(x + 4 * s, 21, z - 10 * s, x + 18 * s, 33, z + 8 * s, 'rigwhite');
  D.add(x - 14 * s, 21, z - 4 * s, x - 8 * s, 60, z + 2 * s, 'trussred'); D.add(x - 20 * s, 40, z + 14 * s, x - 18 * s, 44, z + 16 * s, 'flame');
}

// ------------------------------------------------------------ PLATFORM: GLUG OIL's rig in the North Sea. one big platform:
// the living quarters and the helideck (east), the drill floor under the derrick (west), the process deck between (the
// pipe rack, two separators, the compressor house), the laydown deck with containers (south), the cellar deck under it all
// (the christmas trees round the wellbay), the flare boom out west, a crane on its boom rest, THE SNACK RUN tied up below
// a slick of crude on the sea off the rig (render only): a few overlapping patches, black with a rainbow on it
function oilSlick(D, x, z) {
  for (const [a, b, c, d] of [[-14, -10, 6, 2], [-6, -2, 16, 12], [2, -16, 14, -6], [-20, -2, -8, 8], [8, 6, 22, 16]]) D.add(x + a, RIG.SEA, z + b, x + c, RIG.SEA + 0.05, z + d, 'oil');
}
function platform() {
  const B = builder(), D = builder(), r = rng(7777), add = B.add, st = [];
  // ---- the sea, the far rigs, a tanker going by
  D.add(-420, RIG.SEA - 0.1, -420, 420, RIG.SEA, 420, 'seanorth');
  oilSlick(D, 24, 32);
  farRig(D, -420, -300); farRig(D, 520, 220, 0.8); farRig(D, -160, 540, 1.1);
  D.add(250, RIG.SEA - 2, -230, 405, RIG.SEA + 8, -200, 'rigred'); D.add(370, RIG.SEA + 8, -226, 400, RIG.SEA + 22, -204, 'rigwhite'); D.add(385, RIG.SEA + 22, -218, 388, RIG.SEA + 32, -214, 'metal');

  // ---- the main deck (0): holes for the three stairs down, rails round its edge (open where the flare boom goes off)
  const holes = [[15.1, -21.2, 16.9, -13], [-12.2, 13, -10.4, 21.2], [5.4, 13, 7.2, 21.2]];
  groundHoles(B, -36, -26, 36, 26, -0.5, 0, 'deckplate', holes);
  railBox(B, D, -36, -26, 36, 26, 0, { w: [[21.2, 22.8]] });
  railBox(B, D, 14.95, -21.25, 17.05, -13, 0, { s: [[14.9, 17.1]] }); railBox(B, D, -12.25, 13, -10.35, 21.25, 0, { n: [[-12.3, -10.3]] }); railBox(B, D, 5.35, 13, 7.25, 21.25, 0, { n: [[5.3, 7.3]] });
  for (let x = -30; x <= 30; x += 12) for (const z of [-18, -6, 6, 18]) D.add(x - 0.4, -0.6, z - 0.15, x + 0.4, -0.5, z + 0.15, 'lamp'); // lights under it, over the cellar deck

  // ---- the cellar deck (-7.2): open grating, the wellbay slot (railed: the sea's down there), the christmas trees, the
  // pig launcher, pumps, the jacket's columns up to the main deck
  groundHoles(B, -34, -24, 34, 24, RIG.CD - 0.4, RIG.CD, 'grating', [[-6, -1, 6, 1]]);
  railBox(B, D, -34, -24, 34, 24, RIG.CD, { s: [[-8.5, -6.9]] });
  railBox(B, D, -6.1, -1.1, 6.1, 1.1, RIG.CD);
  D.add(-2, RIG.CD + 0.6, -1.16, 2, RIG.CD + 0.95, -1.1, 'addeep', { fit: 1 }); D.add(-2, RIG.CD + 0.6, 1.1, 2, RIG.CD + 0.95, 1.16, 'addeep', { fit: 1 });
  for (const x of [-5, -3, -1, 1, 3, 5]) D.add(x - 0.25, -34, -0.25, x + 0.25, RIG.CD - 0.4, 0.25, 'rigsteel'); // the conductors, down to the seabed
  for (const x of [-4.5, 0, 4.5]) for (const z of [-2.7, 2.7]) xmasTree(B, D, x, z, RIG.CD, r);
  D.add(8, RIG.CD, -0.3, 8.1, RIG.CD + 1.8, 0.3, 'metal'); D.add(8.1, RIG.CD + 1.0, -1.6, 8.16, RIG.CD + 1.8, 1.6, 'adxmas', { fit: 1 });
  add(8, RIG.CD, -16, 18, RIG.CD + 1.0, -15, 'rigsteel'); D.add(18, RIG.CD + 0.05, -16.1, 18.15, RIG.CD + 0.95, -14.9, 'rigyellow'); D.add(12, RIG.CD + 1.2, -15.04, 15.5, RIG.CD + 1.9, -14.98, 'adpig', { fit: 1 }); D.add(12.5, RIG.CD + 1.0, -15.1, 12.6, RIG.CD + 1.2, -15.0, 'metal'); D.add(15, RIG.CD + 1.0, -15.1, 15.1, RIG.CD + 1.2, -15.0, 'metal');
  add(-22, RIG.CD, -18, -18, RIG.CD + 1.6, -15.5, 'rigblue'); add(18, RIG.CD, 15.5, 22, RIG.CD + 1.6, 18, 'rigblue'); add(-26, RIG.CD, 10, -23, RIG.CD + 2.2, 13, 'rigblue'); // pumps
  for (const x of [-30, 0, 30]) for (const z of [-20, 20]) add(x - 0.8, RIG.CD, z - 0.8, x + 0.8, -0.5, z + 0.8, 'rigyellow'); // the columns
  jacket(D, [-30, 0, 30], [-20, 20]);

  // ---- the stairs down to the cellar deck (north-east, south-west, south middle)
  st.push(rigStair(B, D, false, -21, -13, 15.3, 16.7, RIG.CD, 0));
  st.push(rigStair(B, D, false, 21, 13, -12, -10.6, RIG.CD, 0));
  st.push(rigStair(B, D, false, 21, 13, 5.6, 7.0, RIG.CD, 0));

  // ---- the drilling side (west), the living quarters and helideck (east)
  drillSide(B, D, 0, 0, st);
  livingQuarters(B, D, 0, 0, st);

  // ---- the process deck: the pipe rack (its walkway joins the LQ's 1st floor), the separators, the compressor house
  pipeRack(B, D, -2, 18, 0, [4, 5.6]);
  st.push(rigStair(B, D, false, 6.5, 1.7, 4.0, 5.6, 0, RIG.M1)); add(4.0, RIG.M1 - 0.3, 1.1, 5.6, RIG.M1, 1.7, 'grating');
  rail(B, D, false, -1.1, 1.1, -1.95, RIG.M1);
  separator(B, D, 0, 14, -10); separator(B, D, 0, 14, 10);
  compressorHouse(B, D, 0);

  // ---- the cranes: north-west on its boom rest on the compressor house (grapple up to the cab, walk out on the boom),
  // south-east swung out over the boat
  pedCrane(B, D, -28, -20, true, 34, { rest: [4, 5, -20] });
  pedCrane(B, D, 13, 21, false, 22);

  // ---- the laydown deck (south): containers (a crate up onto them), cargo baskets, gas bottles
  add(-8, 0, 15.5, 4, 2.6, 18, 'containerr'); add(-8, 2.6, 15.5, 4, 5.2, 18, 'containerb'); add(-8, 0, 20.5, 4, 2.6, 23, 'containerg');
  B.box(-9.4, 0.6, 19.2, 1.2, 1.2, 1.2, 'crate'); B.box(-6, 3.2, 21.7, 1.2, 1.2, 1.2, 'crate');
  for (const [x, z] of [[8.5, 15.0], [8.5, 18.6]]) { add(x, 0, z, x + 2.6, 0.9, z + 2, 'rigred'); D.add(x + 0.3, 0.9, z + 0.3, x + 1.2, 1.4, z + 1.7, 'pipe'); }
  add(-1, 0, 24.2, 3, 0.4, 25.6, 'rigyellow'); for (let x = -0.7; x < 2.8; x += 0.5) D.add(x, 0.4, 24.5, x + 0.36, 1.9, 24.86, 'toygreen');
  // the pipe deck (between the drill floor and the rack): drill pipe stacked either side of the V-door ramp
  for (const z0 of [-7.5, 4]) { add(-12.5, 0, z0, -5, 0.5, z0 + 3.5, 'pipe'); add(-12, 0.5, z0 + 0.3, -5.5, 0.95, z0 + 3.2, 'pipe'); }

  // ---- the flare boom (out west from the south-west corner): a catwalk up to the tip, the flare on fire
  rigStair(B, D, true, -36, -62, 21.3, 22.7, 0, 11.7, { thin: true }); // (not on the bots' map: the tip isn't one of their floors)
  for (let k = 0; k < 4; k++) D.add(-36 - 6.5 * (k + 1), 2.925 * k - 1.8, 21.4, -36 - 6.5 * k, 2.925 * k - 0.35, 22.6, 'truss');
  add(-66, 11.4, 20, -62, 11.7, 24, 'grating');
  rail(B, D, true, -66, -62, 20.05, 11.7); rail(B, D, true, -66, -62, 23.95, 11.7); rail(B, D, false, 20.1, 23.9, -65.95, 11.7);
  rail(B, D, false, 20.1, 21.25, -62.05, 11.7); rail(B, D, false, 22.75, 23.9, -62.05, 11.7);
  add(-65, 11.7, 21.5, -64, 15.5, 22.5, 'rigred');
  D.add(-65.6, 15.5, 21, -63.4, 17.8, 23, 'flame'); D.add(-65.1, 17.8, 21.5, -63.9, 20.2, 22.5, 'flame'); D.add(-64.75, 20.2, 21.85, -64.25, 21.6, 22.15, 'flame');
  D.add(-66, 16, 21.6, -65.6, 17.2, 22.4, 'flame'); D.add(-63.4, 16.4, 21.4, -63, 17.4, 22, 'flame');
  D.add(-65.5, 12.2, 24.0, -62.5, 12.6, 24.06, 'adflare', { fit: 1 });

  // ---- THE SNACK RUN alongside (south), the boat landing and its stair
  snackRun(B, D, 0, 0, st, r);

  // ---- spawns: the galley vs under the drill floor (TDM); everywhere for the rest
  const att = [[21, 0.25, -6], [21, 0.25, 6], [25, 0.25, -11.5], [25, 0.25, 11.5], [29.5, 0.25, -6.5], [29.5, 0.25, 6.5], [25, 0.25, 0]];
  const def = [[-30, 0.1, -5], [-30, 0.1, 5], [-27, 0.1, -7.5], [-27, 0.1, 7.5], [-20, 0.1, -3], [-20, 0.1, 3], [-16.5, 0.1, 0]];
  const spawns = [...att.slice(0, 3), ...def.slice(0, 3), [-20, RIG.CD + 0.1, -12], [20, RIG.CD + 0.1, 12], [-22, RIG.CD + 0.1, 12], [12, RIG.CD + 0.1, -8],
    [-8, 0.1, -20], [8, 0.1, 5], [-10, 0.1, 12], [26, 0.1, -23], [-4, 0.1, 19], [-29, RIG.M2 + 0.1, -7], [-18, RIG.M2 + 0.1, 2], [24, RIG.M1 + 0.1, 4],
    [23, RIG.M2 + 0.1, -6], [40, RIG.M3 + 0.1, -6], [-15, RIG.BOAT + 0.1, 32.5], [10, RIG.BOAT + 0.1, 41]];
  let graph = null;
  return { name: 'Platform', size: 'medium', boxes: B.boxes, deco: D.boxes, killY: -16.2, seaY: -14, floorY: -15.5, // (killY: head under the sea)
    sky: { top: 0x4a5a78, mid: 0xb4c2d0, bot: 0x2c3846, fog: 0xb4c2d0 }, fogNear: 90, fogFar: 360,
    spawns, teamSpawns: { att, def }, edgeGuard: true, sea: true,
    peekGraph() { return graph; }, dropGraph() { graph = null; }, get graph() { return graph || (graph = buildNav(B.boxes, { x0: -67, z0: -45, n: 122, cell: 1, levels: [RIG.BOAT, RIG.CD, 0, RIG.M1, RIG.M2, RIG.M3], band: 0.6, stairs: st })); },
  };
}

// a bridge along z (z0..z1) at deck level y, x0..x1 wide: grating, a bundle of pipe down each side (cover up to the
// waist), rails on them, a lattice frame and roof, junction boxes now and then (cover down its length), legs into the sea
function trussBridge(B, D, x0, x1, z0, z1, y) {
  B.add(x0, y - 0.4, z0, x1, y, z1, 'grating');
  B.add(x0, y, z0, x0 + 0.7, y + 0.8, z1, 'pipe'); B.add(x1 - 0.7, y, z0, x1, y + 0.8, z1, 'pipe');
  rail(B, D, false, z0, z1, x0 + 0.15, y + 0.8); rail(B, D, false, z0, z1, x1 - 0.15, y + 0.8);
  D.add(x0, y + 0.8, z0, x0 + 0.06, y + 3.2, z1, 'truss'); D.add(x1 - 0.06, y + 0.8, z0, x1, y + 3.2, z1, 'truss'); D.add(x0, y + 3.2, z0, x1, y + 3.3, z1, 'truss');
  for (let z = z0 + 4, k = 0; z < z1 - 3; z += 8, k++) B.box(k % 2 ? x1 - 1.25 : x0 + 1.25, y + 0.55, z, 0.9, 1.1, 1.2, 'rigblue');
  for (let z = z0 + 6; z < z1 - 4; z += 12) D.add(x0 + 0.6, -40, z - 0.8, x1 - 0.6, y - 0.4, z + 0.8, 'truss');
}
// a pipe bridge along z (z0..z1) at y: grating between two big pipes (cover), rails on them, a lattice under it, valve
// boxes now and then, legs into the sea
function pipeBridge(B, D, x0, x1, z0, z1, y) {
  B.add(x0, y - 0.4, z0, x1, y, z1, 'grating');
  B.add(x0, y, z0, x0 + 0.9, y + 1.0, z1, 'pipe'); B.add(x1 - 0.9, y, z0, x1, y + 1.0, z1, 'rigyellow');
  rail(B, D, false, z0, z1, x0 + 0.15, y + 1.0); rail(B, D, false, z0, z1, x1 - 0.15, y + 1.0);
  D.add(x0 + 0.3, y - 2.6, z0, x1 - 0.3, y - 0.4, z1, 'truss');
  for (let z = z0 + 7; z < z1 - 4; z += 12) D.add(x0 + 0.6, -40, z - 0.8, x1 - 0.6, y - 2.6, z + 0.8, 'truss');
  for (let z = z0 + 5, k = 0; z < z1 - 3; z += 9, k++) B.box(k % 2 ? x1 - 1.4 : x0 + 1.4, y + 0.6, z, 1.0, 1.2, 1.0, 'rigred');
}

// ------------------------------------------------------------ PLATFORM S&D: the Snack Attack (Plant & Defuse). GLUG OIL's
// crew (defenders) hold the rig (north) from its living quarters; SLURP OIL's raiders (attackers) came over on THE SNACK RUN
// to the riser platform (south). between them the bridge support platform; the west bridge at deck level and the east pipe
// bridge a deck lower join all three, and THE TOAD (a personnel basket on a spring: very safe) flings you from the middle
// onto the rig's laydown deck. A is the drill floor up under the derrick (west), B the wellbay in the cellar deck among the
// christmas trees (east). the rig's modules stand between the spawns
function platformSD() {
  const B = builder(), D = builder(), r = rng(7878), add = B.add, st = [], dz = -44, CD = RIG.CD;
  D.add(-420, RIG.SEA - 0.1, -420, 420, RIG.SEA, 420, 'seanorth');
  oilSlick(D, 24, 32);
  farRig(D, -420, -300); farRig(D, 520, 220, 0.8); farRig(D, -300, 460, 1.1);

  // ---- the rig (north, x -36..36, z -70..-22): the main deck (holes for the stairs down), its cellar deck (the wellbay)
  groundHoles(B, -36, -70, 36, -22, -0.5, 0, 'deckplate', [[15.1, -65.2, 16.9, -57], [-12.2, -35.2, -10.4, -27]]);
  railBox(B, D, -36, -70, 36, -22, 0, { s: [[-20.1, -15.9]] });
  railBox(B, D, 14.95, -65.25, 17.05, -57, 0, { s: [[14.9, 17.1]] }); railBox(B, D, -12.25, -35.25, -10.35, -27, 0, { s: [[-12.3, -10.3]] });
  for (let x = -30; x <= 30; x += 12) for (const z of [-62, -50, -38, -28]) D.add(x - 0.4, -0.6, z - 0.15, x + 0.4, -0.5, z + 0.15, 'lamp');
  groundHoles(B, -34, -68, 34, -24, CD - 0.4, CD, 'grating', [[4, -51, 16, -50]]);
  railBox(B, D, -34, -68, 34, -24, CD, { s: [[13.9, 18.1]] });
  railBox(B, D, 3.9, -51.1, 16.1, -49.9, CD);
  D.add(8, CD + 0.6, -51.16, 12, CD + 0.95, -51.1, 'addeep', { fit: 1 }); D.add(8, CD + 0.6, -49.9, 12, CD + 0.95, -49.84, 'addeep', { fit: 1 });
  for (const x of [5, 7, 9, 11, 13, 15]) D.add(x - 0.25, -34, -50.75, x + 0.25, CD - 0.4, -50.25, 'rigsteel');
  for (const x of [5, 10, 15]) for (const z of [-52.7, -48.3]) xmasTree(B, D, x, z, CD, r);
  D.add(1, CD, -50.3, 1.1, CD + 1.8, -49.7, 'metal'); D.add(1.1, CD + 1.0, -51.6, 1.16, CD + 1.8, -48.4, 'adxmas', { fit: 1 });
  for (const [x, z] of [[3.5, -42.5], [15.5, -40.8], [16.3, -41.9]]) B.box(x, CD + 0.6, z, 1.2, 1.2, 1.2, 'crate'); B.box(6.5, CD + 0.8, -44.2, 1.6, 1.6, 1.6, 'wood'); // B's cover
  add(19, CD, -45, 22.5, CD + 1.6, -42.5, 'rigblue'); add(-22, CD, -62, -18, CD + 1.6, -59.5, 'rigblue'); add(20, CD, -61, 23, CD + 2.2, -58, 'rigblue'); add(-26, CD, -34, -23, CD + 2.2, -31, 'rigblue'); // pumps
  siteBoard(D, 6, CD + 2.6, -38.92, 'x', 'siteb', 2.8); siteBoard(D, 18.2, CD + 2.6, -47, 'z', 'siteb', 2.4);
  for (const x of [-30, 0, 30]) for (const z of [-66, -26]) add(x - 0.8, CD, z - 0.8, x + 0.8, -0.5, z + 0.8, 'rigyellow');
  jacket(D, [-30, 0, 30], [-66, -26]);
  st.push(rigStair(B, D, false, -65, -57, 15.3, 16.7, CD, 0)); // the crew's way down to B (north)
  st.push(rigStair(B, D, false, -35, -27, -12, -10.6, CD, 0)); // and the raiders' (south-west, off the laydown deck)

  // ---- on the rig: the drilling side (A), the living quarters (the crew's spawn) and helideck, the pipe rack, a
  // separator, the compressor house, the crane on its rest; the laydown deck (south) where the bridge and THE TOAD come in
  drillSide(B, D, 0, dz, st);
  siteBoard(D, -24, RIG.M2 + 1.2, -39.9, 'x', 'sitea', 3); siteBoard(D, -19.9, RIG.M2 + 1.2, -44, 'z', 'sitea', 2.4);
  livingQuarters(B, D, 0, dz, st);
  pipeRack(B, D, -2, 18, dz, [4, 5.6]);
  st.push(rigStair(B, D, false, -37.5, -42.3, 4.0, 5.6, 0, RIG.M1)); add(4.0, RIG.M1 - 0.3, -42.9, 5.6, RIG.M1, -42.3, 'grating');
  rail(B, D, false, -45.1, -42.9, -1.95, RIG.M1);
  separator(B, D, 0, 14, -54);
  compressorHouse(B, D, dz);
  pedCrane(B, D, -28, -64, true, 34, { rest: [4, 5, -64] });
  add(-9, 0, -27.5, -1, 2.6, -25, 'containerr'); B.box(-0.4, 0.6, -24.3, 1.2, 1.2, 1.2, 'crate');
  add(18, 0, -27, 30, 2.6, -24.5, 'containerb'); add(20, 2.6, -27, 26, 5.2, -24.5, 'containerg');
  for (const [x, z] of [[13, -33], [-5, -33.5]]) B.box(x, 0.8, z, 1.6, 1.6, 1.6, 'wood'); // cable drums
  D.add(-30, 0, -56.1, -29.9, 7, -56, 'metal'); D.add(-29.9, 5, -56.1, -27.4, 6.6, -56.04, 'flagglug');

  // ---- the west bridge (deck level, x -20..-16) and the east pipe bridge (the cellar deck's level, x 14..18), each in two
  // spans: the rig to the middle, the middle to the riser platform
  trussBridge(B, D, -20, -16, -22, 0, 0); trussBridge(B, D, -20, -16, 18, 38, 0);
  pipeBridge(B, D, 14, 18, -24, 2, CD); pipeBridge(B, D, 14, 18, 16, 40, CD);

  // ---- the bridge support platform (the middle, x -22..22, z 0..18): a deck at each level, a stair down each side, a
  // junction hut, cable drums, THE TOAD on its north edge
  groundHoles(B, -22, 0, 22, 18, -0.5, 0, 'deckplate', [[-14.2, 5, -12.4, 13.2], [10.2, 5, 12, 13.2]]);
  railBox(B, D, -22, 0, 22, 18, 0, { n: [[-20.1, -15.9]], s: [[-20.1, -15.9]] });
  railBox(B, D, -14.25, 5, -12.35, 13.25, 0, { n: [[-14.3, -12.3]] }); railBox(B, D, 10.15, 5, 12.05, 13.25, 0, { n: [[10.1, 12.1]] });
  add(-20, CD - 0.4, 2, 20, CD, 16, 'grating'); railBox(B, D, -20, 2, 20, 16, CD, { n: [[13.9, 18.1]], s: [[13.9, 18.1]] });
  st.push(rigStair(B, D, false, 13, 5, -14, -12.6, CD, 0)); st.push(rigStair(B, D, false, 13, 5, 10.4, 11.8, CD, 0));
  for (const x of [-20, 0, 20]) for (const z of [3, 15]) add(x - 0.8, CD, z - 0.8, x + 0.8, -0.5, z + 0.8, 'rigyellow');
  jacket(D, [-20, 0, 20], [3, 15]);
  add(-6, 0, 7, 2, 3, 12, 'rigblue'); D.add(-6, 3, 7, 2, 3.25, 12, 'rigsteel'); D.add(-3, 1.2, 6.94, -0.6, 2.4, 7, 'adtoad', { fit: 1 }); // the junction hut
  B.box(8, 0.8, 4.2, 1.6, 1.6, 1.6, 'wood'); B.box(-10, 0.8, 15.6, 1.6, 1.6, 1.6, 'wood'); B.box(4, 0.6, 15.8, 1.2, 1.2, 1.2, 'crate');
  add(4, 0, 0.6, 8, 0.15, 2.6, 'pad', { pad: [0, 20.5, -19.5] }); // THE TOAD: over the gap onto the laydown deck
  for (const [x0, z0, x1, z1] of [[3.8, 0.4, 8.2, 0.6], [3.8, 2.6, 8.2, 2.8], [3.8, 0.6, 4, 2.6], [8, 0.6, 8.2, 2.6]]) D.add(x0, 0, z0, x1, 0.5, z1, 'lifeboat'); // its basket's ring
  D.add(8.6, 0, 2.2, 8.7, 1.6, 2.3, 'metal'); D.add(8.7, 1.0, 1.2, 8.76, 1.6, 3.4, 'adtoad', { fit: 1 });

  // ---- the riser platform (south, x -24..24, z 38..70): the raiders' spawn behind the riser module, a stair down each
  // side to its cellar deck (the east one to the pipe bridge), SLURP OIL's banner, their snacks; THE SNACK RUN alongside
  groundHoles(B, -24, 38, 24, 70, -0.5, 0, 'deckplate', [[-15.6, 42.8, -13.8, 51], [13.8, 42.8, 15.6, 51]]);
  railBox(B, D, -24, 38, 24, 70, 0, { n: [[-20.1, -15.9]] });
  railBox(B, D, -15.65, 42.75, -13.75, 51, 0, { s: [[-15.7, -13.7]] }); railBox(B, D, 13.75, 42.75, 15.65, 51, 0, { s: [[13.7, 15.7]] });
  add(-22, CD - 0.4, 40, 22, CD, 68, 'grating'); railBox(B, D, -22, 40, 22, 68, CD, { n: [[13.9, 18.1]], s: [[-8.5, -6.9]] });
  st.push(rigStair(B, D, false, 43, 51, -15.4, -14, CD, 0)); st.push(rigStair(B, D, false, 43, 51, 14, 15.4, CD, 0));
  for (const x of [-20, 0, 20]) for (const z of [44, 64]) add(x - 0.8, CD, z - 0.8, x + 0.8, -0.5, z + 0.8, 'rigyellow');
  jacket(D, [-20, 0, 20], [44, 64]);
  add(-10, 0, 42, 10, 5.4, 48, 'rigblue'); D.add(-10, 5.4, 42, 10, 5.6, 48, 'rigsteel'); // the riser module
  for (const x of [-8, -4, 0, 4, 8]) D.add(x - 0.3, -40, 41.6, x + 0.3, 4.6, 42, 'pipe'); // its risers, down to the seabed
  D.add(-6, 2.2, 48.0, 6, 5.0, 48.06, 'adslurp', { fit: 1 });
  D.add(-22, 0, 66.9, -21.9, 7, 67, 'metal'); D.add(-21.9, 5, 66.9, -19.4, 6.6, 66.96, 'flagslurp');
  add(-21, 0, 54, -18.5, 2.6, 62, 'pink'); D.add(-18.5, 0.7, 55.5, -18.44, 1.9, 60.5, 'adsnacks', { fit: 1 }); add(18.5, 0, 56, 21, 2.6, 64, 'pink'); D.add(18.44, 0.7, 57.5, 18.5, 1.9, 62.5, 'adsnacks', { fit: 1 });
  for (let x = -20; x <= 20; x += 10) for (const z of [46, 58]) D.add(x - 0.4, -0.6, z - 0.15, x + 0.4, -0.5, z + 0.15, 'lamp');
  snackRun(B, D, 0, 44, st, r);

  // ---- spawns, the ways in (for the bots), the sites
  const att = [[-12, 0.1, 56], [-6, 0.1, 60], [0, 0.1, 57], [6, 0.1, 60], [12, 0.1, 56], [-3, 0.1, 65], [3, 0.1, 65]];
  const def = [[21, 0.25, -50], [21, 0.25, -38], [25, 0.25, -55.5], [25, 0.25, -32.5], [29.5, 0.25, -50.5], [29.5, 0.25, -37.5], [25, 0.25, -44]];
  const spawns = [...att.slice(0, 3), ...def.slice(0, 3), [-10, 0.1, 10], [10, CD + 0.1, 9], [-26, 0.1, -28], [8, CD + 0.1, -32], [-24, RIG.M2 + 0.1, -36]];
  let graph = null;
  return { name: 'Platform', size: 'medium', boxes: B.boxes, deco: D.boxes, killY: -16.2, seaY: -14, floorY: -15.5, // (killY: head under the sea)
    sky: { top: 0x4a5a78, mid: 0xb4c2d0, bot: 0x2c3846, fog: 0xb4c2d0 }, fogNear: 100, fogFar: 380,
    spawns, teamSpawns: { att, def }, edgeGuard: true, sea: true,
    nav: {
      A: [
        [[-6, 60], [-14, 54], [-18, 46], [-18, 36], [-18, 24], [-18, 9], [-18, -6], [-18, -20], [-24, -24], [-30.3, -24.7], [-30.3, -34.7, RIG.M2], [-26, -37, RIG.M2]], // the west bridge, up the drill floor's south stair
        [[0, 60], [-14, 54], [-18, 46], [-18, 24], [-18, 9], [-18, -6], [-18, -20], [-10, -24], [-2.7, -32], [-2.7, -44], [-14.7, -44, RIG.M2], [-18, -40, RIG.M2]], // the west bridge, the pipe deck, the V-door ramp
        [[4, 62], [14.7, 51.7], [14.7, 41.7, CD], [16, 36, CD], [16, 25, CD], [16, 12, CD], [11.1, 14.3, CD], [11.1, 4.3], [-8, 4], [-18, 1], [-18, -12], [-18, -20], [-10, -24], [-2.7, -32], [-2.7, -44], [-14.7, -44, RIG.M2], [-18, -40, RIG.M2]], // the pipe bridge, up through the middle, the west bridge
        [[24, -54], [17, -54], [13.5, -57.3], [0, -57.3], [-8, -58], [-16.3, -63.3], [-16.3, -53.3, RIG.M2], [-20, -50, RIG.M2]], // the crew: out the west door, the drill floor's north stair
      ],
      B: [
        [[6, 60], [12, 54], [14.7, 51.7], [14.7, 41.7, CD], [16, 36, CD], [16, 25, CD], [16, 9, CD], [16, -4, CD], [16, -14.5, CD], [14, -28, CD], [10, -44, CD]], // the pipe bridge all the way
        [[-6, 62], [-14, 54], [-18, 46], [-18, 24], [-18, 9], [-18, -6], [-18, -20], [-14, -24], [-11.3, -26.3], [-11.3, -36.3, CD], [-2, -42, CD], [8, -45, CD]], // the west bridge, down off the laydown deck, along the cellar deck
        [[-2, 62], [-14, 54], [-18, 46], [-18, 30], [-18, 20], [-8, 4], [9, 4.5], [11.1, 4.3], [11.1, 14.3, CD], [16, 12, CD], [16, 2, CD], [16, -4, CD], [16, -14.5, CD], [14, -28, CD], [10, -44, CD]], // the west bridge to the middle, down, the pipe bridge
        [[24, -44], [17, -54], [16, -56.3], [16, -66.3, CD], [18, -58, CD], [18, -50, CD], [12, -46, CD]], // the crew: out the west door, down the north stair
      ],
    },
    sites: [{ id: 'A', min: [-33, RIG.M2, -53], max: [-15, RIG.M2, -35] }, { id: 'B', min: [2, CD, -53], max: [18, CD, -39] }],
    peekGraph() { return graph; }, dropGraph() { graph = null; }, get graph() { return graph || (graph = buildNav(B.boxes, { x0: -40, z0: -72, n: 162, cell: 1, levels: [RIG.BOAT, CD, 0, RIG.M1, RIG.M2, RIG.M3], band: 0.6, stairs: st })); },
  };
}

// ------------------------------------------------------------ the roof kit (Rooftop, Rooftop S&D)
// a tower's top: the body down to the street foundations, a roof slab with a cornice, a 1 m parapet round it with gaps
// where bridges land (gaps: { n, s, w, e }: lists of [a, b] along that side). y = the roof's top
function roofTop(B, x0, z0, x1, z1, y, facade, gaps = {}, base = -152, holes = null) { // (holes: [[x0, z0, x1, z1]] cut out of the slab)
  const W = B.local(0, 0, 0), g = (k) => (gaps[k] || []).map(([a, b]) => ({ a, b, y0: y, y1: y + 1 }));
  B.add(x0, base, z0, x1, y - 0.5, z1, facade);
  if (holes) groundHoles(B, x0 - 0.4, z0 - 0.4, x1 + 0.4, z1 + 0.4, y - 0.5, y, 'concrete', holes); else B.add(x0 - 0.4, y - 0.5, z0 - 0.4, x1 + 0.4, y, z1 + 0.4, 'concrete');
  wall(W, 'x', z0 - 0.2, x0 - 0.4, x1 + 0.4, y, y + 1, 0.4, 'concrete', g('n'));
  wall(W, 'x', z1 + 0.2, x0 - 0.4, x1 + 0.4, y, y + 1, 0.4, 'concrete', g('s'));
  wall(W, 'z', x0 - 0.2, z0, z1, y, y + 1, 0.4, 'concrete', g('w'));
  wall(W, 'z', x1 + 0.2, z0, z1, y, y + 1, 0.4, 'concrete', g('e'));
}
// solid concrete steps over a gap (along x, or z if !alongX) from a0 at height ya to a1 at yb, w wide round the line c,
// steel rails up both sides. nothing under it but 150 m of air
function stairBridge(B, alongX, a0, a1, c, ya, yb, w = 4, thin = false) { // (thin: each step a 0.4 m slab, not solid down to the low end)
  const n = Math.max(1, Math.ceil(Math.abs(yb - ya) / 0.45)), h = Math.abs(yb - ya) / n, y0 = Math.min(ya, yb), run = (a1 - a0) / n;
  const P = (p0, q0, p1, q1, yA, yB, m) => (alongX ? B.add(p0, yA, q0, p1, yB, q1, m) : B.add(q0, yA, p0, q1, yB, p1, m));
  for (let i = 1; i <= n; i++) { // step i counted from the low end
    const lowA = ya < yb, s0 = lowA ? a0 + (i - 1) * run : a1 - (i - 1) * run, s1 = lowA ? a0 + i * run : a1 - i * run, top = y0 + i * h;
    P(s0, c - w / 2, s1, c + w / 2, thin ? Math.max(y0, top - 0.4) : y0, top, 'concrete');
    P(s0, c - w / 2, s1, c - w / 2 + 0.1, top, top + 1, 'metal'); P(s0, c + w / 2 - 0.1, s1, c + w / 2, top, top + 1, 'metal');
  }
}
// a flat steel bridge (grid deck, rails with neon along them, lamps underneath) from a0 to a1 along x (or z) at height
// y round the line c. gaps: { '-1': [[a, b]], '1': [...] }, stretches of rail left open on that side
function skyBridge(B, D, alongX, a0, a1, c, y, w = 4, gaps = {}, neon = ['neoncyan', 'neonpink']) {
  const P = (bx, p0, yA, q0, p1, yB, q1, m) => (alongX ? bx.add(p0, yA, q0, p1, yB, q1, m) : bx.add(q0, yA, p0, q1, yB, p1, m));
  P(B, a0, y - 0.4, c - w / 2, a1, y, c + w / 2, 'grid');
  for (const s of [-1, 1]) {
    const q0 = s < 0 ? c - w / 2 : c + w / 2 - 0.1, q1 = q0 + 0.1, cuts = [a0, ...(gaps[s] || []).flat(), a1];
    for (let i = 0; i + 1 < cuts.length; i += 2) {
      P(B, cuts[i], y, q0, cuts[i + 1], y + 1.1, q1, 'metal');
      const na = cuts[i] + (i > 0 ? 0.1 : 0), nb = cuts[i + 1] - (i + 2 < cuts.length ? 0.1 : 0); // (stops short of a gangway's rail at a gap)
      P(D, na, y + 0.95, s < 0 ? q0 - 0.06 : q1, nb, y + 1.05, s < 0 ? q0 : q1 + 0.06, neon[s < 0 ? 0 : 1]);
    }
  }
  for (let a = a0 + 3; a < a1 - 2; a += 6) P(D, a - 0.3, y - 0.55, c - 0.3, a + 0.3, y - 0.4, c + 0.3, 'lamp');
}
// the glass penthouse: 20 x 16 round (cx, cz), the bar on its ground floor (at y), the lounge upstairs (y + 4), a helipad
// on the roof (y + 7.9). stairs up in the east side, on up to the roof in the west side. doors per floor:
// o.g / o.u = { n, s, w, e: [[a, b]] } (local: along x on n/s, along z on w/e)
function penthouse(B, D, cx, cz, y, o = {}) {
  const L = B.local(cx, cz, 0, y), Ld = D.local(cx, cz, 0, y), G = o.g || {}, U = o.u || {};
  const op = (list, y0, y1) => (list || []).map(([a, b]) => ({ a, b, y0, y1 }));
  // ground floor: the bar
  L(-9.85, 0, -7.85, 9.85, 0.1, 7.85, 'carpet');
  wall(L, 'x', -8, -10.15, 10.15, 0, 3.75, 0.3, 'glassblock', op(G.n, 0, 2.6));
  wall(L, 'x', 8, -10.15, 10.15, 0, 3.75, 0.3, 'glassblock', [...op(G.s, 0, 2.6), ...op(G.sw, 1.1, 2.6)]);
  wall(L, 'z', -10, -7.85, 7.85, 0, 3.75, 0.3, 'glassblock', op(G.w, 0, 2.6));
  wall(L, 'z', 10, -7.85, 7.85, 0, 3.75, 0.3, 'glassblock', op(G.e, 0, 2.6));
  L(-8.5, 0.1, -7.85, -2.5, 1.2, -5.8, 'wood'); L(-8.5, 1.2, -6.6, -2.5, 1.26, -5.8, 'chrome'); // the bar (back to the wall: no gap behind it to get wedged in)
  Ld(-8.5, 1.5, -7.85, -2.5, 2.6, -7.6, 'shelfstock'); Ld(-6.6, 2.75, -7.85, -4.4, 3.35, -7.8, 'neonbar', { fit: 1 }); // the bottles, BAR?
  for (const x of [-7.8, -6.3, -4.8, -3.3]) L.B(x, 0.55, -5.15, 0.5, 0.9, 0.5, 'metal'); // stools
  for (const [x, z] of [[-6, 2.5], [-1.5, 4.5], [3, 2]]) { L.B(x, 0.5, z, 1.2, 0.8, 1.2, 'wood'); L.B(x, 0.95, z, 1.4, 0.1, 1.4, 'chrome'); }
  L(8.6, 0.1, -7.6, 9.7, 1.9, -6.4, 'toypurple'); Ld(8.55, 0.8, -7.4, 8.6, 1.6, -6.6, 'neonpink'); // the jukebox
  for (const x0 of [-8, 4.5]) { L(x0, 0.1, 6.6, x0 + 3.5, 0.55, 7.85, 'toypink'); L(x0, 0.55, 7.4, x0 + 3.5, 1.05, 7.85, 'toypink'); } // booths under the windows
  for (const x of [-6, 0, 5]) for (const z of [-3, 3]) Ld.B(x, 3.72, z, 1.6, 0.06, 0.4, 'lamp');
  Ld.B(0, 3.0, 0, 0.7, 0.7, 0.7, 'chrome'); Ld.B(0, 3.55, 0, 0.04, 0.4, 0.04, 'metal'); // the disco ball
  // up to the lounge (east side), its floor
  stairs(L, 7.6, 9.7, 1.0, 1, 0.1, 4.0, 'wood', 0.5);
  slab(L, -10.15, -8.15, 10.15, 8.15, 3.75, 4.0, 'wood', [7.5, 1.0, 9.85, 5.5]);
  L(7.4, 4.0, 1.0, 7.5, 5.0, 5.5, 'metal'); L(7.4, 4.0, 0.9, 9.85, 5.0, 1.0, 'metal'); // rails round the stairwell
  // the lounge: the long window onto the pool, sofas, a pool table
  wall(L, 'x', -8, -10.15, 10.15, 4.0, 7.6, 0.3, 'glassblock', op(U.n, 4.0, 6.6));
  wall(L, 'x', 8, -10.15, 10.15, 4.0, 7.6, 0.3, 'glassblock', [...op(U.s, 4.0, 6.6), { a: -6.5, b: 6.5, y0: 5.0, y1: 6.8 }]);
  wall(L, 'z', -10, -7.85, 7.85, 4.0, 7.6, 0.3, 'glassblock', op(U.w, 4.0, 6.6));
  wall(L, 'z', 10, -7.85, 7.85, 4.0, 7.6, 0.3, 'glassblock', op(U.e, 4.0, 6.6));
  for (const x0 of [-6.2, 0.6]) { L(x0, 4.0, 5.4, x0 + 5.4, 4.45, 6.6, 'toypink'); L(x0, 4.45, 6.6, x0 + 5.4, 5.0, 7.1, 'toypink'); }
  L(-2, 4.0, -4.6, 2, 4.85, -2.4, 'wood'); L(-1.85, 4.85, -4.45, 1.85, 4.9, -2.55, 'lawn');
  for (const x of [-4, 2]) for (const z of [-4, 3]) Ld.B(x, 7.57, z, 1.6, 0.06, 0.4, 'lamp');
  Ld(-9.85, 4.9, 3.0, -9.8, 6.3, 5.6, 'tvstatic'); Ld(-2.5, 6.75, -7.85, 2.5, 7.45, -7.8, 'neonwork', { fit: 1 }); // the telly, a motivational neon
  L.B(-9.3, 4.4, 7.3, 0.8, 0.8, 0.8, 'pottery'); Ld.B(-9.3, 5.3, 7.3, 1.2, 1.0, 1.2, 'leaves'); L.B(-9.3, 4.4, -7.3, 0.8, 0.8, 0.8, 'pottery'); Ld.B(-9.3, 5.3, -7.3, 1.2, 1.0, 1.2, 'leaves');
  // up to the roof (west side), the roof: a glass parapet, the helipad, a windsock
  stairs(L, -9.7, -7.6, 1.5, -1, 4.0, 7.9, 'metal', 0.5);
  slab(L, -10.15, -8.15, 10.15, 8.15, 7.6, 7.9, 'roofg', [-9.85, -3.0, -7.5, 1.5]);
  L(-7.5, 7.9, -3.0, -7.4, 8.9, 1.5, 'metal'); L(-9.85, 7.9, 1.5, -7.4, 8.9, 1.6, 'metal');
  wall(L, 'x', -8, -10.15, 10.15, 7.9, 8.7, 0.3, 'glassblock'); wall(L, 'x', 8, -10.15, 10.15, 7.9, 8.7, 0.3, 'glassblock');
  wall(L, 'z', -10, -7.85, 7.85, 7.9, 8.7, 0.3, 'glassblock'); wall(L, 'z', 10, -7.85, 7.85, 7.9, 8.7, 0.3, 'glassblock');
  L(-4.5, 7.9, -4.5, 4.5, 8.0, 4.5, 'helipad', { fit: 1 });
  Ld(-10.21, 7.65, -8.21, 10.21, 7.85, -8.15, 'neonpink'); Ld(-10.21, 7.65, 8.15, 10.21, 7.85, 8.21, 'neonpink'); // neon round the roof's edge
  Ld(-10.21, 7.65, -8.15, -10.15, 7.85, 8.15, 'neonpink'); Ld(10.15, 7.65, -8.15, 10.21, 7.85, 8.15, 'neonpink');
  Ld(-5, 6.9, 8.15, 5, 7.5, 8.2, 'adparty', { fit: 1 }); // over the long window, for the pool
  L.B(8.8, 9.4, -6.8, 0.15, 3, 0.15, 'metal'); Ld(8.88, 10.3, -7.1, 10.2, 10.75, -6.5, 'hazard'); // the windsock (sticks out over the edge)
}

// ------------------------------------------------------------ ROOFTOP: the roof party. three tops over the night city:
// west, the Jank Bank; east, the Hotel 4 Hours (a team's roof each: a lift's machine room stands between each spawn and
// the drop, so nobody sees the other side's spawn); between them and 4 m lower, the party block: the glass penthouse
// (the bar downstairs, the lounge upstairs, the helipad on its roof), the pool deck south of it (cabanas, loungers, the
// DJ, a pool to wade) and the north end under the sky-bridge. three lanes over the gaps: the sky-bridge tower to tower
// (long, open, one gangway into the lounge), the stair-bridges down to the bar's side doors (close up), the stair-
// bridges down to the pool deck (round the cabanas). jump pads throw you back up. the street is 150 m down, in the smog
function rooftop() {
  const B = builder(), D = builder(), r = rng(7707), add = B.add, W = B.local(0, 0, 0), Dw = D.local(0, 0, 0);
  const base = -152, L0 = -4, pick = (a) => a[(r() * a.length) | 0];
  // ---- the two towers: x [-58, -30] and [30, 58], z [-18, 18], roofs at 0. bridges land in the gaps on their inner sides
  const inner = [[-16, -12], [-6.5, -2.5], [11.5, 15.5]];
  roofTop(B, -58, -18, -30, 18, 0, 'office', { e: inner }); roofTop(B, 30, -18, 58, 18, 0, 'tenement', { w: inner });
  for (const s of [-1, 1]) { // the machine rooms: between the spawns and the gap
    add(s * 36, 0, -5, s * 42, 4.5, 5, 'concrete'); add(s * 35.8, 4.5, -5.2, s * 42.2, 4.8, 5.2, 'roofg');
    D.add(s * 42, 0, -0.8, s * 42.05, 2.2, 0.8, 'metal'); D.add(s * 36, 2.6, -3.5, s * 35.95, 3.6, 3.5, 'grid'); // a door on the spawn side, a vent on the other
    for (const z of [-11.5, -8.5]) acUnit(W, s * 52, z, 0); // the AC farm
    D.add(s * 30.3, 0, -17.7, s * 57.7, 0.02, 17.7, 'asphalt'); // the tar roof inside its concrete edge
    for (const [x, z] of [[33, -10], [44, 13], [56, -16]]) { B.box(s * x, 0.45, z, 0.9, 0.9, 0.9, 'metal'); D.add(s * x - 0.35, 0.9, z - 0.35, s * x + 0.35, 0.95, z + 0.35, 'grid'); } // vents
    add(s * 36.5, 0, 9, s * 39.5, 0.5, 13, 'glass'); D.add(s * 36.4, 0.5, 8.9, s * 39.6, 0.56, 13.1, 'metal'); // a skylight
    B.box(s * 39, 7.8, 3.5, 0.2, 6, 0.2, 'metal'); D.box(s * 39, 10.98, 3.5, 0.35, 0.35, 0.35, 'neonred'); // the antenna, its red light
    add(s * 31, 0, 17.15, s * (s < 0 ? 57 : 52), 0.45, 17.55, 'metal'); // a pipe run along the south parapet
  }
  for (const z of [-8, -5, 4]) { B.box(54.6, 1.2, z + 0.4, 0.08, 2.4, 0.08, 'metal'); D.box(54.6, 2.46, z + 0.4, 2.2, 0.12, 2.2, pick(['toypink', 'toyteal', 'cloth'])); } // the hotel's umbrellas
  // the bank (west): its water tower, a satellite dish, the JANK BANK sign over the north parapet
  waterTower(W, -52, 12, 0); add(-35, 0, 10.5, -33, 0.6, 12.5, 'metal'); D.add(-35.3, 0.6, 10.2, -32.7, 2.4, 12.8, 'white'); D.add(-34.2, 1.6, 11.3, -33.8, 3.2, 11.7, 'metal');
  for (const x of [-50, -40]) add(x - 0.2, 0, -17.6, x + 0.2, 6.4, -17.2, 'metal');
  D.add(-52, 2.2, -17.42, -38, 6.2, -17.38, 'adjankbank', { fit: 1 });
  // the hotel (east): HOTEL 4 HOURS in neon on a frame, a hot tub, loungers, the towel hut
  for (const x of [40, 52]) add(x - 0.2, 0, -17.6, x + 0.2, 6.4, -17.2, 'metal');
  D.add(38, 2.2, -17.42, 54, 6.2, -17.38, 'neonhotel', { fit: 1 });
  add(48, 0, 9, 52, 0.9, 9.3, 'tile'); add(48, 0, 12.7, 52, 0.9, 13, 'tile'); add(48, 0, 9.3, 48.3, 0.9, 12.7, 'tile'); add(51.7, 0, 9.3, 52, 0.9, 12.7, 'tile');
  D.add(48.3, 0.02, 9.3, 51.7, 0.75, 12.7, 'water'); // the hot tub
  for (const z of [-8, -5, 4]) add(55, 0, z, 56.8, 0.45, z + 0.8, z > 0 ? 'toyteal' : 'white');
  add(53, 0, 14, 57, 2.6, 17.6, 'wood'); add(52.8, 2.6, 13.8, 57.2, 2.8, 17.8, 'roofpink'); // the towel hut
  // ---- the party block: x [-22, 22], z [-28, 28], its roof at L0, the pool cut into it
  add(-22, base, -28, 22, L0 - 0.5, 28, 'tenement');
  groundHoles(B, -22.4, -28.4, 22.4, 28.4, L0 - 0.5, L0, 'concrete', [[-7, 13, 7, 21]]);
  const gapsC = [[-6.5, -2.5], [11.5, 15.5]];
  wall(W, 'x', -28.2, -22.4, 22.4, L0, L0 + 1, 0.4, 'concrete'); wall(W, 'x', 28.2, -22.4, 22.4, L0, L0 + 1, 0.4, 'concrete');
  wall(W, 'z', -22.2, -28, 28, L0, L0 + 1, 0.4, 'concrete', gapsC.map(([a, b]) => ({ a, b, y0: L0, y1: L0 + 1 })));
  wall(W, 'z', 22.2, -28, 28, L0, L0 + 1, 0.4, 'concrete', gapsC.map(([a, b]) => ({ a, b, y0: L0, y1: L0 + 1 })));
  // the stair-bridges down from the towers (to the bar's side doors, to the pool deck)
  for (const s of [-1, 1]) for (const zc of [-4.5, 13.5]) stairBridge(B, true, s * 22.4, s * 29.6, zc, L0, 0);
  // the sky-bridge tower to tower over the block's north end, a gangway off it into the lounge
  skyBridge(B, D, true, -29.6, 29.6, -14, 0, 4, { '-1': [[-12, -9], [9, 12]], 1: [[-16, -13], [-2, 2], [13, 16]] }); // (gaps to drop down onto the block)
  for (const x of [-14, 0, 14]) B.box(x, (L0 - 0.4) / 2, -14, 0.6, -0.4 - L0, 0.6, 'metal');
  add(-2, -0.25, -12, 2, 0, -10.15, 'grid'); add(-2.1, 0, -12, -2, 1.0, -10.15, 'metal'); add(2, 0, -12, 2.1, 1.0, -10.15, 'metal');
  // the penthouse (z [-10, 6]): doors on all four sides downstairs, the gangway door upstairs
  penthouse(B, D, 0, -2, L0, { g: { n: [[-2, 2]], s: [[-2, 2]], sw: [[-8, -4.5], [4.5, 8]], w: [[-3.5, -1.5]], e: [[-3.5, -1.5]] }, u: { n: [[-2, 2]] } });
  // the north end: the JANK COLA billboard, AC units, the cold store, crates
  billboard(W, 0, -26.6, L0, 'x');
  for (const x of [-18, -15]) acUnit(W, x, -24.5, L0); for (const x of [15, 18]) acUnit(W, x, -19, L0);
  add(-20.5, L0, -11.5, -15.5, L0 + 2.6, -8.5, 'metal'); D.add(-20.5, L0 + 2.6, -11.5, -15.5, L0 + 2.65, -8.5, 'white'); // the cold store
  cratePile(B, 12, -24.5, 3, r); B.box(8, L0 + 0.6, -20, 1.2, 1.2, 1.2, 'crate');
  // ---- the pool deck (z [6, 28]): a pool to wade, loungers, four cabanas, the DJ, palms, party lights
  add(-7, L0 - 0.5, 13, 7, L0 - 0.45, 21, 'tile'); D.add(-7, L0 - 0.45, 13, 7, L0 - 0.12, 21, 'water');
  for (const [x0, z0, x1, z1] of [[-21.8, 6.3, 21.8, 12.4], [-21.8, 21.6, 21.8, 27.8], [-21.8, 12.4, -7.6, 21.6], [7.6, 12.4, 21.8, 21.6]]) D.add(x0, L0, z0, x1, L0 + 0.02, z1, 'wood'); // the decking
  for (const [cx, cz, sx, sz] of [[-3, 17.3, 1.4, 0.35], [-3, 18.7, 1.4, 0.35], [-3.55, 18, 0.35, 1.05], [-2.45, 18, 0.35, 1.05]]) Dw.B(cx, L0 - 0.1, cz, sx, 0.25, sz, 'toyyellow'); // a rubber ring
  add(-7.6, L0, 12.4, 7.6, L0 + 0.1, 13, 'tile'); add(-7.6, L0, 21, 7.6, L0 + 0.1, 21.6, 'tile'); add(-7.6, L0, 13, -7, L0 + 0.1, 21, 'tile'); add(7, L0, 13, 7.6, L0 + 0.1, 21, 'tile');
  for (const x of [-5, -1.5, 2, 5.5]) for (const z of [10.6, 23]) add(x - 0.5, L0, z, x + 0.5, L0 + 0.45, z + 1.8, pick(['white', 'toypink', 'toyteal', 'toyyellow']));
  Dw.B(3, L0 - 0.02, 17, 1.6, 0.3, 0.9, 'toypink'); Dw.B(3.5, L0 + 0.5, 17, 0.25, 0.9, 0.25, 'toypink'); Dw.B(3.75, L0 + 0.9, 17, 0.5, 0.2, 0.2, 'toyorange'); // the flamingo
  for (const [x, z] of [[-16, 9], [16, 9], [-16, 24.5], [16, 24.5]]) { // cabanas: posts, a striped roof, half walls on two sides, a sofa
    for (const dx of [-2, 2]) for (const dz of [-2, 2]) B.box(x + dx, L0 + 1.4, z + dz, 0.15, 2.8, 0.15, 'wood');
    D.add(x - 2.3, L0 + 2.8, z - 2.3, x + 2.3, L0 + 2.95, z + 2.3, 'cloth');
    const ox = x > 0 ? 1 : -1; add(x + ox * 1.85, L0, z - 1.85, x + ox * 1.95, L0 + 1.1, z + 1.85, 'cloth');
    add(x - 1.85, L0, z + (z > 15 ? 1.85 : -1.95), x + 1.85, L0 + 1.1, z + (z > 15 ? 1.95 : -1.85), 'cloth');
    add(x - 1.2, L0, z - 0.6, x + 1.2, L0 + 0.5, z + 0.6, 'toyteal');
  }
  add(-3, L0, 25, 3, L0 + 1.1, 26.4, 'tire'); add(-2.8, L0 + 1.1, 25.2, 2.8, L0 + 1.2, 26.2, 'metal'); D.add(-2.6, L0 + 0.3, 24.96, 2.6, L0 + 0.9, 25, 'addj', { fit: 1 }); // the DJ's booth
  for (const x of [-4, 4]) { add(x - 0.6, L0, 25.1, x + 0.6, L0 + 2.2, 26.3, 'tire'); D.add(x - 0.4, L0 + 1.2, 25.06, x + 0.4, L0 + 2.0, 25.1, 'grid'); } // the speakers
  for (const x of [-5, 5]) B.box(x, L0 + 2, 27, 0.2, 4, 0.2, 'metal'); D.add(-5.1, L0 + 4, 26.9, 5.1, L0 + 4.2, 27.1, 'metal');
  for (let k = 0; k < 6; k++) D.box(-3.75 + k * 1.5, L0 + 3.85, 27, 0.35, 0.3, 0.35, pick(['neonpink', 'neoncyan', 'neonyellow', 'neongreen'])); // the light rig
  for (const [x, z] of [[-20, 26], [20, 26], [-20, 7.5], [20, 7.5]]) { add(x - 1, L0, z - 1, x + 1, L0 + 0.8, z + 1, 'stone'); palm(B.local(x, z, 0, L0 + 0.8), 0, 0, 5, r); }
  for (const [ax, bx, z] of [[-14, 14, 11.6], [-14, 14, 22.4]]) for (let x = ax; x <= bx; x += 1.4) D.box(x, L0 + 3.2 - 0.4 * Math.sin(((x - ax) / (bx - ax)) * Math.PI), z, 0.22, 0.28, 0.22, pick(['neonpink', 'neonyellow', 'neoncyan', 'lamp'])); // strings of party lights
  for (const x of [-14, 14]) for (const z of [11.6, 22.4]) B.box(x, L0 + 1.7, z, 0.12, 3.4, 0.12, 'metal');
  // ---- jump pads: tower -> the penthouse roof, the deck and the north end -> back up the towers
  for (const s of [-1, 1]) {
    add(s * 33.5 - 1.25, 0, 5.75, s * 33.5 + 1.25, 0.15, 8.25, 'pad', { pad: [-s * 22, 21, -6] }); // onto the helipad
    add(s * 18 - 1.25, L0, 16.75, s * 18 + 1.25, L0 + 0.15, 19.25, 'pad', { pad: [s * 13, 22, -2] });
    add(s * 18 - 1.25, L0, -23.55, s * 18 + 1.25, L0 + 0.15, -21.05, 'pad', { pad: [s * 15, 22, 7] });
  }
  // ---- spawns: each team behind its machine room; the rest spread over every roof and floor
  const att = [[-54, 0.2, -3], [-54, 0.2, 3], [-50, 0.2, -4.5], [-50, 0.2, 4.5], [-46, 0.2, -2], [-46, 0.2, 2], [-52, 0.2, 0]];
  const def = att.map(([x, y, z]) => [-x, y, -z]);
  const spawns = [...att.slice(0, 3), ...def.slice(0, 3), [-44, 0.2, -14], [44, 0.2, 14], [-38, 0.2, 14], [38, 0.2, -12], [0, L0 + 0.2, -20], [-12, L0 + 0.2, 0], [12, L0 + 0.2, 0],
    [0, L0 + 0.3, -5], [5, 0.2, 2], [-12, L0 + 0.2, 18], [12, L0 + 0.2, 18], [0, L0 + 0.2, 9], [0, 4.2, -2], [-20, 0.2, -14], [20, 0.2, -14]];

  // ---- the look (render-only): the towers round about, the street far below, the city to the fog
  const rs = rng(7708), scene = [[0, -95, 34, 20, 2], [-105, -95, 30, -30, 1], [105, -95, 28, 35, 3], [-105, 0, 32, 50, 3], [105, 0, 30, 10, 2], [-105, 95, 26, -15, 1], [0, 95, 36, 0, 1], [105, 95, 30, 60, 3]];
  const plan = [], roofs = {};
  for (const [x, z, w, h, t] of scene) { const ry = tower(D, x, z, w, w, h, { tiers: t, base, r: rs }); D.box(x, base - 10, z, w, 20, w, 'office'); plan.push([x, z, w, w, h, t]); roofs[`${x},${z}`] = ry; }
  for (const [x0, x1, z0, z1, y, c] of [[-58, -30, -18, 18, 0, 'neoncyan'], [30, 58, -18, 18, 0, 'neonpink'], [-22, 22, -28, 28, L0, 'neonyellow']]) D.add(x0 - 0.06, y - 2.6, z0 - 0.06, x1 + 0.06, y - 2.1, z1 + 0.06, c); // our three: a glowing band under each roof
  const roads = { xs: [-140, -70, 70, 140], zs: [-140, -50, 50, 140], w: 18 };
  streetLevel(D, -162, [...plan.map(([x, z, w, d]) => ({ x, z, w, d })), { x: -44, z: 0, w: 28, d: 36 }, { x: 44, z: 0, w: 28, d: 36 }, { x: 0, z: 0, w: 44, d: 56 }], roads, 180, rs);
  for (const [x, z, w, d] of [[-44, 0, 28, 36], [44, 0, 28, 36], [0, 0, 44, 56]]) D.add(x - w / 2, -172, z - d / 2, x + w / 2, base, z + d / 2, 'office'); // our three's foundations
  cityDress(D, plan, roofs, base, rs);
  cityBeyond(D, -162, 180, 520, rng(5151), { kill: -150, cap: -14, shore: 340, avenues: [[0, -260, 0.62], [260, 0, -0.95], [-240, 60, 1.4], [-200, -300, 2.6]], streets: gridOut(roads.xs, roads.zs, 180, 200) });

  let graph = null;
  const map = { name: 'Rooftop', size: 'medium', boxes: B.boxes, deco: D.boxes, killY: -161.6, fall: 'street', floorY: -170, cityR: 520, cityCap: -14,
    haze: { k: 0.92, top: -25, bottom: -162, dist: 95, color: 0x6a5c9c }, // look down: the city lights through a night smog
    sky: { top: 0x05051a, mid: 0x4a2a7a, bot: 0x000005, fog: 0x2a2050 }, fogNear: 110, fogFar: 480, spawns, teamSpawns: { att, def }, edgeGuard: true,
    traffic: { grid: { ...roads, S: 180, y: -162 + 0.08, off: 5 } },
    peekGraph() { return graph; }, dropGraph() { graph = null; }, get graph() { return graph || (graph = buildNav(B.boxes, { x0: -62, z0: -62, n: 124, cell: 1, levels: [L0 - 0.45, 0, 3.9], band: 0.6,
      stairs: [...[-1, 1].flatMap((s) => [-4.5, 13.5].map((zc) => ({ top: [s * 30.6, 0, zc], bot: [s * 21.4, L0, zc] }))),
        { bot: [8.65, L0 + 0.1, -2.2], top: [8.65, 0, 4.2] }, { bot: [-8.65, 0, 0.2], top: [-8.65, 3.9, -5.6] }],
      drops: [-1, 1].flatMap((s) => [{ from: [s * 10.5, 0, -15.5], to: [s * 10.5, L0, -17.5] }, { from: [s * 14.5, 0, -12.5], to: [s * 14.5, L0, -11] }]) })); },
  };
  return map;
}


// ------------------------------------------------------------ ROOFTOP S&D: the roof party (Plant & Defuse). the crashers
// (attackers) come up the south tower (JANK COLA on its billboard), security (defenders) hold the north tower (☺ CORP).
// between them, 4 m down, the party block: the penthouse (its walls stand between the two spawns), the pool deck. the
// two sites sit either side of the north tower, a flat bridge from it to each: west, B, the bank's roof; east, A, the
// hotel's. the crashers' ways in: mid (down onto the party block, round the penthouse, up the stair-bridge onto the
// site's side), the side lane (down the south tower's wing onto the low roof, along it, up onto the site's south
// side), and the connector from mid out to the low roof. security also has the stairs down into mid
function rooftopSD() {
  const B = builder(), D = builder(), r = rng(7717), add = B.add, W = B.local(0, 0, 0), Dw = D.local(0, 0, 0);
  const base = -152, L0 = -4, pick = (a) => a[(r() * a.length) | 0];
  // ---- the tops. middle column (x [-22, 22]): the north tower z [-70, -42], the party block z [-34, 14], the south
  // tower z [22, 54]. either side (x [30, 58] and [-58, -30]): the sites z [-58, -26], the low roofs z [-18, 30]
  roofTop(B, -22, -70, 22, -42, 0, 'office', { s: [[-2, 2]], w: [[-52, -48]], e: [[-52, -48]] }); // the north tower (security)
  roofTop(B, -22, 22, 22, 54, 0, 'tenement', { n: [[-12, -8], [8, 12]], w: [[24, 28]], e: [[24, 28]] }); // the south tower (the crashers)
  roofTop(B, -22, -34, 22, 14, L0, 'tenement', { n: [[-2, 2]], w: [[-32, -28], [-8, -4]], e: [[-32, -28], [-8, -4]], s: [[-12, -8], [8, 12]] }, base, [[-7, 0, 7, 8]]); // the party block, the pool cut in
  roofTop(B, -58, -58, -30, -26, 0, 'office', { e: [[-52, -48], [-32, -28]], s: [[-46, -42]] }); // B: the bank
  roofTop(B, 30, -58, 58, -26, 0, 'tenement', { w: [[-52, -48], [-32, -28]], s: [[42, 46]] }); // A: the hotel
  roofTop(B, -58, -18, -30, 30, -2, 'office', { n: [[-46, -42]], e: [[-8, -4], [24, 28]] }); // the low roofs
  roofTop(B, 30, -18, 58, 30, -2, 'tenement', { n: [[42, 46]], w: [[-8, -4], [24, 28]] });
  // ---- the links over the gaps
  stairBridge(B, false, -34.4, -41.6, 0, L0, 0); // north tower -> mid
  stairBridge(B, false, 14.4, 21.6, -10, L0, 0); stairBridge(B, false, 14.4, 21.6, 10, L0, 0); // south tower -> mid
  for (const s of [-1, 1]) {
    skyBridge(B, D, true, Math.min(s * 22.4, s * 29.6), Math.max(s * 22.4, s * 29.6), -50, 0, 4, {}, ['neoncyan', 'neoncyan']); // north tower -> the site (flat)
    stairBridge(B, true, s * 22.4, s * 29.6, -30, L0, 0); // mid -> the site's side
    stairBridge(B, false, -18.4, -25.6, s * 44, -2, 0); // the low roof -> the site's south side
    stairBridge(B, true, s * 22.4, s * 29.6, -6, L0, -2); // mid -> the low roof (the connector)
    stairBridge(B, true, s * 29.6, s * 22.4, 26, -2, 0); // the south tower's side -> the low roof
  }
  // ---- the party block: the penthouse (no door upstairs, its north wall solid: the spawns stay out of each other's
  // sight), the pool deck south of it, the cold store and AC north of it
  penthouse(B, D, 0, -14, L0, { g: { n: [[-2, 2]], s: [[-2, 2]], sw: [[-8, -4.5], [4.5, 8]], w: [[-3.5, -1.5]], e: [[-3.5, -1.5]] } });
  add(-7, L0 - 0.5, 0, 7, L0 - 0.45, 8, 'tile'); D.add(-7, L0 - 0.45, 0, 7, L0 - 0.12, 8, 'water');
  add(-7.6, L0, -0.6, 7.6, L0 + 0.1, 0, 'tile'); add(-7.6, L0, 8, 7.6, L0 + 0.1, 8.6, 'tile'); add(-7.6, L0, 0, -7, L0 + 0.1, 8, 'tile'); add(7, L0, 0, 7.6, L0 + 0.1, 8, 'tile');
  for (const [x0, z0, x1, z1] of [[-21.8, -5.7, 21.8, -0.6], [-21.8, 8.6, 21.8, 13.8], [-21.8, -0.6, -7.6, 8.6], [7.6, -0.6, 21.8, 8.6]]) D.add(x0, L0, z0, x1, L0 + 0.02, z1, 'wood');
  for (const x of [-5, -1.5, 2, 5.5]) add(x - 0.5, L0, 9.4, x + 0.5, L0 + 0.45, 11.2, pick(['white', 'toypink', 'toyteal', 'toyyellow']));
  Dw.B(-3, L0 - 0.02, 4, 1.6, 0.3, 0.9, 'toypink'); Dw.B(-2.5, L0 + 0.5, 4, 0.25, 0.9, 0.25, 'toypink'); Dw.B(-2.25, L0 + 0.9, 4, 0.5, 0.2, 0.2, 'toyorange'); // the flamingo
  for (const [cx, cz, sx, sz] of [[3, 3.3, 1.4, 0.35], [3, 4.7, 1.4, 0.35], [2.45, 4, 0.35, 1.05], [3.55, 4, 0.35, 1.05]]) Dw.B(cx, L0 - 0.1, cz, sx, 0.25, sz, 'toyyellow'); // a rubber ring
  for (const x of [-16, 16]) { // cabanas
    const z = 10;
    for (const dx of [-2, 2]) for (const dz of [-2, 2]) B.box(x + dx, L0 + 1.4, z + dz, 0.15, 2.8, 0.15, 'wood');
    D.add(x - 2.3, L0 + 2.8, z - 2.3, x + 2.3, L0 + 2.95, z + 2.3, 'cloth');
    add(x - 1.85, L0, z + 1.85, x + 1.85, L0 + 1.1, z + 1.95, 'cloth'); add(x - 1.2, L0, z - 0.6, x + 1.2, L0 + 0.5, z + 0.6, 'toyteal');
  }
  add(-3, L0, 12.2, 3, L0 + 1.1, 13.6, 'tire'); add(-2.8, L0 + 1.1, 12.4, 2.8, L0 + 1.2, 13.4, 'metal'); D.add(-2.6, L0 + 0.3, 12.16, 2.6, L0 + 0.9, 12.2, 'addj', { fit: 1 }); // the DJ
  for (const x of [-4, 4]) { add(x - 0.6, L0, 12.3, x + 0.6, L0 + 2.2, 13.5, 'tire'); D.add(x - 0.4, L0 + 1.2, 12.26, x + 0.4, L0 + 2.0, 12.3, 'grid'); }
  for (const z of [-2.5, 9]) { for (let x = -12; x <= 12; x += 1.4) D.box(x, L0 + 3.2 - 0.4 * Math.sin(((x + 12) / 24) * Math.PI), z, 0.22, 0.28, 0.22, pick(['neonpink', 'neonyellow', 'neoncyan', 'lamp'])); for (const x of [-12.2, 12.2]) B.box(x, L0 + 1.7, z, 0.12, 3.4, 0.12, 'metal'); }
  for (const s of [-1, 1]) { add(s * 21, L0, 11.2, s * 19, L0 + 0.8, 13.2, 'stone'); palm(B.local(s * 20, 12.2, 0, L0 + 0.8), 0, 0, 5, r); }
  add(-20.5, L0, -33.2, -15.5, L0 + 2.6, -30.2, 'metal'); D.add(-20.5, L0 + 2.6, -33.2, -15.5, L0 + 2.65, -30.2, 'white'); // the cold store
  for (const x of [15, 18]) acUnit(W, x, -33, L0); B.box(-6, L0 + 0.6, -27, 1.2, 1.2, 1.2, 'crate'); B.box(6, L0 + 0.6, -27, 1.2, 1.2, 1.2, 'crate'); cratePile(B, -4, -32.5, 3, r);
  // ---- B, the bank's roof: its machine room in the middle (cover), the JANK BANK sign, the AC farm, a water tower
  add(-47, 0, -45, -41, 4.5, -39, 'concrete'); add(-47.2, 4.5, -45.2, -40.8, 4.8, -38.8, 'roofg'); D.add(-47.05, 0, -42.8, -47, 2.2, -41.2, 'metal');
  for (const z of [-50, -47]) acUnit(W, -55, z, 0);
  waterTower(W, -53, -31, 0); add(-35, 0, -56, -33, 0.6, -54, 'metal'); D.add(-35.3, 0.6, -56.3, -32.7, 2.4, -53.7, 'white');
  for (const x of [-52, -40]) add(x - 0.2, 0, -57.6, x + 0.2, 6.4, -57.2, 'metal');
  D.add(-54, 2.2, -57.42, -38, 6.2, -57.38, 'adjankbank', { fit: 1 });
  B.box(-36, 0.6, -36, 1.2, 1.2, 1.2, 'crate'); B.box(-36, 0.6, -34.6, 1.2, 1.2, 1.2, 'crate'); B.box(-50, 0.45, -36.5, 0.9, 0.9, 0.9, 'metal');
  D.add(-57.7, 0, -57.7, -30.3, 0.02, -26.3, 'asphalt');
  // ---- A, the hotel's roof: the towel hut in the middle, HOTEL 4 HOURS, a hot tub, loungers under umbrellas
  for (const x of [40, 52]) add(x - 0.2, 0, -57.6, x + 0.2, 6.4, -57.2, 'metal');
  D.add(38, 2.2, -57.42, 54, 6.2, -57.38, 'neonhotel', { fit: 1 });
  add(41, 0, -45, 47, 2.6, -39, 'wood'); add(40.8, 2.6, -45.2, 47.2, 2.8, -38.8, 'roofpink');
  add(50, 0, -33, 54, 0.9, -32.7, 'tile'); add(50, 0, -29.3, 54, 0.9, -29, 'tile'); add(50, 0, -32.7, 50.3, 0.9, -29.3, 'tile'); add(53.7, 0, -32.7, 54, 0.9, -29.3, 'tile');
  D.add(50.3, 0.02, -32.7, 53.7, 0.75, -29.3, 'water');
  for (const z of [-52, -49]) { add(55, 0, z, 56.8, 0.45, z + 0.8, 'white'); B.box(54.6, 1.2, z + 0.4, 0.08, 2.4, 0.08, 'metal'); D.box(54.6, 2.46, z + 0.4, 2.2, 0.12, 2.2, pick(['toypink', 'toyteal'])); }
  B.box(36, 0.6, -36, 1.2, 1.2, 1.2, 'crate'); B.box(36, 0.6, -34.6, 1.2, 1.2, 1.2, 'crate'); B.box(50, 0.45, -37, 0.9, 0.9, 0.9, 'metal');
  D.add(30.3, 0, -57.7, 57.7, 0.02, -26.3, 'asphalt');
  // ---- the low roofs: AC, a skylight, vents, crates; the two towers: machine rooms, AC, the ☺ CORP flag, the billboard
  for (const s of [-1, 1]) {
    acUnit(W, s * 34, 4, -2); acUnit(W, s * 54, 16, -2); add(s * 50.5, -2, 4, s * 53.5, -1.5, 8, 'glass'); acUnit(W, s * 36, -12, -2);
    B.box(s * 38, -1.55, 20, 0.9, 0.9, 0.9, 'metal'); cratePile({ add: B.local(0, 0, 0, -2) }, s < 0 ? -53.5 : 50.5, -16.5, 2, r);
    D.add(s * 30.3, -2, -17.7, s * 57.7, -1.98, 29.7, 'asphalt');
    add(s * 12, 0, -68, s * 18, 4.5, -62, 'concrete'); add(s * 11.8, 4.5, -68.2, s * 18.2, 4.8, -61.8, 'roofg'); // the north tower's machine rooms
    add(s * 14, 0, 38, s * 20, 4.5, 44, 'concrete'); add(s * 13.8, 4.5, 37.8, s * 20.2, 4.8, 44.2, 'roofg'); // the south tower's
    acUnit(W, s * 18, -46, 0); acUnit(W, s * 18, 50, 0);
  }
  for (const x of [-6, 6]) add(x - 0.2, 0, -69.6, x + 0.2, 7, -69.2, 'metal');
  D.add(-8, 2.5, -69.42, 8, 6.8, -69.38, 'flagcorp', { fit: 1 });
  billboard(W, 0, 53, 0, 'x'); // over the crashers' backs
  // privacy walls on the two towers' edges over mid (up off their parapets, open at the stairs): neither spawn
  // looks down into mid or across it, you go down to fight for it
  for (const [x0, x1] of [[-22.4, -2], [2, 22.4]]) { add(x0, 1, -42, x1, 3.2, -41.6, 'glassblock'); D.add(x0, 3.2, -42.06, x1, 3.35, -41.54, 'neoncyan'); }
  for (const [x0, x1] of [[-22.4, -12], [-8, 8], [12, 22.4]]) { add(x0, 1, 21.6, x1, 3.2, 22, 'glassblock'); D.add(x0, 3.2, 21.54, x1, 3.35, 22.06, 'neonpink'); }
  D.add(-21.7, 0, -69.7, 21.7, 0.02, -42.3, 'asphalt'); D.add(-21.7, 0, 22.3, 21.7, 0.02, 53.7, 'asphalt');
  // more cover: a big HVAC box (standing cover) and its grille
  const hvac = (x, z, y = 0, alongX = true) => { const [hx, hz] = alongX ? [1.5, 1] : [1, 1.5]; add(x - hx, y, z - hz, x + hx, y + 2.2, z + hz, 'metal'); D.add(x - hx + 0.3, y + 2.2, z - hz + 0.3, x + hx - 0.3, y + 2.26, z + hz - 0.3, 'grid'); };
  const planter = (x, z, y = 0, alongX = true) => { const [hx, hz] = alongX ? [1.5, 0.6] : [0.6, 1.5]; add(x - hx, y, z - hz, x + hx, y + 0.9, z + hz, 'stone'); D.add(x - hx + 0.15, y + 0.9, z - hz + 0.15, x + hx - 0.15, y + 1.5, z + hz - 0.15, 'hedge'); };
  // A: a rooftop bar with stools, planters, an HVAC box, a day bed
  add(34, 0, -53, 38.5, 1.1, -52, 'wood'); add(33.9, 1.1, -53.1, 38.6, 1.16, -51.9, 'chrome'); for (const x of [34.6, 35.9, 37.2]) B.box(x, 0.4, -51.1, 0.45, 0.8, 0.45, 'metal');
  planter(44, -32); planter(36.5, -44, 0, false); hvac(52, -44, 0, false); add(49, 0, -52.5, 51.4, 0.6, -50.5, 'toypink');
  // B: an HVAC box, a skylight row, the generator, cable drums
  hvac(-36, -46); add(-52, 0, -42, -49, 0.5, -38, 'glass'); D.add(-52.1, 0.5, -42.1, -48.9, 0.56, -37.9, 'metal');
  add(-51.5, 0, -54, -48.5, 1.6, -52.4, 'containerg'); for (const x of [-40, -38.6]) B.box(x, 0.6, -31, 1.2, 1.2, 1.2, 'wood');
  // the low roofs (off the lane down the middle): a water tank, a chimney stack, an HVAC box, planters
  for (const s2 of [-1, 1]) { waterTower(W, s2 * 52, -6, -2); add(s2 * 39.5, -2, 9.5, s2 * 40.5, 1.2, 10.5, 'brick'); hvac(s2 * 37, 24, -2); planter(s2 * 50, 22, -2); planter(s2 * 38, -3, -2, false); }
  // the two towers: HVAC boxes and skylights (cover out of the spawns)
  for (const s2 of [-1, 1]) { hvac(s2 * 9, -50); hvac(s2 * 9, 30); add(s2 * 15, 0, -58, s2 * 18, 0.5, -54, 'glass'); add(s2 * 11.5, 0, 46, s2 * 14.5, 0.5, 50, 'glass'); }
  // the bomb site boards, on the parapets by the crashers' ways in
  siteBoard(D, -50.5, -0.4, -25.52, 'x', 'siteb', 2.0); siteBoard(D, 50.5, -0.4, -25.52, 'x', 'sitea', 2.0);
  siteBoard(D, -29.52, -0.4, -38, 'z', 'siteb', 1.8); siteBoard(D, 29.52, -0.4, -38, 'z', 'sitea', 1.8);

  // ---- spawns: the crashers on the south tower's back half, security on the north tower's
  const att = [[-6, 0.2, 48], [-2, 0.2, 50], [2, 0.2, 50], [6, 0.2, 48], [-4, 0.2, 45], [0, 0.2, 46], [4, 0.2, 45]];
  const def = [[-6, 0.2, -64], [-2, 0.2, -66], [2, 0.2, -66], [6, 0.2, -64], [-4, 0.2, -61], [0, 0.2, -62], [4, 0.2, -61]];
  const spawns = [...att.slice(0, 3), ...def.slice(0, 3), [-44, 0.2, -50], [44, 0.2, -50], [-44, -1.8, 10], [44, -1.8, 10], [0, L0 + 0.2, -28], [-14, L0 + 0.2, 2], [14, L0 + 0.2, 2], [-16, 0.2, 30], [16, 0.2, 30], [-14, 0.2, -54], [14, 0.2, -54]];

  // ---- the look (render-only): the towers round about, the street far below, the city to the fog
  const rs = rng(7718), scene = [[0, -113, 34, 20, 2], [-110, -113, 30, -30, 1], [110, -113, 28, 35, 3], [-110, -15, 32, 50, 3], [110, -15, 30, 10, 2], [-110, 97, 26, -15, 1], [0, 97, 36, 30, 2], [110, 97, 30, 60, 3]];
  const plan = [], roofs = {};
  for (const [x, z, w, h, t] of scene) { const ry = tower(D, x, z, w, w, h, { tiers: t, base, r: rs }); D.box(x, base - 10, z, w, 20, w, 'office'); plan.push([x, z, w, w, h, t]); roofs[`${x},${z}`] = ry; }
  const ours = [[-22, 22, -70, -42, 0, 'neoncyan'], [-22, 22, 22, 54, 0, 'neonpink'], [-22, 22, -34, 14, L0, 'neongreen'], [-58, -30, -58, -26, 0, 'neoncyan'], [30, 58, -58, -26, 0, 'neonpink'], [-58, -30, -18, 30, -2, 'neonyellow'], [30, 58, -18, 30, -2, 'neonyellow']];
  for (const [x0, x1, z0, z1, y, c] of ours) { D.add(x0 - 0.06, y - 2.6, z0 - 0.06, x1 + 0.06, y - 2.1, z1 + 0.06, c); D.add(x0, -172, z0, x1, base, z1, 'office'); }
  const roads = { xs: [-140, -70, 70, 140], zs: [-140, -84, 68, 140], w: 18 };
  streetLevel(D, -162, [...plan.map(([x, z, w, d]) => ({ x, z, w, d })), ...ours.map(([x0, x1, z0, z1]) => ({ x: (x0 + x1) / 2, z: (z0 + z1) / 2, w: x1 - x0, d: z1 - z0 }))], roads, 180, rs);
  cityDress(D, plan, roofs, base, rs);
  cityBeyond(D, -162, 180, 520, rng(5152), { kill: -150, cap: -14, shore: 340, avenues: [[0, -260, 0.62], [260, 0, -0.95], [-240, 60, 1.4], [-200, -300, 2.6]], streets: gridOut(roads.xs, roads.zs, 180, 200) });

  let graph = null;
  const map = { name: 'Rooftop', size: 'medium', boxes: B.boxes, deco: D.boxes, killY: -161.6, fall: 'street', floorY: -170, cityR: 520, cityCap: -14,
    haze: { k: 0.92, top: -25, bottom: -162, dist: 95, color: 0x6a5c9c },
    sky: { top: 0x05051a, mid: 0x4a2a7a, bot: 0x000005, fog: 0x2a2050 }, fogNear: 110, fogFar: 480, spawns, teamSpawns: { att, def }, edgeGuard: true,
    traffic: { grid: { ...roads, S: 180, y: -162 + 0.08, off: 5 } },
    // the crashers' lanes (the bomb carriers walk these; the walk graph gets them round whatever's in the way)
    nav: {
      A: [
        [[0, 46], [8, 36], [16, 30], [22, 26.5], [26, 26], [34, 26], [44, 18], [44, -14], [44, -22], [44, -30], [44, -40]], // the side lane: the low roof, up onto A
        [[2, 46], [10, 30], [10, 18], [10, 12], [12, 2], [12, -6], [12, -24], [18, -30], [26, -30], [34, -30], [40, -36]], // mid, round the penthouse, up A's side
        [[4, 46], [10, 30], [10, 18], [12, 6], [18, -6], [26, -6], [34, -6], [44, -10], [44, -22], [44, -30], [46, -40]], // mid, the connector out to the low roof, up
      ],
      B: [
        [[0, 46], [-8, 36], [-16, 30], [-22, 26.5], [-26, 26], [-34, 26], [-44, 18], [-44, -14], [-44, -22], [-44, -30], [-44, -40]],
        [[-2, 46], [-10, 30], [-10, 18], [-10, 12], [-12, 2], [-12, -6], [-12, -24], [-18, -30], [-26, -30], [-34, -30], [-40, -36]],
        [[-4, 46], [-10, 30], [-10, 18], [-12, 6], [-18, -6], [-26, -6], [-34, -6], [-44, -10], [-44, -22], [-44, -30], [-46, -40]],
      ],
    },
    sites: [{ id: 'A', min: [32, 0, -56], max: [56, 0, -28] }, { id: 'B', min: [-56, 0, -56], max: [-32, 0, -28] }],
    peekGraph() { return graph; }, dropGraph() { graph = null; }, get graph() { return graph || (graph = buildNav(B.boxes, { x0: -62, z0: -74, n: 132, cell: 1, levels: [L0 - 0.45, -2, 0, 3.9], band: 0.6,
      stairs: [{ top: [0, 0, -42.6], bot: [0, L0, -33.4] }, ...[-1, 1].flatMap((s) => [
        { top: [s * 30.6, 0, -30], bot: [s * 21.4, L0, -30] }, { top: [s * 44, 0, -26.6], bot: [s * 44, -2, -17.4] }, { top: [s * 30.6, -2, -6], bot: [s * 21.4, L0, -6] },
        { top: [s * 21.4, 0, 26], bot: [s * 30.6, -2, 26] }, { top: [s * 10, 0, 22.6], bot: [s * 10, L0, 13.4] }]),
        { bot: [8.65, L0 + 0.1, -14.2], top: [8.65, 0, -7.8] }, { bot: [-8.65, 0, -11.8], top: [-8.65, 3.9, -17.6] }] })); },
  };
  return map;
}

// ------------------------------------------------------------ SUBURB: a megacorp show-home cul-de-sac
// two rows of candy-coloured houses face each other across one long street, a bus and a box truck stuck in the middle
// of it as cover, fenced backyards with gates, back lanes behind both rows for flanking, a turnaround with a statue at
// the east end, a corner store and a building site at the west end. the ground runs out flat in every direction and a
// ring of trees marks the edge: walk out through them and you get the RETURN TO THE MAP countdown
function home(B, ox, oz, rot, o, r) {
  // the house's architecture goes through A (tagged for its Blender model), the furniture and the yard through L
  const A = B.arch('home', ox, oz, rot, 0, { paint: { siding: o.siding, roof: o.roof }, fence: !o.noFence }), L = A.plain, F = 3.4;
  shell(A, 14, 12, 2, F, o.siding, { roof: o.roof, backDoor: true, sideDoor: [1, 2.6] });
  // ground floor: a wall splits the kitchen (left) from the living room, and the living room from the laundry at the back
  wall(A, 'z', -1, -6, 6, 0.12, F, 0.2, 'plaster', [{ a: -4, b: -2.4, y0: 0, y1: 2.4 }]);
  wall(A, 'x', 1.5, -1, 7, 0.12, F, 0.2, 'plaster', [{ a: 2, b: 3.4, y0: 0, y1: 2.4 }]);
  // upstairs: two bedrooms + a bathroom
  wall(A, 'x', 1, -1.6, 7, F + 0.25, 2 * F, 0.2, 'plaster', [{ a: 0, b: 1.4, y0: F + 0.25, y1: F + 2.6 }]);
  wall(A, 'z', 2.5, 1, 6, F + 0.25, 2 * F, 0.2, 'plaster', [{ a: 2, b: 3.3, y0: F + 0.25, y1: F + 2.6 }]);
  wall(A, 'z', -1.6, -6, 1, F + 0.25, 2 * F, 0.2, 'plaster', [{ a: -3.5, b: -2, y0: F + 0.25, y1: F + 2.6 }]);
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
  A(-6.3, 2 * F + 0.3, -5.3, 6.3, 2 * F + 0.75, 5.3, o.roof); A(-4.6, 2 * F + 0.75, -3.8, 4.6, 2 * F + 1.2, 3.8, o.roof);
  A(-2.8, 2 * F + 1.2, -2.2, 2.8, 2 * F + 1.65, 2.2, o.roof); A(3.4, 2 * F + 0.75, 1.5, 4.4, 2 * F + 2.6, 2.5, 'brick');
  // porch with a neon OPEN HOUSE sign over the door
  A(-3, 0, -7.6, 3, 0.25, -6, 'wood');
  A(-2.9, 0.25, -7.5, -2.6, 3.0, -7.2, 'wood'); A(2.6, 0.25, -7.5, 2.9, 3.0, -7.2, 'wood');
  A(-3.2, 3.0, -7.8, 3.2, 3.25, -6.15, o.roof);
  L(-1.4, 2.62, -6.45, 1.4, 3.0, -6.17, 'signopen', { fit: 1 });
  // garage: open front, flat roof you can climb onto (bin -> crate -> roof), window from the roof into the bedroom
  wall(A, 'z', 13, -6, 1.2, 0, 3.2, 0.3, 'brick');
  wall(A, 'x', 1.2, 7.15, 13, 0, 3.2, 0.3, 'brick');
  wall(A, 'x', -6, 7.15, 13, 0, 3.2, 0.3, 'brick', [{ a: 7.6, b: 12.6, y0: 0, y1: 2.7 }]);
  A(7.15, 0, -6, 13, 0.1, 1.05, 'concrete'); // (wall face to wall face: no grass slot, no face shared with a wall end)
  A(7, 3.2, -6.2, 13.2, 3.5, 1.4, 'roofg');
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
    A(-8, 0, 13.9, -1.2, fy, 14.1, 'picket'); A(1.2, 0, 13.9, 14, fy, 14.1, 'picket');
    A(-8.1, 0, 6.2, -7.9, fy, 13.9, 'picket');
    A(13.9, 0, 1.4, 14.1, fy, 11, 'picket');
  }
  lollipop(L, -4, 12.8, 4 + r() * 2, r);
  if (!o.noPad) L(2.5, 0, 8.5, 5, 0.25, 11, 'pad', { pad: [0, 21, -4] });
  A(8, 0, 9, 12, 2.6, 13, 'wood'); A(7.8, 2.6, 8.8, 12.2, 2.8, 13.2, 'roofg');
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
  propOf('lollipop', L.pt(x, 0, z), quarter(L, x, z), () => {
    L.B(x, h / 2, z, 0.6, h, 0.6, 'wood');
    L.B(x, h + 0.9, z, 3.6, 1.8, 3.6, leaf);
    L.B(x, h + 2.2, z, 2.4, 1.0, 2.4, leaf);
  }, { t: leaf });
}
function conifer(L, x, z, h, r) {
  const y0 = 2 + ((h * 7.31) % 0.4); // each tree's lowest branches at their own height (neighbours' undersides never in one plane)
  propOf('conifer', L.pt(x, 0, z), quarter(L, x, z), () => {
    L.B(x, y0 / 2, z, 0.5, y0, 0.5, 'wood');
    for (let i = 0; i < 4; i++) L.B(x, y0 + (i + 0.5) * h / 4, z, 4.2 - i * 0.95, h / 4, 4.2 - i * 0.95, i % 2 ? 'leaves2' : 'hedge');
  });
}

// a stubby transit bus along +x (front at x0 + 12): you can get in by the door, shoot out through the window gaps
function bus(B, x0, z0) { propOf('transitbus', [x0, 0, z0], 0, () => busBoxes(B, x0, z0), { keep: (b) => !!b.fit }); } // (the livery stays a picture box)
function busBoxes(B, x0, z0) {
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
  propOf('boxtruck', [x0, 0, z0], 0, () => truckBoxes(B, x0, z0, livery, step), { keep: (b) => !!b.fit, skip: (b) => b.mat === 'crate' }); // (the livery stays a picture box, the step crate is a crate)
}
function truckBoxes(B, x0, z0, livery, step) {
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
  bbPost(L, -w / 3, 0, 0, 0.4, 0.4); bbPost(L, w / 3, 0, 0, 0.4, 0.4);
  propOf('billboard', L.pt(0, 0, 0), L.yaw, () => {
    L.B(0, 6 + h / 2, 0, w + 0.4, h + 0.4, 0.3, 'metal');
    L.B(0, 6 + h / 2, 0, w, h, 0.5, ad, { fit: 1 });
    L.B(0, 5.9, -0.7, w, 0.2, 1.0, 'grid');
  }, bbPicture);
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
  const ftree = (x, z, h, y = 0) => { const L2 = D.local(x, z, 0, y), m = fr() < 0.5 ? 'leaves' : fr() < 0.6 ? 'hedge' : 'leaves2', lolli = fr() < 0.5;
    propOf(lolli ? 'lollipop' : 'conifer', L2.pt(0, 0, 0), quarter(L2, 0, 0), () => ftreeBoxes(L2, h, m, lolli), lolli ? { t: m } : {}); }; // (Blender: round 4's lollipop or conifer)
  const ftreeBoxes = (L2, h, m, lolli) => {
    if (lolli) { L2.B(0, h / 2, 0, 0.6, h, 0.6, 'wood'); L2.B(0, h + 0.8, 0, 3.4 + fr(), 2.2, 3.4 + fr(), m); L2.B(0, h + 2.4, 0, 2.2, 1.2, 2.2, m); }
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
  propOf('founder_sd', [34, 0.1, 0], Math.PI / 2, () => { // (Blender: the monument, its plaque to the street; tools/blender/make_founder.py)
    add(29, 0.1, -5, 39, 0.6, 5, 'stone'); add(29.5, 0.6, -4.5, 38.5, 0.7, 4.5, 'lawn');
    add(32.6, 0.7, -1.4, 35.4, 2.6, 1.4, 'chrome'); add(32.2, 2.6, -1.8, 35.8, 6.2, 1.8, 'toyface', { fit: 1 });
    for (const [x, z] of [[30.5, -3.5], [37.5, 3.5], [30.5, 3.5], [37.5, -3.5]]) W.B(x, 1.3, z, 1.2, 1.2, 1.2, 'hedge');
  });
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
    peekGraph() { return graph; }, dropGraph() { graph = null; }, get graph() { return graph || (graph = buildNav(B.boxes, { x0: bounds[0] - 1, z0: bounds[1] - 1, n: bounds[2] - bounds[0] + 2, cell: 1, levels: [0], band: 0.5, keep: (x, z) => !outOfBounds(map, [x, 0, z]) })); },
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
    propOf('playground', [-24, 0, 0], 0, () => { // (Blender: tools/blender/make_playground.py; the floor stays the map's)
      P(-15.2, 0, -10.2, 15.2, 0.6, -10, 'toyred'); P(-15.2, 0, 10, -2, 0.6, 10.2, 'toyred'); P(2, 0, 10, 15.2, 0.6, 10.2, 'toyred'); P(-15.2, 0, -10, -15, 0.6, 10, 'toyred');
      for (const [x, z] of [[-11, -6], [-7, -6], [-11, -2], [-7, -2]]) P.B(x, 2.7, z, 0.3, 5.4, 0.3, 'toyblue'); // a climbing frame with a slide off it
      P(-11.3, 2.9, -6.3, -6.7, 3.2, -1.7, 'toygreen'); P(-11.3, 5.4, -6.3, -6.7, 5.7, -1.7, 'toyred');
      stairs(P, -10.5, -9, 1.8, -1, 0.12, 3.2, 'toyorange', 0.5);
      // the slide: its top, 28 small steps under the chute (walk up it, run down it), the run-out. (the model's chute runs
      // through the middle of every step's top: tools/blender/make_playground.py)
      P(-6.7, 0.12, -5.2, -6.14, 3.2, -2.8, 'toyteal');
      for (let k = 1; k <= 28; k++) P(-6.14 + (k - 1) * 0.1625, 0.12, -5.2, -6.14 + k * 0.1625, 3.2 - 2.66 * (k - 0.5) / 28, -2.8, 'toyteal');
      P(-1.59, 0.12, -5.2, -1.1, 0.54, -2.8, 'toyteal');
      P(2, 0.12, 2, 9, 1.0, 2.3, 'toyblue'); P(2, 0.12, 8.7, 9, 1.0, 9, 'toyblue'); P(2, 0.12, 2.3, 2.3, 1.0, 8.7, 'toyblue'); P(8.7, 0.12, 2.3, 9, 1.0, 8.7, 'toyblue'); // the ball pit
      const balls = ['toyred', 'toygreen', 'toyorange', 'toyteal', 'toypink'];
      for (let i = 0; i < 5; i++) for (let j = 0; j < 5; j++) P.B(3.1 + i * 1.3, 0.35 + ((i + j) % 2) * 0.12, 3.1 + j * 1.3, 0.9, 0.5 + ((i * j) % 3) * 0.08, 0.9, balls[(i * 3 + j) % 5]);
      P(-13, 0.12, 3, -9, 4.12, 7, 'toyface', { fit: 1 });
      P.B(10, 2.6, -7, 0.3, 5.2, 0.3, 'toyred'); P.B(3, 2.6, -7, 0.3, 5.2, 0.3, 'toyred'); P(2.8, 5.2, -7.2, 10.2, 5.5, -6.8, 'toyred'); // swings
      for (const x of [4.5, 6.5, 8.5]) { P.B(x, 3.6, -7, 0.05, 3.2, 0.05, 'chrome'); P.B(x, 1.85, -7, 0.7, 0.12, 0.4, 'toyteal'); }
    });
  }
  propOf('founder', [0, 0, 0], 0, () => { // the founder's plaza (Blender: the monument, tools/blender/make_founder.py)
    add(-5, 0, -5, 5, 0.4, 5, 'stone'); add(-4.5, 0.4, -4.5, 4.5, 0.5, 4.5, 'lawn');
    add(-1.4, 0.5, -1.4, 1.4, 2.4, 1.4, 'chrome'); add(-1.8, 2.4, -1.8, 1.8, 6, 1.8, 'toyface', { fit: 1 }); add(-0.8, 0.9, -1.43, 0.8, 1.7, -1.4, 'plaque', { fit: 1 });
    for (const [x, z] of [[-3.5, -3.5], [3.5, 3.5], [-3.5, 3.5], [3.5, -3.5]]) W.B(x, 1.1, z, 1.2, 1.2, 1.2, 'hedge');
  });
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
  const CA = B.arch('store', -71, 0, 1), C = CA.plain; // front (local -z) faces east, onto the street
  shell(CA, 18, 12, 1, 4.2, 'brick', { roof: 'roofg', roofAccess: true, backDoor: true });
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
  add(77.3, 0, -9.3, 77.5, 2.4, 9.3, 'plywood'); for (const [z, a] of [[-4.5, 'adbig1'], [4.5, 'adfun']]) D.add(77.51, 0.5, z - 4, 77.55, 2.2, z + 4, a, { fit: 1 }); // hoarding on the frame's far side (the posters a hair off it)
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
  // the lawns and back yards roll a little (shared/terrain.js). roads, pavements, houses and fences stay level
  shapeGround(B, D, { region: [bounds[0], bounds[1], bounds[2], bounds[3]], mat: 'grass', seed: 4242, up: 1.2, down: 0.7, near: 0.8, far: 4, points: [...new Set([...spawns, ...west, ...east])] });
  let graph = null;
  const map = {
    name: 'Suburb', size: 'large', boxes: B.boxes, deco: D.boxes, killY: -60, bounds, floorY: -4,
    sky: { top: 0x2f7cf0, mid: 0xffd3ec, bot: 0x7a4a6a, fog: 0xffd3ec }, fogNear: 110, fogFar: 430,
    spawns, teamSpawns: { att: west, def: east },
    gates, // the gaps in the back fence: [outside, inside] (a bot out past it heads for the nearest)
    // traffic (shared/traffic.js): in from the woods on the north street's inner lane, round the far end, out on the south
    // street's; the other way round on the two outer lanes. the parked cars are on the kerbs outside them
    traffic: { routes: [{ pts: [[-430, -16.5], [49.5, -16.5], [49.5, 16.5], [-430, 16.5]], v: [8, 13], r: 6 }, { pts: [[-430, 20], [53, 20], [53, -20], [-430, -20]], v: [8, 13], r: 6 }] },
    peekGraph() { return graph; }, dropGraph() { graph = null; }, get graph() { return graph || (graph = buildNav(B.boxes, { x0: bounds[0] - 1, z0: bounds[1] - 1, n: bounds[2] - bounds[0] + 2, cell: 1, levels: [0], band: 0.5, keep: (x, z) => !outOfBounds(map, [x, 0, z]) })); },
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
function trailer(B, x0, z0, livery) { propOf('trailer', [x0, 0, z0], 0, () => trailerBoxes(B, x0, z0, livery), bbPicture); } // (the Blender trailer, the livery stays a picture)
function trailerBoxes(B, x0, z0, livery) { // a semi trailer along x on its landing legs (no cab)
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
  propOf(cab ? 'semi' : 'semitrailer', L.pt(0, 0, 0), L.yaw, () => semiBoxes(L, livery, cab), { keep: (b) => !!b.fit }); // (the livery stays a picture box)
}
function semiBoxes(L, livery, cab) {
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
function excavator(Bd, x, z, rot) { const L = Bd.local(x, z, rot); propOf('excavator', L.pt(0, 0, 0), L.yaw, () => excavatorBoxes(L)); }
function excavatorBoxes(L) {
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
function generatorTower(Bd, x, z, rot) { const L = Bd.local(x, z, rot); propOf('generator', L.pt(0, 0, 0), L.yaw, () => generatorBoxes(L)); }
function generatorBoxes(L) { // a generator trailer with a fold-up light mast, lamps on
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
  for (let i = 0; i < n; i++) { const t = n > 1 ? i / (n - 1) : 0, x = x0 + (x1 - x0) * t, z = z0 + (z1 - z0) * t; propOf('cone', [x, 0, z], 0, () => { Bd.box(x, 0.06, z, 0.6, 0.12, 0.6, 'tire'); Bd.box(x, 0.45, z, 0.38, 0.7, 0.38, 'toyorange'); Bd.box(x, 0.5, z, 0.42, 0.14, 0.42, 'white'); }, { spin: spinAt(x, z) }); }
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
  const hb0 = B.boxes.length, hd0 = D.boxes.length; // (the shell from here to the rafters is the Blender hall: wh_hall)
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
  hallArch(B, D, hb0, hd0, 'wh_hall');
  rack(B, -26, -9, 18, r); rack(B, 7, -9, 12, r); // three rows, each broken by a cross aisle (and the office in the corner)
  rack(B, -21, 0, 18, r); rack(B, 6, 0, 12, r);
  rack(B, -26, 9, 18, r); rack(B, 8, 9, 18, r);
  for (const x of [-7, 6.5]) add(x - 0.08, 0, -HZ + 0.5, x + 0.08, 0.02, HZ - 0.5, 'neonyellow');
  // the foreman's office: two floors and stairs to the roof, in the north-east corner
  const O = B.arch('wh_office', 26, -13.5, 0); // (a Blender building: archfield.js; the desks and TVs stay the game's)
  shell(O, 11, 8.4, 2, 3.6, 'magenta', { floor: 'leopard', roof: 'roofg', roofAccess: true, backDoor: true });
  O.plain(-4.5, 0.12, -1.5, -1.5, 0.85, 0.5, 'wood'); O.plain(1.5, 3.85, -1.5, 4.5, 4.6, 0.5, 'wood'); O.plain.B(-3, 1.15, -0.5, 0.9, 0.6, 0.1, 'tvstatic'); O.plain.B(3, 4.9, -0.5, 0.9, 0.6, 0.1, 'tvstatic');
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
  const GB = B.arch('wh_booth', -68, 14, 2);
  shell(GB, 4, 3.4, 1, 2.8, 'toyteal', { roof: 'toyred', floor: 'tile', parapet: false });
  GB.plain(-1.6, 0.12, 0.4, 1.6, 0.95, 1.4, 'wood'); GB.plain.B(0.8, 1.2, 0.9, 0.7, 0.45, 0.1, 'tvstatic');
  barrier(B, -50, -8, true); barrier(B, -46, 12, true); cratePile(B, -54, 2, 5, r);
  const west = [[-70, 0.1, -6], [-70, 0.1, 0], [-70, 0.1, 6], [-62, 0.1, -9], [-62, 0.1, -2], [-62, 0.1, 5], [-62, 0.1, 11]];
  // ---- east: the staff car park (team 2). the site office, cars
  const SO = B.arch('wh_siteoffice', 52, -10, 0);
  shell(SO, 10, 4.2, 1, 3, 'containerb', { roof: 'roofg', floor: 'carpet', parapet: false });
  SO.plain(-4, 3.3, -2.5, 4, 4.2, -2.25, 'adoffice', { fit: 1 }); SO.plain(-4.5, 0.12, 0.6, -1.5, 0.85, 1.9, 'wood'); SO.plain(1.5, 0.12, 0.6, 4.5, 0.85, 1.9, 'wood');
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
    peekGraph() { return graph; }, dropGraph() { graph = null; }, get graph() { return graph || (graph = buildNav(B.boxes, { x0: bounds[0] - 1, z0: bounds[1] - 1, n: bounds[2] - bounds[0] + 2, cell: 1, levels: [0], band: 0.5, keep: (x, z) => !outOfBounds(map, [x, 0, z]) })); },
  };
  return map;
}

// ---- the depot kit (both Warehouse layouts)
// the hall's shell (walls, roof, rafters, lamps, door dressing: boxes hb0.. and deco hd0..) is a Blender building, in the
// map's own frame. look-only: the pictures (the company boards) stay the game's, the lamps still light the floor
function hallArch(B, D, hb0, hd0, id) {
  B.archSince(hb0, id, 0, 0);
  const tag = { av: id, ai: B.boxes.arch.length - 1 };
  for (let i = hb0; i < B.boxes.length; i++) if (B.boxes[i].fit) { delete B.boxes[i].av; delete B.boxes[i].ai; }
  for (let i = hd0; i < D.boxes.length; i++) if (!D.boxes[i].fit) Object.assign(D.boxes[i], tag);
}
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
function barrier(B, x, z, alongZ, len = 3) { propOf('barrier', [x, 0, z], alongZ ? -Math.PI / 2 : 0, () => barrierBox(B, x, z, alongZ, len)); }
function barrierBox(B, x, z, alongZ, len) {
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
  const GB = B.arch('wh_booth', -75, -13, 0); // the guard booth (nobody home)
  shell(GB, 4, 3.4, 1, 2.8, 'toyteal', { roof: 'toyred', floor: 'tile', parapet: false });
  GB.plain(-1.6, 0.12, 0.4, 1.6, 0.95, 1.4, 'wood'); GB.plain.B(0.8, 1.2, 0.9, 0.7, 0.45, 0.1, 'tvstatic');
  barrier(B, -66, -20, false); barrier(B, -66, 20, false);
  const att = [[-73, 0.1, -6], [-73, 0.1, 0], [-73, 0.1, 5], [-67, 0.1, -9], [-67, 0.1, -3], [-67, 0.1, 3], [-67, 0.1, 9]];

  // ---- the apron (between the attackers and the hall's west door): a little cover, the way into mid
  forklift(B, -44, -10, 1); container(B, -40, 14, true, 1, ['containerg']); barrier(B, -34, -4, true); barrier(B, -50, 4, true);
  pallets(B, -30, 17, 5, r); pallets(B, -28.6, 17, 3, r); cratePile(B, -54, -16, 5, r); palletLoad(B, -46, 16);

  // ---- MID: the hall
  const hb0 = B.boxes.length, hd0 = D.boxes.length; // (the shell from here to the rafters is the Blender hall: wh_hall_sd)
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
  hallArch(B, D, hb0, hd0, 'wh_hall_sd');
  for (const z of [-7.4, 7.2]) add(-20, 0, z - 0.06, 20, 0.02, z + 0.06, 'neonyellow'); // the aisle lines
  rack(B, -18, -9, 18, r); rack(B, 0, 9, 18, r); // racking: north side in the west half, south side in the east half
  const O = B.arch('wh_office_sd', 6, 0, 1); // the foreman's office in the middle of the floor (doors west and east, windows all round)
  shell(O, 8, 10, 1, 3.2, 'magenta', { floor: 'leopard', roof: 'roofg', parapet: false, backDoor: true });
  O.plain(-3, 0.12, -1, -1, 0.85, 3, 'wood'); O.plain(1.5, 0.12, -1, 3.5, 0.85, 3, 'wood'); O.plain.B(-2, 1.15, 1, 0.9, 0.6, 0.1, 'tvstatic'); O.plain.B(2.5, 1.15, 1, 0.9, 0.6, 0.1, 'tvstatic');
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
  const DB = B.arch('wh_dispatch', 40, -4, 1); // the dispatch booth (in the line from the hall's east door)
  shell(DB, 6, 4.4, 1, 2.9, 'toyteal', { roof: 'toyred', floor: 'tile', parapet: false, backDoor: true });
  DB.plain.B(0, 1.15, 1.8, 0.9, 0.6, 0.1, 'tvstatic');
  forklift(B, 33, 12, 0); pallets(B, 48, 14, 6, r); pallets(B, 49.4, 14, 4, r); barrier(B, 31, -16, true); barrier(B, 52, -14, false);
  trailerS(30, 17, 'adtruck'); palletLoad(B, 36, 4); palletLoad(B, 52, 18, 1);
  for (let i = 0; i < 4; i++) box(54 + (i % 2) * 0.85, 0.6, 6 + Math.floor(i / 2) * 0.85, 0.75, 1.2, 0.75, i % 2 ? 'barrel' : 'barrelr');
  add(24.3, 0, 21.7, 30.25, 2.4, 27.75, 'wood'); // the bin store in the corner (no way through to the trailer park)
  // the staff block: the defenders spawn behind it, it hides them from the courtyard
  const sb0 = B.boxes.length, sd0 = D.boxes.length; // (the block and its windows are a Blender building: wh_staff)
  add(58, 0, -18, 63, 7.2, 18, 'magenta'); add(57.6, 7.2, -18.4, 63.4, 7.6, 18.4, 'roofg'); // (its roof is over the ceiling: no perch over the spawn)
  for (let z = -14; z <= 14; z += 4) for (const y of [1.2, 4.4]) { D.add(57.96, y, z - 1, 57.98, y + 1.8, z + 1, 'glass'); D.add(63.02, y, z - 1, 63.04, y + 1.8, z + 1, 'glass'); }
  B.archSince(sb0, 'wh_staff', 60.5, 0);
  for (let i = sd0; i < D.boxes.length; i++) Object.assign(D.boxes[i], { av: 'wh_staff', ai: B.boxes.arch.length - 1 });
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
    peekGraph() { return graph; }, dropGraph() { graph = null; }, get graph() { return graph || (graph = buildNav(B.boxes, { x0: bounds[0] - 1, z0: bounds[1] - 1, n: bounds[2] - bounds[0] + 2, cell: 1, levels: [0], band: 0.5, keep: (x, z) => !outOfBounds(map, [x, 0, z]) })); },
  };
  return map;
}

// ------------------------------------------------------------ DESERT: big sand town split by a canyon
// ---- desert props (shared by Desert and Bazaar's outskirts)
function stall(L, x, z, rot, rv) { // a market stall: posts, a loud awning, a counter piled with goods, sometimes a rug
  const T = (lx, lz) => [[lx, lz], [-lz, lx], [-lx, -lz], [lz, -lx]][rot & 3];
  const P = (x0, y0, z0, x1, y1, z1, m, ex) => { const [ax, az] = T(x0, z0), [bx, bz] = T(x1, z1); L(x + ax, y0, z + az, x + bx, y1, z + bz, m, ex); };
  const o = { keep: (b) => !!b.rug }; // (the Blender stall, painted its awning's colour; the rug stays a cloth box)
  propOf('stall', L.pt(x, 0, z), L.yaw - (rot & 3) * Math.PI / 2, () => {
    for (const [px, pz] of [[-1.9, -1.4], [1.7, -1.4], [-1.9, 1.2], [1.7, 1.2]]) P(px, 0, pz, px + 0.2, 2.9, pz + 0.2, 'wood');
    o.t = ['cloth', 'toypink', 'toyteal', 'toyyellow', 'leopard', 'camo'][(rv() * 6) | 0];
    P(-2.3, 2.9, -1.8, 2.3, 3.05, 1.8, o.t);
    P(-1.6, 0, -1.0, 1.6, 0.95, -0.3, 'wood');
    const goods = ['toyorange', 'toygreen', 'toyred', 'pottery', 'shelfstock', 'cloth'];
    for (let i = 0; i < 4; i++) { const gx = -1.4 + i * 0.75, h = 0.2 + rv() * 0.35; P(gx, 0.95, -0.95, gx + 0.6, 0.95 + h, -0.4, goods[(rv() * goods.length) | 0]); }
    if (rv() < 0.6) P(-1.6, 0.6, 1.25, 1.6, 2.6, 1.3, ['leopard', 'camo', 'cloth', 'magenta'][(rv() * 4) | 0], { rug: 1 }); // a rug hung at the back
    if (rv() < 0.7) pot(L, x + T(2.6, -1.2)[0], z + T(2.6, -1.2)[1], 0.8 + rv() * 0.4);
  }, o);
}
function pot(L, x, z, s = 1) { // a big clay pot
  const [ax, , az] = L.pt(x, 0, z);
  propOf('pot', L.pt(x, 0, z), L.yaw, () => { L.B(x, 0.25 * s, z, 0.7 * s, 0.5 * s, 0.7 * s, 'pottery'); L.B(x, 0.7 * s, z, 0.9 * s, 0.4 * s, 0.9 * s, 'pottery'); L.B(x, 1.02 * s, z, 0.45 * s, 0.25 * s, 0.45 * s, 'pottery'); }, { spin: spinAt(ax, az) || 1e-6 });
}
function cart(L, x, z, alongX) { propOf('handcart', L.pt(x, 0, z), L.yaw + (alongX ? 0 : -Math.PI / 2), () => cartBoxes(L, x, z, alongX), { t: ['crate', 'pottery', 'cloth', 'toyorange'][Math.abs((x * 3 + z) | 0) % 4] }); }
function cartBoxes(L, x, z, alongX) { // a wooden hand cart, tipped forward on its handles
  if (alongX) { L(x - 1.2, 0.6, z - 0.8, x + 1.2, 1.3, z + 0.8, 'wood'); for (const s of [-1, 1]) L(x - 0.45, 0, z + s * 0.85 - 0.1, x + 0.45, 0.9, z + s * 0.85 + 0.1, 'tire'); L(x + 1.2, 0.3, z - 0.6, x + 2.6, 0.45, z - 0.45, 'wood'); L(x + 1.2, 0.3, z + 0.45, x + 2.6, 0.45, z + 0.6, 'wood'); }
  else { L(x - 0.8, 0.6, z - 1.2, x + 0.8, 1.3, z + 1.2, 'wood'); for (const s of [-1, 1]) L(x + s * 0.85 - 0.1, 0, z - 0.45, x + s * 0.85 + 0.1, 0.9, z + 0.45, 'tire'); L(x - 0.6, 0.3, z + 1.2, x - 0.45, 0.45, z + 2.6, 'wood'); L(x + 0.45, 0.3, z + 1.2, x + 0.6, 0.45, z + 2.6, 'wood'); }
  L(x - 0.6, 1.3, z - 0.6, x + 0.6, 1.8, z + 0.6, ['crate', 'pottery', 'cloth', 'toyorange'][Math.abs((x * 3 + z) | 0) % 4]);
}
function tent(L, x, z, c) { // a cloth tent on poles (the Bazaar camp's kind)
  propOf('tent', L.pt(x, 0, z), L.yaw, () => {
    L(x - 3, 0, z - 2, x + 3, 0.05, z + 2, 'cloth');
    for (const sx of [-1, 1]) for (const sz of [-1, 1]) L.B(x + sx * 2.8, 1.4, z + sz * 1.8, 0.2, 2.8, 0.2, 'wood');
    L(x - 3.2, 2.8, z - 2.2, x + 3.2, 3.0, z + 2.2, c); L(x - 2.2, 3.0, z - 1.4, x + 2.2, 3.5, z + 1.4, c);
  }, { t: c });
}
function palm(L, x, z, h, r) { // a palm: a trunk that leans a little as it goes up, a crown of fronds
  const o = {}; // (the Blender palm leans along +x: turned to this one's lean)
  propOf('palm', L.pt(x, 0, z), L.yaw, () => {
    const lx = (r() - 0.5) * 0.5, lz = (r() - 0.5) * 0.5, n = Math.max(3, Math.round(h / 1.4));
    o.spin = Math.atan2(-lz, lx) || 1e-6;
    for (let i = 0; i < n; i++) L.B(x + lx * i, (i + 0.5) * (h / n), z + lz * i, 0.55 - i * 0.02, h / n + 0.02, 0.55 - i * 0.02, i % 2 ? 'wood' : 'plywood');
    const tx = x + lx * n, tz = z + lz * n;
    L.B(tx, h + 0.1, tz, 1.4, 0.6, 1.4, 'leaves');
    for (const [dx, dz] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { L.B(tx + dx * 1.9, h, tz + dz * 1.9, dx ? 3 : 0.9, 0.35, dz ? 3 : 0.9, 'leaves2'); L.B(tx + dx * 3.3, h - 0.5, tz + dz * 3.3, dx ? 1.4 : 0.8, 0.3, dz ? 1.4 : 0.8, 'leaves'); }
  }, o);
}
function camel(L, x, z, alongX) { propOf('camel', L.pt(x, 0, z), L.yaw + (alongX ? 0 : -Math.PI / 2), () => camelBoxes(L, x, z, alongX), { t: ['cloth', 'leopard', 'toypink'][Math.abs((x + z) | 0) % 3] }); }
function camelBoxes(L, x, z, alongX) { // a very boxy camel. it judges you
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
function rocks(D, x, z, s, r, tag) { // a rock formation: a banded mesa with a few blocks stacked off it. tag: { av, ai } when a Blender rock model draws it
  const h = s * (1.1 + r() * 0.8);
  D.box(x, h / 2, z, s * 1.6, h, s, 'rock', tag);
  D.box(x + s * 0.2, h + s * 0.12, z - s * 0.1, s * 1.1, s * 0.24, s * 0.7, 'rock', tag);
  if (r() < 0.6) D.box(x - s * 0.9, h * 0.3, z + s * 0.3, s * 0.7, h * 0.6, s * 0.7, 'rock', tag);
  if (r() < 0.5) D.box(x + s * 1.1, h * 0.2, z - s * 0.4, s * 0.5, h * 0.4, s * 0.6, 'rock', tag);
}

// ---- the frontier kit (both Desert layouts): false-front buildings on a boardwalk, a wind pump, water towers, the
// mine's headframe, a train stopped at the depot, the three ways over the canyon, hay, wagons, saguaros, graves
// a false-front building: a shell (stairs to the roof), the tall flat front with its sign stuck above the roofline, a
// boardwalk porch with posts and an awning (or a balcony you can reach through the upstairs windows). front = local -z
function frontier(B, D, x, z, rot, w, d, floors, o = {}) {
  const L = B.local(x, z, rot), Ld = D.local(x, z, rot), F = 3.6, hw = w / 2, hd = d / 2, top = floors * F + 0.3;
  shell(L, w, d, floors, F, o.paint || 'adobe', { floor: 'wood', roof: o.roof || 'wood', roofAccess: o.roofAccess !== false, backDoor: true, parapet: false, winSpacing: 3.5 });
  // the false front: up past the roof, a crest on top, the sign on it (a hair off its face)
  const ft = top + (o.front ?? 2.4);
  L(-hw, top, -hd - 0.15, hw, ft, -hd + 0.15, o.paint || 'adobe');
  L(-hw * 0.45, ft, -hd - 0.15, hw * 0.45, ft + 0.7, -hd + 0.15, o.paint || 'adobe');
  L(-hw - 0.1, ft - 0.25, -hd - 0.35, hw + 0.1, ft + 0.05, -hd + 0.3, o.trim || 'wood'); // the cornice (over the front's top edge)
  if (o.sign) Ld(-hw + 0.8, top + 0.3, -hd - 0.2, hw - 0.8, ft - 0.45, -hd - 0.16, o.sign, { fit: 1 });
  // the boardwalk, its posts, the awning (or the balcony over it)
  L(-hw, 0, -hd - 2.6, hw, 0.35, -hd - 0.15, 'wood');
  for (let px = -hw + 0.3; px <= hw - 0.2; px += (w - 0.6) / Math.max(1, Math.round((w - 0.6) / 3.6))) L.B(px, 1.85, -hd - 2.4, 0.2, 3.0, 0.2, 'wood');
  L(-hw - 0.2, 3.35, -hd - 2.75, hw + 0.2, 3.55, -hd - 0.15, o.awning || 'wood');
  if (o.balcony && floors > 1) { L(-hw - 0.2, 3.55, -hd - 2.75, hw + 0.2, 4.45, -hd - 2.6, 'wood'); for (const s of [-1, 1]) L(s > 0 ? hw + 0.05 : -hw - 0.2, 3.55, -hd - 2.6, s > 0 ? hw + 0.2 : -hw - 0.05, 4.45, -hd - 0.15, 'wood'); }
  if (o.wanted) Ld(o.wanted, 1.1, -hd - 0.2, o.wanted + 0.6, 1.85, -hd - 0.17, 'adwanted', { fit: 1 });
  return { L, Ld, top, F };
}
// a wind pump: a timber lattice tower, a platform you can stand on, the wheel and its tail vane, a trough at its feet
function windpump(B, D, x, z) {
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) B.box(x + sx * 1.1, 4.5, z + sz * 1.1, 0.25, 9, 0.25, 'wood');
  for (const y of [2.5, 5.5]) { D.add(x - 1.2, y, z - 1.25, x + 1.2, y + 0.15, z - 1.15, 'wood'); D.add(x - 1.2, y, z + 1.15, x + 1.2, y + 0.15, z + 1.25, 'wood'); D.add(x - 1.25, y, z - 1.1, x - 1.15, y + 0.15, z + 1.1, 'wood'); D.add(x + 1.15, y, z - 1.1, x + 1.25, y + 0.15, z + 1.1, 'wood'); }
  B.add(x - 1.5, 9, z - 1.5, x + 1.5, 9.25, z + 1.5, 'wood'); // the platform (grapple up)
  D.add(x - 0.15, 9.25, z - 0.15, x + 0.15, 11.4, z + 0.15, 'metal');
  for (const [a, b] of [[[-0.18, 9.6], [0.18, 13.2]], [[-1.8, 11.2], [1.8, 11.56]]]) D.add(x + a[0], a[1], z - 0.55, x + b[0], b[1], z - 0.45, 'white'); // the wheel's blades (a cross)
  D.add(x - 1.3, 9.9, z - 0.56, x + 1.3, 12.9, z - 0.44, 'grid'); D.add(x - 0.25, 11.15, z - 0.45, x + 0.25, 11.65, z + 2.4, 'metal'); D.add(x - 0.05, 10.6, z + 2.2, x + 0.05, 12.2, z + 3.4, 'toyred'); // its spokes, the tail, the vane
  B.add(x + 1.6, 0, z - 0.6, x + 4.4, 0.8, z + 0.6, 'wood'); D.add(x + 1.75, 0.8, z - 0.45, x + 4.25, 0.82, z + 0.45, 'water');
}
// a water tower on stilts: four legs, braces, the tank (you can grapple to it and stand on its lid), a spout
function waterTank(B, D, x, z, h = 7) {
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) B.box(x + sx * 1.5, h / 2, z + sz * 1.5, 0.35, h, 0.35, 'wood');
  for (const y of [h * 0.35, h * 0.7]) { D.add(x - 1.6, y, z - 1.55, x + 1.6, y + 0.15, z - 1.45, 'wood'); D.add(x - 1.6, y, z + 1.45, x + 1.6, y + 0.15, z + 1.55, 'wood'); }
  B.add(x - 2.1, h, z - 2.1, x + 2.1, h + 3.2, z + 2.1, 'wood'); B.add(x - 1.6, h + 3.2, z - 1.6, x + 1.6, h + 3.6, z + 1.6, 'roofg');
  for (const y of [h + 0.7, h + 2.3]) D.add(x - 2.15, y, z - 2.15, x + 2.15, y + 0.12, z + 2.15, 'metal'); // the hoops
  D.add(x + 2.1, h + 0.4, z - 0.12, x + 3.1, h + 0.6, z + 0.12, 'metal');
}
// the mine's headframe: four steel legs up to the sheave wheel, braced, the cable down into the shaft
function headframe(B, D, x, y0, z, h = 14) {
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) B.box(x + sx * 1.6, y0 + h / 2, z + sz * 1.6, 0.4, h, 0.4, 'rust');
  for (let y = y0 + 3; y < y0 + h; y += 3.2) { D.add(x - 1.75, y, z - 1.7, x + 1.75, y + 0.2, z - 1.5, 'rust'); D.add(x - 1.75, y, z + 1.5, x + 1.75, y + 0.2, z + 1.7, 'rust'); D.add(x - 1.7, y, z - 1.5, x - 1.5, y + 0.2, z + 1.5, 'rust'); D.add(x + 1.5, y, z - 1.5, x + 1.7, y + 0.2, z + 1.5, 'rust'); }
  B.add(x - 2, y0 + h, z - 2, x + 2, y0 + h + 0.3, z + 2, 'grid'); // the top deck
  D.add(x - 0.15, y0 + h + 0.3, z - 0.2, x + 0.15, y0 + h + 3.9, z + 0.2, 'toyred'); D.add(x - 1.8, y0 + h + 1.95, z - 0.2, x + 1.8, y0 + h + 2.25, z + 0.2, 'toyred'); // the wheel: a red cross,
  D.add(x - 1.3, y0 + h + 0.8, z - 0.24, x + 1.3, y0 + h + 3.4, z + 0.24, 'grid'); // its spokes
  D.add(x + 1.2, y0, z - 0.04, x + 1.28, y0 + h + 2, z + 0.04, 'tire'); // the cable
}
// a train stopped along z: the engine (its nose at -z: the cowcatcher, the lamp, the stack; the cab at the back), the
// tender behind it, a boxcar with both doors open (walk through it), a flatcar of crates, the caboose. its rails under
// it (ext: how far they run on past each end). returns where it ends. (B, D can be turned frames: { add: L, box: L.B })
function train(B, D, x, z0, ext = [30, 40]) {
  const rails = (a, b) => { for (const s of [-1, 1]) D.add(x + s * 0.75 - 0.06, 0, a, x + s * 0.75 + 0.06, 0.14, b, 'metal'); for (let t = a + 0.12; t < b; t += 0.7) D.add(x - 1.2, 0, t, x + 1.2, 0.08, t + 0.25, 'wood'); }; // (the first tie a bit in from the rails' end: no faces in one plane)
  const wheels = (a, b) => { for (let t = a + 0.7; t < b - 0.5; t += 1.6) for (const s of [-1, 1]) D.add(x + s * 1.47 - 0.08, 0.08, t - 0.55, x + s * 1.47 + 0.08, 1.18, t + 0.55, 'tire'); }; // (just outboard of every car's sides)
  let z = z0;
  // the engine (nose first: the tender's coupled on behind the cab, where a tender goes)
  B.add(x - 1.3, 0.25, z, x + 1.3, 1.3, z + 11, 'metal');
  B.add(x - 1.1, 1.3, z, x + 1.1, 3.5, z + 7.8, 'burnt'); // boiler
  B.add(x - 0.4, 3.5, z + 1.2, x + 0.4, 5.1, z + 2, 'burnt'); D.add(x - 0.6, 5.1, z + 1, x + 0.6, 5.5, z + 2.2, 'burnt'); // stack
  B.add(x - 0.5, 3.5, z + 3.8, x + 0.5, 4.2, z + 4.8, 'gold'); // the dome
  for (const [a, b] of [[-1.5, -1.3], [1.3, 1.5]]) B.add(x + a, 1.3, z + 8, x + b, 4.2, z + 10.8, 'carred'); // cab sides (open in the middle: climb in)
  B.add(x - 1.5, 1.3, z + 10.8, x + 1.5, 4.2, z + 11, 'carred'); B.add(x - 1.65, 4.2, z + 7.7, x + 1.65, 4.45, z + 11.2, 'roofg'); // cab back + roof
  for (const t of [0.4, 0.8, 1.2]) D.add(x - 1.3 + t * 0.3, 0.2, z - 0.4 - t * 0.4, x + 1.3 - t * 0.3, 1.1 - t * 0.5, z - t * 0.4, 'toyred'); // cowcatcher
  D.add(x - 0.35, 3.0, z - 0.06, x + 0.35, 3.5, z, 'light'); D.add(x - 1.12, 2.35, z - 0.02, x + 1.12, 2.65, z + 7.75, 'gold'); // the lamp, a brass band
  wheels(z, z + 11);
  z += 11.6;
  // the tender
  B.add(x - 1.3, 0.25, z, x + 1.3, 2.6, z + 5, 'wood'); D.add(x - 1.1, 2.6, z + 0.2, x + 1.1, 2.9, z + 4.8, 'burnt'); wheels(z, z + 5);
  z += 5.6;
  // the boxcar: walls with a door gap each side, floor at 1.25 (a crate to step up), roof you can stand on
  B.add(x - 1.4, 0.25, z, x + 1.4, 1.25, z + 10, 'metal');
  for (const s of [-1, 1]) { B.add(x + s * 1.4 - (s > 0 ? 0.15 : 0), 1.25, z, x + s * 1.4 + (s > 0 ? 0 : 0.15), 3.9, z + 3.6, 'containerr'); B.add(x + s * 1.4 - (s > 0 ? 0.15 : 0), 1.25, z + 6.4, x + s * 1.4 + (s > 0 ? 0 : 0.15), 3.9, z + 10, 'containerr'); B.add(x + s * 1.4 - (s > 0 ? 0.15 : 0), 3.1, z + 3.6, x + s * 1.4 + (s > 0 ? 0 : 0.15), 3.9, z + 6.4, 'containerr'); }
  B.add(x - 1.25, 1.25, z, x + 1.25, 3.9, z + 0.15, 'containerr'); B.add(x - 1.25, 1.25, z + 9.85, x + 1.25, 3.9, z + 10, 'containerr');
  B.add(x - 1.55, 3.9, z - 0.1, x + 1.55, 4.1, z + 10.1, 'containerr');
  for (const s of [-1, 1]) B.add(x + s * 2.05 - 0.4, 0, z + 4.4, x + s * 2.05 + 0.4, 0.62, z + 5.6, 'crate'); // steps up into it
  wheels(z, z + 10);
  z += 10.6;
  // the flatcar, crates lashed on
  B.add(x - 1.4, 0.25, z, x + 1.4, 1.25, z + 9, 'wood');
  B.add(x - 1.1, 1.25, z + 0.8, x + 0.3, 2.65, z + 2.2, 'crate'); B.add(x - 0.4, 1.25, z + 3.6, x + 1.1, 2.4, z + 5.2, 'crate'); B.add(x - 1.0, 1.25, z + 6.4, x + 0.6, 3.0, z + 8.1, 'crate');
  wheels(z, z + 9);
  z += 9.6;
  // the caboose: red, a cupola on the roof, open at both ends (a little room)
  B.add(x - 1.4, 0.25, z, x + 1.4, 1.25, z + 7, 'metal');
  for (const s of [-1, 1]) B.add(x + s * 1.4 - (s > 0 ? 0.15 : 0), 1.25, z, x + s * 1.4 + (s > 0 ? 0 : 0.15), 3.6, z + 7, 'carred');
  B.add(x - 1.6, 3.6, z - 0.2, x + 1.6, 3.8, z + 7.2, 'roofg'); B.add(x - 0.9, 3.8, z + 2.5, x + 0.9, 4.9, z + 4.5, 'carred');
  wheels(z, z + 7);
  z += 7;
  rails(z0 - ext[0], z + ext[1]);
  return z;
}
// over the canyon (along x, from x0 to x1, centred on z): the mine's timber trestle (narrow, rails on it, a cart);
// the stone bridge (wide, parapets, an arch under it); the rope bridge (planks and rope, nothing else)
function trestle(B, D, x0, x1, z, w = 3.6) {
  B.add(x0, -0.3, z - w / 2, x1, 0, z + w / 2, 'wood');
  for (let x = x0 + 0.3; x < x1; x += 0.7) D.add(x, 0, z - w / 2 + 0.3, x + 0.3, 0.06, z + w / 2 - 0.3, 'wood'); // ties
  for (const s of [-1, 1]) D.add(x0, 0.06, z + s * 0.75 - 0.06, x1, 0.2, z + s * 0.75 + 0.06, 'metal'); // rails
  for (let x = x0 + 1.5; x < x1 - 1; x += 3.5) { for (const s of [-1, 1]) D.add(x - 0.2, -40, z + s * (w / 2 - 0.3) - 0.2, x + 0.2, -0.3, z + s * (w / 2 - 0.3) + 0.2, 'wood'); for (let y = -4; y > -40; y -= 5) D.add(x - 0.15, y, z - w / 2 + 0.1, x + 0.15, y + 0.3, z + w / 2 - 0.1, 'wood'); } // the bents
  for (let y = -6.5; y > -40; y -= 5) for (const s of [-1, 1]) D.add(x0 + 1, y, z + s * (w / 2 - 0.3) - 0.12, x1 - 1, y + 0.25, z + s * (w / 2 - 0.3) + 0.12, 'wood');
}
function stoneBridge(B, D, x0, x1, z, w = 9) {
  B.add(x0, -1.2, z - w / 2, x1, 0, z + w / 2, 'stone');
  for (const s of [-1, 1]) B.add(x0, 0, s > 0 ? z + w / 2 - 0.6 : z - w / 2, x1, 1.0, s > 0 ? z + w / 2 : z - w / 2 + 0.6, 'stone');
  const half = (x1 - x0) / 2;
  for (let i = 0; i < 5; i++) { const k = i / 5, ww = half * (1 - k * k) + 0.4; D.add(x0 - 0.02, -1.2 - (i + 1) * 1.6, z - w / 2 + 0.3, x0 + (half - ww) + 0.6, -1.2 - i * 1.6, z + w / 2 - 0.3, 'stone'); D.add(x1 - (half - ww) - 0.6, -1.2 - (i + 1) * 1.6, z - w / 2 + 0.3, x1 + 0.02, -1.2 - i * 1.6, z + w / 2 - 0.3, 'stone'); } // the arch's two halves stepping in
}
function ropeBridge(B, D, x0, x1, z, w = 2.6) {
  B.add(x0, -0.12, z - w / 2, x1, 0, z + w / 2, 'wood');
  for (let x = x0 + 0.2; x < x1 - 0.1; x += 0.5) D.add(x, 0, z - w / 2, x + 0.38, 0.03, z + w / 2, 'plywood'); // the planks
  for (const s of [-1, 1]) {
    const e = z + s * (w / 2 + 0.05);
    B.add(x0, 0.95, e - 0.04, x1, 1.03, e + 0.04, 'tire'); // the rope (you can lean on it; you can also go over it)
    for (const x of [x0 + 0.1, x1 - 0.1]) B.box(x, 0.7, e, 0.26, 1.4, 0.26, 'wood');
    for (let x = x0 + 1.2; x < x1 - 1; x += 1.2) D.add(x - 0.02, 0, e - 0.02, x + 0.02, 0.95, e + 0.02, 'tire'); // the hangers
  }
}
function hay(B, x, z, n, alongX = true) { // hay bales, stacked (each one a Blender bale)
  for (let i = 0; i < n; i++) { const lvl = i < 3 ? 0 : 1, k = lvl ? i - 3 : i, ox = (k - (lvl ? 0.5 : 1)) * 1.3; propOf('hay', [x + (alongX ? ox : 0), lvl * 0.8, z + (alongX ? 0 : ox)], alongX ? 0 : -Math.PI / 2, () => B.add(x + (alongX ? ox : 0) - (alongX ? 0.6 : 0.4), lvl * 0.8, z + (alongX ? 0 : ox) - (alongX ? 0.4 : 0.6), x + (alongX ? ox : 0) + (alongX ? 0.6 : 0.4), lvl * 0.8 + 0.78, z + (alongX ? 0 : ox) + (alongX ? 0.4 : 0.6), 'yellow')); }
}
function wagon(B, D, x, z, alongX = true, cover = true) { propOf(cover ? 'wagon' : 'wagon_open', [x, 0, z], alongX ? 0 : -Math.PI / 2, () => wagonBoxes(B, D, x, z, alongX, cover)); }
function wagonBoxes(B, D, x, z, alongX, cover) { // a covered wagon: the bed, big wheels, the canvas over hoops
  const R = (x0, y0, z0, x1, y1, z1, m, dd) => (alongX ? (dd ? D : B).add(x + x0, y0, z + z0, x + x1, y1, z + z1, m) : (dd ? D : B).add(x + z0, y0, z + x0, x + z1, y1, z + x1, m));
  R(-2.2, 0.75, -0.9, 2.2, 1.35, 0.9, 'wood');
  for (const wx of [-1.5, 1.5]) for (const s of [-1, 1]) R(wx - 0.55, 0, s * 1.0 - 0.08, wx + 0.55, 1.1, s * 1.0 + 0.08, 'wood', true);
  if (cover) { R(-2.0, 1.35, -0.95, 2.0, 2.6, -0.85, 'white'); R(-2.0, 1.35, 0.85, 2.0, 2.6, 0.95, 'white'); R(-2.0, 2.6, -0.8, 2.0, 2.85, 0.8, 'white'); }
  R(2.2, 0.85, -0.08, 3.6, 0.95, 0.08, 'wood', true); // the tongue
}
function saguaro(L, x, z, h = 4) { // a cartoon saguaro: a trunk and two arms
  propOf('saguaro', L.pt(x, 0, z), L.yaw, () => {
    L.B(x, h / 2, z, 0.6, h, 0.6, 'toygreen');
    L.B(x + 0.6, h * 0.45, z, 0.7, 0.4, 0.4, 'toygreen'); L.B(x + 0.85, h * 0.62, z, 0.4, 0.9, 0.4, 'toygreen');
    L.B(x - 0.55, h * 0.6, z, 0.6, 0.36, 0.36, 'toygreen'); L.B(x - 0.75, h * 0.74, z, 0.36, 0.7, 0.36, 'toygreen');
  });
}
function grave(L, x, z, k) { // a headstone or a wooden cross, and the mound
  propOf(k % 3 ? 'grave' : 'grave_cross', L.pt(x, 0, z), L.yaw, () => {
    L(x - 0.45, 0, z - 0.9, x + 0.45, 0.25, z + 0.9, 'dirt');
    if (k % 3) L(x - 0.32, 0, z - 1.12, x + 0.32, 0.9 + (k % 2) * 0.2, z - 0.9, 'stone');
    else { L.B(x, 0.6, z - 1.0, 0.12, 1.2, 0.12, 'wood'); L.B(x, 0.85, z - 1.0, 0.6, 0.12, 0.12, 'wood'); }
  });
}
// a one-room adobe hut: flat roof with a low lip, a ladder up the side (bars you can climb: steps), a door and windows
function adobeHut(B, D, x, z, rot, w = 6, d = 5, paint = 'adobe') {
  const L = B.arch('adobe', x, z, rot, 0, { paint: { siding: 'hut' + paint } }), hw = w / 2, hd = d / 2; // (drawn as a Blender building, look only: its walls take the hut's paint, archfield.js PAINT)
  shell(L, w, d, 1, 3.2, paint, { floor: 'wood', roof: 'adobe', roofAccess: false, backDoor: false, parapet: true, winSpacing: 3 });
  for (let i = 0; i < 6; i++) L(hw + 0.16, i * 0.58, -0.5, hw + 0.66, i * 0.58 + 0.12, 0.5, 'wood'); // ladder rungs up the side (each one a step), clear of the wall
  for (const s of [-0.55, 0.47]) L(hw + 0.16, 0, s, hw + 0.66, 3.9, s + 0.08, 'wood');
}
// broken adobe walls round a yard (x0..x1, z0..z1): random gaps and heights, the odd doorway
function ruin(B, x0, z0, x1, z1, rv, h = 2.6) {
  const run = (ax, f, a0, a1) => { for (let a = a0; a < a1 - 0.5;) { const len = 2 + rv() * 4, top = Math.min(a1, a + len), hh = 0.8 + rv() * (h - 0.8); if (rv() < 0.78) { if (ax === 'x') B.add(a, 0, f - 0.3, top, hh, f + 0.3, 'adobe'); else B.add(f - 0.3, 0, a, f + 0.3, hh, top, 'adobe'); } a = top + 0.4 + rv() * 1.6; } };
  run('x', z0, x0, x1); run('x', z1, x0, x1); run('z', x0, z0 + 0.3, z1 - 0.3); run('z', x1, z0 + 0.3, z1 - 0.3);
}
// a wooden watchtower: four legs, a platform with a rail, a ladder (steps) up one side
function watchtower(B, x, z, h = 8) {
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) B.box(x + sx * 1.3, h / 2, z + sz * 1.3, 0.3, h, 0.3, 'wood');
  B.add(x - 1.7, h, z - 1.7, x + 1.7, h + 0.25, z + 1.7, 'wood');
  for (const [a, b, c, e] of [[-1.7, -1.7, 1.7, -1.55], [-1.7, 1.55, 1.7, 1.7], [-1.7, -1.55, -1.55, 1.55]]) B.add(x + a, h + 0.25, z + b, x + c, h + 1.25, z + e, 'wood'); // the rail (open on the ladder side)
  B.add(x - 1.9, h + 2.6, z - 1.9, x + 1.9, h + 2.85, z + 1.9, 'roofg'); for (const sx of [-1, 1]) for (const sz of [-1, 1]) B.box(x + sx * 1.6, h + 1.425, z + sz * 1.6, 0.15, 2.35, 0.15, 'wood'); // (posts up under the roof)
  for (let y = 0.45; y < h; y += 0.55) B.add(x + 1.75, y - 0.06, z - 0.5, x + 2.15, y + 0.06, z + 0.5, 'wood'); // ladder rungs
}
// boulders along a line (the canyon's rim): low cover, gaps between
function lipFence(B, x, z0, z1) { // a rail fence along the canyon's lip at x (no strip between it and the drop wide enough to stand in)
  const n = Math.max(1, Math.round((z1 - z0) / 3)); for (let i = 0; i <= n; i++) B.box(x, 0.6, z0 + ((z1 - z0) * i) / n, 0.2, 1.2, 0.2, 'wood');
  B.add(x - 0.05, 0.85, z0, x + 0.05, 0.95, z1, 'wood');
}
function boulders(B, x0, z0, x1, z1, n, rv, edge = 0, skip = null, tag) { // edge: +-1 = on that rim of the canyon (x +-7), flush with the lip
  for (let i = 0; i < n; i++) { const t = (i + 0.2 + rv() * 0.6) / n, x = x0 + (x1 - x0) * t + (rv() - 0.5) * 1.2, z = z0 + (z1 - z0) * t, s = 0.9 + rv() * 1.3;
    if (rv() < 0.8) { const w = s * (1 + rv() * 0.6); if (!(skip && skip(z, s))) B.box(edge ? edge * (6.7 + w / 2) : x, s * 0.4, z, w, s * 0.8, s, 'rock', tag); } }
}

// ------------------------------------------------------------ DESERT: Dry Gulch, a frontier town split by a canyon.
// the old town on the west bank: Main Street (the saloon, the bank, the hotel, the livery, the general store, the
// sheriff, the undertaker, the church and its bell tower), corrals and a blacksmith behind the north row, the
// cemetery behind the south row. three ways over the canyon: the mine's rail trestle (north), the stone bridge (Main
// Street), the rope bridge (south). the east bank: Mine Square, the mine in its mesa (a tunnel, a shaft, the
// headframe on top), the depot with a train stopped at it, the oasis. the town wall and the desert all round it.
// teams: the west gate (team 1) and behind the depot (team 2)
function desert() {
  const B = builder(), D = builder();
  const r = rng(909), rv = rng(9090); // rv: the look's own dice, so nothing you collide with moves
  const S = 100, W = B.local(0, 0, 0), Dw = D.local(0, 0, 0), add = B.add;
  // ---- the ground: sand both sides of the canyon (the east bank has a hole: the mine shaft), rock under it
  B.add(-S, -2, -S, -7, 0, S, 'sand');
  groundHoles(B, 7, -S, S, S, -2, 0, 'sand', [[53, -68, 56, -65]]);
  B.add(-S + 10, -10, -S + 10, -9, -2, S - 10, 'dirt'); groundHoles(B, 9, -S + 10, S - 10, S - 10, -10, -2, 'dirt', [[53, -68, 56, -65]]);
  for (const [x0, z0, x1, z1] of [[52.8, -68.2, 56.2, -68.02], [52.8, -64.98, 56.2, -64.8], [52.8, -68, 52.98, -65], [56.02, -68, 56.2, -65]]) B.add(x0, -50, z0, x1, -10, z1, 'rock'); // the shaft, all the way down (just outside the hole; solid, so a fall can't drift off under the bank)
  // ---- the town wall (gates east and west, a road through both, gate towers, corner towers, battlements)
  for (const s of [-1, 1]) { B.add(-S, 0, s * S - 0.6, S, 9, s * S + 0.6, 'adobe'); B.add(s * S - 0.6, 0, -S, s * S + 0.6, 9, S, 'adobe'); }
  for (const sx of [-1, 1]) {
    carve(B, sx * S - 1, 0, -6, sx * S + 1, 6, 6, (q) => q.mat === 'adobe' && q.min[0] < sx * S + 0.7 && q.max[0] > sx * S - 0.7 && q.max[2] - q.min[2] > 100);
    for (const sz of [-1, 1]) B.add(sx * S - 3, 0, sz > 0 ? 6.5 : -10.5, sx * S + 3, 12, sz > 0 ? 10.5 : -6.5, 'adobe');
    for (const sz of [-1, 1]) B.box(sx * S, 6.75, sz * S, 7, 13.5, 7, 'adobe');
  }
  for (let t = -S + 6; t <= S - 6; t += 3) { // merlons on the outer edge of the wall top
    for (const sz of [-1, 1]) B.add(t - 0.6, 9, sz * (S + 0.6) - (sz > 0 ? 0.5 : 0), t + 0.6, 10, sz * (S + 0.6) + (sz > 0 ? 0 : 0.5), 'adobe');
    if (Math.abs(t) > 12) for (const sx of [-1, 1]) B.add(sx * (S + 0.6) - (sx > 0 ? 0.5 : 0), 9, t - 0.6, sx * (S + 0.6) + (sx > 0 ? 0 : 0.5), 10, t + 0.6, 'adobe');
  }
  const spawns = [];
  // ---- WEST BANK: Main Street, from the west gate to the stone bridge
  add(-97, 0, -9.6, -7, 0.03, 9.6, 'dirtroad'); add(-S, 0, -6, -97, 0.03, 6, 'dirtroad');
  const north = [ // fronts on the street (z -12.2): [x, w, d, floors, paint, sign, extra]
    [-85, 14, 12, 1, 'wood', 'adlivery', { front: 3.4 }], [-65, 18, 14, 2, 'sidemint', 'adsaloon', { balcony: true, awning: 'toypink' }],
    [-46, 12, 12, 1, 'adobe', 'adbank', { front: 2.6 }], [-28, 16, 12, 3, 'sidelemon', 'adhotel', { balcony: true, awning: 'toyteal' }],
  ];
  const south = [ // fronts on the street (z 12.2)
    [-84, 16, 12, 2, 'sideorange', 'adgeneral', { balcony: true, awning: 'toyyellow' }], [-66, 12, 12, 1, 'adobe', 'adsheriff', { wanted: -2.5 }],
    [-51, 10, 10, 1, 'magenta', 'adundertaker', { front: 1.8 }],
  ];
  const bld = {};
  for (const [x, w, d, n, paint, sign, o] of north) { bld[sign] = frontier(B, D, x, -12.2 - d / 2, 2, w, d, n, { paint, sign, ...o }); spawns.push([x, 0.2, -12.2 - d / 2 + 1]); }
  for (const [x, w, d, n, paint, sign, o] of south) { bld[sign] = frontier(B, D, x, 12.2 + d / 2, 0, w, d, n, { paint, sign, ...o }); spawns.push([x, 0.2, 12.2 + d / 2 - 1]); }
  hay(B, -89, -19, 5); camel(W, -82, -19.5, true); // the livery: hay, and a camel (horses sold separately)
  { const L = bld.adsaloon.L; L(-7, 0.12, 4.6, 3, 1.15, 5.6, 'wood'); L(-7, 1.15, 4.4, 3, 1.25, 5.8, 'chrome'); L(4.5, 0.12, 3.4, 8.6, 0.6, 6.6, 'wood'); L(5.5, 0.6, 4.6, 7.4, 1.8, 5.6, 'burnt'); // the bar, the stage, a piano
    for (const [tx, tz] of [[-5, -2], [-1, -3.5], [3, -1.5]]) { L.B(tx, 0.5, tz, 1.4, 0.76, 1.4, 'wood'); } }
  { const L = bld.adbank.L; L(-5.6, 0.12, -1.0, 5.6, 1.2, -0.6, 'wood'); L(-5.6, 1.2, -0.95, 5.6, 2.6, -0.85, 'grid'); // the counter, its bars
    L(-3.6, 0.12, 2.2, -1.2, 3.0, 2.5, 'metal'); L(1.2, 0.12, 2.2, 3.6, 3.0, 2.5, 'metal'); L(-1.2, 2.4, 2.2, 1.2, 3.0, 2.5, 'metal'); // the vault: its front (a doorway in it),
    L(-3.6, 0.12, 2.5, -3.3, 3.0, 5.6, 'metal'); L(3.3, 0.12, 2.5, 3.6, 3.0, 5.6, 'metal'); L(-3.6, 3.0, 2.2, 3.6, 3.3, 5.6, 'metal'); // sides, roof
    L(1.25, 0.12, 0.5, 1.4, 2.4, 2.15, 'gold'); L(-2.8, 0.12, 4.2, -1.0, 0.9, 5.4, 'gold'); L(0.6, 0.12, 4.4, 2.6, 0.6, 5.4, 'gold'); } // its door swung open, the loot
  { const L = bld.adsheriff.L; L(-4.6, 0.12, -4.4, -1.6, 0.85, -3.0, 'wood'); for (let gx = 0.4; gx < 5.6; gx += 0.45) L(gx, 0.12, 1.5, gx + 0.08, 3.4, 1.58, 'metal'); L(0.4, 3.0, 1.5, 5.6, 3.4, 1.58, 'metal'); } // the desk, the cell bars
  { const L = bld.adundertaker.L; for (const cx of [-3.2, -1.9]) L(cx, 0.35, -7.4, cx + 0.8, 2.3, -7.1, 'wood'); } // coffins stood up on the boardwalk
  // the church and its bell tower (the tallest thing on this bank: the bell's up top, grapple or climb)
  { const C = B.local(-31, 20.2, 0); shell(C, 14, 16, 1, 5, 'white', { floor: 'wood', roof: 'roofpink', roofAccess: false, backDoor: true, parapet: false, winSpacing: 3.5 });
    C(-6.4, 5.3, -7.4, 6.4, 6.0, 7.4, 'roofpink'); C(-4.4, 6.0, -7.4, 4.4, 6.7, 7.4, 'roofpink'); C(-2.2, 6.7, -7.4, 2.2, 7.4, 7.4, 'roofpink'); // a stepped roof
    for (let i = 0; i < 4; i++) C(-4 + i * 2.2, 0.12, -1, -2.6 + i * 2.2, 0.6, 5, 'wood'); // pews
    const T = B.local(-41.3, 15.2, 0); shell(T, 6, 6, 4, 3.6, 'white', { floor: 'wood', roof: 'roofpink', roofAccess: true, parapet: true });
    for (const sx of [-1, 1]) for (const sz of [-1, 1]) T.B(sx * 2.7, 16.6, sz * 2.7, 0.3, 3.4, 0.3, 'white'); T(-3.2, 18.3, -3.2, 3.2, 18.6, 3.2, 'roofpink'); T(-2, 18.6, -2, 2, 19.4, 2, 'roofpink'); // posts, a roof over the bell
    D.box(-41.3, 16.9, 15.2, 1.4, 1.2, 1.4, 'gold'); D.box(-41.3, 17.85, 15.2, 0.2, 0.7, 0.2, 'metal'); } // the bell
  spawns.push([-31, 0.2, 15], [-41.3, 0.2, 15.2]);
  // the lot by the canyon (north): the water tower, a wagon, a trough; (south): the wind pump, hay
  waterTank(B, D, -14, -22, 7.5); wagon(B, D, -16, -12.6, true); add(-12, 0, 14, -9.4, 0.8, 15.2, 'wood');
  windpump(B, D, -14, 24); hay(B, -20, 30, 5); wagon(B, D, -24, 40, false, false);
  // Main Street clutter: a broken wagon, barrels, crates, hitching rails, troughs
  wagon(B, D, -58, 3.2, true, false); for (const [x, z] of [[-40, -5.5], [-39.2, -6.3], [-76, 6], [-22, 5.2]]) B.box(x, 0.6, z, 0.75, 1.2, 0.75, 'barrel');
  cratePile(B, -33, -7.8, 4, rv); cratePile(B, -71, 5.8, 3, rv);
  for (const [x0, x1, z] of [[-90, -82, -8.6], [-50, -42, -8.6], [-88, -80, 8.6], [-70, -62, 8.6]]) add(x0, 0, z - 0.08, x1, 0.95, z + 0.08, 'wood');
  // ---- the north back lots: the corral, the blacksmith, the outhouses, the mine's rail spur and its loading dock
  for (const [x0, z0, x1, z1] of [[-94, -52, -70, -52], [-94, -32, -84, -32], [-80, -32, -70, -32]]) add(x0, 0, z0 - 0.1, x1, 1.3, z1 + 0.1, 'wood');
  for (const x of [-94, -70]) add(x - 0.1, 0, -52, x + 0.1, 1.3, -32, 'wood');
  hay(B, -88, -44, 4); hay(B, -76, -40, 3, false); add(-84, 0, -47, -81.5, 0.75, -46, 'wood'); D.add(-83.8, 0.75, -46.8, -81.7, 0.77, -46.2, 'water');
  { const S2 = B.local(-57, -42, 0); for (const sx of [-1, 1]) for (const sz of [-1, 1]) S2.B(sx * 4.5, 1.6, sz * 3, 0.3, 3.2, 0.3, 'wood'); S2(-5, 3.2, -3.4, 5, 3.45, 3.4, 'roofg');
    S2(-4.5, 0, -3.2, -1.5, 1.4, -1.0, 'brick'); D.box(-57 - 3, 1.45, -42 - 2.1, 1.6, 0.1, 1.2, 'neonred'); S2(1.0, 0, -0.5, 2.6, 0.8, 0.5, 'metal'); S2(0.8, 0.8, -0.3, 2.8, 1.05, 0.3, 'metal'); } // the forge (red hot), the anvil
  for (const x of [-48, -45.6]) { add(x - 0.7, 0, -57.2, x + 0.7, 2.4, -55.8, 'wood'); add(x - 0.8, 2.4, -57.3, x + 0.8, 2.55, -55.7, 'roofg'); D.add(x - 0.15, 1.8, -55.79, x + 0.15, 2.0, -55.75, 'yellow'); } // outhouses (the moon's a yellow slot)
  for (let x = -40; x < -7; x += 0.7) D.add(x, 0.03, -61.2, x + 0.25, 0.08, -58.8, 'wood');
  for (const s of [-1, 1]) D.add(-40, 0.08, -60 + s * 0.75 - 0.06, -7, 0.2, -60 + s * 0.75 + 0.06, 'metal'); // the spur
  add(-44, 0, -66.5, -32, 1.2, -61.6, 'wood'); stairs(W, -42, -40.5, -61.6, 1, 0, 1.2, 'wood', 0.5); // the loading dock
  for (const x of [-26, -19]) { add(x - 0.8, 0.2, -60.7, x + 0.8, 1.3, -59.3, 'rust'); D.add(x - 0.6, 1.3, -60.5, x + 0.6, 1.55, -59.5, 'rock'); } // ore carts
  for (const [x, z, h] of [[-62, -60, 4.2], [-52, -66, 3.6], [-30, -46, 4.6], [-90, -60, 3.8], [-16, -40, 4]]) saguaro(W, x, z, h);
  // the north-west corner: rock outcrops to fight round, the camp
  for (const [x, z, sx, sy, sz] of [[-80, -78, 9, 4.5, 6], [-62, -86, 6, 3, 8], [-40, -80, 7, 5.5, 5], [-22, -88, 10, 3.5, 6], [-90, -92, 5, 6, 5]]) { W.B(x, sy / 2, z, sx, sy, sz, 'rock'); W.B(x + sx * 0.15, sy + 0.4, z - sz * 0.1, sx * 0.6, 0.8, sz * 0.6, 'rock'); }
  for (const [x, z, c] of [[-60, -94, 'cloth'], [-52, -94, 'toypink']]) tent(W, x, z, c);
  // ---- the south back lots: the cemetery (picket fence, graves, a dead tree, a crypt), the stagecoach that didn't make it
  for (const [x0, z0, x1, z1] of [[-90, 36, -58, 36.15], [-90, 62, -58, 62.15]]) add(x0, 0, z0, x1, 1.0, z1, 'picket');
  add(-90, 0, 36.15, -89.85, 1.0, 62, 'picket'); add(-58.15, 0, 36.15, -58, 1.0, 46, 'picket'); add(-58.15, 0, 50, -58, 1.0, 62, 'picket');
  let k = 0; for (let gx = -86; gx <= -64; gx += 4.4) for (let gz = 41; gz <= 58; gz += 5.6) if (!(gx > -76 && gx < -70 && gz < 48)) grave(W, gx, gz, k++);
  add(-75, 0, 40, -70, 3.0, 44, 'stone'); add(-75.3, 3.0, 39.7, -69.7, 3.4, 44.3, 'stone'); // the crypt
  { const tx = -62, tz = 56; W.B(tx, 2.2, tz, 0.5, 4.4, 0.5, 'burnt'); W.B(tx + 0.9, 3.6, tz, 1.6, 0.25, 0.25, 'burnt'); W.B(tx - 0.7, 3.0, tz + 0.4, 0.25, 0.25, 1.2, 'burnt'); }
  wagon(B, D, -46, 46, false, true); B.box(-46, 0.6, 50.5, 0.75, 1.2, 0.75, 'barrel');
  for (const [x, z, h] of [[-38, 56, 4.4], [-24, 66, 3.6], [-86, 72, 4]]) saguaro(W, x, z, h);
  for (const [x, z, sx, sy, sz] of [[-80, 82, 8, 4, 7], [-56, 88, 7, 5, 6], [-30, 80, 9, 3.4, 6], [-14, 90, 6, 4.8, 5]]) { W.B(x, sy / 2, z, sx, sy, sz, 'rock'); W.B(x - sx * 0.15, sy + 0.35, z + sz * 0.1, sx * 0.55, 0.7, sz * 0.55, 'rock'); }
  for (const [x, z, c] of [[-20, 94, 'toyteal'], [-12, 94, 'cloth']]) tent(W, x, z, c);
  // ---- the open ground between it all: the old fort (NW), the mission (SW), adobe huts, the canyon's rims
  ruin(B, -66, -90, -44, -70, rv, 3.2); watchtower(B, -46.5, -72.5, 7.5); // the fort that was here before the town
  W(-60, 0, -86, -57, 1.3, -83, 'crate'); W(-52, 0, -80, -48.6, 0.9, -78.4, 'wood'); cart(W, -62, -76, true);
  for (const [x, z, rot] of [[-86, -66, 0], [-30, -72, 1], [-16, -80, 0]]) adobeHut(B, D, x, z, rot, 6, 5, rv() < 0.5 ? 'adobe' : 'sideorange');
  { // the mission: a ruined chapel, its front still standing (an arched gap), the side walls half gone, a bell arch
    const M = B.local(-44, 80, 0);
    M(-7, 0, -6, -1.4, 7, -5.4, 'adobe'); M(1.4, 0, -6, 7, 7, -5.4, 'adobe'); M(-1.4, 4.2, -6, 1.4, 7, -5.4, 'adobe'); M(-2.2, 7, -6, 2.2, 8.6, -5.4, 'adobe'); // the front, the arch
    M(-1.2, 7.3, -6.05, 1.2, 8.3, -5.95, 'burnt'); D.box(-44, 7.8, 80 - 6.25, 0.7, 0.7, 0.3, 'gold'); // the bell hole, the bell in it
    M(-7, 0, -5.4, -6.4, 4.4, 1, 'adobe'); M(-7, 0, 3, -6.4, 2.2, 8, 'adobe'); M(6.4, 0, -5.4, 7, 2.8, -1, 'adobe'); M(6.4, 0, 2, 7, 4.6, 8, 'adobe'); M(-3, 0, 7.4, 4, 1.6, 8, 'adobe');
    M(-4, 0, 1, -1, 1.1, 2, 'stone'); M(1.5, 0, 3, 4, 0.7, 4, 'stone'); // fallen stones
  }
  for (const [x, z, rot] of [[-80, 86, 1], [-22, 74, 0], [-62, 70, 2]]) adobeHut(B, D, x, z, rot, 6, 5, rv() < 0.5 ? 'adobe' : 'sidemint');
  // the east bank's south: the trading post, a corral, the circle of wagons, huts, a wind pump
  frontier(B, D, 66, 40, 3, 14, 10, 2, { paint: 'sidepink', sign: 'adgeneral', balcony: true, awning: 'toyteal' }); spawns.push([66, 0.2, 40]);
  for (const [x0, z0, x1, z1] of [[74, 50, 90, 50], [74, 62, 80, 62], [84, 62, 90, 62]]) add(x0, 0, z0 - 0.1, x1, 1.3, z1 + 0.1, 'wood'); for (const x of [74, 90]) add(x - 0.1, 0, 50, x + 0.1, 1.3, 62, 'wood'); hay(B, 82, 56, 4);
  { const cx = 80, cz = 80; for (const [dx, dz, ax] of [[-5, 0, false], [5, 0, false], [0, -5, true], [0, 5, true]]) wagon(B, D, cx + dx, cz + dz, ax, true); cratePile(B, cx - 1.2, cz - 0.6, 3, rv); B.box(cx + 2.8, 0.6, cz + 2.8, 0.75, 1.2, 0.75, 'barrel'); } // circled up
  for (const [x, z, rot] of [[22, 88, 0], [52, 92, 2], [14, 30, 1]]) adobeHut(B, D, x, z, rot, 6, 5, rv() < 0.5 ? 'adobe' : 'sidelemon');
  windpump(B, D, 12, 50);
  W(30, 0, -44, 36, 2.6, -40, 'stone'); W(29.8, 2.6, -44.2, 36.2, 2.9, -39.8, 'roofg'); W(30.4, 0, -40.1, 31.8, 1.0, -39.6, 'toyred'); // the powder store (the red crates are the reason it's stone)
  for (const [x, z] of [[38, -44], [39.2, -42.6]]) B.box(x, 0.45, z, 0.9, 0.9, 0.9, 'toyred');
  // the canyon's rims: boulders between the crossings, a rail fence here and there (it's a long way down)
  const fenced = (z, s) => (z + s / 2 > -31 && z - s / 2 < -17) || (z + s / 2 > 23 && z - s / 2 < 37); // (where the rail fences are)
  B.boxes.arch.push({ id: 'rocks_desert', p: [0, 0, 0], r: 0 }); const RK = { av: 'rocks_desert', ai: B.boxes.arch.length - 1 }; // the rim boulders and the far formations: one Blender rock model for the map (look only)
  for (const sx of [-1, 1]) { const ex = sx * 8.4; boulders(B, ex, -96, ex, -64, 6, rv, sx, null, RK); boulders(B, ex, -54, ex, -8, 8, rv, sx, fenced, RK); boulders(B, ex, 8, ex, 54, 8, rv, sx, fenced, RK); boulders(B, ex, 66, ex, 96, 6, rv, sx, null, RK); // (on the lip: no strip between a rock and the drop to get stuck in)
    for (const [z0, z1] of [[-30, -18], [24, 36]]) { for (let z = z0; z <= z1; z += 3) B.box(ex - sx * 0.6, 0.6, z, 0.2, 1.2, 0.2, 'wood'); add(ex - sx * 0.6 - 0.05, 0.85, z0, ex - sx * 0.6 + 0.05, 0.95, z1, 'wood'); } }
  // ---- over the canyon
  trestle(B, D, -7, 7, -60);
  stoneBridge(B, D, -7, 7, 0, 10);
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) { const px = sx * 7.8, pz = sz * 5; B.box(px, 1.2, pz, 2, 2.4, 1.6, 'stone'); D.box(px, 2.5, pz, 2.2, 0.2, 1.8, 'roofg'); D.box(px, 2.85, pz, 0.5, 0.5, 0.5, 'light'); }
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) B.add(sx > 0 ? 6.8 : -7.6, 0, sz > 0 ? 5.8 : -8.8, sx > 0 ? 7.6 : -6.8, 1.0, sz > 0 ? 8.8 : -5.8, 'stone'); // wing walls on the lip out from each gatepost (the fights at the bridge's ends were knocking people in) // its gateposts, a lantern on each (and no squeezing round the end of a parapet on the lip)
  ropeBridge(B, D, -7, 7, 60);
  for (const x of [-7.8, 7.8]) for (const [z0, z1] of [[-63.6, -62.2], [-57.8, -54.4], [54.4, 58.4], [61.6, 65.6]]) lipFence(B, x, z0, z1); // the lip beside the trestle's and the rope bridge's ends
  add(-1.2, 0.2, -62.2, 0.4, 1.4, -60.6, 'rust'); D.add(-1.0, 1.4, -62.0, 0.2, 1.65, -60.8, 'rock'); // a cart that jumped the trestle's rails, stuck on one, half over the edge (cover, and a lane past it)
  B.box(-12, 0.15, 33, 2.5, 0.3, 2.5, 'pad', { pad: [26, 18, 0] }); B.box(12, 0.15, -33, 2.5, 0.3, 2.5, 'pad', { pad: [-26, 18, 0] }); // jump pads: over the canyon the fast way
  // ---- EAST BANK: Mine Square (the assay office, the mine company's offices, the well, stalls, the founder's cart)
  add(7, 0, -18, 44, 0.03, 18, 'dirtroad'); add(44, 0, 12, 92, 0.03, 22, 'dirtroad'); add(84, 0, -6, S, 0.03, 12, 'dirtroad');
  frontier(B, D, 22, -26.2, 2, 14, 12, 1, { paint: 'adobe', sign: 'adassay', awning: 'cloth' });
  frontier(B, D, 51, -4, 3, 16, 12, 2, { paint: 'brick', sign: 'admine', balcony: true, awning: 'toyred' }); spawns.push([51, 0.2, -4]); // (its front on the square)
  add(20.8, 0, -1.2, 23.2, 0.9, 1.2, 'stone'); D.add(21.2, 0.9, -0.8, 22.8, 0.92, 0.8, 'water'); for (const [x, z] of [[20.9, -1.1], [23.1, -1.1], [20.9, 1.1], [23.1, 1.1]]) B.box(x, 1.9, z, 0.18, 2.0, 0.18, 'wood'); add(20.4, 2.9, -1.6, 23.6, 3.1, 1.6, 'roofg'); // the well
  add(31, 0, 4, 35, 1.4, 8, 'stone'); add(31.3, 1.4, 4.4, 34.7, 3.0, 7.6, 'rust'); D.add(31.5, 3.0, 4.6, 34.5, 3.4, 7.4, 'gold'); // the founder's ore cart, on a plinth (full of gold. painted)
  for (const [x, z, rot] of [[14, 10, 0], [26, 12.5, 0]]) stall(W, x, z, rot, rv);
  for (const [x, z] of [[36, -12], [37, -14.5], [12, -14]]) B.box(x, 0.6, z, 0.75, 1.2, 0.75, 'barrelr');
  spawns.push([22, 0.2, -26], [30, 0.2, -6]);
  // ---- the mine: the mesa (a tunnel west to east into it, a side chamber with the shaft, the headframe on top)
  const MZ0 = -96, MZ1 = -54;
  add(28, 0, -58, 84, 6, MZ1, 'rock'); // south of the tunnel
  add(28, 0, MZ0, 50, 6, -62, 'rock'); add(58, 0, MZ0, 84, 6, -62, 'rock'); add(50, 0, MZ0, 58, 6, -70, 'rock'); // north of it (the chamber's room left in it)
  add(28, 3.6, -62, 58, 6, -58, 'rock'); add(58, 0, -62, 84, 6, -58, 'rock'); add(50, 3.6, -70, 58, 6, -62, 'rock'); // the tunnel's roof, its end, the chamber's roof
  add(40, 6, MZ0, 76, 12, -74, 'rock'); // the upper tier
  for (const [y0, y1] of [[2.4, 2.8], [4.8, 5.1]]) D.add(27.95, y0, MZ0, 28.0, y1, -62, 'dirt'); // bands in the rock face
  stairs(W, 25, 28, -50, -1, 0, 6, 'rock', 0.5); stairs(W, 37, 40, -72, -1, 6, 12, 'rock', 0.5); // rock steps up both tiers
  for (let x = 28.4; x < 58; x += 0.7) D.add(x, 0.03, -61.2, x + 0.25, 0.08, -58.8, 'wood');
  for (const s of [-1, 1]) D.add(7, 0.08, -60 + s * 0.75 - 0.06, 58, 0.2, -60 + s * 0.75 + 0.06, 'metal'); // the mine rails, in from the trestle
  for (let x = 32; x < 58; x += 8) D.add(x, 3.3, -60.4, x + 0.8, 3.6, -59.6, 'lamp');
  for (const x of [38, 47]) { add(x - 0.8, 0.2, -60.7, x + 0.8, 1.3, -59.3, 'rust'); D.add(x - 0.6, 1.3, -60.5, x + 0.6, 1.55, -59.5, 'rock'); }
  for (const [x0, z0, x1, z1] of [[52.6, -68.4, 56.4, -68.2], [52.6, -64.8, 56.4, -64.6]]) add(x0, 0, z0, x1, 1.0, z1, 'hazard'); // the shaft (two rails: the sides are open. it's a mine)
  D.add(51.5, 1.3, -69.9, 53.5, 2.3, -69.85, 'adshred', { fit: 1 });
  B.add(50.4, 0, -69.8, 52, 1.6, -68.6, 'toyred'); B.add(56.6, 0, -69.6, 57.8, 1.0, -68.4, 'toyred'); // crates of something loud
  add(27.7, 3.6, -63, 28, 4.4, -57, 'wood'); D.add(27.62, 3.75, -61.9, 27.68, 4.3, -58.1, 'admine', { fit: 1 }); // the mine mouth's lintel, its sign
  headframe(B, D, 46, 6, -66, 14);
  spawns.push([40, 0.2, -60], [51.5, 0.2, -66]);
  // ---- the depot: the railway north-south past the mesa, the train stopped at the platform, the station, a water tank
  train(B, D, 70, -52);
  add(73.2, 0, -48, 78, 1.1, -10, 'wood'); stairs(W, 74, 77, -10, 1, 0, 1.1, 'wood', 0.5);
  frontier(B, D, 86, -32, 3, 16, 10, 1, { paint: 'sidelemon', sign: 'addepot', awning: 'roofg', roofAccess: true });
  frontier(B, D, 87, -17, 3, 10, 12, 1, { paint: 'wood', front: 1.2, awning: 'wood' }); // the freight shed (and nobody sees the west gate from behind the depot)
  waterTank(B, D, 63, 30, 7);
  for (const s of [-1, 1]) D.add(66.5, 0.03, 12 + (s > 0 ? 10 : 0) - 0.3, 73.5, 0.05, 12 + (s > 0 ? 10 : 0) + 0.3, 'white'); // the level crossing's lines
  { const X = B.local(75, 11, 0); X.B(0, 1.6, 0, 0.2, 3.2, 0.2, 'white'); X.B(0, 2.9, -0.11, 1.6, 0.3, 0.1, 'toyred'); } // its sign
  hay(B, 88, 20, 5, false); cratePile(B, 90, -8, 5, rv); wagon(B, D, 92, 32, true, true);
  // the freight yard behind the station (team 2): a row of containers walls it off from the town, open at both ends
  container(B, 94, -38, true, 2, ['containerb', 'containerr']); container(B, 94, -24.7, true, 1, ['containerg'], 11); // (a 1.8 m gap between them: the spawn's back door)
  const east = [[97.3, 0.2, -40], [97.3, 0.2, -36], [97.3, 0.2, -32], [97.3, 0.2, -28], [97.3, 0.2, -24], [96, 0.2, -43], [98.4, 0.2, -30]];
  // ---- the oasis: the pond (a real one now: the ground dips under it, over your head in the middle. shapeGround below digs it), palms, a dock, the camp, rocks
  D.add(21, -0.3, 47, 51, -0.25, 75, 'water'); // (a rectangle of water under the sand: only where the ground dips below it does it show)
  add(30, 0.06, 66, 33, 0.5, 74, 'wood'); add(30.5, 0.06, 74, 32.5, 0.6, 74.6, 'wood'); // the dock (and the board across its end)
  add(30.2, -4.6, 66.2, 32.8, 0.06, 72, 'wood'); // ...and what it stands on, down to the pond's bed (solid: nobody wades in under the deck and pops up through it)
  for (const [x, z] of [[22, 48], [50, 50], [21, 64], [51, 68], [36, 76], [44, 46]]) palm(W, x, z, 6 + rv() * 3, rv);
  for (const [x, z, c] of [[62, 70, 'leopard'], [70, 78, 'toyyellow'], [58, 84, 'cloth']]) tent(W, x, z, c);
  for (const [x, z, sx, sy, sz] of [[16, 40, 4, 2.4, 3], [56, 56, 5, 3, 4], [40, 86, 8, 3.6, 5], [78, 60, 7, 5, 6], [88, 86, 9, 4.4, 7], [16, 84, 6, 3.4, 5]]) { W.B(x, sy / 2, z, sx, sy, sz, 'rock'); W.B(x + sx * 0.12, sy + 0.35, z, sx * 0.55, 0.7, sz * 0.6, 'rock'); }
  for (const [x, z, h] of [[60, 44, 4.2], [74, 46, 3.4], [20, 30, 3.8], [86, 52, 4.6]]) saguaro(W, x, z, h);
  spawns.push([36, 0.2, 44], [64, 0.2, 76], [12, 0.2, 72], [80, 0.2, 40]);
  // the open spots in between
  spawns.push([-86, 0.2, -40], [-58, 0.2, -42], [-36, 0.2, -50], [-70, 0.2, 52], [-30, 0.2, 48], [-56, 0.2, 0], [-20, 0.2, 0], [18, 0.2, 0], [-80, 0.2, -86], [-40, 0.2, 90]);
  const west = [[-94, 0.2, -6], [-94, 0.2, -2], [-94, 0.2, 2], [-94, 0.2, 6], [-90, 0.2, -4.5], [-90, 0.2, 4.5], [-96, 0.2, 0]];
  spawns.push(west[0], west[3], east[0], east[4]);
  // ---- the ground between it all (look only): dirt patches, sagebrush, the odd tumbleweed. never inside anything
  { const rg = rng(9192), clear = (x, z, r) => !B.boxes.some((q) => q.max[1] > 0.06 && q.min[1] < 12 && q.mat !== 'dirtroad' && x + r > q.min[0] && x - r < q.max[0] && z + r > q.min[2] && z - r < q.max[2]);
    const ok = (x, z) => Math.abs(x) > 10 && !(x > 18 && x < 54 && z > 44 && z < 78); // (off the canyon's rims, off the oasis)
    for (let i = 0; i < 60; i++) { const x = -96 + rg() * 192, z = -96 + rg() * 192, w = 2 + rg() * 5, d = 2 + rg() * 5; if (ok(x, z) && clear(x, z, Math.max(w, d) / 2)) D.box(x, 0.0075, z, w, 0.015, d, 'dirt'); }
    for (let i = 0; i < 140; i++) { const x = -96 + rg() * 192, z = -96 + rg() * 192, s = 0.4 + rg() * 0.6; if (ok(x, z) && clear(x, z, s)) { D.box(x, s * 0.35, z, s, s * 0.7, s * 0.9, rg() < 0.5 ? 'hedge' : 'leaves2'); if (rg() < 0.4) D.box(x + s * 0.4, s * 0.25, z - s * 0.3, s * 0.6, s * 0.5, s * 0.5, 'leaves2'); } }
    for (let i = 0; i < 14; i++) { const x = -96 + rg() * 192, z = -96 + rg() * 192; if (ok(x, z) && clear(x, z, 0.6)) D.obb(x, 0.4, z, 0.8, 0.8, 0.8, rg() * 3, 'burnt'); }
  }
  // ---- outside: sand all the way out (no cliff), the canyon running on as a ravine with a river at the bottom
  groundHoles(B, -300, -300, 300, 300, -2, 0, 'sand', [[-S, -S, S, S], [-7, -284, 7, -S], [-7, S, 7, 284]]);
  for (const x0 of [-9, 7]) { B.add(x0, -66, -S, x0 + 2, -2, S, 'rock'); D.add(x0, -66, -284, x0 + 2, -2, -S, 'rock'); D.add(x0, -66, S, x0 + 2, -2, 284, 'rock'); } // the walls: solid in town (fall in, grapple the wall; you don't swing about under the town)
  for (const sz of [-1, 1]) D.add(-9, -66, sz > 0 ? 284 : -288, 9, -2, sz > 0 ? 288 : -284, 'rock');
  D.add(-7, -67, -284, 7, -66, 284, 'sand'); D.add(-3.5, -66, -284, 3.5, -65.8, 284, 'water');
  const ro = rng(9091); // (the outside's own dice: the town can change without the desert round it moving)
  for (const z of [-180, -40, 20, 130, 220]) D.add(-5 + ro() * 3, -65.8, z, -1 + ro() * 3, -64.6 + ro(), z + 2 + ro() * 3, 'rock');
  D.add(-4, -65.8, 66, 4, -65.3, 68.5, 'wood'); // somebody's old bridge
  B.add(-300, 0, -3, -S, 0.03, 3, 'dirtroad'); B.add(S, 0, -3, 300, 0.03, 3, 'dirtroad'); // the road on out of both gates
  for (const sx of [-1, 1]) D.add(sx > 0 ? 300 : -760, 0, -3, sx > 0 ? 760 : -300, 0.03, 3, 'dirtroad');
  // ---- the desert round the town (render-only): dunes, rock formations, a caravan camped outside the east gate, more palms
  for (let i = 0; i < 46; i++) { const a = ro() * Math.PI * 2, d = 130 + ro() * 230, x = Math.cos(a) * d, z = Math.sin(a) * d, w = 30 + ro() * 60, dd = 18 + ro() * 36, h = 5 + ro() * 12;
    if (Math.abs(x) < 26 || Math.abs(z) < 14 || (x + w / 2 > -160 && x - w / 2 < -95) || (Math.abs(x) - w / 2 < 106 && Math.abs(z) - dd / 2 < 106)) continue; dune(D, x, z, w, dd, h); } // (not on the track west of the town, traffic.js; not into the town)
  for (let i = 0; i < 16; i++) { const a = ro() * Math.PI * 2, d = 190 + ro() * 220, x = Math.cos(a) * d, z = Math.sin(a) * d; if (Math.abs(x) < 30 || Math.abs(z) < 20 || (x > -185 && x < -80)) continue; rocks(D, x, z, 12 + ro() * 20, ro, RK); }
  for (const [x, z, c] of [[124, -14, 'cloth'], [134, 10, 'toyyellow'], [146, -6, 'leopard']]) tent(Dw, x, z, c);
  for (const [x, z, ax] of [[118, 18, true], [128, 22, false], [142, 16, true], [152, 0, false]]) camel(Dw, x, z, ax);
  Dw(132, 0, -2, 134, 0.4, 0, 'stone'); Dw(132.5, 0.4, -1.5, 133.5, 1.0, -0.5, 'neonred'); // the campfire
  for (let i = 0; i < 30; i++) { const a = ro() * Math.PI * 2, d = 110 + ro() * 120, x = Math.cos(a) * d, z = Math.sin(a) * d; if (Math.abs(x) < 20 || Math.abs(z) < 10 || (x > -150 && x < -118)) continue; palm(Dw, x, z, 6 + ro() * 4, ro); }
  D.add(-260, 0, -210, -230, 26, -180, 'toyface', { fit: 1 }); // something enormous, half buried, smiling
  horizon(D, -300, -300, 300, 300, 1500, 'sand');
  // ---- the ground gets its shape last (shared/terrain.js): dunes, hollows and washes between the buildings. the streets, the
  // canyon's lip and everything big stay level; cacti, crates and graves ride it
  shapeGround(B, D, { region: [-S, -S, S, S], mat: 'sand', seed: 1887, up: 2.3, down: 1.3,
    washes: [{ pts: [[-94, -84], [-70, -86], [-50, -74], [-30, -78], [-12, -68]], w: 3.2, d: 1.2 }, { pts: [[92, 86], [70, 80], [52, 62], [34, 58], [14, 46]], w: 3.2, d: 1.2 }], // two dry washes down to the canyon
    ponds: [{ c: [36, 61], r: [11, 9.5], d: 3.6, wl: 0.25, box: [21, 47, 51, 75], seed: 3 }], // the oasis: wade in, then it's well over your head and you float (map.pools)
    points: [...new Set([...spawns, ...west, ...east])] });

  const bounds = [-S - 1, -S - 1, S + 1, S + 1];
  let graph = null;
  const map = { name: 'Desert', size: 'large', boxes: B.boxes, deco: D.boxes, killY: -65.6, fall: 'river', bounds, floorY: -69, pools: [{ box: [21, 47, 51, 75], top: -0.25 }],
    sky: { top: 0x3f7fd0, mid: 0xf2d9a0, bot: 0x6a4a28, fog: 0xead6a6 }, fogNear: 130, fogFar: 520, spawns, teamSpawns: { att: west, def: east },
    gates: [[-106, 0, -94, 0], [106, 0, 94, 0]], // the town's two gates (a bot out past the wall heads for one)
    edgeGuard: true, // bots don't dodge-jump next to the canyon (server.js: brBotEdge in every mode here)
    // bots: a walk graph over the town (1 m cells), over the bridges, round everything
    peekGraph() { return graph; }, dropGraph() { graph = null; }, get graph() { return graph || (graph = buildNav(B.boxes, { x0: bounds[0], z0: bounds[1], n: bounds[2] - bounds[0], cell: 1, levels: [0], band: 0.5, keep: (x, z) => !outOfBounds(map, [x, 0, z]) })); },
  };
  return map;
}

// ------------------------------------------------------------ DESERT S&D: Dry Gulch, the payroll job (Plant & Defuse).
// the bandits (attackers) come in on the stage by the west gate; the posse (defenders) holds the east bank from behind
// the jail. the canyon's the front line and its three ways over are the three lanes. north: the mine's trestle, straight
// into A (the mine head: the headframe over the capped shaft, the ore loader, the powder store, the mine's tunnel).
// middle: the stone bridge into Mine Square (mid), then up Mine Road to A or down Depot Road to B. south: the rope bridge
// onto the end of the platform, B (the depot: the payroll train stopped at the platform, the station). the posse gets to
// either site ~7 s first and swaps sites through the square; the bandits' way round is back over their own bank. the
// stage office and the jail stand between the spawns, a solid wall inside each (no look straight through the windows)
function desertSD() {
  const B = builder(), D = builder();
  const r = rng(9494), rv = rng(9393), W = B.local(0, 0, 0), Dw = D.local(0, 0, 0), add = B.add;
  const X0 = -96, X1 = 72, Z0 = -62, Z1 = 62, bounds = [X0, Z0, X1, Z1];
  const spawns = [];
  // ---- the ground, the canyon (x -7..7; its walls solid: fall in and grapple out), the river a long way down
  add(-300, -2, -300, -7, 0, 300, 'sand'); add(7, -2, -300, 300, 0, 300, 'sand');
  for (const x0 of [-9, 7]) add(x0, -66, -300, x0 + 2, -2, 300, 'rock');
  D.add(-7, -67, -300, 7, -66, 300, 'sand'); D.add(-3.5, -66, -300, 3.5, -65.8, 300, 'water');
  for (const z of [-150, -34, 22, 118]) D.add(-5 + rv() * 3, -65.8, z, -1 + rv() * 3, -64.6 + rv(), z + 2 + rv() * 3, 'rock');
  // ---- the town wall (its top's over the ceiling): the west gate the stage came in by (shut behind it), north and south
  // walls cut by the canyon (a tower on each lip), the east wall behind the jail; the mesa's the north edge east of the canyon
  const wall = (x0, z0, x1, z1) => add(x0, 0, z0, x1, 9, z1, 'adobe');
  wall(X0 - 0.6, Z0 - 0.6, X0 + 0.6, -7); wall(X0 - 0.6, 7, X0 + 0.6, Z1 + 0.6);
  wall(X0 + 0.6, Z0 - 0.6, -10, Z0 + 0.6); wall(X0 + 0.6, Z1 - 0.6, -10, Z1 + 0.6); wall(10, Z1 - 0.6, X1 - 0.6, Z1 + 0.6); wall(X1 - 0.6, -52, X1 + 0.6, Z1 - 0.6);
  for (const [x, z] of [[X0, Z0], [X0, Z1], [X1, Z1], [-9, Z0], [-9, Z1], [9, Z1]]) B.box(x, 6, z, 4, 12, 4, 'adobe');
  for (const sz of [-1, 1]) add(X0 - 3, 0, sz > 0 ? 6.5 : -11, X0 + 3, 12, sz > 0 ? 11 : -6.5, 'adobe'); // the gate's towers
  add(X0 - 0.3, 0, -6.5, X0 + 0.3, 6.2, 6.5, 'wood'); add(X0 - 0.6, 6.2, -6.5, X0 + 0.6, 9, 6.5, 'adobe'); // the gate, shut
  for (const y of [1.2, 4.6]) D.add(X0 + 0.3, y, -6.3, X0 + 0.34, y + 0.3, 6.3, 'metal'); // its iron bands
  { const mer = (a, b, fixed, alongX, out) => { for (let t = a; t <= b; t += 3) if (alongX) D.add(t - 0.6, 9, out > 0 ? fixed + 0.1 : fixed - 0.6, t + 0.6, 10, out > 0 ? fixed + 0.6 : fixed - 0.1, 'adobe'); else D.add(out > 0 ? fixed + 0.1 : fixed - 0.6, 9, t - 0.6, out > 0 ? fixed + 0.6 : fixed - 0.1, 10, t + 0.6, 'adobe'); };
    mer(X0 + 4, -13, Z0, true, -1); mer(X0 + 4, -13, Z1, true, 1); mer(13, X1 - 4, Z1, true, 1); mer(Z0 + 4, -14, X0, false, -1); mer(14, Z1 - 4, X0, false, -1); mer(-49, Z1 - 4, X1, false, 1); } // battlements, on the outer edge

  // ---- WEST BANK. the stage stop (the bandits' spawn) inside the shut gate; the stage office across the end of the street
  const att = [[-91, 0.2, -6], [-91, 0.2, -2], [-91, 0.2, 2], [-91, 0.2, 6], [-87, 0.2, -4], [-87, 0.2, 0], [-87, 0.2, 4]];
  add(X0 + 0.6, 0, -10, -80.6, 0.03, 10, 'dirtroad'); add(-68, 0, -5.4, -7, 0.03, 5.4, 'dirtroad');
  wagon(B, D, -86, -13.5, true, true); // the stage (it made it. just)
  for (const [x, z] of [[-93, 12], [-92.2, 12.8], [-80, 12.6]]) B.box(x, 0.6, z, 0.75, 1.2, 0.75, 'barrel');
  add(-84, 0, 12, -81.5, 0.8, 13.2, 'wood'); D.add(-83.8, 0.8, 12.2, -81.7, 0.82, 13.0, 'water'); // a trough
  const stage = frontier(B, D, -73, 0, 3, 16, 10, 1, { paint: 'sidemint', sign: 'adstage', awning: 'toyyellow', roofAccess: false });
  { const L = stage.L; L(-7.7, 0.12, -1.15, -4.4, 3.6, -0.85, 'wood'); L(-3.0, 0.12, -1.15, 7.7, 3.6, -0.85, 'wood'); // the ticket wall (its door off to one side)
    L(-2.6, 0.12, -3.6, 2.6, 1.1, -3.0, 'wood'); L(-2.6, 1.1, -3.65, 2.6, 1.2, -2.95, 'chrome'); for (const x of [-6.6, -5.6]) L.B(x, 0.5, 2.6, 0.8, 0.76, 2.4, 'crate'); L.B(5.5, 0.6, 3, 1.6, 0.96, 1.0, 'crate'); } // the counter, the luggage
  // Main Street: the saloon, the bank, the general store (north row); the undertaker, the hotel, the livery (south row)
  const north = [[-57, 16, 12, 2, 'sidemint', 'adsaloon', { balcony: true, awning: 'toypink', roofAccess: false }], [-40, 12, 12, 1, 'adobe', 'adbank', { front: 2.6 }], [-26, 10, 10, 1, 'sideorange', 'adgeneral', { awning: 'toyyellow' }]];
  const south = [[-58, 12, 10, 1, 'magenta', 'adundertaker', { front: 1.8 }], [-43, 14, 12, 2, 'sidelemon', 'adhotel', { balcony: true, awning: 'toyteal', roofAccess: false }], [-27, 12, 12, 1, 'wood', 'adlivery', { front: 3.4 }]];
  const bld = {};
  for (const [x, w, d, n, paint, sign, o] of north) bld[sign] = frontier(B, D, x, -8 - d / 2, 2, w, d, n, { paint, sign, ...o });
  for (const [x, w, d, n, paint, sign, o] of south) bld[sign] = frontier(B, D, x, 8 + d / 2, 0, w, d, n, { paint, sign, ...o });
  { const L = bld.adsaloon.L; L(-5.8, 0.12, 3.6, 3, 1.15, 4.6, 'wood'); L(-5.8, 1.15, 3.4, 3, 1.25, 4.8, 'chrome'); L(4.5, 0.12, 2.4, 7.6, 0.6, 5.6, 'wood'); L(5.2, 0.6, 3.6, 7.0, 1.8, 4.6, 'burnt'); // the bar, the stage, a piano
    for (const [tx, tz] of [[-5, -2], [-1, -3.2], [3, -1.5]]) L.B(tx, 0.5, tz, 1.4, 0.76, 1.4, 'wood'); }
  { const L = bld.adbank.L; L(-5.6, 0.12, -1.0, 5.6, 1.2, -0.6, 'wood'); L(-5.6, 1.2, -0.95, 5.6, 2.6, -0.85, 'grid'); // the counter, its bars
    L(-3.6, 0.12, 2.2, -1.2, 3.0, 2.5, 'metal'); L(1.2, 0.12, 2.2, 3.6, 3.0, 2.5, 'metal'); L(-1.2, 2.4, 2.2, 1.2, 3.0, 2.5, 'metal'); // the vault (a doorway in its front),
    L(-3.6, 0.12, 2.5, -3.3, 3.0, 5.6, 'metal'); L(3.3, 0.12, 2.5, 3.6, 3.0, 5.6, 'metal'); L(-3.6, 3.0, 2.2, 3.6, 3.3, 5.6, 'metal'); // sides, roof
    L(1.25, 0.12, 0.5, 1.4, 2.4, 2.15, 'gold'); L(-2.8, 0.12, 4.2, -1.0, 0.9, 5.4, 'gold'); L(0.6, 0.12, 4.4, 2.6, 0.6, 5.4, 'gold'); } // its door open, the gold (cleaned out next)
  { const L = bld.adundertaker.L; for (const cx of [-3.2, -1.9]) L(cx, 0.35, -6.4, cx + 0.8, 2.3, -6.1, 'wood'); } // coffins stood up on the boardwalk
  hay(B, -31, 22.6, 4); camel(W, -24, 23.4, true); // behind the livery
  wagon(B, D, -45, 2.2, true, false); for (const [x, z] of [[-36, -3.6], [-35.2, -4.4], [-62, 3.8], [-18, 3.4]]) B.box(x, 0.6, z, 0.75, 1.2, 0.75, 'barrel');
  cratePile(B, -30, -3.4, 4, r); cratePile(B, -52, 3.6, 3, r);
  // the lot by the canyon: the water tower (north), the wind pump (south), and the jump pads: over into the square, the fast way
  waterTank(B, D, -14, -16, 7.5); windpump(B, D, -14, 18);
  for (const sz of [-1, 1]) B.box(-15, 0.15, sz * 5.6, 2.5, 0.3, 2.5, 'pad', { pad: [26, 18, 0] });
  // ---- the north back lots: the corral, the blacksmith, the outhouses, the rail spur out to the trestle and its dock
  for (const [x0, z0, x1, z1] of [[-90, -50, -74, -50], [-90, -32, -84, -32], [-80, -32, -74, -32]]) add(x0, 0, z0 - 0.1, x1, 1.3, z1 + 0.1, 'wood');
  for (const x of [-90, -74]) add(x - 0.1, 0, -50, x + 0.1, 1.3, -32, 'wood');
  hay(B, -86, -44, 4); hay(B, -78, -40, 3, false); add(-84, 0, -48, -81.5, 0.75, -47, 'wood'); D.add(-83.8, 0.75, -47.8, -81.7, 0.77, -47.2, 'water'); camel(W, -80, -36, false);
  { const S2 = B.local(-58, -44, 0); for (const sx of [-1, 1]) for (const sz of [-1, 1]) S2.B(sx * 4.5, 1.6, sz * 3, 0.3, 3.2, 0.3, 'wood'); S2(-5, 3.2, -3.4, 5, 3.45, 3.4, 'roofg');
    S2(-4.5, 0, -3.2, -1.5, 1.4, -1.0, 'brick'); D.box(-58 - 3, 1.45, -44 - 2.1, 1.6, 0.1, 1.2, 'neonred'); S2(1.0, 0, -0.5, 2.6, 0.8, 0.5, 'metal'); S2(0.8, 0.8, -0.3, 2.8, 1.05, 0.3, 'metal'); } // the forge, the anvil
  for (const x of [-48, -45.6]) { add(x - 0.7, 0, -57.2, x + 0.7, 2.4, -55.8, 'wood'); add(x - 0.8, 2.4, -57.3, x + 0.8, 2.55, -55.7, 'roofg'); D.add(x - 0.15, 1.8, -55.79, x + 0.15, 2.0, -55.75, 'yellow'); } // outhouses
  for (let x = -40; x < -7; x += 0.7) D.add(x, 0, -41.2, x + 0.25, 0.06, -38.8, 'wood');
  for (const s of [-1, 1]) D.add(-40, 0.06, -40 + s * 0.75 - 0.06, -7, 0.2, -40 + s * 0.75 + 0.06, 'metal'); // the spur
  add(-44, 0, -48.5, -32, 1.2, -43.6, 'wood'); stairs(W, -42, -40.5, -43.6, 1, 0, 1.2, 'wood', 0.5); // the loading dock
  for (const x of [-27, -18]) { add(x - 0.8, 0.2, -40.7, x + 0.8, 1.3, -39.3, 'rust'); D.add(x - 0.6, 1.3, -40.5, x + 0.6, 1.55, -39.5, 'rock'); } // ore carts, waiting
  for (const [x, z, sx, sy, sz] of [[-84, -57, 9, 4.5, 6], [-62, -56, 6, 3, 6], [-30, -57, 8, 4, 6], [-18, -52, 5, 2.6, 4]]) { W.B(x, sy / 2, z, sx, sy, sz, 'rock'); W.B(x + sx * 0.15, sy + 0.4, z - sz * 0.1, sx * 0.6, 0.8, sz * 0.6, 'rock'); }
  for (const [x, z, h] of [[-66, -46, 4.2], [-38, -30, 3.6], [-22, -46, 4.4], [-92, -24, 3.8]]) saguaro(W, x, z, h);
  // ---- the south back lots: the church and its bell tower, the cemetery, a wagon that didn't make it
  { const C = B.local(-44, 38, 0); shell(C, 14, 16, 1, 5, 'white', { floor: 'wood', roof: 'roofpink', roofAccess: false, backDoor: true, parapet: false, winSpacing: 3.5 });
    C(-6.4, 5.3, -7.4, 6.4, 6.0, 7.4, 'roofpink'); C(-4.4, 6.0, -7.4, 4.4, 6.7, 7.4, 'roofpink'); C(-2.2, 6.7, -7.4, 2.2, 7.4, 7.4, 'roofpink'); // a stepped roof
    for (let i = 0; i < 4; i++) C(-4 + i * 2.2, 0.12, -1, -2.6 + i * 2.2, 0.6, 5, 'wood'); // pews
    add(-58, 0, 31, -52, 14.4, 37, 'white'); for (const y of [4.6, 9.6]) D.add(-58.04, y, 30.96, -51.96, y + 0.3, 37.04, 'roofpink'); // the bell tower (solid: its top's over the ceiling, a landmark not a perch)
    for (const sx of [-1, 1]) for (const sz of [-1, 1]) D.box(-55 + sx * 2.7, 16.1, 34 + sz * 2.7, 0.3, 3.4, 0.3, 'white'); D.add(-58.2, 17.8, 30.8, -51.8, 18.1, 37.2, 'roofpink'); D.add(-57, 18.1, 32, -53, 18.9, 36, 'roofpink');
    D.box(-55, 16.4, 34, 1.4, 1.2, 1.4, 'gold'); D.box(-55, 17.35, 34, 0.2, 0.7, 0.2, 'metal'); } // the belfry, the bell
  for (const [x0, z0, x1, z1] of [[-90, 34, -62, 34.15], [-90, 58, -62, 58.15]]) add(x0, 0, z0, x1, 1.0, z1, 'picket');
  add(-90, 0, 34.15, -89.85, 1.0, 58, 'picket'); add(-62.15, 0, 34.15, -62, 1.0, 44, 'picket'); add(-62.15, 0, 48, -62, 1.0, 58, 'picket');
  { let k = 0; for (let gx = -86; gx <= -66; gx += 4.4) for (let gz = 38; gz <= 55; gz += 5.6) if (!(gx > -78 && gx < -72 && gz < 46)) grave(W, gx, gz, k++); }
  add(-77, 0, 38, -72, 3.0, 42, 'stone'); add(-77.3, 3.0, 37.7, -71.7, 3.4, 42.3, 'stone'); // the crypt
  { const tx = -66, tz = 52; W.B(tx, 2.2, tz, 0.5, 4.4, 0.5, 'burnt'); W.B(tx + 0.9, 3.6, tz, 1.6, 0.25, 0.25, 'burnt'); W.B(tx - 0.7, 3.0, tz + 0.4, 0.25, 0.25, 1.2, 'burnt'); } // a dead tree
  wagon(B, D, -28, 48, false, true); B.box(-28, 0.6, 52.5, 0.75, 1.2, 0.75, 'barrel');
  for (const [x, z, sx, sy, sz] of [[-84, 22, 4, 2.2, 3], [-20, 56, 6, 3.4, 5], [-50, 56, 7, 3, 5]]) { W.B(x, sy / 2, z, sx, sy, sz, 'rock'); W.B(x - sx * 0.15, sy + 0.35, z + sz * 0.1, sx * 0.55, 0.7, sz * 0.55, 'rock'); }
  for (const [x, z, h] of [[-36, 54, 4.4], [-16, 30, 3.6], [-92, 46, 4]]) saguaro(W, x, z, h);
  // the canyon's west lip: boulders flush with it between the crossings, a rail fence here and there
  const fenced = (z, s) => Math.abs(z) + s / 2 > 17 && Math.abs(z) - s / 2 < 31;
  B.boxes.arch.push({ id: 'rocks_desert_sd', p: [0, 0, 0], r: 0 }); const RK = { av: 'rocks_desert_sd', ai: B.boxes.arch.length - 1 }; // (its rock: one Blender model, look only)
  boulders(B, -8.4, -60, -8.4, -44, 3, r, -1, null, RK); boulders(B, -8.4, -35, -8.4, -10, 5, r, -1, fenced, RK); boulders(B, -8.4, 10, -8.4, 35, 5, r, -1, fenced, RK); boulders(B, -8.4, 44, -8.4, 60, 3, r, -1, null, RK);
  for (const sz of [-1, 1]) { const z0 = sz > 0 ? 18 : -30, z1 = sz > 0 ? 30 : -18; for (let z = z0; z <= z1; z += 3) B.box(-7.8, 0.6, z, 0.2, 1.2, 0.2, 'wood'); add(-7.85, 0.85, z0, -7.75, 0.95, z1, 'wood'); }

  // ---- over the canyon: the trestle (north, the cart that jumped its rails), the stone bridge (its gateposts), the rope bridge
  trestle(B, D, -7, 7, -40);
  add(-1.2, 0.2, -42.2, 0.4, 1.4, -40.6, 'rust'); D.add(-1.0, 1.4, -42.0, 0.2, 1.65, -40.8, 'rock');
  stoneBridge(B, D, -7, 7, 0, 10);
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) { const px = sx * 7.8, pz = sz * 5; B.box(px, 1.2, pz, 2, 2.4, 1.6, 'stone'); D.box(px, 2.5, pz, 2.2, 0.2, 1.8, 'roofg'); D.box(px, 2.85, pz, 0.5, 0.5, 0.5, 'light'); }
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) B.add(sx > 0 ? 6.8 : -7.6, 0, sz > 0 ? 5.8 : -8.8, sx > 0 ? 7.6 : -6.8, 1.0, sz > 0 ? 8.8 : -5.8, 'stone'); // wing walls on the lip out from each gatepost (the fights at the bridge's ends were knocking people in)
  ropeBridge(B, D, -7, 7, 40);
  for (const [z0, z1] of [[-43.6, -42.2], [-37.8, -35.6], [35.6, 38.4], [41.6, 43.6]]) lipFence(B, -7.8, z0, z1); // the west lip beside the trestle's and the rope bridge's ends

  // ---- EAST BANK. Mine Square (mid): the well, the founder's cart; the assay office (north) and the mining company (south)
  add(7, 0, -8.4, 46.4, 0.03, 8.4, 'dirtroad'); add(28, 0, -28, 38, 0.03, -8.4, 'dirtroad'); add(28, 0, 8.4, 37.4, 0.03, 27, 'dirtroad'); // the square, Mine Road, Depot Road
  frontier(B, D, 20, -17, 2, 16, 12, 1, { paint: 'adobe', sign: 'adassay', awning: 'cloth' });
  frontier(B, D, 20, 17, 0, 16, 12, 1, { paint: 'brick', sign: 'admine', awning: 'toyred' });
  add(18.8, 0, -1.2, 21.2, 0.9, 1.2, 'stone'); D.add(19.2, 0.9, -0.8, 20.8, 0.92, 0.8, 'water'); for (const [x, z] of [[18.9, -1.1], [21.1, -1.1], [18.9, 1.1], [21.1, 1.1]]) B.box(x, 1.9, z, 0.18, 2.0, 0.18, 'wood'); add(18.4, 2.9, -1.6, 21.6, 3.1, 1.6, 'roofg'); // the well
  add(31, 0, -2, 35, 1.4, 2, 'stone'); add(31.3, 1.4, -1.6, 34.7, 3.0, 1.6, 'rust'); D.add(31.5, 3.0, -1.4, 34.5, 3.4, 1.4, 'gold'); // the founder's ore cart on its plinth (gold. painted)
  for (const [x, z] of [[25, -6.4], [25.8, -7.2], [41, 6.6], [13, 6.6]]) B.box(x, 0.6, z, 0.75, 1.2, 0.75, 'barrelr');
  cratePile(B, 42, -6.4, 3, r);
  // the jail (the posse's back door onto the square): its desk, then a solid wall (its door at one end), then the cells
  const jail = frontier(B, D, 54, 0, 3, 18, 10, 1, { paint: 'adobe', sign: 'adsheriff', wanted: -2.5, roofAccess: false });
  { const L = jail.L; L(-8.7, 0.12, 0.85, 4.6, 3.6, 1.15, 'adobe'); L(6.0, 0.12, 0.85, 8.7, 3.6, 1.15, 'adobe');
    L(-4.6, 0.12, -3.4, -1.6, 0.85, -2.0, 'wood'); L(2.0, 0.12, -3.6, 4.4, 1.0, -2.6, 'wood'); // the desk, the gun rack's bench
    for (let gx = -4.6; gx < 7.8; gx += 0.45) L(gx, 0.12, 3.0, gx + 0.08, 3.0, 3.08, 'metal'); L(-4.6, 3.0, 3.0, 7.8, 3.4, 3.08, 'metal'); } // the cells (bars)
  // the posse's camp behind the jail (their spawn): the chuck wagon, the horses (camels: it's a budget posse), a fire
  const def = [[64, 0.2, -7], [64, 0.2, -2.5], [64, 0.2, 2.5], [64, 0.2, 7], [68, 0.2, -5], [68, 0.2, 0], [68, 0.2, 5]];
  wagon(B, D, 64, 13.5, true, true); for (const [x, z] of [[62, -12.5], [67, -13]]) camel(W, x, z, true); hay(B, 70, -10, 3, false);
  add(69, 0, 9, 71, 0.4, 11, 'stone'); D.add(69.5, 0.4, 9.5, 70.5, 1.0, 10.5, 'neonred'); // the fire
  // the mine yard between the square and A (the posse's way up): the water tower, timber, a wagon
  waterTank(B, D, 48, -20, 7); add(40, 0, -15, 45, 1.2, -13.4, 'wood'); D.add(40.2, 1.2, -14.8, 44.8, 1.25, -13.6, 'wood'); wagon(B, D, 56, -24, false, false);
  // the freight shed by Depot Road (the posse's way down to B)
  frontier(B, D, 45, 19, 3, 12, 10, 1, { paint: 'wood', front: 1.2, awning: 'wood' }); hay(B, 54, 22, 4, false); cratePile(B, 55, 32, 4, r);
  // the canyon's east lip: a rail fence along the narrow ways by the drop
  for (const [z0, z1] of [[-51.6, -42.2], [-37.8, -10], [10, 38.4], [41.6, 47]]) lipFence(B, 7.8, z0, z1);

  // ---- A: the mine head. the mesa's the north edge: the mine's in it (in at the mouth, along the gallery behind the rock
  // face, out by the posse's end); the headframe over the capped shaft (yellow and black: plant here), the ore loader, the
  // rails in off the trestle (carts on them), the powder store, timber
  add(7, 0, Z0 - 0.6, 24, 10, -52, 'rock'); add(28, 0, -54, 58, 10, -52, 'rock'); add(24, 0, Z0 - 0.6, 62, 10, -58, 'rock'); add(62, 0, Z0 - 0.6, X1 + 0.6, 10, -52, 'rock');
  add(24, 3.6, -58, 62, 10, -54, 'rock'); add(24, 3.6, -54, 28, 10, -52, 'rock'); add(58, 3.6, -54, 62, 10, -52, 'rock'); // the gallery's roof, the mouth's, the far end's
  for (const [y0, y1] of [[2.4, 2.8], [6.2, 6.5]]) D.add(7, y0, -51.95, 24, y1, -51.9, 'dirt'); // bands in the rock face
  for (const x0 of [23.7, 57.7]) { add(x0, 0, -52.3, x0 + 0.5, 3.5, -51.7, 'wood'); add(x0 + 4.1, 0, -52.3, x0 + 4.6, 3.5, -51.7, 'wood'); add(x0, 3.5, -52.3, x0 + 4.6, 4.3, -51.7, 'wood'); } // the timber frames at both ends
  D.add(24.4, 3.6, -51.68, 27.6, 4.2, -51.64, 'admine', { fit: 1 });
  for (let x = 26; x < 60; x += 7) D.add(x, 3.3, -56.4, x + 0.8, 3.5, -55.6, 'lamp'); for (const z of [-53.4]) for (const x of [25.6, 59.6]) D.add(x, 3.3, z - 0.4, x + 0.8, 3.5, z + 0.4, 'lamp');
  for (const [x, z] of [[33, -56.8], [47, -56.6]]) add(x - 0.8, 0.2, z - 0.7, x + 0.8, 1.3, z + 0.7, 'rust'); add(40, 0, -57.6, 42.4, 1.2, -56.6, 'crate'); // carts, crates
  headframe(B, D, 36, 0, -41, 13); add(34.6, 0, -42.4, 37.4, 0.15, -39.6, 'hazard'); // the headframe, the shaft's cap
  { for (const sx of [-1, 1]) for (const sz of [-1, 1]) B.box(22 + sx * 1.7, 1.7, -46 + sz * 1.7, 0.35, 3.4, 0.35, 'wood'); add(20, 3.4, -48, 24, 6.4, -44, 'wood'); // the ore loader: its bin up on legs
    for (const y of [4.2, 5.6]) D.add(19.98, y, -48.02, 24.02, y + 0.15, -43.98, 'rust');
    for (let i = 0; i < 3; i++) D.add(21.5, 3.0 - i * 0.4, -44 + i, 22.5, 3.15 - i * 0.4, -43 + i, 'rust'); } // its chute
  for (let x = 7.2; x < 31; x += 0.7) D.add(x, 0, -41.2, x + 0.25, 0.06, -38.8, 'wood');
  for (const s of [-1, 1]) D.add(7, 0.06, -40 + s * 0.75 - 0.06, 31, 0.2, -40 + s * 0.75 + 0.06, 'metal'); // the rails in off the trestle
  add(31, 0, -41.2, 31.6, 0.9, -38.8, 'wood'); D.add(31.6, 0.3, -40.9, 31.65, 0.7, -39.1, 'toyred'); // the buffer stop
  for (const x of [13, 25.6]) { add(x - 0.8, 0.2, -40.7, x + 0.8, 1.3, -39.3, 'rust'); D.add(x - 0.6, 1.3, -40.5, x + 0.6, 1.55, -39.5, 'rock'); } // ore carts
  add(41, 0, -35.5, 47, 2.6, -30.5, 'stone'); add(40.8, 2.6, -35.7, 47.2, 2.9, -30.3, 'roofg'); D.add(40.96, 0, -33.6, 41.0, 2.0, -32.4, 'toyred'); D.add(40.96, 2.05, -34.4, 41.0, 2.55, -31.6, 'adpowder', { fit: 1 }); // the powder store
  for (const [x, z, y] of [[39.4, -35, 0.45], [39.6, -36.2, 0.45], [39.5, -35.6, 1.35]]) B.box(x, y, z, 0.9, 0.9, 0.9, 'toyred'); // crates of something loud
  add(27.5, 0, -32.2, 32.5, 1.25, -30.6, 'wood'); for (const x of [28.4, 31.6]) D.add(x, 0.02, -32.24, x + 0.2, 1.29, -30.56, 'rust'); // timber, strapped
  wagon(B, D, 46, -45, true, true);
  siteBoard(D, 36, 4.6, -51.9, 'x', 'sitea', 5); siteBoard(D, 21.5, 2.5, -23.1, 'x', 'sitea', 1.4);

  // ---- B: the depot. the payroll train stopped at the platform (its nose to the rope bridge), the station behind the
  // platform (in through it from Depot Road), the yard behind the train (a boxcar on the siding, the water tank)
  const stn = frontier(B, D, 30, 31, 2, 16, 8, 1, { paint: 'sidelemon', sign: 'addepot', awning: 'roofg' });
  { const L = stn.L; L(4.4, 0.12, 2.4, 7.7, 1.1, 3.0, 'wood'); L(-4.4, 0.12, -1.6, -1.6, 0.5, -1.0, 'wood'); } // the ticket counter, a bench
  add(12, 0, 37.6, 48, 0.45, 41.4, 'wood'); D.add(12, 0.45, 40.9, 48, 0.47, 41.2, 'yellow'); // the platform (stand back from the yellow line)
  { const RB = B.local(13, 44.5, 3), RD = D.local(13, 44.5, 3); train({ add: RB, box: RB.B }, { add: RD, box: RD.B }, 0, 0, [4, 10]); }
  for (const [x0, z] of [[30.6, 43.06], [37, 43.06], [30.6, 45.91], [37, 45.91]]) D.add(x0, 2.0, z, x0 + 2.8, 3.4, z + 0.03, 'adpayroll', { fit: 1 }); // PAYROLL on the boxcar (both sides)
  for (let x = 14; x < 62; x += 0.7) D.add(x, 0, 52.8, x + 0.25, 0.06, 55.2, 'wood');
  for (const s of [-1, 1]) D.add(14, 0.06, 54 + s * 0.75 - 0.06, 62, 0.2, 54 + s * 0.75 + 0.06, 'metal'); // the siding
  add(30, 0.25, 52.6, 40, 1.25, 55.4, 'metal'); add(30, 1.25, 52.6, 40, 3.9, 55.4, 'containerr'); add(29.8, 3.9, 52.5, 40.2, 4.1, 55.5, 'containerr'); // a boxcar on the siding
  for (let t = 30.7; t < 39.5; t += 1.6) for (const z of [52.45, 55.55]) D.add(t - 0.55, 0.08, z - 0.08, t + 0.55, 1.18, z + 0.08, 'tire');
  waterTank(B, D, 18, 58.5, 6.5); cratePile(B, 47, 56, 4, r); hay(B, 54, 49, 3);
  B.box(9.6, 0.6, 33.5, 0.75, 1.2, 0.75, 'barrel'); add(12.6, 0, 31, 15.2, 1.1, 33.2, 'crate'); // by the rope bridge's end
  siteBoard(D, 21.9, 1.4, 33.5, 'z', 'siteb', 2); siteBoard(D, 38.1, 1.4, 31, 'z', 'siteb', 2);

  // ---- the ground between it all (look only): dirt patches, sagebrush, the odd tumbleweed. never inside anything
  { const rg = rng(9595), clear = (x, z, rr) => !B.boxes.some((q) => q.max[1] > 0.06 && q.min[1] < 12 && q.mat !== 'dirtroad' && q.mat !== 'sand' && x + rr > q.min[0] && x - rr < q.max[0] && z + rr > q.min[2] && z - rr < q.max[2]);
    const ok = (x, z) => Math.abs(x) > 10 && !(Math.abs(z) < 9 && x > -70 && x < 47);
    for (let i = 0; i < 40; i++) { const x = X0 + 3 + rg() * (X1 - X0 - 6), z = Z0 + 3 + rg() * (Z1 - Z0 - 6), w = 2 + rg() * 4, d = 2 + rg() * 4; if (ok(x, z) && clear(x, z, Math.max(w, d) / 2)) D.box(x, 0.0075, z, w, 0.015, d, 'dirt'); }
    for (let i = 0; i < 110; i++) { const x = X0 + 3 + rg() * (X1 - X0 - 6), z = Z0 + 3 + rg() * (Z1 - Z0 - 6), s = 0.4 + rg() * 0.6; if (ok(x, z) && clear(x, z, s)) { D.box(x, s * 0.35, z, s, s * 0.7, s * 0.9, rg() < 0.5 ? 'hedge' : 'leaves2'); if (rg() < 0.4) D.box(x + s * 0.4, s * 0.25, z - s * 0.3, s * 0.6, s * 0.5, s * 0.5, 'leaves2'); } }
    for (let i = 0; i < 10; i++) { const x = X0 + 3 + rg() * (X1 - X0 - 6), z = Z0 + 3 + rg() * (Z1 - Z0 - 6); if (ok(x, z) && clear(x, z, 0.6)) D.obb(x, 0.4, z, 0.8, 0.8, 0.8, rg() * 3, 'burnt'); }
  }
  // ---- outside the wall (render-only): dunes, rock formations, palms, the caravan, the thing in the sand
  const ro = rng(9091);
  for (let i = 0; i < 46; i++) { const a = ro() * Math.PI * 2, d = 130 + ro() * 230, x = Math.cos(a) * d, z = Math.sin(a) * d, w = 30 + ro() * 60, dd = 18 + ro() * 36, h = 5 + ro() * 12;
    if (Math.abs(x) < 26 || Math.abs(z) < 14 || (Math.abs(x) - w / 2 < 106 && Math.abs(z) - dd / 2 < 106)) continue; dune(D, x, z, w, dd, h); }
  for (let i = 0; i < 16; i++) { const a = ro() * Math.PI * 2, d = 190 + ro() * 220, x = Math.cos(a) * d, z = Math.sin(a) * d; if (Math.abs(x) < 30 || Math.abs(z) < 20) continue; rocks(D, x, z, 12 + ro() * 20, ro, RK); }
  for (const [x, z, c] of [[104, -14, 'cloth'], [114, 10, 'toyyellow'], [126, -6, 'leopard']]) tent(Dw, x, z, c);
  for (const [x, z, ax] of [[98, 18, true], [108, 22, false], [122, 16, true]]) camel(Dw, x, z, ax);
  for (let i = 0; i < 26; i++) { const a = ro() * Math.PI * 2, d = 110 + ro() * 120, x = Math.cos(a) * d, z = Math.sin(a) * d; if (Math.abs(x) < 20 || Math.abs(z) < 10) continue; palm(Dw, x, z, 6 + ro() * 4, ro); }
  D.add(-260, 0, -210, -230, 26, -180, 'toyface', { fit: 1 }); // something enormous, half buried, smiling
  horizon(D, -300, -300, 300, 300, 1500, 'sand');

  spawns.push(...att.slice(0, 2), ...def.slice(0, 2), [-60, 0.2, 0], [-30, 0.2, 0], [-56, 0.2, -38], [-44, 0.2, 26], [-80, 0.2, -40], [-20, 0.2, 44],
    [20, 0.2, 4], [36, 0.2, -18], [33, 0.2, 18], [28, 0.2, -36], [40, 0.2, -46], [24, 0.2, 49], [40, 0.6, 39.5], [56, 0.2, -36], [56, 0.2, 40]);
  let graph = null;
  const map = { name: 'Desert', size: 'large', boxes: B.boxes, deco: D.boxes, killY: -65.6, fall: 'river', bounds, ceiling: 8.5, floorY: -69,
    sky: { top: 0x3f7fd0, mid: 0xf2d9a0, bot: 0x6a4a28, fog: 0xead6a6 }, fogNear: 120, fogFar: 480, spawns, teamSpawns: { att, def },
    edgeGuard: true, // bots don't dodge-jump next to the canyon (server.js: brBotEdge in every mode here)
    // the bandits' lanes (the bomb carriers walk these; the walk graph gets them round whatever's in the way)
    nav: {
      A: [
        [[-87, -7], [-82, -14], [-70, -24], [-50, -34], [-30, -37], [-16, -37.6], [-7, -39.4], [7, -39.4], [11, -37.4], [20, -36], [32, -36]], // the north lots, the trestle
        [[-86, -1], [-82, -10], [-70, -10], [-66.5, -5], [-60, -1], [-20, -1], [-9, -1], [9, -1], [20, -4], [30, -6], [33, -14], [33, -26], [33, -34]], // Main Street, the bridge, Mine Road
        [[-86, 2], [-82, 10], [-70, 10], [-66.5, 5], [-60, 1], [-20, 1], [-9, 1], [9, 1], [9.8, -10], [9.8, -26], [14, -32], [24, -36]], // Main Street, the bridge, the lip past the assay office
      ],
      B: [
        [[-87, 7], [-82, 14], [-70, 24], [-50, 26], [-30, 28], [-16, 38], [-7, 40], [7, 40], [11, 39.5], [22, 39.5], [32, 39.5]], // the south lots, the rope bridge, the platform
        [[-86, 1], [-82, 10], [-70, 10], [-66.5, 5], [-60, 1], [-20, 1], [-9, 1], [9, 1], [20, 4], [30, 6], [33, 14], [33, 24], [27.7, 25.6], [27.7, 28], [29.5, 33], [30, 38.5]], // the bridge, Depot Road, through the station
        [[-86, -2], [-82, -10], [-70, -10], [-66.5, -5], [-60, -1], [-20, -1], [-9, -1], [9, -1], [9.8, 10], [9.8, 26], [13, 35], [22, 39.5]], // the bridge, the lip past the mining company
      ],
    },
    sites: [{ id: 'A', min: [16, 0, -52], max: [50, 0, -28] }, { id: 'B', min: [12, 0, 30], max: [48, 0, 50] }],
    peekGraph() { return graph; }, dropGraph() { graph = null; }, get graph() { return graph || (graph = buildNav(B.boxes, { x0: bounds[0] - 1, z0: bounds[1] - 1, n: bounds[2] - bounds[0] + 2, cell: 1, levels: [0], band: 0.5, keep: (x, z) => !outOfBounds(map, [x, 0, z]) })); },
  };
  return map;
}

// ------------------------------------------------------------ the island kit (Islands, Islands S&D)
// the sea is a foot deep over the sand round each island (the shelf), then it isn't: past it you sink (killY)
const ISL = { SH: -0.55, SB: -0.6, RF: -0.65, WY: -0.25, DROWN: -30 }; // (DROWN: the kill line, far under the waves. the sea doesn't kill you any more, you float in it (seaSwim). what gets you is swimming off the map: map.bounds, 30 m out past the last island)
void 0; // the shelves' sand, the sandbars' (a hair lower: where one runs into a shelf, the shelf wins), the reef's (lower again), the sea's surface
// a flight of solid steps along x (alongX) or z, from a0 (its foot, at ya) to a1 (its head, yb), c0..c1 across.
// rail: +1 / -1 a rail up the c1 / c0 side. returns { bot, top }: points just off each end, for the walk graph (the
// foot's well clear of the first step: the graph keeps 0.45 m off anything you'd bump into)
function flight(B, alongX, a0, a1, c0, c1, ya, yb, mat = 'wood', rail = 0, stepH = 0.45) {
  const n = Math.max(1, Math.ceil((yb - ya) / stepH)), h = (yb - ya) / n, run = (a1 - a0) / n, s = Math.sign(run), cm = (c0 + c1) / 2;
  const e = rail > 0 ? Math.max(c0, c1) - 0.05 : Math.min(c0, c1) + 0.05;
  for (let i = 1; i <= n; i++) {
    const p0 = a0 + (i - 1) * run, p1 = a0 + i * run, y = ya + i * h;
    if (alongX) B.add(p0, ya, c0, p1, y, c1, mat); else B.add(c0, ya, p0, c1, y, p1, mat);
    if (rail) { if (alongX) B.add(p0, y, e - 0.05, p1, y + 1, e + 0.05, 'metal'); else B.add(e - 0.05, y, p0, e + 0.05, y + 1, p1, 'metal'); }
  }
  return { bot: alongX ? [a0 - s * 1.3, ya, cm] : [cm, ya, a0 - s * 1.3], top: alongX ? [a1 + s * 0.7, yb, cm] : [cm, yb, a1 + s * 0.7] };
}
// an island: sand down to 6 m under, a shelf of shallows round it (shelf m wide: knocked off the beach, you land in
// the shallows, not the deep), surf where the shelf drops away
function isle(B, D, x0, z0, x1, z1, o = {}) {
  const W = B.local(0, 0, 0), s = o.shelf ?? 5;
  slab(W, x0, z0, x1, z1, -6, 0, o.mat || 'sand', o.hole);
  if (s <= 0) return;
  slab(W, x0 - s, z0 - s, x1 + s, z1 + s, -2.5, ISL.SH, 'wetsand', [x0, z0, x1, z1]);
  const X0 = x0 - s, Z0 = z0 - s, X1 = x1 + s, Z1 = z1 + s, f = 0.6, y0 = ISL.WY, y1 = ISL.WY + 0.04;
  D.add(X0 - f, y0, Z0 - f, X1 + f, y1, Z0, 'surf'); D.add(X0 - f, y0, Z1, X1 + f, y1, Z1 + f, 'surf');
  D.add(X0 - f, y0, Z0, X0, y1, Z1, 'surf'); D.add(X1, y0, Z0, X1 + f, y1, Z1, 'surf');
}
// a sandbar from (ax, az) to (bx, bz), w wide: shallows to wade, in steps (boxes only) along its longer way
function sandbar(B, ax, az, bx, bz, w = 10, step = 2) {
  const dx = bx - ax, dz = bz - az, alongX = Math.abs(dx) >= Math.abs(dz), n = Math.max(1, Math.ceil(Math.abs(alongX ? dx : dz) / step));
  for (let i = 0; i < n; i++) {
    const t0 = i / n, t1 = (i + 1) / n, tm = (t0 + t1) / 2;
    if (alongX) { const zc = az + dz * tm; B.add(ax + dx * t0, -2.5, zc - w / 2, ax + dx * t1, ISL.SB, zc + w / 2, 'wetsand'); }
    else { const xc = ax + dx * tm; B.add(xc - w / 2, -2.5, az + dz * t0, xc + w / 2, ISL.SB, az + dz * t1, 'wetsand'); }
  }
}
// a flat of reef between two islands (x0..x1, z0..z1): shallows to wade where the gap was too narrow to be a channel
function reef(B, x0, z0, x1, z1) { B.add(x0, -2.5, z0, x1, ISL.RF, z1, 'wetsand'); }
// a rope bridge along x (alongX) or z, from a0 to a1 on the line c, its deck at 0: planks, rope rails you can lean on
// (or go over), posts, stilts down into the sea. the ropes only run rails[0]..rails[1] (over the deep water): where the
// deck crosses a shelf you can step on and off it from the shallows beside it (bots walking the shallows used to slide
// along a rope off the end of the shelf)
function ropeWalk(B, D, alongX, a0, a1, c, w = 2.6, rails = [a0, a1], tg = null) { // (tg: { av, ai } = drawn by the map's walkway model, look only)
  const [r0, r1] = rails;
  const R = (p0, y0, q0, p1, y1, q1, m, dd) => { const L = dd ? D : B, n = L.boxes.length; L.add(alongX ? p0 : q0, y0, alongX ? q0 : p0, alongX ? p1 : q1, y1, alongX ? q1 : p1, m); if (tg) for (let i = n; i < L.boxes.length; i++) Object.assign(L.boxes[i], tg); };
  R(a0, -0.14, c - w / 2, a1, 0, c + w / 2, 'wood');
  for (let p = a0 + 0.2; p < a1 - 0.1; p += 0.5) R(p, 0, c - w / 2, p + 0.38, 0.03, c + w / 2, 'shipwood', true); // the planks
  for (const s of [-1, 1]) {
    const e = c + s * (w / 2 + 0.05);
    if (r1 - r0 > 0.6) { // (no deep water under it: no ropes)
      R(r0 + 0.13, 0.95, e - 0.04, r1 - 0.13, 1.03, e + 0.04, 'tire'); // the rope (its ends in the posts)
      for (const p of [r0 + 0.13, r1 - 0.13]) R(p - 0.13, 0, e - 0.13, p + 0.13, 1.4, e + 0.13, 'wood');
      for (let p = r0 + 1.2; p < r1 - 1; p += 1.2) R(p - 0.02, 0, e - 0.02, p + 0.02, 0.95, e + 0.02, 'tire', true); // the hangers
    }
    for (let p = a0 + 3; p < a1 - 2; p += 4) R(p - 0.08, -2.4, e - 0.08, p + 0.08, -0.14, e + 0.08, 'wood', true); // stilts
  }
}
// a cannon on its carriage, its mouth toward (dx, dz) (a unit axis): black barrel, wooden carriage, wheels
function cannon(B, D, x, z, y, dx, dz) {
  const ax = dx !== 0, sx = ax ? 1.4 : 0.9, sz = ax ? 0.9 : 1.4;
  B.box(x, y + 0.3, z, sx, 0.6, sz, 'wood');
  D.box(x + dx * 0.5, y + 0.95, z + dz * 0.5, ax ? 2.4 : 0.56, 0.56, ax ? 0.56 : 2.4, 'tire'); D.box(x + dx * 1.62, y + 0.95, z + dz * 1.62, ax ? 0.18 : 0.7, 0.7, ax ? 0.7 : 0.18, 'tire'); // the barrel, its lip
  for (const s of [-1, 1]) for (const k of [-0.45, 0.45]) D.box(x + (ax ? k : s * 0.5), y + 0.3, z + (ax ? s * 0.5 : k), ax ? 0.6 : 0.12, 0.6, ax ? 0.12 : 0.6, 'wood');
}
// a beach hut: bamboo walls, a door on the door side (dz = -1 north / +1 south), a window opposite, a thatched roof
function hut(B, D, cx, cz, dz = -1, w = 4.4, d = 3.6) {
  const W = B.local(0, 0, 0), x0 = cx - w / 2, x1 = cx + w / 2, z0 = cz - d / 2, z1 = cz + d / 2;
  wall(W, 'x', dz < 0 ? z0 : z1, x0, x1, 0, 2.6, 0.2, 'bamboo', [{ a: cx - 0.6, b: cx + 0.6, y0: 0, y1: 2.1 }]);
  wall(W, 'x', dz < 0 ? z1 : z0, x0, x1, 0, 2.6, 0.2, 'bamboo', [{ a: cx - 0.8, b: cx + 0.8, y0: 1.0, y1: 1.9 }]);
  wall(W, 'z', x0, z0 + 0.1, z1 - 0.1, 0, 2.6, 0.2, 'bamboo'); wall(W, 'z', x1, z0 + 0.1, z1 - 0.1, 0, 2.6, 0.2, 'bamboo');
  B.add(x0 - 0.5, 2.6, z0 - 0.5, x1 + 0.5, 2.9, z1 + 0.5, 'thatch'); B.add(x0 + 0.3, 2.9, z0 + 0.3, x1 - 0.3, 3.3, z1 - 0.3, 'thatch');
  D.add(x0 + 0.4, 1.0, cz - 0.25, x1 - 0.4, 1.1, cz + 0.25, 'cloth'); // a hammock
  B.box(x1 - 0.8, 0.4, dz < 0 ? z1 - 0.8 : z0 + 0.8, 0.8, 0.8, 0.8, 'crate');
}
// a lounger under an umbrella (the umbrella's only to look at)
function lounger(B, D, x, z, m) {
  B.add(x - 0.35, 0, z - 0.95, x + 0.35, 0.35, z + 0.95, m); B.add(x - 0.35, 0.35, z - 0.95, x + 0.35, 0.85, z - 0.65, m);
  D.add(x + 0.9, 0, z - 0.05, x + 1.0, 2.2, z + 0.05, 'white'); D.add(x - 0.3, 2.2, z - 1.2, x + 2.2, 2.32, z + 1.2, pickUmb(x + z));
}
const pickUmb = (k) => ['toypink', 'toyteal', 'toyyellow', 'sidelemon'][Math.abs(Math.round(k * 7)) % 4];

// ---- the set pieces. each is built where the standard Islands has it, moved (dx, dz) (Islands S&D moves them about);
// st collects their stairs for the walk graph
const MD = 4.5, QD = 7.5, SKT = SKULL.TOP, FW = 4.5; // the wreck's main deck and quarterdeck, Skull Rock's crown, the fort's wall walk
const SPINE = { z0: 86.6, z1: 78.6, hw: 1.2, top: 9 }; // Skull Rock's spine (local z: its foot in the shallows, its head at the dome), half as wide, how high it takes you
function shifted(B, dx, dz) { // a builder that puts everything dx, dz over
  return { boxes: B.boxes, add: (x0, y0, z0, x1, y1, z1, m, e) => B.add(x0 + dx, y0, z0 + dz, x1 + dx, y1, z1 + dz, m, e),
    box: (cx, cy, cz, sx, sy, sz, m, e) => B.box(cx + dx, cy, cz + dz, sx, sy, sz, m, e), local: (ox, oz, rot = 0, oy = 0) => B.local(ox + dx, oz + dz, rot, oy) };
}
function isPiece(B0, D0, dx, dz, st) {
  const B = shifted(B0, dx, dz), D = shifted(D0, dx, dz);
  return { B, D, add: B.add, W: B.local(0, 0, 0), up: (f) => { st.push({ bot: [f.bot[0] + dx, f.bot[1], f.bot[2] + dz], top: [f.top[0] + dx, f.top[1], f.top[2] + dz], ...(f.via ? { via: f.via.map((p) => [p[0] + dx, p[1], p[2] + dz]) } : {}) }); return f; } };
}
// Mount Kaboom (round 0, -3): three terraces, two ways up each, the crater (its rim open at the two stairs), the throat
// right down. returns the throat in the world (the island under it needs the same hole)
const LAVA_FLOOR = 1.3; // the plug under the throat's lava (its surface is 4.5: over three metres of it. you sink, shared/pits.js mire. off the walk graph's levels on purpose)
const lavaPit = (T) => ({ kind: 'lava', box: T, top: 4.6, bot: LAVA_FLOOR - 0.5 });
// Mount Kaboom as an actual mountain (Islands, quick play): a big uneven cone, steep up top with long low spurs running
// out into the island, six gullies, a broken rim, a crater with a level floor round the throat, an apron of lumpy ground. the shape is ground (shared/terrain.js relief: you walk it,
// grapple it, bots path over it); this only adds what stands on it, at y 0 (the ground lifts it), and the lava down the
// throat, which stays exactly where the pit rules expect it (shared/pits.js). returns { throat, f: the height function }
const KABOOM = { c: [0, -3], rc: 6.4, crest: 15, crater: 11.5, floorR: 4.6, apron: 5, edge: [-28, -24, 28, 24], south: 11.5, side: 26,
  footR: 17, lobe: 1, jag: 1, notch: 1, conc: 1.7, gully: 1, crag: 1, bands: [[0.25, 1.5], [0.5, 2], [0.72, 2.4]], ledgeL: 2.3, ledgeFlat: 0.6, spatter: true,
  boulders: [[-13, -10, 1.2], [11, -7.5, 1.3], [-10.5, 5, 1.0], [6.5, -12, 0.9], [-5, 5.5, 0.8], [13.5, 3, 1.1], [-20.5, -12.5, 1.0], [2, -17, 1.1]], lipY: 0, sign: [-1.6, 0.3, -0.66, 1.6, 0.9, -0.6] };
// Islands S&D's Mount Kaboom (round 0, -13, between the spawns): the same mountain made small, a sloped cone you walk
// straight up (it used to be three box terraces and six stairs). its top a flat exposed summit at 9 m round the throat
// (the map's ceiling is 9.5: a lip, no rim to hide behind), two broken rings of ledges about where the terraces were
// (cover on the way up), shallow gullies, small outcrops, its own boulders. the footprint the terraces had
const KABOOM_SD = { ...KABOOM, rc: 4.2, crest: 9.15, crater: 9.0, floorR: 3.6, apron: 3, edge: [-21, -18, 21, 16], south: 10, side: 15.5,
  footR: 15, lobe: 0.25, jag: 0.06, notch: 0, conc: 1.0, gully: 0.45, crag: 0.3, bands: [], ledgeL: 0.75, ledgeFlat: 0.3, spatter: false,
  boulders: [[-10.5, -6, 1.0], [9.5, -4.5, 1.1], [-7.5, 6.5, 0.9], [6.5, 7, 0.9], [0.5, -14.5, 1.0], [-12, 1.5, 0.8], [12, 2, 0.8]], sign: [3, 0.6, 9.8, 9, 1.8, 9.86] };
function kaboom(B0, D0, dx, dz, K = KABOOM) {
  const B = shifted(B0, dx, dz), D = shifted(D0, dx, dz), T = [-2, -5, 2, -1];
  const cx = K.c[0] + dx, cz = K.c[1] + dz, sm = (a, b, v) => { const k = Math.max(0, Math.min(1, (v - a) / (b - a))); return k * k * (3 - 2 * k); };
  const RAD = Math.PI / 180, bump = (a, m, w) => { let d = ((a - m + 540) % 360) - 180; return Math.exp(-(d / w) * (d / w)); }; // (a, m in degrees, wrapped)
  // the foot: not a circle. a lava delta north, a long ridge spur west-north-west, an east buttress, a south-west shoulder,
  // a collapsed flank south-east. held back from the tiki village (south) and the beaches' sides
  const foot = (a) => {
    let R = K.footR + K.lobe * (5 * bump(a, -90, 14) + 8 * bump(a, 200, 13) + 4.5 * bump(a, -20, 16) + 3 * bump(a, 140, 18) - 4 * bump(a, 50, 20) + 0.8 * Math.sin(5 * a * RAD) + 0.5 * Math.sin(9 * a * RAD));
    const c = Math.cos(a * RAD), s = Math.sin(a * RAD);
    if (s > 0.05) R = Math.min(R, (K.south - K.c[1]) / s);
    if (Math.abs(c) > 0.05) R = Math.min(R, K.side / Math.abs(c));
    return Math.max(K.rc + 6, R);
  };
  // the rim: broken, a notch north (where the lava leaves), a low gap south (the way in from the village)
  const rim = (a) => K.crest + K.jag * (0.55 * Math.sin(2 * a * RAD + 0.4) + 0.35 * Math.sin(5 * a * RAD) + 1.1 * (vnoise(3.4 * Math.cos(a * RAD) + 9, 3.4 * Math.sin(a * RAD) + 9, 31) - 0.5) + 0.9 * Math.max(0, Math.sin(4 * a * RAD + 1)) ** 4
    + 2.4 * (hsh(Math.floor((a + 180) / 18), 0, 61) - 0.5) * (1 - bump(a, -90, 16)) * (1 - bump(a, 90, 18))) // (teeth: a jagged step every couple of metres, not across the two ways in)
    - K.notch * (2.5 * bump(a, -90, 11) + 1.5 * bump(a, 90, 14));
  const lump = (x, z) => Math.sin(x * 0.9 + 1.7) * Math.sin(z * 1.1 - 0.6) * 0.5 + Math.sin(x * 0.37 - z * 0.53) * 0.5; // -1..1, for the apron
  // roughness (the owner: "too smooth still"): the same on every machine (integer hashes), nothing finer than the ground's 1 m grid can hold
  const hsh = (i, j, k) => { let n = Math.imul(i, 374761393) ^ Math.imul(j, 668265263) ^ Math.imul(k + 77, 1442695041); n = Math.imul(n ^ (n >>> 13), 1274126177); return ((n ^ (n >>> 16)) >>> 0) / 4294967295; };
  const vnoise = (x, z, k) => { const i = Math.floor(x), j = Math.floor(z), u = x - i, v = z - j, a = u * u * (3 - 2 * u), b = v * v * (3 - 2 * v); return (hsh(i, j, k) * (1 - a) + hsh(i + 1, j, k) * a) * (1 - b) + (hsh(i, j + 1, k) * (1 - a) + hsh(i + 1, j + 1, k) * a) * b; };
  const crags = (x, z) => { // outcrops: steep-sided knobs of rock scattered over the flanks, 0.6 to 2.6 m tall, some of them hollows instead
    const G = 5.5, ci = Math.floor(x / G), cj = Math.floor(z / G);
    let h = 0;
    for (let i = ci - 1; i <= ci + 1; i++) for (let j = cj - 1; j <= cj + 1; j++) {
      if (hsh(i, j, 1) > 0.78) continue;
      const rr = 2 + 2.8 * hsh(i, j, 2), ox = (i + 0.15 + 0.7 * hsh(i, j, 3)) * G, oz = (j + 0.15 + 0.7 * hsh(i, j, 4)) * G, d = Math.hypot((x - ox) * (0.7 + 0.6 * hsh(i, j, 7)), z - oz);
      if (d >= rr) continue;
      const q = 1 - d / rr, v = K.crag * (hsh(i, j, 6) < 0.2 ? -0.5 : 1) * (1.1 + 2.6 * hsh(i, j, 5)) * Math.min(1, rr / 3) * Math.pow(q * q * (3 - 2 * q), 0.45);
      if (Math.abs(v) > Math.abs(h)) h = v;
    }
    return h;
  };
  // the bare flank at (angle, how far down 0..1): steep up top, long shallow lower slopes, cut by gullies
  const tri = (a, m, w) => Math.max(0, 1 - Math.abs(((a - m + 540) % 360) - 180) / w);
  const BANDS = K.bands; // (where each cliff band sits, how many metres wide its bench is)
  const flank = (a, t, cr) => {
    let h = cr * (0.8 * Math.pow(1 - t, K.conc) + 0.2 * (1 - t));
    const mid = t < 0.9 ? Math.sin(Math.PI * t / 0.9) : 0;
    let g = 0; for (const [m, w, d] of [[18.5, 21, 2.5], [138.5, 21, 2.5], [-101.5, 21, 2.5], [78.5, 13, 1.3], [-41.5, 13, 1.3]]) g = Math.max(g, d * tri(a, m, w));
    h -= g * mid * K.gully; // gullies: V-shaped, a hard break of slope at the bed and at each lip, deepest half way down
    h += 0.75 * (tri(a, -11.5, 9) + tri(a, 108.5, 9) + tri(a, -131.5, 9) + tri(a, 168, 9)) * mid; // knife ridges between them
    h += 0.3 * Math.sin(13 * a * RAD + 2) * mid; // and a finer set of ribs
    h -= 1.5 * bump(a, 50, 20) * sm(0.2, 0.35, t) * (1 - sm(0.65, 0.8, t)); // the scar where the south-east flank fell away
    return h;
  };
  // a spatter cone on the west spur, two thirds of the way out: a stubby little vent with a dimple in the top
  const SPAT = [cx - 17.4, cz - 6.3], spatter = (x0, z0) => { if (!K.spatter) return 0; const d = Math.hypot(x0 - SPAT[0], z0 - SPAT[1]); return d >= 3.6 ? 0 : 2.9 * Math.pow(1 - d / 3.6, 0.8) - 1.3 * Math.max(0, 1 - d / 1.2); };
  const f = (x0, z0) => {
    const x = x0 - cx, z = z0 - cz, r = Math.hypot(x, z), a = Math.atan2(z, x) / RAD, R = foot(a), cr = rim(a);
    if (r >= R + K.apron) return null;
    // the island's own edge: everything eases down to the beach there (no cliff into the shallows)
    const e = Math.min(x0 - dx - K.edge[0], K.edge[2] - (x0 - dx), z0 - dz - K.edge[1], K.edge[3] - (z0 - dz)), ek = sm(0, 3.5, e);
    if (r >= R) { const u = (r - R) / K.apron; return Math.max(0, (0.28 + 0.3 * lump(x0, z0)) * (1 - u) * (1 - u)) * ek; } // the apron: low lumpy ground running out to nothing
    if (r <= K.rc) { // the crater: a level floor, then up to the rim. at the two ways in (south gap, north notch) a longer, gentler ramp you can walk out by
      const way = Math.max(bump(a, 90, 22), bump(a, -90, 18)), fr = K.floorR - 0.5 * way, k = Math.max(0, Math.min(1, (r - fr) / (K.rc - fr)));
      return K.crater + (cr - K.crater) * (k * way + sm(K.floorR, K.rc, r) * (1 - way));
    }
    const t = (r - K.rc) / (R - K.rc);
    let h = flank(a, t, cr);
    const mid = t < 0.9 ? Math.sin(Math.PI * t / 0.9) : 0;
    // cliff bands: three broken rings of bench-then-drop, each only in arcs (gaps to walk through), their edges ragged
    for (let k = 0; k < BANDS.length; k++) {
      const tk = BANDS[k][0] + 0.035 * (vnoise(x0 * 0.45, z0 * 0.45, 50 + k) - 0.5), bw = BANDS[k][1] / (R - K.rc);
      if (t < tk || t >= tk + bw) continue;
      const m = sm(0.44, 0.5, vnoise(2.3 * Math.cos(a * RAD) + 7 * k + 5, 2.3 * Math.sin(a * RAD) + 5, 40 + k)) * (1 - bump(a, 90, 16)) * (1 - bump(a, -90, 12));
      h += (flank(a, tk, cr) - h) * m;
    }
    // broken ledges: the slope steps in benches about 1.7 m apart, but only in patches (never a ring right round)
    const L = K.ledgeL, sN = h / L, fl = Math.floor(sN), bench = (fl + sm(K.ledgeFlat, 0.97, sN - fl)) * L, lk = sm(0.36, 0.6, vnoise(x0 * 0.13, z0 * 0.13, 11));
    h = h * (1 - lk) + bench * lk;
    const rough = Math.max(mid, sm(0.02, 0.12, t) * (1 - sm(0.8, 0.95, t))) * (0.6 + 0.4 * Math.sin(Math.PI * Math.min(1, t * 1.6))); // (none right at the rim or the foot)
    h += crags(x0, z0) * rough + spatter(x0, z0); // outcrops and hollows, the spatter cone
    h += (Math.abs(vnoise(x0 * 0.31, z0 * 0.31, 21) - 0.5) * 2 - 0.5) * 1.4 * rough; // sharp little ridges between them
    return Math.max(0.28 * (1 - t) + 0.05, h) * (t > 0.6 ? 1 - (1 - ek) * sm(0.6, 1, t) : 1);
  };
  f.rock = (x0, z0) => { const x = x0 - cx, z = z0 - cz; return Math.hypot(x, z) < foot(Math.atan2(z, x) / RAD) - 0.3; }; // (where it's bare rock: the apron keeps the island's own grass and sand)
  B.add(T[0], 0, T[1], T[2], LAVA_FLOOR, T[3], 'basalt', { still: 1 }); D.add(T[0], 4.3, T[1], T[2], 4.5, T[3], 'lava', { still: 1 }); // the plug and the lava over it (map.pits)
  for (const [x0, z0, x1, z1] of [[-2.3, -5.3, 2.3, -5], [-2.3, -1, 2.3, -0.7], [-2.3, -5, -2, -1], [2, -5, 2.3, -1]]) B.add(x0, 0, z0, x1, 0.3, z1, 'basalt'); // the throat's lip
  D.add(...K.sign, 'advolcano', { fit: 1 });
  for (const [x, z, s] of K.boulders) B.add(x - s, 0, z - s * 0.8, x + s, s * 1.2, z + s * 0.8, 'basalt'); // boulders on the flanks (cover on the way up)
  return { throat: [T[0] + dx, T[1] + dz, T[2] + dx, T[3] + dz], f };
}
// the tiki bar (round -13, 18): a bamboo counter under a thatched roof on four posts, stools, the back bar and its bottles
function tikiBar(B0, D0, dx, dz, r) {
  const { B, D, add } = isPiece(B0, D0, dx, dz, []), pick = (a) => a[(r() * a.length) | 0];
  add(-17, 0, 18.4, -9, 1.1, 19.4, 'bamboo'); D.add(-17.1, 1.1, 18.3, -8.9, 1.18, 19.5, 'wood'); // the counter
  add(-16.6, 0, 15.6, -9.4, 1.7, 16.1, 'wood'); for (let x = -16.2; x < -9.6; x += 0.55) D.box(x, 1.85, 15.85, 0.22, 0.3, 0.22, pick(['glass', 'toyteal', 'toypink', 'toyyellow'])); // the back bar, its bottles
  for (const x of [-16, -14.5, -13, -11.5, -10]) B.box(x, 0.35, 20.4, 0.5, 0.7, 0.5, 'bamboo'); // stools
  for (const [x, z] of [[-17.6, 15], [-8.4, 15], [-17.6, 20.8], [-8.4, 20.8]]) B.box(x, 1.5, z, 0.3, 3, 0.3, 'bamboo');
  add(-18.6, 3, 14.2, -7.4, 3.3, 21.8, 'thatch'); add(-17.4, 3.3, 15.2, -8.6, 3.7, 20.8, 'thatch'); add(-15.6, 3.7, 16.4, -10.4, 4.0, 19.6, 'thatch');
  D.add(-16, 2.3, 21.82, -10, 2.95, 21.9, 'adtiki', { fit: 1 });
}
// the big tiki (round -21.5, 17): cover, and he's watching
function bigTiki(B0, D0, dx, dz) {
  const { D, add } = isPiece(B0, D0, dx, dz, []);
  add(-22.6, 0, 15.9, -20.4, 0.6, 18.1, 'basalt'); add(-22.4, 0.6, 16.2, -20.6, 3.8, 17.8, 'wood');
  D.add(-22.6, 2.9, 17.8, -20.4, 3.3, 18.1, 'wood'); D.add(-22.1, 2.3, 17.8, -21.7, 2.8, 17.86, 'white'); D.add(-21.3, 2.3, 17.8, -20.9, 2.8, 17.86, 'white');
  D.add(-21.95, 2.4, 17.86, -21.8, 2.6, 17.9, 'tire'); D.add(-21.15, 2.4, 17.86, -21.0, 2.6, 17.9, 'tire'); D.add(-22.1, 1.2, 17.8, -20.9, 1.6, 17.88, 'toyred');
  D.add(-22.8, 3.8, 16.0, -20.2, 4.3, 18.0, 'leaves2');
}
// the surf school (round 24, 14): boards stuck in the sand, its sign
function surfSchool(B0, D0, dx, dz) {
  const { D } = isPiece(B0, D0, dx, dz, []);
  for (const [i, m] of ['toypink', 'toyyellow', 'toyteal'].entries()) D.box(24 + i * 0.8, 1.1, 14.6, 0.6, 2.2, 0.12, m); // surfboards stuck in the sand
  D.add(22.6, 0, 13.4, 22.72, 2.6, 13.52, 'wood'); D.add(21.4, 1.6, 13.52, 23.9, 2.6, 13.6, 'adsurf', { fit: 1 });
}
// the bait shack (round 46, 9, on the pier's wide bit): its hatch, its sign, crates and a barrel out front
function baitShack(B0, D0, dx, dz) {
  const { B, D, add, W } = isPiece(B0, D0, dx, dz, []);
  wall(W, 'x', 8.3, 43, 49, 0, 2.8, 0.2, 'planks', [{ a: 44.2, b: 47.8, y0: 1.0, y1: 2.0 }]); // the shack's front (its hatch)
  wall(W, 'x', 10.3, 43, 49, 0, 2.8, 0.2, 'planks'); wall(W, 'z', 43.1, 8.4, 10.2, 0, 2.8, 0.2, 'planks'); wall(W, 'z', 48.9, 8.4, 10.2, 0, 2.8, 0.2, 'planks');
  add(42.6, 2.8, 7.8, 49.4, 3.05, 10.8, 'roofteal'); add(43.2, 1.0, 7.95, 48.8, 1.08, 8.2, 'wood');
  D.add(43.6, 2.06, 8.18, 48.4, 2.75, 8.2, 'adbait', { fit: 1 });
  for (const [x, z] of [[43.2, 3.2], [44.6, 3.4], [48.5, 3.1]]) B.box(x, 0.45, z, 0.9, 0.9, 0.9, 'crate'); B.box(46.6, 0.55, 3.3, 1.1, 1.1, 1.1, 'barrel');
}
// the Soggy Biscuit (round 0, -69, lying along x), broken in two: the hold (walk in at the break), the main deck (a
// gangway up each side), the quarterdeck over the captain's cabin, the crow's nest, the duck figurehead
function wreck(B0, D0, dx, dz, st) {
  const { B, D, add, W, up } = isPiece(B0, D0, dx, dz, st); const ZA = -73.5, ZB = -64.5; // the hull's sides
  // the ship is drawn as one Blender model (public/models/arch/wreck.glb, look only: these boxes are still what you bump
  // into). own: what it doesn't draw (the barrels, crates and cannons are props of their own; the signs are pictures)
  const n0 = B0.boxes.length, d0 = D0.boxes.length, mine = new Set(), own = (fn) => { const a = B0.boxes.length, b = D0.boxes.length; fn(); for (let i = a; i < B0.boxes.length; i++) mine.add(B0.boxes[i]); for (let i = b; i < D0.boxes.length; i++) mine.add(D0.boxes[i]); };
  const side = (z, x0, x1, y1, ports) => wall(W, 'x', z, x0, x1, 0, y1, 0.4, 'shiphull', ports.map((x) => ({ a: x - 0.5, b: x + 0.5, y0: 0.6, y1: 1.4 })));
  for (const z of [ZA + 0.2, ZB - 0.2]) {
    side(z, 1.5, 15.6, MD, [4, 8, 12]); side(z, -10, -1.5, MD, [-7, -4]); side(z, -18, -10, QD, [-15, -12]);
    wall(W, 'x', z, 1.5, 15.6, MD, MD + 1, 0.4, 'shipwood', z < -69 ? [] : [{ a: 8, b: 10.4, y0: MD, y1: MD + 1 }]); // the bulwarks (a gap where a gangway comes up)
    wall(W, 'x', z, -10, -1.5, MD, MD + 1, 0.4, 'shipwood', z < -69 ? [{ a: -4.6, b: -2.2, y0: MD, y1: MD + 1 }] : []);
    wall(W, 'x', z, -18, -10, QD, QD + 1, 0.4, 'shipwood');
  }
  add(1.5, MD - 0.4, ZA + 0.4, 15.6, MD, ZB - 0.4, 'shipwood'); add(-10, MD - 0.4, ZA + 0.4, -1.5, MD, ZB - 0.4, 'shipwood'); // the main deck (both halves)
  add(-17.6, MD - 0.4, ZA + 0.4, -10, MD, ZB - 0.4, 'shipwood'); add(-17.6, QD - 0.4, ZA + 0.4, -10, QD, ZB - 0.4, 'shipwood'); // the cabin's floor, the quarterdeck
  // the bow: it steps in to a narrower nose (beam 5) and the stem, the rubber duck figurehead under the bowsprit
  for (const [y0, y1, m] of [[0, MD, 'shiphull'], [MD, MD + 1, 'shipwood']]) {
    add(15.6, y0, ZA, 16, y1, ZA + 2.4, m); add(15.6, y0, ZB - 2.4, 16, y1, ZB, m); // where it steps in
    add(16, y0, ZA + 2, 19.2, y1, ZA + 2.4, m); add(16, y0, ZB - 2.4, 19.2, y1, ZB - 2, m); add(19.2, y0, ZA + 2, 19.6, y1, ZB - 2, m); // its sides, the stem
  }
  add(15.6, MD - 0.4, ZA + 2.4, 19.2, MD, ZB - 2.4, 'shipwood');
  // the bow's shoulders: the ship's prow is round (wreck.glb), so the rock-solid part is too. slices under its curve
  const STEM = 20.05, hb = (x) => 4.5 * Math.max(0, 1 - ((x - 15.6) / (STEM - 15.6)) ** 3) ** (1 / 3) - 0.02;
  for (const [x0, x1] of [[16, 16.4], [16.4, 16.8], [16.8, 17.2], [17.2, 17.6], [17.6, 18], [18, 18.4], [18.4, 18.8], [18.8, 19.2], [19.2, 19.6], [19.6, 19.85], [19.85, 20]]) {
    const h = hb(x1), w = x0 < 19.6 ? 2.5 : 0; // (past the stem box: the point of the prow, whole)
    if (h > w + 0.05) { add(x0, 0, -69 - h, x1, MD + 1, -69 - w, 'shiphull'); if (w) add(x0, 0, -69 + w, x1, MD + 1, -69 + h, 'shiphull'); }
  }
  D.add(19.6, 4.5, -69.4, 23.6, 4.8, -68.6, 'shipwood'); // the bowsprit
  add(19.6, 5.5, -69.95, 22.0, 7.0, -68.05, 'toyyellow'); add(21.05, 7.0, -69.5, 22.15, 8.05, -68.5, 'toyyellow'); D.add(22.15, 7.28, -69.25, 22.65, 7.42, -68.75, 'barrelr'); // the duck: a big rubber duck riding the bow, against the sky (it reads from across the map)
  // the stern: the transom (its windows, the name), the cabin's front wall (a door) under the quarterdeck
  wall(W, 'z', -17.8, ZA + 0.4, ZB - 0.4, 0, QD + 1, 0.4, 'shiphull', [{ a: -71, b: -69.8, y0: 5.4, y1: 6.6 }, { a: -68.2, b: -67, y0: 5.4, y1: 6.6 }]);
  own(() => D.add(-18.08, 2.2, -71.4, -18.02, 3.4, -66.6, 'adship', { fit: 1 }));
  wall(W, 'z', -10.15, -71.6, ZB - 0.4, MD, QD - 0.4, 0.3, 'shipwood', [{ a: -69, b: -67.6, y0: MD, y1: MD + 2.1 }]);
  // the ways up: a gangway each side, the quarterdeck stair, the cabin's table and the captain's chest
  up(flight(B, false, -59.9, ZB, 8, 10.4, 0, MD, 'shipwood'));
  up(flight(B, false, -78.1, ZA, -4.6, -2.2, 0, MD, 'shipwood'));
  up(flight(B, true, -5.8, -10, ZA + 0.4, ZA + 1.9, MD, QD, 'shipwood'));
  own(() => { add(-15.6, MD, -69.6, -12.8, MD + 0.8, -68.4, 'wood'); add(-17.4, MD, -66.4, -16.2, MD + 0.8, -65.2, 'crate'); });
  // the masts: the foremast with its crow's nest and the torn sail, the mizzen with the flag, the main mast fallen on the sand
  add(9.75, MD, -69.25, 10.25, 17, -68.75, 'shipwood'); add(8.6, 14.2, -70.4, 11.4, 14.5, -67.6, 'shipwood');
  own(() => D.add(10.35, 14.5, -70.15, 11.15, 14.53, -67.85, 'missing')); // where the intern ran out of textures (secrets.js: Todd stands on it)
  for (const [x0, z0, x1, z1] of [[8.6, -70.4, 11.4, -70.2], [8.6, -67.8, 11.4, -67.6], [8.6, -70.2, 8.8, -67.8], [11.2, -70.2, 11.4, -67.8]]) add(x0, 14.5, z0, x1, 15.4, z1, 'shipwood');
  D.add(9.8, 11, -73, 10.2, 11.3, -65, 'shipwood'); D.add(10.25, 6.5, -72.4, 10.3, 11, -66.4, 'sail'); D.add(10.25, 5.5, -71.4, 10.3, 6.5, -68.6, 'sail');
  add(-14.2, QD, -69.2, -13.8, 15, -68.8, 'shipwood'); own(() => D.add(-13.8, 12.6, -69.04, -11, 14.4, -68.96, 'flagskull', { fit: 1 })); // (the flag: the game's picture)
  D.add(-12.3, QD, -69.15, -12.1, QD + 1.0, -68.85, 'wood'); D.add(-12.4, QD + 0.6, -69.8, -12.0, QD + 1.4, -68.2, 'wood'); // the wheel
  add(-7, 0, -62.5, 6.5, 0.8, -61.7, 'shipwood'); D.add(-6, 0.03, -61.7, 3, 0.1, -59.4, 'sail'); // the main mast, fallen, and its sail
  // the hold: barrels, crates, two cannons at the gunports, hammocks
  own(() => {
    for (const [x, z] of [[3, -72], [3, -70.8], [14, -66], [-3.5, -72.2], [-16.6, -72.2], [-16.6, -71]]) B.box(x, 0.55, z, 1.1, 1.1, 1.1, 'barrel');
    for (const [x, z] of [[6, -66.2], [7.2, -66.4], [-8, -66], [-15.5, -66.2]]) B.box(x, 0.5, z, 1, 1, 1, 'crate');
    cannon(B, D, 12, -71.2, 0, 0, -1); cannon(B, D, -12, -66.6, 0, 0, 1);
  });
  D.add(4, 2.8, -69.3, 9, 2.9, -68.7, 'cloth'); D.add(-9, 2.8, -69.3, -4, 2.9, -68.7, 'cloth');
  for (const x of [11, -7]) { D.box(x, 3.85, -69, 0.06, 0.5, 0.06, 'metal'); D.box(x, 3.4, -69, 0.32, 0.42, 0.32, 'lantern'); } // lanterns in the hold
  // splinters at the break
  for (const [x, z, h] of [[1.5, ZA + 0.2, 1.2], [1.5, ZB - 0.2, 0.8], [-1.5, ZA + 0.2, 0.9], [-1.5, ZB - 0.2, 1.4]]) D.box(x + (x > 0 ? -0.15 : 0.15), MD + h / 2 - 0.3, z, 0.3, h, 0.42, 'shipwood');
  B0.boxes.arch.push({ id: 'wreck', p: [dx, 0, dz], r: 0 }); const tag = { av: 'wreck', ai: B0.boxes.arch.length - 1 };
  for (let i = n0; i < B0.boxes.length; i++) if (!mine.has(B0.boxes[i])) Object.assign(B0.boxes[i], tag);
  for (let i = d0; i < D0.boxes.length; i++) if (!mine.has(D0.boxes[i])) Object.assign(D0.boxes[i], tag);
}
// the lighthouse (round 82, -6): the striped tower, the lantern; o.climb false: no stair round it and no gallery (S&D)
// an octagon over a rectangle (its flats on the rectangle's sides, each corner cut c along both sides) as boxes, every
// one inside it: a cross, and each corner stepped n times out toward the cut. hole: a rectangle [x0, z0, x1, z1] left out
function octoBoxes(x0, z0, x1, z1, c, n = 4, hole = null) {
  const out = [[x0, z0 + c, x1, z1 - c], [x0 + c, z0, x1 - c, z1]];
  for (const [sx, sz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) {
    const cx = sx < 0 ? x0 + c : x1 - c, cz = sz < 0 ? z0 + c : z1 - c; // the corner's inner point
    for (let k = 1; k < n; k++) { const ax = cx + sx * c * k / n, az = cz + sz * c * (n - k) / n; out.push([Math.min(cx, ax), Math.min(cz, az), Math.max(cx, ax), Math.max(cz, az)]); }
  }
  if (!hole) return out;
  const [hx0, hz0, hx1, hz1] = hole, cut = [];
  for (const [a, b, c2, d] of out) {
    if (c2 <= hx0 || a >= hx1 || d <= hz0 || b >= hz1) { cut.push([a, b, c2, d]); continue; }
    if (a < hx0) cut.push([a, b, hx0, d]); if (c2 > hx1) cut.push([hx1, b, c2, d]);
    const m0 = Math.max(a, hx0), m1 = Math.min(c2, hx1);
    if (b < hz0) cut.push([m0, b, m1, hz0]); if (d > hz1) cut.push([m0, hz1, m1, d]);
  }
  return cut;
}
const LH = { c: 1.757, lc: 1.172, hole: [76, -8.75, 79, -4.757] }; // the lighthouse's corner cuts: the tower (a regular octagon 6 m across), the lantern room (4 m); the gallery's hole over the stair's top
// the lighthouse's iron stair (tools/blender/arch/make_lighthouse.py draws the same numbers): 1.8 m wide round the
// tower's eight faces from the west / south-west corner, up the south-west face first, 9 steps a face and a little
// landing at each corner, 0.225 m a step (80 of them to the gallery at 18). -> cells: slabs' tops [x0, z0, x1, z1, h]
// on a grid lined up with the steps on the square faces (a step a cell there; on the cut faces each cell takes the step
// its middle is on, so walking up them every cell you meet is the next one up), posts [x, z, h] along the open side,
// and the walk graph's way up (bot, via, top)
export function lhStair() {
  const C = [82, -6], A0 = 3, A1 = 4.8, T = Math.tan(Math.PI / 8), L = A0 * T, g = 2 * L / 9, r = 18 / 80, MID = 3.95; // (MID: the bots' line, clear of the tower's corners when they cut across a landing)
  const F = [...Array(8)].map((_, k) => { const a = (135 - 45 * k) * Math.PI / 180; return { n: [Math.cos(a), Math.sin(a)], t: [Math.sin(a), -Math.cos(a)] }; });
  const us = (k, x, z) => { const f = F[k], px = x - C[0], pz = z - C[1]; return [px * f.n[0] + pz * f.n[1], px * f.t[0] + pz * f.t[1]]; };
  const at = (k, u, s) => [C[0] + F[k].n[0] * u + F[k].t[0] * s, C[1] + F[k].n[1] * u + F[k].t[1] * s];
  const H = (x, z) => { // the step (or landing) over (x, z), its top; null off the stair
    for (let k = 0; k < 8; k++) {
      const [u, s] = us(k, x, z);
      if (u >= A0 && u <= A1 && s >= -L && s <= L) return (10 * k + Math.min(8, Math.floor((s + L) / g)) + 1) * r;
      if (k < 7) { const [u2, s2] = us(k + 1, x, z); if (s > L && s2 < -L && u <= A1 && u2 <= A1) return (10 * k + 10) * r; }
    }
    return null;
  };
  const cells = [], gx = C[0] - L, gz = C[1] - L, n0 = Math.ceil((A1 + 0.3) / g) + 5;
  for (let j = -n0; j <= n0; j++) {
    const z0 = gz + j * g, z1 = z0 + g; let run = null;
    for (let i = -n0; i <= n0 + 1; i++) {
      const x0 = gx + i * g, h = i <= n0 ? H(x0 + g / 2, z0 + g / 2) : null;
      if (run && h === run[4]) { run[2] = x0 + g; continue; }
      if (run) cells.push(run);
      run = h == null ? null : [x0, z0, x0 + g, z1, h];
    }
  }
  const posts = [], E = A1 * T, np = Math.ceil(2 * E / 0.3);
  for (let k = 0; k < 8; k++) for (let i = 0; i < np; i++) {
    const s = -E + 2 * E * i / np, [x, z] = at(k, A1 + 0.07, s), [hx, hz] = at(k, A1 - 0.15, s), h = H(hx, hz); // (just outside the walk: a body's corner reaches 0.57 out on a cut face)
    if (h != null && h > 0.7) posts.push([x, z, h]); // (none by the first three steps: you can get on from the side down there)
  }
  const via = [];
  for (let k = 0; k < 8; k++) {
    const a = at(k, MID, -L + g / 2), b = at(k, MID, L - g / 2);
    via.push([a[0], (10 * k + 1) * r, a[1]], [b[0], (10 * k + 9) * r, b[1]]);
    if (k < 7) { const ph = (135 - 45 * k - 22.5) * Math.PI / 180, R = A0 / Math.cos(Math.PI / 8) + 0.7; via.push([C[0] + Math.cos(ph) * R, (10 * k + 10) * r, C[1] + Math.sin(ph) * R]); }
  }
  const b0 = at(0, MID, -L - 1.3), t0 = at(7, MID, L + 0.8);
  return { cells, posts, via, bot: [b0[0], 0, b0[1]], top: [t0[0], 18, t0[1]], H, r, g };
}
function lighthouse(B0, D0, dx, dz, st, o = {}) {
  const { B, D, add, W, up } = isPiece(B0, D0, dx, dz, st);
  const n0 = B0.boxes.length, d0 = D0.boxes.length; // (drawn as one Blender model, lighthouse.glb / lighthouse_sd.glb without the stair: look only)
  // an octagonal tower (its flats where the old square's sides were: the stair still runs flush along them)
  [['white', 0], ['toyred', 4.5], ['white', 9], ['toyred', 13.5]].forEach(([m, y]) => { for (const b of octoBoxes(79, -9, 85, -3, LH.c)) add(b[0], y, b[1], b[2], y + 4.5, b[3], m); });
  if (o.climb !== false) {
    // the iron stair: once round all eight faces (lhStair), slabs the height of each step under it (drawn by the model,
    // lighthouse.glb), posts along its open side, one walk-graph stair that winds round with it
    const S = lhStair();
    for (const [x0, z0, x1, z1, h] of S.cells) add(x0, h - 0.3, z0, x1, h, z1, 'metal');
    for (const [x, z, h] of S.posts) add(x - 0.07, h - 0.3, z - 0.07, x + 0.07, h + 1.3, z + 0.07, 'metal'); // (taller than the 1 m rail drawn: never a step up from the stair beside it)
    up({ bot: S.bot, top: S.top, via: S.via });
    // the gallery: an octagon 12 m across round the top (open over the last flight), a railing round it: rails on the
    // flats, close-set posts along the cut corners (nobody squeezes between them)
    const GC = 3.515;
    for (const b of octoBoxes(76, -12, 88, 0, GC, 6, LH.hole)) add(b[0], 17.6, b[1], b[2], 18, b[3], 'metal');
    add(76.1, 18, LH.hole[1] - 0.1, LH.hole[2], 19, LH.hole[1], 'metal'); add(76.1, 18, LH.hole[3], 77.05, 19, LH.hole[3] + 0.1, 'metal'); // (the stair well's rails: the way off it is its south end, over the stair's last step)
    for (const [x0, z0, x1, z1] of [[76 + GC, -12, 88 - GC, -11.9], [76 + GC, -0.1, 88 - GC, 0], [76, -12 + GC, 76.1, -GC], [87.9, -12 + GC, 88, -GC]]) add(x0, 18, z0, x1, 19, z1, 'metal');
    for (const [ax, az, bx, bz] of [[76, -12 + GC, 76 + GC, -12], [88 - GC, -12, 88, -12 + GC], [76, -GC, 76 + GC, 0], [88 - GC, 0, 88, -GC]]) {
      const n = Math.ceil(Math.hypot(bx - ax, bz - az) / 0.32);
      for (let k = 0; k <= n; k++) { const x = ax + (bx - ax) * k / n, z = az + (bz - az) * k / n, ix = x + (x < 82 ? 0.09 : -0.09), iz = z + (z < -6 ? 0.09 : -0.09); add(ix - 0.07, 18, iz - 0.07, ix + 0.07, 19, iz + 0.07, 'metal'); }
    }
  }
  for (const b of octoBoxes(80, -8, 84, -4, LH.lc, 3)) add(b[0], 18, b[1], b[2], 21, b[3], 'glass'); D.add(81.4, 18.6, -6.6, 82.6, 20.2, -5.4, 'light'); // the lantern room, octagonal
  for (const b of octoBoxes(79.6, -8.4, 84.4, -3.6, 1.406, 3)) add(b[0], 21, b[1], b[2], 21.5, b[3], 'toyred'); for (const b of octoBoxes(80.6, -7.4, 83.4, -4.6, 0.82, 2)) add(b[0], 21.5, b[1], b[2], 22.2, b[3], 'toyred'); D.box(82, 22.5, -6, 0.6, 0.6, 0.6, 'metal');
  const id = o.climb === false ? 'lighthouse_sd' : 'lighthouse';
  B0.boxes.arch.push({ id, p: [dx, 0, dz], r: 0 }); const tag = { av: id, ai: B0.boxes.arch.length - 1 };
  for (let i = n0; i < B0.boxes.length; i++) Object.assign(B0.boxes[i], tag);
  for (let i = d0; i < D0.boxes.length; i++) if (D0.boxes[i].mat !== 'light') Object.assign(D0.boxes[i], tag); // (the light itself: the game's, it glows)
  D.add(78.94, 1.6, -7.5, 79.0, 2.6, -4.5, 'adlight', { fit: 1 }); // (the sign: the game's picture)
}
// the keeper's cottage (round 71, 9): its door west, windows, a bed, a table
function cottage(B0, D0, dx, dz) {
  const { add, W } = isPiece(B0, D0, dx, dz, []);
  wall(W, 'z', 67.6, 6.375, 11.625, 0, 3, 0.25, 'plaster', [{ a: 8.3, b: 9.7, y0: 0, y1: 2.2 }]);
  wall(W, 'z', 74.4, 6.375, 11.625, 0, 3, 0.25, 'plaster', [{ a: 8.2, b: 9.8, y0: 1.1, y1: 2.1 }]);
  wall(W, 'x', 6.5, 67.725, 74.275, 0, 3, 0.25, 'plaster', [{ a: 70.2, b: 71.8, y0: 1.1, y1: 2.1 }]); wall(W, 'x', 11.5, 67.725, 74.275, 0, 3, 0.25, 'plaster');
  add(67.1, 3, 5.9, 74.9, 3.3, 12.1, 'roofpink'); add(68, 3.3, 6.8, 74, 3.8, 11.2, 'roofpink');
  add(72.6, 0, 9.6, 74.1, 0.55, 11.2, 'bedsheet'); add(69.4, 0, 7, 70.8, 0.8, 8.2, 'wood');
}
// Fort Splinter (round -77, 0): walls to walk (FW), the gate east (o.westGate: a big one west too, else a back door),
// the bastions, merlons, the armoury, the well, the flag, cannons on the east wall. o.walk false: no stairs up to the
// walls. o.pad: the human cannonball on the east wall
function fort(B0, D0, dx, dz, st, o = {}) { // (drawn as one Blender model over these boxes, look only: fort.glb on Islands, fort_sd.glb on S&D)
  const { B, D, add, W, up } = isPiece(B0, D0, dx, dz, st);
  const n0 = B0.boxes.length;
  wall(W, 'x', -12, -84, -70, 0, FW, 2, 'stone'); wall(W, 'x', 12, -84, -70, 0, FW, 2, 'stone');
  wall(W, 'z', -86, -10, 10, 0, FW, 2, 'stone', [o.westGate ? { a: -2.5, b: 2.5, y0: 0, y1: 3.4 } : { a: -1, b: 1, y0: 0, y1: 2.4 }]); wall(W, 'z', -68, -10, 10, 0, FW, 2, 'stone', [{ a: -2.5, b: 2.5, y0: 0, y1: 3.4 }]);
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) { const x = sx < 0 ? -86 : -68, z = sz * 12; add(x - 2, 0, z - 2, x + 2, 6, z + 2, 'stone'); } // the bastions (jump up from the walls)
  // merlons on the walls' outer edges
  for (let x = -83.2; x < -70.5; x += 2.2) for (const z of [-12.7, 12.7]) add(x, FW, z - 0.3, x + 1.2, FW + 1, z + 0.3, 'stone');
  for (let z = -9.2; z < 9.5; z += 2.2) for (const x of [-86.7, -67.3]) if (!(o.pad && x > -70 && Math.abs(z - 6.2) < 0.1)) add(x - 0.3, FW, z, x + 0.3, FW + 1, z + 1.2, 'stone'); // (a gap for the cannonball)
  D.add(-66.94, 3.5, -2.2, -66.88, 4.3, 2.2, 'adfort', { fit: 1 });
  if (o.walk !== false) up({ ...flight(B, true, -72.7, -79.3, -11, -9.6, 0, FW, 'stone'), top: [-78.7, FW, -12] });
  if (o.walk !== false) up({ ...flight(B, true, -82.3, -75.7, 9.6, 11, 0, FW, 'stone'), top: [-76.3, FW, 11.6] });
  // the courtyard: the armoury against the west wall, the well, the flag, barrels and crates, cannonballs
  wall(W, 'x', -3.2, -85, -80.2, 0, 3, 0.4, 'stone'); wall(W, 'x', -8.8, -85, -80.2, 0, 3, 0.4, 'stone');
  wall(W, 'z', -80.4, -8.6, -3.4, 0, 3, 0.4, 'stone', [{ a: -6.7, b: -5.3, y0: 0, y1: 2.2 }]); add(-85, 3, -9, -80, 3.3, -3, 'wood');
  if (!o.westGate) B0.archSince(n0, 'fort', dx, dz); // (Islands: the walls, bastions, merlons, stairs and armoury. its well and flagpole ride the dunes (shared/terrain.js drapes them), so they stay the game's)
  add(-79.2, 0, 3.2, -77.2, 1.0, 5.2, 'stone'); D.add(-78.9, 1.0, 3.5, -77.5, 1.02, 4.9, 'water'); const d0 = D0.boxes.length; for (const x of [-79.1, -77.3]) D.add(x - 0.08, 1.0, 4.12, x + 0.08, 2.6, 4.28, 'wood'); D.add(-79.4, 2.6, 3.6, -77.0, 2.8, 4.8, 'thatch');
  const d1 = D0.boxes.length; add(-74.1, 0, 5.9, -73.9, 11, 6.1, 'metal'); D.add(-73.9, 8.8, 5.96, -71.2, 10.6, 6.04, 'flagskull', { fit: 1 });
  if (o.westGate) { B0.archSince(n0, 'fort_sd', dx, dz); for (let i = d0; i < d1; i++) Object.assign(D0.boxes[i], { av: 'fort_sd', ai: B0.boxes.arch.length - 1 }); } // (S&D, flat ground: the walls, bastions, merlons, armoury, the well and its winch frame, the flagpole. barrels, crates, cannons, the flag stay the game's)
  for (const [x, z] of [[-75, -6], [-75, -4.8], [-73.8, -5.4], [-82, 7.5], [-80.8, 7.8], [-71.5, 8]]) B.box(x, 0.55, z, 1.1, 1.1, 1.1, 'barrel');
  for (const [x, z] of [[-77.5, -1.5], [-71.6, -7.6], [-83.6, 1.5]]) B.box(x, 0.6, z, 1.2, 1.2, 1.2, 'crate');
  for (const [x, z] of [[-73, 2.2], [-82.5, -1.5]]) for (const [ox, oz, oy] of [[-0.3, -0.3, 0], [0.3, -0.3, 0], [-0.3, 0.3, 0], [0.3, 0.3, 0], [0, 0, 0.5]]) D.box(x + ox, 0.25 + oy, z + oz, 0.5, 0.5, 0.5, 'tire');
  // cannons on the east wall (pointing at the volcano), the human cannonball on it
  for (const z of [-7.5, -4.3]) cannon(B, D, -68.2, z, FW, 1, 0);
  if (o.pad) add(-69, FW, 5.6, -67.2, FW + 0.3, 8, 'pad', { pad: [40, 11, -2.4] }); // (lands on the volcano's west beach)
}
// Skull Rock (round 0, 69): a stone skull on the beach, facing the volcano (shared/skullshape.js: the rock is that shape
// in boxes, drawn as one Blender skull, public/models/arch/skullrock.glb). its mouth a cave in to the treasure (gone), a
// floor in each eye, its dome a walk, and its spine up the back of its head (o.climb false: no spine. Islands S&D, where
// the crown's over the ceiling and the tour group's beach is behind it). returns the walk graph's drops
function skullRock(B0, D0, dx, dz, st, o = {}) {
  const { B, D, add, up } = isPiece(B0, D0, dx, dz, st);
  const n0 = B0.boxes.length;
  for (const b of skullSolid()) add(b[0], b[1], b[2], b[3], b[4], b[5], 'skullrock');
  // the spine: steep steps out of the shallows behind it to where the dome starts leaning back. a bot walks straight on up to the crown
  B0.archSince(n0, 'skullrock', dx, dz);
  if (o.climb !== false) { const n1 = B0.boxes.length; up({ ...flight(B, false, SPINE.z0, SPINE.z1, -SPINE.hw, SPINE.hw, ISL.SH, SPINE.top, 'skullrock'), top: [0, SKT, 71] }); for (let i = n1; i < B0.boxes.length; i++) { const v = B0.boxes[i]; v.min[1] = Math.max(v.min[1], v.max[1] - 0.62); } /* (each step a vertebra, open air under it: a bridge of bone, not a wedge) */ B0.archSince(n1, 'skullspine', dx, dz); } // (its own model: skullspine.glb)
  add(-1.95, 0, 69, -0.75, 0.8, 70.2, 'wood'); D.add(-1.9, 0.8, 69.05, -0.8, 0.95, 70.15, 'gold'); // the chest (empty)
  for (const [x, z] of [[-0.4, 68.6], [0.3, 70.8], [-1.2, 71.2], [0.9, 69.4]]) D.box(x, 0.04, z, 0.3, 0.08, 0.3, 'gold'); // a few coins they dropped
  D.add(-1.98, 1.0, 66, -1.94, 2.0, 68.6, 'adtreasure', { fit: 1 });
  return [-1, 1].map((s) => ({ from: [s * 3.5 + dx, SKULL.EYE, 62.5 + dz], to: [s * 3.5 + dx, 0, 59.5 + dz] })); // the walk graph's ways out of the eyes: step off, land on the beach
}

// ------------------------------------------------------------ ISLANDS: Jank Atoll at sunset, under the sun with a face.
// five islands on a warm sea. in the middle Volcano Island: Mount Kaboom (three terraces, two ways up each, a crater
// with a throat that goes all the way down: get knocked in and that's that), the tiki village on its south beach,
// jungle round the back. north the Wreck (the Soggy Biscuit, broken in two on its reef: the hold, the decks, the
// quarterdeck, the crow's nest), east Lighthouse Point (a stair winds round the tower up to the gallery), west Fort
// Splinter (walls to walk, cannons that fire you over the water), south Skull Rock (a cave through its mouth, the
// treasure: already dug up). from the volcano a rope bridge north, the long pier east, a rope bridge west (or the
// cannon), a sandbar south; round the outside sandbars wade from island to island. TDM: the fort vs the lighthouse
function islands() {
  const B = builder(), D = builder(), r = rng(4242), add = B.add, W = B.local(0, 0, 0), Dw = D.local(0, 0, 0);
  B.boxes.arch.push({ id: 'rocks_islands', p: [0, 0, 0], r: 0 }); const RK = { av: 'rocks_islands', ai: B.boxes.arch.length - 1 }; // (its rock: one Blender model, look only)
  const st = []; // the stair flights, for the walk graph
  // ---- the sea and the sun
  D.add(-420, ISL.WY - 0.1, -420, 420, ISL.WY, 420, 'sea');
  D.add(140, 60, -260, 200, 120, -200, 'toyface', { fit: 1 }); // the sun has a face (lighting.js aims the light from it)

  // ---- C, Volcano Island (x -28..28, z -24..24): Mount Kaboom, the tiki village on the south beach, jungle round the back
  isle(B, D, -28, -24, 28, 24, { hole: [-2, -5, 2, -1] });
  slab(Dw, -25.5, -21.5, 25.5, 14, 0, 0.03, 'grass', [-15, -16, 15, 10]);
  B.boxes.arch.push({ id: 'kaboom', p: [0, 0, 0], r: 0 }); // (its dressing: lava channel, cooled flows, cracks, rim rocks, scree. one Blender model laid on the cone, look only)
  const KB = kaboom(B, D, 0, 0), T = KB.throat; // (quick play: a real cone you walk and grapple anywhere. Islands S&D has the same mountain made small: KABOOM_SD)
  tikiBar(B, D, 0, 0, r); bigTiki(B, D, 0, 0);
  hut(B, D, 7.5, 18, -1); hut(B, D, 18.5, 17.2, -1);
  [[-4.5, 21.6], [-2, 21.6], [10.5, 22.2], [13, 22.2], [21.5, 22]].forEach(([x, z], i) => lounger(B, D, x, z, ['toyteal', 'toypink', 'toyyellow'][i % 3]));
  surfSchool(B, D, 0, 0);
  // the cannon on the west beach (the human cannonball: it fires you at the fort)
  cannon(B, D, -24.2, 9, 0, -1, 0); add(-27.3, 0, 7.7, -25.5, 0.3, 10.3, 'pad', { pad: [-34, 15, -7.4] }); // (lands in front of the fort's gate)
  D.add(-22.4, 0, 11.4, -22.28, 2.6, 11.52, 'wood'); D.add(-24.6, 1.6, 11.52, -20.4, 2.6, 11.6, 'adcannon', { fit: 1 });
  // palms all round the beach, the jungle round the back (ferns, bushes you can hide in, boulders)
  for (const [x, z] of [[-25, 22], [-19, 22.5], [-5.5, 23], [4, 23], [16, 23], [25, 21], [25, 12], [-25.5, 13], [-26, 2], [26, 2], [26, -8], [-26, -9], [-25, -21], [-15, -22], [-6, -22.5], [12, -22], [24, -20], [19, -18]]) palm(W, x, z, 5.5 + r() * 3.5, r);
  for (const [x, z] of [[-21, -18], [-9, -19.5], [3, -19], [15, -19.6], [21, -13], [-22, -4], [21, 0], [-19, 6]]) { const s = 0.8 + r() * 0.5; add(x - s, 0, z - s, x + s, s * 1.5, z + s, 'bush'); }
  for (let i = 0; i < 26; i++) { const x = -25 + r() * 50, z = -23 + r() * 8; if (Math.abs(x - 6) > 2.5) D.box(x, 0.4, z, 1.2 + r(), 0.8, 1.2 + r(), 'fern'); }
  for (const [x, z, s] of [[-12, -20, 1.4], [8, -21, 1.2], [23, -16, 1.6], [-24, -15, 1.3]]) { add(x - s, 0, z - s * 0.8, x + s, s * 1.1, z + s * 0.8, 'basalt'); add(x - s * 0.6, s * 1.1, z - s * 0.5, x + s * 0.5, s * 1.5, z + s * 0.6, 'basalt'); }

  // ---- the ways off it: the rope bridge north (a rock to rest on halfway), the pier east (the bait shack halfway),
  // the rope bridge west (or the cannon), the sandbar south
  isle(B, D, 3, -44, 9, -38, { shelf: 1.5 }); palm(W, 8, -39.5, 5.5, r); add(3.4, 0, -43.6, 4.6, 1.0, -42.4, 'basalt');
  B.boxes.arch.push({ id: 'walks_islands', p: [0, 0, 0], r: 0, drape: true }); const WK = { av: 'walks_islands', ai: B.boxes.arch.length - 1 }; // (every rope walk: one Blender model, look only)
  ropeWalk(B, D, false, -58, -44, 6, 2.6, [-53, -45.5], WK); ropeWalk(B, D, false, -38, -24, 6, 2.6, [-36.5, -29], WK);
  add(28, -0.3, 4.5, 62, 0, 7.5, 'wood'); add(42, -0.3, 2, 50, 0, 4.5, 'wood'); add(42, -0.3, 7.5, 50, 0, 10.5, 'wood'); // the pier, wider round the shack
  for (let x = 28.4; x < 62; x += 0.6) D.add(x, 0, 4.5, x + 0.5, 0.025, 7.5, 'planks');
  for (let x = 30; x < 62; x += 4) for (const z of [4.6, 7.4]) D.box(x, -1.3, z, 0.3, 2.2, 0.3, 'wood');
  for (const x of [32, 38, 54, 60]) for (const z of [4.75, 7.25]) B.box(x, 0.3, z, 0.36, 0.6, 0.36, 'tire'); // bollards
  for (const [x0, x1] of [[33, 42], [50, 57]]) for (const z of [4.56, 7.44]) { add(x0, 0.9, z - 0.06, x1, 1.0, z + 0.06, 'wood'); for (let x = x0 + 0.1; x < x1; x += 2) D.add(x, 0, z - 0.05, x + 0.1, 0.9, z + 0.05, 'wood'); } // its rails
  baitShack(B, D, 0, 0);
  isle(B, D, -48, -4, -42, 2, { shelf: 1.5 }); palm(W, -44, 1, 6, r); add(-47.4, 0, -3.8, -46.2, 1.1, -2.7, 'basalt');
  ropeWalk(B, D, true, -62, -48, -1, 2.6, [-57, -49.5], WK); ropeWalk(B, D, true, -42, -28, -1, 2.6, [-40.5, -33], WK);
  sandbar(B, -6, 26.5, -6, 55.5); add(-8.2, -0.6, 36.5, -6.6, 0.6, 38, 'basalt'); add(-5, -0.6, 45, -3.4, 0.8, 46.8, 'basalt');

  // ---- N, the Wreck (x -22..22, z -80..-58): the Soggy Biscuit on its reef, rocks, two palms, a rowboat
  isle(B, D, -22, -80, 22, -58);
  slab(Dw, -19.5, -77.5, 19.5, -60.5, 0, 0.03, 'wetsand', [-18, -73.5, 19.5, -64.5]);
  wreck(B, D, 0, 0, st);
  for (const [x, z, s] of [[-18, -61, 1.2], [17, -61.5, 1.0], [-19, -78, 1.4], [19, -78, 1.1]]) { add(x - s, 0, z - s * 0.8, x + s, s * 1.2, z + s * 0.8, 'rockf', RK); }
  palm(W, -20, -63.5, 6.5, r); palm(W, 20.5, -66, 5.5, r);
  D.add(-20.5, 0, -76, -17.5, 0.6, -74.6, 'boatwood');

  // ---- E, Lighthouse Point (x 62..92, z -18..18): the tower (a stair round it to the gallery), the keeper's cottage, rocks
  isle(B, D, 62, -18, 92, 18);
  slab(Dw, 64.5, -15.5, 89.5, 15.5, 0, 0.03, 'grass', [76, -12, 88, 0]);
  lighthouse(B, D, 0, 0, st); cottage(B, D, 0, 0);
  for (const [x, z, s] of [[89, -15, 1.6], [90, 6, 1.3], [88.5, 14.5, 1.5], [65, -15.5, 1.2], [73, -14, 1.0], [86, 9, 0.9]]) { add(x - s, 0, z - s * 0.8, x + s, s * 1.1, z + s * 0.8, 'rockf', RK); add(x - s * 0.6, s * 1.1, z - s * 0.5, x + s * 0.5, s * 1.5, z + s * 0.6, 'rockf', RK); }
  palm(W, 65, 14.5, 6, r); palm(W, 72, -4.5, 7, r); palm(W, 90, 2.5, 5.5, r);
  for (const [x, z] of [[64.5, 1.5], [65.6, 1.2], [64.8, 10.5]]) B.box(x, 0.4, z, 0.8, 0.8, 0.8, 'crate');

  // ---- W, Fort Splinter (x -92..-62, z -18..18): the fort (the cannonball on its east wall), palms, rocks, a rowboat
  isle(B, D, -92, -18, -62, 18);
  slab(Dw, -89.5, -15.5, -64.5, 15.5, 0, 0.03, 'grass', [-88, -14, -66, 14]);
  fort(B, D, 0, 0, st, { pad: true });
  for (const [x, z] of [[-89, -16], [-80, -16.2], [-70, -15.6], [-64, -14], [-89, 16.2], [-78, 16.4], [-66, 15.5], [-90, -6], [-90, 7]]) palm(W, x, z, 5.5 + r() * 3, r);
  for (const [x, z, s] of [[-65, -8, 1.2], [-64.5, 9, 1.4], [-90.5, 1.5, 1.0]]) { add(x - s, 0, z - s * 0.8, x + s, s * 1.1, z + s * 0.8, 'rockf', RK); }
  D.add(-93.6, -0.2, -2.6, -92.2, 0.4, 0.6, 'boatwood');

  // ---- S, Skull Rock (x -18..18, z 58..84): the skull, palms, rocks, a rowboat
  isle(B, D, -18, 58, 18, 84); // (4 m more beach south than it had: the skull's bigger, and its spine comes down behind it)
  slab(Dw, -15.5, 60.5, 15.5, 81.5, 0, 0.03, 'grass', [-10.5, 60.5, 10.5, 80]);
  const skDrops = skullRock(B, D, 0, 0, st);
  for (const [x, z] of [[-16, 61], [-12, 78], [-6.5, 82.2], [11, 78.4], [16, 78], [16.5, 62.5], [-16.5, 70]]) palm(W, x, z, 5.5 + r() * 3, r);
  for (const [x, z, s] of [[-12, 63.5, 1.1], [12.5, 62.5, 1.3], [-13, 74, 1.0], [12, 73.5, 1.2]]) add(x - s, 0, z - s * 0.8, x + s, s * 1.1, z + s * 0.8, 'rockf', RK);
  D.add(9, -0.2, 85.2, 12.6, 0.4, 86.6, 'boatwood');

  // ---- the sandbars round the outside, each with a palm islet halfway
  sandbar(B, -59.5, -16, -18, -55.5); sandbar(B, 18, -55.5, 59.5, -16); sandbar(B, 59.5, 16, 15, 55.5); sandbar(B, -15, 55.5, -59.5, 16);
  for (const [x, z] of [[-40, -36], [40, -36], [37.5, 36], [-37.5, 36]]) { isle(B, D, x - 3, z - 3, x + 3, z + 3, { shelf: 1 }); palm(W, x + 1.6, z - 1.4, 5 + r() * 2, r); add(x - 2.6, 0, z + 1.2, x - 1.4, 0.9, z + 2.4, 'rockf', RK); }
  for (const [x, z] of [[-50, -26.5], [-28, -46], [50, -26.5], [28, -46], [49, 26], [26.5, 46], [-49, 26], [-26.5, 46]]) add(x - 0.8, ISL.SB, z - 0.7, x + 0.8, 0.9, z + 0.7, 'rockf', RK);

  // ---- spawns: the fort's courtyard and beaches vs the lighthouse's point (TDM); everywhere for the rest
  const att = [[-78, 0.1, -5], [-76, 0.1, 0], [-78, 0.1, 6.5], [-82, 0.1, 2.5], [-72, 0.1, -1.5], [-89.5, 0.1, -8], [-89.5, 0.1, 8]];
  const def = [[76, 0.1, -12], [70, 0.1, -9], [66, 0.1, 2.5], [76.5, 0.1, 13], [83, 0.1, 6], [88, 0.1, -9.5], [70.5, 0.1, 14]];
  const spawns = [...att.slice(0, 3), ...def.slice(0, 3), [-10, 0.1, 22.5], [6, 0.1, 13], [-22, 0.1, -11], [20, 0.1, -10], [0, 9.1, 0.7], [-6, 3.1, -14],
    [-6, 0.1, -67], [12, 0.1, -61], [-12, MD + 0.1, -69], [6, 0.1, -70], [-11, 0.1, 61], [11, 0.1, 76.5], [0, SKT + 0.1, 70], [-40, 0.1, -38], [40, 0.1, 37]];
  // dunes on the islands (shared/terrain.js): up only, the beaches' edges, the volcano, the fort and the huts stay level
  shapeGround(B, D, { region: [-100, -90, 100, 90], mat: 'sand', seed: 3113, up: 1.6, down: 0.12, near: 0.8, far: 4, drape: ['grass'], soft: 1.15, relief: [{ f: KB.f, mat: 'basalt', paint: KB.f.rock, rock: true }], points: [...new Set([...spawns, ...att, ...def])] });
  for (const p of spawns) if (KB.f(p[0], p[2]) != null) p[1] = B.boxes.terrain.at(p[0], p[2]) + 0.1; // (the two up the mountain: onto its new slopes)
  let graph = null;
  const map = { name: 'Islands', size: 'large', boxes: B.boxes, deco: D.boxes, killY: ISL.DROWN, floorY: -1.5, sky: SKY_SUNSET, fogNear: 110, fogFar: 380,
    spawns, teamSpawns: { att, def }, edgeGuard: true, sea: true, seaY: ISL.WY, seaSwim: true, bounds: [-127, -115, 127, 115], pits: [lavaPit(T)], // (sea: falls are 'into the sea' in the kill feed)
    peekGraph() { return graph; }, dropGraph() { graph = null; }, get graph() { return graph || (graph = buildNav(B.boxes, { x0: -100, z0: -90, n: 196, cell: 1, levels: [ISL.SB, 3, MD, 6, QD, 9, SKT, 13.5, 18], band: 0.6, stairs: st, drops: skDrops })); },
  };
  return map;
}

// ------------------------------------------------------------ ISLANDS S&D: the Treasure Tour (Plant & Defuse). the tour
// group (attackers) comes ashore at Skull Rock (south), the pirates (defenders) hold Fort Splinter (north). in the
// middle Volcano Island: Mount Kaboom stands between the two. the sites sit either side of the fort: B, Lighthouse Point
// (west, a rope bridge from the fort's west gate: the tower's foot, the keeper's cottage, lobster pots); A, the Wreck
// (east, over the reef from its east gate: the Soggy Biscuit, plant in the hold). the tour's ways in: up the middle, round
// the volcano and over a boardwalk to the tiki bar's islet (west) or the beach huts' (east), or a sandbar out to either;
// then over the reef (or its boardwalk) onto the site. the fort's walls stand between its courtyard and the middle
function islandsSD() {
  const B = builder(), D = builder(), r = rng(4343), add = B.add, W = B.local(0, 0, 0), Dw = D.local(0, 0, 0);
  B.boxes.arch.push({ id: 'rocks_islands_sd', p: [0, 0, 0], r: 0 }); const RK = { av: 'rocks_islands_sd', ai: B.boxes.arch.length - 1 }; // (its rock: one Blender model, look only)
  const st = [];
  D.add(-420, ISL.WY - 0.1, -420, 420, ISL.WY, 420, 'sea');
  D.add(140, 60, -260, 200, 120, -200, 'toyface', { fit: 1 });

  // ---- N, Fort Splinter (x -18..18, z -82..-46): the pirates' spawn in its courtyard, a gate east and west to the bridges
  isle(B, D, -18, -82, 18, -46, { shelf: 3 }); // (a narrow shelf: 10 m of deep water between it and the middle's)
  slab(Dw, -15.5, -79.5, 15.5, -48.5, 0, 0.03, 'grass', [-11, -78, 11, -50]);
  fort(B, D, 77, -64, st, { westGate: true, walk: false });
  for (const [x, z] of [[-16, -80], [16, -48.5], [-16, -48.5], [16.2, -80]]) palm(W, x, z, 5.5 + r() * 2, r);
  for (const [x, z, s] of [[-15.5, -58, 1.1], [15.5, -70, 1.2]]) add(x - s, 0, z - s * 0.8, x + s, s * 1.1, z + s * 0.8, 'rockf', RK); // cover outside the gates

  // ---- C, Volcano Island (x -21..21, z -28..6): Mount Kaboom between the spawns
  B.boxes.arch.push({ id: 'kaboom_sd', p: [0, 0, 0], r: 0 }); // (its dressing: lava, crust, cracks, ledges, scree. one Blender model laid on the cone, look only)
  const KB = kaboom(B, D, 0, -10, KABOOM_SD), T = KB.throat; // (a sloped cone you walk up, shaped ground: shapeGround below)
  isle(B, D, -21, -28, 21, 6, { hole: T });
  slab(Dw, -19, -26.5, 19, 4.5, 0, 0.03, 'grass', [-15, -26, 15, 0]);
  for (const [x, z] of [[-18, -26], [18, -26.5], [-18.5, 4], [18, 4.5]]) palm(W, x, z, 5.5 + r() * 3, r);
  for (const [x, z] of [[-18, -3], [18, -2], [18.2, -18], [-18.5, -23]]) { const s = 0.8 + r() * 0.4; add(x - s, 0, z - s, x + s, s * 1.5, z + s, 'bush'); }
  for (const [x, z, s] of [[-9, 4, 1.1], [9, 3.5, 1.2]]) add(x - s, 0, z - s * 0.8, x + s, s * 1.1, z + s * 0.8, 'basalt');

  // ---- S, Skull Rock (x -16..16, z 20..50): the tour group's beach, their boats pulled up on it
  isle(B, D, -16, 20, 16, 50);
  slab(Dw, -13.5, 22.5, 13.5, 47.5, 0, 0.03, 'grass', [-10.5, 26.5, 10.5, 47]);
  const skDrops = skullRock(B, D, 0, -33, st, { climb: false });
  for (const [x, z] of [[-14, 22], [14, 23], [-14, 36], [14, 37], [-12.5, 49], [12.5, 49]]) palm(W, x, z, 5.5 + r() * 3, r);
  for (const [x, z, s] of [[-12.5, 28, 1.1], [12.5, 30, 1.2]]) add(x - s, 0, z - s * 0.8, x + s, s * 1.1, z + s * 0.8, 'rockf', RK);
  D.add(-4.5, -0.2, 51.4, -1.5, 0.4, 52.8, 'boatwood'); D.add(2, -0.2, 51.8, 5, 0.4, 53.2, 'boatwood');

  // ---- W, the tiki bar's islet (x -60..-36, z -36..-12); E, the beach huts' (x 36..60, z -36..-12)
  isle(B, D, -60, -36, -36, -12);
  tikiBar(B, D, -36, -42, r); bigTiki(B, D, -36, -42);
  lounger(B, D, -50, -15, 'toyteal'); lounger(B, D, -46, -15, 'toypink');
  for (const [x, z] of [[-58.5, -14], [-37, -13.5], [-59, -33.5], [-37.5, -24.5]]) palm(W, x, z, 5.5 + r() * 3, r);
  isle(B, D, 36, -36, 60, -12);
  hut(B, D, 44.5, -27, 1); hut(B, D, 53, -19, -1);
  lounger(B, D, 57, -30, 'toyyellow'); lounger(B, D, 57.6, -25.6, 'toyteal');
  surfSchool(B, D, 16, -29);
  for (const [x, z] of [[58.5, -14], [37.5, -13.5], [58.8, -34], [37.5, -29]]) palm(W, x, z, 5.5 + r() * 3, r);

  // ---- B, Lighthouse Point (x -62..-34, z -82..-48): the tower's foot (no way up: the site's big cover), the cottage,
  // lobster pots, an upturned boat, rocks
  isle(B, D, -62, -82, -34, -48);
  slab(Dw, -59.5, -79.5, -36.5, -50.5, 0, 0.03, 'grass', [-47, -74, -39, -66]);
  lighthouse(B, D, -125, -64, st, { climb: false }); cottage(B, D, -125, -64);
  for (const [x, z] of [[-50.4, -75], [-49.4, -75.6], [-50, -74], [-38.5, -60], [-37.6, -59], [-55, -63]]) B.box(x, 0.4, z, 0.8, 0.8, 0.8, 'crate');
  add(-47.5, 0, -58.6, -43.5, 0.8, -57, 'boatwood'); // an upturned rowboat
  for (const [x, z, s] of [[-59.5, -79.5, 1.3], [-36.5, -79.5, 1.2], [-59.5, -62, 1.0]]) add(x - s, 0, z - s * 0.8, x + s, s * 1.1, z + s * 0.8, 'rockf', RK);
  palm(W, -60, -50.5, 6, r); palm(W, -36.5, -50.5, 5.5, r);
  siteBoard(D, -43, 1.8, -66.92, 'x', 'siteb', 2.6); siteBoard(D, -54, 0.9, -52.3, 'x', 'siteb', 1.6);

  // ---- A, the Wreck (x 28..70, z -82..-50): the Soggy Biscuit on its reef, crates, rocks
  isle(B, D, 28, -82, 70, -50);
  slab(Dw, 29.5, -79.5, 68, -52.5, 0, 0.03, 'wetsand', [30, -70.5, 67.6, -61.5]);
  wreck(B, D, 48, 3, st);
  for (const [x, z] of [[34, -56], [35, -55.2], [62, -77], [61, -77.8], [36.5, -77]]) B.box(x, 0.45, z, 0.9, 0.9, 0.9, 'crate');
  for (const [x, z, s] of [[31, -81, 1.2], [68, -52.5, 1.1], [67.5, -80, 1.2]]) add(x - s, 0, z - s * 0.8, x + s, s * 1.2, z + s * 0.8, 'rockf', RK);
  palm(W, 30, -52.5, 6, r);
  siteBoard(D, 38, 2.0, -61.42, 'x', 'sitea', 2); siteBoard(D, 54, 2.0, -61.42, 'x', 'sitea', 2);

  // ---- the links: mid (S to C), the sandbars (S to W / E), the boardwalks C to W / E, W to B, E to A, and the pirates'
  // bridge to B. the reef joins the islands round the sites and the middle (the shallows between them used to be a
  // couple of metres of deep water: a jump for a player, a grave for anyone knocked into it); the deep water left is the
  // moat round the fort, the channel under the attackers' bridge and the open sea
  B.boxes.arch.push({ id: 'walks_islands_sd', p: [0, 0, 0], r: 0, drape: true }); const WK = { av: 'walks_islands_sd', ai: B.boxes.arch.length - 1 }; // (every walkway and boardwalk: one Blender model, look only)
  ropeWalk(B, D, false, 6, 20, -4, 2.6, [11, 15], WK);
  sandbar(B, -12.5, 26, -43, -10.5, 20); sandbar(B, 12.5, 26, 43, -10.5, 20); // (wide: they fill the bays between the middle and the islets)
  ropeWalk(B, D, true, -36, -21, -13, 2.6, [0, 0], WK); ropeWalk(B, D, true, 21, 36, -13, 2.6, [0, 0], WK);
  reef(B, -32, -33, -25, -3); reef(B, 25, -33, 32, -3); // C to W / E
  ropeWalk(B, D, false, -48, -36, -54, 2.6, [0, 0], WK); reef(B, -65, -44, -31, -40); // W to B
  ropeWalk(B, D, false, -50, -36, 54, 2.6, [0, 0], WK); reef(B, 31, -46, 65, -40); // E to A
  ropeWalk(B, D, true, -34, -18, -64, 2.6, [-29, -21], WK); ropeWalk(B, D, true, 18, 28, -78, 2.6, [0, 0], WK); reef(B, 20.5, -85, 23.5, -45); // the fort to A
  for (const [x, z] of [[-29, 12], [29, 12], [-39, -1.5], [39, -1.5]]) add(x - 0.8, ISL.SB, z - 0.7, x + 0.8, 0.9, z + 0.7, 'rockf', RK);

  // ---- spawns, the ways in (for the bots), the sites
  const att = [[-6, 0.1, 46], [0, 0.1, 47], [6, 0.1, 46], [-11, 0.1, 44.5], [11, 0.1, 44.5], [-3, 0.1, 48.5], [3, 0.1, 48.5]];
  const def = [[-4, 0.1, -60], [3, 0.1, -64], [0, 0.1, -71], [5, 0.1, -60.5], [-1.5, 0.1, -56], [6, 0.1, -66.5], [-5.5, 0.1, -58]];
  const spawns = [...att.slice(0, 3), ...def.slice(0, 3), [6, 0.1, 2.5], [-48, 0.1, -16], [48, 0.1, -16], [-48, 0.1, -62], [48, 0.1, -56]];
  shapeGround(B, D, { region: [-22, -29, 22, 7], mat: 'sand', seed: 3114, up: 0, down: 0, near: 0.8, far: 4, drape: ['grass'], soft: 1.15, relief: [{ f: KB.f, mat: 'basalt', paint: KB.f.rock, rock: true }], points: [...new Set([...spawns, ...att, ...def])] }); // (only the middle island: flat but for Mount Kaboom)
  let graph = null;
  const map = { name: 'Islands', size: 'large', boxes: B.boxes, deco: D.boxes, killY: ISL.DROWN, floorY: -1.5, sky: SKY_SUNSET, fogNear: 110, fogFar: 380,
    spawns, teamSpawns: { att, def }, edgeGuard: true, ceiling: 9.5, sea: true, seaY: ISL.WY, seaSwim: true, bounds: [-97, -117, 105, 85], pits: [lavaPit(T)],
    nav: {
      B: [
        [[0, 46], [-4, 22], [-4, 5], [-17, 3], [-19, -5], [-19, -13], [-22, -13], [-36, -13], [-40, -20], [-40, -30], [-40, -38], [-40, -44], [-42, -54]], // mid, the tiki bar's islet, the sandbar
        [[-4, 46], [-4, 22], [-4, 5], [-17, 3], [-19, -13], [-36, -13], [-42, -16], [-41, -25], [-48, -31], [-54, -34], [-54, -40], [-54, -47], [-52, -54]], // mid, the islet, the rope bridge
        [[-6, 46], [-12, 38], [-17.5, 26], [-26, 15], [-34, 5], [-41, -3], [-48, -10.5], [-46, -16], [-41, -20], [-41, -25], [-48, -31], [-54, -34], [-54, -40], [-54, -47], [-52, -54]], // the sandbar out west, the rope bridge
        [[0, -64], [-9, -64], [-18, -64], [-26, -64], [-34, -64], [-38, -64], [-42, -62]], // the pirates: the west gate, the bridge
      ],
      A: [
        [[0, 46], [-4, 22], [-4, 5], [10, 3], [17, 3], [19, -5], [19, -13], [22, -13], [36, -13], [40, -20], [40, -30], [40, -38], [40, -44], [42, -55]],
        [[4, 46], [-4, 22], [-4, 5], [17, 3], [19, -13], [36, -13], [42, -16], [48, -23], [54, -31], [54, -37], [54, -44], [54, -50], [52, -56]],
        [[6, 46], [12, 38], [17.5, 26], [26, 15], [34, 5], [41, -3], [48, -10.5], [48, -15], [48, -23], [54, -31], [54, -37], [54, -44], [54, -50], [52, -56]],
        [[0, -64], [9, -64], [13, -70], [16, -77], [22, -78], [28, -78], [34, -77], [40, -76]], // the pirates: the east gate, round the bastion, the bridge behind the wreck
      ],
    },
    sites: [{ id: 'A', min: [32, 0, -80], max: [66, 0, -54] }, { id: 'B', min: [-60, 0, -80], max: [-36, 0, -50] }],
    peekGraph() { return graph; }, dropGraph() { graph = null; }, get graph() { return graph || (graph = buildNav(B.boxes, { x0: -67, z0: -88, n: 145, cell: 1, levels: [ISL.SB, 3, MD, 6, QD, 9], band: 0.6, stairs: st, drops: skDrops })); },
  };
  return map;
}

// ------------------------------------------------------------ the skyline kit (Skyline, Skyline S&D)
// an enclosed glass tube from roof to roof (along x, or z if !alongX) at height y round the line c: a concrete deck,
// glass-block walls, a roof, neon and lamps inside. cover from the sides, its two ends the only ways in
function tubeBridge(B, D, alongX, a0, a1, c, y, w = 4) {
  const P = (bx, p0, yA, q0, p1, yB, q1, m) => (alongX ? bx.add(p0, yA, q0, p1, yB, q1, m) : bx.add(q0, yA, p0, q1, yB, p1, m));
  P(B, a0, y - 0.3, c - w / 2, a1, y, c + w / 2, 'concrete');
  P(B, a0, y, c - w / 2, a1, y + 2.8, c - w / 2 + 0.2, 'glassblock'); P(B, a0, y, c + w / 2 - 0.2, a1, y + 2.8, c + w / 2, 'glassblock');
  P(B, a0, y + 2.8, c - w / 2, a1, y + 3.1, c + w / 2, 'roofg');
  P(D, a0, y + 2.45, c - w / 2 + 0.2, a1, y + 2.55, c - w / 2 + 0.26, 'neoncyan'); P(D, a0, y + 2.45, c + w / 2 - 0.26, a1, y + 2.55, c + w / 2 - 0.2, 'neoncyan');
  for (let a = Math.min(a0, a1) + 4; a < Math.max(a0, a1) - 3; a += 8) P(D, a - 0.4, y + 2.74, c - 0.3, a + 0.4, y + 2.8, c + 0.3, 'lamp');
}
// a tower crane on a roof at (x, z, y): the mast, the jib out toward +x (len), the counter-jib and its weights, the cab,
// a hook hanging off the jib at hookAt. returns the jib's top (y)
function crane(B, D, x, z, y, h = 32, len = 50, hookAt = 30) {
  const top = y + h;
  B.add(x - 1, y, z - 1, x + 1, top, z + 1, 'hazard'); // the mast
  for (let k = y + 4; k < top - 1; k += 4) D.add(x - 1.06, k, z - 1.06, x + 1.06, k + 0.12, z + 1.06, 'metal'); // its bracing
  B.add(x - 1.5, top, z - 1.5, x + 1.5, top + 2.4, z + 1.5, 'toyyellow'); D.add(x + 1.5, top + 1.0, z - 1.2, x + 1.55, top + 2.0, z + 1.2, 'glass'); // the cab
  B.add(x - 14, top + 2.4, z - 0.6, x + len, top + 3.6, z + 0.6, 'hazard'); // the jib and counter-jib
  B.add(x - 14, top + 3.6, z - 1.2, x - 8, top + 6.6, z + 1.2, 'concrete'); // the counterweights
  D.add(x - 0.4, top + 3.6, z - 0.4, x + 0.4, top + 9, z + 0.4, 'hazard'); D.add(x + 0.4, top + 8.7, z - 0.1, x + len * 0.6, top + 8.8, z + 0.1, 'metal'); D.add(x - 13.5, top + 6.6, z - 0.1, x - 0.4, top + 8.8, z + 0.1, 'metal'); // the tie bars
  D.add(x + hookAt - 0.05, top - 14, z - 0.05, x + hookAt + 0.05, top + 2.4, z + 0.05, 'metal'); B.add(x + hookAt - 0.6, top - 15.2, z - 0.6, x + hookAt + 0.6, top - 14, z + 0.6, 'toyred'); // the hook
  return top + 3.6;
}
// a helicopter parked at (x, y, z), nose to +x: body, glass, tail boom, fin, skids (bumped into), rotors (drawn)
function chopper(B, D, x, y, z, livery = 'toyyellow') {
  B.add(x - 2.4, y + 0.6, z - 1.2, x + 2.2, y + 2.8, z + 1.2, livery); B.add(x + 2.2, y + 0.9, z - 1.0, x + 3.4, y + 2.4, z + 1.0, 'glass');
  B.add(x - 8.4, y + 1.7, z - 0.3, x - 2.4, y + 2.3, z + 0.3, livery); B.add(x - 8.8, y + 1.7, z - 0.1, x - 8.0, y + 3.8, z + 0.1, livery);
  for (const s of [-1, 1]) { B.add(x - 2.6, y, z + s * 1.3 - 0.1, x + 2.8, y + 0.15, z + s * 1.3 + 0.1, 'metal'); for (const k of [-1.4, 1.4]) D.add(x + k - 0.06, y + 0.15, z + s * 1.3 - 0.06, x + k + 0.06, y + 0.6, z + s * 1.3 + 0.06, 'metal'); }
  D.add(x - 0.3, y + 2.8, z - 0.3, x + 0.3, y + 3.3, z + 0.3, 'metal'); D.add(x - 6, y + 3.3, z - 0.18, x + 6, y + 3.38, z + 0.18, 'tire'); D.add(x - 0.18, y + 3.3, z - 6, x + 0.18, y + 3.38, z + 6, 'tire');
  D.add(x - 8.5, y + 2.6, z + 0.1, x - 8.3, y + 2.68, z + 1.2, 'tire'); D.add(x - 8.5, y + 2.6, z - 1.2, x - 8.3, y + 2.68, z - 0.1, 'tire');
}

// the Spire (tools/blender/arch/make_spire.py): the hub tower, its deck's parapet, the glass shaft and the mast drawn as
// one Blender model over their boxes (look only: the boxes stay for physics, bots and hits). ranges: [from, to) in B, dr in D
function spireArch(B, D, id, x, z, y, ranges, dr) {
  B.boxes.arch.push({ id, p: [x, y, z], r: 0 }); const tag = { av: id, ai: B.boxes.arch.length - 1 };
  for (const [a, b] of ranges) for (let i = a; i < b; i++) Object.assign(B.boxes[i], tag);
  for (let i = dr[0]; i < dr[1]; i++) Object.assign(D.boxes[i], tag);
}
// the skyline's set pieces, one per top (x, z: the top's middle, y: its roof)
// Jank Cola HQ: the giant can, vending machines, crates of bottles, the billboard
function skyCola(B, D, x, z, y, r) {
  const add = B.add, W = B.local(0, 0, 0);
  {
    propOf('colacan', [x, y, z - 5], 0, () => { // (drawn as the Blender can, p_colacan: tools/blender/make_colacan.py)
    add(x - 2.1, y, z - 7.1, x + 2.1, y + 9, z - 2.9, 'toyred'); // the can: a core you bump into inside an octagon (four turned slabs)
    for (let k = 0; k < 4; k++) { D.obb(x, y + 4.5, z - 5, 6, 9, 2.49, (k * Math.PI) / 4, 'toyred'); D.obb(x, y + 9.15, z - 5, 5.4, 0.3, 2.2, (k * Math.PI) / 4, 'chrome'); for (const y0 of [0.6, 8.0]) D.obb(x, y + y0 + 0.2, z - 5, 6.12, 0.4, 2.54, (k * Math.PI) / 4, 'chrome'); }
    D.add(x - 1.5, y + 9.3, z - 5.4, x + 1.5, y + 9.5, z - 4.6, 'chrome'); // the ring pull
    });
    for (const dx of [-9, -6.5, 6.5, 9]) { add(x + dx - 1, y, z + 9, x + dx + 1, y + 2.4, z + 10.2, dx < 0 ? 'toyred' : 'toyblue'); D.add(x + dx - 0.8, y + 0.8, z + 8.96, x + dx + 0.8, y + 2.1, z + 9, 'glass'); } // vending machines
    cratePile({ add: B.local(0, 0, 0, y) }, x - 12, z - 10, 5, r); cratePile({ add: B.local(0, 0, 0, y) }, x + 9, z - 10, 4, r);
    billboard(W, x, z - 11.6, y, 'x'); }
}
// the rooftop garden: trees, hedges, a fountain, a gazebo, benches
function skyGarden(B, D, x, z, y, r) {
  const add = B.add, W = B.local(0, 0, 0);
  {
    for (const [tx, tz] of [[-11, 4], [11, 4], [-11, 9], [11, 9], [-6, 10], [6, 10]]) lollipop(B.local(x + tx, z + tz, 0, y), 0, 0, 3 + r() * 1.5, r);
    for (const [hx0, hz0, hx1, hz1] of [[-12, -3, -6, -2.2], [6, -3, 12, -2.2], [-3, 5, 3, 5.8]]) add(x + hx0, y, z + hz0, x + hx1, y + 1.1, z + hz1, 'hedge');
    for (const [fx0, fz0, fx1, fz1] of [[-3, -8.6, 3, -8], [-3, -2.6, 3, -2], [-3, -8, -2.4, -2.6], [2.4, -8, 3, -2.6]]) add(x + fx0, y, z + fz0, x + fx1, y + 0.6, z + fz1, 'marble');
    D.add(x - 2.4, y + 0.02, z - 8, x + 2.4, y + 0.45, z - 2.6, 'water'); B.box(x, y + 1.0, z - 5.3, 0.6, 2, 0.6, 'marble'); D.box(x, y + 2.2, z - 5.3, 1.2, 0.4, 1.2, 'marble');
    for (const dx of [-2, 2]) for (const dz of [-2, 2]) B.box(x + 8 + dx, y + 1.3, z - 7 + dz, 0.15, 2.6, 0.15, 'white'); D.add(x + 5.6, y + 2.6, z - 9.4, x + 10.4, y + 2.8, z - 4.6, 'roofteal'); D.add(x + 6.4, y + 2.8, z - 8.6, x + 9.6, y + 3.1, z - 5.4, 'roofteal'); // the gazebo
    for (const bx of [-9, 9]) add(x + bx - 1.4, y, z - 6.4, x + bx + 1.4, y + 0.5, z - 5.8, 'wood'); }
}
// the news studio: the news chopper on its pad, the dish, studio lights, JANK NEWS 24
function skyNews(B, D, x, z, y, r) {
  const add = B.add, W = B.local(0, 0, 0);
  {
    add(x - 7, y, z - 7, x + 3, y + 0.1, z + 7, 'helipad', { fit: 1 }); propOf('heli', [x - 2, y + 0.1, z], 0, () => { chopper(B, D, x - 2, y + 0.1, z, 'toyblue'); D.add(x - 4.5, y + 1.4, z + 1.21, x - 0.5, y + 2.2, z + 1.25, 'adnews', { fit: 1 }); }); // (drawn as the Blender news chopper, p_heli: JANK NEWS 7)
    add(x - 11, y, z + 8, x - 8, y + 1.2, z + 11, 'metal'); D.add(x - 12.5, y + 1.2, z + 6.5, x - 6.5, y + 1.5, z + 12.5, 'white'); D.add(x - 9.7, y + 1.5, z + 9.3, x - 9.3, y + 3.6, z + 9.7, 'metal'); // the dish
    for (const [lx, lz] of [[6, -10], [9, -10], [6, 10], [9, 10]]) { B.box(x + lx, y + 1.4, z + lz, 0.15, 2.8, 0.15, 'metal'); D.box(x + lx, y + 2.9, z + lz, 0.8, 0.6, 0.5, 'lamp'); }
    for (const lz of [-12.6, 12.6]) { add(x + 4, y, z + lz - 0.6, x + 8, y + 1.6, z + lz + 0.6, 'containerb'); }
    for (const px of [-11]) for (const pz of [-12]) { add(x + px - 1.2, y, z + pz - 1.2, x + px + 1.2, y + 2.2, z + pz + 1.2, 'metal'); }
    D.add(x - 12.6, y + 2.5, z - 14.42, x - 2.6, y + 5.5, z - 14.38, 'adnews', { fit: 1 }); for (const px of [-11.6, -3.6]) add(x + px - 0.2, y, z - 14.6, x + px + 0.2, y + 5.8, z - 14.2, 'metal'); }
}
// Putt Putt Palace: mini golf on the roof (little walls, a windmill, the clown, sand traps)
function skyPutt(B, D, x, z, y, r) {
  const add = B.add, W = B.local(0, 0, 0);
  {
    for (const [a0, b0, a1, b1] of [[-10, -12, -2, -11.6], [-10, -6, -2, -5.6], [2, 5.6, 10, 6], [2, 11.6, 10, 12], [-2.4, -11.6, -2, -6], [2, 6, 2.4, 11.6]]) add(x + a0, y, z + b0, x + a1, y + 0.4, z + b1, 'wood');
    add(x + 4, y, z - 11, x + 7, y + 4.5, z - 8, 'white'); D.add(x + 3.6, y + 4.5, z - 11.4, x + 7.4, y + 5.1, z - 7.6, 'roofpink'); D.add(x + 4.5, y + 5.1, z - 10.5, x + 6.5, y + 5.6, z - 8.5, 'roofpink');
    D.box(x + 5.5, y + 3.6, z - 7.88, 6.6, 0.35, 0.12, 'wood'); D.box(x + 5.5, y + 3.6, z - 7.88, 0.35, 6.6, 0.12, 'wood'); D.box(x + 5.5, y + 3.6, z - 7.78, 0.6, 0.6, 0.12, 'toyred'); // the windmill's sails
    D.add(x - 10, y + 0.02, z + 6, x - 4, y + 0.06, z + 10, 'sand'); D.add(x + 1, y + 0.02, z - 4, x + 4, y + 0.06, z - 1, 'sand');
    add(x - 4, y, z - 1.5, x - 1, y + 3, z + 1.5, 'toyface', { fit: 1 }); // the clown (putt into its mouth. you can't)
    for (const [hx, hz] of [[-6, -9], [6, 9], [-7, 2], [8, -3]]) { D.add(x + hx - 0.25, y + 0.02, z + hz - 0.25, x + hx + 0.25, y + 0.04, z + hz + 0.25, 'tire'); D.add(x + hx - 0.03, y, z + hz - 0.03, x + hx + 0.03, y + 1.4, z + hz + 0.03, 'white'); D.add(x + hx + 0.03, y + 1.0, z + hz - 0.02, x + hx + 0.6, y + 1.35, z + hz + 0.02, 'toyred'); } // holes, flags
    D.add(x - 5, y + 2.4, z - 14.42, x + 5, y + 5.4, z - 14.38, 'adputt', { fit: 1 }); for (const px of [-4, 4]) add(x + px - 0.2, y, z - 14.6, x + px + 0.2, y + 5.7, z - 14.2, 'metal'); }
}
// the building site: bare columns, steel stacks, the site hut, the crane (Mr. Smiles sits up its jib)
function skyBuild(B, D, x, z, y, r) {
  const add = B.add, W = B.local(0, 0, 0);
  {
    for (let cx = -10.5; cx <= 10.5; cx += 7) for (let cz = -10.5; cz <= 10.5; cz += 7) if (!(Math.abs(cx) < 4 && Math.abs(cz) < 4)) B.box(x + cx, y + 2, z + cz, 0.8, 4, 0.8, 'metal');
    for (const [sx0, sz0] of [[-8, 5], [3, -8]]) { for (let k = 0; k < 3; k++) add(x + sx0, y + k * 0.35, z + sz0 + k * 0.1, x + sx0 + 5, y + (k + 1) * 0.35, z + sz0 + 0.6 + k * 0.1, 'rust'); }
    add(x + 5, y, z + 5, x + 10, y + 2.6, z + 8, 'containerr'); D.add(x + 5.6, y + 1.0, z + 4.96, x + 8.4, y + 2.0, z + 5, 'adclosed', { fit: 1 }); // the site hut
    for (const [bx, bz] of [[-3, -11], [0, -11], [3, -11]]) add(x + bx - 1.2, y, z + bz - 0.3, x + bx + 1.2, y + 1.0, z + bz + 0.3, 'jersey');
    propOf('crane', [x - 8, y, z - 8], 0, () => crane(B, D, x - 8, z - 8, y, 32, 50, 34)); } // (drawn as the Blender crane, p_crane: tools/blender/make_crane.py)
}
// the greenhouse: glass panes on a steel frame, planting beds inside, water tanks, solar panels
function skyGreen(B, D, x, z, y, r) {
  const add = B.add, W = B.local(0, 0, 0);
  { const gx0 = x - 9, gx1 = x + 5, gz0 = z - 10, gz1 = z + 4;
    for (let a = gx0; a <= gx1 + 0.01; a += 3.5) for (const zz of [gz0, gz1]) B.box(a, y + 1.525, zz, 0.15, 3.05, 0.15, 'metal'); // (a hair into the glass roof)
    for (let a = gz0 + 3.5; a < gz1 - 0.01; a += 3.5) for (const xx of [gx0, gx1]) B.box(xx, y + 1.525, a, 0.15, 3.05, 0.15, 'metal');
    D.add(gx0 + 0.08, y, gz0 - 0.03, gx1 - 0.08, y + 3, gz0 + 0.03, 'greenglass'); D.add(gx0 + 0.08, y, gz1 - 0.03, gx1 - 0.08, y + 3, gz1 + 0.03, 'greenglass');
    D.add(gx0 - 0.03, y, gz0 + 0.08, gx0 + 0.03, y + 3, gz0 + 5, 'greenglass'); D.add(gx0 - 0.03, y, gz0 + 9, gx0 + 0.03, y + 3, gz1 - 0.08, 'greenglass'); D.add(gx1 - 0.03, y, gz0 + 0.08, gx1 + 0.03, y + 3, gz1 - 0.08, 'greenglass'); // (a doorway in the west side)
    D.add(gx0, y + 3, gz0, gx1, y + 3.1, gz1, 'greenglass'); D.add(gx0 + 2, y + 3.1, gz0 + 2, gx1 - 2, y + 3.8, gz1 - 2, 'greenglass');
    for (const bz of [gz0 + 2, gz0 + 6, gz0 + 10]) { add(gx0 + 1.5, y, bz - 0.6, gx1 - 1.5, y + 0.7, bz + 0.6, 'wood'); D.add(gx0 + 1.7, y + 0.7, bz - 0.4, gx1 - 1.7, y + 1.2, bz + 0.4, 'leaves'); }
    for (const tz of [-11, 9]) waterTower(W, x + 10, z + tz, y);
    for (const pz of [7, 10]) { add(x - 11, y, z + pz - 0.5, x - 3, y + 0.6, z + pz + 0.5, 'metal'); D.add(x - 11, y + 0.6, z + pz - 0.9, x - 3, y + 0.68, z + pz + 0.9, 'glassblock'); } } // solar panels
}
// the observatory: its dome, the telescope out of the slit, benches
function skyObs(B, D, x, z, y, r) {
  const add = B.add, W = B.local(0, 0, 0);
  {
    propOf('observatory', [x, y, z], 0, () => { // (drawn as the Blender observatory, p_observatory: tools/blender/make_observatory.py; its sign stays the map's)
    add(x - 6, y, z - 6, x + 6, y + 4, z + 6, 'white'); dome(D, x, y + 4, z, 6, 'chrome', false);
    D.add(x - 0.6, y + 6.2, z + 2, x + 0.6, y + 7.2, z + 9, 'metal'); D.add(x - 0.8, y + 6.0, z + 8.6, x + 0.8, y + 7.4, z + 9.2, 'glass'); // the telescope
    D.add(x - 4, y + 1.5, z + 6, x + 4, y + 3.3, z + 6.06, 'adobs', { fit: 1 }); }, { keep: (b) => !!b.fit });
    for (const [bx, bz] of [[-9, 9], [9, 9], [-9, -9], [9, -9]]) add(x + bx - 1.3, y, z + bz - 0.3, x + bx + 1.3, y + 0.5, z + bz + 0.3, 'wood'); }
}
// the helipad: the big pad, a parked chopper, fuel tanks, the control booth, a windsock. f = -1 puts the tanks and the
// booth on the north side (S&D: out of the line of the attackers' stairs)
function skyHeli(B, D, x, z, y, r, f = 1) {
  const add = B.add, W = B.local(0, 0, 0);
  {
    add(x - 8, y, z - 8, x + 8, y + 0.1, z + 8, 'helipad', { fit: 1 }); propOf('heli', [x + 1, y + 0.1, z - (f < 0 ? 3 : 1)], 0, () => chopper(B, D, x + 1, y + 0.1, z - (f < 0 ? 3 : 1), 'toyred')); // (S&D: off the pad's middle, the site's. drawn as p_heli)
    // (the tanks, the booth and the windsock are drawn as Blender props: tools/blender/make_helipad.py)
    for (const tx of [-11, -8.5]) propOf('fueltank', [x + tx, y, z + f * 10.5], 0, () => { add(x + tx - 0.9, y, z + f * 9.6, x + tx + 0.9, y + 2.6, z + f * 11.4, 'barrelr'); });
    propOf('flightops', [x + 10.8, y, z + f * 10.8], 0, () => { add(x + 9, y, z + f * 9, x + 12.6, y + 2.8, z + f * 12.6, 'metal'); D.add(x + 8.96, y + 1.2, z + f * 9.4, x + 9, y + 2.4, z + f * 12.2, 'glass'); }); // the booth
    propOf('windsock', [x + 12.5, y, z - f * 12.5], 0, () => { B.box(x + 12.5, y + 2, z - f * 12.5, 0.15, 4, 0.15, 'metal'); D.add(x + 12.5, y + 3.4, z - f * 12.6, x + 14, y + 3.9, z - f * 12.4, 'hazard'); }); }
}

// ------------------------------------------------------------ SKYLINE: the high city. nine tops in a three by three grid
// over a downtown at dusk, 72 m apart, the street 160 m under them. in the middle the Spire: the hub deck at 40 and its
// glass shaft up five floors to a sniper's nest at 62 (pads up there fling you back out). round it four towers at 40,
// each a set piece (Jank Cola's HQ with its giant can, a rooftop garden, the news studio's helipad, mini golf), joined to
// the hub by glass tubes (north and south) and open girder bridges (east and west). on the corners two low towers at
// 30 (the building site with its crane, the greenhouse: the teams' ends) and two high ones at 52 (the observatory, the
// helipad: sniper roofs), long stair-bridges up and down to the ring
function skyline() {
  const B = builder(), D = builder(), r = rng(1337), add = B.add, W = B.local(0, 0, 0), Dw = D.local(0, 0, 0);
  const base = -120, S = 72, R = 40, pick = (a) => a[(r() * a.length) | 0];
  const hi = 52, lo = 30;
  let spireC = null;
  // ---- the nine tops (half sizes): the Spire 13 x 13, the ring 15 x 13 (north/south) / 13 x 15 (east/west), the corners 14 x 14
  const tops = { C: [0, 0, 13, 13, R], N: [0, -S, 15, 13, R], S: [0, S, 15, 13, R], W: [-S, 0, 13, 15, R], E: [S, 0, 13, 15, R],
    NW: [-S, -S, 14, 14, lo], SE: [S, S, 14, 14, lo], NE: [S, -S, 14, 14, hi], SW: [-S, S, 14, 14, hi] };
  const gaps = { C: { n: [[-2, 2]], s: [[-2, 2]], w: [[-2, 2]], e: [[-2, 2]] }, N: { s: [[-2, 2]], w: [[-S - 2, -S + 2]], e: [[-S - 2, -S + 2]] }, S: { n: [[-2, 2]], w: [[S - 2, S + 2]], e: [[S - 2, S + 2]] },
    W: { e: [[-2, 2]], n: [[-S - 2, -S + 2]], s: [[-S - 2, -S + 2]] }, E: { w: [[-2, 2]], n: [[S - 2, S + 2]], s: [[S - 2, S + 2]] },
    NW: { e: [[-S - 2, -S + 2]], s: [[-S - 2, -S + 2]] }, NE: { w: [[-S - 2, -S + 2]], s: [[S - 2, S + 2]] }, SW: { e: [[S - 2, S + 2]], n: [[-S - 2, -S + 2]] }, SE: { w: [[S - 2, S + 2]], n: [[S - 2, S + 2]] } };
  const facade = { C: 'glassblock', N: 'office', S: 'tenement', W: 'office', E: 'tenement', NW: 'concrete', SE: 'office', NE: 'tenement', SW: 'office' };
  for (const [k, [x, z, hx, hz, y]] of Object.entries(tops)) {
    const n0 = B.boxes.length;
    roofTop(B, x - hx, z - hz, x + hx, z + hz, y, facade[k], gaps[k], base);
    if (k === 'S') B.archSince(n0, 'tenement', x, z, 0, y); // the south tower: a Blender tenement (archfield.js)
    if (k === 'C') spireC = [n0, B.boxes.length]; // (the Spire's tower: drawn by its model, below)
    D.add(x - hx + 0.3, y, z - hz + 0.3, x + hx - 0.3, y + 0.02, z + hz - 0.3, k === 'S' ? 'lawn' : k === 'E' ? 'lawn' : 'asphalt'); // the roof's skin
  }
  // ---- the links: the hub to the ring (glass tubes north and south, girder bridges east and west), the ring to the corners
  tubeBridge(B, D, false, -13.4, -S + 13.4, 0, R); tubeBridge(B, D, false, 13.4, S - 13.4, 0, R);
  skyBridge(B, D, true, -S + 13.4, -13.4, 0, R, 4); skyBridge(B, D, true, 13.4, S - 13.4, 0, R, 4, {}, ['neonpink', 'neonyellow']);
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
    const cy = sx === sz ? lo : hi; // NW and SE are the low corners
    stairBridge(B, true, sx * 15.4, sx * (S - 14.4), sz * S, R, cy, 4, true); // from the north / south tower along x
    stairBridge(B, false, sz * 15.4, sz * (S - 14.4), sx * S, R, cy, 4, true); // from the west / east tower along z
  }

  // ---- C, the Spire: the hub deck round its glass shaft (five floors of windows, stairs inside, a sniper's nest on top)
  const Sp = B.local(0, 0, 0, R), sp0 = B.boxes.length, sd0 = D.boxes.length;
  shell(Sp, 12, 12, 5, 4.4, 'glassblock', { floor: 'grid', roof: 'roofg', roofAccess: true, backDoor: true, sideDoor: [-1.5, 1.5], winSpacing: 3 });
  B.box(0, R + 22.3 + 9, 0, 0.6, 18, 0.6, 'metal'); D.box(0, R + 22.3 + 18.3, 0, 0.6, 0.6, 0.6, 'neonred'); D.box(0, R + 22.3 + 12, 0, 1.2, 0.3, 1.2, 'neonpink'); // the mast on the nest
  spireArch(B, D, 'spire', 0, 0, R, [spireC, [sp0, B.boxes.length]], [sd0, D.boxes.length]);
  for (const [x, z] of [[-9, -9], [9, -9], [-9, 9], [9, 9]]) { add(x - 1.2, R, z - 1.2, x + 1.2, R + 0.8, z + 1.2, 'stone'); D.add(x - 1.0, R + 0.8, z - 1.0, x + 1.0, R + 1.6, z + 1.0, 'hedge'); } // planters at the deck's corners
  for (const [x, z, al] of [[-9.5, -4, false], [9.5, 4, false], [-4, 9.5, true]]) add(al ? x - 1.5 : x - 0.3, R, al ? z - 0.3 : z - 1.5, al ? x + 1.5 : x + 0.3, R + 0.5, al ? z + 0.3 : z + 1.5, 'wood'); // benches
  for (const [px, pz, v] of [[0, -4.5, [0, 14, -30]], [0, 4.5, [0, 14, 30]], [-4.5, -3, [-30, 14, 0]], [4.5, 0, [30, 14, 0]]]) add(px - 1, R + 22.3, pz - 1, px + 1, R + 23.2, pz + 1, 'pad', { pad: v }); // off the nest, out to the ring (on pedestals over the parapet's top: hop up, get flung)

  // ---- the set pieces on the tops (the skyline kit, below the map)
  skyCola(B, D, 0, -S, R, r);
  skyGarden(B, D, 0, S, R, r);
  skyNews(B, D, -S, 0, R, r);
  skyPutt(B, D, S, 0, R, r);
  skyBuild(B, D, -S, -S, lo, r);
  skyGreen(B, D, S, S, lo, r);
  skyObs(B, D, S, -S, hi, r);
  skyHeli(B, D, -S, S, hi, r);
  // ---- grapple bait: window washers' platforms on the towers' faces, gold blocks hanging over the gaps
  for (const [k, [x, z, hx, hz, y]] of Object.entries(tops)) for (const [nx, nz] of [[0, -1], [0, 1], [-1, 0], [1, 0]]) {
    if (r() < 0.45) continue;
    const py = y - 14 - r() * 20, fx = x + nx * (hx + 1), fz = z + nz * (hz + 1), off = (r() - 0.5) * 6;
    B.box(nx ? fx : x + off, py, nz ? fz : z + off, nx ? 1.6 : 6, 0.4, nx ? 6 : 1.6, 'metal');
  }
  for (const [gx, gy, gz] of [[-36, 70, -36], [36, 74, 36], [-36, 66, 36], [36, 70, -36], [0, 80, -36], [0, 80, 36], [-36, 76, 0], [36, 76, 0]]) B.box(gx, gy, gz, 4, 1.2, 4, 'gold');

  // ---- spawns: the two low corners are the teams' ends (the Spire stands between them); the rest everywhere
  const att = [[-S - 6, lo + 0.2, -S + 2], [-S - 2, lo + 0.2, -S + 2], [-S + 2, lo + 0.2, -S + 2], [-S - 6, lo + 0.2, -S - 2], [-S + 6, lo + 0.2, -S - 3], [-S - 2, lo + 0.2, -S + 9], [-S + 2, lo + 0.2, -S - 6]];
  const def = att.map(([x, y, z]) => [-x, y, -z]);
  const spawns = [...att.slice(0, 3), ...def.slice(0, 3), [0, R + 0.2, -9], [0, R + 0.2, 9], [-9, R + 0.2, 0], [9, R + 0.2, 0], [0, R + 0.2, -S + 6], [0, R + 0.2, S - 11], [-S + 6, R + 0.2, 0], [S - 6, R + 0.2, 0],
    [S - 8, hi + 0.2, -S - 8], [S + 8, hi + 0.2, -S + 8], [-S + 8, hi + 0.2, S + 8], [-S - 8, hi + 0.2, S - 8], [0, R + 0.4, 0], [3, R + 22.5, 3]];

  // ---- the look (render-only): the street far below, crowns and cables round the towers, the city to the fog
  const rs = rng(4041), plan = [], roofs = {};
  for (const [x, z, w, h, t] of [[-150, -150, 34, 70, 3], [0, -150, 30, 20, 2], [150, -150, 36, 90, 3], [-150, 0, 30, 10, 2], [150, 0, 34, 60, 3], [-150, 150, 32, 85, 3], [0, 150, 36, 35, 2], [150, 150, 30, 15, 2],
    [-75, -150, 26, -20, 1], [75, -150, 28, 45, 2], [-150, -75, 26, 30, 2], [150, 75, 26, -10, 1], [-75, 150, 30, 55, 3], [75, 150, 24, 0, 1], [-150, 75, 28, 40, 2], [150, -75, 30, 25, 2]]) {
    const ry = tower(D, x, z, w, w, h, { tiers: t, base, r: rs }); D.box(x, base - 10, z, w, 20, w, 'office'); plan.push([x, z, w, w, h, t]); roofs[`${x},${z}`] = ry;
  }
  const ours = Object.values(tops).map(([x, z, hx, hz, y]) => ({ x, z, w: hx * 2, d: hz * 2, y }));
  for (const o of ours) { D.add(o.x - o.w / 2 - 0.06, o.y - 2.6, o.z - o.d / 2 - 0.06, o.x + o.w / 2 + 0.06, o.y - 2.1, o.z + o.d / 2 + 0.06, pick(['neoncyan', 'neonpink', 'neonyellow'])); D.add(o.x - o.w / 2, base - 20, o.z - o.d / 2, o.x + o.w / 2, base, o.z + o.d / 2, 'office'); }
  const roads = { xs: [-185, -110, -36, 36, 110, 185], zs: [-185, -110, -36, 36, 110, 185], w: 18 };
  streetLevel(D, -120, [...plan.map(([x, z, w, d]) => ({ x, z, w, d })), ...ours], roads, 200, rs);
  cityDress(D, plan, roofs, base, rs);
  cityBeyond(D, -120, 200, 680, rng(4040), { kill: -108, cap: 30, shore: 470, avenues: [[-60, -230, 0.42], [230, 40, -1.05], [-300, 120, 1.25], [80, -420, 0.06], [-250, -250, 2.35]], streets: gridOut(roads.xs, roads.zs, 200, 200) });

  let graph = null;
  const map = { name: 'Skyline', size: 'huge', boxes: B.boxes, deco: D.boxes, killY: -119.7, fall: 'street', floorY: -128, cityR: 680, cityCap: 30,
    haze: { k: 0.88, top: 15, bottom: -120, dist: 120, color: 0xc89aa4 }, // look down: the city through a dusk haze
    sky: { top: 0x1a2a5a, mid: 0xff9a5a, bot: 0x0a0a1a, fog: 0xd98a6a }, fogNear: 160, fogFar: 700, spawns, teamSpawns: { att, def }, edgeGuard: true,
    traffic: { grid: { ...roads, S: 200, y: -120 + 0.08, off: 5 } },
    peekGraph() { return graph; }, dropGraph() { graph = null; }, get graph() { return graph || (graph = buildNav(B.boxes, { x0: -90, z0: -90, n: 180, cell: 1, levels: [lo, R, hi], band: 0.6,
      stairs: [-1, 1].flatMap((sx) => [-1, 1].flatMap((sz) => { const cy = sx === sz ? lo : hi, hiEnd = cy > R;
        const a = { p: [sx * 14.4, R, sz * S], q: [sx * (S - 13.4), cy, sz * S] }, b = { p: [sx * S, R, sz * 14.4], q: [sx * S, cy, sz * (S - 13.4)] };
        return [a, b].map(({ p, q }) => (hiEnd ? { top: q, bot: p } : { top: p, bot: q })); })) })); },
  };
  return map;
}


// ------------------------------------------------------------ SKYLINE S&D: the Spire job (Plant & Defuse). the crashers
// (attackers) come up the Jank Cola tower (south), ☺ CORP's security (defenders) hold their HQ tower (north). in the
// middle, 4 m down, the Spire's hub deck round its glass shaft (it stands between the spawns). the sites sit either
// side of the HQ, a stair-bridge up from it to each: B, the observatory's roof (west); A, the helipad's (east). the
// crashers' ways in: down into mid and up the stair-bridge onto the news / mini-golf roof, or out along the side (down
// onto the garden / the greenhouse, up onto the news / mini-golf roof), then up one of two stair-bridges onto the site.
// both spawn towers have a privacy wall along their edge over mid
function skylineSD() {
  const B = builder(), D = builder(), r = rng(1338), add = B.add, W = B.local(0, 0, 0), Dw = D.local(0, 0, 0);
  const base = -120, Cy = 36, pick = (a) => a[(r() * a.length) | 0];
  // ---- the tops: [x, z, half x, half z, roof y]. middle column x [-14, 14]: the HQ z [-78, -50], the hub z [-40, 2],
  // the cola tower z [10, 38]. either side x [34, 62]: the sites z [-84, -46], the news / mini-golf roofs z [-39, -9],
  // the garden / greenhouse z [-2, 26]
  const tops = { N: [0, -64, 14, 14, 40], C: [0, -19, 14, 21, Cy], S: [0, 24, 14, 14, 40], B: [-48, -65, 14, 19, 46], A: [48, -65, 14, 19, 46],
    W: [-48, -24, 14, 15, 42], E: [48, -24, 14, 15, 42], SW: [-48, 12, 14, 14, 38], SE: [48, 12, 14, 14, 38] };
  const gaps = { N: { s: [[-2, 2]], w: [[-66, -62]], e: [[-66, -62]] }, C: { n: [[-2, 2]], s: [[-2, 2]], w: [[-26, -22]], e: [[-26, -22]] }, S: { n: [[-2, 2]], w: [[16, 20]], e: [[16, 20]] },
    B: { e: [[-66, -62]], s: [[-58, -54], [-42, -38]] }, A: { w: [[-66, -62]], s: [[38, 42], [54, 58]] },
    W: { n: [[-58, -54], [-42, -38]], e: [[-26, -22]], s: [[-50, -46]] }, E: { n: [[38, 42], [54, 58]], w: [[-26, -22]], s: [[46, 50]] },
    SW: { n: [[-50, -46]], e: [[16, 20]] }, SE: { n: [[46, 50]], w: [[16, 20]] } };
  const facade = { N: 'office', C: 'glassblock', S: 'tenement', B: 'tenement', A: 'office', W: 'office', E: 'tenement', SW: 'office', SE: 'tenement' };
  let spireC = null;
  for (const [k, [x, z, hx, hz, y]] of Object.entries(tops)) {
    const n0 = B.boxes.length;
    roofTop(B, x - hx, z - hz, x + hx, z + hz, y, facade[k], gaps[k], base);
    if (k === 'C') spireC = [n0, B.boxes.length]; // (the Spire's hub tower: drawn by its model, below)
    D.add(x - hx + 0.3, y, z - hz + 0.3, x + hx - 0.3, y + 0.02, z + hz - 0.3, k === 'SW' || k === 'E' ? 'lawn' : 'asphalt');
  }
  // ---- the links
  stairBridge(B, false, 2.4, 9.6, 0, Cy, 40); stairBridge(B, false, -40.4, -49.6, 0, Cy, 40); // the hub up to the cola tower, up to the HQ
  for (const s of [-1, 1]) {
    stairBridge(B, true, s * 33.6, s * 14.4, 18, 38, 40, 4, true); // the cola tower down to the garden / greenhouse
    stairBridge(B, false, -2.4, -8.6, s * 48, 38, 42); // the garden / greenhouse up to the news / mini-golf roof
    for (const x of [40, 56]) stairBridge(B, false, -39.4, -45.6, s * x, 42, 46); // up onto the site (two ways)
    stairBridge(B, true, s * 14.4, s * 33.6, -24, Cy, 42, 4, true); // mid up to the news / mini-golf roof
    stairBridge(B, true, s * 14.4, s * 33.6, -64, 40, 46, 4, true); // the HQ up to the site
  }
  // privacy walls on the spawn towers' edges over mid (open at the stairs)
  for (const [x0, x1] of [[-14.4, -2], [2, 14.4]]) { add(x0, 41, 9.6, x1, 43.2, 10, 'glassblock'); D.add(x0, 43.2, 9.54, x1, 43.35, 10.06, 'neonpink'); add(x0, 41, -50, x1, 43.2, -49.6, 'glassblock'); D.add(x0, 43.2, -50.06, x1, 43.35, -49.54, 'neoncyan'); }
  // ---- mid: the Spire's hub deck, its shaft (four floors, stairs inside, a roof to snipe from), planters, benches, AC
  const sp0 = B.boxes.length, sd0 = D.boxes.length;
  shell(B.local(0, -19, 0, Cy), 12, 12, 4, 4.4, 'glassblock', { floor: 'grid', roof: 'roofg', roofAccess: true, backDoor: true, sideDoor: [-1.5, 1.5], winSpacing: 3 });
  B.box(0, Cy + 17.9 + 7, -19, 0.6, 14, 0.6, 'metal'); D.box(0, Cy + 17.9 + 14.3, -19, 0.6, 0.6, 0.6, 'neonred');
  spireArch(B, D, 'spire_sd', 0, -19, Cy, [spireC, [sp0, B.boxes.length]], [sd0, D.boxes.length]);
  for (const [x, z] of [[-9, -36], [9, -36], [-9, -2], [9, -2]]) { add(x - 1.2, Cy, z - 1.2, x + 1.2, Cy + 0.8, z + 1.2, 'stone'); D.add(x - 1.0, Cy + 0.8, z - 1.0, x + 1.0, Cy + 1.6, z + 1.0, 'hedge'); }
  for (const [x, z] of [[-10, -30], [10, -8]]) add(x - 0.3, Cy, z - 1.5, x + 0.3, Cy + 0.5, z + 1.5, 'wood');
  acUnit(W, -10, -10, Cy); acUnit(W, 10, -30, Cy); B.box(-4, Cy + 0.6, -33, 1.2, 1.2, 1.2, 'crate'); B.box(5, Cy + 0.6, -4, 1.2, 1.2, 1.2, 'crate');
  // ---- the set pieces
  skyObs(B, D, -48, -74, 46, r); skyHeli(B, D, 48, -65, 46, r, -1); // the two sites
  skyNews(B, D, -48, -24, 42, r); skyPutt(B, D, 48, -24, 42, r); skyGarden(B, D, -48, 12, 38, r); skyGreen(B, D, 48, 12, 38, r);
  skyCola(B, D, 0, 24, 40, r); // the crashers' tower
  // more cover on the sites (the bomb wants somewhere to hide)
  for (const s of [-1, 1]) { acUnit(W, s * 58, -50, 46); acUnit(W, s * 58, -80, 46); B.box(s * 38, 46.6, -80, 1.2, 1.2, 1.2, 'crate'); B.box(s * 39.4, 46.6, -80, 1.2, 1.2, 1.2, 'crate'); B.box(s * 52, 46.45, -50, 0.9, 0.9, 0.9, 'metal'); }
  // the sites' cover. both: a building in the back corner with the site letter on it (B: a lift house, A: the helipad's
  // booth), a crate stack, the letter on the tower's face under the attackers' stairs. B: the ticket kiosk, a planter, coin
  // telescopes. A: the chopper's cargo, jersey barriers by the defenders' way in
  B.box(-59.5, 47.6, -74.8, 3.8, 3.2, 4.4, 'concrete'); B.box(-59.5, 49.35, -74.8, 4.2, 0.3, 4.8, 'roofg');
  D.add(-60.4, 46, -72.6, -58.8, 48.2, -72.5, 'metal'); siteBoard(D, -57.52, 46.8, -74.8, 'z', 'siteb', 2.6);
  siteBoard(D, 58.8, 46.5, -73.92, 'x', 'sitea', 1.8);
  for (const s of [-1, 1]) siteBoard(D, s * 48, 42.6, -45.92, 'x', s < 0 ? 'siteb' : 'sitea', 3);
  for (const [x, z, y] of [[-44.5, -61, 46.6], [-44.5, -62.4, 46.6], [-44.4, -61.7, 47.8], [45.1, -54.6, 46.6], [46.5, -54.4, 46.6], [45.8, -54.5, 47.8]]) B.box(x, y, z, 1.2, 1.2, 1.2, 'crate');
  add(-39.2, 46, -75.2, -36.8, 48.6, -72.8, 'toyteal'); add(-39.4, 48.6, -75.4, -36.6, 48.9, -72.6, 'roofg'); // the kiosk
  D.add(-39.3, 47.2, -74.6, -39.2, 48.2, -73.4, 'glass'); siteBoard(D, -38, 46.5, -72.72, 'x', 'siteb', 1.8);
  add(-57, 46, -62, -53, 47, -60.8, 'concrete'); D.add(-56.8, 47, -61.8, -53.2, 47.1, -61, 'lawn'); // the planter
  for (const x of [-50, -46]) { B.box(x, 46.6, -47.6, 0.2, 1.2, 0.2, 'metal'); B.box(x, 47.45, -47.5, 0.36, 0.36, 0.8, 'toyyellow'); } // coin telescopes
  for (const z of [-69.5, -58.5]) add(37.6, 46, z - 1.5, 38.4, 46.9, z + 1.5, 'jersey');
  // B: the radio mast, its plinth the cover between the two stairs. A: the fuel cart by the near stairs. both: roof vents
  add(-51, 46, -55.6, -47.8, 48.6, -52.4, 'concrete'); add(-51.2, 48.6, -55.8, -47.6, 48.9, -52.2, 'roofg');
  D.box(-49.4, 53, -54, 0.3, 8.2, 0.3, 'metal'); for (const [y, w] of [[54.4, 2.6], [56.2, 1.6]]) D.box(-49.4, y, -54, w, 0.12, 0.12, 'metal');
  for (const s of [-1, 1]) D.box(-49.4 + s * 0.55, 51.6, -53.55, 0.8, 1.1, 0.3, 'white'); D.box(-49.4, 57.25, -54, 0.4, 0.3, 0.4, 'neonpink');
  propOf('fuelcart', [44, 46, -50], 0, () => { // (drawn as the Blender fuel bowser, p_fuelcart)
  add(43, 46.5, -52.6, 45, 48.4, -47.4, 'toyred'); add(43.2, 48.4, -52.3, 44.8, 49.0, -48.2, 'chrome'); // the fuel cart
  for (const z of [-51.6, -48.4]) for (const x of [42.85, 45.15]) D.box(x, 46.4, z, 0.2, 0.8, 0.8, 'tire'); });
  for (const [x, z] of [[-60.6, -58], [-35.6, -52], [-60.6, -66], [60.6, -60], [35.6, -78], [60.6, -66]]) { B.box(x, 46.25, z, 0.6, 0.5, 0.6, 'metal'); D.box(x, 46.53, z, 0.4, 0.06, 0.4, 'grid'); }
  // ☺ CORP HQ (security): the flag on its mast frame, two machine rooms, AC
  for (const x of [-6, 6]) add(x - 0.2, 40, -77.6, x + 0.2, 47, -77.2, 'metal');
  D.add(-8, 42.5, -77.42, 8, 46.8, -77.38, 'flagcorp', { fit: 1 });
  for (const s of [-1, 1]) { add(s * 6, 40, -60, s * 11, 44, -55, 'concrete'); add(s * 5.8, 44, -60.2, s * 11.2, 44.3, -54.8, 'roofg'); acUnit(W, s * 11, -74, 40); }
  // ---- outside: the city round about (render-only)
  const rs = rng(4042), plan = [], roofs = {};
  for (const [x, z, w, h, t] of [[-130, -130, 34, 70, 3], [0, -140, 30, 30, 2], [130, -130, 36, 90, 3], [-130, -20, 30, 20, 2], [130, -20, 34, 60, 3], [-130, 90, 32, 85, 3], [0, 110, 30, 35, 2], [130, 90, 30, 25, 2]]) {
    const ry = tower(D, x, z, w, w, h, { tiers: t, base, r: rs }); D.box(x, base - 10, z, w, 20, w, 'office'); plan.push([x, z, w, w, h, t]); roofs[`${x},${z}`] = ry;
  }
  const ours = Object.values(tops).map(([x, z, hx, hz, y]) => ({ x, z, w: hx * 2, d: hz * 2, y }));
  for (const o of ours) { D.add(o.x - o.w / 2 - 0.06, o.y - 2.6, o.z - o.d / 2 - 0.06, o.x + o.w / 2 + 0.06, o.y - 2.1, o.z + o.d / 2 + 0.06, pick(['neoncyan', 'neonpink', 'neonyellow'])); D.add(o.x - o.w / 2, base - 20, o.z - o.d / 2, o.x + o.w / 2, base, o.z + o.d / 2, 'office'); }
  const roads = { xs: [-170, -95, -23, 23, 95, 170], zs: [-170, -103, 48, 150], w: 14 }; // ±23 so the +x streetlight arms clear the tower walls
  streetLevel(D, -120, [...plan.map(([x, z, w, d]) => ({ x, z, w, d })), ...ours], roads, 200, rs);
  cityDress(D, plan, roofs, base, rs);
  cityBeyond(D, -120, 200, 680, rng(4043), { kill: -108, cap: 30, shore: 470, avenues: [[-60, -230, 0.42], [230, 40, -1.05], [-300, 120, 1.25], [80, -420, 0.06], [-250, -250, 2.35]], streets: gridOut(roads.xs, roads.zs, 200, 200) });

  const att = [[-4, 40.2, 30], [0, 40.2, 31], [4, 40.2, 30], [-10, 40.2, 30], [10, 40.2, 30], [-3, 40.2, 36], [3, 40.2, 36]];
  const def = [[-4, 40.2, -70], [0, 40.2, -71], [4, 40.2, -70], [-10, 40.2, -70], [10, 40.2, -70], [-3, 40.2, -75], [3, 40.2, -75]];
  const spawns = [...att.slice(0, 3), ...def.slice(0, 3), [-48, 46.2, -52], [48, 46.2, -52], [-56, 42.2, -24], [56, 42.2, -24], [-40, 38.2, 22], [40, 38.2, 25], [0, Cy + 0.2, -34], [-10, Cy + 0.2, -19], [10, Cy + 0.2, -19]];
  let graph = null;
  const map = { name: 'Skyline', size: 'huge', boxes: B.boxes, deco: D.boxes, killY: -119.7, fall: 'street', floorY: -128, cityR: 680, cityCap: 30,
    haze: { k: 0.88, top: 15, bottom: -120, dist: 120, color: 0xc89aa4 },
    sky: { top: 0x1a2a5a, mid: 0xff9a5a, bot: 0x0a0a1a, fog: 0xd98a6a }, fogNear: 160, fogFar: 700, spawns, teamSpawns: { att, def }, edgeGuard: true,
    traffic: { grid: { ...roads, S: 200, y: -120 + 0.08, off: 5 } },
    nav: {
      A: [
        [[0, 31], [8, 26], [14, 18], [24, 18], [35, 17], [37, 0], [48, -1], [48, -6], [48, -12], [36, -18], [36, -36], [40, -39], [40, -43], [40, -48], [44, -58]], // the side: the greenhouse roof, mini golf, up the near stairs
        [[2, 31], [5, 24], [3, 12], [0, 9], [0, 6], [0, 1], [9, -10], [12, -24], [16, -24], [24, -24], [34, -24], [36, -30], [36, -36], [40, -39], [40, -43], [40, -48], [44, -58]], // mid, up to mini golf, up the near stairs
        [[4, 31], [8, 26], [14, 18], [24, 18], [35, 17], [37, 0], [48, -1], [48, -6], [48, -10], [60, -10], [60, -36], [56, -39], [56, -43], [56, -48], [52, -58]], // the side, round mini golf, up the far stairs
        [[0, -70, 40], [8, -66, 40], [13, -64, 40], [24, -64, 43], [33, -64, 46], [38, -64, 46], [42, -63, 46]], // security: over the bridge from the HQ
      ],
      B: [
        [[0, 31], [-8, 26], [-14, 18], [-24, 18], [-35, 17], [-34.5, 0], [-48, -1], [-48, -6], [-48, -12], [-36, -18], [-36, -36], [-40, -39], [-40, -43], [-40, -48], [-44, -58]],
        [[-2, 31], [-5, 24], [-3, 12], [0, 9], [0, 6], [0, 1], [-9, -10], [-12, -24], [-16, -24], [-24, -24], [-34, -24], [-36, -30], [-36, -36], [-40, -39], [-40, -43], [-40, -48], [-44, -58]],
        [[-4, 31], [-8, 26], [-14, 18], [-24, 18], [-35, 17], [-34.5, 0], [-48, -1], [-48, -6], [-48, -10], [-61, -11], [-61, -38], [-56, -40], [-56, -43], [-56, -48], [-52, -58]],
        [[0, -70, 40], [-8, -66, 40], [-13, -64, 40], [-24, -64, 43], [-33, -64, 46], [-38, -63, 46], [-42, -62, 46]],
      ],
    },
    sites: [{ id: 'A', min: [36, 46, -82], max: [60, 46, -48] }, { id: 'B', min: [-60, 46, -82], max: [-36, 46, -48] }],
    peekGraph() { return graph; }, dropGraph() { graph = null; }, get graph() { return graph || (graph = buildNav(B.boxes, { x0: -66, z0: -88, n: 132, cell: 1, levels: [Cy, 38, 40, 42, 46], band: 0.6,
      stairs: [{ top: [0, 40, 10.6], bot: [0, Cy, 1.4] }, { top: [0, 40, -50.6], bot: [0, Cy, -39.4] }, ...[-1, 1].flatMap((s) => [
        { top: [s * 13.4, 40, 18], bot: [s * 34.6, 38, 18] }, { top: [s * 48, 42, -9.6], bot: [s * 48, 38, -1.4] },
        { top: [s * 40, 46, -46.6], bot: [s * 40, 42, -38.4] }, { top: [s * 56, 46, -46.6], bot: [s * 56, 42, -38.4] },
        { top: [s * 34.6, 42, -24], bot: [s * 13.4, Cy, -24] }, { top: [s * 34.6, 46, -64], bot: [s * 13.4, 40, -64] }])] })); },
  };
  return map;
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

// ------------------------------------------------------------ the souk kit (Bazaar, Bazaar S&D)
// a shop: plastered, a flat roof with a parapet (stairs up), a loud awning out front on two poles, its sign over the
// door, goods on a counter by the door (o.goods: their material). front at local -z
function souk(B, D, x, z, rot, w, d, floors, o = {}) {
  const L = B.local(x, z, rot), Ld = D.local(x, z, rot), F = 3.6, hw = w / 2, hd = d / 2, top = floors * F + 0.3;
  shell(L, w, d, floors, F, o.paint || 'plaster', { floor: o.floor || 'tile', roof: o.roof || 'roof', roofAccess: o.roofAccess !== false, backDoor: o.backDoor !== false, parapet: true, winSpacing: 3.2 });
  if (o.awning !== false) { const aw = Math.max(1.5, hw - 2); Ld(-aw, 2.7, -hd - 1.8, aw, 2.85, -hd, o.awning || 'cloth'); for (const s of [-1, 1]) L.B(s * (aw - 0.2), 1.35, -hd - 1.65, 0.15, 2.7, 0.15, 'wood'); } // (cloth: nobody stands on it. in from the corners: a neighbour's round the corner never meets it)
  if (o.sign) Ld(-Math.min(2.4, hw - 0.6), 2.95, -hd - 0.05, Math.min(2.4, hw - 0.6), 3.5, -hd - 0.02, o.sign, { fit: 1 });
  if (o.goods) { L(-hw + 0.7, 0, -hd - 1.3, -1.3, 0.9, -hd - 0.45, 'wood'); L(-hw + 0.8, 0.9, -hd - 1.2, -1.4, 1.3, -hd - 0.55, o.goods); }
  if (o.balcony && floors > 1) { Ld(-2.2, F, -hd - 1.1, 2.2, F + 0.2, -hd - 0.02, 'wood'); Ld(-2.2, F + 0.2, -hd - 1.1, 2.2, F + 1.5, -hd - 1.04, 'wood'); for (const sx of [-1, 1]) Ld(sx > 0 ? 2.14 : -2.2, F + 0.2, -hd - 1.04, sx > 0 ? 2.2 : -2.14, F + 1.5, -hd - 0.02, 'wood'); } // a wooden balcony, screened
  if (o.canopy) { for (const sx of [-1, 1]) for (const sz of [-1, 1]) L.B(sx * (hw - 0.8), top + 1.1, sz * (hd - 0.8), 0.15, 2.2, 0.15, 'wood'); Ld(-hw + 0.6, top + 2.2, -hd + 0.6, hw - 0.6, top + 2.32, hd - 0.6, o.canopy); } // a canopy over the roof terrace
  return { L, Ld, top, F };
}
// an onion dome out of stacked boxes on a roof (pass B for a solid one: nobody walks into it), a gold finial if nothing
// comes up through it
function dome(D, x, y, z, r, mat = 'roofteal', finial = true) {
  let yy = y;
  for (const [k, h] of [[1, 0.22], [0.92, 0.2], [0.78, 0.18], [0.58, 0.16], [0.34, 0.14]]) { D.box(x, yy + (h * r) / 2, z, 2 * r * k, h * r, 2 * r * k, mat); yy += h * r; }
  if (finial) { D.box(x, yy + 0.4, z, 0.3, 0.8, 0.3, 'gold'); D.box(x, yy + 1.1, z, 0.6, 0.6, 0.6, 'gold'); }
}
// the Lamp Tower: square, banded, a balcony up top, and on it a giant brass oil lamp (rub it. no.)
function lampTower(B, D, x, z, h = 18, bands = [7.6, 11, 14.5]) {
  B.add(x - 2, 0, z - 2, x + 2, h, z + 2, 'tile');
  for (const y of bands) D.add(x - 2.15, y, z - 2.15, x + 2.15, y + 0.4, z + 2.15, 'gold');
  D.add(x - 3, h - 2.4, z - 3, x + 3, h - 2.1, z + 3, 'marble'); for (const sx of [-1, 1]) for (const sz of [-1, 1]) D.box(x + sx * 2.8, h - 1.6, z + sz * 2.8, 0.2, 1.0, 0.2, 'marble'); // the balcony
  D.add(x - 1.8, h, z - 1.2, x + 1.8, h + 1.4, z + 1.2, 'gold'); D.add(x - 1.1, h + 1.4, z - 0.8, x + 1.1, h + 2.0, z + 0.8, 'gold'); D.add(x - 0.4, h + 2.0, z - 0.4, x + 0.4, h + 2.5, z + 0.4, 'gold'); // the lamp, its lid, the knob
  D.add(x + 1.8, h + 0.6, z - 0.3, x + 3.6, h + 1.0, z + 0.3, 'gold'); D.add(x + 3.4, h + 1.0, z - 0.25, x + 3.9, h + 1.4, z + 0.25, 'gold'); D.add(x + 3.45, h + 1.4, z - 0.15, x + 3.85, h + 2.2, z + 0.15, 'neonred'); // the spout, the flame
  D.add(x - 2.8, h + 0.4, z - 0.15, x - 1.8, h + 0.7, z + 0.15, 'gold'); D.add(x - 2.8, h + 0.7, z - 0.15, x - 2.5, h + 1.6, z + 0.15, 'gold'); D.add(x - 2.5, h + 1.3, z - 0.15, x - 1.8, h + 1.6, z + 0.15, 'gold'); // the handle
}
// a dye vat: a stone rim you can stand on, knee-deep colour inside (render-only: jump in, wade about)
function dyeVat(B, D, x, z, s, mat) { propOf('dyevat', [x, 0, z], 0, () => dyeVatBoxes(B, D, x, z, s, mat), { t: mat }); }
function dyeVatBoxes(B, D, x, z, s, mat) {
  const h = s / 2, t = 0.4;
  B.add(x - h, 0, z - h, x + h, 0.9, z - h + t, 'stone'); B.add(x - h, 0, z + h - t, x + h, 0.9, z + h, 'stone');
  B.add(x - h, 0, z - h + t, x - h + t, 0.9, z + h - t, 'stone'); B.add(x + h - t, 0, z - h + t, x + h, 0.9, z + h - t, 'stone');
  D.add(x - h + t, 0.02, z - h + t, x + h - t, 0.7, z + h - t, 'dye' + mat); // (dyemagenta etc: a real liquid, public/js/liquids.js)
}
// a frame (two posts and a bar) with a hanging carpet or cloth: hides you, doesn't stop a bullet (render-only cloth)
function hanging(B, D, x0, x1, z, mat, alongX = true, h = 3) {
  const P = (a, b) => (alongX ? [a, b] : [b, a]);
  for (const a of [x0, x1]) { const [px, pz] = P(a, z); B.box(px, h / 2, pz, 0.2, h, 0.2, 'wood'); }
  { const [ax, az] = P(x0 + 0.1, z - 0.06), [bx, bz] = P(x1 - 0.1, z + 0.06); D.add(ax, h - 0.18, az, bx, h - 0.06, bz, 'wood'); }
  { const [ax, az] = P(x0 + 0.2, z - 0.03), [bx, bz] = P(x1 - 0.2, z + 0.03); D.add(ax, 0.5, az, bx, h - 0.25, bz, mat); }
}

// doors, shuttered windows, lanterns and a plaster cornice on the street faces of solid house blocks (render-only, flat
// on the wall, nothing sticks out past head height but the awnings). blocks: [x0, z0, x1, z1] with .box (the block's own
// box). a slot is left bare where anything is already there (a wall butting on, a crate, a sign, the next block), so the
// dressing never cuts into or z-fights with the map. inside(x, z): the playable town (faces looking out stay bare)
function dressFacades(B, D, blocks, rv, inside) {
  const over = (a, b) => a.min[0] < b.max[0] - 0.002 && a.max[0] > b.min[0] + 0.002 && a.min[1] < b.max[1] - 0.002 && a.max[1] > b.min[1] + 0.002 && a.min[2] < b.max[2] - 0.002 && a.max[2] > b.min[2] + 0.002;
  const pick = (a) => a[(rv() * a.length) | 0];
  const doorM = ['wood', 'blue', 'mint', 'wood', 'sideorange', 'blue'], shutM = ['blue', 'mint', 'wood', 'sidelilac', 'blue'], awnM = ['cloth', 'toyteal', 'magenta', 'toyyellow'];
  for (const bk of blocks) {
    const [x0, z0, x1, z1] = bk, host = bk.box, pad = { min: [x0 - 2.5, -1, z0 - 2.5], max: [x1 + 2.5, 9, z1 + 2.5] };
    const near = () => [...B.boxes.filter((q) => q !== host && over(q, pad)), ...D.boxes.filter((q) => over(q, pad))];
    for (const [axis, fixed, a, b, n] of [['x', z0, x0, x1, -1], ['x', z1, x0, x1, 1], ['z', x0, z0, z1, -1], ['z', x1, z0, z1, 1]]) {
      const SW = 3.6, k = Math.floor((b - a - 1.2) / SW);
      if (k < 1) continue;
      // face-local: u along the face, y up, v out from it
      const Wb = (u0, y0, v0, u1, y1, v1, mat) => { const f0 = fixed + n * v0, f1 = fixed + n * v1, lo = Math.min(f0, f1), hi = Math.max(f0, f1);
        return axis === 'x' ? { min: [Math.min(u0, u1), y0, lo], max: [Math.max(u0, u1), y1, hi], mat } : { min: [lo, y0, Math.min(u0, u1)], max: [hi, y1, Math.max(u0, u1)], mat }; };
      const put = (list) => { const ws = list.map((q) => Wb(...q)), nb = near(); if (ws.some((w) => nb.some((q) => over(w, q)))) return false; for (const w of ws) D.add(w.min[0], w.min[1], w.min[2], w.max[0], w.max[1], w.max[2], w.mat); return true; };
      const u0 = (a + b) / 2 - (k * SW) / 2, done = [];
      for (let i = 0; i < k; i++) {
        const c = u0 + (i + 0.5) * SW, [px, pz] = axis === 'x' ? [c, fixed + n * 1.2] : [fixed + n * 1.2, c];
        if (!inside(px, pz)) { done.push(false); continue; }
        const it = [], g = rv();
        if (g < 0.32) { // a door in a plaster frame, maybe an awning over it
          it.push([c - 0.6, 0, 0, c + 0.6, 2.3, 0.06, pick(doorM)], [c - 0.8, 0, 0, c - 0.6, 2.3, 0.1, 'plaster'], [c + 0.6, 0, 0, c + 0.8, 2.3, 0.1, 'plaster'], [c - 0.8, 2.3, 0, c + 0.8, 2.55, 0.12, 'plaster']);
          if (rv() < 0.4) { it.push([c - 1.0, 2.75, 0, c + 1.0, 2.83, 1.0, pick(awnM)]); it.awn = true; }
        } else if (g < 0.6) { // a small barred window
          it.push([c - 0.45, 1.2, 0, c + 0.45, 2.0, 0.04, 'glass'], [c - 0.6, 1.1, 0, c + 0.6, 1.2, 0.15, 'plaster']);
          for (const du of [-0.17, 0.17]) it.push([c + du - 0.03, 1.2, 0.04, c + du + 0.03, 2.0, 0.07, 'wood']);
        }
        const g2 = rv();
        if (g2 < 0.7) { // upstairs: shutters open, a carved screen, or a balcony
          it.push([c - 0.5, 3.6, 0, c + 0.5, 4.9, 0.04, 'glass'], [c - 0.65, 3.5, 0, c + 0.65, 3.6, 0.16, 'plaster'], [c - 0.65, 4.9, 0, c + 0.65, 5.05, 0.1, 'plaster']);
          const sh = rv();
          if (sh < 0.55) { const m = pick(shutM); it.push([c - 1.0, 3.6, 0, c - 0.5, 4.9, 0.07, m], [c + 0.5, 3.6, 0, c + 1.0, 4.9, 0.07, m]); }
          else if (sh < 0.8) it.push([c - 0.5, 3.6, 0.04, c + 0.5, 4.9, 0.1, 'wood']);
          else it.push([c - 1.1, 3.3, 0, c + 1.1, 3.45, 0.9, 'wood'], [c - 1.1, 3.45, 0.84, c + 1.1, 4.15, 0.9, 'wood'], [c - 1.1, 3.45, 0, c - 1.04, 4.15, 0.84, 'wood'], [c + 1.04, 3.45, 0, c + 1.1, 4.15, 0.84, 'wood']);
          if (sh < 0.8 && !it.awn && rv() < 0.15) it.push([c - 0.45, 2.55, 0.16, c + 0.45, 3.62, 0.19, pick(['carpet', 'magenta', 'cloth'])]); // a rug airing over the sill
        }
        if (rv() < 0.4) it.push([c - 0.35, 6.1, 0, c + 0.35, 6.8, 0.04, 'glass'], [c - 0.45, 6.0, 0, c + 0.45, 6.1, 0.12, 'plaster']); // the top floor
        done.push(it.length ? put(it) : true);
      }
      // lanterns between the slots, a cornice along each run of dressed slots
      for (let i = 0; i < k - 1; i++) if (done[i] && done[i + 1] && rv() < 0.35) { const u = u0 + (i + 1) * SW; put([[u - 0.03, 3.05, 0, u + 0.03, 3.11, 0.4, 'wood'], [u - 0.14, 2.65, 0.22, u + 0.14, 3.05, 0.5, 'lamp']]); }
      for (let i = 0; i < k;) {
        if (!done[i]) { i++; continue; }
        let j = i; while (j + 1 < k && done[j + 1]) j++;
        const ua = u0 + i * SW + 0.1, ub = u0 + (j + 1) * SW - 0.1;
        if (!put([[ua, 7.45, 0, ub, 7.65, 0.14, 'plaster']])) for (let q = i; q <= j; q++) put([[u0 + q * SW + 0.1, 7.45, 0, u0 + (q + 1) * SW - 0.1, 7.65, 0.14, 'plaster']]);
        i = j + 1;
      }
    }
  }
}

// ------------------------------------------------------------ BAZAAR: Jank Bazaar, a walled market town (every mode but
// Plant & Defuse). in the middle the Grand Bazaar, one covered hall (48 m square, stalls in islands, pillars, the fountain,
// the Lamp Tower up through its dome); its four gates sit off-centre, each a quarter-turn round from the last, so no gate
// looks straight out of another. round it a ring street, then the town: the caravanserai (north: a courtyard inn with a
// two-level arcade), the dye works and the canal (south: vats of colour, drying racks, four bridges, ankle-deep water you
// can wade), the spice market (NW), the carpet yard (NE: carpets on frames, a plank bridge over it roof to roof), the tea
// house (SW, a roof terrace), the potters (SE, kilns and stacks of pots). the teams start in the west and east gate
// plazas: between them is the hall, its tower and its staggered gates, so nobody sees the other spawn
function bazaar() {
  const B = builder(), D = builder();
  const r = rng(777), rv = rng(7171), W = B.local(0, 0, 0), Dw = D.local(0, 0, 0), add = B.add;
  const X = 66, bounds = [-X, -X, X, X];
  const spawns = [];
  // ---- the ground (the canal cut out of it), the city wall (its top's over the ceiling), corner towers, shut gates
  groundHoles(B, -300, -300, 300, 300, -2, 0, 'sand', [[-58.4, 43.6, 58.4, 48.4]]);
  for (const s of [-1, 1]) { add(-X - 1.2, 0, s > 0 ? X : -X - 1.2, X + 1.2, 11, s > 0 ? X + 1.2 : -X, 'adobe'); add(s > 0 ? X : -X - 1.2, 0, -X, s > 0 ? X + 1.2 : -X, 11, X, 'adobe'); }
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) B.box(sx * (X + 0.6), 7, sz * (X + 0.6), 5, 14, 5, 'adobe');
  for (const s of [-1, 1]) { // the gatehouses (west and east: the teams came in by them; north and south: shut for the night)
    const i0 = s * X - s * 0.6, i1 = s * X + s * 2.4, d0 = s * X - s * 0.04, b0 = s * X - s * 0.08, b1 = s * X - s * 0.02;
    add(i0, 0, -7, i1, 13, -4, 'adobe'); add(i0, 0, 4, i1, 13, 7, 'adobe'); D.add(d0, 0, -4, s * X, 6.5, 4, 'wood'); D.add(b0, 1.4, -3.8, b1, 1.7, 3.8, 'metal');
    add(-7, 0, i0, -4, 13, i1, 'adobe'); add(4, 0, i0, 7, 13, i1, 'adobe'); D.add(-4, 0, d0, 4, 6.5, s * X, 'wood'); D.add(-3.8, 1.4, b0, 3.8, 1.7, b1, 'metal');
  }

  // ---- THE GRAND BAZAAR: the covered hall in the middle
  const HW = 24;
  add(-HW + 0.3, 0, -HW + 0.3, HW - 0.3, 0.05, HW - 0.3, 'pottery');
  wall(W, 'z', -HW, -HW - 0.3, HW + 0.3, 0, 7, 0.6, 'adobe', [{ a: -10, b: -6, y0: 0, y1: 4 }]); // west gate (north of the middle)
  wall(W, 'z', HW, -HW - 0.3, HW + 0.3, 0, 7, 0.6, 'adobe', [{ a: 6, b: 10, y0: 0, y1: 4 }]); // east gate (south of it)
  wall(W, 'x', -HW, -HW + 0.3, HW - 0.3, 0, 7, 0.6, 'adobe', [{ a: 6, b: 10, y0: 0, y1: 4 }]); // north gate (east of it)
  wall(W, 'x', HW, -HW + 0.3, HW - 0.3, 0, 7, 0.6, 'adobe', [{ a: -10, b: -6, y0: 0, y1: 4 }]); // south gate (west of it)
  slab(W, -HW - 0.3, -HW - 0.3, HW + 0.3, HW + 0.3, 7, 7.3, 'roof', [-2, -2, 2, 2]);
  for (const [x0, z0, x1, z1] of [[-HW - 0.3, -HW - 0.3, HW + 0.3, -HW + 0.3], [-HW - 0.3, HW - 0.3, HW + 0.3, HW + 0.3], [-HW - 0.3, -HW + 0.3, -HW + 0.3, 18.6], [-HW - 0.3, 20.2, -HW + 0.3, HW - 0.3], [HW - 0.3, -HW + 0.3, HW + 0.3, HW - 0.3]]) add(x0, 7.3, z0, x1, 8.1, z1, 'plaster'); // the roof's parapet (a gap where the stairs come up)
  dome(B, 0, 7.3, 0, 9, 'roofteal', false); for (const [x, z] of [[-14, -14], [14, -14], [-14, 14], [14, 14]]) dome(B, x, 7.3, z, 3.2, 'roofblue'); // (solid: over the ceiling past the first tier)
  lampTower(B, D, 0, 0, 18, [16.2]);
  for (const [x0, z0, x1, z1] of [[-4.5, -4.5, 4.5, -4], [-4.5, 4, 4.5, 4.5], [-4.5, -4, -4, 4], [4, -4, 4.5, 4]]) add(x0, 0.05, z0, x1, 0.65, z1, 'marble'); // the fountain round the tower's foot
  for (const [x0, z0, x1, z1] of [[-4, -4, 4, -2], [-4, 2, 4, 4], [-4, -2, -2, 2], [2, -2, 4, 2]]) D.add(x0, 0.07, z0, x1, 0.45, z1, 'water');
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) for (const [px, pz] of [[8, 8], [16, 16], [8, 16], [16, 8]]) { B.box(sx * px, 3.3, sz * pz, 0.7, 6.6, 0.7, 'plaster'); B.box(sx * px, 6.8, sz * pz, 1.1, 0.4, 1.1, 'gold'); } // pillars under the roof, gold capitals
  // stall islands in the four quarters of the hall (counters round a rack of goods, an awning over it all), stalls along the walls
  const goods = ['pottery', 'carpet', 'cloth', 'toyyellow'], awn = ['cloth', 'pink', 'toyteal', 'toyyellow'];
  [[-12, -12], [12, -12], [-12, 12], [12, 12], [-13, 0], [13, 0], [0, -13], [0, 13]].forEach(([cx, cz], j) => {
    const i = j % 4;
    for (const s of [-1, 1]) { add(cx - 3, 0.05, cz + s * 1.2 - 0.45, cx + 3, 1.05, cz + s * 1.2 + 0.45, 'wood'); add(cx - 2.9, 1.05, cz + s * 1.2 - 0.35, cx + 2.9, 1.35, cz + s * 1.2 + 0.35, goods[i]); }
    add(cx - 2.2, 0.05, cz - 0.4, cx + 2.2, 2.2, cz + 0.4, goods[(i + 2) % 4]); // the rack between the counters
    for (const px of [-3.2, 3.2]) for (const pz of [-1.9, 1.9]) B.box(cx + px, 1.45, cz + pz, 0.15, 2.8, 0.15, 'wood');
    add(cx - 3.5, 2.85, cz - 2.2, cx + 3.5, 3.0, cz + 2.2, awn[i]);
  });
  for (const [x0, z0, x1, z1, g] of [[-23.6, -20, -22.4, -14, 'pottery'], [-23.6, 14, -22.4, 20, 'cloth'], [22.4, -20, 23.6, -14, 'carpet'], [22.4, 14, 23.6, 20, 'toyyellow'], [-20, -23.6, -14, -22.4, 'carpet'], [14, 22.4, 20, 23.6, 'pottery'], [-20, 22.4, -14, 23.6, 'cloth'], [14, -23.6, 20, -22.4, 'toyyellow']]) {
    add(x0, 0.05, z0, x1, 1.0, z1, 'wood'); add(x0 + 0.1, 1.0, z0 + 0.1, x1 - 0.1, 1.35, z1 - 0.1, g);
  }
  for (const [x, z] of [[-8, 0], [8, 0], [0, -8], [0, 8], [-16, 0], [16, 0], [0, -16], [0, 16]]) D.box(x, 5.4, z, 0.6, 0.6, 0.6, 'lamp'); // lamps hung under the roof
  const flagM = ['magenta', 'yellow', 'blue', 'mint', 'toyred'];
  for (const c of [-6, 6]) { D.add(-23.6, 6.2, c - 0.02, 23.6, 6.24, c + 0.02, 'wood'); D.add(c - 0.02, 6.29, -23.6, c + 0.02, 6.33, 23.6, 'wood'); // strings of little flags across the hall (one set a little higher: no crossing in one plane)
    for (let k = 0; k < 30; k++) { const a = -22 + k * 1.5; if (Math.abs(a - c) < 0.6) continue; D.add(a - 0.25, 5.65, c - 0.02, a + 0.25, 6.2, c + 0.02, flagM[k % 5]); D.add(c - 0.02, 5.74, a - 0.25, c + 0.02, 6.29, a + 0.25, flagM[(k + 2) % 5]); } }
  for (const [x0, z0, x1, z1] of [[-23.67, 10, -23.64, 14], [23.64, -14, 23.67, -10], [-14, -23.67, -10, -23.64], [10, 23.64, 14, 23.67]]) D.add(x0, 2.0, z0, x1, 6.0, z1, 'carpet'); // carpets hung on the walls
  for (const [x, z] of [[-19, -19], [19, -19], [-19, 19], [19, 19]]) D.add(x - 2, 0.05, z - 1.6, x + 2, 0.07, z + 1.6, 'carpet'); // rugs
  D.add(-HW - 0.33, 4.6, -10, -HW - 0.31, 5.8, -6, 'neonbar', { fit: 1 }); D.add(HW + 0.31, 4.6, 6, HW + 0.33, 5.8, 10, 'neonnoodle', { fit: 1 });
  for (const s of [-1, 1]) { D.add(s > 0 ? HW + 0.3 : -HW - 0.32, 6.0, -HW - 0.32, s > 0 ? HW + 0.32 : -HW - 0.3, 6.5, HW + 0.32, 'tile'); D.add(-HW - 0.3, 6.0, s > 0 ? HW + 0.3 : -HW - 0.32, HW + 0.3, 6.5, s > 0 ? HW + 0.32 : -HW - 0.3, 'tile'); } // a mosaic band all round
  for (const [ax, fx, a0, a1, out] of [['z', -HW, -10, -6, -1], ['z', HW, 6, 10, 1], ['x', -HW, 6, 10, -1], ['x', HW, -10, -6, 1]]) { // each gate: a tiled frame, an awning on two poles
    const o0 = fx + out * 0.3, o1 = fx + out * 0.33, aw0 = fx + out * 0.3, aw1 = fx + out * 2.1, P = (a, b, y0, y1, u0, u1, m, L = D) => (ax === 'z' ? L.add(Math.min(u0, u1), y0, a, Math.max(u0, u1), y1, b, m) : L.add(a, y0, Math.min(u0, u1), b, y1, Math.max(u0, u1), m));
    P(a0 - 0.4, a0, 0, 4.4, o0, o1, 'tile'); P(a1, a1 + 0.4, 0, 4.4, o0, o1, 'tile'); P(a0, a1, 4.0, 4.4, o0, o1, 'tile');
    P(a0 - 0.6, a1 + 0.6, 4.4, 4.55, aw0, aw1, 'cloth', B); for (const a of [a0 - 0.4, a1 + 0.4]) P(a - 0.075, a + 0.075, 0, 4.4, fx + out * 1.85, fx + out * 2.0, 'wood', B); }
  // the roof's stairs: a flight up the outside of the west wall (the roof's a fight of its own)
  stairs(W, -HW - 1.9, -HW - 0.3, 12, 1, 0, 7.3, 'adobe', 0.45);

  // ---- NORTH: the caravanserai (a courtyard inn: an arcade all round, a gallery over it, the yard in the middle)
  { const x0 = -20, x1 = 20, z0 = -58, z1 = -32, t = 0.6, ix0 = -14.7, ix1 = 14.7, iz0 = -52.7, iz1 = -37.3;
    wall(W, 'x', z1, x0 - t / 2, x1 + t / 2, 0, 7.2, t, 'adobe', [{ a: -3, b: 3, y0: 0, y1: 4.2 }]);
    wall(W, 'x', z0, x0 - t / 2, x1 + t / 2, 0, 7.2, t, 'adobe', [{ a: 8, b: 10, y0: 0, y1: 2.6 }]);
    wall(W, 'z', x0, z0 + t / 2, z1 - t / 2, 0, 7.2, t, 'adobe', [{ a: -48, b: -46, y0: 0, y1: 2.6 }]);
    wall(W, 'z', x1, z0 + t / 2, z1 - t / 2, 0, 7.2, t, 'adobe', [{ a: -44, b: -42, y0: 0, y1: 2.6 }]);
    slab(W, x0 + t / 2, z0 + t / 2, x1 - t / 2, z1 - t / 2, 3.6, 3.9, 'wood', [ix0, iz0, ix1, iz1]); // the gallery
    slab(W, x0 - t / 2, z0 - t / 2, x1 + t / 2, z1 + t / 2, 7.2, 7.5, 'roof', [ix0, iz0, ix1, iz1]); // the roof over it
    for (const [a0, a1, fx, ax] of [[x0 - t / 2, x1 + t / 2, z0 - t / 2 + 0.3, 'x'], [x0 - t / 2, x1 + t / 2, z1 + t / 2 - 0.3, 'x'], [z0 + t / 2, z1 - t / 2, x0 - t / 2 + 0.3, 'z'], [z0 + t / 2, z1 - t / 2, x1 + t / 2 - 0.3, 'z']]) wall(W, ax, fx, a0, a1, 7.5, 8.3, 0.6, 'adobe'); // the roof's parapet
    const pil = (a0, a1, fixed, ax) => { const n = Math.round((a1 - a0) / 3.7); for (let i = 0; i <= n; i++) { const a = a0 + ((a1 - a0) * i) / n; for (const [y, h] of [[0, 3.6], [3.9, 3.3]]) ax === 'x' ? B.box(a, y + h / 2, fixed, 0.5, h, 0.5, 'plaster') : B.box(fixed, y + h / 2, a, 0.5, h, 0.5, 'plaster'); } };
    pil(ix0, ix1, iz0, 'x'); pil(ix0, ix1, iz1, 'x'); pil(iz0 + 3.85, iz1 - 3.85, ix0, 'z'); pil(iz0 + 3.85, iz1 - 3.85, ix1, 'z'); // the arcade, both floors
    for (const [a0, a1, fx, ax] of [[ix0 + 0.3, -1.2, iz1, 'x'], [1.2, ix1 - 0.3, iz1, 'x'], [ix0 + 0.3, ix1 - 0.3, iz0, 'x'], [iz0 + 0.3, -47.2, ix0, 'z'], [-45.3, iz1 - 0.3, ix0, 'z'], [iz0 + 0.3, -44.7, ix1, 'z'], [-42.8, iz1 - 0.3, ix1, 'z']]) wall(W, ax, fx, a0, a1, 4.0, 4.8, 0.12, 'wood'); // the gallery's rail (gaps to drop)
    for (let k = 0; k < 9; k++) { add(ix0 + (8 - k) * 0.5, 0, -47, ix0 + (9 - k) * 0.5, (k + 1) * 0.433, -45.5, 'wood'); add(ix1 - (9 - k) * 0.5, 0, -44.5, ix1 - (8 - k) * 0.5, (k + 1) * 0.433, -43, 'wood'); } // two flights up to it from the yard
    add(-1.5, 0, -46.5, 1.5, 0.9, -43.5, 'stone'); D.add(-1.1, 0.9, -46.1, 1.1, 0.92, -43.9, 'water'); for (const [x, z] of [[-1.4, -46.4], [1.4, -46.4], [-1.4, -43.6], [1.4, -43.6]]) B.box(x, 1.9, z, 0.18, 2.0, 0.18, 'wood'); add(-1.9, 2.9, -46.9, 1.9, 3.1, -43.1, 'roofg'); // the well
    camel(W, -8, -40.5, true); camel(W, 8, -49.5, true); hay(B, 9, -40, 3); cart(W, -7, -50, true); cratePile(B, 11, -48.5, 3, r);
    D.add(-4, 4.6, z1 + t / 2 + 0.02, 4, 6.4, z1 + t / 2 + 0.05, 'adcaravan', { fit: 1 }); spawns.push([0, 0.2, -40], [-17, 0.2, -36], [17, 4.1, -55]); }

  // ---- SOUTH: the dye works, the canal (ankle deep, four bridges), the drying racks
  { add(-58, -2, 43.6, 58, -0.5, 48.4, 'stone'); D.add(-58, -0.5, 44, 58, -0.3, 48, 'water'); // the canal's bed, its water
    for (const z0 of [43.6, 48]) add(-58, -0.5, z0, 58, 0.1, z0 + 0.4, 'stone'); // its kerbs
    for (const sx of [-1, 1]) add(sx * 58, -2, 43.6, sx * 58.4, 0.1, 48.4, 'stone'); // its ends
    for (const x of [-45, -12, 12, 45]) { add(x - 2.2, 0.1, 43.2, x + 2.2, 0.4, 48.8, 'stone'); for (const s of [-1, 1]) add(x + s * 2.2 - (s > 0 ? 0.3 : 0), 0.4, 43.2, x + s * 2.2 + (s > 0 ? 0 : 0.3), 1.0, 48.8, 'stone'); } // the bridges (low walls)
    souk(B, D, 0, 33, 2, 16, 6, 1, { paint: 'sidelilac', sign: 'addye', awning: 'magenta', goods: 'cloth' }); // the dye works (its front on the vats)
    ['magenta', 'yellow', 'blue', 'mint', 'toyred', 'toyteal'].forEach((m, i) => dyeVat(B, D, -17.5 + i * 7, 40.4, 4, m));
    for (const [z, mats] of [[53, ['magenta', 'blue', 'yellow']], [57.5, ['mint', 'toyred', 'toyteal']]]) mats.forEach((m, i) => hanging(B, D, -21 + i * 14, -9 + i * 14, z, m));
    spawns.push([0, 0.2, 42], [-25, 0.2, 52], [25, 0.2, 52]); }

  // ---- NW: the spice market (a square with a shop on each side, open at the corners), sacks, cones of spice, lanterns
  { const cx = -45, cz = -45;
    souk(B, D, cx, cz - 11, 2, 10, 8, 1, { paint: 'sideorange', sign: 'adspice', goods: 'toyred', awning: 'toyyellow' });
    souk(B, D, cx, cz + 11, 0, 10, 8, 2, { paint: 'plaster', goods: 'toyyellow', awning: 'pink', balcony: true });
    souk(B, D, cx - 11, cz, 1, 10, 8, 1, { paint: 'sidelemon', goods: 'sideorange', awning: 'cloth' });
    souk(B, D, cx + 11, cz, 3, 10, 8, 2, { paint: 'sidepink', goods: 'pottery', awning: 'toyteal', balcony: true });
    for (const [x, z] of [[-49, -48], [-41, -48], [-45, -41]]) { add(x - 1.6, 0, z - 0.8, x + 1.6, 0.9, z + 0.8, 'wood'); [['toyred', -1], ['toyyellow', 0], ['sideorange', 1]].forEach(([m, k]) => { D.box(x + k, 1.05, z, 0.8, 0.3, 0.8, m); D.box(x + k, 1.3, z, 0.5, 0.2, 0.5, m); }); } // spice tables
    for (const [x, z] of [[-50.5, -42], [-39.6, -50.2], [-50, -50]]) B.box(x, 0.45, z, 0.9, 0.9, 0.7, 'cloth');
    for (const z of [-48, -42]) D.add(-51.5, 3.4, z - 0.02, -38.5, 3.43, z + 0.02, 'wood'); for (const x of [-48, -45, -42]) for (const z of [-48, -42]) D.box(x, 3.0, z, 0.4, 0.5, 0.4, 'lamp'); // lanterns on strings
    spawns.push([-45, 0.2, -45], [-58, 0.2, -32], [-32, 0.2, -58]); }

  // ---- NE: the carpet yard (carpets drying on frames, rolls stacked, a plank bridge over it from roof to roof)
  { const cx = 45, cz = -45;
    souk(B, D, cx, cz - 11, 2, 10, 8, 2, { paint: 'sidepink', sign: 'adcarpet', goods: 'carpet', awning: 'magenta', balcony: true });
    souk(B, D, cx, cz + 11, 0, 10, 8, 2, { paint: 'sidemint', goods: 'carpet', awning: 'cloth', balcony: true });
    souk(B, D, cx + 11, cz, 3, 10, 8, 1, { paint: 'plaster', goods: 'cloth', awning: 'toyteal' });
    for (const [z, m] of [[-48.5, 'carpet'], [-45, 'magenta'], [-41.5, 'carpet']]) hanging(B, D, 39, 48, z, m);
    for (let i = 0; i < 3; i++) add(35.4, i * 0.6, -52 + i * 0.2, 37.8, (i + 1) * 0.6, -48 - i * 0.2, 'carpet'); // rolls, stacked
    add(44, 8.3, -52.3, 46, 8.5, -37.7, 'wood'); for (const x of [44, 45.9]) add(x, 8.5, -52.3, x + 0.1, 9.3, -37.7, 'wood'); // a plank bridge over the yard, parapet to parapet
    spawns.push([45, 0.2, -45], [58, 0.2, -32], [32, 0.2, -58]); }

  // ---- SW: the tea house (cushions on its roof terrace), houses, a garden, the canal behind
  { souk(B, D, -45, 36, 0, 16, 10, 2, { paint: 'sidemint', sign: 'adtea', goods: 'pottery', awning: 'pink', balcony: true, canopy: 'pink' }); // (its front north, onto the street)
    for (const [x, z] of [[-50, 33], [-45, 37], [-40, 33]]) { add(x - 1, 7.5, z - 0.6, x + 1, 7.8, z + 0.6, 'carpet'); add(x - 0.4, 7.8, z - 0.4, x + 0.4, 8.0, z + 0.4, 'wood'); } // cushions, low tables (up top)
    souk(B, D, -54, 55, 0, 10, 8, 1, { paint: 'plaster', awning: false }); souk(B, D, -36, 55, 0, 12, 8, 1, { paint: 'sidelemon', awning: 'cloth' });
    for (const [x, z] of [[-60, 51], [-28, 51]]) palm(W, x, z, 6 + rv() * 2, rv); add(-48, 0, 49.6, -42, 0.5, 51.6, 'hedge');
    spawns.push([-45, 0.5, 46], [-58, 0.2, 32], [-30, 0.2, 36]); }

  // ---- SE: the potters (two kilns, stacks of pots, the pottery shop), houses
  { souk(B, D, 52, 36, 3, 12, 10, 1, { paint: 'sideorange', sign: 'adpottery', goods: 'pottery', awning: 'toyyellow' });
    for (const [x, z] of [[36, 35], [42, 39]]) { add(x - 2, 0, z - 2, x + 2, 2.4, z + 2, 'brick'); add(x - 1.4, 2.4, z - 1.4, x + 1.4, 3.4, z + 1.4, 'brick'); add(x - 0.4, 3.4, z - 0.4, x + 0.4, 4.6, z + 0.4, 'brick'); D.add(x - 0.6, 0.2, z - 2.04, x + 0.6, 1.2, z - 2.0, 'neonred'); } // kilns (red hot)
    for (const [x, z, n] of [[33, 40.4, 3], [44.6, 32.4, 2], [39, 33, 2]]) for (let i = 0; i < n; i++) B.box(x, 0.35 + i * 0.7, z, 1.4 - i * 0.3, 0.7, 1.4 - i * 0.3, 'pottery'); // pots, stacked
    souk(B, D, 36, 55, 0, 12, 8, 2, { paint: 'plaster', awning: 'cloth', balcony: true }); souk(B, D, 54, 55, 0, 10, 8, 1, { paint: 'sidepink', awning: false });
    spawns.push([45, 0.5, 46], [58, 0.2, 32], [30, 0.2, 36]); }

  // ---- WEST and EAST: the gate plazas (the teams' spawns), a fountain each, the houses round them
  const att = [[-58, 0.2, -6], [-58, 0.2, -2], [-58, 0.2, 2], [-58, 0.2, 6], [-54, 0.2, -4], [-54, 0.2, 0], [-54, 0.2, 4]];
  const def = att.map(([x, y, z]) => [-x, y, -z]);
  for (const s of [-1, 1]) {
    souk(B, D, s * 52, -22, 2, 12, 12, 2, { paint: s > 0 ? 'sidelemon' : 'sidepink', goods: 'cloth', awning: 'toyteal', balcony: true }); // (the row north of the plaza faces south onto it,
    souk(B, D, s * 37, -22, 2, 10, 12, 1, { paint: 'plaster', goods: 'pottery', awning: 'pink' });
    souk(B, D, s * 52, 22, 0, 12, 12, 1, { paint: 'plaster', goods: 'carpet', awning: 'cloth' }); // the row south of it north)
    souk(B, D, s * 37, 22, 0, 10, 12, 2, { paint: s > 0 ? 'sidemint' : 'sideorange', goods: 'toyyellow', awning: 'magenta', balcony: true });
    const fx = s * 42; for (let i = 0; i < 8; i++) { const a = (i / 8) * Math.PI * 2; B.box(fx + Math.cos(a) * 2.6, 0.4, Math.sin(a) * 2.6, 2.2, 0.8, 2.2, 'marble'); } D.add(fx - 1.8, 0.05, -1.8, fx + 1.8, 0.6, 1.8, 'water'); B.box(fx, 1.4, 0, 0.7, 2.8, 0.7, 'marble'); // a fountain
    cart(W, s * 34, s * 8, false); for (const [x, z] of [[s * 46, s * -9], [s * 47, s * -10]]) B.box(x, 0.6, z, 0.75, 1.2, 0.75, 'barrel');
  }
  for (const [x, z, rot] of [[-22, -29.8, 2], [-12, -29.8, 2], [14, -29.8, 2], [22, -29.8, 2], [-20, 28.2, 0], [-14, 28.2, 0], [14, 28.2, 0], [20, 28.2, 0], [-28.2, -20, 1], [-28.2, 2, 1], [28.2, -2, 3], [28.2, 20, 3],
    [-47, -11, 2], [-47, 11, 0], [47, -11, 2], [47, 11, 0]]) stall(W, x, z, rot, rv); // market stalls round the hall and in the plazas
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) { B.box(sx * 30, 0.35, sz * 30, 1.8, 0.7, 1.8, 'stone'); palm(W, sx * 30, sz * 30, 6.5 + rv() * 1.5, rv); } // palms in planters, the ring street's corners
  spawns.push(att[0], att[3], def[0], def[3], [-27, 0.2, 0], [27, 0.2, 0], [0, 0.2, -27], [0, 0.2, 27], [-20, 0.2, -20], [20, 0.2, 20], [-6, 0.2, 18], [6, 0.2, -18], [-63, 0.2, -40], [63, 0.2, 40], [-40, 0.2, 63], [40, 0.2, -63]);

  // ---- the ground between it all (look only): sand patches, scrub, the odd tumbleweed, never inside anything
  { const rg = rng(7373), clear = (x, z, rr) => !B.boxes.some((q) => q.max[1] > 0.06 && q.min[1] < 12 && q.mat !== 'sand' && x + rr > q.min[0] && x - rr < q.max[0] && z + rr > q.min[2] && z - rr < q.max[2]);
    const ok = (x, z) => Math.max(Math.abs(x), Math.abs(z)) > 25 && !(z > 42 && z < 50);
    for (let i = 0; i < 70; i++) { const x = -X + 3 + rg() * (2 * X - 6), z = -X + 3 + rg() * (2 * X - 6), s = 0.4 + rg() * 0.5; if (ok(x, z) && clear(x, z, s)) D.box(x, s * 0.35, z, s, s * 0.7, s * 0.9, rg() < 0.5 ? 'hedge' : 'leaves2'); }
    for (let i = 0; i < 8; i++) { const x = -X + 3 + rg() * (2 * X - 6), z = -X + 3 + rg() * (2 * X - 6); if (ok(x, z) && clear(x, z, 0.6)) D.obb(x, 0.4, z, 0.8, 0.8, 0.8, rg() * 3, 'burnt'); }
  }
  // ---- outside the wall (render-only): dunes, rocks, a camp outside the west gate, an oasis, the next town over
  horizon(D, -300, -300, 300, 300, 1500, 'sand');
  for (let i = 0; i < 40; i++) { const a = rv() * Math.PI * 2, d = 120 + rv() * 220, x = Math.cos(a) * d, z = Math.sin(a) * d, w = 30 + rv() * 60, dd = 18 + rv() * 36; if (Math.abs(x) - w / 2 < 80 && Math.abs(z) - dd / 2 < 80) continue; dune(D, x, z, w, dd, 5 + rv() * 12); }
  B.boxes.arch.push({ id: 'rocks_bazaar', p: [0, 0, 0], r: 0 }); const RK = { av: 'rocks_bazaar', ai: B.boxes.arch.length - 1 }; // (its rock: one Blender model, look only)
  for (let i = 0; i < 12; i++) { const a = rv() * Math.PI * 2, d = 200 + rv() * 220; rocks(D, Math.cos(a) * d, Math.sin(a) * d, 12 + rv() * 20, rv, RK); }
  for (const [x, z, c] of [[-86, -14, 'cloth'], [-92, 6, 'toypink'], [-84, 20, 'toyteal']]) tent(Dw, x, z, c);
  for (const [x, z, ax] of [[-98, -4, true], [-90, 30, false], [92, -20, true]]) camel(Dw, x, z, ax);
  D.add(130, 0, -40, 170, 0.2, -10, 'lawn'); D.add(136, 0.2, -34, 164, 0.3, -16, 'water');
  for (const [x, z] of [[132, -42], [168, -38], [128, -20], [172, -14], [150, -8], [146, -44]]) palm(Dw, x, z, 6 + rv() * 3, rv);
  for (let i = 0; i < 26; i++) { const x = -330 + (rv() - 0.5) * 120, z = -180 + (rv() - 0.5) * 140, w = 8 + rv() * 10, h = 4 + rv() * 9;
    D.add(x - w / 2, 0, z - w / 2, x + w / 2, h, z + w / 2, rv() < 0.7 ? 'adobe' : ['sidepink', 'sidelemon', 'sidemint'][(rv() * 3) | 0]); if (rv() < 0.3) dome(D, x, h, z, w * 0.3, rv() < 0.5 ? 'roofteal' : 'roofblue'); }

  // the sand between the stalls and courtyards drifts up and dips (shared/terrain.js). tiled floors, buildings, the canal's banks stay level
  shapeGround(B, D, { region: [-58, -58, 58, 58], mat: 'sand', seed: 777, up: 1.1, down: 0.6, near: 0.8, far: 4.5, points: [...new Set([...spawns, ...att, ...def])] });
  let graph = null;
  const map = { name: 'Bazaar', size: 'large', boxes: B.boxes, deco: D.boxes, killY: -50, floorY: -6, bounds, ceiling: 9,
    sky: { top: 0x4a8fd8, mid: 0xf2dcae, bot: 0x8a6a40, fog: 0xf0d8a8 }, fogNear: 100, fogFar: 380, spawns, teamSpawns: { att, def },
    // bots: a walk graph on the ground and on the caravanserai's gallery (up and down by its two flights)
    peekGraph() { return graph; }, dropGraph() { graph = null; }, get graph() { return graph || (graph = buildNav(B.boxes, { x0: bounds[0] - 1, z0: bounds[1] - 1, n: bounds[2] - bounds[0] + 2, cell: 1, levels: [0, 3.9], band: 0.5, keep: (x, z) => !outOfBounds(map, [x, 0, z]),
      stairs: [{ top: [-15.5, 3.9, -46.25], bot: [-9.5, 0, -46.25] }, { top: [15.5, 3.9, -43.75], bot: [9.5, 0, -43.75] }] })); },
  };
  return map;
}

// ------------------------------------------------------------ BAZAAR S&D: the Jank Bazaar, smugglers vs the bazaar guard
// (Plant & Defuse). the smugglers (attackers) come in with the caravan at the south gate; the guard (defenders) hold the
// palace at the north end. three lanes north: west, the spice alleys (a zigzag between the shops) to B; the middle, the
// Grand Hall (a covered hall, its doors at opposite corners, stalls down the middle) out into the courtyard under the
// Lamp Tower (mid), then the lamp shop west to B or the tea house east to A; east, the canal (walk the quays or wade it,
// three bridges) to A. B = the carpet warehouse's yard (rolls, frames of carpets, the warehouse's upstairs windows on
// it); A = the dye yard (vats to stand on, racks of cloth, the dye house's low roof). the guard come down the palace
// passage to mid, or round by the north alleys to either site, ~7 s before the smugglers
function bazaarSD() {
  const B = builder(), D = builder();
  const r = rng(7878), rv = rng(7979), W = B.local(0, 0, 0), Dw = D.local(0, 0, 0), add = B.add;
  const X0 = -60, X1 = 60, Z0 = -72, Z1 = 72, bounds = [X0, Z0, X1, Z1];
  const spawns = [];
  const blocks = [], block = (x0, z0, x1, z1, h, mat = 'adobe') => { add(x0, 0, z0, x1, h, z1, mat); blocks.push(Object.assign([x0, z0, x1, z1], { box: B.boxes[B.boxes.length - 1] })); add(x0, h, z0, x1, h + 0.3, z1, 'roof'); }; // a solid block of houses (over the ceiling: no roofs to sit on)
  // ---- the ground (the canal cut out of it), the wall round it all (its top's over the ceiling), the gates shut
  groundHoles(B, -300, -300, 300, 300, -2, 0, 'sand', [[39.6, -14.4, 44.4, 56.4]]);
  for (const s of [-1, 1]) { add(X0 - 1.2, 0, s > 0 ? Z1 : Z0 - 1.2, X1 + 1.2, 9, s > 0 ? Z1 + 1.2 : Z0, 'adobe'); add(s > 0 ? X1 : X0 - 1.2, 0, Z0, s > 0 ? X1 + 1.2 : X0, 9, Z1, 'adobe'); }
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) B.box(sx * (X1 + 0.6), 6, sz * (Z1 + 0.6), 5, 12, 5, 'adobe');
  for (const s of [-1, 1]) { const i0 = s * Z1 - s * 0.6, i1 = s * Z1 + s * 2.4; add(-8, 0, Math.min(i0, i1), -5, 11, Math.max(i0, i1), 'adobe'); add(5, 0, Math.min(i0, i1), 8, 11, Math.max(i0, i1), 'adobe'); D.add(-5, 0, s > 0 ? Z1 - 0.04 : Z0, 5, 6, s > 0 ? Z1 : Z0 + 0.04, 'wood'); }

  // ---- the caravan camp inside the south gate (the smugglers' spawn): tents, camels, the goods
  const att = [[-8, 0.2, 65], [-4, 0.2, 63], [0, 0.2, 65], [4, 0.2, 63], [8, 0.2, 65], [-6, 0.2, 68], [6, 0.2, 68]];
  for (const [x, z, c] of [[-20, 66, 'toypink'], [20, 66, 'cloth'], [-30, 62, 'toyteal']]) tent(W, x, z, c);
  for (const [x, z, ax] of [[14, 61, true], [-14, 60, false]]) camel(W, x, z, ax);
  cratePile(B, 26, 60, 4, r); cratePile(B, -26, 56, 3, r); hay(B, 30, 66, 3);
  // the lower town: the square the three lanes start from
  for (const [x, z, rot] of [[-30, 56, 0], [30, 56, 0], [-10, 50, 0], [10, 50, 0]]) stall(W, x, z, rot, rv);
  B.box(0, 0.4, 52, 3, 0.8, 3, 'marble'); B.box(0, 1.4, 52, 0.8, 2, 0.8, 'marble'); // a drinking fountain in the square

  // ---- MID: the Grand Hall (covered, its doors at opposite corners, three stall islands down the middle, side doors
  // half way: west to the alleys, east to the dyers' passage), then the courtyard under the Lamp Tower
  const HX = 9, HZ0 = -4, HZ1 = 40;
  add(-HX + 0.3, 0, HZ0 + 0.3, HX - 0.3, 0.05, HZ1 - 0.3, 'pottery');
  wall(W, 'x', HZ1, -HX - 0.3, HX + 0.3, 0, 7, 0.6, 'adobe', [{ a: -6, b: -2, y0: 0, y1: 4 }]);
  wall(W, 'x', HZ0, -HX - 0.3, HX + 0.3, 0, 7, 0.6, 'adobe', [{ a: 2, b: 6, y0: 0, y1: 4 }]);
  wall(W, 'z', -HX, HZ0 + 0.3, HZ1 - 0.3, 0, 7, 0.6, 'adobe', [{ a: 22, b: 25, y0: 0, y1: 3.4 }]);
  wall(W, 'z', HX, HZ0 + 0.3, HZ1 - 0.3, 0, 7, 0.6, 'adobe', [{ a: 13, b: 16, y0: 0, y1: 3.4 }]);
  add(-HX - 0.3, 7, HZ0 - 0.3, HX + 0.3, 7.3, HZ1 + 0.3, 'roof');
  for (const z of [4, 18, 32]) dome(D, 0, 7.3, z, 3.6, 'roofteal');
  for (const [cz, g, a] of [[29, 'pottery', 'cloth'], [17, 'carpet', 'pink'], [5, 'toyyellow', 'toyteal']]) { // stall islands (counters round a rack, an awning)
    for (const s of [-1, 1]) { add(-3, 0.05, cz + s * 1.2 - 0.45, 3, 1.05, cz + s * 1.2 + 0.45, 'wood'); add(-2.9, 1.05, cz + s * 1.2 - 0.35, 2.9, 1.35, cz + s * 1.2 + 0.35, g); }
    add(-2.2, 0.05, cz - 0.4, 2.2, 2.2, cz + 0.4, g); for (const px of [-3.2, 3.2]) for (const pz of [-1.9, 1.9]) B.box(px, 1.45, cz + pz, 0.15, 2.8, 0.15, 'wood'); add(-3.5, 2.85, cz - 2.2, 3.5, 3.0, cz + 2.2, a);
  }
  for (const [z0, z1, sx, g] of [[30, 36, -1, 'cloth'], [8, 12, -1, 'pottery'], [26, 31, 1, 'carpet'], [0, 6, 1, 'cloth']]) { const x0 = sx > 0 ? HX - 1.5 : -HX + 0.3, x1 = sx > 0 ? HX - 0.3 : -HX + 1.5; add(x0, 0.05, z0, x1, 1.0, z1, 'wood'); add(x0 + 0.1, 1.0, z0 + 0.1, x1 - 0.1, 1.35, z1 - 0.1, g); } // stalls on the walls
  for (const z of [10, 23, 36]) B.box(0, 3.3, z, 0.7, 6.6, 0.7, 'plaster'); // pillars between the islands
  const flagM = ['magenta', 'yellow', 'blue', 'mint', 'toyred'];
  for (const c of [-4.5, 4.5]) { D.add(c - 0.02, 6.2, HZ0 + 0.4, c + 0.02, 6.24, HZ1 - 0.4, 'wood'); for (let k = 0; k < 28; k++) { const z = HZ0 + 1.5 + k * 1.5; D.add(c - 0.02, 5.65, z - 0.25, c + 0.02, 6.2, z + 0.25, flagM[k % 5]); } }
  for (const z of [0, 12, 24, 36]) D.box(0, 5.4, z, 0.6, 0.6, 0.6, 'lamp');
  // the courtyard (mid): the Lamp Tower in a fountain, benches; the lamp shop (west, through to B) and the tea house (east, through to A)
  lampTower(B, D, 0, -15, 18);
  for (const [x0, z0, x1, z1] of [[-4.5, -19.5, 4.5, -19], [-4.5, -11, 4.5, -10.5], [-4.5, -19, -4, -11], [4, -19, 4.5, -11]]) add(x0, 0, z0, x1, 0.6, z1, 'marble');
  for (const [x0, z0, x1, z1] of [[-4, -19, 4, -17], [-4, -13, 4, -11], [-4, -17, -2, -13], [2, -17, 4, -13]]) D.add(x0, 0.02, z0, x1, 0.4, z1, 'water');
  add(-8.5, 0, -7.4, -5.5, 0.5, -6.4, 'wood'); add(5.5, 0, -25.4, 8.5, 0.5, -24.4, 'wood'); // benches
  // the arcades off the courtyard: west to B (the lamp shop on it), east to A (the tea house on it). pillars on the open
  // side, a roof (a low perch), the shops' fronts on the other
  for (const s of [-1, 1]) {
    const x0 = s > 0 ? 9 : -26, x1 = s > 0 ? 26 : -9;
    add(x0, 3.4, -24, x1, 3.6, -18, 'roof'); for (let x = x0 + 1; x <= x1 - 0.9; x += 3.4) B.box(x, 1.7, -18.3, 0.45, 3.4, 0.45, 'plaster');
    souk(B, D, s * 17, -27, 2, 16, 5.7, 1, { // (5.7 deep: shell's walls sit half outside the footprint, so this one's faces meet the wing and the arcade's roof, not cut into them)
      paint: s > 0 ? 'sidemint' : 'sidelemon', goods: s > 0 ? 'pottery' : 'gold', awning: false, roofAccess: false, backDoor: false });
    for (const [x, z] of [[s * 13, -22], [s * 22, -21]]) B.box(x, 0.45, z, 0.9, 0.9, 0.7, 'cloth');
    for (let x = x0 + 2; x < x1 - 1; x += 2.5) D.box(x, 3.1, -21, 0.45, 0.5, 0.45, 'lamp'); // lamps under the arcade's roof
  }

  // ---- the palace (the guard's spawn): its forecourt, the passage south to mid, the alleys west to B and east to A
  const def = [[-8, 0.2, -65], [-4, 0.2, -63], [0, 0.2, -65], [4, 0.2, -63], [8, 0.2, -65], [-6, 0.2, -68], [6, 0.2, -68]];
  for (const x of [-12, -6, 6, 12]) B.box(x, 3, -70.6, 1.2, 6, 1.2, 'marble'); add(-15, 6, -71.4, 15, 7, -69.6, 'marble'); // the palace front (its door's the shut north gate)
  block(X0, Z0, -16, -56, 8); block(16, Z0, X1, -56, 8); // either side of the forecourt (the north alley runs along their south faces)
  block(-26, -50, -4, -30, 8); block(4, -50, 26, -30, 8); // the palace wings: the passage south to mid between them
  block(X0, -50, -46, -46, 8); block(46, -50, X1, -46, 8); // the alley's far ends
  for (const [x, z] of [[-10, -58], [10, -58]]) B.box(x, 0.6, z, 1.2, 1.2, 1.2, 'crate');

  // ---- WEST LANE: the spice alleys (north, a dog-leg east, north, a dog-leg west, north into B)
  block(X0, -22, -46, 40, 8); block(X0, -46, -56, -22, 8); // the west side, behind the warehouse
  block(-42, 26, -9.3, 40, 8); // north of the dog-leg east (which runs on to the hall's side door)
  block(-30, -2, -9.3, 22, 8); block(-46, -2, -34, 22, 8); // either side of the long run north
  block(-38, -19.7, -26, -6, 8); block(-26, -18, -9.3, -6, 8); block(-46, -19.7, -42, -2, 8); // round the last dog-leg west and the run north into B

  for (const [x, z] of [[-42.6, 36], [-30.6, 14], [-38.6, -12]]) B.box(x, 0.45, z, 0.9, 0.9, 0.7, 'cloth');
  for (const [x, z] of [[-22, 25.2]]) { add(x - 1.4, 0, z - 0.7, x + 1.4, 0.9, z + 0.7, 'wood'); for (const [m, k] of [['toyred', -0.8], ['toyyellow', 0], ['sideorange', 0.8]]) D.box(x + k, 1.05, z, 0.6, 0.3, 0.6, m); }
  D.add(-44, 3.6, 23.98, -12, 3.63, 24.02, 'wood'); for (const x of [-40, -33, -26, -19]) D.box(x, 3.2, 24, 0.4, 0.5, 0.4, 'lamp'); // lanterns over the dog-leg

  // ---- EAST LANE: the canal (quays both sides, three bridges, boats moored, ankle-deep water to wade)
  add(39.6, -2, -14.4, 44.4, -0.5, 56.4, 'stone'); D.add(40, -0.5, -14, 44, -0.3, 56, 'water');
  for (const x0 of [39.6, 44]) add(x0, -0.5, -14, x0 + 0.4, 0.1, 56, 'stone'); for (const z of [-14.4, 56]) add(39.6, -2, z, 44.4, 0.1, z + 0.4, 'stone');
  for (const z of [40, 16, -6]) { add(39.2, 0.1, z - 2, 44.8, 0.4, z + 2, 'stone'); for (const s of [-1, 1]) add(39.2, 0.4, s > 0 ? z + 1.7 : z - 2, 44.8, 1.0, s > 0 ? z + 2 : z - 1.7, 'stone'); } // the bridges
  for (const [z0, z1] of [[24, 30], [-2, 3]]) { add(40.4, -0.5, z0, 43.6, 0.0, z1, 'wood'); add(40.6, 0.0, z0 + 0.4, 43.4, 0.35, z1 - 0.4, 'wood'); } // boats (stand in them)
  block(9.3, -18, 26, 12, 8); block(26, -19.7, 35, 12, 8); block(9.3, 17, 35, 40, 8); // the canal's west side: the dyers' passage (from the hall's side door) between
  block(35, -2, 39.6, 8, 8); // a warehouse built out to the canal's edge: the west quay stops here (cross a bridge, or wade)
  block(50, -19.7, X1, 40, 8); block(56, -46, X1, -19.7, 8); block(46, -46, 56, -43, 8); block(46, -23, 56, -19.7, 8); // the east bank's warehouses, round the dye house
  for (const [x, z] of [[47, 33], [36.3, 26], [48.5, 24], [36.3, -10]]) cratePile(B, x, z, 2, r);
  for (const [x, z] of [[46.5, 46], [36.5, -11]]) B.box(x, 0.6, z, 0.75, 1.2, 0.75, 'barrel');

  // ---- B: the carpet warehouse (its upstairs windows on the yard), the yard: rolls stacked, carpets drying on frames
  souk(B, D, -51, -34, 1, 23.7, 10, 2, { paint: 'sidepink', sign: 'adcarpet', goods: 'carpet', awning: 'magenta', balcony: true, roofAccess: false, backDoor: false });
  wall(W, 'x', -20, -46, -26, 0, 3.2, 0.6, 'adobe', [{ a: -42.5, b: -38, y0: 0, y1: 3.2 }]); // the yard's south wall, the alleys' way in
  wall(W, 'x', -46, -46, -26, 0, 3.2, 0.6, 'adobe', [{ a: -35, b: -30.5, y0: 0, y1: 3.2 }]); // its north wall, the guard's way in
  wall(W, 'z', -26, -46.3, -24.6, 0, 3.2, 0.6, 'adobe'); // the east side (the lamp shop's back door at its south end)
  for (const [z, m] of [[-38.5, 'carpet'], [-31, 'magenta']]) hanging(B, D, -42, -32, z, m);
  for (let i = 0; i < 3; i++) add(-45.4, i * 0.6, -28 + i * 0.2, -43, (i + 1) * 0.6, -24 - i * 0.2, 'carpet'); add(-30, 0, -44.2, -27.6, 1.2, -41.8, 'carpet'); add(-38, 0, -26.4, -35, 0.9, -24.4, 'carpet');
  cart(W, -34, -35, true); B.box(-29, 0.6, -33, 1.2, 1.2, 1.2, 'crate');
  siteBoard(D, -38, 0.6, -45.62, 'x', 'siteb', 2.2); siteBoard(D, -44.5, 0.8, -19.62, 'x', 'siteb', 1.6);

  // ---- A: the dye yard (vats to stand on, racks of cloth), the dye house (its low roof looks over it)
  souk(B, D, 51, -33, 3, 19.7, 10, 1, { paint: 'sidelilac', sign: 'addye', goods: 'cloth', awning: 'toyteal', backDoor: false }); // (its roof's under the ceiling: a perch)
  wall(W, 'x', -20, 26, 45, 0, 3.2, 0.6, 'adobe', [{ a: 36, b: 40.5, y0: 0, y1: 3.2 }]); // the yard's south wall, the canal's way in
  wall(W, 'x', -46, 26, 45, 0, 3.2, 0.6, 'adobe', [{ a: 30.5, b: 35, y0: 0, y1: 3.2 }]); // north, the guard's way in
  wall(W, 'z', 26, -46.3, -24.6, 0, 3.2, 0.6, 'adobe');
  ['magenta', 'yellow', 'blue', 'mint'].forEach((m, i) => dyeVat(B, D, i % 2 ? 39 : 32, i < 2 ? -40 : -29, 3.6, m));
  hanging(B, D, 30, 41, -34.5, 'toyred');
  B.box(42.5, 0.6, -24, 1.2, 1.2, 1.2, 'crate'); B.box(42.5, 1.8, -24, 1.1, 1.1, 1.1, 'crate');
  siteBoard(D, 38, 0.6, -45.62, 'x', 'sitea', 2.2); siteBoard(D, 43, 0.8, -19.62, 'x', 'sitea', 1.6);

  dressFacades(B, D, blocks, rng(8181), (x, z) => x > X0 + 0.3 && x < X1 - 0.3 && z > Z0 + 0.3 && z < Z1 - 0.3); // (after everything else: it leaves room for it)

  // ---- outside the wall (render-only): dunes, rocks, the caravan's tail outside the south gate, the next town over
  horizon(D, -300, -300, 300, 300, 1500, 'sand');
  for (let i = 0; i < 40; i++) { const a = rv() * Math.PI * 2, d = 120 + rv() * 220, x = Math.cos(a) * d, z = Math.sin(a) * d, w = 30 + rv() * 60, dd = 18 + rv() * 36; if (Math.abs(x) - w / 2 < 75 && Math.abs(z) - dd / 2 < 85) continue; dune(D, x, z, w, dd, 5 + rv() * 12); }
  B.boxes.arch.push({ id: 'rocks_bazaar_sd', p: [0, 0, 0], r: 0 }); const RK = { av: 'rocks_bazaar_sd', ai: B.boxes.arch.length - 1 }; // (its rock: one Blender model, look only)
  for (let i = 0; i < 12; i++) { const a = rv() * Math.PI * 2, d = 200 + rv() * 220; rocks(D, Math.cos(a) * d, Math.sin(a) * d, 12 + rv() * 20, rv, RK); }
  for (const [x, z, c] of [[-14, 86, 'cloth'], [10, 92, 'toypink'], [30, 84, 'toyteal']]) tent(Dw, x, z, c);
  for (const [x, z, ax] of [[-2, 98, true], [22, 100, false], [-26, 94, true]]) camel(Dw, x, z, ax);
  D.add(-3, 0, 74, 3, 0.03, 400, 'dirtroad');
  for (let i = 0; i < 24; i++) { const x = 300 + (rv() - 0.5) * 120, z = -160 + (rv() - 0.5) * 140, w = 8 + rv() * 10, h = 4 + rv() * 9;
    D.add(x - w / 2, 0, z - w / 2, x + w / 2, h, z + w / 2, rv() < 0.7 ? 'adobe' : ['sidepink', 'sidelemon', 'sidemint'][(rv() * 3) | 0]); if (rv() < 0.3) dome(D, x, h, z, w * 0.3, rv() < 0.5 ? 'roofteal' : 'roofblue'); }

  spawns.push(...att.slice(0, 2), ...def.slice(0, 2), [0, 0.2, 20], [-5, 0.2, 10], [0, 0.2, -24], [-44, 0.2, 44], [-32, 0.2, 12], [-40, 0.2, -12], [37, 0.2, 44], [47, 0.2, 10],
    [36.5, 0.2, -12], [-36, 0.2, -33], [36, 0.2, -36], [0, 0.2, -40], [-30, 0.2, -53], [30, 0.2, -53], [-18, 0.2, -21], [18, 0.2, -21]);
  let graph = null;
  const map = { name: 'Bazaar', size: 'large', boxes: B.boxes, deco: D.boxes, killY: -50, floorY: -6, bounds, ceiling: 7,
    sky: { top: 0x4a8fd8, mid: 0xf2dcae, bot: 0x8a6a40, fog: 0xf0d8a8 }, fogNear: 100, fogFar: 380, spawns, teamSpawns: { att, def },
    // the smugglers' lanes (the bomb carriers walk these; the walk graph gets them round whatever's in the way)
    nav: {
      A: [
        [[6, 61], [20, 54], [38.2, 50], [38.2, 20], [42, 16], [47, 13], [47, -3], [42, -6], [37.5, -8.5], [38.2, -14], [38.5, -20], [37, -27]], // the canal (over and back by the bridges)
        [[0, 61], [-4, 50], [-4, 42], [-6, 36], [-6, 22], [-6, 1], [4, -1], [4, -6], [8, -14], [10, -21], [26, -21.5], [32, -26]], // the hall, the courtyard, the tea arcade
        [[2, 61], [-4, 50], [-4, 42], [6, 34], [6, 20], [7, 14.5], [12, 14.5], [36, 14.5], [42, 16], [47, 13], [47, -3], [42, -6], [37.5, -8.5], [38.2, -14], [38.5, -20], [40, -27]], // the hall, the dyers' passage, the canal
      ],
      B: [
        [[-6, 61], [-20, 54], [-44, 50], [-44, 30], [-44, 24], [-32.5, 24], [-32.5, 4], [-32, -4], [-40.5, -4], [-40.5, -14], [-40, -20], [-38, -27]], // the spice alleys
        [[-2, 61], [-4, 50], [-4, 42], [-6, 36], [-6, 22], [-6, 1], [4, -1], [4, -6], [-8, -14], [-10, -21], [-26, -21.5], [-32, -26]], // the hall, the courtyard, the lamp arcade
        [[-4, 61], [-4, 50], [-4, 42], [-6, 36], [-7, 23.5], [-12, 23.5], [-32.5, 24], [-32.5, 4], [-32, -4], [-40.5, -4], [-40.5, -14], [-40, -20], [-36, -27]], // the hall, the side door, the alleys
      ],
    },
    sites: [{ id: 'A', min: [28, 0, -44], max: [46, 0, -22] }, { id: 'B', min: [-46, 0, -44], max: [-28, 0, -22] }],
    peekGraph() { return graph; }, dropGraph() { graph = null; }, get graph() { return graph || (graph = buildNav(B.boxes, { x0: bounds[0] - 1, z0: bounds[1] - 1, n: Math.max(bounds[2] - bounds[0], bounds[3] - bounds[1]) + 2, cell: 1, levels: [0], band: 0.5, keep: (x, z) => !outOfBounds(map, [x, 0, z]) })); },
  };
  return map;
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
      addOpen(opens, e.ax, e.line, { a: c - w / 2, b: c + w / 2, y0: 0, y1: (r() < 0.55 && r(), H + 0.2) }); // every doorway goes up into the ceiling, so bhops and grapples don't clip a lintel (the r() calls stay so the layout doesn't change)
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
    D.add(pr[0], PY, pr[1], pr[2], PY + 0.42, pr[3], 'poolwater'); // (just under the first step's top, 0.45 up: level with it, the two shimmered)
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
  // ---- look only: every wallpaper wall, pillar and half wall is drawn by one Blender model (tools/blender/arch/make_backrooms.py,
  // archfield.js). the boxes stay what you bump into, and come back if the file doesn't
  B.boxes.arch.push({ id: 'backrooms', p: [0, 0, 0], r: 0 }); const AV = { av: 'backrooms', ai: B.boxes.arch.length - 1 };
  for (const b of B.boxes) if (b.mat === 'wallpaper') Object.assign(b, AV);
  const HZ = 0xb4a35a; // the haze
  return {
    name: 'Backrooms', size: 'extra large', boxes: B.boxes, deco: D.boxes, killY: -50,
    sky: { top: HZ, mid: HZ, bot: HZ, fog: HZ }, fogNear: 6, fogFar: 105,
    light: { hemi: [0xfff3cc, 0xb2a476, 1.35], sun: [0xffe7a6, 0.5] }, // flat fluorescent light from everywhere
    chunk: 48, sealed: true, menuCam: [13, 3.4, -0.08], // big: drawn in chunks. sealed: no sky, and the menu orbits inside the hall
    spawns, spawnSafe: 45, teamSpawns: { att: att2, def: def2 }, teamSpawnsBomb: true, roundTime: 150, // lobbies only for Plant & Defuse (they're 226 m apart); rounds are longer, it's a long walk
     peekGraph() { return graph; }, dropGraph() { graph = null; nav = null; }, get nav() { return lanes(); }, get graph() { return navGraph(); },
    sites: [{ id: 'A', min: [gx(siteA.i0) + 0.5, 0, gx(siteA.j0) + 0.5], max: [gx(siteA.i1) - 0.5, 0, gx(siteA.j1) - 0.5] },
      { id: 'B', min: [gx(siteB.i0) + 0.5, 0, gx(siteB.j0) + 0.5], max: [gx(siteB.i1) - 0.5, 0, gx(siteB.j1) - 0.5] }],
  };
}

function range() {
  const { boxes, box } = builder();
  box(0, -1, -60, 40, 2, 150, 'grass');
  box(0, -6, -60, 30, 8, 130, 'dirt');
  propOf('rangebench', [0, 0, 5], 0, () => box(0, 0.4, 5, 40, 0.8, 1, 'wood')); // the shooting bench (Blender: p_rangebench)
  for (const z of [-10, -25, -50, -100]) propOf('rangemark', [-17, 0, z], 0, () => box(-17, 0.6, z, 4, 1.2, 0.4, 'wood'), { v: 'v' + (5 - z) }); // distance boards: how far from the bench
  box(32, -1, -40, 20, 2, 40, 'grass');
  box(28, 0.15, -25, 2.5, 0.3, 2.5, 'pad', { pad: [0, 30, 0] });
  box(36, 0.15, -35, 2.5, 0.3, 2.5, 'pad', { pad: [0, 22, -22] });
  for (let i = 0; i < 6; i++) box(32 + (i % 2 ? 6 : -6), 20 + i * 4, -30 - i * 14, 3, 1, 3, 'pink');
  box(32, 9, -55, 3, 18, 3, 'stone');
  box(-32, -1, -40, 16, 2, 30, 'stone');
  box(-38, 1, -40, 1, 2, 30, 'missing');
  // the SPRAY RANGE (owner, 2026-11-07): a wall 10 m from a marked firing spot, left of the line. stand in it and S&D guns
  // shoot with the Plant & Defuse spray patterns (public/js/sprayrange.js); the rest of Training stays chaos
  box(-54, 3, -12.25, 16, 6, 0.5, 'stone');
  groundHoles({ add: (...a) => boxes.push({ min: [a[0], a[1], a[2]], max: [a[3], a[4], a[5]], mat: a[6] }) }, -220, -280, 220, 160, -2, 0, 'grass', [[-20, -135, 20, 15], [22, -60, 42, -20], [-40, -55, -24, -25]]);
  const D = builder();
  horizon(D, -220, -280, 220, 160, 1500, 'grass'); // the same grass as the field you stand on
  D.add(-58, 0.01, -2.3, -50, 0.07, -1.7, 'sand'); // the spray range's firing line (10 m from its wall)
  D.add(-60, 0, -175, 60, 12, -160, 'dirt'); D.add(-50, 12, -172, 50, 16, -163, 'dirt'); // the berm the bullets end up in
  for (let x = -18, k = 0; x <= 18; x += 3.2, k++) propOf('sandbags', [x + 1.5, 0, 6.9], 0, () => D.add(x, 0, 6.4, x + 3, 0.8, 7.4, 'sand'), { spin: k % 2 ? Math.PI : 0 }); // sandbags on the firing line (p_sandbags; every other one turned round: no pink bag every 3 m)
  for (const [x, z] of [[-30, 20], [30, 20]]) { for (const sx of [-1, 1]) for (const sz of [-1, 1]) D.box(x + sx * 1.6, 4, z + sz * 1.6, 0.3, 8, 0.3, 'wood'); D.add(x - 2.2, 8, z - 2.2, x + 2.2, 8.3, z + 2.2, 'wood'); D.add(x - 2.4, 10.5, z - 2.4, x + 2.4, 10.8, z + 2.4, 'roofg'); } // watchtowers
  for (let z = 30; z > -260; z -= 10) for (const x of [-90, 90]) { D.box(x, 1, z, 0.15, 2, 0.15, 'metal'); D.add(x - 0.03, 1.6, z, x + 0.03, 1.65, z + 10, 'tire'); }
  for (let i = 0; i < 30; i++) { const rr = rng(400 + i), a = rr() * Math.PI * 2, d = 150 + rr() * 150; (rr() < 0.5 ? conifer : lollipop)(D.local(0, 0, 0), Math.cos(a) * d, -60 + Math.sin(a) * d, 6 + rr() * 4, rr); }
  adBoard(D, -26, -70, 0, 'z', 'adcity6', 14, 6); adBoard(D, -26, -110, 0, 'z', 'adcity3', 14, 6); adBoard(D, 0, -130, 0, 'x', 'adcity2', 24, 9);
  return { name: 'Range', size: 'training', boxes, deco: D.boxes, killY: -60, floorY: -4, bounds: [-90, -175, 90, 40],
    sprayRange: { min: [-63, -1, -12], max: [-45, 8, 16], wall: -12, stand: [-54, 0, -2] }, // (inside it: S&D gunplay)
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
function pine(B, D, x, z, h, r) { const o = {}; propOf('pine', [x, 0, z], 0, () => { o.spin = pineBoxes(B, D, x, z, h, r) || 1e-6; }, o); } // (the Blender pine, turned like its tiers)
function pineBoxes(B, D, x, z, h, r) { // a pine: a trunk you bump into, a stack of turned tiers you only see
  const tw = 0.26 + r() * 0.16;
  B.add(x - tw, 0, z - tw, x + tw, h * 0.94, z + tw, r() < 0.15 ? 'bark2' : 'bark');
  const n = 5 + ((r() * 2) | 0), base = h * (0.3 + r() * 0.08), span = h - base, w0 = 3.4 + r() * 1.6, yaw = r() * 3;
  for (let i = 0; i < n; i++) {
    const k = i / n, w = w0 * (1 - k * 0.82), y = base + k * span;
    D.obb(x, y + span / n * 0.62, z, w, span / n * 1.3, w * (0.82 + r() * 0.3), yaw + i * 0.7 + r() * 0.3, (i + ((x * 7) | 0)) % 3 ? 'pine' : 'pine2');
  }
  D.obb(x, h + 0.45, z, 0.5, 1.1, 0.5, yaw, 'pine2');
  return yaw;
}
function deadTree(B, D, x, z, h, r) { propOf('deadtree', [x, 0, z], 0, () => deadTreeBoxes(B, D, x, z, h, r), { spin: spinAt(x, z) || 1e-6 }); }
function deadTreeBoxes(B, D, x, z, h, r) { // bare, grey, too many elbows
  B.add(x - 0.3, 0, z - 0.3, x + 0.3, h, z + 0.3, 'deadbark');
  for (let i = 0; i < 5; i++) {
    const y = h * (0.4 + i * 0.12), l = 1.2 + r() * 1.8 * (1 - i * 0.12), a = r() * 6.3;
    D.obb(x + Math.cos(a) * l / 2, y, z + Math.sin(a) * l / 2, l, 0.16, 0.16, -a, 'deadbark');
    D.obb(x + Math.cos(a) * l, y + 0.45, z + Math.sin(a) * l, 0.12, 0.9, 0.12, -a, 'deadbark'); // the elbow up at the end
  }
}
function birch(B, D, x, z, h, r) { propOf('birch', [x, 0, z], 0, () => birchBoxes(B, D, x, z, h, r), { spin: spinAt(x, z) || 1e-6 }); }
function birchBoxes(B, D, x, z, h, r) { // white trunks: they catch the flashlight, so you think something is standing there
  B.add(x - 0.2, 0, z - 0.2, x + 0.2, h, z + 0.2, 'birch');
  for (let i = 0; i < 3; i++) D.obb(x + (r() - 0.5) * 0.8, h * (0.62 + i * 0.13), z + (r() - 0.5) * 0.8, 2.4 - i * 0.5, 1.1, 2.0 - i * 0.4, r() * 3, 'birchleaf');
}
function log(B, x0, z0, x1, z1, rr = 0.42) { // a fallen log along x or z (with a lighter cut end)
  const ax = Math.abs(x1 - x0) > Math.abs(z1 - z0);
  if (ax) { B.add(x0, 0, z0 - rr, x1, rr * 2, z0 + rr, 'logside'); B.add(x1, 0.02, z0 - rr + 0.04, x1 + 0.06, rr * 2 - 0.04, z0 + rr - 0.04, 'logend'); }
  else { B.add(x0 - rr, 0, z0, x0 + rr, rr * 2, z1, 'logside'); B.add(x0 - rr + 0.04, 0.02, z1, x0 + rr - 0.04, rr * 2 - 0.04, z1 + 0.06, 'logend'); }
}
function boulder(B, x, z, s, r, tag) { // a rock: a big block and a couple of smaller ones shoved into it. tag: { av, ai } when a Blender rock model draws it
  B.add(x - s, 0, z - s * 0.8, x + s, s * 1.1, z + s * 0.8, 'rockf', tag);
  B.add(x - s * 0.7, s * 1.1, z - s * 0.5, x + s * 0.5, s * 1.5, z + s * 0.6, 'rockf', tag);
  if (r() < 0.6) B.add(x + s * 0.7, 0, z + s * 0.4, x + s * 1.5, s * 0.7, z + s * 1.2, 'rockmoss', tag);
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
  B.boxes.arch.push({ id: 'rocks_forest', p: [0, 0, 0], r: 0 }); const RK = { av: 'rocks_forest', ai: B.boxes.arch.length - 1 }; // (its rock: one Blender model, look only)
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
  for (let i = 0; i < 520; i++) { const x = bx0 - 20 + r() * (bx1 - bx0 + 40), z = bz0 - 20 + r() * (bz1 - bz0 + 40); if (x > SH - 2 || !free(x, z, -0.5)) continue; const s = 0.6 + r() * 0.8, a = r() * 3; if (r() < 0.55) { propOf('fern', [x, 0, z], 0, () => { for (let k = 0; k < 3; k++) D.obb(x, s * 0.28, z, s * 1.5, s * 0.56, 0.07, a + k * 1.05, 'fern'); }, { spin: a || 1e-6 }); } else { propOf('bush', [x, 0, z], 0, () => { D.obb(x, s * 0.3, z, s * 1.1, s * 0.6, s * 0.9, a, 'bush'); D.obb(x + 0.2, s * 0.75, z - 0.1, s * 0.7, s * 0.4, s * 0.6, a + 0.8, 'bush'); }, { spin: a || 1e-6 }); } } // ferns: three crossed fronds. bushes: a clump
  for (let i = 0; i < 70; i++) { const x = bx0 + r() * (bx1 - bx0), z = bz0 + r() * (bz1 - bz0); if (x > SH - 4 || !free(x, z, 1)) continue; if (r() < 0.55) { const l = 3 + r() * 4; r() < 0.5 ? log(B, x, z, x + l, z) : log(B, x, z, x, z + l); } else if (r() < 0.6) boulder(B, x, z, 0.6 + r() * 0.9, r, RK); else B.add(x - 0.35, 0, z - 0.35, x + 0.35, 0.5 + r() * 0.4, z + 0.35, 'logend'); }

  // ---- the clearing: a ring of standing stones, one dead tree, and an office chair facing away from you
  for (let i = 0; i < 7; i++) { const a = (i / 7) * Math.PI * 2 + 0.3, x = CLR[0] + Math.cos(a) * 9.5, z = CLR[1] + Math.sin(a) * 9.5, tall = 1.8 + (i % 3) * 0.6; B.add(x - 0.6, 0, z - 0.45, x + 0.6, tall, z + 0.45, i % 2 ? 'rockf' : 'rockmoss'); }
  deadTree(B, D, CLR[0] + 3, CLR[1] - 2, 8.5, r);
  W(CLR[0] - 2.4, 0, CLR[1] + 1.7, CLR[0] - 1.8, 0.08, CLR[1] + 2.3, 'metal'); W(CLR[0] - 2.15, 0.08, CLR[1] + 1.95, CLR[0] - 2.05, 0.55, CLR[1] + 2.05, 'chrome'); // the office chair: base, stem
  W(CLR[0] - 2.45, 0.55, CLR[1] + 1.7, CLR[0] - 1.75, 0.68, CLR[1] + 2.4, 'officechair'); W(CLR[0] - 2.45, 0.68, CLR[1] + 2.32, CLR[0] - 1.75, 1.45, CLR[1] + 2.42, 'officechair');
  W(CLR[0] + 6, 0, CLR[1] + 4, CLR[0] + 6.6, 1.25, CLR[1] + 4.6, 'white'); W(CLR[0] + 6.05, 1.25, CLR[1] + 4.05, CLR[0] + 6.55, 1.75, CLR[1] + 4.55, 'coolerwater'); // a water cooler. in the woods. for whom
  log(B, CLR[0] - 12, CLR[1] + 8, CLR[0] - 6, CLR[1] + 8); boulder(B, CLR[0] + 11, CLR[1] - 8, 1.0, r, RK);

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
  // the forest floor heaves: rises, hollows, root mounds (shared/terrain.js). the two sites, the cabin, the trails' ends and the lake shore stay level
  shapeGround(B, D, { region: [FOREST.bounds[0], FOREST.bounds[1], FOREST.shore, FOREST.bounds[3]], mat: 'needles', seed: 6161, up: 1.6, down: 1.0, big: 9,
    flat: sites.map((q) => [q.min[0] - 2, q.min[2] - 2, q.max[0] + 2, q.max[2] + 2]), points: [...new Set([...spawns, ...att, ...def])] });
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
    peekGraph() { return graph; }, dropGraph() { graph = null; nav = null; }, get nav() { return lanes(); }, get graph() { return navGraph(); },
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
  B.add(-0.9, 0, -29, 0.9, 0.9, -28.1, 'crate', W.P('zmcrate', 0, -28.55, 0, { v: 'body' })); // (the Blender crate's body is drawn over it, its lid swings in public/js/zombies.js)
  const cola = { at: [-10.4, 0, -24], n: [1, 0, 0] };
  B.add(-10.75, 0, -24.55, -10.05, 2.03, -23.45, 'metal'); // (Jank Cola's machine is drawn over it too)
  // ---- ARCADE: three rows of back-to-back cabinets (gaps halfway down), screens glowing on both sides
  for (const x of [-31, -24, -17]) for (const [z0, z1] of [[-24, -15], [-13, -4]]) {
    B.add(x - 0.9, 0, z0, x + 0.9, 1.9, z1, x === -24 ? 'containerr' : 'containerb');
    B.add(x - 0.96, 1.15, z0 + 0.3, x - 0.9, 1.65, z1 - 0.3, 'light'); B.add(x + 0.9, 1.15, z0 + 0.3, x + 0.96, 1.65, z1 - 0.3, 'light');
  }
  // ---- LOADING DOCK: crates, pallets, a forklift, the power switch on the east wall
  for (const [x, z, n] of [[16, -24, 2], [17.3, -24, 1], [29, -18, 2], [21, -8, 1], [32, -27, 1], [15.2, -1.5, 1]]) for (let k = 0; k < n; k++) B.box(x, 0.6 + k * 1.2, z, 1.2, 1.2, 1.2, 'crate');
  B.add(23, 0, -15, 26, 0.25, -12, 'wood'); B.add(30, 0, -6, 31.4, 1.4, -4, 'caryellow'); B.add(30.2, 1.4, -5.8, 31.2, 2.2, -4.6, 'glass');
  const power = { at: [36.7, 1.6, -14], n: [-1, 0, 0] };
  // ---- the other cola machines (shared/zmshop.js), one per wing, and the Warranty Voider on the dock's north wall
  const colas = [
    { id: 'getup', at: [10.4, 0, 24], n: [-1, 0, 0] }, { id: 'legday', at: [-36.4, 0, 7], n: [1, 0, 0] },
    { id: 'pockets', at: [36.4, 0, 16], n: [-1, 0, 0] }, { id: 'thirdhand', at: [-28, 0, 3.4], n: [0, 0, -1] },
  ];
  for (const c of colas) B.add(c.at[0] - (c.n[0] ? 0.35 : 0.55), 0, c.at[2] - (c.n[2] ? 0.35 : 0.55), c.at[0] + (c.n[0] ? 0.35 : 0.55), 2.03, c.at[2] + (c.n[2] ? 0.35 : 0.55), 'metal'); // a bit inside the model (the client draws the machine over it)
  const up = { at: [20, 0, -29.5], n: [0, 0, 1] };
  B.add(19.15, 0, -29.97, 20.85, 0.93, -28.96, 'metal'); B.add(19.15, 0.93, -29.97, 20.85, 2.28, -29.4, 'metal'); // a bit inside the model (the client draws the machine over it), behind its sunken screen
  // ---- the Cheat Machine (server/zmextra.js): against the arcade's north wall, a random modifier once the power's on
  const mach = { at: [-14, 0, -29.6], n: [0, 0, 1] };
  B.add(-14.5, 0, -29.97, -13.5, 1.28, -29.25, 'metal'); B.add(-14.5, 1.28, -29.97, -13.5, 2.12, -29.38, 'metal'); // a bit inside the model (the client draws the machine over it), behind its sunken screen
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
    { w: 'burst', price: 1300, at: [10.79, 1.55, -8], n: [-1, 0, 0] }, // the rifle pack (the other two are in the crate)
    { w: 'lever', price: 1100, at: [-36.99, 1.55, 2], n: [1, 0, 0] },
    { w: 'autoshot', price: 1400, at: [-20, 1.55, 4.21], n: [0, 0, 1] },
  ];
  const spawns = [[-4, 0.1, 24], [4, 0.1, 24], [-7, 0.1, 17.5], [7, 0.1, 17.5], [0, 0.1, 25], [-8, 0.1, 22], [8, 0.1, 22], [0, 0.1, 15]];
  return {
    name: 'Dead Mall', size: 'medium', boxes: B.boxes, killY: -20,
    sky: { top: 0x06050c, mid: 0x1a1220, bot: 0x05040a, fog: 0x140e18 }, fogNear: 16, fogFar: 80, spawns,
    zm: { bounds: [X0 - 4, Z0 - 4, X1 + 4, Z1 + 4], H, start: 'hall', areas, doors, windows, buys, crate, power, cola, mach, colas, up },
  };
}

export const MAPS = {
  crate: crate(), platform: platform(), platform_sd: platformSD(), rooftop: rooftop(), rooftop_sd: rooftopSD(), suburb: suburb(), suburb_sd: suburbSD(), warehouse: warehouse(), warehouse_sd: warehouseSD(),
  desert: desert(), desert_sd: desertSD(), islands: islands(), islands_sd: islandsSD(), skyline: skyline(), skyline_sd: skylineSD(), bazaar: bazaar(), bazaar_sd: bazaarSD(), range: range(), backrooms: backrooms(), forest: forest(),
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
  BOXES.terrain = m.boxes.terrain || null; // shaped ground (shared/terrain.js): the copy needs the heightfield too
  SPAWNS.length = 0; SPAWNS.push(...m.spawns);
  Object.assign(MAP, { id: MAPS[id] ? id : 'islands', name: m.name, killY: m.killY, sky: m.sky, fogNear: m.fogNear, fogFar: m.fogFar, size: m.size });
}
setMap('islands');
// the building kit, for maps built in their own files (shared/jankburg.js)
export { builder, rng, wall, slab, stairs, windows, shell, car, tree, streetlight, billboard, tower, carve, horizon, home, lollipop, conifer, adBoard, stall, pot, cart, tent, palm, pallets, forklift, groundHoles, unstick };
