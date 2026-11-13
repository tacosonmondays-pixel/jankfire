// the zombies warehouse: walk in, talk to Deb (pick a passive), Gus (a pistol), Marge (an item), poke the zombie
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const OUT = process.env.OUT, [W, H] = (process.env.SIZE || '1280x720').split('x').map(Number), J = Number(process.env.JANK ?? 3);
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await (await b.newContext({ viewport: { width: W, height: H } })).newPage();
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.addInitScript((j) => { localStorage.setItem('jf_giftseen_all', '1'); localStorage.setItem('jankfire', JSON.stringify({ name: 'taco', killcam: false, jank: j })); }, J);
  await pg.goto(`http://localhost:${process.env.PORT}/`); await sleep(2500);
  await pg.evaluate((j) => { const e = document.getElementById('jank'); e.value = String(j); e.dispatchEvent(new Event('change')); }, J);
  await pg.evaluate(() => document.querySelector('[data-hub="' + (process.env.SIDE || 'offline') + '"]').click()).catch(() => pg.evaluate(() => document.querySelector('[data-hub="offline"]').click()));
  await sleep(500);
  await pg.evaluate(() => document.querySelector('[data-mode2="zm"]').click());
  const info = () => pg.evaluate(async () => (await import('/js/lobbyscenes/index.js')).lobbySceneInfo());
  for (let i = 0; i < 60 && !(await info()); i++) await sleep(250);
  await sleep(4000);
  console.log('info', JSON.stringify(await info()));
  await pg.screenshot({ path: `${OUT}/zm0.jpg`, quality: 85 });
  const tp = (p, yaw) => pg.evaluate(async ([p, yaw]) => { const w = (await import('/js/lobbyscenes/index.js')).lobbySceneWalk(); w.me.pos = p; w.me.yaw = yaw; w.W.camYaw = yaw; }, [p, yaw]);
  for (const [who, p, yaw, opt] of [['deb', [-6.6, 0, -4.4], 0.75, 2], ['gus', [0, 0, -7.4], 0, 1], ['marge', [7.2, 0, -5.0], -0.75, 3]]) {
    await tp(p, yaw); await sleep(1500);
    const before = await info();
    await pg.keyboard.press('KeyE'); await sleep(1200);
    await pg.screenshot({ path: `${OUT}/zm_${who}.jpg`, quality: 85 });
    const opened = await pg.evaluate(() => { const p = document.querySelector('#lsTags .ls-pick'); return p && p.style.display !== 'none' ? p.querySelectorAll('button').length : 0; });
    await pg.evaluate((i) => { const bs = document.querySelectorAll('#lsTags .ls-pick button'); if (bs[i]) bs[i].click(); }, opt);
    await sleep(900);
    const after = await info();
    console.log(who, 'near:', before.near, '· picker buttons:', opened, '· zload', JSON.stringify(before.extra.zload), '->', JSON.stringify(after.extra.zload));
    await pg.screenshot({ path: `${OUT}/zm_${who}_picked.jpg`, quality: 85 });
  }
  await tp([-4, 0, 7], Math.PI * 0.2); await sleep(1500);
  await pg.keyboard.press('KeyE'); await sleep(900);
  await pg.screenshot({ path: `${OUT}/zm_zombie.jpg`, quality: 85 });
  console.log('saved zload', JSON.stringify(await pg.evaluate(() => JSON.parse(localStorage.getItem('jankfire') || '{}').zload)));
  console.log('errors:', JSON.stringify(errs));
  await b.close();
})();
