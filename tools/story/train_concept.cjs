// renders the REVENUE PROTECTION concept sheet (tools/story/train_concept.html, a three.js blockout) to a png.
// usage: node tools/story/train_concept.cjs [out.png]   (serves the page itself: no game server needed)
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '../..'), OUT = process.argv[2] || path.join(ROOT, 'docs/story/train/revenue_protection_sheet.png');
const MAP = [['/vendor/three/', 'node_modules/three/'], ['/fonts/', 'public/fonts/'], ['/', 'tools/story/']];
const TYPE = { '.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2' };
const srv = http.createServer((q, r) => {
  const u = decodeURIComponent(q.url.split('?')[0]); if (u.includes('..')) { r.writeHead(400); return r.end(); }
  const m = MAP.find(([p]) => u.startsWith(p)), f = path.join(ROOT, m[1], u.slice(m[0].length));
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'content-type': TYPE[path.extname(f)] || 'application/octet-stream' }); r.end(d); });
});
srv.listen(0, async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 1920, height: 1260 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message)); pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.goto(`http://localhost:${srv.address().port}/train_concept.html`);
  await pg.waitForFunction(() => window.DONE, null, { timeout: 180000 }).catch(() => errs.push('timeout'));
  await pg.evaluate(() => document.fonts.ready);
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  await pg.locator('#wrap').screenshot({ path: OUT });
  console.log(OUT, errs.length ? errs : 'ok'); await b.close(); srv.close();
});
