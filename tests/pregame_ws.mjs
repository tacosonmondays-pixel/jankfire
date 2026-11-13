// the pre-game deck over plain ws: two people join a mode lobby. everyone (bots too) spawns on the deck, shots / items /
// streaks / t-bags do nothing, a shove is knockback only (cooldown, range, junk ignored), unknown emotes are dropped,
// off the deck (below, beside, below killY) = put back alive, bots wander and nobody dies, both get the same board,
// READY: the match starts and everyone's off the deck onto the map.
// (start a server first: PORT=3100 node server.js; then KIND=bomb|zm|br node tests/pregame_ws.mjs 3100)
import WebSocket from 'ws';
import '../shared/royale.js';
import '../shared/zombies.js';
import { MAPS } from '../shared/map.js';
import { padFor, offPad } from '../shared/pregame.js';
const PORT = process.argv[2] || 3100, KIND = process.env.KIND || 'bomb', MODE = process.env.MODE || 'bots';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const ok = [], bad = [];
const check = (c, msg) => (c ? ok : bad).push(msg);
function client(name) {
  const ws = new WebSocket(`ws://localhost:${PORT}/ws`), C = { ws, msgs: [], name };
  ws.on('message', (d) => { const m = JSON.parse(d); C.msgs.push(m); if (m.t === 'welcome') C.w = m; if (m.t === 'spawn') { C.pos = m.p; C.q = m.q; } if (m.t === 'tp') C.tp = m.p; if (m.t === 'kb') C.kb = m.v; if (m.t === 'pgb') C.board = m; if (m.t === 'lobby') C.lobby = m; if (m.t === 'sn') C.sn = m; if (m.t === 'cfg') C.cfg = m.cfg; });
  C.send = (m) => ws.send(JSON.stringify(m));
  C.open = new Promise((r) => ws.on('open', r));
  return C;
}
const A = client('alpha'), B = client('bravo');
await A.open; A.send({ t: 'join', name: 'alpha', mode: MODE, cfg: { lobby: KIND, bots: 3 } });
await sleep(800);
await B.open; B.send({ t: 'join', name: 'bravo', mode: MODE, cfg: { lobby: KIND, bots: 3 } });
await sleep(1500);
const map = MAPS[A.w.cfg.map]; const pad = padFor(map);
console.log('map', A.w.cfg.map, 'pad', pad.c, 'A', A.w.you && A.w.you.pos, 'lobby', JSON.stringify(A.w.lobby));
check(A.w.lobby && A.w.lobby.pg && A.w.lobby.pg.look === 'deck', 'welcome has pg look');
check(B.w.room === A.w.room || B.w.id !== A.w.id, 'both in');
const row = (C, id) => C.sn && C.sn.p.find((r) => r[0] === id);
const at = (C, id) => { const r = row(C, id); return r ? [r[1], r[2], r[3]] : null; };
// 1. everyone (people and bots) on the deck
await sleep(500);
const all = A.sn.p.map((r) => [r[0], r[1], r[2], r[3]]);
check(all.every((r) => !offPad(pad, [r[1], r[2], r[3]])), `all ${all.length} on the deck: ` + JSON.stringify(all.map((r) => r.slice(1).map(Math.round))));
// 2. stand B next to A, then A shoots B (hit + fire): no damage
let pa = [pad.c[0], pad.c[1], pad.c[2]], pb = [pad.c[0] + 1.5, pad.c[1], pad.c[2]];
const snapA = () => A.send({ t: 's', q: A.w.q, p: pa, v: [0, 0, 0], y: 0, x: 0, w: 'ar' });
const snapB = () => B.send({ t: 's', q: B.w.q, p: pb, v: [0, 0, 0], y: 0, x: 0, w: 'ar' });
for (let i = 0; i < 5; i++) { snapA(); snapB(); await sleep(60); }
A.send({ t: 'fire', w: 'ar', o: [pa[0], pa[1] + 1.6, pa[2]], s: [[pa[0], pa[1] + 1.6, pa[2], pb[0], pb[1] + 1.2, pb[2]]] });
A.send({ t: 'hit', to: B.w.id, w: 'ar', hs: 1, o: [pa[0], pa[1] + 1.6, pa[2]], d: [1, 0, 0] });
A.send({ t: 'item', i: 0 }); A.send({ t: 'deploy', i: 0 }); A.send({ t: 'tbag' }); A.send({ t: 'push', to: B.w.id, w: 'blower' });
await sleep(400);
const hpB = row(A, B.w.id)[10];
check(hpB === 100, 'B hp after shots: ' + hpB);
check(!B.msgs.some((m) => m.t === 'dmg' || m.t === 'kill' || m.t === 'die'), 'no dmg/kill msgs to B');
// 3. shove: B gets a kb; again right away: cooldown
B.kb = null; A.send({ t: 'shove', to: B.w.id }); await sleep(250);
check(Array.isArray(B.kb) && Math.hypot(B.kb[0], B.kb[2]) > 5, 'shove knocks B: ' + JSON.stringify(B.kb));
check(A.msgs.some((m) => m.t === 'pgs' && m.by === A.w.id && m.to === B.w.id), 'pgs broadcast');
B.kb = null; A.send({ t: 'shove', to: B.w.id }); await sleep(200);
check(!B.kb, 'shove cooldown');
// bad shoves: string id, self, far away, junk
await sleep(700);
for (const bad of [{ to: String(B.w.id) }, { to: A.w.id }, { to: 1e9 }, { to: NaN }, { to: { x: 1 } }, {}]) A.send({ t: 'shove', ...bad });
await sleep(200); check(!B.kb, 'junk shoves ignored');
pb = [pad.c[0] + 8, pad.c[1], pad.c[2]]; for (let i = 0; i < 3; i++) { snapB(); await sleep(50); }
A.send({ t: 'shove', to: B.w.id }); await sleep(200); check(!B.kb, 'far shove ignored');
// emote hook: unknown ids dropped
A.send({ t: 'emote', e: 'dab' }); A.send({ t: 'emote', e: '__proto__' }); A.send({ t: 'emote', e: 5 }); await sleep(150);
check(!B.msgs.some((m) => m.t === 'emote'), 'unknown emotes dropped');
// 4. off the deck: B "falls" below it -> tp back; below map killY too: no death
B.tp = null; pb = [pad.c[0], pad.c[1] - 20, pad.c[2]]; snapB(); await sleep(250);
check(B.tp && !offPad(pad, B.tp), 'fell off: put back ' + JSON.stringify(B.tp));
B.tp = null; pb = [pad.c[0] + 40, pad.c[1] + 1, pad.c[2]]; snapB(); await sleep(250);
check(B.tp && !offPad(pad, B.tp), 'walked off sideways: put back');
B.tp = null; pb = [pad.c[0], map.killY - 50, pad.c[2]]; snapB(); await sleep(250);
check(B.tp && row(A, B.w.id)[11] === 1, 'below killY: put back, still alive');
// junk snapshot positions don't crash
B.send({ t: 's', q: B.w.q, p: [NaN, 1, 2], v: [0, 0, 0] }); B.send({ t: 's', q: B.w.q, p: 'x', v: [0, 0, 0] }); B.send({ t: 's', q: B.w.q, p: [1, 2], v: [0, 0, 0] });
await sleep(200);
// 5. bots: wander, no shots, all alive, nobody died
await sleep(3000);
const botsMoved = A.sn.p.filter((r) => r[0] !== A.w.id && r[0] !== B.w.id);
check(botsMoved.every((r) => !offPad(pad, [r[1], r[2], r[3]])), 'bots still on the deck');
check(A.sn.p.every((r) => r[11] === 1 && r[15] === 0), 'nobody dead, no deaths: ' + JSON.stringify(A.sn.p.map((r) => [r[0], r[11], r[15]])));
check(!A.msgs.some((m) => m.t === 'kill'), 'no kill messages at all');
check(!A.msgs.some((m) => m.t === 'fx' && (m.k === 'tracer' || m.k === 'shot')), 'no shot fx');
// 6. the board
check(A.board && Array.isArray(A.board.rows) && A.board.rows.length === Math.min(3, A.sn.p.length), 'board: ' + JSON.stringify(A.board));
check(B.board && JSON.stringify(B.board.rows) === JSON.stringify(A.board.rows), 'B has the same board');
// 7. READY both -> 5 s -> match starts: everyone off the deck onto the map
A.send({ t: 'ready', on: true }); B.send({ t: 'ready', on: true });
for (let i = 0; i < 40 && !(A.lobby && A.lobby.end); i++) await sleep(250);
check(A.lobby && A.lobby.end, 'match started');
await sleep(800);
const after = A.sn.p.map((r) => [r[1], r[2], r[3]]);
check(after.every((p) => offPad(pad, p)), 'everyone left the deck: ' + JSON.stringify(after.map((p) => p.map(Math.round))));
check(!A.sn.round.warm, 'no warm in the round info');
// damage works again
console.log('OK', ok.length, '\n  ' + ok.join('\n  '));
console.log('BAD', bad.length, '\n  ' + bad.join('\n  '));
process.exit(bad.length ? 1 : 0);
