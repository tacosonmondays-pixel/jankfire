// BOARD GAME NIGHT over plain ws (server/bgn.js, docs/party/DESIGN.md). starts its own servers, each with its own
// JF_BGN_* knobs, and checks: a whole bots-only game runs to a winner (every phase, payouts by format, coupons add up,
// duel stakes conserved); dice and moves come from the server; every board message drops junk (wrong seat, wrong
// question, NaN, '__proto__', out of range, roll spam); the bakery and store prices hold; a duel starts when you land on
// someone; the bench keeps sitting-out seats dead; a human leaving mid-turn and mid-minigame hands the seat to a bot with
// the same coupons, bread and bag (online lobby); minigames 1-10 each start on their map and return to the board with pay.
//   node tests/bgn_ws.cjs [basePort=3400] [part ...]   (parts: game human duel leave pub minis)
const { spawn } = require('child_process');
const path = require('path');
const WS = require('ws');
const ROOT = path.join(__dirname, '..');
const base = Number(process.argv[2]) || 3400;
const only = process.argv.slice(3);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0;
const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };

const SERVERS = []; // (all killed on the way out, even when a part throws)
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
  const c = { ws, name, id: 0, st: null, sts: [], ev: [], alive: new Map(), spawns: 0, msgs: [], closed: false };
  ws.on('message', (d) => {
    const m = JSON.parse(d);
    c.msgs.push(m); if (c.msgs.length > 4000) c.msgs.splice(0, 2000);
    if (m.t === 'welcome') c.id = m.id;
    if (m.t === 'bg') { if (m.k === 'st') { c.st = m.s; c.sts.push(m.s); } else c.ev.push(m); }
    if (m.t === 'sn') for (const r of m.p) c.alive.set(r[0], r[11]);
    if (m.t === 'spawn') c.spawns++;
  });
  ws.on('close', () => { c.closed = true; });
  ws.on('error', () => {});
  c.send = (o) => { if (ws.readyState === 1) ws.send(JSON.stringify(o)); };
  c.bg = (o) => c.send({ t: 'bg', ...o });
  c.until = (pred, ms = 30000) => new Promise((res) => { const t0 = Date.now(); const iv = setInterval(() => { let v = false; try { v = pred(); } catch { v = false; } if (v || Date.now() - t0 > ms) { clearInterval(iv); res(!!v); } }, 15); });
  c.seat = () => c.st && c.st.seats.find((s) => s.id === c.id);
  c.asked = (k) => { const s = c.seat(); return !!(s && c.st.ask && c.st.ask.seat === s.i && c.st.ask.k === k); };
  c.evs = (k) => c.ev.filter((e) => e.k === k);
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'join', name, ...join }); res(c); }));
}
const OFF = (rounds) => ({ mode: 'bots', cfg: { priv: true, game: 'bgn', map: 'crate', bots: 3, rounds } });
const rankOf = (seats) => seats.slice().sort((a, b) => b.b - a.b || b.c - a.c || a.i - b.i);

