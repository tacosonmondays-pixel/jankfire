// The train set seen in the game's renderer (three.js): loads rp_train.glb, rp_tunnel.glb, rp_commuter.glb and the parts
// file, checks every part the parts file names is a node, and writes the sheets. Serves the page itself: no game server.
// usage: node tools/blender/rp_train_shots.cjs [outDir] [sheets,comma]   (default docs/story/train, all four)
//   -> rp_train_game_turn.jpg, rp_train_game_detail.jpg, rp_train_game_tunnel.jpg, rp_train_game_commuter.jpg
// exit code 1 if a part is missing or the page threw.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '../..'), OUT = process.argv[2] || path.join(ROOT, 'docs/story/train'), SHEETS = (process.argv[3] || 'turn,detail,tunnel,commuter').split(',');
const MAP = [['/vendor/three/', 'node_modules/three/'], ['/models/', 'public/models/'], ['/', 'tools/blender/']];
const TYPE = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.glb': 'model/gltf-binary' };
const srv = http.createServer((q, r) => {
  const u = decodeURIComponent(q.url.split('?')[0]); if (u.includes('..')) { r.writeHead(400); return r.end(); }
  const m = MAP.find(([p]) => u.startsWith(p)), f = path.join(ROOT, m[1], u.slice(m[0].length));
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'content-type': TYPE[path.extname(f)] || 'application/octet-stream' }); r.end(d); });
});
srv.listen(0, async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  let bad = 0; fs.mkdirSync(OUT, { recursive: true });
  for (const sheet of SHEETS) {
    const pg = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
    const errs = []; pg.on('pageerror', (e) => errs.push(e.message)); pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await pg.goto(`http://localhost:${srv.address().port}/rp_train_shots.html?sheet=${sheet}`);
    await pg.waitForFunction(() => window.DONE, null, { timeout: 300000 }).catch(() => errs.push('timeout'));
    const info = await pg.evaluate(() => window.INFO).catch(() => null);
    const out = path.join(OUT, `rp_train_game_${sheet}.jpg`);
    await pg.locator('#wrap').screenshot({ path: out, type: 'jpeg', quality: 86 });
    if (!info || info.missing.length || errs.length || info.errs.length) bad = 1;
    console.log(out, JSON.stringify(info), errs.length ? errs : 'no errors');
    await pg.close();
  }
  await b.close(); srv.close(); process.exit(bad);
});
