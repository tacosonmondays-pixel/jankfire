// Katana guard: what a parry looks like. weapons.js layers the first-person guard over the viewmodel every frame,
// remote.js poses everyone else (killcam ghosts too), parry.js / replay.js report what got blocked.
// the guard is a two-handed braced block: right fist on the tsuka, blade laid across the body rising to the left,
// edge out and sloped (uke-nagashi: a hit glances off the edge and slides away, it never meets the flat), left palm
// pressed on the mune. it snaps up on the press, holds for the whole window (PARRY.win) with a little life in it,
// then drops back quickly (it blocked something) or sags and recovers slowly (a whiff), so the cooldown reads.
import * as THREE from 'three';
import { PARRY } from '/shared/weapons.js';
import { G } from './ctx.js';
import { M } from './models.js';
import { fx } from './fx.js';

const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const cl01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
const out3 = (u) => 1 - (1 - u) ** 3; // fast out of the gate
const smooth = (u) => u * u * (3 - 2 * u);
const smoother = (u) => u * u * u * (u * (u * 6 - 15) + 10);
// a struck thing rings out: kicked to 1, it decays while it wobbles back through 0
const ring = (t, decay, hz) => (t < 0 ? 0 : Math.exp(-t / decay) * Math.cos(t * hz * Math.PI * 2));
// seconds: snap up, quick return after a block, a whiff's sag + slow rise
export const GUARD = { IN: 0.055, IN3: 0.07, BACK: 0.24, SAG: 0.17, RISE: 0.4 };
const WHIFF_END = GUARD.SAG + 0.05 + GUARD.RISE;

const UP = V3(0, 1, 0);
const tq = new THREE.Quaternion(), tq2 = new THREE.Quaternion(), tq3 = new THREE.Quaternion(), te3 = new THREE.Euler();
const ta = new THREE.Vector3(), tb = new THREE.Vector3(), tc = new THREE.Vector3(), td = new THREE.Vector3(), te = new THREE.Vector3(), tf = new THREE.Vector3(), tg = new THREE.Vector3();
const bx = new THREE.Vector3(), by = new THREE.Vector3(), bz = new THREE.Vector3(), bm = new THREE.Matrix4();
// a rotation that lays the katana's -z (tsuka -> tip) along d and its -y (the edge) along e, squared up to d
function bladeQ(q, d, e) {
  bz.copy(d).normalize();
  by.copy(e).addScaledVector(bz, -e.dot(bz)).normalize().negate();
  bz.negate();
  bx.crossVectors(by, bz);
  return q.setFromRotationMatrix(bm.makeBasis(bx, by, bz));
}
const turn = (v, axis, a) => (a ? v.applyQuaternion(tq3.setFromAxisAngle(axis, a)) : v); // v about a unit axis

// the blade as a straight line in g's own space, root (where katBlade starts) to tip (the muzzle), every katana skin
// and every length. lift > 0 = toward the mune, < 0 = toward the edge
function bladeLocal(g, u, lift, out) {
  const ud = g.userData, r = ud.katBlade && ud.katBlade.position, mz = ud.muzzle;
  if (!r || !mz) return out.set(0, lift, -0.14 - 0.7 * u);
  return out.set(0, r.y + (mz.y - r.y) * u + lift, r.z + (mz.z - r.z) * u);
}
const bladeLen = (g) => { const ud = g.userData; return ud.katBlade && ud.muzzle ? ud.katBlade.position.z - ud.muzzle.z : 0.7; };

// ================================================================ first person
// viewmodel space: camera at the origin looking down -z. metres (the katana viewmodel is at 0.85 scale).
// the edge faces out and a little up, which turns the flat up toward you and the light: a thin dark line otherwise.
// the fist stays right of the hotbar and the blade passes well under the crosshair; a long blade runs off the top left
export const VG = { // (exported: the pose lab tunes it live)
  grip: V3(0.19, -0.2, -0.38), dir: V3(-1, 0.46, -0.4), edge: V3(0, 0.4, -0.92), // the guard
  lowGrip: V3(0.2, -0.245, -0.4), lowDir: V3(-0.75, 0.04, -0.66), lowEdge: V3(0.25, 0.3, -0.92), // a whiff sags to here (still lit)
  brace: 0.26, // the left palm sits this far up the blade from the tsuba (m), whatever its length
  elbowL: V3(-0.25, -0.31, -0.37), elbowR: V3(0.27, -0.38, -0.23), // forearm length away, just off the bottom
};
VG.dir.normalize(); VG.lowDir.normalize();
const VM = { hits: 0, hit: null, whiff: null, arms: null, pops: [], k: 0, q: new THREE.Quaternion(), p: new THREE.Vector3(), resid: 0, rt: 0 };
export const vmGuardState = VM; // k = how far up the guard is (tests read it)
const braceU = (g) => Math.min(0.75, (VG.brace / (g.scale.x || 1)) / bladeLen(g));

