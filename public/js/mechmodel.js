// MECH DROP, the looks: code stand-ins for the two frames until the Blender hero models land. They use the hero
// models' own skeleton, pivots, marker and clip names (docs/mechs/MECHS.md, pivots from the concept files' `jf` meta),
// so x_mech_<frame>.glb drops in: when it's there it replaces the stand-in (its bones are posed by the same code, or
// its own clips play), when it's missing or broken the stand-in stays. Space: the mech faces -z, right is +x, feet on
// y = 0. PAPER PLANE: a ~4.85 m origami flyer (paper-plane nose chest with the canopy on its keel, V wings, pencil
// missile pods). NIGHT SHIFT: a ~5.7 m security-guard knight (great helm, amber beacon, hi-vis bands, a snap-off blade
// sword, a PLEASE HOLD tower shield). Also: the code poses (with held key poses and overshoot), the clip name for what
// it's doing, the sword's glowing arc, thrust flames, the glowing hatch, and the gib pop when it blows up.
import * as THREE from 'three';
import { G } from './ctx.js';
import { cbox, cyl, cylX, cylZ, rfx, rmesh } from './rigmodel.js';
import { authored, glossyPaint, nodeIn, AUTHORED, whenLate, glbLoader, metaOf } from './glbkit.js';
import { clone as skClone } from 'three/addons/utils/SkeletonUtils.js'; // (a skinned hero model needs its bones cloned with it)
import { MECH } from '/shared/mech.js';

// the hero models' files (public/models, lazy like x_rig): when one is there it replaces the stand-in
export const GLB_ID = { paperplane: 'x_mech_paperplane', nightshift: 'x_mech_nightshift' };
// the skeleton (MECHS.md): name -> [pivot in game coords at rest, parent]. from the concept files' jf meta
const PIV = {
  paperplane: { hips: [[0, 2.62, 0], 'root'], waist: [[0, 2.98, 0.04], 'hips'], chest: [[0, 3.22, 0.04], 'waist'], neck: [[0, 4.06, -0.02], 'chest'], head: [[0, 4.22, -0.03], 'neck'],
    hatch: [[0, 4.02, -0.4], 'chest'], backpack: [[0, 3.62, 0.5], 'chest'], shoulder_R: [[0.56, 3.92, 0.08], 'chest'], pod_R: [[0.99, 4.24, 0.12], 'shoulder_R'], upperarm_R: [[0.98, 3.86, 0.08], 'shoulder_R'],
    forearm_R: [[1.06, 3.04, 0.1], 'upperarm_R'], hand_R: [[1.11, 2.26, 0.05], 'forearm_R'], thigh_R: [[0.4, 2.55, 0], 'hips'], shin_R: [[0.44, 1.52, -0.06], 'thigh_R'], foot_R: [[0.46, 0.5, 0.06], 'shin_R'],
    toe_R: [[0.46, 0.13, -0.4], 'foot_R'], skirt_R: [[0.5, 2.84, 0], 'hips'], wing_R: [[0.3, 4.02, 0.86], 'backpack'] },
  nightshift: { hips: [[0, 2.8, 0], 'root'], waist: [[0, 3.18, 0.04], 'hips'], chest: [[0, 3.42, 0.04], 'waist'], neck: [[0, 4.78, 0.02], 'chest'], head: [[0, 4.9, 0], 'neck'], beacon: [[0, 5.626, 0], 'head'],
    hatch: [[0, 3.64, -0.62], 'chest'], backpack: [[0, 4.1, 0.62], 'chest'], shoulder_R: [[0.8, 4.56, 0.06], 'chest'], upperarm_R: [[1.42, 4.4, 0.06], 'shoulder_R'], forearm_R: [[1.52, 3.4, 0.1], 'upperarm_R'],
    hand_R: [[1.56, 2.44, 0.04], 'forearm_R'], thigh_R: [[0.56, 2.7, 0], 'hips'], shin_R: [[0.62, 1.64, -0.08], 'thigh_R'], foot_R: [[0.64, 0.58, 0.08], 'shin_R'], toe_R: [[0.64, 0.17, -0.52], 'foot_R'],
    skirt_R: [[0.66, 3.02, 0], 'hips'], sword: [[1.58, 2.2, 0], 'hand_R'], shield: [[-1.54, 2.92, 0.07], 'forearm_L'] },
};
for (const P of Object.values(PIV)) for (const [k, [at, par]] of Object.entries({ ...P })) { // mirror the _R side
  if (!k.endsWith('_R')) continue;
  P[k.slice(0, -2) + '_L'] = [[-at[0], at[1], at[2]], par.endsWith('_R') ? par.slice(0, -2) + '_L' : par];
}
// gameplay markers (the names agreed with the art lane; mk_muzzle_* and mk_mark are ours, asked of them): parent joint
// + spot in game coords at rest. a hero model's own empties win; these stand in at the same spots
const MK = {
  paperplane: { mk_seat: ['chest', [0, 3.75, -0.1]], mk_eject: ['chest', [0, 4.3, -0.2]], mk_thrust_back_L: ['backpack', [-0.28, 3.25, 0.82]], mk_thrust_back_R: ['backpack', [0.28, 3.25, 0.82]],
    mk_thrust_heel_L: ['foot_L', [-0.46, 0.25, 0.35]], mk_thrust_heel_R: ['foot_R', [0.46, 0.25, 0.35]],
    mk_muzzle_L: ['forearm_L', [-1.14, 2.4, -0.75]], mk_muzzle_R: ['forearm_R', [1.14, 2.4, -0.75]], mk_drone: ['wing_L', [-0.9, 4.7, 0.95]], mk_mark: ['head', [0, 5.6, 0]] },
  nightshift: { mk_seat: ['chest', [0, 4.0, -0.2]], mk_eject: ['chest', [0, 4.6, -0.4]], mk_thrust_back_L: ['backpack', [-0.45, 3.45, 1.0]], mk_thrust_back_R: ['backpack', [0.45, 3.45, 1.0]],
    mk_thrust_heel_L: ['foot_L', [-0.64, 0.3, 0.45]], mk_thrust_heel_R: ['foot_R', [0.64, 0.3, 0.45]],
    mk_thrust_calf_L0: ['shin_L', [-0.62, 1.2, 0.42]], mk_thrust_calf_L1: ['shin_L', [-0.62, 0.85, 0.42]], mk_thrust_calf_R0: ['shin_R', [0.62, 1.2, 0.42]], mk_thrust_calf_R1: ['shin_R', [0.62, 0.85, 0.42]],
    mk_sword_base: ['sword', [1.58, 2.2, -0.75]], mk_sword_tip: ['sword', [1.58, 2.2, -4.6]], mk_shield_face: ['shield', [-1.54, 2.92, -0.75]], mk_beacon: ['beacon', [0, 5.8, 0]], mk_mark: ['head', [0, 6.4, 0]] },
};
for (const s of ['L', 'R']) for (let i = 0; i < 6; i++) MK.paperplane[`mk_missile_${s}${i}`] = [`pod_${s}`, [(s === 'L' ? -1 : 1) * (0.88 + (i % 3) * 0.11), 4.3 - (i > 2 ? 0.1 : 0), -0.42]]; // 12 for the swarm (6 a pod)
export const JOINTS = [...new Set([...Object.keys(PIV.paperplane), ...Object.keys(PIV.nightshift)])];
export const MARKERS = { paperplane: Object.keys(MK.paperplane), nightshift: Object.keys(MK.nightshift) };
// the clips (MECHS.md): poseMech names the one that fits what the mech is doing (inst.clip); a hero model that has it
// plays it, the stand-in poses it in code
export const CLIPS = { shared: ['idle', 'walk', 'run', 'boost_dash', 'jump', 'land', 'hover', 'hit_react', 'drop_in', 'pilot_in', 'destroy', 'eject'],
  paperplane: ['jet_in', 'jet_fly', 'jet_out', 'missile_salvo', 'lunge', 'drone_launch', 'drone_return', 'drone_flap'], nightshift: ['sword_combo_1', 'sword_combo_2', 'sword_combo_3', 'triple_shift', 'shield_block', 'shield_bash', 'ground_slam'] };

