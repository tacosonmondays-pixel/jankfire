// Programmer art. If you generated Tripo models (npm run models), they replace these automatically.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { jankify } from './jank.js';
import { applySkin } from './skins.js';
import { COSMETICS } from '/shared/cosmetics.js';
import { SUITS, RANKS, ARROW_TIPS } from '/shared/weapons.js';

// ------------------------------------------------------------ playing card faces (canvas, cached)
const cardFaces = new Map();
export function cardFace(id) {
  if (cardFaces.has(id)) return cardFaces.get(id);
  const c = document.createElement('canvas'); c.width = 32; c.height = 48;
  const g = c.getContext('2d');
  g.fillStyle = '#fff'; g.fillRect(0, 0, 32, 48);
  g.strokeStyle = '#222'; g.lineWidth = 2; g.strokeRect(1, 1, 30, 46);
  if (id === 'back') {
    g.fillStyle = '#c02040'; g.fillRect(4, 4, 24, 40);
    g.fillStyle = '#ffe14d'; for (let y = 6; y < 44; y += 6) for (let x = 6; x < 28; x += 6) g.fillRect(x, y, 2, 2);
  } else {
    const suit = SUITS[id[0]], rank = RANKS[Number(id.slice(1))] || 'JOKER';
    g.fillStyle = suit.color;
    g.font = 'bold 11px sans-serif'; g.textAlign = 'left'; g.textBaseline = 'top';
    g.fillText(id[0] === 'j' ? 'J' : rank, 3, 3);
    g.font = 'bold 22px sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillText(suit.sym, 16, 27);
  }
  const t = new THREE.CanvasTexture(c);
  t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestFilter; t.colorSpace = THREE.SRGBColorSpace;
  const m = new THREE.MeshBasicMaterial({ map: t });
  cardFaces.set(id, m);
  return m;
}

// ------------------------------------------------------------ Tripo GLB overrides
export const GLB = {};

export async function loadTripoModels() {
  let list = [];
  try { list = await (await fetch('/models/list')).json(); } catch { return 0; }
  if (!list.length) return 0;
  const loader = new GLTFLoader();
  await Promise.all(list.map((it) => new Promise((res) => {
    loader.load(it.url, (gltf) => { GLB[it.id] = prep(gltf.scene, it); res(); }, undefined, (e) => { console.warn('tripo model failed', it.id, e); res(); });
  })));
  return Object.keys(GLB).length;
}

function prep(scene, it) {
  scene.traverse((o) => {
    if (!o.isMesh) return;
    for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
      for (const k of ['map', 'emissiveMap', 'normalMap', 'roughnessMap', 'metalnessMap']) {
        if (m[k]) { m[k].magFilter = THREE.NearestFilter; m[k].minFilter = THREE.NearestFilter; m[k].generateMipmaps = false; m[k].needsUpdate = true; }
      }
      if ('roughness' in m) m.roughness = Math.max(0.6, m.roughness ?? 1);
      if ('metalness' in m) m.metalness = Math.min(0.2, m.metalness ?? 0);
      m.flatShading = true;
      jankify(m);
      m.needsUpdate = true;
    }
  });
  return { scene, size: it.size || 1, rot: (it.rot || [0, 0, 0]).map((d) => (d * Math.PI) / 180) };
}

// opts: { size, feet: bool, byHeight: bool, alignZ: bool, zOffset }
export function fitted(id, opts = {}) {
  const e = GLB[id];
  if (!e) return null;
  const holder = new THREE.Group(), inner = new THREE.Group();
  inner.add(e.scene.clone(true));
  holder.add(inner);
  inner.rotation.set(e.rot[0], e.rot[1], e.rot[2]);
  const measure = () => { holder.updateMatrixWorld(true); return new THREE.Box3().setFromObject(inner); };
  let box = measure();
  const sz = box.getSize(new THREE.Vector3());
  if (opts.alignZ && sz.x > sz.z && sz.x >= sz.y && !e.rot.some((r) => r)) {
    inner.rotation.y += Math.PI / 2;
    box = measure(); box.getSize(sz);
  }
  const target = opts.size ?? e.size;
  const s = target / Math.max(1e-6, opts.byHeight ? sz.y : Math.max(sz.x, sz.y, sz.z));
  inner.scale.setScalar(s);
  box = measure();
  const c = box.getCenter(new THREE.Vector3());
  if (opts.feet) inner.position.set(-c.x, -box.min.y, -c.z);
  else inner.position.set(-c.x, -c.y, -c.z + (opts.zOffset || 0));
  return holder;
}

// ------------------------------------------------------------ primitive helpers
const matCache = new Map();
export function M(color, basic = false) {
  const key = color + (basic ? 'b' : 'l');
  if (!matCache.has(key)) {
    matCache.set(key, jankify(basic
      ? new THREE.MeshBasicMaterial({ color })
      : new THREE.MeshLambertMaterial({ color, flatShading: true })));
  }
  return matCache.get(key);
}
function bx(w, h, d, color, x = 0, y = 0, z = 0, basic = false) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), M(color, basic));
  m.position.set(x, y, z);
  return m;
}
function cylZ(r, len, color, x = 0, y = 0, z = 0, seg = 6, basic = false) {
  const g = new THREE.CylinderGeometry(r, r, len, seg);
  g.rotateX(Math.PI / 2);
  const m = new THREE.Mesh(g, M(color, basic));
  m.position.set(x, y, z);
  return m;
}
function ball(r, color, x = 0, y = 0, z = 0, basic = false) {
  const m = new THREE.Mesh(new THREE.SphereGeometry(r, 6, 4), M(color, basic));
  m.position.set(x, y, z);
  return m;
}

