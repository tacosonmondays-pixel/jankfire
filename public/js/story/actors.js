// OVERDUE actors: story NPCs in the world. spawn, stand at home, walk patrol loops / schedules / scripted paths,
// turn to look at you, talk (the jaw flaps with their babble voice, a hand moves with the words), and play little
// gesture clips (wave, nod, shrug, point, cry, flex, bow, stomp, think, write). Legs come from loco.js (the same walk as
// every player), the rest is posed here. Puppets step at 12 fps (the claymation feel, ART_BIBLE §5).
import * as THREE from 'three';
import { G } from '../ctx.js';
import { BOXES } from '/shared/map.js';
import { raycast } from '/shared/physics.js';
import { locoPose } from '../loco.js';
import { buildLook, faceLocked } from './looks.js';
import { voice } from './babble.js';

export const actors = new Map();
const TAU = Math.PI * 2;
const wrapA = (a) => Math.atan2(Math.sin(a), Math.cos(a));
const lerp = (a, b, k) => a + (b - a) * k;
const ss = (t) => (t <= 0 ? 0 : t >= 1 ? 1 : t * t * (3 - 2 * t));
const bump = (t) => (t <= 0 || t >= 1 ? 0 : Math.sin(t * Math.PI));
const yawTo = (ax, az, bx, bz) => Math.atan2(-(bx - ax), -(bz - az));

// gesture clips: (a, t, k) -> poses the actor's arms/head/spine. t = seconds in, k = blend weight. len in s
// conventions (front is -z): arm / fore rotation.x + = raise forward / bend the elbow, spine.x - = bend forward,
// head.x + = look up, arm.z + (right) / - (left) = out to the side
export const CLIPS = {
  wave: { len: 1.8, f(c, t, k) { c.arm.rotation.x += 2.6 * k; c.arm.rotation.z += (0.5 + Math.sin(t * 12) * 0.35) * k; c.foreR.rotation.x += 0.5 * k; } },
  nod: { len: 0.9, f(c, t, k) { c.head.rotation.x -= Math.abs(Math.sin(t * 9)) * 0.25 * k; } },
  shake: { len: 1.0, f(c, t, k) { c.head.rotation.y += Math.sin(t * 16) * 0.35 * k; } },
  shrug: { len: 1.2, f(c, t, k) { const b = bump(t / 1.2) * k; c.arm.rotation.z += 0.45 * b; c.armL.rotation.z -= 0.45 * b; c.foreR.rotation.x += 1.3 * b; c.foreL.rotation.x += 1.3 * b; c.foreR.rotation.z += 0.6 * b; c.foreL.rotation.z -= 0.6 * b; c.head.rotation.z += 0.2 * b; c.spine.position.y += 0.03 * b; } },
  point: { len: 1.6, f(c, t, k) { c.arm.rotation.x += 1.5 * k; c.foreR.rotation.x -= 0.2 * k; } },
  cry: { len: 3, f(c, t, k) { c.armL.rotation.x += 2.3 * k; c.foreL.rotation.x += 1.7 * k; c.head.rotation.x -= (0.3 + Math.sin(t * 9) * 0.06) * k; c.spine.rotation.x -= 0.12 * k; } },
  flex: { len: 1.8, f(c, t, k) { const b = ss(t / 0.3) * k; c.arm.rotation.z += 1.45 * b; c.armL.rotation.z -= 1.45 * b; c.foreR.rotation.z += 1.9 * b; c.foreL.rotation.z -= 1.9 * b; c.spine.rotation.x += 0.08 * b; } },
  bow: { len: 1.6, f(c, t, k) { c.spine.rotation.x -= 0.7 * bump(t / 1.6) * k; } },
  stomp: { len: 0.8, f(c, t, k) { c.spine.position.y -= 0.06 * bump(t / 0.25) * k; c.arm.rotation.z += 0.4 * bump(t / 0.8) * k; c.armL.rotation.z -= 0.4 * bump(t / 0.8) * k; } },
  think: { len: 2.5, f(c, t, k) { c.arm.rotation.x += 1.0 * k; c.foreR.rotation.x += 2.2 * k; c.arm.rotation.z -= 0.3 * k; c.head.rotation.z += 0.15 * k; c.head.rotation.x += 0.12 * k; } },
  write: { len: 9e9, f(c, t, k) { c.armL.rotation.x += 0.9 * k; c.foreL.rotation.x += 1.0 * k; c.arm.rotation.x += 0.8 * k; c.foreR.rotation.x += (1.1 + Math.sin(t * 18) * 0.12) * k; c.arm.rotation.z -= 0.2 * k; c.head.rotation.x -= 0.4 * k; } },
  hold: { len: 9e9, f(c, t, k) { c.arm.rotation.x += 0.7 * k; c.armL.rotation.x += 0.7 * k; c.foreR.rotation.x += 0.9 * k; c.foreL.rotation.x += 0.9 * k; c.arm.rotation.z -= 0.1 * k; c.armL.rotation.z += 0.1 * k; } },
  shock: { len: 1.2, f(c, t, k) { const b = ss(t / 0.12) * k; c.arm.rotation.z += 0.9 * b; c.armL.rotation.z -= 0.9 * b; c.foreR.rotation.x += 1.2 * b; c.foreL.rotation.x += 1.2 * b; c.spine.rotation.x += 0.15 * b; c.head.rotation.x += 0.1 * b; } },
  // "you're late." (mina, act III): a slow look away down the street, chin down, a beat; then the head comes round to
  // you, sharp, with a little overshoot, she straightens, chin up, a tilt, and holds it (the eyes get there first: face.js)
  late: { len: 3.2, f(c, t, k) { const away = ss(t / 0.5) * (1 - ss((t - 1.1) / 0.28)), back = ss((t - 1.1) / 0.28), over = bump((t - 1.3) / 0.35) * 0.07, up = back * (1 - ss((t - 2.6) / 0.6));
    c.head.rotation.y += (-0.7 * away + over) * k; c.head.rotation.x += (-0.06 * away + 0.07 * up) * k; c.head.rotation.z += 0.08 * up * k; c.spine.rotation.x += 0.035 * up * k; c.spine.position.y += 0.008 * up * k; } },
};

