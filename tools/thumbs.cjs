// Map thumbnails for the end-of-match vote cards: renders every map in the real game (HD) and writes
// public/thumbs/<map>.jpg (480x300). Re-run after map changes:  node server.js &  then  node tools/thumbs.cjs [url]
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs'), os = require('os'), path = require('path');
const url = process.argv[2] || 'http://localhost:3000/';
const out = path.join(__dirname, '..', 'public', 'thumbs');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'jfthumb-'));
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 960, height: 600 } });
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ jank: 3, name: 'thumbs' })));
  await pg.goto(url); await sleep(1500);
  const ids = await pg.evaluate(async () => (await import('/shared/map.js')).MAP_ORDER);
  for (const id of ids) {
    await pg.evaluate(async (id) => {
      const { G } = await import('/js/ctx.js'); const { loadMap } = await import('/js/world.js');
      G.cfg.map = id; loadMap(id);
      document.getElementById('menu').classList.add('hidden');
    }, id);
    await sleep(2500);
    const png = path.join(tmp, id + '.png');
    await pg.locator('#game').screenshot({ path: png });
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', png, '-vf', 'scale=480:300:flags=lanczos', '-q:v', '4', path.join(out, id + '.jpg')]);
    console.log('thumb', id);
  }
  await b.close();
})();
