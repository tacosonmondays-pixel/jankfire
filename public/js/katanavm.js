// The katana, held like a katana: two fists on the tsuka (right one behind the tsuba, left one at the kashira) and
// forearms that run back to your shoulders off screen, so the hands never float. Keyframes in anim.js move the wrap as
// usual; the channel 'kl' (0..1) says how much the left hand is on the grip (an iai draw is one-handed until the left
// hand joins, the inspect lets go to turn the blade over). Third person: the left arm reaches round to the kashira.
import * as THREE from 'three';
import { makeHand, aimHand, aimCuff, mixPose, POSES } from './hands.js';
import { M } from './models.js';
import { G } from './ctx.js';
import { ANIMS } from './anim.js';

const GRIP_R = -0.083, GRIP_L = 0.085; // model z of each hand's centre (the tsuka runs -0.13 .. +0.13, blade to -z)
const TSUKA_R = 0.0138; // the tsuka's radius (model units): the fingers wrap a circle this size
const SH_R = new THREE.Vector3(0.3, -1.1, -0.12), SH_L = new THREE.Vector3(-0.2, -1.1, -0.1); // shoulders, camera space (the cuffs point at them)
const REST_L = new THREE.Vector3(-0.17, -0.42, -0.2); // where the left hand waits when it isn't on the grip
const v1 = new THREE.Vector3(), v2 = new THREE.Vector3(), UP = new THREE.Vector3(0, 1, 0);

// once per viewmodel build (weapons.js rebuildViewmodels): two PS1 hands round the tsuka, index ends toward the tsuba,
// backs of the hands up and out, fingers under the edge. a katana skin can say where its hands go: userData.grips [zR, zL]
export function katanaHands(m, hand) {
  if (hand) hand.visible = false;
  const s = m.cfg.s, gz = m.g.userData.grips || [GRIP_R, GRIP_L], kh = {};
  for (const [k, z, back] of [['R', gz[0], [0.55, 0.85, 0]], ['L', gz[1], [-0.55, 0.85, 0]]]) {
    const f = makeHand(k, { pose: 'grip', r: TSUKA_R * s, arm: [0, -0.4, 1] });
    aimHand(f, [0, 0, -1], back);
    m.wrap.add(f);
    kh[k] = { f, z: z * s, q: f.quaternion.clone() };
  }
  m.kh = kh;
  m.pivot = new THREE.Vector3(0, 0, gz[0] * s); // spins + tosses turn round the right hand (bladefeel.js)
}

