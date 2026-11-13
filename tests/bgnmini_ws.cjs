// BOARD GAME NIGHT minigames 11-15 over plain ws (server/bgnmini.js, docs/party/DESIGN.md 3.1, 3.2, 4.4). starts its own
// servers, each with its own JF_BGN_* knobs, and checks:
//   boss    the boss spawns in his mech with the right armour (frame x (2 + 0.5 a human seat)); a boss break pays +8 each and
//           the MVP +5 more; the clock running out pays the pity (+2 each, RENT IS DUE); he's gone afterwards
//   half    HALFTIME BOSS: round N/2's minigame is a boss
//   carts   a ram (with a server-okayed boost) throws a bot out of its cart and into the void, credited to the rammer;
//           boost spam and fake boosts are dropped; rams never hurt
//   cartwin bots-only: bots drive carts, the last cart standing wins (it ends early) and is paid 1st
//   peace   bots stay on the box for 60 s when nobody rams them (JF_BGN_PEACE), and they really drive about
//   ducks   two people: catches are judged by the server (nothing from 5 m away, a made-up 'catch' does nothing), a pickup
//           off the floor is +1, a catch in the air +2, a slap drops 3 ducks, the cursed duck halves your pile
//   duck2   bots-only 2v2: the team total decides it
//   bigguy  the leader gets a fresh overdrive rig every life and their kills count x3
//   online  the online lobby: a person who comes back takes "<name>'s bot" back; the warm-up after a game is on the crate
//   node tests/bgnmini_ws.cjs [basePort=3500] [part ...]
const { spawn } = require('child_process');
const path = require('path');
const WS = require('ws');
const ROOT = path.join(__dirname, '..');
const base = Number(process.argv[2]) || 3500;
const only = process.argv.slice(3);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0;
const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };

const SERVERS = [];
process.on('exit', () => { for (const p of SERVERS) try { p.kill(); } catch { /* gone */ } });
function server(port, env) {
  const p = spawn(process.execPath, ['server.js'], { cwd: ROOT, env: { ...process.env, PORT: String(port), JF_GRAPH_TTL: '1', ...env }, stdio: ['ignore', 'pipe', 'pipe'] });
  SERVERS.push(p);
  let log = '';
  p.stdout.on('data', (d) => { log += d; }); p.stderr.on('data', (d) => { log += d; });
  return new Promise((res, rej) => {
    const t0 = Date.now();
    const iv = setInterval(() => {
      if (log.includes('JANKFIRE is running')) { clearInterval(iv); res({ log: () => log, stop: () => p.kill() }); }
      else if (Date.now() - t0 > 20000) { clearInterval(iv); p.kill(); rej(new Error('server did not start: ' + log.slice(-400))); }
    }, 50);
  });
}
const errorsIn = (log) => log.split('\n').filter((l) => /^\s+at |\[(tick|msg|close|snapshot)[^\]]*\]/.test(l));
function client(port, name, join) {
  const ws = new WS(`ws://localhost:${port}/ws`);
  const c = { ws, name, id: 0, q: 1, pos: null, st: null, sts: [], ev: [], alive: new Map(), ppos: new Map(), msgs: [], closed: false, auto: false };
  ws.on('message', (d) => {
    const m = JSON.parse(d);
    c.msgs.push(m); if (c.msgs.length > 6000) c.msgs.splice(0, 3000);
    if (m.t === 'welcome') { c.id = m.id; c.q = m.q || 1; }
    if (m.t === 'spawn') { c.q = m.q; c.pos = m.p.slice(); }
    if (m.t === 'bg') { if (m.k === 'st') { m.s.at = Date.now(); c.st = m.s; c.sts.push(m.s); if (c.auto) c.answer(); } else { m.at = Date.now(); c.ev.push(m); } }
    if (m.t === 'sn') for (const r of m.p) { c.alive.set(r[0], r[11]); c.ppos.set(r[0], [r[1], r[2], r[3]]); }
  });
  ws.on('close', () => { c.closed = true; });
  ws.on('error', () => {});
  c.send = (o) => { if (ws.readyState === 1) ws.send(JSON.stringify(o)); };
  c.bg = (o) => c.send({ t: 'bg', ...o });
  c.until = (pred, ms = 30000) => new Promise((res) => { const t0 = Date.now(); const iv = setInterval(() => { let v = false; try { v = pred(); } catch { v = false; } if (v || Date.now() - t0 > ms) { clearInterval(iv); res(!!v); } }, 15); });
  c.seat = () => c.st && c.st.seats.find((s) => s.id === c.id);
  c.evs = (k) => c.ev.filter((e) => e.k === k);
  c.place = (p, v = [0, 0, 0], w = 'slapper') => { c.pos = p.slice(); c.send({ t: 's', q: c.q, p, v, y: 0, x: 0, w }); };
  // play the board quickly (roll, then whatever's cheapest), so the minigame comes round
  c.answer = () => {
    const s = c.seat(), a = c.st && c.st.ask;
    if (!s || !a || a.seat !== s.i) return;
    const k = a.k, o = { roll: { k: 'roll' }, path: { k: 'path', i: 0 }, bread: { k: 'bread', yes: false }, shop: { k: 'buy', it: null }, stake: { k: 'stake', s: 'coupons' }, who: { k: 'who', seat: a.opts && a.opts[0] }, house: { k: 'house', i: 1 } }[k];
    if (o) setTimeout(() => c.bg(o), 60);
  };
  c.inMg = (id) => { const s = c.seat(); return !!(s && c.st.ph === 'mg' && c.st.mg && c.st.mg.id === id && c.st.mg.seats.includes(s.i)); };
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'join', name, ...join }); res(c); }));
}
const OFF = (rounds) => ({ mode: 'bots', cfg: { priv: true, game: 'bgn', map: 'crate', bots: 3, rounds } });
const sum = (a) => a.reduce((x, y) => x + y, 0);

