// usage: node shots.cjs <outdir> <port> <jank> [maps,comma]
require(process.env.PWLOCK || '/dev/null'); // pwlock.cjs from claude/handoff:handoff/tests caps headless browsers
const { chromium } = require('playwright');
const [out, port, jank, only] = process.argv.slice(2);
const MAPS = (only || 'crate,platform,rooftop,suburb,suburb_sd,warehouse,warehouse_sd,desert,desert_sd,bazaar,bazaar_sd,islands,skyline,backrooms,forest,deadmall,jankburg').split(',');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 960, height: 540 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message + '\n' + e.stack));
  await pg.goto(`http://localhost:${port}/`); await pg.waitForTimeout(800);
  await pg.click('#scr-main [data-mode="training"]'); await pg.waitForTimeout(2500);
  if (!process.env.HUD) await pg.addStyleTag({ content: 'body > *:not(#game):not(canvas) { visibility: hidden !important; }' });
  for (const id of MAPS) {
    await pg.evaluate(async ([id, jank]) => {
      const W = await import('/js/world.js'); const { MAPS } = await import('/shared/map.js'); const { ME } = await import('/js/player.js');
      W.setJank(Number(jank));
      W.loadMap(id);
      const m = MAPS[id], s = m.spawns[0];
      let cx = 0, cz = 0; for (const p of m.spawns) { cx += p[0] / m.spawns.length; cz += p[2] / m.spawns.length; }
      const ind = m.sealed || m.zm;
      // look away from the sun (shadows fall towards you... away), from up high outdoors
      const sx = id === 'islands' ? 170 : m.night ? -260 : 300, sz = id === 'islands' ? -230 : -420;
      const dx = ind ? cx - s[0] : -sx, dz = ind ? cz - s[2] : -sz, yaw = Math.atan2(-dx, -dz) + (ind ? 0 : 0.5);
      const up = ind ? 0.6 : Math.min(9, m.ceiling != null ? m.ceiling - s[1] - 1.5 : 9);
      clearInterval(window.__fly);
      const p = [s[0], s[1] + up, s[2]];
      window.__fly = setInterval(() => { ME.pos = p.slice(); ME.vel = [0, 0, 0]; ME.yaw = (dx || dz) ? yaw : 0; ME.pitch = ind ? -0.15 : -0.45; }, 5);
    }, [id, jank]);
    await pg.waitForTimeout(2500);
    await pg.screenshot({ path: `${out}/${id}.png` });
    if (process.env.INFO) console.log(id, JSON.stringify(await pg.evaluate(async () => { try { const L = await import('/js/lighting.js'); return L.lightInfo(); } catch (e) { return 'n/a'; } })));
  }
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
