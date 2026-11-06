// Programmer art. If you generated Tripo models (npm run models), they replace these automatically.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { jankify } from './jank.js';
import { applySkin } from './skins.js';
import { COSMETICS } from '/shared/cosmetics.js';
import { SUITS, RANKS, ARROW_TIPS } from '/shared/weapons.js';
import { BLADES } from './blades/index.js';
import { lathe } from './blades/kit.js';
import { LASSO_MODELS, buildLoopProjectile } from './lasso_model.js';
import { buildRigMissile } from './rigmodel.js'; // overdrive rig killstreak
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { laserBuild, calculator } from './gearmodels.js'; // the new gear's models (laser pointer, pop quiz calculator)
import { prepAuthored, authored, AUTHORED, bindAuthored, nodeIn, glossBlade, LAZY, isLazy } from './glbkit.js';
import { SEC_WB, SEC_HATS, secAuthored } from './secmodels.js'; // water pistol, taser, tv remote, radar gun
import { nailgunBuild, tennisBuild, cartCannonBuild, tennisBall, cartModel, nailgunStaple, tennisMachine, cartBasket } from './primmodels.js'; // the new primaries + what they shoot
import { catEars, catTail, maidDress } from './catwear.js'; // Board Approved: cat ears, cat tail, maid dress
import { RIFLE_WB, bindRifle } from './riflemodels.js'; // the rifle pack (burst rifle, lmg, marksman, lever-action, auto shotgun)
import { pistolBuild, akimboBuild, sawnoffBuild } from './sidemodels.js'; // Plan B, Lefty & Righty, Half a Shotgun

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
  for (const it of list) if (isLazy(it.id)) LAZY.set(it.id, it.url); // skins: fetched when first shown (glbkit.js)
  list = list.filter((it) => !LAZY.has(it.id));
  await Promise.all(list.map((it) => new Promise((res) => {
    loader.load(it.url, (gltf) => { if (!prepAuthored(it.id, gltf.scene)) GLB[it.id] = prep(gltf.scene, it); res(); }, undefined, (e) => { console.warn('model failed', it.id, e); res(); });
  })));
  return Object.keys(GLB).length + Object.keys(AUTHORED).length;
}

function prep(scene, it) {
  scene.traverse((o) => {
    if (!o.isMesh) return;
    o.geometry.userData.shared = true; // every clone of this model uses the same geometry: freeTree leaves it alone
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
// a discarded model's own geometries go back to the GPU (shared ones, sprites' and GLB parts stay). materials are
// mostly the shared M() ones, so each owner frees its own.
export function freeTree(root) {
  root.traverse((o) => { if (o.geometry && !o.isSprite && !o.geometry.userData.shared) o.geometry.dispose(); });
}
// in a team game the team colour beats clothing colours (so nobody dresses as the other team)
export function teamLook(look, team) { return team && look ? { ...look, topColor: '', bottomColor: '', teamed: true } : look; }
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


// ------------------------------------------------------------ Redline + Marble Shotgun bits
let tachoMat = null;
function tachoFace() { // tachometer dial: ticks sweep clockwise from bottom-left to bottom-right, red zone at the end
  if (tachoMat) return tachoMat;
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const x = c.getContext('2d');
  x.fillStyle = '#0d0d10'; x.beginPath(); x.arc(64, 64, 63, 0, Math.PI * 2); x.fill();
  const P = (th, r) => [64 + Math.sin(th) * r, 64 - Math.cos(th) * r];
  x.strokeStyle = '#e8281e'; x.lineWidth = 12; x.beginPath(); x.arc(64, 64, 49, 1.2 - Math.PI / 2, 2.3 - Math.PI / 2); x.stroke();
  for (let i = 0; i <= 10; i++) {
    const th = -2.3 + (4.6 * i) / 10, [x0, y0] = P(th, 57), [x1, y1] = P(th, i % 2 ? 47 : 40);
    x.strokeStyle = th > 1.15 ? '#ff6a5a' : '#f2f2f2'; x.lineWidth = i % 2 ? 3 : 6;
    x.beginPath(); x.moveTo(x0, y0); x.lineTo(x1, y1); x.stroke();
  }
  x.fillStyle = '#f2f2f2'; x.font = 'bold 17px sans-serif'; x.textAlign = 'center'; x.fillText('RPM', 64, 100);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.magFilter = THREE.NearestFilter;
  return (tachoMat = new THREE.MeshBasicMaterial({ map: t }));
}
function redlineBuild(g, hot) {
  const body = hot ? 0xc8ccd4 : 0x24262d, accent = hot ? 0xff7a1a : 0xc81e1e, dark = hot ? 0x2a2a2e : 0x151515;
  g.add(bx(0.06, 0.1, 0.3, body, 0, 0, -0.04)); // receiver
  g.add(bx(0.062, 0.018, 0.3, accent, 0, 0.058, -0.04)); // top rail
  g.add(bx(0.062, 0.012, 0.16, accent, 0, -0.03, -0.07)); // stripe
  const grip = bx(0.04, 0.12, 0.05, dark, 0, -0.1, 0.05); grip.rotation.x = -0.3; g.add(grip);
  g.add(bx(0.036, 0.16, 0.05, dark, 0, -0.12, -0.1)); // mag
  g.add(bx(0.05, 0.08, 0.16, dark, 0, -0.01, 0.19)); // stock
  g.add(cylZ(0.034, 0.22, hot ? 0xd8dde4 : 0x3a3d45, 0, 0.01, -0.29, 8)); // barrel shroud
  // vents in the shroud glow hotter the lower your HP (weapons.js drives the colour)
  const vent = jankify(new THREE.MeshBasicMaterial({ color: 0x401010 }));
  for (let i = 0; i < 4; i++) {
    const v = new THREE.Mesh(new THREE.BoxGeometry(0.072, 0.012, 0.022), vent);
    v.position.set(0, 0.012, -0.21 - i * 0.045); v.userData.noWrap = true; g.add(v);
  }
  g.userData.vents = vent;
  g.add(cylZ(0.016, 0.07, 0x111111, 0, 0.01, -0.43, 8)); // muzzle brake
  for (const sx of [-1, 1]) g.add(bx(0.006, 0.02, 0.03, 0x111111, sx * 0.016, 0.01, -0.42));
  // the tachometer on the left side, facing you: its needle is your fire rate
  const dial = new THREE.Group(); dial.position.set(-0.034, 0.03, -0.05); g.add(dial);
  dial.add(new THREE.Mesh(new THREE.CylinderGeometry(0.036, 0.036, 0.01, 14).rotateZ(Math.PI / 2), M(hot ? 0xd8dde4 : 0x101010)));
  const face = new THREE.Mesh(new THREE.CircleGeometry(0.031, 18), tachoFace());
  face.rotation.y = -Math.PI / 2; face.position.x = -0.0055; face.userData.noWrap = true; dial.add(face);
  const needle = new THREE.Group(); needle.position.x = -0.007; dial.add(needle);
  const nm = new THREE.Mesh(new THREE.BoxGeometry(0.002, 0.026, 0.003), M(0xff2a2a, true)); nm.position.y = 0.011; nm.userData.noWrap = true; needle.add(nm);
  needle.rotation.x = -2.3;
  g.userData.needle = needle;
  if (hot) { // hot rod: chrome side pipes and flame licks
    for (const sx of [-1, 1]) {
      g.add(cylZ(0.009, 0.24, 0xd8dde4, sx * 0.04, -0.035, -0.1, 8));
      g.add(cylZ(0.012, 0.02, 0x333333, sx * 0.04, -0.035, -0.225, 8));
      for (let i = 0; i < 3; i++) { const f = bx(0.003, 0.012, 0.07 - i * 0.015, i % 2 ? 0xffd23b : 0xff7a1a, sx * 0.031, 0.02 - i * 0.014, 0.02 + i * 0.01); f.rotation.x = 0.25; g.add(f); }
    }
  }
  g.userData.muzzle = new THREE.Vector3(0, 0.01, -0.47);
  g.userData.len = 0.68;
}
const MARBLE_COLS = [0x2f7bff, 0x19c37d, 0xff4f4f, 0xffd23b, 0xb07dff, 0xff8a1a, 0x37d6ff];
const GUM_COLS = [0xff2e63, 0xffd400, 0x00c2ff, 0x7dff4f, 0xff7a1a, 0xffffff, 0xff4fd8];
function glassMat() { return jankify(new THREE.MeshLambertMaterial({ color: 0xcfefff, transparent: true, opacity: 0.3, depthWrite: false })); }
function fillWith(g, cols, n, cx, cy, cz, rx, h, r) { // marbles/gumballs piled in a container
  for (let i = 0; i < n; i++) {
    const a = i * 2.4, k = (i % 4) / 4;
    const m = ball(r, cols[i % cols.length], cx + Math.cos(a) * rx * (0.3 + k), cy + Math.floor(i / 4) * r * 1.7, cz + Math.sin(a) * rx * (0.3 + k));
    m.userData.noWrap = true; g.add(m);
  }
}

// ------------------------------------------------------------ Shredder bits
let hazardMat = null;
function hazard() { // yellow/black warning stripes
  if (hazardMat) return hazardMat;
  const c = document.createElement('canvas'); c.width = c.height = 32;
  const x = c.getContext('2d');
  x.fillStyle = '#f2b01e'; x.fillRect(0, 0, 32, 32);
  x.fillStyle = '#151515';
  for (let i = -32; i < 64; i += 16) { x.beginPath(); x.moveTo(i, 0); x.lineTo(i + 8, 0); x.lineTo(i - 24, 32); x.lineTo(i - 32, 32); x.fill(); }
  const t = new THREE.CanvasTexture(c);
  t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestFilter; t.colorSpace = THREE.SRGBColorSpace;
  return (hazardMat = jankify(new THREE.MeshLambertMaterial({ map: t, flatShading: true })));
}
let heatFace = null;
function heatDial() { // heat gauge face: cold on the left, the red zone where it overheats on the right
  if (heatFace) return heatFace;
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const x = c.getContext('2d');
  x.fillStyle = '#f2efe4'; x.beginPath(); x.arc(32, 32, 31, 0, Math.PI * 2); x.fill();
  x.lineWidth = 7;
  for (const [a0, a1, col] of [[-2.3, -0.4, '#3cb83c'], [-0.4, 1.0, '#f2b01e'], [1.0, 2.3, '#e8281e']]) { x.strokeStyle = col; x.beginPath(); x.arc(32, 32, 24, a0 - Math.PI / 2, a1 - Math.PI / 2); x.stroke(); }
  x.fillStyle = '#151515'; x.font = 'bold 13px sans-serif'; x.textAlign = 'center'; x.fillText('HOT', 32, 52);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.magFilter = THREE.NearestFilter;
  return (heatFace = new THREE.MeshBasicMaterial({ map: t }));
}
// a thin box from a to b (vanes)
function strut(a, b, w, h, color) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, a.distanceTo(b)), M(color));
  m.position.copy(a).add(b).multiplyScalar(0.5); m.lookAt(b);
  return m;
}
// a shredder's teeth heating up, k 0..1: the steel darkens to a dull red and glows orange over it (glowing on top of
// near-white steel would just look whiter). base = the glow a material already has (remote.js lights players up)
const hotDark = new THREE.Color(0x3a0c04), hotGlow = new THREE.Color();
export function heatTeeth(g, k, base = 0) {
  const m = g.userData.blade && g.userData.blade.material;
  if (!m || !m.emissive) return;
  const c0 = g.userData.bladeColor || (g.userData.bladeColor = m.color.clone());
  m.color.copy(c0).lerp(hotDark, k * 0.85);
  m.emissive.copy(m.color).multiplyScalar(base).add(hotGlow.setRGB(k, k * 0.32, k * 0.05));
  const b = g.userData.blur;
  if (b) { b.material.color.copy(m.color); b.material.emissive.copy(m.emissive); } // the blur of them glows too
}
// the rotor turning at k (1 = full speed). a tooth steps at most a third of the gap to the next one a frame, so at any
// fps they never seem to stand still or run backwards; past that, the blur sleeve fades in over them and sells the speed
export function spinTeeth(g, dt, k) {
  const ud = g.userData;
  if (!ud.teeth) return;
  ud.teeth.rotation.z -= Math.min(0.3, dt * k * 40);
  const b = ud.blur, o = Math.min(1, Math.max(0, (k - 0.3) / 0.6));
  if (!b) return;
  b.visible = o > 0.01;
  b.material.opacity = 0.62 * o;
  b.rotation.z -= dt * k * 31; // (streaks, not teeth: no stepping to worry about)
}
let blurMap = null;
function blurTex() { // the teeth smeared round the drum: steel streaks with the red tips in them, one band per row
  if (blurMap) return blurMap;
  const c = document.createElement('canvas'); c.width = 64; c.height = 32;
  const x = c.getContext('2d');
  for (const v of [3, 16, 29]) { // (rows 0-2: the cage hides row 3, it's down the throat)
    x.globalAlpha = 0.28; x.fillStyle = '#b8bdc5'; x.fillRect(0, v - 3, 64, 7); // the steel, smeared all the way round
    for (let i = 0; i < 14; i++) {
      x.globalAlpha = 0.4 + Math.random() * 0.55;
      x.fillStyle = Math.random() < 0.3 ? '#8a1010' : Math.random() < 0.5 ? '#f2f5fa' : '#a8adb5';
      const len = 10 + Math.random() * 30, u = Math.random() * 64, h = 1 + Math.random() * 2, y = v - 3 + Math.random() * 6;
      x.fillRect(u, y, len, h); x.fillRect(u - 64, y, len, h); // wraps round the seam
    }
  }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  return (blurMap = t);
}
// colours + the intake shape (segs/phase: 4 + PI/4 = a square hopper). fills g, sets muzzle / chute / teeth / lamps / gauge
function shredderBuild(g, o) {
  const y = 0.055; // the axis the rotor + funnel sit on
  const grip = bx(0.045, 0.13, 0.055, o.grip, 0, -0.075, 0.03); grip.rotation.x = -0.3; g.add(grip);
  g.add(bx(0.014, 0.036, 0.016, 0xd01c1c, 0, -0.03, -0.022)); // big red trigger
  // motor at the back, the chute on top of it
  g.add(bx(0.19, 0.17, 0.26, o.body, 0, y, 0.16));
  g.add(bx(0.15, 0.13, 0.03, o.dark, 0, y, 0.3));
  if (o.hazard) { const hz = new THREE.Mesh(new THREE.BoxGeometry(0.198, 0.178, 0.05), hazard()); hz.position.set(0, y, 0.06); hz.userData.noWrap = true; g.add(hz); }
  for (let i = 0; i < 5; i++) for (const sx of [-1, 1]) g.add(bx(0.012, 0.13, 0.016, o.dark, sx * 0.1, y, 0.1 + i * 0.042)); // cooling fins
  // carry handle over the cage (the hat sits on it)
  for (const z of [0.0, -0.13]) g.add(bx(0.016, 0.06, 0.016, o.dark, 0, 0.19, z));
  g.add(bx(0.024, 0.024, 0.17, o.grip, 0, 0.222, -0.065));
  g.add(bx(0.07, 0.06, 0.07, o.dark, 0, 0.17, 0.12)); // chute collar
  g.add(bx(0.06, 0.08, 0.06, o.chute, 0, 0.22, 0.125));
  const bend = bx(0.065, 0.065, 0.15, o.chute, 0, 0.265, 0.18); bend.rotation.x = -0.45; g.add(bend);
  const lip = bx(0.08, 0.08, 0.02, o.dark, 0, 0.297, 0.248); lip.rotation.x = -0.45; g.add(lip);
  const hole = bx(0.046, 0.046, 0.01, 0x000000, 0, 0.3, 0.255, true); hole.rotation.x = -0.45; g.add(hole);
  g.userData.chute = new THREE.Vector3(0, 0.305, 0.262);
  g.userData.chuteDir = new THREE.Vector3(0, 0.43, 0.9).normalize();
  // power lamps (one on the back for everyone else, one by the gauge for you): weapons.js / shredder.js light them
  // as the motor spins and blink them when it overheats. meshes, not materials: remote.js swaps in tinted copies
  const lamp = (w, h, d, px, py, pz) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), jankify(new THREE.MeshBasicMaterial({ color: 0x500000 }))); m.position.set(px, py, pz); m.userData.noWrap = true; g.add(m); return m; };
  g.userData.lamps = [lamp(0.03, 0.03, 0.012, 0.045, 0.1, 0.316), lamp(0.014, 0.01, 0.014, -0.082, 0.15, 0.077)];
  // heat gauge on top of the stripes, tipped back at you: the needle climbs to the red as it heats up (weapons.js)
  const gauge = new THREE.Group(); gauge.position.set(-0.048, 0.146, 0.058); gauge.rotation.x = 0.55; g.add(gauge);
  gauge.add(new THREE.Mesh(new THREE.CylinderGeometry(0.027, 0.029, 0.01, 12), M(o.dark)));
  const face = new THREE.Mesh(new THREE.CircleGeometry(0.023, 14).rotateX(-Math.PI / 2), heatDial()); face.position.y = 0.0055; face.userData.noWrap = true; gauge.add(face);
  const needle = new THREE.Group(); needle.position.y = 0.007; gauge.add(needle);
  const nm = new THREE.Mesh(new THREE.BoxGeometry(0.003, 0.002, 0.02), M(0xd01c1c, true)); nm.position.z = -0.008; nm.userData.noWrap = true; needle.add(nm);
  needle.rotation.y = 2.3;
  g.userData.heatNeedle = needle; // not .needle: that one's the Redline's tachometer
  // the rotor cage: bars you can see the teeth through
  for (const z of [0.005, -0.15]) g.add(cylZ(0.108, 0.026, o.dark, 0, y, z, 12));
  for (let i = 0; i < 8; i++) {
    const a = (i / 8) * Math.PI * 2 + 0.2, bar = bx(0.013, 0.013, 0.16, o.dark, Math.cos(a) * 0.102, y + Math.sin(a) * 0.102, -0.072);
    bar.rotation.z = a; g.add(bar);
  }
  // teeth: four rows of hooked blades on a hub, spinning round the funnel axis (weapons.js / shredder.js spin it).
  // bare steel under any wrap, with their own material: they glow red-hot as it overheats
  const steel = jankify(new THREE.MeshLambertMaterial({ color: o.teeth, flatShading: true }));
  const teeth = new THREE.Group(); teeth.position.set(0, y, -0.06);
  teeth.add(cylZ(0.026, 0.27, 0x55595f, 0, 0, -0.04, 8));
  for (let row = 0; row < 4; row++) {
    for (let i = 0; i < 6; i++) {
      const a = (i / 6) * Math.PI * 2 + row * 0.52, t = new THREE.Mesh(new THREE.BoxGeometry(0.016, 0.062, 0.028), steel);
      t.position.set(Math.cos(a) * 0.052, Math.sin(a) * 0.052, 0.05 - row * 0.062); t.rotation.set(0.35, 0, a - Math.PI / 2); t.userData.noWrap = true; teeth.add(t);
      const tip = bx(0.017, 0.016, 0.03, 0x8a1010, Math.cos(a) * 0.082, Math.sin(a) * 0.082, 0.05 - row * 0.062);
      tip.rotation.z = a - Math.PI / 2; tip.userData.noWrap = true; teeth.add(tip);
      g.userData.blade = t; // any blade: its material (or the tinted copy remote.js swaps in) is the one to heat up
    }
  }
  g.add(teeth);
  g.userData.teeth = teeth;
  // motion blur: a see-through sleeve of streaks round the teeth inside the cage, faded in with speed (spinTeeth).
  // its own material per gun: each one fades and heats on its own
  const blur = new THREE.Mesh(new THREE.CylinderGeometry(0.094, 0.094, 0.13, 18, 1, true).rotateX(Math.PI / 2),
    jankify(new THREE.MeshLambertMaterial({ color: o.teeth, map: blurTex(), transparent: true, opacity: 0, depthWrite: false })));
  blur.position.set(0, y, -0.0725); blur.visible = false; blur.userData.noWrap = true; g.add(blur);
  g.userData.blur = blur;
  // the intake: a thick-walled funnel, painted outside, dark inside so the teeth at the bottom of it show
  const R = o.mouthR, Z = o.mouthZ, lp = { segs: o.segs, phase: o.phase, y };
  g.add(lathe([[R - 0.008, Z], [R + 0.012, Z], [R + 0.012, Z + 0.025], [0.112, -0.15], [0.09, -0.15]], o.funnel, lp)); // (profile order = which way the faces point)
  g.add(lathe([[0.09, -0.15], [0.09, -0.175], [R - 0.008, Z]], o.liner, lp));
  // vanes down the inside give the air its spin (round intake only)
  if (o.vanes) for (let i = 0; i < 6; i++) {
    const a0 = (i / 6) * Math.PI * 2, a1 = a0 + 0.7, r0 = 0.092, r1 = R - 0.035, z0 = -0.18, z1 = Z + 0.03;
    g.add(strut(new THREE.Vector3(Math.cos(a0) * r0, y + Math.sin(a0) * r0, z0), new THREE.Vector3(Math.cos(a1) * r1, y + Math.sin(a1) * r1, z1), 0.007, 0.012, o.vanes));
  }
  const lipR = new THREE.Mesh(new THREE.TorusGeometry(R + 0.004, 0.016, 4, o.segs, Math.PI * 2), M(o.rim));
  lipR.position.set(0, y, Z); lipR.rotation.z = o.phase || 0; g.add(lipR);
  const nb = o.segs === 4 ? 4 : 8; // bolts round the rim (in the corners of a square hopper)
  for (let i = 0; i < nb; i++) { const a = (o.phase || 0) + (i / nb) * Math.PI * 2 + (nb === 4 ? 0 : Math.PI / 8); g.add(bx(0.012, 0.012, 0.008, 0xb8bcc4, Math.cos(a) * (R + 0.006), y + Math.sin(a) * (R + 0.006), Z - 0.017)); }
  g.userData.muzzle = new THREE.Vector3(0, y, Z - 0.01);
  Object.assign(g.userData, { mouthR: R, axisY: y, throatZ: -0.19 }); // where the air goes in (weapons.js draws it)
  g.userData.len = 0.75;
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

