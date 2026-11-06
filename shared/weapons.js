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
    desc: 'Spins up then never stops. Its bullets shove people: hold it on someone and they get pushed away. The recoil is strong enough to fly on.',
    auto: true, rate: 25, mag: 250, reload: 3.5, spinup: 0.6, dmg: 6, head: 1.5, spread: 0.045,
    kb: 1.7, recoil: 1.25, kick: 0.004, range: 200,
    ads: { zoom: 1.15, spread: 0.6, p: [0.08, -0.2, -0.36] },
  },
  sniper: {
    slot: 'primary', kind: 'hitscan', name: 'Sniper', color: '#ff4fd8',
    desc: 'Right click to scope. A headshot always kills, a body shot sends them flying off the map. Hipfire is a gamble.',
    rate: 1 / 1.1, mag: 5, reload: 2.2, dmg: 55, head: 2, spread: 0.05,
    kb: 75, kbUp: 14, recoil: 12, kick: 0.06, range: 500, tracer: 0xff4fd8, thick: 0.09,
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
    desc: 'Hold to draw, let go to fire. Every arrow gets a random tip: regular, power, knockback, flame, explosion, gas or sleep (knocks them flat for 4 s).',
    cd: 0.35, draw: 0.9, speed: 34, speedMax: 85, grav: 9, r: 0.12, dmg: 20, dmgMax: 60,
    ads: { zoom: 1.6, p: [0, -0.1, -0.3] },
  },
  banana: {
    slot: 'primary', kind: 'proj', name: 'Peel Shooter', color: '#ffe135',
    desc: 'Hard bananas that bonk and make them slip. Misses stay on the floor as peels.',
    auto: true, cd: 0.3, speed: 42, grav: 18, r: 0.25, dmg: 14, kb: 9, bounce: 0.35,
    ads: { zoom: 1.25, p: [0, -0.12, -0.32] },
  },
  // hold to suck (cone like the leaf blower, but it pulls). the server works out the pull and the shredding:
  // pull = pull..pullMax per tick (harder the closer), capped so they arrive at ~vmax; inside grabR of the intake
  // (mouth m in front of your eyes) it just yanks them into the teeth, inside shredR they take dps.
  // heat works like the blower's fuel.
  shredder: {
    slot: 'primary', kind: 'cone', name: 'Shredder', color: '#ffb31a',
    desc: 'An industrial vacuum-shredder. Hold to suck people in, harder the closer they get. Whoever reaches the intake gets shredded and spat out the chute. Overheats after 4 s.',
    range: 14, cone: 0.61, tick: 0.09, mouth: 1.3, shredR: 2, grabR: 3.5, dps: 150, pull: 4, pullMax: 22, vmax: 10, lift: 1.4,
    fuel: 4, regen: 1, coolTo: 0.35, speedMul: 0.92,
  },

  // hold to charge (charge s for a full one, you walk at slow x speed), let go: a beam down where you look for dur s
  // (it follows your aim) that goes through everyone in it. [a, b] pairs run from a tap (charge <= tap s) to a full charge.
  // the server times the charge itself (from the 'ch' you sent when you pressed) and does every hit
  laser: {
    slot: 'primary', kind: 'beam', name: 'Big Laser Pointer', color: '#39ff14',
    desc: 'An office laser pointer the size of a leg. Hold to charge it up (you walk slower), let go for a fat beam that goes through everyone in a line. Tap it for a little zap. Do not point at aircraft.',
    charge: 1.2, tap: 0.3, cd: 0.45, range: 120, tick: 0.1, dur: [0.16, 0.62], r: [0.22, 0.7], dmg: [5, 21], kb: [1.5, 7], kbUp: 1.5,
    slow: 0.72, speedMul: 0.97, tracer: 0x39ff14,
  },

  // ------------------------------------------------------------ secondary
  revolver: {
    slot: 'secondary', kind: 'hitscan', name: 'Revolver', color: '#e0c070',
    desc: '6 shots, twirled round your finger after each one. Tap for a dead-accurate shot, hold to fan the hammer: the rest goes in a second, wild and a bit weaker. Ricochets off walls twice. A headshot does 96: almost a kill.',
    rate: 1 / 0.4, mag: 6, reload: 2.0, dmg: 40, head: 2.4, spread: 0.003,
    kb: 0, kbUp: 0, recoil: 3, kick: 0.07, range: 250, ricochet: 2, tracer: 0xffd060,
    // hold fire to fan the hammer: after `hold` s the rest of the cylinder goes at `rate`/s, `dmg` a shot, way more spread,
    // `kick` x the aim kick and recoil. the server enforces the rate, the damage and 6 shots per reload
    fanHammer: { rate: 6, hold: 0.2, dmg: 28, spread: 0.065, kick: 0.3 },
    ads: { zoom: 1.4, spread: 0.2, p: [0, -0.085, -0.28] },
  },
  // plain sidearms (public/js/sidearms.js does their moving parts + the akimbo hands)
  // Plan B: semi-auto, one shot per click (the server holds the rate). the slide locks back on the last round
  pistol: {
    slot: 'secondary', kind: 'hitscan', name: 'Plan B', color: '#a0b4ff',
    desc: 'A plain pistol for when plan A runs dry. Out of the holster in a blink, 12 shots, and the slide locks back to tell you you\'re empty.',
    rate: 5, mag: 12, reload: 1.35, dmg: 20, head: 2.2, spread: 0.006, bloom: 0.007, maxBloom: 0.03,
    kb: 0, kbUp: 0, recoil: 0.6, kick: 0.035, range: 220, tracer: 0xb8c8ff, speedMul: 1.05,
    ads: { zoom: 1.35, spread: 0.25, p: [0, -0.085, -0.28] },
  },
  // Lefty & Righty: one machine pistol per hand. left click = left gun, right click = right gun (no aiming), each full
  // auto at `rate`, each with its own half of `mag` (mag = both hands) and its own reload. `hands` = how many guns
  // fire at once, so the server lets the pair through at hands x rate
  akimbo: {
    slot: 'secondary', kind: 'hitscan', name: 'Lefty & Righty', color: '#00e5a0', hands: 2,
    desc: 'Two machine pistols, one per hand. Left click fires lefty, right click fires righty, hold both to hose. They reload one at a time, so keep one busy.',
    auto: true, rate: 9, mag: 40, reload: 1.5, dmg: 6, head: 1.6, spread: 0.045, bloom: 0.003, maxBloom: 0.05,
    kb: 0, recoil: 0.25, kick: 0.012, range: 140, tracer: 0x7dffd0, speedMul: 1.05,
  },
  // Half a Shotgun: a sawed-off double. both shells, a huge shove on whoever eats the pellets, and enough kick that a
  // shot at your feet hops you off the floor
  sawnoff: {
    slot: 'secondary', kind: 'hitscan', name: 'Half a Shotgun', color: '#e05a3a',
    desc: 'Somebody sawed a shotgun in half. Two shells, and point blank they go flying. Shoot the floor for a little hop.',
    rate: 1 / 0.3, mag: 2, reload: 2.3, pellets: 12, dmg: 9, head: 1.3, spread: 0.11,
    kb: 3.4, kbUp: 9, recoil: 10, kick: 0.09, range: 32, tracer: 0xffa060,
    ads: { zoom: 1.12, spread: 0.7, p: [0, -0.1, -0.3] },
  },
  marbles: {
    slot: 'secondary', kind: 'hitscan', name: 'Marble Shotgun', color: '#7fd0ff',
    desc: 'A hundred glass marbles per shot. One marble barely tickles, but point blank they all land: one shot, one kill. They stay on the floor after: anyone who runs over them slips (crouch-walk to cross).',
    rate: 1 / 0.9, mag: 2, reload: 1.9, pellets: 100, dmg: 1.15, head: 1.3, spread: 0.27,
    kb: 0, kbUp: 0, recoil: 4, kick: 0.07, range: 30, marbles: true,
    ads: { zoom: 1.15, spread: 0.8, p: [0, -0.1, -0.3] },
  },
  cig: {
    slot: 'secondary', kind: 'cone', name: 'Cigarette', color: '#ff7a1a',
    desc: 'Hold to smoke. Let go to breathe fire for as long as you inhaled. Hold it into TOO MUCH and you cough smoke instead of fire (and it hurts).',
    range: 13, cone: 0.42, dmg: 5, tick: 0.09, maxCharge: 3, coughAt: 4.5, exhaleMul: 1.2, jet: 6,
  },
  // the shot is paid in your own HP (cost). the bolt sticks, a cross bursts out of them (fuse), then pops (burst) for dmg + a small blast
  bloodcross: {
    slot: 'secondary', kind: 'blood', name: 'Blood Cross', color: '#ff1f3d',
    desc: 'No gun: you shoot blood out of your fingertip and every shot costs you 12 HP. The bolt sticks to whoever it hits, a cross bursts out of their body and they pop. A kill pays the blood back.',
    cd: 0.7, speed: 75, grav: 0, r: 0.15, life: 2, cost: 12, fuse: 0.6, burst: 0.25, dmg: 75, blastR: 3, blastDmg: 35, kb: 6,
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
  // item now (G), like the duck: this is how it works, ITEMS.popper is how often you get it
  popper: {
    slot: 'item', kind: 'melee', name: 'Party Popper', color: '#ff6bd0',
    desc: 'Yank the string: a confetti blast shoves everyone in front of you away, hard, and launches you backwards. Zero damage.',
    range: 9, cone: 0.6, dmg: 0, kb: 50, kbUp: 12, recoil: 17, lift: 5, radial: true,
  },
  reverse: {
    slot: 'item', kind: 'reverse', name: 'Reverse Card', color: '#ff3b3b',
    desc: 'Flash it and for 3s every bullet, blast and shove aimed at you goes back to whoever sent it.',
    dur: 3,
  },
  duck: {
    slot: 'item', kind: 'proj', name: 'Rubber Duck', color: '#ffd23b',
    desc: 'Throw it. It homes in on enemies and sticks to whoever it touches: the black hole opens ON them and follows them, dragging their friends in, eating everyone\'s momentum and snapping grapples. Then it pops.',
    cd: 5, speed: 22, grav: 22, r: 0.3, bounce: 0.45, fuse: 1.0,
    holeTime: 3, holeR: 15, pull: 70, blastR: 9, blastKb: 30, blastDmg: 45,
    // homing (range, cos of the cone, rad/s), sticking (delay before the hole opens on them, crush per 0.1s on the victim),
    // momentum eater (speed bled per second at the middle, how much of that the one it's stuck to gets, rope snap distance)
    homeR: 25, homeCos: 0.5, turn: 3, stick: 0.3, stuckDmg: 1, drag: 6, onDrag: 0.5, snapR: 6, lift: 1,
  },
  snowball: {
    slot: 'secondary', kind: 'proj', name: 'Snowball', color: '#dff4ff',
    desc: 'Barely hurts. Every hit adds frost; 4 hits freezes them solid. Hit a frozen target and they shatter.',
    cd: 0.3, speed: 46, grav: 10, r: 0.13, dmg: 9, kb: 3, kbUp: 1.5, life: 3, freezeAt: 4, freeze: 2.4, frostDecay: 3,
  },
  // thrown items (not in a weapon slot; the item slot fires these)
  frag: { slot: 'hidden', kind: 'proj', name: 'Frag Grenade', color: '#7a8a3a', speed: 24, grav: 22, r: 0.15, bounce: 0.42, fuse: 2.2, radius: 7.5, dmg: 105, kb: 34, life: 6 },
  calc: { slot: 'hidden', kind: 'proj', name: 'Pop Quiz', color: '#7fffd4', speed: 30, grav: 16, r: 0.22, bounce: 0.35, life: 3.5 }, // pop quiz: the thrown calculator
  smokegren: { slot: 'hidden', kind: 'proj', name: 'Smoke Bomb', color: '#9aa0a8', speed: 22, grav: 22, r: 0.15, bounce: 0.35, fuse: 1.3, life: 5 },

  // bubble wand soap bubbles: they fly the exact path in shared/wand.js (kind 'soap', so nothing can 'fire' them)
  soap: { slot: 'hidden', kind: 'soap', name: 'Bubble Wand', color: '#9fe8ff', speed: 11, r: 0.4, drag: 1.4, drift: 1, lift: 0.25, bob: 0.2, sway: 0.25, life: 4 },

  // ------------------------------------------------------------ melee
  bread: {
    slot: 'melee', kind: 'melee', name: 'Bread', color: '#d9a35b',
    desc: 'A huge loaf. Home run hits. Smack the floor or a wall to pogo off it.',
    cd: 0.55, range: 4.2, cone: 0.8, dmg: 40, kb: 38, kbUp: 10, pogo: 16, delay: 0.07,
  },
  slipper: {
    slot: 'melee', kind: 'proj', name: 'Slipper', color: '#ff9ad5',
    desc: 'Thrown like a boomerang. Curves into the nearest enemy in front of it, then flies back to you. Hits on the way out and on the way back.',
    cd: 0.5, speed: 32, grav: 0, r: 0.3, out: 0.45, back: 38, dmg: 30, kb: 22, kbUp: 6, life: 3,
    // homing on the way out: locks the nearest enemy within homeR m and homeCone degrees of its heading, turns homeTurn rad/s,
    // and keeps flying out (up to outLock s) while it has a lock so far targets are reachable
    homeR: 30, homeCone: 70, homeTurn: 5, outLock: 1,
  },
  katana: {
    slot: 'melee', kind: 'melee', name: 'Katana', color: '#e8e8f0',
    desc: 'Every kill makes the blade longer and your reach further (resets when you die). Right click parries: bullets, rockets and swords from the front bounce off, and a perfect parry sends bullets straight back.',
    cd: 0.5, range: 2.8, cone: 0.7, dmg: 48, kb: 6, kbUp: 2, delay: 0.1, grow: 0.5, growMax: 30,
  },
  parry: { slot: null, kind: 'parry', name: 'Katana Parry', color: '#9fe8ff' }, // kill credit: bullets parried back, parry shoves into the void
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
  spoon: { // modeOnly: not in the loadout any more (it's a knife skin now); Gun Game's last rung and Spoons & Grapples still hand it out
    slot: 'melee', kind: 'melee', name: 'Spoon', color: '#e8e8f0', modeOnly: true,
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

  // ------------------------------------------------------------ mode weapons (handed out by a game mode, never in loadouts)
  claw: {
    slot: 'mode', mode: 'inf', kind: 'melee', name: 'Zombie Claw', color: '#7dff4f',
    desc: 'Infection only. Two swipes and they turn. Zombies run faster with their arms out.',
    cd: 0.45, range: 2.6, cone: 0.85, dmg: 55, kb: 8, kbUp: 3, delay: 0.08, speedMul: 1.3,
  },
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
  overdrive: { kills: 8, name: 'Overdrive Rig', desc: '25s as a scrap-built juggernaut: overshield, LMB rocket punch, RMB block, Space jumps sky high (hold to leap), E thrusters, G homing missiles, R quickhack', auto: true, dur: 25 },
  spinbot: { kills: 6, name: 'Spinbot', desc: 'aimbot + spinbot for 10s. you are now a cheater.', auto: true, dur: 10 },
  wreckingball: { kills: 6, name: 'Wrecking Ball', desc: 'become a giant steel wrecking ball for 20s: ram people (faster = harder), swing on the chain (E, W pumps it), crouch in the air to ground slam (higher = bigger)', auto: true, dur: 20 },
  satellite: { kills: 7, name: 'Spy Satellite', desc: 'see every enemy through walls for 20s', auto: true, dur: 20 },
  giantduck: { kills: 10, name: 'Giant Duck', desc: 'a giant black hole where you aim that pulls in everyone but you and eats their momentum', deploy: true },
};
export const DEFAULT_LOADOUT = { primary: 'ar', secondary: 'cig', melee: 'bread', item: 'frag', streaks: ['moonboots', 'chickenstrike', 'scythe'] };

// items: one per loadout, G to use. charges come back over time (recharge = seconds per charge)
// charges refill when you respawn, so charges = what you get per life, recharge = how often in a long life.
// w: the item is that weapon's model: it pops into your hand (with its skin) when you use it
export const ITEMS = {
  frag: { name: 'Frag Grenade', desc: 'Bounces, blows up after 2s. Knocks people (and you) flying.', charges: 2, recharge: 18, color: '#9ab04a', proj: 'frag' },
  medkit: { name: 'Medkit', desc: 'Heals 45 over a couple of seconds. Carry two.', charges: 2, recharge: 20, color: '#ff4f4f', heal: 45 },
  bubble: { name: 'Shield Bubble', desc: 'A dome for 7s. Nothing from outside can hurt anyone inside.', charges: 1, recharge: 28, color: '#4fd8ff', dur: 7, r: 4.4 },
  duck: { name: 'Rubber Duck', desc: 'Homes in and sticks to an enemy. The black hole opens on them and follows them: their friends get dragged in, speed gets eaten, ropes snap. Then it pops.', charges: 1, recharge: 20, color: '#ffd23b', proj: 'duck' },
  smoke: { name: 'Smoke Bomb', desc: 'A thick cloud nobody can see through for 10s.', charges: 3, recharge: 14, color: '#9aa0a8', proj: 'smokegren', dur: 10, r: 6.5 },
  popper: { name: 'Party Popper', desc: 'A confetti blast: everyone in front of you gets shoved away hard and you get launched backwards. Zero damage, all void kills and escapes.', charges: 2, recharge: 9, color: '#ff6bd0', w: 'popper' },
  reverse: { name: 'Reverse Card', desc: 'For 3s every bullet, blast and shove aimed at you goes back to whoever sent it. Everyone sees you flash it.', charges: 1, recharge: 22, color: '#ff3b3b', w: 'reverse' },
  // bubbles: soap bubbles per blow, gap ms apart. a hit seals them in a giant bubble for dur s that floats up (rise m/s)
  // and away from you (drift m/s), then pops. any hit pops it early. safe = s before they can be bubbled again, or
  // safeK x how long they were in if that's longer (two wands can't chain someone)
  wand: { name: 'Bubble Wand', desc: 'Blow a stream of soap bubbles. An enemy one touches is sealed in a giant bubble that floats up and away for 5s (no moving, no shooting), then pops and drops them. Over the void, that is your kill. Any hit pops it early.', charges: 2, recharge: 15, color: '#9fe8ff', bubbles: 4, gap: 90, dur: 5, rise: 2, drift: 1.5, safe: 1.5, safeK: 0.6 },
};
export const ITEM_ORDER = ['frag', 'medkit', 'bubble', 'duck', 'smoke', 'popper', 'reverse', 'wand', 'camera', 'quiz', 'nvg'];

// a real key of the table (client data: no '__proto__', no arrays)
const has = (T, k) => typeof k === 'string' && Object.hasOwn(T, k);
export function validLoadout(lo) {
  const out = { ...DEFAULT_LOADOUT };
  if (lo) for (const s of SLOTS) if (has(WEAPONS, lo[s]) && WEAPONS[lo[s]].slot === s && !WEAPONS[lo[s]].modeOnly) out[s] = lo[s];
  if (lo && has(ITEMS, lo.item)) out.item = lo.item;
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

export const FLAGS = { SMOKE: 1, FIRE: 2, BLOW: 4, SPIN: 8, SLIP: 16, SLIDE: 32, REVERSE: 64, CROUCH: 128, DASH: 256, SLEEP: 512 };
export const SLIP_TIME = 1.7;
// overdrive rig killstreak: in the rig, blocking, winding up a punch, crouched for a leap. the server only believes
// them from someone it saw activate the streak (the numbers are RIG in shared/rig.js)
Object.assign(FLAGS, { RIG: 16384, RIG_BLOCK: 32768, RIG_CHARGE: 65536, RIG_LEAP: 131072 });
// not guns: what the rig's hits are called in the kill feed (its missiles fly as server projectiles)
Object.assign(WEAPONS, {
  rigpunch: { slot: null, kind: 'rig', name: 'Rocket Punch', color: '#ff2a6d' },
  rigslam: { slot: null, kind: 'rig', name: 'Wall Slam', color: '#ffb000' },
  rigquake: { slot: null, kind: 'rig', name: 'Crater', color: '#3ee6ff' },
  rigmissile: { slot: 'hidden', kind: 'proj', name: 'Rig Missiles', color: '#ff6a3d', grav: 0, r: 0.22, life: 5 },
});
export const SLEEP_TIME = 4; // sleep arrow: knocked flat on the floor this long (s)
export const HOOK = { range: 90, pull: 42, tug: 16 };
// katana right click. times in seconds: the window, its perfect start, the cooldown after it, and server slack for
// hit reports that arrive a bit late. arc = full cone (degrees) around where you look that counts as "the front":
// 70 either side covers the whole screen at the default fov (95 tall is ~125 across at 16:9) plus a bit for the
// server's yaw being up to a snapshot old. shove / shoveUp / stagger = what a parried melee attacker gets.
export const PARRY = { win: 0.35, perfect: 0.15, cd: 0.8, slack: 0.05, arc: 140, shove: 14, shoveUp: 5, stagger: 0.55 };
FLAGS.SUCK = 2048; // a shredder is running: everyone else sees the suction and hears the motor

// your 3 killstreaks, cheapest first (keys 5 / 6 / 7)
export function validStreaks(list) {
  const ok = Array.isArray(list) ? [...new Set(list.filter((id) => has(STREAKS, id)))] : [];
  const out = ok.slice(0, 3);
  for (const id of DEFAULT_LOADOUT.streaks) if (out.length < 3 && !out.includes(id)) out.push(id);
  for (const id of Object.keys(STREAKS)) if (out.length < 3 && !out.includes(id)) out.push(id);
  return out.sort((a, b) => STREAKS[a].kills - STREAKS[b].kills);
}

// ------------------------------------------------------------ wrecking ball killstreak
// the client rolls the ball; the server judges rams + slams with these same numbers.
FLAGS.BALL = 4096; // set in your snapshots while you're the ball (the server only believes it if you activated one)
// not a gun, just the name + colour rams and slams show in the kill feed
WEAPONS.wreck = { slot: null, kind: 'wreck', name: 'Wrecking Ball', color: '#b8c4d0' };
// ram: see ramDmg. slam: sized by how high you were when you started it, from a hop (h0 m: slamDmg[0] at the centre,
// slamR[0] m across the floor) up to h1 m or more (slamDmg[1], slamR[1]).
export const WRECK = {
  r: 1.1, ramMin: 6, ramMul: 2, ramKnee: 26, ramMul2: 4.5, ramMax: 120, ramCd: 600, ramKb: 8, ramKbMul: 0.9, ramKbMax: 60, ramUp: 6, ramReach: 0.75,
  h0: 0.5, h1: 18, slamDmg: [30, 150], slamR: [4, 10], slamKb: [12, 34], slamUp: [7, 20], slamCd: 1.5, slamV: 62,
};
// what ramming someone at sp m/s does: 2 x speed up to rolling top speed (26 m/s = 52), then it climbs much faster so
// a chain swing or a big drop hurts a lot more than just rolling (about 75 at 31 m/s, 97 at 36, 120 from 41)
export function ramDmg(sp) {
  const W = WRECK;
  return sp < W.ramMin ? 0 : Math.min(W.ramMax, sp <= W.ramKnee ? W.ramMul * sp : W.ramMul * W.ramKnee + (sp - W.ramKnee) * W.ramMul2);
}
// how big a slam from h metres up is (k: 0 = off a hop, 1 = from 18 m up or more)
export function slamSize(h) {
  const k = Math.max(0, Math.min(1, (h - WRECK.h0) / (WRECK.h1 - WRECK.h0)));
  const at = (a) => a[0] + (a[1] - a[0]) * k;
  return { k, dmg: at(WRECK.slamDmg), r: at(WRECK.slamR), kb: at(WRECK.slamKb), up: at(WRECK.slamUp) };
}

// ------------------------------------------------------------ new gear: instant camera, pop quiz, night vision goggles
// (the Big Laser Pointer is up with the primaries). the server's half is server/gear.js
FLAGS.NV = 8192; // night vision goggles on: everyone sees them on your face, lenses glowing
FLAGS.CHARGE = 16384; // charging the Big Laser Pointer: everyone sees the tip glow and hears the whine
// kill-feed tags (not guns): telefrags + frames, and failed quizzes
WEAPONS.camera = { slot: null, kind: 'photo', name: 'Instant Camera', color: '#c9a7ff' };
WEAPONS.quiz = { slot: null, kind: 'quiz', name: 'Pop Quiz', color: '#7fffd4' };
WEAPONS.nvg = { slot: null, kind: 'flash', name: 'Night Vision Goggles', color: '#3dff8a' };
// G: the first press snaps a photo (the server keeps where you stood + which way you faced), the next press prints it:
// a frame stands up `at` m in front of you for `life` s. walk into it (anyone can) and you come out where the photo was
// taken, facing the same way. w x h = the frame's opening, cd = s before the same person can use a frame again,
// frag = m: whoever is standing on the spot when you arrive gets telefragged
export const PHOTO = { at: 1.9, life: 20, w: 1.8, h: 2.1, depth: 0.55, cd: 1.6, frag: 0.9, drop: 3, res: 256 };
ITEMS.camera = { name: 'Instant Camera', desc: 'G snaps a photo of what\'s in front of you. G again prints it as a frame you can walk into: it puts you back where you took it. Anyone can walk through, so photograph somewhere nasty.', charges: 1, recharge: 25, color: '#c9a7ff' };
// a hit freezes them with a maths question for `time` s (4 answers, keys 1-4). wrong or too slow: dead (your kill).
// right: +heal HP, nothing hurts them for `invuln` s and they run `fast` x speed for `fastT` s. `safe` s after a quiz
// before the same person can get another one. bots get it right `bot[diff]` of the time, after `botT` s
export const QUIZ = { time: 6, invuln: 2.5, heal: 25, fast: 1.25, fastT: 4, safe: 10, bot: { easy: 0.5, normal: 0.7, hard: 0.85 }, botT: [1.3, 4.2] };
ITEMS.quiz = { name: 'Pop Quiz', desc: 'A calculator you throw. Whoever it hits freezes and gets a maths question: wrong or too slow and they die, right and they get a gold star, some HP and a few seconds nothing can hurt them.', charges: 1, recharge: 22, color: '#7fffd4', proj: 'calc' };
// G puts them on / takes them off (free). while they're on, H (FLASH) spends a charge: everyone you can see within range m
// and cone rad of your crosshair is blinded for dur[0] (looking away) .. dur[1] s (looking at you). wearing goggles
// yourself makes any flash last nvMul x longer
export const NVG = { range: 34, cone: 0.62, dur: [0.6, 3.2], nvMul: 2, toggle: 0.35 };
ITEMS.nvg = { name: 'Night Vision Goggles', desc: 'G puts them on: the dark goes green and people glow. While they\'re on, middle click flashes everyone you can see. Flashes blind you twice as long while you wear them.', charges: 2, recharge: 14, color: '#3dff8a' };
