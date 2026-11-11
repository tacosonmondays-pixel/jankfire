// Skull Rock's shape (Islands, Islands S&D): one function for the look and for what you bump into. the Blender model
// (tools/blender/arch/make_skullrock.py) skins the grid this makes (tools/arch/dumpskull.mjs writes it out), and
// shared/map.js skullRock() stands the same shape up as boxes (skullSolid). change a number here: re-dump, re-run Blender.
// what it is: a weathered stone skull half sunk in the beach, facing -z. a domed cranium, a heavy brow, two deep eye
// sockets (a level floor in each: you stand in them), the nose's hole, cheekbones, the upper jaw on the sand with the
// cave mouth under its teeth. local frame: its middle at x 0, z 69. about 19 m wide, 20 m deep, 12.6 m tall.
const C = [0, 5.85, 69], RX = 9, RY = 6.4, RZ = 9.2;  // the cranium's middle (sunk to its upper teeth) and half sizes
const NT = 104, NP = 52, P0 = -1, P1 = Math.PI / 2;  // columns round it, rows up it (elevation from under the sand to the crown)
const IC = 12, JC = 4;                               // the teeth's row; the cave mouth: this many columns each side of the face's middle
const EYE = 6, TOP = 12.5;                           // the eye sockets' floor, the crown (both walk-graph levels: shared/map.js)
export const SKULL = { C, RX, RY, RZ, NT, NP, IC, JC, EYE, TOP, cave: { hw: 2, top: 3, back: 72.5 } }; // (the cave: 4 m wide, 3 m high, in from the mouth to z 72.5)

const hsh = (...a) => { let x = 0; a.forEach((v, i) => { x += Math.sin(v * (12.9898 + i * 7.233) + i * 3.17) * 43758.5453; }); return x - Math.floor(x); };
const wrap = (a) => { const t = (a + Math.PI) % (2 * Math.PI); return (t < 0 ? t + 2 * Math.PI : t) - Math.PI; };
const g = (th, ph, t0, p0, wt, wp) => Math.exp(-((wrap(th - t0) * Math.cos(ph) / wt) ** 2) - ((ph - p0) / wp) ** 2); // a bump (or a hollow) at azimuth t0, elevation p0
const sq = (th, ph, t0, p0, wt, wp, k = 4) => Math.exp(-(Math.abs(wrap(th - t0) * Math.cos(ph) / wt) ** k) - Math.abs((ph - p0) / wp) ** k); // the same, squarer shoulders
const sm = (t) => { t = Math.max(0, Math.min(1, t)); return t * t * (3 - 2 * t); };

