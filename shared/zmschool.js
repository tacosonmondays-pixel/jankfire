// ------------------------------------------------------------ JANKFIELD HIGH: a zombies map on two floors.
// ground floor: the entrance lobby (start), the cafeteria, a locker corridor with the main stairs, a science lab, the
// boiler room (the power) and a double-height gym. upstairs: the long corridor, the library, the art room, the
// principal's office (the Warranty Voider) and a balcony over the gym with bleacher steps down into it. two ways up
// (the main stairs, the bleachers), so there's a loop through both floors to drag a crowd round. every floor is flat;
// the only height is real steps (0.45 m a metre: zombies and bots walk them on the nav grid, server/zombies.js).
// windows on both floors open onto boarded ledges the zombies climb in from. `zm` is read by the zombies mode.
import { MAPS, MAP_ORDER, builder, wall, stairs, unstick } from './map.js';

function school() {
  const B = builder(), D = builder(); // D: looked at, never bumped into (signs, chalkboards, the court)
  const W = B.local(0, 0, 0);
  const F = 4.5, H = 9, T = 0.4; // floor to floor, the roof, slab thickness
  const X0 = -30, X1 = 30, Z0 = -24, Z1 = 24;
  const up = (y) => (y > 1 ? 1 : 0);
  // a panel flat on a wall. axis 'x': the wall runs along x at z = at (it faces +-z); 'z': along z at x = at
  const sg = (axis, at, c, y, w, h, mat) => (axis === 'x' ? D.add(c - w / 2, y - h / 2, at - 0.03, c + w / 2, y + h / 2, at + 0.03, mat, { fit: 1 }) : D.add(at - 0.03, y - h / 2, c - w / 2, at + 0.03, y + h / 2, c + w / 2, mat, { fit: 1 }));
  const areas = [
    { id: 'lobby', name: 'Main Entrance', r: [-8, 8, 8, 24], y: [0, F - T], floor: 'tile' },
    { id: 'cafe', name: 'Cafeteria', r: [-30, 0, -8, 24], y: [0, F - T], floor: 'tile' },
    { id: 'lockers', name: 'Locker Hall', r: [-8, -24, 8, 8], y: [0, F - T], floor: 'stone' },
    { id: 'lab', name: 'Science Lab', r: [-30, -24, -8, 0], y: [0, F - T], floor: 'tile' },
    { id: 'boiler', name: 'Boiler Room', r: [8, -24, 30, -4], y: [0, F - T], floor: 'concrete' },
    { id: 'gym', name: 'Gym', r: [8, -4, 30, 24], y: [0, F - T], floor: 'wood' },
    { id: 'lockers', name: 'Locker Hall', r: [-3, -14.5, 3, -12], y: [F - 0.2, H], part: 1 }, // the top of the main stairs, this side of its shutter
    { id: 'upper', name: 'Upstairs Hall', r: [-8, -24, 8, 24], y: [F - 0.2, H], floor: 'carpet' },
    { id: 'library', name: 'Library', r: [-30, 0, -8, 24], y: [F - 0.2, H], floor: 'carpet' },
    { id: 'art', name: 'Art Room', r: [-30, -24, -8, 0], y: [F - 0.2, H], floor: 'wood' },
    { id: 'office', name: 'Principal\'s Office', r: [8, -24, 30, -4], y: [F - 0.2, H], floor: 'carpet' },
    { id: 'gym', name: 'Gym', r: [8, -4, 15.5, 24], y: [F - 0.2, H], part: 1 }, // its balcony: you walk up the bleachers, no door
  ];
  // ---- floors and ceilings. the ground everywhere; the upstairs slab over everything but the gym (a hole for the main stairs)
  for (const a of areas) if (!up(a.y[0]) && !a.part) B.add(a.r[0], -0.4, a.r[1], a.r[2], 0, a.r[3], a.floor);
  const STAIR = [-3, -13, 3, -3]; // the stairwell: x0, z0, x1, z1 (steps climb toward -z)
  for (const a of areas) {
    if (!up(a.y[0]) || a.part) continue;
    const [x0, z0, x1, z1] = a.r;
    if (a.id !== 'upper') { B.add(x0, F - T, z0, x1, F, z1, a.floor); continue; }
    B.add(x0, F - T, z0, STAIR[0], F, z1, a.floor); B.add(STAIR[2], F - T, z0, x1, F, z1, a.floor);
    B.add(STAIR[0], F - T, z0, STAIR[2], F, STAIR[1], a.floor); B.add(STAIR[0], F - T, STAIR[3], STAIR[2], F, z1, a.floor);
  }
  B.add(X0, H, Z0, X1, H + 0.4, Z1, 'roofg'); // the roof
  // ---- the main stairs: ten 1 m steps up the middle of the locker hall, railings round the hole upstairs
  stairs(W, STAIR[0], STAIR[2], STAIR[3], -1, 0, F, 'wood', 1);
  // (glass to the ceiling, not a rail: no hopping down into a locker hall nobody has opened, where zombies can't follow)
  B.add(STAIR[0] - 0.15, F, STAIR[1] + 1, STAIR[0], H, STAIR[3] + 0.15, 'hospglass'); B.add(STAIR[2], F, STAIR[1] + 1, STAIR[2] + 0.15, H, STAIR[3] + 0.15, 'hospglass');
  B.add(STAIR[0], F, STAIR[3], STAIR[2], H, STAIR[3] + 0.15, 'hospglass');
  for (const [x0, z0, x1, z1] of [[STAIR[0] - 0.17, STAIR[1] + 1, STAIR[0] + 0.02, STAIR[3] + 0.17], [STAIR[2] - 0.02, STAIR[1] + 1, STAIR[2] + 0.17, STAIR[3] + 0.17], [STAIR[0], STAIR[3] - 0.02, STAIR[2], STAIR[3] + 0.17]]) D.add(x0, F + 1.0, z0, x1, F + 1.08, z1, 'metal'); // a handrail on it
  // ---- the gym balcony (a 4 m walkway down the west side) and the bleacher steps up to it
  B.add(8, F - T, -4, 12, F, 24, 'wood');
  B.add(12, F - T, 6, 15, F, 10, 'wood'); // the landing at the top of the bleachers
  stairs(W, 12, 15, 20, -1, 0, F, 'planks', 1); // from z 20 up to z 10
  B.add(12, F, -4, 12.15, F + 1.1, 6, 'metal'); B.add(12, F, 20, 12.15, F + 1.1, 24, 'metal'); // rail along the open edge
  B.add(15, F, 6, 15.15, F + 1.1, 10, 'metal'); B.add(12, F, 6, 15.15, F + 1.1, 6.15, 'metal');
  for (const z of [0, 14]) B.add(11.6, 0, z - 0.2, 12, F - T, z + 0.2, 'metal'); // posts under the walkway

  // ---- windows: an opening in the outside wall onto a boarded ledge the zombies come from (ground: a back alley)
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
  win('s', -4, 'lobby'); win('s', 4, 'lobby');
  win('w', 6, 'cafe'); win('w', 18, 'cafe'); win('s', -20, 'cafe');
  win('n', 5.5, 'lockers'); win('n', -5.5, 'lockers');
  win('w', -8, 'lab'); win('w', -18, 'lab'); win('n', -20, 'lab');
  win('e', -10, 'boiler'); win('n', 20, 'boiler');
  win('e', 4, 'gym'); win('e', 16, 'gym'); win('s', 22, 'gym');
  win('s', 0, 'upper', F); win('n', 0, 'upper', F);
  win('w', 12, 'library', F); win('s', -14, 'library', F);
  win('w', -12, 'art', F); win('n', -14, 'art', F);
  win('e', -16, 'office', F); win('n', 14, 'office', F);
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
    doors.push({ a, b, price, name: areas.find((x) => x.id === b).name, box, at: axis === 'z' ? [fixed, y0 + 1.5, c] : [c, y0 + 1.5, fixed] });
    B.add(box.min[0] - (axis === 'z' ? 0.11 : 0.1), y0 + 2.95, box.min[2] - (axis === 'z' ? 0.1 : 0.11), box.max[0] + (axis === 'z' ? 0.11 : 0.1), y0 + 3.3, box.max[2] + (axis === 'z' ? 0.1 : 0.11), 'hazard'); // its housing
    return { a: c - 2, b: c + 2, y0, y1: y0 + 3 };
  };
  const g0 = [0, F - T], g1 = [F, H];
  // ground floor
  const dLC = door('z', -8, 16, 'lobby', 'cafe', 750), dLG = door('z', 8, 16, 'lobby', 'gym', 1000), dLK = door('x', 8, 0, 'lobby', 'lockers', 750);
  const dKL = door('z', -8, -18, 'lockers', 'lab', 1000), dKB = door('z', 8, -18, 'lockers', 'boiler', 1250), dCL = door('x', 0, -19, 'cafe', 'lab', 1000);
  wall(W, 'z', -8, Z0, Z1, ...g0, 0.4, 'plaster', [dLC, dKL]);
  wall(W, 'z', 8, Z0, Z1, ...g0, 0.4, 'plaster', [dLG, dKB]);
  wall(W, 'x', 8, -8, 8, ...g0, 0.4, 'plaster', [dLK]);
  wall(W, 'x', 0, X0, -8, ...g0, 0.4, 'plaster', [dCL]);
  wall(W, 'x', -4, 8, X1, ...g0, 0.4, 'brick', []); // boiler room | gym
  // upstairs
  const dST = door('x', STAIR[1] - 1.5, 0, 'lockers', 'upper', 1250, F); // the shutter at the top of the main stairs
  wall(W, 'x', STAIR[1] - 1.5, STAIR[0], STAIR[2], ...g1, 0.3, 'plaster', [dST]); // the stairs come up into a little box: the shutter ahead,
  for (const x of [STAIR[0], STAIR[2]]) wall(W, 'z', x, STAIR[1] - 1.5, STAIR[1] + 1, ...g1, 0.3, 'plaster', []); // a wall either side (the hall runs past on both)
  const dUL = door('z', -8, 14, 'upper', 'library', 1000, F), dUA = door('z', -8, -6, 'upper', 'art', 1000, F), dUO = door('z', 8, -20, 'upper', 'office', 1500, F);
  const dUB = door('z', 8, 12, 'upper', 'gym', 1000, F), dLA = door('x', 0, -19, 'library', 'art', 750, F);
  wall(W, 'z', -8, Z0, Z1, ...g1, 0.4, 'plaster', [dUL, dUA]);
  wall(W, 'z', 8, Z0, Z1, ...g1, 0.4, 'plaster', [dUO, dUB]);
  wall(W, 'x', 0, X0, -8, ...g1, 0.4, 'plaster', [dLA]);
  wall(W, 'x', -4, 8, X1, ...g1, 0.4, 'brick', []); // office | the gym's upper half

  // ---- LOBBY: the reception desk, a trophy case, two pillars
  B.add(-2.5, 0, 17.5, 2.5, 1.1, 19, 'wood'); B.add(-0.4, 1.1, 17.9, 0.4, F - T, 18.7, 'plaster');
  for (const x of [-5.5, 5.5]) B.add(x - 0.4, 0, 11.6, x + 0.4, F - T, 12.4, 'plaster');
  B.add(-7.6, 0, 20.5, -7, 2, 23.5, 'glassblock');
  // ---- CAFETERIA: long tables in rows, the serving counter along the west wall
  for (const x of [-25, -19, -13]) for (const z of [6, 13, 20]) B.box(x, 0.4, z, 3.2, 0.8, 1.2, 'wood');
  B.add(-29.6, 0, 1, -28.4, 1.05, 4.4, 'tile'); B.add(-29.6, 1.05, 0.8, -28.2, 1.15, 4.6, 'metal');
  // ---- LOCKER HALL: lockers down both walls (the stairs fill the middle)
  for (const x of [-7.6, 7.1]) for (const [z0, z1] of [[-12, -4], [2, 6]]) B.add(x, 0, z0, x + 0.5, 2, z1, x < 0 ? 'lockerb' : 'lockerp');
  // ---- SCIENCE LAB: benches with sinks, a fume cupboard
  for (const x of [-25, -18, -11.5]) for (const z of [-18, -9]) B.box(x, 0.45, z, 3, 0.9, 1.4, 'metal');
  B.add(-29.6, 0, -23.6, -27, 2.2, -22.6, 'glassblock');
  // ---- BOILER ROOM: the boiler, pipes, crates. the power switch on the east wall
  B.add(18, 0, -22, 22, 2.6, -18, 'metal'); B.add(19.4, 2.6, -20.6, 20.6, F - T, -19.4, 'metal');
  for (const [x, z, n] of [[11, -7, 2], [12.3, -7, 1], [27, -22, 2], [26, -8, 1]]) for (let k = 0; k < n; k++) B.box(x, 0.6 + k * 1.2, z, 1.2, 1.2, 1.2, 'crate');
  const power = { at: [29.7, 1.6, -15], n: [-1, 0, 0] };
  B.add(29.6, 1.0, -15.5, 30, 2.2, -14.5, 'metal');
  // ---- GYM: the court, a vaulting box, mats. the mystery crate under the far hoop
  B.box(22, 0.5, 2, 1.6, 1, 0.8, 'wood'); B.box(26, 0.15, 18, 3, 0.3, 2, 'blue'); B.box(18, 0.15, -1, 3, 0.3, 2, 'pink');
  B.add(29.3, 2.6, 9, 29.9, 3.8, 11, 'backboard', { fit: 1 }); // the backboard
  const crate = { at: [27.5, 0, 10], price: 950 };
  B.add(26.6, 0, 9.55, 28.4, 0.9, 10.45, 'crate');
  // ---- UPSTAIRS HALL: benches, a vending corner
  for (const z of [4, 20]) B.add(-1.5, F, z - 0.3, 1.5, F + 0.45, z + 0.3, 'wood');
  // ---- LIBRARY: shelves you weave between, a reading table
  for (const x of [-26, -21, -16]) B.add(x - 0.35, F, 8, x + 0.35, F + 2.2, 20, 'books');
  B.box(-12, F + 0.4, 4, 2.4, 0.8, 1.4, 'wood'); B.box(-12, F + 0.4, 21, 2.4, 0.8, 1.4, 'wood');
  // ---- ART ROOM: easels, a kiln, a table of bad sculptures
  for (const [x, z] of [[-25, -8], [-20, -14], [-14, -9]]) B.box(x, F + 0.8, z, 0.9, 1.6, 0.2, 'wood');
  B.add(-29.6, F, -23.6, -28, F + 1.8, -22, 'brick'); B.box(-18, F + 0.4, -20, 3, 0.8, 1.4, 'yellow');
  for (const [x, z] of [[-24, -17], [-13, -15]]) B.box(x, F + 0.4, z, 2.6, 0.8, 1.2, 'wood'); // paint tables
  // ---- PRINCIPAL'S OFFICE: a desk that's too big, filing cabinets, a rug
  B.box(22, F + 0.45, -12, 3.4, 0.9, 1.6, 'wood'); B.add(28.9, F, -9, 29.6, F + 1.5, -6, 'metal');
  B.add(11, F, -23.6, 15, F + 2.2, -23, 'books'); B.box(22, F + 0.3, -9.6, 0.7, 0.6, 0.7, 'pink'); B.box(22, F + 0.5, -14.6, 0.9, 1.0, 0.9, 'carblack'); // a bookcase nobody read, the naughty stool, the big chair

  // ---- dressing (look-only): what makes each room read as its room
  sg('x', 8.23, 0, 3.62, 7, 0.9, 'sgnschool'); sg('z', -7.77, 22, 2.5, 2.8, 0.7, 'sgntrophy'); sg('z', 7.77, 19, 1.9, 1.6, 1.0, 'sgnprom');
  sg('x', 7.77, -5, 2.6, 3.4, 0.7, 'sgnhall'); // locker hall, by the lobby door
  sg('z', -29.97, 2.7, 2.5, 3.2, 1.2, 'sgnmenu'); sg('x', 0.23, -13, 2.7, 4, 0.8, 'sgnnorun');
  for (const x of [-25, -19, -13]) for (const z of [6, 13, 20]) for (const s of [-1, 1]) D.add(x - 1.5, 0.42, z + s * 0.95 - 0.18, x + 1.5, 0.5, z + s * 0.95 + 0.18, s < 0 ? 'blue' : 'pink'); // benches
  for (let k = 0; k < 4; k++) D.add(-29.3 + (k % 2) * 0.5, 1.15, 1.4 + k * 0.75, -29.0 + (k % 2) * 0.5, 1.19, 1.9 + k * 0.75, k % 2 ? 'pink' : 'yellow'); // trays nobody took back
  sg('x', -0.23, -13, 2.2, 4.2, 2.1, 'sgnperiodic'); sg('x', -23.97, -13, 2.1, 5, 2.2, 'chalk2'); sg('z', -29.97, -3, 2.1, 3.4, 1.7, 'chalk1'); sg('z', -8.23, -18, 3.55, 3, 0.56, 'sgnlab');
  for (const x of [-25, -18, -11.5]) for (const z of [-18, -9]) { D.add(x - 1.1, 0.9, z - 0.3, x - 0.5, 0.94, z + 0.3, 'tile'); D.add(x + 0.5, 0.9, z - 0.1, x + 0.7, 1.25, z + 0.1, 'greenglass'); D.add(x + 0.9, 0.9, z + 0.2, x + 1.05, 1.15, z + 0.35, 'pink'); } // a sink, a flask, a beaker
  sg('z', 8.23, -12, 2.5, 4.4, 1.1, 'sgnboiler');
  for (const z of [-23.4, -22.6]) D.add(9, 3.5, z - 0.12, 29, 3.74, z + 0.12, 'pipe'); D.add(20, 3.5, -22.6, 20.24, 3.74, -5, 'pipe'); // pipes off the boiler
  D.add(13, 0, -2, 29, 0.02, 22, 'court', { fit: 1 });
  for (const [a, b, c, d] of [[28.75, 9.7, 28.8, 10.3], [29.25, 9.7, 29.3, 10.3], [28.75, 9.7, 29.3, 9.75], [28.75, 10.25, 29.3, 10.3]]) D.add(a, 2.85, b, c, 2.9, d, 'hoop'); // the rim
  for (const [a, b, c, d] of [[28.78, 9.72, 28.8, 10.28], [29.25, 9.72, 29.27, 10.28], [28.78, 9.72, 29.27, 9.74], [28.78, 10.26, 29.27, 10.28]]) D.add(a, 2.4, b, c, 2.85, d, 'net');
  sg('x', -3.77, 21, 6.6, 7, 1.75, 'sgnchamps'); sg('z', 29.97, 10, 6.3, 5, 2, 'sgnscore');
  for (const z of [2, 10, 18]) { D.add(13.2, 8.1, z - 0.01, 28.8, 8.13, z + 0.01, 'white'); for (let x = 13.6, k = 0; x < 28.6; x += 0.9, k++) D.add(x - 0.25, 7.6 + (k % 2) * 0.12, z - 0.012, x + 0.25, 8.1, z + 0.012, ['pink', 'yellow', 'blue'][k % 3]); } // bunting from a pep rally that never ended
  sg('z', -7.77, 14, F + 3.56, 3, 0.56, 'sgnlib'); sg('z', -7.77, -6, F + 3.56, 3, 0.56, 'sgnart'); sg('z', 7.77, -20, F + 3.56, 3, 0.56, 'sgnprin');
  for (const z of [10, 16]) sg('z', 7.77, z === 10 ? 4 : -8, F + 1.9, 1.5, 1.1, z === 10 ? 'kidart2' : 'kidart3'); // the hall's wall of fame
  [[-25, -8], [-20, -14], [-14, -9]].forEach(([x, z], i) => D.add(x - 0.36, F + 0.95, z + 0.1, x + 0.36, F + 1.5, z + 0.13, 'kidart' + (i + 1), { fit: 1 }));
  sg('z', -29.97, -18.5, F + 2.1, 4, 2, 'chalk3'); for (const x of [-18.9, -18, -17.1]) D.add(x - 0.2, F + 0.8, -20.2, x + 0.2, F + 1.1 + (x + 19) * 0.25, -19.8, x < -18.5 ? 'pink' : x < -17.5 ? 'dyemint' : 'crate'); // sculptures (bad)
  for (const [x, z, m] of [[-24.6, -17, 'pink'], [-23.6, -16.8, 'dyemint'], [-13.4, -15.2, 'yellow'], [-12.6, -14.8, 'blue']]) D.add(x - 0.2, F + 0.8, z - 0.2, x + 0.2, F + 0.83, z + 0.2, m); // paint that will never dry
  sg('x', -4.23, 22, F + 2.3, 3, 1.5, 'sgndet'); D.add(19, F, -14.6, 25, F + 0.02, -9.4, 'carpetb'); D.add(21.6, F + 0.9, -12.3, 22.4, F + 0.94, -11.7, 'white'); // the list, a rug, paperwork

  // ---- the machines. colas: one per wing; Jank Cola by the gym door
  const cola = { at: [8.75, 0, 22], n: [1, 0, 0] };
  const colas = [
    { id: 'getup', at: [-7.25, 0, 10.5], n: [1, 0, 0] }, { id: 'legday', at: [-29.25, 0, 22], n: [1, 0, 0] },
    { id: 'pockets', at: [-29.25, F, 2], n: [1, 0, 0] }, { id: 'thirdhand', at: [7.25, F, 22], n: [-1, 0, 0] },
  ];
  for (const c of [cola, ...colas]) B.add(c.at[0] - 0.35, c.at[1], c.at[2] - 0.55, c.at[0] + 0.35, c.at[1] + 2.03, c.at[2] + 0.55, 'metal'); // a bit inside the model
  const mach = { at: [-19, F, -23.4], n: [0, 0, 1] }; // the Cheat Machine: the art room's north wall
  B.add(-19.5, F, -23.77, -18.5, F + 1.28, -23.05, 'metal'); B.add(-19.5, F + 1.28, -23.77, -18.5, F + 2.12, -23.18, 'metal');
  const upm = { at: [19, F, -23.5], n: [0, 0, 1] }; // the Warranty Voider: the principal's office
  B.add(18.15, F, -23.97, 19.85, F + 0.93, -22.96, 'metal'); B.add(18.15, F + 0.93, -23.97, 19.85, F + 2.28, -23.4, 'metal');

  // ---- wall guns
  const buys = [
    { w: 'revolver', price: 300, at: [-4.5, 1.55, 8.21], n: [0, 0, 1] },
    { w: 'smg', price: 900, at: [4.5, 1.55, 8.21], n: [0, 0, 1] },
    { w: 'bread', price: 600, at: [-29.79, 1.55, 12], n: [1, 0, 0] },
    { w: 'shotgun', price: 1200, at: [-7.79, 1.55, -1], n: [1, 0, 0] },
    { w: 'banana', price: 750, at: [29.79, 1.55, -1.5], n: [-1, 0, 0] },
    { w: 'lever', price: 1100, at: [-29.79, 1.55, -13], n: [1, 0, 0] },
    { w: 'autoshot', price: 1400, at: [14, 1.55, -4.21], n: [0, 0, -1] },
    { w: 'ar', price: 1200, at: [-7.79, F + 1.55, 2], n: [1, 0, 0] },
    { w: 'bow', price: 1000, at: [-18, F + 1.55, 23.79], n: [0, 0, -1] },
    { w: 'burst', price: 1300, at: [-29.79, F + 1.55, -6], n: [1, 0, 0] },
    { w: 'sniper', price: 1500, at: [8.21, F + 1.55, 2], n: [1, 0, 0] },
    { w: 'katana', price: 2000, at: [29.79, F + 1.55, -12], n: [-1, 0, 0] },
  ];
  const spawns = [[-4, 0.1, 21], [4, 0.1, 21], [-6, 0.1, 14], [6, 0.1, 14], [0, 0.1, 22], [-3, 0.1, 11], [3, 0.1, 11], [0, 0.1, 14]];
  return {
    name: 'Jankfield High', size: 'medium', boxes: B.boxes, deco: D.boxes, killY: -20,
    sky: { top: 0x0a0814, mid: 0x241a30, bot: 0x08060e, fog: 0x1a1424 }, fogNear: 18, fogFar: 90, spawns,
    zm: { bounds: [X0 - 4, Z0 - 4, X1 + 4, Z1 + 4], H, start: 'lobby', floors: [0, F], areas, doors, windows, buys, crate, power, cola, mach, colas, up: upm,
      skins: ['student', 'teacher', 'lunchlady'] },
  };
}

MAPS.school = school();
unstick(MAPS.school.boxes, MAPS.school.spawns);
if (!MAP_ORDER.includes('school')) MAP_ORDER.push('school');
