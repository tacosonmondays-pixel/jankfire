// Overdrive Rig killstreak, the client: you in the rig (heavy fast movement, the rocket punch dash, block, quickhack,
// missiles, the charged leap, camera feel, the HUD panel, the overdrive trail + screen tint, the hum), everyone else in
// theirs (Remote.update and the replay ghosts call rigRemote), and the server's rig events. The server judges every hit
// (server/rig.js); what the client does with a hit is only how it looks and sounds.
import * as THREE from 'three';
import { BOXES } from '/shared/map.js';
import { raycast, movePlayer } from '/shared/physics.js';
import { FLAGS } from '/shared/weapons.js';
import { RIG, dashDir, leapVel, punchDist, rigBoxes, thrustVel, useThrust, thrustCharges } from '/shared/rig.js';
import { G } from './ctx.js';
import { ME, eye, look, hspeed, releaseHook } from './player.js';
import { W, punchCam, isFriend } from './weapons.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { fx } from './fx.js';
import { recordEv } from './replay.js';
import { buildRig, poseRig, freeRig, setRigColor, rigGhost, updateGhosts, hideGhosts, rfx, rmesh, rigBurst, rigHex } from './rigmodel.js';
import { armsReady, armsOn, armsOff, armsHide, playArms, armsStep, armsJolt, updateArms } from './rigarms.js';
import { rigsfx, rigHum } from './rigsfx.js';

export { rigBoxes };
const P = RIG.punch, L = RIG.leap, M = RIG.miss, H = RIG.hack;
const r2 = (x) => Math.round(x * 100) / 100;
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const $ = (id) => document.getElementById(id);
const S = G.settings;

// ------------------------------------------------------------ you, in the rig
export const RS = {
  on: false, until: 0, dur: 25000, shield: RIG.shield, store: 0, model: null, startT: 0,
  lmb: false, charging: false, chargeT0: 0, charge: 0, punchCd: 0, dashT: 0, dashDir: [0, 0, -1], dashHit: new Set(), punchC: 0, punchT: 0,
  hackCd: 0, missCd: 0, hackT: 0, missT: 0, leapCd: 0, leapCharging: false, leapT0: 0, leapK: 0, leapAir: false, landT: 9, landK: 0,
  airMin: 0, stepPhase: 0, stepSide: 1, dip: 0, hitStop: 0, tint: 0, ghostT: 0, ghostN: 0, lastYaw: 0, lastPitch: 0, swayX: 0, swayY: 0,
  shieldFlash: 0, blockFlash: 0, fov: 0, thr: { n: RIG.thrust.n, next: 0, t: 0 }, thrT: 0,
};
export const rigOn = (now = performance.now()) => RS.on && ME.alive && now < RS.until;

function startLocal(dur, sh) {
  const now = performance.now();
  if (!RS.on) RS.startT = now;
  Object.assign(RS, { on: true, until: now + dur, dur, shield: sh, store: 0, lmb: false, charging: false, charge: 0, dashT: 0, punchCd: now + 500,
    hackCd: 0, missCd: 0, hackT: 0, missT: 0, leapCd: now + 400, leapCharging: false, leapK: 0, leapAir: false, airMin: 0, hitStop: 0, thr: { n: RIG.thrust.n, next: 0, t: 0 }, thrT: 0 });
  releaseHook();
  W.held = false; W.aimHeld = false; W.dashHeld = false; W.charge = 0; W.exhale = 0; W.aim = 0; W.zoom = 1; W.scoped = false;
  ME.dashing = false; ME.sliding = false;
  hud.scope(false); hud.ammo(null); hud.meter(null); hud.cards(null);
  if (!RS.model) RS.model = buildRig(G.myColor);
  else setRigColor(RS.model, G.myColor);
  RS.model.root.scale.setScalar(1.2);
  RS.model.onStep = null;
  document.body.classList.add('rigging');
  armsOn();
  rigsfx.on(null);
  G.shake = Math.max(G.shake, 0.7);
  punchCam(-0.05, 0, 0.02);
  hud.msg('OVERDRIVE ONLINE', 1.6, 'brag');
  hud.chat(null, null, 'overdrive rig: hold LMB to charge a rocket punch · hold RMB to block (it charges the punch) · Space jumps way up (hold to leap) · E thrusters (in the air too) · G missiles · R quickhack');
  panel(true);
}
function endLocal(why) {
  if (!RS.on) return;
  RS.on = false;
  const dead = why === 'dead';
  RS.charging = false; RS.dashT = 0; RS.leapCharging = false; ME.dashing = false;
  W.held = false; W.aimHeld = false; W.zoom = 1; W.swap = 1; // the gun comes back up
  document.body.classList.remove('rigging');
  panel(false); tint(0, true); rigHum({ on: false });
  if (RS.model) {
    hideGhosts(RS.model);
    if (dead) { placeModel(); rigBurst(RS.model, ME.vel); rigsfx.burst(null); }
    RS.model.root.removeFromParent();
  }
  if (dead || why === 'quit') armsHide();
  else { armsOff(); rigsfx.off(null); rfx.smoke([ME.pos[0], ME.pos[1] + 1.6, ME.pos[2]], 16, 0xd8dde2, 0.9, 1.5, 1.4, 0.8); hud.msg('OVERDRIVE OFFLINE', 1.2); }
}
// the model that follows you (nobody draws it but your afterimages, the intro shot and the scrap when you die)
function placeModel() {
  const m = RS.model.root;
  m.position.set(ME.pos[0], ME.pos[1], ME.pos[2]);
  m.rotation.set(0, ME.yaw, 0);
  m.updateMatrixWorld(true);
}

