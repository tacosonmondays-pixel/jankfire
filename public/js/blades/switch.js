// Switchblade skin: the classic Italian stiletto, 23 cm (9") class, side opening, as made in Maniago (Frank Beltrame, AKC,
//   Latama...). A slim 4" bayonet blade, 13 mm deep and 3 mm thick, with a long top swedge (an unsharpened false edge ground
//   from the point back past the middle of the blade), a short square ricasso with a little notch where the edge starts and
//   a half-height grind. Nickel-silver bolsters front and back: the front one carries the small guard ears top and bottom,
//   the pivot pin and the push button; on the button side it is the swivel bolster, its top ear the thumb tab that swings
//   to unlock the blade for closing. Domed Brazilian horn scales on brass liners, the steel backspring showing along the
//   back, a rounded butt coming to a soft point. 227 mm open, 124.5 mm shut, the handle 17.4 mm deep and 16.4 mm thick
//   (17.7 mm over the button, which is how the dealers below measure "handle thickness").
// Refs: Tactical Elements, Frank Beltrame 9" Italian Stiletto Automatic Bayonet (9.00" overall, 4.00" blade, 4.875" closed);
//   PVK, Frank B Italian Stiletto 9" Bayonet (23 cm): 8.90" overall, 4.91" closed, 0.145" blade, push-button side opening
//   with a swivel bolster; Grindworx, Frank B 9" honey horn (4" blade, 3.5" cutting edge, 0.11" thick, handle 0.68" thick);
//   BladeHQ, AKC Swinguard 9" and Frank B 9" listings (3.875-4" blade, 0.50-0.55" wide, 0.10-0.12" thick, handle 4.95-5.125"
//   long, 0.70-0.75" wide, 0.69-0.75" thick, nickel-silver bolsters); Tactical Elements / PVK, Latama 23 cm Classic (9" overall,
//   4" blade, 4.875" handle, solid nickel-silver bolsters, 1-1.2 mm brass liners, brass pins, 5 mm backspring); All About
//   Pocket Knives, Frank Beltrame 23 cm bayonet listings (4 mm kick spring, 4 mm backspring, 3 mm blade tang), a Renzo
//   Beltrame swivel-bolster stiletto ("released to close by pushing down the guard on the top bolster with your thumb") and
//   the "bolster button" Italian stilettos; the AAPK forum note that on post-1960s stilettos the button sits right up against
//   the front bolster; kapesni-noze.cz, original stiletto 23 cm (23 cm overall, 9.5 cm blade); Sharg24, Frank Beltrame Switch
//   Bayonet 23 cm FB 23/37TB and FB 23/36B (230 mm overall, 98-98.6 mm blade, 2.8-3.05 mm thick, 121 mm handle, handle
//   17.8 mm thick); baterky-noze.sk, Frank Beltrame stiletto 23 cm (125 mm closed, handle 18 mm thick); PVK, Frank Beltrame
//   28 cm (open and locked, you pivot the top bolster outward to unlock the blade, then close it).
// Moving part: userData.flipBlade, a group on the pivot pin in the front bolster, holds the blade (tip to -Z). The game
// sets its rotation.x: 0 = open, PI = shut. Shut, the blade lies in the 4 mm slot between the liners, edge up under the
// backspring, spine down along the open belly of the handle, point 6 mm short of the butt. The group sits inside a y-mirror
// and holds the blade inside another one: the two mirrors cancel out (the blade renders as modelled) but turn the game's
// PI -> 0 sweep around, so the blade swings out of the belly slot spine first, like the real knife, not up through the spring.
import { THREE, mat, slab, pin, curve } from './kit.js';

