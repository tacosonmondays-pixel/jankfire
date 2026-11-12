// BATTLE ISLAND + parties over real sockets: the Online room plays island (JF_GAME=island). three strangers walk in
// first, then a party of two comes in on its tickets. the old pick (late boarders take the fullest squad with room)
// split it (X, Z, lead | Y, pal); now the party lands in one squad. starts its own server: node tests/isleparty_ws.cjs [port]
const WS = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const port = Number(process.argv[2]) || 3192;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
function hub(name) {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, name, party: null, go: [] };
  ws.on('message', (d) => { const m = JSON.parse(d); if (m.t === 'party') c.party = m; if (m.t === 'pgo') c.go.push(m); });
  c.send = (m) => ws.send(JSON.stringify(m));
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'hub', name, look: { color: '#ff4fd8' } }); setTimeout(() => res(c), 400); }));
}
let sq = null;
function player(name, cfg) {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, id: 0, name };
  ws.on('message', (d) => { const m = JSON.parse(d); if (m.t === 'welcome') c.id = m.id; if (m.t === 'isle' && m.k === 'sq') sq = new Map(m.l); });
  return new Promise((res) => ws.on('open', () => { ws.send(JSON.stringify({ t: 'join', name, mode: 'ffa', cfg })); setTimeout(() => res(c), 700); }));
}
(async () => {
  const srv = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(port), JF_GAME: 'island', JF_TRAFFIC: 'off' }, stdio: ['ignore', 'pipe', 'pipe'] });
  let srvErr = ''; srv.stderr.on('data', (d) => { srvErr += d; });
  process.on('exit', () => srv.kill());
  for (let i = 0; i < 60; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }
  const A = await hub('lead'), B = await hub('pal');
  B.send({ t: 'pjoin', code: A.party.code }); await sleep(500);
  ok(A.party.ms.length === 2, 'a party of two');
  const X = await player('Xray'), Y = await player('Yankee'), Z = await player('Zulu');
  A.send({ t: 'pgo', mode: 'ffa', cfg: {} }); await sleep(600);
  ok(A.go[0] && B.go[0] && A.go[0].cfg.ticket && B.go[0].cfg.ticket, 'START: a ticket each');
  const PA = await player('lead', A.go[0].cfg), PB = await player('pal', B.go[0].cfg);
  const all = [X, Y, Z, PA, PB];
  for (let t = 0; t < 600 && !(sq && all.every((c) => sq.has(c.id))); t++) await sleep(100);
  ok(sq && all.every((c) => sq.has(c.id)), 'everyone got a squad');
  console.log('  squads:', all.map((c) => `${c.name}=${sq && sq.get(c.id)}`).join(' '));
  ok(sq && sq.get(PA.id) === sq.get(PB.id), 'the party lands in one squad');
  ok(sq && new Set(all.map((c) => sq.get(c.id))).size >= 2, 'still at least two squads (someone has to win)');
  ok(!/Error/.test(srvErr), 'no server errors ' + srvErr.slice(0, 200));
  for (const c of [A, B, ...all]) c.ws.close();
  console.log(fails ? `${fails} FAILED` : 'ALL OK');
  process.exit(fails ? 1 : 0);
})();