// def: an npc def (shared/story content). at: [x, y, z] world (already offset by the host). face: yaw
export function spawnActor(id, def, at, face = 0) {
  despawnActor(id);
  const L = buildLook(def.look, def.hint);
  const a = {
    id, def, L, ch: L.ch, face: L.face, pos: [...at], yaw: face, home: { p: [...at], face }, voice: voice(def.voice),
    // the fake "remote" locoPose reads (it keeps its own state in r.lo)
    r: { ch: L.ch, pos: [...at], yaw: face, f: 0, gy: at[1], buf: null, w: 'npc', weaponMeshL: true, frozenUntil: 0 },
    path: null, speed: def.walk ? def.walk.speed || 1.4 : 1.4, loopI: 0, lookAt: null, lookK: 0, talking: false, clip: null, base: null,
    idle: def.idle || 'idle', t: Math.random() * 10, stepAcc: 0, puppet: L.kind === 'puppet', hidden: false,
  };
  a.r.pos = a.pos;
  if (def.walk && def.walk.loop) a.loop = def.walk.loop;
  a.dropY = dropTo(at);
  a.pos[1] = a.dropY;
  L.ch.root.position.set(...a.pos); L.ch.root.rotation.y = face;
  G.scene.add(L.ch.root);
  actors.set(id, a);
  return a;
}
export function despawnActor(id) { const a = actors.get(id); if (!a) return; G.scene.remove(a.ch.root); actors.delete(id); }
export function clearActors() { for (const id of [...actors.keys()]) despawnActor(id); }

// the floor under a spot (drops onto boxes; nothing under it = keep y)
export function dropTo(p, up = 1.5) { const h = raycast([p[0], p[1] + up, p[2]], [0, -1, 0], up + 6, BOXES); return h ? h.point[1] : p[1]; }

// commands (the scene player and quests use these)
export function walkTo(a, pts, speed, done) { a.path = pts.map((p) => [...p]); a.pathDone = done || null; if (speed) a.speedNow = speed; }
export function play(a, name, opts = {}) { if (!CLIPS[name]) return; a.clip = { name, t: 0, k: 0, len: opts.len ?? CLIPS[name].len, hold: !!opts.hold }; }
export function setFace(a, f) { if (!faceLocked(a.face)) a.face.set(f || 'neutral'); }

// world position of an actor's eyes / head (cameras aim at it)
const hv = new THREE.Vector3();
export function headPos(a, out = new THREE.Vector3()) { a.ch.head.getWorldPosition(out); out.y += 0.12 * a.ch.root.scale.y; return out; }

