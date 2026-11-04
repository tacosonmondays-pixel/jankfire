require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs'); // at most 2 headless browsers machine-wide
const { chromium } = require('playwright');
const out = process.argv[2];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 960, height: 600 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message + '\n' + e.stack));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ name: 'itemtest', loadout: { primary: 'ar', secondary: 'snowball', melee: 'knife', item: 'frag' } })));
  await pg.goto('http://localhost:' + (process.env.PORT || 3000) + '/'); await sleep(500);
  await pg.click('#scr-main [data-mode="training"]'); await sleep(1800);
  await pg.evaluate(async () => {
    const { net } = await import('/js/net.js');
    window.__ev = [];
    net.ws.addEventListener('message', (e) => { const m = JSON.parse(e.data); if (m.t !== 'sn' && m.t !== 'po') window.__ev.push(m); });
  });
  await pg.evaluate(async () => { const { net } = await import('/js/net.js'); window.__sent = []; const s0 = net.ws.send.bind(net.ws); net.ws.send = (d) => { try { const m = JSON.parse(d); if (m.t === 'itemsel') window.__sent.push(m.i); } catch { /* */ } return s0(d); }; });
  const aim = (lob = 0) => pg.evaluate(async (lob) => {
    const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js');
    let best = null, bd = 1e9;
    for (const r of G.remotes.values()) { if (!r.alive) continue; const d = Math.hypot(r.pos[0] - ME.pos[0], r.pos[2] - ME.pos[2]); if (d < bd && d > 4) { bd = d; best = r; } }
    if (!best) return 'none';
    const e = [ME.pos[0], ME.pos[1] + 1.6, ME.pos[2]];
    const t = [best.pos[0], best.pos[1] + 1.2 + lob * bd * 0.35 + bd * bd * 0.0035, best.pos[2]];
    const d = t.map((v, i) => v - e[i]), L = Math.hypot(...d);
    ME.yaw = Math.atan2(-d[0], -d[2]); ME.pitch = Math.asin(d[1] / L);
    return best.id + '@' + bd.toFixed(1);
  }, lob);
  const count = (f) => pg.evaluate((src) => window.__ev.filter(eval(src)).length, f);
  // frag x2
  console.log('aim', await aim(0.25));
  await pg.keyboard.press('KeyG'); await sleep(300); await pg.keyboard.press('KeyG'); await sleep(400); await pg.keyboard.press('KeyG');
  await sleep(2600);
  await pg.screenshot({ path: `${out}/it_frag.png` });
  console.log('frags thrown', await count("(m) => m.t === 'ps' && m.k === 'frag'"), 'booms', await count("(m) => m.t === 'boom'"), 'dmg', await count("(m) => m.t === 'dmg' && m.w === 'frag'"), 'charges msg', JSON.stringify(await pg.evaluate(() => window.__ev.filter((m) => m.t === 'ic').map((m) => m.n))));
  // other items
  // the server only lets you use your equipped item: switch it the real way (LOADOUT while dead sends 'itemsel' now)
  const ITEM_NAME = { medkit: 'Medkit', bubble: 'Shield Bubble', smoke: 'Smoke' };
  for (const id of ['medkit', 'bubble', 'smoke']) {
    await pg.evaluate(async () => { const { ME } = await import('/js/player.js'); const { net } = await import('/js/net.js'); net.send({ t: 's', q: ME.seq, p: [0, -2000, 0], v: [0, 0, 0], y: 0, x: 0, w: 'ar', f: 0 }); });
    await sleep(400);
    await pg.evaluate(([id, name]) => { window.JANK.show('loadout'); const b = [...document.querySelectorAll('#lo-item button')].find((x) => x.textContent.startsWith(name)); if (b) b.click(); document.getElementById('resume').click(); }, [id, ITEM_NAME[id]]);
    for (let i = 0; i < 20 && !(await pg.evaluate(async () => (await import('/js/player.js')).ME.alive)); i++) await sleep(300);
    await sleep(400);
    await aim(0.2);
    await pg.keyboard.press('KeyG'); await sleep(id === 'smoke' ? 2200 : 700);
    await pg.screenshot({ path: `${out}/it_${id}.png` });
  }
  console.log('itemsel sent', JSON.stringify(await pg.evaluate(() => window.__sent || []))); console.log('medkit fx', await count("(m) => m.t === 'fx' && m.k === 'medkit'"), 'bubble', await count("(m) => m.t === 'bub+'"), 'smoke', await count("(m) => m.t === 'smoke'"));
  // snowballs: 4 to freeze, 5th shatters
  await pg.keyboard.press('Digit2'); await sleep(500);
  for (let i = 0; i < 6; i++) {
    await aim(0);
    await pg.evaluate(async () => { const w = await import('/js/weapons.js'); w.fireDown(); w.fireUp(); });
    await sleep(i === 3 ? 450 : 420);
    if (i === 3) await pg.screenshot({ path: `${out}/it_frozen.png` });
  }
  await sleep(500);
  console.log('frost', await count("(m) => m.t === 'frost'"), 'freeze', await count("(m) => m.t === 'freeze'"), 'shatter', await count("(m) => m.t === 'fx' && m.k === 'shatter'"), 'snow kills', await count("(m) => m.t === 'kill' && m.w === 'snowball'"));
  console.log('hotbar item', await pg.textContent('#itemSlot'));
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
