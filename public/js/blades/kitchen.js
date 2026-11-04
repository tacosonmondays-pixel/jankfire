// Kitchen knife skin: the Wüsthof Classic 8" (20 cm) Chef's Knife (4582/20, now 1040100120), the archetypal
// forged German chef's knife.
//   Blade 200 mm, 47 mm tall at the heel, spine 3 mm at the heel with a distal taper toward the tip; a full flat grind
//   with a narrow sharpened bevel (~14 degrees a side) along the edge. German profile: a straight spine that drops
//   into the point over the last half, a short flat at the heel, then one long continuous belly rising into a point
//   that sits about a third of the blade height below the spine (just below the grip axis).
//   Forged full bolster flush with the spine, its finger guard running all the way down to the heel of the edge.
//   Full tang: the steel shows along the top and the bottom of the handle and round the butt, between two black POM
//   scales held by three stainless rivets. The handle is 130 mm with the bolster, the bottom flaring a little at the butt.
// Refs: Wüsthof product page (Classic 8" Chef's Knife, 1040100120: 8" blade, 1.9" wide, forged, full bolster,
//   triple-riveted synthetic handle, 58 HRC); Cutlery and More listing (blade 8" / 200 mm, height 1.9" / 47 mm,
//   handle 5.1" / 130 mm, overall 13.2" / 335 mm, spine 3 mm, 9.3 oz, triple-riveted POM, full tang, ~14 degree
//   edge); Best Buy listing (47 mm / 130 mm / 335 mm / 3 mm spine, full bolster and finger guard); Knife Merchant
//   (spine 2.9 mm); TechGearLab review (measured spine 2.6 mm, 9.1 oz); Wikipedia "Chef's knife" (German profile:
//   deeper, continuous curve along the whole edge; fully forged blade, bolster and tang from one piece of steel).
// Held like every knife: the handle centred on the grip axis (y = 0) and the hand (z -0.036 .. +0.08); the spine runs
// flush along the top of the handle, so the heel hangs ~23 mm below the handle and the knuckles clear the board.
// Edge down, tip to -Z. No moving parts.
import { THREE, blade, slab, pin, resample, mat } from './kit.js';

const MM = 0.001;
// ---------------------------------------------------------------- measurements (mm)
// u = mm in front of the bolster's back face (toward the tip), v = mm above the grip axis
const Z_BACK = -0.036;                   // the bolster's back face = front of the handle scales
const SPINE_V = 12;                      // the spine line = the top of the handle (full tang, flush)
const BLADE_H = 47;                      // spine to edge at the heel
const EDGE_V = SPINE_V - BLADE_H;        // -35: the heel of the edge, 23 mm below the handle
const SPINE_T = 3.0;                     // spine thickness at the heel
const BOLSTER_L = 16;                    // bolster along the spine (130 mm handle - 114 mm scales)
const HEEL_U = 20.2;                     // the edge leaves the finger guard here
const TIP_U = HEEL_U + 199.3;            // ~200 mm of edge
const TIP_V = -3;                        // the point: 15 mm below the spine, 32 mm above the edge line
const FLAT = 40, DROP0 = 95;             // the edge is flat for 40 mm; the spine starts to drop 95 mm from the heel
const N = 30;                            // blade stations

// ---------------------------------------------------------------- colours
const STEEL = 0xd2d8df, STEEL_SPINE = 0xbac1ca, EDGE_BRIGHT = 0xf1f4f7; // satin X50CrMoV15, the honed edge
const BOLSTER = 0xdde2e8, TANG = 0xb3bac3, RIVET = 0xe2e6eb;
const POM = 0x1f2023;                    // black polyoxymethylene scales

const P = (u, v) => [Z_BACK - u * MM, v * MM]; // side view point [z, y]
const V3 = (x, u, v) => [x * MM, v * MM, Z_BACK - u * MM]; // model point from mm

// ---------------------------------------------------------------- a closed solid through cross-section loops
// loops: arrays of [x, y, z] (same count each). Consecutive loops are joined; the first and last get flat caps.
// Faces are turned to point away from the middle of the loops they join (fine for convex sections).
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

