// The Commute's ground as a real landscape: rolling hills, dry gullies and hollows round the dead highway instead of
// half-metre terraces. commuteY(x, z) is the height anywhere, worked out from the point alone (seeded noise, no grid),
// so two chunks built apart meet exactly at their seam and the server and every client agree.
// The ground is held level (or on its own gentle ramp) where something stands on it: the deck and its shoulders, the
// slip road down from the Bottom, the Unpaid camp, the fallen 13, the shops, the Loop's portal, the Pile-Up. Hills ease
// in over a few metres from those (FLAT). groundField() turns a rectangle of it into a 2 m grid: the chunk draws that
// grid (mesh.js 'field'), hides stepped boxes under it ({ ter: 1 }, the rest of the game's ground) and the physics
// walks on the same grid (world.js ChunkWorld: boxes.terrain), so what you see is what you stand on.
import { SLICE, hwY, GROUND } from './slice.js';
import { SLIP, GUT_LINK } from './roads.js';
import { lattice } from '../terrain.js';

const H = SLICE.highway, C = SLICE.camp, D = SLICE.digit;
const sm = (a, b, v) => { const k = Math.max(0, Math.min(1, (v - a) / (b - a))); return k * k * (3 - 2 * k); };
const n1 = lattice(0x7e11), n2 = lattice(0x7e12), n3 = lattice(0x7e13), wob = lattice(0x7e14);
export const CELL = 2; // the grid (m): physics, the drawn ground and the hidden steps all use it
const base = (z) => hwY(z) - 0.25; // the hill's own climb (smooth: no more half-metre terraces)
const deck = (z) => hwY(z) - 0.4; // just under the deck and anything built at the old ground's height
const onBase = (x, z) => base(z), onDeck = (x, z) => deck(z);
// the town's side of the Commute's west edge (x 96): the Bottom's terraces, the Gut border, the Gut plateau. the
// hillside climbs to meet them (no more dirt cliff), its edge following their floors smoothed over a terrace's depth
const BT = SLICE.bottom, westStep = (z) => (z >= 0 ? Math.min(BT.n - 1, Math.max(0, Math.floor((256 - z) / BT.terr))) * BT.rise : z >= -48 ? SLICE.border.y : SLICE.gut.y);
export const westY = (z) => { let s = 0; for (let k = -6; k <= 6; k++) s += westStep(z + k * 2.2); return s / 13; };

// [x0, z0, x1, z1, y (a number or (x, z) => y), ease (m), 'soft'?]: level ground; the hills come back over `ease` m round it
const sy = hwY(SLIP.z, true), sz0 = SLIP.z - 2.6;
export const FLAT = [
  [40, -256, 96, 256, (x, z) => westY(z) - 0.05, 36], // the town's edge: the hillside climbs to its terraces and the border (the slope pass widens it as it needs)
  [H.x0 - 1.2, H.westZ[0] - 3, H.x1 + 1.2, 256, onDeck, 10], // the deck, its barriers, the gap under the collapse
  [96, H.westZ[0] - 3, H.x0, H.westZ[1] + 3, H.yTop - 0.04, 8], // the top turn west into the Gut (GUT_LINK)
  [GUT_LINK.rect[2] - 1, GUT_LINK.rect[1], 98, GUT_LINK.rect[3], H.yTop - 0.04, 4],
  [C.x - 26, C.z - 22, C.x + 26, C.z + 22, hwY(C.z, true) - 0.02, 10], // the Unpaid camp (everything in it stands at one height)
  [D.x - 12, D.z - 12, D.x + 12, D.z + 12, hwY(D.z, true) - 0.02, 8], // the fallen 13's glassed ring
  [112, 210, 156, 222, (x, z) => base(z) + (hwY(202, true) - 0.04 - base(212)) * (1 - Math.max(0, Math.min(1, (z - 212) / 12))), 6, 'soft'], // PREVIOUSLY LOVED MOTORS' forecourt: a gentle ramp up to the showroom
  [112, 200, 128, 212, hwY(202, true) - 0.02, 6], // ...and the showroom (shops.js) level
  [122, 122, 140, 134, hwY(124, true) - 0.02, 6], // PETROL & PISTOLS
  [97, sz0 - 0.4, SLIP.x1, SLIP.z + 3, (x) => 4 - (4 - sy) * (x - SLIP.x0) / (SLIP.x1 - SLIP.x0) - 0.15, 3], // under the slip road's ramp off terrace 1 (roads.js)
  [SLIP.x1, sz0 - 0.6, SLIP.ex + 5, SLIP.z + 3.2, sy - 0.02, 7], // the slip road's level stretch (the road is the ground here)
  [SLIP.ex - 5, sz0, SLIP.ex + 5, SLIP.sz + 3, (x, z) => sy * Math.max(0, Math.min(1, (SLIP.sz - z) / (SLIP.sz - sz0))) - 0.15, 6], // its ramp round the deck's foot
  [SLIP.ex - 6, H.zLow, H.x1 + 6, 256, 0, 6], // the deck's foot: cars come round it at 0
  [286, -104, 320, -88, hwY(-96, true) - 0.02, 10], // the Under-Hill Loop's portal and rails (act1set.js)
  [214, -28, 234, -12, hwY(-20, true) - 0.02, 6], // the Pile-Up and its pad (playground.js)
  [254, -158, 270, -142, hwY(-150, true) - 0.1, 6], // the dead walker tank
];
// dry gullies the rain cut downhill (south): x wanders along z. [x, z0, z1, depth, half width, seed]
const GULLY = [[246, -235, 230, 1.5, 9, 1], [292, -70, 236, 1.2, 7, 2], [124, -120, 105, 1.1, 7, 3]];