// ------------------------------------------------------------ weapons (forward = -Z, grip at origin)
function cardTexture() {
  const c = document.createElement('canvas');
  c.width = 32; c.height = 48;
  const g = c.getContext('2d');
  g.fillStyle = '#ffffff'; g.fillRect(0, 0, 32, 48);
  g.fillStyle = '#e8262b'; g.fillRect(2, 2, 28, 44);
  g.save(); g.translate(16, 24); g.rotate(-0.5);
  g.fillStyle = '#ffffff'; g.beginPath(); g.ellipse(0, 0, 10, 17, 0, 0, Math.PI * 2); g.fill();
  g.restore();
  g.strokeStyle = '#e8262b'; g.lineWidth = 3;
  g.beginPath(); g.arc(16, 24, 6, Math.PI * 0.9, Math.PI * 1.9); g.stroke();
  g.beginPath(); g.arc(16, 24, 6, -Math.PI * 0.1, Math.PI * 0.9); g.stroke();
  g.fillStyle = '#e8262b';
  g.fillRect(19, 14, 5, 3); g.fillRect(8, 31, 5, 3);
  const t = new THREE.CanvasTexture(c);
  t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestFilter; t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
let _cardTex = null;
export function cardTex() { return _cardTex || (_cardTex = cardTexture()); }

function duck(g, s = 1) {
  const b = ball(0.12 * s, 0xffd23b, 0, 0, 0); b.scale.set(1, 0.85, 1.25); g.add(b);
  g.add(ball(0.08 * s, 0xffd23b, 0, 0.11 * s, -0.09 * s));
  g.add(bx(0.07 * s, 0.025 * s, 0.07 * s, 0xff8a00, 0, 0.1 * s, -0.17 * s));
  g.add(ball(0.015 * s, 0x000000, 0.045 * s, 0.14 * s, -0.14 * s, true));
  g.add(ball(0.015 * s, 0x000000, -0.045 * s, 0.14 * s, -0.14 * s, true));
  g.add(bx(0.05 * s, 0.04 * s, 0.06 * s, 0xffd23b, 0, 0.04 * s, 0.15 * s));
}
function slipper(g, s = 1) {
  g.add(bx(0.11 * s, 0.03 * s, 0.28 * s, 0xc85a8a, 0, 0, 0));
  const toe = ball(0.07 * s, 0xff9ad5, 0, 0.03 * s, -0.07 * s); toe.scale.set(0.85, 0.55, 1.4); g.add(toe);
  g.add(ball(0.025 * s, 0xffffff, 0, 0.07 * s, -0.12 * s));
}
function bowlingBall(g, r) {
  g.add(ball(r, 0x2a3aa8));
  for (const [x, y] of [[-0.25, 0.5], [0.25, 0.5], [0, 0.22]]) g.add(ball(r * 0.13, 0x000000, x * r, y * r, -0.85 * r, true));
}

const WB = {
  ar(g) {
    g.add(bx(0.07, 0.11, 0.5, 0x3b4a2a, 0, 0, -0.05));
    g.add(cylZ(0.018, 0.4, 0x111111, 0, 0.015, -0.5));
    g.add(bx(0.05, 0.05, 0.1, 0x222222, 0, 0.015, -0.42));
    const mag = bx(0.05, 0.2, 0.08, 0x222222, 0, -0.14, -0.12); mag.rotation.x = -0.25; g.add(mag);
    g.add(bx(0.05, 0.14, 0.06, 0x222222, 0, -0.12, 0.08));
    g.add(bx(0.06, 0.1, 0.25, 0x3b4a2a, 0, -0.02, 0.32));
    g.add(bx(0.03, 0.04, 0.12, 0x111111, 0, 0.08, -0.05));
    g.userData.muzzle = new THREE.Vector3(0, 0.015, -0.72);
    g.userData.len = 1.0;
  },
  smg(g) {
    g.add(bx(0.07, 0.11, 0.32, 0x2a2a35, 0, 0, -0.05));
    g.add(cylZ(0.02, 0.16, 0x111111, 0, 0.01, -0.28));
    g.add(bx(0.04, 0.26, 0.05, 0x111111, 0, -0.17, -0.12));
    g.add(bx(0.05, 0.14, 0.06, 0x111111, 0, -0.11, 0.06));
    g.add(bx(0.04, 0.03, 0.2, 0x555566, 0, 0.0, 0.2));
    g.userData.muzzle = new THREE.Vector3(0, 0.01, -0.37);
    g.userData.len = 0.6;
  },
  shotgun(g) {
    g.add(cylZ(0.025, 0.7, 0x1a1a1a, 0, 0.025, -0.38));
    g.add(cylZ(0.02, 0.55, 0x333333, 0, -0.025, -0.3));
    g.add(bx(0.07, 0.07, 0.14, 0x8a5a2b, 0, -0.025, -0.32));
    g.add(bx(0.07, 0.1, 0.2, 0x222222, 0, 0, 0.0));
    g.add(bx(0.06, 0.14, 0.3, 0x8a5a2b, 0, -0.04, 0.24));
    g.userData.muzzle = new THREE.Vector3(0, 0.025, -0.74);
    g.userData.len = 1.1;
  },
  minigun(g) {
    const barrels = new THREE.Group();
    barrels.position.set(0, 0, -0.35);
    for (let i = 0; i < 6; i++) {
      const a = (i / 6) * Math.PI * 2;
      barrels.add(cylZ(0.016, 0.6, 0x333333, Math.cos(a) * 0.045, Math.sin(a) * 0.045, -0.1, 5));
    }
    barrels.add(cylZ(0.07, 0.04, 0x555555, 0, 0, -0.32, 6));
    barrels.add(cylZ(0.07, 0.04, 0x555555, 0, 0, 0.1, 6));
    g.add(barrels);
    g.userData.barrels = barrels;
    g.add(bx(0.16, 0.16, 0.3, 0x4a4a4a, 0, 0, 0.05));
    g.add(bx(0.05, 0.08, 0.2, 0x222222, 0, 0.13, 0.05));
    g.add(bx(0.1, 0.12, 0.14, 0x6b5a2a, 0.12, -0.05, 0.08));
    g.userData.muzzle = new THREE.Vector3(0, 0, -0.75);
    g.userData.len = 1.0;
  },
  revolver(g) {
    g.add(cylZ(0.02, 0.22, 0x888888, 0, 0.03, -0.17));
    g.add(cylZ(0.045, 0.07, 0x666666, 0, 0.02, -0.02, 6));
    g.add(bx(0.04, 0.06, 0.1, 0x777777, 0, 0.03, 0.04));
    const grip = bx(0.045, 0.13, 0.06, 0x6b3a1a, 0, -0.06, 0.08); grip.rotation.x = 0.35; g.add(grip);
    g.userData.muzzle = new THREE.Vector3(0, 0.03, -0.29);
    g.userData.len = 0.35;
  },
  sniper(g) {
    g.add(bx(0.07, 0.12, 0.55, 0x2b2b2b));
    g.add(cylZ(0.022, 1.2, 0x111111, 0, 0.02, -0.85));
    g.add(cylZ(0.05, 0.32, 0x333333, 0, 0.11, -0.05));
    g.add(bx(0.06, 0.16, 0.32, 0x5a3a1a, 0, -0.03, 0.42));
    g.add(bx(0.05, 0.14, 0.06, 0x222222, 0, -0.12, 0.1));
    g.add(bx(0.075, 0.05, 0.14, 0xff4fd8, 0, 0.03, -0.15));
    g.add(bx(0.05, 0.05, 0.09, 0xff4fd8, 0, 0.02, -1.42));
    g.userData.muzzle = new THREE.Vector3(0, 0.02, -1.48);
    g.userData.len = 1.8;
  },
  chicken(g) {
    g.add(cylZ(0.09, 0.75, 0x3d7a2a, 0, 0, -0.1, 8));
    g.add(bx(0.05, 0.16, 0.08, 0x222222, 0, -0.12, 0.05));
    g.add(ball(0.075, 0xffe14d, 0, 0, -0.5));
    g.add(bx(0.03, 0.03, 0.07, 0xff8a00, 0, -0.005, -0.59));
    g.add(bx(0.015, 0.05, 0.07, 0xff2222, 0, 0.075, -0.5));
    g.add(ball(0.014, 0x000000, 0.05, 0.02, -0.54));
    g.add(ball(0.014, 0x000000, -0.05, 0.02, -0.54));
    g.userData.muzzle = new THREE.Vector3(0, 0, -0.62);
    g.userData.len = 0.9;
  },
  bowling(g) {
    g.add(cylZ(0.17, 0.8, 0x2a2a3a, 0, 0, -0.15, 8));
    g.add(cylZ(0.19, 0.06, 0x6b7bff, 0, 0, -0.53, 8));
    g.add(bx(0.06, 0.18, 0.08, 0x222222, 0, -0.22, 0.05));
    const b = new THREE.Group(); b.position.set(0, 0, -0.42); bowlingBall(b, 0.15); g.add(b);
    g.userData.muzzle = new THREE.Vector3(0, 0, -0.6);
    g.userData.len = 0.9;
  },
  banana(g) {
    g.add(bx(0.08, 0.12, 0.38, 0x8a5a2b));
    g.add(bx(0.05, 0.14, 0.07, 0x5a3a1a, 0, -0.12, 0.08));
    const t = new THREE.Mesh(new THREE.TorusGeometry(0.15, 0.035, 4, 8, Math.PI * 0.9), M(0xffe135));
    t.rotation.y = Math.PI / 2; t.position.set(0, 0.0, 0.02);
    g.add(t);
    g.add(cylZ(0.03, 0.15, 0xffe135, 0, 0, -0.25));
    g.add(bx(0.03, 0.03, 0.03, 0x3a2a10, 0, 0, -0.33));
    g.userData.muzzle = new THREE.Vector3(0, 0, -0.36);
    g.userData.len = 0.6;
  },
  cig(g) {
    g.add(cylZ(0.012, 0.13, 0xf4f4f4, 0, 0, -0.03));
    g.add(cylZ(0.0125, 0.045, 0xd98b3a, 0, 0, 0.055));
    const tip = cylZ(0.0135, 0.014, 0xff4400, 0, 0, -0.1, 6, true);
    tip.userData.noWrap = true;
    g.add(tip);
    g.userData.tip = tip;
    g.userData.muzzle = new THREE.Vector3(0, 0, -0.11);
    g.userData.len = 0.18;
  },
  blower(g) {
    g.add(bx(0.2, 0.24, 0.3, 0xff7a00, 0, 0, 0.05));
    g.add(bx(0.06, 0.1, 0.18, 0x222222, 0, 0.17, 0.05));
    g.add(bx(0.21, 0.08, 0.12, 0x333333, 0, -0.06, 0.12));
    g.add(cylZ(0.05, 0.75, 0x9a9a9a, 0, -0.03, -0.45, 8));
    g.add(cylZ(0.065, 0.06, 0xff7a00, 0, -0.03, -0.83, 8));
    g.userData.muzzle = new THREE.Vector3(0, -0.03, -0.87);
    g.userData.len = 1.0;
  },
  popper(g) {
    const c = new THREE.Mesh(new THREE.ConeGeometry(0.07, 0.24, 6).rotateX(-Math.PI / 2), M(0xff6bd0));
    c.position.set(0, 0, -0.08); g.add(c);
    for (let i = 0; i < 3; i++) {
      const band = new THREE.Mesh(new THREE.CylinderGeometry(0.02 + i * 0.018, 0.02 + i * 0.018, 0.02, 6).rotateX(Math.PI / 2), M([0xffe14d, 0x4fd8ff, 0x7dff4f][i]));
      band.position.set(0, 0, -0.01 - i * 0.07); g.add(band);
    }
    g.add(bx(0.01, 0.01, 0.12, 0xffffff, 0, -0.01, 0.1));
    g.userData.muzzle = new THREE.Vector3(0, 0, -0.21);
    g.userData.len = 0.3;
  },
  reverse(g) {
    const card = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.18, 0.004), new THREE.MeshBasicMaterial({ map: cardTex() }));
    card.rotation.x = -0.2;
    g.add(card);
    g.userData.card = card;
    g.userData.muzzle = new THREE.Vector3(0, 0.05, -0.05);
    g.userData.len = 0.2;
  },
  duck(g) {
    duck(g, 0.8);
    g.userData.muzzle = new THREE.Vector3(0, 0, -0.15);
    g.userData.len = 0.25;
  },
  bread(g) {
    // a huge loaf. hold it like a bat.
    const loaf = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.11, 1.5, 7), M(0xd9a35b));
    loaf.geometry.rotateX(Math.PI / 2);
    loaf.position.set(0, 0, -0.65); g.add(loaf);
    for (const z of [0.1, -1.4]) { const end = ball(0.11, 0xc8904a, 0, 0, z); end.scale.set(1, 1, 1.3); g.add(end); }
    for (let i = 0; i < 6; i++) {
      const s = bx(0.13, 0.025, 0.08, 0xa8732f, 0, 0.095, -0.1 - i * 0.22);
      s.rotation.y = 0.6;
      g.add(s);
    }
    g.userData.muzzle = new THREE.Vector3(0, 0, -1.45);
    g.userData.len = 1.6;
  },
  snowball(g) {
    const b = ball(0.07, 0xf2f8ff, 0, 0.02, -0.08); b.scale.set(1, 0.92, 1); g.add(b);
    g.add(ball(0.03, 0xffffff, 0.03, 0.06, -0.1));
    g.userData.muzzle = new THREE.Vector3(0, 0.02, -0.16);
    g.userData.len = 0.18;
  },
  slipper(g) {
    slipper(g, 1);
    g.userData.muzzle = new THREE.Vector3(0, 0, -0.15);
    g.userData.len = 0.3;
  },
  katana(g) { // wrapped handle, round guard, a long thin blade (in its own group so it can grow)
    g.add(cylZ(0.022, 0.24, 0x1a1a1a, 0, 0, 0.06, 6));
    for (let i = 0; i < 5; i++) g.add(bx(0.05, 0.012, 0.012, 0xc02030, 0, 0, 0.16 - i * 0.045));
    g.add(new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.015, 10), M(0xb08a3a)).rotateX(Math.PI / 2).translateY(0.0).translateZ(0));
    const blade = new THREE.Group(); blade.position.z = -0.07;
    blade.add(bx(0.012, 0.04, 0.72, 0xe8ecf2, 0, 0.005, -0.36));
    blade.add(bx(0.014, 0.008, 0.72, 0xffffff, 0, 0.026, -0.36, true)); // the edge catches the light
    const tip = bx(0.012, 0.03, 0.06, 0xe8ecf2, 0, 0.012, -0.74); tip.rotation.x = 0.3; blade.add(tip);
    g.add(blade);
    g.userData.katBlade = blade; g.userData.katLen = 0.72;
    g.userData.muzzle = new THREE.Vector3(0, 0.01, -0.82); g.userData.len = 0.95;
  },
  knife(g) { // standard combat knife
    g.add(bx(0.035, 0.05, 0.13, 0x2a2a2a, 0, 0, 0.02));
    g.add(bx(0.07, 0.015, 0.02, 0x555555, 0, 0.01, -0.05));
    const blade = bx(0.012, 0.045, 0.2, 0xd8dde4, 0, 0.012, -0.16); g.add(blade);
    g.add(bx(0.012, 0.02, 0.05, 0xd8dde4, 0, 0.03, -0.27));
    g.userData.muzzle = new THREE.Vector3(0, 0.01, -0.3);
    g.userData.len = 0.35;
  },
  slapper(g) { // toy hand on a stick
    g.add(cylZ(0.015, 0.6, 0xffe14d, 0, 0, -0.2, 6));
    const hand = new THREE.Group(); hand.position.set(0, 0, -0.55);
    hand.add(bx(0.16, 0.025, 0.14, 0xff7ab8, 0, 0, 0));
    for (let i = 0; i < 4; i++) hand.add(bx(0.03, 0.022, 0.1, 0xff7ab8, -0.06 + i * 0.04, 0, -0.11));
    const thumb = bx(0.03, 0.022, 0.08, 0xff7ab8, 0.1, 0, -0.02); thumb.rotation.y = -0.6; hand.add(thumb);
    g.add(hand);
    g.userData.hand = hand;
    g.userData.muzzle = new THREE.Vector3(0, 0, -0.7);
    g.userData.len = 0.8;
  },
  scythe(g) { // gunmetal pole with a rifle built in and a big glowing blade
    g.add(cylZ(0.022, 1.5, 0x3a3e46, 0, 0, -0.35, 6));
    g.add(bx(0.06, 0.09, 0.3, 0x2a2e34, 0, -0.02, 0.05)); // receiver
    g.add(bx(0.04, 0.1, 0.05, 0x1a1a1a, 0, -0.1, 0.12)); // grip
    g.add(cylZ(0.035, 0.18, 0x222222, 0, 0.07, 0, 6)); // scope
    g.add(bx(0.05, 0.03, 0.4, 0xc8a070, 0, 0, 0.3)); // tan wrap
    const blade = new THREE.Group(); blade.position.set(0, 0.03, -1.1);
    for (let i = 0; i < 6; i++) {
      const seg = bx(0.015, 0.08 - i * 0.008, 0.16, 0x9aa4b0, 0, 0.06 + i * 0.07, 0.02 + i * i * 0.012);
      seg.rotation.x = -0.25 - i * 0.18;
      blade.add(seg);
      const edge = bx(0.018, 0.012, 0.16, 0x3ee6c8, 0, 0.1 + i * 0.07, 0.02 + i * i * 0.012, true);
      edge.userData.noWrap = true;
      edge.rotation.x = -0.25 - i * 0.18;
      blade.add(edge);
    }
    g.add(blade);
    g.userData.blade = blade;
    g.userData.muzzle = new THREE.Vector3(0, 0, -1.12);
    g.userData.len = 1.7;
  },
  scythe_rifle(g) { // same thing folded: blade tucked back along the barrel
    g.add(cylZ(0.022, 1.1, 0x3a3e46, 0, 0, -0.45, 6));
    g.add(bx(0.06, 0.1, 0.35, 0x2a2e34, 0, -0.02, 0.0));
    g.add(bx(0.04, 0.1, 0.05, 0x1a1a1a, 0, -0.11, 0.08));
    g.add(cylZ(0.04, 0.26, 0x222222, 0, 0.09, -0.05, 6));
    g.add(bx(0.05, 0.12, 0.25, 0xc8a070, 0, -0.03, 0.28));
    const folded = bx(0.015, 0.06, 0.7, 0x9aa4b0, 0, -0.06, -0.45); g.add(folded);
    g.add(bx(0.018, 0.012, 0.7, 0x3ee6c8, 0, -0.09, -0.45, true));
    g.userData.muzzle = new THREE.Vector3(0, 0, -1.02);
    g.userData.len = 1.4;
  },
  bow(g) {
    // riser + two limbs bending back + string + a nocked arrow
    g.add(bx(0.03, 0.16, 0.04, 0x5a3a1a, 0, 0, 0));
    for (const sy of [1, -1]) {
      for (let i = 0; i < 3; i++) {
        const seg = bx(0.022, 0.13, 0.025, 0x8a5a2b, 0, sy * (0.12 + i * 0.12), 0.02 + i * i * 0.025);
        seg.rotation.x = sy * (0.25 + i * 0.25);
        g.add(seg);
      }
    }
    const string = new THREE.Group();
    for (const sy of [1, -1]) {
      const st = bx(0.004, 0.42, 0.004, 0xeeeeee, 0, sy * 0.2, 0.14, true);
      st.rotation.x = -sy * 0.22;
      string.add(st);
    }
    g.add(string);
    const arrow = new THREE.Group();
    arrow.add(cylZ(0.006, 0.7, 0xc8a070, 0, 0, -0.18, 4));
    const tip = bx(0.02, 0.02, 0.05, 0xdddddd, 0, 0, -0.55, true); tip.userData.noWrap = true; arrow.add(tip);
    arrow.add(bx(0.002, 0.03, 0.06, 0xff4fd8, 0, 0, 0.14));
    g.add(arrow);
    g.userData.arrow = arrow; g.userData.arrowTip = tip; g.userData.string = string;
    g.userData.muzzle = new THREE.Vector3(0, 0, -0.6);
    g.userData.len = 0.9;
  },
  cards(g) {
    // a fanned hand of five cards; faces get set from your actual hand
    const fan = [];
    for (let i = 0; i < 5; i++) {
      const c = new THREE.Mesh(new THREE.PlaneGeometry(0.08, 0.12), cardFace('back'));
      c.userData.noWrap = true;
      const a = (i - 2) * 0.22;
      c.position.set(Math.sin(a) * 0.09, Math.cos(a) * 0.09 - 0.07, -0.002 * i);
      c.rotation.z = -a;
      g.add(c);
      fan.push(c);
    }
    g.userData.fan = fan;
    g.userData.muzzle = new THREE.Vector3(0, 0.05, -0.1);
    g.userData.len = 0.2;
  },
  spoon(g) {
    g.add(cylZ(0.008, 0.16, 0xd8d8e0, 0, 0, -0.02, 5));
    const bowl = ball(0.035, 0xe8e8f0, 0, 0.005, -0.13); bowl.scale.set(0.8, 0.35, 1.2); g.add(bowl);
    g.userData.muzzle = new THREE.Vector3(0, 0, -0.17);
    g.userData.len = 0.22;
  },
};

