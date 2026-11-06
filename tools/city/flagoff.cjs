// The live game with story mode off: node tools/city/flagoff.cjs <port> [outPng]
// Starts a bots match from the menu, plays 8 s, swings the melee with a left click, and reports page errors,
// console warnings that mention FLAGS, bot count, map, and whether the swing happened. Run it on main and on the
// branch: the numbers should match.
const { chromium } = require('playwright');
const [port = 3107, png] = process.argv.slice(2);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 960, height: 540 } });
  const errs = [], flags = [], reqs = [];
  pg.on('pageerror', (e) => errs.push(e.message));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); if (/FLAGS/.test(m.text())) flags.push(m.text()); });
  pg.on('request', (r) => { if (/\/(city|story)\//.test(r.url()) || /storytest/.test(r.url())) reqs.push(r.url()); });
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ name: 'flagoff', loadout: { primary: 'ar', secondary: 'revolver', melee: 'knife' } })));
  await pg.goto(`http://localhost:${port}/`); await sleep(1500);
  await pg.evaluate(() => document.getElementById('setupGo').click());
  await sleep(8000);
  await pg.keyboard.press('Digit3'); await sleep(700);
  await pg.mouse.move(480, 270); await pg.mouse.down(); await sleep(60);
  const swing = await pg.evaluate(async () => { const w = await import('/js/weapons.js'); return { swing: w.W.swing, slot: w.W.slot ?? null }; });
  await pg.mouse.up();
  const st = await pg.evaluate(async () => { const { G } = await import('/js/ctx.js'); const { MAP } = await import('/shared/map.js'); return { mode: G.mode, joined: G.joined, remotes: G.remotes.size, map: MAP.id }; });
  if (png) await pg.screenshot({ path: png });
  console.log(JSON.stringify({ ...st, swung: swing.swing > 0, swing, pageErrors: errs, flagWarnings: flags, storyRequests: reqs }));
  await b.close();
})();
