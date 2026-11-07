// playwright e2e (WP0/WP3). run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_sweep.cjs (needs a running server; t_flagoff also wants main on 3313)
// WP3 sweep: every held weapon from a rotating bar slot (equip + fire + reload), every gear item from the bar (G throws one)
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const skipIntro = require('./skipintro.cjs'); // the intro cinematic holds the keys: skip it
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 960, height: 600 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message + ' ' + (e.stack || '').split('\n')[1]));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.addInitScript(() => { localStorage.setItem('jankfire', JSON.stringify({ name: 'sweep', loadout: { primary: 'ar', secondary: 'pistol', melee: 'knife', item: 'frag' } })); if (!sessionStorage.getItem('sw')) { sessionStorage.setItem('sw', 1); localStorage.removeItem('jfStorySaves'); } });
  await pg.goto(`http://localhost:${process.env.PORT}/?story=1&storydev=1&storytest=1`); await sleep(1500);
  await pg.click('#storyBtn', { force: true }); await sleep(700); await pg.click('#storyPick .st-btn.yellow', { force: true }); await sleep(3500); await skipIntro(pg);
  const ids = await pg.evaluate(async () => { const { WEAPONS, ITEMS } = await import('/shared/weapons.js'); const { kindOf } = await import('/shared/story/items.js'); return { w: Object.keys(WEAPONS).filter((k) => kindOf(k) === 'gun' || kindOf(k) === 'melee'), g: Object.keys(ITEMS) }; });
  await pg.evaluate(async () => { const { net } = await import('/js/net.js'); window.__sent = []; const s0 = net.ws.send.bind(net.ws); net.ws.send = (d) => { try { const m = JSON.parse(d); if (m.t === 'fire' || m.t === 'item' || m.t === 'hit') window.__sent.push(m.t + ':' + (m.w || m.i || '')); } catch {} return s0(d); }; });
  const empty = () => pg.evaluate(async () => { const { clearDrops } = await import('/js/story/bar.js'); clearDrops(); const { G } = await import('/js/ctx.js'); const { IV } = await import('/js/story/bar.js'); for (const x of IV.inv.bag) if (x) G.story.send('inv', { op: 'drop', u: x.u }); });
  const bad = [];
  let n = 0;
  for (const id of ids.w) {
    const slot = n++ % 8;
    if (slot === 0) { await empty(); await sleep(300); }
    await pg.evaluate(async ([id, slot]) => { const { G } = await import('/js/ctx.js'); G.story.send('give', { b: id, slot }); }, [id, slot]);
    await pg.waitForFunction(async ([id, slot]) => { const { IV } = await import('/js/story/bar.js'); const u = IV.inv.bar[slot]; const x = IV.inv.bag.find((y) => y && y.u === u); return !!x && x.b === id; }, [id, slot], { timeout: 5000 }).catch(() => bad.push(id + ': never reached the bar'));
    await pg.keyboard.press('Digit' + (slot + 1)); await sleep(450);
    await pg.mouse.down(); await sleep(1000); await pg.mouse.up(); await sleep(200);
    await pg.keyboard.press('KeyR'); await sleep(120);
    const r = await pg.evaluate(async (id) => { const { W } = await import('/js/weapons.js'); const s = window.__sent.splice(0); return { cur: W.cur, fired: s.some((x) => x.endsWith(':' + id)), s }; }, id);
    if (r.cur !== id) bad.push(`${id}: holding ${r.cur}`);
    if (!r.fired) bad.push(`${id}: no fire msg (${r.s.join(' ')})`);
  }
  console.log('weapons swept', ids.w.length);
  for (const g of ids.g) {
    await empty(); await sleep(300);
    await pg.evaluate(async (g) => { const { G } = await import('/js/ctx.js'); G.story.send('give', { b: g, slot: 3, q: 2 }); }, g);
    await pg.waitForFunction(async (g) => { const { IV } = await import('/js/story/bar.js'); const u = IV.inv.bar[3]; const x = IV.inv.bag.find((y) => y && y.u === u); return !!x && x.b === g; }, g, { timeout: 5000 }).catch(() => bad.push(g + ': never reached the bar'));
    await pg.keyboard.press('Digit4'); await sleep(300);
    const before = await pg.evaluate(async () => { const { W } = await import('/js/weapons.js'); return W.item; });
    await pg.keyboard.press('KeyG'); await sleep(700);
    const r = await pg.evaluate(async (g) => { const { IV } = await import('/js/story/bar.js'); const { count } = await import('/shared/story/items.js'); return { left: count(IV.inv, g), sent: window.__sent.splice(0) }; }, g);
    if (before !== g) bad.push(`gear ${g}: G item is ${before}`);
    if (!r.sent.includes('item:' + g)) bad.push(`gear ${g}: no item msg (${r.sent.join(' ')})`);
    else if (r.left !== 1) bad.push(`gear ${g}: ${r.left} left, wanted 1`);
  }
  console.log('gear swept', ids.g.length);
  console.log('PROBLEMS', bad.length, '\n' + bad.join('\n'));
  console.log('ERRORS', errs.length, errs.slice(0, 10).join('\n'));
  await b.close();
})();
