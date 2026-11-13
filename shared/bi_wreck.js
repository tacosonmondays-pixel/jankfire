// RETURN TO SENDER (Battle Island's north-east point, docs/maps/battleisland/DESIGN.md): the MV NEXT DAY, a little geared
// container feeder (88 m, the real size of a 300-box coaster), run aground broadside off the point and listing 5 degrees
// toward the beach. Its forward hold is torn open on the beach side: wade in through the hole (wide and tall enough for
// a mech) onto the sand that came in with the sea, climb the hold's ladder to the deck. The aft hold is shut, its
// containers still stacked on the hatch (the beach-side rows are gone: they're on the beach). Two deck cranes (the
// forward one swung out over the sand with a container still on its hook, the aft one topped up high: grapple both),
// the house aft (the mess room on A deck, the outside ladder up to the bridge wing, the wheelhouse, the funnel).
// On the beach: the containers that went over the side (walk into the open ones), one burst open, a hatch cover, the
// orange lifeboat the crew left in. Every piece is a Blender model over its boxes (tools/blender/make_wreck.py: it
// reads its numbers from here with node), built at the ground's own height with its boxes `still`.
import { grid } from './battleisland.js';
import { propOf } from './propcap.js';

const r3 = (v) => Math.round(v * 1000) / 1000;
// the ship. its own frame: x from the bow (-44, west) to the stern (+44, east), y up from the bottom of the keel, z across
// to the beach side (+z, south). in the world: rolled `list` degrees about its keel (the beach side down), keel at ky
export const RS = {
  c: [234, -167], ky: -2.0, list: 5,
  L: 88, B: 14, D: 8.6, // length, beam, depth to the main deck
  fc: [-44, -33, 11.0], // the forecastle: x0, x1, its deck
  bowLine: [[-44.6, 0.3], [-43.5, 1.75], [-42, 3.15], [-40, 4.65], [-37.5, 5.9], [-35, 6.65], [-33, 6.95], [-31, 7]], // the deck's half-width at the bow (the model's curve: blocks follow it)
  sternLine: [[38, 7], [40, 6.95], [41.5, 6.7], [42.8, 6.2], [43.8, 5.5], [44.4, 4.7]], // and at the stern (the transom at the end)
  h1: [-33, -7], h1in: 6.4, tank: 1.2, // hold 1 (open, torn): its bulkheads, its inside half-width, the tank top
  hatch1: [-31, -9, 5], coam: 1.2, coamT: 0.3, // the hatch opening (x0, x1, half-width) and its coaming (height, thickness)
  hole: [-27, -15], sand: 0.3, // the tear in the beach side, the sand floor in the hold (world y)
  ladder: [-19, -9, -4, -2.8, 2.0], // the hold's ladder: from x0 (bottom) up to x1 (the deck), z0..z1, bottom y (ship)
  hatch2: [-1.5, 24.5, 5], hatchH: 1.4, // hold 2 (shut): its hatch cover (x0, x1, half-width) and height over the deck
  boxes: { x: [-1.2, 11.6], rows: [-4.89, -2.44, 0.01, 2.46], h: [[3, 2, 2, 0], [2, 2, 1, 0]] }, // 40 ft on the hatch: bay starts, row starts (2.44 each), stacks per row (north to south)
  rail: 1.0, railT: 0.08, // the deck railing
  crane1: { x: -5, ped: 1.3, pedH: 4, house: [2, 3.2, 2.2], jib: [[2.4, 13.6], [22, 15.2]], jibW: 1.0 }, // pedestal half-size, height; house half-x, height, half-z; jib from (z, y) to (z, y)
  crane2: { x: 27, ped: 1.3, pedH: 4, house: [2, 3.2, 2.0], jib: [[25, 13.8], [7, 27.6]], jibW: 1.0 }, // the aft one: its jib up toward the bow (x, y)
  hook: { drop: 2.6, len: 6.06, w: 2.44, h: 2.59 }, // the container on crane 1's hook: its bottom this far over the sand, a 20 ft along z
  house: [29, 40, 5.5], wall: 0.3, decks: [8.6, 11.4, 17.0, 19.8], // the house: x0, x1, half-width; A deck, B deck, the bridge, its roof
  bridge: [29, 34, 7.2], win: [18.0, 19.4], // the wheelhouse x0, x1, the wings' half-width; the front windows' sill and head
  messDoor: [-0.6, 0.6, 10.7], wingDoor: [31.4, 32.5, 19.1], // the mess room's aft door (z0, z1, top); the wheelhouse's side doors (x0, x1, top)
  stair: [42, 34, 5.65, 6.85, 30], // the outside ladder up the house's beach side: x bottom, x top, z0, z1, steps
  fstair: [-28.4, -33, 5.45, 6.75, 9], // up to the forecastle (both sides): x bottom, x top, |z| range, steps
  funnel: [35.4, 39, 2.1, 23.6], // x0, x1, half-width, top
};
const D2R = Math.PI / 180;
export const hwAt = (line, x) => { for (let i = 0; i + 1 < line.length; i++) { const [a, wa] = line[i], [b, wb] = line[i + 1]; if (x <= b) return wa + (wb - wa) * Math.max(0, (x - a) / (b - a)); } return line.at(-1)[1]; };
// the bow and stern as blocks a metre or so long, each as wide as the curve at its middle: [[x0, x1, half-width], ...]
const blocks = (line, x0, x1) => { const n = Math.ceil((x1 - x0) / 1.1), o = []; for (let i = 0; i < n; i++) { const a = x0 + (x1 - x0) * i / n, b = x0 + (x1 - x0) * (i + 1) / n; o.push([a, b, r3(hwAt(line, (a + b) / 2))]); } return o; };
export const BOWB = blocks(RS.bowLine, -44.6, -33), STERNB = blocks(RS.sternLine, 40, 44.4);

