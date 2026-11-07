require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs'); // at most 2 headless browsers machine-wide
const { chromium } = require('playwright');
{ const L = chromium.launch.bind(chromium); chromium.launch = async (...a) => { const b = await L(...a), seen = () => { try { localStorage.setItem('jf_giftseen_all', '1'); } catch (e) { /* no storage */ } }; const np = b.newPage.bind(b), nc = b.newContext.bind(b); b.newPage = async (...o) => { const p = await np(...o); await p.addInitScript(seen); return p; }; b.newContext = async (...o) => { const c = await nc(...o); await c.addInitScript(seen); return c; }; return b; }; } // the guest gift popup (multiopen.js) would cover the menu: every page starts with it already seen
const out = process.argv[2];
const looks = [
  { color: '#ff4fd8', hair: 'afro', hairColor: '#ff4fd8', top: 'hoodie', topColor: '#4fd8ff', bottom: 'pants', bottomColor: '#3a3a44', skin: '#8d5524', back: 'cape' },
  { color: '#ffe14d', hair: 'short', hairColor: '#4a2a10', top: 'suit', topColor: '#1a1a1a', bottom: 'pants', bottomColor: '#1a1a1a', skin: '#ffdbac', back: 'backpack', face: 'shades' },
  { color: '#7dff4f', hair: 'mohawk', hairColor: '#7dff4f', top: 'tee', topColor: '#ffffff', bottom: 'skirt', bottomColor: '#ff4f4f', skin: '#9ad0ff', back: 'wings' },
  { color: '#ff7a1a', hair: 'long', hairColor: '#d9b45a', top: 'jacket', topColor: '#8a5a2b', bottom: 'shorts', bottomColor: '#2a4a8a', skin: '#e0ac69', back: 'jetpack' },
  { color: '#b07dff', hair: 'ponytail', hairColor: '#c02030', top: 'none', bottom: 'pants', bottomColor: '#3a6a2a', back: 'voidcape' },
  { color: '#4fd8ff', hair: 'spiky', hairColor: '#ffe14d', top: 'tank', bottom: 'shorts', head: 'cowboy' },
];
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 900 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message + e.stack));
  await pg.goto('http://localhost:3000/'); await pg.waitForTimeout(500);
  for (let i = 0; i < looks.length; i++) {
    await pg.evaluate((lk) => { localStorage.setItem('jankfire', JSON.stringify({ name: 'fit', look: lk })); }, looks[i]);
    await pg.reload(); await pg.waitForTimeout(500);
    await pg.click('#scr-main [data-go="character"]'); await pg.waitForTimeout(250);
    for (const t of [0, 1700, 1800]) {
      if (t) await pg.waitForTimeout(t);
      await pg.locator('#preview').screenshot({ path: `${out}/fit_${i}_${t}.png` });
    }
  }
  await pg.screenshot({ path: `${out}/fit_ui.png` });
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
