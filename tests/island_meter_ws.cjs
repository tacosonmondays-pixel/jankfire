// battle island, step 2 (PR B): hero picks, the MECH METER, energy cells, the call, the reset after a mech, and the
// island's zone schedule, over real sockets, with the exploit checks (spoofed meters, double calls, calling below 100
// or while down, far / full cell pick-ups, hero clashes, garbage). Online room, JF_GAME=island, squads of 2:
// A + B, C + D. phase 2 is a quick zone: a mech outside it loses armour, its pilot's HP is safe, people on foot bleed.
// starts its own servers: node tests/island_meter_ws.cjs [port]
const WS = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const port = Number(process.argv[2]) || 3190;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
const S = [0, 0, 24], at = (dx, dz) => [S[0] + dx, S[1], S[2] + dz];
const ROOT = path.join(__dirname, '..');
let log = [], T0 = Date.now();
const ms = () => Date.now() - T0;
function client(name, mf, prt) {
  const c = { name, id: 0, q: 1, pos: at(0, 0), snap: true, mm: [], ws: new WS(`ws://localhost:${prt}/ws`) };
  c.send = (o) => { if (c.ws.readyState === 1) c.ws.send(typeof o === 'string' ? o : JSON.stringify(o)); };
  c.ws.on('message', (d) => {
    const m = JSON.parse(d);
    if (m.t === 'welcome') { c.id = m.id; c.q = m.q; }
    if (m.t === 'spawn' && m.q) c.q = m.q;
    if (m.t === 'isle' && m.k === 'fix') c.pos = m.p;
    if (m.t === 'isle' && m.k === 'mm') c.mm.push([ms(), m.v, m.out]);
    if (m.t === 'mech' && m.k === 'pos' && Array.isArray(m.p)) c.pos = m.p;
    if (['isle', 'dmg', 'kill', 'br', 'mech', 'bhp', 'round'].includes(m.t)) log.push([ms(), name, m]);
  });
  c.ws.on('open', () => c.send({ t: 'join', name, mode: 'ffa', mf }));
  return c;
}
const heard = (pred, since = 0) => log.find((e) => e[0] >= since && pred(e[2], e[1]));
async function waitFor(pred, max, since = 0) { const t = Date.now(); while (Date.now() - t < max) { const e = heard(pred, since); if (e) return e; await sleep(50); } return null; }
const mmNow = (c) => (c.mm.length ? c.mm[c.mm.length - 1][1] : -1);
async function server(env, prt) {
  const srv = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: ROOT, env: { ...process.env, PORT: String(prt), JF_GAME: 'island', JF_TRAFFIC: 'off', JF_ISLE_SIZE: '2', ...env }, stdio: ['ignore', 'pipe', 'pipe'] });
  srv.err = ''; srv.stderr.on('data', (d) => { srv.err += d; }); srv.stdout.on('data', (d) => { if (/Error|uncaught/i.test(String(d))) srv.err += d; });
  process.on('exit', () => srv.kill());
  for (let i = 0; i < 60; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${prt}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }
  return srv;
}
const land = (cs) => { for (const c of cs) c.send({ t: 'brjump' }); };
const snapper = (cs) => setInterval(() => { for (const c of cs) if (c.snap && c.ws.readyState === 1) c.send({ t: 's', q: c.q, p: c.pos, v: [0, 0, 0], y: c.yaw || 0, x: 0, w: 'bread', g: 0, f: 0 }); }, 100);

