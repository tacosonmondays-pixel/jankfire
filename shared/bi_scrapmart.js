// SCRAP MART (Battle Island, west-centre: docs/maps/battleisland/DESIGN.md): the mech hangar and its scrapyard. The
// hangar is a barrel-roofed steel shed 40 x 32 m (the real size of a big maintenance hangar), Hangar Road running
// straight through it: both end doors are open (16+ m wide, 12 m high: two mechs pass), the mech docks along its north
// wall (two half-built mechs in their cradles), the overhead crane (an arm hanging off it), the parts office in the south
// corner with the catwalk over it (up the stairs by the east door), roof lights. Outside: the yard's portal crane (a car
// still on its magnet), stacks of crushed-car bales, the car crusher, burnt-out cars, tyre piles, the test range east of
// the shed (sandbag firing line, mech-size targets, a berm), the SCRAP MART pylon sign by the road. Every piece is a
// Blender model over its boxes (tools/blender/make_scrapmart.py reads its numbers from here with node), built at the
// ground's own height with its boxes `still`.
import { grid } from './battleisland.js';
import { propOf } from './propcap.js';
import { car } from './map.js';

const r3 = (v) => Math.round(v * 1000) / 1000;
const box6 = (a, b, c, d, e, f, m) => [r3(Math.min(a, d)), r3(Math.min(b, e)), r3(Math.min(c, f)), r3(Math.max(a, d)), r3(Math.max(b, e)), r3(Math.max(c, f)), m]; // (corners in any order)
export const SM = {
  hangar: { x0: -124, x1: -84, z0: 11, z1: 43, eave: 13, ridge: 19, t: 0.4, // the shed: its walls' outer faces, eave and ridge heights, wall thickness
    door: [18, 40.3, 12], // the end doors (both ends): z0, z1, top
    pilot: [-112.2, -110.8, 2.4], // the pilot door in the north wall: x0, x1, top
    strips: 16, roofT: 0.35 }, // the barrel roof in strips across (2 m each), its thickness
  mezz: { x0: -123.6, x1: -91.5, z0: 40.6, y: 6.0, t: 0.25, rail: 1.1 }, // the catwalk along the south wall (to the wall's inside)
  stair: [-85.2, -91.5, 41.0, 42.4, 22], // up to the catwalk: x at the floor, x at the top, z0, z1, steps
  office: [-123.6, -115, 40.6, 3.0, [-117.6, -116.4, 2.2]], // the parts office under the catwalk's west end: x0, x1, its glass front's z, height; the door (x0, x1, top)
  docks: [-114, -94], post: 0.35, dockD: [11.4, 18], dockW: 6.4, dockH: 9.5, // the mech docks (x centres) along the north wall: z span, width, beam height
  mech: { leg: [0.9, 4.0, 1.2], legX: 1.0, torso: [3.4, 2.6, 2.4], head: [1.2, 1.0, 1.2], z: 14.4 }, // a half-built mech in each: leg size, legs apart, torso, head; its z
  crane: { rail: 11, x: -104, arm: [-105.2, -102.8, 25, 29.5, 6.8, 9.6] }, // the overhead crane: rails' top, the bridge's x; the arm on its hook (x0, x1, z0, z1, y0, y1)
  gantry: { x: -104, z: [-9, 9.5], h: 12, leg: 0.9, legX: 3.2 }, // the yard's portal crane: legs at z0 and z1 (an A each side of x), the girder's height
  magnet: { z: 0.5, y: 6.2 }, // its magnet (a car stuck to it): z under the girder, the car's bottom
  bales: { L: 2.9, W: 1.7, H: 1.25, rows: [[-122, -5.2, 10, [3, 2, 3, 1, 2, 3, 2, 0, 0, 0]], [-122, 5.8, 10, [2, 3, 0, 0, 1, 2, 3, 2, 1, 2]]] }, // crushed cars: size; rows of [x0, z, count, stack heights] (gaps under the gantry's legs)
  crusher: [-90, -7, -79.5, -1.4, 3.2], // the car crusher: x0, z0, x1, z1, height
  tyres: [[-82.5, 3.5], [-127.5, -3.0], [-73.0, -4.0], [-96.5, 50.5]], tyre: [3.2, 1.4], // tyre piles: centres; footprint, height
  cars: [[-118.5, 1.0, 1, 'burnt'], [-89.5, 9.0, 0, 'burnt'], [-128.5, 17.5, 1, 'carblue'], [-78.0, 10.5, 1, 'burnt']], // burnt-out cars: x, z, along z?, paint
  range: { line: -80.5, bags: [2.0, 18.5], targets: [[-67, 3.0], [-67, 10.0], [-67, 17.0]], board: [3.2, 6.0], berm: -63.4 }, // the test range: the firing line's x and z span, targets, board size, the berm's x
  sign: [-78.5, 46.5, 12], // the pylon sign by the road: x, z, height
};