const mats = new Map();
const cached = (k, mk) => mats.get(k) || mats.set(k, mk()).get(k);
const lam = (c, e = 0.1) => cached('l' + c + e, () => new THREE.MeshLambertMaterial({ color: c, flatShading: true, emissive: new THREE.Color(c).multiplyScalar(e) }));
const chrome = (c) => cached('c' + c, () => new THREE.MeshPhongMaterial({ color: c, specular: 0xffffff, shininess: 110, flatShading: true, emissive: new THREE.Color(c).multiplyScalar(0.1) }));
const glow = (c) => cached('g' + c, () => new THREE.MeshBasicMaterial({ color: c }));
const glass = () => cached('glass', () => new THREE.MeshPhongMaterial({ color: 0x8fe8ff, specular: 0xffffff, shininess: 150, transparent: true, opacity: 0.8, emissive: 0x0c3a4a }));

function add(parent, geo, mat, p = [0, 0, 0], r = null) {
  const m = new THREE.Mesh(geo, mat);
  m.position.fromArray(p);
  if (r) m.rotation.set(r[0], r[1], r[2]);
  parent.add(m);
  return m;
}
// a part placed in game coords (rest pose) under joint j (pivot `at`)
function part2(j, pa, world, geo, mat) { return add(j, geo, mat, [world[0] - pa[0], world[1] - pa[1], world[2] - pa[2]]); } // (under a model's own joint: its pivot is pa)
function part(j, geo, mat, world, r = null) { return add(j, geo, mat, [world[0] - j.userData.at[0], world[1] - j.userData.at[1], world[2] - j.userData.at[2]], r); }
// a limb box from this joint's pivot toward a point (game coords), w x d thick
function limb(j, to, w, d, mat, k = 1, c = 0.05) {
  const a = j.userData.at, v = new THREE.Vector3(to[0] - a[0], to[1] - a[1], to[2] - a[2]), l = v.length() * k;
  const m = add(j, cbox(w, l, d, c), mat);
  m.position.copy(v.clone().normalize().multiplyScalar(l / 2));
  m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), v.normalize());
  return m;
}
function fold(a, b, c, t = 0.05) { // a flat triangle (a paper fold) with some thickness, in its own xy plane
  const s = new THREE.Shape([new THREE.Vector2(a[0], a[1]), new THREE.Vector2(b[0], b[1]), new THREE.Vector2(c[0], c[1])]);
  return new THREE.ExtrudeGeometry(s, { depth: t, bevelEnabled: false }).translate(0, 0, -t / 2);
}
const wedge = (w, h, d) => { const g = new THREE.CylinderGeometry(0, w, d, 4, 1).rotateX(-Math.PI / 2).rotateZ(Math.PI / 4); g.scale(1, h / w, 1); return g; };
const at = (P, k) => P[k][0];