// the ship's boxes, relative to its anchor (the keel's middle, at ky): [[x0, y0, z0, x1, y1, z1, mat], ...]. each box of the
// ship's frame is cut into pieces small enough that the list's tilt stays within a few cm, each piece upright at its
// tilted centre (the boxes stay axis-aligned: floors step 12 cm per 1.5 m across, walls 25 cm per deck)
export function shipBoxes() {
  const S = RS, out = [], c = Math.cos(S.list * D2R), s = Math.sin(S.list * D2R);
  const R = (x0, y0, z0, x1, y1, z1, m = 'metal', solid = false) => {
    const nz = Math.max(1, Math.ceil((z1 - z0) / 1.5 - 1e-9)), ny = solid ? 1 : Math.max(1, Math.ceil((y1 - y0) / 3.2 - 1e-9));
    for (let i = 0; i < nz; i++) for (let j = 0; j < ny; j++) {
      const za = z0 + (z1 - z0) * i / nz, zb = z0 + (z1 - z0) * (i + 1) / nz, ya = y0 + (y1 - y0) * j / ny, yb = y0 + (y1 - y0) * (j + 1) / ny;
      const zc = (za + zb) / 2, yc = (ya + yb) / 2, wy = yc * c - zc * s, wz = zc * c + yc * s, hy = (yb - ya) / 2, hz = (zb - za) / 2;
      out.push([r3(x0), r3(wy - hy), r3(wz - hz), r3(x1), r3(wy + hy), r3(wz + hz), m]);
    }
  };
  const W = (x0, y0, z0, x1, y1, z1, m) => out.push([x0, y0, z0, x1, y1, z1, m].map((v) => (typeof v === 'number' ? r3(v) : v))); // (upright in the world: the sand, the hanging box)
  const at = (y, z) => [y * c - z * s, z * c + y * s]; // a point of the ship's frame (y, z) -> anchor frame (y, z)
  const D = S.D, B2 = S.B / 2, rl = S.rail, rt = S.railT;
  // ---- the bow: the forecastle (solid to its deck, narrowing to the stem), its bulwark, the break's front wall
  const fd = S.fc[2];
  for (const [xa, xb, w] of BOWB) R(xa, 0, -w, xb, fd, w, 'metal', true);
  for (const sz of [-1, 1]) for (const [xa, xb, w] of BOWB) R(xa, fd, sz > 0 ? w - 0.15 : -w, xb, fd + rl, sz > 0 ? w : -w + 0.15); // the bulwark (stepped with the blocks)
  // ---- hold 1: open to the sky, torn on the beach side. double bottom, the side shells, the bulkheads, the side decks,
  // the coaming round the hatch
  const [h0, h1] = S.h1, hi = S.h1in, tk = S.tank, [a0, a1, aw] = S.hatch1, ct = S.coamT, [t0, t1] = S.hole;
  R(h0, 0, -B2, h1, tk, B2, 'metal', true);
  R(h0, tk, -B2, h1, D, -hi); // the sea side
  R(h0, tk, hi, t0, D, B2); R(t1, tk, hi, h1, D, B2); // the beach side, the hole between
  R(h0, tk, -hi, h0 + 0.4, D, hi); R(h1 - 0.4, tk, -hi, h1, D, hi); // the bulkheads
  R(h0, D - 0.3, -B2, h1, D, -aw); R(h0, D - 0.3, aw, t0, D, B2); R(t1, D - 0.3, aw, h1, D, B2); // the side decks (torn off over the hole)
  R(h0 + 0.4, D - 0.3, -aw, a0, D, aw); R(a1, D - 0.3, -aw, h1 - 0.4, D, aw); // the deck at each end of the hatch
  R(a0, D, -aw - ct, a1, D + S.coam, -aw); R(a0, D, aw, t0 - 0.5, D + S.coam, aw + ct); R(t1 + 0.5, D, aw, a1, D + S.coam, aw + ct); // the coaming (torn away over the hole: a mech walks in under the open sky)
  R(a0 - ct, D, -aw - ct, a0, D + S.coam, aw + ct); R(a1, D, -aw - ct, a1 + ct, D + S.coam, S.ladder[2] - 0.1); R(a1, D, S.ladder[3] + 0.1, a1 + ct, D + S.coam, aw + ct); // (the aft one: a gap where the ladder comes up)
  R(-33.08, fd, -5.3, -33, fd + rl, 5.3); // the forecastle's rail along its break (the ladders come up at each side of it)
  // the hold's ladder (an inclined ladder up to the deck at the hatch's aft end), its treads
  { const [lx0, lx1, lz0, lz1, ly0] = S.ladder, n = Math.round((D - ly0) / 0.275), run = (lx1 - lx0) / n;
    for (let i = 1; i <= n; i++) { const y = ly0 + (D - ly0) * i / n; R(lx0 + run * (i - 1), y - 0.12, lz0, lx0 + run * i, y, lz1); } }
  // the sand the sea brought in (level in the world), out through the hole as a ramp down to the shallows
  { const [, zs] = at(tk, -hi), [, zn] = at(tk, hi), [, zo] = at(0.3, B2), sy = S.sand - S.ky; // (world y -> the anchor's)
    W(h0 + 0.4, 0.3, zs + 0.3, h1 - 0.4, sy, zn - 0.2, 'sand');
    W(t0, 0.5, zn - 0.2, t1, sy - 0.25, zo + 1.4, 'sand'); W(t0 + 1, 0.5, zo + 1.4, t1 - 1, sy - 0.5, zo + 3.2, 'sand'); }
  // ---- midships: solid to the deck (the cross deck, hold 2, the house's footing), hold 2's hatch cover, the containers
  R(h1, 0, -B2, 40, D, B2, 'metal', true);
  const [b0, b1, bw] = S.hatch2;
  R(b0, D, -bw, b1, D + S.hatchH, bw, 'metal', true);
  const H2 = D + S.hatchH, CL = 12.19, CW = 2.44, CH = 2.59;
  S.boxes.x.forEach((bx, k) => S.boxes.rows.forEach((rz, j) => { for (let t = 0; t < S.boxes.h[k][j]; t++) R(bx, H2 + t * CH, rz, bx + CL, H2 + (t + 1) * CH, rz + CW, ['containerr', 'containerb', 'containerg'][(k * 5 + j * 3 + t) % 3], true); }));
  // ---- the stern: solid to the deck, narrowing to the transom
  for (const [xa, xb, w] of STERNB) R(xa, 0, -w, xb, D, w, 'metal', true);
  // the deck railing (both sides, bow to stern; not where the side's torn away), the stern rail
  for (const sz of [-1, 1]) {
    const z0 = sz > 0 ? B2 - rt : -B2, z1 = sz > 0 ? B2 : -B2 + rt;
    if (sz > 0) { R(S.fc[1], D, z0, t0, D + rl, z1); R(t1, D, z0, 40, D + rl, z1); } else R(S.fc[1], D, z0, 40, D + rl, z1);
    for (const [xa, xb, w] of STERNB) R(xa, D, sz > 0 ? w - rt : -w, xb, D + rl, sz > 0 ? w : -w + rt);
  }
  { const [, xe, we] = STERNB.at(-1); R(xe - rt, D, -we, xe, D + rl, we); } // the stern rail across the transom
  // the ladders up to the forecastle (each side, aft of the break)
  { const [fx0, fx1, z0, z1, n] = S.fstair, run = (fx1 - fx0) / n;
    for (const sz of [-1, 1]) for (let i = 1; i <= n; i++) { const y = D + (fd - D) * i / n; R(fx0 + run * (i - 1), y - 0.12, sz > 0 ? z0 : -z1, fx0 + run * i, y, sz > 0 ? z1 : -z0); } }
  // ---- the cranes: pedestal, house, jib (in steps along it: something to grapple)
  const jibs = (pts, x, w, along) => { const [[p0, q0], [p1, q1]] = pts, n = 6;
    for (let i = 0; i < n; i++) { const u0 = p0 + (p1 - p0) * i / n, u1 = p0 + (p1 - p0) * (i + 1) / n, v = q0 + (q1 - q0) * (i + 0.5) / n, hv = Math.abs(q1 - q0) / n / 2 + 0.5;
      if (along === 'z') R(x - w / 2, v - hv, Math.min(u0, u1), x + w / 2, v + hv, Math.max(u0, u1)); else R(Math.min(u0, u1), v - hv, -w / 2, Math.max(u0, u1), v + hv, w / 2); } };
  { const C = S.crane1, [hx, hh, hz] = C.house;
    R(C.x - C.ped, D, -C.ped, C.x + C.ped, D + C.pedH, C.ped); R(C.x - hx, D + C.pedH, -hz, C.x + hx, D + C.pedH + hh, hz);
    jibs(C.jib, C.x, C.jibW, 'z');
    // the container still on its hook: hanging plumb under the jib's tip, its bottom `drop` over the sand
    const [, tz] = at(C.jib[1][1], C.jib[1][0]), K = S.hook, g = groundAt(RS.c[0] + C.x, RS.c[1] + tz) - S.ky, yb = g + K.drop;
    W(C.x - K.w / 2, yb, tz - K.len / 2, C.x + K.w / 2, yb + K.h, tz + K.len / 2, 'containerb'); }
  { const C = S.crane2, [hx, hh, hz] = C.house;
    R(C.x - C.ped, D, -C.ped, C.x + C.ped, D + C.pedH, C.ped); R(C.x - hx, D + C.pedH, -hz, C.x + hx, D + C.pedH + hh, hz);
    jibs(C.jib, 0, C.jibW, 'x'); }
  // ---- the house: A deck's mess room (in by its aft door), B and C decks (cabins: shut), the wheelhouse on top (in from
  // either wing), its front windows smashed out (shoot or jump through them), the wings, the funnel, the roof's rails
  const [x0, x1, hw] = S.house, t = S.wall, [dA, dB, dW, dR] = S.decks, [md0, md1, mdt] = S.messDoor;
  R(x0, dA, -hw, x1, dB, -hw + t); R(x0, dA, hw - t, x1, dB, hw); // A deck: north, south walls
  R(x0, dA, -hw + t, x0 + t, dB, hw - t); // its front
  R(x1 - t, dA, -hw + t, x1, dB, md0); R(x1 - t, dA, md1, x1, dB, hw - t); R(x1 - t, mdt, md0, x1, dB, md1); // its aft wall: the door
  R(x0, dB - 0.2, -hw, x1, dB, hw); // the ceiling
  R(x0, dB, -hw, x1, dW, hw, 'metal', true); // B and C decks
  const [w0, w1, ww] = S.bridge, [s0, s1] = S.win, [wd0, wd1, wdt] = S.wingDoor;
  R(w0, dW - 0.2, -ww, w1, dW, ww); // the bridge deck and its wings
  R(w0, dW, -hw, w0 + t, s0, hw); R(w0, s1, -hw, w0 + t, dR, hw); // the front: under and over the windows
  for (const zm of [-hw, -2.85, -0.15, 2.55, hw - 0.3]) R(w0, s0, zm, w0 + t, s1, zm + 0.3); // the mullions (the panes are gone)
  for (const sz of [-1, 1]) { const za = sz > 0 ? hw - t : -hw, zb = sz > 0 ? hw : -hw + t; R(w0 + t, dW, za, wd0, dR, zb); R(wd1, dW, za, w1, dR, zb); R(wd0, wdt, za, wd1, dR, zb); } // the sides: the doors to the wings
  R(w1 - t, dW, -hw + t, w1, dR, hw - t); // the back (the funnel deck's side: shut)
  R(w0 - 0.2, dR, -hw - 0.3, w1 + 0.2, dR + 0.3, hw + 0.3); // the roof
  for (const sz of [-1, 1]) { const z0 = sz > 0 ? ww - rt : -ww, z1 = sz > 0 ? ww : -ww + rt; R(w0, dW, z0, w1, dW + rl, z1); R(w0, dW, sz > 0 ? hw : -ww, w0 + rt, dW + rl, sz > 0 ? ww : -hw); } // the wings' rails (out, front)
  R(w1 - rt, dW, -ww, w1, dW + rl, -hw); // the north wing's back rail (the beach wing's back is the ladder's head)
  R(w1, dW, -hw, x1, dW + rl, -hw + rt); R(x1 - rt, dW, -hw, x1, dW + rl, hw); R(w1 + 1.4, dW, hw - rt, x1, dW + rl, hw); // the funnel deck's rails (in from the ladder's head on the beach side)
  { const [f0, f1, fw, ft] = S.funnel; R(f0, dW, -fw, f1, ft, fw, 'metal', true); }
  // the outside ladder: from the stern deck up the house's beach side to the beach wing
  { const [sx0, sx1, z0, z1, n] = S.stair, run = (sx1 - sx0) / n;
    for (let i = 1; i <= n; i++) { const y = dA + (dW - dA) * i / n; R(sx0 + run * (i - 1), y - 0.12, z0, sx0 + run * i, y, z1); } }
  return out;
}
// the ground's height in the world (the island's own grid)
const groundAt = (x, z) => grid().at(x, z);

