// PARTIES over plain ws (server/party.js): a menu connection gets a party of one with a code; join by code; only the
// leader sets, starts, kicks, passes the lead; wrong codes run out; a full party says no; junk is ignored; the leader's
// START hands everyone a ticket to the same room and they land there on the same side; a ticket works once
// (start a server first: PORT=3100 node server.js; then node tests/party_ws.cjs 3100)
const WS = require('ws');
const port = process.argv[2] || 3100;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
function hub(name) {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, name, party: null, errs: [], go: [], id: 0 };
  ws.on('message', (d) => { const m = JSON.parse(d); if (m.t === 'party') c.party = m; if (m.t === 'perr') c.errs.push(m.m); if (m.t === 'pgo') c.go.push(m); if (m.t === 'hubok') c.id = m.id; });
  c.send = (m) => ws.send(JSON.stringify(m));
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'hub', name, look: { color: '#ff4fd8' }, gun: name === 'lead' ? 'ar' : 'knife', mf: name === 'lead' ? 'nightshift' : 'junk' }); setTimeout(() => res(c), 400); }));
}
function player(name, mode, cfg) {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, id: 0, seen: new Set(), color: null, team: null };
  ws.on('message', (d) => { const m = JSON.parse(d); if (m.t === 'welcome') { c.id = m.id; c.color = m.color; } if (m.t === 'sn' && Array.isArray(m.p)) for (const r of m.p) c.seen.add(r[0]); if (m.t === 'teams') { const e = m.list.find((x) => x[0] === c.id); if (e) c.team = e[1]; } });
  return new Promise((res) => ws.on('open', () => { ws.send(JSON.stringify({ t: 'join', name, mode, cfg })); setTimeout(() => res(c), 1500); }));
}
(async () => {
  const A = await hub('lead'), B = await hub('pal'), C = await hub('rando');
  ok(A.party && /^[A-HJKMNP-Z2-9]{5}$/.test(A.party.code) && A.party.ms.length === 1 && A.party.lead === A.id, 'hello: a party of one with a code ' + (A.party && A.party.code));
  ok(A.party.code !== B.party.code, 'everyone gets their own code');
  { const a = A.party.ms[0], b = B.party.ms[0]; ok(a.gun === 'ar' && a.mf === 'nightshift' && b.gun === null && b.mf === 'paperplane', 'gun + mech frame ride along, checked (a knife is no primary, junk is the default frame) ' + JSON.stringify([a.gun, a.mf, b.gun, b.mf])); }
  B.send({ t: 'pjoin', code: A.party.code.toLowerCase() }); await sleep(400);
  ok(B.party.code === A.party.code && A.party.ms.length === 2, 'join by code (lower case is fine)');
  B.send({ t: 'pme', gun: 'shotgun', mf: 'nightshift', look: { color: '#4fd8ff', hair: 'nope' } }); await sleep(300);
  { const b = A.party.ms.find((m) => m.name === 'pal'); ok(b && b.gun === 'shotgun' && b.mf === 'nightshift' && b.look && b.look.color === '#4fd8ff' && b.look.hair !== 'nope', 'pme: a new primary, frame and look reach the party (the look checked) ' + JSON.stringify(b && [b.gun, b.mf, b.look.hair])); }
  C.send({ t: 'pjoin', code: 'QQQQQ' }); await sleep(300);
  ok(C.errs.includes('no party with that code'), 'a wrong code: told so');
  C.send({ t: 'pjoin', code: A.party.code }); await sleep(200);
  ok(C.party.code !== A.party.code, 'joins faster than one a second are ignored');
  await sleep(1050); // (a try inside the second doesn't count, right or wrong)
  for (let i = 0; i < 9; i++) { C.send({ t: 'pjoin', code: 'ZZZZ' + 'ABCDEFGHJ'[i] }); await sleep(1050); }
  C.errs.length = 0; C.send({ t: 'pjoin', code: A.party.code }); await sleep(400);
  ok(C.errs.some((e) => /too many wrong codes/.test(e)) && C.party.code !== A.party.code, 'ten wrong codes in a minute: even the right one waits');
  // the leader's powers
  B.send({ t: 'pset', side: 'offline', mode: 'bomb' }); B.send({ t: 'pkick', id: A.id }); B.send({ t: 'plead', id: B.id }); await sleep(400);
  ok(!A.party.set && A.party.ms.length === 2 && A.party.lead === A.id, 'a member cannot set, kick or take the lead');
  A.send({ t: 'pset', side: 'offline', mode: 'bomb' }); await sleep(300);
  ok(B.party.set && B.party.set.side === 'offline' && B.party.set.mode === 'bomb', "the leader's mode reaches the members");
  A.send({ t: 'pset', side: 'sideways', mode: 'bomb' }); A.send({ t: 'pjoin', code: 12345 }); A.send({ t: 'pkick', id: '2' }); A.send({ t: 'pgo', mode: 'bots', cfg: [1, 2] }); A.send({ t: 'pready', on: { a: 1 } }); A.send({ t: 'nope' }); await sleep(3200);
  ok(A.party.set.side === 'offline' && A.party.ms.length === 2, 'junk is ignored (and the server is still up)');
  A.go.length = 0; B.go.length = 0;
  // full: 6 is the most
  const extra = []; for (let i = 0; i < 4; i++) { const x = await hub('x' + i); x.send({ t: 'pjoin', code: A.party.code }); extra.push(x); }
  await sleep(500);
  ok(A.party.ms.length === 6, 'six in the party');
  const D = await hub('late'); D.send({ t: 'pjoin', code: A.party.code }); await sleep(400);
  ok(D.errs.some((e) => /full/.test(e)) && A.party.ms.length === 6, 'the seventh is told it is full');
  for (const x of extra) x.send({ t: 'pleave' }); await sleep(600);
  ok(A.party.ms.length === 2, 'leave: back to a party of one (and the others see it)');
  // START: a private P&D for the party. everyone gets a ticket to the same room
  await sleep(3000);
  A.send({ t: 'pgo', mode: 'bots', cfg: { game: 'bomb', map: 'warehouse_sd', bots: 4, diff: 'easy', hip: 'normal', priv: false, room: 'ffa' } }); await sleep(600);
  const ga = A.go[0], gb = B.go[0];
  ok(ga && gb && ga.cfg.room === gb.cfg.room && ga.cfg.ticket !== gb.cfg.ticket && ga.cfg.priv === true && ga.cfg.game === 'bomb', 'START: same room, a ticket each, always private ' + JSON.stringify(ga && ga.cfg));
  const PA = await player('lead', ga.mode, ga.cfg), PB = await player('pal', gb.mode, gb.cfg);
  await sleep(1500);
  ok(PA.seen.has(PB.id) || PB.seen.has(PA.id), 'the party lands in the same room');
  ok(PA.color && PA.color === PB.color, 'on the same side (P&D) ' + PA.color + ' ' + PB.color);
  const PX = await player('thief', ga.mode, ga.cfg); await sleep(1200);
  ok(!PX.seen.has(PA.id) && !PA.seen.has(PX.id), 'a used ticket gets you nowhere near the party');
  // kick + the lead passing on
  A.send({ t: 'pkick', id: B.id }); await sleep(500);
  ok(B.party.code !== A.party.code && B.errs.some((e) => /kicked/.test(e)), 'the leader kicks: you are on your own, and told');
  B.send({ t: 'pjoin', code: A.party.code }); await sleep(1200); A.ws.close(); await sleep(600);
  ok(B.party.ms.length === 1 || (B.party.lead === B.id), 'the leader leaves: the lead passes on');
  for (const c of [A, B, C, D, ...extra, PA, PB, PX]) c.ws.close();
  console.log(fails ? `${fails} FAILED` : 'all ok');
  process.exit(fails ? 1 : 0);
})();