let starT = null;
function starTex() {
  if (starT) return starT;
  const c = document.createElement('canvas'); c.width = c.height = 32;
  const x = c.getContext('2d'), gr = x.createRadialGradient(16, 16, 0, 16, 16, 16);
  gr.addColorStop(0, '#ffffff'); gr.addColorStop(0.25, '#fffbe0'); gr.addColorStop(0.55, '#ffcf6a'); gr.addColorStop(1, 'rgba(255,120,20,0)');
  x.fillStyle = gr; x.beginPath();
  for (let i = 0; i < 16; i++) { const a = (i / 16) * Math.PI * 2, r = i % 2 ? 4 : i % 4 ? 11 : 16; x.lineTo(16 + Math.cos(a) * r, 16 + Math.sin(a) * r); }
  x.fill();
  starT = new THREE.CanvasTexture(c);
  starT.magFilter = THREE.NearestFilter; starT.minFilter = THREE.NearestFilter;
  return starT;
}
// a white-hot star where a hit landed on the blade (viewmodel scene), gone in a blink
function vmPop(p, size, life) {
  let s = VM.pops.find((o) => o.life <= 0);
  if (!s && VM.pops.length < 4) {
    s = { spr: new THREE.Sprite(new THREE.SpriteMaterial({ map: starTex(), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, fog: false })), life: 0 };
    s.spr.renderOrder = 6; G.vmScene.add(s.spr); VM.pops.push(s);
  }
  s ||= VM.pops[0];
  s.spr.position.copy(p); s.size = size; s.life = s.ml = life; s.rot = Math.random() * 6.28; s.spr.visible = true;
}
function stepPops(dt) {
  for (const s of VM.pops) {
    if (s.life <= 0) { s.spr.visible = false; continue; }
    s.life -= dt;
    const k = Math.max(0, s.life / s.ml);
    s.spr.scale.setScalar(s.size * (0.55 + 0.75 * (1 - k * k)));
    s.spr.material.opacity = k;
    s.spr.material.rotation = s.rot + (1 - k) * 0.6;
  }
}

// the left hand (palm on the mune) and both forearms: only there while the guard is up
function vmArms() {
  if (VM.arms) return VM.arms;
  const skin = M(0xf1c27d), dark = M(0xd9a766);
  const box = (w, h, d, m, x, y, z) => { const o = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); o.position.set(x, y, z); return o; };
  // hand space: origin = middle of the palm, -z = the way the palm pushes, +y = the fingers, +x = the thumb side.
  // an open hand flat on the spine, fingers up past it (never round the edge), thumb along it
  const hand = new THREE.Group();
  hand.add(box(0.05, 0.052, 0.02, skin, 0, 0, 0)); // palm
  hand.add(box(0.05, 0.012, 0.022, dark, 0, 0.026, 0.002)); // knuckles
  for (let i = 0; i < 4; i++) { // fingers, a little apart, the long ones in the middle
    const f = box(0.0105, 0.034 + (i === 1 || i === 2 ? 0.006 : 0) - (i === 3 ? 0.006 : 0), 0.015, skin, -0.0185 + i * 0.0124, 0.05, -0.003);
    f.rotation.z = (i - 1.5) * -0.06; hand.add(f);
  }
  const th = box(0.014, 0.036, 0.015, dark, 0.03, -0.006, -0.006); th.rotation.z = -0.5; hand.add(th); // thumb, along the spine
  hand.add(box(0.044, 0.012, 0.022, dark, 0, -0.03, 0.002)); // heel of the hand
  const cyl = (r0, r1) => { const g = new THREE.CylinderGeometry(r1, r0, 1, 7); g.rotateX(Math.PI / 2); g.translate(0, 0, 0.5); return new THREE.Mesh(g, skin); };
  const foreL = cyl(0.02, 0.026), foreR = cyl(0.02, 0.026); // 1 long on +z: scaled to fit wrist -> elbow
  for (const o of [hand, foreL, foreR]) { o.visible = false; G.vmScene.add(o); }
  VM.arms = { hand, foreL, foreR };
  return VM.arms;
}
function placeFore(o, wrist, elbow) { o.position.copy(wrist); o.lookAt(elbow); o.scale.set(1, 1, wrist.distanceTo(elbow)); }

