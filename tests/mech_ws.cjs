// mech drop over plain ws: the marker's checks, the drop + shockwave + squash, climbing in (owner only, close), the
// armour taking hits (your HP untouched), cockpit headshots, every move's damage + cooldown + energy, the speed cap,
// eject at 0 armour (fling + blast with credit), hopping out and back in, dying inside, disconnect cleanup, garbage.
// starts its own server: node tests/mech_ws.cjs [port]   (JF_TRAIN_STREAKS: your 3 streaks always ready; JF_MECH_HP: weaker mechs)
const WS = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const port = Number(process.argv[2]) || 3147;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
const HP = 0.3; // JF_MECH_HP: paper plane 270, night shift 450
const EYE_PP = 4.4 * 1.35; // the paper plane's cockpit eye (shared/mech.js: x MECH.scale)
const MF = { MECH: 1 << 22, A: 1 << 23, B: 1 << 30, C: 1 << 31 };
let srvRef = null, srv2Ref = null;
const Y = 0.03, X0 = 42, Z0 = 12; // warehouse: the flat open yard round [42, 0, 12]. the test works in coordinates round it
const sh = (a, k) => (Array.isArray(a) && a.length === 3 && a.every(Number.isFinite) ? [a[0] + X0 * k, a[1], a[2] + Z0 * k] : a);

