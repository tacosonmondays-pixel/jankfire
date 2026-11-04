// Karambit skin: the Fox Knives FX-598 Karambit Fixed Blade (Fox Knives, Maniago, Italy), the full-tang fixed-blade
//   version of Fox's FX-599 folding karambit (the karambit Doug Marcaida demonstrates). A 6 cm hawkbill claw in 3 mm
//   Bohler N690Co with a black Idroglider coating (the honed edge shows bare steel), a swedge ground along the whole
//   spine, a small Spanish (sharpening) notch at the heel of the edge, a jimped thumb ramp on the spine and a jimped
//   finger guard. Full tang under contoured, textured black G10 scales with machined grooves, held by three Torx screws;
//   an enlarged finger ring at the tail.
//   The handle keeps the folder's curve: a folding karambit's handle has to swallow its own curved blade, so its belly
//   bulges (three shallow finger grooves in it) and its back sweeps up into the ring.
// Refs: Fox Knives FX-598 product page (blade 6 cm / 2.36", 3 mm thick, overall 17.5 cm / 6.89", 95 g, N690Co, G10);
//   Knifeguy "Fox Karambit Fixed Blade FX-598" (blade 5.99 cm, handle 11.48 cm, overall 17.47 cm; hawkbill with a
//   full-length swedge, small Spanish notch at the heel for sharpening, jimped thumb ramp and finger guard, textured G10
//   scales with relief, machined grooves, the karambit tail ring); Dream-Knives (handle 115 mm, the fixed version of the
//   FX-599 folder); KnifeCenter 02FX700 (2.36" N690 hawkbill, full-length swedge, jimped thumb ramp and finger guard,
//   textured G10 with relief and machined grooves, tail ring); Lamnia (6.89" overall, 2.36" blade, 0.12" thick, 3.35 oz);
//   kapesni-noze.cz (17.5 cm, 6 cm blade, 3 mm, 95 g); BladeHQ #88388 / Tamreen (handle 0.45" thick); sharg24 "FOX
//   Fixed Blade G10 Black Black Idroglider FX-598" (enlarged back ring); knivesandtools FX-599XT (the same claw: 6.3 cm
//   blade, 3 mm, and a 2.4 cm figure read as its height); Pinoy Built "Doug Marcaida Shows How To Use The 599 FOX
//   Karambit Knife". No source gives the ring size or the handle's height and curve: a 24 mm hole in a 36 mm ring, a
//   25-27 mm tall handle and the sweep (the ring's centre 6.5 mm above the front of the handle) are estimates.
// Held in the forward grip with the little finger through the ring: ring behind the fist (+Z), the claw in front of it
// curving down, the edge on the inside of the curve. Contract: userData.pivot = the ring's centre (on the Z axis); the
// spin animations turn the whole knife round it about X, so the ring's hole runs along X and is centred exactly there.
import { THREE, blade, slab, arc, resample, mat } from './kit.js';

const MM = 0.001;
const P = (p) => [p[0] * MM, p[1] * MM];
const clamp01 = (v) => Math.min(1, Math.max(0, v));

// ---------------------------------------------------------------- measurements (mm: z toward the ring, y up)
const RING_Z = 64, RING_RO = 18, RING_RI = 12;     // finger ring centre (= pivot, y = 0): 36 mm round, 24 mm hole
const HANDLE_T = 11.4;                            // 0.45" across the scales
const STEEL_T = 3.0;                              // 0.12" stock
const BEV = 0.9;                                  // the scales' rounded edges
const LINE = 0.3;                                 // the tang's edge stands this proud of the scales, all round
// the handle's centre line: level at the front of the scales, then sweeping up (ever steeper) into the ring
const ZF = -27, YF = -6.5;
const yc = (z) => { const s = clamp01((z - ZF) / (RING_Z - ZF)); return YF * (1 - s * s); };
// spine side: 12.3 mm above the centre line, rising into the ring through a fillet
const top = (z) => yc(z) + 12.3 + 3.4 * Math.pow(clamp01((z - 33) / 20), 2.2);
// finger side: 13 mm below it, a belly bulging between the guard and the ring, cut by three shallow finger grooves
// (index, middle and ring finger; the little finger goes through the ring)
const belly = (z) => 1.9 * Math.sin(Math.PI * clamp01((z + 20) / 72));
const groove = (z) => [39, 17, -5].reduce((a, zc) => a + 1.5 * Math.max(0, Math.cos((Math.PI * (z - zc)) / 20)) ** 2, 0);
const bot = (z) => yc(z) - 13 - belly(z) + groove(z);
// blade: the edge is an arc round C (radius RE) from the heel E0 to the point; the spine rides H(t) outside it and
// closes onto the point at TH_TIP. 67 mm of edge along the curve, the point 62 mm from the heel of the edge.
const DY = YF + 0.8;                              // the front of the knife sits this far below the ring's centre line
const E0 = [-38.5, -11.2 + DY];                   // heel of the edge, just in front of the sharpening notch
const H0 = 24;                                    // blade height at the heel (FX-599 claw: 2.4 cm)
const RE = 48, TH_TIP = (80 * Math.PI) / 180;     // the point faces 80 degrees down
const C = [E0[0], E0[1] - RE];
const Hof = (t) => H0 * (1 - Math.pow(t, 1.6));   // t = theta / TH_TIP: stays wide, then closes into a claw point

