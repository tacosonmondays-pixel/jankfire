// AUTO BOTS over ws (shared/autobots.js + room.js addHuman): an OFFLINE hub match (private, no bot count sent) gets
// the count picked for its mode + map: few on a small map, more on a big one, even teams in a team mode. CUSTOM (the
// classic bots setup: a count sent) still gets exactly its count; a silly count is clamped
// (start a server first: PORT=3100 node server.js; then node tests/autobots_ws.cjs 3100)
const WS = require('ws');
const port = process.argv[2] || 3100;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
// join, wait, and count: the bots in the room, and (team modes) how many fighters on each side
function room(mode, cfg) {
  const ws = new WS(`ws://localhost:${port}/ws`), bots = new Set(), team = new Map(); let me = 0, conf = null;
  ws.on('message', (d) => {
    const m = JSON.parse(d);
    if (m.t === 'welcome') { me = m.id; conf = m.cfg; for (const p of m.players) if (p.bot) bots.add(p.id); }
    if (m.t === 'pj' && m.bot) bots.add(m.id);
    if (m.t === 'pl') bots.delete(m.id);
    if (m.t === 'teams') for (const [id, t] of m.list) team.set(id, t);
  });
  return new Promise((res) => ws.on('open', () => {
    ws.send(JSON.stringify({ t: 'join', name: 'auto', mode, cfg }));
    setTimeout(() => { const sides = [0, 0]; for (const [id, t] of team) if (id === me || bots.has(id)) sides[t - 1]++; ws.close(); res({ bots: bots.size, sides, cfg: conf }); }, 2500);
  }));
}
(async () => {
  const small = await room('bots', { priv: true, game: 'dm', map: 'crate', hub: undefined });
  const big = await room('bots', { priv: true, game: 'dm', map: 'skyline' });
  ok(small.bots === 3, `offline quick play on a tiny map: 3 bots (${small.bots})`);
  ok(big.bots === 9, `offline quick play on a huge map: 9 bots (${big.bots})`);
  const tdm = await room('bots', { priv: true, game: 'tdm', map: 'suburb' });
  ok(tdm.bots === 7 && tdm.sides[0] === tdm.sides[1] && tdm.sides[0] === 4, `team deathmatch on a large map: even teams ${tdm.sides.join('v')} (${tdm.bots} bots)`);
  const custom = await room('bots', { game: 'dm', map: 'skyline', bots: 2, diff: 'easy' });
  ok(custom.bots === 2, `CUSTOM (the classic bots setup): its own count, 2 on a huge map (${custom.bots})`);
  const silly = await room('bots', { priv: true, game: 'dm', map: 'crate', bots: 500 });
  ok(silly.bots === 12, `a hand-made client asking for 500: clamped to 12 (${silly.bots})`);
  const junk = await room('bots', { priv: true, game: 'dm', map: 'crate', bots: 'lots' });
  ok(junk.bots === 3, `junk bot count: treated as none, the automatic 3 (${junk.bots})`);
  console.log(fails ? `${fails} FAILED` : 'all ok');
  process.exit(fails ? 1 : 0);
})();
