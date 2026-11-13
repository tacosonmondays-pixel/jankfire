// SERVER HONESTY over plain ws (server/honesty.js), on Crate (a 5 m block in the middle, 3 m tall, under a roof slab):
// refused: hitscan / melee / a clubs shockwave through the block, melee / cigarette / leaf blower behind you, a gun you don't hold, one you
// swapped away from a while ago, a second primary in one life, a taser / remote you don't hold, a chicken strike aimed
// 400 m away, a giant duck aimed through the floor, a randomizer hit outside your roll, garbage fields.
// still landing: open shots, peeking past the corner (one edge showing), strafing into cover (both moving), the shotgun
// up close, the sniper at 400 m, a revolver ricochet around the block, swap-and-fire in one frame, fire-then-swap,
// melee at the edge of reach, a shot through scenery (deco), a randomizer hit inside your roll.
// Every "refused" check fails against a server without the honesty pass (JF_ROOT=<old checkout> runs the old one).
// starts its own servers: node tests/honesty_ws.cjs [port]   (the randomizer part uses port + 1)
const WS = require('ws');
const path = require('path');
const { spawn } = require('child_process');
const port = Number(process.argv[2]) || 3841;
const ROOT = process.env.JF_ROOT || path.join(__dirname, '..');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
const srvs = [];
process.on('exit', () => { for (const s of srvs) s.kill(); });

function server(p, env) {
  const s = spawn(process.execPath, ['--max-old-space-size=320', 'server.js'], { cwd: ROOT, env: { ...process.env, PORT: String(p), JF_TRAFFIC: 'off', JF_TRAIN_STREAKS: '1', ...env }, stdio: ['ignore', 'pipe', 'pipe'] });
  s.log = ''; s.stdout.on('data', (d) => { s.log += d; }); s.stderr.on('data', (d) => { s.log += d; });
  srvs.push(s);
  return s;
}
async function up(p) {
  for (let i = 0; i < 80; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${p}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); return true; } catch { await sleep(250); } }
  return false;
}
let PORT = port, nC = 0;
function client(name, extra = {}) {
  const ws = new WS(`ws://localhost:${PORT}/ws`), c = { ws, got: [], id: 0, q: 0, name };
  ws.on('message', (d) => {
    const m = JSON.parse(d);
    if (m.t === 'welcome') { c.id = m.id; c.q = m.q; c.map = m.cfg && m.cfg.map; }
    if (m.t === 'spawn') c.q = m.q;
    if (m.t === 'loadout') c.lo = m.lo;
    if (m.t === 'sn') return;
    c.got.push(m);
    if (c.got.length > 3000) c.got.splice(0, 1000);
  });
  ws.on('error', () => {});
  c.send = (m) => { if (ws.readyState === 1) ws.send(typeof m === 'string' ? m : JSON.stringify(m)); };
  c.place = (p, o = {}) => c.send({ t: 's', q: c.q, p, v: o.v || [0, 0, 0], y: o.y ?? 0, x: o.x ?? 0, w: o.w || 'ar', f: o.f || 0 });
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'join', name: name + (++nC), mode: 'ffa', streaks: ['chickenstrike', 'giantduck', 'spinbot'], ...extra }); setTimeout(() => res(c), 600); }));
}
const eyeAt = (p) => [p[0], p[1] + 1.6, p[2]];
const look = (a, b) => { const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], h = Math.hypot(d[0], d[2]), l = Math.hypot(...d); return { y: Math.atan2(-d[0], -d[2]), x: Math.atan2(d[1], h), d: d.map((v) => Math.round((v / l) * 100) / 100) }; };
const chest = (p) => [p[0], p[1] + 1.1, p[2]];