// ------------------------------------------------------------ input hooks (weapons.js / player.js call these)
// LMB: hold to charge the rocket punch, let go to throw it. returns true while the rig has your hands
export function rigFire(down) {
  const now = performance.now();
  if (!rigOn(now)) return false;
  RS.lmb = down;
  if (down) { if (!W.aimHeld) startCharge(now); }
  else if (RS.charging) releasePunch(now);
  return true;
}
function startCharge(now) {
  if (RS.charging || RS.dashT > 0) return;
  RS.charging = true;
  RS.chargeT0 = Math.max(now, RS.punchCd - 100);
  rigsfx.servo(null, 0.8);
}
function releasePunch(now) {
  RS.charging = false;
  if (now < RS.punchCd) { rigsfx.denied(); return; }
  const c = RS.charge, d = look();
  RS.store = 0; RS.charge = 0;
  net.send({ t: 'rig', k: 'punch', c: r2(c), d: d.map(r2) });
  RS.dashDir = dashDir(d); RS.dashT = punchDist(c) / P.speed; RS.punchC = c; RS.dashHit.clear(); RS.punchCd = now + P.cd * 1000; RS.punchT = now;
  ME.dashing = true;
  playArms('rig_punch');
  rigsfx.release(null, c);
  punchCam(0.012 + c * 0.03, 0, 0.02 * (Math.random() - 0.5));
  G.shake = Math.max(G.shake, 0.25 + c * 0.45);
  RS.fov = 1;
}
// E (or whatever grapples): the thrusters in the rig; a fried grapple when you've been hacked
export function rigHook(now = performance.now()) {
  if (rigOn(now)) { tryThrust(now); return true; }
  if (now < (ME.hackedUntil || 0)) { hud.msg(`GRAPPLE FRIED · ${((ME.hackedUntil - now) / 1000).toFixed(1)}s`, 0.7, 'slip'); rigsfx.denied(); return true; }
  return false;
}
// R (reload: no gun to reload in the rig): the quickhack
export function rigReload() { const now = performance.now(); if (!rigOn(now)) return false; tryHack(now); return true; }
// thrusters: a burst of lift from the back jets and the boots, in the air too. 3 charges, one back every 2.6 s (the
// server counts them too: it only shows everyone a burst it believes)
function tryThrust(now) {
  if (thrustCharges(RS.thr, now) < 1) { hud.msg(`THRUSTERS ${(Math.max(0, RS.thr.next - now) / 1000).toFixed(1)}s`, 0.6); rigsfx.denied(); return; }
  if (!useThrust(RS.thr, now)) return;
  if (RS.leapCharging) { RS.leapCharging = false; RS.leapK = 0; } // (a thrust off the floor cancels a wind-up)
  thrustVel(ME.vel, look());
  ME.onGround = false; ME.pos[1] += 0.02; RS.airMin = Math.min(0, RS.airMin * 0.3); RS.thrT = now;
  net.send({ t: 'rig', k: 'thrust' });
  rigsfx.thrust(null, 1);
  playArms('rig_miss', 0.8); // (the rack kicks on your back)
  G.shake = Math.max(G.shake, 0.3); punchCam(0.02, 0, 0); RS.fov = Math.max(RS.fov, 0.5);
  jetFx(ME.pos, ME.yaw);
}
// jet flame + smoke out of the boots and the back, pointing down
function jetFx(p, yaw) {
  const s = Math.sin(yaw), c = Math.cos(yaw);
  for (const [x, z, y] of [[0.3, 0, 0], [-0.3, 0, 0], [0.35, 0.45, 1.9], [-0.35, 0.45, 1.9]]) {
    const at = [p[0] + c * x + s * z, p[1] + y, p[2] - s * x + c * z];
    rfx.sparks(at, 10, 7, [0xffffff, 0xffd060, 0xff7ae8, 0xff4a20], 0.35, 0.1, [0, -1, 0]);
    rfx.smoke(at, 4, 0xbfc4ca, 0.7, 0.9, 1.1, 0.5);
  }
}
function tryHack(now) {
  if (now < RS.hackCd) { hud.msg(`QUICKHACK ${((RS.hackCd - now) / 1000).toFixed(1)}s`, 0.6); rigsfx.denied(); return; }
  const o = eye(), d = look();
  let best = null, bc = 0.97;
  for (const r of G.remotes.values()) {
    if (!r.alive || isFriend(r)) continue;
    const c = [r.pos[0], r.pos[1] + 1.2, r.pos[2]], v = [c[0] - o[0], c[1] - o[1], c[2] - o[2]], l = Math.hypot(v[0], v[1], v[2]);
    if (l > H.range || l < 0.5) continue;
    const cos = (v[0] * d[0] + v[1] * d[1] + v[2] * d[2]) / l;
    if (cos < bc || raycast(o, [v[0] / l, v[1] / l, v[2] / l], l - 0.5, BOXES)) continue;
    bc = cos; best = { r, c };
  }
  if (!best) { hud.msg('QUICKHACK: NO TARGET IN SIGHT', 0.8); rigsfx.denied(); return; }
  RS.hackCd = now + H.cd * 1000; RS.hackT = now;
  net.send({ t: 'rig', k: 'hack', to: best.r.id });
  playArms('rig_hack');
  rigsfx.hack(null);
}
// G: the missile salvo
export function rigItem() {
  const now = performance.now();
  if (!rigOn(now)) return false;
  if (now < RS.missCd) { hud.msg(`MISSILES ${((RS.missCd - now) / 1000).toFixed(1)}s`, 0.6); rigsfx.denied(); return true; }
  RS.missCd = now + M.cd * 1000; RS.missT = now;
  net.send({ t: 'rig', k: 'miss', d: look().map(r2) });
  playArms('rig_miss');
  rigsfx.missiles(null);
  punchCam(-0.02, 0, 0); G.shake = Math.max(G.shake, 0.35);
  hud.msg('MISSILES AWAY', 0.9, 'brag');
  return true;
}
// right click in the rig is the block (it holds W.aimHeld like aiming does): not the knife stab, not the card picker
export const rigBlockKey = () => rigOn();

