// Local player movement: quake-ish air strafing, bhop with NO speed cap, slide, grapple, slipping.
import { movePlayer, raycast, rayBox, PH } from '/shared/physics.js';
import { BOXES } from '/shared/map.js';
import { HOOK, SLIP_TIME } from '/shared/weapons.js';
import { ropeStep, ropeJump, ROPE } from '/shared/hookphys.js';
import { G } from './ctx.js';
import { sfx } from './audio.js';
import { hud } from './hud.js';
import { net } from './net.js';
import { fx } from './fx.js';

export const ME = {
  pos: [0, 5, 0], vel: [0, 0, 0], yaw: 0, pitch: 0,
  onGround: false, groundTicks: 0, jumpBuf: 0, combo: 0,
  hook: null, slipUntil: 0, sliding: false, speedMul: 1,
  alive: false, hp: 100, seq: 0, airMaxFall: 0,
  crouching: false, sprinting: false, eyeH: 1.6, crouchTaps: [], tbagWarned: 0,
  dashing: false, moonUntil: 0,
};

export const C = {
  grav: 26, jump: 9.2,
  gSpeed: 10, gAccel: 11, fric: 6, stop: 3,
  airCap: 1.4, airAccel: 90, airCtl: 2.6,
  slideFric: 0.25, slideMin: 7,
  sprintMul: 1.45, crouchMul: 0.45, standEye: 1.6, crouchEye: 1.05, slideEye: 0.95,
  tbagWindow: 4000, tbagWarn: 9, tbagBoom: 14,
};

export function eye() {
  return [ME.pos[0], ME.pos[1] + ME.eyeH, ME.pos[2]];
}

// crouch taps: spam crouch for too long and your body can't handle it
export function crouchTap(now) {
  if (!ME.alive) return 0;
  ME.crouchTaps = ME.crouchTaps.filter((t) => now - t < C.tbagWindow);
  ME.crouchTaps.push(now);
  const n = ME.crouchTaps.length;
  if (n >= C.tbagBoom) { ME.crouchTaps = []; return 2; }
  if (n >= C.tbagWarn && now - ME.tbagWarned > 1500) { ME.tbagWarned = now; hud.msg('your knees are getting hot...', 1.2); }
  return n >= C.tbagWarn ? 1 : 0;
}
export function look() {
  const cp = Math.cos(ME.pitch);
  return [-Math.sin(ME.yaw) * cp, Math.sin(ME.pitch), -Math.cos(ME.yaw) * cp];
}
export function hspeed() { return Math.hypot(ME.vel[0], ME.vel[2]); }

export function applyKb(v) {
  ME.vel[0] += v[0]; ME.vel[1] += v[1]; ME.vel[2] += v[2];
  if (v[1] > 0.5 && ME.onGround) { ME.onGround = false; ME.pos[1] += 0.02; }
}

export function slip(now) {
  ME.slipUntil = now + SLIP_TIME * 1000;
  const d = look();
  ME.vel[0] += d[0] * 6; ME.vel[2] += d[2] * 6;
  ME.vel[1] = Math.max(ME.vel[1], 6.5);
  ME.onGround = false;
  ME.hook = null;
  sfx.whoops();
  hud.msg('WHOOPS!', 1.4, 'slip');
}

function accelerate(v, wx, wz, wishSpeed, accel, dt) {
  const cur = v[0] * wx + v[2] * wz;
  const add = wishSpeed - cur;
  if (add <= 0) return;
  let a = accel * wishSpeed * dt;
  if (a > add) a = add;
  v[0] += a * wx; v[2] += a * wz;
}

export function hookPoint() {
  const h = ME.hook;
  if (!h) return null;
  if (h.target) {
    const r = G.remotes.get(h.target);
    if (!r || !r.alive) return null;
    return [r.pos[0], r.pos[1] + 1, r.pos[2]];
  }
  return h.point;
}

