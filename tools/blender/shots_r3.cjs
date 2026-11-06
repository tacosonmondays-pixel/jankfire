// Round 3 side by side: the gear, the wrecking ball and the Overdrive Rig, each as OLD (code model) | BLENDER | IN USE,
// in a studio with the game's lights and render preset. Writes <outDir>/<preset>_<item>.png (the rig: two strips).
// usage: node tools/blender/shots_r3.cjs <port> <outDir> [items=camera,frame,calc,nvg,wand,wreck,rig,arms,missile] [presets=3,0]
//   (start the server first: PORT=<port> node server.js). prints which ones are Blender and any page errors
const { chromium } = require('playwright');
const [port = '3100', out = '.', list = 'camera,frame,calc,nvg,wand,wreck,rig,arms,missile', presets = '3,0'] = process.argv.slice(2);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const FILES = { camera: ['x_camera'], frame: ['x_photoframe'], calc: ['x_calc'], nvg: ['x_nvg'], wand: ['x_wand'], wreck: ['x_wreck'], rig: ['x_rig'], arms: ['x_rigarms'], missile: ['pj_rigmissile'] };

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  let bad = 0;
  for (const jank of presets.split(',').map(Number)) {
    const tag = ['potato', 'crusty', 'mid', 'toohd'][jank];
    const pg = await b.newPage({ viewport: { width: 960, height: 600 } });
    const errs = [];
    pg.on('pageerror', (e) => errs.push('PAGEERR ' + (e.stack || e.message).split('\n').slice(0, 3).join(' | ')));
    pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await pg.addInitScript((jank) => localStorage.setItem('jankfire', JSON.stringify({ name: 'shots', killcam: false, jank })), jank);
    await pg.goto(`http://localhost:${port}/`); await sleep(2500);
    const items = list.split(',');
    const res = await pg.evaluate(async ([items, FILES, jank]) => {
      const THREE = await import('three');
      const k = await import('/js/glbkit.js');
      for (let i = 0; i < 150 && !Object.keys(k.AUTHORED).length; i++) await new Promise((r) => setTimeout(r, 100)); // the base set
      k.prefetch(items.flatMap((it) => FILES[it] || []));
      for (let i = 0; i < 300 && k.lateBusy(); i++) await new Promise((r) => setTimeout(r, 100));
      const gm = await import('/js/gearmodels.js'), wr = await import('/js/wreck.js'), wa = await import('/js/wand.js');
      const rm = await import('/js/rigmodel.js'), mo = await import('/js/models.js');
      const W = 480, H = 360, sc = [0.22, 0.36, 0.6, 1][jank];
      const r = new THREE.WebGLRenderer({ antialias: jank === 3, preserveDrawingBuffer: true }); r.setSize(Math.floor(W * sc), Math.floor(H * sc), false);
      r.setClearColor(0x3a3048);
      const scene = new THREE.Scene();
      scene.add(new THREE.HemisphereLight(0xcfe8ff, 0x7a4a6a, 1.8));
      const sun = new THREE.DirectionalLight(0xffffff, 1.5); sun.position.set(2, 3, 4); scene.add(sun);
      const cam = new THREE.PerspectiveCamera(30, W / H, 0.01, 200);
      const box = new THREE.Box3(), ctr = new THREE.Vector3(), sz = new THREE.Vector3();
      // one panel: frame the thing from a direction (yaw, pitch), draw it, label it
      const panel = (obj, label, view = [0.6, 0.25], fill = 0.75, frame = null) => {
        scene.add(obj); obj.updateMatrixWorld(true);
        box.setFromObject(obj); box.getCenter(ctr); box.getSize(sz);
        if (frame) { ctr.fromArray(frame.c); sz.setScalar(frame.r * 2 / Math.sqrt(3)); } // (the rig: sprites + hoses make its box lie)
        const rad = Math.max(0.05, sz.length() / 2), d = rad / Math.sin((cam.fov * Math.PI) / 360) / fill;
        const [yw, pt] = view;
        cam.position.set(ctr.x + Math.sin(yw) * Math.cos(pt) * d, ctr.y + Math.sin(pt) * d, ctr.z - Math.cos(yw) * Math.cos(pt) * d);
        cam.near = d / 50; cam.far = d * 10; cam.updateProjectionMatrix(); cam.lookAt(ctr);
        k.withEnv(r, scene, () => { r.render(scene, cam); r.render(scene, cam); }); // (twice: the missile turns itself on the first)
        const c = document.createElement('canvas'); c.width = W; c.height = H;
        const x = c.getContext('2d'); x.imageSmoothingEnabled = jank === 3; x.drawImage(r.domElement, 0, 0, W, H);
        x.font = 'bold 20px sans-serif'; const tw = x.measureText(label).width; x.fillStyle = 'rgba(0,0,0,0.6)'; x.fillRect(6, 6, tw + 14, 30);
        x.fillStyle = label.startsWith('OLD') ? '#ffffff' : '#ffe14d'; x.fillText(label, 13, 28);
        scene.remove(obj);
        return c;
      };
      const strip = (cs) => { // panels side by side, a dark rule between them
        const c = document.createElement('canvas'); c.width = cs.reduce((n, p) => n + p.width, 0); c.height = H; const x = c.getContext('2d');
        let at = 0; cs.forEach((p, i) => { x.drawImage(p, at, 0); if (i) { x.fillStyle = '#120818'; x.fillRect(at - 2, 0, 4, H); } at += p.width; }); return c.toDataURL('image/png');
      };
      const code = (ids, fn) => { const keep = ids.map((id) => k.AUTHORED[id]); ids.forEach((id) => delete k.AUTHORED[id]); try { return fn(); } finally { ids.forEach((id, i) => { if (keep[i]) k.AUTHORED[id] = keep[i]; }); } };
      const testTex = () => { // a stand-in photo: sky, a sun, a mannequin, the date stamp
        const c = document.createElement('canvas'); c.width = c.height = 128; const x = c.getContext('2d');
        const g = x.createLinearGradient(0, 0, 0, 128); g.addColorStop(0, '#6fc8ff'); g.addColorStop(1, '#ff9ad5'); x.fillStyle = g; x.fillRect(0, 0, 128, 128);
        x.fillStyle = '#ffe14d'; x.beginPath(); x.arc(96, 30, 14, 0, 7); x.fill(); x.fillStyle = '#39ff14'; x.fillRect(0, 96, 128, 32);
        x.fillStyle = '#e6cba2'; x.fillRect(52, 50, 24, 46); x.beginPath(); x.arc(64, 42, 12, 0, 7); x.fill();
        x.fillStyle = '#ff8a2a'; x.font = 'bold 12px monospace'; x.fillText("'26 11 06", 60, 122);
        const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
      };
      const isBl = (g) => g.userData.glb === 'blender';
      const outp = {}, info = [];
      const pose = (inst, s, n = 90) => { for (let i = 0; i < n; i++) rm.poseRig(inst, { spd: 0, on: 1, ...s }, 1 / 60); inst.root.updateMatrixWorld(true); };
      // views are [yaw, pitch]: yaw 0 = in front (everything faces -z), + = round to its left side as you face it
      for (const it of items) {
        try {
          if (it === 'camera') {
            const a = code(['x_camera'], () => gm.instantCamera()), b = gm.instantCamera(), u = gm.instantCamera();
            u.userData.print.visible = true; u.userData.print.position.set(0, -0.04, -0.105);
            u.userData.pic.material.map = testTex(); u.userData.pic.material.color.setRGB(1, 1, 1); u.userData.pic.material.needsUpdate = true;
            u.userData.flash.material.color.setHex(0xffffff);
            const v = [-0.6, 0.25];
            outp.camera = strip([panel(a, 'OLD (code)', v), panel(b, 'BLENDER', v), panel(u, 'IN USE: FLASH + PRINT', [-0.45, 0.5])]);
            info.push('camera ' + (isBl(b) ? 'blender' : 'code'));
          } else if (it === 'frame') {
            const a = code(['x_photoframe'], () => gm.photoFrame(null)), b = gm.photoFrame(null), u = gm.photoFrame(testTex());
            u.userData.pm.uniforms.uDev.value = 1; u.userData.pm.uniforms.uT.value = 3;
            outp.frame = strip([panel(a, 'OLD (code)', [0.45, 0.12], 0.9), panel(b, 'BLENDER', [0.45, 0.12], 0.9), panel(u, 'IN USE: THE PORTAL', [0.2, 0.1], 0.9)]);
            info.push('frame ' + (isBl(b) ? 'blender' : 'code'));
          } else if (it === 'calc') {
            const a = code(['x_calc'], () => gm.calculator()), b = gm.calculator(), u = gm.calculator(gm.lcdTexture(['6 x 7 = ?', 'POP QUIZ']));
            u.scale.setScalar(4.6);
            const v = [0.5, 0.15];
            outp.calc = strip([panel(a, 'OLD (code)', v), panel(b, 'BLENDER', v), panel(u, 'IN USE: THE GIANT ONE', [0.15, 0.05], 0.85)]);
            info.push('calc ' + (isBl(b) ? 'blender' : 'code'));
          } else if (it === 'nvg') {
            const a = code(['x_nvg'], () => gm.nvGoggles()), b = gm.nvGoggles();
            const ch = mo.buildCharacter('#4fd8ff', null), g = gm.nvGoggles({ strap: true, big: 1.9 });
            g.position.set(0, 0.16, -0.13); ch.head.add(g); g.userData.pivot.rotation.x = 0;
            for (const l of g.userData.lenses) l.color.setHex(0x39ff14);
            const head = new THREE.Group(), hc = ch.head.clone(true); hc.position.set(0, 0, 0); hc.rotation.set(0, 0, 0); head.add(hc);
            const v = [0.7, 0.2];
            outp.nvg = strip([panel(a, 'OLD (code)', v), panel(b, 'BLENDER', v), panel(head, 'IN USE: ON A HEAD', [0.65, 0.15], 0.7)]);
            info.push('nvg ' + (isBl(b) ? 'blender' : 'code'));
          } else if (it === 'wand') {
            const a = code(['x_wand'], () => wa.wandMesh()), b = wa.wandMesh(), u = wa.wandMesh();
            u.userData.film.scale.z = 0.03; u.rotation.set(0.1, 0.35, -0.2);
            const v = [0.35, 0.15];
            outp.wand = strip([panel(a, 'OLD (code)', v), panel(b, 'BLENDER', v), panel(u, 'IN USE: BLOWING', [0.3, 0.15])]);
            info.push('wand ' + (isBl(b) ? 'blender' : 'code'));
          } else if (it === 'wreck') {
            const look = { skin: '#e6cba2' };
            const a = code(['x_wreck'], () => wr.buildWreckBall('#ff4fd8', look)), b = wr.buildWreckBall('#ff4fd8', look), u = wr.buildWreckBall('#4fd8ff', { skin: '#8a5a3a', face: 'shades' });
            for (const p of u.userData.pupils) p.position.x = p.userData.x + 0.025;
            const grp = new THREE.Group(); grp.add(u);
            const ch = new wr.Chain(grp), hk = u.userData.hook; ch.set([hk.x, hk.y, hk.z], [hk.x + 0.4, hk.y + 3, hk.z + 0.6], 0.15);
            const v = [0.5, 0.22];
            outp.wreck = strip([panel(a, 'OLD (code)', v), panel(b, 'BLENDER', v), panel(grp, 'IN USE: ON ITS CHAIN', [0.55, 0.12], 0.85)]);
            info.push('wreck ' + (isBl(b) ? 'blender' : 'code'));
          } else if (it === 'rig') {
            rm.rigReset();
            const a = code(['x_rig'], () => rm.buildRig('#ff4fd8', { outline: false }));
            rm.rigReset();
            const mk = () => rm.buildRig('#ff4fd8', { outline: false });
            const b = mk(), bl = rm.rigIsBlender(), pu = mk(), bk = mk(), lp = mk(), as = mk();
            pose(a, {}); pose(b, {}); pose(pu, { punchT: 0.12, missT: 0.6 }); pose(bk, { block: true }); pose(lp, { leap: 1 }); pose(as, { on: 0.45 }, 30);
            const v = [0.6, 0.18], F = { c: [0, 1.38, 0], r: 1.55 };
            outp.rig = strip([panel(a.root, 'OLD (code)', v, 0.9, F), panel(b.root, 'BLENDER', v, 0.9, F), panel(pu.root, 'PUNCH + MISSILE PODS', [0.75, 0.15], 0.9, F)]);
            outp.rig2 = strip([panel(bk.root, 'BLOCK', [0.3, 0.15], 0.9, F), panel(lp.root, 'LEAP CROUCH', v, 0.9, F), panel(as.root, 'ASSEMBLING', v, 0.9, F)]);
            info.push('rig ' + (bl ? 'blender' : 'code'));
          } else if (it === 'arms') {
            const ra = await import('/js/rigarms.js'), { G } = await import('/js/ctx.js');
            const vmShot = (label, st, setup, n = 40) => {
              ra.armsReset(); ra.armsOn(); for (let i = 0; i < 30; i++) ra.updateArms(1 / 60, { visible: true }); // (settled at rest first)
              if (setup) setup();
              for (let i = 0; i < n; i++) ra.updateArms(1 / 60, { visible: true, ...st });
              const VW = Math.round(H * 16 / 9), vc = G.vmCamera.clone(); vc.aspect = VW / H; vc.updateProjectionMatrix(); // (a 16:9 screen, the arms where you see them)
              const A = ra.armsObj(), ts = new THREE.Scene(); // just the arms, in the viewmodel's own lights
              for (const o of G.vmScene.children) if (o.isLight) ts.add(o.clone());
              if (!ts.children.length) { ts.add(new THREE.HemisphereLight(0xcfe8ff, 0x7a4a6a, 1.8)); const d = new THREE.DirectionalLight(0xffffff, 1.5); d.position.set(2, 3, 4); ts.add(d); }
              ts.add(A.grp);
              r.setSize(Math.floor(VW * sc), Math.floor(H * sc), false);
              k.withEnv(r, ts, () => { r.setClearColor(0x3a3048); r.render(ts, vc); });
              G.vmScene.add(A.grp);
              const c = document.createElement('canvas'); c.width = VW; c.height = H;
              const x = c.getContext('2d'); x.imageSmoothingEnabled = jank === 3; x.drawImage(r.domElement, 0, 0, VW, H);
              r.setSize(Math.floor(W * sc), Math.floor(H * sc), false);
              x.font = 'bold 20px sans-serif'; const tw = x.measureText(label).width; x.fillStyle = 'rgba(0,0,0,0.6)'; x.fillRect(6, 6, tw + 14, 30);
              x.fillStyle = label.startsWith('OLD') ? '#ffffff' : '#ffe14d'; x.fillText(label, 13, 28);
              return c;
            };
            const a = code(['x_rigarms'], () => vmShot('OLD (code)', {}));
            const b = vmShot('BLENDER', {}), u = vmShot('IN USE: PUNCH', {}, () => ra.playArms('rig_punch'), 9), bk = vmShot('BLOCK', { block: true });
            ra.armsReset();
            outp.arms = strip([a, b, u, bk]);
            info.push('arms ' + (k.AUTHORED.x_rigarms ? 'blender' : 'code'));
          } else if (it === 'missile') {
            // (in flight it turns itself along its path; here the same mesh held still, side on, nose to the left)
            const plain = (grp, fl) => { const body = grp.children[0], m = new THREE.Mesh(body.geometry, body.material), g = new THREE.Group(); g.add(m); if (fl) m.add(new THREE.Mesh(body.children[0].geometry, body.children[0].material)); return g; };
            rm.rigReset();
            const a = code(['pj_rigmissile'], () => { rm.rigReset(); return plain(rm.buildRigMissile()); });
            rm.rigReset();
            const bg = rm.buildRigMissile(), b = plain(bg), u = plain(rm.buildRigMissile(), true);
            const v = [Math.PI / 2, 0.15];
            outp.missile = strip([panel(a, 'OLD (code)', v, 0.6), panel(b, 'BLENDER', v, 0.6), panel(u, 'IN USE: FLYING', [Math.PI / 2 + 0.3, 0.3], 0.6)]);
            info.push('missile ' + (Array.isArray(bg.children[0].material) ? 'blender' : 'code'));
          }
        } catch (e) { info.push(it + ' FAILED ' + e.message); }
      }
      r.dispose();
      return { outp, info };
    }, [items, FILES, jank]);
    for (const [n, url] of Object.entries(res.outp)) require('fs').writeFileSync(`${out}/${tag}_${n}.png`, Buffer.from(url.split(',')[1], 'base64'));
    console.log(tag, res.info.join(', '), errs.length ? '\n' + errs.join('\n') : '(no page errors)');
    bad += errs.length + res.info.filter((x) => x.includes('FAILED')).length;
    await pg.close();
  }
  await b.close();
  process.exitCode = bad ? 1 : 0;
})();
