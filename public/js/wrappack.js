// The big wrap pack: candy solids, porcelain, japanese patterns and a pile of stupid ones.
// Every pattern is drawn once on a small canvas (seeded, so everyone sees the same one) and put on the gun with a
// triplanar shader in each mesh's own space (metres): it tiles the same on code models and Blender models, needs no
// UVs and never stretches along a barrel. The legendaries animate in the shader off one shared clock: no per-frame JS.
import * as THREE from 'three';
import { jankify } from './jank.js';
import { WRAP_PACK } from '/shared/cosmetics.js';

// [id, tracer, spec] (names + rarities live in shared/cosmetics.js WRAP_PACK). spec: c = colour, r = roughness, m = metalness, tx = pattern, den = tiles per metre,
// fx = shader trick, vel = scroll (tiles / s), gc / gk = glow colour / strength
const L = [
  // ---------------- commons: glossy candy solids + two-tones
  ['cherry', 0xff2a3d, { c: 0xe0162b }],
  ['tangerine', 0xff8a2a, { c: 0xff7a12 }],
  ['lemon', 0xfff04d, { c: 0xffde1f }],
  ['lime', 0x9dff2a, { c: 0x86d817 }],
  ['mint', 0x8affd0, { c: 0x6fe8b8 }],
  ['teal', 0x2ae0e0, { c: 0x0f9f9f }],
  ['sky', 0x7fd0ff, { c: 0x4fb8ff }],
  ['navy', 0x5a7aff, { c: 0x1c2a6b }],
  ['grape', 0xb36bff, { c: 0x7a2fc0 }],
  ['magenta', 0xff00dc, { c: 0xff00c8 }],
  ['cream', 0xfff3d8, { c: 0xf0e2bc, r: 0.4 }],
  ['matte', 0x666677, { c: 0x1b1b20, r: 0.9, env: 0.15 }],
  ['white', 0xffffff, { c: 0xf2f4f7, r: 0.3 }],
  ['ketchup', 0xff4a1a, { tx: 'ketchup', den: 7, r: 0.25 }],
  ['creamsicle', 0xffa040, { tx: 'creamsicle', den: 5, r: 0.25 }],
  ['bubblegum', 0xff9ccf, { tx: 'bubblegum', den: 7, r: 0.22 }],
  ['hazard', 0xffd400, { tx: 'hazard', den: 14, r: 0.45 }],
  ['hivis', 0xff7a00, { tx: 'hivis', den: 9, r: 0.5 }],
  // ---------------- porcelain
  ['china', 0x3a64d8, { tx: 'china', den: 5.5, r: 0.12, env: 1.1 }],
  ['crackle', 0xbfe0c8, { tx: 'crackle', den: 4.5, r: 0.14, env: 1 }],
  ['kintsugi', 0xffc84a, { tx: 'kintsugi', glow: 'kintsugi', den: 4.5, r: 0.12, env: 1, fx: 6, gc: 0xffb820 }],
  // ---------------- japanese
  ['seigaiha', 0x4fd8ff, { tx: 'seigaiha', den: 6.5, r: 0.3 }],
  ['asanoha', 0xff6aa8, { tx: 'asanoha', den: 7, rep: [1, 64 / 111], r: 0.35 }],
  ['shibori', 0x8aa8ff, { tx: 'shibori', den: 7, r: 0.75, env: 0.3 }],
  ['washi', 0xf3ead8, { tx: 'washi', den: 6, r: 0.9, env: 0.2 }],
  ['sakura', 0xffb3d6, { tx: 'sakura', den: 8, r: 0.3, vel: [0.03, -0.05] }],
  ['koi', 0xff7a2a, { tx: 'koi', den: 3.5, r: 0.15, vel: [0.012, 0.006] }],
  ['bigwave', 0x2a5aa8, { tx: 'bigwave', den: 3.5, r: 0.45 }],
  ['urushi', 0xe8b74a, { tx: 'urushi', den: 4, r: 0.08, env: 1.2 }],
  ['tokyo', 0xff4fd8, { tx: 'tokyo', glow: 'tokyo', den: 3.2, r: 0.2, fx: 5, gk: 1.6 }],
  // ---------------- go crazy
  ['bubblewrap', 0xd9f4ff, { tx: 'bubblewrap', den: 14, r: 0.1, env: 1.2 }],
  ['cheese', 0xffd23f, { tx: 'cheese', den: 6, r: 0.55 }],
  ['denim', 0x4a6ab8, { tx: 'denim', den: 6, r: 0.85, env: 0.2 }],
  ['plaid', 0xd02a34, { tx: 'plaid', den: 7, r: 0.85, env: 0.2 }],
  ['receipt', 0xf6f3ea, { tx: 'receipt', den: 3.2, r: 0.6 }],
  ['pizza', 0xf2b632, { tx: 'pizza', den: 6, r: 0.35 }],
  ['leopard', 0xe3a85a, { tx: 'leopard', den: 7, r: 0.5 }],
  ['zebra', 0xf5f5f0, { tx: 'zebra', den: 6, r: 0.45 }],
  ['stained', 0xff4fd8, { tx: 'stained', glow: 'stained', den: 4, r: 0.08, env: 1, fx: 9, gk: 0.45 }],
  ['circuit', 0x39ff14, { tx: 'circuit', glow: 'circuit', den: 8, r: 0.35, fx: 7, gc: 0x39ff14 }],
  ['crt', 0x4fd8ff, { tx: 'crt', glow: 'crt', den: 16, r: 0.15, fx: 3 }],
  ['sheet', 0x4fbf5a, { tx: 'sheet', den: 2.6, r: 0.5 }],
  ['memo', 0xff3030, { tx: 'memo', den: 2.8, r: 0.6 }],
  ['holo', 0xc8a8ff, { tx: 'holo', glow: 'holo', den: 10, r: 0.22, m: 0.7, env: 1.1, fx: 1 }],
  ['lchrome', 0xe8f0ff, { c: 0x101014, r: 0.25, notex: 1, fx: 2, gk: 1 }],
  ['glitch', 0xff00dc, { tx: 'glitch', glow: 'glitch', den: 5, r: 0.3, fx: 4, gk: 0.4 }],
  ['meat', 0xff2040, { tx: 'meat', glow: 'meat', den: 6, r: 0.16, env: 0.9, fx: 8, gc: 0xff2040 }],
  ['corp', 0xffe14d, { tx: 'corp', glow: 'corp', den: 3.6, r: 0.25, vel: [0.08, 0], fx: 10, gk: 1.2 }],
];
export const PACK = {};
for (const [id, tracer, spec] of L) PACK[id] = { name: WRAP_PACK[id][0], tracer, spec };

