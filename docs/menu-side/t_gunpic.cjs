// the CUSTOMIZE plaque's gun at 1280x720 (and the column bottom) with different equipped guns and skins
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const CASES = [['ar', null], ['sniper', ['pink', 'none', 'none', 'default', 'full']], ['shotgun', ['wood', 'cone', 'none', 'default', 'normal']], ['smg', null], ['minigun', null], ['redline', ['pink', 'party', 'none', 'default', 'reverse']]];
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const errs = [], bad = [];
  let i = 0;
  for (const [gun, skin] of CASES) {
    const ctx = await b.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 2 });
    const pg = await ctx.newPage();
    pg.on('pageerror', (e) => errs.push(e.message)); pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    pg.on('response', (r) => { if (r.status() >= 400) bad.push(r.status() + ' ' + r.url()); });
    await pg.addInitScript(([g, s]) => { localStorage.setItem('jankfire', JSON.stringify({ name: 'gunpic', jank: 3, loadout: { primary: g, secondary: 'cig', melee: 'bread', item: 'frag', streaks: ['moonboots', 'chickenstrike', 'scythe'] }, skins: s ? { [g]: s } : {} })); }, [gun, skin]);
    await pg.goto(`http://localhost:${process.env.PORT}/`); await sleep(4500);
    await pg.evaluate(() => window.JANK.show('main')); await sleep(1200); // (models loaded: the picture follows)
    await pg.locator('#navCustomize').screenshot({ path: `${process.env.SP}/gp_${i}_${gun}.png` });
    if (i === 0) { await pg.screenshot({ path: `${process.env.SP}/gp_home720.png` }); const r = await pg.evaluate(() => { const a = document.querySelector('#pnBtn').getBoundingClientRect(), s = document.querySelector('#homeStrip').getBoundingClientRect(), st = document.querySelector('#status').getBoundingClientRect(); return { pnBottom: Math.round(a.bottom), strip: Math.round(s.top), status: Math.round(st.top) }; }); console.log('720p: patch notes bottom / strip top / status top', JSON.stringify(r)); }
    await ctx.close(); i++;
  }
  console.log(errs.join('\n') || 'no console errors'); console.log(bad.join('\n') || 'no 4xx');
  await b.close();
})();
