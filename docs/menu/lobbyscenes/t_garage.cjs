// garage: open the offline lobby on BATTLE ISLAND, screenshot, swap the mech (frames), switch modes, memory check
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const OUT = process.env.OUT, PORT = process.env.PORT, JANK = Number(process.env.JANK ?? 3), [W, H] = (process.env.SIZE || '1280x720').split('x').map(Number);
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const ctx = await b.newContext({ viewport: { width: W, height: H } });
  if (process.env.VIDEO) await ctx.close();
  const c2 = process.env.VIDEO ? await b.newContext({ viewport: { width: W, height: H }, recordVideo: { dir: OUT + '/vid', size: { width: W, height: H } } }) : ctx;
  const pg = await c2.newPage();
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message)); pg.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') errs.push('console: ' + m.text()); });
  await pg.addInitScript((j) => { localStorage.setItem('jf_giftseen_all', '1'); localStorage.setItem('jankfire', JSON.stringify({ name: 'taco', killcam: false, jank: j })); }, JANK);
  await pg.goto(`http://localhost:${PORT}/`); await sleep(2500);
  await pg.evaluate((j) => { const e = document.getElementById('jank'); e.value = String(j); e.dispatchEvent(new Event('change')); }, JANK);
  await pg.evaluate(() => document.querySelector('[data-hub="offline"]').click()); await sleep(600);
  const mem0 = await pg.evaluate(() => ({ ...window.JANK.G.renderer.info.memory }));
  await pg.evaluate(() => document.querySelector('[data-mode2="isle"]').click());
  for (let i = 0; i < 40; i++) { await sleep(500); const inf = await pg.evaluate(async () => (await import('/js/lobbyscenes/index.js')).lobbySceneInfo()); if (inf && inf.extra && inf.extra.glb[1]) break; }
  await sleep(1500);
  const info = await pg.evaluate(async () => (await import('/js/lobbyscenes/index.js')).lobbySceneInfo());
  console.log('info', JSON.stringify(info));
  await pg.screenshot({ path: `${OUT}/garage_${JANK}_${W}.jpg`, quality: 85 });
  if (process.env.SWAP) {
    await pg.evaluate((ts) => { window.JANK.G.lsTimeScale = ts; document.querySelector('#lsTags .ls-swap button[data-d="1"]').click(); }, Number(process.env.TS || 1));
    for (let i = 0; i < 12; i++) { await sleep(Number(process.env.STEP || 170)); await pg.screenshot({ path: `${OUT}/swap_${String(i).padStart(2, '0')}.jpg`, quality: 80 }); }
    await sleep(2500); await pg.screenshot({ path: `${OUT}/garage_after.jpg`, quality: 85 });
  }
  if (process.env.MEM) {
    for (let k = 0; k < 5; k++) for (const m of ['qp', 'isle', 'zm', 'isle']) { await pg.evaluate((m) => document.querySelector(`[data-mode2="${m}"]`).click(), m); await sleep(700); }
    await pg.evaluate(() => document.querySelector('[data-mode2="qp"]').click()); await sleep(1500);
    const mem1 = await pg.evaluate(() => ({ ...window.JANK.G.renderer.info.memory }));
    console.log('memory before', JSON.stringify(mem0), 'after 20 switches', JSON.stringify(mem1));
  }
  console.log('errors:', JSON.stringify(errs.filter((e) => !/favicon|404/.test(e)).slice(0, 12)));
  await c2.close(); await b.close();
})();
