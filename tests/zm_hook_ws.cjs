// "cooldown on hook for zombies too!": the grapple runs on charges in Zombies, the same rule as Jank Royale
// (shared/royale.js BR.hook: 2 charges, one back every 8 s), counted by the server so a client can't skip it.
// (start a zombies server first: JF_GAME=zm JF_ZM_SWIPE=0 JF_ZM_REST=600000 PORT=3100 node server.js; then node tests/zm_hook_ws.cjs 3100)
const WS = require('ws');
const port = process.argv[2] || 3100;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
function client(name) {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, got: [], id: 0, q: 0, pos: null, seen: {} };
  ws.on('message', (d) => { const m = JSON.parse(d); if (m.t === 'welcome') { c.id = m.id; c.q = m.q; } if (m.t === 'spawn') { c.q = m.q; c.pos = m.p || c.pos; } if (m.t === 'sn') { for (const e of m.p) c.seen[e[0]] = e; return; } c.got.push(m); });
  c.send = (m) => ws.send(JSON.stringify(m));
  c.take = (t, f) => { const i = c.got.findIndex((m) => m.t === t && (!f || f(m))); return i < 0 ? null : c.got.splice(i, 1)[0]; };
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'join', name, mode: 'ffa' }); setTimeout(() => res(c), 1500); }));
}
(async () => {
  const A = await client('swinger'), B = await client('watcher');
  const at = [0, 0.1, 16];
  // hold a rope to g (or none) for ms, the way the game sends it: in every snapshot
  const hold = async (g, ms) => { for (let t = 0; t < ms; t += 80) { A.send({ t: 's', q: A.q, p: at, v: [0, 0, 0], y: 0, x: 0, w: 'revolver', g: g || 0, f: 0 }); B.send({ t: 's', q: B.q, p: [2, 0.1, 16], v: [0, 0, 0], y: 0, x: 0, w: 'revolver', g: 0, f: 0 }); await sleep(80); } };
  const roped = () => { const e = B.seen[A.id]; return !!(e && e.some((v) => Array.isArray(v) && v.length === 3 && Math.abs(v[1] - 3) < 0.01)); }; // (does the watcher see A's rope point, y = 3?)
  await hold(0, 400);
  A.got.length = 0;
  // 1. two ropes straight away: both allowed, each spends a charge
  await hold([10, 3, 16], 400); const a1 = A.take('zhook'); const saw1 = roped();
  await hold(0, 250);
  await hold([-10, 3, 16], 400); const a2 = A.take('zhook');
  ok(a1 && !a1.no && a2 && !a2.no, 'two ropes in a row: both go through ' + JSON.stringify([a1 && a1.h, a2 && a2.h]));
  ok(saw1, 'the other player sees the rope');
  ok(a2 && a2.h && a2.h.n < 1, 'the server says no charge is left (' + (a2 && a2.h && a2.h.n.toFixed(2)) + ')');
  // 2. a third at once: refused, and nobody sees a rope however long the client keeps sending it
  await hold(0, 250);
  await hold([10, 3, 26], 600); const a3 = A.take('zhook');
  ok(a3 && a3.no === 1, 'a third rope straight away: refused');
  await hold([10, 3, 26], 500);
  ok(!roped(), 'a client that keeps sending the rope anyway: the server shows nobody a rope');
  // 3. the same rope held for ages costs nothing more (a swing is one charge)
  A.got.length = 0;
  await hold(0, 8600); // one charge back (8 s)
  await hold([10, 3, 16], 300); const a4 = A.take('zhook');
  ok(a4 && !a4.no, 'after the recharge: a rope again');
  A.got.length = 0;
  await hold([10, 3, 16], 1500);
  ok(!A.take('zhook'), 'holding that rope: no more charges spent');
  // 4. garbage never crashes, never spends
  for (const g of ['x', [1, 2], [NaN, 1, 2], { a: 1 }, [1e999, 0, 0]]) { A.send({ t: 's', q: A.q, p: at, v: [0, 0, 0], y: 0, x: 0, w: 'revolver', g, f: 0 }); await sleep(100); }
  ok(A.ws.readyState === 1 && !A.take('zhook', (m) => !m.no), 'garbage rope points: still connected, nothing spent');
  console.log(fails ? `${fails} FAILED` : 'all ok');
  process.exit(fails ? 1 : 0);
})();
