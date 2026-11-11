// TICKETS, PLEASE (m06): the train arena and the shape of the REVENUE PROTECTION fight, shared by the referee
// (server/storytrain.js: it owns HP, phases, arms, hits and THE GAP) and the client (public/js/story/trainfight.js: it
// only shows them). pure: no node, no dom. design: docs/story/TRAIN.md §4, what is built: docs/story/train/FIGHT.md
//   the world: the train stands still at z 0 .. 21 (the wagon's back rail is z = 0) in a 9.2 m bore; the tunnel is
//   scrolled past by the client. the mask is behind you at z = -gap, facing +z, its middle on the bore's axis (y = cy)
//   the boss model's own space (revenue_protection.parts.json): x right, y up, +z toward the train; world = [x, cy + y, z - gap]

// ---------------------------------------------------------------- the world (shared/story/worlds.js lists it)
// THE TABLE: every size of the arena is here. the room's collision boxes (buildTrainMap), the client's stand-in train
// (trainfight.js draws these boxes itself, so a Blender train can replace them, built to this), where arms grip, where
// you are put back, and the tests all read it. metres; z runs from the back of the train (0) to the front
export const HW = 2.1; // half the deck's width: 4.2 m across (the bore is 9.2 m, so the arms still have wall to walk along)
export const CARS = [ // back to front. deck = the top of its floor. the first one's back rail is THE GAP's zero
  { id: 'wagon', z0: 0.2, z1: 9.2, deck: 1.0, rail: 0.75 }, // the low open wagon: a rail round three sides (too tall to step over, low enough to jump)
  { id: 'flat', z0: 9.8, z1: 19.8, deck: 1.3 }, // the flatbed: crates, the chained-down fridge
  { id: 'van', z0: 20.4, z1: 27.4, deck: 1.3, roof: 3.45, roofZ0: 22.8, under: 2.0, stairs: 4, stairW: 1.1 }, // the tool van: a flat roof on posts (open sides: a sweeper passes under it), stairs up its left side
  { id: 'loco', z0: 28.0, z1: 33.0, deck: 0.5, top: 3.6 }, // not part of the fight: the front wall
];
export const CAR = Object.fromEntries(CARS.map((c) => [c.id, c]));
export const COVER = [ // [car, x, z, width, height, depth, material]: stands on its car's deck. the middle lane stays clear, and there is always some within about 4 m
  ['wagon', -1.25, 2.6, 1, 1, 1, 'crate'], ['wagon', 1.25, 6.2, 1, 1, 1, 'crate'],
  ['flat', -1.25, 11.4, 1, 1, 1, 'crate'], ['flat', 1.25, 13.6, 1, 1.8, 1, 'crate'], ['flat', -1.25, 16.4, 0.9, 1.9, 0.8, 'white'], ['flat', 1.25, 18.4, 1, 1, 1, 'crate'], // (white: the fridge)
  ['van', 1.4, 24.2, 0.8, 1.1, 1.6, 'metal'], ['van', -1.4, 26.3, 0.8, 1.1, 1.4, 'metal'], // tool lockers under the roof
];
export const CREW = [ // where the three would fight (static stand-ins for now: no AI). until: the phase they are there up to
  { id: 'pallet_jack', p: [0.9, 1.0, 1.2], yaw: 0, until: 0 }, // at the back rail
  { id: 'lumps', p: [-1.1, 1.3, 14.2], yaw: 0, until: 2 }, // hauling crates on the flatbed (off the middle lane: you shoot down it)
  { id: 'gordo', p: [1.3, 1.3, 21.4], yaw: 0, until: 2 }, // by the van's stairs, with the blood bags
];
const FAR = { p: [0, -900, 0], r: 0.1 }; // no Machine, Locker or clinic on a train
export const TRAIN = { id: 'story_train', name: 'The Under-Hill Loop', killY: -30, spawn: [0, 1.1, 4.7], yaw: 0, terminal: FAR, locker: FAR, clinic: FAR };
export const ARENA = { boreR: 4.6, cy: 3.13, z0: -70, z1: 56, cut: CAR.flat.z0 }; // the bore, its axis above the track bed (y = 0), how far the tunnel's boxes run · the train's back once the wagon is bitten off
export const deckAt = (z) => (z < (CAR.wagon.z1 + CAR.flat.z0) / 2 ? CAR.wagon.deck : CAR.flat.deck);
// what you stand on at z: the deck, or the van's roof / stairs if you are up there (feet at y)
export const onRoof = (p) => p[2] >= CAR.van.z0 && p[2] <= CAR.van.z1 && p[1] - CAR.van.deck >= CAR.van.roof - CAR.van.deck - 0.4;
// off the train: down on the track bed, or past the side / the back and already below the deck's edge. rear: the train's back (0, or ARENA.cut once the wagon is gone)
export const offTrain = (p, rear = 0) => p[1] < 0.75 || ((Math.abs(p[0]) > HW + 0.55 || p[2] < rear - 0.25) && p[1] < deckAt(p[2]) + 0.15);
// where you are put back: the middle of the rear-most car still on the train
export const backSpot = (rear = 0) => { const c = rear > 0 ? CAR.flat : CAR.wagon; return [0, c.deck + 0.1, c.z0 + (c.z1 - c.z0) * (rear > 0 ? 0.35 : 0.5)]; };
// where a Grabber takes hold of the rear-most car: three spots a side and two on the back. p: the grip point, o: which way is outboard
export function gripSpots(rear = 0) {
  const c = rear > 0 ? CAR.flat : CAR.wagon, y = c.deck + (c.rail || 0), L = c.z1 - c.z0, out = [];
  for (const sx of [1, -1]) for (const k of [0.15, 0.5, 0.85]) out.push({ p: [sx * (HW - 0.05), y, c.z0 + L * k], o: [sx, 0], side: sx });
  for (const sx of [1, -1]) out.push({ p: [sx * 0.9, y, c.z0 + 0.05], o: [sx * 0.3, -0.95], side: sx });
  return out;
}

