// PALLET JACK in the game's renderer (the dressed model, the real face rig, the real clip code):
//   node tools/blender/cast/pjshots.cjs <port> <outDir> [turn,face,dmg,parts,poses,clips] [clip,clip...]
// turn  = turnaround next to Lumps and the mannequin, the hand truck beside him     -> pj_game_turn.jpg
// face  = the face at talk distance: his resting face, the faces his clips use      -> pj_game_face.jpg
// dmg   = every damage state, the far LOD up close                                  -> pj_game_damage.jpg
// parts = the rig parts close up, at rest and with the rig up                        -> pj_game_parts.jpg
// poses = one key pose per clip                                                      -> pj_game_poses.jpg
// clips = a contact sheet per clip (12 frames, the marks called out)                 -> pj_clip_<name>.jpg
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { execSync } = require('child_process');
const [PORT = 3000, OUT = '.', WHAT = 'turn,face,dmg,parts,poses,clips', ONLY = ''] = process.argv.slice(2);
const W = 1600, H = 900;
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: W, height: H } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message)); pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.goto(`http://localhost:${PORT}/`); await pg.waitForTimeout(800);
  const init = await pg.evaluate(async () => {
    const THREE = await import('three');
    const { G } = await import('/js/ctx.js');
    const { jankUniforms } = await import('/js/jank.js'); jankUniforms.uSnap.value.set(4000, 3000);
    const looks = await import('/js/story/looks.js');
    const { CLIPS } = await import('/js/story/actors.js');
    const { PJ, evalClip } = await import('/js/story/palletjack.js');
    const { glbLoader } = await import('/js/glbkit.js');
    const got = await looks.loadCast(['pallet_jack', 'lumps', 'mannequin'], 30000);
    const truck = await glbLoader().loadAsync('/models/story/s_handtruck.glb').then((g) => g.scene).catch(() => null);
    PJ.fx = false; PJ.auto = false;
    const r = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true }); r.setSize(1600, 900); r.setPixelRatio(1); r.outputColorSpace = THREE.SRGBColorSpace; r.shadowMap.enabled = true;
    r.domElement.style.cssText = 'position:fixed;inset:0;z-index:99999'; document.body.append(r.domElement);
    const lab = document.createElement('div'); lab.style.cssText = 'position:fixed;inset:0;z-index:100000;pointer-events:none'; document.body.append(lab);
    let n = 0;
    const X = (window.PJX = { THREE, looks, CLIPS, PJ, evalClip, r, lab, truck, got });
    X.scene = (bg = 0x2a1830, floorR = 4) => { const sc = new THREE.Scene(); sc.background = new THREE.Color(bg); G.scene = sc;
      sc.add(new THREE.HemisphereLight(0xffe8f0, 0x402040, 1.4)); const d = new THREE.DirectionalLight(0xffd0b0, 2.4); d.position.set(-3, 6, -5); d.castShadow = true; d.shadow.mapSize.set(1024, 1024);
      Object.assign(d.shadow.camera, { left: -4, right: 4, top: 4, bottom: -4, near: 0.5, far: 20 }); sc.add(d);
      const rim = new THREE.DirectionalLight(0xff70a0, 1.4); rim.position.set(4, 3, 5); sc.add(rim);
      const fl = new THREE.Mesh(new THREE.CircleGeometry(floorR, 40), new THREE.MeshStandardMaterial({ color: 0x3a2a40 })); fl.rotation.x = -Math.PI / 2; fl.receiveShadow = true; sc.add(fl); return sc; };
    // a Jack in a state / a clip at a time. face: a FACES name (default: what the clip says, else his own)
    X.jack = (o = {}) => {
      const L = looks.buildLook('pallet_jack'), c = L.ch; c.head.rotation.z = 0;
      const a = { id: 'pjx' + n++, L, ch: c, pos: [0, 0, 0], yaw: 0, clip: null, face: L.face };
      const rig = PJ.rig(a); rig.manual = true;
      c.arm.rotation.set(0.05, 0, 0.1); c.armL.rotation.set(0.05, 0, -0.1); c.foreR.rotation.set(0.22, 0, 0); c.foreL.rotation.set(0.22, 0, 0);
      if (o.vest === false) rig.vestOn = false;
      if (o.state) rig.dmg(o.state);
      let face = o.face || 'jack';
      if (o.clip) {
        CLIPS[o.clip].f(c, o.t, 1); a.clip = { name: o.clip, t: o.t, len: 9e9 };
        const F = PJ.data.clips[o.clip].face; for (const [ft, fn] of F) if (o.t >= ft && !o.face) face = fn;
      }
      rig.update(0, null);
      if (o.set) PJ.set(a, o.set);
      if (o.far) { rig.far = true; rig.vis(); }
      L.face.set(face); for (let k = 0; k < 30; k++) { L.face.blinkT = 9; L.face.update(0.05); }
      if (o.look) L.face.look = o.look;
      c.root.updateMatrixWorld(true);
      return { L, c, a, rig };
    };
    X.other = (id) => { const L = looks.buildLook(id); L.ch.head.rotation.z = 0; L.ch.arm.rotation.z = 0.1; L.ch.armL.rotation.z = -0.1; L.ch.foreR.rotation.x = 0.25; L.ch.foreL.rotation.x = 0.25; for (let k = 0; k < 30; k++) { L.face.blinkT = 9; L.face.update(0.05); } return L; };
    X.cell = (i, cols, rows, sc, cam, text, sub) => {
      const w = 1600 / cols, h = 900 / rows, x0 = (i % cols) * w, y0 = 900 - (Math.floor(i / cols) + 1) * h;
      cam.aspect = w / h; cam.updateProjectionMatrix();
      r.setScissorTest(true); r.autoClear = false; r.setViewport(x0, y0, w, h); r.setScissor(x0, y0, w, h); r.clear(); r.render(sc, cam);
      if (text) { const d = document.createElement('div'); d.textContent = text; d.style.cssText = `position:absolute;left:${x0 + 6}px;top:${Math.floor(i / cols) * h + 5}px;font:700 13px sans-serif;color:#ffe14d;background:rgba(18,8,24,.85);padding:1px 5px;border:2px solid #ff4fd8`; lab.append(d); }
      if (sub) { const d = document.createElement('div'); d.textContent = sub; d.style.cssText = `position:absolute;left:${x0 + 6}px;top:${Math.floor(i / cols) * h + h - 24}px;font:700 12px sans-serif;color:#4fd8ff;background:rgba(18,8,24,.85);padding:1px 5px`; lab.append(d); }
    };
    X.clear = () => { r.setScissorTest(false); r.setViewport(0, 0, 1600, 900); r.setClearColor(0x120818); r.clear(); lab.innerHTML = ''; };
    X.cam = (pos, at, fov = 30) => { const cam = new THREE.PerspectiveCamera(fov, 1, 0.05, 100); cam.position.set(...pos); cam.lookAt(...at); return cam; };
    X.orbit = (at, deg, dist, up = 0.12, fov = 30) => { const a = deg * Math.PI / 180; return X.cam([at[0] + Math.sin(a) * dist * Math.cos(up), at[1] + Math.sin(up) * dist, at[2] - Math.cos(a) * dist * Math.cos(up)], at, fov); }; // deg 0 = from his front
    X.placeTruck = (sc, c, clipPose = true) => { if (!truck) return null; const t = truck.clone(true); const p = new THREE.Vector3(); (window.PJX.lastPalm = p); return t; };
    const L0 = looks.buildLook('pallet_jack');
    return { got, blender: !!L0.blender, parts: Object.keys(L0.parts || {}), clips: PJ.clips, truck: !!truck };
  });
  console.log(JSON.stringify(init));
  const shot = async (name) => { await pg.waitForTimeout(150); const png = path.join(OUT, name + '.png'); await pg.screenshot({ path: png }); const jpg = path.join(OUT, name + '.jpg'); execSync(`ffmpeg -loglevel error -y -i "${png}" -q:v 3 "${jpg}"`); fs.unlinkSync(png); console.log('wrote', jpg); };
  const what = WHAT.split(',');

  if (what.includes('turn')) {
    await pg.evaluate(() => { const X = window.PJX, { THREE } = X; X.clear();
      const views = [['front', 0], ['three quarter', 35], ['his right side', 90], ['back', 180], ['his left side', -90], ['from above', 20]];
      views.forEach(([nm, deg], i) => {
        const sc = X.scene(0x2a1830, 5);
        const J = X.jack({ clip: 'pj_idle', t: 1.0 }); sc.add(J.c.root);
        const side = /side/.test(nm); // (side on, the other two would stand in front of him)
        if (!side) { const M = X.other('mannequin'); M.ch.root.position.set(1.6, 0, 0); sc.add(M.ch.root);
          const Lu = X.other('lumps'); Lu.ch.root.position.set(-1.95, 0, 0); sc.add(Lu.ch.root); }
        if (X.truck) { const t = X.truck.clone(true); const p = J.rig.at('palmL'); t.position.set(p.x, 0, p.z - 0.05); sc.add(t); }
        const cam = nm === 'from above' ? X.orbit([-0.1, 1.0, 0], deg, 8.0, 0.5) : side ? X.orbit([0, 1.08, 0], deg, 5.6, 0.06) : X.orbit([-0.1, 1.08, 0], deg, 7.5, 0.06);
        X.cell(i, 3, 2, sc, cam, i === 0 ? 'the mannequin (2.1 m)  ·  PALLET JACK (2.1 m, vest on, a hand on his truck)  ·  LUMPS (2.2 m)' : nm);
      }); });
    await shot('pj_game_turn');
  }
  if (what.includes('face')) {
    await pg.evaluate(() => { const X = window.PJX; X.clear();
      const cells = [['his resting face (jack)', 'jack', 0, 0.05], ['three quarter', 'jack', 32, 0.08], ['his right', 'jack', 90, 0.03], ['from his left: the broken nose', 'jack', -58, 0.06], ['from above', 'jack', 15, 0.5], ['from below (you are 40 kilos)', 'jack', -10, -0.35],
        ['grin', 'grin', 20, 0.05], ['the rig is up (jack_set)', 'jack_set', 20, 0.05], ['run through (jack_hurt)', 'jack_hurt', 20, 0.05], ['he breaks it (jack_mad)', 'jack_mad', 20, 0.05], ['shock', 'shock', 20, 0.05], ['after (jack_gone)', 'jack_gone', 20, 0.05]];
      cells.forEach(([nm, face, deg, up], i) => { const sc = X.scene(0x2a1830, 3); const J = X.jack({ face, vest: i < 6 }); sc.add(J.c.root);
        const hp = new X.THREE.Vector3(); J.c.head.getWorldPosition(hp); hp.y += 0.17; X.cell(i, 6, 2, sc, X.orbit([hp.x, hp.y, hp.z], deg, 1.55, up, 26), nm); }); });
    await shot('pj_game_face');
  }
  // a close-up aims at a marker (+ an offset in metres): [label, jack options, marker or [x, y, z], offset, deg, distance, up]
  const closeups = async (cells, cols, rows, file) => {
    await pg.evaluate(([cells, cols, rows]) => { const X = window.PJX; X.clear();
      cells.forEach(([nm, o, mk, off, deg, d, up], i) => { const sc = X.scene(0x2a1830, 4); const J = X.jack(o); sc.add(J.c.root);
        const p = Array.isArray(mk) ? new X.THREE.Vector3(...mk) : J.rig.at(mk); p.x += off[0]; p.y += off[1]; p.z += off[2];
        X.cell(i, cols, rows, sc, X.orbit([p.x, p.y, p.z], deg, d, up), nm); }); }, [cells, cols, rows]);
    await shot(file);
  };
  const full = [0, 1.1, 0], Z = [0, 0, 0];
  if (what.includes('dmg')) {
    const nv = { vest: false }, rt = { vest: false, state: 'run_through', face: 'jack_hurt' }, ab = { vest: false, state: 'armour_broken', face: 'jack_hurt' }, mt = { vest: false, state: 'marrow_taken', face: 'jack_gone' };
    await closeups([['fresh, vest off', nv, full, Z, 25, 7.8, 0.08], ['fresh, vest off: back', nv, full, Z, 205, 7.8, 0.08],
      ['run_through', rt, full, Z, 28, 7.8, 0.08], ['run_through: back', rt, full, Z, 208, 7.8, 0.08], ['run_through: his right side', rt, [0, 1.25, 0], Z, 90, 5.6, 0.05],
      ['the hole under his ribs', rt, 'woundAt', [0, 0, -0.1], 30, 2.2, 0.12], ['what is left of it in front', rt, 'armFrontEnd', [0, 0.05, 0.1], -50, 1.9, 0.2], ['the boiler split, its hand out of his back', rt, 'ventAt', [0, 0.02, 0.1], 205, 2.3, 0.18],
      ['armour_broken', ab, full, Z, 28, 7.8, 0.08], ['armour_broken: back', ab, full, Z, 212, 7.8, 0.08], ['collarbone weld sprung', ab, 'weldAt', [0.04, 0, -0.05], 18, 1.6, 0.22],
      ['shin locks blown', ab, [0, 0.2, -0.1], Z, 25, 1.9, 0.15], ['stacks bent', ab, 'boilerAt', [0, 0.55, 0.05], 200, 2.9, 0.4],
      ['marrow_taken: back', mt, full, Z, 185, 7.8, 0.08], ['the boiler opened, the gap in his spine', mt, 'boilerAt', [0, 0, 0], 181, 1.75, 0.1], ['marrow_taken: from his left', mt, 'boilerAt', [0, 0, -0.05], 225, 2.2, 0.2],
      ['far LOD (past 28 m), vest on', { far: true }, full, Z, 25, 7.8, 0.08], ['far LOD at 30 m', { far: true }, full, Z, 25, 30, 0.05]], 6, 3, 'pj_game_damage');
  }
  if (what.includes('parts')) {
    const up = { rig: 1, flap: 1, cock: 1 }, nv = { vest: false };
    await closeups([['the boiler: a beer keg. fire door, relief valve', {}, 'boilerAt', [0, 0, 0], 180, 2.0, 0.1], ['gauge, manifold, his left stack', {}, 'gaugeAt', [0, 0, 0.05], 222, 1.5, 0.35], ['bleed valve, level glass', {}, 'bleedAt', [0, 0.08, 0.02], 140, 1.5, 0.1],
      ['stacks at rest: down, caps shut', nv, 'boilerAt', [0, 0.62, 0.05], 185, 2.5, 0.4], ['rig up: stacks risen, caps open', { vest: false, set: up }, 'boilerAt', [0, 0.62, 0.05], 185, 2.5, 0.4], ['the welded collarbone', nv, 'weldAt', [0, 0, -0.05], 10, 1.7, 0.22],
      ['the launcher forearm: collar forward', nv, 'fistAt', [0, 0.2, 0], 62, 1.45, 0.1], ['cocked: the collar back up the barrel', { vest: false, set: up }, 'fistAt', [0, 0.2, 0], 62, 1.45, 0.1], ['knuckles: bare steel', {}, 'fistAt', [0, 0.02, 0], 25, 1.2, -0.25],
      ['the exhaust bell behind his elbow', {}, 'elbowAt', [0, -0.05, 0], 140, 1.5, 0.25], ['piston shin: lock open', {}, [0.21, 0.2, -0.08], Z, 35, 1.25, 0.12], ['rig up: lock snapped shut', { set: up }, [0.21, 0.2, -0.08], Z, 35, 1.25, 0.12],
      ['a shin from the side: daylight through it', {}, [0.21, 0.24, -0.02], Z, 90, 1.7, 0.05], ['plate under scar, hydraulic lines', nv, 'armL', [0, -0.12, 0], -72, 1.6, 0.2], ['MARSH DELIVERIES', {}, 'boilerAt', [0, 0.36, -0.1], 180, 1.5, 0.12],
      ['tea towel, belt, keys', {}, 'boilerAt', [0.1, -0.42, -0.1], 200, 1.9, 0.05], ['THIS WAY UP, rubber bands', {}, 'foreL', [0, -0.18, 0], -90, 1.25, 0.05], ['the open hand', {}, 'palmL', [0, 0, 0], -150, 1.1, 0.1]], 6, 3, 'pj_game_parts');
  }
  const POSES = [['pj_idle', 1.0, 35, 'fresh', true], ['pj_idle_eating', 1.85, 40, 'fresh', false], ['pj_walk_load', 1.0, 35, 'fresh', false], ['pj_kneel_vest', 3.7, 50, 'fresh', false], ['pj_rig_up', 2.12, 35, 'fresh', false], ['pj_fight_idle', 0.5, 35, 'fresh', false],
    ['pj_rocket_punch', 0.44, 60, 'fresh', false], ['pj_rocket_punch', 0.56, 60, 'fresh', false], ['pj_block', 0.4, 35, 'fresh', false], ['pj_stagger', 0.3, 60, 'fresh', false], ['pj_impaled', 1.2, 60, 'run_through', false], ['pj_impaled', 3.6, 40, 'run_through', false],
    ['pj_break_it', 2.95, 40, 'run_through', false], ['pj_land_kneel', 0.6, 50, 'run_through', false], ['pj_stand_anyway', 3.3, 35, 'run_through', false], ['pj_fight_idle_hurt', 1.0, 35, 'run_through', false], ['pj_armour_break_fall', 0.2, 60, 'armour_broken', false], ['pj_armour_break_fall', 2.2, 50, 'armour_broken', false],
    ['pj_dying_talk', 2.6, 45, 'armour_broken', false], ['pj_dying_talk', 4.6, 45, 'armour_broken', false], ['pj_last_breath', 3.6, 45, 'armour_broken', false], ['pj_carried', 0, 60, 'marrow_taken', false]];
  const STATE = Object.fromEntries(POSES.map((p) => [p[0], p[3]]));
  if (what.includes('poses')) {
    await pg.evaluate((POSES) => { const X = window.PJX; X.clear();
      POSES.forEach(([clip, t, deg, state, vest], i) => { const sc = X.scene(0x2a1830, 4); const J = X.jack({ clip, t, state, vest }); sc.add(J.c.root);
        if (clip === 'pj_idle' && X.truck) { const tr = X.truck.clone(true); const p = J.rig.at('palmL'); tr.position.set(p.x, 0, p.z - 0.05); sc.add(tr); }
        const hips = new X.THREE.Vector3(); J.c.spine.getWorldPosition(hips);
        X.cell(i, 8, 3, sc, X.orbit([hips.x, Math.max(0.8, hips.y * 0.75 + 0.3), hips.z], deg, 6.9, 0.1), clip.slice(3) + ' @' + t); }); }, POSES);
    await shot('pj_game_poses');
  }
  if (what.includes('clips')) {
    const clips = init.clips.filter((c) => !ONLY || ONLY.split(',').includes(c));
    for (const clip of clips) {
      await pg.evaluate(([clip, state]) => { const X = window.PJX, C = X.PJ.data.clips[clip]; X.clear();
        const len = C.len || C.loop || C.keys[C.keys.length - 1].t || 1, N = 12;
        const ts = Array.from({ length: N }, (_, i) => +(len * i / (N - 1)).toFixed(2));
        for (const [mt] of C.marks) { let bi = 1, bd = 9; ts.forEach((t, i) => { if (i > 0 && i < N - 1 && Math.abs(t - mt) < bd) { bd = Math.abs(t - mt); bi = i; } }); if (mt > 0 && mt < len) ts[bi] = +(mt + 0.02).toFixed(2); } // the marks get a frame each
        ts.sort((a, b) => a - b);
        const deg = /eating|kneel|dying|last|carried|fall/.test(clip) ? 55 : 40;
        ts.forEach((t, i) => { const sc = X.scene(0x2a1830, 5);
          const st = /impaled/.test(clip) ? (t >= 0.05 ? 'run_through' : 'fresh') : /armour_break/.test(clip) ? (t >= 0.06 ? 'armour_broken' : 'run_through') : state;
          const J = X.jack({ clip, t, state: st, vest: /idle$|kneel_vest|walk_load/.test(clip) && !(clip === 'pj_kneel_vest' && t >= 1.75) }); sc.add(J.c.root);
          if (clip === 'pj_idle' && X.truck) { const tr = X.truck.clone(true); const J0 = X.jack({ clip, t: 0 }); const p = J0.rig.at('palmL'); tr.position.set(p.x, 0, p.z - 0.05); sc.add(tr); }
          const mk = C.marks.filter(([mt]) => Math.abs(mt + 0.02 - t) < 0.011).map((m) => m[1]).join(' ');
          const sit = /eating|dying|last|carried/.test(clip), high = /impaled|break_it|land_kneel/.test(clip); // (sat on the deck / a metre off it)
          X.cell(i, 6, 2, sc, X.orbit([0, high ? 1.5 : sit ? 0.85 : 1.0, 0.1], deg, high ? 8.8 : sit ? 6.4 : 7.6, 0.1), (i === 0 ? clip + '   ' : '') + t.toFixed(2) + ' s', mk ? 'mark: ' + mk : ''); }); }, [clip, STATE[clip] || 'fresh']);
      await shot('pj_clip_' + clip.slice(3));
    }
  }
  console.log(errs.length ? 'ERRORS:\n' + [...new Set(errs)].join('\n') : 'no errors');
  await b.close();
})();
