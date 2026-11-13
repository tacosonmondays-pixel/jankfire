// Account storage. Two backends with the same interface:
//   - FileStore (default): data/jankfire-db.json next to the game. Zero setup, perfect for hosting on your own PC.
//   - SupabaseStore: used automatically when SUPABASE_URL + SUPABASE_SERVICE_KEY are set. Survives redeploys on
//     hosts like Render whose disks get wiped. Run supabase.sql once in the Supabase SQL editor first.
// A user record: { name_lower, name, salt, hash, created_at, profile, kills, deaths, bot_kills, best_wave, top_speed, xp, playtime }
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { CONTAINERS, migrateInv } from '../shared/cosmetics.js';
const FIELD = (kind) => (CONTAINERS[kind] ? CONTAINERS[kind].field : null);

export const STAT_KEYS = ['kills', 'deaths', 'bot_kills', 'wins', 'best_wave', 'top_speed', 'xp', 'playtime', 'void_kills', 'headshots', 'tbags'];
STAT_KEYS.push('airborne', 'wings_old'); // Never Landed + the grandfathered Wings
STAT_KEYS.push('sniper_feats'); // Sniper Royalty (bit flags, see BIT_KEYS)
STAT_KEYS.push('quiz_right'); // Smarty Pants: pop quiz questions answered right
STAT_KEYS.push('chicken_kills', 'melee_kills'); // Poultry in Motion (Chicken Rocket kills) + Sworn Protector (melee kills)
const MAX_KEYS = new Set(['best_wave', 'top_speed']); // these keep the max instead of adding up
import { MODE_STATS, mergeModes } from '../shared/modestats.js'; // per-mode leaderboards (inv.ms, no new columns)
const BIT_KEYS = new Set(['sniper_feats']); // bit flags (Sniper Royalty feats): OR'd in, so a feat never counts twice or turns off

function applyDelta(u, d) {
  const out = {};
  for (const k of STAT_KEYS) {
    if (d[k] == null) continue;
    out[k] = MAX_KEYS.has(k) ? Math.max(u[k] || 0, d[k]) : (u[k] || 0) + d[k];
    if (BIT_KEYS.has(k)) out[k] = (u[k] | 0) | (d[k] | 0);
  }
  return out;
}

// per-mode stats live in inv.ms = { qp: {...}, bomb: {...}, zm: {...}, br: {...} }: mergeModes (shared/modestats.js) adds a delta