// ---------------------------------------------------------------- a whole bots-only game
async function partGame(port) {
  const S = await server(port, { JF_WATCH: '1', JF_BGN_FAST: '20', JF_BGN_ROUNDS: '4', JF_BGN_MGTIME: '6', JF_BGN_COUPONS: '30' });
  const W = await client(port, 'watchA', OFF(5));
  const done = await W.until(() => W.evs('cere').length && W.sts.some((s) => s.ph === 'done'), 200000); // (the ceremony event goes out just before the 'done' state: wait for both)
  ok(done, 'a bots-only game (4 rounds) runs to the end');
  const phs = new Set(W.sts.map((s) => s.ph));
  ok(['intro', 'dibs', 'turn', 'roll', 'move', 'land', 'mgintro', 'mg', 'mgres', 'done'].every((p) => phs.has(p)), 'it went through every phase: ' + [...phs].join(' '));
  ok(W.sts.some((s) => s.lc), 'LAST CALL came round');
  ok(W.evs('house').length === 1, 'last place picked a house rule');
  const fin = W.evs('cere')[0] && W.evs('cere')[0].final;
  ok(fin && fin.place.length === 4 && fin.win === fin.place[0][0], 'there is a winner, and 4 places');
  const last = W.sts.filter((s) => s.ph === 'done').pop();
  if (fin && last) {
    const top = rankOf(last.seats)[0];
    ok(last.seats[fin.win].b === top.b && last.seats[fin.win].c === top.c, 'the winner has the most golden bread (coupons break ties)');
    for (const s of last.seats) { const sum = 30 + W.evs('cash').filter((e) => e.seat === s.i).reduce((a, e) => a + e.d, 0); if (sum !== s.c) ok(false, `seat ${s.i}: cash events add up to ${sum}, it has ${s.c}`); }
    ok(true, 'every coupon change was an event with a reason (they add up to every seat\'s coupons)');
  }
  ok(W.evs('cash').filter((e) => e.why === 'duel').reduce((a, e) => a + e.d, 0) === 0, `duel stakes are conserved (${W.evs('dwin').length} duels won)`);
  ok(W.evs('cash').every((e) => typeof e.why === 'string' && Number.isInteger(e.d)), 'every cash event has a reason');
  // payouts by format, and who's on which side
  let checked = 0;
  for (const r of W.evs('res')) {
    const pay = new Map(r.pay || []);
    if (r.fmt === 'ffa') ok([10, 6, 3, 1].every((v, k) => pay.get(r.place[k]) === v), `ffa ${r.id}: 10/6/3/1 by place`);
    else if (r.fmt === '2v2') ok(r.sides.every((side, k) => side.every((i) => pay.get(i) === (r.winSide === -1 ? 4 : r.winSide === k ? 8 : 1))), `2v2 ${r.id}: winners +8, losers +1 (tie: +4)`);
    else if (r.fmt === '3v1') ok(r.winSide === 1 ? pay.get(r.one) === 15 && pay.size === 1 : r.sides[0].every((i) => pay.get(i) === 5) && !pay.has(r.one), `3v1 ${r.id}: the leader +15 or the three +5`);
    else if (r.fmt === 'boss') ok(r.seats.every((i) => pay.get(i) === (r.winSide === 0 ? 8 + (i === r.mvp ? 5 : 0) : 2)), `boss ${r.id}: +8 each and the MVP +5, or the pity +2`); // (bosses are on since PR 3: halftime is one)
    else continue;
    checked++;
  }
  ok(checked >= 4, `every round minigame paid out (${checked})`);
  // sides: 3v1's one is the leader, 2v2 is 1st+4th vs 2nd+3rd (from round 2)
  const mgSt = W.sts.filter((s, k) => s.ph === 'mgintro' && (k === 0 || W.sts[k - 1].ph !== 'mgintro'));
  for (const s of mgSt) {
    const mg = s.mg, rk = rankOf(s.seats);
    if (mg.fmt === '3v1') ok(rk[0].b === s.seats[mg.one].b && rk[0].c === s.seats[mg.one].c, `round ${s.round} 3v1: the one is the leader (seat ${mg.one})`);
    if (mg.fmt === '2v2' && s.round > 1) ok(mg.sides[0].includes(rk[0].i) && mg.sides[0].includes(rk[3].i), `round ${s.round} 2v2: 1st + 4th vs 2nd + 3rd`);
  }
  const errs = errorsIn(S.log());
  ok(!errs.length, 'no server errors' + (errs.length ? ': ' + errs.slice(0, 3).join(' | ') : ''));
  W.ws.close(); S.stop();
}

