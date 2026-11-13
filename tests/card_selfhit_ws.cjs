// thrown cards leave the thrower's hand at any angle (they used to start inside the thrower's own box when thrown on a
// diagonal, "hit" them and vanish at once, so a fan only ever flew when you aimed along the map's axes)
// (start a server with spades in hand: JF_CARD_HAND=s7,s8,s9,s10,s2 PORT=3119 node server.js; then node tests/card_selfhit_ws.cjs 3119)
const WS = require('ws');
const port = process.argv[2] || 3119, sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
(async () => {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { got: [], hand: [] };
  ws.on('message', (d) => { const m = JSON.parse(d); if (m.t === 'welcome') c.q = m.q; if (m.t === 'spawn') c.q = m.q; if (m.t === 'hand') c.hand = m.hand; if (m.t !== 'sn') c.got.push(m); });
  const send = (m) => ws.send(JSON.stringify(m));
  await new Promise((r) => ws.on('open', r));
  send({ t: 'join', name: 'dealer', mode: 'training', loadout: { primary: 'ar', secondary: 'cards', melee: 'knife' } });
  await sleep(1000);
  const pos = [5, 0, 10];
  const hold = async (ms) => { for (let t = 0; t < ms; t += 100) { send({ t: 's', q: c.q, p: pos, v: [0, 0, 0], y: 0, x: 0, w: 'cards' }); await sleep(100); } };
  await hold(1500);
  for (const deg of [0, 20, 45, 60, -35]) {
    let i = c.hand.findIndex((x) => x[0] === 's');
    for (let k = 0; i < 0 && k < 6; k++) { await hold(800); i = c.hand.findIndex((x) => x[0] === 's'); } // (a fresh hand deals itself)
    if (i < 0) { ok(false, `no spade in hand to throw at ${deg} deg (${c.hand})`); continue; }
    const a = deg * Math.PI / 180, d = [-Math.sin(a), -0.03, -Math.cos(a)], l = Math.hypot(...d);
    c.got = [];
    send({ t: 'fire', w: 'cards', i, o: [pos[0], pos[1] + 1.55, pos[2]], d: d.map((x) => x / l) });
    await hold(1600);
    const ps = new Map(c.got.filter((m) => m.t === 'ps' && m.k === 'card').map((m) => [m.id, m.p]));
    const flew = c.got.filter((m) => m.t === 'pd' && ps.has(m.id)).map((m) => Math.hypot(m.p[0] - ps.get(m.id)[0], m.p[2] - ps.get(m.id)[2]));
    ok(ps.size === 6 && flew.length === 6 && flew.every((f) => f > 2), `a spade fan ${deg} deg off the axis: ${ps.size} cards, flew ${flew.map((f) => f.toFixed(1)).join(' ')} m`);
    await hold(800);
  }
  console.log(fails ? `${fails} FAILED` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