// ------------------------------------------------------------ PAPER PLANE (colours: SKY MAIL, the paint is yours)
function buildPaper(j, own) {
  const P = PIV.paperplane, white = lam(0xf3f0e6, 0.2), navy = lam(0x1d2747, 0.08), yellow = lam(0xffd23a, 0.25), acc = own.accent, ink = lam(0x2a2a40, 0.05);
  for (const s of ['L', 'R']) {
    const sg = s === 'L' ? -1 : 1;
    limb(j['thigh_' + s], at(P, 'shin_' + s), 0.42, 0.46, white);
    part(j['thigh_' + s], cbox(0.46, 0.22, 0.5, 0.04), acc, [0.42 * sg, 2.25, -0.02]);
    limb(j['shin_' + s], at(P, 'foot_' + s), 0.36, 0.42, white);
    part(j['shin_' + s], wedge(0.5, 0.42, 0.5), acc, [0.44 * sg, 1.5, -0.3]); // a folded knee
    part(j['shin_' + s], cbox(0.3, 0.6, 0.06, 0.02), ink, [0.45 * sg, 1.0, -0.26]); // the crease down the shin
    part(j['foot_' + s], cbox(0.42, 0.3, 0.55, 0.05), navy, [0.46 * sg, 0.3, 0.12]);
    part(j['toe_' + s], wedge(0.44, 0.24, 0.6), white, [0.46 * sg, 0.12, -0.45]);
    part(j['skirt_' + s], fold([0, 0], [0.32 * sg, 0], [0.12 * sg, -0.5], 0.06), acc, [0.42 * sg, 2.9, -0.1], [0, 0, 0]);
  }
  part(j.hips, cbox(0.85, 0.4, 0.55, 0.06), navy, [0, 2.62, 0]);
  part(j.waist, cbox(0.55, 0.38, 0.45, 0.05), navy, [0, 3.04, 0.02]);
  // the chest: a paper plane's nose, white with your colour, the canopy on its keel (the hatch)
  part(j.chest, cbox(1.15, 0.8, 0.85, 0.1), white, [0, 3.65, 0.08]);
  part(j.chest, wedge(1.15, 0.7, 0.9), acc, [0, 3.62, -0.55]);
  part(j.chest, fold([-0.5, 0.3], [0.5, 0.3], [0, -0.4], 0.04), yellow, [0, 3.62, -0.62], [0.35, 0, 0]); // the V chevron
  part(j.chest, cbox(0.04, 0.8, 0.9, 0.01), ink, [0, 3.65, 0.08]); // the centre fold
  part(j.hatch, wedge(0.5, 0.32, 0.65), glass(), [0, 3.9, -0.62]);
  part(j.hatch, cbox(0.52, 0.06, 0.6, 0.02), own.hatch, [0, 4.07, -0.5]);
  // head: small, folded crest, yellow eyes, ear flaps (and a paperclip antenna)
  part(j.head, cbox(0.48, 0.4, 0.5, 0.06), white, [0, 4.42, -0.02]);
  part(j.head, cbox(0.36, 0.08, 0.06, 0.02), own.visor, [0, 4.44, -0.28]);
  part(j.head, fold([0, 0], [0, 0.32], [0.5, 0.05], 0.05), acc, [0, 4.6, 0.1], [0, Math.PI / 2, 0]);
  for (const sg of [-1, 1]) part(j.head, fold([0, 0], [0.22 * sg, 0.34], [0.18 * sg, 0], 0.04), white, [0.24 * sg, 4.45, 0]);
  part(j.head, cbox(0.03, 0.35, 0.03, 0.01), chrome(0xd0d8e2), [-0.3, 4.75, 0.05]);
  // backpack + its jets, and the wings: two folded halves stowed up and out like a V
  part(j.backpack, cbox(0.8, 0.8, 0.45, 0.06), navy, [0, 3.62, 0.62]);
  for (const sg of [-1, 1]) part(j.backpack, cyl(0.16, 0.22, 0.4, 10), navy, [0.28 * sg, 3.3, 0.8]);
  for (const s of ['L', 'R']) {
    const sg = s === 'L' ? -1 : 1, w = j['wing_' + s];
    part(w, fold([0, 0], [1.1 * sg, 1.9], [0.35 * sg, -0.9], 0.05), white, [0.3 * sg, 4.02, 0.9]);
    part(w, fold([0.12 * sg, 0.3], [1.05 * sg, 1.85], [0.95 * sg, 1.55], 0.06), acc, [0.3 * sg, 4.02, 0.88]); // the leading edge
    part(w, cbox(0.06, 1.6, 0.07, 0.01), ink, [0.75 * sg, 4.5, 0.93], [0, 0, -0.45 * sg]); // FOLD HERE
  }
  // shoulders, the pencil missile pods, arms with a twin cannon under each forearm
  for (const s of ['L', 'R']) {
    const sg = s === 'L' ? -1 : 1;
    part(j['shoulder_' + s], cbox(0.6, 0.45, 0.6, 0.07), white, [0.85 * sg, 3.95, 0.08]);
    part(j['shoulder_' + s], cbox(0.62, 0.1, 0.62, 0.02), acc, [0.85 * sg, 4.15, 0.08]);
    part(j['pod_' + s], cbox(0.44, 0.26, 0.5, 0.04), navy, [0.99 * sg, 4.3, 0.1]);
    for (let i = 0; i < 3; i++) { // pencils: yellow hex bodies, pink erasers out the back, sharpened tips forward
      const x = (0.88 + i * 0.11) * sg;
      part(j['pod_' + s], new THREE.CylinderGeometry(0.045, 0.045, 0.55, 6).rotateX(Math.PI / 2), yellow, [x, 4.3, -0.05]);
      part(j['pod_' + s], new THREE.ConeGeometry(0.045, 0.13, 6).rotateX(-Math.PI / 2), lam(0xe8c9a0), [x, 4.3, -0.38]);
      part(j['pod_' + s], cylZ(0.046, 0.08, 6), lam(0xff7ab8, 0.2), [x, 4.3, 0.26]);
    }
    limb(j['upperarm_' + s], at(P, 'forearm_' + s), 0.3, 0.34, white);
    limb(j['forearm_' + s], at(P, 'hand_' + s), 0.34, 0.38, navy);
    part(j['forearm_' + s], cbox(0.38, 0.22, 0.42, 0.04), acc, [1.08 * sg, 2.9, 0.1]);
    part(j['forearm_' + s], cbox(0.24, 0.24, 0.5, 0.04), navy, [1.12 * sg, 2.45, -0.35]); // the cannon housing
    for (const b of [-0.06, 0.06]) part(j['forearm_' + s], cylZ(0.05, 0.5, 8), chrome(0xd0d8e2), [1.14 * sg + b, 2.4, -0.55]);
    part(j['hand_' + s], cbox(0.26, 0.3, 0.3, 0.05), ink, [1.11 * sg, 2.1, 0.05]);
  }
}
// the origami crane drone (also flown by mech.js)
export function buildCrane(color) {
  const g = new THREE.Group(), m = lam(new THREE.Color(color || '#ff4fd8').getHex(), 0.3), w = lam(0xf6f2e6, 0.25);
  add(g, wedge(0.22, 0.2, 0.55), w);
  add(g, cbox(0.05, 0.32, 0.05, 0.01), w, [0, 0.12, -0.3], [0.6, 0, 0]);
  add(g, wedge(0.07, 0.07, 0.2), m, [0, 0.27, -0.42]);
  const wl = add(g, fold([0, 0], [-0.55, 0.15], [-0.1, -0.25], 0.02), w, [-0.05, 0.05, 0], [Math.PI / 2, 0, 0]);
  const wr = add(g, fold([0, 0], [0.55, 0.15], [0.1, -0.25], 0.02), w, [0.05, 0.05, 0], [Math.PI / 2, 0, 0]);
  add(g, wedge(0.12, 0.08, 0.3), m, [0, 0.05, 0.3], [0.4, Math.PI, 0]);
  g.userData.wings = [wl, wr];
  return g;
}

