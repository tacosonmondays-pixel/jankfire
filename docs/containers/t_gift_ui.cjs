// gift popup (guest + new account), the CONTAINERS cards, an x10 open (rattling + results) and OPEN ALL. SP, PORT, OUT
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let bad = 0; const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) bad++; };
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const ctx = await b.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 2 });
  const pg = await ctx.newPage();
  const errs = [], bad4 = [];
  pg.on('pageerror', (e) => errs.push(e.message)); pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  pg.on('response', (r) => { if (r.status() >= 400) bad4.push(r.status() + ' ' + r.url()); });
  const O = (n) => `${process.env.OUT}/${n}.jpg`;
  await pg.goto(`http://localhost:${process.env.PORT}/`); await sleep(5000);
  ok(await pg.isVisible('#multibox .gift'), 'a guest sees the gift once, with LOG IN TO CLAIM');
  await pg.screenshot({ path: O('gift_guest'), quality: 85 });
  await pg.click('#multibox button:has-text("LATER")'); await sleep(400);
  await pg.reload(); await sleep(4000);
  ok(!(await pg.isVisible('#multibox .gift')), '...and not again after a reload');
  // sign up: the gift lands
  await pg.click('#acctBar button:has-text("SIGN UP")'); await sleep(600);
  const name = 'gift' + Date.now().toString(36).slice(-5);
  await pg.fill('#acctName', name); await pg.fill('#acctPass', 'hunter22'); await pg.fill('#acctPass2', 'hunter22'); await pg.click('#acctGo'); await sleep(3500);
  ok(await pg.isVisible('#multibox .gift') && /\+30[\s\S]*\+25[\s\S]*\+70/.test(await pg.textContent('#multibox')), 'new account: THE MANAGEMENT FEELS GENEROUS +30 / +25 / +70');
  await sleep(800); await pg.screenshot({ path: O('gift_popup'), quality: 85 });
  await pg.click('#multibox button:has-text("OPEN THEM")'); await sleep(2500);
  ok(await pg.isVisible('#scr-crates'), 'OPEN THEM goes to CONTAINERS');
  await pg.screenshot({ path: O('crates_cards'), quality: 85 });
  // x10 crates
  await pg.click('#crateCards .cratecard >> nth=0 >> button[data-n="10"]'); await sleep(900);
  ok(await pg.isVisible('#multibox .mo-shake'), 'x10: ten crates rattling');
  await pg.screenshot({ path: O('x10_rattle'), quality: 85 });
  await sleep(4500);
  const n = await pg.locator('#multibox .mo-card').count();
  ok(n === 10, `x10 results: ${n} cards; ${await pg.textContent('#multibox .mo-sum')}`);
  await sleep(6000); await pg.screenshot({ path: O('x10_results'), quality: 85 }); // (time for skin models to land: their pictures redraw)
  const left = await pg.evaluate(async () => (await import('/js/account.js')).account.me.rolls.crate);
  ok(left === 21, 'crates left: ' + left);
  // equip one from the results (a skin goes on its weapon)
  const eq = pg.locator('#multibox .mo-eq').first();
  if (await eq.count()) { await eq.click(); await sleep(300); ok((await eq.textContent()) === 'ON ✓', 'EQUIP from the results'); }
  await pg.click('#multibox button:has-text("OK")'); await sleep(600);
  // OPEN ALL boxes (71 -> 0) with a click-to-skip
  await pg.click('#crateCards .cratecard >> nth=2 >> button[data-n="all"]'); await sleep(700);
  await pg.mouse.click(640, 300); await sleep(3500);
  const m = await pg.locator('#multibox .mo-card').count();
  ok(m === 71, `OPEN ALL boxes, skipped: ${m} cards`);
  await sleep(1500); await pg.screenshot({ path: O('all_boxes_results'), quality: 85 });
  ok(errs.length === 0, 'page/console errors: ' + (errs.join(' | ') || 0));
  ok(bad4.length === 0, '4xx: ' + (bad4.join(' | ') || 0));
  console.log(bad ? `${bad} FAIL` : 'ALL OK');
  await b.close();
})();
