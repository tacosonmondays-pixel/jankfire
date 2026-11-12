// island arena over plain ws: you start in your mech on your team's side, only mech kills score, an eject leaves you a
// pilot with the meter at 60% (and the call waits for 100%), the hero pick, the fence (out of the circle, the river,
// the sea: pushed back in, never dead), the win at the mech-kill target, garbage and exploits.
// starts its own server (the online room in this mode, JF_GAME=arena): node tests/arena_ws.cjs [port]
const WS = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const port = Number(process.argv[2]) || 3197;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
const MECH = 1 << 22;
let srvRef = null;
function client(name, extra = {}) {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, got: [], id: 0, q: 0, hp: 100, alive: true, name, team: 0 };
  ws.on('message', (d) => {
    const m = JSON.parse(d);
    if (m.t === 'welcome') { c.id = m.id; c.q = m.q; c.team = m.team; c.pos = m.pos; }
    if (m.t === 'spawn') { c.q = m.q; c.pos = m.p; }
    if (m.t === 'teams') for (const [id, t] of m.list) if (id === c.id) c.team = t;
    if (m.t === 'isle' && m.k === 'mm') c.mm = m;
    if (m.t === 'sn') { const r = m.p.find((x) => x[0] === c.id); if (r) { c.hp = r[10]; c.alive = !!r[11]; c.spos = [r[1], r[2], r[3]]; } c.sn = m; return; }
    c.got.push(m);
  });
  ws.on('error', () => {});
  c.send = (m) => { if (ws.readyState === 1) ws.send(typeof m === 'string' ? m : JSON.stringify(m)); };
  c.place = (p, o = {}) => c.send({ t: 's', q: c.q, p, v: o.v || [0, 0, 0], y: o.y ?? 0, x: o.x ?? 0, w: o.w || 'ar', f: o.f || 0 });
  c.take = (t, f) => { const i = c.got.findIndex((m) => m.t === t && (!f || f(m))); return i < 0 ? null : c.got.splice(i, 1)[0]; };
  c.all = (t, f) => c.got.filter((m) => m.t === t && (!f || f(m)));
  c.wait = async (t, f, ms = 4000) => { for (let i = 0; i < ms / 50; i++) { const m = c.take(t, f); if (m) return m; await sleep(50); } return null; };
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'join', name, mode: 'ffa', streaks: ['mechdrop', 'moonboots', 'scythe'], ...extra }); setTimeout(() => res(c), 700); }));
}
const hold = async (ms, who) => { for (let t = 0; t < ms; t += 60) { for (const [c, p, o] of who) c.place(typeof p === 'function' ? p(t) : p, o); await sleep(60); } };
const aim = (a, b) => { const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], l = Math.hypot(...d); return d.map((v) => v / l); };
const meter = (c) => c.mm || null;

