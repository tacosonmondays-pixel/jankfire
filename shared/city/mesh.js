// Chunk -> render buffers, with no three.js (it runs in the chunk worker). Boxes, turned deco boxes and shapes (tubes,
// blobs, lathes) become one indexed buffer set per kind (solid / flesh / glow / glass / acid): that's 1-5 draw calls a
// chunk. lod 0 = everything; lod 1 = the mid ring (big pieces only, no undersides, half-res shapes).
// Vertex layout: pos f32x3, nrm i8x3 (normalised), uv f32x2 (world metres / tile size), col u8x4: rgb paint with a
// baked contact shade, a = atlas family (low 5 bits) + flesh pulse weight (high 3 bits).
// impostorCells(): 4 x 4 cells of 16 m per chunk (top height + colour) for the far ring's one big mesh.
import { MATS, FAMS, CHUNK } from './plan.js';
import { FLAGS } from './chunk.js';

const FAM = Object.fromEntries(FAMS.map((f, i) => [f, i]));
export const TILE_M = { dirt: 3, asphalt: 4, concrete: 3, plaster: 2.5, brick: 2, metal: 2, wood: 1.5, tile: 1, corrug: 1.5, fabric: 2, tiedye: 3, bone: 0.8, paint: 1, rib: 2, window: 2, flesh: 3, glass: 2, glow: 2 };
export const KINDS = ['solid', 'flesh', 'glow', 'glass', 'acid'];

function sink() {
  let n = 0, ni = 0, pos = new Float32Array(3072), nrm = new Int8Array(3072), uv = new Float32Array(2048), col = new Uint8Array(4096), idx = new Uint32Array(4096);
  const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
  const grow = (a, need) => { if (need <= a.length) return a; const b = new a.constructor(Math.max(need, a.length * 2)); b.set(a); return b; };
  return {
    get n() { return n; },
    v(x, y, z, nx, ny, nz, u, w, r, g, b, a) {
      if (n * 3 + 3 > pos.length) { pos = grow(pos, n * 3 + 3); nrm = grow(nrm, n * 3 + 3); uv = grow(uv, n * 2 + 2); col = grow(col, n * 4 + 4); }
      pos[n * 3] = x; pos[n * 3 + 1] = y; pos[n * 3 + 2] = z;
      nrm[n * 3] = Math.round(nx * 127); nrm[n * 3 + 1] = Math.round(ny * 127); nrm[n * 3 + 2] = Math.round(nz * 127);
      uv[n * 2] = u; uv[n * 2 + 1] = w;
      col[n * 4] = r; col[n * 4 + 1] = g; col[n * 4 + 2] = b; col[n * 4 + 3] = a;
      if (x < min[0]) min[0] = x; if (y < min[1]) min[1] = y; if (z < min[2]) min[2] = z;
      if (x > max[0]) max[0] = x; if (y > max[1]) max[1] = y; if (z > max[2]) max[2] = z;
      return n++;
    },
    t(a, b, c) { if (ni + 3 > idx.length) idx = grow(idx, ni + 3); idx[ni++] = a; idx[ni++] = b; idx[ni++] = c; },
    done() {
      if (!n) return null;
      const big = n > 65535;
      return { pos: pos.slice(0, n * 3), nrm: nrm.slice(0, n * 3), uv: uv.slice(0, n * 2), col: col.slice(0, n * 4), idx: big ? idx.slice(0, ni) : Uint16Array.from(idx.subarray(0, ni)), min, max, verts: n, tris: ni / 3 };
    },
  };
}

const famOf = (m) => FAM[MATS[m] ? MATS[m][1] : 'concrete'] ?? 0;
const kindOf = (m) => (MATS[m] && MATS[m][3]) || 'solid';
const rgbOf = (m, tint) => { const c = tint || (MATS[m] ? MATS[m][2] : 0xffffff); return [(c >> 16) & 255, (c >> 8) & 255, c & 255]; };
const tileOf = (m) => TILE_M[MATS[m] ? MATS[m][1] : 'concrete'] || 2;

// the 6 faces of a box: normal axis, sign, and the two axes the face spans (u, v)
const FACES = [[0, 1, 2, 1], [0, -1, 2, 1], [1, 1, 0, 2], [1, -1, 0, 2], [2, 1, 0, 1], [2, -1, 0, 1]];

