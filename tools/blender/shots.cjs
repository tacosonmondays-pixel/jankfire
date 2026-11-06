// In-game screenshots of the Blender models next to the code-built ones they replace, plus an aiming check.
// usage: node tools/blender/shots.cjs <port> <outDir> [weapons=ar,shotgun,revolver] [presets=3,0] [--check-only] [--no-check]
//   (start the server first: PORT=<port> node server.js)
// writes <outDir>/<preset>_<weapon>_<glb|code>_<hip|ads>.png and <outDir>/<preset>_lineup.png
// (the lineup is code model on top, Blender model under it, in the game's own lights and render preset)
// ADS check (Blender models, Too HD): with each gun fully aimed, at 1280x720, 1280x800 and 900x900 and FOV 70 and 120,
// it renders only the viewmodel and measures how much of the screen's centre (the middle 40% x 40%, where you look for
// people) the gun covers (pixels at least half opaque). More than LIMIT anywhere = exit code 1. A scoped sniper hides its gun, so it reads 0 (scope).
const { chromium } = require('playwright');
const args = process.argv.slice(2).filter((a) => !a.startsWith('--'));
const flags = new Set(process.argv.slice(2).filter((a) => a.startsWith('--')));
const [port = '3100', out = '.', list = 'ar,shotgun,revolver', presets = '3,0'] = args;
const LIMIT = 0.25, CENTRE = 0.4;
const SIZES = [[1280, 720], [1280, 800], [900, 900]], FOVS = [70, 120];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const SECONDARY = new Set(['revolver', 'pistol', 'akimbo', 'sawnoff', 'marbles', 'cig', 'blower', 'cards', 'snowball', 'bloodcross']);
const weapons = list.split(',');
const NO_ADS = new Set(['akimbo']); // no aiming: right click fires the right gun, so there's nothing to check

async function session(b, jank, useGlb, viewport = { width: 960, height: 600 }) {
  const pg = await b.newPage({ viewport });
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

const pick = (pg, id) => pg.evaluate(async ([id, slot]) => {
  const w = await import('/js/weapons.js');
  const lo = { primary: 'ar', secondary: 'cards', melee: 'knife' }; lo[slot] = id;
  w.setLoadout(lo); w.switchSlot(slot === 'primary' ? 1 : 0); w.switchSlot(slot === 'primary' ? 0 : 1);
}, [id, SECONDARY.has(id) ? 'secondary' : 'primary']);
const aim = (pg, on) => pg.evaluate(async (on) => { const { W } = await import('/js/weapons.js'); W.aimHeld = on; }, on);

// share of the screen's centre box covered by the viewmodel (rendered alone into a transparent target)
const coverage = (pg) => pg.evaluate(async (CENTRE) => {
  const THREE = await import('three'); const { G } = await import('/js/ctx.js'); const { W } = await import('/js/weapons.js');
  for (let i = 0; i < 40 && W.aim < 0.98; i++) await new Promise((r) => setTimeout(r, 50));
  if (W.scoped) return -1;
  const r = G.renderer, sz = r.getSize(new THREE.Vector2()), w = sz.x, h = sz.y;
  const rt = new THREE.WebGLRenderTarget(w, h);
  const cc = r.getClearColor(new THREE.Color()), ca = r.getClearAlpha(), bg = G.vmScene.background;
  G.vmScene.background = null;
  r.setRenderTarget(rt); r.setClearColor(0x000000, 0); r.clear(true, true, true); r.render(G.vmScene, G.vmCamera);
  const cw = Math.round(w * CENTRE), ch = Math.round(h * CENTRE), x0 = Math.round((w - cw) / 2), y0 = Math.round((h - ch) / 2);
  const buf = new Uint8Array(cw * ch * 4);
  r.readRenderTargetPixels(rt, x0, y0, cw, ch, buf);
  r.setRenderTarget(null); r.setClearColor(cc, ca); G.vmScene.background = bg; rt.dispose();
  let n = 0; for (let i = 3; i < buf.length; i += 4) if (buf[i] >= 128) n++; // mostly opaque: see-through glass (a red-dot lens, the marble jar) doesn't block the view
  return n / (cw * ch);
}, CENTRE);

async function adsCheck(b) {
  const { pg, errs } = await session(b, 3, true, { width: SIZES[0][0], height: SIZES[0][1] });
  const rows = [];
  for (const [vw, vh] of SIZES) {
    await pg.setViewportSize({ width: vw, height: vh }); await sleep(600);
    for (const fov of FOVS) {
      await pg.evaluate(async (fov) => { const { G } = await import('/js/ctx.js'); G.settings.fov = fov; }, fov);
      for (const id of weapons.filter((w) => !NO_ADS.has(w))) {
        await pick(pg, id); await sleep(800);
        await aim(pg, true);
        const c = await coverage(pg);
        await aim(pg, false); await sleep(250);
        rows.push({ id, size: `${vw}x${vh}`, fov, c });
      }
    }
  }
  await pg.close();
  const fmt = (c) => (c < 0 ? 'scope' : (c * 100).toFixed(1) + '%');
  console.log(`\nADS check: share of the centre ${CENTRE * 100}% x ${CENTRE * 100}% the gun covers while aiming (limit ${LIMIT * 100}%)`);
  console.log('gun'.padEnd(10) + SIZES.flatMap(([w, h]) => FOVS.map((f) => `${w}x${h}@${f}`.padStart(15))).join(''));
  let worst = 0;
  for (const id of weapons.filter((w) => !NO_ADS.has(w))) {
    const cs = rows.filter((r) => r.id === id);
    worst = Math.max(worst, ...cs.map((r) => r.c));
    console.log(id.padEnd(10) + cs.map((r) => (fmt(r.c) + (r.c > LIMIT ? ' FAIL' : '')).padStart(15)).join(''));
  }
  console.log(`worst ${fmt(worst)} -> ${worst > LIMIT ? 'FAIL' : 'pass'}`, errs.length ? '\n' + errs.join('\n') : '(no page errors)');
  return worst <= LIMIT && !errs.length;
}

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  if (!flags.has('--check-only')) for (const jank of presets.split(',').map(Number)) {
    const tag = ['potato', 'crusty', 'mid', 'toohd'][jank];
    for (const useGlb of [false, true]) {
      const { pg, errs } = await session(b, jank, useGlb);
      for (const id of weapons) {
        await pick(pg, id);
        await sleep(900);
        const name = `${out}/${tag}_${id}_${useGlb ? 'glb' : 'code'}`;
        await pg.screenshot({ path: `${name}_hip.png` });
        await aim(pg, true);
        await sleep(700);
        await pg.screenshot({ path: `${name}_ads.png` });
        await aim(pg, false);
        await sleep(300);
      }
      if (useGlb) { // lineup: every weapon as the code builds it (top) and from Blender (bottom), side on, game lights
        const png = await pg.evaluate(async ([weapons, jank]) => {
          const THREE = await import('three');
          const { buildWeapon } = await import('/js/models.js');
          const { AUTHORED } = await import('/js/glbkit.js');
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
            x += Math.min(len, 1.35) * (['revolver', 'pistol', 'akimbo'].includes(id) ? 0.45 : id === 'sawnoff' ? 0.6 : 1);
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
  const ok = flags.has('--no-check') ? true : await adsCheck(b);
  await b.close();
  process.exitCode = ok ? 0 : 1;
})();
