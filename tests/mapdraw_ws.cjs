// the big map's PENCIL over real sockets (server/pings.js onDraw). BATTLE ISLAND (JF_GAME=island, strokes live 6 s
// via JF_DRAW_LIFE): A + B share a squad, C is the other squad. A stroke / a wipe reaches A and B, never C; points snap
// to 0.5 m and repeats drop; 64 points max; junk is dropped whole; 4 strokes per 3 s; a 7th live stroke rubs out the
// oldest (gone); once strokes fade (the life runs out) they stop counting. Training: only you see yours.
// starts its own server: node tests/mapdraw_ws.cjs [port]
const WS = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const port = Number(process.argv[2]) || 3176;
const LIFE = 6000;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };

function client(name, join = {}) {
  const c = { name, id: 0, got: [], ws: new WS(`ws://localhost:${port}/ws`) };
  c.send = (o) => { if (c.ws.readyState === 1) c.ws.send(typeof o === 'string' ? o : JSON.stringify(o)); };
  c.ws.on('message', (d) => {
    const m = JSON.parse(d);
    if (m.t === 'welcome') c.id = m.id;
    if (m.t === 'isle' && m.k === 'sq') c.sqList = m.l;
    if (m.t === 'mdraw') c.got.push(m);
  });
  c.ws.on('open', () => c.send({ t: 'join', name, mode: 'ffa', ...join }));
  return c;
}
const lines = (c) => c.got.filter((m) => m.pts);
const clear = (cs) => { for (const c of cs) c.got.length = 0; };
async function until(fn, max = 8000) { const t = Date.now(); while (Date.now() - t < max) { if (fn()) return true; await sleep(50); } return !!fn(); }
const zig = (n, x0 = 0) => Array.from({ length: n }, (_, i) => [x0 + i * 2, (i % 2) * 3]).flat();