class FileStore {
  constructor(dir) {
    this.kind = 'file';
    this.file = path.join(dir, 'jankfire-db.json');
    fs.mkdirSync(dir, { recursive: true });
    try { this.db = JSON.parse(fs.readFileSync(this.file, 'utf8')); } catch { this.db = {}; }
    this.db.users ||= {};
    this.db.secret ||= crypto.randomBytes(32).toString('hex');
    this.timer = null;
    // the Wings moved from Frequent Flyer to Never Landed: everyone who had Frequent Flyer at that moment keeps them (runs once)
    if (!this.db.wingsMoved) { for (const u of Object.values(this.db.users)) if ((u.top_speed || 0) >= 1000) u.wings_old = 1; this.db.wingsMoved = 1; }
    this.flushNow();
  }
  flushNow() {
    const tmp = this.file + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(this.db));
    fs.renameSync(tmp, this.file);
  }
  save() {
    if (this.timer) return;
    this.timer = setTimeout(() => { this.timer = null; try { this.flushNow(); } catch (e) { console.error('db save failed', e.message); } }, 800);
  }
  async secret() { return this.db.secret; }
  async get(nameLower) { const u = this.db.users[nameLower] || null; if (u && migrateInv(u.inv)) this.save?.(); return u; } // retired skins -> their new ids
  async create(u) {
    if (this.db.users[u.name_lower]) return false;
    this.db.users[u.name_lower] = { kills: 0, deaths: 0, bot_kills: 0, wins: 0, best_wave: 0, top_speed: 0, xp: 0, playtime: 0, void_kills: 0, headshots: 0, tbags: 0, chicken_kills: 0, melee_kills: 0, crates: 1, bags: 1, boxes: 1, inv: {}, profile: {}, created_at: new Date().toISOString(), ...u };
    this.save();
    return true;
  }
  async setProfile(nameLower, profile) {
    const u = this.db.users[nameLower];
    if (!u) return;
    u.profile = profile;
    this.save();
  }
  async addStats(nameLower, d) {
    const u = this.db.users[nameLower];
    if (!u) return;
    Object.assign(u, applyDelta(u, d));
    this.save();
  }
  async grantRolls(nameLower, kind, n) {
    const u = this.db.users[nameLower], f = FIELD(kind);
    if (!u || !f) return;
    u[f] = (u[f] || 0) + n;
    this.save();
  }
  // open one container and add the item; returns false if you didn't have one
  async spendRoll(nameLower, kind, item) {
    const u = this.db.users[nameLower], f = FIELD(kind);
    if (!u || !f || !(u[f] > 0)) return false;
    u[f]--;
    u.inv ||= {};
    if (item) (u.inv[item.type] ||= []).push(item.id);
    this.save();
    return true;
  }
  // open n of a kind in one go: one decrement by n, every item pushed, one write. false if you have fewer than n
  async spendRolls(nameLower, kind, n, items) {
    const u = this.db.users[nameLower], f = FIELD(kind);
    if (!u || !f || !(n > 0) || !((u[f] || 0) >= n)) return false;
    u[f] -= n;
    u.inv ||= {};
    for (const it of items) if (it) (u.inv[it.type] ||= []).push(it.id);
    this.save();
    return true;
  }
  // a gift from the management (shared/gifts.js): its containers, once per account (the id goes in inv.gifts).
  // the file store is one process with no await in between: two logins at once can't both get past the check
  async claimGift(nameLower, gift) {
    const u = this.db.users[nameLower];
    if (!u) return false;
    u.inv ||= {};
    const had = Array.isArray(u.inv.gifts) ? u.inv.gifts : (u.inv.gifts = []);
    if (had.includes(gift.id)) return false;
    had.push(gift.id);
    for (const [kind, n] of Object.entries(gift.rolls || {})) { const f = FIELD(kind); if (f) u[f] = (u[f] || 0) + n; }
    this.save();
    return true;
  }
  // a hidden NPC / cat found (shared/secrets.js): the id goes in inv.lore, plus its gift (a cosmetic or a container).
  // false if this account already had it (nothing is given twice)
  async addLore(nameLower, id, gift) {
    const u = this.db.users[nameLower];
    if (!u) return false;
    u.inv ||= {};
    const lore = Array.isArray(u.inv.lore) ? u.inv.lore : (u.inv.lore = []);
    if (lore.includes(id)) return false;
    lore.push(id);
    if (gift && gift.type) (u.inv[gift.type] ||= []).push(gift.id);
    if (gift && gift.roll && FIELD(gift.roll)) u[FIELD(gift.roll)] = (u[FIELD(gift.roll)] || 0) + 1;
    this.save();
    return true;
  }
  // story saves (OVERDUE, server/story.js). the file store acts like the jf_story table (3 slots in u.story);
  // JF_STORY_FALLBACK=1 makes it act like Supabase before the SQL re-run (1 slot in inv.story) to test that path
  async storyInfo() { return process.env.JF_STORY_FALLBACK === '1' ? { slots: 1, table: false } : { slots: 3, table: true }; }
  async getStory(nameLower) {
    const u = this.db.users[nameLower];
    if (!u) return [];
    const t = (await this.storyInfo()).table, src = t ? u.story : u.inv && u.inv.story;
    return src && typeof src === 'object' ? Object.values(src) : [];
  }
  async putStory(nameLower, slot, save) {
    const u = this.db.users[nameLower];
    if (!u) return false;
    if ((await this.storyInfo()).table) (u.story ||= {})[slot] = save;
    else { u.inv ||= {}; u.inv.story = { [slot]: save }; }
    this.save();
    return true;
  }
  async delStory(nameLower, slot) { // wipe one slot (and an old fallback copy of it)
    const u = this.db.users[nameLower];
    if (!u) return false;
    if (u.story && typeof u.story === 'object') delete u.story[slot];
    if (u.inv && u.inv.story && typeof u.inv.story === 'object') delete u.inv.story[slot];
    this.save();
    return true;
  }
  async addModeStats(nameLower, d) {
    const u = this.db.users[nameLower];
    if (!u) return;
    u.inv = mergeModes(u.inv || {}, d);
    this.save();
  }
  // rows for a mode's boards: the top n by one of its stats, each with that mode's whole bucket
  async modeRows(mode, key, n = 15) {
    if (!Object.hasOwn(MODE_STATS, mode)) return [];
    const b = (u) => (u.inv && u.inv.ms && u.inv.ms[mode]) || null;
    return Object.values(this.db.users).filter((u) => b(u) && (b(u)[key] || 0) > 0)
      .sort((x, y) => (b(y)[key] || 0) - (b(x)[key] || 0)).slice(0, n)
      .map((u) => ({ name: u.name, xp: u.xp || 0, ms: b(u) }));
  }
  async top(col, n = 15) {
    return Object.values(this.db.users).filter((u) => (u[col] || 0) > 0)
      .sort((a, b) => (b[col] || 0) - (a[col] || 0)).slice(0, n)
      .map((u) => ({ name: u.name, value: u[col] || 0, xp: u.xp || 0 }));
  }
}

