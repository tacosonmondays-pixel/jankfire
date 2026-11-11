// dump MADAM CHAIR's rest skeleton (public/js/story/hatlook.js) into tools/blender/cast/joints.json: the 14 cast joints
// plus her own (the hat, its brim, the lids, the fingers). only her entry is written: everyone else's stays as it was.
//   node tools/blender/cast/hljoints.cjs <port>
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
    const { buildLookCode } = await import('/js/story/looks.js');
    const { EXTRA } = await import('/js/story/hatlook.js');
    const L = buildLookCode('hat_lord'), ch = L.ch, s = ch.root.scale.x;
    ch.root.scale.setScalar(1); ch.head.rotation.z = 0; ch.root.updateMatrixWorld(true);
    const wp = (o) => { const v = new THREE.Vector3(); o.getWorldPosition(v); return [+v.x.toFixed(4), +v.y.toFixed(4), +v.z.toFixed(4)]; };
    const J = {}, M = {}, P = {}, LOC = {};
    const base = ['body', 'legL', 'legR', 'kneeL', 'kneeR', 'spine', 'neck', 'head', 'armL', 'arm', 'foreL', 'foreR', 'handL', 'handR'];
    const par = { body: null, legL: 'body', legR: 'body', kneeL: 'legL', kneeR: 'legR', spine: 'body', neck: 'spine', head: 'neck', armL: 'spine', arm: 'spine', foreL: 'armL', foreR: 'arm', handL: 'foreL', handR: 'foreR' };
    for (const e of EXTRA) par[e[0]] = e[1];
    for (const k of base.concat(EXTRA.map((e) => e[0]))) { J[k] = wp(ch[k]); M[k] = ch[k].matrixWorld.elements.map((x) => +x.toFixed(6)); P[k] = par[k];
      LOC[k] = { p: ch[k].position.toArray().map((x) => +x.toFixed(5)), r: [ch[k].rotation.x, ch[k].rotation.y, ch[k].rotation.z].map((x) => +x.toFixed(5)), s: +ch[k].scale.x.toFixed(5) }; }
    const F = { eyes: L.face.eyes.map((e) => wp(e.piv)), eyeR: L.face.eyes[0].ball.geometry.parameters.radius, mouth: wp(L.face.mouth), mouthW: L.face.mw };
    const box = new THREE.Box3().setFromObject(ch.head);
    return { scale: s, kind: L.kind, joints: J, mats: M, parents: P, local: LOC, order: base.concat(EXTRA.map((e) => e[0])), face: F, headBox: [box.min.toArray().map((x) => +x.toFixed(4)), box.max.toArray().map((x) => +x.toFixed(4))], hunch: ch.spine.rotation.x, legScale: ch.legL.scale.x };
  });
  const f = path.join(__dirname, 'joints.json'), all = JSON.parse(fs.readFileSync(f, 'utf8'));
  all.hat_lord = out;
  fs.writeFileSync(f, JSON.stringify(all, null, 1));
  console.log('hat_lord:', out.order.length, 'joints, head', out.joints.head, 'hat', out.joints.hat, errs.join('\n') || 'no errors');
  await b.close();
})();
