// node bench.cjs <port> <jank> <map...>: ms per scene render from a fixed view (best of 5 batches of 8, gl synced),
// plus the same with the water hidden (liquid meshes on this branch, the old water/sea map meshes on main)
require(__dirname + '/pwlock.cjs');
const { chromium } = require('playwright');
const [port, jank, ...maps] = process.argv.slice(2);
const VIEW = { islands: [[0, 14, 62], -0.28, 0], platform: [[0, 6, 40], -0.3, 0], forest: [[62, 3, 6], -0.12, -1.4] };
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const ctx = await b.newContext({ viewport: { width: 800, height: 450 } });
  await ctx.addInitScript((j) => localStorage.setItem('jankfire', JSON.stringify({ jank: j, name: 'bench' })), Number(jank));
  for (const map of maps) {
    const pg = await ctx.newPage();
    await pg.goto(`http://localhost:${port}/`); await pg.waitForTimeout(800);
    await pg.click('[data-pick="bots"]', { force: true }); await pg.waitForTimeout(700); await pg.click('#mpCustom', { force: true });
    await pg.selectOption('#setupMap', map); await pg.locator('#setupBots').fill('1'); await pg.selectOption('#setupDiff', 'easy');
    await pg.click('#setupGo', { force: true }); await pg.waitForTimeout(4000);
    const r = await pg.evaluate(async ([p, pitch, yaw]) => {
      const { ME } = await import('/js/player.js'); const { G } = await import('/js/ctx.js');
      setInterval(() => { ME.pos = [p[0], p[1] - 1.6, p[2]]; ME.vel = [0, 0, 0]; ME.pitch = pitch; ME.yaw = yaw; }, 5);
      await new Promise((r) => setTimeout(r, 2000));
      const R = G.renderer, gl = R.getContext(), px = new Uint8Array(4), cam = G.camera.clone();
      const water = []; G.scene.traverse((o) => { const m = o.material; if (o.isMesh && m && (m.userData && m.userData.liquid || (!m.isShaderMaterial && m.transparent && m.color && [0x3a9ae8, 0x2ab8d4, 0x24607a, 0x86dbe6].includes(m.color.getHex())))) water.push(o); });
      const time = () => { let best = 1e9; for (let k = 0; k < 5; k++) { const t0 = performance.now(); for (let i = 0; i < 8; i++) { R.clear(); R.render(G.scene, cam); } gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px); best = Math.min(best, (performance.now() - t0) / 8); } return best; };
      time();
      const withW = time(); water.forEach((o) => { o.userData._v = o.visible; o.visible = false; }); const noW = time(); water.forEach((o) => { o.visible = o.userData._v; });
      return { msWith: +withW.toFixed(1), msNoWater: +noW.toFixed(1), waterMs: +(withW - noW).toFixed(1), waterMeshes: water.length };
    }, VIEW[map]);
    console.log(`${map} jank${jank}`, JSON.stringify(r));
    await pg.close();
  }
  await b.close();
})();
