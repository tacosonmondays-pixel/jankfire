// Character customizer: body colour + head / face / back accessories.
// Some accessories are free, the rest are unlocked by achievements (checked on the server).
export const LOOK_COLORS = ['#ff4fd8', '#4fd8ff', '#ffe14d', '#7dff4f', '#ff7a1a', '#b07dff', '#ff4f4f', '#4fffb0', '#ffffff', '#ff9ad5', '#3a3a44', '#8a5a2b'];

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
};

export const ACCESSORIES = {
  head: {
    none: { name: 'None' }, cap: { name: 'Cap' }, beanie: { name: 'Beanie' }, cowboy: { name: 'Cowboy Hat' },
    party: { name: 'Party Hat' }, headphones: { name: 'Headphones' }, bucket: { name: 'Bucket Hat' },
    crown: { name: 'Champion Crown', ach: 'champion' }, helmet: { name: 'Racing Helmet', ach: 'speed' },
    hardhat: { name: 'Hard Hat', ach: 'waves' }, icepack: { name: 'Ice Pack', ach: 'knees' },
  },
  face: {
    none: { name: 'None' }, shades: { name: 'Sunglasses' }, mustache: { name: 'Mustache' }, clown: { name: 'Clown Nose' },
    eyepatch: { name: 'Eyepatch' }, bandana: { name: 'Bandana', ach: 'firstblood' }, visor: { name: 'Visor', ach: 'sharp' },
  },
  back: {
    none: { name: 'None' }, backpack: { name: 'Backpack' }, cape: { name: 'Cape' },
    wings: { name: 'Wings', ach: 'flyer' }, voidcape: { name: 'Void Cape', ach: 'void' }, jetpack: { name: 'Jetpack', ach: 'nolife' },
  },
};
export const LOOK_SLOTS = ['head', 'face', 'back'];
export const DEFAULT_LOOK = { color: '', head: 'none', face: 'none', back: 'none' };

export function achievementsFrom(stats) {
  const out = new Set();
  if (!stats) return out;
  for (const [id, a] of Object.entries(ACHIEVEMENTS)) if ((stats[a.stat] || 0) >= a.goal) out.add(id);
  return out;
}

// anything you haven't unlocked falls back to none
export function validLook(look, achs) {
  const out = { ...DEFAULT_LOOK };
  if (!look || typeof look !== 'object') return out;
  if (LOOK_COLORS.includes(look.color)) out.color = look.color;
  for (const s of LOOK_SLOTS) {
    const a = ACCESSORIES[s][look[s]];
    if (a && (!a.ach || (achs && achs.has(a.ach)))) out[s] = look[s];
  }
  return out;
}