// ---------------------------------------------------------------- the bosses
async function partBoss(port) {
  // a break: weak armour (JF_MECH_HP), bots only (no humans at the table: x2)
  let S = await server(port, { JF_WATCH: '1', JF_BGN_FAST: '20', JF_BGN_ROUNDS: '4', JF_BGN_MG: 'landlord', JF_BGN_MGTIME: '60', JF_MECH_HP: '0.1' });
  let W = await client(port, 'watchB', OFF(5));
  ok(await W.until(() => W.evs('mini').some((e) => e.x && e.x.k === 'boss'), 40000), 'THE LANDLORD: a boss minigame starts');
  const mg = W.st.mg, bossId = W.evs('mini').find((e) => e.x && e.x.k === 'boss').x.id;
  ok(mg.fmt === 'boss' && mg.sides && mg.sides[0].length === 4, 'all four seats on one side');
  const inM = W.msgs.find((m) => m.t === 'mech' && m.k === 'in' && m.id === bossId);
  const bhp = W.msgs.filter((m) => m.t === 'bhp' && m.id === bossId).pop();
  ok(inM && inM.f === 'wrecking', `he spawned straight into his mech (${inM && inM.f})`);
  ok(!W.msgs.some((m) => m.t === 'mech' && m.k === 'call' && m.o === bossId), 'no drop: no mech call for him');
  ok(bhp && bhp.max === 280, `his armour is the frame's x2 with no people at the table (140 x 2 = ${bhp && bhp.max})`);
  const tm = W.msgs.filter((m) => m.t === 'teams').flatMap((m) => m.list).filter((e) => e[0] === bossId).pop();
  ok(tm && tm[1] === 2, 'he is on team 2');
  ok(await W.until(() => W.evs('res').length, 80000), 'it ended');
  const r = W.evs('res')[0], pay = new Map(r.pay);
  ok(W.evs('bossdown').length === 1 && r.winSide === 0, 'boss down: the four win');
  ok(r.mvp != null && pay.get(r.mvp) === 13 && r.seats.filter((i) => i !== r.mvp).every((i) => pay.get(i) === 8), `+8 each, the MVP (seat ${r.mvp}, ${JSON.stringify(r.dmg)}) +5 more`);
  ok(r.dmg.find((e) => e[0] === r.mvp)[1] === Math.max(...r.dmg.map((e) => e[1])), 'the MVP did the most damage');
  await sleep(600);
  ok(!W.st.seats.some((s) => s.id === bossId) && W.msgs.filter((m) => m.t === 'sn').slice(-2).every((m) => !m.p.some((x) => x[0] === bossId)), 'he went home afterwards');
  let errs = errorsIn(S.log());
  ok(!errs.length, 'no server errors' + (errs.length ? ': ' + errs.slice(0, 3).join(' | ') : ''));
  W.ws.close(); S.stop();
  // the clock: huge armour, a short clock, one person at the table (x2.5)
  S = await server(port + 1, { JF_BGN_FAST: '10', JF_BGN_ROUNDS: '4', JF_BGN_MG: 'nightmgr', JF_BGN_MGTIME: '12', JF_MECH_HP: '20' });
  const H = await client(port + 1, 'tina', OFF(5));
  H.auto = true;
  ok(await H.until(() => H.evs('mini').some((e) => e.x && e.x.k === 'boss'), 90000), 'THE NIGHT MANAGER: a boss minigame with a person in it');
  const bid = H.evs('mini').find((e) => e.x && e.x.k === 'boss').x.id, b2 = H.msgs.filter((m) => m.t === 'bhp' && m.id === bid).pop(), in2 = H.msgs.find((m) => m.t === 'mech' && m.k === 'in' && m.id === bid);
  ok(in2 && in2.f === 'nightshift' && b2 && b2.max === 1500 * 20 * 2.5, `night shift, armour x2.5 with one person at the table (${b2 && b2.max})`);
  ok(await H.until(() => H.evs('res').some((e) => e.fmt === 'boss'), 40000), 'the clock ran out');
  const r2 = H.evs('res').find((e) => e.fmt === 'boss'); // (a duel of ours may have come first)
  ok(r2.winSide === 1 && r2.pay.length === 4 && r2.pay.every(([, d]) => d === 2), 'he lives: +2 each (the pity)');
  ok(H.evs('call').some((e) => e.c === 'rent' && H.ev.indexOf(e) > H.ev.indexOf(r2) - 30), 'RENT IS DUE');
  errs = errorsIn(S.log());
  ok(!errs.length, 'no server errors' + (errs.length ? ': ' + errs.slice(0, 3).join(' | ') : ''));
  H.ws.close(); S.stop();
}

