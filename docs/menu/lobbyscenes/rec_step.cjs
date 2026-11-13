// a smooth clip from slow software GL: the lobby scene is held and stepped 1/30 s per screenshot (G.lsHold), then
// ffmpeg makes a 30 fps video. STEPS: a script of [action, frames]
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const fs = require('fs');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const OUT = process.env.OUT, [W, H] = (process.env.SIZE || '1280x720').split('x').map(Number);
(async () => {
  fs.mkdirSync(OUT + '/f', { recursive: true });
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await (await b.newContext({ viewport: { width: W, height: H } })).newPage();
  pg.on('pageerror', (e) => console.log('PAGEERR', e.message));
  await pg.addInitScript(() => { localStorage.setItem('jf_giftseen_all', '1'); localStorage.setItem('jankfire', JSON.stringify({ name: 'taco', killcam: false, jank: 3 })); });
  await pg.goto(`http://localhost:${process.env.PORT}/`); await sleep(2500);
  await pg.evaluate(() => { const e = document.getElementById('jank'); e.value = '3'; e.dispatchEvent(new Event('change')); });
  await pg.evaluate(() => document.querySelector('[data-hub="offline"]').click());
  if (process.env.SCRIPT !== 'zm') await pg.evaluate(async () => { const k = await import('/js/glbkit.js'); k.prefetch(['x_mech_paperplane', 'x_mech_nightshift', 'x_lobby_gantry'], 9); for (let i = 0; i < 60 && !(k.AUTHORED.x_mech_paperplane && k.AUTHORED.x_mech_nightshift && k.AUTHORED.x_lobby_gantry); i++) await new Promise((r) => setTimeout(r, 500)); await import('/js/lobbyscenes/garage.js'); });
  await pg.evaluate(() => { window.JANK.G.lsHold = true; });
  let n = 0;
  const shot = async () => { await pg.evaluate(() => new Promise((r) => { window.JANK.G.lsAdvance = 1 / 30; requestAnimationFrame(() => r()); })); await pg.screenshot({ path: `${OUT}/f/${String(n++).padStart(4, '0')}.jpg`, quality: 88 }); };
  const run = async (k) => { for (let i = 0; i < k; i++) await shot(); };
  const click = (sel) => pg.evaluate((s) => document.querySelector(s).click(), sel);
  await run(10);
  await click(process.env.SCRIPT === 'zm' ? '[data-mode2="zm"]' : '[data-mode2="isle"]');
  for (let i = 0; i < 60; i++) { if (await pg.evaluate(async () => !!(await import('/js/lobbyscenes/index.js')).lobbySceneWalk())) break; await sleep(250); }
  await sleep(1500);
  const info = () => pg.evaluate(async () => JSON.stringify((await import('/js/lobbyscenes/index.js')).lobbySceneInfo().extra));
  const kd = (k) => pg.keyboard.down(k), ku = (k) => pg.keyboard.up(k), tap = async (k) => { await kd(k); await run(1); await ku(k); };
  if (process.env.SCRIPT === 'zm') {
    await run(15);
    await kd('ShiftLeft'); await kd('KeyW'); await run(20); await kd('KeyA'); await run(30); await ku('KeyA'); await ku('KeyW'); await ku('ShiftLeft'); await run(6);
    const nearOf = () => pg.evaluate(async () => { const w = (await import('/js/lobbyscenes/index.js')).lobbySceneWalk(); return w && w.W.near ? w.W.near.label() : null; });
    console.log('near', await nearOf());
    if (!/DEB/.test(await nearOf() || '')) { await pg.evaluate(async () => { const w = (await import('/js/lobbyscenes/index.js')).lobbySceneWalk(); w.me.pos = [-6.6, 0, -4.4]; }); await run(3); } // (a nudge, if the run fell short)
    await tap('KeyE'); await run(25);
    await pg.evaluate(() => { const bs = document.querySelectorAll('#lsTags .ls-pick button'); if (bs[2]) bs[2].click(); }); await run(30);
    await tap('KeyE'); await run(15);
    await kd('ShiftLeft'); await kd('KeyS'); await run(30); await ku('KeyS'); await ku('ShiftLeft'); await run(4);
    console.log('near', await nearOf());
    if (!/ZOMBIE/.test(await nearOf() || '')) { await pg.evaluate(async () => { const w = (await import('/js/lobbyscenes/index.js')).lobbySceneWalk(); w.me.pos = [-4.2, 0, 6.4]; w.me.yaw = 0.6; }); await run(3); }
    await tap('KeyE'); await run(40);
    await tap('KeyZ'); await run(20);
  } else if (process.env.SCRIPT === 'walk') {
    await run(20);
    await kd('KeyW'); await kd('KeyD'); await run(27); await ku('KeyW'); await ku('KeyD'); await run(4);
    await tap('KeyE'); await run(60); console.log('after swap', await info());
    await kd('KeyA'); await run(18); await ku('KeyA'); await run(4);
    await tap('KeyE'); await run(10); console.log('riding', await info());
    await kd('KeyS'); await run(36); await kd('KeyD'); await run(18); await ku('KeyD'); await run(14); await ku('KeyS'); await run(6);
    await tap('KeyE'); await run(50); console.log('home', await info());
    await tap('KeyZ'); await run(30);
  } else {
    await run(45);
    await click('#lsTags .ls-swap button[data-d="1"]'); await run(70);
    await run(15);
    await click('#lsTags .ls-swap button[data-d="-1"]'); await run(70);
    await run(15);
    await click('[data-mode2="zm"]'); await run(12);
  }
  console.log('frames', n);
  await b.close();
})();
