// BATTLE ISLAND: the mech-hero battle royale's map (docs/maps/battleisland/DESIGN.md). One big island that reads as an
// island from the blimp: a real coastline (the harbour bay south, the lagoon east behind its reef, cliffs north-west, a
// lighthouse headland, dunes south-west), a ridge across the middle with the radio tower on top, a river (a sea-level
// estuary) from the lagoon up into the jungle, islets off the coast. Nine POIs, ring road + cross roads, all sized
// for 5-6 m mechs. This file is the master plan: numbers in metres, x east, z south (north = -z), y up, sea at SEA.
// islandH(x, z) is the ground's height (the same on the server and every client); the map builder turns it into
// shared/terrain.js relief + boxes.

export const SEA = -0.25; // the water's surface (Islands' too). no swimming here: deeper than WADE is the sea kill
export const WADE = 1.5; // water up to this deep is walked through (the mode slows you to 60%); deeper and you're gone
const sm = (a, b, v) => { const k = Math.max(0, Math.min(1, (v - a) / (b - a))); return k * k * (3 - 2 * k); };
const lerp = (a, b, t) => a + (b - a) * t;
// a hash noise that's the same everywhere (no Math.random: the server and the clients build the same island)
function lat(seed) {
  const h = (i, j) => { let n = Math.imul(i, 374761393) ^ Math.imul(j, 668265263) ^ seed; n = Math.imul(n ^ (n >>> 13), 1274126177); return ((n ^ (n >>> 16)) >>> 0) / 4294967295 * 2 - 1; };
  return (x, z) => { const i = Math.floor(x), j = Math.floor(z), u = x - i, v = z - j, a = u * u * (3 - 2 * u), b = v * v * (3 - 2 * v);
    return (h(i, j) * (1 - a) + h(i + 1, j) * a) * (1 - b) + (h(i, j + 1) * (1 - a) + h(i + 1, j + 1) * a) * b; };
}
const N1 = lat(7101), N2 = lat(7202), N3 = lat(7303), N4 = lat(7404);
const fbm = (x, z) => 0.55 * N1(x / 90, z / 90) + 0.3 * N2(x / 38, z / 38) + 0.15 * N3(x / 14, z / 14);
// distance from a point to a polyline [[x, z]...]
export function segDist(x, z, pts) {
  let d = 1e9;
  for (let q = 0; q + 1 < pts.length; q++) { const [ax, az] = pts[q], [bx, bz] = pts[q + 1], ex = bx - ax, ez = bz - az, t = Math.max(0, Math.min(1, ((x - ax) * ex + (z - az) * ez) / (ex * ex + ez * ez || 1))); d = Math.min(d, Math.hypot(x - ax - ex * t, z - az - ez * t)); }
  return d;
}

