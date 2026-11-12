require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs'); // at most 2 headless browsers machine-wide
const { chromium } = require('playwright');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1000, height: 600 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message + e.stack));
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ name: 'streaker', killcam: false, loadout: { primary: 'sniper', secondary: 'cig', melee: 'knife', item: 'frag', streaks: ['moonboots', 'spinbot', 'satellite'] } })));
  await pg.goto('http://localhost:3000/'); await sleep(500);
  await pg.click('#scr-main [data-go="setup"]');
  await pg.locator('#setupBots').fill('6');
  await pg.selectOption('#setupDiff', 'easy');
  await pg.click('#setupGo'); await sleep(2500);
  console.log('tray', await pg.textContent('#streakTray'));
  // headshot bots one after another
  let kills = 0;
  for (let i = 0; i < 40 && kills < 6; i++) {
    const r = await pg.evaluate(async () => {
      const { G } = await import('/js/ctx.js'); const { net } = await import('/js/net.js'); const { ME } = await import('/js/player.js');
      const t = [...G.remotes.values()].find((x) => x.alive);
      if (!t || !ME.alive) return 'none';
      const e = [ME.pos[0], ME.pos[1] + 1.6, ME.pos[2]], to = [t.pos[0], t.pos[1] + 2, t.pos[2]];
      const d = to.map((v, k) => v - e[k]); const L = Math.hypot(...d);
      net.send({ t: 'hit', to: t.id, w: 'sniper', d: d.map((v) => v / L), n: 1, h: 1 });
      return 'shot';
    });
    await sleep(900);
    kills = await pg.evaluate(async () => (await import('/js/ctx.js')).G.kills || 0);
  }
  console.log('kills', kills, 'pocket', JSON.stringify(await pg.evaluate(async () => (await import('/js/ctx.js')).G.pocket)));
  await pg.screenshot({ path: process.argv[2] + '/streak_tray.png' });
  console.log('tray', await pg.textContent('#streakTray'));
  await pg.keyboard.press('Digit5'); await sleep(500);
  await pg.keyboard.press('Digit6'); await sleep(500);
  const st = await pg.evaluate(async () => { const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js'); return { moon: ME.moonUntil > performance.now(), spin: G.spinUntil > performance.now(), pocket: G.pocket }; });
  console.log('after 5+6', JSON.stringify(st));
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
