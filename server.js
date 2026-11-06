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
import { ROYAL, ROYAL_FEATS, featOn } from './shared/looks.js'; // Sniper Royalty
import { achInv, wrapMode, WRAP_MODES } from './shared/cosmetics.js'; // achievement-locked skins (the Golden Sniper), wrap modes
import { STAT_KEYS } from './server/store.js';
import { installRig } from './server/rig.js';
import { rigClash } from './shared/rig.js'; // overdrive rig killstreak
import { soapAt, trapBoxes, trapPreroll } from './shared/wand.js';
import { MAPS, MAP_ORDER } from './shared/map.js';
import { GAMES, GAME_ORDER, TEAMS, TARGETS, BOMB, TAG_LIFE, VOTE_MS, siteAt, mapsFor, mapForGame, canDefuse, LADDER, GUNGAME, INFECT } from './shared/modes.js';
import { VOTE, voteTotal, modeCards, mapCards, tally, winner as voteWinner, eventGame, inQuickPlay } from './shared/vote.js';
import { matchReset, matchKill, matchSummary } from './server/match.js';
import { SKIP, isSkipCmd, skipCommand, skipTick, skipPeople, skipInfo } from './server/skip.js';
import { WEAPONS, SLOTS, HOOK, HIPFIRE, BOT_DIFF, MODES, STREAKS, FLAGS, ARROW_TIPS, ITEMS, SLEEP_TIME, validStreaks, fireRate } from './shared/weapons.js';
import { stepProjectile, rayBox, raycast, playerBoxes, movePlayer, PH } from './shared/physics.js';
import { verdict } from './shared/verdict.js';

import { WRECK, slamSize, ramDmg } from './shared/weapons.js'; // wrecking ball
import { query } from './shared/physics.js';
import { epicCheck, epicCamMs, EPIC } from './shared/epic.js';
import { holeDrag, steer } from './shared/physics.js';
import { steer as steerTo } from './shared/homing.js'; // homing slippers (steerTo(v, from, to, max)); the duck's steer(v, dir, max) is physics.js's
import { PARRY } from './shared/weapons.js';
import { ROPE, classicRopeStep, classicRopeJump } from './shared/hookphys.js';
import { query as boxQuery } from './shared/physics.js';
import { navSteer } from './shared/nav.js';
import { DUCKRAIN } from './shared/modes.js';
import { surfaces, lavaOk, onLava, lavaBelow, nearestSafe, LAVA } from './shared/lava.js';
import { OOB, outOfBounds, boundsCenter } from './shared/bounds.js';
import { Traffic } from './server/traffic.js'; // cars on the roads (server/traffic.js)
import { SECRETS, SECRET, canReach, secretsOff, loreOf, catsOf } from './shared/secrets.js'; // hidden NPCs + cats
import { installRoyale } from './server/royale.js'; // Jank Royale (battle royale)
import { BR } from './shared/royale.js';
import { tickHR, hrBot } from './server/hrguy.js'; // the Tall Guy From HR (Scary Forest)
import { HR } from './shared/hr.js';
import { installGear } from './server/gear.js'; // laser pointer, instant camera, pop quiz, night vision goggles
import { installSec } from './server/secondaries.js'; // water pistol, taser, tv remote, speed trap
import { SPEED } from './shared/weapons.js';
import { installRifles, RIFLE_PREF, RIFLE_BOTS } from './server/rifles.js'; // burst rifle, lmg, marksman, lever-action, auto shotgun
import { installEcon } from './server/econ.js';
import { installPrimaries } from './server/primaries.js'; // nail gun pins, tennis ball bounces, shopping carts
import { installTactical } from './server/tactical.js';
import { TAC } from './shared/tactical.js'; // Plant & Defuse gunplay: spray patterns, moving spread, the hit check
import { MSLIP, onPatch, patchPreroll } from './shared/marbles.js';
import { installLasso } from './server/lasso.js'; // lasso (secondary): its Room methods
import { lassoPreroll } from './shared/lasso.js';
import { ZM } from './shared/zombies.js';
import { installZombies } from './server/zombies.js';
import { inShredder } from './shared/shredpit.js'; // the Warehouse's shredder pit: its teeth kill like the void
import { installLobby } from './server/lobby.js'; // mode lobbies: the countdown before a match
import { LOBBY } from './shared/lobby.js';

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
  '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.wav': 'audio/wav', '.mp3': 'audio/mpeg', '.ogg': 'audio/ogg',
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
  if (url === '/now') { // main menu "now playing" strip: the online room's mode + map, who's around
    const r = rooms.get('ffa');
    res.writeHead(200, { 'content-type': 'application/json', 'cache-control': 'no-cache' });
    res.end(JSON.stringify({ online: humans(), room: r ? r.humans().length : 0, game: r ? r.game : process.env.JF_GAME || 'dm', map: r ? r.cfg.map : 'islands', region: process.env.JF_REGION || process.env.RENDER_REGION || '', ev: eventGame() }));
    return;
  }
  if (url === '/lobbies') { // home menu mode cards: how many real people are in each mode, Online and With Bots
    res.writeHead(200, { 'content-type': 'application/json', 'cache-control': 'no-cache' });
    res.end(JSON.stringify(lobbyCounts()));
    return;
  }
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
const BOT_GUNS = ['ar', 'ar', 'smg', 'shotgun', 'shotgun', 'sniper', 'chicken', 'banana', 'minigun', 'revolver', 'redline', 'marbles', 'laser', 'nailgun', 'tennis', 'cart'];
BOT_GUNS.push('shredder'); // bots suck too (botShred)
BOT_GUNS.push('water', 'taser', 'remote'); // the new secondaries (server/secondaries.js secBotFire)
BOT_GUNS.push(...RIFLE_BOTS); // the rifle pack (server/rifles.js)
BOT_GUNS.push('pistol', 'akimbo', 'sawnoff'); // the plain sidearms
if (process.env.JF_PIN_DUR) WEAPONS.nailgun.nails.dur = Number(process.env.JF_PIN_DUR) || WEAPONS.nailgun.nails.dur; // test knob: longer nail gun pins (screenshots)
if (process.env.JF_BOT_GUNS) BOT_GUNS.splice(0, BOT_GUNS.length, ...process.env.JF_BOT_GUNS.split(',').filter((w) => Object.hasOwn(WEAPONS, w))); // test knob: JF_BOT_GUNS=nailgun,cart
const SKIN_F = ['default', 'default', 'gold', 'chrome', 'pink', 'camo', 'neon', 'rainbow', 'galaxy', 'lava', 'missing', 'tiger', 'fade', 'carbon', 'tape', 'cherry', 'sky', 'hazard', 'china', 'seigaiha', 'sakura', 'denim', 'pizza', 'tokyo', 'holo', 'corp', 'meat'];
const SKIN_H = ['none', 'none', 'none', 'tophat', 'party', 'crown', 'cowboy', 'propeller', 'cone', 'eyes', 'duck'];
const SKIN_E = ['none', 'none', 'none', 'sparkles', 'flames', 'money', 'smoke'];
const SKIN_KEYS = { f: /^[a-z_]{1,24}$/ };

