// JANKFIRE clothes: the tops and bottoms on the mannequin (models.js buildCharacter calls wearTop / wearBottom).
// Each garment is cut for the body it goes on: the build and the body sliders give a body (fitOf), a garment is rows of
// [height, half width, front depth, back depth] round it (a shell), and its collar, pockets, zip and seams are laid on
// that shell, so nothing floats off a big belly or sinks into one. A whole piece is ONE mesh: its colours come from a
// tiny palette texture (the garment's own colour in a few tones + fixed colours), so a jacket is five draw calls, not
// forty. Shapes are built once per garment + body and shared. Looks only: the server's hitboxes never hear of this.
import * as THREE from 'three';
import { jankify } from './jank.js';
import { BUILDS, JOKE, JOKE_MAX } from '/shared/looks.js';

const PI = Math.PI, TAU = PI * 2, DEG = PI / 180;
const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const T = (x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0, sx = 1, sy = sx, sz = sx) => new THREE.Matrix4().compose(V3(x, y, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz)), V3(sx, sy, sz));
const mix = (a, b, t) => a + (b - a) * t, cl01 = (t) => Math.max(0, Math.min(1, t)), ss = (a, b, x) => { const t = cl01((x - a) / (b - a)); return t * t * (3 - 2 * t); };

// ------------------------------------------------------------ palette: one tiny texture per garment colour
// cells 0-7 come from the garment's own colour (so seams, hems and folds follow whatever you pick); the rest are fixed
const PW = 32;
const C = { base: 0, panel: 1, seam: 2, deep: 3, light: 4, hi: 5, pop: 6, popd: 7,
  white: 8, cream: 9, grey: 10, ink: 11, coal: 12, silver: 13, steel: 14, brass: 15, red: 16, redd: 17, pink: 18, rose: 19,
  yellow: 20, cyan: 21, brown: 22, tan: 23, tee: 24, frill: 25, pencil: 26, eraser: 27, soled: 28 };
const FIXED = [0xf2f1ec, 0xe2dccb, 0x8f949c, 0x1c1c21, 0x34343c, 0xc6ccd4, 0x70767f, 0xffc21a, 0xc02030, 0x8a1422, 0xff4fd8, 0xff9ad5,
  0xffe14d, 0x4fd8ff, 0x6b3a1a, 0xc8a070, 0x2b2b31, 0xffffff, 0xffd21a, 0xff7ab8, 0x3a2412];
