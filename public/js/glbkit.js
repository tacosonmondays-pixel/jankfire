// Models made in Blender (tools/blender/make_*.py). Unlike the old generated ones they're built in the game's own
// space (metres, -z forward, muzzle where the code model has it), so they go in exactly as they are: no fitting.
// The root node carries a `jf` JSON blob (muzzle, sight line, hat spot, moving parts...) from the Blender script.
// Visual only: collisions stay boxes. Anything missing or broken falls back to the code-built model.
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { jankify } from './jank.js';
import { G } from './ctx.js';
import { WEAPONS } from '/shared/weapons.js';
import { COSMETICS } from '/shared/cosmetics.js';

export const AUTHORED = {}; // id -> { scene, meta }

// skin models (w_<skin>.glb, pj_<skin>.glb) aren't downloaded up front: only the first time someone shows that skin
// (you, another player, the locker). Until then it's the code model; when it lands, onLateModel's callback rebuilds.
export const LAZY = new Map(); // id -> url
export const isLazy = (id) => { const m = /^(?:w|pj)_(.+)$/.exec(id); return !!(m && m[1] !== 'default' && Object.hasOwn(COSMETICS.model, m[1])); };
const late = { fn: null, t: 0, busy: 0 };
export function onLateModel(fn) { late.fn = fn; }
export const lateBusy = () => late.busy; // skins still downloading (tests wait for them)
function fetchLate(id) {
  const url = LAZY.get(id);
  LAZY.delete(id);
  late.busy++;
  new GLTFLoader().load(url, (gltf) => {
    late.busy--;
    if (!prepAuthored(id, gltf.scene)) return;
    clearTimeout(late.t);
    late.t = setTimeout(() => { if (late.fn) late.fn(id); }, 120); // a few at once: one rebuild
  }, undefined, (e) => { late.busy--; console.warn('model failed', id, e); });
}

// two looks to compare: 'glossy' (default: the materials as made in Blender + a studio reflection) and 'flat'
// (faceted Lambert like the code models, no gloss, each weapon's own colour from shared/weapons.js on its paint).
// pick with ?models=flat in the address or localStorage jf_models = 'flat'.
function styleFlag() {
  try {
    const q = new URLSearchParams(location.search).get('models');
    return (q || localStorage.getItem('jf_models') || 'glossy') === 'flat' ? 'flat' : 'glossy';
  } catch { return 'glossy'; }
}
export const MODEL_STYLE = styleFlag();

let env = null;
function envMap() { // one small studio reflection for glossy toy plastic and metal (the world's own materials don't use it)
  if (env || !G.renderer) return env;
  const pm = new THREE.PMREMGenerator(G.renderer);
  env = pm.fromScene(new RoomEnvironment(), 0.04).texture;
  pm.dispose();
  return env;
}

// the hotbar pictures, the locker / menu hero and the mode art draw with their own renderers (other WebGL contexts),
// where the game's reflection map is just black (mirror chrome came out as a black shape): each gets its own while it draws
const sideEnv = new WeakMap();
export function withEnv(renderer, root, draw) {
  if (!env || !renderer || renderer === G.renderer) return draw();
  let e = sideEnv.get(renderer);
  if (!e) { const pm = new THREE.PMREMGenerator(renderer); e = pm.fromScene(new RoomEnvironment(), 0.04).texture; pm.dispose(); sideEnv.set(renderer, e); }
  const swapped = [];
  root.traverse((o) => { if (o.material) for (const m of Array.isArray(o.material) ? o.material : [o.material]) if (m && m.envMap === env) { m.envMap = e; swapped.push(m); } });
  try { return draw(); } finally { for (const m of swapped) m.envMap = env; } // (materials are shared with the game's copies)
}

export function metaOf(scene) {
  let meta = null;
  scene.traverse((o) => {
    if (meta || !o.userData || typeof o.userData.jf !== 'string') return;
    try { meta = JSON.parse(o.userData.jf); } catch { meta = null; }
  });
  return meta;
}

// the flat look: same texture + colour, faceted Lambert, glows kept. paint = the weapon's colour for its paint parts
function flatOf(m, paint) {
  const f = new THREE.MeshLambertMaterial({
    name: m.name, color: paint ? paint.clone() : m.color.clone(), map: paint ? null : m.map, flatShading: true,
    transparent: m.transparent, opacity: m.opacity, side: m.side, alphaTest: m.alphaTest,
    emissive: m.emissive ? m.emissive.clone() : new THREE.Color(0), emissiveIntensity: m.emissiveIntensity ?? 1, emissiveMap: m.emissiveMap || null,
  });
  f.depthWrite = m.depthWrite;
  return f;
}

