// THE HEADLINER in the real game (story mode, his rehearsal: ?story=1&jesterlord=1), photographed at Too HD and Potato:
//   node tools/blender/cast/jlgame.cjs <port> <outDir> [presets: 3,0]
// -> jl_ingame_hd_<shot>.jpg (jank 3) and jl_ingame_potato_<shot>.jpg (jank 0). The rehearsal is held on one clip at a
// time and you are stood where the shot wants you; nothing here does damage.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { execSync } = require('child_process');
const [PORT = 3000, OUT = '.', PRESETS = '3,0'] = process.argv.slice(2);
// [name, clip, clip time to wait for, how far he stands, how far to his side (m), look-up pitch, walk across (m) or 0]
const SHOTS = [['idle_7m', 'jl_idle', 1.2, 7, 0, 0.2, 0], ['talk', 'jl_talk', 0.5, 5.2, 0.4, 0.3, 0], ['bow', 'jl_bow', 1.8, 6.5, 1.2, 0.12, 0],
  ['scuttle', 'jl_walk', 0, 8.5, 0, 0.12, 6], ['web_hang', 'jl_hang', 3.4, 7.5, 0.5, 0.5, 0], ['leg_off', 'jl_leg_off', 1.5, 7.5, 1.4, 0.16, 0],
  ['from_30m', 'jl_idle', 1.0, 30, 0, 0.05, 0]];
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const errs = [];
  for (const jank of PRESETS.split(',').map(Number)) {
    const tag = jank === 3 ? 'hd' : jank === 0 ? 'potato' : 'jank' + jank;
    const ctx = await b.newContext({ viewport: { width: 1280, height: 720 } });
    const pg = await ctx.newPage(); pg.on('pageerror', (e) => errs.push(tag + ': ' + e.message));
    await pg.addInitScript((j) => { localStorage.setItem('jf_giftseen_all', '1'); if (!sessionStorage.getItem('jfInit')) { localStorage.setItem('jankfire', JSON.stringify({ name: 'director', killcam: false, jank: j })); sessionStorage.setItem('jfInit', '1'); } }, jank);
    await pg.goto(`http://localhost:${PORT}/?story=1&jesterlord=1`);
    const pump = (ms) => new Promise((r) => setTimeout(r, ms));
    const dismiss = () => pg.evaluate(() => { for (const b of document.querySelectorAll('button')) if (/^(LATER|NICE)$/.test(b.textContent.trim()) && b.offsetParent) b.click(); }).catch(() => {});
    await pump(1500);
    for (let i = 0; i < 150 && !(await pg.evaluate(() => !!document.getElementById('storyBtn'))); i++) await pump(100);
    // (story mode doesn't wait for the cast; load him first so he is the model, not the code puppet)
    console.log(tag, 'his model loaded first:', await pg.evaluate(async () => (await import('/js/story/looks.js')).loadCast(['jester_lord'], 180000)));
    await pg.evaluate(() => { localStorage.removeItem('jfStorySaves'); document.getElementById('storyBtn').click(); });
    for (let i = 0; i < 150 && !(await pg.evaluate(() => !!document.querySelector('#storyPick .st-slot .st-btn'))); i++) await pump(100);
    await pg.evaluate(() => document.querySelector('#storyPick .st-slot .st-btn').click());
    for (let i = 0; i < 800 && !(await pg.evaluate(() => !!window.JF_JLP)); i++) await pump(250);
    if (!(await pg.evaluate(() => !!window.JF_JLP))) { errs.push(tag + ': the rehearsal never started'); await ctx.close(); continue; }
    await dismiss();
    const msFrame = await pg.evaluate(() => new Promise((res) => { const t0 = performance.now(); let n = 0; const f = () => { if (++n >= 4) res(Math.round((performance.now() - t0) / n)); else requestAnimationFrame(f); }; requestAnimationFrame(f); }));
    console.log(tag, 'ms a frame once warm', msFrame);
    const info = await pg.evaluate(async () => { const P = window.JF_JLP; P.len = 1e9; const { ME } = await import('/js/player.js'); window.__ME = ME; return { blender: !!P.a.L.blender, at: P.home, you: ME.pos.map((v) => Math.round(v * 10) / 10), map: (await import('/shared/map.js')).MAP.id }; });
    console.log(tag, JSON.stringify(info));
    for (const [name, clip, t, dist, side, pitch, across] of SHOTS) {
      await pg.evaluate(async ([clip, dist, side, pitch, across]) => { const P = window.JF_JLP, a = P.a, ME = window.__ME, { dropTo, walkTo } = await import('/js/story/actors.js');
        // (he is stood where the shot wants him from you: moving you to him is a teleport the server undoes)
        a.path = null; a.yaw = a.home.face;
        const f = [-Math.sin(a.yaw), -Math.cos(a.yaw)], r = [Math.cos(a.yaw), -Math.sin(a.yaw)]; // (his forward, his right)
        const p = [ME.pos[0], ME.pos[1], ME.pos[2]];
        a.pos[0] = p[0] - f[0] * dist - r[0] * (side - across / 2); a.pos[2] = p[2] - f[1] * dist - r[1] * (side - across / 2); a.pos[1] = dropTo([a.pos[0], P.home[1], a.pos[2]], 3);
        window.__her = across ? null : [a.pos[0], a.pos[1], a.pos[2]];
        window.__stand = { p, yaw: Math.atan2(-(a.pos[0] + r[0] * across / 2 - p[0]), -(a.pos[2] + r[1] * across / 2 - p[2])), pitch };
        if (across) walkTo(a, [[a.pos[0] + r[0] * across, a.pos[1], a.pos[2] + r[1] * across]], 1.6);
        P.label = clip.toUpperCase(); P.marks = []; window.JF_JL.play(a, clip); window.__t0 = performance.now(); }, [clip, dist, side, pitch, across]);
      const hold = () => pg.evaluate(async () => { const sc = await import('/js/story/scene.js'); if (sc.playing()) sc.skipScene(); const S = window.__stand, ME = window.__ME, A = window.JF_JLP.a; ME.pos[0] = S.p[0]; ME.pos[2] = S.p[2]; ME.vel = [0, 0, 0]; ME.yaw = S.yaw; ME.pitch = S.pitch;
        if (window.__her) { A.pos[0] = window.__her[0]; A.pos[1] = window.__her[1]; A.pos[2] = window.__her[2]; } const c = A.clip; return c ? [c.name, c.t, (performance.now() - window.__t0) / 1000] : null; });
      for (let i = 0; i < 400; i++) { const c = await hold(); if (c && c[0] === clip && (across ? c[2] >= 2.2 : c[1] >= t)) break; await pump(120); }
      await dismiss(); await hold();
      const png = path.join(OUT, `jl_ingame_${tag}_${name}.png`), jpg = png.replace(/png$/, 'jpg');
      await pg.screenshot({ path: png, timeout: 600000 }); execSync(`ffmpeg -loglevel error -y -i "${png}" -q:v 3 "${jpg}"`); fs.unlinkSync(png); console.log('wrote', jpg);
    }
    await ctx.close();
  }
  await b.close();
  console.log(errs.length ? 'ERRORS:\n' + [...new Set(errs)].join('\n') : 'no errors');
})();
