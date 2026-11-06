// Weapon skins = finish (material) + hat (sits on the gun) + effect (particles off the gun).
// Everything is mix and match, per weapon, and other players see yours.
import * as THREE from 'three';
import { jankify } from './jank.js';
import { PSys } from './fx.js';
import { WRAP_MODES, zoneOf, paints } from './wrapzones.js';
import { PACK, packMat, packTick } from './wrappack.js';
export { WRAP_MODES, WRAP_MODE_NAMES } from './wrapzones.js';

export const FINISHES = {
  default: { name: 'Default' },
  gold: { name: 'Gold', tracer: 0xffd23b },
  chrome: { name: 'Chrome', tracer: 0xe8f0ff },
  pink: { name: 'Pink', tracer: 0xff6bd0 },
  camo: { name: 'Camo', tracer: 0xb0ff80 },
  neon: { name: 'Neon', tracer: 0x39ff14 },
  rainbow: { name: 'Rainbow', tracer: 'rainbow' },
  galaxy: { name: 'Galaxy', tracer: 0xb07dff },
  lava: { name: 'Lava', tracer: 0xff5a1a },
  ice: { name: 'Ice', tracer: 0x9ff0ff },
  ghost: { name: 'Ghost', tracer: 0xffffff },
  wood: { name: 'Wood' },
  tape: { name: 'Duct Tape', tracer: 0xdddddd },
  carbon: { name: 'Carbon Fiber', tracer: 0x88aaff },
  tiger: { name: 'Tiger', tracer: 0xff9a1a },
  fade: { name: 'Fade', tracer: 0xff6bd0 },
  missing: { name: 'Missing Texture', tracer: 0xff00dc },
};
for (const [id, p] of Object.entries(PACK)) FINISHES[id] = { name: p.name, tracer: p.tracer }; // the big wrap pack (wrappack.js)
export const HATS = {
  none: { name: 'None' }, tophat: { name: 'Top Hat' }, party: { name: 'Party Hat' }, crown: { name: 'Crown' },
  cowboy: { name: 'Cowboy Hat' }, propeller: { name: 'Propeller Cap' }, halo: { name: 'Halo' }, chef: { name: 'Chef Hat' },
  cone: { name: 'Traffic Cone' }, eyes: { name: 'Googly Eyes' }, duck: { name: 'Tiny Duck' },
};
export const EFFECTS = {
  none: { name: 'None' }, sparkles: { name: 'Sparkles' }, flames: { name: 'Flames' }, hearts: { name: 'Hearts' },
  bubbles: { name: 'Bubbles' }, electric: { name: 'Electric' }, music: { name: 'Music' }, money: { name: 'Money' },
  smoke: { name: 'Smoke' }, rainbow: { name: 'Rainbow' },
};
export const DEFAULT_SKIN = ['default', 'none', 'none', 'default', 'normal'];

// skin = [wrap, hat, effect, model, wrap mode]. saves from before wrap modes have no 5th slot: they get normal
export function validSkin(s) {
  const ok = (T, v) => v === 'random' || (typeof v === 'string' && Object.hasOwn(T, v)); // 'random': rolled on every spawn (customize.js)
  if (!Array.isArray(s) || !ok(FINISHES, s[0]) || !ok(HATS, s[1]) || !ok(EFFECTS, s[2])) return DEFAULT_SKIN;
  return [s[0], s[1], s[2], typeof s[3] === 'string' ? s[3] : 'default', WRAP_MODES.includes(s[4]) ? s[4] : 'normal'];
}
// what gets drawn: a 'random' slot that wasn't rolled yet (a menu hover) is drawn as the default
const drawable = (skin) => validSkin(skin).map((v, i) => (v === 'random' ? DEFAULT_SKIN[i] : v));
export function randomSkin() {
  const pick = (o) => { const k = Object.keys(o); return k[(Math.random() * k.length) | 0]; };
  return [pick(FINISHES), pick(HATS), pick(EFFECTS), 'default', WRAP_MODES[(Math.random() * 3) | 0]];
}