// the train's boxes carry { car, pv: 'rp_train' }: car = which car (the room drops the wagon's when it is bitten off), pv = the
// client's stand-in draws them (world.js leaves a box alone when a prop of that name is registered; without one they are plain boxes)
export function buildTrainMap(kit) {
  const B = kit.builder(), D = kit.builder(), A = ARENA;
  B.add(-6.2, -2, A.z0, 6.2, 0, A.z1, 'dirt'); // the track bed
  // the tunnel's walls and roof stand just behind the round lining the client draws (collisions stay boxes)
  B.add(-6.2, 0, A.z0, -A.boreR - 0.1, 9, A.z1, 'brick'); B.add(A.boreR + 0.1, 0, A.z0, 6.2, 9, A.z1, 'brick'); B.add(-6.2, A.cy + A.boreR + 0.1, A.z0, 6.2, 9.4, A.z1, 'brick');
  B.add(-6.2, 0, A.z0 - 1, 6.2, 9.4, A.z0, 'brick'); B.add(-6.2, 0, A.z1, 6.2, 9.4, A.z1 + 1, 'brick');
  for (const x of [-0.75, 0.75]) D.add(x - 0.05, 0, A.z0, x + 0.05, 0.14, A.z1, 'metal'); // the rails
  const add = (car, x0, y0, z0, x1, y1, z1, mat) => B.add(x0, y0, z0, x1, y1, z1, mat, { car, pv: 'rp_train' });
  for (let i = 0; i < CARS.length; i++) {
    const c = CARS[i], n = CARS[i + 1];
    if (c.id === 'loco') { add(c.id, -HW + 0.4, c.deck, c.z0, HW - 0.4, 2.2, c.z1, 'yellow'); add(c.id, -HW + 0.4, 2.2, c.z0 + 0.3, HW - 0.4, c.top, c.z0 + 2.6, 'yellow'); continue; } // more of a tractor, but it's on rails
    add(c.id, -HW, c.deck - 0.2, c.z0, HW, c.deck, c.z1, c.id === 'wagon' ? 'wood' : 'metal');
    if (c.rail) { for (const sx of [-1, 1]) add(c.id, sx * HW, c.deck, c.z0, sx * (HW - 0.1), c.deck + c.rail, c.z1, 'metal'); add(c.id, -HW, c.deck, c.z0, HW, c.deck + c.rail, c.z0 + 0.1, 'metal'); }
    if (c.roof) { // the tool van: stairs up the left side, then a flat roof on posts
      const rise = (c.roof - c.deck) / c.stairs, run = (c.roofZ0 - c.z0) / c.stairs;
      for (let k = 0; k < c.stairs; k++) add(c.id, -HW, c.deck, c.z0 + k * run, -HW + c.stairW, c.deck + (k + 1) * rise, c.roofZ0, 'wood');
      add(c.id, -HW, c.deck + c.under, c.roofZ0, HW, c.roof, c.z1, 'metal');
      for (const sx of [-1, 1]) for (const z of [c.roofZ0, c.z1 - 0.14]) add(c.id, sx * HW, c.deck, z, sx * (HW - 0.14), c.deck + c.under, z + 0.14, 'metal');
    }
    if (n) add(i === 0 ? 'wagon' : c.id, -1.1, Math.min(c.deck, n.deck) - 0.3, c.z1, 1.1, Math.min(c.deck, n.deck), n.z0, 'metal'); // the coupling, decked over (the wagon's goes with the wagon)
  }
  for (const [car, x, z, w, h, d, mat] of COVER) add(car, x - w / 2, CAR[car].deck, z - d / 2, x + w / 2, CAR[car].deck + h, z + d / 2, mat);
  return {
    name: TRAIN.name, size: 'story', boxes: B.boxes, deco: D.boxes, killY: TRAIN.killY, floorY: -2, bounds: [-6.2, A.z0, 6.2, A.z1],
    sky: { top: 0x050307, mid: 0x050307, bot: 0x050307, fog: 0x050307 }, fogNear: 18, fogFar: 78, // a lot of dark
    sealed: true, light: { hemi: [0x7a6a8a, 0x1a1012, 0.5], sun: [0xffe0c0, 0.15] },
    spawns: [TRAIN.spawn.slice()], story: true,
  };
}

