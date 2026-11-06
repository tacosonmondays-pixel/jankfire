// OVERDUE scene recorder (TECH_PLAN §6): plays one story scene at Too HD and writes an mp4 + a frame contact sheet.
// The story runs in capture mode (boot.js): each recorded frame is exactly 1/fps of story time however slow the GPU is.
// usage: node tools/scene.cjs <sceneId> [--port 3000] [--out docs/story/scenes] [--fps 24] [--w 1280 --h 720] [--pre <js>]
// needs a running server (npm start) and ffmpeg. Starts a fresh story run (STORY, slot 1, NEW GAME) on the test lot.
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs'), path = require('path'), os = require('os');
const A = process.argv.slice(2), opt = (k, d) => { const i = A.indexOf('--' + k); return i >= 0 ? A[i + 1] : d; };
const ID = A[0]; if (!ID || ID.startsWith('--')) { console.log('usage: node tools/scene.cjs <sceneId> [--port 3000] [--out dir] [--fps 24]'); process.exit(1); }
const PORT = opt('port', 3000), OUT = opt('out', 'docs/story/scenes'), FPS = Number(opt('fps', 12)), W = Number(opt('w', 960)), H = Number(opt('h', 540)), PRE = opt('pre', '');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: W, height: H } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.addInitScript(() => { if (!sessionStorage.getItem('jfInit')) { localStorage.setItem('jankfire', JSON.stringify({ name: 'director', jank: 3 })); sessionStorage.setItem('jfInit', '1'); } });
  await pg.goto(`http://localhost:${PORT}/?story=1&fresh=1&lab=1`);
  const pump = (ms) => new Promise((r) => setTimeout(r, ms));
  const step = async () => { await pg.evaluate((dt) => { window.JF_STORY.capStep = dt; }, 1 / FPS); await pg.waitForFunction(() => window.JF_STORY.capStep === 0, null, { polling: 'raf' }); await pg.evaluate(() => new Promise((r) => requestAnimationFrame(() => r()))); };
  await pump(1500);
  for (let i = 0; i < 100 && !(await pg.evaluate(() => !!document.getElementById('storyBtn'))); i++) await pump(100);
  await pg.evaluate(() => { localStorage.removeItem('jfStorySaves'); document.getElementById('storyBtn').click(); }); // STORY -> slot 1 -> NEW GAME
  for (let i = 0; i < 100 && !(await pg.evaluate(() => !!document.querySelector('#storyPick .st-slot .st-btn'))); i++) await pump(100);
  await pg.evaluate(() => document.querySelector('#storyPick .st-slot .st-btn').click());
  for (let i = 0; i < 300 && !(await pg.evaluate(() => !!(window.JF_STORY && window.JF_STORY.on))); i++) await pump(100);
  await pg.evaluate(() => { window.JF_STORY.capture = true; });
  await pg.evaluate(async (pre) => { const { ME } = await import('/js/player.js'); ME.pitch = -0.05; const S = window.JF_STORY.S;
    S.run(['log:lumps|lumps asked you for soup. the red kind.', 'log:gordo|you paid wee gordo to call off the interns. he remembers.', 'log:auntie|auntie wrote SOUP: 1 in crayon. underlined twice.']);
    if (pre) (0, eval)(pre); }, PRE);
  await pump(1500);
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'scene-'));
  await pg.evaluate((id) => window.JF_STORY.scene.playScene(id), ID);
  let n = 0;
  for (; n < FPS * 150; n++) {
    await step();
    // a talk scene answers for itself (first answer, next line every second)
    if (n % FPS === FPS - 1) await pg.evaluate(() => { const t = document.getElementById('stTalk'); if (t && !t.classList.contains('hidden')) dispatchEvent(new KeyboardEvent('keydown', { code: document.querySelector('#stTalk .st-opt') ? 'Digit1' : 'KeyF', key: 'f', bubbles: true })); });
    await pg.screenshot({ path: path.join(tmp, `f${String(n).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 88 });
    if (!(await pg.evaluate(() => window.JF_STORY.scene.playing()))) break;
  }
  for (let k = 0; k < FPS * 1.2; k++, n++) { await step(); await pg.screenshot({ path: path.join(tmp, `f${String(n).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 88 }); } // the blend back to gameplay
  await b.close();
  fs.mkdirSync(OUT, { recursive: true });
  const mp4 = path.join(OUT, `${ID}.mp4`), sheet = path.join(OUT, `${ID}_sheet.jpg`);
  execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-framerate', String(FPS), '-i', path.join(tmp, 'f%05d.jpg'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '26', '-preset', 'veryfast', '-vf', 'scale=960:-2', mp4]);
  const every = Math.max(1, Math.floor(n / 12));
  execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-framerate', String(FPS), '-i', path.join(tmp, 'f%05d.jpg'), '-vf', `select='not(mod(n\\,${every}))',scale=480:-1,tile=3x4`, '-frames:v', '1', '-q:v', '4', sheet]);
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log(`${ID}: ${n} frames (${(n / FPS).toFixed(1)} s) -> ${mp4}, ${sheet}${errs.length ? '\nerrors:\n' + errs.join('\n') : ''}`);
})();
