// Scales of Justice ranged SUMMONS over plain ws: ring under the target, pillar a second later, verdict damage,
// stepping out saves you, the recharge, and it needs the scales in hand
// (start a server first: PORT=3100 node server.js; then node tests/gavel_ws.cjs 3100)
const WS = require('ws');
const port = process.argv[2] || 3100;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
function client(name) {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, got: [], id: 0, q: 0, hp: 100 };
  ws.on('message', (d) => { const m = JSON.parse(d); if (m.t === 'welcome') { c.id = m.id; c.q = m.q; } if (m.t === 'spawn') c.q = m.q; if (m.t === 'sn') { const r = m.p.find((x) => x[0] === c.id); if (r) c.hp = r[10]; return; } c.got.push(m); });
  c.send = (m) => ws.send(JSON.stringify(m));
  c.place = (p, w = 'ar') => c.send({ t: 's', q: c.q, p, v: [0, 0, 0], y: 0, x: 0, w });
  c.take = (t, f) => { const i = c.got.findIndex((m) => m.t === t && (!f || f(m))); return i < 0 ? null : c.got.splice(i, 1)[0]; };
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'join', name, mode: 'ffa' }); setTimeout(() => res(c), 800); }));
}
(async () => {
  const A = await client('judge'), B = await client('accused');
  const y = 90, hold = (ms, bp) => (async () => { for (let t = 0; t < ms; t += 100) { A.place([700, y, 0], 'scales'); B.place(bp); await sleep(100); } })();
  const cast = () => A.send({ t: 'gavel', o: [700, y + 1.6, 0], d: [0, 0, -1] });
  // 1. not holding the scales: nothing
  A.place([700, y, 0], 'ar'); B.place([700, y, -15]); await sleep(250);
  cast(); await sleep(300);
  ok(!A.take('fx', (m) => m.k === 'gavel'), 'no scales in hand: no summons');
  // 2. scales out, aimed at B: a ring under B, then the pillar hits B
  await hold(300, [700, y, -15]);
  cast(); await hold(400, [700, y, -15]);
  const ring = A.take('fx', (m) => m.k === 'gavel');
  ok(ring && ring.to === B.id && Math.abs(ring.p[2] + 15) < 0.5 && ring.d === 1, 'ring opens under the accused ' + JSON.stringify(ring && { to: ring.to, p: ring.p, r: ring.r, d: ring.d }));
  await hold(1100, [700, y, -15]);
  const boom = A.take('fx', (m) => m.k === 'gavelx');
  ok(boom && boom.hit.includes(B.id), 'pillar lands and hits them');
  const vd = A.take('fx', (m) => m.k === 'verdict' && m.id === B.id);
  await sleep(200);
  ok(vd && B.hp < 100 && B.hp >= 30, `verdict x${vd && vd.m}: accused at ${B.hp} HP (20 x verdict, never a one-shot from full)`);
  // 3. recharge: a second cast straight away is refused
  cast(); await hold(300, [700, y, -15]);
  ok(!A.take('fx', (m) => m.k === 'gavel') && A.take('gavel', (m) => m.cd > 5000), 'recharging: refused, with the time left');
  // 4. garbage never crashes
  for (const bad of [{ t: 'gavel' }, { t: 'gavel', d: 'x', o: {} }, { t: 'gavel', d: [NaN, 1e99, null], o: [1e99, 0, 0] }]) { A.send(bad); await sleep(120); }
  ok(A.ws.readyState === 1, 'garbage input: still connected');
  // 5. after the recharge: summon again, the accused walks out, the pillar hits nobody
  console.log('     (waiting out the 10 s recharge)');
  await hold(9800, [700, y, -15]);
  const hp0 = B.hp; A.got.length = 0;
  cast(); await hold(300, [700, y, -15]);
  ok(A.take('fx', (m) => m.k === 'gavel'), 'second summons after the recharge');
  await hold(1200, [706, y, -15]); // 6 m to the side: out of the 2.3 m ring
  const boom2 = A.take('fx', (m) => m.k === 'gavelx');
  await sleep(200);
  ok(boom2 && boom2.hit.length === 0 && B.hp === hp0, `stepped out: the pillar hit nobody (HP still ${B.hp})`);
  console.log(fails ? `${fails} FAILED` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
