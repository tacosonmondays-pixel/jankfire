// VENDING MACHINE (battle island support) over plain ws, in Team Deathmatch so it has allies: the coin turret (aim
// cone, rate), DISPENSE (charges, where the can lands, allies only, full HP walks past, healing charges the ult),
// OUT OF ORDER (it eats enemy guns, mech guns and projectiles, allies shoot through, a shot past its edge lands, it
// breaks), RESTOCK (a full ult, allies in range only), hop out / death / disconnect cleanup, and on two more servers
// the dice: JAMMED (the kick: garbage, enemies, far away, not jammed) and STUCK (x2, the cola cap). Each exploit check
// fails on a naive server (no charges, no cone, no side check, a straight line to the middle, no range).
// starts its own servers: node tests/mech_vending_ws.cjs [port]
const WS = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const port0 = Number(process.argv[2]) || 3641;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
const MF = { MECH: 1 << 22, A: 1 << 23, B: 1 << 30, C: 1 << 31 };
const S = Number(process.env.JF_MECH_SCALE) || 1.35; // (MECH.scale: the machine's spots, its wall, its reaches grow with it)
const Y = 0.03, X0 = 42, Z0 = 12; // warehouse: the flat open yard round [42, 0, 12]
const sh = (a, k) => (Array.isArray(a) && a.length === 3 && a.every(Number.isFinite) ? [a[0] + X0 * k, a[1], a[2] + Z0 * k] : a);
const TEAM = new Map();
let srvRef = null, srvErr = '';

function client(port, name, extra = {}) {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, got: [], id: 0, q: 0, hp: 100, alive: true, name };
  ws.on('message', (d) => {
    const m = JSON.parse(d);
    if ((m.t === 'mech' || m.t === 'welcome' || m.t === 'spawn') && m.p) m.p = sh(m.p, -1);
    if (m.t === 'mech' && m.b) m.b = sh(m.b, -1);
    if (m.t === 'welcome') { c.id = m.id; c.q = m.q; for (const p of m.players || []) TEAM.set(p.id, p.team); }
    if (m.t === 'pj') { TEAM.set(m.id, m.team); if (process.env.DBG && name === 'vendor') console.log('   pj', m.id, m.name, m.bot, m.team); }
    if (m.t === 'teams') for (const [id, tm] of m.list) TEAM.set(id, tm);
    if (m.t === 'spawn') { c.q = m.q; if (process.env.DBG) console.log('   spawn', name, m.q); }
    if (process.env.DBG && (m.t === 'kill' || m.t === 'die') && name === 'vendor') console.log('   kill', JSON.stringify(m).slice(0, 160));
    if (m.t === 'sn') { const r = m.p.find((x) => x[0] === c.id); if (r) { c.hp = r[10]; c.alive = !!r[11]; c.f = r[13]; } return; }
    if (process.env.DBG && m.t === 'mech' && name === 'vendor' && !/^(en|list|vmlist|vmcoin)$/.test(m.k)) console.log('   .', JSON.stringify(m).slice(0, 200));
    c.got.push(m);
  });
  ws.on('error', () => {});
  c.send = (m) => { if (typeof m === 'object' && (m.t === 's' || m.t === 'mech') && m.p) m = { ...m, p: sh(m.p, 1) }; if (typeof m === 'object' && m.at) m = { ...m, at: sh(m.at, 1) }; if (typeof m === 'object' && m.o) m = { ...m, o: sh(m.o, 1) }; if (ws.readyState === 1) ws.send(typeof m === 'string' ? m : JSON.stringify(m)); };
  c.place = (p, o = {}) => c.send({ t: 's', q: c.q, p, v: o.v || [0, 0, 0], y: o.y ?? 0, x: o.x ?? 0, w: o.w || 'ar', f: o.f || 0 });
  c.take = (t, f) => { const i = c.got.findIndex((m) => m.t === t && (!f || f(m))); return i < 0 ? null : c.got.splice(i, 1)[0]; };
  c.all = (t, f) => c.got.filter((m) => m.t === t && (!f || f(m)));
  c.wait = async (t, f, ms = 4000) => { for (let i = 0; i < ms / 50; i++) { const m = c.take(t, f); if (m) return m; await sleep(50); } return null; };
  c.team = () => TEAM.get(c.id);
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'join', name, mode: 'ffa', streaks: ['mechdrop', 'moonboots', 'scythe'], ...extra }); setTimeout(() => res(c), 600); }));
}
const aim = (a, b) => { const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], h = Math.hypot(d[0], d[2]), l = Math.hypot(...d); return { y: Math.atan2(-d[0], -d[2]), x: Math.atan2(d[1], h), d: d.map((v) => v / l) }; };
const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const eyeP = (p) => [p[0], p[1] + 1.6, p[2]], mid = (p) => [p[0], p[1] + 0.9, p[2]];