// hot sparks in the viewmodel scene from p, flying along v (camera space), some along `along` (a blade) if given.
// each one is a white-hot head with two cooler bits behind it on its path, so it reads as a streak, not a square
export function vmSparks(p, v, along, n, hot) {
  if (!G.skinFxVM) return;
  const R = (s) => (Math.random() - 0.5) * s, add = G.skinFxVM.add, sz = hot ? 0.011 : 0.009;
  for (let i = 0; i < n; i++) {
    const al = along && Math.random() < 0.3 ? (Math.random() < 0.5 ? -1 : 1) * (0.8 + Math.random() * 1.6) : 0, s = 0.9 + Math.random() * (hot ? 2.8 : 2);
    const vx = v.x * s * 0.7 + R(2) + (al ? along.x * al : 0), vy = 0.5 + Math.random() * 1.7 + (al ? along.y * al : 0), vz = v.z * s * 0.7 + R(1.2) + (al ? along.z * al : 0);
    const life = 0.1 + Math.random() * (hot ? 0.3 : 0.22);
    for (let j = 0; j < 3; j++) {
      add.spawn(p.x - vx * j * 0.006, p.y - vy * j * 0.006, p.z - vz * j * 0.006, vx, vy, vz, life * (1 - j * 0.12), sz * (1 - j * 0.25), 0.002,
        j === 0 ? 0xffffff : j === 1 ? 0xfff0a0 : 0xffa040, 0xff6a10, 1 - j * 0.2, 5, 1.2);
    }
  }
}

// a press: the guard goes up this frame. the forearms wear your sleeves (hoodie / jacket / suit), bare otherwise
export function vmGuardStart() {
  VM.hits = 0; VM.hit = null; VM.whiff = null; VM.resid = 0;
  const A = vmArms(), lk = G.settings.look || {}, long = ['hoodie', 'jacket', 'suit'].includes(lk.top);
  A.foreL.material = A.foreR.material = long ? M(new THREE.Color(lk.topColor || G.myColor || '#2a6fdb').getHex()) : M(0xf1c27d);
}

// we blocked something. m = the katana viewmodel, from = world point it came from (or null), pf = perfect,
// big = the first in a while. returns a world point on screen over where it hit (the perfect tracer starts there)
export function vmGuardHit(m, from, pf, big, now) {
  VM.hits++;
  if (!m) return null;
  const g = m.g, cam = G.camera;
  m.wrap.updateMatrixWorld(true);
  // which bit of the blade is between you and them: the point nearest (on screen) to where they are
  let sx = 0, sy = 0;
  const dirIn = V3(0, 0, -1); // toward them, camera space (= viewmodel space)
  if (from) {
    ta.set(from[0], from[1], from[2]);
    dirIn.copy(ta).sub(cam.position).normalize().applyQuaternion(tq.copy(cam.quaternion).invert());
    ta.project(cam);
    if (ta.z < 1) { sx = Math.max(-1.2, Math.min(1.2, ta.x)); sy = Math.max(-1.2, Math.min(1.2, ta.y)); }
  }
  const asp = G.vmCamera.aspect || 1.7, ub = braceU(g);
  let best = 0.5, bd = 1e9;
  for (let i = 0; i <= 24; i++) {
    const u = 0.1 + (i / 24) * 0.86;
    g.localToWorld(bladeLocal(g, u, 0, tb)).project(G.vmCamera);
    const d = ((tb.x - sx) * asp) ** 2 + (tb.y - sy) ** 2 + (Math.abs(u - ub) < 0.07 ? 0.03 : 0); // not under the left hand
    if (d < bd) { bd = d; best = u; }
  }
  const p = g.localToWorld(bladeLocal(g, best, -0.035, V3(0, 0, 0))); // on the edge: that's what faces them
  VM.hit = { t: now, pf, big, p, dirIn, stop: big ? (pf ? 0.13 : 0.09) : 0.03 };
  // sparks off the edge, back toward them and up, some skittering along the blade
  g.localToWorld(bladeLocal(g, Math.min(1, best + 0.1), -0.035, td)).sub(p).normalize();
  vmSparks(p, dirIn, td, big ? (pf ? 34 : 22) : 7, pf);
  vmPop(p, big ? (pf ? 0.11 : 0.075) : 0.04, big ? (pf ? 0.12 : 0.08) : 0.05);
  // the same spot on screen, in the world just in front of the camera
  tb.copy(p).project(G.vmCamera);
  te.set(tb.x, tb.y, 0.5).unproject(cam).sub(cam.position).normalize();
  return cam.position.clone().addScaledVector(te, 0.7).toArray();
}

