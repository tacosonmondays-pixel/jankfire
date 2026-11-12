// playwright e2e: the story slot picker's DELETE / RESTART (a guest's browser save). a save sitting on the train is in
// slot 1: delete -> nah keeps it; delete -> WIPE IT empties it (NEW GAME) and NEW GAME starts at the opening in the city
// slice, not back on the train. (account saves go through POST /api/story/delete: tests/story/slotwipe.test.mjs)
// run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_slotwipe.cjs
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const OUT = process.env.SP + '/shots';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) process.exitCode = 1; };
// a run that got as far as the train (m01 and m02 done)
const TRAINSAVE = { v: 1, slot: 0, act: 1, chapter: 'return_to_sender', playtime: 1834, coupons: 41, at: { map: 'story_train', p: [0, 1.1, 4.7], yaw: 0 }, data: { flags: ['init_done'], quests: {}, seen: [] } };
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const ctx = await b.newContext({ viewport: { width: 960, height: 540 }, deviceScaleFactor: 2 });
  const pg = await ctx.newPage();
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message));
  await pg.addInitScript((sv) => {
    localStorage.setItem('jf_giftseen_all', '1');
    localStorage.setItem('jankfire', JSON.stringify({ name: 'change', jank: 0, loadout: { primary: 'ar', secondary: 'pistol', melee: 'knife', item: 'frag' } }));
    if (!sessionStorage.getItem('seeded')) { sessionStorage.setItem('seeded', '1'); localStorage.setItem('jfStorySaves', JSON.stringify([sv])); }
  }, TRAINSAVE);
  await pg.goto(`http://localhost:${process.env.PORT || 3411}/?story=1`); await sleep(1500);
  const ev = (f, a) => pg.evaluate(f, a);
  const card0 = () => ev(() => { const c = document.querySelectorAll('#storyPick .st-slot')[0]; return c ? { text: c.innerText, btns: [...c.querySelectorAll('button')].map((x) => x.textContent) } : null; });
  await pg.click('#storyBtn', { force: true });
  for (let i = 0; i < 20 && !(await ev(() => !!document.querySelector('#storyPick [data-wipe]'))); i++) await sleep(250);
  let c = await card0();
  ok(c && c.btns.includes('CONTINUE') && c.btns.includes('DELETE / RESTART'), 'the filled slot has CONTINUE and DELETE / RESTART: ' + JSON.stringify(c && c.btns));
  ok(!(await ev(() => document.querySelectorAll('#storyPick .st-slot')[1].querySelector('[data-wipe]'))), 'an empty slot has no delete button');
  await pg.screenshot({ path: `${OUT}/slotwipe_picker.png` });
  // nah: nothing happens
  await pg.click('#storyPick [data-wipe="0"]');
  await sleep(300);
  ok(await ev(() => /wipe this body\? the machine forgets\./.test(document.querySelector('#storyPick .st-wipe').innerText)), 'the confirm asks: "wipe this body? the machine forgets."');
  await pg.screenshot({ path: `${OUT}/slotwipe_confirm.png` });
  await pg.click('#storyPick .st-wipe button:text-is("nah")');
  await sleep(300);
  ok(await ev(() => !document.querySelector('#storyPick .st-wipe')) && (await ev(() => !!JSON.parse(localStorage.getItem('jfStorySaves'))[0])), 'nah: the confirm goes, the save stays');
  // WIPE IT
  await pg.click('#storyPick [data-wipe="0"]'); await sleep(300);
  await pg.click('#storyPick .st-wipe button:text-is("WIPE IT")');
  for (let i = 0; i < 20; i++) { c = await card0(); if (c && c.btns.includes('NEW GAME')) break; await sleep(250); }
  ok(c && c.btns.length === 1 && c.btns[0] === 'NEW GAME' && /empty/.test(c.text), 'wiped: slot 1 is empty with NEW GAME: ' + JSON.stringify(c));
  ok(await ev(() => JSON.parse(localStorage.getItem('jfStorySaves'))[0] == null), 'the browser save for slot 1 is gone');
  await sleep(400); await pg.screenshot({ path: `${OUT}/slotwipe_after.png` });
  // NEW GAME: the opening, not the train
  await pg.click('#storyPick .st-btn.yellow', { force: true });
  for (let i = 0; i < 60 && !(await ev(async () => { const { G } = await import('/js/ctx.js'); return G.joined && G.mode === 'story'; })); i++) await sleep(500);
  await sleep(6000);
  const st = await ev(async () => {
    const { G } = await import('/js/ctx.js'); const { MAP } = await import('/shared/map.js');
    const cur = G.story.cur, S = window.JF_STORY && window.JF_STORY.S;
    return { mode: G.mode, map: MAP.id, curMap: cur && cur.at.map, playtime: cur && cur.playtime, coupons: cur && cur.coupons, done: S ? Object.entries(S.st.quests).filter(([, q]) => q.done).map(([k]) => k) : null };
  });
  ok(st.mode === 'story' && st.map === 'story_slice' && st.curMap === 'story_slice', 'NEW GAME starts in the city slice (the opening), not the train: ' + JSON.stringify(st));
  ok(st.playtime < 60 && !st.coupons && Array.isArray(st.done) && st.done.length === 0, 'a fresh body: no playtime, no coupons, no missions done');
  await pg.screenshot({ path: `${OUT}/slotwipe_newgame.png` });
  // ---- logged in: the same buttons wipe the account's slot (POST /api/story/delete on this server's file store)
  const B = `http://localhost:${process.env.PORT || 3411}`;
  const reg = await (await fetch(B + '/api/register', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ name: 'wipe' + Math.floor(Math.random() * 1e6), pass: 'pass1234' }) })).json();
  const auth = { 'content-type': 'application/json', authorization: 'Bearer ' + reg.token };
  const sv = await fetch(B + '/api/story/save', { method: 'POST', headers: auth, body: JSON.stringify({ slot: 0, save: TRAINSAVE }) });
  ok(sv.ok, 'an account save on the train in slot 1');
  const pg2 = await ctx.newPage();
  pg2.on('pageerror', (e) => errs.push('PAGEERR ' + e.message));
  await pg2.addInitScript((t) => { localStorage.setItem('jankfire_token', t); }, reg.token);
  await pg2.goto(`${B}/?story=1`); await sleep(2500);
  const ev2 = (f, a) => pg2.evaluate(f, a);
  await pg2.click('#storyBtn', { force: true });
  for (let i = 0; i < 20 && !(await ev2(() => !!document.querySelector('#storyPick [data-wipe]'))); i++) await sleep(250);
  ok(await ev2(() => /saves are on your account/.test(document.querySelector('#storyPick').innerText)), 'the picker reads the account saves');
  await pg2.click('#storyPick [data-wipe="0"]'); await sleep(300);
  await pg2.click('#storyPick .st-wipe button:text-is("WIPE IT")');
  let a0 = null;
  for (let i = 0; i < 20; i++) { a0 = await ev2(() => { const c = document.querySelectorAll('#storyPick .st-slot')[0]; return c ? [...c.querySelectorAll('button')].map((x) => x.textContent) : []; }); if (a0.includes('NEW GAME')) break; await sleep(250); }
  ok(a0 && a0.length === 1 && a0[0] === 'NEW GAME', 'account slot 1 shows NEW GAME after the wipe: ' + JSON.stringify(a0));
  const L = await (await fetch(B + '/api/story/list', { method: 'POST', headers: auth, body: '{}' })).json();
  ok(L.saves && L.saves[0] == null, "the server's slot 1 is empty");
  console.log('ERRORS', errs.length, errs.slice(0, 5).join('\n'));
  await b.close();
})();
