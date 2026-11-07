// records MR. OVERTIME's rehearsal (?otpreview=1: his whole move set on a loop, no damage) on the Gut border landing.
// The headless renderer is slow, so it records the page in real time and then retimes the video to story time (the
// preview counts its own seconds): smooth enough, and every move plays at its true speed. An mp4 + a contact sheet.
// usage: node tools/otpreview.cjs [--port 3000] [--out docs/story/scenes] [--secs 46] [--w 960 --h 540] [--name ot_preview]
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs'), path = require('path'), os = require('os');
const A = process.argv.slice(2), opt = (k, d) => { const i = A.indexOf('--' + k); return i >= 0 ? A[i + 1] : d; };
const PORT = opt('port', 3000), OUT = opt('out', 'docs/story/scenes'), SECS = Number(opt('secs', 46)), NAME = opt('name', 'ot_preview');
const W = Number(opt('w', 960)), H = Number(opt('h', 540)), TILE = opt('tile', '4x4');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const vdir = fs.mkdtempSync(path.join(os.tmpdir(), 'otv-'));
  const ctx = await b.newContext({ viewport: { width: W, height: H }, recordVideo: { dir: vdir, size: { width: W, height: H } } });
  const pg = await ctx.newPage(); const T0 = Date.now();
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.addInitScript(() => { if (!sessionStorage.getItem('jfInit')) { localStorage.setItem('jankfire', JSON.stringify({ name: 'director', jank: 3 })); sessionStorage.setItem('jfInit', '1'); } });
  await pg.goto(`http://localhost:${PORT}/?story=1&otpreview=1`);
  const pump = (ms) => new Promise((r) => setTimeout(r, ms));
  await pump(1500);
  for (let i = 0; i < 100 && !(await pg.evaluate(() => !!document.getElementById('storyBtn'))); i++) await pump(100);
  await pg.evaluate(() => { localStorage.removeItem('jfStorySaves'); document.getElementById('storyBtn').click(); });
  for (let i = 0; i < 100 && !(await pg.evaluate(() => !!document.querySelector('#storyPick .st-slot .st-btn'))); i++) await pump(100);
  await pg.evaluate(() => document.querySelector('#storyPick .st-slot .st-btn').click());
  for (let i = 0; i < 600 && !(await pg.evaluate(() => !!window.JF_OTP)); i++) await pump(250);
  // story time vs video time: from the preview's first counted second to SECS later
  const g0 = await pg.evaluate(() => window.JF_OTP.total), r0 = (Date.now() - T0) / 1000;
  let g1 = g0;
  for (;;) { await pump(2000); g1 = await pg.evaluate(() => window.JF_OTP.total); if (g1 - g0 >= SECS) break; }
  const r1 = (Date.now() - T0) / 1000;
  await ctx.close(); await b.close();
  const raw = path.join(vdir, fs.readdirSync(vdir).find((f) => f.endsWith('.webm')));
  const k = (g1 - g0) / (r1 - r0); // story seconds per real second (< 1: the page ran slow)
  fs.mkdirSync(OUT, { recursive: true });
  const mp4 = path.join(OUT, `${NAME}.mp4`), sheet = path.join(OUT, `${NAME}_sheet.jpg`);
  execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-ss', String(r0), '-to', String(r1), '-i', raw, '-vf', `setpts=(PTS-STARTPTS)*${k.toFixed(4)},fps=24,scale=${W}:-2`, '-an', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '26', '-preset', 'veryfast', mp4]);
  const [tc, tr] = TILE.split('x').map(Number);
  execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-i', mp4, '-vf', `fps=${(tc * tr / (g1 - g0)).toFixed(4)},scale=400:-1,tile=${TILE}`, '-frames:v', '1', '-q:v', '4', sheet]);
  fs.rmSync(vdir, { recursive: true, force: true });
  console.log(`${NAME}: ${(g1 - g0).toFixed(1)} story s in ${(r1 - r0).toFixed(0)} real s (x${(1 / k).toFixed(1)} slow) -> ${mp4}, ${sheet}${errs.length ? '\nerrors:\n' + errs.join('\n') : '\nno errors'}`);
})();