const tmpC = new THREE.Color();
export function tracerColor(skin, fallback) {
  const f = FINISHES[drawable(skin)[0]];
  if (!f || !f.tracer) return fallback;
  if (f.tracer === 'rainbow') return tmpC.setHSL(Math.random(), 1, 0.6).getHex();
  return f.tracer;
}

// ------------------------------------------------------------ textures
function tex(size, draw, repeat = 1) {
  const c = document.createElement('canvas');
  c.width = c.height = size;
  draw(c.getContext('2d'), size);
  const t = new THREE.CanvasTexture(c);
  t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestFilter; t.generateMipmaps = false;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(repeat, repeat);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
const rnd = (n) => (Math.random() * n) | 0;
let T = null;
function textures() {
  if (T) return T;
  T = {
    camo: tex(16, (g, s) => {
      const cols = ['#4b5a2a', '#6b7a3a', '#3a2f1e', '#8a8a5a'];
      g.fillStyle = cols[0]; g.fillRect(0, 0, s, s);
      for (let i = 0; i < 14; i++) { g.fillStyle = cols[1 + rnd(3)]; g.fillRect(rnd(s), rnd(s), 2 + rnd(5), 2 + rnd(4)); }
    }),
    galaxy: tex(32, (g, s) => {
      for (let y = 0; y < s; y += 2) for (let x = 0; x < s; x += 2) { const k = rnd(40); g.fillStyle = `rgb(${20 + k},${5 + rnd(15)},${50 + k * 2})`; g.fillRect(x, y, 2, 2); }
      for (let i = 0; i < 18; i++) { g.fillStyle = Math.random() < 0.3 ? '#ff9aff' : '#ffffff'; g.fillRect(rnd(s), rnd(s), 1, 1); }
    }),
    lava: tex(16, (g, s) => {
      for (let y = 0; y < s; y++) for (let x = 0; x < s; x++) {
        const v = Math.sin(x * 0.8 + Math.sin(y * 0.6) * 2) + Math.random() * 0.6;
        g.fillStyle = v > 0.9 ? '#ffe14d' : v > 0.3 ? '#ff5a1a' : v > -0.4 ? '#a81a00' : '#2a0800';
        g.fillRect(x, y, 1, 1);
      }
    }),
    wood: tex(16, (g, s) => {
      for (let y = 0; y < s; y++) { const k = (Math.sin(y * 1.3) * 20) | 0; g.fillStyle = `rgb(${150 + k},${100 + k},${55 + k / 2})`; g.fillRect(0, y, s, 1); }
      g.fillStyle = '#5a3a1a'; g.fillRect(4, 5, 3, 2);
    }),
    tape: tex(16, (g, s) => {
      for (let y = 0; y < s; y += 4) { const k = 150 + rnd(40); g.fillStyle = `rgb(${k},${k},${k + 6})`; g.fillRect(0, y, s, 4); g.fillStyle = 'rgba(0,0,0,0.25)'; g.fillRect(0, y + 3, s, 1); }
      g.fillStyle = 'rgba(255,255,255,0.25)'; for (let i = 0; i < 6; i++) g.fillRect(rnd(s), rnd(s), 3, 1);
    }),
    carbon: tex(8, (g) => { for (let y = 0; y < 8; y += 2) for (let x = 0; x < 8; x += 2) { g.fillStyle = (x + y) % 4 ? '#1a1c22' : '#3a3e48'; g.fillRect(x, y, 2, 2); } }, 2),
    tiger: tex(16, (g, s) => {
      g.fillStyle = '#ff8a1a'; g.fillRect(0, 0, s, s); g.fillStyle = '#1a0a00';
      for (let i = 0; i < 6; i++) { const x = rnd(s); g.fillRect(x, 0, 2, 4 + rnd(6)); g.fillRect(x + 1, 6 + rnd(4), 2, 3 + rnd(5)); }
    }),
    fade: tex(16, (g, s) => {
      for (let y = 0; y < s; y++) { const t = y / s; g.fillStyle = `rgb(${255 - t * 120 | 0},${80 + t * 120 | 0},${200 + t * 50 | 0})`; g.fillRect(0, y, s, 1); }
      g.fillStyle = 'rgba(255,255,120,0.5)'; g.fillRect(0, 0, s, 3);
    }),
    missing: tex(8, (g) => { for (let y = 0; y < 2; y++) for (let x = 0; x < 2; x++) { g.fillStyle = (x + y) % 2 ? '#000' : '#ff00dc'; g.fillRect(x * 4, y * 4, 4, 4); } }, 2),
  };
  return T;
}

// ------------------------------------------------------------ finish materials
const cache = new Map();
const rainbowMats = [];
function finishMat(finish, base, zoned, ps = 1) {
  const hsl = {};
  base.getHSL(hsl);
  // full: keeps dark parts dark. a zoned wrap has to read against the unpainted half, so near-black barrels get lifted
  const f = Math.round(Math.min(1.15, zoned ? 0.72 + hsl.l * 0.5 : 0.4 + hsl.l * 1.1) * 10) / 10;
  const key = finish + f;
  if (cache.has(key)) return cache.get(key);
  if (PACK[finish]) { const k2 = key + 'x' + ps; if (!cache.has(k2)) cache.set(k2, packMat(finish, f, ps)); return cache.get(k2); } // pack wraps build their own shader
  const T = textures();
  const c = (hex) => new THREE.Color(hex).multiplyScalar(f);
  let m;
  switch (finish) {
    case 'gold': m = new THREE.MeshPhongMaterial({ color: c(0xffc21a), specular: 0xfff0a0, shininess: 80, emissive: 0x2a1800, flatShading: true }); break;
    case 'chrome': m = new THREE.MeshPhongMaterial({ color: c(0xd8dde8), specular: 0xffffff, shininess: 140, emissive: 0x111118, flatShading: true }); break;
    case 'pink': m = new THREE.MeshLambertMaterial({ color: c(0xff6bd0), flatShading: true }); break;
    case 'camo': m = new THREE.MeshLambertMaterial({ map: T.camo, color: c(0xffffff) }); break;
    case 'neon': m = new THREE.MeshBasicMaterial({ color: c(0x39ff14) }); break;
    case 'rainbow': m = new THREE.MeshLambertMaterial({ color: 0xffffff, emissive: 0x000000, flatShading: true }); rainbowMats.push({ m, f }); break;
    case 'galaxy': m = new THREE.MeshBasicMaterial({ map: T.galaxy, color: new THREE.Color(0xffffff).multiplyScalar(0.6 + f * 0.4) }); break;
    case 'lava': m = new THREE.MeshBasicMaterial({ map: T.lava, color: new THREE.Color(0xffffff).multiplyScalar(0.5 + f * 0.5) }); break;
    case 'ice': m = new THREE.MeshPhongMaterial({ color: c(0xaaf4ff), specular: 0xffffff, shininess: 90, transparent: true, opacity: 0.72, flatShading: true }); break;
    case 'ghost': m = new THREE.MeshBasicMaterial({ color: 0xbfe8ff, transparent: true, opacity: 0.3, depthWrite: false, blending: THREE.AdditiveBlending }); break;
    case 'wood': m = new THREE.MeshLambertMaterial({ map: T.wood, color: c(0xffffff) }); break;
    case 'missing': m = new THREE.MeshBasicMaterial({ map: T.missing }); break;
    case 'tape': m = new THREE.MeshLambertMaterial({ map: T.tape, color: c(0xffffff) }); break;
    case 'carbon': m = new THREE.MeshPhongMaterial({ map: T.carbon, color: c(0xffffff), specular: 0x666688, shininess: 60 }); break;
    case 'tiger': m = new THREE.MeshLambertMaterial({ map: T.tiger, color: c(0xffffff) }); break;
    case 'fade': m = new THREE.MeshPhongMaterial({ map: T.fade, color: new THREE.Color(0xffffff).multiplyScalar(0.7 + f * 0.3), specular: 0xffffff, shininess: 90 }); break;
    default: return null;
  }
  jankify(m);
  cache.set(key, m);
  return m;
}

// ------------------------------------------------------------ hats (unit size, base at y=0, front = -Z)
const hm = new Map();
function HM(color, basic = false) {
  const k = color + (basic ? 'b' : '');
  if (!hm.has(k)) hm.set(k, jankify(basic ? new THREE.MeshBasicMaterial({ color }) : new THREE.MeshLambertMaterial({ color, flatShading: true })));
  return hm.get(k);
}
function mesh(geo, color, x = 0, y = 0, z = 0, basic = false) { const m = new THREE.Mesh(geo, HM(color, basic)); m.position.set(x, y, z); return m; }
const cyl = (rt, rb, h, seg = 8) => new THREE.CylinderGeometry(rt, rb, h, seg);
const sph = (r, a = 6, b = 4) => new THREE.SphereGeometry(r, a, b);

const HAT_BUILD = {
  tophat(g) {
    g.add(mesh(cyl(0.8, 0.8, 0.06), 0x111111, 0, 0.03, 0));
    g.add(mesh(cyl(0.5, 0.5, 0.9), 0x161616, 0, 0.5, 0));
    g.add(mesh(cyl(0.51, 0.51, 0.16), 0xc0102a, 0, 0.16, 0));
  },
  party(g) {
    g.add(mesh(new THREE.ConeGeometry(0.42, 1.1, 8), 0xff4fd8, 0, 0.55, 0));
    g.add(mesh(cyl(0.3, 0.33, 0.1), 0xffe14d, 0, 0.3, 0));
    g.add(mesh(cyl(0.16, 0.19, 0.08), 0x4fd8ff, 0, 0.7, 0));
    g.add(mesh(sph(0.13), 0xffffff, 0, 1.12, 0));
  },
  crown(g) {
    g.add(mesh(new THREE.CylinderGeometry(0.5, 0.5, 0.3, 10, 1, true), 0xffc21a, 0, 0.15, 0));
    for (let i = 0; i < 5; i++) {
      const a = (i / 5) * Math.PI * 2;
      g.add(mesh(new THREE.ConeGeometry(0.12, 0.35, 4), 0xffc21a, Math.cos(a) * 0.45, 0.45, Math.sin(a) * 0.45));
      g.add(mesh(sph(0.06), [0xff2040, 0x40a0ff, 0x30ff60][i % 3], Math.cos(a + 0.6) * 0.5, 0.16, Math.sin(a + 0.6) * 0.5, true));
    }
  },
  cowboy(g) {
    const brim = mesh(cyl(1.0, 1.0, 0.06, 10), 0x8a5a2b, 0, 0.05, 0); brim.scale.z = 0.8; g.add(brim);
    g.add(mesh(cyl(0.38, 0.48, 0.5), 0x8a5a2b, 0, 0.32, 0));
    g.add(mesh(cyl(0.49, 0.49, 0.1), 0x3a2010, 0, 0.12, 0));
  },
  propeller(g) {
    const cap = new THREE.Mesh(new THREE.SphereGeometry(0.5, 8, 4, 0, Math.PI * 2, 0, Math.PI / 2), HM(0x4fd8ff)); g.add(cap);
    g.add(mesh(cyl(0.04, 0.04, 0.25), 0xffe14d, 0, 0.6, 0));
    const prop = new THREE.Group(); prop.position.y = 0.73;
    prop.add(mesh(new THREE.BoxGeometry(1.1, 0.03, 0.14), 0xff4040));
    prop.add(mesh(new THREE.BoxGeometry(0.14, 0.03, 1.1), 0x4fff60));
    g.add(prop);
    g.userData.tick = (dt) => { prop.rotation.y += dt * 25; };
  },
  halo(g) {
    const h = mesh(new THREE.TorusGeometry(0.42, 0.07, 4, 12), 0xfff27a, 0, 0.6, 0, true);
    h.rotation.x = Math.PI / 2; g.add(h);
    g.userData.tick = (dt, now) => { h.position.y = 0.6 + Math.sin(now * 0.004) * 0.1; };
  },
  chef(g) {
    g.add(mesh(cyl(0.4, 0.4, 0.45), 0xffffff, 0, 0.22, 0));
    const puff = mesh(sph(0.58, 8, 5), 0xf4f4f4, 0, 0.62, 0); puff.scale.y = 0.6; g.add(puff);
  },
  cone(g) {
    g.add(mesh(new THREE.BoxGeometry(0.9, 0.06, 0.9), 0xff6a00, 0, 0.03, 0));
    g.add(mesh(new THREE.ConeGeometry(0.4, 1.1, 8), 0xff6a00, 0, 0.6, 0));
    g.add(mesh(cyl(0.22, 0.28, 0.16), 0xffffff, 0, 0.6, 0));
  },
  eyes(g) {
    const pupils = [];
    for (const s of [-1, 1]) {
      g.add(mesh(sph(0.3), 0xffffff, s * 0.32, 0.3, 0, true));
      const p = mesh(sph(0.14), 0x000000, s * 0.32, 0.3, -0.24, true);
      p.userData.base = p.position.clone();
      g.add(p);
      pupils.push(p);
    }
    g.userData.tick = () => { for (const p of pupils) { p.position.x = p.userData.base.x + (Math.random() - 0.5) * 0.1; p.position.y = p.userData.base.y + (Math.random() - 0.5) * 0.1; } };
  },
  duck(g) {
    const b = mesh(sph(0.42), 0xffd23b, 0, 0.32, 0); b.scale.set(1, 0.8, 1.25); g.add(b);
    g.add(mesh(sph(0.28), 0xffd23b, 0, 0.72, -0.28));
    g.add(mesh(new THREE.BoxGeometry(0.22, 0.08, 0.22), 0xff8a00, 0, 0.68, -0.58));
    g.add(mesh(sph(0.05), 0x000000, 0.14, 0.8, -0.5, true));
    g.add(mesh(sph(0.05), 0x000000, -0.14, 0.8, -0.5, true));
  },
};

const liveHats = new Set();
export function makeHat(id) {
  const g = new THREE.Group();
  (HAT_BUILD[id] || (() => {}))(g);
  if (g.userData.tick) liveHats.add(g);
  return g;
}

// ------------------------------------------------------------ apply
const tmpBox = new THREE.Box3(), tmpV = new THREE.Vector3(), tmpS = new THREE.Vector3();
export function applySkin(g, skin) {
  const [finish, hat, effect, , mode] = drawable(skin);
  const meshes = [];
  g.traverse((o) => { if (o.isMesh) meshes.push(o); });
  if (finish !== 'default') {
    const key = g.userData.model && g.userData.model !== 'default' ? g.userData.model : g.userData.wid;
    if (mode !== 'full') g.updateMatrixWorld(true);
    // pack patterns are sized in metres: a knife or a card gets them 2.2x finer so a whole motif fits on a handle
    let ps = 1;
    if (PACK[finish]) { g.updateMatrixWorld(true); tmpBox.setFromObject(g); tmpBox.getSize(tmpS); ps = Math.max(tmpS.x, tmpS.y, tmpS.z) < 0.5 ? 2.2 : 1; }
    for (const o of meshes) {
      const mats = Array.isArray(o.material) ? o.material : [o.material];
      // glowing bits and black eyes always keep their look
      if (o.userData.noWrap || mats.some((m) => m.isShaderMaterial)) continue;
      if (mats.some((m) => m.isMeshBasicMaterial && m.color && m.color.getHex() === 0x000000 && !m.map)) continue;
      const base = mats[0].color || new THREE.Color(1, 1, 1);
      // normal paints the handle side, reverse the business end, full the lot (see wrapzones.js); the rest keeps its own material
      if (mode !== 'full' && !paints(mode, zoneOf(o, g, key, base))) continue;
      const m = finishMat(finish, base, mode !== 'full', ps);
      if (m) o.material = m;
    }
  }
  g.userData.skinMeshes = meshes;
  g.userData.effect = effect;
  if (hat !== 'none' && meshes.length) {
    const h = makeHat(hat);
    if (g.userData.hatAt) { // hand placed spot for this weapon
      const [p, s] = g.userData.hatAt;
      h.scale.setScalar(s);
      h.position.set(p[0], p[1] - s * 0.04, p[2]);
    } else { // unknown shape: measure it and sit the hat on top
      g.updateMatrixWorld(true);
      tmpBox.setFromObject(g);
      tmpBox.getSize(tmpS); tmpBox.getCenter(tmpV);
      const len = Math.max(tmpS.x, tmpS.y, tmpS.z);
      const s = Math.min(0.2, Math.max(0.05, len * 0.15));
      h.scale.setScalar(s);
      h.position.set(tmpV.x, tmpBox.max.y - s * 0.05, tmpV.z + tmpS.z * 0.15);
    }
    h.userData.isHat = true;
    g.userData.hat = h;
    g.add(h);
  }
  return g;
}

// ------------------------------------------------------------ effect particles
let atlas = null;
function iconAtlas() {
  if (atlas) return atlas;
  const c = document.createElement('canvas');
  c.width = 64; c.height = 16;
  const g = c.getContext('2d');
  g.fillStyle = '#fff';
  const draw = (tile, rows) => rows.forEach((r, y) => [...r].forEach((ch, x) => { if (ch === 'X') g.fillRect(tile * 16 + 3 + x, 3 + y, 1, 1); }));
  draw(0, ['.XX...XX.', 'XXXX.XXXX', 'XXXXXXXXX', 'XXXXXXXXX', '.XXXXXXX.', '..XXXXX..', '...XXX...', '....X....']);
  draw(1, ['.....XX..', '.....X.X.', '.....X..X', '.....X...', '.....X...', '..XXXX...', '.XXXXX...', '.XXXX....', '..XX.....']);
  draw(2, ['...X...', '.XXXXX.', 'X..X...', 'X..X...', '.XXXXX.', '...X..X', '...X..X', '.XXXXX.', '...X...']);
  g.strokeStyle = '#fff'; g.lineWidth = 1.5;
  g.beginPath(); g.arc(48 + 8, 8, 5, 0, Math.PI * 2); g.stroke();
  g.fillRect(48 + 5, 5, 2, 2);
  atlas = new THREE.CanvasTexture(c);
  atlas.magFilter = THREE.NearestFilter; atlas.minFilter = THREE.NearestFilter; atlas.generateMipmaps = false;
  return atlas;
}

// one set of particle systems per scene (world, viewmodel, menu preview)
export function makeSkinSystems(scene, scale) {
  const sys = {
    add: new PSys(1200, THREE.AdditiveBlending, { scale }),
    norm: new PSys(800, THREE.NormalBlending, { scale }),
    icon: new PSys(500, THREE.NormalBlending, { scale, map: iconAtlas(), tiles: 4 }),
    update(dt) { this.add.update(dt); this.norm.update(dt); this.icon.update(dt); },
  };
  scene.add(sys.norm.points, sys.icon.points, sys.add.points);
  return sys;
}

const RATE = { sparkles: 22, flames: 40, hearts: 5, bubbles: 7, electric: 45, music: 4, money: 5, smoke: 10, rainbow: 30 };
const R = (s = 1) => (Math.random() * 2 - 1) * s;
const NOTE_COLS = [0xff4fd8, 0x4fd8ff, 0xffe14d, 0x7dff4f];
const wp = new THREE.Vector3();

// k = size of the weapon in that scene's units (1 = real world size)
export function emitSkinFx(sys, g, dt, k = 1, effectOverride) {
  if (!g || !sys) return;
  const e = effectOverride || g.userData.effect;
  if (!e || e === 'none') return;
  const meshes = g.userData.skinMeshes;
  if (!meshes || !meshes.length) return;
  let n = RATE[e] * dt;
  n = Math.floor(n) + (Math.random() < n % 1 ? 1 : 0);
  for (let i = 0; i < n; i++) {
    meshes[(Math.random() * meshes.length) | 0].getWorldPosition(wp);
    const x = wp.x + R(0.08 * k), y = wp.y + R(0.06 * k), z = wp.z + R(0.08 * k);
    switch (e) {
      case 'sparkles': sys.add.spawn(x, y, z, R(0.3 * k), R(0.3 * k), R(0.3 * k), 0.5, 0.12 * k, 0, 0xffffff, 0xffe14d); break;
      case 'flames': sys.add.spawn(x, y, z, R(0.15 * k), (0.8 + Math.random() * 0.5) * k, R(0.15 * k), 0.4, 0.17 * k, 0.02 * k, 0xffee88, 0xcc2200, 1, -k); break;
      case 'hearts': sys.icon.spawn(x, y, z, R(0.15 * k), 0.5 * k, R(0.15 * k), 1.2, 0.24 * k, 0.24 * k, 0xff3f8f, 0xff9ad5, 1, 0, 0, 0); break;
      case 'bubbles': sys.icon.spawn(x, y, z, R(0.2 * k), 0.45 * k, R(0.2 * k), 1.4, 0.14 * k, 0.22 * k, 0x9ff0ff, 0xffffff, 0.9, 0, 0, 3); break;
      case 'electric': sys.add.spawn(x + R(0.1 * k), y + R(0.1 * k), z + R(0.1 * k), R(3 * k), R(3 * k), R(3 * k), 0.07, 0.08 * k, 0.04 * k, 0xe8fbff, 0x4fd8ff); break;
      case 'music': sys.icon.spawn(x, y, z, R(0.3 * k), 0.5 * k, R(0.3 * k), 1.3, 0.22 * k, 0.22 * k, NOTE_COLS[(Math.random() * 4) | 0], 0xffffff, 1, 0, 0, 1); break;
      case 'money': sys.icon.spawn(x, y, z, R(0.4 * k), 0.6 * k, R(0.4 * k), 1.2, 0.22 * k, 0.22 * k, 0x3fdf3f, 0x2a8a2a, 1, 2.5 * k, 0, 2); break;
      case 'smoke': sys.norm.spawn(x, y, z, R(0.1 * k), 0.4 * k, R(0.1 * k), 1.2, 0.08 * k, 0.4 * k, 0xbbbbbb, 0x666666, 0.5); break;
      case 'rainbow': sys.add.spawn(x, y, z, R(0.2 * k), R(0.2 * k), R(0.2 * k), 0.6, 0.12 * k, 0, tmpC.setHSL(Math.random(), 1, 0.55).getHex(), 0xffffff); break;
    }
  }
}

// ------------------------------------------------------------ per-frame animation
function inScene(o) { while (o.parent) o = o.parent; return o.isScene; }
export function skinTick(dt, now) {
  packTick(now);
  const T = textures();
  T.galaxy.offset.x += dt * 0.05; T.galaxy.offset.y += dt * 0.02;
  T.lava.offset.y -= dt * 0.25; T.lava.offset.x = Math.sin(now * 0.001) * 0.2;
  for (const { m, f } of rainbowMats) {
    m.color.setHSL((now * 0.00025) % 1, 0.9, 0.45 * f);
    m.emissive.setHSL((now * 0.00025) % 1, 0.9, 0.12);
  }
  for (const h of liveHats) {
    // out of every scene = a discarded weapon (they're all added the frame they're built): let it go
    if (!inScene(h)) { liveHats.delete(h); continue; }
    h.userData.tick(dt, now);
  }
}