// ------------------------------------------------------------ Scales of Justice: held upright by the handle at the bottom
// of the pillar, beam across X, a pan hanging off each end. Built at rest; scales.js tilts the beam toward the verdict
// and swings the pans like pendulums. Left pan holds the heart (guilt), right pan the feather (innocence).
function chainLinks(g, a, b, n, color) { // little flat links from a to b, every other one turned 90 degrees
  const d = new THREE.Vector3().subVectors(b, a), len = d.length(), q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), d.normalize());
  for (let i = 0; i < n; i++) {
    const l = new THREE.Mesh(new THREE.BoxGeometry(0.009, (len / n) * 1.2, 0.0035), M(color));
    l.position.copy(a).addScaledVector(d, ((i + 0.5) / n) * len);
    l.quaternion.copy(q);
    if (i % 2) l.rotateY(Math.PI / 2);
    g.add(l);
  }
}
const ARC_MATS = {}; // the dial's red / pale halves: shared, so swapping to the scales doesn't make new materials every time
function scalesBuild(g, toy) {
  const C = toy
    ? { metal: 0xe0a860, dark: 0xe8402a, hi: 0x2f6bff, grip: 0xe0a860, pan: 0x3fbf4a, beam: 0xffd23b, chain: 0xf4f0e0 }
    : { metal: 0xc89a32, dark: 0x7a5a1c, hi: 0xffd86a, grip: 0x4a2a14, pan: 0xd8a840, beam: 0xc89a32, chain: 0x9a7a2a };
  const TOP = 0.46, HALF = 0.21, LEN = 0.15, PR = 0.065; // beam height, half span to the hooks, chain length, pan radius
  // handle (what you hold) + pommel
  g.add(ball(toy ? 0.036 : 0.03, toy ? 0xe8402a : C.metal, 0, -0.115, 0));
  const grip = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.022, 0.17, 8), M(C.grip)); grip.position.y = -0.02; g.add(grip);
  for (const y of [-0.09, 0.05]) { const r = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.012, 8), M(toy ? 0x2f6bff : C.metal)); r.position.y = y; g.add(r); }
  // everything above the handle (the toy one wobbles on it)
  const body = new THREE.Group(); body.position.y = 0.07; g.add(body);
  const foot = new THREE.Mesh(new THREE.CylinderGeometry(0.035, toy ? 0.07 : 0.075, 0.035, toy ? 8 : 10), M(toy ? 0x2f6bff : C.metal)); foot.position.y = 0.01; body.add(foot);
  const pillar = new THREE.Mesh(new THREE.CylinderGeometry(toy ? 0.022 : 0.014, toy ? 0.022 : 0.018, 0.34, 8), M(C.metal)); pillar.position.y = 0.2; body.add(pillar);
  body.add(ball(0.024, toy ? 0xffd23b : C.hi, 0, 0.1, 0), ball(0.02, toy ? 0xe8402a : C.metal, 0, 0.26, 0));
  body.add(bx(0.05, 0.05, 0.03, C.dark, 0, TOP - 0.09, 0)); // fulcrum bracket
  body.add(cylZ(0.008, 0.05, C.hi, 0, TOP - 0.07, 0, 6)); // the pin the beam rocks on
  // dial behind the pointer: red half = guilty, pale half = not guilty (the toy has a kangaroo there instead)
  if (!toy) {
    const plate = new THREE.Mesh(new THREE.CircleGeometry(0.084, 10, Math.PI / 2 - 0.95, 1.9), M(C.dark)); plate.position.set(0, TOP - 0.07, 0.002); body.add(plate);
    for (const [a0, col] of [[Math.PI / 2, 0xff3a2a], [Math.PI / 2 - 0.85, 0xdff8ff]]) {
      const arc = new THREE.Mesh(new THREE.RingGeometry(0.056, 0.078, 8, 1, a0, 0.85), (ARC_MATS[col] ||= new THREE.MeshBasicMaterial({ color: col, side: THREE.DoubleSide })));
      arc.position.set(0, TOP - 0.07, 0.005); arc.userData.noWrap = true; body.add(arc);
    }
  }
  const beam = new THREE.Group(); beam.position.y = TOP - 0.07; body.add(beam);
  beam.add(bx(HALF * 2 + 0.03, toy ? 0.03 : 0.016, toy ? 0.026 : 0.018, C.beam));
  for (const sx of [-1, 1]) {
    beam.add(ball(toy ? 0.024 : 0.017, toy ? 0xe8402a : C.hi, sx * (HALF + 0.018), 0, 0));
    beam.add(bx(0.006, 0.022, 0.006, C.dark, sx * HALF, -0.016, 0)); // hook
  }
  if (!toy) beam.add(bx(0.006, 0.075, 0.005, C.hi, 0, 0.042, 0.012)); // pointer: leans toward the heavy side
  const pans = [-1, 1].map((sx) => {
    const pan = new THREE.Group();
    pan.userData.pivot = new THREE.Vector3(sx * HALF, -0.024, 0);
    pan.position.copy(pan.userData.pivot);
    for (let i = 0; i < 3; i++) { // chains (strings on the toy) from the hook to the rim
      const a = (i / 3) * Math.PI * 2 + Math.PI / 2, rim = new THREE.Vector3(Math.cos(a) * PR * 0.85, -LEN + 0.012, Math.sin(a) * PR * 0.85);
      if (toy) { const s = new THREE.Mesh(new THREE.CylinderGeometry(0.0025, 0.0025, rim.length(), 4), M(C.chain)); s.position.copy(rim).multiplyScalar(0.5); s.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), rim.clone().normalize()); pan.add(s, ball(0.008, 0xe8402a, rim.x * 0.5, rim.y * 0.5, rim.z * 0.5)); }
      else chainLinks(pan, new THREE.Vector3(), rim, 6, C.chain);
    }
    const prof = [[0, -0.012], [PR * 0.55, -0.01], [PR * 0.9, 0], [PR, 0.014], [PR * 0.9, 0.012], [PR * 0.5, -0.002], [0, -0.004]];
    const bowl = new THREE.Mesh(new THREE.LatheGeometry(prof.map(([r, y]) => new THREE.Vector2(r, y)), toy ? 8 : 12), M(C.pan));
    bowl.position.y = -LEN; pan.add(bowl);
    if (sx < 0) { // guilt: a heart (the toy has a stack of blocks)
      if (toy) { pan.add(bx(0.04, 0.03, 0.04, 0xe8402a, 0, -LEN + 0.02, 0), bx(0.03, 0.026, 0.03, 0x2f6bff, 0.004, -LEN + 0.047, 0)); }
      else {
        for (const hx of [-1, 1]) pan.add(ball(0.016, 0xd8202a, hx * 0.012, -LEN + 0.038, 0));
        const tip = new THREE.Mesh(new THREE.ConeGeometry(0.024, 0.034, 6), M(0xd8202a)); tip.rotation.z = Math.PI; tip.position.y = -LEN + 0.02; pan.add(tip);
      }
    } else if (toy) pan.add(ball(0.024, 0xffd23b, 0, -LEN + 0.026, 0)); // innocence: a feather (the toy has a ball)
    else {
      const vane = ball(0.045, 0xf6f6f6, 0.004, -LEN + 0.05, 0); vane.scale.set(0.32, 1, 0.1); vane.rotation.z = -0.35; pan.add(vane);
      const quill = bx(0.004, 0.05, 0.004, 0xd8c8a0, -0.012, -LEN + 0.016, 0); quill.rotation.z = -0.35; pan.add(quill);
    }
    beam.add(pan);
    return pan;
  });
  if (toy) { // the judge: a kangaroo in a wig, sitting on top
    const k = new THREE.Group(); k.position.y = TOP - 0.055; body.add(k);
    const fur = 0xb5651d;
    const tum = ball(0.026, fur, 0, 0.022, 0); tum.scale.set(0.85, 1.15, 0.8); k.add(tum);
    k.add(ball(0.017, fur, 0, 0.06, 0.004), ball(0.009, 0x8a4a14, 0, 0.056, 0.019), ball(0.003, 0x000000, -0.007, 0.065, 0.016, true), ball(0.003, 0x000000, 0.007, 0.065, 0.016, true));
    for (const sx of [-1, 1]) { const ear = bx(0.008, 0.03, 0.004, fur, sx * 0.009, 0.085, 0); ear.rotation.z = -sx * 0.3; k.add(ear); k.add(ball(0.008, 0xf4f4f4, sx * 0.016, 0.052, -0.004)); } // ears + wig curls
    const tail = cylZ(0.006, 0.06, fur, 0, 0.006, -0.03, 5); tail.rotation.x = 0.5; k.add(tail);
  }
  g.userData.court = { beam, pans, body, len: LEN, wobble: toy };
  g.userData.faceOn = true; // pictures look at it from the front so both pans show
  g.userData.muzzle = new THREE.Vector3(0, TOP, 0); // the swing trail follows the top of the scale
  g.userData.len = 0.7;
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
  redline(g) { redlineBuild(g, false); }, // a stubby carbine with a tachometer bolted on
  marbles(g) { // a brass blunderbuss fed from a jar of marbles
    const grip = bx(0.036, 0.12, 0.048, 0x6b3a1a, 0, -0.07, 0.07); grip.rotation.x = -0.45; g.add(grip);
    g.add(bx(0.044, 0.06, 0.2, 0x6b3a1a, 0, -0.012, 0.0)); // walnut stock
    g.add(bx(0.05, 0.05, 0.1, 0x34343c, 0, 0.004, -0.03)); // iron lock
    g.add(bx(0.006, 0.035, 0.05, 0x1a1a1a, 0, -0.05, 0.02)); // trigger guard
    g.add(bx(0.04, 0.035, 0.12, 0x6b3a1a, 0, -0.022, -0.15)); // forestock
    g.add(lathe([[0.019, -0.08], [0.019, -0.24], [0.024, -0.3], [0.036, -0.335], [0.052, -0.36], [0.05, -0.368], [0.036, -0.35], [0.022, -0.31], [0, -0.3]], 0xc8a050, { segs: 12, y: 0.012 }));
    g.add(cylZ(0.023, 0.016, 0xa07830, 0, 0.012, -0.1, 12)); // barrel bands
    g.add(cylZ(0.023, 0.016, 0xa07830, 0, 0.012, -0.22, 12));
    const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.016, 0.03, 8), M(0xc8a050)); neck.position.set(0, 0.045, -0.06); g.add(neck);
    const jar = new THREE.Mesh(new THREE.CylinderGeometry(0.036, 0.036, 0.075, 12), glassMat());
    jar.position.set(0, 0.098, -0.06); jar.userData.noWrap = true; jar.renderOrder = 2; g.add(jar);
    const lid = new THREE.Mesh(new THREE.CylinderGeometry(0.038, 0.038, 0.012, 12), M(0x2a2a2a)); lid.position.set(0, 0.141, -0.06); g.add(lid);
    fillWith(g, MARBLE_COLS, 10, 0, 0.074, -0.06, 0.018, 0, 0.012);
    g.userData.muzzle = new THREE.Vector3(0, 0.012, -0.37);
    g.userData.len = 0.5;
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
  shredder(g) { // gunmetal motor with warning stripes, a rotor cage, a yellow intake; the chute spits out the back
    shredderBuild(g, { body: 0x3d4452, dark: 0x1e2126, funnel: 0xf2b01e, liner: 0x4a3a1a, vanes: 0x8a6a2a, rim: 0x151515, chute: 0x8a919b, teeth: 0xd6dce4, grip: 0x1a1a1a, segs: 14, phase: 0, mouthR: 0.21, mouthZ: -0.43, hazard: true });
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
  scales(g) { scalesBuild(g, false); },
  claw(g) { // infection: a rotten green forearm, a torn cuff and four long dirty nails
    const SK = 0x6f9a3a, DK = 0x55782b, NAIL = 0xd8cf9a, y = -0.03;
    g.add(cylZ(0.055, 0.24, SK, 0, y, 0.03, 6));
    for (let i = 0; i < 5; i++) { const rag = bx(0.03, 0.05, 0.05 + (i % 2) * 0.03, 0x4a5a3a, -0.05 + i * 0.025, y - 0.03, 0.14); rag.rotation.z = (i - 2) * 0.5; g.add(rag); }
    g.add(bx(0.12, 0.045, 0.11, SK, 0, y, -0.15));
    for (let i = 0; i < 4; i++) {
      const x = -0.045 + i * 0.03;
      const f = bx(0.022, 0.024, 0.09, DK, x, y + 0.004, -0.24); f.rotation.x = -0.2; g.add(f);
      const nail = new THREE.Mesh(new THREE.ConeGeometry(0.012, 0.065, 4), M(NAIL));
      nail.rotation.x = -Math.PI / 2 - 0.45; nail.position.set(x, y - 0.012, -0.3); g.add(nail);
    }
    const thumb = bx(0.024, 0.024, 0.075, DK, 0.075, y, -0.16); thumb.rotation.y = -0.6; g.add(thumb);
    g.userData.muzzle = new THREE.Vector3(0, y, -0.33);
    g.userData.len = 0.4;
  },
};

