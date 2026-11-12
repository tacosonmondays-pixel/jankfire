require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs'); // at most 2 headless browsers machine-wide
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1000, height: 600 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message + e.stack));
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ name: 'hot', loadout: { primary: 'sniper', secondary: 'cards', melee: 'knife' }, skins: { sniper: ['gold', 'tophat', 'none', 'default'], knife: ['pink', 'party', 'none', 'knife_kitchen'] } })));
  await pg.goto('http://localhost:3000/'); await pg.waitForTimeout(500);
  await pg.click('#scr-main [data-mode="training"]'); await pg.waitForTimeout(1600);
  await pg.keyboard.press('Digit3'); await pg.waitForTimeout(400);
  await pg.screenshot({ path: process.argv[2] + '/hotbar.png' });
  console.log('slots', await pg.locator('#weapons .hslot').count(), 'imgs', await pg.locator('#weapons .hslot img').count(), 'on', await pg.locator('#weapons .hslot.on .nm').textContent());
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
