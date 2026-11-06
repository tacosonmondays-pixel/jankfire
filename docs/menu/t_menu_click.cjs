// click-through: every feature reached from the new nav. PORT, SP; account cztest/hunter22 must exist with rolls left
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let bad = 0; const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) bad++; };
const vis = (pg, sel) => pg.isVisible(sel);
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
  const bad4 = []; pg.on('response', (r) => { if (r.status() >= 400) bad4.push(`${r.status()} ${r.url()}`); });
  await pg.addInitScript(() => { if (!localStorage.getItem('jankfire')) localStorage.setItem('jankfire', JSON.stringify({ name: 'clicker', killcam: false, jank: 1 })); });
  const URL = `http://localhost:${process.env.PORT}/`;
  await pg.goto(URL); await sleep(2500);
  const home = async () => { await pg.evaluate(() => { if (window.JANK.G.joined) window.JANK.quitToMenu(); window.JANK.show('main'); }); await sleep(700); };
  const lo = () => pg.evaluate(() => JSON.parse(localStorage.getItem('jankfire')).loadout);
  // the nav itself
  const nav = await pg.$$eval('#scr-main .home-left button:not(.hidden)', (bs) => bs.map((x) => x.textContent.trim()));
  console.log('home nav:', nav.join(' | '));
  ok(!nav.some((t) => /^LOADOUT|^COSMETICS/.test(t)), 'no LOADOUT / COSMETICS duplicates on the home nav');
  // CUSTOMIZE hub
  await pg.click('#navCustomize', { force: true }); await sleep(1500);
  ok(await vis(pg, '#scr-customize.lo-mode') && await vis(pg, '#czLo'), 'CUSTOMIZE opens the hub on LOADOUT');
  await pg.click('.cz-row[data-id=smg]'); await sleep(500); await pg.click('.cz-equip'); await sleep(400);
  await pg.click('.cz-lo .lo-item:has-text("Medkit")'); await sleep(400);
  const picks0 = (await lo()).streaks;
  await pg.click(`.cz-lo .lo-streak:has-text("${picks0[0] === 'moonboots' ? 'Moon Boots' : 'Moon Boots'}")`); await sleep(300);
  await pg.click('.cz-lo .lo-streak:has-text("Giant Duck")'); await sleep(400);
  let L = await lo();
  ok(L.primary === 'smg' && L.item === 'medkit' && L.streaks.includes('giantduck') && L.streaks.length === 3, 'equip SMG, Medkit, swap a killstreak for Giant Duck: ' + JSON.stringify(L));
  await pg.reload(); await sleep(2500);
  L = await lo(); ok(L.primary === 'smg' && L.item === 'medkit' && L.streaks.includes('giantduck'), 'loadout persists after reload');
  await pg.click('#navCustomize', { force: true }); await sleep(1500);
  await pg.click('.cz-hub .hub-tab[data-hub=weapons]'); await sleep(1200);
  ok(await vis(pg, '#scr-customize:not(.lo-mode)'), 'hub WEAPONS');
  for (const t of ['skin', 'wrap', 'charm', 'effect', 'finisher']) { await pg.click(`.cz-tab[data-tab=${t}]`); await sleep(600); ok(await vis(pg, '#czStrip') && (await pg.locator('#czTiles .cz-tile').count()) >= 2, `weapons tab ${t}`); }
  await pg.click('.cz-hub .hub-tab[data-hub=character]'); await sleep(1200);
  ok(await vis(pg, '#scr-character') && (await pg.locator('#lk-hair .chip').count()) > 3, 'hub CHARACTER (outfits)');
  await pg.click('#scr-character .hub-tab[data-hub=grapple]'); await sleep(1200);
  ok(await vis(pg, '#scr-cosmetics') && (await pg.locator('#sk-grapple > *').count()) > 3 && (await pg.locator('#sk-spray > *').count()) > 3, 'hub GRAPPLE & SPRAY');
  await pg.click('#scr-cosmetics .back'); await sleep(800);
  ok(await vis(pg, '#scr-main'), 'BACK to home');
  // the side menu: every button (the icon row is plaques now; ids/selectors unchanged)
  for (const [sel, scr] of [['.hicon[data-go=settings]', 'settings'], ['.hicon[data-go=guide]', 'guide'], ['.hicon[data-go=lore]', 'lore'], ['#pnBtn', 'patchnotes'], ['[data-go=leaders]', 'leaders'], ['#cratesBtn', 'crates']]) {
    await home(); await pg.click('#scr-main ' + sel, { force: true }); await sleep(900); ok(await vis(pg, '#scr-' + scr), `home ${sel} -> ${scr}`);
    if (scr === 'settings') { await pg.click('#ctlBtn'); await sleep(700); ok(await vis(pg, '#scr-controls'), 'settings -> KEY BINDINGS'); }
    if (scr === 'leaders') { await sleep(800); ok(!/loading/.test(await pg.textContent('#leaders')), 'leaderboard loads'); }
  }
  // the hero shortcuts
  await home(); await pg.click('.hero-stage', { force: true }); await sleep(900); ok(await vis(pg, '#scr-character'), 'click the 3D hero -> CHARACTER');
  await home(); await pg.click('#heroGun', { force: true }); await sleep(900); ok(await vis(pg, '#scr-customize.lo-mode'), 'click EQUIPPED gun -> LOADOUT');
  // every play card
  for (const [pick, kind] of [['online', 'qp'], ['bots', 'qp']]) {
    await home(); await pg.click(`[data-pick=${pick}]`, { force: true }); await sleep(900);
    const n = await pg.locator('#mpCards .mp-card').count();
    await pg.click(`#mpCards .mp-card[data-kind=${kind}]`, { force: true }); await sleep(3500);
    ok(await pg.evaluate(() => window.JANK.G.joined), `${pick}: ${n} mode cards, quick play joins`);
  }
  for (const m of ['coop', 'training']) { await home(); await pg.click(`[data-mode=${m}]`, { force: true }); await sleep(3500); ok(await pg.evaluate(() => window.JANK.G.joined), `${m} joins`); }
  // pause menu (in training)
  await pg.evaluate(() => document.exitPointerLock && document.exitPointerLock());
  await pg.keyboard.press('Escape'); await sleep(700); if (!(await vis(pg, '#scr-pause'))) { await pg.keyboard.press('Escape'); await sleep(700); }
  const pb = await pg.$$eval('#scr-pause button:not(.hidden)', (bs) => bs.map((x) => x.textContent.trim()));
  console.log('pause:', pb.join(' | '));
  ok(pb.join(',') === 'RESUME,CUSTOMIZE,MATCH SETTINGS,SETTINGS,QUIT TO MENU', 'pause has only resume / customize / match settings / settings / quit');
  await pg.click('#scr-pause [data-go=loadout]'); await sleep(1200); ok(await vis(pg, '#scr-customize'), 'pause -> CUSTOMIZE');
  await pg.click('.cz-tab[data-tab=leave]'); await sleep(600); ok(await vis(pg, '#scr-pause'), 'LEAVE -> pause');
  await pg.click('#scr-pause [data-go=match]'); await sleep(700); ok(await vis(pg, '#scr-match'), 'pause -> MATCH SETTINGS');
  await pg.click('#scr-match .back'); await sleep(500); await pg.click('#quit'); await sleep(1200); ok(await vis(pg, '#scr-main'), 'QUIT TO MENU');
  // account: log in, profile, open a container, log out
  await pg.click('#acctBar button:has-text("LOG IN")'); await sleep(600);
  await pg.fill('#acctName', 'cztest'); await pg.fill('#acctPass', 'hunter22'); await pg.click('#acctGo'); await sleep(2500);
  ok(await pg.locator('#acctBar button:has-text("PROFILE")').count() === 1 && await pg.locator('#acctBar button:has-text("LOG OUT")').count() === 0, 'logged in: PROFILE in the bar (log out moved to the profile page)');
  await pg.click('#cratesBtn', { force: true }); await sleep(1000);
  const open = pg.locator('#crateCards .cratecard button:not([disabled])');
  if (await open.count()) { await open.first().click(); await sleep(6500); ok((await pg.textContent('#rollResult')).length > 3, 'container opens: ' + (await pg.textContent('#rollResult'))); await pg.click('#rollBtns button:has-text("OK")'); await sleep(500); }
  else console.log('(no containers left to open on this account)');
  await home(); await pg.click('#acctBar button:has-text("PROFILE")'); await sleep(900);
  ok(await vis(pg, '#scr-profile'), 'PROFILE');
  await pg.click('#logoutBtn'); await sleep(900); ok(await pg.locator('#acctBar button:has-text("LOG IN")').count() === 1, 'LOG OUT from the profile');
  ok(errs.length === 0, 'page + console errors: ' + (errs.join(' | ') || 0));
  ok(bad4.length === 0, '4xx/5xx responses: ' + (bad4.join(' | ') || 0));
  console.log(bad ? `${bad} FAIL` : 'ALL OK');
  await b.close();
})();
