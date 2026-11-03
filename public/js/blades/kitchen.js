// Kitchen Knife skin. (placeholder: the old box model)
import { box, THREE } from './kit.js';

export function build(g) {
  g.add(box(0.03, 0.045, 0.12, 0x2a1a10, 0, 0, 0.02));
  g.add(box(0.008, 0.06, 0.24, 0xe8ecef, 0, 0.012, -0.16));
  g.userData.muzzle = new THREE.Vector3(0, 0.01, -0.29); g.userData.len = 0.36;
}
export const hatAt = [[0, 0.0225, 0.04], 0.05];
