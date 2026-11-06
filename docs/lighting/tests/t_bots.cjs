// bots match on WITH BOTS > CUSTOM at Too HD: page errors, outgoing messages for a melee left click and a Blood Cross shot
require(process.env.PWLOCK || '/dev/null'); // pwlock.cjs from claude/handoff:handoff/tests caps headless browsers
const { chromium } = require('playwright');
const [port, out] = process.argv.slice(2);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 960, height: 540 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message + '\n' + e.stack));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push('CONSOLE ' + m.text()); });
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ name: 'lightbot', jank: 3, killcam: true, loadout: { primary: 'ar', secondary: 'bloodcross', melee: 'knife', item: 'frag' } })));
  await pg.goto(`http://localhost:${port}/`); await sleep(800);
  await pg.click('[data-pick="bots"]'); await sleep(400); await pg.click('#mpCustom'); await sleep(400);
  await pg.locator('#setupBots').fill('8');
  await pg.click('#setupGo'); await sleep(3000);
  await pg.evaluate(async () => {
    const { net } = await import('/js/net.js');
    window.__out = {}; window.__in = {};
    const s = net.ws.send.bind(net.ws);
    net.ws.send = (d) => { try { const m = JSON.parse(d); window.__out[m.t] = (window.__out[m.t] || 0) + 1; } catch { /* binary */ } return s(d); };
    net.ws.addEventListener('message', (e) => { try { const m = JSON.parse(e.data); window.__in[m.t] = (window.__in[m.t] || 0) + 1; } catch { /* */ } });
  });
  const res = {};
  for (const [slot, name] of [['Digit3', 'melee'], ['Digit2', 'bloodcross']]) {
    await pg.evaluate(async () => { const { ME } = await import('/js/player.js'); for (let i = 0; i < 40 && !ME.alive; i++) await new Promise((r) => setTimeout(r, 250)); });
    await pg.keyboard.press(slot); await sleep(900);
    await pg.evaluate(() => { window.__out = {}; });
    await pg.mouse.move(480, 270); await pg.mouse.down(); await sleep(250); await pg.mouse.up(); await sleep(900);
    res[name] = await pg.evaluate(() => window.__out);
    await pg.screenshot({ path: `${out}/bots_${name}.png` });
  }
  await sleep(20000); // let the bots play
  await pg.screenshot({ path: `${out}/bots_match.png` });
  const info = await pg.evaluate(async () => (await import('/js/lighting.js')).lightInfo());
  console.log('sent after left click:', JSON.stringify(res));
  console.log('received:', JSON.stringify(await pg.evaluate(() => window.__in)));
  console.log('lighting:', JSON.stringify(info));
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
