// your own mech landing on you (the owner's "youre own mech land kills you"): over real sockets on Battle Island
// (squads of 2: A + B vs C + D). A calls the mech onto its own feet with mate B and enemy C on the circle too:
// A and B live and get one BEEP BEEP shove off it (server-picked, toward clear floor, then a hop), A can climb straight
// in from where it lands, C is still squashed flat. a client asking for a bonk itself gets nothing.
// then plain FFA (warehouse yard): the caller alone on its own circle, same thing.
// starts its own servers: node tests/mech_selfsquash_ws.cjs [port]
const WS = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const port = Number(process.argv[2]) || 3174;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
const ROOT = path.join(__dirname, '..');
const S = [0, 0, 24], at = (dx, dz) => [S[0] + dx, S[1], S[2] + dz];
let log = [], T0 = Date.now();
const ms = () => Date.now() - T0;
const pos = new Map(), alive = new Map();
function client(name, prt, join) {
  const c = { name, id: 0, q: 1, pos: at(0, 0), snap: true, ws: new WS(`ws://localhost:${prt}/ws`) };
  c.send = (o) => { if (c.ws.readyState === 1) c.ws.send(typeof o === 'string' ? o : JSON.stringify(o)); };
  c.ws.on('message', (d) => {
    const m = JSON.parse(d);
    if (m.t === 'welcome') { c.id = m.id; c.q = m.q; }
    if (m.t === 'spawn' && m.q) c.q = m.q;
    if (m.t === 'isle' && m.k === 'fix') c.pos = m.p;
    if (m.t === 'sn') { for (const e of m.p) { pos.set(e[0], [e[1], e[2], e[3]]); alive.set(e[0], !!e[11]); } return; }
    log.push([ms(), name, m]);
  });
  c.ws.on('error', () => {});
  c.ws.on('open', () => c.send(join));
  return c;
}
const heard = (pred, since = 0) => log.find((e) => e[0] >= since && pred(e[2], e[1]));
const count = (pred, since = 0) => log.filter((e) => e[0] >= since && pred(e[2], e[1])).length;
async function until(fn, max = 8000) { const t = Date.now(); while (Date.now() - t < max) { if (fn()) return true; await sleep(50); } return !!fn(); }
const near = (c, p, tol = 0.6) => { const q = pos.get(c.id); return !!q && Math.hypot(q[0] - p[0], q[1] - p[1], q[2] - p[2]) < tol; };
const settle = (cs) => until(() => cs.every((c) => near(c, c.pos)), 10000);
const inSquads = (cs) => until(() => cs.every((c) => c.id) && (() => { const e = [...log].reverse().find((x) => x[2].t === 'isle' && x[2].k === 'sq'); return e && cs.every((c) => e[2].l.some((r) => r[0] === c.id)); })(), 15000);
const mmNow = (c) => { const e = [...log].reverse().find((x) => x[1] === c.name && x[2].t === 'isle' && x[2].k === 'mm'); return e ? e[2].v : -1; };
const srvs = [];
async function server(env, prt) {
  const srv = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: ROOT, env: { ...process.env, PORT: String(prt), JF_TRAFFIC: 'off', ...env }, stdio: ['ignore', 'pipe', 'pipe'] });
  srv.err = ''; srv.stderr.on('data', (d) => { srv.err += d; }); srv.stdout.on('data', (d) => { if (/Error|uncaught/i.test(String(d))) srv.err += d; });
  srvs.push(srv);
  for (let i = 0; i < 90; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${prt}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }
  return srv;
}
const land = async (cs) => { const t = ms(); await until(() => { for (const c of cs) if (!heard((m) => m.t === 'br' && m.k === 'jump' && m.id === c.id, t)) c.send({ t: 'brjump' }); return cs.every((c) => heard((m) => m.t === 'br' && m.k === 'jump' && m.id === c.id, t)); }, 20000); };
const snapper = (cs) => setInterval(() => { for (const c of cs) if (c.snap && c.ws.readyState === 1) c.send({ t: 's', q: c.q, p: c.pos, v: [0, 0, 0], y: c.yaw || 0, x: c.pitch || 0, w: 'bread', g: 0, f: 0 }); }, 100);
// where a shove (kb velocity v) puts you on flat ground: the hop's airtime (gravity 26) times the push
const after = (p, v) => { const air = 2 * v[1] / 26; return [p[0] + v[0] * air, p[1], p[2] + v[2] * air]; };
const end = (code) => { for (const s of srvs) s.kill(); setImmediate(() => process.exit(code)); };

