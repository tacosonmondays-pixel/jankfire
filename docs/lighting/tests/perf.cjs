// node perf.cjs <port> <label> : renderer.info + timing per preset on 3 maps
require(process.env.PWLOCK || '/dev/null'); // pwlock.cjs from claude/handoff:handoff/tests caps headless browsers
const { chromium } = require('playwright');
const [port, label] = process.argv.slice(2);
const MAPS = (process.env.MAPS || 'jankburg,skyline,suburb').split(',');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio', '--disable-frame-rate-limit', '--disable-gpu-vsync'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.goto(`http://localhost:${port}/`); await pg.waitForTimeout(800);
  await pg.click('#scr-main [data-mode="training"]'); await pg.waitForTimeout(3000);
  if (process.env.FORCE) await pg.evaluate(() => { window.__force = true; });
  await pg.evaluate(async () => {
    const { G } = await import('/js/ctx.js');
    const r = G.renderer; r.info.autoReset = false;
    const P = (window.__perf = { frames: 0, calls: 0, tris: 0, ms: 0, shMs: 0, shCalls: 0, shN: 0 });
    const rr = r.render.bind(r);
    r.render = (s, c) => { const t = performance.now(); rr(s, c); P.ms += performance.now() - t; };
    const sm = r.shadowMap, sr = sm.render.bind(sm);
    sm.render = (lights, s, c) => { const t = performance.now(), c0 = r.info.render.calls; sr(lights, s, c); const dc = r.info.render.calls - c0; if (dc) { P.shN++; P.shCalls += dc; } P.shMs += performance.now() - t; };
    const sun = G.scene.children.find((o) => o.isDirectionalLight);
    const loop = () => { if (window.__force) sun.shadow.needsUpdate = true; P.frames++; P.calls += r.info.render.calls; P.tris += r.info.render.triangles; r.info.reset(); requestAnimationFrame(loop); };
    requestAnimationFrame(loop);
  });
  const rows = [];
  for (const id of MAPS) for (const j of (process.env.PRESETS || '0,1,2,3').split(',').map(Number)) {
    await pg.evaluate(async ([id, j]) => {
      const W = await import('/js/world.js'); const { MAPS } = await import('/shared/map.js'); const { ME } = await import('/js/player.js');
      W.setJank(j); if (window.__map !== id) { W.loadMap(id); window.__map = id; }
      const m = MAPS[id], s = m.spawns[0];
      clearInterval(window.__fly);
      let t = 0;
      window.__fly = setInterval(() => { t += 0.005; ME.pos = [s[0] + Math.sin(t) * 6, s[1] + 3, s[2] + Math.cos(t) * 6]; ME.vel = [0, 0, 0]; ME.yaw = t * 0.6; ME.pitch = -0.2; }, 5); // a slow circle: the shadow centre moves now and then
    }, [id, j]);
    await pg.waitForTimeout(7000); // shaders compile after a preset / map change: keep that out of the numbers
    await pg.evaluate(() => { const P = window.__perf; for (const k in P) P[k] = 0; window.__t0 = performance.now(); });
    await pg.waitForTimeout(6000);
    const P = await pg.evaluate(() => ({ ...window.__perf, wall: performance.now() - window.__t0 }));
    const f = Math.max(1, P.frames);
    rows.push({ map: id, preset: ['Potato', 'Crusty', 'Mid', 'TooHD'][j], fps: +(f / (P.wall / 1000)).toFixed(1), renderMs: +(P.ms / f).toFixed(2), calls: Math.round(P.calls / f), tris: Math.round(P.tris / f), shadowPassesPerFrame: +(P.shN / f).toFixed(2), shadowCallsPerPass: P.shN ? Math.round(P.shCalls / P.shN) : 0, shadowMsPerFrame: +(P.shMs / f).toFixed(2) });
    console.log(JSON.stringify(rows[rows.length - 1]));
  }
  require('fs').writeFileSync(`${__dirname}/perf_${label}.json`, JSON.stringify(rows, null, 1));
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
