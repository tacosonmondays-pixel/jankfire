// THE HEADLINER's rehearsal in the real game, recorded (Playwright recordVideo, then ffmpeg):
//   node tools/blender/cast/jlrec.cjs <port> <out.mp4> [jank 3] [seconds 39]
// story mode, ?jesterlord=1: you stand still and watch him run the whole set once from the top; the camera tips up
// for the web. nothing here does damage
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { execSync } = require('child_process');
const [PORT = 3000, OUT = 'jl_rehearsal.mp4', JANK = '3', SECS = '39'] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const raw = path.join(path.dirname(path.resolve(OUT)), 'jlrec_raw'); fs.mkdirSync(raw, { recursive: true });
  const ctx = await b.newContext({ viewport: { width: 960, height: 540 }, recordVideo: { dir: raw, size: { width: 960, height: 540 } } });
  const pg = await ctx.newPage(); const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  const t0 = Date.now();
  await pg.addInitScript((j) => { localStorage.setItem('jf_giftseen_all', '1'); if (!sessionStorage.getItem('jfInit')) { localStorage.setItem('jankfire', JSON.stringify({ name: 'director', killcam: false, jank: j })); sessionStorage.setItem('jfInit', '1'); } }, Number(JANK));
  await pg.goto(`http://localhost:${PORT}/?story=1&jesterlord=1`);
  const pump = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 150 && !(await pg.evaluate(() => !!document.getElementById('storyBtn'))); i++) await pump(100);
  await pg.evaluate(async () => (await import('/js/story/looks.js')).loadCast(['jester_lord'], 180000));
  await pg.evaluate(() => { localStorage.removeItem('jfStorySaves'); document.getElementById('storyBtn').click(); });
  for (let i = 0; i < 150 && !(await pg.evaluate(() => !!document.querySelector('#storyPick .st-slot .st-btn'))); i++) await pump(100);
  await pg.evaluate(() => document.querySelector('#storyPick .st-slot .st-btn').click());
  for (let i = 0; i < 800 && !(await pg.evaluate(() => !!window.JF_JLP)); i++) await pump(250);
  await pg.evaluate(() => { for (const b of document.querySelectorAll('button')) if (/^(LATER|NICE)$/.test(b.textContent.trim()) && b.offsetParent) b.click(); });
  // from the top of the set; you hold still and look at him (up at the web when he is in it)
  await pg.evaluate(async () => {
    const { ME } = await import('/js/player.js'); const sc = await import('/js/story/scene.js'); const P = window.JF_JLP, p = ME.pos.slice();
    P.a.pos[0] = P.home[0]; P.a.pos[2] = P.home[2]; P.i = -1; P.t = 0;
    window.__hold = setInterval(() => { if (sc.playing()) sc.skipScene(); ME.pos[0] = p[0]; ME.pos[2] = p[2]; ME.vel = [0, 0, 0];
      const a = P.a, up = a.clip && /jl_(hang|drop)/.test(a.clip.name) ? 0.5 : 0.24; ME.yaw = Math.atan2(-(a.pos[0] - p[0]), -(a.pos[2] - p[2])); ME.pitch += (up - ME.pitch) * 0.08; }, 16);
  });
  const start = (Date.now() - t0) / 1000;
  await pump(Number(SECS) * 1000);
  const v = pg.video(); await ctx.close(); await b.close();
  const webm = await v.path();
  execSync(`ffmpeg -loglevel error -y -ss ${start.toFixed(2)} -i "${webm}" -t ${SECS} -c:v libx264 -pix_fmt yuv420p -crf 24 -preset veryfast -movflags +faststart "${OUT}"`);
  fs.rmSync(raw, { recursive: true, force: true });
  console.log('wrote', OUT, fs.statSync(OUT).size >> 10, 'KB', 'started at', start.toFixed(1), 's', errs.length ? 'ERRORS: ' + errs.join(' | ') : 'no errors');
})();
