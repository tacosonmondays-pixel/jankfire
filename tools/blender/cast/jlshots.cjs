// THE HEADLINER in the game's renderer (the dressed skinned model, the real clip code in jesterlord.js):
//   node tools/blender/cast/jlshots.cjs <port> <outDir> [check,turn,sil,close,poses,clips] [clip,clip...]
// check = the actor path: the model dresses the skeleton, every part and marker of the parts file is there, every clip
//         plays through (nothing NaN, every mark fires), the bells hang, the web and the stump show when they should,
//         the far LOD swaps in and back, the code puppet still stands. prints JL_CHECK ok / the failures (exit code 1)
// turn  = turnaround beside a 1.8 m mannequin                                  -> jl_game_turn.jpg
// sil   = his silhouette (side and 30 m) beside the owner's sketch            -> jl_game_silhouette.jpg
// close = face, eyes open, nose, hat, horns and bells, collar, marotte, stockings, foot and bell, big top, the stump -> jl_game_closeups.jpg
// poses = one moment a clip                                                    -> jl_game_poses.jpg
// clips = a contact strip per clip (12 frames, the marks called out)           -> jl_clip_<name>.jpg
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { execSync } = require('child_process');
const [PORT = 3000, OUT = '.', WHAT = 'check,turn,sil,close,poses,clips', ONLY = ''] = process.argv.slice(2);
const ROOT = path.join(__dirname, '..', '..', '..');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1600, height: 900 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message)); pg.on('console', (m) => { if (m.type() === 'error' && !/favicon|404/.test(m.text())) errs.push(m.text()); });
  await pg.addInitScript(() => localStorage.setItem('jf_giftseen_all', '1'));
  await pg.goto(`http://localhost:${PORT}/`); await pg.waitForTimeout(800);
  const init = await pg.evaluate(async () => {
    const THREE = await import('three');
    const { G } = await import('/js/ctx.js');
    const { jankUniforms } = await import('/js/jank.js'); jankUniforms.uSnap.value.set(4000, 3000);
    const looks = await import('/js/story/looks.js');
    const { CLIPS } = await import('/js/story/actors.js');
    const { JL, evalClip, durationOf } = await import('/js/story/jesterlord.js');
    const got = await looks.loadCast(['jester_lord', 'mannequin'], 60000);
    const meta = await fetch('/models/cast/c_jester_lord.parts.json').then((r) => r.json());
    JL.auto = false;
    const r = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true }); r.setSize(1600, 900); r.setPixelRatio(1); r.outputColorSpace = THREE.SRGBColorSpace; r.shadowMap.enabled = true;
    r.domElement.style.cssText = 'position:fixed;inset:0;z-index:99999'; document.body.append(r.domElement);
    const lab = document.createElement('div'); lab.style.cssText = 'position:fixed;inset:0;z-index:100000;pointer-events:none'; document.body.append(lab);
    let n = 0;
    const X = (window.JLX = { THREE, looks, CLIPS, JL, evalClip, durationOf, r, lab, got, meta, G });
    X.scene = (bg = 0x2a1830, floorR = 7) => { const sc = new THREE.Scene(); sc.background = new THREE.Color(bg); G.scene = sc;
      sc.add(new THREE.HemisphereLight(0xffe8f0, 0x402040, 1.4)); const d = new THREE.DirectionalLight(0xffd0b0, 2.4); d.position.set(-4, 9, -6); d.castShadow = true; d.shadow.mapSize.set(2048, 2048);
      Object.assign(d.shadow.camera, { left: -6, right: 6, top: 7, bottom: -5, near: 0.5, far: 30 }); sc.add(d);
      const rim = new THREE.DirectionalLight(0xff70a0, 1.4); rim.position.set(5, 4, 6); sc.add(rim);
      if (floorR) { const fl = new THREE.Mesh(new THREE.CircleGeometry(floorR, 48), new THREE.MeshStandardMaterial({ color: 0x3a2a40 })); fl.rotation.x = -Math.PI / 2; fl.receiveShadow = true; sc.add(fl); } return sc; };
    // him, in a clip at a time: stepped at 30 fps up to t (so the bells' swing is real). walk = metres a second he moves (the scuttle runs by distance)
    X.jester = (o = {}) => {
      const L = looks.buildLook('jester_lord'), c = L.ch;
      const a = { id: 'jlx' + n++, L, ch: c, pos: [0, 0, 0], yaw: 0, clip: null, face: L.face, lookY: 0, lookX: 0 };
      const rig = JL.rig(a); rig.manual = true; rig.manualDt = 1 / 30;
      const clip = o.clip || 'jl_idle', t = o.t ?? 0.4, t0 = Math.max(0, t - (o.settle ?? 1.5));
      for (let tt = t0; tt <= t + 1e-6; tt += 1 / 30) { if (o.walk) a.pos[2] -= o.walk / 30; CLIPS[clip].f(c, Math.min(tt, t), 1); }
      if (o.walk) { a.pos[2] = 0; }
      if (o.far) rig.vis(true);
      c.root.updateMatrixWorld(true);
      return { L, c, a, rig };
    };
    X.other = (id, h) => { const L = looks.buildLook(id); L.ch.head.rotation.z = 0; L.ch.arm.rotation.z = 0.1; L.ch.armL.rotation.z = -0.1; L.ch.foreR.rotation.x = 0.25; L.ch.foreL.rotation.x = 0.25; for (let k = 0; k < 30; k++) { L.face.blinkT = 9; L.face.update(0.05); }
      if (h) { L.ch.root.updateMatrixWorld(true); const bx = new THREE.Box3().setFromObject(L.ch.root); L.ch.root.scale.multiplyScalar(h / (bx.max.y - bx.min.y)); } return L; };
    X.cell = (i, cols, rows, sc, cam, text, sub) => {
      const w = 1600 / cols, h = 900 / rows, x0 = (i % cols) * w, y0 = 900 - (Math.floor(i / cols) + 1) * h;
      cam.aspect = w / h; cam.updateProjectionMatrix();
      r.setScissorTest(true); r.autoClear = false; r.setViewport(x0, y0, w, h); r.setScissor(x0, y0, w, h); r.clear(); r.render(sc, cam);
      if (text) { const d = document.createElement('div'); d.textContent = text; d.style.cssText = `position:absolute;left:${x0 + 6}px;top:${Math.floor(i / cols) * h + 5}px;font:700 13px sans-serif;color:#ffe14d;background:rgba(18,8,24,.85);padding:1px 5px;border:1px solid #ff4fd8;max-width:${w - 14}px`; lab.append(d); }
      if (sub) { const d = document.createElement('div'); d.textContent = sub; d.style.cssText = `position:absolute;left:${x0 + 6}px;top:${Math.floor(i / cols) * h + h - 24}px;font:700 12px sans-serif;color:#4fd8ff;background:rgba(18,8,24,.85);padding:1px 5px`; lab.append(d); }
    };
    X.clear = (col = 0x120818) => { r.setScissorTest(false); r.setViewport(0, 0, 1600, 900); r.setClearColor(col); r.clear(); lab.innerHTML = ''; };
    X.cam = (pos, at, fov = 30) => { const cam = new THREE.PerspectiveCamera(fov, 1, 0.05, 300); cam.position.set(...pos); cam.lookAt(...at); return cam; };
    X.orbit = (at, deg, dist, up = 0.12, fov = 30) => { const a = (deg * Math.PI) / 180; return X.cam([at[0] + Math.sin(a) * dist * Math.cos(up), at[1] + Math.sin(up) * dist, at[2] - Math.cos(a) * dist * Math.cos(up)], at, fov); }; // deg 0 = from his front, 90 = from his right
    X.tris = (root) => { let t = 0; root.traverse((o) => { if (o.isMesh) { let v = true; for (let p = o; p; p = p.parent) if (!p.visible) v = false; if (v) t += (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count) / 3; } }); return Math.round(t); };
    X.draws = (root) => { let d = 0; root.traverse((o) => { if (o.isMesh) { let v = true; for (let p = o; p; p = p.parent) if (!p.visible) v = false; if (v) d++; } }); return d; };
    const L0 = looks.buildLook('jester_lord');
    return { got, blender: !!L0.blender, tags: Object.keys(L0.parts || {}).length, clips: JL.clips };
  });
  console.log(JSON.stringify(init));
  const shot = async (name) => { await pg.waitForTimeout(150); const png = path.join(OUT, name + '.png'); await pg.screenshot({ path: png }); const jpg = path.join(OUT, name + '.jpg'); execSync(`ffmpeg -loglevel error -y -i "${png}" -q:v 3 "${jpg}"`); fs.unlinkSync(png); console.log('wrote', jpg); return jpg; };
  const what = WHAT.split(',');
  let bad = 0;

  if (what.includes('check')) {
    const res = await pg.evaluate(() => { const X = window.JLX, { THREE, JL, CLIPS, meta } = X; const fails = [];
      const sc = X.scene(); const J = X.jester({}); sc.add(J.c.root);
      if (!J.L.blender) fails.push('the glb did not dress the skeleton');
      for (const k of Object.keys(meta.parts)) if (!J.L.parts[k] || !J.L.parts[k].userData.blender) fails.push('part missing: ' + k);
      for (const k of Object.keys(meta.markers)) if (!J.L.parts[k]) fails.push('marker missing: ' + k);
      for (const k of Object.keys(meta.joints)) if (!J.c[k]) fails.push('joint missing: ' + k);
      let skinned = 0, bound = 0; J.c.root.traverse((o) => { if (o.isSkinnedMesh) { skinned++; if (o.skeleton && o.skeleton.bones.length === Object.keys(meta.joints).length) bound++; } });
      if (!skinned || bound !== skinned) fails.push(`skinned meshes ${skinned}, bound to the whole skeleton ${bound}`);
      // markers land where the parts file says they do, at rest
      const L1 = X.looks.buildLook('jester_lord'); L1.ch.root.updateMatrixWorld(true); let worst = 0, wk = '';
      for (const [k, m] of Object.entries(meta.markers)) { const p = L1.parts[k].getWorldPosition(new THREE.Vector3()); const d = Math.hypot(p.x - m.at[0], p.y - m.at[1], p.z - m.at[2]); if (d > worst) { worst = d; wk = k; } }
      if (worst > 0.004) fails.push(`marker ${wk} is ${worst.toFixed(4)} m from the parts file`);
      // every clip: steps through, nothing NaN, something moves, every mark fires
      const marks = []; JL.on((ev) => marks.push(ev.clip + ':' + ev.mark));
      const report = {};
      for (const clip of JL.clips) {
        const K = X.jester({ clip, t: 0, settle: 0 }); const dur = X.durationOf(clip); let moved = 0, nan = false, web = 0, stump = 0; const q0 = {};
        for (const j of Object.keys(meta.joints)) q0[j] = K.c[j].quaternion.clone();
        for (let t = 0; t <= dur + 0.05; t += 1 / 30) { CLIPS[clip].f(K.c, t, 1);
          for (const j of Object.keys(meta.joints)) { const q = K.c[j].quaternion, p = K.c[j].position; if (![q.x, q.y, q.z, q.w, p.x, p.y, p.z].every(Number.isFinite)) nan = true; moved = Math.max(moved, 1 - Math.abs(q.dot(q0[j]))); }
          if (K.rig.web && K.rig.web.visible) web++; if (K.L.parts.dmgStump && K.L.parts.dmgStump.visible) stump++; }
        const want = JL.data.clips[clip].marks.map((m) => clip + ':' + m[1]), miss = want.filter((w) => !marks.includes(w));
        if (nan) fails.push(clip + ': NaN'); if (moved < 1e-5) fails.push(clip + ': nothing moves'); if (miss.length) fails.push(clip + ': marks not fired: ' + miss.join(' '));
        if ((clip === 'jl_hang') !== (web > 10) && clip !== 'jl_drop') fails.push(clip + ': the web ' + (web ? 'shows' : 'does not show'));
        if (/leg_(off|back)/.test(clip) !== (stump > 5)) fails.push(clip + ': the stump ' + (stump ? 'shows' : 'does not show'));
        report[clip] = { dur, marks: want.length, web, stump };
      }
      // the bells hang straight down whatever the foot is doing (the hang turns him over: they still point at the floor)
      const Hg = X.jester({ clip: 'jl_hang', t: 3.0 }); Hg.c.root.updateMatrixWorld(true); let tilt = 0;
      for (const bn of JL.data.bells) { const q = Hg.c[bn].getWorldQuaternion(new THREE.Quaternion()); const dn = new THREE.Vector3(0, -1, 0).applyQuaternion(q); tilt = Math.max(tilt, Math.acos(Math.min(1, -dn.y))); }
      if (tilt > 0.6) fails.push('a bell hangs ' + tilt.toFixed(2) + ' rad off straight down in the hang');
      // the far LOD
      const near = X.tris(J.c.root), drawsNear = X.draws(J.c.root); J.rig.vis(true); const far = X.tris(J.c.root), drawsFar = X.draws(J.c.root); J.rig.vis(false); const back = X.tris(J.c.root);
      if (!(far > 500 && far < near / 4)) fails.push(`far LOD: ${far} triangles against ${near}`); if (back !== near) fails.push('far LOD does not swap back');
      // the code puppet (no glb) stands up and takes a clip
      const Lc = X.looks.buildLookCode('jester_lord'); let codeMeshes = 0; Lc.ch.root.traverse((o) => { if (o.isMesh) codeMeshes++; });
      const ac = { id: 'jlcode', L: Lc, ch: Lc.ch, pos: [0, 0, 0], yaw: 0, clip: null, face: Lc.face }; const rc = JL.rig(ac); rc.manual = true; rc.manualDt = 0.03; CLIPS.jl_bow.f(Lc.ch, 1.2, 1);
      if (codeMeshes < 40) fails.push('code puppet: only ' + codeMeshes + ' meshes');
      return { fails, near, far, drawsNear, drawsFar, worst, wk, clips: Object.keys(report).length, marks: marks.length, codeMeshes, tilt, report };
    });
    console.log('JL_CHECK', res.fails.length ? 'FAILED\n  ' + res.fails.join('\n  ') : 'ok', JSON.stringify({ near: res.near, far: res.far, draws: [res.drawsNear, res.drawsFar], worstMarker: res.wk + ' ' + res.worst.toFixed(4), clips: res.clips, marks: res.marks, codeMeshes: res.codeMeshes, bellTilt: +res.tilt.toFixed(3) }));
    console.log(JSON.stringify(res.report));
    bad += res.fails.length;
  }
  if (what.includes('turn')) {
    await pg.evaluate(() => { const X = window.JLX; X.clear();
      const views = [['front', 0], ['three quarter', 36], ['his right', 90], ['back', 180], ['three quarter back', 216], ['his left', -90]];
      views.forEach(([nm, deg], i) => { const sc = X.scene(0x2a1830, 8); const J = X.jester({ clip: 'jl_idle', t: 0.3 }); sc.add(J.c.root);
        const M = X.other('mannequin', 1.8); const side = /right|left/.test(nm); M.ch.root.position.set(side ? 0 : 3.4, 0, /right/.test(nm) ? -3.0 : /left/.test(nm) ? 3.0 : -0.6); M.ch.root.rotation.y = 0; sc.add(M.ch.root);
        X.cell(i, 3, 2, sc, X.orbit([0.2, 1.75, 0.2], deg, 13.5, 0.08), i === 0 ? 'THE HEADLINER, 3.3 m to his cap, 3.8 m to the hat bells, 4.9 m across the legs, beside a 1.8 m mannequin (you)' : nm); }); });
    await shot('jl_game_turn');
  }
  if (what.includes('sil')) {
    await pg.evaluate(() => { const X = window.JLX, { THREE } = X; X.clear(0xffffff);
      const black = new THREE.MeshBasicMaterial({ color: 0x000000 });
      const mk = (o) => { const sc = new THREE.Scene(); sc.background = new THREE.Color(0xffffff); X.G.scene = sc; const J = X.jester(o); J.L.face.root.visible = false; sc.add(J.c.root); sc.overrideMaterial = black; return sc; };
      X.cell(0, 4, 1, mk({ clip: 'jl_idle', t: 0.3 }), X.cam([-5.6, 2.95, -0.45], [0, 2.95, -0.45], 30), '', 'his head from his left, like the sketch');
      X.cell(1, 4, 1, mk({ clip: 'jl_idle', t: 0.3 }), X.cam([-30, 1.9, 0.2], [0, 1.9, 0.2], 10.5), '', 'from his left at 30 m, enlarged');
      X.cell(2, 4, 1, mk({ clip: 'jl_idle', t: 0.3, far: true }), X.cam([0, 1.9, -34], [0, 1.9, 0.2], 9.5), '', 'the far model (past 34 m), front, enlarged');
      const s3 = mk({ clip: 'jl_idle', t: 0.3 }); const M = X.other('mannequin', 1.8); M.ch.root.position.set(3.2, 0, 0); s3.add(M.ch.root); const fl = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), new THREE.MeshBasicMaterial({ color: 0xdddddd })); fl.rotation.x = -Math.PI / 2; s3.add(fl); s3.overrideMaterial = null;
      s3.children[0].traverse((o) => { if (o.isMesh) o.material = black; }); M.ch.root.traverse((o) => { if (o.isMesh) o.material = new THREE.MeshBasicMaterial({ color: 0x888888 }); });
      X.cell(3, 4, 1, s3, X.cam([0, 1.7, -30], [0, 1.9, 0], 55), '', 'true size at 30 m (grey: 1.8 m)');
    });
    const jpg = await shot('jl_game_sil_raw');
    const dst = path.join(OUT, 'jl_game_silhouette.jpg'), sk = path.join(ROOT, 'docs', 'story', 'cast', 'refs', 'jester_lord_owner_sketch.jpg');
    execSync(`ffmpeg -loglevel error -y -i "${sk}" -i "${jpg}" -filter_complex "[0:v]crop=1500:1220:400:180,scale=1106:900,eq=contrast=1.4:brightness=0.03[a];[a][1:v]hstack=inputs=2,scale=2400:-2" -q:v 3 "${dst}"`);
    fs.unlinkSync(jpg); console.log('wrote', dst);
  }
  // a close-up aims at a marker or joint (+ an offset): [label, jester options, marker | joint | [x, y, z], offset, deg, distance, up, fov]
  const closeups = async (cells, cols, rows, file) => {
    await pg.evaluate(([cells, cols, rows]) => { const X = window.JLX; X.clear();
      cells.forEach(([nm, o, mk, off, deg, d, up, fov], i) => { const sc = X.scene(0x2a1830, 7); const J = X.jester(o); sc.add(J.c.root);
        const p = Array.isArray(mk) ? new X.THREE.Vector3(...mk) : J.rig.at(mk); p.x += off[0]; p.y += off[1]; p.z += off[2];
        X.cell(i, cols, rows, sc, X.orbit([p.x, p.y, p.z], deg, d, up, fov || 30), nm); }); }, [cells, cols, rows]);
    await shot(file);
  };
  const Z = [0, 0, 0];
  if (what.includes('close')) {
    await closeups([
      ['his face: shut, smug, a grin past his ears', {}, 'faceAt', [0, 0.02, 0], 6, 2.6, 0.04], ['three quarter: the long nose', {}, 'faceAt', [0, 0.05, -0.1], 50, 2.8, 0.06],
      ['profile, like the sketch', {}, 'faceAt', [0, 0.15, 0.1], -90, 3.6, 0.03], ['his eyes open (the leg comes off)', { clip: 'jl_leg_off', t: 0.75 }, 'eyeAt', [0, -0.1, 0], 75, 1.7, 0.05],
      ['the hat from behind: horns, bells', {}, 'faceAt', [0, 0.45, 0.3], 160, 3.2, 0.25], ['a horn and its bell', {}, 'hatTipR', [-0.05, -0.15, 0], 60, 1.6, 0.1],
      ['the dummy jaw open (talking)', { clip: 'jl_talk', t: 0.2 }, 'mouthAt', [0, 0.05, 0], 14, 1.9, 0.05], ['the collar of bells, the ruff', {}, 'chestAt', [0, 0.18, 0], 20, 2.2, 0.25],
      ['the marotte: his own little head', {}, 'marotteAt', [0, 0, 0], 20, 1.2, 0.05], ['his right hand on his hip', {}, 'palmR', [0, 0.05, 0], 40, 1.4, 0.1],
      ['the stockings at a knee', {}, 'tibRB', [0, -0.15, 0], 30, 1.9, 0.1], ['a foot: the curled toe, the bell', {}, 'bellRA', [0, 0.05, 0], 30, 1.1, 0.12],
      ['the big top from behind', {}, 'topAt', [0, -0.75, 0.3], 160, 4.6, 0.32], ['the thorax: the carousel band, four red eyes', { clip: 'jl_idle', t: 0.3 }, [0, 1.2, -0.55], Z, 12, 2.4, -0.05],
      ['the stump (leg off)', { clip: 'jl_leg_off', t: 3.0 }, 'stumpAt', [0.05, 0, 0], 70, 1.6, 0.25], ['the far model, close up', { far: true }, [0, 1.7, 0.2], Z, 30, 12.5, 0.08]], 4, 4, 'jl_game_closeups');
  }
  const POSES = [['jl_idle', 0.9, 25, 12.5, 1.75], ['jl_talk', 0.5, 20, 9.5, 2.1], ['jl_talk', 3.0, 20, 9.5, 2.1], ['jl_bow', 0.55, 40, 12, 1.9], ['jl_bow', 2.0, 25, 12, 1.6], ['jl_bow', 2.6, 30, 12, 2.0],
    ['jl_walk', 0.2, 60, 12.5, 1.6], ['jl_hang', 0.75, 30, 15, 3.0], ['jl_hang', 3.0, 20, 15, 3.2], ['jl_drop', 1.0, 30, 12.5, 1.6], ['jl_leg_off', 0.4, 30, 13, 2.0], ['jl_leg_off', 1.6, 35, 13, 1.7], ['jl_leg_off', 3.9, 30, 13, 1.7], ['jl_leg_back', 1.9, 40, 12, 1.7]];
  if (what.includes('poses')) {
    await pg.evaluate(([POSES]) => { const X = window.JLX; X.clear();
      POSES.forEach(([clip, t, deg, dist, y], i) => { const sc = X.scene(0x2a1830, 8); const J = X.jester({ clip, t, walk: clip === 'jl_walk' ? 1.875 : 0 }); sc.add(J.c.root);
        X.cell(i, 7, 2, sc, X.orbit([0.4, y, 0], deg, dist, 0.08), clip.slice(3) + ' @' + t); }); }, [POSES]);
    await shot('jl_game_poses');
  }
  if (what.includes('clips')) {
    const VIEW = Object.fromEntries(POSES.map((p) => [p[0], p.slice(2)]));
    const clips = init.clips.filter((c) => !ONLY || ONLY.split(',').includes(c));
    for (const clip of clips) {
      await pg.evaluate(([clip, view]) => { const X = window.JLX, C = X.JL.data.clips[clip]; X.clear();
        const len = X.durationOf(clip), N = 12;
        const ts = Array.from({ length: N }, (_, i) => +((len * i) / (C.loop ? N : N - 1)).toFixed(2));
        for (const [mt] of C.marks) { let bi = 1, bd = 9; ts.forEach((t, i) => { if (i > 0 && i < N - 1 && Math.abs(t - mt) < bd) { bd = Math.abs(t - mt); bi = i; } }); if (mt > 0 && mt < len) ts[bi] = +(mt + 0.02).toFixed(2); }
        ts.sort((a, b) => a - b);
        const [deg, dist, y] = view || [30, 12.5, 1.8];
        ts.forEach((t, i) => { const sc = X.scene(0x2a1830, 8); const J = X.jester({ clip, t, walk: clip === 'jl_walk' ? 1.875 : 0 }); sc.add(J.c.root);
          const mk = C.marks.filter(([mt]) => Math.abs(mt + 0.02 - t) < 0.011).map((m) => m[1]).join(' ');
          X.cell(i, 6, 2, sc, X.orbit([0.4, y, 0], deg, dist, 0.08), (i === 0 ? clip + '   ' : '') + t.toFixed(2) + ' s', mk ? 'mark: ' + mk : ''); }); }, [clip, VIEW[clip] || null]);
      await shot('jl_clip_' + clip.slice(3));
    }
  }
  console.log(errs.length ? 'ERRORS:\n' + [...new Set(errs)].join('\n') : 'no errors');
  await b.close();
  process.exit(bad || errs.length ? 1 : 0);
})();
