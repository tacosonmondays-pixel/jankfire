// The zombies lobby's people in the game (x_lobby_deb / _gus / _marge.glb): close stills of each at a graphics preset,
// or a clip of each going idle -> talk (E) -> gesture (a pick). Needs a server (PORT=3100 node server.js).
//   node tools/blender/lobby/npc_shots.cjs <port> <outDir> stills 3,0     Too HD + Potato stills (+ the wide room)
//   node tools/blender/lobby/npc_shots.cjs <port> <outDir> clip 3         a webm per person (ffmpeg it to mp4)
// PW_LOCK=<path to pwlock.cjs> caps the headless browsers.
if (process.env.PW_LOCK) require(process.env.PW_LOCK);
const { chromium } = require('playwright');
const fs = require('fs');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const [port, OUT, mode = 'stills', presets = '3'] = process.argv.slice(2);
fs.mkdirSync(OUT, { recursive: true });
// where to stand to look at each (x, z, the yaw the camera looks along) and how far the camera sits
const WHO = { deb: { at: [-7.55, -6.25], yaw: 0.764, dist: 3.0, pitch: 0.02, pick: 2 },
  gus: { at: [0, -7.6], yaw: 0, dist: 3.2, pitch: 0.1, pick: 1 },
  marge: { at: [7.6, -5.5], yaw: -0.76, dist: 3.4, pitch: 0.12, pick: 3 } };

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const errs = [];
  for (const J of presets.split(',').map(Number)) {
    const ctx = await b.newContext({ viewport: { width: 1280, height: 720 }, ...(mode === 'clip' ? { recordVideo: { dir: OUT, size: { width: 1280, height: 720 } } } : {}) });
    const pg = await ctx.newPage();
    pg.on('pageerror', (e) => errs.push(e.message));
    await pg.addInitScript((j) => { localStorage.setItem('jf_giftseen_all', '1'); localStorage.setItem('jankfire', JSON.stringify({ name: 'taco', killcam: false, jank: j })); }, J);
    await pg.goto(`http://localhost:${port}/`); await sleep(2500);
    await pg.evaluate((j) => { const e = document.getElementById('jank'); e.value = String(j); e.dispatchEvent(new Event('change')); }, J);
    await pg.evaluate(() => document.querySelector('[data-hub="offline"]').click()); await sleep(500);
    await pg.evaluate(() => document.querySelector('[data-mode2="zm"]').click());
    const info = () => pg.evaluate(async () => (await import('/js/lobbyscenes/index.js')).lobbySceneInfo());
    for (let i = 0; i < 80; i++) { const x = await info(); if (x && x.extra && x.extra.rigs && x.extra.rigs.length >= 3) break; await sleep(250); }
    await sleep(1500);
    const inf = await info(); console.log('preset', J, 'rigs', JSON.stringify(inf && inf.extra && inf.extra.rigs));
    const stand = (w, show) => pg.evaluate(async ([w, show]) => {
      const m = await import('/js/lobbyscenes/index.js'), W = m.lobbySceneWalk();
      W.me.pos = [w.at[0], 0, w.at[1]]; W.me.yaw = w.yaw; W.W.camYaw = w.yaw; W.W.dist = w.dist; W.W.camPitch = w.pitch;
      W.me.ch.root.visible = show;
    }, [w, show]);
    if (mode === 'stills') {
      await stand({ at: [0, 7], yaw: 0, dist: 9, pitch: 0.42 }, false); await sleep(1500);
      await pg.screenshot({ path: `${OUT}/room_j${J}.jpg`, quality: 88 });
      for (const [k, w] of Object.entries(WHO)) {
        await stand(w, false); await sleep(2200);
        await pg.screenshot({ path: `${OUT}/${k}_j${J}.jpg`, quality: 88 });
      }
    } else {
      for (const [k, w] of Object.entries(WHO)) {
        await stand({ ...w, at: [w.at[0] + Math.sin(w.yaw) * 4, w.at[1] + Math.cos(w.yaw) * 4] }, false); await sleep(1200);
        const t0 = Date.now(); console.log('clip', k, 'starts', t0);
        await stand(w, false); await sleep(3500);                            // idle (and the hi as you walk up: talk)
        await pg.keyboard.press('KeyE'); await sleep(3000);                  // talk
        await pg.evaluate((i) => { const bs = document.querySelectorAll('#lsTags .ls-pick button'); if (bs[i]) bs[i].click(); }, w.pick);
        await sleep(3600);                                                   // the gesture
        await pg.keyboard.press('KeyE'); await sleep(600);
      }
    }
    await ctx.close();
  }
  console.log('errors:', JSON.stringify(errs));
  await b.close();
})();
