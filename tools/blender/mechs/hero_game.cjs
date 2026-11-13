// A Battle Island hero's file (public/models/x_mech_<hero>.glb) in the real game before its gameplay code exists:
// Training range, the game's lights, sky and renderer at a preset, loaded through the game's own glb pipeline
// (glbkit) with the hero kit on it (public/js/mechlook.js: rim light, ink, glows, stickers), posed by its own clips.
// usage: node tools/blender/mechs/hero_game.cjs <port> <outDir> <hero> [preset=3] [set=shots|turn|lod] [tag]
//   (start a server after the glb is in public/models: it lists the models when it boots)
//   writes <hero>_<preset><tag>_<shot>.jpg and <hero>_<preset><tag>.jpg (all of them on one sheet)
//   set turn: a turnaround (8 angles, idle); set lod: the near model over its far LOD at 8, 16 and 30 m;
//   set burst: the game's mechBurst on it (destroyed: the debris), at 0.15, 0.5 and 1.1 s
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const { execFileSync } = require('child_process');
const [port = '3100', outDir = '.', hero = 'wrecking', presetArg = '3', SET = 'shots', TAG = ''] = process.argv.slice(2);
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
  vending: [
    ['hero', 'held after its landing: ta-da, door flung open, a can on offer', 'hero_intro', 1.7, [-4.0, 1.7, 7.0], [0.0, 2.8, 0], 50],
    ['close', 'close up: the face, coin-slot mouth, keypad chin, the drinks', 'idle', 0.0, [-2.2, 3.7, 3.4], [-0.3, 3.3, 0], 50],
    ['dispense', 'dispense: the door swings, a cola pops out of the flap', 'dispense', 0.3, [-3.6, 2.0, 6.4], [0, 2.2, 0], 50, 0, true],
    ['order', 'OUT OF ORDER: slammed into the floor in front of it', 'out_of_order', 0.5, [-6.0, 2.6, 8.6], [0, 1.6, 1.4], 52, 0, true],
    ['restock', 'RESTOCK: everything flung open and lit', 'restock', 0.6, [-4.4, 2.6, 7.6], [0, 3.0, 0], 50],
    ['walk', 'the waddle (side)', 'walk', 0.0, [6.8, 2.4, 1.6], [0, 2.4, 0], 50],
    ['side', 'detail: skins bolted on the chassis, the shoulder mount, the vent, the arm ram', 'idle', 0.0, [3.4, 2.7, 1.2], [0.2, 2.3, 0], 50],
    ['back', 'detail: the sign on its back, the coiled power cord, the compressor vent', 'idle', 0.0, [-2.0, 2.4, -4.8], [0, 2.1, 0], 50],
    ['legs', 'detail: rams behind the knees, greaves, treads, levelling feet', 'idle', 0.0, [-1.9, 0.9, 2.7], [0, 0.6, 0], 50],
    ['far', 'from the firing line, 30 m: the silhouette', 'idle', 0.0, [0, 1.75, 30], [0, 2.6, 0], 75],
  ],
};

const TALL = { wrecking: 2.4, trolley: 1.2 }[hero] || 2.6; // (where to look: about the middle of it)
const turn = () => Array.from({ length: 8 }, (_, i) => { const a = i * Math.PI / 4, r = TALL * 3.6; return [`turn${i}`, `${i * 45} degrees`, 'idle', 0.0, [Math.sin(a) * r, TALL * 0.95, Math.cos(a) * r], [0, TALL * 0.92, 0], 50]; });
const lod = () => [8, 16, 30].flatMap((d) => [false, true].map((f) => [`${f ? 'far' : 'near'}${d}`, `${f ? 'far LOD' : 'near model'} at ${d} m`, 'idle', 0.0, [-d * 0.42, TALL * 0.8, d * 0.91], [0, TALL * 0.85, 0], 40, 0, false, f]))
  .sort((a, b) => (a[9] - b[9]));