// ------------------------------------------------------------ canvas patterns
const rng = (seed) => () => { seed = (seed + 0x6d2b79f5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
// draw at every wrap-around copy so shapes cross the tile edge cleanly
const around = (w, h, fn) => { for (const dx of [-w, 0, w]) for (const dy of [-h, 0, h]) fn(dx, dy); };
const TAU = Math.PI * 2;
function ell(g, x, y, rx, ry, rot, col) { g.fillStyle = col; g.beginPath(); g.ellipse(x, y, rx, ry, rot, 0, TAU); g.fill(); }
function circ(g, x, y, r, col) { g.fillStyle = col; g.beginPath(); g.arc(x, y, r, 0, TAU); g.fill(); }
function ring(g, x, y, r, col, lw, a0 = 0, a1 = TAU) { g.strokeStyle = col; g.lineWidth = lw; g.beginPath(); g.arc(x, y, r, a0, a1); g.stroke(); }
function line(g, pts, col, lw) { g.strokeStyle = col; g.lineWidth = lw; g.beginPath(); pts.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.stroke(); }
function grain(g, w, h, r, amt, a = 1) { // per-pixel brightness noise over what's there
  const d = g.getImageData(0, 0, w, h), p = d.data;
  for (let i = 0; i < p.length; i += 4) { const k = (r() - 0.5) * amt * a; p[i] += k; p[i + 1] += k; p[i + 2] += k; }
  g.putImageData(d, 0, 0);
}
// toroidal voronoi: for each pixel the two nearest feature distances + the nearest cell
function voronoi(w, h, n, r) {
  const pts = []; for (let i = 0; i < n; i++) pts.push([r() * w, r() * h]);
  const d1 = new Float32Array(w * h), d2 = new Float32Array(w * h), id = new Uint16Array(w * h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    let a = 1e9, b = 1e9, k = 0;
    for (let i = 0; i < n; i++) {
      let dx = Math.abs(x + 0.5 - pts[i][0]), dy = Math.abs(y + 0.5 - pts[i][1]);
      dx = Math.min(dx, w - dx); dy = Math.min(dy, h - dy);
      const d = Math.sqrt(dx * dx + dy * dy);
      if (d < a) { b = a; a = d; k = i; } else if (d < b) b = d;
    }
    d1[y * w + x] = a; d2[y * w + x] = b; id[y * w + x] = k;
  }
  return { d1, d2, id, pts };
}
function pix(g, w, h, fn) { // fn(x, y) -> [r, g, b] or null to keep
  const d = g.getImageData(0, 0, w, h), p = d.data;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const c = fn(x, y); if (!c) continue; const i = (y * w + x) * 4; p[i] = c[0]; p[i + 1] = c[1]; p[i + 2] = c[2]; p[i + 3] = 255; }
  g.putImageData(d, 0, 0);
}
// tiling value noise: a period x period lattice, smooth-interpolated; fbm = a few octaves of it. returns 0..1
function noiseTile(period, r) {
  const v = new Float32Array(period * period).map(() => r());
  return (x, y) => {
    const xi = Math.floor(x), yi = Math.floor(y), fx = x - xi, fy = y - yi, sx = fx * fx * (3 - 2 * fx), sy = fy * fy * (3 - 2 * fy);
    const at = (i, j) => v[(((j % period) + period) % period) * period + (((i % period) + period) % period)];
    const a = at(xi, yi) + (at(xi + 1, yi) - at(xi, yi)) * sx, b = at(xi, yi + 1) + (at(xi + 1, yi + 1) - at(xi, yi + 1)) * sx;
    return a + (b - a) * sy;
  };
}
function fbm(w, r, oct = [4, 8, 16]) { // for a w-wide tile
  const ns = oct.map((p) => [noiseTile(p, r), p / w]);
  return (x, y) => { let t = 0, a = 0.5, n = 0; for (const [f, k] of ns) { t += f(x * k, y * k) * a; n += a; a *= 0.5; } return t / n; };
}
const hexRgb = (s) => [parseInt(s.slice(1, 3), 16), parseInt(s.slice(3, 5), 16), parseInt(s.slice(5, 7), 16)];
// a blurred copy that still tiles (draw the source at its 9 wrap-around spots through the blur)
function blurTile(g, src, w, h, px) { g.save(); g.filter = `blur(${px}px)`; around(w, h, (dx, dy) => g.drawImage(src, dx, dy)); g.restore(); }
const mkCanvas = (w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; };
// tiny made-up glyphs (no real script): a few strokes in a box, for signs and labels
function glyph(g, x, y, s, r) {
  const n = 2 + ((r() * 3) | 0);
  for (let i = 0; i < n; i++) {
    const t = (r() * 5) | 0, a = r(), b = r();
    if (t === 0) line(g, [[x, y + s * a], [x + s, y + s * a]], g.strokeStyle, g.lineWidth);
    else if (t === 1) line(g, [[x + s * a, y], [x + s * a, y + s]], g.strokeStyle, g.lineWidth);
    else if (t === 2) line(g, [[x + s * a, y], [x + s * b, y + s]], g.strokeStyle, g.lineWidth);
    else if (t === 3) line(g, [[x, y + s * 0.5], [x + s * 0.5, y + s * b], [x + s, y + s * 0.5]], g.strokeStyle, g.lineWidth);
    else g.strokeRect(x + s * 0.15, y + s * 0.15 + a * s * 0.3, s * 0.7, s * 0.4);
  }
}
function smiley(g, x, y, r, face, ink) {
  circ(g, x, y, r, face);
  ell(g, x - r * 0.35, y - r * 0.25, r * 0.12, r * 0.22, 0, ink); ell(g, x + r * 0.35, y - r * 0.25, r * 0.12, r * 0.22, 0, ink);
  g.lineCap = 'round'; ring(g, x, y + r * 0.02, r * 0.55, ink, r * 0.14, 0.18 * Math.PI, 0.82 * Math.PI); g.lineCap = 'butt';
}

// name: [w, h, draw(g, w, h, r, glow)]. glow = drawing the glow mask (black = no glow) with the same seed
const TX = {
  hazard: [32, 32, (g, w) => { for (let y = 0; y < w; y++) for (let x = 0; x < w; x++) { g.fillStyle = ((x + y) >> 3) & 1 ? '#161616' : '#ffd400'; g.fillRect(x, y, 1, 1); } }],
  hivis: [32, 32, (g, w, h, r) => {
    g.fillStyle = '#ff6a00'; g.fillRect(0, 0, w, h);
    g.fillStyle = '#9aa2ae'; g.fillRect(0, 11, w, 10); g.fillStyle = '#e4e9f0'; g.fillRect(0, 12, w, 8);
    g.fillStyle = 'rgba(255,255,255,0.7)'; for (let x = 0; x < w; x += 4) g.fillRect(x, 13 + ((x >> 2) & 1) * 4, 2, 1);
    grain(g, w, h, r, 14);
  }],
  china: [128, 128, (g, w, h, r) => {
    const co = '#1f46a8', lt = '#7193dc';
    g.fillStyle = '#f5f7fb'; g.fillRect(0, 0, w, h);
    for (let i = 0; i < 26; i++) { const x = r() * w, y = r() * h, s = 6 + r() * 14; around(w, h, (dx, dy) => circ(g, x + dx, y + dy, s, 'rgba(60,100,200,0.05)')); }
    const medal = (cx, cy) => {
      ring(g, cx, cy, 27, co, 3); ring(g, cx, cy, 22, lt, 1.2);
      for (let i = 0; i < 14; i++) { const a = (i / 14) * TAU; circ(g, cx + Math.cos(a) * 24.5, cy + Math.sin(a) * 24.5, 1.4, co); }
      for (let i = 0; i < 8; i++) { const a = (i / 8) * TAU; ell(g, cx + Math.cos(a) * 11, cy + Math.sin(a) * 11, 8.5, 4, a, co); ell(g, cx + Math.cos(a) * 11, cy + Math.sin(a) * 11, 4.5, 1.6, a, lt); }
      for (let i = 0; i < 8; i++) { const a = ((i + 0.5) / 8) * TAU; ell(g, cx + Math.cos(a) * 15, cy + Math.sin(a) * 15, 3.4, 1.6, a, lt); }
      circ(g, cx, cy, 4.5, co); circ(g, cx, cy, 2, '#f5f7fb');
    };
    const sprig = (cx, cy) => {
      for (let i = 0; i < 4; i++) { const a = (i / 4) * TAU + 0.4; ell(g, cx + Math.cos(a) * 7, cy + Math.sin(a) * 7, 6, 2.6, a, lt); line(g, [[cx, cy], [cx + Math.cos(a) * 12, cy + Math.sin(a) * 12]], co, 1.2); }
      circ(g, cx, cy, 3, co);
      for (let i = 0; i < 4; i++) { const a = (i / 4) * TAU + 1.2; g.strokeStyle = co; g.lineWidth = 1.2; g.beginPath(); g.arc(cx + Math.cos(a) * 17, cy + Math.sin(a) * 17, 5, a, a + 3); g.stroke(); }
    };
    around(w, h, (dx, dy) => { medal(64 + dx, 64 + dy); medal(dx, dy); sprig(64 + dx, dy); sprig(dx, 64 + dy); });
  }],
  crackle: [128, 128, (g, w, h, r) => crackle(g, w, h, r, '#d6e6d2', '#4a5a48', '#9fb09a', 1.5)],
  kintsugi: [128, 128, (g, w, h, r, glow) => crackle(g, w, h, r, glow ? '#000000' : '#f1efe8', glow ? '#ffffff' : '#e0a628', glow ? null : '#b9b4a6', 2.6, glow)],
  seigaiha: [64, 64, (g) => {
    const rings = ['#f4f0e2', '#1b2a6b', '#f4f0e2', '#1b2a6b', '#4fd8ff'], rad = [16, 13, 10, 7, 3.5];
    g.fillStyle = '#1b2a6b'; g.fillRect(0, 0, 64, 64);
    for (let y = -32, k = 0; y <= 96; y += 8, k++) for (let x = -32; x <= 96; x += 32) {
      const cx = x + (k & 1 ? 16 : 0);
      rad.forEach((rr, i) => circ(g, cx, y, rr, rings[i]));
    }
  }],
  asanoha: [64, 111, (g, w, h) => {
    g.fillStyle = '#d42a6c'; g.fillRect(0, 0, w, h);
    const a = 32, rh = h / 4, P = (i, j) => [(i + (j & 1) * 0.5) * a, j * rh];
    g.lineCap = 'round';
    const tri = (A, B, C) => {
      const G2 = [(A[0] + B[0] + C[0]) / 3, (A[1] + B[1] + C[1]) / 3];
      line(g, [A, B, C, A], '#fff2f6', 1.8);
      for (const V of [A, B, C]) line(g, [V, G2], '#ffd0e2', 1.2);
    };
    for (let j = -1; j <= 5; j++) for (let i = -2; i <= 3; i++) {
      tri(P(i, j), P(i + 1, j), P(i + (j & 1), j + 1));
      const q = (j + 1) & 1; tri(P(i, j + 1), P(i + 1, j + 1), P(i + q, j));
    }
  }],
  shibori: [64, 64, (g, w, h, r) => {
    const s = mkCanvas(w, h), q = s.getContext('2d');
    q.fillStyle = '#1d2a66'; q.fillRect(0, 0, w, h);
    const kumo = (cx, cy) => {
      for (const rr of [4, 9.5, 15]) ring(q, cx, cy, rr, '#c4d2f2', 2.2);
      for (let i = 0; i < 12; i++) { const a = (i / 12) * TAU; line(q, [[cx + Math.cos(a) * 3, cy + Math.sin(a) * 3], [cx + Math.cos(a) * 17, cy + Math.sin(a) * 17]], 'rgba(196,210,242,0.7)', 1); }
    };
    around(w, h, (dx, dy) => { kumo(32 + dx, 32 + dy); kumo(dx, dy); });
    blurTile(g, s, w, h, 1.1);
    grain(g, w, h, r, 16);
  }],
  washi: [64, 64, (g, w, h, r) => {
    g.fillStyle = '#f8f0dc'; g.fillRect(0, 0, w, h);
    for (let i = 0; i < 18; i++) { const x = r() * w, y = r() * h, s = 4 + r() * 6; around(w, h, (dx, dy) => circ(g, x + dx, y + dy, s, 'rgba(225,205,165,0.18)')); }
    const fib = (col, n) => { for (let i = 0; i < n; i++) { const x = r() * w, y = r() * h, a = r() * TAU, l = 6 + r() * 14, b = (r() - 0.5) * 6; around(w, h, (dx, dy) => { g.strokeStyle = col; g.lineWidth = 0.8; g.beginPath(); g.moveTo(x + dx, y + dy); g.quadraticCurveTo(x + dx + Math.cos(a) * l * 0.5 + b, y + dy + Math.sin(a) * l * 0.5 - b, x + dx + Math.cos(a) * l, y + dy + Math.sin(a) * l); g.stroke(); }); } };
    fib('rgba(150,115,70,0.6)', 34); fib('rgba(230,60,120,0.75)', 6); fib('rgba(255,255,255,0.9)', 10);
    for (let i = 0; i < 4; i++) { const x = r() * w, y = r() * h, a = r() * TAU, c = ['rgba(255,120,170,0.55)', 'rgba(120,190,90,0.5)', 'rgba(255,190,60,0.55)'][i % 3]; around(w, h, (dx, dy) => { for (let k = 0; k < (i % 3 === 1 ? 1 : 5); k++) ell(g, x + dx + Math.cos(a + k * 1.26) * 2.6, y + dy + Math.sin(a + k * 1.26) * 2.6, i % 3 === 1 ? 4.5 : 2.4, 1.5, a + k * 1.26, c); }); } // pressed petals and a leaf
    grain(g, w, h, r, 12);
  }],
  sakura: [64, 64, (g, w, h, r) => {
    g.fillStyle = '#3a0f36'; g.fillRect(0, 0, w, h);
    for (let i = 0; i < 30; i++) { const x = r() * w, y = r() * h; g.fillStyle = 'rgba(255,170,220,0.18)'; g.fillRect(x | 0, y | 0, 1, 1); }
    const petal = (x, y, a, s, col) => { ell(g, x, y, 3.3 * s, 2.1 * s, a, col); ell(g, x + Math.cos(a) * 2.8 * s, y + Math.sin(a) * 2.8 * s, 0.9 * s, 0.9 * s, a, '#3a0f36'); };
    for (let i = 0; i < 4; i++) {
      const x = r() * w, y = r() * h, rot = r() * TAU, s = 0.85 + r() * 0.4;
      around(w, h, (dx, dy) => {
        for (let k = 0; k < 5; k++) { const a = rot + (k / 5) * TAU; petal(x + dx + Math.cos(a) * 3.2 * s, y + dy + Math.sin(a) * 3.2 * s, a, s, '#ffb8da'); }
        circ(g, x + dx, y + dy, 1.8 * s, '#ff6fae'); circ(g, x + dx, y + dy, 0.9 * s, '#ffe68a');
      });
    }
    for (let i = 0; i < 9; i++) { const x = r() * w, y = r() * h, a = r() * TAU; around(w, h, (dx, dy) => petal(x + dx, y + dy, a, 0.75, i & 1 ? '#ffd6ea' : '#ff9ccc')); }
  }],
  koi: [128, 128, (g, w, h, r) => {
    g.fillStyle = '#0d6a83'; g.fillRect(0, 0, w, h);
    for (let i = 0; i < 16; i++) { const x = r() * w, y = r() * h, s = 10 + r() * 18; around(w, h, (dx, dy) => circ(g, x + dx, y + dy, s, 'rgba(10,40,70,0.18)')); }
    for (let i = 0; i < 9; i++) { const x = r() * w, y = r() * h, s = 6 + r() * 12; around(w, h, (dx, dy) => { ring(g, x + dx, y + dy, s, 'rgba(170,240,255,0.35)', 1.2); ring(g, x + dx, y + dy, s * 0.6, 'rgba(170,240,255,0.2)', 1); }); }
    const pad = (x, y, s, flower) => {
      circ(g, x + 1.5, y + 2, s, 'rgba(0,30,40,0.35)');
      g.fillStyle = '#3f9a3a'; g.beginPath(); g.moveTo(x, y); g.arc(x, y, s, 0.4, TAU - 0.1); g.closePath(); g.fill();
      ring(g, x, y, s - 1, '#6fc75a', 1, 0.5, TAU - 0.2);
      if (flower) for (let k = 0; k < 6; k++) { const a = (k / 6) * TAU; ell(g, x - 3 + Math.cos(a) * 3, y - 2 + Math.sin(a) * 3, 3, 1.6, a, k & 1 ? '#ffd0e6' : '#ff8cc0'); }
    };
    const fish = (x, y, a, s, cols) => {
      g.save(); g.translate(x, y); g.rotate(a); g.scale(s, s);
      ell(g, 2, 2.5, 13, 5, 0, 'rgba(0,30,40,0.35)');
      g.fillStyle = cols[0]; g.beginPath(); g.moveTo(9, 0); g.lineTo(17, -5); g.lineTo(15, 0); g.lineTo(17, 5); g.closePath(); g.fill();
      ell(g, -6, -4, 3, 1.4, -0.6, cols[0]); ell(g, -6, 4, 3, 1.4, 0.6, cols[0]);
      g.save(); g.beginPath(); g.ellipse(0, 0, 11, 4.5, 0, 0, TAU); g.clip();
      g.fillStyle = cols[0]; g.fillRect(-12, -5, 24, 10);
      ell(g, -4, -1, 4.5, 3.5, 0.3, cols[1]); ell(g, 4, 1.5, 3.5, 3, 0, cols[1]);
      if (cols[2]) { circ(g, 1, -2, 1.5, cols[2]); circ(g, 6, 1, 1.2, cols[2]); }
      g.restore();
      circ(g, -8.5, -1.6, 0.8, '#111'); circ(g, -8.5, 1.6, 0.8, '#111');
      g.restore();
    };
    const items = [];
    for (let i = 0; i < 3; i++) items.push(['p', r() * w, r() * h, 8 + r() * 5, i === 0]);
    const C = [['#fff6ea', '#ff5a10', '#151515'], ['#ff7a1a', '#fff2e0'], ['#fff6ea', '#e01818']];
    for (let i = 0; i < 4; i++) items.push(['f', r() * w, r() * h, r() * TAU, 0.85 + r() * 0.35, C[i % 3]]);
    around(w, h, (dx, dy) => { for (const it of items) if (it[0] === 'p') pad(it[1] + dx, it[2] + dy, it[3], it[4]); });
    around(w, h, (dx, dy) => { for (const it of items) if (it[0] === 'f') fish(it[1] + dx, it[2] + dy, it[3], it[4], it[5]); });
  }],
  bigwave: [128, 128, (g, w, h, r) => {
    g.fillStyle = '#efe0bc'; g.fillRect(0, 0, w, h);
    grain(g, w, h, r, 14);
    circ(g, 98, 22, 10, '#d8343a');
    const wave = (base, ph) => {
      const y = (x) => base + 6 * Math.sin((TAU * x) / 64 + ph) - 15 * Math.pow(Math.max(0, Math.sin((TAU * x) / 128 + ph)), 3);
      for (const dy of [-128, 0, 128]) {
        g.fillStyle = '#1c3d73'; g.beginPath(); g.moveTo(-2, y(-2) + dy);
        for (let x = 0; x <= w + 2; x += 2) g.lineTo(x, y(x) + dy);
        g.lineTo(w + 2, base + 40 + dy); g.lineTo(-2, base + 40 + dy); g.closePath(); g.fill();
        for (const [o, c, lw] of [[5, '#3f6faa', 2], [10, '#2a5590', 2], [16, '#4a7cb8', 1.5], [24, '#2a5590', 1.5], [32, '#16305c', 2]]) line(g, Array.from({ length: 66 }, (_, i) => [i * 2 - 2, y(i * 2 - 2) + o + dy]), c, lw);
        line(g, Array.from({ length: 66 }, (_, i) => [i * 2 - 2, y(i * 2 - 2) + dy]), '#f4f1e6', 2.2);
        for (let x = 0; x < w; x += 4) {
          const top = Math.pow(Math.max(0, Math.sin((TAU * x) / 128 + ph)), 3);
          if (top > 0.25) { // foam claws curling off the crest
            g.strokeStyle = '#f4f1e6'; g.lineWidth = 1.6; g.beginPath(); g.arc(x - 2, y(x) - 3 + dy, 2.5 + top * 2, Math.PI * 0.9, Math.PI * 2.1); g.stroke();
          }
          if (r() < 0.35) circ(g, x + r() * 3, y(x) - 2 - r() * 6 + dy, 0.9 + r(), '#f4f1e6');
        }
      }
    };
    wave(48, 0.4); wave(112, 2.6);
  }],
  urushi: [128, 128, (g, w, h, r) => {
    g.fillStyle = '#0c0506'; g.fillRect(0, 0, w, h);
    pix(g, w, h, (x, y) => { const d = (x + y + 256) % 128; return d > 70 && d < 104 ? (d < 72 || d > 101 ? [90, 8, 12] : [168, 16, 26]) : null; }); // a red lacquer sash
    for (let i = 0; i < 260; i++) { const t = r() * 128, o = (r() - 0.5) * 24 * r(), x = (t + 87 - o) % 128, y = (t + o * 2 + 128) % 128; g.fillStyle = r() < 0.5 ? '#e8b74a' : '#ffd97a'; g.fillRect(x | 0, y | 0, 1, 1); } // nashiji gold dust on the sash edge
    const vine = (x, y, a, n) => {
      for (let k = 0; k < n; k++) {
        const r0 = 6 + r() * 6, ax = x + Math.cos(a) * r0, ay = y + Math.sin(a) * r0;
        around(w, h, (dx, dy) => {
          g.strokeStyle = '#e8b74a'; g.lineWidth = 1.4; g.beginPath(); g.arc(ax + dx, ay + dy, r0, a + Math.PI, a + Math.PI + 2.2); g.stroke();
          ell(g, ax + dx + Math.cos(a + 1.2) * r0, ay + dy + Math.sin(a + 1.2) * r0, 3, 1.3, a, '#ffd97a');
          circ(g, ax + dx + Math.cos(a + 2.2) * r0, ay + dy + Math.sin(a + 2.2) * r0, 1.3, '#ffe9a8');
        });
        x = ax + Math.cos(a + 2.2) * r0; y = ay + Math.sin(a + 2.2) * r0; a += 2.2 - Math.PI + (r() - 0.5);
      }
    };
    vine(20, 30, 0.3, 6); vine(60, 100, -1.3, 5);
    for (let i = 0; i < 3; i++) { const x = r() * w, y = r() * h; around(w, h, (dx, dy) => { for (let k = 0; k < 5; k++) { const a = (k / 5) * TAU; ell(g, x + dx + Math.cos(a) * 3, y + dy + Math.sin(a) * 3, 2.6, 1.6, a, '#e8b74a'); } circ(g, x + dx, y + dy, 1.4, '#a3121a'); }); } // gold plum blossoms
  }],
  tokyo: [128, 128, (g, w, h, r, glow) => {
    g.fillStyle = glow ? '#000' : '#0b0818'; g.fillRect(0, 0, w, h);
    if (!glow) { // the city behind the signs has its own dice so the glow pass lines up
      const br = rng(5);
      for (let i = 0; i < 26; i++) { const x = (br() * w) | 0, y = (br() * h) | 0, k = 18 + br() * 30; g.fillStyle = 'rgba(30,26,60,0.9)'; g.fillRect(x, y, 6 + br() * 14, k); }
      for (let i = 0; i < 60; i++) { g.fillStyle = br() < 0.5 ? 'rgba(255,225,120,0.5)' : 'rgba(120,200,255,0.35)'; g.fillRect((br() * w) | 0, (br() * h) | 0, 2, 2); } // lit windows
    }
    const cols = ['#ff4fd8', '#4fd8ff', '#ffe14d', '#39ff14', '#ff3030', '#ff9a1a'];
    const signs = [[6, 6, 14, 52, 1], [30, 10, 44, 14, 0], [84, 4, 12, 44, 1], [30, 34, 26, 26, 0], [62, 36, 16, 40, 1], [100, 58, 22, 14, 0], [6, 72, 40, 14, 0], [52, 84, 12, 40, 1], [72, 88, 50, 16, 0], [100, 4, 22, 22, 0], [8, 96, 30, 26, 0]];
    for (const [x, y, sw, sh, vert] of signs) {
      const c = cols[(r() * cols.length) | 0], c2 = cols[(r() * cols.length) | 0];
      g.fillStyle = glow ? '#000' : '#140d24'; g.fillRect(x, y, sw, sh);
      g.strokeStyle = c; g.lineWidth = 1.6; g.strokeRect(x + 1, y + 1, sw - 2, sh - 2);
      g.strokeStyle = c2; g.lineWidth = 1.3;
      const s = Math.min(sw, sh) - 6;
      if (vert) for (let yy = y + 3; yy + s <= y + sh - 3; yy += s + 2) glyph(g, x + 3, yy, s, r);
      else for (let xx = x + 3; xx + s <= x + sw - 3; xx += s + 2) glyph(g, xx, y + 3, s, r);
    }
    g.strokeStyle = '#ffe14d'; g.lineWidth = 1.5; // a little ☺ sign up top
    ring(g, 113, 112, 7, '#ffe14d', 1.5); circ(g, 110.5, 110, 1, '#ffe14d'); circ(g, 115.5, 110, 1, '#ffe14d'); ring(g, 113, 112, 4, '#ffe14d', 1.2, 0.2 * Math.PI, 0.8 * Math.PI);
  }],
  bubblewrap: [64, 64, (g, w, h, r) => {
    g.fillStyle = '#d6edf4'; g.fillRect(0, 0, w, h);
    for (let y = -16, k = 0; y <= 80; y += 16, k++) for (let x = -16; x <= 80; x += 16) {
      const cx = x + (k & 1 ? 8 : 0) + 4, cy = y + 4;
      if ((((cx + 64) * 7 + (cy + 64) * 13) % 11) === 3) { // popped: flat and crinkly
        line(g, [[cx - 4, cy - 1], [cx - 1, cy + 2], [cx + 2, cy - 2], [cx + 4, cy + 1]], '#a9cbd8', 1); continue;
      }
      circ(g, cx + 1, cy + 1.5, 6.2, '#9fc6d4'); circ(g, cx, cy, 6.2, '#c4e4ef'); ring(g, cx, cy, 6, '#8dbccc', 1);
      ell(g, cx - 2, cy - 2.4, 2.3, 1.4, -0.6, '#ffffff'); circ(g, cx + 2.6, cy + 2.4, 0.8, '#f4fbff');
    }
  }],
  cheese: [64, 64, (g, w, h, r) => {
    g.fillStyle = '#ffd23f'; g.fillRect(0, 0, w, h);
    grain(g, w, h, r, 18);
    for (let i = 0; i < 9; i++) {
      const x = r() * w, y = r() * h, s = 2 + r() * 6;
      around(w, h, (dx, dy) => { circ(g, x + dx, y + dy, s + 0.8, '#f0b828'); circ(g, x + dx, y + dy, s, '#b77a0e'); circ(g, x + dx + s * 0.25, y + dy + s * 0.3, s * 0.78, '#e4a21a'); });
    }
  }],
  denim: [64, 64, (g, w, h, r) => {
    pix(g, w, h, (x, y) => { const k = (r() - 0.5) * 22, t = ((x - y + 64) & 3) < 2; return t ? [44 + k, 74 + k, 138 + k] : [32 + k, 56 + k, 112 + k]; });
    for (let i = 0; i < 90; i++) { g.fillStyle = 'rgba(190,210,250,0.5)'; g.fillRect((r() * w) | 0, (r() * h) | 0, 1, 1); }
    g.fillStyle = 'rgba(10,20,50,0.45)'; g.fillRect(0, 44, w, 2);
    g.fillStyle = '#e8a33a'; for (let x = 0; x < w; x += 5) { g.fillRect(x, 40, 3, 1); g.fillRect(x + 2, 48, 3, 1); }
  }],
  plaid: [64, 64, (g, w, h) => {
    g.fillStyle = '#b3202a'; g.fillRect(0, 0, w, h);
    const bands = [[6, 14, 'rgba(20,40,24,0.72)'], [34, 9, 'rgba(22,32,80,0.7)'], [50, 2, 'rgba(255,225,77,0.95)'], [25, 2, 'rgba(244,244,244,0.7)'], [57, 2, 'rgba(20,40,24,0.8)']];
    for (const [p, s, c] of bands) { g.fillStyle = c; g.fillRect(p, 0, s, h); }
    for (const [p, s, c] of bands) { g.fillStyle = c; g.fillRect(0, p, w, s); }
    g.fillStyle = 'rgba(0,0,0,0.12)'; for (let y = 0; y < h; y++) for (let x = (y & 1); x < w; x += 2) g.fillRect(x, y, 1, 1);
  }],
  receipt: [128, 128, (g, w, h, r) => {
    g.fillStyle = '#f6f3ea'; g.fillRect(0, 0, w, h);
    grain(g, w, h, r, 8);
    g.font = 'bold 9px monospace'; g.textBaseline = 'top';
    const rows = [['  JANK MART #0069', 1], ['----------------------', 0.6], ['1x BANANA       0.99', 1], ['1x MARBLES(BAG) 4.20', 1], ['1x BREAD        2.50', 0.8], ['AMMO (BULK)    69.00', 1], ['1x DIGNITY      0.00', 0.5], ['SUBTOTAL       76.69', 1], ['TAX (JANK)      6.66', 0.9], ['TOTAL          83.35', 1], ['THANK U COME AGAIN ☺', 0.7]];
    rows.forEach(([t, a], i) => { g.fillStyle = `rgba(40,40,46,${a})`; g.fillText(t, 2, 2 + i * 9.6); });
    for (let x = 14; x < 114;) { const bw = 1 + ((r() * 3) | 0); g.fillStyle = '#26262c'; g.fillRect(x, 110, bw, 14); x += bw + 1 + ((r() * 2) | 0); }
  }],
  pizza: [64, 64, (g, w, h, r) => {
    g.fillStyle = '#f2b632'; g.fillRect(0, 0, w, h);
    for (let i = 0; i < 14; i++) { const x = r() * w, y = r() * h, s = 3 + r() * 5, a = r() * 3; around(w, h, (dx, dy) => ell(g, x + dx, y + dy, s, s * 0.7, a, i & 1 ? '#f8d462' : '#e09a22')); }
    for (let i = 0; i < 5; i++) { const x = r() * w, y = r() * h; around(w, h, (dx, dy) => ell(g, x + dx, y + dy, 2.2, 1.5, 0.5, '#c8321e')); }
    for (let i = 0; i < 5; i++) {
      const x = r() * w, y = r() * h, sp = [[r() - 0.5, r() - 0.5], [r() - 0.5, r() - 0.5], [r() - 0.5, r() - 0.5]];
      around(w, h, (dx, dy) => {
        circ(g, x + dx + 0.8, y + dy + 1, 6.4, 'rgba(120,40,0,0.35)'); circ(g, x + dx, y + dy, 6.2, '#8a1a12'); circ(g, x + dx, y + dy, 5.4, '#b5241c');
        for (const [a, b] of sp) circ(g, x + dx + a * 7, y + dy + b * 7, 0.9, '#6e120c');
        ell(g, x + dx - 2, y + dy - 2.2, 1.8, 0.8, -0.6, 'rgba(255,200,170,0.55)');
      });
    }
    for (let i = 0; i < 5; i++) { const x = r() * w, y = r() * h, a = r() * 3; around(w, h, (dx, dy) => ell(g, x + dx, y + dy, 2.4, 1.1, a, '#2f8a2a')); }
    for (let i = 0; i < 8; i++) { const x = r() * w, y = r() * h; around(w, h, (dx, dy) => circ(g, x + dx, y + dy, 1, '#6a3a12')); }
  }],
  leopard: [64, 64, (g, w, h, r) => {
    g.fillStyle = '#e3a85a'; g.fillRect(0, 0, w, h);
    grain(g, w, h, r, 14);
    for (let j = 0; j < 4; j++) for (let i = 0; i < 4; i++) {
      const x = i * 16 + 8 + (r() - 0.5) * 7 + (j & 1) * 6, y = j * 16 + 8 + (r() - 0.5) * 7, s = 4 + r() * 1.6, rot = r() * TAU;
      const gaps = [r(), r(), r()];
      around(w, h, (dx, dy) => {
        ell(g, x + dx, y + dy, s * 0.8, s * 0.65, rot, '#b56c26');
        g.lineCap = 'round';
        for (let k = 0; k < 3; k++) { const a0 = rot + (k / 3) * TAU + gaps[k] * 0.4; ring(g, x + dx, y + dy, s, '#24130a', 2.3, a0, a0 + 1.5); }
        g.lineCap = 'butt';
      });
    }
    for (let i = 0; i < 10; i++) { const x = r() * w, y = r() * h, s = 1 + r() * 0.8; around(w, h, (dx, dy) => circ(g, x + dx, y + dy, s, '#24130a')); }
  }],
  zebra: [64, 64, (g, w, h) => pix(g, w, h, (x, y) => {
    const u = (TAU * x) / 64, v = (TAU * y) / 64;
    const s = Math.sin(v * 3 + 1.7 * Math.sin(u) + 0.7 * Math.sin(u * 2 + 1) + 0.4 * Math.sin(v * 2 + u));
    return s > 0.18 ? [20, 20, 22] : [245, 245, 238];
  })],
  stained: [128, 128, (g, w, h, r, glow) => {
    const pal = ['#ff4fd8', '#4fd8ff', '#ffe14d', '#39ff14', '#ff3030', '#8a4fff', '#2f6bff', '#ff9a1a'].map(hexRgb);
    const v = voronoi(w, h, 18, r);
    const cc = v.pts.map((_, i) => pal[i % pal.length]);
    pix(g, w, h, (x, y) => {
      const i = y * w + x, e = v.d2[i] - v.d1[i];
      if (e < 2.6) return glow ? [0, 0, 0] : [20, 16, 24];
      const c = cc[v.id[i]], k = glow ? 0.8 : 0.7 + Math.min(0.5, e / 30) - Math.min(0.25, v.d1[i] / 60);
      return [Math.min(255, c[0] * k), Math.min(255, c[1] * k), Math.min(255, c[2] * k)];
    });
  }],
  circuit: [64, 64, (g, w, h, r, glow) => {
    g.fillStyle = glow ? '#000' : '#0b4d2a'; g.fillRect(0, 0, w, h);
    if (!glow) { g.fillStyle = 'rgba(0,0,0,0.18)'; for (let i = 0; i < w; i += 4) { g.fillRect(i, 0, 1, h); g.fillRect(0, i, w, 1); } }
    const tc = glow ? '#ffffff' : '#c8a040', paths = [];
    for (let i = 0; i < 9; i++) {
      let x = ((r() * 8) | 0) * 8, y = ((r() * 8) | 0) * 8; const pts = [[x, y]];
      for (let k = 0; k < 4; k++) { const d = (r() * 4) | 0, l = 8 + ((r() * 3) | 0) * 8; if (d === 0) x += l; else if (d === 1) y += l; else if (d === 2) { x += l * 0.5; y += l * 0.5; } else { x += l * 0.5; y -= l * 0.5; } pts.push([x, y]); }
      paths.push(pts);
    }
    around(w, h, (dx, dy) => {
      for (const p of paths) { line(g, p.map(([x, y]) => [x + dx, y + dy]), tc, 1.6); for (const q of [p[0], p[p.length - 1]]) { circ(g, q[0] + dx, q[1] + dy, 2.4, tc); if (!glow) circ(g, q[0] + dx, q[1] + dy, 0.9, '#062a16'); } }
    });
    if (!glow) {
      const chip = (x, y, cw, ch) => { g.fillStyle = '#c8ccd4'; for (let i = 2; i < cw - 1; i += 3) { g.fillRect(x + i, y - 2, 1, ch + 4); } g.fillStyle = '#16161a'; g.fillRect(x, y, cw, ch); g.fillStyle = '#2a2a30'; g.fillRect(x + 1, y + 1, cw - 2, 1); circ(g, x + 2.5, y + ch - 2.5, 0.8, '#55555c'); };
      chip(36, 18, 16, 9); chip(6, 42, 11, 7);
    }
  }],
  crt: [32, 32, (g, w, h, r, glow) => {
    g.fillStyle = '#060608'; g.fillRect(0, 0, w, h);
    const sub = [[255, 40, 60], [40, 255, 90], [60, 110, 255]];
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      if ((y & 3) === 3 || (x & 3) === 3) continue;
      const c = sub[x & 3], k = glow ? 1 : 0.32;
      g.fillStyle = `rgb(${c[0] * k | 0},${c[1] * k | 0},${c[2] * k | 0})`; g.fillRect(x, y, 1, 1);
    }
  }],
  sheet: [128, 128, (g, w, h, r) => {
    g.fillStyle = '#fbfbf7'; g.fillRect(0, 0, w, h);
    g.fillStyle = '#4fbf5a'; g.fillRect(0, 0, w, 16); g.fillStyle = '#e4e6e0'; g.fillRect(0, 16, 16, h);
    const hi = { '3,2': '#ffe14d', '5,4': '#ff9ad5', '2,6': '#ffe14d', '6,7': '#9fe3ff' };
    for (const [k, c] of Object.entries(hi)) { const [cx, cy] = k.split(',').map(Number); g.fillStyle = c; g.fillRect(cx * 16, cy * 16, 16, 16); }
    g.fillStyle = '#c4c6c0'; for (let i = 0; i <= 128; i += 16) { g.fillRect(i, 0, 1, h); g.fillRect(0, i, w, 1); }
    g.font = 'bold 9px monospace'; g.textBaseline = 'middle'; g.textAlign = 'center';
    g.fillStyle = '#ffffff'; 'ABCDEFG'.split('').forEach((c, i) => g.fillText(c, 16 + i * 16 + 8, 8.5));
    g.fillStyle = '#55585a'; for (let j = 1; j < 8; j++) g.fillText(String(j), 8, j * 16 + 8.5);
    g.font = '8px monospace';
    for (let j = 1; j < 8; j++) for (let i = 1; i < 8; i++) {
      if (i === 4 && j === 3) { g.fillStyle = '#e01818'; g.fillText('#REF', i * 16 + 8, j * 16 + 8.5); continue; }
      if (r() < 0.2) continue;
      const n = r() < 0.15 ? '69' : String((r() * 99) | 0);
      g.fillStyle = '#1a1a1e'; g.fillText(n, i * 16 + 8, j * 16 + 8.5);
    }
    g.strokeStyle = '#1a7a2a'; g.lineWidth = 2; g.strokeRect(65, 49, 15, 15); // the selected cell
  }],
  memo: [128, 128, (g, w, h, r) => {
    g.fillStyle = '#f7f5ee'; g.fillRect(0, 0, w, h);
    grain(g, w, h, r, 6);
    g.textBaseline = 'top'; g.fillStyle = '#111'; g.font = 'bold 15px sans-serif'; g.fillText('MEMO', 6, 4);
    g.fillRect(6, 21, 116, 2);
    g.font = '8px sans-serif'; g.fillStyle = '#333';
    ['TO: all associates', 'FROM: management ☺', 'RE: fun is now mandatory'].forEach((t, i) => g.fillText(t, 6, 27 + i * 10));
    g.fillStyle = '#9a9aa0'; for (let i = 0; i < 6; i++) { let x = 6; while (x < 118) { const l = 4 + r() * 14; g.fillRect(x, 62 + i * 9, Math.min(l, 120 - x), 3); x += l + 3; } }
    g.save(); g.translate(78, 92); g.rotate(-0.28); g.strokeStyle = 'rgba(220,30,40,0.85)'; g.lineWidth = 2.5; g.strokeRect(-26, -9, 52, 18);
    g.fillStyle = 'rgba(220,30,40,0.85)'; g.font = 'bold 12px sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('URGENT', 0, 1); g.restore();
    around(w, h, (dx, dy) => { ring(g, 28 + dx, 108 + dy, 13, 'rgba(120,70,30,0.32)', 2.5); ring(g, 28 + dx, 108 + dy, 11, 'rgba(120,70,30,0.15)', 1.2); });
  }],
  holo: [64, 64, (g, w, h, r, glow) => {
    g.fillStyle = glow ? '#000' : '#c3c7d4'; g.fillRect(0, 0, w, h);
    if (!glow) { for (let i = -64; i < 64; i += 3) line(g, [[i, 0], [i + 64, 64]], 'rgba(255,255,255,0.18)', 1); grain(g, w, h, r, 12); } else { r(); }
    const star = (x, y, s, c) => { g.fillStyle = c; g.beginPath(); g.moveTo(x, y - s); g.lineTo(x + s * 0.28, y - s * 0.28); g.lineTo(x + s, y); g.lineTo(x + s * 0.28, y + s * 0.28); g.lineTo(x, y + s); g.lineTo(x - s * 0.28, y + s * 0.28); g.lineTo(x - s, y); g.lineTo(x - s * 0.28, y - s * 0.28); g.closePath(); g.fill(); };
    const rr = rng(77);
    for (let i = 0; i < 9; i++) { const x = rr() * w, y = rr() * h, s = 2.5 + rr() * 4; around(w, h, (dx, dy) => star(x + dx, y + dy, s, glow ? '#ffffff' : '#f4f6ff')); }
    for (let i = 0; i < 30; i++) { const x = rr() * w, y = rr() * h; g.fillStyle = glow ? '#bbb' : '#ffffff'; g.fillRect(x | 0, y | 0, 1, 1); }
  }],
  glitch: [64, 64, (g, w, h, r) => {
    const pal = ['#ff00dc', '#4fd8ff', '#39ff14', '#ffe14d', '#111116', '#111116', '#f4f4f4', '#2a1a4a'];
    for (let y = 0; y < h; y += 8) for (let x = 0; x < w; x += 8) { g.fillStyle = pal[(r() * pal.length) | 0]; g.fillRect(x, y, 8, 8); }
    for (let i = 0; i < 10; i++) { const y = (r() * h) | 0, x = (r() * w) | 0; g.drawImage(g.canvas, x, y, 16, 3, (x + 6 + r() * 20) % w, y, 16 + r() * 24, 3); } // smeared rows
    for (let i = 0; i < 8; i++) { const y = (r() * h) | 0; g.fillStyle = pal[(r() * 4) | 0]; g.fillRect(0, y, w, 1); }
    for (let i = 0; i < 40; i++) { g.fillStyle = r() < 0.5 ? '#ffffff' : '#000000'; g.fillRect((r() * w) | 0, (r() * h) | 0, 2, 1); }
  }],
  meat: [64, 64, (g, w, h, r, glow) => {
    const n = fbm(w, r), q = fbm(w, r, [4, 8]);
    if (!glow) pix(g, w, h, (x, y) => {
      const wx = x + (q(x, y) - 0.5) * 30, wy = y + (q(y + 17, x + 5) - 0.5) * 30; // warped twice: marbled, not stripy
      const m = n(wx, wy), fat = Math.abs(Math.sin(n(wy * 0.7 + 9, wx * 0.7) * 14)), k = (r() - 0.5) * 14;
      if (fat < 0.12) return [240 + k * 0.4, 214 + k, 200 + k];
      if (fat < 0.22) return [214 + k, 128 + k, 132 + k];
      return m > 0.56 ? [178 + k, 30 + k * 0.5, 48 + k * 0.5] : m > 0.42 ? [138 + k, 18, 38] : [92 + k, 8, 30];
    }); else { g.fillStyle = '#000'; g.fillRect(0, 0, w, h); }
    const vr = rng(9);
    for (let i = 0; i < 6; i++) {
      let x = vr() * w, y = vr() * h, a = vr() * TAU; const pts = [[x, y]];
      for (let k = 0; k < 8; k++) { a += (vr() - 0.5) * 1.4; x += Math.cos(a) * 5; y += Math.sin(a) * 5; pts.push([x, y]); }
      around(w, h, (dx, dy) => line(g, pts.map(([px, py]) => [px + dx, py + dy]), glow ? '#ffffff' : '#4a1a5a', i < 2 ? 1.8 : 1.1));
    }
  }],
  ketchup: [64, 64, (g, w, h, r) => {
    g.fillStyle = '#d81e1e'; g.fillRect(0, 0, w, h);
    for (let i = 0; i < 10; i++) { const x = r() * w, y = r() * h; around(w, h, (dx, dy) => ell(g, x + dx, y + dy, 5, 2.5, 0.3, 'rgba(255,90,70,0.25)')); }
    g.lineCap = 'round'; g.lineJoin = 'round';
    for (const [y0, a] of [[16, 0], [48, 8]]) around(w, h, (dx, dy) => {
      const pts = []; for (let x = -8; x <= 72; x += 8) pts.push([x + dx + a * 0, y0 + dy + ((x / 8) & 1 ? -5 : 5)]);
      line(g, pts, '#b07a00', 5); line(g, pts, '#ffcc12', 3.6); line(g, pts.map(([x, y]) => [x - 0.6, y - 1]), '#ffe680', 1);
    });
    g.lineCap = 'butt'; g.lineJoin = 'miter';
  }],
  creamsicle: [64, 64, (g, w, h) => pix(g, w, h, (x, y) => {
    const u = (TAU * x) / 64, v = (TAU * y) / 64, sw = Math.sin(v * 2 + 1.6 * Math.sin(u + 0.5 * Math.sin(v)));
    return sw > 0.35 ? [255, 243, 222] : sw > 0.25 ? [255, 196, 140] : [255, 132, 36];
  })],
  bubblegum: [64, 64, (g, w, h, r) => {
    g.fillStyle = '#ff92c9'; g.fillRect(0, 0, w, h);
    for (let i = 0; i < 11; i++) {
      const x = r() * w, y = r() * h, s = 2.5 + r() * 6.5;
      around(w, h, (dx, dy) => { circ(g, x + dx, y + dy, s, '#9fe3ff'); ring(g, x + dx, y + dy, s, '#62bfe8', 1); ell(g, x + dx - s * 0.35, y + dy - s * 0.4, s * 0.35, s * 0.2, -0.6, '#ffffff'); });
    }
  }],
  corp: [128, 128, (g, w, h, r, glow) => {
    g.fillStyle = glow ? '#000' : '#141414'; g.fillRect(0, 0, w, h);
    if (!glow) { g.fillStyle = '#1f1f1f'; for (let i = -128; i < 128; i += 12) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i + 6, 0); g.lineTo(i + 134, 128); g.lineTo(i + 128, 128); g.fill(); } }
    const ink = glow ? '#000' : '#141414';
    smiley(g, 30, 32, 21, glow ? '#ffffff' : '#ffe14d', ink); smiley(g, 94, 96, 21, glow ? '#ffffff' : '#ffe14d', ink);
    g.textAlign = 'center'; g.textBaseline = 'middle'; g.font = 'bold 26px sans-serif';
    g.fillStyle = glow ? '#ffffff' : '#ff4fd8'; g.fillText('CORP', 94, 34); g.fillText('CORP', 30, 98);
    g.font = 'bold 8px sans-serif'; g.fillStyle = glow ? '#555' : '#ffe14d'; g.fillText('™ have a nice day', 94, 54); g.fillText('™ have a nice day', 30, 118);
  }],
};
function crackle(g, w, h, r, base, crack, fine, lw, glow) {
  const big = voronoi(w, h, 16, r), small = voronoi(w, h, 55, r), b = hexRgb(base), c = hexRgb(crack), f = fine && hexRgb(fine);
  pix(g, w, h, (x, y) => {
    const i = y * w + x;
    if (big.d2[i] - big.d1[i] < lw) return c;
    if (f && small.d2[i] - small.d1[i] < 0.9) return f;
    const k = glow ? 0 : Math.sin(x * 0.11 + y * 0.07) * 5; return [b[0] + k, b[1] + k, b[2] + k];
  });
}

