// Models made in Blender (tools/blender/make_*.py). Unlike the old generated ones they're built in the game's own
// space (metres, -z forward, muzzle where the code model has it), so they go in exactly as they are: no fitting.
// The root node carries a `jf` JSON blob (muzzle, sight line, hat spot...) from the Blender script.
// Visual only: collisions stay boxes. Anything missing or broken falls back to the code-built model.
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { jankify } from './jank.js';
import { G } from './ctx.js';

export const AUTHORED = {}; // id -> { scene, meta }

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

// returns true if it took the model (it was made in Blender)
export function prepAuthored(id, scene) {
  const meta = metaOf(scene);
  if (!meta) return false;
  const e = envMap();
  scene.traverse((o) => {
    if (!o.isMesh) return;
    o.geometry.userData.shared = true; // clones share it: freeTree leaves it alone
    o.castShadow = false; o.receiveShadow = false;
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

// moving parts of Blender guns (nodes named in the file's metadata): the shotgun's forend racks with the pump
// animation, the revolver's cylinder turns a chamber and its hammer flicks on every shot
export function findParts(g, meta) {
  const node = (n) => { let r = null; g.traverse((o) => { if (!r && o.name === n) r = o; }); return r; };
  const p = {};
  if (meta.pump) { p.pump = node(meta.pump.node); if (p.pump) { p.pump0 = p.pump.position.z; p.travel = meta.pump.travel || 0.09; } }
  if (meta.cylinder) { p.cyl = node(meta.cylinder.node); p.step = meta.cylinder.step || Math.PI / 3; p.cylA = 0; p.cylTo = 0; }
  if (meta.hammer) { p.hammer = node(meta.hammer.node); p.hamT = 1; }
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
}
