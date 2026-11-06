// Zombies (co-op wave survival): the rules and numbers, the shop, and what you're looking at when you hold F.
// Shared so the server (which runs the mode) and the client (prompts, prices, your ammo) always agree.

export const ZM = {
  start: 500, hit: 10, kill: 60, bonus: 100, // credits: start with 500, +10 a hit, +60 a kill, +100 for a headshot or melee kill
  hitCap: 10, hitGap: 180, // a zombie only pays for its first 10 hits, and you bank at most one per 180 ms from it (flame ticks)
  first: 6000, rest: 10000, // ms before round 1 / between rounds
  hold: 0.3, power: 1, revive: 3, bleed: 30, // seconds: hold F to buy / to throw the power switch / to revive; how long a downed friend lasts
  regenAfter: 4, regen: 25, // 4 s without a hit and you heal 25 HP/s
  swipe: 40, swipeCd: 1100, windup: 350, reach: 1.5, reachHit: 2.2, reachUp: 2.6, // the claws (ms, metres). reachUp: you can't hide on a crate
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
export function zmMaxAlive(players = 1) { return Math.min(24, 14 + 6 * (Math.max(1, players) - 1)); }
export function zmGap(r, players = 1) { return Math.max(450, 2000 - 150 * (r - 1)) * (players > 1 ? 0.75 : 1); } // ms between spawns
// how one moves (roll = 0..1): shamblers early, runners from round 4, sprinters from round 9
export function zmGait(r, roll, jitter = 0.5) {
  const run = Math.min(1, Math.max(0, (r - 3) * 0.22)), sprint = r >= 9 ? Math.min(0.6, 0.2 + (r - 9) * 0.1) : 0;
  if (roll < sprint) return { speed: 9.2, kind: 2 };
  if (roll < run) return { speed: 6.8 + jitter, kind: 1 };
  return { speed: 2.6 + jitter * 0.9, kind: 0 };
}

// every round you get with a gun (the mag plus the spares). melee, the cigarette and the leaf blower don't use ammo
export const ZM_AMMO = { revolver: 54, smg: 315, ar: 300, redline: 280, shotgun: 54, sniper: 40, minigun: 750, marbles: 22, chicken: 24, bowling: 20, banana: 60, snowball: 50, bow: 40, cards: 50, burst: 300, lmg: 500, dmr: 60, lever: 64, autoshot: 80 };
export const zmAmmo = (id) => ZM_AMMO[id] ?? null;
export const zmAmmoPrice = (price) => Math.ceil(price / 20) * 10; // a refill is half the gun's price

// the mystery crate (weights): mostly good stuff, a couple of jokes
export const ZM_CRATE = { minigun: 6, chicken: 6, marbles: 6, redline: 6, bowling: 5, snowball: 5, cig: 4, cards: 4, sniper: 3, ar: 3, smg: 3, shotgun: 3, bow: 3, banana: 3, spoon: 3, slapper: 2, blower: 2, burst: 4, lmg: 5, dmr: 3, lever: 4, autoshot: 5 };
Object.assign(ZM_CRATE, { nailgun: 5, tennis: 4, cart: 4 }); // the new primaries: pin zombies to walls, bank balls round corners, bowl carts through the horde
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
  for (const a of Z.areas) if (p[0] >= a.r[0] && p[0] <= a.r[2] && p[2] >= a.r[1] && p[2] <= a.r[3]) return a.id;
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
  if (Z.crate) { const u = to([Z.crate.at[0], 0.7, Z.crate.at[2]]); if (u[3] <= 2.6 + slack && facing(u, 0.5)) take({ k: 'crate', kind: 'crate', price: ZM.crate }, u[3]); }
  if (Z.power && !st.power) { const u = to(Z.power.at); if (u[3] <= 2.3 + slack && facing(u, 0.6) && front(Z.power.at, Z.power.n)) take({ k: 'power', kind: 'power' }, u[3]); }
  if (Z.cola) { const at = [Z.cola.at[0], 1.3, Z.cola.at[2]], u = to(at); if (u[3] <= 2.4 + slack && facing(u, 0.55) && front(at, Z.cola.n)) take({ k: 'cola', kind: 'cola', price: ZM.cola }, u[3]); }
  return best;
}