// where a hat sits on each weapon (local position) and how tall it is. hand placed so every hat fits every weapon.
const HAT_AT = {
  ar: [[0, 0.1, 0.02], 0.12], smg: [[0, 0.055, 0.0], 0.1], shotgun: [[0, 0.05, 0.0], 0.11], minigun: [[0, 0.17, 0.05], 0.14],
  sniper: [[0, 0.16, -0.05], 0.13], chicken: [[0, 0.075, -0.5], 0.09], bowling: [[0, 0.17, -0.1], 0.15], banana: [[0, 0.185, 0.02], 0.1],
  revolver: [[0, 0.065, -0.02], 0.08], cig: [[0, 0.0125, 0.055], 0.04], blower: [[0, 0.22, 0.05], 0.14], popper: [[0, 0.07, 0.02], 0.07],
  reverse: [[0, 0.09, 0.02], 0.07], duck: [[0, 0.152, -0.072], 0.06], bread: [[0, 0.11, -0.3], 0.16], slipper: [[0, 0.068, -0.08], 0.07],
  spoon: [[0, 0.017, -0.13], 0.04], knife: [[0, 0.025, 0.04], 0.05], slapper: [[0, 0.0125, -0.55], 0.09], scythe: [[0, 0.47, -0.8], 0.14],
  scythe_rifle: [[0, 0.13, -0.05], 0.12], bow: [[0, 0.08, 0.0], 0.08], cards: [[0, 0.07, -0.004], 0.07],
  knife_kitchen: [[0, 0.0225, 0.04], 0.05], knife_bowie: [[0, 0.025, 0.04], 0.05], knife_cleaver: [[0, 0.1, -0.12], 0.07],
  knife_switch: [[0, 0.02, 0.03], 0.05], knife_karambit: [[0, 0.02, 0.01], 0.05], knife_butterfly: [[0, 0.016, 0.02], 0.05],
  slapper_foam: [[0, 0.03, -0.5], 0.1], slapper_paw: [[0, 0.06, -0.5], 0.1], bread_croissant: [[0, 0.15, -0.6], 0.15],
  p_chicken: [[0, 0.31, -0.28], 0.15], p_bowling: [[0, 0.45, 0], 0.3], p_duck: [[0, 0.418, -0.2], 0.2], p_slipper: [[0, 0.11, -0.13], 0.1], p_banana: [[0, 0.24, 0], 0.12],
};

