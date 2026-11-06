// playwright e2e (WP0/WP3). run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_wp3.cjs (needs a running server; t_flagoff also wants main on 3313)
// WP3 e2e: starter bar, pick up test loot, bar keys equip each kind, wheel (no input leaks, slow time), bag drag, locker, drop, save/load
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const PORT = process.env.PORT || 3311, OUT = process.env.SP + '/shots';
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message + ' ' + (e.stack || '').split('\n')[1]));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.addInitScript(() => { localStorage.setItem('jankfire', JSON.stringify({ name: 'wp3', jank: 3, loadout: { primary: 'ar', secondary: 'snowball', melee: 'knife', item: 'frag' } })); if (!sessionStorage.getItem('w3')) { sessionStorage.setItem('w3', 1); localStorage.removeItem('jfStorySaves'); } });
  await pg.goto(`http://localhost:${PORT}/?story=1`); await sleep(1500);
  await pg.click('#storyBtn', { force: true }); await sleep(700);
  await pg.click('#storyPick .st-btn.yellow', { force: true }); await sleep(3500);
  const S = () => pg.evaluate(async () => {
    const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js'); const { W } = await import('/js/weapons.js'); const { IV } = await import('/js/story/bar.js');
    const inv = IV.inv; const it = (u) => inv.bag.find((x) => x && x.u === u);
    return { slots: W.slots.join(','), cur: W.cur, slot: W.slot, item: W.item, bar: inv ? inv.bar.map((u) => (u == null ? '-' : it(u).b + (it(u).q > 1 ? 'x' + it(u).q : ''))).join(',') : null, bag: inv ? inv.bag.filter(Boolean).length : 0, locker: inv ? inv.locker.length : 0, hp: ME.hp, pos: ME.pos.map((x) => +x.toFixed(1)) };
  });
  const tp = (p) => pg.evaluate(async (p) => { const { ME } = await import('/js/player.js'); ME.pos = p.slice(); ME.vel = [0, 0, 0]; }, p);
  const key = async (k, ms = 80) => { await pg.keyboard.down(k); await sleep(ms); await pg.keyboard.up(k); await sleep(250); };
  console.log('start', JSON.stringify(await S()));
  // pick up every test drop
  const drops = await pg.evaluate(async () => { const { G } = await import('/js/ctx.js'); return []; });
  const list = await pg.evaluate(() => new Promise((res) => { import('/js/ctx.js').then(({ G }) => { G.story.on('drops', (m) => res(m.list)); G.story.send('noop', {}); setTimeout(() => res(null), 50); }); }));
  const dl = await pg.evaluate(async () => { const { nearestDrop } = await import('/js/story/bar.js'); return true; });
  for (let i = 0; i < 11; i++) {
    const a = (i / 11) * Math.PI * 2; await tp([8 * Math.cos(a), 0.1, -2 + 8 * Math.sin(a)]); await sleep(250);
    const h = await pg.evaluate(() => document.querySelector('.st-hint').textContent);
    await key('KeyF'); if (i === 0) { console.log('hint', h); await pg.screenshot({ path: `${OUT}/w3_pick.png` }); }
  }
  console.log('after picks', JSON.stringify(await S()));
  await tp([0, 0.1, 6]); await sleep(300);
  await pg.screenshot({ path: `${OUT}/w3_bar.png` });
  // each bar key: what's in hand / G
  for (let i = 1; i <= 8; i++) { await key('Digit' + i); const s = await S(); console.log('bar', i, s.cur, s.item, s.hp); }
  // fire with whatever's in hand now: the shot reaches the worker (no errors)
  await key('Digit1'); await pg.mouse.move(640, 360); await pg.mouse.down(); await sleep(300); await pg.mouse.up();
  // the wheel: hold Q, move the mouse (pointer-lock is off headless: drive wheelLook directly), click must not fire
  await pg.evaluate(async () => { const { net } = await import('/js/net.js'); window.__sent = []; const s0 = net.ws.send.bind(net.ws); net.ws.send = (d) => { try { const m = JSON.parse(d); if (m.t !== 's' && m.t !== 'pi') window.__sent.push(m.t + ':' + (m.k || m.w || '')); } catch {} return s0(d); }; });
  await pg.keyboard.down('KeyQ'); await sleep(300);
  const ts = await pg.evaluate(async () => { const { G } = await import('/js/ctx.js'); const { wheelLook } = await import('/js/story/wheel.js'); wheelLook(0, 120); return G.story.timeScale(); });
  await pg.mouse.down(); await sleep(100); await pg.mouse.up(); await pg.keyboard.press('Digit2'); await pg.keyboard.press('Space');
  await pg.screenshot({ path: `${OUT}/w3_wheel.png` });
  const leaked = await pg.evaluate(() => window.__sent.slice()); 
  const wpick = await pg.evaluate(() => [...document.querySelectorAll('.st-wedge.pick')].map((c) => c.dataset.i + ':' + (c.querySelector('img') || {}).alt));
  await pg.keyboard.up('KeyQ'); await sleep(300);
  console.log('wedge picked', JSON.stringify(wpick));
  const sw = await S(); console.log('wheel timeScale', ts, 'sent while open', JSON.stringify(leaked), '-> picked slot 5 (down):', sw.cur, sw.item, 'after', (await pg.evaluate(async () => (await import('/js/ctx.js')).G.story.timeScale())));
  // the bag: I opens, drag slot1's thing to bar slot 8, a bag cell to DROP
  await key('KeyI'); await sleep(400);
  await pg.screenshot({ path: `${OUT}/w3_bag.png` });
  await pg.dragTo ? 0 : 0;
  await pg.locator('#storyBag [data-bar="0"]').dragTo(pg.locator('#storyBag [data-bar="7"]')); await sleep(400);
  console.log('dragged bar1 -> bar8', (await S()).bar);
  await pg.locator('#storyBag [data-cell="5"]').dragTo(pg.locator('#storyBag [data-drop]')); await sleep(400);
  console.log('dropped cell 6', JSON.stringify(await S()));
  // click-click: cell 0 then bar 3
  await pg.click('#storyBag [data-cell="0"]'); await pg.click('#storyBag [data-bar="2"]'); await sleep(400);
  console.log('click cell1 -> bar3', (await S()).bar);
  await pg.click('#storyBag .st-btn'); await sleep(300);
  // locker: stand at it, F opens the bag with the locker; stash cell 1, then take it back
  await tp([6, 0.1, -12]); await sleep(300); await key('KeyF'); await sleep(400);
  const hasLocker = await pg.evaluate(() => !!document.querySelector('#storyBag [data-locker]'));
  await pg.locator('#storyBag [data-cell="1"]').dragTo(pg.locator('#storyBag [data-locker]')); await sleep(400);
  const afterStash = await S();
  await pg.screenshot({ path: `${OUT}/w3_locker.png` });
  await pg.locator('#storyBag [data-lk="0"]').dragTo(pg.locator('#storyBag [data-cell="19"]')); await sleep(400);
  console.log('locker shown', hasLocker, 'stash ->', afterStash.locker, afterStash.bag, 'unstash ->', JSON.stringify(await S()));
  await pg.keyboard.press('KeyI'); await sleep(300);
  // drop held (H), then save + reload + continue: the bar comes back
  await key('Digit3'); await key('KeyH'); await sleep(300);
  const before = await S(); console.log('after H', JSON.stringify(before));
  await pg.keyboard.press('KeyB'); await sleep(800); await pg.click('#quit', { force: true }); await sleep(1000);
  await pg.goto(`http://localhost:${PORT}/?story=1`); await sleep(1500);
  await pg.click('#storyBtn', { force: true }); await sleep(700); await pg.click('#storyPick .st-btn.yellow', { force: true }); await sleep(3500);
  const after = await S(); console.log('reloaded', JSON.stringify(after), 'same bar', after.bar === before.bar);
  console.log('ERRORS', errs.length, errs.slice(0, 8).join('\n'));
  await b.close();
})();
