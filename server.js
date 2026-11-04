// JANKFIRE server: serves the client and runs every match over WebSockets.
// Rooms: one shared Online room, one shared Coop room, and private Bots / Training rooms per player.
// Human movement is client-authoritative (it's a jank game). The server owns damage, kills, projectiles,
// peels, black holes, reverse cards, respawns, bots, coop waves and lobby settings.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import os from 'node:os';
import { spawn } from 'node:child_process';
import { WebSocketServer } from 'ws';
import { makeStore } from './server/store.js';
import { Accounts, levelOf } from './server/accounts.js';
import { ownedSkin, ownedKill, randomContainer, CONTAINERS, COSMETICS } from './shared/cosmetics.js';
import { validLook, achievementsFrom, ACHIEVEMENTS } from './shared/looks.js';
import { STAT_KEYS } from './server/store.js';
import { MAPS, MAP_ORDER } from './shared/map.js';
import { GAMES, GAME_ORDER, TEAMS, TARGETS, BOMB, TAG_LIFE, VOTE_MS, siteAt, mapsFor } from './shared/modes.js';
import { WEAPONS, HOOK, HIPFIRE, BOT_DIFF, MODES, STREAKS, FLAGS, ARROW_TIPS, ITEMS, validStreaks, fireRate } from './shared/weapons.js';
import { stepProjectile, rayBox, raycast, playerBoxes, movePlayer, PH } from './shared/physics.js';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
// secrets like SUPABASE_SERVICE_KEY can live in a .env file next to server.js (never commit it, never ship it in the exe)
try { if (fs.existsSync(path.join(ROOT, '.env'))) process.loadEnvFile(path.join(ROOT, '.env')); } catch (e) { console.warn('could not read .env:', e.message); }
const PORT = Number(process.env.PORT) || 3000;
const store = makeStore(ROOT);
const accounts = new Accounts(store);

// ---------------------------------------------------------------- static files
const ROUTES = [
  ['/vendor/three/', path.join(ROOT, 'node_modules/three/')],
  ['/shared/', path.join(ROOT, 'shared/')],
  ['/', path.join(ROOT, 'public/')],
];
const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css',
  '.json': 'application/json', '.glb': 'model/gltf-binary', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.wav': 'audio/wav', '.mp3': 'audio/mpeg',
  '.webmanifest': 'application/manifest+json',
};

function modelList() {
  let cfg = [];
  try { cfg = JSON.parse(fs.readFileSync(path.join(ROOT, 'tools/models.json'), 'utf8')); } catch { /* none */ }
  let files = [];
  try { files = fs.readdirSync(path.join(ROOT, 'public/models')).filter((f) => f.endsWith('.glb')); } catch { /* none */ }
  return files.map((f) => {
    const id = f.slice(0, -4);
    const c = cfg.find((x) => x.id === id) || {};
    return { id, url: '/models/' + f, size: c.size, rot: c.rot };
  });
}

function serve(req, res) {
  let url;
  try { url = decodeURIComponent(new URL(req.url, 'http://x').pathname); } catch { res.writeHead(400).end(); return; }
  if (url === '/models/list') {
    res.writeHead(200, { 'content-type': 'application/json', 'cache-control': 'no-cache' });
    res.end(JSON.stringify(modelList()));
    return;
  }
  if (url === '/health') { res.writeHead(200).end('ok ' + humans()); return; }
  if (url.startsWith('/api/')) { accounts.handle(req, res, url); return; }
  for (const [prefix, dir] of ROUTES) {
    if (!url.startsWith(prefix)) continue;
    const file = path.normalize(path.join(dir, url.slice(prefix.length) || 'index.html'));
    if (!file.startsWith(dir)) { res.writeHead(403).end(); return; }
    fs.stat(file, (err, st) => {
      if (err || !st.isFile()) { res.writeHead(404).end('404'); return; }
      res.writeHead(200, { 'content-type': MIME[path.extname(file)] || 'application/octet-stream', 'cache-control': 'no-cache' });
      fs.createReadStream(file).pipe(res);
    });
    return;
  }
  res.writeHead(404).end();
}

const server = http.createServer(serve);
// name cards make some messages chunky: those (and replays) get compressed, the 20 Hz snapshots don't
const wss = new WebSocketServer({ server, path: '/ws', maxPayload: 40000, perMessageDeflate: { threshold: 4096 } });

// ---------------------------------------------------------------- helpers
const COLORS = ['#ff4fd8', '#4fd8ff', '#ffe14d', '#7dff4f', '#ff7a1a', '#b07dff', '#ff4f4f', '#4fffb0', '#ffffff', '#ff9ad5'];
const DEFAULT_NAMES = ['player', 'guy', 'someone', 'nobody', 'dude', 'person'];
const BOT_NAMES = ['Gary', 'Linda', 'Steve', 'Brenda', 'Kevin', 'Doug', 'Karen', 'Phil', 'Tina', 'Rick', 'Deb', 'Carl', 'Pam', 'Todd', 'Barb', 'Chad'];
const BOT_GUNS = ['ar', 'ar', 'smg', 'shotgun', 'shotgun', 'sniper', 'chicken', 'banana', 'minigun', 'revolver', 'redline', 'marbles'];
BOT_GUNS.push('shredder'); // bots suck too (botShred)
const SKIN_F = ['default', 'default', 'gold', 'chrome', 'pink', 'camo', 'neon', 'rainbow', 'galaxy', 'lava', 'missing', 'tiger', 'fade', 'carbon', 'tape'];
const SKIN_H = ['none', 'none', 'none', 'tophat', 'party', 'crown', 'cowboy', 'propeller', 'cone', 'eyes', 'duck'];
const SKIN_E = ['none', 'none', 'none', 'sparkles', 'flames', 'money', 'smoke'];
const SKIN_KEYS = { f: /^[a-z_]{1,24}$/ };

