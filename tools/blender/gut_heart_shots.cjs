// THE HEART OF THE GUT seen in the game's renderer (three.js): loads public/models/story/s_gut_heart.glb, checks the
// ripple's vertex channel is there on every flesh mesh, and writes the sheets + the ripple clip. Serves the page itself:
// no game server needed.
//   node tools/blender/gut_heart_shots.cjs [outDir] [--only=turn,reads,close,ripple,clip]   (default docs/story/gut)
//   node tools/blender/gut_heart_shots.cjs --serve [port]     just serve the demo: open /gut_heart_demo.html
// exit code 1 if the page threw, a flesh mesh has no TEXCOORD_1, or a node the json names is missing.
const http = require('http'), fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const ROOT = path.join(__dirname, '../..'), args = process.argv.slice(2), flag = (k) => args.find((a) => a === '--' + k || a.startsWith('--' + k + '='));
const OUT = args.find((a) => !a.startsWith('--') && !/^\d+$/.test(a)) || path.join(ROOT, 'docs/story/gut');
const MAP = [['/vendor/three/', 'node_modules/three/'], ['/models/', 'public/models/'], ['/fonts/', 'public/fonts/'], ['/', 'tools/blender/']];
const TYPE = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.glb': 'model/gltf-binary', '.woff2': 'font/woff2' };
const srv = http.createServer((q, r) => {
  const u = decodeURIComponent(q.url.split('?')[0]); if (u.includes('..')) { r.writeHead(400); return r.end(); }
  const m = MAP.find(([p]) => u.startsWith(p)), f = path.join(ROOT, m[1], u.slice(m[0].length));
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'content-type': TYPE[path.extname(f)] || 'application/octet-stream', 'cache-control': 'no-store' }); r.end(d); });
});
if (flag('serve')) {
  const port = +(args.find((a) => /^\d+$/.test(a)) || 8787);
  srv.listen(port, () => console.log(`the heart of the gut: http://localhost:${port}/gut_heart_demo.html`));
} else srv.listen(0, async () => {
  const { chromium } = require('playwright');
  const only = flag('only') ? flag('only').split('=')[1].split(',') : ['turn', 'reads', 'close', 'ripple', 'clip'];
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  let bad = 0; fs.mkdirSync(OUT, { recursive: true }); const base = `http://localhost:${srv.address().port}/gut_heart_demo.html`;
  for (const sheet of only.filter((s) => s !== 'clip')) {
    const pg = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
    const errs = []; pg.on('pageerror', (e) => errs.push(e.message)); pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await pg.goto(`${base}?sheet=${sheet}`);
    await pg.waitForFunction(() => window.DONE, null, { timeout: 300000 }).catch(() => errs.push('timeout'));
    const info = await pg.evaluate(() => window.INFO).catch(() => null);
    const out = path.join(OUT, `gut_heart_${sheet}.jpg`);
    await pg.locator('#wrap').screenshot({ path: out, type: 'jpeg', quality: 88 });
    const noUv1 = info ? Object.keys(info.attrs).filter((k) => /gh_(heart|creep)/.test(k) && !/uv1/.test(info.attrs[k])) : ['?'];
    if (!info || errs.length || info.errs.length || noUv1.length) bad = 1;
    console.log(out, JSON.stringify(info ? { tris: info.tris, mats: info.mats, uv1: info.uv1, attrs: info.attrs, noUv1 } : null), errs.length ? errs : 'no errors');
    await pg.close();
  }
  if (only.includes('clip')) {   // the ripple running: 2 beats at 20 fps, a far view then a near one, side by side would hide it: two clips in one file
    const pg = await b.newPage({ viewport: { width: 960, height: 720 }, deviceScaleFactor: 1 });
    const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
    await pg.goto(`${base}?still=1`); await pg.waitForFunction(() => window.DONE && window.frame, null, { timeout: 300000 }).catch(() => errs.push('timeout'));
    const tmp = fs.mkdtempSync(path.join(require('os').tmpdir(), 'ghclip')); const fps = 20, rate = 0.72, beats = 2, n = Math.round(beats / rate * fps);
    const views = [{ t: [0, 27, 0], d: 62, az: 0.5, el: 0.0, fov: 60 }, { t: [0.5, 35.5, 0], d: 24, az: 0.35, el: 0.02, fov: 60 }, { t: [2.6, 28.6, 0.8], d: 6.5, az: 0.9, el: -0.3, fov: 75 }];
    let k = 0;
    for (const v of views) for (let i = 0; i < n; i++) {
      await pg.evaluate(([t, vv]) => window.frame(t, vv), [i / fps, v]);
      await pg.locator('canvas').screenshot({ path: path.join(tmp, `f${String(k++).padStart(4, '0')}.png`) });
    }
    const out = path.join(OUT, 'gut_heart_ripple.mp4');
    execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-framerate', String(fps), '-i', path.join(tmp, 'f%04d.png'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '24', '-movflags', '+faststart', out]);
    fs.rmSync(tmp, { recursive: true, force: true });
    if (errs.length) bad = 1;
    console.log(out, `${k} frames`, errs.length ? errs : 'no errors');
    await pg.close();
  }
  await b.close(); srv.close(); process.exit(bad);
});
