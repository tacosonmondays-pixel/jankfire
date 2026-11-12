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
  for (const c of [...cs, late, tr]) c.ws.close();
  console.log(fails ? `${fails} FAILED` : 'all ok');
  process.exit(fails ? 1 : 0);
})();
