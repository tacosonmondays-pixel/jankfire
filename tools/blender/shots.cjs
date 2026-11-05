// In-game screenshots of the Blender models next to the code-built ones they replace.
// usage: node tools/blender/shots.cjs <port> <outDir> [weapons=ar,shotgun,revolver] [presets=3,0]
//   (start the server first: PORT=<port> node server.js)
// writes <outDir>/<preset>_<weapon>_<glb|code>_<hip|ads>.png and <outDir>/<preset>_lineup.png
// (the lineup is code model on top, Blender model under it, in the game's own lights and render preset)
const { chromium } = require('playwright');
const [port = '3100', out = '.', list = 'ar,shotgun,revolver', presets = '3,0'] = process.argv.slice(2);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const SECONDARY = new Set(['revolver', 'marbles', 'cig', 'blower', 'cards', 'snowball', 'bloodcross']);
const weapons = list.split(',');

async function session(b, jank, useGlb) {
  const pg = await b.newPage({ viewport: { width: 960, height: 600 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  if (!useGlb) await pg.route('**/models/list', (r) => r.fulfill({ contentType: 'application/json', body: '[]' }));
  await pg.addInitScript((jank) => localStorage.setItem('jankfire', JSON.stringify({ name: 'shots', killcam: false, jank })), jank);
  await pg.goto(`http://localhost:${port}/`); await sleep(1500);
  await pg.click('#scr-main [data-mode="training"]'); await sleep(2500);
  await pg.evaluate(async () => { const { ME } = await import('/js/player.js'); window.__h = setInterval(() => { ME.pitch = -0.05; ME.yaw = 0.6; ME.vel = [0, 0, 0]; }, 10); });
  return { pg, errs };
}

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  for (const jank of presets.split(',').map(Number)) {
    const tag = ['potato', 'crusty', 'mid', 'toohd'][jank];
    for (const useGlb of [false, true]) {
      const { pg, errs } = await session(b, jank, useGlb);
      for (const id of weapons) {
        const slot = SECONDARY.has(id) ? 'secondary' : 'primary';
        await pg.evaluate(async ([id, slot]) => {
          const w = await import('/js/weapons.js');
          const lo = { primary: 'ar', secondary: 'cards', melee: 'knife' }; lo[slot] = id;
          w.setLoadout(lo); w.switchSlot(slot === 'primary' ? 1 : 0); w.switchSlot(slot === 'primary' ? 0 : 1);
        }, [id, slot]);
        await sleep(900);
        const name = `${out}/${tag}_${id}_${useGlb ? 'glb' : 'code'}`;
        await pg.screenshot({ path: `${name}_hip.png` });
        await pg.evaluate(async () => { const { W } = await import('/js/weapons.js'); W.aimHeld = true; });
        await sleep(700);
        await pg.screenshot({ path: `${name}_ads.png` });
        await pg.evaluate(async () => { const { W } = await import('/js/weapons.js'); W.aimHeld = false; });
        await sleep(300);
      }
      if (useGlb) { // lineup: every weapon as the code builds it (top) and from Blender (bottom), side on, game lights
        const png = await pg.evaluate(async ([weapons, jank]) => {
          const THREE = await import('three');
          const { buildWeapon } = await import('/js/models.js');
          const { AUTHORED } = await import('/js/glbkit.js');
          const { G } = await import('/js/ctx.js');
          const W = 1280, H = 300 * 2;
          const scale = [0.22, 0.36, 0.6, 1][jank];
          const r = new THREE.WebGLRenderer({ antialias: jank === 3 }); r.setSize(Math.floor(W * scale), Math.floor(H * scale), false);
          r.setClearColor(0x3a3048);
          const sc = new THREE.Scene();
          sc.add(new THREE.HemisphereLight(0xcfe8ff, 0x7a4a6a, 1.8));
          const sun = new THREE.DirectionalLight(0xffffff, 1.5); sun.position.set(2, 3, 4); sc.add(sun);
          const cam = new THREE.OrthographicCamera(-W / 2, W / 2, H / 2, -H / 2, 0.01, 100); cam.position.set(0, 0, 10); cam.zoom = 300; cam.updateProjectionMatrix();
          let x = -W / 2 / 300 + 0.15;
          for (const id of weapons) {
            const len = 1.25;
            const keep = AUTHORED['w_' + id]; delete AUTHORED['w_' + id];
            const a = buildWeapon(id); if (keep) AUTHORED['w_' + id] = keep;
            const bb = buildWeapon(id);
            for (const [g, y] of [[a, 0.45], [bb, -0.5]]) {
              g.rotation.y = -Math.PI / 2;
              g.position.set(x + len / 2 + 0.0, y, 0);
              sc.add(g);
            }
            x += Math.min(len, 1.35) * (id === 'revolver' ? 0.45 : 1);
          }
          r.render(sc, cam);
          const url = r.domElement.toDataURL('image/png');
          r.dispose();
          return url;
        }, [weapons, jank]);
        require('fs').writeFileSync(`${out}/${tag}_lineup.png`, Buffer.from(png.split(',')[1], 'base64'));
      }
      console.log(tag, useGlb ? 'glb' : 'code', errs.join('\n') || 'no errors');
      await pg.close();
    }
  }
  await b.close();
})();
