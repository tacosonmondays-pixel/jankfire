// JANKFIRE clothes: the tops and bottoms on the mannequin (models.js buildCharacter calls wearTop / wearBottom).
// Each garment is cut for the body it goes on: the build and the body sliders give a body (fitOf), a garment is rows of
// [height, half width, front depth, back depth] round it (a shell), and its collar, pockets, zip and seams are laid on
// that shell, so nothing floats off a big belly or sinks into one. A piece is one mesh (+ one for its small trim): its
// colours come from a tiny palette texture (the garment's own colour in a few tones + fixed colours), so a jacket is
// seven meshes, not twenty. Shapes are built once per garment + body and shared. Looks only: the server's hitboxes
// never hear of this.
import * as THREE from 'three';
import { jankify } from './jank.js';
import { BUILDS, JOKE, JOKE_MAX } from '/shared/looks.js';

const PI = Math.PI, TAU = PI * 2, DEG = PI / 180;
const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const T = (x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0, sx = 1, sy = sx, sz = sx) => new THREE.Matrix4().compose(V3(x, y, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz)), V3(sx, sy, sz));
const mix = (a, b, t) => a + (b - a) * t, cl01 = (t) => Math.max(0, Math.min(1, t));

// ------------------------------------------------------------ palette: one tiny texture per garment colour
// cells 0-9 come from the garment's own colour (so seams, hems and folds follow whatever you pick); the rest are fixed
const PW = 48;
const C = { base: 0, panel: 1, seam: 2, deep: 3, light: 4, hi: 5, btn: 6, pop: 7, mark: 8, sauce: 9 };
const FIXED = { white: 0xf2f1ec, cream: 0xe2dccb, ink: 0x1c1c21, coal: 0x34343c, silver: 0xc6ccd4, steel: 0x70767f, brass: 0xffc21a, red: 0xc02030, redd: 0x8a1422,
  pink: 0xff4fd8, rose: 0xff9ad5, tan: 0xd9a35b, tee: 0x2b2b31, frill: 0xffffff, pencil: 0xffd21a, eraser: 0xff7ab8, sole: 0x3a2412, shoe: 0x15121a,
  bun: 0xe3ad62, crust: 0xb9783a, bunm: 0xcf9550, crumb: 0xf4dfa8, tape: 0xe9d49a, straw: 0xe8c66a, strawd: 0xc39a45, card: 0xc8a070, cardd: 0xa07c4c, buoy: 0xf03a2a };
Object.keys(FIXED).forEach((k, i) => { C[k] = 10 + i; });
const TONES = [1, 0.87, 0.72, 0.5, 1.13, 1.3, 0.42]; // base, panel, seam, deep shadow, light, highlight, buttons
function tone(hex, k, flip) { // in screen (sRGB) values: k < 1 darker, > 1 paler
  const c = [(hex >> 16) & 255, (hex >> 8) & 255, hex & 255];
  if (flip && k < 1 && Math.max(...c) < 64) k = 1 + (1 - k) * 0.85; // near-black cloth can't go darker: its panels and seams go paler instead
  if (flip && k > 1 && Math.min(...c) > 190) k = 1 - (k - 1) * 0.9; // ...and near-white cloth's pale bits go darker
  return c.map((v) => (k <= 1 ? v * k : v + (255 - v) * (k - 1) * 0.8));
}
const pals = new Map(), mats = new Map();
function palette(col) {
  if (pals.has(col)) return pals.get(col);
  const d = new Uint8Array(PW * 4).fill(255), put = (i, c) => { d[i * 4] = c[0]; d[i * 4 + 1] = c[1]; d[i * 4 + 2] = c[2]; };
  TONES.forEach((k, i) => put(i, tone(col, k, i !== 0 && i !== 3)));
  // the accent (linings, pull tabs): hot pink, or yellow on anything already pink / red
  const hsl = new THREE.Color(col).getHSL({}), pop = (hsl.h > 0.78 || hsl.h < 0.05) && hsl.s > 0.35 ? 0xffe14d : 0xff4fd8;
  put(C.pop, tone(pop, 1)); put(C.mark, tone(Math.max((col >> 16) & 255, (col >> 8) & 255, col & 255) < 110 ? pop : col, 1)); // mark: the garment's colour where it has to show on black (a dark one: the accent)
  put(C.sauce, tone(hsl.h > 0.1 && hsl.h < 0.2 && hsl.s > 0.4 && hsl.l > 0.4 ? 0xd0241c : 0xffd21a, 1)); // mustard (ketchup on anything already yellow)
  for (const k of Object.keys(FIXED)) put(C[k], tone(FIXED[k], 1));
  const t = new THREE.DataTexture(d, PW, 1, THREE.RGBAFormat);
  t.colorSpace = THREE.SRGBColorSpace; t.magFilter = t.minFilter = THREE.NearestFilter; t.generateMipmaps = false; t.needsUpdate = true;
  pals.set(col, t);
  return t;
}
// both faces (cloth is thin sheets, and gibs flip over). the palette is the emissive map too: other players glow a
// little in their own colours (remote.js), and a plain emissive would wash the black bits grey
function cloth(col) {
  if (!mats.has(col)) { const t = palette(col); mats.set(col, jankify(new THREE.MeshLambertMaterial({ map: t, emissiveMap: t, flatShading: true, side: THREE.DoubleSide }))); }
  return mats.get(col);
}

// ------------------------------------------------------------ the kit: triangles painted with a palette cell
const UNIT = {}; // three's own shapes as bare triangle lists, made once
function soup(key, make) { if (!UNIT[key]) { const g = make(), n = g.index ? g.toNonIndexed() : g; UNIT[key] = n.attributes.position.array; } return UNIT[key]; }
const _v = V3(0, 0, 0);
class Kit {
  // split: small raised bits (boxes, cords, pockets, collars) go to a second list, this.t, that becomes its own mesh
  // with no outline: an outline is a blown-up copy, and blown-up trim shows as coloured slivers beside the real trim
  constructor(split) { this.p = []; this.c = []; this.t = split ? new Kit() : null; }
  solid(fn) { const t = this.t; this.t = null; fn(); this.t = t; return this; } // (a big shape made of those bits that should keep its outline)
  tri(a, b, c, cell) { this.p.push(a[0], a[1], a[2], b[0], b[1], b[2], c[0], c[1], c[2]); this.c.push(cell, cell, cell); }
  // a quad, turned to face along `out`: other players' outlines are a back-face copy, so every face has to look outwards
  quad(a, b, c, d, cell, out) {
    if (out) { const ux = c[0] - a[0], uy = c[1] - a[1], uz = c[2] - a[2], vx = d[0] - b[0], vy = d[1] - b[1], vz = d[2] - b[2]; if ((uy * vz - uz * vy) * out[0] + (uz * vx - ux * vz) * out[1] + (ux * vy - uy * vx) * out[2] < 0) { const t = b; b = d; d = t; } }
    this.tri(a, b, c, cell); this.tri(a, c, d, cell);
  }
  // (ni x nj) quads through P(i, j). cell: a cell, or (i, j) -> cell / null for a hole. wrap: the last column joins the first
  grid(ni, nj, P, cell, out, wrap) {
    const pts = [];
    for (let i = 0; i <= ni; i++) { const r = []; for (let j = 0; j <= nj; j++) r.push(wrap && j === nj ? r[0] : P(i, j)); pts.push(r); }
    for (let i = 0; i < ni; i++) for (let j = 0; j < nj; j++) {
      const k = typeof cell === 'function' ? cell(i, j) : cell;
      if (k != null) this.quad(pts[i][j], pts[i][j + 1], pts[i + 1][j + 1], pts[i + 1][j], k, typeof out === 'function' ? out(i, j, pts) : out);
    }
    return pts;
  }
  // a bare triangle list (or another kit) through a matrix. a mirror turns faces inside out: turned back here
  put(arr, cell, m) {
    const flip = m && m.determinant() < 0, cells = typeof cell === 'number' ? null : cell;
    for (let i = 0; i < arr.length; i += 9) for (let k = 0; k < 3; k++) {
      const o = i + (flip ? [0, 2, 1][k] : k) * 3;
      _v.set(arr[o], arr[o + 1], arr[o + 2]); if (m) _v.applyMatrix4(m);
      this.p.push(_v.x, _v.y, _v.z); this.c.push(cells ? cells[i / 3] : cell);
    }
    return this;
  }
  add(kit, m) { return this.put(kit.p, kit.c, m); }
  box(w, h, d, cell, m) { (this.t || this).put(soup('box', () => new THREE.BoxGeometry(1, 1, 1)), cell, (m || T()).clone().multiply(T(0, 0, 0, 0, 0, 0, w, h, d))); return this; }
  ball(r, cell, m, ws = 8, hs = 6) { (this.t || this).put(soup('ball' + ws + hs, () => new THREE.SphereGeometry(1, ws, hs)), cell, (m || T()).clone().multiply(T(0, 0, 0, 0, 0, 0, r))); return this; }
  cyl(r0, r1, h, n, cell, m) { (this.t || this).put(soup(`cyl${n}${r0 === r1 ? '' : (r0 / r1).toFixed(3)}`, () => new THREE.CylinderGeometry(r0 / r1, 1, 1, n)), cell, (m || T()).clone().multiply(T(0, 0, 0, 0, 0, 0, r1, h, r1))); return this; }
  // a tube: prof rows are [radius, distance along, cell, rib]. along -z (an arm), or -y with o.y (a leg). rib: every other
  // column sits that much further in (ribbed knit). o.sx / o.sy squash it; o.cell(row, column, cell) repaints single faces;
  // o.angles: the columns' own angles (a narrow one is a seam)
  lathe(prof, n, cell, o = {}) {
    const ang = o.angles; if (ang) n = ang.length;
    const pt = (r, d, j, rib) => { const a = ang ? ang[j % n] * DEG : (j / n) * TAU + (o.turn || 0), k = rib && j % 2 ? 1 - rib : 1, x = Math.cos(a) * r * k * (o.sx || 1), y = Math.sin(a) * r * k * (o.sy || 1); return o.y ? [x, -d, -y] : [x, y, -d]; };
    for (let i = 0; i < prof.length - 1; i++) {
      const A = prof[i], B = prof[i + 1], k = A[2] ?? cell, rib = A[3] || 0;
      for (let j = 0; j < n; j++) { const a = pt(A[0], A[1], j, rib), b = pt(A[0], A[1], j + 1, rib), c = pt(B[0], B[1], j + 1, rib), d = pt(B[0], B[1], j, rib); this.quad(a, b, c, d, o.cell ? o.cell(i, j, k) : k, o.y ? [a[0] + c[0], 0, a[2] + c[2]] : [a[0] + c[0], a[1] + c[1], 0]); }
    }
    return this;
  }
  // a cord through points, n-sided. r: its radius (or one per point)
  tube(pts, r, n, cell) {
    if (this.t) { this.t.tube(pts, r, n, cell); return this; }
    const P = pts.map((p) => V3(p[0], p[1], p[2])), rings = [];
    let N = null;
    for (let i = 0; i < P.length; i++) {
      const t = P[Math.min(i + 1, P.length - 1)].clone().sub(P[Math.max(i - 1, 0)]).normalize();
      N = N || (Math.abs(t.y) > 0.9 ? V3(0, 0, 1) : V3(0, 1, 0));
      N = N.clone().addScaledVector(t, -N.dot(t)).normalize(); // carried along the cord, so it doesn't twist
      const B = t.clone().cross(N), rr = Array.isArray(r) ? r[i] : r;
      rings.push(Array.from({ length: n }, (_, j) => { const a = (j / n) * TAU + PI / n, q = P[i].clone().addScaledVector(N, Math.cos(a) * rr).addScaledVector(B, Math.sin(a) * rr); return [q.x, q.y, q.z]; }));
    }
    for (let i = 0; i < rings.length - 1; i++) for (let j = 0; j < n; j++) {
      const a = rings[i][j], b = rings[i][(j + 1) % n], c = rings[i + 1][(j + 1) % n], d = rings[i + 1][j], m = P[i].clone().add(P[i + 1]).multiplyScalar(0.5);
      this.quad(a, b, c, d, cell, [(a[0] + c[0]) / 2 - m.x, (a[1] + c[1]) / 2 - m.y, (a[2] + c[2]) / 2 - m.z]);
    }
    for (const [ring, at, dir] of [[rings[0], P[0], -1], [rings[rings.length - 1], P[P.length - 1], 1]]) { // end caps
      const t = P[P.length - 1].clone().sub(P[0]).multiplyScalar(dir), o = [at.x, at.y, at.z];
      for (let j = 0; j < n; j++) this.quad(o, ring[j], ring[(j + 1) % n], o, cell, [t.x, t.y, t.z]);
    }
    return this;
  }
  piece(axis) { return { g: this.done(axis), t: this.t && this.t.c.length ? this.t.done(axis) : null }; } // -> { the outlined shape, its trim }
  // -> a shared geometry centred on itself (outlines and gibs scale + spin about the middle). axis: centred along that
  // axis only, so a limb piece stays on its limb's own line (the body sliders fatten limbs from there)
  done(axis) {
    const g = new THREE.BufferGeometry(), n = this.c.length, uv = new Float32Array(n * 2);
    for (let i = 0; i < n; i++) { uv[i * 2] = (this.c[i] + 0.5) / PW; uv[i * 2 + 1] = 0.5; }
    g.setAttribute('position', new THREE.Float32BufferAttribute(this.p, 3));
    g.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    g.computeVertexNormals(); g.computeBoundingBox();
    const c = g.boundingBox.getCenter(V3(0, 0, 0));
    if (axis) for (const k of ['x', 'y', 'z']) if (k !== axis) c[k] = 0;
    g.translate(-c.x, -c.y, -c.z);
    g.userData.shared = true; g.userData.at = c;
    return g;
  }
}