// weapon skins: a different model for the same weapon
let skipTexture = null;
function skipTex() {
  if (skipTexture) return skipTexture;
  const c = document.createElement('canvas'); c.width = 32; c.height = 48;
  const x = c.getContext('2d');
  x.fillStyle = '#2a7a3a'; x.fillRect(0, 0, 32, 48); x.fillStyle = '#fff'; x.fillRect(3, 3, 26, 42);
  x.fillStyle = '#2a7a3a'; x.fillRect(5, 5, 22, 38);
  x.strokeStyle = '#fff'; x.lineWidth = 4; x.beginPath(); x.arc(16, 24, 8, 0, Math.PI * 2); x.stroke();
  x.beginPath(); x.moveTo(10, 30); x.lineTo(22, 18); x.stroke();
  skipTexture = new THREE.CanvasTexture(c); skipTexture.magFilter = THREE.NearestFilter;
  return skipTexture;
}
// skins for every weapon: alternate models. each belongs to its weapon and keeps that weapon's muzzle / moving parts
const SKIN_BUILD = {
  ar_bullpup(g) { // magazine behind the grip, everything stubby
    g.add(bx(0.075, 0.12, 0.62, 0x2a2a30, 0, 0, 0.02));
    g.add(cylZ(0.019, 0.26, 0x111111, 0, 0.015, -0.4));
    g.add(bx(0.05, 0.2, 0.08, 0x222222, 0, -0.15, 0.18));
    g.add(bx(0.05, 0.13, 0.06, 0x222222, 0, -0.12, -0.06));
    g.add(bx(0.05, 0.05, 0.3, 0x444450, 0, 0.09, -0.02));
    g.userData.muzzle = new THREE.Vector3(0, 0.015, -0.72); g.userData.len = 1.0;
  },
  ar_toy(g) { // a foam dart blaster: bright, chunky, orange tip
    g.add(bx(0.09, 0.14, 0.5, 0x4fd8ff, 0, 0, -0.05));
    g.add(cylZ(0.035, 0.36, 0xffe14d, 0, 0.02, -0.46));
    g.add(cylZ(0.04, 0.06, 0xff7a1a, 0, 0.02, -0.66, 8, true));
    g.add(bx(0.06, 0.18, 0.07, 0xff4fd8, 0, -0.14, 0.06));
    g.add(bx(0.07, 0.12, 0.26, 0xff4fd8, 0, -0.02, 0.32));
    g.add(bx(0.05, 0.06, 0.16, 0xffe14d, 0, 0.1, -0.08));
    g.userData.muzzle = new THREE.Vector3(0, 0.02, -0.72); g.userData.len = 1.0;
  },
  smg_uzi(g) {
    g.add(bx(0.07, 0.13, 0.26, 0x222228, 0, 0, -0.06));
    g.add(cylZ(0.018, 0.12, 0x111111, 0, 0.02, -0.26));
    g.add(bx(0.045, 0.3, 0.05, 0x111111, 0, -0.18, -0.02));
    g.add(bx(0.06, 0.03, 0.2, 0x444450, 0, 0.08, -0.06));
    g.userData.muzzle = new THREE.Vector3(0, 0.02, -0.37); g.userData.len = 0.6;
  },
  shotgun_double(g) { // side by side, all wood and brass
    for (const sx of [-1, 1]) g.add(cylZ(0.024, 0.62, 0x2a2a2a, sx * 0.026, 0.02, -0.36));
    g.add(bx(0.11, 0.08, 0.16, 0xb08a3a, 0, 0, -0.02));
    g.add(bx(0.08, 0.13, 0.32, 0x6b3a1a, 0, -0.04, 0.22));
    g.add(bx(0.1, 0.05, 0.3, 0x6b3a1a, 0, -0.035, -0.26));
    g.userData.muzzle = new THREE.Vector3(0, 0.02, -0.74); g.userData.len = 1.1;
  },
  minigun_gatling(g) { // old brass gatling with a crank
    const barrels = new THREE.Group(); barrels.position.set(0, 0, -0.35);
    for (let i = 0; i < 8; i++) { const a = (i / 8) * Math.PI * 2; barrels.add(cylZ(0.014, 0.62, 0xb08a3a, Math.cos(a) * 0.055, Math.sin(a) * 0.055, -0.1, 5)); }
    barrels.add(cylZ(0.08, 0.05, 0x8a6a2a, 0, 0, -0.34, 8)); barrels.add(cylZ(0.08, 0.05, 0x8a6a2a, 0, 0, 0.12, 8));
    g.add(barrels); g.userData.barrels = barrels;
    g.add(bx(0.16, 0.18, 0.3, 0x5a4a2a, 0, 0, 0.06));
    g.add(bx(0.03, 0.03, 0.16, 0xb08a3a, 0.12, 0.02, 0.1)); g.add(bx(0.03, 0.12, 0.03, 0xb08a3a, 0.14, -0.04, 0.16)); // crank
    g.add(bx(0.06, 0.14, 0.08, 0x3a2a1a, 0, 0.14, 0.04));
    g.userData.muzzle = new THREE.Vector3(0, 0, -0.75); g.userData.len = 1.0;
  },
  sniper_musket(g) { // long wooden musket with a bayonet
    g.add(bx(0.06, 0.09, 1.0, 0x6b3a1a, 0, -0.01, -0.3));
    g.add(cylZ(0.02, 1.2, 0x555555, 0, 0.04, -0.85));
    g.add(bx(0.07, 0.16, 0.34, 0x6b3a1a, 0, -0.05, 0.38));
    g.add(bx(0.008, 0.02, 0.28, 0xdddddd, 0, -0.02, -1.55, true));
    g.add(bx(0.04, 0.05, 0.06, 0xb08a3a, 0, 0.06, 0.05));
    g.userData.muzzle = new THREE.Vector3(0, 0.04, -1.48); g.userData.len = 1.8;
  },
  revolver_flint(g) { // flintlock pistol
    g.add(cylZ(0.022, 0.26, 0x555555, 0, 0.03, -0.17));
    g.add(bx(0.05, 0.06, 0.24, 0x6b3a1a, 0, 0.01, -0.1));
    g.add(bx(0.02, 0.05, 0.04, 0x888888, 0, 0.07, 0.02));
    const grip = bx(0.05, 0.15, 0.07, 0x6b3a1a, 0, -0.06, 0.08); grip.rotation.x = 0.6; g.add(grip);
    g.add(ball(0.03, 0xb08a3a, 0, -0.12, 0.13));
    g.userData.muzzle = new THREE.Vector3(0, 0.03, -0.29); g.userData.len = 0.35;
  },
  chicken_turkey(g) {
    g.add(cylZ(0.1, 0.8, 0x6b4a2a, 0, 0, -0.1, 8));
    g.add(cylZ(0.11, 0.05, 0xb08a3a, 0, 0, -0.5, 8));
    for (let i = 0; i < 5; i++) { const f = bx(0.05, 0.2, 0.02, [0xc02030, 0xff7a1a, 0x8a5a2b, 0xffe14d, 0xc02030][i], (i - 2) * 0.05, 0.16, 0.28); f.rotation.z = (i - 2) * 0.25; g.add(f); }
    g.add(bx(0.06, 0.14, 0.06, 0x333333, 0, -0.14, 0.05));
    g.userData.muzzle = new THREE.Vector3(0, 0, -0.62); g.userData.len = 0.9;
  },
  bowling_cannon(g) { // pirate hand cannon
    g.add(cylZ(0.12, 0.7, 0x2a2a2a, 0, 0, -0.18, 8));
    g.add(cylZ(0.14, 0.06, 0x2a2a2a, 0, 0, -0.52, 8));
    g.add(ball(0.12, 0x2a2a2a, 0, 0, 0.16));
    g.add(bx(0.06, 0.18, 0.06, 0x6b3a1a, 0, -0.16, 0.02));
    g.add(bx(0.02, 0.02, 0.06, 0xff7a1a, 0, 0.12, 0.12, true)); // fuse
    g.userData.muzzle = new THREE.Vector3(0, 0, -0.6); g.userData.len = 0.9;
  },
  banana_bunch(g) {
    g.add(cylZ(0.05, 0.5, 0x6b4a2a, 0, 0, -0.1, 6));
    for (let i = 0; i < 4; i++) { const b = cylZ(0.03, 0.26, 0xffe135, (i - 1.5) * 0.04, 0.07, -0.25); b.rotation.x = -0.3 - i * 0.05; g.add(b); }
    g.add(bx(0.05, 0.14, 0.06, 0x333333, 0, -0.1, 0.05));
    g.userData.muzzle = new THREE.Vector3(0, 0, -0.36); g.userData.len = 0.6;
  },
  bow_compound(g) { // cams, cables, a sight. same string + arrow as the normal bow
    g.add(bx(0.035, 0.22, 0.05, 0x2a2a30, 0, 0, 0));
    for (const sy of [1, -1]) {
      const limb = bx(0.03, 0.26, 0.03, 0x111111, 0, sy * 0.24, 0.05); limb.rotation.x = sy * 0.35; g.add(limb);
      const cam = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.02, 10), M(0xb0b0b8)); cam.rotation.z = Math.PI / 2; cam.position.set(0, sy * 0.36, 0.1); g.add(cam);
    }
    g.add(bx(0.01, 0.06, 0.08, 0x7dff4f, 0.03, 0.06, -0.05, true));
    const string = new THREE.Group();
    for (const sy of [1, -1]) { const st = bx(0.004, 0.36, 0.004, 0xeeeeee, 0, sy * 0.18, 0.14, true); st.rotation.x = -sy * 0.12; string.add(st); }
    g.add(string);
    const arrow = new THREE.Group();
    arrow.add(cylZ(0.006, 0.7, 0x333333, 0, 0, -0.18, 4));
    const tip = bx(0.02, 0.02, 0.05, 0xdddddd, 0, 0, -0.55, true); tip.userData.noWrap = true; arrow.add(tip);
    arrow.add(bx(0.002, 0.03, 0.06, 0x4fd8ff, 0, 0, 0.14));
    g.add(arrow);
    g.userData.arrow = arrow; g.userData.arrowTip = tip; g.userData.string = string;
    g.userData.muzzle = new THREE.Vector3(0, 0, -0.6); g.userData.len = 0.9;
  },
  cig_cigar(g) {
    g.add(cylZ(0.022, 0.22, 0x6b3a1a, 0, 0, 0, 8));
    g.add(cylZ(0.024, 0.03, 0xc02030, 0, 0, 0.06, 8));
    const tip = cylZ(0.023, 0.02, 0xff4a1a, 0, 0, -0.115, 8, true);
    tip.userData.noWrap = true; g.add(tip); g.userData.tip = tip;
    g.userData.muzzle = new THREE.Vector3(0, 0, -0.11); g.userData.len = 0.18;
  },
  blower_dryer(g) { // a hair dryer, obviously
    g.add(cylZ(0.08, 0.36, 0xff9ad5, 0, 0, -0.2, 10));
    g.add(cylZ(0.06, 0.12, 0xff4fd8, 0, 0, -0.42, 10));
    g.add(bx(0.06, 0.24, 0.07, 0xff9ad5, 0, -0.16, 0.0));
    g.add(bx(0.07, 0.03, 0.04, 0xffffff, 0, -0.06, -0.06));
    g.userData.muzzle = new THREE.Vector3(0, -0.03, -0.87); g.userData.len = 1.0;
  },
  popper_bottle(g) { // champagne
    g.add(cylZ(0.05, 0.2, 0x2a5a2a, 0, 0, 0, 10));
    g.add(cylZ(0.025, 0.1, 0x2a5a2a, 0, 0, -0.14, 8));
    g.add(cylZ(0.028, 0.05, 0xffd21a, 0, 0, -0.18, 8));
    g.add(bx(0.07, 0.07, 0.08, 0xffffff, 0, 0, 0.02));
    g.userData.muzzle = new THREE.Vector3(0, 0, -0.21); g.userData.len = 0.3;
  },
  reverse_skip(g) {
    const card = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.18, 0.004), new THREE.MeshBasicMaterial({ map: skipTex() }));
    card.rotation.x = -0.2; g.add(card); g.userData.card = card;
    g.userData.muzzle = new THREE.Vector3(0, 0.05, -0.05); g.userData.len = 0.2;
  },
  snowball_ice(g) {
    const c = bx(0.12, 0.12, 0.12, 0xbfe8ff, 0, 0.02, -0.08); c.rotation.set(0.4, 0.6, 0.2); g.add(c);
    g.userData.muzzle = new THREE.Vector3(0, 0.02, -0.16); g.userData.len = 0.18;
  },
  spoon_ladle(g) {
    g.add(cylZ(0.01, 0.2, 0xc8c8d0, 0, 0, -0.02, 5));
    const bowl = ball(0.06, 0xd8d8e0, 0, -0.02, -0.15); bowl.scale.set(1, 0.6, 1); g.add(bowl);
    g.userData.muzzle = new THREE.Vector3(0, 0, -0.17); g.userData.len = 0.22;
  },
  slipper_croc(g) { // a croc, holes and all
    g.add(bx(0.13, 0.07, 0.3, 0x7dff4f, 0, 0, -0.02));
    g.add(ball(0.07, 0x7dff4f, 0, 0.03, -0.14));
    for (let i = 0; i < 6; i++) g.add(bx(0.02, 0.01, 0.02, 0x3a8a2a, (i % 3 - 1) * 0.04, 0.04, -0.12 + Math.floor(i / 3) * 0.06));
    g.add(bx(0.13, 0.02, 0.04, 0x3a8a2a, 0, 0.04, 0.1));
    g.userData.muzzle = new THREE.Vector3(0, 0, -0.15); g.userData.len = 0.3;
  },
  scythe_reaper(g) { // black wood, a bone-white blade
    g.add(cylZ(0.022, 1.6, 0x1a1a1a, 0, 0, -0.3, 6));
    const blade = new THREE.Group(); blade.position.set(0, 0.05, -1.05);
    for (let i = 0; i < 6; i++) { const seg = bx(0.015, 0.08 - i * 0.008, 0.16, 0xe8e4d8, 0, 0.06 + i * 0.07, 0.02 + i * i * 0.012); seg.rotation.x = -0.25 - i * 0.18; blade.add(seg); }
    g.add(blade); g.userData.blade = blade;
    g.add(ball(0.05, 0xe8e4d8, 0, 0, 0.5));
    g.userData.muzzle = new THREE.Vector3(0, 0, -1.12); g.userData.len = 1.7;
  },
};

