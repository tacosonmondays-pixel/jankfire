// TROLLEY (battle island hero) over plain ws, in Team Deathmatch (allies ride, enemies get scooped): climbing in, the
// drift's RAM CHARGE only at a speed the server MEASURED (and by its clock), the push dealing what that charge says,
// speed caps outside the push / AISLE 5 windows, rams by measured speed, tin cans (rate, aim, bounces, the bonk), CLEAN
// UP AISLE 5 (scoop enemies only, max 3, only what it runs into, they can't shoot or walk out, 8/s, the dump), the pound
// coin lock (allies only, close, one rider, guns work, hops out), every cleanup path (hop out, break, death and
// disconnect of either side, a map change), garbage. Each exploit check fails on a naive server.
// starts its own server: node tests/mech_trolley_ws.cjs [port]
const WS = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const port = Number(process.argv[2]) || 3171;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
const HP = 0.25; // JF_MECH_HP: trolley 200 armour
const MF = { MECH: 1 << 22, A: 1 << 23, B: 1 << 30, C: 1 << 31 }; // (trolley: A drift, B AISLE 5, C push)
const Y = 0.03, X0 = 42, Z0 = 12; // warehouse: the flat yard round [42, 0, 12]. the lane x = 0 is clear from z = 26 to -20
const sh = (a, k) => (Array.isArray(a) && a.length === 3 && a.every(Number.isFinite) ? [a[0] + X0 * k, a[1], a[2] + Z0 * k] : a);
let srvRef = null;
const SN = new Map(); // id -> where the server has them

function client(name, extra = {}) {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, got: [], id: 0, q: 0, hp: 100, alive: true, name, team: 0 };
  ws.on('message', (d) => {
    const m = JSON.parse(d);
    if ((m.t === 'mech' || m.t === 'welcome' || m.t === 'spawn' || m.t === 'pd' || m.t === 'ps' || m.t === 'pu') && m.p) m.p = sh(m.p, -1);
    if (m.t === 'welcome') { c.id = m.id; c.q = m.q; c.team = m.team || 0; }
    if (m.t === 'spawn') { c.q = m.q; }
    if (m.t === 'teams' && Array.isArray(m.list)) { const r = m.list.find((x) => x[0] === c.id); if (r) c.team = r[1]; }
    if (m.t === 'sn') { for (const e of m.p) SN.set(e[0], [e[1] - X0, e[2], e[3] - Z0]); const r = m.p.find((x) => x[0] === c.id); if (r) { c.hp = r[10]; c.alive = !!r[11]; c.f = r[13]; } return; }
    if (process.env.DBG && m.t === 'mech' && /^(no|fix|trhold|traisle|trpush|down|out|in)$/.test(m.k) && (name === 'pilot' || m.k === 'no')) console.log('   .', name, JSON.stringify(m));
    c.got.push(m);
    if (c.got.length > 4000) c.got.splice(0, 1000);
  });
  ws.on('error', () => {});
  c.send = (m) => { if (typeof m === 'object' && (m.t === 's' || m.t === 'mech') && m.p) m = { ...m, p: sh(m.p, 1) }; if (typeof m === 'object' && m.at) m = { ...m, at: sh(m.at, 1) }; if (ws.readyState === 1) ws.send(typeof m === 'string' ? m : JSON.stringify(m)); };
  c.place = (p, o = {}) => c.send({ t: 's', q: c.q, p, v: o.v || [0, 0, 0], y: o.y ?? 0, x: o.x ?? 0, w: o.w || 'ar', f: o.f || 0 });
  c.take = (t, f) => { const i = c.got.findIndex((m) => m.t === t && (!f || f(m))); return i < 0 ? null : c.got.splice(i, 1)[0]; };
  c.all = (t, f) => c.got.filter((m) => m.t === t && (!f || f(m)));
  c.wait = async (t, f, ms = 4000) => { for (let i = 0; i < ms / 50; i++) { const m = c.take(t, f); if (m) return m; await sleep(50); } return null; };
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'join', name, mode: 'ffa', streaks: ['mechdrop', 'moonboots', 'scythe'], ...extra }); setTimeout(() => res(c), 500); }));
}
const aim = (a, b) => { const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], h = Math.hypot(d[0], d[2]), l = Math.hypot(...d); return { y: Math.atan2(-d[0], -d[2]), x: Math.atan2(d[1], h), d: d.map((v) => v / l) }; };
const lerp = (a, b, k) => a.map((x, i) => x + (b[i] - x) * Math.max(0, Math.min(1, k)));
const near = (a, b, r) => !!a && !!b && Math.hypot(a[0] - b[0], a[2] - b[2]) < r;