// ---------------------------------------------------------------- blade outline
const L = TIP_U - HEEL_U;
const RISE = TIP_V - EDGE_V, DROP = SPINE_V - TIP_V;
const rise = (s) => (s <= FLAT ? 0 : RISE * Math.pow((s - FLAT) / (L - FLAT), 2.5)); // the belly
const drop = (s) => (s <= DROP0 ? 0 : DROP * Math.pow((s - DROP0) / (L - DROP0), 2.0)); // the spine into the point

// ---------------------------------------------------------------- bolster + finger guard (side view, mm)
// back: the handle face (u = 0) down to the bottom of the handle, then the finger guard rounds down and forward to the
// heel (a quarter ellipse), meeting the edge line so the guard bottoms out exactly at the edge
const guardBack = (v) => (v >= -12 ? 0 : HEEL_U - HEEL_U * Math.sqrt(Math.max(0, 1 - ((v + 12) / (EDGE_V + 12)) ** 2)));
// front: where the bolster runs out into the blade, sweeping forward a little to the heel
const PLUNGE = [[SPINE_V, BOLSTER_L], [0, 16.3], [-12, 17.0], [-24, 18.2], [-31, 19.4], [EDGE_V, HEEL_U]];
const guardFront = (v) => {
  for (let i = 0; i < PLUNGE.length - 1; i++) {
    const [va, ua] = PLUNGE[i], [vb, ub] = PLUNGE[i + 1];
    if (v <= va && v >= vb) return ua + (ub - ua) * ((va - v) / (va - vb));
  }
  return v > SPINE_V ? BOLSTER_L : HEEL_U;
};
// half thickness at the back of each row: the full bolster in the handle's height, thinning down the guard
const guardHalf = (v) => (v >= -12 ? 6.3 : 0.7 + 5.6 * Math.sqrt(Math.max(0, (v - EDGE_V) / (-12 - EDGE_V))));
// the blade's half thickness at height v at the heel (full flat grind: 1.5 mm at the spine, 0.25 at the edge)
const bladeHalf = (v) => 0.25 + (SPINE_T / 2 - 0.25) * Math.max(0, (v - EDGE_V) / BLADE_H);

// ---------------------------------------------------------------- handle (stations from the bolster to the butt, mm)
//   u, top, bottom, half width
const HANDLE = [
  [0, 12.0, -12.0, 6.6],
  [-5, 12.0, -12.0, 7.6],
  [-13, 12.0, -12.0, 8.1],
  [-24, 12.0, -12.0, 8.25],
  [-45, 12.0, -12.05, 8.25],
  [-66, 12.0, -12.2, 8.25],
  [-84, 12.0, -12.7, 8.25],
  [-96, 11.95, -13.6, 8.2],
  [-103, 11.4, -14.4, 8.0],
  [-108.5, 9.6, -14.3, 7.6],
  [-112.3, 6.4, -12.4, 6.8],
  [-114.6, 2.4, -8.6, 5.4],
  [-115.5, -1.6, -4.4, 3.2],
];
const RIVETS_U = [-20, -56.5, -93], RIVET_R = 3.0;
const TANG_OUT = 0.25; // the tang stands this much proud of the scales so its steel shows

// a rounded-rectangle section: flat top/bottom (where the tang shows), round corners, flat sides
function section(u, top, bot, w) {
  const a = Math.min(1.9, w * 0.5), r = Math.min(4.6, (top - bot) * 0.38), cx = a + (w - a) * 0.707, cy = r * 0.293;
  const pts = [[a, top], [cx, top - cy], [w, top - r], [w, bot + r], [cx, bot + cy], [a, bot]];
  const loop = pts.map(([x, v]) => V3(x, u, v));
  for (let i = pts.length - 1; i >= 0; i--) loop.push(V3(-pts[i][0], u, pts[i][1]));
  return loop;
}

