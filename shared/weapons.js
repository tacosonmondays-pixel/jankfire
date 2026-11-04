// Weapon tuning. Unbalanced on purpose.
// kind: hitscan | proj | cone | melee | reverse
// hitscan guns use rate (shots/sec), mag, reload. Everything else uses cd (seconds).
export const SLOTS = ['primary', 'secondary', 'melee'];

export const WEAPONS = {
  // ------------------------------------------------------------ primary
  ar: {
    slot: 'primary', kind: 'hitscan', name: 'Assault Rifle', color: '#9fd36b',
    desc: 'Full auto, steady, accurate when you aim down sights.',
    auto: true, rate: 10, mag: 30, reload: 1.7, dmg: 11, head: 2, spread: 0.01, bloom: 0.004, maxBloom: 0.04,
    kb: 0, kbUp: 0, recoil: 0.4, kick: 0.008, range: 300,
    ads: { zoom: 1.5, spread: 0.2, p: [0, -0.11, -0.3] },
  },
  smg: {
    slot: 'primary', kind: 'hitscan', name: 'SMG', color: '#6bd3c8',
    desc: 'Sprays fast. Light, so you run faster with it out.',
    auto: true, rate: 16, mag: 45, reload: 1.5, dmg: 7, head: 1.5, spread: 0.03, bloom: 0.002, maxBloom: 0.05,
    kb: 0, recoil: 0.2, kick: 0.005, range: 200, speedMul: 1.2,
    ads: { zoom: 1.3, spread: 0.4, p: [0, -0.1, -0.28] },
  },
  redline: {
    slot: 'primary', kind: 'hitscan', name: 'Redline', color: '#ff3b3b',
    desc: 'The lower your HP, the faster it fires. On full health it plods along; on 10 HP it screams. Watch the needle.',
    auto: true, rate: 6, rateMax: 22, mag: 40, reload: 1.8, dmg: 10, head: 1.8, spread: 0.018, bloom: 0.0025, maxBloom: 0.06,
    kb: 0, recoil: 0.3, kick: 0.006, range: 250,
    ads: { zoom: 1.4, spread: 0.35, p: [0, -0.1, -0.3] },
  },
  shotgun: {
    slot: 'primary', kind: 'hitscan', name: 'Shotgun', color: '#e0a060',
    desc: '10 pellets. Shoot the floor to launch yourself.',
    rate: 1 / 0.75, mag: 6, reload: 2.0, pellets: 10, dmg: 8, head: 1.5, spread: 0.075,
    kb: 0, kbUp: 0, recoil: 17, kick: 0.08, range: 80,
    ads: { zoom: 1.2, spread: 0.65, p: [0, -0.1, -0.3] },
  },
  minigun: {
    slot: 'primary', kind: 'hitscan', name: 'Minigun', color: '#c8c8c8',
    desc: 'Spins up then never stops. The only gun that shoves people: hold it on someone and they get pushed away. The recoil is strong enough to fly on.',
    auto: true, rate: 25, mag: 250, reload: 3.5, spinup: 0.6, dmg: 6, head: 1.5, spread: 0.045,
    kb: 1.7, recoil: 1.25, kick: 0.004, range: 200,
    ads: { zoom: 1.15, spread: 0.6, p: [0.08, -0.2, -0.36] },
  },
  sniper: {
    slot: 'primary', kind: 'hitscan', name: 'Sniper', color: '#ff4fd8',
    desc: 'Right click to scope. A headshot ends them. Hipfire is a gamble.',
    rate: 1 / 1.1, mag: 5, reload: 2.2, dmg: 55, head: 2, spread: 0.05,
    kb: 0, kbUp: 0, recoil: 12, kick: 0.06, range: 500, tracer: 0xff4fd8, thick: 0.09,
    ads: { zoom: 4, spread: 0, scope: true, p: [0, -0.1, -0.25] },
  },
  chicken: {
    slot: 'primary', kind: 'proj', name: 'Chicken Rocket', color: '#ffe14d',
    desc: 'Rubber chickens that explode. Shoot your feet to rocket jump.',
    cd: 0.85, speed: 36, grav: 6, r: 0.35, radius: 7.5, dmg: 55, kb: 34, selfKb: 1.0,
    ads: { zoom: 1.25, p: [0.06, -0.15, -0.38] },
  },
  bowling: {
    slot: 'primary', kind: 'proj', name: 'Bowling Ball Launcher', color: '#6b7bff',
    desc: 'Rolls along the floor and bowls over everyone in the way.',
    cd: 1.3, speed: 30, grav: 30, r: 0.45, bounce: 0.25, dmg: 45, kb: 40, kbUp: 10, life: 6,
    ads: { zoom: 1.25, p: [0.06, -0.18, -0.38] },
  },
  bow: {
    slot: 'primary', kind: 'bow', name: 'Bow', color: '#c88a4a',
    desc: 'Hold to draw, let go to fire. Every arrow gets a random tip: regular, power, knockback, flame, explosion, gas or sleep.',
    cd: 0.35, draw: 0.9, speed: 34, speedMax: 85, grav: 9, r: 0.12, dmg: 20, dmgMax: 60,
    ads: { zoom: 1.6, p: [0, -0.1, -0.3] },
  },
  banana: {
    slot: 'primary', kind: 'proj', name: 'Peel Shooter', color: '#ffe135',
    desc: 'Hard bananas that bonk and make them slip. Misses stay on the floor as peels.',
    auto: true, cd: 0.3, speed: 42, grav: 18, r: 0.25, dmg: 14, kb: 9, bounce: 0.35,
    ads: { zoom: 1.25, p: [0, -0.12, -0.32] },
  },

  // ------------------------------------------------------------ secondary
  revolver: {
    slot: 'secondary', kind: 'hitscan', name: 'Revolver', color: '#e0c070',
    desc: '6 shots. Bullets ricochet off walls twice. Headshots basically kill.',
    rate: 1 / 0.4, mag: 6, reload: 2.0, dmg: 40, head: 2.5, spread: 0.003,
    kb: 0, kbUp: 0, recoil: 3, kick: 0.07, range: 250, ricochet: 2, tracer: 0xffd060,
    ads: { zoom: 1.4, spread: 0.2, p: [0, -0.085, -0.28] },
  },
  marbles: {
    slot: 'secondary', kind: 'hitscan', name: 'Marble Shotgun', color: '#7fd0ff',
    desc: 'A hundred glass marbles per shot. One marble barely tickles, but point blank they all land: one shot, one kill. They bounce round the floor after.',
    rate: 1 / 0.9, mag: 2, reload: 1.9, pellets: 100, dmg: 1.15, head: 1.3, spread: 0.27,
    kb: 0, kbUp: 0, recoil: 4, kick: 0.07, range: 30, marbles: true,
    ads: { zoom: 1.15, spread: 0.8, p: [0, -0.1, -0.3] },
  },
  cig: {
    slot: 'secondary', kind: 'cone', name: 'Cigarette', color: '#ff7a1a',
    desc: 'Hold to smoke. Let go to breathe fire for as long as you inhaled. Too long and you cough.',
    range: 13, cone: 0.42, dmg: 5, tick: 0.09, maxCharge: 3, coughAt: 4.5, exhaleMul: 1.2, jet: 6,
  },
  blower: {
    slot: 'secondary', kind: 'cone', name: 'Leaf Blower', color: '#ff9a3a',
    desc: 'Pushes people off the map. Point it at the floor to hover.',
    range: 16, cone: 0.42, tick: 0.09, push: 5.5, self: 34, fuel: 4, regen: 0.8,
  },
  cards: {
    slot: 'secondary', kind: 'cards', name: 'Card Deck', color: '#ffffff',
    desc: 'Hold 5 cards. Right click picks one, left click plays it, R redraws. Hearts heal, spades throw cards, clubs blast, diamonds dash, aces teleport, face cards go ultimate, jokers are random.',
    cd: 0.35,
  },
  card: { slot: null, kind: 'proj', name: 'Card', color: '#ffffff', cd: 0, speed: 55, grav: 4, r: 0.12, dmg: 9, kb: 4 },
  popper: {
    slot: 'secondary', kind: 'melee', name: 'Party Popper', color: '#ff6bd0',
    desc: 'Zero damage. Ridiculous knockback.',
    cd: 1.0, range: 9, cone: 0.6, dmg: 0, kb: 50, kbUp: 12, recoil: 12, radial: true,
  },
  reverse: {
    slot: 'secondary', kind: 'reverse', name: 'Reverse Card', color: '#ff3b3b',
    desc: 'For 1.2s, any damage or knockback aimed at you goes back to whoever sent it.',
    cd: 6, dur: 1.2,
  },
  duck: {
    slot: 'item', kind: 'proj', name: 'Rubber Duck', color: '#ffd23b',
    desc: 'Throw it. It turns into a black hole that sucks everyone in, then pops.',
    cd: 5, speed: 22, grav: 22, r: 0.3, bounce: 0.45, fuse: 1.0,
    holeTime: 2.5, holeR: 15, pull: 45, blastR: 9, blastKb: 30, blastDmg: 25,
  },
  snowball: {
    slot: 'secondary', kind: 'proj', name: 'Snowball', color: '#dff4ff',
    desc: 'Barely hurts. Every hit adds frost; 4 hits freezes them solid. Hit a frozen target and they shatter.',
    cd: 0.3, speed: 46, grav: 10, r: 0.13, dmg: 9, kb: 3, kbUp: 1.5, life: 3, freezeAt: 4, freeze: 2.4, frostDecay: 3,
  },
  // thrown items (not in a weapon slot; the item slot fires these)
  frag: { slot: 'hidden', kind: 'proj', name: 'Frag Grenade', color: '#7a8a3a', speed: 24, grav: 22, r: 0.15, bounce: 0.42, fuse: 2.2, radius: 7.5, dmg: 105, kb: 34, life: 6 },
  smokegren: { slot: 'hidden', kind: 'proj', name: 'Smoke Bomb', color: '#9aa0a8', speed: 22, grav: 22, r: 0.15, bounce: 0.35, fuse: 1.3, life: 5 },

  // ------------------------------------------------------------ melee
  bread: {
    slot: 'melee', kind: 'melee', name: 'Bread', color: '#d9a35b',
    desc: 'A huge loaf. Home run hits. Smack the floor or a wall to pogo off it.',
    cd: 0.55, range: 4.2, cone: 0.8, dmg: 40, kb: 38, kbUp: 10, pogo: 16, delay: 0.07,
  },
  slipper: {
    slot: 'melee', kind: 'proj', name: 'Slipper', color: '#ff9ad5',
    desc: 'Thrown like a boomerang. Hits on the way out and on the way back.',
    cd: 0.5, speed: 32, grav: 0, r: 0.3, out: 0.45, back: 38, dmg: 30, kb: 22, kbUp: 6, life: 3,
  },
  katana: {
    slot: 'melee', kind: 'melee', name: 'Katana', color: '#e8e8f0',
    desc: 'Every kill with it makes the blade longer and your reach further. Resets when you die. How long can you get it?',
    cd: 0.5, range: 2.8, cone: 0.7, dmg: 48, kb: 6, kbUp: 2, delay: 0.1, grow: 0.5, growMax: 30,
  },
  knife: {
    slot: 'melee', kind: 'melee', name: 'Knife', color: '#c8d0dc',
    desc: 'Left click: fast slashes. Right click: heavy stab (from behind = dead). Comes in a lot of skins.',
    cd: 0.42, range: 2.6, cone: 0.75, dmg: 55, kb: 9, kbUp: 3, delay: 0.08, backstab: 3, speedMul: 1.1,
    // right click: CS-style heavy stab. slower, shorter reach, hits harder; from behind it's a kill
    heavy: { dmg: 90, cd: 0.95, range: 2.2, cone: 0.6, kb: 16, kbUp: 4 },
  },
  slapper: {
    slot: 'melee', kind: 'melee', name: 'Hand Slapper', color: '#ff7ab8',
    desc: 'A big toy hand on a stick. Point blank only. Launches them and makes them slip.',
    cd: 0.8, range: 1.9, cone: 0.8, dmg: 15, kb: 55, kbUp: 14, delay: 0.1, slip: true, radial: true,
  },
  spoon: {
    slot: 'melee', kind: 'melee', name: 'Spoon', color: '#e8e8f0',
    desc: 'Kills in one hit, but only point blank. You run way faster holding it.',
    cd: 0.7, range: 2.0, cone: 0.9, dmg: 999, kb: 12, kbUp: 6, delay: 0.05, speedMul: 1.8,
  },
  scales: {
    slot: 'melee', kind: 'melee', name: 'Scales of Justice', color: '#ffc83a',
    desc: 'Hits as hard as they deserve: leaders, streakers and your killer take up to x3.',
    // dmg is multiplied by the server's verdict at hit time (shared/verdict.js): x0.4 .. x3
    cd: 0.6, range: 3.2, cone: 0.75, dmg: 35, kb: 14, kbUp: 5, delay: 0.22, verdict: true, speedMul: 0.95,
  },

  // ------------------------------------------------------------ killstreak reward (not in loadouts)
  scythe: {
    slot: 'streak', kind: 'melee', name: 'Scythe Rifle', color: '#3ee6c8',
    desc: 'Killstreak reward. Wide reaping swings. X turns it into a rifle. Hold V to glitch dash.',
    cd: 0.6, range: 4.6, cone: 1.1, dmg: 65, kb: 30, kbUp: 9, delay: 0.16,
  },
  scythe_rifle: {
    slot: 'streak', kind: 'hitscan', name: 'Scythe Rifle (rifle)', color: '#3ee6c8',
    desc: 'The same scythe, folded into a sniper. X to flip back.',
    rate: 1 / 0.9, mag: 4, reload: 1.8, dmg: 60, head: 2, spread: 0.03, kb: 0, kbUp: 0, recoil: 20, kick: 0.07,
    range: 500, tracer: 0x3ee6c8, thick: 0.08,
    ads: { zoom: 3, spread: 0, scope: true, p: [0, -0.1, -0.25] },
  },
  dash: { slot: null, kind: 'dash', name: 'Glitch Dash', color: '#ff00dc', dmg: 30, kb: 28, kbUp: 8, range: 3.5, speed: 38, max: 5, regen: 1.2 },
};