// ------------------------------------------------------------ the body under the clothes
// the same numbers jokeBody (models.js) reshapes the mannequin with: the build's three bands, fat, the chest, and the
// lumps it adds (belly, bust, butt). key: everything that changes the torso
const band = (y, c, w, h) => (y >= 1.3 ? c : y >= 1.14 ? w + ((c - w) * (y - 1.14)) / 0.16 : y >= 0.98 ? h + ((w - h) * (y - 0.98)) / 0.16 : h);
const fits = new Map();
function fitOf(lk) {
  const bk = Object.hasOwn(BUILDS, lk.build || '') ? lk.build || '' : '', b = BUILDS[bk], fem = bk === 'f';
  const lv = (k) => Math.max(0, Math.min(JOKE_MAX, lk[k] | 0)), ft = lv('fat'), ch = lv('bigChest'), bt = lv('bigButt'), hd = lv('bigHead');
  const key = `${bk}${ft}${ch}${bt}`;
  if (fits.has(key + hd)) return fits.get(key + hd);
  const kc = b.chest * (1 + JOKE.fat * 0.5 * ft) * (1 + (fem ? 0.03 : JOKE.chest) * ch), kcz = (1 + JOKE.fat * 0.6 * ft) * (1 + (fem ? 0.04 : JOKE.chest * 1.4) * ch);
  const kw = b.waist * (1 + JOKE.fat * 1.5 * ft), kh = b.hips * (1 + JOKE.fat * 0.9 * ft), khz = 1 + JOKE.fat * 0.9 * ft;
  const lumps = []; // what jokeBody adds: [x, y, z, rx, ry, rz] (z < 0: out the front). one each side unless x is 0
  if (ft) { const r = 0.1 + JOKE.belly * ft; lumps.push([0, 1.13 - r * 0.1, -(0.05 + r * 0.45), r * 1.25, r * 1.02, r]); }
  if (ch && fem) { const r = 0.05 + JOKE.bust * ch; lumps.push([(0.085 + r * 0.25) * kc, 1.33 - r * 0.15, -(0.11 * kcz + r * 0.45), r, r * 0.95, r]); }
  if (bt) { const r = 0.085 + JOKE.butt * bt; lumps.push([(0.075 + r * 0.32) * kh, 0.97 - r * 0.12, 0.06 + r * 0.62, r, r * 1.05, r * 1.08]); }
  const skin = (y) => { // the bare torso at a height: [half width, half depth]
    let w = 0, d = 0;
    const k = (y - 1.34) / 0.22;
    if (Math.abs(k) < 1) { const s = Math.sqrt(1 - k * k); w = 0.24 * kc * s; d = 0.144 * kcz * s; }
    if (y >= 1.04 && y <= 1.22) { const r = (0.1 + (cl01((1.21 - y) / 0.16)) * 0.02) * kw; w = Math.max(w, r); d = Math.max(d, r); }
    if (y >= 0.88 && y <= 1.08) { w = Math.max(w, 0.17 * kh); d = Math.max(d, 0.115 * khz); }
    return [w, d];
  };
  // one row of a garment drawn for the plain mannequin -> the same row on this body. fol: how closely it follows the
  // build (1 = cut close, less = it hangs off the shoulders). gap: room between cloth and body
  const fitRow = (y, w, f, bk2, fol, gap) => {
    const kx = 1 + (band(y, kc, kw, kh) - 1) * fol, kz = 1 + (band(y, kcz, kw, khz) - 1) * fol, [sw, sd] = skin(y);
    return [y, Math.max(w * kx, sw + gap), Math.max(f * kz, sd + gap), Math.max(bk2 * kz, sd + gap)];
  };
  const F = {
    key, hd, kc, kw, kh, skin, lumps, fem, ft, ch, bt,
    // a garment's rows, fitted. the lumps go with them (shell() pushes the cloth out round each), + extra rows through
    // every lump so the cloth has the points to round it. seat: bottoms sit under a belly, not over it. a row's 5th
    // number is its own fol
    rows(src, fol = 1, gap = 0.012, seat = false) {
      const ys = src.map((r) => r[0]), lo = ys[0], hi = ys[ys.length - 1], mine = seat ? lumps.filter((L) => L[2] > 0) : lumps, lg = seat ? gap : gap + 0.024; // (tops clear the trousers on a big butt too)
      for (const L of mine) for (const k of [-0.95, -0.72, -0.4, 0, 0.4, 0.72, 0.95]) { const y = L[1] + (L[4] + lg) * k; if (y > lo + 0.012 && y < hi - 0.012 && !ys.some((v) => Math.abs(v - y) < 0.014)) ys.push(y); }
      ys.sort((p, q) => p - q);
      const out = ys.map((y) => { let i = 1; while (i < src.length - 1 && src[i][0] < y) i++; const a = src[i - 1], c = src[i], t = cl01((y - a[0]) / (c[0] - a[0])); return fitRow(y, mix(a[1], c[1], t), mix(a[2], c[2], t), mix(a[3], c[3], t), a[4] ?? fol, gap); });
      out.lumps = mine; out.gap = lg;
      return out;
    },
    // the bare torso as a shell (just off the skin, round any belly)
    bare() { return F.skinShell || (F.skinShell = shell(F.rows([0.9, 0.98, 1.06, 1.1, 1.16, 1.22, 1.28, 1.34, 1.4, 1.46, 1.5, 1.53, 1.548].map((y) => [y, 0, 0, 0]), 1, 0.01), 2.2)); },
    // the torso with a top on: the widest of that top's shells at each height (the skin where it has none)
    dressed(shells) {
      const B = F.bare(), ys = [0.96, 1.0, 1.04, 1.08, 1.11, 1.16, 1.22, 1.28, 1.34, 1.4, 1.46, 1.5, 1.53, 1.548];
      for (const r of B.rows) if (!ys.some((y) => Math.abs(y - r[0]) < 0.014)) ys.push(r[0]);
      for (const S of shells) if (S.y0 > 0.96 && !ys.includes(S.y0)) ys.push(S.y0); // (exact at each hem)
      const rows = ys.sort((p, q) => p - q).map((y) => { const a = B.at(y).slice(); for (const S of shells) if (y >= S.y0 - 0.004 && y <= S.y1 + 0.004) S.at(y).forEach((v, k) => { a[k] = Math.max(a[k], v); }); return [y, ...a]; });
      rows.lumps = lumps; rows.gap = shells.length ? shells[0].rows.gap || 0.026 : 0.024;
      return shell(rows, shells.length ? shells[0].e : 2.2);
    },
    // the head at a height (the big head slider): [half width, half depth]
    head(y) { const s = 1 + JOKE.head * hd, t = (y - 1.62 - 0.14 * s) / (0.171 * s); return Math.abs(t) < 1 ? [0.119 * s * Math.sqrt(1 - t * t), 0.133 * s * Math.sqrt(1 - t * t)] : [0, 0]; },
  };
  fits.set(key + hd, F);
  return F;
}

// ------------------------------------------------------------ shells: a garment's surface
// rows of [y, half width, front depth, back depth], rounded off as a squashed superellipse (e: how square), then
// pushed out round the body's lumps (rows.lumps, from fitOf: a belly, a bust, a butt), so cloth stretches over them.
// angles go round the body: 0 = the back (+z), 90 = their right (+x), 180 = the front (-z)
function shell(rows, e = 2.6) {
  const k = 2 / e, n = rows.length, lumps = rows.lumps || [], gap = rows.gap || 0;
  const at = (y) => { let i = 1; while (i < n - 1 && rows[i][0] < y) i++; const a = rows[i - 1], b = rows[i], t = cl01((y - a[0]) / (b[0] - a[0])); return [mix(a[1], b[1], t), mix(a[2], b[2], t), mix(a[3], b[3], t)]; };
  const raw = (y, u) => {
    const [w, f, b] = at(y), s = Math.sin(u), c = Math.cos(u), x = Math.sign(s) * Math.abs(s) ** k * w, z = Math.sign(c) * Math.abs(c) ** k * (c > 0 ? b : f);
    if (!lumps.length) return [x, y, z];
    const r0 = Math.hypot(x, z) || 1e-6, dx = x / r0, dz = z / r0;
    let r = r0;
    for (const L of lumps) { // as far out as the lump (+ the gap) reaches along this spoke
      const t = (y - L[1]) / (L[4] + gap);
      if (Math.abs(t) >= 1) continue;
      const q = Math.sqrt(1 - t * t), a2 = ((L[3] + gap) * q) ** 2, b2 = ((L[5] + gap) * q) ** 2, A = (dx * dx) / a2 + (dz * dz) / b2;
      for (const cx of L[0] ? [L[0], -L[0]] : [0]) { const B = -2 * ((dx * cx) / a2 + (dz * L[2]) / b2), D = B * B - 4 * A * ((cx * cx) / a2 + (L[2] * L[2]) / b2 - 1); if (D > 0) r = Math.max(r, (-B + Math.sqrt(D)) / (2 * A)); }
    }
    return [dx * r, y, dz * r];
  };
  const S = {
    rows, e, at, y0: rows[0][0], y1: rows[n - 1][0], lumpy: lumps.length > 0,
    nrm(y, u) { // outward normal (numeric)
      const a = raw(y, u - 0.03), b = raw(y, u + 0.03), c = raw(y - 0.004, u), d = raw(y + 0.004, u);
      const tx = b[0] - a[0], ty = b[1] - a[1], tz = b[2] - a[2], vx = d[0] - c[0], vy = d[1] - c[1], vz = d[2] - c[2];
      const nx = ty * vz - tz * vy, ny = tz * vx - tx * vz, nz = tx * vy - ty * vx, l = Math.hypot(nx, ny, nz) || 1;
      return [nx / l, ny / l, nz / l];
    },
    // the point at height y, angle u, `lift` off the cloth
    p(y, u, lift = 0) { const a = raw(y, u); if (!lift) return a; const N = S.nrm(y, u); return [a[0] + N[0] * lift, a[1] + N[1] * lift, a[2] + N[2] * lift]; },
    // the angle where the front (or back) of the shell is x across
    ux(y, x, back) { const a = Math.asin(Math.min(1, Math.abs(x) / at(y)[0]) ** (1 / k)) * Math.sign(x); return back ? a : PI - a; },
    f(x, y, lift) { return S.p(y, S.ux(y, x), lift); },
    b(x, y, lift) { return S.p(y, S.ux(y, x, true), lift); },
    // a frame sitting on the cloth: x = to the right as you look at it, y = up the cloth, z = out of it
    frame(y, u, lift = 0) {
      const N = S.nrm(y, u), Z = V3(N[0], N[1], N[2]), X = V3(0, 1, 0).cross(Z);
      if (X.lengthSq() < 1e-6) X.set(1, 0, 0);
      X.normalize();
      const p = raw(y, u);
      return new THREE.Matrix4().makeBasis(X, Z.clone().cross(X), Z).setPosition(p[0] + N[0] * lift, p[1] + N[1] * lift, p[2] + N[2] * lift);
    },
    ff(x, y, lift) { return S.frame(y, S.ux(y, x), lift); },
    bf(x, y, lift) { return S.frame(y, S.ux(y, x, true), lift); },
    // the height that's `dist` down the cloth from y (collars and hems are so long, however steep the shoulder is)
    down(y, u, dist) { const a = raw(y, u); let lo = y - dist, hi = y; for (let i = 0; i < 12; i++) { const m = (lo + hi) / 2, b = raw(m, u); if (Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]) > dist) lo = m; else hi = m; } return (lo + hi) / 2; },
    // heights for a loft from y0 to y1: its own rows in between (so the cloth really is the shell) + any more
    lv(y0, y1, more = []) { const out = [y0, y1, ...more.filter((y) => y > y0 && y < y1)]; for (const r of rows) if (r[0] > y0 + 0.008 && r[0] < y1 - 0.008 && !out.some((y) => Math.abs(y - r[0]) < 0.008)) out.push(r[0]); return out.sort((a, b) => a - b); },
  };
  return S;
}
// cloth on a shell between heights lv and angles us. an angle can be a function of the height (an edge that isn't
// straight up, like a zip pulled open). openCols marks the two edges of an open front: nothing is drawn between them.
// cell: a palette cell or (y, u, i, j) -> cell / null (a hole). o.lift(i, j)
function loft(K, S, lv, us, cell, o = {}) {
  const U = (i, j) => (typeof us[j] === 'function' ? us[j](lv[i], i) : us[j]), n = o.wrap ? us.length : us.length - 1;
  const hole = (j) => us[j].edge && us[(j + 1) % us.length].edge; // between the two edges of an open front
  return K.grid(lv.length - 1, n, (i, j) => S.p(lv[i], U(i, j), typeof o.lift === 'function' ? o.lift(i, j) : o.lift || 0),
    (i, j) => (hole(j) ? null : typeof cell === 'function' ? cell((lv[i] + lv[i + 1]) / 2, (U(i, j) + (o.wrap && j === n - 1 ? U(i, 0) + TAU : U(i, j + 1))) / 2, i, j) : cell),
    (i, j, p) => { const a = p[i][j], c = p[i + 1][j + 1], x = a[0] + c[0], z = a[2] + c[2]; return o.inward ? [-x, 0, -z] : [x, 0, z]; }, o.wrap);
}
// a raised piece lying on a shell. g(s, t) -> [x, y] as it looks from the front (o.back: from behind; o.uy: [angle, y]),
// cut into ns x nt quads, `lift` off the cloth (a number, or (i, j) -> a height: ruffles), with a rim back down to it
// (o.rim: its cell, or false for none)
function panel(K, S, g, ns, nt, cell, lift = 0.006, o = {}) {
  if (S.lumpy) { ns *= 2; nt *= 2; } // finer over a belly / bust / butt, so it stays on top of the cloth it lies on
  const at = (s, t, l) => { const [a, y] = g(s, t); return S.p(y, o.uy ? a : S.ux(y, a, o.back), l); };
  const mid = at(0.5, 0.5, 0), out = (i, j, p) => { const a = p[i][j], c = p[i + 1][j + 1]; return [a[0] + c[0], 0, a[2] + c[2]]; };
  K = K.t || K;
  const top = K.grid(nt, ns, (i, j) => at(j / ns, i / nt, typeof lift === 'function' ? lift(i, j) : lift), cell, out);
  if (o.rim === false) return top;
  const rc = o.rim ?? (typeof cell === 'function' ? cell(0, 0) : cell), base = (i, j) => at(j / ns, i / nt, -0.003);
  const wall = (i0, j0, i1, j1) => { const a = top[i0][j0], b = top[i1][j1]; K.quad(a, b, base(i1, j1), base(i0, j0), rc, [(a[0] + b[0]) / 2 - mid[0], (a[1] + b[1]) / 2 - mid[1], (a[2] + b[2]) / 2 - mid[2]]); };
  for (let j = 0; j < ns; j++) { wall(0, j, 0, j + 1); wall(nt, j, nt, j + 1); }
  for (let i = 0; i < nt; i++) { wall(i, 0, i + 1, 0); wall(i, ns, i + 1, ns); }
  return top;
}
const rect = (x0, y0, x1, y1) => (s, t) => [mix(x0, x1, s), mix(y0, y1, t)];
const quad4 = (a, b, c, d) => (s, t) => [mix(mix(a[0], b[0], s), mix(d[0], c[0], s), t), mix(mix(a[1], b[1], s), mix(d[1], c[1], s), t)]; // a, b along the bottom; d, c along the top
// a straight strip from a to b ([x, y] in the front / back view), w wide
function bar(K, S, a, b, w, cell, lift, o = {}) {
  const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1, nx = (-dy / l) * w * 0.5, ny = (dx / l) * w * 0.5, w1 = o.taper ?? 1;
  return panel(K, S, quad4([a[0] - nx, a[1] - ny], [a[0] + nx, a[1] + ny], [b[0] + nx * w1, b[1] + ny * w1], [b[0] - nx * w1, b[1] - ny * w1]), 1, Math.max(1, Math.ceil(l / (o.step || 0.05))), cell, lift, o);
}
// a button / snap / stud flat on the cloth
function stud(K, m, r, cell, h = 0.008, n = 6) { K.cyl(r * 0.8, r, h, n, cell, m.clone().multiply(T(0, 0, h / 2, PI / 2))); }
// seven-segment block digits (the unit number), h tall, starting at x and reading the right way round from where you look
const SEG = { a: [0, 1, 1], b: [1, 0.5, 0], c: [1, -0.5, 0], d: [0, -1, 1], e: [-1, -0.5, 0], f: [-1, 0.5, 0], g: [0, 0, 1] }, DIGIT = ['abcdef', 'bc', 'abged', 'abgcd', 'fgbc', 'afgcd', 'afgedc', 'abc', 'abcdefg', 'abfgcd'];
function digits(K, S, str, x, y, h, cell, lift, back) {
  const w = h * 0.52, t = h * 0.17, dir = back ? 1 : -1;
  [...str].forEach((ch, i) => { for (const s of DIGIT[+ch]) { const [sx, sy, flat] = SEG[s], cx = x + dir * (i * w * 1.55 + (sx * (w - t)) / 2), cy = y + (sy * (h - t)) / 2, hw = flat ? w / 2 : t / 2, hh = flat ? t / 2 : (h - t) / 4 + t / 2; panel(K, S, rect(cx - hw, cy - hh, cx + hw, cy + hh), 1, 1, cell, lift, { back, rim: false }); } });
}

// ------------------------------------------------------------ limbs
// where each arm piece hangs: [start, turn about y, stretch]. the right arm points straight out front holding the gun;
// the left one reaches across. one sleeve shape does both arms (the left's pieces are a touch longer)
const ARM = { ur: [[0, 0, 0], 0, 1], fr: [[-0.03, -0.01, -0.3], 0, 1], ul: [[0.005, -0.02, -0.005], -0.45, 1.05], fl: [[0.153, -0.04, -0.307], -0.9, 1.1] };
const Y = V3(0, 1, 0);
function hang(parent, geo, mat, [pos, ry, kz] = [[0, 0, 0], 0, 1]) {
  const m = new THREE.Mesh(geo, mat), a = geo.userData.at;
  m.rotation.y = ry; m.scale.z = kz;
  _v.set(a.x, a.y, a.z * kz).applyAxisAngle(Y, ry);
  m.position.set(pos[0] + _v.x, pos[1] + _v.y, pos[2] + _v.z);
  parent.add(m);
  return m;
}
// hang a piece: its outlined shape, and its trim marked so other players' outlines skip it (remote.js noShell)
function wear(parent, pc, mat, at) { const m = hang(parent, pc.g, mat, at); if (pc.flat) m.userData.noShell = true; if (pc.t) hang(parent, pc.t, mat, at).userData.noShell = true; }
const limbs = new Map(); // sleeve and leg shapes: the same on every body (jokeBody fattens the meshes)
function limb(key, make) { if (!limbs.has(key)) limbs.set(key, make()); return limbs.get(key); }
// garment shapes cut for a body, newest last. past the cap the oldest goes: whoever still wears it frees it with their character
const cuts = new Map(), CUTS = 72;
function cut(key, make) {
  let g = cuts.get(key);
  if (g) { cuts.delete(key); cuts.set(key, g); return g; }
  g = make(); cuts.set(key, g);
  if (cuts.size > CUTS) { const old = cuts.keys().next().value, pc = cuts.get(old); for (const x of [pc.g, pc.t]) if (x) x.userData.shared = false; cuts.delete(old); }
  return g;
}