// ---------------------------------------------------------------- halftime boss
async function partHalf(port) {
  const S = await server(port, { JF_WATCH: '1', JF_BGN_FAST: '20', JF_BGN_ROUNDS: '4', JF_BGN_MGTIME: '5', JF_MECH_HP: '0.05', JF_BGN_SEED: '7' });
  const W = await client(port, 'watchH', OFF(5));
  ok(await W.until(() => W.st && W.st.round === 2 && W.st.mg, 120000), 'round 2 (of 4) reaches its minigame');
  const mg = W.st.mg;
  ok(mg.fmt === 'boss' && (mg.id === 'landlord' || mg.id === 'nightmgr'), `HALFTIME BOSS: round 2's minigame is ${mg.id}`);
  const errs = errorsIn(S.log());
  ok(!errs.length, 'no server errors' + (errs.length ? ': ' + errs.slice(0, 3).join(' | ') : ''));
  W.ws.close(); S.stop();
}

// ---------------------------------------------------------------- bumper carts: a person rams a bot off
async function partCarts(port) {
  const S = await server(port, { JF_BGN_FAST: '10', JF_BGN_ROUNDS: '4', JF_BGN_MG: 'carts', JF_BGN_FMT: 'ffa', JF_BGN_MGTIME: '70', JF_BGN_PEACE: '1' });
  const H = await client(port, 'rammy', OFF(5));
  H.auto = true;
  ok(await H.until(() => H.inMg('carts'), 60000), 'bumper carts with us in it');
  ok(await H.until(() => H.msgs.some((m) => m.t === 'cart' && m.r === H.id), 3000), 'the server put us in a cart');
  ok(H.msgs.filter((m) => m.t === 'loadout').pop().lo.only.join() === 'slapper', 'no guns: the hand slapper only');
  const bots = H.st.mg.seats.map((i) => H.st.seats[i]).filter((s) => s.bot).map((s) => s.id);
  ok(await H.until(() => bots.every((id) => H.msgs.some((m) => m.t === 'cart' && m.r === id)), 3000), 'every bot is in a cart too');
  await sleep(1300); // (spawn protection)
  // a boost while we're in the cart: one counts, spam in the cooldown doesn't
  for (let k = 0; k < 4; k++) H.bg({ k: 'boost' });
  await sleep(500);
  ok(H.evs('boost').filter((e) => e.id === H.id).length === 1, 'boost spam: one boost per cooldown');
  await sleep(1200);
  // ram: get on the inside of a bot (between it and the middle), then charge it outward with a boost. a ram can still
  // land someone on the box (a crate in the way): up to 4 goes for one that goes into the void
  let pos = H.pos ? [H.pos[0], 1, H.pos[2]] : [-11, 1, -11], ram = null, fell = null;
  for (let go = 0; go < 4 && !fell; go++) {
    const n0 = H.evs('ram').filter((e) => e.a === H.id).length, t0 = Date.now();
    let boosted = false;
    await sleep(go ? 1600 : 0); // (the boost's cooldown)
    while (Date.now() - t0 < 12000 && H.evs('ram').filter((e) => e.a === H.id).length === n0) {
      const live = bots.filter((id) => H.alive.get(id) && H.ppos.get(id) && H.ppos.get(id)[1] > 0.5);
      const victim = live.sort((a, b) => Math.hypot(...H.ppos.get(b)) - Math.hypot(...H.ppos.get(a)))[0];
      if (!victim) { H.place(pos); await sleep(50); continue; }
      const bp = H.ppos.get(victim), l = Math.hypot(bp[0], bp[2]) || 1, u = [bp[0] / l, bp[2] / l];
      const stage = [bp[0] - u[0] * 3.2, bp[2] - u[1] * 3.2], ds = Math.hypot(stage[0] - pos[0], stage[1] - pos[2]);
      let dir, sp;
      if (ds > 1.2 && !boosted) { dir = [(stage[0] - pos[0]) / ds, (stage[1] - pos[2]) / ds]; sp = Math.min(13, ds / 0.05); }
      else { if (!boosted) { H.bg({ k: 'boost' }); boosted = true; } const dd = Math.hypot(bp[0] - pos[0], bp[2] - pos[2]) || 1; dir = [(bp[0] - pos[0]) / dd, (bp[2] - pos[2]) / dd]; sp = 20; }
      pos = [pos[0] + dir[0] * sp * 0.05, 1, pos[2] + dir[1] * sp * 0.05];
      H.place(pos, [dir[0] * sp, 0, dir[1] * sp]);
      await sleep(50);
      if (boosted && Date.now() - t0 > 5000 && Math.random() < 0.02) boosted = false; // (missed: line up again)
    }
    ram = H.evs('ram').filter((e) => e.a === H.id)[n0] || ram;
    if (!ram) continue;
    for (let k = 0; k < 60 && !fell; k++) { H.place(pos); await sleep(50); fell = H.evs('fell').find((e) => e.id === ram.b && e.by === H.id); }
  }
  ok(!!ram, `we rammed a bot (${ram ? ram.s + ' m/s' : 'no ram'})`);
  if (ram) {
    ok(H.msgs.some((m) => m.t === 'cart' && m.k === 'u' && m.r === 0 && m.o === ram.b), 'it got thrown out of its cart (the cart rolls on empty)');
    ok(fell && fell.out === 0 && fell.x.lives[fell.seat] === 1, 'into the void: a life gone (1 left), and it\'s our knock-off');
    ok(await H.until(() => new Set(H.msgs.filter((m) => m.t === 'cart' && m.r === ram.b).map((m) => m.id)).size >= 2, 6000), 'it respawned straight into a fresh cart');
    const kill = H.msgs.find((m) => m.t === 'kill' && m.v === ram.b && m.k === H.id);
    ok(kill && kill.w === 'void' && kill.via === 'cart', 'the kill feed says we price-checked it into the void');
  }
  ok(!H.msgs.some((m) => m.t === 'dmg' && m.w === 'cart'), 'rams never do damage');
  const errs = errorsIn(S.log());
  ok(!errs.length, 'no server errors' + (errs.length ? ': ' + errs.slice(0, 3).join(' | ') : ''));
  H.ws.close(); S.stop();
}

