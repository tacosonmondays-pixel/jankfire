// playwright e2e: the boss bar doesn't outlive the fight. m04 in the slice: walk to the Sunset Wall, c4, the cut to the
// gate, the bar is up; then the fight step ends WITHOUT his defeat (the killBoss the Act I e2e fakes): the bar goes, and
// so does he. then on through m04 and into m05: still no bar. run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_bossbar.cjs
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const skipIntro = require('./skipintro.cjs');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const PORT = process.env.PORT || 3311, OUT = process.env.SP + '/shots';
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 960, height: 540 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.addInitScript(() => { localStorage.setItem('jankfire', JSON.stringify({ name: 'bar', jank: 1 })); localStorage.setItem('jf_giftseen_all', '1'); localStorage.removeItem('jfStorySaves'); });
  await pg.goto(`http://localhost:${PORT}/?story=1&storydev=1`); await sleep(1500);
  await pg.click('#storyBtn', { force: true }); await sleep(700); await pg.click('#storyPick .st-btn.yellow', { force: true }); await sleep(9000); await skipIntro(pg);
  const ev = (f, a) => pg.evaluate(f, a);
  const st = () => ev(async () => { const { G } = await import('/js/ctx.js'); const S = window.JF_STORY.S, o = S.quests.objectives().find((x) => x.quest === 'm04_clocking_in'); const bar = document.getElementById('stBossBar');
    return { step: o ? o.step : (S.st.quests.m04_clocking_in || {}).done ? 'DONE' : '-', bar: !!bar && !bar.classList.contains('hidden'), boss: [...G.remotes.values()].filter((r) => /OVERTIME/.test(r.name)).length }; });
  const log = async (t) => { const s = await st(); console.log(t, JSON.stringify(s)); return s; };
  await ev(async () => { const S = window.JF_STORY.S; for (const m of ['m01_return_to_sender', 'm02_soup_run', 'm03_somethings_digesting']) S.st.quests[m] = { done: true, step: '', t: 0 }; S.quests.start('m04_clocking_in'); });
  await sleep(1500); await skipIntro(pg);
  await ev(async () => { const { ME } = await import('/js/player.js'); ME.pos = [-200, 33, 6]; ME.vel = [0, 0, 0]; ME.hold = ME.pos.slice(); });
  await sleep(5000); await skipIntro(pg); // (c4 at the Sunset Wall: its end is the fight)
  let s; for (let i = 0; i < 30; i++) { s = await st(); if (s.bar) break; await sleep(1000); }
  await log('fight'); await pg.screenshot({ path: `${OUT}/bb1_fight.png` });
  await ev(() => { window.JF_STORY.S.emit({ type: 'killBoss', boss: 'overtime_1' }); window.JF_STORY.S.tick(0.1); }); // (a faked end: no defeat in the referee)
  await sleep(3000); await skipIntro(pg); await sleep(1500);
  const after = await log('faked end'); await pg.screenshot({ path: `${OUT}/bb2_after.png` });
  await ev(() => { const S = window.JF_STORY.S; S.run(['flag:heart_ripped', 'flag:truck_choice_made']); S.emit({ type: 'talk', npc: 'overtime', node: 'm04_clocking_in.rescheduled.start' }); S.tick(0.1); S.emit({ type: 'reach', zone: 'bottom:lostfound' }); S.tick(0.1); S.run(['flag:truck_choice_made']); S.tick(0.1); S.emit({ type: 'reach', zone: 'bottom:lostfound' }); S.tick(0.1); });
  await sleep(2000); await skipIntro(pg); await sleep(1500);
  const later = await log('later');
  const ok = after.bar === false && after.boss === 0 && later.bar === false;
  console.log(ok ? 'PASS' : 'FAIL', 'errors', errs.length, errs.slice(0, 4).join(' | '));
  await b.close(); process.exit(ok ? 0 : 1);
})();
