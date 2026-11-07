// the cast in the game's renderer: code puppet vs Blender model, front / 3-4 / side / back + face close-ups (neutral,
// grin, shock), with the real face rig and a pose. node tools/blender/cast/castshots.cjs <port> <out.png> <id>[,<id>...]
const { chromium } = require('playwright');
const [PORT = 3000, OUT = 'cast.png', IDS = 'lumps'] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1600, height: 900 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.goto(`http://localhost:${PORT}/`); await pg.waitForTimeout(800);
  const info = await pg.evaluate(async (ids) => {
    const THREE = await import('three');
    const { jankUniforms } = await import('/js/jank.js'); jankUniforms.uSnap.value.set(4000, 3000);
    const looks = await import('/js/story/looks.js');
    const { CLIPS } = await import('/js/story/actors.js');
    const r = new THREE.WebGLRenderer({ antialias: true }); r.setSize(1600, 900); r.setPixelRatio(1); r.outputColorSpace = THREE.SRGBColorSpace; r.shadowMap.enabled = true;
    r.domElement.style.cssText = 'position:fixed;inset:0;z-index:99999'; document.body.append(r.domElement);
    const scene0 = () => { const sc = new THREE.Scene(); sc.background = new THREE.Color(0x2a1830);
      sc.add(new THREE.HemisphereLight(0xffe8f0, 0x402040, 1.4)); const d = new THREE.DirectionalLight(0xffd0b0, 2.4); d.position.set(-3, 6, -5); sc.add(d);
      const rim = new THREE.DirectionalLight(0xff70a0, 1.4); rim.position.set(4, 3, 5); sc.add(rim);
      const fl = new THREE.Mesh(new THREE.CircleGeometry(3, 32), new THREE.MeshStandardMaterial({ color: 0x3a2a40 })); fl.rotation.x = -Math.PI / 2; sc.add(fl); return sc; };
    const rows = [];
    const code = {}; for (const id of ids) code[id] = true;
    const got = await looks.loadCast(ids, 20000);
    r.setScissorTest(true); r.autoClear = false; r.clear();
    const cols = 6, W = 1600 / cols, Hh = 900 / (ids.length * 2);
    let row = 0;
    for (const id of ids) for (const which of ['code', 'blender']) {
      const views = [[Math.PI, 'full'], [Math.PI + 0.7, 'full'], [Math.PI / 2, 'full'], [0, 'full'], [Math.PI + 0.35, 'face:neutral'], [Math.PI + 0.35, 'face:grin']];
      views.forEach(([yaw, kind], ci) => {
        const L = which === 'code' ? (() => { const save = looks.castLoaded(id); return looks.buildLookCode ? looks.buildLookCode(id) : null; })() || null : looks.buildLook(id);
        if (!L) return;
        const sc = scene0(); sc.add(L.ch.root); L.ch.root.rotation.y = yaw;
        L.ch.arm.rotation.z = 0.1; L.ch.armL.rotation.z = -0.1; L.ch.foreR.rotation.x = 0.25; L.ch.foreL.rotation.x = 0.25;
        const f = kind.split(':')[1] || 'neutral'; L.face.set(f); for (let i = 0; i < 30; i++) { L.face.blinkT = 9; L.face.update(0.05); }
        L.ch.root.updateMatrixWorld(true);
        const box = new THREE.Box3().setFromObject(L.ch.root), c = box.getCenter(new THREE.Vector3()), sz = box.getSize(new THREE.Vector3());
        const cam = new THREE.PerspectiveCamera(30, W / Hh, 0.05, 100);
        if (kind === 'full') { cam.position.set(c.x, c.y + sz.y * 0.05, c.z + sz.y * 2.1); cam.lookAt(c); }
        else { const hp = new THREE.Vector3(); L.ch.head.getWorldPosition(hp); const hb = new THREE.Box3().setFromObject(L.ch.head); const hc = hb.getCenter(new THREE.Vector3()); const hs = hb.getSize(new THREE.Vector3()).length(); cam.position.set(hc.x + hs * 0.6, hc.y + hs * 0.1, hc.z + hs * 1.6); cam.lookAt(hc); }
        const y0 = 900 - (row + 1) * Hh;
        r.setViewport(ci * W, y0, W, Hh); r.setScissor(ci * W, y0, W, Hh); r.clear(); r.render(sc, cam);
      });
      rows.push(id + ':' + which); row++;
    }
    return { got, rows };
  }, IDS.split(','));
  await pg.waitForTimeout(300); await pg.screenshot({ path: OUT });
  console.log(JSON.stringify(info), errs.join('\n') || 'no errors'); await b.close();
})();
