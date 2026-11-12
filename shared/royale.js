// Battle Royale ("JANK ROYALE"): everyone rides the drop blimp over the map, jumps, glides down with an umbrella,
// loots the floor and fights inside a shrinking zone. last one standing wins. shared by the server (the real rules)
// and the client (loot labels, the zone wall, the blimp's path, the glide).
import { GAMES, GAME_ORDER, TARGETS } from './modes.js';
import { MAPS } from './map.js';
import { PLAN as JB } from './jankburg.js'; // (registers the Jankburg map)
import './battleisland.js'; // (registers Battle Island: the mech royale's island, docs/maps/battleisland/DESIGN.md)
import { WEAPONS, ITEMS, FLAGS } from './weapons.js';

FLAGS.GLIDE = 1 << 18; // under an umbrella (everyone sees it open over your head). its own bit: 32768 is the rig's block, which the server clears on anyone not rigged

// maps big enough for it (a walled play area + scenery out to the horizon). mapOk reads this flag
// Jank Royale only plays on Jankburg, the big city (it used to also run on Desert, Warehouse and Suburb)
// Jankburg: the big one. the first circle covers the city and the outer ring; each district is a POI (see POI below)
if (MAPS.jankburg) MAPS.jankburg.royale = { zone0: [0, 0, 300], blimpY: 195, pois: JB.districts, loot: 380 };
// which POI a point is in (null outside them)
export function poiAt(map, p) { const ps = map && map.royale && map.royale.pois; return (ps && ps.find((d) => p[0] >= d.rect[0] && p[0] <= d.rect[2] && p[2] >= d.rect[1] && p[2] <= d.rect[3])) || null; }

Object.assign(GAMES, {
  br: { name: 'Jank Royale', desc: 'battle royale. jump out of the blimp, loot the floor, stay in the zone. last one standing wins', teams: false, royale: true, mapOk: (m) => !!(m && m.royale) },
});
GAME_ORDER.push('br');
TARGETS.ffa.br = 0; TARGETS.bots.br = 0; // no kill limit: last one standing

export const BR = {
  bots: 15, // a Bots room fills up to this many bots for a royale (the room's own count if it's higher)
  blimp: { speed: 24, len: 200, wait: 2.5 }, // m/s, half the path length past the middle (m), seconds before it starts moving
  // the drop: free fall (steer a bit), then the umbrella opens by itself this high above the floor (or press space)
  fall: { vMax: 34, steer: 18, open: 42 },
  glide: { vy: 7, speed: 15, minOpen: 6 }, // umbrella: sink speed, steering speed, the lowest you can open it
  pickR: 2.6, // pick-up reach from your feet (m); the server allows a little more for lag
  autoR: 1.4, // walk over ammo, heals and armour to grab them
  armor: { max: 100, absorb: 0.6 }, // armour takes this share of every hit until it's gone (not the zone)
  cola: { heal: 25, max: 100, n: 8 }, medkit: { heal: 75, max: 100, n: 3 }, // heals: how much, up to what, most you can carry
  healMs: { cola: 1600, medkit: 3500 }, // time to drink / patch up (interrupted by getting hit? no: jank, keep it simple)
  slots: 2, // gun slots (plus the melee one)
  melee: 'bread', // everyone lands with a loaf
  dropNo: 900, // ms before you can pick up what you just dropped
  spotGap: 5.5, // loot spots at least this far apart
  late: 25000, // ms after the start that a late joiner still gets a seat on the blimp
  // the grapple runs on charges here (no endless swinging across the city): a grab spends one, each one comes back
  // `cd` s after the last one came back (or after you used one at full). the server counts them too
  hook: { charges: 2, cd: 8 },
};
// grapple charges at time t (ms): h = { n (charges at t0), t0 }. returns { n (whole charges), k (0..1 to the next) }
export function hookCharges(h, t) {
  const H = BR.hook;
  if (!h) return { n: H.charges, k: 1, f: H.charges };
  const f = Math.min(H.charges, h.n + Math.max(0, t - h.t0) / (H.cd * 1000));
  return { n: Math.floor(f + 1e-6), k: f >= H.charges ? 1 : f - Math.floor(f), f };
}
// spend one (null = none ready). returns the new state
export function hookSpend(h, t) {
  const c = hookCharges(h, t);
  if (c.n < 1) return null;
  return { n: c.f - 1, t0: t };
}

