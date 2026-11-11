// Plant & Defuse in 3D: the armor people bought on their models (a plate carrier, a bucket on the head, defuse
// pliers on the hip), gear lying on the floor (the real weapon models, tumbling down and settling), the spawn barriers,
// and the first-person buy / pickup / drop moves. Shapes are built once per fit and shared; materials are cached.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { G } from './ctx.js';
import { M, buildWeapon, buildProjectile, setKatana, freeTree, buildCharacter } from './models.js';
import { jankify } from './jank.js';
import { BOXES } from '/shared/map.js';
import { raycast } from '/shared/physics.js';
import { ITEMS } from '/shared/weapons.js';
import { TEAMS } from '/shared/modes.js';
import { fx } from './fx.js';
import { emitSkinFx } from './skins.js';
import { ANIMS } from './anim.js';
import { topSize } from './clothes.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);
const hex = (c) => new THREE.Color(c).getHex();
const teamHex = (t) => (TEAMS[t] ? hex(TEAMS[t].color) : 0xffe14d);
const T = (x, y, z, rx = 0, ry = 0, rz = 0) => new THREE.Matrix4().compose(V(x, y, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz)), V(1, 1, 1));

// ------------------------------------------------------------ geometry kit
// pieces get merged into one geometry per material, so they all need the same attributes and no index
function prep(g) {
  const n = g.index ? g.toNonIndexed() : g;
  if (n !== g) g.dispose();
  for (const k of Object.keys(n.attributes)) if (k !== 'position' && k !== 'normal' && k !== 'uv') n.deleteAttribute(k);
  if (!n.attributes.uv) n.setAttribute('uv', new THREE.Float32BufferAttribute(new Float32Array(n.attributes.position.count * 2), 2));
  if (!n.attributes.normal) n.computeVertexNormals();
  n.clearGroups();
  return n;
}
// centred on itself (outline shells and gibs scale + spin round the middle); shared, so nobody disposes it
function centered(g) {
  g.computeBoundingBox();
  const c = g.boundingBox.getCenter(new THREE.Vector3());
  g.translate(-c.x, -c.y, -c.z);
  g.userData.shared = true; g.userData.at = c;
  return g;
}
class Parts { // pieces by material key
  constructor() { this.m = {}; }
  add(key, geo, mat4) { const g = prep(geo); if (mat4) g.applyMatrix4(mat4); (this.m[key] || (this.m[key] = [])).push(g); return this; }
  each(fn) { for (const list of Object.values(this.m)) for (const g of list) fn(g); return this; }
  into(P, mat4) { for (const [k, list] of Object.entries(this.m)) for (const g of list) P.add(k, mat4 ? g.applyMatrix4(mat4) : g); return P; }
  done() { const out = {}; for (const [k, list] of Object.entries(this.m)) { out[k] = centered(mergeGeometries(list)); for (const g of list) g.dispose(); } return out; }
}
const rbox = (w, h, d, r = 0.008) => new RoundedBoxGeometry(w, h, d, 1, Math.min(r, w / 2.2, h / 2.2, d / 2.2));
// bend round a vertical axis: the edges of something centred on x = 0 curve back by k * x^2 (z grows)
function bend(g, k) { const p = g.attributes.position; for (let i = 0; i < p.count; i++) p.setZ(i, p.getZ(i) + k * p.getX(i) ** 2); p.needsUpdate = true; return g; }
// quads between rings of points (rings stacked, points going round with the angle growing): faces point outwards
function loft(rings, keep = () => true, flip = false) {
  const pos = [], n = rings[0].length;
  for (let i = 0; i < rings.length - 1; i++) for (let j = 0; j < n; j++) {
    if (!keep(i, j)) continue;
    const a = rings[i][j], b = rings[i][(j + 1) % n], c = rings[i + 1][(j + 1) % n], d = rings[i + 1][j];
    for (const p of flip ? [a, c, b, a, d, c] : [a, b, c, a, c, d]) pos.push(p[0], p[1], p[2]);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.computeVertexNormals();
  return g;
}
// a squashed superellipse round the body: u = 0 at the back (+z), PI/2 right (+x), PI at the front (-z)
function ring(y, w, d, n, e = 2.4) {
  const out = [], k = 2 / e;
  for (let j = 0; j < n; j++) { const u = (j / n) * Math.PI * 2, s = Math.sin(u), c = Math.cos(u); out.push([Math.sign(s) * Math.abs(s) ** k * w, y, Math.sign(c) * Math.abs(c) ** k * d]); }
  return out;
}
// a solid band through rings: [outer skin, the rest (inner skin t further in, top + bottom edges)]. kept apart because
// the game's outline is a scaled back-face copy: an inward-facing skin in it would paint over the whole band
function band(rings, t) {
  const inner = rings.map((r) => r.map(([x, y, z]) => { const l = Math.hypot(x, z) || 1; return [x - (x / l) * t, y, z - (z / l) * t]; }));
  return [loft(rings), mergeGeometries([loft(inner, undefined, true), loft([inner[0], rings[0]]), loft([rings[rings.length - 1], inner[inner.length - 1]])].map(prep))];
}
// a plate's outline (centred, w x h): rounded bottom corners, shooter's cuts at the top (room for the arms), a scoop
// for the neck. depth along z, a little bevel so it catches the light
function plate(w, h, depth, cut = [0.06, 0.11], scoop = 0.022, bev = 0.006) {
  const s = new THREE.Shape(), x0 = -w / 2, x1 = w / 2, y0 = -h / 2, y1 = h / 2, r = 0.03, cw = cut[0], ch = cut[1];
  s.moveTo(x0 + r, y0);
  s.lineTo(x1 - r, y0); s.quadraticCurveTo(x1, y0, x1, y0 + r);
  s.lineTo(x1, y1 - ch); s.quadraticCurveTo(x1, y1 - ch + 0.012, x1 - 0.01, y1 - ch + 0.02);
  s.lineTo(x1 - cw + 0.008, y1 - 0.004); s.quadraticCurveTo(x1 - cw, y1, x1 - cw - 0.012, y1);
  s.quadraticCurveTo(0, y1 - scoop * 2, x0 + cw + 0.012, y1);
  s.quadraticCurveTo(x0 + cw, y1, x0 + cw - 0.008, y1 - 0.004);
  s.lineTo(x0 + 0.01, y1 - ch + 0.02); s.quadraticCurveTo(x0, y1 - ch + 0.012, x0, y1 - ch);
  s.lineTo(x0, y0 + r); s.quadraticCurveTo(x0, y0, x0 + r, y0);
  const g = new THREE.ExtrudeGeometry(s, { depth, bevelEnabled: true, bevelThickness: bev, bevelSize: bev, bevelSegments: 1, curveSegments: 5, steps: 1 });
  g.translate(0, 0, -depth / 2);
  return g;
}
// a strap through points: thin boxes end to end (width along x), so it bends over a shoulder
function strap(pts, w, t) {
  const out = [];
  for (let i = 0; i < pts.length - 1; i++) {
    const a = pts[i], b = pts[i + 1], len = Math.hypot(b[1] - a[1], b[2] - a[2]) + 0.006;
    const g = new THREE.BoxGeometry(w, t, len);
    g.applyMatrix4(T((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2, Math.atan2(-(b[1] - a[1]), b[2] - a[2]), 0, 0));
    out.push(prep(g));
  }
  return mergeGeometries(out);
}
// both sides lit (thin sheets and the inside of the bucket)
const mat2s = new Map();
function M2(color) {
  if (!mat2s.has(color)) mat2s.set(color, jankify(new THREE.MeshLambertMaterial({ color, flatShading: true, side: THREE.DoubleSide })));
  return mat2s.get(color);
}

// ------------------------------------------------------------ armor: what each top makes the torso
// the chest every top has is an egg (tees and hoodies a bigger one, jackets a box round it): its half width + depth at y
const CHEST = { tee: [0.258, 0.2365, 0.159], hoodie: [0.258, 0.2365, 0.159], jacket: [0.25, 0.229, 0.152], suit: [0.25, 0.229, 0.152], runner: [0.274, 0.25, 0.186] };
function torso(top, y) {
  const cut = topSize(top, y); // the top as clothes.js really cuts it (the numbers below: a top it doesn't make)
  if (cut) return cut;
  const c = CHEST[top] || [0.24, 0.22, 0.144], k = (y - 1.34) / c[1], f = Math.abs(k) < 1 ? Math.sqrt(1 - k * k) : 0;
  let w = c[0] * f, d = c[2] * f;
  if (y < 1.22) { const r = 0.1 + ((1.21 - Math.max(1.05, Math.min(1.21, y))) / 0.16) * 0.02; w = Math.max(w, r); d = Math.max(d, r); } // waist
  if (top === 'tank' && y > 1.07 && y < 1.55) d = Math.max(d, 0.158); // the sash stands off the chest
  if ((top === 'jacket' || top === 'suit') && y > 1.05 && y < 1.55) { w = Math.max(w, 0.252); d = Math.max(d, 0.178); } // boxy jacket panels
  if (top === 'runner' && y > 1.08 && y < 1.53) { w = Math.max(w, 0.262); d = Math.max(d, 0.18); } // the puffy bomber
  return [w, d];
}
const KNOWN_TOPS = new Set(['tank', 'none', 'tee', 'hoodie', 'jacket', 'suit', 'runner', 'lifetank', 'refshirt', 'robe', 'hotdog']);
// coyote tan carrier, darker pouches, near-black webbing; the team colour on the edges, shoulder pads, tabs and patches
const VC = { tan: 0x9b7d50, tan2: 0x7e6440, web: 0x3a3022 };

const vestCache = new Map();
// back: something covers the back (backpack / jetpack): no back plate under it
function vestGeo(top, back) {
  const key = top + '|' + back;
  if (vestCache.has(key)) return vestCache.get(key);
  if (!KNOWN_TOPS.has(top)) top = 'jacket'; // a top this file doesn't know yet: the roomiest fit
  let D = 0;
  for (let y = 1.12; y <= 1.47; y += 0.035) D = Math.max(D, torso(top, y)[1]);
  const P = new Parts(), th = 0.034, tilt = 0.075, k = 1.25, pw = 0.31, ph = 0.37, pcy = 1.305;
  const zf = D + 0.008 + th / 2; // plate centre, out from the body
  // ---- front: plate, team-coloured binding round it, three mag pouches (flaps + pull tabs), an admin pouch with a patch
  const F = new Parts();
  F.add('front', plate(pw, ph, th));
  F.add('trim', plate(pw + 0.018, ph + 0.016, th * 0.55, [0.064, 0.116], 0.022, 0.003), T(0, 0, 0.004));
  for (const x of [-0.084, 0, 0.084]) {
    F.add('tan2', rbox(0.072, 0.096, 0.044, 0.01), T(x, -0.12, -th / 2 - 0.02));
    F.add('front', rbox(0.076, 0.03, 0.05, 0.008), T(x, -0.075, -th / 2 - 0.024, -0.12));
    F.add('trim', new THREE.BoxGeometry(0.018, 0.02, 0.006), T(x, -0.094, -th / 2 - 0.05));
  }
  F.add('tan2', rbox(0.15, 0.064, 0.024, 0.008), T(0, 0.105, -th / 2 - 0.011));
  F.add('trim', new THREE.BoxGeometry(0.074, 0.042, 0.006), T(0.018, 0.106, -th / 2 - 0.025));
  for (const y of [-0.012, 0.03]) F.add('web', new THREE.BoxGeometry(0.27, 0.01, 0.006, 8, 1, 1), T(0, y, -th / 2 - 0.004));
  F.each((g) => bend(g, k));
  F.into(P, T(0, pcy, -zf, tilt, 0, 0)); // the top leans in a touch, like the chest under it
  // ---- back: plate + binding, a hydration pouch, molle rows, a team stripe and a drag handle
  if (!back) {
    const B = new Parts();
    const bh = top === 'hoodie' ? 0.34 : 0.38, bcy = top === 'hoodie' ? pcy - 0.02 : pcy + 0.005;
    B.add('back', plate(pw + 0.01, bh, th, [0.05, 0.08], 0.012));
    B.add('trim', plate(pw + 0.028, bh + 0.016, th * 0.55, [0.054, 0.084], 0.012, 0.003), T(0, 0, 0.004));
    B.add('tan2', rbox(0.2, 0.22, 0.03, 0.012), T(0, -0.045, -th / 2 - 0.014));
    for (const y of [-0.12, -0.08, -0.04, 0.0]) B.add('web', new THREE.BoxGeometry(0.205, 0.009, 0.005, 6, 1, 1), T(0, y, -th / 2 - 0.03));
    B.add('trim', new THREE.BoxGeometry(0.24, 0.03, 0.006, 6, 1, 1), T(0, 0.105, -th / 2 - 0.003));
    const handle = new THREE.TorusGeometry(0.03, 0.007, 4, 8, Math.PI);
    B.add('web', handle, T(0, bh / 2 - 0.035, -th / 2 - 0.006, 0, 0, 0));
    B.each((g) => bend(g, k * 0.8));
    B.into(P, T(0, bcy, zf, -tilt, Math.PI, 0));
  }
  // ---- cummerbund: wraps the sides from plate to plate, hugging the waist; two rows of webbing on it
  const cy = [1.12, 1.215, 1.31], cbD = D + 0.014, n = 28;
  const cw = (y) => Math.max(torso(top, y)[0] + 0.016, pw / 2 + 0.006);
  const [bOut, bIn] = band(cy.map((y) => ring(y, cw(y), cbD, n, 3.2)), 0.012);
  P.add('band', bOut); P.add('tanIn', bIn);
  const side = (i, j) => { const u = (j / n) * Math.PI * 2; return Math.abs(Math.cos(u)) < 0.62; };
  for (const y of [1.165, 1.255]) P.add('web', loft([ring(y - 0.005, cw(y) + 0.004, cbD + 0.004, n, 3.2), ring(y + 0.005, cw(y) + 0.004, cbD + 0.004, n, 3.2)], side));
  // ---- shoulder straps over the top, with team-coloured pads where they sit on the shoulder
  const c = CHEST[top] || [0.24, 0.22, 0.144], ys = Math.max(1.52, 1.34 + c[1] * Math.sqrt(1 - (0.128 / c[0]) ** 2) + 0.012), zt = zf - th / 2 - 0.006;
  for (const sx of [-1, 1]) {
    const x = sx * 0.128;
    const pts = [[sx * 0.112, 1.462, -zt], [x, ys - 0.035, -zt * 0.62], [x, ys - 0.008, -zt * 0.3], [x, ys, 0], [x, ys - 0.008, zt * 0.3], [x, ys - 0.035, zt * 0.62], [sx * 0.112, 1.462, zt]];
    P.add('tanIn', strap(pts, 0.056, 0.016));
    P.add('trim', rbox(0.062, 0.022, 0.13, 0.008), T(x, ys + 0.017, 0));
    P.add('web', new THREE.BoxGeometry(0.03, 0.012, 0.016), T(x, 1.47, -zt - 0.01)); // buckle where the strap meets the plate
  }
  // ---- a radio on the left hip with a whip antenna (reads at range), a small pouch on the right
  const wl = torso(top, 1.22)[0];
  P.add('tan2', rbox(0.052, 0.12, 0.066, 0.01), T(-(wl + 0.036), 1.215, 0.075, 0, 0, -0.04));
  P.add('web', new THREE.CylinderGeometry(0.0045, 0.006, 0.34, 4), T(-(wl + 0.046), 1.44, 0.11, 0.14, 0, 0.09)); // behind the shoulder
  P.add('web', new THREE.SphereGeometry(0.009, 4, 3), T(-(wl + 0.061), 1.608, 0.133));
  P.add('tan2', rbox(0.05, 0.075, 0.056, 0.01), T(wl + 0.036, 1.2, 0.07, 0, 0, 0.04));
  const out = P.done();
  vestCache.set(key, out);
  return out;
}

// the bucket: a galvanised pail upside down, rolled lip, two ribs, a team band, the handle hangs under the chin as the
// chin strap (with its wooden grip). sized for the hair under it: rim radius, extra height, rim height, z offset
const HAIR_FIT = {
  none: [0.158, 0, 0.205], short: [0.166, 0, 0.205], bowl: [0.172, 0.006, 0.212], spiky: [0.166, 0.03, 0.205],
  mohawk: [0.184, 0.1, 0.2, 0.006], long: [0.17, 0, 0.205], ponytail: [0.17, 0, 0.205], bun: [0.166, 0.05, 0.205], afro: [0.238, 0.05, 0.19, 0.03],
};
const BK = { metal: 0xaab5bd, wire: 0x2b2d31 };
const bucketCache = new Map();
function bucketGeo(hair) {
  const fit = HAIR_FIT[hair] || HAIR_FIT.short;
  if (bucketCache.has(fit)) return bucketCache.get(fit);
  const [R, xh] = fit, H = 0.158 + xh, rt = R * 0.8, t = 0.008;
  const rAt = (y) => R + (rt - R) * (y / H);
  const v2 = (pts) => pts.map(([r, y]) => new THREE.Vector2(r, y));
  const outer = [[R - t, -0.002], [R + 0.004, -0.004], [R + 0.013, 0.004], [R + 0.013, 0.016], [R + 0.003, 0.024]];
  for (const [y, b] of [[0.04, 0], [H * 0.3, 0], [H * 0.34, 0.007], [H * 0.38, 0], [H * 0.68, 0], [H * 0.72, 0.007], [H * 0.76, 0], [H - 0.008, 0]]) outer.push([rAt(y) + b, y]);
  outer.push([rt - 0.008, H + 0.002], [rt * 0.55, H + 0.008], [0.001, H + 0.01]);
  const inner = [[0.001, H - t], [rt - t, H - t], [R - t - 0.002, 0.03], [R - t, -0.002]];
  const P = new Parts();
  P.add('metal', new THREE.LatheGeometry(v2(outer.slice(4)), 18));
  P.add('metal', new THREE.LatheGeometry(v2(outer.slice(0, 5)), 18));
  P.add('metalIn', new THREE.LatheGeometry(v2(inner), 18));
  P.add('trim', new THREE.LatheGeometry(v2([[rAt(H * 0.42) + 0.003, H * 0.42], [rAt(H * 0.64) + 0.003, H * 0.64]]), 18));
  P.add('trim', new THREE.LatheGeometry(v2([[rAt(H * 0.64) + 0.003, H * 0.64], [rAt(H * 0.64) + 0.0005, H * 0.645]]), 18));
  P.add('trim', new THREE.LatheGeometry(v2([[rAt(H * 0.415) + 0.0005, H * 0.415], [rAt(H * 0.42) + 0.003, H * 0.42]]), 18));
  // the handle: lugs on both sides, a wire down round the jaw, a wooden grip under the chin
  for (const sx of [-1, 1]) P.add('wire', rbox(0.012, 0.03, 0.022, 0.004), T(sx * (R + 0.006), 0.05, 0));
  const bail = new THREE.CatmullRomCurve3([[-R - 0.008, 0.05, 0], [-R * 0.96, -0.05, -0.035], [-R * 0.66, -0.14, -0.095], [0, -0.175, -0.125], [R * 0.66, -0.14, -0.095], [R * 0.96, -0.05, -0.035], [R + 0.008, 0.05, 0]].map((p) => V(...p)));
  P.add('wire', new THREE.TubeGeometry(bail, 20, 0.0042, 4, false));
  const grip = new THREE.CylinderGeometry(0.011, 0.011, 0.07, 6); grip.rotateZ(Math.PI / 2);
  P.add('wire', grip, T(0, -0.171, -0.122));
  const out = P.done();
  bucketCache.set(fit, out);
  return out;
}

// defuse pliers in a pouch on the hip: olive pouch + flap, red dipped handles sticking out
let kitG = null;
function kitGeo() {
  if (kitG) return kitG;
  const P = new Parts();
  P.add('olive', rbox(0.07, 0.085, 0.05, 0.01), T(0, 0, 0));
  P.add('olive', rbox(0.074, 0.022, 0.056, 0.006), T(0, 0.036, -0.002, -0.2));
  for (const sx of [-1, 1]) P.add('red', rbox(0.013, 0.075, 0.013, 0.005), T(sx * 0.012, 0.078, 0.008, 0.08, 0, sx * -0.16));
  P.add('red', rbox(0.028, 0.026, 0.012, 0.004), T(0, 0.12, 0.012));
  kitG = P.done();
  return kitG;
}
const KC = { olive: 0x56603a, red: 0xd02a2a };

// Remote.build: the look to build with (a hat comes off under the bucket)
export function gearLook(look, bits) { return bits & 2 ? { ...(look || {}), head: 'none' } : look; }
// Remote.build: put the armor on a freshly built character (before its outline shells are made)
export function dressGear(ch, bits, look, team) {
  const lk = look || {}, col = teamHex(team);
  // small bits sit inside a bigger piece's outline already: no outline shell of their own (fewer draw calls)
  const add = (parent, geo, mat, noShell) => { const m = new THREE.Mesh(geo, mat); m.position.copy(geo.userData.at); m.userData.gear = true; if (noShell) m.userData.noShell = true; parent.add(m); return m; };
  if (bits & 1) {
    const covered = lk.back === 'backpack' || lk.back === 'jetpack';
    const g = vestGeo(lk.top || 'tank', covered);
    for (const k of ['front', 'back', 'band']) if (g[k]) add(ch.body, g[k], M(VC.tan)); // closed outer shapes: outlined
    add(ch.body, g.tanIn, M(VC.tan), true); add(ch.body, g.tan2, M(VC.tan2), true); add(ch.body, g.web, M(VC.web), true); add(ch.body, g.trim, M(col), true);
    // a cape or wings hang off the vest's back, not through it
    if (ch.cape) { ch.cape.position.z += 0.05; ch.cape.position.y += 0.012; }
    if (ch.wings) for (const w of ch.wings) w.position.z += 0.05;
  }
  if (bits & 2) {
    const fit = HAIR_FIT[lk.hair] || HAIR_FIT.short, g = bucketGeo(lk.hair);
    const b = new THREE.Group();
    b.position.set(0, fit[2], fit[3] || 0.012);
    b.rotation.set(lk.hair === 'mohawk' ? 0.08 : 0.17, 0, 0); // pushed back so the face shows (a mohawk needs it straighter)
    add(b, g.metal, M(BK.metal)); add(b, g.metalIn, M(BK.metal), true); add(b, g.trim, M(col), true); add(b, g.wire, M(BK.wire), true);
    ch.head.add(b);
    ch.bucket = b;
  }
  if (bits & 4) {
    const g = kitGeo(), k = new THREE.Group();
    k.position.set(lk.bottom === 'skirt' ? 0.232 : 0.205, 1.0, -0.035);
    k.rotation.set(0, -0.35, 0.06);
    add(k, g.olive, M(KC.olive)); add(k, g.red, M(KC.red), true);
    ch.body.add(k);
  }
}

// ------------------------------------------------------------ gear on the floor
const drops = new Map(); // id -> entry
const tmpQ = new THREE.Quaternion(), tmpE = new THREE.Euler(), tmpV = new THREE.Vector3(), tmpBox = new THREE.Box3();
const UP = V(0, 1, 0);
const SHADOW_TEX = (() => {
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const x = c.getContext('2d'), g = x.createRadialGradient(32, 32, 2, 32, 32, 31);
  g.addColorStop(0, 'rgba(0,0,0,0.6)'); g.addColorStop(0.55, 'rgba(0,0,0,0.32)'); g.addColorStop(1, 'rgba(0,0,0,0)');
  x.fillStyle = g; x.fillRect(0, 0, 64, 64);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  return t;
})();
const RING_TEX = (() => {
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const x = c.getContext('2d'), g = x.createRadialGradient(32, 32, 14, 32, 32, 31);
  g.addColorStop(0, 'rgba(255,240,170,0)'); g.addColorStop(0.55, 'rgba(255,240,170,0.9)'); g.addColorStop(0.75, 'rgba(255,255,255,0.5)'); g.addColorStop(1, 'rgba(255,240,170,0)');
  x.fillStyle = g; x.fillRect(0, 0, 64, 64);
  return new THREE.CanvasTexture(c);
})();
const FLAT = new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2);
// things on the floor are as big as they are in someone's hands (third-person scale x the bigger players)
const WSCALE = (id) => (id === 'bread' ? 1.0 : 1.5) * 1.2;

function itemModel(id, n) {
  const g = new THREE.Group();
  const one = () => {
    if (id === 'frag') return buildProjectile('frag');
    if (id === 'smoke') return buildProjectile('smokegren');
    if (id === 'duck') { const d = buildProjectile('duck'); d.scale.setScalar(0.75); return d; }
    const m = new THREE.Group();
    if (id === 'medkit') { // white case, red cross on the lid, a handle on the side
      m.add(new THREE.Mesh(rbox(0.26, 0.13, 0.2, 0.022), M(0xf2f2f2)));
      const cr = M(0xe02828);
      for (const [w, d] of [[0.12, 0.036], [0.036, 0.12]]) { const a = new THREE.Mesh(new THREE.BoxGeometry(w, 0.008, d), cr); a.position.y = 0.066; m.add(a); }
      const h = new THREE.Mesh(new THREE.TorusGeometry(0.035, 0.01, 4, 8, Math.PI), M(0x444444)); h.position.set(0, 0, -0.1); h.rotation.x = -Math.PI / 2; m.add(h);
    } else if (id === 'bubble') {
      m.add(new THREE.Mesh(new THREE.IcosahedronGeometry(0.11, 1), new THREE.MeshLambertMaterial({ color: 0x4fd8ff, transparent: true, opacity: 0.55, emissive: 0x0a3a50 })));
      m.add(new THREE.Mesh(new THREE.IcosahedronGeometry(0.05, 0), M(0xffffff, true)));
    } else {
      const c = ITEMS[id] ? hex(ITEMS[id].color || '#cccccc') : 0xcccccc;
      m.add(new THREE.Mesh(rbox(0.16, 0.12, 0.16, 0.02), M(c)));
    }
    return m;
  };
  const k = Math.min(3, Math.max(1, n || 1));
  for (let i = 0; i < k; i++) { const m = one(); m.position.x = (i - (k - 1) / 2) * 0.24; g.add(m); }
  return g;
}
function kitModel() {
  const g = kitGeo(), k = new THREE.Group();
  for (const [key, c] of Object.entries(KC)) { const m = new THREE.Mesh(g[key], M(c)); m.position.copy(g[key].userData.at); k.add(m); }
  k.scale.setScalar(1.6);
  return k;
}
function dropModel(d) {
  if (d.k === 'w') {
    const g = buildWeapon(d.w, Array.isArray(d.sk) ? d.sk : undefined);
    if (d.w === 'katana') setKatana(g, d.kat || 0);
    g.scale.setScalar(WSCALE(d.w));
    return { g, flat: true };
  }
  if (d.k === 'i') return { g: itemModel(d.w, d.n), flat: d.w === 'frag' || d.w === 'smoke' };
  return { g: kitModel(), flat: false };
}
// the 8 corners of what it looks like, in its own space: the lowest one (for any rotation) sits on the floor
function cornersOf(obj) {
  obj.updateMatrixWorld(true);
  const inv = new THREE.Matrix4().copy(obj.matrixWorld).invert(), box = new THREE.Box3(), m = new THREE.Matrix4();
  obj.traverse((o) => {
    if (!o.isMesh) return;
    o.geometry.computeBoundingBox();
    box.union(tmpBox.copy(o.geometry.boundingBox).applyMatrix4(m.multiplyMatrices(inv, o.matrixWorld)));
  });
  const out = [];
  for (let i = 0; i < 8; i++) out.push(V(i & 1 ? box.max.x : box.min.x, i & 2 ? box.max.y : box.min.y, i & 4 ? box.max.z : box.min.z));
  return { out, box };
}
function lowest(e, q) { let lo = Infinity; for (const c of e.corners) { tmpV.copy(c).multiply(e.inner.scale).applyQuaternion(q); lo = Math.min(lo, tmpV.y); } return lo; }
function floorUnder(p) {
  const h = raycast([p[0], p[1] + 0.4, p[2]], [0, -1, 0], 3, BOXES);
  return h ? h.point[1] : p[1] - 0.15;
}

// from: where it left (a hand, a body), or null when it was already lying there (you just joined)
export function dropAdd(d, from) {
  dropRemove(d.id, 0, true);
  const { g, flat } = dropModel(d);
  const root = new THREE.Group(), inner = new THREE.Group();
  inner.add(g);
  inner.scale.copy(g.scale); g.scale.setScalar(1);
  root.add(inner);
  const { out: corners, box } = cornersOf(g);
  // lying on its side, pointing anywhere: a gun shows its profile, never stands on its muzzle
  const yaw = Math.random() * Math.PI * 2, side = Math.random() < 0.5 ? 1 : -1;
  const qRest = new THREE.Quaternion().setFromEuler(tmpE.set(0, yaw, 0, 'YXZ')).multiply(new THREE.Quaternion().setFromEuler(tmpE.set(0, 0, flat ? side * Math.PI / 2 : 0)));
  const e = { d, root, inner, g, corners, box, qRest, floor: floorUnder(d.p), born: performance.now(), hi: 0, mats: null };
  e.restY = e.floor - lowest(e, qRest) + 0.004; // a hair above the floor: lying on it, never in it
  e.rest = V(d.p[0], e.restY, d.p[2]);
  // the shadow it casts on the floor: as big as what's lying there
  const sz = box.getSize(new THREE.Vector3()).multiply(inner.scale);
  const foot = flat ? [sz.y, sz.z] : [Math.max(sz.x, sz.z), Math.max(sz.x, sz.z)];
  e.shadow = new THREE.Mesh(FLAT, new THREE.MeshBasicMaterial({ map: SHADOW_TEX, transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2, opacity: 0 }));
  e.shadow.scale.set(Math.max(0.3, foot[0] * 1.25), 1, Math.max(0.3, foot[1] * 1.15));
  e.shadow.rotation.y = yaw;
  e.shadow.position.set(d.p[0], e.floor + 0.006, d.p[2]);
  e.shadow.renderOrder = 1;
  e.ring = new THREE.Mesh(FLAT, new THREE.MeshBasicMaterial({ map: RING_TEX, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, polygonOffset: true, polygonOffsetFactor: -3, polygonOffsetUnits: -3, opacity: 0 }));
  e.ring.position.set(d.p[0], e.floor + 0.008, d.p[2]);
  e.ring.renderOrder = 2;
  e.ring.visible = false;
  const r0 = Math.max(0.55, Math.max(foot[0], foot[1]) * 0.8);
  e.ring.scale.set(r0 * 1.6, 1, r0 * 1.6);
  G.scene.add(root, e.shadow, e.ring);
  if (from) {
    // thrown: from the hand in an arc, tumbling, one bounce, then it settles flat
    const s = V(...from), dist = Math.hypot(e.rest.x - s.x, e.rest.z - s.z);
    const t = e.flight = 0.34 + Math.min(0.3, dist * 0.08);
    e.pos = s.clone();
    e.vel = V((e.rest.x - s.x) / t * 0.86, 0, (e.rest.z - s.z) / t * 0.86);
    e.vel.y = (e.restY - s.y + 13 * t * t) / t; // lands at the rest height after t
    e.q = new THREE.Quaternion().setFromEuler(tmpE.set(Math.random() * 6, yaw + 1.2, Math.random() * 6));
    e.spin = V((Math.random() - 0.5) * 14, (Math.random() - 0.5) * 8, (Math.random() - 0.5) * 14);
    e.bounces = 0; e.settle = 0; e.state = 'fly';
  } else { e.pos = e.rest.clone(); e.q = qRest.clone(); e.state = 'rest'; e.shadow.material.opacity = 1; }
  place(e);
  drops.set(d.id, e);
  return e;
}
function place(e) { e.root.position.copy(e.pos); e.inner.quaternion.copy(e.q); }
// a pile of item charges got smaller (or anything else about it changed): rebuild its model where it lies
export function dropUpdate(d) {
  const e = drops.get(d.id);
  if (!e) return dropAdd(d, null);
  if (e.d.k === 'i' && e.d.n !== d.n) return dropAdd(d, null);
  e.d = d;
  return e;
}
export function dropRemove(id, picker, quiet) {
  const e = drops.get(id);
  if (!e) return;
  drops.delete(id);
  unlight(e);
  G.scene.remove(e.root, e.shadow, e.ring);
  freeTree(e.root);
  e.shadow.material.dispose(); e.ring.material.dispose();
  if (!quiet && picker) fx.spray([e.pos.x, e.pos.y + 0.1, e.pos.z], 7, [0xffffff, 0xffe14d], 2.2, 0.35, 0.07, 3, 2);
}
export function dropsClear() { for (const id of [...drops.keys()]) dropRemove(id, 0, true); }
export const dropList = () => drops.values();
export const dropEntry = (id) => drops.get(id);

// highlight = the materials glow a little (own copies while it's the one you'd pick up) + a ring on the floor
function light(e) {
  if (e.mats) return;
  e.mats = [];
  e.g.traverse((o) => {
    if (!o.isMesh) return;
    const was = o.material, arr = Array.isArray(was) ? was : [was];
    const now = arr.map((m) => { if (!m || !m.emissive) return m; const c = jankify(m.clone()); c.userData.glow = true; return c; });
    e.mats.push([o, was, now]);
    o.material = Array.isArray(was) ? now : now[0];
  });
}
function unlight(e) {
  if (!e.mats) return;
  for (const [o, was, now] of e.mats) { o.material = was; for (const m of now) if (m && m.userData.glow) m.dispose(); }
  e.mats = null;
}
const GRAV = 26;
export function dropsTick(dt, now, targetId) {
  for (const e of drops.values()) {
    if (e.state === 'fly') {
      e.vel.y -= GRAV * dt;
      e.pos.addScaledVector(e.vel, dt);
      const sp = e.spin.length();
      if (sp > 0.01) e.q.premultiply(tmpQ.setFromAxisAngle(tmpV.copy(e.spin).divideScalar(sp), sp * dt));
      // never through the floor: whatever corner is lowest right now rests on it
      const lo = e.floor - lowest(e, e.q) + 0.004;
      if (e.pos.y <= lo && e.vel.y < 0) {
        e.pos.y = lo;
        if (e.bounces++ < 1 && e.vel.y < -3) {
          e.vel.y *= -0.28; e.vel.x *= 0.45; e.vel.z *= 0.45; e.spin.multiplyScalar(0.4);
          fx.dust([e.pos.x, e.floor, e.pos.z], 3);
          if (e.onLand) e.onLand(e, 1);
        } else { e.state = 'settle'; e.settle = 0; e.from = e.pos.clone(); e.q0 = e.q.clone(); if (e.onLand) e.onLand(e, 2); }
      }
      // it'll come to rest where the server put it: pull it in as it goes
      e.pos.x += (e.rest.x - e.pos.x) * Math.min(1, dt * 2.2); e.pos.z += (e.rest.z - e.pos.z) * Math.min(1, dt * 2.2);
      if (now - e.born > 2500) { e.state = 'settle'; e.settle = 0; e.from = e.pos.clone(); e.q0 = e.q.clone(); }
    } else if (e.state === 'settle') {
      // rocks over onto its side and slides the last bit: eased, with the lowest corner held on the floor
      e.settle = Math.min(1, e.settle + dt / 0.2);
      const u = e.settle, k = u * u * (3 - 2 * u);
      e.q.slerpQuaternions(e.q0, e.qRest, k);
      e.pos.lerpVectors(e.from, e.rest, k);
      e.pos.y = Math.max(e.pos.y, e.floor - lowest(e, e.q) + 0.004);
      if (u >= 1) { e.state = 'rest'; e.pos.copy(e.rest); e.q.copy(e.qRest); }
    }
    if (e.state !== 'rest' || e.shadow.material.opacity < 1) {
      const h = Math.max(0, e.pos.y - e.restY);
      e.shadow.material.opacity = Math.max(0.15, 1 - h * 1.2);
      e.shadow.position.x = e.pos.x; e.shadow.position.z = e.pos.z;
      place(e);
    }
    // the one you'd pick up glows and gets a ring
    const on = e.d.id === targetId;
    e.hi += ((on ? 1 : 0) - e.hi) * Math.min(1, dt * 10);
    if (on) light(e);
    else if (e.hi < 0.02) unlight(e);
    if (e.mats) {
      const pulse = e.hi * (0.22 + Math.sin(now * 0.008) * 0.08);
      for (const [, , ms] of e.mats) for (const m of ms) if (m && m.userData.glow) m.emissive.setRGB(pulse * 1.1, pulse, pulse * 0.7);
    }
    e.ring.visible = e.hi > 0.02;
    if (e.ring.visible) { e.ring.material.opacity = e.hi * (0.55 + Math.sin(now * 0.008) * 0.2); e.ring.rotation.y += dt * 0.6; e.ring.position.x = e.pos.x; e.ring.position.z = e.pos.z; }
    if (e.state === 'rest' && e.g.userData.effect && e.g.userData.effect !== 'none') { e.root.updateMatrixWorld(true); emitSkinFx(G.skinFxWorld, e.g, dt * 0.5, 1.2); }
  }
}

// ------------------------------------------------------------ spawn barriers
// each side's zone: four walls in the team colour, hazard stripes sliding along, the countdown printed on them
let walls = null;
const wallTex = new Map(); // colour -> { canvas, tex }
function wallTexture(color) {
  let w = wallTex.get(color);
  if (w) return w;
  const c = document.createElement('canvas'); c.width = 256; c.height = 384;
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = THREE.RepeatWrapping; tex.colorSpace = THREE.SRGBColorSpace; tex.magFilter = THREE.NearestFilter; tex.minFilter = THREE.LinearFilter; tex.generateMipmaps = false;
  w = { c, tex, label: null, color };
  wallTex.set(color, w);
  return w;
}
// 32 px a metre, 12 m tall: the floor is 2 m up from the bottom (zones start 2 m under the lowest spawn)
function paintWall(w, label) {
  if (w.label === label) return;
  w.label = label;
  const x = w.c.getContext('2d'), W2 = 256, H = 384, fy = H - 64, col = w.color;
  x.clearRect(0, 0, W2, H);
  const g = x.createLinearGradient(0, fy - 170, 0, fy + 8);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(0.6, col + '26'); g.addColorStop(1, col + '70');
  x.fillStyle = g; x.fillRect(0, fy - 170, W2, 178);
  // hazard stripes in the band you walk into
  x.save(); x.beginPath(); x.rect(0, fy - 46, W2, 46); x.clip();
  x.globalAlpha = 0.4; x.fillStyle = col;
  for (let i = -4; i < 22; i++) { x.beginPath(); x.moveTo(i * 16, fy); x.lineTo(i * 16 + 8, fy); x.lineTo(i * 16 + 54, fy - 46); x.lineTo(i * 16 + 46, fy - 46); x.fill(); }
  x.restore();
  x.fillStyle = col; x.globalAlpha = 0.95; x.fillRect(0, fy - 48, W2, 2); x.fillRect(0, fy - 3, W2, 5);
  // the label on a dark strip at eye height, once every 8 m
  x.globalAlpha = 1;
  x.font = 'bold 11px "Comic Sans MS", "Comic Neue", cursive'; x.textAlign = 'center'; x.textBaseline = 'middle';
  const tw = x.measureText(label).width + 14, ly = fy - 50 - 12;
  x.fillStyle = 'rgba(10,0,20,0.72)'; x.fillRect(128 - tw / 2, ly - 8, tw, 16);
  x.fillStyle = col; x.fillRect(128 - tw / 2, ly + 7, tw, 2);
  x.fillStyle = '#ffffff'; x.fillText(label, 128, ly + 1);
  x.clearRect(0, fy + 2, W2, H - fy - 2); // nothing under the floor line
  w.tex.needsUpdate = true;
}
const fmt = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
// zones: [{ z: {min, max}, team }]
export function barriersSet(zones) {
  barriersClear();
  if (!zones.length) return;
  const group = new THREE.Group(), mats = [];
  for (const { z, team } of zones) {
    const w = wallTexture(TEAMS[team] ? TEAMS[team].color : '#ffe14d');
    paintWall(w, 'BUY PHASE');
    const h = z.max[1] - z.min[1], sx = z.max[0] - z.min[0], sz = z.max[2] - z.min[2], cx = (z.min[0] + z.max[0]) / 2, cz = (z.min[2] + z.max[2]) / 2, cy = (z.min[1] + z.max[1]) / 2;
    for (const [len, x, zz, ry] of [[sx, cx, z.min[2], 0], [sx, cx, z.max[2], Math.PI], [sz, z.min[0], cz, Math.PI / 2], [sz, z.max[0], cz, -Math.PI / 2]]) {
      const tex = w.tex.clone(); tex.repeat.set(Math.max(1, Math.round(len / 8)), 1); tex.needsUpdate = true;
      const m = new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, side: THREE.DoubleSide, opacity: 0 });
      const mesh = new THREE.Mesh(new THREE.PlaneGeometry(len, h), m);
      mesh.position.set(x, cy, zz); mesh.rotation.y = ry;
      mesh.renderOrder = 3;
      group.add(mesh);
      mats.push({ m, tex, w, base: [x, z.min[1] + 2, zz], len, ry });
    }
  }
  G.scene.add(group);
  walls = { group, mats, born: performance.now(), drop: 0 };
}
export function barriersDrop() {
  if (!walls || walls.drop) return;
  walls.drop = performance.now();
  // sparks along the foot of every wall as it goes
  for (const { base, len, ry } of walls.mats) {
    const dx = Math.cos(ry), dz = -Math.sin(ry);
    for (let i = 0; i < 6; i++) { const t = (Math.random() - 0.5) * len; fx.spray([base[0] + dx * t, base[1] + 0.1, base[2] + dz * t], 3, [0xffffff, 0xffe14d], 3, 0.5, 0.08, 6, 1); }
  }
}
export function barriersClear() {
  if (!walls) return;
  G.scene.remove(walls.group);
  for (const { m, tex } of walls.mats) { m.dispose(); tex.dispose(); }
  walls.group.traverse((o) => { if (o.geometry) o.geometry.dispose(); });
  walls = null;
}
export function barriersTick(dt, now, left) {
  if (!walls) return;
  const label = walls.drop ? 'GO GO GO' : left > 0 ? `BUY PHASE ${fmt(Math.ceil(left / 1000))}` : 'BUY PHASE';
  const seen = new Set();
  for (const w of walls.mats) {
    if (!seen.has(w.w)) { seen.add(w.w); paintWall(w.w, label); }
    w.tex.offset.x = (now * 0.00006) % 1;
    if (w.w.tex.version !== w.v) { w.v = w.w.tex.version; w.tex.needsUpdate = true; }
  }
  const fadeIn = Math.min(1, (now - walls.born) / 350);
  if (!walls.drop) { for (const w of walls.mats) w.m.opacity = fadeIn * (0.85 + Math.sin(now * 0.004) * 0.08); return; }
  // dropping: a flash, then the walls sink into the floor and fade out
  const k = Math.min(1, (now - walls.drop) / 700);
  walls.group.position.y = -k * k * 3.2;
  for (const w of walls.mats) w.m.opacity = (1 - k) * (k < 0.15 ? 1.4 : 1);
  if (k >= 1) barriersClear();
}
export const barriersUp = () => !!walls && !walls.drop;

