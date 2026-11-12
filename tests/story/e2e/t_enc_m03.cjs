// playwright e2e: m03 SOMETHING'S DIGESTING's encounters in the city slice. Lumps leads you down Peristalsis Avenue
// (walks while you keep up, waits when you don't), then the stomach-dog chase out of the Gut: a pack behind you, more
// herding in, Lumps carries you over the last stretch to the border gate and the dogs stop there.
// run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_enc_m03.cjs
const { boot, jump, settle, step, sleep } = require('./enc_util.cjs');
const skipIntro = require('./skipintro.cjs');
const OUT = process.env.SP + '/shots';
const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) process.exitCode = 1; };
(async () => {
  const { b, pg, ev, errs } = await boot({ hd: process.env.HD === '1', size: [960, 540] });
  const shot = (n) => pg.screenshot({ path: `${OUT}/m03_${n}.png`, timeout: 120000 });
  const lumps = () => ev(async () => { const { actors } = await import('/js/story/actors.js'); const a = actors.get('lumps'); return a ? a.pos.map((v) => +v.toFixed(1)) : null; });
  // ---- the escort
  await settle(ev, [-116, 40.5, -133], 3000);
  ok(await jump(ev, 'm03_somethings_digesting', 'walk'), 'm03 at "follow lumps"');
  await sleep(1500); await skipIntro(pg, 8);
  // you lag behind: he waits for you (you're held 20 m back down the avenue)
  await ev(async () => { const { ME } = await import('/js/player.js'); window.__h = setInterval(() => { ME.pos = [-134, 40.5, -133]; ME.vel = [0, 0, 0]; }, 30); });
  await sleep(3000);
  const w0 = await lumps(); await sleep(5000); const w1 = await lumps();
  ok(w0 && w1 && Math.abs(w1[0] - w0[0]) < 1 && w0[0] < -96, `he waits for you: ${w0} -> ${w1}`);
  await ev(() => clearInterval(window.__h));
  // you keep up: he walks (you're held a couple of metres behind him)
  await ev(async () => { const { ME } = await import('/js/player.js'); const { actors } = await import('/js/story/actors.js'); window.__h = setInterval(() => { const a = actors.get('lumps'); if (a) { ME.pos = [a.pos[0] - 2.5, a.pos[1] + 0.3, a.pos[2] + 1]; ME.vel = [0, 0, 0]; ME.yaw = -Math.PI / 2; } }, 30); });
  const l0 = await lumps(); await sleep(6000); const l1 = await lumps();
  ok(l0 && l1 && l1[0] > l0[0] + 2, `he leads the way east: ${l0} -> ${l1}`);
  await shot('escort');
  // you stay with him: the walk is done when HE gets to his mum (not when the street carries you there first)
  for (let i = 0; i < 40 && (await step(ev, 'm03_somethings_digesting')) === 'walk'; i++) await sleep(1000);
  await ev(() => clearInterval(window.__h));
  const lw = await lumps();
  ok(await step(ev, 'm03_somethings_digesting') !== 'walk' && lw[0] > -93, `he got to the wall, the walk is done: ${await step(ev, 'm03_somethings_digesting')} ${lw}`);
  await ev(async () => { const tk = await import('/js/story/talk.js'); if (tk.talking()) tk.endTalk(); });
  // ---- the chase out
  await settle(ev, [-262, 40.5, -178], 3000);
  await ev(() => window.JF_STORY.S.quests.enterStep('m03_somethings_digesting', 'out'));
  await sleep(1500); await skipIntro(pg, 4);
  await ev(async () => { const { ME } = await import('/js/player.js'); window.__h = setInterval(() => { ME.pos = [-262, 40.5, -178]; ME.vel = [0, 0, 0]; ME.yaw = Math.PI; ME.pitch = -0.1; ME.hp = 100; }, 30); });
  await sleep(6000);
  const dogs = await ev(() => [...window.JF_STORY.enc.units0.values()].filter((u) => u.kind === 'stomach_dog').length);
  ok(dogs >= 3, 'a pack of stomach-dogs: ' + dogs);
  ok(await ev(async () => { const { actors } = await import('/js/story/actors.js'); return actors.has('lumps'); }), 'lumps runs with you');
  await shot('dogs');
  await ev(() => clearInterval(window.__h));
  // the last stretch: lumps carries you to the gate
  await settle(ev, [-44, 40.5, -52], 1200);
  for (let i = 0; i < 16; i++) { if (await step(ev, 'm03_somethings_digesting') === 'DONE') break; await sleep(800); }
  await shot('carried');
  const me = await ev(async () => { const { ME } = await import('/js/player.js'); return ME.pos.map((v) => +v.toFixed(1)); });
  ok(me[2] > -24, 'carried over to the border: ' + me);
  ok(await step(ev, 'm03_somethings_digesting') === 'DONE', "out of the Gut: SOMETHING'S DIGESTING done: " + await step(ev, 'm03_somethings_digesting'));
  await sleep(2000);
  const left = await ev(async () => { const { G } = await import('/js/ctx.js'); return [...G.remotes.values()].filter((r) => r.alive).length; });
  ok(left === 0, 'the dogs stopped at the gate (none left): ' + left);
  console.log('ERRORS', errs.length, errs.slice(0, 10).join('\n'));
  await b.close();
})();
