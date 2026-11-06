// The Overdrive Rig in the real game (Training, the killstreak itself), two ways:
//   fp: first person: it comes on (the frame assembles), wind-up, rocket punch, block, thrusters, missiles.
//       screenshots fp_<step>.png at each step (+ a video with --video)
//   3p: the rig the way other players see it: one stands in front of you on the range and runs through the same pose
//       code remote rigs use (assemble, stomp about, wind-up + punch, thrusters, missile pods, block, leap), with a video
// usage: node tools/blender/rig_game.cjs <port> <outDir> [fp|3p|both] [preset=3] [--video]
//   (start the server first: PORT=<port> node server.js). prints whether the Blender rig was used + page errors
const { chromium } = require('playwright');
const fs = require('fs');
const args = process.argv.slice(2).filter((a) => !a.startsWith('--')), flags = new Set(process.argv.slice(2).filter((a) => a.startsWith('--')));
const [port = '3100', out = '.', mode = 'both', preset = '3'] = args;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const jank = Number(preset), video = flags.has('--video');

async function open(b, tag) {
  const ctx = await b.newContext({ viewport: { width: 960, height: 540 }, ...(video ? { recordVideo: { dir: `${out}/raw_${tag}`, size: { width: 960, height: 540 } } } : {}) });
  const pg = await ctx.newPage();
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + (e.stack || e.message).split('\n').slice(0, 3).join(' | ')));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.addInitScript((jank) => localStorage.setItem('jankfire', JSON.stringify({ name: 'RIGTEST', killcam: false, jank, loadout: { primary: 'ar', secondary: 'revolver', melee: 'knife', item: 'frag', streaks: ['overdrive', 'wreckingball', 'moonboots'] } })), jank);
  await pg.goto(`http://localhost:${port}/`); await sleep(2500);
  await pg.evaluate(async () => { // the rig's models (they load when the rig is in your killstreaks: wait for them)
    const k = await import('/js/glbkit.js');
    for (let i = 0; i < 150 && !Object.keys(k.AUTHORED).length; i++) await new Promise((r) => setTimeout(r, 100));
    k.prefetch(['x_rig', 'x_rigarms', 'pj_rigmissile']);
    for (let i = 0; i < 300 && k.lateBusy(); i++) await new Promise((r) => setTimeout(r, 100));
  });
  await pg.click('#scr-main [data-mode="training"]'); await sleep(4000);
  return { ctx, pg, errs };
}
async function finish(ctx, pg, tag) {
  const v = video ? pg.video() : null;
  await ctx.close();
  if (v) { const p = await v.path(); fs.renameSync(p, `${out}/rig_${tag}.webm`); }
}

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  let bad = 0;
  if (mode === 'fp' || mode === 'both') {
    const { ctx, pg, errs } = await open(b, 'fp');
    const slot = await pg.evaluate(async () => { const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js'); ME.pitch = -0.05; return (G.activeStreaks || []).indexOf('overdrive'); });
    await pg.mouse.move(480, 270);
    const shot = (n) => pg.screenshot({ path: `${out}/fp_${n}.png` });
    await pg.keyboard.press('Digit' + (5 + Math.max(0, slot))); await sleep(300); await shot('assembling'); await sleep(2000); await shot('on');
    await pg.mouse.down(); await sleep(900); await shot('charge'); await pg.mouse.up(); await sleep(110); await shot('punch'); await sleep(900);
    await pg.mouse.down({ button: 'right' }); await sleep(600); await shot('block'); await pg.mouse.up({ button: 'right' }); await sleep(500);
    await pg.keyboard.press('KeyE'); await sleep(160); await shot('thrusters'); await sleep(1300);
    await pg.keyboard.press('KeyG'); await sleep(450); await shot('missiles'); await sleep(1500);
    const st = await pg.evaluate(async () => { const { RS } = await import('/js/rig.js'); const rm = await import('/js/rigmodel.js'); const ra = await import('/js/rigarms.js'); const k = await import('/js/glbkit.js'); return { on: RS.on, rig: rm.rigIsBlender(), arms: !!k.AUTHORED.x_rigarms, missile: !!k.AUTHORED.pj_rigmissile, armsBuilt: !!ra.armsObj() }; });
    console.log('fp', JSON.stringify(st), errs.length ? '\n' + errs.join('\n') : '(no page errors)');
    bad += errs.length;
    await finish(ctx, pg, 'fp');
  }
  if (mode === '3p' || mode === 'both') {
    const { ctx, pg, errs } = await open(b, '3p');
    // one rig on the range in front of you, driven by poseRig through a timeline (what everyone else sees)
    const res = await pg.evaluate(async () => {
      const THREE = await import('three');
      const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js'); const rm = await import('/js/rigmodel.js');
      const { raycast } = await import('/shared/physics.js'); const { BOXES } = await import('/shared/map.js');
      if (G.vmScene) Object.defineProperty(G.vmScene, 'visible', { get: () => false, set: () => {} }); // (no gun in your hands for this one)
      rm.rigReset();
      const inst = rm.buildRig('#ff4fd8', { outline: true });
      // walk forward until nothing (the range's fence) stands between you and a rig 5 m further on
      const fwd = [-Math.sin(ME.yaw), -Math.cos(ME.yaw)], me = ME.pos.slice();
      for (let i = 0; i < 30; i++) {
        const e = [me[0], me[1] + 1.6, me[2]], tgt = [me[0] + fwd[0] * 5, me[1] + 1.4, me[2] + fwd[1] * 5], d = [tgt[0] - e[0], tgt[1] - e[1], tgt[2] - e[2]], l = Math.hypot(...d);
        const h = raycast(e, d.map((x) => x / l), l, BOXES), h2 = raycast([e[0], me[1] + 0.4, e[2]], [fwd[0], 0, fwd[1]], 5.5, BOXES);
        if (!h && !h2) break;
        me[0] += fwd[0]; me[2] += fwd[1];
      }
      const yaw0 = ME.yaw;
      setInterval(() => { ME.pos = me.slice(); ME.vel = [0, 0, 0]; ME.yaw = yaw0; ME.pitch = 0.1; }, 10);
      const at = [me[0] + fwd[0] * 5, me[1], me[2] + fwd[1] * 5];
      inst.root.position.set(at[0], at[1], at[2]);
      G.scene.add(inst.root);
      const T = [ // [t0, t1, state(u 0..1)]
        [0, 1.5, (u) => ({ on: u })],
        [1.5, 2.6, () => ({})],
        [2.6, 3.9, (u) => ({ spd: 3.5, fwd: 3.5 })],
        [3.9, 4.8, (u) => ({ charge: u })],
        [4.8, 5.6, (u, t) => ({ punchT: t - 4.8, dash: u < 0.3 ? 1 : 0 })],
        [5.6, 6.5, (u, t) => ({ thrustT: t - 5.6, air: true, vy: 6 - u * 10 })],
        [6.5, 7.0, (u, t) => ({ landT: t - 6.5, landK: 0.8 })],
        [7.0, 8.6, (u, t) => ({ missT: t - 7.0 })],
        [8.6, 9.8, () => ({ block: true })],
        [9.8, 10.8, (u) => ({ leap: Math.min(1, u * 2) })],
      ];
      return await new Promise((done) => {
        const t0 = performance.now(); let last = t0, y0 = at[1];
        const step = () => {
          const now = performance.now(), t = (now - t0) / 1000, dt = Math.min(0.05, (now - last) / 1000); last = now;
          const seg = T.find((s) => t >= s[0] && t < s[1]);
          if (!seg) { done({ blender: rm.rigIsBlender() }); return; }
          const u = (t - seg[0]) / (seg[1] - seg[0]), s = { spd: 0, on: 1, pitch: 0, ...seg[2](u, t) };
          // a little walk forward, a hop on the thrusters, turned three-quarters so you see its side and its pods
          let ry = ME.yaw + Math.PI + 0.55 * Math.sin(t * 0.45);
          if (s.spd) { at[0] -= Math.sin(ry) * s.spd * dt * 0.4; at[2] -= Math.cos(ry) * s.spd * dt * 0.4; }
          inst.root.position.set(at[0], y0 + (s.air ? Math.sin(u * Math.PI) * 2.2 : 0), at[2]);
          inst.root.rotation.y = ry;
          rm.poseRig(inst, s, dt);
          requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
      });
    });
    await pg.screenshot({ path: `${out}/3p_end.png` });
    console.log('3p', JSON.stringify(res), errs.length ? '\n' + errs.join('\n') : '(no page errors)');
    bad += errs.length;
    await finish(ctx, pg, '3p');
  }
  await b.close();
  process.exitCode = bad ? 1 : 0;
})();
