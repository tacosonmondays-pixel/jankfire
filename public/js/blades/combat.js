// Default knife: the KA-BAR USMC Fighting/Utility Knife (KA-BAR 1217, the Marine Corps knife since 1942).
//   7" (177.8 mm) clip-point blade in 1095 Cro-Van, black epoxy powder coat with the sharpened edge bare steel, a long
//   fuller up near the spine, a slightly concave clip ground as a false edge (swedge). Oval 12-gauge steel double guard,
//   2.5" tip to tip, slightly rounded with its points tipping back toward the hand. Stacked leather washer handle, oval,
//   cut with six traction grooves (seven rings), swelling toward the butt; a parkerized steel butt cap, cross-pinned,
//   with the round peened nut on the end of the rat-tail tang.
// Refs: KA-BAR 1217 product page / catalog (OAL 11-7/8", blade 7", blade width 1.188", 12GA carbon steel guard and butt
//   cap, oval stacked-leather handle with traction grooves, pinned butt cap); retailer spec tables (Knifeworks, KY Gun Co,
//   Osograndeknives, Milgear: handle 4.875", blade thickness 0.165-0.17" / 4.2 mm, 11.2 oz, flat grind with a 20 degree
//   secondary edge); Wikipedia "Ka-Bar" (7" 1095 clip point, leather washer handle, crossguard straight then slightly
//   curved, peened then pinned pommel); Outdoor Life "The Ka-Bar Knife" (guard slightly rounded, points tipping back toward
//   the handle; round pinned pommel); IMA-USA WWII Mark 2 listings (crossguard 2-7/16" to 2-1/2").
// Held like every knife: the leather grip centred on the hand (z -0.031 .. +0.075), the guard just in front of the fist,
// edge down, tip to -Z. No moving parts.
import { THREE, blade, plate, lathe, pin, curve, resample } from './kit.js';

const IN = 0.0254, MM = 0.001;
// ---------------------------------------------------------------- measurements
const BLADE_L = 7 * IN;                 // 177.8 mm, guard face to tip
const HALF_H = 0.5 * 1.188 * IN;        // blade 30.2 mm tall at the heel, centred on the tang / handle axis
const SPINE_T = 0.165 * IN;             // 4.2 mm
const HANDLE_L = 4.875 * IN;            // 123.8 mm behind the guard face: guard + leather + butt cap + nut
const GUARD_H = 2.5 * IN, GUARD_W = 24.5 * MM, GUARD_T = 0.1046 * IN; // 63.5 x 24.5 mm oval, 12 ga (2.66 mm) plate
const GUARD_BEND = 2.4 * MM;            // how far the quillon tips lean back toward the hand
const CAP_L = 12 * MM, NUT_L = 2.6 * MM;
const LEATHER_L = HANDLE_L - GUARD_T - CAP_L - NUT_L; // ~106.5 mm of stacked leather
const Z_GUARD = -0.034;                 // the guard's front face (where the blade length is measured from)
const Z_L0 = Z_GUARD + GUARD_T, Z_L1 = Z_L0 + LEATHER_L, Z_CAP = Z_L1 + CAP_L;
const TIP_Y = 2.4 * MM;                 // the clip point sits a little above the handle axis
const N = 30;                           // blade stations

// ---------------------------------------------------------------- colours
const COAT = 0x34383e, COAT_BEVEL = 0x41454c, FULLER_DARK = 0x24272b, FULLER_LIT = 0x4b5058, SWEDGE = 0x4a4e56;
const BARE = 0xd9dee4;                  // the sharpened edge: the coating is ground off
const STEEL = 0x50545b, NUT = 0x7a7f87;  // parkerized guard + butt cap, the peened nut a little brighter
const LEATHER = 0x83502e;

// side view point: u = mm in front of the guard face, y = mm above the handle axis
const P = (u, y) => [Z_GUARD - u * MM, y * MM];
const U_TIP = BLADE_L / MM, H = HALF_H / MM, YT = TIP_Y / MM;