// one box into a sink. yaw (deco) turns it round its centre. lod 1 drops the underside. fit = the texture once per face
function boxInto(S, x0, y0, z0, x1, y1, z1, m, tint, flag, lod, yaw = 0) {
  const lo = [x0, y0, z0], hi = [x1, y1, z1], c = [(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2];
  const [r, g, b] = rgbOf(m, tint), fam = famOf(m), tile = tileOf(m), fit = flag & FLAGS.FIT;
  const cs = Math.cos(yaw), sn = Math.sin(yaw), turned = yaw !== 0;
  for (const [ax, sg, ua, va] of FACES) {
    if (ax === 1 && sg < 0 && (lod || y0 <= 0.001 || (y1 - y0 > 1.5 && Math.min(x1 - x0, z1 - z0) < 0.6))) continue; // undersides on the ground, of walls, and far away: never seen
    const p = [0, 0, 0], base = S.n;
    const nx = ax === 0 ? sg : 0, ny = ax === 1 ? sg : 0, nz = ax === 2 ? sg : 0;
    const wnx = turned ? nx * cs + nz * sn : nx, wnz = turned ? -nx * sn + nz * cs : nz;
    for (let k = 0; k < 4; k++) {
      const uu = k === 1 || k === 2, vv = k >= 2;
      p[ax] = sg > 0 ? hi[ax] : lo[ax]; p[ua] = uu ? hi[ua] : lo[ua]; p[va] = vv ? hi[va] : lo[va];
      let wx = p[0], wz = p[2];
      if (turned) { const dx = p[0] - c[0], dz = p[2] - c[2]; wx = c[0] + dx * cs + dz * sn; wz = c[2] - dx * sn + dz * cs; }
      // contact shade: walls get darker toward their foot, undersides darkest (cheap fake AO)
      const sh = ax === 1 ? (sg > 0 ? 1 : 0.55) : 0.72 + 0.28 * Math.min(1, (p[1] - y0) / 2.5);
      const u = fit ? (uu ? 1 : 0) : (turned ? (ua === 1 ? p[1] : (ua === 0 ? p[0] - c[0] : p[2] - c[2])) : p[ua]) / tile;
      const w = fit ? (vv ? 1 : 0) : (turned ? (va === 1 ? p[1] : (va === 0 ? p[0] - c[0] : p[2] - c[2])) : p[va]) / tile;
      S.v(wx, p[1], wz, wnx, ny, wnz, u, w, r * sh, g * sh, b * sh, fam);
    }
    // winding: counter-clockwise seen from outside
    const flip = ax === 2 ? sg < 0 : sg > 0; // u x v points down the face's axis on x and y faces
    if (flip) { S.t(base, base + 2, base + 1); S.t(base, base + 3, base + 2); } else { S.t(base, base + 1, base + 2); S.t(base, base + 2, base + 3); }
  }
}

// catmull-rom point on a polyline
function cr(pts, t) {
  const n = pts.length - 1, s = Math.min(n - 1e-6, Math.max(0, t * n)), i = Math.floor(s), f = s - i;
  const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(n, i + 2)];
  const q = (k) => 0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * f + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * f * f + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * f * f * f);
  return [q(0), q(1), q(2)];
}
const norm = (v) => { const l = Math.hypot(v[0], v[1], v[2]) || 1; return [v[0] / l, v[1] / l, v[2] / l]; };
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];