// ------------------------------------------------------------ tailoring shared by the garments
const ROUND = [0, 26, 50, 72, 90, 108, 130, 152, 180, 208, 230, 252, 270, 288, 310, 334].map((d) => d * DEG); // columns round a closed body
const DENSE = ROUND.flatMap((a, j) => [a, (a + (j < 15 ? ROUND[j + 1] : TAU)) / 2]); // twice as many: a body with a belly / bust / butt to go round
const cols = (S) => (S.lumpy ? DENSE : ROUND);
// columns round a body that's open down the front: edge(y) = how far each edge is from x0
// (round a belly or a bust there's one more column each side of the opening, kept clear of the edge, so the fronts
// round it too instead of cutting straight across and letting the shirt under them through)
function openCols(S, edge, x0 = 0) {
  const [R, L] = [1, -1].map((k) => Object.assign((y) => S.ux(y, x0 + k * edge(y)), { edge: true }));
  const mid = S.lumpy ? [(y) => Math.min(166 * DEG, R(y) - 0.03), R, L, (y) => Math.max(194 * DEG, L(y) + 0.03)] : [R, L];
  return [...cols(S).filter((a) => a < 153 * DEG), ...mid, ...cols(S).filter((a) => a > 207 * DEG)];
}
const ring = (n) => Array.from({ length: n }, (_, j) => (j / n) * TAU);
const radial = (i, j, p) => { const a = p[i][j], c = p[i + 1][j + 1]; return [a[0] + c[0], 0, a[2] + c[2]]; };
const upish = (i, j, p) => { const a = p[i][j], c = p[i + 1][j + 1]; return [(a[0] + c[0]) * 0.3, 1, (a[2] + c[2]) * 0.3]; };
const front = (u) => (1 - Math.cos(u)) / 2; // 0 at the back, 1 at the front
const covered = (lk) => !!lk.back && lk.back !== 'none' && lk.back !== 'cattail'; // something sits on the back
// ribbed knit round a shell from y0 to y1 (every other column sits in). stripe: [from, to, cell] through it
function rib(K, S, y0, y1, cell, n = 36, stripe) {
  loft(K, S, S.lv(y0, y1, stripe ? [stripe[0], stripe[1]] : []), ring(n), stripe ? (y) => (y > stripe[0] && y < stripe[1] ? stripe[2] : cell) : cell, { wrap: true, lift: (i, j) => (j % 2 ? 0 : -0.007) });
}
// a stitched line up the cloth at an angle
const seam = (K, S, d, y0, y1, cell = C.seam, w = 2.2) => panel(K, S, (s, t) => [(d + (s - 0.5) * w) * DEG, mix(y0, y1, t)], 1, Math.max(1, Math.ceil((y1 - y0) / 0.07)), cell, 0.0025, { uy: true, rim: false });
// a flat lid across a shell's ring (waistbands, the bottom of a seat)
function lid(K, S, y, cell, up) { const c = [0, y, 0], us = cols(S), n = us.length; for (let j = 0; j < n; j++) K.tri(c, S.p(y, us[up ? j : (j + 1) % n]), S.p(y, us[up ? (j + 1) % n : j]), cell); }
// the layer under a jacket: the same shell, a little smaller
function inner(S, d = 0.012) { const rows = S.rows.map(([y, w, f, b]) => [y, w - d, f - d, b - d]); rows.lumps = S.rows.lumps; rows.gap = Math.max(0.002, (S.rows.gap || 0) - d); return shell(rows, S.e); }
// a collar lying on a shell: from the neck edge top(u) it comes len(u) down the cloth, lifted off it, with a rim round the
// outside. o.a0 -> o.a1: an open one (its two ends get closed). o.stand: how far it stands up round the neck first
function collar(K, S, top, len, cell, o = {}) {
  const n = o.n || 16, a0 = o.a0 ?? 0, a1 = o.a1 ?? TAU, open = Math.abs(a1 - a0) < TAU - 0.01, nt = o.nt || 1, lift = o.lift ?? 0.01;
  const U = (j) => mix(a0, a1, j / n), Yt = (u) => (typeof top === 'function' ? top(u) : top), L = (u) => (typeof len === 'function' ? len(u) : len);
  const at = (i, j, l) => { const u = U(j); return S.p(S.down(Yt(u), u, L(u) * (1 - i / nt)), u, l); };
  K = K.t || K;
  const g = K.grid(nt, n, (i, j) => at(i, j, typeof lift === 'function' ? lift(i, j) : lift), cell, upish, !open);
  const rc = o.rim ?? (typeof cell === 'function' ? cell(0, 0) : cell);
  for (let j = 0; j < n; j++) { const a = g[0][j], b = g[0][j + 1]; K.quad(a, b, at(0, j + 1, -0.002), at(0, j, -0.002), rc, [a[0] + b[0], -0.7, a[2] + b[2]]); }
  if (open) for (const j of [0, n]) for (let i = 0; i < nt; i++) { const a = g[i][j], b = g[i + 1][j], q = g[i][j ? n - 1 : 1]; K.quad(a, b, at(i + 1, j, -0.002), at(i, j, -0.002), rc, [a[0] - q[0], a[1] - q[1], a[2] - q[2]]); }
  if (o.stand) K.grid(1, n, (i, j) => { const p = g[nt][open ? j : j % n]; return i ? [p[0] * 0.95, p[1] + o.stand, p[2] * 0.95] : p; }, o.standCell ?? rc, radial, !open);
  return g;
}

// ------------------------------------------------------------ Runner Jacket: an oversized hi-vis bomber
// black yoke, sides and ribbed knit (hem, cuffs, a stripe through each), a big padded collar left open with a loud
// lining, a chunky zip a bit off-centre, reflective tape and an armband on the sleeves, slanted hand pockets, and a
// black panel on the back with a little running figure on it (it's a runner jacket)
const RUN_E = 2.7, RUN_ZX = 0.046;
function runnerCut(F) {
  const e = RUN_E;
  return [shell(F.rows([[1.085, 0.24, 0.168, 0.17], [1.105, 0.262, 0.182, 0.18], [1.14, 0.28, 0.192, 0.188], [1.26, 0.284, 0.194, 0.19], [1.39, 0.294, 0.196, 0.192],
    [1.46, 0.296, 0.19, 0.19], [1.505, 0.284, 0.176, 0.182], [1.535, 0.215, 0.15, 0.156], [1.552, 0.134, 0.118, 0.122]], 0.55, 0.016), e),
  shell(F.rows([[0.996, 0.23, 0.16, 0.164], [1.092, 0.238, 0.166, 0.168]], 1, 0.026), e)];
}
function runnerBody(F, lk, [S, R]) {
  const K = new Kit(true), zx = RUN_ZX;
  const open = (y) => 0.036 * cl01((y - 1.44) / 0.112) ** 1.4; // the zip is pulled down to the yoke: the fronts part above it
  const side = (u) => Math.abs(Math.abs(u - PI) - PI / 2) < 18.5 * DEG;
  loft(K, S, S.lv(1.085, 1.552, [1.105, 1.14, 1.26, 1.39, 1.455, 1.505, 1.535]), openCols(S, open, zx), (y, u) => (y > 1.455 || side(u) ? C.ink : C.base), { wrap: true });
  // the yoke dips to a point front and back
  for (const back of [false, true]) for (const sx of [-1, 1]) { const x0 = back ? 0 : zx; panel(K, S, quad4([x0, 1.398], [sx * 0.215, 1.458], [sx * 0.215, 1.46], [x0, 1.46]), 4, 1, C.ink, 0.003, { back, rim: false }); }
  // panel seams down the body, a stitched line across each yellow panel (so the big faces aren't bare)
  for (const d of [26, 130, 230, 334]) seam(K, S, d, 1.14, 1.45);
  for (const back of [false, true]) for (const [x0, x1] of back ? [[-0.2, -0.105], [0.105, 0.2]] : [[-0.215, -0.02], [zx + 0.03, 0.215]]) bar(K, S, [x0, 1.232], [x1, 1.232], 0.007, C.seam, 0.0025, { back, rim: false, step: 0.04 });
  rib(K, R, 0.996, 1.092, C.ink, 36, [1.03, 1.047, C.mark]); // ribbed hem band with a stripe through it
  // a dark tee in the open neck
  const N = shell(F.rows([[1.3, 0, 0, 0], [1.42, 0, 0, 0], [1.5, 0, 0, 0], [1.548, 0.07, 0.066, 0.066]], 1, 0.008), 2.2);
  loft(K, N, N.lv(1.36, 1.548), [100, 125, 150, 180, 210, 235, 260].map((d) => d * DEG), C.tee);
  // ---- the collar: padded, flared, open at the front, lower there than at the nape. the lining is the loud bit
  const ch = [1.548, 1.6, 1.655, 1.705].map((y) => { const h = F.head(y), t = (y - 1.548) / 0.157; return [y, Math.max(mix(0.134, 0.178, t), h[0] + 0.04), Math.max(mix(0.118, 0.16, t), h[1] + 0.032), Math.max(mix(0.122, 0.166, t), h[1] + 0.034)]; });
  const Cl = shell(ch, 2.3), cn = 14, ct = 3, gapAt = (t) => 0.036 + 0.05 * t;
  const cu = (t, j) => { const y = mix(1.548, 1.705, t); return mix(Cl.ux(y, zx + gapAt(t)), Cl.ux(y, zx - gapAt(t)) - TAU, j / cn); };
  const cp = (lift) => (i, j) => { const t = i / ct, u = cu(t, j); return Cl.p(mix(1.548, 1.705 - 0.05 * front(u) ** 2, t), u, lift); };
  const co = K.grid(ct, cn, cp(0), (i) => (i === ct - 1 ? C.coal : C.ink), radial), ci = K.grid(ct, cn, cp(-0.02), C.pop, (i, j, p) => radial(i, j, p).map((v) => -v));
  for (let j = 0; j < cn; j++) K.quad(co[ct][j], co[ct][j + 1], ci[ct][j + 1], ci[ct][j], C.ink, [0, 1, 0]); // the rolled top edge
  for (const j of [0, cn]) for (let i = 0; i < ct; i++) K.quad(co[i][j], co[i + 1][j], ci[i + 1][j], ci[i][j], C.ink, [j ? -1 : 1, 0, -1]); // its two front ends
  // ---- the zip: tape, chunky teeth, a slider with a pull in the accent colour
  panel(K, S, rect(zx - 0.016, 1.092, zx + 0.016, 1.444), 1, 5, C.ink, 0.004);
  for (let i = 0, y = 1.104; y < 1.43; y += 0.026, i++) K.box(0.017, 0.012, 0.009, C.silver, S.ff(zx + (i % 2 ? 0.004 : -0.004), y, 0.008));
  K.box(0.03, 0.036, 0.016, C.silver, S.ff(zx, 1.446, 0.01));
  K.box(0.018, 0.05, 0.007, C.pop, S.ff(zx, 1.446, 0.016).multiply(T(0.004, -0.036, 0, 0, 0, 0.18)));
  K.box(0.008, 0.016, 0.01, C.steel, S.ff(zx, 1.446, 0.016).multiply(T(0.001, -0.012, 0)));
  // ---- chest: a signal tab on their left, the stripe tab on their right
  panel(K, S, rect(-0.17, 1.3, -0.085, 1.365), 2, 1, C.ink, 0.006);
  [0.016, 0.028, 0.042].forEach((h, i) => panel(K, S, rect(-0.108 - i * 0.02, 1.309, -0.094 - i * 0.02, 1.309 + h), 1, 1, C.silver, 0.01, { rim: false }));
  panel(K, S, rect(-0.163, 1.343, -0.151, 1.355), 1, 1, C.pop, 0.01, { rim: false });
  panel(K, S, rect(0.115, 1.292, 0.17, 1.372), 1, 1, C.ink, 0.006);
  for (const y of [1.318, 1.346]) panel(K, S, rect(0.121, y - 0.007, 0.164, y + 0.007), 1, 1, C.silver, 0.01, { rim: false });
  // ---- slanted hand pockets: a black welt, a snap at the top
  for (const sx of [-1, 1]) {
    bar(K, S, [sx * 0.2 + zx * 0.3, 1.262], [sx * 0.152 + zx * 0.3, 1.165], 0.026, C.ink, 0.006);
    stud(K, S.ff(sx * 0.21 + zx * 0.3, 1.276, 0.002), 0.011, C.silver);
  }
  // ---- the back: a black panel in a tape frame, the runner on it (left off under a backpack, cape, wings...)
  panel(K, S, rect(-0.165, 1.15, 0.165, 1.405), 6, 3, C.ink, 0.006, { back: true });
  for (const [a, b] of [[[-0.15, 1.165], [0.15, 1.165]], [[-0.15, 1.39], [0.15, 1.39]], [[-0.15, 1.165], [-0.15, 1.39]], [[0.15, 1.165], [0.15, 1.39]]]) bar(K, S, a, b, 0.009, C.silver, 0.009, { back: true, rim: false, step: 0.06 });
  if (!covered(lk)) {
    const B = (a, b, w = 0.024) => bar(K, S, a, b, w, C.mark, 0.0105, { back: true, rim: false, step: 0.2 });
    panel(K, S, rect(0.018, 1.336, 0.056, 1.374), 1, 1, C.mark, 0.0105, { back: true, rim: false }); // head
    B([-0.008, 1.262], [0.026, 1.332], 0.036); // body, leaning into it
    B([0.02, 1.322], [0.064, 1.296], 0.02); B([0.064, 1.296], [0.092, 1.322], 0.02); // front arm
    B([0.016, 1.318], [-0.034, 1.306], 0.02); B([-0.034, 1.306], [-0.058, 1.276], 0.02); // back arm
    B([-0.006, 1.268], [0.05, 1.236]); B([0.05, 1.236], [0.04, 1.184]); B([0.03, 1.186], [0.066, 1.186], 0.014); // front leg + foot
    B([-0.008, 1.262], [-0.052, 1.226]); B([-0.052, 1.226], [-0.106, 1.24]); // back leg, kicked up
    for (const [y, l] of [[1.35, 0.05], [1.316, 0.036], [1.282, 0.05]]) B([-0.134, y], [-0.134 + l, y], 0.011); // speed lines
    digits(K, S, '12', 0.092, 1.196, 0.036, C.silver, 0.0105, true);
  }
  return K.piece();
}
// puffy sleeves gathered into ribbed cuffs: a black shoulder (the yoke carries on over it), a tape - black - tape armband,
// tape round the forearm. left: their left sleeve gets the pen pocket
function runnerSleeve(part, left) {
  const K = new Kit(true), n = 12;
  if (part === 'up') {
    K.lathe([[0.001, -0.094, C.ink], [0.066, -0.076, C.ink], [0.094, -0.03, C.ink], [0.099, 0.022], [0.094, 0.1], [0.094, 0.112, C.silver], [0.096, 0.126, C.ink], [0.096, 0.166, C.silver], [0.094, 0.18],
      [0.088, 0.184], [0.082, 0.25], [0.085, 0.288], [0.074, 0.318], [0.05, 0.33]], n, C.base);
    if (left) { // a pen pocket on the outside of the arm: black flap, two pens
      const m = T(-0.093, 0.004, -0.058, 0, PI / 2, 0);
      K.box(0.07, 0.05, 0.012, C.ink, m.clone().multiply(T(0, 0, 0.002))); K.box(0.076, 0.016, 0.016, C.coal, m.clone().multiply(T(0, 0.022, 0.004)));
      for (const [x, c] of [[-0.016, C.pop], [0.004, C.silver]]) K.box(0.009, 0.03, 0.009, c, m.clone().multiply(T(x, 0.04, 0.004)));
    }
  } else {
    K.lathe([[0.066, -0.03], [0.078, 0.02], [0.08, 0.062], [0.081, 0.066, C.silver], [0.081, 0.084], [0.079, 0.088], [0.072, 0.13], [0.06, 0.148], [0.058, 0.15, C.ink, 0.09], [0.058, 0.166, C.mark, 0.09], [0.058, 0.176, C.ink, 0.09], [0.055, 0.202], [0.047, 0.204, C.deep], [0.04, 0.19]], n, C.base);
  }
  return K.piece('z');
}

