// MR. OVERTIME's hitboxes for the combat referee (it runs in a worker, no meshes): measures the dressed Blender model in
// the game at its real size (root scale 2.5, metres, root space: feet at 0, front = -z) and writes
// public/models/cast/c_overtime.parts.json = { scale, parts: { name: { joint, c, h } }, body: { r, h }, markers,
// marks: { clip: { mark: s } }, clips: { clip: { t: [...], body_dy: [...], gunR: [[x, y, z]...] } } }
// usage: node tools/blender/cast/otparts.cjs [port]   (rerun after changing the model or a clip's timing)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const PORT = process.argv[2] || 3000;
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage();
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.goto(`http://localhost:${PORT}/`);
  const out = await pg.evaluate(async () => {
    const THREE = await import('three');
    const looks = await import('/js/story/looks.js');
    const { CLIPS } = await import('/js/story/actors.js');
    const { MARKS } = await import('/js/story/overtime.js');
    const got = await looks.loadCast(['overtime'], 20000);
    const L = looks.buildLook('overtime'), ch = L.ch;
    ch.head.rotation.z = 0; ch.root.updateMatrixWorld(true);
    const r3 = (v) => v.toArray().map((x) => +x.toFixed(3));
    const box = (o) => new THREE.Box3().setFromObject(o);
    const JOINT = { plate: 'spine', heart: 'spine', slot: 'spine', card: 'spine', tie: 'spine', cables: 'spine', gunR: 'foreR', gunL: 'foreL', head: 'head' };
    const parts = {};
    for (const [k, j] of Object.entries(JOINT)) {
      const g = L.parts && L.parts[k]; if (!g) continue;
      const bx = box(g); if (bx.isEmpty()) continue;
      parts[k] = { joint: j, c: r3(bx.getCenter(new THREE.Vector3())), h: r3(bx.getSize(new THREE.Vector3()).multiplyScalar(0.5)) };
    }
    // the body capsule: everything but the far LOD and the damage pieces
    const all = new THREE.Box3();
    ch.root.traverse((o) => { if (!o.isMesh) return; let p = o, skip = false; while (p) { if (p.name === 'ot_lod' || /^ot_dmg/.test(p.name)) skip = true; p = p.parent; } if (!skip) all.expandByObject(o); });
    const sz = all.getSize(new THREE.Vector3());
    const body = { r: +(Math.max(sz.x, sz.z) * 0.36).toFixed(3), h: +sz.y.toFixed(3), c: r3(all.getCenter(new THREE.Vector3())) };
    const markers = {};
    for (const k of ['muzzleR', 'muzzleL', 'tieEnd']) if (L.parts && L.parts[k]) markers[k] = r3(L.parts[k].getWorldPosition(new THREE.Vector3()));
    // marks: clip -> { name: seconds } (repeated names get numbered: clack1, clack2...)
    const marks = {};
    for (const [clip, list] of Object.entries(MARKS)) {
      if (!list.length || !clip.startsWith('ot_')) continue;
      const n = {}, m = {};
      for (const [t, k] of list) { n[k] = (n[k] || 0) + 1; }
      const c2 = {};
      for (const [t, k] of list) { c2[k] = (c2[k] || 0) + 1; m[n[k] > 1 ? k + c2[k] : k] = t; }
      marks[clip] = m;
    }
    // clips that move him a lot: the hips' height and the right stapler's centre at each mark (and the start)
    const clips = {};
    const rest = (fresh) => { fresh.ch.root.updateMatrixWorld(true); };
    for (const clip of ['ot_staple', 'ot_fan', 'ot_slam', 'ot_punchin', 'ot_coffee', 'ot_kneel', 'ot_clockout']) {
      const len = CLIPS[clip].len < 100 ? CLIPS[clip].len : 3.5, ts = [...new Set([...Array.from({ length: Math.round(len / 0.2) + 1 }, (_, i) => +(i * 0.2).toFixed(2)), ...Object.values(marks[clip] || {})])].sort((x, y) => x - y);
      const row = { t: [], body_dy: [], gunR: [] };
      for (const t of ts) {
        const F = looks.buildLook('overtime'), c = F.ch; c.head.rotation.z = 0;
        CLIPS[clip].f(c, t, 1); rest(F);
        const hips = c.body.getWorldPosition(new THREE.Vector3()).y;
        const g = F.parts && F.parts.gunR ? box(F.parts.gunR).getCenter(new THREE.Vector3()) : c.foreR.getWorldPosition(new THREE.Vector3());
        row.t.push(+t.toFixed(3)); row.body_dy.push(+hips.toFixed(3)); row.gunR.push(r3(g));
      }
      const h0 = row.body_dy[0]; row.body_dy = row.body_dy.map((y) => +(y - h0).toFixed(3));
      clips[clip] = row;
    }
    return { v: 1, model: 'c_overtime.glb', blender: !!L.blender, got, scale: ch.root.scale.x, units: 'metres, root space at rest, feet at y 0, front -z', parts, body, markers, marks, clips };
  });
  const file = path.join(__dirname, '../../../public/models/cast/c_overtime.parts.json');
  fs.writeFileSync(file, JSON.stringify(out, null, 1));
  console.log(Object.keys(out.parts).join(' '), '| body', JSON.stringify(out.body), '| blender', out.blender, errs.join('\n') || 'no errors');
  await b.close();
})();