// where a hat sits on each weapon (local position) and how tall it is. hand placed so every hat fits every weapon.
Object.assign(WB, SEC_WB); // the new secondaries + the radar gun (secmodels.js)

Object.assign(WB, RIFLE_WB);
const HAT_AT = {
  ar: [[0, 0.1, 0.02], 0.12], smg: [[0, 0.055, 0.0], 0.1], shotgun: [[0, 0.05, 0.0], 0.11], minigun: [[0, 0.17, 0.05], 0.14],
  sniper: [[0, 0.16, -0.05], 0.13], chicken: [[0, 0.075, -0.5], 0.09], bowling: [[0, 0.17, -0.1], 0.15], banana: [[0, 0.185, 0.02], 0.1],
  revolver: [[0, 0.065, -0.02], 0.08], cig: [[0, 0.0125, 0.055], 0.04], blower: [[0, 0.22, 0.05], 0.14], popper: [[0, 0.07, 0.02], 0.07],
  reverse: [[0, 0.09, 0.02], 0.07], duck: [[0, 0.152, -0.072], 0.06], bread: [[0, 0.11, -0.3], 0.16], slipper: [[0, 0.068, -0.08], 0.07],
  spoon: [[0, 0.017, -0.13], 0.04], slapper: [[0, 0.0125, -0.55], 0.09], scythe: [[0, 0.47, -0.8], 0.14],
  scythe_rifle: [[0, 0.13, -0.05], 0.12], bow: [[0, 0.08, 0.0], 0.08], cards: [[0, 0.07, -0.004], 0.07],
  slapper_foam: [[0, 0.03, -0.5], 0.1], slapper_paw: [[0, 0.06, -0.5], 0.1], bread_croissant: [[0, 0.15, -0.6], 0.15],
  shredder: [[0, 0.234, -0.065], 0.11], shredder_chipper: [[0, 0.234, -0.065], 0.11],
  sniper_golden: [[0, 0.245, -0.05], 0.09], // on the crown's cross
  p_chicken: [[0, 0.31, -0.28], 0.15], p_bowling: [[0, 0.45, 0], 0.3], p_duck: [[0, 0.418, -0.2], 0.2], p_slipper: [[0, 0.11, -0.13], 0.1], p_banana: [[0, 0.24, 0], 0.12],
  scales: [[0, 0.555, 0], 0.07], scales_kangaroo: [[0, 0.6, 0.004], 0.05],
};
Object.assign(HAT_AT, SEC_HATS);

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
// ------------------------------------------------------------ Golden Sniper (Sniper Royalty reward)
// gold plate with darker gold scrollwork (canvas, nearest-filtered so it stays crunchy), jewels, a crown on the scope
// and a glint that hops around the metal. everything is noWrap: a wrap can't take the gold off a trophy
const goldMats = new Map();
function goldMat(kind) {
  if (goldMats.has(kind)) return goldMats.get(kind);
  const P = (o) => jankify(new THREE.MeshPhongMaterial({ flatShading: true, ...o }));
  const m = kind === 'dark' ? P({ color: 0x9a6410, specular: 0xffcf6a, shininess: 40, emissive: 0x160a00 })
    : kind === 'gold' ? P({ color: 0xffc21a, specular: 0xfff0a0, shininess: 80, emissive: 0x2a1800 })
      : P({ map: engraving(kind), color: 0xffc21a, specular: 0xfff0a0, shininess: 80, emissive: 0x2a1800 }); // gold x a grey pattern (other players' glow tints by colour)
  goldMats.set(kind, m);
  return m;
}
function engraving(kind) { // a scroll vine, curls and a border, in grey: the material colour makes it gold (dark lines = darker gold)
  const W = kind === 'long' ? 64 : 32, H = 16;
  const c = document.createElement('canvas'); c.width = W; c.height = H;
  const x = c.getContext('2d');
  const gr = x.createLinearGradient(0, 0, 0, H); gr.addColorStop(0, '#ffffff'); gr.addColorStop(1, '#e2d8c6');
  x.fillStyle = gr; x.fillRect(0, 0, W, H);
  x.strokeStyle = '#7a6040'; x.lineWidth = 1;
  x.strokeRect(1.5, 1.5, W - 3, H - 3);
  x.beginPath();
  for (let i = 0; i <= W - 8; i++) { const y = H / 2 + Math.sin(i * 0.45) * 2.6; if (i) x.lineTo(4 + i, y); else x.moveTo(4, y); }
  x.stroke();
  for (let k = 0; k < W / 14; k++) { // a curl above, then below the vine
    const cx = 8 + k * 14, up = k % 2 ? 1 : -1;
    x.beginPath(); x.arc(cx, H / 2 + up * 3.5, 2.2, 0, Math.PI * 1.6); x.stroke();
    x.fillStyle = '#7a6040'; x.fillRect(cx + 4, H / 2 - up * 3, 1, 1);
  }
  const t = new THREE.CanvasTexture(c);
  t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestFilter; t.generateMipmaps = false; t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
let glintTexture = null;
function glintTex() { // a star: four long rays, four short ones, a hot core
  if (glintTexture) return glintTexture;
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const x = c.getContext('2d');
  const core = x.createRadialGradient(32, 32, 0, 32, 32, 9);
  core.addColorStop(0, 'rgba(255,255,255,1)'); core.addColorStop(0.45, 'rgba(255,240,180,0.75)'); core.addColorStop(1, 'rgba(255,220,120,0)');
  x.fillStyle = core; x.fillRect(0, 0, 64, 64);
  const ray = (a, len, w) => {
    x.save(); x.translate(32, 32); x.rotate(a);
    const g = x.createLinearGradient(0, 0, len, 0); g.addColorStop(0, 'rgba(255,255,240,1)'); g.addColorStop(1, 'rgba(255,225,140,0)');
    x.fillStyle = g; x.beginPath(); x.moveTo(0, -w); x.lineTo(len, 0); x.lineTo(0, w); x.fill(); x.restore();
  };
  for (let i = 0; i < 4; i++) { ray((i * Math.PI) / 2, 31, 2.6); ray(Math.PI / 4 + (i * Math.PI) / 2, 13, 1.5); }
  glintTexture = new THREE.CanvasTexture(c);
  glintTexture.colorSpace = THREE.SRGBColorSpace;
  return glintTexture;
}
// the glint: one star that flashes on a different bit of metal every 1.6 s. it animates itself whenever it's drawn,
// so it works on your viewmodel, other players' guns, replays and the menu preview alike
const GLINT_AT = [[0, 0.112, -0.245, 0.11], [0, 0.25, -0.05, 0.1], [0.018, 0.05, -0.7, 0.13], [0.04, 0.03, 0.02, 0.1], [0, 0.048, -1.18, 0.12], [0.035, 0.03, 0.4, 0.1]];
function addGlint(g, spots = GLINT_AT) {
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: glintTex(), color: 0xfff2b8, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }));
  s.scale.setScalar(1e-4);
  s.frustumCulled = false;
  s.renderOrder = 3;
  const phase = Math.random() * 20, PER = 1.6, FLASH = 0.42;
  s.onBeforeRender = () => {
    const t = performance.now() / 1000 + phase, u = (t % PER) / FLASH;
    const at = spots[Math.floor(t / PER) % spots.length], k = u < 1 ? Math.sin(u * Math.PI) ** 2 : 0;
    s.position.set(at[0], at[1], at[2]);
    s.scale.setScalar(Math.max(1e-4, at[3] * k));
    s.material.rotation = u * 1.4;
    s.updateMatrixWorld();
  };
  g.add(s);
}
function goldSniper(g) {
  const gold = goldMat('gold'), dark = goldMat('dark');
  const part = (geo, mat, x = 0, y = 0, z = 0) => { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.userData.noWrap = true; g.add(m); return m; };
  const box = (w, h, d, mat, x, y, z) => part(new THREE.BoxGeometry(w, h, d), mat, x, y, z);
  const tube = (r, len, mat, x, y, z, seg = 8) => part(new THREE.CylinderGeometry(r, r, len, seg).rotateX(Math.PI / 2), mat, x, y, z);
  const gem = (r, color, x, y, z) => part(new THREE.SphereGeometry(r, 6, 4), M(color, true), x, y, z);
  // body: same shape as the standard sniper, so it holds, aims and scopes the same
  box(0.07, 0.12, 0.55, goldMat('long'), 0, 0, 0); // receiver, scrollwork all round (one material per mesh: other players' guns expect that)
  box(0.072, 0.012, 0.55, dark, 0, 0.064, 0); // dark gold rib along the top
  box(0.072, 0.01, 0.55, dark, 0, -0.064, 0);
  tube(0.022, 1.2, gold, 0, 0.02, -0.85); // barrel
  for (const z of [-0.36, -0.62, -0.88, -1.14]) tube(0.026, 0.018, dark, 0, 0.02, z); // engraved bands
  tube(0.03, 0.09, dark, 0, 0.02, -1.42, 6); // muzzle brake
  for (const z of [-1.4, -1.44]) box(0.062, 0.008, 0.012, gold, 0, 0.02, z);
  box(0.06, 0.16, 0.32, goldMat('short'), 0, -0.03, 0.42); // stock
  box(0.064, 0.17, 0.03, dark, 0, -0.03, 0.585); // butt plate
  box(0.062, 0.04, 0.18, M(0x9a0f2a), 0, 0.05, 0.43); // red velvet cheek rest
  const grip = box(0.05, 0.14, 0.06, gold, 0, -0.12, 0.1); grip.rotation.x = -0.12;
  box(0.012, 0.05, 0.012, dark, 0, -0.08, 0.02); // trigger
  box(0.008, 0.012, 0.11, dark, 0, -0.105, 0.02); // trigger guard
  tube(0.007, 0.05, dark, 0.05, 0.03, 0.12, 6).rotation.set(0, Math.PI / 2, 0); // bolt handle
  part(new THREE.SphereGeometry(0.013, 6, 4), gold, 0.077, 0.03, 0.12); // bolt knob
  for (const sx of [-1, 1]) { // jewels set into both sides of the receiver
    box(0.004, 0.034, 0.12, dark, sx * 0.036, 0.0, -0.15);
    gem(0.011, 0xff1f45, sx * 0.038, 0.0, -0.19); gem(0.011, 0x2a6bff, sx * 0.038, 0.0, -0.15); gem(0.011, 0x18d060, sx * 0.038, 0.0, -0.11);
  }
  // scope: gold tube, dark gold bells and mounts, a blue lens
  tube(0.05, 0.32, gold, 0, 0.11, -0.05);
  tube(0.058, 0.05, dark, 0, 0.11, -0.215);
  tube(0.054, 0.04, dark, 0, 0.11, 0.11);
  for (const z of [-0.13, 0.03]) { box(0.03, 0.03, 0.03, dark, 0, 0.072, z); tube(0.053, 0.014, dark, 0, 0.11, z); }
  const lens = part(new THREE.CircleGeometry(0.046, 10), M(0x7fd6ff, true), 0, 0.11, -0.2405); lens.rotation.y = Math.PI;
  // a small jewelled crown on top of the scope
  const cz = -0.05, cy = 0.158;
  part(new THREE.CylinderGeometry(0.036, 0.031, 0.026, 10), gold, 0, cy + 0.013, cz); // band
  part(new THREE.SphereGeometry(0.03, 8, 4, 0, Math.PI * 2, 0, Math.PI / 2), M(0x9a0f2a), 0, cy + 0.024, cz); // velvet cap
  for (let i = 0; i < 5; i++) {
    const a = (i / 5) * Math.PI * 2;
    part(new THREE.ConeGeometry(0.009, 0.03, 4), gold, Math.cos(a) * 0.031, cy + 0.04, cz + Math.sin(a) * 0.031);
    gem(0.005, 0xfff6e0, Math.cos(a) * 0.031, cy + 0.057, cz + Math.sin(a) * 0.031); // pearls on the points
    gem(0.0065, [0xff1f45, 0x2a6bff, 0x18d060][i % 3], Math.cos(a + 0.63) * 0.036, cy + 0.013, cz + Math.sin(a + 0.63) * 0.036);
  }
  part(new THREE.SphereGeometry(0.009, 6, 4), gold, 0, cy + 0.058, cz); // orb
  box(0.004, 0.022, 0.004, gold, 0, cy + 0.076, cz); box(0.014, 0.004, 0.004, gold, 0, cy + 0.079, cz); // cross
  addGlint(g);
  g.userData.muzzle = new THREE.Vector3(0, 0.02, -1.48);
  g.userData.len = 1.8;
}

