// battle island, step 1: the attack pass. tries to break the squad rules over real sockets: garbage and flooded
// messages, a downed pilot doing everything it shouldn't (shoot, loot, grapple, sprint, fly), a 'use' flood to revive
// faster, and the races (the reviver goes down mid-revive, the downed one leaves mid-revive, the reviver leaves, the
// last one up leaves with squadmates on the floor). A, B, E are squad 1, C, D squad 2. Online room, JF_GAME=island.
// starts its own server: node tests/island_attack_ws.cjs [port]
const WS = require('ws');
const { spawn } = require('child_process');
const path = require('path');
let port = Number(process.argv[2]) || 3184;
const port0 = port;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const failed = []; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) { fails++; failed.push(msg.slice(0, 80)); } };
const S = [0, 0, 24], at = (dx, dz) => [S[0] + dx, S[1], S[2] + dz];
let log = [], T0 = Date.now();
const ms = () => Date.now() - T0;
const pos = new Map(); // id -> where the server has them (from the snapshots everyone gets)
function client(name) {
  const c = { name, id: 0, q: 1, pos: at(0, 0), snap: true, ws: new WS(`ws://localhost:${port}/ws`) };
  c.send = (o) => { if (c.ws.readyState === 1) c.ws.send(typeof o === 'string' ? o : JSON.stringify(o)); };
  c.ws.on('message', (d) => {
    const m = JSON.parse(d);
    if (m.t === 'welcome') { c.id = m.id; c.q = m.q; }
    if (m.t === 'spawn' && m.q) c.q = m.q;
    if (m.t === 'sn') for (const e of m.p) { pos.set(e[0], [e[1], e[2], e[3]]); posMax.set(e[0], Math.max(posMax.has(e[0]) ? posMax.get(e[0]) : -1e9, e[2])); }
    if (m.t === 'isle' && m.k === 'fix') { c.fixes = (c.fixes || 0) + 1; if (!c.cheat) c.pos = m.p; }
    if (['isle', 'dmg', 'kill', 'br', 'heal', 'round'].includes(m.t)) log.push([ms(), name, m]);
  });
  c.ws.on('open', () => c.send({ t: 'join', name, mode: 'ffa' }));
  return c;
}
const heard = (pred, since = 0) => log.find((e) => e[0] >= since && pred(e[2], e[1]));
async function waitFor(pred, max, since = 0) { const t = Date.now(); while (Date.now() - t < max) { const e = heard(pred, since); if (e) return e; await sleep(50); } return null; }
// waiting on the server, not the clock (CPU-loaded machines): a condition with a deadline
async function until(fn, max = 8000) { const t = Date.now(); while (Date.now() - t < max) { if (fn()) return true; await sleep(50); } return !!fn(); }
const near = (c, p, tol = 0.6) => { const q = pos.get(c.id); return !!q && Math.hypot(q[0] - p[0], q[1] - p[1], q[2] - p[2]) < tol; };
async function settle(cs) { return until(() => cs.every((c) => near(c, c.pos)), 10000); } // the server has everyone where they say they are
// everyone in a squad (the latest 'sq' lists them all), then off the blimp (once it's moving) and down on the ground
async function ready(cs) {
  await until(() => cs.every((c) => c.id) && (() => { const e = [...log].reverse().find((x) => x[2].t === 'isle' && x[2].k === 'sq'); return e && cs.every((c) => e[2].l.some((r) => r[0] === c.id)); })(), 15000);
}
async function jumpAll(cs) {
  const t = ms();
  await until(() => { for (const c of cs) if (!heard((m) => m.t === 'br' && m.k === 'jump' && m.id === c.id, t)) c.send({ t: 'brjump' }); return cs.every((c) => heard((m) => m.t === 'br' && m.k === 'jump' && m.id === c.id, t)); }, 20000);
}
const posMax = new Map(); // id -> the highest the server has had them since it was cleared