class SupabaseStore {
  constructor(url, key) {
    this.kind = 'supabase';
    this.base = url.replace(/\/$/, '') + '/rest/v1/jf_users';
    this.key = key;
  }
  headers(extra) {
    // new-style keys (sb_secret_...) go in apikey only; old service_role JWTs also go in Authorization
    const auth = this.key.startsWith('sb_') ? {} : { Authorization: `Bearer ${this.key}` };
    return { apikey: this.key, ...auth, 'Content-Type': 'application/json', ...extra };
  }
  async req(method, query, body, extra, table) { // table: another table than jf_users ('/jf_story')
    const res = await fetch((table ? this.base.replace(/\/jf_users$/, table) : this.base) + query, { method, headers: this.headers(extra), body: body ? JSON.stringify(body) : undefined });
    if (!res.ok) throw new Error(`supabase ${method} ${res.status}: ${(await res.text()).slice(0, 200)}`);
    const t = await res.text();
    return t ? JSON.parse(t) : null;
  }
  async secret() { return crypto.createHash('sha256').update('jankfire:' + this.key).digest('hex'); }
  async get(nameLower) {
    const rows = await this.req('GET', `?name_lower=eq.${encodeURIComponent(nameLower)}&select=*`);
    if (rows && rows[0]) migrateInv(rows[0].inv); // retired skins -> their new ids (in memory: the next inv write keeps it)
    return rows && rows[0] ? rows[0] : null;
  }
  async create(u) {
    try { await this.req('POST', '', u, { Prefer: 'return=minimal' }); return true; }
    catch (e) { if (String(e.message).includes('409')) return false; throw e; }
  }
  async setProfile(nameLower, profile) {
    await this.req('PATCH', `?name_lower=eq.${encodeURIComponent(nameLower)}`, { profile }, { Prefer: 'return=minimal' });
  }
  async addStats(nameLower, d) {
    const u = await this.get(nameLower);
    if (!u) return;
    const out = applyDelta(u, d);
    // a stat column the table doesn't have yet (supabase.sql not re-run) would fail the whole batch: skip just that stat
    for (const k of Object.keys(out)) if (!(k in u)) { delete out[k]; if (!this.warned?.[k]) { (this.warned ||= {})[k] = 1; console.warn(`  !! jf_users has no '${k}' column: run the new block in supabase.sql`); } }
    await this.req('PATCH', `?name_lower=eq.${encodeURIComponent(nameLower)}`, out, { Prefer: 'return=minimal' });
  }
  async grantRolls(nameLower, kind, n) {
    const u = await this.get(nameLower), f = FIELD(kind);
    if (u && f) await this.req('PATCH', `?name_lower=eq.${encodeURIComponent(nameLower)}`, { [f]: (u[f] || 0) + n }, { Prefer: 'return=minimal' });
  }
  async spendRoll(nameLower, kind, item) {
    const u = await this.get(nameLower), f = FIELD(kind);
    if (!u || !f || !(u[f] > 0)) return false;
    const inv = u.inv || {};
    if (item) (inv[item.type] ||= []).push(item.id);
    // only succeeds if nobody opened that container in the meantime
    const rows = await this.req('PATCH', `?name_lower=eq.${encodeURIComponent(nameLower)}&${f}=eq.${u[f]}`, { [f]: u[f] - 1, inv }, { Prefer: 'return=representation' });
    return !!(rows && rows.length);
  }
  // n at once: the row only changes if the count is still what we read (a parallel open or a double click loses)
  async spendRolls(nameLower, kind, n, items) {
    const u = await this.get(nameLower), f = FIELD(kind);
    if (!u || !f || !(n > 0) || !((u[f] || 0) >= n)) return false;
    const inv = u.inv || {};
    for (const it of items) if (it) (inv[it.type] ||= []).push(it.id);
    const rows = await this.req('PATCH', `?name_lower=eq.${encodeURIComponent(nameLower)}&${f}=eq.${u[f]}`, { [f]: u[f] - n, inv }, { Prefer: 'return=representation' });
    return !!(rows && rows.length);
  }
  // a gift, once: the PATCH only lands if all three container counts are still what we read, so of two logins at once
  // one wins and the other reads again, sees the gift id and stops. (a container opened in between: try again)
  async claimGift(nameLower, gift) {
    for (let tries = 0; tries < 4; tries++) {
      const u = await this.get(nameLower);
      if (!u) return false;
      const inv = u.inv || {};
      const had = Array.isArray(inv.gifts) ? inv.gifts : (inv.gifts = []);
      if (had.includes(gift.id)) return false;
      had.push(gift.id);
      const patch = { inv };
      for (const [kind, n] of Object.entries(gift.rolls || {})) { const f = FIELD(kind); if (f) patch[f] = (u[f] || 0) + n; }
      const cond = ['crates', 'bags', 'boxes'].map((f) => `&${f}=eq.${u[f] || 0}`).join('');
      const rows = await this.req('PATCH', `?name_lower=eq.${encodeURIComponent(nameLower)}${cond}`, patch, { Prefer: 'return=representation' });
      if (rows && rows.length) return true;
    }
    return false;
  }
  async addLore(nameLower, id, gift) {
    const u = await this.get(nameLower);
    if (!u) return false;
    const inv = u.inv || {};
    const lore = Array.isArray(inv.lore) ? inv.lore : (inv.lore = []);
    if (lore.includes(id)) return false;
    lore.push(id);
    if (gift && gift.type) (inv[gift.type] ||= []).push(gift.id);
    const patch = { inv }, f = gift && gift.roll && FIELD(gift.roll);
    if (f) patch[f] = (u[f] || 0) + 1;
    await this.req('PATCH', `?name_lower=eq.${encodeURIComponent(nameLower)}`, patch, { Prefer: 'return=minimal' });
    return true;
  }
  // story saves: the jf_story table if the owner ran its supabase.sql block, else ONE slot in inv.story (TECH_PLAN §7)
  async storyInfo() {
    if (this.storyTable == null || (!this.storyTable && Date.now() - this.storyT > 600000)) { // (no table: look again every 10 min, the sql may have been run)
      this.storyT = Date.now();
      try { await this.req('GET', '?limit=0', null, null, '/jf_story'); this.storyTable = true; }
      catch { if (this.storyTable == null) console.warn('  !! no jf_story table: story saves use inv.story (1 slot) until docs/story/jf_story.sql is run in Supabase'); this.storyTable = false; }
    }
    return this.storyTable ? { slots: 3, table: true } : { slots: 1, table: false };
  }
  async getStory(nameLower) {
    if ((await this.storyInfo()).table) {
      const rows = await this.req('GET', `?name_lower=eq.${encodeURIComponent(nameLower)}&select=slot,version,act,chapter,playtime,coupons,data,updated_at`, null, null, '/jf_story');
      if (rows && rows.length) return rows.map((r) => { const { at, ...data } = r.data || {}; return { v: r.version, slot: r.slot, act: r.act, chapter: r.chapter, playtime: r.playtime, coupons: Number(r.coupons) || 0, at, data, t: Date.parse(r.updated_at) || 0 }; });
      // nothing in the table yet: a save made before the sql re-run is still in inv.story (it moves on the next save)
    }
    const u = await this.get(nameLower);
    const src = u && u.inv && u.inv.story;
    return src && typeof src === 'object' ? Object.values(src) : [];
  }
  async putStory(nameLower, slot, save) {
    if ((await this.storyInfo()).table) {
      const row = { name_lower: nameLower, slot, version: save.v, act: save.act, chapter: save.chapter, playtime: save.playtime, coupons: save.coupons, data: { ...save.data, at: save.at }, updated_at: new Date().toISOString() };
      await this.req('POST', '?on_conflict=name_lower,slot', row, { Prefer: 'resolution=merge-duplicates,return=minimal' }, '/jf_story');
      return true;
    }
    const u = await this.get(nameLower);
    if (!u) return false;
    const inv = u.inv || {};
    inv.story = { [slot]: save };
    await this.req('PATCH', `?name_lower=eq.${encodeURIComponent(nameLower)}`, { inv }, { Prefer: 'return=minimal' });
    return true;
  }
  // wipe one slot: its jf_story row (when the table exists), and an old inv.story copy of it (pre-table saves are still
  // read from there while the table has none). slot is an integer the route already checked
  async delStory(nameLower, slot) {
    if ((await this.storyInfo()).table) await this.req('DELETE', `?name_lower=eq.${encodeURIComponent(nameLower)}&slot=eq.${slot | 0}`, null, { Prefer: 'return=minimal' }, '/jf_story');
    const u = await this.get(nameLower);
    const st = u && u.inv && u.inv.story;
    if (st && typeof st === 'object' && Object.values(st).some((x) => x && x.slot === slot)) {
      const keep = Object.fromEntries(Object.entries(st).filter(([, x]) => !(x && x.slot === slot)));
      await this.req('PATCH', `?name_lower=eq.${encodeURIComponent(nameLower)}`, { inv: { ...u.inv, story: keep } }, { Prefer: 'return=minimal' });
    }
    return true;
  }
  async addModeStats(nameLower, d) {
    const u = await this.get(nameLower);
    if (!u) return;
    await this.req('PATCH', `?name_lower=eq.${encodeURIComponent(nameLower)}`, { inv: mergeModes(u.inv || {}, d) }, { Prefer: 'return=minimal' });
  }
  // mode and key are checked against MODE_STATS before they go in the query (PostgREST json paths)
  async modeRows(mode, key, n = 15) {
    if (!Object.hasOwn(MODE_STATS, mode) || !MODE_STATS[mode].keys.includes(key)) return [];
    const rows = await this.req('GET', `?select=name,xp,ms:inv->ms->${mode}&inv->ms->${mode}->>${key}=gt.0&order=inv->ms->${mode}->${key}.desc.nullslast&limit=${n}`);
    return (rows || []).filter((u) => u.ms && typeof u.ms === 'object').map((u) => ({ name: u.name, xp: u.xp || 0, ms: u.ms }));
  }
  async top(col, n = 15) {
    const rows = await this.req('GET', `?select=name,xp,${col}&${col}=gt.0&order=${col}.desc&limit=${n}`);
    return (rows || []).map((u) => ({ name: u.name, value: u[col] || 0, xp: u.xp || 0 }));
  }
}

export function makeStore(root) {
  const url = process.env.SUPABASE_URL, key = (process.env.SUPABASE_SERVICE_KEY || '').trim();
  if (url && key) {
    // the public key can't write to the locked table: every sign-up would fail. stop and say why.
    let role = '';
    try { role = JSON.parse(Buffer.from(key.split('.')[1] || '', 'base64url').toString()).role || ''; } catch { /* not a jwt */ }
    if (key.startsWith('sb_publishable_') || role === 'anon') {
      console.error('\n  !! SUPABASE_SERVICE_KEY is your PUBLISHABLE (public) key. The server needs the SECRET key.');
      console.error('  !! Supabase -> Project Settings -> API Keys -> Secret keys -> copy the one starting with sb_secret_');
      console.error('  !! Put it in .env (or Render\'s environment settings) and start the server again.\n');
      process.exit(1);
    }
    return new SupabaseStore(url, key);
  }
  return new FileStore(process.env.JF_DATA_DIR || path.join(root, 'data'));
}
