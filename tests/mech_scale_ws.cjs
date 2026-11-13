// mech size over plain ws (shared/mech.js mechScale, x1.35 by default): the welcome tells the client the size; the drop
// refuses spots with no room (under the warehouse roof, under the wall over its door, against a wall: NO ROOM FOR IT
// HERE, the streak stays) and lands in the open yard; the bigger squash circle and shockwave; climbing in from further;
// the cockpit's eye height; the stomp circle; hopping out onto a free spot; an empty mech's taller box and cockpit band.
// then a JF_MECH_SCALE=1 server: the old numbers.
// starts its own servers: node tests/mech_scale_ws.cjs [port]   (uses port and port + 1)
const WS = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const port = Number(process.argv[2]) || 3171;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
const MF = { MECH: 1 << 22 };
const Y = 0.03; // the warehouse floor (+ a hair). the yard east of the building (x > 32.3) is open sky; the building's roof is at 10 m
let srv = null;

function client(name, prt, extra = {}) {
  const ws = new WS(`ws://localhost:${prt}/ws`), c = { ws, got: [], id: 0, q: 0, alive: true, name };
  ws.on('message', (d) => {
    const m = JSON.parse(d);
    if (m.t === 'welcome') { c.id = m.id; c.q = m.q; c.ms = m.ms; }
    if (m.t === 'spawn') c.q = m.q;
    if (m.t === 'sn') { const r = m.p.find((x) => x[0] === c.id); if (r) c.alive = !!r[11]; return; }
    c.got.push(m);
  });
  ws.on('error', () => {});
  c.send = (m) => { if (ws.readyState === 1) ws.send(JSON.stringify(m)); };
  c.place = (p, o = {}) => c.send({ t: 's', q: c.q, p, v: o.v || [0, 0, 0], y: o.y ?? 0, x: o.x ?? 0, w: o.w || 'ar', f: o.f || 0 });
  c.take = (t, f) => { const i = c.got.findIndex((m) => m.t === t && (!f || f(m))); return i < 0 ? null : c.got.splice(i, 1)[0]; };
  c.all = (t, f) => c.got.filter((m) => m.t === t && (!f || f(m)));
  c.wait = async (t, f, ms = 4000) => { for (let i = 0; i < ms / 50; i++) { const m = c.take(t, f); if (m) return m; await sleep(50); } return null; };
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'join', name, mode: 'ffa', streaks: ['mechdrop', 'moonboots', 'scythe'], ...extra }); setTimeout(() => res(c), 700); }));
}
const aim = (a, b) => { const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], h = Math.hypot(d[0], d[2]); return { y: Math.atan2(-d[0], -d[2]), x: Math.atan2(d[1], h), d: d.map((v) => v / Math.hypot(...d)) }; };
const hold = async (ms, who) => { for (let t = 0; t < ms; t += 60) { for (const [c, p, o] of who) c.place(typeof p === 'function' ? p(t) : p, o); await sleep(60); } };
const near = (a, b, e) => Math.abs(a - b) <= e;

async function boot(prt, env) {
  srv = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(prt), JF_TRAIN_STREAKS: '1', JF_MECH_HP: '0.3', JF_MECH_WAIT: '30', ...env }, stdio: ['ignore', 'pipe', 'pipe'] });
  srv.err = ''; srv.stderr.on('data', (d) => { srv.err += d; }); srv.stdout.on('data', (d) => { if (/Error|uncaught/i.test(String(d))) srv.err += d; });
  for (let i = 0; i < 60; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${prt}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }
  const A = await client('pilot', prt, { mf: 'paperplane' });
  A.send({ t: 'cfg', map: 'warehouse' }); await sleep(900);
  const B = await client('victim', prt), C = await client('bystander', prt);
  await sleep(1500); // spawn protection + the tray fills (JF_TRAIN_STREAKS)
  return { A, B, C };
}
// call one in at `at` from `from` (others held where they are); the 'call' or the 'no'
async function call(A, from, at, others, f = 'paperplane') {
  const l = aim([from[0], from[1] + 1.6, from[2]], at);
  await hold(300, [[A, from, { y: l.y, x: l.x }], ...others]);
  A.got.length = 0;
  A.send({ t: 'deploy', r: 'mechdrop', at, mf: f });
  await hold(400, [[A, from, { y: l.y, x: l.x }], ...others]);
  return { call: A.take('mech', (m) => m.k === 'call'), no: A.take('mech', (m) => m.k === 'no'), back: A.take('streak', (m) => m.earned === 'mechdrop') };
}

