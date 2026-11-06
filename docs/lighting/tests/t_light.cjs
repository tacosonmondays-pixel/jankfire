// lighting checks: settings select, forest flashlight shadow on Too HD, zombies power switch dims the fill, night vision
require(process.env.PWLOCK || '/dev/null'); // pwlock.cjs from claude/handoff:handoff/tests caps headless browsers
const { chromium } = require('playwright');
const [port, out] = process.argv.slice(2);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 960, height: 540 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message + '\n' + e.stack));
  await pg.goto(`http://localhost:${port}/`); await sleep(800);
  await pg.click('#scr-main [data-mode="training"]'); await sleep(2500);
  const r = await pg.evaluate(async () => {
    const W = await import('/js/world.js'); const { G } = await import('/js/ctx.js'); const L = await import('/js/lighting.js');
    const res = {};
    const sun = G.scene.children.find((o) => o.isDirectionalLight);
    W.setJank(3); W.loadMap('forest'); await new Promise((r) => setTimeout(r, 1500));
    let spot = null; G.scene.traverse((o) => { if (o.isSpotLight && o.userData.mine) spot = o; });
    res.forestHD = { level: L.shadowLevel(), spotShadow: spot && spot.castShadow };
    W.setJank(2); res.forestMid = { level: L.shadowLevel(), spotShadow: spot && spot.castShadow };
    L.setShadowPref('off'); res.prefOff = { level: L.shadowLevel(), enabled: G.renderer.shadowMap.enabled, sunCast: sun.castShadow };
    L.setShadowPref('high'); res.prefHigh = { level: L.shadowLevel(), type: G.renderer.shadowMap.type, size: sun.shadow.mapSize.x, spotShadow: spot && spot.castShadow };
    L.setShadowPref('auto'); W.setJank(0); res.potato = { level: L.shadowLevel(), enabled: G.renderer.shadowMap.enabled };
    W.setJank(3);
    // the mall: the power is off at first (zombies.js dims hemi + sun), our fill light follows the sun
    W.loadMap('deadmall'); const { zmSetup } = await import('/js/zombies.js'); zmSetup('deadmall');
    await new Promise((r) => setTimeout(r, 800));
    const fill = G.scene.children.filter((o) => o.isDirectionalLight)[1];
    res.mallOff = { sun: +sun.intensity.toFixed(2), fill: +fill.intensity.toFixed(3) };
    W.loadMap('suburb'); zmSetup('suburb'); await new Promise((r) => setTimeout(r, 800));
    res.suburb = { sun: +sun.intensity.toFixed(2), fill: +fill.intensity.toFixed(3), info: L.lightInfo() };
    return res;
  });
  // the settings screen has the new select
  r.settingsSelect = await pg.evaluate(() => [...document.querySelectorAll('#shadows option')].map((o) => o.value));
  console.log(JSON.stringify(r, null, 1));
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