// every frame, after weapons.js has posed the viewmodel: blend the guard over it. kat = the katana is what's out.
// the phases run on real time (the guard drops exactly when the window and the ring close); a hit's freeze-frame
// and recoil are layered on top
export function vmGuard(m, W, dt, now, kat) {
  const A = vmArms();
  const anim = kat && W.anim && W.anim.name === 'parry_katana' ? W.anim : null;
  const a = (now - (W.parryT || -1e9)) / 1000, P = PARRY.win;
  if (a >= P && VM.whiff == null) VM.whiff = VM.hits === 0; // decided as the window closes (a late report doesn't jerk it back up)
  const whiff = VM.whiff ?? VM.hits === 0;
  let k = 0, low = 0, hand = 0;
  if (anim) {
    if (a < P) { k = out3(cl01(a / GUARD.IN)); hand = out3(cl01((a - 0.012) / (GUARD.IN + 0.03))); }
    else if (!whiff) { const u = cl01((a - P) / GUARD.BACK); k = 1 - smoother(u); hand = 1 - smooth(cl01(u * 1.6)); }
    else { // whiff: the guard sags and the left hand lets go, then the blade comes back up, slowly
      low = smooth(cl01((a - P) / GUARD.SAG));
      k = 1 - smoother(cl01((a - P - GUARD.SAG - 0.05) / GUARD.RISE));
      hand = 1 - smooth(cl01((a - P) / 0.12));
    }
    if (a >= P + (whiff ? WHIFF_END : GUARD.BACK)) { W.anim = null; k = 0; } // all the way back: free the anim slot
  }
  // something else took over mid-guard (a slash right as the window closed): fade what's left of it out under that
  if (!anim && VM.k > 0.01) { VM.resid = kat && W.anim ? VM.k : 0; VM.rt = 0; }
  VM.k = k;
  const fist = m.wrap.userData.fist; // the right fist closes round the tsuka (it hangs under it for the other poses)
  if (fist) { fist.userData.p0 ||= fist.position.clone(); fist.position.copy(fist.userData.p0); fist.position.y += 0.04 * k; }
  if (k <= 0.001) {
    A.hand.visible = A.foreL.visible = A.foreR.visible = false;
    if (VM.resid > 0 && kat) {
      VM.rt += dt;
      const rk = VM.resid * (1 - smooth(cl01(VM.rt / 0.09)));
      if (rk <= 0.001) VM.resid = 0;
      else { m.wrap.quaternion.slerp(VM.q, rk); m.wrap.position.lerp(VM.p, rk); }
    } else VM.resid = 0;
    stepPops(dt);
    return;
  }
  // ---- the guard pose, with some life in it
  const t = Math.max(0, a), grip = ta.copy(VG.grip), dir = tb.copy(VG.dir), edge = tc.copy(VG.edge);
  if (low > 0) { grip.lerp(VG.lowGrip, low); dir.lerp(VG.lowDir, low).normalize(); edge.lerp(VG.lowEdge, low); }
  const side = td.crossVectors(dir, UP).normalize(); // horizontal, square to the blade: turning about it lifts the tip
  // a hair past the guard on the snap, settling back. holding: it presses up and out a touch, breathes, trembles
  const settle = Math.exp(-Math.max(0, t - GUARD.IN) / 0.05) * Math.sin(cl01(t / (GUARD.IN + 0.09)) * Math.PI) * 0.09;
  const hold = smooth(cl01((t - 0.08) / 0.5));
  turn(dir, side, settle + 0.035 * hold + Math.sin(t * 9.4) * 0.006 + Math.sin(t * 23) * 0.0015);
  turn(dir, UP, Math.sin(t * 6.1 + 1) * 0.008);
  grip.x += Math.sin(t * 7.3) * 0.0015; grip.y += Math.sin(t * 8.6 + 2) * 0.002 - 0.004 * hold; grip.z -= 0.012 * hold;
  // a block: the hit shoves the blade back at you, it shudders there through the hit stop, then springs back
  const H = VM.hit;
  if (H) {
    const ht = (now - H.t) / 1000, after = ht - H.stop, mag = H.big ? (H.pf ? 1.25 : 1) : 0.4;
    const shove = (after < 0 ? 1 : ring(after, 0.07, 7)) * mag;
    const shake = after < 0 ? Math.sin(ht * 260) * 0.006 * mag : 0;
    const lever = tf.copy(H.p).sub(VG.grip), len = Math.max(0.15, lever.length());
    const ax = te.crossVectors(lever, H.dirIn).normalize(); // turning about it swings the blade at them (+) or back at you (-)
    turn(dir, ax, -(0.05 / len) * shove + shake); turn(edge, ax, -(0.05 / len) * shove);
    grip.addScaledVector(H.dirIn, -0.018 * shove); grip.y -= 0.006 * shove;
    if (H.pf && after > 0) { // perfect: flick the blade out at them (it sends the bullet home), then back into the guard
      const f = after < 0.06 ? out3(after / 0.06) : after < 0.1 ? 1 : 1 - smooth(cl01((after - 0.1) / 0.2));
      turn(dir, ax, 0.42 * f); turn(edge, ax, 0.3 * f);
      grip.addScaledVector(H.dirIn, 0.05 * f);
    }
    if (ht > 1.2) VM.hit = null;
  }
  // it lags behind your view like the gun does, a bit steadier (two hands on it)
  tq2.setFromEuler(te3.set(-W.swayY * 0.5, W.swayX * 0.75, W.swayX * 0.3));
  grip.applyQuaternion(tq2); dir.applyQuaternion(tq2); edge.applyQuaternion(tq2);
  bladeQ(tq, dir, edge);
  m.wrap.position.lerp(grip, k); // grip = where the tsuka sits (the wrap's origin)
  m.wrap.quaternion.slerp(tq, k);
  VM.q.copy(m.wrap.quaternion); VM.p.copy(m.wrap.position);
  // ---- the left hand on the spine + both forearms
  m.wrap.updateMatrixWorld(true);
  const g = m.g, u = braceU(g);
  const brace = g.localToWorld(bladeLocal(g, u, 0.014, te));
  const along = g.localToWorld(bladeLocal(g, Math.min(1, u + 0.1), 0.014, tf)).sub(brace).normalize();
  const push = tg.set(0, -1, 0).transformDirection(g.matrixWorld); // the palm pushes the way the edge faces
  const fingers = ta.copy(UP).addScaledVector(push, -push.y); // fingers as near straight up as the palm allows
  if (fingers.lengthSq() < 0.01) fingers.crossVectors(push, along);
  fingers.normalize();
  by.copy(push).negate();
  bm.makeBasis(bx.crossVectors(fingers, by).normalize(), fingers, by);
  A.hand.quaternion.setFromRotationMatrix(bm);
  // it comes up from below and slaps onto the spine a beat after the blade lands; lets go first on the way down
  const hk = hand * k;
  A.hand.position.copy(brace).addScaledVector(push, -0.016).lerp(VG.elbowL, 1 - hk);
  A.hand.visible = A.foreL.visible = hk > 0.02;
  if (A.hand.visible) placeFore(A.foreL, tf.copy(A.hand.position).addScaledVector(fingers, -0.04).addScaledVector(push, 0.006), VG.elbowL);
  A.foreR.visible = k > 0.15; // from the fist down to the bottom right corner
  if (A.foreR.visible) placeFore(A.foreR, m.wrap.localToWorld(fist ? tf.copy(fist.position).add(tg.set(0.002, 0.01, 0.03)) : tf.set(0.006, -0.03, 0.05)), tc.copy(VG.elbowR).lerp(VG.grip, 0.15));
  stepPops(dt);
}

