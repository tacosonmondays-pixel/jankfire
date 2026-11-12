// Backrooms pictures: stand at spots on a map and take a screenshot from each, in the game's own lights and fog.
// Joins a bots match, then stops listening to the server (no deaths, rounds or pop quizzes can move the camera) and
// pins the camera to each spot. usage:
//   node tools/blender/arch/brshots.cjs <port> <outdir> <spots.json> [presets=3,0] [query=''] [tag='']
//   spots: [{ name, cam: [x, y, z], at: [x, y, z] }]   query: '?arch=0' shows the boxes (the before)
// out: <outdir>/<tag><name>_<preset>.png (1280x720)
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const [port = '3100', outdir = 'shots', spotsF, presetsArg = '3,0', query = '', tag = ''] = process.argv.slice(2);
const spots = JSON.parse(fs.readFileSync(spotsF, 'utf8')), presets = presetsArg.split(',').map(Number);
const map = process.env.JF_SHOT_MAP || 'backrooms';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
fs.mkdirSync(outdir, { recursive: true });
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  pg.on('pageerror', (e) => console.log('PAGEERR', e.message));
  await pg.addInitScript(() => localStorage.setItem('jf_giftseen_all', '1') || localStorage.setItem('jankfire', JSON.stringify({ name: 'SHOTS', killcam: false, jank: 3 })));
  await pg.goto(`http://localhost:${port}/${query}`); await sleep(2500);
  const T = { timeout: 180000 };
  await pg.click('#scr-main [data-pick="bots"]', T); await pg.click('#mpCustom', T);
  await pg.selectOption('#setupGame', 'dm', T); await pg.selectOption('#setupMap', map, T);
  const bots = pg.locator('#setupBots'); if (await bots.isVisible() && await bots.isEnabled()) await bots.fill('1');
  await pg.selectOption('#setupDiff', 'easy', { timeout: 3000 }).catch(() => {});
  await pg.click('#setupGo', T);
  const ok = await pg.evaluate(async (map) => {
    const { G } = await import('/js/ctx.js'); const { MAP } = await import('/shared/map.js');
    for (let i = 0; i < 900 && !(G.joined && MAP.id === map); i++) await new Promise((r) => setTimeout(r, 100));
    return G.joined && MAP.id === map;
  }, map);
  if (!ok) { console.log('never joined'); process.exit(1); }
  await sleep(6000); // (the arch model and prop files land, the map redraws)
  await pg.evaluate(async () => {
    const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js'); const { net } = await import('/js/net.js');
    net.ws.onmessage = null; net.send = () => {}; // deaf and mute: the match goes on without us
    const css = document.createElement('style'); css.textContent = 'body > :not(#game) { display: none !important; }'; document.head.append(css);
    G.vmCamera.layers.disableAll();
    const r = G.renderer, draw = r.render.bind(r); r.info.autoReset = false; window.__perf = { calls: 0, tris: 0, n: 0 };
    r.render = (scene, cam) => { r.info.reset(); draw(scene, cam); if (scene === G.scene) { window.__perf.calls += r.info.render.calls; window.__perf.tris += r.info.render.triangles; window.__perf.n++; } }; // (the world pass, shadows included)
    window.__pin = null;
    setInterval(() => { const q = window.__pin; if (q) { ME.alive = true; ME.pos = q.p.slice(); ME.vel = [0, 0, 0]; ME.yaw = q.yaw; ME.pitch = q.pitch; ME.hp = 100; } }, 4);
    setInterval(() => { for (const o of G.scene.children) if (o.isPoints) o.visible = false; G.remotes.forEach((r) => { if (r.ch && r.ch.root) r.ch.root.visible = false; }); }, 16);
  });
  const perf = [];
  for (const pr of presets) {
    await pg.evaluate(async (pr) => { const { G } = await import('/js/ctx.js'); const w = await import('/js/world.js'); G.settings.jank = pr; w.setJank(pr); }, pr);
    await sleep(1500);
    for (const s of spots) {
      const [cx, cy, cz] = s.cam, [ax, ay, az] = s.at, dx = ax - cx, dy = ay - cy, dz = az - cz;
      await pg.evaluate((q) => { window.__pin = q; }, { p: [cx, cy - 1.6, cz], yaw: Math.atan2(-dx, -dz), pitch: Math.atan2(dy, Math.hypot(dx, dz)) });
      await sleep(1200);
      await pg.evaluate(() => { window.__perf = { calls: 0, tris: 0, n: 0 }; });
      await sleep(400);
      const pf = await pg.evaluate(() => window.__perf); perf.push({ spot: s.name, preset: pr, calls: Math.round(pf.calls / Math.max(1, pf.n)), tris: Math.round(pf.tris / Math.max(1, pf.n)) });
      await pg.screenshot({ path: path.join(outdir, `${tag}${s.name}_${pr}.png`) });
      console.log('shot', s.name, pr);
    }
  }
  fs.writeFileSync(path.join(outdir, `${tag}perf.json`), JSON.stringify(perf, null, 0));
  const avg = (k) => Math.round(perf.reduce((a, q) => a + q[k], 0) / perf.length);
  console.log('world pass per frame (avg over spots): draw calls', avg('calls'), 'triangles', avg('tris'));
  await b.close();
})();
