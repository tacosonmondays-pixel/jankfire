// dump the story cast's rest-pose skeletons (public/js/story/looks.js) so the Blender cast scripts can build each body
// part exactly where its joint is: node tools/blender/cast/joints.cjs [port] -> tools/blender/cast/joints.json
// positions are root space (game coords, root scale 1), plus the code face rig's anchors (eyes, mouth, head radii)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const PORT = process.argv[2] || 3000;
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage();
  await pg.goto(`http://localhost:${PORT}/`);
  const out = await pg.evaluate(async () => {
    const THREE = await import('three');
    const { buildLook, LOOK_IDS } = await import('/js/story/looks.js');
    const res = {};
    for (const id of LOOK_IDS) {
      const L = buildLook(id), ch = L.ch, s = ch.root.scale.x;
      ch.root.scale.setScalar(1); ch.head.rotation.z = 0; ch.root.updateMatrixWorld(true); // (no random head tilt: the game tilts the whole dressed head)
      const wp = (o) => { const v = new THREE.Vector3(); o.getWorldPosition(v); return [+v.x.toFixed(4), +v.y.toFixed(4), +v.z.toFixed(4)]; };
      const J = {}, M = {};
      for (const k of ['body', 'legL', 'legR', 'kneeL', 'kneeR', 'spine', 'neck', 'head', 'armL', 'arm', 'foreL', 'foreR', 'handL', 'handR']) if (ch[k]) { J[k] = wp(ch[k]); M[k] = ch[k].matrixWorld.elements.map((x) => +x.toFixed(6)); }
      const F = L.face ? { eyes: L.face.eyes.map((e) => wp(e.piv)), eyeR: L.face.eyes[0] && L.face.eyes[0].ball.geometry.parameters.radius, mouth: wp(L.face.mouth), mouthW: L.face.mw } : null;
      const box = new THREE.Box3().setFromObject(ch.head);
      res[id] = { scale: s, kind: L.kind, joints: J, mats: M, face: F, headBox: [box.min.toArray().map((x) => +x.toFixed(4)), box.max.toArray().map((x) => +x.toFixed(4))], hunch: ch.spine.rotation.x, legScale: ch.legL.scale.x };
    }
    return res;
  });
  fs.writeFileSync(path.join(__dirname, 'joints.json'), JSON.stringify(out, null, 1));
  console.log(Object.keys(out).join(', '));
  await b.close();
})();