function client(name, extra = {}, prt = port) {
  const ws = new WS(`ws://localhost:${prt}/ws`), c = { ws, got: [], id: 0, q: 0, hp: 100, alive: true, name };
  ws.on('message', (d) => {
    const m = JSON.parse(d);
    if ((m.t === 'mech' || m.t === 'welcome' || m.t === 'spawn') && m.p) m.p = sh(m.p, -1);
    if (m.t === 'welcome') { c.id = m.id; c.q = m.q; }
    if (m.t === 'spawn') { c.q = m.q; c.spawnT = Date.now(); }
    if (m.t === 'sn') { c.sn = m.p; const r = m.p.find((x) => x[0] === c.id); if (r) { c.hp = r[10]; c.alive = !!r[11]; c.f = r[13]; c.spos = [r[1] - X0, r[2], r[3] - Z0]; } return; }
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
// look from a to b (yaw, pitch the game's way)
const aim = (a, b) => { const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], h = Math.hypot(d[0], d[2]); return { y: Math.atan2(-d[0], -d[2]), x: Math.atan2(d[1], h), d: d.map((v) => v / Math.hypot(...d)) }; };
// keep sending snapshots for everyone in `who` (each [client, pos, opts]) for ms
const hold = async (ms, who) => { for (let t = 0; t < ms; t += 60) { for (const [c, p, o] of who) c.place(typeof p === 'function' ? p(t) : p, o); await sleep(60); } };
const bhp = (c, id) => { const l = c.all('bhp', (m) => m.id === id); return l.length ? l[l.length - 1].hp : null; };

(async () => {
  const srv = srvRef = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(port), JF_TRAIN_STREAKS: '1', JF_MECH_HP: String(HP) }, stdio: ['ignore', 'pipe', 'pipe'] });
  let srvErr = ''; srv.stderr.on('data', (d) => { srvErr += d; }); srv.stdout.on('data', (d) => { if (/Error|uncaught/i.test(String(d))) srvErr += d; });
  const end = (code) => { srv.kill(); process.exit(code); };
  for (let i = 0; i < 60; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }
  const A = await client('pilot', { mf: 'paperplane' });
  A.send({ t: 'cfg', map: 'warehouse' }); await sleep(900);
  const B = await client('victim'), C = await client('bystander');
  await sleep(1500); // spawn protection + the tray fills (JF_TRAIN_STREAKS)
  const pa = [0, Y, 9], pb = [0, Y, -8], pc = [4, Y, -8];
  const look = aim([0, Y + 1.6, 9], [0, Y, -8]);
  const place3 = (ms, oa = { y: look.y, x: look.x }) => hold(ms, [[A, pa, oa], [B, pb], [C, pc]]);
  await place3(400);

  // ---- 1. the marker: too far, not in sight
  A.got.length = 0;
  A.send({ t: 'deploy', r: 'mechdrop', at: [0, Y, -120], mf: 'paperplane' }); await place3(300);
  ok((A.take('mech', (m) => m.k === 'no') || {}).why === 'too far (60 m max)' && A.take('streak', (m) => m.earned === 'mechdrop'), 'marker past 60 m: refused, back in the tray');
  A.send({ t: 'deploy', r: 'mechdrop', at: [0, Y - 6, -5], mf: 'paperplane' }); await place3(300);
  const ns = A.take('mech', (m) => m.k === 'no');
  ok(ns && ns.why === "can't see there", 'marker through the roof (no line of sight): refused · ' + (ns && ns.why));
  ok(!A.all('mech', (m) => m.k === 'call').length, 'no mech called for either');

  // ---- 2. the drop: B stands on the marker (squashed), C 4 m off (shockwave)
  A.send({ t: 'deploy', r: 'mechdrop', at: [0, Y, -8], mf: 'paperplane' });
  const call = await A.wait('mech', (m) => m.k === 'call', 1500);
  ok(call && call.f === 'paperplane' && Math.abs(call.p[1] - Y) < 0.1, 'marker placed on the floor under the crosshair');
  await place3(2900);
  const land = A.take('mech', (m) => m.k === 'land');
  ok(land && land.id === call.id, 'it lands after 2.5 s');
  ok(A.take('mech', (m) => m.k === 'squash' && m.to === B.id) && !B.alive, 'B was on the marker: SQUASHED');
  const cd = C.take('dmg', (m) => m.to === C.id && m.w === 'mechdrop'), ckb = C.take('kb');
  ok(cd && cd.a > 20 && cd.a < 60 && ckb && ckb.v[1] > 5, `C 4 m away: shockwave ${cd && cd.a} damage and knocked up ${ckb && ckb.v[1]}`);
  const mp = land.p;

  // ---- 3. climbing in: not B's, A too far, then A
  await sleep(2700); await hold(1400, [[A, pa], [B, [mp[0] + 2, Y, mp[2]]], [C, pc]]); // B respawned: put them next to it
  B.got.length = 0; B.send({ t: 'mech', k: 'in' }); await sleep(250);
  ok((B.take('mech', (m) => m.k === 'no') || {}).why === 'no mech of yours here' && !B.all('mech', (m) => m.k === 'in').length, 'someone else F on it: refused');
  A.send({ t: 'mech', k: 'in' }); await sleep(250);
  ok((A.take('mech', (m) => m.k === 'no') || {}).why === 'get closer', 'owner 17 m away: refused');
  const pin = [mp[0] + 1.5, Y, mp[2] + 1];
  await hold(300, [[A, pin]]);
  A.got.length = 0; A.send({ t: 'mech', k: 'in' });
  const ein = await A.wait('mech', (m) => m.k === 'in' && m.id === A.id, 1000);
  ok(ein && ein.f === 'paperplane' && ein.max === Math.round(900 * HP), 'owner next to it: climbs in · armour ' + (ein && ein.hp));
  let P = mp.slice(); // the pilot's position from here
  const pb2 = [P[0], Y, P[2] - 12], pc2 = [P[0] + 30, Y, P[2] + 25];
  const lookB = () => aim([P[0], P[1] + EYE_PP, P[2]], [pb2[0], Y + 1, pb2[2]]);
  const fly = (ms, f = 0, path) => hold(ms, [[A, path || (() => P), { ...lookB(), f: MF.MECH | f }], [B, pb2], [C, pc2]]);
  await fly(800);
  ok(A.f & MF.MECH, 'the snapshot carries the MECH flag');

  // ---- 4. the armour takes hits, not your HP; the cockpit is a 1.5x headshot
  const hit = (h) => B.send({ t: 'hit', w: 'ar', to: A.id, d: aim(pb2, P).d, n: 1, h });
  const a0 = bhp(A, A.id) ?? ein.hp; hit(0); await fly(350);
  const a1 = bhp(A, A.id); hit(1); await fly(350);
  const a2 = bhp(A, A.id);
  ok(a0 - a1 === 11 && A.hp === 100, `body hit: armour ${a0} -> ${a1}, pilot HP still ${A.hp}`);
  ok(Math.abs((a1 - a2) - 16.5) <= 0.6, `cockpit hit: ${a1 - a2} (11 x 1.5)`);

  // ---- 5. PAPER PLANE moves
  // cannons: 14 a shot on B (aimed), a shot way off your view refused
  B.got.length = 0;
  A.send({ t: 'mech', k: 'gun', d: lookB().d }); await fly(250);
  const gd = B.take('dmg', (m) => m.to === B.id && m.w === 'mechgun');
  ok(gd && gd.a === 14, 'twin cannons: 14 on B');
  A.send({ t: 'mech', k: 'gun', d: [0, 1, 0] }); await fly(250);
  ok(!B.take('dmg', (m) => m.w === 'mechgun'), 'a shot straight up (not where you look): refused');
  // crane drone: pecks B a few times, then a cooldown
  A.send({ t: 'mech', k: 'crane', to: B.id }); await fly(2600);
  const pecks = B.all('dmg', (m) => m.to === B.id && m.w === 'mechcrane');
  ok(A.all('mech', (m) => m.k === 'crane').length === 1 && pecks.length >= 3 && pecks.every((m) => m.a === 6), `crane drone: ${pecks.length} pecks of 6`);
  A.send({ t: 'mech', k: 'crane', to: B.id }); await fly(300);
  ok(A.all('mech', (m) => m.k === 'crane').length === 1, 'crane again right away: cooldown');
  // swarm: twelve missiles, B takes some, then a cooldown
  await sleep(3000); // (B's back to full: the crane's 24 + cannons left them alive)
  A.got.length = 0; B.got.length = 0;
  A.send({ t: 'mech', k: 'swarm', d: lookB().d }); await fly(3200);
  const mis = A.all('ps', (m) => m.k === 'mechmissile').length, md = B.all('dmg', (m) => m.to === B.id && m.w === 'mechmissile');
  ok(mis === 12 && md.length >= 1, `missile swarm: ${mis} missiles, ${md.length} hit B`);
  A.send({ t: 'mech', k: 'swarm', d: lookB().d }); await fly(300);
  ok(A.all('ps', (m) => m.k === 'mechmissile').length === 12, 'swarm again: cooldown');
  await sleep(2600);
  // lunge: rocket through B: 30, and it repairs half of what it dealt
  B.got.length = 0;
  const arm0 = bhp(A, A.id);
  A.send({ t: 'mech', k: 'lunge', to: B.id, d: lookB().d });
  const t0 = Date.now(), from = P.slice(), to = [pb2[0], Y, pb2[2] - 3];
  await fly(500, MF.C, () => { const k = Math.min(1, (Date.now() - t0) / 480); return [from[0] + (to[0] - from[0]) * k, Y, from[2] + (to[2] - from[2]) * k]; });
  P = to.slice();
  const ld = B.take('dmg', (m) => m.to === B.id && m.w === 'mechlunge'), heal = A.take('mech', (m) => m.k === 'heal');
  ok(ld && ld.a === 30, 'boost lunge: 30 on B');
  ok(heal && heal.a === 15 && bhp(A, A.id) > arm0, `lunge repairs the mech: +${heal && heal.a} armour`);
  // energy: lunges cost 25; four in a row empties it, the fifth is refused
  await sleep(200); // (after the first lunge's 0.65 s window, before the 0.8 s refill delay)
  for (let i = 0; i < 3; i++) { A.send({ t: 'mech', k: 'lunge', d: [0, 0, 1] }); await sleep(680); }
  A.got.length = 0; A.send({ t: 'mech', k: 'lunge', d: [0, 0, 1] }); await fly(200);
  ok((A.take('mech', (m) => m.k === 'no') || {}).why === 'no energy' && !A.take('mech', (m) => m.k === 'lunge'), 'fifth lunge with no energy: refused');
  // jet: fly through B for 60 and a fling, then a cooldown
  await sleep(2400); // B's spawn protection etc.
  const bpos = [P[0], Y, P[2] + 14];
  await hold(300, [[A, () => P, { f: MF.MECH }], [B, bpos], [C, pc2]]);
  B.got.length = 0; A.got.length = 0;
  A.send({ t: 'mech', k: 'jet', on: 1 }); const j0 = Date.now(), jf = P.slice(), jt = [P[0], Y + 1, P[2] + 22];
  await hold(900, [[A, () => { const k = Math.min(1, (Date.now() - j0) / 600); return [jf[0], jf[1] + k, jf[2] + (jt[2] - jf[2]) * k]; }, { f: MF.MECH | MF.B, v: [0, 0, 40] }], [B, bpos], [C, pc2]]);
  P = jt.slice(); P[1] = Y;
  const jr = B.take('dmg', (m) => m.to === B.id && m.w === 'mechjet');
  ok(A.take('mech', (m) => m.k === 'jet' && m.on === 1) && jr && jr.a === 60 && B.take('kb', (m) => Math.hypot(m.v[0], m.v[2]) > 15), 'jet ram: 60 and B goes flying');
  A.send({ t: 'mech', k: 'jet', on: 0 }); await fly(200);
  A.send({ t: 'mech', k: 'jet', on: 1 }); await fly(200);
  ok(!A.take('mech', (m) => m.k === 'jet' && m.on === 1), 'jet again: cooldown');

  // ---- 6. speed cap: a 40 m jump in one snapshot is put back
  await fly(400);
  A.got.length = 0;
  A.place([P[0] + 40, Y, P[2]], { f: MF.MECH }); await sleep(200);
  const fix = A.take('mech', (m) => m.k === 'fix');
  ok(fix && Math.abs(fix.p[0] - P[0]) < 1, 'teleporting 40 m: corrected back to ' + (fix && fix.p.join(',')));
  await sleep(500); await fly(400);

  // ---- 7. hop out (F), the mech waits, back in with the same armour
  const arm1 = bhp(A, A.id);
  A.got.length = 0; A.send({ t: 'mech', k: 'out' });
  const out = await A.wait('mech', (m) => m.k === 'out' && m.id === A.id, 800);
  ok(out && out.why === 'hop' && !A.take('mech', (m) => m.k === 'down'), 'F inside: hops out, no explosion');
  const pos = await A.wait('mech', (m) => m.k === 'pos', 500);
  await hold(1100, [[A, pos ? pos.p : P]]); // (a second to climb down before you can climb back in)
  A.send({ t: 'mech', k: 'in' });
  const in2 = await A.wait('mech', (m) => m.k === 'in', 800);
  ok(in2 && Math.abs(in2.hp - arm1) <= 1, `back in within 10 s, same armour (${arm1} -> ${in2 && in2.hp})`);
  P = in2 ? in2.p : P;

  // ---- 8. eject at 0 armour: flung out, the mech blows up, C next to it hurt, credit to B
  const near = [P[0] + 2.5, Y, P[2]];
  await hold(1500, [[A, () => P, { f: MF.MECH }], [B, pb2, { w: 'ar' }], [C, near]]);
  A.got.length = 0; C.got.length = 0; B.got.length = 0;
  let down = null;
  for (let i = 0; i < 80 && !down; i++) { B.send({ t: 'hit', w: 'ar', to: A.id, d: aim(pb2, P).d, n: 1, h: 1 }); await hold(110, [[A, () => P, { f: MF.MECH }], [B, pb2], [C, near]]); down = A.all('mech', (m) => m.k === 'down')[0]; }
  ok(down && down.id === A.id && down.by === B.id, 'armour at 0: MECH DOWN, credited to B');
  const ej = A.take('mech', (m) => m.k === 'pos');
  ok(ej && ej.v[1] > 10 && ej.p[1] > P[1] + 2, 'EJECT! EJECT!: flung up out of the cockpit');
  await sleep(300);
  const blast = C.take('dmg', (m) => m.to === C.id && m.w === 'mechboom');
  ok(blast && blast.from === B.id && blast.a >= 20, `the blast hits C for ${blast && blast.a}, credited to B`);
  ok(A.hp === 100 && A.alive, 'the pilot walks away at full HP');

  // ---- 9. NIGHT SHIFT: sword combo + overtime, shield + bash, triple shift + energy, slam + cooldown, stomp
  await sleep(1500);
  const K = [0, Y, 8];
  await hold(1600, [[A, K, { y: 0 }], [B, [0, Y, -6]], [C, [8, Y, 10]]]);
  A.got.length = 0;
  A.send({ t: 'deploy', r: 'mechdrop', at: [0, Y, 2], mf: 'nightshift' });
  const call2 = await A.wait('mech', (m) => m.k === 'call', 1500);
  ok(call2 && call2.f === 'nightshift', 'second call: the frame from your pick (NIGHT SHIFT)');
  await hold(2900, [[A, K], [B, [0, Y, -6]], [C, [8, Y, 10]]]);
  await hold(300, [[A, [0, Y, 4]]]);
  A.send({ t: 'mech', k: 'in' });
  const in3 = await A.wait('mech', (m) => m.k === 'in', 800);
  ok(in3 && in3.f === 'nightshift', 'in the knight');
  P = in3.p;
  const pbS = [P[0], Y, P[2] - 4]; // 4 m in front (yaw 0 faces -z)
  const knight = (ms, f = 0, bp = pbS, ap) => hold(ms, [[A, ap || (() => P), { y: 0, x: 0, f: MF.MECH | f }], [B, bp], [C, [8, Y, 10]]]);
  await knight(1500);
  if (B.hp < 100) { B.send({ t: 'tbag' }); await sleep(2700); await knight(1400); } // a fresh B (a t-bag too hard: it explodes them)
  B.got.length = 0;
  for (let i = 0; i < 3; i++) { A.send({ t: 'mech', k: 'swing' }); await knight(i < 2 ? 450 : 700); }
  const sw = B.all('dmg', (m) => m.to === B.id && m.w === 'mechsword').map((m) => m.a);
  ok(sw.join(',') === '40,40,70', 'sword combo: ' + sw.join(' / '));
  const marks = A.all('mech', (m) => m.k === 'mark' && m.to === B.id).map((m) => m.n);
  ok(marks.join(',') === '1,2' && !B.alive, 'overtime marks stamped: ' + marks.join(',') + ' (the third swing killed them)');
  await sleep(2600); await knight(1400); // B died to 150? (40+40+70 = 150: yes) -> back, protected
  B.got.length = 0; A.got.length = 0;
  // four marks: only something tough lives that long, so B calls a mech in 5 m in front and climbs in. the 4th mark
  // CLOCKS THEM OUT (a 1 s stun), then a few seconds where marks don't build
  const bm = [P[0], Y, P[2] - 5];
  await knight(300, 0, bm);
  B.send({ t: 'deploy', r: 'mechdrop', at: bm, mf: 'paperplane' });
  await knight(3000, 0, bm);
  B.send({ t: 'mech', k: 'in' }); await knight(600, 0, bm);
  ok(B.take('mech', (m) => m.k === 'in' && m.id === B.id), 'B is in a mech of their own (two mechs at once)');
  A.got.length = 0; B.got.length = 0;
  for (let i = 0; i < 4; i++) { A.send({ t: 'mech', k: 'swing' }); await knight(i === 2 ? 1500 : 450, 0, bm); }
  const marks2 = A.all('mech', (m) => m.k === 'mark' && m.to === B.id).map((m) => m.n);
  const clock = A.take('mech', (m) => m.k === 'clock' && m.to === B.id), stun = B.take('stun');
  ok(marks2.join(',') === '1,2,3' && clock && stun && stun.dur >= 0.9, `marks ${marks2.join(',')}, then the 4th: CLOCKED OUT (stunned ${stun && stun.dur} s)`);
  B.send({ t: 'mech', k: 'gun', d: [0, 0, 1] }); await knight(200, 0, bm);
  ok(!A.take('mech', (m) => m.k === 'gun'), 'clocked out: their mech can\'t shoot');
  A.got.length = 0; A.send({ t: 'mech', k: 'swing' }); await knight(500, 0, bm);
  ok(!A.take('mech', (m) => m.k === 'mark' || m.k === 'clock'), 'right after: immune, no new marks (no stun lock)');
  await sleep(1700); B.send({ t: 'mech', k: 'out' }); await knight(600, 0, bm); // (not right after a hit: no hopping out under fire)
  ok(B.take('mech', (m) => m.k === 'out' && m.id === B.id), 'B hops out of theirs once nobody is hitting it');
  await sleep(2600); await knight(1400);
  // shield: B shoots from the front, 85% blocked; then the bash
  await knight(300, MF.A);
  const s0 = bhp(A, A.id) ?? in3.hp;
  A.got.length = 0;
  B.send({ t: 'hit', w: 'ar', to: A.id, d: [0, 0, 1], n: 1, h: 0 }); await knight(300, MF.A);
  const s1 = bhp(A, A.id), blk = A.take('mech', (m) => m.k === 'blk');
  ok(blk && Math.abs((s0 - s1) - 11 * 0.15) <= 1, `tower shield: an 11 hit took ${(s0 - s1).toFixed(2)} (85% blocked; the pool is sent rounded)`);
  B.got.length = 0; A.send({ t: 'mech', k: 'bash' }); await knight(300);
  ok(B.take('dmg', (m) => m.to === B.id && m.w === 'mechbash' && m.a === 30), 'shield bash right after a block: 30');
  A.send({ t: 'mech', k: 'bash' }); await knight(300);
  ok(!B.take('dmg', (m) => m.w === 'mechbash'), 'bash without a fresh block: nothing');
  // triple shift: 35 energy, twice fine, the third refused
  await sleep(1500);
  A.got.length = 0; B.got.length = 0;
  const tf = P.slice(), tt = [P[0], Y, P[2] - 8];
  A.send({ t: 'mech', k: 'triple' }); const tr0 = Date.now();
  await knight(1200, MF.C, pbS, () => { const k = Math.min(1, (Date.now() - tr0) / 800); return [tf[0], Y, tf[2] + (tt[2] - tf[2]) * k]; });
  P = tt.slice();
  const tr = B.all('dmg', (m) => m.to === B.id && m.w === 'mechtriple');
  ok(A.take('mech', (m) => m.k === 'triple') && tr.length >= 1 && tr[0].a === 25, `triple shift cuts B (${tr.length} cut${tr.length > 1 ? 's' : ''} of 25)`);
  // back to back (each one's 1.1 s), the refill can't keep up: one of the next three is refused
  let refused = 0;
  for (let i = 0; i < 3; i++) { A.got.length = 0; A.send({ t: 'mech', k: 'triple' }); await knight(1120, MF.C); if (A.all('mech', (m) => m.k === 'no' && m.why === 'no energy').length) refused++; }
  ok(refused >= 1, `triple shifts back to back: ${refused} refused for no energy`);
  // slam: up, down, a shockwave on B 3 m away; then a cooldown
  await sleep(2600);
  const pbq = [P[0] + 3, Y, P[2]];
  await knight(1500, 0, pbq);
  B.got.length = 0; A.got.length = 0;
  A.send({ t: 'mech', k: 'slam' }); A.wait('mech', (m) => m.k === 'slam', 300); const sl0 = Date.now();
  await knight(800, MF.B, pbq, () => { const k = (Date.now() - sl0) / 800; return [P[0], Y + Math.sin(Math.min(1, k) * Math.PI) * 6, P[2]]; });
  A.send({ t: 'mech', k: 'slamland', p: P }); await knight(300, 0, pbq);
  const sq = B.take('dmg', (m) => m.to === B.id && m.w === 'mechslam');
  ok(A.take('mech', (m) => m.k === 'quake') && sq && sq.a > 60, `ground slam: ${sq && sq.a} on B 3 m away`);
  A.send({ t: 'mech', k: 'slam' }); await knight(300, 0, pbq);
  ok(!A.take('mech', (m) => m.k === 'slam'), 'slam again: cooldown');
  // stomp: come down on B from a jump
  await sleep(2600);
  const under = [P[0], Y, P[2]];
  await knight(1500, 0, under, () => [P[0] + 3, Y, P[2]]);
  B.got.length = 0; A.got.length = 0;
  const st0 = Date.now(); // a real hop (14 m/s up, 32 gravity: 3 m high, 0.875 s) from 3 m off, coming down on B
  await knight(1100, 0, under, () => { const t = Math.min(0.875, (Date.now() - st0) / 1000); return [P[0] + 3 - 3 * Math.min(1, t / 0.875), Math.max(Y, Y + 14 * t - 16 * t * t), P[2]]; });
  await knight(400, 0, under);
  const sd = B.take('dmg', (m) => m.to === B.id && m.w === 'mechstomp');
  ok(sd && sd.a === 50 && B.take('sleep'), 'STOMPED: 50 and flat on the floor');

  // ---- 10. dying inside some other way (the void): the mech blows up
  await sleep(1500);
  A.got.length = 0;
  A.place([P[0], -80, P[2]], { f: MF.MECH }); await sleep(400);
  ok(A.take('mech', (m) => m.k === 'down' && m.id === A.id) && !A.alive, 'fell in the void inside: it blows up too');

  // ---- 11. disconnect: the mech goes with you
  await sleep(3000);
  const D = await client('leaver'); await sleep(300);
  await hold(1600, [[D, [-6, Y, 0]]]);
  D.send({ t: 'deploy', r: 'mechdrop', at: [-6, Y, -6] });
  const dcall = await B.wait('mech', (m) => m.k === 'call' && m.o === D.id, 1500);
  await hold(2900, [[D, [-6, Y, 0]]]);
  await hold(300, [[D, [-6, Y, -5]]]); D.send({ t: 'mech', k: 'in' }); await sleep(400);
  B.got.length = 0;
  D.ws.close(); await sleep(1400);
  const gone = B.take('mech', (m) => (m.k === 'out' && m.id === D.id) || (m.k === 'gone' && m.m === (dcall && dcall.id)));
  const list = B.all('mech', (m) => m.k === 'list').pop();
  ok(dcall && gone && !(list && list.m.some((e) => e[1] === D.id)), 'left mid-mech: no orphan mech');

  // ---- 13. exploits a review found (each of these got through the old server)
  const mechUp = async (c, f, at, stand, others) => { // call one in, wait for it, climb in
    await hold(1600, [[c, stand], ...others]);
    c.got.length = 0;
    c.send({ t: 'deploy', r: 'mechdrop', at, mf: f });
    await c.wait('mech', (m) => m.k === 'call', 1500);
    await hold(2900, [[c, stand], ...others]);
    await hold(300, [[c, [at[0] + 1.5, Y, at[2] + 1]], ...others]);
    c.send({ t: 'mech', k: 'in' });
    return c.wait('mech', (m) => m.k === 'in' && m.id === c.id, 1000);
  };
  await sleep(1500);
  const far = [[B, [-4, Y, 12]], [C, [10, Y, 12]]];
  const inX = await mechUp(A, 'paperplane', [4, Y, -4], [4, Y, 3], far);
  ok(inX && inX.f === 'paperplane', 'exploit tests: A in a fresh PAPER PLANE');
  P = inX ? inX.p : [4, Y, -4];
  const still = (ms, o = {}, extra = far) => hold(ms, [[A, () => P, { f: MF.MECH, ...o }], ...extra]);
  await still(800);
  // speed hack: +1.5 m every 15 ms (each one inside the old 3 m grace window) for 1.7 s
  A.got.length = 0;
  { const x0 = P[0]; let x = x0; const t0 = Date.now(); while (Date.now() - t0 < 1700) { x += 1.5; A.place([x, Y, P[2]], { f: MF.MECH, v: [100, 0, 0] }); await sleep(15); } }
  await sleep(400);
  const gotX = A.spos[0] - P[0];
  ok(gotX < 40, `speed hack (+1.5 m every 15 ms for 1.7 s): the server let it go ${gotX.toFixed(1)} m (old: ~144), ${A.all('mech', (m) => m.k === 'fix').length} corrections`);
  P = A.spos.slice(); P[1] = Y; await still(800);
  // free flight: +2.4 m up every 30 ms with no hover flag
  { let y = P[1]; const t0 = Date.now(); while (Date.now() - t0 < 1200) { y += 2.4; A.place([P[0], y, P[2]], { f: MF.MECH, v: [0, 80, 0] }); await sleep(30); } }
  await sleep(400);
  ok(A.spos[1] < P[1] + 6, `free flight (+2.4 m up every 30 ms, no hover): got to ${(A.spos[1] - P[1]).toFixed(1)} m up (old: ~79)`);
  await still(1200);
  // ...while a real hover climb (hop, then 6.5 m/s up with the hover flag for 1.3 s, then hang) is fine
  A.got.length = 0;
  { const t0 = Date.now(); while (Date.now() - t0 < 2200) { const t = (Date.now() - t0) / 1000; A.place([P[0], P[1] + Math.min(t, 1.3) * 6.5, P[2]], { f: MF.MECH | MF.A, v: [0, t < 1.3 ? 6.5 : 0, 0] }); await sleep(50); } }
  ok(!A.all('mech', (m) => m.k === 'fix').length && A.spos[1] > P[1] + 7, `a real hover climb to ${(A.spos[1] - P[1]).toFixed(1)} m: no corrections`);
  await still(1500);
  // stomp spam: B right under it, A on the floor saying it's falling fast / not falling, every 25 ms
  B.got.length = 0;
  await hold(400, [[A, () => P, { f: MF.MECH }], [B, () => P], [C, [10, Y, 12]]]);
  { const t0 = Date.now(); let k = 0; while (Date.now() - t0 < 1000) { A.place(P, { f: MF.MECH, v: [0, k++ % 2 ? 0 : -20, 0] }); if (k % 3 === 0) B.place(P); await sleep(25); } }
  await still(300, {}, [[B, () => P], [C, [10, Y, 12]]]);
  const spam = B.all('dmg', (m) => m.to === B.id && m.w === 'mechstomp').length;
  ok(spam === 0, `stomp spam from a fake fall (on the floor the whole time): ${spam} stomps (old: 2+)`);
  // ram while standing still: B touching the front, A sends v -15 m/s but doesn't move
  await sleep(1500);
  const front = [P[0], Y, P[2] - 1.2];
  await still(1500, {}, [[B, front], [C, [10, Y, 12]]]);
  B.got.length = 0;
  await still(2000, { v: [0, 0, -15] }, [[B, front], [C, [10, Y, 12]]]);
  const rams = B.all('dmg', (m) => m.to === B.id && m.w === 'mechram').length;
  ok(rams === 0, `ram while standing still (claims 15 m/s): ${rams} rams (old: 4)`);
  // ...but really walking into them at speed still rams
  await sleep(1500);
  const rf = P.slice(), rt = [P[0], Y, P[2] - 5.5], bt = [P[0], Y, P[2] - 6.5];
  await still(1200, {}, [[B, bt], [C, [10, Y, 12]]]);
  B.got.length = 0; const r0 = Date.now();
  await hold(900, [[A, () => { const k = Math.min(1, (Date.now() - r0) / 480); return [rf[0], Y, rf[2] + (rt[2] - rf[2]) * k]; }, { f: MF.MECH, v: [0, 0, -11.5] }], [B, bt], [C, [10, Y, 12]]]);
  P = rt.slice();
  ok(B.all('dmg', (m) => m.to === B.id && m.w === 'mechram').length >= 1, 'really running into someone at ~11 m/s: still a ram');
  // hop out + back in to skip cooldowns: the swarm's cooldown (and the energy) stay with the mech
  await sleep(1500); await still(600);
  A.got.length = 0;
  A.send({ t: 'mech', k: 'swarm', d: [0, 0, -1] }); await still(400);
  const sw1 = A.all('mech', (m) => m.k === 'swarm' && m.id === A.id).length;
  A.send({ t: 'mech', k: 'out' });
  const ho = await A.wait('mech', (m) => m.k === 'pos', 800);
  const hp2 = ho ? ho.p : P;
  await hold(300, [[A, hp2], ...far]);
  A.send({ t: 'mech', k: 'in' }); await hold(350, [[A, hp2], ...far]);
  const quick = A.take('mech', (m) => m.k === 'in' && m.id === A.id), qno = A.take('mech', (m) => m.k === 'no');
  ok(!quick && qno && qno.why === 'still climbing down', `back in straight away: refused (${qno && qno.why})`);
  await hold(900, [[A, hp2], ...far]);
  A.send({ t: 'mech', k: 'in' });
  const back2 = await A.wait('mech', (m) => m.k === 'in' && m.id === A.id, 800);
  P = back2 ? back2.p : P;
  await still(400);
  A.send({ t: 'mech', k: 'swarm', d: [0, 0, -1] }); await still(500);
  const sw2 = A.all('mech', (m) => m.k === 'swarm' && m.id === A.id).length;
  ok(sw1 === 1 && back2 && sw2 === 1, `hop out + in, swarm again: still on cooldown (${sw2} swarm${sw2 > 1 ? 's' : ''}, old: 2)`);
  // B in a NIGHT SHIFT next to a thin wall (warehouse: a wall 1.7 m to its -x)
  await sleep(2600);
  const W = [-8, Y, 0], aOff = [[A, () => P, { f: MF.MECH }], [C, [10, Y, 12]]];
  const inN = await mechUp(B, 'nightshift', W, [-3, Y, 0], aOff);
  ok(inN && inN.f === 'nightshift', 'B in a NIGHT SHIFT by the wall');
  const BP = inN ? inN.p : W;
  // hop out with the wall on the climbing-out side: not through it
  await hold(800, [[B, BP, { y: Math.PI, f: MF.MECH }], ...aOff]);
  B.got.length = 0; B.send({ t: 'mech', k: 'out' });
  const bo = await B.wait('mech', (m) => m.k === 'pos', 800);
  ok(bo && bo.p[0] > W[0] - 1.4, `hop out next to a wall: out at x ${bo && bo.p[0].toFixed(2)} (the wall's face is at ${(W[0] - 1.7).toFixed(1)}; old: ${(W[0] - 2.2).toFixed(1)}, inside it)`);
  await hold(1200, [[B, bo ? bo.p : W], ...aOff]);
  B.send({ t: 'mech', k: 'in' });
  const inN2 = await B.wait('mech', (m) => m.k === 'in' && m.id === B.id, 800);
  const BQ = inN2 ? inN2.p : BP;
  // the shield: no swinging behind it
  await hold(600, [[B, BQ, { y: 0, f: MF.MECH | MF.A }], ...aOff]);
  A.got.length = 0;
  B.send({ t: 'mech', k: 'swing' }); await hold(400, [[B, BQ, { y: 0, f: MF.MECH | MF.A }], ...aOff]);
  ok(!A.take('mech', (m) => m.k === 'swing' && m.id === B.id), 'swing with the shield up: refused');
  await hold(300, [[B, BQ, { y: 0, f: MF.MECH }], ...aOff]);
  B.send({ t: 'mech', k: 'swing' }); await hold(400, [[B, BQ, { y: 0, f: MF.MECH }], ...aOff]);
  ok(A.take('mech', (m) => m.k === 'swing' && m.id === B.id), 'shield down: swings again');
  // ...and walking behind it at full speed gets put back (it slows you to 45%)
  await hold(1400, [[B, BQ, { y: 0, f: MF.MECH | MF.A }], ...aOff]);
  B.got.length = 0; const sq0 = Date.now();
  await hold(1500, [[B, () => [BQ[0] + 10.5 * (Date.now() - sq0) / 1000, Y, BQ[2]], { y: 0, f: MF.MECH | MF.A, v: [10.5, 0, 0] }], ...aOff]);
  ok(B.all('mech', (m) => m.k === 'fix').length >= 1, 'full speed (10.5 m/s) with the shield up: corrected');
  const half = B.spos.slice(); B.got.length = 0; const sq1 = Date.now();
  await hold(1500, [[B, () => [half[0] + 4.6 * (Date.now() - sq1) / 1000, Y, half[2]], { y: 0, f: MF.MECH | MF.A, v: [4.6, 0, 0] }], ...aOff]);
  ok(!B.all('mech', (m) => m.k === 'fix').length, 'shield speed (4.6 m/s) behind it: fine');
  // hopping out to dodge MECH DOWN: not while you're being hit
  A.got.length = 0;
  C.send({ t: 'hit', w: 'ar', to: A.id, d: aim([10, Y + 1.6, 12], P).d, n: 1, h: 0 }); await still(150, {}, [[B, () => B.spos], [C, [10, Y, 12]]]);
  A.send({ t: 'mech', k: 'out' }); await still(300, {}, [[B, () => B.spos], [C, [10, Y, 12]]]);
  const uf = A.take('mech', (m) => m.k === 'no');
  ok(uf && uf.why === "can't hop out under fire" && !A.take('mech', (m) => m.k === 'out'), 'hop out right after a hit: refused (under fire)');

  // ---- 14. empty mechs take hits: one idle after a hop-out, one waiting after it lands (all of this was ignored before)
  await sleep(1700);
  const hurts = (c, id) => c.all('mech', (m) => m.k === 'hurt' && m.m === id);
  const lastHurt = (c, id) => hurts(c, id).pop() || null;
  await hold(400, [[B, BQ, { y: 0, f: MF.MECH }], ...aOff]);
  B.got.length = 0;
  B.send({ t: 'mech', k: 'out' });
  const bo2 = await B.wait('mech', (m) => m.k === 'out' && m.id === B.id && m.why === 'hop', 800);
  const nsId = bo2 ? bo2.m : -1, nsP = bo2 ? bo2.p : BQ, bOut = (await B.wait('mech', (m) => m.k === 'pos', 500) || {}).p || BQ;
  const cS = [nsP[0] + 8, Y, nsP[2]], cE = [cS[0], Y + 1.6, cS[2]], body = [nsP[0], nsP[1] + 2, nsP[2]], pit = [nsP[0], nsP[1] + 3.9, nsP[2]];
  const ring = (ms, cp = cS, co = {}) => hold(ms, [[A, () => P, { f: MF.MECH }], [B, bOut], [C, cp, co]]);
  await ring(700);
  C.got.length = 0; A.got.length = 0;
  C.send({ t: 'hit', mk: nsId, w: 'ar', d: aim(cE, body).d, n: 1, h: 0 }); await ring(250);
  const e1 = lastHurt(C, nsId);
  ok(e1 && e1.a === 11 && e1.hp === 450 - 11 && e1.by === C.id && lastHurt(A, nsId), `shot B's idle NIGHT SHIFT (hopped out): armour 450 -> ${e1 && e1.hp}, everyone sees it`);
  C.send({ t: 'hit', mk: nsId, w: 'ar', d: aim(cE, pit).d, n: 1, h: 1 }); await ring(250);
  const e2 = lastHurt(C, nsId);
  ok(e2 && e2.hs === 1 && Math.abs(e2.a - 16.5) <= 0.6, `the cockpit is the head here too: ${e2 && e2.a} (11 x 1.5)`);
  // a headshot claimed while aiming at its legs: body damage
  await ring(300); C.got.length = 0;
  C.send({ t: 'hit', mk: nsId, w: 'ar', d: aim(cE, [nsP[0], nsP[1] + 1, nsP[2]]).d, n: 1, h: 1 }); await ring(250);
  ok((lastHurt(C, nsId) || {}).a === 11 && !(lastHurt(C, nsId) || {}).hs, `"headshot" aimed at its knees: ${(lastHurt(C, nsId) || {}).a} (body)`);
  // swapping guns to dodge the fire rate: an AR hit, then a sniper hit right after
  C.got.length = 0;
  C.send({ t: 'hit', mk: nsId, w: 'ar', d: aim(cE, body).d, n: 1, h: 0 }); C.place(cS, { w: 'sniper' }); await sleep(30);
  C.send({ t: 'hit', mk: nsId, w: 'sniper', d: aim(cE, body).d, n: 1, h: 0 }); await ring(300, cS, { w: 'sniper' });
  ok(hurts(C, nsId).length === 1, `AR hit then a sniper hit 30 ms later: ${hurts(C, nsId).length} counted (one clock per mech)`);
  await ring(300);
  // attacks on it: through a wall, pointing the wrong way, too fast, a knife from 8 m, its own owner, garbage ids, a pilot's hands
  const hp0 = lastHurt(C, nsId) ? lastHurt(C, nsId).hp : 0;
  const inside = [-14, Y, -6]; // in the warehouse, the metal wall between it and the mech
  await ring(500, inside); C.got.length = 0;
  C.send({ t: 'hit', mk: nsId, w: 'ar', d: aim([inside[0], Y + 1.6, inside[2]], body).d, n: 1, h: 0 }); await ring(250, inside);
  ok(!hurts(C, nsId).length, 'through the warehouse wall: nothing');
  await ring(600); C.got.length = 0;
  C.send({ t: 'hit', mk: nsId, w: 'ar', d: [0, 1, 0], n: 1, h: 0 }); await ring(200);
  ok(!hurts(C, nsId).length, 'a "hit" pointing at the sky: nothing');
  for (let i = 0; i < 20; i++) C.send({ t: 'hit', mk: nsId, w: 'ar', d: aim(cE, body).d, n: 1, h: 0 });
  await ring(250);
  ok(hurts(C, nsId).length >= 1 && hurts(C, nsId).length <= 2, `20 hits in one go: ${hurts(C, nsId).length} counted (the AR's rate, with a little lag slack)`);
  await ring(400, cS, { w: 'knife' }); C.got.length = 0;
  C.send({ t: 'hit', mk: nsId, w: 'knife', d: aim(cE, body).d }); await ring(250, cS, { w: 'knife' });
  ok(!hurts(C, nsId).length, 'a knife from 8 m: nothing');
  const cK = [nsP[0] + 2.4, Y, nsP[2]];
  await ring(500, cK, { w: 'knife' }); C.got.length = 0;
  C.send({ t: 'hit', mk: nsId, w: 'knife', d: aim([cK[0], Y + 1.6, cK[2]], body).d }); await ring(250, cK, { w: 'knife' });
  ok((lastHurt(C, nsId) || {}).a === 55, 'a knife from 2.4 m: 55');
  B.got.length = 0;
  B.send({ t: 'hit', mk: nsId, w: 'ar', d: aim([bOut[0], Y + 1.6, bOut[2]], body).d, n: 1, h: 0 }); await ring(250, cK, { w: 'knife' });
  ok(!hurts(B, nsId).length, 'its owner shooting it: nothing');
  A.got.length = 0;
  A.send({ t: 'hit', mk: nsId, w: 'ar', d: aim([P[0], Y + 4.4, P[2]], body).d, n: 1, h: 0 }); await ring(250, cK, { w: 'knife' });
  ok(!hurts(A, nsId).length, 'a pilot (no hands, only the mech\'s guns): nothing');
  const hpG = (lastHurt(C, nsId) || {}).hp; C.got.length = 0;
  for (const mk of [-1, 0, 1e9, 1.5, 'x', null, { id: nsId }, [nsId], NaN]) C.send({ t: 'hit', mk, w: 'ar', d: aim(cE, body).d, n: 1, h: 0 });
  C.send({ t: 'hit', mk: nsId, w: '__proto__', d: [1, 0, 0] }); C.send({ t: 'hit', mk: nsId, w: 'ar', d: [NaN, 0, 1e999], n: 1e9, h: -5 });
  await ring(300, cK, { w: 'knife' });
  ok(C.ws.readyState === 1 && !hurts(C, nsId).length, `garbage ids / numbers: nothing (armour still ${hpG}, was ${hp0} before the attack round)`);
  // B climbs back in: the damage stays
  const left = hpG;
  await hold(500, [[B, [nsP[0] + 1.5, Y, nsP[2]]], ...aOff]);
  B.got.length = 0; B.send({ t: 'mech', k: 'in' });
  const in4 = await B.wait('mech', (m) => m.k === 'in' && m.id === B.id, 800);
  ok(in4 && left < 450 && Math.abs(in4.hp - left) <= 1, `climbing back in keeps the damage: ${in4 && in4.hp} / 450`);
  // a mech waiting after it lands: shot to pieces. MECH DOWN, credited to the shooter, its blast hits the owner next to it
  const F2 = await client('waiter', { mf: 'paperplane' }); await sleep(300);
  const fw0 = [16, Y, -12], fAt = [16, Y, -18];
  const crowd = (ms, fp = fw0) => hold(ms, [[A, () => P, { f: MF.MECH }], [B, () => B.spos || nsP, { f: MF.MECH }], [C, [24, Y, -18]], [F2, fp]]);
  await crowd(1800);
  F2.send({ t: 'deploy', r: 'mechdrop', at: fAt, mf: 'paperplane' });
  const fc = await F2.wait('mech', (m) => m.k === 'call', 1500);
  await crowd(2900);
  const fl = F2.take('mech', (m) => m.k === 'land');
  ok(fc && fl, 'F calls a PAPER PLANE in, it lands and waits');
  const fid = fc ? fc.id : -1, fp = fl ? fl.p : fAt, cE2 = [24, Y + 1.6, -18], fBody = [fp[0], fp[1] + 1.5, fp[2]], fNear = [fp[0] - 3, Y, fp[2]];
  await crowd(500, fNear);
  C.got.length = 0; F2.got.length = 0;
  let fdown = null;
  for (let i = 0; i < 50 && !fdown; i++) { C.send({ t: 'hit', mk: fid, w: 'ar', d: aim(cE2, fBody).d, n: 1, h: 0 }); await crowd(115, fNear); fdown = C.all('mech', (m) => m.k === 'down' && m.m === fid)[0]; }
  const fh = hurts(C, fid);
  ok(fh.length >= 20 && fh[0].hp === 270 - 11, `the waiting mech takes every bullet: ${fh.length} hits, 270 -> ${fh.length ? fh[fh.length - 1].hp : '?'}`);
  ok(fdown && fdown.e === 1 && fdown.by === C.id && fdown.id === F2.id, 'armour at 0: MECH DOWN, credited to C (nobody inside)');
  await crowd(300, fNear);
  const fblast = F2.take('dmg', (m) => m.to === F2.id && m.w === 'mechboom');
  ok(fblast && fblast.from === C.id, `its blast hits its owner standing next to it: ${fblast && fblast.a}, credited to C`);
  const fgone = C.all('mech', (m) => m.k === 'gone' && m.m === fid).length;
  C.got.length = 0; await crowd(1300, fNear);
  const flist = C.all('mech', (m) => m.k === 'list').pop();
  ok(fgone && flist && !flist.m.some((e) => e[0] === fid), 'and it is gone');
  // review probes (#413), on G's waiting NIGHT SHIFT by the warehouse wall: an unearned streak gun, the revolver at fan
  // rate with no reload, a fake velocity through the wall / from too far
  const G2 = await client('probe', { mf: 'nightshift' }); await sleep(300);
  const gAt = [-8, Y, -10], gS = [-3, Y, -10], cG = [0, Y, -10], cGE = [cG[0], Y + 1.6, cG[2]];
  const gring = (ms, cp = cG, co = {}) => hold(ms, [[A, () => P, { f: MF.MECH }], [B, () => B.spos || nsP, { f: MF.MECH }], [C, cp, co], [G2, gS]]);
  await gring(1800);
  G2.send({ t: 'deploy', r: 'mechdrop', at: gAt, mf: 'nightshift' });
  const gc = await G2.wait('mech', (m) => m.k === 'call', 1500);
  await gring(2900);
  const gl = G2.take('mech', (m) => m.k === 'land'), gid = gc ? gc.id : -1, gp = gl ? gl.p : gAt, gBody = [gp[0], gp[1] + 2, gp[2]], gPit = [gp[0], gp[1] + 3.9, gp[2]];
  ok(gc && gl && gc.f === 'nightshift', 'probe mech: G calls a NIGHT SHIFT in by the wall, it waits');
  await gring(400, cG, { w: 'scythe_rifle' }); C.got.length = 0;
  C.send({ t: 'hit', mk: gid, w: 'scythe_rifle', d: aim(cGE, gBody).d, n: 1, h: 0 }); await gring(300, cG, { w: 'scythe_rifle' });
  ok(!hurts(C, gid).length, `the scythe's rifle without earning the scythe: ${hurts(C, gid).length ? hurts(C, gid)[0].a + ' damage' : 'nothing'}`);
  const gIn = [-14, Y, -12]; // in the warehouse, the metal wall between it and the mech
  await gring(400, gIn, { v: [90000, 0, 0] }); C.got.length = 0;
  C.send({ t: 'hit', mk: gid, w: 'ar', d: aim([gIn[0], Y + 1.6, gIn[2]], gBody).d, n: 1, h: 0 }); await gring(250, gIn, { v: [90000, 0, 0] });
  C.send({ t: 'hit', mk: gid, w: 'ar', d: aim([gIn[0], Y + 1.6, gIn[2]], gPit).d, n: 1, h: 1 }); await gring(250, gIn, { v: [90000, 0, 0] });
  ok(!hurts(C, gid).length, `through the wall with a fake 90 km/s velocity (body + cockpit): ${hurts(C, gid).length} hits`);
  const gFar = [gp[0] + 12, Y, gp[2]];
  await gring(400, gFar, { v: [90000, 0, 0], w: 'knife' }); C.got.length = 0;
  C.send({ t: 'hit', mk: gid, w: 'knife', d: aim([gFar[0], Y + 1.6, gFar[2]], gBody).d }); await gring(250, gFar, { v: [90000, 0, 0], w: 'knife' });
  ok(!hurts(C, gid).length, `a knife (2.6 m) from 12 m with a fake velocity: ${hurts(C, gid).length} hits`);
  await gring(2700, cG, { w: 'revolver' }); C.got.length = 0; // (a fresh cylinder)
  for (let i = 0; i < 8; i++) { C.send({ t: 'hit', mk: gid, w: 'revolver', d: aim(cGE, gBody).d, n: 1, h: 0 }); await gring(110, cG, { w: 'revolver' }); }
  const rv = hurts(C, gid), rvd = rv.reduce((a, m) => a + m.a, 0);
  ok(rv.length >= 1 && rv.length <= 6 && rvd <= 160, `8 revolver taps 110 ms apart: ${rv.length} hits, ${rvd} damage (the cylinder's rules, as for a player: early "taps" are fan damage; old: 8 hits, 320)`);
  await gring(2700, cG, { w: 'revolver' }); C.got.length = 0;
  for (let i = 0; i < 9; i++) { C.send({ t: 'hit', mk: gid, w: 'revolver', d: aim(cGE, gBody).d, n: 1, h: 0, fan: 1 }); await gring(110, cG, { w: 'revolver' }); }
  const rfan = hurts(C, gid);
  ok(rfan.length >= 1 && rfan.length <= 6 && rfan.every((m) => m.a <= 28), `9 fanned shots: ${rfan.length} hits of ${rfan.map((m) => m.a).join('/')} (6 a cylinder, then a reload; fan damage)`);
  await gring(300); C.got.length = 0;
  C.send({ t: 'hit', mk: gid, w: 'ar', d: aim(cGE, gBody).d, n: 1, h: 0 }); await gring(250);
  ok((lastHurt(C, gid) || {}).a === 11, 'and a plain AR shot from 8 m still lands: 11');
  G2.ws.close();
  // a chicken rocket's blast hurts an empty mech too (B hops out again)
  await sleep(1700);
  await hold(300, [[B, () => B.spos, { f: MF.MECH }], [C, [24, Y, -18]]]);
  B.got.length = 0; B.send({ t: 'mech', k: 'out' });
  const bo3 = await B.wait('mech', (m) => m.k === 'out' && m.id === B.id, 800);
  const n3 = bo3 ? bo3.p : nsP, cR = [n3[0], Y, n3[2] - 7], bOut3 = (await B.wait('mech', (m) => m.k === 'pos', 500) || {}).p || n3;
  const bAway = [n3[0], Y, n3[2] + 9]; // (the owner out of the rocket's way)
  await hold(800, [[B, bAway], [C, cR, { w: 'chicken' }]]);
  C.got.length = 0;
  C.send({ t: 'fire', w: 'chicken', o: [cR[0], Y + 1.6, cR[2]], d: aim([cR[0], Y + 1.6, cR[2]], [n3[0], n3[1] + 1.5, n3[2]]).d }); await hold(800, [[B, bAway], [C, cR, { w: 'chicken' }]]);
  const ch = lastHurt(C, bo3 ? bo3.m : -1);
  ok(ch && ch.w === 'chicken' && ch.a >= 50, `a chicken rocket into the idle knight: ${ch && ch.a} (a projectile + its blast)`);
  F2.ws.close();

  // ---- 12. garbage
  const junk = [{ t: 'mech' }, { t: 'mech', k: 5 }, { t: 'mech', k: 'gun', d: 'x' }, { t: 'mech', k: 'gun', d: [NaN, 1e999, null] }, { t: 'mech', k: '__proto__' },
    { t: 'mech', k: 'constructor' }, { t: 'mech', k: 'slamland', p: { 0: 1 } }, { t: 'mech', k: 'lunge', to: { x: 1 }, d: [1, 2] }, { t: 'mech', k: 'crane', to: -1 },
    { t: 'mech', k: 'jet', on: 'yes' }, { t: 'deploy', r: 'mechdrop', at: [1e308, -1e308, NaN], mf: { evil: 1 } }, { t: 'deploy', r: 'mechdrop', at: 'here' },
    { t: 's', q: B.q, p: [0, Y, 0], v: [0, 0, 0], f: 2 ** 40 }, { t: 'streaks', list: ['mechdrop'], mf: ['x'] }, '{"t":"mech","k":"in"', { t: 'mech', k: 'x'.repeat(5000) }];
  for (const j of junk) { B.send(j); C.send(j); }
  for (let i = 0; i < 200; i++) B.send({ t: 'mech', k: 'gun', d: [0, 0, -1] });
  await sleep(800);
  ok(B.ws.readyState === 1 && C.ws.readyState === 1, 'garbage: nobody disconnected');
  const E = await client('after'); await sleep(600);
  ok(E.id > 0 && E.sn, 'garbage: the server still runs (a new player joins and gets snapshots)');
  ok(!/uncaught|TypeError|ReferenceError/.test(srvErr), 'no server errors' + (srvErr ? ': ' + srvErr.slice(0, 600) : ''));

  // ---- 15. teams (a second server in team deathmatch): your team can't touch your empty mech, the other team can
  const port2 = port + 1;
  const srv2 = srv2Ref = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(port2), JF_TRAIN_STREAKS: '1', JF_MECH_HP: String(HP), JF_GAME: 'tdm' }, stdio: ['ignore', 'pipe', 'pipe'] });
  let srvErr2 = ''; srv2.stderr.on('data', (d) => { srvErr2 += d; }); srv2.stdout.on('data', (d) => { if (/Error|uncaught/i.test(String(d))) srvErr2 += d; });
  for (let i = 0; i < 60; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${port2}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }
  const X = await client('owner', { mf: 'paperplane' }, port2);
  X.send({ t: 'cfg', map: 'warehouse' }); await sleep(900);
  const Y2 = await client('two', {}, port2), Z = await client('three', {}, port2);
  await sleep(1500);
  const team = new Map();
  for (const c of [X, Y2, Z]) { const w = c.all('welcome').pop(); if (w) team.set(c.id, w.team); }
  for (const c of [X, Y2, Z]) for (const tm of c.all('teams')) for (const [id, t] of tm.list) team.set(id, t);
  const mate = [Y2, Z].find((c) => team.get(c.id) === team.get(X.id)), foe = [Y2, Z].find((c) => team.get(c.id) !== team.get(X.id));
  ok(mate && foe && team.get(X.id), `tdm: X is on team ${team.get(X.id)}, a mate and an enemy (${[...team.values()].join(',')})`);
  if (mate && foe) {
    const xs = [0, Y, 9], ms0 = [8, Y, -8], fs0 = [-8, Y, -8];
    const tdm = (ms, o = {}) => hold(ms, [[X, xs], [mate, ms0, o.m], [foe, fs0, o.f]]);
    await tdm(500);
    X.send({ t: 'deploy', r: 'mechdrop', at: [0, Y, -8], mf: 'paperplane' });
    const xc = await X.wait('mech', (m) => m.k === 'call', 1500);
    await tdm(2900);
    ok(xc && X.take('mech', (m) => m.k === 'land'), "X's mech lands and waits");
    const xid = xc ? xc.id : -1, xb = [0, Y + 1.5, -8];
    mate.got.length = 0;
    for (let i = 0; i < 4; i++) { mate.send({ t: 'hit', mk: xid, w: 'ar', d: aim([ms0[0], Y + 1.6, ms0[2]], xb).d, n: 1, h: 0 }); await tdm(150); }
    await tdm(400, { m: { w: 'chicken' } });
    mate.send({ t: 'fire', w: 'chicken', o: [ms0[0], Y + 1.6, ms0[2]], d: aim([ms0[0], Y + 1.6, ms0[2]], xb).d }); await tdm(800, { m: { w: 'chicken' } });
    ok(!mate.all('mech', (m) => m.k === 'hurt').length, "a teammate's bullets and chicken rocket: nothing");
    foe.got.length = 0;
    foe.send({ t: 'hit', mk: xid, w: 'ar', d: aim([fs0[0], Y + 1.6, fs0[2]], xb).d, n: 1, h: 0 }); await tdm(300);
    const fh2 = foe.all('mech', (m) => m.k === 'hurt' && m.m === xid).pop();
    ok(fh2 && fh2.a === 11 && fh2.hp === 270 - 11, `the other team's bullet: armour 270 -> ${fh2 && fh2.hp}`);
  }
  ok(!/uncaught|TypeError|ReferenceError/.test(srvErr2), 'no server errors (tdm)' + (srvErr2 ? ': ' + srvErr2.slice(0, 600) : ''));
  srv2.kill();

  console.log(fails ? `${fails} FAILED` : 'ALL OK'); end(fails ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
process.on("exit", () => { try { srvRef && srvRef.kill(); } catch {} try { srv2Ref && srv2Ref.kill(); } catch {} });
