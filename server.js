// JANKFIRE server: serves the client and runs every match over WebSockets.
// Rooms: one shared Online room, one shared Coop room, and private Bots / Training rooms per player.
// Human movement is client-authoritative (it's a jank game). The server owns damage, kills, projectiles,
// peels, black holes, reverse cards, respawns, bots, coop waves and lobby settings.
import './shared/mapedits/apply.js'; // the owner's shipped map edits, on every map before anything reads them (shared/mapedits)
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import os from 'node:os';
import { spawn } from 'node:child_process';
import { WebSocketServer } from 'ws';
import { makeStore } from './server/store.js';
import { Accounts, levelOf } from './server/accounts.js';
import { owns, SPRAY } from './shared/cosmetics.js';
import { validLook, achievementsFrom, ACHIEVEMENTS } from './shared/looks.js';
import { STAT_KEYS } from './server/store.js';
import { MAPS, MAP_ORDER } from './shared/map.js';
import { warmMap, startGraphSweeper } from './server/graphs.js'; // the bots' walk graphs: built at room start, dropped when no room has used the map for a while
import { VOTE, voteTotal, modeCards, mapCards, tally, winner as voteWinner, eventGame, inQuickPlay } from './shared/vote.js';

import { surfaces, lavaOk, onLava, lavaBelow, nearestSafe, LAVA } from './shared/lava.js';
import { SECRETS, SECRET, canReach, secretsOff, loreOf, catsOf } from './shared/secrets.js'; // hidden NPCs + cats
import { sendStatic } from './server/static.js';
import { browsableServer } from './server/browsable.js'; // the room code the story's solo referee runs in the browser
import { rooms, roomFor, lobbyCounts, humans, flushStats, logErr, safe, tooDeep, clean, now, GRAPH_TTL, GRAPH_SWEEP, setRoomDeps } from './server/room.js'; // the game rooms (class Room + its helpers)

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.PORT) || 3000;
const store = makeStore(ROOT);
setRoomDeps({ store });
const accounts = new Accounts(store);

// ---------------------------------------------------------------- static files
const serverFile = browsableServer(ROOT); // /server/<file>: only server/room.js and what it imports
const ROUTES = [
  ['/vendor/three/', path.join(ROOT, 'node_modules/three/')],
  ['/shared/', path.join(ROOT, 'shared/')],
  ['/mechs/concept/', path.join(ROOT, 'docs/mechs/concept/')], // the mechs' placeholder models (the client's fallback until public/models/x_mech_*.glb lands)
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
  if (url.startsWith('/server/')) { // the story's solo referee (a web worker) runs the real room code
    const file = serverFile(url);
    if (!file) { res.writeHead(404).end('404'); return; }
    fs.stat(file, (err, st) => { if (err || !st.isFile()) { res.writeHead(404).end('404'); return; } sendStatic(req, res, file, st, '.js', MIME['.js']); });
    return;
  }
  for (const [prefix, dir] of ROUTES) {
    if (!url.startsWith(prefix)) continue;
    const file = path.normalize(path.join(dir, url.slice(prefix.length) || 'index.html'));
    if (!file.startsWith(dir)) { res.writeHead(403).end(); return; }
    fs.stat(file, (err, st) => {
      if (err || !st.isFile()) { res.writeHead(404).end('404'); return; }
      sendStatic(req, res, file, st, path.extname(file), MIME[path.extname(file)] || 'application/octet-stream'); // (ETag + gzip: server/static.js)
    });
    return;
  }
  res.writeHead(404).end();
}

const server = http.createServer(serve);
// name cards make some messages chunky: those (and replays) get compressed, the 20 Hz snapshots don't
const wss = new WebSocketServer({ server, path: '/ws', maxPayload: 40000, perMessageDeflate: { threshold: 4096 } });

// ---------------------------------------------------------------- helpers

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

// the bots' walk graphs (and the maze maps' lanes) are built when a room starts on a map (Room.tick -> warmMap), not all
// at boot (together they were ~150 MB of the heap), and dropped once no room has been on a map for GRAPH_TTL
startGraphSweeper(() => rooms.values(), GRAPH_TTL, GRAPH_SWEEP);

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
