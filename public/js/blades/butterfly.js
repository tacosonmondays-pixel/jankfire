// Butterfly skin: the Benchmade Model 42 Bali-Song (Weehawk), the classic production balisong: a 4.2" Weehawk spear point
//   in 154CM, 1/8" stock, a high flat grind with a long ground swedge running down the spine into the point, a squared
//   kicker at the heel of the edge with a small sharpening choil in front of it. Two milled titanium channel handles, 5.2"
//   long, skeletonised with three long windows (shut, you see the blade through them), Torx pivot screws on each handle at
//   the tang, zen pins just behind them, a screw at the butt and, on the bite handle, Benchmade's spring latch tucked in
//   at the butt, its tab standing proud of the end. A tang pin through the tang shows when the handles swing away.
// Refs: BladeHQ, Benchmade 42 Balisong (#8961 / #166 / #10925): 9.40" overall, 154CM Weehawk; sharpthingsokc 42PO and
//   bladeforums 42 sale threads: 4.20" blade, 0.125" thick, 5.20" closed, 4.10 oz, flat grind, skeletonised 6Al4V titanium
//   handles, spring latch (older ones a T-latch); americanedgeknives 42 / 42S listings (milled titanium handles, spring
//   latch); knivesshipfree / Knife Informer, Benchmade 51 Morpho (the 42's successor: 9.375-9.4" open, 5.375-5.4" closed,
//   handle 0.48" thick across both handles); Tactical Elements, Squid Industries Krake Raken (handle 0.5" thick, 5.625"
//   long) and a 51BK listing (blade width 0.75") for the class; Squid Industries / knifepivotlube / BladeHQ blog balisong
//   anatomy: the bite handle closes on the edge and carries the latch, the safe handle closes on the spine; tang pins sit
//   in the tang and stop the handles, zen pins sit in the handles; the kicker is the unsharpened lobe between the edge and
//   the pivots that keeps the edge off the handles; the blade rests between the handles' channels when shut.
//   No source gives the handle or blade height: 19 mm (0.75") handles and a 15 mm (0.59") blade are estimates sized so the
//   shut blade hides between the handles, as on the real knife.
// Contract: userData.handles = [h1, h2], one group per handle on the tang pivot (z = -0.045, y = 0), each handle modelled
//   pointing +Z inside it. The game sets h.rotation.x: 0 = open (handles back in the hand), PI = shut (folded over the
//   blade), and spins them through 2 PI for flips. The blade (fixed, added to g) is 3.2 mm thick and lives in the 3.6 mm
//   slot between the two handles' inner faces, so a handle swinging round its pivot never cuts through it, open, shut or
//   anywhere in between; the latch sits in the slot too, but beyond the radius the point reaches. Both pivots are on the
//   blade's axis (y = 0): with one pivot nearer the spine and one nearer the edge the two handles would only line up in
//   one of the two states (two half turns round different pins differ by a shift of twice their spacing), and here they
//   must line up both open in the hand and shut over the blade.
//   h1 (+X) is the safe handle, h2 (-X, the side the first-person camera sees) the bite handle with the latch.
import { THREE, blade, slab, pin, curve, arc, resample } from './kit.js';

const MM = 0.001, IN = 25.4;
// ---------------------------------------------------------------- measurements (mm)
const Z_P = -45;                  // the pivot, at the base of the blade
const NOSE = 8.5;                 // the handle's rounded front reaches this far ahead of the pivot
const HANDLE_L = 5.2 * IN;        // 132 mm shut: nose to butt
const BUTT = HANDLE_L - NOSE;     // 123.6 mm behind the pivot
const Z_F = Z_P - NOSE;           // the handles' front, where the blade length is measured from
const BLADE_L = 4.2 * IN;         // 106.7 mm
const HH = 9.5;                   // half the handle height (19 mm)
const X_IN = 1.8, X_OUT = 6.25;   // each handle: from the slot to the outside (both: 12.5 mm = 0.49")
const HX = (X_IN + X_OUT) / 2;    // the handle groups sit mid handle
const T = 0.125 * IN;             // 3.2 mm stock
const SPINE_Y = 7.4, EDGE_Y = -7.6, TIP_Y = 0.4; // 15 mm deep blade on the handle axis
const KICK_Y = -8.3;              // the kicker hangs 0.7 mm below the edge line
const RIC = 7.6;                  // square ricasso / kicker: the first 7.6 mm in front of the handles
const SW_U = 36, SWEDGE = 2.6;    // the 42's swedge is cut back far: from 36 mm out, 2.6 mm deep at full width
const DROP_U = 50;                // where the spine starts to drop to the point
const TANG_R = 7.48;
const GRIND = 0.78;                // a high flat grind               // the tang is rounded round the pivot

