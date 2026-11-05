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
