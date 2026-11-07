require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs'); // at most 2 headless browsers machine-wide
const { chromium } = require('playwright');
{ const L = chromium.launch.bind(chromium); chromium.launch = async (...a) => { const b = await L(...a), seen = () => { try { localStorage.setItem('jf_giftseen_all', '1'); } catch (e) { /* no storage */ } }; const np = b.newPage.bind(b), nc = b.newContext.bind(b); b.newPage = async (...o) => { const p = await np(...o); await p.addInitScript(seen); return p; }; b.newContext = async (...o) => { const c = await nc(...o); await c.addInitScript(seen); return c; }; return b; }; } // the guest gift popup (multiopen.js) would cover the menu: every page starts with it already seen
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
