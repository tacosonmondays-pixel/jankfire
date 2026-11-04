require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs'); // at most 2 headless browsers machine-wide
const { chromium } = require('playwright');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 900, height: 560 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message + e.stack));
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ name: 'samurai', loadout: { primary: 'ar', secondary: 'cig', melee: 'katana', item: 'frag' } })));
  await pg.goto('http://localhost:3000/'); await sleep(500);
  await pg.click('#scr-main [data-mode="training"]'); await sleep(1600);
  await pg.keyboard.press('Digit3'); await sleep(600);
  await pg.screenshot({ path: process.argv[2] + '/kat_0.png' });
  // teleport next to dummies and slash until 4 kills
  for (let i = 0; i < 40; i++) {
    const k = await pg.evaluate(async () => (await import('/js/weapons.js')).W.kat || 0);
    if (k >= 4) break;
    await pg.evaluate(async () => {
      const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js'); const w = await import('/js/weapons.js');
      const t = [...G.remotes.values()].find((r) => r.alive && r.name === 'Dummy');
      if (!t) return;
      ME.pos = [t.pos[0], t.pos[1], t.pos[2] + 1.8]; ME.vel = [0, 0, 0]; ME.yaw = 0; ME.pitch = 0.1;
      w.fireDown(); w.fireUp();
    });
    await sleep(560);
  }
  const k = await pg.evaluate(async () => (await import('/js/weapons.js')).W.kat || 0);
  console.log('katana kills', k);
  await pg.evaluate(async () => { const { ME } = await import('/js/player.js'); ME.pitch = 0.2; });
  await sleep(400);
  await pg.screenshot({ path: process.argv[2] + '/kat_4.png' });
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