// returns true if it took the model (it was made in Blender)
export function prepAuthored(id, scene) {
  const meta = metaOf(scene);
  if (!meta) return false;
  const flat = MODEL_STYLE === 'flat';
  const e = flat ? null : envMap();
  const w = meta.kind === 'weapon' && WEAPONS[meta.id];
  const paint = flat && w && w.color && meta.paint ? new THREE.Color(w.color) : null;
  const swapped = new Map();
  scene.traverse((o) => {
    if (!o.isMesh) return;
    o.geometry.userData.shared = true; // clones share it: freeTree leaves it alone
    o.castShadow = false; o.receiveShadow = false;
    if (flat) {
      const conv = (m) => {
        if (!swapped.has(m)) swapped.set(m, flatOf(m, paint && meta.paint.includes(m.name) ? paint : null));
        return swapped.get(m);
      };
      o.material = Array.isArray(o.material) ? o.material.map(conv) : conv(o.material);
    }
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    for (const m of mats) {
      for (const k of ['map', 'emissiveMap']) { // crunchy pixels at every preset, like the rest of the game
        if (m[k]) { m[k].magFilter = THREE.NearestFilter; m[k].minFilter = THREE.NearestMipmapNearestFilter; m[k].anisotropy = 1; m[k].needsUpdate = true; }
      }
      if (e && 'envMap' in m) { m.envMap = e; m.envMapIntensity = m.metalness > 0.5 ? 0.9 : 0.3; }
      if (m.transparent) { m.depthWrite = false; o.renderOrder = 2; }
      if (m.emissive && m.emissive.getHex() && m.emissiveIntensity > 0) { o.userData.noWrap = true; m.toneMapped = false; } // glows stay glowing under a skin
      if (m.userData.shared) continue;
      m.userData.shared = true;
      jankify(m); // potato vertex snap
      m.needsUpdate = true;
    }
  });
  AUTHORED[id] = { scene, meta };
  return true;
}

// a fresh copy of an authored model (geometry + materials shared), or null
export function authored(id) {
  const a = AUTHORED[id];
  if (!a) { if (LAZY.has(id)) fetchLate(id); return null; }
  const c = a.scene.clone(true);
  c.userData.glbId = id;
  return { obj: c, meta: a.meta };
}
export const hasAuthored = (id) => !!AUTHORED[id];

export const nodeIn = (g, n) => { let r = null; g.traverse((o) => { if (!r && o.name === n) r = o; }); return r; };

// a Blender weapon's hooks into the game, the same ones the code models have: the Redline's tachometer needle and
// HP-hot vents, the minigun's spinning barrels, and our own moving parts (pump, cylinder, hammer, bolt)
export function bindAuthored(g, meta) {
  if (meta.needle) g.userData.needle = nodeIn(g, meta.needle);
  if (meta.barrels) g.userData.barrels = nodeIn(g, meta.barrels);
  if (meta.vents) { // one unlit material per gun (weapons.js sets its colour from your HP), like the code model
    const vm = jankify(new THREE.MeshBasicMaterial({ color: 0x401010 }));
    g.traverse((o) => { if (o.isMesh && o.material && o.material.name === meta.vents) { o.material = vm; o.userData.noWrap = true; } });
    g.userData.vents = vm;
  }
  // the code models' other hooks: the cigarette's ember (weapons.js swells it as you charge), the card fan (weapons.js
  // deals your hand onto it: each card is its face mesh, back + edge are its children), the slapper's hand, a scythe's blade
  if (meta.tip) {
    const t = nodeIn(g, meta.tip);
    if (t) { if (g.userData.tip && g.userData.tip.isObject3D && g.userData.tip !== t) g.userData.tip.removeFromParent(); g.userData.tip = t; }
  }
  for (const k of ['hand', 'blade', 'card']) if (meta[k]) { const n = nodeIn(g, meta[k]); if (n) g.userData[k] = n; }
  if (Array.isArray(meta.fan)) {
    const fan = meta.fan.map((n) => nodeIn(g, n)).filter((c) => c && c.isMesh);
    if (fan.length) { g.userData.fan = fan; for (const c of fan) c.traverse((o) => { o.userData.noWrap = true; }); }
  }
  if (meta.bow) bowRig(g, meta.bow);
  if (meta.noWrap) g.traverse((o) => { if (o.isMesh) o.userData.noWrap = true; }); // trophies (the Golden Sniper): no wrap covers them
  g.userData.parts = findParts(g, meta);
}