// ---------------------------------------------------------------- the numbers
// from docs/story/TRAIN.md where it gives one (marked "design"); the rest chosen for the first playable (marked "chosen").
// the boss's HP, layers, phase thresholds and crits are not here: they come from content/bosses.js + boss_fights.js
export const RP = {
  gap: { start: 22, max: 22, grab: 1, moment: 6, // chosen: starts 22 m (the design says 30: at 30 the mask reads small from the wagon) · design: each gripping arm closes it 1 m/s · 6 m and holds for the middle scene
    sever: 2, flinch: 5, retry: 16, send: 0.25 }, // chosen: a severed arm opens it 2 m, a flinch 5 m · a retry starts at 16 m · seconds between gap messages
  arm: { hp: 320, rope: 0.15, // chosen: an arm's HP (the wrist knot takes the content's x2: 9 bolts) · hits on the rope / the hand count this much
    max: [4, 4, 5], first: 2.5, every: [[3, 4.5], [2.6, 3.8], [1.9, 2.8]], // chosen: arms at once per phase (design: 4) · seconds to the first · between arms
    mix: [{ grab: 5, sweep: 3, snatch: 2 }, { grab: 5, sweep: 3, snatch: 3 }, { grab: 6, sweep: 3, snatch: 2 }], // chosen: how often each kind comes
    blood: 20, cut: 1.1, back: 1 }, // chosen: HP back for a sever (design: "gives blood back") · seconds a stump whips back · an arm takes to leave
  grab: { reach: 3.5 }, // chosen: seconds from the rim to the rail (the tell)
  sweep: { tell: 1.4, speed: 12, back: 1.6, z1: 27.6, x: 3.6, dmg: 22, kb: [6, 5, 6], low: 0.55, over: 1.75, half: 0.45, y: [0.45, 1.65] }, // chosen: it lies across 1.6 m behind the train, then runs every deck to the van's front at 12 m/s. y: the bar above the deck under it. knee: be 0.55 m off the deck. head: slide or crouch. on the van's roof (1.75 m up) both pass under you
  snatch: { reach: 2.2, hold: 6, dmg: 40, gap: 5, up: 2.5, roof: 0.6 }, // design: 6 s to shoot it off · chosen: the rest (v1 goes for you: the crew isn't simulated). roof: the chance the next arm is a Snatcher while you are on the van's roof
  flinch: { n: 4, within: 10, open: 5 }, // design: four severs inside ten seconds · chosen: the eye housings stay open 5 s
  mask: { plateHp: 240, craze: 0.5, soft: 0.5, far: 0.25 }, // chosen: a plate's HP, crazed at half · holes / the lamps · phase 3, anything that isn't the Inspector
  stages: [['hairline', 60], ['left_eye', 45], ['smile', 30]], // chosen: the HP % each break stage starts at (design: the order, in phase 2)
  jack: 90, // chosen: seconds Jack holds the rail (his bar): phase 1 ends at 60% (design) or when it runs out
  lunge: { every: [8, 11], tell: 1.5, gap: 4, min: 1.5, bite: 6, dmg: 35, reach: 3.5 }, // chosen: phase 3. it rears, then takes 4 m. the first one bites the rear wagon off (design): be on the flatbed. after that, inside 6 m it bites the back 3.5 m of the train
  bag: { every: 10, hp: 20 }, // chosen: Gordo's blood bags, caught for you (design: "on a timer")
  off: { dmg: 25, grace: 1.5 }, // chosen: the track takes 25 and you are put back (fairer than a death)
  cut: 1, fail: 2, // seconds a phase change holds at least · a caught fight waits before it restarts
  slack: 0.14, knotR: 0.42, ropeR: 0.32, critSlack: 0.25, // metres round a part when checking a shot
};

