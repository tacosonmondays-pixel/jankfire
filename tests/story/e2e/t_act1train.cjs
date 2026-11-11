// playwright e2e: m06 TICKETS, PLEASE on a fresh save, the way a player gets through it: board at the service tunnel,
// the ride in (c6_mind_the_gap), the fade onto the train, phase 1 (dev damage) to its scripted end, Jack's moment
// played through with [FIRE] and [TAKE] taken with your own trigger and use key, phases 2 and 3, the terminus, P5b, and
// the fade back out into the slice with act1_done. run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_act1train.cjs
// screenshots: $SP/shots/t*.png
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const skipIntro = require('./skipintro.cjs');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const PORT = process.env.PORT || 3311, OUT = process.env.SP + '/shots';
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message + ' ' + (e.stack || '').split('\n')[1]));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.addInitScript(() => { localStorage.setItem('jankfire', JSON.stringify({ name: 'train', jank: 2, loadout: { primary: 'ar', secondary: 'pistol', melee: 'knife', item: 'frag' } })); localStorage.setItem('jf_giftseen_all', '1'); if (!sessionStorage.getItem('tr')) { sessionStorage.setItem('tr', 1); localStorage.removeItem('jfStorySaves'); } });
  await pg.goto(`http://localhost:${PORT}/?story=1&storydev=1`); await sleep(1500);
  await pg.click('#storyBtn', { force: true }); await sleep(700); await pg.click('#storyPick .st-btn.yellow', { force: true }); await sleep(9000); await skipIntro(pg);
  const ev = (f, a) => pg.evaluate(f, a);
  const shot = (n) => pg.screenshot({ path: `${OUT}/${n}.png`, timeout: 120000 });
  const Q = 'm06_tickets_please';
  const st = () => ev(async (Q) => { const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js'); const sc = await import('/js/story/scene.js'), tk = await import('/js/story/talk.js'); const S = window.JF_STORY.S, o = S.quests.objectives().find((x) => x.quest === Q), T = window.JF_TRAIN;
    return { map: G.cfg && G.cfg.map, me: ME.pos.map((x) => +x.toFixed(1)), step: o ? o.step : (S.st.quests[Q] || {}).done ? 'DONE' : '-', scene: sc.playing(), talk: tk.talking(), opts: [...document.querySelectorAll('.st-opt')].map((x) => x.textContent), live: T && T.F.live, phase: T && T.F.phase,
      flags: ['jack_fired', 'jack_marrow_taken', 'seen_mo_carry', 'act1_done', 'train_unlocked'].filter((f) => S.st.flags[f]) }; }, Q);
  const log = async (t) => { const s = await st(); console.log(t, JSON.stringify(s)); return s; };
  const until = async (fn, ms, every = 500) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { const s = await st(); if (fn(s)) return s; await sleep(every); } return st(); };
  const dev = (o) => ev(async (o) => { const { G } = await import('/js/ctx.js'); G.story.send('bossdev', o); }, o);
  // a save at m06 (m01-m05 done), fitted and ready to board
  await ev(async (Q) => { const S = window.JF_STORY.S; for (const m of ['m01_return_to_sender', 'm02_soup_run', 'm03_somethings_digesting', 'm04_clocking_in', 'm05_second_stomach']) S.st.quests[m] = { done: true, step: '', t: 0 }; S.quests.start(Q);
    S.emit({ type: 'talk', npc: 'gordo', node: `${Q}.the_loop.start` }); S.tick(0.1); S.emit({ type: 'talk', npc: 'bev', node: `${Q}.loaner.start` }); S.tick(0.1); }, Q);
  await sleep(1500); await skipIntro(pg); await log('board');
  // walk into the service tunnel (its zone, wherever the world has it)
  await ev(async () => { const { ME } = await import('/js/player.js'); const p = window.JF_STORY.where('bottom:service_tunnel'); ME.pos = [p[0], p[1] + 0.5, p[2]]; ME.vel = [0, 0, 0]; ME.hold = ME.pos.slice(); });
  let s = await until((x) => x.step === 'ride', 15000); await sleep(2500); await shot('t1_ride_in'); await log('ride');
  await skipIntro(pg); // (the ride's end: the fade onto the train)
  await sleep(250); await shot('t2_fade');
  s = await until((x) => x.map === 'story_train' && x.live, 90000); await sleep(2000); await shot('t3_on_the_train'); await log('train');
  await dev({ calm: true });
  for (let i = 0; i < 10; i++) { s = await st(); if (s.step !== 'hold') break; await dev({ dmg: 900, part: 'eye' }); await sleep(800); }
  s = await until((x) => x.scene, 15000); await sleep(4000); await shot('t4_jack_moment'); await log('jack');
  s = await until((x) => x.talk && x.opts.length === 1, 120000, 1000); await shot('t5_fire_prompt'); await log('fire prompt');
  await pg.mouse.down(); await sleep(80); await pg.mouse.up(); await sleep(700); await shot('t6_fired'); // your own trigger
  s = await until((x) => x.talk && x.opts.length === 1 && /TAKE/.test(x.opts[0]), 60000, 1000); await shot('t7_take_prompt');
  await pg.keyboard.press('KeyF'); await sleep(1500); await shot('t8_taken'); await log('taken');
  s = await until((x) => x.step === 'break', 60000, 1000); await log('break');
  await skipIntro(pg); await sleep(2500); await dev({ calm: true });
  for (let i = 0; i < 30; i++) { s = await st(); if (s.step !== 'break') break; if (s.live) await dev({ dmg: 900, i: i % 8 }); if (i === 4) await shot('t9_phase2'); await sleep(900); if (s.scene || s.talk) await skipIntro(pg); }
  await sleep(3000); await shot('t10_finish'); await log('beaten');
  for (let i = 0; i < 10; i++) { s = await st(); if (s.step === 'DONE') break; if (s.scene) { await shot(`t11_${s.step}`); await sleep(1500); await skipIntro(pg); } await sleep(1500); }
  s = await until((x) => x.map === 'story_slice', 90000, 1000); await sleep(4000); await shot('t12_back_out'); await log('back');
  console.log('ERRORS', errs.length, errs.slice(0, 10).join('\n'));
  await b.close();
})();