export function updateActors(dt, now, eye) {
  for (const a of actors.values()) updateActor(a, dt, now, eye);
}

function updateActor(a, dt, now, eye) {
  a.t += dt;
  const c = a.ch;
  // ---- moving: a scripted path first, else the patrol loop (paused while talking)
  let target = null;
  if (a.path && a.path.length) target = a.path[0];
  else if (a.loop && !a.talking && !a.hold) target = a.loop[a.loopI % a.loop.length];
  let moving = false;
  if (target) {
    const dx = target[0] - a.pos[0], dz = target[2] - a.pos[2], d = Math.hypot(dx, dz);
    if (d < 0.15) {
      if (a.path && a.path.length) { a.path.shift(); if (!a.path.length) { a.path = null; a.speedNow = 0; const f = a.pathDone; a.pathDone = null; if (f) f(a); } }
      else a.loopI++;
    } else {
      const sp = Math.min(d / dt, a.speedNow || a.speed);
      a.pos[0] += (dx / d) * sp * dt; a.pos[2] += (dz / d) * sp * dt;
      a.yaw += wrapA(yawTo(0, 0, dx, dz) - a.yaw) * Math.min(1, dt * 7);
      moving = true;
    }
    const fy = dropTo(a.pos, 0.8);
    a.pos[1] += (fy - a.pos[1]) * Math.min(1, dt * 12);
  }
  // ---- turning to whoever they talk to / you, when close and idle
  const look = a.lookAt || (eye && !moving && Math.hypot(eye[0] - a.pos[0], eye[2] - a.pos[2]) < 7 ? eye : null);
  if (!moving && (a.talking || a.faceTarget) && look) { const want = a.faceTarget != null ? a.faceTarget : yawTo(a.pos[0], a.pos[2], look[0], look[2]); a.yaw += wrapA(want - a.yaw) * Math.min(1, dt * 3.5); }
  else if (!moving && !a.loop && !a.path && !a.lookAt && a.faceTarget == null && !a.hold) a.yaw += wrapA(a.home.face - a.yaw) * Math.min(1, dt * 1.2);
  if (a.faceTarget != null && !look) a.yaw += wrapA(a.faceTarget - a.yaw) * Math.min(1, dt * 3.5);
  c.root.position.set(a.pos[0], a.pos[1], a.pos[2]);
  c.root.rotation.y = a.yaw;
  c.root.visible = !a.hidden;
  if (a.hidden) return;
  // puppets pose at 12 fps (stop-motion), everyone else every frame
  a.stepAcc += dt;
  const step = a.puppet ? 1 / 12 : 0;
  a.voice.update(dt);
  a.face.flap = a.voice.level;
  a.face.look = look ? (a.lookV ||= new THREE.Vector3()).set(look[0], look[1], look[2]) : null; // (its own vector: pose() reuses hv for the head, and the eyes went cross-eyed at their own chin)
  if (a.stepAcc < step) { a.face.update(dt); return; }
  const pdt = a.stepAcc; a.stepAcc = 0;
  a.r.yaw = a.yaw; a.r.gy = a.pos[1];
  locoPose(a.r, pdt, now);
  pose(a, pdt, moving, look);
  if (a.sit) sitPose(a);
  a.face.update(dt); // (the face already ran every frame between steps: pdt here ran its clock twice, blinks and looks jumped on the step)
}

// sitting (benches, chairs): thighs out level, shins down, hands on the knees, the hips at the seat's height
const AX = new THREE.Vector3(1, 0, 0);
export function sitActor(a, seat) {
  a.ch.root.position.set(a.pos[0], a.pos[1], a.pos[2]); a.ch.root.updateMatrixWorld(true);
  a.ch.legL.getWorldPosition(hv); // (hip height on this rig, at its scale)
  a.sit = true; a.pos = [seat[0], seat[1] - (hv.y - a.pos[1]), seat[2]]; a.r.pos = a.pos; a.home.p = a.pos.slice();
}
function sitPose(a) {
  const c = a.ch, k = 0.08 * Math.sin(a.t * 0.7); // (a jiggling knee)
  c.legL.quaternion.setFromAxisAngle(AX, 1.5 + k); c.legR.quaternion.setFromAxisAngle(AX, 1.45);
  c.kneeL.rotation.x = -1.5 - k; c.kneeR.rotation.x = -1.45;
  c.arm.rotation.x += 0.55; c.armL.rotation.x += 0.55; c.foreR.rotation.x += 0.35; c.foreL.rotation.x += 0.35;
  c.spine.rotation.x -= 0.08;
}