const TONES = [1, 0.87, 0.72, 0.5, 1.13, 1.3]; // base, panel, seam, deep shadow, light, highlight
function tone(hex, k, flip) { // in screen (sRGB) values: k < 1 darker, > 1 paler
  const c = [(hex >> 16) & 255, (hex >> 8) & 255, hex & 255];
  if (flip && k < 1 && Math.max(...c) < 64) k = 1 + (1 - k) * 0.85; // near-black cloth can't go darker: its panels and seams go paler instead
  return c.map((v) => (k <= 1 ? v * k : v + (255 - v) * (k - 1) * 0.8));
}
const pals = new Map(), mats = new Map();
function palette(col) {
  if (pals.has(col)) return pals.get(col);
  const d = new Uint8Array(PW * 4).fill(255), put = (i, c) => { d[i * 4] = c[0]; d[i * 4 + 1] = c[1]; d[i * 4 + 2] = c[2]; };
  TONES.forEach((k, i) => put(i, tone(col, k, i === 1 || i === 2)));
  // the accent (linings, pull tabs): hot pink, or yellow on anything already pink / red
  const hsl = new THREE.Color(col).getHSL({}), pop = (hsl.h > 0.78 || hsl.h < 0.05) && hsl.s > 0.35 ? 0xffe14d : 0xff4fd8;
  put(C.pop, tone(pop, 1)); put(C.popd, tone(pop, 0.72));
  FIXED.forEach((c, i) => put(C.white + i, tone(c, 1)));
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
  constructor() { this.p = []; this.c = []; }
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
  box(w, h, d, cell, m) { return this.put(soup('box', () => new THREE.BoxGeometry(1, 1, 1)), cell, (m || T()).clone().multiply(T(0, 0, 0, 0, 0, 0, w, h, d))); }
  ball(r, cell, m, ws = 8, hs = 6) { return this.put(soup('ball' + ws + hs, () => new THREE.SphereGeometry(1, ws, hs)), cell, (m || T()).clone().multiply(T(0, 0, 0, 0, 0, 0, r))); }
  cyl(r0, r1, h, n, cell, m) { return this.put(soup(`cyl${n}${r0 === r1 ? '' : (r0 / r1).toFixed(3)}`, () => new THREE.CylinderGeometry(r0 / r1, 1, 1, n)), cell, (m || T()).clone().multiply(T(0, 0, 0, 0, 0, 0, r1, h, r1))); }
  // a tube: prof rows are [radius, distance along, cell, rib]. along -z (an arm), or -y with o.y (a leg). rib: every other
  // column sits that much further in (ribbed knit). o.sx / o.sy squash it
  lathe(prof, n, cell, o = {}) {
    const pt = (r, d, j, rib) => { const a = (j / n) * TAU + (o.turn || 0), k = rib && j % 2 ? 1 - rib : 1, x = Math.cos(a) * r * k * (o.sx || 1), y = Math.sin(a) * r * k * (o.sy || 1); return o.y ? [x, -d, -y] : [x, y, -d]; };
    for (let i = 0; i < prof.length - 1; i++) {
      const A = prof[i], B = prof[i + 1], k = A[2] ?? cell, rib = A[3] || 0;
      if (k == null) continue;
      for (let j = 0; j < n; j++) { const a = pt(A[0], A[1], j, rib), b = pt(A[0], A[1], j + 1, rib), c = pt(B[0], B[1], j + 1, rib), d = pt(B[0], B[1], j, rib); this.quad(a, b, c, d, k, o.y ? [a[0] + c[0], 0, a[2] + c[2]] : [a[0] + c[0], a[1] + c[1], 0]); }
    }
    return this;
  }
  // a cord through points, n-sided. r: its radius (or one per point)
  tube(pts, r, n, cell) {
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
  const lumps = []; // [x, y, depth (out from the middle), rx, ry, rz, front?, how much of it the cloth covers]
  if (ft) { const r = 0.1 + JOKE.belly * ft; lumps.push([0, 1.13 - r * 0.1, 0.05 + r * 0.45, r * 1.25, r * 1.02, r, 1, 1]); }
  if (ch && fem) { const r = 0.05 + JOKE.bust * ch; lumps.push([(0.085 + r * 0.25) * kc, 1.33 - r * 0.15, 0.11 * kcz + r * 0.45, r, r * 0.95, r, 1, 0.82]); } // (the cloth tents over it: the two bumps still show)
  if (bt) { const r = 0.085 + JOKE.butt * bt; lumps.push([(0.075 + r * 0.32) * kh, 0.97 - r * 0.12, 0.06 + r * 0.62, r, r * 1.05, r * 1.08, 0, 1]); }
  const skin = (y) => { // the bare torso at a height: [half width, half depth]
    let w = 0, d = 0;
    const k = (y - 1.34) / 0.22;
    if (Math.abs(k) < 1) { const s = Math.sqrt(1 - k * k); w = 0.24 * kc * s; d = 0.144 * kcz * s; }
    if (y >= 1.04 && y <= 1.22) { const r = (0.1 + (cl01((1.21 - y) / 0.16)) * 0.02) * kw; w = Math.max(w, r); d = Math.max(d, r); }
    if (y >= 0.88 && y <= 1.08) { w = Math.max(w, 0.17 * kh); d = Math.max(d, 0.115 * khz); }
    return [w, d];
  };
  // one row of a garment drawn for the plain mannequin -> the same row on this body. fol: how closely it follows the
  // build (1 = cut close, less = it hangs off the shoulders). gap: room between cloth and body. e: how square it is
  const fitRow = (y, w, f, bk2, fol, gap, e) => {
    const kx = 1 + (band(y, kc, kw, kh) - 1) * fol, kz = 1 + (band(y, kcz, kw, khz) - 1) * fol, [sw, sd] = skin(y);
    w = Math.max(w * kx, sw + gap); f = Math.max(f * kz, sd + gap); bk2 = Math.max(bk2 * kz, sd + gap);
    for (const L of lumps) { // grow that side until the lump is inside
      const t = (y - L[1]) / L[4];
      if (Math.abs(t) >= 1) continue;
      const s = Math.sqrt(1 - t * t) * L[7], rx = L[3] * s + gap, rz = L[5] * s + gap;
      w = Math.max(w, (L[0] + rx) * 1.1);
      let d = L[6] ? f : bk2;
      for (let a = 0; a <= 4; a++) { const px = L[0] + rx * Math.sin((a * PI) / 8), pz = L[2] + rz * Math.cos((a * PI) / 8); d = Math.max(d, pz / (1 - (px / w) ** e) ** (1 / e)); }
      if (L[6]) f = d; else bk2 = d;
    }
    return [y, w, f, bk2];
  };
  const F = {
    key, hd, kc, kw, kh, skin, lumps, fem, ft, ch, bt,
    // a garment's rows, fitted (+ extra rows through the lumps, so the cloth rounds them). a row's 5th number is its own fol
    rows(src, fol = 1, gap = 0.012, e = 2.6) {
      const ys = src.map((r) => r[0]), lo = ys[0], hi = ys[ys.length - 1];
      for (const L of lumps) for (const k of [-0.85, -0.5, 0, 0.5, 0.85]) { const y = L[1] + L[4] * k; if (y > lo + 0.014 && y < hi - 0.014 && !ys.some((v) => Math.abs(v - y) < 0.016)) ys.push(y); }
      ys.sort((p, q) => p - q);
      return ys.map((y) => { let i = 1; while (i < src.length - 1 && src[i][0] < y) i++; const a = src[i - 1], c = src[i], t = cl01((y - a[0]) / (c[0] - a[0])); return fitRow(y, mix(a[1], c[1], t), mix(a[2], c[2], t), mix(a[3], c[3], t), a[4] ?? fol, gap, e); });
    },
    // the head at a height (the big head slider): [half width, half depth]
    head(y) { const s = 1 + JOKE.head * hd, t = (y - 1.62 - 0.14 * s) / (0.171 * s); return Math.abs(t) < 1 ? [0.119 * s * Math.sqrt(1 - t * t), 0.133 * s * Math.sqrt(1 - t * t)] : [0, 0]; },
  };
  fits.set(key + hd, F);
  return F;
}

// ------------------------------------------------------------ shells: a garment's surface
// rows of [y, half width, front depth, back depth], rounded off as a squashed superellipse (e: how square).
// angles go round the body: 0 = the back (+z), 90 = their right (+x), 180 = the front (-z)
function shell(rows, e = 2.6) {
  const k = 2 / e, n = rows.length;
  const at = (y) => { let i = 1; while (i < n - 1 && rows[i][0] < y) i++; const a = rows[i - 1], b = rows[i], t = cl01((y - a[0]) / (b[0] - a[0])); return [mix(a[1], b[1], t), mix(a[2], b[2], t), mix(a[3], b[3], t)]; };
  const raw = (y, u) => { const [w, f, b] = at(y), s = Math.sin(u), c = Math.cos(u); return [Math.sign(s) * Math.abs(s) ** k * w, y, Math.sign(c) * Math.abs(c) ** k * (c > 0 ? b : f)]; };
  const S = {
    rows, e, at, y0: rows[0][0], y1: rows[n - 1][0],
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
    // heights for a loft from y0 to y1: its own rows in between (so the cloth really is the shell) + any more
    lv(y0, y1, more = []) { const out = [y0, y1, ...more.filter((y) => y > y0 && y < y1)]; for (const r of rows) if (r[0] > y0 + 0.008 && r[0] < y1 - 0.008 && !out.some((y) => Math.abs(y - r[0]) < 0.008)) out.push(r[0]); return out.sort((a, b) => a - b); },
  };
  return S;
}
// cloth on a shell between heights lv and angles us. an angle can be a function of the height (an edge that isn't
// straight up, like a zip pulled open). cell: a palette cell or (y, u, i, j) -> cell / null (a hole). o.lift(i, j)
function loft(K, S, lv, us, cell, o = {}) {
  const U = (i, j) => (typeof us[j] === 'function' ? us[j](lv[i], i) : us[j]), n = o.wrap ? us.length : us.length - 1;
  return K.grid(lv.length - 1, n, (i, j) => S.p(lv[i], U(i, j), typeof o.lift === 'function' ? o.lift(i, j) : o.lift || 0),
    typeof cell === 'function' ? (i, j) => cell((lv[i] + lv[i + 1]) / 2, (U(i, j) + (o.wrap && j === n - 1 ? U(i, 0) + TAU : U(i, j + 1))) / 2, i, j) : cell,
    (i, j, p) => { const a = p[i][j], c = p[i + 1][j + 1], x = a[0] + c[0], z = a[2] + c[2]; return o.inward ? [-x, 0, -z] : [x, 0, z]; }, o.wrap);
}
// a raised piece lying on a shell. g(s, t) -> [x, y] as it looks from the front (o.back: from behind; o.uy: [angle, y]),
// cut into ns x nt quads, `lift` off the cloth, with a rim back down to it (o.rim: its cell, or false for none)
function panel(K, S, g, ns, nt, cell, lift = 0.006, o = {}) {
  const at = (s, t, l) => { const [a, y] = g(s, t); return S.p(y, o.uy ? a : S.ux(y, a, o.back), l); };
  const mid = at(0.5, 0.5, 0), out = (i, j, p) => { const a = p[i][j], c = p[i + 1][j + 1]; return [a[0] + c[0], 0, a[2] + c[2]]; };
  const top = K.grid(nt, ns, (i, j) => at(j / ns, i / nt, lift), cell, out);
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
const limbs = new Map(); // sleeve and leg shapes: the same on every body (jokeBody fattens the meshes)
function limb(key, make) { if (!limbs.has(key)) limbs.set(key, make()); return limbs.get(key); }
// garment shapes cut for a body, newest last. past the cap the oldest goes: whoever still wears it frees it with their character
const cuts = new Map(), CUTS = 72;
function cut(key, make) {
  let g = cuts.get(key);
  if (g) { cuts.delete(key); cuts.set(key, g); return g; }
  g = make(); cuts.set(key, g);
  if (cuts.size > CUTS) { const old = cuts.keys().next().value; for (const x of Object.values(cuts.get(old))) if (x && x.isBufferGeometry) x.userData.shared = false; cuts.delete(old); }
  return g;
}

// ------------------------------------------------------------ Runner Jacket: an oversized hi-vis bomber
// black yoke, sides and ribbed knit (hem, cuffs, a stripe through each), a big padded collar left open with a loud
// lining, a chunky zip a bit off-centre, reflective tape and an armband on the sleeves, slanted hand pockets, and a
// black panel on the back with a little running figure on it (it's a runner jacket)
const RUN_E = 2.7, RUN_ZX = 0.046;
function runnerBody(F, lk) {
  const K = new Kit(), e = RUN_E, zx = RUN_ZX, covered = lk.back && lk.back !== 'none';
  const S = shell(F.rows([[1.085, 0.238, 0.166, 0.166], [1.105, 0.262, 0.182, 0.18], [1.14, 0.28, 0.192, 0.188], [1.26, 0.284, 0.194, 0.19], [1.39, 0.294, 0.196, 0.192],
    [1.46, 0.296, 0.19, 0.19], [1.505, 0.284, 0.176, 0.182], [1.535, 0.215, 0.15, 0.156], [1.552, 0.134, 0.118, 0.122]], 0.55, 0.016, e), e);
  const open = (y) => 0.036 * cl01((y - 1.44) / 0.112) ** 1.4; // the zip is pulled down to the yoke: the fronts part above it
  const cols = [0, 26, 50, 72, 90, 108, 130, 152].map((d) => d * DEG), zi = cols.length;
  const us = [...cols, (y) => S.ux(y, zx + open(y)), (y) => S.ux(y, zx - open(y)), ...[208, 230, 252, 270, 288, 310, 334].map((d) => d * DEG)];
  const side = (u) => Math.abs(Math.abs(u - PI) - PI / 2) < 18.5 * DEG;
  loft(K, S, S.lv(1.085, 1.552, [1.105, 1.14, 1.26, 1.39, 1.455, 1.505, 1.535]), us, (y, u, i, j) => (j === zi ? null : y > 1.455 || side(u) ? C.ink : C.base), { wrap: true });
  // the yoke dips to a point front and back
  for (const back of [false, true]) for (const sx of [-1, 1]) { const x0 = back ? 0 : zx; panel(K, S, quad4([x0, 1.398], [sx * 0.215, 1.458], [sx * 0.215, 1.46], [x0, 1.46]), 4, 1, C.ink, 0.003, { back, rim: false }); }
  // a stitched line across each yellow panel, so the big faces aren't bare
  for (const back of [false, true]) for (const [x0, x1] of back ? [[-0.2, -0.105], [0.105, 0.2]] : [[-0.215, -0.02], [zx + 0.03, 0.215]]) bar(K, S, [x0, 1.232], [x1, 1.232], 0.007, C.seam, 0.0025, { back, rim: false, step: 0.04 });
  // panel seams down the body, front and back
  for (const d of [26, 130, 230, 334]) panel(K, S, (s, t) => [(d + (s - 0.5) * 2.4) * DEG, mix(1.14, 1.45, t)], 1, 4, C.seam, 0.0025, { uy: true, rim: false });
  // ribbed hem band with a stripe through it
  const R = shell(F.rows([[0.996, 0.228, 0.158, 0.158], [1.092, 0.236, 0.165, 0.165]], 1, 0.022, e), e), rn = 36;
  loft(K, R, [0.996, 1.03, 1.047, 1.092], Array.from({ length: rn }, (_, j) => (j / rn) * TAU), (y) => (y > 1.03 && y < 1.047 ? C.base : C.ink), { wrap: true, lift: (i, j) => (j % 2 ? 0 : -0.007) });
  // a dark tee in the open neck
  const N = shell(F.rows([[1.3, 0, 0, 0], [1.42, 0, 0, 0], [1.5, 0, 0, 0], [1.548, 0.07, 0.066, 0.066]], 1, 0.008, 2.2), 2.2);
  loft(K, N, N.lv(1.36, 1.548), [100, 125, 150, 180, 210, 235, 260].map((d) => d * DEG), C.tee);
  // ---- the collar: padded, flared, open at the front, lower there than at the nape. the lining is the loud bit
  const ch = [1.548, 1.6, 1.655, 1.705].map((y) => { const h = F.head(y); return [y, Math.max(mix(0.134, 0.178, (y - 1.548) / 0.157), h[0] + 0.04), Math.max(mix(0.118, 0.16, (y - 1.548) / 0.157), h[1] + 0.032), Math.max(mix(0.122, 0.166, (y - 1.548) / 0.157), h[1] + 0.034)]; });
  const Cl = shell(ch, 2.3), cn = 14, ct = 3, gapAt = (t) => 0.036 + 0.05 * t;
  const cu = (t, j) => { const a = Cl.ux(mix(1.548, 1.705, t), zx + gapAt(t)), b = Cl.ux(mix(1.548, 1.705, t), zx - gapAt(t)) - TAU; return mix(a, b, j / cn); };
  const cy = (t, u) => mix(1.548, 1.705 - 0.05 * ((1 - Math.cos(u)) / 2) ** 2, t);
  const cp = (lift) => (i, j) => { const t = i / ct, u = cu(t, j); return Cl.p(cy(t, u), u, lift); };
  const rad = (inward) => (i, j, p) => { const a = p[i][j], c = p[i + 1][j + 1], x = a[0] + c[0], z = a[2] + c[2]; return inward ? [-x, 0, -z] : [x, 0, z]; };
  const co = K.grid(ct, cn, cp(0), (i) => (i === ct - 1 ? C.coal : C.ink), rad(false)), ci = K.grid(ct, cn, cp(-0.02), C.pop, rad(true));
  for (let j = 0; j < cn; j++) K.quad(co[ct][j], co[ct][j + 1], ci[ct][j + 1], ci[ct][j], C.ink, [0, 1, 0]); // the rolled top edge
  for (const j of [0, cn]) for (let i = 0; i < ct; i++) K.quad(co[i][j], co[i + 1][j], ci[i + 1][j], ci[i][j], C.ink, [j ? -1 : 1, 0, -1]); // the two front ends
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
  if (!covered) {
    const B = (a, b, w = 0.024) => bar(K, S, a, b, w, C.base, 0.0105, { back: true, rim: false, step: 0.2 });
    panel(K, S, rect(0.018, 1.336, 0.056, 1.374), 1, 1, C.base, 0.0105, { back: true, rim: false }); // head
    B([-0.008, 1.262], [0.026, 1.332], 0.036); // body, leaning into it
    B([0.02, 1.322], [0.064, 1.296], 0.02); B([0.064, 1.296], [0.092, 1.322], 0.02); // front arm
    B([0.016, 1.318], [-0.034, 1.306], 0.02); B([-0.034, 1.306], [-0.058, 1.276], 0.02); // back arm
    B([-0.006, 1.268], [0.05, 1.236]); B([0.05, 1.236], [0.04, 1.184]); B([0.03, 1.186], [0.066, 1.186], 0.014); // front leg + foot
    B([-0.008, 1.262], [-0.052, 1.226]); B([-0.052, 1.226], [-0.106, 1.24]); // back leg, kicked up
    for (const [y, l] of [[1.35, 0.05], [1.316, 0.036], [1.282, 0.05]]) B([-0.134, y], [-0.134 + l, y], 0.011); // speed lines
    digits(K, S, '12', 0.092, 1.196, 0.036, C.silver, 0.0105, true);
  }
  return K.done();
}
// puffy sleeves gathered into ribbed cuffs: a black shoulder (the yoke carries on over it), a tape - black - tape armband,
// tape round the forearm. left: their left sleeve gets the pen pocket
function runnerSleeve(part, left) {
  const K = new Kit(), n = 12;
  if (part === 'up') {
    K.lathe([[0.012, -0.092, C.ink], [0.066, -0.076, C.ink], [0.094, -0.03, C.ink], [0.099, 0.022], [0.094, 0.1], [0.094, 0.112, C.silver], [0.096, 0.126, C.ink], [0.096, 0.166, C.silver], [0.094, 0.18],
      [0.088, 0.184], [0.082, 0.25], [0.085, 0.288], [0.074, 0.318], [0.05, 0.33]], n, C.base);
    if (left) { // a pen pocket on the outside of the arm: black flap, two pens
      const m = T(-0.093, 0.004, -0.058, 0, PI / 2, 0);
      K.box(0.07, 0.05, 0.012, C.ink, m.clone().multiply(T(0, 0, 0.002))); K.box(0.076, 0.016, 0.016, C.coal, m.clone().multiply(T(0, 0.022, 0.004)));
      for (const [x, c] of [[-0.016, C.pop], [0.004, C.silver]]) K.box(0.009, 0.03, 0.009, c, m.clone().multiply(T(x, 0.04, 0.004)));
    }
  } else {
    K.lathe([[0.066, -0.03], [0.078, 0.02], [0.08, 0.062], [0.081, 0.066, C.silver], [0.081, 0.084], [0.079, 0.088], [0.072, 0.13], [0.06, 0.148], [0.058, 0.15, C.ink, 0.09], [0.058, 0.166, C.base, 0.09], [0.058, 0.176, C.ink, 0.09], [0.055, 0.202], [0.047, 0.204, C.deep], [0.04, 0.19]], n, C.base);
  }
  return K.done('z');
}

// ------------------------------------------------------------ putting them on
const TOPS = {
  runner: { body: runnerBody, sleeve: runnerSleeve, key: (lk, F) => `${F.hd}${lk.back && lk.back !== 'none' ? 1 : 0}`, pocket: true },
};
const wearOn = (P) => P.wear || (P.wear = P.body.add(new THREE.Group()).children.at(-1)); // one group for everything on the torso: jokeBody leaves groups alone (these are cut to fit already)
// P: the mannequin's parts { body, arm, armL, legL, legR, kneeL, kneeR, head }. col: the top's colour. false = not ours
export function wearTop(P, lk, col) {
  const top = lk.top || 'tank', G = TOPS[top];
  if (!G) return false;
  const F = fitOf(lk), mat = cloth(col);
  const g = cut(`${top}|${F.key}|${G.key ? G.key(lk, F) : ''}`, () => ({ body: G.body(F, lk) }));
  hang(wearOn(P), g.body, mat);
  if (G.sleeve) {
    const s = limb(top, () => ({ up: G.sleeve('up'), fore: G.long !== false ? G.sleeve('fore') : null, upL: G.pocket ? G.sleeve('up', true) : null }));
    hang(P.arm, s.up, mat, ARM.ur); hang(P.armL, s.upL || s.up, mat, ARM.ul);
    if (s.fore) { hang(P.arm, s.fore, mat, ARM.fr); hang(P.armL, s.fore, mat, ARM.fl); }
  }
  return true;
}