// ------------------------------------------------------------ T-Shirt: a crew neck with a chest pocket
// loose over the waistband, a ribbed collar that sits lower at the front, hemmed sleeves, side seams, a little hem tag
function teeCut(F) { const e = 2.4; return [shell(F.rows([[1.015, 0.22, 0.158, 0.162], [1.09, 0.212, 0.153, 0.155], [1.2, 0.222, 0.152, 0.152], [1.32, 0.252, 0.162, 0.16], [1.42, 0.264, 0.158, 0.158], [1.49, 0.252, 0.136, 0.142], [1.525, 0.165, 0.106, 0.116], [1.548, 0.098, 0.088, 0.092]], 0.9, 0.012), e)]; }
// the neck hole of a pullover: the cloth carries on up to an edge that sits lower at the front, a ribbed band round it
function crewNeck(K, S, yb, dip, cell, band) {
  const top = (u) => S.y1 - dip * front(u) ** 2;
  K.grid(2, 16, (i, j) => { const u = ROUND[j % 16]; return S.p(mix(yb, top(u), i / 2), u); }, cell, upish, true);
  collar(K, S, top, 0.017, band, { lift: 0.005, stand: 0.007 });
}
function teeBody(F, lk, [S]) {
  const K = new Kit(true);
  loft(K, S, S.lv(1.015, 1.525, [1.04]), cols(S), (y) => (y < 1.04 ? C.panel : C.base), { wrap: true });
  crewNeck(K, S, 1.525, 0.02, C.base, C.panel);
  panel(K, S, rect(-0.168, 1.325, -0.096, 1.398), 2, 2, C.panel, 0.005, { rim: C.seam }); // chest pocket (their left)
  bar(K, S, [-0.17, 1.392], [-0.094, 1.392], 0.014, C.panel, 0.007, { step: 0.04 });
  seam(K, S, 90, 1.045, 1.36); seam(K, S, 270, 1.045, 1.36);
  for (const back of [false, true]) for (const sx of [-1, 1]) { // where it creases at the waist
    bar(K, S, [sx * 0.205, 1.18], [sx * 0.115, 1.142], 0.009, C.panel, 0.003, { back, rim: false, taper: 0.15, step: 0.04 });
    bar(K, S, [sx * 0.21, 1.245], [sx * 0.15, 1.222], 0.008, C.panel, 0.003, { back, rim: false, taper: 0.15, step: 0.04 });
  }
  K.box(0.02, 0.026, 0.005, C.white, S.frame(1.052, 252 * DEG, 0.003)); // the hem tag
  return K.piece();
}
function teeSleeve() {
  return new Kit().lathe([[0.001, -0.09], [0.058, -0.072], [0.081, -0.03], [0.085, 0.02], [0.082, 0.112], [0.082, 0.118, C.panel], [0.084, 0.122, C.panel], [0.084, 0.152], [0.074, 0.154, C.deep], [0.062, 0.134]], 12, C.base).piece('z');
}

// ------------------------------------------------------------ Hoodie: a heavy pullover
// ribbed hem and cuffs, a kangaroo pocket you can see into, a hood lying down the back (tucked flat under a backpack
// or a cape), its thick edge round the neck, two drawstrings with metal tips
function hoodieCut(F) {
  const e = 2.5;
  return [shell(F.rows([[1.07, 0.228, 0.164, 0.166], [1.092, 0.246, 0.174, 0.172], [1.2, 0.246, 0.176, 0.172], [1.33, 0.264, 0.178, 0.174], [1.43, 0.274, 0.168, 0.168], [1.495, 0.262, 0.148, 0.156], [1.53, 0.172, 0.116, 0.13], [1.552, 0.112, 0.096, 0.1]], 0.75, 0.014), e),
    shell(F.rows([[0.998, 0.222, 0.158, 0.162], [1.078, 0.226, 0.162, 0.164]], 1, 0.026), e)];
}
function hoodieBody(F, lk, [S, R]) {
  const K = new Kit(true), flat = covered(lk);
  loft(K, S, S.lv(1.07, 1.552), cols(S), C.base, { wrap: true });
  rib(K, R, 0.998, 1.078, C.panel);
  seam(K, S, 90, 1.095, 1.36); seam(K, S, 270, 1.095, 1.36);
  // kangaroo pocket: a raised pouch, dark where the hands go in
  panel(K, S, quad4([-0.152, 1.088], [0.152, 1.088], [0.104, 1.222], [-0.104, 1.222]), 4, 2, C.base, 0.013, { rim: C.panel });
  for (const sx of [-1, 1]) bar(K, S, [sx * 0.146, 1.1], [sx * 0.11, 1.206], 0.026, C.deep, 0.0146, { rim: false, step: 0.04 });
  bar(K, S, [-0.098, 1.214], [0.098, 1.214], 0.008, C.seam, 0.0146, { rim: false, step: 0.04 });
  // the hood's thick edge round the neck: low at the throat, high at the nape
  const h = F.head(1.61), hx = Math.max(0.12, h[0] + 0.034), hz = Math.max(0.114, h[1] + 0.03), pts = [], rs = [];
  for (let i = 0; i <= 14; i++) { const a = mix(0.16, TAU - 0.16, i / 14), q = front(a + PI), end = Math.abs(i - 7) / 7; pts.push([Math.sin(a) * hx, mix(1.528, 1.604, q) - 0.016 * end ** 6, -Math.cos(a) * hz - 0.014 * end ** 6]); rs.push(mix(0.031, 0.024, end)); }
  K.solid(() => K.tube(pts, rs, 6, C.base));
  // the hood itself, down the back: a soft sack with its opening on top. its edges tuck in against the jacket
  const zb = (x, y) => S.b(x, Math.min(y, S.y1))[2] - 0.006, hang0 = flat ? 0.035 : 0.09, tip = flat ? 1.47 : 1.415;
  const line = [[1.632, hz - 0.004, 0.13], [1.622, hz + hang0 * 0.75, 0.17], [1.565, hz + hang0 + 0.035, 0.18], [1.495, hz + hang0 + 0.028, 0.148], [tip, 0, 0.06]];
  K.grid(4, 6, (i, j) => { const [y, z, hw] = line[i], s = (j / 6) * 2 - 1, x = hw * s, yy = y - 0.014 * s * s, back = zb(x, yy); return [x, yy, i === 4 ? back + 0.012 : mix(z, back, Math.abs(s) ** 2.4)]; }, (i) => (i ? C.base : C.seam), [0, 0.5, 1]);
  // drawstrings with metal tips
  for (const sx of [-1, 1]) {
    K.tube([S.f(sx * 0.03, 1.505, 0.016), S.f(sx * 0.037, 1.455, 0.012), S.f(sx * 0.041, 1.395, 0.012)], 0.0062, 4, C.cream);
    K.box(0.014, 0.03, 0.014, C.steel, S.ff(sx * 0.0415, 1.38, 0.012));
  }
  return K.piece();
}
function hoodieSleeve(part) {
  const K = new Kit(true);
  if (part === 'up') K.lathe([[0.001, -0.092], [0.062, -0.074], [0.087, -0.03], [0.091, 0.02], [0.088, 0.056], [0.089, 0.058, C.seam], [0.089, 0.066], [0.086, 0.068], [0.078, 0.2], [0.081, 0.236], [0.075, 0.25], [0.081, 0.286], [0.072, 0.318], [0.05, 0.33]], 12, C.base);
  else K.lathe([[0.064, -0.03], [0.075, 0.02], [0.077, 0.05], [0.071, 0.064], [0.076, 0.08], [0.07, 0.13], [0.06, 0.146], [0.059, 0.148, C.panel, 0.09], [0.057, 0.2, C.panel], [0.048, 0.202, C.deep], [0.04, 0.188]], 12, C.base);
  return K.piece('z');
}

// ------------------------------------------------------------ Jacket: a boxy work jacket, worn open over a white tee
// a fold-down collar, two chest pockets with pointed flaps and brass buttons, a button placket, seams down to a
// waistband with side tabs, a yoke across the back, buttoned cuffs
function jacketCut(F) { const e = 2.9; return [shell(F.rows([[1.03, 0.228, 0.165, 0.163], [1.075, 0.23, 0.166, 0.164], [1.2, 0.238, 0.17, 0.168], [1.33, 0.262, 0.176, 0.172], [1.43, 0.276, 0.172, 0.17], [1.492, 0.266, 0.152, 0.158], [1.528, 0.175, 0.118, 0.13], [1.548, 0.11, 0.094, 0.1]], 0.8, 0.014), e)]; }
// what shows in an open front: the layer under it (cells(y) paints it) and the thickness of the jacket's two edges
function openFront(K, S, edge, y0, y1, cell, x0 = 0) {
  const I = inner(S), lv = S.lv(y0, y1), all = S.lv(S.y0, y1);
  loft(K, I, lv, [1, 0.4, -0.4, -1].map((k) => (y) => I.ux(y, x0 + k * (edge(y) + (Math.abs(k) === 1 ? 0.03 : 0)))), cell);
  for (const sx of [-1, 1]) for (let i = 0; i < all.length - 1; i++) { const a = all[i], b = all[i + 1]; K.quad(S.p(a, S.ux(a, x0 + sx * edge(a))), S.p(b, S.ux(b, x0 + sx * edge(b))), I.p(b, I.ux(b, x0 + sx * edge(b))), I.p(a, I.ux(a, x0 + sx * edge(a))), C.seam, [-sx, 0, -0.2]); }
  return I;
}
function jacketBody(F, lk, [S]) {
  const K = new Kit(true), edge = (y) => mix(0.07, 0.048, cl01((y - 1.03) / 0.44)) + 0.034 * cl01((y - 1.47) / 0.078) ** 2; // it hangs open: wider at the hem, spread at the collar
  loft(K, S, S.lv(1.03, 1.548, [1.075]), openCols(S, edge), (y) => (y < 1.075 ? C.panel : C.base), { wrap: true });
  const I = openFront(K, S, edge, 1.03, 1.548, C.white);
  bar(K, I, [-0.07, 1.528], [0.07, 1.528], 0.016, C.cream, 0.003, { rim: false, step: 0.03 }); // the tee's collar
  // placket + brass buttons down their right front, the buttonholes down their left
  panel(K, S, (s, t) => { const y = mix(1.078, 1.47, t); return [edge(y) + 0.002 + s * 0.028, y]; }, 1, 6, C.panel, 0.003, { rim: false });
  for (let y = 1.105; y < 1.46; y += 0.068) { stud(K, S.ff(edge(y) + 0.016, y, 0.003), 0.012, C.brass); bar(K, S, [-edge(y) - 0.008, y], [-edge(y) - 0.026, y], 0.006, C.deep, 0.003, { rim: false }); }
  for (const sx of [-1, 1]) { // chest pockets: a patch, a pointed flap, a button; two seams running down from each to the waistband
    panel(K, S, rect(sx * 0.098, 1.298, sx * 0.178, 1.38), 2, 2, C.base, 0.004, { rim: C.seam });
    for (const k of [-1, 1]) panel(K, S, quad4([sx * 0.138, 1.352], [sx * (0.138 + k * 0.043), 1.37], [sx * (0.138 + k * 0.043), 1.402], [sx * 0.138, 1.402]), 1, 1, C.panel, 0.009);
    stud(K, S.ff(sx * 0.138, 1.37, 0.009), 0.01, C.brass);
    for (const x of [0.108, 0.168]) bar(K, S, [sx * x, 1.296], [sx * (x + 0.006), 1.078], 0.006, C.seam, 0.0025, { rim: false, step: 0.06 });
  }
  // back: a yoke seam, two seams down from it, tabs with buttons on the waistband
  bar(K, S, [-0.25, 1.432], [0.25, 1.432], 0.008, C.seam, 0.0025, { back: true, rim: false, step: 0.04 });
  for (const sx of [-1, 1]) {
    bar(K, S, [sx * 0.12, 1.428], [sx * 0.105, 1.078], 0.006, C.seam, 0.0025, { back: true, rim: false, step: 0.06 });
    panel(K, S, rect(sx * 0.13, 1.04, sx * 0.2, 1.066), 2, 1, C.base, 0.006, { back: true, rim: C.seam });
    stud(K, S.bf(sx * 0.142, 1.053, 0.006), 0.009, C.brass);
  }
  seam(K, S, 90, 1.078, 1.36); seam(K, S, 270, 1.078, 1.36);
  // the collar: folded down, longer to its two points at the front
  const a0 = S.ux(1.548, edge(1.548));
  collar(K, S, 1.548, (u) => 0.042 + 0.05 * front(u) ** 3, C.base, { a0, a1: -a0, n: 14, lift: 0.012, rim: C.seam, stand: 0.02 });
  return K.piece();
}
function jacketSleeve(part) {
  const K = new Kit(true);
  if (part === 'up') K.lathe([[0.001, -0.092], [0.06, -0.074], [0.085, -0.03], [0.088, 0.016], [0.087, 0.018, C.seam], [0.088, 0.026], [0.085, 0.028], [0.08, 0.2], [0.079, 0.288], [0.07, 0.318], [0.05, 0.33]], 12, C.base);
  else {
    K.lathe([[0.064, -0.03], [0.073, 0.02], [0.067, 0.138], [0.068, 0.14, C.panel], [0.069, 0.144, C.panel], [0.068, 0.196, C.panel], [0.059, 0.198, C.deep], [0.046, 0.184]], 12, C.base);
    K.cyl(0.008, 0.01, 0.008, 6, C.brass, T(0, -0.072, -0.17)); // cuff button (underneath: the back of the wrist with the arm down)
  }
  return K.piece('z');
}

// ------------------------------------------------------------ Suit: tailored, buttoned, over a white shirt and a red tie
// notch lapels and a collar, two buttons, a breast pocket with a pocket square, flapped hip pockets, the fronts cut
// away at the hem, a seam and a vent up the back, shirt cuffs and buttons at the wrists
function suitCut(F) { const e = 2.8; return [shell(F.rows([[0.965, 0.236, 0.17, 0.168], [1.06, 0.226, 0.165, 0.163], [1.15, 0.224, 0.165, 0.161], [1.3, 0.256, 0.176, 0.17], [1.42, 0.28, 0.172, 0.17], [1.488, 0.274, 0.152, 0.158], [1.526, 0.178, 0.118, 0.13], [1.548, 0.108, 0.094, 0.1]], 0.9, 0.014), e)]; }
function suitBody(F, lk, [S]) {
  const K = new Kit(true), X = 0.012; // the fronts overlap a touch to their right of centre
  const edge = (y) => (y > 1.27 ? 0.066 * cl01((y - 1.27) / 0.26) ** 0.9 : 0.055 * cl01((1.05 - y) / 0.085) ** 1.3); // the V down to the top button; cut away below the bottom one
  loft(K, S, S.lv(0.965, 1.548, [1.05, 1.27]), openCols(S, edge, X), C.base, { wrap: true });
  const I = openFront(K, S, edge, 1.06, 1.548, C.white, X); // the shirt (the trousers show in the cutaway)
  // tie: a knot, a blade widening down to its point
  K.box(0.042, 0.036, 0.02, C.red, I.ff(X, 1.512, 0.01));
  panel(K, I, quad4([X - 0.027, 1.33], [X + 0.027, 1.33], [X + 0.014, 1.498], [X - 0.014, 1.498]), 1, 3, C.red, 0.008, { rim: C.redd });
  panel(K, I, quad4([X, 1.282], [X, 1.282], [X + 0.027, 1.33], [X - 0.027, 1.33]), 1, 1, C.red, 0.008, { rim: C.redd });
  for (const sx of [-1, 1]) {
    panel(K, I, quad4([X + sx * 0.012, 1.522], [X + sx * 0.06, 1.492], [X + sx * 0.074, 1.532], [X + sx * 0.03, 1.552]), 1, 1, C.white, 0.007, { rim: C.cream }); // shirt collar points
    // lapel: from the top button up the V to its notch; the collar comes round from the back to meet it
    panel(K, S, quad4([X + sx * 0.004, 1.274], [X + sx * 0.004, 1.274], [X + sx * 0.132, 1.436], [X + sx * edge(1.45), 1.452]), 1, 4, C.panel, 0.01, { rim: C.seam });
    panel(K, S, quad4([X + sx * edge(1.462), 1.462], [X + sx * 0.122, 1.458], [X + sx * 0.142, 1.528], [X + sx * 0.078, 1.546]), 2, 2, C.panel, 0.011, { rim: C.seam });
    panel(K, S, rect(sx * 0.112, 1.078, sx * 0.205, 1.11), 2, 1, C.panel, 0.007, { rim: C.seam }); // hip pocket flaps
    bar(K, S, [sx * 0.19, 1.4], [sx * 0.165, 1.0], 0.006, C.seam, 0.0025, { back: true, rim: false, step: 0.07 }); // back side seams
  }
  collar(K, S, 1.548, 0.04, C.panel, { a0: 118 * DEG, a1: -118 * DEG, n: 10, lift: 0.011, rim: C.seam, stand: 0.016 });
  bar(K, S, [X + 0.006, 1.27], [X + 0.008, 1.05], 0.006, C.seam, 0.0025, { rim: false, step: 0.06 }); // where the fronts overlap
  for (const y of [1.245, 1.158]) stud(K, S.ff(X - 0.012, y, 0.002), 0.012, C.btn);
  bar(K, S, [-0.172, 1.386], [-0.092, 1.392], 0.013, C.seam, 0.004, { step: 0.04 }); // breast pocket + pocket square
  for (const [x, h] of [[-0.152, 0.03], [-0.128, 0.022]]) panel(K, S, quad4([x - 0.014, 1.394], [x + 0.014, 1.396], [x + 0.004, 1.396 + h], [x - 0.006, 1.394 + h]), 1, 1, C.white, 0.008, { rim: C.cream });
  bar(K, S, [0, 1.5], [0, 1.1], 0.006, C.seam, 0.0025, { back: true, rim: false, step: 0.06 }); // back seam, the vent under it
  bar(K, S, [0, 1.1], [0, 0.967], 0.014, C.deep, 0.003, { back: true, rim: false, step: 0.06 });
  return K.piece();
}
function suitSleeve(part) {
  const K = new Kit(true);
  if (part === 'up') K.lathe([[0.001, -0.092], [0.064, -0.076], [0.088, -0.034], [0.09, 0.008], [0.089, 0.01, C.seam], [0.09, 0.018], [0.087, 0.02], [0.076, 0.2], [0.075, 0.288], [0.068, 0.318], [0.05, 0.33]], 12, C.base);
  else {
    K.lathe([[0.062, -0.03], [0.069, 0.02], [0.063, 0.184], [0.055, 0.186, C.white], [0.055, 0.206, C.white], [0.047, 0.208, C.deep], [0.04, 0.192]], 12, C.base);
    for (const d of [0.132, 0.15, 0.168]) K.cyl(0.006, 0.0075, 0.007, 6, C.btn, T(0, -0.0655, -d)); // (underneath: the back of the wrist with the arm down)
  }
  return K.piece('z');
}

