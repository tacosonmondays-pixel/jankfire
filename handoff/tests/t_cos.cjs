require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs'); // at most 2 headless browsers machine-wide
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 900 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.goto('http://localhost:3000/'); await pg.waitForTimeout(500);
  await pg.click('#scr-main [data-go="cosmetics"]'); await pg.waitForTimeout(300);
  console.log('all mode default', await pg.isChecked('#skAllMode'));
  await pg.click('#sk-finish .chip:has-text("Pink")');
  await pg.click('#sk-hat .chip:has-text("Traffic Cone")');
  const skins = await pg.evaluate(() => JSON.parse(localStorage.getItem('jankfire')).skins);
  const ids = Object.keys(skins);
  console.log('weapons dressed', ids.length, 'scythe?', !!skins.scythe, 'sample', JSON.stringify(skins.knife), JSON.stringify(skins.ar));
  console.log('list has killstreak', await pg.locator('#cosWeapons .lt:has-text("killstreak")').count(), 'kill chips', await pg.locator('#sk-kill .chip').count());
  const eq = await pg.evaluate(async () => (await import('/js/ctx.js')).G.equipped.scythe_rifle);
  console.log('scythe_rifle borrows', JSON.stringify(eq));
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
