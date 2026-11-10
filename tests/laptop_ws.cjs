// laptop item, server logic over plain ws (start a server first: PORT=3100 node server.js; then node tests/laptop_ws.cjs 3100)
const WS = require('ws');
const port = process.argv[2] || 3100;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
function client(name) {
  const ws = new WS(`ws://localhost:${port}/ws`); ws.on('close', (code) => console.log(name, 'CLOSED', code)); const c = { ws, name, got: [], id: 0, q: 0, pos: null };
  ws.on('message', (d) => { let m; try { m = JSON.parse(d); } catch { return; } if (m.t === 'welcome') { c.id = m.id; c.q = m.q; c.pos = m.pos; } if (m.t === 'spawn') { c.q = m.q; c.pos = m.p; } if (m.t !== 'sn') { c.got.push(m); } });
  c.send = (m) => ws.send(JSON.stringify(m));
  c.take = (t, f) => { const i = c.got.findIndex((m) => m.t === t && (!f || f(m))); return i < 0 ? null : c.got.splice(i, 1)[0]; };
  c.place = (p, yaw = 0) => { c.pos = p; c.send({ t: 's', q: c.q, p, v: [0, 0, 0], y: yaw, x: 0, w: 'ar' }); };
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'join', name, mode: 'ffa' }); setTimeout(() => res(c), 700); }));
}
(async () => {
  const A = await client('adman'), B = await client('victim');
  ok(A.id && B.id, 'both joined');
  A.send({ t: 'itemsel', i: 'laptop' }); B.send({ t: 'itemsel', i: 'reverse' });
  await sleep(300);
  // high up in the air, 12 m apart on z: nothing in the way. A at z=0 looking down -z at B
  const y = 60; A.place([0, y, 0]); B.place([0, y, -12]);
  await sleep(200);
  const use = (d, o) => A.send({ t: 'item', i: 'laptop', o: o || [0, y + 1.6, 0], d });
  // 1. aimed the wrong way: no target, charge comes back
  use([0, 0, 1]); await sleep(300);
  ok(A.take('ads!'), 'aimed away: NO SIGNAL');
  const ic = A.got.filter((m) => m.t === 'ic').pop(); ok(ic && ic.i === 'laptop' && ic.n === 1, 'charge refunded (n=' + (ic && ic.n) + ')');
  ok(!B.take('ads'), 'victim got nothing');
  // 3. aimed at B: B gets the ads, everyone gets the fx
  await sleep(500); B.got.length = 0;
  use([0, 0, -1]); await sleep(300);
  const ad = B.take('ads'); ok(ad && ad.by === A.id && ad.n === 5 && ad.dur === 7, 'victim got ads ' + JSON.stringify(ad));
  ok(A.take('fx', (m) => m.k === 'ads' && m.id === A.id && m.to === B.id), 'fx broadcast');
  const ic2 = A.got.filter((m) => m.t === 'ic').pop(); ok(ic2 && ic2.n === 0, 'charge spent');
  // 4. no charge left: nothing more
  await sleep(500); use([0, 0, -1]); await sleep(300); ok(!B.take('ads'), 'no charge: nothing');
  // 5. garbage input never crashes or serves
  for (const bad of [{ t: 'item', i: 'laptop', d: 'x' }, { t: 'item', i: 'laptop', d: [NaN, 0, 0], o: [1e99, 0, 0] }, { t: 'item', i: 'laptop', d: { a: 1 } }, { t: 'item', i: '__proto__' }, { t: 'item' }]) { A.send(bad); await sleep(450); }
  ok(A.ws.readyState === 1, 'garbage input: still connected, server alive');
  // 6. reverse card: the ads come home
  const C = await client('adman2'), D = await client('mirror');
  C.send({ t: 'itemsel', i: 'laptop' }); D.send({ t: 'itemsel', i: 'reverse' }); await sleep(300);
  C.place([300, y, 0]); D.place([300, y, -10]); await sleep(200);
  D.send({ t: 'item', i: 'reverse', o: [300, y + 1.6, -10], d: [0, 0, 1] }); await sleep(250);
  C.send({ t: 'item', i: 'laptop', o: [300, y + 1.6, 0], d: [0, 0, -1] }); await sleep(300);
  const back = C.take('ads'); ok(back && back.by === D.id, 'reverse card: the user gets their own ads, credited to the card holder');
  ok(!D.take('ads'), 'reverse card holder sees no ads');
  console.log(fails ? `${fails} FAILED` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