// ---------------------------------------------------------------- a human: junk, dice, path, bakery, store, off-turn
async function partHuman(port) {
  const S = await server(port, { JF_BGN_FAST: '10', JF_BGN_DIE: '6,5,4,3,6,1,1,2', JF_BGN_BAKERY: '3', JF_BGN_COUPONS: '27', JF_BGN_ROUNDS: '4', JF_BGN_MGTIME: '4', JF_BGN_MG: 'brawl' });
  const H = await client(port, 'kevin', OFF(5));
  ok(await H.until(() => H.asked('roll'), 15000), 'dibs: the 6 goes first, and it is asked to roll');
  const me = H.seat();
  ok(me && me.i === 0 && me.c === 27 && me.at === 0, 'seat 0, 27 coupons, on the box lid');
  // junk while it's our roll
  const junk = [{}, { k: '__proto__' }, { k: 'constructor' }, { k: 7 }, { k: null }, { k: ['roll'] }, { k: 'use', it: '__proto__' }, { k: 'use', it: 'lasso', to: 1 }, { k: 'use', it: 'peel' },
    { k: 'path', i: 0 }, { k: 'bread', yes: true }, { k: 'buy', it: 'peel' }, { k: 'stake', s: 'coupons' }, { k: 'who', seat: 1 }, { k: 'house', i: 0 }, { k: 'roll', x: [[[[[[[[1]]]]]]]] }, { k: 'step', to: 30 }, { k: 'move', n: 6 }];
  for (const j of junk) H.bg(j);
  await sleep(1100);
  ok(H.asked('roll') && !H.evs('roll').length && H.seat().at === 0, 'junk dropped (wrong question, NaN, __proto__, made-up moves, too deep)');
  ok(H.st.ask.left > 0, 'still our roll');
  H.send({ t: 'bg', k: 'roll', v: 1, seat: 2 }); // a seat and a die value of our own: both ignored, but it's still a roll
  await sleep(400);
  const rolls = H.evs('roll');
  ok(rolls.length === 1 && rolls[0].seat === 0 && rolls[0].v[0] === 6, 'the roll is the server\'s (6 from JF_BGN_DIE, not the client\'s 1)');
  for (let k = 0; k < 10; k++) H.bg({ k: 'roll' }); // spam
  // the bakery on plate 3: BUY GOLDEN BREAD? 20 COUPONS
  ok(await H.until(() => H.asked('bread'), 8000), 'passing the bakery stops you: buy golden bread?');
  ok(H.evs('roll').filter((e) => e.seat === 0).length === 1, 'roll spam did nothing');
  for (const j of [{ k: 'bread', yes: 'yes' }, { k: 'bread', yes: 1 }, { k: 'bread' }, { k: 'path', i: 0 }]) H.bg(j);
  await sleep(1100);
  ok(H.asked('bread') && H.seat().at === 3, 'bread junk dropped (still asked, still on 3)');
  H.bg({ k: 'bread', yes: true });
  ok(await H.until(() => H.seat().b === 1, 3000) && H.seat().c === 7, 'bought golden bread: -20 coupons exactly, +1 bread');
  ok(await H.until(() => H.evs('bakery').length, 3000) && H.st.bakery !== 3, 'the bakery moved after the sale');
  // fork A at 5: LOOP or CREASE
  ok(await H.until(() => H.asked('path'), 8000) && H.seat().at === 5, 'fork A asks LOOP or CREASE');
  for (const j of [{ k: 'path', i: -1 }, { k: 'path', i: 2 }, { k: 'path', i: 0.5 }, { k: 'path', i: '0' }, { k: 'path', i: null }, { k: 'path', i: NaN }]) H.bg(j);
  await sleep(1100);
  ok(H.asked('path'), 'path junk dropped (-1, 2, 0.5, "0", null, NaN)');
  H.bg({ k: 'path', i: 0 });
  // the corner store on 6
  ok(await H.until(() => H.asked('shop'), 8000) && H.seat().at === 6, 'landed on the corner store (moves are the server\'s: 6 from the lid)');
  const stock = H.st.ask.opts, cost = { peel: 5, sign: 6, cart: 8, fake: 10, lasso: 12 };
  ok(Array.isArray(stock) && stock.length === 3, 'the store has 3 items: ' + stock.join(', '));
  const outOf = ['peel', 'sign', 'cart', 'fake', 'lasso'].find((x) => !stock.includes(x));
  const broke = stock.find((x) => cost[x] > 7);
  for (const j of [{ k: 'buy', it: '__proto__' }, { k: 'buy', it: 'toString' }, { k: 'buy', it: outOf }, { k: 'buy', it: 5 }, { k: 'buy', it: broke }, { k: 'buy' }]) H.bg(j);
  await sleep(1100);
  ok(H.asked('shop') && H.seat().c === 7 && !H.seat().bag.length, `store junk dropped (not in stock: ${outOf}, too dear: ${broke})`);
  const buy = stock.find((x) => cost[x] <= 7);
  H.bg({ k: 'buy', it: buy || null });
  if (buy) ok(await H.until(() => H.seat().bag.includes(buy), 3000) && H.seat().c === 7 - cost[buy], `bought ${buy}: -${cost[buy]} coupons exactly`);
  // off-turn: it's the bots' turns now
  ok(await H.until(() => H.st.ask && H.st.ask.seat !== 0, 8000), 'next seat\'s turn');
  for (let k = 0; k < 3; k++) { H.bg({ k: 'roll' }); await sleep(150); }
  ok(H.evs('roll').filter((e) => e.seat === 0).length === 1 && H.seat().at === 6, 'an off-turn roll is rejected');
  ok(await H.until(() => H.evs('res').length, 40000), 'the round\'s minigame was played and paid');
  ok(await H.until(() => H.st.round === 2 && H.st.ph === 'turn', 20000), 'back to the board for round 2');
  const errs = errorsIn(S.log());
  ok(!errs.length, 'no server errors' + (errs.length ? ': ' + errs.slice(0, 3).join(' | ') : ''));
  H.ws.close(); S.stop();
}

