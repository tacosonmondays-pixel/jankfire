require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.addInitScript(([t]) => { localStorage.setItem('jankfire_token', t); localStorage.setItem('jankfire', JSON.stringify({ name: 'cztest', jank: 3 })); }, [process.env.TOKEN]);
  await pg.goto(`http://localhost:${process.env.PORT}/`); await sleep(3000);
  await pg.click('#cratesBtn', { force: true }); await sleep(1500);
  await pg.click(`#crateCards .cratecard >> nth=${process.env.N || 0} >> button`);
  for (const t of [800, 2500, 4900, 5600, 7000]) { await sleep(t - (this.last || 0)); this.last = t; await pg.screenshot({ path: `${process.env.SP}/roll_${t}.jpg`, quality: 75 }); }
  console.log('result:', await pg.textContent('#rollResult'));
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
