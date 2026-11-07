// a clip of a real swing: node tools/city/swingclip.cjs <port> <path.json> <out.mp4> [jank=3]
// path.json from `node tools/city/grapple.mjs <route> --path path.json` (the rope physics' own flight, 30 Hz). Opens the
// city test page at the route's start, waits for the city to stream in, replays the flight (window.__replay: camera
// on the path, the rope drawn, facing the way you swing) while Playwright records, then trims the loading off with ffmpeg.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const [port = 3107, file, out = 'swing.mp4', jank = '3'] = process.argv.slice(2);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const P = JSON.parse(fs.readFileSync(file, 'utf8')), p0 = P.pts[0], p1 = P.pts[Math.min(P.pts.length - 1, 20)];
  const yaw = Math.atan2(-(p1[0] - p0[0]), -(p1[2] - p0[2])) || 0;
  const dir = fs.mkdtempSync(path.join(path.dirname(path.resolve(out)), '.clip-'));
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio', '--ignore-gpu-blocklist'] });
  const ctx = await b.newContext({ viewport: { width: 1280, height: 720 }, recordVideo: { dir, size: { width: 1280, height: 720 } } });
  const t0 = Date.now(), pg = await ctx.newPage(), errs = [];
  pg.on('pageerror', (e) => errs.push(e.message));
  await pg.goto(`http://localhost:${port}/storytest.html?city=slice&jank=${jank}&fly=1&at=${p0[0]},${p0[1]},${p0[2]}&yaw=${yaw.toFixed(3)}`);
  await pg.waitForFunction(() => window.__city, null, { timeout: 60000 });
  await pg.evaluate(() => { const h = document.getElementById('help'); if (h) h.style.display = 'none'; const st = document.createElement('style'); st.textContent = '#perf,#help{display:none!important}'; document.head.append(st); });
  // let the rings round the whole route stream in: walk the camera along it once, invisibly fast, then back to the start
  for (let i = 0; i < P.pts.length; i += 45) { await pg.evaluate((q) => { window.__city.me.pos = [q[0], q[1], q[2]]; }, P.pts[i]); await sleep(900); }
  await pg.evaluate((q) => { window.__city.me.pos = [q[0], q[1], q[2]]; }, p0);
  await pg.waitForFunction(() => window.__city.stream.stats().inflight === 0, null, { timeout: 60000 }).catch(() => {});
  await sleep(3500);
  const tStart = (Date.now() - t0) / 1000;
  await pg.evaluate((pts) => { window.__replay = { pts }; }, P.pts);
  await pg.waitForFunction(() => !window.__replay, null, { timeout: 120000, polling: 200 });
  await sleep(600);
  const W = await pg.evaluate(() => ({ a: window.__replayed.wall0, b: window.__replayed.wall1 })); // when the swing really ran (page clock)
  const tEnd = (W.b - t0) / 1000 + 0.5;
  const st = await pg.evaluate(() => ({ fps: Math.round(window.__city.fps()), tris: window.__city.renderer.info.render.triangles }));
  const vid = await pg.video().path();
  await ctx.close(); await b.close();
  execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-ss', String(Math.max(0, (W.a - t0) / 1000 - 0.4)), '-to', String(tEnd), '-i', vid, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '24', '-r', '30', out]);
  fs.rmSync(dir, { recursive: true, force: true });
  console.log(JSON.stringify({ out, route: P.route, secs: +((W.b - W.a) / 1000).toFixed(1), waited: +((W.a - t0) / 1000 - tStart).toFixed(1), ...st, errors: errs.slice(0, 3) }));
})();
