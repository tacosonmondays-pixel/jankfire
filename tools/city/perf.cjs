// City streaming in a real browser: node tools/city/perf.cjs <port> <outDir> [city] [presets=0,3] [secs=40]
// 1. hash: 40 chunks built in the page's chunk worker hash the same as in Node (server == client, to the bit)
// 2. per preset: a fly-through (fast laps over the roofs at 60 m/s and high at 120 m/s) and a walk-through (on the
//    ground, the real physics); records the streamer's main-thread ms per frame (max = hitch), draw calls, triangles,
//    chunks per ring, geometry MB, JS heap. Screenshots along the way. Prints JSON, writes <outDir>/perf.json.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [port = 3107, out = '.', city = 'stress', presetArg = '0,3', secsArg = '40'] = process.argv.slice(2);
const presets = presetArg.split(',').map(Number), secs = Number(secsArg);
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const { buildChunk, packChunk, hashChunk } = await import(path.resolve(__dirname, '../../shared/city/chunk.js'));
  await import(path.resolve(__dirname, '../../shared/city/slice.js'));
  const { CITIES } = await import(path.resolve(__dirname, '../../shared/city/plan.js'));
  const C = CITIES[city];
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio', '--ignore-gpu-blocklist', '--enable-precise-memory-info', '--js-flags=--expose-gc'] });
  const page = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = [];
  page.on('pageerror', (e) => errs.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  const res = { city, hash: null, runs: [] };
  for (const pr of presets) {
    await page.goto(`http://localhost:${port}/storytest.html?city=${city}&jank=${pr}&fly=1&perf=1`);
    await page.waitForFunction(() => window.__city && window.__city.stream.stats().near > 0, null, { timeout: 60000 });
    await page.evaluate(() => { document.getElementById('help').style.display = 'none'; });
    if (!res.hash) { // the hash test, once
      const ids = []; for (let i = 0; i < 40; i++) ids.push([C.cx0 + ((i * 7) % (C.cx1 - C.cx0)), C.cz0 + ((i * 11) % (C.cz1 - C.cz0))]);
      const browser = await page.evaluate(async ([city, ids]) => {
        const w = new Worker('/js/city/chunkworker.js', { type: 'module' });
        const out = [];
        for (const [cx, cz] of ids) out.push(await new Promise((r) => { w.onmessage = (e) => r(e.data.hash); w.postMessage({ op: 'chunk', id: 'h', city, cx, cz, want: { hash: true } }); }));
        w.terminate(); return out;
      }, [city, ids]);
      const node = ids.map(([cx, cz]) => hashChunk(packChunk(buildChunk(city, cx, cz))));
      res.hash = { chunks: ids.length, same: node.filter((h, i) => h === browser[i]).length, sample: [node[0], browser[0]] };
    }
    const run = { preset: pr, phases: [] };
    const X0 = C.cx0 * 64 + 40, X1 = C.cx1 * 64 - 40, Z0 = C.cz0 * 64 + 40, Z1 = C.cz1 * 64 - 40;
    // phases: [name, fly, speed, height, seconds]
    for (const [name, fly, speed, h, T] of [['roofs 60 m/s', 1, 60, 40, secs / 2], ['high 120 m/s', 1, 120, 140, secs / 4], ['walk', 0, 11, 0.3, secs / 4]]) {
      const r = await page.evaluate(async ([fly, speed, h, T, X0, Z0, X1, Z1]) => {
        const c = window.__city, me = c.me, s = c.stream;
        me.fly = !!fly; me.pos = [X0, h, Z0]; me.vel = [0, 0, 0]; me.pitch = fly ? -0.25 : 0;
        const og = s.update.bind(s); let maxUp = 0, sumUp = 0, n = 0, maxCalls = 0, maxTris = 0, worstFrame = 0, last = performance.now(), held = 0;
        s.update = (cam, dt) => { const t = performance.now(); og(cam, dt); const ms = performance.now() - t; if (n > 5) maxUp = Math.max(maxUp, ms); sumUp += ms; n++; };
        const t0 = performance.now(); let k = 0;
        // a lap: a rectangle round the city, then a diagonal back through the middle
        const pts = [[X0, Z0], [X1, Z0], [X1, Z1], [X0, Z1], [X1, Z0]];
        let seg = 0, along = 0;
        while (performance.now() - t0 < T * 1000) {
          await new Promise((res) => requestAnimationFrame(res));
          const now = performance.now(), dt = Math.min(0.05, (now - last) / 1000); last = now;
          if (n > 10) worstFrame = Math.max(worstFrame, dt * 1000);
          const a = pts[seg % (pts.length - 1)], b2 = pts[seg % (pts.length - 1) + 1], L = Math.hypot(b2[0] - a[0], b2[1] - a[1]);
          me.yaw = Math.atan2(-(b2[0] - a[0]), -(b2[1] - a[1]));
          if (fly) { along += speed * dt; if (along > L) { along = 0; seg++; } me.pos = [a[0] + (b2[0] - a[0]) * along / L, h, a[1] + (b2[1] - a[1]) * along / L]; window.__auto = null; }
          else { window.__auto = { z: 1 }; if (++k % 240 === 0) { me.pos = [a[0] + Math.random() * 200, 30, a[1] + Math.random() * 200]; me.vel = [0, 0, 0]; } } // walk, dropping in somewhere new every 4 s
          const i = c.renderer.info.render; maxCalls = Math.max(maxCalls, i.calls); maxTris = Math.max(maxTris, i.triangles);
        }
        window.__auto = null; s.update = og;
        const st = s.stats(), mem = performance.memory;
        return { maxUpdateMs: +maxUp.toFixed(1), avgUpdateMs: +(sumUp / Math.max(1, n)).toFixed(2), frames: n, worstFrameMs: +worstFrame.toFixed(0), fps: +c.fps().toFixed(1), maxCalls, maxTris, held: +me.held.toFixed(1), ...st, heapMB: mem ? +(mem.usedJSHeapSize / 1048576).toFixed(0) : null, gpuGeos: c.renderer.info.memory.geometries, gpuTex: c.renderer.info.memory.textures };
      }, [fly, speed, h, T, X0, Z0, X1, Z1]);
      r.name = name;
      await page.screenshot({ path: path.join(out, `perf_${city}_${pr}_${name.split(' ')[0]}.png`) });
      run.phases.push(r);
    }
    res.runs.push(run);
  }
  res.pageErrors = errs.slice(0, 10);
  fs.writeFileSync(path.join(out, 'perf.json'), JSON.stringify(res, null, 1));
  console.log(JSON.stringify(res, null, 1));
  await b.close();
})();
