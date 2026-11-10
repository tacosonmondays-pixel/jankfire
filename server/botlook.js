// Bot outfits: every bot gets its own look (skin, hair, clothes, hats, face, back) and weapon skins, rolled from the
// whole catalog (shared/looks.js + shared/cosmetics.js, so new packs show up on bots the day they land). Seeded from the
// bot's name and the room, so a bot keeps its look for the whole match. Achievement items are fair game for bots:
// validLook gets every achievement, players still need to earn theirs (their looks go through validLook with their own).
import { validLook, ACCESSORIES, HAIRS, TOPS, BOTTOMS, SKIN_TONES, HAIR_COLORS, CLOTH_COLORS, LOOK_COLORS, ACHIEVEMENTS, LEGACY_ACHS } from '../shared/looks.js';
import { COSMETICS, WRAP_MODES } from '../shared/cosmetics.js';

const ALL_ACHS = new Set([...Object.keys(ACHIEVEMENTS), ...Object.keys(LEGACY_ACHS)]);

// a tiny seeded rng (mulberry32) and a string hash, so the same name in the same room rolls the same bot
export function hashStr(s) { let h = 2166136261; for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619); return h >>> 0; }
export function rng(seed) {
  let a = seed >>> 0;
  return () => { a = (a + 0x6d2b79f5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
const pk = (r, a) => a[Math.floor(r() * a.length)];
const keys = (o) => Object.keys(o);

// themed presets so a lobby isn't pure noise. each field is a value or a list to pick from; anything left out is rolled
export const PRESETS = {
  corpo: { top: 'suit', topColor: ['#1a1a1a', '#3a3a44', '#2a4a8a'], bottom: 'pants', bottomColor: ['#1a1a1a', '#3a3a44'], hair: ['short', 'none', 'bun'], face: ['shades', 'bigglasses', 'none'], head: 'none', back: ['none', 'backpack'] },
  ratking: { top: ['none', 'tank'], topColor: ['#8a5a2b', '#3a3a44'], bottom: 'shorts', bottomColor: ['#8a5a2b', '#3a6a2a'], skin: ['#555560', '#a8e6a1', '#c8a2ff'], hair: ['mohawk', 'spiky', 'long'], hairColor: ['#3a3a44', '#7dff4f', '#4a2a10'], head: 'crown', face: ['eyepatch', 'clown', 'mustache'], back: ['cape', 'voidcape'] },
  mallcop: { top: 'jacket', topColor: ['#2a4a8a', '#1a1a1a'], bottom: 'pants', bottomColor: ['#2a4a8a', '#1a1a1a'], hair: ['short', 'bowl', 'none'], head: ['cap', 'hardhat'], face: ['mustache', 'shades'], back: 'none' },
  delivery: { top: ['tee', 'runner', 'hoodie'], topColor: ['#ff7a1a', '#ffe14d', '#ff4f4f', '#7dff4f'], bottom: ['shorts', 'pants'], bottomColor: ['#3a3a44', '#1a1a1a', '#2a4a8a'], head: ['cap', 'helmet', 'headphones'], face: ['none', 'shades'], back: 'backpack' },
  maid: { top: 'maid', topColor: ['#1a1a1a', '#ff9ad5', '#b07dff'], bottom: 'skirt', bottomColor: ['#1a1a1a', '#ffffff'], hair: ['ponytail', 'long', 'bun'], head: ['catears', 'none'], face: ['eyepatch', 'visor', 'none'], back: ['none', 'cattail', 'jetpack'] },
  nightshift: { top: ['hoodie', 'tee'], topColor: ['#3a3a44', '#3a6a2a'], bottom: 'overalls', bottomColor: ['#2a4a8a', '#c8b48a'], head: 'hardhat', face: ['visor', 'goggles'], back: 'none' },
  influencer: { top: ['jacket', 'runner'], topColor: ['#ff4fd8', '#4fd8ff', '#ffffff'], bottom: ['skirt', 'shorts'], bottomColor: ['#ff9ad5', '#ffffff', '#4fd8ff'], hair: ['long', 'bun', 'afro'], hairColor: ['#ff4fd8', '#4fd8ff', '#f2e6c8'], head: ['party', 'bucket'], face: 'shades', back: 'wings' },
  voidintern: { top: 'runner', topColor: ['#1a1a1a', '#7a4aff'], bottom: 'pants', bottomColor: '#1a1a1a', hair: ['spiky', 'none'], hairColor: ['#7a4aff', '#ffffff'], head: 'headphones', face: ['visor', 'goggles'], back: 'voidcape' },
  cowpoke: { top: ['jacket', 'tank'], topColor: ['#8a5a2b', '#c8b48a'], bottom: 'pants', bottomColor: ['#2a4a8a', '#8a5a2b'], head: 'cowboy', face: ['mustache', 'bandana'], back: ['none', 'cape'] },
};
export const PRESET_IDS = keys(PRESETS);

// a random look that still looks dressed: top and bottom never the same colour, accessories now and then
// achievement items show up on bots, but rarer than the free stuff (or every lobby is all maid dresses)
const pkRare = (r, T, ks) => { let k = pk(r, ks); if (T[k] && T[k].ach && r() < 0.65) k = pk(r, ks); return k; };
function rollLook(r) {
  const top = pkRare(r, TOPS, keys(TOPS)), topColor = pk(r, CLOTH_COLORS);
  let bottomColor = pk(r, CLOTH_COLORS);
  if (bottomColor === topColor) bottomColor = pk(r, CLOTH_COLORS.filter((c) => c !== topColor));
  const acc = (slot, p) => (r() < p ? pkRare(r, ACCESSORIES[slot], keys(ACCESSORIES[slot]).filter((k) => k !== 'none')) : 'none');
  return {
    color: pk(r, LOOK_COLORS), skin: pk(r, SKIN_TONES), hair: pk(r, keys(HAIRS)), hairColor: pk(r, HAIR_COLORS),
    top, topColor, bottom: pkRare(r, BOTTOMS, keys(BOTTOMS)), bottomColor, head: acc('head', 0.6), face: acc('face', 0.45), back: acc('back', 0.35),
  };
}

export function botLook(seed, presetChance = 0.3) {
  const r = rng(seed), look = rollLook(r);
  let preset = '';
  if (r() < presetChance) {
    preset = pk(r, PRESET_IDS);
    for (const [k, v] of Object.entries(PRESETS[preset])) look[k] = Array.isArray(v) ? pk(r, v) : v;
  }
  // the joke body, now and then (its own dice, so nobody's outfit changed when this was added): a build for half of them, a big head or a big butt for a few
  const j = rng(seed ^ 0x2c1b3c6d);
  look.build = pk(j, ['', '', 'm', 'f']);
  if (j() < 0.12) look.bigHead = 1 + Math.floor(j() * 4);
  if (j() < 0.1) look.bigButt = 1 + Math.floor(j() * 4);
  for (const k of ['bigChest', 'bigArms', 'bigLegs', 'fat']) if (j() < 0.08) look[k] = 1 + Math.floor(j() * 4); // (after the two above, so the bots that already had a big head keep it)
  return { look: validLook(look, ALL_ACHS), preset }; // never invalid, whatever the tables above say
}

// weapon skins from the whole catalog: wraps (both wrap packs), hats, effects, and the skins made for that weapon
const FINISHES = keys(COSMETICS.finish), HATS = keys(COSMETICS.hat), EFFECTS = keys(COSMETICS.effect);
export function botSkins(seed, weapons) {
  const r = rng(seed ^ 0x5bd1e995), out = {};
  for (const id of weapons) {
    if (r() >= 0.6) continue;
    const models = keys(COSMETICS.model).filter((m) => COSMETICS.model[m].weapon === id);
    out[id] = [
      r() < 0.85 ? pk(r, FINISHES) : 'default',
      r() < 0.3 ? pk(r, HATS) : 'none',
      r() < 0.3 ? pk(r, EFFECTS) : 'none',
      models.length && r() < 0.55 ? pk(r, models) : 'default',
      pk(r, WRAP_MODES),
    ];
  }
  return out;
}