const burst = () => [0.15, 0.5, 1.1].map((t) => [`burst${t}`, `destroyed: mechBurst, ${t} s`, 'idle', 0.0, [-7.5, TALL * 1.2, 9.5], [0, TALL * 0.7, 0], 55, 0, false, null, t]);
const LIST = SET === 'turn' ? turn() : SET === 'lod' ? lod() : SET === 'burst' ? burst() : SHOTS[hero];
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } }), errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + (e.stack || e.message).split('\n').slice(0, 3).join(' | ')));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text().slice(0, 200)); });
  await pg.addInitScript((pr) => { localStorage.setItem('jf_giftseen_all', '1'); localStorage.setItem('jankfire', JSON.stringify({ name: 'SHOTS', killcam: false, jank: pr })); }, PR);
  await pg.goto(`http://localhost:${port}/`); await sleep(2500);
  await pg.click('#scr-main [data-mode="training"]', { timeout: 180000 });
  const info = await pg.evaluate(async ([H, P, SPRAY]) => {
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
    const SKU = await import('three/addons/utils/SkeletonUtils.js'); let glb = a.obj; let skn = false; glb.traverse((o) => { if (o.isSkinnedMesh) skn = true; });
    if (skn) glb = SKU.clone(kit.AUTHORED[id].scene); // (a skinned hero: its bones cloned with it, like buildMech does)
    const meta = a.meta || kit.metaOf(glb) || {}, root = new THREE.Group();
    root.add(glb); root.position.set(P[0], P[1], P[2]); root.rotation.y = Math.PI; G.scene.add(root);
    const j = {}, att = {};
    glb.traverse((o) => { if (meta.joints && Object.hasOwn(meta.joints, o.name)) j[o.name] = o; if (/^mk_/.test(o.name)) att[o.name] = o; });
    const inst = { frame: H, root, j, att, own: {}, flames: [], t: 0, glb: true, clip: 'idle', act: null };
    inst.mixer = new THREE.AnimationMixer(glb); inst.clips = Object.fromEntries((glb.animations || []).map((c) => [c.name, c]));
    look.lookMech(inst, glb, '#ffffff', kit.AUTHORED[id].scene);
    if (SPRAY) { // (JF_SPRAY=1: a test spray on each decal slot, to see it lands)
      const cv = document.createElement('canvas'); cv.width = cv.height = 256; const c = cv.getContext('2d');
      c.fillStyle = '#39ff14'; c.beginPath(); c.arc(128, 128, 110, 0, 7); c.fill(); c.fillStyle = '#120818'; c.font = 'bold 64px sans-serif'; c.textAlign = 'center'; c.fillText('SPRAY', 128, 150);
      const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace;
      for (let k = 0; k < (inst.look.slots || []).length; k++) look.sprayOnMech(inst, k, tex);
    }
    let last = performance.now();
    const tick = () => { const n = performance.now(), dt = Math.min(0.1, (n - last) / 1000); last = n; inst.t += dt; inst.mixer.update(window.__run ? dt : 0); look.lookTick(inst, {}, dt); requestAnimationFrame(tick); };
    tick();
    const mm = await import('/js/mechmodel.js'); window.__burst = () => { inst.root.visible = true; mm.mechBurst(inst, [0, 0, 0]); };
    window.__show = (clip, t, lift, run, force) => {
      if (inst.look) inst.look.lodForce = force == null ? null : !!force;
      inst.mixer.stopAllAction(); const act = inst.mixer.clipAction(inst.clips[clip]); act.reset(); act.setLoop(THREE.LoopOnce, 1); act.clampWhenFinished = true; act.play();
      act.time = Math.max(0, t); inst.mixer.update(0); inst.act = act; inst.clip = clip; window.__run = !!run;
      root.position.y = P[1] + (lift || 0);
    };
    G.scene.onBeforeRender = (r, sc, cam) => { const c = window.__cam; if (!c) return; cam.position.fromArray(c.e); cam.lookAt(c.t[0], c.t[1], c.t[2]); if (c.fov && cam.fov !== c.fov) { cam.fov = c.fov; cam.updateProjectionMatrix(); } cam.updateMatrixWorld(); };
    return { clips: Object.keys(inst.clips).length, marks: Object.keys(att).length, glows: inst.look.glows.length, ink: inst.look.outline.length, mats: inst.look.mats.length, events: Object.keys(inst.look.events).length, slots: inst.look.slots.length, sprays: inst.look.sprays.length };
  }, [hero, P, !!process.env.JF_SPRAY]);
  if (info.err) { console.log(info.err); await b.close(); process.exit(1); }
  await sleep(4000); // (shaders compile on first sight: software GL is slow)
  const shots = [];
  let burstAt = 0;
  for (const [name, cap, clip, t, e, tg, fov, lift = 0, run = false, force = null, bt = null] of LIST) {
    await pg.evaluate(([clip, t, lift, run, cam, force]) => { window.__show(clip, t, lift, run, force); window.__cam = cam; }, [clip, t, lift, run, { e: [P[0] + e[0], P[1] + e[1], P[2] + e[2]], t: [P[0] + tg[0], P[1] + tg[1] + lift, P[2] + tg[2]], fov }, force]);
    if (bt != null) { if (!burstAt) { await sleep(2200); await pg.evaluate(() => window.__burst()); burstAt = Date.now(); } await sleep(Math.max(0, bt * 1000 * 6 - (Date.now() - burstAt))); } // (software GL runs ~6x slow: game time)
    else await sleep(run ? 700 : 2200);
    if (run) await pg.evaluate(() => { window.__run = false; });
    const f = path.join(outDir, `${hero}_${PR}${TAG}_${name}.jpg`); await pg.screenshot({ path: f, type: 'jpeg', quality: 88, timeout: 180000 }); shots.push([f, cap]);
  }
  await b.close();
  const n = shots.length, cols = SET === 'turn' ? 4 : Math.ceil(n / 2), args = [];
  for (const [f] of shots) args.push('-i', f);
  const lab = shots.map(([, c], i) => `[${i}:v]scale=640:360,drawtext=text='${c.replace(/[':,]/g, ' ')}':x=10:y=330:fontsize=18:fontcolor=0xffe14d:box=1:boxcolor=0x120818@0.85:boxborderw=6[v${i}]`).join(';');
  const pad = n % 2 ? ';color=c=0x120818:s=640x360:d=1[vpad]' : '';
  const ins = shots.map((_, i) => `[v${i}]`).join('') + (n % 2 ? '[vpad]' : '');
  const lay = Array.from({ length: cols * 2 }, (_, i) => `${(i % cols) * 640}_${Math.floor(i / cols) * 360}`).join('|');
  const sheet = path.join(outDir, `${hero}_${PR}${TAG}${SET === 'shots' ? '' : '_' + SET}.jpg`);
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', ...args, '-filter_complex', `${lab}${pad};${ins}xstack=inputs=${cols * 2}:layout=${lay}`, '-frames:v', '1', '-q:v', '3', sheet]);
  console.log(sheet, JSON.stringify(info), errs.length ? errs.slice(0, 8) : '(0 page errors)');
  process.exit(errs.length ? 1 : 0);
})();
