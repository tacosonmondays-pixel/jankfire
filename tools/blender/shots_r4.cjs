// Round 4 sheets: the box-built prop next to the Blender one, in the game's own lights and fog, from the same camera,
// at Too HD and Potato. Or (ids = map) before/after views of whole maps.
// usage: node tools/blender/shots_r4.cjs <port> <outdir> <ids|map> [maps] [presets=3,0] [n=2]
//   ids: prop ids, comma separated (pine,lollipop,stall...), or "all" for every prop on those maps
//   maps: comma separated (default: every map that has one of the ids; for "map": jankburg,suburb,skyline)
//   (start the server first: PORT=<port> node server.js. Cap browsers with pwlock.cjs.)
// out: <outdir>/r4_<id>.png (rows = copies on their maps, columns = box / Blender per preset) or r4_map_<map>.png
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const [port = '3100', outdir = 'tools/blender/compare', idsArg = 'all', mapsArg = '', presetsArg = '3,0', nArg = '2'] = process.argv.slice(2);
const presets = presetsArg.split(',').map(Number), N = Number(nArg), MAPVIEWS = idsArg === 'map';
const PRESET = ['Potato', 'Crusty', 'Mid', 'Too HD'];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const GAME = { jankburg: 'br' };
fs.mkdirSync(outdir, { recursive: true });
const tmp = fs.mkdtempSync(path.join(require('os').tmpdir(), 'r4shots-'));

async function mapsWith(b, ids) { // which maps have these props (asked of the game's own map data)
  const pg = await b.newPage();
  await pg.goto(`http://localhost:${port}/`); await sleep(1500);
  const r = await pg.evaluate(async (ids) => {
    const { MAPS } = await import('/shared/map.js'); await import('/shared/royale.js');
    const out = {};
    for (const [m, d] of Object.entries(MAPS)) for (const l of [d.boxes.props, d.deco && d.deco.props]) for (const p of l || []) if (ids === 'all' || ids.includes(p.id)) (out[m] ||= new Set()).add(p.id);
    return Object.fromEntries(Object.entries(out).map(([k, v]) => [k, [...v]]));
  }, idsArg === 'all' ? 'all' : idsArg.split(','));
  await pg.close();
  return r;
}

