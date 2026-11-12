// playwright: crouch is Left Ctrl too, and Ctrl+W closes a browser tab (the owner: "I just held crouch in liquid and
// it closed my chrome"). checks the three guards:
//   1. mid story run, closing the tab asks "Leave site?" first (beforeunload, after a user gesture)
//   2. in fullscreen while playing, Keyboard Lock holds the shortcut keys (W, Q, T, N, Tab, 1-9) for the game,
//      and lets go on the menu and when fullscreen ends (public/js/kblock.js)
//   3. windowed, the first Ctrl crouch shows a one-time tip; and Ctrl+W / Ctrl+Q keydowns are swallowed (preventDefault)
// run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_ctrlw.cjs   (needs a running server)
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const skipIntro = require('./skipintro.cjs');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const PORT = process.env.PORT || 3411;
const fails = [];
const check = (ok, what) => { console.log((ok ? 'ok   ' : 'FAIL ') + what); if (!ok) fails.push(what); };

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 640, height: 360 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message));
  await pg.addInitScript(() => {
    localStorage.setItem('jf_giftseen_all', '1'); localStorage.setItem('jankfire', JSON.stringify({ name: 'ctrlw', jank: 0 }));
    localStorage.removeItem('jfStorySaves'); localStorage.removeItem('jfCtrlTip');
  });
  await pg.goto(`http://localhost:${PORT}/?story=1&storytest=1`); await sleep(2000);
  await pg.click('#storyBtn', { force: true }); await sleep(700);
  await pg.click('#storyPick .st-btn.yellow', { force: true }); await sleep(8000);
  await skipIntro(pg);
  await pg.mouse.click(320, 180); await sleep(500); // (a click: the user gesture Chrome wants before it asks anything)
  const ev = (f, a) => pg.evaluate(f, a);
  check(await ev(async () => { const { G } = await import('/js/ctx.js'); return G.joined && G.mode === 'story'; }), 'in a story run');
  // probes, added after the game's own handlers (so they see what those did): Ctrl+W/Q keydowns, the tip
  await ev(async () => {
    addEventListener('keydown', (e) => { if (e.ctrlKey && /^Key[WQ]$/.test(e.code)) (window.__ctrlKeys ||= []).push([e.code, e.defaultPrevented]); });
    const { hud } = await import('/js/hud.js'); const o = hud.msg; window.__tips = 0;
    hud.msg = function (t, ...r) { if (/ctrl\+w/i.test(String(t))) window.__tips++; return o.call(this, t, ...r); };
  });

  // 3a. the tip: windowed, the first Ctrl crouch
  const tips = () => ev(() => window.__tips);
  await pg.keyboard.down('Control'); await sleep(300);
  check(await tips() === 1 && /ctrl\+w closes the browser tab/i.test(await ev(() => document.body.innerText)), 'windowed: crouching on Ctrl shows the ctrl+w tip');
  // 3b. Ctrl+W / Ctrl+Q while crouched: swallowed by the game's key handler
  await pg.keyboard.press('KeyW'); await pg.keyboard.press('KeyQ'); await sleep(200);
  await pg.keyboard.up('Control'); await sleep(200);
  const ck = await ev(() => window.__ctrlKeys || []);
  check(ck.length >= 2 && ck.every(([, p]) => p), `Ctrl+W / Ctrl+Q keydowns are preventDefault'ed (${JSON.stringify(ck)})`);
  await pg.keyboard.down('Control'); await sleep(300); await pg.keyboard.up('Control');
  check(await tips() === 1, 'the tip only shows once');
  check(await ev(() => localStorage.getItem('jfCtrlTip') === '1'), 'the tip is remembered');

  // 2. fullscreen + playing: the shortcut keys are locked for the game
  const hasKb = await ev(() => !!(navigator.keyboard && navigator.keyboard.lock));
  console.log('navigator.keyboard.lock available:', hasKb);
  await ev(() => { document.addEventListener('click', () => document.documentElement.requestFullscreen().catch((e) => { window.__fsErr = String(e); }), { once: true, capture: true }); });
  await pg.mouse.click(320, 180); await sleep(1500);
  const st = () => ev(async () => { const k = await import('/js/kblock.js'); return { fs: !!document.fullscreenElement, pl: !!document.pointerLockElement, locked: k.kbLocked(), menu: !document.getElementById('menu').classList.contains('hidden'), err: window.__fsErr || null }; });
  let s = await st(); console.log('fullscreen, playing:', JSON.stringify(s));
  if (hasKb && s.fs && s.pl) {
    check(s.locked, 'fullscreen + playing: Keyboard Lock is on');
    await pg.keyboard.press('KeyB'); await sleep(800); // the pause menu
    s = await st(); console.log('menu open:', JSON.stringify(s));
    check(s.menu && !s.locked, 'pause menu: Keyboard Lock let go');
    await ev(async () => { await document.exitFullscreen().catch(() => {}); }); await sleep(800);
    s = await st(); check(!s.fs && !s.locked, 'out of fullscreen: no lock');
  } else console.log('SKIP the lock checks: this browser gave fullscreen ' + s.fs + ', pointer lock ' + s.pl + ', keyboard api ' + hasKb);

  // 1. "Leave site?": closing the tab mid-run (what Ctrl+W does) shows the beforeunload dialog. (test browsers skip
  // the guard so other tests can reload: __jfUnloadGuard turns it back on here)
  await ev(() => { window.__jfUnloadGuard = true; });
  await pg.mouse.click(320, 180); await sleep(300);
  // (Ctrl+W runs the same beforeunload step as this reload; playwright's close() doesn't report that dialog)
  let asked = null;
  pg.once('dialog', async (d) => { asked = d.type(); await d.dismiss(); }); // dismiss = "stay"
  await pg.reload({ timeout: 4000 }).catch(() => {}); await sleep(1000);
  check(asked === 'beforeunload', `leaving the page mid-run asks first (dialog: ${asked})`);
  check(await ev(async () => { const { G } = await import('/js/ctx.js'); return G.joined && G.mode === 'story'; }).catch(() => false), '"stay" keeps the run going');
  await ev(() => { window.__jfUnloadGuard = false; });
  let asked2 = null; pg.once('dialog', async (d) => { asked2 = d.type(); await d.accept(); });
  await pg.reload({ timeout: 15000 }).catch(() => {}); await sleep(500);
  check(asked2 === null, 'test browsers (guard off) leave without asking, so the other e2e reloads still work');
  check(!errs.length, 'no page errors' + (errs.length ? ': ' + errs.slice(0, 3).join(' | ') : ''));
  await b.close();
  console.log(fails.length ? `\n${fails.length} FAILED` : '\nALL OK');
  process.exit(fails.length ? 1 : 0);
})();
