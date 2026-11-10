// REVENUE PROTECTION seen in the game's renderer (three.js): loads the two .glb and the parts file, checks every part
// the parts file names is a node in the glb, and writes the sheets. Serves the page itself: no game server needed.
// usage: node tools/blender/rp_shots.cjs [outDir]   (default docs/story/train)  ->  rp_game_turn.jpg, rp_game_stages.jpg,
// rp_game_close.jpg. exit code 1 if a part is missing or the page threw.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '../..'), OUT = process.argv[2] || path.join(ROOT, 'docs/story/train');
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
  for (const sheet of ['turn', 'stages', 'close']) {
    const pg = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
    const errs = []; pg.on('pageerror', (e) => errs.push(e.message)); pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await pg.goto(`http://localhost:${srv.address().port}/rp_shots.html?sheet=${sheet}`);
    await pg.waitForFunction(() => window.DONE, null, { timeout: 240000 }).catch(() => errs.push('timeout'));
    const info = await pg.evaluate(() => window.INFO).catch(() => null);
    const out = path.join(OUT, `rp_game_${sheet}.jpg`);
    await pg.locator('#wrap').screenshot({ path: out, type: 'jpeg', quality: 86 });
    if (!info || info.missing.length || errs.length || info.errs.length) bad = 1;
    console.log(out, JSON.stringify(info ? { nodes: info.nodes, parts: info.meshes, missing: info.missing, arm: info.arm.length, hidden: info.hidden } : null), errs.length ? errs : 'no errors');
    await pg.close();
  }
  await b.close(); srv.close(); process.exit(bad);
});