// skins for every weapon: alternate models. each belongs to its weapon and keeps that weapon's muzzle / moving parts
const SKIN_BUILD = {
  redline_hotrod(g) { redlineBuild(g, true); },
  shredder_chipper(g) { // a rustic garden wood chipper: green, orange square hopper, a little petrol engine, wheels
    shredderBuild(g, { body: 0x3a7a2a, dark: 0x22301c, funnel: 0xff7a1a, liner: 0x4a2a14, rim: 0x2a2a2a, chute: 0xff7a1a, teeth: 0xc8ccd2, grip: 0x8a5a2b, segs: 4, phase: Math.PI / 4, mouthR: 0.27, mouthZ: -0.44 });
    for (const sx of [-1, 1]) {
      const wheel = new THREE.Mesh(new THREE.CylinderGeometry(0.055, 0.055, 0.03, 10).rotateZ(Math.PI / 2), M(0x1a1a1a));
      wheel.position.set(sx * 0.122, -0.025, 0.25); g.add(wheel);
      g.add(bx(0.006, 0.03, 0.03, 0xf2b01e, sx * 0.139, -0.025, 0.25)); // hub
    }
    g.add(bx(0.06, 0.06, 0.1, 0x2a2a2a, 0.062, 0.165, 0.215)); // petrol engine
    const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.014, 0.014, 0.014, 8), M(0xd01c1c)); cap.position.set(0.062, 0.202, 0.24); g.add(cap);
    g.add(bx(0.004, 0.004, 0.05, 0xdddddd, -0.1, 0.09, 0.2)); // pull-start cord + handle
    g.add(bx(0.014, 0.014, 0.05, 0x1a1a1a, -0.108, 0.09, 0.17));
    for (const [x, yy, z] of [[-0.096, 0.02, 0.24], [0.096, 0.1, 0.06], [-0.096, 0.1, 0.07]]) g.add(bx(0.003, 0.03, 0.04, 0x8a4a1a, x, yy, z)); // rust
    const flap = bx(0.075, 0.006, 0.06, 0xff7a1a, 0, 0.34, 0.26); flap.rotation.x = 0.35; g.add(flap); // deflector
    for (let i = 0; i < 5; i++) { const ch = bx(0.024, 0.008, 0.03, 0xc8a070, -0.05 + i * 0.024, -0.04 + (i % 2) * 0.01, -0.24 - (i % 3) * 0.03); ch.rotation.y = i; ch.userData.noWrap = true; g.add(ch); } // wood chips
  },
  marbles_gumball(g) { // a gumball machine you can shoot
    const grip = bx(0.036, 0.12, 0.048, 0xd01c2a, 0, -0.07, 0.07); grip.rotation.x = -0.45; g.add(grip);
    g.add(bx(0.062, 0.07, 0.2, 0xd01c2a, 0, -0.01, 0.0)); // red cast body
    g.add(bx(0.064, 0.032, 0.05, 0xd8dde4, 0, -0.005, -0.065)); // chrome coin box
    const knob = cylZ(0.014, 0.016, 0xd8dde4, 0, 0, 0, 8); knob.rotation.y = Math.PI / 2; knob.position.set(-0.04, -0.005, -0.065); g.add(knob);
    g.add(cylZ(0.024, 0.26, 0xd8dde4, 0, 0.012, -0.2, 10)); // chute
    g.add(cylZ(0.032, 0.03, 0xd01c2a, 0, 0.012, -0.335, 10)); // mouth ring
    const base = new THREE.Mesh(new THREE.CylinderGeometry(0.034, 0.04, 0.02, 12), M(0xd01c2a)); base.position.set(0, 0.035, -0.03); g.add(base);
    const globe = new THREE.Mesh(new THREE.SphereGeometry(0.055, 12, 8), glassMat()); globe.position.set(0, 0.095, -0.03); globe.userData.noWrap = true; globe.renderOrder = 2; g.add(globe);
    const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.02, 0.012, 10), M(0xd01c2a)); cap.position.set(0, 0.153, -0.03); g.add(cap);
    fillWith(g, GUM_COLS, 14, 0, 0.06, -0.03, 0.026, 0, 0.014);
    g.userData.muzzle = new THREE.Vector3(0, 0.012, -0.35);
    g.userData.len = 0.48;
  },
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
  sniper_golden(g) { goldSniper(g); }, // Sniper Royalty: gold plate, scrollwork, jewels, a crown on the scope, a glint
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
  scales_kangaroo(g) { scalesBuild(g, true); }, // a wobbly wooden toy scale with a kangaroo judge on top
};

