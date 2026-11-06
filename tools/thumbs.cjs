// Map thumbnails for the end-of-match vote cards: renders every map in the real game (HD) and writes
// public/thumbs/<map>.jpg (480x300). Re-run after map changes:  node server.js &  then  node tools/thumbs.cjs [url] [map,map]
// Each map gets a hand-picked camera (CAMS: [x, y, z, yaw, pitch], picked from contact sheets of candidate views);
// a map without one uses its own inside camera (menuCam, sealed maps) or an automatic high three-quarter view.
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs'), os = require('os'), path = require('path');
const url = process.argv[2] || 'http://localhost:3000/';
const only = process.argv[3] ? process.argv[3].split(',') : null;
const out = path.join(__dirname, '..', 'public', 'thumbs');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const orbit = (r, h, a, pitch) => [Math.sin(a) * r, h, Math.cos(a) * r, a, pitch]; // the menu backdrop's orbit, frozen at angle a
const CAMS = {
  crate: [13.05, 6.85, 13.05, 0.79, -0.25],
  platform: [72, 34, 72, 0.79, -0.33], // far enough to see it's a slab floating over the clouds
  rooftop: [-60, 22, 40, -0.938, -0.312], // up over the bank: its sign, the party block's pool and palms, the hotel
  rooftop_sd: [18, 6, 24, 0.633, -0.237], // over a low roof onto the party block: the pool, the cabanas, the penthouse
  suburb: [-45.96, 16.29, -45.96, -2.36, -0.21],
  warehouse: [-29, 4.2, -4.5, -1.571, -0.1], // inside the hall, down an aisle between the racks
  warehouse_sd: [34, 6.5, -27, -0.42, -0.16], // the A site: the red dock, the gantry, the BOMB SITE A board
  desert: [-88, 9, 0, -1.571, -0.102], // down Main Street from the west gate: the saloon, the bell tower, the general store
  desert_sd: [3, 1.9, 40, -1.661, 0.018], // off the rope bridge onto B: the payroll train, the station, the BOMB SITE B board
  bazaar: [48, 20, 48, 0.785, -0.259], // high over the potters (south-east): the Grand Bazaar under its dome, the canal, the souks
  bazaar_sd: [27.5, 2.5, -44, -2.478, -0.074], // the A site: the dye vats, the dye house, cloth on the racks
  islands: [52.8, 5.1, 48, 0.8, -0.04],
  skyline: [78.18, 78.31, 76.18, 0.79, -0.13],
};
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'jfthumb-'));
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 960, height: 600 } });
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ jank: 3, fov: 75, name: 'thumbs' })));
  await pg.goto(url); await sleep(1500);
  const ids = (await pg.evaluate(async () => (await import('/shared/map.js')).MAP_ORDER)).filter((id) => !only || only.includes(id));
  for (const id of ids) {
    await pg.evaluate(async ({ id, cam }) => {
      const { G } = await import('/js/ctx.js'); const { loadMap } = await import('/js/world.js'); const { MAPS } = await import('/shared/map.js');
      G.cfg.map = id; loadMap(id);
      document.getElementById('menu').classList.add('hidden');
      const m = MAPS[id];
      if (!cam && m.menuCam) cam = [Math.sin(1) * m.menuCam[0], m.menuCam[1], Math.cos(1) * m.menuCam[0], 1, m.menuCam[2]];
      if (!cam) { // automatic: up and back from the middle of the spawns, looking at it
        const sp = m.spawns, xs = sp.map((s) => s[0]), zs = sp.map((s) => s[2]), y = sp.reduce((a, s) => a + s[1], 0) / sp.length;
        const c = [(Math.min(...xs) + Math.max(...xs)) / 2, y, (Math.min(...zs) + Math.max(...zs)) / 2];
        const e = Math.max((Math.max(...xs) - Math.min(...xs)) / 2, (Math.max(...zs) - Math.min(...zs)) / 2, 8), d = e * 0.95 + 8;
        const p = [c[0] + d * 0.707, c[1] + e * 0.55 + 6, c[2] + d * 0.707], v = [c[0] - p[0], c[1] + 1 - p[1], c[2] - p[2]];
        cam = [...p, Math.atan2(-v[0], -v[2]), Math.atan2(v[1], Math.hypot(v[0], v[2]))];
      }
      G.thumbCam = cam;
    }, { id, cam: CAMS[id] || null });
    await sleep(2500);
    const png = path.join(tmp, id + '.png');
    await pg.locator('#game').screenshot({ path: png });
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', png, '-vf', 'scale=480:300:flags=lanczos', '-q:v', '4', path.join(out, id + '.jpg')]);
    console.log('thumb', id);
  }
  await b.close();
})();
