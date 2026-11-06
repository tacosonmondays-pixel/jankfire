// Accounts: register / login with username + password, signed session tokens, profile sync,
// stats, levels and leaderboards. All HTTP, all JSON, under /api/*.
import crypto from 'node:crypto';
import { promisify } from 'node:util';
import { STAT_KEYS } from './store.js';
import { rollPick, itemInfo, CONTAINERS } from '../shared/cosmetics.js';
import { achievementsFrom } from '../shared/looks.js';
import { catsOf } from '../shared/secrets.js';
import { storyApi } from './story.js'; // OVERDUE save slots (/api/story/*)

const scrypt = promisify(crypto.scrypt);
const NAME_RE = /^[A-Za-z0-9_]{3,16}$/;
const TOKEN_DAYS = 60;

export function levelOf(xp) { return Math.floor(Math.sqrt((xp || 0) / 40)) + 1; }
export function xpForLevel(l) { return (l - 1) * (l - 1) * 40; }

function b64(s) { return Buffer.from(s).toString('base64url'); }

export class Accounts {
  constructor(store) {
    this.store = store;
    this.secretP = store.secret();
    this.hits = new Map(); // ip -> [timestamps] for login rate limiting
  }

  async sign(nameLower) {
    const body = b64(JSON.stringify({ n: nameLower, e: Date.now() + TOKEN_DAYS * 864e5 }));
    const mac = crypto.createHmac('sha256', await this.secretP).update(body).digest('base64url');
    return `${body}.${mac}`;
  }
  async verify(token) {
    if (typeof token !== 'string' || token.length > 400) return null;
    const [body, mac] = token.split('.');
    if (!body || !mac) return null;
    const want = crypto.createHmac('sha256', await this.secretP).update(body).digest('base64url');
    if (mac.length !== want.length || !crypto.timingSafeEqual(Buffer.from(mac), Buffer.from(want))) return null;
    try {
      const { n, e } = JSON.parse(Buffer.from(body, 'base64url').toString());
      if (Date.now() > e) return null;
      return await this.store.get(n);
    } catch { return null; }
  }

  public(u) {
    const stats = {};
    for (const k of STAT_KEYS) stats[k] = u[k] || 0;
    stats.cats = catsOf(u.inv); // hidden cats petted (kept in inv.lore, not a column)
    return { name: u.name, level: levelOf(u.xp), xp: u.xp || 0, stats, achs: [...achievementsFrom(stats)], profile: u.profile || {}, inv: pubInv(u.inv), rolls: { crate: u.crates || 0, bag: u.bags || 0, box: u.boxes || 0 }, created: u.created_at };
  }

  limited(ip) {
    const now = Date.now();
    const list = (this.hits.get(ip) || []).filter((t) => now - t < 60000);
    list.push(now);
    this.hits.set(ip, list);
    return list.length > 12;
  }

  async register(name, pass) {
    if (!NAME_RE.test(name || '')) return { error: 'username: 3-16 letters, numbers or _' };
    if (typeof pass !== 'string' || pass.length < 4 || pass.length > 100) return { error: 'password needs at least 4 characters' };
    const salt = crypto.randomBytes(16).toString('hex');
    const hash = (await scrypt(pass, salt, 32)).toString('hex');
    const ok = await this.store.create({ name_lower: name.toLowerCase(), name, salt, hash });
    if (!ok) return { error: 'that name is taken' };
    const u = await this.store.get(name.toLowerCase());
    return { token: await this.sign(u.name_lower), me: this.public(u) };
  }

  async login(name, pass) {
    const u = typeof name === 'string' ? await this.store.get(name.toLowerCase()) : null;
    if (!u || typeof pass !== 'string') return { error: 'wrong username or password' };
    const hash = await scrypt(pass, u.salt, 32);
    if (!crypto.timingSafeEqual(hash, Buffer.from(u.hash, 'hex'))) return { error: 'wrong username or password' };
    return { token: await this.sign(u.name_lower), me: this.public(u) };
  }