// how far out the surface is along (th azimuth from the face, ph elevation), as a share of the cranium; how deep in a
// hollow that point is (0..1: the sockets, the nose go dark); and how far into an eye socket
function radius(th, ph) {
  const front = Math.cos(th); // 1 at the face, -1 at the back of the head
  let r = 1, hole = 0, eye = 0;
  r += 0.12 * g(th, ph, Math.PI, 0.2, 1.0, 0.7);                 // the back of the head swells
  r += 0.05 * g(th, ph, 0, 0.75, 0.8, 0.25);                     // the forehead
  for (const s of [-1, 1]) {
    r += 0.13 * g(th, ph, s * 0.5, 0.42, 0.36, 0.075);           // the brow ridge, heavy, over each eye
    r += 0.11 * g(th, ph, s * 0.95, -0.12, 0.2, 0.16);           // cheekbones
    r -= 0.08 * g(th, ph, s * 1.45, 0.1, 0.28, 0.3);             // temples, hollow
  }
  for (const s of [-1, 1]) { const e = sq(th, ph, s * 0.5, 0.14, 0.27, 0.2, 3); r -= 0.42 * e; eye = Math.max(eye, e); } // eye sockets: big, deep
  hole = eye;
  const n = Math.max(g(th, ph, 0, -0.2, 0.06, 0.13), g(th, ph, 0.07, -0.3, 0.07, 0.08), g(th, ph, -0.07, -0.3, 0.07, 0.08)); // the nose: a point over two lobes
  r -= 0.3 * n; hole = Math.max(hole, n);
  const low = Math.max(0, Math.min(1, (-ph - 0.2) / 0.3)); // below the cheekbones the face narrows to the upper jaw
  r -= low * (0.07 * Math.max(0, front) ** 0.6 + 0.03 * Math.abs(Math.sin(th)) ** 2);
  r += 0.06 * g(th, ph, 0, -0.44, 0.6, 0.08);                    // the upper jaw's ridge, where the teeth sit
  r += (hsh(Math.round(th * 9), Math.round(ph * 9)) - 0.5) * 0.02; // weathered, in facets
  return [r, hole, eye];
}
const PC = P0 + (P1 - P0) * IC / NP; // the teeth line
// a point of the skin: [x, y, z, hole]
function pt(th, ph) {
  const p = Math.max(ph, PC), cp = Math.cos(p), [r, hole, eye] = radius(th, p);
  // (hr: how far out, level. the sockets go straight back into the head, as tall inside as their openings: room to stand)
  let y = C[1] + Math.sin(p) * RY * (r + 0.42 * eye) * (1 + 0.1 * Math.max(0, Math.sin(ph))), hr = cp * r;
  if (ph < PC) { // below the teeth the jaw and cheeks carry the skull's width down to the sand, lumpy, the cheeks as buttresses
    const t = (PC - ph) / (PC - P0);
    const base = 1.02 + 0.045 * Math.sin(th * 5 + 1) + 0.03 * Math.sin(th * 11) + 0.07 * (g(th, 0, 1.15, 0, 0.3, 9) + g(th, 0, -1.15, 0, 0.3, 9)) - 0.04 * Math.max(0, Math.cos(th)) ** 3;
    hr += (base - hr) * sm(t * 1.7);
    y += (-0.35 - y) * t;
  }
  if (eye > 0.08 && y < EYE) y += (EYE - (EYE - y) * 0.2 - y) * sm((eye - 0.08) / 0.2); // the sockets' floors: level, to stand on
  if (eye > 0.08 && y > 7 && y < EYE + 2.2) y += (EYE + 2.2 - (EYE + 2.2 - y) * 0.2 - y) * sm((eye - 0.08) / 0.2); // and their roofs, level too: headroom, right to the back
  y -= Math.max(0, y - 12.2) * 0.6; // the crown: flatter (it's a floor too)
  return [C[0] + Math.sin(th) * RX * hr, y, C[2] - Math.cos(th) * RZ * hr, hole]; // th 0 = the face = -z; +th turns toward +x
}
let GRID = null;
// the skin: (NP + 1) rows of NT points, row 0 under the sand, the last row the crown
export function skullGrid() {
  if (GRID) return GRID;
  GRID = [];
  for (let i = 0; i <= NP; i++) { const row = []; for (let j = 0; j < NT; j++) row.push(pt(2 * Math.PI * j / NT - Math.PI, P0 + (P1 - P0) * i / NP)); GRID.push(row); }
  return GRID;
}

