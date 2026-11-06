// playwright e2e (WP5). run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_wp5.cjs
// clinic buy + install, Spring Knees jump height + fold, Pigeon Eyes x-ray + flip, Second Stomach eat, HYPE -> Moon Boots,
// Punch-Clock free mag + low-HP slow, save/load keeps the body
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const PORT = process.env.PORT || 3311, OUT = process.env.SP + '/shots';
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message + ' ' + (e.stack || '').split('\n')[1]));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.addInitScript(() => { localStorage.setItem('jankfire', JSON.stringify({ name: 'wp5', jank: 3, loadout: { primary: 'ar', secondary: 'pistol', melee: 'knife', item: 'frag' } })); if (!sessionStorage.getItem('w5')) { sessionStorage.setItem('w5', 1); localStorage.removeItem('jfStorySaves'); } });
  const start = async () => { await pg.goto(`http://localhost:${PORT}/?story=1&storydev=1&storytest=1`); await sleep(1500); await pg.click('#storyBtn', { force: true }); await sleep(700); await pg.click('#storyPick .st-btn.yellow', { force: true }); await sleep(3500); };
  await start();
  const ev = (f, a) => pg.evaluate(f, a);
  const tp = (p, yaw = 0, pitch = 0) => ev(async ([p, yaw, pitch]) => { const { ME } = await import('/js/player.js'); ME.pos = p.slice(); ME.vel = [0, 0, 0]; ME.yaw = yaw; ME.pitch = pitch; }, [p, yaw, pitch]);
  const key = async (k, ms = 80) => { await pg.keyboard.down(k); await sleep(ms); await pg.keyboard.up(k); await sleep(300); };
  const jumpH = async () => ev(async () => { // take-off speed from the real player step (height goes with speed squared)
    const { ME, stepPlayer } = await import('/js/player.js');
    ME.pos = [-20, 0.1, 10]; ME.vel = [0, 0, 0]; ME.onGround = true; ME.groundTicks = 10; ME.jumpBuf = 0;
    stepPlayer(1 / 120, { jump: true, jumpPressed: true }, performance.now());
    return +(ME.vel[1] * ME.vel[1]).toFixed(3);
  });
  const h0 = await jumpH();
  // the clinic: F at the chair, buy Spring Knees + Pigeon Eyes, install both
  await tp([-5.1, 0.1, -14], 1.57, -0.2); await sleep(400);
  const hint = await ev(() => document.querySelector('.st-hint').textContent);
  await key('KeyF'); await sleep(600);
  const open = await ev(() => !document.getElementById('storyClinic').classList.contains('hidden'));
  console.log('hint', hint, 'clinic open', open);
  await pg.screenshot({ path: `${OUT}/w5_clinic0.png` });
  const buy = async (id) => { await pg.click(`#storyClinic .st-crow:has(.st-cname2:text-is("${id}")) .st-btn`); await sleep(500); };
  await buy('SPRING KNEES'); await buy('PIGEON EYES');
  for (let i = 0; i < 2; i++) { await pg.click('#storyClinic .st-btn.yellow'); await sleep(600); }
  await sleep(800);
  await pg.screenshot({ path: `${OUT}/w5_clinic1.png` });
  const body = await ev(async () => { const { B } = await import('/js/story/body.js'); return { slots: B.body.slots, coupons: B.coupons, drift: B.drift, budget: B.budget }; });
  console.log('after installs', JSON.stringify(body), 'msg:', await ev(() => document.querySelector('#storyClinic .st-info').textContent));
  await pg.click('#storyClinic .st-bagtop .st-btn'); await sleep(400);
  const h1 = await jumpH();
  console.log('jump v^2 (height)', h0, '->', h1, 'ratio', (h1 / h0).toFixed(2), '(want 1.8)');
  // the wrong knee: force a fold (Math.random low) on a landing
  await ev(() => { window.__rnd = Math.random; Math.random = () => 0.001; });
  await tp([-20, 6, 10]); await sleep(2200);
  const fold = await ev(async () => { const { bodyDebug } = await import('/js/story/body.js'); return bodyDebug().folds || 0; });
  await ev(() => { Math.random = window.__rnd; });
  console.log('knee folded on landing', fold);
  // pigeon eyes: a beam 25 m away behind the crates draws through walls; force the back-eye flip
  await tp([0, 0.1, 8], 0, 0); await sleep(600);
  const xr = await ev(async () => { const { G } = await import('/js/ctx.js'); let n = 0, all = 0; G.scene.traverse((o) => { if (o.material && o.material.blending === 2) { all++; if (o.material.depthTest === false) n++; } }); return { xray: n, beams: all }; });
  await ev(async () => { const { bodyDebug } = await import('/js/story/body.js'); bodyDebug().flipT = 999; }); await sleep(120);
  const flip = await ev(async () => { const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js'); return +(Math.abs(((G.camera.rotation.y - ME.yaw) % (2 * Math.PI)) - Math.PI)).toFixed(2); });
  console.log('pigeon eyes', JSON.stringify(xr), 'flip |camYaw - yaw - pi| =', flip);
  await pg.screenshot({ path: `${OUT}/w5_xray.png` });
  // Second Stomach: pick up the core from the test pile, install it, hold F on a dropped weapon
  await tp([-9, 0.1, -10]); await sleep(400); await key('KeyF');
  await tp([-5.1, 0.1, -14], 1.57); await sleep(300); await key('KeyF'); await sleep(500);
  await pg.click('#storyClinic .st-btn.yellow'); await sleep(800); await pg.click('#storyClinic .st-bagtop .st-btn'); await sleep(300);
  const gun = await ev(async () => { const { IV } = await import('/js/story/bar.js'); const { G } = await import('/js/ctx.js'); return null; });
  const target = await ev(async () => { const { nearestDrop } = await import('/js/story/bar.js'); return null; });
  // the rarity row by the north wall is all weapons: stand on the common one
  await tp([-12, 0.1, -23.2], 0, -0.6); await sleep(500);
  await ev(async () => { const { ME } = await import('/js/player.js'); const { G } = await import('/js/ctx.js'); ME.hp = 30; G.story.send('devHp', { hp: 30 }); }); await sleep(300);
  await pg.keyboard.down('KeyF'); await sleep(1300); await pg.keyboard.up('KeyF'); await sleep(600);
  const hp = await ev(async () => (await import('/js/player.js')).ME.hp);
  console.log('ate a weapon: hp 30 ->', hp);
  // HYPE: dev +60, a Moon Boots item from the test pile onto the bar, use it
  await tp([-13, 0.1, -6]); await sleep(400); await key('KeyF'); await sleep(300);
  await ev(async () => { const { G } = await import('/js/ctx.js'); const { IV } = await import('/js/story/bar.js'); G.story.send('hypeEv', { ev: 'test', n: 60 }); const it = IV.inv.bag.find((x) => x && x.b === 'moonboots'); G.story.send('inv', { op: 'bar', slot: 7, u: it.u }); });
  await sleep(500); await key('Digit8'); await sleep(500);
  const moon = await ev(async () => { const { ME } = await import('/js/player.js'); const { B } = await import('/js/story/body.js'); return { moon: ME.moonUntil > performance.now(), hype: B.hype }; });
  console.log('moon boots from HYPE', JSON.stringify(moon), '(hype 60 - 25 = 35)');
  await pg.screenshot({ path: `${OUT}/w5_hud.png` });
  // Punch-Clock: install the prime core, empty the mag with the free one ready, drop under 20 HP
  await tp([-11, 0.1, -10]); await sleep(400); await key('KeyF');
  await tp([-5.1, 0.1, -14], 1.57); await sleep(300); await key('KeyF'); await sleep(500);
  await pg.click('#storyClinic .st-btn.yellow'); await sleep(800);
  await pg.screenshot({ path: `${OUT}/w5_clinic2.png` });
  await pg.click('#storyClinic .st-bagtop .st-btn'); await sleep(300);
  await key('Digit1');
  const pc = await ev(async () => { const { W, magOf } = await import('/js/weapons.js'); const { bodyDebug } = await import('/js/story/body.js'); bodyDebug().freeT = 999; await new Promise((r) => setTimeout(r, 300)); W.ammo[W.cur] = 0; await new Promise((r) => setTimeout(r, 300)); const full = W.ammo[W.cur] === magOf(W.cur); const { ME } = await import('/js/player.js'); const { G } = await import('/js/ctx.js'); ME.hp = 15; await new Promise((r) => setTimeout(r, 300)); return { freeMag: full, reload: W.reloadId, slow: G.story.timeScale() }; });
  console.log('punch clock', JSON.stringify(pc));
  // save + reload: the body comes back
  await ev(async () => { const { ME } = await import('/js/player.js'); ME.hp = 100; });
  await pg.keyboard.press('KeyB'); await sleep(800); await pg.click('#quit', { force: true }); await sleep(1000);
  await start();
  const back = await ev(async () => { const { B } = await import('/js/story/body.js'); const { ME } = await import('/js/player.js'); return { slots: Object.keys(B.body.slots), jumpMul: +ME.jumpMul.toFixed(3), coupons: B.coupons, hype: B.hype }; });
  console.log('after reload', JSON.stringify(back));
  // the look on the mannequin: open the clinic for the preview
  await tp([-5.1, 0.1, -14], 1.57); await sleep(300); await key('KeyF'); await sleep(1200);
  await pg.screenshot({ path: `${OUT}/w5_look.png` });
  console.log('ERRORS', errs.length, errs.slice(0, 8).join('\n'));
  await b.close();
})();
