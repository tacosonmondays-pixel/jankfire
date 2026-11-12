// Mech glbs side by side as three.js draws them (compare.html): one row per model, one column per view.
// usage: node tools/blender/mechs/compare.cjs <out.jpg> "<views>" <label>=<file.glb> [<label>=<file.glb> ...]
//   views: front,q,side,back and clip:<name>:<seconds>, e.g. "front,q,side,clip:walk:0.3,clip:ground_slam:0.56"
//   env: TALL=6 (camera framing height, m), TITLE="...", CW/CH (cell size, px)
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '../../..'), [OUT, VIEWS, ...MODELS] = process.argv.slice(2);
const files = MODELS.map((m) => path.resolve(m.slice(m.indexOf('=') + 1))), labels = MODELS.map((m) => m.slice(0, m.indexOf('=')));
const MAP = [['/vendor/three/', 'node_modules/three/'], ['/', 'tools/blender/mechs/']];
const TYPE = { '.html': 'text/html', '.js': 'text/javascript', '.glb': 'model/gltf-binary' };
const srv = http.createServer((q, r) => {
  const u = decodeURIComponent(q.url.split('?')[0]); if (u.includes('..')) { r.writeHead(400); return r.end(); }
  let f;
  if (u.startsWith('/f/')) f = files[parseInt(u.slice(3), 10)];
  else { const m = MAP.find(([p]) => u.startsWith(p)); f = path.join(ROOT, m[1], u.slice(m[0].length)); }
  fs.readFile(f || '', (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'content-type': TYPE[path.extname(f)] || 'application/octet-stream' }); r.end(d); });
});
srv.listen(0, async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const cw = +(process.env.CW || 300), ch = +(process.env.CH || 380), nv = VIEWS.split(',').length;
  const pg = await b.newPage({ viewport: { width: Math.max(1200, cw * nv + 20), height: Math.max(800, ch * files.length + 60) } }), errs = [];
  pg.on('pageerror', (e) => errs.push(e.message)); pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  const qs = new URLSearchParams({ n: files.length, labels: labels.join('|'), views: VIEWS, tall: process.env.TALL || '5.8', title: process.env.TITLE || '', cw: process.env.CW || '300', ch: process.env.CH || '380' });
  await pg.goto(`http://localhost:${srv.address().port}/compare.html?${qs}`);
  await pg.waitForFunction(() => window.DONE, null, { timeout: 300000 }).catch(() => errs.push('timeout'));
  const info = await pg.evaluate(() => window.INFO).catch(() => null);
  const box = await pg.evaluate(() => { const c = document.getElementById('c'); return { w: c.width, h: c.height }; });
  await pg.screenshot({ path: OUT, type: 'jpeg', quality: 86, clip: { x: 0, y: 0, width: box.w, height: box.h } });
  console.log(OUT, JSON.stringify(info), errs.length ? errs : 'no errors');
  await b.close(); srv.close(); process.exit(errs.length || !info || info.missing.length ? 1 : 0);
});
