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
    knife_spoon: { name: 'Spoon', rarity: 'epic', weapon: 'knife' }, // a serving spoon. it still stabs
    slapper_foam: { name: 'Foam Finger', rarity: 'rare', weapon: 'slapper' },
    slapper_paw: { name: 'Bear Paw', rarity: 'epic', weapon: 'slapper' },
    bread_croissant: { name: 'Croissant Club', rarity: 'epic', weapon: 'bread' },
    ar_toy: { name: 'Toy Blaster', rarity: 'common', weapon: 'ar' },
    ar_bullpup: { name: 'Bullpup', rarity: 'rare', weapon: 'ar' },
    smg_uzi: { name: 'Pocket Uzi', rarity: 'rare', weapon: 'smg' },
    shotgun_double: { name: 'Double Barrel', rarity: 'rare', weapon: 'shotgun' },
    minigun_gatling: { name: 'Old Gatling', rarity: 'epic', weapon: 'minigun' },
    sniper_musket: { name: 'Musket', rarity: 'legendary', weapon: 'sniper' },
    // ach: never in a container. it's yours once you have that achievement (the server checks, see achInv)
    sniper_golden: { name: 'Golden Sniper', rarity: 'legendary', weapon: 'sniper', ach: 'royalty' },
    revolver_flint: { name: 'Flintlock', rarity: 'epic', weapon: 'revolver' },
    chicken_turkey: { name: 'Turkey Launcher', rarity: 'rare', weapon: 'chicken' },
    bowling_cannon: { name: 'Hand Cannon', rarity: 'epic', weapon: 'bowling' },
    nailgun_staple: { name: 'Office Stapler', rarity: 'rare', weapon: 'nailgun' },
    tennis_machine: { name: 'Ball Machine', rarity: 'epic', weapon: 'tennis' },
    cart_basket: { name: 'Basket Case', rarity: 'rare', weapon: 'cart' },
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
    katana_bokken: { name: 'Bokken', rarity: 'common', weapon: 'katana' },
    marbles_gumball: { name: 'Gumball Machine', rarity: 'rare', weapon: 'marbles' },
    bloodcross_shadow: { name: 'Shadow Cross', rarity: 'epic', weapon: 'bloodcross' }, // a charred hand that bleeds purple
    redline_hotrod: { name: 'Hot Rod', rarity: 'epic', weapon: 'redline' },
    katana_shirasaya: { name: 'Shirasaya', rarity: 'rare', weapon: 'katana' },
    scales_kangaroo: { name: 'Kangaroo Court', rarity: 'rare', weapon: 'scales' },
    shredder_chipper: { name: 'Wood Chipper', rarity: 'epic', weapon: 'shredder' },
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
    blastzone: { name: 'Blast Zone', rarity: 'legendary', desc: 'knocked clean off the screen. it is very loud' },
  },
  // your grappling hook: the rope and the thing on the end. one per player, everyone sees it.
  grapple: {
    rope: { name: 'Rope', rarity: 'free', desc: 'brown rope, iron hook. classic' },
    chain: { name: 'Chain', rarity: 'common', desc: 'clanky chain with a claw on the end' },
    candy: { name: 'Candy Cane', rarity: 'common', desc: 'striped rope, candy cane hook' },
    plunger: { name: 'Plunger', rarity: 'rare', desc: 'it sticks. do not ask where it has been' },
    vine: { name: 'Jungle Vine', rarity: 'rare', desc: 'leafy vine and a wooden hook' },
    laser: { name: 'Laser', rarity: 'epic', desc: 'a cyan beam that grabs things' },
    sticky: { name: 'Sticky Hand', rarity: 'epic', desc: 'the vending machine toy. stretchy' },
    rainbow: { name: 'Rainbow', rarity: 'legendary', desc: 'colour-cycling beam with a star on the end' },
  },
  // graffiti you paint on walls with Z. one per player. the art is drawn in public/js/sprays.js
  spray: {
    gg: { name: 'GG', rarity: 'free', desc: 'good game' },
    ez: { name: 'EZ', rarity: 'free', desc: 'too easy' },
    wp: { name: 'WP', rarity: 'free', desc: 'well played' },
    gl: { name: 'GL', rarity: 'free', desc: 'good luck (you need it)' },
    l: { name: 'L', rarity: 'common', desc: 'take the L' },
    noob: { name: 'NOOB', rarity: 'common', desc: 'for the new guy' },
    what: { name: '?', rarity: 'common', desc: 'what' },
    oof: { name: 'OOF', rarity: 'common', desc: 'big oof' },
    rip: { name: 'RIP', rarity: 'rare', desc: 'press F' },
    heart: { name: 'Heart', rarity: 'rare', desc: 'spread love. and bullets' },
    smiley: { name: 'Smiley', rarity: 'rare', desc: 'have a nice day' },
    skull: { name: 'Skull', rarity: 'epic', desc: 'spooky' },
    flame: { name: 'Flame', rarity: 'epic', desc: 'this wall is on fire' },
    duck: { name: 'Rubber Duck', rarity: 'epic', desc: 'quack' },
    logo: { name: 'JANKFIRE', rarity: 'legendary', desc: 'the rainbow logo' },
  },
};
// sprays: size of the decal (m), how far Z reaches (m), cooldown (s), how many are shown at once, the one you start with
export const SPRAY = { size: 1.2, reach: 6, cd: 10, max: 24, def: 'gg' };
export function ownedSpray(id, inv) { return owns(inv, 'spray', id) ? id : SPRAY.def; }
export const TYPES = ['finish', 'hat', 'effect', 'model'];
// everything you can roll: the four weapon-skin parts plus kill effects, grapple skins and sprays
export const LOOT_TYPES = [...TYPES, 'kill', 'grapple', 'spray'];
export const TYPE_NAMES_ALL = { finish: 'Wrap', hat: 'Hat', effect: 'Effect', model: 'Skin', kill: 'Kill Effect', grapple: 'Grapple', spray: 'Spray' };
export function ownedKill(id, inv) { return owns(inv, 'kill', id) ? id : 'none'; }
// hasOwn: ids come off the network, so '__proto__' and friends must not look like catalog entries
export function ownedGrapple(id, inv) { return typeof id === 'string' && Object.hasOwn(COSMETICS.grapple, id) && owns(inv, 'grapple', id) ? id : 'rope'; }
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
// wrap modes: what part of the weapon the wrap paints (normal = handle side, reverse = business end, full = all of it).
// free for everyone, and the 5th slot of a skin. old saves have no 5th slot: they read as normal
export const WRAP_MODES = ['normal', 'reverse', 'full'];
export const wrapMode = (v) => (WRAP_MODES.includes(v) ? v : 'normal');

