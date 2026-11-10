// Character customizer: body colour + head / face / back accessories.
// Some accessories are free, the rest are unlocked by achievements (checked on the server).
export const LOOK_COLORS = ['#ff4fd8', '#4fd8ff', '#ffe14d', '#7dff4f', '#ff7a1a', '#b07dff', '#ff4f4f', '#4fffb0', '#ffffff', '#ff9ad5', '#3a3a44', '#8a5a2b'];

// Sniper Royalty: three kinds of sniper kill, in any order, over any number of matches. the sniper_feats stat keeps
// bit flags (one kill can tick several, the server decides every tick); each feat says which bits tick it (mask).
// the quick-scope and the no-scope used to be two boxes (bits 2 and 4): now either one ticks the trick-shot box,
// so anyone who already had either keeps it
export const ROYAL_FEATS = [
  { id: 'long', name: 'LONG SHOT', desc: 'a sniper kill from 50 m or more', bit: 1, mask: 1 },
  { id: 'trick', name: 'QUICK-SCOPE / NO-SCOPE', desc: 'a sniper kill fired within 0.35 s of the scope coming up, or without the scope at all', bit: 2, mask: 2 | 4 },
  { id: 'head', name: 'HEADSHOT', desc: 'a sniper headshot kill', bit: 8, mask: 8 },
];
export const featOn = (bits, f) => !!(bits & f.mask);
export const ROYAL_ALL = ROYAL_FEATS.reduce((m, f) => m | f.bit, 0); // every box ticked
// long: metres between server positions. quick: ms after the scope is fully up. a victim who hasn't moved `moved`
// metres for `still` ms never counts, so nobody farms it on an AFK player or a friend standing still
export const ROYAL = { long: 50, quick: 350, still: 5000, moved: 0.6 };

export const ACHIEVEMENTS = {
  firstblood: { name: 'First Blood', desc: 'get your first kill', stat: 'kills', goal: 1 },
  champion: { name: 'Champion', desc: 'win 10 rounds', stat: 'wins', goal: 10 },
  speed: { name: 'Speed Demon', desc: 'hit 500 km/h', stat: 'top_speed', goal: 500 },
  flyer: { name: 'Frequent Flyer', desc: 'hit 1000 km/h', stat: 'top_speed', goal: 1000 },
  waves: { name: 'Survivor', desc: 'reach wave 10 in coop', stat: 'best_wave', goal: 10 },
  void: { name: 'Void Lord', desc: 'knock 25 people into the void', stat: 'void_kills', goal: 25 },
  sharp: { name: 'Sharpshooter', desc: 'land 50 headshots', stat: 'headshots', goal: 50 },
  knees: { name: 'Knee Trouble', desc: 't-bag so hard you explode', stat: 'tbags', goal: 1 },
  nolife: { name: 'No Life', desc: 'play for 5 hours', stat: 'playtime', goal: 18000 },
  airborne: { name: 'Never Landed', desc: 'finish a whole match without touching the ground after any spawn', stat: 'airborne', goal: 1 },
  royalty: { name: 'Sniper Royalty', desc: 'sniper kills: a 50 m+ long shot, a quick-scope or no-scope, and a headshot', stat: 'sniper_feats', goal: 3, feats: ROYAL_FEATS },
  smarty: { name: 'Smarty Pants', desc: 'get 3 pop quiz questions right (someone else has to throw them)', stat: 'quiz_right', goal: 3 },
  // the hidden cats (shared/secrets.js). the cats stat isn't a column: the server counts the pets in inv.lore
  board: { name: 'Board Approved', desc: 'pet all 5 cats on the board of directors. they hide. press F', stat: 'cats', goal: 5 },
};
// hidden unlocks that aren't in the list: the Wings used to come from Frequent Flyer, and whoever had them by then keeps them
export const LEGACY_ACHS = { oldwings: { stat: 'wings_old', goal: 1 } };
// careful: these ids show up in /api/me achs too, so anything mapping achs through ACHIEVEMENTS[id] must skip unknown ids
// an accessory is yours if you have its achievement (or its legacy one)
export function hasAcc(a, achs) { return !!a && (!a.ach || !!(achs && (achs.has(a.ach) || (a.legacy && achs.has(a.legacy))))); }
// progress toward an achievement. a multi-part one keeps its parts as bit flags in one stat: progress = how many are done
export function achProgress(a, stats) {
  const v = (stats && stats[a.stat]) || 0;
  return a.feats ? a.feats.filter((f) => featOn(v, f)).length : v;
}

