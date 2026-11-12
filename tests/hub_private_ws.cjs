// The hub's PRIVATE match (public/js/hubmenu.js -> cfg.priv, server/room.js roomFor): over plain ws.
// a private bots room gets its own room; a With Bots pick of the same mode, another private pick, a Quick Play With Bots
// pick never land in it; a non-boolean priv is just an ordinary bots pick; its settings (mode, map) stick
// (start a server first: PORT=3100 node server.js; then node tests/hub_private_ws.cjs 3100)
const WS = require('ws');
const port = process.argv[2] || 3100;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
function client(name, join) {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, id: 0, seen: new Set(), cfg: null, game: null };
  ws.on('message', (d) => {
    const m = JSON.parse(d);
    if (m.t === 'welcome') { c.id = m.id; if (m.cfg) c.cfg = m.cfg; if (m.round && m.round.game) c.game = m.round.game; if (m.game) c.game = m.game; }
    if (m.t === 'cfg' && m.cfg) c.cfg = m.cfg;
    if (m.t === 'sn' && Array.isArray(m.p)) for (const r of m.p) c.seen.add(r[0]);
  });
  c.send = (m) => ws.send(JSON.stringify(m));
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'join', name, ...join }); setTimeout(() => res(c), 1200); }));
}
const together = (a, b) => a.seen.has(b.id) || b.seen.has(a.id);
(async () => {
  const A = await client('host', { mode: 'bots', cfg: { priv: true, game: 'tdm', map: 'crate', bots: 3, diff: 'hard', hip: 'tight' } });
  const B = await client('stranger', { mode: 'bots', cfg: { game: 'tdm', map: 'crate', bots: 3 } }); // the old With Bots CUSTOM pick of the same mode
  const C = await client('another', { mode: 'bots', cfg: { priv: true, game: 'tdm', map: 'crate', bots: 3 } }); // someone else's private match
  const D = await client('qp', { mode: 'bots', cfg: { lobby: 'qp' } }); // With Bots Quick Play: drops into any room with a bot to replace
  const E = await client('junk', { mode: 'bots', cfg: { priv: 'yes', game: 'tdm', map: 'crate', bots: 3 } }); // priv must be true, not truthy
  await sleep(1500);
  ok(A.id && B.id && C.id && D.id && E.id, 'everyone got in');
  ok(!together(A, B), 'a With Bots pick of the same mode does not join the private match');
  ok(!together(A, C), 'two private matches are two rooms');
  ok(!together(A, D), 'With Bots Quick Play does not drop into a private match');
  ok(!together(A, E), "priv: 'yes' is not private (and does not get in either)");
  ok(together(B, E), "priv: 'yes' is an ordinary With Bots pick (it joins the stranger's room)");
  ok(A.cfg && A.cfg.map === 'crate' && A.cfg.diff === 'hard' && A.cfg.hip === 'tight', 'the private match keeps its settings ' + JSON.stringify(A.cfg));
  for (const c of [A, B, C, D, E]) c.ws.close();
  console.log(fails ? `${fails} FAILED` : 'all ok');
  process.exit(fails ? 1 : 0);
})();