async function session(b, map, ids) {
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + (e.stack || e.message).split('\n').slice(0, 3).join(' | ')));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text().slice(0, 200)); });
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ name: 'SHOTS', killcam: false, jank: 3 })));
  await pg.goto(`http://localhost:${port}/`); await sleep(2500);
  const T = { timeout: 180000 }; // (a busy machine: the menu can take a while to answer)
  await pg.click('#scr-main [data-pick="bots"]', T); await pg.click('#mpCustom', T);
  await pg.selectOption('#setupGame', GAME[map] || 'dm', T);
  await pg.selectOption('#setupMap', map, T);
  await pg.locator('#setupBots').fill('1'); await pg.selectOption('#setupDiff', 'easy').catch(() => {}); // (one slow bot: the least it allows)
  await pg.click('#setupGo', T);
  const ok = await pg.evaluate(async (map) => {
    const { G } = await import('/js/ctx.js'); const { MAP } = await import('/shared/map.js');
    for (let i = 0; i < 700 && !(G.joined && MAP.id === map); i++) await new Promise((r) => setTimeout(r, 100));
    if (!(G.joined && MAP.id === map)) return 'joined ' + G.joined + ', map ' + MAP.id;
    const k = await import('/js/glbkit.js'), pf = await import('/js/propfield.js'), { MAPS } = await import('/shared/map.js');
    const need = pf.modelsFor(MAPS[map]);
    for (let i = 0; i < 300 && (need.some((m) => k.LAZY.has(m)) || k.lateBusy()); i++) await new Promise((r) => setTimeout(r, 100)); // (the map's prop files)
    await new Promise((r) => setTimeout(r, 2500)); // (the redraw once they're in)
    return G.joined && MAP.id === map ? true : 'lost the map: ' + MAP.id;
  }, map);
  if (ok !== true) { console.log(map, 'never joined:', ok, errs.slice(0, 3).join(' / ')); await pg.close(); return []; }
  // the camera: pinned where we want it, no HUD, no gun
  await pg.evaluate(async () => {
    const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js');
    const h = document.getElementById('hud'); if (h) h.style.display = 'none';
    for (const id of ['crosshair', 'killfeed', 'chat', 'minimap']) { const e = document.getElementById(id); if (e) e.style.display = 'none'; }
    G.vmScene.visible = false;
    window.__pin = null;
    setInterval(() => { const q = window.__pin; if (q) { ME.pos = q.p.slice(); ME.vel = [0, 0, 0]; ME.yaw = q.yaw; ME.pitch = q.pitch; ME.hp = 100; } }, 4);
  });
  // where to look from (in the page: the map data + a ray against the boxes so nothing stands in the way)
  const views = await pg.evaluate(async ({ ids, N, MAPVIEWS, map }) => {
    const { MAPS, BOXES } = await import('/shared/map.js'); const { raycast } = await import('/shared/physics.js');
    const def = MAPS[map], out = [];
    const inBox = (x, y, z) => [...BOXES, ...(def.deco || [])].some((b) => !b.rot && x > b.min[0] - 0.3 && x < b.max[0] + 0.3 && y > b.min[1] - 0.3 && y < b.max[1] + 0.3 && z > b.min[2] - 0.3 && z < b.max[2] + 0.3);
    const lookAt = (cam, c) => { const dx = c[0] - cam[0], dy = c[1] - cam[1], dz = c[2] - cam[2]; return { p: [cam[0], cam[1] - 1.6, cam[2]], yaw: Math.atan2(-dx, -dz), pitch: Math.atan2(dy, Math.hypot(dx, dz)) }; };
    if (MAPVIEWS) { // two views a map: a spawn looking in at 7 m up, and high over the middle
      const sp = def.spawns.length ? def.spawns : [[0, 2, 0]], s0 = sp[0], s1 = sp[Math.floor(sp.length / 2)];
      let cx = 0, cz = 0; for (const s of sp) { cx += s[0] / sp.length; cz += s[2] / sp.length; }
      out.push({ id: 'map', k: 0, ...lookAt([s0[0], s0[1] + 7, s0[2]], [cx, s0[1] + 1, cz]) });
      const d = Math.max(30, Math.hypot(s1[0] - cx, s1[2] - cz));
      out.push({ id: 'map', k: 1, ...lookAt([cx + d * 0.7, s1[1] + d * 0.45 + 8, cz + d * 0.7], [cx, s1[1], cz]) });
      return out;
    }
    const all = [...(def.boxes.props || []), ...((def.deco && def.deco.props) || [])];
    for (const id of ids) {
      const list = all.filter((p) => p.id === id);
      let got = 0;
      for (let t = 0; t < list.length && got < N; t++) {
        const p = list[Math.floor((t * 0.618034 % 1) * list.length)]; // (spread over the map)
        let c, size, fr;
        if (p.a) {
          fr = p.f !== undefined ? p.f : p.y;
          const lx = (p.lo[0] + p.hi[0]) / 2, ly = (p.lo[1] + p.hi[1]) / 2, lz = (p.lo[2] + p.hi[2]) / 2, cs = Math.cos(fr), sn = Math.sin(fr);
          c = [p.a[0] + lx * cs + lz * sn, p.a[1] + ly, p.a[2] - lx * sn + lz * cs];
          size = Math.max(p.hi[0] - p.lo[0], p.hi[1] - p.lo[1], p.hi[2] - p.lo[2]);
        } else { c = [p.p[0], p.p[1] + 1, p.p[2]]; size = 2.5 * (p.s || 1); fr = -(p.r || 0) * Math.PI / 2; }
        const D = Math.min(40, Math.max(3.5, size * 1.45 + 2.2)), el = size > 6 ? 0.3 : 0.24;
        for (let k = 0; k < 12; k++) {
          const az = fr + Math.PI + [0.6, -0.6, 1.2, -1.2, 0, 1.9, -1.9, 2.5, -2.5, 3.14, 0.3, -0.3][k]; // from the front first (local -z), a bit to the side
          const cam = [c[0] - Math.sin(az) * D * Math.cos(el), c[1] + D * Math.sin(el), c[2] - Math.cos(az) * D * Math.cos(el)];
          if (inBox(...cam)) continue;
          const d = [c[0] - cam[0], c[1] - cam[1], c[2] - cam[2]], L = Math.hypot(...d); d[0] /= L; d[1] /= L; d[2] /= L;
          const h = raycast(cam, d, L, BOXES);
          if (h && h.t < L - size * 0.5 && h.box.pv !== id) continue;
          out.push({ id, k: got, ...lookAt(cam, c) }); got++; break;
        }
      }
    }
    return out;
  }, { ids, N, MAPVIEWS, map });
  const shots = [];
  for (const pr of presets) {
    await pg.evaluate(async (pr) => { const { G } = await import('/js/ctx.js'); const w = await import('/js/world.js'); G.settings.jank = pr; w.setJank(pr); }, pr);
    for (const boxes of [false, true]) {
      await pg.evaluate(async (boxes) => { const w = await import('/js/world.js'); w.showPropBoxes(boxes); }, boxes); // (the prop boxes drawn over the map as it is: no rebuild)
      await sleep(1200);
      for (const v of views) {
        await pg.evaluate((v) => { window.__pin = { p: v.p, yaw: v.yaw, pitch: v.pitch }; }, v);
        await sleep(1100);
        const f = path.join(tmp, `${map}_${v.id}_${v.k}_${pr}_${boxes ? 'box' : 'glb'}.png`);
        await pg.screenshot({ path: f, timeout: 120000 });
        shots.push({ map, id: v.id, k: v.k, pr, boxes, f });
      }
    }
  }
  await pg.evaluate(async () => { const w = await import('/js/world.js'); w.showPropBoxes(false); });
  if (errs.length) console.log(map, 'page errors:\n  ' + errs.slice(0, 6).join('\n  '));
  await pg.close();
  return shots;
}

