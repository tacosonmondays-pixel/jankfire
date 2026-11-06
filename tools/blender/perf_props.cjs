// Draw calls + triangles of the world pass (renderer.info, the shadow pass included: one is forced each measured
// frame so before/after compare like for like) in a real bots match, from fixed views: 3 spawns x 4 directions.
// Also the scene's totals (meshes, instanced meshes, triangles in view-independent terms) and page errors.
// usage: node tools/blender/perf_props.cjs <port> <out.json> [maps=jankburg,suburb,skyline] [preset=3]
//   (start the server first: PORT=<port> node server.js; Jankburg plays as Jank Royale, the rest as Deathmatch)
const { chromium } = require('playwright');
const fs = require('fs');
const [port = '3100', out = 'perf.json', list = 'jankburg,suburb,skyline', preset = '3'] = process.argv.slice(2);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const GAME = { jankburg: 'br' };

async function measure(b, map) {
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + (e.stack || e.message).split('\n').slice(0, 3).join(' | ')));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.addInitScript((jank) => localStorage.setItem('jankfire', JSON.stringify({ name: 'PERF', killcam: false, jank })), Number(preset));
  await pg.goto(`http://localhost:${port}/`); await sleep(2500);
  await pg.evaluate(async () => { const k = await import('/js/glbkit.js'); for (let i = 0; i < 200 && !Object.keys(k.AUTHORED).length; i++) await new Promise((r) => setTimeout(r, 100)); });
  await pg.click('#scr-main [data-pick="bots"]'); await pg.click('#mpCustom');
  await pg.selectOption('#setupGame', GAME[map] || 'dm');
  await pg.selectOption('#setupMap', map);
  await pg.locator('#setupBots').fill('1');
  await pg.selectOption('#setupDiff', 'easy').catch(() => {});
  await pg.click('#setupGo');
  const ok = await pg.evaluate(async (map) => {
    const { G } = await import('/js/ctx.js'); const { MAP } = await import('/shared/map.js');
    for (let i = 0; i < 300 && !(G.joined && MAP.id === map); i++) await new Promise((r) => setTimeout(r, 100));
    return G.joined && MAP.id === map;
  }, map);
  if (!ok) { await pg.close(); return { map, error: 'never joined the map', errs }; }
  await sleep(6000); // the map's late models, traffic, the first shadow pass
  const res = await pg.evaluate(async (map) => {
    const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js'); const { MAPS } = await import('/shared/map.js');
    const lt = await import('/js/lighting.js');
    const r = G.renderer, orig = r.render.bind(r);
    r.info.autoReset = false;
    let cur = null;
    r.render = (scene, cam) => { r.info.reset(); orig(scene, cam); if (scene === G.scene && cur) { cur.calls += r.info.render.calls; cur.tris += r.info.render.triangles; cur.n++; } };
    const frame = () => new Promise((res) => requestAnimationFrame(() => res()));
    const def = MAPS[map], sp = def.spawns.length ? def.spawns : [[0, 2, 0]];
    const pick = [sp[0], sp[Math.floor(sp.length / 2)], sp[sp.length - 1]];
    let pin = null; const iv = setInterval(() => { if (pin) { ME.pos = pin.p.slice(); ME.vel = [0, 0, 0]; ME.yaw = pin.yaw; ME.pitch = -0.04; } }, 5);
    const views = [];
    for (const p of pick) for (let k = 0; k < 4; k++) {
      pin = { p: [p[0], p[1] + 0.05, p[2]], yaw: k * Math.PI / 2 };
      for (let i = 0; i < 25; i++) await frame(); // settle (chunks, culling, the shadow camera)
      cur = { calls: 0, tris: 0, n: 0 };
      for (let i = 0; i < 6; i++) { lt.lightingRefresh(); await frame(); }
      views.push({ calls: Math.round(cur.calls / Math.max(1, cur.n)), tris: Math.round(cur.tris / Math.max(1, cur.n)) });
      cur = null;
    }
    clearInterval(iv); r.render = orig; r.info.autoReset = true;
    // the scene's own totals (what's built, not what one view sees)
    let meshes = 0, inst = 0, tris = 0, instances = 0;
    G.scene.traverse((o) => {
      if (!o.isMesh || !o.geometry) return;
      const g = o.geometry, t = (g.index ? g.index.count : g.attributes.position.count) / 3;
      if (o.isInstancedMesh) { inst++; instances += o.count; tris += t * o.count; } else { meshes++; tris += t; }
    });
    const avg = (k) => Math.round(views.reduce((s, v) => s + v[k], 0) / views.length), max = (k) => Math.max(...views.map((v) => v[k]));
    return { map, calls: avg('calls'), callsMax: max('calls'), tris: avg('tris'), trisMax: max('tris'), views, scene: { meshes, instancedMeshes: inst, instances, tris: Math.round(tris) }, geometries: r.info.memory.geometries, textures: r.info.memory.textures };
  }, map);
  res.errs = errs;
  await pg.close();
  return res;
}

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const all = [];
  for (const m of list.split(',')) {
    const r = await measure(b, m);
    all.push(r);
    console.log(`${m}: calls avg ${r.calls} max ${r.callsMax}, tris avg ${r.tris} max ${r.trisMax}; scene ${JSON.stringify(r.scene)}${r.error ? ' ERROR ' + r.error : ''}${r.errs && r.errs.length ? '\n  ' + r.errs.slice(0, 6).join('\n  ') : ' (no page errors)'}`);
  }
  fs.writeFileSync(out, JSON.stringify(all, null, 1));
  await b.close();
})();