export const ACCESSORIES = {
  head: {
    none: { name: 'None' }, cap: { name: 'Cap' }, beanie: { name: 'Beanie' }, cowboy: { name: 'Cowboy Hat' },
    party: { name: 'Party Hat' }, headphones: { name: 'Headphones' }, bucket: { name: 'Bucket Hat' },
    crown: { name: 'Champion Crown', ach: 'champion' }, helmet: { name: 'Racing Helmet', ach: 'speed' },
    hardhat: { name: 'Hard Hat', ach: 'waves' }, icepack: { name: 'Ice Pack', ach: 'knees' }, catears: { name: 'Cat Ears', ach: 'board' },
  },
  face: {
    none: { name: 'None' }, shades: { name: 'Sunglasses' }, mustache: { name: 'Mustache' }, clown: { name: 'Clown Nose' },
    eyepatch: { name: 'Eyepatch' }, bandana: { name: 'Bandana', ach: 'firstblood' }, visor: { name: 'Visor', ach: 'sharp' },
    goggles: { name: 'Flight Goggles', ach: 'flyer' }, bigglasses: { name: 'Big Glasses', ach: 'smarty' },
  },
  back: {
    none: { name: 'None' }, backpack: { name: 'Backpack' }, cape: { name: 'Cape' },
    wings: { name: 'Wings', ach: 'airborne', legacy: 'oldwings' }, voidcape: { name: 'Void Cape', ach: 'void' }, jetpack: { name: 'Jetpack', ach: 'nolife' }, cattail: { name: 'Cat Tail', ach: 'board' },
  },
};
export const LOOK_SLOTS = ['head', 'face', 'back'];
// outfit: skin, hair, top + bottom (all free)
export const SKIN_TONES = ['#e6cba2', '#ffdbac', '#f1c27d', '#e0ac69', '#c68642', '#8d5524', '#5c3a21', '#ffffff', '#9ad0ff', '#a8e6a1', '#c8a2ff', '#555560'];
export const HAIR_COLORS = ['#1a1a1a', '#4a2a10', '#8a5a2b', '#d9b45a', '#f2e6c8', '#c02030', '#ff4fd8', '#4fd8ff', '#7dff4f', '#ffffff', '#ff7a1a', '#7a4aff'];
export const CLOTH_COLORS = ['#ff4fd8', '#4fd8ff', '#ffe14d', '#7dff4f', '#ff7a1a', '#b07dff', '#ff4f4f', '#4fffb0', '#ffffff', '#ff9ad5', '#3a3a44', '#8a5a2b', '#1a1a1a', '#2a4a8a', '#3a6a2a', '#c8b48a'];
export const HAIRS = { none: { name: 'Bald' }, short: { name: 'Short' }, bowl: { name: 'Bowl Cut' }, spiky: { name: 'Spiky' }, mohawk: { name: 'Mohawk' }, long: { name: 'Long' }, ponytail: { name: 'Ponytail' }, bun: { name: 'Bun' }, afro: { name: 'Afro' } };
export const TOPS = { tank: { name: 'Sash' }, tee: { name: 'T-Shirt' }, hoodie: { name: 'Hoodie' }, jacket: { name: 'Jacket' }, suit: { name: 'Suit' }, runner: { name: 'Runner Jacket' }, none: { name: 'Nothing' }, maid: { name: 'Maid Dress', ach: 'board' } }; // tops can be achievement-locked too
export const BOTTOMS = { shorts: { name: 'Shorts' }, pants: { name: 'Pants' }, skirt: { name: 'Skirt' }, overalls: { name: 'Overalls', ach: 'smarty' } }; // bottoms can be achievement-locked too (hasAcc)
export const OUTFIT = { skin: SKIN_TONES, hairColor: HAIR_COLORS, topColor: CLOTH_COLORS, bottomColor: CLOTH_COLORS };
// joke body (free, looks only: hitboxes never change). build: the mannequin's shape. bigHead / bigButt: 0 (normal) .. JOKE_MAX
// chest / waist / hips: how wide that band of the torso is for a build. head / butt: growth per slider step
export const BUILDS = { '': { name: 'Mannequin', chest: 1, waist: 1, hips: 1 }, m: { name: 'Male', chest: 1.1, waist: 1.1, hips: 0.94 }, f: { name: 'Female', chest: 0.93, waist: 0.84, hips: 1.13 } };
export const JOKE_MAX = 4;
export const JOKE = { head: 0.24, butt: 0.036 };
export const DEFAULT_LOOK = { color: '', head: 'none', face: 'none', back: 'none', skin: '', hair: 'none', hairColor: '#1a1a1a', top: 'tank', topColor: '', bottom: 'shorts', bottomColor: '', build: '', bigHead: 0, bigButt: 0 };

export function achievementsFrom(stats) {
  const out = new Set();
  if (!stats) return out;
  for (const [id, a] of Object.entries(ACHIEVEMENTS)) if (achProgress(a, stats) >= a.goal) out.add(id);
  for (const [id, a] of Object.entries(LEGACY_ACHS)) if ((stats[a.stat] || 0) >= a.goal) out.add(id);
  return out;
}

const has = (T, k) => typeof k === 'string' && Object.hasOwn(T, k); // client data: real keys only
// anything you haven't unlocked falls back to none
export function validLook(look, achs) {
  const out = { ...DEFAULT_LOOK };
  if (!look || typeof look !== 'object') return out;
  if (LOOK_COLORS.includes(look.color)) out.color = look.color;
  for (const s of LOOK_SLOTS) {
    const a = has(ACCESSORIES[s], look[s]) && ACCESSORIES[s][look[s]];
    if (a && hasAcc(a, achs)) out[s] = look[s];
  }
  if (has(HAIRS, look.hair)) out.hair = look.hair;
  if (has(TOPS, look.top) && hasAcc(TOPS[look.top], achs)) out.top = look.top;
  if (has(BOTTOMS, look.bottom) && hasAcc(BOTTOMS[look.bottom], achs)) out.bottom = look.bottom;
  for (const [k, list] of Object.entries(OUTFIT)) if (list.includes(look[k])) out[k] = look[k];
  if (has(BUILDS, look.build)) out.build = look.build;
  for (const k of ['bigHead', 'bigButt']) if (Number.isInteger(look[k]) && look[k] >= 0 && look[k] <= JOKE_MAX) out[k] = look[k];
  return out;
}
