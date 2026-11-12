// eye probe: the real actor code (actors.js + face.js), stepped at 60 fps; per look (the Blender model and the code
// puppet), with you standing 2.4 m in front: how far each eye points off you (mean / worst, deg), how far apart the two
// eyes point (convergence: a couple of degrees at that range, ~60 was cross-eyed), the biggest jump of an eye in one
// frame (the puppets' 12 fps steps), and how far the two eyes drift apart up / down at rest.
//   node tools/blender/cast/eyeprobe.cjs <port> [ids]
const { chromium } = require('playwright');
const [PORT = 3115, IDS = 'gordo,lumps,sharon,bev,dot,mina,pallet_jack,auntie,choir,choir_b,dale,dumpling,eotm,sister_agenda,intern,overtime,mannequin,gen_normal,gen_puppet'] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 400, height: 300 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.goto(`http://localhost:${PORT}/`); await pg.waitForTimeout(800);
  const out = await pg.evaluate(async (ids) => {
    const THREE = await import('three');
    const looks = await import('/js/story/looks.js'); const A = await import('/js/story/actors.js'); const { G } = await import('/js/ctx.js');
    const real = ids.filter((i) => !i.startsWith('gen_'));
    await looks.loadCast(real, 30000);
    const sc = new THREE.Scene(); const g0 = G.scene; G.scene = sc;
    const res = {};
    const fwd = new THREE.Vector3(), q = new THREE.Quaternion(), p = new THREE.Vector3(), d = new THREE.Vector3();
    const deg = (r) => +(r * 180 / Math.PI).toFixed(1);
    for (const id of ids) {
      for (const mode of ['glb', 'code']) {
        if (mode === 'glb' && (id.startsWith('gen_') || !looks.castLoaded(id))) continue;
        const def = id === 'gen_normal' ? { look: 'zz_someone', hint: { body: 'normal', desc: '' } } : id === 'gen_puppet' ? { look: 'zz_offspec', hint: { body: 'puppet', desc: 'huge head' } } : { look: id };
        let a;
        A.clearActors();
        if (mode === 'code' && looks.castLoaded(id)) { a = A.spawnActor('p', { ...def, voice: { kind: 'chirp' } }, [0, 0, 0], 0); const L = looks.buildLookCode(id); sc.remove(a.ch.root); // (the code puppet in the same actor, for a side-by-side)
          a.L = L; a.ch = L.ch; a.face = L.face; a.r.ch = L.ch; a.puppet = L.kind === 'puppet'; sc.add(L.ch.root); }
        else a = A.spawnActor('p', { ...def, voice: { kind: 'chirp' } }, [0, 0, 0], 0);
        a.pos[1] = 0; a.home.p = a.pos.slice();
        if (!a.face || !a.face.eyes.length || !a.face.eyes[0].piv.visible) { res[id + ':' + mode] = { noEyes: true }; continue; }
        a.ch.root.updateMatrixWorld(true);
        const hp = new THREE.Vector3(); a.ch.head.getWorldPosition(hp);
        A.updateActors(1 / 60, 0, null); a.ch.root.updateMatrixWorld(true); const ey = a.face.eyes[0].piv.getWorldPosition(new THREE.Vector3()).y;
        const eye = [0.9, ey + 0.25, -2.2]; // the player: front-right, a bit above, 2.4 m
        const T = new THREE.Vector3(...eye);
        const meas = () => a.face.eyes.map((e) => { e.piv.getWorldQuaternion(q); fwd.set(0, 0, -1).applyQuaternion(q); e.piv.getWorldPosition(p); d.copy(T).sub(p).normalize(); return { err: fwd.angleTo(d), dir: fwd.clone(), yaw: e.piv.rotation.y, pitch: e.piv.rotation.x }; });
        let t = 0, worst = 0, sum = 0, n = 0, jit = 0, prev = null, conv = [], maxStep = 0;
        a.blinkOff = true;
        for (let i = 0; i < 180; i++) { // 3 s at 60 fps, the player standing there
          t += 1 / 60; a.face.blinkT = 9; A.updateActors(1 / 60, t * 1000, eye);
          if (i >= 90) { const m = meas(); for (const e of m) { worst = Math.max(worst, e.err); sum += e.err; n++; }
            const c = m[0].dir.angleTo(m[1].dir); conv.push(c);
            if (prev) maxStep = Math.max(maxStep, ...m.map((e, k) => e.dir.angleTo(prev[k].dir)));
            prev = m; }
        }
        const m = meas();
        // rest: nobody near, 4 s: vertical misalignment between the eyes
        let vmis = 0; A.clearActors(); sc.add(a.ch.root); a.face.look = null;
        for (let i = 0; i < 240; i++) { t += 1 / 60; a.face.blinkT = 9; a.face.look = null; a.face.update(1 / 60); const mm = a.face.eyes.map((e) => e.piv.rotation.x); vmis = Math.max(vmis, Math.abs(mm[0] - mm[1])); }
        res[id + ':' + mode] = { kind: a.L.kind, blender: !!a.L.blender, meanErr: deg(sum / n), worstErr: deg(worst), lastYaw: m.map((e) => deg(e.yaw)), lastPitch: m.map((e) => deg(e.pitch)), convergeMax: deg(Math.max(...conv)), maxFrameStep: deg(maxStep), restVertMisalign: deg(vmis) };
      }
    }
    G.scene = g0; return res;
  }, IDS.split(','));
  for (const [k, v] of Object.entries(out)) console.log(k.padEnd(22), JSON.stringify(v));
  console.log(errs.join('\n') || 'no errors'); await b.close();
})();
