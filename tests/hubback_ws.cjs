// BACK TO THE LOBBY (server/hubback.js): an offline single-mode match from the hub ends with PLAY AGAIN / LOBBY, not the
// quick play vote; when the timer runs out you're sent back ('go'); PLAY AGAIN from everyone starts the same mode
// straight away; an offline quick play (no hub) still votes; junk is ignored
// (start a server with short rounds first: PORT=3100 JF_ROUND_TIME=6 node server.js; then node tests/hubback_ws.cjs 3100)
const WS = require('ws');
const port = process.argv[2] || 3100;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
function player(name, cfg) {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, got: [], game: null };
  ws.on('message', (d) => { const m = JSON.parse(d); if (['round', 'vote', 'hubback'].includes(m.t)) c.got.push({ ...m, at: Date.now() }); if (m.t === 'welcome') c.game = m.cfg && m.cfg.game; });
  c.send = (m) => ws.send(JSON.stringify(m));
  c.wait = async (f, ms) => { const t = Date.now(); while (Date.now() - t < ms) { const x = c.got.find(f); if (x) return x; await sleep(100); } return null; };
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'join', name, mode: 'bots', cfg }); setTimeout(() => res(c), 800); }));
}
(async () => {
  // 1: a hub pick (plant & defuse's lobby, dm here so the clock ends it): no vote, PLAY AGAIN / LOBBY, then 'go'
  const A = await player('solo', { priv: true, game: 'dm', map: 'crate', bots: 0, hub: 'bomb' });
  const over = await A.wait((m) => m.t === 'round' && m.over, 20000);
  ok(!!over, 'the match ends (short rounds)');
  const open = await A.wait((m) => m.t === 'hubback' && m.k === 'open', 3000);
  ok(open && open.mode === 'bomb', 'the end screen gets PLAY AGAIN / LOBBY for its lobby ' + JSON.stringify(open));
  A.send({ t: 'hbagain', on: 'yes' }); A.send({ t: 'hbagain' }); A.send({ t: 'vote', i: 0 });
  const go = await A.wait((m) => m.t === 'hubback' && m.k === 'go', (over ? over.next : 20000) + 4000);
  ok(go && go.mode === 'bomb' && go.at - over.at >= over.next - 500, `when the clock runs out: back to the lobby (${go ? go.at - over.at : '-'} ms, the end screen said ${over && over.next})`);
  ok(!A.got.some((m) => m.t === 'vote'), 'no quick play vote at all (junk PLAY AGAIN ignored)');
  await sleep(1500);
  ok(!A.got.some((m) => m.t === 'round' && m.start && m.at > over.at), 'and no new match starts behind them');
  A.ws.close();
  // 2: PLAY AGAIN: the same mode, straight away
  const B = await player('again', { priv: true, game: 'dm', map: 'crate', bots: 0, hub: 'isle' });
  const o2 = await B.wait((m) => m.t === 'round' && m.over, 20000);
  await B.wait((m) => m.t === 'hubback' && m.k === 'open', 3000);
  B.send({ t: 'hbagain', on: true });
  const cnt = await B.wait((m) => m.t === 'hubback' && m.k === 'again', 2000);
  ok(cnt && cnt.n === 1 && cnt.of === 1 && cnt.total >= 600 && cnt.total <= 2000, 'PLAY AGAIN counted, with the new countdown ' + JSON.stringify(cnt));
  B.send({ t: 'hbagain', on: false }); await sleep(150);
  ok(B.got.filter((m) => m.t === 'hubback' && m.k === 'again').length === 1, 'flipping it back inside 250 ms: ignored');
  const st = await B.wait((m) => m.t === 'round' && m.start && m.at > o2.at, 3000);
  ok(st && st.game === 'dm' && st.at - o2.at < o2.next - 1000, `everyone said PLAY AGAIN: the same mode starts now (${st ? st.at - o2.at : '-'} ms in)`);
  ok(!B.got.some((m) => m.t === 'hubback' && m.k === 'go'), 'and nobody is sent back');
  B.ws.close();
  // 3: offline quick play (no hub) keeps its vote; a bad hub value is no hub
  const C = await player('qp', { priv: true, game: 'dm', map: 'crate', bots: 0, hub: 'qp' });
  await C.wait((m) => m.t === 'round' && m.over, 20000);
  const v = await C.wait((m) => m.t === 'vote', 3000);
  ok(!!v && !C.got.some((m) => m.t === 'hubback'), 'offline quick play still gets the vote');
  C.send({ t: 'hbagain', on: true }); await sleep(400);
  ok(!C.got.some((m) => m.t === 'hubback'), 'PLAY AGAIN in a voting room: ignored');
  C.ws.close();
  console.log(fails ? `${fails} FAILED` : 'all ok');
  process.exit(fails ? 1 : 0);
})();
