// the big map's PINGS over real sockets (server/pings.js). Two servers, one after the other:
// 1. BATTLE ISLAND (JF_GAME=island): A + B share a squad, C is the other squad. A's ping reaches A and B, never C.
//    Training and a bots room are solo: only you see yours. Junk (Infinity, strings, arrays, deep objects, off the map,
//    __proto__) is dropped without a word, the rate limit holds (3 per 2.5 s, 250 ms apart) and says so once.
// 2. TEAM DEATHMATCH (JF_GAME=tdm): a teammate gets it, someone on the other team doesn't.
// starts its own servers: node tests/mapping_ws.cjs [port]
const WS = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const port = Number(process.argv[2]) || 3176;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };

function client(name, join = {}) {
  const c = { name, id: 0, got: [], sq: 0, team: 0, ws: new WS(`ws://localhost:${port}/ws`) };
  c.send = (o) => { if (c.ws.readyState === 1) c.ws.send(typeof o === 'string' ? o : JSON.stringify(o)); };
  c.ws.on('message', (d) => {
    const m = JSON.parse(d);
    if (m.t === 'welcome') { c.id = m.id; c.team = m.team || 0; }
    if (m.t === 'teams') for (const [id, t] of m.list) if (id === c.id) c.team = t;
    if (m.t === 'isle' && m.k === 'sq') c.sqList = m.l;
    if (m.t === 'mping') c.got.push(m);
  });
  c.ws.on('open', () => c.send({ t: 'join', name, mode: 'ffa', ...join }));
  return c;
}
const pings = (c) => c.got.filter((m) => !m.no);
const clear = (cs) => { for (const c of cs) c.got.length = 0; };
async function until(fn, max = 8000) { const t = Date.now(); while (Date.now() - t < max) { if (fn()) return true; await sleep(50); } return !!fn(); }
async function server(env) {
  const srv = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(port), JF_TRAFFIC: 'off', ...env }, stdio: ['ignore', 'pipe', 'pipe'] });
  srv.err = ''; srv.stderr.on('data', (d) => { srv.err += d; }); srv.stdout.on('data', (d) => { if (/Error|uncaught/i.test(String(d))) srv.err += d; });
  process.on('exit', () => srv.kill());
  for (let i = 0; i < 60; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }
  return srv;
}
const stop = (srv) => new Promise((r) => { srv.on('exit', r); srv.kill(); });

