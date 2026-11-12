// The Gut's floor swells: wherever there's open ground (the gaps between the campus offices, the yards, the dead
// ends) the flesh rises in slow mounds and fat lumps, veined and bruised, breathing with the rest of the Gut. Streets,
// buildings, props, pools, the story's places and a 2 m strip at the chunk's edge stay flat, so nothing is swallowed
// and two chunks always meet flat. Same machinery as the Commute's hills (ground.js): a 'field' shape drawn only
// where it swells (ok cells), soft hidden steps under it, joined into boxes.terrain by world.js.
// gut.js gut() calls it last, when everything in the chunk is down.
import { SLICE, PLACES } from './slice.js';
import { NPC_SPOTS } from './cast_slice.js';
import { lattice } from '../terrain.js';

const GY = SLICE.gut.y, C = 2, LIFT = 0.02; // grid (m); the drawn swell sits a hair over the floor so they never fight
const n1 = lattice(0x6a31), n2 = lattice(0x6a32), v1 = lattice(0x6a33), w1 = lattice(0x6a34);
const sm = (a, b, v) => { const k = Math.max(0, Math.min(1, (v - a) / (b - a))); return k * k * (3 - 2 * k); };
const SPOTS = [...Object.values(PLACES).map((p) => p.p), ...Object.values(NPC_SPOTS).map((s) => s.p)];

// how much flesh swells at (x, z) with nothing in the way: mounds, and a vein web (0 or more, m)
function swell(x, z) {
  const m = Math.max(0, (0.62 * n1(x / 21, z / 21) + 0.38 * n2(x / 9, z / 9)) * 2.4 - 0.25) * 2.3;
  const wx = x + 4 * w1(x / 19, z / 19), wz = z + 4 * w1(z / 19 + 7.7, x / 19 - 3.3), d = Math.abs(v1(wx / 26, wz / 26)) * 26 * 0.6, t = 1 - d / 1.1;
  return m + (t > 0 ? 0.35 * Math.sqrt(t * (2 - t)) : 0);
}

