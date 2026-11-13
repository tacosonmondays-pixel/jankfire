// WRECKING BALL (battle island hero) over plain ws: climbing in, rams by the MEASURED speed (not what the client
// claims), the rev launch timed by the server, the chain only onto something solid in sight (and the climb it pays
// for), slams sized by the height really fallen, the PILE DRIVER (ult, rise, aim, blast, fizzle), the passive (no
// knockback while rolling), hop out keeps the ult, death / disconnect cleanup, garbage. Each exploit check fails on a
// naive server (trusting client velocity, client charge, client height, unchecked anchors).
// starts its own server: node tests/mech_wrecking_ws.cjs [port]
const WS = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const port = Number(process.argv[2]) || 3161;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
const HP = 0.5; // JF_MECH_HP: wrecking ball 700
const MF = { MECH: 1 << 22, A: 1 << 23, B: 1 << 30, C: 1 << 31 };
const Y = 0.03, X0 = 42, Z0 = 12; // warehouse: the flat open yard round [42, 0, 12]; its west wall is at x = 32.3 (relative -9.7), about 11 m tall
const sh = (a, k) => (Array.isArray(a) && a.length === 3 && a.every(Number.isFinite) ? [a[0] + X0 * k, a[1], a[2] + Z0 * k] : a);
let srvRef = null;

function client(name, extra = {}) {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, got: [], id: 0, q: 0, hp: 100, alive: true, name };
  ws.on('message', (d) => {
    const m = JSON.parse(d);
    if ((m.t === 'mech' || m.t === 'welcome' || m.t === 'spawn') && m.p) m.p = sh(m.p, -1);
    if (m.t === 'mech' && m.to && Array.isArray(m.to)) m.to = sh(m.to, -1);
    if (m.t === 'welcome') { c.id = m.id; c.q = m.q; }
    if (m.t === 'spawn') { c.q = m.q; }
    if (m.t === 'sn') { const r = m.p.find((x) => x[0] === c.id); if (r) { c.hp = r[10]; c.alive = !!r[11]; c.f = r[13]; } return; }
    if (process.env.DBG && m.t === 'mech' && name === 'baller' && /^(no|fix|wbchain|wbpile|wbquake|wbrev|wbslam|down|out|in|gone)$/.test(m.k)) console.log('   .', JSON.stringify(m));
    c.got.push(m);
  });
  ws.on('error', () => {});
  c.send = (m) => { if (typeof m === 'object' && (m.t === 's' || m.t === 'mech') && m.p) m = { ...m, p: sh(m.p, 1) }; if (typeof m === 'object' && m.at) m = { ...m, at: sh(m.at, 1) }; if (ws.readyState === 1) ws.send(typeof m === 'string' ? m : JSON.stringify(m)); };
  c.place = (p, o = {}) => c.send({ t: 's', q: c.q, p, v: o.v || [0, 0, 0], y: o.y ?? 0, x: o.x ?? 0, w: o.w || 'ar', f: o.f || 0 });
  c.take = (t, f) => { const i = c.got.findIndex((m) => m.t === t && (!f || f(m))); return i < 0 ? null : c.got.splice(i, 1)[0]; };
  c.all = (t, f) => c.got.filter((m) => m.t === t && (!f || f(m)));
  c.wait = async (t, f, ms = 4000) => { for (let i = 0; i < ms / 50; i++) { const m = c.take(t, f); if (m) return m; await sleep(50); } return null; };
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'join', name, mode: 'ffa', streaks: ['mechdrop', 'moonboots', 'scythe'], ...extra }); setTimeout(() => res(c), 700); }));
}
const aim = (a, b) => { const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], h = Math.hypot(d[0], d[2]), l = Math.hypot(...d); return { y: Math.atan2(-d[0], -d[2]), x: Math.atan2(d[1], h), d: d.map((v) => v / l) }; };
const hold = async (ms, who) => { for (let t = 0; t < ms; t += 60) { for (const [c, p, o] of who) c.place(typeof p === 'function' ? p(t) : p, typeof o === 'function' ? o(t) : o); await sleep(60); } };
// where the server has the pilot after a move that may have been corrected: the last 'fix', else where it went
const settle = (c, end) => { const f = c.all('mech', (m) => m.k === 'fix').pop(); return f ? f.p.slice() : end.slice(); };
const lerp = (a, b, k) => a.map((x, i) => x + (b[i] - x) * Math.max(0, Math.min(1, k)));

