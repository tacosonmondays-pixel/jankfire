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
export function buildChunkNav(p) {
  const X0 = p.cx * CHUNK, Z0 = p.cz * CHUNK, L = NAV.L;
  const h = new Int16Array(N * N * L).fill(NAV.none), link = new Uint8Array(N * N * L);
  // a coarse bucket grid of this chunk's solid boxes (8 m cells)
  const B = 8, NB = CHUNK / B, bucket = Array.from({ length: NB * NB }, () => []);
  const solid = [];
  for (let i = 0; i < p.mat.length; i++) {
    if (p.flag[i] & FLAGS.NC) continue;
    const j = i * 6, b = [p.box[j], p.box[j + 1], p.box[j + 2], p.box[j + 3], p.box[j + 4], p.box[j + 5]];
    solid.push(b);
    for (let a = Math.max(0, Math.floor((b[0] - X0) / B)); a <= Math.min(NB - 1, Math.floor((b[3] - X0 - 1e-4) / B)); a++)
      for (let c = Math.max(0, Math.floor((b[2] - Z0) / B)); c <= Math.min(NB - 1, Math.floor((b[5] - Z0 - 1e-4) / B)); c++) bucket[a + c * NB].push(b);
  }
  const near = (x, z) => bucket[Math.min(NB - 1, Math.max(0, Math.floor((x - X0) / B))) + Math.min(NB - 1, Math.max(0, Math.floor((z - Z0) / B))) * NB];
  // floors: every box top under the cell centre with headroom above it (nothing solid in [top, top + height))
  let nodes = 0;
  for (let i = 0; i < N; i++) for (let k = 0; k < N; k++) {
    const x = X0 + (i + 0.5) * NAV.cell, z = Z0 + (k + 0.5) * NAV.cell, list = near(x, z);
    const under = list.filter((b) => x >= b[0] && x < b[3] && z >= b[2] && z < b[5]);
    const tops = [...new Set(under.map((b) => b[4]))].sort((a, b) => a - b);
    let lv = 0;
    for (const t of tops) {
      if (lv >= L) break;
      if (under.some((b) => b[1] < t + NAV.height && b[4] > t + 0.01)) continue; // something's in the way above it
      h[(i + k * N) * L + lv++] = Math.round(t * 10); nodes++;
    }
  }
  // half links: from the centre toward each neighbour as far as the cell edge, a body-height box at this floor must
  // not hit anything (except what it's standing on: up to a step's height counts as walkable)
  const hw = 0.3;
  for (let i = 0; i < N; i++) for (let k = 0; k < N; k++) for (let lv = 0; lv < L; lv++) {
    const hv = h[(i + k * N) * L + lv];
    if (hv === NAV.none) continue;
    const y = hv / 10, x = X0 + (i + 0.5) * NAV.cell, z = Z0 + (k + 0.5) * NAV.cell, list = near(x, z);
    let bits = 0;
    for (let d = 0; d < 8; d++) {
      const ex = x + DIRS[d][0] * NAV.cell * 0.5, ez = z + DIRS[d][1] * NAV.cell * 0.5;
      const mnx = Math.min(x, ex) - hw, mxx = Math.max(x, ex) + hw, mnz = Math.min(z, ez) - hw, mxz = Math.max(z, ez) + hw;
      let ok = true;
      for (const b of list.length < 200 ? list : solid) if (b[0] < mxx && b[3] > mnx && b[2] < mxz && b[5] > mnz && b[1] < y + NAV.height && b[4] > y + NAV.step) { ok = false; break; }
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
    const s = this.locate(a[0], a[1], a[2]), g = this.locate(b[0], b[1], b[2]);
    if (!s || !g) return null;
    const key = (n) => ((n.gx + 32768) * 65536 + (n.gz + 32768)) * 4 + n.lv;
    const hx = (n) => Math.hypot(n.gx - g.gx, n.gz - g.gz) * NAV.cell;
    const open = new Heap(); open.push([hx(s), 0, s]);
    const came = new Map([[key(s), null]]), cost = new Map([[key(s), 0]]);
    const gk = key(g);
    let it = 0, end = null;
    while (open.size && it++ < max) {
      const [, c, n] = open.pop();
      const nk = key(n);
      if (nk === gk) { end = n; break; }
      if (c > cost.get(nk)) continue;
      for (const m of this.next(n)) {
        const mk = key(m), mc = c + m.cost;
        if (cost.has(mk) && cost.get(mk) <= mc) continue;
        cost.set(mk, mc); came.set(mk, n); open.push([mc + hx(m), mc, m]);
      }
    }
    if (!end) return null;
    const pts = [];
    for (let n = end; n; n = came.get(key(n))) pts.push([(n.gx + 0.5) * NAV.cell, this.y(n), (n.gz + 0.5) * NAV.cell]);
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