// shapes: { kind: 'tube', pts, r (number or per-point), seg, mat, tint, pulse, open } | { kind: 'blob', c, r: [x, y, z], seg }
// | { kind: 'lathe', c, prof: [[r, y], ...], seg } . pulse 0-7 = how much the flesh shader breathes it (default 3 on flesh)
function shapeInto(S, s, lod) {
  const m = typeof s.mat === 'number' ? s.mat : MATS.findIndex((q) => q[0] === s.mat);
  const [r, g, b] = rgbOf(m < 0 ? 0 : m, s.tint), fam = famOf(m), tile = tileOf(m);
  const pulse = Math.max(0, Math.min(7, s.pulse ?? (kindOf(m) === 'flesh' ? 3 : 0)));
  const a = fam | (pulse << 5), seg = Math.max(3, Math.round((s.seg || 10) / (lod ? 2 : 1)));
  if (s.kind === 'tube') {
    const pts = s.pts; let len = 0;
    for (let i = 1; i < pts.length; i++) len += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1], pts[i][2] - pts[i - 1][2]);
    const steps = Math.max(2, Math.ceil(len / (s.step || 1.2) / (lod ? 2 : 1)));
    let up = [0, 1, 0], base0 = S.n;
    for (let i = 0; i <= steps; i++) {
      const t = i / steps, p = cr(pts, t), q = cr(pts, Math.min(1, t + 1e-3)), p0 = cr(pts, Math.max(0, t - 1e-3));
      const tan = norm([q[0] - p0[0], q[1] - p0[1], q[2] - p0[2]]);
      if (Math.abs(tan[1]) > 0.95) up = [1, 0, 0];
      const nx = norm(cross(up, tan)), ny = cross(tan, nx);
      const rad = Array.isArray(s.r) ? s.r[0] + (s.r[1] - s.r[0]) * t : s.r;
      const ribs = s.ribs ? 1 + s.ribs * Math.cos(t * len * 2.2) : 1; // intestine ridges
      for (let k = 0; k <= seg; k++) {
        const ang = (k / seg) * Math.PI * 2, ca = Math.cos(ang), sa = Math.sin(ang);
        const n = [nx[0] * ca + ny[0] * sa, nx[1] * ca + ny[1] * sa, nx[2] * ca + ny[2] * sa];
        const sign = s.inside ? -1 : 1;
        S.v(p[0] + n[0] * rad * ribs, p[1] + n[1] * rad * ribs, p[2] + n[2] * rad * ribs, n[0] * sign, n[1] * sign, n[2] * sign, (k / seg) * rad * 6.283 / tile, (t * len) / tile, r, g, b, a);
      }
    }
    for (let i = 0; i < steps; i++) for (let k = 0; k < seg; k++) {
      const a0 = base0 + i * (seg + 1) + k, a1 = a0 + 1, b0 = a0 + seg + 1, b1 = b0 + 1;
      if (s.inside) { S.t(a0, b0, a1); S.t(a1, b0, b1); } else { S.t(a0, a1, b0); S.t(a1, b1, b0); }
    }
  } else if (s.kind === 'blob' || s.kind === 'lathe') {
    const prof = s.kind === 'lathe' ? s.prof : null, rows = prof ? prof.length - 1 : Math.max(3, Math.round(seg * 0.6));
    const R = s.kind === 'blob' ? (Array.isArray(s.r) ? s.r : [s.r, s.r, s.r]) : [1, 1, 1], c = s.c, base0 = S.n;
    for (let i = 0; i <= rows; i++) {
      let rr, y, ny0;
      if (prof) { rr = prof[i][0]; y = prof[i][1]; const pa = prof[Math.max(0, i - 1)], pb = prof[Math.min(rows, i + 1)]; const dy = pb[1] - pa[1], dr = pb[0] - pa[0]; const l = Math.hypot(dy, dr) || 1; ny0 = [dy / l, -dr / l]; } else { const ph = (i / rows) * Math.PI; rr = Math.sin(ph); y = -Math.cos(ph); ny0 = [rr, y]; }
      for (let k = 0; k <= seg; k++) {
        const ang = (k / seg) * Math.PI * 2, ca = Math.cos(ang), sa = Math.sin(ang);
        const n = norm(prof ? [ny0[0] * ca, ny0[1], ny0[0] * sa] : [rr * ca / R[0], y / R[1], rr * sa / R[2]]);
        S.v(c[0] + rr * ca * R[0], c[1] + y * R[1], c[2] + rr * sa * R[2], n[0], n[1], n[2], (k / seg) * 6.283 * Math.max(R[0], rr) / tile, (y * R[1]) / tile, r, g, b, a);
      }
    }
    for (let i = 0; i < rows; i++) for (let k = 0; k < seg; k++) {
      const a0 = base0 + i * (seg + 1) + k, a1 = a0 + 1, b0 = a0 + seg + 1, b1 = b0 + 1;
      S.t(a0, b0, a1); S.t(a1, b0, b1);
    }
  }
}

