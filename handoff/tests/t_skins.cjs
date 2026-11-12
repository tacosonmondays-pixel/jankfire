require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs'); // at most 2 headless browsers machine-wide
const { chromium } = require('playwright');
const out = process.argv[2];
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 900 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message + e.stack));
  await pg.goto('http://localhost:3000/'); await pg.waitForTimeout(500);
  await pg.click('#scr-main [data-go="cosmetics"]'); await pg.waitForTimeout(400);
  const list = await pg.evaluate(async () => { const { COSMETICS } = await import('/shared/cosmetics.js'); return Object.entries(COSMETICS.model).filter(([id, v]) => v.weapon && !id.startsWith('knife') && !id.startsWith('slapper') && id !== 'bread_croissant').map(([id, v]) => [v.weapon, id]); });
  let i = 0;
  for (const [w, id] of list) {
    await pg.evaluate(async ([w, id]) => { const { showPreview } = await import('/js/preview.js'); showPreview(w, ['default', 'none', 'none', id]); }, [w, id]);
    await pg.waitForTimeout(450);
    await pg.locator('#preview').screenshot({ path: `${out}/sk_${String(i++).padStart(2, '0')}_${id}.png` });
  }
  console.log(i, 'skins', errs.join('\n') || 'no errors');
  await b.close();
})();
