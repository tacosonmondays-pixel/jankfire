// a map still being built (map.wip, e.g. Battle Island) in your own OFFLINE match: the hub sends wip: true when the page
// has ?wip=1 (public/js/hubmenu.js), and only a private bots room takes it (server/room.js addHuman). without the flag,
// with a junk flag, in a public bots room, an online lobby or for a mode that can't play the map: the usual map instead.
// the server's own rotation is untouched (WIP_ON stays env-only): run the server WITHOUT JF_WIP_MAPS
// (start a server first: PORT=3100 node server.js; then node tests/wip_offline_ws.cjs 3100)
const WS = require('ws');
const port = process.argv[2] || 3100;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
function client(name, join) {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, id: 0, cfg: null, game: null };
  ws.on('message', (d) => {
    const m = JSON.parse(d);
    if (m.t === 'welcome') { c.id = m.id; if (m.cfg) c.cfg = m.cfg; if (m.game) c.game = m.game; }
    if (m.t === 'cfg' && m.cfg) c.cfg = m.cfg;
  });
  c.send = (m) => ws.send(JSON.stringify(m));
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'join', name, ...join }); setTimeout(() => res(c), 1500); }));
}
const ISLE = { priv: true, game: 'island', map: 'battleisland', bots: 5 };
(async () => {
  const A = await client('tester', { mode: 'bots', cfg: { ...ISLE, wip: true } });
  const B = await client('noflag', { mode: 'bots', cfg: { ...ISLE } });
  const H = await client('hub', { mode: 'bots', cfg: { priv: true, game: 'island', map: 'battleisland', hub: 'isle', wip: true } }); // exactly what the hub sends now: no bot count (the server picks it, shared/autobots.js)
  const junk = [];
  for (const w of ['true', 1, {}, [true], null]) junk.push(await client('junk', { mode: 'bots', cfg: { ...ISLE, wip: w } }));
  const P = await client('public', { mode: 'bots', cfg: { game: 'island', map: 'battleisland', bots: 5, wip: true } }); // not priv
  const L = await client('lobby', { mode: 'ffa', cfg: { lobby: 'isle', map: 'battleisland', wip: true } });
  const O = await client('online', { mode: 'ffa', cfg: { map: 'battleisland', wip: true } });
  const D = await client('dm', { mode: 'bots', cfg: { priv: true, game: 'dm', map: 'battleisland', bots: 3, wip: true } }); // a royale-only map, not for deathmatch
  const N = await client('nomap', { mode: 'bots', cfg: { priv: true, game: 'island', map: 'nope', wip: true } });
  await sleep(1000);
  const map = (c) => c.cfg && c.cfg.map;
  ok(A.id && map(A) === 'battleisland', 'a private bots room with wip: true plays Battle Island (' + map(A) + ', ' + A.game + ')');
  ok(A.game === 'island', 'and it plays the island mode (' + A.game + ')');
  ok(H.id && map(H) === 'battleisland' && H.cfg.bots > 0, 'the hub\'s own pick (no bot count) plays Battle Island with bots picked for it (' + map(H) + ', ' + (H.cfg && H.cfg.bots) + ' bots)');
  ok(B.id && map(B) && map(B) !== 'battleisland', 'without the flag: the fallback map (' + map(B) + ')');
  junk.forEach((c, i) => ok(c.id && map(c) !== 'battleisland', `junk wip value #${i} is ignored (${map(c)})`));
  ok(P.id && map(P) !== 'battleisland', 'a public bots room ignores the flag (' + map(P) + ')');
  ok(L.id && map(L) !== 'battleisland', 'an online lobby ignores the flag (' + map(L) + ')');
  ok(O.id && map(O) !== 'battleisland', 'the online room ignores the flag (' + map(O) + ')');
  ok(D.id && map(D) !== 'battleisland', 'a mode that cannot play the map (deathmatch) does not get it (' + map(D) + ')');
  ok(N.id && map(N) !== 'nope', 'an unknown map is ignored (' + map(N) + ')');
  for (const c of [A, B, H, ...junk, P, L, O, D, N]) c.ws.close();
  console.log(fails ? `${fails} FAILED` : 'all ok');
  process.exit(fails ? 1 : 0);
})();
