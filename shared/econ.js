// Plant & Defuse economy: credits, prices, armor, ammo. Shared by the server (the real rules) and the client (buy menu, HUD).
// Data-driven: every weapon whose slot is a loadout slot (WEAPONS[id].slot in SLOTS) and every ITEMS entry can be bought.
// An id without a row here uses the fallback rules (by slot / by kind), so new weapons and items show up on their own.
import { WEAPONS, ITEMS, SLOTS } from './weapons.js';

export const ECON = {
  games: ['bomb'], // game types that run the economy (Online + Bots rooms, teams on)
  start: 800, max: 9000, // credits at the start of each half, and the most you can hold
  buyTime: 15, // seconds of buy phase at the start of every round (the round clock starts after it)
  // round payouts. winners by how the round ended; losers climb the ladder with every loss in a row (a win resets it)
  win: { elim: 2600, time: 2600, defused: 2900, exploded: 2900 },
  loss: [1300, 1750, 2200, 2650], // 1st, 2nd, 3rd, 4th+ loss in a row
  plant: 300, // to the planter, when the plant completes
  plantTeam: 600, // to every attacker when they lose a round in which the bomb was planted
  defuse: 300, // to the defuser
  timeSurvivorBonus: false, // attackers still alive when time runs out (no plant) get no loss bonus
  refill: 0.25, // buying a weapon you already hold refills its ammo for this fraction of its price
  kitDefuse: 2.5, // seconds to defuse with a kit (BOMB.defuse without)
  defaultSecondary: 'revolver', defaultMelee: 'bread', // what everyone has at the start of a half (and after dying)
  grapple: false, streaks: false, // no grappling hook and no killstreaks in this mode
  // spawn barriers: each side's zone is the box around its team spawns, this much bigger (m). no team spawns: a box this
  // big around each player's own spawn. slack: how far past the edge the server lets you be before it puts you back
  zonePad: 4, personalZone: 3.5, zoneSlack: 0.75, zoneBelow: 2, zoneAbove: 10,
  // dropped gear on the floor
  pickR: 2.2, // manual pick-up / swap reach (m, from your feet), plus a little for speed
  autoR: 1.3, // walking over something picks it up when the slot is free
  dropNoPick: 1200, // ms before you auto-pick up what you just dropped
  maxDrops: 48, // oldest goes first
  joinerMin: 800, // a mid-match joiner gets their team's average credits, at least this
};

// armor. absorb: the share of a hit the armor takes (body hits; head hits only with the helmet; explosions)
// wear: armor points lost per point of damage it takes. pen (per weapon below): how much of the armor's share a weapon ignores
export const ARMOR = { max: 100, body: 0.45, head: 0.4, blast: 0.35, wear: 0.6 };
export const BLAST = ['chicken', 'frag', 'duck', 'bomb', 'tbag']; // damage of these ids counts as an explosion
export const GEAR = {
  vest: { name: 'Padded Vest', desc: '100 armor. Soaks up a share of body hits and blasts.', price: 650 },
  helm: { name: 'Vest + Bucket', desc: 'The vest plus a bucket on your head: headshots hurt less. (Not sniper headshots.)', price: 350 },
  kit: { name: 'Defuse Pliers', desc: `Defuse in ${ECON.kitDefuse} s instead of 5. Defenders only. Drops when you die.`, price: 400, def: true },
};

// per weapon: price (null = can't be bought), kill reward, armor pen, ammo (mags = spare magazines for guns with a magazine,
// shots = total uses for weapons without one). no mags / shots = unlimited (melee, cones, the reverse card)
export const PRICES = {
  // primary
  ar: { price: 3000, kill: 250, pen: 0.3, mags: 3 },
  smg: { price: 1250, kill: 500, pen: 0.15, mags: 3 },
  redline: { price: 2500, kill: 250, pen: 0.25, mags: 3 },
  shotgun: { price: 1100, kill: 750, pen: 0, mags: 4 },
  minigun: { price: 4200, kill: 150, pen: 0.1, mags: 1 },
  sniper: { price: 4750, kill: 100, pen: 0.8, mags: 3 },
  chicken: { price: 3200, kill: 200, shots: 3 }, // competitive nerfs: fewer uses per buy (was 6)
  bowling: { price: 2100, kill: 450, shots: 4 }, // was 8
  bow: { price: 1650, kill: 600, pen: 0.5, shots: 10 }, // was 24
  banana: { price: 1400, kill: 650, shots: 18 }, // was 45
  laser: { price: 3400, kill: 250, shots: 6 }, // the Big Laser Pointer: 6 beams a buy (was free-firing, the 2000 default price)
  // secondary
  revolver: { price: 250, kill: 250, pen: 0.5, mags: 4 },
  marbles: { price: 900, kill: 400, pen: 0, mags: 2 }, // competitive: 2+4 (was 2+10)
  cig: { price: 450, kill: 900 },
  blower: { price: 600, kill: 1000 },
  cards: { price: 750, kill: 650, shots: 12 }, // was 40
  popper: { price: 350, kill: 1200 },
  reverse: { price: 700, kill: 1500 },
  snowball: { price: 400, kill: 900, shots: 10 }, // was 36
  bloodcross: { price: 900, kill: 450, shots: 8 }, // 8 bolts a buy (was unlimited at the 600 default)
  // melee
  bread: { price: null, kill: 1000 }, // the default melee: free, never sold, never dropped
  slipper: { price: 450, kill: 850, shots: 4 }, // 4 throws a buy (was unlimited: it comes back)
  katana: { price: 950, kill: 750 },
  knife: { price: 350, kill: 1100, pen: 0.5 },
  slapper: { price: 300, kill: 1050 },
  spoon: { price: null, kill: 600, pen: 1 }, // mode-only now (a knife skin): never sold
};
// kill rewards for things that aren't loadout weapons (the kill's w, or for void / cough kills the weapon that sent them)
export const OTHER_KILL = { frag: 300, duck: 350, smokegren: 300, tbag: 1500, bomb: 0, scythe: 0, scythe_rifle: 0, hook: 300 };
// items (G): price per charge, limit = most charges you can carry and buy in one round
export const ITEM_PRICES = {
  frag: { price: 300, limit: 2 },
  medkit: { price: 400, limit: 1 },
  bubble: { price: 650, limit: 1 },
  duck: { price: 500, limit: 1 },
  smoke: { price: 250, limit: 2 },
};
// fallbacks for ids with no row above
export const FALLBACK = {
  price: { primary: 2000, secondary: 600, melee: 500 },
  kill: { primary: 300, secondary: 450, melee: 1000, other: 300 },
  mags: 3, // spare magazines for any gun with a magazine
  shots: (cd) => Math.max(6, Math.min(60, Math.round(6 / Math.max(0.05, cd || 0.5)))), // weapons with a cooldown that fire something
  item: { price: 400, limit: 1 },
};

