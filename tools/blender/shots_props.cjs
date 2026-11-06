// In-game screenshots of the Blender props on real maps, next to the box versions they replace.
// usage: node tools/blender/shots_props.cjs <port> <outDir> [presets=3,0]   (server running: PORT=<port> node server.js)
// writes <outDir>/<preset>_<view>_<glb|code>.png and <preset>_showcase.png (every prop in a row on the range)
const { chromium } = require('playwright');
const [port = '3100', out = '.', presets = '3,0'] = process.argv.slice(2);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
// [name, map, eye position, look-at point]
const VIEWS = [
  ['wh_forklift', 'warehouse', [-12, 1.7, -3], [-1, 0.8, -12]],
  ['wh_racks', 'warehouse', [-20, 2.2, -21], [-34, 3, -30]],
  ['sub_street', 'suburb', [-50, 1.7, 1.5], [-20, 1.2, -1]],
  ['sub_cars', 'suburb', [-38, 2.2, 8], [-34, 0.6, -4]],
];

async function page(b, jank, useGlb) {
  const pg = await b.newPage({ viewport: { width: 960, height: 600 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  if (!useGlb) await pg.route('**/models/list', (r) => r.fulfill({ contentType: 'application/json', body: '[]' }));
  await pg.addInitScript((jank) => localStorage.setItem('jankfire', JSON.stringify({ name: 'props', killcam: false, jank })), jank);
  await pg.goto(`http://localhost:${port}/`); await sleep(1500);
  await pg.click('#scr-main [data-mode="training"]'); await sleep(2500);
  await pg.addStyleTag({ content: '#hud, .hud, #hotbar { display: none !important }' });
  return { pg, errs };
}

async function look(pg, map, eye, at) {
  await pg.evaluate(async ([map, eye, at]) => {
    const { ME } = await import('/js/player.js'); const { loadMap } = await import('/js/world.js'); const { MAP } = await import('/shared/map.js');
    if (MAP.id !== map) loadMap(map);
    clearInterval(window.__hold);
    const d = at.map((v, i) => v - eye[i]), L = Math.hypot(...d);
    window.__hold = setInterval(() => { ME.pos = [eye[0], eye[1] - 1.6, eye[2]]; ME.vel = [0, 0, 0]; ME.yaw = Math.atan2(-d[0], -d[2]); ME.pitch = Math.asin(d[1] / L); }, 5);
    const w = await import('/js/weapons.js'); w.setLoadout({ primary: 'ar', secondary: 'cards', melee: 'knife' });
  }, [map, eye, at]);
  await sleep(1200);
}

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  for (const jank of presets.split(',').map(Number)) {
    const tag = ['potato', 'crusty', 'mid', 'toohd'][jank];
    for (const useGlb of [false, true]) {
      const { pg, errs } = await page(b, jank, useGlb);
      for (const [name, map, eye, at] of VIEWS) {
        await look(pg, map, eye, at);
        await pg.screenshot({ path: `${out}/${tag}_${name}_${useGlb ? 'glb' : 'code'}.png` });
      }
      if (useGlb) { // every prop in a row on the range
        await pg.evaluate(async () => {
          const THREE = await import('three'); const { G } = await import('/js/ctx.js'); const { loadMap } = await import('/js/world.js');
          const { authored } = await import('/js/glbkit.js');
          loadMap('range');
          const row = [['p_bus', null, 0], ['p_car', null, 9], ['p_forklift', null, 14.5], ['p_pallet', null, 18.5], ['p_pallet_load', null, 20.2], ['p_rack', 'bay', 22.5], ['p_streetlight', null, 30], ['p_numball', 'n0', 33]];
          const grp = new THREE.Group(); grp.name = 'showcase';
          for (const [id, v, x] of row) {
            const a = authored(id); if (!a) continue;
            let o = a.obj;
            if (v) { o.traverse((n) => { if (n.name === v) o = n.clone(true); }); o.position.set(0, 0, 0); }
            o.position.set(x - 14, 0, -16); grp.add(o);
          }
          for (let k = 1; k < 10; k++) { const a = authored('p_numball'); let o; a.obj.traverse((n) => { if (n.name === 'n' + k) o = n.clone(true); }); o.position.set(20.5 + (k % 5) * 1.1, Math.floor(k / 5) * 1.0, -16 + 1.6); grp.add(o); }
          G.scene.add(grp);
        });
        await look(pg, 'range', [3, 4.5, 2], [5, 1.5, -16]);
        await pg.evaluate(async () => { const { ME } = await import('/js/player.js'); });
        await pg.screenshot({ path: `${out}/${tag}_showcase.png` });
      }
      console.log(tag, useGlb ? 'glb' : 'code', errs.join('\n') || 'no errors');
      await pg.close();
    }
  }
  await b.close();
})();