// ---------------------------------------------------------------- landing on someone = a duel; the bench
async function partDuel(port) {
  // (4 rounds: round 1 isn't LAST CALL, so no house rule. NO MORE FEES would make space 2 a JANK, and a SWAP there can pull a pawn off the space we aim for)
  const S = await server(port, { JF_BGN_FAST: '10', JF_BGN_DIE: '1,6,5,4,1,1,2,1', JF_BGN_BAKERY: '27', JF_BGN_ROUNDS: '4', JF_BGN_MGTIME: '5', JF_BGN_BOTDUEL: '1', JF_BGN_MG: 'brawl' });
  const H = await client(port, 'linda', OFF(5));
  ok(await H.until(() => H.st && H.st.order.length === 4, 10000) && H.st.order[3] === 0, 'dibs: the 1 goes last');
  // seat 2 lands on seat 1 (both bots, JF_BGN_BOTDUEL plays it out): we sit on the bench
  ok(await H.until(() => H.st.ph === 'mg' && H.st.mg && H.st.mg.fmt === 'duel', 15000), 'two bots on one space: a duel minigame');
  const mg = H.st.mg;
  ok(mg.seats.length === 2 && !mg.seats.includes(0), 'only the two duelists play: ' + mg.seats.join(' v '));
  const sp0 = H.spawns;
  await sleep(600);
  H.send({ t: 'respawn' }); H.send({ t: 'fire', w: 'ar', o: [0, 2, 0], d: [0, 0, 1] }); H.send({ t: 'reset' });
  await sleep(1200);
  const duelIds = mg.seats.map((i) => H.st.seats[i].id), benchIds = H.st.seats.filter((s) => !mg.seats.includes(s.i)).map((s) => s.id);
  ok(benchIds.every((id) => H.alive.get(id) === 0) && H.spawns === sp0, 'the bench stays down (no spawn, respawn ignored)');
  ok(duelIds.some((id) => H.alive.get(id) === 1), 'the duelists are up and fighting');
  ok(await H.until(() => H.evs('res').length >= 1, 20000), 'the duel ended');
  // our turn: roll 1, land on the two bots' space
  ok(await H.until(() => H.asked('roll'), 20000), 'our roll');
  H.bg({ k: 'roll' });
  ok(await H.until(() => H.asked('who'), 8000), 'landed on two pawns: pick who to duel');
  const opts = H.st.ask.opts;
  for (const j of [{ k: 'who', seat: 0 }, { k: 'who', seat: 3 }, { k: 'who', seat: String(opts[0]) }, { k: 'who', seat: 1.5 }, { k: 'stake', s: 'bread' }]) H.bg(j);
  await sleep(1100);
  ok(H.asked('who'), 'who junk dropped');
  const before = H.st.seats.map((s) => s.c);
  H.bg({ k: 'who', seat: opts[0] });
  ok(await H.until(() => H.evs('duel').some((e) => e.a === 0), 8000), 'a duel triggers on landing');
  const d = H.evs('duel').find((e) => e.a === 0);
  ok(d.b === opts[0] && d.stake === 'coupons', 'against the one we picked, for coupons (round 1: no bread duels)');
  ok(await H.until(() => H.st.ph === 'mg' && H.st.mg.seats.includes(0), 10000) && await H.until(() => H.spawns > sp0, 8000), 'we play it (unbenched, spawned)');
  ok(await H.until(() => H.evs('res').length >= 2, 30000), 'our duel ended');
  await H.until(() => H.st.ph !== 'mgres', 10000);
  await sleep(300);
  const after = H.st.seats.map((s) => s.c), win = H.evs('dwin').find((e) => e.seat === 0 || e.lose === 0);
  const fx = H.evs('cash').filter((e) => e.seat === 0 && e.why !== 'duel' && H.ev.indexOf(e) > H.ev.indexOf(d)).reduce((a, e) => a + e.d, 0); // (the space we landed on pays too)
  ok(before[0] + before[d.b] === after[0] - fx + after[d.b], `coupons conserved in the duel (${win ? 'won by seat ' + win.seat : 'hung jury'})`);
  const errs = errorsIn(S.log());
  ok(!errs.length, 'no server errors' + (errs.length ? ': ' + errs.slice(0, 3).join(' | ') : ''));
  H.ws.close(); S.stop();
}

