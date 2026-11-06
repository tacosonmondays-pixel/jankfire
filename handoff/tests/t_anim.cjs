require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs'); // at most 2 headless browsers machine-wide
// training mode: knife slash/stab, card throw, shotgun pump, draw anims, speed lines. screenshots mid-animation.
const { chromium } = require('playwright');
const out = process.argv[2];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 800, height: 500 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message + '\n' + e.stack));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ name: 'animtest', loadout: { primary: 'shotgun', secondary: 'cards', melee: 'knife' } })));
  await pg.goto('http://localhost:3000/');
  await pg.waitForTimeout(500);
  await pg.click('#scr-main [data-mode="training"]');
  await pg.waitForTimeout(1500);
  const W = (code) => pg.evaluate(code);
  const shot = (n) => pg.screenshot({ path: `${out}/an_${n}.png` });
  // shotgun: fire, flash frame, then pump
  await W(async () => { const { ME } = await import('/js/player.js'); ME.pitch = 0.6; });
  await sleep(50);
  await W(async () => { const w = await import('/js/weapons.js'); w.fireDown(); w.fireUp(); });
  await sleep(16); await shot('shotgun_flash');
  console.log('flash', await W(async () => { const { W } = await import('/js/weapons.js'); return W.flashT; }));
  await sleep(300); await shot('shotgun_pump');
  // knife: draw, slash 1, slash 2, heavy
  await W(async () => { const { ME } = await import('/js/player.js'); ME.pitch = 0; });
  await pg.keyboard.press('Digit3'); await sleep(120); await shot('knife_draw');
  console.log('alive before knife', await W(async () => (await import('/js/player.js')).ME.alive));
  await sleep(500);
  const st = await W(async () => { const { W } = await import('/js/weapons.js'); return W.anim && W.anim.name; });
  console.log('anim after draw', st);
  await W(async () => { const w = await import('/js/weapons.js'); w.fireDown(); w.fireUp(); });
  await sleep(120); await shot('knife_slash1');
  await sleep(450);
  await W(async () => { const w = await import('/js/weapons.js'); w.fireDown(); w.fireUp(); });
  await sleep(120); await shot('knife_slash2');
  await sleep(600);
  const hv = await W(async () => { const w = await import('/js/weapons.js'); const r = w.heavyAttack(); return [r, w.W.anim && w.W.anim.name]; });
  console.log('heavy', JSON.stringify(hv));
  await sleep(180); await shot('knife_windup');
  await sleep(110); await shot('knife_thrust');
  await sleep(900);
  // cards: throw
  await pg.keyboard.press('Digit2'); await sleep(450);
  const hand = await W(async () => (await import('/js/ctx.js')).G.hand);
  console.log('hand', JSON.stringify(hand));
  await W(async () => { const w = await import('/js/weapons.js'); w.fireDown(); w.fireUp(); return w.W.anim && w.W.anim.name; }).then((n) => console.log('card anim', n));
  await sleep(60); await shot('card_windup');
  await sleep(110); await shot('card_flick');
  await sleep(120); await shot('card_fly');
  // speed lines: fake fast velocity
  await W(async () => { const { ME } = await import('/js/player.js'); const p0 = ME.pos.slice(); window.__sp = setInterval(() => { ME.pos = [p0[0], p0[1] + 6, p0[2]]; ME.vel = [8, 1, -90]; ME.yaw = 0; ME.pitch = 0; }, 4); });
  await sleep(200); await shot('speedlines');
  console.log('speedlines px', await W(() => { const c = document.getElementById('speedLinesCv'); const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let a = 0; for (let i = 3; i < d.length; i += 4) a += d[i]; return [c.width, c.height, a, getComputedStyle(c).display, c.getBoundingClientRect().width]; }));
  console.log('speed', await W(async () => { const { ME } = await import('/js/player.js'); return [ME.alive, Math.hypot(...ME.vel).toFixed(1)]; }));
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
