// Default knife: standard combat knife. (kit smoke test, to be rebuilt from references)
import { blade, slab, plate, lathe, pin, curve, THREE } from './kit.js';

export function build(g) {
  // blade: heel at z=-0.03, tip at z=-0.21 (18 cm)
  const spine = curve([[-0.03, 0.012], [-0.12, 0.012], [-0.18, 0.006], [-0.21, -0.002]], 18);
  const edge = curve([[-0.03, -0.014], [-0.14, -0.014], [-0.19, -0.010], [-0.21, -0.002]], 18);
  g.add(blade({ spine, edge, thick: 0.005, grind: 0.45, color: 0xb9c0c9, edgeColor: 0xe6eaef,
    bands: [{ from: 0.55, to: 0.68, color: 0x8d949e, s0: 0.05, s1: 0.6 }] }));
  // guard + handle
  g.add(plate([[-0.012, -0.024], [0.012, -0.024], [0.012, 0.02], [-0.012, 0.02]], 0.008, 0x3a3d42, { z: -0.026 }));
  g.add(lathe([[0, 0.11], [0.012, 0.108], [0.014, 0.08], [0.0125, 0.03], [0.014, -0.022], [0.012, -0.024], [0, -0.024]], 0x2a2c30, { segs: 8, sx: 0.85, sy: 1.15, y: -0.002 }));
  g.add(pin(0.004, 0.026, 0x8a8f99, 0, -0.002, 0.1));
  g.userData.muzzle = new THREE.Vector3(0, -0.002, -0.21);
  g.userData.len = 0.33;
}
export const hatAt = [[0, 0.025, 0.04], 0.05];