export const PLAN = {
  // the land: an island about 560 m east-west by 460 north-south. half sizes + the wobble of the coast (polar harmonics)
  land: { rx: 290, rz: 232, harm: [[2, 0.1, 0.6], [3, 0.09, 2.1], [4, 0.05, 1.2], [5, 0.045, 0.3], [7, 0.025, 4.0]] },
  ground: [-420, -380, 420, 380], // the play area (walkable sand and sea floor): the zone's first circle sits inside it
  seaOut: 900, // the sea runs out to here, the haze takes it after
  // set shapes that bend the coast: [x, z, rx, rz, depth (+ = land pushed out, - = sea cut in)]
  coast: [
    [30, 196, 84, 66, -2.1], // the harbour bay (south): a deep round bay, the town round its north shore
    [-262, -178, 46, 62, 1], // the lighthouse headland (north-west), pushed out into the sea
    [246, -138, 60, 46, 1.25], // the north-east point (the wreck lies aground off its tip)
    [-60, -236, 60, 30, -0.7], // a cove on the north coast below the quarry
    [130, 236, 50, 34, -0.6], // a little bay south-east of the harbour
    [-240, 182, 70, 46, 0.5], // the south-west dune spit
  ],
  // the lagoon (east): calm water inside the reef. its rim on the sea side is the reef: shallow flats a mech wades
  lagoon: { c: [238, 40], r: [52, 70], reefW: 18, gap: [300, 52, 20] },
  // the ridge across the middle: a line of peaks [x, z, height, radius]. the radio tower stands on the highest
  ridge: [[-140, -70, 26, 70], [-60, -92, 38, 66], [20, -62, 52, 64], [96, -84, 34, 58], [150, -130, 22, 50]],
  cliffs: { c: [-230, -150], r: 105, h: 24, sx: 1.25, sz: 0.8 }, // the north-west: high ground that ends in a sheer drop into the sea
  // the river: a sea-level channel (the sea comes up it) from the lagoon west into the jungle, to the temple's falls
  river: { pts: [[200, 30], [166, 16], [136, 34], [104, 22], [76, 30], [52, 12]], w: 16, bank: 14 },
  // roads (12 m: two mechs pass): the ring, the cross roads. polylines
  roads: [
    { name: 'Ring Road', w: 12, ring: true, pts: [[-170, 40], [-150, -40], [-120, -128], [-30, -178], [70, -170], [170, -96], [168, -30], [150, 96], [90, 112], [-40, 112], [-140, 120], [-170, 40]] },
    { name: 'Main Drag', w: 14, pts: [[28, 146], [28, 120], [22, 70], [18, 40], [8, -14]] }, // the harbour up to the radio tower's saddle
    { name: 'Hangar Road', w: 14, pts: [[-170, 40], [-110, 32], [-40, 26], [18, 40]] },
    { name: 'Quarry Track', w: 12, pts: [[-30, -178], [-48, -136]] },
    { name: 'Resort Drive', w: 12, pts: [[150, 96], [176, 112]] },
    { name: 'Point Road', w: 10, pts: [[-150, -40], [-210, -110], [-250, -160]] },
  ],
  // the POIs. rect = [x0, z0, x1, z1] (what the HUD names), c = its middle, y = the level it's built on (flattened),
  // flat = the radius kept flat round c, r = its radius (HUD, callouts, bots), drop = open-sky flat spots a mech is
  // called down onto ([dx, dz, radius] from c, 12 m+ across), cells = energy-cell spots (tagged apart from loot)
  pois: [
    { id: 'port', name: 'Port Jankton', c: [28, 118], rect: [-44, 84, 104, 170], y: 1.6, flat: 58, r: 66, drop: [[0, -36, 8], [-18, 20, 6]], cells: 6, color: '#4fd8ff', lab: [0, 36], loot: 0.18, blurb: 'the harbour town: docks, warehouses, a main street. the biggest drop' },
    { id: 'resort', name: 'The All-Inclusive', c: [180, 110], rect: [150, 78, 214, 150], y: 1.2, flat: 34, r: 40, drop: [[18, 26, 8]], cells: 4, color: '#ff4fd8', lab: [20, -40], loot: 0.12, blurb: 'a beach resort on the lagoon. wristbands not checked' },
    { id: 'radio', name: 'Dead Air', c: [20, -62], rect: [-6, -88, 46, -36], y: 50, flat: 26, r: 30, drop: [[-14, 12, 7]], cells: 3, color: '#ffe14d', loot: 0.06, blurb: 'the radio tower on top of the island. broadcasting nothing, loudly' },
    { id: 'wreck', name: 'Return to Sender', c: [240, -154], rect: [204, -194, 276, -116], y: 0.9, flat: 0, r: 44, drop: [[-24, 10, 7]], cells: 4, color: '#ff9a3a', loot: 0.12, blurb: 'a cargo ship on the reef, its containers all up the beach' },
    { id: 'hangar', name: 'Scrap Mart', c: [-110, 30], rect: [-150, -6, -66, 72], y: 3.2, flat: 50, r: 48, drop: [[0, 24, 10], [-30, -24, 7]], cells: 6, color: '#39ff14', lab: [0, 22], loot: 0.14, blurb: 'the mech hangar and scrapyard. some assembly required' },
    { id: 'temple', name: 'Ancient Temple (Probably)', c: [70, -6], rect: [40, -34, 104, 22], y: 4.5, flat: 26, r: 36, drop: [[12, -12, 8]], cells: 4, color: '#7dff4f', lab: [10, 0], loot: 0.1, blurb: 'a jungle temple up the river. the gift shop is newer' },
    { id: 'lighthouse', name: 'Wrong Way Point', c: [-268, -186], rect: [-300, -224, -230, -150], y: 0, flat: 0, r: 36, drop: [[18, 14, 7]], cells: 3, color: '#ff3030', loot: 0.06, blurb: 'a lighthouse on the cliffs. points ships at the rocks' },
    { id: 'farm', name: 'Moo-Tel', c: [-200, 104], rect: [-246, 66, -150, 150], y: 2.4, flat: 46, r: 50, drop: [[24, 24, 10]], cells: 4, color: '#d8b06a', loot: 0.1, blurb: 'a farm on the west flats. the cows have seen things' },
    { id: 'quarry', name: 'The Big Hole', c: [-60, -150], rect: [-104, -190, -16, -112], y: 0, flat: 0, r: 46, drop: [[0, 0, 9]], cells: 5, color: '#b07dff', loot: 0.12, blurb: 'the quarry: terraces down into a pit, a conveyor, a rock crusher' },
  ],
  islets: [[-372, 40, 30, 24], [354, 20, 26, 20], [-130, 300, 34, 22], [186, 268, 22, 18], [-60, -300, 28, 20]], // [x, z, rx, rz]
  quarry: { c: [-60, -150], r: 40, depth: 16, terraces: 4 }, // the pit: cut into the ridge's north foot
  harbour: { x0: -30, x1: 100, z: 146, bed: -1.4, out: 26 }, // Port Jankton's quay (a straight wall at z) and the basin in front of it: waist-deep (fall off the quay and wade), then the bay
  blimpY: 210,
  zone0: [0, 0, 330],
};