// a fresh pair (full HP, fresh rate limits, a fresh life), both parked long enough that the spawn teleport has aged out of
// the server's history and spawn protection is over. hold(t) says where everyone is and what A holds at time t
let A = null, B = null;
async function pair() {
  if (A) A.ws.close(); if (B) B.ws.close();
  A = await client('A'); B = await client('B');
}
async function park(ms, at) {
  for (let t = 0; t < ms; t += 50) { const s = at(t); A.place(s.a, s.ao || {}); B.place(s.b, s.bo || {}); await sleep(50); }
}
const dmgs = (w) => B.got.filter((m) => m.t === 'dmg' && m.to === B.id && m.from === A.id && (!w || m.w === w));
const clear = () => { A.got.length = 0; B.got.length = 0; };
// one hitscan / melee case: park, then fire n hits (each with a fresh snapshot first), count A's damage on B
async function shoot(at, w, n = 2, hitExtra = {}, gap = 450) {
  await pair();
  await park(1400, at);
  clear();
  for (let i = 0; i < n; i++) {
    const s = at(1400 + i * gap);
    A.place(s.a, s.ao || {}); B.place(s.b, s.bo || {});
    const L = look(eyeAt(s.a), chest(s.b));
    A.send({ t: 'fire', w, o: eyeAt(s.a), d: L.d, s: [] });
    A.send({ t: 'hit', to: B.id, w, d: hitExtra.d || L.d, n: 1, h: 0, ...hitExtra, ...(hitExtra.d ? { d: hitExtra.d } : {}) });
    await sleep(gap);
  }
  await sleep(250);
  return dmgs(w).length;
}
const facing = (a, b, w, o = {}) => ({ y: look(eyeAt(a), chest(b)).y, x: look(eyeAt(a), chest(b)).x, w, ...o });