const groundAt = (x, z) => grid().at(x, z);
// the boxes of one piece in its own frame (x, z about its anchor, y up from the floor): [[x0, y0, z0, x1, y1, z1, mat], ...]
// the hangar's anchor = the middle of its floor
export function hangarBoxes() {
  const H = SM.hangar, t = H.t, cx = (H.x0 + H.x1) / 2, cz = (H.z0 + H.z1) / 2, X0 = H.x0 - cx, X1 = H.x1 - cx, Z0 = H.z0 - cz, Z1 = H.z1 - cz, o = [];
  const B = (x0, y0, z0, x1, y1, z1, m = 'metal') => o.push(box6(x0, y0, z0, x1, y1, z1, m));
  const [d0, d1, dt] = H.door.map((v, i) => (i < 2 ? v - cz : v)), [p0, p1, pt] = H.pilot.map((v, i) => (i < 2 ? v - cx : v));
  B(X0 + t, 0, Z0 + t, X1 - t, 0.06, Z1 - t, 'concrete'); // the floor (a slab on the ground: feet land on its paint)
  B(X0, 0, Z0, p0, H.eave, Z0 + t); B(p1, 0, Z0, X1, H.eave, Z0 + t); B(p0, pt, Z0, p1, H.eave, Z0 + t); // north wall, the pilot door
  B(X0, 0, Z1 - t, X1, H.eave, Z1); // south wall
  for (const [xa, xb] of [[X0, X0 + t], [X1 - t, X1]]) { B(xa, 0, Z0 + t, xb, H.eave, d0); B(xa, 0, d1, xb, H.eave, Z1 - t); B(xa, dt, d0, xb, H.eave, d1); } // the ends: the doors
  for (const [xf, out] of [[X0, -1], [X1, 1]]) { B(xf, 0.05, Z0 + 0.3, xf + out * 1.1, dt + 0.3, d0 + 0.05); B(xf, dt + 0.3, Z0, xf + out * 1.15, dt + 0.6, d1 + 0.4); } // the door leaves, parked outside over the wall north of each opening; their track
  // the barrel roof: strips across, each at the arch's height over its middle; the gable ends fill up under it
  const n = H.strips, w = (Z1 - Z0) / n, rise = H.ridge - H.eave;
  for (let i = 0; i < n; i++) {
    const za = Z0 + w * i, zb = za + w, u = (za + zb) / 2 / ((Z1 - Z0) / 2), top = H.eave + rise * (1 - u * u);
    B(X0 - 0.2, top - H.roofT, za, X1 + 0.2, top, zb);
    for (const [xa, xb] of [[X0, X0 + t], [X1 - t, X1]]) if (top - H.roofT > H.eave + 0.05) B(xa, H.eave, za, xb, top - H.roofT, zb);
  }
  // the catwalk along the south wall, its rail (an opening where the stairs come up), its posts; the stairs
  const Mz = SM.mezz, mx0 = Mz.x0 - cx, mx1 = Mz.x1 - cx, mz0 = Mz.z0 - cz, my = Mz.y, rt = 0.08;
  B(mx0, my - Mz.t, mz0, mx1, my, Z1 - t);
  B(mx0, my, mz0, mx1, my + Mz.rail, mz0 + rt); B(mx1 - rt, my, mz0 + rt, mx1, my + Mz.rail, SM.stair[2] - cz); B(mx1 - rt, my, SM.stair[3] - cz, mx1, my + Mz.rail, Z1 - t); // (its east end: the stairs come up through it)
  for (const x of [mx0 + 9, mx0 + 18, mx0 + 27, mx1 - 0.4]) B(x, 0, mz0, x + 0.3, my - Mz.t, mz0 + 0.3);
  { const [sx0, sx1, sz0, sz1, ns] = SM.stair, run = (sx1 - sx0) / ns;
    for (let i = 1; i <= ns; i++) { const y = my * i / ns; B(sx0 - cx + run * (i - 1), y - 0.12, sz0 - cz, sx0 - cx + run * i, y, sz1 - cz); } }
  // the parts office under the catwalk's west end: its glass front (the door), its east wall (its back is the shed's wall)
  { const [ox0, ox1, oz, oh, [od0, od1, odt]] = SM.office, x0 = ox0 - cx, x1 = ox1 - cx, z = oz - cz;
    B(x0, 0, z, od0 - cx, oh, z + 0.15, 'glass'); B(od1 - cx, 0, z, x1, oh, z + 0.15, 'glass'); B(od0 - cx, odt, z, od1 - cx, oh, z + 0.15, 'glass');
    B(x1 - 0.15, 0, z + 0.15, x1, oh, Z1 - t); }
  // the mech docks: four posts and the beam over each, the half-built mech standing in it (legs, torso, head)
  const [dz0, dz1] = SM.dockD.map((v) => v - cz), P = SM.post, M = SM.mech;
  for (const dx of SM.docks) {
    const x = dx - cx, hw = SM.dockW / 2;
    for (const sx of [-1, 1]) for (const z of [dz0 + P, dz1 - P]) B(x + sx * hw - P / 2, 0, z - P / 2, x + sx * hw + P / 2, SM.dockH, z + P / 2, 'hazard');
    for (const sx of [-1, 1]) B(x + sx * hw - P / 2, SM.dockH, dz0, x + sx * hw + P / 2, SM.dockH + 0.6, dz1, 'hazard');
    const mz = M.z - cz, [lw, lh, ld] = M.leg, [tw, th, td] = M.torso, [hw2, hh2, hd2] = M.head;
    for (const sx of [-1, 1]) B(x + sx * M.legX - lw / 2, 0, mz - ld / 2, x + sx * M.legX + lw / 2, lh, mz + ld / 2);
    B(x - tw / 2, lh, mz - td / 2, x + tw / 2, lh + th, mz + td / 2); B(x - hw2 / 2, lh + th, mz - hd2 / 2, x + hw2 / 2, lh + th + hh2, mz + hd2 / 2);
  }
  // the overhead crane: its runway beams along both long walls, the bridge across, the arm hanging off its hook
  const C = SM.crane, bx = C.x - cx;
  B(X0 + t, C.rail - 0.8, Z0 + t, X1 - t, C.rail, Z0 + t + 0.6); B(X0 + t, C.rail - 0.8, Z1 - t - 0.6, X1 - t, C.rail, Z1 - t);
  B(bx - 0.6, C.rail, Z0 + t, bx + 0.6, C.rail + 1.1, Z1 - t);
  { const [ax0, ax1, az0, az1, ay0, ay1] = C.arm; B(ax0 - cx, ay0, az0 - cz, ax1 - cx, ay1, az1 - cz); }
  return o;
}
// the yard's portal crane: anchor = the middle between its legs (x, the middle of z0..z1)
export function gantryBoxes() {
  const G = SM.gantry, zc = (G.z[0] + G.z[1]) / 2, o = [], l = G.leg;
  const B = (x0, y0, z0, x1, y1, z1, m = 'metal') => o.push(box6(x0, y0, z0, x1, y1, z1, m));
  for (const z of G.z) for (const sx of [-1, 1]) B(sx * G.legX - l / 2, 0, z - zc - l / 2, sx * G.legX + l / 2, G.h, z - zc + l / 2, 'hazard');
  for (const z of G.z) B(-G.legX - l / 2, G.h, z - zc - l / 2, G.legX + l / 2, G.h + 0.9, z - zc + l / 2, 'hazard'); // the heads joining each A
  B(-0.7, G.h + 0.9, G.z[0] - zc - 0.8, 0.7, G.h + 2.2, G.z[1] - zc + 0.8, 'hazard'); // the girder
  B(-1.2, G.h + 0.2, SM.magnet.z - zc - 1.2, 1.2, G.h + 0.9, SM.magnet.z - zc + 1.2, 'metal'); // the trolley under it
  B(-1.0, SM.magnet.y + 1.5, SM.magnet.z - zc - 1.0, 1.0, SM.magnet.y + 2.1, SM.magnet.z - zc + 1.0, 'metal'); // the magnet
  B(-0.95, SM.magnet.y, SM.magnet.z - zc - 2.3, 0.95, SM.magnet.y + 1.5, SM.magnet.z - zc + 2.3, 'metal'); // the car stuck to it (along z)
  return o;
}
export const baleBoxes = () => { const { L, W, H } = SM.bales; return [[-L / 2, 0, -W / 2, L / 2, H, W / 2, 'metal']]; };
export function crusherBoxes() { // the crusher: anchor = its middle; its chamber open on top (a car half in it), the control booth
  const [x0, z0, x1, z1, h] = SM.crusher, L = x1 - x0, W = z1 - z0, X = L / 2, Z = W / 2, o = [];
  const B = (a, b, c, d, e, f, m = 'metal') => o.push(box6(a, b, c, d, e, f, m));
  B(-X, 0, -Z, X - 2.2, 1.0, Z); // the bed
  B(-X, 1.0, -Z, X - 2.2, h, -Z + 0.5); B(-X, 1.0, Z - 0.5, X - 2.2, h, Z); B(-X, 1.0, -Z + 0.5, -X + 0.6, h, Z - 0.5); // the chamber's walls
  B(X - 2.2, 0, -Z, X, h + 0.6, Z, 'metal'); // the ram's housing
  return o;
}
export const tyreBoxes = () => { const [f, h] = SM.tyre; return [[-f / 2, 0, -f / 2, f / 2, h, f / 2, 'roofg']]; };
export function targetBoxes() { // a mech-size target board on its stand (facing west, -x), anchor = its foot
  const [w, h] = SM.range.board; return [[-0.6, 0, -w / 2, 0.6, 0.8, w / 2, 'metal'], [-0.1, 0.8, -w / 2, 0.1, 0.8 + h, w / 2, 'wood']];
}
export function bagsBoxes() { const [z0, z1] = SM.range.bags, L = z1 - z0; return [[-0.6, 0, -L / 2, 0.6, 1.1, L / 2, 'sand']]; } // the firing line's sandbags (along z)
export function bermBoxes() { const [z0, z1] = [-2.0, 22.0], L = z1 - z0; return [[-1.4, 0, -L / 2, 1.4, 3.2, L / 2, 'dirt']]; }
export function signBoxes() { const h = SM.sign[2]; return [[-0.5, 0, -0.5, 0.5, h - 3.6, 0.5, 'metal'], [-0.4, h - 3.6, -4.6, 0.4, h, 4.6, 'metal']]; } // the pylon and its board (along z, facing the road both ways)

