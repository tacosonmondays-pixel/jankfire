// The katana, held like a katana: two fists on the tsuka (right one behind the tsuba, left one at the kashira) and
// forearms that run back to your shoulders off screen, so the hands never float. Keyframes in anim.js move the wrap as
// usual; the channel 'kl' (0..1) says how much the left hand is on the grip (an iai draw is one-handed until the left
// hand joins, the inspect lets go to turn the blade over). Third person: the left arm reaches round to the kashira.
import * as THREE from 'three';
import { M } from './models.js';
import { G } from './ctx.js';
import { ANIMS } from './anim.js';

const SKIN = 0xf1c27d, KNUCK = 0xe3ae68;
const GRIP_R = -0.083, GRIP_L = 0.085; // model z of each fist's centre (the tsuka runs -0.13 .. +0.13, blade to -z)
const SH_R = new THREE.Vector3(0.27, -0.56, 0.1), SH_L = new THREE.Vector3(-0.2, -0.6, 0.1); // shoulders, camera space
const REST_L = new THREE.Vector3(-0.2, -0.5, -0.16); // where the left hand waits when it isn't on the grip
const FORE = 0.36; // forearm length (it's cut off by the screen edge long before the elbow)
const v1 = new THREE.Vector3(), v2 = new THREE.Vector3(), v3 = new THREE.Vector3(), UP = new THREE.Vector3(0, 1, 0);

function sleeveColor() {
  const lk = (G.settings && G.settings.look) || {};
  if (!['hoodie', 'jacket', 'suit', 'runner', 'maid'].includes(lk.top)) return null;
  try { return new THREE.Color(lk.topColor || lk.color || '#2a2440').getHex(); } catch { return 0x2a2440; }
}

// a fist closed round the tsuka: back of the hand + knuckles on top (the mune side), fingers wrapped under the edge,
// thumb hooked round the left side
function fist(left) {
  const g = new THREE.Group(), sx = left ? -1 : 1;
  const back = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.03, 0.074), M(SKIN)); back.position.set(0.004 * sx, 0.022, 0); g.add(back);
  const fing = new THREE.Mesh(new THREE.BoxGeometry(0.052, 0.026, 0.07), M(KNUCK)); fing.position.set(0, -0.021, 0); g.add(fing);
  const side = new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.05, 0.072), M(SKIN)); side.position.set(0.024 * sx, 0, 0); g.add(side); // the palm / heel side
  for (let i = 0; i < 4; i++) { const k = new THREE.Mesh(new THREE.BoxGeometry(0.012, 0.012, 0.016), M(KNUCK)); k.position.set(-0.012 * sx, 0.034, -0.026 + i * 0.0175); g.add(k); }
  const th = new THREE.Mesh(new THREE.BoxGeometry(0.016, 0.034, 0.03), M(SKIN)); th.position.set(-0.026 * sx, 0.004, -0.024); th.rotation.x = 0.35; g.add(th);
  return g;
}
function forearm(sl) {
  const g = new THREE.Group();
  const f = new THREE.Mesh(new THREE.CylinderGeometry(0.026, 0.032, FORE, 7), M(SKIN)); f.position.y = FORE / 2; g.add(f);
  const wr = new THREE.Mesh(new THREE.CylinderGeometry(0.029, 0.029, 0.03, 7), M(0xff4fd8)); wr.position.y = 0.05; g.add(wr); // a pink sweatband, because of course
  if (sl != null) { const s = new THREE.Mesh(new THREE.CylinderGeometry(0.038, 0.042, FORE * 0.55, 7), M(sl)); s.position.y = FORE * 0.78; g.add(s); }
  return g;
}

// knives: the same closed fist round the handle instead of the old box under it (the box read as a brick when the
// inspect turns the knife over). knife models all put the grip axis on y = 0, the hand over z -0.036 .. +0.08
export function wrapFist(m, hand, z = 0.022, k = 1) {
  if (hand) hand.visible = false;
  const f = fist(false); f.scale.setScalar(k); f.position.set(0, 0, z * m.cfg.s); m.wrap.add(f);
  return f;
}
// once per viewmodel build (weapons.js rebuildViewmodels). hand = the default single fist, hidden
export function katanaHands(m, hand) {
  if (hand) hand.visible = false;
  const s = m.cfg.s, sl = sleeveColor(), kh = {};
  for (const [k, z] of [['R', GRIP_R], ['L', GRIP_L]]) {
    const f = fist(k === 'L'); f.scale.setScalar(s); m.wrap.add(f);
    const a = forearm(sl); m.wrap.add(a);
    kh[k] = { f, a, z: z * s };
  }
  m.kh = kh;
}

