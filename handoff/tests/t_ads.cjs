require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs'); // at most 2 headless browsers machine-wide
const { chromium } = require('playwright');
{ const L = chromium.launch.bind(chromium); chromium.launch = async (...a) => { const b = await L(...a), seen = () => { try { localStorage.setItem('jf_giftseen_all', '1'); } catch (e) { /* no storage */ } }; const np = b.newPage.bind(b), nc = b.newContext.bind(b); b.newPage = async (...o) => { const p = await np(...o); await p.addInitScript(seen); return p; }; b.newContext = async (...o) => { const c = await nc(...o); await c.addInitScript(seen); return c; }; return b; }; } // the guest gift popup (multiopen.js) would cover the menu: every page starts with it already seen
const out = process.argv[2];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 640, height: 400 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message + '\n' + e.stack));
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ name: 'ads', skins: { ar: ['default', 'tophat', 'none', 'default'] } })));
  await pg.goto('http://localhost:3000/'); await sleep(500);
  await pg.click('#scr-main [data-mode="training"]'); await sleep(1500);
  await pg.evaluate(async () => { const { ME } = await import('/js/player.js'); setInterval(() => { ME.pitch = 0.02; ME.yaw = 0; }, 10); });
  await pg.addStyleTag({ content: '#centerMark{position:fixed;left:50%;top:50%;width:6px;height:6px;margin:-3px 0 0 -3px;background:red;z-index:99;pointer-events:none}' });
  await pg.evaluate(() => { const d = document.createElement('div'); d.id = 'centerMark'; document.body.append(d); });
  for (const id of (process.argv[3] || 'ar,smg,shotgun,revolver,banana,chicken,minigun,bow,bowling').split(',')) {
    const slot = ['revolver'].includes(id) ? 'secondary' : 'primary';
    await pg.evaluate(async ([id, slot]) => {
      const w = await import('/js/weapons.js');
      const lo = { primary: 'ar', secondary: 'cards', melee: 'knife' }; lo[slot] = id;
      w.setLoadout(lo); w.switchSlot(slot === 'primary' ? 1 : 0); w.switchSlot(slot === 'primary' ? 0 : 1);
    }, [id, slot]);
    await sleep(500);
    await pg.screenshot({ path: `${out}/ads_${id}_hip.png` });
    await pg.evaluate(async () => { const { W } = await import('/js/weapons.js'); W.aimHeld = true; });
    await sleep(500);
    await pg.screenshot({ path: `${out}/ads_${id}_ads.png` });
    await pg.evaluate(async () => { const { W } = await import('/js/weapons.js'); W.aimHeld = false; });
    await sleep(300);
  }
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
