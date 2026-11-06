// OVERDUE inventory (WP3): the Tote Bag, the 8-slot quick bar and the safehouse Locker. pure: no node, no dom.
// the sim (solo worker or co-op StoryRoom) owns an inventory and applies every edit through invOp(), so a client can
// only move, bar or drop items it really has. the quest engine and loot call the same functions.
//
// an item: { u, b, r, s, n?, q? }
//   u: its id in this inventory (a number, never reused)   b: the base (a weapon / item / streak id, or STORY_ITEMS)
//   r: rarity (WP4: common .. premium; 'common' for now)    s: the loot seed (WP4 rebuilds stats from it)
//   n: a custom name (rare)                                  q: how many (stackables only)
//   br: brand, m: [modifier ids] (max 2), lg: a named legendary's id (loot.js; stats come from s, never stored)
// an inventory: { bag: [item|null] (cap cells), cap, bar: [u|null] x 8, locker: [item], next }
import { WEAPONS, ITEMS, STREAKS } from '../weapons.js';
import { BRANDS, MODIFIERS, LEGENDARIES } from './content/loot.js'; // the writer's loot data (WP4 rolls it in loot.js)
import { ITEMS as STORY_CONTENT_ITEMS } from './content/items.js'; // key / quest items

export const INV = { bar: 8, bag: 20, bagMax: 60, locker: 200, streakMax: 3, stackMax: 20 };
export const RARITIES = ['common', 'rare', 'epic', 'legendary', 'premium']; // WP4 rolls these (shared/cosmetics.js colours + ☺ PREMIUM)

// story-only things: snacks, junk to sell, quest items (the writer's content can add more with addStoryItem)
export const STORY_ITEMS = Object.create(null);
export function addStoryItem(id, def) { if (/^[a-z][a-z0-9_]{0,31}$/.test(id) && !WEAPONS[id] && !ITEMS[id] && !STREAKS[id]) STORY_ITEMS[id] = { kind: 'snack', ...def }; }
addStoryItem('jank_cola', { kind: 'snack', name: 'Jank Cola', color: '#ff3030', desc: 'warm, flat and still fizzing somehow. heals 25.', heal: 25, stack: 10 });
addStoryItem('bread_heel', { kind: 'snack', name: 'Heel of Bread', color: '#e0a050', desc: 'the end bit. nobody wants it. heals 10.', heal: 10, stack: 10 });
addStoryItem('bottlecap', { kind: 'junk', name: 'Bottle Cap', color: '#c0c0c0', desc: 'worth nothing. people still take them.', stack: 20, value: 1 });
// the writer's key / quest items (content/items.js): pages, keys and documents are quest things you can't drop.
// 'weapon' ones are weapons with a name (loot gives them as { b: base, n: name }), so they aren't registered here
for (const [id, d] of Object.entries(STORY_CONTENT_ITEMS)) {
  if (d.kind === 'weapon') continue;
  const kind = d.kind === 'consumable' ? 'snack' : 'quest';
  addStoryItem(id, { kind, name: d.name, desc: d.desc, color: kind === 'quest' ? '#ffe14d' : '#7dff4f', quest: kind === 'quest' && !!d.keep, keep: !!d.keep });
}

const HELD = new Set(['primary', 'secondary', 'melee']);
const has = (T, k) => typeof k === 'string' && Object.hasOwn(T, k);
// what sort of thing a base is: weapon (gun or melee), gear (the G items), streak, snack, junk, quest. null = not a thing
export function kindOf(b) {
  if (has(WEAPONS, b) && !WEAPONS[b].modeOnly && HELD.has(WEAPONS[b].slot)) return WEAPONS[b].slot === 'melee' ? 'melee' : 'gun'; // (not the rig's fists, the claw, a thrown frag...)
  if (has(ITEMS, b)) return 'gear';
  if (has(STREAKS, b)) return 'streak';
  if (has(STORY_ITEMS, b)) return STORY_ITEMS[b].kind;
  return null;
}
export function stackOf(b) { const k = kindOf(b); return k === 'streak' ? INV.streakMax : k === 'gear' ? 5 : has(STORY_ITEMS, b) ? STORY_ITEMS[b].stack || 1 : 1; }
export function infoOf(it) {
  const b = it && it.b, k = kindOf(b);
  const d = has(WEAPONS, b) ? WEAPONS[b] : has(ITEMS, b) ? ITEMS[b] : has(STREAKS, b) ? STREAKS[b] : has(STORY_ITEMS, b) ? STORY_ITEMS[b] : null;
  const L = it.lg && has(LEGENDARIES, it.lg) ? LEGENDARIES[it.lg] : null;
  return d ? { kind: k, name: L ? L.name : (it.n || d.name), color: d.color || '#ffe14d', desc: L ? `"${L.flavour}" ${L.quirk}` : d.desc || '' } : null;
}