const D2R = Math.PI / 180;
// how far inside the coast a point is: > 0 on land (m, roughly), < 0 out at sea
export function coastIn(x, z) {
  const L = PLAN.land, u = x / L.rx, v = z / L.rz, a = Math.atan2(v, u);
  let R = 1; for (const [k, amp, ph] of L.harm) R += amp * Math.sin(k * a + ph);
  R += 0.035 * N4(Math.cos(a) * 3 + 11, Math.sin(a) * 3 + 7); // (a crinkled coast: small coves and points)
  let d = (R - Math.hypot(u, v)) * Math.min(L.rx, L.rz);
  for (const [cx, cz, rx, rz, k] of PLAN.coast) { const q = Math.hypot((x - cx) / rx, (z - cz) / rz); if (q < 1.6) d += k * Math.min(rx, rz) * (1 - sm(0.2, 1.6, q)); }
  return d;
}
const IS = PLAN.islets;
// the ground's height at (x, z): the sea floor, beaches, the plateau, the ridge, the cliffs, the river, the lagoon, the
// quarry, the POIs' level pads. null never: the sea floor goes on out under the water
export function islandH(x, z, raw = false) {
  let d = coastIn(x, z);
  // islets: little humps of sand and rock
  let isl = -1e9; for (const [cx, cz, rx, rz] of IS) { const a = Math.atan2(z - cz, x - cx), w = 1 + 0.22 * Math.sin(2 * a + cx) + 0.14 * Math.sin(3 * a + cz) + 0.1 * N3(x / 9, z / 9); isl = Math.max(isl, (w - Math.hypot((x - cx) / rx, (z - cz) / rz)) * Math.min(rx, rz)); } // (lumpy, not round)
  // the sea floor: a sandy shelf (wadeable, -0.6) for 14 m out, then down to deep water
  const shelf = (dd) => dd > -14 ? lerp(-0.6, SEA + 0.05, sm(-14, 0, dd)) : lerp(-0.6, -9, sm(-14, -60, dd));
  // the land: a beach up from the waterline, then the plateau with its rolls, then the ridge
  const n = fbm(x, z);
  let h;
  if (d <= 0) h = shelf(d);
  else {
    const beach = sm(0, 26, d); // 0 at the waterline, 1 26 m in
    h = SEA + 0.15 + beach * (2.2 + 4.5 * sm(30, 140, d) + n * 3.2);
    for (const [px, pz, ph, pr] of PLAN.ridge) { const q = Math.hypot(x - px, z - pz) / pr; if (q < 1.4) h = Math.max(h, h + ph * Math.exp(-q * q * 2.2) * (0.92 + 0.1 * N2(x / 40, z / 40))); }
    // the north-west: the land rises to the cliff top and stops; the cliff face goes straight down into the sea
    const C = PLAN.cliffs, cq = Math.hypot((x - C.c[0]) / C.sx, (z - C.c[1]) / C.sz) / C.r;
    if (cq < 1.2) h = Math.max(h, (SEA + C.h * sm(1.2, 0.55, cq)) * sm(0, 4, d) + n * 2);
  }
  if (isl > -20) { const ih = isl > 0 ? SEA + 0.2 + Math.min(4, isl * 0.18) : shelf(isl); h = Math.max(h, ih); }
  // the lagoon: calm water inside, the reef its rim (shallow flats), white sand round its inner shore
  const G = PLAN.lagoon, lq = Math.hypot((x - G.c[0]) / G.r[0], (z - G.c[1]) / G.r[1]);
  if (lq < 1.25) {
    const inner = -1.25 - 0.2 * sm(0.9, 0.3, lq); // the lagoon's bed: waist-deep at most (the mode: up to 1.5 m is walkable, deeper is the sea kill)
    if (lq < 1) h = Math.min(h, lerp(inner, SEA - 0.3, sm(0.55, 1, lq)));
    else if (G.gap && Math.abs(z - G.gap[1]) < G.gap[2] / 2 && x > G.c[0]) h = Math.min(h, -3.2); // (the channel out through the reef: the boats' way in)
    else { const reef = SEA - 0.32; h = d > 0 ? Math.min(h, lerp(reef, h, sm(1, 1.25, lq))) : Math.max(h, lerp(reef, h, sm(1.05, 1.25, lq))); } // (the reef: shin-deep, all the way round the sea side)
  }
  // the river: a channel cut down below the sea (the sea comes up it), banks sloping up to the jungle
  const R = PLAN.river, rd = segDist(x, z, R.pts);
  if (rd < R.w / 2 + R.bank) { const bed = -1.3; h = rd < R.w / 2 ? Math.min(h, bed) : Math.min(h, lerp(bed, h, sm(R.w / 2, R.w / 2 + R.bank, rd))); }
  // the quarry: terraces stepping down into a pit
  const Q = PLAN.quarry, qd = Math.hypot(x - Q.c[0], z - Q.c[1]);
  if (qd < Q.r * 1.25) { const rim = h, t = 1 - Math.min(1, qd / Q.r), step = Math.floor(t * Q.terraces * 1.6) / (Q.terraces * 1.6); const pit = Math.max(1.2, rim - Q.depth * Math.min(1, step * 1.6)); h = qd < Q.r ? pit : lerp(pit, rim, sm(Q.r, Q.r * 1.25, qd)); }
  // the POIs: a level pad at the POI's own height (built on), easing back into the land round it
  for (const P of PLAN.pois) if (P.flat > 0 && d > 0) { const pd = Math.hypot(x - P.c[0], z - P.c[1]); if (pd < P.flat * 1.6) h = lerp(h, P.y, (1 - sm(P.flat, P.flat * 1.6, pd)) * sm(0, 8, d)); } // (eased out to the waterline: the bay stays a bay)
  // the mech drop pads: open, level ground a mech is called down onto (at the height the land has under the pad's middle)
  if (!raw) for (const q of PADS) { const pd = Math.hypot(x - q[0], z - q[1]); if (pd < q[2] * 1.7) h = lerp(q[3], h, sm(q[2] + 1, q[2] * 1.7, pd)); }
  // the harbour: the quay's straight wall, the land behind it level with the town, the basin in front wadeable
  const HB = PLAN.harbour;
  if (x > HB.x0 && x < HB.x1 && z > HB.z - 12 && z < HB.z + HB.out + 10) { if (z < HB.z) h = Math.max(h, 1.6); else if (z < HB.z + HB.out) h = HB.bed; else h = lerp(HB.bed, h, sm(HB.z + HB.out, HB.z + HB.out + 10, z)); }
  return h;
}
// the pads in world space with their level: [x, z, r, y]
const PADS = PLAN.pois.flatMap((p) => p.drop.map(([dx, dz, r]) => { const x = p.c[0] + dx, z = p.c[1] + dz; return [x, z, r, Math.max(SEA + 0.6, islandH(x, z, true))]; }));
// which POI a point is in (null outside them): the HUD's place name
export const poiAt = (x, z) => PLAN.pois.find((p) => x >= p.rect[0] && x <= p.rect[2] && z >= p.rect[1] && z <= p.rect[3]) || null;


