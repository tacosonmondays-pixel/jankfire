// walkable garage: open BATTLE ISLAND offline, walk forward/turn, hop in the mech and stomp, hop out, swap at the terminal
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const OUT = process.env.OUT, [W, H] = (process.env.SIZE || '1280x720').split('x').map(Number), J = Number(process.env.JANK ?? 3);
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await (await b.newContext({ viewport: { width: W, height: H } })).newPage();
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.addInitScript((j) => { localStorage.setItem('jf_giftseen_all', '1'); localStorage.setItem('jankfire', JSON.stringify({ name: 'taco', killcam: false, jank: j })); }, J);
  await pg.goto(`http://localhost:${process.env.PORT}/`); await sleep(2500);
  await pg.evaluate((j) => { const e = document.getElementById('jank'); e.value = String(j); e.dispatchEvent(new Event('change')); }, J);
  await pg.evaluate(() => document.querySelector('[data-hub="offline"]').click());
  await pg.evaluate(async () => { const k = await import('/js/glbkit.js'); k.prefetch(['x_mech_paperplane', 'x_mech_nightshift', 'x_lobby_gantry'], 9); for (let i = 0; i < 60 && !(k.AUTHORED.x_mech_paperplane && k.AUTHORED.x_mech_nightshift && k.AUTHORED.x_lobby_gantry); i++) await new Promise((r) => setTimeout(r, 500)); });
  await pg.evaluate(() => document.querySelector('[data-mode2="isle"]').click());
  for (let i = 0; i < 40; i++) { if (await pg.evaluate(() => !!document.querySelector('#lsTags .ls-swap'))) break; await sleep(250); }
  await sleep(2500);
  const info = () => pg.evaluate(async () => (await import('/js/lobbyscenes/index.js')).lobbySceneInfo());
  console.log('info', JSON.stringify(await info()));
  await pg.screenshot({ path: `${OUT}/w0_${J}_${W}.jpg`, quality: 85 });
  const hold = async (key, ms) => { await pg.keyboard.down(key); await sleep(ms); await pg.keyboard.up(key); };
  // walk back toward the camera (out to the pad), turn the camera by dragging
  await hold('KeyS', 2500); await pg.screenshot({ path: `${OUT}/w1.jpg`, quality: 85 });
  await pg.mouse.move(640, 400); await pg.mouse.down(); await pg.mouse.move(900, 380, { steps: 8 }); await pg.mouse.up(); await sleep(400);
  await pg.screenshot({ path: `${OUT}/w2.jpg`, quality: 85 });
  if (process.env.FULL) {
    // back to the bay and hop in
    await pg.evaluate(async () => { const m = await import('/js/lobbyscenes/index.js'); }); 
    await pg.evaluate(() => { const w = window.__lsWalk; });
  }
  console.log('errors:', JSON.stringify(errs));
  await b.close();
})();