  async leaderboard() {
    const [wins, kills, speed, wave, xp] = await Promise.all([
      this.store.top('wins'), this.store.top('kills'), this.store.top('top_speed'), this.store.top('best_wave'), this.store.top('xp'),
    ]);
    const lv = (rows) => rows.map((r) => ({ ...r, level: levelOf(r.xp) }));
    return { wins: lv(wins), kills: lv(kills), speed: lv(speed), wave: lv(wave), xp: lv(xp) };
  }

  async roll(u, kind) {
    const c = CONTAINERS[kind];
    if (!c) return { error: 'open a crate, duffel bag or box' };
    if (!(u[c.field] > 0)) return { error: `no ${c.plural.toLowerCase()} left. win a round to get more` };
    const pick = rollPick(u.inv || {}, Math.random, c.types);
    if (!pick) {
      // you own everything in this kind of container: it turns into xp instead
      if (!(await this.store.spendRoll(u.name_lower, kind, null))) return { error: 'none left' };
      await this.store.addStats(u.name_lower, { xp: 100 });
      const fresh = await this.store.get(u.name_lower);
      return { item: null, me: this.public(fresh) };
    }
    if (!(await this.store.spendRoll(u.name_lower, kind, pick))) return { error: 'none left' };
    const fresh = await this.store.get(u.name_lower);
    return { item: itemInfo(pick.type, pick.id), me: this.public(fresh) };
  }

  // ------------------------------------------------------------ HTTP
  async handle(req, res, url) {
    // stringify first: if it throws, the catch below can still answer (headers not sent yet)
    const send = (code, obj) => { const s = JSON.stringify(obj); res.writeHead(code, { 'content-type': 'application/json', 'cache-control': 'no-store' }); res.end(s); };
    try {
      const body = req.method === 'POST' ? await readJson(req) : {};
      const auth = (req.headers.authorization || '').replace(/^Bearer /, '');
      const ip = req.socket.remoteAddress || '?';
      if (url.startsWith('/api/story/')) return await storyApi(this, url, body, auth, send);
      switch (url) {
        case '/api/register':
        case '/api/login': {
          if (this.limited(ip)) return send(429, { error: 'slow down' });
          const r = url === '/api/register' ? await this.register(body.name, body.pass) : await this.login(body.name, body.pass);
          return send(r.error ? 400 : 200, r);
        }
        case '/api/me': {
          const u = await this.verify(auth);
          return u ? send(200, { me: this.public(u) }) : send(401, { error: 'not logged in' });
        }
        case '/api/profile': {
          const u = await this.verify(auth);
          if (!u) return send(401, { error: 'not logged in' });
          if (!body.profile || typeof body.profile !== 'object') return send(400, { error: 'bad profile' });
          // JSON.parse takes nesting JSON.stringify can't write back (that would break every later save): it must
          // serialize, and fit a name card (up to 24 KB, see cleanCard) plus loadout, skins, look and settings
          let s = null;
          try { s = JSON.stringify(body.profile); } catch { /* too deep */ }
          if (!s || s.length > 40000) return send(400, { error: 'bad profile' });
          await this.store.setProfile(u.name_lower, body.profile);
          return send(200, { ok: true });
        }
        case '/api/roll': {
          const u = await this.verify(auth);
          if (!u) return send(401, { error: 'log in to roll' });
          const r = await this.roll(u, body.kind);
          return send(r.error ? 400 : 200, r);
        }
        case '/api/leaderboard': return send(200, await this.leaderboard());
        case '/api/status': return send(200, { store: this.store.kind });
        default: return send(404, { error: 'nope' });
      }
    } catch (e) {
      console.error('api error', url, e.message);
      if (!res.headersSent) send(500, { error: 'server error' });
    }
  }
}

// the story save fallback lives in inv.story (server/story.js): it's not a cosmetic, keep it out of /api/me
function pubInv(inv) { if (!inv || !inv.story) return inv || {}; const { story, ...rest } = inv; return rest; }

function readJson(req) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on('data', (c) => {
      size += c.length;
      if (size > 64 * 1024) { reject(new Error('too big')); req.destroy(); return; }
      chunks.push(c);
    });
    req.on('end', () => { try { resolve(JSON.parse(Buffer.concat(chunks).toString() || '{}')); } catch { resolve({}); } });
    req.on('error', reject);
  });
}
