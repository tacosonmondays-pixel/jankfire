// The streamed city in the real game: node tools/city/ingame.cjs <port> <outDir> [jank=3]
// /?story=1 -> STORY -> new game (the sim's test lot) -> swap the map for story_slice (what the sim will send once it
// uses the slice) -> wait for the ground to stream in -> walk with the real controller -> screenshots + numbers.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [port = 3107, out = '.', jank = '3'] = process.argv.slice(2);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio', '--ignore-gpu-blocklist'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.addInitScript((j) => { localStorage.setItem('jfStory', '1'); const s = JSON.parse(localStorage.getItem('jankfire') || '{}'); s.jank = +j; s.name = 'cityrun'; localStorage.setItem('jankfire', JSON.stringify(s)); }, jank);
  await pg.goto(`http://localhost:${port}/`);
  await pg.waitForSelector('#storyBtn', { timeout: 60000 });
  await pg.click('#storyBtn');
  await pg.waitForSelector('#storyPick .st-btn.yellow', { timeout: 30000 });
  await pg.click('#storyPick .st-btn.yellow');
  await pg.waitForFunction(async () => { const { G } = await import('/js/ctx.js'); return G.joined && G.mode === 'story'; }, null, { timeout: 60000 });
  await sleep(1500);
  const t0 = Date.now();
  await pg.evaluate(async () => {
    const { MAPS } = await import('/shared/map.js'); const w = await import('/js/world.js'); const { ME } = await import('/js/player.js'); const sm = await import('/js/city/storymap.js');
    sm.registerStoryMaps(MAPS); w.loadMap('story_slice');
    ME.pos = sm.STORY_SLICE.spawn.slice(); ME.vel = [0, 0, 0]; ME.yaw = sm.STORY_SLICE.yaw; ME.pitch = 0.05;
    document.getElementById('menu').classList.add('hidden');
  });
  await pg.waitForFunction(async () => { const m = await import('/js/city/ingame.js'); const s = m.cityStream(); return s && s.stats().near > 3 && s.ready(-189, 196); }, null, { timeout: 90000 });
  const loadMs = Date.now() - t0;
  await sleep(2500);
  const shot = async (name) => { await pg.screenshot({ path: path.join(out, `ingame_${name}.png`) }); };
  await shot('spawn');
  const p0 = await pg.evaluate(async () => (await import('/js/player.js')).ME.pos.slice());
  await pg.keyboard.down('KeyW'); await sleep(3500); await pg.keyboard.up('KeyW');
  const p1 = await pg.evaluate(async () => (await import('/js/player.js')).ME.pos.slice());
  await shot('walked');
  const st = await pg.evaluate(async () => { const m = await import('/js/city/ingame.js'); const { G } = await import('/js/ctx.js'); const { BOXES } = await import('/shared/map.js'); return { ...m.cityStream().stats(), calls: G.renderer.info.render.calls, tris: G.renderer.info.render.triangles, BOXES: BOXES.length }; });
  console.log(JSON.stringify({ loadMs, p0: p0.map((v) => +v.toFixed(2)), p1: p1.map((v) => +v.toFixed(2)), walked: +Math.hypot(p1[0] - p0[0], p1[2] - p0[2]).toFixed(1), ...st, errors: errs.slice(0, 8) }));
  await b.close();
})();