// ---------------------------------------------------------------- bumper carts: bots-only, last cart standing
async function partCartWin(port) {
  const S = await server(port, { JF_WATCH: '1', JF_BGN_FAST: '20', JF_BGN_ROUNDS: '4', JF_BGN_MG: 'carts', JF_BGN_FMT: 'ffa', JF_BGN_MGTIME: '70' });
  const W = await client(port, 'watchC', OFF(5));
  ok(await W.until(() => W.evs('res').length, 120000), 'a bots-only bumper carts game ended');
  const r = W.evs('res')[0], mgSt = W.sts.find((s) => s.ph === 'mg' && s.mg && s.mg.id === 'carts'), pay = new Map(r.pay);
  ok(W.evs('ram').some((e) => e.a && e.b) && W.evs('boost').length > 0, `bots rammed (${W.evs('ram').length}) and boosted (${W.evs('boost').length})`);
  ok(r.x.out.length === 3 && r.x.out.every((i) => r.x.falls[i] === 2), `three went into the void twice each (out: ${r.x.out.join(',')})`);
  ok(!r.x.out.includes(r.place[0]) && pay.get(r.place[0]) === 10, `the last cart standing (seat ${r.place[0]}) is 1st and paid 10`);
  ok(r.place.slice(1).every((i, k, a) => k === 0 || r.x.out.indexOf(a[k - 1]) > r.x.out.indexOf(i)), 'the rest by who lasted longest');
  const took = mgSt ? W.evs('res')[0].at - mgSt.at : 1e9;
  ok(mgSt && took < 68000, `it ended before the clock (after ${Math.round(took / 1000)} of 70 s)`);
  const errs = errorsIn(S.log());
  ok(!errs.length, 'no server errors' + (errs.length ? ': ' + errs.slice(0, 3).join(' | ') : ''));
  W.ws.close(); S.stop();
}

