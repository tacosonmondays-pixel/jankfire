// Reference frames of a web-game effect, at fixed times after it fires (roblox/docs/VFX-PIPELINE.md, step 1).
// Serves public/js, shared/ and three.js, opens ref_harness.html in headless Chrome (DevTools protocol, no npm
// packages), and for each shot in the plan: REF.start(effect, view, opts), then REF.advance(t) + a screenshot per time.
//
//   node tools/roblox/vfx/ref_capture.mjs <plan.json> <out dir> [--three <dir with build/three.module.js>]
//
// plan.json: [{ "id": "ar_eye", "effect": "shot", "view": "eye", "times": [0.01, 0.03, 0.06, 0.1, 0.2], "opts": {...} }]
// Writes <out>/<id>_<ms>.png (640 x 360) and <out>/ref.json (what was shot, at which sim times).
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import os from 'node:os';

const HERE = path.dirname(new URL(import.meta.url).pathname).replace(/^\/([A-Za-z]:)/, '$1');
const REPO = path.resolve(HERE, '..', '..', '..');
const args = process.argv.slice(2);
const planFile = args[0], outDir = args[1];
const ti = args.indexOf('--three');
const THREE_DIR = ti > 0 ? args[ti + 1] : process.env.THREE_DIR || path.join(REPO, 'node_modules', 'three');
const CHROME = process.env.CHROME || ['C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find((p) => fs.existsSync(p));
if (!planFile || !outDir) { console.error('usage: ref_capture.mjs <plan.json> <out dir> [--three <dir>]'); process.exit(1); }
const plan = JSON.parse(fs.readFileSync(planFile, 'utf8'));
fs.mkdirSync(outDir, { recursive: true });

// ---- a tiny static server
const ROUTES = [['/vendor/three/', THREE_DIR + '/'], ['/js/', path.join(REPO, 'public/js/')], ['/shared/', path.join(REPO, 'shared/')],
  ['/sprites/', path.join(REPO, 'public/sprites/')], ['/vfx/', HERE + '/']];
const TYPES = { '.js': 'text/javascript', '.mjs': 'text/javascript', '.html': 'text/html', '.png': 'image/png', '.json': 'application/json', '.jpg': 'image/jpeg' };
const PAGE = `<!doctype html><html><head><style>html,body{margin:0;background:#000;overflow:hidden}</style>
<script type="importmap">{ "imports": { "three": "/vendor/three/build/three.module.js", "three/addons/": "/vendor/three/examples/jsm/" } }</script>
</head><body><script type="module" src="/vfx/ref_harness.js"></script></body></html>`;
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url.split('?')[0]);
  if (u === '/' || u === '/index.html') { res.writeHead(200, { 'content-type': 'text/html' }); res.end(PAGE); return; }
  for (const [pre, dir] of ROUTES) {
    if (!u.startsWith(pre)) continue;
    const f = path.join(dir, u.slice(pre.length));
    if (!f.startsWith(path.resolve(dir)) || !fs.existsSync(f)) break;
    res.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' });
    fs.createReadStream(f).pipe(res);
    return;
  }
  res.writeHead(404); res.end('nope ' + u);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const PORT = server.address().port;

// ---- headless Chrome, driven over the DevTools protocol
const prof = fs.mkdtempSync(path.join(os.tmpdir(), 'jfref-'));
const chrome = spawn(CHROME, ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${prof}`, '--no-first-run', '--no-default-browser-check',
  '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--window-size=640,360', '--hide-scrollbars', 'about:blank'], { stdio: ['ignore', 'ignore', 'pipe'] });
const wsUrl = await new Promise((resolve, reject) => {
  let buf = '';
  chrome.stderr.on('data', (d) => { buf += d; const m = buf.match(/DevTools listening on (ws:\/\/\S+)/); if (m) resolve(m[1]); });
  setTimeout(() => reject(new Error('chrome did not start: ' + buf.slice(-400))), 20000);
});
const port = new URL(wsUrl).port;
const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
const pageWs = targets.find((t) => t.type === 'page').webSocketDebuggerUrl;
const ws = new WebSocket(pageWs);
await new Promise((r) => ws.addEventListener('open', r, { once: true }));
let msgId = 0;
const waiting = new Map();
const logs = [];
ws.addEventListener('message', (ev) => {
  const m = JSON.parse(ev.data);
  if (m.id && waiting.has(m.id)) { waiting.get(m.id)(m); waiting.delete(m.id); }
  else if (m.method === 'Runtime.consoleAPICalled') logs.push(m.params.args.map((a) => a.value ?? a.description).join(' '));
  else if (m.method === 'Runtime.exceptionThrown') logs.push('EXC ' + JSON.stringify(m.params.exceptionDetails).slice(0, 600));
});
const send = (method, params = {}) => new Promise((r) => { const id = ++msgId; waiting.set(id, r); ws.send(JSON.stringify({ id, method, params })); });
const evalJs = async (expr) => {
  const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
  if (r.result.exceptionDetails) throw new Error(expr + ' -> ' + JSON.stringify(r.result.exceptionDetails).slice(0, 800));
  return r.result.result.value;
};
await send('Runtime.enable');
await send('Emulation.setDeviceMetricsOverride', { width: 640, height: 360, deviceScaleFactor: 1, mobile: false });
await send('Page.navigate', { url: `http://127.0.0.1:${PORT}/` });
let ok = false;
for (let i = 0; i < 300 && !ok; i++) { await new Promise((r) => setTimeout(r, 100)); try { ok = await evalJs('!!(window.REF && window.REF.ready)'); } catch { /* still loading */ } }
if (!ok) { console.error('harness never got ready\n' + logs.join('\n')); chrome.kill(); process.exit(2); }

const done = [];
for (const shot of plan) {
  await evalJs(`REF.start(${JSON.stringify(shot.effect)}, ${JSON.stringify(shot.view)}, ${JSON.stringify(shot.opts || {})})`);
  for (const t of shot.times) {
    const simT = await evalJs(`REF.advance(${t})`);
    const shotPng = await send('Page.captureScreenshot', { format: 'png', clip: { x: 0, y: 0, width: 640, height: 360, scale: 1 } });
    const file = path.join(outDir, `${shot.id}_${String(Math.round(t * 1000)).padStart(5, '0')}.png`);
    fs.writeFileSync(file, Buffer.from(shotPng.result.data, 'base64'));
    done.push({ id: shot.id, effect: shot.effect, view: shot.view, t, simT, file: path.basename(file) });
  }
  console.log('shot', shot.id, shot.times.length, 'frames');
}
fs.writeFileSync(path.join(outDir, 'ref.json'), JSON.stringify({ plan, frames: done, logs: logs.slice(-50) }, null, 1));
if (logs.length) console.log('page log (last 10):\n' + logs.slice(-10).join('\n'));
ws.close(); chrome.kill(); server.close();
try { fs.rmSync(prof, { recursive: true, force: true }); } catch { /* chrome may still hold it */ }