// ------------------------------------------------------------ Sash: a pageant sash over a bare chest
// from their left shoulder to their right hip, gold along both edges, a rosette with two tails on the hip, a gold pin
function sashBody(F) {
  const K = new Kit(true), S = F.bare(), n = 30, m = -1.3, hw = 0.082, lift = 0.012;
  // where the slanted plane y = c + m x cuts the body
  const cutY = (u, c) => { let y = 1.3; for (let i = 0; i < 14; i++) y = mix(y, Math.max(1.065, Math.min(1.546, c + m * S.p(y, u)[0])), 0.5); return y; };
  const offs = [-hw, -hw + 0.02, hw - 0.02, hw], P = (l) => (i, j) => { const u = (j / n) * TAU; return S.p(cutY(u, 1.31 + offs[i]), u, l); };
  const g = K.grid(3, n, P(lift), (i) => (i === 1 ? C.base : C.brass), radial, true), b = K.grid(3, n, P(0), null, radial, true);
  for (let j = 0; j < n; j++) { K.quad(g[0][j], g[0][j + 1], b[0][j + 1], b[0][j], C.brass, [0, -1, 0]); K.quad(g[3][j], g[3][j + 1], b[3][j + 1], b[3][j], C.brass, [0, 1, 0]); }
  // rosette + tails on their right hip, a pin on the chest
  const hy = cutY(96 * DEG, 1.31), hip = S.frame(hy, 96 * DEG, lift);
  for (const sx of [-1, 1]) { K.box(0.04, 0.15, 0.008, C.base, hip.clone().multiply(T(sx * 0.022, -0.085, 0.002, 0, 0, sx * 0.2))); K.box(0.042, 0.022, 0.01, C.brass, hip.clone().multiply(T(sx * 0.036, -0.15, 0.002, 0, 0, sx * 0.2))); }
  K.cyl(0.05, 0.056, 0.014, 8, C.brass, hip.clone().multiply(T(0, 0, 0.008, PI / 2))); K.cyl(0.03, 0.036, 0.014, 8, C.base, hip.clone().multiply(T(0, 0, 0.02, PI / 2))); K.ball(0.016, C.brass, hip.clone().multiply(T(0, 0, 0.03)), 6, 4);
  const py = cutY(190 * DEG, 1.31);
  K.box(0.034, 0.034, 0.008, C.brass, S.frame(py, 190 * DEG, lift + 0.004).multiply(T(0, 0, 0, 0, 0, PI / 4))); K.box(0.016, 0.016, 0.012, C.white, S.frame(py, 190 * DEG, lift + 0.006).multiply(T(0, 0, 0, 0, 0, PI / 4)));
  return K.piece();
}

// a skirt's rows with room for the thighs under it (the legs slider and fat thicken them; trousers are thicker than
// skin): everything from the hips down is at least that wide and deep
const legKey = (lk, F) => `${Math.max(0, Math.min(JOKE_MAX, lk.bigLegs | 0))}${lk.bottom === 'pants' || lk.bottom === 'overalls' ? 1 : 0}`;
function legRoom(rows, lk, F, trousers) {
  const kl = 1 + JOKE.legs * Math.max(0, Math.min(JOKE_MAX, lk.bigLegs | 0)) + JOKE.fat * 0.45 * F.ft, r = (trousers ? 0.1 : 0.076) * kl + 0.014;
  return rows.map(([y, w, f, b]) => { const q = r * (y > 0.97 ? 0.82 : 1); return y > 1.005 ? [y, w, f, b] : [y, Math.max(w, 0.1 + q), Math.max(f, q * 1.05), Math.max(b, q * 1.05)]; }); // (their rounded tops come up to the waist)
}

// ------------------------------------------------------------ Maid Dress
// black (or your colour) with a white apron: a fitted bodice, a pleated bell skirt with a ruffled petticoat under the
// hem, the apron (frilled bib, straps crossing down the back, a frilled skirt panel with a pocket), a white sash tied
// in a big bow behind, a ruffled collar with a pink ribbon, puff sleeves with frilled cuffs. bare legs get knee socks
// and strap shoes; with nothing on your head (or the Cat Ears) you also get the frilly headdress
function maidCut(F, lk) { const e = 2.3; return [shell(F.rows(legRoom([[0.6, 0.36, 0.36, 0.36], [0.7, 0.33, 0.33, 0.33], [0.86, 0.27, 0.27, 0.27], [0.95, 0.222, 0.218, 0.22], [1.0, 0.196, 0.188, 0.192], [1.1, 0.14, 0.132, 0.134], [1.2, 0.2, 0.148, 0.146], [1.32, 0.252, 0.164, 0.16], [1.42, 0.262, 0.158, 0.158], [1.49, 0.25, 0.136, 0.142], [1.525, 0.165, 0.108, 0.118], [1.548, 0.1, 0.09, 0.094]], lk, F, lk.bottom === 'pants' || lk.bottom === 'overalls'), 1, 0.012), e)]; }
function maidBody(F, lk, [S]) {
  const K = new Kit(true), n = 28, amp = (y) => 0.016 * cl01((1.04 - y) / 0.32), zig = (j) => (j % 2 ? 1 : -1);
  const sk = S.lv(0.6, 1.1);
  loft(K, S, sk, ring(n), (y) => (y < 0.62 ? C.panel : C.base), { wrap: true, lift: (i, j) => zig(j) * amp(sk[i]) }); // the pleated skirt
  loft(K, S, S.lv(1.1, 1.525), cols(S), C.base, { wrap: true });
  crewNeck(K, S, 1.525, 0.012, C.base, C.base);
  // petticoat: a white ruffle showing under the hem
  const Pt = shell([[0.566, S.at(0.6)[0] + 0.03, S.at(0.6)[1] + 0.03, S.at(0.6)[2] + 0.03], [0.632, S.at(0.632)[0] - 0.012, S.at(0.632)[1] - 0.012, S.at(0.632)[2] - 0.012]], 2.3);
  loft(K.t, Pt, [0.566, 0.6, 0.632], ring(n), C.frill, { wrap: true, lift: (i, j) => zig(j) * (i === 2 ? 0 : 0.014) });
  // apron skirt: a white panel down the front over the pleats, a frill round its edge, a pocket
  const ua = (j) => (139 + j * 10.25) * DEG, av = S.lv(0.69, 1.1), al = (y) => 0.01 + amp(y) * 1.25;
  loft(K.t, S, av, Array.from({ length: 9 }, (_, j) => ua(j)), C.white, { lift: (i) => al(av[i]) });
  loft(K.t, S, [0.648, 0.69], Array.from({ length: 17 }, (_, j) => ua(j / 2)), C.frill, { lift: (i, j) => al(0.69) + (i ? 0 : j % 2 ? 0.016 : -0.004) });
  for (const d of [139, 221]) panel(K, S, (s, t) => [(d + (s - 0.5) * 5) * DEG, mix(0.66, 1.09, t)], 1, 10, C.frill, (i) => al(mix(0.66, 1.09, i / 10)) + (i % 2 ? 0.012 : 0.002), { uy: true, rim: false });
  panel(K, S, rect(-0.15, 0.845, -0.07, 0.93), 2, 1, C.white, al(0.88) + 0.008, { rim: C.cream }); bar(K, S, [-0.152, 0.925], [-0.068, 0.925], 0.014, C.frill, al(0.9) + 0.012, { rim: false, step: 0.04 });
  // apron bib + its frills, straps over the shoulders crossing down the back
  panel(K, S, rect(-0.085, 1.2, 0.085, 1.4), 4, 3, C.white, 0.008);
  for (const sx of [-1, 1]) {
    panel(K, S, rect(sx * 0.085, 1.2, sx * 0.116, 1.4), 1, 8, C.frill, (i) => (i % 2 ? 0.02 : 0.006), { rim: false });
    bar(K, S, [sx * 0.07, 1.4], [sx * 0.106, 1.546], 0.036, C.white, 0.008, { step: 0.03 });
    bar(K, S, [sx * 0.106, 1.546], [sx * 0.036, 1.14], 0.036, C.white, 0.008, { back: true, step: 0.035 });
  }
  panel(K, S, rect(-0.085, 1.4, 0.085, 1.42), 8, 1, C.frill, (i, j) => (j % 2 ? 0.02 : 0.006), { rim: false });
  // the sash round the waist, tied in a big bow at the back
  loft(K, S, S.lv(1.078, 1.138, [1.105]), cols(S), C.white, { wrap: true, lift: 0.007 });
  const bow = S.bf(0, 1.11, 0.012);
  for (const sx of [-1, 1]) {
    K.ball(1, C.white, bow.clone().multiply(T(sx * 0.082, 0.02, 0.022, 0, sx * 0.2, sx * 0.42, 0.082, 0.05, 0.026)), 6, 4);
    bar(K, S, [sx * 0.024, 1.1], [sx * 0.085, 0.88], 0.052, C.white, (i) => 0.022 + amp(mix(1.1, 0.88, i / 5)), { back: true, step: 0.045 }); // its two tails, down over the pleats
    bar(K, S, [sx * 0.079, 0.9], [sx * 0.085, 0.88], 0.058, C.frill, 0.03 + amp(0.89), { back: true, rim: false });
  }
  K.box(0.05, 0.056, 0.05, C.frill, bow.clone().multiply(T(0, 0.008, 0.026)));
  // ruffled collar, a pink ribbon at the throat, two gold buttons
  collar(K, S, 1.548, 0.046, C.frill, { n: 20, lift: (i, j) => (j % 2 ? 0.02 : 0.005), stand: 0.008 });
  const rb = S.ff(0, 1.52, 0.022);
  for (const sx of [-1, 1]) { K.box(0.052, 0.036, 0.016, C.rose, rb.clone().multiply(T(sx * 0.03, 0, 0, 0, 0, sx * 0.35))); K.box(0.017, 0.058, 0.01, C.rose, rb.clone().multiply(T(sx * 0.015, -0.04, -0.002, 0, 0, sx * 0.3))); }
  K.ball(0.015, C.pink, rb.clone().multiply(T(0, 0, 0.004)), 6, 4);
  for (const y of [1.468, 1.428]) stud(K, S.ff(0, y, 0.008), 0.011, C.brass);
  return K.piece();
}
function maidSleeve() { // a short puff gathered into a frilled white cuff
  return new Kit().lathe([[0.001, -0.098], [0.07, -0.08], [0.104, -0.03], [0.108, 0.03], [0.092, 0.082], [0.064, 0.098], [0.062, 0.1, C.frill, 0.1], [0.072, 0.106, C.frill, 0.1], [0.07, 0.128, C.frill], [0.058, 0.13, C.deep], [0.05, 0.112]], 12, C.base).piece('z');
}
function maidSock() { return new Kit().lathe([[0.06, 0.092, C.frill, 0.1], [0.068, 0.1, C.frill, 0.1], [0.063, 0.112], [0.058, 0.2], [0.05, 0.38], [0.05, 0.402]], 10, C.white, { y: true }).piece('y'); }
function maidShoe() { // (says it's a box, like legPiece's shoes: wider with big legs, never longer)
  const g = new Kit().box(0.108, 0.066, 0.232, C.shoe, T(0, -0.43, -0.05)).box(0.112, 0.014, 0.032, C.shoe, T(0, -0.394, -0.1)).box(0.02, 0.016, 0.012, C.brass, T(0.05, -0.394, -0.1)).box(0.108, 0.02, 0.07, C.sole, T(0, -0.456, 0.03)).piece('y');
  g.g.type = 'BoxGeometry';
  return g;
}
function maidHeaddress(big) { // a frilly white crescent across the top of the head (head space), sized for the hair under it
  const K = new Kit(), cy = 0.15 + (big - 1) * 0.12, rx = 0.138 * big, ry = 0.176 * big, pts = [];
  for (let i = 0; i <= 10; i++) { const a = mix(-1.12, 1.12, i / 10); pts.push([Math.sin(a) * rx, cy + Math.cos(a) * ry, 0]); }
  K.tube(pts, 0.014, 4, C.white);
  for (let i = 0; i <= 8; i++) { const a = -1.05 + (i / 8) * 2.1; K.ball(0.027, C.frill, T(Math.sin(a) * rx, cy + Math.cos(a) * ry + 0.01, 0, 0, 0, -a, 1, 1.2, 0.5), 6, 4); }
  return new Kit().add(K, T(0, -0.01, -0.06, -0.32)).piece();
}