const MODEL_BUILD = {
  ...SKIN_BUILD,
  knife_kitchen(g) {
    g.add(bx(0.03, 0.045, 0.12, 0x2a1a10, 0, 0, 0.02));
    g.add(bx(0.008, 0.06, 0.24, 0xe8ecef, 0, 0.012, -0.16));
    g.userData.muzzle = new THREE.Vector3(0, 0.01, -0.29); g.userData.len = 0.36;
  },
  knife_bowie(g) {
    g.add(bx(0.04, 0.05, 0.13, 0x6b3a1a, 0, 0, 0.03));
    g.add(bx(0.09, 0.02, 0.025, 0xc8a050, 0, 0.01, -0.05));
    g.add(bx(0.014, 0.06, 0.27, 0xd0d6dc, 0, 0.015, -0.19));
    const tipB = bx(0.014, 0.03, 0.06, 0xd0d6dc, 0, 0.035, -0.34); tipB.rotation.x = 0.5; g.add(tipB);
    g.userData.muzzle = new THREE.Vector3(0, 0.02, -0.36); g.userData.len = 0.45;
  },
  knife_cleaver(g) {
    g.add(cylZ(0.02, 0.12, 0x2a1a10, 0, 0, 0.03, 6));
    g.add(bx(0.01, 0.12, 0.2, 0xc8ccd0, 0, 0.04, -0.12));
    g.userData.muzzle = new THREE.Vector3(0, 0.05, -0.22); g.userData.len = 0.33;
  },
  knife_switch(g) {
    g.add(bx(0.03, 0.04, 0.13, 0x111111, 0, 0, 0.02));
    g.add(bx(0.032, 0.012, 0.13, 0xc8a050, 0, 0.022, 0.02));
    // the blade pivots on a pin at the front of the handle so it can flick out
    const pin = new THREE.Group(); pin.position.set(0, 0.01, -0.045); g.add(pin);
    pin.add(bx(0.01, 0.035, 0.15, 0xe0e4ea, 0, 0, -0.075));
    g.userData.flipBlade = pin;
    g.userData.muzzle = new THREE.Vector3(0, 0.01, -0.2); g.userData.len = 0.3;
  },
  knife_karambit(g) {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.03, 0.008, 4, 8), M(0x222222)); ring.rotation.y = Math.PI / 2; ring.position.set(0, 0, 0.09); g.add(ring);
    g.userData.pivot = new THREE.Vector3(0, 0, 0.09); // your finger goes through the ring: it spins round this
    g.add(bx(0.03, 0.04, 0.11, 0x2a2a2a, 0, 0, 0.01));
    for (let i = 0; i < 5; i++) { const s2 = bx(0.01, 0.03, 0.045, 0xd8dde4, 0, -0.01 - i * i * 0.006, -0.06 - i * 0.04); s2.rotation.x = 0.15 + i * 0.22; g.add(s2); }
    g.userData.muzzle = new THREE.Vector3(0, -0.1, -0.25); g.userData.len = 0.33;
  },
  knife_butterfly(g) {
    // each handle hangs off a hinge pin at the base of the blade, so it can swing round the blade like a real balisong
    const hinge = (x) => { const p = new THREE.Group(); p.position.set(x, 0, -0.045); g.add(p); return p; };
    const p1 = hinge(0.012), p2 = hinge(-0.012);
    p1.add(bx(0.014, 0.03, 0.13, 0x8a8f99, 0, 0, 0.065));
    p2.add(bx(0.014, 0.03, 0.13, 0x8a8f99, 0, 0, 0.065));
    for (let i = 0; i < 4; i++) p1.add(bx(0.018, 0.004, 0.01, 0x333333, 0.004, 0.016, 0.025 + i * 0.03)); // holes in the safe handle
    g.add(bx(0.008, 0.035, 0.15, 0xe8ecf0, 0, 0.005, -0.12));
    g.userData.handles = [p1, p2];
    g.userData.muzzle = new THREE.Vector3(0, 0.005, -0.2); g.userData.len = 0.33;
  },
  slapper_foam(g) {
    g.add(cylZ(0.015, 0.5, 0x4fd8ff, 0, 0, -0.18, 6));
    g.add(bx(0.2, 0.06, 0.18, 0x3070ff, 0, 0, -0.5));
    g.add(bx(0.05, 0.05, 0.22, 0x3070ff, 0, 0, -0.69));
    g.add(bx(0.18, 0.005, 0.1, 0xffffff, 0, 0.033, -0.5, true));
    g.userData.muzzle = new THREE.Vector3(0, 0, -0.8); g.userData.len = 0.85;
  },
  slapper_paw(g) {
    g.add(cylZ(0.018, 0.55, 0x6b3a1a, 0, 0, -0.18, 6));
    const palm = ball(0.11, 0x5a3a20, 0, 0, -0.52); palm.scale.set(1.2, 0.5, 1); g.add(palm);
    for (let i = 0; i < 4; i++) { const claw = ball(0.03, 0x2a1a10, -0.07 + i * 0.045, 0, -0.64); claw.scale.set(1, 0.6, 1.4); g.add(claw); }
    const pad = ball(0.05, 0xd8b090, 0, 0.03, -0.5); pad.scale.set(1.3, 0.4, 1); g.add(pad);
    g.userData.muzzle = new THREE.Vector3(0, 0, -0.7); g.userData.len = 0.8;
  },
  bread_croissant(g) {
    for (let i = 0; i < 7; i++) {
      const r = 0.09 + Math.sin((i / 6) * Math.PI) * 0.08;
      const seg = ball(r, i % 2 ? 0xd9a35b : 0xc8904a, Math.sin((i / 6) * Math.PI) * -0.18, 0, -0.1 - i * 0.2);
      seg.scale.set(1, 0.8, 1.3);
      g.add(seg);
    }
    g.userData.muzzle = new THREE.Vector3(0, 0, -1.3); g.userData.len = 1.4;
  },
};

