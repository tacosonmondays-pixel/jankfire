// every mode in the bots setup: start it, play 6 s, count page errors / console errors / 4xx. then melee: left click swings
require(__dirname + '/pwlock.cjs');
const { chromium } = require('playwright');
const port = process.argv[2];
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const ctx = await b.newContext({ viewport: { width: 640, height: 360 } });
  await ctx.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ jank: 1, name: 'smoke' })));
  const pg0 = await ctx.newPage(); await pg0.goto(`http://localhost:${port}/`); await pg0.waitForTimeout(800);
  const games = await pg0.evaluate(() => [...document.querySelectorAll('#setupGame option')].map((o) => o.value)); await pg0.close();
  let fails = 0;
  for (const g of games) {
    const pg = await ctx.newPage(), errs = [], bad = [];
    pg.on('pageerror', (e) => errs.push(e.message)); pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    pg.on('response', (r) => { if (r.status() >= 400) bad.push(r.status() + ' ' + r.url()); });
    await pg.goto(`http://localhost:${port}/`); await pg.waitForTimeout(800);
    await pg.click('[data-pick="bots"]', { force: true }); await pg.waitForTimeout(600); await pg.click('#mpCustom', { force: true });
    await pg.selectOption('#setupGame', g); await pg.waitForTimeout(200);
    const maps = await pg.evaluate(() => [...document.querySelectorAll('#setupMap option')].map((o) => o.value));
    await pg.evaluate(() => { const e = document.getElementById('setupBots'); e.value = '2'; e.dispatchEvent(new Event('input')); }); await pg.click('#setupGo', { force: true }); await pg.waitForTimeout(7000);
    let swing = '';
    if (g === 'dm') {
      await pg.mouse.click(320, 180); await pg.waitForTimeout(300);
      await pg.keyboard.press('Digit3'); await pg.waitForTimeout(900);
      swing = await pg.evaluate(async () => { const { W } = await import('/js/weapons.js'); window.__sw = 0; const t0 = performance.now(); const id = setInterval(() => { window.__sw = Math.max(window.__sw, W.swing || 0); if (performance.now() - t0 > 1500) clearInterval(id); }, 10); return W.cur; });
      await pg.mouse.down(); await pg.waitForTimeout(150); await pg.mouse.up(); await pg.waitForTimeout(1500);
      swing = ` melee=${swing} swung=${await pg.evaluate(() => window.__sw)}`;
    }
    const L = await pg.evaluate(async () => { const m = await import('/js/liquids.js'); return m.liquidInfo(); });
    console.log(`${g} [${maps[0]}] errors=${errs.length} 4xx=${bad.length}${swing} liquids=${JSON.stringify(L.keys)}`, errs.slice(0, 2).join(' | '), bad.slice(0, 2).join(' | '));
    if (errs.length || bad.length) fails++;
    await pg.close();
  }
  console.log('modes', games.length, 'failing', fails);
  await b.close();
})();
