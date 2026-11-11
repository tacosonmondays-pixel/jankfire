// the bow's damage: a full draw to the body is 70 (two kill), a headshot is 105 (one kills), a quick tap is weak
// (start a server with plain tips only: JF_ARROW_TIP=regular PORT=3100 node server.js; then node tests/bowdmg_ws.cjs 3100)
const WS = require('ws');
const port = process.argv[2] || 3100;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
function client(name) {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, got: [], id: 0, q: 0, hp: 100, alive: 1, at: null };
  ws.on('message', (d) => { const m = JSON.parse(d); if (m.t === 'welcome') { c.id = m.id; c.q = m.q; c.at = m.pos; } if (m.t === 'spawn') { c.q = m.q; c.at = m.p; } if (m.t === 'sn') { const r = m.p.find((x) => x[0] === c.id); if (r) { c.hp = r[10]; c.alive = r[11]; } return; } c.got.push(m); });
  c.send = (m) => ws.send(JSON.stringify(m));
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'join', name, mode: 'ffa' }); setTimeout(() => res(c), 800); }));
}
(async () => {
  const A = await client('archer'), B = await client('target');
  // the archer stays on its spawn; the target stands 8 m in front of it (-z), a little up so nothing is in the way
  const a = A.at.slice(); a[1] += 6; const b = [a[0], a[1], a[2] - 8];
  const hold = async (ms) => { for (let t = 0; t < ms; t += 100) { A.send({ t: 's', q: A.q, p: a, v: [0, 0, 0], y: 0, x: 0, w: 'bow' }); if (B.alive) B.send({ t: 's', q: B.q, p: b, v: [0, 0, 0], y: 0, x: 0, w: 'ar' }); await sleep(100); } };
  const shoot = async (c, aimY) => { const o = [a[0], a[1] + 1.6, a[2]], to = [b[0] - o[0], b[1] + aimY - o[1], b[2] - o[2]], l = Math.hypot(...to), hp = B.hp; A.send({ t: 'fire', w: 'bow', o, d: to.map((v) => v / l), c }); await hold(700); return hp - B.hp; };
  const kills = () => A.got.filter((m) => m.t === 'kill' && m.v === B.id && m.k === A.id).length;
  const fresh = async () => { B.send({ t: 'respawn' }); for (let i = 0; i < 60 && !B.alive; i++) { await hold(100); if (i % 10 === 9) B.send({ t: 'respawn' }); } await hold(3200); }; // back up, spawn protection over
  await hold(1500);
  const body = await shoot(1, 1.0);
  ok(body === 70, `full draw to the body: ${body} HP (want 70)`);
  await hold(900);
  const k0 = kills(); await shoot(1, 1.0); await hold(400);
  ok(kills() === k0 + 1, 'a second full body arrow kills');
  await fresh();
  const tap = await shoot(0.15, 1.0);
  ok(tap === 36, `a quick tap from full HP: ${tap} HP (30 + 15% of the way to 70 = 36)`);
  await hold(900); await shoot(1, 1.0); await hold(400); // finish it off for a clean headshot test
  await fresh();
  const hp0 = B.hp, k1 = kills();
  await shoot(1, 1.75);
  ok(hp0 === 100 && kills() === k1 + 1, `full draw to the head from ${hp0} HP: ${kills() > k1 ? 'one-shot kill' : 'they lived with ' + B.hp} (105)`);
  console.log(fails ? `${fails} FAILED` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
