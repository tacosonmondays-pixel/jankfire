// aimed killstreaks are judged on the server: a chicken strike / giant duck marker past 300 m from your eyes, or behind a
// wall, is refused and the streak stays in your tray (a modded client can't drop one on the enemy spawn). a normal one
// still goes off. mech drop by killstreak only calls the loadout frames (paper plane / night shift), not the island heroes.
// over real sockets in Training (the range: a 18 m stone pillar at x 32, z -55). starts its own server:
// node tests/streak_aim_ws.cjs [port]
const WS = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const port = Number(process.argv[2]) || 3191;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
const ROOT = path.join(__dirname, '..');
let log = [], T0 = Date.now();
const ms = () => Date.now() - T0;
const pos = new Map();
function client(name, join) {
  const c = { name, id: 0, q: 1, pos: [32, 0.03, -45], ws: new WS(`ws://localhost:${port}/ws`) };
  c.send = (o) => { if (c.ws.readyState === 1) c.ws.send(JSON.stringify(o)); };
  c.ws.on('message', (d) => {
    const m = JSON.parse(d);
    if (m.t === 'welcome') { c.id = m.id; c.q = m.q; }
    if (m.t === 'spawn' && m.q) c.q = m.q;
    if (m.t === 'sn') { for (const e of m.p) pos.set(e[0], [e[1], e[2], e[3]]); return; }
    log.push([ms(), name, m]);
  });
  c.ws.on('error', () => {});
  c.ws.on('open', () => c.send(join));
  return c;
}
const heard = (pred, since = 0, who) => log.find((e) => e[0] >= since && (!who || e[1] === who) && pred(e[2]));
async function until(fn, max = 8000) { const t = Date.now(); while (Date.now() - t < max) { if (fn()) return true; await sleep(50); } return !!fn(); }
const near = (c) => { const q = pos.get(c.id); return !!q && Math.hypot(q[0] - c.pos[0], q[1] - c.pos[1], q[2] - c.pos[2]) < 0.6; };
const snapper = (cs) => setInterval(() => { for (const c of cs) c.send({ t: 's', q: c.q, p: c.pos, v: [0, 0, 0], y: 0, x: 0, w: 'bread', g: 0, f: 0 }); }, 100);
let srv;
const end = (code) => { if (srv) srv.kill(); setImmediate(() => process.exit(code)); };

