// every menu screen, both sizes, Too HD + Potato. OUT=dir. logged in (account) unless GUEST=1
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const OUT = process.env.OUT, PORT = process.env.PORT, TOKEN = process.env.TOKEN;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const SCREENS = (process.env.SCREENS || 'main,loadout,character,cosmetics,classic,crates,leaders,settings,controls,guide,lore,patchnotes,modes,profile,pause').split(',');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const errs = [];
  const sizes = (process.env.SIZES || '1280x720,1920x1080').split(',').map((s) => s.split('x').map(Number));
  for (const [W, H] of sizes) for (const [jank, jn] of [[3, 'toohd'], [0, 'potato']]) {
    const ctx = await b.newContext({ viewport: { width: W, height: H } });
    const pg = await ctx.newPage();
    pg.on('pageerror', (e) => errs.push(`${W} ${jn}: ${e.message}`));
    await pg.addInitScript(([t]) => { if (!localStorage.getItem('jankfire')) { localStorage.setItem('jankfire_token', t); localStorage.setItem('jankfire', JSON.stringify({ name: 'cztest', killcam: false })); } }, [TOKEN]);
    await pg.goto(`http://localhost:${PORT}/`); await sleep(2500);
    await pg.evaluate((j) => { const e = document.getElementById('jank'); e.value = String(j); e.dispatchEvent(new Event('change')); }, jank); await sleep(300);
    const go = async (s) => {
      await pg.evaluate(([s, AFTER_FLAG]) => {
        const click = (sel) => { const e = document.querySelector(sel); if (e) e.click(); return !!e; };
        click('#scr-main [data-go="settings"]'); // anything that leaves a sub-screen
        if (AFTER_FLAG) { // after the cleanup: everything through the real nav
          if (s === 'main') return window.JANK.show('main');
          if (s === 'classic') { window.JANK.show('character'); return document.querySelector('#scr-character .hub-tab[data-hub=grapple]').click(); }
          if (s === 'modes') return click('[data-pick="online"]');
          if (s === 'profile') return [...document.querySelectorAll('#acctBar button')].find((x) => x.textContent === 'PROFILE').click();
          return window.JANK.show(s);
        }
        if (s === 'main') return click('#settingsBack') || [...document.querySelectorAll('#scr-settings .back')][0].click();
        if (s === 'modes') return click('[data-pick="online"]');
        if (s === 'classic') { click('[data-go="cosmetics"]'); return setTimeout(() => click('.cz-btn:nth-last-child(1)'), 300); }
        if (s === 'profile') return [...document.querySelectorAll('#acctBar button')].find((x) => x.textContent === 'PROFILE').click();
        click(`[data-go="${s}"]`);
      }, [s, !!process.env.AFTER]);
      await sleep(s === 'cosmetics' || s === 'classic' || s === 'main' ? 2500 : 1200);
    };
    for (const s of SCREENS) {
      if (s === 'pause') {
        await go('main'); await pg.click('[data-mode="training"]', { force: true }); await sleep(5000);
        await pg.evaluate(() => document.exitPointerLock && document.exitPointerLock());
        await pg.keyboard.press('Escape'); await sleep(800);
        if (!(await pg.isVisible('#scr-pause'))) { await pg.keyboard.press('Escape'); await sleep(800); }
      } else await go(s);
      await pg.screenshot({ path: `${OUT}/${W}x${H}_${jn}_${s}.jpg`, quality: 78 });
    }
    await ctx.close();
  }
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
