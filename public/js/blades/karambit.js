// Karambit skin. (placeholder: the old box model)
// contract: userData.pivot = the centre of the finger ring (a Vector3 on the X axis line); the spin animations turn the whole
// knife round it (rotation about X), so the ring's hole must run along X and be centred there.
import { box, ring, THREE } from './kit.js';

export function build(g) {
  g.add(ring(0.03, 0.008, 0x222222, { axis: 'x', z: 0.09, tubeSegs: 4, segs: 8 }));
  g.userData.pivot = new THREE.Vector3(0, 0, 0.09);
  g.add(box(0.03, 0.04, 0.11, 0x2a2a2a, 0, 0, 0.01));
  for (let i = 0; i < 5; i++) { const s2 = box(0.01, 0.03, 0.045, 0xd8dde4, 0, -0.01 - i * i * 0.006, -0.06 - i * 0.04); s2.rotation.x = 0.15 + i * 0.22; g.add(s2); }
  g.userData.muzzle = new THREE.Vector3(0, -0.1, -0.25); g.userData.len = 0.33;
}
export const hatAt = [[0, 0.02, 0.01], 0.05];