export function build(g) {
  // ---------------------------------------------------------- blade: full flat grind, distal taper, honed edge bevel
  const spine = [], edge = [];
  for (let k = 0; k <= 48; k++) {
    const s = L * (1 - (1 - k / 48) ** 1.35); // denser toward the point
    spine.push(P(HEEL_U + s, SPINE_V - drop(s)));
    edge.push(P(HEEL_U + s, EDGE_V + rise(s)));
  }
  // both start one station back, inside the bolster (the edge climbing into the guard), so station 1 is exactly the heel
  const len = (pts) => pts.reduce((a, p, i) => (i ? a + Math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1]) : 0), 0);
  const ds = len(spine) / (N - 2) / MM, de = len(edge) / (N - 2) / MM; // mm
  spine.unshift(P(HEEL_U - ds, SPINE_V));
  edge.unshift(P(HEEL_U - de * 0.92, EDGE_V + de * 0.39));
  const S = resample(spine, N), E = resample(edge, N);
  const at = (s, arr) => { const f = s * (N - 1), i = Math.min(N - 2, Math.floor(f)), t = f - i; return arr[i] + (arr[i + 1] - arr[i]) * t; };
  const sy = S.map((p) => p[1]), ey = E.map((p) => p[1]);
  const hgt = (s) => Math.max(1e-4, at(s, sy) - at(s, ey));
  const sOf = (u) => { // station fraction where the edge passes u
    for (let i = 0; i < N - 1; i++) if ((Z_BACK - E[i + 1][0]) / MM >= u) return (i + ((u - (Z_BACK - E[i][0]) / MM) / ((E[i][0] - E[i + 1][0]) / MM))) / (N - 1);
    return 1;
  };
  g.add(blade({
    spine, edge, n: N, thick: SPINE_T * MM, grind: 1, taper: 0.66, edgeThick: 0.0005,
    color: STEEL_SPINE, edgeColor: STEEL,
    bands: [{ from: 0, to: (s) => Math.min(0.5, (1.3 * MM) / hgt(s)), color: EDGE_BRIGHT, s0: sOf(HEEL_U), s1: 1 }],
  }));

  // ---------------------------------------------------------- forged bolster + finger guard: horizontal slices, thick at
  // the back, running out into the blade at the front
  const rows = [SPINE_V + 0.12, SPINE_V - 0.9, 8, 2, -5, -12, -17, -22, -26.5, -30, -32.8, EDGE_V + 0.15];
  const cols = [0, 0.18, 0.36, 0.54, 0.72, 0.87, 1];
  const bol = rows.map((v, k) => {
    const ub = guardBack(v), uf = guardFront(v), hb = guardHalf(v), hf = bladeHalf(v) + 0.22;
    const shoulder = k === 0 ? 0.72 : k === 1 ? 0.94 : 1; // round the top edges over a little
    // an S: parallel with the handle at the back, flowing out tangent into the blade at the front
    const side = cols.map((f) => [hf + (hb - hf) * (1 - f * f * (3 - 2 * f)) * shoulder, ub + (uf - ub) * f]);
    const loop = side.map(([h, u]) => V3(h, u, v));
    for (let i = side.length - 1; i >= 0; i--) loop.push(V3(-side[i][0], side[i][1], v));
    return loop;
  });
  g.add(loft(bol, BOLSTER));

  // ---------------------------------------------------------- handle: two black POM scales round the full tang
  g.add(loft(HANDLE.map(([u, t, b, w]) => section(u, t, b, w)), POM));
  // the tang: a 3 mm steel plate the shape of the handle, standing a hair proud along the top, the bottom and the butt
  const out = [];
  for (const [u, t] of HANDLE) out.push(P(u, t + TANG_OUT));
  const [ue, te, be] = HANDLE[HANDLE.length - 1];
  out.push(P(ue - TANG_OUT, (te + be) / 2));
  for (let i = HANDLE.length - 1; i >= 0; i--) out.push(P(HANDLE[i][0], HANDLE[i][2] - TANG_OUT));
  g.add(slab(out, SPINE_T * MM, TANG));
  // three stainless rivets, flush with the scales
  for (const u of RIVETS_U) {
    const st = HANDLE.findIndex((h) => h[0] < u), [u0, , , w0] = HANDLE[st - 1], [u1, , , w1] = HANDLE[st];
    const w = w0 + (w1 - w0) * ((u - u0) / (u1 - u0));
    g.add(pin(RIVET_R * MM, (2 * w + 0.3) * MM, RIVET, 0, 0, Z_BACK - u * MM, 10));
  }

  g.userData.muzzle = new THREE.Vector3(0, TIP_V * MM, Z_BACK - TIP_U * MM);
  g.userData.len = (TIP_U - HANDLE[HANDLE.length - 1][0] + TANG_OUT) * MM; // ~0.335 = 13.2"
}
// a hat on the spine of the handle, over the middle of the grip
export const hatAt = [[0, (SPINE_V + TANG_OUT) * MM, 0.03], 0.05];