// ---------------------------------------------------------------- bumper carts: nobody rams, nobody falls (60 s)
async function partPeace(port) {
  const S = await server(port, { JF_WATCH: '1', JF_BGN_FAST: '20', JF_BGN_ROUNDS: '4', JF_BGN_MG: 'carts', JF_BGN_FMT: 'ffa', JF_BGN_MGTIME: '62', JF_BGN_PEACE: '1' });
  const W = await client(port, 'watchP', OFF(5));
  ok(await W.until(() => W.st && W.st.ph === 'mg' && W.st.mg.id === 'carts', 40000), 'bumper carts, bots only, nobody rams');
  const ids = W.st.mg.seats.map((i) => W.st.seats[i].id), path = new Map(ids.map((id) => [id, 0])), last = new Map(), t0 = Date.now();
  let lowest = 99;
  while (Date.now() - t0 < 61000 && !W.evs('res').length) {
    for (const id of ids) { const p = W.ppos.get(id); if (!p) continue; const q = last.get(id); if (q) path.set(id, path.get(id) + Math.hypot(p[0] - q[0], p[2] - q[2])); last.set(id, p); if (W.alive.get(id)) lowest = Math.min(lowest, p[1]); }
    await sleep(100);
  }
  ok(Date.now() - t0 >= 60000, 'the minigame ran its 60 s');
  ok(!W.evs('fell').length && !W.msgs.some((m) => m.t === 'kill'), 'nobody fell off the box in 60 s');
  ok(lowest > 0.5, `everyone stayed up on the box the whole time (lowest ${lowest.toFixed(2)})`);
  ok([...path.values()].every((d) => d > 60), 'and they really drove about: ' + [...path.values()].map((d) => Math.round(d) + ' m').join(', '));
  ok(ids.every((id) => W.msgs.some((m) => m.t === 'cart' && m.r === id)), 'every bot rode a cart');
  const errs = errorsIn(S.log());
  ok(!errs.length, 'no server errors' + (errs.length ? ': ' + errs.slice(0, 3).join(' | ') : ''));
  W.ws.close(); S.stop();
}