// ------------------------------------------------------------ movement (player.js stepPlayer hands the step over)
// much faster than on foot, and heavy: it takes a moment to get going, slides to a stop, turns its momentum round,
// falls hard. Space charges a leap instead of jumping (a tap is a hop). no grapple, no bhop, no slides
export function rigStep(dt, inp, now) {
  if (!RS.on || !ME.alive) return false;
  if (now >= RS.until) { endLocal('time'); return false; }
  const v = ME.vel, p = ME.pos;
  ME.hook = null; ME.sliding = false;
  if (RS.hitStop > 0) { RS.hitStop -= dt; return true; } // the punch connected: you hang there for a beat
  if (RS.dashT > 0) { dashStep(dt, now); return true; }
  const fw = (inp.f ? 1 : 0) - (inp.b ? 1 : 0), st = (inp.r ? 1 : 0) - (inp.l ? 1 : 0);
  const s = Math.sin(ME.yaw), c = Math.cos(ME.yaw);
  let wx = -s * fw + c * st, wz = -c * fw - s * st;
  const wl = Math.hypot(wx, wz);
  if (wl) { wx /= wl; wz /= wl; }
  const crouch = !!inp.crouch;
  ME.crouching = crouch && ME.onGround;
  ME.sprinting = !!inp.sprint && fw > 0 && ME.onGround && !crouch;
  let top = RIG.speed * (ME.sprinting ? RIG.sprint : 1);
  if (W.aimHeld) top *= RIG.block.slow;
  if (RS.charging) top *= 0.75;
  if (RS.leapCharging) top *= 0.3;
  if (crouch) top *= 0.5;
  const hs = Math.hypot(v[0], v[2]);
  if (ME.onGround) {
    if (hs > 0) { const ns = Math.max(0, hs - Math.max(hs, 3) * RIG.fric * (wl ? 0.45 : 1) * dt) / hs; v[0] *= ns; v[2] *= ns; }
    if (wl) {
      const h2 = Math.hypot(v[0], v[2]);
      if (h2 > 2) { // the momentum swings round toward where you push (heavy, not on rails)
        const cur = Math.atan2(v[0], v[2]);
        let da = Math.atan2(wx, wz) - cur;
        while (da > Math.PI) da -= Math.PI * 2;
        while (da < -Math.PI) da += Math.PI * 2;
        if (Math.abs(da) < 1.9) { const na = cur + clamp(da, -RIG.steer * dt, RIG.steer * dt); v[0] = Math.sin(na) * h2; v[2] = Math.cos(na) * h2; }
      }
      push(v, wx, wz, top, RIG.accel, dt);
    }
  } else if (wl) push(v, wx, wz, Math.min(top, RIG.airCap + 0.0), RIG.airAccel, dt);
  // Space: on the floor, hold to charge a leap, let go to jump where you look. a quick tap is a hop
  if (ME.onGround && inp.jump && !RS.leapCharging && now >= RS.leapCd && !RS.charging) { RS.leapCharging = true; RS.leapT0 = now; rigsfx.servo(null, 1); }
  if (RS.leapCharging) {
    RS.leapK = Math.min(1, (now - RS.leapT0) / (L.charge * 1000));
    if (!inp.jump || !ME.onGround) leap(now);
  }
  v[1] -= RIG.grav * dt * 0.5; // (half before the move, half after: the same jump height at any frame rate)
  const was = ME.onGround;
  if (!was) RS.airMin = Math.min(RS.airMin, v[1]);
  const res = movePlayer(p, v, dt, BOXES, was);
  if (!res.ground) v[1] -= RIG.grav * dt * 0.5;
  ME.onGround = !!res.ground && v[1] <= 0.01;
  if (ME.onGround && !was) land(now);
  if (ME.onGround && res.ground.pad) { const pd = res.ground.pad; v[0] += pd[0]; v[1] = pd[1]; v[2] += pd[2]; ME.onGround = false; }
  // footsteps: every one thuds
  const hs2 = Math.hypot(v[0], v[2]);
  if (ME.onGround && hs2 > 1.2) {
    const was2 = Math.floor(RS.stepPhase);
    RS.stepPhase += dt * clamp(1.5 + hs2 * 0.14, 1.5, 4.3);
    if (Math.floor(RS.stepPhase) !== was2) stomp(hs2);
  }
  eyeStep(dt, crouch);
  return true;
}
function push(v, wx, wz, top, accel, dt) {
  const cur = v[0] * wx + v[2] * wz, add = top - cur;
  if (add <= 0) return;
  const a = Math.min(add, accel * top * dt);
  v[0] += a * wx; v[2] += a * wz;
}
function eyeStep(dt, crouch) {
  // taller in the rig, but never through a low ceiling (and a dip on every footstep)
  let want = crouch ? 1.45 : RIG.eye;
  const up = raycast([ME.pos[0], ME.pos[1] + 1.2, ME.pos[2]], [0, 1, 0], want - 0.9, BOXES);
  if (up) want = Math.min(want, 1.2 + up.t - 0.3);
  ME.eyeH += (want - ME.eyeH) * Math.min(1, dt * 10);
}
function stomp(hs) {
  const run = clamp(hs / 20, 0, 1), side = RS.stepSide = -RS.stepSide;
  G.shake = Math.max(G.shake, 0.12 + run * 0.16);
  punchCam(-0.004 - run * 0.007, 0, side * 0.004);
  RS.dip = 1;
  armsStep(side, 0.6 + run * 0.6);
  rigsfx.stomp(null, 0.55 + run * 0.4);
  const s = Math.sin(ME.yaw), c = Math.cos(ME.yaw);
  rfx.dust([ME.pos[0] + c * side * 0.4, ME.pos[1], ME.pos[2] - s * side * 0.4], 4 + Math.round(run * 4), 0.5, 1.5 + run * 2);
}
function leap(now) {
  RS.leapCharging = false;
  const k = RS.leapK;
  RS.leapK = 0;
  if (!ME.onGround) return;
  const v = ME.vel;
  if (k < L.tap) { v[1] = RIG.hop; rigsfx.leap(null, 0.35); rfx.dust(ME.pos, 8, 0.7, 3); G.shake = Math.max(G.shake, 0.25); playArms('rig_leap', 0.45); } // a tap: way up (several times a normal jump)
  else {
    const lv = leapVel(k, look());
    v[0] = lv[0] + v[0] * 0.25; v[1] = lv[1]; v[2] = lv[2] + v[2] * 0.25;
    net.send({ t: 'rig', k: 'leap', c: r2(k) });
    RS.leapAir = true; RS.leapCd = now + L.cd * 1000;
    playArms('rig_leap', 0.6 + k * 0.4);
    rigsfx.leap(null, k);
    G.shake = Math.max(G.shake, 0.3 + k * 0.4);
    rfx.dust(ME.pos, 14, 0.9, 4 + k * 4);
    rmesh.ring(ME.pos, 2.5 + k * 2, 0xd8c8a8, 0.35);
  }
  ME.onGround = false; ME.pos[1] += 0.02; RS.airMin = 0;
}
// touching down: every landing craters a bit; a leap's landing is the shockwave (the server says how it went)
function land(now) {
  const impact = -RS.airMin;
  RS.airMin = 0;
  const k = clamp((impact - 8) / 18, 0, 1);
  if (RS.leapAir) {
    RS.leapAir = false;
    net.send({ t: 'rig', k: 'land', p: ME.pos.map(r2) });
    craterFx(ME.pos, 5 + k * 3, Math.max(0.5, k), true);
    playArms('rig_land', 1);
  } else if (impact > 9) { craterFx(ME.pos, 2 + k * 3, k * 0.6, true); playArms('rig_land', 0.4 + k * 0.6); }
  else if (impact > 4) { rigsfx.stomp(null, 0.7); RS.dip = 1.4; }
  RS.landT = now; RS.landK = k;
}
function dashStep(dt, now) {
  const v = ME.vel, p = ME.pos, d = RS.dashDir, sp = P.speed;
  RS.dashT -= dt;
  v[0] = d[0] * sp; v[1] = d[1] * sp; v[2] = d[2] * sp;
  const res = movePlayer(p, v, dt, BOXES, ME.onGround);
  ME.onGround = !!res.ground && v[1] <= 0.01;
  // feel it land before the server says so (it decides the damage): the fist meets someone in the way
  const f = [p[0] + d[0] * P.reach, p[1] + 1.35 + d[1] * P.reach, p[2] + d[2] * P.reach];
  for (const r of G.remotes.values()) {
    if (!r.alive || isFriend(r) || RS.dashHit.has(r.id)) continue;
    const big = r.rigOn ? 1.6 : 1.1;
    if (Math.hypot(r.pos[0] - f[0], r.pos[1] + big - f[1], r.pos[2] - f[2]) > P.radius + 0.75) continue;
    RS.dashHit.add(r.id);
    impactFx([r.pos[0], r.pos[1] + big, r.pos[2]], [d[0], d[2]], RS.punchC, true);
  }
  if (res.wall || RS.dashT <= 0) { // ran out (or into a wall): it's heavy, most of the momentum dies
    if (res.wall && RS.dashT > 0.03) { G.shake = Math.max(G.shake, 0.5); rigsfx.wall(null); rfx.dust(p, 8, 0.6, 3); }
    RS.dashT = 0; ME.dashing = false;
    v[0] = d[0] * sp * 0.28; v[2] = d[2] * sp * 0.28; v[1] = Math.min(v[1], 2);
  }
  ME.eyeH += (RIG.eye - ME.eyeH) * Math.min(1, dt * 10);
}

