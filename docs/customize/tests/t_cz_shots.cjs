// customize screen screenshots: Too HD + Potato, 1920x1080 + 1280x720, every tab, hover, search. logged in (owned + locked mix)
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const OUT = process.env.OUT, PORT = process.env.PORT, TOKEN = process.env.TOKEN;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const errs = [];
  for (const [W, H] of [[1920, 1080], [1280, 720]]) for (const [jank, jn] of [[3, 'toohd'], [0, 'potato']]) {
    const ctx = await b.newContext({ viewport: { width: W, height: H } });
    const pg = await ctx.newPage();
    pg.on('pageerror', (e) => errs.push(`${W} ${jn}: ${e.message}`));
    await pg.addInitScript(([t, j]) => { if (!localStorage.getItem('jankfire')) { localStorage.setItem('jankfire_token', t); localStorage.setItem('jankfire', JSON.stringify({ name: 'cztest', jank: j, skins: { ar: ['chrome', 'cowboy', 'sparkles', 'default', 'normal'] } })); } }, [TOKEN, jank]);
    await pg.goto(`http://localhost:${PORT}/`); await sleep(2500);
    await pg.evaluate((j) => { const e = document.getElementById('jank'); e.value = String(j); e.dispatchEvent(new Event('change')); }, jank); await sleep(300); // after login: the account's synced preset would win otherwise
    console.log(`${W}x${H} preset`, await pg.evaluate(() => document.getElementById('jank').selectedOptions[0].textContent));
    const tag = `${W}x${H}_${jn}`;
    await pg.click('#scr-main [data-go="cosmetics"]', { force: true }); await sleep(2500);
    await pg.screenshot({ path: `${OUT}/${tag}_0_main.jpg`, quality: 82 });
    for (const t of ['skin', 'wrap', 'charm', 'effect', 'finisher']) {
      await pg.click(`.cz-tab[data-tab=${t}]`); await sleep(t === 'wrap' ? 3500 : 2200);
      await pg.screenshot({ path: `${OUT}/${tag}_${t}.jpg`, quality: 82 });
      if (t === 'wrap') {
        await pg.hover('.cz-tile[data-k=gold]'); await sleep(900);
        await pg.screenshot({ path: `${OUT}/${tag}_wrap_hover.jpg`, quality: 82 });
        await pg.fill('#czSearch', 'camo'); await sleep(1500);
        await pg.screenshot({ path: `${OUT}/${tag}_wrap_search.jpg`, quality: 82 });
        console.log(tag, 'search camo ->', await pg.textContent('#czN'));
        await pg.fill('#czSearch', 'stuff'); await sleep(400); // tooltip text: "comes off the gun" etc.
        await pg.fill('#czSearch', '');
      }
      if (t === 'skin') { // the sniper: the achievement-locked Golden Sniper and its hover requirement
        await pg.click('.cz-row[data-id=sniper]'); await sleep(1500);
        await pg.hover('.cz-tile[data-k=sniper_golden]'); await sleep(1200);
        await pg.screenshot({ path: `${OUT}/${tag}_skin_sniper_royalty.jpg`, quality: 82 });
        console.log(tag, 'royalty hover:', (await pg.textContent('#czHover')).slice(0, 160));
        await pg.click('.cz-row[data-id=ar]'); await sleep(800);
      }
    }
    await ctx.close();
  }
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
