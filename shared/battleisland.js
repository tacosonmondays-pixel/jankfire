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
    { name: 'Main Drag', w: 14, pts: [[28, 120], [22, 70], [18, 40], [8, -14]] }, // the harbour up to the radio tower's saddle
    { name: 'Hangar Road', w: 14, pts: [[-170, 40], [-110, 32], [-40, 26], [18, 40]] },
    { name: 'Quarry Track', w: 12, pts: [[-30, -178], [-48, -136]] },
    { name: 'Resort Drive', w: 12, pts: [[150, 96], [176, 112]] },
    { name: 'Point Road', w: 10, pts: [[-150, -40], [-210, -110], [-250, -160]] },
  ],
  // the POIs. rect = [x0, z0, x1, z1] (what the HUD names), c = its middle, y = the level it's built on (flattened),
  // flat = the radius kept flat round c, r = its radius (HUD, callouts, bots), drop = open-sky flat spots a mech is
  // called down onto ([dx, dz, radius] from c, 12 m+ across), cells = energy-cell spots (tagged apart from loot)
  pois: [
    { id: 'port', name: 'Port Jankton', c: [28, 118], rect: [-44, 84, 104, 170], y: 1.6, flat: 58, r: 66, drop: [[0, -28, 9], [-30, -6, 7]], cells: 6, color: '#4fd8ff', lab: [0, 36], loot: 0.18, blurb: 'the harbour town: docks, warehouses, a main street. the biggest drop' },
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
import { MAPS, MAP_ORDER, builder, rng, horizon, palm, unstick } from './map.js';
import { shapeGround } from './terrain.js';
import { buildNav } from './nav.js';
import { propOf } from './propcap.js';
import { outOfBounds } from './bounds.js';

export const REGION = [-410, -330, 410, 330]; // the shaped ground (whole metres): the island, its shelf, the islets
const BOUNDS = [-404, -324, 404, 324];
export const KILL_Y = SEA - WADE - 0.6; // feet this far down = in water over your head: into the sea
const DEEP = -4.2; // the deep sea's bed (drawn under the water, past where you can stand)
export const GRID = (() => { // the plan's heights on the terrain's 1 m grid, worked out once (the relief asks for every vertex five times)
  const [X0, Z0, X1, Z1] = REGION, vx = X1 - X0 + 1, vz = Z1 - Z0 + 1, H = new Float32Array(vx * vz);
  for (let i = 0; i < vx; i++) for (let j = 0; j < vz; j++) H[i * vz + j] = Math.max(DEEP, islandH(X0 + i, Z0 + j)); // (past the kill line the sea bed is flat: nobody walks there)
  const at = (x, z) => { const fx = Math.max(0, Math.min(vx - 1.001, x - X0)), fz = Math.max(0, Math.min(vz - 1.001, z - Z0)), i = Math.floor(fx), j = Math.floor(fz), u = fx - i, v = fz - j;
    return (H[i * vz + j] * (1 - u) + H[(i + 1) * vz + j] * u) * (1 - v) + (H[i * vz + j + 1] * (1 - u) + H[(i + 1) * vz + j + 1] * u) * v; };
  const slope = (x, z) => Math.hypot(at(x + 0.5, z) - at(x - 0.5, z), at(x, z + 0.5) - at(x, z - 0.5));
  // nothing steeper than a mech can walk up (the ridge, the dunes, the beaches), except where it's meant to be a wall: the
  // north-west cliffs and the quarry's terrace faces (grapple those). peaks keep their height, their flanks are eased
  const MAXS = 0.62, wall = new Uint8Array(vx * vz), C = PLAN.cliffs, Q = PLAN.quarry;
  for (let i = 0; i < vx; i++) for (let j = 0; j < vz; j++) { const x = X0 + i, z = Z0 + j; if (Math.hypot((x - C.c[0]) / C.sx, (z - C.c[1]) / C.sz) / C.r < 1.25 || Math.hypot(x - Q.c[0], z - Q.c[1]) < Q.r * 1.3 || PADS.some((q) => Math.hypot(x - q[0], z - q[1]) < q[2] + 1)) wall[i * vz + j] = 1; } // (and the drop pads: level, whatever's round them)
  for (let pass = 0; pass < 40; pass++) { // raise the low side of anything too steep (a cut-and-fill that keeps every summit and pad)
    let any = 0;
    for (let i = 1; i < vx - 1; i++) for (let j = 1; j < vz - 1; j++) { const k = i * vz + j; if (wall[k] || H[k] <= SEA) continue;
      const top = Math.max(H[k - vz], H[k + vz], H[k - 1], H[k + 1]) - MAXS; if (H[k] < top) { H[k] = top; any++; } }
    for (let i = vx - 2; i > 0; i--) for (let j = vz - 2; j > 0; j--) { const k = i * vz + j; if (wall[k] || H[k] <= SEA) continue;
      const top = Math.max(H[k - vz], H[k + vz], H[k - 1], H[k + 1]) - MAXS; if (H[k] < top) { H[k] = top; any++; } }
    if (!any) break;
  }
  return { H, vx, vz, at, slope, f: (x, z) => H[(x - X0) * vz + (z - Z0)] };
})();
const onRoad = (x, z) => PLAN.roads.some((r) => segDist(x, z, r.pts) < r.w / 2);
const jungle = (x, z) => segDist(x, z, PLAN.river.pts) < 46 || Math.hypot(x - 70, z + 6) < 58;
const nearPoi = (x, z, m = 0) => PLAN.pois.some((p) => Math.hypot(x - p.c[0], z - p.c[1]) < p.r + m);
const nearPad = (x, z, m = 0) => PLAN.pois.some((p) => p.drop.some(([dx, dz, r]) => Math.hypot(x - p.c[0] - dx, z - p.c[1] - dz) < r + m));

// DEAD AIR (the summit): the island's landmark, a 70 m guyed lattice radio mast (tools/blender/make_deadair.py,
// p_deadair: one Blender model over all of these boxes). the mast is a column you grapple, its work platform at 50 m
// you can stand on, the transmitter shack is locked (solid: loot on its roof), the guy wires' three anchor blocks are
// cover. built at y 0 round the mast's foot: the shaped ground lifts it onto the summit. DA = the numbers the model is
// built to (the Blender script reads the same table)
export const DA = { plinth: 2, top: 70, deck: 50, deckW: 2.2, anchors: [80, 200, 320], anchorR: 18, anchorW: 0.9, anchorH: 0.9,
  shack: [-5.7, -12.4, 2.3, -7.4], shackH: 3.6 };
function deadAir(B, cx, cz) {
  propOf('deadair', [cx, 0, cz], 0, () => {
    B.add(cx - DA.plinth, 0, cz - DA.plinth, cx + DA.plinth, 0.8, cz + DA.plinth, 'concrete'); // the foundation
    B.box(cx, 0.8 + (DA.top - 0.8) / 2, cz, 1.8, DA.top - 0.8, 1.8, 'metal'); // the mast (grapple it)
    B.add(cx - DA.deckW, DA.deck, cz - DA.deckW, cx + DA.deckW, DA.deck + 0.25, cz + DA.deckW, 'grid'); // the work platform
    for (const a of DA.anchors) { const x = cx + Math.cos(a * Math.PI / 180) * DA.anchorR, z = cz + Math.sin(a * Math.PI / 180) * DA.anchorR; B.add(x - DA.anchorW, 0, z - DA.anchorW, x + DA.anchorW, DA.anchorH, z + DA.anchorW, 'concrete'); }
    const [x0, z0, x1, z1] = DA.shack; B.add(cx + x0, 0, cz + z0, cx + x1, DA.shackH, cz + z1, 'metal'); // the transmitter shack (locked)
  });
}

function battleIsland() {
  const B = builder(), D = builder(), W = B.local(0, 0, 0), r = rng(4141), rv = rng(4242);
  const [X0, Z0, X1, Z1] = REGION, G = GRID;
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
  // ---- the sea all round (the island's shelf shows through it), on out to the horizon
  D.add(-900, SEA - 0.1, -900, 900, SEA, 900, 'sea');
  horizon(D, -900, -900, 900, 900, 2600, 'sea', SEA);
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
  const steep = (x, z) => G.slope(x, z) > 1.05, wet = (x, z) => G.at(x, z) < SEA - 0.05, dry = (x, z) => !wet(x, z);
  const T = shapeGround(B, D, { region: REGION, mat: 'sand', seed: 77, up: 0, down: 0, step: 0.5, coarse: 2, soft: 1.15,
    relief: [
      { f: G.f, mat: 'wetsand', paint: wet }, // under the water: the shelf, the reef, the lagoon's bed (seen through the sea)
      { f: G.f, mat: 'grass', paint: (x, z) => dry(x, z) && G.at(x, z) > SEA + 1.3 && !steep(x, z) },
      { f: G.f, mat: 'leaves', paint: (x, z) => dry(x, z) && G.at(x, z) > SEA + 1.1 && jungle(x, z) && !steep(x, z) },
      { f: G.f, mat: 'stone', rock: true, paint: (x, z) => steep(x, z) }, // cliffs, the quarry's terrace faces, the ridge's crags
      { f: G.f, mat: 'dirtroad', paint: (x, z) => dry(x, z) && onRoad(x, z) && !steep(x, z) },
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
      finale: [[PLAN.pois.find((p) => p.id === 'radio').c[0], PLAN.pois.find((p) => p.id === 'radio').c[1], 24], [-110, 30, 48]] },
    get graph() { return graph || (graph = buildNav(B.boxes, { x0: X0, z0: Z0, n: X1 - X0, cell: 2, levels: [0], band: 0.5, keep: (x, z) => !outOfBounds(map, [x, 0, z]) && G.at(x, z) > KILL_Y + 0.5 }), graph.maxExpand = 40000, graph); },
  };
  unstick(map.boxes, map.spawns);
  return map;
}
export const BATTLE_ISLAND = battleIsland();
MAPS.battleisland = BATTLE_ISLAND;
if (!MAP_ORDER.includes('battleisland')) MAP_ORDER.push('battleisland');
