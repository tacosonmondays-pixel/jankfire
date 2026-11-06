require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const PORT = process.env.PORT, TOKEN = process.env.TOKEN, SP = process.env.SP;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const errs = [];
  const ctx = await b.newContext({ viewport: { width: 1280, height: 720 }, recordVideo: { dir: SP + '/vid', size: { width: 1280, height: 720 } } });
  const pg = await ctx.newPage();
  pg.on('pageerror', (e) => errs.push(e.message));
  await pg.addInitScript(([t]) => { if (!localStorage.getItem('jankfire')) { localStorage.setItem('jankfire_token', t); localStorage.setItem('jankfire', JSON.stringify({ name: 'cztest', jank: 3 })); } }, [TOKEN]);
  await pg.goto(`http://localhost:${PORT}/`); await sleep(3000);
  await pg.click('#scr-main [data-go="cosmetics"]', { force: true }); await sleep(2500);
  // drag it around
  await pg.mouse.move(640, 300); await pg.mouse.down();
  for (let i = 0; i < 20; i++) { await pg.mouse.move(640 + i * 14, 300 + Math.sin(i / 3) * 30); await sleep(40); }
  await pg.mouse.up(); await sleep(1200);
  await pg.click('.cz-tab[data-tab=wrap]'); await sleep(3000);
  for (const k of ['pink', 'chrome', 'neon', 'gold']) { await pg.hover(`.cz-tile[data-k=${k}]`); await sleep(900); }
  await pg.click('.cz-tile[data-k=neon]'); await sleep(800);
  await pg.click('.cz-wm button:has-text("FULL")'); await sleep(900);
  await pg.click('#czSearch'); await pg.keyboard.type('camo', { delay: 120 }); await sleep(1500);
  await pg.hover('.cz-tile[data-k=camo]'); await sleep(900);
  await pg.fill('#czSearch', ''); await sleep(300);
  await pg.click('.cz-tab[data-tab=charm]'); await sleep(1800);
  for (const k of ['cowboy', 'crown', 'chef']) { await pg.hover(`.cz-tile[data-k=${k}]`); await sleep(900); }
  await pg.click('.cz-tab[data-tab=effect]'); await sleep(1500);
  for (const k of ['sparkles', 'hearts']) { await pg.hover(`.cz-tile[data-k=${k}]`); await sleep(1400); }
  await pg.click('.cz-tab[data-tab=finisher]'); await sleep(1500);
  await pg.hover('.cz-tile.rand'); await sleep(1200);
  await pg.click('.cz-row[data-id=sniper]'); await sleep(800);
  await pg.click('.cz-tab[data-tab=skin]'); await sleep(2000);
  await pg.hover('.cz-tile[data-k=sniper_golden]'); await sleep(1500);
  await pg.hover('.cz-tile[data-k=sniper_musket]'); await sleep(1500);
  await pg.click('.cz-row[data-id=knife]'); await sleep(2000);
  for (const k of ['knife_butterfly', 'knife_karambit', 'knife_spoon']) { await pg.hover(`.cz-tile[data-k=${k}]`); await sleep(1100); }
  await pg.mouse.move(640, 200); await sleep(1000);
  await ctx.close();
  // idle: no input for 15 s -> the 3D view stops drawing
  const ctx2 = await b.newContext({ viewport: { width: 1024, height: 576 } });
  const p2 = await ctx2.newPage();
  p2.on('pageerror', (e) => errs.push(e.message));
  await p2.goto(`http://localhost:${PORT}/`); await sleep(2500);
  await p2.click('#scr-main [data-go="cosmetics"]', { force: true }); await sleep(1500);
  const busy = await p2.evaluate(async () => { const c = await import('/js/customize.js'); return c.czFrame(0.05) || c.czFrame(0.05); });
  await sleep(15500);
  const idle = await p2.evaluate(async () => { const c = await import('/js/customize.js'); let n = 0; for (let i = 0; i < 10; i++) if (c.czFrame(0.05)) n++; return n; });
  console.log('renders while turning:', busy > 0, '| renders out of 10 frames after 15 s idle:', idle);
  await p2.click('.cz-tab[data-tab=wrap]'); await sleep(3000);
  await p2.screenshot({ path: SP + '/small_1024x576.png' });
  await p2.click('.cz-btn:has-text("GRAPPLE")'); await sleep(1000);
  console.log('classic locker opens:', await p2.isVisible('#scr-cosmetics'), '| grapple cards:', await p2.locator('#sk-grapple > *').count(), '| sprays:', await p2.locator('#sk-spray .chip, #sk-spray > *').count());
  await ctx2.close();
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