// ============================================================ the map (look and collisions from the plan above)
// the ground is one heightfield over the whole sea area (shared/terrain.js relief, like Islands' volcano): you walk it,
// grapple it, bots path over it, loot lands on it. painted by what it is: sand, wet sand under the water, grass, jungle
// floor along the river, bare rock on anything steep, the roads. vegetation is the existing Blender props (palms on the
// beaches, ferns and bushes in the jungle). the POIs' buildings come in their own PRs, Blender from the start
import { MAPS, MAP_ORDER, builder, rng, horizon, palm, unstick, forklift, pallets } from './map.js';
import { shapeGround } from './terrain.js';
import { buildNav } from './nav.js';
import { scrapMart } from './bi_scrapmart.js';
import { propOf } from './propcap.js';
import { outOfBounds } from './bounds.js';
import { WIP_ON } from './modes.js';

export const REGION = [-410, -330, 410, 330]; // the shaped ground (whole metres): the island, its shelf, the islets
const BOUNDS = [-404, -324, 404, 324];
export const KILL_Y = SEA - WADE - 0.6; // feet this far down = in water over your head: into the sea
const DEEP = -4.2; // the deep sea's bed (drawn under the water, past where you can stand)
let GRID_ = null;
export const grid = () => GRID_ || (GRID_ = makeGrid()); // (built the first time the island is: nothing at import)
function makeGrid() { // the plan's heights on the terrain's 1 m grid, worked out once (the relief asks for every vertex five times)
  const [X0, Z0, X1, Z1] = REGION, vx = X1 - X0 + 1, vz = Z1 - Z0 + 1, H = new Float32Array(vx * vz);
  for (let i = 0; i < vx; i++) for (let j = 0; j < vz; j++) H[i * vz + j] = Math.max(DEEP, islandH(X0 + i, Z0 + j)); // (past the kill line the sea bed is flat: nobody walks there)
  const at = (x, z) => { const fx = Math.max(0, Math.min(vx - 1.001, x - X0)), fz = Math.max(0, Math.min(vz - 1.001, z - Z0)), i = Math.floor(fx), j = Math.floor(fz), u = fx - i, v = fz - j;
    return (H[i * vz + j] * (1 - u) + H[(i + 1) * vz + j] * u) * (1 - v) + (H[i * vz + j + 1] * (1 - u) + H[(i + 1) * vz + j + 1] * u) * v; };
  const slope = (x, z) => Math.hypot(at(x + 0.5, z) - at(x - 0.5, z), at(x, z + 0.5) - at(x, z - 0.5));
  // nothing steeper than a mech can walk up (the ridge, the dunes, the beaches), except where it's meant to be a wall: the
  // north-west cliffs and the quarry's terrace faces (grapple those). peaks keep their height, their flanks are eased
  const MAXS = 0.62, wall = new Uint8Array(vx * vz), C = PLAN.cliffs, Q = PLAN.quarry;
  for (let i = 0; i < vx; i++) for (let j = 0; j < vz; j++) { const x = X0 + i, z = Z0 + j; if (Math.hypot((x - C.c[0]) / C.sx, (z - C.c[1]) / C.sz) / C.r < 1.25 || Math.hypot(x - Q.c[0], z - Q.c[1]) < Q.r * 1.3 || PADS.some((q) => Math.hypot(x - q[0], z - q[1]) < q[2] + 1) || (x > PLAN.harbour.x0 - 1 && x < PLAN.harbour.x1 + 1 && Math.abs(z - PLAN.harbour.z) < 3)) wall[i * vz + j] = 1; } // (and the quay: a sheer wall) // (and the drop pads: level, whatever's round them)
  for (let pass = 0; pass < 40; pass++) { // raise the low side of anything too steep (a cut-and-fill that keeps every summit and pad)
    let any = 0;
    for (let i = 1; i < vx - 1; i++) for (let j = 1; j < vz - 1; j++) { const k = i * vz + j; if (wall[k] || H[k] <= SEA) continue;
      const top = Math.max(H[k - vz], H[k + vz], H[k - 1], H[k + 1]) - MAXS; if (H[k] < top) { H[k] = top; any++; } }
    for (let i = vx - 2; i > 0; i--) for (let j = vz - 2; j > 0; j--) { const k = i * vz + j; if (wall[k] || H[k] <= SEA) continue;
      const top = Math.max(H[k - vz], H[k + vz], H[k - 1], H[k + 1]) - MAXS; if (H[k] < top) { H[k] = top; any++; } }
    if (!any) break;
  }
  return { H, vx, vz, at, slope, f: (x, z) => H[(x - X0) * vz + (z - Z0)] };
}
export const onRoad = (x, z) => PLAN.roads.some((r) => segDist(x, z, r.pts) < r.w / 2);
const jungle = (x, z) => segDist(x, z, PLAN.river.pts) < 46 || Math.hypot(x - 70, z + 6) < 58;
export const nearPoi = (x, z, m = 0) => PLAN.pois.some((p) => Math.hypot(x - p.c[0], z - p.c[1]) < p.r + m);
export const nearPad = (x, z, m = 0) => PLAN.pois.some((p) => p.drop.some(([dx, dz, r]) => Math.hypot(x - p.c[0] - dx, z - p.c[1] - dz) < r + m));

