// ------------------------------------------------------------ SECOND OPINION GENERAL: a zombies map on two floors.
// ground floor: Emergency (start: the front desk and a double-height waiting room), the pharmacy, Ward A, the back
// corridor with the wheelchair ramp, the morgue (the backup generator = the power) and X-Ray with the fire stairs.
// upstairs: the upstairs corridor, Ward B with a skybridge across the waiting room, the children's ward, the staff
// lounge, the operating theatre (the Warranty Voider) and intensive care. two ways up (the ramp, the stairs) and the
// bridge between the wings, so there's a loop through both floors; hop the bridge rail to drop back into the waiting room.
// every floor is flat; the only height is real steps (the "ramp" is ten shallow ones a lane: zombies and bots walk
// them on the nav grid, server/zombies.js). `zm` is read by the zombies mode.
import { MAPS, MAP_ORDER, builder, wall, stairs, unstick } from './map.js';

function hospital() {
  const B = builder(), D = builder(); // D: looked at, never bumped into
  const W = B.local(0, 0, 0);
  const F = 4.5, H = 9, T = 0.4; // floor to floor, the roof, slab thickness
  const X0 = -30, X1 = 30, Z0 = -24, Z1 = 24;
  const sg = (axis, at, c, y, w, h, mat) => (axis === 'x' ? D.add(c - w / 2, y - h / 2, at - 0.03, c + w / 2, y + h / 2, at + 0.03, mat, { fit: 1 }) : D.add(at - 0.03, y - h / 2, c - w / 2, at + 0.03, y + h / 2, c + w / 2, mat, { fit: 1 }));
  const RAMP = [-8, -24, 4, -16]; // the ramp's well: x0, z0, x1, z1 (two 4 m lanes and a landing)
  const STEPS = [26, 10, 30, 20]; // the fire stairs' well in X-Ray
  const areas = [
    { id: 'wardb', name: 'Ward B', r: [-10, -2, 10, 2], y: [F - 0.2, H], part: 1 }, // the skybridge (listed first: it crosses the waiting room's air)
    { id: 'er', name: 'Emergency', r: [-10, 6, 10, 24], y: [0, F - T], floor: 'lino' },
    { id: 'er', name: 'Emergency', r: [-10, -10, 10, 6], y: [0, H], part: 1, floor: 'lino' }, // the waiting room, open to the roof
    { id: 'pharm', name: 'Pharmacy', r: [-30, 6, -10, 24], y: [0, F - T], floor: 'tile' },
    { id: 'warda', name: 'Ward A', r: [-30, -24, -10, 6], y: [0, F - T], floor: 'lino' },
    { id: 'hall', name: 'Back Corridor', r: [-10, -24, 10, -10], y: [0, F - T], floor: 'linob' },
    { id: 'morgue', name: 'Morgue', r: [10, -24, 30, -6], y: [0, F - T], floor: 'concrete' },
    { id: 'xray', name: 'X-Ray', r: [10, -6, 30, 24], y: [0, F - T], floor: 'linob' },
    { id: 'hall', name: 'Back Corridor', r: [RAMP[0], RAMP[1], RAMP[2] + 1.5, RAMP[3]], y: [F - 0.2, H], part: 1 }, // the ramp's glass box, this side of its shutter
    { id: 'xray', name: 'X-Ray', r: [STEPS[0], 6, STEPS[2], STEPS[3]], y: [F - 0.2, H], part: 1 }, // the top of the stairs, this side of its shutter
    { id: 'uhall', name: 'Upstairs Corridor', r: [-10, -24, 10, -10], y: [F - 0.2, H], floor: 'linob' },
    { id: 'wardb', name: 'Ward B', r: [-30, -24, -10, 6], y: [F - 0.2, H], floor: 'lino' },
    { id: 'kids', name: 'Children\'s Ward', r: [-30, 6, -10, 24], y: [F - 0.2, H], floor: 'carpet' },
    { id: 'staff', name: 'Staff Lounge', r: [-10, 6, 10, 24], y: [F - 0.2, H], floor: 'wood' },
    { id: 'surgery', name: 'Operating Theatre', r: [10, -24, 30, -6], y: [F - 0.2, H], floor: 'tile' },
    { id: 'icu', name: 'Intensive Care', r: [10, -6, 30, 24], y: [F - 0.2, H], floor: 'lino' },
  ];
  // ---- floors. the ground everywhere; upstairs a slab over everything but the waiting room, with a hole for the ramp and one for the stairs
  for (const a of areas) if (a.y[0] < 1) B.add(a.r[0], -0.4, a.r[1], a.r[2], 0, a.r[3], a.floor);
  const cut = (r, h, mat) => { // slab r with hole h (both x0, z0, x1, z1)
    B.add(r[0], F - T, r[1], h[0], F, r[3], mat); B.add(h[2], F - T, r[1], r[2], F, r[3], mat);
    B.add(h[0], F - T, r[1], h[2], F, h[1], mat); B.add(h[0], F - T, h[3], h[2], F, r[3], mat);
  };
  for (const a of areas) {
    if (a.y[0] < 1 || a.part) continue;
    if (a.id === 'uhall') cut(a.r, RAMP, a.floor); else if (a.id === 'icu') cut(a.r, STEPS, a.floor); else B.add(a.r[0], F - T, a.r[1], a.r[2], F, a.r[3], a.floor);
  }
  B.add(X0, H, Z0, X1, H + 0.4, Z1, 'roofg'); // the roof
  D.add(-7, H - 0.06, -8, 7, H, 4, 'glass'); for (const x of [-7, 0, 7]) D.add(x - 0.1, H - 0.2, -8, x + 0.1, H, 4, 'metal'); // a skylight over the waiting room

  // ---- the wheelchair ramp (back corridor): lane A climbs west along the south side, a landing, lane B comes back east along the wall
  for (let i = 0; i < 10; i++) {
    B.add(3 - i, 0, -20, 4 - i, (i + 1) * 0.225, -16, 'mint'); // lane A: 0 -> 2.25
    B.add(-6 + i, 0, -24, -5 + i, 2.25 + (i + 1) * 0.225, -20, 'mint'); // lane B: 2.25 -> F
    D.add(3 - i, (i + 1) * 0.225, -16.2, 3.12 - i, (i + 1) * 0.225 + 0.012, -19.8, 'hazard'); D.add(-5.12 + i, 2.25 + (i + 1) * 0.225, -23.8, -5 + i, 2.262 + (i + 1) * 0.225, -20.2, 'hazard'); // a stripe on each lip
  }
  B.add(-8, 0, -24, -6, 2.25, -16, 'mint'); // the landing
  // its glass box upstairs (no hopping the rail into a corridor you haven't opened)
  B.add(-8, F, -16, 4.15, H, -15.85, 'hospglass'); B.add(-8.15, F, -24, -8, H, -15.85, 'hospglass'); B.add(4, F, -20, 4.15, H, -16, 'hospglass');
  for (const [a, b, c, d] of [[-8.15, -16, 4.15, -15.85], [-8.15, -24, -8, -15.85], [4, -20, 4.15, -16]]) { D.add(a - 0.02, F, b - 0.02, c + 0.02, F + 0.12, d + 0.02, 'metal'); D.add(a - 0.02, F + 1.0, b - 0.02, c + 0.02, F + 1.08, d + 0.02, 'mint'); }
  B.add(-6, 2.25, -20.08, 4, F + 1.1, -19.92, 'metal'); // the rail between the lanes
  // ---- the fire stairs (X-Ray, east wall): ten steps up to a landing, a wall round the hole
  stairs(W, STEPS[0], STEPS[2], STEPS[3], -1, 0, F, 'concrete', 1); // from z 20 up to z 10
  B.add(STEPS[0], F - T, 6, STEPS[2], F, STEPS[1], 'concrete'); // (the landing is the slab's own edge: this keeps it if the hole moves)
  wall(W, 'z', STEPS[0], 6, STEPS[3], F, H, 0.3, 'plaster', []); wall(W, 'x', STEPS[3], STEPS[0], STEPS[2], F, H, 0.3, 'plaster', []);
  B.add(STEPS[0] - 0.15, 0, STEPS[1], STEPS[0], 1.1, STEPS[3], 'metal'); // a rail down the open side, ground floor
  // ---- the skybridge over the waiting room, and the overlook at the end of the upstairs corridor
  B.add(-10, F - T, -2, 10, F, 2, 'metal');
  for (const z of [-2, 1.85]) { B.add(-9.8, F, z, 9.8, F + 0.2, z + 0.15, 'metal'); B.add(-9.8, F + 0.95, z, 9.8, F + 1.1, z + 0.15, 'metal'); for (let x = -9.8; x < 9.9; x += 2.8) B.add(x, F, z, x + 0.15, F + 1.1, z + 0.15, 'metal'); }
  for (const x of [-5, 5]) B.add(x - 0.3, 0, -0.3, x + 0.3, F - T, 0.3, 'metal'); // its legs
  B.add(-9.8, F, -10.15, 9.8, F + 1.1, -10, 'metal'); B.add(-10, F - T, -10.2, 10, F, -10, 'metal'); // the overlook's rail

  // ---- windows: an opening in the outside wall onto a boarded ledge the zombies come from
  const holes = { w: [], e: [], n: [], s: [] }, windows = [];
  const win = (side, c, area, y0 = 0) => {
    holes[side].push({ a: c - 1, b: c + 1, y0: y0 + 0.9, y1: y0 + 2.9 });
    const [ox, oz] = { w: [-1, 0], e: [1, 0], n: [0, -1], s: [0, 1] }[side];
    const face = side === 'w' ? X0 - 0.6 : side === 'e' ? X1 + 0.6 : side === 'n' ? Z0 - 0.6 : Z1 + 0.6;
    const P = (d, l) => (ox ? [face + ox * d, l] : [l, face + oz * d]);
    const box = (d0, d1, l0, l1, ya, yb, mat) => { const [ax, az] = P(d0, l0), [bx, bz] = P(d1, l1); B.add(ax, ya, az, bx, yb, bz, mat); };
    box(0, 3, c - 1.8, c + 1.8, y0 - 0.4, y0, y0 ? 'metal' : 'road'); // the ledge (upstairs: a fire escape)
    box(0, 3.3, c - 2.1, c + 2.1, y0 + 3.2, y0 + 3.5, 'roofg');
    box(3, 3.3, c - 2.1, c + 2.1, y0 - 0.4, y0 + 3.2, y0 ? 'grid' : 'brick');
    box(0, 3, c - 2.1, c - 1.8, y0 - 0.4, y0 + 3.2, y0 ? 'grid' : 'brick'); box(0, 3, c + 1.8, c + 2.1, y0 - 0.4, y0 + 3.2, y0 ? 'grid' : 'brick');
    const out = P(1.5, c), inn = P(-1.6, c), at = P(-0.3, c);
    windows.push({ area, out: [out[0], y0, out[1]], in: [inn[0], y0, inn[1]], at: [at[0], y0 + 1.9, at[1]], yaw: Math.atan2(ox, oz), n: [-ox, 0, -oz] });
  };
  win('s', -5, 'er'); win('s', 5, 'er');
  win('w', 14, 'pharm'); win('s', -20, 'pharm');
  win('w', -4, 'warda'); win('w', -16, 'warda'); win('n', -20, 'warda');
  win('n', 8, 'hall');
  win('e', -14, 'morgue'); win('n', 20, 'morgue');
  win('e', 0, 'xray'); win('s', 18, 'xray');
  win('n', 8, 'uhall', F);
  win('w', -4, 'wardb', F); win('w', -16, 'wardb', F); win('n', -20, 'wardb', F);
  win('w', 14, 'kids', F); win('s', -20, 'kids', F);
  win('s', 0, 'staff', F);
  win('e', -14, 'surgery', F); win('n', 20, 'surgery', F);
  win('e', 0, 'icu', F); win('s', 18, 'icu', F);
  for (const [mat, t0] of [['plaster', 0], ['brick', 0.3]]) { // outside walls, full height, with every window hole
    wall(W, 'z', X0 - 0.15 - t0, Z0 - 0.6, Z1 + 0.6, -0.4, H + 0.4, 0.3, mat, holes.w);
    wall(W, 'z', X1 + 0.15 + t0, Z0 - 0.6, Z1 + 0.6, -0.4, H + 0.4, 0.3, mat, holes.e);
    wall(W, 'x', Z0 - 0.15 - t0, X0, X1, -0.4, H + 0.4, 0.3, mat, holes.n);
    wall(W, 'x', Z1 + 0.15 + t0, X0, X1, -0.4, H + 0.4, 0.3, mat, holes.s);
  }

  // ---- doors: roller shutters you buy open (not map boxes: the mode adds the closed ones to the room)
  const doors = [];
  const door = (axis, fixed, c, a, b, price, y0 = 0) => {
    const box = axis === 'z' ? { min: [fixed - 0.15, y0, c - 2], max: [fixed + 0.15, y0 + 3, c + 2], mat: 'metal' } : { min: [c - 2, y0, fixed - 0.15], max: [c + 2, y0 + 3, fixed + 0.15], mat: 'metal' };
    doors.push({ a, b, price, name: areas.find((x) => x.id === b && !x.part).name, box, at: axis === 'z' ? [fixed, y0 + 1.5, c] : [c, y0 + 1.5, fixed] });
    B.add(box.min[0] - (axis === 'z' ? 0.11 : 0.1), y0 + 2.95, box.min[2] - (axis === 'z' ? 0.1 : 0.11), box.max[0] + (axis === 'z' ? 0.11 : 0.1), y0 + 3.3, box.max[2] + (axis === 'z' ? 0.1 : 0.11), 'hazard'); // its housing
    return { a: c - 2, b: c + 2, y0, y1: y0 + 3 };
  };
  const g0 = [0, F - T], g1 = [F, H];
  // ground floor (Emergency and its waiting room are one open room)
  const dEP = door('z', -10, 15, 'er', 'pharm', 750), dEA = door('z', -10, -2, 'er', 'warda', 1000), dEX = door('z', 10, 15, 'er', 'xray', 1000);
  const dEH = door('x', -10, 0, 'er', 'hall', 750), dHM = door('z', 10, -17, 'hall', 'morgue', 1250);
  const dPA = door('x', 6, -20, 'pharm', 'warda', 1000), dMX = door('x', -6, 20, 'morgue', 'xray', 1000);
  wall(W, 'z', -10, Z0, Z1, ...g0, 0.4, 'plaster', [dEP, dEA]);
  wall(W, 'z', 10, Z0, Z1, ...g0, 0.4, 'plaster', [dEX, dHM]);
  wall(W, 'x', -10, -10, 10, ...g0, 0.4, 'plaster', [dEH]);
  wall(W, 'x', 6, X0, -10, ...g0, 0.4, 'plaster', [dPA]);
  wall(W, 'x', -6, 10, X1, ...g0, 0.4, 'plaster', [dMX]);
  // upstairs
  const dRT = door('z', RAMP[2] + 1.5, -22, 'hall', 'uhall', 1250, F); // the shutter at the top of the ramp
  wall(W, 'x', -20, RAMP[2], RAMP[2] + 1.65, ...g1, 0.3, 'plaster', []); B.add(RAMP[2] + 1.35, F + 3.3, -24, RAMP[2] + 1.65, H, -20, 'plaster');
  const dST = door('x', 6, 28, 'xray', 'icu', 1250, F); // and the one at the top of the stairs
  B.add(STEPS[0], F + 3.3, 5.85, STEPS[2], H, 6.15, 'plaster');
  const dUB = door('z', -10, -13, 'uhall', 'wardb', 1000, F), dUS = door('z', 10, -13, 'uhall', 'surgery', 1500, F);
  const dBI = door('z', 10, 0, 'wardb', 'icu', 1000, F); // the far end of the skybridge
  const dKS = door('z', -10, 15, 'kids', 'staff', 750, F), dSI = door('z', 10, 15, 'staff', 'icu', 1000, F);
  const dBK = door('x', 6, -20, 'wardb', 'kids', 1000, F), dSU = door('x', -6, 20, 'surgery', 'icu', 1250, F);
  wall(W, 'z', -10, Z0, Z1, ...g1, 0.4, 'plaster', [dUB, { a: -2, b: 2, y0: F, y1: F + 3 }, dKS]); // (the bridge's mouth: no shutter this end)
  wall(W, 'z', 10, Z0, Z1, ...g1, 0.4, 'plaster', [dUS, dBI, dSI]);
  wall(W, 'x', 6, X0, 10, ...g1, 0.4, 'plaster', [dBK]); // Ward B | the children's ward, the waiting room's air | the lounge
  wall(W, 'x', -6, 10, X1, ...g1, 0.4, 'plaster', [dSU]);
  void dRT; void dST;

  // ---- EMERGENCY: the front desk, pillars under the lounge's edge, the waiting room's seats (the bridge overhead)
  B.add(-3, 0, 6.6, 3, 1.1, 8, 'white'); B.add(-3.1, 1.1, 6.5, 3.1, 1.18, 8.1, 'mint');
  for (const x of [-7, 7]) B.add(x - 0.4, 0, 5.6, x + 0.4, F - T, 6.4, 'plaster');
  B.add(-10, F - T, 5.8, 10, F, 6.2, 'plaster');
  for (const z of [-7, 3.6]) for (const x of [-5.5, 5.5]) { B.box(x, 0.25, z, 5, 0.5, 0.7, 'blue'); D.add(x - 2.5, 0.5, z + 0.25, x + 2.5, 1.0, z + 0.35, 'blue'); for (let k = -2; k <= 2; k++) D.add(x + k - 0.03, 0.5, z - 0.35, x + k + 0.03, 0.72, z + 0.35, 'metal'); }
  for (const [x, z] of [[-9, -9], [9, -9]]) { B.box(x, 0.4, z, 0.9, 0.8, 0.9, 'brick'); D.add(x - 0.5, 0.8, z - 0.5, x + 0.5, 1.9, z + 0.5, 'grass'); } // plants doing better than the patients
  // ---- PHARMACY: the counter, shelves of pills behind it
  B.add(-24, 0, 12.6, -14, 1.1, 13.8, 'white'); B.add(-24.1, 1.1, 12.5, -13.9, 1.18, 13.9, 'mint');
  for (const x of [-27, -22.5, -17]) B.add(x - 0.35, 0, 16.5, x + 0.35, 2.2, 21, 'pills');
  // ---- the wards: beds down the walls (a bed: frame, mattress, a blanket, a pillow)
  const bed = (x, y, z, dx, mat = 'blanket', len = 2.1) => { // dx: which way the feet point (+-1 along x)
    B.box(x, y + 0.3, z, len, 0.6, 1.0, 'sheet');
    D.add(x - len / 2 - 0.02, y + 0.6, z - 0.52, x + len / 2 + 0.02, y + 0.68, z + 0.52, 'sheet'); D.add(x - dx * len / 2, y + 0.6, z - 0.52, x - dx * (len / 2 - 0.08), y + 1.1, z + 0.52, 'metal'); // the headboard
    D.add(Math.min(x - dx * 0.2, x + dx * len / 2), y + 0.68, z - 0.53, Math.max(x - dx * 0.2, x + dx * len / 2), y + 0.74, z + 0.53, mat);
    D.add(x - dx * (len / 2 - 0.15) - 0.25, y + 0.68, z - 0.3, x - dx * (len / 2 - 0.15) + 0.25, y + 0.8, z + 0.3, 'white');
  };
  const curtain = (x0, x1, y, z) => { D.add(x0, y + 2.25, z - 0.02, x1, y + 2.3, z + 0.02, 'metal'); D.add(x0, y + 0.3, z - 0.015, x0 + (x1 - x0) * 0.6, y + 2.25, z + 0.015, 'curtain'); };
  for (const y of [0, F]) { // Ward A, and Ward B straight above it
    for (const z of [-21.5, -10, 2]) { bed(-28.6, y, z, 1); curtain(-29.8, -27, y, z + 1.1); D.add(-29.9, y + 1.3, z - 0.9, -29.5, y + 1.7, z - 0.4, 'ecg', { fit: 1 }); }
    for (const z of [-21, -7.5]) { bed(-11.4, y, z, -1, y ? 'pink' : 'blanket'); curtain(-13, -10.2, y, z + 1.1); }
    for (const z of [-15, 0]) { B.box(-20, y + 0.45, z, 0.6, 0.9, 1.4, 'metal'); D.add(-20.25, y + 0.9, z - 0.5, -19.75, y + 1.0, z + 0.5, 'white'); } // a trolley of things you don't want to know about
  }
  // ---- BACK CORRIDOR: a gurney parked badly
  B.box(-6, 0.45, -12.2, 2, 0.9, 0.8, 'sheet'); D.add(-7, 0.9, -12.6, -5, 0.96, -11.8, 'blanket');
  // ---- MORGUE: the drawers, two slabs, the backup generator. the power switch on the east wall
  B.add(11.5, 0, -23.6, 18, 2.4, -22.8, 'morgue');
  for (const x of [15.5, 21.5]) { B.box(x, 0.45, -13, 2.2, 0.9, 0.9, 'metal'); D.add(x - 1, 0.9, -13.4, x + 1, 1.05, -12.6, 'sheet'); }
  B.add(23.5, 0, -22.5, 28, 2.2, -19.5, 'metal'); B.add(26.6, 2.2, -21.6, 27.4, F - T, -20.8, 'pipe'); D.add(23.44, 0.5, -22, 23.5, 1.7, -20, 'hazard');
  const power = { at: [29.7, 1.6, -9], n: [-1, 0, 0] };
  B.add(29.6, 1.0, -9.5, 30, 2.2, -8.5, 'metal');
  // ---- X-RAY: the table and its arm, a lead screen. the mystery crate
  B.box(16, 0.45, 3, 2.4, 0.9, 1.0, 'metal'); B.add(15.6, 0, 4.2, 16.4, 2.7, 4.7, 'metal'); D.add(15.5, 2.4, 2.4, 16.5, 2.7, 4.2, 'metal'); D.add(15.3, 1.9, 2.5, 16.7, 2.4, 3.5, 'carwhite');
  B.add(20.5, 0, 0.5, 20.7, 2, 4, 'glassblock');
  const crate = { at: [16, 0, 15], price: 950 };
  B.add(15.1, 0, 14.55, 16.9, 0.9, 15.45, 'crate');
  // ---- UPSTAIRS CORRIDOR: benches
  for (const x of [-4, 3]) B.add(x - 1.5, F, -13.2, x + 1.5, F + 0.45, -12.6, 'blue');
  // ---- CHILDREN'S WARD: small beds, building blocks, a play mat
  for (const z of [18, 21.6]) bed(-28.9, F, z, 1, 'yellow', 1.6);
  for (const z of [10.5, 21]) bed(-11.2, F, z, -1, 'pink', 1.6);
  for (const [x, z, s, m] of [[-18, 13, 0.9, 'dyemagenta'], [-17.2, 13.6, 0.6, 'dyeyellow'], [-21, 16, 0.7, 'dyeblue']]) B.box(x, F + s / 2, z, s, s, s, m);
  D.add(-24, F, 10, -16, F + 0.02, 18, 'pink'); D.add(-18.2, F + 0.9, 12.8, -17.8, F + 1.3, 13.2, 'dyemint');
  // ---- STAFF LOUNGE: a sofa that has seen things, a table, the coffee machine
  B.box(-6, F + 0.35, 22.4, 4, 0.7, 1.2, 'carred'); D.add(-8, F + 0.7, 22.75, -4, F + 1.2, 23, 'carred');
  B.box(4.5, F + 0.4, 13, 2.2, 0.8, 2.2, 'wood'); B.add(-9.7, F, 8, -9.1, F + 1.3, 9.6, 'metal'); D.add(-9.1, F + 0.9, 8.4, -8.95, F + 1.15, 8.9, 'carblack');
  for (const [x, z] of [[3.6, 12.6], [5.2, 13.5]]) D.add(x - 0.1, F + 0.8, z - 0.1, x + 0.1, F + 0.98, z + 0.1, 'white'); // mugs
  // ---- OPERATING THEATRE: the table, the big lamp, a trolley, scrub sinks
  B.box(20, F + 0.5, -15, 1.1, 1.0, 2.4, 'sheet'); D.add(19.4, F + 1.0, -16.3, 20.6, F + 1.06, -13.7, 'mint');
  D.add(19.9, F + 3.4, -15.1, 20.1, H, -14.9, 'metal'); D.add(19, F + 3.1, -16, 21, F + 3.4, -14, 'carwhite'); D.add(19.3, F + 3.06, -15.7, 20.7, F + 3.1, -14.3, 'light');
  B.box(22.6, F + 0.45, -16, 0.8, 0.9, 0.5, 'metal'); D.add(22.3, F + 0.9, -16.2, 22.9, F + 0.93, -15.8, 'white');
  B.add(24, F, -6.8, 28, F + 0.9, -6.2, 'metal'); D.add(24.3, F + 0.9, -6.7, 25.3, F + 0.94, -6.3, 'tile'); D.add(26.7, F + 0.9, -6.7, 27.7, F + 0.94, -6.3, 'tile');
  // ---- INTENSIVE CARE: beds with a monitor each
  for (const z of [8, 12.5, 17]) { bed(18, F, z, 1, 'blanket'); B.box(16.4, F + 0.6, z + 0.9, 0.4, 1.2, 0.4, 'metal'); D.add(16.15, F + 1.2, z + 0.65, 16.65, F + 1.6, z + 1.15, 'ecg', { fit: 1 }); }

  // ---- dressing (look-only): signs, the wall rail, lightboxes
  sg('x', 23.77, 0, 3.6, 7, 0.9, 'sgnhosp'); // over the front windows, inside
  sg('x', 6.23, 0, 6.6, 8, 1.3, 'sgner'); // on the lounge wall, facing the waiting room
  D.add(-1.6, 2.9, 2.02, 1.6, 3.9, 2.08, 'sgnwait', { fit: 1 }); D.add(-1.6, 2.9, -2.08, 1.6, 3.9, -2.02, 'sgnbridge', { fit: 1 }); // hung off the bridge
  sg('z', -9.77, 15, 3.56, 3, 0.56, 'sgnpharm'); sg('z', -9.77, -2, 3.56, 3, 0.56, 'sgnwarda'); sg('z', 9.77, 15, 3.56, 3, 0.56, 'sgnxray');
  sg('x', -9.77, 0, 3.56, 3, 0.56, 'sgnramp'); sg('z', 9.77, -17, 3.56, 3, 0.56, 'sgnmorgue');
  sg('z', 9.77, 9.5, 2.0, 1.4, 2.0, 'eyechart'); sg('z', -9.77, 8.5, 2.2, 2.6, 0.7, 'sgnwash');
  sg('x', 5.77, -16, 2.4, 3, 0.75, 'sgnquiet'); sg('x', -23.97, -12, F + 2.4, 3, 0.75, 'sgnquiet');
  sg('z', 29.97, -17.5, 2.9, 3.4, 0.85, 'sgngen');
  for (const x of [13, 15.5, 24]) sg('x', -5.77, x, 2.0, 1.3, 1.75, 'xraylit');
  sg('z', -9.77, -13, F + 3.56, 3, 0.56, 'sgnwardb'); sg('z', 9.77, -13, F + 3.56, 3.4, 0.56, 'sgnsurg'); sg('z', -10.23, 15, F + 3.56, 3, 0.56, 'sgnstaff');
  sg('z', 9.77, 0, F + 3.56, 3, 0.56, 'sgnicu'); sg('x', 5.77, -20, F + 3.56, 3, 0.56, 'sgnkids');
  sg('x', 6.23, -14, F + 1.9, 7, 2.4, 'mural'); sg('z', 10.23, -9, F + 2.2, 2.6, 0.7, 'sgnwash');
  // the mint bumper rail round the corridors (wheelchair height)
  for (const y of [0, F]) { D.add(-9.8, y + 0.9, -10.26, -2.2, y + 1.05, -10.2, 'mint'); D.add(2.2, y + 0.9, -10.26, 9.8, y + 1.05, -10.2, 'mint'); }
  D.add(-9.8, 0.9, -9.8, -9.74, 1.05, -4.2, 'mint'); D.add(9.74, 0.9, -9.8, 9.8, 1.05, 12.8, 'mint'); D.add(-9.8, 0.9, 0.2, -9.74, 1.05, 5.4, 'mint');
  // a wheelchair by the ramp, an IV stand that got left behind
  D.add(6.6, 0.45, -18.4, 7.2, 0.52, -17.8, 'carblack'); D.add(6.6, 0.52, -18.4, 6.66, 1.1, -17.8, 'carblack'); for (const z of [-18.46, -17.78]) D.add(6.55, 0.05, z, 7.15, 0.65, z + 0.04, 'tire');
  D.add(-3.03, 0, -11.53, -2.97, 1.9, -11.47, 'metal'); D.add(-3.25, 0, -11.55, -2.75, 0.05, -11.45, 'metal'); D.add(-3.1, 1.55, -11.6, -2.9, 1.9, -11.4, 'greenglass');

  // ---- the machines. Jank Cola by the front doors; one more cola per wing
  const cola = { at: [9.25, 0, 21], n: [-1, 0, 0] };
  const colas = [
    { id: 'getup', at: [-29.25, 0, 9], n: [1, 0, 0] }, { id: 'legday', at: [9.25, 0, -12], n: [-1, 0, 0] },
    { id: 'pockets', at: [-29.25, F, 9], n: [1, 0, 0] }, { id: 'thirdhand', at: [9.25, F, 21], n: [-1, 0, 0] },
  ];
  for (const c of [cola, ...colas]) B.add(c.at[0] - 0.35, c.at[1], c.at[2] - 0.55, c.at[0] + 0.35, c.at[1] + 2.03, c.at[2] + 0.55, 'metal'); // a bit inside the model
  const mach = { at: [-14, F, -23.4], n: [0, 0, 1] }; // the Cheat Machine: Ward B's north wall
  B.add(-14.5, F, -23.77, -13.5, F + 1.28, -23.05, 'metal'); B.add(-14.5, F + 1.28, -23.77, -13.5, F + 2.12, -23.18, 'metal');
  const upm = { at: [16, F, -23.5], n: [0, 0, 1] }; // the Warranty Voider: it operates in the theatre
  B.add(15.15, F, -23.97, 16.85, F + 0.93, -22.96, 'metal'); B.add(15.15, F + 0.93, -23.97, 16.85, F + 2.28, -23.4, 'metal');

  // ---- wall guns
  const buys = [
    { w: 'revolver', price: 300, at: [-9.79, 1.55, 10.5], n: [1, 0, 0] },
    { w: 'smg', price: 900, at: [9.79, 1.55, 10.5], n: [-1, 0, 0] },
    { w: 'bread', price: 600, at: [-14, 1.55, 23.79], n: [0, 0, -1] },
    { w: 'shotgun', price: 1200, at: [-10.21, 1.55, -14.5], n: [-1, 0, 0] },
    { w: 'banana', price: 750, at: [18, 1.55, -5.79], n: [0, 0, 1] },
    { w: 'lever', price: 1100, at: [6, 1.55, -10.21], n: [0, 0, -1] },
    { w: 'autoshot', price: 1400, at: [26, 1.55, -6.21], n: [0, 0, -1] },
    { w: 'ar', price: 1200, at: [9.79, F + 1.55, -18.5], n: [-1, 0, 0] },
    { w: 'bow', price: 1000, at: [-14, F + 1.55, 23.79], n: [0, 0, -1] },
    { w: 'burst', price: 1300, at: [-29.79, F + 1.55, -7], n: [1, 0, 0] },
    { w: 'sniper', price: 1500, at: [14, F + 1.55, -5.79], n: [0, 0, 1] },
    { w: 'katana', price: 2000, at: [29.79, F + 1.55, -9], n: [-1, 0, 0] },
  ];
  const spawns = [[-4, 0.1, 20], [4, 0.1, 20], [-6, 0.1, 15], [6, 0.1, 15], [0, 0.1, 21], [-3, 0.1, 12], [3, 0.1, 12], [0, 0.1, 16]];
  return {
    name: 'Second Opinion General', size: 'medium', boxes: B.boxes, deco: D.boxes, killY: -20,
    sky: { top: 0x08101a, mid: 0x16283a, bot: 0x060a10, fog: 0x101c26 }, fogNear: 18, fogFar: 90, spawns,
    zm: { bounds: [X0 - 4, Z0 - 4, X1 + 4, Z1 + 4], H, start: 'er', floors: [0, F], areas, doors, windows, buys, crate, power, cola, mach, colas, up: upm,
      skins: ['patient', 'nurse', 'surgeon'] },
  };
}

MAPS.hospital = hospital();
unstick(MAPS.hospital.boxes, MAPS.hospital.spawns);
if (!MAP_ORDER.includes('hospital')) MAP_ORDER.push('hospital');
