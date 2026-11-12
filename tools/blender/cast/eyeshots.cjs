// story cast eye close-ups in the game's renderer, through the real actor code (actors.js, face.js, loco), stepped at
// 60 fps. one contact sheet per run: a row per cast member, the same shots every time:
//   talk   the dialogue close-up (talk.js closeup: your shoulder, 42 deg), them looking at you
//   front  straight on, looking at the camera
//   past   straight on, you standing 1.6 m off to their left: the eyes should look off to the side, both the same way
//   up     looking up and to the side (where the iris meets the lids)
//   blink  mid-blink, half shut, looking up
//   shut   the blink fully shut
//   side   profile, nobody near (the ball vs the head)
//   node tools/blender/cast/eyeshots.cjs <port> <out.png> [day|gut] [hd|potato] [ids] [walk]   (EYES_TW=180: tile size)
// walk: instead, a frame strip of each id tracking you walking past them 1.8 m away (and a forced blink half way)
// gen_puppet / gen_normal = a code-only NPC from a cast hint. docs/story/cast/eyes_before_after.jpg is two runs of this
// (main, then the fix) cut together
const { chromium } = require('playwright');
const fs = require('fs');
const [PORT = 3115, OUT = 'eyes.png', LIGHT = 'day', Q = 'hd', IDS = 'gordo,lumps,sharon,bev,dot,mina,pallet_jack,hat_lord,choir,choir_b,gen_puppet', WALK = ''] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const TW = +(process.env.EYES_TW || 240), TH = TW;
  const pg = await b.newPage({ viewport: { width: 800, height: 600 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message)); pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.goto(`http://localhost:${PORT}/`); await pg.waitForTimeout(800);
  const data = await pg.evaluate(async ([ids, light, q, TW, TH, walk]) => {
    const THREE = await import('three');
    const { jankUniforms } = await import('/js/jank.js');
    const potato = q === 'potato', SC = potato ? 0.22 : 1;
    const looks = await import('/js/story/looks.js'); const A = await import('/js/story/actors.js'); const { G } = await import('/js/ctx.js');
    await looks.loadCast(ids.filter((i) => !i.startsWith('gen_')), 30000);
    const rw = Math.max(8, Math.round(TW * SC)), rh = Math.max(8, Math.round(TH * SC));
    const r = new THREE.WebGLRenderer({ antialias: !potato, preserveDrawingBuffer: true }); r.setSize(rw, rh); r.setPixelRatio(1); r.outputColorSpace = THREE.SRGBColorSpace; r.shadowMap.enabled = true;
    // (potato: the game's vertex snap for a full 1280x720 screen at 0.22 scale, and pixels; the tile is a crop of that screen)
    if (potato) jankUniforms.uSnap.value.set((160 * (16 / 9)) / 2 * (TW / 1280) * 2.2, 160 / 2 * (TH / 720) * 2.2); else jankUniforms.uSnap.value.set(1e5, 1e5);
    const sc = new THREE.Scene();
    if (light === 'gut') {
      sc.background = new THREE.Color(0x3a0e1a); sc.fog = new THREE.Fog(0x5a1426, 6, 16);
      sc.add(new THREE.HemisphereLight(0xffd8e0, 0x501020, 0.8));
      const key = new THREE.DirectionalLight(0xffe0c8, 1.1); key.position.set(-2.5, 4, -4); key.castShadow = true; sc.add(key);
      const rim = new THREE.DirectionalLight(0xff6f91, 1.4); rim.position.set(3, 2.5, 3); sc.add(rim);
      const lamp = new THREE.PointLight(0xff6f91, 5, 7); lamp.position.set(0.6, 3.0, -1.8); sc.add(lamp);
      const fl = new THREE.Mesh(new THREE.PlaneGeometry(30, 30), new THREE.MeshStandardMaterial({ color: 0x7a1a2c, roughness: 0.5 })); fl.rotation.x = -Math.PI / 2; fl.receiveShadow = true; sc.add(fl);
    } else {
      sc.background = new THREE.Color(0x8fc8ff); sc.fog = new THREE.Fog(0xbfe0ff, 30, 120);
      sc.add(new THREE.HemisphereLight(0xdff0ff, 0x6a7a50, 1.5));
      const sun = new THREE.DirectionalLight(0xfff0d0, 2.6); sun.position.set(-3, 6, -4); sun.castShadow = true; sun.shadow.mapSize.set(1024, 1024); sc.add(sun);
      const fl = new THREE.Mesh(new THREE.PlaneGeometry(30, 30), new THREE.MeshStandardMaterial({ color: 0x7a9a5a, roughness: 0.9 })); fl.rotation.x = -Math.PI / 2; fl.receiveShadow = true; sc.add(fl);
    }
    const g0 = G.scene;
    const v = (x, y, z) => new THREE.Vector3(x, y, z);
    const cam = new THREE.PerspectiveCamera(30, TW / TH, 0.03, 80);
    const grab = () => { const c = document.createElement('canvas'); c.width = TW; c.height = TH; const g = c.getContext('2d'); g.imageSmoothingEnabled = false; g.drawImage(r.domElement, 0, 0, rw, rh, 0, 0, TW, TH); return c; };
    const spawn = (id) => {
      G.scene = sc; A.clearActors();
      const def = id === 'gen_puppet' ? { look: 'zz_offspec', hint: { body: 'puppet', desc: 'huge head' } } : id === 'gen_normal' ? { look: 'zz_someone', hint: { body: 'normal', desc: '' } } : { look: id };
      const a = A.spawnActor('p', { ...def, voice: { kind: 'chirp' } }, [0, 0, 0], 0); a.pos[1] = 0; a.home.p = a.pos.slice(); G.scene = g0;
      a.ch.head.userData.tilt = 0; a.ch.head.rotation.z = 0; // (no random jank tilt: the same face every run)
      a.t = 1.0; a.face.t = 1.0; a.face.blinkT = 99;
      return a;
    };
    let T = 0;
    const step = (a, n, eye, dt = 1 / 60) => { if (a.L.look === 'hat_lord') { a.lookAt = eye; if (window.JF_HL) window.JF_HL.rig(a).manualDt = dt; } for (let i = 0; i < n; i++) { T += dt; a.face.blinkT = Math.max(a.face.blinkT, 9); G.scene = sc; A.updateActors(dt, T * 1000, eye); G.scene = g0; } a.ch.root.updateMatrixWorld(true); };
    const mid = (a) => { const m = v(0, 0, 0); if (a.face && a.face.eyes[0].piv.visible) { for (const e of a.face.eyes) m.add(e.piv.getWorldPosition(v(0, 0, 0))); m.multiplyScalar(0.5); } else if (a.ch.eyeHR && a.ch.eyeHL) { m.add(a.ch.eyeHR.getWorldPosition(v(0, 0, 0))).add(a.ch.eyeHL.getWorldPosition(v(0, 0, 0))).multiplyScalar(0.5); } else if (a.L.parts && a.L.parts.eyeAt) a.L.parts.eyeAt.getWorldPosition(m); else A.headPos(a, m); return m; };
    const shot = (a, camPos, at, fov) => { cam.fov = fov; cam.aspect = TW / TH; cam.updateProjectionMatrix(); cam.position.copy(camPos); cam.lookAt(at); G.scene = sc; r.render(sc, cam); G.scene = g0; return grab(); };
    const rows = [];
    for (const id of ids) {
      const a = spawn(id); const S = a.ch.root.scale.y;
      step(a, 10, null); const M0 = mid(a), hb = new THREE.Box3().setFromObject(a.ch.head), hs = hb.getSize(v(0, 0, 0)), H = a.ch.eyeHR ? 0.3 : Math.max(hs.x, hs.y * 0.8, 0.22);
      const tiles = [], info = { id, look: a.L.look, blender: !!a.L.blender, kind: a.L.kind };
      const near = (deg, dist, up = 0) => { const t = deg * Math.PI / 180; return v(M0.x - Math.sin(t) * dist, M0.y + up, M0.z - Math.cos(t) * dist); };
      if (walk) {
        // you walk past, left to right, 1.8 m in front of them, at your eye height (1.6 m); a fixed camera over your path
        const eyeH = 1.6, camP = v(M0.x - 0.12, M0.y + 0.02, M0.z - H * 2.6), fov = 22;
        step(a, 30, [-3, eyeH, -1.8]);
        for (let i = 0; i < 48; i++) {
          const x = -3 + i * (6 / 47), eye = [x, eyeH, -1.8];
          if (i === 26) a.face.blink = 1, a.face.blinkT = 99;
          if (a.L.look === 'hat_lord') a.lookAt = eye; for (let k = 0; k < 2; k++) { T += 1 / 60; G.scene = sc; A.updateActors(1 / 60, T * 1000, eye); G.scene = g0; if (i !== 26) a.face.blinkT = 99; }
          a.ch.root.updateMatrixWorld(true);
          tiles.push([shot(a, camP, mid(a), fov), `f${i} you x ${x.toFixed(1)}` + (i >= 26 && i <= 29 ? ' blink' : '')]);
        }
        rows.push({ info, tiles }); continue;
      }
      // talk: the closeup over your shoulder (talk.js), you 1.7 m away, a little off to their left
      const you = near(-12, 1.7); you.y = Math.max(1.55, M0.y - 0.1);
      step(a, 90, [you.x, you.y, you.z]);
      { const hp = A.headPos(a, v(0, 0, 0)), fw = hp.clone().sub(you); fw.y = 0; fw.normalize(); const side = v(-fw.z, 0, fw.x); const dist = 1.25 * Math.max(1, S * 0.85) + (a.L.look === 'gordo' ? 0.5 : 0);
        const p = hp.clone().addScaledVector(fw, -dist).addScaledVector(side, -0.42 * Math.max(1, S * 0.7)); p.y = hp.y + 0.05 - (hp.y - you.y) * 0.25; const lk = hp.clone(); lk.y -= 0.06 * S;
        tiles.push([shot(a, p, lk, 30), 'talk: at you']); }
      // front, looking at the camera
      const cf = near(0, H * 3.4); step(a, 90, [cf.x, cf.y, cf.z]); tiles.push([shot(a, cf, mid(a), 22), 'front: at camera']);
      // you off to their left (+x is their right: -x), the camera stays in front
      step(a, 90, [M0.x - 1.6, M0.y + 0.05, M0.z - 1.2]); tiles.push([shot(a, cf, mid(a), 22), 'you to the side']);
      // looking up and to the side: where the iris meets the lids
      const upT = [M0.x + 1.2, M0.y + 1.3, M0.z - 1.6]; step(a, 90, upT); tiles.push([shot(a, cf, mid(a), 22), 'looking up']);
      // mid-blink, still looking up; then fully shut
      a.face.blink = 0.9; a.face.update(0); a.ch.root.updateMatrixWorld(true); tiles.push([shot(a, cf, mid(a), 22), 'blink, half']);
      a.face.blink = 0.5; a.face.update(0); a.ch.root.updateMatrixWorld(true); tiles.push([shot(a, cf, mid(a), 22), 'blink, shut']);
      a.face.blink = 0; step(a, 60, null);
      // the side: profile, nobody near
      const cs = near(80, H * 3.4); step(a, 60, null); tiles.push([shot(a, cs, mid(a), 22), 'side']);
      rows.push({ info, tiles });
    }
    // the sheet
    const LW = 150, cols = Math.max(...rows.map((r) => r.tiles.length)), W = LW + cols * TW, Hh = rows.length * (TH + 4);
    const sheet = document.createElement('canvas'); sheet.width = W; sheet.height = Hh; const g = sheet.getContext('2d'); g.imageSmoothingEnabled = false;
    g.fillStyle = '#120818'; g.fillRect(0, 0, W, Hh);
    rows.forEach((row, ri) => {
      const y = ri * (TH + 4);
      g.fillStyle = '#ffe14d'; g.font = 'bold 17px sans-serif'; g.fillText(row.info.id, 8, y + 26);
      g.fillStyle = '#4fd8ff'; g.font = '13px sans-serif'; g.fillText(`${row.info.kind} ${row.info.blender ? 'glb' : 'code'}`, 8, y + 46);
      row.tiles.forEach(([c, label], ci) => { g.drawImage(c, LW + ci * TW, y); g.fillStyle = 'rgba(0,0,0,0.6)'; g.fillRect(LW + ci * TW, y + TH - 20, TW, 20); g.fillStyle = '#fff'; g.font = '13px sans-serif'; g.fillText(label, LW + ci * TW + 6, y + TH - 6); });
    });
    return { url: sheet.toDataURL('image/png'), rows: rows.map((r) => r.info) };
  }, [IDS.split(','), LIGHT, Q, TW, TH, WALK === 'walk']);
  fs.writeFileSync(OUT, Buffer.from(data.url.split(',')[1], 'base64'));
  console.log(JSON.stringify(data.rows)); console.log(errs.join('\n') || 'no errors'); await b.close();
})();
