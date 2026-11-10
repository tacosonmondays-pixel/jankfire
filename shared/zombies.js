// Zombies (co-op wave survival): the rules and numbers, the shop, and what you're looking at when you hold F.
// Shared so the server (which runs the mode) and the client (prompts, prices, your ammo) always agree.
import './zmschool.js'; // (registers the school map: it only needs shared/map.js)

export const ZM = {
  start: 500, hit: 10, kill: 60, bonus: 100, // credits: start with 500, +10 a hit, +60 a kill, +100 for a headshot or melee kill
  hitCap: 10, hitGap: 180, // a zombie only pays for its first 10 hits, and you bank at most one per 180 ms from it (flame ticks)
  first: 6000, rest: 10000, // ms before round 1 / between rounds
  hold: 0.3, power: 1, revive: 3, bleed: 30, // seconds: hold F to buy / to throw the power switch / to revive; how long a downed friend lasts
  regenAfter: 4, regen: 25, // 4 s without a hit and you heal 25 HP/s
  swipe: 15, swipeCd: 1100, windup: 350, reach: 1.5, reachHit: 2.2, reachUp: 2.6, // the claws (ms, metres). reachUp: you can't hide on a crate
  crate: 950, spin: 3600, offer: 8000, // the mystery crate: price, spin, how long the weapon waits for you (ms)
  cola: 2500, // Jank Cola (needs the power on): zombies hit you half as hard and you heal faster. gone if you go down
  guns: 2, startGuns: ['revolver'], startMelee: 'knife',
};

// zombies in round r, solo (friends add 75% each)
export function zmCount(r, players = 1) {
  const solo = r <= 5 ? [6, 9, 13, 18, 24][r - 1] : 24 + (r - 5) * 3;
  return Math.round(solo * (1 + 0.75 * (Math.min(4, Math.max(1, players)) - 1)));
}
// their HP: one revolver shot in round 1, +22 a round to round 9, then +9% a round
export function zmHp(r) { return r <= 9 ? 40 + 22 * (r - 1) : Math.round(216 * Math.pow(1.09, r - 9)); }
export function zmMaxAlive(players = 1) { return ZM.maxAlive || Math.min(24, 14 + 6 * (Math.max(1, players) - 1)); } // (ZM.maxAlive: a test knob)
export function zmGap(r, players = 1) { return Math.max(450, 2000 - 150 * (r - 1)) * (players > 1 ? 0.75 : 1); } // ms between spawns
// how one moves (roll = 0..1): shamblers early, runners from round 4, sprinters from round 9
export function zmGait(r, roll, jitter = 0.5) {
  const run = Math.min(1, Math.max(0, (r - 3) * 0.22)), sprint = r >= 9 ? Math.min(0.6, 0.2 + (r - 9) * 0.1) : 0;
  if (roll < sprint) return { speed: 9.2, kind: 2 };
  if (roll < run) return { speed: 6.8 + jitter, kind: 1 };
  return { speed: 2.6 + jitter * 0.9, kind: 0 };
}

// every round you get with a gun (the mag plus the spares). melee, the cigarette and the leaf blower don't use ammo
export const ZM_AMMO = { revolver: 54, smg: 315, ar: 300, redline: 280, shotgun: 54, sniper: 40, minigun: 750, marbles: 22, chicken: 24, bowling: 20, banana: 60, snowball: 50, bow: 40, cards: 50, burst: 300, lmg: 500, dmr: 60, lever: 64, autoshot: 80, pistol: 84, akimbo: 280, sawnoff: 30 };
export const zmAmmo = (id) => ZM_AMMO[id] ?? null;
export const zmAmmoPrice = (price) => Math.ceil(price / 20) * 10; // a refill is half the gun's price