export function ownedSkin(skin, inv, weapon) {
  const d = ['default', 'none', 'none', 'default'];
  if (!Array.isArray(skin)) return [...d, 'normal'];
  return [...TYPES.map((t, i) => {
    const v = skin[i] ?? d[i];
    if (t === 'model' && v !== 'default' && (typeof v !== 'string' || !Object.hasOwn(COSMETICS.model, v) || (weapon && COSMETICS.model[v].weapon !== weapon))) return 'default';
    return owns(inv, t, v) ? v : d[i];
  }), wrapMode(skin[4])];
}

export function unowned(inv) {
  const out = [];
  for (const t of LOOT_TYPES) for (const [id, c] of Object.entries(COSMETICS[t])) if (c.rarity !== 'free' && !c.ach && !owns(inv, t, id)) out.push({ type: t, id, rarity: c.rarity });
  return out;
}

// your inventory plus the achievement rewards you've earned (cosmetics with an ach field). achs: Set or array of ids.
// an ach item only ever counts from the achievement, never from the inventory itself
export function achInv(inv, achs) {
  const has = (a) => (achs instanceof Set ? achs.has(a) : Array.isArray(achs) && achs.includes(a));
  const out = {};
  for (const t of Object.keys(COSMETICS)) {
    const ids = inv && Array.isArray(inv[t]) ? inv[t].filter((id) => !(Object.hasOwn(COSMETICS[t], id) && COSMETICS[t][id].ach)) : [];
    for (const [id, c] of Object.entries(COSMETICS[t])) if (c.ach && has(c.ach)) ids.push(id);
    if (ids.length) out[t] = ids;
  }
  return out;
}

