// Draws a map's Blender props (shared/props.js). The boxes they stand in for are skipped by world.js only while the
// model is loaded, so a missing file just leaves the old box look.
import * as THREE from 'three';
import { AUTHORED } from './glbkit.js';

const PAINT = { carred: 0xc8202c, carblue: 0x2050b0, carwhite: 0xe8e8e8, carblack: 0x26262a, cargreen: 0x2a8a4a, caryellow: 0xe8c020 };
const paintCache = new Map();
let group = null;

export const propModel = (id) => AUTHORED['p_' + id] || null;
export const hasProp = (id) => !!AUTHORED['p_' + id];

// one variant (a node named like the variant: 'bay', 'n7', ...) or the whole model, as a shared-geometry copy
function copyOf(a, v) {
  if (v === undefined || v === null) return a.scene.clone(true);
  const names = [String(v), 'n' + v, 'v' + v];
  let node = null;
  a.scene.traverse((o) => { if (!node && names.includes(o.name)) node = o; });
  if (!node) return a.scene.clone(true);
  const c = node.clone(true);
  c.position.set(0, 0, 0); c.rotation.set(0, 0, 0); c.scale.set(1, 1, 1); // variants sit side by side in the file
  return c;
}

function repaint(obj, color) { // car paint: the material called car_paint takes the map's colour
  const hex = PAINT[color];
  if (hex === undefined) return;
  obj.traverse((o) => {
    if (!o.isMesh || !o.material || o.material.name !== 'car_paint') return;
    const k = o.material.uuid + ':' + hex;
    if (!paintCache.has(k)) { const m = o.material.clone(); m.color.setHex(hex); m.userData.shared = true; m.onBeforeCompile = o.material.onBeforeCompile; paintCache.set(k, m); }
    o.material = paintCache.get(k);
  });
}

export function buildProps(scene, list) {
  if (group) { scene.remove(group); group = null; } // geometry + materials are shared with the loaded model: nothing to free
  if (!list || !list.length) return;
  group = new THREE.Group();
  group.name = 'props';
  for (const p of list) {
    const a = propModel(p.id);
    if (!a) continue;
    const o = copyOf(a, p.v);
    if (p.color) repaint(o, p.color);
    o.position.set(p.p[0], p.p[1], p.p[2]);
    o.rotation.y = -(p.r || 0) * Math.PI / 2; // quarter turns like the map builder's local frames
    if (p.s) o.scale.setScalar(p.s);
    o.traverse((m) => { if (m.isMesh) m.matrixAutoUpdate = false; m.updateMatrix(); });
    o.matrixAutoUpdate = false; o.updateMatrix();
    group.add(o);
  }
  scene.add(group);
}