(async () => {
  const srv = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(port), JF_GAME: 'island', JF_TRAFFIC: 'off', JF_ISLE_BLEED: '150' }, stdio: ['ignore', 'pipe', 'pipe'] });
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
  await ready(all);
  // ---------------------------------------------------------- garbage, from the blimp
  const junk = ['null', '[]', '"use"', '7', '{"t":"use","x":{"a":{"b":{"c":{"d":{"e":{"f":1}}}}}}}', '{"t":"use","id":1e400}', '{"t":"s","q":1,"p":[1e400,0,0],"v":[0,0,0]}',
    '{"t":"s","q":1,"p":"here","v":null}', '{"t":"brjump","x":[1,2,3]}', '{"t":"use","__proto__":{"dn":1}}', '{"t":"isle","k":"up","id":2}', '{"t":"isle","k":"rv","id":2,"by":4}', 'not json at all', '{"t":"hit","w":"bread","to":"2","d":[0,0,1]}'];
  for (let i = 0; i < 300; i++) C.send(junk[i % junk.length]);
  C.send({ t: 'use' }); A.send({ t: 'use' });
  await sleep(600);
  ok(!heard((m) => m.t === 'isle' && m.k === 'rv'), 'garbage + use from the blimp: nothing starts');
  // land everyone
  await jumpAll(all);
  A.pos = at(0, 0); B.pos = at(1.5, 0); E.pos = at(-1.5, 0); C.pos = at(1.5, 2.5); D.pos = at(30, 30);
  const snaps = setInterval(() => { for (const c of all) if (c.snap && c.ws.readyState === 1) c.send({ t: 's', q: c.q, p: c.pos, v: [0, 0, 0], y: 0, x: 0, w: 'bread', g: c.g || 0, f: c.f || 0 }); }, 100);
  await settle(all); await sleep(2000); // (landed: on the floor and still for 1.5 s)
  const downBy = async (atk, tgt) => { await settle([atk, tgt]); const t1 = ms(); for (let i = 0; i < 25; i++) { atk.send({ t: 'hit', w: 'bread', to: tgt.id, d: [1, 0, 0] }); if (await waitFor((m) => m.t === 'isle' && m.k === 'down' && m.id === tgt.id, 600, t1)) return true; } console.log('  dbg downBy', atk.name, tgt.name, JSON.stringify({ a: pos.get(atk.id), t: pos.get(tgt.id), dmg: log.filter((e) => e[0] >= t1 && e[2].t === 'dmg' && e[2].to === tgt.id).length })); return false; };
  { const e = [...log].reverse().find((x) => x[2].t === 'isle' && x[2].k === 'sq'); console.log('  phase 1 squads:', all.map((c) => `${c.name}=${new Map(e[2].l).get(c.id)}`).join(' '), 'jumped:', all.map((c) => !!heard((m) => m.t === 'br' && m.k === 'jump' && m.id === c.id)).join(','), 'pos ok:', all.map((c) => near(c, c.pos)).join(',')); }
  ok(await downBy(C, B), 'C downs B');
  // (review #1) flying while still "flung" by the bonk: one snapshot 40 m up
  B.cheat = true; B.fixes = 0; const bf = (pos.get(B.id) || B.pos).slice();
  const tb = ms(); C.send({ t: 'hit', w: 'bread', to: B.id, d: [1, 0, 0] }); await waitFor((m) => m.t === 'dmg' && m.to === B.id && m.dn, 3000, tb); // (a fresh shove: B is "flung")
  posMax.delete(B.id); B.pos = [bf[0], bf[1] + 40, bf[2]];
  await until(() => B.fixes > 0, 4000); await sleep(300);
  const bfy = posMax.get(B.id); // (the highest the server had B while it claimed to be 40 m up)
  B.pos = bf.slice(); await sleep(300);
  ok(B.fixes > 0 && bfy < bf[1] + 3, `flung by a bonk, a downed pilot can't jump 40 m up (${B.fixes} corrections, y ${bfy.toFixed(1)})`);
  B.cheat = false;
  // ---------------------------------------------------------- a downed pilot doing what it shouldn't
  let t = ms();
  const acts = [{ t: 'hit', w: 'bread', to: C.id, d: [0, 0, 1] }, { t: 'fire', w: 'bread' }, { t: 'push', w: 'hook', to: C.id, d: [0, 0, 1] }, { t: 'item', d: [0, 0, 1] }, { t: 'deploy', i: 0 }, { t: 'tbag' }, { t: 'parry' }, { t: 'spray', p: [0, 0, 0] },
    { t: 'slam' }, { t: 'cart' }, { t: 'mech', k: 'in' }, { t: 'brpick', i: 1, f: 1 }, { t: 'brheal', k: 'cola' }, { t: 'brkick' }, { t: 'use' }, { t: 'cough' }, { t: 'brdrop', k: 'gun', i: 0 }, { t: 'brswap' }, { t: 'lava' }];
  for (let i = 0; i < 3; i++) { for (const a of acts) { B.send(a); await sleep(20); } await sleep(300); }
  await sleep(600);
  ok(!heard((m) => (m.t === 'dmg' && m.to === B.id && m.w === 'cough') || (m.t === 'dmg' && m.from === B.id) || (m.t === 'isle' && m.k === 'rv' && m.by === B.id) || (m.t === 'br' && m.k === 'take' && m.by === B.id), t), 'downed B: 19 kinds of action (cough, drop and swap too), none do anything');
  // sprinting while down: 0.5 m every 100 ms (3x the crawl) for 3 s
  await sleep(1600); // (the shove from the last bonk wears off)
  B.cheat = true; const b0 = (pos.get(B.id) || B.pos).slice(); t = ms();
  for (let i = 0; i < 30; i++) { B.pos = [B.pos[0] + 0.5, B.pos[1], B.pos[2]]; await sleep(100); }
  await until(() => B.fixes > 0, 4000); await sleep(300);
  const b1 = pos.get(B.id), went = b1 ? Math.hypot(b1[0] - b0[0], b1[2] - b0[2]) : -1;
  ok(went >= 0 && went < 9.5 && B.fixes > 0, `sprinting while down: the server lets it crawl ${went.toFixed(1)} m of the 15 m tried (${B.fixes} corrections)`);
  // flying while down
  B.fixes = 0; B.pos = [b1[0], b1[1] + 6, b1[2]];
  await until(() => B.fixes > 0, 4000); await sleep(200);
  const b2 = pos.get(B.id);
  ok(B.fixes > 0 && b2 && b2[1] < b1[1] + 1, `flying while down: put back (y ${b2 && b2[1].toFixed(2)})`);
  // (review #1) climbing 0.7 m a snapshot (under the old per-snapshot limit) for 3 s
  B.cheat = true; B.fixes = 0; await sleep(400); const c0 = pos.get(B.id).slice();
  posMax.delete(B.id);
  for (let i = 0; i < 30; i++) { B.pos = [c0[0], c0[1] + 0.7 * (i + 1), c0[2]]; await sleep(100); }
  await until(() => B.fixes > 0, 4000); await sleep(300);
  const c1 = posMax.get(B.id);
  ok(c1 - c0[1] < 2.5 && B.fixes > 0, `a slow climb while down (0.7 m a snapshot, 21 m tried): ${(c1 - c0[1]).toFixed(1)} m at the highest`);
  B.pos = c0.slice(); B.cheat = false; await sleep(400);
  // a rope while down: the server drops it (everyone sees no rope)
  B.pos = b1.slice(); B.cheat = false; B.g = [b1[0], b1[1] + 20, b1[2]];
  await sleep(500);
  B.g = 0;
  // ---------------------------------------------------------- 'use' flood: 1000 a second doesn't make it faster
  B.pos = (pos.get(B.id) || b1).slice(); A.pos = [B.pos[0] + 1.2, B.pos[1], B.pos[2]];
  await settle([A]); t = ms();
  const flood = setInterval(() => { for (let i = 0; i < 5; i++) A.send({ t: 'use' }); }, 25); // (200 a second: 40x a real client, without starving A's own snapshots on a loaded machine)
  const up = await waitFor((m) => m.t === 'isle' && m.k === 'up' && m.id === B.id, 15000, t);
  clearInterval(flood);
  const st = heard((m) => m.t === 'isle' && m.k === 'rv' && m.id === B.id, t);
  if (!up) console.log('  dbg flood', JSON.stringify({ A: pos.get(A.id), B: pos.get(B.id), Apos: A.pos, ev: log.filter((e) => e[0] >= t - 500 && e[1] === 'Alfa' && (e[2].t === 'isle' && e[2].k !== 'st' || e[2].t === 'kill')).map((e) => e[2]).slice(0, 8) }));
  ok(up && st && up[0] - st[0] >= 3850, `a 'use' flood (200/s): still a ${up && st ? up[0] - st[0] : '?'} ms revive`);
  await sleep(300);
  // ---------------------------------------------------------- races
  // the reviver goes down mid-revive: it stops, the downed one stays down
  C.pos = [A.pos[0] + 1.5, A.pos[1], A.pos[2] + 1];
  ok(await downBy(C, B), 'C downs B again');
  // (review nice-to-have) letting go of F stops it at once; shooting stops it too
  const startRv = async () => { const t1 = ms(), k = setInterval(() => A.send({ t: 'use' }), 200); const r = await waitFor((m) => m.t === 'isle' && m.k === 'rv' && m.by === A.id, 6000, t1); clearInterval(k); return r; };
  await startRv();
  const tl = ms(); A.send({ t: 'use', up: 1 });
  const lg = await waitFor((m) => m.t === 'isle' && m.k === 'rvx' && m.by === A.id, 6000, tl);
  ok(!!lg && lg[2].why === 'released', `letting go of F stops the revive at once (${lg ? lg[2].why + ', ' + (lg[0] - tl) + ' ms' : '-'}: not the 1 s gap)`);
  await startRv();
  const ts = ms(); A.send({ t: 'fire', w: 'bread' });
  const sh = await waitFor((m) => m.t === 'isle' && m.k === 'rvx' && m.by === A.id, 6000, ts);
  ok(!!sh && sh[2].why === 'shot', `shooting stops the revive (${sh ? sh[2].why + ' ' + (sh[0] - ts) + ' ms' : '-'})`);
  await sleep(1200);
  await sleep(300); t = ms();
  const keep = setInterval(() => A.send({ t: 'use' }), 200);
  await waitFor((m) => m.t === 'isle' && m.k === 'rv' && m.by === A.id, 6000, t);
  ok(await downBy(C, A), 'C downs A in the middle of picking B up');
  clearInterval(keep);
  const x1 = await waitFor((m) => m.t === 'isle' && m.k === 'rvx' && m.by === A.id && m.why === 'down', 4000, t);
  await sleep(4500);
  ok(!!x1 && x1[2].why === 'down' && !heard((m) => m.t === 'isle' && m.k === 'up' && m.id === B.id, t), `the revive stops when the reviver goes down (${x1 ? x1[2].why : 'not stopped'}), B stays down`);
  // the downed one leaves mid-revive: no crash, the reviver is free again
  B.pos = (pos.get(B.id) || B.pos).slice(); E.pos = [B.pos[0] - 1, B.pos[1], B.pos[2]];
  await settle([E]); t = ms();
  const keepE = setInterval(() => E.send({ t: 'use' }), 200);
  const eb = await waitFor((m) => m.t === 'isle' && m.k === 'rv' && m.by === E.id, 8000, t);
  if (!eb) console.log('  dbg E', JSON.stringify({ E: pos.get(E.id), A: pos.get(A.id), B: pos.get(B.id), ev: log.filter((e) => e[0] >= t - 15000 && e[1] === 'Echo' && ((e[2].t === 'isle' && e[2].k !== 'st') || e[2].t === 'kill')).map((e) => [e[0] - t, e[2].t, e[2].k, e[2].id || e[2].v, e[2].by, e[2].why]) }));
  ok(!!eb, `E starts picking up ${eb && eb[2].id === B.id ? 'B' : 'A'}`);
  const who = eb && eb[2].id === B.id ? B : A, other = who === B ? A : B;
  E.pos = [other.pos[0] + 1, other.pos[1], other.pos[2]]; // (next to both of them)
  await settle([E]); t = ms();
  who.snap = false; who.ws.close();
  const eo = await waitFor((m) => m.t === 'isle' && m.k === 'rv' && m.by === E.id && m.id === other.id, 8000, t);
  await sleep(1000);
  ok(!!eo, `${who.name} left mid-revive: E moves on to ${other.name}`);
  // the reviver leaves mid-revive, and it was the last one up: the squad is out, the downed one finished
  t = ms();
  clearInterval(keepE); E.snap = false; E.ws.close();
  const fin = await waitFor((m) => m.t === 'kill' && m.v === other.id, 8000, t);
  const out = await waitFor((m) => m.t === 'isle' && m.k === 'sqout', 8000, t);
  ok(!!fin && !!out && out[2].place === 2, `the last one up leaves: ${other.name} (down) is finished, squad 1 out at #${out ? out[2].place : '?'}`);
  const win = await waitFor((m) => m.t === 'br' && m.k === 'win', 8000, t);
  ok(!!win && win[2].sq && win[2].ids.includes(C.id), 'squad 2 wins');
  // ---------------------------------------------------------- after the end: late 'use's, dead people's messages
  for (let i = 0; i < 50; i++) { C.send({ t: 'use' }); other.send({ t: 'use' }); D.send({ t: 's', q: D.q, p: [0, 1e6, 0], v: [0, 0, 0] }); }
  await sleep(500);
  const fresh = await new Promise((res) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(true); }); w.on('error', () => res(false)); });
  ok(fresh, 'the server is still up and taking connections');
  clearInterval(snaps);
  ok(!/uncaught|TypeError|ReferenceError|RangeError/.test(srvErr), 'no server errors' + (srvErr ? ': ' + srvErr.slice(0, 800) : ''));
  for (const c of all) c.ws.close();
  srv.kill();
  await phase2(); await phase3();
  console.log(fails ? `${fails} FAILED: ${failed.join(' | ')}` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();

// ---------------------------------------------------------- the review's must-fixes, on their own servers
async function boot(env) {
  const srv = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(port), JF_GAME: 'island', JF_TRAFFIC: 'off', JF_ISLE_SIZE: '2', ...env }, stdio: ['ignore', 'pipe', 'pipe'] });
  srv.err = ''; srv.stderr.on('data', (d) => { srv.err += d; }); srv.stdout.on('data', (d) => { if (/Error|uncaught/i.test(String(d))) srv.err += d; });
  process.on('exit', () => srv.kill());
  for (let i = 0; i < 60; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }
  return srv;
}
const lastSq = () => { const e = [...log].reverse().find((x) => x[2].t === 'isle' && x[2].k === 'sq'); return new Map(e ? e[2].l : []); };
const downer = async (atk, tgt) => { await settle([atk, tgt]); const t1 = ms(); for (let i = 0; i < 25; i++) { atk.send({ t: 'hit', w: 'bread', to: tgt.id, d: [1, 0, 0] }); if (await waitFor((m) => m.t === 'isle' && m.k === 'down' && m.id === tgt.id, 600, t1)) return true; } return false; };
async function geo() {
  const { MAPS } = await import('../shared/map.js'); await import('../shared/royale.js'); const { raycast } = await import('../shared/physics.js');
  const M = MAPS.jankburg, gy = (x, z) => { const g = raycast([x, 30, z], [0, -1, 0], 40, M.boxes); return g ? 30 - g.t : null; };
  const walls = []; // a wall (a fence, mostly) with open floor 2.7 m apart either side of it: in revive reach, no line between
  for (let x = -150; x <= 150; x += 1) for (let z = -150; z <= 150; z += 1) {
    const y = gy(x, z); if (y == null || Math.abs(y) > 0.3) continue;
    for (const d of [[1, 0], [0, 1]]) {
      const D = 2.7, h = raycast([x, y + 1.1, z], [d[0], 0, d[1]], D, M.boxes); if (!h || h.t < 0.35) continue;
      const f = [x + d[0] * D, z + d[1] * D], y2 = gy(f[0], f[1]); if (y2 == null || Math.abs(y2 - y) > 0.2) continue;
      const h2 = raycast([f[0], y + 1.1, f[1]], [-d[0], 0, -d[1]], D, M.boxes); if (!h2 || h2.t < 0.35) continue;
      if (raycast([x, y + 0.3, z], [0, 1, 0], 2.2, M.boxes) || raycast([f[0], y2 + 0.3, f[1]], [0, 1, 0], 2.2, M.boxes)) continue;
      walls.push([[x, y, z], [f[0], y2, f[1]]]);
    }
  }
  walls.sort((a, b) => Math.hypot(a[0][0], a[0][2]) - Math.hypot(b[0][0], b[0][2]));
  const wall = walls[0];
  const open = [];
  for (let x = -200; x <= 200; x += 8) for (let z = -200; z <= 200; z += 8) {
    const y = gy(x, z); if (y == null || Math.abs(y) > 0.3 || raycast([x, y + 0.3, z], [0, 1, 0], 40, M.boxes)) continue;
    let ok2 = true; for (let a = 0; a < 8 && ok2; a++) if (raycast([x, y + 1, z], [Math.cos(a * 0.785), 0, Math.sin(a * 0.785)], 7, M.boxes)) ok2 = false;
    if (ok2) open.push([x, y, z]);
  }
  return { wall, open };
}
async function phase2() {
  port = port0 + 1; log = []; T0 = Date.now(); pos.clear();
  const G = await geo();
  const srv = await boot({ JF_ISLE_ZONE: '0.05', JF_ISLE_BLEED: '60' });
  const cs = []; for (const n of ['P1', 'P2', 'P3', 'P4', 'P5']) { cs.push(client(n)); await until(() => cs[cs.length - 1].id, 8000); await sleep(400); }
  await ready(cs);
  // (review #2) late joiners: never the only squad, never into a full squad
  const sq = lastSq(), cnt = {}; for (const c of cs) cnt[sq.get(c.id)] = (cnt[sq.get(c.id)] || 0) + 1;
  console.log('  phase 2 squads:', cs.map((c) => `${c.name}=${sq.get(c.id)}`).join(' '));
  ok(sq.get(cs[0].id) !== sq.get(cs[1].id), 'the 2nd person in (a late boarder) gets a squad of their own, not the only one');
  ok(Object.values(cnt).every((n) => n <= 2) && Object.keys(cnt).length >= 3, `nobody lands in a full squad (${JSON.stringify(cnt)})`);
  // roles from whatever squads came out: X + Y together, Z an enemy
  let X = null, Y = null, Z = null;
  for (const a of cs) for (const b of cs) if (!X && a !== b && sq.get(a.id) === sq.get(b.id)) { X = a; Y = b; }
  Z = cs.find((c) => sq.get(c.id) !== sq.get(X.id));
  await jumpAll(cs);
  const [w1, w2] = G.wall;
  for (const c of cs) c.pos = G.open[0].slice();
  Y.pos = w1.slice(); Z.pos = [w1[0] + 0.01, w1[1], w1[2] + 0.01]; X.pos = w2.slice();
  const sn = setInterval(() => { for (const c of cs) if (c.snap && c.ws.readyState === 1) c.send({ t: 's', q: c.q, p: c.pos, v: [0, 0, 0], y: 0, x: 0, w: 'bread', g: 0, f: 0 }); }, 100);
  await settle(cs); await sleep(2000);
  ok(await downer(Z, Y), 'phase 2: Y goes down by a wall');
  // (review #3) X on the other side of the wall (2.7 m away, in reach): no revive through it
  await settle([X]); let t = ms();
  for (let i = 0; i < 6; i++) { X.send({ t: 'use' }); await sleep(200); }
  ok(!heard((m) => m.t === 'isle' && m.k === 'rv' && m.by === X.id, t), `no revive through a wall (${Math.hypot(w1[0] - w2[0], w1[2] - w2[2]).toFixed(1)} m apart, wall between)`);
  const away = [w1[0] - w2[0], w1[2] - w2[2]], al = Math.hypot(away[0], away[1]);
  X.pos = [w1[0] + away[0] / al * 1.2, w1[1], w1[2] + away[1] / al * 1.2]; await settle([X]); t = ms(); // (same side as Y now)
  const kx = setInterval(() => X.send({ t: 'use' }), 200);
  ok(!!(await waitFor((m) => m.t === 'isle' && m.k === 'rv' && m.by === X.id, 6000, t)), 'round the wall, it starts');
  clearInterval(kx); X.send({ t: 'use', up: 1 });
  // (review #1) zone shoves aren't a free run: a downed pilot outside the zone tries 10 m/s for 3 s
  const start = log.find((e) => e[2].t === 'br' && e[2].k === 'start')[2], fz = start.zone.steps[start.zone.steps.length - 1];
  const far = G.open.slice().sort((a, b) => Math.hypot(b[0] - fz.c[0], b[2] - fz.c[1]) - Math.hypot(a[0] - fz.c[0], a[2] - fz.c[1]))[0];
  const V = cs.find((c) => c !== Z && sq.get(c.id) === sq.get(Z.id)); // (Z's squadmate: Z stays up in the last ring, so V goes down, not out)
  Z.pos = [fz.c[0], 0, fz.c[1]]; V.pos = far.slice(); X.pos = [far[0] + 1.5, far[1], far[2]];
  await settle([X, V]);
  const vd = await downer(X, V);
  t = ms();
  const zoneHit = await waitFor((m) => m.t === 'dmg' && m.to === V.id && m.w === 'zone', 40000, t);
  ok(vd && !!zoneHit, `phase 2: ${V.name} is down outside the zone, getting shoved by it`);
  await sleep(1600); // (the bonk's own shove is over: only the zone's from here)
  V.cheat = true; V.fixes = 0; const v0 = pos.get(V.id).slice();
  for (let i = 0; i < 50; i++) { V.pos = [v0[0] + (i + 1), v0[1], v0[2]]; await sleep(100); }
  await until(() => V.fixes > 0, 4000); await sleep(300);
  const v1 = pos.get(V.id), moved = Math.hypot(v1[0] - v0[0], v1[2] - v0[2]);
  ok(moved < 30, `a downed pilot in the zone's shoves can't sprint off (${moved.toFixed(1)} m of 50 m tried in 5 s: the crawl + what the pushes slide you; ${V.fixes} corrections)`);
  clearInterval(sn);
  ok(!/uncaught|TypeError|ReferenceError|RangeError/.test(srv.err), 'no server errors (phase 2)' + (srv.err ? ': ' + srv.err.slice(0, 800) : ''));
  for (const c of cs) c.ws.close();
  srv.kill();
}
// (review nice-to-have) the winners' downed don't bleed out in the 3 s after the win. Z downs Y, then Z jumps into the
// void (an instant kill: no timing) and X's squad wins with Y still down. it only counts when Y's bleed-out was due inside
// those 3 s (the old code would have killed Y then); a slow machine that misses that gets another go
async function phase3() {
  let res = null;
  for (let attempt = 0; attempt < 3 && !(res && res.valid); attempt++) {
    port = port0 + 2 + attempt * 7; log = []; T0 = Date.now(); pos.clear();
    const srv = await boot({ JF_ISLE_BLEED: '3' });
    const cs = []; for (const n of ['Q1', 'Q2', 'Q3']) { cs.push(client(n)); await until(() => cs[cs.length - 1].id, 8000); await sleep(400); }
    await ready(cs);
    const sq = lastSq();
    let X = null, Y = null; for (const a of cs) for (const b of cs) if (!X && a !== b && sq.get(a.id) === sq.get(b.id)) { X = a; Y = b; }
    const Z = cs.find((c) => c !== X && c !== Y);
    await jumpAll(cs);
    X.pos = at(0, 0); Y.pos = at(1.5, 0); Z.pos = at(1.5, 2.5);
    const sn = setInterval(() => { for (const c of cs) if (c.ws.readyState === 1) c.send({ t: 's', q: c.q, p: c.pos, v: [0, 0, 0], y: 0, x: 0, w: 'bread', g: 0, f: 0 }); }, 100);
    await settle(cs); await sleep(2000);
    const dn = !!X && sq.get(Z.id) !== sq.get(X.id) && await downer(Z, Y);
    const td = ms();
    Z.pos = [Z.pos[0], -60, Z.pos[2]]; // into the void
    const win = await waitFor((m) => m.t === 'br' && m.k === 'win', 8000, td);
    const downAt = (heard((m) => m.t === 'isle' && m.k === 'down' && m.id === Y.id) || [0])[0];
    const deadBefore = win && heard((m) => m.t === 'kill' && m.v === Y.id && true, 0) && heard((m) => m.t === 'kill' && m.v === Y.id)[0] <= win[0];
    await sleep(3800);
    const killAfter = win ? heard((m) => m.t === 'kill' && m.v === Y.id, win[0] + 1) : null;
    const due = downAt + 3000; // (when Y's clock would have run out)
    res = { dn, won: !!win, valid: dn && !!win && !deadBefore && due > win[0] && due < win[0] + 3200, killAfter, lead: win ? due - win[0] : null };
    console.log(`  phase 3 attempt ${attempt + 1}: ${JSON.stringify({ ...res, killAfter: !!killAfter })}`);
    clearInterval(sn);
    if (attempt === 2 || res.valid) ok(!/uncaught|TypeError|ReferenceError|RangeError/.test(srv.err), 'no server errors (phase 3)' + (srv.err ? ': ' + srv.err.slice(0, 800) : ''));
    for (const c of cs) c.ws.close();
    srv.kill();
    await sleep(500);
  }
  ok(res.valid && !res.killAfter, `the winners' downed squadmate doesn't bleed out after the win (its clock ran out ${res.lead} ms into the 3.2 s)`);
}
