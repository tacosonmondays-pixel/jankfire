require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs'); // at most 2 headless browsers machine-wide
// unified hotbar: bottom and right-side layouts, with a ready killstreak, at two window sizes
const { chromium } = require('playwright');
const [port, out] = process.argv.slice(2);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const errs = [];
  for (const pos of ['bottom', 'right']) {
    for (const [w, h] of [[1280, 720], [800, 450]]) {
      const pg = await b.newPage({ viewport: { width: w, height: h } });
      pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message + '\n' + e.stack));
      await pg.addInitScript((pos) => localStorage.setItem('jankfire', JSON.stringify({ name: 'bar', hotbar: pos, loadout: { primary: 'redline', secondary: 'marbles', melee: 'knife', item: 'bubble', streaks: ['moonboots', 'chickenstrike', 'scythe'] } })), pos);
      await pg.goto(`http://localhost:${port}/`); await sleep(500);
      await pg.click('#scr-main [data-mode="training"]'); await sleep(1600);
      await pg.evaluate(async () => { const { G } = await import('/js/ctx.js'); const { net } = await import('/js/net.js'); net.ws.onmessage({ data: JSON.stringify({ t: 'streak', earned: 'chickenstrike', n: 4 }) }); const { ME } = await import('/js/player.js'); setInterval(() => { ME.pitch = 0.2; }, 20); });
      await pg.keyboard.press('Digit2'); await sleep(900);
      await pg.screenshot({ path: `${out}/bar_${pos}_${w}.png` });
      const box = await pg.evaluate(() => { const r = document.getElementById('hotbar').getBoundingClientRect(); const a = document.getElementById('ammo').getBoundingClientRect(); const k = document.getElementById('streakTray').getBoundingClientRect(); const hp = document.getElementById('hpbox').getBoundingClientRect(); return { bar: [r.left, r.top, r.right, r.bottom].map(Math.round), ammo: [a.left, a.top, a.right, a.bottom].map(Math.round), streaks: [k.left, k.top, k.right, k.bottom].map(Math.round), hp: [hp.left, hp.top, hp.right, hp.bottom].map(Math.round), kids: document.querySelectorAll('#hotbar .hslot, #hotbar .kstreak').length }; });
      console.log(pos, w + 'x' + h, JSON.stringify(box));
      await pg.close();
    }
  }
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
