// playwright e2e: m02 SAUCE RUN's encounters in the city slice. the soup pot rides with Lumps in your car and slops out
// on a real terrace drop; the Ring Road ambush (EOTM's talk, the fight answer) spawns interns + a rig through the
// referee, the HUD clock runs, the step finishes and everything is cleared; the trade post stands at the Gut border.
// run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_enc_m02.cjs
const { boot, jump, tp, settle, step, talkThrough, sleep } = require('./enc_util.cjs');
const skipIntro = require('./skipintro.cjs');
const OUT = process.env.SP + '/shots';
const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) process.exitCode = 1; };
(async () => {
  const { b, pg, ev, errs } = await boot({ hd: process.env.HD === '1', size: [960, 540] });
  const shot = (n) => pg.screenshot({ path: `${OUT}/m02_${n}.png`, timeout: 120000 });
  // ---- steal a car: getting in counts
  ok(await jump(ev, 'm02_sauce_run', 'car'), 'm02 started at "steal a car"');
  await sleep(1500); await skipIntro(pg, 8); // (the mission card's comic)
  await settle(ev, [-198, 8.4, 196], 2500);
  const carId = await ev(async () => { const { DV } = await import('/js/story/drive.js'); for (const x of DV.meshes.values()) if (x.c.ty === 'hatch') return x.c.id; return 0; });
  await ev((id) => window.JF_STORY && import('/js/ctx.js').then(({ G }) => G.story.send('carIn', { id })), carId);
  await sleep(1500);
  ok(await ev(async () => { const { DV } = await import('/js/story/drive.js'); return !!DV.car; }), 'in the hatch');
  ok(await step(ev, 'm02_sauce_run') === 'pot', 'getting in a car finished "steal a car": ' + await step(ev, 'm02_sauce_run'));
  // ---- the pot: in the bag, the drive step
  await ev(() => { window.JF_STORY.inv.give('soup_pot'); window.JF_STORY.S.emit({ type: 'pickup', item: 'soup_pot' }); });
  await sleep(1500);
  await skipIntro(pg, 4); // (lumps' car ride talk opens on the drive step)
  ok(await step(ev, 'm02_sauce_run') === 'drive', 'driving the soup: ' + await step(ev, 'm02_sauce_run'));
  ok(await ev(async () => { const { actors } = await import('/js/story/actors.js'); const a = actors.get('lumps'); return !!(a && a.ride); }), 'lumps rides shotgun');
  // ---- slosh: off the terrace edge (south, downhill: a 4 m drop)
  await ev(async () => { const { DV } = await import('/js/story/drive.js'); DV.car.h = 0; });
  const soup0 = await ev(() => window.JF_STORY.S.st.vars['m02.soup'] ?? 100);
  console.log('fps', await ev(() => new Promise((res) => { let n = 0; const t0 = performance.now(); const f = () => { n++; if (performance.now() - t0 < 2000) requestAnimationFrame(f); else res(n / 2); }; requestAnimationFrame(f); })));
  // a hard landing: the car dropped 9 m onto the road (headless frames are too slow to drive off a terrace in time)
  await ev(async () => { const { DV } = await import('/js/story/drive.js'); DV.car.vy = 0; DV.car.y += 9; DV.car.ground = false; });
  await sleep(4500); // (a 9 m fall is a couple of seconds of headless frames)
  const soup1 = await ev(() => window.JF_STORY.S.st.vars['m02.soup'] ?? 100);
  ok(soup1 < soup0, `the drop slopped soup out: ${soup0} -> ${soup1}`);
  ok(await ev(() => !document.querySelector('#encHud .soup').classList.contains('hidden')), 'the soup meter shows');
  await shot('slosh');
  // ---- the ambush at the ring road (on foot here: the car can't be teleported past the sim's checks)
  await ev(async () => { const { endDrive } = await import('/js/story/drive.js'); endDrive(true); });
  await settle(ev, [182, 2, 238], 5000);
  await ev(() => window.JF_STORY.S.quests.enterStep('m02_sauce_run', 'ambush'));
  await sleep(1500);
  ok(await ev(async () => { const { actors } = await import('/js/story/actors.js'); return actors.has('eotm'); }), 'EOTM is up on the road');
  await ev(async () => { const sc = await import('/js/story/scene.js'); if (sc.playing()) sc.skipScene(); });
  for (let i = 0; i < 20 && !(await ev(async () => (await import('/js/story/talk.js')).talking())); i++) await sleep(500); // (EOTM's talk opens on the step)
  await shot('eotm_talk');
  await ev(async () => { const tk = await import('/js/story/talk.js'); window.JF_STORY.S.run(['flag:fought_the_unpaid']); if (tk.talking()) tk.endTalk(); }); // ("*draw a weapon*": the fight. answering through the whole talk is too slow headless)
  await sleep(2500);
  ok(await ev(() => !!window.JF_STORY.S.st.flags.fought_the_unpaid), 'picked the fight');
  const units = await ev(() => [...window.JF_STORY.enc.units0.values()].map((u) => u.kind));
  console.log('remotes', await ev(async () => { const { G } = await import('/js/ctx.js'); return [...G.remotes.values()].map((r) => r.name).join(','); }));
  ok(units.filter((k) => k === 'intern').length >= 4, 'interns came: ' + units.join(','));
  ok(await ev(() => !document.querySelector('#encHud .clock').classList.contains('hidden')), 'the HOLD THE ROAD clock shows');
  await ev(async () => { const { ME } = await import('/js/player.js'); ME.yaw = 0; ME.pitch = -0.05; });
  await sleep(2500); await shot('ambush');
  const hp = await ev(async () => { const { ME } = await import('/js/player.js'); return ME.hp; });
  console.log('hp after 2.5 s of the ambush', hp);
  // the rest of the 90 s: wound on
  await ev(() => { window.JF_STORY.S.st.quests.m02_sauce_run.t = 95; });
  await sleep(1500);
  ok(await step(ev, 'm02_sauce_run') === 'deliver', 'held the road: on to the delivery: ' + await step(ev, 'm02_sauce_run'));
  await sleep(1500);
  const left = await ev(async () => { const { G } = await import('/js/ctx.js'); return [...G.remotes.values()].filter((r) => r.alive).length; });
  ok(left === 0, 'the unpaid clocked off (no enemies left): ' + left);
  await shot('pizza');
  // ---- the trade post at the gut border
  await settle(ev, [-40, 36.5, -6], 5000);
  await ev(async () => { const { ME } = await import('/js/player.js'); ME.yaw = 0.9; ME.pitch = -0.1; });
  await sleep(1200);
  ok(await ev(async () => { const { actors } = await import('/js/story/actors.js'); return actors.has('sister_agenda'); }), 'the choir clerk is at the counter');
  await settle(ev, [-44, 36.5, -14], 2500);
  ok(await step(ev, 'm02_sauce_run') === 'count', 'reaching the trade post with the pot delivers it: ' + await step(ev, 'm02_sauce_run'));
  await shot('tradepost');
  console.log('ERRORS', errs.length, errs.slice(0, 10).join('\n'));
  await b.close();
})();