// ================================================================ third person
// mannequin body space (faces -z, right = +x, before the 1.2 player scale). the right arm is one straight stick from
// the shoulder, so the guard is a direction for it. the left arm is rigid too: the palm goes where the blade passes
// at its reach
export const TG = { // (exported for the pose tests)
  arm: V3(-0.06, -0.2, -1), dir: V3(-1, 0.42, -0.16), edge: V3(0, 0.3, -1), // the guard: rising to their left, edge out
  lowArm: V3(0.08, -0.78, -0.62), lowDir: V3(-0.55, -0.62, -0.56), lowEdge: V3(0, -0.6, -0.8), // a whiff sags here
  stArm: V3(0.55, 0.62, -0.5), stL: V3(-0.85, 0.15, -0.45), // staggered: weapon flung up and out, left arm thrown wide
};
for (const v of Object.values(TG)) v.normalize();
const HANDL = V3(0.3875, -0.04, -0.4932); // the end of the left forearm from the shoulder (models.js buildCharacter)
const HANDL_N = HANDL.clone().normalize(), REACH_L = HANDL.length();
const qa = new THREE.Quaternion(), qb = new THREE.Quaternion(), qc = new THREE.Quaternion(), qd = new THREE.Quaternion();
const pa = new THREE.Vector3(), pb = new THREE.Vector3(), pc = new THREE.Vector3(), pd = new THREE.Vector3(), pe = new THREE.Vector3(), pf3 = new THREE.Vector3();

