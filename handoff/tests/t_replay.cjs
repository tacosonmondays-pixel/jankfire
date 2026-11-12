require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs'); // at most 2 headless browsers machine-wide
// two players in FFA: A snipes B. checks killcam on B, kill effect, then play of the round.
const { chromium } = require('playwright');
const out = process.argv[2];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const errs = [];
  async function player(name, extra) {
    const ctx = await b.newContext({ viewport: { width: 960, height: 600 } });
    const pg = await ctx.newPage();
    pg.on('pageerror', (e) => errs.push(name + ' PAGEERR ' + e.message + '\n' + e.stack));
    pg.on('console', (m) => { if (m.type() === 'error') errs.push(name + ' ' + m.text()); });
    await pg.addInitScript((s) => localStorage.setItem('jankfire', JSON.stringify(s)), { name, ...extra });
    await pg.goto('http://localhost:3000/');
    await pg.waitForTimeout(600);
    await pg.click('#scr-main [data-mode="ffa"]');
    await pg.waitForTimeout(1500);
    return pg;
  }
  const B = await player('victim', { killcam: true, look: { color: '#4fd8ff', head: 'cowboy', face: 'shades', back: 'cape' } });
  const A = await player('killer', { kfx: 'confetti', look: { color: '#ff7a1a', head: 'party', face: 'mustache', back: 'backpack' } });
  await sleep(1500);
  const shoot = async () => A.evaluate(async () => {
    const { G } = await import('/js/ctx.js');
    const { net } = await import('/js/net.js');
    const { ME } = await import('/js/player.js');
    const t = [...G.remotes.values()].find((r) => r.name.startsWith('victim'));
    if (!t || !t.alive) return 'no target';
    const e = [ME.pos[0], ME.pos[1] + 1.6, ME.pos[2]];
    const to = [t.pos[0], t.pos[1] + 2.0, t.pos[2]];
    const d = to.map((v, i) => v - e[i]); const L = Math.hypot(...d); const dir = d.map((v) => v / L);
    ME.yaw = Math.atan2(-dir[0], -dir[2]); ME.pitch = Math.asin(dir[1]);
    await new Promise((r) => setTimeout(r, 150));
    net.send({ t: 'fire', w: 'sniper', o: e, s: [[...e, ...to]] });
    net.send({ t: 'hit', w: 'sniper', to: t.id, d: dir, n: 1, h: 1 });
    return 'shot ' + t.id + ' at ' + L.toFixed(1) + 'm';
  });
  const state = (pg) => pg.evaluate(async () => {
    const { RP } = await import('/js/replay.js');
    const { ME } = await import('/js/player.js');
    const { G } = await import('/js/ctx.js');
    return { rp: RP.mode, alive: ME.alive, pending: !!G.killcamPending, replayUI: !document.getElementById('replay').classList.contains('hidden'), roundEnd: !document.getElementById('roundEnd').classList.contains('hidden') };
  });
  // kill 1: B gets a killcam
  for (let i = 0; i < 4; i++) { console.log(await shoot()); await sleep(700); if (!(await state(B)).alive) break; }
  console.log('B right after death', JSON.stringify(await state(B)));
  await B.screenshot({ path: out + '/kc_dead.png' });
  await sleep(1800);
  console.log('B during killcam', JSON.stringify(await state(B)));
  await B.screenshot({ path: out + '/kc_play.png' });
  await sleep(1600);
  await B.screenshot({ path: out + '/kc_slow.png' });
  await sleep(3500);
  console.log('B after killcam', JSON.stringify(await state(B)));
  // kills 2 + 3 with killcam off -> round over -> play of the round
  await B.evaluate(async () => { const { net } = await import('/js/net.js'); net.send({ t: 'kc', on: false }); const { G } = await import('/js/ctx.js'); G.settings.killcam = false; });
  for (let k = 0; k < 2; k++) {
    await sleep(1600);
    for (let i = 0; i < 4; i++) { const r = await shoot(); console.log(r); await sleep(700); if (!(await state(B)).alive) break; }
    console.log('B state', JSON.stringify(await state(B)));
  }
  await sleep(2200);
  console.log('A at hl', JSON.stringify(await state(A)));
  console.log('B at hl', JSON.stringify(await state(B)));
  await A.screenshot({ path: out + '/hl_a.png' });
  await B.screenshot({ path: out + '/hl_b.png' });
  await sleep(2500);
  await A.screenshot({ path: out + '/hl_a2.png' });
  await sleep(4500);
  console.log('A after hl', JSON.stringify(await state(A)));
  await A.screenshot({ path: out + '/hl_after.png' });
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