export const ORDER = Object.keys(WEAPONS);
// shots per second right now. The Redline speeds up as your HP drops (rate at full HP -> rateMax at 0 HP).
export function fireRate(w, hp = 100) {
  if (!w.rateMax) return w.rate;
  const missing = Math.max(0, Math.min(1, 1 - (Number(hp) || 0) / 100));
  return w.rate + (w.rateMax - w.rate) * missing;
}
// killstreaks: kills in a row without dying. earned ones wait in your pocket (even after you die) until you press 5/6/7.
export const STREAKS = {
  moonboots: { kills: 3, name: 'Moon Boots', desc: 'low gravity + huge jumps for 25s', auto: true, dur: 25 },
  chickenstrike: { kills: 4, name: 'Chicken Strike', desc: 'rain exploding chickens where you aim', deploy: true },
  scythe: { kills: 5, name: 'Scythe Rifle', desc: 'X: rifle mode · hold V: glitch dash', auto: true },
  spinbot: { kills: 6, name: 'Spinbot', desc: 'aimbot + spinbot for 10s. you are now a cheater.', auto: true, dur: 10 },
  satellite: { kills: 7, name: 'Spy Satellite', desc: 'see every enemy through walls for 20s', auto: true, dur: 20 },
  giantduck: { kills: 10, name: 'Giant Duck', desc: 'a giant black hole where you aim that pulls in everyone but you', deploy: true },
};
export const DEFAULT_LOADOUT = { primary: 'ar', secondary: 'cig', melee: 'bread', item: 'frag', streaks: ['moonboots', 'chickenstrike', 'scythe'] };