// iron sights: a rear notch + front post (glowing tip) on top of the gun, at one height, so the line of sight
// runs over the top of the gun. ADS puts that line on the centre of the screen and the gun hangs below it.
const SIGHTS = { ar: 'iron', smg: 'iron', revolver: 'iron', banana: 'iron', shotgun: 'bead' };
const SIGHT_DOT = 0x7dff4f;
function addSights(id, g) {
  const kind = SIGHTS[id];
  if (!kind || !g.userData.muzzle) return;
  g.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(g);
  const mz = g.userData.muzzle;
  const ys = box.max.y + 0.014; // line of sight, just above the highest part
  const zf = mz.z + 0.05;
  const zr = Math.max(mz.z * 0.55, Math.min(box.max.z - 0.05, mz.z * 0.08)); // over the receiver, not the stock
  const dark = 0x1a1a1a;
  // front post (+ the bright tip you put on the target)
  const postH = Math.max(0.01, ys - mz.y);
  if (kind === 'iron') g.add(bx(0.007, postH, 0.008, dark, 0, mz.y + postH / 2 - 0.004, zf));
  const tip = bx(kind === 'bead' ? 0.012 : 0.008, kind === 'bead' ? 0.012 : 0.008, kind === 'bead' ? 0.012 : 0.008, SIGHT_DOT, 0, ys - 0.004, zf, true);
  tip.userData.noWrap = true;
  g.add(tip);
  if (kind === 'iron') { // rear notch: two ears with a gap the front post sits in
    for (const sx of [-1, 1]) g.add(bx(0.008, 0.022, 0.012, dark, sx * 0.011, ys - 0.007, zr));
    g.add(bx(0.03, 0.007, 0.012, dark, 0, ys - 0.016, zr));
  } else { // shotgun: a vent rib along the top to sight down
    g.add(bx(0.012, 0.005, Math.abs(zf - zr), dark, 0, ys - 0.008, (zf + zr) / 2));
  }
  g.userData.sight = { y: ys - 0.004, z: zr };
}

export function buildWeapon(id, skin) {
  const g = new THREE.Group();
  const model = skin && skin[3];
  const variant = model && MODEL_BUILD[model] && COSMETICS.model[model] && COSMETICS.model[model].weapon === id;
  (variant ? MODEL_BUILD[model] : WB[id] || WB.cig)(g);
  g.userData.model = variant ? model : 'default';
  g.userData.hatAt = HAT_AT[variant ? model : id];
  const glb = variant ? null : fitted('w_' + id, { alignZ: true, size: g.userData.len, zOffset: g.userData.muzzle.z / 2 });
  if (glb) delete g.userData.hatAt; // a generated model has its own shape: fall back to measuring it
  if (glb) {
    for (const c of [...g.children]) if (c !== g.userData.tip) g.remove(c);
    if (g.userData.tip) g.userData.tip.visible = true;
    g.add(glb);
  }
  if (!glb) addSights(id, g);
  applySkin(g, skin);
  return g;
}

// ------------------------------------------------------------ characters: janky mannequins
const SKIN = 0xe6cba2, JOINT = 0xbf9f74;
function limb(r0, r1, len, color, y) { // vertical cylinder hanging down from its pivot
  const m = new THREE.Mesh(new THREE.CylinderGeometry(r0, r1, len, 6), M(color));
  m.position.y = y;
  return m;
}
// ------------------------------------------------------------ hair (sits on the egg head; head group local, top of the egg ~y 0.31)
function addHair(H, lk) {
  const style = lk.hair || 'none';
  if (style === 'none' || lk.head === 'helmet') return;
  const hc = new THREE.Color(lk.hairColor || '#1a1a1a').getHex();
  const cap = (cover = 0.45, sx = 0.9, sy = 1.18, r = 0.15) => {
    const m = new THREE.Mesh(new THREE.SphereGeometry(r, 10, 6, 0, Math.PI * 2, 0, Math.PI * cover), M(hc));
    m.scale.set(sx, sy, 1.0); m.position.y = 0.15; H.add(m); return m;
  };
  switch (style) {
    case 'short': cap(0.42); break;
    case 'bowl': cap(0.56, 0.95, 1.2, 0.155); H.add(bx(0.24, 0.04, 0.04, hc, 0, 0.215, -0.135)); break;
    case 'spiky': cap(0.4); for (let i = 0; i < 7; i++) { const a = (i / 7) * Math.PI * 2; const k = new THREE.Mesh(new THREE.ConeGeometry(0.04, 0.14, 5), M(hc)); k.position.set(Math.cos(a) * 0.07, 0.31, Math.sin(a) * 0.07); k.rotation.set(Math.sin(a) * 0.5, 0, -Math.cos(a) * 0.5); H.add(k); } break;
    case 'mohawk': H.add(bx(0.035, 0.13, 0.3, hc, 0, 0.33, 0.01)); break;
    case 'long': cap(0.45); H.add(bx(0.25, 0.34, 0.06, hc, 0, 0.08, 0.12)); for (const sx of [-1, 1]) H.add(bx(0.04, 0.26, 0.12, hc, sx * 0.12, 0.1, 0.02)); break;
    case 'ponytail': cap(0.45); H.add(ball(0.05, hc, 0, 0.22, 0.15)); { const t = cylZ(0.035, 0.2, hc, 0, 0.12, 0.2); t.rotation.x = 1.1; H.add(t); } break;
    case 'bun': cap(0.45); H.add(ball(0.07, hc, 0, 0.32, 0.06)); break;
    case 'afro': { const a = ball(0.21, hc, 0, 0.22, 0.03); a.scale.set(1.05, 0.95, 1.05); H.add(a); break; }
  }
}

