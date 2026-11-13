// playwright e2e: the standard inventory in story (owner: "it should hide your standard inventory"). walking: the story
// bar and the ammo show, multiplayer's hotbar and killstreak tray don't. in a car: no bar, the ammo stays. on the train
// (the Blood Drive in your hands): no bar, no ammo, no weapon name, only THE GAP panel. quit to a training sim: the
// multiplayer hotbar and the tray are back. screenshots go to OUT.
// run: SP=<dir with pwlock.cjs> PORT=<port> OUT=<dir> node tests/story/e2e/t_hidebar.cjs   (needs a running server)
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const fs = require('fs');
const skipIntro = require('./skipintro.cjs');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const OUT = process.env.OUT || '.';
const shown = (pg) => pg.evaluate(() => {
  const v = (s) => { const e = document.querySelector(s); if (!e) return false; const cs = getComputedStyle(e), r = e.getBoundingClientRect(); return cs.display !== 'none' && cs.visibility !== 'hidden' && +cs.opacity > 0 && r.width > 0 && r.height > 0; };
  return { storyBar: v('#storyBar'), hotbar: v('#hotbar'), tray: v('#streakTray'), ammo: v('#ammo'), gap: v('#rpGap'), hands: document.body.classList.contains('st-hands'), car: document.body.classList.contains('st-car') };
});
let fails = 0;
const want = (tag, got, exp) => { const bad = Object.keys(exp).filter((k) => got[k] !== exp[k]); console.log(bad.length ? 'FAIL' : 'ok  ', tag, JSON.stringify(got), bad.length ? 'wanted ' + JSON.stringify(exp) : ''); fails += bad.length ? 1 : 0; };
async function open(b, train) {
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  pg.errs = []; pg.on('pageerror', (e) => pg.errs.push('PAGEERR ' + e.message));
  await pg.addInitScript(() => { localStorage.setItem('jankfire', JSON.stringify({ name: 'hidebar', jank: 3, killcam: false, loadout: { primary: 'ar', secondary: 'pistol', melee: 'knife', item: 'frag' } })); localStorage.setItem('jf_giftseen_all', '1'); localStorage.removeItem('jfStorySaves'); });
  await pg.goto(`http://localhost:${process.env.PORT}/?story=1&storytest=1${train ? '&train=1' : ''}&storydev=1`); await sleep(4000);
  await pg.click('#storyBtn', { force: true }); await sleep(1500); await pg.click('#storyPick .st-btn.yellow', { force: true }); await sleep(3500); await skipIntro(pg);
  await sleep(4000); await skipIntro(pg);
  return pg;
}
(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  // 1. walking on the test lot
  let pg = await open(b, false);
  await sleep(1500); await pg.screenshot({ path: OUT + '/walk.png', timeout: 180000 });
  want('walking', await shown(pg), { storyBar: true, hotbar: false, tray: false, ammo: true, hands: false, car: false });
  // 2. in the sofa-car (t_wp7's spot)
  await pg.evaluate(async () => { const { ME } = await import('/js/player.js'); ME.pos = [-36, 0.1, 33.5]; ME.yaw = 0; }); await sleep(700);
  await pg.keyboard.down('KeyF'); await sleep(80); await pg.keyboard.up('KeyF'); await sleep(1200);
  const drv = await pg.evaluate(async () => { const { driving } = await import('/js/story/drive.js'); return driving(); });
  if (drv) { await pg.screenshot({ path: OUT + '/car.png', timeout: 180000 }); want('driving', await shown(pg), { storyBar: false, tray: false, ammo: true, car: true }); await pg.keyboard.down('KeyF'); await sleep(80); await pg.keyboard.up('KeyF'); await sleep(1000); want('out of the car', await shown(pg), { storyBar: true, car: false }); }
  else { console.log('FAIL never got in the car'); fails++; }
  // 3. quit story into a training sim: multiplayer's own hotbar and tray come back
  await pg.keyboard.press('KeyB'); await sleep(600); await pg.click('#quit', { force: true }); await sleep(1500);
  await pg.click('#scr-main [data-mode="training"]', { force: true }); await sleep(4500);
  await pg.screenshot({ path: OUT + '/sim.png', timeout: 180000 });
  want('training sim', await shown(pg), { storyBar: false, hotbar: true, tray: true, ammo: true, hands: false, car: false });
  const e1 = pg.errs; await pg.close();
  // 4. the train: the Blood Drive in your hands
  pg = await open(b, true);
  for (let i = 0; i < 60; i++) { if (await pg.evaluate(() => !!(window.JF_TRAIN && window.JF_TRAIN.F && window.JF_TRAIN.F.live))) break; await sleep(500); }
  await sleep(2500); await pg.screenshot({ path: OUT + '/train.png', timeout: 180000 });
  want('train fight', await shown(pg), { storyBar: false, hotbar: false, tray: false, ammo: false, gap: true, hands: true });
  // 5. quit the train to the menu and into a sim: all back
  await pg.keyboard.press('KeyB'); await sleep(600); await pg.click('#quit', { force: true }); await sleep(1500);
  await pg.click('#scr-main [data-mode="training"]', { force: true }); await sleep(4500);
  want('sim after the train', await shown(pg), { storyBar: false, hotbar: true, tray: true, ammo: true, hands: false });
  const errs = [...e1, ...pg.errs]; console.log('errors', errs.length, JSON.stringify(errs.slice(0, 3)));
  await b.close();
  console.log(fails || errs.length ? 'FAILED' : 'PASSED');
  process.exit(fails || errs.length ? 1 : 0);
})();