// ------------------------------------------------------------ effects everyone sees
// a punch lands: the CLANG, sparks, a shock ring facing the punch, a flash (you: a hit-stop freeze + a big kick)
function impactFx(at, d2, c, mine) {
  rigsfx.clang(at, 0.6 + c * 0.6);
  rfx.sparks(at, 26 + Math.round(c * 40), 9 + c * 10, [0xfff2b0, 0xffb060, 0xff2bd6, 0xffffff], 0.5, 0.14, [d2[0] * 0.8, 0.2, d2[1] * 0.8]);
  rmesh.vring(at, [d2[0], 0, d2[1]], 1.6 + c * 2.4, 0xff2bd6, 0.28);
  rmesh.flash(at, 1 + c * 1.4, 0xffd0f0, 0.14);
  if (mine) {
    RS.hitStop = 0.05 + c * 0.06;
    G.shake = Math.max(G.shake, 0.6 + c * 0.6);
    punchCam(-0.05 - c * 0.05, 0.02 * (Math.random() - 0.5), 0.05 * (Math.random() - 0.5));
    if (c > 0.85) hud.msg('ROCKET PUNCH', 0.8, 'brag');
  } else shakeNear(at, 0.6, 24);
}
function shakeNear(at, k, r) { const d = Math.hypot(at[0] - ME.pos[0], at[1] - ME.pos[1], at[2] - ME.pos[2]); G.shake = Math.max(G.shake, k * Math.max(0, 1 - d / r)); }
// a crater: shockwave rings, a wall of dust rolling out, chunks of floor, a cracked decal
function craterFx(p, r, k, mine) {
  const fl = raycast([p[0], p[1] + 0.5, p[2]], [0, -1, 0], 3, BOXES), y = fl ? fl.point[1] : p[1], at = [p[0], y, p[2]];
  rmesh.ring(at, r * 1.1, 0xffffff, 0.3 + k * 0.15);
  rmesh.ring(at, r * 0.8, 0x6ff6ff, 0.5 + k * 0.2);
  if (k > 0.4) rmesh.ring(at, r * 1.4, 0xff2bd6, 0.65);
  rfx.dust(at, 18 + Math.round(k * 26), r * 0.6, r * 1.3);
  rfx.debris(at, 10 + Math.round(k * 20), 5 + k * 6);
  rmesh.crater(at, 0.8 + r * 0.25);
  rigsfx.land(mine ? null : at, k);
  if (mine) { G.shake = Math.max(G.shake, 0.5 + k * 0.6); punchCam(-0.03 - k * 0.04); RS.dip = 2; }
  else shakeNear(at, 0.4 + k * 0.5, 20 + r * 2);
}

