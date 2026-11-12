// MECH DROP, the looks: code stand-ins for the two frames until the Blender hero models land (docs/mechs/MECHS.md),
// in each frame's real proportions so it plays right now. PAPER PLANE: a ~5 m folded-paper flyer, origami wings,
// twin forearm cannons, shoulder missile pods, back jets, a crane drone docked on its left wing. NIGHT SHIFT: a ~6 m
// knight, helmet cockpit with a glowing visor, a huge sword, a tower shield with a clock-and-moon crest, back and leg
// boosters. One builder per frame; both expose the same joints and named attachment points (inst.att) so a .glb can
// replace the stand-in later (GLB_ID: its nodes carry those names; a missing file falls back to the stand-in).
// Also here: the pose (walk, hover, jet fold, swings with held key poses and overshoot, shield, slam, landings), the
// sword's glowing arc, jet flames, the glowing hatch, and the gib pop when one blows up.
import * as THREE from 'three';
import { G } from './ctx.js';
import { cbox, cyl, cylX, cylZ, rfx, rmesh } from './rigmodel.js';
import { authored, glossyPaint, nodeIn } from './glbkit.js';
import { MECH } from '/shared/mech.js';

// the hero models' files (tools/blender, public/models): when one is there it replaces the stand-in
export const GLB_ID = { paperplane: 'x_mech_paperplane', nightshift: 'x_mech_nightshift' };
// the attachment points every model has (Blender node names = these)
export const ATT = {
  paperplane: ['cockpit', 'hatch', 'handL', 'handR', 'muzzleL', 'muzzleR', 'podL', 'podR', 'jetL', 'jetR', 'wingL', 'wingR', 'craneDock'],
  nightshift: ['cockpit', 'hatch', 'handL', 'handR', 'swordHand', 'sword', 'swordBase', 'swordTip', 'shieldArm', 'shield', 'boosterL', 'boosterR', 'legBoosterL', 'legBoosterR'],
};
const JOINTS = ['hips', 'torso', 'cockpit', 'hatch', 'shoulderL', 'shoulderR', 'armL', 'armR', 'foreL', 'foreR', 'handL', 'handR', 'thighL', 'thighR', 'shinL', 'shinR', 'footL', 'footR'];

const mats = new Map();
const lam = (c, e = 0.1) => mats.get('l' + c + e) || mats.set('l' + c + e, new THREE.MeshLambertMaterial({ color: c, flatShading: true, emissive: new THREE.Color(c).multiplyScalar(e) })).get('l' + c + e);
const chrome = (c) => mats.get('c' + c) || mats.set('c' + c, new THREE.MeshPhongMaterial({ color: c, specular: 0xffffff, shininess: 110, flatShading: true, emissive: new THREE.Color(c).multiplyScalar(0.1) })).get('c' + c);
const glow = (c) => mats.get('g' + c) || mats.set('g' + c, new THREE.MeshBasicMaterial({ color: c })).get('g' + c);
const PAL = { paper: 0xf6f2e6, crease: 0xc9c2b0, ink: 0x22202a, gun: 0x3a4250, steel: 0x8a96a6, yellow: 0xffe14d, cyan: 0x4fd8ff, navy: 0x1c2140, night: 0x2a2f55, gold: 0xe8b730, red: 0xff3030, black: 0x14141a, chrome: 0xd0d8e2 };

function add(parent, geo, mat, p = [0, 0, 0], r = null, name = '') {
  const m = new THREE.Mesh(geo, mat);
  m.position.fromArray(p);
  if (r) m.rotation.set(r[0], r[1], r[2]);
  if (name) m.name = name;
  parent.add(m);
  return m;
}
function node(parent, name, p = [0, 0, 0]) { const n = new THREE.Group(); n.name = name; n.position.fromArray(p); n.userData.rest = p.slice(); parent.add(n); return n; }
// a flat triangle (a paper fold) with some thickness
function fold(a, b, c, t = 0.05) {
  const s = new THREE.Shape([new THREE.Vector2(a[0], a[1]), new THREE.Vector2(b[0], b[1]), new THREE.Vector2(c[0], c[1])]);
  return new THREE.ExtrudeGeometry(s, { depth: t, bevelEnabled: false }).translate(0, 0, -t / 2);
}
const wedge = (w, h, d) => { const g = new THREE.CylinderGeometry(0, w, d, 4, 1).rotateX(-Math.PI / 2).rotateZ(Math.PI / 4); g.scale(1, h / w, 1); return g; };

