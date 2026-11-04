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
import { ownedSkin, ownedKill, ownedGrapple, randomContainer, CONTAINERS, COSMETICS } from './shared/cosmetics.js';
import { owns, SPRAY } from './shared/cosmetics.js';
import { validLook, achievementsFrom, ACHIEVEMENTS } from './shared/looks.js';
import { STAT_KEYS } from './server/store.js';
import { soapAt, trapBoxes, trapPreroll } from './shared/wand.js';
import { MAPS, MAP_ORDER } from './shared/map.js';
import { GAMES, GAME_ORDER, TEAMS, TARGETS, BOMB, TAG_LIFE, VOTE_MS, siteAt, mapsFor } from './shared/modes.js';
import { WEAPONS, HOOK, HIPFIRE, BOT_DIFF, MODES, STREAKS, FLAGS, ARROW_TIPS, ITEMS, DEFAULT_LOADOUT, validStreaks, fireRate } from './shared/weapons.js';
import { stepProjectile, rayBox, raycast, playerBoxes, movePlayer, PH } from './shared/physics.js';
import { verdict } from './shared/verdict.js';

import { WRECK, slamSize, ramDmg } from './shared/weapons.js'; // wrecking ball
import { query } from './shared/physics.js';
import { epicCheck, epicCamMs, EPIC } from './shared/epic.js';
import { holeDrag, steer } from './shared/physics.js';
import { steer as steerTo } from './shared/homing.js'; // homing slippers (steerTo(v, from, to, max)); the duck's steer(v, dir, max) is physics.js's
import { PARRY } from './shared/weapons.js';
import { ropeStep, ropeJump, ROPE } from './shared/hookphys.js';
import { query as boxQuery } from './shared/physics.js';

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
if (process.env.JF_WRECK) STREAKS.wreckingball.kills = Number(process.env.JF_WRECK) || STREAKS.wreckingball.kills; // test knob: earn the wrecking ball fast
if (process.env.JF_WRECK_DUR) STREAKS.wreckingball.dur = Number(process.env.JF_WRECK_DUR) || STREAKS.wreckingball.dur; // test knob: a longer ball (slow test browsers)
const ROUND = { ffa: { kills: 20, time: 360 }, bots: { kills: 15, time: 300 } };
if (process.env.JF_ROUND_KILLS) for (const r of Object.values(ROUND)) r.kills = Number(process.env.JF_ROUND_KILLS) || r.kills;
// Never Landed: grace after each spawn to get off the ground (+ slack for lag), and how late you can join a match and still count
const AIR = { grace: 3000, slack: 400, join: 5000 };
// feet resting on a box top. jump pads don't count: they launch you, you can't stand on them
function onBoxTop(pos, boxes) {
  const hw = PH.halfW;
  for (const b of boxQuery(boxes, pos[0] - hw, pos[2] - hw, pos[0] + hw, pos[2] + hw, [])) {
    if (b.pad || pos[1] < b.max[1] - 0.02 || pos[1] > b.max[1] + 0.03) continue; // narrow: positions are rounded to 1 cm
    if (pos[0] + hw > b.min[0] && pos[0] - hw < b.max[0] && pos[2] + hw > b.min[2] && pos[2] - hw < b.max[2]) return true;
  }
  return false;
}
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
const GRAP_IDS = Object.keys(COSMETICS.grapple).filter((k) => k !== 'rope');
// name cards: a small picture you drew or uploaded, as a data url. anything else is dropped.
const CARD_RE = /^data:image\/(jpeg|png|webp);base64,[A-Za-z0-9+/]+=*$/;
function cleanCard(c) { return typeof c === 'string' && c.length <= 24000 && CARD_RE.test(c) ? c : ''; }
// replays: the server keeps the last few seconds of everything so it can send the play of the round
const REC_T = new Set(['kill', 'boom', 'fx', 'pd', 'he']);
const REC_FX = new Set(['shot', 'swing', 'tbag', 'reflect']);
REC_FX.add('verdict'); // scales of justice: highlights show the ruling
const REC_MS = 12000;
for (const k of ['trap', 'trapx']) REC_T.add(k); // bubble wand: replays draw the giant soap bubble too
for (const t of ['parry', 'guard']) REC_T.add(t); // katana parries show up in killcams too
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
    this.sprays = new Map(); this.sprayMap = ''; // owner id -> graffiti, and the map they were painted on
    this.cfg = { map: mode === 'training' ? 'range' : mode === 'coop' ? 'warehouse' : 'islands', hip: 'normal', bots: 5, diff: 'normal' };
    this.wave = 0; this.toSpawn = 0; this.interUntil = 0;
    this.round = ROUND[mode] ? { target: ROUND[mode].kills, ends: now() + ROUND[mode].time * 1000, over: false, next: 0 } : null;
    if (mode === 'coop') this.interUntil = now() + 4000;
    if (this.round) this.round.t0 = now();
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
    lo.item = pick(Object.keys(ITEMS)); // the popper + reverse card left the secondary pool for this one
    return lo;
  }
  sendLoadout(p) {
    if (p.isBot) { if (GAMES[this.game].random && !p.ai.dummy) { p.w = pick(BOT_GUNS); p.ai.ammo = WEAPONS[p.w].mag || 1; } return; }
    const rnd = (this.mode === 'ffa' || this.mode === 'bots') && GAMES[this.game].random;
    if (rnd) { p.forced = true; const lo = this.randomLoadout(); p.item = lo.item; send(p, { t: 'loadout', lo }); }
    else if (p.forced) { p.forced = false; if (p.ownItem) p.item = p.ownItem; send(p, { t: 'loadout', lo: null }); }
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
  info(p) { return { id: p.id, name: p.name, color: p.color, skins: p.skins, bot: p.isBot, level: p.level, look: p.look, card: p.card || '', team: p.team || 0, grap: p.grap || 'rope' }; }

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
    p.grap = ownedGrapple(m.grap, inv);
    p.kc = !!m.kc;
    p.item = p.ownItem = this.okItem(m.item) || DEFAULT_LOADOUT.item;
    if (this.mode === 'bots' && m.cfg && GAMES[m.cfg.game] && !this.humans().length) this.setGame(m.cfg.game);
    this.joinTeam(p);
    if (p.team) p.pos = this.pickSpawn(false, p);
    this.players.set(p.id, p);
    // in from the start (or close enough): your Never Landed run counts. the welcome below is your first spawn
    if (this.round && !this.round.over && now() - (this.round.t0 || 0) < AIR.join) p.air = { ok: !(this.airBad && this.airBad.has(name)), rest: 0 };
    send(p, {
      t: 'welcome', id: p.id, name, color: p.color, pos: p.pos, q: p.seq, mode: this.mode, cfg: this.cfg,
      players: [...this.players.values()].filter((o) => o !== p).map((o) => this.info(o)),
      peels: [...this.peels.values()].map((pl) => ({ id: pl.id, p: pl.p })),
      projs: [...this.projectiles.values()].map((pr) => ({ id: pr.id, k: pr.k, p: pr.p, v: pr.v, o: pr.o })),
      holes: [...this.holes.values()].map((h) => ({ id: h.id, p: h.p, o: h.o, big: h.big, on: h.on || 0, age: (now() - h.born) / 1000 })),
      wave: this.waveInfo(), level: p.level, account: !!p.acct, round: this.roundInfo(),
      bubbles: [...this.bubbles.values()].map((b) => ({ id: b.id, p: b.p, r: b.r, left: b.until - now() })),
      kat: [...this.players.values()].filter((o) => o.kat).map((o) => [o.id, o.kat]),
      game: this.game, team: p.team || 0, tags: [...this.tags.values()].map((g) => ({ id: g.id, p: g.p, team: g.team })), vote: this.voteInfo(),
      sprays: this.sprayList(),
    });
    this.broadcast({ t: 'pj', ...this.info(p) }, p.id);
    send(p, { t: 'tip', tip: p.tip });
    for (const t of this.players.values()) if (t.trap) send(p, { t: 'trap', ...this.trapInfo(t) }); // anyone already floating in a soap bubble
    send(p, { t: 'court', s: [...this.players.values()].filter((o) => o.streak > 0).map((o) => [o.id, o.streak]) }); // scales of justice: streaks so far
    if (p.air && p.air.ok) send(p, { t: 'air', on: 1, grace: AIR.grace });
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
    if (!opts.dummy && Math.random() < 0.5) b.grap = pick(GRAP_IDS); // bots show off ropes you can roll
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
      if (t.trap) continue; // sealed in a soap bubble: shooting it would only set them free, wait for the pop
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
    if ((this.players.get(ai.target) || {}).trap) ai.retarget = 0; // whoever it was after just got sealed in a soap bubble
    if (n > ai.retarget) { const t = this.botTarget(b); ai.target = t ? t.id : 0; ai.retarget = n + 400 + Math.random() * 600; }
    const t = this.players.get(ai.target);
    let wx = 0, wz = 0, jump = false;
    const w = WEAPONS[b.w];
    const pref = b.w === 'sniper' ? [25, 60] : b.w === 'shotgun' ? [3, 9] : b.w === 'marbles' ? [1.5, 4] : b.w === 'chicken' ? [10, 30] : [7, 22];
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
          for (const hb of p.trap ? trapBoxes(p.pos) : playerBoxes(p.pos)) { // a soap bubble gets hit on the bubble
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
    if (b.trap) { this.driftTrapped(b); return; } // in a soap bubble: no thinking, just floating
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
    // on the rope: the same pendulum rope as a player's grapple (shared/hookphys.js), so bots swing smoothly too.
    // let go near the point (or when it's been a while) with a grapple jump
    const hk = b.ai && b.ai.hook;
    if (hk) {
      ropeStep(hk, hk.point, b.pos, v, dt, 26);
      b.ropeLift = 1;
      if (hk.dist < 4.5 || n > hk.until || slipping) {
        // grapple jump the way they're facing, a bit up, and never flung into the surface they're hooked on
        if (!slipping) { const cp = Math.cos(b.pitch); ropeJump(v, [-Math.sin(b.yaw) * cp, Math.max(0.3, Math.sin(b.pitch)), -Math.cos(b.yaw) * cp], hk.n); }
        b.ai.hook = null; b.g = null;
      }
      b.onGround = false;
    } else if (b.ropeLift > 0) { // let go: the rope's share of their weight fades out like a player's (no one-step drop)
      b.ropeLift = Math.max(0, b.ropeLift - dt / 0.15);
      v[1] += 26 * ROPE.lift * b.ropeLift * dt;
    }
    this.eatMomentum(b, dt);
    const was = b.onGround;
    const res = movePlayer(b.pos, v, dt, this.boxes, was);
    b.onGround = !!res.ground && v[1] <= 0.01;
    if (b.onGround && res.ground.pad && !b.ai.dummy) { const pd = res.ground.pad; v[0] += pd[0]; v[1] = pd[1]; v[2] += pd[2]; b.onGround = false; }
    b.f = slipping ? 16 : 0;
    if (b.pos[1] < this.map.killY) this.kill(b, null, 'void');
  }

  // ---------------------------------------------------------- items (G): charges refill over time
  // only ITEMS' own keys: '__proto__' / 'constructor' must not reach p.ic (that would write onto Object.prototype)
  okItem(id) { return typeof id === 'string' && Object.hasOwn(ITEMS, id) ? id : null; }
  // the item in your loadout ('lo' / join). switching counts right away only before you've used one this life
  setItem(p, id) {
    id = this.okItem(id);
    if (!id || p.forced) return; // randomizer: you get its item
    p.ownItem = id;
    if (!p.alive || (now() - p.spawnT < 5500 && (p.itemT || 0) < p.spawnT)) p.item = id;
  }
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
    const it = Object.hasOwn(ITEMS, m.i) ? ITEMS[m.i] : null;
    if (!it || !p.alive || m.i !== p.item) return; // only the one item in your loadout
    const c = this.itemCharges(p, m.i);
    if (c.n <= 0 || now() - (p.itemT || 0) < 400) return;
    p.itemT = now();
    c.n--;
    if (!c.next) c.next = now() + it.recharge * 1000;
    send(p, { t: 'ic', i: m.i, n: c.n, next: c.next ? c.next - now() : 0 });
    let o = vec3(m.o);
    if (!o || dist3(o, eyeOf(p)) > 4) o = eyeOf(p);
    const d = norm(vec3(m.d)) || [0, 0, -1];
    if (m.i === 'wand') { this.blowWand(p, o, d); return; }
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
    } else if (m.i === 'popper') this.popperUse(p, o, d);
    else if (m.i === 'reverse') this.reverseUse(p);
  }
  // party popper (item): the client finds who's in its cone and sends 'hit's. they only count for a moment after
  // a charge was really spent here, once per target, and only on people in front of where you aimed
  popperUse(p, o, d) {
    p.pop = { t: now(), d, hit: new Set() };
    this.broadcast({ t: 'fx', k: 'swing', w: 'popper', id: p.id, a: o.map(r2) }, p.id);
  }
  popperHit(p, t, toT) {
    const w = WEAPONS.popper, pop = p.pop;
    if (!pop || now() - pop.t > 750 || pop.hit.has(t.id) || !this.rangeOk(p, t, w.range)) return;
    const e = eyeOf(p), to = [t.pos[0] - e[0], t.pos[1] + 1 - e[1], t.pos[2] - e[2]], dist = Math.hypot(...to);
    if (dist > 2.5 && (to[0] * pop.d[0] + to[1] * pop.d[1] + to[2] * pop.d[2]) / dist < Math.cos(w.cone + 0.35)) return; // point blank counts from any angle (positions lag)
    pop.hit.add(t.id);
    this.hurt(t, p, 'popper', 0, [toT[0] * w.kb, toT[1] * w.kb + w.kbUp, toT[2] * w.kb]);
  }
  // reverse card (item): for a few seconds everything aimed at you goes back to whoever sent it (see hurt)
  reverseUse(p) {
    const dur = WEAPONS.reverse.dur;
    p.reverseUntil = now() + dur * 1000;
    this.broadcast({ t: 'fx', k: 'reverse', id: p.id, dur });
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

  // ---------------------------------------------------------- bubble wand: soap bubbles that seal people in a giant one
  // G blows a short stream of slow wobbly bubbles: server projectiles on the exact path in shared/wand.js
  blowWand(p, o, d) {
    const it = ITEMS.wand, w = WEAPONS.soap, ey = eyeOf(p);
    const od = [o[0] - ey[0], o[1] - ey[1], o[2] - ey[2]], ol = Math.hypot(...od);
    if (ol > 1e-3 && raycast(ey, od.map((x) => x / ol), ol, this.boxes)) o = ey; // no blowing from the far side of a wall
    const off = [o[0] - p.pos[0], o[1] - p.pos[1] - 0.15, o[2] - p.pos[2]]; // the wand is at your mouth, a bit under your eyes
    for (let i = 0; i < it.bubbles; i++) setTimeout(() => {
      if (this.players.get(p.id) !== p || !p.alive || p.trap) return;
      const s = spreadDir(d, i ? 0.09 : 0.02), sp = w.speed * (0.85 + Math.random() * 0.3);
      const e = [p.pos[0] + off[0], p.pos[1] + off[1], p.pos[2] + off[2]];
      const wall = raycast(e, s, 0.8, this.boxes);
      const k = wall ? Math.max(0, wall.t - w.r - 0.05) : 0.8;
      const pos = [e[0] + s[0] * k, e[1] + s[1] * k, e[2] + s[2] * k].map(r2);
      // your momentum carries them, but only so much: p.vel is whatever the client said, and a 1e5 m/s bubble would
      // sweep half the map in its first tick
      const pl = Math.hypot(...p.vel), ik = pl > 25 ? 0.3 * 25 / pl : 0.3;
      const vel = [s[0] * sp + p.vel[0] * ik, s[1] * sp + p.vel[1] * ik + 0.5, s[2] * sp + p.vel[2] * ik].map(r2);
      this.makeProj(p, 'soap', pos, vel, { born: now(), p0: pos.slice(), v0: vel.slice() });
    }, i * it.gap);
  }
  stepSoap(pr, n, owner, prev, dt) {
    const w = WEAPONS.soap, age = (n - pr.born) / 1000;
    if (!owner || age > w.life) { this.removeProj(pr); return; }
    soapAt(pr.p0, pr.v0, pr.id, age, pr.p);
    for (let k = 0; k < 3; k++) pr.v[k] = (pr.p[k] - prev[k]) / dt; // only for late joiners: roughly where it's heading now
    // walls, floors and the void pop it
    const seg = [pr.p[0] - prev[0], pr.p[1] - prev[1], pr.p[2] - prev[2]], len = Math.hypot(...seg);
    const h = len > 1e-6 ? raycast(prev, seg.map((x) => x / len), len + w.r, this.boxes) : null;
    if (h) { const b = Math.max(0, h.t - w.r) / len; for (let k = 0; k < 3; k++) pr.p[k] = prev[k] + seg[k] * b; this.removeProj(pr); return; }
    if (pr.p[1] < this.map.killY) { this.removeProj(pr); return; }
    // it pops on the outside of a shield bubble
    for (const b of this.bubbles.values()) if (dist3(pr.p, b.p) < b.r && dist3(prev, b.p) >= b.r) { this.removeProj(pr); return; }
    // the first person it touches (not you, not your team) gets sealed in
    const hits = this.sweep(prev, pr.p, w.r, (t) => t.id === pr.o || this.friendly(owner, t));
    if (!hits.length) return;
    const t = hits[0].t;
    pr.p = hits[0].at;
    this.removeProj(pr);
    const dir = norm([pr.v0[0], 0, pr.v0[2]]) || norm([t.pos[0] - owner.pos[0], 0, t.pos[2] - owner.pos[2]]) || [0, 0, 0]; // away from the blower
    this.trapPlayer(t, owner, dir);
  }
  trapInfo(t) { return { id: t.id, by: t.trap.by, left: Math.max(0, t.trap.until - now()), v: t.trap.v }; }
  // sealed in: can't move or attack, floats up and along dir, pops after dur. humans float on their own client
  // (movement is theirs), bots in driftTrapped. no new bubble for a moment after one pops.
  trapPlayer(t, owner, dir, reflected) {
    const it = ITEMS.wand, n = now();
    if (!t.alive || t.trap || n < (t.trapSafe || 0) || (this.round && this.round.over)) return false;
    if (this.isBall(t, n)) return false; // a 2 m steel wrecking ball just bursts the soap (its client rolls it, a bubble can't hold it)
    if (owner && owner !== t && !t.isBot && n - t.spawnT < 1200) return false; // spawn protection
    for (const b of this.bubbles.values()) if (this.inBubble(b, t)) return false; // soap can't get into a shield bubble
    if (!reflected && owner && owner !== t && owner.alive && t.reverseUntil > n) { // reverse card: the blower gets sealed in instead
      this.broadcast({ t: 'fx', k: 'reflect', id: t.id, by: owner.id });
      return this.trapPlayer(owner, t, [-dir[0], 0, -dir[2]], true);
    }
    // at = where the bubble should have them by now (humans move themselves, see holdTrapped), slack = lag allowance
    t.trap = { by: owner ? owner.id : 0, until: n + it.dur * 1000, v: [dir[0] * it.drift, it.rise, dir[2] * it.drift].map(r2), seq: t.seq,
      at: t.pos.slice(), atT: n, slack: 2.5 + Math.min(30, Math.hypot(...t.vel)) * 0.25 };
    t.g = null; t.burnUntil = 0; // no air in there: the fire goes out
    if (t.ai) t.ai.hook = null;
    this.tag(t, owner, 'soap');
    this.broadcast({ t: 'trap', ...this.trapInfo(t) });
    return true;
  }
  // pop: a hit (by = who, with w), time, or they died / respawned. whoever set up the drop is tagged so a fall into the
  // void is their kill: an enemy who shot it open, otherwise the bubbler
  popTrap(t, why, by, w) {
    const tr = t.trap;
    if (!tr) return false;
    t.trap = null;
    const held = (now() - tr.until) / 1000 + ITEMS.wand.dur; // s they were in it
    t.trapSafe = now() + Math.max(ITEMS.wand.safe, held * ITEMS.wand.safeK) * 1000; // so two wands can't keep someone in one for good
    const owner = this.players.get(tr.by);
    if (t.alive && (why === 'hit' || why === 'time')) {
      if (by && by !== t && by !== owner && !this.friendly(by, t)) this.tag(t, by, w);
      else this.tag(t, owner, 'soap');
    }
    // p: they weren't going where it floated (lag, or a client that won't drift): drop them from where the server has them
    this.broadcast({ t: 'trapx', id: t.id, why, pb: by ? by.id : 0, p: why === 'time' && tr.off && !t.isBot ? t.pos.map(r2) : undefined });
    return true;
  }
  tickTraps(n) {
    for (const p of this.players.values()) {
      const tr = p.trap;
      if (!tr) continue;
      if (!p.alive || tr.seq !== p.seq) this.popTrap(p, 'gone');
      else if (n >= tr.until) this.popTrap(p, 'time');
      else if (!p.isBot) { // by the clock, like their client. held every tick: a client that goes quiet still floats
        movePlayer(tr.at, tr.v.slice(), Math.min(0.1, (n - tr.atT) / 1000), this.boxes, false); tr.atT = n;
        this.holdTrapped(p);
      }
    }
  }
  // movement is the client's, but nobody steers a soap bubble: a sealed-in player's reported position is kept within
  // reach of where the bubble would have floated them (the slack covers lag and how fast they were going when it hit)
  // rep = from their own report. the first one that is drifting with the bubble (their client got the 'trap') moves the
  // path onto them (once, and not far): the server's guess started where it last had them and can snag on a ledge
  // their client floats past
  holdTrapped(p, rep) {
    const tr = p.trap, d = dist3(p.pos, tr.at);
    if (rep && !tr.ack && d <= Math.min(tr.slack, 3) && dist3(p.vel, tr.v) < 0.3) { tr.ack = 1; tr.at = p.pos.slice(); return this.holdTrapped(p); }
    if (rep) tr.off = d > tr.slack;
    if (d > tr.slack) for (let k = 0; k < 3; k++) p.pos[k] = tr.at[k] + (p.pos[k] - tr.at[k]) * (tr.slack / d);
    p.vel = tr.v.slice(); p.g = null;
  }
  driftTrapped(b) {
    const tr = b.trap, n = now();
    b.vel = tr.v.slice();
    movePlayer(b.pos, b.vel, Math.min(0.1, (n - tr.atT) / 1000), this.boxes, false); // by the clock: same speed when ticks run late
    tr.atT = n;
    b.onGround = false; b.g = null; b.f = 0;
    if (b.pos[1] < this.map.killY) this.kill(b, null, 'void');
  }

  // ---------------------------------------------------------- combat
  tag(t, attacker, w) {
    if (!attacker || attacker === t) return;
    t.lastAttacker = attacker.id; t.lastAttackW = w; t.lastAttackT = now();
  }
  knock(t, v, w) {
    if (Math.hypot(v[0], v[1], v[2]) >= 1) t.knockT = now(); // EPIC anti-farm: getting shoved around isn't moving (0-knockback bullets don't count)
    if (t.isBot) {
      if (t.ai.dummy && t.ai.dummy.move) return;
      t.vel[0] += v[0]; t.vel[1] += v[1]; t.vel[2] += v[2];
      if (v[1] > 0.5 && t.onGround) { t.onGround = false; t.pos[1] += 0.02; }
      return;
    }
    send(t, { t: 'kb', v: v.map(r2), w });
  }
  slip(t) {
    t.knockT = now(); // sliding on a banana isn't moving either
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
    if (t.trap) return; // sealed in a soap bubble: burning, gas and the like can't get in (a real hit pops it, see hurt)
    if (this.round && this.round.over && w !== 'void') return;
    if (attacker && attacker !== t && now() - t.spawnT < 1200 && !t.isBot) return; // spawn protection
    if (this.friendly(attacker, t)) return;
    if (this.bubbleBlocks(attacker, t)) return;
    if (attacker && attacker.isBot && !t.isBot && this.mode !== 'bots') amt *= 0.6; // coop bots hit softer
    t.hp -= amt;
    if (!attacker || attacker === t) t.selfHurtT = now(); // EPIC: coughing yourself down to 4 HP doesn't make you a clutch hero
    t.lastHs = !!hs;
    if (hs && attacker && attacker !== t && attacker.acct && this.mode !== 'training') stat(attacker, 'headshots', 1);
    this.tag(t, attacker, w);
    this.broadcast({ t: 'dmg', to: t.id, from: attacker ? attacker.id : 0, a: Math.round(Math.min(amt, 999)), w, hs: !!hs, ko: t.hp <= 0 ? 1 : undefined }); // ko: this hit kills (heavier headshot sounds)
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
    if (t.trap && !this.bubbleBlocks(attacker, t) && this.popTrap(t, 'hit', attacker, w)) return; // in a soap bubble: the first hit (teammates' too) only pops it
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
    if (t.trap) this.popTrap(t, 'dead');
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
    if (killer && killer !== t && (w === 'katana' || w === 'parry')) { // the katana grows with every kill (parries too)
      killer.kat = Math.min(WEAPONS.katana.growMax, (killer.kat || 0) + 1);
      this.broadcast({ t: 'kat', id: killer.id, n: killer.kat });
    }
    if (t.kat) { t.kat = 0; this.broadcast({ t: 'kat', id: t.id, n: 0 }); }
    if (killer && killer !== t) {
      killer.kills++;
      killer.streak = (killer.streak || 0) + 1;
      if (killer.lastKiller === t.id) killer.lastKiller = 0; // revenge served (scales of justice)
      t.lastKiller = killer.id;
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
    // EPIC kill: the victim (if they have killcams on) has to watch all of it. their respawn waits it out, never past the 9 s cap
    const ep = this.epicOf(killer, t, w, via);
    t.lastEpic = ep;
    t.epicLock = ep && !t.isBot && t.kc ? Math.min(t.respawnAt, now() + epicCamMs()) : 0;
    if (t.epicLock) ep.lock = 1;
    if (killer && killer !== t && this.round && !this.round.over && !(t.isBot && t.ai && t.ai.dummy) && this.mode !== 'training') this.hlCandidate(killer, t, w);
    send(t, { t: 'streak', reset: 1 });
    t.streak = 0;
    t.scythe = false; // active stuff ends when you die; earned-but-unused streaks stay in your tray
    t.ballUntil = 0; t.f &= ~FLAGS.BALL; // (or everyone sees a steel ball at the spawn until the respawned client speaks)
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
    this.broadcast({ t: 'kill', k: killer && killer !== t ? killer.id : 0, v: t.id, w, via, vel: t.vel.map(r2), pos: t.pos.map(r2), yaw: r2(t.yaw || 0), fx: kfx, ep: ep || undefined });
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
    // the best EPIC kill in this clip (the label names it; its banner shows when it lands)
    if (t.lastEpic && !(k.bestEpic && n - k.bestEpic.at < 8000 && k.bestEpic.d >= t.lastEpic.d)) k.bestEpic = { d: t.lastEpic.d, at: n };
    const ep = k.bestEpic && k.bestEpic.at >= k.killLog[0] ? k.bestEpic : null;
    const score = multi * 10 + Math.min(12, spd / 40) + Math.min(6, dist / 15) + (w === 'void' ? 5 : 0) + (t.lastHs ? 3 : 0) + (k.isBot ? -8 : 0) + Math.random() + (ep ? 18 : 0); // an EPIC kill beats a double kill
    const r = this.round;
    if (r.hl && r.hl.score >= score) return;
    const label = ep && multi < 3 ? `EPIC SHOT · ${ep.d}M` : multi >= 5 ? 'RAMPAGE' : multi === 4 ? 'QUAD KILL' : multi === 3 ? 'TRIPLE KILL' : multi === 2 ? 'DOUBLE KILL'
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
  // is this kill EPIC? only what the server trusts: its positions, the hit, the killer's state (see shared/epic.js)
  epicOf(k, t, w, via) {
    if (via || !k || k === t || k.isBot || this.mode === 'training' || this.mode === 'coop') return null; // via: credited to whoever hit them last (void, cough, hazards): nobody aimed that. coop is all bot kills: it'd never stop bragging
    const n = now(), used = k.usedAt || {}, wd = WEAPONS[w];
    if (k.reverseUntil > n) return null; // bounced off their reverse card: nobody aimed that one
    if (used.spinbot > (k.deadT || 0) && n - used.spinbot < STREAKS.spinbot.dur * 1000 + 500) return null; // the aimbot did it
    if (w === 'chicken' && n - (used.chickenstrike || 0) < 6000) return null; // an airstrike
    if (w === 'bow' && (t.burnUntil > n || [...this.clouds.values()].some((c) => c.o === k.id && dist3(center(t), c.p) < 5.5))) return null; // burn / gas ticks
    // a projectile counts from where (and how) they let go of it: firing from 34 m and backing off is still a 34 m kill
    const pj = this.epicProj && this.epicProj.o === k.id && this.epicProj.ef && (this.epicProj.k === w || (this.epicProj.k === 'card' && w === 'cards')) ? this.epicProj : null;
    if (pj && k.deadT > pj.ef.at) return null; // they died while it was flying
    const s = pj ? pj.ef : this.epicState(k);
    let dist = dist3(s.pos, t.pos);
    // melee can't land further than its reach (+ the speed the server saw, not the one they claim): no WHAT A REACH from a faked velocity
    if (wd && wd.kind === 'melee') dist = Math.min(dist, Math.max(wd.range, wd.heavy ? wd.heavy.range : 0) + (k.kat || 0) * (wd.grow || 0) + 2 + this.speedOf(k) * 0.3);
    return epicCheck({
      dist, w, hs: !!t.lastHs && !!wd && wd.kind !== 'melee' && w !== 'snowball', ns: w === 'sniper' && !!k.nsHit, // a backstab isn't a headshot
      air: s.air, rope: s.rope, kmh: s.kmh, hp: s.hp,
      still: n - (t.movedT || n), // anti-farm: shooting someone who stood still for 5 s is no trophy
    });
  }
  // the killer's state that counts for EPIC: right now, or (stored on a projectile) when they fired it
  epicState(k) {
    // mid-air: nothing under any part of their 0.8 m footprint (feet on a ledge edge isn't flying)
    const hw = PH.halfW, feet = [[0, 0], [1, 1], [1, -1], [-1, 1], [-1, -1], [1, 0], [-1, 0], [0, 1], [0, -1]];
    const air = feet.every(([a, b]) => !raycast([k.pos[0] + a * hw, k.pos[1] + 0.05, k.pos[2] + b * hw], [0, -1, 0], EPIC.airH + 0.05, this.boxes));
    return {
      at: now(), pos: k.pos.slice(), air, rope: !!k.g && dist3(k.g, k.pos) < HOOK.range + 10, kmh: this.speedOf(k) * 3.6,
      hp: k.alive && !(k.selfHurtT > k.spawnT) ? k.hp : 0, // any self-damage this life: no low-HP bonus
    };
  }
  // from the snapshots: when everyone last really moved (EPIC.moved metres; a respawn or getting knocked around doesn't count)
  // and where they were over the last 0.6 s (how fast they're really going)
  trackMoves(n) {
    for (const p of this.players.values()) {
      if (!p.alive) { p.trail = null; continue; }
      if (p.trackSeq !== p.seq) { p.trackSeq = p.seq; p.trail = null; } // respawned or put back at a spawn (round start): that jump isn't moving
      if (!p.stillAt) p.movedT = n; // just joined
      if (!p.stillAt || !p.trail || dist3(p.stillAt, p.pos) > EPIC.moved) {
        if (p.stillAt && p.trail && n - (p.knockT || 0) > 1200) p.movedT = n;
        p.stillAt = p.pos.slice();
      }
      (p.trail ||= []).push([n, p.pos[0], p.pos[1], p.pos[2]]);
      while (p.trail[0][0] < n - 600) p.trail.shift();
    }
  }
  // the speed they say they're going, but no faster than the snapshots saw them move (+25% for network jitter)
  speedOf(p) {
    const tr = p.trail, v = Math.hypot(p.vel[0], p.vel[1], p.vel[2]);
    if (!p.alive || !tr || !tr.length) return 0;
    const [t0, x, y, z] = tr[0], dt = (now() - t0) / 1000;
    return dt < 0.25 ? 0 : Math.min(v, (Math.hypot(p.pos[0] - x, p.pos[1] - y, p.pos[2] - z) / dt) * 1.25);
  }
  // a slice of the recording: 10 Hz frames + the events in that window + who's who
  clip(t0, t1) {
    const frames = this.rec.frames.filter((f) => f.s >= t0 && f.s <= t1 && f.odd);
    const ev = this.rec.ev.filter((e) => e.s >= t0 && e.s <= t1);
    ev.unshift(...trapPreroll(this.rec.ev, t0)); // someone already floating in a soap bubble when the clip starts
    const info = {};
    for (const f of frames) for (const e of f.p) if (!info[e[0]]) {
      const pl = this.players.get(e[0]);
      if (pl) info[e[0]] = { name: pl.name, color: pl.color, skins: pl.skins, bot: pl.isBot, look: pl.look, level: pl.level, grap: pl.grap || 'rope' };
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

  // revolver: a tap is the accurate shot (1 per 0.4 s), holding fire fans the hammer (6/s, fan damage). the server keeps
  // its own cylinder per shooter (a revolver bullet hits one player, so a hit is a shot) with two schedules: nothing
  // counts faster than a fan, and full damage only for unmarked hits on the tap schedule (a fanned hit pushes the next
  // tap a whole tap away), so a hacked client firing fast gets fan damage. a hit may come up to 40% of a shot early
  // (lag), but the average rate holds. 6 hits, then the next needs a reload-length pause. returns the damage
  // multiplier, 0 = drop it
  revolverHit(p, t, m, w) {
    if (!this.rangeOk(p, t, w.range)) return 0;
    const n = now(), f = w.fanHammer, tapMs = 1000 / w.rate, fanMs = 1000 / f.rate;
    let c = p.revCyl;
    if (!c || c.t < p.spawnT) c = p.revCyl = { t: -1e9, n: 0, tap: 0, fan: 0 }; // respawned with a full cylinder
    if (n < c.fan - fanMs * 0.4) return 0;
    if (n - c.t >= w.reload * 750) c.n = 0; // long enough to have reloaded
    if (c.n >= w.mag && this.mode !== 'training') return 0; // training = infinite ammo
    const tap = !m.fan && n >= c.tap - tapMs * 0.4;
    c.fan = Math.max(c.fan, n) + fanMs;
    c.tap = tap ? Math.max(c.tap, n) + tapMs : Math.max(c.tap, n + tapMs);
    c.t = n; c.n++;
    return tap ? 1 : f.dmg / w.dmg;
  }

  applyHitscan(p, t, wid, n, h, d, mul = 1) {
    if (this.isBall(t)) h = 0; // a wrecking ball has no head
    if (this.parryShot(p, t, wid, n, h, d, mul)) return; // katana parry: blocked, or sent back
    const w = WEAPONS[wid], pellets = w.pellets || 1;
    const dmg = (w.dmg * (n - h) + w.dmg * (w.head || 1) * h) * mul;
    const k = w.kb * n;
    this.hurt(t, p, wid, dmg, [d[0] * k, d[1] * k + (w.kbUp || 0) * (n / pellets), d[2] * k], { hs: h > 0 });
  }

  // scales of justice: how guilty t is next to p, from what the server knows right now (formula in shared/verdict.js)
  verdictOf(p, t) {
    let teams = null;
    if (this.teamsOn() && p.team && t.team) { const sc = this.game === 'bomb' && this.bomb ? this.bomb.wins : this.score; teams = [sc[p.team] || 0, sc[t.team] || 0]; }
    return verdict(p, t, { board: this.fighters(), teams, revenge: !!p.lastKiller && p.lastKiller === t.id, npc: (this.mode === 'coop' && t.isBot) || !!(t.ai && t.ai.dummy) });
  }

  onHit(p, m) {
    const w = WEAPONS[m.w];
    const t = this.players.get(m.to);
    const d = norm(vec3(m.d));
    if (!w || !t || !d || t === p || !t.alive || !p.alive) return;
    if (this.isBall(p)) return; // no hands in the wrecking ball
    if (now() < (p.staggerUntil || 0)) return; // got parried: still reeling
    if ((w.slot === 'streak' || w.kind === 'dash') && !p.scythe) return; // you have to earn it
    if (w.kind === 'dash') {
      if (!(p.f & FLAGS.DASH) || !this.pairOk(p, t, 'dash', 280) || !this.rangeOk(p, t, w.range)) return;
      if (this.parryMelee(p, t)) return;
      this.hurt(t, p, 'scythe', w.dmg, [d[0] * w.kb, d[1] * w.kb + w.kbUp, d[2] * w.kb]);
      return;
    }
    const toT = norm([t.pos[0] - p.pos[0], t.pos[1] - p.pos[1], t.pos[2] - p.pos[2]]) || d;
    if (m.w === 'popper') { this.popperHit(p, t, toT); return; } // an item now: only right after a real pop
    if (w.kind === 'hitscan') {
      const pellets = w.pellets || 1;
      const n = clampInt(m.n, 1, Math.min(pellets, this.maxPellets(w, p, t))), h = clampInt(m.h, 0, n);
      if (w.fanHammer) { const mul = this.revolverHit(p, t, m, w); if (mul) this.applyHitscan(p, t, m.w, n, h, d, mul); return; } // tap or fan the hammer
      if (!this.pairOk(p, t, 'hs' + m.w, (1000 / fireRate(w, p.hp)) * 0.6) || !this.rangeOk(p, t, w.range)) return; // the Redline fires faster as you lose HP
      p.nsHit = m.w === 'sniper' && p.w === 'sniper' && (m.ns === 1 || m.ns === true); // a no-scope (ns: 1) can make the kill EPIC
      const hp0 = t.hp; // no-scope hype only goes out if the shot really landed
      this.applyHitscan(p, t, m.w, n, h, d);
      p.nsHit = false;
      if (m.ns === 1 && m.w === 'sniper') this.noScope(p, t, h > 0, hp0);
    } else if (w.kind === 'melee') {
      const hv = m.heavy && w.heavy ? w.heavy : null; // knife right click
      const reach = w.range + (m.w === 'katana' ? (p.kat || 0) * w.grow : 0);
      if (hv) { if (!this.pairOk(p, t, 'mh' + m.w, hv.cd * 750) || !this.rangeOk(p, t, hv.range)) return; }
      else if (!this.pairOk(p, t, 'm' + m.w, w.cd * 750) || !this.rangeOk(p, t, reach)) return;
      if (this.parryMelee(p, t)) return;
      const dir = w.radial ? toT : d;
      let dmg = hv ? hv.dmg : w.dmg, back = false;
      if (w.backstab) { // they're facing away from you -> backstab
        const fwd = [-Math.sin(t.yaw), -Math.cos(t.yaw)];
        const hl = Math.hypot(toT[0], toT[2]) || 1;
        if (fwd[0] * (toT[0] / hl) + fwd[1] * (toT[2] / hl) > 0.45) { dmg *= w.backstab; back = true; }
      }
      const kb = hv ? hv.kb : w.kb, kbUp = hv ? hv.kbUp : w.kbUp;
      const vd = w.verdict ? this.verdictOf(p, t) : null; // scales of justice: the court decides how hard it lands
      if (vd) dmg *= vd.mult;
      const hp0 = t.hp;
      this.hurt(t, p, m.w, dmg, [dir[0] * kb, dir[1] * kb + kbUp, dir[2] * kb], { slip: !!w.slip, hs: back });
      if (vd && t.hp < hp0) this.broadcast({ t: 'fx', k: 'verdict', id: t.id, by: p.id, m: vd.mult, g: vd.g, one: !t.alive && dmg >= 100 ? 1 : 0, p: center(t).map(r2) });
    } else if (m.w === 'cig') {
      if (!this.pairOk(p, t, 'cig', 75) || !this.rangeOk(p, t, w.range)) return;
      this.hurt(t, p, 'cig', w.dmg, [d[0] * 1.5, 0.6, d[2] * 1.5]);
    }
  }

  // no-scope hype. "ns" is the shooter's word, so it only buys cosmetics, never damage: the distance is measured here,
  // nothing goes out if the shot was blocked (spawn protection, bubble, reverse card, teammate, round over), and one per shot
  noScope(p, t, hs, hp0) {
    if (t.alive && t.hp >= hp0) return;
    const n = now();
    if (n - (p.nsT || 0) < 700) return; // a bolt action can't fire faster than this anyway
    p.nsT = n;
    const ev = { t: 'ns', k: p.id, v: t.id, d: Math.min(999, Math.round(dist3(p.pos, t.pos))), hs: hs ? 1 : 0, kill: t.alive ? 0 : 1, p: t.pos.map(r2) };
    // a long one (25 m+, like the client's NS_LONG) holds the victim's killcam back ~1.3 s for the MLG overlay: don't force their respawn mid-killcam
    if (ev.kill && ev.d >= 25 && !t.isBot && t.kc && this.mode !== 'training') {
      t.respawnAt = Math.max(t.respawnAt, n + 10500);
      // an EPIC no-scope: the overlay first, then the unskippable killcam (1.3 s later than usual), so its lock moves too
      if (t.epicLock) t.epicLock = Math.min(t.respawnAt, Math.max(t.epicLock, n + epicCamMs() + 1300));
    }
    this.broadcast(ev);
    this.rec.ev.push({ s: n, m: ev }); // so the play of the round gets the fireworks too
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
  }

  // ---------------------------------------------------------- katana parry
  // right click with the katana opens a short window. anything hitting you from the front in it bounces off:
  // bullets are blocked (in the perfect start of the window they go straight back into the shooter), projectiles get
  // batted back at whoever threw them, melee attackers get shoved off and staggered. explosions still hurt.
  startParry(p, m) {
    const n = now(), P = PARRY;
    if (!p.alive || p.w !== 'katana' || this.isBall(p, n)) return; // p.w comes from your snapshots. no hands in the wrecking ball
    if (n < (p.staggerUntil || 0)) return; // your own swing just got parried: no guard until you stop reeling
    if (n - (p.parryT || 0) < (P.win + P.cd) * 900) return; // cooldown, with a little slack for network jitter
    if (Number.isFinite(m.y)) p.yaw = m.y; // freshest look direction for the facing check
    p.parryT = n; p.parryN = 0;
    this.parryUntil = Math.max(this.parryUntil || 0, n + (P.win + P.slack) * 1000);
    this.broadcast({ t: 'guard', id: p.id });
  }
  // 0 = not parried, 1 = parried, 2 = perfect. inc = the way the hit comes from (parrier -> source)
  parryAt(t, inc) {
    const P = PARRY, age = now() - (t.parryT || 0);
    if (!t.alive || !t.parryT || t.w !== 'katana' || age > (P.win + P.slack) * 1000 || this.isBall(t) || t.trap) return 0; // (a ball has no hands; soap pops first)
    // the front = within arc/2 of where you look, side to side. from (nearly) straight above or below always counts.
    // inc is always built from positions the server tracks (shots, melee) or simulates (projectiles), never sent by a client
    const hl = Math.hypot(inc[0], inc[2]), l = Math.hypot(inc[0], inc[1], inc[2]);
    if (hl > l * 0.3 && (-Math.sin(t.yaw) * inc[0] - Math.cos(t.yaw) * inc[2]) / hl < Math.cos((P.arc / 2) * Math.PI / 180)) return 0;
    return age <= (P.perfect + P.slack) * 1000 ? 2 : 1; // the slack moves the perfect cut-off too: a late report is late there as well
  }
  // where the sparks fly: just in front of the chest, toward the hit
  parrySpot(t, inc) {
    const hl = Math.hypot(inc[0], inc[2]), fx = hl > 0.05 ? inc[0] / hl : -Math.sin(t.yaw), fz = hl > 0.05 ? inc[2] / hl : -Math.cos(t.yaw);
    return [t.pos[0] + fx * 0.55, t.pos[1] + 1.35, t.pos[2] + fz * 0.55];
  }
  parryFx(t, by, pf, k, at, extra) {
    t.parryN = (t.parryN || 0) + 1; // nth thing parried this window (clients only make a big deal of the first)
    this.broadcast({ t: 'parry', id: t.id, by: by ? by.id : 0, pf: pf ? 1 : 0, k, n: t.parryN, p: at.map(r2), ...extra });
  }
  // hitscan: players' hit reports and bots' shots (both come through applyHitscan)
  parryShot(p, t, wid, n, h, d, mul) {
    if (!t.parryT || p === t || this.friendly(p, t) || this.bubbleBlocks(p, t)) return false;
    // where the shot comes from: the shooter's eye, a position the server tracks. never the d in their hit message
    // (a crafted d decides front or back). d only when the two coincide, and for the knockback below
    const e = eyeOf(p), c = center(t), inc = norm([e[0] - c[0], e[1] - c[1], e[2] - c[2]]) || [-d[0], -d[1], -d[2]];
    const pr = this.parryAt(t, inc);
    if (!pr) return false;
    const w = WEAPONS[wid], back = pr === 2 && p.alive;
    this.parryFx(t, p, back, 'shot', this.parrySpot(t, inc), back ? { b: center(p).map(r2) } : {});
    if (back) { // perfect: the same bullets (pellets, headshots) go back into the shooter, credited to the parrier
      const dmg = (w.dmg * (n - h) + w.dmg * (w.head || 1) * h) * mul, k = (w.kb || 0) * n, up = (w.kbUp || 0) * (n / (w.pellets || 1));
      this.hurt(p, t, 'parry', dmg, k || up ? [-d[0] * k, -d[1] * k + up, -d[2] * k] : null, { hs: h > 0 });
    }
    return true;
  }
  // melee: no damage. the attacker gets shoved back and staggered (their hits don't count for a moment)
  parryMelee(p, t) {
    if (!t.parryT || this.friendly(p, t)) return false;
    const inc = [p.pos[0] - t.pos[0], p.pos[1] - t.pos[1], p.pos[2] - t.pos[2]], pr = this.parryAt(t, inc);
    if (!pr) return false;
    const P = PARRY, f = pr === 2 ? 1.4 : 1, hl = Math.hypot(inc[0], inc[2]);
    const dx = hl > 0.05 ? inc[0] / hl : -Math.sin(t.yaw), dz = hl > 0.05 ? inc[2] / hl : -Math.cos(t.yaw);
    p.staggerUntil = now() + P.stagger * f * 1000;
    if (p.isBot && p.ai) p.ai.nextShot = Math.max(p.ai.nextShot, p.staggerUntil);
    this.knock(p, [dx * P.shove * f, P.shoveUp, dz * P.shove * f], 'parry');
    this.tag(p, t, 'parry'); // shoved off a ledge by a parry = the parrier's kill
    this.parryFx(t, p, pr === 2, 'melee', this.parrySpot(t, inc), { st: r2(P.stagger * f) });
    return true;
  }
  // projectiles: batted back toward whoever threw them at the same speed. the parrier owns it now, so it hits the thrower.
  // runs right after the projectile moves, so it also catches things that normally fly through people (ducks, grenades)
  parryProj(pr, prev) {
    if (pr.back) this.parryHome(pr, prev);
    const n = now();
    if (n > (this.parryUntil || 0)) return false; // nobody has a window open
    const spd = Math.hypot(pr.v[0], pr.v[1], pr.v[2]);
    if (spd < 4) return false; // rolling / resting stuff isn't hitting anyone
    const owner = this.players.get(pr.o), lim = (PARRY.win + PARRY.slack) * 1000;
    const c = this.sweep(prev, pr.p, pr.r + 0.3, (t) => t.id === pr.o || !t.parryT || n - t.parryT > lim || (pr.hit.has(t.id) && n - pr.hit.get(t.id) < 700) || this.friendly(owner, t))[0];
    if (!c) return false;
    const t = c.t, seg = [prev[0] - pr.p[0], prev[1] - pr.p[1], prev[2] - pr.p[2]];
    const inc = Math.hypot(...seg) > 1e-4 ? seg : pr.v.map((x) => -x);
    const pf = this.parryAt(t, inc);
    if (!pf) return false;
    let dir = null, eta = 0;
    if (owner && owner.alive) {
      const g = WEAPONS[pr.k].grav || 0, oc = center(owner), to = [oc[0] - c.at[0], oc[1] - c.at[1], oc[2] - c.at[2]];
      eta = Math.hypot(...to) / spd;
      dir = norm([to[0], to[1] + 0.5 * g * eta * eta, to[2]]); // aim a bit high so gravity drops it onto them
    }
    dir ||= norm(inc) || [0, 1, 0];
    pr.p = c.at.slice();
    pr.v = dir.map((x) => x * spd);
    pr.o = t.id;
    pr.hit.clear(); pr.hit.set(t.id, n); // can't hit the parrier on its way out
    if (pr.k === 'slipper') { pr.phase = 0; pr.born = n - (WEAPONS.slipper.out - Math.max(0.3, eta + 0.15)) * 1000; } // out to the thrower, then home to the parrier
    if (pr.k === 'frag' || pr.k === 'smokegren' || pr.k === 'duck') pr.back = owner && owner.alive ? owner.id : 0;
    this.broadcast({ t: 'pu', id: pr.id, p: pr.p.map(r2), v: pr.v.map(r2) });
    this.parryFx(t, owner, pf === 2, 'proj', c.at, { pr: pr.id });
    return true;
  }
  // grenades and ducks fly through people, so a batted-back one would sail right past the thrower: it stops dead on
  // them instead and goes off at their feet
  parryHome(pr, prev) {
    const t = this.players.get(pr.back);
    if (!t || !t.alive) { pr.back = 0; return; }
    if (!this.sweep(prev, pr.p, pr.r + 0.3, (x) => x !== t).length) return;
    pr.back = 0;
    pr.v = [pr.v[0] * 0.08, Math.min(pr.v[1], 0), pr.v[2] * 0.08];
    this.broadcast({ t: 'pu', id: pr.id, p: pr.p.map(r2), v: pr.v.map(r2) });
  }

  onFire(p, m) {
    const w = WEAPONS[m.w];
    if (!w || !p.alive) return;
    if (w.slot === 'streak' && !p.scythe) return;
    // only loadout weapons fire. items (popper, reverse card, duck), grenades and thrown cards come from G / the deck
    if (!['primary', 'secondary', 'melee', 'streak'].includes(w.slot)) return;
    let o = vec3(m.o);
    if (!o || dist3(o, eyeOf(p)) > 4) o = eyeOf(p);
    if (w.kind === 'hitscan') { this.broadcast({ t: 'fx', k: 'shot', w: m.w, id: p.id, s: segs(m.s), fan: (w.fanHammer && m.fan ? 1 : undefined) }, p.id); return; } // fan: everyone sees the fanning spin
    if (w.kind === 'melee') { this.broadcast({ t: 'fx', k: 'swing', w: m.w, id: p.id, a: o.map(r2), h: m.heavy ? 1 : undefined }, p.id); return; }
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
    pr.ef = this.epicState(p); // EPIC: where (and how) they fired it from
    this.projectiles.set(pr.id, pr);
    this.broadcast({ t: 'ps', id: pr.id, k: pr.k, p: pr.p.map(r2), v: pr.v.map(r2), o: p.id });
  }

  makeProj(p, wid, pos, vel, extra = {}) {
    const w = WEAPONS[wid];
    const pr = { id: this.nextProj++, k: wid, o: p.id, r: w.r, bounce: w.bounce || 0, born: now() - 300, phase: 0, hit: new Map(), sync: 0, p: pos.slice(), v: vel.slice(), ...extra };
    pr.ef = this.epicState(p); // EPIC: where (and how) they fired it from
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
    if (t.trap) { this.hurt(t, owner, 'bow', 0, null); return; } // a soap bubble takes the arrow: no fire, sleep or knockback gets in
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
      for (const hb of t.trap ? trapBoxes(t.pos) : this.isBall(t) ? ballBoxes(t.pos) : playerBoxes(t.pos)) { // a soap bubble gets hit on the bubble; a wrecking ball is one big ball
        const e = { min: hb.min.map((x) => x - r), max: hb.max.map((x) => x + r) };
        const h = rayBox(prev, dir, e, len + 1e-3);
        if (h && h.t < best) best = h.t;
      }
      if (best < Infinity) out.push({ t, at: [prev[0] + dir[0] * best, prev[1] + dir[1] * best, prev[2] + dir[2] * best], d: best });
    }
    return out.sort((a, b) => a.d - b.d);
  }

  // homing slippers lock the nearest enemy in front of them that they can see: never the thrower, teammates,
  // players behind a bubble, or anyone this slipper already hit on the way out (it would orbit them)
  slipperTarget(pr, owner) {
    const w = WEAPONS.slipper, s = Math.hypot(...pr.v);
    if (s < 1) return null;
    if (this.round && this.round.over) return null; // no damage then anyway
    const cone = Math.cos(w.homeCone * (owner.isBot ? 0.5 : 1) * Math.PI / 180), n = now(); // bots: narrower, so their aim error still matters
    let best = null, bs = Infinity;
    for (const t of this.players.values()) {
      if (!t.alive || t === owner || pr.hit.has(t.id) || this.friendly(owner, t) || this.bubbleBlocks(owner, t)) continue;
      if (!t.isBot && n - t.spawnT < 1200) continue; // spawn protected: a hit would do nothing
      const c = center(t), to = [c[0] - pr.p[0], c[1] - pr.p[1], c[2] - pr.p[2]], d = Math.hypot(...to);
      const sc = t.id === pr.tg ? d * 0.8 : d; // keep the current lock unless another is clearly nearer (no flip-flopping)
      if (d >= w.homeR || sc >= bs || d < 1e-3 || (to[0] * pr.v[0] + to[1] * pr.v[1] + to[2] * pr.v[2]) / (d * s) < cone) continue;
      if (raycast(pr.p, to.map((x) => x / d), d, this.boxes)) continue; // behind a wall
      best = t; bs = sc;
    }
    return best;
  }

  removeProj(pr, extra) {
    this.projectiles.delete(pr.id);
    this.broadcast(Object.assign({ t: 'pd', id: pr.id, p: pr.p.map(r2) }, extra));
  }

  tickProjectiles(dt) {
    const n = now();
    for (const pr of this.projectiles.values()) {
      this.epicProj = pr; // a kill by this projectile counts from where it was fired (epicOf)
      const w = WEAPONS[pr.k];
      const age = (n - pr.born) / 1000;
      const owner = this.players.get(pr.o);
      const prev = pr.p.slice();
      let hit = null;
      if (pr.k === 'soap') { this.stepSoap(pr, n, owner, prev, dt); continue; }
      if (pr.k === 'slipper') {
        if (!owner || !owner.alive) { this.removeProj(pr); continue; }
        if (pr.phase === 0) { // homing: curve toward the nearest enemy ahead, and keep going out while locked on
          const tg = age < w.outLock ? this.slipperTarget(pr, owner) : null, id = tg ? tg.id : 0;
          if (id !== (pr.tg || 0)) pr.sync = Math.min(pr.sync, 0.03); // tell clients soon so their prediction follows the new curve (capped if the lock wobbles)
          pr.tg = id;
          if (tg) steerTo(pr.v, pr.p, center(tg), w.homeTurn * dt);
        }
        if (pr.phase === 0 && age >= (pr.tg ? w.outLock : w.out)) { pr.phase = 1; pr.hit.clear(); pr.tg = 0; pr.sync = 0; }
        if (pr.phase === 0) {
          if (stepProjectile(pr, dt, this.boxes, 0)) { pr.phase = 1; pr.hit.clear(); pr.tg = 0; pr.sync = 0; }
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
        if (pr.sync <= 0) { pr.sync = 0.1; this.broadcast({ t: 'pu', id: pr.id, p: pr.p.map(r2), v: pr.v.map(r2), tg: pr.tg || undefined, ph: pr.phase || undefined }); }
      } else {
        if (pr.k === 'duck' && this.duckFly(pr, owner, dt)) continue; // homing, and it stuck to someone
        hit = stepProjectile(pr, dt, this.boxes, w.grav);
      }
      if (this.parryProj(pr, prev)) continue; // batted back by a katana parry
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
        const victims = this.sweep(prev, pr.p, pr.r, (t) => (t.id === pr.o && age < ownerImmune) || (pr.hit.has(t.id) && n - pr.hit.get(t.id) < 700) || (this.friendly(owner, t) && !t.trap));
        if (victims.length) {
          if (pr.k === 'chicken') { pr.p = victims[0].at; this.projectiles.delete(pr.id); this.explode(pr); continue; }
          if (pr.k === 'snowball') {
            const v = victims[0];
            pr.p = v.at;
            this.removeProj(pr, { b: 1 });
            if (v.t.id === pr.o) continue;
            const d = norm(pr.v) || [0, 0, 1];
            if (v.t.trap) { this.hurt(v.t, owner, 'snowball', 0, null); continue; } // a soap bubble takes it (teammates' too): pop, no frost
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
    this.epicProj = null;
  }

  makeHole(p, owner, o = {}) {
    const w = WEAPONS.duck;
    const big = !!o.big;
    const h = {
      id: this.nextHole++, p: p.map(r2), o: owner, born: now(), tick: 0, big,
      time: big ? 6 : w.holeTime, R: big ? 34 : w.holeR, pull: big ? 80 : w.pull, blastR: big ? 18 : w.blastR, blastKb: big ? 45 : w.blastKb, blastDmg: big ? 70 : w.blastDmg,
    };
    if (o.on) { h.on = o.on; h.born += (o.delay || 0) * 1000; h.syncT = now() + 500; } // stuck on someone: opens on them a moment later
    this.holes.set(h.id, h);
    this.broadcast({ t: 'hs', id: h.id, p: h.p, o: owner, big, on: h.on || 0, age: r2((now() - h.born) / 1000) });
    return h;
  }

  tickHoles(dt) {
    const w = WEAPONS.duck, n = now();
    for (const h of this.holes.values()) {
      const age = (n - h.born) / 1000;
      const owner = this.players.get(h.o);
      this.holeSync(h, n);
      if (age < 0) continue; // stuck duck: the hole opens on them in a moment
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
        if (t.id === h.on) { this.damage(t, w.stuckDmg, owner, 'duck'); continue; } // the one it's stuck to IS the middle
        const c = center(t);
        const to = [h.p[0] - c[0], h.p[1] - c[1], h.p[2] - c[2]];
        const dist = Math.hypot(...to);
        if (dist > h.R || dist < 0.05) continue;
        const s = (h.pull * (1 - dist / h.R) + 8) * 0.1 * Math.min(1, dist / 1.5);
        // plus a little lift each pulse: off their feet, ground friction can't hold them back (a duck stuck on someone at floor height pulls sideways)
        this.knock(t, [to[0] / dist * s, to[1] / dist * s + w.lift * Math.min(1, dist / 1.5), to[2] / dist * s], 'duck');
        if (t.id !== h.o) this.tag(t, owner, 'duck');
        if (dist < 2 && t.id !== h.o) this.damage(t, 3, owner, 'duck');
      }
    }
  }

  // ---------------------------------------------------------- rubber duck: homes in, sticks, the hole rides its victim
  // in flight: latch onto an enemy it touched since last tick, else steer toward the nearest enemy ahead of it.
  // ducks nobody threw (thrower left, ducks from the sky) just fly. true = it stuck and is gone
  duckFly(pr, owner, dt) {
    if (!owner) return false;
    const w = WEAPONS.duck;
    const skip = (t) => t.id === pr.o || this.friendly(owner, t) || this.bubbleBlocks(owner, t);
    let stuck = pr.lp ? this.sweep(pr.lp, pr.p, pr.r + 0.1, skip)[0] : null;
    if (!stuck) for (const t of this.players.values()) { // sat still inside someone (sweep needs movement)
      if (!t.alive || skip(t)) continue;
      if (playerBoxes(t.pos).some((b) => b.min.every((m, i) => pr.p[i] > m - pr.r) && b.max.every((m, i) => pr.p[i] < m + pr.r))) { stuck = { t, at: pr.p.slice() }; break; }
    }
    if (stuck) {
      pr.p = stuck.at;
      this.removeProj(pr);
      this.makeHole(center(stuck.t), pr.o, { on: stuck.t.id, delay: w.stick });
      this.tag(stuck.t, owner, 'duck');
      return true;
    }
    pr.lp = pr.p.slice();
    // homing: nearest enemy within homeR, inside a 60 degree cone of where it's flying, in plain view
    const sp = Math.hypot(pr.v[0], pr.v[1], pr.v[2]);
    let tgt = null, bd = w.homeR;
    if (sp > 4) for (const t of this.players.values()) {
      if (!t.alive || skip(t)) continue;
      const c = center(t), to = [c[0] - pr.p[0], c[1] - pr.p[1], c[2] - pr.p[2]], d = Math.hypot(...to);
      if (d >= bd || d < 0.05 || (to[0] * pr.v[0] + to[1] * pr.v[1] + to[2] * pr.v[2]) / (d * sp) < w.homeCos) continue;
      if (raycast(pr.p, to.map((x) => x / d), d, this.boxes)) continue;
      tgt = t; bd = d;
    }
    if (tgt) { const c = center(tgt); steer(pr.v, [c[0] - pr.p[0], c[1] - pr.p[1], c[2] - pr.p[2]], w.turn * dt); }
    // clients steer it too (toward the same person); this keeps them honest
    const hid = tgt ? tgt.id : 0;
    pr.sync -= dt;
    if (hid !== (pr.hid || 0) || (hid && pr.sync <= 0)) {
      pr.hid = hid; pr.sync = 0.1;
      this.broadcast({ t: 'dh', id: pr.id, p: pr.p.map(r2), v: pr.v.map(r2), h: hid });
    }
    return false;
  }
  // a stuck duck's hole rides its victim until they die. everyone gets its size, who it's on and where it is
  // right away and twice a second after (late joiners catch up the same way)
  holeSync(h, n) {
    if (h.on) {
      const t = this.players.get(h.on);
      if (t && t.alive) h.p = center(t).map(r2);
      else { h.on = 0; h.syncT = 0; }
    }
    if (n < (h.syncT || 0)) return;
    h.syncT = n + 500;
    this.broadcast({ t: 'hu', id: h.id, p: h.p, R: h.R, on: h.on || 0, age: r2((n - h.born) / 1000) });
  }
  // bots inside a black hole lose their momentum like players do (not the thrower or their team) and ropes near the middle snap
  eatMomentum(b, dt) {
    if (!this.holes.size || (b.ai.dummy && b.ai.dummy.move)) return;
    const w = WEAPONS.duck, n = now();
    for (const h of this.holes.values()) {
      if (n < h.born || b.id === h.o || this.friendly(this.players.get(h.o), b)) continue;
      const d = holeDrag(b.pos, b.vel, h.p, h.R, w.drag * (b.id === h.on ? w.onDrag : 1), dt);
      if (d >= 0 && d < w.snapR * (h.big ? 1.6 : 1) && b.ai.hook) { b.ai.hook = null; b.g = null; }
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

  // ---------------------------------------------------------- sprays (Z): one graffiti per player, a new map wipes them
  onSpray(p, m, fresh) {
    const n = now(), at = vec3(m.p), nm = vec3(m.n);
    const id = typeof m.id === 'string' && Object.hasOwn(COSMETICS.spray, m.id) ? m.id : null;
    if (!p.alive || !at || !nm || !id || n - (p.sprayT || 0) < SPRAY.cd * 1000 - 500) return; // half a second of slack for jitter
    if (this.isBall(p, n)) return; // no hands in the wrecking ball
    // flat on a wall, floor or ceiling: one axis, +-1
    const k = nm.findIndex((x) => x !== 0);
    if (k < 0 || Math.abs(nm[k]) !== 1 || nm.some((x, i) => i !== k && x !== 0)) return;
    // near you (your position here can be one update old, so a bit more room when you're fast) and facing you, so no painting through walls
    const e = eyeOf(p);
    if (dist3(at, e) > SPRAY.reach + 1 + Math.min(6, Math.hypot(...p.vel) * 0.05)) return;
    if ((e[0] - at[0]) * nm[0] + (e[1] - at[1]) * nm[1] + (e[2] - at[2]) * nm[2] < -0.25) return;
    // and on a real face of this map
    const h = raycast([at[0] + nm[0] * 0.05, at[1] + nm[1] * 0.05, at[2] + nm[2] * 0.05], [-nm[0], -nm[1], -nm[2]], 0.15, this.boxes);
    if (!h || h.normal[k] !== nm[k]) return;
    if (!owns(p.inv, 'spray', id)) { // rolled it since you joined? read your inventory again (once) and retry
      if (fresh || !p.acct || n - (p.invT || 0) < 3000) return;
      p.invT = n;
      store.get(p.acct.n).then((u) => { if (u) p.inv = u.inv || {}; if (this.players.get(p.id) === p) this.onSpray(p, m, true); }).catch(() => {});
      return;
    }
    p.sprayT = n;
    if (this.sprayMap !== this.cfg.map) { this.sprays.clear(); this.sprayMap = this.cfg.map; } // painted on the old map: gone
    const pt = h.point.map(r2);
    pt[k] = nm[k] > 0 ? h.box.max[k] : h.box.min[k]; // exactly on the face
    const yaw = Number.isFinite(m.y) ? m.y : p.yaw || 0, TAU = Math.PI * 2;
    const s = { id: p.id, s: id, p: pt, n: nm, r: k === 1 ? r2(((yaw % TAU) + TAU) % TAU) : 0 }; // floors + ceilings face the way you look
    this.sprays.delete(p.id); // your new one replaces the old one (and goes to the back of the line)
    this.sprays.set(p.id, s);
    while (this.sprays.size > SPRAY.max) this.sprays.delete(this.sprays.keys().next().value);
    this.broadcast({ t: 'spray', ...s });
  }
  // what a late joiner gets in the welcome (clients wipe their own when the map changes)
  sprayList() { return this.sprayMap === this.cfg.map ? [...this.sprays.values()] : []; }

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
      p.parryT = 0; p.staggerUntil = 0; // katana parry: the client resets on 'spawn', so the server does too
      p.pos = this.pickSpawn(p.isBot, p);
      send(p, { t: 'spawn', p: p.pos, q: p.seq });
      this.sendLoadout(p);
    }
    if (this.mode === 'training') { this.removeBots(); this.spawnDummies(); }
  }

  handle(p, m) {
    if (p.trap && ['fire', 'hit', 'push', 'item', 'deploy', 'tbag', 'use', 'parry', 'spray'].includes(m.t)) return; // sealed in a soap bubble: no attacks, parries, items, streaks, sprays or planting till it pops
    switch (m.t) {
      case 's': {
        if (!p.alive || m.q !== p.seq) return;
        const pos = vec3(m.p), vel = vec3(m.v);
        if (!pos || !vel) return;
        p.pos = pos; p.vel = vel;
        if (p.acct) { const kmh = Math.min(20000, Math.hypot(vel[0], vel[2]) * 3.6); if (kmh > (p.acct.d.top_speed || 0)) { p.acct.d.top_speed = kmh; if (kmh > 450) checkAch(p); } }
        if (Number.isFinite(m.y)) p.yaw = m.y;
        if (Number.isFinite(m.x)) p.pitch = m.x;
        this.airCheck(p);
        if (WEAPONS[m.w]) p.w = m.w;
        p.g = vec3(m.g);
        p.f = m.f | 0;
        if (p.trap) this.holdTrapped(p, true); // sealed in a soap bubble: you go where it floats
        if (p.pos[1] < this.map.killY) this.kill(p, null, 'void');
        if ((p.f & FLAGS.BALL) && !(p.ballUntil > now())) p.f &= ~FLAGS.BALL; // only someone who earned the wrecking ball gets to be one
        if (p.ballUntil > now()) this.ballAir(p);
        break;
      }
      case 'hit': this.onHit(p, m); break;
      case 'push': this.onPush(p, m); break;
      case 'slam': this.onSlam(p, m); break;
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
        (p.usedAt ||= {})[m.r] = now(); // EPIC kills skip the spinbot's (aimbot) and the chicken strike's
        if (m.r === 'scythe') p.scythe = true;
        if (m.r === 'wreckingball') { p.ballUntil = now() + STREAKS.wreckingball.dur * 1000 + 1000; p.slamT = 0; p.ballTop = p.pos[1]; p.ballVy = 0; } // +1s for lag
        send(p, { t: 'streak', reward: m.r, dur: STREAKS[m.r].dur });
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
      case 'grap': // grapple skin: free ones or ones you own. quick clicks batch into one inventory read, the last pick wins
        p.grapWant = typeof m.id === 'string' ? m.id : '';
        if (!p.grapQ) p.grapQ = setTimeout(async () => {
          try { // nothing here may reject: an unhandled rejection takes the whole server down
            if (p.acct) { const u = await store.get(p.acct.n).catch(() => null); if (u) p.inv = u.inv || {}; }
            const g = ownedGrapple(p.grapWant, p.inv);
            if (g !== p.grap && this.players.get(p.id) === p) { p.grap = g; this.broadcast({ t: 'gr', id: p.id, g }, p.id); }
          } catch (e) { console.error('grap failed', e.message); } finally { p.grapQ = null; }
        }, 250);
        break;
      case 'kc': p.kc = !!m.on; break;
      case 'use': this.tryUse(p); break;
      case 'parry': this.startParry(p, m); break;
      case 'item': this.useItem(p, m); break;
      case 'spray': this.onSpray(p, m); break;
      case 'lo': this.setItem(p, m.item); break;
      case 'vote':
        if (this.vote && Number.isInteger(m.i) && m.i >= 0 && m.i < this.vote.options.length) {
          this.vote.votes.set(p.id, m.i);
          this.broadcast({ t: 'votes', counts: this.voteInfo().counts });
        }
        break;
      case 'respawn': // killcam finished or skipped
        if (!p.alive) p.respawnAt = Math.min(p.respawnAt, Math.max(now(), (p.deadT || 0) + 1500));
        if (!p.alive && p.epicLock) p.respawnAt = Math.max(p.respawnAt, Math.min(p.epicLock, (p.deadT || 0) + 10500)); // EPIC killcam: no skipping it (9 s cap, 10.5 s after a long no-scope's overlay)
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
      case 'land': this.airFail(p, false); break; // your client saw you touch the ground: run's over
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
    this.airEnd();
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
    for (const p of this.players.values()) p.lastKiller = 0; // new match: the court forgets old grudges
    this.round = { target: (TARGETS[this.mode] || TARGETS.ffa)[this.game] || ROUND[this.mode].kills, ends: now() + ROUND[this.mode].time * 1000, over: false, next: 0 };
    this.round.t0 = now();
    this.score = { 1: 0, 2: 0 };
    this.clearTags();
    this.assignTeams();
    this.bomb = this.game === 'bomb' && this.teamsOn() ? { att: 1, n: 0, wins: { 1: 0, 2: 0 } } : null;
    if (this.bomb) { this.round.ends = now() + 3600 * 1000; this.newBombRound(true); }
    else this.resetWorld();
    this.airStart(); // after the respawns: a client must get its 'spawn' (fresh grace) before the run starts
    this.broadcast({ t: 'round', start: 1, ...this.roundInfo() });
  }
  // ---------------------------------------------------------- Never Landed: a whole match without touching the ground
  // the client knows exactly when it lands and reports it ('land'); the server also watches snapshots so a client
  // that never reports can't just stand around. the match end decides.
  airStart() {
    this.airBad = new Set(); // names that touched down this match: leaving and rejoining doesn't wipe it
    for (const p of this.players.values()) {
      if (p.isBot) continue;
      p.air = { ok: true, rest: 0 };
      send(p, { t: 'air', on: 1, grace: AIR.grace });
    }
  }
  airCheck(p) {
    const a = p.air;
    if (!a || !a.ok) return;
    if (now() - p.spawnT < AIR.grace + AIR.slack) { a.rest = 0; return; }
    // feet within 3 cm of a box top for two snapshots in a row: a bhop touch is 0.3 m up by the next one
    if (onBoxTop(p.pos, this.boxes) && !(p.vel[1] > 0.5)) { if (++a.rest >= 2) this.airFail(p, true); } else a.rest = 0;
  }
  airFail(p, seen) {
    if (!p.air || !p.air.ok) return;
    p.air.ok = false;
    (this.airBad ||= new Set()).add(p.name);
    if (seen) send(p, { t: 'air', fail: 1 });
  }
  airEnd() {
    for (const p of this.players.values()) {
      if (p.isBot || !p.air) continue;
      const ok = p.air.ok;
      p.air = null;
      send(p, { t: 'air', end: 1, ok: ok ? 1 : 0, acct: p.acct ? 1 : 0 });
      if (ok) { console.log(`never landed: ${p.name}`); stat(p, 'airborne', 1); }
    }
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
    this.tickTraps(n);
    for (const b of this.players.values()) if (b.isBot && b.alive) this.stepBot(b, dt);
    this.tickProjectiles(dt);
    this.tickHoles(dt);
    this.tickStatus(dt);
    this.tickPeels();
    this.tickBalls();
    this.tickWaves();
    if (this.sprays.size && this.sprayMap !== this.cfg.map) this.sprays.clear(); // the map changed: its graffiti goes with it
    for (const p of this.players.values()) {
      if (!p.alive && n >= p.respawnAt) {
        if (p.isBot && this.mode === 'coop') continue;
        p.alive = true; p.hp = 100; p.vel = [0, 0, 0]; p.spawnT = n; p.seq++;
        p.pos = p.isBot && p.ai.dummy ? p.ai.dummy.home.slice() : this.pickSpawn(p.isBot, p);
        p.slipUntil = 0; p.burnUntil = 0; p.sleepUntil = 0; p.frozenUntil = 0; p.frost = 0; p.ic = {}; p.healLeft = 0;
        p.parryT = 0; p.staggerUntil = 0; // katana parry: a new life starts with the guard ready (the client resets too)
        if (p.ownItem) p.item = p.ownItem; // a switch made mid-life lands now (sendLoadout swaps in the randomizer's)
        send(p, { t: 'spawn', p: p.pos, q: p.seq });
        this.sendLoadout(p);
        if (!p.isBot) deal(p);
      }
    }
  }

  // ---------------------------------------------------------- wrecking ball (killstreak)
  // a ball only counts if this player really activated the streak and their snapshots say they're rolling
  isBall(p, n = now()) { return p.alive && p.ballUntil > n && !!(p.f & FLAGS.BALL); }
  // the highest the ball has been since it last touched a floor, from its snapshots + the server's own map (slam height)
  ballAir(p) {
    const y = p.pos[1], vy0 = p.ballVy || 0, n = now();
    p.ballVy = p.vel[1];
    p.ballSnapT = n;
    if (p.vel[1] < -(WRECK.slamV - 12)) p.diveT = n; // slam dive (onSlam wants to have seen one)
    (p.ballHist ||= []).push([n, p.pos.slice()]); // where it really was lately, so a claimed speed has to match the moves
    while (p.ballHist.length > 2 && n - p.ballHist[0][0] > 160) p.ballHist.shift();
    if (p.ballTop == null || (p.vel[1] > -3 && floorUnder(this.boxes, p.pos, 0.3) != null)) { p.ballTop = y; return; } // (diving at it isn't touching it)
    if (vy0 < -3 && p.vel[1] > 0 && floorUnder(this.boxes, p.pos, 3) != null) { p.ballTop = y; return; } // bounced off the floor between snapshots
    p.ballTop = Math.max(p.ballTop, y);
  }
  // rams: judged here from server-side positions + velocities, never from a client saying it hit someone.
  // the ball's path since the last tick is a segment, so a fast ball can't skip through someone between snapshots.
  tickBalls() {
    const n = now(), R = WRECK.r;
    for (const p of this.players.values()) {
      if (!this.isBall(p, n)) { p.ballPrev = null; p.ballHist = null; continue; }
      const c = [p.pos[0], p.pos[1] + R, p.pos[2]];
      let a = p.ballPrev || c;
      p.ballPrev = c;
      if (dist3(a, c) > 6) a = c; // a jump that big is a teleport, not a roll: don't sweep everyone in between
      // how fast it really moved over its last few snapshots: a claimed speed only counts if the position keeps up with it
      // (timed by when they arrived, but at least 1/30 s per snapshot: after a network stall they arrive all at once)
      const hh = p.ballHist || [], h0 = hh[0], h1 = hh[hh.length - 1];
      const span = hh.length > 1 ? Math.max(h1[0] - h0[0], (hh.length - 1) * 33) : 0;
      const mv = span && n - h1[0] < 200 ? dist3(h0[1], h1[1]) / (span / 1000) : 0;
      // rolling, swinging and falling onto people count. rising doesn't (the bounce after a slam), and neither does the
      // slam dive itself: the slam does its own damage, sized by the height
      const down = p.vel[1] < -(WRECK.slamV - 8) ? 0 : Math.max(0, -p.vel[1]);
      const vl = Math.hypot(p.vel[0], down, p.vel[2]);
      const sp = Math.min(vl, mv * 1.4 + 3);
      if (sp < WRECK.ramMin) continue;
      const dir = [p.vel[0] / vl, -down / vl, p.vel[2] / vl];
      for (const t of this.players.values()) {
        if (t === p || !t.alive || this.friendly(p, t)) continue;
        const tc = center(t);
        const reach = R + 0.5 + WRECK.ramReach + Math.hypot(t.vel[0], t.vel[2]) * 0.04; // ball + body + a bit for lag
        if (segPointDist(a, c, tc) > reach) continue;
        if ((tc[0] - a[0]) * dir[0] + (tc[1] - a[1]) * dir[1] + (tc[2] - a[2]) * dir[2] < -0.3) continue; // it's rolling away from them
        const to = [tc[0] - c[0], tc[1] - c[1], tc[2] - c[2]], td = Math.hypot(...to);
        if (td > 0.3 && raycast(c, to.map((x) => x / td), td - 0.3, this.boxes)) continue; // there's a wall in between
        if (!this.pairOk(p, t, 'ram', WRECK.ramCd)) continue;
        const dmg = ramDmg(sp);
        const k = Math.min(WRECK.ramKbMax, WRECK.ramKb + sp * WRECK.ramKbMul);
        const hl = Math.hypot(dir[0], dir[2]) || 1;
        // launched the way the ball was going, and up off the floor
        this.hurt(t, p, 'wreck', dmg, [dir[0] / hl * k, WRECK.ramUp + sp * 0.2, dir[2] / hl * k]);
        this.broadcast({ t: 'fx', k: 'ram', id: p.id, to: t.id, p: tc.map(r2), s: Math.round(sp) });
        this.knock(p, [-dir[0] * sp * 0.18, 1.5, -dir[2] * sp * 0.18], 'wreck'); // the ball keeps most of its momentum
      }
    }
  }
  // ground slam: the client lands a slam and says where. ball active, cooldown, the spot near where we think it is and on
  // a floor. how big it is comes from the server's own record of how high the ball got since it last touched the floor.
  onSlam(p, m) {
    const n = now();
    if (!this.isBall(p, n) || n - (p.slamT || 0) < WRECK.slamCd * 1000 - 250) return;
    let at = vec3(m.p);
    if (!at || Math.hypot(at[0] - p.pos[0], at[2] - p.pos[2]) > 4 + Math.hypot(p.vel[0], p.vel[2]) * 0.1 || at[1] > p.pos[1] + 1.5 || at[1] < p.pos[1] - 8) at = p.pos.slice();
    let fl = floorUnder(this.boxes, [at[0], at[1] + 1, at[2]], 9);
    if (fl == null) { at = p.pos.slice(); fl = floorUnder(this.boxes, [at[0], at[1] + 1, at[2]], 9); } // no floor where it says: try where we think it is
    if (fl == null) return; // nothing under it to slam into
    at[1] = fl;
    // its last snapshot has to be near that floor, or diving at it: a ball hanging on its chain or hovering up there can't
    // slam the floor below. (a slam that starts and lands between two snapshots can only have dived as far as a slam
    // goes in that time: at 30 a second that's about 2 m)
    const above = p.pos[1] - fl, since = Math.min(0.1, (n - (p.ballSnapT || 0)) / 1000);
    if (above > 8 || (above > 2.5 + since * WRECK.slamV && !(n - (p.diveT || 0) < 400))) return;
    const h = Math.min(30, (p.ballTop ?? p.pos[1]) - fl);
    if (!(h >= 0.25)) return; // it never left the floor
    p.slamT = n; p.ballTop = fl;
    const S = slamSize(h), c = [at[0], fl + WRECK.r, at[2]];
    this.broadcast({ t: 'fx', k: 'slam', id: p.id, p: at.map(r2), r: r2(S.r), h: r2(h) }, p.id);
    for (const t of this.players.values()) {
      if (t === p || !t.alive || this.friendly(p, t)) continue;
      const tc = center(t), to = [tc[0] - c[0], tc[1] - c[1], tc[2] - c[2]], d = Math.hypot(...to);
      const f = 1 - Math.max(0, d - WRECK.r) / S.r; // full at the ball's edge, nothing past the radius
      if (f <= 0) continue;
      if (d > 0.3 && raycast(c, to.map((x) => x / d), d - 0.3, this.boxes)) continue; // it's a shockwave: not through walls or the floor
      const hl = Math.hypot(to[0], to[2]), out = hl > 0.2 ? [to[0] / hl, to[2] / hl] : [0, 0];
      const k = S.kb * (0.35 + 0.65 * f);
      this.hurt(t, p, 'wreck', S.dmg * (0.2 + 0.8 * f), [out[0] * k, S.up * (0.5 + 0.5 * f) + 3, out[1] * k]); // up and out
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
    this.trackMoves(n);
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

REC_FX.add('slam').add('ram'); // wrecking ball hits show up in killcams + highlights
// what a wrecking ball is hit-tested as (the same box the clients shoot at)
function ballBoxes(pos) {
  const r = WRECK.r, [x, y, z] = pos;
  return [{ min: [x - r, y, z - r], max: [x + r, y + 2 * r, z + r], head: false }];
}
// the top of the floor right under these feet (no more than drop below them), or null (wrecking ball slams)
const qFloor = [];
function floorUnder(boxes, p, drop, hw = 0.6) {
  let best = null;
  for (const b of query(boxes, p[0] - hw, p[2] - hw, p[0] + hw, p[2] + hw, qFloor)) {
    const top = b.max[1];
    if (top > p[1] + 0.05 || top < p[1] - drop || (best != null && top <= best)) continue;
    if (b.min[0] < p[0] + hw && b.max[0] > p[0] - hw && b.min[2] < p[2] + hw && b.max[2] > p[2] - hw) best = top;
  }
  return best;
}
// shortest distance from point c to the segment a-b (wrecking ball rams)
function segPointDist(a, b, c) {
  const ab = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], l2 = ab[0] * ab[0] + ab[1] * ab[1] + ab[2] * ab[2];
  const t = l2 > 1e-9 ? Math.max(0, Math.min(1, ((c[0] - a[0]) * ab[0] + (c[1] - a[1]) * ab[1] + (c[2] - a[2]) * ab[2]) / l2)) : 0;
  return Math.hypot(a[0] + ab[0] * t - c[0], a[1] + ab[1] * t - c[1], a[2] + ab[2] * t - c[2]);
}

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
  ws.on('error', () => {}); // oversized or broken frames: ws closes the socket itself, an unhandled 'error' would kill the whole server
  ws.on('pong', () => { ws.isAlive = true; });
  ws.on('message', (data) => {
    let m;
    try { m = JSON.parse(data); } catch { return; }
    if (!m || typeof m !== 'object') return;
    if (!me) {
      if (m.t !== 'join' || ws.joining) return;
      ws.joining = true;
      for (const k of ['_name', '_acct', '_level', '_inv', '_achs']) delete m[k]; // only the server fills these in (from the token), never the client
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