// ------------------------------------------------------------ gear pictures for the buy menu
// a mannequin from the waist up in the gear (team trim in your colour), or the pliers pouch
// the gear on its own, like an inventory picture: the vest from the front three-quarters (the bucket over it)
export function gearModel(id, team) {
  const g = new THREE.Group(), col = teamHex(team);
  const add = (geo, mat, p) => { const m = new THREE.Mesh(geo, mat); m.position.copy(geo.userData.at); p.add(m); };
  if (id === 'kit') { const k = kitModel(); k.rotation.set(0.25, Math.PI - 0.7, 0.1); g.add(k); return g; }
  const v = vestGeo('tee', false);
  for (const k of ['front', 'back', 'band', 'tanIn']) add(v[k], M(VC.tan), g);
  add(v.tan2, M(VC.tan2), g); add(v.web, M(VC.web), g); add(v.trim, M(col), g);
  if (id === 'helm') {
    const b = bucketGeo('short'), h = new THREE.Group();
    for (const [k, c] of [['metal', BK.metal], ['metalIn', BK.metal], ['trim', col], ['wire', BK.wire]]) add(b[k], M(c), h);
    h.position.set(0.16, 1.74, -0.05); h.rotation.set(0.25, 0.4, -0.18);
    g.add(h);
  }
  g.rotation.set(0.18, Math.PI - 0.62, 0);
  return g;
}

