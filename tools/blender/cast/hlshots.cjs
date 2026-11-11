// MADAM CHAIR in the game's renderer (the dressed model, the real mouth rig, the real clip code in hatlord.js):
//   node tools/blender/cast/hlshots.cjs <port> <outDir> [check,turn,sil,close,poses,clips] [clip,clip...]
// check = the actor path: the model dresses the skeleton, every part and marker of the parts file is there, every clip
//         plays through, the far LOD swaps in. prints HL_CHECK ok / the failures (exit code 1)
// turn  = turnaround beside a 1.8 m mannequin                                      -> hl_game_turn.jpg
// sil   = her silhouette at 30 m, enlarged and at true size, beside the owner's sketch -> hl_game_silhouette.jpg
// close = the hat (top, underside, mouth), HER eyes, the eyeless reveal, hands, chest, the far LOD -> hl_game_closeups.jpg
// poses = one moment a clip                                                          -> hl_game_poses.jpg
// clips = a contact strip per clip (12 frames, the marks called out)                 -> hl_clip_<name>.jpg
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
    const { HL, evalClip, durationOf } = await import('/js/story/hatlord.js');
    const got = await looks.loadCast(['hat_lord', 'mannequin'], 40000);
    const meta = await fetch('/models/cast/c_hat_lord.parts.json').then((r) => r.json());
    HL.auto = false;
    const r = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true }); r.setSize(1600, 900); r.setPixelRatio(1); r.outputColorSpace = THREE.SRGBColorSpace; r.shadowMap.enabled = true;
    r.domElement.style.cssText = 'position:fixed;inset:0;z-index:99999'; document.body.append(r.domElement);
    const lab = document.createElement('div'); lab.style.cssText = 'position:fixed;inset:0;z-index:100000;pointer-events:none'; document.body.append(lab);
    let n = 0;
    const X = (window.HLX = { THREE, looks, CLIPS, HL, evalClip, durationOf, r, lab, got, meta, G });
    X.scene = (bg = 0x2a1830, floorR = 5) => { const sc = new THREE.Scene(); sc.background = new THREE.Color(bg); G.scene = sc;
      sc.add(new THREE.HemisphereLight(0xffe8f0, 0x402040, 1.4)); const d = new THREE.DirectionalLight(0xffd0b0, 2.4); d.position.set(-3, 7, -5); d.castShadow = true; d.shadow.mapSize.set(1024, 1024);
      Object.assign(d.shadow.camera, { left: -4, right: 4, top: 5, bottom: -4, near: 0.5, far: 24 }); sc.add(d);
      const rim = new THREE.DirectionalLight(0xff70a0, 1.4); rim.position.set(4, 3, 5); sc.add(rim);
      if (floorR) { const fl = new THREE.Mesh(new THREE.CircleGeometry(floorR, 40), new THREE.MeshStandardMaterial({ color: 0x3a2a40 })); fl.rotation.x = -Math.PI / 2; fl.receiveShadow = true; sc.add(fl); } return sc; };
    // her, in a clip at a time. look = what the hat looks at ([x, y, z]; null = nothing). far = the far LOD
    X.chair = (o = {}) => {
      const L = looks.buildLook('hat_lord'), c = L.ch;
      const a = { id: 'hlx' + n++, L, ch: c, pos: [0, 0, 0], yaw: 0, clip: null, face: L.face, lookY: 0, lookX: 0 };
      const rig = HL.rig(a); rig.manual = true; rig.manualDt = 0.25; rig.lookTo = o.look === undefined ? null : o.look;
      const clip = o.clip || 'hl_idle', t = o.t ?? 0.4;
      if (o.walk) { // her walk runs by distance: walk her there, then stand her back on the spot for the picture
        rig.manualDt = 1 / 30; for (let tt = 0; tt <= t + 1.2; tt += 1 / 30) { a.pos[2] -= o.walk / 30; CLIPS[clip].f(c, tt, 1); } a.pos[2] = 0;
      } else for (let k = 0; k < 14; k++) CLIPS[clip].f(c, t, 1); // (the look eases in: let it arrive)
      if (o.far) rig.vis(true);
      const F = HL.data.clips[clip].face; let face = 'chair'; for (const [ft, fn] of F) if (t >= ft) face = fn;
      L.face.set(o.face || face); for (let k = 0; k < 30; k++) { L.face.blinkT = 9; L.face.update(0.05); }
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
    X.cam = (pos, at, fov = 30) => { const cam = new THREE.PerspectiveCamera(fov, 1, 0.05, 200); cam.position.set(...pos); cam.lookAt(...at); return cam; };
    X.orbit = (at, deg, dist, up = 0.12, fov = 30) => { const a = deg * Math.PI / 180; return X.cam([at[0] + Math.sin(a) * dist * Math.cos(up), at[1] + Math.sin(up) * dist, at[2] - Math.cos(a) * dist * Math.cos(up)], at, fov); }; // deg 0 = from her front, 90 = from her right
    X.tris = (root) => { let t = 0; root.traverse((o) => { if (o.isMesh && o.visible) { let v = true; for (let p = o; p; p = p.parent) if (!p.visible) v = false; if (v) t += (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count) / 3; } }); return Math.round(t); };
    const L0 = looks.buildLook('hat_lord');
    return { got, blender: !!L0.blender, tags: Object.keys(L0.parts || {}).length, clips: HL.clips };
  });
  console.log(JSON.stringify(init));
  const shot = async (name) => { await pg.waitForTimeout(150); const png = path.join(OUT, name + '.png'); await pg.screenshot({ path: png }); const jpg = path.join(OUT, name + '.jpg'); execSync(`ffmpeg -loglevel error -y -i "${png}" -q:v 3 "${jpg}"`); fs.unlinkSync(png); console.log('wrote', jpg); return jpg; };
  const what = WHAT.split(',');
  let bad = 0;

  if (what.includes('check')) {
    const res = await pg.evaluate(() => { const X = window.HLX, { THREE, HL, CLIPS, meta } = X; const fails = [];
      const sc = X.scene(); const J = X.chair({}); sc.add(J.c.root);
      if (!J.L.blender) fails.push('the glb did not dress the skeleton');
      for (const k of Object.keys(meta.parts)) if (!J.L.parts[k] || !J.L.parts[k].userData.blender) fails.push('part missing: ' + k);
      for (const k of Object.keys(meta.markers)) if (!J.L.parts[k]) fails.push('marker missing: ' + k);
      for (const k of Object.keys(meta.joints)) if (!J.c[k]) fails.push('joint missing: ' + k);
      // markers land where the parts file says they do, at rest
      const L1 = X.looks.buildLook('hat_lord'); L1.ch.root.updateMatrixWorld(true); let worst = 0, wk = '';
      for (const [k, m] of Object.entries(meta.markers)) { const p = L1.parts[k].getWorldPosition(new THREE.Vector3()); const d = Math.hypot(p.x - m.at[0], p.y - m.at[1], p.z - m.at[2]); if (d > worst) { worst = d; wk = k; } }
      if (worst > 0.004) fails.push(`marker ${wk} is ${worst.toFixed(4)} m from the parts file`);
      // every clip: steps through, nothing goes NaN, something moves, every mark fires
      const marks = []; HL.on((ev) => marks.push(ev.clip + ':' + ev.mark));
      const report = {};
      for (const clip of HL.clips) {
        const K = X.chair({ clip, t: 0 }); K.rig.manualDt = 1 / 30; const dur = X.durationOf(clip); let moved = 0, nan = false; const q0 = {};
        for (const j of Object.keys(meta.joints)) q0[j] = K.c[j].quaternion.clone();
        for (let t = 0; t <= dur + 0.05; t += 1 / 30) { CLIPS[clip].f(K.c, t, 1);
          for (const j of Object.keys(meta.joints)) { const q = K.c[j].quaternion, p = K.c[j].position; if (![q.x, q.y, q.z, q.w, p.x, p.y, p.z].every(Number.isFinite)) nan = true; moved = Math.max(moved, 1 - Math.abs(q.dot(q0[j]))); } }
        const want = X.HL.data.clips[clip].marks.map((m) => clip + ':' + m[1]), miss = want.filter((w) => !marks.includes(w));
        if (nan) fails.push(clip + ': NaN'); if (moved < 1e-5) fails.push(clip + ': nothing moves'); if (miss.length) fails.push(clip + ': marks not fired: ' + miss.join(' '));
        report[clip] = { dur, marks: want.length };
      }
      // the far LOD
      const near = X.tris(J.c.root); J.rig.vis(true); const far = X.tris(J.c.root); J.rig.vis(false); const back = X.tris(J.c.root);
      if (!(far > 500 && far < near / 5)) fails.push(`far LOD: ${far} triangles against ${near}`); if (back !== near) fails.push('far LOD does not swap back');
      // the code puppet (no glb) stands up and takes a clip
      const Lc = X.looks.buildLookCode('hat_lord'); let codeMeshes = 0; Lc.ch.root.traverse((o) => { if (o.isMesh) codeMeshes++; });
      const ac = { id: 'hlcode', L: Lc, ch: Lc.ch, pos: [0, 0, 0], yaw: 0, clip: null, face: Lc.face }; const rc = HL.rig(ac); rc.manual = true; rc.manualDt = 0.03; CLIPS.hl_lunge.f(Lc.ch, 0.7, 1);
      return { fails, near, far, worst, wk, clips: Object.keys(report).length, marks: marks.length, codeMeshes, draw: (() => { let d = 0; J.c.root.traverse((o) => { if (o.isMesh && o.visible) d++; }); return d; })() };
    });
    console.log('HL_CHECK', res.fails.length ? 'FAILED\n  ' + res.fails.join('\n  ') : 'ok', JSON.stringify({ near: res.near, far: res.far, worstMarker: res.wk + ' ' + res.worst.toFixed(4), clips: res.clips, marks: res.marks, codeMeshes: res.codeMeshes, meshes: res.draw }));
    bad += res.fails.length;
  }
  if (what.includes('turn')) {
    await pg.evaluate(() => { const X = window.HLX; X.clear();
      const views = [['front', 0], ['three quarter', 36], ['her right: the low wing, the feeler', 90], ['back', 180], ['three quarter back', 216], ['her left: the long wing', -90]];
      views.forEach(([nm, deg], i) => { const sc = X.scene(0x2a1830, 6); const J = X.chair({ clip: 'hl_idle', t: 0.4 }); sc.add(J.c.root);
        const M = X.other('mannequin', 1.8); M.ch.root.position.set(/right|left/.test(nm) ? 0 : 1.55, 0, /right/.test(nm) ? 1.6 : /left/.test(nm) ? -1.6 : 0.2); M.ch.root.rotation.y = 0; sc.add(M.ch.root);
        X.cell(i, 3, 2, sc, X.orbit([0.1, 1.75, 0], deg, 9.4, 0.07), i === 0 ? 'MADAM CHAIR and OVERSIGHT, 2.96 m to the top of her head, beside a 1.8 m mannequin (you)' : nm); }); });
    await shot('hl_game_turn');
  }
  if (what.includes('sil')) {
    await pg.evaluate(() => { const X = window.HLX, { THREE } = X; X.clear(0xffffff);
      const black = new THREE.MeshBasicMaterial({ color: 0x000000 });
      const mk = () => { const sc = new THREE.Scene(); sc.background = new THREE.Color(0xffffff); X.G.scene = sc; const J = X.chair({ clip: 'hl_idle', t: 0.4 }); J.L.face.root.visible = false; sc.add(J.c.root); sc.overrideMaterial = black; return sc; };
      // 30 m away: enlarged (a long lens), the far model enlarged the same, and what a 1600 x 900 screen shows at the game's field of view
      const tele = (far) => { const sc = mk(); if (far) sc.children[0].traverse(() => {}); return sc; };
      const s1 = tele(false); X.cell(0, 3, 1, s1, X.cam([-0.2, 1.84, -30], [-0.2, 1.84, 0], 7.6), '', 'from 30 m, enlarged');
      const sc2 = new THREE.Scene(); sc2.background = new THREE.Color(0xffffff); X.G.scene = sc2; const J2 = X.chair({ clip: 'hl_idle', t: 0.4, far: true }); J2.L.face.root.visible = false; sc2.add(J2.c.root); sc2.overrideMaterial = black;
      X.cell(1, 3, 1, sc2, X.cam([-0.2, 1.84, -34], [-0.2, 1.84, 0], 6.7), '', 'the far model (past 34 m), enlarged');
      const s3 = mk(); const M = X.other('mannequin', 1.8); M.ch.root.position.set(1.9, 0, 0); s3.add(M.ch.root); const fl = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), new THREE.MeshBasicMaterial({ color: 0xdddddd })); fl.rotation.x = -Math.PI / 2; s3.add(fl); s3.overrideMaterial = null;
      s3.children[0].traverse((o) => { if (o.isMesh) o.material = black; }); M.ch.root.traverse((o) => { if (o.isMesh) o.material = new THREE.MeshBasicMaterial({ color: 0x888888 }); });
      const c3 = X.cam([0, 1.7, -30], [0, 1.9, 0], 55); X.cell(2, 3, 1, s3, c3, '', 'true size at 30 m on a 16:9 screen (the grey figure is 1.8 m)');
    });
    const jpg = await shot('hl_game_sil_raw');
    const dst = path.join(OUT, 'hl_game_silhouette.jpg'), sk = path.join(ROOT, 'docs', 'story', 'cast_refs', 'hat_lord_owner_sketch.jpg');
    execSync(`ffmpeg -loglevel error -y -i "${sk}" -i "${jpg}" -filter_complex "[0:v]crop=1360:1496:130:440,scale=818:900,eq=contrast=1.5:brightness=0.04[a];[a][1:v]hstack=inputs=2" -q:v 3 "${dst}"`);
    fs.unlinkSync(jpg); console.log('wrote', dst);
  }
  // a close-up aims at a marker (+ an offset in metres): [label, chair options, marker or [x, y, z], offset, deg, distance, up, fov]
  const closeups = async (cells, cols, rows, file) => {
    await pg.evaluate(([cells, cols, rows]) => { const X = window.HLX; X.clear();
      cells.forEach(([nm, o, mk, off, deg, d, up, fov], i) => { const sc = X.scene(0x2a1830, 5); const J = X.chair(o); sc.add(J.c.root);
        const p = Array.isArray(mk) ? new X.THREE.Vector3(...mk) : J.rig.at(mk); p.x += off[0]; p.y += off[1]; p.z += off[2];
        X.cell(i, cols, rows, sc, X.orbit([p.x, p.y, p.z], deg, d, up, fov || 30), nm); }); }, [cells, cols, rows]);
    await shot(file);
  };
  const Z = [0, 0, 0], you = [0, 1.7, -2.4];
  if (what.includes('close')) {
    await closeups([
      ['the hat from above', {}, 'hatTopAt', [0, -0.1, 0], 18, 6.4, 0.8], ['the underside, from where you stand (1.7 m, 2.4 m off)', { clip: 'hl_talk', t: 1.5, look: you }, 'faceAt', [0, 0.1, 0], 4, 2.9, -0.42, 55],
      ['its mouth: the band splits (the lunge, held)', { clip: 'hl_lunge', t: 1.7, look: you }, 'hatMouthAt', [0, 0.02, 0], 35, 3.0, -0.1], ['the growths on her right of the crown', {}, 'weakA', [-0.05, 0, 0], 60, 2.2, 0.25],
      ['HER eyes: the brown pair, looking at you', { clip: 'hl_talk', t: 1.5, look: you }, 'eyeAt', Z, 0, 1.25, -0.15], ['her eyes shut together (a blink)', { clip: 'hl_idle', t: 1.75 }, 'eyeAt', Z, 12, 1.5, 0.05],
      ['one of its own: they blink alone', { clip: 'hl_idle', t: 6.5 }, 'weakC', Z, 10, 1.4, 0.45], ['her face under the brim: its fingers', {}, 'faceAt', [0, 0.06, 0], 14, 2.1, -0.2],
      ['the reveal: no eyes', { clip: 'hl_reveal', t: 2.8, look: null }, 'faceAt', [0, 0.08, 0], 10, 2.0, -0.16], ['the reveal, from her left', { clip: 'hl_reveal', t: 2.8, look: null }, 'faceAt', [0, 0.1, 0], -58, 2.6, -0.1],
      ['her right hand at rest', {}, 'palmR', [0, -0.1, 0], 50, 1.5, 0.05], ['the offer: palm up', { clip: 'hl_offer', t: 2.0, look: you }, 'palmR', [0, 0.02, 0], 55, 1.7, 0.3],
      ['one raised finger', { clip: 'hl_lunge', t: 1.8, look: you }, 'fingerTipL', [0, -0.08, 0], -35, 1.6, 0.0], ['the chest: the empty socket', {}, 'socketAt', [0.04, 0, 0], 8, 1.5, 0.05],
      ['the collar: its star brooches, the lapels', {}, [0.12, 2.38, -0.08], Z, 30, 1.6, 0.2], ['the cape from behind', {}, [0, 1.4, 0], Z, 180, 8.4, 0.08],
      ['the low wing and the feeler', {}, 'brimTipR', [-0.15, 0, 0], 30, 2.6, -0.1], ['the far model, close up', { far: true }, [0, 1.75, 0], Z, 25, 9.4, 0.07]], 6, 3, 'hl_game_closeups');
  }
  const POSES = [['hl_idle', 1.75, 24, 9.2, 1.75], ['hl_walk', 0.35, 62, 9.2, 1.6], ['hl_duck', 2.2, 55, 9.2, 1.5], ['hl_talk', 1.5, 28, 6.4, 2.4], ['hl_offer', 1.9, 40, 7.4, 1.9], ['hl_bow', 1.3, 62, 8.0, 1.9], ['hl_lunge', 0.72, 60, 8.2, 2.0], ['hl_lunge', 1.7, 58, 8.2, 2.0],
    ['hl_reveal', 2.6, 14, 4.2, 2.7], ['hl_attack_tell', 1.0, 24, 9.6, 1.9], ['hl_strike', 0.3, 30, 9.6, 1.8], ['hl_stagger', 0.14, 60, 9.4, 1.7], ['hl_hat_off', 1.4, 40, 11.5, 2.2], ['hl_hat_off', 4.4, 40, 11.5, 1.9]];
  if (what.includes('poses')) {
    await pg.evaluate(([POSES, you]) => { const X = window.HLX; X.clear();
      POSES.forEach(([clip, t, deg, dist, y], i) => { const sc = X.scene(0x2a1830, 6); const J = X.chair({ clip, t, look: you, walk: clip === 'hl_walk' ? 0.726 : 0 }); sc.add(J.c.root);
        X.cell(i, 7, 2, sc, X.orbit([0, y, -0.2], deg, dist, 0.08), clip.slice(3) + ' @' + t); }); }, [POSES, you]);
    await shot('hl_game_poses');
  }
  if (what.includes('clips')) {
    const VIEW = Object.fromEntries(POSES.map((p) => [p[0], p.slice(2)]));
    const clips = init.clips.filter((c) => !ONLY || ONLY.split(',').includes(c));
    for (const clip of clips) {
      await pg.evaluate(([clip, view, you]) => { const X = window.HLX, C = X.HL.data.clips[clip]; X.clear();
        const len = X.durationOf(clip), N = 12;
        const ts = Array.from({ length: N }, (_, i) => +(len * i / (C.loop ? N : N - 1)).toFixed(2));
        for (const [mt] of C.marks) { let bi = 1, bd = 9; ts.forEach((t, i) => { if (i > 0 && i < N - 1 && Math.abs(t - mt) < bd) { bd = Math.abs(t - mt); bi = i; } }); if (mt > 0 && mt < len) ts[bi] = +(mt + 0.02).toFixed(2); } // the marks get a frame each
        ts.sort((a, b) => a - b);
        const [deg, dist, y] = view || [30, 9.4, 1.8];
        ts.forEach((t, i) => { const sc = X.scene(0x2a1830, 6); const J = X.chair({ clip, t, look: you, walk: clip === 'hl_walk' ? 0.726 : 0 }); sc.add(J.c.root);
          const mk = C.marks.filter(([mt]) => Math.abs(mt + 0.02 - t) < 0.011).map((m) => m[1]).join(' ');
          X.cell(i, 6, 2, sc, X.orbit([0, y, -0.2], deg, dist, 0.08), (i === 0 ? clip + '   ' : '') + t.toFixed(2) + ' s', mk ? 'mark: ' + mk : ''); }); }, [clip, VIEW[clip] || (clip === 'hl_reveal_end' ? [14, 4.2, 2.7] : null), you]);
      await shot('hl_clip_' + clip.slice(3));
    }
  }
  console.log(errs.length ? 'ERRORS:\n' + [...new Set(errs)].join('\n') : 'no errors');
  await b.close();
  process.exit(bad || errs.length ? 1 : 0);
})();