(async () => {
  srv = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: ROOT, env: { ...process.env, PORT: String(port), JF_TRAFFIC: 'off', JF_TRAIN_STREAKS: '', JF_MECH_DROP: '0.6' }, stdio: ['ignore', 'pipe', 'pipe'] });
  srv.err = ''; srv.stderr.on('data', (d) => { srv.err += d; }); srv.stdout.on('data', (d) => { if (/Error|uncaught/i.test(String(d))) srv.err += d; });
  for (let i = 0; i < 90; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }

  const A = client('Aimer', { t: 'join', name: 'Aimer', mode: 'training', streaks: ['chickenstrike', 'giantduck', 'mechdrop'], mf: 'trolley' });
  const B = client('Shift', { t: 'join', name: 'Shift', mode: 'training', streaks: ['mechdrop', 'moonboots', 'scythe'], mf: 'nightshift' });
  B.pos = [-10, 0.03, -10];
  const snaps = snapper([A, B]);
  ok(await until(() => A.id && B.id && near(A) && near(B), 10000), 'both in Training, standing where they say');
  const ready = (c, r) => !!heard((m) => m.t === 'streak' && m.earned === r, 0, c.name);
  ok(await until(() => ['chickenstrike', 'giantduck', 'mechdrop'].every((r) => ready(A, r)) && ready(B, 'mechdrop'), 6000), 'training fills the trays');
  await sleep(300);
  const used = (r, t) => heard((m) => m.t === 'streak' && m.reward === r, t, 'Aimer');
  const struck = (t) => heard((m) => m.t === 'fx' && m.k === 'strikeCall', t, 'Aimer');
  const back = (r, t) => heard((m) => m.t === 'streak' && m.earned === r, t, 'Aimer');
  const no = (why, t) => heard((m) => m.t === 'mech' && m.k === 'no' && m.why === why, t, 'Aimer');

  // ---------------------------------------------------------- too far: 455 m down the range
  let t = ms();
  A.send({ t: 'deploy', r: 'chickenstrike', at: [32, 0, -500] });
  await sleep(500);
  ok(!struck(t) && !used('chickenstrike', t), 'chicken strike 455 m away: refused (no birds, not used)');
  ok(!!back('chickenstrike', t) && !!no('too far (300 m max)', t), 'it goes back in the tray, "too far"');
  t = ms();
  A.send({ t: 'deploy', r: 'giantduck', at: [1e5, 0, 1e5] });
  await sleep(400);
  ok(!used('giantduck', t) && !!back('giantduck', t), 'giant duck on the far side of the world: refused, back in the tray');

  // ---------------------------------------------------------- behind the stone pillar (x 30.5..33.5, z -56.5..-53.5, 18 m tall)
  t = ms();
  A.send({ t: 'deploy', r: 'giantduck', at: [32, 0, -59] });
  await sleep(400);
  ok(!used('giantduck', t) && !!back('giantduck', t) && !!no("can't see there", t), 'giant duck behind the pillar: refused, "can\'t see there"');

  // ---------------------------------------------------------- refused then a normal one in the same breath: it never left the tray
  t = ms();
  A.send({ t: 'deploy', r: 'chickenstrike', at: [32, 0, -900] });
  A.send({ t: 'deploy', r: 'chickenstrike', at: [32, 0, -50] }); // 5 m ahead, in plain sight
  await until(() => used('chickenstrike', t), 3000);
  ok(!!struck(t) && !!used('chickenstrike', t), 'a normal chicken strike right after the refused one goes off (it stayed in the tray)');
  ok(await until(() => heard((m) => m.t === 'chat' && /used Chicken Strike/i.test(m.m), t, 'Aimer'), 2000), 'and the chat says so');
  t = ms();
  A.send({ t: 'deploy', r: 'giantduck', at: [32, 1.2, -30] }); // up at chest height in the open (a raycast miss lands in the air)
  await until(() => used('giantduck', t), 2000);
  ok(!!used('giantduck', t), 'a normal giant duck goes off');

  // ---------------------------------------------------------- mech drop by streak: the loadout frames only
  t = ms();
  A.send({ t: 'streaks', list: ['chickenstrike', 'giantduck', 'mechdrop'], mf: 'vending' });
  A.send({ t: 'deploy', r: 'mechdrop', at: [32, 0, -50], mf: 'trolley' });
  ok(await until(() => heard((m) => m.t === 'mech' && m.k === 'call' && m.o === A.id, t), 3000), 'mech drop called');
  const callA = heard((m) => m.t === 'mech' && m.k === 'call' && m.o === A.id, t);
  ok(callA && callA[2].f === 'paperplane', `asking for an island hero frame (trolley) gets the paper plane (got ${callA && callA[2].f})`);
  t = ms();
  B.send({ t: 'deploy', r: 'mechdrop', at: [-10, 0, -16], mf: 'nightshift' });
  ok(await until(() => heard((m) => m.t === 'mech' && m.k === 'call' && m.o === B.id, t), 3000), 'night shift called');
  const callB = heard((m) => m.t === 'mech' && m.k === 'call' && m.o === B.id, t);
  ok(callB && callB[2].f === 'nightshift', `night shift (a loadout frame) still comes as night shift (got ${callB && callB[2].f})`);

  clearInterval(snaps); A.ws.close(); B.ws.close();
  await sleep(300);
  if (/Error|uncaught/i.test(srv.err)) ok(false, 'server errors: ' + srv.err.slice(0, 300));
  console.log(fails ? `\n${fails} FAILED` : '\nall passed');
  end(fails ? 1 : 0);
})().catch((e) => { console.error(e); end(1); });
setTimeout(() => { console.log('timeout'); end(1); }, 90000);
