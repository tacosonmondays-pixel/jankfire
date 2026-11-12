require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs'); // at most 2 headless browsers machine-wide
const { chromium } = require('playwright');
{ const L = chromium.launch.bind(chromium); chromium.launch = async (...a) => { const b = await L(...a), seen = () => { try { localStorage.setItem('jf_giftseen_all', '1'); } catch (e) { /* no storage */ } }; const np = b.newPage.bind(b), nc = b.newContext.bind(b); b.newPage = async (...o) => { const p = await np(...o); await p.addInitScript(seen); return p; }; b.newContext = async (...o) => { const c = await nc(...o); await c.addInitScript(seen); return c; }; return b; }; } // the guest gift popup (multiopen.js) would cover the menu: every page starts with it already seen
const out = process.argv[2];
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 800, height: 500 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message)); // (regress2 wants a 'no errors' line)
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ name: 'flash', loadout: { primary: 'ar', secondary: 'cards', melee: 'knife' } })));
  await pg.goto('http://localhost:3000/'); await pg.waitForTimeout(500);
  await pg.click('#scr-main [data-mode="training"]'); await pg.waitForTimeout(1500);
  await pg.evaluate(async () => { const { W } = await import('/js/weapons.js'); window.__f = setInterval(() => { W.flashT = 1; }, 5); });
  await pg.waitForTimeout(150);
  await pg.screenshot({ path: out + '/an_flash_ar.png', clip: { x: 300, y: 200, width: 500, height: 300 } });
  await pg.evaluate(() => clearInterval(window.__f));
  await pg.keyboard.press('Digit2'); await pg.waitForTimeout(500);
  await pg.evaluate(async () => { const w = await import('/js/weapons.js'); w.fireDown(); w.fireUp(); });
  for (const t of [180, 260]) { await pg.waitForTimeout(t === 180 ? 180 : 80); await pg.screenshot({ path: `${out}/an_cardfly_${t}.png`, clip: { x: 200, y: 100, width: 600, height: 400 } }); }
  console.log(errs.length ? errs.join('\n') : 'no errors');
  await b.close();
})();