// every frame, after the wrap has its pose. kl = left hand on the grip (0..1)
export function katanaStep(m, kl) {
  const kh = m.kh;
  if (!kh) return;
  const wrap = m.wrap, root = wrap.parent;
  wrap.updateMatrixWorld(true);
  kl = Math.max(0, Math.min(1, kl));
  for (const k of ['R', 'L']) {
    const h = kh[k];
    h.f.position.set(0, 0, h.z); h.f.rotation.set(0, 0, 0);
    if (k === 'L' && kl < 1) { // off the grip: slide it (in camera space) toward where it rests, turned a bit
      v1.set(0, 0, h.z); wrap.localToWorld(v1); root.worldToLocal(v1);
      v1.lerp(REST_L, 1 - kl); root.localToWorld(v1); wrap.worldToLocal(v1);
      h.f.position.copy(v1); h.f.rotation.set((1 - kl) * 0.9, 0, (1 - kl) * 0.6);
    }
    h.f.visible = !(k === 'L' && kl < 0.04);
    // the forearm: from the back of the fist toward that shoulder (camera space -> wrap space)
    v2.copy(k === 'R' ? SH_R : SH_L); root.localToWorld(v2); wrap.worldToLocal(v2);
    v1.copy(h.f.position);
    v3.subVectors(v2, v1); const len = v3.length() || 1; v3.divideScalar(len);
    h.a.position.copy(v1).addScaledVector(v3, 0.02 * m.cfg.s);
    h.a.quaternion.setFromUnitVectors(UP, v3);
    h.a.visible = h.f.visible;
  }
}