(async () => {
  const srv = srvRef = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(port), JF_TRAIN_STREAKS: '1', JF_MECH_HP: String(HP), JF_MECH_ULT: '20' }, stdio: ['ignore', 'pipe', 'pipe'] });
  let srvErr = ''; srv.stderr.on('data', (d) => { srvErr += d; }); srv.stdout.on('data', (d) => { if (process.env.WBDBG) process.stdout.write('SRV ' + d); if (/Error|uncaught/i.test(String(d))) srvErr += d; });
  const end = (code) => { srv.kill(); process.exit(code); };
  for (let i = 0; i < 60; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }
  const A = await client('baller', { mf: 'wrecking' });
  A.send({ t: 'cfg', map: 'warehouse' }); await sleep(900);
  const B = await client('victim'), C = await client('bystander');
  await sleep(1500);
  const pa = [0, Y, 6], far = [25, Y, 25], far2 = [28, Y, 22];
  const look = aim([0, Y + 1.6, 6], [0, Y, -2]);
  await hold(400, [[A, pa, { y: look.y, x: look.x }], [B, far], [C, far2]]);

  // ---- 1. call it and climb in
  A.send({ t: 'deploy', r: 'mechdrop', at: [0, Y, -2], mf: 'wrecking' });
  const call = await A.wait('mech', (m) => m.k === 'call', 1500);
  ok(call && call.f === 'wrecking', 'MECH DROP with the wrecking frame: called in · ' + (call && call.f));
  await hold(2900, [[A, pa, { y: look.y, x: look.x }], [B, far], [C, far2]]);
  const land = A.take('mech', (m) => m.k === 'land');
  ok(land && land.f === 'wrecking', 'it lands');
  const mp = land ? land.p : [0, Y, -2];
  await hold(300, [[A, [mp[0] + 1.5, Y, mp[2] + 1]], [B, far], [C, far2]]);
  A.got.length = 0; A.send({ t: 'mech', k: 'in' });
  const ein = await A.wait('mech', (m) => m.k === 'in' && m.id === A.id, 1000);
  ok(ein && ein.f === 'wrecking' && ein.max === 1400 * HP, 'climbs in: WRECKING BALL, armour ' + (ein && ein.max));
  const P0 = mp.slice();
  let P = P0.slice();
  const pilot = (ms, path, f = 0, o = {}) => hold(ms, [[A, path || (() => P), (t) => ({ f: MF.MECH | f, ...(typeof o === 'function' ? o(t) : o) })], [B, o.b || far], [C, o.c || far2]]);
  await pilot(800);
  const en0 = A.all('mech', (m) => m.k === 'en').pop();
  ok(en0 && Number.isFinite(en0.u), 'the energy message carries the ultimate charge · u ' + (en0 && en0.u));

  // ---- 2. ram: by the speed the server measured
  const bAt = [P0[0], Y, P0[2] - 16];
  B.got.length = 0; A.got.length = 0;
  // (a) a cheat: sits still but claims to be doing 30 m/s
  await hold(1200, [[A, P0, { f: MF.MECH, v: [0, 0, -30] }], [B, [P0[0], Y, P0[2] - 2]], [C, far2]]);
  ok(!B.all('dmg', (m) => m.to === B.id && m.w === 'wbram').length, 'sitting next to them claiming 30 m/s: no ram (the server measures)');
  // (b) really rolls through them at 20 m/s
  await hold(300, [[A, P0, { f: MF.MECH }], [B, bAt], [C, far2]]);
  B.got.length = 0;
  const roll = (t) => { const s2 = t < 600 ? 0.5 * (20 / 0.6) * (t / 1000) ** 2 : 6 + 20 * (t - 600) / 1000; return [P0[0], Y, P0[2] - Math.min(30, s2)]; }; // (it gets going like a real ball: 0 to 20 m/s in 0.6 s)
  await hold(2100, [[A, roll, { f: MF.MECH, v: [0, 0, -20] }], [B, bAt], [C, far2]]);
  P = [P0[0], Y, P0[2] - 30];
  const rd = B.all('dmg', (m) => m.to === B.id && m.w === 'wbram');
  ok(rd.length === 1 && rd[0].a >= 35 && rd[0].a <= 55, `rolled through them at 20 m/s: one ram for ${rd[0] && rd[0].a} (8 + 14 x 2.6 = 44)`);
  ok(!A.all('mech', (m) => m.k === 'fix').length, 'top speed (22) is allowed: no correction');
  await sleep(2600); // (B respawns if it died)
  // (review #418) a saved-up teleport: sits still a second (the move bank fills), then ONE snapshot 10 m into them
  { const T0 = P.slice(), T1 = [P[0], Y, P[2] - 10], bT = [P[0], Y, P[2] - 10.5];
    await hold(1200, [[A, T0, { f: MF.MECH }], [B, bT], [C, far2]]); B.got.length = 0;
    await hold(600, [[A, T1, { f: MF.MECH }], [B, bT], [C, far2]]);
    const td = B.all('dmg', (m) => m.to === B.id && m.w === 'wbram');
    ok(!td.length || td[0].a <= 30, `sat still, then one 10 m snapshot into them: no max ram (${td.length ? td[0].a : 'none'}; was 70)`);
    P = settle(A, T1); await pilot(900); await sleep(2000); }

  // ---- 3. the rev: timed by the server
  A.got.length = 0;
  A.send({ t: 'mech', k: 'rev', on: 0 }); await pilot(200);
  ok(!A.all('mech', (m) => m.k === 'wbrev' && m.on === 2).length, 'let go of a rev it never started: nothing');
  A.send({ t: 'mech', k: 'rev', on: 1 }); await pilot(100); A.send({ t: 'mech', k: 'rev', on: 0 }); await pilot(200);
  ok(!A.all('mech', (m) => m.k === 'wbrev' && m.on === 2).length, 'a 0.1 s tap: too short, no launch');
  // a cheat: no rev, just goes 34 m/s
  A.got.length = 0;
  const Q0 = P.slice();
  await pilot(1500, (t) => lerp(Q0, [Q0[0] + 60, Y, Q0[2]], t / 1500));
  ok(A.all('mech', (m) => m.k === 'fix').length > 0, '40 m/s for 1.5 s without a launch: put back');
  P = settle(A, [Q0[0] + 60, Y, Q0[2]]);
  await pilot(800); // (the correction's grace)
  A.got.length = 0;
  A.send({ t: 'mech', k: 'rev', on: 1 }); await pilot(900); A.send({ t: 'mech', k: 'rev', on: 0 }); await sleep(30);
  const rev = await A.wait('mech', (m) => m.k === 'wbrev' && m.on === 2, 800);
  ok(rev && rev.v >= 35 && rev.v <= 36.01, 'held 0.9 s: launch at ' + (rev && rev.v) + ' m/s');
  const Q1 = P.slice();
  await pilot(800, (t) => lerp(Q1, [Q1[0] - 24, Y, Q1[2]], t / 700));
  P = [Q1[0] - 24, Y, Q1[2]];
  ok(!A.all('mech', (m) => m.k === 'fix').length, 'the launch (34 m/s for 0.7 s): allowed');
  const en1 = A.all('mech', (m) => m.k === 'en').pop();
  ok(en1 && en1.v <= 82, 'it cost energy · ' + (en1 && en1.v));
  await pilot(1500);

  // ---- 4. the chain: onto something solid you can see, in reach; it pays for a climb to its anchor
  const W0 = [-6, Y, 0]; // 3.7 m off the west wall
  A.got.length = 0;
  { const from = P.slice(), l = Math.hypot(W0[0] - from[0], W0[2] - from[2]), ms = Math.max(600, l / 15 * 1000); await pilot(ms + 300, (t) => lerp(from, W0, t / ms)); }
  P = W0.slice();
  A.got.length = 0;
  A.send({ t: 'mech', k: 'chain', p: [0, 12, 8] }); await pilot(150);
  ok((A.take('mech', (m) => m.k === 'no') || {}).why === 'chain: nothing to hook', 'chain at thin air: refused');
  A.send({ t: 'mech', k: 'chain', p: [-30, 6, 0] }); await pilot(150);
  ok((A.take('mech', (m) => m.k === 'no') || {}).why === 'chain: nothing to hook', 'chain at a spot behind the wall (no line of sight): refused');
  A.send({ t: 'mech', k: 'chain', p: [-9.7, 9, 60] }); await pilot(150);
  ok((A.take('mech', (m) => m.k === 'no') || {}).why === 'chain: out of reach', 'chain 60 m away: out of reach');
  A.send({ t: 'mech', k: 'chain', p: 'x' }); A.send({ t: 'mech', k: 'chain', p: [NaN, 1, 2] }); A.send({ t: 'mech', k: 'chain', p: [1e9, 1e9, 1e9] }); await pilot(150);
  ok(!A.all('mech', (m) => m.k === 'wbchain' && !m.off).length, 'garbage anchors: nothing');
  A.got.length = 0;
  // a cheat first: up 10 m with no chain
  await pilot(500, (t) => [W0[0], Y + 10 * Math.min(1, t / 300), W0[2]]);
  ok(A.all('mech', (m) => m.k === 'fix').length > 0, 'climbing 10 m with nothing paying for it: put back');
  P = W0.slice();
  await pilot(900);
  A.got.length = 0;
  A.send({ t: 'mech', k: 'chain', p: [-9.7, 9, 0] }); await pilot(150, null, MF.A);
  const ch = A.take('mech', (m) => m.k === 'wbchain' && !m.off);
  ok(ch && Math.abs(ch.p[0] + 9.7) < 0.3 && ch.len > 5 && ch.len < 9, `chain onto the wall in sight: bites at ${ch && ch.p.map((x) => x.toFixed(1))}, ${ch && ch.len} m`);
  ok(B.all('mech', (m) => m.k === 'wbchain').length > 0, 'everyone sees the chain');
  await pilot(400, (t) => lerp(W0, [-5, 7, 0], t / 400), MF.A);
  P = [-5, 7, 0];
  ok(!A.all('mech', (m) => m.k === 'fix').length, 'swung up 7 m on the chain: allowed');
  await pilot(300, (t) => lerp(P, [-5, 20, 0], t / 200), MF.A);
  const fx = A.all('mech', (m) => m.k === 'fix').length, off = A.all('mech', (m) => m.k === 'wbchain' && m.off);
  ok(fx > 0 || off.length > 0, 'way above the anchor (20 m): put back / the chain snaps');
  A.send({ t: 'mech', k: 'chain', off: 1 }); await pilot(200);
  P = W0.slice();
  await pilot(1200, () => W0);
  A.got.length = 0;
  A.send({ t: 'mech', k: 'chain', p: [-9.7, 9, 0] }); await pilot(100);
  A.send({ t: 'mech', k: 'chain', off: 1 }); await pilot(100);
  A.send({ t: 'mech', k: 'chain', p: [-9.7, 9, 0] }); await pilot(100);
  ok(A.all('mech', (m) => m.k === 'wbchain' && !m.off).length === 1, 'chain, let go, chain again at once: the cooldown holds');
  // (review #418) the climb the chain paid for doesn't outlive it: chain, let go, roll off, wait on the floor, then 9 m up in one snapshot
  await pilot(1200);
  A.send({ t: 'mech', k: 'chain', p: [-9.7, 9, 0] }); await pilot(300, null, MF.A);
  A.send({ t: 'mech', k: 'chain', off: 1 }); await pilot(200);
  { const R0 = P.slice(), R1 = [P[0] + 6, Y, P[2]]; await pilot(700, (t) => lerp(R0, R1, t / 600)); P = R1; await pilot(2500);
    A.got.length = 0; await pilot(300, () => [P[0], Y + 9, P[2]]);
    ok(A.all('mech', (m) => m.k === 'fix').length > 0, 'chain let go, rolled off, waited: a 9 m climb later is put back (no leftover chain budget)');
    P = settle(A, P); await pilot(900); }
  { const back = P.slice(); await pilot(900, (t) => lerp(back, W0, t / 700)); P = W0.slice(); await pilot(600); }
  await pilot(1500);

  // ---- 5. the slam: sized by the height it really fell
  const S0 = [0, Y, -6], cAt = [3, Y, -6];
  { const from = P.slice(), l = Math.hypot(S0[0] - from[0], S0[2] - from[2]), ms = Math.max(600, l / 15 * 1000); await pilot(ms + 300, (t) => lerp(from, S0, t / ms), 0, { c: cAt }); }
  P = S0.slice();
  await pilot(600, null, 0, { c: cAt });
  A.got.length = 0; C.got.length = 0;
  A.send({ t: 'mech', k: 'slam' });
  await pilot(560, (t) => (t < 280 ? [S0[0], Y + 2.8 * (t / 280), S0[2]] : [S0[0], Math.max(Y, Y + 2.8 - 2.8 * ((t - 280) / 160)), S0[2]]), MF.B, { c: cAt });
  await pilot(300, null, 0, { c: cAt });
  const q = A.all('mech', (m) => m.k === 'wbquake');
  ok(q.length === 1 && q[0].sz < 0.15 && q[0].r < 6, `hop slam (a 2.8 m drop): a small one · size ${q[0] && q[0].sz}, r ${q[0] && q[0].r}`);
  const cs = C.all('dmg', (m) => m.to === C.id && m.w === 'wbslam');
  ok(cs.length === 1 && cs[0].a > 15 && cs[0].a < 45, 'C 3 m away: slammed for ' + (cs[0] && cs[0].a));
  A.got.length = 0;
  A.send({ t: 'mech', k: 'slam' }); await pilot(200);
  ok(!A.all('mech', (m) => m.k === 'wbslam').length, 'slam again at once: cooldown');
  // a cheat: claims it fell from 25 m (it never got up there)
  await pilot(6000, null, 0, { c: far2 });
  A.got.length = 0;
  A.send({ t: 'mech', k: 'slam' });
  await pilot(700, (t) => (t < 200 ? [S0[0], Y + 25, S0[2]] : [S0[0], Y, S0[2]]), MF.B);
  await pilot(300);
  const q2 = A.all('mech', (m) => m.k === 'wbquake');
  ok(A.all('mech', (m) => m.k === 'fix').length > 0 && (!q2.length || q2[0].sz < 0.15), `a slam "from 25 m" it never climbed: put back, no big slam · ${q2.length ? 'size ' + q2[0].sz : 'none'}`);
  await pilot(800);

  // ---- 6. the passive: no knockback while it's rolling
  const kbAt = (moving) => moving ? (t) => [S0[0] + 0.5 + t / 1000 * 18, Y, S0[2]] : () => S0;
  A.got.length = 0;
  for (const moving of [false, true]) {
    await pilot(600, kbAt(moving), 0, { b: [S0[0], Y, S0[2] - 14] });
    B.place([S0[0], Y, S0[2] - 14], { w: 'sniper' }); await sleep(60);
    A.got = A.got.filter((m) => m.t !== 'kb');
    const at = moving ? [S0[0] + 0.5 + 0.6 * 18, Y, S0[2]] : S0;
    B.send({ t: 'hit', w: 'sniper', to: A.id, d: aim([S0[0], Y + 1.6, S0[2] - 14], [at[0], Y + 1.5, at[2]]).d, n: 1, h: 0 });
    await pilot(250, (t) => (moving ? [at[0] + t / 1000 * 18, Y, at[2]] : S0), 0, { b: [S0[0], Y, S0[2] - 14] });
    const kb = A.all('kb').pop(), mag = kb ? Math.hypot(...kb.v) : -1;
    if (!moving) ok(kb && mag > 0, 'standing still: a mech takes a little knockback · ' + mag.toFixed(2));
    else ok(kb && mag === 0, 'rolling at 18 m/s: none at all (the passive) · ' + mag.toFixed(2));
  }
  P = [S0[0] + 0.5 + 0.85 * 18, Y, S0[2]];
  { const from = P.slice(); await pilot(1600, (t) => lerp(from, S0, t / 1300)); } P = S0.slice();

  // ---- 7. PILE DRIVER: ult, rise, hang, aim, dive, blast
  for (let i = 0; i < 60; i++) { const e = A.all('mech', (m) => m.k === 'en').pop(); if (e && e.u >= 100) break; await pilot(150); }
  const eU = A.all('mech', (m) => m.k === 'en').pop();
  ok(eU && eU.u >= 100, 'the ultimate charged (JF_MECH_ULT) · ' + (eU && eU.u));
  A.got.length = 0; B.got.length = 0; C.got.length = 0;
  const tgt = [S0[0], Y, S0[2] - 18], cNear = [S0[0] + 5, Y, S0[2] - 18];
  A.send({ t: 'mech', k: 'pile' });
  // the real thing: up 30 m over 1.1 s, hang, aim at B, dive
  const top = [S0[0], Y + 30, S0[2]];
  await pilot(1200, (t) => lerp(S0, top, t / 1100), MF.B, { b: tgt, c: cNear });
  A.got = A.got.filter((m) => !(m.t === 'mech' && m.k === 'fix'));
  const la = aim([top[0], top[1] + 3.4, top[2]], tgt);
  await pilot(400, () => top, MF.B, { y: la.y, x: la.x, b: tgt, c: cNear });
  A.send({ t: 'mech', k: 'pdrop', d: la.d });
  const dn = await A.wait('mech', (m) => m.k === 'wbpile' && m.ph === 'down', 600);
  ok(dn && Math.hypot(dn.to[0] - tgt[0], dn.to[2] - tgt[2]) < 1.5, 'aimed at B: it dives at ' + (dn && dn.to.map((x) => x.toFixed(1))));
  await pilot(700, (t) => lerp(top, [tgt[0], Y, tgt[2]], t / 600), MF.B, { y: la.y, x: la.x, b: tgt, c: cNear });
  P = [tgt[0], Y, tgt[2]];
  await pilot(300, null, 0, { b: tgt, c: cNear });
  const pq = A.all('mech', (m) => m.k === 'wbquake' && m.big);
  ok(pq.length === 1, 'PILE DRIVER lands: one big quake');
  ok(!A.all('mech', (m) => m.k === 'fix').length, 'the rise and the dive it paid for: no correction');
  const bd = B.all('dmg', (m) => m.to === B.id && m.w === 'wbpile'), cd2 = C.all('dmg', (m) => m.to === C.id && m.w === 'wbpile');
  ok(bd.length === 1 && bd[0].ko, 'B right under it: flattened (' + (bd[0] && bd[0].a) + ')');
  ok(cd2.length === 1 && cd2[0].a > 60 && cd2[0].a < 160, 'C 5 m out: a share of it · ' + (cd2[0] && cd2[0].a));
  A.send({ t: 'mech', k: 'pile' }); await pilot(200);
  ok((A.take('mech', (m) => m.k === 'no') || {}).why === 'ultimate not ready', 'pile driver again at once: the ult is spent (its own hits don\'t recharge it)');
  // a cheat: the ult's back (JF_MECH_ULT), it claims it shot up 60 m
  for (let i = 0; i < 60; i++) { const e = A.all('mech', (m) => m.k === 'en').pop(); if (e && e.u >= 100) break; await pilot(150, null, 0, { b: tgt, c: cNear }); }
  // a cheat: claims it shot up 60 m
  A.got.length = 0;
  A.send({ t: 'mech', k: 'pile' });
  await pilot(400, (t) => [P[0], Y + 60 * Math.min(1, t / 300), P[2]], MF.B, { b: tgt, c: cNear });
  ok(A.all('mech', (m) => m.k === 'wbpile' && m.ph === 'up').length === 1 && A.all('mech', (m) => m.k === 'fix' && m.p[1] < Y + 37).length > 0 && A.all('mech', (m) => m.k === 'fix').length > 0, 'pile driver: going 60 m up when it only pays for 30: put back');
  await pilot(900, () => P, MF.B, { b: tgt, c: cNear }); // (it spent that one: no blast)
  ok(!A.all('mech', (m) => m.k === 'wbquake' && m.big).length, 'and that cheat never lands a blast');
  await sleep(2600);

  // a fizzle: the ult's back again, it "dives" without ever having gone up
  for (let i = 0; i < 60; i++) { const e = A.all('mech', (m) => m.k === 'en').pop(); if (e && e.u >= 100) break; await pilot(150, null, 0, { b: tgt, c: cNear }); }
  A.got.length = 0; C.got.length = 0;
  A.send({ t: 'mech', k: 'pile' });
  await pilot(400, null, MF.B, { b: tgt, c: cNear });
  A.send({ t: 'mech', k: 'pdrop', d: [0, -1, 0] });
  await pilot(300, (t) => [P[0], Y + 3 * Math.min(1, t / 100), P[2]], MF.B, { b: tgt, c: cNear });
  await pilot(400, () => P, MF.B, { b: tgt, c: cNear });
  ok(!A.all('mech', (m) => m.k === 'wbquake' && m.big).length && !C.all('dmg', (m) => m.w === 'wbpile').length, 'a pile driver that never got up there: fizzles, nobody hurt');
  // (review #418) the fizzle's 32 m of paid climb doesn't linger: 3 s later, 25 m up in one snapshot
  await pilot(3000, null, 0, { b: tgt, c: cNear });
  A.got.length = 0; await pilot(300, () => [P[0], Y + 25, P[2]], 0, { b: tgt, c: cNear });
  ok(A.all('mech', (m) => m.k === 'fix').length > 0, 'after a fizzled pile driver, 25 m up in one snapshot: put back (no leftover budget)');
  P = settle(A, P); await pilot(1200, (t) => [P[0], Y, P[2]]); P = [P[0], Y, P[2]];
  // (review #418) a real rise, aimed at a spot 18 m out, then it flies on THROUGH the spot and comes down 12 m past it (inside the old 'within 5 m of how far it was' rule)
  for (let i = 0; i < 60; i++) { const e = A.all('mech', (m) => m.k === 'en').pop(); if (e && e.u >= 100) break; await pilot(150); }
  { const S1 = P.slice(), top3 = [S1[0], Y + 30, S1[2]], spot = [S1[0], Y, S1[2] - 18], past = [S1[0], Y, S1[2] - 30];
    A.got.length = 0; C.got.length = 0;
    A.send({ t: 'mech', k: 'pile' });
    await pilot(1300, (t) => lerp(S1, top3, t / 1100), MF.B, { c: past });
    const la3 = aim([top3[0], top3[1] + 4.6, top3[2]], spot);
    await pilot(300, () => top3, MF.B, { y: la3.y, x: la3.x, c: past });
    A.send({ t: 'mech', k: 'pdrop', d: la3.d }); await pilot(60, () => top3, MF.B, { y: la3.y, x: la3.x, c: past });
    const dn3 = await A.wait('mech', (m) => m.k === 'wbpile' && m.ph === 'down', 600);
    await pilot(900, (t) => lerp(top3, past, t / 800), MF.B, { c: past });
    await pilot(400, null, 0, { c: past });
    ok(dn3 && !A.all('mech', (m) => m.k === 'wbquake' && m.big).length && !C.all('dmg', (m) => m.w === 'wbpile').length, `pile driver aimed 18 m out, flown on and down 12 m past the ring: no blast where it came down (${A.all('mech', (m) => m.k === 'wbpile' && m.ph === 'off').length ? 'ended' : 'no off'})`);
    P = settle(A, past); await pilot(1200, (t) => [P[0], Y, P[2]]); P = [P[0], Y, P[2]]; await pilot(600);
    const b2 = P.slice(), l2 = Math.hypot(S0[0] - b2[0], S0[2] - b2[2]), ms2 = Math.max(600, l2 / 15 * 1000); await pilot(ms2 + 400, (t) => lerp(b2, S0, t / ms2)); P = S0.slice(); } // (back to the middle of the yard)
  await sleep(2600);

  // a cheat: a real rise and dive call, then it keeps zooming sideways at 65 m/s instead of landing
  for (let i = 0; i < 60; i++) { const e = A.all('mech', (m) => m.k === 'en').pop(); if (e && e.u >= 100) break; await pilot(150); }
  A.got.length = 0;
  A.send({ t: 'mech', k: 'pile' });
  const top2 = [P[0], Y + 30, P[2]], P2 = P.slice();
  await pilot(1500, (t) => lerp(P2, top2, t / 1100), MF.B);
  A.send({ t: 'mech', k: 'pdrop', d: [0, -1, 0] }); await pilot(100, () => top2, MF.B);
  await pilot(1000, (t) => [top2[0] + 65 * t / 1000, top2[1], top2[2]], MF.B);
  ok(A.all('mech', (m) => m.k === 'wbpile' && m.ph === 'off').length === 1 && A.all('mech', (m) => m.k === 'fix').length > 0, 'pile driver dive, then zooming sideways at 65 m/s: the dive ends, put back');
  P = settle(A, top2);
  await pilot(1800, (t) => lerp(P, [P[0], Y, P[2]], t / 1200)); P = [P[0], Y, P[2]];
  await pilot(900);

  // ---- 8. hop out keeps the ult and cooldowns; disconnect cleans up
  A.got.length = 0;
  A.send({ t: 'mech', k: 'slam' }); await pilot(100);
  A.send({ t: 'mech', k: 'out' }); await sleep(300);
  const out = await A.wait('mech', (m) => m.k === 'out' && m.why === 'hop', 800);
  ok(out, 'hops out');
  await hold(1300, [[A, [P[0] + 2.2, Y, P[2]]], [B, far], [C, far2]]);
  A.got.length = 0; A.send({ t: 'mech', k: 'in' });
  await hold(500, [[A, P, { f: MF.MECH }], [B, far], [C, far2]]);
  const back = A.all('mech', (m) => m.k === 'en').pop();
  ok(back && back.cd && back.cd.slam > 0, 'back in: the slam cooldown waited with the mech · ' + (back && JSON.stringify(back.cd)));
  A.send({ t: 'mech', k: 'chain', p: [-9.7, 9, 0] }); await pilot(200);
  // garbage: wrong types, unknown keys, a flood
  for (const m of [{ k: 'rev', on: '1' }, { k: 'rev', on: { x: 1 } }, { k: 'pdrop', d: [1e12, 0, 0] }, { k: 'pdrop', d: 'down' }, { k: 'pile', x: [[[[1]]]] }, { k: 'swing' }, { k: 'lunge', to: 5 }, { k: 'x'.repeat(40) }, { k: null }]) A.send({ t: 'mech', ...m });
  for (let i = 0; i < 200; i++) A.send({ t: 'mech', k: 'slam' });
  await pilot(400);
  ok(srv.exitCode === null, 'garbage + a flood: the server is fine');
  A.ws.close(); await sleep(800);
  const gone = B.all('mech', (m) => (m.k === 'out' || m.k === 'gone') && (m.id === A.id || m.m));
  ok(gone.length > 0, 'the pilot disconnects: the mech goes with them');
  ok(!/TypeError|ReferenceError|uncaught/i.test(srvErr), 'no server errors' + (srvErr ? ': ' + srvErr.slice(0, 400) : ''));
  console.log(fails ? `\n${fails} FAILED` : '\nall passed');
  end(fails ? 1 : 0);
})().catch((e) => { console.log('crash', e); if (srvRef) srvRef.kill(); process.exit(1); });