// ------------------------------------------------------------ NIGHT SHIFT (colours: GRAVEYARD SHIFT, the paint is yours)
function buildKnight(j, own) {
  const P = PIV.nightshift, white = lam(0xf0ede4, 0.18), navy = lam(0x161c38, 0.08), hivis = lam(0xffd23a, 0.3), acc = own.accent, steel = chrome(0x9aa6b6), black = lam(0x121218, 0.04);
  for (const s of ['L', 'R']) {
    const sg = s === 'L' ? -1 : 1;
    limb(j['thigh_' + s], at(P, 'shin_' + s), 0.62, 0.68, acc);
    part(j['thigh_' + s], cbox(0.66, 0.12, 0.72, 0.03), hivis, [0.6 * sg, 2.25, 0]);
    limb(j['shin_' + s], at(P, 'foot_' + s), 0.66, 0.72, white);
    part(j['shin_' + s], cbox(0.5, 0.7, 0.14, 0.04), acc, [0.63 * sg, 1.15, -0.42]); // greave
    part(j['shin_' + s], cylX(0.26, 0.7, 10), navy, [0.62 * sg, 1.64, -0.08]); // knee
    part(j['foot_' + s], cbox(0.78, 0.42, 0.85, 0.08), acc, [0.64 * sg, 0.3, 0.05]);
    part(j['toe_' + s], cbox(0.76, 0.3, 0.55, 0.08), white, [0.64 * sg, 0.15, -0.6]);
    part(j['skirt_' + s], cbox(0.5, 0.7, 0.7, 0.06), navy, [0.72 * sg, 2.75, 0]);
  }
  part(j.hips, cbox(1.3, 0.5, 0.8, 0.08), navy, [0, 2.8, 0]);
  part(j.hips, cbox(0.5, 0.25, 0.1, 0.03), hivis, [0, 2.85, -0.42]); // the belt buckle
  part(j.hips, cylX(0.12, 0.3, 8), steel, [0.45, 2.6, -0.45]); // the keyring (jank: it's huge)
  part(j.waist, cbox(1.0, 0.4, 0.75, 0.06), white, [0, 3.25, 0.04]);
  // the barrel breastplate: your colour, hi-vis bands, a brass badge. the breastplate is the cockpit hatch
  part(j.chest, new THREE.CylinderGeometry(0.95, 0.85, 1.25, 12), acc, [0, 4.05, 0.04]);
  for (const y of [3.75, 3.95]) part(j.chest, new THREE.CylinderGeometry(0.965, 0.95, 0.07, 12), hivis, [0, y, 0.04]);
  part(j.hatch, cbox(1.0, 0.85, 0.12, 0.05), acc, [0, 4.05, -0.88]);
  part(j.hatch, cbox(1.02, 0.07, 0.14, 0.02), hivis, [0, 3.85, -0.9]);
  part(j.hatch, cbox(0.2, 0.2, 0.05, 0.02), chrome(0xd9a63a), [-0.3, 4.25, -0.95]); // NIGHT SHIFT badge
  part(j.hatch, cbox(0.6, 0.06, 0.16, 0.02), own.hatch, [0, 4.45, -0.88]);
  // the great helm: one glowing visor slit, the amber beacon on top, a walkie-talkie antenna
  part(j.head, cbox(0.8, 0.8, 0.8, 0.12), white, [0, 5.25, 0]);
  part(j.head, cbox(0.82, 0.12, 0.82, 0.02), acc, [0, 5.0, 0]);
  part(j.head, cbox(0.6, 0.07, 0.06, 0.01), own.visor, [0, 5.3, -0.42]);
  part(j.head, cbox(0.03, 0.5, 0.03, 0.01), black, [0.32, 5.8, 0.2]);
  part(j.beacon, cyl(0.16, 0.18, 0.12, 10), steel, [0, 5.68, 0]);
  part(j.beacon, new THREE.SphereGeometry(0.16, 10, 6, 0, Math.PI * 2, 0, Math.PI / 2), own.beacon, [0, 5.74, 0]);
  part(j.beacon, cbox(0.3, 0.12, 0.04, 0.01), glow(0xffffff), [0, 5.8, -0.1]); // the rotating reflector
  // backpack + boosters
  part(j.backpack, cbox(1.2, 1.0, 0.55, 0.08), navy, [0, 4.15, 0.8]);
  for (const sg of [-1, 1]) part(j.backpack, cyl(0.24, 0.3, 0.8, 10), black, [0.45 * sg, 3.8, 1.0]);
  part(j.backpack, cbox(0.5, 0.25, 0.02, 0.01), hivis, [0, 4.4, 1.08]); // HOW'S MY PILOTING?
  // pauldrons, arms, the torch on the right pauldron
  for (const s of ['L', 'R']) {
    const sg = s === 'L' ? -1 : 1;
    part(j['shoulder_' + s], new THREE.SphereGeometry(0.62, 10, 6, 0, Math.PI * 2, 0, Math.PI / 2), acc, [1.25 * sg, 4.45, 0.06]);
    part(j['shoulder_' + s], cbox(1.0, 0.14, 0.9, 0.04), white, [1.25 * sg, 4.42, 0.06]);
    limb(j['upperarm_' + s], at(P, 'forearm_' + s), 0.5, 0.54, white);
    limb(j['forearm_' + s], at(P, 'hand_' + s), 0.58, 0.62, navy);
    part(j['forearm_' + s], cbox(0.64, 0.16, 0.68, 0.04), hivis, [1.52 * sg, 3.3, 0.1]);
    part(j['hand_' + s], cbox(0.42, 0.42, 0.46, 0.08), black, [1.56 * sg, 2.25, 0.04]);
  }
  part(j.shoulder_R, cyl(0.1, 0.12, 0.3, 8).rotateX(Math.PI / 2), glow(0xfff2b0), [1.55, 4.75, -0.2]);
  // the snap-off blade sword in the right hand: rubber grip, chunky guard, a long dark blade with glowing edges
  part(j.sword, cylZ(0.11, 0.8, 8), black, [1.58, 2.2, 0.05]);
  part(j.sword, cbox(0.9, 0.22, 0.24, 0.05), hivis, [1.58, 2.2, -0.42]);
  part(j.sword, cbox(0.1, 0.42, 3.7, 0.03), lam(0x2a2e3a, 0.1), [1.58, 2.2, -2.4]);
  for (const y of [-0.22, 0.22]) part(j.sword, cbox(0.12, 0.05, 3.7, 0.01), own.edge, [1.58, 2.2 + y, -2.4]);
  for (let i = 0; i < 6; i++) part(j.sword, cbox(0.12, 0.42, 0.02, 0.005), black, [1.58, 2.2, -0.9 - i * 0.55], [0.5, 0, 0]); // the snap lines
  part(j.sword, wedge(0.12, 0.42, 0.55), lam(0x2a2e3a, 0.1), [1.58, 2.2, -4.45]);
  // the PLEASE HOLD tower shield on the left forearm
  part(j.shield, cbox(1.5, 2.7, 0.2, 0.08), acc, [-1.6, 2.95, -0.62]);
  part(j.shield, cbox(1.56, 0.2, 0.24, 0.03), hivis, [-1.6, 4.25, -0.62]);
  part(j.shield, cbox(1.56, 0.2, 0.24, 0.03), hivis, [-1.6, 1.65, -0.62]);
  part(j.shield, cbox(1.0, 0.45, 0.06, 0.02), black, [-1.6, 3.2, -0.74]);
  part(j.shield, cbox(0.9, 0.12, 0.02, 0.01), own.led, [-1.6, 3.28, -0.78]); // PLEASE HOLD
  part(j.shield, cbox(0.22, 0.08, 0.02, 0.01), own.led, [-1.94, 3.1, -0.78]); // stuck at 25%
}

