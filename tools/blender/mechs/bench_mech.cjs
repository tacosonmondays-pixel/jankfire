// What a squad of one hero costs to draw: N copies on the Training range (spread 12-45 m out, like a fight on Battle
// Island), the game's renderer at a preset, through the game's own glb pipeline and the hero kit (ink hulls, rim,
// glows, the far LOD). Per mode: triangles and draw calls per frame (exact) and the mean frame time (software GL here:
// read it as relative, not as a real GPU's number).
// usage: node tools/blender/mechs/bench_mech.cjs <port> <hero> [n=8] [preset=2] [modes=none,near,auto,far] [secs=6]
//   none = the range alone, near / far = every mech held on one LOD, auto = the LOD picks by distance (the game)
const { chromium } = require('playwright');
const [port = '3100', hero = 'vending', nArg = '8', presetArg = '2', modesArg = 'none,near,auto,far', secsArg = '6'] = process.argv.slice(2);
const N = Number(nArg), PR = Number(presetArg), SECS = Number(secsArg), sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 800, height: 450 } }), errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + (e.stack || e.message).split('\n').slice(0, 3).join(' | ')));
  await pg.addInitScript((pr) => { localStorage.setItem('jf_giftseen_all', '1'); localStorage.setItem('jankfire', JSON.stringify({ name: 'BENCH', killcam: false, jank: pr })); }, PR);
  await pg.goto(`http://localhost:${port}/`); await sleep(2500);
  await pg.click('#scr-main [data-mode="training"]', { timeout: 180000 });
  const ok = await pg.evaluate(async ([H, N]) => {
    const THREE = await import('three'); const { G } = await import('/js/ctx.js'); const { MAP } = await import('/shared/map.js'); const { ME } = await import('/js/player.js');
    for (let i = 0; i < 700 && !(G.joined && MAP.id === 'range'); i++) await new Promise((r) => setTimeout(r, 100));
    if (!(G.joined && MAP.id === 'range')) return 'never got to the range';
    const kit = await import('/js/glbkit.js'); const look = await import('/js/mechlook.js');
    const id = 'x_mech_' + H; kit.prefetch([id], 9);
    for (let i = 0; i < 400 && !kit.AUTHORED[id]; i++) await new Promise((r) => setTimeout(r, 150));
    if (!kit.AUTHORED[id]) return 'the game never loaded ' + id;
    const css = document.createElement('style'); css.textContent = 'body > :not(#game) { display: none !important; }'; document.head.append(css);
    G.vmCamera.layers.disableAll();
    setInterval(() => { ME.pos = [0.4, 0, -3]; ME.vel = [0, 0, 0]; ME.hp = 100; G.remotes.forEach((r) => { if (r.ch && r.ch.root) r.ch.root.visible = false; if (r.marker) r.marker.visible = false; if (r.tag) r.tag.visible = false; }); }, 4);
    const insts = [];
    for (let i = 0; i < N; i++) {
      const a = kit.authored(id), SKU = await import('three/addons/utils/SkeletonUtils.js'); let glb = a.obj, skn = false; glb.traverse((o) => { if (o.isSkinnedMesh) skn = true; });
      if (skn) glb = SKU.clone(kit.AUTHORED[id].scene); // (a skinned hero: its bones cloned with it, like buildMech does)
      const meta = a.meta || {}, root = new THREE.Group();
      const row = Math.floor(i / 4), col = i % 4;
      root.add(glb); root.position.set((col - 1.5) * 9, 0, -14 - row * 22 - (col % 2) * 6); root.rotation.y = Math.PI + (col - 1.5) * 0.3; G.scene.add(root);
      const j = {}, att = {};
      glb.traverse((o) => { if (meta.joints && Object.hasOwn(meta.joints, o.name)) j[o.name] = o; if (/^mk_/.test(o.name)) att[o.name] = o; });
      const inst = { frame: H, root, j, att, own: {}, flames: [], t: 0, glb: true, clip: 'idle', act: null };
      inst.mixer = new THREE.AnimationMixer(glb); const clip = (glb.animations || []).find((c) => c.name === 'walk') || glb.animations[0];
      if (clip) { const act = inst.mixer.clipAction(clip); act.time = i * 0.11; act.play(); }
      look.lookMech(inst, glb, '#ffffff', kit.AUTHORED[id].scene);
      insts.push(inst);
    }
    let last = performance.now();
    const tick = () => { const n = performance.now(), dt = Math.min(0.1, (n - last) / 1000); last = n; for (const inst of insts) { inst.t += dt; inst.mixer.update(dt); look.lookTick(inst, {}, dt); } requestAnimationFrame(tick); };
    tick();
    window.__mode = (m) => { for (const inst of insts) { inst.root.visible = m !== 'none'; if (inst.look) inst.look.lodForce = m === 'near' ? false : m === 'far' ? true : null; } };
    const cam = { e: [0, 2.0, 2.0], t: [0, 2.4, -30] };
    G.scene.onBeforeRender = (r, sc, c) => { c.position.fromArray(cam.e); c.lookAt(cam.t[0], cam.t[1], cam.t[2]); if (c.fov !== 70) { c.fov = 70; c.updateProjectionMatrix(); } c.updateMatrixWorld(); };
    const info = G.renderer.info; info.autoReset = false; // (the whole frame: every pass, not just the last post pass)
    window.__measure = (ms) => new Promise((res) => {
      const t0 = performance.now(); let n = 0, tri = 0, calls = 0, prev = t0; const dts = [];
      info.reset();
      const f = () => { const t = performance.now(); dts.push(t - prev); prev = t; n++; tri += info.render.triangles; calls += info.render.calls; info.reset();
        if (t - t0 < ms) requestAnimationFrame(f); else { dts.shift(); dts.sort((a, b) => a - b); res({ frames: n, ms: +(dts.reduce((a, b) => a + b, 0) / dts.length).toFixed(1), p50: +dts[dts.length >> 1].toFixed(1), tris: Math.round(tri / n), calls: Math.round(calls / n), far: insts.filter((i) => i.look && i.look.isFar).length }); } };
      requestAnimationFrame(f);
    });
    return 'ok';
  }, [hero, N]);
  if (ok !== 'ok') { console.log(ok); await b.close(); process.exit(1); }
  await sleep(5000); // (shaders compile on first sight)
  const out = {};
  for (const m of modesArg.split(',')) {
    await pg.evaluate((m) => window.__mode(m), m); await sleep(1500);
    out[m] = await pg.evaluate((ms) => window.__measure(ms), SECS * 1000);
    console.log(`BENCH ${hero} n=${N} preset=${PR} ${m}: ${JSON.stringify(out[m])}`);
  }
  await b.close();
  console.log(errs.length ? errs.slice(0, 6) : '(0 page errors)');
  process.exit(errs.length ? 1 : 0);
})();