// ---- the beach: the containers that went over the side and the rest. each one a model over its boxes, in its own frame
// (x along its length; the door end at -x). anchor = the middle of its foot
export const BOX40 = { L: 12.19, W: 2.44, H: 2.59, t: 0.12, fl: 0.14 }; // a 40 ft high-cube-ish box: wall and floor thickness
export function box40Boxes(burst) { // walk in at the door end (-x); burst: the beach-facing side (+z) torn open as well
  const { L, W, H, t, fl } = BOX40, X = L / 2, Z = W / 2, o = [];
  o.push([-X, 0, -Z, X, fl, Z, 'metal'], [-X, H - t, -Z, X, H, Z, 'metal'], [-X, fl, -Z, X, H - t, -Z + t, 'metal'], [X - t, fl, -Z + t, X, H - t, Z - t, 'metal']);
  if (burst) o.push([-X, fl, Z - t, -X + 3.2, H - t, Z, 'metal'], [X - 2.4, fl, Z - t, X, H - t, Z, 'metal']); // (the split side: a 6.6 m tear)
  else o.push([-X, fl, Z - t, X, H - t, Z, 'metal']);
  return o;
}
export const BOAT = { L: 8.4, W: 3.0, H: 3.0, floor: 0.5, canopy: 2.55, door: [-0.4, 0.8] }; // the enclosed lifeboat: its floor, the canopy's underside, the side door (x0, x1)
export function boatBoxes() { // along x, bow at +x, the door in its beach-ward side (+z)
  const { L, W, H, floor, canopy, door } = BOAT, X = L / 2, Z = W / 2, t = 0.14, o = [];
  o.push([-X + 0.5, 0, -Z + 0.3, X - 0.6, floor, Z - 0.3, 'yellow']); // the hull's bottom (it narrows: the keel)
  o.push([-X, 0.3, -Z, X, canopy, -Z + t, 'yellow'], [-X, 0.3, Z - t, door[0], canopy, Z, 'yellow'], [door[1], 0.3, Z - t, X, canopy, Z, 'yellow']); // the sides
  o.push([-X, 0.3, -Z + t, -X + t, canopy, Z - t, 'yellow'], [X - t, 0.3, -Z + t, X, canopy, Z - t, 'yellow']); // the ends
  o.push([-X, canopy, -Z, X, H, Z, 'yellow']); // the canopy
  return o;
}
export const HATCH = { L: 12.6, W: 5.2, H: 0.75 }; // a hatch cover panel, slid off and down onto the sand
export const hatchBoxes = () => [[-HATCH.L / 2, 0, -HATCH.W / 2, HATCH.L / 2, HATCH.H, HATCH.W / 2, 'metal']];
// where they lie: [kind, x, z, turn (quarter turns: 0 = along x, door west), sink (m into the sand), tint]
export const SPILL = [
  ['wreck_box', 243, -134, 0, 0.25, 'carred'], ['wreck_box', 205.5, -133, 1, 0.3, 'caryellow'], ['wreck_burst', 256.5, -141.5, 2, 0.3, 'carblue'],
  ['wreck_box', 233.5, -124, 3, 0.25, 'cargreen'], ['wreck_hatch', 222, -128, 0, 0.2], ['wreck_boat', 262, -128, 0, 0.35],
];
// 20 ft boxes (the game's own container model): [x, z, along z?, material, y over the sand (- = sunk), on top of SPILL[i]]
export const BOX20 = [[198, -156.5, 0, 'containerg', -0.9], [264, -158, 1, 'containerr', -0.7], [246, -134, 0, 'containerb', 0, 0], [213.5, -125.0, 1, 'containerr', 0]]; // (none between the beach and the box on the hook: you see it hanging)

