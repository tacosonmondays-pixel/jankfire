// Plant & Defuse: every gun you carry into a round starts it full (magazine + reserve). not mid-round, not guns on the floor
// (start a server: JF_FFA_BOMB=2 JF_BUY_TIME=3 JF_BOMB_ROUND=7 JF_START_MONEY=9000 PORT=3100 node server.js; then node tests/restock_ws.cjs 3100)
const WS = require('ws');
const port = process.argv[2] || 3100;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
function client(name) {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, got: [], id: 0, q: 0, at: null, inv: null, round: 0, drops: [], dead: false };
  ws.on('message', (d) => {
    const m = JSON.parse(d);
    if (m.t === 'sn') return;
    if (m.t === 'welcome') { c.id = m.id; c.q = m.q; c.at = m.pos; }
    if (m.t === 'spawn') { c.q = m.q; c.at = m.p; c.dead = false; }
    if (m.t === 'inv' && !m.off) c.inv = m;
    if (m.t === 'am' && c.inv) for (const x of Object.values(c.inv.sl)) if (x && x.u === m.u) { x.m = m.m; x.r = m.r; }
    if (m.t === 'eround') c.round = m.n;
    if (m.t === 'dr+') c.drops.push(m);
    if (m.t === 'kill' && m.v === c.id) c.dead = true;
    c.got.push(m);
  });
  c.send = (m) => ws.send(JSON.stringify(m));
  c.gun = (s) => c.inv && c.inv.sl[s];
  c.stay = () => { if (!c.dead && c.at) c.send({ t: 's', q: c.q, p: c.at, v: [0, 0, 0], y: 0, x: 0, w: (c.gun('primary') || c.gun('secondary')).id }); };
  c.shoot = async (w, n) => { for (let i = 0; i < n; i++) { c.send({ t: 'fire', w, o: [c.at[0], c.at[1] + 1.6, c.at[2]], d: [0, 1, 0] }); await sleep(130); } await sleep(250); };
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'join', name, mode: 'ffa' }); setTimeout(() => res(c), 800); }));
}
(async () => {
  const A = await client('survivor'), B = await client('goner');
  const tick = setInterval(() => { A.stay(); B.stay(); }, 100);
  const until = async (f, ms) => { for (let t = 0; t < ms && !f(); t += 100) await sleep(100); return f(); };
  ok(await until(() => A.round === 1 && A.inv && B.inv, 6000), 'round 1 started with the economy on');
  A.send({ t: 'buy', k: 'w', id: 'ar' }); B.send({ t: 'buy', k: 'w', id: 'ar' });
  await until(() => A.gun('primary') && B.gun('primary'), 2000);
  const full = A.gun('primary') && [A.gun('primary').m, A.gun('primary').r];
  ok(full && full[0] === 30 && full[1] === 90, `bought a rifle: ${full}`);
  await sleep(3300); // the barriers drop
  // the survivor: 10 out of the magazine, a reload (so the reserve goes down), 12 more, and half the pistol's magazine
  await A.shoot('ar', 10); A.send({ t: 'rl', w: 'ar' }); await sleep(2600); await A.shoot('ar', 12); await A.shoot('pistol', 6);
  const a1 = [A.gun('primary').m, A.gun('primary').r, A.gun('secondary').m];
  ok(a1[0] === 18 && a1[1] === 80 && a1[2] === 6, `survivor ends round 1 on rifle ${a1[0]}+${a1[1]}, pistol ${a1[2]}`);
  // the goner shoots a few and jumps into the void
  await B.shoot('ar', 5);
  const spot = B.at; B.at = [spot[0], -400, spot[2]];
  ok(await until(() => B.dead, 8000), 'the other one died');
  ok(A.gun('primary').m === 18 && A.gun('primary').r === 80, 'nothing refills mid-round');
  ok(await until(() => A.round === 2, 15000), 'round 2 started');
  await sleep(600);
  const a2 = [A.gun('primary').m, A.gun('primary').r, A.gun('secondary').m, A.gun('secondary').r];
  ok(a2[0] === 30 && a2[1] === 90, `survivor's kept rifle starts round 2 full: ${a2[0]}+${a2[1]}`);
  ok(a2[2] === 12 && a2[3] === 36, `and the pistol: ${a2[2]}+${a2[3]}`);
  ok(!B.gun('primary') && B.gun('secondary').m === 12 && B.gun('secondary').r === 36, `the dead one lost the rifle, pistol is full: ${JSON.stringify(B.inv.sl.primary)} ${B.gun('secondary').m}+${B.gun('secondary').r}`);
  B.send({ t: 'buy', k: 'w', id: 'ar' }); await until(() => B.gun('primary'), 2000);
  ok(B.gun('primary') && B.gun('primary').m === 30 && B.gun('primary').r === 90, 'their rebuy is full');
  await sleep(3000);
  // mid-round: drop a half-used rifle and pick it up again
  await A.shoot('ar', 7);
  A.drops.length = 0; A.send({ t: 'drop', s: 'primary' });
  ok(await until(() => A.drops.length && !A.gun('primary'), 2000) && A.drops[0].m === 23, `dropped rifle lies there with ${A.drops[0] && A.drops[0].m} rounds`);
  await sleep(1400);
  if (!A.gun('primary')) A.send({ t: 'pick', id: A.drops[0].id });
  ok(await until(() => A.gun('primary'), 2500) && A.gun('primary').m === 23 && A.gun('primary').r === 90, `picked back up mid-round: ${A.gun('primary') && A.gun('primary').m}+${A.gun('primary') && A.gun('primary').r} (not refilled)`);
  for (const bad of [{ t: 'rl', w: 7 }, { t: 'rl', w: 'ar', n: 1e99 }, { t: 'buy', k: 'w', id: { a: 1 } }]) A.send(bad);
  await sleep(300);
  ok(A.ws.readyState === 1, 'garbage input: still connected');
  clearInterval(tick);
  console.log(fails ? `${fails} FAILED` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
