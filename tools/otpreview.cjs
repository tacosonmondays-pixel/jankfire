// records MR. OVERTIME's rehearsal (?otpreview=1: his whole move set on a loop, no damage) on the Gut border landing, in
// capture mode (each frame = 1/fps of story time): an mp4 + a contact sheet.
// usage: node tools/otpreview.cjs [--port 3000] [--out docs/story/scenes] [--fps 12] [--secs 44] [--name ot_preview]
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs'), path = require('path'), os = require('os');
const A = process.argv.slice(2), opt = (k, d) => { const i = A.indexOf('--' + k); return i >= 0 ? A[i + 1] : d; };
const PORT = opt('port', 3000), OUT = opt('out', 'docs/story/scenes'), FPS = Number(opt('fps', 12)), SECS = Number(opt('secs', 44)), NAME = opt('name', 'ot_preview');
const W = Number(opt('w', 960)), H = Number(opt('h', 540)), TILE = opt('tile', '4x4');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: W, height: H } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.addInitScript(() => { if (!sessionStorage.getItem('jfInit')) { localStorage.setItem('jankfire', JSON.stringify({ name: 'director', jank: 3 })); sessionStorage.setItem('jfInit', '1'); } });
  await pg.goto(`http://localhost:${PORT}/?story=1&otpreview=1`);
  const pump = (ms) => new Promise((r) => setTimeout(r, ms));
  await pump(1500);
  for (let i = 0; i < 100 && !(await pg.evaluate(() => !!document.getElementById('storyBtn'))); i++) await pump(100);
  await pg.evaluate(() => { localStorage.removeItem('jfStorySaves'); document.getElementById('storyBtn').click(); });
  for (let i = 0; i < 100 && !(await pg.evaluate(() => !!document.querySelector('#storyPick .st-slot .st-btn'))); i++) await pump(100);
  await pg.evaluate(() => document.querySelector('#storyPick .st-slot .st-btn').click());
  for (let i = 0; i < 300 && !(await pg.evaluate(() => !!(window.JF_STORY && window.JF_STORY.on))); i++) await pump(100);
  await pg.evaluate(async () => { const { ME } = await import('/js/player.js'); window.JF_STORY.capture = true; });
  const step = async () => { await pg.evaluate((dt) => { window.JF_STORY.capStep = dt; }, 1 / FPS); await pg.waitForFunction(() => window.JF_STORY.capStep === 0, null, { polling: 'raf' }); await pg.evaluate(() => new Promise((r) => requestAnimationFrame(() => r()))); };
  for (let i = 0; i < 6; i++) await step(); // (he spawns)
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'otp-'));
  const N = Math.round(SECS * FPS);
  for (let n = 0; n < N; n++) { await step(); await pg.screenshot({ path: path.join(tmp, `f${String(n).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 88 }); }
  await b.close();
  fs.mkdirSync(OUT, { recursive: true });
  const mp4 = path.join(OUT, `${NAME}.mp4`), sheet = path.join(OUT, `${NAME}_sheet.jpg`);
  execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-framerate', String(FPS), '-i', path.join(tmp, 'f%05d.jpg'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '26', '-preset', 'veryfast', '-vf', 'scale=960:-2', mp4]);
  const [tc, tr] = TILE.split('x').map(Number), every = Math.max(1, Math.floor(N / (tc * tr)));
  execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-framerate', String(FPS), '-i', path.join(tmp, 'f%05d.jpg'), '-vf', `select='not(mod(n\\,${every}))',scale=400:-1,tile=${TILE}`, '-frames:v', '1', '-q:v', '4', sheet]);
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log(`${NAME}: ${N} frames -> ${mp4}, ${sheet}${errs.length ? '\nerrors:\n' + errs.join('\n') : '\nno errors'}`);
})();