// the hills on their own (no flats): a slow swell, smaller hummocks, crumbs; then the gullies cut through
export function hills(x, z) {
  let n = (0.58 * n1(x / 70, z / 70) + 0.32 * n2(x / 32, z / 32) + 0.1 * n3(x / 13, z / 13)) * 2.1;
  n = Math.max(-1, Math.min(1, n));
  let h = n > 0 ? n * 3 : n * 1.4;
  for (const [gx, z0, z1, d, w, s] of GULLY) {
    if (z < z0 - w || z > z1 + w) continue;
    const cx = gx + 16 * wob(z / 90, s * 7.3) + 4 * wob(z / 23, s * 3.1), dd = Math.abs(x - cx);
    if (dd > w * 1.6) continue;
    const k = (1 - sm(w * 0.35, w * 1.6, dd)) * sm(z0 - w, z0 + 24, z) * (1 - sm(z1 - 24, z1 + w, z)); // (fading in and out at its ends)
    h = h * (1 - k) + Math.min(h, -d) * k;
  }
  return h;
}
// how far (x, z) is from a rectangle (0 inside)
const away = (f, x, z) => Math.hypot(Math.max(f[0] - x, 0, x - f[2]), Math.max(f[1] - z, 0, z - f[3]));
const fy = (f, x, z) => (typeof f[4] === 'function' ? f[4](x, z) : f[4]);

// the shape before smoothing: the hills, pulled to the flats near them. extra: a chunk's own flats ([x0, z0, x1, z1, y, ease])
function raw(x, z, L = FLAT, withHills = true) {
  let k = 1;
  const near = [];
  for (const f of L) {
    const d = away(f, x, z);
    if (d >= f[5]) continue;
    const w = 1 - sm(0, f[5], d);
    near.push(f, w); if (1 - w < k) k = 1 - w;
  }
  let y = base(z) + (withHills && k > 0 ? hills(x, z) * k : 0);
  for (let i = 0; i < near.length; i += 2) y += (fy(near[i], x, z) - y) * near[i + 1]; // (in list order: later ones win where they overlap)
  return y;
}
const inFlat = (L, x, z) => L.some((f) => f[6] !== 'soft' && x >= f[0] && x <= f[2] && z >= f[1] && z <= f[3]); // (soft: a shape to aim for, eased by the walkable-slope pass)
// nothing steeper than you can walk (and drive) up without noticing: ease the steep bits, the flats stay put
const MAXS = 0.5; // m per 2 m cell
function relax(Hs, fixed, nx, nz, edges) { // edges: the grid's own border moves too (the whole Commute); a chunk keeps its border (the seam)
  const vz = nz + 1, e = edges ? 0 : 1;
  for (let pass = 0; pass < 400; pass++) { // each point kept within MAXS of all four neighbours (cut down or built up)
    let any = false;
    for (let i = e; i <= nx - e; i++) for (let j = e; j <= nz - e; j++) {
      const k = i * vz + j;
      if (fixed[k]) continue;
      let mx = -Infinity, mn = Infinity, v;
      if (i > 0) { v = Hs[k - vz]; if (v > mx) mx = v; if (v < mn) mn = v; }
      if (i < nx) { v = Hs[k + vz]; if (v > mx) mx = v; if (v < mn) mn = v; }
      if (j > 0) { v = Hs[k - 1]; if (v > mx) mx = v; if (v < mn) mn = v; }
      if (j < nz) { v = Hs[k + 1]; if (v > mx) mx = v; if (v < mn) mn = v; }
      const lo = mx - MAXS, hi = mn + MAXS, h = Hs[k], t = lo > hi ? (lo + hi) / 2 : h < lo ? lo : h > hi ? hi : h;
      if (Math.abs(t - h) > 1e-4) { Hs[k] = t; any = true; }
    }
    if (!any) break;
  }
  for (let pass = 0; pass < 2; pass++) for (let i = 1; i < nx; i++) for (let j = 1; j < nz; j++) { // (then rounded off a little: no creases)
    const k = i * vz + j;
    if (!fixed[k]) Hs[k] = (Hs[k - vz] + Hs[k + vz] + Hs[k - 1] + Hs[k + 1] + Hs[k] * 4) / 8;
  }
}
// the whole Commute on one 2 m grid, made once (the same on the server and every client)
const R = { x0: SLICE.commute.rect[0], z0: SLICE.commute.rect[1], x1: SLICE.commute.rect[2], z1: SLICE.commute.rect[3] };
let G = null;
function grid() {
  if (G) return G;
  const nx = (R.x1 - R.x0) / CELL, nz = (R.z1 - R.z0) / CELL, vz = nz + 1, Hs = new Float32Array((nx + 1) * vz), fixed = new Uint8Array((nx + 1) * vz);
  for (let i = 0; i <= nx; i++) for (let j = 0; j <= nz; j++) { const x = R.x0 + i * CELL, z = R.z0 + j * CELL; Hs[i * vz + j] = raw(x, z); fixed[i * vz + j] = inFlat(FLAT, x, z) ? 1 : 0; }
  relax(Hs, fixed, nx, nz, true);
  return (G = { x0: R.x0, z0: R.z0, nx, nz, cell: CELL, H: Hs });
}
// the ground's height at (x, z) in the Commute
export function commuteY(x, z) {
  if (x < R.x0 || x > R.x1 || z < R.z0 || z > R.z1) return raw(x, z);
  return fieldAt(grid(), x, z);
}

