// Streaming walk graphs for the city: one small grid per chunk (1 m cells, up to 3 floors a cell), built from that
// chunk's own boxes, packed into typed arrays (~30 KB a chunk). Links are stored as "half links": a cell's bit for a
// direction means the half step from its centre to the edge, toward that neighbour, is clear at its height. A real link
// needs both cells' half links and heights that match (a step or a drop), so chunks stitch across borders with no
// knowledge of each other: load any set of chunks and the graph is already joined.
// Used by the server's story rooms (NPCs, bots, enemies) and the client sim.
import { CHUNK } from './plan.js';
import { FLAGS } from './chunk.js';

export const NAV = { cell: 1, L: 3, step: 0.65, drop: 4.5, height: 1.8, none: -32768 };
const N = CHUNK / NAV.cell; // cells a side
const DIRS = [[1, 0], [0, 1], [-1, 0], [0, -1], [1, 1], [-1, 1], [-1, -1], [1, -1]]; // bit i = DIRS[i]
const OPP = [2, 3, 0, 1, 6, 7, 4, 5];

// a packed chunk (chunk.js) -> { cx, cz, h: Int16Array (decimetres, NAV.none = no floor), link: Uint8Array, nodes }
// built on a half-metre occupancy grid: every solid box drops its [y0, y1] into each 0.5 m sub-cell it overlaps, then
// floors and half links are read off the sub-cells (a few interval tests each, no box loops): ~5 ms a chunk
export function buildChunkNav(p) {
  const X0 = p.cx * CHUNK, Z0 = p.cz * CHUNK, L = NAV.L, S = 2, M = N * S; // sub-cells per cell side, per chunk side
  const h = new Int16Array(N * N * L).fill(NAV.none), link = new Uint8Array(N * N * L);
  // intervals per sub-cell, as a linked list in typed arrays (y0, y1, next)
  let cap = 1 << 16, iy0 = new Float32Array(cap), iy1 = new Float32Array(cap), inext = new Int32Array(cap), ni = 0;
  const head = new Int32Array(M * M).fill(-1);
  const push = (c, y0, y1) => {
    if (ni === cap) { cap *= 2; const g = (a) => { const b = new a.constructor(cap); b.set(a); return b; }; iy0 = g(iy0); iy1 = g(iy1); inext = g(inext); }
    iy0[ni] = y0; iy1[ni] = y1; inext[ni] = head[c]; head[c] = ni++;
  };
  for (let i = 0; i < p.mat.length; i++) {
    if (p.flag[i] & FLAGS.NC) continue;
    const j = i * 6, x0 = p.box[j], y0 = p.box[j + 1], z0 = p.box[j + 2], x1 = p.box[j + 3], y1 = p.box[j + 4], z1 = p.box[j + 5];
    const a0 = Math.max(0, Math.floor((x0 - X0) * S + 1e-4)), a1 = Math.min(M - 1, Math.ceil((x1 - X0) * S - 1e-4) - 1);
    const c0 = Math.max(0, Math.floor((z0 - Z0) * S + 1e-4)), c1 = Math.min(M - 1, Math.ceil((z1 - Z0) * S - 1e-4) - 1);
    for (let a = a0; a <= a1; a++) for (let c = c0; c <= c1; c++) push(a + c * M, y0, y1);
  }
  // anything solid in sub-cell sc between ya and yb?
  const solid = (sc, ya, yb) => { for (let k = head[sc]; k >= 0; k = inext[k]) if (iy0[k] < yb && iy1[k] > ya) return true; return false; };
  let nodes = 0;
  const tops = new Float32Array(64), cells = new Int32Array(4);
  for (let i = 0; i < N; i++) for (let k = 0; k < N; k++) {
    const sa = i * S, sc0 = k * S;
    cells[0] = sa + sc0 * M; cells[1] = sa + 1 + sc0 * M; cells[2] = sa + (sc0 + 1) * M; cells[3] = sa + 1 + (sc0 + 1) * M;
    // the floor candidates: every top in the cell's 4 sub-cells, low to high
    let nt = 0;
    for (let c = 0; c < 4; c++) for (let q = head[cells[c]]; q >= 0 && nt < 64; q = inext[q]) tops[nt++] = iy1[q];
    if (!nt) continue;
    const ts = tops.subarray(0, nt).sort();
    let lv = 0, last = -1e9;
    for (let ti = 0; ti < nt && lv < L; ti++) {
      const t = ts[ti];
      if (t - last < 0.3) continue;
      // the floor has to hold up the middle (2+ of the 4 sub-cells have a top within a step of it), with headroom
      let held = 0, blocked = false;
      for (let c = 0; c < 4 && !blocked; c++) {
        let hold = false;
        for (let q = head[cells[c]]; q >= 0; q = inext[q]) {
          if (iy1[q] <= t + 1e-3 && iy1[q] > t - NAV.step && iy0[q] < t) hold = true;
          if (iy0[q] < t + NAV.height && iy1[q] > t + 0.01) { blocked = true; break; }
        }
        if (hold) held++;
      }
      if (blocked || held < 2) continue;
      h[(i + k * N) * L + lv++] = Math.round(t * 10); nodes++; last = t;
    }
  }
  // half links: the sub-cells on the side of the cell toward each neighbour must be clear from a step up to head height
  const SIDE = [[[1, 0], [1, 1]], [[0, 1], [1, 1]], [[0, 0], [0, 1]], [[0, 0], [1, 0]], [[1, 1]], [[0, 1]], [[0, 0]], [[1, 0]]];
  for (let i = 0; i < N; i++) for (let k = 0; k < N; k++) for (let lv = 0; lv < L; lv++) {
    const hv = h[(i + k * N) * L + lv];
    if (hv === NAV.none) continue;
    const y = hv / 10;
    let bits = 0;
    for (let d = 0; d < 8; d++) {
      let ok = true;
      for (const [u, v] of SIDE[d]) if (solid(i * S + u + (k * S + v) * M, y + NAV.step, y + NAV.height)) { ok = false; break; }
      if (ok) bits |= 1 << d;
    }
    link[(i + k * N) * L + lv] = bits;
  }
  return { cx: p.cx, cz: p.cz, h, link, nodes, bytes: h.byteLength + link.byteLength };
}

