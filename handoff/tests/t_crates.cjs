require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs'); // at most 2 headless browsers machine-wide
const { chromium } = require('playwright');
{ const L = chromium.launch.bind(chromium); chromium.launch = async (...a) => { const b = await L(...a), seen = () => { try { localStorage.setItem('jf_giftseen_all', '1'); } catch (e) { /* no storage */ } }; const np = b.newPage.bind(b), nc = b.newContext.bind(b); b.newPage = async (...o) => { const p = await np(...o); await p.addInitScript(seen); return p; }; b.newContext = async (...o) => { const c = await nc(...o); await c.addInitScript(seen); return c; }; return b; }; } // the guest gift popup (multiopen.js) would cover the menu: every page starts with it already seen
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const pg = await b.newPage({ viewport: { width: 1200, height: 800 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message + e.stack));
  await pg.goto('http://localhost:3000/'); await pg.waitForTimeout(500);
  const nm = 'crt' + (Date.now() % 100000);
  await pg.evaluate(async (nm) => { const a = await import('/js/account.js'); await a.register(nm, 'hunter22'); }, nm);
  await pg.reload(); await pg.waitForTimeout(900);
  console.log('menu btn', await pg.textContent('#cratesBtn'));
  await pg.click('#cratesBtn'); await pg.waitForTimeout(300);
  await pg.screenshot({ path: process.argv[2] + '/crates.png' });
  await pg.click('#crateCards .cratecard >> nth=1 >> button'); await pg.waitForTimeout(3500);
  console.log('roll result', (await pg.textContent('#rollResult')).trim().slice(0, 80));
  await pg.click('#rollBtns button >> text=OK').catch(() => {});
  await pg.waitForTimeout(300);
  console.log('after', await pg.textContent('#cratesBtn'), '| cards', (await pg.textContent('#crateCards')).replace(/\s+/g, ' ').slice(0, 160));
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
