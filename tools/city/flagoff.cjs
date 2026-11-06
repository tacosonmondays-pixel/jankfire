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
  for (let i = 0; i < 30; i++) { // the menu wires up after the models load: keep pressing GO until we're in
    const j = await pg.evaluate(async () => { const { G } = await import('/js/ctx.js'); if (!G.joined) document.getElementById('setupGo').click(); return G.joined; });
    if (j) break; await sleep(2000);
  }
  await sleep(8000);
  await pg.keyboard.press('Digit3'); await sleep(700);
  await pg.mouse.move(480, 270); await pg.mouse.click(480, 270); await sleep(1200); // the first click may only drop you in
  await pg.keyboard.press('Digit3'); await sleep(700);
  // headless Chromium has no pointer lock, so the game sits on its pause menu: put it away like a locked mouse would,
  // and listen for the swing going out to the server
  const pre = await pg.evaluate(async () => {
    const { net } = await import('/js/net.js'); const { ME } = await import('/js/player.js');
    window.__sent = []; const send = net.send.bind(net); net.send = (m) => { if (m && m.t === 'fire') window.__sent.push(m.w); return send(m); };
    document.getElementById('menu').classList.add('hidden');
    return { alive: ME.alive };
  });
  const watch = pg.evaluate(async () => { const w = await import('/js/weapons.js'); let mx = 0; const t = performance.now(); while (performance.now() - t < 900) { mx = Math.max(mx, w.W.swing || 0); await new Promise((r) => requestAnimationFrame(r)); } return { swing: mx, slot: w.W.slot ?? null }; });
  await sleep(100); await pg.mouse.down(); await sleep(80); await pg.mouse.up();
  const swing = await watch;
  swing.sent = await pg.evaluate(() => window.__sent); swing.alive = pre.alive;
  const st = await pg.evaluate(async () => { const { G } = await import('/js/ctx.js'); const { MAP } = await import('/shared/map.js'); return { mode: G.mode, joined: G.joined, remotes: G.remotes.size, map: MAP.id }; });
  if (png) await pg.screenshot({ path: png });
  console.log(JSON.stringify({ ...st, swung: swing.swing > 0 || (swing.sent || []).length > 0, swing, pageErrors: errs, flagWarnings: flags, storyRequests: reqs }));
  await b.close();
})();
