require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs'); // at most 2 headless browsers machine-wide
// bots room soak: bots carry the new guns (marbles from other players + replays), plus skin previews of the new guns
const { chromium } = require('playwright');
const [port, out] = process.argv.slice(2);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 960, height: 600 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message + '\n' + e.stack));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ name: 'soak', killcam: true, loadout: { primary: 'redline', secondary: 'marbles', melee: 'katana', item: 'medkit' } })));
  await pg.goto(`http://localhost:${port}/`); await sleep(500);
  // skin previews
  for (const [w, id] of [['marbles', 'default'], ['marbles', 'marbles_gumball'], ['redline', 'default'], ['redline', 'redline_hotrod']]) {
    await pg.evaluate(async ([w, id]) => { const { showPreview } = await import('/js/preview.js'); showPreview(w, ['default', 'none', 'none', id]); }, [w, id]);
    await pg.click('#scr-main [data-go="cosmetics"]').catch(() => {}); await sleep(250);
    await pg.evaluate(async ([w, id]) => { const { showPreview } = await import('/js/preview.js'); showPreview(w, ['default', 'none', 'none', id]); }, [w, id]);
    await sleep(600);
    await pg.locator('#preview').screenshot({ path: `${out}/skin_${w}_${id}.png` }).catch((e) => errs.push(e.message));
    await pg.goto(`http://localhost:${port}/`); await sleep(400);
  }
  await pg.click('#scr-main [data-go="setup"]');
  await pg.locator('#setupBots').fill('7');
  await pg.click('#setupGo'); await sleep(2000);
  // make every bot carry a marble shotgun or a redline
  const shots = await pg.evaluate(async () => {
    const { net } = await import('/js/net.js');
    window.__n = { marbles: 0, redline: 0, kills: 0 };
    net.ws.addEventListener('message', (e) => { const m = JSON.parse(e.data); if (m.t === 'fx' && m.k === 'shot' && window.__n[m.w] !== undefined) window.__n[m.w]++; if (m.t === 'kill') window.__n.kills++; });
    return true;
  });
  for (let i = 0; i < 6; i++) { await sleep(5000); await pg.screenshot({ path: `${out}/soak_${i}.png` }); }
  console.log('remote shots seen', JSON.stringify(await pg.evaluate(() => window.__n)));
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