// ---------------------------------------------------------------- colours
const COAT = 0x2b2e34, COAT_BEVEL = 0x383c43, SWEDGE = 0x484d55, BARE = 0xd6dce3; // black Idroglider, bare honed edge
const G10 = 0x3b3d42, G10_GROOVE = 0x232529, SCREW = 0x6c727b;

// ---------------------------------------------------------------- 2D helpers (mm)
const areaSign = (pts) => { let a = 0; for (let i = 0; i < pts.length; i++) { const p = pts[i], q = pts[(i + 1) % pts.length]; a += p[0] * q[1] - q[0] * p[1]; } return a > 0 ? 1 : -1; };
const segNormal = (a, b, sgn) => { const dz = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dz, dy) || 1; return [(sgn * dy) / l, (-sgn * dz) / l]; };
// grow (d > 0) or shrink (d < 0) a closed outline
function offset(pts, d) {
  const n = pts.length, sgn = areaSign(pts);
  return pts.map((p, i) => {
    const n1 = segNormal(pts[(i - 1 + n) % n], p, sgn), n2 = segNormal(p, pts[(i + 1) % n], sgn);
    let mz = n1[0] + n2[0], my = n1[1] + n2[1];
    const ml = Math.hypot(mz, my) || 1; mz /= ml; my /= ml;
    const c = Math.max(0.5, mz * n1[0] + my * n1[1]);
    return [p[0] + (mz * d) / c, p[1] + (my * d) / c];
  });
}
const circle = (cz, cy, r, n) => arc(cz, cy, r, 0, Math.PI * 2 * (1 - 1 / n), n);
// jimping: `count` V-notches `depth` deep cut into the outline along a -> b (the steel lies on the (dy, -dz) side)
function jimping(a, b, count, depth, w = 0.45) {
  const dz = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dz, dy), u = [dz / L, dy / L], out = [];
  for (let k = 0; k < count; k++) {
    const t = (k + 0.5) / count, m = [a[0] + dz * t, a[1] + dy * t];
    out.push([m[0] - u[0] * w, m[1] - u[1] * w], [m[0] + u[1] * depth, m[1] - u[0] * depth], [m[0] + u[0] * w, m[1] + u[1] * w]);
  }
  return out;
}
// where a handle line y = f(z) runs into the ring's outer circle (between the grip and the ring's centre)
function meetRing(f) {
  const out = (z) => Math.hypot(z - RING_Z, f(z)) > RING_RO;
  let a = RING_Z - 30, b = RING_Z - 1;            // a: still outside the circle, b: inside it
  for (let i = 0; i < 40; i++) { const m = (a + b) / 2; if (out(m)) a = m; else b = m; }
  return [a, f(a)];
}

