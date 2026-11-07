// playwright e2e: New Game drops you in the Bottom (the streamed city slice) at the Machine; locker + clinic stand-ins work
// run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_slice.cjs
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const skipIntro = require('./skipintro.cjs'); // the intro cinematic holds the keys: skip it
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const PORT = process.env.PORT || 3311, OUT = process.env.SP + '/shots';
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message + ' ' + (e.stack || '').split('\n')[1]));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.addInitScript(() => { localStorage.setItem('jankfire', JSON.stringify({ name: 'slice', loadout: { primary: 'ar', secondary: 'pistol', melee: 'knife', item: 'frag' } })); if (!sessionStorage.getItem('sl')) { sessionStorage.setItem('sl', 1); localStorage.removeItem('jfStorySaves'); } });
  await pg.goto(`http://localhost:${PORT}/?story=1`); await sleep(1500);
  await pg.click('#storyBtn', { force: true }); await sleep(700); await pg.click('#storyPick .st-btn.yellow', { force: true }); await sleep(9000); await skipIntro(pg);
  const ev = (f, a) => pg.evaluate(f, a);
  const st = () => ev(async () => { const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js'); return { map: G.cfg && G.cfg.map, pos: ME.pos.map((x) => +x.toFixed(1)), ground: ME.onGround, hint: document.querySelector('.st-hint') && !document.querySelector('.st-hint').classList.contains('hidden') ? document.querySelector('.st-hint').textContent : '' }; });
  console.log('spawned', JSON.stringify(await st()));
  await pg.screenshot({ path: `${OUT}/sl_spawn.png`, timeout: 120000 });
  const W = await ev(async () => { const { worldOf } = await import('/shared/story/worlds.js'); return worldOf('story_slice'); });
  const tp = (p, yaw) => ev(async ([p, yaw]) => { const { ME } = await import('/js/player.js'); ME.pos = p.slice(); ME.vel = [0, 0, 0]; if (yaw != null) ME.yaw = yaw; }, [p, yaw]);
  for (const [name, at] of [['terminal', W.terminal.p], ['locker', W.locker.p], ['clinic', W.clinic.p]]) {
    await tp([at[0], at[1] + 0.3, at[2] + (name === "terminal" ? 2.4 : 1.6)], 0); await sleep(1500); // (the Machine is 2+ m deep now: stand in front of it)
    const s = await st(); console.log(name, JSON.stringify(s));
    await pg.screenshot({ path: `${OUT}/sl_${name}.png`, timeout: 120000 });
  }
  await pg.keyboard.down('KeyF'); await sleep(80); await pg.keyboard.up('KeyF'); await sleep(800);
  console.log('clinic opens', await ev(() => !!document.getElementById('storyClinic') && !document.getElementById('storyClinic').classList.contains('hidden')));
  await pg.screenshot({ path: `${OUT}/sl_clinicui.png`, timeout: 120000 });
  console.log('ERRORS', errs.length, errs.slice(0, 8).join('\n'));
  await b.close();
})();