// ------------------------------------------------------------ Blood Cross: no gun, a bare right hand doing finger guns
// held like a pistol: the index points down -Z, the thumb is up (+Y), the palm faces left (-X), the back of the hand and the nails
// face right (+X), the knuckles run top (index) to bottom (pinky). real sizes in metres. fingers are chains of capsule bones on
// pivots built from joint positions (they curl toward the palm, about Y); nails, veins and the glow are placed in model space and
// attached to the bone they ride on. userData.index / .thumb are plain pivots for the 'bang', .curl opens the fist for the draw,
// .bare is the forearm for the viewmodel, kept out of the model (other players hold it in their own hand, the icon is just the hand)
const BC_HAND = {
  blood: { skin: 0xefbf86, knuckle: 0xe3a978, palm: 0xf3c592, nail: 0xf3c6b6, vein: 0xd4001e, veinDark: 0xa30018, tip: 0xff3a4c, halo: 0xff1a2e, sleeve: 0x2b2431, cuff: 0x4a3f55 },
  shadow: { skin: 0x3d3547, knuckle: 0x2e2837, palm: 0x473e52, nail: 0x2a0d3b, vein: 0xa43dff, veinDark: 0x8a2be0, tip: 0xeec4ff, halo: 0x9a2bff, sleeve: 0x0f0c14, cuff: 0x2a2135 },
};
const bcV = (x, y, z) => new THREE.Vector3(x, y, z), BC_FWD = bcV(0, 0, -1);
let bcGlowTx = null;
function bcHandGlow() { // soft round glow for the fingertip (additive sprite)
  if (bcGlowTx) return bcGlowTx;
  const c = document.createElement('canvas'); c.width = c.height = 32;
  const x = c.getContext('2d'), gr = x.createRadialGradient(16, 16, 0, 16, 16, 16);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.3, 'rgba(255,255,255,0.55)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  x.fillStyle = gr; x.fillRect(0, 0, 32, 32);
  return (bcGlowTx = new THREE.CanvasTexture(c));
}
let bcFlareTx = null;
function bcFlareTex() { // a ragged star, white-hot in the middle: the blood muzzle flash
  if (bcFlareTx) return bcFlareTx;
  const c = document.createElement('canvas'); c.width = c.height = 32;
  const x = c.getContext('2d'), gr = x.createRadialGradient(16, 16, 0, 16, 16, 16);
  gr.addColorStop(0, '#ffffff'); gr.addColorStop(0.3, 'rgba(255,190,200,0.95)'); gr.addColorStop(0.65, 'rgba(255,120,130,0.8)'); gr.addColorStop(1, 'rgba(255,60,80,0)');
  x.fillStyle = gr; x.beginPath();
  for (let i = 0; i < 14; i++) { const a = (i / 14) * Math.PI * 2, r = i % 2 ? 5 + (i % 4) : 16; x.lineTo(16 + Math.cos(a) * r, 16 + Math.sin(a) * r); }
  x.fill();
  bcFlareTx = new THREE.CanvasTexture(c); bcFlareTx.magFilter = THREE.NearestFilter; bcFlareTx.minFilter = THREE.NearestFilter;
  return bcFlareTx;
}
// a box whose edges + corners are pushed out round an inner box: the palm
function bcRoundBox(w, h, d, r, seg = 3) {
  const geo = new THREE.BoxGeometry(w, h, d, seg, seg, seg), a = geo.attributes.position, v = new THREE.Vector3();
  const ix = w / 2 - r, iy = h / 2 - r, iz = d / 2 - r;
  for (let i = 0; i < a.count; i++) {
    const x = a.getX(i), y = a.getY(i), z = a.getZ(i);
    const cx = Math.max(-ix, Math.min(ix, x)), cy = Math.max(-iy, Math.min(iy, y)), cz = Math.max(-iz, Math.min(iz, z));
    v.set(x - cx, y - cy, z - cz).setLength(r);
    a.setXYZ(i, cx + v.x, cy + v.y, cz + v.z);
  }
  return geo;
}
// one bone: a capsule from its joint (the pivot origin) to the next joint (-len on Z), a little flatter front to back
function bcBone(r, len, color, flat = 0.88) {
  const m = new THREE.Mesh(new THREE.CapsuleGeometry(r, len, 2, 8).rotateX(-Math.PI / 2).translate(0, 0, -len / 2), M(color));
  m.scale.x = flat;
  return m;
}
// a chain of bones through joint positions (model space: the weapon has no parent while it's built), one pivot per joint
function bcBones(parent, pts, radii, color, flat) {
  const piv = [];
  let p = parent;
  for (let i = 0; i < pts.length - 1; i++) {
    p.updateMatrixWorld(true);
    const d = new THREE.Vector3().subVectors(pts[i + 1], pts[i]), len = d.length();
    const j = new THREE.Group();
    j.position.copy(p.worldToLocal(pts[i].clone()));
    j.quaternion.copy(p.getWorldQuaternion(new THREE.Quaternion()).invert().multiply(new THREE.Quaternion().setFromUnitVectors(BC_FWD, d.normalize())));
    j.add(bcBone(radii[i], len, color, flat));
    p.add(j); piv.push(j); p = j;
  }
  return piv;
}
// joints of a finger curled toward the palm: each bone turns a further ang[i] about Y (0 = straight down -Z)
function bcCurled(mcp, lens, ang, drop = 0) {
  const pts = [mcp.clone()];
  let a = 0;
  for (let i = 0; i < lens.length; i++) { a += ang[i]; const p = pts[i]; pts.push(bcV(p.x - Math.sin(a) * lens[i], p.y - drop, p.z - Math.cos(a) * lens[i])); }
  return pts;
}
// put a mesh on a bone's surface in model space (flat side facing n, long side along dir), then hang it on the pivot
function bcOnBone(piv, mesh, pos, n, dir) {
  const z = dir.clone().normalize(), x = n.clone().addScaledVector(z, -n.dot(z)).normalize(), y = new THREE.Vector3().crossVectors(z, x);
  mesh.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, y, z));
  mesh.position.copy(pos);
  piv.updateMatrixWorld(true);
  piv.attach(mesh);
  return mesh;
}
const bcBlob = (color, glow) => new THREE.Mesh(new THREE.SphereGeometry(1, 8, 6), M(color, glow));
// a nail at the end of bone a->b (radius r), facing n. shadow nails are claws: longer, pointed past the tip
function bcNail(piv, a, b, r, n, H, claw) {
  const dir = new THREE.Vector3().subVectors(b, a), m = bcBlob(H.nail);
  m.scale.set(r * 0.3, r * (claw ? 0.66 : 0.74), r * (claw ? 1.22 : 0.95));
  const at = a.clone().lerp(b, claw ? 0.8 : 0.64).addScaledVector(n.clone().normalize(), r * 0.78);
  return bcOnBone(piv, m, at, n, dir);
}
// a glowing line between two model-space points (veins, the X brand). never wrapped
function bcLine(piv, a, b, th, color) {
  const d = new THREE.Vector3().subVectors(b, a), m = new THREE.Mesh(new THREE.BoxGeometry(th, th * 0.7, d.length()), M(color, true));
  m.userData.noWrap = true;
  return bcOnBone(piv, m, a.clone().lerp(b, 0.5), bcV(1, 0, 0).cross(d).lengthSq() > 1e-9 ? bcV(1, 0, 0) : bcV(0, 1, 0), d);
}
function fingerGun(g, shadow) {
  const H = BC_HAND[shadow ? 'shadow' : 'blood'];
  // palm: a rounded block, narrower toward the wrist, the back a touch domed
  const pg = bcRoundBox(0.03, 0.082, 0.09, 0.012), pa = pg.attributes.position;
  for (let i = 0; i < pa.count; i++) {
    const z = pa.getZ(i), k = (z + 0.045) / 0.09;
    pa.setY(i, pa.getY(i) * (1 - 0.13 * k) - 0.004 * k);
    if (pa.getX(i) > 0) pa.setX(i, pa.getX(i) * (1 + 0.25 * (1 - Math.abs(pa.getY(i)) / 0.045)));
  }
  pg.computeVertexNormals();
  const palm = new THREE.Mesh(pg, M(H.skin)); palm.position.set(0.001, -0.005, 0.005); g.add(palm);
  const thenar = bcBlob(H.palm); thenar.scale.set(0.0085, 0.018, 0.024); thenar.position.set(-0.0105, 0.01, 0.012); thenar.rotation.x = 0.45; g.add(thenar); // the fat bit under the thumb
  const hypo = bcBlob(H.palm); hypo.scale.set(0.007, 0.015, 0.022); hypo.position.set(-0.0085, -0.029, 0.018); g.add(hypo);
  // index: straight out, relaxed (a hair of bend at each joint). its own pivot on the big knuckle
  const index = new THREE.Group(); index.position.set(0.003, 0.025, -0.036); g.add(index);
  const ip = [bcV(0.003, 0.025, -0.036), bcV(0.001, 0.0262, -0.0765), bcV(-0.0012, 0.0262, -0.1005), bcV(-0.003, 0.0258, -0.1175)], ir = [0.0099, 0.0091, 0.0085];
  const ib = bcBones(index, ip, ir, H.skin);
  bcNail(ib[2], ip[2], ip[3], ir[2], bcV(1, 0.08, 0), H, shadow);
  // the glowing point it all comes out of: a hot bead + a soft additive glow, riding the fingertip
  const tip = new THREE.Group(), tipAt = ip[3].clone().addScaledVector(new THREE.Vector3().subVectors(ip[3], ip[2]).normalize(), ir[2] * 0.7);
  const bead = bcBlob(H.tip, true); bead.scale.setScalar(0.0052); bead.userData.noWrap = true; tip.add(bead);
  const halo = new THREE.Sprite(new THREE.SpriteMaterial({ map: bcHandGlow(), color: H.halo, transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending, depthWrite: false }));
  halo.scale.setScalar(0.034); tip.add(halo);
  // the bang: a ragged burst of blood out of the fingertip (normal blend so it stays red on grass + sky) round a white-hot core
  const flare = new THREE.Group(), fm = new THREE.MeshBasicMaterial({ map: bcFlareTex(), color: H.halo, transparent: true, depthWrite: false, side: THREE.DoubleSide, fog: false });
  const face = new THREE.Mesh(new THREE.PlaneGeometry(0.07, 0.07), fm); face.userData.noWrap = true; flare.add(face);
  for (const r of [0, Math.PI / 2]) { const sd = new THREE.Mesh(new THREE.PlaneGeometry(0.1, 0.04), fm); sd.rotation.set(0, Math.PI / 2, r); sd.position.z = -0.028; sd.userData.noWrap = true; flare.add(sd); }
  const hot = new THREE.Sprite(new THREE.SpriteMaterial({ map: bcHandGlow(), color: H.tip, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false })); hot.scale.setScalar(0.04); flare.add(hot);
  flare.userData.face = face; flare.visible = false; tip.add(flare);
  tip.position.copy(tipAt); ib[2].updateMatrixWorld(true); ib[2].attach(tip);
  // blood running up the top of the finger to the tip
  for (let i = 0; i < 3; i++) {
    const up = bcV(0.25, 1, 0).normalize().multiplyScalar(ir[i] * 0.86);
    bcLine(ib[i], ip[i].clone().add(up), ip[i + 1].clone().add(up).addScaledVector(bcV(0, 0, i === 2 ? 0.004 : 0), 1), 0.0021, H.vein);
  }
  // middle, ring, pinky curled into the palm under the index (their nails show under the thumb)
  const curl = [];
  for (const [mcp, lens, r, ang, drop] of [
    [bcV(0.004, 0.0045, -0.038), [0.044, 0.027, 0.019], [0.0101, 0.0094, 0.0087], [1.42, 1.78, 0.95], 0.001],
    [bcV(0.004, -0.0155, -0.0355), [0.041, 0.026, 0.018], [0.0096, 0.0089, 0.0083], [1.48, 1.78, 0.95], 0.002],
    [bcV(0.003, -0.034, -0.0305), [0.034, 0.02, 0.016], [0.0084, 0.0078, 0.0073], [1.55, 1.8, 0.95], 0.003],
  ]) {
    const pts = bcCurled(mcp, lens, ang, drop), fb = bcBones(g, pts, r, H.skin);
    let a = 0;
    fb.forEach((j, i) => { a += ang[i]; curl.push({ j, q: j.quaternion.clone(), a: ang[i] }); });
    bcNail(fb[2], pts[2], pts[3], r[2], bcV(Math.cos(a), 0, -Math.sin(a)), H, false);
    const k = bcBlob(H.knuckle); k.scale.set(0.0062, 0.0088, 0.009); k.position.set(mcp.x + 0.009, mcp.y, mcp.z + 0.003); g.add(k); // big knuckle on the back
  }
  const ik = bcBlob(H.knuckle); ik.scale.set(0.0062, 0.0092, 0.0095); ik.position.set(0.012, 0.025, -0.033); g.add(ik);
  // thumb: up like a cocked hammer, leaning back a little. its pivot is the root by the wrist so it can drop forward onto the index
  const thumb = new THREE.Group(); thumb.position.set(-0.01, 0.012, 0.026); g.add(thumb);
  const tp = [bcV(-0.01, 0.012, 0.026), bcV(-0.013, 0.037, 0.004), bcV(-0.011, 0.064, -0.004), bcV(-0.008, 0.084, 0)], tr = [0.0135, 0.0118, 0.0108];
  const tb = bcBones(thumb, tp, tr, H.skin, 1);
  bcNail(tb[2], tp[2], tp[3], tr[2], bcV(0.5, -0.1, 0.86), H, shadow);
  if (shadow) { // charred: cracks glowing through the thumb + the side of the index, where you can see them
    const back = bcV(0.45, 0, 0.9).normalize();
    for (let i = 0; i < 2; i++) bcLine(tb[i + 1], tp[i + 1].clone().addScaledVector(back, tr[i + 1] * 0.9), tp[i + 2].clone().addScaledVector(back, tr[i + 1] * 0.82).add(bcV(0, -0.004, 0)), 0.0015, H.vein);
    const side = bcV(-1, 0.3, 0).normalize();
    bcLine(ib[0], ip[0].clone().addScaledVector(side, ir[0] * 0.86).add(bcV(0, 0, -0.008)), ip[1].clone().addScaledVector(side, ir[0] * 0.84), 0.0014, H.vein);
  }
  // the back of the hand: veins running down to the index knuckle, and the brand that gives it its name
  const bx0 = 0.0175;
  const path = (pts, th) => { for (let i = 0; i < pts.length - 1; i++) bcLine(g, bcV(bx0, pts[i][0], pts[i][1]), bcV(bx0, pts[i + 1][0], pts[i + 1][1]), th, H.veinDark); };
  path([[-0.006, 0.05], [-0.003, 0.04], [0.003, 0.03], [0.007, 0.019], [0.011, 0.007], [0.016, -0.008], [0.019, -0.019], [0.021, -0.028]], 0.0017); // the big one, wrist to index knuckle
  path([[0.007, 0.019], [0.0, 0.012], [-0.005, 0.002], [-0.007, -0.01], [-0.006, -0.026]], 0.0013); // off to the middle knuckle
  path([[0.011, 0.007], [0.019, 0.003], [0.025, -0.004], [0.029, -0.013]], 0.0011);
  path([[-0.026, 0.048], [-0.024, 0.036], [-0.027, 0.024], [-0.03, 0.01], [-0.028, -0.008]], 0.0012); // pinky side
  for (const s of [-1, 1]) {
    const c = bcV(bx0 + 0.0004, -0.013, -0.004), u = bcV(0, 0.7071 * s, 0.7071).multiplyScalar(0.0125);
    bcLine(g, c.clone().sub(u), c.clone().add(u), 0.0034, H.tip);
  }
  if (shadow) { // charred: glowing cracks across the back and up the knuckles
    for (const [a, b] of [[bcV(bx0, 0.028, 0.03), bcV(bx0, 0.016, 0.004)], [bcV(bx0, 0.016, 0.004), bcV(bx0, 0.024, -0.016)], [bcV(bx0, -0.036, 0.0), bcV(bx0, -0.026, -0.024)],
      [bcV(bx0, -0.04, 0.03), bcV(bx0, -0.03, 0.012)]]) bcLine(g, a, b, 0.0016, H.vein);
  }
  // forearm + sleeve: viewmodel only, so it stays out of the model (icons, previews + skin effects only see the hand); weapons.js adds it
  const arm = new THREE.Group();
  const wrist = cylZ(0.027, 0.07, H.skin, 0.0, -0.007, 0.07, 10); wrist.scale.x = 0.7; arm.add(wrist);
  const fg = new THREE.CylinderGeometry(0.029, 0.036, 0.23, 10).rotateX(-Math.PI / 2);
  const fore = new THREE.Mesh(fg, M(H.skin)); fore.position.set(0, -0.009, 0.19); fore.scale.x = 0.8; arm.add(fore);
  const sg = new THREE.CylinderGeometry(0.041, 0.047, 0.16, 12).rotateX(-Math.PI / 2);
  const sleeve = new THREE.Mesh(sg, M(H.sleeve)); sleeve.position.set(0, -0.01, 0.29); sleeve.scale.x = 0.9; arm.add(sleeve);
  const cuff = cylZ(0.043, 0.024, H.cuff, 0, -0.01, 0.214, 12); cuff.scale.x = 0.9; arm.add(cuff);
  g.updateMatrixWorld(true);
  const mz = new THREE.Vector3(); tip.getWorldPosition(mz);
  Object.assign(g.userData, { index, thumb, curl, fingertip: tip, flare, bare: arm, muzzle: mz, len: 0.2 });
}
WB.bloodcross = (g) => fingerGun(g, false);
SKIN_BUILD.bloodcross_shadow = (g) => fingerGun(g, true);
HAT_AT.bloodcross = [[0.004, 0.036, -0.05], 0.028]; // on top of the index, in front of the thumb
HAT_AT.bloodcross_shadow = HAT_AT.bloodcross;

