// battle island, step 1 (PR A): every squad rule over real sockets, plus the exploit checks. Five people in the Online
// room playing BATTLE ISLAND (JF_GAME=island, no traffic, a 12 s bleed-out): A, B, E land in squad 1, C, D in squad 2.
// squads + no friendly fire, down / crawl / bleed-out / revive (range, hold time, interrupted), squad out, the winner,
// and the tricks: reviving from far away, instant revives, reviving while down, reviving an enemy, two revivers at
// once, a downed pilot shooting / looting / teleporting, garbage messages.
// starts its own server: node tests/island_squads_ws.cjs [port]
const WS = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const port = Number(process.argv[2]) || 3182;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const failed = []; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) { fails++; failed.push(msg.slice(0, 80)); } };
const S = [69.2, 0.2, -10.4]; // a jankburg spawn: open ground
const at = (dx, dz) => [S[0] + dx, S[1], S[2] + dz];
const log = []; // [ms, who heard it, message]
const T0 = Date.now(), ms = () => Date.now() - T0;
const pos = new Map(); // id -> where the server has them

function client(name) {
  const c = { name, id: 0, q: 1, pos: at(0, 0), snap: true, ws: new WS(`ws://localhost:${port}/ws`) };
  c.send = (o) => { if (c.ws.readyState === 1) c.ws.send(typeof o === 'string' ? o : JSON.stringify(o)); };
  c.ws.on('message', (d) => {
    const m = JSON.parse(d);
    if (m.t === 'welcome') { c.id = m.id; c.q = m.q; }
    if (m.t === 'spawn' && m.q) c.q = m.q;
    if (m.t === 'isle' && m.k === 'fix') c.pos = m.p; // the server put a crawler back (like the real client)
    if (m.t === 'sn') for (const e of m.p) pos.set(e[0], [e[1], e[2], e[3]]);
    if (['isle', 'dmg', 'kill', 'br', 'heal', 'round'].includes(m.t)) log.push([ms(), name, m]);
  });
  c.ws.on('open', () => c.send({ t: 'join', name, mode: 'ffa' }));
  return c;
}
const heard = (pred, since = 0) => log.find((e) => e[0] >= since && pred(e[2], e[1]));
async function waitFor(pred, max, since = 0) { const t = Date.now(); while (Date.now() - t < max) { const e = heard(pred, since); if (e) return e; await sleep(50); } return null; }
// waiting on the server, not the clock (CPU-loaded machines)
async function until(fn, max = 8000) { const t = Date.now(); while (Date.now() - t < max) { if (fn()) return true; await sleep(50); } return !!fn(); }
const near = (c, p, tol = 0.6) => { const q = pos.get(c.id); return !!q && Math.hypot(q[0] - p[0], q[1] - p[1], q[2] - p[2]) < tol; };
const settle = (cs) => until(() => cs.every((c) => near(c, c.pos)), 10000);
const keepUsing = (c) => setInterval(() => c.send({ t: 'use' }), 200);
const hp = (who, of) => { const e = [...log].reverse().find((x) => x[1] === who.name && x[2].t === 'isle' && x[2].k === 'st'); const r = e && e[2].m.find((row) => row[0] === of.id); return r || null; };

