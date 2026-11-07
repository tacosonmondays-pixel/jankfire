require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs'); // at most 2 headless browsers machine-wide
// Marble Shotgun damage by distance on a training dummy + screenshots; Redline fire rate at different HP.
// usage: node t_guns.cjs <port> <outDir>
const { chromium } = require('playwright');
{ const L = chromium.launch.bind(chromium); chromium.launch = async (...a) => { const b = await L(...a), seen = () => { try { localStorage.setItem('jf_giftseen_all', '1'); } catch (e) { /* no storage */ } }; const np = b.newPage.bind(b), nc = b.newContext.bind(b); b.newPage = async (...o) => { const p = await np(...o); await p.addInitScript(seen); return p; }; b.newContext = async (...o) => { const c = await nc(...o); await c.addInitScript(seen); return c; }; return b; }; } // the guest gift popup (multiopen.js) would cover the menu: every page starts with it already seen
const [port, out] = process.argv.slice(2);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 960, height: 600 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message + '\n' + e.stack));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ name: 'gunner', killcam: false, loadout: { primary: 'redline', secondary: 'marbles', melee: 'knife', item: 'frag' } })));
  await pg.goto(`http://localhost:${port}/`); await sleep(500);
  await pg.click('#scr-main [data-mode="training"]'); await sleep(1800);
  await pg.evaluate(async () => {
    const { net } = await import('/js/net.js');
    window.__ev = [];
    net.ws.addEventListener('message', (e) => { const m = JSON.parse(e.data); if (m.t === 'dmg' || m.t === 'kill') window.__ev.push(m); });
  });
  // stand d metres in front of a dummy and fire at its chest
  const setup = (dist) => pg.evaluate(async (dist) => {
    const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js');
    const ds = [...G.remotes.values()].filter((r) => r.alive && /Dummy/.test(r.name || ''));
    const t = ds.sort((a, b) => Math.hypot(a.pos[0] - ME.pos[0], a.pos[2] - ME.pos[2]) - Math.hypot(b.pos[0] - ME.pos[0], b.pos[2] - ME.pos[2]))[0];
    if (!t) return null;
    clearInterval(window.__hold);
    const p = [t.pos[0], t.pos[1], t.pos[2] + dist];
    window.__hold = setInterval(() => {
      ME.pos = p.slice(); ME.vel = [0, 0, 0];
      const e = [p[0], p[1] + 1.6, p[2]], to = [t.pos[0], t.pos[1] + 1.15, t.pos[2]];
      const d = to.map((v, i) => v - e[i]), L = Math.hypot(...d);
      ME.yaw = Math.atan2(-d[0], -d[2]); ME.pitch = Math.asin(d[1] / L);
    }, 5);
    return t.id;
  }, dist);
  await pg.keyboard.press('Digit2'); await sleep(700);
  const results = [];
  for (const dist of [1.5, 2.5, 3, 4, 6, 10]) {
    const id = await setup(dist);
    if (!id) { results.push([dist, 'no dummy']); continue; }
    await sleep(2600); // dummy back to full HP, reloaded
    await pg.evaluate(() => { window.__ev = []; });
    await pg.evaluate(async () => { const w = await import('/js/weapons.js'); w.fireDown(); w.fireUp(); });
    await sleep(dist === 2.5 ? 120 : 600);
    if (dist === 2.5) await pg.screenshot({ path: `${out}/marbles_flight.png` });
    await sleep(500);
    const ev = await pg.evaluate((id) => window.__ev.filter((m) => m.to === id || m.t === 'kill'), id);
    const dmg = ev.filter((m) => m.t === 'dmg').reduce((s, m) => s + m.a, 0), kill = ev.some((m) => m.t === 'kill');
    results.push([dist, dmg, kill ? 'KILL' : '']);
    if (dist === 4) await pg.screenshot({ path: `${out}/marbles_floor.png` });
  }
  console.log('marble damage by distance (m, dmg):', JSON.stringify(results));
  await pg.evaluate(() => clearInterval(window.__hold));
  // Redline: count shots in 1.5 s at different HP (client cooldown follows HP)
  await pg.keyboard.press('Digit1'); await sleep(800);
  for (const hp of [100, 50, 10]) {
    const n = await pg.evaluate(async (hp) => {
      const { ME } = await import('/js/player.js'); const w = await import('/js/weapons.js'); const { G } = await import('/js/ctx.js');
      ME.pitch = 0.3;
      window.__hp = hp; // pretend the server says this is our HP (snapshots would reset a plain assignment)
      Object.defineProperty(ME, 'hp', { get: () => window.__hp, set: () => {}, configurable: true });
      const keep = 0;
      let shots = 0; const { net } = await import('/js/net.js');
      const orig = net.send.bind(net);
      net.send = (m) => { if (m.t === 'fire') shots++; return orig(m); };
      w.fireDown(); await new Promise((r) => setTimeout(r, 1500)); w.fireUp();
      net.send = orig;
      Object.defineProperty(ME, 'hp', { value: hp, writable: true, configurable: true, enumerable: true });
      return shots;
    }, hp);
    await pg.screenshot({ path: `${out}/redline_hp${hp}.png`, clip: { x: 300, y: 200, width: 660, height: 400 } });
    console.log(`redline at ${hp} HP: ${n} shots in 1.5 s (${(n / 1.5).toFixed(1)}/s)`);
    await sleep(2200);
  }
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