// a binary min-heap on e[0]
class Heap {
  constructor() { this.a = []; }
  get size() { return this.a.length; }
  push(e) { const a = this.a; a.push(e); let i = a.length - 1; while (i) { const p = (i - 1) >> 1; if (a[p][0] <= a[i][0]) break; [a[p], a[i]] = [a[i], a[p]]; i = p; } }
  pop() {
    const a = this.a, top = a[0], last = a.pop();
    if (a.length) { a[0] = last; let i = 0; for (;;) { const l = 2 * i + 1, r = l + 1; let m = i; if (l < a.length && a[l][0] < a[m][0]) m = l; if (r < a.length && a[r][0] < a[m][0]) m = r; if (m === i) break; [a[m], a[i]] = [a[i], a[m]]; i = m; } }
    return top;
  }
}

// a set of loaded chunk navs: lookups by global cell, A*, and a simple path smoother
export class NavWorld {
  constructor() { this.chunks = new Map(); }
  set(cx, cz, nav) { this.chunks.set(cx * 65536 + cz, nav); }
  drop(cx, cz) { this.chunks.delete(cx * 65536 + cz); }
  // the floor heights at global cell (gx, gz): Int16 view of up to L values, or null if the chunk isn't loaded
  cell(gx, gz) {
    const cx = Math.floor(gx / N), cz = Math.floor(gz / N), c = this.chunks.get(cx * 65536 + cz);
    if (!c) return null;
    return { c, o: ((gx - cx * N) + (gz - cz * N) * N) * NAV.L };
  }
  // nearest node to a world point: the floor in that cell closest below the feet (+ a step)
  locate(x, y, z) {
    const gx = Math.floor(x / NAV.cell), gz = Math.floor(z / NAV.cell);
    for (let r = 0; r <= 2; r++) for (let dx = -r; dx <= r; dx++) for (let dz = -r; dz <= r; dz++) {
      if (Math.max(Math.abs(dx), Math.abs(dz)) !== r) continue;
      const q = this.cell(gx + dx, gz + dz);
      if (!q) continue;
      let best = -1, bd = 1e9;
      for (let lv = 0; lv < NAV.L; lv++) { const hv = q.c.h[q.o + lv]; if (hv === NAV.none) continue; const d = Math.abs(hv / 10 - y) + (hv / 10 > y + NAV.step ? 5 : 0); if (d < bd) { bd = d; best = lv; } }
      if (best >= 0 && bd < 6) return { gx: gx + dx, gz: gz + dz, lv: best };
    }
    return null;
  }
  y(n) { const q = this.cell(n.gx, n.gz); return q ? q.c.h[q.o + n.lv] / 10 : 0; }
  // the neighbours of a node: both half links set, and a step up / any step down / a drop (one way) to a floor there
  *next(n) {
    const q = this.cell(n.gx, n.gz);
    if (!q) return;
    const bits = q.c.link[q.o + n.lv], y = q.c.h[q.o + n.lv] / 10;
    for (let d = 0; d < 8; d++) {
      if (!(bits & (1 << d))) continue;
      const gx = n.gx + DIRS[d][0], gz = n.gz + DIRS[d][1], r = this.cell(gx, gz);
      if (!r) continue;
      if (d >= 4) { // a diagonal needs both of its side cells open too, or bots cut wall corners
        const a = this.cell(n.gx + DIRS[d][0], n.gz), b = this.cell(n.gx, n.gz + DIRS[d][1]);
        if (!a || !b || !(bits & (1 << (DIRS[d][0] > 0 ? 0 : 2))) || !(bits & (1 << (DIRS[d][1] > 0 ? 1 : 3)))) continue;
      }
      for (let lv = 0; lv < NAV.L; lv++) {
        const hv = r.c.h[r.o + lv];
        if (hv === NAV.none) continue;
        const dy = hv / 10 - y;
        if (dy > NAV.step || dy < -NAV.drop) continue;
        if (!(r.c.link[r.o + lv] & (1 << OPP[d])) && dy > -NAV.step) continue; // a drop needs only our side clear
        yield { gx, gz, lv, cost: (d >= 4 ? 1.414 : 1) * NAV.cell + Math.abs(dy) * 0.5 };
      }
    }
  }
  // A* between two world points. returns [[x, y, z], ...] (smoothed) or null. max = nodes to expand before giving up
  path(a, b, max = 8000) {
    const s0 = this.locate(a[0], a[1], a[2]), g = this.locate(b[0], b[1], b[2]);
    if (!s0 || !g) return null;
    // node key: (gx, gz, lv) packed into one number; per-search maps of cost and parent
    const key = (gx, gz, lv) => ((gx + 32768) * 65536 + (gz + 32768)) * 4 + lv;
    const gk = key(g.gx, g.gz, g.lv), cost = new Map(), came = new Map(), open = new Heap();
    const sk = key(s0.gx, s0.gz, s0.lv);
    cost.set(sk, 0); came.set(sk, -1); open.push([Math.hypot(s0.gx - g.gx, s0.gz - g.gz), 0, sk]);
    let it = 0, found = false;
    while (open.size && it++ < max) {
      const [, c, k] = open.pop();
      if (k === gk) { found = true; break; }
      if (c > cost.get(k)) continue;
      const lv = k % 4, gz = Math.floor(k / 4) % 65536 - 32768, gx = Math.floor(k / 4 / 65536) - 32768;
      const q = this.cell(gx, gz);
      if (!q) continue;
      const bits = q.c.link[q.o + lv], y = q.c.h[q.o + lv];
      for (let d = 0; d < 8; d++) {
        if (!(bits & (1 << d))) continue;
        const nx = gx + DIRS[d][0], nz = gz + DIRS[d][1];
        if (d >= 4 && (!(bits & (1 << (DIRS[d][0] > 0 ? 0 : 2))) || !(bits & (1 << (DIRS[d][1] > 0 ? 1 : 3))))) continue; // no corner cutting
        const r = this.cell(nx, nz);
        if (!r) continue;
        for (let l2 = 0; l2 < NAV.L; l2++) {
          const hv = r.c.h[r.o + l2];
          if (hv === NAV.none) continue;
          const dy = (hv - y) / 10;
          if (dy > NAV.step || dy < -NAV.drop) continue;
          if (!(r.c.link[r.o + l2] & (1 << OPP[d])) && dy > -NAV.step) continue;
          const mk = key(nx, nz, l2), mc = c + (d >= 4 ? 1.414 : 1) * NAV.cell + Math.abs(dy) * 0.5;
          const old = cost.get(mk);
          if (old !== undefined && old <= mc) continue;
          cost.set(mk, mc); came.set(mk, k); open.push([mc + Math.hypot(nx - g.gx, nz - g.gz) * NAV.cell * 1.4, mc, mk]); // a greedy heuristic: a slightly longer path, far fewer nodes
        }
      }
    }
    if (!found) return null;
    const pts = [];
    for (let k = gk; k !== -1 && k !== undefined; k = came.get(k)) {
      const lv = k % 4, gz = Math.floor(k / 4) % 65536 - 32768, gx = Math.floor(k / 4 / 65536) - 32768;
      pts.push([(gx + 0.5) * NAV.cell, this.y({ gx, gz, lv }), (gz + 0.5) * NAV.cell]);
    }
    pts.reverse();
    // drop points on straight runs (same direction, same height)
    const out = [pts[0]];
    for (let i = 1; i < pts.length - 1; i++) {
      const p = out[out.length - 1], q = pts[i], r = pts[i + 1];
      const d1 = [Math.sign(q[0] - p[0]), Math.sign(q[2] - p[2])], d2 = [Math.sign(r[0] - q[0]), Math.sign(r[2] - q[2])];
      if (d1[0] !== d2[0] || d1[1] !== d2[1] || Math.abs(q[1] - p[1]) > 0.05 || Math.abs(r[1] - q[1]) > 0.05) out.push(q);
    }
    if (pts.length > 1) out.push(pts[pts.length - 1]);
    return out;
  }
  get bytes() { let b = 0; for (const c of this.chunks.values()) b += c.bytes; return b; }
}