// ------------------------------------------------------------ character accessories (head / face / back)
function addAccessories(ch, look, c) {
  if (!look) return;
  const H = ch.head, Bd = ch.body;
  const at = (parent, m) => { parent.add(m); return m; };
  const y0 = 0.3; // top of the egg head (head group local)
  switch (look.head) {
    case 'cap': { const d = new THREE.Mesh(new THREE.SphereGeometry(0.15, 8, 4, 0, Math.PI * 2, 0, Math.PI / 2), M(c)); d.position.y = y0 - 0.06; H.add(d); at(H, bx(0.22, 0.02, 0.14, c, 0, y0 - 0.06, -0.15)); break; }
    case 'beanie': { const d = new THREE.Mesh(new THREE.SphereGeometry(0.155, 8, 4, 0, Math.PI * 2, 0, Math.PI / 2), M(0x2a4a8a)); d.position.y = y0 - 0.07; d.scale.y = 1.3; H.add(d); at(H, ball(0.045, 0xffffff, 0, y0 + 0.13, 0)); break; }
    case 'cowboy': { const b = cylZ(0.26, 0.02, 0x8a5a2b, 0, y0 - 0.04, 0, 10); b.rotation.x = 0; b.geometry.rotateX(Math.PI / 2); H.add(b); at(H, new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.13, 0.14, 8), M(0x8a5a2b))).position.y = y0 + 0.04; break; }
    case 'party': { const k = new THREE.Mesh(new THREE.ConeGeometry(0.1, 0.3, 8), M(0xff4fd8)); k.position.y = y0 + 0.1; H.add(k); at(H, ball(0.035, 0xffe14d, 0, y0 + 0.26, 0)); break; }
    case 'headphones': { const t = new THREE.Mesh(new THREE.TorusGeometry(0.16, 0.02, 4, 10, Math.PI), M(0x222222)); t.position.y = 0.16; H.add(t); for (const sx of [-1, 1]) at(H, bx(0.06, 0.1, 0.1, c, sx * 0.15, 0.13, 0)); break; }
    case 'bucket': { H.add(new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.16, 0.12, 8), M(0xc8b48a))).children; const m = H.children[H.children.length - 1]; m.position.y = y0 - 0.02; at(H, new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.015, 10), M(0xc8b48a))).position.y = y0 - 0.08; break; }
    case 'crown': { const r = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.08, 10, 1, true), M(0xffc21a)); r.position.y = y0; H.add(r); for (let i = 0; i < 5; i++) { const a = (i / 5) * Math.PI * 2; const sp = new THREE.Mesh(new THREE.ConeGeometry(0.03, 0.09, 4), M(0xffc21a)); sp.position.set(Math.cos(a) * 0.11, y0 + 0.08, Math.sin(a) * 0.11); H.add(sp); } break; }
    case 'helmet': { const d = ball(0.2, c, 0, 0.16, 0); d.scale.set(1, 1.05, 1.05); H.add(d); at(H, bx(0.26, 0.07, 0.03, 0x111122, 0, 0.17, -0.19, true)); break; }
    case 'hardhat': { const d = new THREE.Mesh(new THREE.SphereGeometry(0.16, 8, 4, 0, Math.PI * 2, 0, Math.PI / 2), M(0xffd21a)); d.position.y = y0 - 0.05; H.add(d); at(H, new THREE.Mesh(new THREE.CylinderGeometry(0.21, 0.21, 0.015, 10), M(0xffd21a))).position.y = y0 - 0.05; break; }
    case 'icepack': at(H, bx(0.14, 0.04, 0.14, 0x6ad0ff, 0, y0 + 0.01, 0)); break;
  }
  const fz = -0.15; // front of the face
  switch (look.face) {
    case 'shades': at(H, bx(0.22, 0.05, 0.02, 0x111111, 0, 0.17, fz, true)); at(H, bx(0.26, 0.015, 0.015, 0x111111, 0, 0.19, fz)); break;
    case 'mustache': at(H, bx(0.12, 0.025, 0.02, 0x4a2a10, 0, 0.09, fz + 0.01)); break;
    case 'clown': at(H, ball(0.035, 0xff2020, 0, 0.12, fz - 0.01, true)); break;
    case 'eyepatch': at(H, bx(0.06, 0.05, 0.02, 0x111111, 0.05, 0.17, fz, true)); at(H, bx(0.28, 0.012, 0.012, 0x111111, 0, 0.19, fz + 0.01)); break;
    case 'bandana': at(H, bx(0.22, 0.09, 0.03, 0xc02030, 0, 0.07, fz + 0.01)); break;
    case 'visor': at(H, bx(0.24, 0.05, 0.02, 0x3ee6c8, 0, 0.17, fz - 0.005, true)); break;
  }
  // back stuff hangs off the upper back (chest back surface ~z 0.15) and is strapped over the shoulders
  const thick = look.top === 'jacket' || look.top === 'suit' || look.top === 'hoodie' ? 0.03 : 0;
  const bk = 0.15 + thick;
  const straps = (col) => { for (const sx of [-1, 1]) { at(Bd, bx(0.045, 0.025, 0.32, col, sx * 0.11, 1.52, 0.0)); at(Bd, bx(0.045, 0.3, 0.025, col, sx * 0.11, 1.37, -0.16 - thick)); } };
  switch (look.back) {
    case 'backpack':
      at(Bd, bx(0.3, 0.38, 0.15, c, 0, 1.3, bk + 0.075));
      at(Bd, bx(0.31, 0.12, 0.16, 0x222222, 0, 1.44, bk + 0.08));
      at(Bd, bx(0.2, 0.12, 0.05, 0x222222, 0, 1.2, bk + 0.16));
      straps(0x222222);
      break;
    case 'cape': case 'voidcape': {
      const voidc = look.back === 'voidcape';
      const piv = new THREE.Group(); piv.position.set(0, 1.52, bk - 0.02); Bd.add(piv);
      piv.add(bx(0.4, 0.04, 0.05, voidc ? 0xff00dc : 0xffc21a, 0, 0, -0.02, voidc)); // clasp across the shoulders
      piv.add(bx(0.5, 0.95, 0.025, voidc ? 0x2a002a : 0xc02030, 0, -0.48, 0.02));
      if (voidc) piv.add(bx(0.52, 0.05, 0.03, 0xff00dc, 0, -0.95, 0.02, true));
      piv.rotation.x = 0.1;
      ch.cape = piv;
      break;
    }
    case 'wings': {
      at(Bd, bx(0.14, 0.2, 0.05, 0xdddddd, 0, 1.36, bk + 0.02));
      ch.wings = [];
      for (const sx of [-1, 1]) {
        const piv = new THREE.Group(); piv.position.set(sx * 0.06, 1.42, bk + 0.04); Bd.add(piv);
        const w1 = bx(0.5, 0.22, 0.025, 0xffffff, sx * 0.27, 0.04, 0); w1.rotation.z = sx * 0.35; piv.add(w1);
        const w2 = bx(0.36, 0.14, 0.022, 0xe8e8ff, sx * 0.22, -0.1, 0.01); w2.rotation.z = sx * 0.1; piv.add(w2);
        piv.rotation.y = sx * -0.25;
        ch.wings.push(piv);
      }
      break;
    }
    case 'jetpack':
      at(Bd, bx(0.26, 0.34, 0.04, 0x55595f, 0, 1.33, bk + 0.02));
      for (const sx of [-1, 1]) {
        const t = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 0.4, 8), M(0x8a8f99)); t.position.set(sx * 0.09, 1.3, bk + 0.1); Bd.add(t);
        const n = new THREE.Mesh(new THREE.ConeGeometry(0.06, 0.1, 8), M(0xff6a1a, true)); n.position.set(sx * 0.09, 1.05, bk + 0.1); n.rotation.x = Math.PI; Bd.add(n);
      }
      straps(0x333333);
      break;
  }
}

export function buildCharacter(color, look) {
  const root = new THREE.Group();
  const body = new THREE.Group();
  root.add(body);
  const c = new THREE.Color(color).getHex();
  const legL = new THREE.Group(), legR = new THREE.Group(), kneeL = new THREE.Group(), kneeR = new THREE.Group();
  const head = new THREE.Group(), arm = new THREE.Group(), armL = new THREE.Group(), slot = new THREE.Group();
  const jank = { tilt: (Math.random() - 0.5) * 0.5, shoulder: (Math.random() - 0.5) * 0.12, lean: (Math.random() - 0.5) * 0.12, wrongKnee: Math.random() < 0.25 };
  const glb = fitted('player', { feet: true, byHeight: true, size: 1.85 });
  if (glb) {
    body.add(glb);
    body.add(bx(0.5, 0.15, 0.5, c, 0, 1.95, 0));
  } else {
    const lk = look || {};
    const SK = lk.skin ? new THREE.Color(lk.skin).getHex() : SKIN;
    const JT = new THREE.Color(SK).multiplyScalar(0.82).getHex();
    const TOP = lk.topColor ? new THREE.Color(lk.topColor).getHex() : c;
    const BOT = lk.bottomColor ? new THREE.Color(lk.bottomColor).getHex() : c;
    const top = lk.top || 'tank', bottom = lk.bottom || 'shorts';
    const sleeves = top === 'tee' ? 'short' : top === 'hoodie' || top === 'jacket' || top === 'suit' ? 'long' : null;
    // legs: hip -> thigh -> knee -> shin -> foot
    for (const [leg, knee, sx] of [[legL, kneeL, -1], [legR, kneeR, 1]]) {
      leg.position.set(0.1 * sx, 0.92, 0);
      leg.add(ball(0.075, JT));
      leg.add(limb(0.07, 0.058, 0.42, SK, -0.22));
      if (bottom === 'pants') leg.add(limb(0.082, 0.07, 0.44, BOT, -0.22));
      knee.position.y = -0.44;
      knee.add(ball(0.062, JT));
      knee.add(limb(0.056, 0.045, 0.4, SK, -0.21));
      if (bottom === 'pants') knee.add(limb(0.068, 0.058, 0.38, BOT, -0.2));
      knee.add(bx(0.1, 0.06, 0.22, bottom === 'pants' ? 0x222222 : SK, 0, -0.43, -0.05));
      leg.add(knee);
      body.add(leg);
    }
    if (bottom === 'skirt') { const sk = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.28, 0.36, 8), M(BOT)); sk.position.y = 0.88; body.add(sk); }
    else body.add(bx(0.34, 0.18, 0.23, BOT, 0, 0.98, 0)); // shorts / top of the pants
    body.add(limb(0.1, 0.12, 0.16, top === 'none' || top === 'tank' ? SK : TOP, 1.13)); // waist
    const chest = ball(0.2, SK, 0, 1.34, 0); chest.scale.set(1.2, 1.1, 0.72); body.add(chest);
    if (top === 'tank') { const sash = bx(0.09, 0.56, 0.31, TOP, 0, 1.31, 0); sash.rotation.z = 0.65; body.add(sash); }
    if (top === 'tee' || top === 'hoodie') { const sh = ball(0.215, TOP, 0, 1.34, 0); sh.scale.set(1.2, 1.1, 0.74); body.add(sh); }
    if (top === 'hoodie') {
      const hood = ball(0.13, TOP, 0, 1.58, 0.13); hood.scale.set(1.2, 0.8, 0.8); body.add(hood);
      body.add(bx(0.22, 0.1, 0.03, new THREE.Color(TOP).multiplyScalar(0.8).getHex(), 0, 1.2, -0.155)); // front pocket
      for (const sx of [-1, 1]) body.add(bx(0.012, 0.12, 0.012, 0xffffff, sx * 0.04, 1.42, -0.16));
    }
    if (top === 'jacket' || top === 'suit') {
      const sh = ball(0.208, top === 'suit' ? 0xffffff : 0xf0f0f0, 0, 1.34, 0); sh.scale.set(1.2, 1.1, 0.73); body.add(sh); // shirt under
      for (const sx of [-1, 1]) { // the two front panels + back
        const pnl = bx(0.17, 0.5, 0.05, TOP, sx * (top === 'suit' ? 0.07 : 0.11), 1.3, -0.135); pnl.rotation.y = sx * 0.25; body.add(pnl);
        const lap = bx(0.05, 0.2, 0.03, new THREE.Color(TOP).multiplyScalar(0.75).getHex(), sx * 0.06, 1.45, -0.16); lap.rotation.z = sx * 0.4; body.add(lap);
      }
      body.add(bx(0.42, 0.5, 0.06, TOP, 0, 1.3, 0.13));
      for (const sx of [-1, 1]) body.add(bx(0.07, 0.5, 0.26, TOP, sx * 0.215, 1.3, 0));
      if (top === 'suit') body.add(bx(0.04, 0.26, 0.02, 0xc02030, 0, 1.36, -0.165)); // tie
    }
    body.add(limb(0.045, 0.05, 0.12, SK, 1.57));
    head.position.set(0, 1.62, 0);
    const egg = ball(0.14, SK, 0, 0.14, 0); egg.scale.set(0.85, 1.22, 0.95); head.add(egg);
    head.add(bx(0.005, 0.2, 0.3, JT, 0, 0.14, 0)); // seam where the mold met
    head.rotation.z = jank.tilt;
    body.add(head);
    for (const sx of [-1, 1]) body.add(ball(0.068, sleeves ? TOP : JT, 0.25 * sx, 1.45 + (sx > 0 ? jank.shoulder : 0), 0));
    // right arm holds the gun
    arm.add(cylZ(0.048, 0.28, SK, 0, 0, -0.14));
    if (sleeves) arm.add(cylZ(0.058, sleeves === 'long' ? 0.29 : 0.15, TOP, 0, 0, sleeves === 'long' ? -0.145 : -0.075));
    arm.add(ball(0.05, sleeves === 'long' ? TOP : JT, 0, 0, -0.29));
    arm.add(cylZ(0.042, 0.24, SK, -0.03, -0.01, -0.42));
    if (sleeves === 'long') arm.add(cylZ(0.052, 0.16, TOP, -0.025, -0.008, -0.38));
    arm.add(ball(0.045, SK, -0.04, -0.02, -0.55));
    const tag = bx(0.05, 0.07, 0.005, 0xffffff, 0.05, -0.06, -0.2); tag.rotation.z = 0.5; arm.add(tag); // price tag still on
    // left arm reaches for the front of the gun, badly
    armL.position.set(-0.25, 1.45, 0);
    const upper = cylZ(0.048, 0.3, SK, 0.07, -0.02, -0.14); upper.rotation.y = -0.45; armL.add(upper);
    if (sleeves) { const sl = cylZ(0.058, sleeves === 'long' ? 0.31 : 0.15, TOP, sleeves === 'long' ? 0.07 : 0.035, -0.02, sleeves === 'long' ? -0.14 : -0.07); sl.rotation.y = -0.45; armL.add(sl); }
    armL.add(ball(0.05, sleeves === 'long' ? TOP : JT, 0.14, -0.04, -0.28));
    const fore = cylZ(0.042, 0.3, SK, 0.27, -0.04, -0.4); fore.rotation.y = -0.9; armL.add(fore);
    if (sleeves === 'long') { const fs = cylZ(0.052, 0.18, TOP, 0.2, -0.035, -0.34); fs.rotation.y = -0.9; armL.add(fs); }
    addHair(head, lk);
    body.add(armL);
  }
  arm.position.set(0.25, 1.45 + jank.shoulder, 0);
  slot.position.set(-0.03, -0.03, -0.56);
  arm.add(slot);
  body.add(arm);
  body.rotation.z = jank.lean * 0.3;
  const out = { root, body, legL, legR, kneeL, kneeR, head, arm, armL, slot, pupils: [], jank };
  if (!glb) addAccessories(out, look, c);
  return out;
}

