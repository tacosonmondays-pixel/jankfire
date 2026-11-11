// the card deck's spade fan, with a forced hand: a spade throws a flat fan of 6 (a face spade 24), aimed where you
// look, the right width, and the cards really hurt whoever stands in it
// (start a server with the hand forced: JF_CARD_HAND=s7,s2,s12,h5,c9 PORT=3100 node server.js; then node tests/spadefan_ws.cjs 3100)
const WS = require('ws');
const port = process.argv[2] || 3100;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
function client(name) {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, got: [], id: 0, q: 0, hp: 100, hand: null };
  ws.on('message', (d) => { const m = JSON.parse(d); if (m.t === 'welcome') { c.id = m.id; c.q = m.q; } if (m.t === 'spawn') c.q = m.q; if (m.t === 'hand') c.hand = m.hand; if (m.t === 'sn') { const r = m.p.find((x) => x[0] === c.id); if (r) c.hp = r[10]; return; } c.got.push(m); });
  c.send = (m) => ws.send(JSON.stringify(m));
  c.place = (p, w = 'ar') => c.send({ t: 's', q: c.q, p, v: [0, 0, 0], y: 0, x: 0, w });
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'join', name, mode: 'ffa' }); setTimeout(() => res(c), 800); }));
}
(async () => {
  const A = await client('dealer'), B = await client('mark');
  const y = 90, o = [700, y + 1.6, 0], d = [0, 0, -1];
  const hold = (ms, dist) => (async () => { for (let t = 0; t < ms; t += 100) { A.place([700, y, 0], 'cards'); B.place([700, y, -dist]); await sleep(100); } })();
  const shots = () => A.got.filter((m) => m.t === 'ps' && m.k === 'card' && m.o === A.id);
  await hold(600, 60);
  ok(A.hand && A.hand.join() === 's7,s2,s12,h5,c9', 'forced hand dealt: ' + (A.hand && A.hand.join()));
  const play = async (i, dist) => { const b = shots().length, hp = B.hp; A.send({ t: 'fire', w: 'cards', o, d, i }); await hold(900, dist); return { cards: shots().slice(b), lost: hp - B.hp }; };
  const ang = (v) => Math.atan2(v[0], -v[2]);
  // s7 with the mark 6 m in front
  const r1 = await play(0, 6), a1 = r1.cards.map((c) => ang(c.v)).sort((x, z) => x - z);
  ok(r1.cards.length === 6, `7 of spades threw ${r1.cards.length} cards (want 6)`);
  ok(a1.length === 6 && Math.abs(a1[5] - a1[0] - 0.16) < 0.02 && Math.abs(a1[0] + a1[5]) < 0.02, `fan is ${(a1[5] - a1[0]).toFixed(3)} rad wide, centred on the aim (want 0.16)`);
  ok(r1.cards.every((c) => Math.abs(Math.hypot(...c.v) - 85) < 3), 'every card flies at 85 m/s');
  const per = 11 + 0.6 * 7;
  ok(r1.lost > 0, `mark 6 m away lost ${r1.lost} HP (${(r1.lost / per).toFixed(1)} cards of ${per.toFixed(1)} landed)`);
  // s2 (now index 0... the hand shifted): still a full fan, weaker cards
  await hold(2500, 60); // out of the way while it heals nothing; just spacing
  const hp2 = B.hp, r2 = await play(0, 6);
  ok(r2.cards.length === 6, `2 of spades threw ${r2.cards.length} cards (want 6: the rank is only the damage)`);
  ok(r2.lost > 0, `2 of spades still hurts: ${r2.lost} HP (the mark only had ${hp2} left after the 7)`);
  // s12 (queen): the ultimate, 24 cards over a wide arc
  await hold(1200, 60);
  const r3 = await play(0, 60), a3 = r3.cards.map((c) => ang(c.v)).sort((x, z) => x - z);
  ok(r3.cards.length === 24, `queen of spades threw ${r3.cards.length} cards (want 24)`);
  ok(a3.length === 24 && Math.abs(a3[23] - a3[0] - 0.9) < 0.05, `the big fan is ${(a3.length ? a3[23] - a3[0] : 0).toFixed(2)} rad wide (want 0.9)`);
  // h5: not a spade, flicks 2
  await hold(1200, 60);
  const r4 = await play(0, 60);
  ok(r4.cards.length === 2, `5 of hearts flicked ${r4.cards.length} cards (want 2)`);
  console.log(fails ? `${fails} FAILED` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