// DEAD AIR (the summit): the island's landmark, a 70 m guyed lattice radio mast (tools/blender/make_deadair.py,
// p_deadair: one Blender model over all of these boxes). the mast is a column you grapple, its work platform at 50 m
// (railed) you can stand on, a fence round its foot (the gate's open), the DEAD AIR board on its south face, the guy
// wires' three anchor blocks (cover), and the transmitter shack you can walk into: the studio (two transmitter racks,
// the broadcast desk), a door toward the mast, a window west. built at y 0 round the mast's foot: the shaped ground lifts
// it onto the summit. DA = the numbers the model is built to (make_deadair.py has the same table)
export const DA = { plinth: 2, top: 70, deck: 50, deckW: 2.2, rail: 1.1, anchors: [80, 200, 320], anchorR: 18, anchorW: 0.9, anchorH: 0.9,
  fence: 3.4, fenceH: 2.0, gate: 1.1, board: [18, 19.6, 2.3], // fence half-size, height, the gate's half-width; the board's bottom, top, half-width
  shack: [-5.7, -12.4, 2.3, -7.4], shackH: 3.6, wallT: 0.2, door: [0.1, 1.3, 2.3], win: [-10.6, -9.2, 1.1, 2.1], // door x0, x1, top (south wall); window z0, z1, y0, y1 (west wall)
  racks: [[-4.9, -4.1], [-3.9, -3.1]], rackD: 0.7, rackH: 2.1, desk: [1.3, -11.7, 2.1, -9.1, 0.78] }; // racks' x ranges (north wall); desk x0, z0, x1, z1, height (east wall)
function deadAir(B, cx, cz) {
  // built at the summit's own height, every box `still` (the shaped ground leaves it where it is: wider things than 7 m
  // would otherwise stay at y 0 under the hill while the model drew on top)
  const y0 = grid().at(cx, cz), S = { still: 1 };
  propOf('deadair', [cx, y0, cz], 0, () => {
    const L = (x0, ya, z0, x1, yb, z1, m) => B.add(cx + x0, y0 + ya, cz + z0, cx + x1, y0 + yb, cz + z1, m, S);
    L(-DA.plinth, 0, -DA.plinth, DA.plinth, 0.8, DA.plinth, 'concrete'); // the foundation
    L(-0.9, 0.8, -0.9, 0.9, DA.top, 0.9, 'metal'); // the mast (grapple it)
    const W = DA.deckW, R = 0.06;
    L(-W, DA.deck, -W, W, DA.deck + 0.25, W, 'grid'); // the work platform, railed round
    for (const s of [-1, 1]) { L(-W, DA.deck + 0.25, s * W - (s > 0 ? R : 0), W, DA.deck + 0.25 + DA.rail, s * W + (s < 0 ? R : 0), 'metal'); L(s * W - (s > 0 ? R : 0), DA.deck + 0.25, -W + R, s * W + (s < 0 ? R : 0), DA.deck + 0.25 + DA.rail, W - R, 'metal'); }
    const [b0, b1, bw] = DA.board; L(-bw, b0, 0.9, bw, b1, 1.05, 'metal'); // the DEAD AIR board, on the south face
    const F = DA.fence, g = DA.gate; // the fence round the foot (thin: chain-link), its gate open on the south side
    L(-F, 0, -F - 0.05, F, DA.fenceH, -F + 0.05, 'metal'); L(-F - 0.05, 0, -F, -F + 0.05, DA.fenceH, F, 'metal'); L(F - 0.05, 0, -F, F + 0.05, DA.fenceH, F, 'metal');
    L(-F, 0, F - 0.05, -g, DA.fenceH, F + 0.05, 'metal'); L(g, 0, F - 0.05, F, DA.fenceH, F + 0.05, 'metal');
    for (const a of DA.anchors) { const x = Math.cos(a * Math.PI / 180) * DA.anchorR, z = Math.sin(a * Math.PI / 180) * DA.anchorR; L(x - DA.anchorW, 0, z - DA.anchorW, x + DA.anchorW, DA.anchorH, z + DA.anchorW, 'concrete'); }
    // the transmitter shack: floor, walls (the door toward the mast, a window west), roof, the studio's racks and desk
    const [x0, z0, x1, z1] = DA.shack, H = DA.shackH, t = DA.wallT, [d0, d1, dt] = DA.door, [w0, w1, wy0, wy1] = DA.win, top = H - 0.3;
    L(x0, 0, z0, x1, 0.15, z1, 'concrete');
    L(x0, 0.15, z0, x1, top, z0 + t, 'metal'); L(x1 - t, 0.15, z0 + t, x1, top, z1 - t, 'metal'); // north, east
    L(x0, 0.15, z1 - t, d0, top, z1, 'metal'); L(d1, 0.15, z1 - t, x1, top, z1, 'metal'); L(d0, dt, z1 - t, d1, top, z1, 'metal'); // south: the door
    L(x0, 0.15, z0 + t, x0 + t, top, w0, 'metal'); L(x0, 0.15, w1, x0 + t, top, z1 - t, 'metal'); L(x0, 0.15, w0, x0 + t, wy0, w1, 'metal'); L(x0, wy1, w0, x0 + t, top, w1, 'metal'); // west: the window
    L(x0 - 0.15, top, z0 - 0.15, x1 + 0.15, H, z1 + 0.15, 'metal'); // roof
    for (const [r0, r1] of DA.racks) L(r0, 0.15, z0 + t, r1, 0.15 + DA.rackH, z0 + t + DA.rackD, 'metal');
    const [k0, kz0, k1, kz1, kh] = DA.desk; L(k0, 0.15, kz0, k1, kh, kz1, 'wood'); // (k1 = the east wall's inside face)
  });
}

