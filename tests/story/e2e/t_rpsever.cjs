// playwright e2e: Revenue Protection, an arm shot off mid-reach. it must pull in from where it was (never snap out to
// full length first) and go limp. frames go to OUT (a contact sheet is made with ffmpeg by the caller).
// run: SP=<dir with pwlock.cjs> PORT=<port> OUT=<dir> node tests/story/e2e/t_rpsever.cjs   (needs a running server)
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const fs = require('fs');
const skipIntro = require('./skipintro.cjs');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const OUT = process.env.OUT || '.', SLOW = 0.1; // the client plays the cut at a tenth of real time, so headless frames catch it
(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 960, height: 600 } });
  const errs = []; pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message));
  await pg.addInitScript(() => { localStorage.setItem('jankfire', JSON.stringify({ name: 'sever', jank: 3, killcam: false, loadout: { primary: 'ar', secondary: 'pistol', melee: 'knife', item: 'frag' } })); localStorage.setItem('jf_giftseen_all', '1'); localStorage.removeItem('jfStorySaves'); });
  await pg.goto(`http://localhost:${process.env.PORT}/?story=1&storytest=1&train=1&storydev=1`); await sleep(1500);
  await sleep(2500); await pg.click('#storyBtn', { force: true }); await sleep(1500); await pg.click('#storyPick .st-btn.yellow', { force: true }); await sleep(3500); await skipIntro(pg);
  await sleep(5000); await skipIntro(pg); // (&train=1: straight onto the wagon, the fight starts by itself)
  // keep the arms' messages; hold back 'gone' so the slowed-down client can play the whole cut
  await pg.evaluate(async () => {
    const { net } = await import('/js/net.js'); const ws = net.ws, on = ws.onmessage; window.__arms = [];
    ws.onmessage = (e) => { try { const m = JSON.parse(e.data); const ev = m.t === 'sty' && m.ev; if (ev && ev.type === 'arm') { window.__arms.push(ev); if (ev.st === 'gone') return; } } catch {} on(e); };
  });
  const dev = (o) => pg.evaluate(async (o) => { const { G } = await import('/js/ctx.js'); G.story.send('bossdev', o); }, o);
  // the fight is on once the client has it live: at once calm (no arms by themselves) and THE GAP pinned open, or the
  // arms already out close it while we wait and it restarts (and a restarting fight ignores the staging)
  for (let i = 0; i < 60; i++) { if (await pg.evaluate(() => !!(window.JF_TRAIN && window.JF_TRAIN.F && window.JF_TRAIN.F.live))) break; await sleep(500); }
  await dev({ calm: true, pin: true, gap: 22 }); await sleep(4000); await dev({ calm: true, pin: true, gap: 22 }); await sleep(3000); // (again: past a restart)
  await pg.evaluate(async () => { const { ME } = await import('/js/player.js'); ME.pos = [0, 1.1, 8.6]; ME.vel = [0, 0, 0]; ME.yaw = 0; ME.pitch = 0.12; }); // the back of the wagon, looking up the tunnel: the whole arm in view
  await dev({ sever: true }); await sleep(2500); // (clear any arm already out)
  await pg.setViewportSize({ width: 160, height: 100 }); await sleep(1500); // (a tiny page renders fast, so its timers keep up with the fight)
  // the staging runs in the page (round trips to a headless page are slow): a grabber, and 30 % into its reach the sever,
  // then the client slows to a tenth so the frames below catch the whole cut
  const arm = await pg.evaluate(async (slow) => {
    const { G } = await import('/js/ctx.js'); const n0 = window.__arms.length;
    G.story.send('bossdev', { want: 'grab' });
    let a = null; for (let i = 0; i < 80 && !a; i++) { await new Promise((r) => setTimeout(r, 25)); a = window.__arms.slice(n0).find((x) => x.k === 'grab' && x.st === 'reach'); }
    if (!a) return null;
    await new Promise((r) => setTimeout(r, a.dur * 1000 * 0.15)); // (aim for 30 %: a busy page's timers run late)
    G.story.send('bossdev', { sever: true }); G.story.fightScale = () => slow;
    return a;
  }, SLOW);
  if (!arm) { console.log('FAIL no arm came', JSON.stringify(errs.slice(0, 3))); await pg.screenshot({ path: OUT + '/noarm.png' }); await b.close(); process.exit(1); }
  await pg.setViewportSize({ width: 960, height: 600 });
  // face the wall the arm walks along, from the back of the wagon on the other side
  await pg.evaluate(async (t) => { const { ME } = await import('/js/player.js'); const sx = Math.sign(t[0]) || 1; ME.pos = [-1.4 * sx, 1.1, 9.0]; ME.vel = [0, 0, 0]; ME.yaw = Math.atan2(-0.62 * sx, 1); ME.pitch = 0.18; }, arm.tgt);
  for (let i = 1; i <= 12; i++) { await pg.screenshot({ path: `${OUT}/f${String(i).padStart(2, '0')}.png` }); await sleep(450); }
  const cut = await pg.evaluate((id) => window.__arms.find((a) => a.id === id && a.st === 'cut'), arm.id);
  console.log('arms', JSON.stringify(await pg.evaluate(() => window.__arms.map((a) => [a.id, a.k, a.st, a.e0, a.tgt])))); console.log('cut message', JSON.stringify(cut && { st: cut.st, e0: cut.e0, dur: cut.dur }), 'errs', JSON.stringify(errs.slice(0, 3)));
  await b.close();
  process.exit(cut && Number.isFinite(cut.e0) && cut.e0 < 0.95 && !errs.length ? 0 : 1);
})();
