// The Tall Guy From HR in the Scary Forest at night, from fixed cameras: near (3 m), about 8 m and far between the trees
// (your flashlight on him), at Too HD and Potato. Run it before and after a model change for a before/after sheet.
// usage: node tools/blender/shots_hrguy.cjs <port> <outdir> <tag> [presets=3,0] [spot.json]
//   (start the server first with HR kept off so only this script places him: JF_HR_FIRST=999999 JF_HR_EVERY=999999
//   JF_ROUND_TIME=7200 JF_ROUND_KILLS=999 PORT=<port> node server.js. Cap browsers with pwlock.cjs.)
// out: <outdir>/<tag>_<view>_<preset>.png (view = near, mid, far, pose<n>) and <tag>_errors.txt (page errors seen)
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const [port = '3203', outdir = 'tools/blender/compare', tag = 'hr', presetsArg = '3,0', spotArg = ''] = process.argv.slice(2);
const presets = presetsArg.split(',').map(Number);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
// a spot in the woods with clear lines to him from 3.2, 8 and 26 m (found with the map's own boxes), trees either side
const SPOT = spotArg ? JSON.parse(fs.readFileSync(spotArg, 'utf8')) : { hr: [-82.87, 0, -64.5], cams: [[-80.61, 0, -62.24], [-77.22, 0, -58.84], [-64.49, 0, -46.11]], pose: 7 };
const VIEWS = [['near', 0, 74, 1.75], ['mid', 1, 52, 1.9], ['far', 2, 30, 2.0]]; // name, camera, fov, height looked at
fs.mkdirSync(outdir, { recursive: true });