// ------------------------------------------------------------ first person: buy, pick up, toss
const K = (t, p = [0, 0, 0], r = [0, 0, 0], e = 'smooth', s = 1) => ({ t, p, r, e, s });
Object.assign(ANIMS, {
  // fresh from the shop: comes up from under the screen with a flip and lands in the hand with a little bounce
  econ_buy: { keys: [K(0, [0.06, -0.36, 0.1], [-1.1, 0.7, 0.5]), K(0.2, [0.02, 0.04, 0.02], [0.18, -0.12, -0.12], 'snap'), K(0.32, [0, -0.012, 0], [-0.06, 0.03, 0.03]), K(0.46)] },
  // grabbed off the floor: swings up from low left, twists into the grip, settles
  econ_grab: { keys: [K(0, [-0.2, -0.32, 0.06], [0.5, -0.9, 0.7]), K(0.17, [0.015, 0.02, 0.01], [-0.12, 0.1, -0.08], 'snap'), K(0.3, [0, -0.008, 0], [0.04, -0.02, 0.02]), K(0.42)] },
  // tossed away: a short wind-up, then out and down past the bottom of the screen (held there till the next one draws)
  econ_toss: { keys: [K(0), K(0.07, [0.02, 0.03, 0.04], [0.28, 0.05, -0.12]), K(0.25, [-0.12, -0.42, -0.42], [-1.15, 0.35, 0.9], 'in'), K(0.6, [-0.12, -0.42, -0.42], [-1.15, 0.35, 0.9])] },
  // gear on: the gun dips while you strap the vest / pull the bucket down
  econ_strap: { keys: [K(0), K(0.12, [-0.03, -0.09, 0.03], [0.32, 0.1, 0.2]), K(0.3, [-0.02, -0.07, 0.02], [0.26, 0.08, 0.16]), K(0.42, [0, 0.006, 0], [-0.04, 0, 0], 'snap'), K(0.56)] },
});
for (const id of ['econ_buy', 'econ_grab', 'econ_toss', 'econ_strap']) ANIMS[id].dur = ANIMS[id].keys[ANIMS[id].keys.length - 1].t;
