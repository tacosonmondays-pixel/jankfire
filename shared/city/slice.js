// The vertical slice city: The Bottom (bottom of the hill, south-west), The Gut (up the hill, north-west), the Gut
// border between them (flesh creeping over pastel houses, the first Mr. Overtime arena) and a strip of The Commute
// (a dead-traffic highway climbing the east side from the Bottom up into the Gut). 640 x 512 m = 80 chunks.
// SLICE is the master plan; the district generators (bottom.js, gut.js, commute.js) read it.
// x east, z south: north (-z) is up the hill. Heights: the Bottom terraces climb 4 m every 26 m (y 0 - 32), the border is at 36, the Gut plateau at 40.
import { registerCity } from './plan.js';

export const SLICE = {
  x0: -320, z0: -256, x1: 320, z1: 256,
  // the Bottom: terraces k = 0..8 from the south edge up, each TERR deep and RISE high
  bottom: { rect: [-320, 0, 96, 256], terr: 26, rise: 4, n: 9 },
  border: { rect: [-320, -48, 96, 0], y: 36 },
  gut: { rect: [-320, -256, 96, -48], y: 40 },
  commute: { rect: [96, -256, 320, 256] },
  // the highway: deck x range, climbing from (z = 256, y = 0) to (z = -150, y = 30), then turning west into the Gut
  highway: { x0: 168, x1: 196, zLow: 244, zTop: -150, yTop: 40, westZ: [-186, -158] },
  longStairs: { x0: -48, x1: -40 }, // the Long Stairs: straight up the Bottom, 9 flights, to the border gate
  lostFound: { rect: [-214, 178, -164, 204] }, // the Lost & Found depot (the Machine inside)
  plaza: { rect: [-150, 232, -60, 254] }, // the market at the bottom
  gym: { rect: [8, 128, 40, 150] }, // Lumps' Gym
  escalator: { x: -112, z0: 64, z1: 90 }, // the Down Escalator
  gate: { x: -44, z: -24 }, // the Gut border gate (top of the Long Stairs)
  arena: { rect: [-86, -104, -2, -56] }, // Clocking In: the first Mr. Overtime fight (WP9)
  stomach: { x: -170, z: -180, r: 48, floor: 22, acid: 24.5 }, // the Big Stomach crater + acid lake
  peri: { z0: -136, z1: -124, x0: -300, x1: 80 }, // Peristalsis Avenue (the moving street), runs east-west
  ribAve: { x0: -50, x1: -38, z0: -256, z1: -48 }, // the rib-arched avenue north from the gate
  choir: { x: -268, z: -214 }, // the Choir Lung
  teeth: { rect: [10, -220, 70, -170] }, // Tooth Market
  heart: { x: -96, z: -78 }, // the Big Heart: the open ground behind Meat Mechanics, west of the old time-office plaza (bigheart.js)
  camp: { x: 236, z: 40 }, // the Unpaid raider camp under the highway
  digit: { x: 280, z: -60 }, // the fallen 13: a giant glowing orbital digit (a hot zone)
};

// ground height of the open ground (not counting buildings) at (x, z)
export function groundY(x, z) {
  const S = SLICE;
  if (z >= 0 && x < 96) { const b = S.bottom; return Math.min(b.n - 1, Math.max(0, Math.floor((256 - z) / b.terr))) * b.rise; }
  if (x < 96) return z >= -48 ? S.border.y : S.gut.y;
  // the Commute: the wasteland's hills (ground.js, once it's loaded: it hangs itself on GROUND), else the old 0.5 m steps
  return GROUND.commute ? GROUND.commute(x, z) : hwY(z, true);
}
export const GROUND = { commute: null };
// the highway deck height at z (smooth, before stepping)
export function hwY(z, ground) {
  const H = SLICE.highway, t = Math.max(0, Math.min(1, (H.zLow - z) / (H.zLow - H.zTop)));
  const y = t * H.yTop;
  return ground ? Math.floor(y / 0.5) * 0.5 : y; // 0.5 m steps: you just walk up them
}
export const terraceOf = (z) => Math.min(SLICE.bottom.n - 1, Math.max(0, Math.floor((256 - z) / SLICE.bottom.terr)));