// ---------------------------------------------------------------- the model's numbers (revenue_protection.parts.json; these are the same, for when it isn't loaded)
const CRACK0 = [[-4.33, -0.203], [-3.969, -0.275], [-3.608, -0.347], [-3.248, -0.42], [-2.887, -0.492], [-2.526, -0.61], [-2.165, -0.869], [-1.804, -1.074], [-1.443, -1.233], [-1.083, -1.352], [-0.722, -1.435], [-0.361, -1.484], [0, -1.5], [0.361, -1.484], [0.722, -1.435], [1.083, -1.352], [1.443, -1.233], [1.804, -1.074], [2.165, -0.869], [2.526, -0.61], [2.887, -0.492], [3.248, -0.42], [3.608, -0.347], [3.969, -0.275], [4.33, -0.203]];
export const GEO0 = {
  maskR: 4.35, faceZ: 0.14,
  sockets: [14, 46, 76, 104, 134, 166, 194, 226, 256, 284, 314, 346].map((d) => [4.5 * Math.cos(d * Math.PI / 180), 4.5 * Math.sin(d * Math.PI / 180), -0.5]),
  mouth: [[-2.6, -1.299, -0.7], [-1.5, -1.96, -0.7], [1.5, -1.96, -0.7], [2.6, -1.299, -0.7]],
  eyes: { L: { c: [1.25, 0.7], h: [0.6, 1.08] }, R: { c: [-1.25, 0.7], h: [0.6, 1.08] } },
  insp: { crit: [0, -2.404, -0.721], r: 0.2, body: { c: [-0.05, -2.5, -0.88], h: [0.31, 0.47, 0.17] }, head: { c: [0, -1.84, -0.88], h: [0.17, 0.23, 0.2] } },
  crack: CRACK0,
};
const fin = Number.isFinite;
const vN = (a, n, max) => (Array.isArray(a) && a.length === n && a.every((x) => fin(x) && Math.abs(x) <= max) ? a.slice() : null);
// the parts file, kept only as far as it makes sense (data from the model pipeline, but the room trusts nothing)
export function geoFrom(j) {
  const G = JSON.parse(JSON.stringify(GEO0)), m = j && typeof j === 'object' && j.markers && typeof j.markers === 'object' ? j.markers : null;
  if (!m) return G;
  const list = (a, n) => (Array.isArray(a) && a.length === n ? a.map((s) => s && vN(s.pos, 3, 20)) : []);
  const so = list(m.sockets, 12), mo = list(m.mouth_sockets, 4);
  if (so.length === 12 && so.every(Boolean)) G.sockets = so;
  if (mo.length === 4 && mo.every(Boolean)) G.mouth = mo;
  for (const k of ['L', 'R']) { const e = m['eye_' + k], c = e && vN(e.centre, 3, 20), h = e && vN(e.half, 2, 5); if (c && h && h.every((x) => x > 0.05)) G.eyes[k] = { c: [c[0], c[1]], h }; }
  const I = m.inspector, cr = I && vN(I.crit, 3, 20);
  if (cr && fin(I.crit_r) && I.crit_r > 0 && I.crit_r < 3) { G.insp.crit = cr; G.insp.r = I.crit_r; }
  if (Array.isArray(m.smile_crack) && m.smile_crack.length >= 2 && m.smile_crack.length <= 64 && m.smile_crack.every((p) => vN(p, 2, 20))) G.crack = m.smile_crack.map((p) => p.slice()).sort((a, b) => a[0] - b[0]);
  if (fin(m.plate_face_z) && Math.abs(m.plate_face_z) < 2) G.faceZ = m.plate_face_z;
  if (j.tunnel && fin(j.tunnel.mask_r) && j.tunnel.mask_r > 1 && j.tunnel.mask_r < 20) G.maskR = j.tunnel.mask_r;
  for (const p of Array.isArray(j.parts) ? j.parts.slice(0, 200) : []) { const k = p && (p.name === 'insp_body' ? 'body' : p.name === 'insp_head' ? 'head' : ''), c = k && vN(p.centre, 3, 20), h = k && vN(p.half, 3, 5); if (c && h && h.every((x) => x > 0)) G.insp[k] = { c, h }; }
  return G;
}