// Blood Cross bolt: a white-hot core in a red glow, long along Z. bloodcross.js turns every one of these to face where it's
// flying and draws its trail, live or in a replay, so this keeps a list of them
export const BLOOD_BOLTS = new Set();
let bloodBoltGeo = null;
const bcGlowMat = (color, opacity) => new THREE.MeshBasicMaterial({ color, transparent: true, opacity, depthWrite: false });
function bloodBolt(g) {
  bloodBoltGeo ||= [new THREE.OctahedronGeometry(1, 0), new THREE.SphereGeometry(1, 8, 6)];
  const core = new THREE.Mesh(bloodBoltGeo[0], new THREE.MeshBasicMaterial({ color: 0xff4a5c }));
  core.scale.set(0.05, 0.05, 0.22); core.position.z = -0.06;
  const sh = new THREE.Mesh(bloodBoltGeo[0], bcGlowMat(0xd0001a, 0.6));
  sh.scale.set(0.1, 0.1, 0.44); sh.position.z = 0.06;
  const halo = new THREE.Mesh(bloodBoltGeo[1], bcGlowMat(0xff0018, 0.2));
  halo.scale.set(0.17, 0.17, 0.5); halo.position.z = 0.12;
  for (const m of [core, sh, halo]) { m.userData.noWrap = true; g.add(m); }
  g.userData.bolt = { core, shell: sh, halo };
  BLOOD_BOLTS.add(g);
}

const MODEL_BUILD = {
  ...SKIN_BUILD,
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
WB.laser = laserBuild; // Big Laser Pointer (gearmodels.js)
WB.nailgun = nailgunBuild; WB.tennis = tennisBuild; WB.cart = cartCannonBuild; // the new primaries (primmodels.js)
Object.assign(MODEL_BUILD, { nailgun_staple: nailgunStaple, tennis_machine: tennisMachine, cart_basket: cartBasket }); // ...and their skins
Object.assign(WB, { pistol: pistolBuild, akimbo: akimboBuild, sawnoff: sawnoffBuild }); // plain sidearms (sidemodels.js)
Object.assign(HAT_AT, { pistol: [[0, 0.05, -0.07], 0.07], akimbo: [[0, 0.06, -0.08], 0.07], sawnoff: [[0, 0.047, 0.02], 0.08] });
// knives + swords live in blades/ (one file each, real proportions): base weapons go in WB, skins in MODEL_BUILD
for (const [id, mod] of Object.entries(BLADES)) {
  (COSMETICS.model[id] ? MODEL_BUILD : WB)[id] = mod.build;
  if (mod.hatAt) HAT_AT[id] = mod.hatAt;
}
// the lasso + its skins live in lasso_model.js, registered the same way
for (const [id, mod] of Object.entries(LASSO_MODELS)) {
  (COSMETICS.model[id] ? MODEL_BUILD : WB)[id] = mod.build;
  if (mod.hatAt) HAT_AT[id] = mod.hatAt;
}

// iron sights: a rear notch + front post (glowing tip) on top of the gun, at one height, so the line of sight
// runs over the top of the gun. ADS puts that line on the centre of the screen and the gun hangs below it.
const SIGHTS = { ar: 'iron', smg: 'iron', redline: 'iron', revolver: 'iron', banana: 'iron', shotgun: 'bead' };
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
  g.userData.wid = id; // wrap zones look up their rule by model (or weapon) id
  g.userData.hatAt = HAT_AT[variant ? model : id];
  const bl = authored('w_' + (variant ? model : id)); // made in Blender, in this model's own space: swap it in as is (skins too)
  if (bl) {
    for (const c of [...g.children]) if (c !== g.userData.tip) g.remove(c);
    g.add(bl.obj);
    const mt = bl.meta;
    if (mt.muzzle) g.userData.muzzle = new THREE.Vector3(...mt.muzzle);
    if (mt.sight) g.userData.sight = { y: mt.sight.y, z: mt.sight.z };
    if (Array.isArray(mt.ads) && mt.ads.every(Number.isFinite)) g.userData.adsPose = mt.ads; // no sights: its own aiming pose
    if (Array.isArray(mt.port) && mt.port.length === 3 && mt.port.every(Number.isFinite)) g.userData.port = new THREE.Vector3(...mt.port); // where its shells fly out (a bullpup's port is by your cheek)
    if (mt.hatAt) g.userData.hatAt = mt.hatAt; else delete g.userData.hatAt;
    g.userData.glb = 'blender';
    g.userData.jf = mt; // the sidearms read their moving parts' names from it (sidearms.js)
    g.userData.wid = 'bl_' + (variant ? model : id); // wrap zones come from the Blender parts' own names (_wzA / _wzB / _wzN), not the code model's rule
    bindAuthored(g, mt); // needle, vents, barrels, ember, card fan, bow string + the pump / cylinder / hammer / bolt that the viewmodel moves
    secAuthored(id, g, mt); // the radar gun's speed readout, the water pistol's tank level, the taser's ARMED light
    bindRifle(g, mt); // rifle pack: mag, charging handle, lever, feed cover, belt links, barrel heat
    if (Array.isArray(mt.glint) && mt.glint.length && mt.glint.every((a) => Array.isArray(a) && a.length === 4 && a.every(Number.isFinite))) addGlint(g, mt.glint);
    applySkin(g, skin);
    return g;
  }
  const glb = variant ? null : fitted('w_' + id, { alignZ: true, size: g.userData.len, zOffset: g.userData.muzzle.z / 2 });
  if (glb) delete g.userData.hatAt; // a generated model has its own shape: fall back to measuring it
  if (glb) g.userData.wid = 'glb_' + id; // ...and its own parts: zones come from _wzA/_wzB names or the colour guess
  if (glb) {
    for (const c of [...g.children]) if (c !== g.userData.tip) g.remove(c);
    if (g.userData.tip) g.userData.tip.visible = true;
    g.add(glb);
  }
  if (!glb) addSights(id, g);
  if (BLADES[variant ? model : id]) glossBlade(g); // knives + katanas stay code-built (real-reference models): same gloss as the Blender ones
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
// ------------------------------------------------------------ Smarty Pants: Big Glasses + Overalls
// Big Glasses: oversized round frames (each lens wider than an eye socket, together wider than the head), thick black
// rims, white tape round the bridge where they broke, arms back to the ears. just the glasses (no eyes behind them)
function bigGlasses(H, fz) {
  const F = 0x141416, y = 0.172, R = 0.066, x = 0.084, z = fz - 0.012;
  const glass = jankify(new THREE.MeshLambertMaterial({ color: 0xcfeeff, transparent: true, opacity: 0.28, depthWrite: false }));
  for (const sx of [-1, 1]) {
    const rim = new THREE.Mesh(new THREE.TorusGeometry(R, 0.013, 6, 18), M(F)); rim.position.set(sx * x, y, z); rim.scale.z = 1.6; H.add(rim);
    const ln = new THREE.Mesh(new THREE.CircleGeometry(R, 18), glass); ln.position.set(sx * x, y, z); ln.rotation.y = Math.PI; ln.renderOrder = 2; ln.userData.noWrap = true; H.add(ln);
    const gl = bx(0.026, 0.008, 0.002, 0xffffff, sx * x - 0.028, y + 0.035, z - 0.002, true); gl.rotation.z = 0.6; H.add(gl); // glint
    // arm back along the side of the head, hooked down behind the ear
    const arm = bx(0.012, 0.014, 0.16, F, sx * 0.13, y + 0.01, fz + 0.075); arm.rotation.y = -sx * 0.18; H.add(arm);
    const hook = bx(0.012, 0.05, 0.014, F, sx * 0.118, y - 0.012, fz + 0.155); hook.rotation.x = 0.4; H.add(hook);
    H.add(bx(0.022, 0.022, 0.016, F, sx * (x + R + 0.004), y + 0.012, z)); // hinge block
  }
  H.add(bx(0.04, 0.014, 0.014, F, 0, y + 0.01, z)); // bridge
  const tape = bx(0.028, 0.04, 0.03, 0xf4f1e6, 0, y + 0.008, z - 0.002); tape.rotation.z = 0.12; H.add(tape); // the tape round it (it broke)
  for (const dx of [-0.007, 0.006]) { const w = bx(0.002, 0.042, 0.032, 0xc8c2ae, dx, y + 0.008, z - 0.002); w.rotation.z = 0.12; H.add(w); } // tape wraps
}
// overalls default to denim; a picked bottoms colour wins, and a team game paints them the team colour like any bottoms
function overallsColor(lk, c) { return lk && lk.bottomColor ? new THREE.Color(lk.bottomColor).getHex() : lk && lk.teamed ? c : 0x3b64a8; }
// the bib up the front of the chest with a pocket (and a pencil in it), straps over both shoulders, brass buckles,
// side buttons at the hips, a little back panel the straps go into. thick = how far a jacket / hoodie sticks out
function overallsBib(Bd, col, thick) {
  const D = col, ST = 0xffc21a, SEAM = new THREE.Color(col).offsetHSL(0, -0.05, 0.16).getHex();
  const fz = -0.15 - thick * 0.6;
  const bib = bx(0.25, 0.27, 0.03, D, 0, 1.235, fz); bib.rotation.x = -0.1; Bd.add(bib);
  for (const sx of [-1, 1]) { const sm = bx(0.008, 0.25, 0.034, SEAM, sx * 0.112, 1.235, fz); sm.rotation.x = -0.1; Bd.add(sm); } // stitching down the edges
  const pk = bx(0.13, 0.1, 0.01, new THREE.Color(col).offsetHSL(0, 0, -0.05).getHex(), 0.0, 1.27, fz - 0.024); pk.rotation.x = -0.1; Bd.add(pk); // bib pocket
  const pks = bx(0.13, 0.008, 0.012, SEAM, 0, 1.318, fz - 0.03); pks.rotation.x = -0.1; Bd.add(pks); // its top hem
  // a pencil in the pocket: yellow, a pink eraser, a silver band
  const pen = cylZ(0.013, 0.14, 0xffd21a, 0.04, 1.35, fz - 0.03, 6); pen.rotation.x = Math.PI / 2 - 0.12; pen.rotation.y = 0.0; pen.rotation.z = -0.15; Bd.add(pen);
  const er = cylZ(0.013, 0.022, 0xff7ab8, 0.049, 1.43, fz - 0.04, 6); er.rotation.x = Math.PI / 2 - 0.12; er.rotation.z = -0.15; Bd.add(er);
  const fe = cylZ(0.0135, 0.012, 0xc8ccd4, 0.048, 1.416, fz - 0.038, 6); fe.rotation.x = Math.PI / 2 - 0.12; fe.rotation.z = -0.15; Bd.add(fe);
  // straps: up from the bib corners, over the shoulders, down the back into the back panel
  for (const sx of [-1, 1]) {
    const fr = bx(0.05, 0.2, 0.02, D, sx * 0.1, 1.44, fz - 0.005); fr.rotation.x = 0.18; Bd.add(fr);
    Bd.add(bx(0.05, 0.022, 0.3, D, sx * 0.105, 1.545, 0.0)); // over the shoulder
    const bk = bx(0.05, 0.4, 0.02, D, sx * 0.09, 1.34, 0.16 + thick); bk.rotation.z = sx * 0.12; Bd.add(bk);
    const bu = bx(0.06, 0.04, 0.014, ST, sx * 0.1, 1.355, fz - 0.024); bu.rotation.x = -0.1; Bd.add(bu); // brass buckle
    Bd.add(bx(0.026, 0.012, 0.016, 0x8a6a10, sx * 0.1, 1.355, fz - 0.03)); // its bar
    Bd.add(ball(0.016, ST, sx * 0.175, 1.04, -0.03)); // hip button
  }
  Bd.add(bx(0.2, 0.12, 0.024, D, 0, 1.12, 0.14 + thick * 0.5)); // back panel
}
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
    case 'catears': ch.ears = catEars(H, look); break;
  }
  const fz = -0.15; // front of the face
  switch (look.face) {
    case 'shades': at(H, bx(0.22, 0.05, 0.02, 0x111111, 0, 0.17, fz, true)); at(H, bx(0.26, 0.015, 0.015, 0x111111, 0, 0.19, fz)); break;
    case 'mustache': at(H, bx(0.12, 0.025, 0.02, 0x4a2a10, 0, 0.09, fz + 0.01)); break;
    case 'clown': at(H, ball(0.035, 0xff2020, 0, 0.12, fz - 0.01, true)); break;
    case 'eyepatch': at(H, bx(0.06, 0.05, 0.02, 0x111111, 0.05, 0.17, fz, true)); at(H, bx(0.28, 0.012, 0.012, 0x111111, 0, 0.19, fz + 0.01)); break;
    case 'bandana': at(H, bx(0.22, 0.09, 0.03, 0xc02030, 0, 0.07, fz + 0.01)); break;
    case 'visor': at(H, bx(0.24, 0.05, 0.02, 0x3ee6c8, 0, 0.17, fz - 0.005, true)); break;
    case 'bigglasses': bigGlasses(H, fz); break; // Smarty Pants
    case 'goggles': { // old-school flight goggles: leather strap round the head, two round amber lenses
      const s = new THREE.Mesh(new THREE.CylinderGeometry(0.153, 0.153, 0.035, 12, 1, true), M(0x6a3f1e)); s.position.y = 0.17; H.add(s);
      for (const sx of [-1, 1]) { at(H, cylZ(0.048, 0.04, 0x8a5a2b, sx * 0.058, 0.175, fz + 0.005, 10)); at(H, cylZ(0.036, 0.01, 0xffb84d, sx * 0.058, 0.175, fz - 0.016, 10, true)); }
      break;
    }
  }
  // back stuff hangs off the upper back (chest back surface ~z 0.15) and is strapped over the shoulders
  const thick = look.top === 'runner' ? 0.04 : look.top === 'jacket' || look.top === 'suit' || look.top === 'hoodie' ? 0.03 : 0;
  if (look.bottom === 'overalls' && look.top !== 'maid') overallsBib(Bd, overallsColor(look, c), thick); // (the apron covers it)
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
      piv.rotation.x = -0.1; // negative = the bottom edge swings back (+z), away from the body
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
    case 'cattail': catTail(ch, look, look.top === 'maid' ? 0.2 : look.bottom === 'skirt' ? 0.19 : 0.125); break; // out from under the skirt
  }
}

