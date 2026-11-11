// Code-built things lined up one at a time on the Training range, each framed on its own bounding box, in the game's
// light (docs/blender/INVENTORY.md's sheets for the weapons, gear, characters and menu groups).
// usage: node tools/blender/shots_lineup.cjs <port> <outdir> <items.json> [preset=3]
//   items.json: [{ sheet, label, js }]: js is the body of an async function run in the page that returns the
//   THREE.Object3D to show (import the game's own builders: `const m = await import('/js/models.js'); return m.buildHole();`)
//   ({ sheet, label, home: true } = the home screen as the game opens). out: <outdir>/<sheet>.png, 4 across.
//   Cap browsers with pwlock.cjs.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const [port = '3100', outdir = '.', itemsArg, presetArg = '3'] = process.argv.slice(2);
const ITEMS = JSON.parse(fs.readFileSync(itemsArg, 'utf8')), PR = Number(presetArg);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
fs.mkdirSync(outdir, { recursive: true });
const tmp = fs.mkdtempSync(path.join(require('os').tmpdir(), 'lineup-'));

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + (e.stack || e.message).split('\n').slice(0, 3).join(' | ')));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text().slice(0, 200)); });
  await pg.addInitScript((pr) => localStorage.setItem('jf_giftseen_all', '1') || localStorage.setItem('jankfire', JSON.stringify({ name: 'SHOTS', killcam: false, jank: pr })), PR);
  await pg.goto(`http://localhost:${port}/`); await sleep(2500);
  const home = path.join(tmp, 'home.png'); // (an item with home: true is the home screen as it opens: the hero platform, the menu props)
  if (ITEMS.some((t) => t.home)) { await sleep(6000); await pg.screenshot({ path: home, timeout: 120000 }); }
  await pg.click('#scr-main [data-mode="training"]', { timeout: 180000 });
  const ok = await pg.evaluate(async () => {
    const { G } = await import('/js/ctx.js'); const { MAP } = await import('/shared/map.js');
    for (let i = 0; i < 700 && !(G.joined && MAP.id === 'range'); i++) await new Promise((r) => setTimeout(r, 100));
    return G.joined && MAP.id === 'range' ? true : 'never got to the range: ' + MAP.id;
  });
  if (ok !== true) { console.log(ok); await b.close(); process.exit(1); }
  // the camera pinned (a narrower lens, so a small thing fills the shot), only the 3D view, nobody walking through
  await pg.evaluate(async () => {
    const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js');
    const css = document.createElement('style'); css.textContent = 'body > :not(#game) { display: none !important; }'; document.head.append(css);
    G.vmCamera.layers.disableAll();
    setInterval(() => { const q = window.__pin; if (q) { ME.pos = q.p.slice(); ME.vel = [0, 0, 0]; ME.yaw = q.yaw; ME.pitch = q.pitch; ME.hp = 100; } }, 4);
    setInterval(() => { for (const o of G.scene.children) if (o.isPoints) o.visible = false; G.remotes.forEach((r) => { if (r.ch && r.ch.root) r.ch.root.visible = false; }); }, 16);
    const draw = G.renderer.render.bind(G.renderer);
    G.renderer.render = (sc, cam) => { if (cam === G.camera && cam.fov !== 40) { cam.fov = 40; cam.near = 0.02; cam.updateProjectionMatrix(); } return draw(sc, cam); };
  });
  await sleep(1500);
  const shots = [];
  for (const [i, it] of ITEMS.entries()) {
    if (it.home) { shots.push({ it, f: home }); continue; }
    const r = await pg.evaluate(async ({ js, i }) => {
      const { G } = await import('/js/ctx.js'); const THREE = await import('three');
      if (window.__obj) { G.scene.remove(window.__obj); window.__obj = null; }
      let o;
      try { o = await (new Function(`return (async () => { ${js} })();`))(); } catch (e) { return 'build failed: ' + e.message; }
      if (!o || !o.isObject3D) return 'not a 3D object';
      const holder = new THREE.Group(); holder.add(o); holder.position.set(0, 0, 20); holder.rotation.y = 0.6;
      G.scene.add(holder); window.__obj = holder;
      holder.updateMatrixWorld(true);
      const bb = new THREE.Box3().setFromObject(holder); if (bb.isEmpty()) return 'empty';
      const c = bb.getCenter(new THREE.Vector3()), s = bb.getSize(new THREE.Vector3()), size = Math.max(s.x, s.y, s.z);
      if (bb.min.y < 0.02) holder.position.y += 0.02 - bb.min.y, c.y += 0.02 - bb.min.y; // (on the floor, not in it)
      holder.traverse((m) => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; m.frustumCulled = false; } });
      const D = Math.max(0.5, size * 1.7 + 0.25), cam = [c.x + D * 0.25, c.y + D * 0.35, c.z + D * 0.92];
      const dx = c.x - cam[0], dy = c.y - cam[1], dz = c.z - cam[2];
      window.__pin = { p: [cam[0], cam[1] - 1.6, cam[2]], yaw: Math.atan2(-dx, -dz), pitch: Math.atan2(dy, Math.hypot(dx, dz)) };
      const { shadowDirty } = await import('/js/lighting.js'); shadowDirty();
      return { size: +size.toFixed(2) };
    }, { js: it.js, i });
    if (typeof r === 'string') { console.log(it.label, ':', r); shots.push({ it, f: null }); continue; }
    await sleep(1400);
    const f = path.join(tmp, `item_${i}.png`);
    await pg.screenshot({ path: f, timeout: 120000 });
    shots.push({ it, f });
  }
  await b.close();
  for (const name of [...new Set(ITEMS.map((t) => t.sheet))]) {
    const W = 480, H = 270, cells = [];
    shots.forEach((s, i) => {
      if (s.it.sheet !== name) return;
      const lab = `${s.it.label}${s.f ? '' : ' (failed)'}`.replace(/[:']/g, ' ').slice(0, 58), o = path.join(tmp, `c_${i}.png`);
      const src = s.f ? ['-i', s.f] : ['-f', 'lavfi', '-i', `color=c=0x120818:s=${W}x${H}:d=1`, '-frames:v', '1'];
      execFileSync('ffmpeg', ['-loglevel', 'error', '-y', ...src, '-vf', `scale=${W}:${H},drawbox=x=0:y=0:w=${W}:h=22:color=black@0.6:t=fill,drawtext=text='${lab}':x=8:y=4:fontsize=15:fontcolor=yellow`, o]);
      cells.push(o);
    });
    const args = []; for (const c of cells) args.push('-i', c);
    const lay = cells.map((_, i) => `${(i % 4) * W}_${Math.floor(i / 4) * H}`).join('|'), out = path.join(outdir, `${name}.png`);
    execFileSync('ffmpeg', ['-loglevel', 'error', '-y', ...args, '-filter_complex', cells.length > 1 ? `xstack=inputs=${cells.length}:layout=${lay}:fill=black` : 'null', out]);
    console.log('wrote', out);
  }
  console.log(errs.length ? 'page errors:\n  ' + errs.slice(0, 6).join('\n  ') : '(0 page errors)');
  fs.rmSync(tmp, { recursive: true, force: true });
})();
