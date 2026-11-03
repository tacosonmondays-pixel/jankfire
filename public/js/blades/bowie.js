// Bowie skin. (placeholder: the old box model)
import { box, THREE } from './kit.js';

export function build(g) {
  g.add(box(0.04, 0.05, 0.13, 0x6b3a1a, 0, 0, 0.03));
  g.add(box(0.09, 0.02, 0.025, 0xc8a050, 0, 0.01, -0.05));
  g.add(box(0.014, 0.06, 0.27, 0xd0d6dc, 0, 0.015, -0.19));
  const tipB = box(0.014, 0.03, 0.06, 0xd0d6dc, 0, 0.035, -0.34); tipB.rotation.x = 0.5; g.add(tipB);
  g.userData.muzzle = new THREE.Vector3(0, 0.02, -0.36); g.userData.len = 0.45;
}
export const hatAt = [[0, 0.025, 0.04], 0.05];
