// Each outdoor map's own look (the owner: "go crazy", after Battle Island's look pass): a painted sky and clouds in the
// map's time of day, its fog and colour grade, and its life (grass tufts, flowers, swaying plants, gulls, boats).
// bilook.js draws the sky and applies the rest; bilife.js grows the life. A map with no entry keeps the old box sky.
//  sky: zen / mid / hor / sea = zenith, mid sky, horizon haze, under the horizon; sunCol / glow = the sun (or moon) and
//       the air round it; glowK > 1 = a sunset's wide burn on the horizon; disc 0 hides the disc; moon: a cratered moon
//       instead of the sun; stars 0..1; cloudLit / cloudShade / cloudWarm = the clouds' sunny side, shade and the warm
//       light near the sun; cover = how much of the sky overhead is cloud; towers = how tall the horizon cumulus stand
//  fog: { color, near, far } (any left out keep the map's own); grade: [saturation, warmth, contrast, amount] (shaders on)
//  life: see bilife.js biLifeMap
import { MAPS } from '/shared/map.js';

const SWAY = 'palm|fern|bush|lollipop|conifer|pine|birch|deadtree'; // (the trees and plants that move in the wind)
export const LOOKS = {
  battleisland: {
    sky: { zen: 0x2477e6, mid: 0x6cbcff, hor: 0xd2f1ff, sea: 0x9fd8f0, sunCol: 0xfff3d6, glow: 0xfff0c0, cloudLit: 0xffffff, cloudShade: 0xb3c3ec, cloudWarm: 0xfff1dc, cover: 0.4, towers: 1.0, drift: 0.004 },
    fog: { color: 0xc8ecfa, near: 140, far: 1150 },
    grade: [1.12, 0.035, 1.05, 1],
    life: { grass: ['grass', 'leaves'], flowers: 0.05, gulls: 3, boats: 7, sway: 'palm|fern|bush', span: 260 },
  },
  // the cul-de-sac: a pastel late afternoon, pink haze on the horizon, lavender-shaded cumulus, lawns full of tufts
  suburb: {
    sky: { zen: 0x2c78ee, mid: 0x7fb8ff, hor: 0xffd6ec, sea: 0xd9b4d6, sunCol: 0xfff0d8, glow: 0xffe2cc, cloudLit: 0xfffaf4, cloudShade: 0xc6b6ea, cloudWarm: 0xffe0ea, cover: 0.38, towers: 0.75, glowK: 1.25, drift: 0.004 },
    grade: [1.1, 0.03, 1.05, 1],
    life: { boxGrass: ['grass'], flowers: 0.06, gulls: 1, boats: 0, sway: SWAY },
  },
  // the depot on the night shift: a purple dusk going to night, stars, a moon, the yard's lawn round the fences
  warehouse: {
    sky: { zen: 0x0b0d2c, mid: 0x2e2660, hor: 0x6a3c7e, sea: 0x2a1a3a, sunCol: 0xe6ecff, glow: 0x8a7cc0, cloudLit: 0x8c88c4, cloudShade: 0x2a2450, cloudWarm: 0xa07cb4, cover: 0.3, towers: 0.55, stars: 0.9, moon: 1, glowK: 0.9, drift: 0.003 },
    grade: [1.06, -0.02, 1.06, 1],
    life: { boxGrass: ['grass'], flowers: 0.02, gulls: 0, boats: 0, sway: SWAY, tint: 0x9aa0c8 },
  },
};
// a map's look: its own, or its base map's (the S&D versions, <id>_sd)
export function lookFor(id) {
  if (LOOKS[id]) return LOOKS[id];
  const d = id && id !== 'battleisland' ? MAPS[id] : null;
  return d && d.base && LOOKS[d.base] ? LOOKS[d.base] : null;
}
