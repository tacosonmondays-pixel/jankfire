// MADAM CHAIR in the real game (story mode, her rehearsal: ?story=1&hatlord=1), photographed at Too HD and Potato:
//   node tools/blender/cast/hlgame.cjs <port> <outDir> [presets: 3,0]
// -> hl_ingame_hd_<shot>.jpg (jank 3) and hl_ingame_potato_<shot>.jpg (jank 0). The rehearsal is held on one clip at a
// time and you are stood where the shot wants you; nothing here does damage.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { execSync } = require('child_process');
const [PORT = 3000, OUT = '.', PRESETS = '3,0'] = process.argv.slice(2);
// [name, clip, clip time to wait for, how far you stand, how far to her side (m), look-up pitch, only at Too HD]
const SHOTS = [['idle_7m', 'hl_idle', 1.2, 7, 0, 0.12, false], ['talk', 'hl_talk', 1.5, 2.7, 0.3, 0.42, false], ['offer', 'hl_offer', 2.0, 2.6, -0.5, 0.3, true], ['lunge', 'hl_lunge', 1.55, 3.0, 1.2, 0.36, true],
  ['reveal', 'hl_reveal', 2.5, 2.3, 0.2, 0.5, true], ['hat_off', 'hl_hat_off', 4.2, 6.5, 1.5, 0.2, true], ['from_30m', 'hl_idle', 1.0, 30, 0, 0.04, true]];
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const errs = [];
  for (const jank of PRESETS.split(',').map(Number)) {
    const tag = jank === 3 ? 'hd' : jank === 0 ? 'potato' : 'jank' + jank;
    const ctx = await b.newContext({ viewport: { width: 1280, height: 720 } });
    const pg = await ctx.newPage(); pg.on('pageerror', (e) => errs.push(tag + ': ' + e.message));
    await pg.addInitScript((j) => { localStorage.setItem('jf_giftseen_all', '1'); if (!sessionStorage.getItem('jfInit')) { localStorage.setItem('jankfire', JSON.stringify({ name: 'director', killcam: false, jank: j })); sessionStorage.setItem('jfInit', '1'); } }, jank);
    await pg.goto(`http://localhost:${PORT}/?story=1&hatlord=1`);
    const pump = (ms) => new Promise((r) => setTimeout(r, ms));
    const dismiss = () => pg.evaluate(() => { for (const b of document.querySelectorAll('button')) if (/^(LATER|NICE)$/.test(b.textContent.trim()) && b.offsetParent) b.click(); }).catch(() => {});
    await pump(1500);
    for (let i = 0; i < 150 && !(await pg.evaluate(() => !!document.getElementById('storyBtn'))); i++) await pump(100);
    await pg.evaluate(() => { localStorage.removeItem('jfStorySaves'); document.getElementById('storyBtn').click(); });
    for (let i = 0; i < 150 && !(await pg.evaluate(() => !!document.querySelector('#storyPick .st-slot .st-btn'))); i++) await pump(100);
    await pg.evaluate(() => document.querySelector('#storyPick .st-slot .st-btn').click());
    for (let i = 0; i < 800 && !(await pg.evaluate(() => !!window.JF_HLP)); i++) await pump(250);
    if (!(await pg.evaluate(() => !!window.JF_HLP))) { errs.push(tag + ': the rehearsal never started'); await ctx.close(); continue; }
    await dismiss();
    // (software GL compiles the whole map's shaders on the first frames: wait for real frames before the first shot)
    const msFrame = await pg.evaluate(() => new Promise((res) => { const t0 = performance.now(); let n = 0; const f = () => { if (++n >= 4) res(Math.round((performance.now() - t0) / n)); else requestAnimationFrame(f); }; requestAnimationFrame(f); }));
    console.log(tag, 'ms a frame once warm', msFrame);
    const info = await pg.evaluate(async () => { const P = window.JF_HLP; P.len = 1e9; const { ME } = await import('/js/player.js'); window.__ME = ME; return { blender: !!P.a.L.blender, at: P.home, you: ME.pos.map((v) => Math.round(v * 10) / 10), map: (await import('/shared/map.js')).MAP.id }; });
    console.log(tag, JSON.stringify(info));
    for (const [name, clip, t, dist, side, pitch, hdOnly] of SHOTS) {
      if (hdOnly && jank !== 3) continue;
      await pg.evaluate(async ([clip, dist, side, pitch]) => { const P = window.JF_HLP, a = P.a, ME = window.__ME, { dropTo } = await import('/js/story/actors.js');
        // (she is stood where the shot wants her from you: moving you to her is a teleport the server undoes, and at
        // software-GL frame rates it always does)
        a.path = null; a.yaw = a.home.face;
        const f = [-Math.sin(a.yaw), -Math.cos(a.yaw)], r = [Math.cos(a.yaw), -Math.sin(a.yaw)]; // (her forward, her right)
        const p = [ME.pos[0], ME.pos[1], ME.pos[2]];
        a.pos[0] = p[0] - f[0] * dist - r[0] * side; a.pos[2] = p[2] - f[1] * dist - r[1] * side; a.pos[1] = dropTo([a.pos[0], P.home[1], a.pos[2]], 3);
        window.__her = [a.pos[0], a.pos[1], a.pos[2]];
        window.__stand = { p, yaw: Math.atan2(-(a.pos[0] - p[0]), -(a.pos[2] - p[2])), pitch };
        P.label = clip.toUpperCase(); P.marks = []; window.JF_HL.play(a, clip); }, [clip, dist, side, pitch]);
      const hold = () => pg.evaluate(() => { const S = window.__stand, ME = window.__ME, A = window.JF_HLP.a; ME.pos[0] = S.p[0]; ME.pos[2] = S.p[2]; ME.vel = [0, 0, 0]; ME.yaw = S.yaw; ME.pitch = S.pitch; A.pos[0] = window.__her[0]; A.pos[1] = window.__her[1]; A.pos[2] = window.__her[2]; const c = window.JF_HLP.a.clip; return c ? [c.name, c.t] : null; });
      for (let i = 0; i < 400; i++) { const c = await hold(); if (c && c[0] === clip && c[1] >= t) break; await pump(120); }
      await dismiss(); await hold();
      const png = path.join(OUT, `hl_ingame_${tag}_${name}.png`), jpg = png.replace(/png$/, 'jpg');
      await pg.screenshot({ path: png, timeout: 600000 }); execSync(`ffmpeg -loglevel error -y -i "${png}" -q:v 3 "${jpg}"`); fs.unlinkSync(png); console.log('wrote', jpg);
    }
    await ctx.close();
  }
  await b.close();
  console.log(errs.length ? 'ERRORS:\n' + [...new Set(errs)].join('\n') : 'no errors');
})();