(async () => {
  const { ISLE_ZONE, ISLE_FINAL } = await import('../shared/island.js');
  const srv = await server({ JF_ISLE_BLEED: '25', JF_MECH_DROP: '0.6', JF_MECH_WAIT: '4', JF_MECH_HP: '0.05' }, port);
  const A = client('Alfa', 'nightshift', port); await sleep(400);
  const B = client('Bravo', 'nightshift', port); await sleep(250);
  const C = client('Charlie', 'paperplane', port); await sleep(250);
  const D = client('Delta', undefined, port);
  const all = [A, B, C, D];
  await sleep(1800);
  // ---------------------------------------------------------- heroes
  const sqm = [...log].reverse().find((e) => e[2].t === 'isle' && e[2].k === 'sq')[2];
  const hero = new Map(sqm.hero), sq = new Map(sqm.l);
  console.log('  squads + heroes:', all.map((c) => `${c.name}=${sq.get(c.id)}/${hero.get(c.id)}`).join(' '));
  ok(sq.get(A.id) === sq.get(B.id) && sq.get(C.id) === sq.get(D.id) && sq.get(A.id) !== sq.get(C.id), 'squads of 2: A + B, C + D');
  ok(hero.get(A.id) === 'nightshift' && hero.get(B.id) === 'paperplane', 'A and B both want NIGHT SHIFT: A (first in) gets it, B gets PAPER PLANE');
  ok(new Set([hero.get(C.id), hero.get(D.id)]).size === 2, 'squad 2 has one of each too');
  let t = ms();
  B.send({ t: 'hero', h: 'nightshift' });
  const no = await waitFor((m, w) => w === 'Bravo' && m.t === 'isle' && m.k === 'hero' && m.no, 1500, t);
  ok(!!no && no[2].h === 'paperplane', `B asks for A's NIGHT SHIFT: refused (${no ? no[2].why : '-'})`);
  for (const h of [{}, null, 7, 'zzz', '__proto__', 'constructor', ['nightshift']]) B.send({ t: 'hero', h });
  for (let i = 0; i < 40; i++) A.send({ t: 'hero', h: i % 2 ? 'paperplane' : 'nightshift' }); // (flood: a few get through)
  await sleep(400);
  t = ms(); A.send({ t: 'hero', h: 'paperplane' });
  const noA = await waitFor((m, w) => w === 'Alfa' && m.t === 'isle' && m.k === 'hero' && m.no, 1500, t);
  ok(!!noA && !log.some((e) => e[0] >= t && e[2].t === 'isle' && e[2].k === 'hero' && !e[2].no), 'A asks for B\'s PAPER PLANE: refused too (squads of 2, 2 heroes: one each)');
  ok(!log.some((e) => e[2].t === 'isle' && e[2].k === 'hero' && !e[2].no && e[2].id === A.id && e[2].h !== 'nightshift'), 'the garbage picks and a 40-message flood changed nothing');
  t = ms(); C.send({ t: 'deploy', r: 'mechdrop', at: [0, 0, 0] }); await sleep(500);
  ok(!heard((m) => m.t === 'mech' && (m.k === 'call' || m.k === 'no'), t), 'a call from the blimp: ignored');
  // ---------------------------------------------------------- land
  await sleep(1200);
  land(all);
  A.pos = at(0, 0); B.pos = at(1.5, 0); C.pos = at(1.5, 2.5); D.pos = at(25, 25);
  const snaps = snapper(all);
  await sleep(2400);
  t = ms(); A.send({ t: 'hero', h: 'nightshift' });
  const late = await waitFor((m, w) => w === 'Alfa' && m.t === 'isle' && m.k === 'hero' && m.no, 1500, t);
  ok(!!late && late[2].why === 'only on the blimp', 'no hero swaps after you jump');
  // ---------------------------------------------------------- the meter: spoofs, the call below 100, time
  for (const o of [{ t: 'isle', k: 'mm', v: 100 }, { t: 'mm', v: 100 }, { t: 'meter', v: 100 }, { t: 'isle', k: 'cell' }, { t: 'brpick', i: -1 }, { t: 'deploy', r: 'mechdrop' }, { t: 'deploy', r: 'mechdrop', at: [1e400, 0, 0] }, { t: 'deploy', r: 'chickenstrike', at: at(0, -8) }]) A.send(o);
  await sleep(400); // (past the call's rate limit)
  t = ms(); A.send({ t: 'deploy', r: 'mechdrop', at: at(0, -8) });
  const low = await waitFor((m, w) => w === 'Alfa' && m.t === 'mech' && m.k === 'no', 1500, t);
  await sleep(300);
  ok(!!low && /meter at/.test(low[2].why) && !heard((m) => m.t === 'mech' && m.k === 'call'), `spoofed meters and the call below 100%: refused (${low ? low[2].why : '-'})`);
  ok(mmNow(A) < 15, `the meter is the server's (A at ${mmNow(A)}% after the spoofs)`);
  const m0 = mmNow(A), t0 = ms();
  await sleep(6000);
  const m1 = mmNow(A), secs = (ms() - t0) / 1000, rate = (m1 - m0) / secs;
  ok(rate > 0.8 && rate < 1.5, `time fills it: ${rate.toFixed(2)}%/s (full in ~${Math.round(100 / rate)} s, the table says 90)`);
  // damage: +1% per 10 dealt (bread: 40)
  let b4 = mmNow(A); t = ms();
  A.send({ t: 'hit', w: 'bread', to: C.id, d: [0, 0, 1] });
  await waitFor((m) => m.t === 'dmg' && m.from === A.id && m.to === C.id, 1500, t); await sleep(350);
  const dHit = mmNow(A) - b4 - (ms() - t) / 1000 * 1.11;
  ok(dHit > 2.8 && dHit < 5.5, `a 40-damage hit: +${dHit.toFixed(1)}% (4 by the table)`);
  // a kill: +25. C goes down (D's up), then A finishes it off
  for (let i = 0; i < 6 && !heard((m) => m.t === 'isle' && m.k === 'down' && m.id === C.id, t); i++) { A.send({ t: 'hit', w: 'bread', to: C.id, d: [0, 0, 1] }); await sleep(480); }
  let kill = null;
  for (let i = 0; i < 8 && !kill; i++) { b4 = mmNow(A); const t1 = ms(); A.send({ t: 'hit', w: 'bread', to: C.id, d: [0, 0, 1] }); kill = await waitFor((m) => m.t === 'kill' && m.v === C.id, 480, t1); }
  await sleep(400);
  const dKill = mmNow(A) - b4;
  ok(!!kill && dKill >= 27 && dKill <= 32, `finishing C: +${dKill}% (25 for the kill + 4 for the hit)`);
  // ---------------------------------------------------------- energy cells
  const start = [...log].find((e) => e[2].t === 'br' && e[2].k === 'start')[2];
  const cells = start.loot.filter((l) => l[1] === 'cell').map((l) => ({ i: l[0], p: [l[6], l[7], l[8]] }));
  ok(cells.length >= 10, `energy cells on the floor at the start (${cells.length} of ${start.loot.length} loot)`);
  const pickAt = async (c, cell, off = 0) => { c.pos = [cell.p[0] + off, cell.p[1], cell.p[2]]; await sleep(350); const t1 = ms(); c.send({ t: 'brpick', i: cell.i, f: 1 }); return waitFor((m) => m.t === 'br' && m.k === 'take' && m.i === cell.i && m.by === c.id, 700, t1); };
  ok(!(await pickAt(A, cells[0], 9)), 'a cell 9 m away: no');
  b4 = mmNow(A);
  ok(!!(await pickAt(A, cells[0])), 'standing on it: taken');
  await sleep(400);
  ok(mmNow(A) - b4 >= 19 && mmNow(A) - b4 <= 21.5 || mmNow(A) === 100, `a cell: +${mmNow(A) - b4}%`);
  let ci = 1;
  while (mmNow(A) < 100 && ci < 8) await pickAt(A, cells[ci++]);
  await sleep(400);
  ok(mmNow(A) === 100, `the meter caps at 100 (${mmNow(A)}%)`);
  const ready = heard((m, w) => w === 'Alfa' && m.t === 'isle' && m.k === 'mm' && m.v === 100);
  ok(!!ready, 'MECH READY is sent');
  ok(!(await pickAt(A, cells[ci])), 'a full meter leaves the next cell on the floor');
  // ---------------------------------------------------------- the call at 100%, double calls, one mech at a time
  A.pos = at(0, 0); await sleep(500);
  t = ms(); A.send({ t: 'deploy', r: 'mechdrop', at: at(0, -200) });
  const farC = await waitFor((m, w) => w === 'Alfa' && m.t === 'mech' && m.k === 'no', 1200, t);
  await sleep(400);
  ok(!!farC && mmNow(A) === 100 && !heard((m) => m.t === 'mech' && m.k === 'call', t), `a call aimed 200 m away: refused by MECH DROP's own check (${farC ? farC[2].why : '-'}), the meter stays full`);
  t = ms();
  A.send({ t: 'deploy', r: 'mechdrop', at: at(0, -8) }); A.send({ t: 'deploy', r: 'mechdrop', at: at(3, -8) });
  const call = await waitFor((m) => m.t === 'mech' && m.k === 'call' && m.o === A.id, 1500, t);
  await sleep(700);
  ok(!!call && call[2].f === 'nightshift', `at 100% the streak key calls A's hero in with MECH DROP (${call ? call[2].f : 'no call'})`);
  ok(log.filter((e) => e[0] >= t && e[1] === 'Delta' && e[2].t === 'mech' && e[2].k === 'call').length === 1, 'two calls at once: one mech');
  ok(mmNow(A) === 0, `the meter empties on the call (${mmNow(A)}%)`);
  A.send({ t: 'deploy', r: 'mechdrop', at: at(-3, -8) });
  const twice = await waitFor((m, w) => w === 'Alfa' && m.t === 'mech' && m.k === 'no', 1000, ms());
  ok(!!twice, `calling again with one out: refused (${twice ? twice[2].why : '-'})`);
  await sleep(2000);
  ok(mmNow(A) === 0 && !(await pickAt(A, cells[ci + 1])), 'with a mech out the meter stays empty and cells stay on the floor');
  A.pos = at(0, 0);
  // the mech isn't climbed into: it flies off after JF_MECH_WAIT (4 s) and the meter restarts at 25
  const gone = await waitFor((m) => m.t === 'mech' && m.k === 'gone', 6000, t);
  await sleep(500);
  ok(!!gone && mmNow(A) >= 25 && mmNow(A) <= 27, `the unused mech flies off: meter back to ${mmNow(A)}%`);
  // ---------------------------------------------------------- eject: B fills up, calls NIGHT SHIFT, climbs in, D breaks it
  B.pos = at(1.5, 0);
  while (mmNow(B) < 100 && ci < cells.length - 2) await pickAt(B, cells[ci++]);
  B.pos = at(4, 0); await sleep(600);
  t = ms(); B.send({ t: 'deploy', r: 'mechdrop', at: at(4, -8) });
  const bc = await waitFor((m) => m.t === 'mech' && m.k === 'call' && m.o === B.id, 1500, t);
  ok(!!bc && bc[2].f === 'paperplane', 'B calls its PAPER PLANE');
  await waitFor((m) => m.t === 'mech' && m.k === 'land' && m.o === B.id, 3000, t);
  B.pos = at(4, -8); await sleep(400); B.send({ t: 'mech', k: 'in' });
  const bin = await waitFor((m) => m.t === 'mech' && m.k === 'in' && m.id === B.id, 1500, t);
  ok(!!bin, 'B climbs in (MECH DROP\'s own climb-in)');
  D.pos = at(4, -5.5); await sleep(1500); t = ms();
  for (let i = 0; i < 8 && !heard((m) => m.t === 'mech' && m.k === 'down' && m.id === B.id, t); i++) { D.send({ t: 'hit', w: 'bread', to: B.id, d: [0, 0, -1] }); await sleep(480); }
  const ej = await waitFor((m) => m.t === 'mech' && m.k === 'down' && m.id === B.id, 1500, t);
  await sleep(500);
  ok(!!ej && mmNow(B) >= 25 && mmNow(B) <= 27, `B's mech breaks (EJECT): B's meter restarts at ${mmNow(B)}%`);
  // ---------------------------------------------------------- calling while down
  while (mmNow(B) < 100 && ci < cells.length - 1) await pickAt(B, cells[ci++]);
  B.pos = at(1.5, 0); D.pos = at(1.5, 2.5); await sleep(1500);
  t = ms();
  for (let i = 0; i < 6 && !heard((m) => m.t === 'isle' && m.k === 'down' && m.id === B.id, t); i++) { D.send({ t: 'hit', w: 'bread', to: B.id, d: [0, 0, -1] }); await sleep(480); }
  ok(!!heard((m) => m.t === 'isle' && m.k === 'down' && m.id === B.id, t) && mmNow(B) === 100, 'B is down with a full meter');
  B.send({ t: 'deploy', r: 'mechdrop', at: at(1.5, -8) });
  await sleep(800);
  ok(!heard((m) => m.t === 'mech' && m.k === 'call' && m.o === B.id, t), 'calling while down: nothing');
  // ---------------------------------------------------------- the zone schedule
  const z = start.zone, st = z.steps;
  const k = st[0].wait / ISLE_ZONE[0][0];
  const total = st.reduce((s, x) => s + x.wait + x.shrink, 0);
  ok(st.length === 5 && st.every((s, i) => Math.abs(s.wait - ISLE_ZONE[i][0] * k) < 0.01 && Math.abs(s.shrink - ISLE_ZONE[i][1] * k) < 0.01 && s.dps === ISLE_ZONE[i][3]), `5 rings on the island's table (${st.map((s) => `${s.wait}+${s.shrink}s r${s.r}`).join(', ')})`);
  ok(total >= 650 && total <= 780, `about 12 minutes of rings (${Math.round(total)} s = ${(total / 60).toFixed(1)} min)`);
  ok(st[4].r >= ISLE_FINAL.r, `the last ring is ${st[4].r * 2} m across (40 at least)`);
  let inside = true, prev = { c: z.c0, r: z.r0 };
  for (const s of st) { if (Math.hypot(s.c[0] - prev.c[0], s.c[1] - prev.c[1]) > prev.r - s.r + 0.05 || s.r > prev.r) inside = false; prev = s; }
  ok(inside, 'each ring sits inside the one before');
  const { MAPS } = await import('../shared/map.js'); await import('../shared/royale.js'); const { raycast } = await import('../shared/physics.js');
  const M = MAPS.jankburg, f = st[4], floor = [];
  for (let i = 0; i <= 8; i++) { const a = i * Math.PI / 4, r = i ? f.r * 0.8 : 0, h = raycast([f.c[0] + Math.cos(a) * r, 120, f.c[1] + Math.sin(a) * r], [0, -1, 0], 160, M.boxes); floor.push(h ? +(120 - h.t).toFixed(1) : null); }
  ok(floor.every((y) => y != null && y > M.killY + 2), `the last ring has floor all round, no void (${floor.join(' ')})`);
  clearInterval(snaps);
  for (const c of all) c.ws.close();
  ok(!/uncaught|TypeError|ReferenceError|RangeError/.test(srv.err), 'no server errors' + (srv.err ? ': ' + srv.err.slice(0, 800) : ''));
  srv.kill();

  // ---------------------------------------------------------- phase 2: a quick zone. a mech outside it, a pilot on foot outside it
  log = []; T0 = Date.now();
  const p2 = port + 1, srv2 = await server({ JF_ISLE_ZONE: '0.04', JF_ISLE_METER: '60', JF_MECH_DROP: '0.5', JF_MECH_WAIT: '30', JF_ISLE_BLEED: '120' }, p2);
  const P = client('Pilot', 'nightshift', p2); await sleep(400);
  const W2 = client('Wingman', 'paperplane', p2); await sleep(250);
  const E = client('Enemy', 'paperplane', p2);
  const all2 = [P, W2, E];
  await sleep(1800);
  const z2 = (await waitFor((m) => m.t === 'br' && m.k === 'start', 3000))[2].zone, fz = z2.steps[4];
  // stand well away from where the last ring ends up (open ground: the middle square, 24 m out)
  const far = [[0, 24], [0, -24], [24, 0], [-24, 0]].map(([x, zz]) => [x, 0, zz]).sort((a, b) => Math.hypot(b[0] - fz.c[0], b[2] - fz.c[1]) - Math.hypot(a[0] - fz.c[0], a[2] - fz.c[1]))[0];
  await sleep(1500); // (the blimp has to be moving before anyone can jump)
  land(all2);
  P.pos = far.slice(); W2.pos = [far[0] + 1.5, 0, far[2]]; E.pos = [fz.c[0], 0, fz.c[1]]; // (the enemy waits in the last ring: the match doesn't end)
  const snaps2 = snapper(all2);
  for (let i = 0; i < 40 && mmNow(P) < 100; i++) await sleep(250);
  const dir = Math.hypot(far[0], far[2]) > 1 ? [-far[0] / Math.hypot(far[0], far[2]), -far[2] / Math.hypot(far[0], far[2])] : [0, -1];
  const spot = [far[0] + dir[0] * 7, 0, far[2] + dir[1] * 7];
  t = ms(); P.send({ t: 'deploy', r: 'mechdrop', at: spot });
  await waitFor((m) => m.t === 'mech' && m.k === 'land' && m.o === P.id, 3000, t);
  P.pos = spot.slice(); await sleep(400); P.send({ t: 'mech', k: 'in' });
  const pin = await waitFor((m) => m.t === 'mech' && m.k === 'in' && m.id === P.id, 2000, t);
  if (!pin) console.log('  dbg P', mmNow(P), JSON.stringify(log.filter((e) => e[1] === 'Pilot' && (e[2].t === 'mech' || (e[2].t === 'isle' && e[2].k !== 'st'))).map((e) => e[2])).slice(0, 600));
  ok(!!pin, `phase 2: P calls and climbs into its mech (${Math.round(Math.hypot(spot[0] - fz.c[0], spot[2] - fz.c[1]))} m from the last ring's middle, r ${fz.r})`);
  const zoneEnd = z2.t0 + z2.steps.reduce((s, x) => s + (x.wait + x.shrink) * 1000, 0);
  t = ms();
  await sleep(Math.max(2000, zoneEnd - Date.now() + 2500));
  const armour = log.filter((e) => e[0] >= t && e[2].t === 'bhp' && e[2].id === P.id).map((e) => e[2].hp);
  const pHurt = log.some((e) => e[0] >= t && e[2].t === 'dmg' && e[2].to === P.id);
  ok(armour.length >= 2 && armour[armour.length - 1] < armour[0], `outside the zone the mech's armour drains (${armour[0]} -> ${armour[armour.length - 1]})`);
  ok(!pHurt, 'and the pilot inside takes no HP damage');
  ok(log.some((e) => e[0] >= t && e[2].t === 'dmg' && e[2].to === W2.id && e[2].w === 'zone'), 'a pilot on foot outside it takes HP damage');
  clearInterval(snaps2);
  ok(!/uncaught|TypeError|ReferenceError|RangeError/.test(srv2.err), 'no server errors (phase 2)' + (srv2.err ? ': ' + srv2.err.slice(0, 800) : ''));
  srv2.kill();
  console.log(fails ? `${fails} FAILED` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