// ------------------------------------------------------------ every frame (main.js, after the camera is set)
export function updateRig(dt, now, cam, replaying) {
  if (!ME.alive) ME.hackedUntil = 0; // (a hack doesn't follow you into your next life)
  hackedUi(now);
  updateGhosts(dt, cam);
  rfx.update(dt); rmesh.update(dt);
  if (RS.on && !G.joined) endLocal('quit');
  else if (RS.on && !ME.alive) endLocal('dead');
  else if (RS.on && now >= RS.until) endLocal('time');
  if (!RS.on) return;
  // charge: held time, or what blocking stored (whichever is more). blocking puts it down, letting go of block with
  // the button still held picks it back up
  if (W.aimHeld && RS.charging) RS.charging = false;
  if (RS.lmb && !RS.charging && !W.aimHeld && RS.dashT <= 0) startCharge(now);
  RS.charge = RS.charging ? clamp(Math.max(RS.store, (now - RS.chargeT0) / (P.charge * 1000)), 0, 1) : RS.store;
  if (RS.charging && RS.charge >= 1 && !RS.full) { RS.full = true; rigsfx.ready(); }
  if (!RS.charging) RS.full = false;
  // camera: a little zoom as the punch winds up, a kick out on the dash; the dip of each footstep and landing
  RS.fov = Math.max(0, RS.fov - dt * 3);
  W.zoom = 1 + (RS.charging ? RS.charge * 0.07 : 0) - RS.fov * 0.12;
  RS.dip = Math.max(0, RS.dip - dt * 7);
  cam.position.y -= RS.dip * 0.035;
  // the model that follows you: its pose feeds your afterimages (and the scrap if you die)
  const m = RS.model, hs = hspeed();
  placeModel();
  const s = Math.sin(ME.yaw), c = Math.cos(ME.yaw);
  poseRig(m, {
    spd: ME.onGround ? hs : 0, fwd: -(ME.vel[0] * s + ME.vel[2] * c), side: ME.vel[0] * c - ME.vel[2] * s, air: !ME.onGround, vy: ME.vel[1],
    block: W.aimHeld ? 1 : 0, charge: RS.charging ? RS.charge : 0, leap: RS.leapCharging ? RS.leapK : 0,
    punchT: (now - RS.punchT) / 1000, dash: RS.dashT > 0, missT: (now - RS.missT) / 1000, hackT: (now - RS.hackT) / 1000,
    landT: (now - RS.landT) / 1000, landK: RS.landK, pitch: ME.pitch, on: clamp((now - RS.startT) / 700, 0, 1), thrustT: (now - RS.thrT) / 1000,
  }, dt);
  // the overdrive trail: afterimages along your path when you're going fast
  const fast = hs > RIG.trail || RS.dashT > 0;
  RS.ghostT -= dt;
  if (fast && RS.ghostT <= 0 && !replaying) { RS.ghostT = 0.045; rigGhost(m, RS.ghostN++ % 2 ? 0xff2bd6 : 0x2ef2ff, true); }
  tint(replaying ? 0 : RS.dashT > 0 ? 1 : clamp((hs - RIG.trail) / 9, 0, 1));
  panelUpdate(now);
  rigHum({ on: !replaying && $('menu').classList.contains('hidden'), speed: hs, motion: RS.charging || RS.dashT > 0 ? 1 : W.aimHeld ? 0.5 : 0, charge: RS.charging ? RS.charge : -1, slow: RS.tint });
}
// weapons.js updateWeapons hands over the viewmodel while you're in the rig (guns holstered, the arms instead)
export function rigVM(dt, now, vmRoot) {
  const on = RS.on && ME.alive;
  if (vmRoot) vmRoot.visible = !on;
  if (!on) { updateArms(dt, { visible: true }); return false; } // (lets the arms finish putting themselves away, then hides them)
  W.flags = FLAGS.RIG | (W.aimHeld ? FLAGS.RIG_BLOCK : 0) | (RS.charging ? FLAGS.RIG_CHARGE : 0) | (RS.leapCharging ? FLAGS.RIG_LEAP : 0);
  W.aim = 0; W.scoped = false;
  ME.speedMul = 1;
  hud.ammo(null); hud.meter(null);
  stepPunch(dt);
  // the arms lag your mouse a little (they're heavy), and pump when you run
  let dy = ME.yaw - RS.lastYaw; while (dy > Math.PI) dy -= Math.PI * 2; while (dy < -Math.PI) dy += Math.PI * 2;
  const dp = ME.pitch - RS.lastPitch;
  RS.lastYaw = ME.yaw; RS.lastPitch = ME.pitch;
  const cl = (x) => clamp(x, -0.08, 0.08);
  RS.swayX += (cl(dy * 0.5) - RS.swayX) * Math.min(1, dt * 7);
  RS.swayY += (cl(dp * 0.5) - RS.swayY) * Math.min(1, dt * 7);
  armsReady();
  updateArms(dt, {
    charge: RS.charge, charging: RS.charging, block: !!W.aimHeld, dash: RS.dashT > 0, hack: now - RS.hackT < 600,
    leap: RS.leapCharging ? RS.leapK : 0, run: ME.onGround ? clamp(hspeed() / 22, 0, 1) : 0, phase: RS.stepPhase / 2,
    swayX: RS.swayX, swayY: RS.swayY, visible: true,
  }, (ev) => { if (ev === 'servo') rigsfx.servo(null); else if (ev === 'clank') rigsfx.block(null); else if (ev === 'beep') rigsfx.ready(); });
  return true;
}
// the camera's punch spring (weapons.js steps it, but not while the rig has the viewmodel)
function stepPunch(dt) {
  const p = G.punch;
  if (!p) return;
  const n = Math.min(40, Math.max(1, Math.ceil(dt * 240))), h = dt / n;
  for (let i = 0; i < n; i++) {
    p.vx += (-160 * p.x - 18 * p.vx) * h; p.x += p.vx * h;
    p.vy += (-160 * p.y - 18 * p.vy) * h; p.y += p.vy * h;
    p.vz += (-160 * p.z - 18 * p.vz) * h; p.z += p.vz * h;
  }
}

