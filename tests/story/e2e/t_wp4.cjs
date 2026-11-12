// playwright e2e (WP4). run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_wp4.cjs
// beams per rarity, the compare card, rolled stats reach the weapon code (and stop in a sim), save/load keeps loot fields
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const skipIntro = require('./skipintro.cjs'); // the intro cinematic holds the keys: skip it
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const PORT = process.env.PORT || 3311, OUT = process.env.SP + '/shots';
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message + ' ' + (e.stack || '').split('\n')[1]));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.addInitScript(() => { localStorage.setItem('jankfire', JSON.stringify({ name: 'wp4', jank: 3, loadout: { primary: 'ar', secondary: 'pistol', melee: 'knife', item: 'frag' } })); if (!sessionStorage.getItem('w4')) { sessionStorage.setItem('w4', 1); localStorage.removeItem('jfStorySaves'); } });
  await pg.goto(`http://localhost:${PORT}/?story=1&storydev=1&storytest=1`); await sleep(1500);
  await pg.click('#storyBtn', { force: true }); await sleep(700); await pg.click('#storyPick .st-btn.yellow', { force: true }); await sleep(3500); await skipIntro(pg);
  const tp = (p, yaw = 0, pitch = 0) => pg.evaluate(async ([p, yaw, pitch]) => { const { ME } = await import('/js/player.js'); ME.pos = p.slice(); ME.vel = [0, 0, 0]; ME.yaw = yaw; ME.pitch = pitch; }, [p, yaw, pitch]);
  // the row of rarities by the north wall (z = -24): stand back and look at it
  await tp([-6, 0.1, -12], 0, 0.15); await sleep(1500);
  await pg.screenshot({ path: `${OUT}/w4_beams.png` });
  await tp([5, 0.1, -16], -0.3, 0.3); await sleep(1500);
  await pg.screenshot({ path: `${OUT}/w4_named.png` });
  // walk up to the premium one: the card shows with arrows against the AR in hand
  await tp([0, 0.1, -22.5], 0, -0.3); await sleep(800);
  const card = await pg.evaluate(() => { const c = document.querySelector('.st-lootcard:not(.hidden) .st-lcard'); return c ? { txt: c.innerText.replace(/\s+/g, ' ').slice(0, 300), ups: c.querySelectorAll('.st-up').length, dns: c.querySelectorAll('.st-dn').length } : null; });
  console.log('card', JSON.stringify(card));
  await pg.screenshot({ path: `${OUT}/w4_card.png` });
  await skipIntro.clearF(pg); // (a memory / quest marker nearby takes F first)
  // pick it up, put it on slot 1, compare its magazine + fire interval to a plain AR
  await pg.keyboard.down('KeyF'); await sleep(80); await pg.keyboard.up('KeyF'); await sleep(600);
  const r = await pg.evaluate(async () => {
    const { IV } = await import('/js/story/bar.js'); const { G } = await import('/js/ctx.js'); const { W, magOf, STAT } = await import('/js/weapons.js'); const { statsOf } = await import('/shared/story/loot.js'); const { WEAPONS } = await import('/shared/weapons.js');
    const it = IV.inv.bag.find((x) => x && x.r === 'premium'); if (!it) return 'no premium in bag';
    G.story.send('inv', { op: 'bar', slot: 4, u: it.u }); await new Promise((r) => setTimeout(r, 500));
    return { b: it.b, r: it.r, s: statsOf(it), baseMag: WEAPONS[it.b].mag, it };
  });
  console.log('premium', JSON.stringify(r).slice(0, 300));
  await pg.keyboard.press('Digit5'); await sleep(700);
  const held = await pg.evaluate(async () => { const { W, magOf, STAT } = await import('/js/weapons.js'); return { cur: W.cur, mag: magOf(W.cur), mul: STAT.mul ? STAT.mul(W.cur, 'rate') : null }; });
  console.log('held', JSON.stringify(held), 'expected mag', r.baseMag ? Math.round(r.baseMag * r.s.mag) : 'none (a gadget: no magazine)', 'expected rate x', r.s.rate);
  // into a sim and back: no rolled stats in multiplayer
  await tp([0, 0.1, -12]); await sleep(400);
  await pg.keyboard.down('KeyF'); await sleep(80); await pg.keyboard.up('KeyF'); await sleep(1500);
  await pg.click('#scr-main [data-mode="training"]', { force: true }); await sleep(3500);
  const sim = await pg.evaluate(async () => { const { G } = await import('/js/ctx.js'); const { STAT, magOf } = await import('/js/weapons.js'); return { mode: G.mode, mul: STAT.mul, mag: magOf('ar') }; });
  console.log('in sim', JSON.stringify(sim));
  await pg.keyboard.press('KeyB'); await sleep(600); await pg.click('#quit', { force: true }); await sleep(3500);
  // reload the page: the premium still has its seed, brand, mods
  await pg.keyboard.press('KeyB'); await sleep(800); await pg.click('#quit', { force: true }); await sleep(1000);
  await pg.goto(`http://localhost:${PORT}/?story=1&storydev=1&storytest=1`); await sleep(1500);
  await pg.click('#storyBtn', { force: true }); await sleep(700); await pg.click('#storyPick .st-btn.yellow', { force: true }); await sleep(3500); await skipIntro(pg);
  const back = await pg.evaluate(async () => { const { IV } = await import('/js/story/bar.js'); return IV.inv.bag.find((x) => x && x.r === 'premium') || null; });
  console.log('after reload', JSON.stringify(back), 'same', JSON.stringify({ ...back, u: 0 }) === JSON.stringify({ ...r.it, u: 0 }));
  await pg.keyboard.press('KeyI'); await sleep(500);
  await pg.hover(`#storyBag [data-cell]:has(img[alt])`); await sleep(300);
  await pg.screenshot({ path: `${OUT}/w4_bag.png` });
  console.log('ERRORS', errs.length, errs.slice(0, 8).join('\n'));
  await b.close();
})();