// the build: the ship (one model, its boxes rolled with it), the spill on the beach
export function wreck(B) {
  const S = { still: 1 }, [cx, cz] = RS.c, ky = RS.ky;
  propOf('wreck_ship', [cx, ky, cz], 0, () => { for (const [x0, y0, z0, x1, y1, z1, m] of shipBoxes()) B.add(cx + x0, ky + y0, cz + z0, cx + x1, ky + y1, cz + z1, m, S); });
  const kinds = { wreck_box: () => box40Boxes(false), wreck_burst: () => box40Boxes(true), wreck_boat: boatBoxes, wreck_hatch: hatchBoxes };
  const ys = [];
  for (const [id, x, z, q, sink, tint] of SPILL) {
    const bx = kinds[id](), c = [1, 0, -1, 0][q], s = [0, 1, 0, -1][q], frame = q * Math.PI / 2; // (three's turn for q quarter turns: local x -> world (c, -s))
    let lo = 1e9; for (const [x0, , z0, x1, , z1] of bx) for (const [u, v] of [[x0, z0], [x1, z0], [x0, z1], [x1, z1]]) lo = Math.min(lo, groundAt(x + u * c + v * s, z - u * s + v * c));
    const y = Math.max(lo, groundAt(x, z) - sink); ys.push(y); // (its low corner just touches the sand, or it's sunk `sink` at its middle)
    propOf(id, [x, y, z], frame, () => { for (const [x0, y0, z0, x1, y1, z1, m] of bx) { const ax = x + x0 * c + z0 * s, az = z - x0 * s + z0 * c, bx2 = x + x1 * c + z1 * s, bz = z - x1 * s + z1 * c; B.add(ax, y + y0, az, bx2, y + y1, bz, m, S); } }, tint ? { t: tint } : {});
  }
  for (const [x, z, alongZ, m, dy, on] of BOX20) { // (one box each: the game's container model, spotted by its size)
    const hx = alongZ ? 1.22 : 3.03, hz = alongZ ? 3.03 : 1.22, base = on !== undefined ? ys[on] + BOX40.H : Math.min(groundAt(x - hx, z - hz), groundAt(x + hx, z - hz), groundAt(x - hx, z + hz), groundAt(x + hx, z + hz));
    B.add(x - hx, base + dy, z - hz, x + hx, base + dy + 2.6, z + hz, m, S);
  }
}
