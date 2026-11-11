// Round 4 traffic sheet: every traffic car built two ways, the code car (cars.js buildDesign) next to the Blender one
// (p_car_<type>.glb), parked in the same spot, same camera, Too HD and Potato. On Training's range: flat, no traffic of
// its own, dummies that don't shoot. usage: node tools/blender/shots_traffic.cjs <port> <outdir>
// out: <outdir>/r4_traffic.png (a row per car, columns = code / Blender per preset). Cap browsers with pwlock.cjs.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const [port = '3100', outdir = 'tools/blender/compare'] = process.argv.slice(2);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const TYPES = ['hatch', 'sedan', 'taxi', 'pickup', 'van', 'icecream', 'truck', 'bus'];
const PRESET = ['Potato', 'Crusty', 'Mid', 'Too HD'];
fs.mkdirSync(outdir, { recursive: true });
const tmp = fs.mkdtempSync(path.join(require('os').tmpdir(), 'r4traffic-'));

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + (e.stack || e.message).split('\n').slice(0, 3).join(' | ')));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text().slice(0, 200)); });
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ name: 'SHOTS', killcam: false, jank: 3 })));
  await pg.goto(`http://localhost:${port}/`); await sleep(2500);
  await pg.click('#scr-main [data-mode="training"]', { timeout: 180000 });
  const ok = await pg.evaluate(async (types) => {
    const { G } = await import('/js/ctx.js'); const { MAP } = await import('/shared/map.js'); const k = await import('/js/glbkit.js');
    for (let i = 0; i < 700 && !(G.joined && MAP.id === 'range'); i++) await new Promise((r) => setTimeout(r, 100));
    if (!(G.joined && MAP.id === 'range')) return 'never got to the range: ' + MAP.id;
    k.prefetch(types.map((t) => 'p_car_' + t)); // (the cars come with the maps that drive them: fetch them all here)
    for (let i = 0; i < 300 && types.some((t) => !k.AUTHORED['p_car_' + t]); i++) await new Promise((r) => setTimeout(r, 100));
    const miss = types.filter((t) => !k.AUTHORED['p_car_' + t]);
    return miss.length ? 'no Blender file for ' + miss.join(', ') : true;
  }, TYPES);
  if (ok !== true) { console.log(ok, errs.slice(0, 3).join(' / ')); await b.close(); process.exit(1); }
  // the camera pinned (a narrower lens than the game's, so a car fills the shot), only the 3D view, the cars'
  // materials as traffic.js makes them (the jank snap + the haze)
  await pg.evaluate(async () => {
    const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js');
    const css = document.createElement('style'); css.textContent = 'body > :not(#game) { display: none !important; }'; document.head.append(css);
    G.vmCamera.layers.disableAll();
    setInterval(() => { const q = window.__pin; if (q) { ME.pos = q.p.slice(); ME.vel = [0, 0, 0]; ME.yaw = q.yaw; ME.pitch = q.pitch; ME.hp = 100; } }, 4);
    setInterval(() => { for (const o of G.scene.children) if (o.isPoints) o.visible = false; G.remotes.forEach((r) => { if (r.ch && r.ch.root) r.ch.root.visible = false; }); }, 16);
    const draw = G.renderer.render.bind(G.renderer);
    G.renderer.render = (sc, cam) => { if (cam === G.camera && cam.fov !== 42) { cam.fov = 42; cam.updateProjectionMatrix(); } return draw(sc, cam); };
    const { initCarMats } = await import('/js/cars.js'); const { jankify } = await import('/js/jank.js'); const { hazify } = await import('/js/world.js');
    window.__carPatch = (m) => { jankify(m); const j = m.onBeforeCompile; hazify(m, 1); const h = m.onBeforeCompile; m.onBeforeCompile = (sh, r) => { j(sh, r); h(sh, r); }; m.customProgramCacheKey = () => 'carhaze'; return m; }; // (traffic.js's patch)
    initCarMats(window.__carPatch);
  });
  const shots = [];
  for (const pr of [3, 0]) {
    await pg.evaluate(async (pr) => { const { G } = await import('/js/ctx.js'); const w = await import('/js/world.js'); G.settings.jank = pr; w.setJank(pr); }, pr);
    await sleep(1500);
    for (let i = 0; i < TYPES.length; i++) for (const code of [true, false]) {
      // the car parked on the range turned three-quarters to the camera, the camera framed on it
      await pg.evaluate(async ({ ty, i, code }) => {
        const { G } = await import('/js/ctx.js'); const cars = await import('/js/cars.js'); const k = await import('/js/glbkit.js'); const { CAR_COLORS, CARS } = await import('/shared/traffic.js');
        if (window.__car) { G.scene.remove(window.__car); window.__car = null; }
        const key = 'p_car_' + ty, keep = k.AUTHORED[key];
        if (code) delete k.AUTHORED[key]; // (makeCar builds the code car when there's no Blender one)
        let v;
        try { v = cars.makeCar(ty, CAR_COLORS[i % CAR_COLORS.length], i, window.__carPatch); } finally { if (code) k.AUTHORED[key] = keep; }
        v.root.position.set(0, 0, 20); v.root.rotation.y = 0.75; // (three-quarters on: the nose and a side)
        v.root.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
        G.scene.add(v.root); window.__car = v.root;
        const T = CARS[ty], D = Math.max(6.5, T.L * 1.25 + 2), cam = [0, T.H * 0.7 + 1.4, 20 + D], at = [0, T.H * 0.45, 20]; // (the camera inside the range: z under 40)
        const dx = at[0] - cam[0], dy = at[1] - cam[1], dz = at[2] - cam[2];
        window.__pin = { p: [cam[0], cam[1] - 1.6, cam[2]], yaw: Math.atan2(-dx, -dz), pitch: Math.atan2(dy, Math.hypot(dx, dz)) };
        const { shadowDirty } = await import('/js/lighting.js'); shadowDirty();
      }, { ty: TYPES[i], i, code });
      await sleep(1600);
      const f = path.join(tmp, `traffic_${TYPES[i]}_${pr}_${code ? 'code' : 'glb'}.png`);
      await pg.screenshot({ path: f, timeout: 120000 });
      shots.push({ ty: TYPES[i], pr, code, f });
    }
  }
  // the sheet: a row per car, columns = code / Blender for each preset
  const W = 480, H = 270, cells = [];
  for (const ty of TYPES) for (const pr of [3, 0]) for (const code of [true, false]) {
    const s = shots.find((x) => x.ty === ty && x.pr === pr && x.code === code);
    const lab = `${code ? 'code car' : 'Blender'} - ${PRESET[pr]} - ${ty}`;
    const o = s.f.replace(/\.png$/, '_l.png');
    execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-i', s.f, '-vf', `scale=${W}:${H},drawbox=x=0:y=0:w=${W}:h=22:color=black@0.6:t=fill,drawtext=text='${lab}':x=8:y=4:fontsize=15:fontcolor=${code ? 'white' : 'yellow'}`, o]);
    cells.push(o);
  }
  const args = [];
  for (const c of cells) args.push('-i', c);
  const lay = cells.map((_, i) => `${(i % 4) * W}_${Math.floor(i / 4) * H}`).join('|');
  const out = path.join(outdir, 'r4_traffic.png');
  execFileSync('ffmpeg', ['-loglevel', 'error', '-y', ...args, '-filter_complex', `xstack=inputs=${cells.length}:layout=${lay}`, out]);
  console.log('wrote', out, errs.length ? '\npage errors:\n  ' + errs.slice(0, 6).join('\n  ') : '(0 page errors)');
  await b.close();
})();