// every frame, after the wrap has its pose. kl = left hand on the grip (0..1)
const OPEN_L = mixPose('grip', 'open', 1);
export function katanaStep(m, kl) {
  const kh = m.kh;
  if (!kh) return;
  const wrap = m.wrap, root = wrap.parent;
  wrap.updateMatrixWorld(true);
  kl = Math.max(0, Math.min(1, kl));
  for (const k of ['R', 'L']) {
    const h = kh[k], f = h.f;
    f.position.set(0, 0, h.z); f.quaternion.copy(h.q);
    if (k === 'L') {
      if (kl < 1) { // off the grip: slide it (in camera space) toward where it rests, opening up
        v1.set(0, 0, h.z); wrap.localToWorld(v1); root.worldToLocal(v1);
        v1.lerp(REST_L, 1 - kl); root.localToWorld(v1); wrap.worldToLocal(v1);
        f.position.copy(v1); f.rotateX((1 - kl) * 0.7);
      }
      f.userData.hand.pose = kl < 1 ? mixPose(OPEN_L, 'grip', kl) : POSES.grip;
    }
    f.visible = !(k === 'L' && kl < 0.04);
    // the cuff points back at that shoulder (off screen), so the hand reads as attached
    v2.copy(k === 'R' ? SH_R : SH_L); root.localToWorld(v2); wrap.worldToLocal(v2);
    aimCuff(f, v2);
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
    KP(0.055, [0.2, -0.08, -0.42], [0.45, 0.82, 0.35], [-0.45, 0.35, -0.82]), // cocked over the right shoulder, edge forward
    KP(0.08, [0.21, -0.075, -0.415], [0.42, 0.86, 0.3], [-0.45, 0.35, -0.82], 'linear'), // a hair of hang: then it goes
    KP(0.12, [0.06, -0.15, -0.5], [-0.55, 0.32, -0.77], [-0.5, -0.8, -0.1], 'linear'), // WHIP across the middle
    KP(0.16, [0, -0.2, -0.42], [-0.9, -0.14, -0.41], [-0.3, -0.6, 0.74], 'snap'), // through, out low left
    KP(0.26, [-0.025, -0.22, -0.41], [-0.9, -0.22, -0.38], [-0.32, -0.55, 0.77]), // the weight carries it on, the smear fades
    KK(0.5, 'back'), // and it springs back into kamae
  ], events: [[0.07, 'whoosh']], trail: [0.07, 0.25] },
  swing_katana2: { hit: 0.12, keys: [
    KK(0),
    KP(0.055, [-0.04, -0.07, -0.42], [-0.5, 0.8, 0.33], [0.5, 0.3, -0.81]),
    KP(0.08, [-0.05, -0.065, -0.415], [-0.47, 0.84, 0.28], [0.5, 0.3, -0.81], 'linear'),
    KP(0.12, [0.08, -0.15, -0.5], [0.55, 0.3, -0.78], [0.5, -0.82, -0.05], 'linear'),
    KP(0.16, [0.2, -0.2, -0.42], [0.9, -0.14, -0.41], [0.3, -0.6, 0.74], 'snap'),
    KP(0.26, [0.225, -0.22, -0.41], [0.9, -0.22, -0.38], [0.32, -0.55, 0.77]),
    KK(0.5, 'back'),
  ], events: [[0.07, 'whoosh']], trail: [0.07, 0.25] },
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
    KP(0.3, [0.15, -0.2, -0.46], [0.05, 0.95, -0.25], [1, 0, 0.15]), // left hand off, blade up at your right side, the flat to you
    KP(1.0, [0.15, -0.195, -0.46], [0.05, 0.95, -0.25], [1, 0, 0.15]), // (it twirls round the right hand, a wheel facing you: the toss channel)
    KP(1.25, [0.07, -0.1, -0.36], [-0.9, 0.12, -0.42], [0.1, 0.85, -0.5], 'back'), // caught flat across, edge up: look down the hamon
    KP(1.5, [0.07, -0.095, -0.36], [-0.9, 0.14, -0.41], [0.1, 0.85, -0.5]),
    KP(1.62, [0.07, -0.1, -0.36], [-0.9, 0.12, -0.42], [0.1, -0.85, -0.5], 'snap'), // flip it to the other face
    KP(1.74, [0.17, -0.05, -0.38], [0.3, 0.88, -0.36], [0.3, 0.3, -0.9], 'in'), // up...
    KP(1.86, [0.12, -0.16, -0.45], [0.86, -0.36, -0.36], [0.2, -0.3, 0.93], 'snap'), // ...FLICK (chiburi: the blood comes off)
    KP(2.02, [0.13, -0.165, -0.45], [0.85, -0.4, -0.35], [0.2, -0.3, 0.93]),
    KK(2.4, 'back'),
  ], ch: { kl: [[0, 1], [0.2, 0], [2.05, 0], [2.3, 1]], toss: [[0.32, 0, 0, 0, 0, 0, 0], [0.4, 0, 0, 0, 0.25, 0, 0], [0.98, 0, 0, 0, -Math.PI * 4, 0, 0]] },
  events: [[0.42, 'whoosh'], [0.62, 'whoosh'], [0.82, 'whoosh'], [1.25, 'ting'], [1.74, 'whoosh'], [1.86, 'chiburi']] },
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
