// Thrown things (and the floor peel) side by side: the code-built one on top, the Blender one under it, in the game's lights.
// usage: node tools/blender/shots_proj.cjs <port> <outDir> [kinds=chicken,bowling,banana,peel,frag,smokegren,card,slipper,duck,snowball,bow] [presets=3,0]
//   a skin's own thrown one is kind:model (slipper:slipper_croc). writes <outDir>/<preset>_projectiles.png
//   (start the server first: PORT=<port> node server.js)
const { chromium } = require('playwright');
const [port = '3100', out = '.', list = 'chicken,bowling,banana,peel,frag,smokegren,card,slipper,duck,snowball,bow', presets = '3,0'] = process.argv.slice(2);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  let bad = 0;
  for (const jank of presets.split(',').map(Number)) {
    const tag = ['potato', 'crusty', 'mid', 'toohd'][jank];
    const pg = await b.newPage({ viewport: { width: 960, height: 600 } });
    const errs = [];
    pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message));
    pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await pg.addInitScript((jank) => localStorage.setItem('jankfire', JSON.stringify({ name: 'shots', killcam: false, jank })), jank);
    await pg.goto(`http://localhost:${port}/`); await sleep(2500);
    const res = await pg.evaluate(async ([kinds, jank]) => {
      const THREE = await import('three');
      const k = await import('/js/glbkit.js');
      for (const e of kinds) if (e.includes(':')) k.authored('pj_' + e.split(':')[1]); // skins' thrown ones load on first use
      for (let i = 0; i < 150 && k.lateBusy(); i++) await new Promise((r) => setTimeout(r, 100));
      const { buildProjectile, buildPeel, tipColor, M } = await import('/js/models.js');
      const { AUTHORED } = await import('/js/glbkit.js');
      const W = 1600, H = 640;
      const scale = [0.22, 0.36, 0.6, 1][jank];
      const r = new THREE.WebGLRenderer({ antialias: jank === 3 }); r.setSize(Math.floor(W * scale), Math.floor(H * scale), false);
      r.setClearColor(0x3a3048);
      const sc = new THREE.Scene();
      sc.add(new THREE.HemisphereLight(0xcfe8ff, 0x7a4a6a, 1.8));
      const sun = new THREE.DirectionalLight(0xffffff, 1.5); sun.position.set(2, 3, 4); sc.add(sun);
      const make = (e) => {
        const [k, model] = e.split(':');
        if (k === 'peel') return buildPeel();
        const g = buildProjectile(k, model ? ['default', 'none', 'none', model, 'normal'] : undefined);
        if (k === 'bow' && g.userData.tip) g.userData.tip.material = M(tipColor('explosive'), true); // the tip shows the arrow type
        return g;
      };
      const row = [], info = [];
      for (const e of kinds) {
        const [k, model] = e.split(':'), key = k === 'peel' ? 'pj_peel' : 'pj_' + (model || k);
        const keep = AUTHORED[key], keepK = AUTHORED['pj_' + k]; delete AUTHORED[key]; delete AUTHORED['pj_' + k];
        const a = make(e); if (keep) AUTHORED[key] = keep; if (keepK) AUTHORED['pj_' + k] = keepK;
        const bb = make(e);
        info.push(`${e}: ${bb.userData.glb === 'blender' || bb.children.some((c) => c.userData.glbId) ? 'blender' : 'code'}${k === 'bow' ? (bb.userData.tip ? ' (tip ok)' : ' (NO TIP)') : ''}`);
        const bs = [a, bb].map((g) => new THREE.Box3().setFromObject(g));
        row.push({ a, bb, bs, len: Math.max(0.3, ...bs.map((x) => Math.max(x.max.x - x.min.x, x.max.z - x.min.z))) + 0.15, tall: Math.max(...bs.map((x) => x.max.y - x.min.y)) });
      }
      const total = row.reduce((t, q) => t + q.len, 0) + 0.2, tall = Math.max(0.5, ...row.map((q) => q.tall));
      const zoom = Math.min(400, W / total, H / (2 * tall + 0.3));
      const cam = new THREE.OrthographicCamera(-W / 2, W / 2, H / 2, -H / 2, 0.01, 100); cam.position.set(4, 3, 10); cam.lookAt(0, 0, 0); cam.zoom = zoom; cam.updateProjectionMatrix();
      const right = new THREE.Vector3(1, 0, 0).applyQuaternion(cam.quaternion), up = new THREE.Vector3(0, 1, 0).applyQuaternion(cam.quaternion);
      let x = -W / 2 / zoom + 0.1;
      for (const q of row) {
        [[q.a, q.bs[0], H / 4 / zoom], [q.bb, q.bs[1], -H / 4 / zoom]].forEach(([g, bx, y]) => {
          const c = bx.getCenter(new THREE.Vector3());
          g.position.copy(right.clone().multiplyScalar(x + q.len / 2)).add(up.clone().multiplyScalar(y)).sub(c);
          g.rotation.y = 0.5; // a three-quarter look: nose (-z) to the left
          sc.add(g);
        });
        x += q.len;
      }
      r.render(sc, cam);
      const url = r.domElement.toDataURL('image/png');
      r.dispose();
      return { url, info };
    }, [list.split(','), jank]);
    require('fs').writeFileSync(`${out}/${tag}_projectiles.png`, Buffer.from(res.url.split(',')[1], 'base64'));
    console.log(tag, res.info.join(', '), errs.length ? '\n' + errs.join('\n') : '(no page errors)');
    bad += errs.length;
    await pg.close();
  }
  await b.close();
  process.exitCode = bad ? 1 : 0;
})();