async function session() {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio', '--ignore-gpu-blocklist'] });
  const pg = await b.newPage({ viewport: { width: 960, height: 540 } }); // (Too HD under swiftshader is ~3 GB at 1280 x 720: smaller survives a busy machine)
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + (e.stack || e.message).split('\n').slice(0, 3).join(' | ')));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text().slice(0, 200)); });
  await pg.addInitScript(() => localStorage.setItem('jf_giftseen_all', '1') || localStorage.setItem('jankfire', JSON.stringify({ name: 'SHOTS', killcam: false, jank: 3 })));
  await pg.goto(`http://localhost:${port}/`); await sleep(2500);
  const T = { timeout: 180000 };
  await pg.click('#scr-main [data-pick="bots"]', T); await pg.click('#mpCustom', T);
  await pg.selectOption('#setupGame', 'dm', T); await pg.selectOption('#setupMap', 'forest', T);
  const bots = pg.locator('#setupBots'); if (await bots.isVisible() && await bots.isEnabled()) await bots.fill('1');
  await pg.selectOption('#setupDiff', 'easy', { timeout: 3000 }).catch(() => {});
  await pg.click('#setupGo', T);
  const ok = await pg.evaluate(async () => {
    const { G } = await import('/js/ctx.js'); const { MAP, MAPS } = await import('/shared/map.js');
    for (let i = 0; i < 900 && !(G.joined && MAP.id === 'forest'); i++) await new Promise((r) => setTimeout(r, 100));
    if (!(G.joined && MAP.id === 'forest')) return 'joined ' + G.joined + ', map ' + MAP.id;
    const k = await import('/js/glbkit.js'), pf = await import('/js/propfield.js');
    const need = pf.modelsFor(MAPS.forest);
    for (let i = 0; i < 400 && (need.some((m) => k.LAZY.has(m)) || k.lateBusy()); i++) await new Promise((r) => setTimeout(r, 100));
    await new Promise((r) => setTimeout(r, 2500));
    return true;
  });
  if (ok !== true) { console.log('never joined:', ok, errs.slice(0, 3).join(' / ')); await b.close(); throw new Error('never joined'); }
  await pg.evaluate(async () => {
    const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js');
    const css = document.createElement('style'); css.textContent = 'body > :not(#game) { display: none !important; } #hrStatic { display: none !important; }'; document.head.append(css);
    G.vmCamera.layers.disableAll();
    window.__pin = null;
    setInterval(() => { const q = window.__pin; if (q) { if (!window.__hide) window.__hide = ME.pos.slice(); ME.pos = q.p.slice(); ME.vel = [0, 0, 0]; ME.yaw = q.yaw; ME.pitch = q.pitch; } }, 4);
    const { net } = await import('/js/net.js'), send0 = net.send.bind(net);
    net.send = (o) => send0(window.__pin && window.__hide && o && o.t === 's' ? { ...o, p: window.__hide.map((v) => Math.round(v * 100) / 100), v: [0, 0, 0] } : o); // (the bot hunts where you spawned, not the camera)
    const draw = G.renderer.render.bind(G.renderer);
    G.renderer.render = (sc, cam) => {
      if (cam === G.camera && window.__pin && window.__fov && cam.fov !== window.__fov) { cam.fov = window.__fov; cam.updateProjectionMatrix(); }
      if (cam === G.camera && window.__pin) G.remotes.forEach((r) => { if (r.ch && r.ch.root) r.ch.root.visible = false; });
      return draw(sc, cam);
    };
  });
  const lookAt = (cam, c) => { const dx = c[0] - cam[0], dy = c[1] - cam[1], dz = c[2] - cam[2]; return { p: [cam[0], cam[1], cam[2]], yaw: Math.atan2(-dx, -dz), pitch: Math.atan2(dy, Math.hypot(dx, dz)) }; };
  const shots = [];
  for (const pr of presets) {
    await pg.evaluate(async (pr) => { const { G } = await import('/js/ctx.js'); const w = await import('/js/world.js'); G.settings.jank = pr; w.setJank(pr); }, pr);
    await sleep(1500);
    for (const [name, ci, fov, lookY] of VIEWS) {
      const cam = SPOT.cams[ci], h = SPOT.hr, v = lookAt([cam[0], cam[1] + 1.6, cam[2]], [h[0], h[1] + lookY, h[2]]);
      v.p[1] -= 1.6;
      await pg.evaluate(async ({ v, fov, h, cam, pose }) => {
        window.__pin = { p: v.p, yaw: v.yaw, pitch: v.pitch }; window.__fov = fov;
        const m = await import('/js/hrguy.js');
        m.hrMsg({ on: 1, p: h, y: Math.atan2(h[0] - cam[0], h[2] - cam[2]), tg: -1, pose, st: 0 });
      }, { v, fov, h, cam, pose: SPOT.pose });
      await sleep(2500);
      for (let i = 0; i < 60; i++) { // (dead: wait for the respawn)
        const alive = await pg.evaluate(async () => { const { ME } = await import('/js/player.js'); return ME.alive; });
        if (alive) break; await sleep(1000);
      }
      await pg.evaluate(async ({ h, cam, pose }) => { const m = await import('/js/hrguy.js'); m.hrMsg({ on: 1, p: h, y: Math.atan2(h[0] - cam[0], h[2] - cam[2]), tg: -1, pose, st: 0 }); }, { h, cam, pose: SPOT.pose });
      await sleep(1200);
      const f = path.join(outdir, `${tag}_${name}_${pr}.png`);
      await pg.screenshot({ path: f });
      shots.push(f); console.log('shot', f);
    }
  }
  const info = await pg.evaluate(async () => { // what he's made of right now
    const { G } = await import('/js/ctx.js'); const S = G.hrState; let meshes = 0, tris = 0; const mats = new Set();
    if (S.mesh) S.mesh.traverse((o) => { if (o.isMesh && o.visible) { meshes++; mats.add(o.material); const g = o.geometry; tris += (g.index ? g.index.count : g.attributes.position.count) / 3; } });
    return { glb: !!(S.mesh && S.mesh.userData.glb), meshes, tris: Math.round(tris), mats: mats.size, calls: G.renderer.info.render.calls };
  });
  console.log('HR', JSON.stringify(info));
  fs.writeFileSync(path.join(outdir, `${tag}_errors.txt`), errs.join('\n') + '\n');
  console.log('errors', errs.length, errs.slice(0, 5).join('\n'));
  await b.close();
}
(async () => { // (a crashed tab, e.g. the machine ran out of memory: start over, up to 3 times)
  for (let i = 0; i < 3; i++) { try { await session(); return; } catch (e) { console.log('attempt', i + 1, 'failed:', String(e).split('\n')[0]); } }
  process.exit(1);
})();
