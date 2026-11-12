// The Gut Choir in the game's renderer, driven by the real actor code (actors.js: the stance, loco, the face rig;
// choir.js: the hum, sing and heads clips, playTogether), stepped at a fixed 30 fps so a slow software GL still gives
// smooth frames. A little studio: the lung's red flesh, the bone floor, its pink light.
//   node tools/blender/cast/choirshots.cjs <port> <outdir> [stills|clip|walk|both] [code]
// stills: <outdir>/choir_*.png (the pair front, 3/4 and back, faces and hands up close, the stalls)
// clip:   <outdir>/clip/f_0000.jpg ... (hum 5 s, sing 5 s, the heads all turning to you 5 s) -> ffmpeg makes the mp4
// walk:   <outdir>/walk/f_0000.jpg ... (a procession: loco walks them, the binders stay up)
// code:   the code puppets instead of the Blender models (for side-by-sides)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [PORT = 3000, OUT = 'choir_shots', MODE = 'both', CODE = ''] = process.argv.slice(2);
(async () => {
  for (const d of ['clip', 'walk']) fs.mkdirSync(path.join(OUT, d), { recursive: true });
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message)); pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.goto(`http://localhost:${PORT}/`); await pg.waitForTimeout(800);
  await pg.evaluate(async (code) => {
    const THREE = await import('three');
    const { jankUniforms } = await import('/js/jank.js'); jankUniforms.uSnap.value.set(4000, 3000);
    const looks = await import('/js/story/looks.js'); if (!code) await looks.loadCast(['choir', 'choir_b'], 20000);
    const A = await import('/js/story/actors.js'); const C = await import('/js/story/choir.js'); const { G } = await import('/js/ctx.js');
    const r = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true }); r.setSize(1280, 720); r.setPixelRatio(1); r.outputColorSpace = THREE.SRGBColorSpace; r.shadowMap.enabled = true;
    r.domElement.style.cssText = 'position:fixed;inset:0;z-index:99999'; document.body.append(r.domElement);
    const sc = new THREE.Scene(); sc.background = new THREE.Color(0x3a0e1a); sc.fog = new THREE.Fog(0x5a1426, 9, 26);
    sc.add(new THREE.HemisphereLight(0xffd8e0, 0x501020, 1.25));
    const key = new THREE.DirectionalLight(0xffe0c8, 2.1); key.position.set(-3, 6, -5); key.castShadow = true; key.shadow.mapSize.set(2048, 2048); for (const k of ['left', 'bottom']) key.shadow.camera[k] = -6; for (const k of ['right', 'top']) key.shadow.camera[k] = 6; sc.add(key);
    const rim = new THREE.DirectionalLight(0xff6f91, 1.5); rim.position.set(4, 3, 4); sc.add(rim);
    const fl = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), new THREE.MeshStandardMaterial({ color: 0xc4b288, roughness: 0.6 })); fl.rotation.x = -Math.PI / 2; fl.receiveShadow = true; sc.add(fl); // (the lung's bone floor)
    const back = new THREE.Mesh(new THREE.SphereGeometry(14, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xa82430, roughness: 0.4, side: THREE.BackSide })); back.position.set(0, 0, 2); sc.add(back);
    window.__M = { THREE, A, C, r, sc, looks, G, code };
  }, CODE === 'code');
  // people: [[look, [x, y, z], yaw], ...]
  const setup = (people) => pg.evaluate((people) => {
    const { A, G, sc, code, looks } = window.__M, g0 = G.scene; G.scene = sc; A.clearActors();
    const list = people.map(([look, at, face], i) => { const a = A.spawnActor('choir_' + i, { look, voice: { kind: 'choir', pitch: 1 }, idle: 'idle' }, at, face); a.pos[1] = 0; a.home.p = a.pos.slice(); return a; });
    G.scene = g0;
    for (const a of list) { a.t = 3.1; a.stepAcc = 1; a.ch.gazeAt = new window.__M.THREE.Vector3(); } // (stepAcc 1: posed on the first update, as choir.js spawns them)
    window.__L = list; window.__t = 0;
    return list.map((a) => `${a.L.look}:${a.L.blender ? 'blender' : 'code'}`);
  }, people);
  // step the world n frames at 30 fps. o.eye: where you are; o.look: 'page' (eyes on the hymns) | 'up' (singing out)
  const step = (n, o = {}) => pg.evaluate(([n, o]) => {
    const { A } = window.__M, L = window.__L, v = new window.__M.THREE.Vector3();
    for (let i = 0; i < n; i++) {
      window.__t += 1 / 30;
      for (const a of L) {
        a.ch.head.getWorldPosition(v);
        if (o.stare && o.eye) { const yaw = Math.atan2(-(o.eye[0] - v.x), -(o.eye[2] - v.z)); a.ch.turnY = Math.max(-1.75, Math.min(1.75, Math.atan2(Math.sin(yaw - a.yaw), Math.cos(yaw - a.yaw)))); a.ch.turnX = Math.max(-0.5, Math.min(0.5, Math.atan2(o.eye[1] - v.y, Math.hypot(o.eye[0] - v.x, o.eye[2] - v.z)))); a.ch.gazeAt.set(...o.eye); }
        const d = o.look === 'up' ? [2.4, 0.5] : o.look === 'ahead' ? [2, 0] : [1.6, -0.45];
        a.lookAt = [a.pos[0] - Math.sin(a.yaw) * d[0], v.y + d[1], a.pos[2] - Math.cos(a.yaw) * d[0]];
        if (o.walk) { a.pos[0] -= Math.sin(a.yaw) * o.walk / 30; a.pos[2] -= Math.cos(a.yaw) * o.walk / 30; }
      }
      A.updateActors(1 / 30, window.__t * 1000, o.eye || null);
    }
  }, [n, o]);
  const together = (name, hold) => pg.evaluate(([name, hold]) => window.__M.C.playTogether(window.__L, name, { hold }), [name, hold]);
  const shoot = (cam, look, file, fov = 35) => pg.evaluate(([cam, look, fov]) => {
    const { THREE, r, sc } = window.__M;
    const c = new THREE.PerspectiveCamera(fov, 1280 / 720, 0.03, 80); c.position.set(...cam); c.lookAt(new THREE.Vector3(...look));
    r.render(sc, c); return r.domElement.toDataURL('image/jpeg', 0.92);
  }, [cam, look, fov]).then((d) => fs.writeFileSync(file, Buffer.from(d.split(',')[1], 'base64')));
  const yawOf = (a) => pg.evaluate((y) => { for (const a of window.__L) { a.yaw = y; a.home.face = y; } }, a);

  if (MODE === 'stills' || MODE === 'both') {
    console.log('pair', JSON.stringify(await setup([['choir', [-0.7, 0, 0], 0], ['choir_b', [0.7, 0, 0], 0]])));
    await step(45, { look: 'ahead' });
    await shoot([0, 1.45, -5.6], [0, 1.05, 0], path.join(OUT, 'choir_pair_front.png'));
    await shoot([3.6, 1.6, -4.2], [0, 1.0, 0], path.join(OUT, 'choir_pair_34.png'));
    await shoot([-0.7, 2.0, -1.55], [-0.7, 1.82, 0], path.join(OUT, 'choir_face_tall.png'), 30);
    await shoot([0.7, 1.4, -1.35], [0.7, 1.22, 0], path.join(OUT, 'choir_face_squat.png'), 30);
    await shoot([-0.2, 1.55, -1.6], [-0.1, 1.15, -0.3], path.join(OUT, 'choir_hands.png'), 35);
    await shoot([-0.55, 1.2, -1.15], [-0.7, 1.12, -0.3], path.join(OUT, 'choir_binder_front.png'), 34); // (what you see of the hymns: the back of the binder, the hands under it)
    await shoot([0.75, 0.85, -1.0], [0.7, 0.8, -0.2], path.join(OUT, 'choir_clipboard_front.png'), 34);
    await shoot([-0.6, 1.05, -0.9], [-0.68, 0.92, -0.15], path.join(OUT, 'choir_badge_tall.png'), 30);
    await shoot([0.8, 0.62, -0.85], [0.72, 0.6, -0.2], path.join(OUT, 'choir_badge_squat.png'), 30);
    await shoot([0.1, 0.35, -1.5], [0.0, 0.1, 0], path.join(OUT, 'choir_shoes.png'), 34);
    await yawOf(Math.PI); await step(30, { look: 'ahead' });
    await shoot([0, 1.45, -5.6], [0, 1.05, 0], path.join(OUT, 'choir_pair_back.png'));
    await yawOf(-Math.PI / 2); await step(30, { look: 'ahead' });
    await shoot([0, 1.45, -5.6], [0, 1.05, 0], path.join(OUT, 'choir_pair_side.png'));
    // the stalls: two rows across an aisle, from the door end, then all of them turned to you
    await setup([['choir', [-2.7, 0, 0], -Math.PI / 2], ['choir_b', [-2.7, 0, -1.3], -Math.PI / 2], ['choir', [-2.7, 0, -2.6], -Math.PI / 2], ['choir_b', [2.7, 0, -0.6], Math.PI / 2], ['choir', [2.7, 0, -1.95], Math.PI / 2]]);
    await step(40, { look: 'page' });
    await shoot([0.4, 1.7, 7.5], [0, 1.2, -1.3], path.join(OUT, 'choir_stalls.png'));
    await together('sing'); await step(96, { look: 'up' });
    await shoot([0.4, 1.7, 7.5], [0, 1.2, -1.3], path.join(OUT, 'choir_stalls_sing.png'));
    await step(60, { look: 'page' });
    const eye = [0.4, 1.7, 7.5];
    await together('heads', true); await step(45, { eye, stare: true, look: 'ahead' });
    await shoot(eye, [0, 1.3, -1.3], path.join(OUT, 'choir_stalls_heads.png'));
  }
  if (MODE === 'clip' || MODE === 'both') {
    await setup([['choir', [-2.4, 0, 0], -Math.PI / 2], ['choir_b', [-2.4, 0, -1.3], -Math.PI / 2], ['choir', [-2.4, 0, -2.6], -Math.PI / 2], ['choir_b', [2.4, 0, -0.6], Math.PI / 2], ['choir', [2.4, 0, -1.95], Math.PI / 2]]);
    const eye = [0.35, 1.7, 4.2], wide = [[0.6, 1.8, 4.6], [0, 1.3, -1.3], 44], west = [[0.5, 1.85, 0.9], [-2.4, 1.55, -1.4], 40], you = [[0.35, 1.72, 4.2], [0, 1.35, -1.3], 46];
    await step(10, { look: 'page' });
    let f = 0;
    const frame = async (n, o, [cam, at, fov]) => { for (let i = 0; i < n; i++) { await step(1, o); await shoot(cam, at, path.join(OUT, 'clip', `f_${String(f++).padStart(4, '0')}.jpg`), fov); } };
    await frame(135, { look: 'page' }, wide); // the hum: everyone swaying together, eyes on the hymns
    await together('sing'); await frame(150, { look: 'up' }, west); // a phrase, together: a breath, the words, the big note
    await frame(15, { look: 'page' }, wide);
    await together('heads', true); await frame(120, { eye, stare: true, look: 'ahead' }, you); // you walk in: every head, at once
    await pg.evaluate(() => window.__M.C.releaseTogether(window.__L, 'heads')); await frame(45, { look: 'page' }, you); // and back to the hymn, all together
    console.log('frames', f);
  }
  if (MODE === 'walk') {
    await setup([['choir', [-0.5, 0, 2], Math.PI], ['choir_b', [0.6, 0, 1], Math.PI]]);
    let f = 0;
    for (let i = 0; i < 120; i++) { await step(1, { walk: 1.3, look: 'page' }); await pg.evaluate(() => { for (const a of window.__L) a.home.p = a.pos.slice(); }); const z = 2 + (i / 30) * 1.3; await shoot([3.2, 1.4, z + 0.5], [0, 0.9, z - 0.6], path.join(OUT, 'walk', `f_${String(f++).padStart(4, '0')}.jpg`), 40); }
    console.log('walk frames', f);
  }
  console.log(errs.join('\n') || 'no errors'); await b.close();
})();
