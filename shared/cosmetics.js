// Cosmetic catalog + rarities. Shared so the server can hand out rolls and reject cosmetics you don't own.
export const RARITY = {
  free: { name: 'Free', color: '#bbbbbb', weight: 0 },
  common: { name: 'Common', color: '#7dff4f', weight: 55 },
  rare: { name: 'Rare', color: '#4fb4ff', weight: 28 },
  epic: { name: 'Epic', color: '#c46bff', weight: 13 },
  legendary: { name: 'Legendary', color: '#ffb31a', weight: 4 },
};

export const COSMETICS = {
  finish: {
    default: { name: 'Default', rarity: 'free' }, pink: { name: 'Pink', rarity: 'free' }, wood: { name: 'Wood', rarity: 'free' },
    camo: { name: 'Camo', rarity: 'common' }, chrome: { name: 'Chrome', rarity: 'common' },
    ice: { name: 'Ice', rarity: 'rare' }, neon: { name: 'Neon', rarity: 'rare' }, ghost: { name: 'Ghost', rarity: 'rare' },
    gold: { name: 'Gold', rarity: 'epic' }, lava: { name: 'Lava', rarity: 'epic' }, galaxy: { name: 'Galaxy', rarity: 'epic' },
    tape: { name: 'Duct Tape', rarity: 'common' }, carbon: { name: 'Carbon Fiber', rarity: 'rare' },
    tiger: { name: 'Tiger', rarity: 'epic' }, fade: { name: 'Fade', rarity: 'epic' },
    missing: { name: 'Missing Texture', rarity: 'legendary' }, rainbow: { name: 'Rainbow', rarity: 'legendary' },
  },
  // weapon models. each one belongs to one weapon.
  model: {
    default: { name: 'Standard', rarity: 'free' },
    knife_kitchen: { name: 'Kitchen Knife', rarity: 'free', weapon: 'knife' },
    knife_bowie: { name: 'Bowie', rarity: 'common', weapon: 'knife' },
    knife_cleaver: { name: 'Cleaver', rarity: 'rare', weapon: 'knife' },
    knife_switch: { name: 'Switchblade', rarity: 'rare', weapon: 'knife' },
    knife_karambit: { name: 'Karambit', rarity: 'epic', weapon: 'knife' },
    knife_butterfly: { name: 'Butterfly', rarity: 'legendary', weapon: 'knife' },
    slapper_foam: { name: 'Foam Finger', rarity: 'rare', weapon: 'slapper' },
    slapper_paw: { name: 'Bear Paw', rarity: 'epic', weapon: 'slapper' },
    bread_croissant: { name: 'Croissant Club', rarity: 'epic', weapon: 'bread' },
    ar_toy: { name: 'Toy Blaster', rarity: 'common', weapon: 'ar' },
    ar_bullpup: { name: 'Bullpup', rarity: 'rare', weapon: 'ar' },
    smg_uzi: { name: 'Pocket Uzi', rarity: 'rare', weapon: 'smg' },
    shotgun_double: { name: 'Double Barrel', rarity: 'rare', weapon: 'shotgun' },
    minigun_gatling: { name: 'Old Gatling', rarity: 'epic', weapon: 'minigun' },
    sniper_musket: { name: 'Musket', rarity: 'legendary', weapon: 'sniper' },
    revolver_flint: { name: 'Flintlock', rarity: 'epic', weapon: 'revolver' },
    chicken_turkey: { name: 'Turkey Launcher', rarity: 'rare', weapon: 'chicken' },
    bowling_cannon: { name: 'Hand Cannon', rarity: 'epic', weapon: 'bowling' },
    banana_bunch: { name: 'Bunch Blaster', rarity: 'rare', weapon: 'banana' },
    bow_compound: { name: 'Compound Bow', rarity: 'rare', weapon: 'bow' },
    cig_cigar: { name: 'Fat Cigar', rarity: 'rare', weapon: 'cig' },
    blower_dryer: { name: 'Hair Dryer', rarity: 'epic', weapon: 'blower' },
    popper_bottle: { name: 'Champagne', rarity: 'epic', weapon: 'popper' },
    reverse_skip: { name: 'Skip Card', rarity: 'common', weapon: 'reverse' },
    snowball_ice: { name: 'Ice Cube', rarity: 'rare', weapon: 'snowball' },
    spoon_ladle: { name: 'Ladle', rarity: 'common', weapon: 'spoon' },
    slipper_croc: { name: 'Croc', rarity: 'epic', weapon: 'slipper' },
    scythe_reaper: { name: 'Reaper', rarity: 'legendary', weapon: 'scythe' },
  },
  hat: {
    none: { name: 'None', rarity: 'free' }, party: { name: 'Party Hat', rarity: 'free' }, cone: { name: 'Traffic Cone', rarity: 'free' },
    cowboy: { name: 'Cowboy Hat', rarity: 'common' }, chef: { name: 'Chef Hat', rarity: 'common' },
    propeller: { name: 'Propeller Cap', rarity: 'rare' }, eyes: { name: 'Googly Eyes', rarity: 'rare' },
    tophat: { name: 'Top Hat', rarity: 'epic' }, halo: { name: 'Halo', rarity: 'epic' },
    crown: { name: 'Crown', rarity: 'legendary' }, duck: { name: 'Tiny Duck', rarity: 'legendary' },
  },
  effect: {
    none: { name: 'None', rarity: 'free' }, smoke: { name: 'Smoke', rarity: 'free' }, bubbles: { name: 'Bubbles', rarity: 'free' },
    sparkles: { name: 'Sparkles', rarity: 'common' }, music: { name: 'Music', rarity: 'common' },
    hearts: { name: 'Hearts', rarity: 'rare' }, electric: { name: 'Electric', rarity: 'rare' },
    flames: { name: 'Flames', rarity: 'epic' }, money: { name: 'Money', rarity: 'epic' },
    rainbow: { name: 'Rainbow', rarity: 'legendary' },
  },
  // what happens to the people you kill. one per player, not per weapon.
  kill: {
    none: { name: 'Gibs', rarity: 'free', desc: 'the mannequin falls apart' },
    confetti: { name: 'Confetti', rarity: 'free', desc: 'party time' },
    grave: { name: 'Tombstone', rarity: 'common', desc: 'RIP bozo' },
    cash: { name: 'Make It Rain', rarity: 'common', desc: 'they explode into money' },
    pixel: { name: 'Missing Texture', rarity: 'rare', desc: 'they shatter into error cubes' },
    balloon: { name: 'Balloons', rarity: 'rare', desc: 'they float away' },
    chicken: { name: 'Chickens', rarity: 'epic', desc: 'they turn into chickens that run off' },
    bsod: { name: 'Blue Screen', rarity: 'epic', desc: 'fatal error: player.exe' },
    yeet: { name: 'Yeet', rarity: 'epic', desc: 'launched into orbit. ding.' },
    ascend: { name: 'Ascend', rarity: 'legendary', desc: 'a beam from the sky takes them' },
    duck: { name: 'Big Duck', rarity: 'legendary', desc: 'a giant duck eats them' },
  },
};
export const TYPES = ['finish', 'hat', 'effect', 'model'];
// everything you can roll: the four weapon-skin parts plus kill effects
export const LOOT_TYPES = [...TYPES, 'kill'];
export const TYPE_NAMES_ALL = { finish: 'Wrap', hat: 'Hat', effect: 'Effect', model: 'Skin', kill: 'Kill Effect' };
export function ownedKill(id, inv) { return owns(inv, 'kill', id) ? id : 'none'; }
// "finish" is called a wrap in the UI: the paint job. "model" is the skin: a different weapon shape.
export const TYPE_NAMES = { finish: 'Wrap', hat: 'Hat', effect: 'Effect', model: 'Skin' };
export function modelsFor(weapon) { return Object.entries(COSMETICS.model).filter(([id, c]) => id === 'default' || c.weapon === weapon).map(([id]) => id); }