// ------------------------------------------------------------ which model: the hero file, the concept, the code
// 1. public/models/x_mech_<frame>.glb (lazy, glbkit: once listed it loads the first time a mech shows up)
// 2. the concept glb (docs/mechs/concept, the owner's OK'd placeholder; the server hands it out at /mechs/concept/)
// 3. the code stand-in below. modelVer goes up whenever a better one lands: mech.js rebuilds what it shows
const CONCEPT = {}, conceptT = {};
export let modelVer = 0;
const bump = () => { modelVer++; };
for (const f of ['paperplane', 'nightshift']) whenLate(GLB_ID[f], bump);
function sourceOf(frame) {
  const a = authored(GLB_ID[frame]); // (asks for the hero file if the server lists it)
  if (a) return { obj: a.obj, scene: AUTHORED[GLB_ID[frame]].scene };
  if (CONCEPT[frame]) return { obj: CONCEPT[frame].clone(true), scene: CONCEPT[frame] };
  if (!conceptT[frame]) {
    conceptT[frame] = 1;
    glbLoader().load(`/mechs/concept/mech_${frame}_concept.glb`, (g) => { g.scene.animations = g.animations || []; g.scene.traverse((o) => { if (o.isMesh) o.geometry.userData.shared = true; }); CONCEPT[frame] = g.scene; bump(); }, undefined, () => {}); // (missing: the code stand-in stays)
  }
  return null;
}

// ------------------------------------------------------------ build / free
export function buildMech(frame, color, opts = {}) {
  frame = frame === 'nightshift' ? 'nightshift' : 'paperplane';
  const col = new THREE.Color(color || '#ff4fd8');
  const own = { // per-mech materials: <p>_paint (your colour), the glows
    accent: glossyPaint(col, 0.25),
    hatch: new THREE.MeshBasicMaterial({ color: 0xffe14d }),
    visor: new THREE.MeshBasicMaterial({ color: frame === 'nightshift' ? 0xffb43a : 0xffe14d }),
    edge: new THREE.MeshBasicMaterial({ color: 0xffd23a }),
    beacon: new THREE.MeshBasicMaterial({ color: 0xffa020, transparent: true, opacity: 0.95 }),
    led: new THREE.MeshBasicMaterial({ color: 0xff8a2a }),
  };
  const root = new THREE.Group(), j = { root };
  root.name = 'root'; root.userData.at = [0, 0, 0];
  const P = PIV[frame];
  const make = (k) => { // joints in parent order, local offsets from the rest pivots
    if (j[k]) return j[k];
    const [w, par] = P[k], pj = make(par === 'root' ? 'root' : par) || root;
    const n = new THREE.Group(); n.name = k; n.userData.at = w; n.userData.rest = [w[0] - pj.userData.at[0], w[1] - pj.userData.at[1], w[2] - pj.userData.at[2]];
    n.position.fromArray(n.userData.rest); pj.add(n); j[k] = n;
    return n;
  };
  for (const k of Object.keys(P)) make(k);
  let glb = null;
  const a = opts.noGlb ? null : sourceOf(frame);
  if (a) { // a real model: its nodes are the joints (same names, same pivots); the stand-in skeleton is dropped
    glb = a.obj;
    let skinned = false; glb.traverse((o) => { if (o.isSkinnedMesh) skinned = true; });
    if (skinned) { glb = skClone(a.scene); glb.animations = a.scene.animations || []; }
    root.add(glb);
    const pre = frame === 'paperplane' ? 'pp_' : 'ns_'; // MECHS.md material roles: <p>_paint takes your colour, the glows stay lit
    glb.traverse((o) => { if (o.isMesh && !Array.isArray(o.material) && o.material.name && o.material.name.startsWith(pre + 'paint')) o.material = own.accent; });
    for (const k of Object.keys(P)) { const n = nodeIn(glb, k); if (n) { j[k].visible = false; j[k] = n; n.userData.rest = n.position.toArray(); } }
    for (const n of root.children) if (n !== glb) n.visible = false;
    if (frame === 'paperplane') for (const s of ['L', 'R']) { const sg = s === 'L' ? -1 : 1, fa = j['forearm_' + s]; part2(fa, PIV.paperplane['forearm_' + s][0], [1.12 * sg, 2.45, -0.35], cbox(0.24, 0.24, 0.5, 0.04), lam(0x1d2747, 0.08)); for (const b of [-0.06, 0.06]) part2(fa, PIV.paperplane['forearm_' + s][0], [1.14 * sg + b, 2.4, -0.55], cylZ(0.05, 0.5, 8), chrome(0xd0d8e2)); } // (the twin cannons: ours, the model has none yet)
  } else if (frame === 'paperplane') buildPaper(j, own);
  else buildKnight(j, own);
  // markers: the hero model's empties, else ours at the same spots
  const att = {};
  for (const [k, [jn, w]] of Object.entries(MK[frame])) {
    let n = glb && nodeIn(glb, k);
    if (!n) { const pj = j[jn]; n = new THREE.Object3D(); n.name = k; const pa = PIV[frame][jn][0]; n.position.set(w[0] - pa[0], w[1] - pa[1], w[2] - pa[2]); pj.add(n); }
    att[k] = n;
  }
  for (const k of ['hatch', 'chest', 'head', 'backpack', 'sword', 'shield', 'beacon', 'wing_L', 'wing_R', 'pod_L', 'pod_R']) if (j[k]) att[k] = j[k];
  att.drone = (glb && nodeIn(glb, 'drone')) || null; // the crane drone: a joint under wing_L (ours stands in at mk_drone)
  if (!att.drone && att.mk_drone) { const c = buildCrane(own.accent.color); c.rotation.y = Math.PI; c.name = 'drone'; att.mk_drone.add(c); att.drone = c; }
  // thrust flames on every mk_thrust_* (additive cones, out the back / down)
  const flameMat = new THREE.MeshBasicMaterial({ color: frame === 'nightshift' ? 0xffb43a : 0x5ff0ff, transparent: true, opacity: 0.8, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
  const coreMat = new THREE.MeshBasicMaterial({ color: 0xfff4c0, transparent: true, opacity: 0.95, blending: THREE.AdditiveBlending, depthWrite: false });
  const flames = [];
  for (const [k, n] of Object.entries(att)) {
    if (!k.startsWith('mk_thrust')) continue;
    const f = new THREE.Group(), leg = !k.includes('back'), big = leg ? 0.6 : 1;
    f.rotation.set(leg ? Math.PI : Math.PI * 0.75, 0, 0);
    add(f, new THREE.ConeGeometry(0.22 * big, 1.4 * big, 10, 1, true).translate(0, 0.7 * big, 0), flameMat);
    add(f, new THREE.ConeGeometry(0.1 * big, 0.8 * big, 8).translate(0, 0.4 * big, 0), coreMat);
    for (const c of f.children) c.renderOrder = 7;
    f.visible = false; n.add(f); flames.push(f);
  }
  for (const s of ['L', 'R']) { const mz = att['mk_muzzle_' + s]; if (!mz) continue; const fl = add(mz, new THREE.SphereGeometry(0.22, 8, 6), new THREE.MeshBasicMaterial({ color: 0xfff2a0, transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending, depthWrite: false })); fl.visible = false; mz.userData.flash = fl; }
  // the glowing sword arc (a ribbon behind the blade while it swings)
  let trail = null;
  if (att.mk_sword_tip) {
    const N = 14, geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(N * 2 * 3), 3).setUsage(THREE.DynamicDrawUsage));
    geo.setAttribute('a', new THREE.BufferAttribute(new Float32Array(N * 2), 1).setUsage(THREE.DynamicDrawUsage));
    const idx = []; for (let i = 0; i < N - 1; i++) { const a2 = i * 2; idx.push(a2, a2 + 1, a2 + 2, a2 + 1, a2 + 3, a2 + 2); }
    geo.setIndex(idx);
    const mat = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending,
      uniforms: { uC: { value: new THREE.Color(0xffc23a) } },
      vertexShader: 'attribute float a; varying float vA; void main(){ vA = a; gl_Position = projectionMatrix * viewMatrix * vec4(position, 1.0); }',
      fragmentShader: 'uniform vec3 uC; varying float vA; void main(){ gl_FragColor = vec4(mix(uC, vec3(1.0), vA * vA), vA * 0.85); }' });
    trail = new THREE.Mesh(geo, mat); trail.frustumCulled = false; trail.renderOrder = 8;
    trail.userData = { N, pts: [] };
  }
  const inst = { v: modelVer, frame, root, j, att, own, flames, flameMat, coreMat, trail, glb: !!glb, mixer: null, clip: 'idle', sp: {}, phase: 0, t: Math.random() * 10,
    jank: { tilt: (Math.random() - 0.5) * 0.1, knee: Math.random() < 0.5 ? 'L' : 'R' }, hatchOpen: 0 };
  if (glb && glb.animations && glb.animations.length) { // the rig's clips (MECHS.md), their play rules from its jf meta
    inst.mixer = new THREE.AnimationMixer(glb);
    inst.clips = Object.fromEntries(glb.animations.map((c) => [c.name, c]));
    const meta = metaOf(glb) || {}, list = Array.isArray(meta.clips) ? meta.clips : Object.entries(meta.clips || {}).map(([name, v]) => ({ name, ...v }));
    inst.clipMeta = Object.fromEntries(list.filter((c) => c && typeof c.name === 'string').map((c) => [c.name, { hold: /hold/.test(String(c.hold ?? c.play ?? '')) || c.hold === true, loop: c.loop }]));
  }
  root.userData.mech = inst;
  return inst;
}
export function freeMech(inst) {
  if (!inst) return;
  inst.root.removeFromParent();
  if (inst.trail) { inst.trail.removeFromParent(); inst.trail.geometry.dispose(); inst.trail.material.dispose(); }
  for (const m of Object.values(inst.own)) m.dispose();
  inst.flameMat.dispose(); inst.coreMat.dispose();
  inst.root.traverse((o) => { if (o.isMesh && !o.geometry.userData.shared) o.geometry.dispose(); });
}
export function setMechColor(inst, color) { const c = new THREE.Color(color); inst.own.accent.color.copy(c); inst.own.accent.emissive.copy(c).multiplyScalar(0.25); }

