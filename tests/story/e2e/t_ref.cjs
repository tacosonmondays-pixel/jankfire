// playwright e2e (the combat referee). run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_ref.cjs
// story on the test lot: the referee's room comes up in the worker, the story asks for enemies, they show up as people,
// you shoot one with the real gun (mouse + aim), the hits and the kill come back as combat events; an enemy shoots you
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const skipIntro = require('./skipintro.cjs');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const PORT = process.env.PORT || 3311, OUT = process.env.SP + '/shots';
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const ctx = await b.newContext({ viewport: { width: 960, height: 540 }, ...(process.env.VID ? { recordVideo: { dir: process.env.SP + '/vid', size: { width: 960, height: 540 } } } : {}) });
  const pg = await ctx.newPage();
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message + ' ' + (e.stack || '').split('\n')[1]));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.addInitScript(() => { localStorage.setItem('jankfire', JSON.stringify({ name: 'ref', jank: 3, loadout: { primary: 'ar', secondary: 'pistol', melee: 'knife', item: 'frag' } })); localStorage.removeItem('jfStorySaves'); window.__ev = []; });
  await pg.goto(`http://localhost:${PORT}/?story=1&storydev=1&storytest=1`); await sleep(1500);
  await pg.click('#storyBtn', { force: true }); await sleep(700); await pg.click('#storyPick .st-btn.yellow', { force: true }); await sleep(3500); await skipIntro(pg);
  const ev = (f, a) => pg.evaluate(f, a);
  // catch the combat events (the story engine's own hook gets them in the game; here the test listens)
  await ev(async () => { const { G } = await import('/js/ctx.js'); const was = G.story.combat; G.story.combat = (e) => { window.__ev.push(e); if (was) was(e); }; });
  await sleep(2500); // (the room loads in the worker)
  // the story asks for two temps in front of you (the lot's spawn faces -z)
  await ev(async () => { const { ME } = await import('/js/player.js'); ME.pos = [0, 0.1, 0]; ME.vel = [0, 0, 0]; ME.yaw = 0; ME.pitch = 0; });
  await sleep(500);
  await ev(async () => { const { G } = await import('/js/ctx.js'); G.story.send('spawn', { kind: 'corp_temp', at: [0, 0.1, -9], id: 'temp_a', hp: 60 }); G.story.send('hold', { id: 'temp_a', on: true }); });
  await sleep(1500);
  const seen = await ev(async () => { const { G } = await import('/js/ctx.js'); return [...G.remotes.values()].map((r) => ({ id: r.id, name: (G.names.get(r.id) || {}).name, p: (r.pos || r.group?.position?.toArray?.() || []).map?.((v) => +(+v).toFixed(1)) })); });
  console.log('enemies on the client', JSON.stringify(seen));
  await pg.screenshot({ path: `${OUT}/ref_enemies.png` });
  // aim at the temp and hold fire with the real mouse (pointer lock is faked by the game's test path: just press)
  const shoot = async (ms) => {
    const t0 = Date.now();
    await ev(async () => (await import('/js/weapons.js')).fireDown()); // (the trigger: headless has no pointer lock for the mouse)
    while (Date.now() - t0 < ms && !(await ev(() => window.__ev.some((e) => e.type === 'kill' && e.target === 'temp_a')))) {
      await ev(async () => { const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js'); const r = [...G.remotes.values()].find((x) => ((G.names.get(x.id) || {}).name || '').includes('Temp')); if (!r || !r.ch) return; const p = r.ch.root.position.toArray(); const dx = p[0] - ME.pos[0], dz = p[2] - ME.pos[2], dy = (p[1] + 1.2) - (ME.pos[1] + 1.6); ME.yaw = Math.atan2(-dx, -dz); ME.pitch = Math.atan2(dy, Math.hypot(dx, dz)); });
      await sleep(60);
    }
    await ev(async () => (await import('/js/weapons.js')).fireUp());
  };
  await shoot(8000);
  await pg.screenshot({ path: `${OUT}/ref_shoot.png` });
  await sleep(800);
  const evs = await ev(() => window.__ev);
  const hits = evs.filter((e) => e.type === 'hit' && e.target === 'temp_a'), kill = evs.find((e) => e.type === 'kill' && e.target === 'temp_a');
  console.log('hits on temp_a', hits.length, JSON.stringify(hits.slice(0, 2)), '\nkill', JSON.stringify(kill));
  // now a raider: stand there and let it shoot back
  await ev(async () => { const { G } = await import('/js/ctx.js'); G.story.send('spawn', { kind: 'raider', at: [6, 0.1, -12], id: 'raider_b' }); });
  await sleep(6000);
  const evs2 = await ev(() => window.__ev);
  console.log('you got hit', evs2.filter((e) => e.type === 'hit' && e.target === 'me').length, 'times; downs', evs2.filter((e) => e.type === 'down').length, '| hp', await ev(async () => (await import('/js/player.js')).ME.hp));
  await pg.screenshot({ path: `${OUT}/ref_raider.png` });
  console.log('ERRORS', errs.length, errs.slice(0, 8).join('\n'));
  await ctx.close(); await b.close();
})();
