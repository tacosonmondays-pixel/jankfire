// Cleaver skin: the Wüsthof 6" (16 cm) Cleaver, 1129500916 (old number 4680/16), a compact Western meat cleaver
// from Solingen.
//   Blade 160 mm long and ~72 mm tall, a near rectangle: a dead straight spine 3.2 mm thick at the heel, a square
//   nose with its top corner rounded off, and a long, almost straight edge that rises a little into the front corner.
//   Stamped (non-forged) from one sheet: no bolster, no distal taper to speak of; the blade's back edge drops straight
//   down from the handle to the heel. Parallel sides with an axe-like primary bevel ~16 mm tall along the edge, then a
//   narrow honed edge. A round hanging hole near the front top corner.
//   Full tang: the steel shows along the top of the handle (flush with the spine), along the bottom and round the butt
//   of a 128 mm handle of two black POM scales held by three stainless rivets.
// Refs: Wüsthof product page "Cleaver 16 cm | 6 inch" (1129500916: blade 16 cm, width 7.07 cm, handle 12.8 cm,
//   non-forged, 56 HRC, "polished stainless steel blade with a hole for hanging and a black handle secured by three
//   rivets"); Cutlery and More "Wusthof Meat Cleaver" (same SKU: blade 6", blade height 2.87" / 72.9 mm, overall 11.5",
//   spine 3.2 mm at the heel, 444 g); Knife Merchant (same SKU: blade 6.299" / 160 mm, handle 5.039" / 128 mm);
//   knivesandtools (4680/16: 16 cm x 7.1 cm, overall 28.9 cm, 442 g, POM handle); KaTom (4680/16: full tang, POM);
//   BladeHQ (4680/16: blade 6.0-6.25", width 3.00", thickness 0.12" / 3 mm, overall 11.25-11.5").
//   The hole's size and place are not in any spec sheet: ~11 mm, about 16 mm under the spine and 18 mm from the nose,
//   as on most Western cleavers.
// Held like every knife: the handle centred on the grip axis (y = 0) and the hand (z -0.036 .. +0.092); the spine runs
// flush along the top of the handle, so the blade hangs ~46 mm below the handle. Edge down, nose to -Z. No moving parts.
import { THREE, blade, slab, pin, resample, curve, arc, mat } from './kit.js';

const MM = 0.001;
// ---------------------------------------------------------------- measurements (mm)
// u = mm in front of the blade's back edge (= the front of the scales), v = mm above the grip axis
const Z0 = -0.036;                       // the blade's back edge / the front face of the scales
const BLADE_L = 160;                     // back edge to nose, along the spine
const SPINE_V = 13.0;                    // the spine = the top of the tang = the top of the handle
const BLADE_H = 72;                      // spine to edge at the heel
const SPINE_T = 3.2;                     // the sheet the blade is stamped from
const BEVEL_H = 16;                      // primary bevel: this tall above the edge
const HONE_H = 1.4;                      // the honed edge
const NOSE_R = 7;                        // the nose's top corner, rounded off
const HOLE_U = 142, HOLE_V = SPINE_V - 16, HOLE_R = 5.5;
const TANG_OUT = 0.5;                    // the tang stands this much proud of the scales so its steel shows
const N = 26;                            // blade stations

// ---------------------------------------------------------------- colours
const STEEL = 0xcdd3da;                  // polished flats, spine and tang
const BEVEL = 0xe7ebef;                  // the ground bevel catches the light differently
const HONED = 0xf6f8fa;                  // the sharpened edge
const POM = 0x1d1e21;                    // black polyoxymethylene scales
const RIVET = 0xdde2e7;

const P = (u, v) => [Z0 - u * MM, v * MM];          // side view point [z, y]
const V3 = (x, u, v) => [x * MM, v * MM, Z0 - u * MM]; // model point from mm

// ---------------------------------------------------------------- handle stations (u negative = toward the butt)
//   u, top, bottom, half width (of the POM, at the widest)
const HANDLE = [
  [0, 12.5, -12.5, 7.4],
  [-2.5, 12.5, -12.6, 8.2],
  [-14, 12.5, -12.8, 8.6],
  [-40, 12.5, -13.1, 8.8],
  [-70, 12.5, -13.3, 8.8],
  [-95, 12.5, -13.7, 8.7],
  [-108, 12.4, -14.4, 8.5],
  [-116, 11.9, -14.8, 8.2],
  [-121.2, 10.6, -14.3, 7.7],
  [-124.8, 8.0, -12.4, 6.9],
  [-126.9, 4.4, -9.0, 5.7],
  [-127.6, 0.2, -4.2, 4.0],
];
const RIVETS_U = [-22, -63, -104], RIVET_R = 2.6;
const BUTT_U = HANDLE[HANDLE.length - 1][0] - TANG_OUT;