(async () => {
  const srv = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(port), JF_GAME: 'island', JF_TRAFFIC: 'off', JF_ISLE_BLEED: '12' }, stdio: ['ignore', 'pipe', 'pipe'] });
  let srvErr = ''; srv.stderr.on('data', (d) => { srvErr += d; }); srv.stdout.on('data', (d) => { if (/Error|uncaught/i.test(String(d))) srvErr += d; });
  process.on('exit', () => srv.kill());
  for (let i = 0; i < 60; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }

  // (the 2nd one in always starts a second squad; after that people fill the fullest squad with room)
  const A = client('Alfa'); await sleep(400);
  const C = client('Charlie'); await sleep(250);
  const B = client('Bravo'); await sleep(250);
  const E = client('Echo'); await sleep(250);
  const D = client('Delta');
  const all = [A, B, E, C, D];
  await until(() => all.every((c) => c.id) && (() => { const e = [...log].reverse().find((x) => x[2].t === 'isle' && x[2].k === 'sq'); return e && all.every((c) => e[2].l.some((r) => r[0] === c.id)); })(), 15000);
  // ---------------------------------------------------------- squads
  const sqMsg = [...log].reverse().find((e) => e[2].t === 'isle' && e[2].k === 'sq');
  const sq = new Map(sqMsg ? sqMsg[2].l : []);
  console.log('  squads:', all.map((c) => `${c.name}=${sq.get(c.id)}`).join(' '));
  ok(sq.get(A.id) && sq.get(A.id) === sq.get(B.id) && sq.get(B.id) === sq.get(E.id), 'A, B and E share a squad (C, the 2nd one in, started the other)');
  ok(sq.get(C.id) && sq.get(C.id) === sq.get(D.id) && sq.get(C.id) !== sq.get(A.id), 'C and D are the next squad');
  // a 'use' from the blimp does nothing
  A.send({ t: 'use' });
  // everyone jumps and "lands" on the spawn (movement is the client's)
  const tj = ms();
  await until(() => { for (const c of all) if (!heard((m) => m.t === 'br' && m.k === 'jump' && m.id === c.id, tj)) c.send({ t: 'brjump' }); return all.every((c) => heard((m) => m.t === 'br' && m.k === 'jump' && m.id === c.id, tj)); }, 20000); // (once the blimp's moving)
  A.pos = at(0, 0); B.pos = at(1.5, 0); E.pos = at(-1.5, 0); C.pos = at(0, 2.5); D.pos = at(30, 30);
  const snaps = setInterval(() => { for (const c of all) if (c.snap) c.send({ t: 's', q: c.q, p: c.pos, v: [0, 0, 0], y: c.face ? Math.atan2(c.pos[0] - c.face.pos[0], c.pos[2] - c.face.pos[2]) : 0, x: 0, w: 'bread', g: 0, f: 0 }); }, 100); // (face: who c swings at, the server checks a swing's cone)
  await settle(all); await sleep(2000); // (landed: on the floor and still)

  // ---------------------------------------------------------- no friendly fire
  let t = ms();
  A.send({ t: 'hit', w: 'bread', to: B.id, d: [1, 0, 0] });
  await sleep(500);
  ok(!heard((m) => m.t === 'dmg' && m.to === B.id && m.from === A.id, t), 'no friendly fire: A bonks squadmate B, nothing');
  A.face = C; await sleep(250);
  A.send({ t: 'hit', w: 'bread', to: C.id, d: [0, 0, 1] });
  ok(!!(await waitFor((m) => m.t === 'dmg' && m.to === C.id && m.from === A.id, 6000, t)), 'A bonks enemy C: it lands');
  // ---------------------------------------------------------- down, not dead
  const downBy = async (atk, tgt) => { atk.face = tgt; await settle([atk]); await sleep(250); const t1 = ms(); for (let i = 0; i < 25; i++) { atk.send({ t: 'hit', w: 'bread', to: tgt.id, d: [1, 0, 0] }); if (await waitFor((m) => m.t === 'isle' && m.k === 'down' && m.id === tgt.id, 600, t1)) return true; } return false; };
  C.pos = at(1.5, 2.5);
  t = ms();
  ok(await downBy(C, B), 'B at 0 HP goes DOWN, not dead (A and E are still up)');
  ok(!heard((m) => m.t === 'kill' && m.v === B.id, t), '...no kill message for B');
  await until(() => { const r = hp(B, B); return r && r[2] === 1; }, 5000);
  let row = hp(B, B);
  ok(row && row[2] === 1 && row[3] > 100 && row[3] <= 120, `B's squad HUD says down with ~12 s to bleed (${row && row.join(',')})`);
  // a downed pilot can't shoot, loot or revive
  t = ms();
  B.send({ t: 'hit', w: 'bread', to: C.id, d: [0, 0, 1] }); B.send({ t: 'fire', w: 'bread' }); B.send({ t: 'brpick', i: 1, f: 1 }); B.send({ t: 'brheal', k: 'cola' }); B.send({ t: 'deploy', i: 0 });
  await sleep(500);
  ok(!heard((m) => m.t === 'dmg' && m.from === B.id, t), 'downed B can\'t hit anyone');
  // crawl: a snapshot 12 m away gets put back
  t = ms();
  await sleep(1600); // (past the shove from the last bonk)
  t = ms(); B.pos = at(14, 0);
  const fix = await waitFor((m, who) => who === 'Bravo' && m.t === 'isle' && m.k === 'fix', 6000, t);
  ok(!!fix && Math.hypot(fix[2].p[0] - S[0], fix[2].p[2] - S[2]) < 4, `downed B teleporting 12 m is put back (${fix ? fix[2].p.join(',') : 'no fix'})`);
  B.pos = fix ? fix[2].p : at(1.5, 0);
  // the enemy can't revive B; E (down? no: up) and A are its squad
  t = ms();
  C.pos = [B.pos[0] + 1, B.pos[1], B.pos[2]]; await settle([C]); t = ms();
  for (let i = 0; i < 6; i++) { C.send({ t: 'use' }); await sleep(200); }
  ok(!heard((m) => m.t === 'isle' && m.k === 'rv' && m.by === C.id, t), 'an enemy can\'t revive B');
  C.pos = at(0, 8);
  // too far: 4 m away
  A.pos = [B.pos[0] + 4, B.pos[1], B.pos[2]];
  await settle([A]); t = ms();
  for (let i = 0; i < 6; i++) { A.send({ t: 'use' }); await sleep(200); }
  ok(!heard((m) => m.t === 'isle' && m.k === 'rv', t), 'A can\'t revive from 4 m');
  // in reach: starts; let go after 1.5 s: interrupted, B still down
  A.pos = [B.pos[0] + 1.5, B.pos[1], B.pos[2]];
  await settle([A]); t = ms();
  let k = keepUsing(A); await waitFor((m) => m.t === 'isle' && m.k === 'rv' && m.by === A.id, 6000, t); await sleep(600); clearInterval(k);
  ok(!!heard((m) => m.t === 'isle' && m.k === 'rv' && m.id === B.id && m.by === A.id && m.ms === 4000, t), 'A in reach (1.5 m) starts picking B up (4 s)');
  // a second reviver on the same person is ignored
  E.pos = [B.pos[0] - 1.2, B.pos[1], B.pos[2]];
  await settle([E]); E.send({ t: 'use' }); await sleep(400); E.send({ t: 'use' }); await sleep(400);
  ok(!heard((m) => m.t === 'isle' && m.k === 'rv' && m.by === E.id, t), 'a second squadmate can\'t double up on the same revive');
  const rvx = await waitFor((m) => m.t === 'isle' && m.k === 'rvx' && m.id === B.id, 6000, t);
  ok(!!rvx && !heard((m) => m.t === 'isle' && m.k === 'up' && m.id === B.id, t), `letting go of F interrupts it (${rvx ? rvx[2].why : '-'}), B stays down`);
  // moving out of reach mid-revive interrupts it too
  t = ms();
  k = keepUsing(A); await waitFor((m) => m.t === 'isle' && m.k === 'rv' && m.by === A.id, 6000, t);
  const tm = ms(); A.pos = [B.pos[0] + 6, B.pos[1], B.pos[2]];
  const mv = await waitFor((m) => m.t === 'isle' && m.k === 'rvx' && m.id === B.id, 6000, tm); clearInterval(k);
  ok(!!mv && mv[2].why === 'moved', `walking away mid-revive stops it (${mv ? mv[2].why : 'not stopped'})`);
  // spamming 'use' 25 times a second doesn't make it any faster: the full hold, then up at 30 HP
  A.pos = [B.pos[0] + 1.5, B.pos[1], B.pos[2]];
  await settle([A]); await sleep(1200); t = ms();
  const spam = setInterval(() => A.send({ t: 'use' }), 40);
  const up = await waitFor((m) => m.t === 'isle' && m.k === 'up' && m.id === B.id, 15000, t);
  clearInterval(spam);
  const start = heard((m) => m.t === 'isle' && m.k === 'rv' && m.id === B.id, t);
  const took = up && start ? up[0] - start[0] : -1;
  ok(!!up && up[2].by === A.id && took >= 3850 && took < 6500, `held 4 s (spammed): B is back up (${took} ms)`);
  const healed = await waitFor((m) => m.t === 'heal' && m.id === B.id && m.hp === 30, 4000, t);
  ok(!!healed, 'B is back at 30 HP');
  await until(() => { const r = hp(A, B); return r && r[2] === 0; }, 5000);
  row = hp(A, B);
  ok(row && row[2] === 0 && row[1] === 30, `the squad HUD shows B up at 30 (${row && row.join(',')})`);

  // ---------------------------------------------------------- reviving while down yourself
  C.pos = at(0, 2.5);
  t = ms();
  ok(await downBy(C, E), 'E goes down');
  ok(await downBy(C, B), 'B goes down again (A still up)');
  E.pos = [B.pos[0] + 1, B.pos[1], B.pos[2]];
  await sleep(1600); t = ms();
  for (let i = 0; i < 6; i++) { E.send({ t: 'use' }); await sleep(200); }
  ok(!heard((m) => m.t === 'isle' && m.k === 'rv' && m.by === E.id, t), 'downed E can\'t revive downed B');
  // A picks E up meanwhile (B is left on the floor)
  E.pos = (pos.get(E.id) || E.pos).slice(); A.pos = [E.pos[0] + 1.2, E.pos[1], E.pos[2]];
  await settle([A]);
  const spamE = setInterval(() => A.send({ t: 'use' }), 200);
  const upE = await waitFor((m) => m.t === 'isle' && m.k === 'up' && m.id === E.id, 12000, t);
  clearInterval(spamE);
  ok(!!upE, 'A picks E up');
  // bleed-out: nobody helps B; it takes the 12 s, the kill goes to C who put B down
  const bdown = [...log].reverse().find((e) => e[2].t === 'isle' && e[2].k === 'down' && e[2].id === B.id);
  const bled = await waitFor((m) => m.t === 'kill' && m.v === B.id, 25000, t);
  const bt = bled && bdown ? bled[0] - bdown[0] : -1;
  ok(!!bled && bt >= 11500 && bt < 16000, `B bleeds out after ~12 s (${bt} ms)`);
  ok(!!bled && bled[2].k === C.id, 'the bleed-out kill is credited to whoever put B down');
  // damage while down speeds it up: C downs E (30 HP) and bonks it again: 10 s of its 12 gone, it's over in ~2 s
  E.pos = (pos.get(E.id) || E.pos).slice(); C.pos = [E.pos[0] + 1.5, E.pos[1], E.pos[2]];
  t = ms();
  ok(await downBy(C, E), 'C downs E again');
  const edown = heard((m) => m.t === 'isle' && m.k === 'down' && m.id === E.id, t);
  await sleep(480);
  C.send({ t: 'hit', w: 'bread', to: E.id, d: [1, 0, 0] });
  const edead = await waitFor((m) => m.t === 'kill' && m.v === E.id, 10000, t);
  const et = edead && edown ? edead[0] - edown[0] : -1;
  ok(!!edead && et > 0 && et < 7000, `bonking downed E eats its bleed clock: out after ${et} ms, not 12 s`);
  // ---------------------------------------------------------- squad 2 out, squad 1 wins
  // C is squad 2's ... first down D (C up), then take C out: D gets finished, squad 2 is out at #2
  A.pos = at(22, 22); D.pos = at(24, 24); C.pos = at(0, 20); // (open ground with nothing between A and D: at(30, 30) is inside a building there)
  await settle([A, C, D]); await sleep(1500);
  ok(await downBy(A, D), 'A downs D');
  A.pos = at(0, 18);
  await settle([A]);
  A.face = C; await sleep(250);
  t = ms();
  for (let i = 0; i < 30 && !heard((m) => m.t === 'kill' && m.v === C.id, t); i++) { A.send({ t: 'hit', w: 'bread', to: C.id, d: [0, 0, 1] }); await sleep(500); }
  ok(!heard((m) => m.t === 'isle' && m.k === 'down' && m.id === C.id, t), 'C, the last one up in squad 2, isn\'t downed: it\'s out');
  const dk = await waitFor((m) => m.t === 'kill' && m.v === D.id, 8000, t);
  ok(!!dk && dk[2].k === A.id, 'downed D is finished off when its squad has nobody up (credited to A)');
  const so = await waitFor((m) => m.t === 'isle' && m.k === 'sqout' && m.sq === sq.get(C.id), 8000, t);
  ok(!!so && so[2].place === 2 && so[2].ids.includes(C.id) && so[2].ids.includes(D.id), `squad 2 is out at #2 (${so ? so[2].place : '-'})`);
  const win = await waitFor((m) => m.t === 'br' && m.k === 'win', 8000, t);
  ok(!!win && win[2].sq === sq.get(A.id) && win[2].ids.includes(B.id) && win[2].ids.includes(E.id), `last squad standing: squad ${win && win[2].sq} wins (the dead and downed in it too)`);
  const over = await waitFor((m, who) => who === 'Alfa' && m.t === 'round' && m.over, 12000, t);
  ok(!!over && over[2].isle && over[2].isle.win === sq.get(A.id) && over[2].br.find((r) => r[0] === B.id)[1] === 1 && over[2].br.find((r) => r[0] === C.id)[1] === 2, 'the round end: squad 1 #1 (B too), squad 2 #2');
  const perf = (who) => new Promise((res) => { const f = (d) => { const m = JSON.parse(d); if (m.t === 'perf') { who.ws.off('message', f); res(m); } }; who.ws.on('message', f); setTimeout(() => res(null), 3000); });
  clearInterval(snaps);
  ok(!/uncaught|TypeError|ReferenceError|RangeError/.test(srvErr), 'no server errors' + (srvErr ? ': ' + srvErr.slice(0, 800) : ''));
  void perf;
  console.log(fails ? `${fails} FAILED: ${failed.join(' | ')}` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