// the bow: weapons.js pulls the arrow back as you draw (and the code bow's whole string with it). here the string stays
// on the limb tips and bends to the nock instead, and the limbs flex. b = { string: [top, bottom] node names,
// tips: where each half meets its limb, nock: the arrow's nock at rest, limbs: [top, bottom] nodes (origin = where they
// leave the riser), flex: radians at full draw, draw: metres of pull at full draw }
const tmpV3 = new THREE.Vector3();
function bowRig(g, b) {
  const halves = (b.string || []).map((n) => nodeIn(g, n));
  if (halves.length !== 2 || !halves.every(Boolean) || !Array.isArray(b.tips) || !Array.isArray(b.nock)) return;
  const arrow = nodeIn(g, b.arrow || 'arrow');
  if (arrow) g.userData.arrow = arrow;
  if (b.arrowTip) { const t = nodeIn(g, b.arrowTip); if (t && t.isMesh) g.userData.arrowTip = t; }
  g.userData.string = new THREE.Object3D(); // weapons.js moves this one; the real string follows the arrow below
  g.updateMatrixWorld(true);
  const nock = new THREE.Vector3(...b.nock);
  const rig = { nock, draw: b.draw || 0.16, flex: b.flex || 0, halves: [], limbs: [] };
  halves.forEach((h, i) => {
    const T = new THREE.Vector3(...b.tips[i]), v0 = nock.clone().sub(T);
    const piv = new THREE.Object3D(); // +y of the pivot runs along the string half, so scale.y stretches it
    piv.position.copy(T); piv.rotation.x = Math.atan2(v0.z, v0.y);
    h.parent.add(piv); piv.updateMatrixWorld(true); piv.attach(h);
    rig.halves.push({ piv, T, len: v0.length() });
  });
  (b.limbs || []).forEach((n, i) => { const l = nodeIn(g, n); if (l) rig.limbs.push({ l, rx: l.rotation.x, sign: i ? -1 : 1 }); });
  g.userData.bowRig = rig;
}
function stepBow(g) {
  const r = g.userData.bowRig, a = g.userData.arrow;
  const d = a ? a.position.z : 0, k = Math.max(0, Math.min(1.2, d / r.draw));
  const phi = k * r.flex;
  for (const L of r.limbs) L.l.rotation.x = L.rx + L.sign * phi;
  r.halves.forEach((h, i) => {
    const L = r.limbs[i], s = i ? -1 : 1;
    const T = h.T, P = L ? L.l.position : null;
    let ty = T.y, tz = T.z;
    if (P && phi) { const y = T.y - P.y, z = T.z - P.z, c = Math.cos(s * phi), sn = Math.sin(s * phi); ty = P.y + y * c - z * sn; tz = P.z + y * sn + z * c; }
    h.piv.position.set(T.x, ty, tz);
    tmpV3.set(r.nock.x, r.nock.y - ty, r.nock.z + d - tz);
    h.piv.rotation.x = Math.atan2(tmpV3.z, tmpV3.y);
    h.piv.scale.y = Math.hypot(tmpV3.y, tmpV3.z) / h.len;
  });
}

