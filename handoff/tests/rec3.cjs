require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs');
// earn a killstreak on a bot (bots room), then show it off. usage: node rec3.cjs <port> <outDir> <wreckingball|overdrive>
const { chromium } = require('playwright');
const fs = require('fs');
const [port, out, kind] = process.argv.slice(2);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const t0 = Date.now();
  const ctx = await b.newContext({ viewport: { width: 960, height: 540 }, recordVideo: { dir: out + '/raw', size: { width: 960, height: 540 } } });
  const pg = await ctx.newPage(); const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  let mark = 0;
  try {
    await pg.addInitScript((k) => localStorage.setItem('jankfire', JSON.stringify({ name: 'JANKFIRE', killcam: false, jank: 3, loadout: { primary: 'ar', secondary: 'marbles', melee: 'knife', item: 'frag', streaks: [k, 'moonboots', 'satellite'] } })), kind);
    await pg.goto(`http://localhost:${port}/`); await sleep(700);
    await pg.click('#scr-main [data-go="setup"]'); await sleep(500);
    await pg.evaluate(() => { const s = document.getElementById('setupBots'); s.value = '1'; s.dispatchEvent(new Event('input')); });
    await pg.click('#setupGo'); await sleep(4000);
    // glue ourselves 1.5 m behind the bot, aimed at its chest, and pop it with the marble shotgun
    await pg.evaluate(async () => {
      const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js');
      window.__hold = setInterval(() => {
        const t = [...G.remotes.values()].find((r) => r.alive && r.bot); if (!t) return;
        const p = [t.pos[0], t.pos[1], t.pos[2] + 1.5]; ME.pos = p; ME.vel = [0, 0, 0];
        const e = [p[0], p[1] + 1.6, p[2]], to = [t.pos[0], t.pos[1] + 1.1, t.pos[2]];
        const v = to.map((x, i) => x - e[i]), L = Math.hypot(...v); ME.yaw = Math.atan2(-v[0], -v[2]); ME.pitch = Math.asin(v[1] / L);
      }, 5);
    });
    await pg.keyboard.press('Digit2'); await sleep(1200);
    for (let i = 0; i < 2; i++) { await pg.evaluate(async () => { const w = await import('/js/weapons.js'); w.fireDown(); w.fireUp(); }); await sleep(1300); }
    await pg.evaluate(async () => { clearInterval(window.__hold); const { ME } = await import('/js/player.js'); ME.pitch = -0.1; });
    await sleep(600);
    mark = (Date.now() - t0) / 1000;
    for (const k of ['Digit5', 'Digit6', 'Digit7']) { await pg.keyboard.press(k); await sleep(300); }
    await sleep(1500);
    const turn = (a) => pg.evaluate(async (a) => { const { ME } = await import('/js/player.js'); ME.yaw += a; }, a);
    if (kind === 'wreckingball') {
      await pg.keyboard.down('KeyW'); await sleep(2500); await turn(1.2); await sleep(1500);
      await pg.keyboard.press('Space'); await sleep(500); await pg.keyboard.press('Space'); await sleep(400); await pg.keyboard.press('KeyC'); await sleep(1800);
      await turn(-2); await sleep(1500); await pg.keyboard.press('Space'); await sleep(600); await pg.keyboard.press('KeyC'); await sleep(2000);
      await pg.keyboard.up('KeyW');
    } else {
      await pg.keyboard.down('KeyW'); await sleep(2500); await turn(1.4); await sleep(1200); await pg.keyboard.up('KeyW');
      await pg.mouse.down(); await sleep(1200); await pg.mouse.up(); await sleep(1200); // charged rocket punch
      await pg.mouse.down({ button: 'right' }); await sleep(1300); await pg.mouse.up({ button: 'right' }); await sleep(400); // block
      await pg.keyboard.press('KeyG'); await sleep(2200); // homing missiles
      await pg.keyboard.down('Space'); await sleep(1100); await pg.keyboard.up('Space'); await sleep(2500); // charged leap
      await pg.keyboard.down('KeyW'); await turn(-2); await sleep(2000); await pg.keyboard.up('KeyW');
    }
  } catch (e) { errs.push('FAIL ' + e.message.slice(0, 160)); }
  const v = pg.video(); await ctx.close();
  if (v) try { fs.renameSync(await v.path(), `${out}/raw/${kind}.webm`); } catch {}
  fs.writeFileSync(`${out}/mark_${kind}.txt`, String(Math.max(0, mark - 1)));
  console.log(kind, JSON.stringify(errs.slice(0, 3)));
  await b.close();
})();
