// RESET (respawn) over plain ws: a plain reset, a reset after being hurt hands the attacker the kill, the wait between
// resets, garbage input, and a Plant & Defuse bots room says no
// (start a server first: PORT=3100 node server.js; then node tests/reset_ws.cjs 3100)
const WS = require('ws');
const port = process.argv[2] || 3100;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
function client(name, join) {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, got: [], id: 0, q: 0, hp: 100, alive: 1 };
  ws.on('message', (d) => { const m = JSON.parse(d); if (m.t === 'welcome') { c.id = m.id; c.q = m.q; } if (m.t === 'spawn') c.q = m.q; if (m.t === 'sn') { const r = m.p.find((x) => x[0] === c.id); if (r) { c.hp = r[10]; c.alive = r[11]; } return; } c.got.push(m); });
  c.send = (m) => ws.send(JSON.stringify(m));
  c.place = (p, w = 'ar') => c.send({ t: 's', q: c.q, p, v: [0, 0, 0], y: 0, x: 0, w });
  c.take = (t, f) => { const i = c.got.findIndex((m) => m.t === t && (!f || f(m))); return i < 0 ? null : c.got.splice(i, 1)[0]; };
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'join', name, mode: 'ffa', ...join }); setTimeout(() => res(c), 800); }));
}
(async () => {
  const A = await client('judge'), B = await client('quitter');
  const y = 90, hold = (ms, bw = 'ar') => (async () => { for (let t = 0; t < ms; t += 100) { A.place([100, y, 0], 'scales'); if (B.alive) B.place([100, y, -15], bw); await sleep(100); } })();
  // 1. straight after spawning: not yet
  B.send({ t: 'reset' }); await hold(300);
  const early = B.take('reset');
  ok(early && /RESET IN/.test(early.no) && !B.take('kill', (m) => m.v === B.id), 'fresh spawn: refused for a moment ' + JSON.stringify(early));
  // 2. nobody hurt them: a plain self reset
  await hold(2600);
  B.send({ t: 'reset' }); await hold(400);
  const k1 = B.take('kill', (m) => m.v === B.id);
  ok(k1 && k1.w === 'reset' && !k1.k, 'no attacker: plain reset, nobody gets a kill ' + JSON.stringify(k1));
  // dead: a reset does nothing
  B.send({ t: 'reset' }); await sleep(300);
  ok(!B.take('reset') && !B.take('kill', (m) => m.v === B.id), 'dead: reset ignored');
  B.send({ t: 'respawn' }); for (let i = 0; i < 60 && !B.alive; i++) { await sleep(100); A.place([100, y, 0], 'scales'); if (i % 10 === 9) B.send({ t: 'respawn' }); }
  ok(B.alive, 'respawned after the reset');
  // 3. the wait between resets holds after a respawn
  await hold(2700);
  B.send({ t: 'reset' }); await hold(300);
  const cd = B.take('reset');
  ok(cd && /RESET IN \d+s/.test(cd.no) && cd.ms > 0 && B.alive, 'second reset too soon: refused with the time left ' + JSON.stringify(cd));
  // 4. A hurts B (Scales summons), B rage resets: A gets the kill
  A.got.length = 0;
  A.send({ t: 'gavel', o: [100, y + 1.6, 0], d: [0, 0, -1] }); await hold(1700);
  ok(B.hp < 100, `the judge hurt them first (${B.hp} HP)`);
  await hold(Math.max(0, (cd ? cd.ms : 0) - 1700 + 300));
  B.send({ t: 'reset' }); await hold(400);
  const k2 = A.take('kill', (m) => m.v === B.id);
  ok(k2 && k2.k === A.id && k2.w === 'reset', 'hurt then reset: the attacker gets the kill ' + JSON.stringify(k2));
  // 5. garbage never crashes
  for (const bad of [{ t: 'reset', no: 'x' }, { t: 'reset', a: { b: [1, 2] } }]) { A.send(bad); await sleep(120); }
  ok(A.ws.readyState === 1, 'garbage input: still connected');
  // 6. Plant & Defuse against bots: no reset there
  const C = await client('planter', { mode: 'bots', cfg: { game: 'bomb', bots: 3 } });
  await sleep(3200);
  C.send({ t: 'reset' }); await sleep(400);
  const no = C.take('reset');
  ok(no && /NO RESET/.test(no.no) && !C.take('kill', (m) => m.v === C.id), 'plant & defuse: refused ' + JSON.stringify(no));
  // 7. bots room, normal deathmatch: allowed
  const D = await client('botter', { mode: 'bots', cfg: { bots: 1 } });
  await sleep(3000);
  D.send({ t: 'reset' }); await sleep(500);
  const k3 = D.take('kill', (m) => m.v === D.id), r3 = D.take('reset');
  ok(k3 && k3.w === 'reset', 'bots room: reset works ' + JSON.stringify(k3 || r3));
  console.log(fails ? `${fails} FAILED` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
