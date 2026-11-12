// lobby scenes: renderer memory after the first visit vs after N more mode switches (must not grow)
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await (await b.newContext({ viewport: { width: 1280, height: 720 } })).newPage();
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.addInitScript(() => { localStorage.setItem('jf_giftseen_all', '1'); localStorage.setItem('jankfire', JSON.stringify({ name: 'taco', killcam: false })); });
  await pg.goto(`http://localhost:${process.env.PORT}/`); await sleep(2500);
  await pg.evaluate(() => document.querySelector('[data-hub="offline"]').click()); await sleep(600);
  const mode = (m) => pg.evaluate((m) => document.querySelector(`[data-mode2="${m}"]`).click(), m);
  const mem = () => pg.evaluate(() => { const i = window.JANK.G.renderer.info; return { geo: i.memory.geometries, tex: i.memory.textures, prog: i.programs ? i.programs.length : 0 }; });
  const MODES = (process.env.MODES || 'isle').split(',');
  for (const m of MODES) { await mode(m); await sleep(6000); } // first visits: models land, caches fill
  await mode('qp'); await sleep(1500);
  const a = await mem();
  for (let k = 0; k < Number(process.env.N || 6); k++) { for (const m of MODES) { await mode(m); await sleep(1200); await mode("qp"); await sleep(800); } console.log("cycle", k, JSON.stringify(await mem())); }
  await sleep(1000);
  const c = await mem();
  console.log('after first visits', JSON.stringify(a), 'after more', JSON.stringify(c), c.geo - a.geo > 2 || c.tex - a.tex > 1 ? 'LEAK' : 'OK');
  console.log('errors:', JSON.stringify(errs));
  await b.close();
})();
