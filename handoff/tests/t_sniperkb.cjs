require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs');
const { chromium } = require('playwright');
{ const L = chromium.launch.bind(chromium); chromium.launch = async (...a) => { const b = await L(...a), seen = () => { try { localStorage.setItem('jf_giftseen_all', '1'); } catch (e) { /* no storage */ } }; const np = b.newPage.bind(b), nc = b.newContext.bind(b); b.newPage = async (...o) => { const p = await np(...o); await p.addInitScript(seen); return p; }; b.newContext = async (...o) => { const c = await nc(...o); await c.addInitScript(seen); return c; }; return b; }; } // the guest gift popup (multiopen.js) would cover the menu: every page starts with it already seen
const [port] = process.argv.slice(2);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 960, height: 600 } });
  const errs = []; pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message));
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ name: 'kbtest', killcam: false, loadout: { primary: 'sniper', secondary: 'cig', melee: 'knife', item: 'frag' } })));
  await pg.goto(`http://localhost:${port}/`); await sleep(500);
  await pg.click('#scr-main [data-mode="training"]'); await sleep(2000);
  const r = await pg.evaluate(async () => {
    const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js'); const w = await import('/js/weapons.js');
    const t = [...G.remotes.values()].filter((r) => r.alive && /Dummy/.test(r.name || '')).sort((a, b) => Math.hypot(a.pos[0] - ME.pos[0], a.pos[2] - ME.pos[2]) - Math.hypot(b.pos[0] - ME.pos[0], b.pos[2] - ME.pos[2]))[0];
    const p = [t.pos[0], t.pos[1], t.pos[2] + 12], start = t.pos.slice();
    const hold = setInterval(() => { ME.pos = p.slice(); ME.vel = [0, 0, 0]; const e = [p[0], p[1] + 1.6, p[2]], to = [start[0], start[1] + 0.9, start[2]]; const d = to.map((v, i) => v - e[i]), L = Math.hypot(...d); ME.yaw = Math.atan2(-d[0], -d[2]); ME.pitch = Math.asin(d[1] / L); }, 5);
    await new Promise((r) => setTimeout(r, 900));
    w.fireDown(); w.fireUp();
    let maxMove = 0; for (let i = 0; i < 20; i++) { await new Promise((r) => setTimeout(r, 50)); maxMove = Math.max(maxMove, Math.hypot(t.pos[0] - start[0], t.pos[1] - start[1], t.pos[2] - start[2])); }
    clearInterval(hold);
    return { dummy: t.name, moved: +maxMove.toFixed(1), alive: t.alive };
  });
  console.log(JSON.stringify(r)); console.log(errs.join('\n') || 'no errors'); await b.close();
})();
