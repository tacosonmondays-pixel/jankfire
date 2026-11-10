// gadget items keep their charges and cooldown through death and item swaps; grenades still refill on respawn
// (start a server first: PORT=3100 node server.js; then node tests/itemcarry_ws.cjs 3100)
const WS = require('ws');
const port = process.argv[2] || 3100;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
function client(name) {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, got: [], id: 0, q: 0, ic: null, dead: false };
  ws.on('message', (d) => { const m = JSON.parse(d); if (m.t === 'welcome') { c.id = m.id; c.q = m.q; if (m.ic) c.ic = m.ic; } if (m.t === 'spawn') { c.q = m.q; c.dead = false; } if (m.t === 'ic') c.ic = m; if (m.t === 'kill' && m.v === c.id) c.dead = true; if (m.t !== 'sn') c.got.push(m); });
  c.send = (m) => ws.send(JSON.stringify(m));
  c.place = (p) => c.send({ t: 's', q: c.q, p, v: [0, 0, 0], y: 0, x: 0, w: 'ar' });
  c.die = async () => { for (let i = 0; i < 40 && !c.dead; i++) { c.place([0, -400, 0]); await sleep(150); } await sleep(300); for (let i = 0; i < 60 && c.dead; i++) { c.send({ t: 'respawn' }); await sleep(200); } await sleep(400); };
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'join', name, mode: 'ffa' }); setTimeout(() => res(c), 800); }));
}
(async () => {
  const A = await client('gadget'), B = await client('target');
  const y = 70;
  A.send({ t: 'itemsel', i: 'laptop' }); await sleep(300);
  ok(A.ic && A.ic.i === 'laptop' && A.ic.n === 1, 'laptop: 1 charge to start');
  A.place([600, y, 0]); B.place([600, y, -10]); await sleep(250);
  A.send({ t: 'item', i: 'laptop', o: [600, y + 1.6, 0], d: [0, 0, -1] }); await sleep(400);
  ok(A.ic.n === 0 && A.ic.next > 30000, `laptop used: 0 left, ${Math.round(A.ic.next / 1000)} s to the next`);
  await A.die();
  ok(!A.dead, 'died and respawned');
  ok(A.ic && A.ic.i === 'laptop' && A.ic.n === 0 && A.ic.next > 20000, `after respawn: still 0 left, ${A.ic && Math.round(A.ic.next / 1000)} s to go (death did not refill it)`);
  // the swap trick: away and back in the first seconds of a life
  A.send({ t: 'itemsel', i: 'frag' }); await sleep(450); A.send({ t: 'itemsel', i: 'laptop' }); await sleep(450);
  ok(A.ic.i === 'laptop' && A.ic.n === 0, 'swapping to another item and back does not refill it either');
  // a grenade still comes back full on respawn
  A.send({ t: 'itemsel', i: 'frag' }); await sleep(450);
  const before = A.ic.n;
  A.place([600, y, 0]); await sleep(200);
  A.send({ t: 'item', i: 'frag', o: [600, y + 1.6, 0], d: [0, 1, 0] }); await sleep(500);
  const used = A.ic.n;
  await A.die();
  ok(A.ic.i === 'frag' && A.ic.n === 2, `frag: ${before} -> ${used} after a throw -> ${A.ic.n} after respawn (refilled, like before)`);
  console.log(fails ? `${fails} FAILED` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
