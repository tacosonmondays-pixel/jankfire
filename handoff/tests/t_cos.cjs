try { require((process.env.SP || __dirname) + '/pwlock.cjs'); } catch {} // at most 2 headless browsers machine-wide
const { chromium } = require('playwright');
{ const L = chromium.launch.bind(chromium); chromium.launch = async (...a) => { const b = await L(...a), seen = () => { try { localStorage.setItem('jf_giftseen_all', '1'); } catch (e) { /* no storage */ } }; const np = b.newPage.bind(b), nc = b.newContext.bind(b); b.newPage = async (...o) => { const p = await np(...o); await p.addInitScript(seen); return p; }; b.newContext = async (...o) => { const c = await nc(...o); await c.addInitScript(seen); return c; }; return b; }; } // the guest gift popup (multiopen.js) would cover the menu: every page starts with it already seen
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 900 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.goto('http://localhost:3000/'); await pg.waitForTimeout(500);
  await pg.click('#navCustomize', { force: true }); await pg.waitForTimeout(800); // CUSTOMIZE (the hub opens on LOADOUT)
  await pg.click('.cz-hub .hub-tab[data-hub=weapons]'); await pg.waitForTimeout(600);
  await pg.click('.cz-tab[data-tab=wrap]'); await pg.waitForTimeout(400);
  console.log('all mode default', await pg.isChecked('.cz-chk:has-text("every weapon") input'));
  await pg.click('.cz-tile[data-k=pink]');
  await pg.click('.cz-tab[data-tab=charm]'); await pg.waitForTimeout(300);
  await pg.click('.cz-tile[data-k=cone]');
  const skins = await pg.evaluate(() => JSON.parse(localStorage.getItem('jankfire')).skins);
  const ids = Object.keys(skins);
  console.log('weapons dressed', ids.length, 'scythe?', !!skins.scythe, 'sample', JSON.stringify(skins.knife), JSON.stringify(skins.ar));
  await pg.click('.cz-tab[data-tab=finisher]'); await pg.waitForTimeout(300);
  console.log('list has killstreak', await pg.locator('#czList .cz-slot:has-text("Killstreak")').count(), 'kill tiles', await pg.locator('#czTiles .cz-tile').count());
  const eq = await pg.evaluate(async () => (await import('/js/ctx.js')).G.equipped.scythe_rifle);
  console.log('scythe_rifle borrows', JSON.stringify(eq));
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