// items: one per loadout, G to use. charges come back over time (recharge = seconds per charge)
export const ITEMS = {
  frag: { name: 'Frag Grenade', desc: 'Bounces, blows up after 2s. Knocks people (and you) flying.', charges: 2, recharge: 16, color: '#9ab04a', proj: 'frag' },
  medkit: { name: 'Medkit', desc: 'Heals 60 over a couple of seconds.', charges: 1, recharge: 22, color: '#ff4f4f', heal: 60 },
  bubble: { name: 'Shield Bubble', desc: 'A dome for 7s. Nothing from outside can hurt anyone inside.', charges: 1, recharge: 28, color: '#4fd8ff', dur: 7, r: 4.4 },
  duck: { name: 'Rubber Duck', desc: 'Turns into a black hole that sucks everyone in, then pops.', charges: 1, recharge: 20, color: '#ffd23b', proj: 'duck' },
  smoke: { name: 'Smoke Bomb', desc: 'A thick cloud nobody can see through for 10s.', charges: 2, recharge: 18, color: '#9aa0a8', proj: 'smokegren', dur: 10, r: 6.5 },
};
export const ITEM_ORDER = ['frag', 'medkit', 'bubble', 'duck', 'smoke'];

export function validLoadout(lo) {
  const out = { ...DEFAULT_LOADOUT };
  if (lo) for (const s of SLOTS) if (WEAPONS[lo[s]] && WEAPONS[lo[s]].slot === s) out[s] = lo[s];
  if (lo && ITEMS[lo.item]) out.item = lo.item;
  out.streaks = validStreaks(lo && lo.streaks);
  return out;
}