function gd(r) {
  const S = r.gd || (r.gd = { t0: null, hits: 0, hit: null, whiff: null, k: 0, on: false, stg: null, star: null });
  if (S.t0 !== r.parryT) { S.t0 = r.parryT; S.hits = 0; S.hit = null; S.whiff = null; } // a new guard went up
  return S;
}

// the pose. t = this remote's clock in ms (performance.now(), or the replay's for killcam ghosts)
export function guardPose(r, ch, t) {
  const S = gd(r), P = PARRY.win;
  const a = (t - (r.parryT ?? -1e9)) / 1000;
  if (a >= P && S.whiff == null) S.whiff = S.hits === 0;
  const whiff = S.whiff ?? S.hits === 0;
  let k = 0, low = 0, hand = 0;
  if (r.w === 'katana' && r.weaponMesh && a >= 0) {
    if (a < P) { k = out3(cl01(a / GUARD.IN3)); hand = out3(cl01((a - 0.02) / 0.09)); }
    else if (!whiff) { const u = cl01((a - P) / GUARD.BACK); k = 1 - smoother(u); hand = 1 - smooth(cl01(u * 1.6)); }
    else { low = smooth(cl01((a - P) / GUARD.SAG)); k = 1 - smoother(cl01((a - P - GUARD.SAG - 0.05) / GUARD.RISE)); hand = 1 - smooth(cl01((a - P) / 0.12)); }
  }
  S.k = k;
  const stg = staggerK(S, t);
  if (k <= 0.001 && stg <= 0.001) {
    if (S.on) { S.on = false; ch.slot.rotation.set(0, 0, 0); ch.arm.rotation.z = 0; ch.armL.rotation.y = 0; ch.body.rotation.y = 0; }
    return;
  }
  S.on = true;
  ch.arm.rotation.z = 0; ch.armL.rotation.y = 0; // nothing else sets these: start from the plain pose
  qa.copy(ch.arm.quaternion); qb.copy(ch.armL.quaternion);
  if (k > 0.001) guardArms(r, ch, S, Math.max(0, a), k, low, hand, t);
  else ch.slot.rotation.set(0, 0, 0);
  if (stg > 0.001) staggerArms(ch, S, stg, t);
  else ch.body.rotation.y = 0;
  glint(r, S, a);
}

