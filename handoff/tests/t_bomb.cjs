require('/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad/pwlock.cjs'); // at most 2 headless browsers machine-wide
// bots room, Plant & Defuse on Bazaar: teams, carrier, plants/defuses, round wins, match end -> vote -> next match
const { chromium } = require('playwright');
const out = process.argv[2];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1000, height: 600 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message + '\n' + e.stack));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ name: 'bomber', killcam: false })));
  await pg.goto('http://localhost:3000/'); await sleep(500);
  await pg.click('#scr-main [data-go="setup"]');
  await pg.selectOption('#setupGame', 'bomb');
  await pg.selectOption('#setupMap', 'bazaar');
  await pg.locator('#setupBots').fill('7');
  await pg.click('#setupGo'); await sleep(2500);
  await pg.evaluate(async () => {
    const { net } = await import('/js/net.js');
    window.__ev = [];
    net.ws.addEventListener('message', (e) => { const m = JSON.parse(e.data); if (['bombev', 'teams', 'round', 'vote', 'votes', 'bombyou', 'cfg'].includes(m.t)) window.__ev.push(m); });
  });
  const st = () => pg.evaluate(async () => {
    const { G } = await import('/js/ctx.js');
    const r = G.round || {};
    const teams = {}; for (const x of G.remotes.values()) teams[x.team] = (teams[x.team] || 0) + 1;
    return { game: r.game, myTeam: G.myTeam, teams, bomb: r.bomb && { ph: r.bomb.ph, n: r.bomb.n, att: r.bomb.att, wins: r.bomb.wins, carrier: r.bomb.carrier, left: Math.round(r.bomb.left / 1000), act: r.bomb.act }, map: G.cfg.map };
  });
  console.log('start', JSON.stringify(await st()));
  await pg.evaluate(async () => { const { net } = await import('/js/net.js'); net.send({ t: 'tbag' }); }); // drop the bomb for the bots
  await pg.screenshot({ path: `${out}/bomb_start.png` });
  for (let i = 0; i < 22; i++) {
    await sleep(6000);
    const s = await st();
    console.log(`t+${(i + 1) * 6}s`, JSON.stringify(s));
    if (i === 3) await pg.screenshot({ path: `${out}/bomb_mid.png` });
    const vote = await pg.evaluate(async () => !!(await import('/js/ctx.js')).G.vote);
    if (vote) { console.log('VOTE OPEN'); await pg.screenshot({ path: `${out}/bomb_vote.png` }); await pg.keyboard.press('Digit2'); await sleep(16000); console.log('after vote', JSON.stringify(await st())); break; }
  }
  const ev = await pg.evaluate(() => window.__ev.map((m) => m.t === 'bombev' ? `${m.t}:${m.k}${m.site ? ':' + m.site : ''}${m.why ? ':' + m.why : ''}` : m.t));
  console.log('events', ev.join(' '));
  await pg.screenshot({ path: `${out}/bomb_end.png` });
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
