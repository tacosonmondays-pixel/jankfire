require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs'); // at most 2 headless browsers machine-wide
const { chromium } = require('playwright');
{ const L = chromium.launch.bind(chromium); chromium.launch = async (...a) => { const b = await L(...a), seen = () => { try { localStorage.setItem('jf_giftseen_all', '1'); } catch (e) { /* no storage */ } }; const np = b.newPage.bind(b), nc = b.newContext.bind(b); b.newPage = async (...o) => { const p = await np(...o); await p.addInitScript(seen); return p; }; b.newContext = async (...o) => { const c = await nc(...o); await c.addInitScript(seen); return c; }; return b; }; } // the guest gift popup (multiopen.js) would cover the menu: every page starts with it already seen
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 860 } });
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ name: 'fit', look: { color: '#ff4fd8', hair: 'afro', hairColor: '#ff4fd8', top: 'hoodie', topColor: '#4fd8ff', bottom: 'pants', bottomColor: '#3a3a44', skin: '#8d5524', back: 'cape' } })));
  await pg.goto('http://localhost:3000/'); await pg.waitForTimeout(500);
  await pg.click('#scr-main [data-go="character"]'); await pg.waitForTimeout(400);
  await pg.screenshot({ path: process.argv[2] + '/fit_top.png' });
  await pg.evaluate(() => { document.getElementById('menu').scrollTop = 600; });
  await pg.waitForTimeout(1900);
  await pg.screenshot({ path: process.argv[2] + '/fit_scrolled.png' });
  await b.close();
})();
