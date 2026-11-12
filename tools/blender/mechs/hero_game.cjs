// A Battle Island hero's file (public/models/x_mech_<hero>.glb) in the real game before its gameplay code exists:
// Training range, the game's lights, sky and renderer at a preset, loaded through the game's own glb pipeline
// (glbkit) with the hero kit on it (public/js/mechlook.js: rim light, ink, glows, stickers), posed by its own clips.
// usage: node tools/blender/mechs/hero_game.cjs <port> <outDir> <hero> [preset=3]
//   (start a server after the glb is in public/models: it lists the models when it boots)
//   writes <hero>_<preset>_<shot>.jpg and <hero>_<preset>.jpg (all of them on one sheet)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const { execFileSync } = require('child_process');
const [port = '3100', outDir = '.', hero = 'wrecking', presetArg = '3'] = process.argv.slice(2);
const PR = Number(presetArg), sleep = (ms) => new Promise((r) => setTimeout(r, ms));
fs.mkdirSync(outDir, { recursive: true });
const P = [0, 0, -16]; // (the hero stands here, facing you at the firing line)
// per hero: [name, caption, clip, t, camera eye (relative to P), look-at (relative to P), fov, root lift, play: let the clip run (events fire)]
const SHOTS = {
  wrecking: [
    ['hero', 'held after its landing: the window looks up at you', 'hero_intro', 1.7, [-4.6, 1.2, 6.6], [0.2, 2.5, 0], 50],
    ['close', 'close up: clean paint, white trims, the porthole and the pilot seat', 'idle', 0.0, [-1.9, 2.6, 4.2], [0.0, 2.2, 0], 50],
    ['roll', 'rolling: feet tucked, treads on the floor', 'roll', 0.3, [-6.2, 2.0, 2.6], [0, 2.0, 0], 50],
    ['slam', 'ground slam: feet stamp out, dust and a crater', 'slam', 0.27, [-5.4, 1.6, 6.2], [0, 1.8, 0], 52, 0, true],
    ['pile', 'PILE DRIVER: launched, feet folded over the top', 'pile_driver', 0.8, [-5.0, 2.4, 6.4], [0, 4.4, 0], 52, 2.6],
    ['back', 'from behind: the hatch, the hook on its chain, stickers', 'idle', 0.0, [3.8, 3.6, -5.6], [0, 2.6, 0], 50],
    ['far', 'from the firing line, 30 m: the silhouette', 'idle', 0.0, [0, 1.75, 30], [0, 2.2, 0], 75],
  ],
};

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } }), errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + (e.stack || e.message).split('\n').slice(0, 3).join(' | ')));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text().slice(0, 200)); });
  await pg.addInitScript((pr) => { localStorage.setItem('jf_giftseen_all', '1'); localStorage.setItem('jankfire', JSON.stringify({ name: 'SHOTS', killcam: false, jank: pr })); }, PR);
  await pg.goto(`http://localhost:${port}/`); await sleep(2500);
  await pg.click('#scr-main [data-mode="training"]', { timeout: 180000 });
  const info = await pg.evaluate(async ([H, P]) => {
    const THREE = await import('three'); const { G } = await import('/js/ctx.js'); const { MAP } = await import('/shared/map.js'); const { ME } = await import('/js/player.js');
    for (let i = 0; i < 700 && !(G.joined && MAP.id === 'range'); i++) await new Promise((r) => setTimeout(r, 100));
    if (!(G.joined && MAP.id === 'range')) return { err: 'never got to the range: ' + MAP.id };
    const kit = await import('/js/glbkit.js'); const look = await import('/js/mechlook.js');
    const id = 'x_mech_' + H; kit.prefetch([id], 9);
    let a = null; for (let i = 0; i < 400 && !(a = kit.authored(id)); i++) await new Promise((r) => setTimeout(r, 150));
    if (!a) return { err: 'the game never loaded ' + id };
    const css = document.createElement('style'); css.textContent = 'body > :not(#game) { display: none !important; }'; document.head.append(css);
    G.vmCamera.layers.disableAll();
    setInterval(() => { ME.pos = [0.4, 0, -3]; ME.vel = [0, 0, 0]; ME.hp = 100; G.remotes.forEach((r) => { if (r.ch && r.ch.root) r.ch.root.visible = false; if (r.marker) r.marker.visible = false; if (r.tag) r.tag.visible = false; }); }, 4);
    const glb = a.obj, meta = a.meta || kit.metaOf(glb) || {}, root = new THREE.Group();
    root.add(glb); root.position.set(P[0], P[1], P[2]); root.rotation.y = Math.PI; G.scene.add(root);
    const j = {}, att = {};
    glb.traverse((o) => { if (meta.joints && Object.hasOwn(meta.joints, o.name)) j[o.name] = o; if (/^mk_/.test(o.name)) att[o.name] = o; });
    const inst = { frame: H, root, j, att, own: {}, flames: [], t: 0, glb: true, clip: 'idle', act: null };
    inst.mixer = new THREE.AnimationMixer(glb); inst.clips = Object.fromEntries((glb.animations || []).map((c) => [c.name, c]));
    look.lookMech(inst, glb, '#ffffff', kit.AUTHORED[id].scene);
    let last = performance.now();
    const tick = () => { const n = performance.now(), dt = Math.min(0.1, (n - last) / 1000); last = n; inst.t += dt; inst.mixer.update(window.__run ? dt : 0); look.lookTick(inst, {}, dt); requestAnimationFrame(tick); };
    tick();
    window.__show = (clip, t, lift, run) => {
      inst.mixer.stopAllAction(); const act = inst.mixer.clipAction(inst.clips[clip]); act.reset(); act.setLoop(THREE.LoopOnce, 1); act.clampWhenFinished = true; act.play();
      act.time = Math.max(0, t); inst.mixer.update(0); inst.act = act; inst.clip = clip; window.__run = !!run;
      root.position.y = P[1] + (lift || 0);
    };
    G.scene.onBeforeRender = (r, sc, cam) => { const c = window.__cam; if (!c) return; cam.position.fromArray(c.e); cam.lookAt(c.t[0], c.t[1], c.t[2]); if (c.fov && cam.fov !== c.fov) { cam.fov = c.fov; cam.updateProjectionMatrix(); } cam.updateMatrixWorld(); };
    return { clips: Object.keys(inst.clips).length, marks: Object.keys(att).length, glows: inst.look.glows.length, ink: inst.look.outline.length, mats: inst.look.mats.length, events: Object.keys(inst.look.events).length, slots: inst.look.slots.length };
  }, [hero, P]);
  if (info.err) { console.log(info.err); await b.close(); process.exit(1); }
  await sleep(4000); // (shaders compile on first sight: software GL is slow)
  const shots = [];
  for (const [name, cap, clip, t, e, tg, fov, lift = 0, run = false] of SHOTS[hero]) {
    await pg.evaluate(([clip, t, lift, run, cam]) => { window.__show(clip, t, lift, run); window.__cam = cam; }, [clip, t, lift, run, { e: [P[0] + e[0], P[1] + e[1], P[2] + e[2]], t: [P[0] + tg[0], P[1] + tg[1] + lift, P[2] + tg[2]], fov }]);
    await sleep(run ? 700 : 2200);
    if (run) await pg.evaluate(() => { window.__run = false; });
    const f = path.join(outDir, `${hero}_${PR}_${name}.jpg`); await pg.screenshot({ path: f, type: 'jpeg', quality: 88 }); shots.push([f, cap]);
  }
  await b.close();
  const n = shots.length, cols = Math.ceil(n / 2), args = [];
  for (const [f] of shots) args.push('-i', f);
  const lab = shots.map(([, c], i) => `[${i}:v]scale=640:360,drawtext=text='${c.replace(/[':,]/g, ' ')}':x=10:y=330:fontsize=18:fontcolor=0xffe14d:box=1:boxcolor=0x120818@0.85:boxborderw=6[v${i}]`).join(';');
  const pad = n % 2 ? ';color=c=0x120818:s=640x360:d=1[vpad]' : '';
  const ins = shots.map((_, i) => `[v${i}]`).join('') + (n % 2 ? '[vpad]' : '');
  const lay = Array.from({ length: cols * 2 }, (_, i) => `${(i % cols) * 640}_${Math.floor(i / cols) * 360}`).join('|');
  const sheet = path.join(outDir, `${hero}_${PR}.jpg`);
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', ...args, '-filter_complex', `${lab}${pad};${ins}xstack=inputs=${cols * 2}:layout=${lay}`, '-frames:v', '1', '-q:v', '3', sheet]);
  console.log(sheet, JSON.stringify(info), errs.length ? errs.slice(0, 8) : '(0 page errors)');
  process.exit(errs.length ? 1 : 0);
})();
