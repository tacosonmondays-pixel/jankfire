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

  // ---- furniture: Blender pieces from p_hospkit.glb (tools/blender/make_hospkit.py). each keeps its box here: that's what
  // you bump into, and what you see if the model isn't in. K(piece, x, z, quarter turns, floor height) -> the boxes' tag
  const K = (v, x, z, r = 0, y = 0) => W.P('hospkit', x, z, r, { v, y });
  const small = (v, x, z, r, y, w, h, mat = 'metal') => B.box(x, y + h / 2, z, w, h, w, mat, K(v, x, z, r, y)); // poles, plants, wheelchairs
  const bed = (x, y, z, dx, v = 'bed', len = 2.1) => B.box(x, y + 0.3, z, len, 0.6, 1.0, 'sheet', K(v, x, z, dx > 0 ? 0 : 2, y)); // dx: which way the feet point
  const curtain = (x, y, z, r) => { W.P('hospkit', x, z, r, { v: 'curtain', y }); }; // (you walk through curtains)
  const chairs = (x, y, z, r) => (r & 1 ? B.box(x, y + 0.25, z, 0.7, 0.5, 5, 'blue', K('chairs', x, z, r, y)) : B.box(x, y + 0.25, z, 5, 0.5, 0.7, 'blue', K('chairs', x, z, r, y)));
  // ---- EMERGENCY: the front desk, pillars under the lounge's edge, the waiting room's seats (the bridge overhead)
  for (const x of [-2, 0, 2]) B.add(x - 1, 0, 6.7, x + 1, 1.1, 7.9, 'white', K('counter', x, 7.3));
  for (const x of [-7, 7]) B.add(x - 0.4, 0, 5.6, x + 0.4, F - T, 6.4, 'plaster');
  B.add(-10, F - T, 5.8, 10, F, 6.2, 'plaster');
  for (const z of [-7, 3.6]) for (const x of [-5.5, 5.5]) chairs(x, 0, z, 0);
  chairs(5.5, 0, -3.5, 0); chairs(-5.5, 0, 0.9, 0);
  for (const [x, z] of [[-9, -9], [9, -9], [-9, 23.2], [9, 23.3]]) B.box(x, 0.4, z, 0.9, 0.8, 0.9, 'brick', K('planter', x, z)); // plants doing better than the patients
  B.box(-8.6, 0.45, 20, 0.8, 0.9, 2, 'sheet', K('gurney', -8.6, 20, 1)); small('wheelchair', -7, 11.6, 1, 0, 0.7, 1.0, 'carblack'); small('ivstand', 8.6, 12.4, 0, 0, 0.5, 1.9);
  // ---- PHARMACY: the counter, shelves of pills behind it, somewhere to wait for your number
  for (let x = -23; x < -14; x += 2) B.add(x - 1, 0, 12.6, x + 1, 1.1, 13.8, 'white', K('counter', x, 13.2, 2));
  for (const x of [-27, -22.5, -17]) for (const z of [17.25, 18.75, 20.25]) B.add(x - 0.35, 0, z - 0.75, x + 0.35, 2.2, z + 0.75, 'pills', K('pillshelf', x, z, 1));
  chairs(-14, 0, 6.9, 0); B.box(-11, 0.4, 23, 0.9, 0.8, 0.9, 'brick', K('planter', -11, 23)); small('wheelchair', -27.5, 10.5, 3, 0, 0.7, 1.0, 'carblack');
  for (const z of [17.25, 18.75, 20.25]) B.add(-12.85, 0, z - 0.75, -12.15, 2.2, z + 0.75, 'pills', K('pillshelf', -12.5, z, 1)); chairs(-26, 0, 6.9, 0);
  // ---- the wards: beds down the walls, a curtain and a monitor each
  for (const y of [0, F]) { // Ward A, and Ward B straight above it
    for (const z of [-21.5, -10, 2]) { bed(-28.6, y, z, 1); curtain(-28.4, y, z + 1.1, 0); small('monitor', -29.3, z - 0.9, 3, y, 0.5, 1.3); }
    for (const z of [-21, -7.5]) { bed(-11.4, y, z, -1); curtain(-11.6, y, z + 1.1, 2); small('ivstand', -10.6, z - 0.9, 0, y, 0.5, 1.9); }
    for (const z of [-15, 0]) B.box(-20, y + 0.45, z, 0.5, 0.9, 0.8, 'metal', K('trolley', -20, z, 1, y)); // a trolley of things you don't want to know about
    for (const z of [-18, -12, -6]) { bed(-21.1, y, z, -1); bed(-18.9, y, z, 1); small('ivstand', -20, z + 0.75, 0, y, 0.5, 1.9); curtain(-21.2, y, z + 1.3, 0); curtain(-18.8, y, z + 1.3, 2); } // an island of beds down the middle
    for (const x of [-15, -13]) B.add(x - 1, y, 2.9, x + 1, y + 1.1, 4.1, 'white', K('counter', x, 3.5, 2, y)); small('monitor', -16.6, 3.5, 2, y, 0.5, 1.3); // the nurses' station
    small('wheelchair', -19, 4.4, 2, y, 0.7, 1.0, 'carblack'); B.box(-15.5, y + 0.45, -22.6, 2, 0.9, 0.8, 'sheet', K('gurney', -15.5, -22.6, 0, y));
    B.add(-24.5, y, 5.1, -21.5, y + 0.45, 5.7, 'blue', K('bench', -23, 5.4, 0, y));
  }
  // ---- BACK CORRIDOR: a gurney parked badly, a wheelchair by the ramp, an IV stand that got left behind
  B.box(-6, 0.45, -12.2, 2, 0.9, 0.8, 'sheet', K('gurney', -6, -12.2));
  small('wheelchair', 6.9, -18.1, 1, 0, 0.7, 1.0, 'carblack'); small('ivstand', -3, -11.5, 0, 0, 0.5, 1.9); B.add(-9.8, 0, -14.5, -9.2, 0.45, -11.5, 'blue', K('bench', -9.5, -13, 1));
  // ---- MORGUE: the drawers, two slabs, the backup generator. the power switch on the east wall
  for (let k = 0; k < 5; k++) B.add(11.5 + k * 1.3, 0, -23.6, 12.8 + k * 1.3, 2.4, -22.8, 'morgue', K('morgue', 12.15 + k * 1.3, -23.2));
  for (const x of [15.5, 21.5]) B.box(x, 0.45, -13, 2.2, 0.9, 0.9, 'metal', K('slab', x, -13));
  { const t = K('generator', 25.75, -21); B.add(23.5, 0, -22.5, 28, 2.2, -19.5, 'metal', t); B.add(26.6, 2.2, -21.6, 27.4, F - T, -20.8, 'pipe', t); }
  const power = { at: [29.7, 1.6, -9], n: [-1, 0, 0] };
  B.add(29.6, 1.0, -9.5, 30, 2.2, -8.5, 'metal');
  B.box(18.5, 0.45, -16.5, 0.8, 0.9, 0.5, 'metal', K('trolley', 18.5, -16.5)); B.add(11, 0, -7.1, 14, 0.45, -6.5, 'blue', K('bench', 12.5, -6.8));
  for (const [x, z] of [[15.5, -9.5], [21.5, -17]]) B.box(x, 0.45, z, 2.2, 0.9, 0.9, 'metal', K('slab', x, z));
  for (let k = 0; k < 4; k++) B.add(10.2, 0, -13.3 + k * 1.3, 11, 2.4, -12 + k * 1.3, 'morgue', K('morgue', 10.6, -12.65 + k * 1.3, 3)); // more drawers down the west wall
  B.box(24, 0.45, -10.5, 2, 0.9, 0.8, 'sheet', K('gurney', 24, -10.5)); B.box(25, 0.45, -16.5, 2, 0.9, 0.8, 'sheet', K('gurney', 25, -16.5)); B.box(13, 0.45, -15.5, 0.8, 0.9, 0.5, 'metal', K('trolley', 13, -15.5));
  B.add(14.5, 0, -6.8, 16.5, 0.9, -6.2, 'metal', K('scrubsink', 15.5, -6.5, 2));
  // ---- X-RAY: the table and its arm, a lead screen, seats. the mystery crate
  { const t = K('xray', 16, 3.65, 2); B.box(16, 0.45, 3, 2.4, 0.9, 1.0, 'metal', t); B.add(15.6, 0, 4.2, 16.4, 2.7, 4.7, 'metal', t); }
  B.add(20.5, 0, 0.5, 20.7, 2, 4, 'glassblock');
  chairs(13.5, 0, 23.3, 2); small('wheelchair', 23, 21, 0, 0, 0.7, 1.0, 'carblack'); B.box(24, 0.45, -4.6, 2, 0.9, 0.8, 'sheet', K('gurney', 24, -4.6)); small('monitor', 18.6, 5.4, 2, 0, 0.5, 1.3);
  { const t = K('xray', 22, 10); B.box(22, 0.45, 10.65, 2.4, 0.9, 1.0, 'metal', t); B.add(21.6, 0, 8.95, 22.4, 2.7, 9.45, 'metal', t); } // a second bay
  B.add(21.9, 0, 1.2, 23.1, 1.1, 3.2, 'white', K('counter', 22.5, 2.2, 1)); chairs(10.6, 0, 7, 3); B.add(25, 0, 23.1, 28, 0.45, 23.7, 'blue', K('bench', 26.5, 23.4));
  for (const z of [-5, -3.5]) B.add(29.05, 0, z - 0.75, 29.75, 2.2, z + 0.75, 'pills', K('pillshelf', 29.4, z, 1)); curtain(12.6, 0, 19.5, 0); curtain(12.6, 0, 11.5, 0);
  const crate = { at: [16, 0, 15], price: 950 };
  B.add(15.1, 0, 14.55, 16.9, 0.9, 15.45, 'crate');
  // ---- UPSTAIRS CORRIDOR: benches, a plant, a wheelchair somebody walked away from
  for (const x of [-4, 3]) B.add(x - 1.5, F, -13.2, x + 1.5, F + 0.45, -12.6, 'blue', K('bench', x, -12.9, 0, F));
  B.box(-9.2, F + 0.4, -11.2, 0.9, 0.8, 0.9, 'brick', K('planter', -9.2, -11.2, 0, F)); small('wheelchair', 7, -17, 3, F, 0.7, 1.0, 'carblack');
  B.box(7.5, F + 0.45, -13, 2, 0.9, 0.8, 'sheet', K('gurney', 7.5, -13, 0, F)); B.box(9.2, F + 0.4, -23, 0.9, 0.8, 0.9, 'brick', K('planter', 9.2, -23, 0, F));
  // ---- CHILDREN'S WARD: small beds, building blocks, a play mat, a little table
  for (const z of [18, 21.6]) bed(-28.9, F, z, 1, 'kidbed', 1.6);
  for (const z of [10.5, 21]) bed(-11.2, F, z, -1, 'kidbed', 1.6);
  for (const [x, z, s, m] of [[-18, 13, 0.9, 'dyemagenta'], [-17.2, 13.6, 0.6, 'dyeyellow'], [-21, 16, 0.7, 'dyeblue']]) B.box(x, F + s / 2, z, s, s, s, m);
  D.add(-24, F, 10, -16, F + 0.02, 18, 'pink'); D.add(-18.2, F + 0.9, 12.8, -17.8, F + 1.3, 13.2, 'dyemint');
  B.box(-15, F + 0.4, 20.5, 2.2, 0.8, 2.2, 'wood', K('table', -15, 20.5, 0, F)); chairs(-25.2, F, 6.9, 0); B.box(-28.9, F + 0.4, 11.5, 0.9, 0.8, 0.9, 'brick', K('planter', -28.9, 11.5, 0, F));
  bed(-11.2, F, 18.6, -1, 'kidbed', 1.6); B.box(-25.5, F + 0.4, 20, 2.2, 0.8, 2.2, 'wood', K('table', -25.5, 20, 0, F)); B.add(-14.5, F, 6.6, -11.5, F + 0.45, 7.2, 'blue', K('bench', -13, 6.9, 0, F));
  // ---- STAFF LOUNGE: a sofa that has seen things, a table, the coffee machine
  B.box(-6, F + 0.35, 22.4, 4, 0.7, 1.2, 'carred', K('sofa', -6, 22.4, 2, F));
  B.box(4.5, F + 0.4, 13, 2.2, 0.8, 2.2, 'wood', K('table', 4.5, 13, 0, F)); B.add(-9.7, F, 8, -9.1, F + 1.3, 9.6, 'metal', K('coffee', -9.4, 8.8, 0, F));
  B.box(9, F + 0.4, 7, 0.9, 0.8, 0.9, 'brick', K('planter', 9, 7, 0, F)); B.add(4, F, 23.1, 7, F + 0.45, 23.7, 'blue', K('bench', 5.5, 23.4, 0, F));
  B.box(-4, F + 0.4, 12.5, 2.2, 0.8, 2.2, 'wood', K('table', -4, 12.5, 0, F)); B.box(3, F + 0.35, 7, 4, 0.7, 1.2, 'carred', K('sofa', 3, 7, 0, F)); B.add(-6, F, 6.4, -4, F + 1.1, 7.6, 'white', K('counter', -5, 7, 0, F)); chairs(9.4, F, 10.2, 1);
  // ---- OPERATING THEATRE: the table, the big lamp, a trolley, scrub sinks
  B.box(20, F + 0.5, -15, 1.1, 1.0, 2.4, 'sheet', K('optable', 20, -15, 0, F)); W.P('hospkit', 20, -15, 0, { v: 'oplamp', y: F });
  B.box(22.6, F + 0.45, -16, 0.8, 0.9, 0.5, 'metal', K('trolley', 22.6, -16, 0, F));
  for (const x of [25, 27]) B.add(x - 1, F, -6.8, x + 1, F + 0.9, -6.2, 'metal', K('scrubsink', x, -6.5, 2, F));
  small('monitor', 18.4, -16.6, 0, F, 0.5, 1.3); small('ivstand', 21.4, -13.4, 0, F, 0.5, 1.9); B.box(12.5, F + 0.45, -22, 2, 0.9, 0.8, 'sheet', K('gurney', 12.5, -22, 0, F));
  for (const z of [-9.2, -7.7]) B.add(10.25, F, z - 0.75, 10.95, F + 2.2, z + 0.75, 'pills', K('pillshelf', 10.6, z, 1, F)); // supplies
  for (const x of [13, 15]) B.add(x - 1, F, -6.8, x + 1, F + 0.9, -6.2, 'metal', K('scrubsink', x, -6.5, 2, F));
  B.box(26, F + 0.45, -17.5, 2.2, 0.9, 0.9, 'metal', K('slab', 26, -17.5, 0, F)); B.box(25.5, F + 0.45, -11, 2, 0.9, 0.8, 'sheet', K('gurney', 25.5, -11, 0, F)); B.box(17.4, F + 0.45, -13.6, 0.8, 0.9, 0.5, 'metal', K('trolley', 17.4, -13.6, 0, F)); B.add(24.5, F, -22.9, 27.5, F + 0.45, -22.3, 'blue', K('bench', 26, -22.6, 0, F));
  // ---- INTENSIVE CARE: beds with a monitor and a drip each, seats for whoever is waiting
  for (const z of [8, 12.5, 17]) { bed(18, F, z, 1); small('monitor', 16.4, z + 0.9, 3, F, 0.5, 1.3); small('ivstand', 16.5, z - 0.85, 0, F, 0.5, 1.9); curtain(18.2, F, z + 1.7, 0); }
  chairs(10.6, F, 7.5, 3); B.box(24.5, F + 0.45, -3, 0.8, 0.9, 0.5, 'metal', K('trolley', 24.5, -3, 0, F));
  for (const z of [8, 12.5, 17]) { bed(23, F, z, -1); small('monitor', 24.9, z + 0.9, 1, F, 0.5, 1.3); curtain(22.8, F, z + 1.7, 2); } // a second row, heads to the stairwell wall
  for (const x of [20, 22]) B.add(x - 1, F, -3.1, x + 1, F + 1.1, -1.9, 'white', K('counter', x, -2.5, 0, F)); // the nurses' station

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