// the zone: [wait (s), shrink time (s), new radius as a share of the first one, damage per second outside]
// a desert match runs about six minutes; the last circle closes to nothing
export const ZONE = [
  [55, 35, 0.62, 2], [35, 28, 0.4, 4], [28, 24, 0.24, 7], [22, 20, 0.12, 11], [18, 18, 0.04, 16], [14, 14, 0, 25],
];
export const ZONE_COLOR = 0x8a3cff; // electric violet: nothing else in the game is this colour

// rarity tiers: colour, damage multiplier, armour plates / vest size
export const TIERS = [
  { name: 'Common', color: '#e8e8e8', mul: 1 },
  { name: 'Uncommon', color: '#7dff4f', mul: 1.08 },
  { name: 'Rare', color: '#4fd8ff', mul: 1.16 },
  { name: 'Epic', color: '#ff4fd8', mul: 1.26 },
  { name: 'Legendary', color: '#ffe14d', mul: 1.4 },
];
// the guns on the floor: lowest tier it can come in, how often (weight), and its ammo:
// mags = how many magazines come with it (guns with a mag), shots = uses (everything else that fires something)
export const GUNS = {
  smg: { tier: 0, w: 10, mags: 3 }, revolver: { tier: 0, w: 9, mags: 3 }, shotgun: { tier: 0, w: 9, mags: 4 },
  snowball: { tier: 0, w: 4, shots: 30 }, banana: { tier: 0, w: 5, shots: 30 }, cards: { tier: 0, w: 4, shots: 30 },
  ar: { tier: 1, w: 9, mags: 3 }, marbles: { tier: 1, w: 5, mags: 6 }, bow: { tier: 1, w: 5, shots: 20 }, redline: { tier: 1, w: 6, mags: 3 },
  bowling: { tier: 1, w: 3, shots: 8 }, cig: { tier: 1, w: 2 }, blower: { tier: 1, w: 2 },
  sniper: { tier: 2, w: 5, mags: 3 }, chicken: { tier: 2, w: 3, shots: 8 }, bloodcross: { tier: 2, w: 3 }, shredder: { tier: 2, w: 2 },
  minigun: { tier: 3, w: 2, mags: 1 },
  laser: { tier: 3, w: 2 }, // the Big Laser Pointer (charge it, it beams)
  pistol: { tier: 0, w: 9, mags: 3 }, sawnoff: { tier: 0, w: 6, mags: 6 }, akimbo: { tier: 1, w: 5, mags: 3 }, // the plain sidearms
};
export const MELEE = { knife: { tier: 0, w: 4 }, slapper: { tier: 0, w: 3 }, katana: { tier: 1, w: 3 }, slipper: { tier: 1, w: 2 }, scales: { tier: 2, w: 2 } };
// throwables and gadgets (the G key): how many come in one pick-up
export const GADGETS = { frag: { tier: 0, n: 2, w: 6 }, smoke: { tier: 0, n: 2, w: 4 }, popper: { tier: 1, n: 2, w: 3 }, duck: { tier: 2, n: 1, w: 2 }, bubble: { tier: 2, n: 1, w: 2 }, wand: { tier: 2, n: 2, w: 2 }, reverse: { tier: 3, n: 1, w: 1 },
  camera: { tier: 2, n: 1, w: 2 }, quiz: { tier: 1, n: 2, w: 3 } }; // the new gear: instant camera, pop quiz. (no night vision goggles in a royale: owner, 2026-11-06)
