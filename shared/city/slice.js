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
  camp: { x: 236, z: 40 }, // the Unpaid raider camp under the highway
  digit: { x: 280, z: -60 }, // the fallen 13: a giant glowing orbital digit (a hot zone)
};

// ground height of the open ground (not counting buildings) at (x, z)
export function groundY(x, z) {
  const S = SLICE;
  if (z >= 0 && x < 96) { const b = S.bottom; return Math.min(b.n - 1, Math.max(0, Math.floor((256 - z) / b.terr))) * b.rise; }
  if (x < 96) return z >= -48 ? S.border.y : S.gut.y;
  // the Commute: the wasteland follows the highway climb in 0.5 m steps (walkable)
  return hwY(z, true);
}
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
};

const fogLight = (hemi, hemiG, hk, sun, sk) => ({ hemi: [hemi, hemiG, hk], sun: [sun, sk] });
registerCity('slice', {
  name: 'OVERDUE slice', cx0: -5, cz0: -4, cx1: 5, cz1: 4,
  spawn: [-189, 8.4, 196],
  horizon: 'horizon',
  ringScale: { near: 0.62, props: 0.75 }, // the slice is dense: full detail a bit closer in, lod1 (one box per house) past it
  districts: [
    // order matters: the first rect that holds a point is its district (districtAt)
    { id: 'border', name: 'The Gut Border', rect: SLICE.border.rect, gen: 'border', margin: 40,
      sky: { top: 0x2a1030, mid: 0x9a3a5a, bot: 0x3a1a28, fog: 0x8a4058 }, fogNear: 50, fogFar: 380, night: 0.6, light: fogLight(0xffb0c0, 0x6a2a3a, 1.3, 0xffc0a0, 1.4) },
    { id: 'bottom', name: 'The Bottom', rect: SLICE.bottom.rect, gen: 'bottom', margin: 40,
      sky: { top: 0x140828, mid: 0x5a2a70, bot: 0x2a1840, fog: 0x3e2452 }, fogNear: 80, fogFar: 520, night: 1, light: fogLight(0xc8b8ff, 0x7a4a6a, 1.55, 0xd8c8ff, 0.9) },
    { id: 'gut', name: 'The Gut', rect: SLICE.gut.rect, gen: 'gut', margin: 40,
      sky: { top: 0x1a0408, mid: 0x6a1a28, bot: 0x2a0a12, fog: 0x4a1424 }, fogNear: 70, fogFar: 340, night: 0.6, light: fogLight(0xffe0d0, 0x3a1020, 1.25, 0xfff0e0, 1.6) },
    { id: 'commute', name: 'The Commute', rect: SLICE.commute.rect, gen: 'commute', margin: 40,
      sky: { top: 0x3a4a8a, mid: 0xe0904a, bot: 0x7a5038, fog: 0xd8a070 }, fogNear: 60, fogFar: 600, night: 0.2, light: fogLight(0xffe0b0, 0x7a5a40, 1.4, 0xffd090, 1.9) },
  ],
  post: 'edges',
});