const texCache = {};
function patTex(name, glow) {
  const key = name + (glow ? ':g' : '');
  if (texCache[key]) return texCache[key];
  const [w, h, draw] = TX[name];
  const c = mkCanvas(w, h), g = c.getContext('2d', { willReadFrequently: true });
  let seed = 0; for (const ch of name) seed = (seed * 31 + ch.charCodeAt(0)) | 0;
  draw(g, w, h, rng(seed), !!glow);
  const t = new THREE.CanvasTexture(c);
  t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestMipmapNearestFilter; t.anisotropy = 1; // crunchy pixels at every preset
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace;
  return (texCache[key] = t);
}

// one tiny studio for the clear-coat shine (an equirect canvas: every renderer, the menu preview too, makes its own copy)
let ENV = null;
function studio() {
  if (ENV) return ENV;
  const c = mkCanvas(128, 64), g = c.getContext('2d');
  const gr = g.createLinearGradient(0, 0, 0, 64);
  gr.addColorStop(0, '#b8c4ff'); gr.addColorStop(0.45, '#ffffff'); gr.addColorStop(0.52, '#ffd0f0'); gr.addColorStop(0.6, '#3a2a48'); gr.addColorStop(1, '#120a1a');
  g.fillStyle = gr; g.fillRect(0, 0, 128, 64);
  g.fillStyle = '#ffffff'; g.fillRect(14, 10, 22, 12); g.fillRect(74, 6, 30, 9); g.fillStyle = '#ffe9a8'; g.fillRect(52, 20, 8, 8); g.fillStyle = '#9fe8ff'; g.fillRect(110, 16, 10, 14);
  ENV = new THREE.CanvasTexture(c);
  ENV.mapping = THREE.EquirectangularReflectionMapping; ENV.colorSpace = THREE.SRGBColorSpace;
  return ENV;
}