// the mystery crate (weights): mostly good stuff, a couple of jokes
export const ZM_CRATE = { minigun: 6, chicken: 6, marbles: 6, redline: 6, bowling: 5, snowball: 5, cig: 4, cards: 4, sniper: 3, ar: 3, smg: 3, shotgun: 3, bow: 3, banana: 3, slapper: 2, blower: 2, burst: 4, lmg: 5, dmr: 3, lever: 4, autoshot: 5 }; // (Plan B from the crate is a joke)
Object.assign(ZM_CRATE, { nailgun: 5, tennis: 4, cart: 4 }); // the new primaries: pin zombies to walls, bank balls round corners, bowl carts through the horde
Object.assign(ZM_CRATE, { akimbo: 5, sawnoff: 5, pistol: 1 }); // the plain sidearms
Object.assign(ZM_CRATE, { water: 3, taser: 3, remote: 2 }); // the new secondaries: soak them, tase the whole wet horde, rewind the fast ones
export function zmPick(owned = [], rnd = Math.random) {
  const pool = Object.entries(ZM_CRATE).filter(([id]) => !owned.includes(id));
  let t = rnd() * pool.reduce((a, [, w]) => a + w, 0);
  for (const [id, w] of pool) if ((t -= w) <= 0) return id;
  return pool.length ? pool[pool.length - 1][0] : 'minigun';
}

// the areas you can get to: walk out from the start through the open doors (only these spawn zombies or sell you things)
export function zmOpenAreas(Z, open) {
  const out = new Set([Z.start]);
  for (let grew = true; grew;) {
    grew = false;
    Z.doors.forEach((d, i) => { if (open[i] && out.has(d.a) !== out.has(d.b)) { out.add(d.a); out.add(d.b); grew = true; } });
  }
  return out;
}
// which area of the map a position is in (null: outside, e.g. in an alley)
export function zmAreaAt(Z, p) {
  for (const a of Z.areas) if (p[0] >= a.r[0] && p[0] <= a.r[2] && p[2] >= a.r[1] && p[2] <= a.r[3] && (!a.y || (p[1] >= a.y[0] - 0.3 && p[1] < a.y[1]))) return a.id; // (a.y: which floor, on maps with an upstairs)
  return null;
}

// what F does from eye e looking along d (unit): a closed door, a wall gun, the crate, the power switch, the cola machine
// or a downed friend. Z = the map's zm block. st = { open: [bool per door], power, down: [[id, x, y, z]], me }.
// slack: the server's copy of your aim is a few ms old, so it forgives a bit more than the prompt does.
export function zmTarget(Z, st, e, d, slack = 0) {
  let best = null, bs = Infinity;
  const take = (t, score) => { if (score < bs) { bs = score; best = t; } };
  const to = (p) => { const v = [p[0] - e[0], p[1] - e[1], p[2] - e[2]], l = Math.hypot(v[0], v[1], v[2]) || 1e-6; return [v[0] / l, v[1] / l, v[2] / l, l]; };
  const facing = (u, min) => u[0] * d[0] + u[1] * d[1] + u[2] * d[2] >= min - slack * 0.5;
  const front = (at, n) => (e[0] - at[0]) * n[0] + (e[2] - at[2]) * n[2] > 0.05; // no buying through the wall
  for (const dn of st.down || []) { // a downed friend: just stand over them
    if (dn[0] === st.me) continue;
    const h = Math.hypot(dn[1] - e[0], dn[3] - e[2]);
    if (h <= 2.2 + slack && Math.abs(dn[2] + 1.6 - e[1]) < 2.2) take({ k: 'r' + dn[0], kind: 'revive', id: dn[0] }, h - 3);
  }
  Z.doors.forEach((dr, i) => {
    if (st.open && st.open[i]) return;
    const u = to([0, 1, 2].map((k) => Math.max(dr.box.min[k], Math.min(dr.box.max[k], e[k])))); // nearest point of the shutter
    if (u[3] > 2.4 + slack || (u[3] > 0.8 && !facing(u, 0.4))) return;
    take({ k: 'd' + i, kind: 'door', i, price: dr.price }, u[3]);
  });
  Z.buys.forEach((b, i) => {
    const u = to(b.at);
    if (u[3] <= 2.3 + slack && facing(u, 0.7) && front(b.at, b.n)) take({ k: 'b' + i, kind: 'buy', i, w: b.w, price: b.price }, u[3]);
  });
  if (Z.crate) { const u = to([Z.crate.at[0], Z.crate.at[1] + 0.7, Z.crate.at[2]]); if (u[3] <= 2.6 + slack && facing(u, 0.5)) take({ k: 'crate', kind: 'crate', price: ZM.crate }, u[3]); }
  if (Z.power && !st.power) { const u = to(Z.power.at); if (u[3] <= 2.3 + slack && facing(u, 0.6) && front(Z.power.at, Z.power.n)) take({ k: 'power', kind: 'power' }, u[3]); }
  if (Z.cola) { const at = [Z.cola.at[0], Z.cola.at[1] + 1.3, Z.cola.at[2]], u = to(at); if (u[3] <= 2.4 + slack && facing(u, 0.55) && front(at, Z.cola.n)) take({ k: 'cola', kind: 'cola', price: ZM.cola }, u[3]); }
  return best;
}