(async () => {
  // ---------------------------------------------------------- battle island: you, a mate and an enemy on the circle
  await server({ JF_GAME: 'island', JF_ISLE_SIZE: '2', JF_ISLE_METER: '100', JF_MECH_DROP: '0.6', JF_ISLE_ZONE: '5' }, port);
  const join = (mf) => ({ t: 'join', name: '', mode: 'ffa', mf });
  const A = client('Alfa', port, { ...join('nightshift'), name: 'Alfa' }); await sleep(400);
  const C = client('Charlie', port, { ...join('paperplane'), name: 'Charlie' }); await sleep(250);
  const B = client('Bravo', port, { ...join('paperplane'), name: 'Bravo' }); await sleep(250);
  const D = client('Delta', port, { ...join(undefined), name: 'Delta' });
  const all = [A, B, C, D];
  ok(await inSquads(all), 'four in, two squads');
  const sq = new Map([...log].reverse().find((e) => e[2].t === 'isle' && e[2].k === 'sq')[2].l);
  ok(sq.get(A.id) === sq.get(B.id) && sq.get(C.id) === sq.get(D.id) && sq.get(A.id) !== sq.get(C.id), 'squads: A + B, C + D');
  await land(all);
  A.pos = at(0, 0); B.pos = at(1, 0.5); C.pos = at(-1, -0.5); D.pos = at(25, 25);
  const snaps = snapper(all);
  await settle(all); await sleep(2000);
  ok(await until(() => mmNow(A) >= 100, 20000), `A's mech meter is full (${mmNow(A)}%)`);
  let t = ms();
  A.send({ t: 'deploy', r: 'mechdrop', at: A.pos.slice() }); // aimed at its own feet
  const call = await (async () => { await until(() => heard((m) => m.t === 'mech' && m.k === 'call', t), 4000); return heard((m) => m.t === 'mech' && m.k === 'call', t); })();
  ok(!!call, 'the call at your own feet is allowed (a floor, open sky)');
  ok(await until(() => heard((m) => m.t === 'mech' && m.k === 'land', t), 5000), 'it lands');
  await sleep(600);
  const kbOf = (c) => heard((m, w) => w === c.name && m.t === 'kb' && m.w === 'mechbonk', t);
  const bonked = (c) => heard((m, w) => w === 'Delta' && m.t === 'mech' && m.k === 'bonk' && m.to === c.id && m.id === A.id, t);
  const hurtBy = (c) => count((m, w) => w === 'Delta' && m.t === 'dmg' && m.to === c.id && m.w === 'mechdrop', t);
  ok(alive.get(A.id) !== false && !hurtBy(A) && !heard((m) => m.t === 'isle' && m.k === 'down' && m.id === A.id, t), 'A (the caller, dead centre) is NOT squashed: no damage, not down, alive');
  ok(!!bonked(A) && !!kbOf(A), `A gets the BEEP BEEP bonk + a shove ${kbOf(A) ? JSON.stringify(kbOf(A)[2].v) : '-'}`);
  ok(alive.get(B.id) !== false && !hurtBy(B) && !heard((m) => m.t === 'isle' && m.k === 'down' && m.id === B.id, t), 'B (A\'s squadmate, on the circle) is NOT squashed');
  ok(!!bonked(B) && !!kbOf(B), `B gets bonked off it too ${kbOf(B) ? JSON.stringify(kbOf(B)[2].v) : '-'}`);
  ok(!!heard((m) => m.t === 'mech' && m.k === 'squash' && m.to === C.id, t) && !!heard((m) => m.t === 'isle' && m.k === 'down' && m.id === C.id, t), 'C (an enemy on the circle) is still SQUASHED (downed)');
  ok(!bonked(C) && !bonked(D) && !kbOf(D), 'enemies get no bonk; D (25 m off) nothing at all');
  const v = kbOf(A) ? kbOf(A)[2].v : [0, 0, 0], hv = Math.hypot(v[0], v[2]);
  ok(hv > 4 && hv < 9 && v[1] > 5 && v[1] < 9, `the shove is a fixed hop (${hv.toFixed(1)} m/s out, ${v[1]} up), not a fling`);
  ok(count((m, w) => w === 'Alfa' && m.t === 'kb' && m.w === 'mechbonk', t) === 1 && count((m, w) => w === 'Bravo' && m.t === 'kb' && m.w === 'mechbonk', t) === 1, 'one shove each per landing');
  // A lands where the shove puts it and climbs straight in
  A.pos = after(A.pos, v); await settle([A]);
  const d = Math.hypot(A.pos[0] - call[2].p[0], A.pos[2] - call[2].p[2]);
  t = ms(); A.send({ t: 'mech', k: 'in' });
  ok(await until(() => heard((m) => m.t === 'mech' && m.k === 'in' && m.id === A.id, t), 3000), `A climbs straight in from where it landed (${d.toFixed(1)} m off)`);
  // nobody can ask for a bonk
  t = ms();
  for (const o of [{ t: 'mech', k: 'bonk' }, { t: 'mech', k: 'bonk', to: B.id, v: [99, 99, 99] }, { t: 'bonk', v: [50, 50, 50] }, { t: 'mech', k: 'land', id: call[2].id }]) B.send(o);
  await sleep(700);
  ok(!heard((m) => m.t === 'kb' && m.w === 'mechbonk', t) && !heard((m) => m.t === 'mech' && (m.k === 'bonk' || m.k === 'land'), t), 'a client asking for a bonk (or a landing) gets nothing');
  clearInterval(snaps); for (const c of all) c.ws.close();

  // ---------------------------------------------------------- plain FFA: the caller alone on its own circle
  log = []; pos.clear(); alive.clear();
  const p2 = port + 1;
  await server({ JF_TRAIN_STREAKS: '1', JF_MECH_DROP: '0.6' }, p2);
  const P = client('Solo', p2, { t: 'join', name: 'Solo', mode: 'ffa', streaks: ['mechdrop', 'moonboots', 'scythe'], mf: 'paperplane' });
  await until(() => P.id, 5000); P.send({ t: 'cfg', map: 'warehouse' }); await sleep(1500);
  P.pos = [42, 0.03, 21]; P.pitch = -1.5;
  const s2 = snapper([P]); await settle([P]); await sleep(1500);
  t = ms(); P.send({ t: 'deploy', r: 'mechdrop', at: P.pos.slice(), mf: 'paperplane' });
  ok(await until(() => heard((m) => m.t === 'mech' && m.k === 'land', t), 5000), 'FFA: called at your own feet, it lands');
  await sleep(500);
  ok(alive.get(P.id) !== false && !heard((m) => m.t === 'dmg' && m.to === P.id, t), 'FFA: the caller lives (no damage)');
  ok(!!heard((m) => m.t === 'kb' && m.w === 'mechbonk', t) && !!heard((m) => m.t === 'mech' && m.k === 'bonk' && m.to === P.id, t), 'FFA: and gets the BEEP BEEP shove');
  clearInterval(s2); P.ws.close();
  for (const s of srvs) if (/Error|uncaught/i.test(s.err)) { ok(false, 'server errors: ' + s.err.slice(0, 300)); break; }
  console.log(fails ? `\n${fails} FAILED` : '\nall passed');
  end(fails ? 1 : 0);
})().catch((e) => { console.error(e); end(1); });
setTimeout(() => { console.log('timeout'); end(1); }, 170000);
