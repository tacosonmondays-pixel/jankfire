// hit reach vs a faked velocity, over plain ws: a hit's range slack grows with speed, and the speed used to be whatever
// the client claimed (v: [90000, 0, 0] = a knife from 12 m, an AR past its range). now it's no faster than the server's
// snapshots saw you move (speedOf), so honest fast movers still land.  node tests/reach_ws.cjs [port]
const WS = require('ws');
const path = require('path');
const { spawn } = require('child_process');
const port = Number(process.argv[2]) || 3198; // (the knife from 12 m was already refused by the melee checks; kept as a guard)
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
const srv = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(port), JF_TRAFFIC: 'off' }, stdio: ['ignore', 'pipe', 'pipe'] });
let log = ''; srv.stdout.on('data', (d) => { log += d; }); srv.stderr.on('data', (d) => { log += d; });
process.on('exit', () => srv.kill());
function client(name) {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, got: [], id: 0, q: 0 };
  ws.on('message', (d) => { const m = JSON.parse(d); if (m.t === 'welcome') { c.id = m.id; c.q = m.q; } if (m.t === 'spawn') c.q = m.q; if (m.t === 'dmg') c.got.push(m); });
  c.send = (m) => ws.send(JSON.stringify(m));
  c.place = (p, v = [0, 0, 0], w = 'ar') => c.send({ t: 's', q: c.q, p, v, y: 0, x: 0, w });
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'join', name, mode: 'ffa' }); setTimeout(() => res(c), 900); }));
}
(async () => {
  for (let i = 0; i < 40 && !log.includes('localhost:' + port); i++) await sleep(250);
  const A = await client('Reacher'); let B = await client('Target'), nT = 0;
  const fresh = async () => { B.ws.close(); B = await client('Target' + (++nT)); }; // (a full-hp target each time: a dead one takes no hits)
  const Y = 90;
  // hold both in place (with A's claimed velocity) for a while, then fire a few hits; count B's damage
  const trial = async (aAt, bAt, v, w, hit, aMove) => {
    await fresh();
    for (let t = 0; t < 1500; t += 100) { A.place(aMove ? aMove(t) : aAt, v, w); B.place(bAt); await sleep(100); }
    A.got.length = 0; B.got.length = 0;
    for (let i = 0; i < 3; i++) { if (aMove) A.place(aMove(1500 + i * 100), v, w); else A.place(aAt, v, w); B.place(bAt); hit(); await sleep(500); }
    await sleep(300);
    return [...A.got, ...B.got].filter((m) => m.to === B.id).length;
  };
  const knife = () => { A.send({ t: 'fire', w: 'knife', o: [700, Y + 1.6, 0], d: [0, 0, -1] }); A.send({ t: 'hit', w: 'knife', to: B.id, d: [0, 0, -1] }); };
  const ar = () => A.send({ t: 'hit', w: 'ar', to: B.id, d: [0, 0, -1], n: 1, h: 0 });
  // honest speed: A really moving 30 m/s sideways (the snapshots see it), B 14 m away: 2.6 + 6 + 30 * 0.3 = 17.6 m of reach
  const run = (t) => [640 + 30 * t / 1000, Y, 0];
  const runB = (t) => [run(t)[0], Y, -14];
  let honest = 0;
  for (let t = 0; t < 1500; t += 100) { A.place(run(t), [30, 0, 0], 'knife'); B.place(runB(t)); await sleep(100); }
  A.got.length = 0; B.got.length = 0;
  for (let i = 0; i < 3; i++) { const t = 1500 + i * 150; A.place(run(t), [30, 0, 0], 'knife'); B.place(runB(t)); A.send({ t: 'fire', w: 'knife', o: [run(t)[0], Y + 1.6, 0], d: [0, 0, -1] }); A.send({ t: 'hit', w: 'knife', to: B.id, d: [0, 0, -1] }); await sleep(150); }
  await sleep(400); honest = [...A.got, ...B.got].filter((m) => m.to === B.id).length;
  ok(honest > 0, `honest 30 m/s runner, knife at 14 m: lands (${honest})`);
  const FAKE = [90000, 0, 0];
  ok(await trial([700, Y, 0], [700, Y, -12], [0, 0, 0], 'knife', knife) === 0, 'honest knife from 12 m: nothing (control)');
  ok(await trial([700, Y, 0], [700, Y, -12], FAKE, 'knife', knife) === 0, 'knife from 12 m with a fake 90 km/s velocity: nothing');
  ok(await trial([700, Y, 0], [700, Y, -330], FAKE, 'ar', ar) === 0, 'AR from 330 m (range 300) with a fake velocity: nothing');
  ok(await trial([700, Y, 0], [700, Y, -303], [0, 0, 0], 'ar', ar) > 0, 'honest AR at 303 m (range 300 + 6 m slack): lands');
  ok(!/Error|uncaught/i.test(log), 'no server errors ' + (log.match(/.*Error.*/) || [''])[0]);
  A.ws.close(); B.ws.close();
  console.log(fails ? `${fails} FAILED` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