// ---------------------------------------------------------------- duck catch: two people, the server's judging
async function partDucks(port) {
  const S = await server(port, { JF_WATCH: '1', JF_LOBBY_WAIT: '1500', JF_BGN_FAST: '10', JF_BGN_ROUNDS: '4', JF_BGN_MG: 'duckcatch', JF_BGN_FMT: 'ffa', JF_BGN_MGTIME: '75', JF_BGN_PEACE: '1' });
  const W = await client(port, 'watchK', { mode: 'bots', cfg: { lobby: 'bgn' } });
  const A = await client(port, 'alma', { mode: 'bots', cfg: { lobby: 'bgn' } });
  const B = await client(port, 'bert', { mode: 'bots', cfg: { lobby: 'bgn' } });
  A.auto = true; B.auto = true;
  ok(await A.until(() => A.inMg('duckcatch') && B.inMg('duckcatch'), 120000), 'duck catch with both of us in it');
  ok(A.msgs.filter((m) => m.t === 'loadout').pop().lo.only.join() === 'slapper', 'the hand slapper only');
  const sB = B.seat().i, e0 = B.ev.length, now0 = () => B.ev.slice(e0), pileB = () => { const e = now0().filter((x) => (x.k === 'duckx' || x.k === 'slap' || x.k === 'curse') && x.seat === sB).pop(); return e ? e.pile : 0; };
  let hold = { A: null, B: null };
  const tick = setInterval(() => { if (hold.A) A.place(hold.A); if (hold.B) B.place(hold.B); }, 50);
  // A: 5 m from where a duck lands, the whole way down and a second after. a made-up catch message does nothing either
  const near = (c, k) => c.ev.filter((e) => e.k === 'duck' && !e.one && e.ms > 1500 && !k.has(e.id) && Date.now() - e.at < e.ms - 700 && !c.ev.some((x) => x.k === 'duckx' && x.id === e.id)); // (still well up in the air)
  const used = new Set();
  ok(await A.until(() => near(A, used).length, 20000), 'ducks are falling');
  const d1 = near(A, used)[0]; used.add(d1.id);
  hold.A = [d1.p[0] + 5, d1.p[1], d1.p[2]];
  for (const j of [{ k: 'catch', id: d1.id }, { k: 'duckx', id: d1.id }, { k: 'grab', id: d1.id, p: d1.p }]) A.bg(j);
  await sleep(d1.ms + 1000);
  ok(!A.evs('duckx').some((e) => e.id === d1.id && e.by === A.id), 'standing 5 m away (and saying we caught it) catches nothing');
  // ...then walking onto it (if it's still there): a pickup off the floor
  if (!A.evs('duckx').some((e) => e.id === d1.id)) {
    hold.A = d1.p.slice();
    ok(await A.until(() => A.evs('duckx').some((e) => e.id === d1.id), 2000), 'walking onto it picks it up');
    const e = A.evs('duckx').find((x) => x.id === d1.id);
    ok(e && e.by === A.id && e.air === 0 && e.v === (e.g ? 5 : 1), `off the floor: +${e && e.v}`);
  }
  // B: stand right under falling ducks, catch them in the air (+2, gold +5)
  for (let k = 0; k < 4; k++) {
    const d = near(B, used)[0];
    if (!d) { await sleep(400); continue; }
    used.add(d.id); hold.B = d.p.slice();
    await B.until(() => B.evs('duckx').some((e) => e.id === d.id), d.ms + 1500);
  }
  const airs = B.evs('duckx').filter((e) => e.by === B.id && e.air);
  ok(airs.length >= 2 && airs.every((e) => e.v === (e.g ? 5 : 2)), `caught in the air: ${airs.map((e) => '+' + e.v).join(' ')}`);
  ok(pileB() === sum(now0().filter((e) => e.k === 'duckx' && e.by === B.id).map((e) => e.v)) - sum(now0().filter((e) => (e.k === 'slap' || e.k === 'curse') && e.seat === sB).map((e) => e.n)), `B's pile is what B caught, minus what B lost (${pileB()})`);
  // A slaps B: 3 ducks fly out
  const before = pileB(), bp = B.pos.slice();
  hold.A = [bp[0] + 1, bp[1], bp[2]];
  await sleep(300);
  A.send({ t: 'hit', w: 'slapper', to: B.id, d: [-1, 0, 0] });
  ok(await A.until(() => A.evs('slap').some((e) => e.a === A.id && e.b === B.id), 2000), 'a slap lands');
  const sl = A.evs('slap').find((e) => e.a === A.id);
  ok(sl.n === Math.min(3, sl.pile + sl.n) && sl.n > 0, `it knocked ${sl.n} ducks loose (${sl.pile + sl.n} -> ${sl.pile}; ${before} a moment before)`);
  await sleep(150);
  ok(A.evs('duck').filter((e) => e.one && A.ev.indexOf(e) > A.ev.indexOf(sl)).length === Math.min(sl.n, 4), 'they pop out round B as ducks worth 1');
  ok(!A.msgs.some((m) => m.t === 'dmg' && m.w === 'slapper'), 'slaps don\'t hurt');
  // the cursed duck: B stands where it lands, loses half
  hold.A = null;
  for (let k = 0; k < 4 && pileB() < 4; k++) { const d = near(B, used)[0]; if (!d) { await sleep(400); continue; } used.add(d.id); hold.B = d.p.slice(); await B.until(() => B.evs('duckx').some((e) => e.id === d.id), d.ms + 1500); }
  let cu = null, had = 0; // (a cursed duck can stick to someone else on its way down: up to 3 of them)
  for (let k = 0; k < 3 && !cu; k++) {
    const nc = B.evs('cursed').length;
    if (!await B.until(() => B.evs('cursed').length > nc, 14000)) break;
    const cz = B.evs('cursed').pop(); had = pileB();
    hold.B = cz.p.slice();
    await B.until(() => B.evs('curse').some((e) => e.id === B.id), cz.ms + 4000);
    cu = B.evs('curse').find((e) => e.id === B.id) || null;
  }
  ok(!!cu, 'a cursed duck came down on B');
  ok(cu && cu.n === Math.floor((cu.pile + cu.n) / 2) && cu.pile + cu.n >= 2, `the cursed duck halved B's pile (${cu && cu.pile + cu.n} -> ${cu && cu.pile}; ${had} when it was spotted)`);
  clearInterval(tick);
  ok(await W.until(() => W.evs('res').some((e) => e.id === 'duckcatch' && e.fmt === 'ffa'), 100000), 'duck catch ended');
  const r = W.evs('res').find((e) => e.id === 'duckcatch' && e.fmt === 'ffa'), sc = r.place.map((i) => r.x.pile[i] || 0);
  ok(sc.every((v, k) => k === 0 || sc[k - 1] >= v), `places go by ducks: ${sc.join(' ')}`);
  const errs = errorsIn(S.log());
  ok(!errs.length, 'no server errors' + (errs.length ? ': ' + errs.slice(0, 3).join(' | ') : ''));
  for (const c of [W, A, B]) c.ws.close();
  S.stop();
}