// moving parts of Blender guns (nodes named in the file's metadata): the shotgun's forend racks with the pump
// animation, the revolver's cylinder turns a chamber and its hammer flicks on every shot, the sniper's bolt cycles
export function findParts(g, meta) {
  const p = {};
  if (meta.pump) { p.pump = nodeIn(g, meta.pump.node); if (p.pump) { p.pump0 = p.pump.position.z; p.travel = meta.pump.travel || 0.09; } else delete p.pump; }
  if (meta.cylinder) { p.cyl = nodeIn(g, meta.cylinder.node); p.step = meta.cylinder.step || Math.PI / 3; p.cylA = 0; p.cylTo = 0; if (!p.cyl) delete p.cyl; }
  if (meta.hammer) { p.hammer = nodeIn(g, meta.hammer.node); p.hamT = 1; if (!p.hammer) delete p.hammer; }
  if (meta.bolt) { p.bolt = nodeIn(g, meta.bolt.node); if (p.bolt) { p.bolt0 = p.bolt.position.z; p.lift = meta.bolt.lift || 1; p.btravel = meta.bolt.travel || 0.1; } else delete p.bolt; }
  return Object.keys(p).length ? p : null;
}
export function partsShot(g) {
  const p = g && g.userData.parts;
  if (!p) return;
  if (p.cyl) p.cylTo += p.step;
  if (p.hammer) p.hamT = 0;
}
export function stepParts(g, dt, an, at) {
  if (g && g.userData.bowRig) stepBow(g);
  const p = g && g.userData.parts;
  if (!p) return;
  if (p.pump) { // back on the way out, snap home: same timing as the pump_shotgun keys (0.1 s back, 0.17 s home)
    const k = an !== 'pump_shotgun' ? 0 : at < 0.1 ? at / 0.1 : at < 0.17 ? 1 - (at - 0.1) / 0.07 : 0;
    p.pump.position.z = p.pump0 + k * p.travel;
  }
  if (p.cyl) { p.cylA += (p.cylTo - p.cylA) * Math.min(1, dt * 24); p.cyl.rotation.z = -p.cylA; }
  if (p.hammer) { p.hamT = Math.min(1, p.hamT + dt); const t = p.hamT; p.hammer.rotation.x = t < 0.05 ? (t / 0.05) * 0.55 : Math.max(0, 0.55 * (1 - (t - 0.05) / 0.05)); }
  if (p.bolt) { // lift, run back, slam home, drop: the bolt_sniper keys (up by 0.12 s, back by 0.22, home by 0.3)
    let up = 0, back = 0;
    if (an === 'bolt_sniper') {
      up = at < 0.12 ? at / 0.12 : at < 0.3 ? 1 : at < 0.42 ? 1 - (at - 0.3) / 0.12 : 0;
      back = at < 0.12 ? 0 : at < 0.22 ? (at - 0.12) / 0.1 : at < 0.3 ? 1 - (at - 0.22) / 0.08 : 0;
    }
    p.bolt.rotation.z = up * p.lift;
    p.bolt.position.z = p.bolt0 + back * p.btravel;
  }
}

// knives + katanas (public/js/blades) stay code-built: they're real-reference models already. this gives them the
// Blender models' studio gloss so they sit with the rest: steel and brass get a satin metal sheen, wood a varnish, dark
// grips a satin coat, coloured bits candy paint. glows, see-through bits and the flat look stay as they are
const glossMats = new Map(), hsl = {};
function glossOf(m) {
  if (!m || !m.isMeshLambertMaterial || m.transparent || (m.emissive && m.emissive.getHex())) return m;
  let c = glossMats.get(m);
  if (c) return c;
  m.color.getHSL(hsl);
  const { h, s, l } = hsl;
  const steel = (s < 0.2 && l > 0.38) || (s < 0.25 && l > 0.6);
  const brass = h > 0.09 && h < 0.14 && s > 0.45 && s < 0.75 && l > 0.4 && l < 0.62;
  const wood = !brass && h > 0.02 && h < 0.13 && s > 0.25 && l < 0.85;
  const metal = steel || brass;
  c = new THREE.MeshPhysicalMaterial({
    name: m.name, color: m.color.clone(), map: m.map, side: m.side, flatShading: true,
    // steel stays as bright as the code blade: mostly its own colour + a strong studio reflection (full metalness
    // turned the flats dark grey whenever they face away from the lights)
    metalness: metal ? 0.35 : 0, roughness: metal ? 0.22 : wood ? 0.55 : l < 0.25 ? 0.42 : 0.36,
    clearcoat: metal ? 0 : wood ? 0.3 : l < 0.25 ? 0.35 : 0.6, clearcoatRoughness: 0.25,
    envMap: envMap(), envMapIntensity: metal ? 1.5 : 0.3,
  });
  c.userData.shared = true;
  jankify(c);
  glossMats.set(m, c);
  return c;
}
export function glossBlade(g) {
  if (MODEL_STYLE === 'flat' || !Object.keys(AUTHORED).length || !envMap()) return; // comes with the Blender set: no models loaded, no gloss
  g.traverse((o) => { if (o.isMesh) o.material = Array.isArray(o.material) ? o.material.map(glossOf) : glossOf(o.material); });
}
