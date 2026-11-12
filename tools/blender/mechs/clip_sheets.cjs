// The mechs' clips as three.js plays them (AnimationMixer on public/models/x_mech_<id>.glb): contact sheets, one row
// per clip, frames across. Serves the page itself (no game server needed).
// usage: node tools/blender/mechs/clip_sheets.cjs [outDir=docs/mechs/clips] [mech=all] [rowsPerSheet=5]
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '../../..'), OUT = process.argv[2] || path.join(ROOT, 'docs/mechs/clips');
const ONLY = process.argv[3] && process.argv[3] !== 'all' ? [process.argv[3]] : ['paperplane', 'nightshift'], PER = +(process.argv[4] || 5);
const MAP = [['/vendor/three/', 'node_modules/three/'], ['/models/', 'public/models/'], ['/', 'tools/blender/mechs/']];
const TYPE = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.glb': 'model/gltf-binary' };
const srv = http.createServer((q, r) => {
  const u = decodeURIComponent(q.url.split('?')[0]); if (u.includes('..')) { r.writeHead(400); return r.end(); }
  const m = MAP.find(([p]) => u.startsWith(p)), f = path.join(ROOT, m[1], u.slice(m[0].length));
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'content-type': TYPE[path.extname(f)] || 'application/octet-stream' }); r.end(d); });
});
srv.listen(0, async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  fs.mkdirSync(OUT, { recursive: true }); let bad = 0;
  for (const mech of ONLY) {
    const glb = fs.readFileSync(path.join(ROOT, 'public/models', `x_mech_${mech}.glb`)), n = glb.readUInt32LE(12), j = JSON.parse(glb.slice(20, 20 + n));
    const names = j.animations.map((a) => a.name);
    for (let i = 0; i < names.length; i += PER) {
      const part = names.slice(i, i + PER), pg = await b.newPage({ viewport: { width: 1610, height: 1500 } });
      const errs = []; pg.on('pageerror', (e) => errs.push(e.message)); pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
      await pg.goto(`http://localhost:${srv.address().port}/clip_sheets.html?mech=${mech}&clips=${part.join(',')}&frames=7`);
      await pg.waitForFunction(() => window.DONE, null, { timeout: 300000 }).catch(() => errs.push('timeout'));
      const info = await pg.evaluate(() => window.INFO).catch(() => null);
      const box = await pg.evaluate(() => { const c = document.getElementById('c'); return { w: c.width, h: c.height }; });
      const out = path.join(OUT, `${mech}_clips_${String(i / PER + 1).padStart(2, '0')}.jpg`);
      await pg.screenshot({ path: out, type: 'jpeg', quality: 84, clip: { x: 0, y: 0, width: box.w, height: box.h } });
      if (!info || info.missing.length || errs.length) bad = 1;
      console.log(path.relative(ROOT, out), JSON.stringify(info), errs.length ? errs : 'no errors');
      await pg.close();
    }
  }
  await b.close(); srv.close(); process.exit(bad);
});
