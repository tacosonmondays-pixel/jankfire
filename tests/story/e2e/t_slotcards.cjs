// playwright e2e: the story slot cards say where each save is ("ACT 1 · tickets please"), worked out from its quests.
// a guest with two browser saves at different chapters, then an account with saves at act I and act II.
// run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_slotcards.cjs
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const OUT = process.env.SP + '/shots';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) process.exitCode = 1; };
const done = { step: '', n: [], t: 0, done: true }, on = (s) => ({ step: s, n: [], t: 0 });
const sv = (slot, quests, playtime, coupons, map = 'story_slice') => ({ v: 1, slot, act: 1, chapter: 'return_to_sender', playtime, coupons, at: { map, p: [0, 1.1, 4.7], yaw: 0 }, data: { flags: ['init_done'], seen: [], quests } });
const ACT1END = sv(0, { m01_return_to_sender: done, m02_sauce_run: done, m03_somethings_digesting: done, m04_clocking_in: done, m05_second_stomach: done, m06_tickets_please: on('board') }, 7260, 212, 'story_train');
const SAUCE = sv(1, { m01_return_to_sender: done, m02_sauce_run: on('drive') }, 1500, 18);
const ACT2 = sv(1, { m06_tickets_please: done, m06_option_c: done, m07_an_offer: on('meet') }, 11000, 530);
const B = `http://localhost:${process.env.PORT || 3411}`;
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const ctx = await b.newContext({ viewport: { width: 960, height: 540 }, deviceScaleFactor: 2 });
  const errs = [];
  const open = async (init, arg) => {
    const pg = await ctx.newPage();
    pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message));
    await pg.addInitScript(init, arg);
    await pg.goto(`${B}/?story=1`); await sleep(2000);
    await pg.click('#storyBtn', { force: true });
    for (let i = 0; i < 30 && !(await pg.evaluate(() => document.querySelectorAll('#storyPick .st-slot').length === 3)); i++) await sleep(250);
    await sleep(300);
    return { pg, cards: await pg.evaluate(() => [...document.querySelectorAll('#storyPick .st-slot span')].map((s) => s.textContent)) };
  };
  // ---- a guest: two browser saves
  const g = await open((s) => {
    localStorage.setItem('jf_giftseen_all', '1');
    localStorage.setItem('jankfire', JSON.stringify({ name: 'change', jank: 0 }));
    localStorage.setItem('jfStorySaves', JSON.stringify(s));
  }, [ACT1END, SAUCE]);
  console.log(g.cards);
  ok(/^ACT 1 · tickets please · 121 min · 212 coupons$/.test(g.cards[0]), 'slot 1 (end of act I): ' + g.cards[0]);
  ok(/^ACT 1 · sauce run · 25 min · 18 coupons$/.test(g.cards[1]), 'slot 2 (mission 2): ' + g.cards[1]);
  ok(/empty/.test(g.cards[2]), 'slot 3 empty');
  await g.pg.screenshot({ path: `${OUT}/slotcards_guest.png` });
  // ---- an account: the server's /api/story/list cards say the same
  const reg = await (await fetch(B + '/api/register', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ name: 'cards' + Math.floor(Math.random() * 1e6), pass: 'pass1234' }) })).json();
  const auth = { 'content-type': 'application/json', authorization: 'Bearer ' + reg.token };
  ok((await fetch(B + '/api/story/save', { method: 'POST', headers: auth, body: JSON.stringify({ slot: 0, save: ACT1END }) })).ok, 'account save 1');
  await sleep(10200); // (one save per 10 s)
  ok((await fetch(B + '/api/story/save', { method: 'POST', headers: auth, body: JSON.stringify({ slot: 1, save: ACT2 }) })).ok, 'account save 2');
  const a = await open((t) => { localStorage.setItem('jankfire_token', t); localStorage.setItem('jf_giftseen_all', '1'); }, reg.token);
  console.log(a.cards);
  ok(/^ACT 1 · tickets please · /.test(a.cards[0]), 'account slot 1: ' + a.cards[0]);
  ok(/^ACT 2 · an offer · 183 min · 530 coupons$/.test(a.cards[1]), 'account slot 2 (act II): ' + a.cards[1]);
  await a.pg.screenshot({ path: `${OUT}/slotcards_account.png` });
  console.log('ERRORS', errs.length, errs.slice(0, 5).join('\n'));
  await b.close();
})();