// ------------------------------------------------------------ bottoms
// the seat: waistband down to the crotch, cut to the hips (the two cheeks of a big butt still show through it)
const HIP_E = 2.6;
function hipCut(F, E, top = 1.084) { // E: a top's surface the waist has to go round (overalls)
  let rows = F.rows([[0.872, 0.14, 0.1, 0.106], [0.9, 0.19, 0.13, 0.138], [0.98, 0.2, 0.138, 0.144], ...(E ? [[1.02, 0.198, 0.137, 0.142]] : []), [1.05, 0.196, 0.136, 0.14], [top, 0.19, 0.133, 0.136]], 1, 0.014, true);
  if (E) { // (baggy down to the legs: no bucket rim. from the hips up it's sized for the top's hem, wherever that hangs)
    const wide = rows.map(([y, w, f, b]) => { if (y < 0.89) return [y, w, f, b]; const a = E.at(Math.max(y, 1.02)), k = y < 0.97 ? 0.006 : 0.016; return [y, Math.max(w, a[0] + k), Math.max(f, a[1] + k), Math.max(b, a[2] + k)]; });
    wide.lumps = rows.lumps; wide.gap = (E.rows.gap || rows.gap) + 0.016; rows = wide; // (round the outside of the top on a big butt too)
  }
  return shell(rows, HIP_E);
}
function shortsBody(F) {
  const K = new Kit(true), S = hipCut(F);
  loft(K, S, S.lv(0.872, 1.05), cols(S), C.base, { wrap: true });
  lid(K, S, 0.872, C.base, false); lid(K, S, 1.084, C.deep, true);
  rib(K, S, 1.05, 1.084, C.panel, 32); // elastic waistband
  for (const sx of [-1, 1]) { // drawstring: two cords out of the waistband, a knot
    K.tube([S.f(sx * 0.012, 1.066, 0.006), S.f(sx * 0.03, 1.03, 0.012), S.f(sx * 0.034, 0.975, 0.012)], 0.0062, 4, C.cream);
    K.box(0.014, 0.022, 0.014, C.cream, S.ff(sx * 0.034, 0.966, 0.012));
    panel(K, S, (s, t) => [(sx > 0 ? 90 : 270) * DEG + (s - 0.5) * 0.36, mix(0.866, 1.05, t)], 1, 3, C.hi, 0.002, { uy: true, rim: false }); // side stripe (carries on down the leg)
    bar(K, S, [sx * 0.105, 1.046], [sx * 0.178, 0.975], 0.008, C.seam, 0.003, { rim: false, step: 0.04 }); // pocket openings
  }
  K.box(0.03, 0.02, 0.016, C.cream, S.ff(0, 1.064, 0.006));
  panel(K, S, rect(0.05, 0.925, 0.15, 1.0), 3, 3, C.base, 0.005, { back: true, rim: C.seam }); // back pocket: a flap and a snap
  panel(K, S, rect(0.046, 0.985, 0.154, 1.012), 3, 1, C.panel, 0.009, { back: true }); stud(K, S.bf(0.1, 0.992, 0.009), 0.009, C.silver);
  return K.piece();
}
function pantsBody(F) {
  const K = new Kit(true), S = hipCut(F);
  loft(K, S, S.lv(0.872, 1.084, [1.05]), cols(S), (y) => (y > 1.05 ? C.panel : C.base), { wrap: true });
  lid(K, S, 0.872, C.base, false); lid(K, S, 1.084, C.deep, true);
  for (const d of [0, 38, 90, 152, 208, 270, 322]) K.box(0.016, 0.044, 0.006, C.seam, S.frame(1.067, d * DEG, 0.002)); // belt loops
  stud(K, S.ff(0, 1.067, 0.003), 0.012, C.brass);
  bar(K, S, [-0.016, 1.048], [-0.016, 0.945], 0.006, C.seam, 0.003, { rim: false, step: 0.04 }); bar(K, S, [-0.016, 0.945], [0.004, 0.918], 0.006, C.seam, 0.003, { rim: false }); // fly
  for (const sx of [-1, 1]) {
    bar(K, S, [sx * 0.098, 1.05], [sx * 0.15, 1.02], 0.006, C.seam, 0.003, { rim: false }); bar(K, S, [sx * 0.15, 1.02], [sx * 0.188, 0.972], 0.006, C.seam, 0.003, { rim: false }); // front pockets
    bar(K, S, [sx * 0.205, 1.04], [0, 1.006], 0.006, C.seam, 0.003, { back: true, rim: false, step: 0.04 }); // back yoke
    panel(K, S, quad4([sx * 0.052, 0.918], [sx * 0.15, 0.918], [sx * 0.156, 0.996], [sx * 0.046, 0.996]), 3, 3, C.base, 0.006, { back: true, rim: C.seam }); // back pockets, stitched
    bar(K, S, [sx * 0.058, 0.972], [sx * 0.101, 0.95], 0.006, C.tan, 0.008, { back: true, rim: false, step: 0.02 }); bar(K, S, [sx * 0.101, 0.95], [sx * 0.144, 0.972], 0.006, C.tan, 0.008, { back: true, rim: false, step: 0.02 });
  }
  panel(K, S, rect(0.058, 1.052, 0.112, 1.082), 1, 1, C.tan, 0.006, { back: true }); // the patch on the waistband
  return K.piece();
}
function skirtBody(F, lk) {
  const K = new Kit(true), e = 2.3, n = 28;
  const S = shell(F.rows(legRoom([[0.69, 0.3, 0.3, 0.3], [0.8, 0.262, 0.258, 0.262], [0.92, 0.218, 0.204, 0.208], [0.955, 0.208, 0.184, 0.188], [1.0, 0.196, 0.158, 0.162], [1.045, 0.19, 0.136, 0.14], [1.084, 0.188, 0.133, 0.136]], lk, F, false), 1, 0.022, true), e); // (it stands off a big butt: the pleats and the shorts under it need the room)
  const amp = (y) => 0.016 * cl01((1.035 - y) / 0.3), lv = S.lv(0.69, 1.045, [0.716, 0.738]);
  loft(K, S, lv, ring(n), (y) => (y > 0.716 && y < 0.738 ? C.hi : C.base), { wrap: true, lift: (i, j) => (j % 2 ? 1 : -1) * amp(lv[i]) }); // knife pleats, a stripe above the hem
  loft(K, S, S.lv(1.045, 1.084), cols(S), C.panel, { wrap: true, lift: 0.004 }); lid(K, S, 1.084, C.deep, true);
  stud(K, S.frame(1.064, 270 * DEG, 0.002), 0.011, C.btn); seam(K, S, 270, 0.9, 1.045);
  const pin = S.frame(0.85, 208 * DEG, amp(0.85) + 0.004).multiply(T(0, 0, 0, 0, 0, 0.16)); // a big kilt pin
  K.box(0.011, 0.085, 0.008, C.silver, pin); K.box(0.026, 0.02, 0.01, C.silver, pin.clone().multiply(T(0, 0.045, 0))); K.box(0.02, 0.012, 0.009, C.silver, pin.clone().multiply(T(0, -0.044, 0)));
  const U = shell(F.rows([[0.87, 0.15, 0.105, 0.112], [0.905, 0.186, 0.126, 0.134], [1.0, 0.184, 0.126, 0.132]], 1, 0.004, true), 3); // shorts underneath
  loft(K, U, U.lv(0.87, 1.0, [0.905]), cols(U), C.deep, { wrap: true }); lid(K, U, 0.87, C.deep, false);
  return K.piece();
}
// overalls: the seat goes round the outside of whatever top is tucked into it, the bib and straps lie on that top
function overallsBody(F, lk, E) {
  const K = new Kit(true), S = hipCut(F, E, 1.112), ST = C.tan;
  loft(K, S, S.lv(0.872, 1.112, [1.07]), cols(S), (y) => (y > 1.07 ? C.panel : C.base), { wrap: true });
  lid(K, S, 0.872, C.base, false); lid(K, S, 1.112, C.deep, true);
  bar(K, S, [-0.012, 1.066], [-0.012, 0.94], 0.006, ST, 0.003, { rim: false, step: 0.04 }); // fly stitching
  for (const sx of [-1, 1]) {
    bar(K, S, [sx * 0.085, 1.07], [sx * 0.14, 1.03], 0.006, ST, 0.003, { rim: false }); bar(K, S, [sx * 0.14, 1.03], [sx * 0.185, 0.97], 0.006, ST, 0.003, { rim: false }); // front pockets
    for (const y of [1.085, 1.035]) stud(K, S.frame(y, (sx > 0 ? 80 : 280) * DEG, 0.002), 0.014, C.brass); // side buttons
    panel(K, S, quad4([sx * 0.05, 0.918], [sx * 0.15, 0.918], [sx * 0.156, 1.0], [sx * 0.044, 1.0]), 3, 3, C.base, 0.006, { back: true, rim: C.panel }); // back pockets
    bar(K, S, [sx * 0.05, 0.992], [sx * 0.15, 0.992], 0.005, ST, 0.008, { back: true, rim: false, step: 0.025 });
  }
  // the bib: a pocket on it with a pencil in, brass buckles at its top corners
  const L = 0.018;
  panel(K, E, quad4([-0.122, 1.1], [0.122, 1.1], [0.102, 1.372], [-0.102, 1.372]), 4, 4, C.base, L, { rim: C.panel });
  bar(K, E, [-0.1, 1.362], [0.1, 1.362], 0.007, ST, L + 0.0015, { rim: false, step: 0.04 });
  for (const sx of [-1, 1]) bar(K, E, [sx * 0.112, 1.11], [sx * 0.094, 1.36], 0.006, ST, L + 0.0015, { rim: false, step: 0.05 });
  panel(K, E, rect(-0.062, 1.212, 0.062, 1.312), 2, 1, C.panel, L + 0.007, { rim: C.seam }); bar(K, E, [-0.062, 1.306], [0.062, 1.306], 0.007, ST, L + 0.0085, { rim: false, step: 0.04 });
  const pen = E.ff(-0.036, 1.33, L + 0.012).multiply(T(0, 0, 0, 0, 0, 0.14));
  K.cyl(0.011, 0.011, 0.12, 6, C.pencil, pen); K.cyl(0.0115, 0.0115, 0.014, 6, C.silver, pen.clone().multiply(T(0, 0.062, 0))); K.cyl(0.011, 0.011, 0.02, 6, C.eraser, pen.clone().multiply(T(0, 0.078, 0)));
  for (const sx of [-1, 1]) { // straps: up from the bib, over the shoulders, down the back into the back panel
    bar(K, E, [sx * 0.092, 1.35], [sx * 0.11, 1.546], 0.05, C.base, L, { rim: C.panel, step: 0.03 });
    bar(K, E, [sx * 0.11, 1.546], [sx * 0.058, 1.3], 0.05, C.base, L, { back: true, rim: C.panel, step: 0.035 });
    K.box(0.062, 0.044, 0.012, C.brass, E.ff(sx * 0.094, 1.362, L + 0.006)); K.box(0.03, 0.014, 0.016, C.sole, E.ff(sx * 0.094, 1.362, L + 0.008));
  }
  const by = F.bt ? Math.min(1.26, Math.max(1.1, 0.97 + (0.085 + JOKE.butt * F.bt) * 0.93 + 0.04)) : 1.1; // the back panel starts above a big butt
  panel(K, E, quad4([-0.125, by], [0.125, by], [0.082, 1.32], [-0.082, 1.32]), 3, 3, C.base, L, { back: true, rim: C.panel });
  bar(K, E, [-0.078, 1.31], [0.078, 1.31], 0.007, ST, L + 0.0015, { back: true, rim: false, step: 0.04 });
  return K.piece();
}
// legs: a thigh piece on the leg, a shin piece on the knee (so they bend where the mannequin does). sx: which leg
// (-1 = their left): the stripe and the tool pockets go on the outside. each has a ball at its top, so a bent joint
// stays covered
function legPiece(kind, part, sx) {
  const K = new Kit(part !== 'shoe'), boot = kind === 'overalls';
  if (part === 'shoe') { // what goes on the mannequin's plain shoe box: a sole, a toe cap, laces (overalls: work boots)
    const lace = boot ? C.pencil : C.white;
    K.box(0.108, 0.022, 0.234, boot ? C.sole : C.white, T(0, -0.452, -0.05)).box(0.104, boot ? 0.05 : 0.04, 0.062, boot ? C.sole : C.white, T(0, boot ? -0.432 : -0.436, -0.134));
    if (boot) K.box(0.108, 0.03, 0.07, C.sole, T(0, -0.448, 0.027));
    for (let i = 0; i < 3; i++) K.box(0.056, 0.007, 0.011, lace, T(0, -0.398, -0.03 - i * 0.027));
    const pc = K.piece('y');
    pc.g.type = 'BoxGeometry'; // (jokeBody widens a foot but doesn't lengthen it, and it knows a foot by its box: this says it's one)
    return pc;
  }
  // columns round the leg: a narrow one down the outside and one down the inside are the seams (0 = their right)
  const o = { y: true, sy: 1.05, angles: [-14, -4, 4, 14, 60, 120, 166, 176, 184, 194, 240, 300] }, out = sx > 0 ? 1 : 7, st = boot ? C.tan : C.seam;
  const seams = (from) => (i, j, k) => ((j === 1 || j === 7) && i >= from && k === C.base ? st : k);
  if (kind === 'shorts') { // wide legs to mid-thigh, hemmed, a stripe down the outside
    K.lathe([[0.001, -0.094], [0.076, -0.072], [0.098, -0.025], [0.101, 0.02], [0.107, 0.166], [0.108, 0.168, C.panel], [0.11, 0.172, C.panel], [0.11, 0.2, C.panel], [0.1, 0.202, C.deep], [0.086, 0.186]], 0, C.base, { ...o, cell: (i, j, k) => (Math.abs(j - out) < 2 && i > 1 && i < 5 ? C.hi : k) });
  } else if (part === 'thigh') {
    const w = boot ? 0.004 : 0;
    K.lathe([[0.001, -0.094], [0.074 + w, -0.072], [0.094 + w, -0.025], [0.096 + w, 0.02], [0.089 + w, 0.18], [0.08 + w, 0.34], [0.082 + w, 0.376], [0.076 + w, 0.44]], 0, C.base, { ...o, cell: seams(3) });
    if (boot && sx > 0) K.tube([[0.096, -0.1, 0.03], [0.124, -0.135, 0.004], [0.094, -0.17, -0.03]], 0.0065, 4, C.panel); // hammer loop
    if (boot && sx < 0) K.box(0.014, 0.13, 0.062, C.panel, T(-0.098, -0.2, 0.004, 0, 0, 0.04)).box(0.016, 0.008, 0.064, C.tan, T(-0.1, -0.137, 0.004)); // ruler pocket
  } else if (boot) { // straight work legs, knee patches, the cuffs rolled up (the paler inside of the denim)
    K.lathe([[0.001, -0.09], [0.05, -0.076], [0.083, -0.04], [0.087, 0], [0.083, 0.04], [0.077, 0.3], [0.079, 0.332], [0.085, 0.335, C.light], [0.088, 0.342, C.light], [0.088, 0.404, C.light], [0.079, 0.407, C.deep], [0.06, 0.39]], 0, C.base, { ...o, cell: seams(3) });
    K.box(0.1, 0.105, 0.016, C.panel, T(0, -0.045, -0.083, 0.03)); for (const y of [0.002, -0.092]) K.box(0.09, 0.006, 0.018, C.tan, T(0, y, -0.084, 0.03));
  } else { // pants: creased at the knee, hemmed over the shoe
    K.lathe([[0.001, -0.086], [0.05, -0.072], [0.079, -0.04], [0.083, 0], [0.079, 0.035], [0.071, 0.066], [0.075, 0.086], [0.066, 0.3], [0.068, 0.36], [0.071, 0.364, C.panel], [0.072, 0.397, C.panel], [0.064, 0.399, C.deep], [0.05, 0.386]], 0, C.base, { ...o, cell: seams(3) });
  }
  return K.piece('y');
}

// ------------------------------------------------------------ costume pieces (shared/costumes.js)
// a flat five-point paper star in a frame's xy plane (stuck on: it doesn't bend with the cloth)
const _s = V3(0, 0, 0);
function star(K, m, r, cell, rot = 0) {
  K = K.t || K;
  const P = (i) => { const a = rot + (i * PI) / 5, q = i % 2 ? r * 0.46 : r; _s.set(Math.sin(a) * q, Math.cos(a) * q, 0).applyMatrix4(m); return [_s.x, _s.y, _s.z]; };
  _s.set(0, 0, 0).applyMatrix4(m);
  const c = [_s.x, _s.y, _s.z];
  for (let i = 0; i < 10; i++) K.tri(c, P(i + 1), P(i), cell);
}
// a whistle on a cord round the neck, lying on the chest
function whistle(K, S, cord, body) {
  for (const sx of [-1, 1]) K.tube([S.f(sx * 0.075, S.y1 - 0.012, 0.008), ...[0.25, 0.5, 0.75].map((t) => S.f(mix(sx * 0.064, 0.016, t), mix(1.5, 1.39, t), 0.01)), S.f(0.012, 1.386, 0.012)], 0.005, 4, cord); // (points close enough to ride over a bust)
  const m = S.ff(0.012, 1.368, 0.014).multiply(T(0, 0, 0, 0, 0, 0.35));
  K.box(0.046, 0.026, 0.02, body, m).box(0.022, 0.016, 0.016, body, m.clone().multiply(T(0.03, 0.006, 0))).box(0.012, 0.008, 0.022, C.ink, m.clone().multiply(T(0.004, 0.012, 0)));
  K.cyl(0.013, 0.013, 0.021, 8, body, m.clone().multiply(T(-0.014, -0.004, 0, PI / 2)));
}