// PORT JANKTON (the harbour town, south): the waterfront. a straight quay along the bay (PLAN.harbour: the wall is the
// ground's own), bollards on its edge, three timber piers out over the waist-deep basin, two trawlers moored at them,
// the portal crane on its rails (mechs walk under it), two warehouses you walk (or stomp) straight through (8 m doors on
// the quay and street sides, a pilot door at the end, crates and containers inside), containers stacked on the apron.
// every piece is a Blender model over its boxes (tools/blender/make_portjankton.py), built at the town's own height with
// its boxes `still`. PJ = the numbers the models are built to
export const PJ = { y: 1.6, quayZ: 146, quayX: [-30, 100], bollards: [-25, -12, 12, 24, 48, 60, 84, 95],
  piers: [0, 36, 72], pierW: 4, pierL: 30, pierT: 0.3,
  crane: { x: 56, z: 140, legX: 4, legZ: 3, leg: 1, h: 9, top: [5, 3.2, 5] }, // portal half-spans, leg size, girder top; the machinery house on top
  sheds: [{ x0: -30, x1: 0, sign: 'cold' }, { x0: 56, x1: 86, sign: 'fish' }], shedZ: [112, 132], shedH: 10, shedT: 0.3, door: [3.5, 8], side: [-3, 3, 2.6], // the mech doors: half-width, height; the pilot door (z range, height) in the west end
  boats: [{ x: 6, z: 151, side: 1 }, { x: 66, z: 151, side: -1 }], boatW: 4.2, boatL: 18, deck: 1.2, house: [3, 2.6, 4] }; // moored along a pier: hull from z to z + L
function portJankton(B) {
  const y = PJ.y, S = { still: 1 };
  const A = (x0, y0, z0, x1, y1, z1, m) => B.add(x0, y + y0, z0, x1, y + y1, z1, m, S);
  // the quay's bollards (the wall itself is the ground; its face, coping and fenders are the quay model's: p_pj_quay)
  for (let x = PJ.quayX[0]; x < PJ.quayX[1]; x += 10) propOf('pj_quay', [x + 5, y, PJ.quayZ], 0, () => A(x, PLAN.harbour.bed - y, PJ.quayZ - 1, x + 10, 0, PJ.quayZ, 'stone')); // (a solid block from the bed up: the ground's 1 m grid can't make a sheer face)
  for (const x of PJ.bollards) propOf('pj_bollard', [x, y, PJ.quayZ - 0.6], 0, () => A(x - 0.25, 0, PJ.quayZ - 0.85, x + 0.25, 0.75, PJ.quayZ - 0.35, 'metal'));
  // the piers: a timber deck out over the basin (wade under it), level with the quay
  for (const x of PJ.piers) propOf('pj_pier', [x, y, PJ.quayZ], 0, () => A(x - PJ.pierW / 2, -PJ.pierT, PJ.quayZ, x + PJ.pierW / 2, 0, PJ.quayZ + PJ.pierL, 'wood'));
  // the portal crane: four legs, the portal girders, the machinery house on top (the jib out over the water is the model's)
  { const C = PJ.crane;
    propOf('pj_crane', [C.x, y, C.z], 0, () => {
      for (const sx of [-1, 1]) for (const sz of [-1, 1]) A(C.x + sx * C.legX - C.leg / 2, 0, C.z + sz * C.legZ - C.leg / 2, C.x + sx * C.legX + C.leg / 2, C.h, C.z + sz * C.legZ + C.leg / 2, 'metal');
      A(C.x - C.legX - 0.5, C.h, C.z - C.legZ - 0.5, C.x + C.legX + 0.5, C.h + 1, C.z + C.legZ + 0.5, 'metal');
      A(C.x - C.top[0] / 2, C.h + 1, C.z - C.top[2] / 2, C.x + C.top[0] / 2, C.h + 1 + C.top[1], C.z + C.top[2] / 2, 'metal');
    }); }
  // the warehouses: walls with the mech doors (quay side and street side) and a pilot door in the west end, a roof
  const [sz0, sz1] = PJ.shedZ, H = PJ.shedH, t = PJ.shedT, [dw, dh] = PJ.door;
  for (const sh of PJ.sheds) {
    const cx = (sh.x0 + sh.x1) / 2;
    propOf('pj_shed_' + sh.sign, [cx, y, (sz0 + sz1) / 2], 0, () => {
      for (const z of [sz0, sz1 - t]) { A(sh.x0, 0, z, cx - dw, H, z + t, 'brick'); A(cx + dw, 0, z, sh.x1, H, z + t, 'brick'); A(cx - dw, dh, z, cx + dw, H, z + t, 'brick'); }
      const [p0, p1, ph] = PJ.side, zc = (sz0 + sz1) / 2;
      A(sh.x0, 0, sz0 + t, sh.x0 + t, H, zc + p0, 'brick'); A(sh.x0, 0, zc + p1, sh.x0 + t, H, sz1 - t, 'brick'); A(sh.x0, ph, zc + p0, sh.x0 + t, H, zc + p1, 'brick');
      A(sh.x1 - t, 0, sz0 + t, sh.x1, H, sz1 - t, 'brick');
      A(sh.x0 - 0.3, H, sz0 - 0.3, sh.x1 + 0.3, H + 0.3, sz1 + 0.3, 'roofg');
    });
    // inside: crate stacks along the walls (each crate a Blender crate), a container to one side (cover)
    for (const [dx, dz, n] of [[-11, -7, 3], [-7, 7, 2], [9, -7, 2], [12, 6, 3]]) for (let k = 0; k < n; k++) A(cx + dx + (k % 2) * 1.6, (k >> 1) * 1.5, (sz0 + sz1) / 2 + dz, cx + dx + (k % 2) * 1.6 + 1.5, (k >> 1) * 1.5 + 1.5, (sz0 + sz1) / 2 + dz + 1.5, 'crate');
    A(cx + 5, 0, (sz0 + sz1) / 2 - 1.2, cx + 11.06, 2.6, (sz0 + sz1) / 2 + 1.24, sh.sign === 'cold' ? 'containerb' : 'containerr'); // (off the doors' line: a mech walks straight through)
    // a forklift with a load on its forks, pallet stacks (the existing Blender models; built on the ground, the shaped ground puts them on the floor)
    const zc = (sz0 + sz1) / 2, pr = rng(4300 + sh.x0);
    forklift(B, cx - 8, zc - 3, sh.sign === 'cold' ? 1 : 3, 1);
    for (const [dx, dz, n] of [[-12.5, 4, 5], [5, -6.5, 4], [-1 + 6, 4.5, 6]]) pallets(B, cx + dx, zc + dz, n, pr);
  }
  // containers stacked on the apron (east of the crane), crates by the quay
  for (const [x, z, k, m] of [[40, 136, 0, 'containerg'], [40, 136, 1, 'containerr'], [40, 140, 0, 'containerb'], [88, 136, 0, 'containerr'], [88, 140, 0, 'containerg'], [88, 140, 1, 'containerb']]) A(x, k * 2.6, z, x + 6.06, k * 2.6 + 2.6, z + 2.44, m);
  for (const [x, z] of [[-20, 140], [-18.4, 140], [30, 143], [74, 141]]) A(x, 0, z, x + 1.5, 1.5, z + 1.5, 'crate');
  // the trawlers, moored alongside the piers: the hull (deck at 1.2 above the water), the wheelhouse aft
  for (const b of PJ.boats) {
    const x0 = b.x - PJ.boatW / 2, x1 = b.x + PJ.boatW / 2, z0 = b.z, z1 = b.z + PJ.boatL, [hw, hh, hd] = PJ.house;
    propOf('pj_trawler', [b.x, PLAN.harbour.bed, z0], 0, () => {
      B.add(x0, PLAN.harbour.bed, z0 + 1, x1, PJ.deck, z1, 'wood', S); B.add(x0 + 0.6, PLAN.harbour.bed, z0, x1 - 0.6, PJ.deck, z0 + 1, 'wood', S); // the hull (its bow narrows)
      B.add(b.x - hw / 2, PJ.deck, z1 - 1 - hd, b.x + hw / 2, PJ.deck + hh, z1 - 1, 'white', S); // the wheelhouse
    });
  }
}

