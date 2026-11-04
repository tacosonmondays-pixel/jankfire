require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs'); // at most 2 headless browsers machine-wide
const { chromium } = require('playwright');
const out = process.argv[2];
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 800, height: 450 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message + e.stack));
  await pg.goto('http://localhost:3000/'); await pg.waitForTimeout(500);
  await pg.click('#scr-main [data-go="setup"]');
  await pg.locator('#setupBots').fill('1');
  await pg.click('#setupGo'); await pg.waitForTimeout(1500);
  for (const id of ['suburb', 'desert', 'bazaar', 'warehouse', 'skyline', 'rooftop', 'islands', 'platform']) {
    await pg.evaluate(async (id) => {
      const { loadMap } = await import('/js/world.js'); const { MAPS } = await import('/shared/map.js'); const { ME } = await import('/js/player.js');
      loadMap(id);
      let x1 = -1e9, z1 = -1e9; for (const bx of MAPS[id].boxes) { if (bx.max[1] < -6 || bx.min[1] > 2) continue; x1 = Math.max(x1, bx.max[0]); z1 = Math.max(z1, bx.max[2]); }
      clearInterval(window.__fly);
      const p = [x1 * 0.9, 25, z1 * 0.9];
      window.__fly = setInterval(() => { ME.pos = p.slice(); ME.vel = [0, 0, 0]; ME.yaw = -Math.PI * 0.75; ME.pitch = -0.28; }, 5);
    }, id);
    await pg.waitForTimeout(700);
    await pg.screenshot({ path: `${out}/scn_${id}.png` });
  }
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