// three kinds of loot: crates have weapon skins, duffel bags have hats + effects, boxes have the paint (wraps + sprays)
export const CONTAINERS = {
  crate: { name: 'Crate', plural: 'Crates', types: ['model'], desc: 'weapon skins', field: 'crates' },
  bag: { name: 'Duffel Bag', plural: 'Duffel Bags', types: ['hat', 'effect', 'kill', 'grapple'], desc: 'hats, effects, kill effects + grapples', field: 'bags' },
  box: { name: 'Box', plural: 'Boxes', types: ['finish', 'spray'], desc: 'wraps + sprays', field: 'boxes' },
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
// lasso skin: a garden hose with a brass nozzle for the knot (the rope you throw and swing them on is hose too)
COSMETICS.model.lasso_hose = { name: 'Garden Hose', rarity: 'rare', weapon: 'lasso' };
// the big wrap pack: id -> [name, rarity]. the looks are drawn in public/js/wrappack.js
export const WRAP_PACK = {
  cherry: ['Cherry Pop', 'common'],
  tangerine: ['Tangerine', 'common'],
  lemon: ['Lemon Drop', 'common'],
  lime: ['Lime', 'common'],
  mint: ['Mint', 'common'],
  teal: ['Pool Tile', 'common'],
  sky: ['Sky', 'common'],
  navy: ['Navy', 'common'],
  grape: ['Grape Soda', 'common'],
  magenta: ['Hot Magenta', 'common'],
  cream: ['Cream', 'common'],
  matte: ['Matte Black', 'common'],
  white: ['Fridge White', 'common'],
  ketchup: ['Ketchup & Mustard', 'common'],
  creamsicle: ['Creamsicle', 'common'],
  bubblegum: ['Bubblegum', 'common'],
  hazard: ['Hazard Stripes', 'common'],
  hivis: ['Hi-Vis', 'common'],
  china: ["Grandma's China", 'rare'],
  crackle: ['Crackle Glaze', 'rare'],
  kintsugi: ['Kintsugi', 'legendary'],
  seigaiha: ['Seigaiha', 'rare'],
  asanoha: ['Asanoha', 'rare'],
  shibori: ['Shibori', 'rare'],
  washi: ['Washi Paper', 'rare'],
  sakura: ['Sakura Storm', 'epic'],
  koi: ['Koi Pond', 'epic'],
  bigwave: ['Big Wave', 'epic'],
  urushi: ['Urushi Maki-e', 'epic'],
  tokyo: ['Tokyo Night', 'legendary'],
  bubblewrap: ['Bubble Wrap', 'rare'],
  cheese: ['Swiss Cheese', 'rare'],
  denim: ['Denim', 'rare'],
  plaid: ['Dad Plaid', 'rare'],
  receipt: ['Receipt', 'rare'],
  pizza: ['Pizza', 'epic'],
  leopard: ['Leopard', 'epic'],
  zebra: ['Zebra', 'epic'],
  stained: ['Stained Glass', 'epic'],
  circuit: ['Circuit Board', 'epic'],
  crt: ['CRT', 'epic'],
  sheet: ['Spreadsheet', 'epic'],
  memo: ['Corporate Memo', 'epic'],
  holo: ['Holo Foil', 'legendary'],
  lchrome: ['Liquid Chrome', 'legendary'],
  glitch: ['Datamosh', 'legendary'],
  meat: ['Meat Suit', 'legendary'],
  corp: ['☺ CORP', 'legendary'],
};
for (const [id, [name, rarity]] of Object.entries(WRAP_PACK)) COSMETICS.finish[id] = { name, rarity };
