// playwright e2e (WP7). run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_wp7.cjs
// get in the sofa-car, drive, boost (heat), handbrake drift, crash into the lot wall, get out; the car stays where you
// left it after a reload. records a video into $SP/vid
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const PORT = process.env.PORT || 3311, OUT = process.env.SP + '/shots';
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const ctx = await b.newContext({ viewport: { width: 960, height: 540 }, recordVideo: { dir: process.env.SP + '/vid', size: { width: 960, height: 540 } } });
  const pg = await ctx.newPage();
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message + ' ' + (e.stack || '').split('\n')[1]));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.addInitScript(() => { localStorage.setItem('jankfire', JSON.stringify({ name: 'wp7', loadout: { primary: 'ar', secondary: 'pistol', melee: 'knife', item: 'frag' } })); if (!sessionStorage.getItem('w7')) { sessionStorage.setItem('w7', 1); localStorage.removeItem('jfStorySaves'); } });
  const start = async () => { await pg.goto(`http://localhost:${PORT}/?story=1&storydev=1&storytest=1`); await sleep(1500); await pg.click('#storyBtn', { force: true }); await sleep(700); await pg.click('#storyPick .st-btn.yellow', { force: true }); await sleep(4000); };
  await start();
  const ev = (f, a) => pg.evaluate(f, a);
  const st = () => ev(async () => { const { DV } = await import('/js/story/drive.js'); const { ME } = await import('/js/player.js'); const { W } = await import('/js/weapons.js'); const c = DV.car; const h = document.querySelector('.st-hint'); return { driving: !!c, id: DV.id, car: c ? { p: [c.x, c.y, c.z].map((v) => +v.toFixed(1)), v: +Math.hypot(c.vx, c.vz).toFixed(1), h: +c.h.toFixed(2), heat: +c.heat.toFixed(2), hot: c.hot > 0, hp: Math.round(c.hp) } : null, me: ME.pos.map((v) => +v.toFixed(1)), cur: W.cur, hint: h && !h.classList.contains('hidden') ? h.textContent : '' }; });
  let vmax = 0; // the top speed seen during the last hold (sampled)
  const hold = async (keys, ms) => { vmax = 0; for (const k of keys) await pg.keyboard.down(k); const t0 = Date.now(); while (Date.now() - t0 < ms) { await sleep(100); const v = await ev(async () => { const { DV } = await import('/js/story/drive.js'); return DV.car ? Math.hypot(DV.car.vx, DV.car.vz) : 0; }); vmax = Math.max(vmax, v); } for (const k of keys) await pg.keyboard.up(k); };
  // walk up to the sofa-car (parked at 10, 0, 12)
  await ev(async () => { const { ME } = await import('/js/player.js'); ME.pos = [-36, 0.1, 33.5]; ME.yaw = 0; });
  await sleep(600);
  console.log('near', JSON.stringify(await st()));
  await pg.screenshot({ path: `${OUT}/w7_sofa.png` });
  await hold(['KeyF'], 80); await sleep(700);
  const s0 = await st(); console.log('in', JSON.stringify(s0));
  // turn it round to face the long way across the lot (-z: 50 m to the north wall); heading isn't something the sim polices
  // find a clear lane across the lot (no box taller than a kerb within 2.5 m of x, z from 34 to -37) and put the car at its
  // south end facing north. (one hop, before the first update: the sim's teleport check is per update, and this is the start)
  const lane = await ev(async () => { const { BOXES } = await import('/shared/map.js'); for (let x = -36; x <= 36; x += 0.5) { if (!BOXES.some((b) => b.max[1] > 0.7 && b.max[0] > x - 2.5 && b.min[0] < x + 2.5 && b.max[2] > -37 && b.min[2] < 34)) return x; } return null; });
  console.log('clear lane at x =', lane);
  await ev(async () => { const { ME } = await import('/js/player.js'); ME.yaw = 0; }); // (the sofa-car is parked at the south end of that lane, facing north)
  await hold(['KeyW'], 1400); const s1 = await st(); console.log('drove', JSON.stringify(s1), 'top speed', vmax.toFixed(1)); const v1 = vmax;
  await pg.screenshot({ path: `${OUT}/w7_drive.png` });
  await hold(['KeyW', 'ShiftLeft'], 1100); const s2 = await st(); console.log('boost', JSON.stringify(s2), 'top speed', vmax.toFixed(1), 'faster:', vmax > v1);
  await pg.screenshot({ path: `${OUT}/w7_boost.png` });
  // handbrake drift: how far the velocity points away from the nose
  await hold(['KeyW', 'KeyD', 'Space'], 450);
  const slip = await ev(async () => { const { DV } = await import('/js/story/drive.js'); const c = DV.car; const vf = c.vx * Math.sin(c.h) + c.vz * Math.cos(c.h), vl = c.vx * Math.cos(c.h) - c.vz * Math.sin(c.h); return { slipDeg: Math.round(Math.abs(Math.atan2(vl, vf)) * 180 / Math.PI), v: +Math.hypot(c.vx, c.vz).toFixed(1) }; });
  console.log('drift', JSON.stringify(slip));
  await pg.screenshot({ path: `${OUT}/w7_drift.png` });
  // the sim's view of the car (it checked every update)
  const simCar = await ev(async () => { const { G } = await import('/js/ctx.js'); return new Promise((res) => { G.story.on('saved', (m) => res(m.save.data.cars)); G.story.save('test'); }); });
  console.log('sim car', JSON.stringify(simCar).slice(0, 120));
  // ram the wall: keep boosting until something gives (hp drops / thrown out)
  const hp0 = (await st()).car.hp;
  await hold(['KeyW', 'ShiftLeft'], 3000); const s4 = await st(); console.log('wall', JSON.stringify(s4), 'hp', hp0, '->', s4.car ? s4.car.hp : 'thrown out');
  await pg.screenshot({ path: `${OUT}/w7_crash.png` });
  if (s4.driving) { await hold(['KeyF'], 80); await sleep(600); }
  const s5 = await st(); console.log('out', JSON.stringify(s5));
  // reload: the car stays where it was left
  await pg.keyboard.press('KeyB'); await sleep(800); await pg.click('#quit', { force: true }); await sleep(1000);
  await start();
  const back = await ev(async () => { const { DV } = await import('/js/story/drive.js'); return [...DV.meshes.values()].map((x) => ({ ty: x.c.ty, p: x.c.p.map((v) => +v.toFixed(1)) })); });
  console.log('after reload', JSON.stringify(back));
  console.log('ERRORS', errs.length, errs.slice(0, 8).join('\n'));
  await ctx.close(); await b.close();
})();
