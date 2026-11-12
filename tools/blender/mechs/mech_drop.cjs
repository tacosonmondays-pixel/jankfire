// A MECH DROP in the real game, filmed: Training range, the game's own buildMech / poseMech / mech camera with the
// hero kit (public/js/mechlook.js), at a graphics preset. Plays the client side of a drop (the server's 'call' then
// 'land' messages, fed to the client's own handler: nothing on the server changes) and records it.
// usage: node tools/blender/mechs/mech_drop.cjs <port> <outDir> [frame=nightshift] [preset=3] [video=1]
//   writes drop_<frame>_<preset>.mp4 (real time: the call, the fall, the landing, seen from where you stand), drop_<frame>_<preset>.jpg (stills: the fall, the
//   landing shot frozen at points of hero_intro, the held signature pose, a close-up). start a server first.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const { execFileSync } = require('child_process');
const [port = '3100', outDir = '.', frame = 'nightshift', presetArg = '3', video = '1'] = process.argv.slice(2);
const PR = Number(presetArg), tag = `${frame}_${PR}`, sleep = (ms) => new Promise((r) => setTimeout(r, ms));
fs.mkdirSync(outDir, { recursive: true });
const W = 1280, H = 720;

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const vdir = path.join(outDir, `.vid_${tag}`);
  const ctx = await b.newContext({ viewport: { width: W, height: H }, ...(video === '1' ? { recordVideo: { dir: vdir, size: { width: W, height: H } } } : {}) });
  const pg = await ctx.newPage(), errs = [], v0 = Date.now(); // (v0: the video's clock, to cut the drop out of it)
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + (e.stack || e.message).split('\n').slice(0, 3).join(' | ')));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text().slice(0, 200)); });
  await pg.addInitScript((pr) => { localStorage.setItem('jf_giftseen_all', '1'); localStorage.setItem('jankfire', JSON.stringify({ name: 'SHOTS', killcam: false, jank: pr })); }, PR);
  await pg.goto(`http://localhost:${port}/`); await sleep(2500);
  await pg.click('#scr-main [data-mode="training"]', { timeout: 180000 });
  const ok = await pg.evaluate(async (F) => {
    const { G } = await import('/js/ctx.js'); const { MAP } = await import('/shared/map.js'); const { ME } = await import('/js/player.js');
    for (let i = 0; i < 700 && !(G.joined && MAP.id === 'range'); i++) await new Promise((r) => setTimeout(r, 100));
    if (!(G.joined && MAP.id === 'range')) return 'never got to the range: ' + MAP.id;
    const mm = await import('/js/mechmodel.js');
    let warm = null;
    for (let i = 0; i < 300; i++) { warm = mm.buildMech(F, '#ff4fd8'); if (warm.glb) break; mm.freeMech(warm); warm = null; await new Promise((r) => setTimeout(r, 200)); } // (asks for the hero file, waits)
    if (warm) { // (software GL: the first sight of its shaders stalls for seconds, so they compile here, not during the 1.5 s landing shot)
      warm.root.position.set(0, 0, -12); G.scene.add(warm.root);
      for (let i = 0; i < 30; i++) await new Promise((r) => requestAnimationFrame(r));
      mm.freeMech(warm);
    }
    const css = document.createElement('style'); css.textContent = 'body > :not(#game) { display: none !important; }'; document.head.append(css);
    G.vmCamera.layers.disableAll();
    window.__pin = { p: [0.4, 0, -3], yaw: 0, pitch: 0.06 };
    G.scene.onBeforeRender = (r, sc, cam) => { const c = window.__cam; if (!c) return; cam.position.fromArray(c.e); cam.lookAt(c.t[0], c.t[1], c.t[2]); if (c.fov && cam.fov !== c.fov) { cam.fov = c.fov; cam.updateProjectionMatrix(); } cam.updateMatrixWorld(); }; // (stills: the script holds the camera)
    setInterval(() => { const q = window.__pin; ME.pos = q.p.slice(); ME.vel = [0, 0, 0]; ME.yaw = q.yaw; ME.pitch = q.pitch; ME.hp = 100;
      G.remotes.forEach((r) => { if (r.ch && r.ch.root) r.ch.root.visible = false; if (r.marker) r.marker.visible = false; if (r.tag) r.tag.visible = false; }); }, 4);
    return true;
  }, frame);
  if (ok !== true) { console.log(ok); await b.close(); process.exit(1); }
  await sleep(1500);
  const feed = (m) => pg.evaluate(async (m) => { const { net } = await import('/js/net.js'); const { G } = await import('/js/ctx.js'); m.o = G.myId; net.ws.onmessage({ data: JSON.stringify({ t: 'mech', ...m }) }); }, m);
  const P = [0, 0, -16], YAW = Math.PI; // (16 m out, facing you)
  const shots = []; // [file, caption]
  const shot = async (name, cap) => { const f = path.join(outDir, `.s_${tag}_${name}.jpg`); await pg.screenshot({ path: f, type: 'jpeg', quality: 88 }); shots.push([f, cap]); };
  // 1. the call and the fall (2.5 s), the real thing in real time
  const tc = Date.now(), cut = [(tc - v0) / 1000 - 1.5, 0];
  await feed({ k: 'call', id: 990, f: frame, p: P, yaw: YAW, ms: 2500 });
  await pg.evaluate(() => { window.__pin.pitch = 0.32; }); // (look up at it)
  await sleep(1100); await shot('fall', 'the fall: drop_fall + contrails');
  await pg.evaluate(() => { window.__pin.pitch = 0.06; });
  await sleep(Math.max(0, 2500 - (Date.now() - tc)));
  const t0 = Date.now();
  await feed({ k: 'land', id: 990, f: frame, p: P, yaw: YAW });
  await sleep(Math.max(0, 3600 - (Date.now() - t0))); await shot('held', 'held: what you see from 13 m away'); cut[1] = (Date.now() - v0) / 1000 + 2;
  await sleep(600);
  // 2. stills: the landing shot frozen at points of hero_intro (the camera held where it was at that moment)
  // the landing shot's own camera (mechCam's hero branch: low, off to the side, orbiting) held at u seconds in,
  // the mech's hero_intro frozen at t seconds (a slow software GPU can't play the 1.5 s shot in real time)
  const freeze = (t, u, cam) => pg.evaluate(async ([t, u, cam]) => {
    const { mechDebug } = await import('/js/mech.js'); const { WM } = mechDebug(); const w = WM.get(990);
    if (!w || !w.inst || !w.inst.act) return 'no mech';
    w.inst.act.time = t; w.inst.act.timeScale = 0; w.inst.mixer.update(0);
    if (cam) { window.__cam = cam; return w.inst.clip; }
    const p = w.p, a = Math.atan2(0.4 - p[0], -3 - p[2]) - 0.2 + 0.55 + Math.min(1, u / 1.5) * 0.4, R = Math.max(2.5, 6.5 - Math.min(1, u / 1.5) * 1.2);
    window.__cam = { e: [p[0] + Math.sin(a) * R, p[1] + 0.6 + 0.04 * R, p[2] + Math.cos(a) * R], t: [p[0], p[1] + 3.9, p[2]] };
    return w.inst.clip;
  }, [t, u, cam]);
  const D = frame === 'nightshift' ? 1.25 : 1, ns = frame === 'nightshift';
  const STILLS = [[0.05 * D, 0.1, 'hero_intro: the superhero landing'], [0.5 * D, 0.45, 'the beat: looking up'], [(ns ? 0.92 : 0.8) * D, 0.8, 'the gather'],
    [(ns ? 1.06 : 1.0) * D, 1.0, ns ? 'the sword goes in' : 'up: wings out, pods up'], [1.7 * D, 1.4, 'the signature pose (held)']];
  for (const [t, u, cap] of STILLS) {
    const c = await freeze(t, u); if (c !== 'hero_intro') errs.push('freeze: ' + c);
    await sleep(1800); await shot('t' + Math.round(t * 100), cap);
  }
  // a test spray on each decal slot (sprayOnMech, the hook sprays / skins will use)
  const sprayed = await pg.evaluate(async () => {
    const THREE = await import('three'); const { mechDebug } = await import('/js/mech.js'); const { sprayOnMech } = await import('/js/mechlook.js');
    const c = document.createElement('canvas'); c.width = c.height = 128; const x = c.getContext('2d');
    x.fillStyle = '#ffe14d'; x.beginPath(); x.arc(64, 64, 56, 0, 7); x.fill(); x.lineWidth = 8; x.strokeStyle = '#120818'; x.stroke();
    x.fillStyle = '#120818'; x.fillRect(40, 40, 12, 20); x.fillRect(76, 40, 12, 20); x.beginPath(); x.arc(64, 72, 28, 0.2, Math.PI - 0.2); x.stroke();
    x.font = 'bold 22px sans-serif'; x.textAlign = 'center'; x.fillStyle = '#ff00dc'; x.fillText('JANK', 64, 122);
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
    const w = mechDebug().WM.get(990); return [0, 1].map((k) => !!sprayOnMech(w.inst, k, t));
  });
  if (!sprayed.every(Boolean)) errs.push('spray slots: ' + JSON.stringify(sprayed));
  // 3. close-ups: the upper body from the front-left and a three-quarter from the right (rim light, ink, decals, glows)
  const hy = ns ? 3.9 : 3.4;
  await freeze(1.7 * D, 0, { e: [P[0] - 2.4, hy + 0.6, P[2] + 4.6], t: [P[0] + 0.1, hy, P[2]], fov: 50 }); await sleep(1800); await shot('close', 'close-up: rim light, ink, decals, glows');
  fs.copyFileSync(shots[shots.length - 1][0], path.join(outDir, `drop_${tag}_close.jpg`));
  await freeze(1.7 * D, 0, { e: [P[0] - 5.2, 2.2, P[2] + 6.4], t: [P[0], hy - 0.6, P[2]], fov: 55 }); await sleep(1800); await shot('q', 'three-quarter, low');
  fs.copyFileSync(shots[shots.length - 1][0], path.join(outDir, `drop_${tag}_q.jpg`));
  await freeze(1.7 * D, 0, { e: [P[0] + 3.4, hy + 1.2, P[2] - 5.6], t: [P[0], hy - 0.2, P[2]], fov: 50 }); await sleep(1800); await shot('back', 'from behind: stickers, the test sprays');
  fs.copyFileSync(shots[shots.length - 1][0], path.join(outDir, `drop_${tag}_back.jpg`));
  const info = await pg.evaluate(async () => {
    const { mechDebug } = await import('/js/mech.js'); const w = mechDebug().WM.get(990); const L = w && w.inst && w.inst.look;
    return L ? { glows: L.glows.length, mats: L.mats.length, outline: L.outline.length, trails: L.trails.length, events: Object.keys(L.events).length, slots: L.slots.length } : null;
  });
  await pg.close(); await ctx.close(); await b.close();
  // the stills on one sheet (2 rows), the video to mp4
  const n = shots.length, cols = Math.ceil(n / 2);
  const args = []; for (const [f] of shots) args.push('-i', f);
  const lab = shots.map(([, c], i) => `[${i}:v]scale=640:360,drawtext=text='${c.replace(/[':,]/g, ' ')}':x=10:y=330:fontsize=18:fontcolor=0xffe14d:box=1:boxcolor=0x120818@0.85:boxborderw=6[v${i}]`).join(';');
  const pad = n % 2 ? `;color=c=0x120818:s=640x360:d=1[vpad]` : '';
  const ins = shots.map((_, i) => `[v${i}]`).join('') + (n % 2 ? '[vpad]' : '');
  const lay = Array.from({ length: cols * 2 }, (_, i) => `${(i % cols) * 640}_${Math.floor(i / cols) * 360}`).join('|');
  const sheet = path.join(outDir, `drop_${tag}.jpg`);
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', ...args, '-filter_complex', `${lab}${pad};${ins}xstack=inputs=${cols * 2}:layout=${lay}`, '-frames:v', '1', '-q:v', '3', sheet]);
  for (const [f] of shots) fs.unlinkSync(f);
  if (video === '1') {
    const v = fs.readdirSync(vdir).find((x) => x.endsWith('.webm'));
    if (v) execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-ss', String(Math.max(0, cut[0])), '-to', String(cut[1]), '-i', path.join(vdir, v), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '24', '-movflags', '+faststart', path.join(outDir, `drop_${tag}.mp4`)]);
    fs.rmSync(vdir, { recursive: true, force: true });
  }
  console.log(sheet, JSON.stringify(info), errs.length ? errs.slice(0, 8) : '(0 page errors)');
  process.exit(errs.length ? 1 : 0);
})();