(async () => {
  const srv = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(port), JF_TRAFFIC: 'off', JF_GAME: 'island', JF_DRAW_LIFE: String(LIFE) }, stdio: ['ignore', 'pipe', 'pipe'] });
  let err = ''; srv.stderr.on('data', (d) => { err += d; }); srv.stdout.on('data', (d) => { if (/Error|uncaught/i.test(String(d))) err += d; });
  process.on('exit', () => srv.kill());
  for (let i = 0; i < 60; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }
  const A = client('Alfa'); await sleep(400);
  const C = client('Charlie'); await sleep(250);
  const B = client('Bravo');
  const all = [A, B, C];
  await until(() => all.every((c) => c.id && c.sqList && all.every((o) => c.sqList.some((r) => r[0] === o.id))), 15000);
  const sq = new Map((A.sqList || []).map((r) => [r[0], r[1]]));
  ok(sq.get(A.id) && sq.get(A.id) === sq.get(B.id) && sq.get(A.id) !== sq.get(C.id), 'island: A + B share a squad, C is the other one');

  // ---------------------------------------------------------- the squad sees it, the other squad doesn't; snapped + deduped
  clear(all);
  A.send({ t: 'mdraw', pts: [1.26, 2.24, 1.3, 2.2, 10, 10], sq: sq.get(C.id), by: C.id });
  await until(() => lines(A).length && lines(B).length, 3000); await sleep(400);
  const a = lines(A)[0], b = lines(B)[0];
  ok(a && b && a.id === b.id && a.by === A.id, 'squad: A and B get the stroke ' + JSON.stringify(b));
  ok(b && JSON.stringify(b.pts) === JSON.stringify([1.5, 2, 10, 10]), 'points snap to 0.5 m and a repeat is dropped');
  ok(!lines(C).length, 'the other squad never sees it (extra sq / by fields ignored)');
  await sleep(300);
  A.send({ t: 'mdraw', pts: zig(64) });
  await until(() => lines(B).length >= 2, 3000);
  await sleep(300); clear(all);
  A.send({ t: 'mdraw', pts: zig(64, 100) }); await sleep(300);
  A.send({ t: 'mdraw', pts: zig(65) }); await sleep(300);
  A.send({ t: 'mdraw', pts: [310, 0, 320, 0] }); await sleep(300); // jankburg: the zone's 300 m + 5 % + 8 m of slack = 323
  A.send({ t: 'mdraw', pts: [310, 0, 330, 0] }); await sleep(500);
  const L0 = lines(B).map((m) => m.pts.length / 2 + (m.pts[2] === 320 ? '@320' : ''));
  ok(L0.length === 2 && L0[0] === '64', 'points cap: a 64-point stroke gets through, a 65-point one is dropped ' + JSON.stringify(L0));
  ok(L0.length === 2 && L0[1] === '2@320', 'bounds: a stroke to the edge (x 320) gets through, one past it (x 330) is dropped ' + JSON.stringify(L0));

  // ---------------------------------------------------------- wipe mine
  await sleep(300); clear(all);
  A.send({ t: 'mdraw', clr: true }); await sleep(600);
  ok(!A.got.length && !B.got.length, 'wipe: clr must be exactly 1');
  A.send({ t: 'mdraw', clr: 1 });
  await until(() => B.got.some((m) => m.clr), 3000); await sleep(300);
  ok(A.got.some((m) => m.clr && m.by === A.id) && B.got.some((m) => m.clr && m.by === A.id) && !C.got.length, 'wipe: A and B hear it, C doesn\'t');
  clear(all); await sleep(600);
  A.send({ t: 'mdraw', clr: 1 }); await sleep(500);
  ok(!A.got.length && !B.got.length, 'wipe with nothing to wipe: no message');

  // ---------------------------------------------------------- junk: dropped whole, nobody hears anything
  await sleep(3200); clear(all);
  const junk = [
    { t: 'mdraw' }, { t: 'mdraw', pts: 'lol' }, { t: 'mdraw', pts: { 0: 1, 1: 2, 2: 3, 3: 4, length: 4 } }, { t: 'mdraw', pts: [1, 2, 3] }, { t: 'mdraw', pts: [1, 2] },
    { t: 'mdraw', pts: zig(65) }, { t: 'mdraw', pts: [1, 2, '3', 4] }, { t: 'mdraw', pts: [1, 2, null, 4] }, { t: 'mdraw', pts: [1, 2, [3], 4] }, { t: 'mdraw', pts: [1, 2, { x: 3 }, 4] },
    '{"t":"mdraw","pts":[1,2,1e999,4]}', '{"t":"mdraw","pts":[1,2,-1e999,4]}', { t: 'mdraw', pts: [1, 2, 5000, 4] }, { t: 'mdraw', pts: [0, 0, 0, -400] }, { t: 'mdraw', pts: [3, 3, 3.1, 3.1, 2.9, 2.9] },
    '{"t":"mdraw","__proto__":{"pts":[1,2,3,4]}}', { t: 'mdraw', pts: [1, 2, 3, 4], x: { a: { b: { c: { d: { e: { f: 1 } } } } } } }, { t: 'mdraw', pts: Array(4000).fill(1) }, { t: 'mdraw', clr: '1' }, { t: 'mdraw', clr: [1] },
  ];
  for (const j of junk) { A.send(j); await sleep(230); }
  await sleep(500);
  ok(!A.got.length && !B.got.length && !C.got.length, `junk: ${junk.length} bad strokes, none relayed ${JSON.stringify(A.got).slice(0, 200)}`);
  ok(A.ws.readyState === 1, 'junk: still connected');

  // ---------------------------------------------------------- rate limit: 4 per 3 s, 200 ms apart
  await sleep(LIFE + 300); clear(all); // (and let everything fade so the cap starts at 0)
  A.send({ t: 'mdraw', pts: [0, 0, 5, 5] }); A.send({ t: 'mdraw', pts: [0, 0, 6, 6] }); // the 2nd is too quick
  await sleep(250);
  for (let i = 0; i < 5; i++) { A.send({ t: 'mdraw', pts: [0, 0, 10 + i, 0] }); await sleep(250); }
  await sleep(400);
  const got = lines(B).map((m) => m.pts[2]);
  ok(got.length === 4 && got[0] === 5 && got[1] === 10 && got[3] === 12, 'rate limit: 4 per 3 s, the too-quick 2nd dropped ' + JSON.stringify(got));
  ok(A.got.filter((m) => m.no).length === 1 && !B.got.some((m) => m.no), 'rate limit: the drawer hears "slow down" once');

  // ---------------------------------------------------------- the cap: a 7th live stroke rubs out the oldest
  await until(() => false, 1900); // the window opens again ~3 s after the 1st
  for (let i = 0; i < 3; i++) { A.send({ t: 'mdraw', pts: [0, 0, 20 + i, 0] }); await sleep(250); }
  await sleep(500);
  const L = lines(B);
  ok(L.length === 7 && L[6].gone === L[0].id && !L.slice(0, 6).some((m) => m.gone), `cap: the 7th live stroke says gone = the 1st (${L.length} strokes, gone ${L[6] && L[6].gone} vs ${L[0] && L[0].id})`);
  ok(lines(A).length === 7 && lines(A)[6].gone === L[0].id, 'cap: the drawer hears the same');
  // ---------------------------------------------------------- fade: once they're past their life they stop counting
  await sleep(LIFE + 300); clear(all);
  for (let i = 0; i < 6; i++) { A.send({ t: 'mdraw', pts: [0, 0, 30 + i, 0] }); await sleep(i === 3 ? 3100 : 250); }
  await until(() => lines(B).length >= 6, 4000); await sleep(300);
  ok(lines(B).length === 6 && !lines(B).some((m) => m.gone), 'fade: old strokes faded, 6 new ones and nothing rubbed out');

  // ---------------------------------------------------------- solo: training only hears itself
  const T = client('Trainee', { mode: 'training' });
  await until(() => T.id, 8000); await sleep(1200); clear(all);
  T.send({ t: 'mdraw', pts: [0, 0, 4, 4] });
  await until(() => lines(T).length, 3000); await sleep(400);
  ok(lines(T).length === 1 && lines(T)[0].by === T.id, 'training: you see your own stroke');
  ok(!all.some((c) => c.got.length), 'training: nobody else does');
  T.send({ t: 'mdraw', pts: [0, 0, 900, 0] }); await sleep(400);
  ok(lines(T).length === 1, 'training: a stroke off the range map is dropped');
  ok(!/Error|uncaught/i.test(err), 'no server errors ' + err.slice(0, 300));
  for (const c of [...all, T]) c.ws.close();
  console.log(fails ? `${fails} FAILED` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