export function makeNameTag(name, color) {
  const c = document.createElement('canvas');
  c.width = 128; c.height = 32;
  const g = c.getContext('2d');
  g.font = 'bold 18px "Comic Sans MS", "Comic Neue", cursive';
  g.textAlign = 'center'; g.textBaseline = 'middle';
  g.lineWidth = 4; g.strokeStyle = '#000';
  g.strokeText(name, 64, 16);
  g.fillStyle = color;
  g.fillText(name, 64, 16);
  const t = new THREE.CanvasTexture(c);
  t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestFilter;
  t.colorSpace = THREE.SRGBColorSpace;
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, transparent: true }));
  s.scale.set(1.8, 0.45, 1);
  return s;
}

export function makeShadow() {
  const m = new THREE.Mesh(new THREE.CircleGeometry(0.45, 8).rotateX(-Math.PI / 2),
    new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.35, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2 }));
  m.renderOrder = 1;
  return m;
}

// ------------------------------------------------------------ projectiles
export function buildProjectile(k, skin) {
  const g = buildProjectileRaw(k);
  if (!g.userData.glb) g.userData.hatAt = HAT_AT['p_' + k];
  return applySkin(g, skin);
}
function buildProjectileRaw(k) {
  const g = new THREE.Group();
  const sizes = { chicken: 0.7, banana: 0.4, bowling: 0.9, duck: 0.5, slipper: 0.45, bow: 0.9, card: 0.25 };
  const glb = fitted('p_' + k, { size: sizes[k] || 0.5, alignZ: true });
  if (glb) { g.add(glb); g.userData.glb = true; return g; }
  if (k === 'chicken') {
    const b = ball(0.2, 0xffe14d); b.scale.set(1, 0.9, 1.5); g.add(b);
    g.add(ball(0.13, 0xffe14d, 0, 0.18, -0.28));
    g.add(bx(0.06, 0.05, 0.12, 0xff8a00, 0, 0.16, -0.43));
    g.add(bx(0.03, 0.1, 0.12, 0xff2222, 0, 0.32, -0.27));
    g.add(ball(0.025, 0x000000, 0.09, 0.22, -0.36, true));
    g.add(ball(0.025, 0x000000, -0.09, 0.22, -0.36, true));
    g.add(bx(0.04, 0.2, 0.04, 0xff8a00, 0.08, -0.22, 0.05));
    g.add(bx(0.04, 0.2, 0.04, 0xff8a00, -0.08, -0.22, 0.05));
  } else if (k === 'bow') {
    g.add(cylZ(0.012, 0.9, 0xc8a070, 0, 0, 0, 4));
    const tip = bx(0.04, 0.04, 0.08, 0xdddddd, 0, 0, -0.48, true); g.add(tip); g.userData.tip = tip;
    g.add(bx(0.004, 0.06, 0.1, 0xff4fd8, 0, 0, 0.4)); g.add(bx(0.06, 0.004, 0.1, 0xff4fd8, 0, 0, 0.4));
  } else if (k === 'snowball') {
    const b = ball(0.13, 0xf2f8ff); g.add(b); g.add(ball(0.06, 0xffffff, 0.05, 0.06, 0));
  } else if (k === 'frag') {
    const b = ball(0.12, 0x4a5a2a); b.scale.set(1, 1.2, 1); g.add(b);
    g.add(bx(0.05, 0.06, 0.05, 0x333333, 0, 0.15, 0));
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.035, 0.008, 4, 8), M(0xcccccc)); ring.position.set(0.05, 0.17, 0); g.add(ring);
  } else if (k === 'smokegren') {
    const c = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 0.22, 8), M(0x9aa0a8)); g.add(c);
    g.add(bx(0.15, 0.03, 0.15, 0x555a60, 0, 0.12, 0));
  } else if (k === 'card') {
    const c = new THREE.Mesh(new THREE.PlaneGeometry(0.18, 0.26), cardFace('back'));
    c.material.side = THREE.DoubleSide;
    c.rotation.x = -Math.PI / 2;
    g.add(c);
  } else if (k === 'bowling') {
    bowlingBall(g, 0.45);
  } else if (k === 'duck') {
    duck(g, 2.2);
  } else if (k === 'slipper') {
    slipper(g, 1.6);
  } else {
    const t = new THREE.Mesh(new THREE.TorusGeometry(0.18, 0.06, 4, 8, Math.PI * 0.8), M(0xffe135));
    g.add(t);
    g.add(bx(0.04, 0.04, 0.06, 0x3a2a10, 0.18, 0, 0));
  }
  return g;
}

export function buildHole() {
  const g = new THREE.Group();
  g.add(new THREE.Mesh(new THREE.IcosahedronGeometry(1, 1), new THREE.MeshBasicMaterial({ color: 0x000000 })));
  const shell = new THREE.Mesh(new THREE.IcosahedronGeometry(1.5, 1), new THREE.MeshBasicMaterial({ color: 0x9a3bff, transparent: true, opacity: 0.35, blending: THREE.AdditiveBlending, depthWrite: false }));
  g.add(shell);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(2.2, 0.12, 4, 16), new THREE.MeshBasicMaterial({ color: 0xff7aff, transparent: true, opacity: 0.7, blending: THREE.AdditiveBlending, depthWrite: false }));
  ring.rotation.x = Math.PI / 2;
  g.add(ring);
  const d = new THREE.Group(); duck(d, 1.6); d.position.set(2.2, 0, 0);
  const orbit = new THREE.Group(); orbit.add(d); g.add(orbit);
  g.userData = { shell, ring, orbit };
  return g;
}

export function buildPeel() {
  const g = new THREE.Group();
  const glb = fitted('peel', { size: 0.6, feet: true });
  if (glb) { g.add(glb); return g; }
  g.add(bx(0.16, 0.08, 0.16, 0xffe135, 0, 0.04, 0));
  for (let i = 0; i < 4; i++) {
    const arm = bx(0.12, 0.03, 0.34, i % 2 ? 0xffe135 : 0xf2d02a, 0, 0.02, 0);
    arm.geometry.translate(0, 0, 0.17);
    arm.rotation.y = (i / 4) * Math.PI * 2 + 0.4;
    arm.rotation.x = -0.15;
    g.add(arm);
  }
  g.add(bx(0.04, 0.12, 0.04, 0x5a3a1a, 0, 0.1, 0));
  return g;
}

export function tipColor(tip) { return new THREE.Color((ARROW_TIPS[tip] || ARROW_TIPS.regular).color).getHex(); }

// the katana gets longer with kills: stretch the blade (and move its tip, so trails follow)
export function setKatana(g, n) {
  if (!g || !g.userData.katBlade) return;
  const k = 1 + n * 0.55;
  g.userData.katBlade.scale.z = k;
  g.userData.muzzle.z = -0.07 - (g.userData.katLen + 0.03) * k;
}