export function build(g) {
  // ---------------------------------------------------------- blade
  // spine: straight to the clip, then a slightly concave clip down to the point
  const spine = [P(-2, H), P(56, H), ...curve([P(112, H), P(119, H - 0.6), P(130, 11.9), P(143, 8.8), P(156, 6.1), P(168, 4.1), P(U_TIP, YT)], 12)];
  // edge: straight, then a long belly sweeping up into the point (arrives at ~32 degrees)
  const edge = [P(-2, -H), P(52, -H), ...curve([P(105, -H), P(122, -14.6), P(136, -13.0), P(148, -10.4), P(158, -7.2), P(166, -4.0), P(172.8, -0.7), P(U_TIP, YT)], 14)];
  // station heights, so painted bands can be placed in mm
  const S = resample(spine, N), E = resample(edge, N);
  const at = (s, arr) => { const f = s * (N - 1), i = Math.min(N - 2, Math.floor(f)), t = f - i; return arr[i] + (arr[i + 1] - arr[i]) * t; };
  const sy = S.map((p) => p[1]), ey = E.map((p) => p[1]);
  const hgt = (s) => Math.max(1e-4, at(s, sy) - at(s, ey));
  const frac = (s, y) => (y - at(s, ey)) / hgt(s);          // absolute height y (m) -> 0 edge .. 1 spine
  const sOf = (u) => (u + 2) / (U_TIP + 2);                  // mm from the guard -> station fraction
  const ramp = (x, a, b) => Math.max(0, Math.min(1, (x - a) / (b - a)));
  // fuller: 6.5 mm wide, its top 4.7 mm below the spine, from 1 cm ahead of the guard to where the clip starts.
  // a groove: its lower half faces up and catches the light, the upper half is in shade. blunt back, tapered front.
  const F0 = sOf(11), F1 = sOf(113), fTop = 10.4 * MM, fBot = 3.9 * MM, fMid = (fTop + fBot) / 2;
  const fw = (s) => Math.min(ramp(s, F0 - 0.04, F0 + 0.01), ramp(F1, s, s + 0.06));
  const fLo = (s) => frac(s, fMid - (fMid - fBot) * fw(s)), fHi = (s) => frac(s, fMid + (fTop - fMid) * fw(s));
  const fLit = (s) => frac(s, fMid);
  // swedge: the clip's false edge, ~3 mm wide, black like the rest
  const W0 = sOf(112);
  const swLo = (s) => Math.max(0.55, 1 - (3.2 * MM * ramp(s, W0, W0 + 0.07)) / hgt(s));
  // the bare steel edge bevel: ~2.4 mm tall all the way into the point
  const edgeTo = (s) => Math.min(0.38, 2.4 * MM / hgt(s));
  // flat grind from mid-height (just under the fuller) to the edge; the coat covers it, only the edge bevel is bare
  g.add(blade({
    spine, edge, n: N, thick: SPINE_T, grind: 0.5, taper: 0.5, color: COAT, edgeColor: COAT_BEVEL,
    bands: [
      { from: 0, to: edgeTo, color: BARE, s0: sOf(5), s1: 1 },
      { from: fLo, to: fLit, color: FULLER_LIT, s0: F0, s1: F1 },
      { from: fLit, to: fHi, color: FULLER_DARK, s0: F0, s1: F1 },
      { from: swLo, to: 1, color: SWEDGE, s0: W0, s1: 1 },
    ],
  }));

  // ---------------------------------------------------------- guard: an oval plate, its points tipping back toward the handle
  const oval = [];
  for (let k = 0; k < 20; k++) {
    const a = (k / 20) * Math.PI * 2, c = Math.cos(a), s = Math.sin(a), p = 2 / 2.4; // a little fuller than an ellipse
    oval.push([(GUARD_W / 2) * Math.sign(c) * Math.abs(c) ** p, (GUARD_H / 2) * Math.sign(s) * Math.abs(s) ** p]);
  }
  const guard = plate(oval, GUARD_T, STEEL, { z: Z_GUARD + GUARD_T / 2 });
  const gp = guard.geometry.attributes.position;
  for (let i = 0; i < gp.count; i++) gp.setZ(i, gp.getZ(i) + GUARD_BEND * (gp.getY(i) / (GUARD_H / 2)) ** 2);
  guard.geometry.computeVertexNormals();
  g.add(guard);

  // ---------------------------------------------------------- stacked leather handle: oval, 6 grooves, swelling to the butt
  const rOf = (t) => (12.4 + 2.8 * Math.sin(Math.min(1, t / 0.72) * Math.PI / 2) - 0.6 * ramp(t, 0.8, 1)) * MM; // half height
  const prof = [];
  const zt = (t) => Z_L0 - 0.0006 + (LEATHER_L + 0.0012) * t; // tucked a hair into the guard and the cap
  prof.push([rOf(0) - 0.0006, zt(0)], [rOf(0.012), zt(0.012)]);
  for (let k = 1; k <= 6; k++) {
    const t = k / 7, w = 0.014;                                // groove ~3 mm wide, 1.5 mm deep
    prof.push([rOf(t - w), zt(t - w)], [rOf(t) - 1.5 * MM, zt(t)], [rOf(t + w), zt(t + w)]);
  }
  prof.push([rOf(0.988), zt(0.988)], [rOf(1) - 0.0005, zt(1)]);
  g.add(lathe(prof, LEATHER, { segs: 8, sx: 0.78 }));

  // ---------------------------------------------------------- butt cap, its cross pin and the peened nut
  const capR = 15.4 * MM;
  g.add(lathe([[0, Z_L1], [capR - 0.5 * MM, Z_L1], [capR, Z_L1 + 2.5 * MM], [capR, Z_L1 + 7.5 * MM], [capR - 1.3 * MM, Z_CAP - 1.4 * MM], [capR - 3.4 * MM, Z_CAP], [0, Z_CAP]], STEEL, { segs: 8, sx: 0.78 }));
  g.add(pin(1.5 * MM, capR * 0.78 * 2 + 0.4 * MM, NUT, 0, 0, Z_L1 + 5 * MM, 6));
  g.add(lathe([[5.2 * MM, Z_CAP - 0.3 * MM], [5.2 * MM, Z_CAP + 1.7 * MM], [3.9 * MM, Z_CAP + NUT_L], [0, Z_CAP + NUT_L]], NUT, { segs: 8 }));

  g.userData.muzzle = new THREE.Vector3(0, TIP_Y, Z_GUARD - BLADE_L);
  g.userData.len = Z_CAP + NUT_L - (Z_GUARD - BLADE_L); // 0.302 = 11-7/8"
}
// a hat on the leather, just behind the middle of the grip
export const hatAt = [[0, 0.0148, 0.028], 0.05];