// ---------------------------------------------------------------- the mask's face: which plate, which eye, the mouth
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
export const ss = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };
export const PLATES = 12, LOW = [9, 10], SPLIT = [2, 3, 8, 11]; // wholly under the smile crack · cut in two by it
// 00-03 the inner quadrants from +x counter-clockwise, 04-11 the outer ring, 45 degrees each
export function plateAt(x, y) {
  const a = (Math.atan2(y, x) + Math.PI * 2) % (Math.PI * 2);
  return Math.hypot(x, y) < 2.3 ? Math.min(3, Math.floor(a / (Math.PI / 2))) : 4 + Math.min(7, Math.floor(a / (Math.PI / 4)));
}
export function crackY(G, x) {
  const c = G.crack; if (x <= c[0][0]) return c[0][1]; if (x >= c[c.length - 1][0]) return c[c.length - 1][1];
  let i = 0; while (i < c.length - 2 && c[i + 1][0] < x) i++;
  const k = (x - c[i][0]) / Math.max(1e-6, c[i + 1][0] - c[i][0]);
  return c[i][1] + (c[i + 1][1] - c[i][1]) * k;
}
const inEye = (e, x, y) => ((x - e.c[0]) / e.h[0]) ** 2 + ((y - e.c[1]) / e.h[1]) ** 2 <= 1;

