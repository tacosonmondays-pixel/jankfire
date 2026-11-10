// Accounts: register / login with username + password, signed session tokens, profile sync,
// stats, levels and leaderboards. All HTTP, all JSON, under /api/*.
import crypto from 'node:crypto';
import { promisify } from 'node:util';
import { STAT_KEYS } from './store.js';
import { rollPick, itemInfo, CONTAINERS } from '../shared/cosmetics.js';
import { achievementsFrom } from '../shared/looks.js';
import { catsOf } from '../shared/secrets.js';
import { storyApi } from './story.js'; // OVERDUE save slots (/api/story/*)
import { MODE_STATS, modeBoard, boardValue } from '../shared/modestats.js'; // per-mode leaderboards
import { giftsDue, ROLL_BATCH_MAX } from '../shared/gifts.js'; // free containers from the management, once per account

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
    this.batchT = new Map(); // name -> last batch open (one every 700 ms)
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
    const [u, gifts] = await this.giveGifts(await this.store.get(name.toLowerCase())); // signing up while a gift runs: it's yours too
    return { token: await this.sign(u.name_lower), me: this.public(u), gifts };
  }

  async login(name, pass) {
    const u = typeof name === 'string' ? await this.store.get(name.toLowerCase()) : null;
    if (!u || typeof pass !== 'string') return { error: 'wrong username or password' };
    const hash = await scrypt(pass, u.salt, 32);
    if (!crypto.timingSafeEqual(hash, Buffer.from(u.hash, 'hex'))) return { error: 'wrong username or password' };
    const [fresh, gifts] = await this.giveGifts(u);
    return { token: await this.sign(u.name_lower), me: this.public(fresh), gifts };
  }

  // hand out any gift this account hasn't had (shared/gifts.js). the store makes each one once-only, even for two
  // logins at the same moment. returns [the account as it is now, the gifts just given]
  async giveGifts(u) {
    if (!u) return [u, []];
    const out = [];
    for (const g of giftsDue(u.inv)) if (await this.store.claimGift(u.name_lower, g)) out.push({ id: g.id, title: g.title, rolls: g.rolls });
    return [out.length ? await this.store.get(u.name_lower) : u, out];
  }

  async leaderboard() {
    const [wins, kills, speed, wave, xp] = await Promise.all([
      this.store.top('wins'), this.store.top('kills'), this.store.top('top_speed'), this.store.top('best_wave'), this.store.top('xp'),
    ]);
    const lv = (rows) => rows.map((r) => ({ ...r, level: levelOf(r.xp) }));
    return { wins: lv(wins), kills: lv(kills), speed: lv(speed), wave: lv(wave), xp: lv(xp) };
  }

  // one mode's boards (/api/leaderboard/<mode>) or one board (/api/leaderboard/<mode>/<board>). a ratio board ranks
  // the top 200 by its minimum's stat, so it only lists people who played enough. cached 20 s per mode
  async modeBoard(mode, id) {
    const M = MODE_STATS[mode], boards = id ? [modeBoard(mode, id)] : M.boards, n = Date.now();
    this.mbCache ||= new Map();
    const key = mode + '/' + (id || ''), hit = this.mbCache.get(key);
    if (hit && n - hit.t < 20000) return hit.v;
    const out = { mode, name: M.name, boards: {} };
    await Promise.all(boards.map(async (b) => {
      const rows = await this.store.modeRows(mode, b.ratio ? (b.min || b.ratio)[0] : b.key, b.ratio ? 200 : 15);
      out.boards[b.id] = rows.map((r) => ({ name: r.name, level: levelOf(r.xp), value: boardValue(b, r.ms) })).filter((r) => r.value != null)
        .sort((a, c) => c.value - a.value).slice(0, 15);
    }));
    this.mbCache.set(key, { t: n, v: out });
    return out;
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

  // open n containers of one kind in one go (OPEN x5 / x10 / ALL): the same picks as one at a time (rollPick, never
  // something you already have, and never the same thing twice in one batch); when a kind runs out of new stuff each
  // extra one is +100 xp, like a single open. one store write for all of them
  async rollMany(u, kind, n) {
    if (typeof kind !== 'string' || !Object.hasOwn(CONTAINERS, kind)) return { error: 'open crates, duffel bags or boxes' };
    if (!Number.isInteger(n) || n < 1 || n > ROLL_BATCH_MAX) return { error: `open 1 to ${ROLL_BATCH_MAX} at a time` };
    const c = CONTAINERS[kind], have = u[c.field] || 0;
    if (n > have) return { error: `you only have ${have} ${have === 1 ? c.name.toLowerCase() : c.plural.toLowerCase()}` };
    const now = Date.now();
    if (now - (this.batchT.get(u.name_lower) || 0) < 700) return { error: 'slow down', code: 429 };
    this.batchT.set(u.name_lower, now);
    if (this.batchT.size > 5000) this.batchT.clear();
    const inv = {}; // what you'd own after each pick (so one batch never repeats itself)
    for (const t of c.types) inv[t] = [...((u.inv && Array.isArray(u.inv[t])) ? u.inv[t] : [])];
    const picks = [];
    let xp = 0;
    for (let i = 0; i < n; i++) {
      const p = rollPick(inv, Math.random, c.types);
      if (p) { inv[p.type].push(p.id); picks.push(p); } else { picks.push(null); xp += 100; }
    }
    if (!(await this.store.spendRolls(u.name_lower, kind, n, picks))) return { error: 'none left' };
    if (xp) await this.store.addStats(u.name_lower, { xp });
    const fresh = await this.store.get(u.name_lower);
    return { items: picks.map((p) => (p ? itemInfo(p.type, p.id) : null)), xp, me: this.public(fresh) };
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
          const u0 = await this.verify(auth);
          if (!u0) return send(401, { error: 'not logged in' });
          const [u, gifts] = await this.giveGifts(u0); // coming back with a saved login: gifts land here
          return send(200, { me: this.public(u), gifts });
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
        case '/api/rollmany': {
          const u = await this.verify(auth);
          if (!u) return send(401, { error: 'log in to open containers' });
          const r = await this.rollMany(u, body.kind, body.n);
          return send(r.error ? r.code || 400 : 200, r);
        }
        case '/api/leaderboard': return send(200, await this.leaderboard());
        case '/api/leaderboard/modes': return send(200, Object.fromEntries(Object.entries(MODE_STATS).map(([m, M]) => [m, { name: M.name, boards: M.boards.map((b) => [b.id, b.title]) }])));
        case '/api/status': return send(200, { store: this.store.kind });
        default: {
          const lb = /^\/api\/leaderboard\/([a-z]{1,8})(?:\/([a-z0-9]{1,12}))?$/.exec(url); // per-mode boards: mode + board checked against MODE_STATS
          if (lb) {
            if (!Object.hasOwn(MODE_STATS, lb[1])) return send(400, { error: 'unknown mode' });
            if (lb[2] && !modeBoard(lb[1], lb[2])) return send(400, { error: 'unknown board' });
            return send(200, await this.modeBoard(lb[1], lb[2]));
          }
          return send(404, { error: 'nope' });
        }
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
