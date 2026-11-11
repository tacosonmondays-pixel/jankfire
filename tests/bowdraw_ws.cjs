// the bow's draw is checked by the server: an arrow can't claim more draw than the time since the last one
// (start a server first: PORT=3100 node server.js; then node tests/bowdraw_ws.cjs 3100)
const WS = require('ws');
const port = process.argv[2] || 3100;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
(async () => {
  const ws = new WS(`ws://localhost:${port}/ws`), got = []; let me = 0, q = 0, at = null; // at: where the server spawned us (standing out in the void gets you killed mid-test)
  ws.on('message', (d) => { const m = JSON.parse(d); if (m.t === 'welcome') { me = m.id; q = m.q; at = m.pos; } if (m.t === 'spawn') { q = m.q; at = m.p; } if (m.t !== 'sn') got.push(m); });
  const send = (m) => ws.send(JSON.stringify(m));
  await new Promise((r) => ws.on('open', r));
  send({ t: 'join', name: 'archer', mode: 'ffa' }); await sleep(800);
  const o = [at[0], at[1] + 1.6, at[2]], d = [0, 0.6, -0.8]; // up a bit: nobody to hit
  const hold = async (ms) => { for (let t = 0; t < ms; t += 100) { send({ t: 's', q, p: at, v: [0, 0, 0], y: 0, x: 0, w: 'bow' }); await sleep(100); } };
  const arrows = () => got.filter((m) => m.t === 'ps' && m.k === 'bow' && m.o === me);
  const speed = (a) => Math.hypot(...a.v);
  const fast = (a) => speed(a) > 110; // a full draw is 115 m/s (149 on a power tip); half a draw is about 80 (104)
  await hold(1500);
  send({ t: 'fire', w: 'bow', o, d, c: 1 }); await hold(300);
  ok(arrows().length === 1 && fast(arrows()[0]), 'a full draw after a real wait flies at full speed: ' + (arrows()[0] ? speed(arrows()[0]).toFixed(0) : 'none') + ' m/s');
  // spam: claim a full draw every 300 ms
  const before = arrows().length;
  for (let i = 0; i < 3; i++) { send({ t: 'fire', w: 'bow', o, d, c: 1 }); await hold(300); } // (3: the quiver runs dry after a few)
  const spam = arrows().slice(before);
  ok(spam.length === 3 && spam.every((a) => !fast(a)), `full draws claimed 0.3 s apart come out as half draws: ${spam.map((a) => speed(a).toFixed(0)).join(', ')} m/s`);
  // an honest rhythm (cooldown + 0.7 s draw) still gets the full draw
  await hold(1100);
  const b2 = arrows().length; send({ t: 'fire', w: 'bow', o, d, c: 1 }); await hold(300);
  ok(arrows().length === b2 + 1 && fast(arrows()[b2]), 'drawing for real again: full speed ' + (arrows()[b2] ? speed(arrows()[b2]).toFixed(0) : 'none') + ' m/s');
  for (const bad of [{ t: 'fire', w: 'bow', o, d, c: 'x' }, { t: 'fire', w: 'bow', o, d, c: 1e99 }, { t: 'fire', w: 'bow', o, d, c: -5 }]) { send(bad); await hold(350); }
  ok(ws.readyState === 1, 'garbage draw values: still connected');
  console.log(fails ? `${fails} FAILED` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