// ---------------------------------------------------------------- arms: a rope from a rim socket along the tunnel wall to a wrist
// an arm: { k: 'grab' | 'sweep' | 'snatch', sock, mouth, tgt: [x, y, z] (the wrist, world), st, t (seconds in st), dur }
export const wallA = (side, y) => { const a = Math.asin(Math.max(-0.47, Math.min(1, (y - ARENA.cy) / 4.28))); return side > 0 ? a : Math.PI - a; }; // the wall at height y, on the +x / -x side
const AMIN = -0.5, AMAX = Math.PI + 0.5, RWALL = 4.28; // the wall run keeps off the floor · the rope's middle sits this far out
const quad = (a, c, b, u) => [0, 1, 2].map((i) => (1 - u) * (1 - u) * a[i] + 2 * u * (1 - u) * c[i] + u * u * b[i]);
// how far along its path an arm is: it walks out along the wall (the tell), holds, and whips back
export function armExt(a) {
  const u = a.dur > 0 ? a.t / a.dur : 1;
  if (a.st === 'reach' || a.st === 'tell') return 0.1 + 0.9 * ss(u);
  if (a.st === 'back' || a.st === 'cut') return 1 - 0.9 * ss(u);
  return 1;
}
// a sweeper's bar: behind the wagon through the tell, then along the deck
export const sweepZ = (a) => { const z0 = (a.rear || 0) - RP.sweep.back; return a.st === 'sweep' ? Math.min(RP.sweep.z1, z0 + RP.sweep.speed * a.t) : a.st === 'back' ? RP.sweep.z1 : z0; }; // (a.rear: the train's back when it came)
export const sweepY = (a, z = sweepZ(a)) => deckAt(Math.max(z, (a.rear || 0) + 0.3)) + RP.sweep.y[a.hi ? 1 : 0]; // the bar keeps its height over the deck under it
// the whole path, socket to wrist (world points)
export function armPts(G, a, gap) {
  const cy = ARENA.cy, S = (a.mouth ? G.mouth : G.sockets)[a.sock] || G.sockets[0], T = a.tgt, zs = S[2] - gap, P0 = [S[0], cy + S[1], zs], out = [];
  if (a.mouth) { // out of the mouth: no wall, one arc over the gap
    const c = [S[0] * 0.5 + T[0] * 0.5, Math.max(P0[1], T[1]) + 1.6, (zs + T[2]) / 2];
    for (let i = 0; i <= 14; i++) out.push(quad(P0, c, T, i / 14));
    return out;
  }
  let a0 = Math.atan2(S[1], S[0]), a1 = fin(a.wa) ? a.wa : Math.atan2(T[1] - cy, T[0]); // (wa: the wall angle it keeps to: a sweeper stays on its own side)
  if (a0 < -Math.PI / 2) a0 += Math.PI * 2; if (a1 < -Math.PI / 2) a1 += Math.PI * 2;
  a1 = clamp(a1, AMIN, AMAX);
  const r0 = Math.hypot(S[0], S[1]), lead = a.k === 'sweep' ? 0.7 : 2.6, zl = Math.max(zs + 1.5, T[2] - lead);
  for (let i = 0; i <= 10; i++) {
    const u = i / 10, z = zs + (zl - zs) * u, an = clamp(a0 + (a1 - a0) * ss(u), Math.min(a0, AMIN), Math.max(a0, AMAX)), r = r0 + (RWALL - r0) * clamp((z - zs) / 3, 0, 1);
    out.push([r * Math.cos(an), cy + r * Math.sin(an), z]);
  }
  const Wl = out[out.length - 1], c = a.k === 'sweep' ? [Wl[0], T[1], T[2]] : [Wl[0] * 0.92 + T[0] * 0.08, Wl[1] * 0.7 + T[1] * 0.3, Wl[2] + lead * 0.8];
  for (let i = 1; i <= 8; i++) out.push(quad(Wl, c, T, i / 8));
  return out;
}
// the path up to `ext` of its length: { pts, wrist, dir (the way the wrist points), len }
export function armPose(G, a, gap, ext = armExt(a)) {
  const all = armPts(G, a, gap), d = [0];
  for (let i = 1; i < all.length; i++) d.push(d[i - 1] + Math.hypot(all[i][0] - all[i - 1][0], all[i][1] - all[i - 1][1], all[i][2] - all[i - 1][2]));
  const want = d[d.length - 1] * clamp(ext, 0.02, 1), pts = [all[0]];
  let i = 1; for (; i < all.length && d[i] < want; i++) pts.push(all[i]);
  i = Math.min(i, all.length - 1);
  const k = d[i] > d[i - 1] ? clamp((want - d[i - 1]) / (d[i] - d[i - 1]), 0, 1) : 1, A = all[i - 1], Bp = all[i];
  const wrist = [0, 1, 2].map((n) => A[n] + (Bp[n] - A[n]) * k), l = Math.hypot(Bp[0] - A[0], Bp[1] - A[1], Bp[2] - A[2]) || 1;
  pts.push(wrist);
  return { pts, wrist, dir: [(Bp[0] - A[0]) / l, (Bp[1] - A[1]) / l, (Bp[2] - A[2]) / l], len: want };
}
export const armLive = (a) => a.st === 'reach' || a.st === 'tell' || a.st === 'grip' || a.st === 'sweep' || a.st === 'hold';