(async () => {
  // ================================================================ x1.35 (the default)
  let { A, B, C } = await boot(port, {});
  ok(A.ms === 1.35, `the welcome says how big mechs are: ${A.ms}`);
  const park = [[B, [60, Y, 30]], [C, [62, Y, 30]]];
  // ---- the drop: no room
  let r = await call(A, [29.5, Y, -6.5], [26, Y, -5], park);
  ok(!r.call && r.no && r.no.why === 'no room for it here' && r.back, `under the warehouse roof (between the rafters): ${r.no && r.no.why}, back in the tray`);
  r = await call(A, [40, Y, -6.5], [33, Y, -6.5], park);
  ok(!r.call && r.no && r.no.why === 'no room for it here' && r.back, `in the 5 m door, under the wall over it: ${r.no && r.no.why}`);
  r = await call(A, [40, Y, 5], [33, Y, 5], park);
  ok(!r.call && r.no && r.no.why === 'no room for it here' && r.back, `0.7 m off the outside wall (no width): ${r.no && r.no.why}`);
  r = await call(A, [40, Y, 5], [33.6, Y, 5], park, 'nightshift');
  ok(!r.call && r.no && r.no.why === 'no room for it here', `1.3 m off it: the paper plane would fit, the wider NIGHT SHIFT doesn't: ${r.no && r.no.why}`);

  // ---- open sky: it lands. B 2.3 m off the marker (old squash circle 1.9 m): squashed; C 7.4 m off (old shockwave 6 m): hit
  const M = [45, Y, 10], pb = [M[0] + 2.3, Y, M[2]], pc = [M[0], Y, M[2] + 7.4], pa = [45, Y, 24];
  r = await call(A, pa, M, [[B, pb], [C, pc]]);
  ok(r.call && !r.no, 'the open yard: called in');
  await hold(2900, [[A, pa], [B, pb], [C, pc]]);
  const land = A.take('mech', (m) => m.k === 'land');
  ok(!!land, 'it lands');
  ok(A.take('mech', (m) => m.k === 'squash' && m.to === B.id), 'B 2.3 m off the marker: SQUASHED (the circle grew: 2.57 m)');
  const cd = C.take('dmg', (m) => m.to === C.id && m.w === 'mechdrop');
  ok(cd && cd.a > 20, `C 7.4 m off: shockwave ${cd && Math.round(cd.a)} (its radius grew: 8.1 m)`);
  // ---- climb in from 5.6 m (old reach: 5)
  await sleep(2600);
  const pin = [M[0] + 5.6, Y, M[2]], far2 = [[B, [60, Y, 30]], [C, [M[0], Y, M[2] - 12]]];
  await hold(1200, [[A, pin], ...far2]);
  A.got.length = 0; A.send({ t: 'mech', k: 'in' });
  const ein = await A.wait('mech', (m) => m.k === 'in' && m.id === A.id, 1000);
  ok(!!ein, 'climbs in from 5.6 m away (reach 6.1 m)');
  const P = ein ? ein.p : M.slice(), mid = ein ? ein.m : 0;
  // ---- the cockpit's eye: a level cannon shot leaves from 5.94 m up (old 4.4)
  const inMech = (ms, path, o = {}) => hold(ms, [[A, path || P, { y: 0, x: 0, f: MF.MECH, ...o }], ...far2]);
  await inMech(800);
  B.got.length = 0;
  A.send({ t: 'mech', k: 'gun', d: [0, 0, -1] }); await inMech(300);
  const g = B.take('mech', (m) => m.k === 'gun' && m.id === A.id);
  ok(g && near(g.b[1] - P[1], 5.94, 0.05), `cannons fire from the cockpit, ${g && (g.b[1] - P[1]).toFixed(2)} m up (old 4.4)`);
  // ---- stomp: a hop straight up and down next to B, 1.45 m off (old stomp circle 1.25 m, now 1.53)
  await sleep(1500);
  const pbs = [P[0] + 1.45, Y, P[2]], sq = [[B, pbs], [C, [M[0], Y, M[2] - 12]]];
  await hold(1500, [[A, P, { f: MF.MECH }], ...sq]);
  B.got.length = 0;
  const t0 = Date.now(); // the paper plane's hop: 12 m/s up, 30 gravity (2.4 m, 0.8 s)
  await hold(1000, [[A, () => { const t = Math.min(0.8, (Date.now() - t0) / 1000); return [P[0], Math.max(Y, Y + 12 * t - 15 * t * t), P[2]]; }, { f: MF.MECH }], ...sq]);
  await hold(400, [[A, P, { f: MF.MECH }], ...sq]);
  const sd = B.take('dmg', (m) => m.to === B.id && m.w === 'mechstomp');
  ok(sd && sd.a === 50, `STOMPED 1.45 m off its middle: ${sd && sd.a}`);
  // ---- hop out: onto a free spot off its side, 2.97 m out (old 2.2)
  await sleep(1600);
  await inMech(400);
  A.got.length = 0; A.send({ t: 'mech', k: 'out' });
  const po = await A.wait('mech', (m) => m.k === 'pos', 800);
  const dOut = po ? Math.hypot(po.p[0] - P[0], po.p[2] - P[2]) : 0;
  ok(po && near(dOut, 2.97, 0.05) && near(po.p[1], 0, 0.1), `hops out ${dOut.toFixed(2)} m off its side, on the floor`);
  // ---- its empty box: C 30 m off shoots its near face at 5.8 m up (old: over its 4.9 m head) = the cockpit; 6.4 m = the shoulders; 7.6 m = over it
  const pcs = [P[0], Y, P[2] - 30], eye = [pcs[0], Y + 1.6, pcs[2]], stand = [[A, po ? po.p : P], [B, [60, Y, 30]]];
  const shoot = async (hgt, h) => {
    const l = aim(eye, [P[0], P[1] + hgt, P[2] - 1.08]); // (its near face: a shallow line, so it meets the box where it's aimed)
    await hold(400, [[C, pcs, { y: l.y, x: l.x }], ...stand]);
    C.got.length = 0; C.send({ t: 'hit', mk: mid, w: 'ar', d: l.d, n: 1, h });
    await hold(300, [[C, pcs, { y: l.y, x: l.x }], ...stand]);
    return C.take('mech', (m) => m.k === 'hurt' && m.m === mid);
  };
  let h = await shoot(5.8, 1);
  ok(h && h.hs === 1 && near(h.a, 16.5, 0.6), `shot at 5.8 m up: a cockpit hit ${h && h.a} (11 x 1.5)`);
  h = await shoot(6.5, 1);
  ok(h && !h.hs && h.a === 11, `shot at 6.5 m up, "headshot": lands on the shoulders, ${h && h.a} (body)`);
  h = await shoot(7.6, 0);
  ok(!h, 'shot at 7.6 m up: over it, nothing');
  ok(!srv.err, 'no server errors' + (srv.err ? ': ' + srv.err.slice(0, 300) : ''));
  for (const c of [A, B, C]) c.ws.close();
  srv.kill(); await sleep(800);

  // ================================================================ JF_MECH_SCALE=1: the old mech
  ({ A, B, C } = await boot(port + 1, { JF_MECH_SCALE: '1' }));
  ok(A.ms === 1, `JF_MECH_SCALE=1: the welcome says ${A.ms}`);
  r = await call(A, [29.5, Y, -6.5], [26, Y, -5], park);
  ok(!r.call && r.no && r.no.why === 'no room for it here', 'size 1 under the roof: still no room');
  r = await call(A, pa, M, [[B, pb], [C, pc]]);
  await hold(2900, [[A, pa], [B, pb], [C, pc]]);
  ok(r.call && A.take('mech', (m) => m.k === 'land'), 'size 1: lands in the yard');
  ok(!A.take('mech', (m) => m.k === 'squash') && B.take('dmg', (m) => m.to === B.id && m.w === 'mechdrop'), 'size 1: B 2.3 m off is outside the 1.9 m squash circle (shockwave only)');
  ok(!C.take('dmg', (m) => m.to === C.id && m.w === 'mechdrop'), 'size 1: C 7.4 m off is outside the 6 m shockwave');
  await hold(1200, [[A, pin], ...far2]);
  A.got.length = 0; A.send({ t: 'mech', k: 'in' }); await sleep(300);
  ok((A.take('mech', (m) => m.k === 'no') || {}).why === 'get closer', 'size 1: 5.6 m is too far to climb in');
  await hold(400, [[A, [M[0] + 4, Y, M[2]]], ...far2]);
  A.send({ t: 'mech', k: 'in' });
  const in1 = await A.wait('mech', (m) => m.k === 'in' && m.id === A.id, 1000);
  ok(!!in1, 'size 1: climbs in from 4 m');
  const P1 = in1 ? in1.p : M;
  await hold(800, [[A, P1, { y: 0, x: 0, f: MF.MECH }], ...far2]);
  B.got.length = 0;
  A.send({ t: 'mech', k: 'gun', d: [0, 0, -1] }); await hold(300, [[A, P1, { y: 0, x: 0, f: MF.MECH }], ...far2]);
  const g1 = B.take('mech', (m) => m.k === 'gun' && m.id === A.id);
  ok(g1 && near(g1.b[1] - P1[1], 4.4, 0.05), `size 1: cannons from ${g1 && (g1.b[1] - P1[1]).toFixed(2)} m up`);
  ok(!srv.err, 'no server errors (size 1)' + (srv.err ? ': ' + srv.err.slice(0, 300) : ''));
  for (const c of [A, B, C]) c.ws.close();
  srv.kill();
  console.log(fails ? `${fails} FAILED` : 'ALL OK');
  process.exit(fails ? 1 : 0);
})().catch((e) => { console.error(e); if (srv) srv.kill(); process.exit(1); });
