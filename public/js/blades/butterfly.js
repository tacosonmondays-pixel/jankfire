// Butterfly (balisong) skin. (placeholder: the old box model)
// contract: userData.handles = [h1, h2], two groups on the hinge pins at the base of the blade; each handle hangs off its
// group towards +Z. The animation sets h.rotation.x: 0 = open (handles back, in the hand), PI = shut (folded over the blade).
import { box, THREE } from './kit.js';

export function build(g) {
  const hinge = (x) => { const p = new THREE.Group(); p.position.set(x, 0, -0.045); g.add(p); return p; };
  const p1 = hinge(0.012), p2 = hinge(-0.012);
  p1.add(box(0.014, 0.03, 0.13, 0x8a8f99, 0, 0, 0.065));
  p2.add(box(0.014, 0.03, 0.13, 0x8a8f99, 0, 0, 0.065));
  for (let i = 0; i < 4; i++) p1.add(box(0.018, 0.004, 0.01, 0x333333, 0.004, 0.016, 0.025 + i * 0.03));
  g.add(box(0.008, 0.035, 0.15, 0xe8ecf0, 0, 0.005, -0.12));
  g.userData.handles = [p1, p2];
  g.userData.muzzle = new THREE.Vector3(0, 0.005, -0.2); g.userData.len = 0.33;
}
export const hatAt = [[0, 0.016, 0.02], 0.05];