export function tryHook() {
  if (!ME.alive || ME.hook) return;
  const o = eye(), d = look();
  const mh = raycast(o, d, HOOK.range, BOXES);
  const maxT = mh ? mh.t : HOOK.range;
  let best = null;
  for (const r of G.remotes.values()) {
    if (!r.alive) continue;
    for (const hb of r.hitboxes()) {
      const h = rayBox(o, d, hb, maxT);
      if (h && (!best || h.t < best.t)) best = { t: h.t, r };
    }
  }
  if (best) {
    ME.hook = { target: best.r.id, len: best.t + 0.5 };
    net.send({ t: 'push', to: best.r.id, w: 'hook' });
    hud.msg('GET OVER HERE', 0.8);
  } else if (mh) {
    ME.hook = { point: mh.point, len: mh.t };
  } else {
    const end = [o[0] + d[0] * HOOK.range, o[1] + d[1] * HOOK.range, o[2] + d[2] * HOOK.range];
    fx.rope([o[0], o[1] - 0.3, o[2]], end, 0.1);
    return;
  }
  sfx.grapple();
}

export function releaseHook() { ME.hook = null; }

function hookStep(dt) {
  const a = hookPoint();
  if (!a) { ME.hook = null; return; }
  // pendulum rope, same as the bots': reels in at a steady rate, keeps your swing, soft instead of snapping
  ropeStep(ME.hook, a, ME.pos, ME.vel, dt, C.grav);
  feel.lift = 1;
}

// letting go: the rope's share of your weight fades out over a moment instead of dropping you in one step
function ropeLetGo(dt) {
  if (feel.lift <= 0) return;
  feel.lift = Math.max(0, feel.lift - dt / 0.15);
  ME.vel[1] += C.grav * ROPE.lift * feel.lift * dt;
}

// camera feel on the rope: lean a little toward the rope and widen the fov a touch, eased in and out with
// critically damped springs (no snaps). main.js adds ME.lean to the camera roll and ME.ropeFov to the fov.
const feel = { lean: 0, leanV: 0, fov: 0, fovV: 0, kick: 0, lift: 0, t: 0 };
function ease(k, target, w, dt) {
  feel[k + 'V'] += (w * w * (target - feel[k]) - 2 * w * feel[k + 'V']) * dt;
  feel[k] += feel[k + 'V'] * dt;
}
function hookFeel(dt, now) {
  if (now - feel.t > 250) Object.assign(feel, { leanV: 0, fovV: 0, kick: 0, lift: 0 }); // respawned / was paused: the springs ease lean and fov back from where they were
  feel.t = now;
  let lean = 0, fov = 0;
  const h = ME.hook;
  if (h && h.n) {
    const side = h.n[0] * Math.cos(ME.yaw) - h.n[2] * Math.sin(ME.yaw); // + = the rope pulls to your right
    lean = -side * 0.06; // by the rope's angle, so a steady swing leans too. roll is + to the left, so lean right = negative
    fov = 1.5 + Math.min(2.5, hspeed() * 0.08);
  }
  feel.kick = Math.max(0, feel.kick - dt * 3); // grapple jump: a short swell instead of a text popup
  ease('lean', lean, 7, dt);
  ease('fov', fov + feel.kick * 4, 6, dt);
  ME.lean = feel.lean; ME.ropeFov = feel.fov;
}

