// OVERDUE camera control: the talk cam and the scene player ask for a shot, this blends the game camera into it and
// back out ("gameplay starts where the scene ends": the last shot eases back into the player's own view).
// shot: { pos: Vector3, look: Vector3, fov, roll, cut (no blend), blend (s) }. take(cam, dt) runs after main.js has
// placed the player camera, so leaving the shot always lands on the real view.
import * as THREE from 'three';

const C = { shot: null, k: 0, from: null, blend: 0.6, smPos: new THREE.Vector3(), smLook: new THREE.Vector3(), has: false };
const m4 = new THREE.Matrix4(), qShot = new THREE.Quaternion(), qGame = new THREE.Quaternion(), up = new THREE.Vector3(0, 1, 0), qRoll = new THREE.Quaternion(), Z = new THREE.Vector3(0, 0, 1);
const ss = (t) => t * t * (3 - 2 * t);

export function wantShot(shot) {
  if (shot && shot.cut) { C.k = 1; C.has = false; }
  C.shot = shot; if (shot && shot.blend != null) C.blend = shot.blend; else if (shot) C.blend = 0.6;
}
export const shotOn = () => !!C.shot || C.k > 0.001;

export function takeCamera(cam, dt) {
  const target = C.shot ? 1 : 0;
  const rate = dt / Math.max(0.05, C.shot ? C.blend : 0.55);
  C.k = target > C.k ? Math.min(1, C.k + rate) : Math.max(0, C.k - rate);
  if (C.k <= 0.0001 && !C.shot) { C.has = false; return false; }
  const s = C.shot || C.last;
  if (!s) return false;
  C.last = s;
  // the shot eases a little itself (so presets that follow a moving actor don't jitter), unless it was a cut
  const sk = C.has && !s.cut ? Math.min(1, dt * (s.follow ?? 8)) : 1;
  C.smPos.lerp(s.pos, sk); C.smLook.lerp(s.look, sk);
  if (!C.has || sk === 1) { C.smPos.copy(s.pos); C.smLook.copy(s.look); }
  C.has = true; s.cut = false;
  m4.lookAt(C.smPos, C.smLook, up); qShot.setFromRotationMatrix(m4);
  if (s.roll) qShot.multiply(qRoll.setFromAxisAngle(Z, s.roll));
  const k = ss(C.k);
  qGame.copy(cam.quaternion);
  cam.position.lerp(C.smPos, k);
  cam.quaternion.copy(qGame).slerp(qShot, k);
  const fov = cam.fov + ((s.fov || 50) - cam.fov) * k;
  if (Math.abs(cam.fov - fov) > 0.01) { cam.fov = fov; cam.updateProjectionMatrix(); }
  cam.updateMatrixWorld();
  return k > 0.5;
}