// ------------------------------------------------------------ pose
// s: { spd, fwd, side (local m/s), air, vy, hover, jet (0..1), dash, shield, swingT, swingI, slam (1 up / 2 down), gunT,
//      gunSide, swarmT, craneOut, landT, landK, pitch, empty (nobody in it: hatch open + glowing), boost, slashing }
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const back = (u) => { const c = 1.9; return 1 + (c + 1) * Math.pow(u - 1, 3) + c * Math.pow(u - 1, 2); }; // overshoot
const ease = (u) => u * u * (3 - 2 * u);
function spr(inst, k, target, stiff, dt) { // a damped spring per channel: the settle (and overshoot) after a key pose
  const s = inst.sp[k] || (inst.sp[k] = { x: target, v: 0 });
  const d = 2 * Math.sqrt(stiff) * 0.6, n = Math.max(1, Math.ceil(dt * 120)), h = dt / n;
  for (let i = 0; i < n; i++) { s.v += (stiff * (target - s.x) - d * s.v) * h; s.x += s.v * h; }
  return s.x;
}
// the knight's swings: [upperarm x (raise), upperarm z (out), upperarm y (twist), chest twist] at the wind-up and the end
const SWING = [
  { up: [-2.3, 0.5, 0.6, 0.55], end: [-0.5, -0.3, -0.9, -0.7] }, // right to left, high
  { up: [-1.2, -0.9, -0.8, -0.6], end: [-0.9, 0.3, 0.9, 0.6] }, // back the other way
  { up: [-3.0, -0.1, 0.1, 0.2], end: [-0.2, 0.0, 0.0, -0.1] }, // the big overhead
];
// which clip this moment is (MECHS.md names): a hero model with clips plays it, the stand-in poses it below
function clipOf(inst, s) {
  if (s.empty) return 'drop_in'; // (it ends in a held low hero pose: an empty mech waits like that)
  if (inst.frame === 'paperplane') {
    if (s.jet) return 'jet_fly';
    if (s.dash) return 'lunge';
    if (s.swarmT < 0.6) return 'missile_salvo';
    if (s.hover) return 'hover';
  } else {
    if (s.slam) return 'ground_slam';
    if (s.dash) return 'triple_shift';
    if (s.swingT < 0.75) return 'sword_combo_' + ((s.swingI | 0) + 1);
    if (s.shield) return 'shield_block';
  }
  if (s.landT < 0.4) return 'land';
  if (s.air) return 'jump';
  return s.spd > MECH[inst.frame].speed * 0.7 ? 'run' : s.spd > 0.6 ? 'walk' : 'idle';
}
export function poseMech(inst, s, dt) {
  const j = inst.j, pp = inst.frame === 'paperplane', T = inst.t += dt, F = MECH[inst.frame];
  const clip = clipOf(inst, s);
  if (inst.mixer) { // a hero model with its own clips: play the one that fits (crossfade), skip the code pose
    const again = clip === inst.clip && clip.startsWith('sword_combo') && s.swingT < (inst.lastSwing ?? 9); // (the same swing again: from the top)
    inst.lastSwing = s.swingT;
    if (clip !== inst.clip || again) {
      const c = inst.clips[clip];
      if (c) {
        const act = inst.mixer.clipAction(c), m = inst.clipMeta[clip] || {};
        act.reset();
        if (m.hold || m.loop === false) { act.setLoop(THREE.LoopOnce, 1); act.clampWhenFinished = true; } // "hold last frame" / "once"
        act.fadeIn(0.12).play();
        if (inst.act && inst.act !== act) inst.act.fadeOut(0.12);
        inst.act = act;
      }
    }
    inst.clip = clip; inst.mixer.update(dt);
    effects(inst, s, T);
    return;
  }
  inst.clip = clip;
  // ---- legs: a stomping walk, knees bend on landings and in the shield crouch
  const run = clamp(s.spd / F.speed, 0, 1.4);
  if (!s.air && s.spd > 0.6) inst.phase += dt * (1.4 + s.spd * (pp ? 0.32 : 0.26));
  const ph = inst.phase * Math.PI, sw = Math.sin(ph) * 0.55 * run;
  const land = s.landT < 0.5 ? Math.sin(clamp(s.landT / 0.5, 0, 1) * Math.PI) * (0.4 + s.landK * 0.6) : 0;
  const crouch = (s.shield ? 0.25 : 0) + land + (s.slam === 1 ? 0.3 : 0);
  const air = s.air ? 1 : 0, jet = s.jet || 0, hov = s.hover ? 1 : 0;
  for (const [L, sg] of [['L', 1], ['R', -1]]) {
    const leg = sw * sg, k = Math.max(0, -Math.sin(ph) * sg) * run;
    const th = -leg - crouch * 0.9 - air * (0.35 + hov * 0.4) * (1 - jet), sn = crouch * 1.7 + k * 0.9 + air * (0.7 + hov * 0.5) * (1 - jet) + (inst.jank.knee === L ? 0.08 : 0); // (a knee that bends just a bit wrong)
    j['thigh_' + L].rotation.x = spr(inst, 'th' + L, th + jet * 0.15, 140, dt);
    j['shin_' + L].rotation.x = spr(inst, 'sn' + L, sn, 140, dt);
    j['foot_' + L].rotation.x = spr(inst, 'ft' + L, -th - sn + (s.air ? 0.4 : 0) + jet * 0.9, 160, dt); // jet: feet pointed
    j['thigh_' + L].rotation.z = spr(inst, 'tz' + L, jet * 0.06 * sg, 100, dt); // jet: legs together
  }
  const bob = !s.air ? -Math.abs(Math.sin(ph)) * 0.12 * run - crouch * 0.45 : 0;
  j.hips.position.y = spr(inst, 'hy', j.hips.userData.rest[1] + bob + (s.air ? 0.15 * Math.sin(T * 3) * hov : 0), 220, dt);
  // ---- body: lean into the run, the dash; jet mode lies it flat (head up)
  const lean = clamp(s.fwd / F.speed, -1, 1.5) * 0.12 + (s.dash ? 0.35 : 0) + jet * 1.35;
  j.hips.rotation.x = spr(inst, 'lean', -lean, 90, dt);
  j.hips.rotation.z = spr(inst, 'roll', -clamp(s.side / F.speed, -1, 1) * 0.12 + inst.jank.tilt, 80, dt);
  // ---- arms (rest = hanging down: x raises them forward, z swings them out)
  let xL = 0.15 * sw, xR = -0.15 * sw, zL = -0.08, zR = 0.08, yL = 0, yR = 0, fL = -0.25, fR = -0.25, twist = 0;
  const aim = clamp(s.pitch || 0, -0.8, 0.8);
  if (pp) {
    xL = xR = -1.45 - aim; fL = fR = -0.05; zL = -0.1; zR = 0.1; // cannons up where you look
    if (s.gunT < 0.12) { const k = 1 - s.gunT / 0.12; if (s.gunSide > 0) xR += k * 0.25; else xL += k * 0.25; }
    if (jet) { xL = xR = -1.45 + 1.6 * jet; zL = -0.1 - 0.15 * jet; zR = -zL; fL = fR = -0.05 - 0.3 * jet; } // tucked along the body
    if (s.dash) xL = xR = -1.9;
    const pk = s.swarmT < 1.2 ? Math.sin(clamp(s.swarmT / 1.2, 0, 1) * Math.PI) : 0; // the pods flip up on a salvo
    for (const L of ['L', 'R']) if (j['pod_' + L]) j['pod_' + L].rotation.x = spr(inst, 'pod' + L, -0.7 * pk, 200, dt);
    for (const [k, sg] of [['wing_L', -1], ['wing_R', 1]]) { // stowed V; spread on a hover; swung down flat in jet mode
      const w = j[k];
      if (!w) continue;
      w.rotation.z = spr(inst, k + 'z', -sg * (hov * 0.25 + jet * 1.15) + (hov ? Math.sin(T * 9) * 0.04 : 0), 90, dt);
      w.rotation.x = spr(inst, k + 'x', jet * 0.4, 90, dt);
    }
    if (inst.att.drone) inst.att.drone.visible = !s.craneOut; // (out flying: mech.js flies a copy)
  } else {
    xR = -0.35 + 0.15 * sw; zR = 0.2; fR = -0.55;
    const si = s.swingI | 0, st = s.swingT;
    if (st < 0.75 && SWING[si]) { // wind-up held, a fast strike that overshoots, follow-through held, recover
      const S = SWING[si], u = st < 0.1 ? ease(st / 0.1) : 1, v = st < 0.1 ? 0 : st < 0.24 ? back((st - 0.1) / 0.14) : 1, r = st > 0.45 ? ease((st - 0.45) / 0.3) : 0;
      const pose = S.up.map((a, i) => a + (S.end[i] - a) * v), k = u * (1 - r);
      xR += (pose[0] - xR) * k; zR += (pose[1] - zR) * k; yR = pose[2] * k; twist = pose[3] * k; fR = -0.2 * k + fR * (1 - k);
    }
    if (s.dash) { xR = -1.6; zR = 0.9; yR = 1.2; twist = -0.5; } // the dash slash: blade out low to the side
    if (s.slam === 1) { xR = -3.0; zR = 0; fR = -0.1; } else if (s.slam === 2) { xR = -1.0; fR = -0.1; twist = 0; }
    const sh = s.shield ? 1 : 0;
    xL = -0.25 - 0.3 * sh + 0.15 * -sw * (1 - sh); zL = -0.15 + 0.6 * sh; fL = -0.4 - 0.25 * sh; // shield up: the arm across the front
    if (j.shield) j.shield.rotation.x = spr(inst, 'shx', 0.85 * sh, 200, dt); // (kept upright, the PLEASE HOLD face forward)
    if (j.beacon) j.beacon.rotation.y = T * 6; // the security light spins
  }
  j.chest.rotation.y = spr(inst, 'tw', twist, pp ? 140 : 260, dt);
  j.chest.rotation.x = spr(inst, 'tp', pp ? -aim * 0.2 : 0, 90, dt);
  const st2 = pp ? 160 : 420; // the knight's swing snaps (stiff springs keep the overshoot readable)
  j.upperarm_L.rotation.x = spr(inst, 'xL', xL, 160, dt); j.upperarm_R.rotation.x = spr(inst, 'xR', xR, st2, dt);
  j.upperarm_L.rotation.z = spr(inst, 'zL', zL, 160, dt); j.upperarm_R.rotation.z = spr(inst, 'zR', zR, st2, dt);
  j.upperarm_L.rotation.y = spr(inst, 'yL', yL, 160, dt); j.upperarm_R.rotation.y = spr(inst, 'yR', yR, st2, dt);
  j.forearm_L.rotation.x = spr(inst, 'fL', fL, 160, dt); j.forearm_R.rotation.x = spr(inst, 'fR', fR, st2, dt);
  j.head.rotation.x = spr(inst, 'hd', -aim * 0.3 - jet * 1.0, 60, dt); // (jet: head up)
  j.head.rotation.z = inst.jank.tilt * 0.6;
  effects(inst, s, T, dt);
}
// what both the code poses and a hero model's clips show: the hatch, flames, muzzle flashes, the sword's arc
function effects(inst, s, T, dt = 0) {
  if (inst.mixer && inst.j.beacon) inst.j.beacon.rotation.y = T * 6; // (the rig leaves the beacon's spin to code)
  inst.hatchOpen = spr(inst, 'hatch', s.empty ? 1 : 0, 40, dt || 0.016);
  if (inst.j.hatch) inst.j.hatch.rotation.x = inst.frame === 'paperplane' ? -inst.hatchOpen * 0.9 : inst.hatchOpen * 1.2; // the nose lifts / the breastplate drops
  inst.own.hatch.color.setHex(s.empty ? (Math.sin(T * 6) > 0 ? 0xffe14d : 0xff4fd8) : 0x2a2f45);
  const burn = Math.max(s.jet || 0, s.hover ? 0.7 : 0, s.dash ? 1 : 0, s.boost || 0);
  for (const f of inst.flames) { f.visible = burn > 0.05; if (f.visible) f.scale.set(0.8 + burn * 0.4, (0.6 + burn) * (0.85 + Math.random() * 0.3), 0.8 + burn * 0.4); }
  for (const L of ['L', 'R']) { const mz = inst.att['mk_muzzle_' + L]; if (mz && mz.userData.flash) { mz.userData.flash.visible = s.gunT < 0.05 && (s.gunSide > 0) === (L === 'R'); mz.userData.flash.scale.setScalar(0.7 + Math.random() * 0.6); } }
  updateTrail(inst, s.slashing);
}
const _a = new THREE.Vector3(), _b = new THREE.Vector3();
function updateTrail(inst, on) {
  const tr = inst.trail;
  if (!tr) return;
  if (!tr.parent && G.scene) G.scene.add(tr);
  const U = tr.userData;
  if (on && inst.root.visible) {
    inst.root.updateMatrixWorld(true);
    inst.att.mk_sword_base.getWorldPosition(_a); inst.att.mk_sword_tip.getWorldPosition(_b);
    U.pts.unshift([_a.x, _a.y, _a.z, _b.x, _b.y, _b.z]);
  } else if (U.pts.length) U.pts.pop();
  while (U.pts.length > U.N) U.pts.pop();
  tr.visible = U.pts.length > 1;
  if (!tr.visible) return;
  const pos = tr.geometry.attributes.position.array, al = tr.geometry.attributes.a.array;
  for (let i = 0; i < U.N; i++) {
    const p = U.pts[Math.min(i, U.pts.length - 1)], a = Math.max(0, 1 - i / (U.pts.length - 1 || 1));
    pos.set(p, i * 6); al[i * 2] = a * 0.4; al[i * 2 + 1] = a;
  }
  tr.geometry.attributes.position.needsUpdate = true; tr.geometry.attributes.a.needsUpdate = true;
}