// hipfire spread multiplier (lobby setting). aiming down sights always tightens it further.
export const HIPFIRE = {
  laser: { name: 'Laser (perfect)', mul: 0 },
  tight: { name: 'Tight', mul: 0.5 },
  normal: { name: 'Normal', mul: 1 },
  sloppy: { name: 'Sloppy', mul: 2 },
  storm: { name: 'Stormtrooper', mul: 4 },
};
export const BOT_DIFF = {
  easy: { name: 'Easy', react: 750, err: 0.09, rate: 0.45, turn: 4, speed: 0.75 },
  normal: { name: 'Normal', react: 420, err: 0.045, rate: 0.7, turn: 7, speed: 0.9 },
  hard: { name: 'Hard', react: 200, err: 0.018, rate: 1, turn: 12, speed: 1 },
};
export const MODES = {
  ffa: { name: 'Online', desc: 'Free for all with real people.' },
  bots: { name: 'Bots', desc: 'Free for all against bots. Just you.' },
  coop: { name: 'Coop', desc: 'You and your friends against waves of bots.' },
  training: { name: 'Training', desc: 'Target dummies, infinite ammo, a movement playground.' },
};

export const ARROW_TIPS = {
  regular: { name: 'Regular', color: '#dddddd' },
  power: { name: 'Power', color: '#ffe14d' },
  knockback: { name: 'Knockback', color: '#4fd8ff' },
  flame: { name: 'Flame', color: '#ff6a1a' },
  explosion: { name: 'Explosion', color: '#ff3030' },
  gas: { name: 'Gas', color: '#7dff4f' },
  sleep: { name: 'Sleep', color: '#b07dff' },
};
export const SUITS = { h: { name: 'Hearts', sym: '♥', color: '#e0202a' }, s: { name: 'Spades', sym: '♠', color: '#111111' }, c: { name: 'Clubs', sym: '♣', color: '#111111' }, d: { name: 'Diamonds', sym: '♦', color: '#e0202a' }, j: { name: 'Joker', sym: '★', color: '#b07dff' } };
export const RANKS = ['', 'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'];

export const FLAGS = { SMOKE: 1, FIRE: 2, BLOW: 4, SPIN: 8, SLIP: 16, SLIDE: 32, REVERSE: 64, CROUCH: 128, DASH: 256 };
export const SLIP_TIME = 1.7;
export const HOOK = { range: 90, pull: 42, tug: 16 };

// your 3 killstreaks, cheapest first (keys 5 / 6 / 7)
export function validStreaks(list) {
  const ok = Array.isArray(list) ? [...new Set(list.filter((id) => STREAKS[id]))] : [];
  const out = ok.slice(0, 3);
  for (const id of DEFAULT_LOADOUT.streaks) if (out.length < 3 && !out.includes(id)) out.push(id);
  for (const id of Object.keys(STREAKS)) if (out.length < 3 && !out.includes(id)) out.push(id);
  return out.sort((a, b) => STREAKS[a].kills - STREAKS[b].kills);
}
