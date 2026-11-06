// playwright e2e (WP0/WP3). run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_flagoff.cjs (needs a running server; t_flagoff also wants main on 3313)
// flag OFF: the home DOM matches main exactly, and a bots match runs with no errors
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const crypto = require('crypto');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function run(port, tag) {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ name: 'flagoff', loadout: { primary: 'ar', secondary: 'snowball', melee: 'knife', item: 'frag' } })));
  await pg.goto(`http://localhost:${port}/`); await sleep(2500);
  const dom = await pg.evaluate(() => { const c = document.querySelector('#menu').cloneNode(true); for (const e of c.querySelectorAll('canvas,svg,#homeStrip,#homeEvent,.org-bg')) e.remove(); return { html: c.innerHTML.replace(/\s+/g, ' '), story: !!document.getElementById('storyBtn'), styles: document.styleSheets.length, gstory: 'story' in (window.G || {}) }; });
  require('fs').writeFileSync(process.env.SP + '/dom_' + tag + '.html', dom.html.replace(/></g, '>\n<'));
  dom.controlsRows = await pg.evaluate(async () => { const k = await import('/js/keys.js'); return k.ACTIONS.length + '/' + k.GROUPS.join('|'); });
  console.log(tag, 'controls', dom.controlsRows);
  const h = crypto.createHash('sha1').update(dom.html).digest('hex').slice(0, 12);
  await pg.screenshot({ path: `${process.env.SP}/shots/off_${tag}_home.png` });
  // a bots match: the WITH BOTS picker -> quickest path is the start api the event card uses
  await pg.click('#scr-main [data-pick="bots"]', { force: true }); await sleep(800);
  await pg.screenshot({ path: `${process.env.SP}/shots/off_${tag}_pick.png` });
  await pg.goto(`http://localhost:${port}/`); await sleep(2500);
  await pg.click('#homeEvent button', { force: true }); await sleep(4000);
  await pg.mouse.down(); await pg.keyboard.down('KeyW'); await sleep(6000); await pg.mouse.up(); await pg.keyboard.up('KeyW');
  await pg.keyboard.press('Digit3'); await sleep(300); await pg.mouse.down(); await sleep(80); await pg.mouse.up(); await sleep(6000);
  await pg.screenshot({ path: `${process.env.SP}/shots/off_${tag}_bots.png` });
  const r = await pg.evaluate(async () => { const { G } = await import('/js/ctx.js'); return { joined: G.joined, mode: G.mode, story: !!G.story, remotes: G.remotes.size, map: G.cfg.map }; });
  console.log(tag, 'dom', h, 'len', dom.html.length, 'storyBtn', dom.story, 'sheets', dom.styles, JSON.stringify(r));
  await b.close();
  return { h, errs };
}
(async () => {
  const a = await run(3313, 'main'), c = await run(3311, 'branch');
  console.log('IDENTICAL HOME DOM:', a.h === c.h, '| errors main', a.errs.length, 'branch', c.errs.length, c.errs.slice(0, 5));
})();