// everything else on the floor (no tier roll): ammo, heals, armour
export const STUFF = {
  ammo: { name: 'Ammo Bucket', desc: 'a bucket of loose bullets. tops up every gun you carry', color: '#ffb84f' },
  cola: { name: 'Jank Cola', desc: `+${BR.cola.heal} HP. tastes like a battery`, color: '#ff3030' },
  medkit: { name: 'Medkit', desc: `+${BR.medkit.heal} HP. a box of plasters and hope`, color: '#ffffff' },
  plate: { name: 'Cardboard Plate', desc: '+25 armour. it is cardboard', color: '#c9a36a' },
  vest: { name: 'Bin Lid Vest', desc: '+50 armour. two bin lids and some tape', color: '#4fd8ff' },
  fridge: { name: 'Riot Fridge', desc: 'full armour. you are wearing a fridge door', color: '#ff4fd8' },
};
export const ARMOR_OF = { plate: 25, vest: 50, fridge: 100 };

// how many rounds a gun comes with (total, mag included). null = unlimited (cones, melee, the blood cross costs HP)
export function ammoFor(id, mul = 1) {
  const g = GUNS[id], w = WEAPONS[id];
  if (!g || !w) return null;
  if (g.mags && w.mag) return Math.round(w.mag * g.mags * mul);
  if (g.shots) return Math.round(g.shots * mul);
  return null;
}
// an ammo bucket: about one and a half magazines (or a third of the shots) of each gun you carry
export function bucketFor(id) {
  const g = GUNS[id], w = WEAPONS[id];
  if (!g || !w) return 0;
  if (g.mags && w.mag) return Math.max(6, Math.round(w.mag * 1.5));
  if (g.shots) return Math.max(4, Math.round(g.shots / 3));
  return 0;
}
// what a loot entry is called on the floor ("Rare AR")
export function lootName(l) {
  if (l.k === 'gun' || l.k === 'melee') return `${TIERS[l.tier].name} ${WEAPONS[l.id] ? WEAPONS[l.id].name : l.id}`;
  if (l.k === 'gadget') return `${ITEMS[l.id] ? ITEMS[l.id].name : l.id} x${l.n}`;
  return STUFF[l.id] ? STUFF[l.id].name : l.id;
}
export function lootColor(l) { return l.k === 'gun' || l.k === 'melee' || l.k === 'gadget' ? TIERS[l.tier || 0].color : (STUFF[l.id] || {}).color || '#fff'; }

// the blimp: a straight line over the middle of the map. path = { a: [x, z], d: [dx, dz] (unit), y, t0 (ms) }
// the point at time t (ms), and how far along it is (m, from the start)
export function blimpAt(path, t) {
  const s = Math.max(0, (t - path.t0) / 1000 - BR.blimp.wait) * BR.blimp.speed;
  return [path.a[0] + path.d[0] * s, path.y, path.a[1] + path.d[1] * s, s];
}
export const blimpDone = (path, t) => blimpAt(path, t)[3] >= BR.blimp.len * 2;

// the zone at time t: { c: [x, z], r, next: { c, r } | null, dps, phase, left (ms to the next change), shrinking }
// z = the server's zone plan: { t0, r0, steps: [{ c, r, wait, shrink, dps }] }, c0 = the first centre
export function zoneAt(z, t) {
  if (!z) return null;
  let c = z.c0, r = z.r0, at = z.t0;
  for (let i = 0; i < z.steps.length; i++) {
    const s = z.steps[i], w1 = at + s.wait * 1000, s1 = w1 + s.shrink * 1000;
    if (t < w1) return { c, r, next: s, dps: i ? z.steps[i - 1].dps : 1, phase: i, left: w1 - t, shrinking: false };
    if (t < s1) {
      const k = (t - w1) / (s1 - w1);
      return { c: [c[0] + (s.c[0] - c[0]) * k, c[1] + (s.c[1] - c[1]) * k], r: r + (s.r - r) * k, next: s, dps: s.dps, phase: i, left: s1 - t, shrinking: true };
    }
    c = s.c; r = s.r; at = s1;
  }
  const last = z.steps[z.steps.length - 1];
  return { c, r, next: null, dps: last ? last.dps * 1.6 : 30, phase: z.steps.length, left: 0, shrinking: false };
}
export function outsideZone(zn, p) { return !!zn && Math.hypot(p[0] - zn.c[0], p[2] - zn.c[1]) > zn.r; }
