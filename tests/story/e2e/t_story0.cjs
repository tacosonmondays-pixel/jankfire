// playwright e2e (WP0/WP3). run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_story0.cjs (needs a running server; t_flagoff also wants main on 3313)
// WP0 e2e: flag on -> STORY -> NEW GAME -> walk -> Machine terminal -> Training sim -> quit -> back at the same spot
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const skipIntro = require('./skipintro.cjs'); // the intro cinematic holds the keys: skip it
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const PORT = process.env.PORT || 3311, OUT = process.env.SP + '/shots';
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ name: 'storytest', jank: 3, loadout: { primary: 'ar', secondary: 'snowball', melee: 'knife', item: 'frag' } })));
  await pg.goto(`http://localhost:${PORT}/?story=1&storytest=1`); await sleep(1500);
  await pg.screenshot({ path: `${OUT}/s0_home.png` });
  await pg.click('#storyBtn', { force: true }); await sleep(800);
  await pg.screenshot({ path: `${OUT}/s0_picker.png` });
  await pg.click('#storyPick .st-btn.yellow', { force: true }); await sleep(3000); await skipIntro(pg);
  const st = () => pg.evaluate(async () => { const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js'); return { joined: G.joined, mode: G.mode, map: G.cfg && G.cfg.map, pos: ME.pos.map((x) => +x.toFixed(2)), menu: !document.getElementById('menu').classList.contains('hidden'), hint: !document.querySelector('.st-hint').classList.contains('hidden') }; });
  console.log('in story', JSON.stringify(await st()));
  await pg.screenshot({ path: `${OUT}/s0_lot.png` });
  // melee on left click
  await pg.evaluate(async () => { const { W } = await import('/js/weapons.js').catch(() => ({})); });
  await pg.keyboard.press('Digit3'); await sleep(400);
  await pg.evaluate(async () => { const { net } = await import('/js/net.js'); window.__sent = []; const s0 = net.ws.send.bind(net.ws); net.ws.send = (d) => { try { const m = JSON.parse(d); if (m.t !== 's' && m.t !== 'pi') window.__sent.push(m.t + ':' + (m.w || '')); } catch {} return s0(d); }; });
  await pg.mouse.move(640, 360); await pg.mouse.down(); await sleep(60); await pg.mouse.up(); await sleep(120); await pg.screenshot({ path: `${OUT}/s0_melee.png` }); await sleep(400);
  console.log('melee sent', JSON.stringify(await pg.evaluate(() => window.__sent)));
  // walk toward the Machine (forward = -z)
  await pg.keyboard.down('KeyW'); await sleep(2600); await pg.keyboard.up('KeyW'); await sleep(400);
  let s = await st(); console.log('near machine', JSON.stringify(s));
  if (!s.hint) { await pg.evaluate(async () => { const { ME } = await import('/js/player.js'); ME.pos = [0, 0.1, -12]; ME.vel = [0, 0, 0]; }); await sleep(500); s = await st(); console.log('placed', JSON.stringify(s)); }
  await pg.screenshot({ path: `${OUT}/s0_machine.png` });
  const before = s.pos;
  await pg.keyboard.down('KeyF'); await sleep(300); await pg.keyboard.up('KeyF'); await sleep(1500);
  s = await st(); console.log('after terminal', JSON.stringify(s), await pg.textContent('#storyBtn b'));
  await pg.screenshot({ path: `${OUT}/s0_menu.png` });
  await pg.click('#scr-main [data-mode="training"]', { force: true }); await sleep(3500);
  s = await st(); console.log('in sim', JSON.stringify(s));
  await pg.evaluate(async () => { const { G } = await import('/js/ctx.js'); }); 
  await pg.keyboard.press('KeyB'); await sleep(600);
  await pg.click('#quit', { force: true }); await sleep(3000);
  s = await st(); console.log('back', JSON.stringify(s), 'dist', Math.hypot(s.pos[0] - before[0], s.pos[2] - before[2]).toFixed(2));
  await pg.screenshot({ path: `${OUT}/s0_back.png` });
  const ls = await pg.evaluate(() => localStorage.getItem('jfStorySaves')); console.log('local save', ls && ls.slice(0, 160));
  // quit story to menu -> normal home, button says STORY
  await pg.keyboard.press('KeyB'); await sleep(600); await pg.click('#quit', { force: true }); await sleep(1200);
  s = await st(); console.log('quit story', JSON.stringify(s), await pg.textContent('#storyBtn b'));
  console.log('ERRORS', errs.length, errs.slice(0, 8).join('\n'));
  await b.close();
})();
