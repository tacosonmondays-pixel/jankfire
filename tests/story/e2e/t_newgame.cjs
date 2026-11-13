// playwright e2e: a new game always starts Act I (owner: "how do I play act 1 of the story when i start new it starts me
// at the train fight"). on the old train demo link (?story=1&storytest=1&train=1, no storydev), NEW GAME in each real
// slot, before and after a chapter-select train jump, and FROM THE BEGINNING, all start m01 in the city (story_slice),
// and stay there. the picker says TEST MODE only on a dev link (storydev + storytest), where new games go to the test lot.
// run: SP=<dir with pwlock.cjs> PORT=<port> OUT=<dir> node tests/story/e2e/t_newgame.cjs   (needs a running server)
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const fs = require('fs');
const skipIntro = require('./skipintro.cjs');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const OUT = process.env.OUT || '.', BASE = `http://localhost:${process.env.PORT}`;
let fails = 0;
const check = (tag, ok, info) => { console.log(ok ? 'ok  ' : 'FAIL', tag, info ? JSON.stringify(info) : ''); if (!ok) fails++; };
(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const ctx = await b.newContext({ viewport: { width: 960, height: 540 } });
  await ctx.addInitScript(() => { if (sessionStorage.getItem('ng')) return; sessionStorage.setItem('ng', 1); localStorage.setItem('jankfire', JSON.stringify({ name: 'newgame', jank: 0, loadout: { primary: 'ar', secondary: 'pistol', melee: 'knife', item: 'frag' } })); localStorage.setItem('jf_giftseen_all', '1'); localStorage.removeItem('jfStorySaves'); localStorage.removeItem('jfStoryJump'); });
  const pg = await ctx.newPage(); const errs = []; pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message));
  const st = () => pg.evaluate(async () => { const { G } = await import('/js/ctx.js'); const { MAP } = await import('/shared/map.js'); const ST = window.JF_STORY; const o = ST && ST.S ? ST.S.quests.objectives().find((x) => x.kind === 'main') : null; return { map: MAP.id, slot: G.story.cur && G.story.cur.slot, q: o && o.quest }; });
  // where the run is over ~15 s (the train used to take a new game a few seconds in): every sample must be Act I in the city
  const act1 = async (tag, slot) => { const seen = new Set(); let s; for (let i = 0; i < 6; i++) { await skipIntro(pg, 1); s = await st(); seen.add(`${s.map}|${s.q}|${s.slot}`); await sleep(2500); } check(tag, seen.size === 1 && s.map === 'story_slice' && s.q === 'm01_return_to_sender' && s.slot === slot, [...seen]); };
  const quit = async () => { await pg.keyboard.press('KeyB'); await sleep(700); await pg.click('#quit', { force: true }); await sleep(2500); };
  const open = async () => { await pg.click('#storyBtn', { force: true }); await sleep(2000); };
  const newGame = async (i) => { await open(); await pg.click(`#storyPick .st-slot:nth-child(${i + 1}) .st-btn.yellow`, { force: true }); await sleep(6000); };
  // 1. the old train demo link: no TEST MODE, a new game is Act I
  await pg.goto(`${BASE}/?story=1&storytest=1&train=1`); await sleep(5000);
  await open(); await pg.screenshot({ path: OUT + '/oldlink_picker.png' });
  check('old link: no TEST MODE tag', !(await pg.$('#storyPick .st-test')));
  await pg.click('#storyPick .st-slot:nth-child(1) .st-btn.yellow', { force: true }); await sleep(6000);
  await act1('old link: NEW GAME slot 1 is Act I in the city', 0); await pg.screenshot({ path: OUT + '/oldlink_newgame.png' }); await quit();
  // 2. a chapter-select train jump, then every real slot
  await open(); await pg.click('#storyPick [data-jump="train"]', { force: true }); await sleep(8000); await skipIntro(pg, 3);
  check('the train jump is on the train', (await st()).map === 'story_train'); await quit();
  await newGame(1); await act1('after the jump: NEW GAME slot 2 is Act I', 1); await quit();
  await newGame(2); await act1('after the jump: NEW GAME slot 3 is Act I', 2); await quit();
  await open(); await pg.click('#storyPick [data-begin="0"]', { force: true }); await sleep(400); await pg.click('#storyPick .st-wipe .st-btn.red', { force: true }); await sleep(6000);
  await act1('after the jump: FROM THE BEGINNING slot 1 is Act I', 0); await quit();
  // 3. a dev link still gets the test lot, and says so
  await pg.goto(`${BASE}/?story=1&storydev=1&storytest=1`); await sleep(5000); await open();
  check('dev link: TEST MODE tag', /TEST MODE/.test(await pg.evaluate(() => (document.querySelector('#storyPick .st-test') || {}).textContent || '')));
  await pg.screenshot({ path: OUT + '/devlink_picker.png' });
  console.log('errors', errs.length, JSON.stringify(errs.slice(0, 3)));
  await b.close();
  console.log(fails || errs.length ? 'FAILED' : 'PASSED');
  process.exit(fails || errs.length ? 1 : 0);
})();