// a closed solid through cross-section loops ([x, y, z] each, same count). Consecutive loops are joined; the first
// and the last get flat caps. Faces are turned away from the middle of the loops they join (fine for convex sections).
function loft(loops, color) {
  const pos = [];
  const cen = loops.map((L) => {
    const c = [0, 0, 0];
    for (const p of L) { c[0] += p[0] / L.length; c[1] += p[1] / L.length; c[2] += p[2] / L.length; }
    return c;
  });
  const tri = (a, b, c, ref, dir) => {
    const ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2], vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2];
    const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    if (nx * nx + ny * ny + nz * nz < 1e-18) return;
    const d = dir || [(a[0] + b[0] + c[0]) / 3 - ref[0], (a[1] + b[1] + c[1]) / 3 - ref[1], (a[2] + b[2] + c[2]) / 3 - ref[2]];
    if (nx * d[0] + ny * d[1] + nz * d[2] < 0) pos.push(...a, ...c, ...b); else pos.push(...a, ...b, ...c);
  };
  for (let k = 0; k < loops.length - 1; k++) {
    const A = loops[k], B = loops[k + 1], n = A.length;
    const ref = [(cen[k][0] + cen[k + 1][0]) / 2, (cen[k][1] + cen[k + 1][1]) / 2, (cen[k][2] + cen[k + 1][2]) / 2];
    for (let j = 0; j < n; j++) {
      const j1 = (j + 1) % n;
      tri(A[j], A[j1], B[j1], ref); tri(A[j], B[j1], B[j], ref);
    }
  }
  const cap = (k, o) => {
    const L = loops[k], c = cen[k], dir = [c[0] - cen[o][0], c[1] - cen[o][1], c[2] - cen[o][2]];
    for (let j = 0; j < L.length; j++) tri(c, L[j], L[(j + 1) % L.length], null, dir);
  };
  cap(0, 1); cap(loops.length - 1, loops.length - 2);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.computeVertexNormals();
  return new THREE.Mesh(geo, mat(color));
}

// a scale pair's cross-section: a flat top and bottom over the tang, the edges rounded over, the sides a little full
function section(u, top, bot, w) {
  const rc = Math.min(3.5, w * 0.45, (top - bot) * 0.3), k = rc * (1 - Math.SQRT1_2), mid = (top + bot) / 2;
  const side = [[w - rc, top], [w - k, top - k], [w, top - rc], [w + 0.3, mid], [w, bot + rc], [w - k, bot + k], [w - rc, bot]];
  const loop = side.map(([x, v]) => V3(x, u, v));
  for (let i = side.length - 1; i >= 0; i--) loop.push(V3(-side[i][0], u, side[i][1]));
  return loop;
}

export function build(g) {
  // ---------------------------------------------------------- outlines
  // the edge: nearly straight, its lowest point a little ahead of the middle, rising ~3 mm into the front corner
  const EDGE = resample(curve([P(0, SPINE_V - BLADE_H), P(45, SPINE_V - BLADE_H - 0.8), P(100, SPINE_V - BLADE_H - 1.2),
    P(135, SPINE_V - BLADE_H - 0.6), P(BLADE_L, SPINE_V - BLADE_H + 2.2)], 24), N);
  // the grind line: the bevel's top, parallel to the edge
  const GRIND = EDGE.map(([z, y]) => [z, y + BEVEL_H * MM]);

  // ---------------------------------------------------------- the steel: one stamped sheet, blade flats + full tang
  // (everything above the bevel; the bevel itself is the blade() below). Round from the nose, back along the
  // grind line, up the back edge, round the tang (standing proud of the scales) and forward along the spine.
  const sheet = [];
  sheet.push(...arc(Z0 - (BLADE_L - NOSE_R) * MM, (SPINE_V - NOSE_R) * MM, NOSE_R * MM, Math.PI / 2, Math.PI, 5)); // nose corner
  for (let i = N - 1; i >= 0; i--) sheet.push(GRIND[i]);                           // along the bevel's top to the heel
  for (const [u, , b] of HANDLE) sheet.push(P(u, b - TANG_OUT));                   // under the handle, back to the butt
  sheet.push(P(BUTT_U, (HANDLE[HANDLE.length - 1][1] + HANDLE[HANDLE.length - 1][2]) / 2));
  for (let i = HANDLE.length - 1; i >= 0; i--) sheet.push(P(HANDLE[i][0], HANDLE[i][1] + TANG_OUT)); // the tang's top = the spine
  const hole = [];
  for (let k = 0; k < 14; k++) { const a = (k / 14) * Math.PI * 2; hole.push(P(HOLE_U + Math.cos(a) * HOLE_R, HOLE_V + Math.sin(a) * HOLE_R)); }
  g.add(slab(sheet, SPINE_T * MM, STEEL, { holes: [hole] }));

  // ---------------------------------------------------------- the bevel: full sheet thickness at the grind line down to the
  // edge, with the honed edge along the bottom
  g.add(blade({
    spine: GRIND, edge: EDGE, n: N, thick: SPINE_T * MM, grind: 1, taper: 0, edgeThick: 0.0007,
    color: STEEL, edgeColor: BEVEL,
    bands: [{ from: 0, to: HONE_H / BEVEL_H, color: HONED }],
  }));

  // ---------------------------------------------------------- handle: two black POM scales round the tang
  g.add(loft(HANDLE.map(([u, t, b, w]) => section(u, t, b, w)), POM));
  // three stainless rivets through scales and tang, flush with the scales
  for (const u of RIVETS_U) {
    const st = HANDLE.findIndex((h) => h[0] < u), A = HANDLE[st - 1], B = HANDLE[st], f = (u - A[0]) / (B[0] - A[0]);
    const w = A[3] + (B[3] - A[3]) * f, mid = ((A[1] + A[2]) / 2) * (1 - f) + ((B[1] + B[2]) / 2) * f;
    g.add(pin(RIVET_R * MM, (2 * (w + 0.3) + 0.25) * MM, RIVET, 0, mid * MM, Z0 - u * MM, 10));
  }

  // the trail is drawn from the front of the edge (the nose's bottom corner): that corner leads the chop
  const front = EDGE[N - 1];
  g.userData.muzzle = new THREE.Vector3(0, front[1], front[0]);
  g.userData.len = (BLADE_L - BUTT_U) * MM; // ~0.288 = 11.3"
}
// a hat on the spine of the handle, over the middle of the grip
export const hatAt = [[0, SPINE_V * MM, 0.028], 0.05];
