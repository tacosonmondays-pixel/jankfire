// The room cap (server/room.js roomFor MAX_ROOMS): a packed server doesn't make new rooms, it sends you to the online
// room. Start the server with a tiny cap: JF_MAX_ROOMS=3 PORT=3100 node server.js; then node tests/rooms_cap_ws.cjs 3100
const WS = require('ws');
const port = process.argv[2] || 3100;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
function join(name, mode, cfg) {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, mode: null };
  ws.on('message', (d) => { const m = JSON.parse(d); if (m.t === 'welcome') c.mode = m.mode; });
  return new Promise((res) => ws.on('open', () => { ws.send(JSON.stringify({ t: 'join', name, mode, cfg })); setTimeout(() => res(c), 1200); }));
}
(async () => {
  const cs = [];
  for (let i = 0; i < 3; i++) cs.push(await join('p' + i, 'bots', { priv: true, game: 'dm', map: 'crate', bots: 1 }));
  ok(cs.every((c) => c.mode === 'bots'), 'under the cap: private bots rooms, as asked');
  const late = await join('late', 'bots', { priv: true, game: 'dm', map: 'crate', bots: 1 });
  ok(late.mode === 'ffa', 'packed: the next private match goes to the online room instead (' + late.mode + ')');
  const tr = await join('trainee', 'training');
  ok(tr.mode === 'ffa', 'packed: training too (' + tr.mode + ')');
  // a party's START on a packed server: everyone to the same (online) room, together
  const hub = (name) => { const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, party: null, go: [] }; ws.on('message', (d) => { const m = JSON.parse(d); if (m.t === 'party') c.party = m; if (m.t === 'pgo') c.go.push(m); }); c.send = (m) => ws.send(JSON.stringify(m)); return new Promise((res) => ws.on('open', () => { c.send({ t: 'hub', name, look: {} }); setTimeout(() => res(c), 400); })); };
  const L = await hub('lead'), M = await hub('mate'); M.send({ t: 'pjoin', code: L.party.code }); await sleep(500);
  L.send({ t: 'pgo', mode: 'bots', cfg: { game: 'dm', map: 'crate', bots: 2 } }); await sleep(600);
  const gl = L.go[0], gm = M.go[0];
  ok(gl && gm && gl.mode === 'ffa' && gm.mode === 'ffa' && gl.cfg.room === gm.cfg.room, 'packed + a party START: both sent to the online room ' + JSON.stringify(gl && [gl.mode, gl.cfg.room]));
  const seen = new Set(), PL = new WS(`ws://localhost:${port}/ws`), PM = new WS(`ws://localhost:${port}/ws`); let idL = 0, idM = 0;
  PL.on('message', (d) => { const m = JSON.parse(d); if (m.t === 'welcome') idL = m.id; if (m.t === 'sn') for (const r of m.p) seen.add(r[0]); });
  PM.on('message', (d) => { const m = JSON.parse(d); if (m.t === 'welcome') idM = m.id; });
  await Promise.all([new Promise((r) => PL.on('open', r)), new Promise((r) => PM.on('open', r))]);
  PL.send(JSON.stringify({ t: 'join', name: 'lead', mode: gl.mode, cfg: gl.cfg })); PM.send(JSON.stringify({ t: 'join', name: 'mate', mode: gm.mode, cfg: gm.cfg })); await sleep(1800);
  ok(idL && idM && seen.has(idM), 'and they land in it together');
  for (const c of [L, M]) c.ws.close(); PL.close(); PM.close();
  for (const c of [...cs, late, tr]) c.ws.close();
  console.log(fails ? `${fails} FAILED` : 'all ok');
  process.exit(fails ? 1 : 0);
})();