// ------------------------------------------------------------ HUD: the rig panel, the screen tint, hacked
let el = null;
function panel(on) {
  if (!el) {
    el = document.createElement('div');
    el.id = 'rigHud';
    el.innerHTML = '<div class="rh-top"><b>OVERDRIVE RIG</b><span class="rh-t"></span></div><div class="rh-bar rh-time"><i></i></div>'
      + '<div class="rh-row rh-sh"><span>SHIELD</span><div class="rh-bar"><i></i></div><em></em></div>'
      + '<div class="rh-row rh-pu"><span>PUNCH</span><div class="rh-bar"><i></i></div><em></em></div>'
      + '<div class="rh-ab"><div class="rh-th"><kbd>E</kbd> THRUST <em></em></div><div class="rh-mi"><kbd>G</kbd> MISSILES <em></em></div><div class="rh-ha"><kbd>R</kbd> HACK <em></em></div></div>';
    $('hud').append(el);
  }
  el.style.display = on ? 'block' : 'none';
  el.dataset.key = '';
}
function panelUpdate(now) {
  if (!el) return;
  const left = Math.max(0, RS.until - now), missL = Math.max(0, RS.missCd - now), hackL = Math.max(0, RS.hackCd - now);
  const thN = thrustCharges(RS.thr, now);
  const key = [thN, Math.ceil(left / 100), Math.round(RS.shield), Math.round(RS.charge * 50), Math.ceil(missL / 100), Math.ceil(hackL / 100), W.aimHeld ? 1 : 0, RS.charging ? 1 : 0].join('|');
  if (el.dataset.key === key) return;
  el.dataset.key = key;
  el.querySelector('.rh-t').textContent = (left / 1000).toFixed(1) + 's';
  el.querySelector('.rh-time i').style.width = (left / RS.dur) * 100 + '%';
  el.querySelector('.rh-sh i').style.width = (RS.shield / RIG.shield) * 100 + '%';
  el.querySelector('.rh-sh em').textContent = Math.round(RS.shield);
  el.querySelector('.rh-pu i').style.width = RS.charge * 100 + '%';
  el.querySelector('.rh-pu em').textContent = W.aimHeld ? (RS.store > 0 ? `BLOCK +${Math.round(RS.store * 100)}%` : 'BLOCKING') : RS.charge >= 1 ? 'FULL' : Math.round(RS.charge * 100) + '%';
  el.querySelector('.rh-th em').textContent = '\u25cf'.repeat(thN) + '\u25cb'.repeat(RIG.thrust.n - thN);
  el.querySelector('.rh-th').classList.toggle('ready', thN > 0);
  el.querySelector('.rh-mi em').textContent = missL > 0 ? (missL / 1000).toFixed(1) + 's' : 'READY';
  el.querySelector('.rh-ha em').textContent = hackL > 0 ? (hackL / 1000).toFixed(1) + 's' : 'READY';
  el.classList.toggle('low', left < 5000);
  el.classList.toggle('nosh', RS.shield <= 0);
  el.classList.toggle('full', RS.charge >= 1);
  el.querySelector('.rh-mi').classList.toggle('ready', missL <= 0);
  el.querySelector('.rh-ha').classList.toggle('ready', hackL <= 0);
}
function flashPanel(cls) { if (!el) return; el.classList.remove(cls); void el.offsetWidth; el.classList.add(cls); }
// fast in overdrive: the screen drags a cyan / magenta fringe and saturates (a bit of slow motion)
let tintEl = null, tintKey = -1;
function tint(k, now = false) {
  RS.tint = now ? k : RS.tint + (k - RS.tint) * 0.15;
  if (RS.tint < 0.01) RS.tint = 0;
  const q = Math.round(RS.tint * 12);
  if (q === tintKey) return;
  tintKey = q;
  if (!tintEl) { tintEl = document.createElement('div'); tintEl.id = 'rigTint'; $('hud').prepend(tintEl); }
  const t = q / 12;
  tintEl.style.opacity = String(t);
  const cv = $('game');
  if (cv) cv.style.filter = t > 0 ? `saturate(${(1 + t * 0.45).toFixed(2)}) contrast(${(1 + t * 0.08).toFixed(2)}) hue-rotate(${(-t * 12).toFixed(1)}deg)` : '';
}
let hackEl = null;
function hackedUi(now) {
  const left = (ME.hackedUntil || 0) - now;
  if (!hackEl && left <= 0) return;
  if (!hackEl) { hackEl = document.createElement('div'); hackEl.id = 'rigHacked'; hackEl.innerHTML = '<b>HACKED</b><span></span>'; $('hud').append(hackEl); }
  const on = left > 0 && ME.alive;
  hackEl.style.display = on ? 'flex' : 'none';
  if (on) hackEl.querySelector('span').textContent = `GRAPPLE OFFLINE · ${(left / 1000).toFixed(1)}s`;
}

