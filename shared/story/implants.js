// OVERDUE bio-implants (WP5): body slots, the Body Budget, Drift, installs, organ-core quality, and the numbers the
// slice's implants run on. the DATA is the writer's (shared/story/content/implants.js: 50 implants, 10 slots); this is
// the engine. pure: no node, no dom.
//
// a body: { slots: { slot: { b, ql? } }, perm (permanent drift from installs / cold choices), fines }
// an implant in the Tote Bag is an item { b: implant id, r, s, ql? } (ql: an organ core's quality)
//   budget(ctx) -> n                         3 + 1 per act after the first + 1 per 3 board cats
//   driftOf(body, ctx) -> n                  over budget + permanent drift (anchors are negative)
//   installOp(body, inv, m, ctx) -> { ok, out? } | { error }    install / uninstall through the inventory
//   perk(body, id, ctx) -> numbers | null    what an installed implant does right now (quality and overload applied)
//   rollQuality(rand) -> 'bruised' | 'fresh' | 'prime' | 'premium'
import { IMPLANTS } from './content/implants.js';

export { IMPLANTS };
export const BODY_SLOTS = ['head', 'eyes', 'mouth', 'heart', 'lungs', 'guts', 'spine', 'arms', 'legs', 'skin'];
export const QUALITY = { bruised: 0.7, fresh: 1, prime: 1.2, premium: 1.5 }; // content/implants.js header
export const QUALITY_W = [['bruised', 30], ['fresh', 40], ['prime', 22], ['premium', 8]];
export const OVERLOAD = 1.5; // over budget: every downside's chance x1.5
export const UNINSTALL_FEE = 150; // coupons (the Meat Mechanic keeps the bits)
const has = (T, k) => typeof k === 'string' && Object.hasOwn(T, k);
export const isImplant = (b) => has(IMPLANTS, b);

export function newBody() { return { slots: {}, perm: 0 }; }
export function cleanBody(raw) {
  const b = newBody();
  if (!raw || typeof raw !== 'object') return b;
  if (raw.slots && typeof raw.slots === 'object') for (const s of BODY_SLOTS) {
    const x = Object.hasOwn(raw.slots, s) && raw.slots[s];
    if (x && has(IMPLANTS, x.b) && IMPLANTS[x.b].slot === s) b.slots[s] = { b: x.b, ...(has(QUALITY, x.ql) ? { ql: x.ql } : {}) };
  }
  b.perm = Number.isFinite(raw.perm) ? Math.max(-10, Math.min(20, Math.round(raw.perm))) : 0;
  return b;
}

export function budget(ctx = {}) { return 3 + Math.max(0, (ctx.act || 1) - 1) + Math.floor(Math.max(0, ctx.cats || 0) / 3); }
export const installed = (body) => BODY_SLOTS.filter((s) => body.slots[s]).map((s) => body.slots[s].b);
export const overBudget = (body, ctx) => Math.max(0, installed(body).length - budget(ctx));
export function driftOf(body, ctx = {}) { return Math.max(0, overBudget(body, ctx) + (body.perm || 0)); }
// what Drift means for the story (content/implants.js): 0-1 Cale, 2-3 fading, 4+ "a perfect employee"
export const driftBand = (d) => (d <= 1 ? 'cale' : d <= 3 ? 'fading' : 'employee');

export function rollQuality(rand = Math.random) {
  const tot = QUALITY_W.reduce((a, [, w]) => a + w, 0);
  let x = rand() * tot;
  for (const [q, w] of QUALITY_W) { x -= w; if (x < 0) return q; }
  return 'fresh';
}

// install / uninstall. inv is the Tote Bag (shared/story/items.js); the implant moves bag <-> body. the caller (the sim)
// checks you're at a clinic and charges coupons; this checks everything about the body itself.
//   { op: 'install', u }   the implant item with that u goes in its slot; what was there comes back to the bag
//   { op: 'uninstall', slot }
export function installOp(body, inv, m, { takeItem, giveItem }) {
  if (!m || typeof m.op !== 'string') return { error: 'bad op' };
  if (m.op === 'install') {
    const it = Number.isInteger(m.u) ? inv.bag.find((x) => x && x.u === m.u) : null;
    if (!it || !has(IMPLANTS, it.b)) return { error: "that's not an implant" };
    const I = IMPLANTS[it.b], slot = I.slot;
    if (!BODY_SLOTS.includes(slot)) return { error: 'no slot for that' };
    const old = body.slots[slot];
    takeItem(it.u);
    if (old && !giveItem({ b: old.b, r: 'common', s: 0, ...(old.ql ? { ql: old.ql } : {}) })) { giveItem(it); return { error: 'the tote bag is full (the old one has to go somewhere)' }; }
    body.slots[slot] = { b: it.b, ...(has(QUALITY, it.ql) ? { ql: it.ql } : {}) };
    body.perm = (body.perm || 0) + (Number.isFinite(I.drift) ? I.drift : 0); // permanent: it stays even if you take it out
    return { ok: true, slot, swapped: old ? old.b : null };
  }
  if (m.op === 'uninstall') {
    if (!BODY_SLOTS.includes(m.slot) || !body.slots[m.slot]) return { error: 'nothing in there' };
    const old = body.slots[m.slot];
    if (!giveItem({ b: old.b, r: 'common', s: 0, ...(old.ql ? { ql: old.ql } : {}) })) return { error: 'the tote bag is full' };
    delete body.slots[m.slot];
    return { ok: true, slot: m.slot, out: old.b };
  }
  return { error: 'bad op' };
}

// ------------------------------------------------------------ the slice's implants as numbers (perk text in content)
// ql scales the perk (cores); over budget scales the downside's chance by OVERLOAD
const SLICE = {
  pigeon_eyes: () => ({ seeLoot: 40, wobble: 0.012, flipEvery: 30, flipFor: 0.3 }),
  spring_knees: () => ({ jump: 1.8, fall: 0.5, fold: 1 / 20, stumble: 0.6 }),
  core_second_stomach: (q) => ({ eat: { common: 10, rare: 20, epic: 35, legendary: 55, premium: 80 }, eatMul: q, burpEvery: 30, vomitAfter: 3, eatHold: 0.8 }),
  core_cracked_punch_clock: (q) => ({ freeMagEvery: Math.round(60 / q), slowAt: 20, slowFor: 3 * q, slowScale: 0.45, tickR: 12, clockEvery: 120, clockStill: 5, fine: 10 }),
};
export const SLICE_IMPLANTS = Object.keys(SLICE);
export function perk(body, id, ctx = {}) {
  const s = BODY_SLOTS.find((k) => body.slots[k] && body.slots[k].b === id);
  if (!s || !SLICE[id]) return null;
  const q = QUALITY[body.slots[s].ql] || 1, p = SLICE[id](q), over = overBudget(body, ctx) > 0 ? OVERLOAD : 1;
  for (const k of ['fold', 'flipEvery', 'burpEvery', 'clockEvery']) if (p[k] != null) p[k] = k === 'fold' ? Math.min(1, p[k] * over) : p[k] / over; // louder downsides
  p.q = q; p.over = over > 1;
  return p;
}
// eating a weapon with the Second Stomach: HP by its rarity (x the core's quality)
export function eatHp(p, rarity) { return p && p.eat ? Math.round((p.eat[rarity] || p.eat.common) * (p.eatMul || 1)) : 0; }