const up = (port) => new Promise((res) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(true); }); w.on('error', () => res(false)); });
process.on('exit', () => { if (srvRef) srvRef.kill(); });
async function boot(port, env) {
  srvErr = '';
  if (await up(port)) { console.log(`port ${port} is taken (someone else's server): pick another`); process.exit(2); }
  const srv = srvRef = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(port), JF_MECH_SCALE: String(S), JF_GAME: 'tdm', JF_TRAIN_STREAKS: '1', JF_MECH_DROP: '0.6', ...env }, stdio: ['ignore', 'pipe', 'pipe'] });
  srv.stderr.on('data', (d) => { srvErr += d; }); srv.stdout.on('data', (d) => { if (process.env.VMDBG) process.stdout.write('SRV ' + d); if (/Error|uncaught/i.test(String(d))) srvErr += d; });
  for (let i = 0; i < 60; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }
  return srv;
}
// a squad: the pilot first, then the rest; who's on whose side comes from the server's team list
async function squad(port, names) {
  const A = await client(port, names[0], { mf: 'vending' });
  A.send({ t: 'cfg', map: 'warehouse' }); await sleep(900);
  const rest = [];
  for (const n of names.slice(1)) rest.push(await client(port, n));
  await sleep(1200);
  const all = [A, ...rest], mine = all.filter((c) => c !== A && c.team() === A.team()), them = all.filter((c) => c.team() && c.team() !== A.team());
  return { A, all, mine, them };
}
// hold everyone's snapshots for ms: who = [[client, pos | fn(t), opts | fn(t)]]; the rest stand still where they are
const holdF = (all) => async (ms, who) => {
  const set = new Map(who.map((w) => [w[0], w]));
  for (let t = 0; t < ms; t += 60) {
    for (const c of all) { const w = set.get(c); if (w) c.place(typeof w[1] === 'function' ? w[1](t) : w[1], typeof w[2] === 'function' ? w[2](t) : w[2]); else if (c.at) c.place(c.at, c.o || {}); }
    await sleep(60);
  }
};
// call the mech in at `at` (pilot standing at `from`), climb in. returns the mech's spot
async function mechIn(c, hold, from, at, f = 'vending') {
  const l = aim(eyeP(from), at);
  c.at = from; c.o = { y: l.y, x: l.x };
  await hold(300, []);
  c.send({ t: 'deploy', r: 'mechdrop', at, mf: f });
  const call = await c.wait('mech', (m) => m.k === 'call' && m.o === c.id, 1500);
  await hold(1200, []);
  const land = c.take('mech', (m) => m.k === 'land' && m.o === c.id);
  const mp = land ? land.p : at;
  c.at = [mp[0] + 1.5, Y, mp[2] + 1]; await hold(300, []);
  c.got.length = 0; c.send({ t: 'mech', k: 'in' });
  const ein = await c.wait('mech', (m) => m.k === 'in' && m.id === c.id, 1200);
  c.at = mp.slice(); c.o = { f: MF.MECH, y: 0 };
  await hold(300, []);
  return { call, ein, mp };
}
const lastEn = (c) => c.all('mech', (m) => m.k === 'en').pop();