// ---------------------------------------------------------------- a shot against the fight
function raySphere(o, d, c, r) {
  const x = o[0] - c[0], y = o[1] - c[1], z = o[2] - c[2], b = x * d[0] + y * d[1] + z * d[2], q = x * x + y * y + z * z - r * r;
  if (q <= 0) return 0; const disc = b * b - q; if (disc < 0) return -1; const t = -b - Math.sqrt(disc); return t >= 0 ? t : -1;
}
// a ray against a fat line a-b (radius r): the distance along the ray where it comes closest, or -1
function raySeg(o, d, a, b, r) {
  const u = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], w = [o[0] - a[0], o[1] - a[1], o[2] - a[2]];
  const uu = u[0] * u[0] + u[1] * u[1] + u[2] * u[2], ud = u[0] * d[0] + u[1] * d[1] + u[2] * d[2], uw = u[0] * w[0] + u[1] * w[1] + u[2] * w[2], dw = d[0] * w[0] + d[1] * w[1] + d[2] * w[2];
  const den = uu - ud * ud; let s = den > 1e-9 ? clamp((uw - ud * dw) / den, 0, 1) : 0, t = s * ud - dw;
  if (t < 0) { t = 0; s = uu > 1e-9 ? clamp(uw / uu, 0, 1) : 0; }
  const dx = w[0] + d[0] * t - u[0] * s, dy = w[1] + d[1] * t - u[1] * s, dz = w[2] + d[2] * t - u[2] * s;
  return dx * dx + dy * dy + dz * dz <= r * r ? t : -1;
}
function rayBox(o, d, c, h, g) {
  let t0 = 0, t1 = 1e9;
  for (let a = 0; a < 3; a++) {
    const lo = c[a] - h[a] - g, hi = c[a] + h[a] + g;
    if (Math.abs(d[a]) < 1e-9) { if (o[a] < lo || o[a] > hi) return -1; continue; }
    let a0 = (lo - o[a]) / d[a], a1 = (hi - o[a]) / d[a]; if (a0 > a1) { const x = a0; a0 = a1; a1 = x; }
    if (a0 > t0) t0 = a0; if (a1 < t1) t1 = a1; if (t0 > t1) return -1;
  }
  return t0;
}
// what a shot from o along d (unit, world) lands on first: { part, t, at, arm?, i? } or null.
//   F: { gap, arms (iterable), plates: [0 on | 1 crazed | 2 gone] x 12, open (the eye housings, a flinch), eyeL (blown),
//        smile (the lower third is off: the mouth, the Inspector) }
//   parts: knot (an arm's wrist: the weak point) · rope (the rest of an arm) · plate · hole (a plate that fell) ·
//          eye (an open or blown housing) · lamp (a shut one) · insp (the Inspector's crit spot) · inspbody · mass
export function rayFight(G, F, o, d, max = 200) {
  let best = null;
  const take = (t, part, x) => { if (t >= 0 && t <= max && (!best || t < best.t)) best = { part, t, ...x }; };
  for (const a of F.arms) {
    if (!armLive(a)) continue;
    const P = armPose(G, a, F.gap), kt = raySphere(o, d, P.wrist, RP.knotR + RP.slack);
    if (kt >= 0) { take(kt, 'knot', { arm: a.id }); continue; } // (the knot wins over the rope next to it)
    for (let i = 1; i < P.pts.length; i++) take(raySeg(o, d, P.pts[i - 1], P.pts[i], RP.ropeR), 'rope', { arm: a.id });
    take(raySeg(o, d, P.wrist, [0, 1, 2].map((n) => P.wrist[n] + P.dir[n] * 1.6), RP.ropeR + 0.1), 'rope', { arm: a.id }); // the hand
  }
  const cy = ARENA.cy, zf = G.faceZ - F.gap;
  if (d[2] < -1e-6) {
    const t = (zf - o[2]) / d[2], x = o[0] + d[0] * t, y = o[1] + d[1] * t - cy;
    if (t > 0 && Math.hypot(x, y) <= G.maskR && (!best || t < best.t) && t <= max) {
      const i = plateAt(x, y);
      if (F.smile && y < crackY(G, x)) { // the mouth: the Inspector, and four hundred people in one piece
        const I = G.insp, w = (c) => [c[0], cy + c[1], c[2] - F.gap];
        if (raySphere(o, d, w(I.crit), I.r + RP.critSlack) >= 0) best = { part: 'insp', t };
        else if (rayBox(o, d, w(I.body.c), I.body.h, RP.slack) >= 0 || rayBox(o, d, w(I.head.c), I.head.h, RP.slack) >= 0) best = { part: 'inspbody', t };
        else best = { part: 'mass', t };
      } else if (inEye(G.eyes.L, x, y)) best = { part: F.open || F.eyeL ? 'eye' : 'lamp', t, i };
      else if (inEye(G.eyes.R, x, y)) best = { part: F.open ? 'eye' : 'lamp', t, i };
      else best = { part: F.plates[i] === 2 ? 'hole' : 'plate', t, i };
    }
  }
  if (best) best.at = [o[0] + d[0] * best.t, o[1] + d[1] * best.t, o[2] + d[2] * best.t];
  return best;
}
