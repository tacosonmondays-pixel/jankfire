// pictures of a converted map, drawn with the web game's own Three.js: the JS map's boxes (shared/map.js) next to the
// Roblox Part list (roblox/build/<map>.parts.json, studs / 3), top down, plus a 3/4 view of the Roblox version.
// run: node tools/roblox/preview.cjs [map=rooftop] [outDir=roblox/build] [port=3918]
const { spawn } = require('child_process');
const path = require('path'), fs = require('fs');
const { chromium } = require('playwright');
const ROOT = path.join(__dirname, '..', '..');
const MAP = process.argv[2] || 'rooftop', OUT = path.resolve(process.argv[3] || path.join(ROOT, 'roblox', 'build')), PORT = Number(process.argv[4]) || 3918;
const PAGE = `<!doctype html><html><head><meta charset="utf-8">
<script type="importmap">{ "imports": { "three": "/vendor/three/build/three.module.js" } }</script>
<style>html,body{margin:0;background:#120818}canvas{display:block}</style></head><body><script type="module">
import * as THREE from 'three';
import { MAPS } from '/shared/map.js';
const parts = await (await fetch('/__parts.json')).json();
const colors = await (await fetch('/__matcolors.json')).json();
const S = parts.S, def = MAPS[parts.map];
const W = 1600, H = 900;
const r = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true }); r.setSize(W, H); r.setPixelRatio(1); document.body.appendChild(r.domElement);
const col = (m) => { const c = colors[m]; return c ? new THREE.Color().setRGB(c.c[0], c.c[1], c.c[2], THREE.SRGBColorSpace) : new THREE.Color(0xff00dc); };
const geo = new THREE.BoxGeometry(1, 1, 1);
function sceneOf(list) { // list: { c: [x,y,z], s: [x,y,z], yaw, color, glow, alpha }
  const sc = new THREE.Scene();
  sc.add(new THREE.HemisphereLight(0xb8a8ff, 0x302040, 1.6)); const d = new THREE.DirectionalLight(0xffffff, 1.4); d.position.set(0.4, 1, 0.3); sc.add(d);
  const byKey = new Map();
  for (const b of list) { const k = b.color.getHexString() + (b.glow ? 'g' : '') + (b.alpha < 1 ? 'a' : ''); if (!byKey.has(k)) byKey.set(k, []); byKey.get(k).push(b); }
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler();
  for (const [k, l] of byKey) {
    const b0 = l[0], mat = b0.glow ? new THREE.MeshBasicMaterial({ color: b0.color }) : new THREE.MeshLambertMaterial({ color: b0.color, transparent: b0.alpha < 1, opacity: b0.alpha });
    const im = new THREE.InstancedMesh(geo, mat, l.length);
    l.forEach((b, i) => { e.set(0, b.yaw || 0, 0); q.setFromEuler(e); m4.compose(new THREE.Vector3(...b.c), q, new THREE.Vector3(...b.s)); im.setMatrixAt(i, m4); });
    sc.add(im);
  }
  return sc;
}
const js = [...def.boxes, ...def.deco].map((b) => ({ c: [0, 1, 2].map((i) => (b.min[i] + b.max[i]) / 2), s: [0, 1, 2].map((i) => b.max[i] - b.min[i]), yaw: b.rot || 0, color: col(b.mat), glow: /^neon|^lamp$|^light$/.test(b.mat), alpha: 1 }));
const rb = parts.parts.map((p) => ({ c: p.pos.map((x) => x / S), s: p.size.map((x) => x / S), yaw: p.yaw, color: new THREE.Color().setRGB(...p.color, THREE.SRGBColorSpace), glow: p.material === 'Neon', alpha: 1 - p.transparency }));
const A = sceneOf(js), B = sceneOf(rb);
for (const s of [A, B]) s.background = new THREE.Color(0x1a1030);
const ext = { x: 66, z: 36 };
const top = () => { const aspect = (W / 2) / H, h = ext.x / aspect; const c = new THREE.OrthographicCamera(-ext.x, ext.x, Math.max(ext.z, h), -Math.max(ext.z, h), 1, 1000); c.position.set(0, 300, 0); c.up.set(0, 0, -1); c.lookAt(0, 0, 0); return c; };
r.setScissorTest(true);
const shot = (fn) => { fn(); return r.domElement.toDataURL('image/png'); };
const out = {};
out.top = shot(() => {
  for (const [i, s] of [[0, A], [1, B]]) { r.setViewport(i * W / 2, 0, W / 2, H); r.setScissor(i * W / 2, 0, W / 2, H); r.render(s, top()); }
});
out.view = shot(() => {
  r.setViewport(0, 0, W, H); r.setScissor(0, 0, W, H);
  B.fog = new THREE.Fog(0x2a2050, 110, 480); B.background = new THREE.Color(0x2a2050);
  const c = new THREE.PerspectiveCamera(55, W / H, 0.5, 2000); c.position.set(-78, 34, 62); c.lookAt(0, -6, 0); r.render(B, c);
});
window.__out = out;
</script></body></html>`;
(async () => {
  const srv = spawn('node', ['server.js'], { cwd: ROOT, env: { ...process.env, PORT: String(PORT) }, stdio: 'ignore' });
  for (let i = 0; i < 120; i++) { try { await fetch(`http://localhost:${PORT}/`); break; } catch { await new Promise((r) => setTimeout(r, 500)); } }
  const br = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  try {
    const pg = await br.newPage({ viewport: { width: 1600, height: 900 } });
    pg.on('pageerror', (e) => console.log('page error', e.message));
    await pg.route('**/__preview.html', (rt) => rt.fulfill({ contentType: 'text/html', body: PAGE }));
    await pg.route('**/__parts.json', (rt) => rt.fulfill({ contentType: 'application/json', body: fs.readFileSync(path.join(ROOT, 'roblox', 'build', MAP + '.parts.json')) }));
    await pg.route('**/__matcolors.json', (rt) => rt.fulfill({ contentType: 'application/json', body: fs.readFileSync(path.join(__dirname, 'matcolors.json')) }));
    await pg.goto(`http://localhost:${PORT}/__preview.html`);
    await pg.waitForFunction(() => window.__out, null, { timeout: 120000 });
    const out = await pg.evaluate(() => window.__out);
    fs.mkdirSync(OUT, { recursive: true });
    for (const [k, d] of Object.entries(out)) { const f = path.join(OUT, `${MAP}-${k}.png`); fs.writeFileSync(f, Buffer.from(d.split(',')[1], 'base64')); console.log('wrote', f); }
  } finally { await br.close(); srv.kill(); }
})();
