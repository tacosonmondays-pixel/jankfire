// records MR. OVERTIME's fight-1 cutscenes in the Gut border gate arena: he's put on the boss spot the way the fight
// does it (a referee hit, bossfight.js), in the state that scene starts from (the phase scenes mid-fight, the retreat
// after the Heart Rip), then the scene plays in capture mode (boot.js: one fixed story step per rendered frame).
// The headless renderer takes seconds per frame, so the page is filmed (recordVideo) with a 16-bit frame counter in a
// strip under the picture; ffmpeg then keeps one video frame per story step and crops the strip off. An mp4 + a sheet each.
// usage: node tools/otscenes.cjs [--port 3000] [--out docs/story/scenes] [--fps 12] [--w 960 --h 540] [ids...]
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs'), path = require('path'), os = require('os');
const A = process.argv.slice(2), opt = (k, d) => { const i = A.indexOf('--' + k); return i >= 0 ? A[i + 1] : d; };
const PORT = opt('port', 3000), OUT = opt('out', 'docs/story/scenes'), FPS = Number(opt('fps', 12)), W = Number(opt('w', 960)), H = Number(opt('h', 540));
const IDS = A.filter((x, i) => !x.startsWith('--') && !(i > 0 && A[i - 1].startsWith('--')));
if (!IDS.length) IDS.push('ot1_coffee', 'ot1_punching_in', 'ot1_retreat');
const BAR = 4, CELL = 4; // (the counter strip: 16 cells, CELL px wide, BAR px tall, under the picture)
// the state each scene starts from, and the pose the boss hooks leave him in afterwards (bossfight.js HOOKS)
const SETUP = {
  ot1_coffee: { dmg: ['plate_off'], clip: 'ot_stalk', after: { clip: 'ot_coffee', dmg: 'cracked' } },
  ot1_punching_in: { dmg: ['plate_off', 'cracked'], clip: 'ot_coffee', after: { clip: 'ot_stalk', dmg: 'sparking' } },
  ot1_retreat: { dmg: ['plate_off', 'ripped'], clip: 'ot_kneel' },
};
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const vdir = fs.mkdtempSync(path.join(os.tmpdir(), 'ots-'));
  const ctx = await b.newContext({ viewport: { width: W, height: H + BAR }, recordVideo: { dir: vdir, size: { width: W, height: H + BAR } } });
  const pg = await ctx.newPage();
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.addInitScript(() => { if (!sessionStorage.getItem('jfInit')) { localStorage.setItem('jankfire', JSON.stringify({ name: 'director', jank: 3 })); sessionStorage.setItem('jfInit', '1'); } });
  await pg.goto(`http://localhost:${PORT}/?story=1`);
  const pump = (ms) => new Promise((r) => setTimeout(r, ms));
  const dismiss = () => pg.evaluate(() => { for (const b of document.querySelectorAll('button')) if (/^(LATER|NICE)$/.test(b.textContent.trim()) && b.offsetParent) b.click(); }).catch(() => {}); // (the shell's gift memo)
  await pump(1500);
  for (let i = 0; i < 100 && !(await pg.evaluate(() => !!document.getElementById('storyBtn'))); i++) await pump(100);
  await pg.evaluate(() => { localStorage.removeItem('jfStorySaves'); document.getElementById('storyBtn').click(); });
  for (let i = 0; i < 100 && !(await pg.evaluate(() => !!document.querySelector('#storyPick .st-slot .st-btn'))); i++) await pump(100);
  await pg.evaluate(() => document.querySelector('#storyPick .st-slot .st-btn').click());
  for (let i = 0; i < 300 && !(await pg.evaluate(() => !!(window.JF_STORY && window.JF_STORY.on))); i++) await pump(100);
  for (let i = 0; i < 600 && !(await pg.evaluate(() => !!(window.JF_STORY.scene && window.JF_STORY.boss))); i++) await pump(250); // (the cast models load first)
  await dismiss();
  // every frame: you're held 9 m south of the boss spot (falling through a block that hasn't loaded sends you home);
  // while filming, the story gets one step and the strip shows the step's number
  await pg.evaluate(async ([fps, bar, cell]) => {
    const { ME } = await import('/js/player.js'); const ST = window.JF_STORY, boss = ST.where('arena.boss');
    const s = document.createElement('div'); s.style.cssText = `position:fixed;left:0;bottom:0;width:100%;height:${bar}px;background:#000;z-index:2147483647;pointer-events:none`;
    const cells = []; for (let i = 0; i < 16; i++) { const c = document.createElement('div'); c.style.cssText = `position:absolute;left:${i * cell}px;top:0;width:${cell}px;height:${bar}px;background:#000`; s.append(c); cells.push(c); }
    document.body.append(s);
    const C = window.JF_CAP = { n: 0, on: false };
    const f = () => {
      ME.pos = [boss[0] + 2, boss[1], boss[2] + 9]; ME.vel = [0, 0, 0]; ME.yaw = Math.atan2(2, 9); ME.pitch = 0.14;
      if (C.on) { C.n++; ST.capStep = 1 / fps; for (let i = 0; i < 16; i++) cells[i].style.background = (C.n >> i) & 1 ? '#fff' : '#000'; }
      requestAnimationFrame(f);
    };
    requestAnimationFrame(f);
  }, [FPS, BAR, CELL]);
  for (let i = 0; i < 10; i++) { await pump(1000); await dismiss(); await pg.evaluate(() => { const ST = window.JF_STORY; while (ST.scene.playing()) ST.scene.skipScene(); }); } // (the block loads in; the opening scenes are skipped)
  const capN = () => pg.evaluate(() => window.JF_CAP.n);
  const waitN = async (n) => { while ((await capN()) < n) await pump(1000); };
  const takes = [];
  for (const ID of IDS) {
    const set = SETUP[ID] || {};
    const n0 = await pg.evaluate(async (set) => {
      const A = await import('/js/story/actors.js'); const { OT } = await import('/js/story/overtime.js');
      const ST = window.JF_STORY;
      A.despawnActor('overtime'); ST.boss.on = null; // (a fresh one for each take)
      ST.boss.combat({ type: 'hit', boss: 'overtime_1', hp: 100, max: 100 });
      const a = A.actors.get('overtime'); for (const d of set.dmg || []) OT.dmg(a, d);
      if (set.clip) { a.clip = null; A.play(a, set.clip, { hold: true }); }
      ST.capture = true; window.JF_CAP.on = true; return window.JF_CAP.n;
    }, set);
    await waitN(n0 + FPS + 2); // (he settles into the pose)
    const n1 = await pg.evaluate(async ([id, after]) => {
      const A = await import('/js/story/actors.js'); const { OT } = await import('/js/story/overtime.js');
      window.JF_STORY.scene.playScene(id, { done: () => { const a = A.actors.get('overtime'); if (!a || !after) return; OT.dmg(a, after.dmg); a.clip = null; A.play(a, after.clip, { hold: true }); } });
      return window.JF_CAP.n;
    }, [ID, set.after || null]);
    while (await pg.evaluate(() => window.JF_STORY.scene.playing())) { await pump(1000); await dismiss(); }
    const n2 = await capN(); await waitN(n2 + FPS); // (a second of the blend back to the fight)
    const n3 = await pg.evaluate(() => { window.JF_CAP.on = false; window.JF_STORY.capture = false; return window.JF_CAP.n; });
    takes.push({ ID, from: n1 + 2, to: n3 - 1 }); console.log(`${ID}: steps ${n1 + 2}..${n3 - 1}`);
    await pump(4000);
  }
  await ctx.close(); await b.close();
  // which video frame shows which step: read the strip, keep the last video frame of each step
  const raw = path.join(vdir, fs.readdirSync(vdir).find((f) => f.endsWith('.webm')));
  const bits = execFileSync('ffmpeg', ['-loglevel', 'error', '-i', raw, '-vf', `crop=${16 * CELL}:${BAR - 2}:0:${H + 1},scale=16:1:flags=area,format=gray`, '-fps_mode', 'passthrough', '-f', 'rawvideo', '-'], { maxBuffer: 1 << 28 });
  const last = new Map();
  for (let f = 0; f * 16 < bits.length; f++) { let n = 0; for (let i = 0; i < 16; i++) if (bits[f * 16 + i] > 127) n |= 1 << i; last.set(n, f); }
  fs.mkdirSync(OUT, { recursive: true });
  for (const { ID, from, to } of takes) {
    const fr = []; for (let n = from; n <= to; n++) if (last.has(n)) fr.push(last.get(n));
    const sel = fr.map((f) => `eq(n\\,${f})`).join('+');
    const mp4 = path.join(OUT, `${ID}.mp4`), sheet = path.join(OUT, `${ID}_sheet.jpg`);
    execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-i', raw, '-vf', `select='${sel}',setpts=N/(${FPS}*TB),crop=${W}:${H}:0:0`, '-r', String(FPS), '-an', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '24', '-preset', 'veryfast', mp4]);
    execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-i', mp4, '-vf', `fps=${(12 * FPS / fr.length).toFixed(4)},scale=480:-1,tile=4x3`, '-frames:v', '1', '-q:v', '4', sheet]);
    console.log(`${ID}: ${fr.length} of ${to - from + 1} steps (${(fr.length / FPS).toFixed(1)} s) -> ${mp4}, ${sheet}`);
  }
  if (opt('keep', '')) console.log('raw video: ' + raw); else fs.rmSync(vdir, { recursive: true, force: true });
  console.log(errs.length ? 'errors:\n' + errs.join('\n') : 'no errors');
})();
