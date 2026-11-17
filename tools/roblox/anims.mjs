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