// ---------------------------------------------------------------- online lobby; leaving hands the seat to a bot
async function partLeave(port) {
  const S = await server(port, { JF_WATCH: '1', JF_LOBBY_WAIT: '1500', JF_BGN_FAST: '10', JF_BGN_ROUNDS: '3', JF_BGN_MGTIME: '8', JF_BGN_MG: 'brawl', JF_BGN_COUPONS: '40' });
  const W = await client(port, 'watchD', { mode: 'bots', cfg: { lobby: 'bgn' } });
  const A = await client(port, 'alice', { mode: 'bots', cfg: { lobby: 'bgn' } });
  const B = await client(port, 'bob', { mode: 'bots', cfg: { lobby: 'bgn' } });
  ok(await W.until(() => W.st && W.st.seats, 15000), 'the board game night lobby starts the game');
  const sa = () => W.st.seats.find((s) => s.name === 'alice'), sb = () => W.st.seats.find((s) => s.name === 'bob');
  const airOk = (c) => !c.msgs.some((m) => m.t === 'air' && m.on) || c.msgs.some((m) => m.t === 'air' && m.end);
  ok(await A.until(() => airOk(A) && airOk(B), 3000), 'no NEVER LANDED run left on from the lobby\'s start');
  ok(sa() && sb() && W.st.seats.filter((s) => s.bot).length === 2 && !W.st.seats.some((s) => s.name.startsWith('watch')), 'alice and bob sit down, 2 bots fill, the observer doesn\'t');
  // alice leaves on her own turn
  ok(await W.until(() => W.st.ask && W.st.ask.seat === sa().i, 60000), 'alice\'s turn');
  const a0 = JSON.parse(JSON.stringify(sa()));
  A.ws.close();
  ok(await W.until(() => W.st.seats[a0.i].bot === 1, 3000), 'alice left: a bot took her seat at once');
  const s = W.st.seats[a0.i];
  ok(s.name === "alice's bot" && s.c === a0.c && s.b === a0.b && JSON.stringify(s.bag) === JSON.stringify(a0.bag), 'named after her, same coupons, bread and bag');
  ok(await W.until(() => !W.st.ask || W.st.ask.seat !== a0.i || W.st.ph !== 'turn', 4000), 'mid-choice: the bot answers right away');
  // bob leaves mid-minigame
  ok(await W.until(() => W.st.ph === 'mg' && W.st.mg && W.st.mg.seats.includes(sb().i), 90000), 'a minigame with bob in it');
  await sleep(800);
  const b0 = JSON.parse(JSON.stringify(sb()));
  B.ws.close();
  ok(await W.until(() => W.st.seats[b0.i].bot === 1, 3000), 'bob left mid-minigame: a bot took his seat');
  const nb = W.st.seats[b0.i];
  ok(nb.c === b0.c && nb.b === b0.b, 'same coupons and bread');
  ok(await W.until(() => W.alive.get(nb.id) === 1, 4000), 'the bot joined the minigame and spawned in');
  ok(W.msgs.filter((m) => m.t === 'streak' && m.reset).length >= 2, 'streaks reset when a minigame starts (not just at the lobby)');
  ok(await W.until(() => W.st.ph === 'mgres' || W.st.ph === 'turn', 30000), 'the minigame finished with the bot');
  const errs = errorsIn(S.log());
  ok(!errs.length, 'no server errors' + (errs.length ? ': ' + errs.slice(0, 3).join(' | ') : ''));
  W.ws.close(); S.stop();
}