const now = () => Date.now();
const r2 = (x) => Math.round(x * 100) / 100;
const dist3 = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
const clampInt = (x, lo, hi) => Math.max(lo, Math.min(hi, Math.floor(Number(x) || 0)));
const pick = (a) => a[(Math.random() * a.length) | 0];
function vec3(a) {
  if (!Array.isArray(a) || a.length !== 3) return null;
  for (const x of a) if (typeof x !== 'number' || !Number.isFinite(x) || Math.abs(x) > 1e6) return null;
  return a.slice();
}
function norm(a) {
  if (!a) return null;
  const l = Math.hypot(a[0], a[1], a[2]);
  return l > 1e-6 ? [a[0] / l, a[1] / l, a[2] / l] : null;
}
function lerpAngle(a, b, t) {
  let d = b - a;
  while (d > Math.PI) d -= Math.PI * 2;
  while (d < -Math.PI) d += Math.PI * 2;
  return a + d * Math.min(1, t);
}
function spreadDir(d, s) {
  if (!s) return d;
  const v = [d[0] + (Math.random() - 0.5) * 2 * s, d[1] + (Math.random() - 0.5) * 2 * s, d[2] + (Math.random() - 0.5) * 2 * s];
  return norm(v) || d;
}
const center = (p) => [p.pos[0], p.pos[1] + 0.9, p.pos[2]];
const eyeOf = (p) => [p.pos[0], p.pos[1] + PH.eye, p.pos[2]];
const lookOf = (p) => { const cp = Math.cos(p.pitch || 0); return [-Math.sin(p.yaw || 0) * cp, Math.sin(p.pitch || 0), -Math.cos(p.yaw || 0) * cp]; };
function clean(s, max) { return String(s || '').replace(/[<>&"'`\u0000-\u001f]/g, '').trim().slice(0, max); }
function cleanSkins(s) {
  const out = {};
  if (!s || typeof s !== 'object') return out;
  for (const id of Object.keys(WEAPONS)) {
    const v = s[id];
    if (Array.isArray(v) && (v.length === 3 || v.length === 4) && v.every((x) => typeof x === 'string' && SKIN_KEYS.f.test(x))) out[id] = v.length === 3 ? [...v, 'default'] : v.slice();
  }
  return out;
}
function enforceSkins(skins, inv) {
  const out = {};
  for (const [id, sk] of Object.entries(skins)) out[id] = ownedSkin(sk, inv, id);
  return out;
}
if (process.env.JF_STREAK) STREAKS.scythe.kills = Number(process.env.JF_STREAK) || STREAKS.scythe.kills;
const ROUND = { ffa: { kills: 20, time: 360 }, bots: { kills: 15, time: 300 } };
if (process.env.JF_ROUND_KILLS) for (const r of Object.values(ROUND)) r.kills = Number(process.env.JF_ROUND_KILLS) || r.kills;
// test knobs for plant & defuse (short rounds / fuse / match)
if (process.env.JF_BOMB_WINS) BOMB.wins = Number(process.env.JF_BOMB_WINS) || BOMB.wins;
if (process.env.JF_BOMB_FUSE) BOMB.fuse = Number(process.env.JF_BOMB_FUSE) || BOMB.fuse;
if (process.env.JF_BOMB_ROUND) BOMB.roundTime = Number(process.env.JF_BOMB_ROUND) || BOMB.roundTime;
if (process.env.JF_TARGET) for (const t of Object.values(TARGETS)) for (const k of Object.keys(t)) t[k] = Number(process.env.JF_TARGET);
function randomSkins() {
  const out = {};
  for (const id of Object.keys(WEAPONS)) if (Math.random() < 0.6) out[id] = [pick(SKIN_F), pick(SKIN_H), pick(SKIN_E), id === 'knife' ? pick(['default', 'knife_karambit', 'knife_butterfly', 'knife_switch', 'knife_cleaver']) : 'default'];
  return out;
}
function send(p, obj) { if (p.ws && p.ws.readyState === 1) p.ws.send(JSON.stringify(obj)); }

const TIP_IDS = Object.keys(ARROW_TIPS);
const KILL_IDS = Object.keys(COSMETICS.kill).filter((k) => k !== 'none');
// name cards: a small picture you drew or uploaded, as a data url. anything else is dropped.
const CARD_RE = /^data:image\/(jpeg|png|webp);base64,[A-Za-z0-9+/]+=*$/;
function cleanCard(c) { return typeof c === 'string' && c.length <= 24000 && CARD_RE.test(c) ? c : ''; }
// replays: the server keeps the last few seconds of everything so it can send the play of the round
const REC_T = new Set(['kill', 'boom', 'fx', 'pd', 'he']);
const REC_FX = new Set(['shot', 'swing', 'tbag', 'reflect']);
const REC_MS = 12000;
function newDeck() {
  const d = [];
  for (const s of ['h', 's', 'c', 'd']) for (let r = 1; r <= 13; r++) d.push(s + r);
  d.push('j0', 'j0');
  for (let i = d.length - 1; i > 0; i--) { const j = (Math.random() * (i + 1)) | 0; [d[i], d[j]] = [d[j], d[i]]; }
  return d;
}
function deal(p) {
  if (!p.deck || p.deck.length < 5) p.deck = newDeck();
  p.hand = p.deck.splice(0, 5);
  send(p, { t: 'hand', hand: p.hand, left: p.deck.length });
}

let nextId = 1;
const rooms = new Map();
const humans = () => { let n = 0; for (const r of rooms.values()) for (const p of r.players.values()) if (!p.isBot) n++; return n; };

// ================================================================ ROOM
class Room {
  constructor(id, mode) {
    this.id = id;
    this.mode = mode;
    this.players = new Map();
    this.projectiles = new Map();
    this.peels = new Map();
    this.holes = new Map();
    this.clouds = new Map(); this.nextCloud = 1;
    this.nextProj = 1; this.nextPeel = 1; this.nextHole = 1;
    this.rec = { frames: [], ev: [] };
    this.game = 'dm'; // dm / tdm / tags / bomb (Online + Bots rooms)
    this.score = { 1: 0, 2: 0 };
    this.tags = new Map(); this.nextTag = 1;
    this.bomb = null;
    this.vote = null;
    this.bubbles = new Map(); this.nextBub = 1;
    this.cfg = { map: mode === 'training' ? 'range' : mode === 'coop' ? 'warehouse' : 'islands', hip: 'normal', bots: 5, diff: 'normal' };
    this.wave = 0; this.toSpawn = 0; this.interUntil = 0;
    this.round = ROUND[mode] ? { target: ROUND[mode].kills, ends: now() + ROUND[mode].time * 1000, over: false, next: 0 } : null;
    if (mode === 'coop') this.interUntil = now() + 4000;
  }
  get map() { return MAPS[this.cfg.map]; }
  get boxes() { return this.map.boxes; }

  broadcast(obj, exceptId) {
    const s = JSON.stringify(obj);
    if (REC_T.has(obj.t) && (obj.t !== 'fx' || REC_FX.has(obj.k)) && (obj.t !== 'pd' || obj.x)) this.rec.ev.push({ s: now(), m: obj });
    for (const p of this.players.values()) if (p.id !== exceptId && p.ws && p.ws.readyState === 1) p.ws.send(s);
  }
  humans() { return [...this.players.values()].filter((p) => !p.isBot); }
  teamsOn() { return (this.mode === 'ffa' || this.mode === 'bots') && !!GAMES[this.game].teams; }
  fighters() { return [...this.players.values()].filter((p) => !(p.isBot && p.ai && p.ai.dummy)); }
  // even teams, humans spread first
  assignTeams() {
    const list = this.fighters().sort((a, b) => (a.isBot - b.isBot) || (Math.random() - 0.5));
    let i = 0;
    for (const p of list) {
      if (!p.ownColor) p.ownColor = p.color;
      if (this.teamsOn()) { p.team = (i++ % 2) + 1; p.color = TEAMS[p.team].color; }
      else { p.team = 0; p.color = (p.look && p.look.color) || p.ownColor; }
    }
    this.broadcast({ t: 'teams', game: this.game, list: list.map((p) => [p.id, p.team, p.color]) });
  }
  teamFor() {
    const c = { 1: 0, 2: 0 };
    for (const p of this.fighters()) if (p.team) c[p.team]++;
    return c[1] <= c[2] ? 1 : 2;
  }
  // randomizer: a fresh random loadout every life (null = back to your own)
  randomLoadout() {
    const lo = {};
    for (const slot of ['primary', 'secondary', 'melee']) lo[slot] = pick(Object.keys(WEAPONS).filter((id) => WEAPONS[id].slot === slot));
    return lo;
  }
  sendLoadout(p) {
    if (p.isBot) { if (GAMES[this.game].random && !p.ai.dummy) { p.w = pick(BOT_GUNS); p.ai.ammo = WEAPONS[p.w].mag || 1; } return; }
    const rnd = (this.mode === 'ffa' || this.mode === 'bots') && GAMES[this.game].random;
    if (rnd) { p.forced = true; send(p, { t: 'loadout', lo: this.randomLoadout() }); }
    else if (p.forced) { p.forced = false; send(p, { t: 'loadout', lo: null }); }
  }
  joinTeam(p) {
    if (!p.ownColor) p.ownColor = p.color;
    if (!this.teamsOn()) { p.team = 0; return; }
    p.team = this.teamFor();
    p.color = TEAMS[p.team].color;
  }

  pickSpawn(forBot, who) {
    let spawns = this.map.spawns;
    const ts = this.map.teamSpawns;
    if (who && who.team && this.teamsOn() && ts) {
      const attacking = this.game === 'bomb' ? who.team === (this.bomb ? this.bomb.att : 1) : who.team === 1;
      spawns = attacking ? ts.att : ts.def;
    }
    let best = spawns[0], bestD = -1;
    for (const s of spawns) {
      let d = 1e9;
      for (const p of this.players.values()) if (p.alive && p !== who && (!forBot || !p.isBot) && !(who && who.team && p.team === who.team)) d = Math.min(d, dist3(s, p.pos));
      d += Math.random() * 15;
      if (d > bestD) { bestD = d; best = s; }
    }
    return best.slice();
  }

  newPlayer(name, opts = {}) {
    const id = nextId++;
    const used = new Set([...this.players.values()].map((p) => p.color));
    const color = opts.color || COLORS.find((c) => !used.has(c)) || COLORS[id % COLORS.length];
    const pos = opts.pos ? opts.pos.slice() : this.pickSpawn(opts.isBot);
    return {
      id, ws: opts.ws || null, room: this, name, color, pos, vel: [0, 0, 0], yaw: Math.random() * 6, pitch: 0,
      w: opts.w || 'ar', hp: 100, alive: true, respawnAt: 0, kills: 0, deaths: 0, seq: 1, spawnT: now(), reverseUntil: 0,
      lastAttacker: 0, lastAttackW: null, lastAttackT: 0, lastFire: {}, pair: new Map(), g: null, f: 0,
      chatT: 0, coughT: 0, cfgT: 0, skinT: 0, skins: opts.skins || {}, isBot: !!opts.isBot, ai: opts.ai || null,
      onGround: false, slipUntil: 0, acct: opts.acct || null, level: opts.level || 0,
    };
  }
  info(p) { return { id: p.id, name: p.name, color: p.color, skins: p.skins, bot: p.isBot, level: p.level, look: p.look, card: p.card || '', team: p.team || 0 }; }

  addHuman(ws, m) {
    if (this.mode === 'bots' && m.cfg && typeof m.cfg === 'object' && !this.humans().length) {
      const c = m.cfg;
      if (MAPS[c.map] && MAP_ORDER.includes(c.map)) this.cfg.map = c.map;
      if (HIPFIRE[c.hip]) this.cfg.hip = c.hip;
      if (BOT_DIFF[c.diff]) this.cfg.diff = c.diff;
      if (c.bots != null) this.cfg.bots = clampInt(c.bots, 0, 12);
    }
    const name = m._name || clean(m.name, 16) || pick(DEFAULT_NAMES) + nextId;
    const inv = m._inv || {};
    const p = this.newPlayer(name, { ws, skins: enforceSkins(cleanSkins(m.skins), inv), acct: m._acct, level: m._level });
    p.inv = inv;
    p.tip = pick(TIP_IDS);
    p.look = validLook(m.look, m._achs || new Set());
    if (p.look.color) p.color = p.look.color;
    p.card = cleanCard(m.card);
    p.streaks = validStreaks(m.streaks);
    p.kfx = ownedKill(m.kfx, inv);
    p.kc = !!m.kc;
    if (this.mode === 'bots' && m.cfg && GAMES[m.cfg.game] && !this.humans().length) this.setGame(m.cfg.game);
    this.joinTeam(p);
    if (p.team) p.pos = this.pickSpawn(false, p);
    this.players.set(p.id, p);
    send(p, {
      t: 'welcome', id: p.id, name, color: p.color, pos: p.pos, q: p.seq, mode: this.mode, cfg: this.cfg,
      players: [...this.players.values()].filter((o) => o !== p).map((o) => this.info(o)),
      peels: [...this.peels.values()].map((pl) => ({ id: pl.id, p: pl.p })),
      projs: [...this.projectiles.values()].map((pr) => ({ id: pr.id, k: pr.k, p: pr.p, v: pr.v, o: pr.o })),
      holes: [...this.holes.values()].map((h) => ({ id: h.id, p: h.p, o: h.o, big: h.big, age: (now() - h.born) / 1000 })),
      wave: this.waveInfo(), level: p.level, account: !!p.acct, round: this.roundInfo(),
      bubbles: [...this.bubbles.values()].map((b) => ({ id: b.id, p: b.p, r: b.r, left: b.until - now() })),
      kat: [...this.players.values()].filter((o) => o.kat).map((o) => [o.id, o.kat]),
      game: this.game, team: p.team || 0, tags: [...this.tags.values()].map((g) => ({ id: g.id, p: g.p, team: g.team })), vote: this.voteInfo(),
    });
    this.broadcast({ t: 'pj', ...this.info(p) }, p.id);
    send(p, { t: 'tip', tip: p.tip });
    deal(p);
    this.sendLoadout(p);
    if (this.mode === 'ffa' || this.mode === 'coop') this.broadcast({ t: 'chat', id: 0, m: `${name} joined` });
    if (this.mode === 'bots') this.fillBots();
    if (this.mode === 'bots' && this.humans().length === 1 && this.game !== 'dm') this.startRound();
    if (this.mode === 'training') this.spawnDummies();
    console.log(`+ ${name} (#${p.id}) -> ${this.id}`);
    return p;
  }

  remove(p) {
    flushStats(p);
    if (this.bomb && this.bomb.carrier === p.id) this.dropBomb(p.pos);
    this.players.delete(p.id);
    for (const pr of this.projectiles.values()) if (pr.k === 'slipper' && pr.o === p.id) this.removeProj(pr);
    this.broadcast({ t: 'pl', id: p.id });
    if (!p.isBot && (this.mode === 'ffa' || this.mode === 'coop')) this.broadcast({ t: 'chat', id: 0, m: `${p.name} left` });
    if (!this.humans().length) rooms.delete(this.id);
  }

  // ---------------------------------------------------------- bots
  addBot(opts = {}) {
    const diff = this.cfg.diff;
    const b = this.newPlayer(opts.dummy ? 'Dummy' : `${pick(BOT_NAMES)} [bot]`, {
      isBot: true, pos: opts.pos, color: opts.dummy ? '#cccccc' : '#aaaaaa',
      w: opts.dummy ? 'ar' : pick(BOT_GUNS), skins: opts.dummy ? {} : randomSkins(),
      ai: { diff, target: 0, retarget: 0, nextShot: now() + 1500, seenAt: 0, ammo: 0, reloadUntil: 0, jumpT: 0, wp: null, seed: Math.random() * 100, dummy: opts.dummy || null, strafeDir: 1 },
    });
    b.ai.ammo = WEAPONS[b.w].mag || 1;
    if (!opts.dummy) { this.joinTeam(b); if (b.team) b.pos = this.pickSpawn(true, b); }
    this.players.set(b.id, b);
    this.broadcast({ t: 'pj', ...this.info(b) });
    return b;
  }
  removeBots() { for (const b of [...this.players.values()]) if (b.isBot) this.remove(b); }
  fillBots() {
    const want = clampInt(this.cfg.bots, 0, 12);
    const bots = [...this.players.values()].filter((p) => p.isBot);
    for (let i = bots.length; i < want; i++) this.addBot();
    for (let i = want; i < bots.length; i++) this.remove(bots[i]);
  }
  spawnDummies() {
    if ([...this.players.values()].some((p) => p.isBot)) return;
    const list = this.map.dummies || this.map.spawns.map((s) => ({ p: s }));
    for (const d of list) this.addBot({ dummy: { home: d.p.slice(), move: d.move || 0, phase: Math.random() * 6 }, pos: d.p });
  }

  waveInfo() { return this.mode === 'coop' ? { n: this.wave, left: this.toSpawn + [...this.players.values()].filter((p) => p.isBot && p.alive).length, inter: Math.max(0, this.interUntil - now()) } : null; }
  tickWaves() {
    if (this.mode !== 'coop' || !this.humans().length) return;
    const n = now();
    const alive = [...this.players.values()].filter((p) => p.isBot);
    if (this.interUntil) {
      if (n < this.interUntil) return;
      this.interUntil = 0;
      this.wave++;
      this.toSpawn = Math.min(30, 2 + this.wave * 2);
      this.broadcast({ t: 'wave', ...this.waveInfo(), start: 1 });
    }
    if (this.toSpawn > 0 && alive.length < Math.min(10, 3 + this.wave)) {
      this.toSpawn--;
      this.addBot({ pos: this.pickSpawn(true) });
      this.broadcast({ t: 'wave', ...this.waveInfo() });
    }
    if (this.toSpawn === 0 && !alive.length) {
      this.interUntil = n + 6000;
      for (const h of this.humans()) {
        stat(h, 'best_wave', this.wave); stat(h, 'xp', 10 + this.wave * 5);
        if (this.wave % 5 === 0 && h.acct) { const kind = randomContainer(); store.grantRolls(h.acct.n, kind, 1).catch(() => {}); send(h, { t: 'roll+', n: 1, kind, why: `cleared wave ${this.wave}` }); }
      }
      this.broadcast({ t: 'wave', ...this.waveInfo(), done: 1 });
    }
  }

  botTarget(b) {
    let best = null, bestD = 1e9;
    for (const t of this.players.values()) {
      if (t === b || !t.alive || (t.isBot && (this.mode === 'coop' || t.ai.dummy))) continue;
      if (this.teamsOn() && t.team === b.team) continue;
      const d = dist3(t.pos, b.pos);
      const vis = !raycast(eyeOf(b), norm([t.pos[0] - b.pos[0], t.pos[1] + 1 - b.pos[1] - PH.eye, t.pos[2] - b.pos[2]]) || [0, 0, 1], d, this.boxes);
      const score = d * (vis ? 1 : 2.5);
      if (score < bestD) { bestD = score; best = t; }
    }
    return best;
  }

  botThink(b, dt) {
    const ai = b.ai, n = now(), D = BOT_DIFF[ai.diff] || BOT_DIFF.normal;
    if (b.sleepUntil > n) return { wx: 0, wz: 0, jump: false };
    const boxes = this.boxes;
    if (ai.dummy) {
      const d = ai.dummy;
      if (d.move) {
        const x = d.home[0] + Math.sin(n * 0.0012 + d.phase) * d.move;
        b.vel[0] = (x - b.pos[0]) * 8; b.vel[2] = (d.home[2] - b.pos[2]) * 8;
      }
      b.yaw = Math.PI;
      return { wx: 0, wz: 0, jump: false };
    }
    if (n > ai.retarget) { const t = this.botTarget(b); ai.target = t ? t.id : 0; ai.retarget = n + 400 + Math.random() * 600; }
    const t = this.players.get(ai.target);
    let wx = 0, wz = 0, jump = false;
    const w = WEAPONS[b.w];
    const pref = b.w === 'sniper' ? [25, 60] : b.w === 'shotgun' ? [3, 9] : b.w === 'marbles' ? [1.5, 4] : b.w === 'chicken' ? [10, 30] : b.w === 'shredder' ? [1.5, 9] : [7, 22];
    if (t && t.alive) {
      const e = eyeOf(b), tc = [t.pos[0], t.pos[1] + 1.1, t.pos[2]];
      const dx = tc[0] - e[0], dy = tc[1] - e[1], dz = tc[2] - e[2];
      const hd = Math.hypot(dx, dz), dist = Math.hypot(dx, dy, dz);
      const vis = !raycast(e, [dx / dist, dy / dist, dz / dist], dist, boxes);
      if (vis && !ai.seenAt) ai.seenAt = n;
      if (!vis) ai.seenAt = 0;
      const yaw = Math.atan2(-dx, -dz), pitch = Math.atan2(dy, hd);
      b.yaw = lerpAngle(b.yaw, yaw, D.turn * dt);
      b.pitch += (pitch - b.pitch) * Math.min(1, D.turn * dt);
      const fx = dx / (hd || 1), fz = dz / (hd || 1);
      if (dist > pref[1] || !vis) { wx += fx; wz += fz; } else if (dist < pref[0]) { wx -= fx; wz -= fz; }
      if (Math.random() < dt * 0.6) ai.strafeDir *= -1;
      wx += -fz * ai.strafeDir * 0.8; wz += fx * ai.strafeDir * 0.8;
      let ang = Math.abs(b.yaw - yaw) % (Math.PI * 2); if (ang > Math.PI) ang = Math.PI * 2 - ang;
      if (vis && ai.seenAt && n - ai.seenAt > D.react && ang < 0.25 && n >= ai.nextShot && n >= ai.reloadUntil && dist < (w.range || 60)) this.botFire(b, t, D);
      if (b.onGround && Math.random() < dt * (dist < 15 ? 1.2 : 0.4)) jump = true;
    } else {
      if (!ai.wp || dist3(ai.wp, b.pos) < 4) ai.wp = pick(this.map.spawns);
      const dx = ai.wp[0] - b.pos[0], dz = ai.wp[2] - b.pos[2], l = Math.hypot(dx, dz) || 1;
      wx = dx / l; wz = dz / l;
      b.yaw = lerpAngle(b.yaw, Math.atan2(-wx, -wz), 3 * dt);
      b.pitch *= 0.95;
    }
    // objectives: carry the bomb to a site and plant it, go defuse it, grab tags
    const goal = this.botGoal(b);
    if (goal) {
      const gx = goal.p[0] - b.pos[0], gz = goal.p[2] - b.pos[2], gl = Math.hypot(gx, gz);
      if (goal.use && gl < goal.r) { wx = 0; wz = 0; jump = false; this.tryUse(b); }
      else if (goal.force || !t || !t.alive || !ai.seenAt) { wx = gx / (gl || 1); wz = gz / (gl || 1); }
    }
    // grappling: chase people who are far / up high / out of sight, save yourself when falling, show off sometimes
    if (!ai.hook && n >= (ai.nextHook || 0) && this.mode !== 'training') {
      const skill = ai.diff === 'easy' ? 0.35 : ai.diff === 'hard' ? 1 : 0.7;
      const below = !b.onGround && !raycast([b.pos[0], b.pos[1] + 0.5, b.pos[2]], [0, -1, 0], 40, boxes);
      let want = null;
      if (below && (b.vel[1] < -4 || b.pos[1] < this.map.killY + 25)) { // falling into the void: hook back toward the middle, up high
        const c = this.map.spawns ? this.map.spawns[0] : [0, 0, 0];
        want = [c[0] - b.pos[0], 18 + Math.max(0, c[1] - b.pos[1]), c[2] - b.pos[2]];
      } else if (t && t.alive && Math.random() < skill) {
        const dx = t.pos[0] - b.pos[0], dy = t.pos[1] - b.pos[1], dz = t.pos[2] - b.pos[2];
        const hd = Math.hypot(dx, dz);
        if (hd > pref[1] + 10 || dy > 4 || !ai.seenAt) want = [dx, dy + hd * 0.35 + 6, dz];
      } else if (!t && Math.random() < 0.25 * skill) {
        const a = Math.random() * Math.PI * 2;
        want = [Math.cos(a) * 20, 14 + Math.random() * 10, Math.sin(a) * 20];
      }
      ai.nextHook = n + (want ? 700 : 1800) + Math.random() * 1200 / skill;
      if (want) {
        const l = Math.hypot(...want) || 1, d = want.map((v) => v / l), e = eyeOf(b);
        const h = raycast(e, d, HOOK.range, boxes);
        if (h && h.t > 6 && h.point[1] > b.pos[1] - 1) { ai.hook = { point: h.point, len: h.t, until: n + 2600 }; b.g = h.point; }
      }
    }
    if (ai.hook) jump = false;
    const wl = Math.hypot(wx, wz);
    if (wl > 0) { wx /= wl; wz /= wl; }
    // don't walk off the map (bots are dumb, not suicidal)
    if (wl > 0 && b.onGround) {
      const probe = [b.pos[0] + wx * 2.5, b.pos[1] + 0.5, b.pos[2] + wz * 2.5];
      if (!raycast(probe, [0, -1, 0], 6, boxes)) { wx = -wx; wz = -wz; ai.strafeDir *= -1; }
    }
    return { wx: wx * D.speed, wz: wz * D.speed, jump };
  }

  // follow the map's lane waypoints toward a site (bots can't path-find, so maps give them routes)
  routeTo(b, siteId, final) {
    const nav = this.map.nav && this.map.nav[siteId];
    if (!nav) return final;
    const ai = b.ai;
    if (!ai.route || ai.routeSite !== siteId) {
      let best = null, bd = 1e9, bi = 0;
      for (const rt of nav) rt.forEach((q, i) => { const d = Math.hypot(q[0] - b.pos[0], q[1] - b.pos[2]); if (d < bd) { bd = d; best = rt; bi = i; } });
      ai.route = best; ai.ri = bi; ai.routeSite = siteId;
    }
    const rt = ai.route;
    while (ai.ri < rt.length && Math.hypot(rt[ai.ri][0] - b.pos[0], rt[ai.ri][1] - b.pos[2]) < 2.6) ai.ri++;
    if (ai.ri >= rt.length) return final;
    return [rt[ai.ri][0], b.pos[1], rt[ai.ri][1]];
  }
  botGoal(b) {
    const B = this.bomb;
    if (B && this.game === 'bomb' && B.ph !== 'done' && !B.between) {
      const sites = this.map.sites || [];
      const mid = (s) => [(s.min[0] + s.max[0]) / 2, s.min[1], (s.min[2] + s.max[2]) / 2];
      if (b.team === B.att) {
        if (B.carrier === b.id) {
          b.ai.site = b.ai.site && sites.find((x) => x.id === b.ai.site.id) ? b.ai.site : pick(sites);
          const inSite = siteAt(this.map, b.pos);
          return { p: inSite ? b.pos : this.routeTo(b, b.ai.site.id, mid(b.ai.site)), use: true, r: inSite ? 99 : 1.5, force: true };
        }
        if (B.drop) return { p: B.drop, force: true, r: 0 };
        if (B.ph === 'planted') return { p: this.routeTo(b, B.site, B.p), r: 0 }; // guard it
        if (!b.ai.site) b.ai.site = pick(sites);
        return b.ai.site ? { p: this.routeTo(b, b.ai.site.id, mid(b.ai.site)), r: 0 } : null;
      }
      if (B.ph === 'planted') {
        const near = dist3(b.pos, B.p) < 8;
        return { p: near ? B.p : this.routeTo(b, B.site, B.p), use: near, r: BOMB.defuseRange - 0.6, force: true };
      }
      if (!b.ai.site || Math.random() < 0.002) b.ai.site = pick(sites);
      return b.ai.site ? { p: this.routeTo(b, b.ai.site.id, mid(b.ai.site)), r: 0 } : null;
    }
    if (this.game === 'tags' && this.tags.size) {
      let best = null, bd = 45;
      for (const g of this.tags.values()) { const d = dist3(g.p, b.pos); if (d < bd) { bd = d; best = g; } }
      if (best) return { p: best.p, r: 0 };
    }
    return null;
  }

  botFire(b, t, D) {
    const w = WEAPONS[b.w], n = now();
    if (b.w === 'shredder') { this.botShred(b); return; } // no shots: it sucks for as long as they're in front of it
    const iv = w.rate ? 1000 / fireRate(w, b.hp) : w.cd * 1000;
    if (w.mag) {
      b.ai.ammo--;
      if (b.ai.ammo <= 0) { b.ai.ammo = w.mag; b.ai.reloadUntil = n + w.reload * 1000; }
    }
    b.ai.nextShot = n + iv / D.rate + (w.auto ? 0 : Math.random() * 300);
    const cp = Math.cos(b.pitch);
    const aim = [-Math.sin(b.yaw) * cp, Math.sin(b.pitch), -Math.cos(b.yaw) * cp];
    const o = eyeOf(b);
    if (w.kind === 'hitscan') {
      const hip = (HIPFIRE[this.cfg.hip] || HIPFIRE.normal).mul;
      const pellets = w.pellets || 1;
      const hits = new Map(), segs = [];
      for (let i = 0; i < pellets; i++) {
        const d = spreadDir(aim, (w.spread || 0) * Math.max(0.3, hip) + D.err);
        const mh = raycast(o, d, w.range, this.boxes);
        let maxT = mh ? mh.t : w.range, victim = null, head = false;
        for (const p of this.players.values()) {
          if (p === b || !p.alive || (p.isBot && this.mode === 'coop')) continue;
          for (const hb of playerBoxes(p.pos)) {
            const h = rayBox(o, d, hb, maxT);
            if (h && h.t < maxT) { maxT = h.t; victim = p; head = hb.head; }
          }
        }
        segs.push([...o, o[0] + d[0] * maxT, o[1] + d[1] * maxT, o[2] + d[2] * maxT].map(r2));
        if (victim) { const h = hits.get(victim) || { n: 0, h: 0, d }; h.n++; if (head) h.h++; hits.set(victim, h); }
      }
      for (const [victim, h] of hits) this.applyHitscan(b, victim, b.w, h.n, h.h, h.d, 0.7);
      this.broadcast({ t: 'fx', k: 'shot', w: b.w, id: b.id, s: segs.slice(0, 12) });
    } else if (w.kind === 'proj') {
      this.spawnProj(b, b.w, o, spreadDir(aim, D.err));
    }
  }

  stepBot(b, dt) {
    const n = now();
    const frozen = n < (b.frozenUntil || 0);
    const think = frozen ? { wx: 0, wz: 0, jump: false } : this.botThink(b, dt);
    if (frozen) { b.vel[0] = 0; b.vel[2] = 0; }
    const v = b.vel;
    const slipping = n < b.slipUntil;
    if (!b.ai.dummy || !b.ai.dummy.move) {
      if (b.onGround) {
        if (think.jump && !slipping) { v[1] = 9.2; b.onGround = false; }
        else {
          const hs = Math.hypot(v[0], v[2]);
          const fr = slipping ? 0.02 : 6;
          if (hs > 0) { const ns = Math.max(0, hs - Math.max(hs, 3) * fr * dt) / hs; v[0] *= ns; v[2] *= ns; }
          if (!slipping) {
            const cur = v[0] * think.wx + v[2] * think.wz, add = 8.5 - cur;
            if (add > 0 && (think.wx || think.wz)) { const a = Math.min(add, 11 * 8.5 * dt); v[0] += a * think.wx; v[2] += a * think.wz; }
          }
        }
      } else if (think.wx || think.wz) {
        const cur = v[0] * think.wx + v[2] * think.wz, add = 1.2 - cur;
        if (add > 0) { const a = Math.min(add, 60 * dt); v[0] += a * think.wx; v[2] += a * think.wz; }
      }
    }
    v[1] -= 26 * dt;
    // on the rope: same pull as a player's grapple. let go near the point (or when it's been a while) with a jump boost
    const hk = b.ai && b.ai.hook;
    if (hk) {
      const dx = hk.point[0] - b.pos[0], dy = hk.point[1] - (b.pos[1] + 1), dz = hk.point[2] - b.pos[2];
      const dist = Math.hypot(dx, dy, dz) || 1, nx = dx / dist, ny = dy / dist, nz = dz / dist;
      if (dist > 2) { v[0] += nx * HOOK.pull * dt; v[1] += ny * HOOK.pull * dt; v[2] += nz * HOOK.pull * dt; }
      v[1] += 26 * 0.35 * dt;
      hk.len = Math.min(hk.len, dist);
      const radial = v[0] * nx + v[1] * ny + v[2] * nz;
      if (dist >= hk.len - 0.05 && radial < 0) { v[0] -= nx * radial; v[1] -= ny * radial; v[2] -= nz * radial; }
      if (dist < 4.5 || n > hk.until || slipping) {
        if (!slipping) { v[0] *= 1.12; v[2] *= 1.12; v[1] = Math.max(v[1], 0) * 1.12 + 11; } // hook jump
        b.ai.hook = null; b.g = null;
      }
      b.onGround = false;
    }
    if (b.held && n < b.held.until) { for (let i = 0; i < 3; i++) v[i] = Math.max(-30, Math.min(30, (b.held.at[i] - b.pos[i]) * 9)); b.onGround = false; } // hanging in a shredder
    const was = b.onGround;
    const res = movePlayer(b.pos, v, dt, this.boxes, was);
    b.onGround = !!res.ground && v[1] <= 0.01;
    if (b.onGround && res.ground.pad && !b.ai.dummy) { const pd = res.ground.pad; v[0] += pd[0]; v[1] = pd[1]; v[2] += pd[2]; b.onGround = false; }
    b.f = slipping ? 16 : 0;
    if (n < (b.suckUntil || 0)) b.f |= FLAGS.SUCK; // shredder running: clients draw the suction
    if (b.pos[1] < this.map.killY) this.kill(b, null, 'void');
  }

  // ---------------------------------------------------------- items (G): charges refill over time
  itemCharges(p, id) {
    const it = ITEMS[id];
    p.ic ||= {};
    let c = p.ic[id];
    if (!c) c = p.ic[id] = { n: it.charges, next: 0 };
    const n = now();
    while (c.n < it.charges && c.next && n >= c.next) { c.n++; c.next = c.n < it.charges ? c.next + it.recharge * 1000 : 0; }
    return c;
  }
  useItem(p, m) {
    const it = ITEMS[m.i];
    if (!it || !p.alive) return;
    const c = this.itemCharges(p, m.i);
    if (c.n <= 0 || now() - (p.itemT || 0) < 400) return;
    p.itemT = now();
    c.n--;
    if (!c.next) c.next = now() + it.recharge * 1000;
    send(p, { t: 'ic', i: m.i, n: c.n, next: c.next ? c.next - now() : 0 });
    let o = vec3(m.o);
    if (!o || dist3(o, eyeOf(p)) > 4) o = eyeOf(p);
    const d = norm(vec3(m.d)) || [0, 0, -1];
    if (it.proj) {
      const w = WEAPONS[it.proj];
      const pr = this.makeProj(p, it.proj, [o[0] + d[0] * 0.7, o[1] + d[1] * 0.7, o[2] + d[2] * 0.7],
        [d[0] * w.speed + p.vel[0] * 0.35, d[1] * w.speed + 3 + p.vel[1] * 0.35, d[2] * w.speed + p.vel[2] * 0.35]);
      pr.born = now();
    } else if (m.i === 'medkit') {
      p.healLeft = it.heal;
      this.broadcast({ t: 'fx', k: 'medkit', id: p.id });
    } else if (m.i === 'bubble') {
      const b = { id: this.nextBub++, p: [r2(p.pos[0]), r2(p.pos[1] + 1), r2(p.pos[2])], r: it.r, until: now() + it.dur * 1000, o: p.id };
      this.bubbles.set(b.id, b);
      this.broadcast({ t: 'bub+', id: b.id, p: b.p, r: b.r, left: it.dur * 1000 });
    }
  }
  inBubble(b, t) { return Math.hypot(t.pos[0] - b.p[0], t.pos[1] + 1 - b.p[1], t.pos[2] - b.p[2]) < b.r; }
  // a bubble protects whoever is inside from anyone outside it
  bubbleBlocks(attacker, t) {
    if (!attacker || attacker === t || !this.bubbles.size) return false;
    for (const b of this.bubbles.values()) if (this.inBubble(b, t) && !this.inBubble(b, attacker)) return true;
    return false;
  }
  // snowballs: frost builds up, enough of it freezes you, a snowball to a frozen target shatters them
  frost(t, owner) {
    const w = WEAPONS.snowball, n = now();
    if (t.frozenUntil > n) {
      t.frozenUntil = 0;
      this.broadcast({ t: 'fx', k: 'shatter', id: t.id, p: center(t).map(r2) });
      this.kill(t, owner, 'snowball');
      return;
    }
    t.frost = Math.max(0, (t.frost || 0) - Math.floor((n - (t.frostT || 0)) / (w.frostDecay * 1000))) + 1;
    t.frostT = n;
    if (t.frost >= w.freezeAt) {
      t.frost = 0;
      t.frozenUntil = n + w.freeze * 1000;
      t.vel[0] = 0; t.vel[2] = 0;
      this.broadcast({ t: 'freeze', id: t.id, dur: w.freeze * 1000 });
    } else this.broadcast({ t: 'frost', id: t.id, n: t.frost });
  }
  tickItems(dt) {
    const n = now();
    for (const b of [...this.bubbles.values()]) if (n >= b.until) { this.bubbles.delete(b.id); this.broadcast({ t: 'bubx', id: b.id }); }
    for (const p of this.players.values()) {
      if (p.healLeft > 0 && p.alive) { const a = Math.min(p.healLeft, 26 * dt); p.healLeft -= a; p.hp = Math.min(100, p.hp + a); }
    }
  }

  // ---------------------------------------------------------- combat
  tag(t, attacker, w) {
    if (!attacker || attacker === t) return;
    t.lastAttacker = attacker.id; t.lastAttackW = w; t.lastAttackT = now();
  }
  knock(t, v, w) {
    if (t.isBot) {
      if (t.ai.dummy && t.ai.dummy.move) return;
      t.vel[0] += v[0]; t.vel[1] += v[1]; t.vel[2] += v[2];
      if (v[1] > 0.5 && t.onGround) { t.onGround = false; t.pos[1] += 0.02; }
      return;
    }
    send(t, { t: 'kb', v: v.map(r2), w });
  }
  slip(t) {
    if (t.isBot) { t.slipUntil = now() + 1700; t.vel[1] = Math.max(t.vel[1], 6.5); t.onGround = false; return; }
    send(t, { t: 'slip' });
  }
  friendly(a, b) {
    if (!a || !b || a === b) return false;
    if (this.mode === 'coop') return a.isBot === b.isBot;
    return this.teamsOn() && a.team && a.team === b.team;
  }
  damage(t, amt, attacker, w, hs) {
    if (!t.alive || amt <= 0) return;
    if (this.round && this.round.over && w !== 'void') return;
    if (attacker && attacker !== t && now() - t.spawnT < 1200 && !t.isBot) return; // spawn protection
    if (this.friendly(attacker, t)) return;
    if (this.bubbleBlocks(attacker, t)) return;
    if (attacker && attacker.isBot && !t.isBot && this.mode !== 'bots') amt *= 0.6; // coop bots hit softer
    t.hp -= amt;
    t.lastHs = !!hs;
    if (hs && attacker && attacker !== t && attacker.acct && this.mode !== 'training') stat(attacker, 'headshots', 1);
    this.tag(t, attacker, w);
    this.broadcast({ t: 'dmg', to: t.id, from: attacker ? attacker.id : 0, a: Math.round(Math.min(amt, 999)), w, hs: !!hs });
    if (t.hp <= 0) this.kill(t, attacker, w);
  }
  heal(p, amt, max = 100) {
    if (!p.alive) return;
    p.hp = Math.min(Math.max(max, 100), p.hp + amt);
    this.broadcast({ t: 'heal', id: p.id, a: Math.round(amt), hp: Math.round(p.hp) });
  }
  burn(t, by, secs) { if (!t.alive) return; t.burnUntil = now() + secs * 1000; t.burnBy = by ? by.id : 0; t.burnTick = 0; }
  sleep(t, by, secs) {
    if (!t.alive) return;
    this.tag(t, by, 'bow');
    if (t.isBot) { t.sleepUntil = now() + secs * 1000; return; }
    send(t, { t: 'sleep', dur: secs });
  }
  makeCloud(p, owner) {
    const c = { id: this.nextCloud++, p: p.map(r2), o: owner, born: now(), tick: 0 };
    this.clouds.set(c.id, c);
    this.broadcast({ t: 'cloud', id: c.id, p: c.p });
  }
  tickStatus(dt) {
    const n = now();
    for (const t of this.players.values()) {
      if (!t.alive) continue;
      if (t.hp > 100) t.hp = Math.max(100, t.hp - 2 * dt); // overheal fades
      if (t.burnUntil > n) {
        t.burnTick -= dt;
        if (t.burnTick <= 0) { t.burnTick = 0.5; this.damage(t, 5, this.players.get(t.burnBy) || null, 'bow'); this.broadcast({ t: 'fx', k: 'burn', id: t.id }); }
      }
    }
    for (const c of this.clouds.values()) {
      if (n - c.born > 4500) { this.clouds.delete(c.id); this.broadcast({ t: 'cloudx', id: c.id }); continue; }
      c.tick -= dt;
      if (c.tick > 0) continue;
      c.tick = 0.4;
      const owner = this.players.get(c.o);
      for (const t of this.players.values()) {
        if (!t.alive || t.id === c.o || this.friendly(owner, t)) continue;
        if (dist3(center(t), c.p) < 5.5) this.damage(t, 4, owner, 'bow');
      }
    }
  }

  // everything that hurts or shoves a player goes through here so reverse cards work on all of it
  hurt(t, attacker, w, dmg, kb, opts = {}) {
    if (!t || !t.alive) return;
    if (this.friendly(attacker, t)) return;
    if (this.bubbleBlocks(attacker, t)) { this.broadcast({ t: 'fx', k: 'bubhit', p: center(t).map(r2) }); return; }
    if (attacker && attacker !== t && attacker.alive && t.reverseUntil > now()) {
      this.broadcast({ t: 'fx', k: 'reflect', id: t.id, by: attacker.id });
      const victim = attacker;
      attacker = t;
      t = victim;
      if (kb) kb = [-kb[0], kb[1], -kb[2]];
    }
    if (kb) this.knock(t, kb, w);
    if (opts.slip) this.slip(t);
    this.tag(t, attacker, w);
    this.damage(t, dmg, attacker, w, opts.hs);
  }
  kill(t, attacker, w) {
    if (!t.alive) return;
    t.alive = false; t.hp = 0; t.deaths++; t.g = null; t.reverseUntil = 0;
    if (t.ai) t.ai.hook = null;
    t.respawnAt = now() + (t.isBot && t.ai.dummy ? 700 : 2500);
    t.deadT = now();
    let killer = attacker, via = null;
    if (w === 'void' || w === 'cough') {
      killer = null;
      if (t.lastAttacker && now() - t.lastAttackT < 10000 && this.players.has(t.lastAttacker)) {
        killer = this.players.get(t.lastAttacker); via = t.lastAttackW;
      }
    }
    if (killer && killer !== t && this.teamsOn() && killer.team !== t.team && this.round && !this.round.over) {
      if (this.game === 'tdm') this.score[killer.team]++;
      if (this.game === 'tags') this.dropTag(t);
    }
    if (this.bomb && this.bomb.carrier === t.id) this.dropBomb(t.pos);
    if (killer && killer !== t && w === 'katana') { // the katana grows with every kill
      killer.kat = Math.min(WEAPONS.katana.growMax, (killer.kat || 0) + 1);
      this.broadcast({ t: 'kat', id: killer.id, n: killer.kat });
    }
    if (t.kat) { t.kat = 0; this.broadcast({ t: 'kat', id: t.id, n: 0 }); }
    if (killer && killer !== t) {
      killer.kills++;
      killer.streak = (killer.streak || 0) + 1;
      if (!killer.isBot && this.mode !== 'training') {
        // your 3 picked streaks: earn one and it waits in your tray until you use it (keys 5 / 6 / 7)
        for (const id of validStreaks(killer.streaks)) {
          const st = STREAKS[id];
          if (killer.streak !== st.kills) continue;
          killer.pocket ||= [];
          if (!killer.pocket.includes(id)) killer.pocket.push(id);
          send(killer, { t: 'streak', earned: id, n: killer.streak });
          this.broadcast({ t: 'chat', id: 0, m: `${killer.name} earned ${st.name} (${st.kills} kills)` }, killer.id);
        }
      }
    }
    // killcam: humans who have it on wait for it to finish (or skip it) before respawning
    if (this.game === 'bomb' && this.teamsOn()) t.respawnAt = now() + BOMB.respawn;
    if (!t.isBot && t.kc && killer && killer !== t && this.mode !== 'training') t.respawnAt = Math.max(t.respawnAt, now() + 9000);
    if (killer && killer !== t && this.round && !this.round.over && !(t.isBot && t.ai && t.ai.dummy) && this.mode !== 'training') this.hlCandidate(killer, t, w);
    send(t, { t: 'streak', reset: 1 });
    t.streak = 0;
    t.scythe = false; // active stuff ends when you die; earned-but-unused streaks stay in your tray
    if (this.mode !== 'training') {
      if (killer && killer !== t && killer.acct) {
        if (t.isBot) stat(killer, 'bot_kills', 1), stat(killer, 'xp', 5);
        else stat(killer, 'kills', 1), stat(killer, 'xp', 20);
        if (w === 'void') stat(killer, 'void_kills', 1);
      }
      if (w === 'tbag' && t.acct) stat(t, 'tbags', 1);
      if (t.acct) stat(t, 'deaths', 1);
    }
    let kfx = 'none';
    if (killer && killer !== t) {
      if (killer.isBot && killer.kfx == null) killer.kfx = Math.random() < 0.45 ? pick(KILL_IDS) : 'none'; // bots show off stuff you can roll
      kfx = killer.kfx || 'none';
    }
    this.broadcast({ t: 'kill', k: killer && killer !== t ? killer.id : 0, v: t.id, w, via, vel: t.vel.map(r2), pos: t.pos.map(r2), yaw: r2(t.yaw || 0), fx: kfx });
    t.lastAttacker = 0;
    if (t.isBot && this.mode === 'coop') { setTimeout(() => { if (this.players.get(t.id) === t) this.remove(t); }, 50); }
  }
  // is this kill the play of the round? multikills, speed, distance and void kills score higher
  hlCandidate(k, t, w) {
    const n = now();
    k.killLog = (k.killLog || []).filter((x) => n - x < 8000);
    k.killLog.push(n);
    const multi = k.killLog.length;
    const spd = Math.hypot(k.vel[0], k.vel[1], k.vel[2]) * 3.6;
    const dist = Math.hypot(k.pos[0] - t.pos[0], k.pos[1] - t.pos[1], k.pos[2] - t.pos[2]);
    const score = multi * 10 + Math.min(12, spd / 40) + Math.min(6, dist / 15) + (w === 'void' ? 5 : 0) + (t.lastHs ? 3 : 0) + (k.isBot ? -8 : 0) + Math.random();
    const r = this.round;
    if (r.hl && r.hl.score >= score) return;
    const label = multi >= 5 ? 'RAMPAGE' : multi === 4 ? 'QUAD KILL' : multi === 3 ? 'TRIPLE KILL' : multi === 2 ? 'DOUBLE KILL'
      : w === 'void' ? 'INTO THE VOID' : spd > 300 ? `${Math.round(spd)} KM/H KILL` : dist > 60 ? `${Math.round(dist)}M SHOT` : t.lastHs ? 'HEADSHOT' : 'NICE KILL';
    const t0 = Math.max(k.killLog[0] - 3200, n - 8000);
    const hl = { score, pending: true };
    r.hl = hl;
    // grab the clip a moment later so it includes the aftermath
    setTimeout(() => {
      if (this.round !== r || r.hl !== hl) return;
      Object.assign(hl, { pending: false, label, id: k.id, name: k.name, color: k.color, card: k.card || '', clip: this.clip(t0, now()) });
    }, 1300);
  }
  // a slice of the recording: 10 Hz frames + the events in that window + who's who
  clip(t0, t1) {
    const frames = this.rec.frames.filter((f) => f.s >= t0 && f.s <= t1 && f.odd);
    const ev = this.rec.ev.filter((e) => e.s >= t0 && e.s <= t1);
    const info = {};
    for (const f of frames) for (const e of f.p) if (!info[e[0]]) {
      const pl = this.players.get(e[0]);
      if (pl) info[e[0]] = { name: pl.name, color: pl.color, skins: pl.skins, bot: pl.isBot, look: pl.look, level: pl.level };
    }
    return { frames: frames.map((f) => ({ s: f.s, p: f.p, j: f.j })), ev, info };
  }
  pairOk(p, t, key, ms) {
    const k = key + ':' + t.id, n = now();
    if (n - (p.pair.get(k) || 0) < ms) return false;
    p.pair.set(k, n);
    return true;
  }
  rangeOk(p, t, range) {
    const slack = 6 + Math.hypot(...p.vel) * 0.3 + Math.hypot(...t.vel) * 0.3;
    return dist3(p.pos, t.pos) <= range + slack;
  }
  // most pellets a shot could honestly land at this distance: the spread disc vs the (client-side, distance-scaled) hitbox, with slack.
  // stops a hacked client claiming all 100 marbles hit from across the map.
  maxPellets(w, p, t) {
    const pellets = w.pellets || 1;
    if (pellets <= 1) return pellets;
    const dist = Math.hypot(t.pos[0] - p.pos[0], t.pos[1] - p.pos[1], t.pos[2] - p.pos[2]);
    const R = (w.spread || 0) * dist * 0.7, ds = 1 + Math.max(0, Math.min(1, (dist - 25) / 60)) * 0.8;
    const frac = R > 0 ? Math.min(1, (2.4 * ds * ds) / (Math.PI * R * R)) : 1;
    return Math.max(1, Math.min(pellets, Math.ceil(pellets * frac * 1.35 + 2)));
  }

  applyHitscan(p, t, wid, n, h, d, mul = 1) {
    const w = WEAPONS[wid], pellets = w.pellets || 1;
    const dmg = (w.dmg * (n - h) + w.dmg * (w.head || 1) * h) * mul;
    const k = w.kb * n;
    this.hurt(t, p, wid, dmg, [d[0] * k, d[1] * k + (w.kbUp || 0) * (n / pellets), d[2] * k], { hs: h > 0 });
  }

  onHit(p, m) {
    const w = WEAPONS[m.w];
    const t = this.players.get(m.to);
    const d = norm(vec3(m.d));
    if (!w || !t || !d || t === p || !t.alive || !p.alive) return;
    if ((w.slot === 'streak' || w.kind === 'dash') && !p.scythe) return; // you have to earn it
    if (w.kind === 'dash') {
      if (!(p.f & FLAGS.DASH) || !this.pairOk(p, t, 'dash', 280) || !this.rangeOk(p, t, w.range)) return;
      this.hurt(t, p, 'scythe', w.dmg, [d[0] * w.kb, d[1] * w.kb + w.kbUp, d[2] * w.kb]);
      return;
    }
    const toT = norm([t.pos[0] - p.pos[0], t.pos[1] - p.pos[1], t.pos[2] - p.pos[2]]) || d;
    if (w.kind === 'hitscan') {
      const pellets = w.pellets || 1;
      const n = clampInt(m.n, 1, Math.min(pellets, this.maxPellets(w, p, t))), h = clampInt(m.h, 0, n);
      if (!this.pairOk(p, t, 'hs' + m.w, (1000 / fireRate(w, p.hp)) * 0.6) || !this.rangeOk(p, t, w.range)) return; // the Redline fires faster as you lose HP
      this.applyHitscan(p, t, m.w, n, h, d);
    } else if (w.kind === 'melee') {
      const hv = m.heavy && w.heavy ? w.heavy : null; // knife right click
      const reach = w.range + (m.w === 'katana' ? (p.kat || 0) * w.grow : 0);
      if (hv) { if (!this.pairOk(p, t, 'mh' + m.w, hv.cd * 750) || !this.rangeOk(p, t, hv.range)) return; }
      else if (!this.pairOk(p, t, 'm' + m.w, w.cd * 750) || !this.rangeOk(p, t, reach)) return;
      const dir = w.radial ? toT : d;
      let dmg = hv ? hv.dmg : w.dmg, back = false;
      if (w.backstab) { // they're facing away from you -> backstab
        const fwd = [-Math.sin(t.yaw), -Math.cos(t.yaw)];
        const hl = Math.hypot(toT[0], toT[2]) || 1;
        if (fwd[0] * (toT[0] / hl) + fwd[1] * (toT[2] / hl) > 0.45) { dmg *= w.backstab; back = true; }
      }
      const kb = hv ? hv.kb : w.kb, kbUp = hv ? hv.kbUp : w.kbUp;
      this.hurt(t, p, m.w, dmg, [dir[0] * kb, dir[1] * kb + kbUp, dir[2] * kb], { slip: !!w.slip, hs: back });
    } else if (m.w === 'cig') {
      if (!this.pairOk(p, t, 'cig', 75) || !this.rangeOk(p, t, w.range)) return;
      this.hurt(t, p, 'cig', w.dmg, [d[0] * 1.5, 0.6, d[2] * 1.5]);
    }
  }

  onPush(p, m) {
    const t = this.players.get(m.to);
    if (!t || t === p || !t.alive || !p.alive) return;
    const toT = norm([t.pos[0] - p.pos[0], t.pos[1] - p.pos[1], t.pos[2] - p.pos[2]]) || [0, 1, 0];
    if (m.w === 'blower') {
      const w = WEAPONS.blower;
      if (!this.pairOk(p, t, 'blow', 75) || !this.rangeOk(p, t, w.range)) return;
      this.hurt(t, p, 'blower', Math.random() < 0.3 ? 1 : 0, [toT[0] * w.push, toT[1] * w.push + 1.2, toT[2] * w.push]);
    } else if (m.w === 'hook') {
      if (!this.pairOk(p, t, 'hook', 400) || !this.rangeOk(p, t, HOOK.range)) return;
      this.hurt(t, p, 'hook', 0, [-toT[0] * HOOK.tug, -toT[1] * HOOK.tug + 5, -toT[2] * HOOK.tug]);
    }
    if (m.w === 'shredder') this.shredPull(p, t);
  }

  // ---------------------------------------------------------- shredder
  // the client only says who is in its cone. everything else comes from server positions: the pull toward the
  // intake (harder the closer they are, never away from you), and once they're in it: held in the teeth + shredded
  shredPull(p, t) {
    const w = WEAPONS.shredder, n = now(), gap = (n - (p.pair.get('shred:' + t.id) || 0)) / 1000;
    if (p.w !== 'shredder' || !this.pairOk(p, t, 'shred', 70) || !this.rangeOk(p, t, w.range)) return;
    // damage + pull scale with the time since the last tick on them, so a low-fps client shreds as fast as anyone
    // (pairOk keeps that gap honest). after a pause it's one normal tick, not a burst
    const el = gap < 0.3 ? gap : w.tick;
    if (!p.isBot && !this.shredHeat(p, n)) return;
    const e = eyeOf(p), L = lookOf(p);
    const mouth = [e[0] + L[0] * w.mouth, e[1] + L[1] * w.mouth - 0.25, e[2] + L[2] * w.mouth];
    // in front of you (loosely: positions lag a bit) and not through a wall
    const c = center(t), fe = [c[0] - e[0], c[1] - e[1], c[2] - e[2]], de = Math.hypot(...fe) || 1e-3;
    if (de > 3 && (fe[0] * L[0] + fe[1] * L[1] + fe[2] * L[2]) / de < Math.cos(w.cone + 0.45)) return;
    if (raycast(e, [fe[0] / de, fe[1] / de, fe[2] / de], Math.max(0, de - 0.5), this.boxes)) return;
    // intake to the nearest bit of their body
    const by = Math.max(t.pos[1] + 0.2, Math.min(t.pos[1] + 1.7, mouth[1]));
    const to = [mouth[0] - t.pos[0], mouth[1] - by, mouth[2] - t.pos[2]], d = Math.hypot(...to) || 1e-3;
    if (d > w.range) return;
    if (d <= w.grabR) { // the last few metres it just yanks them in; inside shredR the teeth have them
      const safe = this.friendly(p, t) || this.bubbleBlocks(p, t) || t.reverseUntil > n || (!t.isBot && n - t.spawnT < 1200);
      // hang them in the air stream just past the mouth, a bit to the right where the gun is, low enough that the
      // shooter can still see past them (that's their feet: their middle is 0.9 up)
      const rx = Math.cos(p.yaw || 0), rz = -Math.sin(p.yaw || 0);
      if (!safe) this.shredHold(t, [mouth[0] + L[0] * 0.75 + rx * 0.3, mouth[1] + L[1] * 0.75 - 1.0, mouth[2] + L[2] * 0.75 + rz * 0.3]);
      this.hurt(t, p, 'shredder', d <= w.shredR ? w.dps * el : 0, null);
      return;
    }
    if (!t.isBot && n - t.spawnT < 1200) return; // spawn protection covers the pull too: no reeling people in as they spawn
    // speed-capped so they don't arrive like a bullet (or overshoot through you on a laggy connection)
    const k = 1 - d / w.range, dir = [to[0] / d, to[1] / d, to[2] / d];
    const along = (t.vel[0] - p.vel[0]) * dir[0] + (t.vel[1] - p.vel[1]) * dir[1] + (t.vel[2] - p.vel[2]) * dir[2];
    const dv = Math.max(0, Math.min((w.pull + (w.pullMax - w.pull) * k * k) * (el / w.tick), w.vmax + d * 0.3 - along));
    this.hurt(t, p, 'shredder', 0, [dir[0] * dv, dir[1] * dv + w.lift * (0.4 + 0.6 * k), dir[2] * dv]);
  }
  // stuck in the intake: a human's client gets told where to hang and chases that point every frame; a bot does the
  // same in stepBot (steering every tick, not once per push, so a shooter's slow or bunched pushes can't fling it)
  shredHold(t, at) {
    if (!t.isBot) { send(t, { t: 'grab', p: at.map(r2) }); return; }
    if (t.ai.dummy && t.ai.dummy.move) return; // moving dummies are on rails
    t.ai.hook = null; t.g = null; // no grappling out of it
    t.held = { at, until: now() + 260 };
  }
  // ~4 s of sucking overheats it (same numbers the client shows), then it has to cool. a hacked client can't keep it on:
  // heat charges exactly the time shredPull credits pull + damage for (the whole gap at a steady cadence, one tick
  // after a pause) and the rest of a pause cools it, so no push cadence shreds for free. that's also the client's own
  // sum (a tick of suction per push, cooling while let go), so an honest one never gets locked out early
  shredHeat(p, n) {
    const w = WEAPONS.shredder, gap = Math.min(10, (n - (p.shredT || 0)) / 1000);
    if ((p.shredT || 0) < p.spawnT) { p.shredHeat = 0; p.shredHot = false; } // a new life starts cold (the client's does too)
    p.shredT = n;
    // overheated: every push is turned away before anything is credited, and only cools it (pushing can't keep it hot)
    if (p.shredHot) {
      p.shredHeat = Math.max(0, p.shredHeat - gap * w.regen);
      if (p.shredHeat <= w.fuel * w.coolTo) p.shredHot = false;
      return false;
    }
    const on = gap < 0.3 ? gap : w.tick;
    p.shredHeat = Math.max(0, (p.shredHeat || 0) + on - (gap - on) * w.regen);
    if (p.shredHeat > w.fuel + 0.75) { p.shredHot = true; return false; } // (0.75 s of slack for network jitter)
    return true;
  }
  // bots: suck everyone in front of them through the same rules, with their own heat
  botShred(b) {
    const w = WEAPONS.shredder, ai = b.ai, n = now(), gap = Math.min(10, (n - (ai.shT || 0)) / 1000);
    if (gap < w.tick) return;
    if ((ai.shT || 0) < b.spawnT) { ai.heat = 0; ai.hot = false; } // respawned: cold again
    ai.shT = n;
    if (ai.hot) { ai.heat = Math.max(0, ai.heat - gap * w.regen); if (ai.heat > w.fuel * w.coolTo) return; ai.hot = false; }
    else ai.heat = gap < 0.25 ? (ai.heat || 0) + gap : Math.max(0, (ai.heat || 0) - gap * w.regen);
    if (ai.heat >= w.fuel) { ai.hot = true; return; }
    b.suckUntil = n + 160;
    for (const t of this.players.values()) if (t !== b && t.alive) this.shredPull(b, t);
  }

  onFire(p, m) {
    const w = WEAPONS[m.w];
    if (!w || !p.alive) return;
    if (w.slot === 'streak' && !p.scythe) return;
    let o = vec3(m.o);
    if (!o || dist3(o, eyeOf(p)) > 4) o = eyeOf(p);
    if (w.kind === 'hitscan') { this.broadcast({ t: 'fx', k: 'shot', w: m.w, id: p.id, s: segs(m.s) }, p.id); return; }
    if (w.kind === 'melee') { this.broadcast({ t: 'fx', k: 'swing', w: m.w, id: p.id, a: o.map(r2), h: m.heavy ? 1 : undefined }, p.id); return; }
    if (w.kind === 'reverse') {
      const n = now();
      if (n - (p.lastFire.reverse || 0) < w.cd * 900) return;
      p.lastFire.reverse = n;
      p.reverseUntil = n + w.dur * 1000;
      this.broadcast({ t: 'fx', k: 'reverse', id: p.id, dur: w.dur });
      return;
    }
    const d = norm(vec3(m.d));
    if (d && w.kind === 'proj') this.spawnProj(p, m.w, o, d);
    if (d && w.kind === 'bow') {
      const n = now();
      if (n - (p.lastFire.bow || 0) < w.cd * 750) return;
      p.lastFire.bow = n;
      const c = Math.max(0.15, Math.min(1, Number(m.c) || 0));
      const tip = p.tip;
      const sp = (w.speed + (w.speedMax - w.speed) * c) * (tip === 'power' ? 1.3 : 1);
      const pr = this.makeProj(p, 'bow', [o[0] + d[0] * 0.7, o[1] + d[1] * 0.7, o[2] + d[2] * 0.7], d.map((x) => x * sp), { tip, charge: c });
      pr.born = now();
      p.tip = pick(TIP_IDS);
      send(p, { t: 'tip', tip: p.tip });
    }
    if (d && w.kind === 'cards') this.playCard(p, m, o, d);
  }

  // ---------------------------------------------------------- card deck
  playCard(p, m, o, d) {
    const n = now();
    if (n - (p.lastFire.cards || 0) < WEAPONS.cards.cd * 750) return;
    const i = clampInt(m.i, 0, 4);
    if (!p.hand || !p.hand[i]) return;
    p.lastFire.cards = n;
    let card = p.hand.splice(i, 1)[0];
    let suit = card[0], rank = Number(card.slice(1));
    const joker = suit === 'j';
    if (joker) { suit = pick(['h', 's', 'c', 'd']); rank = 13; } // joker: a random ultimate
    const ult = rank >= 11;
    this.broadcast({ t: 'fx', k: 'card', id: p.id, card, suit, ult, joker });
    if (rank === 1) { // aces teleport you forward
      const hit = raycast(eyeOf(p), d, 16, this.boxes);
      const dist = hit ? Math.max(0, hit.t - 1) : 16;
      const to = [p.pos[0] + d[0] * dist, p.pos[1] + Math.max(0, d[1] * dist), p.pos[2] + d[2] * dist];
      send(p, { t: 'tp', p: to.map(r2) });
    } else if (suit === 'h') {
      if (ult) this.heal(p, 150, 150); else this.heal(p, rank * 3);
    } else if (suit === 's') {
      const count = ult ? 24 : rank, spread = ult ? 0.9 : 0.12 + rank * 0.02;
      for (let k = 0; k < count; k++) {
        const a = (k / Math.max(1, count - 1) - 0.5) * spread;
        const dir = norm([d[0] * Math.cos(a) - d[2] * Math.sin(a), d[1] + (Math.random() - 0.5) * 0.05, d[0] * Math.sin(a) + d[2] * Math.cos(a)]);
        this.makeProj(p, 'card', [o[0] + dir[0] * 0.8, o[1] + dir[1] * 0.8, o[2] + dir[2] * 0.8], dir.map((x) => x * 55));
      }
    } else if (suit === 'c') { // clubs: shockwave (cone, or all around for face cards)
      const R = ult ? 12 : 9;
      for (const t of this.players.values()) {
        if (t === p || !t.alive) continue;
        const to = [t.pos[0] - p.pos[0], t.pos[1] - p.pos[1], t.pos[2] - p.pos[2]];
        const dist = Math.hypot(...to);
        if (dist > R || dist < 0.01) continue;
        const dir = to.map((x) => x / dist);
        if (!ult && dir[0] * d[0] + dir[1] * d[1] + dir[2] * d[2] < 0.6) continue;
        const k = ult ? 55 : 10 + rank * 4;
        this.hurt(t, p, 'cards', ult ? 25 : rank * 2, [dir[0] * k, dir[1] * k + (ult ? 14 : 6), dir[2] * k]);
      }
    } else if (suit === 'd') { // diamonds: dash
      const k = ult ? 55 : rank * 3.5;
      this.knock(p, [d[0] * k, d[1] * k + (ult ? 6 : 2), d[2] * k], 'cards');
    }
    send(p, { t: 'hand', hand: p.hand, left: (p.deck || []).length });
    if (!p.hand.length) setTimeout(() => { if (this.players.get(p.id) === p) deal(p); }, 1500);
  }

  spawnProj(p, wid, o, d) {
    const w = WEAPONS[wid], n = now();
    if (n - (p.lastFire[wid] || 0) < w.cd * 750) return;
    if (wid === 'slipper') for (const pr of this.projectiles.values()) if (pr.k === 'slipper' && pr.o === p.id) return;
    p.lastFire[wid] = n;
    const wallHit = raycast(o, d, 0.8, this.boxes);
    const off = wallHit ? Math.max(0, wallHit.t - w.r - 0.05) : 0.8;
    const inherit = wid === 'slipper' ? 0 : 0.35;
    const pr = {
      id: this.nextProj++, k: wid, o: p.id, r: w.r, bounce: w.bounce || 0, born: n, phase: 0, hit: new Map(), sync: 0,
      p: [o[0] + d[0] * off, o[1] + d[1] * off, o[2] + d[2] * off],
      v: [d[0] * w.speed + p.vel[0] * inherit, d[1] * w.speed + p.vel[1] * inherit, d[2] * w.speed + p.vel[2] * inherit],
    };
    this.projectiles.set(pr.id, pr);
    this.broadcast({ t: 'ps', id: pr.id, k: pr.k, p: pr.p.map(r2), v: pr.v.map(r2), o: p.id });
  }

  makeProj(p, wid, pos, vel, extra = {}) {
    const w = WEAPONS[wid];
    const pr = { id: this.nextProj++, k: wid, o: p.id, r: w.r, bounce: w.bounce || 0, born: now() - 300, phase: 0, hit: new Map(), sync: 0, p: pos.slice(), v: vel.slice(), ...extra };
    this.projectiles.set(pr.id, pr);
    this.broadcast({ t: 'ps', id: pr.id, k: pr.k, p: pr.p.map(r2), v: pr.v.map(r2), o: p.id, tip: extra.tip });
    return pr;
  }

  // arrow (or thrown card) hit a player (t) or a wall (wall)
  arrowHit(pr, owner, t, wall) {
    this.projectiles.delete(pr.id);
    const d = norm(pr.v) || [0, 0, 1];
    if (pr.k === 'card') {
      this.broadcast({ t: 'pd', id: pr.id, p: pr.p.map(r2) });
      if (t && t.id !== pr.o) this.hurt(t, owner, 'cards', WEAPONS.card.dmg, [d[0] * 4, 1, d[2] * 4]);
      return;
    }
    const w = WEAPONS.bow, tip = pr.tip || 'regular', c = pr.charge || 0.5;
    const stuck = !t && (tip === 'regular' || tip === 'power' || tip === 'knockback' || tip === 'sleep');
    this.broadcast({ t: 'pd', id: pr.id, p: pr.p.map(r2), st: stuck ? 1 : 0, tip, d: d.map(r2) });
    if (tip === 'explosion') { this.explodeAt(pr.p, owner, 'bow', 5.5, 50, 30); return; }
    if (tip === 'gas') { this.makeCloud(pr.p, pr.o); if (!t) return; }
    if (!t || t.id === pr.o) return;
    let dmg = w.dmg + (w.dmgMax - w.dmg) * c;
    let kb = [d[0] * 6, 2, d[2] * 6];
    if (tip === 'power') dmg *= 1.8;
    if (tip === 'knockback') { dmg = 15; kb = [d[0] * 60, 15, d[2] * 60]; }
    if (tip === 'flame') { dmg = 15; this.burn(t, owner, 3); }
    if (tip === 'gas') dmg = 10;
    if (tip === 'sleep') { dmg = 10; this.sleep(t, owner, 2.5); }
    const head = pr.p[1] > t.pos[1] + 1.55;
    this.hurt(t, owner, 'bow', dmg * (head ? 1.5 : 1), kb, { hs: head });
  }
  explodeAt(p, owner, wid, R, dmg, kb) {
    this.broadcast({ t: 'boom', p: p.map(r2), r: R });
    for (const t of this.players.values()) {
      if (!t.alive) continue;
      const c = center(t), to = [c[0] - p[0], c[1] - p[1], c[2] - p[2]], dist = Math.hypot(...to);
      if (dist > R) continue;
      const f = 1 - dist / R, dir = dist > 0.1 ? to.map((x) => x / dist) : [0, 1, 0];
      const self = owner && t.id === owner.id;
      const k = kb * (0.4 + 0.6 * f);
      this.hurt(t, self ? null : owner, wid, self ? 0 : dmg * (0.3 + 0.7 * f), [dir[0] * k, dir[1] * k + 6 * f, dir[2] * k]);
    }
  }

  explode(pr) {
    const w = WEAPONS.chicken;
    const owner = this.players.get(pr.o);
    this.broadcast({ t: 'pd', id: pr.id, p: pr.p.map(r2), x: 1 });
    for (const t of this.players.values()) {
      if (!t.alive) continue;
      const c = center(t);
      const dx = c[0] - pr.p[0], dy = c[1] - pr.p[1], dz = c[2] - pr.p[2];
      const dist = Math.hypot(dx, dy, dz);
      if (dist > w.radius) continue;
      const f = 1 - dist / w.radius;
      const dir = dist > 0.1 ? [dx / dist, dy / dist, dz / dist] : [0, 1, 0];
      const self = t.id === pr.o;
      const k = w.kb * (0.4 + 0.6 * f) * (self ? w.selfKb : 1);
      this.hurt(t, self ? null : owner, 'chicken', self ? 0 : w.dmg * (0.3 + 0.7 * f), [dir[0] * k, dir[1] * k + 6 * f, dir[2] * k]);
    }
  }

  makePeel(p, owner) {
    const pl = { id: this.nextPeel++, p: [r2(p[0]), r2(p[1]), r2(p[2])], born: now(), o: owner };
    this.peels.set(pl.id, pl);
    this.broadcast({ t: 'pe', id: pl.id, p: pl.p });
    if (this.peels.size > 40) {
      const oldest = this.peels.keys().next().value;
      this.peels.delete(oldest);
      this.broadcast({ t: 'pr', id: oldest });
    }
  }

  sweep(prev, cur, r, skip) {
    const seg = [cur[0] - prev[0], cur[1] - prev[1], cur[2] - prev[2]];
    const len = Math.hypot(...seg);
    if (len < 1e-6) return [];
    const dir = seg.map((x) => x / len);
    const out = [];
    for (const t of this.players.values()) {
      if (!t.alive || skip(t)) continue;
      let best = Infinity;
      for (const hb of playerBoxes(t.pos)) {
        const e = { min: hb.min.map((x) => x - r), max: hb.max.map((x) => x + r) };
        const h = rayBox(prev, dir, e, len + 1e-3);
        if (h && h.t < best) best = h.t;
      }
      if (best < Infinity) out.push({ t, at: [prev[0] + dir[0] * best, prev[1] + dir[1] * best, prev[2] + dir[2] * best], d: best });
    }
    return out.sort((a, b) => a.d - b.d);
  }

  removeProj(pr, extra) {
    this.projectiles.delete(pr.id);
    this.broadcast(Object.assign({ t: 'pd', id: pr.id, p: pr.p.map(r2) }, extra));
  }

  tickProjectiles(dt) {
    const n = now();
    for (const pr of this.projectiles.values()) {
      const w = WEAPONS[pr.k];
      const age = (n - pr.born) / 1000;
      const owner = this.players.get(pr.o);
      const prev = pr.p.slice();
      let hit = null;
      if (pr.k === 'slipper') {
        if (!owner || !owner.alive) { this.removeProj(pr); continue; }
        if (pr.phase === 0 && age >= w.out) { pr.phase = 1; pr.hit.clear(); }
        if (pr.phase === 0) {
          if (stepProjectile(pr, dt, this.boxes, 0)) { pr.phase = 1; pr.hit.clear(); }
        } else {
          const tgt = eyeOf(owner); tgt[1] -= 0.3;
          const to = [tgt[0] - pr.p[0], tgt[1] - pr.p[1], tgt[2] - pr.p[2]];
          const dist = Math.hypot(...to);
          if (dist < 1.3 || age > w.life) { this.removeProj(pr, { c: 1 }); continue; }
          const spd = Math.max(w.back, Math.hypot(...owner.vel) + 10);
          pr.v = to.map((x) => (x / dist) * spd);
          for (let k = 0; k < 3; k++) pr.p[k] += pr.v[k] * dt;
        }
        pr.sync -= dt;
        if (pr.sync <= 0) { pr.sync = 0.1; this.broadcast({ t: 'pu', id: pr.id, p: pr.p.map(r2), v: pr.v.map(r2) }); }
      } else {
        hit = stepProjectile(pr, dt, this.boxes, w.grav);
      }
      if (pr.k === 'duck') {
        if (age >= w.fuse) { this.removeProj(pr); this.makeHole(pr.p, pr.o); continue; }
      } else if (pr.k === 'frag' || pr.k === 'smokegren') {
        if (age >= w.fuse) {
          this.removeProj(pr);
          if (pr.k === 'frag') this.explodeAt(pr.p, owner, 'frag', w.radius, w.dmg, w.kb);
          else this.broadcast({ t: 'smoke', p: pr.p.map(r2), r: ITEMS.smoke.r, dur: ITEMS.smoke.dur * 1000 });
          continue;
        }
      } else {
        const ownerImmune = pr.k === 'slipper' ? Infinity : pr.k === 'bowling' ? 0.5 : 0.25;
        const victims = this.sweep(prev, pr.p, pr.r, (t) => (t.id === pr.o && age < ownerImmune) || (pr.hit.has(t.id) && n - pr.hit.get(t.id) < 700) || this.friendly(owner, t));
        if (victims.length) {
          if (pr.k === 'chicken') { pr.p = victims[0].at; this.projectiles.delete(pr.id); this.explode(pr); continue; }
          if (pr.k === 'snowball') {
            const v = victims[0];
            pr.p = v.at;
            this.removeProj(pr, { b: 1 });
            if (v.t.id === pr.o) continue;
            const d = norm(pr.v) || [0, 0, 1];
            if (!this.bubbleBlocks(owner, v.t) && !this.friendly(owner, v.t)) {
              const frozen = v.t.frozenUntil > now();
              if (!frozen) this.hurt(v.t, owner, 'snowball', w.dmg, [d[0] * w.kb, w.kbUp, d[2] * w.kb]);
              if (v.t.alive) this.frost(v.t, owner);
            }
            continue;
          }
        if (pr.k === 'bow' || pr.k === 'card') { pr.p = victims[0].at; this.arrowHit(pr, owner, victims[0].t); continue; }
          if (pr.k === 'banana') {
            const v = victims[0];
            pr.p = v.at;
            const d = norm(pr.v) || [0, 0, 1];
            this.removeProj(pr, { b: 1 });
            if (v.t.id !== pr.o) this.hurt(v.t, owner, 'banana', w.dmg, [d[0] * w.kb, 3, d[2] * w.kb], { slip: true });
            else this.hurt(v.t, null, 'banana', 0, null, { slip: true });
            continue;
          }
          const d = norm([pr.v[0], 0, pr.v[2]]) || [0, 0, 1];
          for (const v of victims) {
            pr.hit.set(v.t.id, n);
            this.hurt(v.t, owner, pr.k, w.dmg, [d[0] * w.kb, w.kbUp, d[2] * w.kb]);
          }
          this.broadcast({ t: 'fx', k: pr.k === 'bowling' ? 'strike' : 'thwack', p: pr.p.map(r2), n: pr.hit.size });
          if (pr.k === 'bowling') {
            pr.v = pr.v.map((x) => x * 0.85);
            this.broadcast({ t: 'pu', id: pr.id, p: pr.p.map(r2), v: pr.v.map(r2) });
          }
        }
      }
      if (hit) {
        if (pr.k === 'bow' || pr.k === 'card') { this.arrowHit(pr, owner, null, hit); continue; }
        if (pr.k === 'snowball') { this.removeProj(pr, { b: 1 }); continue; }
        if (pr.k === 'chicken') { this.projectiles.delete(pr.id); this.explode(pr); continue; }
        if (pr.k === 'banana' && hit.axis === 1 && hit.sign === 1) {
          this.removeProj(pr);
          this.makePeel([pr.p[0], hit.box.max[1], pr.p[2]], pr.o);
          continue;
        }
        if (pr.k === 'bowling' && hit.axis === 1 && hit.sign === 1) { pr.v[0] *= 0.995; pr.v[2] *= 0.995; }
      }
      if (age > (w.life || 6) || pr.p[1] < this.map.killY) this.removeProj(pr);
    }
  }

  makeHole(p, owner, o = {}) {
    const w = WEAPONS.duck;
    const big = !!o.big;
    const h = {
      id: this.nextHole++, p: p.map(r2), o: owner, born: now(), tick: 0, big,
      time: big ? 6 : w.holeTime, R: big ? 34 : w.holeR, pull: big ? 80 : w.pull, blastR: big ? 18 : w.blastR, blastKb: big ? 45 : w.blastKb, blastDmg: big ? 70 : w.blastDmg,
    };
    this.holes.set(h.id, h);
    this.broadcast({ t: 'hs', id: h.id, p: h.p, o: owner, big });
  }

  tickHoles(dt) {
    const w = WEAPONS.duck, n = now();
    for (const h of this.holes.values()) {
      const age = (n - h.born) / 1000;
      const owner = this.players.get(h.o);
      if (age >= h.time) {
        this.holes.delete(h.id);
        this.broadcast({ t: 'he', id: h.id, p: h.p });
        for (const t of this.players.values()) {
          if (!t.alive) continue;
          const c = center(t);
          const to = [c[0] - h.p[0], c[1] - h.p[1], c[2] - h.p[2]];
          const dist = Math.hypot(...to);
          if (dist > h.blastR) continue;
          const f = 1 - dist / h.blastR;
          const dir = dist > 0.1 ? to.map((x) => x / dist) : [0, 1, 0];
          const self = t.id === h.o;
          if (self && h.big) continue;
          const k = h.blastKb * (0.4 + 0.6 * f);
          this.hurt(t, self ? null : owner, 'duck', self ? 0 : h.blastDmg * f, [dir[0] * k, dir[1] * k + 8 * f, dir[2] * k]);
        }
        continue;
      }
      h.tick -= dt;
      if (h.tick > 0) continue;
      h.tick = 0.1;
      for (const t of this.players.values()) {
        if (!t.alive || this.friendly(owner, t) || (h.big && t.id === h.o)) continue;
        const c = center(t);
        const to = [h.p[0] - c[0], h.p[1] - c[1], h.p[2] - c[2]];
        const dist = Math.hypot(...to);
        if (dist > h.R || dist < 0.05) continue;
        const s = (h.pull * (1 - dist / h.R) + 8) * 0.1 * Math.min(1, dist / 1.5);
        this.knock(t, to.map((x) => (x / dist) * s), 'duck');
        if (t.id !== h.o) this.tag(t, owner, 'duck');
        if (dist < 2 && t.id !== h.o) this.damage(t, 3, owner, 'duck');
      }
    }
  }

  tickPeels() {
    const n = now();
    for (const pl of this.peels.values()) {
      if (n - pl.born > 30000) { this.peels.delete(pl.id); this.broadcast({ t: 'pr', id: pl.id }); continue; }
      if (n - pl.born < 600) continue;
      for (const t of this.players.values()) {
        if (!t.alive) continue;
        if (Math.abs(t.pos[0] - pl.p[0]) < 0.85 && Math.abs(t.pos[2] - pl.p[2]) < 0.85 && t.pos[1] > pl.p[1] - 0.4 && t.pos[1] < pl.p[1] + 0.5) {
          this.peels.delete(pl.id);
          this.broadcast({ t: 'pr', id: pl.id, s: 1 });
          const owner = this.players.get(pl.o);
          this.hurt(t, owner === t ? null : owner, 'banana', 0, null, { slip: true });
          break;
        }
      }
    }
  }

  // ---------------------------------------------------------- lobby settings
  setCfg(p, m) {
    const n = now();
    if (n - p.cfgT < 1500) return;
    p.cfgT = n;
    const changes = [];
    if (m.map && MAPS[m.map] && m.map !== this.cfg.map && this.mode !== 'training' && MAP_ORDER.includes(m.map)) {
      this.cfg.map = m.map;
      changes.push(`map → ${MAPS[m.map].name}`);
      if (GAMES[this.game].sites && !(this.map.sites && this.map.sites.length)) { this.game = 'dm'; this.bomb = null; this.assignTeams(); changes.push('mode → Deathmatch (no bomb sites here)'); }
      if (this.bomb) this.newBombRound(true); else this.resetWorld();
    }
    if (m.hip && HIPFIRE[m.hip] && m.hip !== this.cfg.hip) { this.cfg.hip = m.hip; changes.push(`hipfire → ${HIPFIRE[m.hip].name}`); }
    if (m.game && GAMES[m.game] && m.game !== this.game && this.mode === 'bots' && this.setGame(m.game)) { changes.push(`mode → ${GAMES[m.game].name}`); this.vote = null; setTimeout(() => this.startRound(), 50); }
    if (m.diff && BOT_DIFF[m.diff] && m.diff !== this.cfg.diff && this.mode !== 'ffa') {
      this.cfg.diff = m.diff;
      for (const b of this.players.values()) if (b.isBot) b.ai.diff = m.diff;
      changes.push(`bots → ${BOT_DIFF[m.diff].name}`);
    }
    if (m.bots != null && this.mode === 'bots') {
      const c = clampInt(m.bots, 0, 12);
      if (c !== this.cfg.bots) { this.cfg.bots = c; this.fillBots(); changes.push(`bot count → ${c}`); }
    }
    if (!changes.length) return;
    this.broadcast({ t: 'cfg', cfg: this.cfg, by: p.id });
    if (this.mode === 'ffa' || this.mode === 'coop') this.broadcast({ t: 'chat', id: 0, m: `${p.name} set ${changes.join(', ')}` });
  }

  resetWorld() {
    this.projectiles.clear(); this.peels.clear(); this.holes.clear();
    this.broadcast({ t: 'clear' });
    for (const p of this.players.values()) {
      if (p.isBot && p.ai.dummy) continue;
      p.alive = true; p.hp = 100; p.vel = [0, 0, 0]; p.spawnT = now(); p.seq++;
      p.pos = this.pickSpawn(p.isBot, p);
      send(p, { t: 'spawn', p: p.pos, q: p.seq });
      this.sendLoadout(p);
    }
    if (this.mode === 'training') { this.removeBots(); this.spawnDummies(); }
  }

  handle(p, m) {
    switch (m.t) {
      case 's': {
        if (!p.alive || m.q !== p.seq) return;
        const pos = vec3(m.p), vel = vec3(m.v);
        if (!pos || !vel) return;
        p.pos = pos; p.vel = vel;
        if (p.acct) { const kmh = Math.min(20000, Math.hypot(vel[0], vel[2]) * 3.6); if (kmh > (p.acct.d.top_speed || 0)) { p.acct.d.top_speed = kmh; if (kmh > 450) checkAch(p); } }
        if (Number.isFinite(m.y)) p.yaw = m.y;
        if (Number.isFinite(m.x)) p.pitch = m.x;
        if (WEAPONS[m.w]) p.w = m.w;
        p.g = vec3(m.g);
        p.f = m.f | 0;
        if (p.pos[1] < this.map.killY) this.kill(p, null, 'void');
        break;
      }
      case 'hit': this.onHit(p, m); break;
      case 'push': this.onPush(p, m); break;
      case 'fire': this.onFire(p, m); break;
      case 'cough':
        if (p.alive && now() - p.coughT > 800) { p.coughT = now(); this.damage(p, 12, null, 'cough'); }
        break;
      case 'chat': {
        const text = clean(m.m, 120);
        if (text && now() - p.chatT > 400) { p.chatT = now(); this.broadcast({ t: 'chat', id: p.id, m: text }); }
        break;
      }
      case 'tbag': { // crouch-spammed too hard: your knees explode
        if (!p.alive || now() - (p.tbagT || 0) < 3000) break;
        p.tbagT = now();
        const c = center(p);
        this.broadcast({ t: 'fx', k: 'tbag', id: p.id, p: c.map(r2) });
        for (const t of this.players.values()) {
          if (t === p || !t.alive) continue;
          const tc = center(t);
          const to = [tc[0] - c[0], tc[1] - c[1], tc[2] - c[2]];
          const dist = Math.hypot(...to);
          if (dist > 6) continue;
          const f = 1 - dist / 6, dir = dist > 0.1 ? to.map((x) => x / dist) : [0, 1, 0];
          this.hurt(t, p, 'tbag', 70 * f + 10, [dir[0] * 34 * f, dir[1] * 34 * f + 10, dir[2] * 34 * f]);
        }
        this.kill(p, null, 'tbag');
        break;
      }
      case 'streaks': p.streaks = validStreaks(m.list); break;
      case 'deploy': { // use a killstreak from your tray (aimed ones land where you looked)
        const i = (p.pocket || []).indexOf(m.r);
        const at = vec3(m.at);
        if (i < 0 || !p.alive || !STREAKS[m.r]) break;
        if ((m.r === 'chickenstrike' || m.r === 'giantduck') && !at) break;
        p.pocket.splice(i, 1);
        if (m.r === 'scythe') p.scythe = true;
        send(p, { t: 'streak', reward: m.r });
        if (m.r === 'chickenstrike') {
          this.broadcast({ t: 'fx', k: 'strikeCall', id: p.id, p: at.map(r2) });
          for (let k = 0; k < 14; k++) setTimeout(() => {
            if (!this.players.has(p.id)) return;
            const a = Math.random() * Math.PI * 2, rr = Math.random() * 10;
            this.makeProj(p, 'chicken', [at[0] + Math.cos(a) * rr, at[1] + 45, at[2] + Math.sin(a) * rr], [0, -34, 0]);
          }, 600 + k * 170);
        } else if (m.r === 'giantduck') {
          this.makeHole([at[0], at[1] + 4, at[2]], p.id, { big: true });
        }
        this.broadcast({ t: 'chat', id: 0, m: `${p.name} used ${STREAKS[m.r] ? STREAKS[m.r].name : m.r}` });
        break;
      }
      case 'look': {
        if (now() - (p.lookT || 0) < 300) break;
        p.lookT = now();
        p.look = validLook(m.look, p.acct ? p.acct.achs : new Set());
        if (p.look.color) p.color = p.look.color;
        this.broadcast({ t: 'lk', id: p.id, look: p.look, color: p.color });
        break;
      }
      case 'card': {
        if (now() - (p.cardT || 0) < 2000) break;
        p.cardT = now();
        p.card = cleanCard(m.card);
        this.broadcast({ t: 'cd', id: p.id, card: p.card }, p.id);
        break;
      }
      case 'kfx':
        (async () => {
          if (p.acct) { const u = await store.get(p.acct.n).catch(() => null); if (u) p.inv = u.inv || {}; }
          p.kfx = ownedKill(m.id, p.inv);
        })();
        break;
      case 'kc': p.kc = !!m.on; break;
      case 'use': this.tryUse(p); break;
      case 'item': this.useItem(p, m); break;
      case 'vote':
        if (this.vote && Number.isInteger(m.i) && m.i >= 0 && m.i < this.vote.options.length) {
          this.vote.votes.set(p.id, m.i);
          this.broadcast({ t: 'votes', counts: this.voteInfo().counts });
        }
        break;
      case 'respawn': // killcam finished or skipped
        if (!p.alive) p.respawnAt = Math.min(p.respawnAt, Math.max(now(), (p.deadT || 0) + 1500));
        break;
      case 'redraw':
        if (p.alive && now() - (p.redrawT || 0) > 2500) { p.redrawT = now(); deal(p); }
        break;
      case 'cfg': this.setCfg(p, m); break;
      case 'skin':
        if (now() - p.skinT > 250) {
          p.skinT = now();
          (async () => {
            if (p.acct) { const u = await store.get(p.acct.n).catch(() => null); if (u) p.inv = u.inv || {}; }
            p.skins = enforceSkins(cleanSkins(m.s), p.inv);
            this.broadcast({ t: 'sk', id: p.id, s: p.skins }, p.id);
          })();
        }
        break;
      case 'pi': send(p, { t: 'po', c: m.c }); break;
    }
  }

  roundInfo() {
    if (!this.round) return null;
    const r = { target: this.round.target, left: Math.max(0, (this.round.over ? this.round.next : this.round.ends) - now()), over: this.round.over, game: this.game };
    if (this.teamsOn()) r.sc = [this.score[1], this.score[2]];
    const b = this.bomb;
    if (b) {
      const n = now();
      r.bomb = { att: b.att, ph: b.ph, n: b.n, wins: [b.wins[1], b.wins[2]], carrier: b.carrier, drop: b.drop, p: b.p, site: b.site,
        left: Math.max(0, (b.ph === 'planted' ? b.explodeAt : b.between || b.ends) - n),
        act: b.act ? { k: b.act.kind, by: b.act.id, f: Math.min(1, (n - b.act.start) / ((b.act.kind === 'plant' ? BOMB.plant : BOMB.defuse) * 1000)) } : 0 };
    }
    return r;
  }
  tickRound() {
    const r = this.round;
    if (!r) return;
    const n = now();
    if (r.over) { if (n >= r.next) this.startRound(); return; }
    if (!this.humans().length) return;
    if (this.game === 'bomb' && this.bomb) { this.tickBomb(n); return; }
    if (this.teamsOn()) { if (this.score[1] >= r.target || this.score[2] >= r.target || n >= r.ends) this.endRound(); return; }
    let top = null;
    for (const p of this.players.values()) if (!top || p.kills > top.kills) top = p;
    if ((top && top.kills >= r.target) || n >= r.ends) this.endRound();
  }
  endRound() {
    const list = [...this.players.values()].filter((p) => !(p.isBot && p.ai.dummy)).sort((a, b) => b.kills - a.kills || a.deaths - b.deaths);
    // team games: the winning team takes it, and its best player gets the roll
    let winTeam = 0;
    if (this.teamsOn()) {
      const sc = this.game === 'bomb' && this.bomb ? this.bomb.wins : this.score;
      winTeam = sc[1] === sc[2] ? 0 : sc[1] > sc[2] ? 1 : 2;
    }
    const pool = winTeam ? list.filter((p) => p.team === winTeam) : list;
    const winner = pool[0] && (winTeam || pool[0].kills > 0) ? pool[0] : null;
    this.round.over = true;
    this.round.next = now() + VOTE_MS + 2000;
    this.round.winTeam = winTeam;
    if (this.bomb) { this.bomb.act = null; this.bomb.between = 0; }
    this.startVote();
    let roll = null;
    if (winner && !winner.isBot) {
      const eligible = this.mode === 'ffa' ? this.humans().length >= 2 : list.filter((p) => p.isBot).length >= 3;
      if (!winner.acct) roll = { n: 0, guest: 1 };
      else if (!eligible) roll = { n: 0, why: this.mode === 'ffa' ? 'need at least 2 real players for a roll' : 'need at least 3 bots for a roll' };
      else {
        stat(winner, 'wins', 1); stat(winner, 'xp', 50);
        const kind = randomContainer();
        store.grantRolls(winner.acct.n, kind, 1).catch((e) => console.error('roll grant failed', e.message));
        roll = { n: 1, kind, why: 'won the round' };
      }
    }
    this.broadcast({ t: 'round', over: 1, winner: winner ? winner.id : 0, winTeam, game: this.game, sc: this.teamsOn() ? (this.game === 'bomb' && this.bomb ? [this.bomb.wins[1], this.bomb.wins[2]] : [this.score[1], this.score[2]]) : null,
      top: list.slice(0, 6).map((p) => [p.id, p.name, p.kills, p.deaths, p.team || 0]), next: VOTE_MS + 2000 });
    const r = this.round;
    setTimeout(() => {
      if (this.round !== r || !r.hl || r.hl.pending || !r.hl.clip || !r.hl.clip.frames.length) return;
      const { label, id, name, color, card, clip } = r.hl;
      this.broadcast({ t: 'hl', label, id, name, color, card, clip });
    }, 1600);
    if (roll) send(winner, { t: 'roll+', ...roll });
  }
  startRound() {
    this.resolveVote();
    for (const p of this.players.values()) { p.kills = 0; p.deaths = 0; }
    this.round = { target: (TARGETS[this.mode] || TARGETS.ffa)[this.game] || ROUND[this.mode].kills, ends: now() + ROUND[this.mode].time * 1000, over: false, next: 0 };
    this.score = { 1: 0, 2: 0 };
    this.clearTags();
    this.assignTeams();
    this.bomb = this.game === 'bomb' && this.teamsOn() ? { att: 1, n: 0, wins: { 1: 0, 2: 0 } } : null;
    if (this.bomb) { this.round.ends = now() + 3600 * 1000; this.newBombRound(true); }
    else this.resetWorld();
    this.broadcast({ t: 'round', start: 1, ...this.roundInfo() });
  }
  // switch game type (bots setup / match settings / the vote)
  setGame(g) {
    if (!GAMES[g] || (GAMES[g].sites && !(this.map.sites && this.map.sites.length))) return false;
    this.game = g;
    return true;
  }

  // ---------------------------------------------------------- map / mode vote between rounds
  startVote() {
    if (this.mode !== 'ffa' && this.mode !== 'bots') return;
    const games = GAME_ORDER.slice().sort(() => Math.random() - 0.5);
    const options = [], usedMaps = new Set();
    for (const g of games) {
      if (options.length >= 3) break;
      const maps = mapsFor(g, MAPS, MAP_ORDER).filter((m) => !usedMaps.has(m));
      if (!maps.length) continue;
      const m = pick(maps);
      usedMaps.add(m);
      options.push({ game: g, map: m });
    }
    this.vote = { options, votes: new Map(), ends: now() + VOTE_MS };
    this.broadcast({ t: 'vote', ...this.voteInfo() });
  }
  voteInfo() {
    const v = this.vote;
    if (!v) return null;
    const counts = v.options.map(() => 0);
    for (const i of v.votes.values()) counts[i]++;
    return { options: v.options.map((o) => ({ ...o, name: GAMES[o.game].name, mapName: MAPS[o.map].name })), counts, left: Math.max(0, v.ends - now()) };
  }
  resolveVote() {
    const v = this.vote;
    this.vote = null;
    if (!v || !v.options.length) return;
    const counts = v.options.map(() => 0);
    for (const i of v.votes.values()) counts[i]++;
    const max = Math.max(...counts);
    const top = v.options.filter((o, i) => counts[i] === max);
    const win = pick(top);
    const mapChanged = win.map !== this.cfg.map;
    this.cfg.map = win.map;
    this.setGame(win.game);
    this.projectiles.clear(); this.peels.clear(); this.holes.clear();
    if (mapChanged) this.broadcast({ t: 'cfg', cfg: this.cfg });
    this.broadcast({ t: 'chat', id: 0, m: `next up: ${GAMES[this.game].name} on ${this.map.name}` });
  }

  // ---------------------------------------------------------- tags (kill confirmed)
  dropTag(t) {
    const g = { id: this.nextTag++, p: [r2(t.pos[0]), r2(t.pos[1] + 0.9), r2(t.pos[2])], team: t.team, born: now() };
    this.tags.set(g.id, g);
    this.broadcast({ t: 'tag+', id: g.id, p: g.p, team: g.team });
  }
  clearTags() { if (this.tags.size) { this.tags.clear(); this.broadcast({ t: 'tagc' }); } }
  tickTags(n) {
    if (!this.tags.size) return;
    for (const g of [...this.tags.values()]) {
      if (n - g.born > TAG_LIFE) { this.tags.delete(g.id); this.broadcast({ t: 'tagx', id: g.id }); continue; }
      for (const p of this.players.values()) {
        if (!p.alive || !p.team) continue;
        if (Math.hypot(p.pos[0] - g.p[0], p.pos[1] + 0.9 - g.p[1], p.pos[2] - g.p[2]) > 1.9) continue;
        const confirm = p.team !== g.team;
        if (confirm && this.round && !this.round.over) this.score[p.team]++;
        this.tags.delete(g.id);
        this.broadcast({ t: 'tagx', id: g.id, by: p.id, k: confirm ? 'confirm' : 'deny' });
        break;
      }
    }
  }

  // ---------------------------------------------------------- plant & defuse
  newBombRound(first) {
    const b = this.bomb;
    if (!first && b.n === BOMB.swapAfter) { b.att = 3 - b.att; this.broadcast({ t: 'chat', id: 0, m: 'SIDES SWAPPED' }); }
    b.n++;
    Object.assign(b, { ph: 'live', site: null, p: null, drop: null, explodeAt: 0, act: null, between: 0, ends: now() + BOMB.roundTime * 1000, carrier: 0 });
    for (const p of this.players.values()) if (p.ai) { p.ai.site = null; p.ai.route = null; }
    this.projectiles.clear(); this.peels.clear(); this.holes.clear();
    this.resetWorld();
    const att = this.fighters().filter((p) => p.team === b.att && p.alive);
    const carrier = att.find((p) => !p.isBot) || att[0];
    b.carrier = carrier ? carrier.id : 0;
    if (carrier) send(carrier, { t: 'bombyou' });
    this.broadcast({ t: 'bombev', k: 'round', n: b.n, att: b.att });
  }
  dropBomb(pos) {
    const b = this.bomb;
    if (!b || b.ph !== 'live') return;
    b.carrier = 0;
    const h = raycast([pos[0], pos[1] + 1, pos[2]], [0, -1, 0], 60, this.boxes);
    b.drop = h ? [r2(pos[0]), r2(h.point[1] + 0.15), r2(pos[2])] : null;
    if (!b.drop) { // fell into the void with it: it comes back to a random attacker
      const att = this.fighters().filter((p) => p.team === b.att && p.alive);
      if (att.length) b.carrier = pick(att).id;
    }
    this.broadcast({ t: 'bombev', k: 'drop' });
  }
  bombRoundWin(team, why) {
    const b = this.bomb;
    b.wins[team]++;
    b.ph = 'done'; b.act = null;
    this.broadcast({ t: 'bombev', k: 'win', team, why, wins: [b.wins[1], b.wins[2]] });
    if (b.wins[team] >= BOMB.wins) { this.endRound(); return; }
    b.between = now() + BOMB.between;
  }
  tickBomb(n) {
    const b = this.bomb;
    if (b.between) { if (n >= b.between) this.newBombRound(false); return; }
    if (b.ph === 'done') return;
    // dropped bomb: any attacker can grab it
    if (b.ph === 'live' && b.drop) {
      for (const p of this.players.values()) {
        if (!p.alive || p.team !== b.att) continue;
        if (Math.hypot(p.pos[0] - b.drop[0], p.pos[1] - b.drop[1], p.pos[2] - b.drop[2]) < BOMB.pickup) { b.carrier = p.id; b.drop = null; send(p, { t: 'bombyou' }); this.broadcast({ t: 'bombev', k: 'pickup', id: p.id }); break; }
      }
    }
    // planting / defusing: you have to keep holding F and stay put
    if (b.act) {
      const a = this.players.get(b.act.id);
      const hold = a && a.alive && n - (a.useT || 0) < 600 && dist3(a.pos, b.act.pos) < 1.6;
      const ok = hold && (b.act.kind === 'plant' ? b.carrier === a.id && siteAt(this.map, a.pos) : b.ph === 'planted' && dist3(a.pos, b.p) < BOMB.defuseRange + 0.6);
      if (!ok) b.act = null;
      else if (n - b.act.start >= (b.act.kind === 'plant' ? BOMB.plant : BOMB.defuse) * 1000) {
        if (b.act.kind === 'plant') {
          const site = siteAt(this.map, a.pos);
          Object.assign(b, { ph: 'planted', site: site.id, p: [r2(a.pos[0]), r2(a.pos[1] + 0.1), r2(a.pos[2])], explodeAt: n + BOMB.fuse * 1000, carrier: 0, act: null, planter: a.id });
          this.broadcast({ t: 'bombev', k: 'planted', site: site.id, id: a.id });
          if (a.acct) stat(a, 'xp', 10);
        } else {
          b.act = null;
          this.broadcast({ t: 'bombev', k: 'defused', id: a.id });
          if (a.acct) stat(a, 'xp', 15);
          this.bombRoundWin(3 - b.att, 'defused');
          return;
        }
      }
    }
    if (b.ph === 'planted' && n >= b.explodeAt) {
      const at = b.p.slice();
      b.ph = 'done';
      this.explodeAt(at, null, 'bomb', BOMB.radius, BOMB.dmg, 60);
      this.broadcast({ t: 'bombev', k: 'boom', p: at });
      this.bombRoundWin(b.att, 'exploded');
      return;
    }
    if (b.ph === 'live' && n >= b.ends) this.bombRoundWin(3 - b.att, 'time');
  }
  // someone is holding F (players send this every ~250ms while it's held; bots call it directly)
  tryUse(p) {
    const b = this.bomb;
    if (!b || !p.alive || b.between || b.ph === 'done') return;
    p.useT = now();
    if (b.act) return;
    if (b.ph === 'live' && b.carrier === p.id && siteAt(this.map, p.pos)) b.act = { id: p.id, kind: 'plant', start: now(), pos: p.pos.slice() };
    else if (b.ph === 'planted' && p.team !== b.att && dist3(p.pos, b.p) < BOMB.defuseRange) b.act = { id: p.id, kind: 'defuse', start: now(), pos: p.pos.slice() };
    if (b.act) this.broadcast({ t: 'bombev', k: b.act.kind, id: p.id });
  }

  tick(dt) {
    const n = now();
    this.tickRound();
    this.tickTags(n);
    this.tickItems(dt);
    for (const b of this.players.values()) if (b.isBot && b.alive) this.stepBot(b, dt);
    this.tickProjectiles(dt);
    this.tickHoles(dt);
    this.tickStatus(dt);
    this.tickPeels();
    this.tickWaves();
    for (const p of this.players.values()) {
      if (!p.alive && n >= p.respawnAt) {
        if (p.isBot && this.mode === 'coop') continue;
        p.alive = true; p.hp = 100; p.vel = [0, 0, 0]; p.spawnT = n; p.seq++;
        p.pos = p.isBot && p.ai.dummy ? p.ai.dummy.home.slice() : this.pickSpawn(p.isBot, p);
        p.slipUntil = 0; p.burnUntil = 0; p.sleepUntil = 0; p.frozenUntil = 0; p.frost = 0; p.ic = {}; p.healLeft = 0;
        send(p, { t: 'spawn', p: p.pos, q: p.seq });
        this.sendLoadout(p);
        if (!p.isBot) deal(p);
      }
    }
  }

  snapshot() {
    const ps = [];
    for (const p of this.players.values()) {
      ps.push([p.id, r2(p.pos[0]), r2(p.pos[1]), r2(p.pos[2]), r2(p.vel[0]), r2(p.vel[1]), r2(p.vel[2]),
        r2(p.yaw), r2(p.pitch), p.w, Math.max(0, Math.round(p.hp)), p.alive ? 1 : 0,
        p.g ? p.g.map(r2) : 0, p.f, p.kills, p.deaths]);
    }
    const n = now();
    this.recOdd = !this.recOdd;
    this.rec.frames.push({ s: n, p: ps, odd: this.recOdd, j: [...this.projectiles.values()].map((pr) => [pr.id, pr.k, r2(pr.p[0]), r2(pr.p[1]), r2(pr.p[2]), pr.tip || 0]) });
    while (this.rec.frames.length && this.rec.frames[0].s < n - REC_MS) this.rec.frames.shift();
    while (this.rec.ev.length && this.rec.ev[0].s < n - REC_MS) this.rec.ev.shift();
    this.broadcast({ t: 'sn', s: n, p: ps, wave: this.mode === 'coop' ? this.waveInfo() : undefined, round: this.roundInfo() || undefined });
  }
}

// ---------------------------------------------------------------- account stats
function stat(p, key, v) {
  if (!p.acct) return;
  const d = p.acct.d;
  if (key === 'best_wave' || key === 'top_speed') d[key] = Math.max(d[key] || 0, v);
  else d[key] = (d[key] || 0) + v;
  checkAch(p);
}
function liveStats(p) {
  const out = { ...p.acct.base };
  for (const [k, v] of Object.entries(p.acct.d)) out[k] = k === 'best_wave' || k === 'top_speed' ? Math.max(out[k] || 0, v) : (out[k] || 0) + v;
  return out;
}
function checkAch(p) {
  const now2 = achievementsFrom(liveStats(p));
  for (const id of now2) if (!p.acct.achs.has(id)) { p.acct.achs.add(id); send(p, { t: 'ach', id }); }
}
function flushStats(p) {
  if (!p.acct) return;
  const n = now();
  const mins = (n - p.acct.since) / 60000;
  p.acct.since = n;
  const d = p.acct.d;
  d.playtime = (d.playtime || 0) + Math.round(mins * 60);
  d.xp = (d.xp || 0) + Math.round(mins * 2);
  // fold this batch into the base so achievements stay right between saves
  for (const [k, v] of Object.entries(d)) p.acct.base[k] = k === 'best_wave' || k === 'top_speed' ? Math.max(p.acct.base[k] || 0, v) : (p.acct.base[k] || 0) + v;
  p.acct.d = {};
  if (d.top_speed) d.top_speed = Math.round(d.top_speed);
  store.addStats(p.acct.n, d).catch((e) => console.error('stats save failed', e.message));
}
setInterval(() => { for (const r of rooms.values()) for (const p of r.players.values()) flushStats(p); }, 60000);

function segs(s) {
  if (!Array.isArray(s)) return [];
  const out = [];
  for (const seg of s.slice(0, 12)) {
    if (!Array.isArray(seg) || seg.length !== 6 || !seg.every((x) => typeof x === 'number' && Number.isFinite(x))) continue;
    out.push(seg.map(r2));
  }
  return out;
}

function roomFor(mode, ws) {
  if (!MODES[mode]) mode = 'ffa';
  const id = mode === 'ffa' || mode === 'coop' ? mode : `${mode}:${nextId}:${Math.random().toString(36).slice(2, 7)}`;
  if (!rooms.has(id)) rooms.set(id, new Room(id, mode));
  return rooms.get(id);
}

// ---------------------------------------------------------------- sockets
wss.on('connection', (ws) => {
  let me = null;
  ws.isAlive = true;
  ws.on('pong', () => { ws.isAlive = true; });
  ws.on('message', (data) => {
    let m;
    try { m = JSON.parse(data); } catch { return; }
    if (!m || typeof m !== 'object') return;
    if (!me) {
      if (m.t !== 'join' || ws.joining) return;
      ws.joining = true;
      (async () => {
        const u = m.token ? await accounts.verify(m.token).catch(() => null) : null;
        if (u) {
          const base = {}; for (const k of STAT_KEYS) base[k] = u[k] || 0;
          m._name = u.name; m._acct = { n: u.name_lower, d: {}, since: now(), base, achs: achievementsFrom(base) };
          m._level = levelOf(u.xp); m._inv = u.inv || {}; m._achs = m._acct.achs;
        }
        else {
          const want = clean(m.name, 16);
          if (want && await store.get(want.toLowerCase()).catch(() => null)) m._name = want.slice(0, 10) + ' (guest)';
        }
        if (ws.readyState !== 1) return;
        const room = roomFor(m.mode, ws);
        me = room.addHuman(ws, m);
      })().catch((e) => { console.error('join failed', e); ws.close(); });
      return;
    }
    me.room.handle(me, m);
  });
  ws.on('close', () => {
    if (!me) return;
    console.log(`- ${me.name} (#${me.id}) <- ${me.room.id}`);
    me.room.remove(me);
  });
});

// ---------------------------------------------------------------- loops
const TICK = 1 / 60;
setInterval(() => { for (const r of rooms.values()) r.tick(TICK); }, TICK * 1000);
setInterval(() => { for (const r of rooms.values()) if (r.players.size) r.snapshot(); }, 50);
setInterval(() => {
  for (const ws of wss.clients) {
    if (!ws.isAlive) { ws.terminate(); continue; }
    ws.isAlive = false;
    ws.ping();
  }
}, 10000);

server.listen(PORT, () => {
  const lan = Object.values(os.networkInterfaces()).flat().filter((i) => i && i.family === 'IPv4' && !i.internal).map((i) => `http://${i.address}:${PORT}`);
  console.log('');
  console.log('  JANKFIRE is running');
  console.log(`  you:                 http://localhost:${PORT}`);
  if (lan.length) console.log(`  friends on your wifi: ${lan.join('  ')}`);
  console.log(`  accounts saved to:   ${store.kind === 'supabase' ? 'Supabase' : (path.relative(ROOT, store.file).startsWith('..') ? store.file : path.relative(ROOT, store.file))}`);
  console.log('  close this window to stop the server');
  console.log('');
  if (process.env.JF_OPEN) {
    const url = `http://localhost:${PORT}`;
    const cmd = process.platform === 'win32' ? ['cmd', ['/c', 'start', '', url]] : process.platform === 'darwin' ? ['open', [url]] : ['xdg-open', [url]];
    try { spawn(cmd[0], cmd[1], { stdio: 'ignore', detached: true }).unref(); } catch { /* no browser, no problem */ }
  }
});
// save everyone's stats right now (used on shutdown and by the desktop app when it closes)
export function shutdown() {
  for (const r of rooms.values()) for (const p of r.players.values()) flushStats(p);
  if (store.flushNow) store.flushNow();
}
for (const sig of ['SIGINT', 'SIGTERM']) process.on(sig, () => { shutdown(); setTimeout(() => process.exit(0), 300); });
