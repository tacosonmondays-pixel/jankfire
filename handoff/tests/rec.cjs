require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs');
// records one short clip per weapon in Training (graphics: Too HD). usage: node rec.cjs <port> <outDir>
const { chromium } = require('playwright');
const fs = require('fs');
const [port, out] = process.argv.slice(2);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const base = { primary: 'ar', secondary: 'revolver', melee: 'knife', item: 'frag' };
const ALL = [
  { n: 'sniper_launch', lo: { primary: 'sniper' }, key: 'Digit1', d: 14, clicks: 2, gap: 2600, post: 3000 },
  { n: 'marble_shotgun', lo: { secondary: 'marbles' }, key: 'Digit2', d: 3, clicks: 2, gap: 2800, post: 2500 },
  { n: 'redline', lo: { primary: 'redline' }, key: 'Digit1', d: 8, hold: 2600, post: 1200 },
  { n: 'shredder', lo: { primary: 'shredder' }, key: 'Digit1', d: 6, hold: 3800, post: 1800 },
  { n: 'blood_cross', lo: { secondary: 'bloodcross' }, key: 'Digit2', d: 6, clicks: 2, gap: 2600, post: 3000 },
  { n: 'revolver_fan', lo: { secondary: 'revolver' }, key: 'Digit2', d: 10, hold: 2200, post: 2000 },
  { n: 'katana_parry', lo: { melee: 'katana' }, key: 'Digit3', d: 1.9, clicks: 3, gap: 650, parry: 2, post: 1200 },
  { n: 'scales_of_justice', lo: { melee: 'scales' }, key: 'Digit3', d: 1.9, clicks: 3, gap: 950, post: 1800 },
]; const SCENES = ALL.filter((s) => !process.env.SCENE || s.n === process.env.SCENE);
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const log = [];
  for (const s of SCENES) {
    const t0 = Date.now();
    const ctx = await b.newContext({ viewport: { width: 960, height: 540 }, recordVideo: { dir: out + '/raw', size: { width: 960, height: 540 } } });
    const pg = await ctx.newPage();
    const errs = [];
    pg.on('pageerror', (e) => errs.push(e.message));
    const lo = { ...base, ...s.lo };
    await pg.addInitScript((lo) => localStorage.setItem('jankfire', JSON.stringify({ name: 'JANKFIRE', killcam: false, jank: 3, loadout: lo })), lo);
    try {
      await pg.goto(`http://localhost:${port}/`); await sleep(700);
      await pg.click('#scr-main [data-mode="training"]'); await sleep(2200);
      await pg.evaluate(async (d) => {
        const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js');
        const t = [...G.remotes.values()].filter((r) => r.alive && /Dummy/.test(r.name || '')).sort((a, b) => Math.hypot(a.pos[0] - ME.pos[0], a.pos[2] - ME.pos[2]) - Math.hypot(b.pos[0] - ME.pos[0], b.pos[2] - ME.pos[2]))[0];
        if (!t) return;
        const tp = t.pos.slice(), p = [tp[0] + d * 0.35, tp[1], tp[2] + d * 0.94];
        window.__hold = setInterval(() => {
          ME.pos = p.slice(); ME.vel = [0, 0, 0];
          const e = [p[0], p[1] + 1.6, p[2]], to = [tp[0], tp[1] + 1.1, tp[2]];
          const v = to.map((x, i) => x - e[i]), L = Math.hypot(...v);
          ME.yaw = Math.atan2(-v[0], -v[2]); ME.pitch = Math.asin(v[1] / L);
        }, 5);
      }, s.d);
      await pg.keyboard.press(s.key); await sleep(1300);
      const start = (Date.now() - t0) / 1000;
      await pg.evaluate(async (s) => {
        const w = await import('/js/weapons.js'); const wait = (ms) => new Promise((r) => setTimeout(r, ms));
        if (s.hold) { w.fireDown(); await wait(s.hold); w.fireUp(); }
        for (let i = 0; i < (s.clicks || 0); i++) { w.fireDown(); await wait(60); w.fireUp(); await wait(s.gap || 800); }
        for (let i = 0; i < (s.parry || 0); i++) { if (w.parry) w.parry(); await wait(1500); }
      }, s);
      await sleep(s.post);
      log.push({ n: s.n, start: Math.max(0, start - 0.4), errs });
    } catch (e) { log.push({ n: s.n, fail: e.message.slice(0, 200) }); }
    const v = pg.video();
    await ctx.close();
    if (v) { try { fs.renameSync(await v.path(), `${out}/raw/${s.n}.webm`); } catch {} }
    console.log(JSON.stringify(log[log.length - 1]));
  }
  fs.writeFileSync(out + '/log.json', JSON.stringify(log));
  await b.close();
})();