// ------------------------------------------------------------ it blows up: a big gib pop of its parts
export function mechBurst(inst, vel = [0, 0, 0]) {
  inst.root.updateMatrixWorld(true);
  const c = new THREE.Vector3();
  inst.j.chest.getWorldPosition(c);
  const at = [c.x, c.y + 0.4, c.z];
  rfx.sparks(at, 120, 18, [0xfff2b0, 0xff9a3a, 0xff4fd8, 0x4fd8ff], 1.1, 0.2);
  rfx.smoke(at, 40, 0x3a3c40, 1.8, 2.5, 2.6, 1.4);
  rmesh.flash(at, 7, 0xff8a3a, 0.4);
  rmesh.flash(at, 4, 0xffffff, 0.15);
  const floor = inst.root.getWorldPosition(new THREE.Vector3()).y;
  rmesh.ring([at[0], floor, at[2]], 9, 0xff4fd8, 0.5);
  const meshes = [];
  inst.root.traverse((o) => { if (o.isMesh && o.visible && o.material.blending !== THREE.AdditiveBlending && !o.material.isShaderMaterial && !o.isSkinnedMesh) meshes.push(o); });
  for (const m of meshes) {
    const g = new THREE.Mesh(m.geometry, m.material);
    m.matrixWorld.decompose(g.position, g.quaternion, g.scale);
    G.scene.add(g);
    const out = [g.position.x - c.x, g.position.z - c.z], l = Math.hypot(out[0], out[1]) || 1, k = 5 + Math.random() * 9;
    G.gibs.push({ m: g, own: false, floorY: floor + 0.05, life: 4 + Math.random() * 2,
      v: [vel[0] * 0.3 + out[0] / l * k, 6 + Math.random() * 10, vel[2] * 0.3 + out[1] / l * k], av: [(Math.random() - 0.5) * 14, (Math.random() - 0.5) * 14, (Math.random() - 0.5) * 14] });
  }
  inst.root.visible = false;
}