// ------------------------------------------------------------ PAPER PLANE
function buildPaper(j, own) {
  const P = PAL, paper = lam(P.paper, 0.18), crease = lam(P.crease), ink = lam(P.ink, 0.05), gun = lam(P.gun), acc = own.accent;
  // legs: light, bird-like, knees forward
  for (const s of [-1, 1]) {
    const L = s < 0 ? 'L' : 'R', th = j['thigh' + L], sh = j['shin' + L], ft = j['foot' + L];
    add(th, cbox(0.36, 1.0, 0.42, 0.06), paper, [0, -0.5, 0]);
    add(th, cbox(0.4, 0.18, 0.46, 0.04), acc, [0, -0.15, 0]);
    add(sh, cbox(0.3, 1.0, 0.34, 0.05), paper, [0, -0.5, 0]);
    add(sh, cbox(0.32, 0.5, 0.06, 0.02), crease, [0, -0.5, -0.19]); // a crease down the shin
    add(sh, cylX(0.16, 0.42, 8), gun, [0, 0, 0]); // knee joint
    add(ft, wedge(0.5, 0.22, 0.95), paper, [0, 0.1, -0.12]);
    add(ft, cbox(0.48, 0.1, 0.5, 0.02), gun, [0, 0.03, 0.18]);
  }
  add(j.hips, cbox(1.0, 0.45, 0.7, 0.08), gun, [0, 0, 0]);
  add(j.hips, cbox(1.1, 0.16, 0.74, 0.04), acc, [0, 0.22, 0]);
  // torso: a folded paper chest, narrow waist
  add(j.torso, cbox(0.7, 0.6, 0.55, 0.06), gun, [0, 0.35, 0]);
  add(j.torso, cbox(1.6, 1.15, 1.0, 0.12), paper, [0, 1.05, 0]);
  add(j.torso, wedge(1.5, 0.5, 1.2), paper, [0, 1.05, -0.6], [0, 0, 0]); // the chest's paper-plane nose
  add(j.torso, cbox(1.62, 0.08, 1.02, 0.02), crease, [0, 0.95, 0]); // fold line
  add(j.torso, cbox(0.5, 0.5, 0.1, 0.03), acc, [0, 1.15, -0.53]); // a chest panel in your colour
  add(j.torso, cbox(0.18, 0.18, 0.04, 0.01), glow(P.cyan), [0, 1.15, -0.6]);
  // cockpit: the canopy on top (the head: hits here are cockpit hits)
  add(j.cockpit, cbox(1.15, 0.85, 1.15, 0.1), paper, [0, 0, 0.05]);
  add(j.cockpit, wedge(1.0, 0.55, 0.9), paper, [0, -0.05, -0.75]);
  const glass = new THREE.MeshPhongMaterial({ color: 0x5fe8ff, specular: 0xffffff, shininess: 140, transparent: true, opacity: 0.75, emissive: 0x0a3a48 });
  add(j.cockpit, cbox(0.9, 0.42, 0.7, 0.08), glass, [0, 0.18, -0.35]);
  add(j.cockpit, cbox(1.2, 0.08, 1.2, 0.02), acc, [0, 0.46, 0.05]);
  add(j.cockpit, fold([0, 0], [0.5, 0], [0, 0.55], 0.04), paper, [0, 0.45, 0.5], [0, Math.PI / 2, 0]); // a tail fin, folded
  add(j.hatch, cbox(0.7, 0.5, 0.06, 0.02), own.hatch, [0, -0.25, 0]);
  // wings: two big origami folds, a V off the back (they sweep flat in jet mode)
  for (const s of [-1, 1]) {
    const w = node(j.torso, s < 0 ? 'wingL' : 'wingR', [0.35 * s, 1.35, 0.5]);
    const pivot = node(w, 'wfold', [0, 0, 0]);
    add(pivot, fold([0, 0], [2.4 * s, 0.4], [0.3 * s, -0.9], 0.05), paper, [0, 0, 0], [Math.PI / 2 - 0.1, 0, 0]);
    add(pivot, fold([0.25 * s, -0.1], [2.3 * s, 0.35], [2.0 * s, 0.25], 0.06), acc, [0, 0.02, 0], [Math.PI / 2 - 0.1, 0, 0]); // the leading edge stripe
    add(pivot, cbox(0.12, 0.12, 0.9, 0.02), crease, [0.9 * s, 0.03, -0.05], [0, -0.35 * s, 0]);
    w.userData.pivot = pivot;
    if (s < 0) { const dock = node(pivot, 'craneDock', [1.3 * s, 0.25, 0.2]); dock.add(buildCrane(own.accent)); dock.userData.crane = dock.children[0]; }
  }
  // back jets
  for (const s of [-1, 1]) {
    const jt = node(j.torso, s < 0 ? 'jetL' : 'jetR', [0.42 * s, 0.75, 0.55]);
    add(jt, cyl(0.2, 0.26, 0.55, 10), gun, [0, 0, 0], [Math.PI / 2 - 0.5, 0, 0]);
    add(jt, cyl(0.15, 0.15, 0.06, 10), glow(0xff7a3d), [0, -0.12, 0.22], [Math.PI / 2 - 0.5, 0, 0]);
  }
  // arms: shoulders, then forearms that are the twin cannons
  for (const s of [-1, 1]) {
    const L = s < 0 ? 'L' : 'R';
    add(j['shoulder' + L], cbox(0.62, 0.55, 0.65, 0.08), paper, [0.1 * s, 0, 0]);
    const pod = node(j['shoulder' + L], 'pod' + L, [0.18 * s, 0.45, 0.05]);
    add(pod, cbox(0.5, 0.36, 0.62, 0.05), acc, [0, 0, 0]);
    for (let r = 0; r < 2; r++) for (let c = 0; c < 3; c++) add(pod, cylZ(0.06, 0.04, 6), glow(P.red), [(-0.13 + r * 0.26), 0.02, -0.32 + c * 0.0], null).position.set(-0.14 + r * 0.28, -0.08 + c * 0.08, -0.32);
    add(j['arm' + L], cbox(0.34, 0.85, 0.38, 0.05), paper, [0, -0.42, 0]);
    add(j['fore' + L], cbox(0.42, 0.42, 1.0, 0.06), gun, [0, 0, -0.3]);
    add(j['fore' + L], cbox(0.44, 0.12, 0.9, 0.03), acc, [0, 0.23, -0.3]);
    for (const b of [-0.1, 0.1]) add(j['fore' + L], cylZ(0.07, 0.75, 8), chrome(P.chrome), [b, -0.05, -1.05]);
    const mz = node(j['fore' + L], 'muzzle' + L, [0, -0.05, -1.45]);
    mz.userData.flash = add(mz, new THREE.SphereGeometry(0.22, 8, 6), new THREE.MeshBasicMaterial({ color: 0xfff2a0, transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending, depthWrite: false }));
    mz.userData.flash.visible = false;
    j['hand' + L].position.set(0, -0.05, -0.85);
  }
  return { paper, acc };
}
// the origami crane drone (also flown by mech.js)
export function buildCrane(color) {
  const g = new THREE.Group(), m = color && color.isMaterial ? color : lam(new THREE.Color(color || '#ff4fd8').getHex(), 0.3), w = lam(PAL.paper, 0.25);
  add(g, wedge(0.22, 0.2, 0.55), w, [0, 0, 0]);
  add(g, cbox(0.05, 0.32, 0.05, 0.01), w, [0, 0.12, -0.3], [0.6, 0, 0]); // neck
  add(g, wedge(0.07, 0.07, 0.2), m, [0, 0.27, -0.42]); // head / beak
  const wl = add(g, fold([0, 0], [-0.55, 0.15], [-0.1, -0.25], 0.02), w, [-0.05, 0.05, 0], [Math.PI / 2, 0, 0]);
  const wr = add(g, fold([0, 0], [0.55, 0.15], [0.1, -0.25], 0.02), w, [0.05, 0.05, 0], [Math.PI / 2, 0, 0]);
  add(g, wedge(0.12, 0.08, 0.3), m, [0, 0.05, 0.3], [0.4, Math.PI, 0]); // tail
  g.userData.wings = [wl, wr];
  return g;
}

