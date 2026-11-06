require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const PORT = process.env.PORT, TOKEN = process.env.TOKEN, URL = `http://localhost:${PORT}/`;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let bad = 0; const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) bad++; };
const S = (pg) => pg.evaluate(async () => { const { G } = await import('/js/ctx.js'); return JSON.parse(JSON.stringify({ skins: G.settings.skins, favs: G.settings.favs, kfx: G.settings.kfx, eq: G.equipped, id: G.myId, joined: G.joined })); });
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const errs = [];
  const mk = async (token, name) => {
    const ctx = await b.newContext({ viewport: { width: 1280, height: 720 } });
    const pg = await ctx.newPage();
    pg.on('pageerror', (e) => errs.push(name + ': ' + e.message));
    await pg.addInitScript(([t, n]) => { if (!localStorage.getItem('jankfire')) { if (t) localStorage.setItem('jankfire_token', t); localStorage.setItem('jankfire', JSON.stringify({ name: n, killcam: false, jank: 1 })); } }, [token, name]);
    await pg.goto(URL); await sleep(3000);
    return pg;
  };
  // ---- account: equip, favourites, random, finisher
  const A = await mk(TOKEN, 'cztest');
  await A.click('#scr-main [data-go="cosmetics"]', { force: true }); await sleep(1500);
  ok(await A.isVisible('#scr-customize'), 'COSMETICS opens the customize screen');
  await A.click('.cz-tab[data-tab=wrap]'); await sleep(800);
  ok(!(await A.isChecked('.cz-chk:has-text("every weapon") input')), 'put it on every weapon starts unticked');
  await A.click('.cz-tile[data-k=neon]'); await sleep(500);
  await A.click('.cz-wm button:has-text("REVERSE")'); await sleep(400);
  let s = await S(A);
  ok(s.skins.ar && s.skins.ar[0] === 'neon' && s.skins.ar[4] === 'reverse', 'equip neon wrap, reverse mode: ' + JSON.stringify(s.skins.ar));
  ok(!s.skins.smg, 'only the AR got it (copy-to-all off)');
  await A.click('.cz-tab[data-tab=charm]'); await sleep(800);
  for (const k of ['cowboy', 'chef', 'crown']) { // hearts on cowboy + chef only (the account may remember an earlier run)
    const fav = await A.locator(`.cz-tile[data-k=${k}] .heart`).evaluate((e) => e.classList.contains('fav'));
    if (fav !== (k !== 'crown')) await A.click(`.cz-tile[data-k=${k}] .heart`);
  }
  await sleep(300);
  await A.locator('.cz-chk:has-text("favourites") input').check(); await sleep(300);
  await A.click('.cz-tile.rand'); await sleep(500);
  s = await S(A);
  ok(s.favs && s.favs.hat.includes('cowboy') && s.favs.hat.includes('chef') && s.favs.only.includes('hat'), 'favourites + only-favourites saved: ' + JSON.stringify(s.favs));
  ok(s.skins.ar[1] === 'random' && ['cowboy', 'chef'].includes(s.eq.ar[1]), `charm = random, menu roll ${s.eq.ar[1]}`);
  await A.click('.cz-tab[data-tab=finisher]'); await sleep(600);
  await A.click('.cz-tile[data-k=grave]'); await sleep(300);
  ok((await S(A)).kfx === 'grave', 'finisher = tombstone');
  await sleep(1800); // profile save is debounced
  await A.reload(); await sleep(3500);
  s = await S(A);
  ok(s.skins.ar[0] === 'neon' && s.skins.ar[1] === 'random' && s.kfx === 'grave', 'after reload: ' + JSON.stringify(s.skins.ar) + ' ' + s.kfx);
  const C = await mk(TOKEN, 'other'); // a fresh device: only the token, everything comes from the account
  s = await S(C);
  ok(s.skins.ar && s.skins.ar[0] === 'neon' && s.favs && s.favs.hat.length === 2 && s.kfx === 'grave', 'fresh device loads it from the account: ' + JSON.stringify(s.skins.ar) + ' favs ' + JSON.stringify(s.favs));
  await C.context().close();
  // ---- guest: browse, try on, can't equip locked
  const B = await mk(null, 'guesty');
  await B.click('#scr-main [data-go="cosmetics"]', { force: true }); await sleep(1500);
  await B.click('.cz-tab[data-tab=wrap]'); await sleep(800);
  await B.hover('.cz-tile[data-k=gold]'); await sleep(600);
  ok((await B.textContent('#czHover b')) === 'Gold' && await B.isVisible('#czHover'), 'guest hovers a locked wrap: title shows (try-on)');
  await B.click('.cz-tile[data-k=gold]'); await sleep(400);
  s = await S(B);
  ok(!s.skins.ar || s.skins.ar[0] !== 'gold', 'guest can not equip a locked wrap');
  await B.click('.cz-tile[data-k=pink]'); await sleep(400);
  ok((await S(B)).skins.ar[0] === 'pink', 'guest can equip a free wrap');
  // ---- both into online quick play: B sees A's look, A's random charm rerolls every life
  await A.click('#scr-main [data-go="cosmetics"]', { force: true }); await sleep(800); // A is on the main menu after the reload
  for (const pg of [A, B]) { await pg.click('.cz-tab[data-tab=leave]'); await sleep(500); await pg.click('[data-pick="online"]', { force: true }); await sleep(800); await pg.click('.mp-card[data-kind=qp]', { force: true }); await sleep(3500); }
  const aId = (await S(A)).id;
  const seen = await B.evaluate(async (id) => { const { G } = await import('/js/ctx.js'); return G.skins.get(id) && G.skins.get(id).ar; }, aId);
  ok(seen && seen[0] === 'neon' && seen[4] === 'reverse' && ['cowboy', 'chef'].includes(seen[1]), 'other client sees A: ' + JSON.stringify(seen));
  const rolls = [];
  for (let i = 0; i < 5; i++) {
    await A.evaluate(async () => { const { net } = await import('/js/net.js'); const { ME } = await import('/js/player.js'); net.send({ t: 's', q: ME.seq, p: [0, -9999, 0], v: [0, 0, 0], y: 0, x: 0, w: 'ar' }); });
    await sleep(4200);
    const a = (await S(A)).eq.ar[1];
    const bSees = await B.evaluate(async (id) => { const { G } = await import('/js/ctx.js'); return (G.skins.get(id) || {}).ar; }, aId);
    rolls.push(a + (bSees && bSees[1] === a ? '' : '(B saw ' + (bSees && bSees[1]) + ')'));
  }
  console.log('charm rolls per life:', rolls.join(', '));
  ok(rolls.every((r) => /^(cowboy|chef)$/.test(r)), 'every roll is a favourite, and the other client saw the same');
  ok(new Set(rolls).size > 1, 'random changed across respawns');
  console.log(errs.join('\n') || 'no page errors');
  console.log(bad ? `${bad} FAIL` : 'ALL OK');
  await b.close();
})();
