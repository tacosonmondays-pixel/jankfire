require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const URL = `http://localhost:${process.env.PORT}/`;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let bad = 0; const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) bad++; };
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ name: 'botsy', killcam: false, jank: 1, loadout: { primary: 'ar', secondary: 'cig', melee: 'knife', item: 'frag', streaks: ['moonboots', 'spinbot', 'satellite'] } })));
  await pg.goto(URL); await sleep(2500);
  await pg.click('[data-pick="bots"]', { force: true }); await sleep(800); await pg.click('#mpCustom', { force: true });
  await pg.click('#setupGo', { force: true }); await sleep(4000);
  const st = () => pg.evaluate(async () => { const { G } = await import('/js/ctx.js'); return { joined: G.joined, bots: [...G.remotes.values()].length, menu: !document.getElementById('menu').classList.contains('hidden'), eq: G.equipped.ar, knife: G.equipped.knife }; });
  let s = await st();
  ok(s.joined && s.bots > 0, `in a bots match with ${s.bots} bots`);
  // pause -> COSMETICS (the customize screen) -> equip -> LEAVE goes back to pause
  await pg.evaluate(() => document.exitPointerLock && document.exitPointerLock());
  await pg.keyboard.press('Escape'); await sleep(600);
  if (!(await pg.isVisible('#scr-pause'))) { await pg.keyboard.press('Escape'); await sleep(600); }
  await pg.click('#scr-pause [data-go="loadout"]', { force: true }); await sleep(1500);
  ok(await pg.isVisible('#scr-customize'), 'pause -> CUSTOMIZE opens the hub');
  await pg.click('.cz-hub .hub-tab[data-hub=weapons]'); await sleep(1000);
  await pg.click('.cz-row[data-id=knife]'); await sleep(500);
  await pg.click('.cz-tab[data-tab=skin]'); await sleep(1200);
  await pg.click('.cz-tile[data-k=knife_kitchen]'); await sleep(400);
  await pg.click('.cz-tab[data-tab=wrap]'); await sleep(800);
  await pg.click('.cz-tile[data-k=wood]'); await sleep(400);
  await pg.click('.cz-tab[data-tab=leave]'); await sleep(600);
  ok(await pg.isVisible('#scr-pause'), 'LEAVE goes back to the pause menu in a match');
  s = await st();
  ok(s.knife && s.knife[3] === 'knife_kitchen' && s.knife[0] === 'wood', 'knife look applied in game: ' + JSON.stringify(s.knife));
  await pg.click('#resume', { force: true }); await sleep(800);
  await pg.mouse.click(640, 360); await sleep(500);
  s = await st();
  ok(!s.menu, 'back in the game');
  // melee on left click
  await pg.keyboard.press('Digit3'); await sleep(900);
  const before = await pg.evaluate(async () => { const { W } = await import('/js/weapons.js'); W.swingId = null; return W.cur; });
  await pg.mouse.move(640, 360); await pg.mouse.down(); await sleep(60);
  const sw = await pg.evaluate(async () => { const { W } = await import('/js/weapons.js'); return { swing: W.swing, id: W.swingId, cur: W.cur }; });
  await pg.mouse.up();
  ok(sw.id === 'knife', `left click swings the melee (${before} -> ${JSON.stringify(sw)})`);
  await sleep(6000); // let the bots play a bit
  ok(errs.length === 0, 'page errors: ' + (errs.join(' | ') || 0));
  console.log(bad ? `${bad} FAIL` : 'ALL OK');
  await b.close();
})();
