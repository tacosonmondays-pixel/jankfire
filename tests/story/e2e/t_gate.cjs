// playwright e2e: Mr. Overtime at the real Gut Border Gate (the streamed slice, not the test lot). a fresh save is put
// at m04's fight step: the fight cuts you to the arena's start (fade, the place's name), he spawns at the gate, a
// death puts you back at the arena's start, his pool is taken off (dev damage) through the phases to the end, then
// the heart rip, the rescheduled talk, the truck choice and home. run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_gate.cjs
// screenshots: $SP/shots/g*.png
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
  await pg.addInitScript(() => { localStorage.setItem('jankfire', JSON.stringify({ name: 'gate', jank: 2, loadout: { primary: 'ar', secondary: 'pistol', melee: 'knife', item: 'frag' } })); localStorage.setItem('jf_giftseen_all', '1'); if (!sessionStorage.getItem('gt')) { sessionStorage.setItem('gt', 1); localStorage.removeItem('jfStorySaves'); } window.__ev = []; });
  await pg.goto(`http://localhost:${PORT}/?story=1&storydev=1`); await sleep(1500);
  await pg.click('#storyBtn', { force: true }); await sleep(700); await pg.click('#storyPick .st-btn.yellow', { force: true }); await sleep(9000); await skipIntro(pg);
  const ev = (f, a) => pg.evaluate(f, a);
  const shot = (n) => pg.screenshot({ path: `${OUT}/${n}.png`, timeout: 120000 });
  await ev(async () => { const { G } = await import('/js/ctx.js'); G.story.on('combat', (m) => { if (m.ev) window.__ev.push(m.ev); }); });
  const st = () => ev(async () => { const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js'); const S = window.JF_STORY.S, o = S.quests.objectives().find((x) => x.quest === 'm04_clocking_in'); const B = window.JF_STORY.boss;
    return { map: G.cfg && G.cfg.map, me: ME.pos.map((x) => +x.toFixed(1)), alive: ME.alive, yaw: +ME.yaw.toFixed(2), step: o ? o.step : (S.st.quests.m04_clocking_in || {}).done ? 'DONE' : '-', boss: { on: B.on, hp: +B.hp.toFixed(2), phase: B.phase }, remotes: [...G.remotes.values()].map((r) => ({ n: r.name, p: r.pos.map((x) => +x.toFixed(1)) })) }; });
  const skip = () => skipIntro(pg, 30);
  const log = async (t) => console.log(t, JSON.stringify(await st()));
  await log('start');
  // a save at m04 (m01-m03 done), standing at the sunset wall where c4 ends
  await ev(async () => { const { ME } = await import('/js/player.js'); ME.pos = [-200, 33, 6]; ME.vel = [0, 0, 0]; ME.hold = ME.pos.slice(); });
  await sleep(4000);
  await ev(async () => { const S = window.JF_STORY.S; for (const m of ['m01_return_to_sender', 'm02_soup_run', 'm03_somethings_digesting']) S.st.quests[m] = { done: true, step: '', t: 0 }; S.quests.start('m04_clocking_in'); });
  await sleep(2500); await shot('g0_c4'); await log('c4');
  await skip(); // (c4's end, skipped or not, is the fight: the cut to the gate)
  await sleep(200); await shot('g1_fade'); await sleep(2500);
  await log('arrived'); await shot('g2_arrived');
  await sleep(4000); await log('settled'); await shot('g3_facing_him');
  console.log('hits on me', JSON.stringify(await ev(() => window.__ev.filter((e) => e.target === 'me' || e.who === 'me').map((e) => [e.type, e.by, e.weapon, e.dmg, e.hp]))));
  // a death in the fight: back at the arena's start
  await ev(async () => { const { G } = await import('/js/ctx.js'); G.story.send('damage', { id: 'me', dmg: 500, why: 'test' }); });
  await sleep(1500); await log('dead'); await sleep(7000); await log('respawned'); await shot('g4_respawn');
  await ev(async () => { const { G } = await import('/js/ctx.js'); G.story.send('bossdev', { calm: true }); }); // (the rest is the fight's flow, not a duel: he holds his attacks)
  // his pool off in chunks (dev damage through the room), skipping the phase scenes as they come
  for (let i = 0; i < 30; i++) {
    const s = await st(); if (s.step !== 'fight') break;
    await ev(async () => { const { G } = await import('/js/ctx.js'); G.story.send('damage', { id: 'overtime_1', dmg: 300, why: 'test' }); });
    await sleep(700);
    if (i === 6) await shot('g5_fighting');
    const locked = await ev(async () => (await import('/js/story/boot.js')).locked());
    if (locked) { await shot(`g6_scene_${i}`); await skip(); }
  }
  await log('after fight'); await shot('g7_beaten');
  const scenesOnly = () => ev(async () => { const sc = await import('/js/story/scene.js'); if (sc.playing()) sc.skipScene(); }); // (talks and choices are answered, not skipped)
  const talk = () => ev(async () => (await import('/js/story/talk.js')).talking());
  let closed = false;
  for (let i = 0; i < 40; i++) { const s = await st(); if (i % 4 === 0) console.log('step', s.step); if (s.step === 'DONE' || s.step === 'home') break;
    await scenesOnly();
    if (s.step === 'after' && !(await talk())) { await ev(async () => { const { ME } = await import('/js/player.js'); const { actors } = await import('/js/story/actors.js'); const a = actors.get('overtime'); if (a) { ME.pos = [a.pos[0] - Math.sin(a.yaw) * 2.2, a.pos[1] + 0.2, a.pos[2] - Math.cos(a.yaw) * 2.2]; ME.yaw = a.yaw + Math.PI; } }); await sleep(800); await pg.keyboard.press('KeyF'); await sleep(1500); await shot('g8_rescheduled'); }
    else if (await talk()) { const opts = await ev(() => [...document.querySelectorAll('.st-opt')].map((x) => x.textContent)); if (s.step === 'truck' && opts.length && !closed) { closed = true; await ev(async () => (await import('/js/story/talk.js')).endTalk()); await sleep(7000); console.log('closed with Esc, offered again:', await talk()); } // (it has to come back)
      else if (s.step === 'truck' && opts.length) { await shot('g9_truck'); console.log('truck options', JSON.stringify(opts)); await pg.keyboard.press('Digit2'); } else await pg.keyboard.press('KeyF'); }
    await sleep(900); }
  await log('end'); await shot('g10_end');
  const evs = await ev(() => window.__ev.filter((e) => e.type !== 'hit').map((e) => e.type + ':' + (e.phase ?? e.state ?? e.boss ?? e.who ?? '')));
  console.log('events', evs.slice(0, 40).join(' '));
  console.log('ERRORS', errs.length, errs.slice(0, 10).join('\n'));
  await b.close();
})();