// ---------------------------------------------------------------- duck catch 2v2: the team total (bots)
async function partDuck2(port) {
  const S = await server(port, { JF_WATCH: '1', JF_BGN_FAST: '20', JF_BGN_ROUNDS: '4', JF_BGN_MG: 'duckcatch', JF_BGN_FMT: '2v2', JF_BGN_MGTIME: '25' });
  const W = await client(port, 'watchD', OFF(5));
  ok(await W.until(() => W.evs('res').length, 90000), 'a bots-only 2v2 duck catch ended');
  const r = W.evs('res')[0], pay = new Map(r.pay), tot = r.sides.map((side) => sum(side.map((i) => r.x.pile[i] || 0)));
  ok(r.fmt === '2v2' && r.sc && r.sc[0] === tot[0] && r.sc[1] === tot[1], `the team totals decide it (${tot.join(' vs ')})`);
  ok(tot[0] === tot[1] ? r.winSide === -1 : r.winSide === (tot[0] > tot[1] ? 0 : 1), 'the bigger pile wins');
  ok(r.sides.every((side, k) => side.every((i) => pay.get(i) === (r.winSide === -1 ? 4 : r.winSide === k ? 8 : 1))), '+8 / +1 by side');
  ok(W.evs('duckx').filter((e) => e.by).length >= 6, `bots catch ducks (${W.evs('duckx').filter((e) => e.by).length})`);
  const errs = errorsIn(S.log());
  ok(!errs.length, 'no server errors' + (errs.length ? ': ' + errs.slice(0, 3).join(' | ') : ''));
  W.ws.close(); S.stop();
}

// ---------------------------------------------------------------- the big guy
async function partBigGuy(port) {
  const S = await server(port, { JF_WATCH: '1', JF_BGN_FAST: '20', JF_BGN_ROUNDS: '4', JF_BGN_MG: 'bigguy', JF_BGN_MGTIME: '45' });
  const W = await client(port, 'watchG', OFF(5));
  ok(await W.until(() => W.evs('res').length, 90000), 'THE BIG GUY ended');
  const r = W.evs('res')[0], oneId = W.sts.find((s) => s.mg && s.mg.one != null).seats[r.one].id;
  const rigs = W.msgs.filter((m) => m.t === 'rig' && m.k === 'on' && m.id === oneId).length, deaths = W.msgs.filter((m) => m.t === 'kill' && m.v === oneId).length;
  ok(rigs >= 1 && rigs >= deaths && rigs <= deaths + 1, `a fresh rig every life (${rigs} rigs, ${deaths} deaths)`);
  ok(W.msgs.filter((m) => m.t === 'rig' && m.k === 'on').every((m) => m.id === oneId), 'only the leader gets one');
  const kills = r.scores.find((e) => e[0] === r.one)[2];
  ok(r.sc && r.sc[1] === kills * 3, `their kills count x3 (${kills} kills = ${r.sc && r.sc[1]})`);
  ok(r.winSide === (r.sc[1] > r.sc[0] ? 1 : 0), `the side with more wins (${r.sc.join(' vs ')})`);
  const errs = errorsIn(S.log());
  ok(!errs.length, 'no server errors' + (errs.length ? ': ' + errs.slice(0, 3).join(' | ') : ''));
  W.ws.close(); S.stop();
}

