// battle island, step 1: the attack pass. tries to break the squad rules over real sockets: garbage and flooded
// messages, a downed pilot doing everything it shouldn't (shoot, loot, grapple, sprint, fly), a 'use' flood to revive
// faster, and the races (the reviver goes down mid-revive, the downed one leaves mid-revive, the reviver leaves, the
// last one up leaves with squadmates on the floor). A, B, E are squad 1, C, D squad 2. Online room, JF_GAME=island.
// starts its own server: node tests/island_attack_ws.cjs [port]
const WS = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const port = Number(process.argv[2]) || 3184;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
const S = [0, 0, 24], at = (dx, dz) => [S[0] + dx, S[1], S[2] + dz];
const log = [], T0 = Date.now(), ms = () => Date.now() - T0;
const pos = new Map(); // id -> where the server has them (from the snapshots everyone gets)
function client(name) {
  const c = { name, id: 0, q: 1, pos: at(0, 0), snap: true, ws: new WS(`ws://localhost:${port}/ws`) };
  c.send = (o) => { if (c.ws.readyState === 1) c.ws.send(typeof o === 'string' ? o : JSON.stringify(o)); };
  c.ws.on('message', (d) => {
    const m = JSON.parse(d);
    if (m.t === 'welcome') { c.id = m.id; c.q = m.q; }
    if (m.t === 'spawn' && m.q) c.q = m.q;
    if (m.t === 'sn' && name === 'Charlie') for (const e of m.p) pos.set(e[0], [e[1], e[2], e[3]]);
    if (m.t === 'isle' && m.k === 'fix') { c.fixes = (c.fixes || 0) + 1; if (!c.cheat) c.pos = m.p; }
    if (['isle', 'dmg', 'kill', 'br', 'heal', 'round'].includes(m.t)) log.push([ms(), name, m]);
  });
  c.ws.on('open', () => c.send({ t: 'join', name, mode: 'ffa' }));
  return c;
}
const heard = (pred, since = 0) => log.find((e) => e[0] >= since && pred(e[2], e[1]));
async function waitFor(pred, max, since = 0) { const t = Date.now(); while (Date.now() - t < max) { const e = heard(pred, since); if (e) return e; await sleep(50); } return null; }

(async () => {
  const srv = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(port), JF_GAME: 'island', JF_TRAFFIC: 'off', JF_ISLE_BLEED: '40' }, stdio: ['ignore', 'pipe', 'pipe'] });
  let srvErr = ''; srv.stderr.on('data', (d) => { srvErr += d; }); srv.stdout.on('data', (d) => { if (/Error|uncaught/i.test(String(d))) srvErr += d; });
  process.on('exit', () => srv.kill());
  for (let i = 0; i < 60; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }
  const A = client('Alfa'); await sleep(400);
  const B = client('Bravo'); await sleep(250);
  const E = client('Echo'); await sleep(250);
  const C = client('Charlie'); await sleep(250);
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
  // ---------------------------------------------------------- a downed pilot doing what it shouldn't
  let t = ms();
  const acts = [{ t: 'hit', w: 'bread', to: C.id, d: [0, 0, 1] }, { t: 'fire', w: 'bread' }, { t: 'push', w: 'hook', to: C.id, d: [0, 0, 1] }, { t: 'item', d: [0, 0, 1] }, { t: 'deploy', i: 0 }, { t: 'tbag' }, { t: 'parry' }, { t: 'spray', p: [0, 0, 0] },
    { t: 'slam' }, { t: 'cart' }, { t: 'mech', k: 'in' }, { t: 'brpick', i: 1, f: 1 }, { t: 'brheal', k: 'cola' }, { t: 'brkick' }, { t: 'use' }];
  for (let i = 0; i < 3; i++) for (const a of acts) { B.send(a); await sleep(20); }
  await sleep(600);
  ok(!heard((m) => (m.t === 'dmg' && m.from === B.id) || (m.t === 'isle' && m.k === 'rv' && m.by === B.id) || (m.t === 'br' && m.k === 'take' && m.by === B.id), t), 'downed B: 15 kinds of action, none do anything');
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
  ok(up && st && up[0] - st[0] >= 3850, `a 'use' flood (1000/s): still a ${up && st ? up[0] - st[0] : '?'} ms revive`);
  await sleep(300);
  // ---------------------------------------------------------- races
  // the reviver goes down mid-revive: it stops, the downed one stays down
  C.pos = [A.pos[0] + 1.5, A.pos[1], A.pos[2] + 1];
  ok(await downBy(C, B), 'C downs B again');
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
  console.log(fails ? `${fails} FAILED` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
