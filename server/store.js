// Account storage. Two backends with the same interface:
//   - FileStore (default): data/jankfire-db.json next to the game. Zero setup, perfect for hosting on your own PC.
//   - SupabaseStore: used automatically when SUPABASE_URL + SUPABASE_SERVICE_KEY are set. Survives redeploys on
//     hosts like Render whose disks get wiped. Run supabase.sql once in the Supabase SQL editor first.
// A user record: { name_lower, name, salt, hash, created_at, profile, kills, deaths, bot_kills, best_wave, top_speed, xp, playtime }
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { CONTAINERS } from '../shared/cosmetics.js';
const FIELD = (kind) => (CONTAINERS[kind] ? CONTAINERS[kind].field : null);

export const STAT_KEYS = ['kills', 'deaths', 'bot_kills', 'wins', 'best_wave', 'top_speed', 'xp', 'playtime', 'void_kills', 'headshots', 'tbags', 'airborne', 'wings_old'];
const MAX_KEYS = new Set(['best_wave', 'top_speed']); // these keep the max instead of adding up

function applyDelta(u, d) {
  const out = {};
  for (const k of STAT_KEYS) {
    if (d[k] == null) continue;
    out[k] = MAX_KEYS.has(k) ? Math.max(u[k] || 0, d[k]) : (u[k] || 0) + d[k];
  }
  return out;
}

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
    this.timer = setTimeout(() => { this.timer = null; this.flushNow(); }, 800);
  }
  async secret() { return this.db.secret; }
  async get(nameLower) { return this.db.users[nameLower] || null; }
  async create(u) {
    if (this.db.users[u.name_lower]) return false;
    this.db.users[u.name_lower] = { kills: 0, deaths: 0, bot_kills: 0, wins: 0, best_wave: 0, top_speed: 0, xp: 0, playtime: 0, void_kills: 0, headshots: 0, tbags: 0, airborne: 0, crates: 1, bags: 1, boxes: 1, inv: {}, profile: {}, created_at: new Date().toISOString(), ...u };
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
  async req(method, query, body, extra) {
    const res = await fetch(this.base + query, { method, headers: this.headers(extra), body: body ? JSON.stringify(body) : undefined });
    if (!res.ok) throw new Error(`supabase ${method} ${res.status}: ${(await res.text()).slice(0, 200)}`);
    const t = await res.text();
    return t ? JSON.parse(t) : null;
  }
  async secret() { return crypto.createHash('sha256').update('jankfire:' + this.key).digest('hex'); }
  async get(nameLower) {
    const rows = await this.req('GET', `?name_lower=eq.${encodeURIComponent(nameLower)}&select=*`);
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
    await this.req('PATCH', `?name_lower=eq.${encodeURIComponent(nameLower)}`, applyDelta(u, d), { Prefer: 'return=minimal' });
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