export function newInv() { return { bag: Array(INV.bag).fill(null), cap: INV.bag, bar: Array(INV.bar).fill(null), locker: [], next: 1 }; }
// a fresh item (not in any inventory yet): makeItem('redline', { r: 'rare', s: 12345 })
export function makeItem(b, o = {}) {
  if (!kindOf(b)) return null;
  const it = { b, r: RARITIES.includes(o.r) ? o.r : 'common', s: Number.isInteger(o.s) ? o.s >>> 0 : 0 };
  if (typeof o.n === 'string' && o.n) it.n = o.n.slice(0, 40);
  const k = kindOf(b);
  if (k === 'gun' || k === 'melee') { // loot rolls (shared/story/loot.js): only real ids survive
    if (has(BRANDS, o.br)) it.br = o.br;
    if (Array.isArray(o.m)) { const m = [...new Set(o.m.filter((x) => has(MODIFIERS, x)))].slice(0, 2); if (m.length) it.m = m; }
    if (has(LEGENDARIES, o.lg)) { it.lg = o.lg; if (!['legendary', 'premium'].includes(it.r)) it.r = LEGENDARIES[o.lg].rarity === 'premium' ? 'premium' : 'legendary'; }
  }
  if (stackOf(b) > 1) it.q = Math.max(1, Math.min(stackOf(b), o.q | 0 || 1));
  return it;
}
const same = (a, b) => a.b === b.b && a.r === b.r && !a.n && !b.n && !a.lg && !b.lg; // stackables only stack with their own kind
export const find = (inv, u) => inv.bag.findIndex((x) => x && x.u === u);
export const itemAt = (inv, u) => { const i = find(inv, u); return i < 0 ? null : inv.bag[i]; };
export const count = (inv, b) => inv.bag.reduce((n, x) => n + (x && x.b === b ? x.q || 1 : 0), 0);

// put an item in the bag: stacks first, then the first empty cell (into the bar too, if the bar has a free slot and
// it's something you hold). returns the u it landed in, or 0 when the bag is full (the caller leaves it on the floor)
export function invAdd(inv, item, { toBar = true } = {}) {
  const it = makeItem(item && item.b, item || {});
  if (!it) return 0;
  const max = stackOf(it.b);
  let left = max > 1 ? Math.max(1, Math.min(1e6, (item.q | 0) || 1)) : 1, last = 0;
  if (max > 1) for (const x of inv.bag) if (x && same(x, it) && (x.q || 1) < max && left > 0) {
    const take = Math.min(max - (x.q || 1), left);
    x.q = (x.q || 1) + take; left -= take; last = x.u;
  }
  while (left > 0) {
    const i = inv.bag.indexOf(null);
    if (i < 0) { if (item) item.q = left; return 0; } // full: what didn't fit stays with the caller (item.q is the rest)
    const one = { ...it, u: inv.next++ };
    if (max > 1) { one.q = Math.min(max, left); left -= one.q; } else left = 0;
    inv.bag[i] = one; last = one.u;
    const k = kindOf(one.b);
    if (toBar && (k === 'gun' || k === 'melee' || k === 'gear' || k === 'streak' || k === 'snack') && !inv.bar.some((u) => u != null && (itemAt(inv, u) || {}).b === one.b)) { const j = inv.bar.indexOf(null); if (j >= 0) inv.bar[j] = one.u; }
  }
  return last;
}
// take n of u out (all of it by default). returns the removed item (with q = n for stacks) or null
export function invTake(inv, u, n) {
  const i = find(inv, u);
  if (i < 0) return null;
  const x = inv.bag[i], q = x.q || 1, k = n == null ? q : Math.max(1, Math.min(q, n | 0));
  if (k < q) { x.q = q - k; return { ...x, q: k, u: undefined }; }
  inv.bag[i] = null;
  for (let j = 0; j < inv.bar.length; j++) if (inv.bar[j] === u) inv.bar[j] = null;
  return x;
}
export const hasItem = (inv, b, n = 1) => count(inv, b) >= n;

