// lobby scenes: the hub's start paths still work with a scene up. BATTLE ISLAND (offline, the garage) -> START MATCH:
// the match starts and the scene is gone; quit to the menu, back to the lobby: the scene comes back. QUICK PLAY offline
// (no scene) still starts. screenshots at each graphics preset + a small window. no page errors.
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const OUT = process.env.OUT, MODE = process.env.MODE || 'isle';
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const errs = [], res = [];
  const page = async (W, H, j) => {
    const pg = await (await b.newContext({ viewport: { width: W, height: H } })).newPage();
    pg.on('pageerror', (e) => errs.push(`${W}x${H} j${j}: ${e.message}`));
    await pg.addInitScript((j) => { localStorage.setItem('jf_giftseen_all', '1'); localStorage.setItem('jankfire', JSON.stringify({ name: 'taco', killcam: false, jank: j })); }, j);
    await pg.goto(`http://localhost:${process.env.PORT}/`); await sleep(2500);
    await pg.evaluate((j) => { const e = document.getElementById('jank'); e.value = String(j); e.dispatchEvent(new Event('change')); }, j);
    return pg;
  };
  const on = (pg) => pg.evaluate(async () => (await import('/js/lobbyscenes/index.js')).lobbySceneOn());
  const isle = async (pg) => { await pg.evaluate(() => document.querySelector('[data-hub="offline"]').click()); await sleep(500); await pg.evaluate((m) => document.querySelector('[data-mode2="' + m + '"]').click(), MODE); for (let i = 0; i < 60 && !(await on(pg)); i++) await sleep(250); await sleep(3500); };
  // presets + sizes: a picture each
  for (const [W, H, j] of [[1280, 720, 3], [1280, 720, 2], [1280, 720, 0], [960, 540, 3]]) {
    const pg = await page(W, H, j); await isle(pg);
    await pg.screenshot({ path: `${OUT}/${MODE}_preset_${j}_${W}.jpg`, quality: 85 });
    if (j === 3 && W === 1280) { // the panels back (TAB), then away again
      await pg.keyboard.press('Tab'); await sleep(600); await pg.screenshot({ path: `${OUT}/${MODE}_panels.jpg`, quality: 85 });
      const vis = await pg.evaluate(() => getComputedStyle(document.getElementById('hubMatch')).display !== 'none'); res.push('panels with TAB: ' + vis);
      await pg.keyboard.press('Tab'); await sleep(300);
      // a text box keeps its keys: type in the name field, nobody walks
      const p0 = await pg.evaluate(async () => (await import('/js/lobbyscenes/index.js')).lobbySceneInfo());
      res.push('scene: ' + JSON.stringify(p0));
      // START MATCH from the garage
      await pg.evaluate(() => document.getElementById('hubGo').click());
      for (let i = 0; i < 40 && !(await pg.evaluate(() => window.JANK.G.joined)); i++) await sleep(500);
      await sleep(1500);
      res.push(MODE + ' start: joined=' + (await pg.evaluate(() => window.JANK.G.joined)) + ' game=' + (await pg.evaluate(() => window.JANK.G.round && window.JANK.G.round.game)) + ' sceneOn=' + (await on(pg)));
      await pg.screenshot({ path: `${OUT}/${MODE}_started.jpg`, quality: 80 });
      await pg.evaluate(() => window.JANK.quitToMenu()); await sleep(2500);
      await isle(pg);
      res.push('back in the lobby: sceneOn=' + (await on(pg)));
      // a mode with no scene (training) still starts
      await pg.evaluate(() => document.querySelector('[data-mode2="training"]').click()); await sleep(800);
      res.push('training: sceneOn=' + (await on(pg)));
      await pg.evaluate(() => document.getElementById('hubGo').click());
      for (let i = 0; i < 40 && !(await pg.evaluate(() => window.JANK.G.joined)); i++) await sleep(500);
      res.push('training start: joined=' + (await pg.evaluate(() => window.JANK.G.joined)));
    }
    await pg.context().close();
  }
  console.log(res.join('\n'));
  console.log('errors:', JSON.stringify(errs));
  await b.close();
})();