// ------------------------------------------------------------ the shader
export const packTime = { value: 0 };
const JANK = jankify(new THREE.MeshBasicMaterial()).onBeforeCompile; // the potato vertex snap, same as every other material
const PARS = /* glsl */`
varying vec3 vWp; varying vec3 vWn;
uniform float uDen; uniform vec2 uRep; uniform vec2 uVel; uniform float uTime; uniform vec3 uGlowCol; uniform float uGlowK;
#ifndef WP_NOTEX
uniform sampler2D uTri;
#endif
#ifdef WP_GLOW
uniform sampler2D uGlow;
#endif
vec4 wpTri(sampler2D t, vec3 p, vec3 w) {
  vec2 o = uVel * uTime;
  return texture2D(t, p.zy * uRep + o) * w.x + texture2D(t, p.xz * uRep + o) * w.y + texture2D(t, p.xy * uRep + o) * w.z;
}
vec3 wpHue(float h) { return clamp(abs(fract(h + vec3(0., 2. / 3., 1. / 3.)) * 6. - 3.) - 1., 0., 1.); }
float wpHash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
`;
const MAP = /* glsl */`
vec3 wpw = pow(abs(normalize(vWn)), vec3(6.)); wpw /= wpw.x + wpw.y + wpw.z + 1e-5;
vec3 wpp = vWp * uDen;
#if WP_FX == 4
  float wgb = floor(wpp.y * 2.5) + floor(uTime * 6.), wgj = wpHash(vec2(wgb, 1.7));
  wpp.xz += step(0.7, wgj) * (wgj - 0.7) * 5.;
#endif
#ifdef WP_NOTEX
  vec4 wpt = vec4(1.);
#else
  vec4 wpt = wpTri(uTri, wpp, wpw);
#endif
#if WP_FX == 4
  wpt.r = wpTri(uTri, wpp + vec3(0.05, 0., 0.05), wpw).r;
  if (wpHash(vec2(wgb, 9.1)) > 0.9) wpt.rgb = 1. - wpt.rgb;
#endif
#if WP_FX == 8
  float wbt = fract(uTime * 1.1), wbeat = exp(-wbt * 22.) + 0.6 * exp(-max(0., wbt - 0.16) * 22.) * step(0.16, wbt);
  wpt.rgb *= 0.85 + 0.3 * wbeat;
#endif
diffuseColor.rgb *= wpt.rgb;
`;
const EMIS = /* glsl */`
#ifdef WP_GLOW
  vec3 wpg = wpTri(uGlow, wpp, wpw).rgb;
#endif
#if WP_FX == 1
  { float fr = 1. - abs(dot(normal, normalize(vViewPosition)));
    vec3 hh = wpHue(fr * 1.3 + dot(wpp, vec3(0.13, 0.21, 0.17)) + uTime * 0.12);
    totalEmissiveRadiance += hh * (0.18 + 0.7 * fr * fr) + wpg * hh * (0.6 + 0.6 * sin(uTime * 5. + dot(wpp, vec3(3.)))); }
#elif WP_FX == 2
  { vec3 rv = reflect(-normalize(vViewPosition), normal); // a fake sky reflected in molten metal that keeps flowing
    float y = rv.y * 1.3 + 0.45 * sin(vWp.z * 17. + vWp.y * 11. + rv.x * 2. + uTime * 1.8) + 0.25 * sin(vWp.x * 23. + vWp.z * 7. - uTime * 2.6);
    y += 0.18; vec3 c = y > 0. ? mix(vec3(1.), vec3(0.2, 0.62, 1.), smoothstep(0., 0.55, y)) : mix(vec3(1., 0.3, 0.8), vec3(0.1, 0.05, 0.18), smoothstep(0., 0.22, -y));
    totalEmissiveRadiance += (c + smoothstep(0.06, 0., abs(y)) * 0.7) * uGlowK; }
#elif WP_FX == 3
  { float roll = smoothstep(0.7, 1., fract(vWp.y * 3. - uTime * 0.45)); // a bright bar rolling up the screen
    vec3 bars = wpHue(floor(fract(vWp.z * 5. + vWp.x * 5.) * 7.) / 7.) * 0.85 + 0.15; // colour bars test pattern
    totalEmissiveRadiance += wpg * bars * (0.9 + 1.6 * roll) * (0.92 + 0.08 * sin(uTime * 50.)); }
#elif WP_FX == 4
  totalEmissiveRadiance += wpg * uGlowK;
#elif WP_FX == 5
  { vec3 cell = floor(wpp * 2.);
    float fl = step(0.12, wpHash(cell.xy + cell.z * 7. + floor(uTime * 7.)));
    totalEmissiveRadiance += wpg * uGlowK * (0.8 + 0.2 * sin(uTime * 9. + cell.x * 3.)) * fl; }
#elif WP_FX == 6
  { float sw = pow(0.5 + 0.5 * sin(dot(wpp, vec3(1., 0.6, 0.8)) * 2. - uTime * 2.5), 10.);
    totalEmissiveRadiance += wpg * uGlowCol * (0.3 + 1.6 * sw); }
#elif WP_FX == 7
  { float pu = pow(fract(dot(wpp, vec3(0.6, 0.4, 0.8)) * 0.5 - uTime * 0.7), 8.);
    totalEmissiveRadiance += wpg * uGlowCol * (0.12 + 2. * pu); }
#elif WP_FX == 8
  totalEmissiveRadiance += wpg * uGlowCol * (0.08 + 1.4 * wbeat);
#elif WP_FX == 9
  totalEmissiveRadiance += wpg * uGlowK;
#elif WP_FX == 10
  totalEmissiveRadiance += wpg * diffuseColor.rgb * uGlowK * (0.55 + 0.45 * sin(uTime * 3.));
#endif
`;
const UNI = new WeakMap();
function packCompile(sh, r) {
  JANK(sh, r);
  const u = UNI.get(this);
  if (!u) return;
  Object.assign(sh.uniforms, u);
  sh.vertexShader = 'varying vec3 vWp; varying vec3 vWn;\n' + sh.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\nvWp = transformed; vWn = objectNormal;');
  sh.fragmentShader = PARS + sh.fragmentShader
    .replace('#include <map_fragment>', MAP)
    .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n' + EMIS);
}

