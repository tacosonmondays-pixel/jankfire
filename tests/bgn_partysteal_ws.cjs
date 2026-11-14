// BOARD GAME NIGHT: nobody gets a seat a bot is keeping for someone else (server/party.js go(), server/bgn.js
// bgnSeatQueue). alice, bob, carol and dave sit at an online table; carol and bob drop (their bots keep the seats). bob
// makes a party from the menu, mallory joins it by code, bob presses START: mallory never sat at that table, so the
// party gets a normal lobby, not bob's table. then mallory leaves the party, bob starts alone and hands his ticket to
// mallory: she gets into the table room but no kept seat. bob comes back with his own rejoin ticket and gets his own
// seat; carol's stays held the whole time.
//   node tests/bgn_partysteal_ws.cjs [port=4850]
const { spawn } = require('child_process');
const path = require('path');
const WS = require('ws');
const ROOT = path.join(__dirname, '..');
const port = Number(process.argv[2]) || 4850;
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
const party = (h) => h.msgs.filter((m) => m.t === 'party').pop();
const gos = (h) => h.msgs.filter((m) => m.t === 'pgo');
(async () => {
  const log = await server({ JF_WATCH: '1', JF_LOBBY_WAIT: '1500', JF_BGN_FAST: '10', JF_BGN_ROUNDS: '8', JF_BGN_MGTIME: '8', JF_BGN_COUPONS: '40', JF_BGN_NODUEL: '1' });
  const W = await sock({ t: 'join', name: 'watchP', mode: 'bots', cfg: { lobby: 'bgn' } });
  const P = {};
  for (const n of ['alice', 'bob', 'carol', 'dave']) P[n] = await sock({ t: 'join', name: n, mode: 'bots', cfg: { lobby: 'bgn' } });
  ok(await W.until(() => W.st && W.st.seats && ['alice', 'bob', 'carol', 'dave'].every((n) => W.st.seats.some((s) => s.name === n)), 25000), 'alice, bob, carol and dave sit at one table');
  const bt = P.bob.msgs.find((m) => m.t === 'welcome').bt;
  const b0 = JSON.parse(JSON.stringify(W.st.seats.find((s) => s.name === 'bob'))), c0 = W.st.seats.find((s) => s.name === 'carol').i;
  P.carol.ws.close(); P.bob.ws.close();
  ok(await W.until(() => W.st.seats[b0.i].name === "bob's bot" && W.st.seats[c0].name === "carol's bot", 5000), 'carol and bob dropped: bots keep both seats');
  const kept = () => W.st.seats[c0].name === "carol's bot" && W.st.seats[c0].bot;
  // bob's menu: a party, mallory joins by code, bob starts
  const Hb = await sock({ t: 'hub', name: 'bob', bt });
  ok(await Hb.until(() => party(Hb) && party(Hb).code, 5000), "bob's menu has a party with a code");
  const Hm = await sock({ t: 'hub', name: 'mallory' });
  await Hm.until(() => party(Hm), 5000);
  Hm.send({ t: 'pjoin', code: party(Hb).code });
  ok(await Hb.until(() => party(Hb).ms && party(Hb).ms.length === 2, 5000), 'mallory joined bob\'s party');
  Hb.send({ t: 'pgo', mode: 'bots', cfg: { lobby: 'bgn' } });
  ok(await Hm.until(() => gos(Hm).length && gos(Hb).length, 5000), 'the party start answers both');
  const gm = gos(Hm)[0], gb = gos(Hb)[0];
  ok(gm.cfg.room === gb.cfg.room, 'the party goes to one room together');
  const M = await sock({ t: 'join', name: 'mallory', mode: gm.mode, cfg: gm.cfg });
  ok(await M.until(() => M.st && M.st.seats && M.st.seats.some((s) => s.name === 'mallory'), 15000), 'mallory sits at a table');
  ok(!M.st.seats.some((s) => s.name === 'alice' || s.name === 'dave'), "...a fresh one, not bob's table (the steal is refused)");
  ok(!W.st.seats.some((s) => s.name === 'mallory'), "mallory never shows up at bob's table");
  M.ws.close();
  // mallory leaves the party; bob starts alone (back to his table) and forwards his ticket to her
  Hm.send({ t: 'pleave' });
  ok(await Hb.until(() => party(Hb).ms && party(Hb).ms.length === 1, 5000), 'mallory left the party');
  await sleep(3100); // (pgo: once per 3 s)
  Hb.send({ t: 'pgo', mode: 'bots', cfg: { lobby: 'bgn' } });
  ok(await Hb.until(() => gos(Hb).length === 2, 5000), "bob's solo start answers");
  const g2 = gos(Hb)[1];
  ok(g2.cfg.room !== gm.cfg.room, "bob alone goes back to his table's room");
  const M2 = await sock({ t: 'join', name: 'mallory', mode: g2.mode, cfg: g2.cfg });
  ok(await M2.until(() => M2.st && M2.st.seats && M2.st.seats.some((s) => s.name === 'alice'), 8000), "with bob's forwarded ticket mallory gets into the table room");
  const t0 = W.msgs.length;
  await sleep(12000); // turns go by: the seat queue runs between them
  const seenM = W.msgs.slice(t0).some((m) => m.t === 'bg' && m.k === 'st' && m.s.seats.some((s) => s.name === 'mallory'));
  ok(!seenM && !W.st.seats.some((s) => s.name === 'mallory'), "but no seat: the kept ones aren't hers");
  ok(W.st.seats[b0.i].name === "bob's bot" && kept(), "bob's and carol's seats are still held");
  // bob comes back with his own rejoin ticket
  const B2 = await sock({ t: 'join', name: 'bob', mode: 'bots', cfg: { lobby: 'bgn' }, back: bt });
  ok(await W.until(() => W.st.seats[b0.i].name === 'bob' && !W.st.seats[b0.i].bot, 30000), 'bob gets his own seat back');
  ok(W.st.seats[b0.i].b === b0.b, 'with his bread');
  await sleep(4000);
  ok(kept(), "carol's seat stays held for carol");
  ok(!W.st.seats.some((s) => s.name === 'mallory'), 'mallory still has no seat');
  const errs = log().split('\n').filter((l) => /^\s+at |\[(tick|msg|close|snapshot)[^\]]*\]/.test(l));
  ok(!errs.length, 'no server errors' + (errs.length ? ': ' + errs.slice(0, 3).join(' | ') : ''));
  void B2;
  console.log(fails ? `${fails} FAILED` : 'all ok');
  process.exit(fails ? 1 : 0);
})().catch((e) => { console.error('FAIL', e); process.exit(1); });
