// BOARD GAME NIGHT: a party start takes a dropped guest back to their own seat (server/party.js go(), docs/party/DESIGN.md
// 4.5). bob plays at an online table, drops (a bot keeps his seat for his rejoin ticket), then starts board game night
// again from the menu as a party of one: the start sends him back to that table, not a new lobby, and he gets his own
// seat back with its coupons. A guest with a ticket the table doesn't know, and junk tickets, start a fresh lobby.
//   node tests/bgn_partyback_ws.cjs [port=4840]
const { spawn } = require('child_process');
const path = require('path');
const WS = require('ws');
const ROOT = path.join(__dirname, '..');
const port = Number(process.argv[2]) || 4840;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0;
const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
let srv = null;
process.on('exit', () => { try { srv.kill(); } catch { /* gone */ } });
function server(env) {
  srv = spawn(process.execPath, ['server.js'], { cwd: ROOT, env: { ...process.env, PORT: String(port), JF_GRAPH_TTL: '1', ...env }, stdio: ['ignore', 'pipe', 'pipe'] });
  let log = '';
  srv.stdout.on('data', (d) => { log += d; }); srv.stderr.on('data', (d) => { log += d; });
  return new Promise((res, rej) => { const t0 = Date.now(); const iv = setInterval(() => { if (log.includes('JANKFIRE is running')) { clearInterval(iv); res(() => log); } else if (Date.now() - t0 > 20000) { clearInterval(iv); rej(new Error('no server')); } }, 50); });
}
function sock(hello) {
  const ws = new WS(`ws://localhost:${port}/ws`);
  const c = { ws, msgs: [], st: null, id: 0 };
  ws.on('message', (d) => { const m = JSON.parse(d); c.msgs.push(m); if (m.t === 'welcome') c.id = m.id; if (m.t === 'bg' && m.k === 'st') c.st = m.s; });
  ws.on('error', () => {});
  c.send = (o) => { if (ws.readyState === 1) ws.send(JSON.stringify(o)); };
  c.until = (f, ms = 30000) => new Promise((res) => { const t0 = Date.now(); const iv = setInterval(() => { let v = false; try { v = f(); } catch { v = false; } if (v || Date.now() - t0 > ms) { clearInterval(iv); res(!!v); } }, 40); });
  return new Promise((res) => ws.on('open', () => { c.send(hello); res(c); }));
}
const TK = /^[A-Za-z0-9_-]{24}$/;
(async () => {
  const log = await server({ JF_WATCH: '1', JF_LOBBY_WAIT: '1500', JF_BGN_FAST: '10', JF_BGN_ROUNDS: '8', JF_BGN_MGTIME: '8', JF_BGN_COUPONS: '40', JF_BGN_NODUEL: '1' });
  const W = await sock({ t: 'join', name: 'watchP', mode: 'bots', cfg: { lobby: 'bgn' } });
  const A = await sock({ t: 'join', name: 'alice', mode: 'bots', cfg: { lobby: 'bgn' } });
  const B = await sock({ t: 'join', name: 'bob', mode: 'bots', cfg: { lobby: 'bgn' } });
  ok(await W.until(() => W.st && W.st.seats && W.st.seats.some((s) => s.name === 'bob'), 20000), 'the table starts with alice and bob');
  const wb = B.msgs.find((m) => m.t === 'welcome'), bt = wb && wb.bt;
  ok(typeof bt === 'string' && TK.test(bt), 'bob (a guest) was handed a rejoin ticket');
  const room = W.msgs.find((m) => m.t === 'welcome').cfg;
  const b0 = JSON.parse(JSON.stringify(W.st.seats.find((s) => s.name === 'bob')));
  B.ws.close();
  ok(await W.until(() => W.st.seats[b0.i].name === "bob's bot", 4000), "bob dropped: bob's bot keeps his seat");
  // bob's menu connection: a party of one, he leads. junk tickets first (dropped), then his real one
  const H = await sock({ t: 'hub', name: 'bob' });
  ok(await H.until(() => H.msgs.some((m) => m.t === 'party'), 5000), 'the menu connection has a party');
  for (const bad of ['__proto__', 123, 'x'.repeat(25), { a: 1 }, 'aaaaaaaaaaaaaaaaaaaaaaa!']) H.send({ t: 'pbt', bt: bad });
  await sleep(1100);
  H.send({ t: 'pbt', bt });
  await sleep(200);
  H.send({ t: 'pgo', mode: 'bots', cfg: { lobby: 'bgn' } });
  ok(await H.until(() => H.msgs.some((m) => m.t === 'pgo'), 5000), 'the party start answers');
  const go = H.msgs.find((m) => m.t === 'pgo');
  const B2 = await sock({ t: 'join', name: 'bob', mode: go.mode, cfg: go.cfg, back: bt });
  ok(await B2.until(() => B2.st && B2.st.seats && B2.st.seats.some((s) => s.name === 'alice'), 8000), 'the party start took bob back to his table (alice is there), not a new lobby');
  ok(await W.until(() => W.st.seats[b0.i].name === 'bob' && !W.st.seats[b0.i].bot, 30000), 'bob got his own seat back');
  const s1 = W.st.seats[b0.i];
  ok(s1.b === b0.b && s1.c >= 0, 'with his bread (coupons carried on with the bot)');
  // a guest with a ticket the table never gave out: a fresh lobby, never someone else's seat
  const M = await sock({ t: 'hub', name: 'mallory', bt: 'Q'.repeat(24) });
  await M.until(() => M.msgs.some((m) => m.t === 'party'), 5000);
  M.send({ t: 'pgo', mode: 'bots', cfg: { lobby: 'bgn' } });
  ok(await M.until(() => M.msgs.some((m) => m.t === 'pgo'), 5000), "mallory's start answers");
  const gm = M.msgs.find((m) => m.t === 'pgo');
  ok(gm.cfg.room !== go.cfg.room, 'a ticket nobody was given starts a fresh lobby');
  const errs = log().split('\n').filter((l) => /^\s+at |\[(tick|msg|close|snapshot)[^\]]*\]/.test(l));
  ok(!errs.length, 'no server errors' + (errs.length ? ': ' + errs.slice(0, 3).join(' | ') : ''));
  void room;
  console.log(fails ? `${fails} FAILED` : 'all ok');
  process.exit(fails ? 1 : 0);
})().catch((e) => { console.error('FAIL', e); process.exit(1); });
