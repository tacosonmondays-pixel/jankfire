// the viewmodel animations, as Luau data (roblox/src/shared/Anims.luau): the draw, getting parried, and
// the katana's swings / draw / parry, copied from public/js/anim.js and public/js/katanavm.js (same keys, same maths
// for the katana's "hilt + blade direction + edge" keys), plus the two reloads, keyed from the timings in
// roblox/docs/WEAPONS.md (reloads.js). metres and radians, camera space; Luau scales metres to studs.
// run: node tools/roblox/anims.mjs
import * as THREE from 'three';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '..');

const K = (t, p = [0, 0, 0], r = [0, 0, 0], e = 'smooth', s = 1) => ({ t, p, r, e, s });
// katanavm.js: keys written as where the hilt is, which way the blade points and which way the edge faces
const PB = [0.1, -0.185, -0.44], RB = [0.85, -0.7, 0.25];
const mB = new THREE.Matrix4(), eB = new THREE.Euler(), bX = new THREE.Vector3(), bY = new THREE.Vector3(), bZ = new THREE.Vector3();
function aim(dir, edge) {
  bZ.set(...dir).normalize().negate();
  bY.set(...edge).normalize().negate(); bY.addScaledVector(bZ, -bY.dot(bZ)).normalize();
  bX.crossVectors(bY, bZ);
  eB.setFromRotationMatrix(mB.makeBasis(bX, bY, bZ), 'XYZ');
  return [eB.x - RB[0], eB.y - RB[1], eB.z - RB[2]];
}
const KK = (t, e = 'smooth') => ({ t, p: [0, 0, 0], r: [0, 0, 0], e, s: 1 });
const KP = (t, p, dir, edge, e = 'smooth') => ({ t, p: [p[0] - PB[0], p[1] - PB[1], p[2] - PB[2]], r: aim(dir, edge), e, s: 1 });

