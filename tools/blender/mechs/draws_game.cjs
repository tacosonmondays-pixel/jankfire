// What one hero mech costs to draw in a real game: the game's own buildMech (its paint tint, the hero kit's ink and
// glows) stood 9 m in front of the camera on a map. Every mesh the mech owns counts its own draws (onBeforeRender runs
// once per draw, in every pass: the main view, reflections, shadows), and the renderer counts its passes, so the
// numbers don't wobble with whatever else the frame draws. Saves a picture of it too.
// usage: node tools/blender/mechs/draws_game.cjs <port> <outDir> <frame> [preset=3] [map=battleisland] [tag]
//   (map range = the Training range; anything else = a bots custom game on that map, its mode picked for it)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [port = '3100', outDir = '.', frame = 'wrecking', presetArg = '3', map = 'battleisland', tag = ''] = process.argv.slice(2);
const PR = Number(presetArg), sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const GAME = { battleisland: 'island', jankburg: 'br', deadmall: 'zm' };
fs.mkdirSync(outDir, { recursive: true });
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } }), errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + (e.stack || e.message).split('\n').slice(0, 3).join(' | ')));
  await pg.addInitScript((pr) => { localStorage.setItem('jf_giftseen_all', '1'); localStorage.setItem('jankfire', JSON.stringify({ name: 'DRAWS', killcam: false, jank: pr })); }, PR);
  const QS = process.env.JF_SHOT_QS || (map === 'battleisland' ? '?wip=1' : ''); // (Battle Island is still a WIP map: the server wants JF_WIP_MAPS=1 too)
  await pg.goto(`http://localhost:${port}/${QS}`); await sleep(2500);
  const T = { timeout: 180000 };
  if (map === 'range') await pg.click('#scr-main [data-mode="training"]', T);
  else {
    await pg.click('#scr-main [data-pick="bots"]', T); await pg.click('#mpCustom', T);
    await pg.selectOption('#setupGame', GAME[map] || 'dm', T); await pg.selectOption('#setupMap', map, T);
    const bots = pg.locator('#setupBots'); if (await bots.isVisible() && await bots.isEnabled()) await bots.fill('1');
    await pg.selectOption('#setupDiff', 'easy', { timeout: 3000 }).catch(() => {});
    await pg.click('#setupGo', T);
  }
  const info = await pg.evaluate(async ([F, mapId]) => {
    const THREE = await import('three'); const { G } = await import('/js/ctx.js'); const { MAP } = await import('/shared/map.js'); const { ME } = await import('/js/player.js');
    for (let i = 0; i < 900 && !(G.joined && MAP.id === mapId); i++) await new Promise((r) => setTimeout(r, 100));
    if (!(G.joined && MAP.id === mapId)) return { err: 'never got to ' + mapId + ' (on ' + MAP.id + ')' };
    const kit = await import('/js/glbkit.js'); const mm = await import('/js/mechmodel.js');
    const id = 'x_mech_' + F; kit.prefetch([id], 9);
    for (let i = 0; i < 400 && !kit.AUTHORED[id]; i++) await new Promise((r) => setTimeout(r, 150));
    if (!kit.AUTHORED[id]) return { err: 'the game never loaded ' + id };
    const css = document.createElement('style'); css.textContent = 'body > :not(#game) { display: none !important; }'; document.head.append(css);
    G.vmCamera.layers.disableAll();
    const at = ME.pos.slice(); // (where we spawned: on the ground)
    setInterval(() => { ME.pos = at.slice(); ME.vel = [0, 0, 0]; ME.hp = 100; G.remotes.forEach((r) => { if (r.ch && r.ch.root) r.ch.root.visible = false; if (r.marker) r.marker.visible = false; if (r.tag) r.tag.visible = false; }); }, 4);
    let inst = mm.buildMech(F, '#ff7a1c'), via = 'buildMech';
    if (!inst || !inst.glb || inst.frame !== F) { // (a hero this build's mechmodel doesn't know yet: the glb through glbkit + the hero kit, like hero_game.cjs)
      if (inst && mm.freeMech) mm.freeMech(inst);
      const look = await import('/js/mechlook.js'), SKU = await import('three/addons/utils/SkeletonUtils.js');
      const a = kit.authored(id); let glb = a.obj, skn = false; glb.traverse((o) => { if (o.isSkinnedMesh) skn = true; });
      if (skn) glb = SKU.clone(kit.AUTHORED[id].scene);
      const meta = a.meta || kit.metaOf(glb) || {}, root = new THREE.Group(); root.add(glb);
      const j = {}, att = {}; glb.traverse((o) => { if (meta.joints && Object.hasOwn(meta.joints, o.name)) j[o.name] = o; if (/^mk_/.test(o.name)) att[o.name] = o; });
      inst = { frame: F, root, j, att, own: {}, flames: [], t: 0, glb: true, clip: 'idle', act: null };
      inst.mixer = new THREE.AnimationMixer(glb); const idle = (glb.animations || []).find((c) => c.name === 'idle'); if (idle) inst.mixer.clipAction(idle).play();
      look.lookMech(inst, glb, '#ff7a1c', kit.AUTHORED[id].scene); inst.lookTick = look.lookTick; via = 'glbkit + mechlook';
    }
    inst.root.position.set(at[0], at[1], at[2] - 9); inst.root.rotation.y = Math.PI * 0.85; G.scene.add(inst.root);
    let last = performance.now();
    const tick = () => { const n = performance.now(), dt = Math.min(0.1, (n - last) / 1000); last = n; if (inst.lookTick) { inst.t += dt; inst.mixer.update(dt); inst.lookTick(inst, {}, dt); } else mm.poseMech(inst, {}, dt); requestAnimationFrame(tick); };
    tick();
    const cam = { e: [at[0] + 3.2, at[1] + 3.0, at[2] - 1.5], t: [at[0], at[1] + 2.0, at[2] - 9] };
    G.scene.onBeforeRender = (r, sc, c) => { c.position.fromArray(cam.e); c.lookAt(cam.t[0], cam.t[1], cam.t[2]); if (c.fov !== 55) { c.fov = 55; c.updateProjectionMatrix(); } c.updateMatrixWorld(); };
    const C = { draws: 0, tris: 0, passes: 0, main: 0 };
    const hook = () => inst.root.traverse((o) => { if (!o.isMesh || o.userData.jfCount) return; o.userData.jfCount = 1; const prev = o.onBeforeRender;
      o.onBeforeRender = function (r, sc, cam, geo, mat, grp) { C.draws++; const ix = geo.index; C.tris += Math.round((grp ? grp.count : (ix ? ix.count : geo.attributes.position.count)) / 3); if (cam === G.camera) C.main++; return prev.apply(this, arguments); }; });
    const rr = G.renderer.render.bind(G.renderer); G.renderer.render = (sc, cam) => { C.passes++; return rr(sc, cam); };
    window.__count = (frames) => new Promise((res) => {
      hook(); let n = -2; const S = { draws: 0, tris: 0, passes: 0, main: 0 }; // (two frames to settle)
      const f = () => { if (n >= 0) for (const k in S) S[k] += C[k]; for (const k in C) C[k] = 0; if (++n < frames) requestAnimationFrame(f); else res(Object.fromEntries(Object.entries(S).map(([k, v]) => [k, +(v / frames).toFixed(1)]))); };
      for (const k in C) C[k] = 0; requestAnimationFrame(f);
    });
    let prims = 0, mats = new Set(); inst.root.traverse((o) => { if (o.isMesh && o.visible) { prims++; mats.add(o.material); } });
    return { meshes: prims, materials: mats.size, ink: inst.look ? inst.look.outline.length : 0, via };
  }, [frame, map]);
  if (info.err) { console.log(info.err, errs.slice(0, 3)); await b.close(); process.exit(1); }
  await sleep(5000); // (shaders compile on first sight: software GL is slow)
  const c = await pg.evaluate(() => window.__count(10)); await sleep(1500);
  const shot = path.join(outDir, `${frame}_draws_${map}_${PR}${tag}.jpg`); await pg.screenshot({ path: shot, type: 'jpeg', quality: 88, timeout: 180000 });
  await b.close();
  const res = { frame, map, preset: PR, mech_draws_per_frame: c.draws, in_the_main_view: c.main, render_passes_per_frame: c.passes, mech_tris_per_frame: c.tris, ...info };
  console.log('DRAWS', JSON.stringify(res), errs.length ? errs.slice(0, 5) : '(0 page errors)');
  console.log(shot);
  process.exit(errs.length ? 1 : 0);
})();
