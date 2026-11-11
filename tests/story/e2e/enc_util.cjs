// helpers for the Act I encounter e2e tests (t_enc_*.cjs): a fresh story run in the city slice, jump to a mission step,
// teleport, wait for things, screenshots. run them with SP=<dir with pwlock.cjs> PORT=<port>.
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const skipIntro = require('./skipintro.cjs');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function boot({ hd = false, size = [1280, 720], video = null } = {}) {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const ctx = await b.newContext({ viewport: { width: size[0], height: size[1] }, ...(video ? { recordVideo: { dir: video, size: { width: size[0], height: size[1] } } } : {}) });
  const pg = await ctx.newPage();
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message + ' ' + (e.stack || '').split('\n').slice(1, 3).join(' | ')));
  pg.on('console', (m) => { if (m.type() === 'error' || /^enc |encounters/.test(m.text())) errs.push(m.type() + ' ' + m.text()); });
  await pg.addInitScript((hd) => { localStorage.setItem('jf_giftseen_all', '1'); localStorage.setItem('jankfire', JSON.stringify({ name: 'change', jank: hd ? 3 : 0, loadout: { primary: 'ar', secondary: 'pistol', melee: 'knife', item: 'frag' } })); }, hd);
  await pg.goto(`http://localhost:${process.env.PORT || 3411}/?story=1&storydev=1&fresh=1`); await sleep(1500);
  await pg.click('#storyBtn', { force: true }); await sleep(700); await pg.click('#storyPick .st-btn.yellow', { force: true }); await sleep(9000); await skipIntro(pg);
  const ev = (f, a) => pg.evaluate(f, a);
  // the referee up (the slice's room takes a moment to build its boxes)
  for (let i = 0; i < 40; i++) { if (await ev(() => !!(window.JF_STORY && window.JF_STORY.enc))) break; await sleep(500); }
  return { b, ctx, pg, ev, errs };
}
// a mission at a step: everything before it done (act I in order)
async function jump(ev, quest, step) {
  return ev(([quest, step]) => {
    const ST = window.JF_STORY, S = ST.S, order = ['m01_return_to_sender', 'm02_sauce_run', 'm03_somethings_digesting', 'm04_clocking_in'];
    for (const id of order) { if (id === quest) break; S.st.quests[id] = { step: '', n: [], t: 0, done: true }; }
    for (const id of Object.keys(S.st.quests)) if (!order.includes(id) || order.indexOf(id) > order.indexOf(quest)) delete S.st.quests[id];
    delete S.st.quests[quest];
    S.st.track = quest;
    return S.quests.start(quest, step);
  }, [quest, step]);
}
async function tp(ev, p, yaw) {
  await ev(async ([p, yaw]) => { const { ME } = await import('/js/player.js'); ME.pos = p.slice(); ME.vel = [0, 0, 0]; if (yaw != null) ME.yaw = yaw; }, [p, yaw]);
}
// hold someone still for a moment while the chunks under them stream in
async function settle(ev, p, ms = 4000) {
  await ev(async (p) => { const { ME } = await import('/js/player.js'); window.__settle = setInterval(() => { ME.pos = p.slice(); ME.vel = [0, 0, 0]; }, 30); }, p);
  await sleep(ms);
  await ev(() => clearInterval(window.__settle));
}
const step = (ev, quest) => ev((q) => { const Q = window.JF_STORY.S.st.quests[q]; return Q ? (Q.done ? 'DONE' : Q.step) : null; }, quest);
// press through a talk; pick answer k (1-4) whenever there are answers
async function talkThrough(pg, ev, k = 1, max = 40) {
  for (let i = 0; i < max; i++) {
    const t = await ev(async () => { const tk = await import('/js/story/talk.js'); return tk.talking(); });
    if (!t) return true;
    const opts = await ev(() => { const o = document.querySelector('#stTalk .st-opts'); return o ? o.children.length : 0; });
    if (opts) { await pg.keyboard.press(`Digit${k}`); } else { await pg.keyboard.press('KeyF'); }
    await sleep(350);
  }
  return false;
}
module.exports = { boot, jump, tp, settle, step, talkThrough, sleep };
