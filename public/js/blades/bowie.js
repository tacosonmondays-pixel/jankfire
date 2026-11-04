// Bowie skin: the Randall Made Model 12 9" Sportsman's Bowie (Randall Made Knives, Orlando, Florida), in stacked leather
//   and brass. A 9" (228.6 mm) clip-point blade of 1/4" stock, 1-3/4" deep at the hilt, hollow ground, with a short square
//   ricasso and a curved plunge. The long, slightly dished clip is ground as a swedge and sharpened for the last 3-3/4".
//   The hilt is the solid brass "lugged" double hilt: a straight crossguard with a lug turned forward at each end.
//   Oval stacked-leather washer handle, slim at the hilt and swelling toward the butt, closed by a domed brass butt cap.
//   14" overall.
// Refs: Randall Made Knives, "Model 12 - 9" Sportsman Bowie" (9" blade of 1/4" stock, 1-5/8" wide, top cutting edge
//   sharpened approx. 3-3/4", brass lugged hilt, approx. 5" leather handle) and "Extra Features" (lugged hilt = solid brass
//   double hilt with a lug extending forward at each end, standard on the Model 12 9"/11"/13"); A.G. Russell listings
//   (Model 12 Sportsman Bowie with leather handle: 9" blade, stacked leather, brass hilt, brass butt cap, 14" overall;
//   black micarta version: 5" handle, 14" overall, 1 lb 3.4 oz, 440B stainless); Arizona Custom Knives #1112407 (a measured
//   12-9: 14.5" overall, blade stock .231", blade depth 1.784"); the 1954 Randall catalog entry quoted in the BladeForums
//   "Model 12 Smithsonian Bowie" thread (3-1/2" guard on the 11" Bowie with a 2-1/2" blade: used to scale this guard).
// The blade is built here instead of with kit.blade(): it needs a real ground swedge along the clip and a two-facet hollow
// grind, so its cross-section is spine / swedge line / flat / grind line / hollow / edge. Held like every knife: the leather
// centred on the hand, the hilt just in front of the fist, edge down, tip to -Z. No moving parts.
import { THREE, mat, slab, lathe, curve } from './kit.js';

const MM = 0.001, IN = 25.4; // lengths below are in mm
// ---------------------------------------------------------------- measurements
const BLADE_L = 9 * IN;                 // 228.6, hilt face to point
const SPINE_Y = 22.0, EDGE_Y = -22.5;   // 44.5 deep at the hilt (1-5/8" nominal, 1.784" measured), about centred on the tang
const TIP_Y = 1.5;                      // the point sits just above the handle axis
const THICK = 6.0;                      // 1/4" stock (.231" measured)
const TAPER = 0.3;                      // distal taper toward the point
const CLIP_U = 124;                     // the clip starts ~4-1/8" back from the point...
const SHARP_U = BLADE_L - 3.75 * IN;    // ...and its swedge is sharpened for the last 3-3/4"
const SWEDGE = 6.0;                     // height of the swedge bevel
const RIC_U = 10, PLUNGE_U = 21;        // square ricasso (where the stamp goes), then a curved plunge into the hollow grind
const GRIND = 0.58;                     // top of the hollow grind, as a fraction of the height above the edge
const EDGE_T = 0, FALSE_T = 0;          // both edges come to a true edge (a flat strip there shows as a dotted line)
const HILT_T = 7.5, HILT_W = 11, BV = 0.9; // lugged hilt: bar 7.5 thick, 11 across, edges rounded 0.9; 3" tip to tip
const LEATHER_L = 4 * IN;               // 101.6 of stacked washers
const WASHERS = 16;
const CAP_L = 21;                       // domed brass butt cap
const Z_HB = -0.030;                    // the hilt's back face, just in front of the index finger
const Z_HF = Z_HB - HILT_T * MM;        // its front face: the blade is measured from here
const Z_TIP = Z_HF - BLADE_L * MM;
const Z_L1 = Z_HB + LEATHER_L * MM;     // end of the leather / start of the butt cap
const Z_END = Z_L1 + CAP_L * MM;

// ---------------------------------------------------------------- colours
const STEEL = 0xb3bbc5, BEVEL = 0xe3e8ed;  // satin 440B flats, the polished hollow and swedge brighter
const BRASS = 0xd2a54b;
const LEATHER = [0x8a5330, 0x9a6139, 0x76442a]; // washers vary a little in tone
const STACK = [0, 1, 0, 2, 1, 0, 2, 0, 1, 2, 0, 1, 0, 2, 1, 0];

