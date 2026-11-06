// Mode pictures, medals and the end-screen title props, rendered in 3D from the game's own models (weapons, the duck,
// mannequins, boxes) on a little slab, at a crunchy low resolution like the game itself. One offscreen renderer,
// every picture cached as an image after its first render.
import * as THREE from 'three';
import { buildWeapon, buildCharacter, M, freeTree } from './models.js';
import { DEFAULT_LOOK } from '/shared/looks.js';

const COLORS = {
  dm: ['#ff4f6a', '#3a0a18'], tdm: ['#9a7dff', '#1a0a3a'], tags: ['#4fffb0', '#0a2a1e'], bomb: ['#ffb04f', '#2a1206'],
  rand: ['#ff4fd8', '#2a0624'], gun: ['#ffe14d', '#2a2006'], inf: ['#7dff4f', '#0e2406'], spoons: ['#4fd8ff', '#061e2a'],
  duckrain: ['#4fd8ff', '#0a1a3a'], lava: ['#ff5a1a', '#2a0800'], oitc: ['#e0a040', '#24160a'],
};
export function modeColors(g) { return COLORS[g] || ['#ff4fd8', '#2a0624']; }

let R = null, scene, cam;
const cache = new Map();
function init() {
  const c = document.createElement('canvas');
  R = new THREE.WebGLRenderer({ canvas: c, antialias: false, alpha: true, preserveDrawingBuffer: true });
  R.setPixelRatio(1);
  scene = new THREE.Scene();
  cam = new THREE.PerspectiveCamera(32, 1.6, 0.05, 60);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x6a3a5a, 1.7));
  const sun = new THREE.DirectionalLight(0xffffff, 2.1);
  sun.position.set(1, 4, 4); // from the camera side: faces read
  scene.add(sun);
}
// a speckled slab texture, the same recipe the maps use (noisy on purpose)
function speckTex(hex) {
  const cv = document.createElement('canvas'); cv.width = cv.height = 16;
  const g = cv.getContext('2d'), c = new THREE.Color(hex).multiplyScalar(0.62); // a bit dark, so the model on it pops
  for (let y = 0; y < 16; y++) for (let x = 0; x < 16; x++) {
    const k = 0.75 + Math.random() * 0.4;
    g.fillStyle = `rgb(${(c.r * 255 * k) | 0},${(c.g * 255 * k) | 0},${(c.b * 255 * k) | 0})`; g.fillRect(x, y, 1, 1);
  }
  g.fillStyle = 'rgba(0,0,0,0.35)'; g.fillRect(0, 0, 16, 1); g.fillRect(0, 0, 1, 16);
  const t = new THREE.CanvasTexture(cv); t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestFilter; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(3, 2);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
const box = (w, h, d, col, basic) => new THREE.Mesh(new THREE.BoxGeometry(w, h, d), M(col, basic));
function fit(o, size) { // scale a model so its biggest side is `size`, centred, sitting on y = 0
  o.updateMatrixWorld(true);
  const b = new THREE.Box3().setFromObject(o), s = b.getSize(new THREE.Vector3()), c = b.getCenter(new THREE.Vector3());
  const k = size / Math.max(s.x, s.y, s.z, 0.01);
  const w = new THREE.Group(); o.position.sub(c); w.add(o); w.scale.setScalar(k); w.position.y = (s.y * k) / 2;
  return w;
}
const gun = (id, size, rx = 0, ry = 0, rz = 0) => { const g = buildWeapon(id); g.rotation.set(rx, ry, rz); return fit(g, size); };
const dude = (color, look) => { const ch = buildCharacter(color, { ...DEFAULT_LOOK, ...look }); ch.arm.rotation.x = -0.1; ch.armL.rotation.x = -0.1; return fit(ch.root, 1.25); };
const BUILD = {
  dm: () => { const g = gun('ar', 1.7, 0, -0.75, 0.2); g.position.y += 0.2; return g; },
  tdm: () => { const g = new THREE.Group(); const a = dude('#ff4f4f', { teamed: true }), b = dude('#4fa8ff', { teamed: true }); a.position.x = -0.45; a.rotation.y = -0.9; b.position.x = 0.45; b.rotation.y = 0.9 + Math.PI; g.add(a, b); return g; },
  tags: () => {
    const g = new THREE.Group();
    for (const [x, col, r] of [[-0.3, 0xff4f4f, 0.3], [0.3, 0x4fa8ff, -0.25]]) {
      const t = new THREE.Group(); t.add(box(0.4, 0.56, 0.04, 0xffffff, true), box(0.34, 0.5, 0.06, col, true));
      const hole = box(0.07, 0.07, 0.08, 0x120818, true); hole.position.y = 0.19; t.add(hole);
      t.position.set(x, 0.42, 0); t.rotation.set(-0.5, r, r * 0.6); g.add(t);
    }
    return g;
  },
  bomb: () => {
    const g = new THREE.Group(); g.add(box(0.5, 0.26, 0.32, 0x3a3f2a));
    for (const x of [-0.16, 0, 0.16]) { const d = box(0.12, 0.3, 0.12, 0xc02020); d.position.set(x, 0.05, 0); g.add(d); }
    const l = box(0.08, 0.08, 0.08, 0xff2020, true); l.position.set(0, 0.24, 0.1); g.add(l);
    const w = box(0.03, 0.03, 0.4, 0xffe14d); w.position.set(0.1, 0.2, 0.02); w.rotation.y = 0.6; g.add(w);
    const f = fit(g, 1.3); f.rotation.y = -0.5; return f;
  },
  rand: () => {
    const g = new THREE.Group();
    const die = (n) => { const d = new THREE.Group(); d.add(box(0.5, 0.5, 0.5, 0xffffff));
      const pip = [[0, 0], [-0.13, -0.13], [0.13, 0.13], [-0.13, 0.13], [0.13, -0.13], [-0.13, 0], [0.13, 0]];
      for (let i = 0; i < n; i++) { const p = box(0.09, 0.09, 0.04, 0xff4fd8, true); p.position.set(pip[i][0], pip[i][1], 0.25); d.add(p); const q = p.clone(); q.rotation.x = -Math.PI / 2; q.position.set(pip[i][0], 0.25, -pip[i][1]); if (i < 3) d.add(q); }
      return d; };
    const a = die(5); a.position.set(-0.34, 0.25, 0); a.rotation.y = 0.5;
    const b = die(3); b.position.set(0.36, 0.42, 0.1); b.rotation.set(0.7, -0.4, 0.5);
    g.add(a, b); return g;
  },
  gun: () => { const g = new THREE.Group(); [['ar', -0.55], ['shotgun', 0], ['spoon', 0.55]].forEach(([id, x], i) => { const w = gun(id, 1.1, 0, 0, Math.PI / 2); w.position.set(x, i * 0.18, 0); w.rotation.y = 0.35; g.add(w); }); return g; },
  inf: () => { const g = new THREE.Group(); const c = gun('claw', 1.35, -0.2, 1.2, -0.9); c.position.set(-0.15, 0.1, 0); const d = dude('#7dff4f', { skin: '#7dff4f' }); d.position.set(0.55, 0, -0.3); d.rotation.y = -0.6; g.add(c, d); return g; },
  spoons: () => { const g = new THREE.Group(); const a = gun('spoon', 1.5, 0, 0, Math.PI / 2 - 0.5); const b = gun('spoon', 1.5, 0, Math.PI, Math.PI / 2 - 0.5); a.position.x = -0.18; b.position.x = 0.18; g.add(a, b); return g; },
  duckrain: () => { const g = new THREE.Group(); [[-0.5, 0.9, 0.5], [0.15, 1.4, 0.4], [0.55, 0.1, 0.7]].forEach(([x, y, s]) => { const d = gun('duck', s, 0, x * 2, 0); d.position.set(x, y, 0); g.add(d); if (y > 0.2) { const sh = box(s * 0.7, 0.01, s * 0.5, 0x000000, true); sh.material = sh.material.clone(); sh.material.transparent = true; sh.material.opacity = 0.45; sh.position.set(x, 0.02, 0); g.add(sh); } }); return g; },
  lava: () => { const g = new THREE.Group(); const c = box(0.5, 0.5, 0.5, 0xb07840); c.position.y = 0.25; g.add(c); const d = dude('#ffe14d', {}); d.position.y = 0.5; d.scale.multiplyScalar(0.85); g.add(d); return g; },
  oitc: () => { const g = new THREE.Group(); const r = gun('revolver', 1.3, 0, -0.5, 0.15); r.position.x = -0.15; g.add(r);
    const b = new THREE.Group(); const cas = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 0.26, 6), M(0xe0a040)); const tip = new THREE.Mesh(new THREE.ConeGeometry(0.07, 0.14, 6), M(0xc8ccd2)); tip.position.y = 0.2; b.add(cas, tip); b.position.set(0.62, 0.13, 0.3); b.rotation.z = -0.25; g.add(b); return g; },
};
// render a model on a slab: [top colour, sky colour]. returns a data url
function shot(build, col, w = 192, h = 120, slab = true) {
  if (!R) init();
  R.setSize(w, h, false); cam.aspect = w / h; cam.updateProjectionMatrix();
  const root = new THREE.Group();
  if (slab) {
    const top = new THREE.MeshLambertMaterial({ map: speckTex(col[0]) }), side = new THREE.MeshLambertMaterial({ color: new THREE.Color(col[0]).multiplyScalar(0.45) });
    const s = new THREE.Mesh(new THREE.BoxGeometry(3.4, 0.3, 2.2), [side, side, top, side, side, side]); s.position.y = -0.15; root.add(s);
  }
  const m = build(); root.add(m); scene.add(root);
  R.setClearColor(new THREE.Color(col[1]), slab ? 1 : 0);
  if (slab) { cam.position.set(1.05, 1.2, 2.05); cam.lookAt(0, 0.5, 0); } else { cam.position.set(1.5, 1.75, 2.9); cam.lookAt(0, 0.45, 0); }
  R.render(scene, cam);
  const url = R.domElement.toDataURL('image/png');
  scene.remove(root); freeTree(root);
  return url;
}
export function modeImage(g) {
  const k = 'm:' + g;
  if (!cache.has(k)) { try { cache.set(k, shot(BUILD[g] || BUILD.dm, modeColors(g))); } catch (e) { console.warn('mode art', g, e); cache.set(k, ''); } }
  return cache.get(k);
}
export function modeThumb(g, name) {
  const d = document.createElement('div');
  d.className = 'mthumb';
  d.style.setProperty('--a', modeColors(g)[0]); d.style.setProperty('--b', modeColors(g)[1]);
  const url = modeImage(g);
  if (url) { const img = new Image(); img.alt = ''; img.src = url; d.append(img); } else d.append(Object.assign(document.createElement('b'), { textContent: name || g }));
  return d;
}
// a medal: a chunky low-poly octagon badge in its colour, the glyph pressed into the face, tilted at you
function glyphTex(glyph, col) {
  const cv = document.createElement('canvas'); cv.width = cv.height = 64; const x = cv.getContext('2d');
  x.fillStyle = col; x.fillRect(0, 0, 64, 64);
  x.font = 'bold 34px "Comic Neue", "Comic Sans MS", sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle';
  x.lineWidth = 6; x.strokeStyle = '#120818'; x.strokeText(glyph, 32, 34); x.fillStyle = '#fff'; x.fillText(glyph, 32, 34);
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.magFilter = THREE.NearestFilter; return t;
}
export function medalImage(id, md) {
  const k = 'md:' + id;
  if (cache.has(k)) return cache.get(k);
  let url = '';
  try { url = shot(() => {
    const g = new THREE.Group();
    const face = new THREE.MeshLambertMaterial({ map: glyphTex(md.g, md.c) }), rim = new THREE.MeshLambertMaterial({ color: new THREE.Color(md.c).multiplyScalar(0.55), flatShading: true });
    const coin = new THREE.Mesh(new THREE.CylinderGeometry(0.62, 0.62, 0.18, 8), [rim, face, rim]); coin.rotation.x = Math.PI / 2; coin.rotation.y = Math.PI / 8;
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.62, 0.07, 4, 8), new THREE.MeshLambertMaterial({ color: 0x120818, flatShading: true })); ring.rotation.z = Math.PI / 8;
    const strap = new THREE.Group(); for (const [x, c] of [[-0.16, md.c], [0, '#ffffff'], [0.16, md.c]]) { const s = box(0.16, 0.6, 0.06, c); s.position.set(x, 0.9, -0.05); strap.add(s); }
    g.add(coin, ring, strap); g.rotation.set(-0.12, -0.22, 0.06); g.position.y = 0.2;
    return g;
  }, ['#000', '#000'], 96, 112, false); } catch (e) { console.warn('medal art', id, e); } // no webgl: the caller draws a flat badge
  cache.set(k, url);
  return url;
}
// title props: a low-poly skull (defeat), a crown (victory), a gavel-ish block (draw)
const PROPS = {
  lose: () => {
    const g = new THREE.Group(), bone = 0xf0e4d4;
    g.add(box(0.9, 0.8, 0.86, bone));
    const jaw = box(0.62, 0.26, 0.6, bone); jaw.position.set(0, -0.5, 0.08); g.add(jaw);
    for (const x of [-0.22, 0.22]) { const e = box(0.24, 0.22, 0.1, 0x120818, true); e.position.set(x, 0.02, 0.43); g.add(e); const p = box(0.07, 0.07, 0.11, 0xff3030, true); p.position.set(x, 0.02, 0.44); g.add(p); }
    const n = box(0.1, 0.14, 0.1, 0x120818, true); n.position.set(0, -0.2, 0.43); g.add(n);
    for (let i = 0; i < 4; i++) { const t = box(0.03, 0.18, 0.04, 0x120818, true); t.position.set(-0.18 + i * 0.12, -0.46, 0.39); g.add(t); }
    const crack = box(0.04, 0.34, 0.04, 0x6a5a4a); crack.position.set(0.18, 0.3, 0.42); crack.rotation.z = 0.5; g.add(crack);
    g.rotation.set(0.1, -0.22, 0.12); return fit(g, 1.6);
  },
  win: () => {
    const g = new THREE.Group(), gold = 0xffd21a;
    const band = new THREE.Mesh(new THREE.CylinderGeometry(0.6, 0.6, 0.34, 8, 1, true), new THREE.MeshLambertMaterial({ color: gold, flatShading: true, side: THREE.DoubleSide })); g.add(band);
    for (let i = 0; i < 8; i++) { const a = (i / 8) * Math.PI * 2; const sp = new THREE.Mesh(new THREE.ConeGeometry(0.15, 0.42, 4), M(gold)); sp.position.set(Math.sin(a) * 0.55, 0.36, Math.cos(a) * 0.55); g.add(sp);
      const gem = box(0.12, 0.12, 0.06, [0xff3030, 0x4fd8ff, 0x7dff4f, 0xff4fd8][i % 4], true); gem.position.set(Math.sin(a) * 0.61, 0, Math.cos(a) * 0.61); gem.rotation.y = a; g.add(gem); }
    g.rotation.set(0.35, 0.3, -0.12); return fit(g, 1.6);
  },
  draw: () => { const g = new THREE.Group(); const h = box(0.9, 0.36, 0.36, 0x8a5a2a); h.position.y = 0.5; const s = box(0.12, 0.9, 0.12, 0x6a4020); g.add(h, s); g.rotation.set(0.2, -0.5, 0.5); return fit(g, 1.5); },
};
export function propImage(r, flip) {
  const k = 'p:' + r + (flip ? 'f' : '');
  if (!cache.has(k)) {
    let url = '';
    try { url = shot(() => { const p = (PROPS[r] || PROPS.lose)(); if (flip) p.rotation.y += 0.5; return p; }, ['#000', '#000'], 128, 128, false); } catch (e) { console.warn('title art', r, e); }
    cache.set(k, url);
  }
  return cache.get(k);
}