// ---------------------------------------------------------------- mesh helpers
const V = new THREE.Vector3(), W = new THREE.Vector3(), Nn = new THREE.Vector3();
function tri(out, a, b, c, ref) { // one triangle, its normal pointing away from ref
  V.set(b[0] - a[0], b[1] - a[1], b[2] - a[2]); W.set(c[0] - a[0], c[1] - a[1], c[2] - a[2]);
  Nn.crossVectors(V, W);
  const d = Nn.x * ((a[0] + b[0] + c[0]) / 3 - ref[0]) + Nn.y * ((a[1] + b[1] + c[1]) / 3 - ref[1]) + Nn.z * ((a[2] + b[2] + c[2]) / 3 - ref[2]);
  if (d < 0) out.push(...a, ...c, ...b); else out.push(...a, ...b, ...c);
}
function meshOf(pos, color) {
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.computeVertexNormals();
  return new THREE.Mesh(geo, mat(color));
}
// a band of wall w mm wide (across the knife) along a [z, y] polyline, segment i facing the 2D direction nrm(i)
function walls(pts, w, nrm, out) {
  for (let i = 0; i < pts.length - 1; i++) {
    const [z0, y0] = pts[i], [z1, y1] = pts[i + 1], n = nrm(i), x = (w / 2) * MM;
    const A = [x, y0 * MM, z0 * MM], B = [x, y1 * MM, z1 * MM], Cc = [-x, y1 * MM, z1 * MM], D = [-x, y0 * MM, z0 * MM];
    const ref = [0, ((y0 + y1) / 2 - n[1]) * MM, ((z0 + z1) / 2 - n[0]) * MM];
    tri(out, A, B, Cc, ref); tri(out, A, Cc, D, ref);
  }
  return out;
}
// flat convex shapes ([z, y] mm) lying on both faces of the handle (x = +-x0 mm): G10 grooves, screw heads
function decals(shapes, x0, color) {
  const pos = [];
  for (const sx of [1, -1]) for (const s of shapes) {
    const q = s.map(([z, y]) => [sx * x0 * MM, y * MM, z * MM]);
    for (let k = 1; k < q.length - 1; k++) tri(pos, q[0], q[k], q[k + 1], [0, q[0][1], q[0][2]]);
  }
  return meshOf(pos, color);
}
// finishes (tiger, camo, fade...) are textures: give every part side-on planar UVs so a wrap shows its pattern instead of
// one stretched texel. One tile is 8 cm, and v runs from the claw's point (0) to the top of the ring (~0.95), so a
// gradient like the fade covers the whole knife once
function sideUVs(g) {
  g.updateMatrixWorld(true);
  g.traverse((o) => {
    if (!o.isMesh) return;
    const pos = o.geometry.attributes.position, uv = new Float32Array(pos.count * 2);
    for (let i = 0; i < pos.count; i++) {
      V.fromBufferAttribute(pos, i).applyMatrix4(o.matrixWorld);
      uv[i * 2] = -V.z / 0.08; uv[i * 2 + 1] = (V.y + 0.058) / 0.08;
    }
    o.geometry.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  });
}

// ---------------------------------------------------------------- the outline (side view)
const [TZ, TY] = meetRing(top), [BZ, BY] = meetRing(bot);
// spine side of the handle, from the scales' front back to the ring
const TOP = [];
for (let z = ZF; z < TZ - 1.5; z += 4) TOP.push([z, top(z)]);
// finger side, from the ring forward to the root of the finger guard
const BOT = [];
for (let z = BZ - 1.5; z >= -15; z -= 3) BOT.push([z, bot(z)]);
// round the back of the ring, from where the spine side runs into it to where the finger side does
const RING_ARC = arc(RING_Z, 0, RING_RO, Math.atan2(TY, TZ - RING_Z), Math.atan2(BY, BZ - RING_Z), 14);
// finger guard: its root, back to its tip, then its front up to the notch (relative to the knife's front)
const GUARD = [[-18, -15.4], [-22, -16.7], [-25.5, -18.1], [-28.3, -19.0], [-30.8, -19.1]].map(([z, y]) => [z, y + DY]);
const GUARD_FRONT = [[-34.2, -16.6], [-35.0, -14.4], [-35.2, -12.4]].map(([z, y]) => [z, y + DY]);

function bladeLines(n = 40) {
  const spine = [], edge = [];
  for (let i = 0; i < n; i++) {
    const t = i / (n - 1), th = t * TH_TIP, rs = RE + Hof(t);
    edge.push([C[0] - RE * Math.sin(th), C[1] + RE * Math.cos(th)]);
    spine.push([C[0] - rs * Math.sin(th), C[1] + rs * Math.cos(th)]);
  }
  spine[n - 1] = edge[n - 1].slice();
  return { spine, edge };
}

