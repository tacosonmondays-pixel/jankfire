// Sprays: graffiti you paint on the map with Z. Every one is drawn here on a canvas (fat letters, drips, overspray),
// then laid flat on the face you hit and cut to the map faces in that plane, so it never hangs off an edge.
import * as THREE from 'three';
import { G } from './ctx.js';
import { fx } from './fx.js';
import { sfx } from './audio.js';
import { BOXES } from '/shared/map.js';
import { raycast, query } from '/shared/physics.js';
import { COSMETICS, SPRAY } from '/shared/cosmetics.js';

const PX = 128; // texture size: crunchy like the rest of the world
const PAD = 8; // the border stays see-through: decal corners outside the square clamp to it
const TAU = Math.PI * 2;
const INK = '#141018';

// same art for everyone: the randomness is seeded by the spray id
function rng(str) {
  let s = 7;
  for (const ch of str) s = (Math.imul(s, 31) + ch.charCodeAt(0)) | 0;
  return () => { // mulberry32
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ---------------------------------------------------------------- letters
// a fat bubble alphabet: [width, ...centre lines] in a width x 1 box (y down), drawn as thick round strokes
const ell = (cx, cy, rx, ry, n = 18) => Array.from({ length: n + 1 }, (_, i) => [cx + Math.cos((i / n) * TAU) * rx, cy + Math.sin((i / n) * TAU) * ry]);
const GLYPH = {
  A: [0.9, [[0.02, 1], [0.45, 0], [0.88, 1]], [[0.22, 0.64], [0.68, 0.64]]],
  B: [0.78, [[0.08, 0.5], [0.08, 0], [0.48, 0], [0.7, 0.12], [0.7, 0.36], [0.48, 0.5], [0.08, 0.5], [0.08, 1], [0.52, 1], [0.78, 0.86], [0.78, 0.62], [0.52, 0.5]]],
  E: [0.72, [[0.72, 0], [0.06, 0], [0.06, 1], [0.72, 1]], [[0.06, 0.5], [0.56, 0.5]]],
  F: [0.7, [[0.7, 0], [0.06, 0], [0.06, 1]], [[0.06, 0.5], [0.54, 0.5]]],
  G: [0.88, [[0.86, 0.14], [0.72, 0.01], [0.42, 0], [0.13, 0.12], [0.04, 0.5], [0.13, 0.88], [0.42, 1], [0.72, 0.97], [0.88, 0.82], [0.88, 0.6], [0.64, 0.6]]],
  I: [0.16, [[0.08, 0], [0.08, 1]]],
  J: [0.66, [[0.16, 0], [0.66, 0]], [[0.6, 0], [0.6, 0.7], [0.42, 0.98], [0.16, 0.94], [0.02, 0.72]]],
  K: [0.8, [[0.06, 0], [0.06, 1]], [[0.78, 0], [0.1, 0.58]], [[0.34, 0.4], [0.8, 1]]],
  L: [0.66, [[0.06, 0], [0.06, 1], [0.66, 1]]],
  N: [0.8, [[0.06, 1], [0.06, 0], [0.74, 1], [0.74, 0]]],
  O: [0.86, ell(0.43, 0.5, 0.43, 0.5)],
  P: [0.74, [[0.06, 1], [0.06, 0], [0.48, 0], [0.72, 0.13], [0.72, 0.37], [0.48, 0.5], [0.06, 0.5]]],
  R: [0.8, [[0.06, 1], [0.06, 0], [0.44, 0], [0.66, 0.12], [0.66, 0.36], [0.44, 0.48], [0.06, 0.48]], [[0.3, 0.48], [0.8, 1]]], // the leg kicks out wide so it doesn't read as an N
  W: [1.1, [[0, 0], [0.24, 1], [0.55, 0.34], [0.86, 1], [1.1, 0]]],
  Z: [0.76, [[0.04, 0], [0.74, 0], [0.04, 1], [0.76, 1]]],
  '?': [0.66, [[0.04, 0.24], [0.2, 0.03], [0.48, 0], [0.66, 0.18], [0.62, 0.4], [0.33, 0.56], [0.33, 0.7]], [[0.33, 0.96], [0.33, 0.97]]],
  ' ': [0.4],
};
// a = top colour, b = bottom colour, d = the 3d drop behind the letters
const PAINT = {
  lime: { a: '#d4ff5a', b: '#22c23c', d: '#3b0d5e' },
  pink: { a: '#ffb0ee', b: '#e021b8', d: '#1b1a6b' },
  cyan: { a: '#b4f6ff', b: '#1f80ff', d: '#0c1d4a' },
  sun: { a: '#fff47a', b: '#ff7a1a', d: '#5e1d00' },
  red: { a: '#ff8a70', b: '#d10f1f', d: '#2c0012' },
  baby: { a: '#e0f8ff', b: '#62b4ff', d: '#ff4fd8' },
  grape: { a: '#ecb8ff', b: '#7d2cff', d: '#16002e' },
  bone: { a: '#ffffff', b: '#b9c3d3', d: '#2c2c3c' },
  rainbow: { rainbow: ['#ff3b3b', '#ff9a1a', '#ffe14d', '#5dff4f', '#4fd8ff', '#6a5cff', '#ff4fd8'], d: '#2a0a4a' },
};

function dot(x, X, Y, r, col, al = 1) {
  if (X < 6 || Y < 6 || X > PX - 6 || Y > PX - 6) return; // keep the border clean
  x.globalAlpha = al; x.fillStyle = col;
  x.beginPath(); x.arc(X, Y, r, 0, TAU); x.fill();
  x.globalAlpha = 1;
}
// a drip: a line straight down with a blob at the end. e = how much fatter (for the outline pass)
function drip(x, d, e) {
  x.lineWidth = d.w + 2 * e;
  x.beginPath(); x.moveTo(d.x, d.y0); x.lineTo(d.x, d.y1); x.stroke();
  x.beginPath(); x.arc(d.x, d.y1, d.w * 0.62 + e, 0, TAU); x.fill();
}
const dr = (X, y0, len, w) => ({ x: X, y0, y1: y0 + len, w });
function sparkle(x, X, Y, s) {
  x.beginPath(); x.moveTo(X, Y - s);
  for (const [a, b] of [[1, 0], [0, 1], [-1, 0], [0, -1]]) x.quadraticCurveTo(X, Y, X + a * s, Y + b * s);
  x.strokeStyle = INK; x.lineWidth = 2; x.stroke();
  x.fillStyle = '#ffffff'; x.fill();
}
const vg = (x, y0, y1, a, b) => { const g = x.createLinearGradient(0, y0, 0, y1); g.addColorStop(0, a); g.addColorStop(1, b); return g; };

// rows of words ([text, paint]) as fat outlined letters with a 3d drop, drips, a shine and overspray.
// o.box = [x0, y0, x1, y1] to fit in, o.drips (on by default), o.sparkle = how many, o.glow = a colour behind it all, o.rot = tilt
function letters(x, rnd, rows, o = {}) {
  const [bx0, by0, bx1, by1] = o.box || [PAD, PAD, PX - PAD, PX - PAD];
  const K = 0.3, OUT = 0.075, EXT = 0.07, GAP = 0.2, ROWGAP = 0.06, LEAN = 0.18;
  const dripRoom = o.drips === false ? 0 : 0.3, extra = K + 2 * OUT + EXT;
  const lines = rows.map((row) => {
    const out = [];
    row.forEach(([text, paint], wi) => { if (wi) out.push({ ch: ' ', paint }); for (const ch of text) out.push({ ch, paint }); });
    return out;
  });
  const glyph = (ch) => GLYPH[ch] || GLYPH[' '];
  const width = (ln) => ln.reduce((s, l, i) => s + glyph(l.ch)[0] + (i ? GAP : 0), 0);
  // letter height H, and a horizontal squeeze sx so the widest row fits (letters get taller, not tinier)
  const maxW = Math.max(...lines.map(width)), aw = bx1 - bx0, ah = by1 - by0, n = lines.length;
  const tall = n * (1 + extra) + (n - 1) * ROWGAP + dripRoom;
  const wx = extra + LEAN + 0.1; // sideways the lean and the wobble need room too
  const H = Math.min(ah / tall, aw / (maxW * 0.68 + wx));
  const sx = Math.min(1, (aw / H - wx) / maxW);
  const lw = K * H, ol = OUT * H, top = by0 + (ah - H * tall) / 2;
  x.save();
  if (o.rot) { const cx = (bx0 + bx1) / 2, cy = (by0 + by1) / 2; x.translate(cx, cy); x.rotate(o.rot); x.translate(-cx, -cy); }
  const all = [];
  lines.forEach((ln, i) => {
    const rowW = width(ln) * sx * H, y0 = top + i * H * (1 + extra + ROWGAP) + H * (K / 2 + OUT), mid = y0 + H / 2;
    let xa = (bx0 + bx1 - EXT * H - rowW) / 2;
    const rx0 = xa, rx1 = xa + rowW;
    ln.forEach((l, j) => {
      const [w, ...strokes] = glyph(l.ch);
      if (j) xa += GAP * sx * H;
      const lcx = xa + (w * sx * H) / 2;
      xa += w * sx * H;
      if (!strokes.length) return;
      // every letter a bit wonky: tilt, bounce, size
      const rot = (rnd() - 0.5) * 0.16, dy = (rnd() - 0.5) * 0.09 * H, sc = 0.94 + rnd() * 0.1, c = Math.cos(rot), s = Math.sin(rot);
      const T = ([u, v]) => {
        const X = (u - w / 2) * sx * H * sc, Y = (v - 0.5) * H * sc;
        const X2 = X * c - Y * s, Y2 = X * s + Y * c;
        return [lcx + X2 - Y2 * LEAN, mid + Y2 + dy];
      };
      const pts = strokes.map((pl) => pl.map(T));
      const path = new Path2D();
      for (const pl of pts) { path.moveTo(pl[0][0], pl[0][1]); for (const q of pl.slice(1)) path.lineTo(q[0], q[1]); }
      const L = { path, pts, paint: l.paint, y0, rx0, rx1, drips: [] };
      // drips run off the bottom of the last row
      if (i === n - 1 && o.drips !== false && (rnd() < 0.6 || j === ln.length - 1 && !all.some((a) => a.drips.length))) {
        const low = [];
        strokes.forEach((pl, a) => pl.forEach(([, v], b) => { if (v >= 0.85) low.push(pts[a][b]); }));
        if (low.length) {
          const q = low[(rnd() * low.length) | 0], dw = lw * (0.3 + rnd() * 0.2);
          const y1 = Math.min(q[1] + lw / 2 + H * (0.08 + rnd() * 0.22), PX - PAD - dw * 0.62 - ol);
          if (y1 > q[1] + lw / 2 + 1) L.drips.push({ x: q[0] + (rnd() - 0.5) * lw * 0.3, y0: q[1], y1, w: dw });
        }
      }
      all.push(L);
    });
  });
  const paintOf = (L) => {
    if (L.paint.rainbow) { const g = x.createLinearGradient(L.rx0, 0, L.rx1, 0); L.paint.rainbow.forEach((cc, i, a) => g.addColorStop(i / (a.length - 1), cc)); return g; }
    return vg(x, L.y0 - lw / 2, L.y0 + H + lw / 2, L.paint.a, L.paint.b);
  };
  x.lineCap = x.lineJoin = 'round';
  if (o.glow) { x.strokeStyle = o.glow; x.lineWidth = lw + 2 * ol + H * 0.3; for (const L of all) x.stroke(L.path); }
  // the 3d drop behind everything
  const ex = Math.max(1.5, EXT * H);
  for (const L of all) {
    x.strokeStyle = L.paint.d; x.lineWidth = lw + 2 * ol;
    for (let k = 1; k < ex + 0.5; k++) { const e = Math.min(k, ex); x.save(); x.translate(e, e); x.stroke(L.path); x.restore(); }
  }
  // letter by letter, so each one's outline sits on the one before it: outline (+ drips), fill (+ drips), shine
  for (const L of all) {
    x.strokeStyle = INK; x.fillStyle = INK; x.lineWidth = lw + 2 * ol; x.stroke(L.path);
    for (const d of L.drips) drip(x, d, ol);
    const g = paintOf(L);
    x.strokeStyle = g; x.fillStyle = g;
    for (const d of L.drips) drip(x, d, 0);
    x.lineWidth = lw; x.stroke(L.path);
    // shine: a short white streak from the most top-left point along its stroke
    let bi = null, best = 1e9;
    L.pts.forEach((pl, a) => pl.forEach((q, b) => { if (q[0] + q[1] < best) { best = q[0] + q[1]; bi = [a, b]; } }));
    const pl = L.pts[bi[0]], p0 = pl[bi[1]], p1 = pl[bi[1] + 1] || pl[bi[1] - 1];
    if (p1) {
      const dx = p1[0] - p0[0], dy = p1[1] - p0[1], len = Math.hypot(dx, dy) || 1, k = Math.min(len, H * 0.32) / len;
      const ox = -lw * 0.14 + dx * 0.08, oy = -lw * 0.18 + dy * 0.08;
      x.strokeStyle = 'rgba(255,255,255,0.8)'; x.lineWidth = Math.max(1, lw * 0.17);
      x.beginPath(); x.moveTo(p0[0] + ox, p0[1] + oy); x.lineTo(p0[0] + ox + dx * k, p0[1] + oy + dy * k); x.stroke();
    }
  }
  // overspray: paint mist just outside the outlines
  for (const L of all) {
    for (let i = 0; i < 24; i++) {
      const pl = L.pts[(rnd() * L.pts.length) | 0], j = (rnd() * (pl.length - 1)) | 0, q0 = pl[j], q1 = pl[Math.min(j + 1, pl.length - 1)], t = rnd();
      const a = rnd() * TAU, d = lw / 2 + ol + Math.pow(rnd(), 1.5) * H * 0.4;
      const col = L.paint.rainbow ? L.paint.rainbow[(rnd() * L.paint.rainbow.length) | 0] : rnd() < 0.5 ? L.paint.a : L.paint.b;
      dot(x, q0[0] + (q1[0] - q0[0]) * t + Math.cos(a) * d, q0[1] + (q1[1] - q0[1]) * t + Math.sin(a) * d, 0.35 + rnd() * 0.8, col, 0.25 + rnd() * 0.6);
    }
  }
  for (let i = 0; i < (o.sparkle || 0) && all.length; i++) {
    const L = all[(rnd() * all.length) | 0];
    let q = null;
    for (const pl of L.pts) for (const p of pl) if (!q || p[1] < q[1]) q = p;
    const sz = H * (0.15 + rnd() * 0.08), m = PAD + sz + 1; // the whole star stays off the border
    sparkle(x, Math.max(m, Math.min(PX - m, q[0] + lw * 0.45)), Math.max(m, Math.min(PX - m, q[1] - lw * 0.2)), sz);
  }
  x.restore();
}

// ---------------------------------------------------------------- shapes
// one shape, or several merged (every outline first, then every fill), with a 3d drop and drips. fill can be one per path
function shape(x, paths, fill, o = {}) {
  const ol = o.ol ?? 3, ex = o.ex ?? 4, drips = o.drips || [];
  x.lineJoin = x.lineCap = 'round';
  if (o.d) {
    x.fillStyle = o.d; x.strokeStyle = o.d; x.lineWidth = ol * 2;
    for (let k = 1; k <= ex; k++) { x.save(); x.translate(k, k); for (const p of paths) { x.fill(p); x.stroke(p); } x.restore(); }
  }
  x.strokeStyle = INK; x.fillStyle = INK; x.lineWidth = ol * 2;
  for (const p of paths) x.stroke(p);
  for (const d of drips) drip(x, d, ol);
  const f0 = Array.isArray(fill) ? fill[0] : fill;
  x.fillStyle = f0; x.strokeStyle = f0;
  for (const d of drips) drip(x, d, 0);
  paths.forEach((p, i) => { x.fillStyle = Array.isArray(fill) ? fill[i] : fill; x.fill(p); });
}
// overspray around a roundish thing: denser near its edge
function mist(x, rnd, cx, cy, r0, r1, cols, n) {
  for (let i = 0; i < n; i++) {
    const a = rnd() * TAU, d = r0 + Math.pow(rnd(), 1.6) * (r1 - r0);
    dot(x, cx + Math.cos(a) * d, cy + Math.sin(a) * d * 0.92, 0.35 + rnd() * 0.85, cols[(rnd() * cols.length) | 0], 0.2 + rnd() * 0.6);
  }
}
function shine(x, cx, cy, r, a0, a1, w = 4) {
  x.strokeStyle = 'rgba(255,255,255,0.85)'; x.lineWidth = w; x.lineCap = 'round';
  x.beginPath(); x.arc(cx, cy, r, a0, a1); x.stroke();
}
function heartPath(cx, cy, s) {
  const p = new Path2D();
  p.moveTo(cx, cy + s * 0.95);
  p.bezierCurveTo(cx - s * 0.2, cy + s * 0.75, cx - s * 1.25, cy + s * 0.2, cx - s * 1.1, cy - s * 0.4);
  p.bezierCurveTo(cx - s * 0.95, cy - s * 1.05, cx - s * 0.1, cy - s * 1.05, cx, cy - s * 0.45);
  p.bezierCurveTo(cx + s * 0.1, cy - s * 1.05, cx + s * 0.95, cy - s * 1.05, cx + s * 1.1, cy - s * 0.4);
  p.bezierCurveTo(cx + s * 1.25, cy + s * 0.2, cx + s * 0.2, cy + s * 0.75, cx, cy + s * 0.95);
  p.closePath();
  return p;
}
// a flame tongue: round bottom at (cx, cy), licking up to a tip at (tx, ty)
function tongue(cx, cy, r, tx, ty) {
  const p = new Path2D(), h = cy - ty;
  p.moveTo(cx - r, cy);
  p.arc(cx, cy, r, Math.PI, 0, true);
  p.bezierCurveTo(cx + r, cy - h * 0.35, tx + r * 0.3, ty + h * 0.45, tx, ty);
  p.bezierCurveTo(tx - r * 0.1, ty + h * 0.4, cx - r * 1.05, cy - h * 0.3, cx - r, cy);
  p.closePath();
  return p;
}
const circle = (cx, cy, r) => { const p = new Path2D(); p.arc(cx, cy, r, 0, TAU); return p; };

function heart(x, rnd) {
  shape(x, [heartPath(64, 58, 34)], vg(x, 24, 92, '#ff7aa8', '#d80f4a'), { d: '#4a0020', drips: [dr(64, 82, 22, 5), dr(45, 70, 14, 4), dr(84, 68, 9, 3.5)] });
  shine(x, 47, 44, 11, Math.PI * 1.05, Math.PI * 1.55);
  dot(x, 38, 54, 2, '#ffffff', 0.85);
  mist(x, rnd, 64, 58, 40, 54, ['#ff4f8a', '#ff9ac0'], 120);
  sparkle(x, 100, 26, 7);
}
function smiley(x, rnd) {
  shape(x, [circle(64, 56, 38)], vg(x, 18, 94, '#fff36a', '#ffb31a'), { d: '#5e2a00', drips: [dr(50, 86, 16, 5), dr(68, 90, 20, 6), dr(85, 80, 10, 4)] });
  x.fillStyle = INK;
  for (const ex of [51, 77]) { x.beginPath(); x.ellipse(ex, 45, 4.5, 8.5, 0, 0, TAU); x.fill(); }
  x.strokeStyle = INK; x.lineWidth = 5; x.lineCap = 'round';
  x.beginPath(); x.arc(64, 54, 24, 0.16 * Math.PI, 0.84 * Math.PI); x.stroke();
  x.lineWidth = 3; x.beginPath(); x.moveTo(37, 60); x.lineTo(43, 63); x.moveTo(91, 60); x.lineTo(85, 63); x.stroke(); // dimples
  shine(x, 64, 56, 31, Math.PI * 1.1, Math.PI * 1.4);
  mist(x, rnd, 64, 56, 41, 54, ['#ffe14d', '#ffb31a'], 120);
}
function skull(x, rnd) {
  const jaw = new Path2D(); jaw.roundRect(45, 64, 38, 30, 8);
  shape(x, [circle(64, 50, 33), jaw], vg(x, 16, 94, '#ffffff', '#c3ccdb'), { d: '#7a1fd0', drips: [dr(52, 90, 14, 4.5), dr(74, 90, 21, 5)] });
  x.fillStyle = INK;
  for (const k of [-1, 1]) { x.beginPath(); x.ellipse(64 + k * 13, 54, 9, 10.5, k * 0.3, 0, TAU); x.fill(); }
  for (const k of [-1, 1]) dot(x, 64 + k * 12, 55, 2.4, '#7dff4f'); // creepy little eyes
  x.beginPath(); x.moveTo(64, 63); x.lineTo(59, 72); x.lineTo(69, 72); x.closePath(); x.fill(); // nose
  x.strokeStyle = INK; x.lineWidth = 2.2; x.lineCap = 'round';
  x.beginPath(); x.moveTo(50, 80); x.lineTo(78, 80);
  for (const tx of [55, 61, 67, 73]) { x.moveTo(tx, 76); x.lineTo(tx, 89); }
  x.stroke(); // teeth
  x.lineWidth = 1.8; x.beginPath(); x.moveTo(81, 23); x.lineTo(76, 31); x.lineTo(82, 35); x.lineTo(78, 42); x.stroke(); // crack
  shine(x, 64, 50, 27, Math.PI * 1.12, Math.PI * 1.42, 3.5);
  mist(x, rnd, 64, 58, 40, 54, ['#b07dff', '#ffffff'], 110);
}
function flame(x, rnd) {
  const outer = [tongue(64, 80, 27, 58, 10), tongue(43, 88, 17, 24, 40), tongue(86, 86, 18, 106, 30)];
  shape(x, outer, vg(x, 10, 110, '#ffb31a', '#ff2a1a'), { d: '#3b0000', drips: [dr(54, 100, 11, 5), dr(74, 100, 13, 5.5)] });
  x.fillStyle = vg(x, 34, 108, '#ffe14d', '#ff8a1a');
  for (const p of [tongue(64, 88, 19, 62, 34), tongue(48, 94, 10, 38, 58), tongue(80, 93, 11, 92, 54)]) x.fill(p);
  x.fillStyle = vg(x, 58, 104, '#ffffff', '#ffe98a'); x.fill(tongue(64, 95, 10, 66, 60));
  mist(x, rnd, 64, 66, 42, 56, ['#ff7a1a', '#ffb31a', '#ff3b1a'], 110);
  for (let i = 0; i < 7; i++) dot(x, 30 + rnd() * 68, 10 + rnd() * 24, 1 + rnd(), '#ffb31a', 0.9); // embers
}
function duck(x, rnd) {
  const body = new Path2D(); body.ellipse(70, 80, 38, 22, 0, 0, TAU);
  const tail = new Path2D(); tail.moveTo(94, 70); tail.quadraticCurveTo(108, 58, 114, 50); tail.quadraticCurveTo(113, 72, 100, 86); tail.closePath();
  const beak = new Path2D(); beak.moveTo(30, 45); beak.quadraticCurveTo(14, 43, 10, 53); beak.quadraticCurveTo(18, 64, 32, 58); beak.closePath();
  const yel = vg(x, 26, 102, '#fff47a', '#ffc21a');
  shape(x, [tail, body, circle(46, 48, 21), beak], [yel, yel, yel, '#ff8a1a'], { d: '#1f4fbf', drips: [dr(58, 96, 13, 5), dr(84, 95, 17, 5.5)] });
  const wing = new Path2D(); wing.moveTo(60, 79); wing.quadraticCurveTo(76, 58, 97, 72); wing.quadraticCurveTo(84, 93, 60, 79);
  x.fillStyle = '#ffb81a'; x.fill(wing); x.strokeStyle = INK; x.lineWidth = 2; x.stroke(wing);
  x.lineWidth = 1.5; x.beginPath(); x.moveTo(12, 54); x.quadraticCurveTo(22, 53, 31, 51); x.stroke(); // beak line
  x.fillStyle = INK; x.beginPath(); x.arc(44, 42, 4.5, 0, TAU); x.fill();
  dot(x, 42.5, 40.5, 1.6, '#ffffff');
  dot(x, 53, 54, 4, '#ff7aa8', 0.6); // blush
  shine(x, 46, 48, 15, Math.PI * 1.1, Math.PI * 1.45, 3);
  mist(x, rnd, 64, 70, 42, 56, ['#ffe14d', '#4fd8ff'], 100);
  sparkle(x, 100, 30, 6);
}
function noob(x, rnd) {
  const cloud = [[34, 66, 18], [52, 50, 21], [76, 46, 22], [96, 60, 18], [66, 72, 24], [40, 80, 16], [90, 80, 16]].map(([cx, cy, r]) => circle(cx, cy, r));
  shape(x, cloud, vg(x, 24, 98, '#ffffff', '#ffc8ea'), { d: '#ff4fd8', ex: 3 });
  letters(x, rnd, [[['NOOB', PAINT.baby]]], { box: [10, 34, 118, 106], sparkle: 1 });
}
function what(x, rnd) {
  letters(x, rnd, [[['?', PAINT.cyan]]], { box: [8, 10, 46, 54], drips: false, rot: -0.35 });
  letters(x, rnd, [[['?', PAINT.pink]]], { box: [88, 54, 120, 96], drips: false, rot: 0.3 });
  letters(x, rnd, [[['?', PAINT.grape]]], { box: [24, 12, 100, 120], sparkle: 1 });
}
function oof(x, rnd) {
  const burst = new Path2D(), n = 14;
  for (let i = 0; i <= n * 2; i++) {
    const a = (i / (n * 2)) * TAU - Math.PI / 2, r = i % 2 ? 33 + rnd() * 5 : 44 + rnd() * 6;
    const X = 64 + Math.cos(a) * r * 1.06, Y = 62 + Math.sin(a) * r * 0.92;
    if (i) burst.lineTo(X, Y); else burst.moveTo(X, Y);
  }
  burst.closePath();
  shape(x, [burst], vg(x, 12, 112, '#fff47a', '#ffb31a'), { d: '#7a2a00' });
  letters(x, rnd, [[['OOF', PAINT.red]]], { box: [16, 34, 112, 104], sparkle: 1 });
}
function rip(x, rnd) {
  const stone = new Path2D(); stone.moveTo(28, 104); stone.lineTo(28, 50); stone.arc(64, 50, 36, Math.PI, 0); stone.lineTo(100, 104); stone.closePath();
  shape(x, [stone], vg(x, 14, 104, '#c3cad6', '#6b7280'), { d: '#262633' });
  x.strokeStyle = INK; x.lineWidth = 1.5; x.beginPath(); x.moveTo(88, 30); x.lineTo(82, 39); x.lineTo(88, 45); x.lineTo(83, 54); x.stroke(); // crack
  letters(x, rnd, [[['RIP', PAINT.bone]]], { box: [30, 30, 98, 88], drips: false });
  const grass = new Path2D(); grass.moveTo(16, 116);
  for (let i = 0; i <= 12; i++) { const gx = 16 + i * 8; grass.lineTo(gx + 2, 102 - rnd() * 8); grass.lineTo(gx + 4, 110); }
  grass.lineTo(112, 116); grass.closePath();
  shape(x, [grass], vg(x, 94, 116, '#7dff4f', '#2a9a3a'), { ol: 2, ex: 0 });
  mist(x, rnd, 64, 62, 40, 54, ['#c3cad6', '#7dff4f'], 70);
}

// [draw, mist colours when it's sprayed]
const ART = {
  gg: [(x, r) => letters(x, r, [[['GG', PAINT.lime]]], { sparkle: 2 }), [0x7dff4f, 0x22c23c]],
  ez: [(x, r) => letters(x, r, [[['EZ', PAINT.pink]]], { sparkle: 1 }), [0xff4fd8, 0xffb0ee]],
  wp: [(x, r) => letters(x, r, [[['WP', PAINT.cyan]]], { sparkle: 1 }), [0x4fd8ff, 0x1f80ff]],
  gl: [(x, r) => letters(x, r, [[['GL', PAINT.sun]]], { sparkle: 2 }), [0xffe14d, 0xff7a1a]],
  l: [(x, r) => letters(x, r, [[['L', PAINT.red]]], { sparkle: 1 }), [0xff3b3b, 0xd10f1f]],
  noob: [noob, [0x62b4ff, 0xffc8ea]],
  what: [what, [0x7d2cff, 0x4fd8ff, 0xff4fd8]],
  oof: [oof, [0xffe14d, 0xff3b1a]],
  rip: [rip, [0xb9c3d3, 0xffffff]],
  heart: [heart, [0xff4f8a, 0xe0104a]],
  smiley: [smiley, [0xffe14d, 0xffb31a]],
  skull: [skull, [0xffffff, 0x9a4fff]],
  flame: [flame, [0xff7a1a, 0xffe14d, 0xff3b1a]],
  duck: [duck, [0xffe14d, 0xff8a1a]],
  logo: [(x, r) => letters(x, r, [[['JANK', PAINT.rainbow]], [['FIRE', PAINT.rainbow]]], { box: [16, 14, 112, 116], sparkle: 3, glow: 'rgba(255,79,216,0.35)' }), [0xff3b3b, 0xffe14d, 0x5dff4f, 0x4fd8ff, 0xff4fd8]],
};

// each spray is drawn once: the canvas feeds the menu picture and the decal texture
const cache = new Map();
function art(id) {
  if (!ART[id]) id = SPRAY.def;
  let a = cache.get(id);
  if (a) return a;
  const cv = document.createElement('canvas');
  cv.width = cv.height = PX;
  ART[id][0](cv.getContext('2d'), rng(id));
  a = { cv, url: '', tex: null };
  cache.set(id, a);
  return a;
}
export function sprayIcon(id) { const a = art(id); return a.url || (a.url = a.cv.toDataURL()); }
function sprayTex(id) {
  const a = art(id);
  if (!a.tex) {
    const t = a.tex = new THREE.CanvasTexture(a.cv);
    t.colorSpace = THREE.SRGBColorSpace;
    t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestMipmapLinearFilter; t.anisotropy = 4; // crunchy up close, like the walls
  }
  return a.tex;
}

// ---------------------------------------------------------------- decals
// the spray's own frame: U = its right, V = its up, as you look at it
function frame(n, r) {
  if (n[1] > 0) return [[Math.cos(r), 0, -Math.sin(r)], [-Math.sin(r), 0, -Math.cos(r)]]; // floor: upright from where you stood
  if (n[1] < 0) return [[Math.cos(r), 0, -Math.sin(r)], [Math.sin(r), 0, Math.cos(r)]]; // ceiling: upright when you look up
  return [[n[2], 0, -n[0]], [0, 1, 0]]; // wall: upright
}
// rect r minus rect q ([x0, y0, x1, y1]): up to four pieces
function cut(r, q) {
  if (q[0] >= r[2] || q[2] <= r[0] || q[1] >= r[3] || q[3] <= r[1]) return [r];
  const out = [], x0 = Math.max(r[0], q[0]), x1 = Math.min(r[2], q[2]);
  if (q[0] > r[0]) out.push([r[0], r[1], q[0], r[3]]);
  if (q[2] < r[2]) out.push([q[2], r[1], r[2], r[3]]);
  if (q[1] > r[1]) out.push([x0, r[1], x1, q[1]]);
  if (q[3] < r[3]) out.push([x0, q[3], x1, r[3]]);
  return out.filter((o) => o[2] - o[0] > 1e-4 && o[3] - o[1] > 1e-4);
}
const tmpQ = [];
// every map face in the spray's plane (facing the same way), cut to the spray's square. so it stops at edges,
// doorways and windows but carries on across wall pieces. uvs come from the spray's frame: whatever falls
// outside the square (corners of a turned floor spray) samples the clear border
function decalGeometry(p, n, r) {
  const k = n[0] ? 0 : n[1] ? 1 : 2, a = k === 0 ? 1 : 0, b = k === 2 ? 1 : 2, S = SPRAY.size, h = S / 2;
  const [U, V] = frame(n, r);
  const ea = (Math.abs(U[a]) + Math.abs(V[a])) * h, eb = (Math.abs(U[b]) + Math.abs(V[b])) * h;
  const lo = [p[0], p[1], p[2]], hi = [p[0], p[1], p[2]];
  lo[a] -= ea; hi[a] += ea; lo[b] -= eb; hi[b] += eb;
  const rects = [];
  for (const bx of query(BOXES, lo[0] - 0.01, lo[2] - 0.01, hi[0] + 0.01, hi[2] + 0.01, tmpQ)) {
    if (Math.abs((n[k] > 0 ? bx.max[k] : bx.min[k]) - p[k]) > 1e-3) continue;
    const r0 = [Math.max(lo[a], bx.min[a]), Math.max(lo[b], bx.min[b]), Math.min(hi[a], bx.max[a]), Math.min(hi[b], bx.max[b])];
    if (r0[2] - r0[0] < 1e-3 || r0[3] - r0[1] < 1e-3) continue;
    let parts = [r0];
    for (const q of rects) parts = parts.flatMap((pp) => cut(pp, q)); // two faces in one plane: paint it once
    rects.push(...parts);
    if (rects.length > 48) break;
  }
  if (!rects.length) return null;
  const pos = [], uv = [], nor = [], off = 0.012;
  // keep the triangles facing out of the wall (x cross z points down, the other pairs point along +k)
  const fwd = (k === 1 ? -1 : 1) * n[k] > 0;
  for (const [x0, y0, x1, y1] of rects) {
    const cs = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]];
    for (const i of fwd ? [0, 1, 2, 0, 2, 3] : [0, 2, 1, 0, 3, 2]) {
      const d = [0, 0, 0];
      d[k] = n[k] * off; d[a] = cs[i][0] - p[a]; d[b] = cs[i][1] - p[b];
      pos.push(d[0], d[1], d[2]); // relative to the centre: the mesh sits there
      uv.push((d[0] * U[0] + d[1] * U[1] + d[2] * U[2]) / S + 0.5, (d[0] * V[0] + d[1] * V[1] + d[2] * V[2]) / S + 0.5);
      nor.push(n[0], n[1], n[2]);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
  return g;
}

const live = new Map(); // owner id -> { mesh, t }
const ALPHA = 0.88, FADE = 0.35; // a little see-through so it reads as paint, and it fades in as it's sprayed

// what Z would paint: the face you look at, within reach (null = nothing there)
export function sprayAim(eye, dir) {
  const h = raycast(eye, dir, SPRAY.reach, BOXES);
  return h && h.axis >= 0 ? { p: h.point, n: h.normal } : null;
}
// the pssht: paint mist off the wall + the hiss
export function sprayFx(p, n, id) {
  const tint = (ART[id] || ART[SPRAY.def])[1];
  fx.spray([p[0] + n[0] * 0.25, p[1] + n[1] * 0.25, p[2] + n[2] * 0.25], 18, tint, 1.6, 0.7, 0.08, -0.4, 2.5);
  sfx.spray(p);
}
// the server says someone painted one (quiet = it was already there when you joined)
export function addSpray(m, quiet) {
  if (!COSMETICS.spray[m.s] || !Array.isArray(m.p) || !Array.isArray(m.n)) return;
  removeSpray(m.id);
  const g = decalGeometry(m.p, m.n, m.r || 0);
  if (!g) return;
  const mat = new THREE.MeshLambertMaterial({
    map: sprayTex(m.s), transparent: true, opacity: quiet ? ALPHA : 0, depthWrite: false,
    polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2,
  });
  const mesh = new THREE.Mesh(g, mat);
  mesh.position.set(m.p[0], m.p[1], m.p[2]);
  mesh.renderOrder = 1; // before water, so one on a canal floor still looks underwater
  G.scene.add(mesh);
  live.set(m.id, { mesh, t: quiet ? 1 : 0 });
  while (live.size > SPRAY.max) removeSpray(live.keys().next().value);
  if (!quiet && m.id !== G.myId) sprayFx(m.p, m.n, m.s); // yours already hissed when you pressed Z
}
function removeSpray(id) {
  const d = live.get(id);
  if (!d) return;
  G.scene.remove(d.mesh);
  d.mesh.geometry.dispose(); d.mesh.material.dispose();
  live.delete(id);
}
export function clearSprays() { for (const id of [...live.keys()]) removeSpray(id); }
export function updateSprays(dt) {
  for (const d of live.values()) if (d.t < 1) { d.t = Math.min(1, d.t + dt / FADE); d.mesh.material.opacity = ALPHA * d.t; }
}
