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
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
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
    if (m.t === 'sn') for (const e of m.p) pos.set(e[0], [e[1], e[2], e[3]]);
    if (m.t === 'isle' && m.k === 'fix') { c.fixes = (c.fixes || 0) + 1; if (!c.cheat) c.pos = m.p; }
    if (['isle', 'dmg', 'kill', 'br', 'heal', 'round'].includes(m.t)) log.push([ms(), name, m]);
  });
  c.ws.on('open', () => c.send({ t: 'join', name, mode: 'ffa' }));
  return c;
}
const heard = (pred, since = 0) => log.find((e) => e[0] >= since && pred(e[2], e[1]));
async function waitFor(pred, max, since = 0) { const t = Date.now(); while (Date.now() - t < max) { const e = heard(pred, since); if (e) return e; await sleep(50); } return null; }

(async () => {
  const srv = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(port), JF_GAME: 'island', JF_TRAFFIC: 'off', JF_ISLE_BLEED: '80' }, stdio: ['ignore', 'pipe', 'pipe'] });
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
  await sleep(1800);
  // ---------------------------------------------------------- garbage, from the blimp
  const junk = ['null', '[]', '"use"', '7', '{"t":"use","x":{"a":{"b":{"c":{"d":{"e":{"f":1}}}}}}}', '{"t":"use","id":1e400}', '{"t":"s","q":1,"p":[1e400,0,0],"v":[0,0,0]}',
    '{"t":"s","q":1,"p":"here","v":null}', '{"t":"brjump","x":[1,2,3]}', '{"t":"use","__proto__":{"dn":1}}', '{"t":"isle","k":"up","id":2}', '{"t":"isle","k":"rv","id":2,"by":4}', 'not json at all', '{"t":"hit","w":"bread","to":"2","d":[0,0,1]}'];
  for (let i = 0; i < 300; i++) C.send(junk[i % junk.length]);
  C.send({ t: 'use' }); A.send({ t: 'use' });
  await sleep(600);
  ok(!heard((m) => m.t === 'isle' && m.k === 'rv'), 'garbage + use from the blimp: nothing starts');
  // land everyone
  for (const c of all) c.send({ t: 'brjump' });
  A.pos = at(0, 0); B.pos = at(1.5, 0); E.pos = at(-1.5, 0); C.pos = at(1.5, 2.5); D.pos = at(30, 30);
  const snaps = setInterval(() => { for (const c of all) if (c.snap && c.ws.readyState === 1) c.send({ t: 's', q: c.q, p: c.pos, v: [0, 0, 0], y: 0, x: 0, w: 'bread', g: c.g || 0, f: c.f || 0 }); }, 100);
  await sleep(2200);
  const downBy = async (atk, tgt) => { const t1 = ms(); for (let i = 0; i < 12; i++) { atk.send({ t: 'hit', w: 'bread', to: tgt.id, d: [1, 0, 0] }); if (await waitFor((m) => m.t === 'isle' && m.k === 'down' && m.id === tgt.id, 480, t1)) return true; } return false; };
  ok(await downBy(C, B), 'C downs B');
  // (review #1) flying while still "flung" by the bonk: one snapshot 40 m up
  B.cheat = true; B.fixes = 0; const bf = (pos.get(B.id) || B.pos).slice();
  C.send({ t: 'hit', w: 'bread', to: B.id, d: [1, 0, 0] }); await waitFor((m) => m.t === 'dmg' && m.to === B.id && m.dn, 600, ms() - 50); // (a fresh shove: B is "flung")
  B.pos = [bf[0], bf[1] + 40, bf[2]]; await sleep(400);
  const bfy = pos.get(B.id)[1]; // (where the server has B while it claims to be 40 m up)
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
  await sleep(300);
  const b1 = pos.get(B.id), went = b1 ? Math.hypot(b1[0] - b0[0], b1[2] - b0[2]) : -1;
  ok(went >= 0 && went < 9.5 && B.fixes > 0, `sprinting while down: the server lets it crawl ${went.toFixed(1)} m of the 15 m tried (${B.fixes} corrections)`);
  // flying while down
  B.fixes = 0; B.pos = [b1[0], b1[1] + 6, b1[2]];
  await sleep(500);
  const b2 = pos.get(B.id);
  ok(B.fixes > 0 && b2 && b2[1] < b1[1] + 1, `flying while down: put back (y ${b2 && b2[1].toFixed(2)})`);
  // (review #1) climbing 0.7 m a snapshot (under the old per-snapshot limit) for 3 s
  B.cheat = true; B.fixes = 0; await sleep(400); const c0 = pos.get(B.id).slice();
  for (let i = 0; i < 30; i++) { B.pos = [c0[0], c0[1] + 0.7 * (i + 1), c0[2]]; await sleep(100); }
  await sleep(300);
  const c1 = pos.get(B.id);
  ok(c1[1] - c0[1] < 2.5 && B.fixes > 0, `a slow climb while down (0.7 m a snapshot, 21 m tried): ${(c1[1] - c0[1]).toFixed(1)} m allowed`);
  B.pos = c0.slice(); B.cheat = false; await sleep(400);
  // a rope while down: the server drops it (everyone sees no rope)
  B.pos = b1.slice(); B.cheat = false; B.g = [b1[0], b1[1] + 20, b1[2]];
  await sleep(500);
  B.g = 0;
  // ---------------------------------------------------------- 'use' flood: 1000 a second doesn't make it faster
  A.pos = [b1[0] + 1.2, b1[1], b1[2]];
  await sleep(300); t = ms();
  const flood = setInterval(() => { for (let i = 0; i < 10; i++) A.send({ t: 'use' }); }, 10);
  const up = await waitFor((m) => m.t === 'isle' && m.k === 'up' && m.id === B.id, 7000, t);
  clearInterval(flood);
  const st = heard((m) => m.t === 'isle' && m.k === 'rv' && m.id === B.id, t);
  if (!up) console.log('  dbg flood', JSON.stringify({ A: pos.get(A.id), B: pos.get(B.id), Apos: A.pos, ev: log.filter((e) => e[0] >= t - 500 && e[1] === 'Alfa' && (e[2].t === 'isle' && e[2].k !== 'st' || e[2].t === 'kill')).map((e) => e[2]).slice(0, 8) }));
  ok(up && st && up[0] - st[0] >= 3850, `a 'use' flood (1000/s): still a ${up && st ? up[0] - st[0] : '?'} ms revive`);
  await sleep(300);
  // ---------------------------------------------------------- races
  // the reviver goes down mid-revive: it stops, the downed one stays down
  C.pos = [A.pos[0] + 1.5, A.pos[1], A.pos[2] + 1];
  ok(await downBy(C, B), 'C downs B again');
  // (review nice-to-have) letting go of F stops it at once; shooting stops it too
  await sleep(300); t = ms();
  for (let i = 0; i < 3; i++) { A.send({ t: 'use' }); await sleep(200); }
  const tl = ms(); A.send({ t: 'use', up: 1 });
  const lg = await waitFor((m) => m.t === 'isle' && m.k === 'rvx' && m.by === A.id, 1500, tl);
  ok(!!lg && lg[0] - tl < 350, `letting go of F stops the revive at once (${lg ? lg[0] - tl : '-'} ms)`);
  await sleep(300);
  for (let i = 0; i < 3; i++) { A.send({ t: 'use' }); await sleep(200); }
  const ts = ms(); A.send({ t: 'fire', w: 'bread' }); A.send({ t: 'use' });
  const sh = await waitFor((m) => m.t === 'isle' && m.k === 'rvx' && m.by === A.id, 1500, ts);
  ok(!!sh && sh[2].why === 'shot' && sh[0] - ts < 350, `shooting stops the revive (${sh ? sh[2].why + ' ' + (sh[0] - ts) + ' ms' : '-'})`);
  await sleep(1200);
  await sleep(300); t = ms();
  const keep = setInterval(() => A.send({ t: 'use' }), 200);
  await waitFor((m) => m.t === 'isle' && m.k === 'rv' && m.by === A.id, 2000, t);
  ok(await downBy(C, A), 'C downs A in the middle of picking B up');
  clearInterval(keep);
  const x1 = heard((m) => m.t === 'isle' && m.k === 'rvx' && m.by === A.id, t);
  await sleep(4500);
  ok(!!x1 && x1[2].why === 'down' && !heard((m) => m.t === 'isle' && m.k === 'up' && m.id === B.id, t), `the revive stops when the reviver goes down (${x1 ? x1[2].why : 'not stopped'}), B stays down`);
  // the downed one leaves mid-revive: no crash, the reviver is free again
  E.pos = [B.pos[0] - 1, B.pos[1], B.pos[2]];
  await sleep(300); t = ms();
  const keepE = setInterval(() => E.send({ t: 'use' }), 200);
  const eb = await waitFor((m) => m.t === 'isle' && m.k === 'rv' && m.by === E.id, 2500, t);
  ok(!!eb, `E starts picking up ${eb && eb[2].id === B.id ? 'B' : 'A'}`);
  const who = eb && eb[2].id === B.id ? B : A, other = who === B ? A : B;
  E.pos = [other.pos[0] + 1, other.pos[1], other.pos[2]]; // (next to both of them)
  await sleep(300); t = ms();
  who.snap = false; who.ws.close();
  const eo = await waitFor((m) => m.t === 'isle' && m.k === 'rv' && m.by === E.id && m.id === other.id, 3000, t);
  await sleep(1000);
  ok(!!eo, `${who.name} left mid-revive: E moves on to ${other.name}`);
  // the reviver leaves mid-revive, and it was the last one up: the squad is out, the downed one finished
  t = ms();
  clearInterval(keepE); E.snap = false; E.ws.close();
  const fin = await waitFor((m) => m.t === 'kill' && m.v === other.id, 2500, t);
  const out = await waitFor((m) => m.t === 'isle' && m.k === 'sqout', 2500, t);
  ok(!!fin && !!out && out[2].place === 2, `the last one up leaves: ${other.name} (down) is finished, squad 1 out at #${out ? out[2].place : '?'}`);
  const win = await waitFor((m) => m.t === 'br' && m.k === 'win', 2500, t);
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
  console.log(fails ? `${fails} FAILED` : 'ALL OK'); process.exit(fails ? 1 : 0);
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
const downer = async (atk, tgt) => { const t1 = ms(); for (let i = 0; i < 12; i++) { atk.send({ t: 'hit', w: 'bread', to: tgt.id, d: [1, 0, 0] }); if (await waitFor((m) => m.t === 'isle' && m.k === 'down' && m.id === tgt.id, 480, t1)) return true; } return false; };
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
  const cs = []; for (const n of ['P1', 'P2', 'P3', 'P4', 'P5']) { cs.push(client(n)); await sleep(500); }
  await sleep(1500);
  // (review #2) late joiners: never the only squad, never into a full squad
  const sq = lastSq(), cnt = {}; for (const c of cs) cnt[sq.get(c.id)] = (cnt[sq.get(c.id)] || 0) + 1;
  console.log('  phase 2 squads:', cs.map((c) => `${c.name}=${sq.get(c.id)}`).join(' '));
  ok(sq.get(cs[0].id) !== sq.get(cs[1].id), 'the 2nd person in (a late boarder) gets a squad of their own, not the only one');
  ok(Object.values(cnt).every((n) => n <= 2) && Object.keys(cnt).length >= 3, `nobody lands in a full squad (${JSON.stringify(cnt)})`);
  // roles from whatever squads came out: X + Y together, Z an enemy
  let X = null, Y = null, Z = null;
  for (const a of cs) for (const b of cs) if (!X && a !== b && sq.get(a.id) === sq.get(b.id)) { X = a; Y = b; }
  Z = cs.find((c) => sq.get(c.id) !== sq.get(X.id));
  await sleep(1500);
  for (const c of cs) c.send({ t: 'brjump' });
  const [w1, w2] = G.wall;
  for (const c of cs) c.pos = G.open[0].slice();
  Y.pos = w1.slice(); Z.pos = [w1[0] + 0.01, w1[1], w1[2] + 0.01]; X.pos = w2.slice();
  const sn = setInterval(() => { for (const c of cs) if (c.snap && c.ws.readyState === 1) c.send({ t: 's', q: c.q, p: c.pos, v: [0, 0, 0], y: 0, x: 0, w: 'bread', g: 0, f: 0 }); }, 100);
  await sleep(2200);
  ok(await downer(Z, Y), 'phase 2: Y goes down by a wall');
  // (review #3) X on the other side of the wall (2.3 m away, in reach): no revive through it
  await sleep(300); let t = ms();
  for (let i = 0; i < 6; i++) { X.send({ t: 'use' }); await sleep(200); }
  ok(!heard((m) => m.t === 'isle' && m.k === 'rv' && m.by === X.id, t), `no revive through a wall (${Math.hypot(w1[0] - w2[0], w1[2] - w2[2]).toFixed(1)} m apart, wall between)`);
  const away = [w1[0] - w2[0], w1[2] - w2[2]], al = Math.hypot(away[0], away[1]);
  X.pos = [w1[0] + away[0] / al * 1.2, w1[1], w1[2] + away[1] / al * 1.2]; await sleep(300); t = ms(); // (same side as Y now)
  for (let i = 0; i < 4; i++) { X.send({ t: 'use' }); await sleep(200); }
  ok(!!heard((m) => m.t === 'isle' && m.k === 'rv' && m.by === X.id, t), 'round the wall, it starts');
  // (review #1) zone shoves aren't a free run: a downed pilot outside the zone tries 10 m/s for 3 s
  const start = log.find((e) => e[2].t === 'br' && e[2].k === 'start')[2], fz = start.zone.steps[start.zone.steps.length - 1];
  const far = G.open.slice().sort((a, b) => Math.hypot(b[0] - fz.c[0], b[2] - fz.c[1]) - Math.hypot(a[0] - fz.c[0], a[2] - fz.c[1]))[0];
  const V = cs.find((c) => c !== Z && sq.get(c.id) === sq.get(Z.id)); // (Z's squadmate: Z stays up in the last ring, so V goes down, not out)
  Z.pos = [fz.c[0], 0, fz.c[1]]; V.pos = far.slice(); X.pos = [far[0] + 1.5, far[1], far[2]];
  await sleep(1500);
  const vd = await downer(X, V);
  t = ms();
  const zoneHit = await waitFor((m) => m.t === 'dmg' && m.to === V.id && m.w === 'zone', 40000, t);
  ok(vd && !!zoneHit, `phase 2: ${V.name} is down outside the zone, getting shoved by it`);
  await sleep(1600); // (the bonk's own shove is over: only the zone's from here)
  V.cheat = true; V.fixes = 0; const v0 = pos.get(V.id).slice();
  for (let i = 0; i < 50; i++) { V.pos = [v0[0] + (i + 1), v0[1], v0[2]]; await sleep(100); }
  await sleep(300);
  const v1 = pos.get(V.id), moved = Math.hypot(v1[0] - v0[0], v1[2] - v0[2]);
  ok(moved < 30, `a downed pilot in the zone's shoves can't sprint off (${moved.toFixed(1)} m of 50 m tried in 5 s: the crawl + what the pushes slide you; ${V.fixes} corrections)`);
  clearInterval(sn);
  ok(!/uncaught|TypeError|ReferenceError|RangeError/.test(srv.err), 'no server errors (phase 2)' + (srv.err ? ': ' + srv.err.slice(0, 800) : ''));
  for (const c of cs) c.ws.close();
  srv.kill();
}
// (review nice-to-have) the winners' downed don't bleed out in the 3 s after the win
async function phase3() {
  port = port0 + 2; log = []; T0 = Date.now(); pos.clear();
  const srv = await boot({ JF_ISLE_BLEED: '4' });
  const cs = []; for (const n of ['Q1', 'Q2', 'Q3']) { cs.push(client(n)); await sleep(500); }
  await sleep(1500);
  const sq = lastSq();
  let X = null, Y = null; for (const a of cs) for (const b of cs) if (!X && a !== b && sq.get(a.id) === sq.get(b.id)) { X = a; Y = b; }
  const Z = cs.find((c) => c !== X && c !== Y);
  await sleep(1500);
  for (const c of cs) c.send({ t: 'brjump' });
  X.pos = at(0, 0); Y.pos = at(1.5, 0); Z.pos = at(1.5, 2.5);
  const sn = setInterval(() => { for (const c of cs) if (c.ws.readyState === 1) c.send({ t: 's', q: c.q, p: c.pos, v: [0, 0, 0], y: 0, x: 0, w: 'bread', g: 0, f: 0 }); }, 100);
  await sleep(2200);
  ok(!!X && sq.get(Z.id) !== sq.get(X.id) && await downer(Z, Y), 'phase 3: Y goes down (4 s to bleed out)');
  let t = ms();
  for (let i = 0; i < 8 && !heard((m) => m.t === 'kill' && m.v === Z.id, t); i++) { X.send({ t: 'hit', w: 'bread', to: Z.id, d: [0, 0, 1] }); await sleep(450); }
  const win = await waitFor((m) => m.t === 'br' && m.k === 'win', 2000, t);
  t = ms();
  await sleep(3600);
  ok(!!win && !heard((m) => m.t === 'kill' && m.v === Y.id, t - 2000), `the winners' downed squadmate doesn't bleed out after the win (${win ? 'won' : 'no win'})`);
  clearInterval(sn);
  ok(!/uncaught|TypeError|ReferenceError|RangeError/.test(srv.err), 'no server errors (phase 3)' + (srv.err ? ': ' + srv.err.slice(0, 800) : ''));
  for (const c of cs) c.ws.close();
  srv.kill();
}
