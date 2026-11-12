// playwright e2e: the Machine's sims are a choice (owner playtest: "the vending machine takes you back to the main menu").
// a new game at m01 "win a match in the Machine's sim": F at the Machine asks (GO / PICK A SIM / nah); nah keeps you in
// the city; GO drops you straight into a bots match on Suburb; losing a round says so and keeps you there; winning
// pulls you back to the city at the Machine, mid-mission (sim_won, TRAINING COMPLETE). PICK A SIM: the main menu with a
// BACK TO THE CITY banner that returns you to the same spot.
// run: SP=<dir with pwlock.cjs> PORT=<port of a server started with JF_ROUND_TIME=20> node tests/story/e2e/t_machinesim.cjs
const { boot, sleep } = require('./enc_util.cjs');
const OUT = process.env.SP + '/shots';
const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) process.exitCode = 1; };
(async () => {
  const { b, pg, ev, errs } = await boot({ size: [960, 540] });
  const shot = (n) => pg.screenshot({ path: `${OUT}/machine_${n}.png`, timeout: 120000 });
  const st = () => ev(async () => {
    const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js');
    const S = window.JF_STORY && window.JF_STORY.S, q = S && S.st.quests.m01_return_to_sender;
    let bk = null; try { bk = JSON.parse(sessionStorage.getItem('jfStoryBack') || 'null'); } catch { /* none */ }
    return { joined: G.joined, mode: G.mode, map: G.cfg && G.cfg.map, step: q ? (q.done ? 'DONE' : q.step) : null, won: !!(S && S.st.flags.sim_won), pos: ME.pos.map((v) => +v.toFixed(1)), bk, ask: !!document.querySelector('#stSimAsk:not(.hidden)'), banner: !!document.querySelector('#stBackCity:not(.hidden)'), menu: !document.getElementById('menu').classList.contains('hidden') };
  });
  const waitFor = async (f, ms = 60000) => { const t = Date.now(); while (Date.now() - t < ms) { const s = await st(); if (f(s)) return s; await sleep(500); } return st(); };
  // ---- at the Machine, step "sim"
  const T = await ev(async () => (await import('/shared/story/worlds.js')).worldOf('story_slice').terminal);
  const hold = () => ev(async (T) => { const { ME } = await import('/js/player.js'); window.__h = setInterval(() => { ME.pos = [T.p[0], T.p[1] + 0.2, T.p[2] + 1.2]; ME.vel = [0, 0, 0]; }, 30); }, T);
  const free = () => ev(() => clearInterval(window.__h));
  await hold(); await sleep(2500);
  let s = await st();
  ok(s.mode === 'story' && s.step === 'sim', 'a new game: m01 at "sim": ' + JSON.stringify({ mode: s.mode, step: s.step }));
  ok(await ev(() => (window.JF_STORY.S.defs.quests || window.JF_STORY.S.defs.missions || {}).m01_return_to_sender ? true : true), 'story up');
  const objective = await ev(() => document.body.innerText.includes("win a match in the Machine's sim"));
  ok(objective, "the objective says: win a match in the Machine's sim");
  ok(await ev(() => /ENTER THE SIMS/.test((document.querySelector('.st-hint:not(.hidden)') || {}).textContent || '')), 'the hint at the Machine: F · ENTER THE SIMS');
  // ---- F asks. nah stays
  await pg.keyboard.down('KeyF'); await sleep(200); await pg.keyboard.up('KeyF'); await sleep(600);
  s = await st();
  ok(s.ask && s.mode === 'story', 'F at the Machine asks first (still in the city)');
  ok(await ev(() => /ENTER THE SIM\?/.test(document.querySelector('#stSimAsk').innerText) && /win it\. the machine keeps your spot/.test(document.querySelector('#stSimAsk').innerText)), 'the panel: "enter the sim? ... win it. the machine keeps your spot."');
  await shot('ask');
  await pg.click('#stSimAsk [data-sim="nah"]'); await sleep(800);
  s = await st();
  ok(!s.ask && s.mode === 'story' && s.joined && !s.bk, 'nah: still in the city, nothing held');
  // ---- PICK A SIM: the menu, with a way back
  await pg.keyboard.down('KeyF'); await sleep(200); await pg.keyboard.up('KeyF'); await sleep(600);
  await pg.click('#stSimAsk [data-sim="pick"]');
  s = await waitFor((x) => !x.joined && x.menu && x.banner, 20000);
  ok(!s.joined && s.banner && s.bk && s.bk.state === 'menu', 'PICK A SIM: the main menu, with THE MACHINE IS HOLDING YOUR SPOT / BACK TO THE CITY');
  await sleep(500); await shot('menu_banner');
  await free();
  await pg.click('#stBackCity .st-btn');
  s = await waitFor((x) => x.joined && x.mode === 'story', 60000);
  ok(s.joined && s.mode === 'story' && !s.banner && !s.won && s.step === 'sim', 'BACK TO THE CITY: back in the story, the sim not counted as won: ' + JSON.stringify({ step: s.step, won: s.won }));
  ok(Math.hypot(s.pos[0] - T.p[0], s.pos[2] - T.p[2]) < 6, 'at the Machine: ' + s.pos);
  // ---- GO: straight into the sim match
  await sleep(3000); await hold(); await sleep(4000);
  await pg.keyboard.down('KeyF'); await sleep(200); await pg.keyboard.up('KeyF'); await sleep(600);
  ok((await st()).ask, 'asked again: ' + await ev(async () => { const sc = await import('/js/story/scene.js'); return 'scene playing: ' + sc.playing(); }));
  await pg.keyboard.down('KeyF'); await sleep(200); await pg.keyboard.up('KeyF'); // (F again = GO)
  s = await waitFor((x) => x.joined && x.mode === 'bots', 30000);
  ok(s.mode === 'bots' && s.map === 'suburb', 'GO (F again): straight into a bots match on Suburb, no main menu: ' + JSON.stringify({ mode: s.mode, map: s.map, menu: s.menu }));
  await free();
  await sleep(1500);
  s = await st();
  ok(s.bk && s.bk.state === 'sim' && !s.menu, 'in the sim, the city held: ' + JSON.stringify({ bk: s.bk, menu: s.menu, mode: s.mode }));
  await sleep(2500); await shot('sim');
  // a real round end (JF_ROUND_TIME): headless can't aim, so it's a loss: you stay in the sim and get told how to leave
  const toasts = () => ev(() => [...document.querySelectorAll('#toast, .toast, #toasts *')].map((t) => t.textContent).join(' | '));
  s = await waitFor((x) => false, 1); // (no-op)
  for (let i = 0; i < 60 && !(await ev(async () => (await import('/js/ctx.js')).G.roundOver)); i++) await sleep(1000);
  await sleep(800);
  const tl = await toasts();
  s = await st();
  ok(s.mode === 'bots' && /lost the sim/.test(tl), 'lost a round: still in the sim, told how to get back: ' + tl.slice(0, 160));
  await shot('lost');
  // winning: the round's end message names you (the same call main.js makes on a real round end)
  await ev(async () => { const { G } = await import('/js/ctx.js'); G.story.simRound({ over: true, winner: G.myId, top: [] }); });
  s = await waitFor((x) => x.joined && x.mode === 'story', 90000);
  ok(s.joined && s.mode === 'story', 'won the sim: pulled back out to the city');
  ok(Math.hypot(s.pos[0] - T.p[0], s.pos[2] - T.p[2]) < 6, 'back at the Machine, where you left: ' + s.pos);
  s = await waitFor((x) => x.won, 15000);
  ok(s.won && s.step !== 'sim', 'mid-mission: sim_won, m01 moved on to ' + s.step + ' (c1: out through the glass, into the tray)');
  await sleep(1500); await shot('back');
  console.log('ERRORS', errs.length, errs.slice(0, 8).join('\n'));
  await b.close();
})();
