// Katana. (placeholder: the old box model)
// contract: userData.katBlade = a group at the front of the guard holding the whole blade (habaki to tip), pointing -Z;
// userData.katLen = its length. The katana grows with kills by scaling katBlade.scale.z, so nothing but the blade goes in it.
import { box, cyl, THREE } from './kit.js';

export function build(g) {
  g.add(cyl(0.022, 0.24, 0x1a1a1a, 0, 0, 0.06, 6));
  for (let i = 0; i < 5; i++) g.add(box(0.05, 0.012, 0.012, 0xc02030, 0, 0, 0.16 - i * 0.045));
  g.add(cyl(0.06, 0.015, 0xb08a3a, 0, 0, 0, 10));
  const bl = new THREE.Group(); bl.position.z = -0.07;
  bl.add(box(0.012, 0.04, 0.72, 0xe8ecf2, 0, 0.005, -0.36));
  bl.add(box(0.014, 0.008, 0.72, 0xffffff, 0, 0.026, -0.36, true));
  const tip = box(0.012, 0.03, 0.06, 0xe8ecf2, 0, 0.012, -0.74); tip.rotation.x = 0.3; bl.add(tip);
  g.add(bl);
  g.userData.katBlade = bl; g.userData.katLen = 0.72;
  g.userData.muzzle = new THREE.Vector3(0, 0.01, -0.82); g.userData.len = 0.95;
}
export const hatAt = null;