// ---------------------------------------------------------------- helpers
const smooth = (a, b, x) => { const t = Math.max(0, Math.min(1, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
// y at u on a polyline of [u, y] sorted by u
const along = (pts) => (u) => {
  if (u <= pts[0][0]) return pts[0][1];
  for (let i = 1; i < pts.length; i++) if (u <= pts[i][0]) { const [u0, y0] = pts[i - 1], [u1, y1] = pts[i]; return y0 + ((y1 - y0) * (u - u0)) / (u1 - u0 || 1); }
  return pts[pts.length - 1][1];
};
// one triangle, wound so its normal points away from ref (a point inside the part)
const V = new THREE.Vector3(), W = new THREE.Vector3(), N = new THREE.Vector3();
function tri(out, a, b, c, ref) {
  V.set(b[0] - a[0], b[1] - a[1], b[2] - a[2]); W.set(c[0] - a[0], c[1] - a[1], c[2] - a[2]);
  N.crossVectors(V, W);
  if (N.lengthSq() < 1e-16) return;
  const d = N.x * ((a[0] + b[0] + c[0]) / 3 - ref[0]) + N.y * ((a[1] + b[1] + c[1]) / 3 - ref[1]) + N.z * ((a[2] + b[2] + c[2]) / 3 - ref[2]);
  if (d < 0) out.push(...a, ...c, ...b); else out.push(...a, ...b, ...c);
}
// a mesh from per-material triangle lists
function meshOf(lists, colors) {
  const pos = [], geo = new THREE.BufferGeometry();
  let at = 0;
  lists.forEach((l, k) => { pos.push(...l); geo.addGroup(at, l.length / 3, k); at += l.length / 3; });
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.computeVertexNormals();
  return new THREE.Mesh(geo, colors.map((c) => mat(c)));
}

// ---------------------------------------------------------------- blade outline (side view, u = mm ahead of the hilt face)
// spine: straight, then the long clip, rounding in and slightly dished, down to the point
const spineY = along([[-3, SPINE_Y], ...curve([[CLIP_U - 20, SPINE_Y], [CLIP_U, SPINE_Y], [CLIP_U + 12, 20.4], [CLIP_U + 30, 15.5],
  [CLIP_U + 50, 10.5], [CLIP_U + 70, 6.8], [CLIP_U + 88, 3.9], [BLADE_L, TIP_Y]], 40)]);
// edge: straight, then a long belly sweeping up into the point
const edgeY = along([[-3, EDGE_Y], ...curve([[96, EDGE_Y], [110, EDGE_Y], [130, -22.0], [150, -20.6], [170, -18.0], [188, -14.4],
  [203, -10.0], [215, -5.2], [223, -1.6], [BLADE_L, TIP_Y]], 48)]);

// cross-section at u: S+ S- (spine) W+ W- (swedge line) G+ G- (grind line) H+ H- (hollow) E+ E- (edge)
function section(u) {
  const ys = spineY(u), ye = edgeY(u), h = Math.max(0, ys - ye);
  const half = Math.min((THICK / 2) * (1 - (TAPER * Math.max(0, u)) / BLADE_L), 0.07 * h); // the bevels close it up at the point
  const p = smooth(RIC_U, PLUNGE_U, u);                      // 0 = square ricasso, 1 = ground
  const e = Math.min(half, half + (EDGE_T / 2 - half) * p);
  const gv = GRIND * p;
  const ts = Math.min(half, half + (FALSE_T / 2 - half) * smooth(CLIP_U, SHARP_U + 2, u)); // the swedge thins the spine to an edge
  const sw = Math.min(SWEDGE * smooth(CLIP_U, CLIP_U + 12, u), 0.9 * (1 - gv) * h);
  const hx = e + (half - e) * 0.25;                          // hollow: the lower facet is dished in
  const z = Z_HF - u * MM, yg = ye + gv * h, yh = ye + gv * 0.42 * h;
  const q = (x, y) => [x * MM, y * MM, z];
  return { ref: [0, ((ys + ye) / 2) * MM, z], p: [q(ts, ys), q(-ts, ys), q(half, ys - sw), q(-half, ys - sw), q(half, yg), q(-half, yg), q(hx, yh), q(-hx, yh), q(e, ye), q(-e, ye)] };
}

function buildBlade() {
  const us = [-3, RIC_U, 13, 16, 18.5, PLUNGE_U, 45, 75, 100, 110, 116, 121, CLIP_U, 128, 132, 136];
  for (let u = 142; u < BLADE_L - 2; u += 6.2) us.push(u);
  us.push(BLADE_L);
  const R = us.map(section);
  const flat = [], bev = [];
  const strips = [[0, 1, flat], [0, 2, bev], [1, 3, bev], [2, 4, flat], [3, 5, flat], [4, 6, bev], [5, 7, bev], [6, 8, bev], [7, 9, bev], [8, 9, flat]];
  for (let i = 0; i < R.length - 1; i++) {
    const A = R[i].p, B = R[i + 1].p, ref = [0, (R[i].ref[1] + R[i + 1].ref[1]) / 2, (R[i].ref[2] + R[i + 1].ref[2]) / 2];
    for (const [a, b, out] of strips) { tri(out, A[a], A[b], B[b], ref); tri(out, A[a], B[b], B[a], ref); }
  }
  return meshOf([flat, bev], [STEEL, BEVEL]); // the heel sits inside the hilt: no cap
}

// ---------------------------------------------------------------- lugged hilt (side view outline, inset by the rounding)
function buildHilt() {
  // upper half: [mm behind the front face, mm up]; front face, the lug's underside, its rounded nose, the top, the back corner
  const up = [[BV, 25.2], [-0.4, 26.3], [-2.6, 27.0], [-4.9, 27.5], [-6.5, 29.0], [-7.3, 31.1], [-7.2, 33.3], [-6.2, 35.2], [-4.3, 36.5],
    [-1.6, 37.2], [2.6, 37.2], [5.3, 36.5], [HILT_T - BV, 34.8]];
  const pts = [...up, ...up.slice().reverse().map(([z, y]) => [z, -y])].map(([z, y]) => [Z_HF + z * MM, y * MM]);
  return slab(pts, (HILT_W - 2 * BV) * MM, BRASS, { bevel: BV * MM });
}

// ---------------------------------------------------------------- stacked leather handle: oval washers, swelling to the butt
const SX = 0.77; // width / height of the oval
const rOf = along(curve([[0, 14.4], [0.1, 14.2], [0.3, 15.0], [0.55, 16.2], [0.78, 16.7], [0.92, 16.5], [1, 16.2]], 24)); // half height, mm
function buildLeather(segs = 8) {
  const lists = LEATHER.map(() => []);
  const ringAt = (t) => {
    const z = Z_HB - 0.5 * MM + (LEATHER_L + 1) * MM * t, r = rOf(t) * MM, out = [];
    for (let j = 0; j < segs; j++) { const a = (j / segs) * Math.PI * 2; out.push([SX * r * Math.sin(a), -r * Math.cos(a), z]); }
    return out;
  };
  let A = ringAt(0);
  // the front face, against the hilt (wider than the brass bar, so it shows round it)
  for (let j = 1; j < segs - 1; j++) tri(lists[0], A[0], A[j], A[j + 1], [0, 0, A[0][2] + 0.01]);
  for (let k = 0; k < WASHERS; k++) {
    const B = ringAt((k + 1) / WASHERS), out = lists[STACK[k % STACK.length]], ref = [0, 0, (A[0][2] + B[0][2]) / 2];
    for (let j = 0; j < segs; j++) { const j2 = (j + 1) % segs; tri(out, A[j], B[j], B[j2], ref); tri(out, A[j], B[j2], A[j2], ref); }
    A = B;
  }
  return meshOf(lists, LEATHER);
}

export function build(g) {
  g.add(buildBlade());
  g.add(buildHilt());
  g.add(buildLeather());
  // domed brass butt cap, tucked a hair under the last washer
  const z0 = Z_L1 - 0.5 * MM, r0 = rOf(1);
  g.add(lathe([[r0 - 0.3, 0], [r0 + 0.4, 2.5], [r0 + 0.7, 7], [r0 + 0.4, 12], [r0 - 0.8, 16], [r0 - 3.6, 19], [r0 - 8.2, 20.8], [0, CAP_L + 0.5]]
    .map(([r, z]) => [r * MM, z0 + z * MM]), BRASS, { segs: 8, sx: SX }));

  g.userData.muzzle = new THREE.Vector3(0, TIP_Y * MM, Z_TIP);
  g.userData.len = Z_END - Z_TIP; // 0.358 = 14.1"
}
// a hat on the leather, just behind the middle of the grip
export const hatAt = [[0, 0.0163, 0.03], 0.05];
