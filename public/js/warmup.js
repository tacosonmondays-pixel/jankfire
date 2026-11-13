// shaders built before they're needed, so nothing stalls the first time it's on screen (the owner: "optimize game
// without pooping on teh graphics"). Measured before: 10-44 new shaders compiled in 12 s of play (a gun, a zombie, a
// mech or a cola can coming into view), each one a hitch while the browser waits on it. Now every Blender model is
// compiled against the real scene as it lands, and the whole map (hidden bits too) right after it's built. Same
// shaders, same picture: only the when changes. world.js calls warmTick inside renderFrame, with the frame's target
// bound, so the variant built here is exactly the one the real draw uses (render target colour space, lights, fog).
import { G } from './ctx.js';
import * as THREE from 'three';
import { AUTHORED, onGlb } from './glbkit.js';
import { reflectInfo } from './reflect.js';

const WQ = []; // [what, against]: an object vs the world or the gun's scene, or 'map' (all of G.scene)
export const WARM = { budget: 4 }; // ms a frame it may spend (a GLB is well under 1 ms of CPU: the GPU compiles in the background)
export const warmStats = { queued: 0, done: 0, ms: 0, fails: 0 };
const push = (o, k) => { WQ.push([o, k]); warmStats.queued++; };
const model = (id) => { const a = AUTHORED[id]; if (!a || !a.scene) return; push(a.scene, 'world'); if (a.meta && a.meta.kind === 'weapon') push(a.scene, 'vm'); }; // (guns: in your hands too, under the gun's own lights)
onGlb((id) => { if (id && G.scene) model(id); }); // (a model landing mid-match: before anything shows it)
// after a map is built (world.js loadMap): the map itself, then every model we have, against this map's lights and fog
export function warmScene() {
  WQ.length = 0; push(null, 'map');
  for (const id of Object.keys(AUTHORED)) model(id);
}
// the reflection snapshot (reflect.js) draws the world into a texture, not the screen: three builds a second, linear-
// colour variant of every shader for that. with mirrors on, the world and its models get that variant warmed too
let side = null;
const one = (r, o, k) => {
  if (k === 'map') r.compile(G.scene, G.camera);
  else if (k === 'vm') { if (G.vmScene && G.vmCamera) r.compile(o, G.vmCamera, G.vmScene); }
  else r.compile(o, G.camera, G.scene);
};
export function warmTick(r) {
  if (!WQ.length || !G.scene || !G.camera) return;
  const t0 = performance.now();
  while (WQ.length && performance.now() - t0 < WARM.budget) {
    const [o, k] = WQ.shift();
    try {
      one(r, o, k);
      if (k !== 'vm' && reflectInfo().on) { // (the gun never shows in a reflection)
        const prev = r.getRenderTarget();
        r.setRenderTarget(side || (side = new THREE.WebGLRenderTarget(1, 1))); one(r, o, k); r.setRenderTarget(prev);
      }
      warmStats.done++;
    } catch (e) { warmStats.fails++; console.warn('[gfx] shader warm-up skipped one:', e && e.message); }
  }
  warmStats.ms += performance.now() - t0;
}