const A = {
  draw_gun: { keys: [K(0, [0.03, -0.26, 0.06], [-0.9, 0.35, 0.45]), K(0.2, [0, 0.012, 0], [0.09, -0.03, -0.06], 'snap'), K(0.34)], events: [[0.19, 'click']] },
  staggered: { keys: [K(0), K(0.07, [0.08, 0.12, 0.14], [0.75, -0.45, 0.65], 'snap'), K(0.32, [0.06, 0.08, 0.1], [0.55, -0.32, 0.45]), K(0.62)] },
  swing_katana: { hit: 0.12, slerp: RB, keys: [
    KK(0),
    KP(0.055, [0.2, -0.08, -0.42], [0.45, 0.82, 0.35], [-0.45, 0.35, -0.82]),
    KP(0.08, [0.21, -0.075, -0.415], [0.42, 0.86, 0.3], [-0.45, 0.35, -0.82], 'linear'),
    KP(0.12, [0.06, -0.15, -0.5], [-0.55, 0.32, -0.77], [-0.5, -0.8, -0.1], 'linear'),
    KP(0.16, [0, -0.2, -0.42], [-0.9, -0.14, -0.41], [-0.3, -0.6, 0.74], 'snap'),
    KP(0.26, [-0.025, -0.22, -0.41], [-0.9, -0.22, -0.38], [-0.32, -0.55, 0.77]),
    KK(0.5, 'back'),
  ], events: [[0.07, 'whoosh']], trail: [0.07, 0.25] },
  swing_katana2: { hit: 0.12, slerp: RB, keys: [
    KK(0),
    KP(0.055, [-0.04, -0.07, -0.42], [-0.5, 0.8, 0.33], [0.5, 0.3, -0.81]),
    KP(0.08, [-0.05, -0.065, -0.415], [-0.47, 0.84, 0.28], [0.5, 0.3, -0.81], 'linear'),
    KP(0.12, [0.08, -0.15, -0.5], [0.55, 0.3, -0.78], [0.5, -0.82, -0.05], 'linear'),
    KP(0.16, [0.2, -0.2, -0.42], [0.9, -0.14, -0.41], [0.3, -0.6, 0.74], 'snap'),
    KP(0.26, [0.225, -0.22, -0.41], [0.9, -0.22, -0.38], [0.32, -0.55, 0.77]),
    KK(0.5, 'back'),
  ], events: [[0.07, 'whoosh']], trail: [0.07, 0.25] },
  draw_katana: { slerp: RB, keys: [
    KP(0, [-0.16, -0.42, -0.22], [-0.25, -0.15, -0.95], [0, 1, 0]),
    KP(0.12, [-0.1, -0.24, -0.38], [-0.7, 0.05, -0.7], [0.3, 0.6, -0.3]),
    KP(0.21, [0.06, -0.16, -0.47], [0.05, 0.08, -1], [1, 0, 0.05], 'linear'),
    KP(0.29, [0.22, -0.17, -0.4], [0.85, 0.05, -0.52], [0.5, 0, 0.86], 'snap'),
    KP(0.4, [0.23, -0.18, -0.39], [0.88, 0.1, -0.45], [0.45, 0, 0.89]),
    KK(0.66), KK(0.72),
  ], events: [[0.02, 'shing'], [0.14, 'whoosh']], trail: [0.11, 0.31] },
  parry_katana: { slerp: RB, keys: [
    KK(0),
    KP(0.05, [0.08, -0.07, -0.4], [-0.78, 0.5, -0.38], [0.05, 0.45, -0.9], 'snap'),
    KP(0.1, [0.08, -0.09, -0.41], [-0.76, 0.48, -0.42], [0.05, 0.42, -0.9]),
    KP(0.34, [0.085, -0.095, -0.41], [-0.74, 0.46, -0.45], [0.05, 0.4, -0.9], 'linear'),
    KK(0.56),
  ], events: [[0.01, 'whoosh']], trail: [0, 0.07] },
  // the classic modes' melee (17 Nov 2026): the knife's slashes and draw from public/js/bladefeel.js (the re-felt versions
  // that replace anim.js's; the toss and finger channels aren't ported: the hand holds it throughout), its heavy stab
  // and the zombie claw's swipes from public/js/anim.js. offsets from the weapon's rest pose (Weapons vm)
  swing_knife: { hit: 0.1, keys: [
    K(0), K(0.05, [0.085, 0.09, 0.05], [0.32, -0.64, -0.64]), K(0.075, [0.095, 0.1, 0.055], [0.37, -0.7, -0.7], 'linear'),
    K(0.12, [-0.15, 0.0, -0.16], [-0.12, 1.0, 0.86], 'snap'), K(0.18, [-0.18, -0.02, -0.14], [-0.18, 1.12, 0.96]),
    K(0.4, [0, 0, 0], [0, 0, 0], 'back'),
  ], events: [[0.07, 'whoosh']], trail: [0.07, 0.24] },
  swing_knife2: { hit: 0.1, keys: [
    K(0), K(0.05, [-0.11, 0.07, 0.04], [0.26, 0.82, 0.66]), K(0.075, [-0.12, 0.08, 0.045], [0.3, 0.88, 0.72], 'linear'),
    K(0.12, [0.09, 0.0, -0.16], [-0.12, -0.84, -0.8], 'snap'), K(0.18, [0.11, -0.02, -0.14], [-0.18, -0.95, -0.88]),
    K(0.4, [0, 0, 0], [0, 0, 0], 'back'),
  ], events: [[0.07, 'whoosh']], trail: [0.07, 0.24] },
  stab_knife: { hit: 0.29, keys: [
    K(0), K(0.22, [0.05, 0.07, 0.16], [0.5, 0.15, 0.15], 'in'),
    K(0.29, [-0.08, 0.02, -0.24], [-0.12, 0.42, 0.12], 'snap'),
    K(0.46, [-0.08, 0.015, -0.23], [-0.14, 0.44, 0.12]),
    K(0.85, [0, 0, 0], [0, 0, 0], 'smooth'),
  ], events: [[0.25, 'whooshBig']], trail: [0.23, 0.34] },
  draw_knife: { keys: [K(0, [0.01, -0.16, 0.02], [-0.5, 0, 0]), K(0.2, [0, 0.02, 0], [0.1, 0, 0], 'snap'), K(0.3, [0, -0.006, 0], [-0.04, 0, 0]), K(0.4)],
    events: [[0.1, 'whoosh'], [0.25, 'shing']] },
  swing_claw: { hit: 0.1, keys: [
    K(0), K(0.07, [0.1, 0.1, 0.06], [0.6, -0.5, -0.5], 'in'),
    K(0.14, [-0.16, -0.08, -0.12], [-0.5, 0.9, 0.7], 'snap'), K(0.24, [-0.18, -0.1, -0.1], [-0.55, 1.0, 0.75]), K(0.42),
  ], events: [[0.08, 'whoosh']], trail: [0.06, 0.22] },
  swing_claw2: { hit: 0.1, keys: [
    K(0), K(0.07, [-0.14, 0.1, 0.05], [0.6, 0.7, 0.6], 'in'),
    K(0.14, [0.1, -0.08, -0.12], [-0.5, -0.7, -0.7], 'snap'), K(0.24, [0.12, -0.1, -0.1], [-0.55, -0.8, -0.75]), K(0.42),
  ], events: [[0.08, 'whoosh']], trail: [0.06, 0.22] },
  // the Redline's 1.8 s pit stop (reloads.js:165-172): tilt, a jerry can tips in three glugs, a wrist-twist rev
  reload_redline: { keys: [
    K(0), K(0.2, [0.02, -0.03, 0.02], [0.22, 0.3, 0.5]), K(1.26, [0.02, -0.035, 0.02], [0.24, 0.3, 0.5]),
    K(1.36, [0.02, -0.02, 0.02], [0.3, 0.32, 0.95], 'snap'), K(1.52, [0.02, -0.03, 0.02], [0.22, 0.3, 0.5]), K(1.8, [0, 0, 0], [0, 0, 0], 'back'),
  ], events: [[0.5, 'glug'], [0.72, 'glug'], [0.94, 'glug'], [1.3, 'revUp'], [1.6, 'click']] },
  // the Marble Shotgun's 1.9 s jar refill (reloads.js:199): lid open, a net bag pours, one bounces out, lid shut, thwack.
  // (17 Nov, the main session: the bag and the hand under it came up through the middle of the screen. the web's timing
  // stays; the gun now rolls well over to the left and drops while it is open, so the jar's mouth faces down-left and
  // the bag pours in from the lower left, the crosshair clear the whole time; it rolls back with the lid's thwack)
  reload_marbles: { keys: [
    K(0), K(0.22, [0, -0.08, 0.03], [0.35, 0.15, 1.0]), K(1.48, [0, -0.085, 0.03], [0.36, 0.15, 1.0]),
    K(1.53, [0, -0.1, 0.03], [0.28, 0.15, 1.05], 'snap'), K(1.9, [0, 0, 0], [0, 0, 0], 'back'),
  ], events: [[0.3, 'click'], [0.66, 'rattle'], [0.78, 'rattle'], [0.9, 'rattle'], [1.02, 'rattle'], [1.12, 'boing'], [1.18, 'rattle'], [1.45, 'click'], [1.5, 'thwack'], [1.53, 'click']] },
  // ---- weapons batch A (18 Nov 2026): the bread, the hand slapper and the heavy draw, copied from public/js/anim.js
  swing_bread: { hit: 0.19, keys: [
    K(0), K(0.13, [0.12, 0.08, 0.1], [0.25, -0.9, -0.3]),
    K(0.24, [-0.38, -0.02, -0.12], [-0.15, 1.9, 0.5], 'snap'),
    K(0.38, [-0.42, -0.06, -0.08], [-0.2, 2.1, 0.6]),
    K(0.62),
  ], events: [[0.15, 'whoosh']], trail: [0.12, 0.34] },
  swing_bread2: { hit: 0.19, keys: [
    K(0), K(0.13, [-0.3, 0.06, 0.05], [0.2, 1.4, 0.4]),
    K(0.24, [0.14, -0.05, -0.12], [-0.1, -0.9, -0.5], 'snap'),
    K(0.38, [0.18, -0.08, -0.08], [-0.15, -1.1, -0.55]),
    K(0.62),
  ], events: [[0.15, 'whoosh']], trail: [0.12, 0.34] },
  swing_slapper: { hit: 0.17, keys: [
    K(0), K(0.1, [0.05, 0.12, 0.15], [0.9, 0, 0.2], 'in'),
    K(0.18, [-0.08, -0.02, -0.21], [-0.62, 0.34, 0.15], 'snap'), K(0.32, [-0.08, -0.04, -0.2], [-0.68, 0.36, 0.15]), K(0.52),
  ], events: [[0.12, 'whoosh']], trail: [0.1, 0.26] },
  draw_heavy: { keys: [K(0, [0.06, -0.36, 0.12], [-0.7, 0.25, 0.65]), K(0.3, [0, 0.02, 0], [0.1, 0, -0.05], 'snap'), K(0.48)], events: [[0.28, 'clunk']] },
  draw_melee: { keys: [
    K(0, [0, -0.26, 0], [-0.5 - Math.PI * 2, 0, 0]), K(0.16, [0, 0.1, 0], [-Math.PI * 2 * 0.45, 0, 0.3], 'snap'),
    K(0.3, [0, -0.02, 0], [-0.1, 0, 0], 'in'), K(0.42),
  ], events: [[0.29, 'thwack']] },
  draw_bread: { keys: [K(0, [0.12, -0.5, 0.12], [-0.9, 0.1, 0.5]), K(0.22, [0, 0.03, 0], [0.12, 0, -0.06], 'snap'), K(0.34, [0, -0.012, 0], [-0.05, 0, 0.02]), K(0.46)], events: [[0.2, 'thwack']] },
  // ---- the Scythe (18 Nov 2026): a slow wide reap both ways, its draw, and the switch to its rifle and back
  // (18 Nov 2026, the owner: "can you find scythe attack animations online") Mixamo mocap swings, made by
  // tools/roblox/mocap_vm.py (Anims.luau has the notes); tp = the third-person R15 Animation of the same window
  swing_scythe: { hit: 0.24, slerp: [0.9981, -0.3736, -0.3745], tp: 93915182836177, tpDur: 0.62, keys: [
    K(0, [0, 0, 0], [0, 0, 0], 'smooth'),
    K(0.07, [0.115, -0.022, 0.12], [-0.452, -3.064, 0.438], 'smooth'),
    K(0.0842, [0.119, -0.004, 0.12], [-0.291, -3.347, 0.041], 'linear'),
    K(0.0983, [0.119, 0.021, 0.12], [-0.074, -3.492, -0.362], 'linear'),
    K(0.1125, [0.112, 0.049, 0.12], [0.112, -3.464, -0.728], 'linear'),
    K(0.1267, [0.107, 0.08, 0.12], [0.142, -3.328, -0.98], 'linear'),
    K(0.1408, [0.108, 0.113, 0.12], [0.041, -3.224, -1.123], 'linear'),
    K(0.155, [0.106, 0.144, 0.097], [-0.168, -3.142, -1.098], 'linear'),
    K(0.1692, [0.09, 0.163, 0.048], [-0.477, -2.917, -0.867], 'linear'),
    K(0.1833, [0.07, 0.158, 0.002], [-0.797, -2.468, -0.689], 'linear'),
    K(0.1975, [0.052, 0.128, -0.025], [-1.349, -1.999, -0.854], 'linear'),
    K(0.2117, [0.038, 0.08, -0.032], [-2.433, -1.921, -1.523], 'linear'),
    K(0.2258, [0.021, 0.032, -0.025], [-3.258, -2.215, -1.833], 'linear'),
    K(0.24, [0, 0, 0], [-3.706, -2.437, -1.809], 'linear'),
    K(0.2762, [-0.01, -0.019, 0.049], [-3.934, -2.633, -1.827], 'linear'),
    K(0.3124, [-0.012, -0.022, 0.098], [-3.981, -2.81, -1.934], 'linear'),
    K(0.3486, [-0.012, -0.019, 0.12], [-3.937, -2.849, -2.027], 'linear'),
    K(0.3848, [-0.015, -0.017, 0.12], [-3.845, -2.733, -2.08], 'linear'),
    K(0.421, [-0.014, -0.019, 0.12], [-3.707, -2.552, -2.122], 'linear'),
    K(0.4571, [-0.01, -0.017, 0.118], [-3.488, -2.361, -2.151], 'linear'),
    K(0.4933, [-0.003, -0.011, 0.095], [-3.175, -2.234, -2.107], 'linear'),
    K(0.5295, [0.006, -0.001, 0.073], [-2.81, -2.211, -1.953], 'linear'),
    K(0.5657, [0.016, 0.014, 0.054], [-2.521, -2.286, -1.767], 'linear'),
    K(0.6019, [0.028, 0.025, 0.044], [-2.381, -2.395, -1.615], 'linear'),
    K(0.62, [0.034, 0.032, 0.036], [-2.359, -2.483, -1.491], 'linear'),
    K(0.78, [0, 0, 0], [0, 0, 0], 'smooth'),
  ], events: [[0.19, 'whoosh']], trail: [0.17, 0.42] },
  swing_scythe2: { hit: 0.24, slerp: [0.9981, -0.3736, -0.3745], tp: 96474909456484, tpDur: 0.62, keys: [
    K(0, [0, 0, 0], [0, 0, 0], 'smooth'),
    K(0.07, [-0.047, 0.071, 0.11], [-0.883, 0.632, -0.461], 'smooth'),
    K(0.0813, [-0.041, 0.078, 0.12], [-0.989, 0.757, -0.476], 'linear'),
    K(0.0927, [-0.033, 0.087, 0.12], [-1.112, 0.908, -0.446], 'linear'),
    K(0.104, [-0.02, 0.098, 0.12], [-1.239, 1.089, -0.392], 'linear'),
    K(0.1153, [-0.003, 0.109, 0.12], [-1.366, 1.296, -0.33], 'linear'),
    K(0.1267, [0.019, 0.122, 0.12], [-1.539, 1.521, -0.219], 'linear'),
    K(0.138, [0.044, 0.135, 0.12], [-2.089, 1.747, 0.275], 'linear'),
    K(0.1493, [0.073, 0.146, 0.12], [-0.667, 2.178, -1.2], 'linear'),
    K(0.1607, [0.101, 0.15, 0.12], [-1.263, 2.502, -0.716], 'linear'),
    K(0.172, [0.127, 0.144, 0.107], [-1.61, 2.889, -0.631], 'linear'),
    K(0.1833, [0.142, 0.124, 0.07], [-1.931, 3.294, -0.769], 'linear'),
    K(0.1947, [0.143, 0.096, 0.035], [-2.26, 3.644, -1.041], 'linear'),
    K(0.206, [0.127, 0.066, 0.006], [-2.62, 3.873, -1.32], 'linear'),
    K(0.2173, [0.095, 0.039, -0.013], [-3.002, 3.947, -1.547], 'linear'),
    K(0.2287, [0.05, 0.016, -0.016], [-3.335, 3.902, -1.735], 'linear'),
    K(0.24, [0, 0, 0], [-3.599, 3.808, -1.921], 'linear'),
    K(0.2653, [-0.047, -0.006, 0.033], [-3.808, 3.68, -2.098], 'linear'),
    K(0.2907, [-0.083, 0.003, 0.075], [-3.942, 3.545, -2.255], 'linear'),
    K(0.316, [-0.101, 0.021, 0.111], [-4.025, 3.495, -2.429], 'linear'),
    K(0.3413, [-0.102, 0.037, 0.12], [-4.147, 3.527, -2.618], 'linear'),
    K(0.3667, [-0.093, 0.046, 0.12], [-4.301, 3.507, -2.768], 'linear'),
    K(0.392, [-0.084, 0.051, 0.12], [-4.386, 3.428, -2.846], 'linear'),
    K(0.4173, [-0.079, 0.056, 0.12], [-4.383, 3.376, -2.884], 'linear'),
    K(0.4427, [-0.079, 0.059, 0.12], [-4.341, 3.383, -2.878], 'linear'),
    K(0.468, [-0.081, 0.059, 0.12], [-4.295, 3.43, -2.827], 'linear'),
    K(0.4933, [-0.083, 0.055, 0.12], [-4.249, 3.505, -2.77], 'linear'),
    K(0.5187, [-0.084, 0.047, 0.12], [-4.208, 3.62, -2.725], 'linear'),
    K(0.544, [-0.083, 0.037, 0.116], [-4.166, 3.788, -2.672], 'linear'),
    K(0.5693, [-0.081, 0.025, 0.095], [-4.098, 4.001, -2.581], 'linear'),
    K(0.5947, [-0.075, 0.014, 0.072], [-3.974, 4.236, -2.432], 'linear'),
    K(0.62, [-0.064, 0.007, 0.049], [-3.741, 4.461, -2.198], 'linear'),
    K(0.78, [0, 0, 0], [0, 0, 0], 'smooth'),
  ], events: [[0.19, 'whoosh']], trail: [0.17, 0.42] },
  // (the chain's third hit and finisher, extras: off with workspace attribute ScytheExtras = false)
  swing_scythe3: { hit: 0.24, slerp: [0.9981, -0.3736, -0.3745], tp: 122538121952075, tpDur: 0.62, r6: 'swing_scythe_hk', keys: [
    K(0, [0, 0, 0], [0, 0, 0], 'smooth'),
    K(0.0751, [0.094, 0.075, 0.12], [-1.184, -0.13, -1.87], 'smooth'),
    K(0.0878, [0.105, 0.107, 0.12], [-1.099, -0.079, -1.303], 'linear'),
    K(0.1004, [0.105, 0.128, 0.12], [-1.105, 0.334, -0.933], 'linear'),
    K(0.1131, [0.098, 0.13, 0.12], [-1.277, 0.803, -0.638], 'linear'),
    K(0.1258, [0.091, 0.122, 0.12], [-1.661, 1.092, -0.119], 'linear'),
    K(0.1385, [0.09, 0.109, 0.12], [-2.128, 1.188, 0.525], 'linear'),
    K(0.1512, [0.101, 0.097, 0.12], [-2.486, 1.169, 1.189], 'linear'),
    K(0.1639, [0.121, 0.086, 0.12], [-2.76, 1.083, 1.823], 'linear'),
    K(0.1766, [0.14, 0.08, 0.12], [-3.127, 0.997, 2.318], 'linear'),
    K(0.1893, [0.144, 0.071, 0.096], [-3.676, 0.494, 2.608], 'linear'),
    K(0.2019, [0.131, 0.06, 0.058], [-4.406, -0.247, 2.322], 'linear'),
    K(0.2146, [0.096, 0.05, 0.024], [-5.462, -0.394, 1.741], 'linear'),
    K(0.2273, [0.047, 0.031, 0.003], [-6.347, -0.258, 1.346], 'linear'),
    K(0.24, [0, 0, 0], [-7.093, 0.052, 1.15], 'linear'),
    K(0.2847, [-0.034, -0.036, 0.024], [-7.368, 0.513, 1.134], 'linear'),
    K(0.3294, [-0.05, -0.062, 0.066], [-7.27, 0.906, 1.091], 'linear'),
    K(0.3741, [-0.054, -0.076, 0.109], [-7.15, 1.098, 1.051], 'linear'),
    K(0.4188, [-0.052, -0.078, 0.12], [-7.193, 1.161, 1.104], 'linear'),
    K(0.4635, [-0.048, -0.074, 0.12], [-7.265, 1.188, 1.133], 'linear'),
    K(0.5082, [-0.041, -0.071, 0.12], [-7.22, 1.236, 1.053], 'linear'),
    K(0.5529, [-0.034, -0.071, 0.12], [-7.053, 1.26, 0.887], 'linear'),
    K(0.5976, [-0.027, -0.073, 0.12], [-6.893, 1.194, 0.763], 'linear'),
    K(0.62, [-0.021, -0.075, 0.12], [-6.829, 1.039, 0.771], 'linear'),
    K(0.78, [0, 0, 0], [0, 0, 0], 'smooth'),
  ], events: [[0.19, 'whoosh']], trail: [0.17, 0.42] },
  swing_scythe4: { hit: 0.24, slerp: [0.9981, -0.3736, -0.3745], tp: 126447507787950, tpDur: 0.62, r6: 'swing_scythe2_hk', keys: [
    K(0, [0, 0, 0], [0, 0, 0], 'smooth'),
    K(0.07, [-0.078, 0.176, 0.022], [-0.51, -2.468, -0.707], 'smooth'),
    K(0.0983, [-0.078, 0.165, 0.009], [-0.685, -2.406, -0.88], 'linear'),
    K(0.1267, [-0.072, 0.144, -0.007], [-1.004, -2.535, -1.114], 'linear'),
    K(0.155, [-0.063, 0.118, -0.023], [-1.316, -2.769, -1.255], 'linear'),
    K(0.1833, [-0.052, 0.086, -0.033], [-1.661, -3.028, -1.263], 'linear'),
    K(0.2117, [-0.028, 0.036, -0.03], [-2.049, -3.196, -1.209], 'linear'),
    K(0.24, [0, 0, 0], [-3.258, -3.051, -0.597], 'linear'),
    K(0.2907, [0.026, -0.007, 0.053], [-4.04, -2.282, -0.263], 'linear'),
    K(0.3413, [0.042, 0.009, 0.114], [-3.763, -1.523, 0.198], 'linear'),
    K(0.392, [0.039, 0.031, 0.12], [-5.081, -0.721, -1.104], 'linear'),
    K(0.4427, [0.01, 0.074, 0.12], [-5.107, -0.309, -1.067], 'linear'),
    K(0.4933, [-0.035, 0.107, 0.12], [-5.304, 0.088, -1.201], 'linear'),
    K(0.544, [-0.076, 0.125, 0.12], [-5.498, 0.524, -1.283], 'linear'),
    K(0.5947, [-0.105, 0.14, 0.12], [-6.09, 1.065, -1.172], 'linear'),
    K(0.62, [-0.121, 0.15, 0.12], [-6.49, 1.214, -0.986], 'linear'),
    K(0.78, [0, 0, 0], [0, 0, 0], 'smooth'),
  ], events: [[0.19, 'whoosh']], trail: [0.17, 0.42] },
  draw_scythe: { keys: [K(0, [0, -0.3, 0], [0, 0, -Math.PI * 2]), K(0.42, [0, 0.02, 0], [0.05, 0, 0], 'snap'), K(0.55)], events: [[0.38, 'shing']] },
  form_scythe: { keys: [K(0), K(0.12, [0.02, -0.12, 0.05], [-0.35, 0.25, 0.9]), K(0.3, [0, -0.04, 0.02], [-0.08, 0.05, 0.2], 'snap'), K(0.45)], events: [[0.1, 'click'], [0.3, 'clunk']] },
  // ---- weapons batch D (18 Nov 2026): the Scales of Justice's swing, both ways
  swing_scales: { hit: 0.22, keys: [
    K(0), K(0.15, [0.14, 0.1, 0.1], [0.3, -1.0, -0.4]),
    K(0.27, [-0.38, -0.03, -0.14], [-0.2, 1.9, 0.6], 'snap'),
    K(0.42, [-0.42, -0.07, -0.1], [-0.25, 2.05, 0.66]),
    K(0.66),
  ], events: [[0.17, 'whoosh']], trail: [0.14, 0.38] },
  swing_scales2: { hit: 0.22, keys: [
    K(0), K(0.15, [-0.3, 0.08, 0.06], [0.25, 1.45, 0.45]),
    K(0.27, [0.14, -0.06, -0.14], [-0.15, -1.0, -0.55], 'snap'),
    K(0.42, [0.18, -0.09, -0.1], [-0.2, -1.15, -0.6]),
    K(0.66),
  ], events: [[0.17, 'whoosh']], trail: [0.14, 0.38] },
};

