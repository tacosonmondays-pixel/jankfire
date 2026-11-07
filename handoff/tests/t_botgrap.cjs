require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs'); // at most 2 headless browsers machine-wide
const { chromium } = require('playwright');
{ const L = chromium.launch.bind(chromium); chromium.launch = async (...a) => { const b = await L(...a), seen = () => { try { localStorage.setItem('jf_giftseen_all', '1'); } catch (e) { /* no storage */ } }; const np = b.newPage.bind(b), nc = b.newContext.bind(b); b.newPage = async (...o) => { const p = await np(...o); await p.addInitScript(seen); return p; }; b.newContext = async (...o) => { const c = await nc(...o); await c.addInitScript(seen); return c; }; return b; }; } // the guest gift popup (multiopen.js) would cover the menu: every page starts with it already seen
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 800, height: 500 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.goto('http://localhost:3000/'); await pg.waitForTimeout(500);
  await pg.click('[data-pick="bots"]'); await pg.waitForTimeout(700); await pg.click('#mpCustom');
  await pg.selectOption('#setupMap', process.argv[3] || 'skyline');
  await pg.locator('#setupBots').fill('8');
  await pg.selectOption('#setupDiff', 'hard');
  await pg.click('#setupGo'); await pg.waitForTimeout(1500);
  // fly high above so bots have reasons to grapple, and record who's on a rope
  await pg.evaluate(async () => {
    const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js');
    window.__hooks = new Set(); window.__hookFrames = 0; window.__frames = 0;
    setInterval(() => { window.__frames++; let any = false; for (const r of G.remotes.values()) if (r.g && r.alive) { window.__hooks.add(r.id); any = true; } if (any) window.__hookFrames++; }, 100);
  });
  await pg.waitForTimeout(25000);
  const res = await pg.evaluate(() => ({ bots: window.__hooks.size, hookFrames: window.__hookFrames, frames: window.__frames }));
  console.log(JSON.stringify(res));
  await pg.screenshot({ path: process.argv[2] + '/botgrapple.png' });
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