(async () => {
  const srv = srvRef = spawn(process.execPath, ['--max-old-space-size=320', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(port), JF_GAME: 'tdm', JF_TRAIN_STREAKS: '1', JF_MECH_HP: String(HP), JF_MECH_ULT: '25' }, stdio: ['ignore', 'pipe', 'pipe'] });
  let srvErr = ''; srv.stderr.on('data', (d) => { srvErr += d; }); srv.stdout.on('data', (d) => { if (process.env.SRVDBG) process.stdout.write('SRV ' + d); if (/Error|uncaught/i.test(String(d))) srvErr += d; });
  const end = (code) => { srv.kill(); process.exit(code); };
  for (let i = 0; i < 60; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }
  const A = await client('pilot', { mf: 'trolley' });
  A.send({ t: 'cfg', map: 'warehouse', bots: 0 }); await sleep(900);
  const others = [];
  for (let i = 0; i < 7; i++) others.push(await client('p' + i));
  await sleep(1200);
  const allies = others.filter((c) => c.team && c.team === A.team), foes = others.filter((c) => c.team && c.team !== A.team);
  ok(A.team && allies.length >= 2 && foes.length >= 4, `team deathmatch: pilot on team ${A.team}, ${allies.length} allies, ${foes.length} enemies`);
  if (!(allies.length >= 2 && foes.length >= 4)) end(1);
  const [R, R2] = allies, [E1, E2, E3, E4] = foes, ALL = [A, ...others];
  // where everyone stands when a step doesn't say: out of the way along x = 26
  const home = new Map(others.map((c, i) => [c, [26, Y, -16 + i * 6]]));
  let P = [0, Y, 22];
  const look0 = aim([0, Y + 1.6, 22], [0, Y, 16]);
  // one 60 ms beat for everyone: who(t) -> Map(client -> [pos, opts]) for the ones that move this step
  const run = async (ms, who = () => new Map(), af = 0, ao = {}) => {
    for (let t = 0; t < ms; t += 60) {
      const w = who(t);
      for (const c of ALL) {
        if (c.ws.readyState !== 1) continue;
        if (w.has(c)) { const [p, o] = w.get(c); c.place(p, o || {}); continue; }
        if (c === A) { const o = typeof ao === 'function' ? ao(t) : ao; c.place(typeof P === 'function' ? P(t) : P, { f: MF.MECH | (typeof af === 'function' ? af(t) : af), ...o }); continue; }
        c.place(home.get(c));
      }
      await sleep(60);
    }
  };
  await run(400, () => new Map([[A, [P, { y: look0.y, x: look0.x }]]]));

  // ---- 1. call it, climb in
  A.send({ t: 'deploy', r: 'mechdrop', at: [0, Y, 16], mf: 'trolley' });
  const call = await A.wait('mech', (m) => m.k === 'call', 1500);
  ok(call && call.f === 'trolley', 'MECH DROP with the trolley frame: called in · ' + (call && call.f));
  await run(2900, () => new Map([[A, [P, { y: look0.y, x: look0.x }]]]));
  const land = A.take('mech', (m) => m.k === 'land');
  const mp = land ? land.p : [0, Y, 16];
  await run(300, () => new Map([[A, [[mp[0] + 1.5, Y, mp[2] + 1]]]]));
  A.got.length = 0; A.send({ t: 'mech', k: 'in' });
  const ein = await A.wait('mech', (m) => m.k === 'in' && m.id === A.id, 1000);
  ok(ein && ein.f === 'trolley' && ein.max === 800 * HP, 'climbs in: TROLLEY, armour ' + (ein && ein.max));
  P = [0, Y, 22];
  await run(900);
  const en = () => A.all('mech', (m) => m.k === 'en').pop() || {};
  ok(Number.isFinite(en().ch) && Number.isFinite(en().u), `the energy message carries the ram charge and the ult · ch ${en().ch}, u ${en().u}`);
  const dmgOn = (c, w) => c.all('dmg', (m) => m.to === c.id && m.w === w);

  // ---- 2. the drift: the charge only builds at a speed the server measured
  A.got.length = 0;
  await run(2000, () => new Map(), MF.A, { v: [0, 0, -30] }); // sits still, claims a 30 m/s drift
  ok(!(en().ch > 0), 'sitting still claiming a 30 m/s drift: no ram charge · ' + en().ch);
  await run(1200, () => new Map(), MF.A, (t) => ({ v: [0, 0, -8] })); // and creeping at 8 m/s: too slow
  { const Q = P.slice(); P = (t) => [Q[0], Y, Q[2] - 8 * t / 1000]; await run(1200, undefined, MF.A); P = [Q[0], Y, Q[2] - 9.6]; }
  ok(!(en().ch > 0), 'drifting at 8 m/s (under 12): no charge · ' + en().ch);
  // a push with no charge on an enemy right in front: the small one
  const pushAt = (from, to, ms) => (t) => lerp(from, to, t / ms);
  E1.got.length = 0; A.got.length = 0;
  { const Q = P.slice(), tgt = [Q[0], Y, Q[2] - 4.5];
    await run(300, () => new Map([[E1, [tgt]]]));
    A.send({ t: 'mech', k: 'push' });
    P = pushAt(Q, [Q[0], Y, Q[2] - 12], 400);
    await run(600, () => new Map([[E1, [tgt]]]), MF.C);
    P = [Q[0], Y, Q[2] - 12]; }
  const tp0 = A.all('mech', (m) => m.k === 'trpush').pop(), pd0 = dmgOn(E1, 'trpush');
  ok(tp0 && tp0.c === 0 && tp0.v === 30, `push with no charge: ${tp0 && tp0.v} m/s, charge ${tp0 && tp0.c}`);
  ok(pd0.length === 1 && pd0[0].a === 30, 'and it hits for the uncharged 30 (not 80) · ' + (pd0[0] && pd0[0].a));
  A.send({ t: 'mech', k: 'push' }); await run(200);
  ok(A.all('mech', (m) => m.k === 'trpush').length === 1, 'push again at once: the 4 s cooldown');
  await sleep(2500);

  // a real drift: round in an arc at 20 m/s for 1.8 s
  { P = [0, Y, 20]; await run(1500, undefined, 0); }
  A.got.length = 0;
  { const c0 = [6, Y, 14], r = 7, w = 20 / r; P = (t) => [c0[0] - Math.cos(w * t / 1000) * r + (t < 60 ? 0 : 0), Y, c0[2] + Math.sin(w * t / 1000) * r + 6 - 6]; // (starts at [-1, 14]: a short hop from [0, 20] would be a jump: ease over first)
    const from = [0, Y, 20], st = [c0[0] - r, Y, c0[2]];
    const Pa = P; P = (t) => lerp(from, st, t / 500); await run(600);
    P = Pa; await run(1900, undefined, MF.A);
    P = Pa(1900); }
  const ch1 = en().ch;
  ok(ch1 >= 0.95, 'drifting round an arc at 20 m/s for 1.8 s: a full charge · ' + ch1);
  ok(!A.all('mech', (m) => m.k === 'fix').length, 'and no correction (20 m/s is fine)');
  // keep it 3 s: push within that window = the big one
  E2.got.length = 0;
  { const Q = P.slice(), tgt = [Q[0], Y, Q[2] - 5];
    const look = aim([Q[0], Y + 2.9, Q[2]], [Q[0], Y + 1, Q[2] - 10]);
    await run(700, () => new Map([[E2, [tgt]]]), 0, { y: look.y, x: look.x });
    A.got.length = 0;
    A.send({ t: 'mech', k: 'push' });
    P = pushAt(Q, [Q[0], Y, Q[2] - 15], 400);
    await run(600, () => new Map([[E2, [tgt]]]), MF.C, { y: look.y, x: look.x });
    P = [Q[0], Y, Q[2] - 15]; }
  const tp1 = A.all('mech', (m) => m.k === 'trpush').pop(), pd1 = dmgOn(E2, 'trpush');
  ok(tp1 && tp1.c >= 0.9 && tp1.v >= 39, `push with the charge (${tp1 && tp1.c}): ${tp1 && tp1.v} m/s`);
  ok(pd1.length === 1 && pd1[0].a >= 75, 'and it hits for up to 80 · ' + (pd1[0] && pd1[0].a));
  ok(!A.all('mech', (m) => m.k === 'fix').length, 'the 40 m/s lunge in its window: no correction');
  ok(!(en().ch > 0), 'the push spent the charge · ' + en().ch);
  // the charge expires 3 s after the drift
  await sleep(1500);
  { P = [0, Y, 20]; await run(1500); const c0 = [6, Y, 14], r = 7, w = 20 / r, Pa = (t) => [c0[0] - Math.cos(w * t / 1000) * r, Y, c0[2] + Math.sin(w * t / 1000) * r];
    P = (t) => lerp([0, Y, 20], Pa(0), t / 500); await run(600); P = Pa; await run(1900, undefined, MF.A); P = Pa(1900); }
  ok(en().ch >= 0.95, 'drift again: full · ' + en().ch);
  await run(3800);
  ok(!(en().ch > 0), 'and 3.5 s later it\'s gone · ' + en().ch);

  // ---- 3. speed: 26 is fine, 34 outside the push / AISLE 5 windows is put back
  const L0 = [0, Y, 24], L1 = [0, Y, -18];
  { const from = P.slice(); P = (t) => lerp(from, L0, t / 1500); await run(1700); P = L0.slice(); await run(500); }
  A.got.length = 0;
  P = (t) => lerp(L0, L1, t / (42 / 25 * 1000)); await run(1600); P = lerp(L0, L1, 1600 / (42 / 25 * 1000));
  ok(!A.all('mech', (m) => m.k === 'fix').length, 'driving at 25 m/s: allowed');
  { const from = P.slice(); P = (t) => lerp(from, L0, t / 2000); await run(2200); P = L0.slice(); await run(600); }
  A.got.length = 0;
  P = (t) => lerp(L0, L1, t / (42 / 34 * 1000)); await run(1200);
  ok(A.all('mech', (m) => m.k === 'fix').length > 0, '34 m/s with no push or AISLE 5: put back');
  { const f = A.all('mech', (m) => m.k === 'fix').pop(); P = f ? f.p.slice() : L0.slice(); }
  await run(900);

  // ---- 4. rams: by the speed the server measured
  { const from = P.slice(); P = (t) => lerp(from, L0, t / 2000); await run(2200); P = L0.slice(); await run(600); }
  E3.got.length = 0;
  await run(1200, () => new Map([[E3, [[0, Y, 21.5]]]]), 0, { v: [0, 0, -30] });
  ok(!dmgOn(E3, 'trram').length, 'parked next to them claiming 30 m/s: no ram');
  { const tgt = [0, Y, 6]; P = (t) => lerp(L0, L1, t / (42 / 24 * 1000)); await run(1500, () => new Map([[E3, [tgt]]])); P = lerp(L0, L1, 1500 / (42 / 24 * 1000)); }
  const rm = dmgOn(E3, 'trram');
  ok(rm.length === 1 && rm[0].a >= 20 && rm[0].a <= 35, `drove through them at 24 m/s: one ram for ${rm[0] && rm[0].a} (6 + 15 x 1.4 = 27)`);
  await sleep(2600);

  // ---- 5. tin cans: rate, aim, a bonk, bounces
  { const from = P.slice(), to = [0, Y, 10]; P = (t) => lerp(from, to, t / 1200); await run(1400); P = to; }
  const cAim = aim([0.55, Y + 2.55, 10], [0, Y + 1.2, 3.5]), tgt5 = [0, Y, 3.5];
  E4.got.length = 0; A.got.length = 0;
  await run(500, () => new Map([[E4, [tgt5]]]), 0, { y: cAim.y, x: cAim.x });
  for (let i = 0; i < 8; i++) A.send({ t: 'mech', k: 'can', d: cAim.d });
  await run(600, () => new Map([[E4, [tgt5]]]), 0, { y: cAim.y, x: cAim.x });
  const cans = A.all('ps', (m) => m.k === 'trcan');
  ok(cans.length === 1, `8 cans at once: ${cans.length} thrown (3 a second)`);
  const cd5 = dmgOn(E4, 'trcan');
  ok(cd5.length === 1 && cd5[0].a === 22, 'a can at them: BONK for ' + (cd5[0] && cd5[0].a));
  ok(A.all('mech', (m) => m.k === 'trbonk').length === 1, 'everyone hears the bonk');
  A.got.length = 0;
  A.send({ t: 'mech', k: 'can', d: cAim.d.map((x) => -x) }); await run(400, () => new Map([[E4, [tgt5]]]), 0, { y: cAim.y, x: cAim.x });
  ok(!A.all('ps', (m) => m.k === 'trcan').length, 'a can thrown behind it (not where it looks): refused');
  for (const d of ['x', [NaN, 0, 1], [1e9, 0, 0], { 0: 1 }, null]) A.send({ t: 'mech', k: 'can', d });
  await run(400, () => new Map([[E4, [tgt5]]]), 0, { y: cAim.y, x: cAim.x });
  ok(!A.all('ps', (m) => m.k === 'trcan').length, 'garbage can directions: nothing');
  // one into the open floor: it bounces (a few times), then stops
  A.got.length = 0;
  { const fl = aim([0.55, Y + 2.55, 10], [10, Y, 0]); await run(400, undefined, 0, { y: fl.y, x: fl.x }); A.send({ t: 'mech', k: 'can', d: fl.d }); await run(3000, undefined, 0, { y: fl.y, x: fl.x }); }
  const c1 = A.all('ps', (m) => m.k === 'trcan').pop(), bs = c1 ? A.all('pu', (m) => m.id === c1.id && m.b) : [];
  ok(c1 && bs.length >= 2 && bs.length <= 3 && A.all('pd', (m) => m.id === c1.id).length === 1, `a can on the floor: bounced ${bs.length} times, then done`);

  // ---- 6. CLEAN UP AISLE 5
  A.got.length = 0;
  A.send({ t: 'mech', k: 'aisle', on: 1 }); await run(200);
  const notYet = A.all('mech', (m) => m.k === 'no' && /ultimate/.test(m.why)).length > 0 || !A.all('mech', (m) => m.k === 'traisle' && m.on === 1).length;
  for (let i = 0; i < 80; i++) { if (en().u >= 100) break; await run(150); }
  ok(en().u >= 100, 'the ult charged (JF_MECH_ULT) · ' + en().u);
  { const from = P.slice(); P = (t) => lerp(from, L0, t / 1800); await run(2000); P = L0.slice(); await run(500); }
  // an ally right in the path, an enemy in the path, one off to the side, one far away
  const sA = [0, Y, 14], sE1 = [0.5, Y, 8], sE2 = [7, Y, 4], sE3 = [0, Y, -4];
  const lay = () => new Map([[R, [sA, { y: 0 }]], [E1, [sE1]], [E2, [sE2]], [E3, [sE3]]]);
  await run(800, lay);
  for (const c of ALL) c.got.length = 0;
  A.send({ t: 'mech', k: 'aisle', on: 1 });
  const ai1 = await A.wait('mech', (m) => m.k === 'traisle' && m.on === 1, 600);
  ok(ai1 && ai1.ms === 6000, 'CLEAN UP AISLE 5: on for ' + (ai1 && ai1.ms) + ' ms');
  ok(notYet, '(and before the ult was full it was refused)');
  P = (t) => lerp(L0, [0, Y, -6], t / (30 / 32 * 1000)); await run(820, lay, MF.B); P = lerp(L0, [0, Y, -6], 820 / (30 / 32 * 1000));
  const sc = A.all('mech', (m) => m.k === 'trhold' && m.on === 1 && m.s === 'scoop');
  ok(sc.some((m) => m.v === E1.id) && sc.some((m) => m.v === E3.id), 'it runs into two enemies at 32 m/s: both SCOOPED');
  ok(!sc.some((m) => m.v === R.id), 'the ally it drove through: not scooped');
  ok(!sc.some((m) => m.v === E2.id), 'the enemy 7 m off to the side: not scooped');
  ok(!A.all('mech', (m) => m.k === 'fix').length, '32 m/s in AISLE 5: allowed');
  // the scooped send their own positions far away: the server keeps them in the basket
  const runAway = (t) => new Map([[E1, [[20, Y, 20]]], [E3, [[-6, Y, 20]]], [E2, [sE2]], [R, [sA]]]);
  P = [0, Y, -6];
  await run(600, runAway, MF.B);
  ok(near(SN.get(E1.id), P, 2) && near(SN.get(E3.id), P, 2), `scooped players sending their own positions: still in the basket · E1 ${SN.get(E1.id) && SN.get(E1.id).map((x) => x.toFixed(1))}`);
  { const Q = P.slice(); P = (t) => lerp(Q, [0, Y, 6], t / 1000); await run(1000, runAway, MF.B); P = [0, Y, 6]; }
  ok(near(SN.get(E1.id), P, 2.2), 'it drives off: they go with it');
  // they can't shoot (a control shot first, from the free one)
  E2.place(sE2, { w: 'sniper' }); E1.place([20, Y, 20], { w: 'sniper' }); await sleep(100);
  R.got.length = 0;
  E1.send({ t: 'hit', w: 'sniper', to: R.id, d: aim([P[0], Y + 2.6, P[2]], [sA[0], Y + 1, sA[2]]).d, n: 1, h: 0 });
  E2.send({ t: 'hit', w: 'sniper', to: R.id, d: aim([sE2[0], Y + 1.6, sE2[2]], [sA[0], Y + 1, sA[2]]).d, n: 1, h: 0 });
  await run(300, runAway, MF.B);
  const rd = R.all('dmg', (m) => m.to === R.id);
  ok(rd.filter((m) => m.from === E2.id).length === 1, 'the free enemy can shoot the ally (the control shot)');
  ok(!rd.filter((m) => m.from === E1.id).length, 'the scooped one can\'t shoot from the basket');
  E1.send({ t: 'mech', k: 'unride' }); E1.send({ t: 'mech', k: 'in' });
  await run(300, runAway, MF.B);
  ok(near(SN.get(E1.id), P, 2.2), 'scooped can\'t "unride" or climb out');
  ok(dmgOn(E1, 'trscoop').reduce((a, m) => a + m.a, 0) >= 8, 'and the basket hurts: 8/s · ' + dmgOn(E1, 'trscoop').reduce((a, m) => a + m.a, 0));
  // Q again: the dump
  for (const c of ALL) c.got.length = 0;
  A.send({ t: 'mech', k: 'aisle', on: 0 });
  await run(500, () => new Map([[E2, [sE2]], [R, [sA]]]));
  const off = A.all('mech', (m) => m.k === 'trhold' && m.on === 0 && m.why === 'dump');
  ok(off.length === 2, 'Q again: the basket tips, both dumped · ' + off.length);
  const dd = dmgOn(E1, 'trdump');
  ok(dd.length === 1 && dd[0].a === 35, 'dumped: 35 · ' + (dd[0] && dd[0].a));
  const kb = E1.all('kb').pop();
  ok(kb && kb.v[1] >= 12 && Math.hypot(kb.v[0], kb.v[2]) >= 18, `and flung forward and up · ${kb && kb.v.map((x) => x.toFixed(0))}`);
  ok(E1.all('mech', (m) => m.k === 'pos').length === 1, 'the dumped client gets put where the basket let go of it');
  ok(!(en().au > 0), 'AISLE 5 is over');
  await sleep(2600);
  // the ult's own hits didn't charge the next one; then max 3 and the timer
  for (let i = 0; i < 80; i++) { if (en().u >= 100) break; await run(150); }
  { const from = P.slice(); P = (t) => lerp(from, L0, t / 1800); await run(2000); P = L0.slice(); await run(400); }
  const lay4 = () => new Map([[E1, [[0, Y, 16]]], [E2, [[0.4, Y, 10]]], [E3, [[-0.4, Y, 4]]], [E4, [[0, Y, -2]]], [R, [[26, Y, -16]]]]);
  await run(800, lay4);
  for (const c of ALL) c.got.length = 0;
  A.send({ t: 'mech', k: 'aisle', on: 1 });
  P = (t) => lerp(L0, [0, Y, -12], t / (36 / 32 * 1000)); await run(1200, lay4, MF.B); P = [0, Y, -12];
  const sc4 = A.all('mech', (m) => m.k === 'trhold' && m.on === 1 && m.s === 'scoop');
  ok(sc4.length === 3 && en().bk === 3, `four enemies in a row: only ${sc4.length} fit in the basket (bk ${en().bk})`);
  ok(!sc4.some((m) => m.v === E4.id) && dmgOn(E4, 'trram').length === 1, 'the fourth gets rammed instead');
  await run(5200, () => new Map([[R, [[26, Y, -16]]]]), MF.B);
  const off4 = A.all('mech', (m) => m.k === 'trhold' && m.on === 0 && m.why === 'dump');
  ok(A.all('mech', (m) => m.k === 'traisle' && m.on === 0 && m.why === 'time').length === 1 && off4.length === 3, 'six seconds later: time\'s up, all three dumped');
  A.got.length = 0;
  P = (t) => lerp([0, Y, -12], [0, Y, 20], t / 1100); await run(1000);
  ok(A.all('mech', (m) => m.k === 'fix').length > 0, 'after AISLE 5: 30 m/s is put back again');
  { const f = A.all('mech', (m) => m.k === 'fix').pop(); P = f ? f.p.slice() : [0, Y, 0]; }
  await sleep(2600);
  await run(900);

  // ---- 7. the pound coin lock: allies ride in the child seat
  const S0 = P.slice();
  for (const c of ALL) c.got.length = 0;
  E1.send({ t: 'mech', k: 'ride', to: A.id }); await run(300, () => new Map([[E1, [[S0[0] + 2.5, Y, S0[2]]]]]));
  ok((E1.take('mech', (m) => m.k === 'no') || {}).why === "that's not your trolley", 'an enemy tries to ride: refused');
  R.send({ t: 'mech', k: 'ride', to: A.id }); await run(300, () => new Map([[R, [[S0[0] + 12, Y, S0[2]]]]]));
  ok((R.take('mech', (m) => m.k === 'no') || {}).why === 'get closer', 'an ally 12 m away: get closer');
  for (const to of ['x', { a: 1 }, 1e12, -1, null, R.id]) R.send({ t: 'mech', k: 'ride', to });
  await run(400, () => new Map([[R, [[S0[0] + 3.5, Y, S0[2]]]]]));
  ok(!A.all('mech', (m) => m.k === 'trhold' && m.on === 1).length, 'garbage ride targets (and riding themselves): nothing');
  R.got.length = 0;
  R.send({ t: 'mech', k: 'ride', to: A.id }); await run(300, () => new Map([[R, [[S0[0] + 3.5, Y, S0[2]]]], [R2, [[S0[0] - 3.5, Y, S0[2]]]]]));
  const rideOn = A.all('mech', (m) => m.k === 'trhold' && m.on === 1 && m.s === 'ride' && m.v === R.id);
  ok(rideOn.length === 1, 'an ally 3.5 m away presses F: rides in the child seat');
  R2.send({ t: 'mech', k: 'ride', to: A.id }); await run(400, () => new Map([[R2, [[S0[0] - 3.5, Y, S0[2]]]], [R, [[30, Y, 30]]]]));
  ok((R2.take('mech', (m) => m.k === 'no') || {}).why === 'the seat is taken', 'a second ally: the seat is taken');
  ok(near(SN.get(R.id), S0, 2), 'the rider sending positions 30 m away: still in the seat');
  { const Q = S0.slice(); P = (t) => lerp(Q, [Q[0], Y, Q[2] - 12], t / 800); await run(800, () => new Map([[R, [[30, Y, 30]]]])); P = [Q[0], Y, Q[2] - 12]; }
  ok(near(SN.get(R.id), P, 2.2), 'the trolley drives off: the rider comes with it');
  // a gunner: their gun still works
  E2.got.length = 0;
  { const eAt = [P[0] + 10, Y, P[2]]; R.place([30, Y, 30], { w: 'sniper' }); await run(200, () => new Map([[R, [[30, Y, 30], { w: 'sniper' }]], [E2, [eAt]]]));
    R.send({ t: 'hit', w: 'sniper', to: E2.id, d: aim([P[0], Y + 2.6, P[2] + 0.5], [eAt[0], Y + 1, eAt[2]]).d, n: 1, h: 0 });
    await run(300, () => new Map([[R, [[30, Y, 30], { w: 'sniper' }]], [E2, [eAt]]])); }
  ok(E2.all('dmg', (m) => m.to === E2.id).length === 1, 'the rider shoots from the seat (a gunner)');
  R.send({ t: 'deploy', r: 'mechdrop', at: [P[0] + 6, Y, P[2]] }); R.send({ t: 'mech', k: 'in' });
  await run(300, () => new Map([[R, [[30, Y, 30]]]]));
  ok(!R.all('mech', (m) => m.k === 'call').length, 'but no streaks from the seat');
  // hop out
  R.got.length = 0; A.got.length = 0;
  R.send({ t: 'mech', k: 'unride' }); await run(300, () => new Map([[R, [[30, Y, 30]]]]));
  const hop = A.all('mech', (m) => m.k === 'trhold' && m.on === 0 && m.v === R.id);
  const rpos = R.all('mech', (m) => m.k === 'pos').pop();
  ok(hop.length === 1 && hop[0].why === 'hop' && rpos && rpos.v[1] > 4 && near(rpos.p, P, 4), 'F / jump: the rider hops out over the side');
  R2.send({ t: 'mech', k: 'ride', to: A.id }); await run(400, () => new Map([[R2, [[P[0] - 3.5, Y, P[2]]]]]));
  ok(A.all('mech', (m) => m.k === 'trhold' && m.on === 1 && m.v === R2.id).length === 1, 'now the second ally can ride');

  // ---- 8. cleanup: every path lets go
  // (a) the rider disconnects
  A.got.length = 0;
  R2.ws.close(); await run(800);
  ok(A.all('mech', (m) => m.k === 'trhold' && m.on === 0 && m.v === R2.id).length === 1, 'the rider disconnects: the seat is let go');
  R.send({ t: 'mech', k: 'ride', to: A.id }); await run(300, () => new Map([[R, [[P[0] + 3, Y, P[2]]]]]));
  ok(A.all('mech', (m) => m.k === 'trhold' && m.on === 1 && m.v === R.id).length === 1, '(and it\'s free again)');
  // (b) the pilot hops out: the rider's let go
  A.got.length = 0;
  A.send({ t: 'mech', k: 'out' }); await run(400, () => new Map([[A, [[P[0] + 2.2, Y, P[2]]]]]));
  ok(A.all('mech', (m) => m.k === 'trhold' && m.on === 0 && m.v === R.id).length === 1, 'the pilot hops out: the rider is let go');
  await run(1300, () => new Map([[A, [[P[0] + 2.2, Y, P[2]]]], [R, [[P[0] + 2, Y, P[2] + 3]]]]));
  A.send({ t: 'mech', k: 'in' }); await run(400);
  ok(A.all('mech', (m) => m.k === 'in' && m.id === A.id).length === 1, 'and climbs back in');
  // (c) a scooped player dies in the basket; (d) a scooped player disconnects; (e) the trolley breaks with a rider in
  for (let i = 0; i < 80; i++) { if (en().u >= 100) break; await run(150); }
  { const from = P.slice(); P = (t) => lerp(from, L0, t / 1800); await run(2000); P = L0.slice(); await run(400); }
  const lay3 = () => new Map([[E1, [[0, Y, 14]]], [E3, [[0, Y, 6]]], [R, [[3.5, Y, 24]]]]);
  await run(1200, lay3);
  for (const c of ALL) c.got.length = 0;
  R.send({ t: 'mech', k: 'ride', to: A.id });
  A.send({ t: 'mech', k: 'aisle', on: 1 });
  P = (t) => lerp(L0, [0, Y, 2], t / (22 / 30 * 1000)); await run(800, lay3, MF.B); P = [0, Y, 2];
  const sc3 = A.all('mech', (m) => m.k === 'trhold' && m.on === 1);
  ok(sc3.filter((m) => m.s === 'scoop').length === 2 && sc3.filter((m) => m.s === 'ride').length === 1, 'a rider in the seat and two scooped in the basket');
  E3.ws.close(); await run(600, undefined, MF.B);
  ok(A.all('mech', (m) => m.k === 'trhold' && m.on === 0 && m.v === E3.id).length === 1 && en().bk === 1, 'a scooped player disconnects: let go (bk ' + en().bk + ')');
  // E1 dies in the basket: the ally (riding!) shoots them
  for (let i = 0; i < 6 && E1.alive; i++) { R.place([30, Y, 30], { w: 'sniper' }); await sleep(60); R.send({ t: 'hit', w: 'sniper', to: E1.id, d: [0, -0.2, -1], n: 1, h: 1 }); await run(1300, undefined, MF.B); }
  ok(A.all('mech', (m) => m.k === 'trhold' && m.on === 0 && m.v === E1.id && m.why === 'dead').length === 1, 'a scooped player dies in the basket: let go');
  // the trolley breaks: shot to bits by a foe
  for (const c of ALL) c.got.length = 0;
  for (let i = 0; i < 12 && !A.all('mech', (m) => m.k === 'down').length; i++) {
    E2.place([P[0] + 12, Y, P[2]], { w: 'sniper' }); await sleep(60);
    E2.send({ t: 'hit', w: 'sniper', to: A.id, d: aim([P[0] + 12, Y + 1.6, P[2]], [P[0], Y + 2, P[2]]).d, n: 1, h: 0 });
    await run(1300, () => new Map([[E2, [[P[0] + 12, Y, P[2]], { w: 'sniper' }]]]), MF.B);
  }
  ok(A.all('mech', (m) => m.k === 'down').length === 1, 'the trolley breaks');
  const brk = A.all('mech', (m) => m.k === 'trhold' && m.on === 0 && m.v === R.id);
  const rp = R.all('mech', (m) => m.k === 'pos').pop();
  ok(brk.length === 1 && brk[0].why === 'break' && rp && rp.v[1] >= 10, 'the rider is flung out of the wreck');
  // (f) a map change mid-scoop: a fresh mech, a fresh scoop, then cfg
  await sleep(3500);
  A.got.length = 0; A.send({ t: 'deploy', r: 'mechdrop', at: [0, Y, 16], mf: 'trolley' });
  const P2 = [0, Y, 21]; P = P2;
  await run(3200, () => new Map([[A, [P2, { y: look0.y, x: look0.x }]]]));
  A.send({ t: 'mech', k: 'in' }); P = [0, Y, 16]; await run(600);
  for (let i = 0; i < 80; i++) { if (en().u >= 100) break; await run(150); }
  { const from = P.slice(); P = (t) => lerp(from, L0, t / 1500); await run(1700); P = L0.slice(); await run(400); }
  const lay5 = () => new Map([[E4, [[0, Y, 12]]]]);
  await run(800, lay5);
  for (const c of ALL) c.got.length = 0;
  A.send({ t: 'mech', k: 'aisle', on: 1 });
  P = (t) => lerp(L0, [0, Y, 4], t / (20 / 30 * 1000)); await run(800, lay5, MF.B); P = [0, Y, 4];
  ok(A.all('mech', (m) => m.k === 'trhold' && m.on === 1 && m.v === E4.id).length === 1, 'scooped one more');
  A.send({ t: 'cfg', map: 'crate' }); await run(1200);
  ok(A.all('mech', (m) => m.k === 'trhold' && m.on === 0 && m.v === E4.id).length >= 1, 'the map changes: let go');
  // garbage + a flood, then the pilot disconnects
  for (const m of [{ k: 'aisle', on: '1' }, { k: 'aisle', on: { x: 1 } }, { k: 'push', x: [[[[1]]]] }, { k: 'can', d: 'down' }, { k: 'ride', to: [1] }, { k: 'unride', to: 5 }, { k: 'x'.repeat(40) }, { k: null }]) { A.send({ t: 'mech', ...m }); E4.send({ t: 'mech', ...m }); }
  for (let i = 0; i < 200; i++) { A.send({ t: 'mech', k: 'can', d: [0, 0, -1] }); E4.send({ t: 'mech', k: 'ride', to: A.id }); }
  await run(500);
  ok(srv.exitCode === null, 'garbage + a flood: the server is fine');
  ok(!/TypeError|ReferenceError|uncaught/i.test(srvErr), 'no server errors' + (srvErr ? ': ' + srvErr.slice(0, 600) : ''));
  console.log(fails ? `\n${fails} FAILED` : '\nall passed');
  end(fails ? 1 : 0);
})().catch((e) => { console.log('crash', e); if (srvRef) srvRef.kill(); process.exit(1); });