// ------------------------------------------------------------ everyone else (and replay ghosts): Remote.update calls this
const RFX = new Set(['punch', 'hit', 'wall', 'sh', 'hack', 'miss', 'boom', 'leap', 'land', 'thrust']);
export function rigRemote(r, dt, now, floor) {
  if (r.hackedUntil > now && r.alive && Math.random() < dt * 30) rfx.glitch([r.pos[0], r.pos[1] + 1.2, r.pos[2]], 2, 0.7); // fried grapple
  const on = !!(r.f & FLAGS.RIG) && r.alive && r.buf.length > 0;
  let st = r.rig;
  if (!on) {
    if (st && st.on) remoteOff(r, st, true);
    r.rigOn = false;
    return;
  }
  const root = r.ch.root;
  if (!st || st.root !== root) { // (re)build: first time, or the mannequin was rebuilt (new look / team colour)
    if (st) freeRig(st.inst);
    st = r.rig = { inst: buildRig(r.color, { outline: true }), root, on: false, onT: 0, chT: 0, lpT: 0, thrT: 9, punchT: 9, punchC: 0, dashT: 0, missT: 9, hackT: 9, hitT: 9, landT: 9, landK: 0, wasAir: false, minVy: 0, ghostT: 0, ghostN: 0 };
    root.add(st.inst.root);
    st.inst.onStep = (k) => remoteStep(r, k);
  }
  if (!st.on) { // it just came on: the frame closes round them
    st.on = true; st.onT = r.buf.length > 2 ? 0 : 1;
    if (st.onT === 0) { rigsfx.on(r.pos); rfx.smoke([r.pos[0], r.pos[1] + 1.5, r.pos[2]], 14, 0xd8dde2, 0.9, 1.2, 1.2, 0.8); }
  }
  st.inst.root.visible = true;
  r.rigOn = true;
  r.ch.body.visible = st.onT < 0.4; // (the mannequin stands inside while the frame closes round it)
  r.rope.visible = false;
  if (r.weaponMesh && r.weaponMesh.userData.effect && r.weaponMesh.userData.effect !== 'none') { st.fxOf = r.weaponMesh; st.fx = r.weaponMesh.userData.effect; r.weaponMesh.userData.effect = 'none'; } // no skin sparkles out of a holstered gun
  r.marker.position.y = 3.25;
  r.tag.position.y += 0.95;
  // what it's doing, from its snapshots (velocity, the rig flags) and the server's events
  st.onT += dt;
  const f = r.f, vx = r.vel[0], vz = r.vel[2], s = Math.sin(r.yaw), c = Math.cos(r.yaw);
  st.chT = f & FLAGS.RIG_CHARGE ? st.chT + dt : 0;
  st.lpT = f & FLAGS.RIG_LEAP ? st.lpT + dt : 0;
  for (const k of ['punchT', 'missT', 'hackT', 'hitT', 'landT', 'thrT']) st[k] += dt;
  st.dashT = Math.max(0, st.dashT - dt);
  const air = Math.abs(r.vel[1]) > 1.5 && !(floor && r.pos[1] - floor.point[1] < 0.25);
  if (air) st.minVy = Math.min(st.minVy, r.vel[1]);
  else if (st.wasAir) { // touched down: a crater if it came down hard (leap landings come from the server, bigger)
    if (st.minVy < -11 && st.landT > 0.5) craterFx(r.pos, 2 + Math.min(3, -st.minVy / 8), 0.3, false);
    st.landT = 0; st.landK = Math.min(1, -st.minVy / 26); st.minVy = 0;
  }
  st.wasAir = air;
  const hs = Math.hypot(vx, vz);
  poseRig(st.inst, {
    spd: air ? 0 : hs, fwd: -(vx * s + vz * c), side: vx * c - vz * s, air, vy: r.vel[1],
    block: f & FLAGS.RIG_BLOCK ? 1 : 0, charge: st.chT > 0 ? Math.min(1, st.chT / P.charge) : 0, leap: st.lpT > 0 ? Math.min(1, st.lpT / L.charge) : 0,
    punchT: st.punchT, dash: st.dashT > 0, missT: st.missT, hackT: st.hackT, hitT: st.hitT, landT: st.landT, landK: st.landK,
    pitch: r.pitch, on: Math.min(1, st.onT / 0.7), thrustT: st.thrT,
  }, dt);
  // the overdrive trail: their afterimages
  st.ghostT -= dt;
  if ((hs > RIG.trail || st.dashT > 0) && st.ghostT <= 0) { st.ghostT = 0.045; rigGhost(st.inst, st.ghostN++ % 2 ? 0xff2bd6 : 0x2ef2ff); }
  // a thicker outline far away (like everyone else), a bigger shadow
  const k = r.distScale || 1;
  st.inst.outlineMat.uniforms.uThick.value = 0.013 + Math.max(0, Math.min(1, (k - 1) / 0.8)) * 0.05;
  r.shadow.scale.setScalar(2.1 * k);
}
function remoteStep(r, k) {
  rigsfx.stomp(r.pos, 0.4 + k * 0.5);
  if (!r.ghost) shakeNear(r.pos, 0.18 * k, 16); // a rig stomping past shakes your screen too
  if (k > 0.8) rfx.dust(r.pos, 3, 0.5, 2.5);
}
function remoteOff(r, st, poof) {
  st.on = false;
  st.inst.root.visible = false;
  hideGhosts(st.inst);
  r.ch.body.visible = true;
  r.marker.position.y = 2.75;
  r.shadow.scale.setScalar(1);
  if (st.fxOf && st.fxOf === r.weaponMesh) st.fxOf.userData.effect = st.fx;
  st.fxOf = null;
  if (poof && r.alive && r.buf.length > 2) { rigsfx.off(r.pos); rfx.smoke([r.pos[0], r.pos[1] + 1.5, r.pos[2]], 14, 0xd8dde2, 0.9, 1.2, 1.2, 0.8); }
}
// they died in it (the kill message, live or in a replay): the frame bursts apart into scrap
export function rigDied(r, vel) {
  const st = r && r.rig;
  if (!st || !st.on) return;
  r.ch.root.updateMatrixWorld(true);
  rigBurst(st.inst, vel || r.vel);
  rigsfx.burst(r.pos);
  remoteOff(r, st, false);
}
export function rigDispose(r) { if (r.rig) { freeRig(r.rig.inst); r.rig = null; } }

