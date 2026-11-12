// OVERDUE story saves: the shape, a fresh save, and the one cleaner both hosts use (server endpoints, browser).
// pure module: no node, no dom. TECH_PLAN §7. until the owner runs the jf_story block in supabase.sql the server keeps
// ONE slot in jf_users.inv.story (FALLBACK below); with the table it's 3 slots.
//
// a save: { v, slot, act, chapter, playtime, coupons, at: { map, p: [x,y,z], yaw }, data: { ...per-system state } }
// data is owned by the systems: flags/quests/seen (quest engine), bag/bar/locker (inventory, WP3), implants/cores
// (WP5), hype... each system validates its own part with SAVE_PARTS (register below), so this file stays small.
import { CHAPTER_LIST, chapterOf } from './chapters.js';
export const SAVE = { v: 1, slots: 3, maxBytes: 64 * 1024, minGap: 10000, acts: 5 };
export const FALLBACK = { slots: 1, maxBytes: 24 * 1024 }; // inv.story until jf_story exists
export const CHAPTERS = CHAPTER_LIST.map((c) => c.id); // every main mission in story order (chapters.js)
const DEPTH = 8, KEYS = 4000, STR = 2000;

export function newSave(slot = 0, world = 'story_slice') { // at.fresh: no position yet, the sim puts you at the world's spawn
  return { v: SAVE.v, slot, act: 1, chapter: CHAPTERS[0], playtime: 0, coupons: 0, at: { map: world, p: [0, 0.1, 6], yaw: 0, fresh: true }, data: { flags: [], quests: {}, seen: [] } };
}

// systems register a cleaner for their part of save.data: fn(value) -> cleaned value (or undefined to drop it).
// unknown parts are kept as plain json (bounded by the size/depth checks) so a newer client's save isn't eaten.
export const SAVE_PARTS = Object.create(null);
export function savePart(key, fn) { SAVE_PARTS[key] = fn; }
savePart('flags', (v) => (Array.isArray(v) ? [...new Set(v.filter((s) => typeof s === 'string' && s.length <= 64))].slice(0, 2000) : []));
savePart('seen', (v) => (Array.isArray(v) ? [...new Set(v.filter((s) => typeof s === 'string' && s.length <= 64))].slice(0, 500) : []));
savePart('quests', (v) => (plain(v) ? v : {}));

const plain = (v) => !!v && typeof v === 'object' && !Array.isArray(v) && Object.getPrototypeOf(v) === Object.prototype;
const int = (x, lo, hi) => (Number.isFinite(x) && Math.floor(x) === x && x >= lo && x <= hi ? x : null);

// walk once: depth, key count, string length, finite numbers, no '_' or proto keys. false = junk
export function jsonOk(v) {
  const st = [v, 0];
  let n = 0;
  while (st.length) {
    const d = st.pop(), x = st.pop();
    if (typeof x === 'string') { if (x.length > STR) return false; continue; }
    if (typeof x === 'number') { if (!Number.isFinite(x)) return false; continue; }
    if (x === null || typeof x === 'boolean') continue;
    if (typeof x !== 'object' || d >= DEPTH) return false;
    if (!Array.isArray(x) && !plain(x)) return false;
    for (const k of Object.keys(x)) {
      if (++n > KEYS) return false;
      if (!Array.isArray(x) && (k[0] === '_' || k === '__proto__' || k === 'constructor' || k === 'prototype' || k.length > 64)) return false;
      st.push(x[k], d + 1);
    }
  }
  return true;
}

// clean a save coming from a client. prev: the stored save for that slot (or null): act can only go up by one
// per save (no skipping to the ending by editing a request). returns { save } or { error }.
export function cleanSave(raw, { slot = 0, prev = null, maxBytes = SAVE.maxBytes } = {}) {
  if (!plain(raw) || !jsonOk(raw)) return { error: 'bad save' };
  let size = 0;
  try { size = JSON.stringify(raw).length; } catch { return { error: 'bad save' }; }
  if (size > maxBytes) return { error: 'save too big' };
  const act = int(raw.act, 1, SAVE.acts);
  if (act == null) return { error: 'bad act' };
  const top = prev ? (prev.act || 1) + 1 : 2;
  if (act > top) return { error: 'bad act' };
  const chapter = typeof raw.chapter === 'string' && /^[a-z0-9_]{1,40}$/.test(raw.chapter) ? raw.chapter : CHAPTERS[0];
  const playtime = int(raw.playtime, 0, 1e8), coupons = int(raw.coupons, 0, 1e12);
  if (playtime == null || coupons == null) return { error: 'bad numbers' };
  const at = plain(raw.at) ? raw.at : {};
  const p = Array.isArray(at.p) && at.p.length === 3 && at.p.every((x) => Number.isFinite(x) && Math.abs(x) < 1e5) ? at.p.map((x) => Math.round(x * 100) / 100) : [0, 0.1, 6];
  const yaw = Number.isFinite(at.yaw) ? Math.round(at.yaw * 1000) / 1000 : 0;
  const map = typeof at.map === 'string' && /^[a-z0-9_:]{1,40}$/.test(at.map) ? at.map : 'story_slice';
  const data = {};
  const rd = plain(raw.data) ? raw.data : {};
  for (const k of Object.keys(rd)) {
    if (!/^[a-z][a-zA-Z0-9]{0,31}$/.test(k)) continue;
    const v = Object.hasOwn(SAVE_PARTS, k) ? SAVE_PARTS[k](rd[k]) : rd[k];
    if (v !== undefined) data[k] = v;
  }
  for (const k of ['flags', 'seen']) if (!data[k]) data[k] = [];
  if (!data.quests) data.quests = {};
  return { save: { v: SAVE.v, slot, act, chapter, playtime, coupons, at: { map, p, yaw, ...(at.fresh === true ? { fresh: true } : {}) }, data } };
}

// the little card the slot picker shows (no data blob): what /api/story/list returns per slot
export function saveCard(s) {
  if (!s) return null;
  const ch = chapterOf(s.data, s.chapter); // (where the quests say you are: the act and mission on the card)
  return { slot: s.slot | 0, act: ch.act || s.act | 0, chapter: ch.id, title: ch.label, playtime: s.playtime | 0, coupons: s.coupons || 0, at: s.at && s.at.map, t: s.t || 0 };
}