// ------------------------------------------------------------ runner jacket: an oversized hi-vis bomber. black yoke, sides,
// cuffs and ribbed band, reflective sleeve tape, an off-centre zip left open at the collar. shapes are built once and shared
const RUN_YELLOW = 0xffd20f, RUN_INK = 0x1c1c21, RUN_TAPE = 0xc6ccd4, RUN_TEE = 0x2b2b31, RUN_WHITE = 0xf4f4f4;
const RUN_SQ = 2.6, RUN_ZIP = Math.PI * 0.955; // how square the body is; where the zip runs (a bit right of centre)
// body rings, bottom to top: y, half width, half depth, how far the zip has opened (radians round the body)
const RUN_RINGS = [
  [1.085, 0.2, 0.138, 0], [1.115, 0.252, 0.172, 0], [1.25, 0.259, 0.176, 0], [1.38, 0.274, 0.186, 0], // tucked in, blousy, a seam, chest
  [1.455, 0.272, 0.178, 0.02], [1.505, 0.26, 0.17, 0.06], [1.53, 0.2, 0.142, 0.1], // yoke + shoulders, zip pulled down to here
  [1.54, 0.12, 0.108, 0.15], [1.652, 0.156, 0.142, 0.27], // stand-up collar, flared and open
];
function runPt(y, w, d, u) { // round a squashed superellipse: u = 0 at the back, PI/2 right, PI front
  const s = Math.sin(u), c = Math.cos(u), e = 2 / RUN_SQ;
  return [Math.sign(s) * Math.abs(s) ** e * w, y, Math.sign(c) * Math.abs(c) ** e * d];
}
// quads between rings of points (rings stacked upwards, points going round). keep(i, j) picks the quads
function runSheet(rings, keep, inward = false) {
  const pos = [], idx = [], n = rings[0].length;
  for (let i = 0; i < rings.length - 1; i++) for (let j = 0; j < n; j++) {
    if (!keep(i, j)) continue;
    const k = pos.length / 3;
    for (const p of [rings[i][j], rings[i][(j + 1) % n], rings[i + 1][(j + 1) % n], rings[i + 1][j]]) pos.push(p[0], p[1], p[2]);
    if (inward) idx.push(k, k + 2, k + 1, k, k + 3, k + 2); else idx.push(k, k + 1, k + 2, k, k + 2, k + 3);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(new Float32Array((pos.length / 3) * 2), 2));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}
