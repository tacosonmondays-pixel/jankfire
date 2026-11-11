// playwright e2e: m02's drive in a real car, the way a player does it. Gets in the sedan parked above the market (WASD
// through the real keys, steered at a list of waypoints), drives to the Ring Road (m02 "drive the soup to the gut
// border": the zone must fire from the driver's seat), then up the Ring Road (the deck is walled
// in, so the car goes up the deck) to the collapse, over it if it can, into the Gut and down to the gate (m02 "deliver"). Reports every waypoint reached,
// where it got stuck and for how long, and whether the zones fired.
// run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_act1drive.cjs
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const skipIntro = require('./skipintro.cjs');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const PORT = process.env.PORT || 3311;
// [x, y, z, name]: the route, waypoint by waypoint (y is only for the report)
const ROUTE = [
  [-60, 4, 227, 'the lane east'], [30, 4, 227, 'past the gym terrace'], [96, 4, 227, 'the slip road'], [157, 2, 227, 'down the slip road'],
  [160, 1, 234, 'the bend south'], [160, 0, 245, 'on the ramp'], [165, 0, 248, 'round the deck end'], [182, 0, 248, 'THE RING ROAD (zone)'],
  [193, 0, 246, 'the on-ramp'], [188, 2, 222, 'onto the deck'], [188, 10, 140, 'up the Ring Road'], [188, 13, 112, 'to the collapse'],
  [188, 16, 75, 'over the collapse'], [188, 30, -60, 'the climb'], [180, 40, -172, 'the top'], [100, 40, -164, 'the west turn'], [60, 40, -188, 'into the Gut'],
  [-44, 40, -188, 'the rib avenue'], [-44, 40, -60, 'down the avenue'], [-44, 36, -30, 'down the cliff stairs'], [-44, 36, -17, 'THE GATE (zone)'],
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
  const rows = []; let stuckAt = null;
  let prev = [-110, 4, 226.5];
  for (const [x, y, z, name] of ROUTE) {
    const seg = [x - prev[0], z - prev[2]], segL = Math.hypot(seg[0], seg[1]) || 1; prev = [x, y, z];
    const t0 = Date.now(); let best = 1e9, bestT = Date.now(), ok = false, last = null;
    while (Date.now() - t0 < 60000) {
      const c = await ev(async () => { const { DV } = await import('/js/story/drive.js'); const c = DV.car; return c ? [c.x, c.y, c.z, c.h, Math.hypot(c.vx, c.vz)] : null; });
      if (!c) { last = 'fell out of the car'; break; }
      const d = Math.hypot(x - c[0], z - c[2]); last = c;
      if (d < 7 || ((x - c[0]) * seg[0] + (z - c[2]) * seg[1]) / segL < -1 && d < 10) { ok = true; break; } // (close, or driven past it)
      if (d < best - 1) { best = d; bestT = Date.now(); }
      if (Date.now() - bestT > 14000) break; // no progress for 8 s: stuck
      let err = Math.atan2(x - c[0], z - c[2]) - c[3]; err = Math.atan2(Math.sin(err), Math.cos(err));
      const back = Date.now() - bestT > 3000 && Date.now() - bestT < 5500 && c[4] < 3; // (2.5 s of reverse, then try again) // wedged: reverse a moment
      await hold('KeyW', !back && c[4] < (Math.abs(err) > 0.5 ? 9 : 22)); await hold('KeyS', back); // (a sane speed: slow into the turns)
      await hold('KeyA', (back ? -err : err) > 0.08); await hold('KeyD', (back ? -err : err) < -0.08);
      await sleep(90);
    }
    for (const k of [...held]) await hold(k, false);
    const p = last && last.map ? last.slice(0, 3).map((v) => +v.toFixed(1)) : last;
    rows.push({ name, ok, s: ((Date.now() - t0) / 1000).toFixed(0), at: p });
    console.log(`${ok ? 'reached' : 'STUCK  '} ${name.padEnd(28)} ${rows[rows.length - 1].s}s at ${JSON.stringify(p)}`);
    if (!ok) { stuckAt = name; break; }
  }
  const z = await ev(() => window.__zones);
  const step = await ev(() => { const o = window.JF_STORY.S.quests.objectives().find((x) => x.kind === 'main'); return o ? o.quest + '.' + o.step : ''; });
  console.log('zones fired from the car:', [...new Set(z)].join(' '));
  console.log('quest now at:', step, stuckAt ? `(stuck before: ${stuckAt})` : '');
  console.log('ERRORS', errs.length, errs.slice(0, 5).join('\n'));
  await b.close();
})();
