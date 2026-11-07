// MR. OVERTIME's damage states in the game's renderer: fresh / plate off / cracked + sparking / heart ripped + card torn
// / the far LOD up close (what you see past 45 m) / poses. node tools/blender/cast/otstates.cjs <port> <out.png>
const { chromium } = require('playwright');
const [PORT = 3000, OUT = 'otstates.png'] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1600, height: 900 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.goto(`http://localhost:${PORT}/`); await pg.waitForTimeout(800);
  const info = await pg.evaluate(async () => {
    const THREE = await import('three');
    const { G } = await import('/js/ctx.js');
    const { jankUniforms } = await import('/js/jank.js'); jankUniforms.uSnap.value.set(4000, 3000);
    const looks = await import('/js/story/looks.js');
    const { CLIPS } = await import('/js/story/actors.js');
    const { OT } = await import('/js/story/overtime.js');
    await looks.loadCast(['overtime'], 20000);
    const r = new THREE.WebGLRenderer({ antialias: true }); r.setSize(1600, 900); r.setPixelRatio(1); r.outputColorSpace = THREE.SRGBColorSpace;
    r.domElement.style.cssText = 'position:fixed;inset:0;z-index:99999'; document.body.append(r.domElement);
    r.setScissorTest(true); r.autoClear = false; r.clear();
    // [label, damage states, clip + time, view]
    const CELLS = [
      ['fresh (fight 1)', [], null, 'front'], ['plate off', ['plate_off'], null, 'front'], ['cracked + sparking', ['plate_off', 'sparking'], null, 'chest'],
      ['heart ripped, card torn', ['plate_off', 'ripped', 'card_torn'], null, 'chest'], ['far LOD (past 45 m)', ['lod'], null, 'front'], ['back: cables, stacks', [], null, 'back'],
      ['staple: FIRE', [], ['ot_staple', 0.86], 'three'], ['slam: in the air', [], ['ot_slam', 1.2], 'three'], ['slam: LAND', [], ['ot_slam', 1.5], 'three'],
      ['punch in: slot open', [], ['ot_punchin', 0.6], 'front'], ['coffee break', [], ['ot_coffee', 2.6], 'three'], ['roar (phase change)', [], ['ot_roar', 0.9], 'front'],
      ['plate ripped', ['plate_off'], ['ot_plate_rip', 1.3], 'three'], ['kneel ("rescheduled")', ['plate_off', 'ripped'], ['ot_kneel', 2], 'three'], ['clock out', ['plate_off', 'ripped'], ['ot_clockout', 4], 'side'],
    ];
    const cols = 5, rows = 3, W = 1600 / cols, H = 900 / rows;
    CELLS.forEach(([label, dmg, clip, view], i) => {
      const sc = new THREE.Scene(); sc.background = new THREE.Color(0x2a1830); G.scene = sc;
      sc.add(new THREE.HemisphereLight(0xffe8f0, 0x402040, 1.4)); const d = new THREE.DirectionalLight(0xffd0b0, 2.4); d.position.set(-3, 6, -5); sc.add(d);
      const rim = new THREE.DirectionalLight(0xff70a0, 1.4); rim.position.set(4, 3, 5); sc.add(rim);
      const fl = new THREE.Mesh(new THREE.CircleGeometry(6, 32), new THREE.MeshStandardMaterial({ color: 0x3a2a40 })); fl.rotation.x = -Math.PI / 2; sc.add(fl);
      const L = looks.buildLook('overtime'), c = L.ch; c.head.rotation.z = 0;
      const a = { id: 'sheet' + i, L, ch: c, pos: [0, 0, 0], yaw: 0, clip: null };
      sc.add(c.root);
      const rig = OT.rig(a);
      for (const s of dmg) if (s === 'lod') { rig.far = true; rig.vis(); } else rig.dmg(s);
      if (!dmg.includes('lod')) { rig.far = false; rig.vis(); }
      if (clip) { CLIPS[clip[0]].f(c, clip[1], 1); a.clip = { name: clip[0], t: clip[1], len: 9e9 }; rig.update(0, null); }
      c.root.rotation.y = view === 'back' ? 0 : view === 'side' ? Math.PI / 2 : view === 'three' ? Math.PI + 0.6 : Math.PI;
      L.face.set(clip && clip[0] === 'ot_roar' ? 'shock' : 'grin'); for (let k = 0; k < 20; k++) { L.face.blinkT = 9; L.face.update(0.05); }
      // the plate on the floor, as it falls (the rig keeps the fallen copy in its debris)
      for (const db of rig.debris) { db.m.position.set(0.9, 0.12, -1.6); db.m.rotation.set(-Math.PI / 2, 0, 0.4); }
      c.root.updateMatrixWorld(true);
      const cam = new THREE.PerspectiveCamera(30, W / H, 0.05, 200);
      if (view === 'chest') { const h = L.parts.heart || c.spine; const p = new THREE.Vector3(); (L.partsAll.heart ? L.partsAll.heart[0] : c.spine).getWorldPosition(p); const hc = new THREE.Box3().setFromObject(c.spine).getCenter(new THREE.Vector3()); cam.position.set(1.0, 3.6, 3.4); cam.lookAt(0, 3.3, 0); }
      else { cam.position.set(view === 'three' ? 2 : 0, 2.6, 10.5); cam.lookAt(0, 2.2, 0); }
      const x0 = (i % cols) * W, y0 = 900 - (Math.floor(i / cols) + 1) * H;
      r.setViewport(x0, y0, W, H); r.setScissor(x0, y0, W, H); r.clear(); r.render(sc, cam);
    });
    return CELLS.map((c) => c[0]);
  });
  // labels
  await pg.evaluate((labels) => { labels.forEach((t, i) => { const d = document.createElement('div'); d.textContent = t; d.style.cssText = `position:fixed;z-index:100000;left:${(i % 5) * 320 + 8}px;top:${Math.floor(i / 5) * 300 + 6}px;font:700 15px sans-serif;color:#ffe14d;background:rgba(18,8,24,.85);padding:2px 6px;border:2px solid #ff4fd8`; document.body.append(d); }); }, info);
  await pg.waitForTimeout(300); await pg.screenshot({ path: OUT });
  console.log(errs.join('\n') || 'no errors'); await b.close();
})();
