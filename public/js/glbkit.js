// Models made in Blender (tools/blender/make_*.py). Unlike the old generated ones they're built in the game's own
// space (metres, -z forward, muzzle where the code model has it), so they go in exactly as they are: no fitting.
// The root node carries a `jf` JSON blob (muzzle, sight line, hat spot, moving parts...) from the Blender script.
// Visual only: collisions stay boxes. Anything missing or broken falls back to the code-built model.
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { jankify } from './jank.js';
import { G } from './ctx.js';
import { WEAPONS } from '/shared/weapons.js';

export const AUTHORED = {}; // id -> { scene, meta }

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
  if (!a) return null;
  const c = a.scene.clone(true);
  c.userData.glbId = id;
  return { obj: c, meta: a.meta };
}
export const hasAuthored = (id) => !!AUTHORED[id];

const nodeIn = (g, n) => { let r = null; g.traverse((o) => { if (!r && o.name === n) r = o; }); return r; };

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
  g.userData.parts = findParts(g, meta);
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