// ------------------------------------------------------------ the pose + animations
// kamae (weapons.js VM.katana): hilt low and right of centre, both fists on it, blade rising up and to the right, edge
// down and forward. the keys below are written as where the hilt is (camera space), which way the blade points and
// which way the edge faces; they turn into offsets from the kamae, and anim.js slerps between them.
const PB = [0.1, -0.185, -0.44], RB = [0.85, -0.7, 0.25];
export const KAT_VM = { p: PB, r: RB, s: 0.85 };
const mB = new THREE.Matrix4(), eB = new THREE.Euler(), bX = new THREE.Vector3(), bY = new THREE.Vector3(), bZ = new THREE.Vector3();
function aim(dir, edge) { // blade (-z) along dir, edge (-y) toward edge -> euler XYZ
  bZ.set(...dir).normalize().negate();
  bY.set(...edge).normalize().negate(); bY.addScaledVector(bZ, -bY.dot(bZ)).normalize();
  bX.crossVectors(bY, bZ);
  eB.setFromRotationMatrix(mB.makeBasis(bX, bY, bZ), 'XYZ');
  return [eB.x - RB[0], eB.y - RB[1], eB.z - RB[2]];
}
const KK = (t, e = 'smooth') => ({ t, p: [0, 0, 0], r: [0, 0, 0], e, s: 1 }); // the kamae itself
const KP = (t, p, dir, edge, e = 'smooth') => ({ t, p: [p[0] - PB[0], p[1] - PB[1], p[2] - PB[2]], r: aim(dir, edge), e, s: 1 });
const KATANA = {
  // kesa-giri: up over the right shoulder (it leaves the screen), the cut rips down through the middle to the lower
  // left, the weight carries it on a little, then it's hauled back up into kamae. hit 0.12 = the server's timing
  swing_katana: { hit: 0.12, keys: [
    KK(0),
    KP(0.07, [0.2, -0.09, -0.42], [0.45, 0.82, 0.35], [-0.45, 0.35, -0.82]), // wind-up: cocked over the right shoulder, edge forward
    KP(0.12, [0.06, -0.15, -0.5], [-0.55, 0.32, -0.77], [-0.5, -0.8, -0.1], 'linear'), // mid-cut, across the middle
    KP(0.17, [0, -0.2, -0.42], [-0.9, -0.14, -0.41], [-0.3, -0.6, 0.74], 'snap'), // through, out to the lower left
    KP(0.28, [-0.02, -0.215, -0.41], [-0.89, -0.2, -0.4], [-0.32, -0.55, 0.77]), // its weight carries on a touch
    KK(0.5),
  ], events: [[0.07, 'whoosh']], trail: [0.07, 0.23] },
  // gyaku: the backhand return, cocked over the left shoulder and down across to the lower right
  swing_katana2: { hit: 0.12, keys: [
    KK(0),
    KP(0.07, [-0.04, -0.08, -0.42], [-0.5, 0.8, 0.33], [0.5, 0.3, -0.81]),
    KP(0.12, [0.08, -0.15, -0.5], [0.55, 0.3, -0.78], [0.5, -0.82, -0.05], 'linear'),
    KP(0.17, [0.2, -0.2, -0.42], [0.9, -0.14, -0.41], [0.3, -0.6, 0.74], 'snap'),
    KP(0.28, [0.22, -0.215, -0.41], [0.89, -0.2, -0.4], [0.32, -0.55, 0.77]),
    KK(0.5),
  ], events: [[0.07, 'whoosh']], trail: [0.07, 0.23] },
  // iai: the right hand draws from the left hip, edge up, straight into a flat cut across (nukitsuke), the follow-through
  // hangs out right, then the left hand comes off the scabbard onto the kashira and it settles into kamae
  draw_katana: { keys: [
    KP(0, [-0.16, -0.42, -0.22], [-0.25, -0.15, -0.95], [0, 1, 0]),
    KP(0.12, [-0.1, -0.24, -0.38], [-0.7, 0.05, -0.7], [0.3, 0.6, -0.3]), // out of the saya, edge turning to lead
    KP(0.21, [0.06, -0.16, -0.47], [0.05, 0.08, -1], [1, 0, 0.05], 'linear'), // flat cut through the middle
    KP(0.29, [0.22, -0.17, -0.4], [0.85, 0.05, -0.52], [0.5, 0, 0.86], 'snap'), // follow-through, out right
    KP(0.4, [0.23, -0.18, -0.39], [0.88, 0.1, -0.45], [0.45, 0, 0.89]),
    KK(0.66), KK(0.72),
  ], ch: { kl: [[0, 0], [0.4, 0], [0.62, 1]] }, events: [[0.02, 'shing'], [0.14, 'whoosh']], trail: [0.11, 0.31] },
  // let go with the left hand, bring it across flat and look down the edge (the hamon), roll it over to the other side,
  // then chiburi: up, and a hard flick down to the right to throw the blood off, and both hands back on
  inspect_katana: { keys: [
    KK(0),
    KP(0.35, [0.07, -0.1, -0.36], [-0.9, 0.12, -0.42], [0.1, 0.85, -0.5]), // flat across, edge up, the face turned to you
    KP(0.75, [0.07, -0.095, -0.36], [-0.9, 0.14, -0.41], [0.1, 0.85, -0.5]),
    KP(0.95, [0.07, -0.095, -0.35], [-0.9, 0.14, -0.41], [0.35, 0.1, 0.93]), // rolling over, edge to you
    KP(1.15, [0.07, -0.1, -0.36], [-0.9, 0.12, -0.42], [0.1, -0.85, -0.5]), // the other face, edge down
    KP(1.5, [0.07, -0.1, -0.36], [-0.9, 0.1, -0.43], [0.1, -0.85, -0.5]),
    KP(1.7, [0.17, -0.05, -0.38], [0.3, 0.88, -0.36], [0.3, 0.3, -0.9], 'in'), // up...
    KP(1.82, [0.12, -0.16, -0.45], [0.86, -0.36, -0.36], [0.2, -0.3, 0.93], 'snap'), // ...FLICK (the blood comes off)
    KP(2.0, [0.13, -0.165, -0.45], [0.85, -0.4, -0.35], [0.2, -0.3, 0.93]),
    KK(2.4),
  ], ch: { kl: [[0, 1], [0.25, 0], [2.0, 0], [2.3, 1]] }, events: [[0.75, 'ting'], [1.7, 'whoosh'], [1.82, 'chiburi']] },
  // parry (right click): both hands snap it up across the face, edge out, tip high left; hold through the 0.35 s
  // window with a little drift so it isn't frozen; drop back. a landed parry adds hit stop + a kick on top
  parry_katana: { keys: [
    KK(0),
    KP(0.05, [0.08, -0.07, -0.4], [-0.78, 0.5, -0.38], [0.05, 0.45, -0.9], 'snap'),
    KP(0.1, [0.08, -0.09, -0.41], [-0.76, 0.48, -0.42], [0.05, 0.42, -0.9]),
    KP(0.34, [0.085, -0.095, -0.41], [-0.74, 0.46, -0.45], [0.05, 0.4, -0.9], 'linear'),
    KK(0.56),
  ], events: [[0.01, 'whoosh']], trail: [0, 0.07] },
};
for (const a of Object.values(KATANA)) { a.slerp = RB; a.dur = a.keys[a.keys.length - 1].t; }
Object.assign(ANIMS, KATANA);