// ---------------------------------------------------------------- colours
const STEEL = 0xbac0c9, GROUND = 0xd2d7de, EDGE = 0xf1f4f7, SWEDGE_C = 0xe0e4ea; // satin 154CM
const TI = 0xa2a7b0;              // bead blasted titanium
const SCREW = 0x2c2f34, ZEN = 0xc4c8ce, LATCH = 0xa9afb7, TANG_PIN = 0x5d636c;

// side view point in the blade's frame: u = mm in front of the handles' front, y = mm up -> model [z, y] in metres
const P = (u, y) => [(Z_F - u) * MM, y * MM];
// handle-local point: w = mm behind the pivot (towards the butt), y = mm up -> group [z, y] in metres
const L = (w, y) => [w * MM, y * MM];
const arcL = (cw, cy, r, a0, a1, n) => arc(cw, cy, r, a0, a1, n); // angles: 0 = +w (to the butt), PI/2 = up

// ---------------------------------------------------------------- the handle (same outline for both, mirrored in X)
// rounded nose round the pivot, straight sides, a squarer butt
const R_NOSE = 7, R_BUTT = 3;
const OUTLINE = [
  ...arcL(-NOSE + R_NOSE, HH - R_NOSE, R_NOSE, Math.PI / 2, Math.PI, 5),        // top front corner
  ...arcL(-NOSE + R_NOSE, -HH + R_NOSE, R_NOSE, Math.PI, Math.PI * 1.5, 5),     // bottom front corner
  ...arcL(BUTT - R_BUTT, -HH + R_BUTT, R_BUTT, -Math.PI / 2, 0, 3),            // butt, bottom
  ...arcL(BUTT - R_BUTT, HH - R_BUTT, R_BUTT, 0, Math.PI / 2, 3),              // butt, top
];
// three long skeleton windows down the handle (stadium shaped)
const stadium = (w0, w1, h) => {
  const r = h / 2;
  return [...arcL(w1 - r, 0, r, -Math.PI / 2, Math.PI / 2, 5), ...arcL(w0 + r, 0, r, Math.PI / 2, Math.PI * 1.5, 5)];
};
const WINDOWS = [stadium(16, 45, 9), stadium(50, 79, 9), stadium(84, 111, 9)];
// the spring latch (side view, bite handle): pivots on the butt pin, its tab stands proud of the butt
const LATCH_W = 117.5;
const LATCH_PTS = [[LATCH_W, -2.0], [LATCH_W, 2.0], [BUTT - 0.5, 2.3], [BUTT + 1.6, 3.3], [BUTT + 2.9, 2.6], [BUTT + 3.2, 0.2], [BUTT + 2.6, -2.3], [BUTT, -2.6]];

function handle(g, side, bite) {
  const grp = new THREE.Group();
  grp.position.set(side * HX * MM, 0, Z_P * MM);
  g.add(grp);
  const xl = (xAbs) => side * (xAbs - HX) * MM; // absolute distance from the blade plane -> group-local x
  const toM = (pts) => pts.map(([w, y]) => L(w, y));
  // the milled titanium handle, its windows cut right through
  grp.add(slab(toM(OUTLINE), (X_OUT - X_IN) * MM, TI, { x: xl(HX), holes: WINDOWS.map(toM) }));
  // Torx pivot screw, the two zen pins behind it, the screw at the butt
  grp.add(pin(3.0 * MM, 0.9 * MM, SCREW, xl(X_OUT + 0.45), 0, 0, 10));
  for (const y of [5.4, -5.4]) grp.add(pin(1.1 * MM, 0.5 * MM, ZEN, xl(X_OUT + 0.2), y * MM, 10.5 * MM, 6));
  grp.add(pin(1.7 * MM, 0.6 * MM, SCREW, xl(X_OUT + 0.3), 0, 119.5 * MM, 8));
  // the spring latch, in the slot on the bite handle's side (beyond the reach of the point as it swings round)
  if (bite) grp.add(slab(toM(LATCH_PTS), 1.3 * MM, LATCH, { x: xl(1.05) }));
  return grp;
}

