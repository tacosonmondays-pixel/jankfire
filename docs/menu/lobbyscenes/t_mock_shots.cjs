// the LOBBY_SCENES.md mockups: copy mockup.js to public/js/_lsmock.js (don't commit it), run the server, then
// SP=<dir with pwlock.cjs> PORT=3000 OUT=<dir> NODE_PATH=$(npm root -g) node t_mock_shots.cjs
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await (await b.newContext({ viewport: { width: 1280, height: 720 } })).newPage();
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.addInitScript(() => { localStorage.setItem('jf_giftseen_all', '1'); localStorage.setItem('jankfire', JSON.stringify({ name: 'taco', killcam: false })); });
  await pg.goto('http://localhost:' + process.env.PORT + '/'); await sleep(3000);
  await pg.evaluate(() => { const e = document.getElementById('jank'); e.value = '3'; e.dispatchEvent(new Event('change')); });
  await pg.evaluate(() => document.querySelector('[data-hub="offline"]').click()); await sleep(800);
  await pg.evaluate(() => import('/js/_lsmock.js'));
  await pg.evaluate(() => { const m = import('/js/mechmodel.js'); return m; });
  // let the mech glbs arrive
  await pg.evaluate(async () => { const k = await import('/js/glbkit.js'); k.prefetch(['x_mech_paperplane', 'x_mech_nightshift'], 9); for (let i = 0; i < 60 && !(k.AUTHORED.x_mech_paperplane && k.AUTHORED.x_mech_nightshift); i++) await new Promise((r) => setTimeout(r, 500)); });
  const MODE = { garage: 'isle', warehouse: 'zm', royale: 'br', hangar: 'qp' };
  for (const k of (process.env.KINDS || 'garage,warehouse,royale,hangar').split(',')) {
    await pg.evaluate((m) => document.querySelector(`[data-mode2="${m}"]`).click(), MODE[k]); await sleep(400);
    await pg.evaluate((k) => window.__lsMock(k), k); await sleep(4000);
    await pg.screenshot({ path: `${process.env.OUT}/${k}.jpg`, quality: 85 });
  }
  console.log('errors:', errs);
  await b.close();
})();