export function gutMounds(B, streetAt, keep, holes) {
  const [rx0, rz0, rx1, rz1] = SLICE.gut.rect, X0 = Math.max(B.X0, rx0), X1 = Math.min(B.X1, rx1), Z0 = Math.max(B.Z0, rz0), Z1 = Math.min(B.Z1, rz1);
  const nx = Math.floor((X1 - X0) / C), nz = Math.floor((Z1 - Z0) / C);
  if (nx < 6 || nz < 6) return;
  const S = SLICE.stomach, blocked = new Uint8Array(nx * nz), cell = (x, z) => [Math.floor((x - X0) / C), Math.floor((z - Z0) / C)];
  const block = (x0, z0, x1, z1) => { const [a0, b0] = cell(x0, z0), [a1, b1] = cell(x1, z1); for (let i = Math.max(0, a0); i <= Math.min(nx - 1, a1); i++) for (let j = Math.max(0, b0); j <= Math.min(nz - 1, b1); j++) blocked[i * nz + j] = 1; };
  for (let i = 0; i < nx; i++) for (let j = 0; j < nz; j++) {
    const x = X0 + (i + 0.5) * C, z = Z0 + (j + 0.5) * C;
    if (i < 1 || j < 1 || i >= nx - 1 || j >= nz - 1 || streetAt(x, z) || Math.hypot(x - S.x, z - S.z) < S.r + 8 || keep.some((q) => x > q[0] - 4 && x < q[2] + 4 && z > q[1] - 4 && z < q[3] + 4)) blocked[i * nz + j] = 1;
  }
  for (const b of B.out.boxes) if (b[4] > GY + 0.05 && b[1] < GY + 3) block(b[0] - 0.6, b[2] - 0.6, b[3] + 0.6, b[5] + 0.6); // (buildings, walls, hidden boxes of props)
  for (const p of B.out.props) block(p[1] - 1, p[3] - 1, p[1] + 1, p[3] + 1);
  for (const s of B.out.shapes) for (const p of s.pts || [s.c || s.at]) if (p) { const r = s.r && !Array.isArray(s.r) ? s.r : Array.isArray(s.r) && s.kind === 'blob' ? Math.max(s.r[0], s.r[2]) : 1; block(p[0] - r - 0.6, p[2] - r - 0.6, p[0] + r + 0.6, p[2] + r + 0.6); }
  for (const h of holes || []) block(h[0] - 1, h[1] - 1, h[2] + 1, h[3] + 1);
  for (const p of SPOTS) if (Math.abs(p[1] - GY) < 3) block(p[0] - 7, p[2] - 7, p[0] + 7, p[2] + 7);
  // how far each cell is from anything that keeps the floor flat (chamfer, m)
  const dist = new Float32Array(nx * nz).fill(1e4);
  for (let k = 0; k < nx * nz; k++) if (blocked[k]) dist[k] = 0;
  const rel = (i, j, ii, jj, w) => { if (ii >= 0 && jj >= 0 && ii < nx && jj < nz && dist[ii * nz + jj] + w < dist[i * nz + j]) dist[i * nz + j] = dist[ii * nz + jj] + w; };
  for (let i = 0; i < nx; i++) for (let j = 0; j < nz; j++) { rel(i, j, i - 1, j, C); rel(i, j, i, j - 1, C); rel(i, j, i - 1, j - 1, C * 1.414); rel(i, j, i - 1, j + 1, C * 1.414); }
  for (let i = nx - 1; i >= 0; i--) for (let j = nz - 1; j >= 0; j--) { rel(i, j, i + 1, j, C); rel(i, j, i, j + 1, C); rel(i, j, i + 1, j + 1, C * 1.414); rel(i, j, i + 1, j - 1, C * 1.414); }
  // heights at the grid points: the swell, eased in from the nearest blocked cell (a point touching one stays flat)
  const vz = nz + 1, h = new Float32Array((nx + 1) * vz);
  let any = 0;
  for (let i = 0; i <= nx; i++) for (let j = 0; j <= nz; j++) {
    let d = 1e4;
    for (const [a, b] of [[i - 1, j - 1], [i, j - 1], [i - 1, j], [i, j]]) d = Math.min(d, a < 0 || b < 0 || a >= nx || b >= nz ? 0 : dist[a * nz + b]);
    if (d <= 0) continue;
    const v = swell(X0 + i * C, Z0 + j * C) * sm(0.5, 4.5, d);
    h[i * vz + j] = v; if (v > any) any = v;
  }
  if (any < 0.3) return;
  for (let pass = 0; pass < 200; pass++) { // walkable: nothing over ~25% (cut down only: the flat floor stays put)
    let ch = false;
    for (let i = 0; i <= nx; i++) for (let j = 0; j <= nz; j++) {
      const k = i * vz + j; let lo = Infinity;
      if (i > 0) lo = Math.min(lo, h[k - vz]); if (i < nx) lo = Math.min(lo, h[k + vz]); if (j > 0) lo = Math.min(lo, h[k - 1]); if (j < nz) lo = Math.min(lo, h[k + 1]);
      if (h[k] > lo + 0.5) { h[k] = lo + 0.5; ch = true; }
    }
    if (!ch) break;
  }
  const ok = new Uint8Array(nx * nz), H = new Float32Array((nx + 1) * vz), col = new Uint8Array((nx + 1) * vz * 3);
  let hi = GY;
  for (let i = 0; i < nx; i++) for (let j = 0; j < nz; j++) if (Math.max(h[i * vz + j], h[(i + 1) * vz + j], h[i * vz + j + 1], h[(i + 1) * vz + j + 1]) > 0.04) ok[i * nz + j] = 1;
  for (let i = 0; i <= nx; i++) for (let j = 0; j <= nz; j++) {
    const k = i * vz + j, y = GY + LIFT + h[k], x = X0 + i * C, z = Z0 + j * C;
    H[k] = y; if (y > hi) hi = y;
    const top = Math.min(1, h[k] / 1.6), vein = Math.max(0, 1 - Math.abs(v1((x + 4 * w1(x / 19, z / 19)) / 26, (z + 4 * w1(z / 19 + 7.7, x / 19 - 3.3)) / 26)) * 26 * 0.6 / 1.1);
    col[k * 3] = Math.min(255, (0xa0 + 0x50 * top) * (1 - 0.45 * vein)); col[k * 3 + 1] = Math.min(255, (0x22 + 0x58 * top) * (1 - 0.6 * vein)); col[k * 3 + 2] = Math.min(255, (0x2c + 0x40 * top) * (1 - 0.3 * vein)); // (fatty and pale on top, dark bruised cords)
  }
  const f = { kind: 'field', ground: 1, x0: X0, z0: Z0, nx, nz, cell: C, H, col, ok, lo: GY, hi, mat: 'flesh', pulse: 3, at: [X0 + 0.5, GY, Z0 + 0.5] };
  B.shape(f);
  // the hidden steps: only under the swells (the floor's own slabs are under everything else)
  const top = (i, j) => Math.round((H[i * vz + j] + H[(i + 1) * vz + j] + H[i * vz + j + 1] + H[(i + 1) * vz + j + 1]) / 4 / 0.1);
  for (let i = 0; i < nx; i++) for (let j = 0; j < nz;) {
    if (!ok[i * nz + j] || top(i, j) * 0.1 < GY + 0.08) { j++; continue; }
    let e = j + 1; const q = top(i, j);
    while (e < nz && ok[i * nz + e] && top(i, e) === q) e++;
    B.add(X0 + i * C, GY - 0.5, Z0 + j * C, X0 + (i + 1) * C, q * 0.1, Z0 + e * C, 'flesh', { ter: true });
    j = e;
  }
}