function guardArms(r, ch, S, a, k, low, hand, t) {
  const g = r.weaponMesh, sc = g.scale.x || 1.5;
  const u = pa.copy(TG.arm), dir = pb.copy(TG.dir), edge = pc.copy(TG.edge);
  if (low > 0) { u.lerp(TG.lowArm, low).normalize(); dir.lerp(TG.lowDir, low).normalize(); edge.lerp(TG.lowEdge, low); }
  const side = pd.crossVectors(dir, UP).normalize(), lift = pf3.crossVectors(u, UP).normalize();
  const settle = Math.exp(-Math.max(0, a - GUARD.IN3) / 0.06) * Math.sin(cl01(a / 0.17) * Math.PI) * 0.12;
  turn(dir, side, settle + Math.sin(a * 8.2) * 0.01);
  turn(u, UP, Math.sin(a * 5.3 + 1) * 0.012);
  // a block: the blade's driven back toward them, the arms jolt up, then it springs back. perfect: a flick out at them
  const H = S.hit;
  if (H) {
    const ht = (t - H.t) / 1000, after = ht - H.stop, mag = H.big ? (H.pf ? 1.2 : 1) : 0.45;
    const shove = (after < 0 ? 1 : ring(after, 0.08, 6)) * mag;
    turn(dir, UP, 0.24 * shove); turn(edge, UP, 0.24 * shove); turn(u, lift, 0.12 * shove);
    if (H.pf && after > 0 && H.at) {
      const f = after < 0.07 ? out3(after / 0.07) : after < 0.12 ? 1 : 1 - smooth(cl01((after - 0.12) / 0.22));
      const ax = pe.crossVectors(dir, H.at).normalize();
      turn(dir, ax, 0.55 * f); turn(edge, ax, 0.4 * f); turn(u, ax, 0.22 * f);
    }
    if (ht > 1.2) S.hit = null;
  }
  // right arm: point the slot (where the hand holds things) along u
  qc.setFromUnitVectors(pe.copy(ch.slot.position).normalize(), u);
  ch.arm.quaternion.copy(qa).slerp(qc, k);
  // the katana's own turn: the blade pose, minus what the (full) guard arm already does
  bladeQ(qd, dir, edge);
  qc.invert().multiply(qd);
  ch.slot.quaternion.identity().slerp(qc, k);
  // left arm: the palm on the spine, where the blade passes at its reach
  ch.arm.updateMatrix(); ch.slot.updateMatrix(); g.updateMatrix();
  bm.copy(ch.arm.matrix).multiply(ch.slot.matrix).multiply(g.matrix); // g -> body
  const b0 = bladeLocal(g, 0, 0.03, tc).applyMatrix4(bm), b1 = bladeLocal(g, 1, 0.03, td).applyMatrix4(bm);
  const bd = te.copy(b1).sub(b0), bl = bd.length() || 1;
  bd.divideScalar(bl);
  const rel = tf.copy(b0).sub(ch.armL.position);
  const B = rel.dot(bd), C = rel.lengthSq() - REACH_L * REACH_L, disc = B * B - C; // |rel + s bd| = reach: the far root
  let s = disc >= 0 ? -B + Math.sqrt(disc) : -B;
  s = Math.max(0.08 * sc, Math.min(Math.min(bl * 0.7, 0.75 * sc * bladeLen(g) / (g.userData.katBlade ? g.userData.katBlade.scale.z : 1)), s));
  qc.setFromUnitVectors(HANDL_N, rel.addScaledVector(bd, s).normalize());
  ch.armL.quaternion.copy(qb).slerp(qc, k * hand);
}

// staggered (their swing got parried): weapon knocked up and out, wrist bent back, other arm thrown wide, head back
function staggerK(S, t) {
  const st = S.stg;
  if (!st) return 0;
  const a = (t - st.t) / 1000;
  if (a > st.dur) { S.stg = null; return 0; }
  if (a < 0) return 0;
  return out3(cl01(a / 0.06)) * (1 - smooth(cl01((a - st.dur + 0.28) / 0.28)));
}
function staggerArms(ch, S, k, t) {
  const a = (t - S.stg.t) / 1000, wob = ring(a, 0.12, 4.5) * 0.25, sd = S.stg.side;
  const u = pa.copy(TG.stArm); u.x *= sd; turn(u.normalize(), UP, wob * 0.6);
  qc.setFromUnitVectors(pe.copy(ch.slot.position).normalize(), u);
  ch.arm.quaternion.slerp(qc, k);
  qd.setFromEuler(te3.set(0.9 + wob, 0, 0.45 * sd));
  ch.slot.quaternion.slerp(qd, k);
  const l = turn(pb.copy(TG.stL), UP, -wob);
  qc.setFromUnitVectors(HANDL_N, l.normalize());
  ch.armL.quaternion.slerp(qc, k * 0.85);
  ch.head.rotation.x += 0.45 * k; ch.head.rotation.z += 0.2 * k * sd;
  ch.body.rotation.y = -0.38 * k * sd * (1 + wob);
}

