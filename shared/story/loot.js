// OVERDUE loot (WP4): rarity rolls Common -> ☺ PREMIUM, stat ranges per rarity, brands, modifiers, named legendaries
// and loot tables. the DATA is the writer's (shared/story/content/loot.js: BRANDS, MODIFIERS, LEGENDARIES, LOOT_TABLES);
// this is the engine. pure: no node, no dom. no durability, ever.
//
// a rolled weapon item: { b (base weapon), r (rarity), s (seed; 0 = a stock item, no stat roll), br? (brand), m? ([modifier ids]), lg? (legendary id) }
// stats are never stored: statsOf(item) rebuilds them from the seed, so client, worker and server agree and a save
// can't carry made-up numbers.
//   rollTable(id, rand, ctx)  -> [item]   (a table's rolls; ctx.late: late night, premium x2)
//   rollWeapon({ rarity, base, brand }, rand) -> item
//   legendaryItem(id, rand)   -> item
//   statsOf(item) -> { dmg, rate, mag, reload, spread, kb, speed, tags: [...], brand, mods, quirk }  (multipliers, 1 = base)
//   compare(a, b) -> [{ k, label, a, b, up }]   the ▲▼ card
//   QUIRKS[lg] = { dmgMul?(ctx), onHit?(ctx) -> [effects], onKill?(ctx) -> [effects] }  (combat calls these)
import { BRANDS, MODIFIERS, LEGENDARIES, LOOT_TABLES } from './content/loot.js';
import { kindOf } from './items.js';
import { IMPLANTS, rollQuality } from './implants.js'; // organ cores (WP5)
import { WEAPONS } from '../weapons.js';

export { BRANDS, MODIFIERS, LEGENDARIES, LOOT_TABLES };
export const RARITY_ORDER = ['common', 'rare', 'epic', 'legendary', 'premium'];
export const RANGE = { common: [-0.10, 0.10], rare: [0, 0.15], epic: [0.05, 0.25], legendary: [0.10, 0.35], premium: [0.20, 0.45] }; // stat bonus per rarity (content/loot.js header)
export const STATS = [ // key, label for the card, which way is better (+1: more is better; -1: the multiplier shrinks as the bonus grows)
  ['dmg', 'damage', 1], ['rate', 'fire rate', 1], ['mag', 'magazine', 1], ['reload', 'reload speed', -1], ['spread', 'accuracy', -1], ['kb', 'knockback', 1], ['speed', 'projectile speed', 1],
];
const MODS_BY_RARITY = { common: [0.25, 0], rare: [0.6, 0], epic: [1, 0.15], legendary: [1, 0.5], premium: [1, 0.8] }; // [chance of a 1st, chance of a 2nd]
const has = (T, k) => typeof k === 'string' && Object.hasOwn(T, k);

