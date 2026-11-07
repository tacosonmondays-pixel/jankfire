// Round 4 sheets: the box-built prop next to the Blender one, in the game's own lights and fog, from the same camera,
// at Too HD and Potato. Or (ids = map) before/after views of whole maps.
// usage: node tools/blender/shots_r4.cjs <port> <outdir> <ids|map> [maps] [presets=3,0] [n=2]
//   ids: prop ids, comma separated (pine,lollipop,stall...), or "all" for every prop on those maps
//   maps: comma separated (default: every map that has one of the ids; for "map": jankburg,suburb,skyline)
//   (start the server first: JF_ROUND_TIME=7200 JF_ROUND_KILLS=999 JF_BOMB_WINS=99 JF_BOMB_ROUND=3600 JF_BUY_TIME=1 JF_ZM_SWIPE=0
//   PORT=<port> node server.js: the match outlasts the shots, Plant & Defuse keeps going with 1 s buy phases, zombies
//   don't bite. Cap browsers with pwlock.cjs.)
//   JF_SHOT_FOV=45: a narrower lens than the game's for the shots (big props like the buses fill more of the picture)
// out: <outdir>/r4_<id>.png (rows = copies on their maps, columns = box / Blender per preset) or r4_map_<map>.png
// or ids = targets:<file.json>: spots to look at as they are now (docs/blender/INVENTORY.md's sheets), each
//   { sheet, map, label, c: [x, y, z], size: [x, y, z] } (framed like a prop) or { sheet, map, label, cam, at };
//   out: <outdir>/<sheet>.png, 4 across, one cell per spot
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const [port = '3100', outdir = 'tools/blender/compare', idsArg = 'all', mapsArg = '', presetsArg = '3,0', nArg = '2'] = process.argv.slice(2);
const presets = presetsArg.split(',').map(Number), N = Number(nArg), MAPVIEWS = idsArg === 'map';
const TARGETS = /^targets:/.test(idsArg) ? JSON.parse(fs.readFileSync(idsArg.slice(8), 'utf8')) : null;
const PRESET = ['Potato', 'Crusty', 'Mid', 'Too HD'];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const GAME = { jankburg: 'br', deadmall: 'zm' }, gameOf = (m) => GAME[m] || (/_sd$/.test(m) ? 'bomb' : 'dm'); // (the Plant & Defuse layouts are only in that mode's list)
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
  if (map === 'range') await pg.click('#scr-main [data-mode="training"]', T); // (the Training range: only Training plays it)
  else {
    await pg.click('#scr-main [data-pick="bots"]', T); await pg.click('#mpCustom', T);
    await pg.selectOption('#setupGame', gameOf(map), T);
    await pg.selectOption('#setupMap', map, T);
    const bots = pg.locator('#setupBots'); if (await bots.isVisible()) await bots.fill('1'); // (one slow bot: the least it allows; Zombies has none)
    await pg.selectOption('#setupDiff', 'easy', { timeout: 3000 }).catch(() => {});
    await pg.click('#setupGo', T);
  }
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
  await pg.evaluate((f) => { window.__fov = f; }, Number(process.env.JF_SHOT_FOV) || 0);
  await pg.evaluate(async () => {
    const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js');
    const h = document.getElementById('hud'); if (h) h.style.display = 'none';
    const css = document.createElement('style'); css.textContent = 'body > :not(#game) { display: none !important; }'; document.head.append(css); // (only the 3D view: no flash, quiz or out-of-bounds overlays)
    for (const id of ['crosshair', 'killfeed', 'chat', 'minimap']) { const e = document.getElementById(id); if (e) e.style.display = 'none'; }
    G.vmCamera.layers.disableAll(); // (no gun: main.js turns vmScene back on every frame)
    window.__pin = null;
    let last = null; // (where the pin put you last tick: a jump away from it is the game teleporting you, i.e. a respawn)
    setInterval(() => { const q = window.__pin; if (q) { if (!window.__hide || (ME.alive && last && Math.hypot(ME.pos[0] - last[0], ME.pos[2] - last[2]) > 2)) window.__hide = ME.pos.slice(); ME.pos = q.p.slice(); last = q.p; ME.vel = [0, 0, 0]; ME.yaw = q.yaw; ME.pitch = q.pitch; ME.hp = 100; } }, 4);
    // the camera floats where the shot wants it, but the server is told you're still standing where you (re)spawned:
    // bots hunt you there instead of shooting the camera out of the sky (a teleport, e.g. a respawn, moves that spot)
    const { net } = await import('/js/net.js'), send0 = net.send.bind(net);
    net.send = (o) => send0(window.__pin && window.__hide && o && o.t === 's' ? { ...o, p: window.__hide.map((v) => Math.round(v * 100) / 100), v: [0, 0, 0] } : o);
    // each frame as it's drawn: is the camera at your eye, and you about where the pin put you (not shoved up onto a roof)? (a nudge out of a tree
    // trunk is the same in both versions; a replay, spectating, the ball or a knock-down moves the camera off your eye)
    const draw = G.renderer.render.bind(G.renderer);
    G.renderer.render = (sc, cam) => {
      const q = window.__pin;
      if (cam === G.camera && q && window.__fov && cam.fov !== window.__fov) { cam.fov = window.__fov; cam.updateProjectionMatrix(); }
      if (cam === G.camera && q) { const c = cam.position; window.__camOk = Math.hypot(c.x - ME.pos[0], c.y - ME.pos[1] - ME.eyeH, c.z - ME.pos[2]) <= 0.3 && Math.hypot(ME.pos[0] - q.p[0], ME.pos[2] - q.p[2]) <= 1.5 && Math.abs(ME.pos[1] - q.p[1]) <= 0.8; if (!window.__camOk) window.__camBadT = performance.now(); } // (when it last wasn't: a frame or two off between checks counts too)
      if (cam === G.camera && q) { for (const pr of G.projs.values()) if (pr.mesh) pr.mesh.visible = false; G.remotes.forEach((r) => { if (r.ch && r.ch.root) r.ch.root.visible = false; }); } // (no bullets, thrown stuff or players flying through the shot)
      return draw(sc, cam);
    };
    // __life goes up on every death and every new Plant & Defuse round: a shot taken across one is taken again
    window.__life = 0; let was = ME.alive, round = G.eco && G.eco.round;
    setInterval(() => { if (was && !ME.alive) { window.__life++; window.__lifeT = performance.now(); } was = ME.alive; const r = G.eco && G.eco.round; if (r !== round) { round = r; window.__life++; window.__lifeT = performance.now(); } }, 4);
    // the same picture for both versions: no sparks / smoke / confetti (points) and no bot walking through the shot
    setInterval(() => { for (const o of G.scene.children) if (o.isPoints) o.visible = false; G.remotes.forEach((r) => { if (r.ch && r.ch.root) r.ch.root.visible = false; }); }, 16);
  });
  // where to look from (in the page: the map data + a ray against the boxes so nothing stands in the way)
  const views = await pg.evaluate(async ({ ids, N, MAPVIEWS, map, tg }) => {
    const { MAPS, BOXES } = await import('/shared/map.js'); const { raycast } = await import('/shared/physics.js');
    const def = MAPS[map], out = [];
    const inBox = (x, y, z) => [...BOXES, ...(def.deco || [])].some((b) => !b.rot && x > b.min[0] - 0.3 && x < b.max[0] + 0.3 && y > b.min[1] - 0.3 && y < b.max[1] + 0.3 && z > b.min[2] - 0.3 && z < b.max[2] + 0.3);
    // the whole player fits there (feet 1.6 m under the camera): a body inside a crate stack gets shoved off the spot every frame
    const bodyFree = (x, y, z) => !BOXES.some((b) => b.max[0] > x - 0.45 && b.min[0] < x + 0.45 && b.max[1] > y - 1.62 && b.min[1] < y + 0.25 && b.max[2] > z - 0.45 && b.min[2] < z + 0.45);
    const lookAt = (cam, c) => { const dx = c[0] - cam[0], dy = c[1] - cam[1], dz = c[2] - cam[2]; return { p: [cam[0], cam[1] - 1.6, cam[2]], yaw: Math.atan2(-dx, -dz), pitch: Math.atan2(dy, Math.hypot(dx, dz)) }; };
    if (tg) { // the inventory's spots: framed like a prop (a clear line in from one of 12 sides), or a camera given outright
      for (const [k, t] of tg.entries()) {
        if (t.cam) { out.push({ id: t.sheet, k, label: t.label, ...lookAt(t.cam, t.at) }); continue; }
        const c = t.c, size = Math.max(...t.size), D = Math.min(45, Math.max(3.5, size * 1.2 + 2.2)), el = size > 6 ? 0.3 : 0.24;
        for (let j = 0; j < 12; j++) {
          const az = [0.6, -0.6, 1.2, -1.2, 0, 1.9, -1.9, 2.5, -2.5, 3.14, 0.3, -0.3][j];
          const cam = [c[0] - Math.sin(az) * D * Math.cos(el), c[1] + D * Math.sin(el), c[2] - Math.cos(az) * D * Math.cos(el)];
          if (inBox(...cam) || !bodyFree(...cam)) continue;
          const d = [c[0] - cam[0], c[1] - cam[1], c[2] - cam[2]], L = Math.hypot(...d); d[0] /= L; d[1] /= L; d[2] /= L;
          const h = raycast(cam, d, L, BOXES);
          if (h && h.t < L - size * 0.5) continue;
          out.push({ id: t.sheet, k, label: t.label, ...lookAt(cam, c) }); break;
        }
        if (!out.some((o) => o.k === k)) out.push({ id: t.sheet, k, label: t.label + ' (no clear view: from above)', ...lookAt([c[0] + 1, c[1] + D, c[2] + D * 0.4], c) });
      }
      return out;
    }
    if (MAPVIEWS) { // two views a map: a spawn looking in at 7 m up, and high over the middle
      const sp = def.spawns.length ? def.spawns : [[0, 2, 0]], s0 = sp[0], s1 = sp[Math.floor(sp.length / 2)];
      let cx = 0, cz = 0; for (const s of sp) { cx += s[0] / sp.length; cz += s[2] / sp.length; }
      if (Math.hypot(cx - s0[0], cz - s0[2]) < 8) { // the spawns side by side (Training): look at the props instead of the floor
        const ps = [...(def.boxes.props || []), ...((def.deco && def.deco.props) || [])].map((p) => p.a || p.p).filter(Boolean);
        if (ps.length) { cx = 0; cz = 0; for (const q of ps) { cx += q[0] / ps.length; cz += q[2] / ps.length; } }
      }
      if (map === 'deadmall') { // indoors (a roof over everything, walls between): round the props at eye height and 3 m up, the first two spots that see them
        const t = [cx, s0[1] + 0.6, cz];
        for (const [D, y] of [[12, 1.7], [9, 3], [7, 1.7], [5, 3]]) for (let i = 0; i < 12 && out.length < 2; i++) {
          const az = (i / 12) * Math.PI * 2, cam = [cx + Math.sin(az) * D, s0[1] + y, cz + Math.cos(az) * D];
          if (inBox(...cam) || out.some((o) => Math.hypot(o.p[0] - cam[0], o.p[2] - cam[2]) < 10)) continue;
          const d = [t[0] - cam[0], t[1] - cam[1], t[2] - cam[2]], L = Math.hypot(...d), h = raycast(cam, d.map((v) => v / L), L, BOXES);
          if (!h || h.t > L - 1.5) out.push({ id: 'map', k: out.length, ...lookAt(cam, t) });
        }
        return out;
      }
      let v0 = s0; // (the first spawn whose 7 m view in isn't blocked close by: a wall or a gallery in the way shows nothing)
      for (const s of sp) {
        const cam = [s[0], s[1] + 7, s[2]], d = [cx - cam[0], s[1] + 1 - cam[1], cz - cam[2]], L = Math.hypot(...d), h = L > 1 && raycast(cam, d.map((v) => v / L), L, BOXES);
        if (L > 1 && (!h || h.t > Math.min(25, L * 0.6))) { v0 = s; break; }
      }
      out.push({ id: 'map', k: 0, ...lookAt([v0[0], v0[1] + 7, v0[2]], [cx, v0[1] + 1, cz]) });
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
          const az = fr + [0.6, -0.6, 1.2, -1.2, 0, 1.9, -1.9, 2.5, -2.5, 3.14, 0.3, -0.3][k]; // from the front first (local -z: the camera at c - (sin az, cos az) D), a bit to the side
          const cam = [c[0] - Math.sin(az) * D * Math.cos(el), c[1] + D * Math.sin(el), c[2] - Math.cos(az) * D * Math.cos(el)];
          if (inBox(...cam) || !bodyFree(...cam)) continue;
          const d = [c[0] - cam[0], c[1] - cam[1], c[2] - cam[2]], L = Math.hypot(...d); d[0] /= L; d[1] /= L; d[2] /= L;
          const h = raycast(cam, d, L, BOXES);
          if (h && h.t < L - size * 0.5 && h.box.pv !== id) continue;
          out.push({ id, k: got, ...lookAt(cam, c) }); got++; break;
        }
      }
    }
    return out;
  }, { ids, N, MAPVIEWS, map, tg: TARGETS ? TARGETS.filter((t) => t.map === map) : null });
  const shots = [];
  for (const pr of presets) {
    await pg.evaluate(async (pr) => { const { G } = await import('/js/ctx.js'); const w = await import('/js/world.js'); G.settings.jank = pr; w.setJank(pr); }, pr);
    for (const boxes of TARGETS ? [false] : [false, true]) { // (targets: just as it is now)
      await pg.evaluate(async (boxes) => { const w = await import('/js/world.js'); w.showPropBoxes(boxes); }, boxes); // (the prop boxes drawn over the map as it is: no rebuild)
      await sleep(1200);
      for (const v of views) {
        await pg.evaluate((v) => { window.__pin = { p: v.p, yaw: v.yaw, pitch: v.pitch }; }, v);
        await sleep(1100);
        const f = path.join(tmp, `${map}_${v.id}_${v.k}_${pr}_${boxes ? 'box' : 'glb'}.png`);
        let st = 'dead';
        for (let tries = 0; tries < 6; tries++) {
          // still on this map, alive, past a Plant & Defuse buy phase? (a match that ends moves to the next map; a bot can
          // kill you: wait for the respawn; in the buy phase the server holds you in your spawn zone and its walls show)
          st = await pg.evaluate(async (map) => {
            const { MAP } = await import('/shared/map.js'); const { ME } = await import('/js/player.js'); const { G } = await import('/js/ctx.js');
            const off = () => !window.__camOk || performance.now() < (ME.sleepUntil || 0); // (something else had the camera last frame: a replay, spectating, the ball, a knock-down)
            const busy = () => MAP.id === map && (!ME.alive || (G.eco && G.eco.buyEnd > performance.now()) || performance.now() < (ME.quizUntil || 0) || performance.now() - (window.__lifeT || -1e9) < 5000 || off()); // (a bot's pop quiz: frozen, a panel up; a death: its kill effect fades first)
            const t0 = performance.now(), wait = (ms) => new Promise((r) => setTimeout(r, ms));
            while (performance.now() - t0 < 60000) { // (killed again while settling: keep waiting, up to a minute)
              while (busy() && performance.now() - t0 < 60000) await wait(100);
              await wait(900); // (re-pinned, the barriers gone)
              if (!busy()) break;
            }
            return MAP.id !== map ? 'moved on to ' + MAP.id : busy() ? (ME.alive ? 'buy phase' : 'dead') : 'ok';
          }, map);
          if (st !== 'ok') break;
          const before = await pg.evaluate(() => ({ life: window.__life, t: performance.now() }));
          await pg.screenshot({ path: f, timeout: 120000 });
          const after = await pg.evaluate(async (before) => {
            const { ME } = await import('/js/player.js'); const { G } = await import('/js/ctx.js'); const n = performance.now();
            return window.__life !== before.life ? 'died or a new round' : !ME.alive ? 'dead' : !window.__camOk || (window.__camBadT || 0) >= before.t ? 'the camera wasn\'t at the pin' : n < (ME.sleepUntil || 0) ? 'knocked flat' : G.eco && G.eco.buyEnd > n ? 'buy phase' : n < (ME.quizUntil || 0) ? 'pop quiz' : 'ok';
          }, before);
          if (after === 'ok') break;
          st = after + ' during the shot'; console.log(map, v.id, v.k, 'retake:', st);
        }
        if (st !== 'ok') { console.log(map, v.id, v.k, 'skipped:', st, '(start the server with JF_ROUND_TIME=7200 JF_ROUND_KILLS=999 JF_BOMB_WINS=99 JF_BOMB_ROUND=3600 JF_BUY_TIME=1 JF_ZM_SWIPE=0)'); if (st.startsWith('moved')) break; continue; }
        shots.push({ map, id: v.id, k: v.k, pr, boxes, f, label: v.label });
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
  let blank = 0;
  for (const row of rows) for (const s of row) {
    const lab = `${s.boxes ? 'boxes' : 'Blender'} - ${PRESET[s.pr]} - ${s.map}${s.f ? '' : ' (no clean shot)'}`.replace(/:/g, ' ');
    const f = s.f ? s.f.replace(/\.png$/, '_l.png') : path.join(tmp, `blank_${blank++}.png`);
    const src = s.f ? ['-i', s.f] : ['-f', 'lavfi', '-i', `color=c=0x120818:s=${W}x${H}:d=1`, '-frames:v', '1'];
    execFileSync('ffmpeg', ['-loglevel', 'error', '-y', ...src, '-vf', `scale=${W}:${H},drawbox=x=0:y=0:w=${W}:h=22:color=black@0.6:t=fill,drawtext=text='${lab}':x=8:y=4:fontsize=15:fontcolor=${s.boxes ? 'white' : 'yellow'}`, f]);
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
  if (TARGETS) plan = Object.fromEntries([...new Set(TARGETS.map((t) => t.map))].map((m) => [m, ['targets']]));
  else if (MAPVIEWS) plan = Object.fromEntries((mapsArg || 'jankburg,suburb,skyline').split(',').map((m) => [m, ['map']]));
  else {
    const has = await mapsWith(b, idsArg);
    plan = {};
    for (const [m, ids] of Object.entries(has)) if (!mapsArg || mapsArg.split(',').includes(m)) plan[m] = ids;
  }
  const all = [];
  for (const [map, ids] of Object.entries(plan)) { console.log('map', map, ids.join(',')); all.push(...await session(b, map, ids)); }
  await b.close();
  if (TARGETS) { // one sheet per group: the spots in the file's order, 4 across, labelled
    for (const name of [...new Set(TARGETS.map((t) => t.sheet))]) {
      const W = 480, H = 270, cells = [];
      TARGETS.forEach((t, i) => {
        if (t.sheet !== name) return;
        const k = TARGETS.filter((u) => u.map === t.map).indexOf(t), s = all.find((x) => x.map === t.map && x.k === k && x.id === name);
        const lab = `${t.label} - ${t.map}${s ? '' : ' (no clean shot)'}`.replace(/[:']/g, ' ').slice(0, 58), o = path.join(tmp, `t_${i}.png`);
        const src = s ? ['-i', s.f] : ['-f', 'lavfi', '-i', `color=c=0x120818:s=${W}x${H}:d=1`, '-frames:v', '1'];
        execFileSync('ffmpeg', ['-loglevel', 'error', '-y', ...src, '-vf', `scale=${W}:${H},drawbox=x=0:y=0:w=${W}:h=22:color=black@0.6:t=fill,drawtext=text='${lab}':x=8:y=4:fontsize=15:fontcolor=yellow`, o]);
        cells.push(o);
      });
      const args = []; for (const c of cells) args.push('-i', c);
      const lay = cells.map((_, i) => `${(i % 4) * W}_${Math.floor(i / 4) * H}`).join('|'), out = path.join(outdir, `${name}.png`);
      execFileSync('ffmpeg', ['-loglevel', 'error', '-y', ...args, '-filter_complex', cells.length > 1 ? `xstack=inputs=${cells.length}:layout=${lay}:fill=black` : 'null', out]);
      console.log('wrote', out);
    }
    fs.rmSync(tmp, { recursive: true, force: true });
    return;
  }
  const by = new Map();
  for (const s of all) { const key = s.id === 'map' ? 'map_' + s.map : s.id; if (!by.has(key)) by.set(key, new Map()); const rk = s.map + '|' + s.k; if (!by.get(key).has(rk)) by.get(key).set(rk, []); by.get(key).get(rk).push(s); }
  for (const [key, rowsMap] of by) {
    // every row the same grid: boxes / Blender for each preset, a blank cell where a shot never came out clean
    const rows = [...rowsMap.values()].slice(0, 4).map((r) => presets.slice().sort((a, b) => b - a).flatMap((pr) => [true, false].map((boxes) => r.find((s) => s.pr === pr && s.boxes === boxes) || { map: r[0].map, pr, boxes, f: null })));
    sheet(key, rows);
  }
  fs.rmSync(tmp, { recursive: true, force: true });
})();
