// playwright e2e: m04 CLOCKING IN's encounter half in the city slice. at the Gut border gate the Gristle & Sons truck
// is being loaded (Dumpling's dad, old Ken, the old woman with the braid) by two collectors, Lumps pinned to its side;
// after the fight the truck choice plays out: chase it (catch it under the rib arch: TRUCK 0417) or stay (pull the
// staple out of Lumps' arm with F). B's Overtime fight itself isn't run here (it's B's test).
// run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_enc_m04.cjs
const { boot, jump, settle, step, sleep } = require('./enc_util.cjs');
const skipIntro = require('./skipintro.cjs');
const OUT = process.env.SP + '/shots';
const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) process.exitCode = 1; };
(async () => {
  const { b, pg, ev, errs } = await boot({ hd: process.env.HD === '1', size: [960, 540] });
  const shot = (n) => pg.screenshot({ path: `${OUT}/m04_${n}.png`, timeout: 120000 });
  const has = (id) => ev(async (id) => (await import('/js/story/actors.js')).actors.has(id), id);
  const endTalks = () => ev(async () => { const tk = await import('/js/story/talk.js'); const sc = await import('/js/story/scene.js'); if (sc.playing()) sc.skipScene(); if (tk.talking()) tk.endTalk(); });
  // ---- sunset: the truck and the queue by the Sunset Wall (so c4's shots have them)
  await settle(ev, [-196, 32.5, 12], 3000);
  ok(await jump(ev, 'm04_clocking_in', 'sunset__at'), 'm04 at the sunset');
  await sleep(2500);
  ok(await ev(() => window.JF_STORY.enc.truck.where === 'sunset' && !!window.JF_STORY.enc.truck.m), 'the truck is parked by the sunset wall');
  ok(await has('enc_dad') && await has('enc_col0'), 'the queue and the collectors are with it');
  await ev(async () => { const { ME } = await import('/js/player.js'); window.__h = setInterval(() => { ME.pos = [-200, 33.5, 16]; ME.vel = [0, 0, 0]; ME.yaw = -0.6; ME.pitch = -0.1; }, 30); });
  await sleep(2000); await shot('sunset'); await ev(() => clearInterval(window.__h));
  // ---- the fight step: the same truck moved up to the gate, being loaded
  await settle(ev, [-38, 36.5, 2], 3000);
  await ev(() => { window.JF_STORY.S.run(['flag:seen_c4']); window.JF_STORY.S.quests.enterStep('m04_clocking_in', 'fight'); });
  await sleep(1500); await skipIntro(pg, 6);
  ok(await ev(() => window.JF_STORY.enc.truck.where === 'gate'), 'the truck moved up to the gate for the fight');
  await ev(async () => { const { G } = await import('/js/ctx.js'); G.story.send('despawn', { kind: 'overtime_1' }); }); // (his fight is B's: out of the way for this one)
  await ev(async () => { const { ME } = await import('/js/player.js'); window.__h = setInterval(() => { ME.pos = [-40, 36.5, 0]; ME.vel = [0, 0, 0]; ME.yaw = -0.45; ME.pitch = -0.08; ME.hp = 100; }, 30); });
  await sleep(2500);
  ok(await ev(() => !!window.JF_STORY.enc && true), 'encounters up');
  ok(await has('lumps') && await ev(async () => { const a = (await import('/js/story/actors.js')).actors.get('lumps'); return !!(a && a.clip && a.clip.name === 'stapled'); }), 'lumps is stapled to the truck');
  ok(await has('enc_col0') && await has('enc_col1'), 'two collectors');
  ok(await has('enc_dad') && await has('enc_ken') && await has('mina'), "dumpling's dad, old ken and the woman with the braid are in the queue");
  await shot('loading');
  for (let i = 0; i < 40 && await ev(async () => (await import('/js/story/actors.js')).actors.has('mina')); i++) await sleep(1000);
  ok(!(await has('enc_dad')) && !(await has('enc_ken')) && !(await has('mina')), 'all three loaded into the truck');
  await shot('loaded');
  await ev(() => clearInterval(window.__h));
  // ---- the truck choice: chase
  await ev(() => { window.JF_STORY.S.quests.enterStep('m04_clocking_in', 'truck'); });
  await sleep(1500);
  await ev(() => { window.JF_STORY.S.run(['flag:chased_truck', 'flag:truck_choice_made', 'flag:saw_mina_twice']); });
  await endTalks(); await sleep(1500); await endTalks();
  ok(await step(ev, 'm04_clocking_in') === 'home', 'chose: chase the truck: ' + await step(ev, 'm04_clocking_in'));
  await sleep(1500);
  // run after it: stand by the first rib arch where it has to wait
  await ev(async () => { const { ME } = await import('/js/player.js'); window.__h = setInterval(() => { ME.pos = [-41.5, 40.5, -68]; ME.vel = [0, 0, 0]; ME.yaw = 0; }, 30); });
  for (let i = 0; i < 40 && !(await ev(() => !!window.JF_STORY.S.st.flags.knows_truck_number)); i++) await sleep(1000);
  ok(await ev(() => !!window.JF_STORY.S.st.flags.knows_truck_number), 'caught it under the arch: you know the truck number');
  await shot('caught');
  await ev(() => clearInterval(window.__h));
  // ---- the other choice: stay with lumps and pull the staple out
  await ev(() => { const f = window.JF_STORY.S.st.flags; for (const k of ['chased_truck', 'truck_choice_made', 'saw_mina_twice', 'knows_truck_number']) delete f[k]; window.JF_STORY.S.quests.enterStep('m04_clocking_in', 'truck'); });
  await settle(ev, [-35, 36.5, -14.5], 2500);
  await ev(() => { window.JF_STORY.S.run(['flag:stayed_with_lumps', 'flag:truck_choice_made']); });
  await endTalks(); await sleep(1500); await endTalks();
  ok(await step(ev, 'm04_clocking_in') === 'home', 'chose: stay with lumps');
  const near = await ev(async () => { const a = (await import('/js/story/actors.js')).actors.get('lumps'); return a ? [a.pos[0] - 1.6, a.pos[1] + 0.4, a.pos[2]] : null; });
  await ev(async (p) => { const { ME } = await import('/js/player.js'); window.__h = setInterval(() => { ME.pos = p.slice(); ME.vel = [0, 0, 0]; ME.yaw = -Math.PI / 2; }, 30); }, near);
  await sleep(1500);
  for (let i = 0; i < 6; i++) { await pg.keyboard.press('KeyF'); await sleep(500); }
  ok(await ev(() => !!window.JF_STORY.S.st.flags.staple_pulled), 'mashed F: the staple is out');
  ok(await ev(async () => { const a = (await import('/js/story/actors.js')).actors.get('lumps'); return !!(a && (!a.clip || a.clip.name !== 'stapled')); }), 'lumps is free');
  await shot('staple');
  await ev(() => clearInterval(window.__h));
  console.log('ERRORS', errs.length, errs.slice(0, 10).join('\n'));
  await b.close();
})();