// a packed chunk (chunk.js packChunk) -> { solid, flesh, glow, glass, acid } buffer sets (missing kinds = null)
export function meshChunk(p, lod = 0) {
  const sinks = {};
  const get = (m) => { const k = kindOf(m); return sinks[k] || (sinks[k] = sink()); };
  for (let i = 0; i < p.mat.length; i++) {
    const f = p.flag[i];
    if (f & FLAGS.HIDE || (f & FLAGS.L1 && !lod) || (f & FLAGS.L0 && lod)) continue;
    const j = i * 6, x0 = p.box[j], y0 = p.box[j + 1], z0 = p.box[j + 2], x1 = p.box[j + 3], y1 = p.box[j + 4], z1 = p.box[j + 5];
    if (lod && !(f & FLAGS.L1)) { const big = Math.max(x1 - x0, y1 - y0, z1 - z0); if (!(f & FLAGS.LOD) && (big < 2.5 || (f & FLAGS.NC && big < 4))) continue; }
    boxInto(get(p.mat[i]), x0, y0, z0, x1, y1, z1, p.mat[i], p.tint[i], f, lod);
  }
  for (let i = 0; i < p.dmat.length; i++) {
    const j = i * 7, sx = p.deco[j + 3], sy = p.deco[j + 4], sz = p.deco[j + 5];
    if (lod && Math.max(sx, sy, sz) < 3) continue;
    const x = p.deco[j], y = p.deco[j + 1], z = p.deco[j + 2];
    boxInto(get(p.dmat[i]), x - sx / 2, y - sy / 2, z - sz / 2, x + sx / 2, y + sy / 2, z + sz / 2, p.dmat[i], p.dtint[i], 0, lod, p.deco[j + 6]);
  }
  for (const s of p.shapes) {
    if (lod && s.lod === false) continue;
    const m = typeof s.mat === 'number' ? s.mat : MATS.findIndex((q) => q[0] === s.mat);
    shapeInto(get(m < 0 ? 0 : m), s, lod);
  }
  const out = {};
  for (const k of KINDS) out[k] = sinks[k] ? sinks[k].done() : null;
  return out;
}

export function meshTransfer(m) {
  const l = [];
  for (const k of KINDS) if (m[k]) l.push(m[k].pos.buffer, m[k].nrm.buffer, m[k].uv.buffer, m[k].col.buffer, m[k].idx.buffer);
  return l;
}

// the far ring: per 16 m cell the tallest solid top and its colour (boxes under 3 m across are ignored)
export function impostorCells(p) {
  const N = 4, S = CHUNK / N, top = new Float32Array(N * N).fill(-1e9), col = new Uint32Array(N * N), base = new Float32Array(N * N).fill(1e9);
  const x0c = p.cx * CHUNK, z0c = p.cz * CHUNK;
  for (let i = 0; i < p.mat.length; i++) {
    if (p.flag[i] & FLAGS.HIDE) continue;
    const j = i * 6, bx0 = p.box[j], by0 = p.box[j + 1], bz0 = p.box[j + 2], bx1 = p.box[j + 3], by1 = p.box[j + 4], bz1 = p.box[j + 5];
    if (bx1 - bx0 < 3 && bz1 - bz0 < 3) continue;
    const i0 = Math.max(0, Math.floor((bx0 - x0c) / S)), i1 = Math.min(N - 1, Math.floor((bx1 - x0c - 1e-3) / S));
    const k0 = Math.max(0, Math.floor((bz0 - z0c) / S)), k1 = Math.min(N - 1, Math.floor((bz1 - z0c - 1e-3) / S));
    for (let a = i0; a <= i1; a++) for (let b = k0; b <= k1; b++) {
      const c = a + b * N, cover = (Math.min(bx1, x0c + (a + 1) * S) - Math.max(bx0, x0c + a * S)) * (Math.min(bz1, z0c + (b + 1) * S) - Math.max(bz0, z0c + b * S));
      if (cover < S * S * 0.2 && by1 > top[c]) continue; // a thin tower doesn't make the whole 16 m cell tall
      if (by0 < base[c]) base[c] = by0;
      if (by1 > top[c]) { top[c] = by1; const t = p.tint[i]; col[c] = t || (MATS[p.mat[i]] ? MATS[p.mat[i]][2] : 0x888888); }
    }
  }
  return { top, col, base };
}