// mulberry32, like shared/map.js rng: the same seed is the same item everywhere
export function rng(seed) {
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const pickW = (list, rand) => { const tot = list.reduce((a, e) => a + (e.w || 0), 0); let x = rand() * tot; for (const e of list) { x -= e.w || 0; if (x < 0) return e; } return list[list.length - 1]; };
const pick = (a, rand) => a[Math.floor(rand() * a.length) % a.length];

// the weapons a random roll can be: every held gun and melee (no rig fists, no claw, no mode-only kit)
export const LOOT_BASES = Object.keys(WEAPONS).filter((b) => { const k = kindOf(b); return k === 'gun' || k === 'melee'; });
// a guard: a legendary whose base isn't something you can hold gets the nearest thing (the content is fixed, #84;
// this keeps a future typo from rolling a ghost item)
const BASE_FALLBACK = { rigpunch: 'slapper' };
export const legendaryBase = (L) => (kindOf(L.base) ? L.base : BASE_FALLBACK[L.base] || 'slapper');

export function rollWeapon({ rarity = 'common', base, brand } = {}, rand = Math.random) {
  const r = RARITY_ORDER.includes(rarity) ? rarity : 'common';
  const b = base && kindOf(base) ? base : pick(LOOT_BASES, rand);
  const br = brand && has(BRANDS, brand) ? brand : pick(Object.keys(BRANDS), rand);
  const [c1, c2] = MODS_BY_RARITY[r], all = Object.keys(MODIFIERS), m = [];
  if (rand() < c1) m.push(pick(all, rand));
  if (rand() < c2) { const two = pick(all.filter((x) => !m.includes(x)), rand); if (two) m.push(two); }
  const it = { b, r, s: (Math.floor(rand() * 4294967296) >>> 0) || 1, br };
  if (m.length) it.m = m;
  return it;
}
export function legendaryItem(id, rand = Math.random) {
  const L = has(LEGENDARIES, id) && LEGENDARIES[id];
  if (!L) return null;
  return { b: legendaryBase(L), r: L.rarity === 'premium' ? 'premium' : 'legendary', s: (Math.floor(rand() * 4294967296) >>> 0) || 1, br: has(BRANDS, L.brand) ? L.brand : undefined, lg: id };
}
// a rarity-only entry at legendary / premium: one of the named ones of that rarity, or a rolled one
function namedOr(r, rand) {
  const ids = Object.keys(LEGENDARIES).filter((k) => (LEGENDARIES[k].rarity === 'premium') === (r === 'premium'));
  return ids.length && rand() < 0.5 ? legendaryItem(pick(ids, rand), rand) : rollWeapon({ rarity: r }, rand);
}
// one entry -> one item (or null: an item id nothing knows yet, e.g. an organ core before WP5 registers implants)
export function rollEntry(e, rand = Math.random) {
  if (!e) return null;
  if (e.legendary) return legendaryItem(e.legendary, rand);
  if (e.item) { const k = kindOf(e.item); if (!k) return null; const it = { b: e.item, r: 'common', s: 0 }; if (k === 'implant' && IMPLANTS[e.item].kind === 'core') it.ql = rollQuality(rand); return it; } // organ cores roll their quality
  if (!e.base && !e.brand && (e.rarity === 'legendary' || e.rarity === 'premium')) return namedOr(e.rarity, rand);
  return rollWeapon({ rarity: e.rarity, base: e.base, brand: e.brand }, rand);
}
export function rollTable(id, rand = Math.random, ctx = {}) {
  const T = has(LOOT_TABLES, id) && LOOT_TABLES[id];
  if (!T) return [];
  const entries = ctx.late ? T.entries.map((e) => (e.rarity === 'premium' ? { ...e, w: e.w * 2 } : e)) : T.entries; // late night: premium x2
  const out = [];
  for (let i = 0; i < Math.max(1, T.rolls | 0); i++) { const it = rollEntry(pickW(entries, rand), rand); if (it) out.push(it); }
  return out;
}

// ------------------------------------------------------------ stats from the seed
const BRAND_STATS = { // the brand rules that are plain numbers (the rest are tags combat reads)
  corp: { spread: 0.85, reload: 0.9, narrow: true },
  bottom_scrap: { extraPart: true },
  value_pack: { rate: 1.05, jam: 0.03 },
  meat_mechanics: { regen: true },
  famiglia: { grudge: true },
  number_works: { numbers: true },
};
const MOD_STATS = { bouncy: { kb: 1.8 }, fleshy: { mag: 1.2 }, on_loan: { dmg: 1.25 } };
const EXTRA_PARTS = ['scope', 'bayonet', 'cup holder', 'a second, smaller barrel', 'a wok dish', 'a bell'];
export function statsOf(it) {
  const out = { dmg: 1, rate: 1, mag: 1, reload: 1, spread: 1, kb: 1, speed: 1, tags: [], brand: null, mods: [], quirk: null, part: null };
  if (!it || !kindOf(it.b)) return out;
  const r = RANGE[it.r] || RANGE.common, rand = rng((it.s >>> 0) ^ 0x51a7);
  const B = has(BRAND_STATS, it.br) ? BRAND_STATS[it.br] : {};
  for (const [k, , dir] of STATS) {
    if (!it.s) break; // seed 0 = a stock item (your starter kit, quest weapons): no roll, plain numbers
    let u = rand();
    if (B.narrow) u = 0.5 + (u - 0.5) * 0.5; // ☺ CORP: low variance
    const bonus = r[0] + (r[1] - r[0]) * u;
    out[k] = dir > 0 ? 1 + bonus : 1 / (1 + bonus);
  }
  for (const k of ['spread', 'reload', 'rate', 'dmg', 'kb', 'mag']) if (B[k]) out[k] *= B[k];
  if (B.jam) out.tags.push('jam');
  for (const t of ['regen', 'grudge', 'numbers']) if (B[t]) out.tags.push(t);
  if (B.extraPart) out.part = EXTRA_PARTS[Math.floor(rand() * EXTRA_PARTS.length)];
  if (has(BRANDS, it.br)) out.brand = it.br;
  for (const m of Array.isArray(it.m) ? it.m : []) {
    if (!has(MODIFIERS, m) || out.mods.includes(m)) continue;
    out.mods.push(m); out.tags.push(m);
    for (const [k, v] of Object.entries(MOD_STATS[m] || {})) out[k] *= v;
  }
  if (it.lg && has(LEGENDARIES, it.lg)) out.quirk = it.lg;
  for (const [k] of STATS) out[k] = Math.round(out[k] * 1000) / 1000;
  return out;
}
// which stats a base actually has (the card hides the rest: a cigarette has no magazine)
export function statsFor(b) {
  const w = WEAPONS[b] || {};
  return STATS.filter(([k]) => (k === 'dmg' ? true : k === 'rate' ? !!(w.rate || w.cd) : k === 'mag' ? !!w.mag : k === 'reload' ? !!w.reload : k === 'spread' ? !!w.spread : k === 'kb' ? w.kb != null : k === 'speed' ? !!w.speed : true)).map(([k]) => k);
}
// the stat card: what the new one changes against what you hold (up = better)
export function compare(a, b) {
  const A = statsOf(a), Bs = statsOf(b);
  return STATS.map(([k, label, dir]) => ({ k, label, a: A[k], b: Bs[k], up: dir > 0 ? Bs[k] > A[k] : Bs[k] < A[k], same: Math.abs(Bs[k] - A[k]) < 0.005 }));
}
export function nameOf(it) {
  if (!it) return '';
  if (it.lg && has(LEGENDARIES, it.lg)) return LEGENDARIES[it.lg].name;
  const base = WEAPONS[it.b] ? WEAPONS[it.b].name : it.b;
  const mods = (it.m || []).filter((m) => has(MODIFIERS, m)).map((m) => MODIFIERS[m].name);
  return [...mods, base].join(' ');
}

// ------------------------------------------------------------ legendary quirks (the slice's four, more as they're needed)
// combat (the solo worker / StoryRoom) calls these with ctx { me, target, dmg, late (s past the mission timer), ... };
// effects are plain objects the host applies: { heal }, { say }, { slip }, { coupons }, { splash: { r, cone, dmg } },
// { puddle: { r, life, kind } }
export const QUIRKS = {
  late_bloomer: { dmgMul: (c) => 1 + Math.min(0.6, Math.max(0, (c.late || 0) * 0.01)) },
  grandmas_hands: { onHit: () => [{ heal: 6 }, { say: 'sweetie' }, { slip: true }] },
  mothers_ladle: { onHit: (c) => [{ splash: { r: 3, cone: true, dmg: Math.round((c.dmg || 0) * 0.5) } }, { puddle: { r: 1.6, life: 6, kind: 'soup' } }] },
  severance_package: { onKill: () => [{ coupons: 50 }] },
};
// what a hit / kill with this item does beyond its damage (dmg already scaled by statsOf + the quirk's dmgMul)
export function hitWith(it, c = {}) {
  const s = statsOf(it), q = s.quirk && QUIRKS[s.quirk];
  let dmg = (c.dmg || 0) * s.dmg * (q && q.dmgMul ? q.dmgMul(c) : 1);
  if (s.tags.includes('rounded')) dmg = Math.round(dmg / 5) * 5;
  const fx = q && q.onHit ? q.onHit({ ...c, dmg }) : [];
  return { dmg, fx };
}
export const killWith = (it, c = {}) => { const s = statsOf(it), q = s.quirk && QUIRKS[s.quirk]; return q && q.onKill ? q.onKill(c) : []; };
