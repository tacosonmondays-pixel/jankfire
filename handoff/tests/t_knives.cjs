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
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ name: 'knives', loadout: { primary: 'ar', secondary: 'revolver', melee: 'knife' } })));
  await pg.goto('http://localhost:3000/'); await sleep(500);
  await pg.click('#scr-main [data-mode="training"]'); await sleep(1500);
  // look at the sky so the knife reads against a flat background
  await pg.evaluate(async () => { const { ME } = await import('/js/player.js'); setInterval(() => { ME.pitch = 0.35; }, 10); });
  const plan = [
    ['knife_butterfly', [['draw', 0, 260], ['draw', 0, 400], ['inspect', 1, 480], ['inspect', 1, 1080]]],
    ['knife_switch', [['draw', 0, 120], ['draw', 0, 220], ['inspect', 1, 1000], ['inspect', 1, 500]]],
    ['knife_karambit', [['draw', 0, 150], ['draw', 0, 330], ['inspect', 1, 550], ['inspect', 1, 1700]]],
    ['knife_bowie', [['draw', 0, 180], ['inspect', 1, 550], ['inspect', 1, 1300]]],
    ['knife_cleaver', [['inspect', 1, 800], ['swing', 2, 150]]],
    ['knife_kitchen', [['inspect', 1, 700], ['inspect', 1, 1500]]],
  ];
  for (const [model, shots] of plan) {
    await pg.evaluate(async (model) => {
      const { G } = await import('/js/ctx.js');
      const w = await import('/js/weapons.js');
      G.equipped.knife = ['default', 'none', 'none', model];
      w.rebuildViewmodels();
    }, model);
    for (const [what, , at] of shots) {
      await pg.keyboard.press('Digit1'); await sleep(450);
      await pg.keyboard.press('Digit3');
      if (what === 'inspect') { await sleep(650); await pg.keyboard.press('KeyF'); }
      if (what === 'swing') { await sleep(650); await pg.evaluate(async () => { const w = await import('/js/weapons.js'); w.fireDown(); w.fireUp(); }); }
      await sleep(at);
      await pg.screenshot({ path: `${out}/kn_${model}_${what}_${at}.png`, clip: { x: 220, y: 150, width: 420, height: 250 } });
    }
  }
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
