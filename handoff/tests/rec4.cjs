require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs');
// training: streak is always in the tray -> press 5 and show it off. usage: node rec4.cjs <port> <outDir> <wreckingball|overdrive>
const { chromium } = require('playwright');
const fs = require('fs');
const [port, out, kind] = process.argv.slice(2);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const t0 = Date.now();
  const ctx = await b.newContext({ viewport: { width: 960, height: 540 }, recordVideo: { dir: out + '/raw', size: { width: 960, height: 540 } } });
  const pg = await ctx.newPage(); const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  let mark = 0, info = null;
  try {
    await pg.addInitScript((k) => localStorage.setItem('jankfire', JSON.stringify({ name: 'JANKFIRE', killcam: false, jank: 3, loadout: { primary: 'ar', secondary: 'marbles', melee: 'knife', item: 'frag', streaks: [k, 'moonboots', 'satellite'] } })), kind);
    await pg.goto(`http://localhost:${port}/`); await sleep(700);
    await pg.click('#scr-main [data-mode="training"]'); await sleep(3500);
    await pg.evaluate(async () => { const { ME } = await import('/js/player.js'); ME.pitch = -0.1; });
    mark = (Date.now() - t0) / 1000;
    await pg.keyboard.press('Digit6'); await sleep(1800);
    info = await pg.evaluate(async () => { const { G } = await import('/js/ctx.js'); return { pocket: G.pocket }; });
    const turn = (a) => pg.evaluate(async (a) => { const { ME } = await import('/js/player.js'); ME.yaw += a; }, a);
    if (kind === 'wreckingball') {
      await pg.keyboard.down('KeyW'); await sleep(2500); await turn(0.9); await sleep(1500);
      await pg.keyboard.press('Space'); await sleep(500); await pg.keyboard.press('Space'); await sleep(400); await pg.keyboard.press('KeyC'); await sleep(1800);
      await turn(-1.8); await sleep(1600); await pg.keyboard.press('Space'); await sleep(600); await pg.keyboard.press('KeyC'); await sleep(2200);
      await pg.keyboard.up('KeyW');
    } else {
      await pg.keyboard.down('KeyW'); await sleep(2500); await turn(1.2); await sleep(1200); await pg.keyboard.up('KeyW');
      await pg.mouse.down(); await sleep(1200); await pg.mouse.up(); await sleep(1300);
      await pg.mouse.down({ button: 'right' }); await sleep(1300); await pg.mouse.up({ button: 'right' }); await sleep(400);
      await pg.keyboard.press('KeyG'); await sleep(2400);
      await pg.keyboard.down('Space'); await sleep(1100); await pg.keyboard.up('Space'); await sleep(2600);
      await pg.keyboard.down('KeyW'); await turn(-2); await sleep(2000); await pg.keyboard.up('KeyW');
    }
  } catch (e) { errs.push('FAIL ' + e.message.slice(0, 160)); }
  const v = pg.video(); await ctx.close();
  if (v) try { fs.renameSync(await v.path(), `${out}/raw/${kind}.webm`); } catch {}
  fs.writeFileSync(`${out}/mark_${kind}.txt`, String(Math.max(0, mark - 0.5)));
  console.log(kind, JSON.stringify(info), JSON.stringify(errs.slice(0, 3)));
  await b.close();
})();