// one sheet per prop (or per map): rows = copies, columns = box / Blender for each preset
function sheet(name, rows) {
  const cells = [], W = 480, H = 270;
  for (const row of rows) for (const s of row) {
    const lab = `${s.boxes ? 'boxes' : 'Blender'} - ${PRESET[s.pr]} - ${s.map}`.replace(/:/g, ' ');
    const f = s.f.replace(/\.png$/, '_l.png');
    execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-i', s.f, '-vf', `scale=${W}:${H},drawbox=x=0:y=0:w=${W}:h=22:color=black@0.6:t=fill,drawtext=text='${lab}':x=8:y=4:fontsize=15:fontcolor=${s.boxes ? 'white' : 'yellow'}`, f]);
    cells.push(f);
  }
  const cols = rows[0].length, args = [];
  for (const c of cells) args.push('-i', c);
  const lay = cells.map((_, i) => `${(i % cols) * W}_${Math.floor(i / cols) * H}`).join('|');
  const out = path.join(outdir, `r4_${name}.png`);
  execFileSync('ffmpeg', ['-loglevel', 'error', '-y', ...args, '-filter_complex', `xstack=inputs=${cells.length}:layout=${lay}:fill=black`, out]);
  console.log('wrote', out);
}

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  let plan;
  if (MAPVIEWS) plan = Object.fromEntries((mapsArg || 'jankburg,suburb,skyline').split(',').map((m) => [m, ['map']]));
  else {
    const has = await mapsWith(b, idsArg);
    plan = {};
    for (const [m, ids] of Object.entries(has)) if (!mapsArg || mapsArg.split(',').includes(m)) plan[m] = ids;
  }
  const all = [];
  for (const [map, ids] of Object.entries(plan)) { console.log('map', map, ids.join(',')); all.push(...await session(b, map, ids)); }
  await b.close();
  const by = new Map();
  for (const s of all) { const key = s.id === 'map' ? 'map_' + s.map : s.id; if (!by.has(key)) by.set(key, new Map()); const rk = s.map + '|' + s.k; if (!by.get(key).has(rk)) by.get(key).set(rk, []); by.get(key).get(rk).push(s); }
  for (const [key, rowsMap] of by) {
    const rows = [...rowsMap.values()].slice(0, MAPVIEWS ? 4 : 4).map((r) => r.sort((a, b) => (b.pr - a.pr) || (Number(b.boxes) - Number(a.boxes))));
    sheet(key, rows);
  }
  fs.rmSync(tmp, { recursive: true, force: true });
})();