(async () => {
  // ================================================================ 1. the main server (no dice)
  const PH = process.env.PHASE ? process.env.PHASE.split(',').map(Number) : [1, 2, 3];
  let srv = null;
  if (PH.includes(1)) {
  srv = await boot(port0, { JF_MECH_HP: '0.5', JF_MECH_ULT: '5', JF_VM_JAM: '0', JF_VM_STUCK: '0', JF_VM_SLOW: '1.4' }); // (SLOW: the wall stands 14 s, room for every shot at it)
  {
    const { A, all, mine, them } = await squad(port0, ['vendor', 'b', 'c', 'd', 'e']);
    ok(mine.length === 2 && them.length === 2, `teams: the vending machine has ${mine.length} allies, ${them.length} enemies`);
    const [C, E] = mine, [B, D] = them;
    const hold = holdF(all);
    const P0 = [0, Y, 6];
    C.at = [6, Y, 10]; E.at = [-20, Y, 16]; D.at = [20, Y, 16]; B.at = [3, Y, -12];
    // B (enemy) calls a PAPER PLANE in early: its cannons are the mech hitscan the wall has to stop
    const bm = await mechIn(B, hold, [3, Y, -12], [3, Y, -16], 'paperplane');
    ok(bm.ein && bm.ein.f === 'paperplane', 'the enemy is in a PAPER PLANE');
    const { ein, mp } = await mechIn(A, hold, P0, [0, Y, -2]);
    ok(ein && ein.f === 'vending' && ein.max === 550, 'climbs in: VENDING MACHINE, armour ' + (ein && ein.max) + ' (1100 x JF_MECH_HP 0.5)');
    const P = mp.slice();
    A.at = P; A.o = { f: MF.MECH, y: 0, x: 0 };
    await hold(600, []);
    const en0 = lastEn(A);
    ok(en0 && en0.ch === 3 && Number.isFinite(en0.u), `the energy message carries the cans (${en0 && en0.ch}) and the ult (${en0 && en0.u})`);
    A.got.length = 0; A.send({ t: 'mech', k: 'stock' }); await hold(200, []);
    ok((A.take('mech', (m) => m.k === 'no') || {}).why === 'ultimate not ready', 'RESTOCK with no ult: refused');

    // ---- 2. coin turret
    const slot = add(P, [0, 4.0 * S, -0.9 * S]);
    D.at = add(P, [16, 0, 0]); await hold(400, []);
    D.got.length = 0;
    A.send({ t: 'mech', k: 'coin', d: aim(slot, mid(D.at)).d }); await hold(250, []);
    ok(!D.all('dmg', (m) => m.to === D.id && m.w === 'vmcoin').length, 'a coin at someone 90° off where it looks: refused (aim cone)');
    D.at = add(P, [0, 0, -15]); await hold(600, []);
    D.got.length = 0;
    const cd = aim(slot, mid(D.at)).d;
    for (let i = 0; i < 8; i++) A.send({ t: 'mech', k: 'coin', d: cd });
    await hold(300, []);
    ok(D.all('dmg', (m) => m.to === D.id && m.w === 'vmcoin').length === 1, '8 coins in one go: 1 lands (the rate)');
    D.got.length = 0; B.got.length = 0;
    for (let i = 0; i < 5; i++) { A.send({ t: 'mech', k: 'coin', d: cd }); await hold(120, []); }
    await hold(200, []);
    const coins = D.all('dmg', (m) => m.to === D.id && m.w === 'vmcoin');
    ok(coins.length === 5 && coins.every((m) => m.a === 9), `5 coins at 10 a second: ${coins.length} land, ${coins.map((m) => m.a).join(',')} each`);
    ok(B.all('mech', (m) => m.k === 'vmcoin' && m.id === A.id).length >= 5, 'everyone else sees the coins fly');

    // ---- 3. dispense: 3 charges, where it lands, who can drink it
    A.got.length = 0;
    for (let i = 0; i < 4; i++) { A.send({ t: 'mech', k: 'disp' }); await hold(420, []); }
    const colas = A.all('mech', (m) => m.k === 'vmcola');
    ok(colas.length === 3, `4 dispenses on 3 charges: ${colas.length} cans`);
    ok((A.all('mech', (m) => m.k === 'no').pop() || {}).why === 'sold out', 'the 4th: SOLD OUT');
    const cp = colas[0] && colas[0].p;
    ok(cp && Math.abs(cp[0] - P[0]) < 0.3 && Math.abs(cp[2] - (P[2] - 2.4 * S)) < 0.3, `no aim point: it lands ${(2.4 * S).toFixed(1)} m in front · ` + (cp && cp.map((x) => x.toFixed(1))));
    // D (enemy, hurt) stands on them: nothing
    D.got.length = 0; A.got.length = 0;
    D.at = cp; await hold(900, []);
    ok(!A.all('mech', (m) => m.k === 'vmdrink').length, `an enemy (hp ${Math.round(D.hp)}) on the cans: can't drink them`);
    D.at = add(P, [-3, 0, -16]); await hold(200, []);
    // C (ally) at full HP walks over them: nothing
    C.at = cp; await hold(700, []);
    ok(!A.all('mech', (m) => m.k === 'vmdrink').length, 'an ally at full HP walks past them');
    // D shoots C three times, C walks over a can: +40 (up to 100), a sugar rush, the ult charges
    C.at = add(P, [6, 0, -2]); await hold(1600, []);
    const dc = aim(eyeP(D.at), mid(C.at)).d;
    C.got.length = 0;
    for (let i = 0; i < 3; i++) { D.send({ t: 'hit', w: 'ar', to: C.id, d: dc, n: 1, h: 0 }); await hold(150, []); }
    const hurt = C.all('dmg', (m) => m.to === C.id).reduce((s, m) => s + m.a, 0);
    ok(hurt >= 30, 'C got shot for ' + hurt);
    await hold(300, []);
    const u0 = (lastEn(A) || {}).u || 0;
    A.got.length = 0;
    C.at = cp; await hold(500, []);
    const dr = A.all('mech', (m) => m.k === 'vmdrink' && m.to === C.id);
    ok(dr.length === 1 && dr[0].a === Math.min(40, hurt) && dr[0].ms === 3000, `the ally drinks one: +${dr[0] && dr[0].a} HP and a ${dr[0] && dr[0].ms} ms sugar rush`);
    await hold(500, []);
    const u1 = (lastEn(A) || {}).u || 0;
    ok(u1 - u0 >= 14, `the heal charged the ult: ${u0} -> ${u1}`);
    C.at = add(P, [6, 0, 4]); await hold(200, []);

    // ---- 4. OUT OF ORDER
    A.got.length = 0;
    A.send({ t: 'mech', k: 'wall' }); await hold(200, []);
    const wl = A.take('mech', (m) => m.k === 'vmwall');
    ok(wl && Math.abs(wl.p[2] - (P[2] - 3.5 * S)) < 0.3 && Math.abs(wl.p[0] - P[0]) < 0.3 && wl.hp === 600, `OUT OF ORDER: a 600 HP wall ${(3.5 * S).toFixed(1)} m in front · ` + (wl && wl.p.map((x) => x.toFixed(1))));
    A.send({ t: 'mech', k: 'wall' }); await hold(200, []);
    ok(!A.all('mech', (m) => m.k === 'vmwall').length, 'again at once: cooldown, one wall');
    // C (ally) behind the wall, D (enemy) out front shooting at it
    C.at = add(P, [1.8, 0, -2]); D.at = add(P, [0, 0, -30]);
    await hold(500, []);
    C.got.length = 0; A.got.length = 0;
    D.send({ t: 'hit', w: 'ar', to: C.id, d: aim(eyeP(D.at), mid(C.at)).d, n: 1, h: 0 }); await hold(250, []);
    ok(!C.all('dmg', (m) => m.to === C.id).length, 'an enemy shoots an ally through the wall: blocked');
    const wh = A.all('mech', (m) => m.k === 'vmwhit');
    ok(wh.length === 1 && wh[0].hp === 589, 'the wall takes it instead: hp ' + (wh[0] && wh[0].hp));
    D.got.length = 0;
    C.send({ t: 'hit', w: 'ar', to: D.id, d: aim(eyeP(C.at), mid(D.at)).d, n: 1, h: 0 }); await hold(250, []);
    ok(D.all('dmg', (m) => m.to === D.id && m.w === 'ar').length === 1, 'the ally shoots back through it: lands (allies shoot through)');
    // the edge: C half behind it (the panel ends at 4 x S). at the middle: blocked; at the bit that sticks out: lands
    C.at = add(P, [4 * S + 0.4, 0, -1]); await hold(700, []);
    C.got.length = 0;
    D.send({ t: 'hit', w: 'ar', to: C.id, d: aim(eyeP(D.at), mid(C.at)).d, n: 1, h: 0 }); await hold(250, []);
    ok(!C.all('dmg', (m) => m.to === C.id).length, 'half behind the edge, shot at the middle (through the panel): blocked');
    C.got.length = 0;
    D.send({ t: 'hit', w: 'ar', to: C.id, d: aim(eyeP(D.at), add(C.at, [0.45, 1.2, 0])).d, n: 1, h: 0 }); await hold(250, []);
    ok(C.all('dmg', (m) => m.to === C.id).length === 1, 'shot at the bit sticking out past the edge: lands');
    // a projectile: D lobs a banana at C through it
    C.at = add(P, [1.8, 0, -2]); await hold(400, []);
    C.got.length = 0; A.got.length = 0;
    const bd = aim(eyeP(D.at), add(mid(C.at), [0, 4, 0])).d;
    D.send({ t: 'fire', w: 'banana', d: bd, o: eyeP(D.at) }); await hold(900, []);
    ok(!C.all('dmg', (m) => m.to === C.id && m.w === 'banana').length && A.all('mech', (m) => m.k === 'vmwhit').length >= 1, 'a banana through it: stopped, the wall takes it');
    // (review #471) the water pistol: 3 squirts at C through the wall: no damage and NO SOAK either (it used to soak through)
    C.got.length = 0;
    for (let i = 0; i < 3; i++) { D.send({ t: 'hit', w: 'water', to: C.id, d: aim(eyeP(D.at), mid(C.at)).d, n: 1, h: 0 }); await hold(160, []); }
    ok(!C.all('dmg', (m) => m.to === C.id).length && !C.all('soak', (m) => m.id === C.id).length, `the water pistol through the wall: no damage, no soak (${C.all('soak', (m) => m.id === C.id).length} soaks)`);
    // (review #471) a chicken rocket at the sign: it goes off on D's side and the blast stops at the sign (C is 3 m behind it, in its 7.5 m blast)
    C.got.length = 0; A.got.length = 0;
    D.send({ t: 'fire', w: 'chicken', d: aim(eyeP(D.at), add(mid(C.at), [0, 2.5, 0])).d, o: eyeP(D.at) }); await hold(1600, []); // (aimed high: it drops on the way)
    ok(A.all('mech', (m) => m.k === 'vmwhit').length >= 1 && !C.all('dmg', (m) => m.to === C.id && m.w === 'chicken').length, `a chicken rocket at the sign: it goes off on the face, the blast doesn't come through (${C.all('dmg', (m) => m.to === C.id && m.w === 'chicken').map((m) => m.a).join(',') || 'nothing'})`);
    // a mech's cannons: B's PAPER PLANE hammers C through it until it breaks; then they land
    const bAt = B.at.slice(), be = add(bAt, [0, 4.4 * S, 0]), ba = aim(be, mid(C.at));
    B.o = { f: MF.MECH, y: ba.y, x: ba.x };
    await hold(400, []);
    C.got.length = 0; A.got.length = 0;
    let broke = null;
    const dcc = aim(eyeP(D.at), mid(C.at)).d; // (D's rifle joins in: it's only up for 10 s)
    for (let i = 0; i < 80 && !broke; i++) { B.send({ t: 'mech', k: 'gun', d: ba.d }); D.send({ t: 'hit', w: 'ar', to: C.id, d: dcc, n: 1, h: 0 }); await hold(130, []); broke = A.all('mech', (m) => m.k === 'vmwallx').pop(); }
    const bx = C.got.findIndex((m) => m.t === 'mech' && m.k === 'vmwallx'), d1 = C.got.findIndex((m) => m.t === 'dmg' && m.to === C.id); // (C hears both in the server's order)
    ok(bx >= 0 && (d1 < 0 || d1 > bx) && A.all('mech', (m) => m.k === 'vmwhit').length > 5, 'the PAPER PLANE\'s cannons (and a rifle) into the wall: nothing gets through to C');
    ok(broke && broke.why === 'break', 'it breaks · ' + (broke && broke.why));
    for (let i = 0; i < 4; i++) { B.send({ t: 'mech', k: 'gun', d: ba.d }); await hold(130, []); }
    ok(C.all('dmg', (m) => m.to === C.id && m.w === 'mechgun').length >= 1, 'broken: the cannons hit C again');
    // (review #471) coins hit an empty parked enemy mech, like the PAPER PLANE's cannons do (they used to pass through it)
    { const dm = add(P, [9, 0, -14]); D.at = add(P, [9, 0, -4]); const dl = aim(eyeP(D.at), dm); D.o = { y: dl.y, x: dl.x }; await hold(400, []);
      D.got.length = 0; D.send({ t: 'deploy', r: 'mechdrop', at: [dm[0], Y, dm[2]], mf: 'paperplane' });
      const call = await D.wait('mech', (m) => m.k === 'call', 1500);
      D.at = add(P, [20, 0, 10]); await hold(3400, []);
      const hpOf = () => { const l = A.all('mech', (m) => m.k === 'list').pop(), e = l && call && l.m.find((x) => x[0] === call.id); return e ? e[9] : null; };
      A.got.length = 0; await hold(1200, []);
      const h0 = hpOf(), slot = [P[0], P[1] + 4.0 * S, P[2]], tgt = [dm[0], Y + 2.5 * S, dm[2]], ca = aim(slot, tgt);
      A.o = { y: ca.y, x: ca.x }; await hold(300, []);
      for (let i = 0; i < 10; i++) { A.send({ t: 'mech', k: 'coin', d: ca.d }); await hold(130, []); }
      await hold(1200, []);
      const h1 = hpOf();
      ok(call && h0 != null && h1 != null && h0 - h1 >= 45, `coins at an empty parked enemy mech: they hit it (armour ${h0} -> ${h1})`);
      A.o = {}; }
    B.at = add(P, [3, 0, -40]); C.at = add(P, [6, 0, 4]); D.at = add(P, [20, 0, 10]);
    await hold(400, []);

    // ---- 5. a lobbed can: onto the floor where you point, in reach
    for (let i = 0; i < 40; i++) { const e = lastEn(A); if (e && e.ch >= 1) break; await hold(250, []); }
    A.got.length = 0;
    const tossTo = add(P, [3, 0, -3.5]);
    A.send({ t: 'mech', k: 'disp', p: tossTo }); await hold(300, []);
    const tc = A.take('mech', (m) => m.k === 'vmcola');
    ok(tc && Math.hypot(tc.p[0] - tossTo[0], tc.p[2] - tossTo[2]) < 0.3, 'lobbed at a spot 4.6 m off: lands there · ' + (tc && tc.p.map((x) => x.toFixed(1))));

    // ---- 6. RESTOCK: allies in 15 m (yourself too), nobody else
    C.at = add(P, [5, 0, 1]); E.at = add(P, [15 * S + 3, 0, 0]); D.at = add(P, [0, 0, -6]);
    for (let i = 0; i < 160; i++) { const e = lastEn(A); if (e && e.u >= 100) break; await hold(250, []); }
    const eU = lastEn(A);
    ok(eU && eU.u >= 100, 'the ult is charged · ' + (eU && eU.u));
    ok(eU && eU.ch < 3, 'cans used before: ' + (eU && eU.ch));
    A.got.length = 0; C.got.length = 0; D.got.length = 0; E.got.length = 0;
    A.send({ t: 'mech', k: 'stock' }); await hold(400, []);
    const st = A.take('mech', (m) => m.k === 'vmstock');
    const ids = st ? st.l.map((x) => x[0]) : [];
    ok(st && ids.includes(A.id) && ids.includes(C.id), 'RESTOCK reaches the vending machine and the ally 5 m off');
    ok(st && !ids.includes(E.id), `not the ally ${Math.round(15 * S + 3)} m away (out of range: ${15 * S} m)`);
    ok(st && !ids.includes(D.id) && !ids.includes(B.id), 'not the enemies (one 6 m away)');
    const ch = C.all('heal', (m) => m.id === C.id).pop();
    ok(ch && ch.hp === 150, 'TDM has no armour: the ally gets an overheal to ' + (ch && ch.hp));
    ok(!D.all('heal', (m) => m.id === D.id).length, 'the enemy gets nothing');
    await hold(300, []);
    const eR = lastEn(A);
    ok(eR && eR.ch === 3 && !(eR.cd && eR.cd.wall) && eR.u < 10, `its own cans refilled (${eR && eR.ch}), the wall's cooldown cleared, the ult spent (${eR && eR.u})`);
    A.send({ t: 'mech', k: 'stock' }); await hold(200, []);
    ok((A.take('mech', (m) => m.k === 'no') || {}).why === 'ultimate not ready', 'RESTOCK again at once: not charged');

    // ---- 7. hop out: the wall stays its 10 s; back in; then a disconnect takes the cans and the wall with it
    A.send({ t: 'mech', k: 'wall' }); await hold(300, []);
    ok(A.all('mech', (m) => m.k === 'vmwall').length === 1, 'a wall again (the restock cleared its cooldown)');
    A.send({ t: 'mech', k: 'disp' }); await hold(300, []);
    A.got.length = 0; C.got.length = 0;
    A.send({ t: 'mech', k: 'out' }); await hold(200, []);
    const out = await A.wait('mech', (m) => m.k === 'out' && m.why === 'hop', 800);
    ok(out, 'hops out');
    A.at = add(P, [2.2, 0, 0]); A.o = {};
    await hold(1300, []);
    ok(!C.all('mech', (m) => m.k === 'vmwallx').length, 'hopped out: the wall stays up');
    A.at = P; A.o = { f: MF.MECH, y: 0 };
    A.send({ t: 'mech', k: 'in' }); await hold(500, []);
    ok(lastEn(A) && lastEn(A).ch === 2, 'back in: the cans waited with the mech · ' + (lastEn(A) || {}).ch);
    // garbage + a flood
    for (const m of [{ k: 'coin', d: [1e12, 0, 0] }, { k: 'coin', d: 'x' }, { k: 'disp', p: [NaN, 0, 0] }, { k: 'disp', p: [1e9, 1e9, 1e9] }, { k: 'disp', p: 'here' }, { k: 'wall', x: [[[[1]]]] }, { k: 'stock', to: {} }, { k: 'kick', to: A.id }, { k: 'x'.repeat(40) }, { k: null }]) A.send({ t: 'mech', ...m });
    for (let i = 0; i < 200; i++) A.send({ t: 'mech', k: 'disp' });
    await hold(400, []);
    ok(srv.exitCode === null, 'garbage + a flood: the server is fine');
    C.got.length = 0;
    A.ws.close(); await sleep(900);
    ok(C.all('mech', (m) => m.k === 'vmwallx').length === 1 && C.all('mech', (m) => m.k === 'vmcolax').length >= 1, 'the pilot disconnects: its wall and cans go with it');
    ok(!/TypeError|ReferenceError|RangeError|uncaught/i.test(srvErr), 'no server errors' + (srvErr ? ': ' + srvErr.slice(0, 400) : ''));
    for (const c of all) c.ws.close();
  }
  srv.kill(); await sleep(500);
  }

  // ================================================================ 2. every use jams: the kick
  if (PH.includes(2)) {
  srv = await boot(port0 + 1, { JF_MECH_HP: '0.5', JF_VM_JAM: '1', JF_VM_STUCK: '0' });
  {
    const { A, all, mine, them } = await squad(port0 + 1, ['vendor', 'b', 'c']);
    const [C] = mine, [B] = them;
    const hold = holdF(all);
    C.at = [6, Y, 10]; B.at = [-6, Y, 10];
    const { mp } = await mechIn(A, hold, [0, Y, 6], [0, Y, -2]);
    const P = mp.slice();
    A.at = P; A.o = { f: MF.MECH, y: 0 };
    C.at = add(P, [2.5, 0, 1]); await hold(500, []);
    A.got.length = 0;
    C.send({ t: 'mech', k: 'kick', to: A.id }); await hold(350, []);
    ok(!A.all('mech', (m) => m.k === 'vmkick').length, 'kicking a machine that isn\'t jammed: nothing');
    A.send({ t: 'mech', k: 'disp' }); await hold(300, []);
    const jm = A.take('mech', (m) => m.k === 'vmjam');
    ok(jm && jm.ms === 4000 && !A.all('mech', (m) => m.k === 'vmcola').length, 'dispense JAMMED: nothing comes out, locked 4 s');
    await hold(300, []);
    ok((lastEn(A) || {}).ch === 3 && (lastEn(A) || {}).jam > 2000, 'nothing spent, the jam shows on the meter · ' + JSON.stringify({ ch: (lastEn(A) || {}).ch, jam: (lastEn(A) || {}).jam }));
    A.got.length = 0;
    A.send({ t: 'mech', k: 'wall' }); await hold(250, []);
    ok(/jammed/.test((A.take('mech', (m) => m.k === 'no') || {}).why) && !A.all('mech', (m) => m.k === 'vmwall').length, 'jammed: OUT OF ORDER is locked too');
    // garbage kicks, enemies, far away, the pilot itself
    for (const to of ['x', -1, 1.5, 99999, null, { id: A.id }, [A.id], C.id]) { C.send({ t: 'mech', k: 'kick', to }); await hold(280, []); }
    ok(!A.all('mech', (m) => m.k === 'vmkick').length, 'garbage kick targets: nothing');
    for (let i = 0; i < 30; i++) { const e = lastEn(A); if (e && !e.jam) break; await hold(200, []); } // (4 s later it unjams by itself: jam it again)
    A.got.length = 0;
    A.send({ t: 'mech', k: 'disp' }); await hold(250, []);
    ok(A.all('mech', (m) => m.k === 'vmjam').length === 1, 'the lock ran out by itself; jammed again');
    B.at = add(P, [-2.5, 0, 1]); await hold(400, []);
    B.send({ t: 'mech', k: 'kick', to: A.id }); await hold(350, []);
    ok(!A.all('mech', (m) => m.k === 'vmkick').length, 'an enemy kicks it: nothing');
    C.at = add(P, [12, 0, 0]); await hold(400, []);
    C.send({ t: 'mech', k: 'kick', to: A.id }); await hold(350, []);
    ok(!A.all('mech', (m) => m.k === 'vmkick').length, 'an ally kicks it from 12 m: nothing');
    A.send({ t: 'mech', k: 'kick', to: A.id }); await hold(350, []);
    ok(!A.all('mech', (m) => m.k === 'vmkick').length, 'it kicks itself: nothing');
    C.at = add(P, [2.6, 0, 0.5]); await hold(400, []);
    A.got.length = 0;
    C.send({ t: 'mech', k: 'kick', to: A.id }); await hold(350, []);
    const kk = A.take('mech', (m) => m.k === 'vmkick');
    const fc = A.take('mech', (m) => m.k === 'vmcola');
    ok(kk && kk.by === C.id && fc && fc.why === 'kick', 'the ally kicks it next to it: UNSTUCK, a free can pops out');
    await hold(300, []);
    ok((lastEn(A) || {}).ch === 3 && !(lastEn(A) || {}).jam, 'the free can cost nothing; unjammed');
    C.send({ t: 'mech', k: 'kick', to: A.id }); await hold(350, []);
    ok(!A.all('mech', (m) => m.k === 'vmkick').length && !A.all('mech', (m) => m.k === 'vmcola').length, 'kicking it again: nothing more');
    ok(!/TypeError|ReferenceError|RangeError|uncaught/i.test(srvErr), 'no server errors' + (srvErr ? ': ' + srvErr.slice(0, 400) : ''));
    for (const c of all) c.ws.close();
  }
  srv.kill(); await sleep(500);
  }

  // ================================================================ 3. every use comes out twice: STUCK, the can cap, blowing up
  if (PH.includes(3)) {
  srv = await boot(port0 + 2, { JF_MECH_HP: '0.05', JF_VM_JAM: '0', JF_VM_STUCK: '1' });
  {
    const { A, all, mine, them } = await squad(port0 + 2, ['vendor', 'b', 'c']);
    const [C] = mine, [B] = them;
    const hold = holdF(all);
    C.at = [6, Y, 10]; B.at = [-6, Y, 14];
    const { mp } = await mechIn(A, hold, [0, Y, 6], [0, Y, -2]);
    const P = mp.slice();
    A.at = P; A.o = { f: MF.MECH, y: 0 };
    await hold(400, []);
    A.got.length = 0;
    A.send({ t: 'mech', k: 'disp' }); await hold(420, []);
    ok(A.all('mech', (m) => m.k === 'vmcola').length === 2 && A.all('mech', (m) => m.k === 'vmstuck').length === 1, 'STUCK! one charge, two cans');
    for (let i = 0; i < 2; i++) { A.send({ t: 'mech', k: 'disp' }); await hold(420, []); }
    ok(A.all('mech', (m) => m.k === 'vmcola').length === 6, 'three charges: six cans out');
    for (let i = 0; i < 40; i++) { const e = lastEn(A); if (e && e.ch >= 1) break; await hold(250, []); }
    A.got.length = 0; C.got.length = 0;
    A.send({ t: 'mech', k: 'disp' }); await hold(300, []);
    ok(A.all('mech', (m) => m.k === 'vmcola').length === 2 && C.all('mech', (m) => m.k === 'vmcolax').length === 2, 'two more: the two oldest go flat (6 a machine)');
    A.send({ t: 'mech', k: 'wall' }); await hold(300, []);
    const w2 = A.all('mech', (m) => m.k === 'vmwall').pop();
    ok(w2 && w2.hp === 1200 && w2.x2 === 1, 'STUCK wall: double HP · ' + (w2 && w2.hp));
    // it blows up (armour 55): the wall goes down with it; the cans stay on the floor
    B.at = add(P, [12, 0, 6]); await hold(1500, []);
    A.got.length = 0; C.got.length = 0;
    const bd = aim(eyeP(B.at), add(P, [0, 2, 0])).d;
    for (let i = 0; i < 10 && !A.all('mech', (m) => m.k === 'down').length; i++) { B.send({ t: 'hit', w: 'ar', to: A.id, d: bd, n: 1, h: 0 }); await hold(150, []); }
    await hold(400, []);
    ok(A.all('mech', (m) => m.k === 'down').length === 1, 'shot to bits: MECH DOWN');
    const wx = C.all('mech', (m) => m.k === 'vmwallx');
    ok(wx.length === 1 && wx[0].why === 'break', 'its wall breaks with it');
    ok(!C.all('mech', (m) => m.k === 'vmcolax').length, 'the cans stay on the floor');
    // a new round / map: no cans left anywhere
    await hold(1000, []);
    C.got.length = 0;
    A.send({ t: 'cfg', map: 'skyline' }); await sleep(1500);
    ok(C.all('mech', (m) => m.k === 'vmcolax').length >= 1, 'a map change clears the cans (mechReset)');
    ok(!/TypeError|ReferenceError|RangeError|uncaught/i.test(srvErr), 'no server errors' + (srvErr ? ': ' + srvErr.slice(0, 400) : ''));
    for (const c of all) c.ws.close();
  }
  srv.kill();
  }
  console.log(fails ? `\n${fails} FAILED` : '\nall passed');
  process.exit(fails ? 1 : 0);
})().catch((e) => { console.log('crash', e); if (srvRef) srvRef.kill(); process.exit(1); });