// inventory = { finish: [...ids], hat: [...], effect: [...] } of things you rolled. Free stuff is always owned.
export function owns(inv, type, id) {
  const c = typeof id === 'string' && Object.hasOwn(COSMETICS, type) && Object.hasOwn(COSMETICS[type], id) && COSMETICS[type][id];
  if (!c) return false;
  return c.rarity === 'free' || !!(inv && Array.isArray(inv[type]) && inv[type].includes(id));
}

// drop anything you don't own (or a skin for the wrong weapon) back to the default. skin = [wrap, hat, effect, model]
export function ownedSkin(skin, inv, weapon) {
  const d = ['default', 'none', 'none', 'default'];
  if (!Array.isArray(skin)) return d;
  return TYPES.map((t, i) => {
    const v = skin[i] ?? d[i];
    if (t === 'model' && v !== 'default' && (typeof v !== 'string' || !Object.hasOwn(COSMETICS.model, v) || (weapon && COSMETICS.model[v].weapon !== weapon))) return 'default';
    return owns(inv, t, v) ? v : d[i];
  });
}

export function unowned(inv) {
  const out = [];
  for (const t of LOOT_TYPES) for (const [id, c] of Object.entries(COSMETICS[t])) if (c.rarity !== 'free' && !owns(inv, t, id)) out.push({ type: t, id, rarity: c.rarity });
  return out;
}

// three kinds of loot: crates have weapon skins, duffel bags have hats + effects, boxes have wraps
export const CONTAINERS = {
  crate: { name: 'Crate', plural: 'Crates', types: ['model'], desc: 'weapon skins', field: 'crates' },
  bag: { name: 'Duffel Bag', plural: 'Duffel Bags', types: ['hat', 'effect', 'kill'], desc: 'hats, effects + kill effects', field: 'bags' },
  box: { name: 'Box', plural: 'Boxes', types: ['finish'], desc: 'wraps', field: 'boxes' },
};
export function randomContainer(rnd = Math.random) { const r = rnd(); return r < 0.45 ? 'box' : r < 0.8 ? 'bag' : 'crate'; }

// pick a rarity by weight (only rarities you still have stuff left in), then a random item in it
export function rollPick(inv, rnd = Math.random, types = LOOT_TYPES) {
  const left = unowned(inv).filter((x) => types.includes(x.type));
  if (!left.length) return null;
  const rar = [...new Set(left.map((x) => x.rarity))];
  const total = rar.reduce((a, r) => a + RARITY[r].weight, 0);
  let x = rnd() * total, pick = rar[0];
  for (const r of rar) { x -= RARITY[r].weight; if (x <= 0) { pick = r; break; } }
  const pool = left.filter((i) => i.rarity === pick);
  return pool[Math.floor(rnd() * pool.length)];
}

export function itemInfo(type, id) {
  const c = COSMETICS[type][id];
  return { type, id, name: c.name, rarity: c.rarity, color: RARITY[c.rarity].color, rarityName: RARITY[c.rarity].name };
}
