// lobby scenes + parties: A makes a party, B joins with the code, A opens BATTLE ISLAND (the garage), both are in it.
// A walks: B's copy of A walks too (the position relay). A hops in their mech: B sees A's bay mech move. pictures of B.
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const OUT = process.env.OUT, PORT = process.env.PORT;
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const errs = [];
  const mk = async (name) => {
    const pg = await (await b.newContext({ viewport: { width: 800, height: 450 } })).newPage();
    pg.on('pageerror', (e) => errs.push(name + ': ' + e.message));
    await pg.addInitScript((n) => { localStorage.setItem('jf_giftseen_all', '1'); localStorage.setItem('jankfire', JSON.stringify({ name: n, killcam: false, jank: 1 })); }, name);
    await pg.goto(`http://localhost:${PORT}/`); await sleep(3000);
    await pg.evaluate(() => { const e = document.getElementById('jank'); e.value = '1'; e.dispatchEvent(new Event('change')); });
    return pg;
  };
  const A = await mk('taco'), B = await mk('noodle');
  const P = (pg) => pg.evaluate(async () => { const p = (await import('/js/party.js')).P; return { on: p.on, code: p.code, n: p.ms.length, set: p.set, me: p.me, lead: p.lead }; });
  for (let i = 0; i < 20 && !(await P(A)).code; i++) await sleep(500);
  const code = (await P(A)).code;
  await B.evaluate(async (c) => (await import('/js/party.js')).partyJoin(c), code);
  for (let i = 0; i < 20 && (await P(A)).n < 2; i++) await sleep(500);
  console.log('party', JSON.stringify(await P(A)), JSON.stringify(await P(B)));
  await A.evaluate(() => document.querySelector('[data-hub="offline"]').click()); await sleep(800);
  await A.evaluate(() => document.querySelector('[data-mode2="isle"]').click());
  const info = (pg) => pg.evaluate(async () => (await import('/js/lobbyscenes/index.js')).lobbySceneInfo());
  for (let i = 0; i < 40; i++) { const a = await info(A), bb = await info(B); if (a && bb) break; await sleep(500); }
  await sleep(3000);
  console.log('A', JSON.stringify(await info(A)));
  console.log('B', JSON.stringify(await info(B)));
  const ia = await info(A), ib = await info(B);
  const mateOf = (inf) => inf && inf.at[inf.people.indexOf('mate')];
  const b0 = mateOf(ib);
  await A.keyboard.down('KeyS'); await sleep(2500); await A.keyboard.up('KeyS'); await sleep(1500);
  const a1 = (await info(A)).at[0], b1 = mateOf(await info(B));
  console.log('A walked to', JSON.stringify(a1), '· B sees A at', JSON.stringify(b1), '(was', JSON.stringify(b0) + ')');
  await B.screenshot({ path: `${OUT}/party_B.jpg`, quality: 85 });
  // A hops in: walk back to A's bay first (A spawned in front of it), then E
  await A.keyboard.down('KeyW'); await sleep(2300); await A.keyboard.up('KeyW'); await sleep(800);
  await A.keyboard.press('KeyE'); await sleep(1500);
  await A.keyboard.down('KeyS'); await sleep(2500); await A.keyboard.up('KeyS'); await sleep(1500);
  console.log('A riding', JSON.stringify((await info(A)).extra), '· B', JSON.stringify((await info(B)).extra));
  await B.screenshot({ path: `${OUT}/party_B_mech.jpg`, quality: 85 });
  await A.screenshot({ path: `${OUT}/party_A.jpg`, quality: 85 });
  void ia;
  console.log('errors:', JSON.stringify(errs));
  await b.close();
})();