function runDone(g) { // centred on itself (outlines + gibs scale and spin about the middle); every jacket shares it
  g.computeBoundingBox();
  const c = g.boundingBox.getCenter(new THREE.Vector3());
  g.translate(-c.x, -c.y, -c.z);
  g.userData.shared = true; g.userData.at = c;
  return g;
}
function runLathe(prof, segs = 6) { // [radius, distance down the arm] pairs -> a tube along -z
  const g = new THREE.LatheGeometry(prof.map(([r, d]) => new THREE.Vector2(r, -d)).reverse(), segs);
  return g.rotateX(Math.PI / 2);
}
function runRib(r0, r1, d0, d1, n, w = r0, dz = r0) { // ribbed knit: every other column sits in a bit
  const ring = (d) => Array.from({ length: n }, (_, j) => { const u = (j / n) * Math.PI * 2, f = j % 2 ? r1 / r0 : 1; return [Math.sin(u) * w * f, d, Math.cos(u) * dz * f]; });
  return runSheet([ring(d0), ring(d1)], () => true);
}
function runBox(w, h, d, m) { return new THREE.BoxGeometry(w, h, d).applyMatrix4(m); }
let runGeo = null;
function runnerGeo() {
  if (runGeo) return runGeo;
  const J = {};
  // columns round the body (degrees, z = the two sides of the zip); the quad after each one belongs to a panel:
  // b back, s side (black), f front, - the open zip. lower-case = the right hand side
  const cols = [0, 30, 50, 70, 110, 130, 150, 'z', 'z', 210, 230, 250, 290, 310, 330], panel = 'bbbsfff-FFFSbbb';
  const seam = (a, k) => (a === 30 || a === 130 || a === 230 || a === 330 ? k : 1); // stitched panel lines front + back
  const ring = (y, w, d, g, k = 1) => cols.map((a, j) => runPt(y, w * seam(a, k), d * seam(a, k), a !== 'z' ? (a * Math.PI) / 180 : j === 7 ? RUN_ZIP - g : RUN_ZIP + g));
  const R = RUN_RINGS.map((r, i) => ring(...r, i > 0 && i < 4 ? 0.982 : 1)), body = (k) => (i, j) => i < 4 && panel[j] === k, open = (i, j) => panel[j] !== '-';
  J.frontR = runDone(runSheet(R, body('f'))); J.frontL = runDone(runSheet(R, body('F'))); J.back = runDone(runSheet(R, body('b')));
  J.sideR = runDone(runSheet(R, body('s'))); J.sideL = runDone(runSheet(R, body('S')));
  const lin = [[1.546, 0.108, 0.097, RUN_RINGS[7][3]], [1.645, 0.144, 0.13, RUN_RINGS[8][3]]].map((r) => ring(...r));
  J.yoke = runDone(mergeGeometries([runSheet(R, (i, j) => i >= 4 && open(i, j)), runSheet([R[8], lin[1]], open)])); // + collar + its rim
  J.lining = runDone(runSheet(lin, open, true));
  J.band = runDone(runRib(1, 0.955, 0.995, 1.095, 28, 0.222, 0.152));
  J.tee = runDone(new THREE.SphereGeometry(0.2, 6, 4).scale(1.2, 1.05, 0.82).translate(0, 1.34, 0)); // dark tee in the open collar
  J.cap = new THREE.SphereGeometry(0.086, 8, 6); J.cap.userData.shared = true; J.cap.userData.at = new THREE.Vector3(); // puffy shoulders
  // zip: tape up the front, pull where it stops. silver bits share it
  const zipAt = (i, du = 0) => runPt(RUN_RINGS[i][0], RUN_RINGS[i][1] * 1.01, RUN_RINGS[i][2] * 1.01, RUN_ZIP + du);
  const zt = [zipAt(3, -0.01), zipAt(3, 0.01)], zry = Math.atan2(zt[1][2] - zt[0][2], -(zt[1][0] - zt[0][0])), silver = [];
  for (let i = 1; i < 4; i++) {
    const a = zipAt(i), b = zipAt(i + 1), mid = new THREE.Vector3((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2);
    const len = Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]);
    const m = new THREE.Matrix4().makeRotationY(zry).multiply(new THREE.Matrix4().makeRotationX(Math.atan2(b[2] - a[2], b[1] - a[1])));
    silver.push(runBox(0.014, len + 0.004, 0.008, m.setPosition(mid)));
  }
  { const p = zipAt(4); silver.push(runBox(0.022, 0.042, 0.01, new THREE.Matrix4().makeRotationY(zry).setPosition(p[0], p[1] - 0.024, p[2] - 0.006))); }
  // patches: a black diamond with a white plus on the left chest, a stripe tab on the right. each sits flat on its facet
  const front = (y, x) => {
    let i = 1; while (i < 4 && RUN_RINGS[i][0] < y) i++;
    const t = (y - RUN_RINGS[i - 1][0]) / (RUN_RINGS[i][0] - RUN_RINGS[i - 1][0]), P = R[i].map((b, j) => R[i - 1][j].map((a, k) => a + (b[k] - a) * t));
    let j = 4; while (j < 10 && !((P[j][0] - x) * (P[j + 1][0] - x) <= 0 && P[j][0] !== P[j + 1][0])) j++;
    const a = P[j], b = P[j + 1], f = (x - a[0]) / (b[0] - a[0]);
    const m = new THREE.Matrix4().makeRotationY(Math.atan2(b[2] - a[2], -(b[0] - a[0]))); // local -z out of the facet
    return m.setPosition(x, y, a[2] + (b[2] - a[2]) * f);
  };
  const med = front(1.29, -0.13), tab = front(1.3, 0.13);
  const on = (m, x, y, z, rz = 0) => m.clone().multiply(new THREE.Matrix4().makeRotationZ(rz).setPosition(x, y, z));
  J.patch = runDone(mergeGeometries([runBox(0.078, 0.078, 0.012, on(med, 0, 0, -0.004, Math.PI / 4)), runBox(0.05, 0.08, 0.012, on(tab, 0, 0, -0.004))]));
  J.plus = runDone(mergeGeometries([runBox(0.052, 0.016, 0.008, on(med, 0, 0, -0.012)), runBox(0.016, 0.052, 0.008, on(med, 0, 0, -0.012))]));
  for (const dy of [-0.018, 0.018]) silver.push(runBox(0.05, 0.012, 0.006, on(tab, 0, dy, -0.011)));
  J.zip = runDone(mergeGeometries(silver));
  // a big unit number on the back (seven-segment blocks). left off when something covers the back
  const seg = { a: [0, 1, 1], b: [1, 0.5, 0], c: [1, -0.5, 0], d: [0, -1, 1], e: [-1, -0.5, 0], f: [-1, 0.5, 0], g: [0, 0, 1] };
  const digits = [];
  for (const [dx, segs] of [[-0.048, 'bc'], [0.048, 'abged']]) for (const s of segs) {
    const [sx, sy, flat] = seg[s];
    digits.push(runBox(flat ? 0.066 : 0.02, flat ? 0.02 : 0.066, 0.014, new THREE.Matrix4().makeTranslation(dx + sx * 0.023, 1.3 + sy * 0.056, 0.185)));
  }
  J.num = runDone(mergeGeometries(digits));
  // sleeves: puffy, gathered into ribbed cuffs, a reflective band round the upper arm and the forearm
  const arm = (j0, ry0, el, j1, ry1) => {
    const put = (g, j, ry) => g.rotateY(ry).translate(j[0], j[1], j[2]);
    return {
      sleeve: runDone(mergeGeometries([
        put(runLathe([[0.03, -0.05], [0.064, -0.02], [0.077, 0.06], [0.075, 0.2], [0.066, 0.295]]), j0, ry0), // rounded into the shoulder
        new THREE.SphereGeometry(0.066, 6, 4).translate(el[0], el[1], el[2]),
        put(runLathe([[0.066, -0.01], [0.07, 0.07], [0.064, 0.14], [0.054, 0.152]]), j1, ry1),
      ])),
      tape: runDone(mergeGeometries([
        put(runLathe([[0.074, 0.15], [0.083, 0.156], [0.083, 0.179], [0.074, 0.185]]), j0, ry0),
        put(runLathe([[0.067, 0.06], [0.076, 0.066], [0.076, 0.084], [0.067, 0.09]]), j1, ry1),
      ])),
      cuff: runDone(put(runRib(0.057, 0.051, 0.142, 0.19, 12).rotateX(-Math.PI / 2), j1, ry1)),
    };
  };
  J.armR = arm([0, 0, 0], 0, [-0.015, -0.005, -0.295], [-0.03, -0.01, -0.3], 0);
  J.armL = arm([0.005, -0.02, -0.005], -0.45, [0.14, -0.04, -0.28], [0.153, -0.04, -0.307], -0.9);
  return (runGeo = J);
}
const runMats = new Map();
function runMat(color) { // both faces: the jacket is thin sheets, and its bits shouldn't vanish when they flip over as gibs
  if (!runMats.has(color)) runMats.set(color, jankify(new THREE.MeshLambertMaterial({ color, flatShading: true, side: THREE.DoubleSide })));
  return runMats.get(color);
}
// col: the top colour (yellow unless you picked one; in a team game the team colour, like every other top)
function runnerJacket(body, arm, armL, lk, col, jank) {
  const J = runnerGeo(), C = runMat(col), K = runMat(RUN_INK);
  const at = (p, g, mat) => { const m = new THREE.Mesh(g, mat); m.position.copy(g.userData.at); p.add(m); return m; };
  at(body, J.tee, M(RUN_TEE));
  for (const g of [J.frontL, J.frontR, J.back, J.lining]) at(body, g, C);
  for (const g of [J.sideL, J.sideR, J.yoke, J.band]) at(body, g, K);
  at(body, J.patch, M(RUN_INK)); at(body, J.plus, M(RUN_WHITE)); at(body, J.zip, M(RUN_TAPE));
  if (!lk.back || lk.back === 'none') at(body, J.num, M(RUN_INK));
  for (const sx of [-1, 1]) at(body, J.cap, M(RUN_INK)).position.set(0.25 * sx, 1.45 + (sx > 0 ? jank.shoulder : 0), 0);
  for (const [p, s] of [[arm, J.armR], [armL, J.armL]]) { at(p, s.sleeve, C); at(p, s.tape, M(RUN_TAPE)); at(p, s.cuff, K); }
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
    const legs = bottom === 'pants' || bottom === 'overalls'; // full-length legs (overalls are denim unless you pick a colour)
    const LEG = bottom === 'overalls' ? overallsColor(lk, c) : BOT;
    const sleeves = top === 'tee' ? 'short' : top === 'hoodie' || top === 'jacket' || top === 'suit' ? 'long' : null;
    // legs: hip -> thigh -> knee -> shin -> foot
    for (const [leg, knee, sx] of [[legL, kneeL, -1], [legR, kneeR, 1]]) {
      leg.position.set(0.1 * sx, 0.92, 0);
      leg.add(ball(0.075, JT));
      leg.add(limb(0.07, 0.058, 0.42, SK, -0.22));
      if (legs) leg.add(limb(0.082, 0.07, 0.44, LEG, -0.22));
      knee.position.y = -0.44;
      knee.add(ball(0.062, JT));
      knee.add(limb(0.056, 0.045, 0.4, SK, -0.21));
      if (legs) knee.add(limb(0.068, 0.058, 0.38, LEG, -0.2));
      if (bottom === 'overalls') knee.add(limb(0.074, 0.072, 0.07, new THREE.Color(LEG).offsetHSL(0, -0.1, 0.12).getHex(), -0.34)); // rolled-up cuffs, the paler inside of the denim
      knee.add(bx(0.1, 0.06, 0.22, legs ? (bottom === 'overalls' ? 0x6b3a1a : 0x222222) : SK, 0, -0.43, -0.05)); // (overalls come with brown work boots)
      leg.add(knee);
      body.add(leg);
    }
    if (top === 'maid') { /* the dress has its own skirt (and covers the top of the pants) */ } else if (bottom === 'skirt') { const sk = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.28, 0.36, 8), M(BOT)); sk.position.y = 0.88; body.add(sk); }
    else body.add(bx(0.34, 0.18, 0.23, LEG, 0, 0.98, 0)); // shorts / top of the pants
    const MAID = lk.topColor ? TOP : lk.teamed ? c : 0x17141c; // the maid dress: black unless you pick a colour
    body.add(limb(0.1, 0.12, 0.16, top === 'none' || top === 'tank' ? SK : top === 'maid' ? MAID : TOP, 1.13)); // waist
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
    if (top === 'runner') runnerJacket(body, arm, armL, lk, lk.topColor ? TOP : lk.teamed ? c : RUN_YELLOW, jank); // teamed: team colour
    if (top === 'maid') maidDress({ body, arm, armL, kneeL, kneeR, head }, lk, MAID, legs);
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
  if (k === 'rigmissile') return buildRigMissile(); // overdrive rig missiles: they turn along their flight themselves
  if (k === 'cartp') return buildCart(); // shopping carts (replays draw them from the projectile list)
  const g = buildProjectileRaw(k, skin && typeof skin[3] === 'string' ? skin[3] : null);
  if (!g.userData.glb) g.userData.hatAt = HAT_AT['p_' + k];
  return applySkin(g, skin);
}
function buildProjectileRaw(k, model) {
  const g = new THREE.Group();
  if (k === 'loop') return buildLoopProjectile(g); // a lasso loop (lasso.js animates it live; this is for replays + late joiners)
  // made in Blender (tools/blender): as built, centred, nose to -z. a skin can have its own (a thrown croc is a croc)
  const bl = (model && COSMETICS.model[model] && COSMETICS.model[model].weapon === k && authored('pj_' + model)) || authored('pj_' + k);
  if (bl) {
    g.add(bl.obj);
    g.userData.glb = 'blender';
    if (bl.meta.hatAt) g.userData.hatAt = bl.meta.hatAt;
    if (bl.meta.tip) { const t = nodeIn(bl.obj, bl.meta.tip); if (t && t.isMesh) g.userData.tip = t; } // the arrowhead shows the tip type
    return g;
  }
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
  } else if (k === 'bloodcross') {
    bloodBolt(g);
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
  } else if (k === 'tennis') {
    g.add(tennisBall(0.1));
  } else if (k === 'calc') {
    g.add(calculator()); // pop quiz
  } else if (k === 'soap') {
    g.add(soapBubble(0.36, 16)); // a hair smaller than its 0.4 hit radius
  } else {
    const t = new THREE.Mesh(new THREE.TorusGeometry(0.18, 0.06, 4, 8, Math.PI * 0.8), M(0xffe135));
    g.add(t);
    g.add(bx(0.04, 0.04, 0.06, 0x3a2a10, 0.18, 0, 0));
  }
  return g;
}

// a shopping cart: the Blender one (p_cart) when it's loaded, else the code one. feet at y 0, nose at -z
export function buildCart() {
  const bl = authored('p_cart');
  const g = new THREE.Group();
  if (bl) { g.add(bl.obj); g.userData.glb = true; } else g.add(cartModel());
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

// ------------------------------------------------------------ soap bubbles (Bubble Wand)
// see-through in the middle, a thin-film rainbow toward the rim that swirls and shifts with the angle you see it at,
// two little window glints, and a soft wobble. wob = how much it wobbles, uAlpha fades it (pop).
const SOAP_TIME = { value: 0 };
const SOAP_VS = `
uniform float uTime; uniform float uSeed; uniform float uWob;
varying vec3 vN; varying vec3 vV; varying vec3 vO;
void main() {
  vec3 p = position;
  float w = sin(uTime * 5.0 + uSeed + p.y * 3.0) + 0.7 * sin(uTime * 3.7 + uSeed * 1.7 + p.x * 2.6) + 0.5 * sin(uTime * 4.4 - uSeed + p.z * 2.2);
  p *= 1.0 + w * uWob;
  vec4 mv = modelViewMatrix * vec4(p, 1.0);
  vN = normalize(normalMatrix * normal);
  vV = -mv.xyz;
  vO = position;
  gl_Position = projectionMatrix * mv;
}`;
const SOAP_FS = `
uniform float uTime; uniform float uSeed; uniform float uAlpha;
varying vec3 vN; varying vec3 vV; varying vec3 vO;
vec3 film(float h) { return clamp(abs(fract(h + vec3(0.0, 0.667, 0.333)) * 6.0 - 3.0) - 1.0, 0.0, 1.0); }
void main() {
  vec3 n = normalize(vN), v = normalize(vV);
  if (!gl_FrontFacing) n = -n;
  float f = 1.0 - abs(dot(n, v));
  float th = vO.y * 0.8 + sin(vO.x * 3.0 + uTime * 0.9 + uSeed) * 0.3 + sin(vO.z * 4.0 - uTime * 0.7) * 0.2 + f * 1.2 + uTime * 0.04 + uSeed;
  vec3 c = mix(vec3(1.0), film(th), 0.7);
  vec3 r = reflect(-v, n);
  float g = pow(max(dot(r, normalize(vec3(-0.4, 0.75, 0.5))), 0.0), 30.0) + 0.5 * pow(max(dot(r, normalize(vec3(0.7, 0.2, 0.6))), 0.0), 60.0);
  float a = 0.05 + f * f * 0.8;
  gl_FragColor = vec4(c + g, clamp((a + g) * uAlpha, 0.0, 1.0));
}`;
const soapGeos = new Map();
export function soapBubble(r, seg = 16, wob = 0.05) {
  if (!soapGeos.has(seg)) soapGeos.set(seg, new THREE.SphereGeometry(1, seg, Math.round(seg * 0.7)));
  const mat = new THREE.ShaderMaterial({
    uniforms: { uTime: SOAP_TIME, uSeed: { value: Math.random() * 50 }, uWob: { value: wob }, uAlpha: { value: 1 } },
    vertexShader: SOAP_VS, fragmentShader: SOAP_FS, transparent: true, depthWrite: false, side: THREE.DoubleSide,
  });
  const m = new THREE.Mesh(soapGeos.get(seg), mat);
  m.scale.setScalar(r);
  m.renderOrder = 3;
  m.onBeforeRender = () => { SOAP_TIME.value = (performance.now() / 1000) % 1000; }; // keeps swirling in replays too
  return m;
}
// someone sealed in a giant soap bubble kicks and flails in there (ch = their mannequin, t = seconds, any clock)
export function soapFlail(ch, t) {
  ch.legL.rotation.x = Math.sin(t * 7) * 0.7; ch.legR.rotation.x = -Math.sin(t * 7) * 0.7;
  ch.kneeL.rotation.x = 0.6 + Math.sin(t * 7 + 1) * 0.4; ch.kneeR.rotation.x = 0.6 - Math.sin(t * 7 + 1) * 0.4;
  ch.armL.rotation.z = 2 + Math.sin(t * 9) * 0.5;
  ch.body.rotation.z = Math.sin(t * 1.4) * 0.3;
}

export function buildPeel() {
  const g = new THREE.Group();
  const bl = authored('pj_peel');
  if (bl) { g.add(bl.obj); return g; }
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
  const ud = g && g.userData;
  if (!ud || !ud.katBlade) return;
  const k = 1 + n * 0.55;
  ud.katBlade.scale.z = k;
  ud.muzzle.z = ud.katBlade.position.z - ud.katLen * k; // katLen = katBlade origin to the tip
}
