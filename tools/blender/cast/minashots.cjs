// Mina in the game's renderer, driven by the real actor code (actors.js: her stance, talk and the 'late' clip, the face
// rig, loco), stepped at a fixed 30 fps so a slow software GL still gives smooth frames.
//   node tools/blender/cast/minashots.cjs <port> <outdir> [stills|clip|both]
// stills: <outdir>/mina_*.png (the wall at the Gut's colours, her face up close, her hands, the whole of her)
// clip:   <outdir>/clip/f_0000.jpg ... (idle 5 s, talking 4 s, "you're late" 3.5 s) -> ffmpeg makes the mp4
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [PORT = 3000, OUT = 'mina_shots', MODE = 'both'] = process.argv.slice(2);
(async () => {
  fs.mkdirSync(path.join(OUT, 'clip'), { recursive: true });
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.goto(`http://localhost:${PORT}/`); await pg.waitForTimeout(800);
  await pg.evaluate(async () => {
    const THREE = await import('three');
    const { jankUniforms } = await import('/js/jank.js'); jankUniforms.uSnap.value.set(4000, 3000);
    const looks = await import('/js/story/looks.js'); await looks.loadCast(['mina', 'mina_wall'], 20000);
    const A = await import('/js/story/actors.js'); const { G } = await import('/js/ctx.js');
    const r = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true }); r.setSize(1280, 720); r.setPixelRatio(1); r.outputColorSpace = THREE.SRGBColorSpace; r.shadowMap.enabled = true;
    r.domElement.style.cssText = 'position:fixed;inset:0;z-index:99999'; document.body.append(r.domElement);
    const sc = new THREE.Scene(); sc.background = new THREE.Color(0x3a0e1a); sc.fog = new THREE.Fog(0x5a1426, 6, 16);
    sc.add(new THREE.HemisphereLight(0xffd8e0, 0x501020, 1.3));
    const key = new THREE.DirectionalLight(0xffe0c8, 2.2); key.position.set(-2.5, 4, -4); key.castShadow = true; key.shadow.mapSize.set(1024, 1024); sc.add(key);
    const rim = new THREE.DirectionalLight(0xff6f91, 1.6); rim.position.set(3, 2.5, 3); sc.add(rim);
    const lamp = new THREE.PointLight(0xff6f91, 6, 8); lamp.position.set(0, 3.2, -2.5); sc.add(lamp); // (the wall's sick pink lamp, act1set.js)
    // the Gut's floor and the skin slabs' face behind her (her back is to it, 0.16 m behind her root: cast_slice.js)
    const fl = new THREE.Mesh(new THREE.PlaneGeometry(30, 30), new THREE.MeshStandardMaterial({ color: 0x7a1a2c, roughness: 0.5 })); fl.rotation.x = -Math.PI / 2; fl.receiveShadow = true; sc.add(fl);
    const wall = new THREE.Group(); sc.add(wall);
    for (const [x0, x1, h, c] of [[-3.5, -0.37, 3.4, 0xa82430], [-0.13, 3.1, 3.2, 0x8e1622], [3.1, 6, 4, 0xc23a40], [-6, -3.5, 4, 0x7a121c]]) { const m = new THREE.Mesh(new THREE.BoxGeometry(x1 - x0, h, 0.24), new THREE.MeshStandardMaterial({ color: c, roughness: 0.45 })); m.position.set((x0 + x1) / 2, h / 2, 0.28); m.receiveShadow = true; wall.add(m); }
    const fac = new THREE.Mesh(new THREE.PlaneGeometry(14, 6), new THREE.MeshStandardMaterial({ color: 0xd8b8b0, roughness: 0.8 })); fac.position.set(0, 3, 0.42); fac.rotation.y = Math.PI; wall.add(fac); // (the office block's face)
    window.__M = { THREE, A, r, sc, wall, fl, looks, G }; // (G.scene is only pointed at ours while she's added: the menu behind rebuilds its own)
  });
  const setup = (look, at, face, wallOn) => pg.evaluate(([look, at, face, wallOn]) => {
    const { A, wall, G, sc } = window.__M, g0 = G.scene; G.scene = sc; A.clearActors(); wall.visible = wallOn;
    const a = A.spawnActor('mina', { look, voice: { kind: 'chirp', pitch: 1.1 }, idle: 'idle', hint: null }, at, face); G.scene = g0;
    a.pos[1] = 0; a.home.p = a.pos.slice(); window.__a = a; window.__t = 0;
    return { look: a.L.look, blender: !!a.L.blender };
  }, [look, at, face, wallOn]);
  // step the world n frames at 30 fps: talk = blips into her voice like the talk UI's typewriter
  const step = (n, o = {}) => pg.evaluate(([n, o]) => {
    const { A } = window.__M, a = window.__a;
    for (let i = 0; i < n; i++) {
      window.__t += 1 / 30;
      if (o.talk) { a.talking = true; const s = "i'm seventy. you're twenty-two and made of plastic. we'll call it even."; const k = Math.floor(window.__t * 22) % s.length; if (k !== window.__k) { window.__k = k; a.voice.blip(s[k], k, s); } } else a.talking = false;
      A.updateActors(1 / 30, window.__t * 1000, o.eye || null);
    }
  }, [n, o]);
  const shoot = (cam, look, file, fov = 35) => pg.evaluate(([cam, look, fov]) => {
    const { THREE, r, sc } = window.__M;
    const c = new THREE.PerspectiveCamera(fov, 1280 / 720, 0.03, 60); c.position.set(...cam); c.lookAt(new THREE.Vector3(...look));
    r.render(sc, c); return r.domElement.toDataURL('image/jpeg', 0.92);
  }, [cam, look, fov]).then((d) => fs.writeFileSync(file, Buffer.from(d.split(',')[1], 'base64')));
  if (MODE !== 'clip') {
    console.log('wall', JSON.stringify(await setup('mina_wall', [0, 0, 0], 0, true)));
    const eye = [0.4, 1.45, -2.2];
    await step(40, { eye });
    await shoot([0.55, 1.55, -2.6], [0, 1.05, 0], path.join(OUT, 'mina_wall_front.png'));
    await shoot([1.8, 1.35, -1.9], [0, 0.85, 0], path.join(OUT, 'mina_wall_34.png'));
    await shoot([0.18, 1.52, -0.75], [0, 1.43, -0.08], path.join(OUT, 'mina_face.png'), 30);
    await shoot([-0.45, 1.5, -0.62], [0, 1.43, -0.06], path.join(OUT, 'mina_face_34.png'), 30);
    await shoot([0.2, 1.38, -0.75], [0, 1.0, -0.3], path.join(OUT, 'mina_hands.png'), 30);
    console.log('full', JSON.stringify(await setup('mina', [0, 0, 2.5], 0, false)));
    await step(40, { eye: [0.4, 1.5, -1.5] });
    await shoot([0.7, 1.15, -1.6], [0, 0.85, 2.5], path.join(OUT, 'mina_full_front.png'));
    await pg.evaluate(() => { window.__a.yaw = 2.4; window.__a.home.face = 2.4; });
    await step(30);
    await shoot([0.7, 1.15, -1.6], [0, 0.85, 2.5], path.join(OUT, 'mina_full_back.png'));
  }
  if (MODE !== 'stills') {
    await setup('mina_wall', [0, 0, 0], 0, true);
    const eye = [0.35, 1.45, -2.0];
    await step(10, { eye });
    let f = 0;
    const frame = async (n, o, cam) => { for (let i = 0; i < n; i++) { await step(1, o); await shoot(cam, [0, 1.12, 0], path.join(OUT, 'clip', `f_${String(f++).padStart(4, '0')}.jpg`), 30); } };
    const cam = [0.45, 1.5, -2.1];
    await frame(150, { eye: null }, cam); // idle: no one near (her look round, the breathing)
    await frame(120, { eye, talk: true }, cam); // talking to you
    await pg.evaluate(() => { const { A } = window.__M; window.__a.talking = false; A.play(window.__a, 'late'); });
    await frame(105, { eye }, cam); // "you're late."
    console.log('frames', f);
  }
  console.log(errs.join('\n') || 'no errors'); await b.close();
})();