// ---------------------------------------------------------------- online: your seat back, and the warm-up map
async function partOnline(port) {
  const S = await server(port, { JF_WATCH: '1', JF_LOBBY_WAIT: '1500', JF_BGN_FAST: '20', JF_BGN_ROUNDS: '3', JF_BGN_MGTIME: '4', JF_BGN_MG: 'hotfloor', JF_BGN_COUPONS: '40' });
  const W = await client(port, 'watchO', { mode: 'bots', cfg: { lobby: 'bgn' } });
  const Bo = await client(port, 'bob', { mode: 'bots', cfg: { lobby: 'bgn' } });
  await sleep(200);
  const A = await client(port, 'alice', { mode: 'bots', cfg: { lobby: 'bgn' } });
  A.auto = true; Bo.auto = true;
  ok(await W.until(() => W.st && W.st.seats && W.st.seats.some((s) => s.name === 'alice') && W.st.seats.some((s) => s.name === 'bob'), 15000), 'bob and alice sit down');
  const i0 = W.st.seats.find((s) => s.name === 'alice').i, ib = W.st.seats.find((s) => s.name === 'bob').i;
  Bo.ws.close();
  ok(await W.until(() => W.st.seats[ib].name === "bob's bot", 4000), "bob left: bob's bot keeps his seat");
  A.ws.close();
  ok(await W.until(() => W.st.seats[i0].name === "alice's bot", 4000), "alice left: alice's bot keeps her seat");
  ok(ib < i0, `(bob's bot sits before alice's: ${ib} < ${i0}, so the first bot seat isn't hers)`);
  const A2 = await client(port, 'alice', { mode: 'bots', cfg: { lobby: 'bgn' } });
  A2.auto = true;
  ok(await W.until(() => W.st.seats[i0].name === 'alice' && !W.st.seats[i0].bot, 30000), 'she came back and took her own seat back');
  ok(W.st.seats[ib].name === "bob's bot", "bob's bot still has bob's seat");
  ok(await W.until(() => W.st.ph === 'done', 120000), 'the game ran to the end');
  const n0 = W.msgs.length;
  ok(await W.until(() => W.msgs.slice(n0).some((m) => m.t === 'lobby'), 30000), 'back to the lobby\'s warm-up');
  const cfg = W.msgs.slice(n0).filter((m) => m.t === 'cfg' && m.cfg).pop();
  if (!cfg) console.log('   (cfg msgs:', JSON.stringify(W.msgs.slice(n0).filter((m) => m.t === 'cfg' || m.t === 'lobby')).slice(0, 400), ')');
  ok(cfg && cfg.cfg.map === 'crate', `the warm-up is on the crate (${cfg && cfg.cfg.map}), not the last minigame's platform`);
  const errs = errorsIn(S.log());
  ok(!errs.length, 'no server errors' + (errs.length ? ': ' + errs.slice(0, 3).join(' | ') : ''));
  for (const c of [W, A2]) c.ws.close();
  S.stop();
}

(async () => {
  const parts = { boss: partBoss, half: partHalf, carts: partCarts, cartwin: partCartWin, peace: partPeace, ducks: partDucks, duck2: partDuck2, bigguy: partBigGuy, online: partOnline };
  let p = base;
  for (const [k, fn] of Object.entries(parts)) {
    if (only.length && !only.includes(k)) continue;
    console.log(`--- ${k}`);
    try { await fn(p); } catch (e) { ok(false, `${k} threw: ${e.stack || e}`); }
    p += 3;
    await sleep(300);
  }
  console.log(fails ? `${fails} FAILED` : 'all ok');
  process.exit(fails ? 1 : 0);
})();