// ---------------------------------------------------------------- claws, boards, drops, the cheat machine, loadouts
// claw damage: 15 in round 1 (7 hits from full HP, it used to be 40 = 3 hits), +1 a round, never more than 34.
// after a claw lands you get iframe ms where no other claw can (a crowd can't melt you in one frame)
Object.assign(ZM, { swipeRamp: 1, swipeMax: 34, iframe: 450 });
export function zmClaw(r) { return ZM.swipe > 0 ? Math.min(ZM.swipeMax, ZM.swipe + ZM.swipeRamp * Math.max(0, r - 1)) : 0; }

// barricades: planks nailed over every window. zombies tear them off one at a time before they can climb in;
// hold F at one to nail a plank back (one per board ms), +boardPay each, paid for the first boardCap planks a round
Object.assign(ZM, { planks: 6, tear: 1300, tearRun: 850, board: 600, boardPay: 10, boardCap: 20 });

// drops: a zombie you kill sometimes leaves a spinning power-up anyone can walk into (dropCap a round, gone after dropLife ms)
Object.assign(ZM, { dropChance: 0.045, dropCap: 4, dropLife: 25000, dropBlink: 5000, dropReach: 1.7 });
// the game's own killstreaks go off the moment you grab them, plus three that only exist in here
export const ZM_DROPS = {
  tipjar: { name: 'TIP JAR', desc: '+400 credits for everyone', color: '#7dff4f', w: 3 },
  restock: { name: 'RESTOCK', desc: 'everyone gets full ammo', color: '#4fd8ff', w: 3 },
  aisle5: { name: 'CLEAN-UP ON AISLE 5', desc: 'every zombie in the mall pops', color: '#ff4fd8', w: 2 },
  moonboots: { streak: true, w: 1 }, chickenstrike: { streak: true, w: 1.2 }, scythe: { streak: true, w: 1 }, overdrive: { streak: true, w: 0.6 },
  spinbot: { streak: true, w: 1 }, wreckingball: { streak: true, w: 0.8 }, satellite: { streak: true, w: 0.6 }, giantduck: { streak: true, w: 1 },
};
export function zmDropPick(rnd = Math.random) {
  const all = Object.entries(ZM_DROPS);
  let t = rnd() * all.reduce((a, [, d]) => a + d.w, 0);
  for (const [id, d] of all) if ((t -= d.w) <= 0) return id;
  return 'tipjar';
}

// the Cheat Machine (needs the power on): pay, it rolls one of these for a few seconds. team ones are for everyone,
// the rest only for whoever paid. the price goes up every time it's used in a round; it needs machCd ms to cool down
Object.assign(ZM, { mach: 1250, machStep: 500, machSpin: 2600, machCd: 15000 });
export const ZM_MODS = {
  oneshot: { name: 'ONE AND DONE', desc: 'every hit kills', dur: 15, team: true, color: '#ff3030', ico: '1' },
  taxfraud: { name: 'TAX FRAUD', desc: 'double credits for everything', dur: 30, team: true, color: '#7dff4f', ico: '$' },
  bottomless: { name: 'BOTTOMLESS MAG', desc: 'no reloads, no running out', dur: 20, team: false, color: '#ffe14d', ico: '∞' },
  zoomies: { name: 'ZOOMIES', desc: 'you run 40% faster', dur: 25, team: false, color: '#4fd8ff', ico: '»' },
  brainfreeze: { name: 'BRAIN FREEZE', desc: 'zombies move like it\'s a monday', dur: 15, team: true, color: '#bfefff', ico: '❄' },
  bighead: { name: 'BIG HEAD MODE', desc: 'zombie heads are huge. headshots for everyone', dur: 25, team: true, color: '#ffb347', ico: '☺' },
  vampire: { name: 'VAMPIRE TEETH', desc: 'your hits heal you', dur: 20, team: false, color: '#c01040', ico: 'V' },
  bouncy: { name: 'BOUNCY CASTLE', desc: 'every hit sends them flying', dur: 20, team: true, color: '#ff4fd8', ico: '↑' },
};
export const zmMachPrice = (uses) => ZM.mach + ZM.machStep * uses;
export function zmModPick(last, rnd = Math.random) { const ids = Object.keys(ZM_MODS).filter((k) => k !== last); return ids[(rnd() * ids.length) | 0]; }

