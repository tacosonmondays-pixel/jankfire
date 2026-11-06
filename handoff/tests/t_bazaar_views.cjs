require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs'); // at most 2 headless browsers machine-wide
const { chromium } = require('playwright');
const out = process.argv[2];
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 800, height: 450 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.goto('http://localhost:3000/'); await pg.waitForTimeout(500);
  await pg.click('[data-pick="bots"]'); await pg.waitForTimeout(700); await pg.click('#mpCustom');
  await pg.selectOption('#setupMap', 'bazaar');
  await pg.locator('#setupBots').fill('1');
  await pg.click('#setupGo'); await pg.waitForTimeout(1500);
  const views = [
    ['overview', [10, 95, 95], -0.75, 0],
    ['bridge_from_approach', [44, 1.7, -4], -0.12, 1.2],
    ['on_bridge', [26, 5.2, -14], -0.25, -2.1],
    ['upper_long', [35.5, 4.9, 38], -0.12, 0],
    ['mid_gallery', [-7.8, 5.1, 40], -0.15, 0.05],
    ['b_balcony', [-32, 5.5, -27], -0.35, 1.7],
    ['b_arcade_roof', [-50, 7.3, -53], -0.4, 3.0],
    ['cistern', [-45, -1.9, 40], -0.05, 0],
  ];
  for (const [name, p, pitch, yaw] of views) {
    await pg.evaluate(async ([p, pitch, yaw]) => {
      const { ME } = await import('/js/player.js');
      clearInterval(window.__fly);
      window.__fly = setInterval(() => { ME.pos = [p[0], p[1] - 1.6, p[2]]; ME.vel = [0, 0, 0]; ME.pitch = pitch; ME.yaw = yaw; }, 5);
    }, [p, pitch, yaw]);
    await pg.waitForTimeout(500);
    await pg.screenshot({ path: `${out}/bz_${name}.png` });
  }
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
