// the home screen at 1280x720, 1920x1080 and 800x900, deviceScaleFactor 2, logged in (containers to open), install app shown
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const errs = [], bad = [];
  for (const [W, H] of [[1280, 720], [1920, 1080], [800, 900]]) {
    const ctx = await b.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 2 });
    const pg = await ctx.newPage();
    pg.on('pageerror', (e) => errs.push(`${W}: ${e.message}`));
    pg.on('console', (m) => { if (m.type() === 'error') errs.push(`${W} console: ${m.text()}`); });
    pg.on('response', (r) => { if (r.status() >= 400) bad.push(`${r.status()} ${r.url()}`); });
    await pg.addInitScript(([t]) => { localStorage.setItem('jankfire_token', t); localStorage.setItem('jankfire', JSON.stringify({ name: 'cztest', jank: 3 })); }, [process.env.TOKEN]);
    await pg.goto(`http://localhost:${process.env.PORT}/`); await sleep(4000);
    await pg.evaluate(() => document.getElementById('installBtn').classList.remove('hidden'));
    await sleep(1500);
    await pg.screenshot({ path: `${process.env.OUT}/home_${W}x${H}.png` });
    await pg.locator('.home-left').screenshot({ path: `${process.env.OUT}/side_${W}x${H}.png` });
    await ctx.close();
  }
  console.log(errs.join('\n') || 'no console errors');
  console.log(bad.join('\n') || 'no 4xx');
  await b.close();
})();