(async () => {
  const srv = srvRef = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(port), JF_GAME: 'arena', JF_WIP_MAPS: '1', JF_ARENA_KILLS: '2', JF_MECH_HP: '0.1', JF_MECH_DROP: '1', JF_ISLE_METER: '25', JF_ARENA_LOG: '1' }, stdio: ['ignore', 'pipe', 'pipe'] });
  let srvErr = '', srvOut = ''; srv.stderr.on('data', (d) => { srvErr += d; }); srv.stdout.on('data', (d) => { srvOut += d; if (/Error|uncaught/i.test(String(d))) srvErr += d; });
  for (let i = 0; i < 60; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }
  const A = await client('alfa', { mf: 'nightshift' }), B = await client('bravo', { mf: 'paperplane' }), C = await client('charlie', { mf: 'paperplane' });
  const st = await A.wait('arena', (m) => m.k === 'st', 3000);
  ok(st && Array.isArray(st.area) && st.target === 2, `the match: ${st && JSON.stringify(st.area)} (x, z, r), first to ${st && st.target} mech kills`);
  const AR = st ? { c: [st.area[0], st.area[1]], r: st.area[2] } : { c: [-45, -16], r: 130 };
  const mate = [B, C].find((c) => c.team === A.team), foe = [B, C].find((c) => c.team !== A.team);
  ok(A.team && mate && foe, `teams: alfa ${A.team}, bravo ${B.team}, charlie ${C.team}`);
  // ---- 1. everyone starts in their mech, dropped onto their team's side (hangar = team 1, Dead Air = team 2)
  const ins = new Map();
  for (let i = 0; i < 60 && ins.size < 3; i++) { await sleep(100); for (const m of A.all('mech', (m) => m.k === 'in')) ins.set(m.id, m); }
  ok(ins.size === 3, `all three climbed into their mechs on their own (${ins.size}): ${[...ins.values()].map((m) => m.f).join(', ')}`);
  const side = (p) => Math.hypot(p[0] + 110, p[2] - 30) < Math.hypot(p[0] - 20, p[2] + 62) ? 1 : 2; // nearer Scrap Mart or Dead Air
  ok([A, B, C].every((c) => ins.get(c.id) && side(ins.get(c.id).p) === c.team), 'each one landed on its own team\'s pads: ' + [A, B, C].map((c) => ins.get(c.id) ? `${c.name} (team ${c.team}) by ${side(ins.get(c.id).p) === 1 ? 'Scrap Mart' : 'Dead Air'}` : '?').join(', '));
  ok(ins.get(A.id) && ins.get(A.id).f === 'nightshift' && ins.get(B.id) && ins.get(B.id).f === 'paperplane', 'the heroes from the loadout pick (alfa NIGHT SHIFT, bravo PAPER PLANE)');
  const pos = new Map([...ins].map(([id, m]) => [id, m.p]));
  const fly = (ms, extra = []) => hold(ms, [[A, pos.get(A.id), { f: MECH }], [B, pos.get(B.id), { f: MECH }], [C, pos.get(C.id), { f: MECH }], ...extra]);
  await fly(600);
  // ---- 2. a pilot kill scores nothing; a mech kill scores 1. the foe hops out and shoots alfa's mech (NIGHT SHIFT, 150)
  foe.got.length = 0;
  foe.send({ t: 'mech', k: 'out' });
  const fo = await foe.wait('mech', (m) => m.k === 'pos', 1000);
  ok(fo, 'the foe hops out of its mech');
  const fp = fo ? fo.p : pos.get(foe.id);
  const foot = (ms) => hold(ms, [[A, pos.get(A.id), { f: MECH }], [mate, pos.get(mate.id), { f: MECH }], [foe, fp, { w: 'ar' }]]);
  await foot(1200);
  A.got.length = 0; foe.got.length = 0;
  let down = null;
  for (let i = 0; i < 40 && !down; i++) { foe.send({ t: 'hit', w: 'ar', to: A.id, d: aim([fp[0], fp[1] + 1.6, fp[2]], [pos.get(A.id)[0], pos.get(A.id)[1] + 2, pos.get(A.id)[2]]), n: 1, h: 0 }); await foot(110); down = A.all('mech', (m) => m.k === 'down' && m.id === A.id)[0]; }
  ok(down && down.by === foe.id, `alfa's mech breaks: MECH DOWN by ${down ? (down.by === foe.id ? 'the foe' : down.by) : '?'}`);
  await sleep(300);
  const sc1 = A.all('arena', (m) => m.k === 'sc').pop();
  ok(sc1 && sc1.by === foe.id && sc1.sc[foe.team - 1] === 1 && sc1.sc[A.team - 1] === 0, `+1 mech kill for the foe's team (${sc1 && sc1.sc.join('-')})`);
  const mm1 = A.all('isle', (m) => m.k === 'mm' && m.out === 0)[0];
  ok(mm1 && mm1.v >= 60 && mm1.v < 70, `alfa ejects as the pilot, meter at ${mm1 && mm1.v}% (60 + a moment of refill)`);
  // the call below 100%: refused, the meter stays
  const ap = A.all('mech', (m) => m.k === 'pos').pop(), apos = ap ? [ap.p[0], ap.p[1], ap.p[2]] : pos.get(A.id);
  const AA = () => apos;
  const pilot = (ms, extra = []) => hold(ms, [[A, AA, {}], [mate, pos.get(mate.id), { f: MECH }], [foe, fp], ...extra]);
  await pilot(300);
  A.got.length = 0;
  A.send({ t: 'deploy', r: 'mechdrop', at: [apos[0] + 8, apos[1], apos[2]] });
  await pilot(300);
  const no1 = A.take('mech', (m) => m.k === 'no');
  ok(no1 && /meter at/.test(no1.why) && !A.all('mech', (m) => m.k === 'call').length, `call at ${meter(A) ? meter(A).v : '?'}%: refused (${no1 && no1.why})`);
  // pilot kills don't score: the foe shoots alfa (on foot now) dead
  A.got.length = 0;
  for (let i = 0; i < 20 && A.alive; i++) { foe.send({ t: 'hit', w: 'ar', to: A.id, d: aim([fp[0], fp[1] + 1.6, fp[2]], [apos[0], apos[1] + 1, apos[2]]), n: 1, h: 1 }); await pilot(110); }
  await sleep(300);
  const sc2 = A.all('arena', (m) => m.k === 'sc');
  ok(!A.alive && !sc2.length, `alfa killed on foot: no score for that (${sc2.length} score events)`);
  // no killstreaks here: the kill earned the foe nothing in the tray
  ok(!foe.all('streak').length, 'no killstreaks in the arena (the meter is the streak)');
  // ---- 3. the hero pick (for your next mech), garbage picks
  A.got.length = 0;
  for (const h of [5, 'x', '__proto__', null, { a: 1 }, 'constructor']) A.send({ t: 'hero', h });
  await sleep(300);
  ok(!A.all('isle', (m) => m.k === 'hero' && m.id === A.id).length, 'hero pick: garbage ignored');
  A.send({ t: 'hero', h: 'paperplane' }); await sleep(300); // (charlie, the only teammate, has it: a team of 2 gets one of each)
  const hn = A.take('isle', (m) => m.k === 'hero' && m.id === A.id);
  ok(hn && hn.no === 1 && hn.h === 'nightshift', `the teammate's hero: refused (${hn && hn.why})`);
  C.got.length = 0; C.send({ t: 'hero', h: 'nightshift' }); await sleep(300);
  ok(!C.all('isle', (m) => m.k === 'hero' && m.id === C.id && !m.no).length, "charlie can't take alfa's either");
  // respawn: a pilot on your team's pads with the meter at least 60
  const sp = await A.wait('spawn', null, 5000);
  await sleep(200);
  const mm2 = meter(A);
  ok(sp && side(sp.p) === A.team && mm2 && mm2.v >= 60, `respawned on foot on alfa's side, meter ${mm2 && Math.floor(mm2.v)}%`);
  const ap2 = sp ? sp.p : apos;
  apos[0] = ap2[0]; apos[1] = ap2[1]; apos[2] = ap2[2];
  // ---- 4. the fence: out of the circle, then the sea: pushed back in, never dead
  await pilot(2000);
  A.got.length = 0;
  const out = [AR.c[0] + (AR.r + 25), apos[1], AR.c[1]];
  for (let i = 0; i < 3; i++) { A.place(out); await sleep(130); }
  const back = await A.wait('mech', (m) => m.k === 'pos', 800), fn = await A.wait('arena', (m) => m.k === 'fence', 400);
  ok(back && Math.hypot(back.p[0] - AR.c[0], back.p[2] - AR.c[1]) < AR.r && fn, `a snapshot 25 m outside the fence: put back in (${back && back.p.map((x) => Math.round(x)).join(', ')}) + told`);
  await pilot(400);
  ok(A.spos && Math.hypot(A.spos[0] - AR.c[0], A.spos[2] - AR.c[1]) < AR.r && A.alive, 'the server has alfa back inside, alive');
  A.got.length = 0;
  A.place([300, -3, 300]); await sleep(250); // the open sea, under the waterline
  ok(A.take('mech', (m) => m.k === 'pos') && A.alive && !A.all('kill').length, 'a snapshot out in the sea, under the water: pushed back, no sea kill');
  await pilot(600);
  // ---- 5. the meter fills (JF_ISLE_METER), then the call: your new hero drops, you climb in
  for (let i = 0; i < 80 && !(meter(A) && meter(A).v >= 100); i++) await pilot(150);
  ok(meter(A) && meter(A).v >= 100, `meter full (${meter(A) && meter(A).v}%)`);
  A.got.length = 0;
  const at = [apos[0] + 6, apos[1], apos[2]];
  A.send({ t: 'deploy', r: 'mechdrop', at: [1e9, 0, 0] }); A.send({ t: 'deploy', r: 'mechdrop', at: 'x' }); await pilot(400);
  ok(!A.all('mech', (m) => m.k === 'call').length, 'garbage call spots: refused, no mech');
  let call = null;
  for (const dx of [6, -6, 0]) { if (call) break; A.send({ t: 'deploy', r: 'mechdrop', at: [apos[0] + dx, apos[1] + 0.2, apos[2] + (dx ? 0 : 6)] }); await pilot(450); call = A.take('mech', (m) => m.k === 'call'); }
  ok(call && call.f === 'nightshift', `the call at 100%: ${call ? call.f : 'refused: ' + JSON.stringify(A.all('mech', (m) => m.k === 'no').map((m) => m.why))}`);
  A.send({ t: 'deploy', r: 'mechdrop', at: at }); await pilot(300);
  ok(A.all('mech', (m) => m.k === 'call').length === 0, 'a second call while one is out: nothing');
  await pilot(1400);
  if (call) { apos[0] = call.p[0] + 1.5; apos[1] = call.p[1]; apos[2] = call.p[2]; }
  await pilot(300);
  A.send({ t: 'mech', k: 'in' });
  const in2 = await A.wait('mech', (m) => m.k === 'in' && m.id === A.id, 1500);
  ok(in2 && in2.f === 'nightshift', 'climbed into the new NIGHT SHIFT');
  // ---- 6. a teammate can't break your mech; spoofed score messages do nothing
  const ap3 = in2 ? in2.p : apos;
  const inm = (ms) => hold(ms, [[A, ap3, { f: MECH }], [mate, pos.get(mate.id), { f: MECH }], [foe, fp]]);
  mate.send({ t: 'mech', k: 'out' }); const mo = await mate.wait('mech', (m) => m.k === 'pos', 1200);
  const mp = mo ? mo.p : pos.get(mate.id);
  const mates = (ms) => hold(ms, [[A, ap3, { f: MECH }], [mate, mp], [foe, fp]]);
  await mates(1200);
  A.got.length = 0;
  for (let i = 0; i < 12; i++) { mate.send({ t: 'hit', w: 'ar', to: A.id, d: aim([mp[0], mp[1] + 1.6, mp[2]], [ap3[0], ap3[1] + 2, ap3[2]]), n: 1, h: 0 }); await mates(110); }
  for (const j of [{ t: 'arena', k: 'sc', sc: [99, 99] }, { t: 'arena' }, { t: 'hero', h: 'nightshift', x: 'y'.repeat(9000) }]) { A.send(j); mate.send(j); }
  await mates(400);
  ok(!A.all('mech', (m) => m.k === 'down').length && !A.all('arena', (m) => m.k === 'sc').length, 'a teammate shooting your mech + spoofed score messages: nothing');
  // ---- 7. the win: the second mech kill ends it
  A.got.length = 0; foe.got.length = 0;
  let over = null;
  for (let i = 0; i < 60 && !over; i++) { foe.send({ t: 'hit', w: 'ar', to: A.id, d: aim([fp[0], fp[1] + 1.6, fp[2]], [ap3[0], ap3[1] + 2, ap3[2]]), n: 1, h: 0 }); await mates(110); over = A.all('round', (m) => m.over)[0]; }
  ok(over && over.winTeam === foe.team && over.sc[foe.team - 1] === 2, `the second mech kill wins it: ${over ? (over.winTeam === 1 ? 'RED' : 'BLUE') + ' ' + over.sc.join('-') : 'no end'}`);
  // ---- 8. garbage, and the server still runs
  const junk = [{ t: 'deploy' }, { t: 'deploy', r: { x: 1 }, at: [NaN, 1, 2] }, { t: 'hero' }, { t: 'arena', k: '__proto__' }, '{"t":"hero","h":', { t: 'mech', k: 'in' }];
  for (const j of junk) for (const c of [A, B, C]) c.send(j);
  for (let i = 0; i < 100; i++) A.send({ t: 'hero', h: i % 2 ? 'paperplane' : 'nightshift' });
  await sleep(600);
  ok([A, B, C].every((c) => c.ws.readyState === 1), 'garbage: nobody disconnected');
  ok(!/uncaught|TypeError|ReferenceError|RangeError/.test(srvErr), 'no server errors' + (srvErr ? ': ' + srvErr.slice(0, 600) : ''));
  for (const l of srvOut.split('\n').filter((l) => l.startsWith('[arena]')).slice(0, 12)) console.log('  ' + l);
  console.log(fails ? `${fails} FAILED` : 'ALL OK'); srv.kill(); process.exit(fails ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
process.on('exit', () => { try { srvRef && srvRef.kill(); } catch {} });