// ------------------------------------------------------------ third person: the left arm reaches round to the kashira
// (2-bone IK from the left shoulder, elbow down and out). the slot holds the blade raised in a guard.
const B = new THREE.Vector3(), T = new THREE.Vector3(), E = new THREE.Vector3(), D = new THREE.Vector3(), P = new THREE.Vector3();
const UA = 0.3, LA = 0.32;
function limbBetween(o, a, b) { D.subVectors(b, a); const l = D.length() || 1; o.position.copy(a).addScaledVector(D, 0.5); o.quaternion.setFromUnitVectors(UP, D.divideScalar(l)); o.scale.set(1, l, 1); }
const KAMAE = [0.95, 0.22, 0], GUARD = [0.25, 1.45, 0.2]; // slot rotation: blade raised in front / flat across above the head
export function katanaRemote(r, on, pk = 0) {
  const ch = r.ch;
  if (!ch.armL || !ch.body) return;
  if (on) ch.slot.rotation.set(KAMAE[0] + (GUARD[0] - KAMAE[0]) * pk, KAMAE[1] + (GUARD[1] - KAMAE[1]) * pk, KAMAE[2] + (GUARD[2] - KAMAE[2]) * pk);
  else if (r.kArm && r.kArm.g.visible) ch.slot.rotation.set(0, 0, 0);
  if (!on) { if (r.kArm) { r.kArm.g.visible = false; for (const c of ch.armL.children) if (!c.userData.kat) c.visible = c.userData.kVis ?? true; r.kArm.hid = false; } return; }
  if (!r.kArm) {
    let skin = 0xe6cba2; ch.armL.traverse((o) => { if (!r.kSkin && o.isMesh && o.material && o.material.color) { r.kSkin = 1; skin = o.material.color.getHex(); } });
    const g = new THREE.Group(); g.userData.kat = true;
    const mk = (rad) => { const c = new THREE.Mesh(new THREE.CylinderGeometry(rad, rad, 1, 6), M(skin)); g.add(c); return c; };
    r.kArm = { g, up: mk(0.046), lo: mk(0.04), el: new THREE.Mesh(new THREE.SphereGeometry(0.05, 6, 4), M(skin)), fist: new THREE.Mesh(new THREE.SphereGeometry(0.048, 6, 4), M(skin)) };
    g.add(r.kArm.el, r.kArm.fist);
    ch.body.add(g);
  }
  const K = r.kArm;
  if (!K.hid) { for (const c of ch.armL.children) { c.userData.kVis = c.visible; c.visible = false; } K.hid = true; }
  K.g.visible = true;
  // the kashira end of the tsuka, in body space
  const wm = r.weaponMesh;
  if (!wm) return;
  ch.body.updateMatrixWorld(true);
  T.set(0, 0, GRIP_L); wm.localToWorld(T); ch.body.worldToLocal(T);
  ch.armL.getWorldPosition(B); ch.body.worldToLocal(B);
  D.subVectors(T, B); let d = D.length();
  const reach = UA + LA - 0.01;
  if (d > reach) { T.copy(B).addScaledVector(D.normalize(), reach); d = reach; D.subVectors(T, B); }
  // elbow: law of cosines along the shoulder->hand line, pushed down and out
  const a = (UA * UA - LA * LA + d * d) / (2 * d), h = Math.sqrt(Math.max(0, UA * UA - a * a));
  D.normalize(); P.set(-0.5, -1, 0.15).normalize(); P.addScaledVector(D, -P.dot(D)).normalize();
  E.copy(B).addScaledVector(D, a).addScaledVector(P, h);
  limbBetween(K.up, B, E); limbBetween(K.lo, E, T);
  K.el.position.copy(E); K.fist.position.copy(T);
}

// ------------------------------------------------------------ anim events (weapons.js animEvent passes on what it doesn't know)
const tipV = new THREE.Vector3();
export function katanaEvent(ev, g, sys, sfx) {
  if (ev !== 'chiburi') return false;
  sfx.swing();
  if (!sys || !g.userData.muzzle) return true;
  g.updateMatrixWorld(true);
  const gore = G.settings.blood !== false, R = (k) => (Math.random() - 0.5) * k;
  for (let i = 0; i < 16; i++) { // flung off along the blade, mostly from the last third
    tipV.copy(g.userData.muzzle).multiplyScalar(0.55 + Math.random() * 0.45); g.localToWorld(tipV);
    sys.norm.spawn(tipV.x, tipV.y, tipV.z, 0.5 + R(0.5), -0.4 + R(0.4), -0.2 + R(0.4), 0.5, 0.012 + Math.random() * 0.01, 0.006,
      gore ? 0xd8102a : 0xffffff, gore ? 0x6a0010 : 0x9adfff, 1, 3, 0.4);
  }
  return true;
}