// the blade catches the light as the guard lands: a star runs up it, root to tip (it reads from across the map).
// a sprite on the weapon itself, so it rides the blade instead of hanging where the blade was
function glint(r, S, a) {
  const u = (a - 0.05) / 0.16, g = r.weaponMesh;
  if (!(u > 0 && u < 1) || !g || r.w !== 'katana') { if (S.star) S.star.visible = false; return; }
  if (!S.star || S.star.parent !== g) {
    S.star ||= new THREE.Sprite(new THREE.SpriteMaterial({ map: starTex(), color: 0xe8fbff, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, fog: false }));
    g.add(S.star);
  }
  bladeLocal(g, 0.08 + 0.92 * smooth(u), 0.006, S.star.position);
  S.star.scale.setScalar(0.07 + 0.11 * Math.sin(u * Math.PI));
  S.star.material.rotation = u * 2.5;
  S.star.visible = true;
}

// world point on r's blade nearest the line a hit came in on (from -> their chest), on the edge side
export function bladeHitPoint(r, from) {
  const g = r.weaponMesh;
  if (!g || r.w !== 'katana') return null;
  r.ch.root.updateMatrixWorld(true);
  const b0 = g.localToWorld(bladeLocal(g, 0.06, -0.02, pa)), b1 = g.localToWorld(bladeLocal(g, 0.97, -0.02, pb));
  const chest = pc.set(r.pos[0], r.pos[1] + 1.55 * (r.distScale || 1), r.pos[2]);
  const f = from ? pd.set(from[0], from[1], from[2]) : pd.set(-Math.sin(r.yaw), 0, -Math.cos(r.yaw)).add(chest);
  const u = pe.copy(b1).sub(b0), v = tc.copy(chest).sub(f), w0 = td.copy(b0).sub(f); // segment b0 + s u vs line f + q v
  const A = u.dot(u), B = u.dot(v), C = v.dot(v), D = u.dot(w0), E = v.dot(w0), den = A * C - B * B;
  const s = Math.max(0, Math.min(1, den > 1e-9 ? (B * E - C * D) / den : 0.5));
  return b0.addScaledVector(u, s).toArray();
}

// something hit r's guard. m = the 'parry' message, t = r's clock (ms), from = world point it came from (or null).
// sparks fly off the real contact point; returns it (a perfect-parried bullet's tracer leaves from there)
export function guardHit(r, m, t, big, from) {
  const S = gd(r), pf = !!m.pf;
  S.hits++;
  const at = from ? V3(from[0] - r.pos[0], 0, from[2] - r.pos[2]).applyAxisAngle(UP, -r.yaw).normalize() : null; // body space
  S.hit = { t, pf, big, stop: big ? (pf ? 0.11 : 0.075) : 0.03, at };
  const p = (m.k === 'proj' ? bladeHitPoint(r, m.p) : bladeHitPoint(r, from)) || m.p;
  let dir = null;
  if (from) { const dx = from[0] - r.pos[0], dz = from[2] - r.pos[2], l = Math.hypot(dx, dz) || 1; dir = [dx / l, 0, dz / l]; }
  fx.sparks(p, dir, big ? (pf ? 40 : 26) : 8, pf);
  return p;
}

// their swing got parried: the stagger pose for st seconds (side = which way their weapon flies)
export function guardStagger(r, t, st) { gd(r).stg = { t, dur: Math.max(0.3, st || PARRY.stagger), side: Math.random() < 0.5 ? -1 : 1 }; }
// where a hit came from (world): the shooter's eye, the swinger's chest, the batted-back projectile.
// find(id) = their Remote (or killcam ghost); me = your own eye, when it was you
export function hitFrom(m, find, me) {
  if (m.k === 'proj') return m.p;
  if (me) return m.k === 'shot' ? me : [me[0], me[1] - 0.35, me[2]];
  const a = find(m.by);
  return a && a.buf && a.buf.length ? [a.pos[0], a.pos[1] + (m.k === 'shot' ? 1.6 : 1.25), a.pos[2]] : null;
}
// where a remote's weapon is (the clash sparks): most of the way to its tip
export function weaponPoint(r) {
  const g = r.weaponMesh;
  if (!g || !g.userData.muzzle) return null;
  r.ch.root.updateMatrixWorld(true);
  return g.localToWorld(pa.copy(g.userData.muzzle).multiplyScalar(0.75)).toArray();
}
