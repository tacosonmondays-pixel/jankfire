require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs'); // at most 2 headless browsers machine-wide
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 900, height: 560 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ name: 'rando', killcam: false })));
  await pg.goto('http://localhost:3000/'); await pg.waitForTimeout(500);
  await pg.click('[data-pick="bots"]'); await pg.waitForTimeout(700); await pg.click('#mpCustom');
  await pg.selectOption('#setupGame', 'rand');
  await pg.locator('#setupBots').fill('3');
  await pg.click('#setupGo'); await pg.waitForTimeout(2500);
  const slots = () => pg.evaluate(async () => (await import('/js/weapons.js')).W.slots.join(','));
  console.log('life 1', await slots(), 'label', await pg.textContent('#modeLabel'));
  await pg.evaluate(async () => { const { net } = await import('/js/net.js'); net.send({ t: 'tbag' }); });
  await pg.waitForTimeout(4200);
  console.log('life 2', await slots());
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
