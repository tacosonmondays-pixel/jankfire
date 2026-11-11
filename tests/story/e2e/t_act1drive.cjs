// playwright e2e: m02's drive in a real car, the way a player does it: the real keys (F to get in, WASD steered at the
// road by a path follower) from the sedan waiting on the lane above the market, along the lane, down the slip road and
// round the Ring Road's foot. The "drive the soup to the gut border" zone must fire from the driver's seat. The rest of
// the road (the Unpaid's jump over the collapse, up the hill, into the Gut, Peristalsis Avenue, down to the gate) is
// driven with the same car physics in tests/story/act1drive.test.mjs (a headless browser steers too late for the tight
// turn onto the deck between the dead cars: each round trip is a few hundred ms).
// run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_act1drive.cjs
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const skipIntro = require('./skipintro.cjs');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const PORT = process.env.PORT || 3311;
// [x, y, z, name]: the route, waypoint by waypoint (y is only for the report)
const ROUTE = [
  [-60, 4, 227, 'the lane east'], [30, 4, 227, 'past the gym terrace'], [96, 4, 227, 'the slip road'], [157, 2, 227, 'down the slip road'],
  [160, 1, 234, 'the bend south'], [160, 0, 245, 'on the ramp'], [165, 0, 248, 'round the deck end'], [176, 0, 248, 'along the foot (THE RING ROAD zone)'],
];

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 640, height: 360 } });
  const errs = []; pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message));
  await pg.addInitScript(() => { localStorage.setItem('jf_giftseen_all', '1'); localStorage.setItem('jankfire', JSON.stringify({ name: 'drive', jank: 0 })); if (!sessionStorage.getItem('d')) { sessionStorage.setItem('d', 1); localStorage.removeItem('jfStorySaves'); } });
  await pg.goto(`http://localhost:${PORT}/?story=1&fresh=1`); await sleep(2000);
  await pg.click('#storyBtn', { force: true }); await sleep(700); await pg.click('#storyPick .st-btn.yellow', { force: true }); await sleep(9000);
  await skipIntro(pg); await pg.mouse.click(320, 180); await sleep(300);
  const ev = (f, a) => pg.evaluate(f, a);
  await ev(async () => { const { G } = await import('/js/ctx.js'); const r = G.renderer, o = r.render.bind(r); r.render = (sc, c) => { if (!window.__noDraw) o(sc, c); }; window.__noDraw = true; });
  // put the story on m02's drive step (the steps before it are the rehearsal's fakes: the playthrough covers them), with the soup
  for (let i = 0; i < 40; i++) {
    const at = await ev(() => { const o = window.JF_STORY.S.quests.objectives().find((x) => x.kind === 'main'); return o ? o.quest + '.' + o.step : ''; });
    if (at === 'm02_sauce_run.drive') break;
    await ev(async () => { const sc = await import('/js/story/scene.js'), tk = await import('/js/story/talk.js'); if (sc.playing()) sc.skipScene(); if (tk.talking()) tk.endTalk(); });
    await pg.keyboard.down('Shift'); await pg.keyboard.down('KeyR'); await sleep(60); await pg.keyboard.up('KeyR'); await pg.keyboard.up('Shift'); await sleep(500);
  }
  const zones = [];
  await ev(() => { const S = window.JF_STORY.S, e0 = S.emit.bind(S); window.__zones = []; S.emit = (e) => { if (e.type === 'reach') window.__zones.push(e.zone); return e0(e); }; });
  // (the drive step opens Lumps' car-ride talk: close it, or F is "next line")
  for (let i = 0; i < 5; i++) { await ev(async () => { const sc = await import('/js/story/scene.js'), tk = await import('/js/story/talk.js'); if (sc.playing()) sc.skipScene(); if (tk.talking()) tk.endTalk(); }); await sleep(400); }
  // the market sedan: stand by it, F
  await ev(async () => { const { ME } = await import('/js/player.js'); ME.pos = [-110, 4.3, 224.4]; ME.vel = [0, 0, 0]; }); await sleep(1500);
  await pg.keyboard.down('KeyF'); await sleep(80); await pg.keyboard.up('KeyF'); await sleep(1500);
  const inCar = await ev(async () => (await import('/js/story/drive.js')).driving());
  console.log('in the Sauce Run car:', inCar);
  if (!inCar) { console.log('ERRORS', errs.join('\n')); await b.close(); return; }
  const held = new Set(); const hold = async (k, on) => { if (on && !held.has(k)) { held.add(k); await pg.keyboard.down(k); } else if (!on && held.has(k)) { held.delete(k); await pg.keyboard.up(k); } };
  // a path follower: the route as points every 3 m; steer at the point 9 m ahead of the nearest one, and slow for the
  // bends coming up (cars turn wide at speed). each named waypoint is reported when the car gets near it
  const P = []; const name = []; let from = [-110, 4, 226.5];
  for (const [x, y, z, nm] of ROUTE) { const L = Math.hypot(x - from[0], z - from[2]), n = Math.max(1, Math.ceil(L / 3)); for (let i = 1; i <= n; i++) { P.push([from[0] + (x - from[0]) * i / n, 0, from[2] + (z - from[2]) * i / n]); name.push(i === n ? nm : null); } from = [x, y, z]; }
  let dbg = 0; const rows = []; let k = 0, best = 0, bestT = Date.now(), t0 = Date.now(), stuckAt = null, segT = Date.now();
  const turnAhead = (i) => { let m = 0; for (let j = i; j < Math.min(P.length - 2, i + 6); j++) { const a = Math.atan2(P[j + 1][0] - P[j][0], P[j + 1][2] - P[j][2]), b = Math.atan2(P[j + 2][0] - P[j + 1][0], P[j + 2][2] - P[j + 1][2]); m = Math.max(m, Math.abs(Math.atan2(Math.sin(a - b), Math.cos(a - b)))); } return m; };
  while (k < P.length && Date.now() - t0 < 600000) {
    const c = await ev(async () => { const { DV } = await import('/js/story/drive.js'); const c = DV.car; return c ? [c.x, c.y, c.z, c.h, Math.hypot(c.vx, c.vz)] : null; });
    if (!c) { stuckAt = 'fell out of the car at ' + k; break; }
    for (let j = k; j < Math.min(P.length, k + 12); j++) if (Math.hypot(P[j][0] - c[0], P[j][2] - c[2]) < 4.5) { for (let q = k; q <= j; q++) if (name[q]) { rows.push(name[q]); console.log(`reached ${name[q].padEnd(46)} ${((Date.now() - segT) / 1000).toFixed(0)}s at ${JSON.stringify(c.slice(0, 3).map((v) => +v.toFixed(1)))}`); segT = Date.now(); } k = j + 1; }
    if (k > best) { best = k; bestT = Date.now(); }
    if (Date.now() - bestT > 20000) { stuckAt = `${name.slice(k).find(Boolean)} (at ${c.slice(0, 3).map((v) => v.toFixed(1))})`; break; }
    let tgt = P[Math.min(P.length - 1, k + 2)]; for (let j = k; j < P.length; j++) { tgt = P[j]; if (Math.hypot(P[j][0] - c[0], P[j][2] - c[2]) > 9) break; }
    let err = Math.atan2(tgt[0] - c[0], tgt[2] - c[2]) - c[3]; err = Math.atan2(Math.sin(err), Math.cos(err));
    const wedged = Date.now() - bestT > 5000 && Date.now() - bestT < 8000; // (no progress: back up a moment)
    const cap = Math.abs(err) > 0.6 ? 6 : turnAhead(k) > 0.5 ? 10 : 24;
    await hold('KeyW', !wedged && c[4] < cap); await hold('KeyS', wedged || c[4] > cap + 6);
    await hold('KeyA', (wedged ? -err : err) > 0.06); await hold('KeyD', (wedged ? -err : err) < -0.06);
    if (process.env.DEBUG && (dbg = (dbg || 0) + 1) % 5 === 0 && k >= Number(process.env.DEBUG)) console.log('  dbg k', k, 'car', c.map((v) => +v.toFixed(2)).join(','), 'tgt', tgt.map((v) => +v.toFixed(1)).join(','), 'err', err.toFixed(2), 'keys', [...held].join(''));
    await sleep(70);
  }
  for (const key of [...held]) await hold(key, false);
  if (k >= P.length) console.log('END OF THE ROUTE');
  else console.log('STUCK before', stuckAt);
  const z = await ev(() => window.__zones);
  const step = await ev(() => { const o = window.JF_STORY.S.quests.objectives().find((x) => x.kind === 'main'); return o ? o.quest + '.' + o.step : ''; });
  console.log('zones fired from the car:', [...new Set(z)].join(' '));
  console.log('quest now at:', step);
  console.log('ERRORS', errs.length, errs.slice(0, 5).join('\n'));
  await b.close();
})();