// places the quests and scenes refer to: ids are the writer's LOCATIONS (shared/story/content/world.js), checked by
// tools/city/places.mjs. (where a place has no spot yet it isn't here)
export const PLACES = {
  'bottom:lostfound': { p: [-189, 8, 200], name: 'the Lost & Found' },
  'bottom:machine': { p: [-189, 8, 185], name: 'the Machine' },
  'bottom:soup_kitchen': { p: [-105, 0, 238], name: 'the Bottom market' },
  'bottom:long_stairs': { p: [-44, 0, 236], name: 'the Long Stairs' },
  'bottom:gym': { p: [24, 16, 137], name: "Lumps' Gym" },
  'bottom:down_escalator': { p: [-112, 32, 48], name: 'the Down Escalator' },
  'gut:stairs_top': { p: [-44, 36, -18], name: 'the Gut border' },
  'gut:border': { p: [-44, 36, -14], name: 'the Gut Border Gate (Overtime fight 1)' }, // (arenas.js; was the old time office at -44, 40, -80)
  'gut:big_stomach': { p: [-170, 40, -128], name: 'the Big Stomach' },
  'gut:peristalsis': { p: [-120, 40, -130], name: 'Peristalsis Avenue' },
  'gut:choir_lung': { p: [-268, 40, -196], name: 'the Choir Lung' },
  'gut:tooth_market': { p: [40, 40, -174], name: 'Tooth Market' },
  'commute:ring_road': { p: [182, 0, 236], name: 'the Commute' },
  'commute:unpaid_camp': { p: [236, 0, 40], name: 'the Unpaid camp' },
  'commute:digit_13': { p: [280, 0, -60], name: 'the fallen 13' },
  'commute:smiles_hideout': { p: [182, 0, 93], name: 'the overpass hideout (under the collapsed span)' },
  'bottom:sunset_spot': { p: [-200, 32, 6], name: 'the Sunset Wall (top terrace)' },
  'bottom:dale_shed': { p: [-170, 8, 180], name: "Dale's Shed (behind the Machine)" },
  'bottom:rooftops': { p: [-260, 20, 120], name: 'the Wok Roofs' },
  'gut:campus': { p: [-200, 40, -80], name: 'Gristle & Sons Campus' },
  'gut:big_heart': { p: [-94.47, 40, -69.13], name: 'the Big Heart' }, // (its listening spot, 9 m out in front: bigheart.js)
  // act I (the world wiring pass): every place a mission step points at. r = the zone's reach (m, flat; a zone also
  // wants you within 4 m of its height), sized for how you arrive (on foot, by grapple, in a car)
  'sims:suburb': { p: [-189, 8.15, 185.2], name: 'the Machine (ENTER THE SIMS)', r: 3.4 }, // the sims are in the Machine: its terminal (storyworld.js)
  'gut:digester_wall': { p: [-87, 40, -137.4], name: 'the Digester Wall', r: 6 }, // the office block's face on the north side of Peristalsis Avenue (gut.js digesterWall)
  'gut:clinic_bev': { p: [-84.3, 36, -3.2], name: "Bev's Clinic", r: 3.5 }, // the doorstep of a flesh-eaten bungalow on the border, 40 m west of the gate (gut.js bevClinic)
  'bottom:service_tunnel': { p: [-205.8, 4, 206.2], name: 'the Service Tunnel', r: 3 }, // a staff door in the wall under the Lost & Found, its west yard (bottom.js serviceTunnel)
  'commute:underhill_loop': { p: [311, 0, -96], name: 'the Under-Hill Loop', r: 6 }, // the Loop's portal in the east cliff (commute.js loopPortal); y: groundY
  'commute:tunnel_mouth': { p: [292, 0, -96], name: 'the Tunnel Mouth', r: 8 }, // the viaduct stub out of it, where the train comes out
};
// act I zone sizes for places that were already here (a car arrives fast; the Lost & Found is a big hall)
Object.assign(PLACES['commute:ring_road'], { p: [182, 0.8, 236], r: 14 }); // (on the deck)
Object.assign(PLACES['gut:peristalsis'], { r: 12 });
Object.assign(PLACES['gut:border'], { r: 8 });
Object.assign(PLACES['bottom:lostfound'], { r: 7 });
Object.assign(PLACES['gut:choir_lung'], { r: 9 });
Object.assign(PLACES['bottom:rooftops'], { p: [-163.5, 15, 208.8], r: 8.5 }); // the real roofs: the stack east of the Lost & Found's yard, 10 m over the lane (bottom.js wokRoofs)
Object.assign(PLACES['bottom:soup_kitchen'], { p: [-106.5, 0, 235.2], r: 5 }); // in front of Sharon's stall (it was inside the stall)
for (const k of ['commute:underhill_loop', 'commute:tunnel_mouth']) PLACES[k].p[1] = groundY(PLACES[k].p[0], PLACES[k].p[2]);