// your zombies loadout (customize > loadout > ZOMBIES): the pistol you start with, the item you bring, one passive.
// the start pistols trade damage for ammo so none of them is just better
export const ZM_PISTOLS = {
  revolver: { ammo: 54, tip: 'big hits, few bullets. the classic' },
  pistol: { ammo: 96, tip: 'Plan B. smaller hits, way more spare mags' },
  akimbo: { ammo: 240, tip: 'two little guns, a wall of bullets, a light snack each' },
  sawnoff: { ammo: 30, tip: 'deletes whatever is in your face. 30 shells. good luck' },
  water: { ammo: null, tip: 'never runs out, barely hurts. soak them, then zap them' },
};
export const ZM_PASSIVES = {
  quickhands: { name: 'Quick Hands', desc: 'Revive friends twice as fast. You have done this before.', color: '#7dff4f' },
  trustfund: { name: 'Trust Fund', desc: 'Start with +500 credits. Daddy paid.', color: '#ffe14d' },
  stubborn: { name: 'Stubborn', desc: 'Bleed out in 60 s instead of 30. Too angry to die.', color: '#ff3030' },
  handyman: { name: 'Handyman', desc: 'Nail planks twice as fast and get +50% for each one.', color: '#c08040' },
  rabbitfoot: { name: 'Lucky Foot', desc: 'Zombies you kill drop power-ups twice as often. Not lucky for the rabbit.', color: '#ff4fd8' },
  thickskin: { name: 'Thick Skin', desc: 'Claws hurt 15% less. Moisturise.', color: '#ffb347' },
  coupons: { name: 'Coupon Book', desc: 'Everything you buy costs 10% less. Doors, guns, the crate, the cola, the machine.', color: '#4fd8ff' },
  secondwind: { name: 'Second Wind', desc: 'You start healing after 2 s instead of 4.', color: '#bfefff' },
};
export const ZM_LOADOUT = { pistol: 'revolver', item: 'frag', perk: 'trustfund' };
// what the server and the customize screen accept (anything else falls back to the defaults). items: shared/weapons.js
export function zmValidLoadout(lo, items) {
  const o = lo && typeof lo === 'object' ? lo : {}, ok = (t, k) => typeof k === 'string' && Object.hasOwn(t, k);
  return { pistol: ok(ZM_PISTOLS, o.pistol) ? o.pistol : ZM_LOADOUT.pistol, item: items && ok(items, o.item) ? o.item : ZM_LOADOUT.item, perk: ok(ZM_PASSIVES, o.perk) ? o.perk : ZM_LOADOUT.perk };
}
// what F does at a window: nail a plank back (from inside, near the boards). null when it's full or you're too far
export function zmBoardTarget(Z, planks, e, d, slack = 0) {
  let best = null, bs = Infinity;
  (Z.windows || []).forEach((w, i) => {
    if (!planks || planks[i] >= ZM.planks) return;
    const at = [w.at[0], w.at[1], w.at[2]], v = [at[0] - e[0], at[1] - e[1], at[2] - e[2]], l = Math.hypot(v[0], v[1], v[2]) || 1e-6;
    if (l > 2.6 + slack) return;
    if ((e[0] - at[0]) * w.n[0] + (e[2] - at[2]) * w.n[2] < 0.1) return; // only from inside
    if ((v[0] * d[0] + v[1] * d[1] + v[2] * d[2]) / l < 0.45 - slack * 0.5) return;
    if (l < bs) { bs = l; best = { k: 'w' + i, kind: 'board', i }; }
  });
  return best;
}