// the one entry point for edits from a client. op: { op, ... }. returns { ok } or { error }. never throws
//   bar   { slot 0-7, u|null }    put an item you have on a bar slot (null clears it; one slot per item)
//   move  { from, to }            swap two bag cells
//   drop  { u, n? }               take it out of the bag: the sim puts it on the floor (returned as dropped)
//   stash { u }  /  unstash { i } bag <-> locker (only at a locker: the sim checks where you are)
export function invOp(inv, m, { atLocker = false } = {}) {
  if (!m || typeof m.op !== 'string') return { error: 'bad op' };
  const okU = (u) => Number.isInteger(u) && find(inv, u) >= 0;
  const cell = (i) => Number.isInteger(i) && i >= 0 && i < inv.cap;
  switch (m.op) {
    case 'bar': {
      if (!Number.isInteger(m.slot) || m.slot < 0 || m.slot >= INV.bar) return { error: 'bad slot' };
      if (m.u == null) { inv.bar[m.slot] = null; return { ok: true }; }
      if (!okU(m.u)) return { error: "you don't have that" };
      const k = kindOf(itemAt(inv, m.u).b);
      if (k === 'junk' || k === 'quest') return { error: "that doesn't go on the bar" };
      const was = inv.bar.indexOf(m.u), there = inv.bar[m.slot];
      if (was >= 0) inv.bar[was] = there; // dragging along the bar swaps the two
      inv.bar[m.slot] = m.u;
      return { ok: true };
    }
    case 'move': {
      if (!cell(m.from) || !cell(m.to)) return { error: 'bad cell' };
      [inv.bag[m.from], inv.bag[m.to]] = [inv.bag[m.to], inv.bag[m.from]];
      return { ok: true };
    }
    case 'drop': {
      if (!okU(m.u)) return { error: "you don't have that" };
      if (STORY_ITEMS[itemAt(inv, m.u).b] && STORY_ITEMS[itemAt(inv, m.u).b].quest) return { error: "you'll need that" };
      return { ok: true, dropped: invTake(inv, m.u, m.n == null ? undefined : m.n) };
    }
    case 'stash': {
      if (!atLocker) return { error: 'no locker here' };
      if (!okU(m.u)) return { error: "you don't have that" };
      if (inv.locker.length >= INV.locker) return { error: 'the locker is full' };
      const it = invTake(inv, m.u);
      delete it.u;
      inv.locker.push(it);
      return { ok: true };
    }
    case 'unstash': {
      if (!atLocker) return { error: 'no locker here' };
      if (!Number.isInteger(m.i) || m.i < 0 || m.i >= inv.locker.length) return { error: 'bad locker slot' };
      if (!invAdd(inv, inv.locker[m.i], { toBar: false })) return { error: 'the tote bag is full' };
      inv.locker.splice(m.i, 1);
      return { ok: true };
    }
    default: return { error: 'bad op' };
  }
}

// a saved inventory -> a sane one (types, sizes, real bases, unique u's, bar refs that exist). never throws
export function cleanInv(raw) {
  const inv = newInv();
  if (!raw || typeof raw !== 'object') return inv;
  inv.cap = Number.isInteger(raw.cap) ? Math.max(INV.bag, Math.min(INV.bagMax, raw.cap)) : INV.bag;
  inv.bag = Array(inv.cap).fill(null);
  const seen = new Set();
  let top = 0;
  const one = (x, keepU) => {
    if (!x || typeof x !== 'object') return null;
    const it = makeItem(x.b, x);
    if (!it) return null;
    if (keepU) { if (!Number.isInteger(x.u) || x.u < 1 || x.u > 1e9 || seen.has(x.u)) return null; it.u = x.u; seen.add(x.u); top = Math.max(top, x.u); }
    return it;
  };
  if (Array.isArray(raw.bag)) raw.bag.slice(0, inv.cap).forEach((x, i) => { inv.bag[i] = one(x, true); });
  if (Array.isArray(raw.locker)) inv.locker = raw.locker.slice(0, INV.locker).map((x) => one(x, false)).filter(Boolean);
  if (Array.isArray(raw.bar)) for (let j = 0; j < INV.bar; j++) { const u = raw.bar[j]; inv.bar[j] = Number.isInteger(u) && seen.has(u) && !inv.bar.includes(u) ? u : null; }
  inv.next = Math.max(top + 1, Number.isInteger(raw.next) && raw.next <= 1e9 ? raw.next : 1);
  return inv;
}

// the bar as the weapon code sees it: per slot the weapon id (guns + melee) or null (gear, streaks, snacks, empty)
export function barWeapons(inv) { return inv.bar.map((u) => { const it = u == null ? null : itemAt(inv, u); const k = it && kindOf(it.b); return k === 'gun' || k === 'melee' ? it.b : null; }); }
// your normal loadout as a starter kit (New Game): primary, secondary, melee, item on bar slots 1-4
export function starterInv(lo) {
  const inv = newInv();
  for (const b of [lo && lo.primary, lo && lo.secondary, lo && lo.melee, lo && lo.item]) if (kindOf(b)) invAdd(inv, { b });
  return inv;
}