(async () => {
  const srv = server(port, { JF_GAME: 'dm', JF_CARD_HAND: 'c9,c9,c9,c9,c9' }); // (every hand: five 9s of clubs, the shockwave)
  if (!(await up(port))) { console.log('server did not start\n' + srv.log); process.exit(1); }
  const host = await client('host');
  host.send({ t: 'cfg', map: 'crate', bots: 0 });
  await sleep(1500);
  ok(true, `room on ${host.map} -> crate (honesty pass: ${ROOT === path.join(__dirname, '..') ? 'this checkout' : ROOT})`);

  // ------------------------------------------------------------ hitscan line of sight
  {
    const a = [0, 0, -8], b = [0, 0, 8];
    ok((await shoot(() => ({ a, b, ao: facing(a, b, 'ar') }), 'ar')) === 0, 'refused: an AR shot through the 3 m block');
  }
  {
    const a = [-6.5, 0, -8], b = [-6.5, 0, 8];
    ok((await shoot(() => ({ a, b, ao: facing(a, b, 'ar') }), 'ar')) >= 2, 'lands: an AR shot down the open side');
  }
  {
    const a = [-3.2, 0, -9], b = [-2.0, 0, 6]; // only B's left edge shows past the block's corner (centre and head hidden)
    ok((await shoot(() => ({ a, b, ao: facing(a, b, 'ar') }), 'ar')) >= 2, 'lands: peeking past the corner (one shoulder edge showing)');
    const b2 = [-1.5, 0, 6]; // all of them behind it
    ok((await shoot(() => ({ a, b: b2, ao: facing(a, b2, 'ar') }), 'ar')) === 0, 'refused: the same corner, B fully behind it');
  }
  {
    const a = [0, 0, 0.5], b = [0, 0, 8]; // A's snapshots put it inside the block, poking out of nothing
    ok((await shoot(() => ({ a, b, ao: facing(a, b, 'ar') }), 'ar')) === 0, 'refused: shooting from inside the block');
  }
  {
    // strafing: A runs along x, B runs from the open into cover; when the hits arrive the server's newest B is hidden,
    // a moment before it wasn't (what A's client drew)
    const at = (t) => {
      const k = Math.max(0, t - 1400) / 1000;
      return { a: [-3.6 - k * 7, 0, -9], ao: { v: [-7, 0, 0], w: 'ar', y: 0.1, x: 0 }, b: [-3.4 + Math.min(k, 0.35) * 7, 0, 6], bo: { v: [k < 0.35 ? 7 : 0, 0, 0] } };
    };
    await pair();
    await park(1400, (t) => at(t));
    clear();
    for (let t = 1400; t < 1800; t += 33) { const s = at(t); A.place(s.a, s.ao); B.place(s.b, s.bo); await sleep(33); } // B ends at x -0.95: hidden
    const s = at(1800), L = look(eyeAt(s.a), chest([-2.6, 0, 6]));
    A.send({ t: 'hit', to: B.id, w: 'ar', d: L.d, n: 1, h: 0 });
    await sleep(400);
    ok(dmgs('ar').length === 1, `lands: strafing, B ducked into cover a few snapshots ago (${dmgs('ar').length})`);
  }
  {
    const a = [-6.5, 0, -3], b = [-6.5, 0, 0];
    await shoot(() => ({ a, b, ao: facing(a, b, 'shotgun') }), 'shotgun', 1, { n: 10 });
    const g = dmgs('shotgun');
    ok(g.length === 1 && g[0].a >= 60, `lands: the shotgun up close, 10 pellets (${g.length} hit${g[0] ? ', ' + g[0].a + ' damage' : ''})`);
  }
  {
    const a = [-200, 1, 20], b = [200, 1, 20]; // 400 m over the void beside the crate: nothing in between
    ok((await shoot(() => ({ a, b, ao: facing(a, b, 'sniper') }), 'sniper', 1)) === 1, 'lands: the sniper at 400 m');
  }
  {
    const a = [-250, 0, 290], b = [-250, 0, 392]; // a 30 m tall toy block (scenery, not a wall: bullets pass) in between
    ok((await shoot(() => ({ a, b, ao: facing(a, b, 'ar') }), 'ar', 1)) === 1, 'lands: through scenery (deco) the client shoots through');
  }
  {
    // revolver ricochet: no straight line from A to B (the block); A bounces it off the low wall's face at z 9.5
    const a = [-6, 0, -6], b = [0, 0, 6], W = [-1, 1.2, 9.5];
    const dl = [chest(b)[0] - W[0], chest(b)[1] - W[1], chest(b)[2] - W[2]], l = Math.hypot(...dl), d = dl.map((v) => Math.round((v / l) * 100) / 100);
    ok((await shoot(() => ({ a, b, ao: { ...facing(a, W, 'revolver') } }), 'revolver', 1, { d })) === 1, 'lands: a revolver ricochet off the wall around the block');
    const dBad = look(eyeAt(a), chest(b)).d; // the same shot claimed straight through
    ok((await shoot(() => ({ a, b, ao: { ...facing(a, W, 'revolver') } }), 'revolver', 1, { d: [-dBad[0], dBad[1], dBad[2]] })) === 0, 'refused: a revolver "ricochet" whose bounce leads nowhere A can see');
  }

  // ------------------------------------------------------------ weapons: held, swapped, loadout
  {
    const a = [-6.5, 0, -8], b = [-6.5, 0, 8];
    ok((await shoot(() => ({ a, b, ao: facing(a, b, 'ar') }), 'sniper', 1)) === 0, 'refused: a sniper hit while holding the AR');
    // swapped away from the pistol 1.2 s ago
    await pair(); await park(1400, (t) => ({ a, b, ao: facing(a, b, t < 200 ? 'pistol' : 'ar') })); clear();
    A.send({ t: 'hit', to: B.id, w: 'pistol', d: look(eyeAt(a), chest(b)).d, n: 1, h: 0 }); await sleep(500);
    ok(dmgs('pistol').length === 0, 'refused: a pistol hit 1.2 s after putting the pistol away');
    // fire then swap: the hit comes in after the snapshot with the new gun
    await pair(); await park(1400, () => ({ a, b, ao: facing(a, b, 'ar') })); clear();
    A.place(a, facing(a, b, 'pistol')); await sleep(120);
    A.send({ t: 'hit', to: B.id, w: 'ar', d: look(eyeAt(a), chest(b)).d, n: 1, h: 0 }); await sleep(400);
    ok(dmgs('ar').length === 1, 'lands: an AR hit 120 ms after swapping to the pistol');
    // swap and fire in one frame: the hit beats the snapshot with the new gun
    await pair(); await park(1400, () => ({ a, b, ao: facing(a, b, 'pistol') })); clear();
    A.send({ t: 'hit', to: B.id, w: 'ar', d: look(eyeAt(a), chest(b)).d, n: 1, h: 0 }); await sleep(40);
    A.place(a, facing(a, b, 'ar')); await sleep(400);
    ok(dmgs('ar').length === 1, 'lands: swap to the AR and fire in the same frame (the hit waits for the snapshot)');
    // ...but not if the snapshot never comes
    await pair(); await park(1400, () => ({ a, b, ao: facing(a, b, 'pistol') })); clear();
    A.send({ t: 'hit', to: B.id, w: 'ar', d: look(eyeAt(a), chest(b)).d, n: 1, h: 0 }); await sleep(100);
    for (let i = 0; i < 6; i++) { A.place(a, facing(a, b, 'pistol')); await sleep(60); }
    A.place(a, facing(a, b, 'ar')); await sleep(300);
    ok(dmgs('ar').length === 0, 'refused: an AR hit while the snapshots keep saying pistol (the late swap is too late)');
    // one primary per life: held the AR past the loadout window, then a sniper appears
    await pair(); await park(7200, () => ({ a, b, ao: facing(a, b, 'ar') })); clear();
    for (let i = 0; i < 4; i++) { A.place(a, facing(a, b, 'sniper')); await sleep(60); }
    A.send({ t: 'hit', to: B.id, w: 'sniper', d: look(eyeAt(a), chest(b)).d, n: 1, h: 0 }); await sleep(400);
    ok(dmgs('sniper').length === 0, 'refused: a sniper (second primary) 7 s into a life spent holding the AR');
    for (let i = 0; i < 4; i++) { A.place(a, facing(a, b, 'ar')); await sleep(60); }
    A.send({ t: 'hit', to: B.id, w: 'ar', d: look(eyeAt(a), chest(b)).d, n: 1, h: 0 }); await sleep(400);
    ok(dmgs('ar').length === 1, 'lands: the AR again in that life');
  }

  // ------------------------------------------------------------ melee
  {
    const a = [-6.5, 0, 0];
    ok((await shoot(() => ({ a, b: [-6.5, 0, -3.1], ao: { y: 0, x: 0, w: 'knife' } }), 'knife', 1)) === 1, 'lands: the knife at the edge of reach (3.1 m, lag)');
    ok((await shoot(() => ({ a, b: [-6.5, 0, 3.5], ao: { y: 0, x: 0, w: 'knife' } }), 'knife', 1)) === 0, 'refused: the knife on someone 3.5 m behind you');
    ok((await shoot(() => ({ a, b: [-6.5, 0, 1.2], ao: { y: 0, x: 0, w: 'knife' } }), 'knife', 1)) === 1, 'lands: the knife on someone right up close behind you (client: any angle under 1.5 m)');
    const a2 = [0, 0, -3.0], b2 = [0, 0, 3.0];
    ok((await shoot(() => ({ a: a2, b: b2, ao: facing(a2, b2, 'bread') }), 'bread', 1)) === 0, 'refused: the bread through the block (6 m, in reach + slack)');
  }

  // ------------------------------------------------------------ cigarette, leaf blower
  {
    const a = [-6.5, 0, 0];
    const cig = async (b, w) => { await pair(); await park(1400, () => ({ a, b, ao: { y: 0, x: 0, w: 'cig' } })); clear(); for (let i = 0; i < 3; i++) { A.send({ t: 'hit', to: B.id, w: 'cig', d: look(eyeAt(a), chest(b)).d }); await sleep(120); } await sleep(300); return dmgs('cig').length; };
    ok((await cig([-6.5, 0, -7])) >= 2, 'lands: the cigarette on someone 7 m in front');
    ok((await cig([-6.5, 0, 6])) === 0, 'refused: the cigarette on someone 6 m behind you');
    const blow = async (b) => { await pair(); await park(1400, () => ({ a, b, ao: { y: 0, x: 0, w: 'blower' } })); clear(); for (let i = 0; i < 3; i++) { A.send({ t: 'push', to: B.id, w: 'blower' }); await sleep(120); } await sleep(300); return B.got.filter((m) => m.t === 'kb' && m.w === 'blower').length; };
    ok((await blow([-6.5, 0, -8])) >= 2, 'lands: the leaf blower on someone 8 m in front');
    ok((await blow([-6.5, 0, 7])) === 0, 'refused: the leaf blower on someone 7 m behind you');
    const a2 = [0, 0, -4], b2 = [0, 0, 5];
    await pair(); await park(1400, () => ({ a: a2, b: b2, ao: { ...facing(a2, b2, 'blower') } })); clear();
    for (let i = 0; i < 3; i++) { A.send({ t: 'push', to: B.id, w: 'blower' }); await sleep(120); } await sleep(300);
    ok(B.got.filter((m) => m.t === 'kb' && m.w === 'blower').length === 0, 'refused: the leaf blower through the block');
  }

  // ------------------------------------------------------------ clubs shockwave (a 9 of clubs: 30 damage, 9 m cone)
  {
    const wave = async (a, b) => {
      await pair(); await park(1400, () => ({ a, b, ao: facing(a, b, 'cards') })); clear();
      A.send({ t: 'fire', w: 'cards', i: 0, o: eyeAt(a), d: look(eyeAt(a), chest(b)).d }); await sleep(600);
      return dmgs('cards').filter((m) => Math.round(m.a) === 30).length;
    };
    ok((await wave([-6.5, 0, -4], [-6.5, 0, 2])) === 1, 'lands: a clubs shockwave on someone 6 m in front');
    ok((await wave([0, 0, -3.4], [0, 0, 3.4])) === 0, 'refused: a clubs shockwave through the block');
  }

  // ------------------------------------------------------------ taser, tv remote
  {
    const a = [-6.5, 0, -4], b = [-6.5, 0, 2];
    const zaps = () => B.got.filter((m) => m.t === 'fx' && m.k === 'zap' && m.id === A.id && (m.l || []).some((l) => l[1] === B.id)).length;
    await pair(); await park(1400, () => ({ a, b, ao: facing(a, b, 'ar') })); clear();
    A.send({ t: 'fire', w: 'taser', d: look(eyeAt(a), chest(b)).d, to: B.id }); await sleep(400);
    ok(zaps() === 0, 'refused: the taser while holding the AR');
    await pair(); await park(1400, () => ({ a, b, ao: facing(a, b, 'taser') })); clear();
    A.send({ t: 'fire', w: 'taser', d: look(eyeAt(a), chest(b)).d, to: B.id }); await sleep(400);
    ok(zaps() === 1, 'lands: the taser held');
    const pauses = () => B.got.filter((m) => m.t === 'fx' && m.k === 'pause' && m.by === A.id && m.id === B.id).length;
    await pair(); await park(1400, () => ({ a, b, ao: facing(a, b, 'ar') })); clear();
    A.send({ t: 'fire', w: 'remote', d: look(eyeAt(a), chest(b)).d, to: B.id, m: 0 }); await sleep(400);
    ok(pauses() === 0, 'refused: the TV remote while holding the AR');
    await pair(); await park(1400, () => ({ a, b, ao: facing(a, b, 'remote') })); clear();
    A.send({ t: 'fire', w: 'remote', d: look(eyeAt(a), chest(b)).d, to: B.id, m: 0 }); await sleep(400);
    ok(pauses() === 1, 'lands: the TV remote held');
  }

  // ------------------------------------------------------------ chicken strike, giant duck
  {
    const a = [-6.5, 0, -6];
    const used = (r) => A.got.filter((m) => m.t === 'chat' && typeof m.m === 'string' && m.m.includes('used ' + r)).length;
    const back = (r) => A.got.filter((m) => m.t === 'streak' && m.earned === r).length;
    const deploy = async (r, at) => { await pair(); await park(1400, () => ({ a, b: [12, 0, 12], ao: { y: 0, x: 0, w: 'ar' } })); clear(); A.send({ t: 'deploy', r, at }); await sleep(500); };
    await deploy('chickenstrike', [-6.5, 0, -14]);
    ok(used('Chicken Strike') === 1, 'lands: a chicken strike on the floor 8 m ahead');
    await deploy('chickenstrike', [393.5, 0, -6]);
    ok(used('Chicken Strike') === 0 && back('chickenstrike') === 1, `refused: a chicken strike aimed 400 m away (back in the tray: ${back('chickenstrike')})`);
    await deploy('giantduck', [-6.5, 0, -12]);
    ok(used('Giant Duck') === 1, 'lands: a giant duck on the floor 6 m ahead');
    await deploy('giantduck', [-6.5, -6, -10]);
    ok(used('Giant Duck') === 0, 'refused: a giant duck aimed through the floor');
    await deploy('giantduck', [0, 1, 5]);
    ok(used('Giant Duck') === 0, 'refused: a giant duck aimed behind the block');
  }

  // ------------------------------------------------------------ garbage
  {
    const a = [-6.5, 0, -8], b = [-6.5, 0, 8];
    await pair(); await park(1400, () => ({ a, b, ao: facing(a, b, 'ar') })); clear();
    const junk = [{ t: 'hit' }, { t: 'hit', to: B.id }, { t: 'hit', to: B.id, w: '__proto__', d: [0, 0, 1] }, { t: 'hit', to: B.id, w: 'constructor' }, { t: 'hit', to: B.id, w: 'ar', d: 'x' },
      { t: 'hit', to: B.id, w: 'ar', d: [NaN, 0, 1] }, { t: 'hit', to: B.id, w: 'ar', d: [1e308, 1e308, 1e308] }, { t: 'hit', to: { a: 1 }, w: 'ar', d: [0, 0, 1] }, { t: 'push', to: B.id, w: 'blower' }, { t: 'push', w: null },
      { t: 'deploy', r: 'chickenstrike', at: [NaN, 0, 0] }, { t: 'deploy', r: 'giantduck', at: 'up' }, { t: 'deploy', r: 'giantduck', at: [1e9, 1e9, 1e9] }, { t: 'fire', w: 'taser', d: null, to: 'x' }, { t: 'fire', w: 'remote', m: 9, d: [0, 0, 0] },
      { t: 's', q: A.q, p: [-6.5, 0, -8], v: [0, 0, 0], y: 'a', x: null, w: '__proto__' }, { t: 's', q: A.q, p: [-6.5, 0, -8], v: [0, 0, 0], y: 0, x: 0, w: 'ar' }];
    for (const m of junk) { A.send(m); await sleep(20); }
    await sleep(400);
    ok(dmgs().length === 0 && !/TypeError|RangeError|uncaught/i.test(srv.log), 'garbage hits, pushes, deploys, fires and snapshots: nothing lands, nothing throws');
    A.place(a, facing(a, b, 'ar')); await sleep(100);
    A.send({ t: 'hit', to: B.id, w: 'ar', d: look(eyeAt(a), chest(b)).d, n: 1, h: 0 }); await sleep(400);
    ok(dmgs('ar').length === 1, 'and a normal hit right after still lands');
  }
  if (A) A.ws.close(); if (B) B.ws.close(); host.ws.close();

  // ------------------------------------------------------------ randomizer: the roll is the loadout
  {
    PORT = port + 1;
    const s2 = server(PORT, { JF_GAME: 'rand' });
    if (!(await up(PORT))) { ok(false, 'randomizer server did not start'); }
    else {
      const h2 = await client('host'); h2.send({ t: 'cfg', map: 'crate', bots: 0 }); await sleep(1500);
      const { WEAPONS } = await import(path.join(ROOT, 'shared/weapons.js'));
      // a life whose roll has a hitscan gun in it (the primary, else the secondary): a few tries
      let lo = {}, mine = null;
      for (let k = 0; k < 8 && !mine; k++) {
        await pair();
        for (let i = 0; i < 20 && !(A.lo && A.lo.primary); i++) await sleep(100);
        lo = A.lo || {};
        mine = ['primary', 'secondary'].map((s) => lo[s]).find((w) => w && WEAPONS[w] && WEAPONS[w].kind === 'hitscan' && !WEAPONS[w].fanHammer) || null;
      }
      const other = ['ar', 'smg', 'minigun', 'sniper', 'pistol'].find((w) => !Object.values(lo).includes(w));
      const a = [-6.5, 0, -8], b = [-6.5, 0, 8];
      ok(!!mine, `randomizer rolled A: ${JSON.stringify(lo)}`);
      await park(1400, () => ({ a, b, ao: facing(a, b, other) })); clear();
      A.send({ t: 'hit', to: B.id, w: other, d: look(eyeAt(a), chest(b)).d, n: 1, h: 0 }); await sleep(400);
      ok(dmgs(other).length === 0, `refused: a randomizer hit with ${other} (not in the roll), even while "holding" it`);
      if (mine) {
        for (let i = 0; i < 4; i++) { A.place(a, facing(a, b, mine)); await sleep(60); }
        A.send({ t: 'hit', to: B.id, w: mine, d: look(eyeAt(a), chest(b)).d, n: 1, h: 0 }); await sleep(400);
        ok(dmgs(mine).length === 1, `lands: a randomizer hit with the rolled ${mine}`);
      }
      h2.ws.close();
      if (/TypeError|RangeError|uncaught/i.test(s2.log)) ok(false, 'randomizer server threw:\n' + s2.log.slice(-800));
    }
  }
  if (/TypeError|RangeError|uncaught/i.test(srv.log)) ok(false, 'server threw:\n' + srv.log.slice(-800));
  console.log(fails ? `\n${fails} FAILED` : '\nall passed');
  process.exit(fails ? 1 : 0);
})();
