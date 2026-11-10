// playwright e2e (boss fights in the combat referee). run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_boss.cjs
// story on the test lot: Mr. Overtime's first fight, staged one beat at a time (?storydev=1: bossdev calm / want): he
// spawns, you shoot the plate, he staples and slams, the plate comes off, the heart crits, the coffee break, punching
// in, the grab and the fan, and the end. screenshots land in $SP/shots (b*.png). slow under software GL: ~20 min
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const PORT = process.env.PORT || 3311, OUT = process.env.SP + '/shots';
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const ctx = await b.newContext({ viewport: { width: 960, height: 540 } });
  const pg = await ctx.newPage();
  const errs = [];
  pg.on('crash', () => console.log('PAGE CRASHED'));
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message + ' ' + (e.stack || '').split('\n')[1]));
  pg.on('console', (m) => { if (m.type() === 'error' || /boss|story combat|ot listener/i.test(m.text())) errs.push(m.type() + ': ' + m.text()); });
  await pg.addInitScript(() => { localStorage.setItem('jankfire', JSON.stringify({ name: 'ref', jank: 3, fov: 70, loadout: { primary: 'ar', secondary: 'pistol', melee: 'knife', item: 'frag' } })); localStorage.setItem('jf_giftseen_all', '1'); localStorage.removeItem('jfStorySaves'); window.__ev = []; });
  await pg.goto(`http://localhost:${PORT}/?story=1&storydev=1&storytest=1`); await sleep(2500);
  await pg.click('#storyBtn', { force: true }); await sleep(900); await pg.click('#storyPick .st-btn.yellow', { force: true }); await sleep(5000);
  const ev = (f, a) => pg.evaluate(f, a);
  const skip = async () => { for (let i = 0; i < 20; i++) { const l = await ev(async () => { const boot = await import('/js/story/boot.js'); if (!boot.locked()) return false; const sc = await import('/js/story/scene.js'), tk = await import('/js/story/talk.js'); if (sc.playing()) sc.skipScene(); if (tk.talking && tk.talking() && tk.endTalk) tk.endTalk(); return true; }); if (!l) return; await sleep(700); } };
  await skip();
  await ev(async () => { const { G } = await import('/js/ctx.js'); G.story.on('combat', (m) => { if (m.ev) window.__ev.push(m.ev); }); });
  await sleep(3000);
  const stand = (p, yaw, pitch = 0) => ev(async ([p, yaw, pitch]) => { const { ME } = await import('/js/player.js'); ME.pos = p; ME.vel = [0, 0, 0]; ME.yaw = yaw; ME.pitch = pitch; }, [p, yaw, pitch]);
  const send = (k, o) => ev(async ([k, o]) => { const { G } = await import('/js/ctx.js'); G.story.send(k, o); }, [k, o]);
  await stand([-15, 0.1, 22], 0); await sleep(800);
  await ev(async () => { const { actors } = await import('/js/story/actors.js'); setInterval(() => { for (const a of actors.values()) if (a.id !== 'overtime') a.hidden = true; }, 100); });
  await ev(async () => { const { G } = await import('/js/ctx.js'); window.JF_STORY.boss.spawn('overtime_1'); G.story.send('bossdev', { calm: true }); });
  await sleep(5000);
  const state = () => ev(async () => { const { G } = await import('/js/ctx.js'); const { actors } = await import('/js/story/actors.js'); const { ME } = await import('/js/player.js'); const a = actors.get('overtime'); const B = window.JF_STORY.boss;
    return { remotes: [...G.remotes.values()].map((r) => ({ id: r.id, p: r.pos.map((v) => +v.toFixed(1)), vis: r.ch.root.visible, hb: r.hitboxes().length })), actor: a && { p: a.pos.map((v) => +v.toFixed(1)), yaw: +a.yaw.toFixed(2), clip: a.clip && a.clip.name }, me: { p: ME.pos.map((v) => +v.toFixed(1)), hp: ME.hp }, B: { on: B.on, hp: +B.hp.toFixed(3), phase: B.phase }, bar: document.getElementById('stBossBar') && document.getElementById('stBossBar').textContent, n: window.__ev.length }; });
  // stand d metres in front of him (he faces you), looking at a height on him
  const front = (d, h = 3) => ev(async ([d, h]) => { const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js'); const r = [...G.remotes.values()][0]; if (!r) return; ME.pos = [r.pos[0] - Math.sin(r.yaw) * d, r.pos[1] + 0.1, r.pos[2] - Math.cos(r.yaw) * d]; ME.vel = [0, 0, 0]; const dx = r.pos[0] - ME.pos[0], dz = r.pos[2] - ME.pos[2], dy = r.pos[1] + h - (ME.pos[1] + 1.6); ME.yaw = Math.atan2(-dx, -dz); ME.pitch = Math.atan2(dy, Math.hypot(dx, dz)); }, [d, h]);
  const aim = (h) => ev(async (h) => { const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js'); const r = [...G.remotes.values()][0]; if (!r) return; const dx = r.pos[0] - ME.pos[0], dz = r.pos[2] - ME.pos[2], dy = r.pos[1] + h - (ME.pos[1] + 1.6); ME.yaw = Math.atan2(-dx, -dz); ME.pitch = Math.atan2(dy, Math.hypot(dx, dz)); }, h);
  const shoot = async (ms, h, shotAt, name) => { const t0 = Date.now(); let done = false; await ev(async () => (await import('/js/weapons.js')).fireDown()); while (Date.now() - t0 < ms) { await aim(h); await sleep(50); if (!done && shotAt && Date.now() - t0 > shotAt) { done = true; await pg.screenshot({ path: `${OUT}/${name}.png` }); } } await ev(async () => (await import('/js/weapons.js')).fireUp()); };
  const burst = async (name, n, gap = 250, h = 3) => { for (let i = 0; i < n; i++) { await aim(h); await pg.screenshot({ path: `${OUT}/${name}_${i}.png` }); await sleep(gap); } };
  const staged = async (name, move, waits, d, h = 3) => { for (let i = 0; i < waits.length; i++) { await front(d, h); await send('bossdev', { want: move }); await sleep(waits[i]); await aim(h); await pg.screenshot({ path: `${OUT}/${name}_${i}.png` }); await sleep(2500); } };
  const evs = () => ev(() => window.__ev);
  const dmg = (d) => send('damage', { id: 'overtime_1', dmg: d, why: 'script' });
  const log = async (tag) => console.log(tag, JSON.stringify(await state()));
  await front(7); await sleep(1200);
  await log('spawned'); await pg.screenshot({ path: `${OUT}/b1_spawn.png` });
  await shoot(4000, 3.4, 2000, 'b2_shoot_plate');
  { const parts = {}; for (const e of await evs()) if (e.type === 'hit' && e.target === 'overtime_1') parts[e.part] = (parts[e.part] || 0) + 1; console.log('hits by part', JSON.stringify(parts)); }
  await shoot(1500, 0.9);
  { const parts = {}; for (const e of await evs()) if (e.type === 'hit' && e.target === 'overtime_1') parts[e.part] = (parts[e.part] || 0) + 1; console.log('hits by part (after legs + head)', JSON.stringify(parts)); }
  await log('after shooting');
  await staged('b3_staple', 'staple', [500, 900], 7);
  await staged('b3_slam', 'slam', [900, 1400, 1800], 7);
  console.log('acts', JSON.stringify((await evs()).filter((e) => e.type === 'act' || e.type === 'fx' || (e.type === 'hit' && e.target === 'me')).map((e) => e.type + ':' + (e.clip || e.k || e.dmg))));
  await log('after attacks');
  // the plate
  await front(7, 3.3);
  for (let i = 0; i < 3; i++) { await dmg(600); await sleep(250); }
  await burst('b4_plate_off', 3, 400, 3.3);
  console.log('part events', JSON.stringify((await evs()).filter((e) => e.type === 'part')));
  await front(7, 3.4); await shoot(3500, 3.4, 2000, 'b5_heart');
  { const c = (await evs()).filter((e) => e.type === 'hit' && e.crit); console.log('crits', c.length, JSON.stringify(c.slice(0, 1))); }
  // half HP: the coffee break
  await front(7, 2.6);
  for (let i = 0; i < 4; i++) { await dmg(900); await sleep(150); }
  await burst('b6_coffee', 4, 900, 2.6); await log('coffee');
  await skip(); await sleep(2000); await front(7, 2.35);
  await shoot(3500, 2.35, 2000, 'b7_coffee_crit'); await log('coffee shot');
  console.log('phases', JSON.stringify((await evs()).filter((e) => e.type === 'phase')));
  for (let i = 0; i < 2; i++) { await dmg(900); await sleep(150); }
  await burst('b8_punching_in', 3, 900); await log('p2');
  await skip(); await sleep(2500);
  await staged('b9_punchin', 'punchin', [700, 1300], 5);
  await staged('b9_fan', 'fan', [1200, 1800], 7);
  console.log('acts', JSON.stringify((await evs()).filter((e) => e.type === 'act').map((e) => e.clip)), 'hits on me', (await evs()).filter((e) => e.type === 'hit' && e.target === 'me').map((e) => e.dmg + '/' + e.weapon).join(' '));
  // the end
  await front(7, 2.5);
  for (let i = 0; i < 8; i++) { await dmg(900); await sleep(120); }
  await burst('b10_end', 3, 900, 2.2);
  console.log('kill', JSON.stringify((await evs()).filter((e) => e.type === 'kill')));
  await log('end');
  console.log('ERRORS', errs.length, errs.slice(0, 12).join('\n'));
  await ctx.close(); await b.close();
})().catch((e) => { console.error('FAILED', e); process.exit(1); });