const has = (T, k) => typeof k === 'string' && Object.hasOwn(T, k);
const row = (id) => (has(PRICES, id) ? PRICES[id] : null);
// can this weapon be bought / held in this mode at all? (loadout slots only: no streak, hidden or item weapons)
export function econWeapon(id) { return has(WEAPONS, id) && SLOTS.includes(WEAPONS[id].slot); }
export function weaponPrice(id) {
  if (!econWeapon(id)) return null;
  const r = row(id);
  if (r && Object.hasOwn(r, 'price')) return r.price;
  return id === ECON.defaultMelee ? null : FALLBACK.price[WEAPONS[id].slot] ?? null;
}
export function refillPrice(id) {
  const p = weaponPrice(id);
  return p == null ? null : Math.max(50, Math.ceil((p * ECON.refill) / 50) * 50);
}
export function killReward(id) {
  const r = row(id);
  if (r && r.kill != null) return r.kill;
  if (has(OTHER_KILL, id)) return OTHER_KILL[id];
  if (has(WEAPONS, id) && SLOTS.includes(WEAPONS[id].slot)) return FALLBACK.kill[WEAPONS[id].slot];
  return FALLBACK.kill.other;
}
export function armorPen(id) { const r = row(id); return r && r.pen != null ? Math.max(0, Math.min(1, r.pen)) : 0; }
// the ammo a fresh one comes with: { mag, res, clip } (clip: has a magazine to reload; false: res is 0 and mag is the
// total shots), or null for unlimited
export function ammoSpec(id) {
  if (!econWeapon(id)) return null;
  const w = WEAPONS[id], r = row(id);
  if (w.mag) return { mag: w.mag, res: w.mag * (r && r.mags != null ? r.mags : FALLBACK.mags), clip: true };
  if (r) return r.shots ? { mag: r.shots, res: 0, clip: false } : null;
  // unknown weapon without a magazine: things that fire something get a shot count, melee / cones / other kinds are unlimited
  if ((w.kind === 'proj' || w.kind === 'bow') && w.slot !== 'melee') return { mag: FALLBACK.shots(w.cd), res: 0, clip: false };
  return null;
}
export function itemSpec(id) {
  if (!has(ITEMS, id)) return null;
  const r = has(ITEM_PRICES, id) ? ITEM_PRICES[id] : { price: FALLBACK.item.price, limit: Math.max(1, Math.min(2, ITEMS[id].charges || FALLBACK.item.limit)) };
  return { price: r.price, limit: r.limit };
}
// everything in the buy menu, in menu order: { k: 'w' | 'i' | 'g', id, slot, price, name }
export function buyList() {
  const out = [];
  for (const slot of SLOTS) for (const id of Object.keys(WEAPONS)) {
    if (WEAPONS[id].slot !== slot || WEAPONS[id].modeOnly) continue; // the spoon is mode-only
    const price = weaponPrice(id);
    if (price != null) out.push({ k: 'w', id, slot, price, name: WEAPONS[id].name, kill: killReward(id), ammo: ammoSpec(id) });
  }
  for (const id of Object.keys(ITEMS)) { const s = itemSpec(id); out.push({ k: 'i', id, slot: 'item', price: s.price, limit: s.limit, name: ITEMS[id].name }); }
  for (const id of Object.keys(GEAR)) out.push({ k: 'g', id, slot: 'gear', price: GEAR[id].price, name: GEAR[id].name });
  return out;
}
// the price of a gear id for someone with this armor / helmet / kit right now (null = nothing to buy)
export function gearPrice(id, ar, hm, kit) {
  if (id === 'vest') return ar >= ARMOR.max ? null : GEAR.vest.price;
  if (id === 'helm') {
    if (hm && ar >= ARMOR.max) return null;
    return (ar >= ARMOR.max ? 0 : GEAR.vest.price) + (hm ? 0 : GEAR.helm.price);
  }
  if (id === 'kit') return kit ? null : GEAR.kit.price;
  return null;
}
// the new secondaries + the speed trap (shared/weapons.js): what they cost in Plant & Defuse
Object.assign(PRICES, {
  water: { price: 300, kill: 950, pen: 0, mags: 3 },
  taser: { price: 550, kill: 1000, shots: 8 },
  remote: { price: 700, kill: 1100, shots: 14 },
});
ITEM_PRICES.radar = { price: 350, limit: 2 };
