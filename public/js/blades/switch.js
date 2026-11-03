// Switchblade skin. (placeholder: the old box model)
// contract: userData.flipBlade = a group on the pivot pin at the front of the handle; the blade hangs off it towards -Z.
// the animation sets flipBlade.rotation.x: 0 = open, PI = shut (blade folded back into the handle, edge up, spine at the bottom).
import { box, THREE } from './kit.js';

export function build(g) {
  g.add(box(0.03, 0.04, 0.13, 0x111111, 0, 0, 0.02));
  g.add(box(0.032, 0.012, 0.13, 0xc8a050, 0, 0.022, 0.02));
  const pivot = new THREE.Group(); pivot.position.set(0, 0.01, -0.045); g.add(pivot);
  pivot.add(box(0.01, 0.035, 0.15, 0xe0e4ea, 0, 0, -0.075));
  g.userData.flipBlade = pivot;
  g.userData.muzzle = new THREE.Vector3(0, 0.01, -0.2); g.userData.len = 0.3;
}
export const hatAt = [[0, 0.02, 0.03], 0.05];