// arms, spine, head: rest pose + idle life + walking swing + talking + the current clip
function pose(a, dt, moving, look) {
  const c = a.ch, t = a.t, lo = a.r.lo || { ph: 0, spd: 0 };
  const sp = Math.min(1, lo.spd / 1.6);
  const sw = Math.sin(lo.ph) * 0.55 * sp;
  c.arm.rotation.set(sw + 0.05, 0, 0.1); c.armL.rotation.set(-sw + 0.05, 0, -0.1);
  c.foreR.rotation.set(0.22 + Math.max(0, sw) * 0.5, 0, 0); c.foreL.rotation.set(0.22 + Math.max(0, -sw) * 0.5, 0, 0);
  if (c.armRest) { const [ax, fx] = c.armRest; c.arm.rotation.x += ax; c.armL.rotation.x += ax; c.foreR.rotation.x += fx; c.foreL.rotation.x += fx; } // (a look whose arms can't hang: dot's rest on her wall)
  c.spine.rotation.set(c.spine.userData.hunch ??= c.spine.rotation.x, 0, 0);
  c.spine.position.y = c.spine.userData.y0 ??= c.spine.position.y;
  c.head.rotation.x = 0; c.head.rotation.y = 0; c.head.rotation.z = c.head.userData.tilt ??= c.head.rotation.z; // (z starts from the jank tilt every frame: clips that add to it, shrug, think, late, no longer wind the head round)
  // breathing (everyone), and the idle style when standing
  const br = Math.sin(t * 1.9);
  c.spine.position.y += br * 0.006; c.spine.rotation.x -= br * 0.012;
  if (!moving) {
    if (a.idle === 'sway') { c.spine.rotation.z = Math.sin(t * 0.6) * 0.05; c.head.rotation.z = Math.sin(t * 0.6 + 1) * 0.06; }
    if (a.idle === 'fidget') { const f = Math.sin(t * 0.9) > 0.6 ? 1 : 0; c.foreR.rotation.x += 1.2 * f + Math.sin(t * 20) * 0.1 * f; c.arm.rotation.x += 0.4 * f; c.head.rotation.y += Math.sin(t * 0.37) * 0.25; }
    if (a.idle === 'write' && !a.talking) CLIPS.write.f(c, t, 1);
  }
  if (c.stance) c.stance(c, t, a, moving); // (a look's own stance: mina waits with her hands clasped, or leans on her wall)
  // talking: a hand moves with the words, little nods
  if (a.talking && a.voice.level > 0.05) { const k = a.voice.level; if (c.talk) c.talk(c, t, k, a); else { c.foreR.rotation.x += 0.8 * k; c.arm.rotation.x += 0.3 * k; c.head.rotation.x += Math.sin(t * 13) * 0.04 * k; } } // (c.talk: a look's own way of talking)
  if (a.hold) CLIPS.hold.f(c, t, 1);
  // the clip on top, blended in and out
  if (a.clip) {
    const cl = a.clip, C = CLIPS[cl.name];
    cl.t += dt;
    const k = Math.min(ss(cl.t / 0.18), cl.hold ? 1 : ss((cl.len - cl.t) / 0.25));
    C.f(c, cl.t, k);
    if (!cl.hold && cl.t >= cl.len) a.clip = null;
  }
  // head looks (clamped, eased)
  if (look) {
    c.head.getWorldPosition(hv);
    const ty = Math.max(-1.0, Math.min(1.0, wrapA(yawTo(hv.x, hv.z, look[0], look[2]) - a.yaw)));
    const tx = Math.max(-0.45, Math.min(0.45, Math.atan2(look[1] - hv.y, Math.hypot(look[0] - hv.x, look[2] - hv.z))));
    a.lookY = lerp(a.lookY || 0, ty, Math.min(1, dt * 5)); a.lookX = lerp(a.lookX || 0, tx, Math.min(1, dt * 5));
  } else { a.lookY = lerp(a.lookY || 0, 0, Math.min(1, dt * 3)); a.lookX = lerp(a.lookX || 0, 0, Math.min(1, dt * 3)); }
  c.head.rotation.y += a.lookY; c.head.rotation.x += a.lookX;
}