const MM = 0.001;
// ---------------------------------------------------------------- measurements (mm)
const CLOSED_L = 124.5;               // front bolster face to butt (4.875" - 4.91")
const BLADE_L = 102.5;                // front bolster face to point (4")
const PIV_U = 8;                      // pivot pin, behind the bolster face
const Z_F = -42;                      // front bolster face: the guard ears sit just in front of the index finger
const Z_P = Z_F + PIV_U;              // -34
const YC = 1.0;                       // handle centre line; the pivot sits 1 mm below it, on y = 0 (the grip axis)
const HH = 8.7;                       // half height of the handle: 17.4 mm (0.68")
const SLOT = 2.0, LINER = 1.2, OUT = 8.2; // half slot (blade 3 mm in a 4 mm slot), brass liners, outside of scales / bolsters (16.4 mm)
const SPRING_Y0 = 5.9;                // underside of the backspring (model y); the shut blade's edge stops 0.4 below it
// rounding of the parts' edges: [across the knife, in the side view, segments]. The horn scales are domed.
const R_SC = [1.2, 2.4, 2], R_BO = [0.8, 1.2, 1];
// blade: 13 mm deep at the bolster, 3 mm thick, the point a hair above the handle axis
const T = 3.0, TAPER = 0.62, EDGE_T = 0, FALSE_T = 0.5;
const SPINE_Y = 7.3, EDGE_Y = -5.5, TIP_Y = 1.3;
const SW_U = 46, SWEDGE = 2.6;        // the swedge runs from 46 mm out to the point, 2.6 mm deep
const RIC_U = 9.2, PLUNGE_U = 15.5, GRIND = 0.48; // square ricasso, the notch at 9-11 mm, then a half-height grind

// ---------------------------------------------------------------- colours
const STEEL = 0xbac1ca, BEVEL = 0xe6ebf0; // polished blade: flats, then the ground swedge / edge bevels catching light
const NICKEL = 0xe0dccf;              // nickel silver (a warmer silver than the blade)
const PIN = 0xaaa69b, BUTTON = 0xf0ece2, BUTTON_RING = 0x8e8a81;
const BRASS = 0xc7a04b, SPRING = 0x8b929b;
const HORN = 0x56402f;                // Brazilian horn, dark brown