function battleIsland() {
  const B = builder(), D = builder(), W = B.local(0, 0, 0), r = rng(4141), rv = rng(4242);
  const [X0, Z0, X1, Z1] = REGION, G = grid();
  B.add(X0, -12, Z0, X1, 0, Z1, 'sand'); // the slab shapeGround turns into the island (and its sea floor)
  // ---- vegetation (Blender props): palms along the beaches, the jungle along the river, bushes on the plateau
  const taken = [];
  const free = (x, z, d) => !taken.some(([a, b, e]) => Math.hypot(x - a, z - b) < d + e) && !onRoad(x, z) && !nearPoi(x, z, 4) && !nearPad(x, z, 6);
  for (let i = 0; i < 2600 && taken.length < 230; i++) { // palms: on the sand and just above it, leaning out to sea
    const x = X0 + 8 + r() * (X1 - X0 - 16), z = Z0 + 8 + r() * (Z1 - Z0 - 16), h = G.at(x, z), d = coastIn(x, z);
    if (h < SEA + 0.5 || h > SEA + 5 || G.slope(x, z) > 0.35 || !free(x, z, 3.5)) continue;
    if (d > 60 && !jungle(x, z) && r() > 0.2) continue; // (mostly the coast and the river)
    palm(W, x, z, 6 + r() * 4, rv); taken.push([x, z, 3]);
  }
  for (let i = 0; i < 6000; i++) { // the jungle floor: ferns and bushes (look only), thicker by the river
    const x = X0 + r() * (X1 - X0), z = Z0 + r() * (Z1 - Z0), h = G.at(x, z);
    if (h < SEA + 0.8 || G.slope(x, z) > 0.6 || onRoad(x, z) || nearPad(x, z, 3) || nearPoi(x, z, -6)) continue;
    if (!jungle(x, z) && r() > 0.12) continue;
    const s = 0.7 + r() * 0.9, a = r() * 3;
    if (r() < 0.55) propOf('fern', [x, 0, z], 0, () => { for (let k = 0; k < 3; k++) D.obb(x, s * 0.28, z, s * 1.5, s * 0.56, 0.07, a + k * 1.05, 'fern'); }, { spin: a || 1e-6 });
    else propOf('bush', [x, 0, z], 0, () => { D.obb(x, s * 0.3, z, s * 1.1, s * 0.6, s * 0.9, a, 'bush'); D.obb(x + 0.2, s * 0.75, z - 0.1, s * 0.7, s * 0.4, s * 0.6, a + 0.8, 'bush'); }, { spin: a || 1e-6 });
  }
  // ---- the POIs' landmarks (each one Blender model over its own boxes)
  deadAir(B, ...PLAN.pois.find((p) => p.id === 'radio').c);
  portJankton(B);
  scrapMart(B); // Scrap Mart (shared/bi_scrapmart.js)
  // ---- the sea all round (the island's shelf shows through it), on out to the horizon
  D.add(-900, SEA - 0.1, -900, 900, SEA, 900, 'bisea'); // ('bisea': Islands' sea, clearer, its own look: public/js/liquidmats.js)
  horizon(D, -900, -900, 900, 900, 2600, 'bisea', SEA);
  // ---- the spots the mode reads: the POIs' drop pads (open sky, level), energy cells, the finale circles
  const drops = [], cells = [], spawns = [];
  for (const p of PLAN.pois) {
    for (const [dx, dz, rr] of p.drop) drops.push([p.c[0] + dx, 0, p.c[1] + dz, rr]);
    const cr = rng(5000 + p.id.length * 97 + p.c[0]);
    let n = 0;
    for (let t = 0; t < 400 && n < p.cells; t++) { // cells: inside the POI, on open level-ish ground, apart
      const a = cr() * Math.PI * 2, d = p.r * (0.2 + cr() * 0.75), x = p.c[0] + Math.cos(a) * d, z = p.c[1] + Math.sin(a) * d;
      if (G.at(x, z) < SEA + 0.4 || G.slope(x, z) > 0.3 || cells.some((c) => Math.hypot(c[0] - x, c[2] - z) < 10) || B.boxes.some((q) => q.max[1] > 0.05 && x > q.min[0] - 1.5 && x < q.max[0] + 1.5 && z > q.min[2] - 1.5 && z < q.max[2] + 1.5)) continue; // (in the open, not in a building)
      cells.push([x, 0, z]); n++;
    }
    spawns.push([p.c[0], 0.2, p.c[1]]);
  }
  // ---- the ground gets its shape: the plan's heights everywhere, painted by what each bit is
  const HB = PLAN.harbour, onApron = (x, z) => x > HB.x0 - 4 && x < HB.x1 + 4 && z > 104 && z < HB.z;
  const steep = (x, z) => G.slope(x, z) > 1.05, wet = (x, z) => G.at(x, z) < SEA - 0.05, dry = (x, z) => !wet(x, z);
  const T = shapeGround(B, D, { region: REGION, mat: 'sand', seed: 77, up: 0, down: 0, step: 0.5, coarse: 2, soft: 1.15,
    relief: [
      { f: G.f, mat: 'wetsand', paint: wet }, // under the water: the shelf, the reef, the lagoon's bed (seen through the sea)
      { f: G.f, mat: 'grass', paint: (x, z) => dry(x, z) && G.at(x, z) > SEA + 1.3 && !steep(x, z) },
      { f: G.f, mat: 'leaves', paint: (x, z) => dry(x, z) && G.at(x, z) > SEA + 1.1 && jungle(x, z) && !steep(x, z) },
      { f: G.f, mat: 'stone', rock: true, paint: (x, z) => steep(x, z) }, // cliffs, the quarry's terrace faces, the ridge's crags
      { f: G.f, mat: 'dirtroad', paint: (x, z) => dry(x, z) && (onRoad(x, z) || onApron(x, z)) && !steep(x, z) }, // (the port's yard behind the quay too: a working dock, not a lawn)
    ], points: [...spawns, ...drops, ...cells] });
  for (const q of [...drops, ...cells]) q[1] = Math.round(q[1] * 100) / 100; // (lifted onto the ground by shapeGround)
  let graph = null;
  const map = {
    name: 'Battle Island', size: 'huge', royaleOnly: true, wip: true, // wip: out of the map votes until the mode lands (shared/modes.js)
    boxes: B.boxes, deco: D.boxes, killY: KILL_Y, floorY: -12, bounds: BOUNDS, chunk: 128,
    sea: true, seaY: SEA, wade: WADE, // the water's depth anywhere = seaY - the ground there (shallows <= wade: walk through)
    sky: { top: 0x1f7fe0, mid: 0xbfeaff, bot: 0x0b4a7a, fog: 0xc6ecf6 }, fogNear: 180, fogFar: 980,
    spawns, plan: PLAN,
    royale: { zone0: PLAN.zone0, blimpY: PLAN.blimpY, pois: PLAN.pois, loot: 400, cells, drops,
      finale: [[PLAN.pois.find((p) => p.id === 'radio').c[0], PLAN.pois.find((p) => p.id === 'radio').c[1], 24], [-110, 30, 48]] }, // (the summit's flat is 26 m now: the guy anchors stand in it)
    peekGraph() { return graph; }, dropGraph() { graph = null; },
    get graph() { return graph || (graph = buildNav(B.boxes, { x0: X0, z0: Z0, n: X1 - X0, cell: 2, levels: [0], band: 0.5, keep: (x, z) => !outOfBounds(map, [x, 0, z]) && G.at(x, z) > KILL_Y + 0.5 }), graph.maxExpand = 40000, graph); },
  };
  unstick(map.boxes, map.spawns);
  return map;
}
// built the first time something asks for it (a room starting on it, a client loading it, a test): importing the shared
// map list stays as fast as without it. until then it's a hidden getter, so loops over every map (graph sweeps, prop
// extents) don't build it either; once built it's an ordinary entry. in the map lists only while it's a WIP and asked for
Object.defineProperty(MAPS, 'battleisland', { configurable: true, enumerable: false, get() {
  const m = battleIsland();
  Object.defineProperty(MAPS, 'battleisland', { value: m, writable: true, configurable: true, enumerable: true });
  return m;
} });
if (WIP_ON && !MAP_ORDER.includes('battleisland')) MAP_ORDER.push('battleisland');