// ------------------------------------------------------------ server events: { t: 'rig', k }
// live (net) or in a killcam / play of the round (replay.js hands them over with its ghosts: live = false)
function rigEvent(m, getR, live) {
  const me = live && m.id === G.myId, r = getR(m.id), rs = r && r.rig;
  const at = (x) => (x ? [x.pos[0], x.pos[1] + (x.rigOn ? 1.6 : 1.1), x.pos[2]] : null);
  switch (m.k) {
    case 'punch': {
      if (me || !r) break;
      if (rs) { rs.punchT = 0; rs.punchC = m.c || 0; rs.dashT = punchDist(m.c || 0) / P.speed + 0.05; rs.chT = 0; }
      rigsfx.release(r.pos, m.c || 0);
      break;
    }
    case 'hit': {
      if (!Array.isArray(m.p)) break;
      const d2 = Array.isArray(m.d) ? m.d : [0, 1];
      if (me) {
        if (!RS.dashHit.has(m.to)) { RS.dashHit.add(m.to); impactFx(m.p, d2, m.c || 0, true); } // the prediction missed it
        hud.hit(false);
      } else impactFx(m.p, d2, m.c || 0, false);
      if (live && m.to === G.myId) { G.shake = 1; hud.msg('SMASHED', 1, 'slip'); }
      break;
    }
    case 'wall': {
      if (!Array.isArray(m.p)) break;
      const n = Array.isArray(m.n) ? m.n : [0, 0, 1];
      rigsfx.wall(m.p); rfx.dust(m.p, 16, 0.6, 4); rfx.debris(m.p, 14, 5);
      rmesh.crater(m.p, 1.2, n, 6); rmesh.flash(m.p, 1.2, 0xffd9a0, 0.12);
      if (live) shakeNear(m.p, 0.6, 18);
      if (me) hud.msg(`WALL SLAM +${P.wall}`, 1, 'brag');
      break;
    }
    case 'sh': { // shield / block hits on a rig: hex flicker (or sparks off the forearms), hitmarkers for whoever did it
      const blocked = m.b > 0;
      if (me) {
        const was = RS.shield;
        RS.shield = Math.max(0, Number(m.s) || 0); RS.store = clamp(Number(m.st) || 0, 0, 1);
        if (blocked) { armsJolt(Math.min(1.5, 0.4 + m.b / 30)); rigsfx.block(null); flashPanel('blockhit'); if (RS.store >= 1) hud.msg('BLOCK CHARGED · PUNCH!', 0.9, 'brag'); }
        else { rigsfx.shield(null); flashPanel('shhit'); hexScreen(); }
        if (was > 0 && RS.shield <= 0) { rigsfx.shieldBreak(null); hud.msg('OVERSHIELD DOWN', 1.2, 'slip'); }
      } else if (rs && rs.on) {
        const src = Array.isArray(m.p) ? m.p : null, c = at(r);
        let hit = c;
        if (src) { const d = [src[0] - c[0], src[2] - c[2]], l = Math.hypot(d[0], d[1]) || 1; hit = [c[0] + d[0] / l * 0.9, c[1], c[2] + d[1] / l * 0.9]; }
        if (blocked) { rfx.sparks(hit, 10, 6, [0xfff2b0, 0xffffff, 0x2ef2ff], 0.3, 0.1); rigsfx.block(hit); }
        else { rigHex(rs.inst, hit, Math.min(1, (m.a || 10) / 30)); rigsfx.shield(hit); }
        rs.hitT = 0;
      }
      if (live && Array.isArray(m.from) && m.from.includes(G.myId)) { hud.hit(false); }
      break;
    }
    case 'hack': {
      const tg = live && m.to === G.myId ? null : getR(m.to);
      const a = me ? [ME.pos[0], ME.pos[1] + 2.2, ME.pos[2]] : r ? [r.pos[0], r.pos[1] + 2.6, r.pos[2]] : null;
      const b = live && m.to === G.myId ? [ME.pos[0], ME.pos[1] + 1.4, ME.pos[2]] : tg ? at(tg) : null;
      if (a && b) rmesh.beam(a, b, 0.4);
      if (rs) rs.hackT = 0;
      if (tg) { tg.hackedUntil = performance.now() + (m.dur || 4000); tg.g = null; rfx.glitch(b, 24, 0.9); rigsfx.hack(b); }
      if (live && m.to === G.myId) { ME.hackedUntil = performance.now() + (m.dur || 4000); releaseHook(); rigsfx.hacked(); G.shake = Math.max(G.shake, 0.4); }
      if (me) hud.msg('BREACH: GRAPPLE FRIED', 0.9, 'brag');
      break;
    }
    case 'miss': if (rs) rs.missT = 0; if (r && !me) rigsfx.missiles(r.pos); break;
    case 'boom': {
      if (!Array.isArray(m.p)) break;
      rigsfx.boom(m.p); rmesh.flash(m.p, M.r * 0.9, 0xff8a3a, 0.22);
      rfx.sparks(m.p, 30, 10, [0xfff2b0, 0xff8a3a, 0xff2bd6], 0.6, 0.14); rfx.smoke(m.p, 10, 0x4a4c50, 0.9, 1.2, 1.4, 0.6);
      if (live) shakeNear(m.p, 0.5, 22);
      break;
    }
    case 'thrust': if (me) { RS.thr.n = Math.min(RS.thr.n, Number(m.n) || 0); break; } if (r) { if (rs) rs.thrT = 0; rigsfx.thrust(r.pos, 0.9); jetFx(r.pos, r.yaw || 0); } break;
    case 'leap': if (r && !me) { rigsfx.leap(r.pos, m.c || 0.5); rfx.dust(r.pos, 12, 0.9, 5); } break;
    case 'land': {
      if (me || !Array.isArray(m.p)) break; // (you saw your own already)
      craterFx(m.p, m.r || 5, Math.max(0.5, m.c || 0.5), false);
      if (rs) { rs.landT = 0; rs.landK = 1; }
      break;
    }
  }
}
// the hex flicker on your own screen when the shield soaks a hit
let hexEl = null;
function hexScreen() {
  if (!hexEl) { hexEl = document.createElement('div'); hexEl.id = 'rigHex'; $('hud').prepend(hexEl); }
  hexEl.classList.remove('on'); void hexEl.offsetWidth; hexEl.classList.add('on');
}
net.on('rig', (m) => {
  if (!m || typeof m.k !== 'string') return;
  if (RFX.has(m.k)) recordEv(m); // (killcams: on / off are in the snapshot flags)
  if (m.k === 'on') {
    if (m.id === G.myId) startLocal(Number(m.dur) || RIG.dur * 1000, Number(m.sh) || RIG.shield);
    else { const n = G.names.get(m.id); if (n) hud.chat(null, null, `${n.name} is in the OVERDRIVE RIG`); }
    return;
  }
  if (m.k === 'off') { if (m.id === G.myId) endLocal('server'); return; }
  rigEvent(m, (id) => G.remotes.get(id), true);
});
// replay.js: a recorded rig event, with the replay's ghosts standing in for the players
export function rigFx(m, ghosts) { rigEvent(m, (id) => ghosts.get(id), false); }
