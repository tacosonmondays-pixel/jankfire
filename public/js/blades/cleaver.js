// Cleaver skin. (placeholder: the old box model)
import { box, cyl, THREE } from './kit.js';

export function build(g) {
  g.add(cyl(0.02, 0.12, 0x2a1a10, 0, 0, 0.03, 6));
  g.add(box(0.01, 0.12, 0.2, 0xc8ccd0, 0, 0.04, -0.12));
  g.userData.muzzle = new THREE.Vector3(0, 0.05, -0.22); g.userData.len = 0.33;
}
export const hatAt = [[0, 0.1, -0.12], 0.07];
