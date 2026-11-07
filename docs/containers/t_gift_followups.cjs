// follow-ups: killstreak skins in bulk results (their own 3D look + PUT ON <streak>), the guest gift popup closes on
// Esc and on a click outside. needs an account "streaky" that owns every crate skin but the killstreak ones. SP, PORT, OUT
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let bad = 0; const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) bad++; };
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const errs = [];
  const mk = async () => { const c = await b.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 2 }); const pg = await c.newPage(); pg.on('pageerror', (e) => errs.push(e.message)); pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); }); pg.on('response', (r) => { if (r.status() >= 400) errs.push(r.status() + ' ' + r.url()); }); return pg; };
  // guest popup: Esc, then (fresh guest) a click outside -> the PLAY card under it works
  let pg = await mk();
  await pg.goto(`http://localhost:${process.env.PORT}/`); await sleep(5000);
  ok(await pg.isVisible('#multibox .gift'), 'guest popup shows');
  await pg.keyboard.press('Escape'); await sleep(300);
  ok(!(await pg.isVisible('#multibox .gift')), 'Esc closes it');
  await pg.context().close();
  pg = await mk();
  await pg.goto(`http://localhost:${process.env.PORT}/`); await sleep(5000);
  await pg.mouse.click(1100, 640); await sleep(400); // outside the memo, over the PLAY column
  ok(!(await pg.isVisible('#multibox .gift')), 'a click outside closes it');
  await pg.click('[data-pick="bots"]', { force: true }); await sleep(800);
  ok(await pg.isVisible('#scr-modes'), 'and the PLAY cards work right after');
  await pg.context().close();
  // a test hook: jf_giftseen_all skips the popup (the handoff scripts set it)
  pg = await mk();
  await pg.addInitScript(() => localStorage.setItem('jf_giftseen_all', '1'));
  await pg.goto(`http://localhost:${process.env.PORT}/`); await sleep(5000);
  ok(!(await pg.isVisible('#multibox .gift')), 'jf_giftseen_all: no popup');
  // killstreak skins from a bulk open
  await pg.click('#acctBar button:has-text("LOG IN")'); await sleep(500);
  await pg.fill('#acctName', 'streaky'); await pg.fill('#acctPass', 'hunter22'); await pg.click('#acctGo'); await sleep(3000);
  if (await pg.isVisible('#multibox .gift')) { await pg.keyboard.press('Escape'); await sleep(300); }
  await pg.evaluate(() => window.JANK.show('crates')); await sleep(1500);
  await pg.click('#crateCards .cratecard >> nth=0 >> button[data-n="5"]'); await sleep(900);
  await pg.mouse.click(640, 300); await sleep(9000); // skip, then time for the streak models to land
  const cards = await pg.$$eval('#multibox .mo-card', (cs) => cs.map((c) => ({ name: c.querySelector('b').textContent, img: !!(c.querySelector('img') && c.querySelector('img').getAttribute('src')), gift: !!c.querySelector('.glyph'), btn: (c.querySelector('.mo-eq') || {}).textContent || '' })));
  console.log(JSON.stringify(cards));
  ok(cards.length === 5 && cards.every((c) => c.img && !c.gift), 'every killstreak skin has its 3D picture (no gift box)');
  ok(cards.every((c) => /^PUT ON /.test(c.btn)), 'every one has a PUT ON <streak> button');
  await pg.screenshot({ path: `${process.env.OUT}/streak_skins_results.jpg`, quality: 85 });
  await pg.click('#multibox .mo-eq >> nth=0'); await sleep(400);
  const first = cards[0].name;
  const sk = await pg.evaluate(() => JSON.parse(localStorage.getItem('jankfire')).skins);
  const hit = Object.entries(sk).find(([k, v]) => Array.isArray(v) && v[3] && v[3] !== 'default');
  ok(!!hit, `PUT ON saved the look: ${first} -> ${hit && hit[0]} = ${hit && JSON.stringify(hit[1])}`);
  ok(errs.length === 0, 'errors: ' + (errs.join(' | ') || 0));
  console.log(bad ? `${bad} FAIL` : 'ALL OK');
  await b.close();
})();
