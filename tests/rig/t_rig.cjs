// overdrive rig, end to end in training: it comes on (key 7), the frame replaces your guns, a charged punch at a dummy
// lands (the server says 'hit'), block, missiles (salvo + explosions), quickhack attempt, a leap + landing, then it
// runs out and the gun comes back. server: JF_RIG_DUR=14. usage: node t_rig.cjs <outDir>
require(__dirname + '/pwlock.cjs');
const { chromium } = require('playwright');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const PORT = process.env.PORT || 3000, OUT = process.argv[2] || '.';
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1000, height: 600 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message + '\n' + e.stack));
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ name: 'rigtest', killcam: false, loadout: { primary: 'ar', secondary: 'cig', melee: 'bread', item: 'frag', streaks: ['overdrive', 'moonboots', 'scythe'] } })));
  await pg.goto(`http://localhost:${PORT}/`); await sleep(600);
  await pg.click('[data-mode="training"]'); await sleep(2500);
  await pg.mouse.click(500, 300);
  await pg.evaluate(async () => { const { net } = await import('/js/net.js'); window.__ev = []; net.ws.addEventListener('message', (e) => { try { const m = JSON.parse(e.data); if (m.t === 'rig') window.__ev.push(m.k); } catch {} }); /* net.on would replace the game handler */ });
  const st = () => pg.evaluate(async () => { const { RS } = await import('/js/rig.js'); const { ME } = await import('/js/player.js'); const { armsObj } = await import('/js/rigarms.js'); const a = armsObj(); const p = a && a.R.root.position;
    return { on: RS.on, sh: RS.shield, arms: !!(a && a.grp.visible), armsOk: !p || (Math.abs(p.x) < 2 && Math.abs(p.y) < 2), hud: getComputedStyle(document.getElementById('rigHud') || document.body).display, eye: +ME.eyeH.toFixed(2), ev: window.__ev.join(',') }; });
  // stand 6 m in front of the nearest dummy, looking at it
  const aim = (back) => pg.evaluate(async (back) => { const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js');
    const t = [...G.remotes.values()].filter((r) => r.alive).sort((a, c) => Math.hypot(a.pos[0] - ME.pos[0], a.pos[2] - ME.pos[2]) - Math.hypot(c.pos[0] - ME.pos[0], c.pos[2] - ME.pos[2]))[0];
    if (!t) return false;
    ME.pos[0] = t.pos[0]; ME.pos[1] = t.pos[1] + 0.05; ME.pos[2] = t.pos[2] + back; ME.vel[0] = ME.vel[1] = ME.vel[2] = 0;
    ME.yaw = 0; ME.pitch = -0.05; return true; }, back);
  await pg.keyboard.press('Digit7'); await sleep(1500);
  const s1 = await st(); console.log('on', JSON.stringify(s1));
  await aim(6); await sleep(400); await aim(6);
  await pg.mouse.down(); await sleep(900); await aim(6); await pg.mouse.up(); await sleep(900);
  await pg.screenshot({ path: OUT + '/rig_punch.png' });
  await pg.mouse.down({ button: 'right' }); await sleep(500); await pg.mouse.up({ button: 'right' });
  await aim(14); await pg.keyboard.press('KeyG'); await sleep(2500);
  await aim(14); await pg.keyboard.press('KeyE'); await sleep(400);
  await pg.keyboard.down('Space'); await sleep(900); await pg.keyboard.up('Space'); await sleep(2200);
  const s2 = await st(); console.log('mid', JSON.stringify(s2));
  await sleep(9000);
  const s3 = await st(); console.log('after', JSON.stringify(s3));
  const ev = s3.ev.split(','), has = (k) => ev.includes(k);
  const bad = [];
  if (!s1.on || !s1.arms || s1.hud !== 'block' || s1.eye < 1.9) bad.push('did not come on properly');
  if (!s2.armsOk) bad.push('arms flew off screen');
  for (const k of ['on', 'punch', 'hit', 'miss', 'boom', 'land', 'off']) if (!has(k)) bad.push('no ' + k + ' event');
  if (s3.on || s3.arms) bad.push('did not run out');
  if (bad.length) console.log('FAIL: ' + bad.join('; '));
  console.log(errs.join('\n') || (bad.length ? '' : 'no errors'));
  await b.close();
  process.exit(bad.length || errs.length ? 1 : 0);
})();