const fogLight = (hemi, hemiG, hk, sun, sk) => ({ hemi: [hemi, hemiG, hk], sun: [sun, sk] });
registerCity('slice', {
  name: 'OVERDUE slice', cx0: -5, cz0: -4, cx1: 5, cz1: 4,
  spawn: [-189, 8.4, 196],
  horizon: 'horizon',
  // the slice is dense: full detail a bit closer in, lod1 (one box per house) past it. near per preset (Potato, Crusty,
  // High, Too HD): 72 / 88 / 96 / 139 m. lodBand: the last metres of the ring dissolve lod 0 into lod 1 (city/stream.js),
  // so there's no pop line where the detail ends. Too HD is left exactly as it was (its old ring, a plain swap)
  ringScale: { near: [0.5625, 0.55, 0.43, 0.62], props: 0.75 }, lodBand: [24, 24, 24, 0],
  districts: [
    // order matters: the first rect that holds a point is its district (districtAt)
    { id: 'border', name: 'The Gut Border', rect: SLICE.border.rect, gen: 'border', margin: 40,
      sky: { top: 0x2a1030, mid: 0x9a3a5a, bot: 0x3a1a28, fog: 0x8a4058 }, fogNear: 50, fogFar: 380, night: 0.6, pulse: 0.35, light: fogLight(0xffb0c0, 0x6a2a3a, 1.3, 0xffc0a0, 1.4) },
    { id: 'bottom', name: 'The Bottom', rect: SLICE.bottom.rect, gen: 'bottom', margin: 40,
      sky: { top: 0x140828, mid: 0x5a2a70, bot: 0x2a1840, fog: 0x3e2452 }, fogNear: 80, fogFar: 520, night: 1, light: fogLight(0xc8b8ff, 0x7a4a6a, 1.55, 0xd8c8ff, 0.9) },
    { id: 'gut', name: 'The Gut', rect: SLICE.gut.rect, gen: 'gut', margin: 40,
      sky: { top: 0x1a0408, mid: 0x6a1a28, bot: 0x2a0a12, fog: 0x5a1020 }, fogNear: 26, fogFar: 205, night: 0.6, pulse: 1, // a close red fog that beats (pulse 0..1: how hard the fog breathes)
      light: fogLight(0xd09090, 0x2a0810, 0.8, 0xffc0a8, 1.0) } /* dimmer and redder than it was: the owner wants the gut haunting */,
    { id: 'commute', name: 'The Commute', rect: SLICE.commute.rect, gen: 'commute', margin: 40,
      sky: { top: 0x3a4a8a, mid: 0xe0904a, bot: 0x7a5038, fog: 0xd8a070 }, fogNear: 60, fogFar: 600, night: 0.2, light: fogLight(0xffe0b0, 0x7a5a40, 1.4, 0xffd090, 1.9) },
  ],
  post: 'slicepost', // (gens.js: the edges + the road net)
});
