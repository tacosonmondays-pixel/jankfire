// playwright e2e: the chapter select on the story slot picker. FROM THE BEGINNING on a filled slot asks first, then a
// new game in it; START FROM OVERTIME lands at the Gut Border Gate with m04 on its fight and him there; START FROM THE
// TRAIN lands on the train, the ride in, then the fight. the jumps' scratch slot never touches the real slots.
// screenshots go to OUT (JANK=3 Too HD by default).
// run: SP=<dir with pwlock.cjs> PORT=<port> OUT=<dir> node tests/story/e2e/t_chapters.cjs   (needs a running server)
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const fs = require('fs');
const skipIntro = require('./skipintro.cjs');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const OUT = process.env.OUT || '.', JANK = Number(process.env.JANK || 3);
let fails = 0;
const check = (tag, ok, info) => { console.log(ok ? 'ok  ' : 'FAIL', tag, info ? JSON.stringify(info) : ''); if (!ok) fails++; };
// a real slot 0 with some progress on it (what FROM THE BEGINNING has to ask about, and what the jumps must not touch)
const REAL = { v: 1, slot: 0, act: 1, chapter: 'm02_sauce_run', playtime: 900, coupons: 77, at: { map: 'story_slice', p: [-189, 8, 200], yaw: 0 }, data: { flags: ['init_done', 'named_change'], quests: { m01_return_to_sender: { done: true, step: '', t: 0 }, m02_sauce_run: { step: 'brief', n: [0], t: 0 } }, seen: [] } };
(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = []; pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message));
  await pg.addInitScript(([real, jank]) => {
    if (sessionStorage.getItem('chap')) return; sessionStorage.setItem('chap', 1);
    localStorage.setItem('jankfire', JSON.stringify({ name: 'chapters', jank, killcam: false, loadout: { primary: 'ar', secondary: 'pistol', melee: 'knife', item: 'frag' } }));
    localStorage.setItem('jf_giftseen_all', '1'); localStorage.setItem('jfStorySaves', JSON.stringify([real, null, null])); localStorage.removeItem('jfStoryJump');
  }, [REAL, JANK]);
  await pg.goto(`http://localhost:${process.env.PORT}/?story=1`); await sleep(4000);
  const st = () => pg.evaluate(async () => {
    const { G } = await import('/js/ctx.js'); const ST = window.JF_STORY; const o = ST && ST.S ? ST.S.quests.objectives().find((x) => x.kind === 'main') : null;
    const { MAP } = await import('/shared/map.js');
    return { joined: G.joined, mode: G.mode, map: MAP.id, slot: G.story.cur && G.story.cur.slot, quest: o && o.quest, step: o && o.step, live: !!(window.JF_TRAIN && window.JF_TRAIN.F && window.JF_TRAIN.F.live), boss: !!(ST && ST.boss && ST.boss.on), real: JSON.parse(localStorage.getItem('jfStorySaves') || '[]')[0], jump: !!localStorage.getItem('jfStoryJump') };
  });
  const quit = async () => { await pg.keyboard.press('KeyB'); await sleep(700); await pg.click('#quit', { force: true }); await sleep(2000); };
  const open = async () => { await pg.click('#storyBtn', { force: true }); await sleep(1500); };
  // 1. the picker
  await open(); await pg.screenshot({ path: OUT + '/menu.png' });
  check('menu has the chapter select', await pg.evaluate(() => !!document.querySelector('#storyPick [data-jump="train"]') && !!document.querySelector('#storyPick [data-jump="overtime"]') && !!document.querySelector('#storyPick [data-begin="0"]')));
  // 2. Overtime
  await pg.click('#storyPick [data-jump="overtime"]', { force: true }); await sleep(6000); await skipIntro(pg); await sleep(2000);
  let s; for (let i = 0; i < 40; i++) { await skipIntro(pg, 2); s = await st(); if (s.boss) break; await sleep(1000); }
  await sleep(2500); await skipIntro(pg, 2); await pg.screenshot({ path: OUT + '/overtime.png' });
  check('overtime: m04 on the fight, in the city, him spawned, the jump slot', s.joined && s.map === 'story_slice' && s.quest === 'm04_clocking_in' && s.step === 'fight' && s.boss && s.slot === 3, { ...s, real: !!s.real });
  await pg.evaluate(async () => { const { G } = await import('/js/ctx.js'); G.story.save('test'); }); await sleep(1500);
  s = await st(); check('overtime: saved to the scratch slot, the real slot 0 untouched', s.jump && s.real && s.real.coupons === 77 && s.real.chapter === 'm02_sauce_run');
  await quit();
  // 3. the train
  await open(); await pg.click('#storyPick [data-jump="train"]', { force: true }); await sleep(6000);
  for (let i = 0; i < 60; i++) { await skipIntro(pg, 2); s = await st(); if (s.live) break; await sleep(1000); }
  await sleep(2500); await pg.screenshot({ path: OUT + '/train.png' });
  check('train: on the train, m06 at the fight, the fight live', s.map === 'story_train' && s.quest === 'm06_tickets_please' && s.step === 'hold' && s.live, s && { ...s, real: !!s.real });
  await quit();
  // 4. FROM THE BEGINNING on the filled slot: it asks, then a new game in slot 0
  await open(); await pg.click('#storyPick [data-begin="0"]', { force: true }); await sleep(400);
  await pg.screenshot({ path: OUT + '/begin_ask.png' });
  check('begin: it asks first', await pg.evaluate(() => /are you sure\? this wipes your slot/.test(document.querySelector('#storyPick .st-wipe') ? document.querySelector('#storyPick .st-wipe').textContent : '')));
  await pg.click('#storyPick .st-wipe .st-btn.red', { force: true }); await sleep(7000); await skipIntro(pg); await sleep(1500);
  s = await st(); check('begin: a new game in slot 0 (m01)', s.joined && s.slot === 0 && s.quest === 'm01_return_to_sender', { ...s, real: s.real && s.real.chapter });
  console.log('errors', errs.length, JSON.stringify(errs.slice(0, 4)));
  await b.close();
  console.log(fails || errs.length ? 'FAILED' : 'PASSED');
  process.exit(fails || errs.length ? 1 : 0);
})();
