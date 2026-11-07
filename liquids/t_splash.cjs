// splashes only on real liquid: shots and booms on dry ground (a road, a beach over the sea's box, a car wreck) = 0;
// a shot into a pond and a boom on the sea = 1 each
require(__dirname + '/pwlock.cjs');
const { chromium } = require('playwright');
const port = process.argv[2];
const CASES = {
  suburb: [['road shot', 'tracer', [0, 6, 30], [0, 0, 34], 0], ['road boom', 'boom', [0, 0.3, 34], null, 0], ['wreck boom (car on the road)', 'boom', [-30, 1, 30], null, 0],
    ['pond shot (off the footbridge)', 'tracer', [11, 4, 6], [11, -0.3, 0], 1]],
  islands: [['beach boom', 'boom', [0, 1.2, 20], null, 0], ['beach shot', 'tracer', [0, 6, 26], [0, 0.4, 20], 0], ['sea boom (open water)', 'boom', 'auto', null, 1]],
};
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const ctx = await b.newContext({ viewport: { width: 480, height: 270 } });
  await ctx.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ jank: 0, name: 'tsplash' })));
  let fail = 0;
  for (const [map, list] of Object.entries(CASES)) {
    const pg = await ctx.newPage(); const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
    await pg.goto(`http://localhost:${port}/`); await pg.waitForTimeout(800);
    await pg.click('[data-pick="bots"]', { force: true }); await pg.waitForTimeout(700); await pg.click('#mpCustom', { force: true });
    await pg.selectOption('#setupMap', map); await pg.locator('#setupBots').fill('1'); await pg.click('#setupGo', { force: true }); await pg.waitForTimeout(4000);
    for (const [name, kind, a, bb, want] of list) {
      const got = await pg.evaluate(async ([kind, a, bb]) => {
        const L = await import('/js/liquids.js'), { fx } = await import('/js/fx.js'), { G } = await import('/js/ctx.js');
        const watchOff = G.remotes; G.remotes = new Map(); const projs = G.projs; G.projs = new Map(); const gibs = G.gibs; G.gibs = []; // (only what this case does)
        const n0 = L.liquidInfo().splashes;
        if (a === 'auto') { for (let z = 36; z < 120 && a === 'auto'; z += 0.5) if (L.liquidAt(0, -0.2, z, 2.5, 2)) a = [0, -0.2, z]; if (a === 'auto') return 'no open water found'; }
        if (kind === 'tracer') fx.onTracer(a, bb); else fx.onBoom(a);
        const n1 = L.liquidInfo().splashes;
        G.remotes = watchOff; G.projs = projs; G.gibs = gibs;
        return n1 - n0;
      }, [kind, a, bb]);
      const ok = got === want; if (!ok) fail++;
      console.log(`${ok ? 'PASS' : 'FAIL'} ${map} ${name}: ${got} splash(es), want ${want}`);
    }
    if (errs.length) { fail++; console.log('errors', errs.join(' | ')); }
    await pg.close();
  }
  console.log(fail ? `${fail} FAILED` : 'all pass');
  await b.close();
})();