export function build(g) {
  const { spine, edge } = bladeLines();
  const S0 = spine[0];

  // ---------------------------------------------------------- the steel: one piece from the point to the ring
  const ramp = jimping([S0[0] + 0.6, S0[1]], TOP[0], 6, 0.75);    // thumb ramp on the spine
  const guardJimp = jimping(GUARD[GUARD.length - 1], GUARD_FRONT[0], 3, 0.55, 0.4);
  const notch = arc(E0[0] + 1.5, E0[1], 1.5, 0, Math.PI, 6);       // sharpening notch, guard side to edge side
  const front = [...GUARD.slice(1), ...guardJimp, ...GUARD_FRONT, ...notch];
  const outline = [S0, ...ramp, ...TOP, ...RING_ARC, ...BOT, GUARD[0], ...front]; // the whole tang's perimeter
  // the steel in front of the scales (ricasso, thumb ramp, finger guard): its back edge hides inside the scales...
  g.add(slab([S0, ...ramp, TOP[0], TOP[1], ...front].map(P), STEEL_T * MM, COAT));
  // ...and the tang's edge, showing between the scales all round the handle and inside the ring
  const sgn = areaSign(outline), run = [...TOP.slice(1), ...RING_ARC, ...BOT, GUARD[0], GUARD[1]];
  const hole = circle(RING_Z, 0, RING_RI - LINE, 14); hole.push(hole[0]);
  const edges = walls(run, STEEL_T, (i) => segNormal(run[i], run[i + 1], sgn), []);
  walls(hole, STEEL_T, (i) => { const m = [(hole[i][0] + hole[i + 1][0]) / 2 - RING_Z, (hole[i][1] + hole[i + 1][1]) / 2], l = Math.hypot(m[0], m[1]); return [-m[0] / l, -m[1] / l]; }, edges);
  g.add(meshOf(edges, COAT));

  // ---------------------------------------------------------- G10 scales (one slab right across the tang)
  const f = (z, y) => [z, y + DY];                                  // the scales' front edge, relative to the knife's front
  const scaleOut = [[ZF + 0.8, top(ZF + 0.8) - 0.1], ...TOP.slice(1), ...RING_ARC, ...BOT, ...GUARD.slice(0, 4),
    f(-29.8, -18.0), f(-29.0, -14.5), f(-27.9, -6), f(-27.2, 3), f(-26.6, 9)];
  g.add(slab(offset(scaleOut, -(BEV + LINE)).map(P), (HANDLE_T - 2 * BEV) * MM, G10,
    { bevel: BEV * MM, holes: [circle(RING_Z, 0, RING_RI + BEV, 14).map(P)] }));
  // machined grooves in the G10 (two pairs, slanted, between the screws), then the three Torx screw heads
  const across = (z, inset0, inset1) => { // a 1.4 mm groove leaning forward, centred on z at mid-height
    const y0 = bot(z) + inset0, y1 = top(z) - inset1, ym = (y0 + y1) / 2, k = (y) => (y - ym) * 0.28;
    return [[z - 0.7 + k(y0), y0], [z + 0.7 + k(y0), y0], [z + 0.7 + k(y1), y1], [z - 0.7 + k(y1), y1]];
  };
  g.add(decals([across(-4, 4.2, 4.8), across(1.5, 4.3, 4.9), across(25, 4.1, 4.7), across(30.5, 4.2, 4.6)], HANDLE_T / 2 + 0.12, G10_GROOVE));
  g.add(decals([-16, 14, 42].map((z) => circle(z, (top(z) + bot(z)) / 2 + 0.3, 2.3, 8)), HANDLE_T / 2 + 0.15, SCREW));

  // ---------------------------------------------------------- the blade: flat ground, coated, swedge along the spine
  const N = 24;
  const Sr = resample(spine, N), Er = resample(edge, N);
  const hAt = (k) => Math.hypot(Sr[k][0] - Er[k][0], Sr[k][1] - Er[k][1]);
  const hgt = (s) => { const fi = s * (N - 1), i = Math.min(N - 2, Math.floor(fi)), t = fi - i; return Math.max(0.05, hAt(i) + (hAt(i + 1) - hAt(i)) * t); };
  g.add(blade({
    spine: spine.map(P), edge: edge.map(P), n: N, thick: STEEL_T * MM, grind: 0.5, taper: 0.4, edgeThick: 0.0004,
    color: COAT, edgeColor: COAT_BEVEL,
    bands: [
      { from: 0, to: (s) => Math.min(0.45, 1.8 / hgt(s)), color: BARE },                       // the honed edge, ~1.8 mm
      { from: (s) => Math.max(0.55, 1 - 2.4 / hgt(s)), to: 1, color: SWEDGE, s0: 0.04, s1: 1 }, // the swedge, ~2.4 mm
    ],
  }));

  sideUVs(g);
  g.userData.pivot = new THREE.Vector3(0, 0, RING_Z * MM);
  const tip = edge[edge.length - 1];
  g.userData.muzzle = new THREE.Vector3(0, tip[1] * MM, tip[0] * MM);
  let zmin = 0; for (const p of spine) zmin = Math.min(zmin, p[0]);
  g.userData.len = (RING_Z + RING_RO - zmin) * MM;  // ring to the front of the claw
}
// a hat on the spine of the handle, over the middle of the grip
export const hatAt = [[0, top(12) * MM, 0.012], 0.042];