// ------------------------------------------------------------ NIGHT SHIFT
function buildKnight(j, own) {
  const P = PAL, navy = lam(P.navy, 0.12), night = lam(P.night, 0.14), gold = chrome(P.gold), steel = chrome(P.steel), acc = own.accent, black = lam(P.black, 0.05);
  for (const s of [-1, 1]) {
    const L = s < 0 ? 'L' : 'R';
    add(j['thigh' + L], cbox(0.62, 1.25, 0.7, 0.1), navy, [0, -0.62, 0]);
    add(j['thigh' + L], cbox(0.68, 0.2, 0.76, 0.04), gold, [0, -0.08, 0]);
    add(j['shin' + L], cbox(0.58, 1.25, 0.66, 0.1), night, [0, -0.62, 0]);
    add(j['shin' + L], cbox(0.5, 0.6, 0.12, 0.04), steel, [0, -0.45, -0.36]); // greave
    add(j['shin' + L], cylX(0.24, 0.66, 10), gold, [0, 0, 0]); // knee
    const lb = node(j['shin' + L], 'legBooster' + L, [0, -0.7, 0.38]);
    add(lb, cyl(0.16, 0.22, 0.5, 10), black, [0, 0, 0]);
    add(lb, cyl(0.13, 0.13, 0.05, 10), glow(0x7dffff), [0, -0.26, 0]);
    add(j['foot' + L], cbox(0.72, 0.36, 1.25, 0.1), navy, [0, 0.16, -0.18]);
    add(j['foot' + L], cbox(0.74, 0.12, 0.5, 0.04), gold, [0, 0.3, -0.62]);
  }
  add(j.hips, cbox(1.5, 0.6, 0.95, 0.1), night, [0, 0, 0]);
  add(j.hips, cbox(1.1, 1.1, 0.12, 0.04), acc, [0, -0.55, -0.5]); // tabard front, your colour
  add(j.hips, cbox(1.3, 1.0, 0.1, 0.04), acc, [0, -0.5, 0.5]);
  add(j.torso, cbox(1.3, 0.8, 0.95, 0.1), navy, [0, 0.4, 0]);
  add(j.torso, cbox(2.1, 1.55, 1.3, 0.16), night, [0, 1.35, 0]);
  add(j.torso, cbox(1.5, 0.95, 0.12, 0.05), steel, [0, 1.45, -0.68]); // breastplate
  add(j.torso, cbox(0.18, 0.95, 0.04, 0.02), gold, [0, 1.45, -0.75]);
  add(j.torso, cbox(2.14, 0.12, 1.34, 0.03), gold, [0, 0.62, 0]);
  // helmet = cockpit, a visor slit that glows, a crest fin
  add(j.cockpit, cbox(1.2, 1.15, 1.2, 0.14), navy, [0, 0, 0]);
  add(j.cockpit, cbox(1.25, 0.18, 1.25, 0.04), gold, [0, -0.5, 0]);
  add(j.cockpit, cbox(0.95, 0.14, 0.08, 0.02), own.visor, [0, 0.05, -0.62]);
  add(j.cockpit, cbox(1.0, 0.5, 0.1, 0.04), steel, [0, -0.25, -0.62]);
  add(j.cockpit, cbox(0.12, 0.65, 1.3, 0.04), acc, [0, 0.75, 0.05]); // the crest
  add(j.hatch, cbox(0.6, 0.45, 0.06, 0.02), own.hatch, [0, -0.22, 0]);
  // back boosters
  for (const s of [-1, 1]) {
    const b = node(j.torso, s < 0 ? 'boosterL' : 'boosterR', [0.55 * s, 1.3, 0.75]);
    add(b, cyl(0.28, 0.34, 1.3, 10), black, [0, 0, 0]);
    add(b, cyl(0.3, 0.3, 0.14, 10), gold, [0, 0.55, 0]);
    add(b, cyl(0.22, 0.22, 0.05, 10), glow(0x7dffff), [0, -0.66, 0]);
  }
  // arms: pauldrons, heavy forearms
  for (const s of [-1, 1]) {
    const L = s < 0 ? 'L' : 'R';
    add(j['shoulder' + L], cbox(0.95, 0.75, 1.05, 0.14), navy, [0.15 * s, 0.05, 0]);
    add(j['shoulder' + L], cbox(1.0, 0.16, 1.1, 0.04), gold, [0.15 * s, 0.38, 0]);
    add(j['arm' + L], cbox(0.52, 1.0, 0.56, 0.08), night, [0, -0.5, 0]);
    add(j['fore' + L], cbox(0.6, 1.0, 0.64, 0.08), navy, [0, -0.5, 0]);
    add(j['fore' + L], cbox(0.64, 0.16, 0.68, 0.04), gold, [0, -0.1, 0]);
    add(j['hand' + L], cbox(0.5, 0.5, 0.5, 0.08), black, [0, 0, 0]);
  }
  // the sword in the right hand: grip, gold guard, a long blade with a glowing edge
  const sh = node(j.handR, 'swordHand', [0, 0, 0]);
  const sw = node(sh, 'sword', [0, 0, 0]);
  add(sw, cylZ(0.09, 0.8, 8), black, [0, 0, 0.1]);
  add(sw, cbox(1.0, 0.18, 0.2, 0.04), gold, [0, 0, -0.32]);
  add(sw, cbox(0.32, 0.08, 3.6, 0.03), steel, [0, 0, -2.2]);
  add(sw, cbox(0.06, 0.1, 3.5, 0.01), own.edge, [0.17, 0, -2.2]);
  add(sw, cbox(0.06, 0.1, 3.5, 0.01), own.edge, [-0.17, 0, -2.2]);
  add(sw, wedge(0.32, 0.08, 0.5), steel, [0, 0, -4.2]);
  node(sw, 'swordBase', [0, 0, -0.5]);
  node(sw, 'swordTip', [0, 0, -4.4]);
  // the tower shield on the left forearm: the night shift crest (a clock and a moon)
  const sa = node(j.foreL, 'shieldArm', [-0.38, -0.55, -0.1]);
  const shd = node(sa, 'shield', [0, 0, 0]);
  add(shd, cbox(0.18, 2.7, 1.5, 0.08), night, [0, 0, 0]);
  add(shd, cbox(0.2, 2.8, 0.12, 0.03), gold, [0, 0, -0.75]);
  add(shd, cbox(0.2, 2.8, 0.12, 0.03), gold, [0, 0, 0.75]);
  add(shd, cbox(0.2, 0.12, 1.6, 0.03), gold, [0, 1.38, 0]);
  add(shd, new THREE.CylinderGeometry(0.5, 0.5, 0.06, 20).rotateZ(Math.PI / 2), lam(0xf4f0e0, 0.4), [-0.11, 0.3, 0]); // clock face
  add(shd, cbox(0.04, 0.4, 0.06, 0.01), black, [-0.15, 0.45, 0]); // hands at ten to midnight
  add(shd, cbox(0.04, 0.06, 0.3, 0.01), black, [-0.15, 0.32, 0.1], [0.6, 0, 0]);
  add(shd, new THREE.TorusGeometry(0.32, 0.07, 6, 12, Math.PI * 1.2).rotateY(Math.PI / 2), own.visor, [-0.12, -0.55, 0]); // the moon
  return {};
}