export function build(g) {
  // ---------------------------------------------------------- blade (fixed): Weehawk spear point
  const N = 24;
  const spine = [P(RIC - 0.8, SPINE_Y), P(DROP_U - 6, SPINE_Y),
    ...curve([P(DROP_U, SPINE_Y), P(DROP_U + 8, SPINE_Y - 0.3), P(70, 6.3), P(82, 4.85), P(93, 3.0), P(101, 1.5), P(BLADE_L, TIP_Y)], 12)];
  const edge = [P(RIC - 0.8, EDGE_Y), P(58, EDGE_Y),
    ...curve([P(64, EDGE_Y + 0.05), P(74, -7.0), P(84, -5.9), P(93, -4.1), P(100, -2.1), P(104.5, -0.5), P(BLADE_L, TIP_Y)], 12)];
  const S = resample(spine, N), E = resample(edge, N);
  const at = (s, arr) => { const f = s * (N - 1), i = Math.min(N - 2, Math.floor(f)), t = f - i; return arr[i] + (arr[i + 1] - arr[i]) * t; };
  const sy = S.map((p) => p[1]), ey = E.map((p) => p[1]);
  const hgt = (s) => Math.max(1e-4, at(s, sy) - at(s, ey));
  const ramp = (x, a, b) => Math.max(0, Math.min(1, (x - a) / (b - a)));
  const len = BLADE_L - (RIC - 0.8), sOf = (u) => (u - (RIC - 0.8)) / len;
  const W0 = sOf(SW_U);
  g.add(blade({
    spine, edge, n: N, thick: T * MM, grind: GRIND, taper: 0.55, color: STEEL, edgeColor: GROUND,
    bands: [
      { from: 0, to: (s) => Math.min(0.32, (1.2 * MM) / hgt(s)), color: EDGE },                         // honed edge
      { from: (s) => Math.max(GRIND + 0.01, 1 - (SWEDGE * MM * ramp(s, W0, W0 + 0.2)) / hgt(s)), to: 1, color: SWEDGE_C, s0: W0, s1: 1 }, // swedge (kept above the grind line)
    ],
  }));
  // tang, square ricasso and kicker: one 3.3 mm plate, rounded round the pivot, a sharpening choil cut in front of the kicker
  const pu = -NOSE; // the pivot, in blade u
  const tang = [
    P(RIC, SPINE_Y + 0.08), P(pu, SPINE_Y + 0.08),
    ...arc(Z_P * MM, 0, TANG_R * MM, Math.PI / 2, -Math.PI / 2, 9).slice(1, -1), // round the back of the pivot
    P(pu, -TANG_R), P(-1.4, -TANG_R), P(-0.7, KICK_Y), P(2.2, KICK_Y), P(2.9, EDGE_Y - 0.08),
    ...arc((Z_F - 4.85) * MM, EDGE_Y * MM, 1.85 * MM, 0, Math.PI, 7).slice(1, -1),             // the choil
    P(6.7, EDGE_Y - 0.08), P(RIC, EDGE_Y - 0.08),
  ];
  g.add(slab(tang, 3.3 * MM, STEEL));
  // tang pin, standing just proud of the tang, short of the handles' inner faces
  g.add(pin(1.1 * MM, 3.55 * MM, TANG_PIN, 0, 4.6 * MM, (Z_P - 3.2) * MM, 6));

  // ---------------------------------------------------------- the handles
  const safe = handle(g, 1, false), bite = handle(g, -1, true);
  g.userData.handles = [safe, bite];
  g.userData.muzzle = new THREE.Vector3(0, TIP_Y * MM, (Z_F - BLADE_L) * MM);
  g.userData.len = (BUTT + 3.2 - (Z_F - BLADE_L - Z_P)) * MM; // butt (and latch tab) to the point: 0.243
}
// a hat on top of the handles, mid grip
export const hatAt = [[0, HH * MM, 0.03], 0.05];