// place a piece's boxes at (x, z) on the ground (q quarter turns), as model `id` (o: propOf's options)
function piece(B, id, boxes, x, z, q = 0, o = {}, y = null) {
  const c = [1, 0, -1, 0][q & 3], s = [0, 1, 0, -1][q & 3], S = { still: 1 };
  if (y === null) { y = 1e9; for (const [x0, , z0, x1, , z1] of boxes) for (const [u, v] of [[x0, z0], [x1, z0], [x0, z1], [x1, z1], [(x0 + x1) / 2, (z0 + z1) / 2]]) y = Math.min(y, groundAt(x + u * c + v * s, z - u * s + v * c)); }
  propOf(id, [x, y, z], q * Math.PI / 2, () => { for (const [x0, y0, z0, x1, y1, z1, m] of boxes) B.add(x + x0 * c + z0 * s, y + y0, z - x0 * s + z0 * c, x + x1 * c + z1 * s, y + y1, z - x1 * s + z1 * c, m, S); }, o);
  return y;
}

export function scrapMart(B) {
  const H = SM.hangar;
  piece(B, 'sm_hangar', hangarBoxes(), (H.x0 + H.x1) / 2, (H.z0 + H.z1) / 2);
  piece(B, 'sm_gantry', gantryBoxes(), SM.gantry.x, (SM.gantry.z[0] + SM.gantry.z[1]) / 2);
  const tints = ['carred', 'carblue', 'cargreen', 'caryellow', 'carwhite', 'carblack'];
  for (const [x0, z, n, hs] of SM.bales.rows) for (let i = 0; i < n; i++) {
    const x = x0 + i * (SM.bales.L + 0.35) + SM.bales.L / 2;
    let y = null;
    for (let k = 0; k < hs[i]; k++) { const yy = y === null ? null : y + k * SM.bales.H; const g = piece(B, 'sm_bale', baleBoxes(), x + (k % 2 ? 0.12 : 0), z + (k % 2 ? -0.1 : 0), 0, { t: tints[(i * 3 + k * 2 + (z > 0 ? 1 : 0)) % tints.length] }, yy); if (y === null) y = g; }
  }
  const [cx0, cz0, cx1, cz1] = SM.crusher; piece(B, 'sm_crusher', crusherBoxes(), (cx0 + cx1) / 2, (cz0 + cz1) / 2);
  for (const [x, z] of SM.tyres) piece(B, 'sm_tyres', tyreBoxes(), x, z);
  const L = B.local(0, 0, 0);
  for (const [x, z, alongZ, paint] of SM.cars) car(L, x, z, alongZ, paint); // (the game's own cars: burnt-out ones keep their burnt paint)
  const R = SM.range;
  piece(B, 'sm_bags', bagsBoxes(), R.line, (R.bags[0] + R.bags[1]) / 2);
  for (const [x, z] of R.targets) piece(B, 'sm_target', targetBoxes(), x, z);
  piece(B, 'sm_berm', bermBoxes(), R.berm, 10.0);
  piece(B, 'sm_sign', signBoxes(), SM.sign[0], SM.sign[1]);
}