// a rectangle of the Commute as a grid for the chunk: H = heights at the grid points (nx + 1) x (nz + 1), cell CELL m.
// col = per-point colour (rgb): dirt, darker down in the hollows and gullies, paler on the crests, ash to the north
export function groundField(x0, z0, x1, z1, extra) {
  const g = grid(), nx = Math.round((x1 - x0) / CELL), nz = Math.round((z1 - z0) / CELL), vz = nz + 1;
  const Hs = new Float32Array((nx + 1) * vz), col = new Uint8Array((nx + 1) * vz * 3);
  for (let i = 0; i <= nx; i++) for (let j = 0; j <= nz; j++) Hs[i * vz + j] = fieldAt(g, x0 + i * CELL, z0 + j * CELL);
  if (extra && extra.length) { // a chunk's own level bits (a car park): kept inside the chunk, so its edges still meet the next one
    const fixed = new Uint8Array((nx + 1) * vz);
    for (let i = 0; i <= nx; i++) for (let j = 0; j <= nz; j++) {
      const x = x0 + i * CELL, z = z0 + j * CELL, k = i * vz + j;
      for (const f of extra) { const d = away(f, x, z); if (d < f[5]) Hs[k] += (fy(f, x, z) - Hs[k]) * (1 - sm(0, f[5], d)); }
      if (inFlat(extra, x, z)) fixed[k] = 1;
    }
    relax(Hs, fixed, nx, nz);
  }
  let lo = Infinity, hi = -Infinity;
  for (let i = 0; i <= nx; i++) for (let j = 0; j <= nz; j++) {
    const x = x0 + i * CELL, z = z0 + j * CELL, k = i * vz + j, y = Hs[k];
    if (y < lo) lo = y; if (y > hi) hi = y;
    const rel = y - base(z), ash = 1 - sm(-172, -128, z), lite = Math.max(-1, Math.min(1, rel / 3)) * 0.14 + 0.03 * n3(x / 3.1, z / 3.1);
    let r = (0xc8 * (1 - ash) + 0x8a * ash) * (1 + lite), gg = (0xa0 * (1 - ash) + 0x7a * ash) * (1 + lite), b = 0x78 * (1 + lite * 0.6);
    const w = (1 - sm(R.x0, R.x0 + 34, x + 6 * wob(z / 17, x / 17))) * 0.85, fz = sm(-12, 12, z); // near the town: its colours creep out over the dirt
    if (w > 0) { // (the Bottom's pink-grey terrace dirt to the south, bruised flesh toward the Gut)
      const t = [0xb8 * fz + 0x8a * (1 - fz), 0x98 * fz + 0x3a * (1 - fz), 0x98 * fz + 0x44 * (1 - fz)];
      r += (t[0] * (1 + lite) - r) * w; gg += (t[1] * (1 + lite) - gg) * w; b += (t[2] * (1 + lite) - b) * w;
    }
    col[k * 3] = Math.max(0, Math.min(255, r)); col[k * 3 + 1] = Math.max(0, Math.min(255, gg)); col[k * 3 + 2] = Math.max(0, Math.min(255, b));
  }
  return { kind: 'field', ground: 1, x0, z0, nx, nz, cell: CELL, H: Hs, col, lo, hi, mat: 'ground' };
}
// height on a field (the same bilinear patch the physics and the drawn grid use), or null off it
export function fieldAt(f, x, z) {
  const fx = (x - f.x0) / f.cell, fz = (z - f.z0) / f.cell, i = Math.floor(fx), j = Math.floor(fz);
  if (i < 0 || j < 0 || i > f.nx || j > f.nz || fx > f.nx || fz > f.nz) return null;
  const ii = Math.min(i, f.nx - 1), jj = Math.min(j, f.nz - 1), u = fx - ii, v = fz - jj, vz = f.nz + 1, Hs = f.H;
  return (Hs[ii * vz + jj] * (1 - u) + Hs[(ii + 1) * vz + jj] * u) * (1 - v) + (Hs[ii * vz + jj + 1] * (1 - u) + Hs[(ii + 1) * vz + jj + 1] * u) * v;
}
GROUND.commute = commuteY; // (slice.js groundY)