// ---------------------------------------------------------------- helpers
const smooth = (a, b, x) => { const t = Math.max(0, Math.min(1, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
const along = (pts) => (u) => {      // y at u on a polyline of [u, y] sorted by u
  if (u <= pts[0][0]) return pts[0][1];
  for (let i = 1; i < pts.length; i++) if (u <= pts[i][0]) { const [u0, y0] = pts[i - 1], [u1, y1] = pts[i]; return y0 + ((y1 - y0) * (u - u0)) / (u1 - u0 || 1); }
  return pts[pts.length - 1][1];
};
// one triangle, wound so its normal points away from ref (a point inside the part)
const V = new THREE.Vector3(), W = new THREE.Vector3(), N = new THREE.Vector3();
function tri(out, a, b, c, ref) {
  V.set(b[0] - a[0], b[1] - a[1], b[2] - a[2]); W.set(c[0] - a[0], c[1] - a[1], c[2] - a[2]);
  N.crossVectors(V, W);
  if (N.lengthSq() < 1e-18) return;
  const d = N.x * ((a[0] + b[0] + c[0]) / 3 - ref[0]) + N.y * ((a[1] + b[1] + c[1]) / 3 - ref[1]) + N.z * ((a[2] + b[2] + c[2]) / 3 - ref[2]);
  if (d < 0) out.push(...a, ...c, ...b); else out.push(...a, ...b, ...c);
}
// one mesh per colour (not one mesh with a material array: remote.js's third-person copy clones mesh.material)
function meshOf(lists, colors) {
  const g = new THREE.Group();
  lists.forEach((l, k) => {
    if (!l.length) return;
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(l, 3));
    geo.computeVertexNormals();
    g.add(new THREE.Mesh(geo, mat(colors[k])));
  });
  return g;
}
// the outline that an extrusion bevel of size d grows back into pts, so a rounded part keeps its real size. It inverts
// three.js ExtrudeGeometry's own offset (getBevelVec: the mitre, capped at sqrt 2 on sharp corners) by fixed-point
// iteration; a plain mitre inset comes back short wherever a corner is sharper than 90 degrees (the horn's corners).
function bevelVec(pt, prev, next) {
  const vpx = pt[0] - prev[0], vpy = pt[1] - prev[1], vnx = next[0] - pt[0], vny = next[1] - pt[1];
  const vpl2 = vpx * vpx + vpy * vpy, col = vpx * vny - vpy * vnx;
  let tx, ty, sh;
  if (Math.abs(col) > Number.EPSILON) {
    const vpl = Math.sqrt(vpl2), vnl = Math.hypot(vnx, vny);
    const ppx = prev[0] - vpy / vpl, ppy = prev[1] + vpx / vpl, pnx = next[0] - vny / vnl, pny = next[1] + vnx / vnl;
    const sf = ((pnx - ppx) * vny - (pny - ppy) * vnx) / col;
    tx = ppx + vpx * sf - pt[0]; ty = ppy + vpy * sf - pt[1];
    const l2 = tx * tx + ty * ty;
    if (l2 <= 2) return [tx, ty];
    sh = Math.sqrt(l2 / 2);
  } else {
    const E = Number.EPSILON, same = vpx > E ? vnx > E : vpx < -E ? vnx < -E : Math.sign(vpy) === Math.sign(vny);
    if (same) { tx = -vpy; ty = vpx; sh = Math.sqrt(vpl2); } else { tx = vpx; ty = vpy; sh = Math.sqrt(vpl2 / 2); }
  }
  return [tx / sh, ty / sh];
}
function inset(pts, d) {
  let area = 0;
  for (let i = 0; i < pts.length; i++) { const [x0, y0] = pts[i], [x1, y1] = pts[(i + 1) % pts.length]; area += x0 * y1 - x1 * y0; }
  const P = area < 0 ? pts : pts.slice().reverse(), n = P.length; // three.js walks the outline clockwise
  let Q = P.map((p) => p.slice());
  for (let it = 0; it < 12; it++) {
    const E = Q.map((q, i) => { const v = bevelVec(q, Q[(i - 1 + n) % n], Q[(i + 1) % n]); return [q[0] + v[0] * d, q[1] + v[1] * d]; });
    Q = Q.map((q, i) => [q[0] + P[i][0] - E[i][0], q[1] + P[i][1] - E[i][1]]);
  }
  return Q;
}
// handle outline point: u = mm behind the front bolster face, y = mm above the handle centre line -> model [z, y] in metres
const H = (u, y) => [(Z_F + u) * MM, (YC + y) * MM];
const toM = (pts) => pts.map(([u, y]) => H(u, y));
// a rounded side-view part on one side (sx = +1 / -1), its outline given at full size; it runs from just outside the
// slot to the outside of the handle, its inner rounding buried in the liner. r = [across, side view, segments]
const side = (pts, color, [bt, bs, segs], sx, xIn = SLOT + 0.1) => {
  const shape = new THREE.Shape(toM(inset(pts, bs)).map(([z, y]) => new THREE.Vector2(z, y)));
  const core = OUT - xIn - 2 * bt;
  const geo = new THREE.ExtrudeGeometry(shape, { depth: core * MM, bevelEnabled: true, bevelThickness: bt * MM, bevelSize: bs * MM, bevelSegments: segs, curveSegments: 4, steps: 1 });
  geo.translate(0, 0, -core * MM / 2);
  geo.rotateY(-Math.PI / 2); // shape x -> model z, extrusion -> model x
  const m = new THREE.Mesh(geo, mat(color));
  m.position.x = sx * ((xIn + OUT) / 2) * MM;
  return m;
};

// ---------------------------------------------------------------- blade (side view, u = mm ahead of the bolster face)
// spine: straight, then the swedge line runs down, almost straight, to the point
const spineY = along([[-3, SPINE_Y], ...curve([[SW_U - 8, SPINE_Y], [SW_U, SPINE_Y], [SW_U + 6, SPINE_Y - 0.55], [70, 4.75], [88, 2.84], [BLADE_L, TIP_Y]], 30)]);
// edge: the ricasso, a small notch where the sharpening starts, a long straight edge, then a gentle rise into the point
const edgeY = along([[-3, EDGE_Y], [RIC_U, EDGE_Y], [10.3, EDGE_Y + 1.05], [11.4, EDGE_Y + 0.1],
  ...curve([[40, EDGE_Y + 0.1], [64, EDGE_Y + 0.1], [76, -5.0], [86, -3.6], [94, -1.7], [99, -0.1], [BLADE_L, TIP_Y]], 30)]);

// cross-section at u: S+ S- (spine) W+ W- (swedge line) G+ G- (grind line) E+ E- (edge). in pivot space (blade group)
function section(u) {
  const ys = spineY(u), ye = edgeY(u), h = Math.max(0, ys - ye);
  const p = smooth(RIC_U + 2, PLUNGE_U, u);                 // 0 = square ricasso, 1 = ground
  const half = Math.min((T / 2) * (1 - (TAPER * Math.max(0, u)) / BLADE_L), 0.13 * h);
  const e = half + (EDGE_T / 2 - half) * p;
  const gv = GRIND * p;
  const k = Math.max(0, Math.min(1, (u - SW_U) / 34));       // the swedge widens from a point where it starts
  const ts = Math.min(half, half + (FALSE_T / 2 - half) * k);
  const sw = Math.min(SWEDGE * k, 0.9 * (1 - gv) * h);
  const z = -(PIV_U + u), yg = ye + gv * h;
  const q = (x, y) => [x * MM, y * MM, z * MM];
  return { ref: [0, ((ys + ye) / 2) * MM, z * MM], p: [q(ts, ys), q(-ts, ys), q(half, ys - sw), q(-half, ys - sw), q(half, yg), q(-half, yg), q(e, ye), q(-e, ye)] };
}
function buildBlade() {
  const us = [-2, 0, RIC_U, 10.3, 11.4, PLUNGE_U, 24, 35, SW_U, 52, 59, 66, 73, 80, 86, 91, 95, 98.5, 101, BLADE_L];
  const R = us.map(section);
  const flat = [], bev = [];
  const strips = [[0, 1, flat], [0, 2, bev], [1, 3, bev], [2, 4, flat], [3, 5, flat], [4, 6, bev], [5, 7, bev], [6, 7, bev]];
  for (let i = 0; i < R.length - 1; i++) {
    const A = R[i].p, B = R[i + 1].p, ref = [0, (R[i].ref[1] + R[i + 1].ref[1]) / 2, (R[i].ref[2] + R[i + 1].ref[2]) / 2];
    for (const [a, b, out] of strips) { tri(out, A[a], A[b], B[b], ref); tri(out, A[a], B[b], B[a], ref); }
  }
  return meshOf([flat, bev], [STEEL, BEVEL]); // the heel is inside the tang: no cap
}
// the tang round the pivot (hidden in the bolsters; open, its top bears on the spring). pivot space [z, y], mm
const TANG = [[-9.5, 7.2], [-1, 7.2], [2.6, 6.3], [5.2, 4.3], [6.6, 1.2], [6.5, -1.6], [5.1, -3.8], [3.0, -5.2], [-9.5, -5.4]];

// ---------------------------------------------------------------- handle outlines (u behind the bolster face, y off the centre line)
// front bolster: guard ears top and bottom, its back edge a convex arc into the horn
const ear = (pts, sy) => pts.map(([u, dy]) => [u, sy * (HH + dy)]);
const earTop = (tab) => ear(tab
  ? [[-0.7, 1.9], [0.4, 3.1], [1.9, 3.2], [3.9, 1.45], [6.6, 0.15]]   // the swivel's thumb tab: taller, leaning forward
  : [[-0.3, 1.4], [0.9, 2.3], [2.3, 2.15], [3.9, 0.95], [6.2, 0.12]], 1);
const earBot = ear([[6.2, 0.12], [3.9, 0.95], [2.3, 2.15], [0.9, 2.3], [-0.3, 1.4]], -1);
const R_BACK = 16.6, A_BACK = Math.asin(HH / R_BACK);  // front bolster back edge: an arc round (PIV_U, 0), top -> bottom
const backArc = [0.5, 0.25, 0, -0.25, -0.5].map((t) => { const a = t * 2 * A_BACK; return [PIV_U + Math.cos(a) * R_BACK, Math.sin(a) * R_BACK]; });
const frontBolster = (tab) => [[0, -HH + 0.4], [0, HH - 0.4], ...earTop(tab), ...backArc, ...earBot];
// end bolster: its front edge bulges forward into the horn, a rounded butt coming to a soft point
const R_END = 17.5, C_END = 127, A_END = Math.asin(HH / R_END);
const endArc = [-0.5, -0.25, 0, 0.25, 0.5].map((t) => { const a = Math.PI + t * 2 * A_END; return [C_END + Math.cos(a) * R_END, Math.sin(a) * R_END]; });
const BUTT = [[118, 1], [121.3, 0.886], [123.3, 0.614], [124.3, 0.295], [CLOSED_L, 0]];  // its top half, y as a fraction of HH
const butt = [...BUTT, ...BUTT.slice(0, -1).reverse().map(([u, f]) => [u, -f])].map(([u, f]) => [u, f * HH]);
const endBolster = [...butt, ...endArc.slice().reverse()]; // butt top -> bottom, then its front edge bottom -> top
const scale = [backArc[0], ...endArc, ...backArc.slice(1).reverse()]; // the horn between them (both arcs run top -> bottom)
// liners: the handle outline without the ears, a hair inside the bolster faces (and under the bolsters' top / bottom)
const LH = HH - 0.05;
const liner = [[0.4, LH], [117.75, LH], ...butt.slice(1, -1).map(([u, y]) => [u - 0.25, (y * (HH - 0.25)) / HH]), [117.75, -LH], [0.4, -LH]];
// backspring along the back, and the spacer it is riveted to at the butt (the shut blade's point stops short of it)
const SP = SPRING_Y0 - YC, ST = HH - 0.15;
const spring = [[1, SP], [1, ST], [117.5, ST], ...butt.slice(1, 7).map(([u, y]) => [u - 0.5, (y * (HH - 0.5)) / HH]), [121.4, -0.8 * HH], [120.2, -0.84 * HH], [120.2, SP]];

export function build(g) {
  // ---------------------------------------------------------- the blade, on its pivot
  const mirror = new THREE.Group(); mirror.scale.y = -1; g.add(mirror);
  const flip = new THREE.Group(); flip.position.set(0, 0, Z_P * MM); mirror.add(flip);
  const inner = new THREE.Group(); inner.scale.y = -1; flip.add(inner);
  inner.add(buildBlade());
  inner.add(slab(TANG.map(([z, y]) => [z * MM, y * MM]), 2.9 * MM, STEEL));
  g.userData.flipBlade = flip;

  // ---------------------------------------------------------- frame: liners, backspring + butt spacer
  for (const sx of [1, -1]) g.add(slab(toM(liner), LINER * MM, BRASS, { x: sx * (SLOT + LINER / 2) * MM }));
  g.add(slab(toM(spring), (2 * SLOT - 0.2) * MM, SPRING));

  // ---------------------------------------------------------- bolsters and horn scales
  g.add(side(frontBolster(false), NICKEL, R_BO, 1), side(frontBolster(true), NICKEL, R_BO, -1)); // -X: the swivel bolster
  for (const sx of [1, -1]) g.add(side(endBolster, NICKEL, R_BO, sx), side(scale, HORN, R_SC, sx));

  // ---------------------------------------------------------- pins and the button
  g.add(pin(1.55 * MM, (2 * OUT + 0.3) * MM, PIN, 0, 0, Z_P * MM, 8));                       // blade pivot
  g.add(pin(1.2 * MM, (2 * OUT + 0.3) * MM, PIN, 0, (SPRING_Y0 + 1.0) * MM, (Z_F + 117.6) * MM, 8)); // backspring rivet
  // push button on the front bolster (button side = -X, under a right thumb): a domed nickel-silver button in a recessed ring
  const bz = (Z_F + 17.6) * MM, by = YC * MM;
  g.add(pin(3.75 * MM, 0.5 * MM, BUTTON_RING, -(OUT + 0.05) * MM, by, bz, 10));
  const dome = new THREE.LatheGeometry([[3.1, -0.6], [3.1, 0.45], [2.45, 0.95], [1.4, 1.22], [0, 1.3]].map(([r, h]) => new THREE.Vector2(r * MM, h * MM)), 10);
  dome.rotateZ(Math.PI / 2); // lathe axis (y) -> -x
  const btn = new THREE.Mesh(dome, mat(BUTTON));
  btn.position.set(-OUT * MM, by, bz);
  g.add(btn);

  g.userData.muzzle = new THREE.Vector3(0, TIP_Y * MM, (Z_F - BLADE_L) * MM);
  g.userData.len = (CLOSED_L + BLADE_L) * MM; // 0.227 = 8.94"
}
// a hat on the back of the handle, mid grip
export const hatAt = [[0, 0.0097, 0.03], 0.05];