(async () => {
  // ---------------------------------------------------------- 1. battle island squads (Jankburg: zone0 300 m round 0,0)
  let srv = await server({ JF_GAME: 'island' });
  const A = client('Alfa'); await sleep(400);
  const C = client('Charlie'); await sleep(250);
  const B = client('Bravo');
  const all = [A, B, C];
  await until(() => all.every((c) => c.id && c.sqList && all.every((o) => c.sqList.some((r) => r[0] === o.id))), 15000);
  const sq = new Map((A.sqList || []).map((r) => [r[0], r[1]]));
  console.log('  squads:', all.map((c) => `${c.name}=${sq.get(c.id)}`).join(' '));
  ok(sq.get(A.id) && sq.get(A.id) === sq.get(B.id) && sq.get(A.id) !== sq.get(C.id), 'island: A + B share a squad, C is the other one');
  clear(all);
  A.send({ t: 'mping', x: 10.5, y: 2, z: -20.26 });
  await until(() => pings(A).length && pings(B).length, 3000); await sleep(400);
  const pa = pings(A)[0], pb = pings(B)[0];
  ok(pa && pb && pa.id === pb.id && pa.by === A.id && pa.p[0] === 10.5 && pa.p[2] === -20.3, 'island: the pinger and their squadmate get the ping ' + JSON.stringify(pb));
  ok(!pings(C).length, 'island: the other squad never hears it');
  clear(all);
  C.send({ t: 'mping', x: -40, y: 0, z: 40 });
  await until(() => pings(C).length, 3000); await sleep(400);
  ok(pings(C).length === 1 && !pings(A).length && !pings(B).length, "island: C's own ping only goes to C (no squadmate yet)");
  // a client can't pick its side: a team / squad / by field in the message changes nothing
  clear(all);
  C.send({ t: 'mping', x: 5, y: 1, z: 5, sq: sq.get(A.id), team: 1, by: A.id, to: [A.id, B.id] });
  await until(() => pings(C).length, 3000); await sleep(400);
  ok(pings(C).length === 1 && pings(C)[0].by === C.id && !pings(A).length && !pings(B).length, 'island: extra fields (sq / team / by / to) are ignored, the side comes from the server');

  // ---------------------------------------------------------- junk: dropped, nobody hears anything, still connected
  await sleep(2700); clear(all);
  const junk = [
    '{"t":"mping","x":1e999,"y":0,"z":0}', '{"t":"mping","x":0,"y":-1e999,"z":0}', '{"t":"mping","x":null,"y":0,"z":0}',
    { t: 'mping', x: '5', y: 0, z: 0 }, { t: 'mping', x: [5], y: 0, z: 0 }, { t: 'mping', x: { valueOf: 5 }, y: 0, z: 0 }, { t: 'mping', x: true, y: 0, z: 0 },
    { t: 'mping', x: 5, z: 0 }, { t: 'mping' }, { t: 'mping', x: 99999, y: 0, z: 0 }, { t: 'mping', x: 0, y: 0, z: -1e7 }, { t: 'mping', x: 0, y: 5000, z: 0 },
    { t: 'mping', x: 0, y: -900, z: 0 }, { t: 'mping', x: 400, y: 0, z: 0 }, '{"t":"mping","__proto__":{"x":1,"y":1,"z":1}}',
    { t: 'mping', x: 1, y: 1, z: 1, a: { b: { c: { d: { e: { f: { g: 1 } } } } } } }, { t: 'mping', p: [1, 1, 1] }, '{"t":"mping","x":1,"y":1,"z":"NaN"}',
  ];
  for (const j of junk) { A.send(j); await sleep(270); }
  await sleep(500);
  ok(!pings(A).length && !pings(B).length && !pings(C).length, `junk: ${junk.length} bad pings, none relayed (${pings(A).map((m) => JSON.stringify(m.p)).join(' ')})`);
  ok(A.ws.readyState === 1, 'junk: still connected');

  // ---------------------------------------------------------- the rate limit
  clear(all);
  A.send({ t: 'mping', x: 1, y: 0, z: 1 }); A.send({ t: 'mping', x: 2, y: 0, z: 2 }); // 2nd one < 250 ms later
  await sleep(300);
  for (let i = 0; i < 6; i++) { A.send({ t: 'mping', x: 3 + i, y: 0, z: 3 }); await sleep(300); }
  await sleep(400);
  const got = pings(B).map((m) => m.p[0]);
  ok(got.length === 3 && got[0] === 1 && got[1] === 3 && got[2] === 4, 'rate limit: 3 per 2.5 s, the too-quick 2nd dropped ' + JSON.stringify(got));
  ok(A.got.filter((m) => m.no).length === 1 && !B.got.some((m) => m.no), 'rate limit: the pinger hears "slow down" once, the squad hears nothing');
  await sleep(2600); clear(all);
  A.send({ t: 'mping', x: 7, y: 0, z: 7 });
  await until(() => pings(B).length, 3000);
  ok(pings(B).length === 1, 'rate limit: pings again after the window');

  // ---------------------------------------------------------- solo: training + a bots room only ever hear themselves
  clear(all);
  const T = client('Trainee', { mode: 'training' }), Bo = client('Botter', { mode: 'bots', cfg: { bots: 1 } });
  await until(() => T.id && Bo.id, 8000); await sleep(1500);
  T.send({ t: 'mping', x: 0, y: 0, z: 0 }); Bo.send({ t: 'mping', x: 0, y: 0, z: 0 });
  await until(() => pings(T).length && pings(Bo).length, 3000); await sleep(400);
  ok(pings(T).length === 1 && pings(T)[0].by === T.id, 'training: you see your own ping');
  ok(pings(Bo).length === 1 && pings(Bo)[0].by === Bo.id, 'bots room: you see your own ping');
  ok(![A, B, C].some((c) => pings(c).length) && !pings(T).some((m) => m.by === Bo.id), 'solo rooms: nobody else hears them');
  T.send({ t: 'mping', x: 900, y: 0, z: 0 }); await sleep(400);
  ok(pings(T).length === 1, 'training: off the range map is dropped');
  ok(!/Error|uncaught/i.test(srv.err), 'server 1: no errors ' + srv.err.slice(0, 300));
  for (const c of [...all, T, Bo]) c.ws.close();
  await stop(srv);

  // ---------------------------------------------------------- 2. team deathmatch (islands: x ±127, z ±115)
  srv = await server({ JF_GAME: 'tdm' });
  const P = [client('Pink'), client('Blue'), client('Teal'), client('Lime')];
  await until(() => P.every((c) => c.id && c.team), 10000); await sleep(800);
  console.log('  teams:', P.map((c) => `${c.name}=${c.team}`).join(' '));
  const a = P[0], mate = P.find((c) => c !== a && c.team === a.team), foe = P.find((c) => c.team && c.team !== a.team);
  ok(!!mate && !!foe, 'tdm: found a teammate and an enemy');
  clear(P);
  a.send({ t: 'mping', x: 20, y: 3, z: -15 });
  await until(() => mate && pings(mate).length, 3000); await sleep(400);
  ok(mate && pings(mate).length === 1 && pings(a).length === 1, 'tdm: the teammate gets it (and so do you)');
  ok(foe && !pings(foe).length, 'tdm: the other team never does');
  a.send({ t: 'mping', x: 200, y: 0, z: 0 }); await sleep(400);
  ok(pings(a).length === 1, 'tdm: past the edge of Islands is dropped');
  ok(!/Error|uncaught/i.test(srv.err), 'server 2: no errors ' + srv.err.slice(0, 300));
  for (const c of P) c.ws.close();
  await stop(srv);
  console.log(fails ? `${fails} FAILED` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