// is (x, y, z) in the rock? by the column of the skin it's behind: a level line out from it crosses the skin an odd
// number of times. out: counted that much further in than it is (the boxes stand a hair proud of the skin, so a camera
// against them never ends up inside the model)
function inRock(G, x, y, z, out = 0.15) {
  const ux = (x - C[0]) / RX, uz = (z - C[2]) / RZ, d = Math.hypot(ux, uz) - out / RX;
  const th = Math.atan2(ux, -uz), j = ((Math.round((th + Math.PI) / (2 * Math.PI) * NT) % NT) + NT) % NT;
  let n = 0;
  for (let i = 0; i < NP; i++) {
    const a = G[i][j], b = G[i + 1][j];
    if ((a[1] > y) === (b[1] > y)) continue;
    const t = (y - a[1]) / (b[1] - a[1]), h = Math.hypot((a[0] + (b[0] - a[0]) * t - C[0]) / RX, (a[2] + (b[2] - a[2]) * t - C[2]) / RZ);
    if (h > d) n++;
  }
  return n & 1;
}
// true cells -> a few big rectangles that cover them (they may overlap: it's a union). [i0, j0, i1, j1], ends exclusive
function cover(m, nx, nz) {
  const on = (i, j) => i >= 0 && j >= 0 && i < nx && j < nz && m[i * nz + j], done = new Uint8Array(nx * nz), out = [];
  const rowX = (j, i0, i1) => { for (let i = i0; i < i1; i++) if (!on(i, j)) return false; return true; };
  const colZ = (i, j0, j1) => { for (let j = j0; j < j1; j++) if (!on(i, j)) return false; return true; };
  const grow = (i, j, xFirst) => {
    let i0 = i, i1 = i + 1, j0 = j, j1 = j + 1;
    const gx = () => { while (colZ(i0 - 1, j0, j1)) i0--; while (colZ(i1, j0, j1)) i1++; }, gz = () => { while (rowX(j0 - 1, i0, i1)) j0--; while (rowX(j1, i0, i1)) j1++; };
    if (xFirst) { gx(); gz(); } else { gz(); gx(); }
    let fresh = 0;
    for (let a = i0; a < i1; a++) for (let b = j0; b < j1; b++) if (!done[a * nz + b]) fresh++;
    return [i0, j0, i1, j1, fresh];
  };
  for (let i = 0; i < nx; i++) for (let j = 0; j < nz; j++) {
    if (!m[i * nz + j] || done[i * nz + j]) continue;
    const a = grow(i, j, true), b = grow(i, j, false), r = b[4] > a[4] ? b : a;
    for (let p = r[0]; p < r[2]; p++) for (let q = r[1]; q < r[3]; q++) done[p * nz + q] = 1;
    out.push(r.slice(0, 4));
  }
  return out;
}
let SOLID = null;
// the rock as boxes [x0, y0, z0, x1, y1, z1] (local frame): half-metre cells, half-metre layers from the sockets up (a
// body steps up 0.6: the dome's a walk), taller ones below (the jaw's a wall), the cave cut out of it. where two layers
// have the same outline their boxes are one
export function skullSolid() {
  if (SOLID) return SOLID;
  const G = skullGrid(), S = 0.5, X0 = -11, Z0 = 58, nx = 44, nz = 48, cv = SKULL.cave;
  const bands = [[0, cv.top], [cv.top, 4.5], [4.5, 5.5]];
  for (let y = 5.5; y < TOP - 0.01; y += 0.5) bands.push([y, y + 0.5]);
  const open = new Map(); SOLID = [];
  for (const [y0, y1] of bands) {
    const m = new Uint8Array(nx * nz), ys = [];
    for (let y = y0 + 0.25; y < y1; y += 0.25) ys.push(y); // (a tall layer: rock wherever any of its heights is)
    for (let i = 0; i < nx; i++) for (let j = 0; j < nz; j++) {
      const x = X0 + (i + 0.5) * S, z = Z0 + (j + 0.5) * S;
      if (y1 <= cv.top && Math.abs(x) < cv.hw && z < cv.back) continue; // the cave
      if (ys.some((y) => inRock(G, x, y, z))) m[i * nz + j] = 1;
    }
    const next = new Map();
    for (const r of cover(m, nx, nz)) {
      const k = r.join(','), b = open.get(k);
      if (b) { b[4] = y1; next.set(k, b); continue; }
      const nb = [X0 + r[0] * S, y0, Z0 + r[1] * S, X0 + r[2] * S, y1, Z0 + r[3] * S];
      SOLID.push(nb); next.set(k, nb);
    }
    open.clear(); for (const [k, b] of next) open.set(k, b);
  }
  return SOLID;
}