const n = (x) => +x.toFixed(5);
const v = (a) => `{ ${a.map(n).join(', ')} }`;
let out = `--!strict\n-- GENERATED by tools/roblox/anims.mjs from public/js/anim.js + katanavm.js (+ the reload timings in WEAPONS.md): don't edit by hand.\n`;
out += `-- keys: t (s), p offset (m, camera space), r euler XYZ offset (rad), e ease into the key. slerp = the base euler the\n-- rotations are offsets from, blended as quaternions (the katana). hit = when the swing lands, trail = smear window.\nreturn {\n`;
for (const [name, a] of Object.entries(A)) {
  out += `\t${name} = {\n`;
  if (a.hit) out += `\t\thit = ${a.hit},\n`;
  if (a.slerp) out += `\t\tslerp = ${v(a.slerp)},\n`;
  if (a.trail) out += `\t\ttrail = ${v(a.trail)},\n`;
  out += `\t\tdur = ${a.keys[a.keys.length - 1].t},\n\t\tkeys = {\n`;
  for (const k of a.keys) out += `\t\t\t{ t = ${k.t}, p = ${v(k.p)}, r = ${v(k.r)}, e = "${k.e}" },\n`;
  out += `\t\t},\n\t\tevents = { ${(a.events || []).map(([t, e]) => `{ ${t}, "${e}" }`).join(', ')} },\n\t},\n`;
}
out += `}\n`;
fs.writeFileSync(path.join(ROOT, 'roblox/src/shared/Anims.luau'), out);
fs.mkdirSync(path.join(ROOT, 'roblox/build'), { recursive: true });
fs.writeFileSync(path.join(ROOT, 'roblox/build/anims.json'), JSON.stringify(A)); // (for tools/roblox/pose_sheet.py)
console.log('wrote roblox/src/shared/Anims.luau:', Object.keys(A).length, 'clips');