// ps = pattern scale (small weapons get finer patterns). f = the brightness factor skins.js works out for that part (dark parts stay darker, zoned wraps get lifted)
export function packMat(id, f, ps = 1) {
  const p = PACK[id];
  if (!p) return null;
  const s = p.spec;
  const m = new THREE.MeshStandardMaterial({
    color: new THREE.Color(s.c ?? 0xffffff).multiplyScalar(s.tx ? 0.55 + f * 0.45 : f),
    roughness: s.r ?? 0.28, metalness: s.m ?? 0, envMap: studio(), envMapIntensity: s.env ?? 0.8,
  });
  if (!s.tx && !s.fx) return jankify(m); // a plain solid needs nothing else
  const defs = { WP_FX: s.fx || 0 };
  if (!s.tx) defs.WP_NOTEX = '';
  if (s.glow) defs.WP_GLOW = '';
  m.defines = defs;
  UNI.set(m, {
    uTri: { value: s.tx ? patTex(s.tx) : null }, uGlow: { value: s.glow ? patTex(s.glow, true) : null },
    uDen: { value: (s.den || 8) * ps }, uRep: { value: new THREE.Vector2(...(s.rep || [1, 1])) }, uVel: { value: new THREE.Vector2(...(s.vel || [0, 0])) },
    uTime: packTime, uGlowCol: { value: new THREE.Color(s.gc ?? 0xffffff) }, uGlowK: { value: s.gk ?? 1 },
  });
  m.onBeforeCompile = packCompile;
  return m;
}
// one clock for every animated pack wrap. wrapped so mediump floats stay sharp; every scroll speed loops cleanly at 1000 s
export function packTick(now) { packTime.value = (now / 1000) % 1000; }
