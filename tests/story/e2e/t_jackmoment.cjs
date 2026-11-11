// playwright e2e: Jack's moment on its own (the train test route, no city): his clips through the scene (down against
// the fridge, your hand on his chest, the breath out after [FIRE]) and him still down on the deck afterwards.
// run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_jackmoment.cjs   screenshots: $SP/shots/j*.png
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const skipIntro = require('./skipintro.cjs');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const PORT = process.env.PORT || 3311, OUT = process.env.SP + '/shots';
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 960, height: 540 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message + ' ' + (e.stack || '').split('\n')[1]));
  await pg.addInitScript(() => { localStorage.setItem('jankfire', JSON.stringify({ name: 'jack', jank: 1, loadout: { primary: 'ar', secondary: 'pistol', melee: 'knife', item: 'frag' } })); localStorage.setItem('jf_giftseen_all', '1'); localStorage.removeItem('jfStorySaves'); });
  await pg.goto(`http://localhost:${PORT}/?story=1&storydev=1&storytest=1&train=1`); await sleep(1500);
  await pg.click('#storyBtn', { force: true }); await sleep(700); await pg.click('#storyPick .st-btn.yellow', { force: true }); await sleep(8000); await skipIntro(pg);
  const ev = (f, a) => pg.evaluate(f, a);
  const shot = (n) => pg.screenshot({ path: `${OUT}/${n}.png`, timeout: 120000 });
  const Q = 'm06_tickets_please';
  const st = () => ev(async (Q) => { const { actors } = await import('/js/story/actors.js'); const sc = await import('/js/story/scene.js'), tk = await import('/js/story/talk.js'); const S = window.JF_STORY.S, o = S.quests.objectives().find((x) => x.quest === Q);
    const j = actors.get('_scene_jack') || actors.get('rp_pallet_jack'); return { step: o ? o.step : '-', scene: sc.playing(), talk: tk.talking(), opts: [...document.querySelectorAll('.st-opt')].map((x) => x.textContent), jack: j && { id: j.id, clip: j.clip && j.clip.name, hidden: j.hidden } }; }, Q);
  const log = async (t) => { const s = await st(); console.log(t, JSON.stringify(s)); return s; };
  const until = async (fn, ms) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { const s = await st(); if (fn(s)) return s; await sleep(700); } return st(); };
  const ff = (on, k = 0.4) => ev(([on, k]) => { const ST = window.JF_STORY; clearInterval(window.__ff); ST.capture = on; if (on) window.__ff = setInterval(() => { ST.capStep = k; }, 5); }, [on, k]);
  // m06 at the fight (m01-m05 done), on the train
  await ev(async (Q) => { const S = window.JF_STORY.S; for (const m of ['m01_return_to_sender', 'm02_soup_run', 'm03_somethings_digesting', 'm04_clocking_in', 'm05_second_stomach']) S.st.quests[m] = { done: true, step: '', t: 0 }; S.quests.start(Q);
    for (const n of ['the_loop', 'loaner']) S.emit({ type: 'talk', npc: n === 'the_loop' ? 'gordo' : 'bev', node: `${Q}.${n}.start` }); S.emit({ type: 'reach', zone: 'bottom:service_tunnel' }); S.tick(0.1); S.run(['flag:seen_c6_mind_the_gap']); S.tick(0.1); }, Q);
  await sleep(1500); await skipIntro(pg); await ev(() => clearInterval(window.__quiet)); await sleep(4000); await log('hold'); // (skipintro hides the test lot's cast: not here, Jack is who we're looking at)
  await ev(async () => { const { G } = await import('/js/ctx.js'); G.story.send('bossdev', { calm: true }); });
  for (let i = 0; i < 10; i++) { const s = await st(); if (s.step !== 'hold') break; await ev(async () => { const { G } = await import('/js/ctx.js'); G.story.send('bossdev', { dmg: 900, part: 'eye' }); }); await sleep(800); }
  await until((x) => x.scene, 15000); await ff(true, 0.1); await sleep(4000); await log('fall'); await shot('j1_down');
  await ff(true, 0.5); await until((x) => x.jack && x.jack.clip === 'pj_dying_talk', 240000); await ff(true, 0.1); await sleep(5000); await log('hand'); await shot('j2_hand');
  await ff(true, 0.5); await until((x) => x.talk && x.opts.length === 1, 240000); await ff(false); await sleep(500); await shot('j3_fire');
  await pg.mouse.down(); await sleep(80); await pg.mouse.up(); await sleep(400);
  await sleep(1500); await pg.keyboard.press('KeyF'); await sleep(600); // (past the line after it)
  await ff(true, 0.1); await sleep(4000); await log('breath'); await shot('j4_breath');
  await ff(true, 0.5); await until((x) => x.talk && x.opts.length === 1 && /TAKE/.test(x.opts[0]), 240000); await ff(false);
  for (let i = 0; i < 4; i++) { await pg.keyboard.press('KeyF'); await sleep(900); }
  await ff(true, 0.5); await until((x) => !x.scene, 240000); await ff(false); await sleep(3000); await log('after'); await shot('j5_after');
  console.log('ERRORS', errs.length, errs.slice(0, 6).join('\n'));
  await b.close();
})();
