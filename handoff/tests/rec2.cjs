require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs');
// wrecking ball + backrooms walk + entity, graphics Too HD. usage: node rec2.cjs <port> <outDir>
const { chromium } = require('playwright');
const fs = require('fs');
const [port, out] = process.argv.slice(2);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const set = (lo, extra) => JSON.stringify({ name: 'JANKFIRE', killcam: false, jank: 3, loadout: { ...lo, streaks: ['wreckingball', 'moonboots', 'satellite'] }, ...extra });
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const marks = {};
  const rec = async (name, fn) => {
    const t0 = Date.now();
    const ctx = await b.newContext({ viewport: { width: 960, height: 540 }, recordVideo: { dir: out + '/raw', size: { width: 960, height: 540 } } });
    const pg = await ctx.newPage(); const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
    const mark = (k) => { marks[k] = (Date.now() - t0) / 1000; };
    try { await fn(pg, mark); } catch (e) { errs.push('FAIL ' + e.message.slice(0, 160)); }
    const v = pg.video(); await ctx.close();
    if (v) try { fs.renameSync(await v.path(), `${out}/raw/${name}.webm`); } catch {}
    console.log(name, JSON.stringify(errs));
  };
  await rec('wrecking_ball', async (pg, mark) => {
    await pg.addInitScript((s) => localStorage.setItem('jankfire', s), set({ primary: 'ar', secondary: 'marbles', melee: 'knife', item: 'frag' }));
    await pg.goto(`http://localhost:${port}/`); await sleep(700);
    await pg.click('#scr-main [data-mode="training"]'); await sleep(2200);
    await pg.evaluate(async () => {
      const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js');
      const t = [...G.remotes.values()].filter((r) => r.alive && /Dummy/.test(r.name || ''))[0];
      const tp = t.pos.slice(), p = [tp[0], tp[1], tp[2] + 1.6];
      window.__hold = setInterval(() => { ME.pos = p.slice(); ME.vel = [0, 0, 0]; const e = [p[0], p[1] + 1.6, p[2]], to = [tp[0], tp[1] + 1.1, tp[2]]; const v = to.map((x, i) => x - e[i]), L = Math.hypot(...v); ME.yaw = Math.atan2(-v[0], -v[2]); ME.pitch = Math.asin(v[1] / L); }, 5);
    });
    await pg.keyboard.press('Digit2'); await sleep(1200);
    await pg.evaluate(async () => { const w = await import('/js/weapons.js'); w.fireDown(); w.fireUp(); });
    await sleep(1200);
    await pg.evaluate(async () => { clearInterval(window.__hold); const { ME } = await import('/js/player.js'); ME.pitch = -0.15; });
    mark('wb'); for (const k of ['Digit5', 'Digit6', 'Digit7']) { await pg.keyboard.press(k); await sleep(250); }
    await sleep(800);
    await pg.keyboard.down('KeyW'); await sleep(2500);
    await pg.keyboard.press('Space'); await sleep(450); await pg.keyboard.press('Space'); await sleep(500);
    await pg.keyboard.press('KeyC'); await sleep(1500);
    await pg.evaluate(async () => { const { ME } = await import('/js/player.js'); ME.yaw += 2.2; });
    await sleep(2200); await pg.keyboard.press('Space'); await sleep(600); await pg.keyboard.press('KeyC'); await sleep(2200);
    await pg.keyboard.up('KeyW');
  });
  await rec('backrooms', async (pg, mark) => {
    await pg.addInitScript((s) => localStorage.setItem('jankfire', s), set({ primary: 'ar', secondary: 'revolver', melee: 'knife', item: 'frag' }));
    await pg.goto(`http://localhost:${port}/`); await sleep(700);
    await pg.click('#scr-main [data-go="setup"]'); await sleep(500);
    await pg.selectOption('#setupMap', 'backrooms');
    await pg.evaluate(() => { const s = document.getElementById('setupBots'); s.value = '1'; s.dispatchEvent(new Event('input')); });
    await pg.click('#setupGo'); await sleep(5000);
    mark('walk');
    await pg.evaluate(async () => { const { ME } = await import('/js/player.js'); ME.pos = [0, 0.2, 24]; ME.vel = [0, 0, 0]; ME.yaw = 0; ME.pitch = 0.08; window.__turn = setInterval(() => { ME.yaw += 0.0035; }, 16); });
    await pg.keyboard.down('KeyW'); await sleep(9000); await pg.keyboard.up('KeyW');
    await pg.evaluate(() => clearInterval(window.__turn));
    mark('entity');
    await pg.evaluate(async () => { const m = await import('/js/backrooms.js'); m.summonEntity(); });
    await sleep(6500);
  });
  fs.writeFileSync(out + '/marks.json', JSON.stringify(marks));
  await b.close();
})();