// ---------------------------------------------------------------- a public bots room can't be turned into a board
async function partPublic(port) {
  const S = await server(port, { JF_BGN_FAST: '10' });
  const A = await client(port, 'pubA', { mode: 'bots', cfg: { game: 'dm', map: 'crate' } });
  await sleep(1700);
  A.send({ t: 'cfg', game: 'bgn' });
  await sleep(600);
  const B = await client(port, 'pubB', { mode: 'bots', cfg: { game: 'bgn' } });
  await sleep(2500);
  ok(!A.msgs.some((m) => m.t === 'bg') && !A.msgs.some((m) => m.t === 'cfgd' && /Board Game/.test(JSON.stringify(m))), 'cfg game:bgn in a public bots room is refused');
  ok(!A.msgs.some((m) => m.t === 'bg') && !B.msgs.some((m) => m.t === 'bg'), 'a public join asking for bgn gets no board and never pulls the other room onto one');
  const errs = errorsIn(S.log());
  ok(!errs.length, 'no server errors' + (errs.length ? ': ' + errs.slice(0, 3).join(' | ') : ''));
  A.ws.close(); B.ws.close(); S.stop();
}

// ---------------------------------------------------------------- minigames 1-10
const MINIS = { brawl: ['dm', 'crate'], spoons: ['spoons', 'crate'], hotfloor: ['lava', 'platform'], ducks: ['duckrain', 'rooftop'], meat: ['rand', 'crate'],
  oneshot: ['oitc', 'crate'], ladder: ['gun', 'crate'], rvb: ['tdm', 'platform'], tagsale: ['tags', 'platform'], leader: ['inf', 'rooftop'] };
async function oneMini(port, id) {
  const [game, map] = MINIS[id];
  const S = await server(port, { JF_WATCH: '1', JF_BGN_FAST: '20', JF_BGN_ROUNDS: '4', JF_BGN_MGTIME: id === 'leader' ? '12' : '6', JF_BGN_MG: id });
  const W = await client(port, 'watch_' + id, OFF(5));
  let cfgMap = null, roundGame = null;
  const seen = await W.until(() => { for (const m of W.msgs) { if (m.t === 'cfg' || m.t === 'welcome') cfgMap = m.cfg.map; if (m.t === 'round' && m.start && m.game !== 'bgn') roundGame = m.game; } return W.evs('res').length; }, 60000);
  const r = W.evs('res')[0], mgE = W.evs('mg')[0];
  ok(seen && mgE && mgE.id === id && roundGame === game && cfgMap === map, `${id}: ${game} on ${map} (${r ? r.fmt : '?'})`);
  ok(r && r.pay && r.pay.length && r.pay.every(([, d]) => d > 0), `${id}: paid out ${r && JSON.stringify(r.pay)}`);
  ok(await W.until(() => W.st.ph === 'turn' && W.st.round === 2, 20000), `${id}: back to the board`);
  if (id === 'oneshot') { const l = W.msgs.filter((m) => m.t === 'oitcl' && m.list.length).map((m) => Math.max(...m.list.map((x) => x[1]))); ok(l.length && Math.max(...l) === 2, `${id}: 2 lives a seat (this room only)`); }
  if (id === 'ladder') { const g = W.msgs.find((m) => m.t === 'gg' && m.l); ok(g && g.l.length === 6 && g.l[5] === 'knife', `${id}: a 6-rung ladder ending on the spoon: ${g && g.l.join(' ')}`); }
  if (id === 'leader') { const z = W.msgs.find((m) => m.t === 'infect' && m.first), one = mgE && W.sts.find((s) => s.mg && s.mg.one != null); ok(z && one && z.id === one.seats[one.mg.one].id, `${id}: the leader is patient zero`); }
  if (id === 'rvb' || id === 'tagsale') {
    const t = W.msgs.filter((m) => m.t === 'teams' && m.game === game).pop(), st = W.sts.find((s) => s.mg && s.mg.sides);
    const side = (pid) => { const s = st.seats.find((x) => x.id === pid); return s && st.mg.sides[0].includes(s.i) ? 1 : 2; };
    ok(t && st && t.list.length === 4 && t.list.every(([pid, team]) => team === side(pid)), `${id}: 2v2 sides come from the board`);
  }
  const errs = errorsIn(S.log());
  ok(!errs.length, `${id}: no server errors` + (errs.length ? ': ' + errs.slice(0, 2).join(' | ') : ''));
  W.ws.close(); S.stop();
}
async function partMinis(port) {
  const ids = Object.keys(MINIS);
  for (let k = 0; k < ids.length; k += 2) await Promise.all(ids.slice(k, k + 2).map((id, j) => oneMini(port + j, id)));
}

(async () => {
  const parts = { game: partGame, human: partHuman, duel: partDuel, leave: partLeave, pub: partPublic, minis: partMinis };
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
