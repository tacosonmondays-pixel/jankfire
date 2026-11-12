// The Gut Choir in the Choir Lung, in a real story run (the slice city, Too HD, the story's own actors and choir.js):
// stills from the door and up the aisle, and a clip: they hum and sway together, sing a phrase, you step in through
// the door and every head turns to you on the same frame, you walk up the aisle between them (the heads follow), back
// out, and they snap back to the hymn. The story runs in capture mode: each frame is exactly 1/FPS of story time.
//   SP=tests/rig PORT=3112 node tools/blender/cast/choirlung.cjs <outdir> [stills|clip|both]
// clip frames go to <outdir>/lung/f_00000.jpg (ffmpeg makes the mp4)
const path = require('path'), fs = require('fs');
const { boot, tp, settle, sleep } = require(path.join(__dirname, '../../../tests/story/e2e/enc_util.cjs'));
const [OUT = 'choir_lung', MODE = 'both'] = process.argv.slice(2);
const FPS = 24;
(async () => {
  fs.mkdirSync(path.join(OUT, 'lung'), { recursive: true });
  const { b, pg, ev, errs } = await boot({ hd: true });
  const DOOR = [-268, 40, -194.5];
  await tp(ev, DOOR, 0); await settle(ev, DOOR, 9000);
  await ev(() => { const s = document.createElement('style'); s.textContent = '#hud,#crosshair,#stLayer,#questHud,#qhud,.hud,#hotbar,#killfeed,#minimap{display:none!important}'; document.head.append(s); window.JF_STORY.capture = true; });
  const step = async (n = 1) => { for (let i = 0; i < n; i++) { await ev((dt) => { window.JF_STORY.capStep = dt; }, 1 / FPS); await pg.waitForFunction(() => window.JF_STORY.capStep === 0, null, { polling: 'raf' }); } await ev(() => new Promise((r) => requestAnimationFrame(() => r()))); };
  const shot = (pos, look, fov = 50) => ev(async ([pos, look, fov]) => { const THREE = await import('three'); const { wantShot } = await import('/js/story/camctl.js'); wantShot({ pos: new THREE.Vector3(...pos), look: new THREE.Vector3(...look), fov, cut: true, blend: 0.01, follow: 99 }); }, [pos, look, fov]);
  const me = (p) => ev(async (p) => { const { ME } = await import('/js/player.js'); ME.pos = p.slice(); ME.vel = [0, 0, 0]; }, p);
  const C = () => ev(async () => { const c = await import('/js/story/choir.js'); const D = c.choirState(); return { on: D.on, n: D.list.length, looks: D.list.map((a) => a.L.look + ':' + (a.L.blender ? 'B' : 'code')), stare: D.stareT, next: D.next }; });
  const sing = () => ev(async () => { const c = await import('/js/story/choir.js'); c.choirState().next = 0; });
  const snap = (f) => pg.screenshot({ path: path.join(OUT, f), type: 'jpeg', quality: 90 });
  await step(30); console.log('choir', JSON.stringify(await C()));
  if (MODE !== 'clip') {
    await ev(async () => { const c = await import('/js/story/choir.js'); c.choirState().next = 99; c.choirState().cool = 99; }); // (no singing, no stares while we line the stills up)
    await shot([-268, 41.75, -194.8], [-268, 41.1, -210.6], 42); await step(12); await snap('choir_lung_door.jpg');
    await shot([-268.3, 41.6, -203.2], [-268, 41.2, -210.8], 55); await step(12); await snap('choir_lung_aisle.jpg');
    await shot([-266.4, 41.8, -206.6], [-270.7, 41.3, -210.7], 46); await step(12); await snap('choir_lung_west_row.jpg');
    await shot([-269.4, 41.7, -207.2], [-265.3, 41.2, -210.6], 46); await step(12); await snap('choir_lung_east_row.jpg');
    await sing(); await shot([-268.3, 41.6, -203.2], [-268, 41.25, -210.8], 55); await step(Math.round(FPS * 3.2)); await snap('choir_lung_sing.jpg');
    await ev(async () => { const c = await import('/js/story/choir.js'); c.choirState().next = 99; c.choirState().cool = 0; });
    await step(Math.round(FPS * 2));
    await me([-268, 40, -205.5]); await shot([-268, 41.65, -205.3], [-268, 41.3, -211], 60); await step(Math.round(FPS * 1.4)); await snap('choir_lung_heads.jpg'); // you, up the aisle: every head on you
    console.log('after stare', JSON.stringify(await C()));
    await me(DOOR); await step(Math.round(FPS * 5));
  }
  if (MODE !== 'stills') {
    await ev(async () => { const c = await import('/js/story/choir.js'); const D = c.choirState(); D.next = 3.5; D.cool = 0; D.wasIn = false; D.stareT = -1; });
    await me(DOOR);
    let f = 0;
    const rec = async (n, fn) => { for (let i = 0; i < n; i++) { if (fn) await fn(i / n); await step(); await pg.screenshot({ path: path.join(OUT, 'lung', `f_${String(f++).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 85 }); } };
    const lerp = (a, c, t) => a.map((x, i) => x + (c[i] - x) * t);
    await shot([-266.9, 41.75, -199.2], [-268.2, 41.15, -210.8], 50);
    await rec(FPS * 9); // the hum, then a phrase together
    const IN = [-268, 40, -201.5], UP = [-268, 40, -207.4];
    await rec(Math.round(FPS * 1.2), (t) => me(lerp(DOOR, IN, t))); // you step in: every head, at once
    await rec(Math.round(FPS * 2.5));
    await shot([-266.4, 41.7, -214.6], [-268, 41.3, -205], 55); // (from behind the stalls, looking back at you)
    await rec(Math.round(FPS * 3.5), (t) => me(lerp(IN, UP, t))); // up the aisle between them: the heads follow you
    await rec(Math.round(FPS * 1.5));
    await shot([-266.9, 41.75, -199.2], [-268.2, 41.15, -210.8], 50);
    await rec(Math.round(FPS * 2.5), (t) => me(lerp(UP, [-268, 40, -192], t))); // and out
    await rec(Math.round(FPS * 4)); // back to the hymn, all at once
    console.log('frames', f);
  }
  console.log(errs.filter((e) => !/favicon|404/.test(e)).join('\n') || 'no errors');
  await b.close();
})();