export function stepPlayer(dt, inp, now) {
  if (!ME.alive) return;
  const v = ME.vel, p = ME.pos;
  hookFeel(dt, now); // before any early return, so the camera lean keeps easing (e.g. through a dash)
  // glitch dash: fly straight where you look, no gravity. letting go keeps all of it.
  if (ME.dashing) {
    const d = look(), sp = 38;
    v[0] = d[0] * sp; v[1] = d[1] * sp; v[2] = d[2] * sp;
    ME.hook = null;
    ME.eyeH += (C.standEye - ME.eyeH) * Math.min(1, dt * 14);
    const res = movePlayer(p, v, dt, BOXES, false);
    ME.onGround = !!res.ground && v[1] <= 0;
    return;
  }
  const moon = now < ME.moonUntil;
  const grav = C.grav * (moon ? 0.4 : 1), jumpV = C.jump * (moon ? 1.55 : 1);
  const slipping = now < ME.slipUntil;
  const fw = (inp.f ? 1 : 0) - (inp.b ? 1 : 0), st = (inp.r ? 1 : 0) - (inp.l ? 1 : 0);
  const s = Math.sin(ME.yaw), c = Math.cos(ME.yaw);
  let wx = -s * fw + c * st, wz = -c * fw - s * st;
  const wl = Math.hypot(wx, wz);
  if (wl) { wx /= wl; wz /= wl; }
  // grapple jump: let go and get flung along your swing plus a modest hop, added on top of your momentum.
  // timing counts a little: on the upswing, swinging the way you look, you get more
  if (inp.jumpPressed && ME.hook) {
    ME.hook = null;
    const q = ropeJump(v, look());
    ME.onGround = false;
    inp.jumpPressed = false;
    sfx.ropeJump(q);
    feel.kick = 0.6 + q * 0.4;
  }
  if (inp.jumpPressed) ME.jumpBuf = 0.22;
  const wantJump = (ME.jumpBuf > 0 || inp.jump) && !slipping;
  ME.jumpBuf -= dt;
  const hs = Math.hypot(v[0], v[2]);
  // crouch while fast = slide. crouch while slow = crouch walk. shift = sprint.
  ME.sliding = !!inp.crouch && ME.onGround && hs > C.slideMin && !slipping;
  ME.crouching = !!inp.crouch && !ME.sliding;
  ME.sprinting = !!inp.sprint && !inp.crouch && fw > 0 && ME.onGround;
  const moveMul = ME.speedMul * (ME.sprinting ? C.sprintMul : ME.crouching ? C.crouchMul : 1);
  const eyeT = ME.sliding ? C.slideEye : ME.crouching ? C.crouchEye : C.standEye;
  ME.eyeH += (eyeT - ME.eyeH) * Math.min(1, dt * 14);

  if (ME.onGround && !ME.hook) {
    if (wantJump) {
      // jumping on the first tick of landing skips friction entirely = momentum is forever
      v[1] = jumpV;
      ME.combo = ME.groundTicks <= 3 ? ME.combo + 1 : 1;
      ME.onGround = false; ME.jumpBuf = 0;
      sfx.jump();
    } else {
      const fr = slipping ? 0.02 : ME.sliding ? C.slideFric : C.fric;
      if (hs > 0) {
        const ctrl = Math.max(hs, C.stop);
        const ns = Math.max(0, hs - ctrl * fr * dt) / hs;
        v[0] *= ns; v[2] *= ns;
      }
      if (!slipping && !ME.sliding && wl) accelerate(v, wx, wz, C.gSpeed * moveMul, C.gAccel * Math.max(1, moveMul), dt);
      if (ME.groundTicks > 3 && !ME.sliding) ME.combo = 0;
    }
  } else if (wl && !slipping) {
    accelerate(v, wx, wz, C.airCap, C.airAccel, dt);
    // W-only air steering: rotates your momentum toward where you look, keeps ALL the speed
    if (fw > 0 && !st && hs > 2) {
      const cur = Math.atan2(v[0], v[2]), tgt = Math.atan2(wx, wz);
      let da = tgt - cur;
      while (da > Math.PI) da -= Math.PI * 2;
      while (da < -Math.PI) da += Math.PI * 2;
      if (Math.abs(da) < Math.PI / 2) {
        const m = C.airCtl * dt;
        const na = cur + Math.max(-m, Math.min(m, da));
        const h2 = Math.hypot(v[0], v[2]);
        v[0] = Math.sin(na) * h2; v[2] = Math.cos(na) * h2;
      }
    }
  }

  v[1] -= grav * dt;
  if (ME.hook) hookStep(dt); else ropeLetGo(dt);
  if (!ME.onGround) ME.airMaxFall = Math.min(ME.airMaxFall, v[1]);

  const was = ME.onGround;
  const res = movePlayer(p, v, dt, BOXES, was);
  ME.onGround = !!res.ground && v[1] <= 0.01;
  if (ME.onGround) {
    if (!was) {
      if (ME.airMaxFall < -14) { fx.dust(p, 10); sfx.land(); }
      ME.airMaxFall = 0;
      ME.groundTicks = 0;
    }
    ME.groundTicks++;
    if (res.ground.pad) {
      const pd = res.ground.pad;
      v[0] += pd[0]; v[1] = pd[1]; v[2] += pd[2];
      ME.onGround = false;
      sfx.pad();
      hud.msg('BOING', 0.5);
    }
  }
}
