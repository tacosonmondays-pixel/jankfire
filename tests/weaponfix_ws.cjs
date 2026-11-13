// Blood Cross thin shots, the bow's faster arrows and the card deck's fixed fan, over plain ws
// (start a server first: PORT=3100 node server.js; then node tests/weaponfix_ws.cjs 3100)
const WS = require('ws');
const port = process.argv[2] || 3100;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
(async () => {
  const ws = new WS(`ws://localhost:${port}/ws`), got = []; let me = 0, q = 0, hand = null, hp = 100;
  ws.on('message', (d) => { const m = JSON.parse(d); if (m.t === 'welcome') { me = m.id; q = m.q; } if (m.t === 'hand') hand = m.hand; if (m.t === 'sn') { const r = m.p.find((x) => x[0] === me); if (r) hp = r[10]; return; } got.push(m); });
  const send = (m) => ws.send(JSON.stringify(m));
  await new Promise((r) => ws.on('open', r));
  send({ t: 'join', name: 'fixer', mode: 'ffa' }); await sleep(800);
  const y = 80, X = 20, Z = 20, o = [X, y + 1.6, Z], d = [0, 0, -1]; // (inside Islands' bounds, the online room's first map: outside them the out-of-bounds void kills you after ~3 s)
  send({ t: 's', q, p: [X, y, Z], v: [0, 0, 0], y: 0, x: 0, w: 'bow' }); await sleep(200);
  const shots = (k) => got.filter((m) => m.t === 'ps' && m.k === k && m.o === me);
  // bow: a full draw flies at the new top speed
  send({ t: 'fire', w: 'bow', o, d, c: 1 }); await sleep(300);
  const a = shots('bow')[0]; ok(a && Math.abs(Math.hypot(...a.v)) > 100, 'bow: full draw arrow speed ' + (a ? Math.hypot(...a.v).toFixed(0) : 'none') + ' m/s (was 85, x1.3 on a power tip)');
  // cards: every play throws cards. a spade throws 6, anything else (not an ace) flicks 2
  for (let tries = 0; tries < 8 && hand; tries++) {
    const i = 0, card = hand[0], suit = card[0], rank = Number(card.slice(1)), before = shots('card').length;
    send({ t: 's', q, p: [X, y, Z], v: [0, 0, 0], y: 0, x: 0, w: 'cards' });
    send({ t: 'fire', w: 'cards', o, d, i }); await sleep(450);
    const n = shots('card').length - before, want = suit === 'j' ? null : rank === 1 ? 0 : rank >= 11 ? (suit === 's' ? 24 : 2) : suit === 's' ? 6 : 2;
    if (want != null) ok(n === want, `cards: ${card} threw ${n} (want ${want})`);
    if (suit === 'd' || rank === 1 || suit === 'j') break; // a dash / teleport moved us: enough
  }
  const c = shots('card')[0]; ok(!c || Math.hypot(...c.v) > 80, 'cards: fly at ' + (c ? Math.hypot(...c.v).toFixed(0) : '?') + ' m/s (was 55)');
  // blood cross: 8 paid shots take 100 HP to 4, then it still fires (thin) and takes no more
  send({ t: 's', q, p: [X, y, Z], v: [0, 0, 0], y: 0, x: 0, w: 'bloodcross' });
  for (let i = 0; i < 9; i++) { send({ t: 's', q, p: [X, y, Z], v: [0, 0, 0], y: 0, x: 0, w: 'bloodcross' }); send({ t: 'fire', w: 'bloodcross', o, d }); await sleep(620); }
  await sleep(300);
  const paid = shots('bloodcross').length, hpLow = hp;
  ok(hpLow > 0 && hpLow < 12, `blood cross: bled down to ${hpLow} HP after ${paid} shots`);
  await sleep(600); const b0 = shots('bloodcross').length;
  send({ t: 'fire', w: 'bloodcross', o, d }); await sleep(400);
  ok(shots('bloodcross').length === b0 + 1, 'blood cross: out of blood, it still fires');
  ok(hp === hpLow, `blood cross: the thin shot was free (HP ${hp})`);
  send({ t: 'fire', w: 'bloodcross', o, d }); await sleep(300);
  ok(shots('bloodcross').length === b0 + 1, 'blood cross: thin shots are slower (a second one 0.7 s later is refused)');
  console.log(fails ? `${fails} FAILED` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