// ------------------------------------------------------------ Lifeguard Tank: a singlet with white binding
// deep armholes, a scooped neck (lower at the front), straps over the shoulders, a life ring printed on the chest,
// a whistle on a cord
function tankCut(F) { const e = 2.4; return [shell(F.rows([[1.02, 0.218, 0.157, 0.161], [1.09, 0.21, 0.152, 0.154], [1.2, 0.218, 0.15, 0.15], [1.32, 0.248, 0.16, 0.158], [1.4, 0.256, 0.158, 0.156], [1.47, 0.236, 0.14, 0.144], [1.515, 0.196, 0.12, 0.126], [1.545, 0.168, 0.106, 0.114]], 0.95, 0.011), e)]; }
function tankBody(F, lk, [S]) {
  const K = new Kit(true), y0 = 1.38, y1 = S.y1, W = S.at(y0)[0], so = 0.146, si = 0.088; // (so, si: a strap's outer and inner edge at the top)
  loft(K, S, S.lv(1.02, y0 + 0.008, [1.045]), cols(S), (y) => (y < 1.045 ? C.panel : C.base), { wrap: true });
  for (const back of [false, true]) for (const sx of [-1, 1]) { // above the armpits: front and back each narrow to two straps
    const t0 = back ? 0.62 : 0.3, Y = (t) => mix(y0, y1, t), xo = (t) => so + (W - so) * (1 - t) ** 2.4, xi = (t) => (t <= t0 ? 0 : si * ((t - t0) / (1 - t0)) ** 0.6);
    K.solid(() => panel(K, S, (s, t) => [sx * mix(xi(t), xo(t), s), Y(t)], 3, 6, C.base, 0.001, { back, rim: false }));
    panel(K, S, (s, t) => [sx * (xo(t) - 0.016 * s), Y(t)], 1, 6, C.white, 0.004, { back, rim: false }); // white binding round the armhole...
    panel(K, S, (s, t) => { const q = mix(t0, 1, t); return [sx * (xi(q) + 0.016 * s), Y(q)]; }, 1, 4, C.white, 0.004, { back, rim: false }); // ...and the neck
  }
  for (const sx of [-1, 1]) { const P = (x, b) => S.p(y1, S.ux(y1, sx * x, b)); K.quad(P(si), P(so), P(so, true), P(si, true), C.base, [0, 1, 0]); } // the straps meet over the shoulders
  panel(K, S, (s, t) => { const r = mix(0.027, 0.054, s), a = t * TAU; return [Math.sin(a) * r, 1.262 + Math.cos(a) * r]; }, 1, 12, (i) => ((S.lumpy ? i >> 1 : i) % 3 === 1 ? C.deep : C.white), 0.004, { rim: false }); // the life ring
  seam(K, S, 90, 1.05, 1.36); seam(K, S, 270, 1.05, 1.36);
  whistle(K, S, C.white, C.pencil);
  return K.piece();
}

// n columns round a shell evenly spaced by the direction they point from the body's middle (not by its own angle),
// each a function of the height (the shell's width and depth change with it)
function evenCols(S, n) {
  const k = 2 / S.e;
  return Array.from({ length: n }, (_, j) => {
    const th = (j / n) * TAU, h = th % PI > PI / 2 ? PI - (th % PI) : th % PI; // (the direction's angle off the back / front line)
    return (y) => { const [w, f, b] = S.at(y), d = Math.cos(th) > 0 ? b : f, q = Math.atan(((Math.tan(Math.min(h, PI / 2 - 1e-6)) * d) / w) ** (1 / k)); return th <= PI / 2 ? q : th <= PI ? PI - q : th <= 1.5 * PI ? PI + q : TAU - q; };
  });
}

// ------------------------------------------------------------ Referee Shirt: stripes, in the shirt's colour and white
// a fold-down collar and a short placket, a chest pocket with a yellow card in it, a whistle. the shoulders, hem and
// cuffs are the plain colour
function refBody(F, lk, [S]) {
  // a stripe a column, twice the columns of a plain top. over a belly / bust / butt the columns go round evenly by
  // direction instead (the shell's squareness and the lump together would stretch the front ones into blocks), twice as
  // many again, two to a stripe
  const K = new Kit(true), us = S.lumpy ? evenCols(S, 64) : DENSE, st = S.lumpy ? 2 : 1;
  loft(K, S, S.lv(1.015, 1.525, [1.04, 1.468]), us, (y, u, i, j) => (y < 1.04 || y > 1.468 || ((j / st) | 0) % 2 === 0 ? C.base : C.white), { wrap: true });
  crewNeck(K, S, 1.525, 0.02, C.base, C.base);
  const a0 = S.ux(1.548, 0.024);
  collar(K, S, 1.548, (u) => 0.034 + 0.034 * front(u) ** 3, C.base, { a0, a1: -a0, n: 14, lift: 0.011, rim: C.seam, stand: 0.014 });
  panel(K, S, rect(-0.017, 1.43, 0.017, 1.522), 1, 2, C.base, 0.004, { rim: C.seam }); // placket
  for (const y of [1.452, 1.494]) stud(K, S.ff(0, y, 0.004), 0.009, C.white, 0.006);
  panel(K, S, rect(-0.172, 1.3, -0.096, 1.384), 2, 2, C.base, 0.006, { rim: C.seam }); // chest pocket (their left), a yellow card in it
  K.box(0.05, 0.075, 0.005, C.pencil, S.ff(-0.134, 1.404, 0.004).multiply(T(0, 0, 0, 0, 0, -0.1)));
  whistle(K, S, C.ink, C.silver);
  return K.piece();
}
function refSleeve() {
  return new Kit().lathe([[0.001, -0.09], [0.058, -0.072], [0.081, -0.03], [0.085, 0.02], [0.082, 0.112], [0.082, 0.118, C.panel], [0.084, 0.122, C.panel], [0.084, 0.152, C.panel], [0.074, 0.154, C.deep], [0.062, 0.134]], 12, C.base, { cell: (i, j, k) => (k === C.base && i > 1 && j % 2 ? C.white : k) }).piece('z');
}

// ------------------------------------------------------------ Bathrobe (the Budget Wizard's robe)
// knee length, wrapped left over right with a shawl collar and a V of bare chest, a belt with a knot and two ends,
// patch pockets, wide sleeves with turned-back cuffs. paper stars stuck all over it, one of them with tape
function robeCut(F, lk) { const e = 2.5; return [shell(F.rows(legRoom([[0.57, 0.31, 0.275, 0.285], [0.75, 0.285, 0.25, 0.26], [0.95, 0.248, 0.2, 0.208], [1.06, 0.232, 0.176, 0.178], [1.11, 0.226, 0.17, 0.17], [1.2, 0.236, 0.172, 0.17], [1.33, 0.266, 0.18, 0.176], [1.43, 0.28, 0.172, 0.172], [1.495, 0.268, 0.152, 0.158], [1.53, 0.178, 0.12, 0.132], [1.552, 0.116, 0.098, 0.104]], lk, F, lk.bottom === 'pants' || lk.bottom === 'overalls'), 0.8, 0.014), e)]; }
function robeBody(F, lk, [S]) {
  const K = new Kit(true), X = 0.022, y1 = S.y1; // (X: the front edge runs a touch to their right of centre)
  const edge = (y) => 0.088 * cl01((y - 1.2) / 0.34) ** 1.15; // the V of the neck, closed from there down
  loft(K, S, S.lv(S.y0, y1, [0.605]), openCols(S, edge, X), (y) => (y < 0.605 ? C.light : C.base), { wrap: true });
  for (const sx of [-1, 1]) { // shawl collar down both edges of the V, pockets, the belt's two ends
    panel(K, S, (s, t) => { const y = mix(1.17, 1.535, t); return [X + sx * (edge(y) + s * mix(0.03, 0.062, t)), y]; }, 1, 6, C.light, 0.012, { rim: C.panel });
    panel(K, S, rect(sx * 0.095, 0.85, sx * 0.205, 0.985), 2, 2, C.base, 0.006, { rim: C.seam });
    bar(K, S, [sx * 0.093, 0.978], [sx * 0.207, 0.978], 0.016, C.light, 0.008, { step: 0.04 });
    bar(K, S, [-0.05 + sx * 0.012, 1.1], [-0.06 + sx * 0.034, sx > 0 ? 0.87 : 0.91], 0.032, C.panel, 0.013, { step: 0.05 });
  }
  collar(K, S, y1, 0.052, C.light, { a0: 122 * DEG, a1: -122 * DEG, n: 10, lift: 0.012, rim: C.panel, stand: 0.014 });
  bar(K, S, [X, 1.2], [X + 0.034, 0.61], 0.008, C.seam, 0.003, { rim: false, step: 0.06 }); // where it wraps over
  loft(K, S, S.lv(1.084, 1.132), cols(S), C.panel, { wrap: true, lift: 0.008 }); // the belt, knotted off-centre
  K.box(0.056, 0.05, 0.034, C.panel, S.ff(-0.05, 1.107, 0.02));
  // the stars: [x, y, size, turn], front then back
  for (const [x, y, r, a] of [[0.15, 1.35, 0.036, 0.3], [-0.165, 1.255, 0.028, 1.1], [0.145, 0.8, 0.042, 0.7], [-0.13, 0.69, 0.032, 0.2], [0.215, 1.03, 0.026, 1.5], [-0.2, 1.04, 0.022, 0.5]]) star(K, S.ff(x, y, 0.007), r, C.pencil, a);
  for (const [x, y, r, a] of [[0.01, 1.34, 0.064, 0.15], [-0.15, 1.02, 0.036, 0.9], [0.14, 0.82, 0.042, 0.4], [0.165, 1.2, 0.028, 1.2], [-0.09, 0.68, 0.032, 0.6], [-0.17, 1.42, 0.024, 0.2]]) star(K, S.bf(x, y, 0.007), r, C.pencil, a);
  K.box(0.05, 0.016, 0.004, C.silver, S.bf(0.03, 1.375, 0.009).multiply(T(0, 0, 0, 0, 0, 0.5))); // (that one fell off once)
  return K.piece();
}
function robeSleeve(part) {
  const K = new Kit(true);
  if (part === 'up') {
    K.lathe([[0.001, -0.092], [0.062, -0.076], [0.09, -0.03], [0.096, 0.02], [0.093, 0.2], [0.095, 0.288], [0.08, 0.318], [0.05, 0.33]], 12, C.base);
    for (const sx of [-1, 1]) star(K, T(sx * 0.098, 0.004, -0.135, 0, sx * PI / 2, 0), 0.03, C.pencil, 0.4);
  } else K.lathe([[0.07, -0.03], [0.085, 0.02], [0.09, 0.1], [0.097, 0.168], [0.1, 0.172, C.light], [0.102, 0.178, C.light], [0.102, 0.216, C.light], [0.088, 0.218, C.deep], [0.05, 0.19]], 12, C.base);
  return K.piece('z');
}

// ------------------------------------------------------------ Hot Dog Suit
// a sausage from over your head down to your thighs with a hole for the face, lying in a bun that wraps round your back
// (split down the front, where the sausage sits, so your arms and legs poke out), mustard down the front, grill marks
// up the back of the hood. the sausage is the suit's colour. it grows with a big head, a belly and anything else: looks
// only, the hitboxes are the plain mannequin's
function hotdogCut(F, lk) {
  const hs = 1 + JOKE.head * F.hd, up = (y) => (y > 1.6 ? 1.6 + (y - 1.6) * hs : y);
  const fit = (src, gap) => {
    const rows = F.rows(legRoom(src, lk, F, lk.bottom === 'pants' || lk.bottom === 'overalls').map(([y, ...r]) => [up(y), ...r]), 0.6, gap); // (room for big legs at the bottom)
    for (const r of rows) { const h = F.head(r[0]); if (h[0]) { r[1] = Math.max(r[1], h[0] + 0.05); r[2] = Math.max(r[2], h[1] + 0.062); r[3] = Math.max(r[3], h[1] + 0.05); } } // room for the head in it
    return rows;
  };
  // [0] the sausage; [1] the bun round its back (only its size is used: the vest and the back items go round it)
  return [shell(fit([[0.74, 0.2, 0.16, 0.165], [0.8, 0.232, 0.186, 0.19], [0.95, 0.25, 0.205, 0.208], [1.3, 0.258, 0.215, 0.215], [1.6, 0.252, 0.21, 0.21], [1.8, 0.24, 0.2, 0.2], [1.92, 0.205, 0.172, 0.172], [1.995, 0.14, 0.118, 0.118], [2.035, 0.055, 0.046, 0.046]], 0.02), 2.2),
    shell(fit([[0.86, 0.28, 0.15, 0.23], [0.94, 0.32, 0.17, 0.27], [1.3, 0.345, 0.18, 0.3], [1.62, 0.335, 0.18, 0.29], [1.735, 0.28, 0.16, 0.24]], 0.045), 2.1)];
}
function hotdogBody(F, lk, [S, B]) {
  const K = new Kit(true), hs = 1 + JOKE.head * F.hd, hy = (d) => 1.6 + d * hs, f0 = hy(0.04), f1 = hy(0.27), A = 23 * DEG;
  // the sausage: rounded off over the head, a hole to look out of, open underneath for the legs, a shine down one side
  const us = [...cols(S).filter((a) => a < PI - A - 0.05), PI - A, PI + A, ...cols(S).filter((a) => a > PI + A + 0.05)], mid = us.indexOf(PI - A), lv = S.lv(S.y0, S.y1, [f0, f1]);
  loft(K, S, lv, us, (y, u, i, j) => (j === mid && y > f0 && y < f1 ? null : j === mid - 2 && y > 0.92 && y < f0 ? C.hi : C.base), { wrap: true });
  lid(K, S, S.y1, C.base, true); lid(K, S, S.y0, C.deep, false);
  K.solid(() => K.ball(0.028, C.seam, T(0, S.y1 + 0.012, 0), 6, 4)); // the knot at the end
  { // the sides of the face hole, back to the face
    const ys = lv.filter((y) => y > f0 - 1e-6 && y < f1 + 1e-6), edge = [...ys.map((y) => S.p(y, PI + A)), ...ys.slice().reverse().map((y) => S.p(y, PI - A))], c = S.p((f0 + f1) / 2, PI), back = (p) => [p[0] * 0.95, p[1], p[2] + 0.06];
    edge.forEach((a, i) => { const b = edge[(i + 1) % edge.length]; K.quad(a, b, back(b), back(a), C.deep, [c[0] - (a[0] + b[0]) / 2, c[1] - (a[1] + b[1]) / 2, 0]); });
  }
  { // mustard, squeezed on in a hurry (more points over a belly or a bust, so it rides over them)
    const pts = [], sub = S.lumpy ? 3 : 1, zig = (q) => { const a = Math.floor(q), t = q - a; return mix(Math.round(Math.sin(a * PI / 2)), Math.round(Math.sin((a + 1) * PI / 2)), t) * 0.07; };
    for (let i = 0, y = f0 - 0.07; y > S.y0 + 0.14 - 1e-6; i++, y -= 0.055 / sub) pts.push(S.f(zig(i / sub), y, 0.017));
    K.tube(pts, 0.016, 5, C.sauce);
  }
  for (const y of [0.02, 0.1, 0.18]) bar(K, S, [-0.085, hy(y) - 0.022], [0.085, hy(y) + 0.022], 0.022, C.seam, 0.004, { back: true, rim: false, step: 0.05 }); // grill marks, up the back of the hood
  // the bun: one piece round the back from side to side, two fat lobes with a crease down the middle (where it's
  // hinged), a thick lip at the split and rounded off top and bottom. pale crumb where it's cut, sesame seeds
  const ds = [-84, -79, -70, -58, -44, -28, -12, 0, 12, 28, 44, 58, 70, 79, 84], n = ds.length - 1, m = 10, T0 = 0.12;
  const ys = Array.from({ length: m + 1 }, (_, i) => mix(B.y0, B.y1, (1 - Math.cos((i / m) * PI)) / 2)); // (closer together at the ends, where it rounds off)
  const k = (y, d) => { const a = Math.abs(d); return (a < 70 ? 0.74 + 0.26 * Math.sin((a / 70) * PI / 2) : 0.7 + 0.3 * Math.cos(((a - 70) / 14) * PI / 2) ** 0.5) * (0.45 + 0.55 * Math.sin(cl01((y - B.y0) / (B.y1 - B.y0)) * PI) ** 0.4); }; // (the lobes stick out past the sausage at the sides)
  const at = (y, d, l = 0) => S.p(y, d * DEG, T0 * k(y, d) + l);
  K.grid(m, n, (i, j) => at(ys[i], ds[j]), (i) => (i === 0 || i === m - 1 ? C.bunm : C.bun), radial); // (browner where it rounds off at the ends)
  for (const j of [0, n]) for (let i = 0; i < m; i++) K.quad(at(ys[i], ds[j]), at(ys[i + 1], ds[j]), S.p(ys[i + 1], ds[j] * DEG), S.p(ys[i], ds[j] * DEG), C.crumb, [0, 0, -1]); // the split
  for (const i of [0, m]) for (let j = 0; j < n; j++) K.quad(at(ys[i], ds[j]), at(ys[i], ds[j + 1]), S.p(ys[i], ds[j + 1] * DEG), S.p(ys[i], ds[j] * DEG), C.crumb, [0, i ? 1 : -1, 0]);
  for (const [y, d, r] of [[1.5, -30, 0.4], [1.42, 52, 1.2], [1.3, -60, 0.2], [1.2, 30, 0.9], [1.1, -46, 1.4], [1.02, 64, 0.6], [1.36, 20, 0.1], [1.58, 44, 0.8], [0.98, -22, 1.1], [1.26, 70, 0.3], [1.62, -50, 1.5], [1.12, 12, 0.7], [1.44, -10, 1.3]]) {
    const p = at(y, d, 0.002); K.box(0.024, 0.013, 0.008, C.cream, T(p[0], p[1], p[2], 0, d * DEG, r)); // seeds
  }
  return K.piece();
}