const now = () => Date.now();
const r2 = (x) => Math.round(x * 100) / 100;
const dist3 = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
// client numbers: Number() / | 0 on an object call its own toString / valueOf, and {"toString":1} throws
const num = (x) => typeof x === 'number' ? x : typeof x === 'string' ? Number(x) : 0;
const clampInt = (x, lo, hi) => Math.max(lo, Math.min(hi, Math.floor(num(x) || 0)));
const pick = (a) => a[(Math.random() * a.length) | 0];
// client data as a table key: only real string keys (no '__proto__', no arrays that stringify forever)
const has = (T, k) => typeof k === 'string' && Object.hasOwn(T, k);
// one bad message or tick must not take every room down: log it (at most once per 5 s per kind) and carry on
const errT = new Map();
function logErr(kind, e) {
  const n = Date.now();
  if (n - (errT.get(kind) || 0) < 5000) return;
  errT.set(kind, n);
  console.error(`[${kind}]`, e && e.stack || e);
}
const safe = (kind, fn) => (...a) => { try { return fn(...a); } catch (e) { logErr(kind, e); } };
// the protocol nests 3 deep at most (fire.s, join.skins); anything much deeper is junk
function tooDeep(v, max = 6) {
  const st = [v, 0];
  let objs = 0;
  while (st.length) {
    const d = st.pop(), x = st.pop();
    if (!x || typeof x !== 'object') continue;
    if (d >= max || ++objs > 4000) return true;
    for (const k in x) if (x[k] && typeof x[k] === 'object') st.push(x[k], d + 1);
  }
  return false;
}
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
    // [wrap, hat, effect, model?, wrap mode?]: older clients send 3 or 4, the mode is checked against WRAP_MODES
    if (Array.isArray(v) && v.length >= 3 && v.length <= 5 && v.every((x) => typeof x === 'string' && SKIN_KEYS.f.test(x))) out[id] = [v[0], v[1], v[2], v[3] || 'default', wrapMode(v[4])];
  }
  return out;
}
function enforceSkins(skins, inv, achs) {
  const out = {}, own = achInv(inv, achs); // achievement skins (Golden Sniper) only count from your achievements
  for (const [id, sk] of Object.entries(skins)) out[id] = ownedSkin(sk, own, id);
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
if (process.env.JF_MSLIP_LIFE) MSLIP.life = Number(process.env.JF_MSLIP_LIFE) || MSLIP.life; // test knob: marble patches that outlast slow test browsers
if (process.env.JF_TARGET) for (const t of Object.values(TARGETS)) for (const k of Object.keys(t)) t[k] = Number(process.env.JF_TARGET);
// test knobs for the overdrive rig: earn it after this many kills, make it last this many seconds
if (process.env.JF_RIG) STREAKS.overdrive.kills = Number(process.env.JF_RIG) || STREAKS.overdrive.kills;
if (process.env.JF_RIG_DUR) STREAKS.overdrive.dur = Number(process.env.JF_RIG_DUR) || STREAKS.overdrive.dur;
// test knobs for gun game (everyone starts on a later rung) and infection (round length, patient zero delay, in seconds)
const GG_START = Math.max(0, Math.min(LADDER.length - 1, Math.floor(Number(process.env.JF_GG_START) || 0)));
if (process.env.JF_GG_TIME) GUNGAME.time = Number(process.env.JF_GG_TIME) || GUNGAME.time;
if (process.env.JF_INF_TIME) INFECT.time = Number(process.env.JF_INF_TIME) || INFECT.time;
if (process.env.JF_INF_DELAY) INFECT.delay = Number(process.env.JF_INF_DELAY) || INFECT.delay;
if (process.env.JF_INF_HP) INFECT.hp = Number(process.env.JF_INF_HP) || INFECT.hp;
// test knobs for the chaos modes: lives in one in the chamber, round length in seconds, how hard it rains ducks (x), JF_GAME = the online room's first mode
if (process.env.JF_LIVES) GAMES.oitc.lives = Number(process.env.JF_LIVES) || GAMES.oitc.lives;
if (process.env.JF_ROUND_TIME) for (const r of Object.values(ROUND)) r.time = Number(process.env.JF_ROUND_TIME) || r.time;
if (process.env.JF_DUCKS) DUCKRAIN.n = DUCKRAIN.n.map((x) => x * (Number(process.env.JF_DUCKS) || 1));
// the new secondaries: every soak / stun / pause / cage / SLOW DOWN lasts JF_SEC_SLOW x longer (screenshot runs on slow headless browsers)
if (process.env.JF_SEC_SLOW) { const k = Number(process.env.JF_SEC_SLOW) || 1, T = WEAPONS.taser; SPEED.jailT *= k; SPEED.warn *= k; WEAPONS.remote.pause.dur *= k; WEAPONS.water.soak.dur *= k; T.stun *= k; T.chainStun *= k; }
// /skip vote: how long it stays open and the cooldown after one fails, in ms (test knobs)
if (process.env.JF_SKIP_WINDOW) SKIP.window = Number(process.env.JF_SKIP_WINDOW) || SKIP.window;
if (process.env.JF_SKIP_COOL) SKIP.cooldown = Number(process.env.JF_SKIP_COOL) || SKIP.cooldown;
// test knobs for zombies: start on a later round, start rich, short breaks (ms), claw damage, bleed-out (s)
if (process.env.JF_ZM_ROUND) ZM.startRound = Number(process.env.JF_ZM_ROUND) || 1;
if (process.env.JF_ZM_CREDITS) ZM.start = Number(process.env.JF_ZM_CREDITS) || ZM.start;
if (process.env.JF_ZM_REST) ZM.rest = ZM.first = Number(process.env.JF_ZM_REST) || ZM.rest;
if (process.env.JF_ZM_SWIPE) ZM.swipe = Number(process.env.JF_ZM_SWIPE); // 0 = zombies can't hurt you (UI tests)
if (process.env.JF_ZM_BLEED) ZM.bleed = Number(process.env.JF_ZM_BLEED) || ZM.bleed;
function randomSkins() {
  const out = {};
  for (const id of Object.keys(WEAPONS)) if (Math.random() < 0.6) out[id] = [pick(SKIN_F), pick(SKIN_H), pick(SKIN_E), id === 'knife' ? pick(['default', 'knife_karambit', 'knife_butterfly', 'knife_switch', 'knife_cleaver']) : 'default', pick(WRAP_MODES)];
  return out;
}
function send(p, obj) { if (p.ws && p.ws.readyState === 1) p.ws.send(JSON.stringify(obj)); }

const TIP_IDS = Object.keys(ARROW_TIPS).filter((k) => !process.env.JF_ARROW_TIP || k === process.env.JF_ARROW_TIP); // test knob: JF_ARROW_TIP=sleep
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
for (const t of ['snap', 'frame', 'framex', 'quiz', 'quizx']) REC_T.add(t); // instant camera frames + pop quizzes in killcams
for (const k of ['beam', 'tele', 'nvflash']) REC_FX.add(k); // laser beams, frame teleports, goggle flashes
REC_FX.add('plough'); // shopping carts running people over
for (const t of ['mpatch', 'mslip', 'mpx']) REC_T.add(t); // marbles on the floor too
REC_T.add('lasso'); // lasso throws, catches, flings and splats too
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

// bot lanes as a graph: every waypoint is a node, lanes link their neighbours both ways, and lane starts (the spawns)
// and lane ends (the sites) link to each other, so a bot can get from any lane to any site or to a dropped bomb
const NAV = new WeakMap();
function navGraph(map) {
  if (!map || !map.nav || map.graph) return null; // maze maps have a real walk graph instead (shared/nav.js, navSteer)
  let g = NAV.get(map);
  if (g) return g;
  g = { pts: [], adj: [], ends: {} };
  const node = (q) => {
    const x = q[0], z = q[q.length - 1]; // [x, z] (or [x, y, z])
    let i = g.pts.findIndex((p) => Math.hypot(p[0] - x, p[1] - z) < 1);
    if (i < 0) { i = g.pts.length; g.pts.push([x, z]); g.adj.push([]); }
    return i;
  };
  const link = (a, b) => {
    if (a === b || g.adj[a].some((e) => e[0] === b)) return;
    const d = Math.hypot(g.pts[a][0] - g.pts[b][0], g.pts[a][1] - g.pts[b][1]);
    g.adj[a].push([b, d]); g.adj[b].push([a, d]);
  };
  const near = (list, r) => { for (const a of list) for (const b of list) if (Math.hypot(g.pts[a][0] - g.pts[b][0], g.pts[a][1] - g.pts[b][1]) < r) link(a, b); };
  const starts = [];
  for (const [site, lanes] of Object.entries(map.nav)) {
    g.ends[site] = [];
    for (const lane of lanes) {
      if (!lane.length) continue;
      const ids = lane.map(node);
      for (let i = 1; i < ids.length; i++) link(ids[i - 1], ids[i]);
      starts.push(ids[0]); g.ends[site].push(ids[ids.length - 1]);
    }
  }
  near(starts, 22);
  for (const e of Object.values(g.ends)) near(e, 30);
  NAV.set(map, g);
  return g;
}
// cheapest path (dijkstra, the graph is tiny) from node a to any of the goal nodes. cost(u, v, d): edge cost (default: length)
function navPath(g, a, goals, cost) {
  const n = g.pts.length, dist = new Array(n).fill(Infinity), prev = new Array(n).fill(-1), done = new Array(n).fill(false);
  dist[a] = 0;
  for (;;) {
    let u = -1;
    for (let i = 0; i < n; i++) if (!done[i] && dist[i] < Infinity && (u < 0 || dist[i] < dist[u])) u = i;
    if (u < 0) return null;
    if (goals.includes(u)) { const path = []; for (let v = u; v >= 0; v = prev[v]) path.unshift(v); return { path, cost: dist[u] }; }
    done[u] = true;
    for (const [v, d] of g.adj[u]) { const c = dist[u] + (cost ? cost(u, v, d) : d); if (c < dist[v]) { dist[v] = c; prev[v] = u; } }
  }
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
    this.smokes = new Map(); this.nextSmoke = 1; // smoke clouds: bots can't see through them, late joiners get them
    this.oitcOut = new Set(); // one in the chamber: who ran out of lives this round (by account or name)
    if (mode === 'ffa' && GAMES[process.env.JF_GAME]) this.game = process.env.JF_GAME; // test knob: the online room starts in this mode
    this.mpatches = new Map(); this.nextMp = 1; // marble shotgun: marbles on the floor you slip on
    this.cfg = { map: mode === 'training' ? 'range' : mode === 'coop' ? 'warehouse' : 'islands', hip: 'normal', bots: 5, diff: 'normal', hr: 'on' };
    if (GAMES[this.game].mapOk && !GAMES[this.game].mapOk(this.map)) this.cfg.map = mapsFor(this.game, MAPS, MAP_ORDER)[0]; // (the JF_GAME knob: a map the mode can be played on)
    if (GAMES[this.game].zombies) this.setGame(this.game); // JF_GAME=zm: zombies brings its own map
    this.wave = 0; this.toSpawn = 0; this.interUntil = 0;
    this.round = ROUND[mode] ? { target: ROUND[mode].kills, ends: now() + ROUND[mode].time * 1000, over: false, next: 0 } : null;
    if (mode === 'coop') this.interUntil = now() + 4000;
    if (this.round) this.round.t0 = now();
    this.traffic = new Traffic(this);
  }
  get map() { return MAPS[this.cfg.map]; }
  get boxes() { return this.zm ? this.zs.boxes : this.map.boxes; } // zombies: plus the shutters still down

  broadcast(obj, exceptId) {
    const s = JSON.stringify(obj);
    if (REC_T.has(obj.t) && (obj.t !== 'fx' || REC_FX.has(obj.k)) && (obj.t !== 'pd' || obj.x)) this.rec.ev.push({ s: now(), m: obj });
    for (const p of this.players.values()) if (p.id !== exceptId && p.ws && p.ws.readyState === 1) p.ws.send(s);
  }
  humans() { return [...this.players.values()].filter((p) => !p.isBot); }
  sendTo(p, m) { send(p, m); } // for server/ modules
  teamsOn() { return (this.mode === 'ffa' || this.mode === 'bots') && !!GAMES[this.game].teams; }
  fighters() { return [...this.players.values()].filter((p) => !(p.isBot && p.ai && p.ai.dummy) && !p.watch); }
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
    for (const slot of ['primary', 'secondary', 'melee']) lo[slot] = pick(Object.keys(WEAPONS).filter((id) => WEAPONS[id].slot === slot && !WEAPONS[id].modeOnly));
    // weapons only: you keep the item in your own loadout (and its server-side charges). the popper + reverse card are
    // items now, so they left the secondary pool
    return lo;
  }
  sendLoadout(p) {
    if (p.watch) return;
    if (this.isEcon()) { this.econLoadout(p); return; } // Plant & Defuse economy: the gear you bought, not a loadout
    if (p.ec) this.econEnd(p);
    if (this.zm) { if (!p.isBot) this.zmLoadout(p); return; } // zombies: the guns you bought
    if (this.modeLoadout(p)) return; // gun game rung / zombie claw
    if (this.brOn) { this.brLoadout(p); return; } // jank royale: what you picked up
    if (this.sendChaosKit(p)) return;
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

  // could someone standing at spawn s see p? (within the fog, nothing in between)
  inSight(s, p) {
    const e = [s[0], s[1] + PH.eye, s[2]], d = [p.pos[0] - e[0], p.pos[1] + 1 - e[1], p.pos[2] - e[2]], l = Math.hypot(...d);
    return l < (this.map.fogFar || 1e9) && !raycast(e, [d[0] / l, d[1] / l, d[2] / l], l, this.boxes);
  }

  pickSpawn(forBot, who) {
    let spawns = this.map.spawns;
    if (this.lavaOn) spawns = surfaces(this.map).spawns; // floor is lava: only ever spawn on safe ground
    const ts = this.map.teamSpawns;
    if (who && who.team && this.teamsOn() && ts && !(this.map.teamSpawnsBomb && this.game !== 'bomb')) { // teamSpawnsBomb: other team modes spawn all over, away from enemies
      const attacking = this.game === 'bomb' ? who.team === (this.bomb ? this.bomb.att : 1) : who.team === 1;
      spawns = attacking ? ts.att : ts.def;
    }
    let best = spawns[0], bestD = -1;
    for (const s of spawns) {
      let d = 1e9;
      for (const p of this.players.values()) if (p.alive && p !== who && (!forBot || !p.isBot) && !(who && who.team && p.team === who.team)) d = Math.min(d, dist3(s, p.pos));
      if (this.map.spawnSafe) for (const p of this.players.values()) if (p.alive && p !== who && (!forBot || !p.isBot) && !(who && who.team && p.team === who.team) && this.inSight(s, p)) d = Math.min(d, dist3(s, p.pos) * 0.3); // in plain sight down a long hall isn't safe
      if (this.map.spawnSafe) d = Math.min(d, this.map.spawnSafe); // huge maps: far enough is far enough, then it's random (not always the one corner farthest from you)
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
    const p = {
      id, ws: opts.ws || null, room: this, name, color, pos, vel: [0, 0, 0], yaw: Math.random() * 6, pitch: 0,
      w: opts.w || 'ar', hp: 100, alive: true, respawnAt: 0, kills: 0, deaths: 0, seq: 1, spawnT: now(), reverseUntil: 0,
      lastAttacker: 0, lastAttackW: null, lastAttackT: 0, lastFire: {}, pair: new Map(), g: null, f: 0,
      chatT: 0, coughT: 0, cfgT: 0, skinT: 0, skins: opts.skins || {}, isBot: !!opts.isBot, ai: opts.ai || null,
      onGround: false, slipUntil: 0, acct: opts.acct || null, level: opts.level || 0,
    };
    matchReset(p); // this match's report starts now, even for someone joining mid-match
    return p;
  }
  info(p) { return { id: p.id, name: p.name, color: p.color, skins: p.skins, bot: p.isBot, level: p.level, look: p.look, card: p.card || '', team: p.team || 0, grap: p.grap || 'rope' }; }

  addHuman(ws, m) {
    if (this.mode === 'bots' && m.cfg && typeof m.cfg === 'object' && !this.humans().length && !this.lobby) {
      const c = m.cfg;
      if (has(MAPS, c.map) && MAP_ORDER.includes(c.map)) this.cfg.map = c.map;
      if (has(HIPFIRE, c.hip)) this.cfg.hip = c.hip;
      if (has(BOT_DIFF, c.diff)) this.cfg.diff = c.diff;
      if (c.bots != null) this.cfg.bots = clampInt(c.bots, 0, 12);
      if (has(HR.every, c.hr)) this.cfg.hr = c.hr;
    }
    const name = m._name || clean(m.name, 16) || pick(DEFAULT_NAMES) + nextId;
    const inv = m._inv || {};
    const p = this.newPlayer(name, { ws, skins: enforceSkins(cleanSkins(m.skins), inv, m._achs), acct: m._acct, level: m._level });
    p.inv = inv;
    p.tip = pick(TIP_IDS);
    p.look = validLook(m.look, m._achs || new Set());
    if (p.look.color) p.color = p.look.color;
    p.card = cleanCard(m.card);
    p.streaks = validStreaks(m.streaks);
    p.kfx = ownedKill(m.kfx, inv);
    p.grap = ownedGrapple(m.grap, inv);
    p.kc = !!m.kc;
    p.item = has(ITEMS, m.item) ? m.item : 'frag'; // the client confirms it with 'itemsel' right after 'welcome'
    if (process.env.JF_WATCH && name.startsWith('watch')) { p.watch = true; p.alive = false; p.hp = 0; p.respawnAt = p.minRespawnAt = Infinity; } // test knob: a ws observer for bots-only matches (never a fighter)
    if (this.mode === 'bots' && m.cfg && typeof m.cfg === 'object' && has(GAMES, m.cfg.game) && !this.humans().length && !this.lobby) this.setGame(m.cfg.game);
    if (this.mode === 'bots' && !this.humans().length && !this.lobby && !this.map.zm !== !GAMES[this.game].zombies) this.setGame(this.map.zm ? 'zm' : this.game); // the zombie map only with zombies
    if (!p.watch) this.joinTeam(p);
    if (p.team) p.pos = this.pickSpawn(false, p);
    if (this.isEcon() && !p.watch) this.econJoin(p);
    this.players.set(p.id, p);
    // in from the start (or close enough): your Never Landed run counts. the welcome below is your first spawn
    if (this.round && !this.round.over && !this.warm && now() - (this.round.t0 || 0) < AIR.join && !GAMES[this.game].lava && !GAMES[this.game].royale) p.air = { ok: !(this.airBad && this.airBad.has(name)), rest: 0 };
    send(p, {
      t: 'welcome', id: p.id, name, color: p.color, pos: p.pos, q: p.seq, mode: this.mode, cfg: this.cfg,
      players: [...this.players.values()].filter((o) => o !== p).map((o) => this.info(o)),
      peels: [...this.peels.values()].map((pl) => ({ id: pl.id, p: pl.p })),
      projs: [...this.projectiles.values()].map((pr) => ({ id: pr.id, k: pr.k, p: pr.p, v: pr.v, o: pr.o })),
      holes: [...this.holes.values()].map((h) => ({ id: h.id, p: h.p, o: h.o, big: h.big, on: h.on || 0, age: (now() - h.born) / 1000 })),
      wave: this.waveInfo(), level: p.level, account: !!p.acct, round: this.roundInfo(),
      bubbles: [...this.bubbles.values()].map((b) => ({ id: b.id, p: b.p, r: b.r, left: b.until - now() })),
      smokes: [...this.smokes.values()].map((s) => [...s.p, Math.round(s.until - now())]), ic: this.icInfo(p),
      kat: [...this.players.values()].filter((o) => o.kat).map((o) => [o.id, o.kat]),
      game: this.game, team: p.team || 0, tags: [...this.tags.values()].map((g) => ({ id: g.id, p: g.p, team: g.team })), vote: this.voteInfo(),
      sprays: this.sprayList(), skip: skipInfo(this), lobby: this.warmInfo ? this.warmInfo() || undefined : undefined, lk: this.lobby ? this.lobby.kind : undefined,
      mpatch: this.patchList(),
    });
    this.broadcast({ t: 'pj', ...this.info(p) }, p.id);
    skipPeople(this); // one more human: a skip vote needs more
    send(p, { t: 'tip', tip: p.tip });
    for (const t of this.players.values()) if (t.trap) send(p, { t: 'trap', ...this.trapInfo(t) }); // anyone already floating in a soap bubble
    this.gearJoin(p); // photo frames standing, quizzes going
    this.cartsFor(p); // shopping carts already out
    this.lassoJoin(p); // anyone already hanging off a lasso
    send(p, { t: 'court', s: [...this.players.values()].filter((o) => o.streak > 0).map((o) => [o.id, o.streak]) }); // scales of justice: streaks so far
    if (p.air && p.air.ok) send(p, { t: 'air', on: 1, grace: AIR.grace });
    deal(p);
    this.modeJoin(p);
    if (this.brOn && !p.watch) this.brJoin(p); // jank royale: a seat on the blimp, or watch till the next one
    this.sendLoadout(p);
    if (this.mode === 'ffa' || this.mode === 'coop') this.broadcast({ t: 'chat', id: 0, m: `${name} joined` });
    if (this.mode === 'bots') this.fillBots();
    if (this.mode === 'bots' && this.humans().length === 1 && this.game !== 'dm' && !this.lobby) this.startRound();
    if (process.env.JF_FFA_BOMB) this.econTestStart(); // test knob
    if (this.mode === 'ffa' && GAMES[this.game].zombies && !this.zm && this.humans().length === 1 && !this.lobby) this.startRound(); // JF_GAME=zm: the first one in sets the zombies up
    if (this.mode === 'training') this.spawnDummies();
    console.log(`+ ${name} (#${p.id}) -> ${this.id}`);
    return p;
  }

  remove(p) {
    flushStats(p);
    this.lassoDrop(p, 'gone'); // ropes they held (or hung off) drop
    if (this.bomb && this.bomb.carrier === p.id) this.dropBomb(p.pos, p);
    if (this.brOn) this.brLeave(p); // their pockets spill out
    if (this.isEcon()) this.econLeave(p);
    this.players.delete(p.id);
    // whatever they threw goes with them (with no owner it would ignore teams and bubbles); their holes and gas go inert
    for (const pr of this.projectiles.values()) if (pr.o === p.id) this.removeProj(pr);
    this.broadcast({ t: 'pl', id: p.id });
    if (this.vote) { if (this.vote.votes.delete(p.id)) this.broadcast({ t: 'votes', ...this.voteCounts() }); this.voteHurry(); } // whoever's left may all have voted now
    if (this.livesOn) this.oitcList(); // so 'N left' drops them
    if (!p.isBot) skipPeople(this); // a skip vote's majority moved
    if (!p.isBot && (this.mode === 'ffa' || this.mode === 'coop')) this.broadcast({ t: 'chat', id: 0, m: `${p.name} left` });
    if (!this.humans().length) rooms.delete(this.id);
    else if (!p.isBot && this.mode === 'bots') this.fillBots(); // a human left: a bot takes the place back
  }

  // ---------------------------------------------------------- bots
  addBot(opts = {}) {
    const diff = this.cfg.diff;
    const taken = new Set([...this.players.values()].map((p) => p.name)), free = BOT_NAMES.filter((n) => !taken.has(`${n} [bot]`)); // no two Garys if it can help it
    const b = this.newPlayer(opts.dummy ? 'Dummy' : `${pick(free.length ? free : BOT_NAMES)} [bot]`, {
      isBot: true, pos: opts.pos, color: opts.dummy ? '#cccccc' : '#aaaaaa',
      w: opts.dummy ? 'ar' : pick(BOT_GUNS), skins: opts.dummy ? {} : randomSkins(),
      ai: { diff, target: 0, retarget: 0, nextShot: now() + 1500, seenAt: 0, ammo: 0, reloadUntil: 0, jumpT: 0, wp: null, seed: Math.random() * 100, dummy: opts.dummy || null, strafeDir: 1 },
    });
    b.ai.ammo = WEAPONS[b.w].mag || 1;
    this.lassoArm(b); // some bot-room bots carry the lasso
    if (!opts.dummy && Math.random() < 0.5) b.grap = pick(GRAP_IDS); // bots show off ropes you can roll
    if (!opts.dummy) { this.joinTeam(b); if (b.team) b.pos = this.pickSpawn(true, b); }
    if (!opts.dummy && this.isEcon()) this.econJoin(b);
    this.players.set(b.id, b);
    this.sendLoadout(b); // bots added mid-match get the mode's weapons too
    this.broadcast({ t: 'pj', ...this.info(b) });
    if (!opts.dummy) this.modeJoin(b);
    if (!opts.dummy && this.brOn) this.brJoin(b);
    return b;
  }
  removeBots() { for (const b of [...this.players.values()]) if (b.isBot) this.remove(b); }
  // Play With Bots: the room is (bot count + 1) players. every human who joins takes a bot's place, so bots are slowly
  // replaced by people; when someone leaves, a bot comes back. (the JF_WATCH test observer isn't a player)
  botWant() {
    const h = this.humans().filter((p) => !p.watch).length;
    if (this.lobby) return GAMES[this.lobby.next] && GAMES[this.lobby.next].zombies ? 0 : Math.max(0, this.lobbySize() - Math.max(1, h)); // a mode lobby: humans take bots' places (no bots in a zombies warm-up)
    const size = this.brOn ? Math.max(clampInt(this.cfg.bots, 0, 12), clampInt(process.env.JF_BR_BOTS || BR.bots, 0, 31)) : clampInt(this.cfg.bots, 0, 12); // a royale wants a crowd
    return Math.max(0, size + 1 - Math.max(1, h));
  }
  fillBots() {
    if (GAMES[this.game].zombies) return; // zombies brings its own bots
    const want = this.botWant();
    const bots = [...this.players.values()].filter((p) => p.isBot && !(p.ai && p.ai.dummy));
    const staying = bots.filter((b) => !b.leaving);
    // someone left: a bot that was on its way out stays after all, then new ones fill up
    for (const b of bots) if (b.leaving && staying.length < want) { b.leaving = false; staying.push(b); }
    for (let i = staying.length; i < want; i++) this.addBot();
    if (staying.length <= want) return;
    // too many: the dead go first (right away), then from the bigger team; alive ones leave when the round ends
    const c = { 1: 0, 2: 0 };
    for (const p of this.fighters()) if (p.team && !p.leaving) c[p.team]++;
    const order = staying.slice().sort((a, b) => (a.alive - b.alive) || ((c[b.team] || 0) - (c[a.team] || 0)));
    for (const b of order.slice(0, staying.length - want)) this.retireBot(b);
  }
  retireBot(b) {
    if (!b.alive) { this.remove(b); return; }
    b.leaving = true; // round modes: at the round's end. others: as soon as it dies (dropLeavers)
  }
  // bots marked to make room for a human: gone once they're dead, and all of them at a round's start
  dropLeavers(all) { for (const b of [...this.players.values()]) if (b.isBot && b.leaving && (all || !b.alive)) this.remove(b); }
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
      if (t.quiz) continue; // sitting a pop quiz: nothing can hurt them till it's marked
      if (this.friendly(b, t)) continue; // infection: zombies hunt survivors, survivors shoot zombies
      if (this.brOn && !this.brTargetable(t)) continue; // on the blimp / out
      const d = dist3(t.pos, b.pos);
      const vis = this.canSee(eyeOf(b), [t.pos[0], t.pos[1] + 1, t.pos[2]]);
      let score = d * (vis ? 1 : 2.5);
      if (this.brOn) score = this.brBotScore(b, t, score); // pick fights you can win, third-party the hurt ones
      if (score < bestD) { bestD = score; best = t; }
    }
    return best;
  }
  // bot eyesight: walls and smoke clouds block it
  canSee(a, c) {
    const d = [c[0] - a[0], c[1] - a[1], c[2] - a[2]], l = Math.hypot(d[0], d[1], d[2]);
    if (l < 1e-6) return true;
    return !raycast(a, [d[0] / l, d[1] / l, d[2] / l], l, this.boxes) && !this.smokeBlocks(a, c);
  }
  smokeBlocks(a, c) {
    if (!this.smokes.size) return false;
    const d = [c[0] - a[0], c[1] - a[1], c[2] - a[2]], l2 = d[0] * d[0] + d[1] * d[1] + d[2] * d[2] || 1;
    for (const s of this.smokes.values()) { // closest point of the sight line to the cloud's centre
      const k = Math.max(0, Math.min(1, ((s.p[0] - a[0]) * d[0] + (s.p[1] - a[1]) * d[1] + (s.p[2] - a[2]) * d[2]) / l2));
      if (Math.hypot(a[0] + d[0] * k - s.p[0], a[1] + d[1] * k - s.p[1], a[2] + d[2] * k - s.p[2]) < s.r) return true;
    }
    return false;
  }

  botThink(b, dt) {
    const ai = b.ai, n = now(), D = BOT_DIFF[ai.diff] || BOT_DIFF.normal;
    if (b.sleepUntil > n) return { wx: 0, wz: 0, jump: false };
    if (n < (b.blindUntil || 0)) { if (this.lassoHolding(b)) this.lassoEnd(b, 'drop'); return this.botBlind(b, dt); } // flashed by goggles: stumbling about, can't see a thing (and lets go of the rope)
    const lt = this.lassoThink(b, dt); // a lasso bot holding someone does the fling routine (server/lasso.js)
    if (lt) return lt;
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
    let t = this.players.get(ai.target);
    if (t && this.friendly(b, t)) { ai.target = 0; ai.seenAt = 0; t = null; } // teams got reshuffled: that's a teammate now
    if (this.brOn) this.brBotWeapon(b, t && t.alive ? dist3(t.pos, b.pos) : 20); // the right gun for the range
    this.botChaosThink(b, t, n);
    let wx = 0, wz = 0, jump = false;
    const w = WEAPONS[b.w];
    const pref = RIFLE_PREF[b.w] ? [...RIFLE_PREF[b.w]] : b.w === 'sniper' ? [25, 60] : b.w === 'shotgun' ? [3, 9] : b.w === 'sawnoff' ? [1.5, 6] : b.w === 'akimbo' ? [4, 13] : b.w === 'marbles' ? [1.5, 4] : b.w === 'chicken' ? [10, 30] : b.w === 'shredder' ? [1.5, 9] : [7, 22];
    if (w.kind === 'melee') { pref[0] = 0; pref[1] = this.chaosKit || this.isEcon() ? 1.2 : w.range * 0.7; } // claws, melee rungs, spoons + knives: get in their face
    if (b.w === 'taser') { pref[0] = 2; pref[1] = 6; } // darts on wires: get close
    if (t && t.alive) {
      const e = eyeOf(b), tc = [t.pos[0], t.pos[1] + 1.1, t.pos[2]];
      const dx = tc[0] - e[0], dy = tc[1] - e[1], dz = tc[2] - e[2];
      const hd = Math.hypot(dx, dz), dist = Math.hypot(dx, dy, dz);
      const vis = this.canSee(e, tc);
      if (vis && !ai.seenAt) ai.seenAt = n;
      if (!vis) ai.seenAt = 0;
      const yaw = Math.atan2(-dx, -dz), pitch = Math.atan2(dy, hd);
      b.yaw = lerpAngle(b.yaw, yaw, D.turn * dt);
      b.pitch += (pitch - b.pitch) * Math.min(1, D.turn * dt);
      const fx = dx / (hd || 1), fz = dz / (hd || 1);
      if (dist > pref[1] || !vis) { wx += fx; wz += fz; } else if (dist < pref[0]) { wx -= fx; wz -= fz; }
      if (Math.random() < dt * 0.6) ai.strafeDir *= -1;
      if (w.kind !== 'melee') { wx += -fz * ai.strafeDir * 0.8; wz += fx * ai.strafeDir * 0.8; } // melee bots circling at 1 m never line up a swing
      let ang = Math.abs(b.yaw - yaw) % (Math.PI * 2); if (ang > Math.PI) ang = Math.PI * 2 - ang;
      const meleeOk = w.kind === 'melee' && dist < w.range && ang < 0.6; // up close the angle swings too fast for the gun aim check
      if (vis && (meleeOk || (ai.seenAt && n - ai.seenAt > D.react && ang < 0.25)) && n >= ai.nextShot && n >= ai.reloadUntil && dist < (w.range || 60) + (w.kind === 'melee' ? 1 : 0)) this.botFire(b, t, D);
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
      if (goal.use && gl < goal.r) { wx = 0; wz = 0; jump = false; this.tryUse(b); ai.progQ = null; }
      else if (goal.force || !t || !t.alive || !ai.seenAt) { wx = gx / (gl || 1); wz = gz / (gl || 1); if (ai.navJump && b.onGround) jump = true; }
      else ai.progQ = null; // busy fighting, not walking the route: that doesn't count as stuck
    }
    ai.navJump = false;
    // mazes: follow the map's walk graph (shared/nav.js) to wherever we were about to walk straight at (and into a wall).
    // in every mode: fights, wandering, the bomb (lane waypoints from laneTo, a dropped bomb), tags
    if (this.map.graph) {
      const gl = goal ? Math.hypot(goal.p[0] - b.pos[0], goal.p[2] - b.pos[2]) : 0;
      const want = goal && (goal.force || !t || !t.alive || !ai.seenAt) ? (goal.use && gl < goal.r ? null : goal.p) : t && t.alive ? (ai.seenAt && !(n < (ai.edgeT || 0)) ? null : t.pos) : ai.wp; // (seen across a canyon: the edge turned us back, so walk the graph round to them)
      const s = want && navSteer(this.map.graph, ai.nav || (ai.nav = {}), b.pos, want, n);
      if (s) {
        wx = s[0]; wz = s[1];
        if (s[2] && b.onGround) jump = true; // hop to get unstuck
        if (!t || !t.alive || (!ai.seenAt && dist3(t.pos, b.pos) > 12)) b.yaw = lerpAngle(b.yaw, Math.atan2(-wx, -wz), 30 * dt); // look where you walk, not through walls
      }
    }
    if (goal && goal.tac) [wx, wz] = this.econAiHold(b, goal, t, wx, wz, dt); // Plant & Defuse: hold an angle, watch it
    // grappling: chase people who are far / up high / out of sight, save yourself when falling, show off sometimes
    if (!ai.hook && n >= (ai.nextHook || 0) && this.mode !== 'training' && !this.hookOff()) {
      const skill = ai.diff === 'easy' ? 0.35 : ai.diff === 'hard' ? 1 : 0.7;
      const below = !b.onGround && !raycast([b.pos[0], b.pos[1] + 0.5, b.pos[2]], [0, -1, 0], 40, boxes);
      let want = null;
      if (below && (b.vel[1] < -4 || b.pos[1] < this.map.killY + 25)) { // falling into the void: hook back toward the middle, up high
        const c = this.map.spawns ? this.map.spawns[0] : [0, 0, 0];
        want = [c[0] - b.pos[0], 18 + Math.max(0, c[1] - b.pos[1]), c[2] - b.pos[2]];
      } else if (t && t.alive && (b.inf || Math.random() < skill)) {
        const dx = t.pos[0] - b.pos[0], dy = t.pos[1] - b.pos[1], dz = t.pos[2] - b.pos[2];
        const hd = Math.hypot(dx, dz);
        if (hd > pref[1] + 10 || dy > 4 || !ai.seenAt || (b.inf && hd > 6)) want = [dx, dy + hd * 0.35 + 6, dz];
      } else if (!t && Math.random() < 0.25 * skill) {
        const a = Math.random() * Math.PI * 2;
        want = [Math.cos(a) * 20, 14 + Math.random() * 10, Math.sin(a) * 20];
      }
      ai.nextHook = n + (want ? 700 : 1800) + Math.random() * 1200 / skill;
      if (want) {
        const l = Math.hypot(...want) || 1, d = want.map((v) => v / l), e = eyeOf(b);
        const h = raycast(e, d, HOOK.range, boxes);
        if (h && h.t > 6 && h.point[1] > b.pos[1] - 1 && (this.map.ceiling == null || h.point[1] < this.map.ceiling - 1.5)) { ai.hook = { point: h.point, len: h.t, until: n + 2600 }; b.g = h.point; } // (not up over a map's ceiling: that's out of bounds)
      }
    }
    if (ai.hook) jump = false;
    [wx, wz] = this.botGearSteer(b, wx, wz); // walking into its own photo frame
    const wl = Math.hypot(wx, wz);
    if (wl > 0) { wx /= wl; wz /= wl; }
    // don't walk off the map (bots are dumb, not suicidal). a floor up to 15 m down will do (no fall damage); a box
    // far below is no floor: a long fall drifts past it into the void
    if (this.map.bounds && (outOfBounds(this.map, b.pos) || (wl > 0 && outOfBounds(this.map, [b.pos[0] + wx * 3, 0, b.pos[2] + wz * 3])))) {
      // back in, toward the middle. up over the ceiling (on a roof): off the nearest edge of whatever it's standing on
      let c = boundsCenter(this.map);
      const q = this.map.ceiling != null && b.pos[1] > this.map.ceiling && this.boxes.find((o) => b.pos[0] >= o.min[0] && b.pos[0] <= o.max[0] && b.pos[2] >= o.min[2] && b.pos[2] <= o.max[2] && Math.abs(o.max[1] - b.pos[1]) < 0.6);
      if (q) { const e = [[b.pos[0] - q.min[0], q.min[0] - 6, b.pos[2]], [q.max[0] - b.pos[0], q.max[0] + 6, b.pos[2]], [b.pos[2] - q.min[2], b.pos[0], q.min[2] - 6], [q.max[2] - b.pos[2], b.pos[0], q.max[2] + 6]].sort((u, v) => u[0] - v[0])[0]; c = [e[1], e[2]]; }
      // a fenced map (map.gates: the gaps in its fence, [x, z] outside each and [x, z] inside): out past the fence, head
      // for the nearest gap, then in through it (straight at the middle it'd stand against the fence all day)
      else if (this.map.gates && outOfBounds(this.map, b.pos)) {
        const d = (x, z) => Math.hypot(x - b.pos[0], z - b.pos[2]), g = this.map.gates.reduce((u, v) => (d(v[0], v[1]) < d(u[0], u[1]) ? v : u));
        const L = Math.hypot(g[2] - g[0], g[3] - g[1]) || 1, ux = (g[2] - g[0]) / L, uz = (g[3] - g[1]) / L, wx2 = b.pos[0] - g[0], wz2 = b.pos[2] - g[1];
        const along = wx2 * ux + wz2 * uz, side = Math.abs(wx2 * uz - wz2 * ux); // lined up with the gap (in its corridor): go in; else to its outside end
        c = d(g[0], g[1]) < 3 || (along > -1 && side < 2.5) ? [g[2], g[3]] : [g[0], g[1]];
      }
      const dx = c[0] - b.pos[0], dz = c[1] - b.pos[2], l = Math.hypot(dx, dz) || 1;
      wx = dx / l; wz = dz / l;
      if (outOfBounds(this.map, b.pos)) b.yaw = lerpAngle(b.yaw, Math.atan2(-wx, -wz), 8 * dt);
    }
    if (wl > 0 && b.onGround) {
      const probe = [b.pos[0] + wx * 2.5, b.pos[1] + 0.5, b.pos[2] + wz * 2.5];
      if (!raycast(probe, [0, -1, 0], Math.max(6, Math.min(15, probe[1] - this.map.killY)), boxes)) { wx = -wx; wz = -wz; ai.strafeDir *= -1; if (this.map.edgeGuard) ai.edgeT = n + 3000; }
    }
    if (this.map.edgeGuard && !b.onGround && this.botFlightLands(b)) { wx = 0; wz = 0; jump = false; } // thrown over the canyon (a jump pad, a hit) onto the far side: let it fly (steering back brakes it into the drop)
    else if (this.brOn || this.map.edgeGuard) { const e = this.brBotEdge(b, wx, wz, jump); if (this.map.edgeGuard && (e[0] !== wx || e[1] !== wz)) ai.edgeT = n + 3000; [wx, wz, jump] = e; } // jank royale (and maps with a canyon, map.edgeGuard): no hopping into canyons. turned back from one: find a bridge (above)
    if (jump && this.map.edgeGuard && b.onGround && [[2, 0], [-2, 0], [0, 2], [0, -2]].some(([dx, dz]) => !raycast([b.pos[0] + dx, b.pos[1] + 0.5, b.pos[2] + dz], [0, -1, 0], 15, boxes))) jump = false; // a drop beside us (a bridge, the lip): no hops. a hop off a parapet's end is how they fell in
    if (this.lavaOn) [wx, wz, jump] = this.botLava(b, wx, wz, jump, t);
    if (this.hr && this.hr.on) { const o = hrBot(this, b, dt, { wx, wz, jump }), l = Math.hypot(o.wx, o.wz); if (l > 1) { o.wx /= l; o.wz /= l; } ({ wx, wz, jump } = o); } // scary forest: don't stare at HR
    return { wx: wx * D.speed, wz: wz * D.speed, jump };
  }

  // walk the map's lanes toward a site (bots can't path-find, so maps give them routes: see navGraph)
  routeTo(b, siteId, final) {
    if (this.map.graph) return this.laneTo(b, siteId, final); // maze maps: the walk graph drives (see laneTo)
    const g = navGraph(this.map), ends = g && g.ends[siteId];
    return ends && ends.length ? this.navTo(b, 'site' + siteId, final, ends) : final;
  }
  // can a bot walk straight from pos (feet) to q ([x, z])? two rays a body-width apart, at knee and chest height
  clearPath(pos, q) {
    const dx = q[0] - pos[0], dz = q[1] - pos[2], l = Math.hypot(dx, dz);
    if (l < 0.5) return true;
    const d = [dx / l, 0, dz / l], sx = -d[2] * 0.38, sz = d[0] * 0.38;
    for (const h of [0.75, 1.5]) for (const s of [-1, 1]) if (raycast([pos[0] + sx * s, pos[1] + h, pos[2] + sz * s], d, l, this.boxes)) return false;
    return true;
  }
  // the nearest waypoint you can walk straight to (or just the nearest one)
  navEntry(pos, g, avoid = -1) {
    const order = g.pts.map((q, i) => [Math.hypot(q[0] - pos[0], q[1] - pos[2]), i]).filter((e) => e[1] !== avoid).sort((a, c) => a[0] - c[0]);
    if (!order.length) return -1;
    for (const [d, i] of order) if (d < 90 && this.clearPath(pos, g.pts[i])) return i;
    return order[0][1];
  }
  // follow a path through the lane graph to final: go straight once final is in plain sight, cut a corner only when
  // the next waypoint is, and when it stops getting closer, hop and then plan again from where it stands
  navTo(b, key, final, goals) {
    const ai = b.ai, n = now(), g = navGraph(this.map);
    if (!g) return final;
    if (ai.navKey !== key) { ai.navKey = key; ai.route = null; ai.avoid = -1; }
    if (n - (ai.navT || 0) > 500) { ai.progQ = null; ai.losT = 0; } // wasn't routing a moment ago (frozen, asleep, dead)
    if (ai.hook) ai.progQ = null; // swinging somewhere: plans again when it lets go
    ai.navT = n;
    if (n >= (ai.losT || 0)) {
      ai.losT = n + 250;
      ai.direct = Math.hypot(final[0] - b.pos[0], final[2] - b.pos[2]) < 25 && this.clearPath(b.pos, [final[0], final[2]]);
      if (!ai.direct && ai.route && ai.ri + 1 < ai.route.length && this.clearPath(b.pos, ai.route[ai.ri + 1])) ai.ri++;
    }
    let tgt = final;
    if (ai.direct) ai.route = null;
    else {
      if (!ai.route) {
        // a little random cost per waypoint spreads bots over the lanes; legs it got stuck on cost a lot for a while
        const from = this.navEntry(b.pos, g, ai.avoid), jit = g.pts.map(() => 1 + Math.random() * 0.6), bl = ai.blocked;
        const r = from >= 0 ? navPath(g, from, goals, (u, v, d) => d * jit[v] + (bl && (bl.get(u + ':' + v) || 0) > n ? 1000 : 0)) : null;
        ai.rnodes = r ? r.path : []; ai.route = ai.rnodes.map((i) => g.pts[i]); ai.ri = 0;
      }
      const rt = ai.route;
      while (ai.ri < rt.length && Math.hypot(rt[ai.ri][0] - b.pos[0], rt[ai.ri][1] - b.pos[2]) < 1.2) ai.ri++;
      if (ai.ri < rt.length) tgt = [rt[ai.ri][0], b.pos[1], rt[ai.ri][1]];
    }
    const d = Math.hypot(tgt[0] - b.pos[0], tgt[2] - b.pos[2]);
    if (!ai.progQ || Math.abs(ai.progQ[0] - tgt[0]) + Math.abs(ai.progQ[1] - tgt[2]) > 0.5 || d < ai.progD - 1) { ai.progQ = [tgt[0], tgt[2]]; ai.progD = d; ai.progT = n; }
    else if (d > 1.5 && n - ai.progT > 1200) {
      ai.navJump = true;
      if (n - ai.progT > 2600) {
        ai.avoid = -1;
        if (ai.route && ai.ri < ai.rnodes.length) {
          ai.avoid = ai.rnodes[ai.ri];
          if (ai.ri > 0) (ai.blocked ||= new Map()).set(ai.rnodes[ai.ri - 1] + ':' + ai.avoid, n + 60000);
        }
        ai.route = null; ai.direct = false; ai.losT = n + 1500; ai.progQ = null;
      }
    }
    return tgt;
  }
  // a dropped bomb: the one or two attacker bots closest to it by walking distance go get it (re-picked every 1.5 s)
  dropChasers() {
    const B = this.bomb, n = now(), key = B.drop.join();
    if (B.chase && B.chase.key === key && n < B.chase.until) return B.chase.ids;
    const g = navGraph(this.map), at = B.drop;
    B.dropNode = g ? this.navEntry([at[0], at[1] - 0.15, at[2]], g) : -1;
    const cost = (p) => {
      const d = Math.hypot(p.pos[0] - at[0], p.pos[2] - at[2]);
      if (B.dropNode < 0 || (d < 25 && this.clearPath(p.pos, [at[0], at[2]]))) return d;
      const a = this.navEntry(p.pos, g), r = a >= 0 ? navPath(g, a, [B.dropNode]) : null;
      return r ? Math.hypot(g.pts[a][0] - p.pos[0], g.pts[a][1] - p.pos[2]) + r.cost + Math.hypot(g.pts[B.dropNode][0] - at[0], g.pts[B.dropNode][1] - at[2]) : d * 3;
    };
    const ids = this.fighters().filter((p) => p.isBot && p.alive && p.team === B.att).map((p) => [cost(p), p.id]).sort((a, c) => a[0] - c[0]).slice(0, 2).map((e) => e[1]);
    B.chase = { key, until: n + 1500, ids };
    return ids;
  }
  // maze maps (map.graph, e.g. Backrooms): walk one of the site's lanes waypoint by waypoint (they spread the bots out,
  // one goes down through the pools); navSteer in botThink walks each leg through the walk graph, stairs and drops
  laneTo(b, siteId, final) {
    const nav = this.map.nav && this.map.nav[siteId];
    if (!nav) return final;
    const ai = b.ai;
    if (!ai.route || ai.routeSite !== siteId) {
      let best = null, bd = 1e9, bi = 0;
      for (const rt of nav) rt.forEach((q, i) => { const d = Math.hypot(q[0] - b.pos[0], q[1] - b.pos[2]) + Math.abs((q[2] ?? b.pos[1]) - b.pos[1]) * 3; if (d < bd) { bd = d; best = rt; bi = i; } });
      ai.route = best; ai.ri = bi; ai.routeSite = siteId;
    }
    const rt = ai.route; // points are [x, z] or [x, z, y] (routes that go down a level)
    while (ai.ri < rt.length && Math.hypot(rt[ai.ri][0] - b.pos[0], rt[ai.ri][1] - b.pos[2]) < 2.6 && Math.abs((rt[ai.ri][2] ?? b.pos[1]) - b.pos[1]) < 2) ai.ri++;
    if (ai.ri >= rt.length) return final;
    return [rt[ai.ri][0], rt[ai.ri][2] ?? b.pos[1], rt[ai.ri][1]];
  }
  botGoal(b) {
    if (this.brOn) return this.brBotGoal(b); // jank royale: zone, heals, loot
    if (this.isEcon()) { const eg = this.econBotGoal(b); if (eg) return eg; }
    const B = this.bomb;
    if (B && this.game === 'bomb' && B.ph !== 'done' && !B.between) {
      const sites = this.map.sites || [];
      const mid = (s) => [(s.min[0] + s.max[0]) / 2, s.min[1], (s.min[2] + s.max[2]) / 2];
      if (b.team === B.att) {
        if (B.carrier === b.id) {
          b.ai.site = b.ai.site && sites.find((x) => x.id === b.ai.site.id) ? b.ai.site : pick(sites);
          if (siteAt(this.map, b.pos)) return { p: b.pos, use: true, r: 99, force: true };
          return { p: this.routeTo(b, b.ai.site.id, mid(b.ai.site)), r: 0, force: true };
        }
        if (B.drop && this.dropChasers().includes(b.id)) {
          return { p: B.dropNode >= 0 ? this.navTo(b, 'drop' + B.chase.key, B.drop, [B.dropNode]) : B.drop, force: true, r: 0 };
        }
        if (B.ph === 'planted') return { p: this.routeTo(b, B.site, B.p), r: 0 }; // guard it
        if (!b.ai.site) b.ai.site = pick(sites);
        return b.ai.site ? { p: this.routeTo(b, b.ai.site.id, mid(b.ai.site)), r: 0 } : null;
      }
      if (B.ph === 'planted') {
        const near = Math.hypot(b.pos[0] - B.p[0], b.pos[2] - B.p[2]) < 8;
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
    if (this.chaosKit && this.botChaosFire(b, t, D)) return;
    if (this.brOn && !this.brBotShot(b)) return; // jank royale: real bullets
    if (this.isEcon() && !this.econBotShot(b, t, D)) return;
    const w = WEAPONS[b.w], n = now();
    if (b.w === 'shredder') { this.botShred(b); return; } // no shots: it sucks for as long as they're in front of it
    if (w.kind === 'beam') { this.botLaser(b); return; } // laser pointer: charge, then let go
    const iv = w.rate ? 1000 / (fireRate(w, b.hp) * (w.hands || 1)) : w.cd * 1000; // Lefty & Righty: both hands going
    if (w.mag) {
      b.ai.ammo--;
      if (b.ai.ammo <= 0) { b.ai.ammo = w.mag; b.ai.reloadUntil = n + w.reload * 1000; }
    }
    b.ai.nextShot = n + iv / D.rate + (w.auto ? 0 : Math.random() * 300);
    this.rifleBotShot(b, w, D); // burst guns: three, then a breath
    const cp = Math.cos(b.pitch);
    let aim = [-Math.sin(b.yaw) * cp, Math.sin(b.pitch), -Math.cos(b.yaw) * cp];
    const o = eyeOf(b);
    if (w.kind === 'hitscan') {
      const hip = (HIPFIRE[this.cfg.hip] || HIPFIRE.normal).mul;
      const pellets = w.pellets || 1;
      const hits = new Map(), segs = [];
      let spr = (w.spread || 0) * Math.max(0.3, hip) + D.err;
      if (this.isEcon()) [aim, spr] = this.tacBotAim(b, w, aim, spr, D); // Plant & Defuse: the spray pattern + moving spread
      for (let i = 0; i < pellets; i++) {
        const d = spreadDir(aim, spr);
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
      this.broadcast({ t: 'fx', k: 'shot', w: b.w, id: b.id, s: segs.slice(0, 12), hd: w.hands && (b.ai.hd = !b.ai.hd) ? 1 : undefined }); // a bot's Lefty & Righty takes turns
      if (w.marbles) this.marblePatch(b, segs.slice(0, 12)); // bots' marbles trip people too
    } else if (w.kind === 'proj') {
      this.spawnProj(b, b.w, o, spreadDir(aim, D.err));
    } else if (w.kind === 'melee') { // zombie claws and the gun game's melee rungs: botThink only gets here in reach
      const d = norm([t.pos[0] - b.pos[0], t.pos[1] - b.pos[1], t.pos[2] - b.pos[2]]) || aim;
      this.broadcast({ t: 'fx', k: 'swing', w: b.w, id: b.id, a: o.map(r2) });
      if (this.parryMelee(b, t)) return; // a katana parry shoves the bot off, like a player's swing
      const vd = w.verdict ? this.verdictOf(b, t) : null; // the scales rung: the court decides how hard it lands
      const hp0 = t.hp, dmg = w.dmg * (vd ? vd.mult : 1);
      this.hurt(t, b, b.w, dmg, [d[0] * w.kb, d[1] * w.kb + (w.kbUp || 0), d[2] * w.kb], { slip: !!w.slip });
      if (vd && t.hp < hp0) this.broadcast({ t: 'fx', k: 'verdict', id: t.id, by: b.id, m: vd.mult, g: vd.g, one: !t.alive && dmg >= 100 ? 1 : 0, p: center(t).map(r2) });
    } else if (w.kind === 'blood') { // the Blood Cross rung: same HP price and cooldown as a player's
      this.fireBlood(b, o, spreadDir(aim, D.err));
    } else if (w.kind === 'bow') { // bots always loose a full draw
      const d = spreadDir(aim, D.err);
      const pr = this.makeProj(b, 'bow', [o[0] + d[0] * 0.7, o[1] + d[1] * 0.7, o[2] + d[2] * 0.7], d.map((x) => x * w.speedMax), { tip: pick(TIP_IDS), charge: 1 });
      pr.born = now();
    } else if (w.kind === 'cards') { // no hand of cards for bots: they just flick single ones
      this.spawnProj(b, 'card', o, spreadDir(aim, D.err));
    }
  }

  stepBot(b, dt) {
    if (this.lassoBot(b)) return; // on the end of a lasso: whoever holds it moves them
    if (b.trap) { this.driftTrapped(b); return; } // in a soap bubble: no thinking, just floating
    if (this.brOn && this.brBotStep(b, dt)) return; // jank royale: riding the blimp, falling, gliding
    if (b.zmz) { this.zmStep(b, dt); return; }
    const n = now();
    const frozen = n < (b.frozenUntil || 0);
    const think = frozen ? { wx: 0, wz: 0, jump: false } : this.botThink(b, dt);
    if (!frozen) this.traffic.botYield(b, think); // look both ways (mostly)
    if (frozen) { b.vel[0] = 0; b.vel[2] = 0; }
    if (b.rig && this.rigOn(b, n)) { this.rigBotStep(b, think, dt, n); return; } // overdrive rig: its own movement + plan (server/rig.js)
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
            const cur = v[0] * think.wx + v[2] * think.wz, add = 8.5 * this.modeSpeed(b) * (b.ai.spd || 1) - cur;
            if (add > 0 && (think.wx || think.wz)) { const a = Math.min(add, 11 * 8.5 * dt); v[0] += a * think.wx; v[2] += a * think.wz; }
          }
        }
      } else if (think.wx || think.wz) {
        const cur = v[0] * think.wx + v[2] * think.wz, add = 1.2 - cur;
        if (add > 0) { const a = Math.min(add, 60 * dt); v[0] += a * think.wx; v[2] += a * think.wz; }
      }
    }
    v[1] -= 26 * dt * (b.gravMul || 1); // (jank royale: Overdraft Heights' low gravity)
    // on the rope: the same classic grapple as a player's (shared/hookphys.js).
    // let go near the point (or when it's been a while) with a grapple jump
    const hk = b.ai && b.ai.hook;
    if (hk) {
      classicRopeStep(hk, hk.point, b.pos, v, dt, 26, this.hookMul); // (spoons & grapples pulls harder)
      b.ropeLift = 1;
      if (hk.dist < 4.5 || n > hk.until || slipping) {
        if (!slipping) classicRopeJump(v); // hook jump
        b.ai.hook = null; b.g = null; b.ai.route = null; // landed somewhere new: plan again from there
      }
      b.onGround = false;
    } else if (b.ropeLift > 0) { // let go: the rope's share of their weight fades out like a player's (no one-step drop)
      b.ropeLift = Math.max(0, b.ropeLift - dt / 0.15);
      v[1] += 26 * ROPE.lift * b.ropeLift * dt;
    }
    this.eatMomentum(b, dt);
    if (b.held && n < b.held.until) { for (let i = 0; i < 3; i++) v[i] = Math.max(-30, Math.min(30, (b.held.at[i] - b.pos[i]) * 9)); b.onGround = false; } // hanging in a shredder
    const was = b.onGround;
    const res = movePlayer(b.pos, v, dt, this.boxes, was);
    b.onGround = !!res.ground && v[1] <= 0.01;
    if (b.onGround && res.ground.pad && !b.ai.dummy) { const pd = res.ground.pad; v[0] += pd[0]; v[1] = pd[1]; v[2] += pd[2]; b.onGround = false; }
    b.f = (slipping ? 16 : 0) | (n < (b.sleepUntil || 0) ? FLAGS.SLEEP : 0); // asleep: everyone sees them lying on the floor
    if (b.onGround) b.ground = b.pos.slice(); // last place they stood (void deaths drop their tag here)
    if (n < (b.suckUntil || 0)) b.f |= FLAGS.SUCK; // shredder running: clients draw the suction
    if (b.pos[1] < this.map.killY) this.kill(b, null, 'void');
    else if (this.map.shredders && inShredder(this.map, b.pos)) { b.pitT = now(); this.kill(b, null, 'void'); } // into the pit's teeth
  }

  // ---------------------------------------------------------- items (G): charges refill over time
  // one item per loadout (p.item, set with 'itemsel'); its charges are per life and the server's count is the real one.
  // has() = Object.hasOwn: '__proto__' / 'constructor' never become an item
  itemCharges(p) {
    if (this.brOn && p.br) return this.brIc(p); // jank royale: picked up, never recharges
    const it = ITEMS[p.item] || ITEMS.frag;
    if (!p.ic || p.ic.i !== p.item) p.ic = { i: p.item, n: it.charges, next: 0 };
    const c = p.ic, n = now();
    while (c.n < it.charges && c.next && n >= c.next) { c.n++; c.next = c.n < it.charges ? c.next + it.recharge * 1000 : 0; }
    return c;
  }
  icInfo(p) { const c = this.itemCharges(p); return { i: p.item, n: c.n, next: c.next ? c.next - now() : 0 }; }
  sendIc(p) { if (!p.isBot && !(this.brOn && p.br && !(p.br.gadget && p.br.gadget.n > 0))) send(p, { t: 'ic', ...this.icInfo(p) }); } // (jank royale: nothing to say without a gadget)
  // your loadout item changed: right away while dead or in the first 5 s of a life, otherwise from your next life
  // (the client's applyLoadout rule; its 5 s start when 'spawn' reaches it, so allow one round trip more)
  selectItem(p, id) {
    if (!has(ITEMS, id)) return;
    if (id === p.item) p.nextItem = null;
    else if (!p.alive || now() - p.spawnT < 5000 + Math.min(1000, (p.ws && p.ws.rtt) || 250)) {
      // what you already used this life stays used: swapping doesn't hand out fresh charges
      const used = ITEMS[p.item].charges - this.itemCharges(p).n, it = ITEMS[id];
      p.item = id; p.nextItem = null;
      p.ic = { i: id, n: Math.max(0, it.charges - used), next: used > 0 ? now() + it.recharge * 1000 : 0 };
    } else p.nextItem = id;
    this.sendIc(p);
  }
  useItem(p, m) {
    if (this.rigOn(p)) { this.sendIc(p); return; } // no items in the overdrive rig
    if (!p.alive || !has(ITEMS, m.i)) return;
    if (this.gearItem(p, m)) return; // instant camera snap (free), goggles flash without goggles on
    const c = this.itemCharges(p);
    // not your item, no charge left, too fast, or a mode with no items (gun game, zombies, the chaos kits): tell the
    // client the real count so its HUD can't drift
    if (m.i !== p.item || c.n <= 0 || now() - (p.itemT || 0) < 400 || this.modeWeapon(p) || (this.chaosKit && this.chaosKit.noItem)) { this.sendIc(p); return; }
    const it = ITEMS[p.item];
    p.itemT = now();
    c.n--;
    if (!c.next) c.next = now() + it.recharge * 1000;
    this.sendIc(p);
    let o = vec3(m.o);
    if (!o || dist3(o, eyeOf(p)) > 4) o = eyeOf(p);
    const d = norm(vec3(m.d)) || [0, 0, -1];
    if (m.i === 'wand') { this.blowWand(p, o, d); return; }
    if (this.gearUse(p, m, o, d)) return; // print a photo, throw a pop quiz, goggles flash
    if (it.proj) {
      const w = WEAPONS[it.proj];
      const pr = this.makeProj(p, it.proj, [o[0] + d[0] * 0.7, o[1] + d[1] * 0.7, o[2] + d[2] * 0.7],
        [d[0] * w.speed + p.vel[0] * 0.35, d[1] * w.speed + 3 + p.vel[1] * 0.35, d[2] * w.speed + p.vel[2] * 0.35]);
      pr.born = now();
    } else if (p.item === 'medkit') {
      p.healLeft = it.heal;
      this.broadcast({ t: 'fx', k: 'medkit', id: p.id });
    } else if (p.item === 'bubble') {
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
  // a bubble protects whoever is inside from anyone outside it. damage with no attacker (the bomb) passes from: where it came from
  bubbleBlocks(attacker, t, from) {
    if (attacker === t || !this.bubbles.size || (!attacker && !from)) return false;
    for (const b of this.bubbles.values()) {
      if (!this.inBubble(b, t)) continue;
      if (attacker ? !this.inBubble(b, attacker) : Math.hypot(from[0] - b.p[0], from[1] - b.p[1], from[2] - b.p[2]) >= b.r) return true;
    }
    return false;
  }
  // snowballs: frost builds up, enough of it freezes you, a snowball to a frozen target shatters them.
  // only call it for a snowball that really landed (hurt() returned the target)
  frost(t, owner) {
    const w = WEAPONS.snowball, n = now();
    t.frost = Math.max(0, (t.frost || 0) - Math.floor((n - (t.frostT || 0)) / (w.frostDecay * 1000))) + 1;
    t.frostT = n;
    if (t.frost >= w.freezeAt) {
      t.frost = 0;
      t.frozenUntil = n + w.freeze * 1000;
      t.vel[0] = 0; t.vel[2] = 0;
      t.g = null; if (t.ai) t.ai.hook = null; // ice doesn't swing on a rope
      this.broadcast({ t: 'freeze', id: t.id, dur: w.freeze * 1000 });
    } else this.broadcast({ t: 'frost', id: t.id, n: t.frost });
  }
  tickItems(dt) {
    const n = now();
    for (const b of [...this.bubbles.values()]) if (n >= b.until) { this.bubbles.delete(b.id); this.broadcast({ t: 'bubx', id: b.id }); }
    for (const s of [...this.smokes.values()]) if (n >= s.until) this.smokes.delete(s.id);
    for (const p of this.players.values()) {
      if (p.healLeft > 0 && p.alive) { const a = Math.min(p.healLeft, 26 * dt); p.healLeft -= a; if (p.hp < 100) p.hp = Math.min(100, p.hp + a); } // never eats overheal
      if (!p.isBot && p.ic && p.ic.next && n >= p.ic.next) this.sendIc(p); // a charge came back
    }
  }

  // ---------------------------------------------------------- bubble wand: soap bubbles that seal people in a giant one
  // G blows a short stream of slow wobbly bubbles: server projectiles on the exact path in shared/wand.js
  blowWand(p, o, d) {
    const it = ITEMS.wand, w = WEAPONS.soap, ey = eyeOf(p);
    const od = [o[0] - ey[0], o[1] - ey[1], o[2] - ey[2]], ol = Math.hypot(...od);
    if (ol > 1e-3 && raycast(ey, od.map((x) => x / ol), ol, this.boxes)) o = ey; // no blowing from the far side of a wall
    const off = [o[0] - p.pos[0], o[1] - p.pos[1] - 0.15, o[2] - p.pos[2]]; // the wand is at your mouth, a bit under your eyes
    for (let i = 0; i < it.bubbles; i++) setTimeout(safe('wand', () => {
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
    }), i * it.gap);
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
    if (this.rigOn(t, n)) return false; // so does a 3 m overdrive rig
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
    if (t.ai) { t.ai.hook = null; t.ai.route = null; } // floated off its lane: plans again from wherever it drops
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
    if (this.lassoHeld(p)) { p.trap.at = p.pos.slice(); p.trap.atT = now(); return; } // lassoed: the bubble swings with them
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
    else if (this.map.shredders && inShredder(this.map, b.pos)) { b.pitT = now(); this.kill(b, null, 'void'); }
  }

  // ---------------------------------------------------------- combat
  tag(t, attacker, w) {
    if (!attacker || attacker === t) return;
    t.lastAttacker = attacker.id; t.lastAttackW = w; t.lastAttackT = now();
  }
  knock(t, v, w) {
    if (this.rigOn(t)) v = this.rigShrug(v); // the overdrive rig shrugs it off
    if (Math.hypot(v[0], v[1], v[2]) >= 1) t.knockT = now(); // EPIC anti-farm: getting shoved around isn't moving (0-knockback bullets don't count)
    if (t.isBot) {
      if (t.ai.dummy && t.ai.dummy.move) return;
      t.vel[0] += v[0]; t.vel[1] += v[1]; t.vel[2] += v[2];
      if (v[1] > 0.5 && t.onGround) { t.onGround = false; t.pos[1] += 0.02; }
      if (Math.hypot(v[0], v[2]) > 12) t.ai.route = null; // knocked off the lane: plan again from wherever it lands
      return;
    }
    send(t, { t: 'kb', v: v.map(r2), w });
  }
  slip(t, k) {
    if (this.rigOn(t)) return; // a rig doesn't slip on peels (or marbles)
    t.knockT = now(); // sliding on a banana isn't moving either
    if (t.isBot) { t.slipUntil = now() + 1700; t.vel[1] = Math.max(t.vel[1], 6.5); t.onGround = false; return; }
    send(t, k ? { t: 'slip', k } : { t: 'slip' }); // k: what you slipped on (the client says MARBLES! for marbles)
  }
  friendly(a, b) {
    if (!a || !b || a === b) return false;
    if (this.mode === 'coop') return a.isBot === b.isBot;
    if (this.zm) return a.isBot === b.isBot; // zombies: everyone vs the zombies
    if (GAMES[this.game].infect) return !!a.inf === !!b.inf; // infection: survivors vs zombies, no hurting your own side
    return this.teamsOn() && a.team && a.team === b.team;
  }
  // the rules every hit follows: true = it doesn't land
  hitBlocked(t, attacker, w, from) {
    if (!t.alive) return true;
    if (this.round && this.round.over && w !== 'void') return true;
    if (attacker && attacker !== t && now() - t.spawnT < 1200 && !t.isBot) return true; // spawn protection
    if (attacker && attacker !== t && this.invulnerable(t)) return true; // sitting a pop quiz, or the few seconds after acing one
    return !!this.friendly(attacker, t) || this.bubbleBlocks(attacker, t, from);
  }
  // returns true when the damage was applied
  damage(t, amt, attacker, w, hs, from) {
    if (amt <= 0 || !t.alive) return false;
    if (t.trap) return false; // sealed in a soap bubble: burning, gas and the like can't get in (a real hit pops it, see hurt)
    if (this.hitBlocked(t, attacker, w, from)) return false;
    if (this.zm) amt = this.zmDamage(t, amt, attacker); // credits for hits, claws, the cola
    if (attacker && attacker.isBot && !t.isBot && this.mode !== 'bots') amt *= 0.6; // coop bots hit softer
    if (t.rig) { amt = this.rigSoak(t, amt, attacker, w, from); if (amt <= 0) return true; } // overdrive rig: block + overshield first
    if (this.isEcon()) amt = this.econArmor(t, amt, attacker, w, hs);
    if (this.brOn) { amt = this.brDamage(t, amt, attacker, w); if (amt <= 0) return false; } // loot tiers + armour
    t.hp -= amt;
    if (!attacker || attacker === t) t.selfHurtT = now(); // EPIC: coughing yourself down to 4 HP doesn't make you a clutch hero
    t.lastHs = !!hs;
    if (hs && attacker && attacker !== t && attacker.acct && this.mode !== 'training') stat(attacker, 'headshots', 1);
    this.tag(t, attacker, w);
    this.broadcast({ t: 'dmg', to: t.id, from: attacker ? attacker.id : 0, a: Math.round(Math.min(amt, 999)), w, hs: !!hs, ko: t.hp <= 0 ? 1 : undefined }); // ko: this hit kills (heavier headshot sounds)
    if (t.hp <= 0) this.kill(t, attacker, w);
    return true;
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
    if (this.rigOn(t)) return; // the overdrive rig doesn't nap (the arrow still hurt)
    t.sleepUntil = now() + secs * 1000;
    if (t.isBot) { if (t.ai) t.ai.hook = null; t.g = null; return; } // knocked flat: lets go of the rope too (snapshots show FLAGS.SLEEP)
    send(t, { t: 'sleep', dur: secs }); // players send FLAGS.SLEEP themselves while it lasts
  }
  makeCloud(p, owner) {
    const c = { id: this.nextCloud++, p: p.map(r2), o: owner, born: now(), tick: 0 };
    this.clouds.set(c.id, c);
    this.broadcast({ t: 'cloud', id: c.id, p: c.p });
  }
  // out of the play area (map.bounds): OOB.secs to get back, then a void death. the client counts it down on its own
  oobCheck(t, n) {
    if (this.brOn) return false; // jank royale: the zone is the edge of the map
    if (!this.map.bounds || t.trap || (t.isBot && t.ai.dummy)) return false;
    if (!outOfBounds(this.map, t.pos)) { t.oobAt = 0; return false; }
    if (!t.oobAt) { t.oobAt = n; return false; }
    if (n - t.oobAt < (OOB.secs + OOB.grace) * 1000) return false;
    this.kill(t, null, 'void');
    return true;
  }
  tickStatus(dt) {
    const n = now();
    for (const t of this.players.values()) {
      if (!t.alive) continue;
      if (t.hp > 100 && !t.inf && !t.zmz) t.hp = Math.max(100, t.hp - 2 * dt); // overheal fades (zombie HP doesn't)
      if (this.oobCheck(t, n)) continue;
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
      if (!owner) continue; // whoever made it left: it's just fog now
      for (const t of this.players.values()) {
        if (!t.alive || t.id === c.o || this.friendly(owner, t)) continue;
        if (dist3(center(t), c.p) < 5.5) this.damage(t, 4, owner, 'bow');
      }
    }
  }

  // everything that hurts or shoves a player goes through here so reverse cards work on all of it.
  // returns whoever actually took the damage (the attacker when it bounced off a reverse card), or null
  // opts: hs (headshot), slip, lethal (at least their hp: a player's sniper headshot), from (where ownerless damage came from)
  hurt(t, attacker, w, dmg, kb, opts = {}) {
    if (!t || !t.alive) return null;
    if (t.trap && !this.bubbleBlocks(attacker, t, opts.from) && this.popTrap(t, 'hit', attacker, w)) return null; // in a soap bubble: the first hit (teammates' too) only pops it
    if (this.friendly(attacker, t)) return null;
    if (this.bubbleBlocks(attacker, t, opts.from)) { this.broadcast({ t: 'fx', k: 'bubhit', p: center(t).map(r2) }); return null; }
    if (opts.lethal) dmg = Math.max(dmg, t.hp); // sized for whoever was shot: a reverse card bounces that same hit
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
    return this.damage(t, dmg, attacker, w, opts.hs, opts.from) ? t : null;
  }
  kill(t, attacker, w) {
    if (!t.alive) return;
    if (t.trap) this.popTrap(t, 'dead');
    this.lassoDrop(t, 'dead'); // a rope they held (or hung off) drops
    t.alive = false; t.hp = 0; t.deaths++; t.g = null; t.reverseUntil = 0; t.oobAt = 0;
    this.rigDeath(t); // (every client bursts the frame open from the kill message)
    if (t.ai) { t.ai.hook = null; t.ai.route = null; } // a fresh route from the spawn, not the old waypoint index
    // the mode's respawn delay; skipping the killcam ('respawn') can't go below it
    t.respawnAt = t.minRespawnAt = now() + (t.isBot && t.ai.dummy ? 700 : this.game === 'bomb' && this.teamsOn() ? BOMB.respawn : 2500);
    t.deadT = now();
    let killer = attacker, via = null;
    if (w === 'void' || w === 'cough' || ((w === 'car' || w === 'carboom') && !attacker)) { // knocked into traffic counts like the void
      killer = null;
      if (t.lastAttacker && now() - t.lastAttackT < 10000 && this.players.has(t.lastAttacker)) {
        killer = this.players.get(t.lastAttacker); via = t.lastAttackW;
      }
    }
    // sky ducks and lava belong to nobody: whoever hurt you in the last few seconds gets it, else it's on you
    if (!killer && (w === 'duck' || w === 'lava') && t.lastAttacker && now() - t.lastAttackT < 6000 && this.players.has(t.lastAttacker)) { killer = this.players.get(t.lastAttacker); via = t.lastAttackW; }
    if (killer && killer !== t && this.teamsOn() && killer.team !== t.team && this.round && !this.round.over) {
      if (this.game === 'tdm') this.score[killer.team]++;
      if (this.game === 'tags') this.dropTag(t, killer);
    }
    if (this.bomb && this.bomb.carrier === t.id) this.dropBomb(t.pos, t);
    if (killer && killer !== t && (w === 'katana' || w === 'parry')) { // the katana grows with every kill (parries too)
      killer.kat = Math.min(WEAPONS.katana.growMax, (killer.kat || 0) + 1);
      this.broadcast({ t: 'kat', id: killer.id, n: killer.kat });
    }
    if (t.kat) { t.kat = 0; this.broadcast({ t: 'kat', id: t.id, n: 0 }); }
    if (killer && killer !== t) {
      killer.kills++;
      killer.streak = (killer.streak || 0) + 1;
      if (this.round && !this.round.over) matchKill(this, killer, t, via || w);
      if (killer.lastKiller === t.id) killer.lastKiller = 0; // revenge served (scales of justice)
      t.lastKiller = killer.id;
      if (this.zm) killer.streak = 0; // zombies: no killstreaks
      if (!killer.isBot && this.mode !== 'training' && !this.zm && !this.modeWeapon(killer) && !(this.chaosKit && this.chaosKit.noStreaks) && this.streaksOn() && !this.brOn && !this.warm) { // no killstreaks in zombies, gun game, as a zombie or in a chaos kit
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
      // bots have no tray, but the overdrive rig is theirs to earn too (they suit up right away)
      if (killer.isBot && this.mode !== 'training' && !this.modeWeapon(killer) && !(this.chaosKit && this.chaosKit.noStreaks) && killer.streak === STREAKS.overdrive.kills) this.rigBotEarn(killer);
    }
    // killcam: humans who have it on wait for it to finish (or skip it) before respawning
    if (!t.isBot && t.kc && killer && killer !== t && this.mode !== 'training') t.respawnAt = Math.max(t.respawnAt, now() + 9000);
    // EPIC kill: the victim (if they have killcams on) has to watch all of it. their respawn waits it out, never past the 9 s cap
    const ep = this.epicOf(killer, t, w, via);
    t.lastEpic = ep;
    t.epicLock = ep && !t.isBot && t.kc ? Math.min(t.respawnAt, now() + epicCamMs()) : 0;
    if (t.epicLock) ep.lock = 1;
    if (this.warm) { t.respawnAt = t.minRespawnAt = now() + LOBBY.respawn; t.epicLock = 0; if (ep) ep.lock = 0; } // a lobby's warm-up: straight back in
    if (this.zm) this.zmKilled(t, killer, w); // credits for zombie kills, players go down instead of respawning
    if (killer && killer !== t && this.round && !this.round.over && !(t.isBot && t.ai && t.ai.dummy) && this.mode !== 'training') this.hlCandidate(killer, t, w);
    send(t, { t: 'streak', reset: 1 });
    t.streak = 0;
    if (t.nextStreaks) { t.streaks = t.nextStreaks; t.nextStreaks = null; } // picks changed mid-streak count from this life on
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
    this.broadcast({ t: 'kill', k: killer && killer !== t ? killer.id : 0, v: t.id, w, via, vel: t.vel.map(r2), pos: t.pos.map(r2), yaw: r2(t.yaw || 0), fx: kfx, ep: ep || undefined, rs: Math.max(0, t.minRespawnAt - now()), sky: w === 'duck' && now() - (t.skyT || 0) < 800 ? 1 : undefined, pit: w === 'void' && now() - (t.pitT || 0) < 500 ? 1 : undefined }); // (pit: the shredder pit's teeth)
    t.lastAttacker = 0;
    this.chaosKill(t, killer);
    if (t.isBot && this.mode === 'coop') { setTimeout(safe('coop', () => { if (this.players.get(t.id) === t) this.remove(t); }), 50); }
    this.modeKill(t, killer, via || w);
    if (this.brOn) this.brKill(t, killer, w);
    if (this.isEcon()) this.econOnKill(t, killer, w, via);
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
      : w === 'void' ? 'INTO THE VOID' : w === 'car' ? 'ROADKILL' : w === 'carboom' ? 'CAR BOMB' : spd > 300 ? `${Math.round(spd)} KM/H KILL` : dist > 60 ? `${Math.round(dist)}M SHOT` : t.lastHs ? 'HEADSHOT' : 'NICE KILL';
    const t0 = Math.max(k.killLog[0] - 3200, n - 8000);
    const hl = { score, pending: true };
    r.hl = hl;
    // grab the clip a moment later so it includes the aftermath
    setTimeout(safe('clip', () => {
      if (this.round !== r || r.hl !== hl) return;
      Object.assign(hl, { pending: false, label, id: k.id, name: k.name, color: k.color, card: k.card || '', clip: this.clip(t0, now()) });
    }), 1300);
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
  // from the snapshots: when everyone last really moved (a respawn or getting knocked around doesn't count) and where
  // they were over the last 0.6 s (how fast they're really going). one tracker for both anti-farm rules: EPIC kills
  // read movedT (EPIC.moved metres), Sniper Royalty reads royalMovedT (ROYAL.moved metres; the same as long as the
  // two thresholds agree, its own anchor when they don't)
  trackMoves(n) {
    const gate = (p, at, t, metres) => {
      if (!p[at]) p[t] = n; // just joined
      if (!p[at] || !p.trail || dist3(p[at], p.pos) > metres) {
        if (p[at] && p.trail && n - (p.knockT || 0) > 1200) p[t] = n;
        p[at] = p.pos.slice();
      }
    };
    for (const p of this.players.values()) {
      if (!p.alive) { p.trail = null; continue; }
      if (p.trackSeq !== p.seq) { p.trackSeq = p.seq; p.trail = null; } // respawned or put back at a spawn (round start): that jump isn't moving
      gate(p, 'stillAt', 'movedT', EPIC.moved);
      if (ROYAL.moved === EPIC.moved) p.royalMovedT = p.movedT; else gate(p, 'royalAt', 'royalMovedT', ROYAL.moved);
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
    ev.unshift(...this.framePreroll(this.rec.ev, t0)); // photo frames already standing (and the photos in them)
    ev.unshift(...patchPreroll(this.rec.ev, t0)); // marbles already on the floor
    const had = new Set(ev.map((e) => e.m.t === 'mpatch' && e.m.id)); // still down from before the recording kept: from the live patch
    for (const pt of this.mpatches.values()) if (pt.born < t0 && !had.has(pt.id) && pt.until - t0 > 300) ev.unshift({ s: t0, m: { t: 'mpatch', ...this.patchInfo(pt), left: pt.until - t0 } });
    ev.unshift(...lassoPreroll(this.rec.ev, t0)); // or already hanging off a lasso
    const info = {};
    for (const f of frames) for (const e of f.p) if (!info[e[0]]) {
      const pl = this.players.get(e[0]);
      if (pl) info[e[0]] = { name: pl.name, color: pl.color, skins: pl.skins, bot: pl.isBot, look: pl.look, level: pl.level, grap: pl.grap || 'rope' };
    }
    if (GAMES[this.game].infect) for (const id of Object.keys(info)) { const pl = this.players.get(Number(id)); if (pl && pl.inf) info[id].zs = pl.infT || 1; } // replays draw zombies as zombies
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
  revolverHit(p, t, fan, w) {
    if (!this.rangeOk(p, t, w.range)) return 0;
    const n = now(), f = w.fanHammer, tapMs = 1000 / w.rate, fanMs = 1000 / f.rate;
    let c = p.revCyl;
    if (!c || c.t < p.spawnT) c = p.revCyl = { t: -1e9, n: 0, tap: 0, fan: 0 }; // respawned with a full cylinder
    if (n < c.fan - fanMs * 0.4) return 0;
    if (n - c.t >= w.reload * 750) c.n = 0; // long enough to have reloaded
    if (c.n >= w.mag && this.mode !== 'training') return 0; // training = infinite ammo
    const tap = !fan && n >= c.tap - tapMs * 0.4;
    c.fan = Math.max(c.fan, n) + fanMs;
    c.tap = tap ? Math.max(c.tap, n) + tapMs : Math.max(c.tap, n + tapMs);
    c.t = n; c.n++;
    return tap ? 1 : f.dmg / w.dmg;
  }

  applyHitscan(p, t, wid, n, h, d, mul = 1) {
    if (this.isBall(t)) h = 0; // a wrecking ball has no head
    if (this.parryShot(p, t, wid, n, h, d, mul)) return; // katana parry: blocked, or sent back
    const w = WEAPONS[wid], pellets = w.pellets || 1;
    const rx = this.rifleShot(p, t, wid, h); // rifle pack: bursts, the lever ramp, quick-scopes
    if (!rx) return;
    const dmg = (w.dmg * (n - h) + w.dmg * (w.head || 1) * h) * mul * rx.mul + rx.add;
    const k = w.kb * n + rx.kb;
    // a sniper headshot from a player always kills (bots keep their softer shots)
    this.hurt(t, p, wid, dmg, [d[0] * k, d[1] * k + (w.kbUp || 0) * (n / pellets), d[2] * k], { hs: h > 0, lethal: wid === 'sniper' && h > 0 && !p.isBot });
    if (wid === 'nailgun') this.nailHit(p, t, n, d); // enough nails in a row pin them to the wall (server/primaries.js)
  }

  // scales of justice: how guilty t is next to p, from what the server knows right now (formula in shared/verdict.js)
  verdictOf(p, t) {
    let teams = null;
    if (this.teamsOn() && p.team && t.team) { const sc = this.game === 'bomb' && this.bomb ? this.bomb.wins : this.score; teams = [sc[p.team] || 0, sc[t.team] || 0]; }
    return verdict(p, t, { board: this.fighters(), teams, revenge: !!p.lastKiller && p.lastKiller === t.id, npc: (this.mode === 'coop' && t.isBot) || !!(t.ai && t.ai.dummy) });
  }

  onHit(p, m) {
    if (this.rigOn(p)) return; // no guns in the overdrive rig: its hits are judged in server/rig.js
    if (!this.chaosHit(p, m)) return; // chaos kits: only their weapons; one in the chamber's bullet
    const w = has(WEAPONS, m.w) && WEAPONS[m.w];
    const t = this.players.get(m.to);
    const d = norm(vec3(m.d));
    if (!w || !t || !d || t === p || !t.alive || !p.alive) return;
    if (this.isBall(p)) return; // no hands in the wrecking ball
    if (now() < (p.staggerUntil || 0)) return; // got parried: still reeling
    if (!this.allowed(p, m.w)) return; // gun game rung / zombie claw only
    if (this.zm && !this.zmArm(p, m.w)) return; // zombies: only what you bought, while it has ammo
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
      // the shot's flags (ns: no-scope, qs: quick-scope, fan: fanned revolver) are 1 or absent, anything else is absent
      const fan = m.fan === 1, ns = m.ns === 1, qs = m.qs === 1;
      if (w.fanHammer) { const mul = this.revolverHit(p, t, fan, w); if (mul) this.applyHitscan(p, t, m.w, n, h, d, mul); return; } // tap or fan the hammer
      const hd = w.hands && m.hd === 1 ? 'L' : ''; // Lefty & Righty: each gun has its own schedule (claiming the other hand buys at most the pair's real rate)
      if (!this.pairOk(p, t, 'hs' + m.w + hd, (1000 / fireRate(w, p.hp)) * 0.6) || !this.rangeOk(p, t, w.range)) return; // the Redline fires faster as you lose HP
      p.nsHit = m.w === 'sniper' && p.w === 'sniper' && ns; // a no-scope (ns: 1) can make the kill EPIC
      const hp0 = t.hp; // no-scope hype only goes out if the shot really landed
      p.qsHit = !!w.quick && qs; // Second Opinion quick-scope (server/rifles.js caps what it buys)
      this.applyHitscan(p, t, m.w, n, h, d);
      p.nsHit = false; p.qsHit = false;
      if (ns && m.w === 'sniper') this.noScope(p, t, h > 0, hp0);
      if (m.w === 'sniper' && !t.alive) this.royalKill(p, t, ns, qs, h > 0); // this shot killed them (a parried / reflected one hurts you, not them)
    } else if (w.kind === 'melee') {
      const hv = m.heavy === 1 && w.heavy ? w.heavy : null; // knife right click (the flag is 1 or absent)
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

  // Sniper Royalty: the boxes a sniper kill ticks. qs / ns are the shooter's word, so they only ever buy progress, never
  // damage: the kill is the server's, the distance comes from server positions, and a victim who hadn't moved for 5 s
  // (AFK, a friend standing still) never counts. no training (dummies) and no bots doing the shooting
  royalKill(p, t, ns, qs, hs) {
    if (p.isBot || this.mode === 'training' || (t.isBot && t.ai && t.ai.dummy)) return;
    const n = now();
    if (n - (t.royalMovedT ?? n) >= ROYAL.still) return; // epic's tracker (trackMoves), Royalty's own thresholds
    // a quick-scope or a no-scope ticks the trick-shot box. scoped and unscoped at once is a lie: that doesn't count
    const bits = (dist3(p.pos, t.pos) >= ROYAL.long ? RB.long : 0) | (qs !== ns ? RB.trick : 0) | (hs ? RB.head : 0);
    if (bits) royal(p, bits);
  }

  onPush(p, m) {
    if (this.rigOn(p) || (m.w === 'hook' && p.hackedUntil > now())) return; // no grapple in the rig; a hacked one is fried
    if (m.w !== 'hook' && this.chaosKit && !this.chaosKit.slots.includes(m.w)) return;
    const t = this.players.get(m.to);
    if (!t || t === p || !t.alive || !p.alive) return;
    if (this.isBall(p) || now() < (p.staggerUntil || 0)) return; // no hands in the wrecking ball; parried = still reeling (like 'hit')
    if (m.w !== 'hook' && !this.allowed(p, m.w)) return; // the grapple always works; otherwise gun game rung / zombie claw only
    if (this.zm && m.w === 'blower' && !this.zmArm(p, 'blower')) return;
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
    t.ai.hook = null; t.g = null; t.ai.route = null; // no grappling out of it; plans its route again once it's spat out
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
      // a player's sniper headshot stays lethal on the way back (it's the same bullet); bots' stay soft
      this.hurt(p, t, 'parry', dmg, k || up ? [-d[0] * k, -d[1] * k + up, -d[2] * k] : null, { hs: h > 0, lethal: wid === 'sniper' && h > 0 && !p.isBot });
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
    if (this.rigOn(p)) return; // no guns in the overdrive rig
    const w = has(WEAPONS, m.w) && WEAPONS[m.w];
    if (!w || !p.alive || this.isBall(p)) return; // no hands in the wrecking ball
    if (!this.allowed(p, m.w)) return; // gun game rung / zombie claw only
    if (this.zm && !this.zmArm(p, m.w)) return; // zombies: only what you bought, while it has ammo
    if (!this.chaosFire(p, m)) return; // chaos kits: only their weapons; one in the chamber's bullet
    // loadout weapons only (plus the scythe once earned, and the one weapon a mode hands you: the zombie claw): items
    // (frag, smoke, duck, popper, reverse card) come from G, grenades and thrown cards from the deck, never 'fire'
    if (!SLOTS.includes(w.slot) && !(w.slot === 'streak' && p.scythe) && this.modeWeapon(p) !== m.w) return;
    if (w.kind === 'beam') { this.laserFire(p, m); return; } // laser pointer: 'ch' starts the charge, the release fires what we timed
    let o = vec3(m.o);
    if (!o || dist3(o, eyeOf(p)) > 4) o = eyeOf(p);
    const fan = !!(w.fanHammer && m.fan === 1); // revolver: fanning the hammer (validated like every flag: 1 or nothing)
    // shot / swing effects are only relayed, but each goes to everyone: at most ~4x the weapon's rate (frames can bunch up).
    // one limiter per player, not per weapon: you hold one gun at a time, and cycling ids must not add the rates up.
    // the rate is the real one: the Redline speeds up as you lose HP, a fanned revolver goes at the fan rate
    if (w.kind === 'hitscan' || w.kind === 'melee') {
      const rate = w.rate ? (fan ? Math.max(w.rate, w.fanHammer.rate) : fireRate(w, p.hp) * (w.hands || 1)) : 0; // Lefty & Righty: both hands
      const n = now(), iv = rate ? 250 / rate : (w.cd || 0.3) * 250;
      if (n - (p.lastFire.fx || 0) < iv) return;
      p.lastFire.fx = n;
    }
    if (w.marbles && p.w === m.w) this.marblePatch(p, segs(m.s)); // marbles on the floor (the server works out where)
    if (w.kind === 'hitscan') { this.broadcast({ t: 'fx', k: 'shot', w: m.w, id: p.id, s: segs(m.s), fan: fan ? 1 : undefined, hd: w.hands && m.hd === 1 ? 1 : undefined }, p.id); return; } // fan: everyone sees the fanning spin; hd: the left of Lefty & Righty
    if (w.kind === 'melee') { this.broadcast({ t: 'fx', k: 'swing', w: m.w, id: p.id, a: o.map(r2), h: m.heavy === 1 ? 1 : undefined }, p.id); return; }
    const d = norm(vec3(m.d));
    if (d && w.kind === 'proj') this.spawnProj(p, m.w, o, d);
    if (d && w.kind === 'blood') this.fireBlood(p, o, d);
    if (d && w.kind === 'bow') {
      const n = now();
      if (n - (p.lastFire.bow || 0) < w.cd * 750) return;
      p.lastFire.bow = n;
      const c = Math.max(0.15, Math.min(1, num(m.c) || 0));
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
    if (!p.hand.length) setTimeout(safe('deal', () => { if (this.players.get(p.id) === p) deal(p); }), 1500);
  }

  spawnProj(p, wid, o, d) {
    if (wid === 'cart') { this.fireCart(p, o, d); return; } // shopping carts aren't projectiles: they park and stay (server/primaries.js)
    const w = WEAPONS[wid], n = now();
    if (!(w.cd > 0) || n - (p.lastFire[wid] || 0) < w.cd * 750) return; // nothing without a cooldown comes through here
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
    pr.ef = p.pos ? this.epicState(p) : null; // EPIC: where (and how) they fired it from (a sky duck has nobody)
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
    const shielded = this.bubbleBlocks(owner, t); // the bubble stops the arrow's fire and sleep too, not just its damage
    if (tip === 'flame') { dmg = 15; if (!shielded) this.burn(t, owner, 3); }
    if (tip === 'gas') dmg = 10;
    if (tip === 'sleep') { dmg = 10; if (!shielded) this.sleep(t, owner, this.isEcon() ? TAC.sleep : SLEEP_TIME); } // Plant & Defuse: a short nap (a free kill otherwise)
    const head = pr.p[1] > t.pos[1] + 1.55;
    this.hurt(t, owner, 'bow', dmg * (head ? 1.5 : 1), kb, { hs: head });
  }
  explodeAt(p, owner, wid, R, dmg, kb) {
    this.broadcast({ t: 'boom', p: p.map(r2), r: R });
    this.traffic.blast(p, R, dmg, kb, owner);
    for (const t of this.players.values()) {
      if (!t.alive) continue;
      const c = center(t), to = [c[0] - p[0], c[1] - p[1], c[2] - p[2]], dist = Math.hypot(...to);
      if (dist > R) continue;
      const f = 1 - dist / R, dir = dist > 0.1 ? to.map((x) => x / dist) : [0, 1, 0];
      const self = owner && t.id === owner.id;
      const k = kb * (0.4 + 0.6 * f);
      this.hurt(t, self ? null : owner, wid, self ? 0 : dmg * (0.3 + 0.7 * f), [dir[0] * k, dir[1] * k + 6 * f, dir[2] * k], { from: owner ? null : p });
    }
  }

  explode(pr) {
    const w = WEAPONS.chicken;
    const owner = this.players.get(pr.o);
    this.broadcast({ t: 'pd', id: pr.id, p: pr.p.map(r2), x: 1 });
    this.traffic.blast(pr.p, w.radius, w.dmg, w.kb, owner);
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

  // ---------------------------------------------------------- Blood Cross: paid in HP, the bolt sticks, a cross bursts out of them, they pop
  // cross events go to everyone and into the recording, so killcams + the play of the round show the mark, the spikes and the pop
  crossCast(m) { this.broadcast(m); this.rec.ev.push({ s: now(), m }); }
  fireBlood(p, o, d) {
    const w = WEAPONS.bloodcross, n = now();
    if (this.round && this.round.over) return; // nothing can be hurt between rounds, so don't charge blood for it
    if (n - (p.lastFire.bloodcross || 0) < w.cd * 750) return;
    p.lastFire.bloodcross = n; // a refused shot uses the cooldown up too, so spamming it costs the server nothing
    if (p.hp - w.cost < 1) { send(p, { t: 'bcross', k: 'dry', o: p.id }); return; } // it never takes your last HP, so it can't kill you
    p.hp -= w.cost;
    p.selfHurtT = n; // EPIC: bleeding yourself down to low HP doesn't make you a clutch hero (like coughing)
    if (this.mode === 'training') p.bcPaid = (p.bcPaid || 0) + w.cost; // training hands it back once you stop
    const wallHit = raycast(o, d, 0.8, this.boxes);
    const off = wallHit ? Math.max(0, wallHit.t - w.r - 0.05) : 0.8;
    const pr = {
      id: this.nextProj++, k: 'bloodcross', o: p.id, r: w.r, bounce: 0, born: n, phase: 0, hit: new Map(), sync: 0, cost: w.cost,
      p: [o[0] + d[0] * off, o[1] + d[1] * off, o[2] + d[2] * off], v: d.map((x) => x * w.speed), // no gravity, no inherited speed: it goes where you point
    };
    this.projectiles.set(pr.id, pr);
    this.broadcast({ t: 'ps', id: pr.id, k: pr.k, p: pr.p.map(r2), v: pr.v.map(r2), o: p.id });
  }
  tickBloodBolt(pr, dt, n) {
    const w = WEAPONS.bloodcross, owner = this.players.get(pr.o), prev = pr.p.slice();
    const hit = stepProjectile(pr, dt, this.boxes, 0);
    // a katana parry bats it back like any projectile: the parrier owns it now (and didn't pay blood for it)
    if (this.parryProj(pr, prev)) { pr.cost = 0; return; }
    // only up to the wall, so nobody gets hit through it. a shooter who left can't tell friend from foe: it only finds walls then
    const vs = owner ? this.sweep(prev, pr.p, pr.r, (t) => t.id === pr.o || this.friendly(owner, t)) : [];
    if (vs.length) { pr.p = vs[0].at; this.removeProj(pr); this.stickCross(pr, vs[0].t); return; }
    if (hit) { // walls + floors: a red X that fizzles out, no damage
      const nrm = [0, 0, 0]; nrm[hit.axis] = hit.sign;
      this.removeProj(pr);
      this.crossCast({ t: 'bcross', k: 'wall', id: pr.id, o: pr.o, p: pr.p.map(r2), n: nrm });
      return;
    }
    if ((n - pr.born) / 1000 > w.life || pr.p[1] < this.map.killY) this.removeProj(pr);
  }
  // the mark lives in the target's own frame (turned by their yaw), so it turns and moves with them
  crossAt(t, off) {
    const c = Math.cos(t.yaw || 0), s = Math.sin(t.yaw || 0);
    return [t.pos[0] + (off[0] * c + off[2] * s) * 0.15, t.pos[1] + off[1], t.pos[2] + (off[2] * c - off[0] * s) * 0.15];
  }
  stickCross(pr, t) {
    const w = WEAPONS.bloodcross;
    let dx = pr.p[0] - t.pos[0], dz = pr.p[2] - t.pos[2], l = Math.hypot(dx, dz);
    if (l < 0.05) { dx = -pr.v[0]; dz = -pr.v[2]; l = Math.hypot(dx, dz) || 1; } // dropped straight onto their head: face where it came from
    dx /= l; dz /= l;
    const c = Math.cos(t.yaw || 0), s = Math.sin(t.yaw || 0);
    // which side it hit (unit, body-local) + how high: shins count as hips so the cross never ends up in the floor
    const off = [r2(dx * c - dz * s), r2(Math.max(0.9, Math.min(2.15, pr.p[1] - t.pos[1]))), r2(dx * s + dz * c)];
    const mk = { id: pr.id, o: pr.o, t: t.id, seq: t.seq, off, d: norm(pr.v) || [0, 0, -1], at: now() + w.fuse * 1000, ph: 0, cost: pr.cost ?? w.cost };
    mk.p = this.crossAt(t, off);
    (this.crosses ||= new Map()).set(mk.id, mk);
    this.crossCast({ t: 'bcross', k: 'stick', id: mk.id, o: mk.o, to: t.id, off, p: mk.p.map(r2), f: w.fuse });
  }
  tickCrosses() {
    const n = now(), w = WEAPONS.bloodcross;
    if (this.mode === 'training') { // infinite ammo there: the blood you spent comes back 2s after your last shot
      for (const p of this.players.values()) {
        if (!p.bcPaid || n - (p.lastFire.bloodcross || 0) < 2000) continue;
        const a = p.alive ? Math.min(p.bcPaid, 100 - p.hp) : 0;
        if (a > 0) { p.hp += a; send(p, { t: 'bcross', k: 'refill', o: p.id, a: Math.round(a) }); }
        p.bcPaid = 0;
      }
    }
    if (!this.crosses || !this.crosses.size) return;
    for (const mk of this.crosses.values()) {
      const t = this.players.get(mk.t), on = !!(t && t.alive && t.seq === mk.seq);
      if (on) mk.p = this.crossAt(t, mk.off); // died or respawned: it stays where they were
      if (mk.ph === 0 && n >= mk.at) { mk.ph = 1; this.crossCast({ t: 'bcross', k: 'erupt', id: mk.id, o: mk.o, to: mk.t, p: mk.p.map(r2) }); }
      else if (mk.ph === 1 && n >= mk.at + w.burst * 1000) { this.crosses.delete(mk.id); this.blowCross(mk, on ? t : null); }
    }
  }
  blowCross(mk, t) {
    const w = WEAPONS.bloodcross, owner = this.players.get(mk.o) || null, p = mk.p;
    this.crossCast({ t: 'bcross', k: 'boom', id: mk.id, o: mk.o, to: mk.t, p: p.map(r2) });
    // the shooter left before the pop: everyone still sees it, but with no attacker the team, spawn and bubble checks
    // can't work (it would hit their old team), so it does no damage
    if (!owner) return;
    let kills = 0;
    // never a headshot: it's a fixed delayed pop wherever it stuck, so it stays out of the headshot stats + highlights
    const pop = (v, dmg, kb) => { const was = v.alive; this.hurt(v, owner, 'bloodcross', dmg, kb); if (was && !v.alive) kills++; };
    if (t) pop(t, w.dmg, [mk.d[0] * w.kb, 4, mk.d[2] * w.kb]);
    for (const v of [...this.players.values()]) { // the small blast: everyone else close by, not you (teammates are skipped by hurt)
      if (v === t || v === owner || !v.alive) continue;
      const c = center(v), to = [c[0] - p[0], c[1] - p[1], c[2] - p[2]], dist = Math.hypot(...to);
      if (dist > w.blastR) continue;
      const f = 1 - dist / w.blastR, dir = dist > 0.1 ? to.map((x) => x / dist) : [0, 1, 0];
      pop(v, w.blastDmg * f, [dir[0] * w.kb * 1.5 * f, 3 + 3 * f, dir[2] * w.kb * 1.5 * f]);
    }
    if (kills && owner.alive) { // blood magic: a kill pays back what the shot cost (never past full)
      const a = Math.max(0, Math.min(mk.cost, Math.max(100, owner.hp) - owner.hp));
      owner.hp += a;
      this.crossCast({ t: 'bcross', k: 'refund', id: mk.id, o: owner.id, a: Math.round(a), p: p.map(r2) });
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
      if (pr.k === 'rigmissile') { this.rigMissileStep(pr, dt); continue; } // overdrive rig missiles home in (server/rig.js)
      const age = (n - pr.born) / 1000;
      if (pr.k === 'bloodcross') { this.tickBloodBolt(pr, dt, n); continue; }
      if (pr.k === 'tennis') { this.tennisStep(pr, dt, n); continue; } // counted bounces (server/primaries.js)
      const owner = this.players.get(pr.o);
      const prev = pr.p.slice();
      let hit = null;
      if (pr.k === 'soap') { this.stepSoap(pr, n, owner, prev, dt); continue; }
      if (pr.k === 'loop') { this.stepLoop(pr, n, owner, prev, dt); continue; } // lasso loops (server/lasso.js)
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
      if (pr.k !== 'duck' && pr.k !== 'frag' && pr.k !== 'smokegren' && pr.k !== 'slipper' && this.traffic.projHit(pr, prev, owner)) continue; // hit a car
      if (this.parryProj(pr, prev)) continue; // batted back by a katana parry
      if (pr.k === 'duck') {
        // sky ducks (duck rain) open where they land, and their holes are a bit gentler
        if (pr.sky ? !!hit || age > 8 : age >= w.fuse) { this.removeProj(pr); const h = this.makeHole(pr.p, pr.o); if (pr.sky) Object.assign(h, DUCKRAIN.hole, { sky: true }); continue; }
      } else if (pr.k === 'frag' || pr.k === 'smokegren') {
        if (age >= w.fuse) {
          this.removeProj(pr);
          if (pr.k === 'frag') this.explodeAt(pr.p, owner, 'frag', w.radius, w.dmg, w.kb);
          else {
            const sm = { id: this.nextSmoke++, p: pr.p.map(r2), r: ITEMS.smoke.r, until: n + ITEMS.smoke.dur * 1000 };
            this.smokes.set(sm.id, sm);
            this.broadcast({ t: 'smoke', p: sm.p, r: sm.r, dur: ITEMS.smoke.dur * 1000 });
          }
          continue;
        }
      } else {
        const ownerImmune = pr.k === 'slipper' ? Infinity : pr.k === 'bowling' ? 0.5 : 0.25;
        const victims = this.sweep(prev, pr.p, pr.r, (t) => (t.id === pr.o && age < ownerImmune) || (pr.hit.has(t.id) && n - pr.hit.get(t.id) < 700) || (this.friendly(owner, t) && !t.trap));
        if (victims.length) {
          if (pr.k === 'calc') { this.calcHit(pr, owner, victims[0]); continue; } // pop quiz: freeze them with a question
          if (pr.k === 'chicken') { pr.p = victims[0].at; this.projectiles.delete(pr.id); this.explode(pr); continue; }
          if (pr.k === 'snowball') {
            const v = victims[0];
            pr.p = v.at;
            this.removeProj(pr, { b: 1 });
            if (v.t.id === pr.o) continue;
            const d = norm(pr.v) || [0, 0, 1];
            if (v.t.trap) { this.hurt(v.t, owner, 'snowball', 0, null); continue; } // a soap bubble takes it (teammates' too): pop, no frost
            if (v.t.frozenUntil > n) { // frozen: this one shatters them, if a hit could land at all (and no reverse card)
              if (v.t.reverseUntil > n || this.hitBlocked(v.t, owner, 'snowball')) continue;
              v.t.frozenUntil = 0;
              this.broadcast({ t: 'fx', k: 'shatter', id: v.t.id, p: center(v.t).map(r2) });
              this.kill(v.t, owner, 'snowball');
            } else if (this.hurt(v.t, owner, 'snowball', w.dmg, [d[0] * w.kb, w.kbUp, d[2] * w.kb]) === v.t && v.t.alive) this.frost(v.t, owner);
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
        if (!owner && !h.sky) continue; // whoever threw it left: it pops harmlessly (a sky duck's hole is nobody's: it works)
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
          if (h.sky) t.skyT = n; // so the kill feed can tell a sky duck from a thrown one
          this.hurt(t, self ? null : owner, 'duck', self ? 0 : h.blastDmg * f, [dir[0] * k, dir[1] * k + 8 * f, dir[2] * k], { from: owner ? null : h.p });
        }
        continue;
      }
      h.tick -= dt;
      if (h.tick > 0) continue;
      h.tick = 0.1;
      if (!owner && !h.sky) continue;
      for (const t of this.players.values()) {
        if (!t.alive || this.friendly(owner, t) || (h.big && t.id === h.o) || this.bubbleBlocks(owner, t, owner ? null : h.p)) continue; // no pulling people out of a bubble
        if (t.id === h.on) { if (h.sky) t.skyT = n; this.damage(t, w.stuckDmg, owner, 'duck'); continue; } // the one it's stuck to IS the middle
        const c = center(t);
        const to = [h.p[0] - c[0], h.p[1] - c[1], h.p[2] - c[2]];
        const dist = Math.hypot(...to);
        if (dist > h.R || dist < 0.05) continue;
        const s = (h.pull * (1 - dist / h.R) + 8) * 0.1 * Math.min(1, dist / 1.5);
        // plus a little lift each pulse: off their feet, ground friction can't hold them back (a duck stuck on someone at floor height pulls sideways)
        if (h.sky) t.skyT = n;
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
    if (!owner && !pr.sky) return false; // a thrower who left: it just flies
    const w = WEAPONS.duck;
    // a sky duck (duck rain) belongs to nobody: it sticks to whoever it lands on, and a shield bubble stops it from outside
    const skip = owner ? (t) => t.id === pr.o || this.friendly(owner, t) || this.bubbleBlocks(owner, t) : (t) => this.bubbleBlocks(null, t, pr.p);
    let stuck = pr.lp ? this.sweep(pr.lp, pr.p, pr.r + 0.1, skip)[0] : null;
    if (!stuck) for (const t of this.players.values()) { // sat still inside someone (sweep needs movement)
      if (!t.alive || skip(t)) continue;
      if (playerBoxes(t.pos).some((b) => b.min.every((m, i) => pr.p[i] > m - pr.r) && b.max.every((m, i) => pr.p[i] < m + pr.r))) { stuck = { t, at: pr.p.slice() }; break; }
    }
    if (stuck) {
      pr.p = stuck.at;
      this.removeProj(pr);
      const h = this.makeHole(center(stuck.t), pr.o, { on: stuck.t.id, delay: w.stick });
      if (pr.sky) { Object.assign(h, DUCKRAIN.hole, { sky: true }); stuck.t.skyT = now(); } // a sky duck's hole, riding them
      this.tag(stuck.t, owner, 'duck');
      return true;
    }
    pr.lp = pr.p.slice();
    if (pr.sky) return false; // duck rain falls straight down (no homing, so you can dodge it); only a thrown duck homes in
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
  // a bot in the air: does the flight come down on a floor if nobody steers? (a floor near the height it left from)
  botFlightLands(b) {
    const v = b.vel, g = 26 * (b.gravMul || 1), y0 = (b.ground ? b.ground[1] : b.pos[1]) - 1, h = b.pos[1] - y0;
    if (h <= 0 || !Number.isFinite(h)) return false;
    const t = (v[1] + Math.sqrt(v[1] * v[1] + 2 * g * h)) / g;
    return !!raycast([b.pos[0] + v[0] * t, y0 + 3, b.pos[2] + v[2] * t], [0, -1, 0], 8, this.boxes);
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

  // ---------------------------------------------------------- marbles on the floor (Marble Shotgun)
  // a marble shot leaves a patch where its marbles settle, and anyone who runs over it slips. where: from the shooter's
  // eye (a position the server tracks) along the pellet directions, with the server's own raycasts to what they hit
  // and down to the floor. the client's pellet ends only pick the directions and how far (capped at the gun's range).
  marblePatch(p, ss) {
    const M = MSLIP, w = WEAPONS.marbles, n = now();
    if (!p.alive || p.trap || this.isBall(p, n) || !Array.isArray(ss) || !ss.length) return;
    if (n - (p.mpT || 0) < M.cd * 1000) return; // one patch per real shot, however many fire messages come in
    p.mpT = n;
    const e = eyeOf(p), pts = [];
    for (const s of ss) {
      const d = norm([s[3] - e[0], s[4] - e[1], s[5] - e[2]]);
      if (!d) continue;
      const L = Math.min(w.range, Math.hypot(s[3] - e[0], s[4] - e[1], s[5] - e[2]));
      const h = raycast(e, d, L, this.boxes);
      // hit the map: drop off that surface. stopped short of it (a player) or flew the whole way: drop from there
      const a = h ? h.point.map((x, k) => x + h.normal[k] * 0.1 - d[k] * 0.05) : e.map((x, k) => x + d[k] * L);
      const f = raycast(a, [0, -1, 0], 40, this.boxes);
      if (f && f.normal[1] === 1) pts.push([a[0], a[1] - f.t, a[2]]); // (nothing below = it fell into the void)
    }
    // the biggest bunch that landed together on one floor
    let best = [];
    for (const a of pts) {
      const c = pts.filter((b) => Math.abs(b[1] - a[1]) < 0.5 && Math.hypot(b[0] - a[0], b[2] - a[2]) < 2.5);
      if (c.length > best.length) best = c;
    }
    if (best.length < Math.max(3, ss.length * 0.3)) return; // sprayed all over (or into the sky): no patch
    let cx = 0, cz = 0;
    for (const b of best) { cx += b[0] / best.length; cz += b[2] / best.length; }
    const top = Math.max(...best.map((b) => b[1]));
    let f = raycast([cx, top + 0.4, cz], [0, -1, 0], 1.4, this.boxes);
    if (!f || f.normal[1] !== 1) { // the middle is in a pillar the marbles landed round (or over a gap): use the nearest marble
      const b = best.reduce((m, b) => (Math.hypot(b[0] - cx, b[2] - cz) < Math.hypot(m[0] - cx, m[2] - cz) ? b : m));
      cx = b[0]; cz = b[2]; f = raycast([cx, top + 0.4, cz], [0, -1, 0], 1.4, this.boxes);
      if (!f || f.normal[1] !== 1) return;
    }
    const y = top + 0.4 - f.t;
    const rms = Math.sqrt(best.reduce((s, b) => s + (b[0] - cx) ** 2 + (b[2] - cz) ** 2, 0) / best.length);
    const r = Math.max(M.rMin, Math.min(M.rMax, 0.9 + rms * 1.3));
    const pt = { // (more marbles in a bigger patch so it doesn't read as a few specks)
      id: this.nextMp++, c: [r2(cx), r2(y), r2(cz)], r: r2(r),
      n: Math.round(M.n * Math.min(1, (best.length / ss.length) * 1.4) * Math.max(0.7, Math.min(1.6, (r / 1.6) ** 2))), o: p.id, team: p.team || 0,
      born: n, until: n + M.life * 1000, map: this.cfg.map,
    };
    // caps: your oldest goes first, then the room's oldest
    const mine = [...this.mpatches.values()].filter((q) => q.o === p.id);
    while (mine.length >= M.per) this.dropPatch(mine.shift());
    while (this.mpatches.size >= M.room) this.dropPatch(this.mpatches.values().next().value);
    this.mpatches.set(pt.id, pt);
    this.broadcast({ t: 'mpatch', ...this.patchInfo(pt) });
  }
  patchInfo(pt) { return { id: pt.id, c: pt.c, r: pt.r, n: pt.n, o: pt.o, left: Math.max(0, pt.until - now()) }; }
  patchList() { return [...this.mpatches.values()].filter((pt) => pt.map === this.cfg.map).map((pt) => this.patchInfo(pt)); }
  dropPatch(pt) { if (this.mpatches.delete(pt.id)) this.broadcast({ t: 'mpx', id: pt.id }); }
  tickMarbles() {
    if (!this.mpatches.size) return;
    const n = now();
    for (const pt of [...this.mpatches.values()]) {
      if (n > pt.until || pt.map !== this.cfg.map) { this.dropPatch(pt); continue; }
      if (n - pt.born < MSLIP.land * 1000) continue; // still flying
      const owner = this.players.get(pt.o) || null;
      for (const t of this.players.values()) {
        if (!this.slipsOn(t, pt, owner, n)) continue;
        this.marbleSlip(t, pt, owner, n);
        if (!this.mpatches.has(pt.id)) break;
      }
    }
  }
  // who slips: anyone on it going faster than a careful walk (the shooter too, it's a janky game). not teammates
  // (like the banana), a wrecking ball, a soap bubble, frozen or dead people, or someone who just slipped
  slipsOn(t, pt, owner, n) {
    if (!t.alive || t.trap || this.isBall(t, n) || n < (t.frozenUntil || 0) || n - (t.mslipT || 0) < MSLIP.immune) return false;
    if (owner ? owner !== t && this.friendly(owner, t) : this.teamsOn() && pt.team && pt.team === t.team) return false; // (the shooter left: their team is still safe)
    if (!t.isBot && owner !== t && n - t.spawnT < 1200) return false; // spawn protection
    if (t.isBot && owner === t && n - pt.born < 1500) return false; // a bot's marbles at its own feet: a moment to stop strafing
    if (t.isBot ? n < t.slipUntil || !t.onGround || (t.ai.dummy && t.ai.dummy.move) : (t.f & FLAGS.SLIP) || Math.abs(t.vel[1]) > 2) return false; // (players: no vertical speed = on the floor)
    if (!onPatch(pt, t.pos, 0.15) || this.marbleSpeed(t, n) <= this.marbleWalk(t)) return false;
    const dx = t.pos[0] - pt.c[0], dz = t.pos[2] - pt.c[2], l = Math.hypot(dx, dz);
    return !(l > 0.05 && raycast([pt.c[0], pt.c[1] + 0.3, pt.c[2]], [dx / l, 0, dz / l], l, this.boxes)); // a wall between you and the marbles
  }
  // how fast you're going over the marbles: what you say, or what the snapshots saw over the last 0.3 s if that's more
  // (so a client can't run across claiming it stands still). a jump of over 1.5 m between snapshots is a teleport, not running
  marbleSpeed(t, n) {
    const v = Math.hypot(t.vel[0], t.vel[2]), tr = t.trail;
    if (t.isBot || !tr || tr.length < 2) return v;
    let d = 0, t0 = 0;
    for (let i = 1; i < tr.length; i++) {
      if (tr[i][0] < n - 300) continue;
      t0 ||= tr[i - 1][0];
      const s = Math.hypot(tr[i][1] - tr[i - 1][1], tr[i][3] - tr[i - 1][3]);
      if (s < 1.5) d += s;
    }
    const dt = t0 ? (tr[tr.length - 1][0] - t0) / 1000 : 0;
    return dt < 0.15 ? v : Math.max(v, (d / dt) * 0.8); // (-20% for network jitter)
  }
  // a crouch walk is safe with any weapon out (a fast weapon crouch-walks faster), up to where crouching turns into a slide
  marbleWalk(t) { return Math.min(MSLIP.slide, Math.max(MSLIP.walk, MSLIP.crouch * ((WEAPONS[t.w] || {}).speedMul || 1) + 1)); }
  marbleSlip(t, pt, owner, n) {
    const M = MSLIP;
    t.mslipT = n;
    this.slip(t, 'marbles');
    if (t.isBot) { const hs = Math.hypot(t.vel[0], t.vel[2]) || 1; t.vel[0] += (t.vel[0] / hs) * 4; t.vel[2] += (t.vel[2] / hs) * 4; } // feet out the way they were going
    if (owner && owner !== t) this.tag(t, owner, 'marbles'); // slip off a ledge = the shooter's kill
    pt.n = Math.floor(pt.n * M.thin); pt.r = r2(Math.max(M.minR, pt.r * M.thinR)); // the marbles scatter: thinner every time
    this.broadcast({ t: 'mslip', id: pt.id, by: t.id, n: pt.n, r: pt.r, p: t.pos.map(r2) });
    if (pt.n < M.minN) this.dropPatch(pt);
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
      store.get(p.acct.n).then((u) => { if (u) p.inv = u.inv || {}; if (this.players.get(p.id) === p) this.onSpray(p, m, true); }).catch((e) => logErr('spray', e));
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
    if (this.lobby) return; // a mode lobby is everyone's: no one person changes its map, mode or bots
    const n = now();
    if (n - p.cfgT < 1500) return;
    p.cfgT = n;
    // zombie maps only go with zombies: in the Bots room picking one switches the mode (and leaving it ends zombies);
    // the Online room only gets zombies from the vote
    if (m.map && MAPS[m.map] && !MAPS[m.map].zm !== !GAMES[this.game].zombies) { if (this.mode === 'bots') m.game = MAPS[m.map].zm ? 'zm' : 'dm'; else m.map = null; }
    const changes = [];
    const pickMap = has(MAPS, m.map) && MAP_ORDER.includes(m.map) ? mapForGame(this.game, MAPS, m.map) : null; // the version this mode plays
    if (pickMap && pickMap !== this.cfg.map && this.mode !== 'training') {
      this.cfg.map = pickMap;
      changes.push(`map → ${MAPS[pickMap].name}`);
      this.smokes.clear(); // clients drop theirs with the old map
      let fresh = false;
      if (GAMES[this.game].sites && !(this.map.sites && this.map.sites.length)) {
        this.game = 'dm'; this.bomb = null; changes.push('mode → Deathmatch (no bomb sites here)');
        // a new deathmatch round (the bomb round's clock and kills don't carry over). during the vote the vote decides
        if (this.round && !this.round.over) fresh = true; else this.assignTeams();
      }
      if (GAMES[this.game].mapOk && !GAMES[this.game].mapOk(this.map)) { changes.push(`mode → Deathmatch (no ${GAMES[this.game].name} on this map)`); this.game = 'dm'; this.assignTeams(); }
      if (fresh) this.startRound();
      else if (this.round && this.round.over) this.resetWorld(); // the end screen is up: respawn on the new map, the vote still picks what's next
      else if (this.bomb) this.newBombRound(true);
      else if (this.livesOn) { this.vote = null; setTimeout(safe('startRound', () => this.startRound()), 50); } // lives can't be patched mid-match
      else this.resetWorld();
    }
    if (has(HIPFIRE, m.hip) && m.hip !== this.cfg.hip) { this.cfg.hip = m.hip; changes.push(`hipfire → ${HIPFIRE[m.hip].name}`); }
    if (has(GAMES, m.game) && m.game !== this.game && this.mode === 'bots' && this.setGame(m.game)) { changes.push(`mode → ${GAMES[m.game].name}`); this.vote = null; if (this.round) { this.round.over = true; this.round.next = now() + 1000; } setTimeout(safe('startRound', () => this.startRound()), 50); } // over: tickRound mustn't judge the old round by the new mode's rules
    if (has(BOT_DIFF, m.diff) && m.diff !== this.cfg.diff && this.mode !== 'ffa') {
      this.cfg.diff = m.diff;
      for (const b of this.players.values()) if (b.isBot) b.ai.diff = m.diff;
      changes.push(`bots → ${BOT_DIFF[m.diff].name}`);
    }
    if (has(HR.every, m.hr) && m.hr !== this.cfg.hr) { this.cfg.hr = m.hr; changes.push(`the tall guy from HR → ${HR.names[m.hr]}`); }
    if (m.bots != null && this.mode === 'bots') {
      const c = clampInt(m.bots, 0, 12);
      if (c !== this.cfg.bots) { this.cfg.bots = c; this.fillBots(); changes.push(`bot count → ${c}`); }
    }
    this.traffic.setCfg(m, changes);
    if (!changes.length) return;
    this.broadcast({ t: 'cfg', cfg: this.cfg, by: p.id });
    if (this.mode === 'ffa' || this.mode === 'coop') this.broadcast({ t: 'chat', id: 0, m: `${p.name} set ${changes.join(', ')}` });
  }

  // per-life state: cleared on every respawn and on every new round / match / map
  resetLife(p) {
    p.slipUntil = 0; p.burnUntil = 0; p.burnBy = 0; p.burnTick = 0; p.sleepUntil = 0; p.frozenUntil = 0; p.frost = 0; p.frostT = 0; p.pinUntil = 0; p.nails = null; p.held = null;
    p.healLeft = 0; p.reverseUntil = 0; p.g = null; p.lastAttacker = 0; p.ground = null;
    this.rigReset(p); // a new round ends the overdrive rig (and any hack)
    if (p.lz) { this.lassoCut(p, 'gone'); p.lz.fl = null; } // a fresh life: off any rope, no flight still counting
    if (p.ai) { p.ai.hook = null; p.ai.route = null; }
    p.parryT = 0; p.staggerUntil = 0; // katana parry: a new life starts with the guard ready (the client resets too)
    p.ballUntil = 0; p.f &= ~FLAGS.BALL; // a wrecking ball doesn't roll into the next round (or the next mode)
    p.lavaBurn = 0; p.lavaSeen = 0; // floor is lava: the burn ends with the life
    this.gearReset(p); // photo, goggles, laser charge, quiz
    if (!p.isBot) { if (p.nextItem) { p.item = p.nextItem; p.nextItem = null; } p.ic = null; } // full charges (sendIc after 'spawn')
  }
  resetWorld() {
    this.resetChaos();
    this.gearWorldReset(); // photo frames come down
    this.projectiles.clear(); this.peels.clear(); this.holes.clear(); this.clearCarts();
    this.mpatches.clear(); // clients wipe theirs on 'clear'
    this.broadcast({ t: 'clear' });
    this.clearTags();
    for (const b of this.bubbles.values()) this.broadcast({ t: 'bubx', id: b.id });
    for (const c of this.clouds.values()) this.broadcast({ t: 'cloudx', id: c.id });
    this.bubbles.clear(); this.clouds.clear();
    for (const p of this.players.values()) {
      if ((p.isBot && p.ai.dummy) || p.watch) continue;
      p.alive = true; p.hp = 100; p.vel = [0, 0, 0]; p.spawnT = now(); p.seq++;
      p.parryT = 0; p.staggerUntil = 0; // katana parry: the client resets on 'spawn', so the server does too
      p.pos = this.pickSpawn(p.isBot, p);
      this.resetLife(p);
      send(p, { t: 'spawn', p: p.pos, q: p.seq });
      this.sendIc(p);
      this.sendLoadout(p);
    }
    if (this.mode === 'training') { this.removeBots(); this.spawnDummies(); }
    if (this.crosses) this.crosses.clear();
  }

  // hidden NPCs + cats (shared/secrets.js). the client opens the chat / pets straight away; this decides whether it
  // counts: alive, on that map, really next to it, not mid Plant & Defuse, and once per account (gifts too)
  onSecret(p, m) {
    const id = m.id;
    if (typeof id !== 'string' || !Object.hasOwn(SECRETS, id)) return;
    const t = now();
    if (t - (p.secT || 0) < SECRET.cd) return; // rate limit
    p.secT = t;
    const s = SECRETS[id], no = (why) => send(p, { t: 'sec', id, no: why });
    if (s.map !== this.cfg.map) return no('map');
    if (secretsOff(this.game) || this.isEcon()) return no('bomb');
    if (!p.alive || p.isBot) return no('dead');
    if (!canReach(p.pos, id, 0.4)) return no('far'); // (a little slack: you were next to it when you pressed F)
    this.broadcast({ t: 'secfx', id, by: p.id }, p.id); // everyone else sees the cat purr / the NPC turn round
    if (!p.acct) return send(p, { t: 'sec', id, guest: 1 });
    if (p.acct.lore.has(id)) return send(p, { t: 'sec', id, again: 1 });
    p.acct.lore.add(id);
    let gift = s.gift || null;
    if (gift && gift.type && owns(p.inv, gift.type, gift.id)) gift = gift.or || null; // already had it: the fallback
    if (gift) gift = gift.type ? { type: gift.type, id: gift.id } : { roll: gift.roll };
    if (gift && gift.type) (p.inv[gift.type] ||= []).push(gift.id); // yours from now (kill effect / grapple pickers check p.inv)
    store.addLore(p.acct.n, id, gift).catch((e) => logErr('lore', e));
    if (s.kind === 'cat') { p.acct.base.cats = (p.acct.base.cats || 0) + 1; checkAch(p); } // the 5th pet unlocks Board Approved
    send(p, { t: 'sec', id, first: 1, gift, lore: [...p.acct.lore] });
  }
  handle(p, m) {
    if (p.quiz && ['fire', 'hit', 'push', 'item', 'deploy', 'tbag', 'use', 'parry', 'spray'].includes(m.t)) return; // pens down: no attacks during a pop quiz
    if (p.trap && ['fire', 'hit', 'push', 'item', 'deploy', 'tbag', 'use', 'parry', 'spray'].includes(m.t)) return; // sealed in a soap bubble: no attacks, parries, items, streaks, sprays or planting till it pops
    if (this.brOn && this.brHandle(p, m)) return; // jank royale: the blimp, loot, heals; only guns you carry, with bullets left
    if (this.isEcon() && this.econHandle(p, m)) return;
    if ((m.t === 'fire' || m.t === 'hit') && this.lassoHolding(p)) return; // both hands are on the lasso
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
        if (has(WEAPONS, m.w) && (!this.chaosKit || this.chaosKit.slots.includes(m.w))) p.w = m.w;
        const only = this.modeWeapon(p);
        if (only) p.w = only; // everyone sees what you're really allowed to hold
        p.g = vec3(m.g);
        p.f = num(m.f) | 0;
        this.lassoSnap(p); // on the end of a lasso: the rope has you, not your client (and no grapple). spinning one: noted
        if (raycast([pos[0], pos[1] + 0.3, pos[2]], [0, -1, 0], 0.6, this.boxes)) p.ground = pos.slice(); // standing on something
        this.rigSnap(p); // the rig flags only count from someone who activated it; no rope in the rig or when hacked
        if (p.trap) this.holdTrapped(p, true); // sealed in a soap bubble: you go where it floats
        if (p.pos[1] < this.map.killY) this.kill(p, null, 'void');
        else if (this.map.shredders && inShredder(this.map, p.pos)) { p.pitT = now(); this.kill(p, null, 'void'); } // the shredder pit's teeth
        if ((p.f & FLAGS.BALL) && !(p.ballUntil > now())) p.f &= ~FLAGS.BALL; // only someone who earned the wrecking ball gets to be one
        if (p.ballUntil > now()) this.ballAir(p);
        this.gearSnap(p); // goggles / laser flags only if the server agrees; pop quiz holds you in place
        break;
      }
      case 'hit': this.onHit(p, m); break;
      case 'car': this.traffic.onHit(p, m); break; // shot / bonked a car
      case 'push': this.onPush(p, m); break;
      case 'slam': this.onSlam(p, m); break;
      case 'fire': this.onFire(p, m); break;
      case 'cart': this.onCart(p, m); break; // hop in / out of a shopping cart
      case 'cough':
        if (p.alive && now() - p.coughT > 800) {
          p.coughT = now();
          const cp = Math.cos(p.pitch || 0); // everyone else sees the smoke burst out of your face, and you double over
          this.broadcast({ t: 'fx', k: 'cough', id: p.id, p: eyeOf(p).map(r2), d: [-Math.sin(p.yaw || 0) * cp, Math.sin(p.pitch || 0), -Math.cos(p.yaw || 0) * cp].map(r2) }, p.id);
          this.damage(p, 12, null, 'cough');
        }
        break;
      case 'chat': {
        const text = typeof m.m === 'string' ? clean(m.m, 120) : '';
        if (text && isSkipCmd(text)) { skipCommand(this, p); break; } // /skip: a vote to skip this match (server/skip.js), never shown as chat
        if (text && now() - p.chatT > 400) { p.chatT = now(); this.broadcast({ t: 'chat', id: p.id, m: text }); }
        break;
      }
      case 'sec': this.onSecret(p, m); break; // F next to a hidden NPC or cat
      case 'tbag': { // crouch-spammed too hard: your knees explode
        if (this.chaosKit && this.chaosKit.noTbag) break; // one in the chamber: a free area kill that also burns a life
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
      case 'streaks': { // with a streak going the new picks wait for your next life (no swapping picks mid-streak)
        const v = validStreaks(m.list);
        if (p.streak) p.nextStreaks = v; else { p.streaks = v; p.nextStreaks = null; }
        break;
      }
      case 'deploy': { // use a killstreak from your tray (aimed ones land where you looked)
        if (this.chaosKit && this.chaosKit.noStreaks) break;
        if (this.zm) break; // zombies: no killstreaks, not even ones carried over
        const i = (p.pocket || []).indexOf(m.r);
        const at = vec3(m.at);
        if (i < 0 || !p.alive || !has(STREAKS, m.r)) break;
        if (this.modeWeapon(p)) break; // no killstreaks in gun game or as a zombie (they keep for later)
        if ((m.r === 'chickenstrike' || m.r === 'giantduck') && !at) break;
        if (rigClash(m.r, this.rigOn(p), this.isBall(p) || p.ballUntil > now())) break; // overdrive rig vs other body streaks: it keeps in the tray
        p.pocket.splice(i, 1);
        if (m.r === 'overdrive') this.rigStart(p);
        if (this.mode === 'training') (p.trainCd ||= {})[m.r] = now() + ((STREAKS[m.r].dur || 0) + 3) * 1000;
        (p.usedAt ||= {})[m.r] = now(); // EPIC kills skip the spinbot's (aimbot) and the chicken strike's
        if (m.r === 'scythe') p.scythe = true;
        if (m.r === 'wreckingball') { p.ballUntil = now() + STREAKS.wreckingball.dur * 1000 + 1000; p.slamT = 0; p.ballTop = p.pos[1]; p.ballVy = 0; } // +1s for lag
        send(p, { t: 'streak', reward: m.r, dur: STREAKS[m.r].dur });
        if (m.r === 'chickenstrike') {
          this.broadcast({ t: 'fx', k: 'strikeCall', id: p.id, p: at.map(r2) });
          for (let k = 0; k < 14; k++) setTimeout(safe('strike', () => {
            if (!this.players.has(p.id)) return;
            const a = Math.random() * Math.PI * 2, rr = Math.random() * 10;
            this.makeProj(p, 'chicken', [at[0] + Math.cos(a) * rr, at[1] + 45, at[2] + Math.sin(a) * rr], [0, -34, 0]);
          }), 600 + k * 170);
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
        // in team games you stay in your team's colour (no dressing up as the other team); your pick shows again after
        p.color = this.teamsOn() && p.team ? TEAMS[p.team].color : p.look.color || p.color;
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
      case 'kfx': // kill effect: quick clicks batch into one inventory read (like 'grap'), the last pick wins
        p.kfxWant = typeof m.id === 'string' ? m.id : '';
        if (!p.kfxQ) p.kfxQ = setTimeout(() => {
          (async () => {
            if (p.acct) { const u = await store.get(p.acct.n).catch(() => null); if (u) p.inv = u.inv || {}; }
            p.kfx = ownedKill(p.kfxWant, p.inv);
          })().catch((e) => logErr('kfx', e)).finally(() => { p.kfxQ = null; });
        }, 250);
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
      case 'lava': this.lavaTouch(p, true); break; // floor is lava: "ouch, I touched it"
      case 'item': this.useItem(p, m); break;
      case 'ans': this.onAnswer(p, m); break; // pop quiz answer (0-3)
      case 'nv': this.onNv(p, m); break; // night vision goggles on / off
      case 'spray': this.onSpray(p, m); break;
      case 'itemsel': this.selectItem(p, m.i); break;
      case 'ready': if (this.warm) this.onReady(p, m); break; // mode lobby: READY (everyone ready = 5 s)
      case 'vote': { // a vote is for the stage that's open now (s, when sent, must match it). one that comes too soon after
        // the last is kept and counted once the 250 ms are up, so the card you see marked is always the one that counts
        const v = this.vote;
        if (!v || v.stage === 'done' || !Number.isInteger(m.i) || m.i < 0 || m.i >= v.options.length || (m.s != null && m.s !== v.stage)) break;
        if (now() - (p.voteT || 0) > 250) this.castVote(p, m.i); else p.votePend = { i: m.i, stage: v.stage };
        break;
      }
      case 'respawn': // killcam finished or skipped: respawn now, but never sooner than the mode allows
        if (this.zm) break; // zombies: you wait for a revive or the next round
        if (this.livesOn && p.oitc && p.oitc.out) break; // out of lives: you watch
        if (!p.alive) p.respawnAt = Math.min(p.respawnAt, Math.max(now(), p.minRespawnAt || 0));
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
            p.skins = enforceSkins(cleanSkins(m.s), p.inv, p.acct && p.acct.achs);
            this.broadcast({ t: 'sk', id: p.id, s: p.skins }, p.id);
          })().catch((e) => logErr('skin', e));
        }
        break;
      case 'rig': this.onRig(p, m); break; // overdrive rig: punch, hack, missiles, leap, landing (server/rig.js)
      case 'pi': send(p, { t: 'po', c: Number.isFinite(m.c) ? m.c : 0 }); break; // echo a number, not whatever object came in
      case 'land': this.airFail(p, false); break; // your client saw you touch the ground: run's over
      case 'lasso': this.onLasso(p, m); break; // throw / let go / wriggle
      case 'lh': this.onLassoHold(p, m); break; // the body you hold, from your client
    }
  }

  roundInfo() {
    if (!this.round) return null;
    const r = { target: this.round.target, left: Math.max(0, (this.round.over ? this.round.next : this.round.ends) - now()), over: this.round.over, game: this.game };
    if (this.teamsOn()) r.sc = [this.score[1], this.score[2]];
    if (GAMES[this.game].infect) { const s = this.survivors().length; r.inf = { s, z: this.fighters().length - s, t0: this.infAt ? Math.max(0, this.infAt - now()) : 0 }; }
    if (this.zm) r.zm = this.zmInfo();
    if (this.warm) r.warm = this.warmInfo(); // a mode lobby's countdown
    const b = this.bomb;
    if (b) {
      const n = now();
      r.bomb = { att: b.att, ph: b.ph, n: b.n, wins: [b.wins[1], b.wins[2]], carrier: b.carrier, drop: b.drop, p: b.p, site: b.site,
        left: Math.max(0, (b.ph === 'planted' ? b.explodeAt : b.between || b.ends) - n),
        act: b.act ? { k: b.act.kind, by: b.act.id, f: Math.min(1, (n - b.act.start) / this.actMs(b.act)) } : 0 };
      if (this.isEcon()) this.econRoundInfo(r);
    }
    return r;
  }
  tickRound() {
    const r = this.round;
    if (!r) return;
    const n = now();
    skipTick(this, n);
    if (this.warm) { this.tickWarm(n); return; } // a mode lobby: the countdown (no skip vote, no kill limit)
    if (r.over) { this.tickVote(n); if (n >= r.next) { if (this.lobby) this.enterWarm(LOBBY.again); else this.startRound(); } return; } // a mode lobby goes back to a short lobby, so the group stays together
    if (!this.humans().length) return;
    if (this.zm) { this.zmRound(n); return; } // zombies ends when everyone's down
    if (this.game === 'bomb' && this.bomb) { this.tickBomb(n); return; }
    if (this.tickModes(n)) return; // gun game + infection end their own way
    if (this.teamsOn()) { if (this.score[1] >= r.target || this.score[2] >= r.target || n >= r.ends) this.endRound(); return; }
    if (this.livesOn) { this.tickLives(n); return; }
    if (this.brOn) { this.tickBR(n); return; }
    let top = null;
    for (const p of this.players.values()) if (!top || p.kills > top.kills) top = p;
    if ((top && top.kills >= r.target) || n >= r.ends) this.endRound();
  }
  endRound() {
    const list = [...this.players.values()].filter((p) => !(p.isBot && p.ai.dummy)).sort((a, b) => b.kills - a.kills || a.deaths - b.deaths);
    this.modeSort(list, this.round.res);
    const lives = (p) => (p.oitc && !p.oitc.out ? p.oitc.lives : 0);
    if (this.livesOn) list.sort((a, b) => lives(b) - lives(a) || b.kills - a.kills); // one in the chamber: still standing first
    const lastOne = this.livesOn ? list.filter((p) => lives(p) > 0).length === 1 : this.brOn && !!this.br && !!this.br.winner;
    // team games: the winning team takes it, and its best player gets the roll
    let winTeam = 0;
    if (this.teamsOn()) {
      const sc = this.game === 'bomb' && this.bomb ? this.bomb.wins : this.score;
      winTeam = sc[1] === sc[2] ? 0 : sc[1] > sc[2] ? 1 : 2;
    }
    // a drawn team match has no winner (no roll, no stat): FFA needs at least one kill (or to be the last one standing)
    const winner = this.teamsOn() ? (winTeam && list.find((p) => p.team === winTeam)) || null : list[0] && (list[0].kills > 0 || lastOne) ? list[0] : null;
    this.round.over = true;
    this.round.next = now() + (this.mode === 'ffa' || this.mode === 'bots' ? voteTotal() : VOTE_MS + 2000);
    this.round.winTeam = winTeam;
    this.airEnd();
    if (this.bomb) { this.bomb.act = null; this.bomb.between = 0; }
    let roll = null;
    if (winner && !winner.isBot && this.round.skipped) roll = { n: 0, why: 'skipped matches pay no containers' };
    else if (winner && !winner.isBot) {
      const eligible = this.mode === 'ffa' ? this.humans().length >= 2 : list.filter((p) => p.isBot).length >= 3;
      if (!winner.acct) { roll = { n: 0, guest: 1 }; if (eligible && winner.kills && winner.m) winner.m.xp += 50; } // the xp they'd have kept
      else if (!eligible) roll = { n: 0, why: this.mode === 'ffa' ? 'need at least 2 real players for a roll' : 'need at least 3 bots for a roll' };
      else if (!winner.kills) roll = { n: 0, why: 'no kills, no roll (hiding is not winning)' }; // last one standing still needs to have fought
      else {
        stat(winner, 'wins', 1); stat(winner, 'xp', 50);
        const kind = randomContainer();
        store.grantRolls(winner.acct.n, kind, 1).catch((e) => console.error('roll grant failed', e.message));
        roll = { n: 1, kind, why: 'won the round' };
      }
    }
    this.broadcast({ t: 'round', over: 1, skipped: this.round.skipped ? 1 : 0, winner: winner ? winner.id : 0, winTeam, game: this.game, br: this.brOn && this.br ? this.brBoardInfo() : undefined, sc: this.teamsOn() ? (this.game === 'bomb' && this.bomb ? [this.bomb.wins[1], this.bomb.wins[2]] : [this.score[1], this.score[2]]) : null,
      top: list.slice(0, 6).map((p) => [p.id, p.name, p.kills, p.deaths, p.team || 0]), next: this.round.next - now(),
      board: list.map((p, i) => [p.id, p.name, p.kills, p.deaths, p.team || 0, p.isBot ? 1 : 0, matchSummary(p, i, list, this).score]) });
    // your own match report (end screen: performance / medals / rewards). guests see the xp they would have kept
    const side = GAMES[this.game].infect && this.round.res && this.round.res.side; // infection: the whole side that took it won
    const won = (p) => (side ? (side === 'inf') === !!p.inf : p === winner || (winTeam && p.team === winTeam));
    list.forEach((p, i) => { if (!p.isBot) send(p, { t: 'perf', ...matchSummary(p, i, list, this), won: won(p) ? 1 : 0, acct: p.acct ? 1 : 0 }); });
    this.startVote(); // after the result: clients open the end screen on 'round', then the vote fills it in
    const r = this.round;
    setTimeout(safe('hl', () => {
      if (this.round !== r || !r.hl || r.hl.pending || !r.hl.clip || !r.hl.clip.frames.length) return;
      const { label, id, name, color, card, clip } = r.hl;
      this.broadcast({ t: 'hl', label, id, name, color, card, clip });
      // how long it plays: the clip, plus the slow-mo at each of their kills (0.3x for ~0.5 s). the vote's hurry mustn't cut it
      const fr = clip.frames, kills = clip.ev.filter((e) => e.m && e.m.t === 'kill' && e.m.k === id).length;
      r.hlEnd = now() + (fr[fr.length - 1].s - fr[0].s) + kills * 1150 + 500;
    }), 1600);
    if (roll) send(winner, { t: 'roll+', ...roll });
  }
  startRound() {
    this.dropLeavers(true); // bots that gave their place to a human leave between matches
    this.resolveVote();
    for (const p of this.players.values()) { p.kills = 0; p.deaths = 0; matchReset(p); }
    this.firstBlood = 0;
    for (const p of this.players.values()) p.lastKiller = 0; // new match: the court forgets old grudges
    this.round = { target: (TARGETS[this.mode] || TARGETS.ffa)[this.game] || ROUND[this.mode].kills, ends: now() + ROUND[this.mode].time * 1000, over: false, next: 0 };
    this.round.t0 = now();
    this.score = { 1: 0, 2: 0 };
    this.clearTags();
    this.zmReset(); // zombies: a fresh game, or clear the last one away (before teams, so no zombies on them)
    this.startModes();
    this.assignTeams();
    this.bomb = this.game === 'bomb' && this.teamsOn() ? { att: 1, n: 0, wins: { 1: 0, 2: 0 } } : null;
    if (this.bomb) { this.round.ends = now() + 3600 * 1000; this.newBombRound(true); }
    else this.resetWorld();
    this.airStart(); // after the respawns: a client must get its 'spawn' (fresh grace) before the run starts
    this.brRound(); // jank royale: everyone onto the blimp (or off with the old one)
    this.broadcast({ t: 'round', start: 1, ...this.roundInfo() });
  }
  // ---------------------------------------------------------- Never Landed: a whole match without touching the ground
  // the client knows exactly when it lands and reports it ('land'); the server also watches snapshots so a client
  // that never reports can't just stand around. the match end decides.
  airStart() {
    this.airBad = new Set(); // names that touched down this match: leaving and rejoining doesn't wipe it
    // Floor Is Lava has no Never Landed run: everyone's kept off the floor there anyway (and the lava bounces you
    // back up), so it would come almost for free
    if (GAMES[this.game].lava || GAMES[this.game].royale || this.warm) return; // (a royale starts in the sky. a lobby's warm-up doesn't count)
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
      const ok = p.air.ok && !(this.round && this.round.skipped); // a skipped match is too short to count
      p.air = null;
      send(p, { t: 'air', end: 1, ok: ok ? 1 : 0, acct: p.acct ? 1 : 0 });
      if (ok) { console.log(`never landed: ${p.name}`); stat(p, 'airborne', 1); }
    }
  }
  // switch game type (bots setup / match settings / the vote)
  setGame(g) {
    if (!has(GAMES, g)) return false;
    if (!GAMES[g].zombies !== !(MAPS[this.cfg.map] && MAPS[this.cfg.map].zm)) { const ok = mapsFor(g, MAPS, MAP_ORDER); this.cfg.map = ok.includes('islands') ? 'islands' : ok[0]; this.smokes.clear(); } // zombies comes with its own map
    const id = mapForGame(g, MAPS, this.cfg.map), m = MAPS[id]; // a map with an S&D version: Plant & Defuse plays that, the rest the standard one
    if (GAMES[g].sites && !(m.sites && m.sites.length)) return false;
    if (GAMES[g].mapOk && !GAMES[g].mapOk(m)) return false; // e.g. floor is lava: no real floor here (or nothing to stand on)
    if (id !== this.cfg.map) { this.cfg.map = id; this.smokes.clear(); } // (the caller sends the new cfg: clients load the other version)
    this.game = g;
    return true;
  }

  // ---------------------------------------------------------- the end-of-match vote: mode first, then map
  // stage 'mode' (VOTE.mode ms) -> stage 'map' for the mode that won (VOTE.map ms) -> 'done' (the reveal) -> next round.
  // humans decide; bots vote too, but only break ties (shared/vote.js)
  startVote() {
    if (this.mode !== 'ffa' && this.mode !== 'bots') return;
    const options = modeCards(MAPS, MAP_ORDER, this.game, Math.random, this.skipped);
    if (this.mode === 'bots' && !inQuickPlay(this.game) && this.skipped !== this.game && options.length && !options.some((o) => o.game === this.game)) options[options.length - 1] = { game: this.game, event: 0 }; // solo zombies: play again is always an option
    this.skipped = null;
    if (this.lobbyVote && this.lobbyVote()) return; // a one-mode lobby (P&D, royale, zombies): only the map is up for a vote
    if (!options.length) return;
    this.vote = { stage: 'mode', options, votes: new Map(), ends: now() + VOTE.mode, game: null, map: null };
    this.botVotes();
    this.broadcast({ t: 'vote', ...this.voteInfo() });
  }
  castVote(p, i) {
    const v = this.vote;
    p.voteT = now(); p.votePend = null;
    if (v.votes.get(p.id) === i) return;
    v.votes.set(p.id, i);
    this.broadcast({ t: 'votes', ...this.voteCounts() });
    this.voteHurry();
  }
  // the next round never starts before the play of the round has finished playing
  holdForHl() { const r = this.round; if (r && r.over && r.hlEnd) r.next = Math.max(r.next, r.hlEnd); }
  // every human has voted: no point sitting through the rest of the stage. the bots still get their say first
  voteHurry() {
    const v = this.vote, n = now(), soon = n + 2500;
    if (!v || v.stage === 'done' || v.ends <= soon || !this.humans().every((h) => v.votes.has(h.id))) return;
    if (this.round && this.round.over) { this.round.next -= v.ends - soon; this.holdForHl(); }
    v.ends = soon;
    for (const p of this.players.values()) if (p.voteAt) p.voteAt = Math.min(p.voteAt, n + 300 + Math.random() * 1800);
    this.broadcast({ t: 'votes', ...this.voteCounts(), left: soon - n, total: this.round && this.round.over ? this.round.next - n : 0 });
  }
  // every bot picks a card at some random moment of the stage
  botVotes() {
    const v = this.vote, n = now(), span = Math.max(0, Math.min(VOTE.botMax, v.ends - n - 800) - VOTE.botMin);
    for (const p of this.players.values()) if (p.isBot && !(p.ai && p.ai.dummy)) p.voteAt = n + VOTE.botMin + Math.random() * span;
  }
  tickVote(n) {
    const v = this.vote;
    if (!v || v.stage === 'done') return;
    for (const p of this.players.values()) { // re-picks that came in too fast: count them now
      if (!p.votePend || n - (p.voteT || 0) <= 250) continue;
      if (p.votePend.stage === v.stage) this.castVote(p, p.votePend.i); else p.votePend = null;
      if (this.vote !== v || v.stage === 'done') return;
    }
    let changed = false;
    for (const p of this.players.values()) {
      if (!p.isBot || !p.voteAt || n < p.voteAt || v.votes.has(p.id)) continue;
      p.voteAt = 0;
      // bots like the event and whatever's already winning a bit more than the rest
      const { h, b } = tally(v.options.length, v.votes, (id) => this.players.get(id)?.isBot);
      const w = v.options.map((o, i) => 1 + (o.event ? 1.2 : 0) + (h[i] + b[i]) * 0.6);
      let r = Math.random() * w.reduce((x, y) => x + y, 0), i = 0;
      while (i < w.length - 1 && (r -= w[i]) > 0) i++;
      v.votes.set(p.id, i); changed = true;
    }
    if (changed) this.broadcast({ t: 'votes', ...this.voteCounts() });
    if (n >= v.ends) this.advanceVote();
  }
  // close the open stage (also used to fast-forward a vote when the next round starts early)
  advanceVote() {
    const v = this.vote;
    if (!v || v.stage === 'done') return;
    const isBot = (id) => this.players.get(id)?.isBot;
    const win = v.options[voteWinner(v.options.length, v.votes, isBot)];
    for (const p of this.players.values()) { p.voteT = 0; p.votePend = null; } // a new stage: everyone can pick straight away
    if (v.stage === 'mode') {
      v.game = win.game; v.event = win.event;
      const maps = mapCards(v.game, MAPS, MAP_ORDER, this.cfg.map);
      if (maps.length > 1) {
        Object.assign(v, { stage: 'map', options: maps, votes: new Map(), ends: now() + VOTE.map });
        this.botVotes();
        if (this.round && this.round.over) this.round.next = Math.max(this.round.next, v.ends + VOTE.reveal);
        this.broadcast({ t: 'vote', ...this.voteInfo() });
        return;
      }
      v.map = maps.length ? maps[0].map : this.cfg.map;
    } else v.map = win.map;
    Object.assign(v, { stage: 'done', options: [], votes: new Map(), ends: now() + VOTE.reveal });
    if (this.round && this.round.over) { this.round.next = Math.min(this.round.next, now() + VOTE.reveal); this.holdForHl(); }
    this.broadcast({ t: 'vote', ...this.voteInfo() });
    this.broadcast({ t: 'chat', id: 0, m: `next up: ${GAMES[v.game].name} on ${MAPS[v.map].name}` });
  }
  voteCounts() {
    const v = this.vote;
    const { h, b } = tally(v.options.length, v.votes, (id) => this.players.get(id)?.isBot);
    return { stage: v.stage, counts: h, bots: b };
  }
  voteInfo() {
    const v = this.vote;
    if (!v) return null;
    const options = v.options.map((o) => (o.game ? { ...o, name: GAMES[o.game].name, teams: GAMES[o.game].teams ? 1 : 0 } : { ...o, mapName: MAPS[o.map].name, size: MAPS[o.map].size }));
    return { ...this.voteCounts(), options, left: Math.max(0, v.ends - now()), total: this.round && this.round.over ? Math.max(0, this.round.next - now()) : 0,
      game: v.game || undefined, gameName: v.game ? GAMES[v.game].name : undefined, event: v.event ? 1 : 0,
      map: v.map || undefined, mapName: v.map ? MAPS[v.map].name : undefined, ev: eventGame() };
  }
  resolveVote() {
    if (this.vote && this.vote.stage !== 'done') { this.advanceVote(); this.advanceVote(); }
    const v = this.vote;
    this.vote = null;
    for (const p of this.players.values()) { p.voteAt = 0; p.votePend = null; }
    if (!v || !v.game || !v.map || !MAPS[v.map]) return;
    const was = this.cfg.map;
    this.cfg.map = v.map;
    this.setGame(v.game); // (may swap to the version of the map the mode plays: Plant & Defuse -> the S&D one)
    const mapChanged = this.cfg.map !== was;
    this.projectiles.clear(); this.peels.clear(); this.holes.clear(); this.clearCarts();
    if (mapChanged) { this.smokes.clear(); this.broadcast({ t: 'cfg', cfg: this.cfg }); }
  }

  // ---------------------------------------------------------- tags (kill confirmed)
  // the floor under a point (null over the void)
  floorAt(p) {
    if (!p) return null;
    const h = raycast([p[0], p[1] + 1, p[2]], [0, -1, 0], 60, this.boxes);
    return h && h.point[1] > this.map.killY ? h.point : null;
  }
  // tags land on the floor under the body; off the map they drop where the victim last stood (or at the killer)
  dropTag(t, killer) {
    const at = this.floorAt(t.pos) || this.floorAt(t.ground) || (killer && killer.alive && this.floorAt(killer.pos));
    if (!at) return;
    const g = { id: this.nextTag++, p: [r2(at[0]), r2(at[1] + 0.9), r2(at[2])], team: t.team, born: now() };
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
    this.dropLeavers(true); // bots that gave their place to a human leave between rounds
    Object.assign(b, { ph: 'live', site: null, p: null, drop: null, explodeAt: 0, act: null, between: 0, ends: now() + (process.env.JF_BOMB_ROUND ? BOMB.roundTime : this.map.roundTime || BOMB.roundTime) * 1000, carrier: 0 }); // per-map round time (the test knob still wins)
    for (const p of this.players.values()) if (p.ai) { p.ai.site = null; p.ai.route = null; }
    if (this.isEcon()) this.econNewRound(first); // buy phase, payouts carried over, the half's credit reset
    this.projectiles.clear(); this.peels.clear(); this.holes.clear(); this.clearCarts();
    this.resetWorld();
    this.giveBomb();
    this.broadcast({ t: 'bombev', k: 'round', n: b.n, att: b.att });
  }
  // hand the bomb to a random living attacker (humans first, never skip), or leave it at the attackers' spawn
  giveBomb(skip) {
    const b = this.bomb;
    const att = this.fighters().filter((p) => p.team === b.att && p.alive && p !== skip);
    const hs = att.filter((p) => !p.isBot);
    const c = hs.length ? pick(hs) : att.length ? pick(att) : null;
    b.carrier = c ? c.id : 0; b.drop = null; b.idle = null;
    if (c) { send(c, { t: 'bombyou' }); return; }
    const s = (this.map.teamSpawns && this.map.teamSpawns.att[0]) || this.map.spawns[0];
    const f = this.floorAt(s);
    b.drop = [r2(s[0]), r2((f ? f[1] : s[1]) + 0.15), r2(s[2])]; b.dropT = now();
  }
  dropBomb(pos, from) {
    const b = this.bomb;
    if (!b || b.ph !== 'live') return;
    b.carrier = 0; b.idle = null;
    const f = this.floorAt(pos);
    b.drop = f ? [r2(pos[0]), r2(f[1] + 0.15), r2(pos[2])] : null; b.dropT = now();
    if (!b.drop) this.giveBomb(from); // fell into the void with it: it comes back to another attacker
    this.broadcast({ t: 'bombev', k: 'drop' });
  }
  bombRoundWin(team, why) {
    const b = this.bomb;
    b.wins[team]++;
    b.ph = 'done'; b.act = null;
    this.broadcast({ t: 'bombev', k: 'win', team, why, wins: [b.wins[1], b.wins[2]] });
    if (this.isEcon()) this.econRoundEnd(team, why);
    if (b.wins[team] >= BOMB.wins) { this.endRound(); return; }
    b.between = now() + BOMB.between;
  }
  tickBomb(n) {
    const b = this.bomb;
    if (b.between) { if (n >= b.between) this.newBombRound(false); return; }
    if (b.ph === 'done') return;
    if (b.ph === 'live' && !b.drop) {
      const c = this.players.get(b.carrier);
      if (!c || !c.alive || c.team !== b.att) this.giveBomb(); // nobody has it (empty side at round start, a carrier who left)
      else if (!b.idle || b.idle.id !== c.id || dist3(c.pos, b.idle.p) > 1.5) b.idle = { id: c.id, p: c.pos.slice(), t: n };
      else if (n - b.idle.t > 15000 && !b.act && this.fighters().some((p) => p !== c && p.alive && p.team === b.att)) {
        // an AFK carrier drops it for the team (and can't grab it straight back)
        this.dropBomb(c.pos, c);
        b.noPick = { id: c.id, until: n + 8000 };
        send(c, { t: 'chat', id: 0, m: 'you stood still too long and dropped the bomb' });
      }
    }
    // dropped bomb: any attacker can grab it
    if (b.ph === 'live' && b.drop) {
      for (const p of this.players.values()) {
        if (!p.alive || p.team !== b.att || (b.noPick && b.noPick.id === p.id && n < b.noPick.until)) continue;
        if (Math.hypot(p.pos[0] - b.drop[0], p.pos[1] - b.drop[1], p.pos[2] - b.drop[2]) < BOMB.pickup) { b.carrier = p.id; b.drop = null; send(p, { t: 'bombyou' }); this.broadcast({ t: 'bombev', k: 'pickup', id: p.id }); break; }
      }
      // bots can't climb to every ledge: a drop no human attacker is alive to fetch goes back to a bot after 20 s
      // (only to a living one: with every attacker dead, or no bots at all, it stays where it fell)
      if (b.drop && n - (b.dropT || n) > 20000 && !this.fighters().some((p) => !p.isBot && p.alive && p.team === b.att) && this.fighters().some((p) => p.isBot && p.alive && p.team === b.att)) {
        this.giveBomb();
        if (b.carrier) this.broadcast({ t: 'bombev', k: 'pickup', id: b.carrier });
      }
    }
    // planting / defusing: you have to keep holding F and stay put
    if (b.act) {
      const a = this.players.get(b.act.id);
      const hold = a && a.alive && n - (a.useT || 0) < 600 && dist3(a.pos, b.act.pos) < 1.6;
      const ok = hold && (b.act.kind === 'plant' ? b.carrier === a.id && siteAt(this.map, a.pos) : b.ph === 'planted' && canDefuse(a.pos, b.p, 0.6));
      if (!ok) b.act = null;
      else if (n - b.act.start >= this.actMs(b.act)) {
        if (b.act.kind === 'plant') {
          const site = siteAt(this.map, a.pos);
          Object.assign(b, { ph: 'planted', site: site.id, p: [r2(a.pos[0]), r2(a.pos[1] + 0.1), r2(a.pos[2])], explodeAt: n + BOMB.fuse * 1000, carrier: 0, act: null, planter: a.id });
          this.broadcast({ t: 'bombev', k: 'planted', site: site.id, id: a.id });
          if (a.acct) stat(a, 'xp', 10); else if (a.m) a.m.xp += 10;
        } else {
          b.act = null;
          this.broadcast({ t: 'bombev', k: 'defused', id: a.id });
          if (a.acct) stat(a, 'xp', 15); else if (a.m) a.m.xp += 15;
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
    if (this.zm) { this.zmUse(p); return; } // doors, wall guns, the crate, revives
    const b = this.bomb;
    if (!b || !p.alive || b.between || b.ph === 'done') return;
    p.useT = now();
    if (b.act) return;
    if (b.ph === 'live' && b.carrier === p.id && siteAt(this.map, p.pos)) b.act = { id: p.id, kind: 'plant', start: now(), pos: p.pos.slice() };
    else if (b.ph === 'planted' && p.team !== b.att && canDefuse(p.pos, b.p)) b.act = { id: p.id, kind: 'defuse', start: now(), pos: p.pos.slice() };
    if (b.act) this.broadcast({ t: 'bombev', k: b.act.kind, id: p.id });
  }

  // training: your 3 picked killstreaks are always in your tray. a used one comes back once it has run out (+3 s)
  trainingStreaks(n) {
    if (n - (this.trainT || 0) < 1000) return;
    this.trainT = n;
    for (const p of this.players.values()) {
      if (p.isBot || !p.alive) continue;
      p.pocket ||= []; p.trainCd ||= {};
      for (const id of validStreaks(p.streaks)) {
        if (p.pocket.includes(id) || n < (p.trainCd[id] || 0)) continue;
        p.pocket.push(id);
        send(p, { t: 'streak', earned: id, n: 0 });
      }
    }
  }
  // ---------------------------------------------------------- gun game + infection
  // the one weapon a mode lets p use: their gun game rung, or the claw once they're a zombie (null = their own loadout)
  modeWeapon(p) {
    if (this.mode !== 'ffa' && this.mode !== 'bots') return null;
    const g = GAMES[this.game];
    if (g.ladder) return LADDER[Math.min(p.gg || 0, LADDER.length - 1)];
    if (g.infect && p.inf) return 'claw';
    return null;
  }
  // can p hit / fire with wid? only their mode weapon while a mode hands one out, and the claw only as a zombie
  allowed(p, wid) {
    const only = this.modeWeapon(p);
    return only ? wid === only : !(has(WEAPONS, wid) && WEAPONS[wid].mode === 'inf');
  }
  // every spawn: hand out the mode weapon (+ zombie HP), or the normal loadout back once the mode is over
  modeLoadout(p) {
    const w = this.modeWeapon(p);
    if ((!w && !p.only) || (p.isBot && p.ai.dummy)) return false;
    if (w === 'claw' && p.alive) { p.hp = INFECT.hp; p.healLeft = 0; }
    if (w && p.ballUntil) { p.ballUntil = 0; p.f &= ~FLAGS.BALL; } // patient zero mid wrecking ball: claws only (the client ends it on 'modew')
    if (w && p.rig) this.rigEnd(p); // same for the overdrive rig
    if (p.isBot) { p.w = w || pick(BOT_GUNS); p.ai.ammo = WEAPONS[p.w].mag || 1; p.ai.reloadUntil = 0; }
    else {
      if (w && p.forced) { p.forced = false; send(p, { t: 'loadout', lo: null }); }
      if (w) p.w = w;
      send(p, { t: 'modew', w });
    }
    p.only = w;
    return !!w;
  }
  // bots run faster holding a mode weapon that says so (the zombie claw)
  modeSpeed(b) { return b.only ? WEAPONS[b.w].speedMul || 1 : 1; }
  // joined mid-match: bottom of the ladder, or a zombie if the infection already got going. tell them who's where
  modeJoin(p) {
    if (this.mode !== 'ffa' && this.mode !== 'bots') return;
    const g = GAMES[this.game], live = this.round && !this.round.over;
    p.gg = GG_START;
    p.inf = !!(g.infect && live && !this.infAt && this.fighters().some((o) => o.inf));
    if (p.inf) p.infT = now();
    if (p.inf) this.broadcast({ t: 'infect', id: p.id, by: 0, late: 1 }, p.id);
    if (p.isBot) { this.modeLoadout(p); return; }
    send(p, { t: 'gg', all: g.ladder ? this.fighters().map((o) => [o.id, o.gg || 0]) : [] });
    send(p, { t: 'infect', all: g.infect ? this.fighters().filter((o) => o.inf).map((o) => o.id) : [] });
  }
  // a fresh match: everyone back to the bottom of the ladder and human again
  startModes() {
    const g = GAMES[this.game], n = now();
    for (const p of this.players.values()) { p.gg = g.ladder ? GG_START : 0; p.inf = false; }
    this.infAt = g.infect ? n + INFECT.delay * 1000 : 0;
    this.infLast = 0;
    if (g.ladder) { this.round.target = LADDER.length; this.round.ends = n + GUNGAME.time * 1000; }
    if (g.infect) { this.round.target = 0; this.round.ends = n + INFECT.time * 1000; }
    this.broadcast({ t: 'gg', all: g.ladder ? this.fighters().map((p) => [p.id, p.gg]) : [] });
    this.broadcast({ t: 'infect', all: [] });
  }
  // a death under the mode's rules (kw: what really killed them; void kills count for whoever knocked them off)
  modeKill(t, killer, kw) {
    if (!this.round || this.round.over || (this.mode !== 'ffa' && this.mode !== 'bots')) return;
    if (GAMES[this.game].ladder) this.ggKill(t, killer, kw);
    else if (GAMES[this.game].infect && !this.infAt && !t.inf) this.infect(t, killer);
  }
  // gun game ends on the spoon kill or the clock, infection on the clock or when nobody's left to infect
  tickModes(n) {
    const g = GAMES[this.game];
    if (!g.ladder && !g.infect) return false;
    if (g.infect) this.tickInfect(n);
    else if (n >= this.round.ends) this.endRound();
    return true;
  }
  // end screen order: gun game by rung, infection with the winning side on top
  modeSort(list, res) {
    const g = GAMES[this.game];
    if (g.ladder) list.sort((a, b) => (b.gg || 0) - (a.gg || 0) || b.kills - a.kills || a.deaths - b.deaths);
    else if (g.royale && this.br) this.brSort(list);
    else if (g.infect && res) list.sort((a, b) => (!!b.inf === (res.side === 'inf')) - (!!a.inf === (res.side === 'inf'))); // stable: by kills within a side
  }

  // gun game: a kill with your rung's weapon moves you up (the one with the spoon wins), dying to melee knocks you back one
  ggKill(t, killer, kw) {
    if (!killer || killer === t) return;
    const N = LADDER.length;
    if (kw === LADDER[killer.gg || 0]) {
      killer.gg = (killer.gg || 0) + 1;
      this.broadcast({ t: 'gg', id: killer.id, n: killer.gg, k: killer.gg >= N ? 'win' : killer.gg === N - 1 ? 'last' : 'up' });
      if (killer.gg >= N) { this.endRound(); return; } // modeSort puts them on top
      this.modeLoadout(killer); // the next weapon, right now
    }
    if (WEAPONS[kw] && WEAPONS[kw].kind === 'melee') { // humiliated: they get it on respawn
      t.gg = Math.max(0, (t.gg || 0) - 1);
      this.broadcast({ t: 'gg', id: t.id, n: t.gg, k: 'down', by: killer.id });
    }
  }

  // infection: p turns. patient zero turns on the spot; the dead come back as zombies
  infect(p, by, first) {
    if (p.inf) return;
    p.inf = true; p.infT = now();
    if (p.alive) this.modeLoadout(p);
    this.broadcast({ t: 'infect', id: p.id, by: by && by !== p ? by.id : 0, first: first ? 1 : undefined });
  }
  survivors() { return this.fighters().filter((p) => !p.inf); }
  tickInfect(n) {
    if (this.infAt) { // patient zero (two in big lobbies) turns a few seconds in, once there's someone to chase
      if (n < this.infAt) return;
      const pool = this.fighters();
      if (pool.length < 2) { this.infAt = n + 1000; if (n >= this.round.ends) this.endInfect('surv'); return; }
      this.infAt = 0;
      for (let k = pool.length >= INFECT.two ? 2 : 1; k > 0; k--) this.infect(pool.splice((Math.random() * pool.length) | 0, 1)[0], null, true);
    }
    const surv = this.survivors(), z = this.fighters().length - surv.length;
    if (!surv.length) { this.endInfect('inf'); return; }
    if (!z) { if (surv.length >= 2) this.infAt = n; else if (n >= this.round.ends) this.endInfect('surv'); return; } // the zombies all left: someone else turns
    if (surv.length === 1 && this.infLast !== surv[0].id) { this.infLast = surv[0].id; this.broadcast({ t: 'infect', last: surv[0].id }); }
    if (n >= this.round.ends) this.endInfect('surv');
  }
  // the winning side goes on top of the end screen; its best player takes the round (and the roll) only if they
  // got a kill, like dm, so hiding till the clock runs out doesn't pay. the side's title shows either way
  endInfect(side) {
    this.round.res = { side };
    this.broadcast({ t: 'infect', side });
    this.endRound();
  }

  // ---------------------------------------------------------- chaos modes: spoons & grapples, duck rain, floor is lava, one in the chamber
  get chaosKit() { return ((this.mode === 'ffa' || this.mode === 'bots') && GAMES[this.game].kit) || null; }
  get lavaOn() { return (this.mode === 'ffa' || this.mode === 'bots') && !!GAMES[this.game].lava && lavaOk(this.map); }
  get livesOn() { return (this.mode === 'ffa' || this.mode === 'bots') && !!GAMES[this.game].lives; }
  get hookMul() { return ((this.mode === 'ffa' || this.mode === 'bots') && GAMES[this.game].hookMul) || 1; }
  // everyone gets the mode's kit (players get told, bots switch guns and get theirs back afterwards). true = handled
  sendChaosKit(p) {
    const kit = this.chaosKit;
    if (p.isBot) {
      if (p.ai.dummy) return false;
      if (!kit) { if (p.ai.ownW) { p.w = p.ai.ownW; p.ai.ownW = null; p.ai.ammo = WEAPONS[p.w].mag || 1; } return false; }
      if (!p.ai.ownW) p.ai.ownW = p.w;
      p.w = kit.slots[0]; p.ai.ammo = WEAPONS[p.w].mag || 1;
      if (this.livesOn) this.oitcSpawn(p);
      return true;
    }
    if (!kit) return false;
    p.forced = true; p.scythe = false;
    send(p, { t: 'loadout', lo: { only: kit.slots, item: kit.noItem ? 'none' : undefined, noReload: !!kit.noReload, noStreaks: !!kit.noStreaks, desc: kit.desc } });
    if (this.livesOn) this.oitcSpawn(p);
    return true;
  }
  // only your kit's weapons count. one in the chamber: a revolver hit spends a bullet and always kills
  chaosHit(p, m) {
    const kit = this.chaosKit;
    if (!kit) return true;
    if (!kit.slots.includes(m.w)) return false;
    if (!this.livesOn || m.w !== 'revolver') return true;
    const t = this.players.get(m.to), d = norm(vec3(m.d));
    if (!t || !d || t === p || !t.alive || !p.alive || !this.rangeOk(p, t, WEAPONS.revolver.range) || !this.oitcShot(p, 'hit')) return false;
    this.hurt(t, p, 'revolver', 999, null, { hs: clampInt(m.h, 0, 1) > 0 });
    return false;
  }
  chaosFire(p, m) {
    const kit = this.chaosKit;
    if (!kit) return true;
    if (!kit.slots.includes(m.w)) return false;
    return !this.livesOn || m.w !== 'revolver' || this.oitcShot(p, 'fire');
  }
  // a shot sends 'hit' (if it hit someone) and 'fire' a moment apart: both ride on one bullet
  oitcShot(p, kind) {
    const o = p.oitc, n = now();
    if (!o || !p.alive) return false;
    const s = o.shot;
    if (s && n - s.t < 250 && !s[kind]) { s[kind] = true; return true; }
    if (o.bullets <= 0 || (s && n - s.t < 300)) { this.sendOitc(p); return false; }
    o.bullets--;
    o.shot = { t: n, [kind]: true };
    this.sendOitc(p);
    return true;
  }
  // late joiners get as many lives as whoever has the fewest (nobody gets a head start)
  oitcKey(p) { return p.acct ? 'a:' + p.acct.n : 'n:' + p.name; }
  oitcSpawn(p) {
    if (!p.oitc && this.oitcOut.has(this.oitcKey(p))) { // out of lives this round: reconnecting doesn't buy you new ones
      p.oitc = { lives: 0, bullets: 0, out: true, shot: null }; p.alive = false; p.respawnAt = Infinity; p.deadT = now();
      this.sendOitc(p); this.oitcList(); return;
    }
    if (!p.oitc) {
      const ins = [...this.players.values()].filter((o) => o !== p && o.oitc && !o.oitc.out);
      p.oitc = { lives: ins.length ? Math.max(1, Math.min(...ins.map((o) => o.oitc.lives))) : GAMES[this.game].lives, bullets: 0, out: false, shot: null };
      this.oitcList();
    }
    p.oitc.bullets = GAMES[this.game].bullets[0]; p.oitc.shot = null;
    this.sendOitc(p);
  }
  sendOitc(p) { if (!p.isBot && p.oitc) send(p, { t: 'oitc', b: p.oitc.bullets, l: p.oitc.lives, out: p.oitc.out ? 1 : 0 }); }
  oitcList() { this.broadcast({ t: 'oitcl', list: this.fighters().map((x) => [x.id, x.oitc ? x.oitc.lives : 0]) }); }
  // a death: one in the chamber takes a life (none left = out, you spectate) and gives the killer a bullet
  chaosKill(t, killer) {
    if (!this.livesOn || !this.round || this.round.over) return;
    const o = t.oitc;
    if (o && !o.out) {
      o.lives = Math.max(0, o.lives - 1); o.bullets = 0;
      if (!o.lives) { o.out = true; t.respawnAt = Infinity; this.oitcOut.add(this.oitcKey(t)); this.broadcast({ t: 'chat', id: 0, m: `${t.name} is out of lives` }); }
      this.sendOitc(t);
    }
    if (killer && killer !== t && killer.oitc && killer.alive) { killer.oitc.bullets = Math.min(GAMES[this.game].bullets[1], killer.oitc.bullets + 1); this.sendOitc(killer); }
    this.oitcList();
  }
  // last one standing wins (once at least two were in it), or on time: most lives, then most kills
  tickLives(n) {
    const r = this.round, f = this.fighters();
    r.peak = Math.max(r.peak || 0, f.length);
    const ins = f.filter((p) => p.oitc && !p.oitc.out);
    if ((r.peak >= 2 && ins.length <= 1) || n >= r.ends) this.endRound();
  }
  // a new round or map: everyone back in with full lives, the sky clears up
  resetChaos() {
    this.rain = null; this.oitcOut = new Set();
    if (!this.livesOn) return;
    if (this.round) this.round.target = 0; // no kill limit: last one standing
    for (const p of this.players.values()) p.oitc = { lives: GAMES[this.game].lives, bullets: 0, out: false, shot: null };
    this.oitcList();
  }
  tickChaos(dt, n) {
    if (this.mode !== 'ffa' && this.mode !== 'bots') return;
    if (GAMES[this.game].duckRain) this.tickDuckRain(n);
    if (this.lavaOn) this.tickLava(n, dt);
  }
  // duck rain: a few ducks every couple of seconds, more and more often as the match goes on, half of them near someone
  tickDuckRain(n) {
    const r = this.round;
    if (!r || r.over || !this.humans().length) return;
    const R = this.rain || (this.rain = { next: n + 3000 });
    if (n < R.next) return;
    let top = 0;
    for (const p of this.players.values()) top = Math.max(top, p.kills);
    const dur = ROUND[this.mode].time * 1000, k = Math.max(0, Math.min(1, Math.max(1 - (r.ends - n) / dur, top / r.target)));
    R.next = n + (DUCKRAIN.every[0] + (DUCKRAIN.every[1] - DUCKRAIN.every[0]) * k) * 1000;
    const s = surfaces(this.map), size = Math.max(0.5, Math.min(1.8, Math.sqrt(s.total / 9000)));
    const count = Math.max(1, Math.round((DUCKRAIN.n[0] + (DUCKRAIN.n[1] - DUCKRAIN.n[0]) * k) * size + Math.random() - 0.5));
    const alive = this.fighters().filter((p) => p.alive);
    for (let i = 0; i < count; i++) for (let tries = 0; tries < 6; tries++) if (this.skyDuck(alive.length && Math.random() < DUCKRAIN.near ? pick(alive) : null, s)) break;
  }
  // one duck: falls straight down onto whatever is on top there (a roof keeps you dry) and everyone sees where first
  skyDuck(near, s) {
    let x, z;
    if (near) { const a = Math.random() * Math.PI * 2, d = 2 + Math.random() * 12; x = near.pos[0] + Math.cos(a) * d; z = near.pos[2] + Math.sin(a) * d; }
    else {
      let r = Math.random() * s.total, t = s.tops[0];
      for (const tt of s.tops) { r -= tt.area; if (r <= 0) { t = tt; break; } }
      if (!t) return false;
      x = t.b.min[0] + Math.random() * (t.b.max[0] - t.b.min[0]); z = t.b.min[2] + Math.random() * (t.b.max[2] - t.b.min[2]);
    }
    const top = s.maxTop + 20, h = raycast([x, top, z], [0, -1, 0], top - this.map.killY, this.boxes);
    if (!h) return false;
    const w = WEAPONS.duck, land = h.point, y0 = Math.min(top - 1, land[1] + DUCKRAIN.height);
    const pr = this.makeProj({ id: 0 }, 'duck', [x, y0, z], [0, -DUCKRAIN.vy, 0], { sky: true });
    pr.born = now();
    const v = DUCKRAIN.vy, dy = Math.max(0, y0 - land[1] - w.r), eta = (-v + Math.sqrt(v * v + 2 * w.grav * dy)) / w.grav;
    this.broadcast({ t: 'skyduck', id: pr.id, p: land.map(r2), ms: Math.round(eta * 1000) });
    return true;
  }
  // floor is lava: bots get checked here, players bounce themselves and tell us (we also look, in case they don't)
  tickLava(n, dt) {
    const s = surfaces(this.map);
    for (const p of this.players.values()) {
      if (!p.alive || (p.isBot && p.ai.dummy)) continue;
      if (p.lavaBurn > n && n >= (p.lavaBurnT || 0)) { p.lavaBurnT = n + 300; this.broadcast({ t: 'fx', k: 'burn', id: p.id }); this.damage(p, LAVA.burnDmg, null, 'lava'); }
      if (!p.alive) continue;
      if (p.isBot) { if (p.onGround && onLava(s, this.boxes, p.pos)) this.lavaTouch(p, false); continue; }
      p.lavaSeen = onLava(s, this.boxes, p.pos, 0.03) ? (p.lavaSeen || 0) + dt : 0;
      if (p.lavaSeen > 0.12) this.lavaTouch(p, false);
    }
  }
  // touching the ground floor: hurts, keeps burning for a moment and pops you back up
  lavaTouch(p, told) {
    if (!this.lavaOn || !p.alive || (this.round && this.round.over)) return;
    const n = now(), s = surfaces(this.map);
    if (n - (p.lavaT || 0) < LAVA.every * 1000) return;
    // a player saying "ouch" has to be somewhere above lava (now or a tenth of a second ago)
    if (told && !lavaBelow(s, this.boxes, [p.pos[0], p.pos[1] + 0.3, p.pos[2]], 6) && !lavaBelow(s, this.boxes, [p.pos[0] - p.vel[0] * 0.1, p.pos[1] + 0.3, p.pos[2] - p.vel[2] * 0.1], 6)) return;
    p.lavaT = n; p.lavaBurn = n + LAVA.burn * 1000; p.lavaBurnT = n + 300;
    if (p.isBot) { p.vel[1] = Math.max(p.vel[1], LAVA.hop); p.onGround = false; p.pos[1] += 0.05; }
    else if (!told) this.knock(p, [0, LAVA.hop, 0], 'lava');
    this.broadcast({ t: 'sizzle', id: p.id, p: p.pos.map(r2) });
    this.damage(p, LAVA.dmg, null, 'lava');
  }
  // bots: knife when out of bullets or up close, revolver otherwise. melee bots run straight at you, and faster
  botChaosThink(b, t, n) {
    const ai = b.ai;
    if (!this.chaosKit) { if (Math.abs(ai.strafeDir) !== 1) ai.strafeDir = Math.sign(ai.strafeDir) || 1; ai.spd = 1; return; }
    if (this.livesOn && b.oitc) {
      const want = b.oitc.bullets > 0 && !(t && t.alive && dist3(t.pos, b.pos) < 2.5) ? 'revolver' : 'knife';
      if (b.w !== want) { b.w = want; ai.nextShot = Math.max(ai.nextShot, n + 300); }
    }
    const melee = WEAPONS[b.w].kind === 'melee';
    ai.strafeDir = (Math.sign(ai.strafeDir) || 1) * (melee ? 0.3 : 1);
    ai.spd = melee ? WEAPONS[b.w].speedMul || 1.1 : 1;
    if (melee && this.hookMul > 1 && t && t.alive && dist3(t.pos, b.pos) > 12) ai.nextHook = Math.min(ai.nextHook || 0, n + 500);
  }
  // true = handled. melee: swing if they're in reach. one in the chamber: only take a shot that's worth the bullet
  botChaosFire(b, t, D) {
    const w = WEAPONS[b.w], n = now();
    // a beat to look around first, and nobody fresh off a spawn, or small maps empty out in seconds
    if (this.livesOn && (n - (b.spawnT || 0) < 2500 || n - (t.spawnT || 0) < 1500)) return true;
    if (w.kind === 'melee') {
      b.ai.nextShot = n + (w.cd * 1000) / D.rate;
      this.broadcast({ t: 'fx', k: 'swing', w: b.w, id: b.id, a: eyeOf(b).map(r2) });
      if (dist3(b.pos, t.pos) > w.range + 0.9) return true;
      if (this.livesOn && Math.random() < Math.min(0.7, (0.35 * D.err) / 0.045)) return true; // one in the chamber: knife whiffs too
      const to = norm([t.pos[0] - b.pos[0], t.pos[1] - b.pos[1], t.pos[2] - b.pos[2]]) || [0, 0, 1];
      this.hurt(t, b, b.w, w.dmg, [to[0] * w.kb, to[1] * w.kb + (w.kbUp || 0), to[2] * w.kb]);
      return true;
    }
    if (!this.livesOn || b.w !== 'revolver' || !b.oitc) return false;
    if (b.oitc.bullets <= 0 || dist3(b.pos, t.pos) > (b.ai.diff === 'hard' ? 40 : 26)) return true;
    b.oitc.bullets--;
    b.ai.nextShot = n + 700;
    const cp = Math.cos(b.pitch), o = eyeOf(b);
    // bots flub some shots (still costs the bullet): easy ~70%, normal ~35%, hard ~14%, so 3 lives last a while
    const miss = Math.random() < Math.min(0.7, (0.35 * D.err) / 0.045);
    const d = spreadDir([-Math.sin(b.yaw) * cp, Math.sin(b.pitch), -Math.cos(b.yaw) * cp], (w.spread || 0) + D.err * 0.6 + (miss ? 0.14 : 0));
    const mh = raycast(o, d, w.range, this.boxes);
    let maxT = mh ? mh.t : w.range, victim = null, head = false;
    for (const p of this.players.values()) {
      if (p === b || !p.alive) continue;
      for (const hb of playerBoxes(p.pos)) { const h = rayBox(o, d, hb, maxT); if (h && h.t < maxT) { maxT = h.t; victim = p; head = hb.head; } }
    }
    this.broadcast({ t: 'fx', k: 'shot', w: 'revolver', id: b.id, s: [[...o, o[0] + d[0] * maxT, o[1] + d[1] * maxT, o[2] + d[2] * maxT].map(r2)] });
    if (victim) this.hurt(victim, b, 'revolver', 999, null, { hs: head });
    return true;
  }
  // floor is lava bots: look before stepping off something, and if they're in it, jump and grapple back to safe ground
  botLava(b, wx, wz, jump, t) {
    const s = surfaces(this.map), ai = b.ai, n = now(), e = eyeOf(b);
    const hookAt = (to, minT, ms) => {
      const L = Math.hypot(...to) || 1, h = raycast(e, to.map((v) => v / L), HOOK.range, this.boxes);
      if (h && h.t > minT) { ai.hook = { point: h.point, len: h.t, until: n + ms }; b.g = h.point; }
    };
    const inLava = b.onGround && onLava(s, this.boxes, b.pos);
    if (inLava || (!b.onGround && !ai.hook && b.vel[1] < 0 && lavaBelow(s, this.boxes, [b.pos[0], b.pos[1] + 0.2, b.pos[2]], 30))) {
      const safe = nearestSafe(s, b.pos, 45);
      if (!safe) return [wx, wz, true];
      const dx = safe[0] - b.pos[0], dz = safe[2] - b.pos[2], l = Math.hypot(dx, dz) || 1;
      if (!ai.hook && n >= (ai.lavaHookT || 0)) { ai.lavaHookT = n + 700; hookAt([dx, safe[1] + 2.5 - e[1], dz], 2, 2200); }
      return [dx / l, dz / l, true];
    }
    if (b.onGround && (wx || wz) && lavaBelow(s, this.boxes, [b.pos[0] + wx * 1.4, b.pos[1] + 0.5, b.pos[2] + wz * 1.4], 12)) {
      // lava ahead: stop at the edge, sometimes grapple over toward whoever we're after
      if (t && t.alive && !ai.hook && n >= (ai.lavaHookT || 0)) { ai.lavaHookT = n + 1500; if (Math.random() < 0.6) hookAt([t.pos[0] - e[0], t.pos[1] + 4 - e[1], t.pos[2] - e[2]], 6, 2600); }
      return [0, 0, false];
    }
    return [wx, wz, jump];
  }

  tick(dt) {
    const n = now();
    if (this.mode === 'bots' && !this.bomb) this.dropLeavers(false); // (Plant & Defuse: the dead stay till the round ends)
    this.tickRound();
    if (this.isEcon()) this.tickEcon(n);
    this.tickTags(n);
    this.tickItems(dt);
    if (this.mode === 'training') this.trainingStreaks(n);
    this.tickTraps(n);
    for (const b of this.players.values()) if (b.isBot && b.alive) this.stepBot(b, dt);
    this.tickLasso(dt);
    this.tickProjectiles(dt);
    this.tickCarts(dt); // shopping carts: rolling, parked, ridden
    this.tickCrosses();
    this.tickHoles(dt);
    this.tickRig();
    this.tickStatus(dt);
    tickHR(this, dt); // scary forest: the tall guy from HR
    this.tickPeels();
    this.tickMarbles();
    this.tickBalls();
    this.traffic.tick(dt);
    this.tickWaves();
    if (this.sprays.size && this.sprayMap !== this.cfg.map) this.sprays.clear(); // the map changed: its graffiti goes with it
    this.tickChaos(dt, n);
    this.tickGear(n); // laser beams, photo frames, pop quizzes, bots' gadgets
    for (const p of this.players.values()) {
      if (!p.alive && n >= p.respawnAt) {
        if (p.isBot && this.mode === 'coop') continue;
        p.alive = true; p.hp = 100; p.vel = [0, 0, 0]; p.spawnT = n; p.seq++;
        p.pos = p.isBot && p.ai.dummy ? p.ai.dummy.home.slice() : this.pickSpawn(p.isBot, p);
        this.resetLife(p);
        send(p, { t: 'spawn', p: p.pos, q: p.seq });
        this.sendIc(p);
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
    this.rec.frames.push({ s: n, p: ps, odd: this.recOdd, j: [...this.projectiles.values()].map((pr) => [pr.id, pr.k, r2(pr.p[0]), r2(pr.p[1]), r2(pr.p[2]), pr.tip || 0]).concat(this.cartRec()) });
    while (this.rec.frames.length && this.rec.frames[0].s < n - REC_MS) this.rec.frames.shift();
    while (this.rec.ev.length && this.rec.ev[0].s < n - REC_MS) this.rec.ev.shift();
    this.broadcast({ t: 'sn', s: n, p: ps, wave: this.mode === 'coop' ? this.waveInfo() : undefined, round: this.roundInfo() || undefined });
  }
}

installRoyale(Room, { send, movePlayer });
installRig(Room, { now, num, vec3, norm, r2, center, safe, REC_T, WEAPONS }); // the overdrive rig's methods (server/rig.js)
installGear(Room, { now, send, raycast, r2, dist3, eyeOf, lookOf, norm, vec3, stat, liveStats });
installTactical(Room, { send });
installRifles(Room, { now, send });
installPrimaries(Room, { now, send, r2, norm, vec3, REC_T });
installSec(Room, { now, send, raycast, r2, dist3, eyeOf, lookOf, norm, vec3, REC_T, REC_FX }); // after installGear: it wraps gearJoin / tickGear / gearSnap
{ // snapshot flags are one bit each, added by many modules: two on the same bit read as each other (it happened 3 times)
  const seen = new Map();
  for (const [k, v] of Object.entries(FLAGS)) { if (!v || (v & (v - 1))) console.warn(`FLAGS.${k} = ${v} is not a single bit`); else if (seen.has(v)) console.warn(`FLAGS.${k} and FLAGS.${seen.get(v)} share bit ${Math.log2(v)}`); seen.set(v, k); }
}
installEcon(Room, {
  send, cleanSkins, enforceSkins, logErr, BOT_GUNS, navGraph,
  refreshInv: async (p) => { if (p.acct) { const u = await store.get(p.acct.n).catch(() => null); if (u) p.inv = u.inv || {}; } },
});
installLasso(Room);
installZombies(Room, { send, stat, store });
installLobby(Room, { send, rooms });

// ---------------------------------------------------------------- account stats
function stat(p, key, v) {
  if (p.room && p.room.warm) return; // a lobby's warm-up counts for nothing
  if (key === 'xp' && p.m) p.m.xp += v; // this match's xp, for the end screen (guests too: it shows what they'd keep)
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
// Sniper Royalty feats: bit flags in the sniper_feats stat (each feat's bit, see ROYAL_FEATS). d only ever gets bits the
// account doesn't have yet, so liveStats / flushStats can add them up like any other stat (the store ORs them in).
// guests don't keep any: they're told once per feat that it would have counted
const RB = Object.fromEntries(ROYAL_FEATS.map((f) => [f.id, f.bit]));
function royal(p, bits) {
  if (!p.acct) {
    const g = p.royalG || 0, add = bits & ~ROYAL_FEATS.filter((f) => featOn(g, f)).reduce((m, f) => m | f.mask, 0);
    if (add) { p.royalG = (p.royalG || 0) | add; send(p, { t: 'royal', add, all: p.royalG, guest: 1 }); }
    return;
  }
  const have = liveStats(p).sniper_feats || 0, add = ROYAL_FEATS.some((f) => featOn(have, f)) ? bits & ~have & ~ROYAL_FEATS.filter((f) => featOn(have, f)).reduce((m, f) => m | f.mask, 0) : bits & ~have;
  if (!add) return; // (a box you've already ticked, another way, doesn't count again)
  p.acct.d.sniper_feats = (p.acct.d.sniper_feats || 0) | add;
  send(p, { t: 'royal', add, all: have | add });
  checkAch(p); // the last box unlocks the achievement (and with it the Golden Sniper)
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

// real players per mode card: o = Online (quick play is the 'ffa' room), b = With Bots
function lobbyCounts() {
  const o = {}, b = {};
  for (const k of LOBBY.order) { o[k] = 0; b[k] = 0; }
  for (const r of rooms.values()) {
    const n = r.humans().filter((p) => !p.watch).length;
    if (r.id === 'ffa') o.qp += n;
    else if (r.lobby) (r.lobby.online ? o : b)[r.lobby.kind] += n;
    else if (r.qp) b.qp += n;
  }
  return { o, b };
}
function roomFor(mode, ws, cfg) {
  if (!has(MODES, mode)) mode = 'ffa';
  // mode lobbies (home menu ONLINE / WITH BOTS cards): an open lobby for that mode, or a new one. Online Quick Play is the 'ffa' room below
  const lk = cfg && typeof cfg === 'object' && typeof cfg.lobby === 'string' && has(LOBBY.kinds, cfg.lobby) ? cfg.lobby : null;
  if (lk === 'qp' && mode === 'bots') { // With Bots Quick Play: no lobby. drop into a running quick play bots room with a bot to replace, else a new one
    for (const r of rooms.values()) if (r.mode === 'bots' && r.qp && !r.lobby && !r.closed && r.botWant() > 0) return r;
    const r = new Room(`bots:qp:${nextId++}:${Math.random().toString(36).slice(2, 7)}`, 'bots');
    r.qp = true; r.cfg.map = pick(mapsFor('dm', MAPS, MAP_ORDER)) || r.cfg.map;
    rooms.set(r.id, r);
    return r;
  }
  if (lk && lk !== 'qp' && (mode === 'bots' || mode === 'ffa')) {
    for (const r of rooms.values()) if (r.lobbyOpen(mode, lk)) return r;
    const r = new Room(`${mode}:${lk}:${nextId++}:${Math.random().toString(36).slice(2, 7)}`, mode);
    rooms.set(r.id, r);
    r.lobbyInit(lk, mode === 'ffa');
    return r;
  }
  // Play With Bots: join a running bots room playing the same mode that still has a bot to swap out, else start one
  if (mode === 'bots' && cfg && typeof cfg === 'object' && has(GAMES, cfg.game)) {
    for (const r of rooms.values()) if (r.mode === 'bots' && r.game === cfg.game && r.botWant() > 0 && !r.closed) return r;
  }
  const id = mode === 'ffa' || mode === 'coop' ? mode : `${mode}:${nextId}:${Math.random().toString(36).slice(2, 7)}`;
  if (!rooms.has(id)) rooms.set(id, new Room(id, mode));
  return rooms.get(id);
}

// ---------------------------------------------------------------- sockets
wss.on('connection', (ws) => {
  let me = null;
  ws.isAlive = true;
  ws.budget = 400; ws.budgetT = now();
  // ws reports bad frames (too big, broken compression) as 'error': without a listener that would crash the process
  ws.on('error', (e) => logErr('ws', e && e.message));
  ws.on('pong', () => { ws.isAlive = true; if (ws.pingT) ws.rtt = now() - ws.pingT; });
  ws.on('message', (data) => {
    // a generous per-connection budget (a busy client sends ~100/s): floods get dropped, not relayed to the room
    const t = now();
    ws.budget = Math.min(400, ws.budget + (t - ws.budgetT) * 0.3); ws.budgetT = t;
    if (ws.budget < 1) return;
    ws.budget--;
    let m;
    try { m = JSON.parse(data); } catch { return; }
    if (!m || typeof m !== 'object' || Array.isArray(m) || tooDeep(m)) return;
    if (!me) {
      if (m.t !== 'join' || ws.joining) return;
      ws.joining = true;
      for (const k of Object.keys(m)) if (k[0] === '_') delete m[k]; // _acct, _inv, _name...: only the server sets those
      (async () => {
        const u = m.token ? await accounts.verify(m.token).catch(() => null) : null;
        if (u) {
          const base = {}; for (const k of STAT_KEYS) base[k] = u[k] || 0;
          base.cats = catsOf(u.inv); // hidden cats petted (inv.lore, not a column: flushStats never sends it)
          m._name = u.name; m._acct = { n: u.name_lower, d: {}, since: now(), base, achs: achievementsFrom(base), lore: loreOf(u.inv) };
          m._level = levelOf(u.xp); m._inv = u.inv || {}; m._achs = m._acct.achs;
        }
        else {
          const want = clean(m.name, 16);
          if (want && await store.get(want.toLowerCase()).catch(() => null)) m._name = want.slice(0, 10) + ' (guest)';
        }
        if (ws.readyState !== 1) return;
        const room = roomFor(m.mode, ws, m.cfg);
        me = room.addHuman(ws, m);
      })().catch((e) => { console.error('join failed', e); ws.close(); });
      return;
    }
    try { me.room.handle(me, m); } catch (e) { logErr('msg ' + (typeof m.t === 'string' ? m.t.slice(0, 12) : '?'), e); }
  });
  ws.on('close', safe('close', () => {
    if (!me) return;
    console.log(`- ${me.name} (#${me.id}) <- ${me.room.id}`);
    me.room.remove(me);
  }));
});

// maze maps build their bots' walk graph (and lanes) the first time they're asked for: do it now, not mid-match
for (const m of Object.values(MAPS)) if (m.graph) void m.nav;

// ---------------------------------------------------------------- loops
const TICK = 1 / 60;
setInterval(() => { for (const r of rooms.values()) try { r.tick(TICK); } catch (e) { logErr('tick ' + r.mode, e); } }, TICK * 1000);
setInterval(() => { for (const r of rooms.values()) try { if (r.players.size) r.snapshot(); } catch (e) { logErr('snapshot ' + r.mode, e); } }, 50);
setInterval(() => {
  for (const ws of wss.clients) {
    if (!ws.isAlive) { ws.terminate(); continue; }
    ws.isAlive = false;
    ws.pingT = now();
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
// floor is lava + duck rain size up every map once at startup, so a vote never stalls a live match working it out
setImmediate(() => { for (const id of MAP_ORDER) surfaces(MAPS[id]); });
// save everyone's stats right now (used on shutdown and by the desktop app when it closes)
export function shutdown() {
  for (const r of rooms.values()) for (const p of r.players.values()) flushStats(p);
  if (store.flushNow) store.flushNow();
}
// a failed last save must not keep the process alive (the uncaughtException handler below would swallow it)
for (const sig of ['SIGINT', 'SIGTERM']) process.on(sig, () => { try { shutdown(); } catch (e) { logErr('shutdown', e); } setTimeout(() => process.exit(0), 300); });
// last resort: a bug in one room (or one callback) gets logged instead of dropping every room
// (a server that can't even start, e.g. the port is taken, still stops; the desktop app reports that itself)
process.on('uncaughtException', (e) => { logErr('uncaught', e); if (!server.listening && !process.versions.electron) process.exit(1); });
process.on('unhandledRejection', (e) => logErr('unhandled', e));
