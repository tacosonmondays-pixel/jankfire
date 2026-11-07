// records MR. OVERTIME's fight-1 cutscenes on the Gut border landing, in capture mode: he's put in place in the state
// that scene starts from (the phase scenes mid-fight, the retreat after the Heart Rip), then the scene plays.
// usage: node tools/otscenes.cjs [--port 3000] [--out docs/story/scenes] [--fps 6] [--w 640 --h 360] [ids...]
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs'), path = require('path'), os = require('os');
const A = process.argv.slice(2), opt = (k, d) => { const i = A.indexOf('--' + k); return i >= 0 ? A[i + 1] : d; };
const PORT = opt('port', 3000), OUT = opt('out', 'docs/story/scenes'), FPS = Number(opt('fps', 6)), W = Number(opt('w', 640)), H = Number(opt('h', 360));
const IDS = A.filter((x, i) => !x.startsWith('--') && !(i > 0 && A[i - 1].startsWith('--')));
// the state each scene starts from
const SETUP = {
  ot1_coffee: { dmg: ['plate_off'], clip: 'ot_stalk' },
  ot1_punching_in: { dmg: ['plate_off', 'cracked'], clip: 'ot_coffee' },
  ot1_retreat: { dmg: ['plate_off', 'ripped'], clip: 'ot_kneel' },
};
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: W, height: H } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.addInitScript(() => { if (!sessionStorage.getItem('jfInit')) { localStorage.setItem('jankfire', JSON.stringify({ name: 'director', jank: 3 })); sessionStorage.setItem('jfInit', '1'); } });
  await pg.goto(`http://localhost:${PORT}/?story=1`);
  const pump = (ms) => new Promise((r) => setTimeout(r, ms));
  await pump(1500);
  for (let i = 0; i < 100 && !(await pg.evaluate(() => !!document.getElementById('storyBtn'))); i++) await pump(100);
  await pg.evaluate(() => { localStorage.removeItem('jfStorySaves'); document.getElementById('storyBtn').click(); });
  for (let i = 0; i < 100 && !(await pg.evaluate(() => !!document.querySelector('#storyPick .st-slot .st-btn'))); i++) await pump(100);
  await pg.evaluate(() => document.querySelector('#storyPick .st-slot .st-btn').click());
  for (let i = 0; i < 300 && !(await pg.evaluate(() => !!(window.JF_STORY && window.JF_STORY.on))); i++) await pump(100);
  await pump(1500);
  const step = async () => { await pg.evaluate((dt) => { window.JF_STORY.capStep = dt; }, 1 / FPS); await pg.waitForFunction(() => window.JF_STORY.capStep === 0, null, { polling: 'raf', timeout: 180000 }); await pg.evaluate(() => new Promise((r) => requestAnimationFrame(() => r()))); };
  for (const ID of IDS) {
    const set = SETUP[ID] || {};
    await pg.evaluate(async (set) => {
      const { ME } = await import('/js/player.js'); const A = await import('/js/story/actors.js'); const { OT } = await import('/js/story/overtime.js');
      const ST = window.JF_STORY, land = ST.where('gut:stairs_top');
      ME.pos = [land[0], land[1], land[2] + 10]; ME.vel = [0, 0, 0]; ME.yaw = 0; ME.pitch = 0.1;
      const at = [land[0], land[1], land[2] + 1]; at[1] = A.dropTo([at[0], land[1] + 2, at[2]], 4);
      const a = A.spawnActor('overtime', { look: 'overtime', voice: { kind: 'dialtone', pitch: 0.7, rate: 0.9 }, name: 'MR. OVERTIME' }, at, Math.PI);
      a.home.face = Math.PI; OT.variant(a, 1); for (const d of set.dmg || []) OT.dmg(a, d);
      if (set.clip) A.play(a, set.clip, { hold: true });
      ST.capture = true;
    }, set);
    for (let i = 0; i < FPS; i++) await step(); // (settle into the pose)
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ots-'));
    await pg.evaluate((id) => window.JF_STORY.scene.playScene(id), ID);
    let n = 0;
    for (; n < FPS * 40; n++) {
      await step(); await pg.screenshot({ path: path.join(tmp, `f${String(n).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 88, timeout: 180000 });
      if (!(await pg.evaluate(() => window.JF_STORY.scene.playing()))) break;
    }
    for (let k = 0; k < FPS; k++, n++) { await step(); await pg.screenshot({ path: path.join(tmp, `f${String(n).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 88, timeout: 180000 }); }
    const mp4 = path.join(OUT, `${ID}.mp4`), sheet = path.join(OUT, `${ID}_sheet.jpg`);
    fs.mkdirSync(OUT, { recursive: true });
    execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-framerate', String(FPS), '-i', path.join(tmp, 'f%05d.jpg'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '26', '-preset', 'veryfast', '-vf', 'scale=640:-2', mp4]);
    const every = Math.max(1, Math.floor(n / 9));
    execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-framerate', String(FPS), '-i', path.join(tmp, 'f%05d.jpg'), '-vf', `select='not(mod(n\\,${every}))',scale=400:-1,tile=3x3`, '-frames:v', '1', '-q:v', '4', sheet]);
    fs.rmSync(tmp, { recursive: true, force: true });
    console.log(`${ID}: ${n} frames -> ${mp4}`);
  }
  console.log(errs.length ? 'errors:\n' + errs.join('\n') : 'no errors'); await b.close();
})();
