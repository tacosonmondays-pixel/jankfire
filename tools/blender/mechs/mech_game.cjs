// The concept mechs in the real game: Training range, the game's own lights, sky, fog and renderer at a graphics
// preset (default 3 = Too HD), next to the game's own mannequin. Loads docs/mechs/concept/<fid>_concept.glb through
// glbkit's prepAuthored (like any Blender model) and poses them from <fid>_poses.json (three.js quaternions per joint).
// usage: node tools/blender/mechs/mech_game.cjs <port> [outDir=docs/mechs/concept] [preset=3]
//   MECH_SRC=game: the game's own public/models/x_mech_<name>.glb instead, posed by its clips (ready = idle, jet = jet_fly)
//   (start a server first: PORT=3100 node server.js). writes ingame_<shot>.jpg + mechs_ingame.jpg (all of them)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const { execFileSync } = require('child_process');
const ROOT = path.join(__dirname, '../../..');
const [port = '3100', outArg, presetArg = '3'] = process.argv.slice(2);
const OUT = outArg || path.join(ROOT, 'docs/mechs/concept'), PR = Number(presetArg), SRC = path.join(ROOT, 'docs/mechs/concept');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
fs.mkdirSync(OUT, { recursive: true });

const SHOTS = [ // name, caption, what stands where, the camera (eye, target, fov)
  { name: 'lineup', cap: 'scale in the game: mannequin 1.8 m, PAPER PLANE, NIGHT SHIFT (too hd)',
    put: [['mq', [-3.6, 0, -16.5], 0.25], ['mech_paperplane', 'ready', 'A', [-0.6, 0, -16.5], 0.2], ['mech_nightshift', 'ready', 'A', [4.6, 0, -16.8], -0.25]],
    cam: [[-1.5, 3.2, -1.5], [0.7, 2.7, -16.6], 50] },
  { name: 'paperplane', cap: 'PAPER PLANE, colour A sky mail', put: [['mech_paperplane', 'ready', 'A', [0, 0, -16], 0.15], ['mq', [2.2, 0, -14.4], -0.4]],
    cam: [[-4.2, 3.4, -8.6], [0.1, 2.6, -16], 46] },
  { name: 'nightshift', cap: 'NIGHT SHIFT, colour A graveyard shift', put: [['mech_nightshift', 'ready', 'A', [0, 0, -16], 0.15], ['mq', [-2.6, 0, -13.8], 0.4]],
    cam: [[-4.4, 3.6, -8.2], [0.2, 2.9, -16], 48] },
  { name: 'colourB', cap: 'colour B: pink slip + overtime', put: [['mech_paperplane', 'ready', 'B', [-2.6, 0, -16.5], 0.3], ['mech_nightshift', 'ready', 'B', [2.8, 0, -16.8], -0.3]],
    cam: [[-0.5, 3.2, -4.5], [0.2, 2.7, -16.6], 50] },
  { name: 'jet', cap: 'PAPER PLANE jet mode, 3 m up', put: [['mech_paperplane', 'jet', 'A', [0, 3.0, -16], -0.9]],
    cam: [[-5.0, 4.4, -8.5], [0, 4.2, -16], 46] },
  { name: 'ns_sun', cap: 'NIGHT SHIFT up close in the sun: painted metal', put: [['mech_nightshift', 'ready', 'A', [0, 0, -16], -0.6]],
    cam: [[-2.6, 4.2, -11.2], [0.0, 4.3, -16], 40] },
  { name: '30m', cap: 'from the firing line, 30 m away, default fov 95', put: [['mech_paperplane', 'ready', 'A', [-3.2, 0, -20], 0.2], ['mech_nightshift', 'ready', 'A', [3.4, 0, -20], -0.2], ['mq', [0.2, 0, -20], 0]],
    cam: [[0, 1.75, 10], [0, 2.4, -20], 95] },
];

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1600, height: 900 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + (e.stack || e.message).split('\n').slice(0, 3).join(' | ')));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text().slice(0, 200)); });
  await pg.route('**/__mech/**', (r) => { // the concept files stay in docs (not shipped with the game)
    const f = path.join(SRC, path.basename(new URL(r.request().url()).pathname));
    if (!fs.existsSync(f)) return r.fulfill({ status: 404, body: '' });
    r.fulfill({ status: 200, body: fs.readFileSync(f), contentType: f.endsWith('.json') ? 'application/json' : 'model/gltf-binary' });
  });
  await pg.addInitScript((pr) => { localStorage.setItem('jf_giftseen_all', '1'); localStorage.setItem('jankfire', JSON.stringify({ name: 'SHOTS', killcam: false, jank: pr })); }, PR);
  await pg.goto(`http://localhost:${port}/`); await sleep(2500);
  await pg.click('#scr-main [data-mode="training"]', { timeout: 180000 });
  const ok = await pg.evaluate(async () => {
    const { G } = await import('/js/ctx.js'); const { MAP } = await import('/shared/map.js');
    for (let i = 0; i < 700 && !(G.joined && MAP.id === 'range'); i++) await new Promise((r) => setTimeout(r, 100));
    return G.joined && MAP.id === 'range' ? true : 'never got to the range: ' + MAP.id;
  });
  if (ok !== true) { console.log(ok); await b.close(); process.exit(1); }
  const info = await pg.evaluate(async (GAME) => {
    const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js');
    const THREE = await import('three'); const kit = await import('/js/glbkit.js'); const models = await import('/js/models.js');
    const css = document.createElement('style'); css.textContent = 'body > :not(#game) { display: none !important; }'; document.head.append(css);
    G.vmCamera.layers.disableAll();
    setInterval(() => { const q = window.__pin; if (q) { ME.pos = q.p.slice(); ME.vel = [0, 0, 0]; ME.yaw = q.yaw; ME.pitch = q.pitch; ME.hp = 100; } }, 4);
    setInterval(() => { for (const o of G.scene.children) if (o.isPoints) o.visible = false; G.remotes.forEach((r) => { if (r.ch && r.ch.root) r.ch.root.visible = false; }); }, 16);
    const draw = G.renderer.render.bind(G.renderer);
    G.renderer.render = (sc, cam) => {
      const f = window.__fov || 50; if (cam === G.camera && cam.fov !== f) { cam.fov = f; cam.near = 0.05; cam.updateProjectionMatrix(); }
      G.remotes.forEach((r) => { for (const o of [r.ch && r.ch.root, r.marker, r.tag]) if (o) o.visible = false; }); // (Training's dummies, every frame)
      return draw(sc, cam);
    };
    const load = (u) => new Promise((ok, bad) => kit.glbLoader().load(u, ok, undefined, bad));
    const M = {}, out = {};
    for (const id of ['mech_paperplane', 'mech_nightshift']) {
      const g = await load(GAME ? `/models/x_${id}.glb` : `/__mech/${id}_concept.glb`), poses = GAME ? { poses: {} } : await (await fetch(`/__mech/${id}_poses.json`)).json();
      const anims = g.animations || [];
      const took = kit.prepAuthored(id, g.scene);
      const meta = kit.metaOf(g.scene) || {};
      let tris = 0; g.scene.traverse((o) => { if (o.isMesh) tris += (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count) / 3; });
      const nodes = new Set(); g.scene.traverse((o) => o.name && nodes.add(o.name));
      out[id] = { took, tris: Math.round(tris), missing: Object.keys(meta.joints || {}).filter((n) => !nodes.has(n)), pal: meta.palettes };
      M[id] = { scene: g.scene, poses: poses.poses, meta, anims };
    }
    window.__M = M;
    window.__place = (list) => {
      if (window.__objs) for (const o of window.__objs) G.scene.remove(o);
      window.__objs = [];
      for (const it of list) {
        let o;
        if (it[0] === 'mq') { o = models.buildCharacter('#ff4fd8').root; o.position.set(...it[1]); o.rotation.y = it[2]; }
        else {
          const [id, pose, col, pos, yaw] = it, m = M[id]; o = m.scene.clone(true);
          const P = m.poses[pose] || { joints: {}, root_at: [0, 0, 0] };
          o.traverse((n) => { const q = P.joints[n.name]; if (q) n.quaternion.set(q[0], q[1], q[2], q[3]); });
          const clip = m.anims.find((a) => a.name === ({ ready: 'idle', jet: 'jet_fly' }[pose] || pose));
          if (clip) { const mx = new THREE.AnimationMixer(o); const a = mx.clipAction(clip); a.play(); mx.setTime(pose === 'jet' ? 0.3 : 0); }
          const holder = new THREE.Group(); holder.add(o); o.position.set(...P.root_at); holder.position.set(...pos); holder.rotation.y = yaw + Math.PI; o = holder; // (the mechs face -z: turn them to the cameras)
          if (col === 'B') { // colour option B: clone the role materials and swap their colours (names = <prefix>_<role>)
            const pal = m.meta.palettes.B, swap = new Map();
            o.traverse((n) => { if (!n.isMesh) return; n.material = [].concat(n.material).map((mt) => {
              const role = (mt.name || '').replace(/^[a-z]+_/, ''); if (!Object.hasOwn(pal, role)) return mt;
              if (!swap.has(mt)) { const c = mt.clone(); c.color.setHex(pal[role]); if (role === 'glow' || role === 'thrust') c.emissive.setHex(pal[role]); swap.set(mt, c); }
              return swap.get(mt); }); if (n.material.length === 1) n.material = n.material[0]; });
          }
        }
        o.traverse((n) => { if (n.isMesh) { n.castShadow = true; n.receiveShadow = true; n.frustumCulled = false; } });
        G.scene.add(o); window.__objs.push(o);
      }
    };
    window.__aim = (eye, tgt, fov) => {
      const dx = tgt[0] - eye[0], dy = tgt[1] - eye[1], dz = tgt[2] - eye[2];
      window.__fov = fov; window.__pin = { p: [eye[0], eye[1] - 1.6, eye[2]], yaw: Math.atan2(-dx, -dz), pitch: Math.atan2(dy, Math.hypot(dx, dz)) };
    };
    return out;
  }, process.env.MECH_SRC === 'game');
  console.log(JSON.stringify(info));
  const files = [], only = process.env.MECH_SHOTS ? process.env.MECH_SHOTS.split(',') : null;
  for (const s of SHOTS) {
    if (only && !only.includes(s.name)) continue;
    await pg.evaluate(async (s) => { window.__place(s.put); window.__aim(...s.cam); const { shadowDirty } = await import('/js/lighting.js'); shadowDirty(); }, s);
    await sleep(2500);
    const f = path.join(OUT, `ingame_${s.name}.jpg`);
    await pg.screenshot({ path: f, type: 'jpeg', quality: 88, timeout: 180000 });
    files.push([f, s.cap]); console.log('wrote', path.relative(ROOT, f));
  }
  await b.close();
  // a contact sheet with captions (3 x 2 at 800 x 450)
  const W = 800, H = 450, tmp = fs.mkdtempSync(path.join(require('os').tmpdir(), 'mechgame-')), cells = [];
  files.forEach(([f, cap], i) => {
    const o = path.join(tmp, `c${i}.png`), lab = cap.replace('(too hd)', PR === 3 ? '(too hd)' : `(preset ${PR})`).replace(/[:']/g, ' ');
    execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-i', f, '-vf', `scale=${W}:${H},drawbox=x=0:y=${H - 30}:w=${W}:h=30:color=0x120818@0.85:t=fill,drawtext=text='${lab}':x=10:y=${H - 23}:fontsize=17:fontcolor=0xffe14d`, o]);
    cells.push(o);
  });
  const args = []; for (const c of cells) args.push('-i', c);
  const lay = cells.map((_, i) => `${(i % 3) * W}_${Math.floor(i / 3) * H}`).join('|');
  execFileSync('ffmpeg', ['-loglevel', 'error', '-y', ...args, '-filter_complex', cells.length > 1 ? `xstack=inputs=${cells.length}:layout=${lay}:fill=black` : 'null', '-q:v', '3', path.join(OUT, 'mechs_ingame.jpg')]);
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log('wrote', path.relative(ROOT, path.join(OUT, 'mechs_ingame.jpg')));
  console.log(errs.length ? 'page errors:\n  ' + errs.slice(0, 8).join('\n  ') : '(0 page errors)');
  process.exit(errs.length ? 1 : 0);
})();