// ------------------------------------------------------------ build / free
const REST = { // joint rest positions per frame (metres, from the parent joint): legs, torso, cockpit, shoulders
  paperplane: { hips: 2.05, torso: [0, 0.25, 0], cockpit: [0, 2.15, 0.05], hatch: [0, 0.32, -0.62], shoulder: [1.05, 1.45, 0.05], arm: [0, 0, 0], fore: [0, -0.85, 0], hip: [0.36, -0.1, 0], shin: [0, -1.0, 0], foot: [0, -1.02, 0] },
  nightshift: { hips: 2.55, torso: [0, 0.3, 0], cockpit: [0, 2.7, 0], hatch: [0, 0.35, -0.65], shoulder: [1.45, 1.85, 0], arm: [0, -0.1, 0], fore: [0, -1.0, 0], hip: [0.48, -0.15, 0], shin: [0, -1.25, 0], foot: [0, -1.27, 0] },
};
export function buildMech(frame, color, opts = {}) {
  frame = frame === 'nightshift' ? 'nightshift' : 'paperplane';
  const col = new THREE.Color(color || '#ff4fd8');
  const own = {
    accent: glossyPaint(col, 0.25),
    hatch: new THREE.MeshBasicMaterial({ color: 0xffe14d, transparent: true, opacity: 0.95 }),
    visor: new THREE.MeshBasicMaterial({ color: frame === 'nightshift' ? 0x7dffff : 0x4fd8ff }),
    edge: new THREE.MeshBasicMaterial({ color: 0xc8a8ff }),
  };
  const root = new THREE.Group(), j = {};
  root.name = 'mech_' + frame;
  const R = REST[frame];
  j.hips = node(root, 'hips', [0, R.hips, 0]);
  j.torso = node(j.hips, 'torso', R.torso);
  j.cockpit = node(j.torso, 'cockpit', R.cockpit);
  j.hatch = node(j.cockpit, 'hatch', R.hatch);
  for (const s of [-1, 1]) {
    const L = s < 0 ? 'L' : 'R';
    j['shoulder' + L] = node(j.torso, 'shoulder' + L, [R.shoulder[0] * s, R.shoulder[1], R.shoulder[2]]);
    j['arm' + L] = node(j['shoulder' + L], 'arm' + L, R.arm);
    j['fore' + L] = node(j['arm' + L], 'fore' + L, R.fore);
    j['hand' + L] = node(j['fore' + L], 'hand' + L, [0, -1.0, 0]);
    j['thigh' + L] = node(j.hips, 'thigh' + L, [R.hip[0] * s, R.hip[1], R.hip[2]]);
    j['shin' + L] = node(j['thigh' + L], 'shin' + L, R.shin);
    j['foot' + L] = node(j['shin' + L], 'foot' + L, R.foot);
  }
  j.torso.rotation.order = 'YXZ';
  for (const s of ['L', 'R']) j['shoulder' + s].rotation.order = 'XZY';
  let glb = null;
  const a = opts.noGlb ? null : authored(GLB_ID[frame]);
  if (a) { // the hero model: its nodes are the joints and attachment points (same names)
    glb = a.obj; root.add(glb);
    for (const k of JOINTS) { const n = nodeIn(glb, k); if (n) { j[k] = n; n.userData.rest = n.position.toArray(); } }
    j.hips.visible = false; // (the stand-in's skeleton stays only as a fallback for missing joints)
  } else if (frame === 'paperplane') buildPaper(j, own);
  else buildKnight(j, own);
  const att = {};
  for (const k of ATT[frame]) att[k] = (glb && nodeIn(glb, k)) || j[k] || nodeIn(root, k);
  // jet flames on every nozzle (additive cones pointing out the back / down)
  const flameMat = new THREE.MeshBasicMaterial({ color: 0xff7ae8, transparent: true, opacity: 0.8, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
  const coreMat = new THREE.MeshBasicMaterial({ color: 0xfff4c0, transparent: true, opacity: 0.95, blending: THREE.AdditiveBlending, depthWrite: false });
  const flames = [];
  for (const k of ['jetL', 'jetR', 'boosterL', 'boosterR', 'legBoosterL', 'legBoosterR']) {
    const n = att[k];
    if (!n) continue;
    const f = new THREE.Group();
    const up = k.startsWith('jet') ? [Math.PI / 2 - 0.5 + Math.PI, 0, 0] : [Math.PI, 0, 0];
    f.rotation.set(up[0], up[1], up[2]);
    f.position.set(0, k.startsWith('jet') ? -0.1 : -0.7, k.startsWith('jet') ? 0.25 : 0);
    if (k.startsWith('leg')) f.position.y = -0.3;
    const big = k.startsWith('leg') ? 0.7 : 1;
    add(f, new THREE.ConeGeometry(0.22 * big, 1.4 * big, 10, 1, true).translate(0, 0.7 * big, 0), flameMat);
    add(f, new THREE.ConeGeometry(0.1 * big, 0.8 * big, 8).translate(0, 0.4 * big, 0), coreMat);
    for (const c of f.children) c.renderOrder = 7;
    f.visible = false;
    n.add(f); flames.push(f);
  }
  // the glowing sword arc (a ribbon behind the blade while it swings)
  let trail = null;
  if (att.swordTip) {
    const N = 14, geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(N * 2 * 3), 3).setUsage(THREE.DynamicDrawUsage));
    geo.setAttribute('a', new THREE.BufferAttribute(new Float32Array(N * 2), 1).setUsage(THREE.DynamicDrawUsage));
    const idx = []; for (let i = 0; i < N - 1; i++) { const a2 = i * 2; idx.push(a2, a2 + 1, a2 + 2, a2 + 1, a2 + 3, a2 + 2); }
    geo.setIndex(idx);
    const mat = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending,
      uniforms: { uC: { value: new THREE.Color(0xb98cff) } },
      vertexShader: 'attribute float a; varying float vA; void main(){ vA = a; gl_Position = projectionMatrix * viewMatrix * vec4(position, 1.0); }',
      fragmentShader: 'uniform vec3 uC; varying float vA; void main(){ gl_FragColor = vec4(mix(uC, vec3(1.0), vA * vA), vA * 0.85); }' });
    trail = new THREE.Mesh(geo, mat); trail.frustumCulled = false; trail.renderOrder = 8;
    trail.userData = { N, pts: [], on: false };
  }
  const inst = { frame, root, j, att, own, flames, flameMat, coreMat, trail, glb: !!glb, sp: {}, phase: 0, t: Math.random() * 10, stepSide: 1,
    jank: { tilt: (Math.random() - 0.5) * 0.1, knee: Math.random() < 0.5 ? 'L' : 'R' }, hatchOpen: 0 };
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
// s: { spd, fwd, side (local m/s), air, vy, hover, jet (0..1), dash, shield, swingT, swingI, slamT, slam, tripleT,
//      gunT, gunSide, swarmT, craneOut, landT, landK, pitch, empty (nobody in it: hatch open + glow), boost, t }
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const back = (u) => { const c = 1.9; return 1 + (c + 1) * Math.pow(u - 1, 3) + c * Math.pow(u - 1, 2); }; // overshoot
const ease = (u) => u * u * (3 - 2 * u);
function spr(inst, k, target, stiff, dt) { // a critically-ish damped spring per channel (the "settle" after a key pose)
  const s = inst.sp[k] || (inst.sp[k] = { x: target, v: 0 });
  const d = 2 * Math.sqrt(stiff) * 0.6;
  const n = Math.max(1, Math.ceil(dt * 120)), h = dt / n;
  for (let i = 0; i < n; i++) { s.v += (stiff * (target - s.x) - d * s.v) * h; s.x += s.v * h; }
  return s.x;
}
// a sword swing: wind-up (held), strike (fast, overshoots), follow-through (held), recover. returns the arm angles
const SWING = [ // [shoulder x (raise), shoulder z (out), shoulder y (twist), torso twist] for wind-up and strike end
  { up: [-2.4, -0.5, 0.6, 0.55], end: [-0.4, 0.2, -0.9, -0.7] }, // right to left, high
  { up: [-1.2, 0.9, -0.8, -0.6], end: [-0.9, -0.3, 0.9, 0.6] }, // back the other way
  { up: [-3.0, 0.1, 0.1, 0.2], end: [-0.1, 0.0, 0.0, -0.1] }, // the big overhead
];
export function poseMech(inst, s, dt) {
  const j = inst.j, pp = inst.frame === 'paperplane', T = inst.t += dt;
  const F = MECH[inst.frame];
  // ---- legs: a stomping walk, planted feet, knees bend on landings
  const run = clamp(s.spd / F.speed, 0, 1.4);
  if (!s.air && s.spd > 0.6) inst.phase += dt * (1.4 + s.spd * (pp ? 0.32 : 0.26));
  const ph = inst.phase * Math.PI, sw = Math.sin(ph) * 0.55 * run, lift = Math.max(0, Math.cos(ph));
  const land = s.landT < 0.5 ? Math.sin(clamp(s.landT / 0.5, 0, 1) * Math.PI) * (0.4 + s.landK * 0.6) : 0;
  const crouch = (s.shield ? 0.25 : 0) + land + (s.slam === 1 ? 0.3 : 0);
  const air = s.air ? 1 : 0, jet = s.jet || 0, hov = s.hover ? 1 : 0;
  for (const [L, sg] of [['L', 1], ['R', -1]]) {
    const leg = sw * sg, k = Math.max(0, -Math.sin(ph) * sg) * run;
    let th = -leg - crouch * 0.9 - air * (0.35 + hov * 0.4) - jet * 1.2, sn = crouch * 1.7 + k * 0.9 + air * (0.7 + hov * 0.5) + jet * 1.9;
    if (inst.jank.knee === L) sn += 0.08; // a knee that bends just a bit wrong
    j['thigh' + L].rotation.x = spr(inst, 'th' + L, th, 140, dt);
    j['shin' + L].rotation.x = spr(inst, 'sn' + L, sn, 140, dt);
    j['foot' + L].rotation.x = spr(inst, 'ft' + L, -th - sn + (s.air ? 0.4 : 0), 160, dt);
  }
  const bob = !s.air ? -Math.abs(Math.sin(ph)) * 0.12 * run - crouch * 0.45 : 0;
  j.hips.position.y = spr(inst, 'hy', j.hips.userData.rest[1] + bob + (s.air ? 0.15 * Math.sin(T * 3) * hov : 0), 220, dt);
  // ---- torso: lean into the run, the dash, the jet; the jank tilt
  const lean = clamp(s.fwd / F.speed, -1, 1.5) * 0.12 + (s.dash ? 0.35 : 0) + jet * 1.25;
  j.hips.rotation.x = spr(inst, 'lean', lean, 90, dt);
  j.hips.rotation.z = spr(inst, 'roll', -clamp(s.side / F.speed, -1, 1) * 0.12 + inst.jank.tilt, 80, dt);
  // ---- arms by frame
  let sxL = 0.15 * sw, sxR = -0.15 * sw, szL = 0.1, szR = -0.1, syL = 0, syR = 0, fL = -0.3, fR = -0.3, twist = 0;
  const aim = clamp(s.pitch || 0, -0.8, 0.8);
  if (pp) {
    // cannons forward where you look; a kick on each shot, alternating
    sxL = sxR = -1.45 - aim; fL = fR = -0.05; szL = 0.12; szR = -0.12;
    if (s.gunT < 0.12) { const k = 1 - s.gunT / 0.12; if (s.gunSide > 0) sxR += k * 0.25; else sxL += k * 0.25; }
    if (jet) { sxL = sxR = -1.4 + 1.4 * jet; szL = 0.12 + 0.2 * jet; szR = -szL; fL = fR = -0.05 - 0.4 * jet; } // tucked back along the body
    if (s.dash) { sxL = sxR = -1.9; } // arms forward into the lunge
    // pods pop open on a swarm
    const pk = s.swarmT < 1.2 ? Math.sin(clamp(s.swarmT / 1.2, 0, 1) * Math.PI) : 0;
    for (const L of ['L', 'R']) if (inst.att['pod' + L]) inst.att['pod' + L].rotation.x = spr(inst, 'pod' + L, -0.6 * pk, 200, dt);
    // wings: spread on hover, sweep back flat in jet mode, flutter
    for (const [k, sg] of [['wingL', -1], ['wingR', 1]]) {
      const w = inst.att[k];
      if (!w) continue;
      const open = 0.25 + hov * 0.35 - jet * 0.2;
      w.rotation.z = spr(inst, k + 'z', sg * open + (hov ? Math.sin(T * 9) * 0.04 : 0), 90, dt);
      w.rotation.y = spr(inst, k + 'y', -sg * jet * 0.7, 90, dt);
      w.rotation.x = spr(inst, k + 'x', jet * 1.1, 90, dt);
    }
    const crane = inst.att.craneDock && inst.att.craneDock.userData.crane;
    if (crane) crane.visible = !s.craneOut;
  } else {
    // the knight: sword arm by the swing, the shield arm up when blocking
    sxR = -0.35 + 0.15 * sw; szR = -0.25; fR = -0.55; syR = 0;
    const si = s.swingI | 0, st = s.swingT;
    if (st < 0.75 && SWING[si]) { // wind-up held 0.08, strike over 0.12 with overshoot, follow-through held, recover
      const S = SWING[si], u = st < 0.1 ? ease(st / 0.1) : 1, v = st < 0.1 ? 0 : st < 0.24 ? back((st - 0.1) / 0.14) : 1, r = st > 0.45 ? ease((st - 0.45) / 0.3) : 0;
      const pose = S.up.map((a, i) => a + (S.end[i] - a) * v);
      const k = u * (1 - r);
      sxR = sxR + (pose[0] - sxR) * k; szR = szR + (pose[1] - szR) * k; syR = pose[2] * k; twist = pose[3] * k; fR = -0.2 * k + fR * (1 - k);
    }
    if (s.dash) { sxR = -1.6; szR = -0.9; syR = 1.2; twist = -0.5; } // triple shift: blade out to the side, low
    if (s.slam === 1) { sxR = -3.0; szR = 0; fR = -0.1; } // up: the sword over its head
    else if (s.slam === 2) { sxR = -1.0; fR = -0.1; twist = 0; }
    const sh = s.shield ? 1 : 0;
    sxL = -0.25 - 1.3 * sh + 0.15 * -sw; szL = 0.25 + 0.35 * sh; fL = -0.4 - 1.0 * sh; syL = -0.9 * sh;
    if (inst.att.shield) inst.att.shield.rotation.y = spr(inst, 'shy', sh * 0.9, 120, dt);
  }
  j.torso.rotation.y = spr(inst, 'tw', twist, pp ? 140 : 260, dt);
  j.torso.rotation.x = spr(inst, 'tp', pp ? -aim * 0.25 : 0, 90, dt);
  const st2 = pp ? 160 : 420; // the knight's swing snaps (stiff springs keep the overshoot readable)
  j.shoulderL.rotation.x = spr(inst, 'sxL', sxL, 160, dt); j.shoulderR.rotation.x = spr(inst, 'sxR', sxR, st2, dt);
  j.shoulderL.rotation.z = spr(inst, 'szL', szL, 160, dt); j.shoulderR.rotation.z = spr(inst, 'szR', szR, st2, dt);
  j.shoulderL.rotation.y = spr(inst, 'syL', syL, 160, dt); j.shoulderR.rotation.y = spr(inst, 'syR', syR, st2, dt);
  j.foreL.rotation.x = spr(inst, 'fL', fL, 160, dt); j.foreR.rotation.x = spr(inst, 'fR', fR, st2, dt);
  j.cockpit.rotation.x = spr(inst, 'ck', -aim * 0.3, 60, dt);
  j.cockpit.rotation.z = inst.jank.tilt * 0.6;
  // ---- the hatch: open + glowing while it waits for you
  inst.hatchOpen = spr(inst, 'hatch', s.empty ? 1 : 0, 40, dt);
  j.hatch.rotation.x = -inst.hatchOpen * 1.6;
  inst.own.hatch.color.setHex(s.empty ? (Math.sin(T * 6) > 0 ? 0xffe14d : 0xff4fd8) : 0x2a2f45);
  // ---- flames
  const burn = Math.max(jet, hov * 0.7, s.dash ? 1 : 0, s.boost || 0);
  for (const f of inst.flames) { f.visible = burn > 0.05; if (f.visible) f.scale.set(0.8 + burn * 0.4, (0.6 + burn) * (0.85 + Math.random() * 0.3), 0.8 + burn * 0.4); }
  // muzzle flashes
  for (const L of ['L', 'R']) { const mz = inst.att['muzzle' + L]; if (mz && mz.userData.flash) { mz.userData.flash.visible = s.gunT < 0.05 && (s.gunSide > 0) === (L === 'R'); mz.userData.flash.scale.setScalar(0.7 + Math.random() * 0.6); } }
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
    inst.att.swordBase.getWorldPosition(_a); inst.att.swordTip.getWorldPosition(_b);
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
  inst.j.torso.getWorldPosition(c);
  const at = [c.x, c.y + 0.8, c.z];
  rfx.sparks(at, 120, 18, [0xfff2b0, 0xff9a3a, 0xff4fd8, 0x4fd8ff], 1.1, 0.2);
  rfx.smoke(at, 40, 0x3a3c40, 1.8, 2.5, 2.6, 1.4);
  rmesh.flash(at, 7, 0xff8a3a, 0.4);
  rmesh.flash(at, 4, 0xffffff, 0.15);
  rmesh.ring([at[0], inst.root.position.y, at[2]], 9, 0xff4fd8, 0.5);
  const floor = inst.root.getWorldPosition(new THREE.Vector3()).y;
  const meshes = [];
  inst.root.traverse((o) => { if (o.isMesh && o.visible && o.material.blending !== THREE.AdditiveBlending && !o.material.isShaderMaterial) meshes.push(o); });
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