// ------------------------------------------------------------ costume accessories (head / face / back)
// built here like the clothes (one mesh each, + trim), put on by models.js addAccessories. head space: the egg's
// middle is y 0.14, its top 0.31, the face is at z -0.13
function strawHat() { // a wide straw sun hat with a band in your colour, pushed back a bit
  const H = new Kit().lathe([[0.001, 0], [0.11, 0.006], [0.146, 0.03], [0.152, 0.085], [0.153, 0.087, C.base], [0.154, 0.118, C.base], [0.152, 0.12], [0.154, 0.135], [0.2, 0.14, C.strawd], [0.245, 0.148], [0.29, 0.162, C.strawd], [0.3, 0.172], [0.292, 0.178, C.strawd], [0.154, 0.15, C.strawd], [0.14, 0.135]], 14, C.straw, { y: true });
  return new Kit().add(H, T(0, 0.392, 0.014, 0.1, 0, 0.04)).piece();
}
function wizHat() { // a cardboard cone taped into shape, its tip gone soft, a brim cut from the same box, paper stars
  const K = new Kit(true), M0 = T(0, 0.238, 0.012, 0.13, 0, -0.06), at = (p) => { _s.set(p[0], p[1], p[2]).applyMatrix4(M0); return [_s.x, _s.y, _s.z]; };
  K.solid(() => K.tube([[0, 0, 0], [0, 0.2, 0.004], [0.012, 0.36, 0.014], [0.05, 0.45, 0.03], [0.095, 0.475, 0.04]].map(at), [0.158, 0.098, 0.05, 0.026, 0.008], 9, C.card));
  K.add(new Kit().lathe([[0.15, 0, C.cardd], [0.245, 0.004], [0.25, 0.012, C.cardd], [0.15, 0.01, C.cardd]], 12, C.card, { y: true }), M0.clone().multiply(T(0, 0.006, 0)));
  // on the cone at height h, d degrees round from the front, lying on its slope
  const on = (h, d, lift = 0.003) => { const r = 0.158 - 0.3 * h + lift, a = d * DEG; return M0.clone().multiply(T(Math.sin(a) * r, h, -Math.cos(a) * r, 0, PI - a, 0)).multiply(T(0, 0, 0, -0.29)); };
  for (const [h, d, r, a] of [[0.075, 18, 0.034, 0.2], [0.17, -32, 0.026, 0.9], [0.1, 105, 0.03, 0.5], [0.16, 205, 0.026, 1.3], [0.065, 262, 0.03, 0.1], [0.245, 70, 0.02, 0.7], [0.07, -60, 0.024, 1.6]]) star(K, on(h, d), r, C.pencil, a);
  K.box(0.007, 0.27, 0.003, C.cardd, on(0.13, 172, 0.001)); // the seam up the back where it's rolled shut...
  for (const [h, w, r] of [[0.03, 0.07, 0.12], [0.12, 0.06, -0.2], [0.21, 0.045, 0.3]]) K.box(w, 0.024, 0.004, C.tape, on(h, 172, 0.003).multiply(T(0, 0, 0, 0, 0, r))); // ...and the masking tape holding it
  return K.piece();
}
function fakeBeard() { // cotton wool on an elastic: a bib of fluff from the nose to the chest, the string up over the ears
  const K = new Kit(), z = -0.128;
  for (const [x, y, dz, r, sy] of [[0, 0.03, -0.014, 0.062, 1.1], [-0.052, 0.045, 0, 0.05, 1], [0.052, 0.045, 0, 0.05, 1], [-0.032, -0.035, -0.03, 0.055, 1.15], [0.032, -0.035, -0.03, 0.055, 1.15], [0, -0.105, -0.05, 0.048, 1.3], [0, -0.17, -0.058, 0.03, 1.4]]) K.ball(1, C.white, T(x, y, z + dz, 0, 0, 0, r, r * sy, r * 0.62), 6, 4);
  for (const sx of [-1, 1]) {
    K.ball(1, C.cream, T(sx * 0.04, 0.093, z - 0.014, 0, 0, sx * 0.3, 0.046, 0.019, 0.022), 6, 4); // the moustache bit
    K.tube([[sx * 0.085, 0.07, z + 0.03], [sx * 0.119, 0.12, -0.04], [sx * 0.123, 0.15, 0.04], [sx * 0.09, 0.15, 0.116], [0, 0.146, 0.137]], 0.004, 4, C.ink);
  }
  return K.piece();
}
function sunscreen() { // a stripe of it across the nose they don't have
  const K = new Kit().box(0.062, 0.03, 0.02, C.frill, T(0, 0.148, -0.134, 0.05, 0, 0.06)).box(0.026, 0.024, 0.016, C.frill, T(0.004, 0.124, -0.132, 0.05, 0, 0.06)); // the nose stripe..
  for (const sx of [-1, 1]) K.box(0.034, 0.016, 0.012, C.frill, T(sx * 0.06, 0.122 + sx * 0.004, -0.116, 0, -sx * 0.5, sx * 0.2)); // ..and a smear on each cheek
  const pc = K.piece();
  pc.flat = true; // (too small for an outline of its own)
  return pc;
}
// the rescue float: a fat torpedo slung across the back on a rope that goes over one shoulder and round the body.
// E: the torso with its top on (fitOf dressed), so the float rests on the back and the rope rides over a belly or a bust
function rescueFloat(E) {
  const K = new Kit(true), F2 = new Kit(), c = [-0.01, 1.285], dir = [-Math.sin(0.62), -Math.cos(0.62)], L = 0.012; // (dir: from its middle to its bottom end)
  F2.lathe([[0.001, -0.3], [0.046, -0.286], [0.082, -0.24], [0.098, -0.17], [0.1, -0.16, C.white], [0.1, -0.128], [0.1, 0.1, C.white], [0.096, 0.132], [0.088, 0.2], [0.07, 0.262], [0.04, 0.29], [0.001, 0.298]], 10, C.buoy, { sy: 0.62 });
  for (const sx of [-1, 1]) F2.box(0.014, 0.034, 0.21, C.redd, T(sx * 0.097, 0, 0.015)); // the grips moulded down both edges
  let zb = 0; for (let t = -0.27; t < 0.28; t += 0.09) zb = Math.max(zb, E.b(c[0] + dir[0] * t, c[1] + dir[1] * t)[2]); // (on the furthest-out bit of back under it)
  const M = T(c[0], c[1], zb + 0.064, 0, 0, -0.62).multiply(T(0, 0, 0, -PI / 2)); // on its end, leaning across the back, its flat side to you
  K.solid(() => K.add(F2, M));
  const end = (d) => { _s.set(0, 0, -d).applyMatrix4(M); return [_s.x, _s.y, _s.z + 0.01]; };
  const fr = Array.from({ length: 8 }, (_, i) => E.f(mix(0.1, -0.14, i / 7), mix(1.47, 1.12, i / 7), L)); // down the front, close enough together to ride over things
  const side = [235, 262, 290].map((d) => E.p(1.1, d * DEG, L));
  K.tube([end(0.27), E.b(0.13, 1.49, L), [0.118, Math.max(1.556, E.y1 + 0.006), 0], E.f(0.11, 1.52, L), ...fr, ...side, E.b(-0.17, 1.1, L), end(-0.27)], 0.009, 5, C.white);
  K.box(0.03, 0.04, 0.02, C.brass, E.ff(0.031, 1.37, L + 0.004).multiply(T(0, 0, 0, 0, 0, 0.55))); // the buckle
  return K.piece();
}
const ACCS = { strawhat: strawHat, wizhat: wizHat, fakebeard: fakeBeard, sunscreen, float: rescueFloat };
// parent: the head (hats, faces) or the body (back). col: the player's colour. lk: the look (the float is fitted to the
// body and the top it's on). false: not ours
export function wearAcc(parent, id, col, lk = {}) {
  const make = typeof id === 'string' && Object.hasOwn(ACCS, id) && ACCS[id];
  if (!make) return false;
  if (id === 'float') { // cut for the body + top, like the clothes
    const F = fitOf(lk), top = topOf(lk.top || 'tank') ? lk.top || 'tank' : 'tank';
    wear(parent, cut(`float|${cutKey(top, lk, F)}`, () => make(F.dressed(TOPS[top].cut(F, lk)))), cloth(col));
  } else wear(parent, limb(`acc:${id}`, make), cloth(col));
  return true;
}

// ------------------------------------------------------------ putting them on
// cut(F, lk) -> the garment's shells (the first is its main surface: overalls lie their bib on it). body(F, lk, shells)
// -> the torso piece. sleeve(part, left) -> an arm piece. key: what else changes the cut. cap: the colour the
// mannequin's shoulder balls take (they poke out of a sleeve when the arms slider fattens them). dress: it covers the
// hips, so the bottom's seat is left off (trouser legs still show). own / thick: see topOwn, topThick
const TOPS = {
  tank: { cut: () => [], body: sashBody },
  tee: { cut: teeCut, body: teeBody, sleeve: teeSleeve, long: false, cap: 1 },
  hoodie: { cut: hoodieCut, body: hoodieBody, sleeve: hoodieSleeve, cap: 1, key: (lk, F) => `${F.hd}${covered(lk) ? 1 : 0}` },
  jacket: { cut: jacketCut, body: jacketBody, sleeve: jacketSleeve, cap: 1 },
  suit: { cut: suitCut, body: suitBody, sleeve: suitSleeve, cap: 1 },
  runner: { cut: runnerCut, body: runnerBody, sleeve: runnerSleeve, cap: FIXED.ink, pocket: true, key: (lk, F) => `${F.hd}${covered(lk) ? 1 : 0}` },
  maid: { cut: maidCut, body: maidBody, sleeve: maidSleeve, long: false, cap: 1, key: legKey, dress: true },
  lifetank: { cut: tankCut, body: tankBody, thick: 0.008 },
  refshirt: { cut: teeCut, body: refBody, sleeve: refSleeve, long: false, cap: 1, own: FIXED.ink, thick: 0.008 },
  robe: { cut: robeCut, body: robeBody, sleeve: robeSleeve, cap: 1, key: legKey, dress: true, thick: 0.03 },
  hotdog: { cut: hotdogCut, body: hotdogBody, key: (lk, F) => `${F.hd}${legKey(lk, F)}`, dress: true, own: 0xd9482f, thick: 0.12 },
};
const topOf = (top) => (typeof top === 'string' && Object.hasOwn(TOPS, top) ? TOPS[top] : null);
// a top's own colour when you haven't picked one (null: your colour), and how far it stands off the back (models.js
// hangs backpacks and capes that much further out)
export const topOwn = (top) => { const G = topOf(top); return G && G.own != null ? G.own : null; };
export const topThick = (top) => { const G = topOf(top); return (G && G.thick) || 0; };
const BOTTOMS = { shorts: shortsBody, pants: pantsBody, skirt: skirtBody, overalls: overallsBody };
const wearOn = (P) => P.wear || (P.wear = P.body.add(new THREE.Group()).children.at(-1)); // one group for everything on the torso: jokeBody leaves groups alone (these are cut to fit already)
const cutKey = (top, lk, F) => `${top}|${F.key}|${TOPS[top] && TOPS[top].key ? TOPS[top].key(lk, F) : ''}`;
// the colour the mannequin's shoulder balls take under this top (null: bare)
export function topCap(lk, col) { const top = lk.top || 'tank', G = Object.hasOwn(TOPS, top) && TOPS[top]; return G && G.cap ? (G.cap === 1 ? col : G.cap) : null; }
// how big a top is on the plain mannequin at a height: [half width, depth], raised trim and all (econ3d.js fits the
// Plant & Defuse vest round it). null: not one of ours
const sizes = new Map();
export function topSize(top, y) {
  const G = Object.hasOwn(TOPS, top) && TOPS[top];
  if (!G) return null;
  if (!sizes.has(top)) { const F = fitOf({}); sizes.set(top, F.dressed(G.cut(F, {}))); }
  const a = sizes.get(top).at(y), pad = top === 'tank' ? 0.022 : 0.012;
  return [a[0] + pad, Math.max(a[1], a[2]) + pad];
}
// P: the mannequin's parts { body, arm, armL, legL, legR, kneeL, kneeR, head }. col: the top's colour. legs: full-length
// trousers on (a maid's socks stay off). false: this top isn't one of ours
export function wearTop(P, lk, col, legs) {
  const top = lk.top || 'tank', G = Object.hasOwn(TOPS, top) && TOPS[top];
  if (!G) return false;
  const F = fitOf(lk), mat = cloth(col);
  wear(wearOn(P), cut(cutKey(top, lk, F), () => G.body(F, lk, G.cut(F, lk))), mat);
  if (G.sleeve) {
    const s = limb(top, () => ({ up: G.sleeve('up'), fore: G.long !== false ? G.sleeve('fore') : null, upL: G.pocket ? G.sleeve('up', true) : null }));
    wear(P.arm, s.up, mat, ARM.ur); wear(P.armL, s.upL || s.up, mat, ARM.ul);
    if (s.fore) { wear(P.arm, s.fore, mat, ARM.fr); wear(P.armL, s.fore, mat, ARM.fl); }
  }
  if (top === 'maid') {
    if (!legs) for (const kn of [P.kneeL, P.kneeR]) { wear(kn, limb('maidsock', maidSock), mat); wear(kn, limb('maidshoe', maidShoe), mat); }
    if (!lk.head || lk.head === 'none' || lk.head === 'catears') { const big = lk.hair === 'afro' ? 1.42 : lk.hair === 'spiky' || lk.hair === 'bun' ? 1.12 : 1; wear(P.head, limb('maidhead' + big, () => maidHeaddress(big)), mat); }
  }
  return true;
}
// col: the bottom's colour. under a dress (the Maid Dress, a robe, a hot dog) only the trouser legs show
export function wearBottom(P, lk, col) {
  const bottom = lk.bottom || 'shorts', top = lk.top || 'tank', make = Object.hasOwn(BOTTOMS, bottom) && BOTTOMS[bottom];
  if (!make) return false;
  const F = fitOf(lk), mat = cloth(col), dress = !!(topOf(top) && topOf(top).dress);
  if (!dress) wear(wearOn(P), cut(`${bottom}|${bottom === 'overalls' ? cutKey(top, lk, F) : bottom === 'skirt' ? F.key + legKey(lk, F) : F.key}`, () => make(F, lk, bottom === 'overalls' ? F.dressed(TOPS[top] ? TOPS[top].cut(F, lk) : []) : null)), mat);
  if (bottom === 'skirt' || (dress && bottom === 'shorts')) return true; // bare legs
  for (const [leg, knee, sx] of [[P.legL, P.kneeL, -1], [P.legR, P.kneeR, 1]]) {
    const L = limb(bottom + sx, () => ({ thigh: legPiece(bottom, 'thigh', sx), shin: bottom === 'shorts' ? null : legPiece(bottom, 'shin', sx), shoe: bottom === 'shorts' ? null : legPiece(bottom, 'shoe', sx) }));
    wear(leg, L.thigh, mat); if (L.shin) { wear(knee, L.shin, mat); wear(knee, L.shoe, mat); }
  }
  return true;
}
