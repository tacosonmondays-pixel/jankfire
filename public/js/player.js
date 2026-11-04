// Local player movement: quake-ish air strafing, bhop with NO speed cap, slide, grapple, slipping.
import { movePlayer, raycast, rayBox, PH } from '/shared/physics.js';
import { BOXES } from '/shared/map.js';
import { HOOK, SLIP_TIME } from '/shared/weapons.js';
import { ropeStep, ropeJump, ROPE } from '/shared/hookphys.js';
import { G } from './ctx.js';
import { sfx } from './audio.js';
import { hud } from './hud.js';
import { net } from './net.js';
import { query } from '/shared/physics.js';
import { WRECK, slamSize } from '/shared/weapons.js';
import { fx } from './fx.js';
import { flashRope, myGrapple } from './grapple.js';
import { WEAPONS } from '/shared/weapons.js';
import { holeDrag } from '/shared/physics.js';

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
  if (now < (ME.ballUntil || 0)) return 0; // crouch is the ground slam now, and steel balls don't have knees
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

// rubber duck black holes eat momentum: inside one you bleed speed (all but falling in, harder near the middle)
// and close to the middle your rope snaps. never in your own hole or your team's. ME.holeF = how deep you are (0..1)
function friendlyHole(h) {
  if (h.o === G.myId) return true;
  const n = G.names.get(h.o);
  if (G.mode === 'coop') return !!n && !n.bot;
  return !!(G.myTeam && n && n.team === G.myTeam);
}
function holeEat(dt, now) {
  ME.holeF = 0;
  for (const h of G.holes.values()) {
    if (now < h.born || friendlyHole(h)) continue;
    const R = h.R || (h.big ? 34 : WEAPONS.duck.holeR);
    const d = holeDrag(ME.pos, ME.vel, h.p, R, WEAPONS.duck.drag * (h.on === G.myId ? WEAPONS.duck.onDrag : 1), dt); // stuck on you: slowed, not frozen
    if (d < 0) continue;
    ME.holeF = Math.max(ME.holeF, 1 - d / R);
    if (ME.hook && d < WEAPONS.duck.snapR * (h.big ? 1.6 : 1)) {
      const a = hookPoint();
      ME.hook = null;
      if (a) fx.spray(a, 8, [0x9a3bff, 0xffffff], 5, 0.5, 0.1, 10, 1);
      sfx.ropeSnap();
      hud.msg('ROPE SNAPPED', 0.7, 'slip');
    }
  }
}

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
    flashRope([o[0], o[1] - 0.3, o[2]], end, 0.1);
    return;
  }
  sfx.grapple(myGrapple());
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
  if (h && h.n && !(now < (ME.ballUntil || 0))) { // (the wrecking ball's chain doesn't lean the third-person camera)
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
  hookFeel(dt, now); // before any early return, so the camera lean keeps easing (e.g. through a dash, the ball or a soap bubble)
  if (G.lassoStep && G.lassoStep(dt, inp, now)) return; // on the end of a lasso (or tumbling out of a fling): lasso.js moves you
  if (ME.ballUntil) { if (now < ME.ballUntil) { feel.lift = 0; ballStep(dt, inp, now); return; } endBall(); } // wrecking ball killstreak (its chain has its own physics)
  const v = ME.vel, p = ME.pos;
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
  // sealed in a soap bubble (Bubble Wand): you float where it floats and can't steer. looking around still works
  if (now < (ME.trapUntil || 0)) {
    const tv = ME.trapV || [0, 0, 0];
    v[0] = tv[0]; v[1] = tv[1]; v[2] = tv[2];
    ME.hook = null; ME.sliding = false; ME.crouching = false; ME.sprinting = false; ME.jumpBuf = 0; feel.lift = 0;
    ME.eyeH += (C.standEye - ME.eyeH) * Math.min(1, dt * 14);
    movePlayer(p, v, dt, BOXES, false);
    ME.onGround = false;
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
  holeEat(dt, now);
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

// ------------------------------------------------------------ wrecking ball (killstreak)
// You turn into a heavy steel ball: it rolls with real momentum, bounces off walls, hops instead of jumping,
// swings on a chain instead of the rope, and crouch in the air slams it into the floor.
// This is only how the ball moves (movement is client-side). The server judges every ram and slam itself.
export const BALL = {
  hw: 0.65, h: 1.95, step: 0.75, // collision box: wider than you, but it still squeezes through doors (the ball is 2.2 m)
  grav: 40, top: 26, accel: 20, airAccel: 7, steer: 2.4, airSteer: 0.8, // heavy: falls fast, fast top speed, turns slowly
  roll: 1.8, rollK: 0.09, brake: 24, hop: 6.5, // rolling resistance (low), crouch on the floor = brake
  wall: 0.6, floor: 0.3, eye: 3.0, corner: 0.45, // bounce off walls / hard landings, camera pivot above your feet, corner slide
  floatK: 0.4, floatTo: -8, // after a slam: lighter gravity on the way up and over the top, so there's time to slam again
  reel: 2, reelAcc: 40, reelMax: 26, winch: 25, minLen: 4.5, clear: 0.8, catch: 0.7, // chain winch + snapping tight
  pump: 9, pumpMax: 40, // W on a tight chain pumps the swing, up to this fast
};
export const BS = {
  hw: PH.halfW, h: PH.height, slam: false, slamReady: 0, slamBuf: 0, airPress: false, crouchWas: false, float: false,
  chain: null, pivotY: 0, bonkT: 0, top: 0, slamTop: 0, last: null, snapNow: false,
};
ME.ballUntil = 0;
export const ballOn = (now = performance.now()) => ME.alive && now < (ME.ballUntil || 0);

export function startBall(dur) {
  const now = performance.now();
  if (!(ME.ballUntil > now)) { BS.hw = PH.halfW; BS.h = PH.height; BS.pivotY = ME.pos[1] + ME.eyeH; } // grows into the ball as soon as there's room
  ME.ballUntil = now + dur * 1000;
  BS.slam = false; BS.float = false; BS.chain = null; BS.slamReady = now + 300; BS.slamBuf = 0; BS.airPress = false;
  BS.top = ME.pos[1]; BS.last = null;
  ME.sliding = false; ME.crouching = false; ME.sprinting = false; ME.dashing = false; ME.combo = 0;
}
export function endBall() {
  if (!ME.ballUntil) return;
  ME.ballUntil = 0;
  BS.slam = false; BS.float = false; BS.chain = null; BS.slamBuf = 0; BS.airPress = false;
  if (!ME.alive) ME.eyeH = C.standEye; // died in it: the death cam starts from your own eyes
}

const qBall = [];
const ov = (x0, y0, z0, x1, y1, z1, b) => x0 < b.max[0] && x1 > b.min[0] && y0 < b.max[1] && y1 > b.min[1] && z0 < b.max[2] && z1 > b.min[2];
function ballOverlap(p, hw, h, boxes) {
  for (const b of boxes || query(BOXES, p[0] - hw, p[2] - hw, p[0] + hw, p[2] + hw, qBall)) if (ov(p[0] - hw, p[1], p[2] - hw, p[0] + hw, p[1] + h, p[2] + hw, b)) return b;
  return null;
}
// like movePlayer but with the ball's box, and walls bounce the ball back instead of stopping it dead
function moveBall(pos, vel, dt, canStep) {
  const hw = BS.hw, h = BS.h, m = hw + 0.8;
  const boxes = query(BOXES, Math.min(pos[0], pos[0] + vel[0] * dt) - m, Math.min(pos[2], pos[2] + vel[2] * dt) - m,
    Math.max(pos[0], pos[0] + vel[0] * dt) + m, Math.max(pos[2], pos[2] + vel[2] * dt) + m, qBall);
  const steps = Math.min(300, Math.max(1, Math.ceil((Math.hypot(vel[0], vel[1], vel[2]) * dt) / 0.25)));
  const sdt = dt / steps;
  const res = { ground: null, ceil: false, wall: 0, n: null, landV: 0 };
  for (let i = 0; i < steps; i++) {
    for (const ax of [1, 0, 2]) {
      const d = vel[ax] * sdt;
      if (d === 0) continue;
      pos[ax] += d;
      let hit = false;
      for (const b of boxes) {
        if (!ov(pos[0] - hw, pos[1], pos[2] - hw, pos[0] + hw, pos[1] + h, pos[2] + hw, b)) continue;
        if (ax === 1) {
          if (d < 0) { pos[1] = b.max[1]; res.ground = b; res.landV = Math.min(res.landV, vel[1]); } else { pos[1] = b.min[1] - h - 1e-4; res.ceil = true; }
          vel[1] = 0;
        } else {
          const rise = b.max[1] - pos[1];
          if ((canStep || res.ground) && rise > 0 && rise <= BALL.step) { // kerbs and stairs: roll up them
            const old = pos[1];
            pos[1] = b.max[1] + 1e-3;
            if (!ballOverlap(pos, hw, h, boxes)) { res.ground = b; continue; }
            pos[1] = old;
          }
          // only clipped its corner (a door frame, the end of a wall): slide round it instead of bouncing off
          const pa = 2 - ax, lo = pos[pa] + hw - b.min[pa], hi = b.max[pa] - (pos[pa] - hw);
          const nudge = lo < hi ? -lo - 1e-3 : hi + 1e-3;
          if (Math.abs(nudge) <= BALL.corner) {
            const old = pos[pa];
            pos[pa] += nudge;
            if (!ballOverlap(pos, hw, h, boxes)) continue;
            pos[pa] = old;
          }
          pos[ax] = d > 0 ? b.min[ax] - hw - 1e-4 : b.max[ax] + hw + 1e-4;
          hit = true;
        }
      }
      if (hit) { // once per axis, however many boxes that wall is made of
        const imp = Math.abs(vel[ax]);
        if (imp > res.wall) { res.wall = imp; res.n = ax === 0 ? [d > 0 ? -1 : 1, 0, 0] : [0, 0, d > 0 ? -1 : 1]; }
        vel[ax] = imp > 3 ? -vel[ax] * BALL.wall : 0;
      }
    }
  }
  return res;
}

// heavy steering: your momentum turns toward where you want to go a bit at a time, then you push along it up to top speed
function ballPush(v, wx, wz, accel, steer, dt) {
  const hs = Math.hypot(v[0], v[2]);
  if (hs > 2) {
    const cur = Math.atan2(v[0], v[2]);
    let da = Math.atan2(wx, wz) - cur;
    while (da > Math.PI) da -= Math.PI * 2;
    while (da < -Math.PI) da += Math.PI * 2;
    if (Math.abs(da) < 1.75) { const na = cur + Math.max(-steer * dt, Math.min(steer * dt, da)); v[0] = Math.sin(na) * hs; v[2] = Math.cos(na) * hs; }
  }
  const add = BALL.top - (v[0] * wx + v[2] * wz);
  if (add > 0) { const a = Math.min(add, accel * dt); v[0] += wx * a; v[2] += wz * a; }
}

// on a tight chain W pumps the swing like a real wrecking ball: it pushes along the swing (never along the chain), and
// only while the ball is already going your way, so holding W builds the swing up instead of damping it
function ballPump(v, wx, wz, dt) {
  const a = hookPoint(), p = ME.pos;
  if (!a) return;
  let nx = a[0] - p[0], ny = a[1] - (p[1] + WRECK.r), nz = a[2] - p[2];
  const nl = Math.hypot(nx, ny, nz) || 1;
  nx /= nl; ny /= nl; nz /= nl;
  const k = wx * nx + wz * nz;
  let tx = wx - nx * k, ty = -ny * k, tz = wz - nz * k;
  const tl = Math.hypot(tx, ty, tz);
  if (tl < 0.2) return; // pushing straight along the chain does nothing
  tx /= tl; ty /= tl; tz /= tl;
  const sp = Math.hypot(v[0], v[1], v[2]), along = v[0] * tx + v[1] * ty + v[2] * tz;
  if ((along <= 0 && sp > 2) || sp >= BALL.pumpMax) return; // (from a dead hang any push gets it going)
  const add = Math.min(BALL.pump * dt, BALL.pumpMax - sp);
  v[0] += tx * add; v[1] += ty * add; v[2] += tz * add;
}

// how long the chain can be with the bottom of the swing still clearing the floor under the anchor. look down from just
// beside the anchor on your side of it (the anchor itself is on a wall, a ceiling or the top of something)
function swingRoom(a, p) {
  const hx = p[0] - a[0], hz = p[2] - a[2], hl = Math.hypot(hx, hz) || 1, o = WRECK.r + 0.5;
  for (const s of [[a[0] + hx / hl * o, a[1] + 0.1, a[2] + hz / hl * o], [a[0] + hx / hl * 0.3, a[1] - 0.3, a[2] + hz / hl * 0.3]]) {
    const fl = raycast(s, [0, -1, 0], 300, BOXES);
    if (fl && fl.t > 0.02) return a[1] - fl.point[1] - WRECK.r - BALL.clear;
    if (!fl) return Infinity;
  }
  return Infinity;
}
// the chain: a heavy pendulum on a crane winch. it never stretches and it can go slack. the winch hauls you in until your
// swing clears the floor under the anchor, or while you drag along the floor or just hang there; while you're swinging
// it holds the chain, so the pendulum keeps all your momentum. when the chain snaps tight, most of your speed turns into
// swing instead of stopping you dead. hooked a person: it reels you straight into them.
function ballHookStep(dt) {
  const a = hookPoint();
  if (!a) { ME.hook = null; BS.chain = null; return; }
  const v = ME.vel, p = ME.pos, R = WRECK.r;
  const dx = a[0] - p[0], dy = a[1] - (p[1] + R), dz = a[2] - p[2];
  const dist = Math.hypot(dx, dy, dz);
  if (dist < 0.01) return;
  const nx = dx / dist, ny = dy / dist, nz = dz / dist;
  let ch = BS.chain;
  if (!ch || ch.hook !== ME.hook) ch = BS.chain = { hook: ME.hook, len: dist, reel: BALL.reel, taut: false, dist, maxLen: ME.hook.target ? Infinity : swingRoom(a, p) };
  ch.dist = dist;
  if (ME.hook.target && dist < 3.2) { ME.hook = null; BS.chain = null; return; } // reeled a person in: let go, the ram does the rest
  const r0 = v[0] * nx + v[1] * ny + v[2] * nz, vt2 = Math.max(0, v[0] * v[0] + v[1] * v[1] + v[2] * v[2] - r0 * r0);
  const sw = (v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) / (2 * BALL.grav) + (p[1] + R - (a[1] - ch.len)); // swing energy as a height
  const haul = ME.hook.target || ch.len > ch.maxLen ? 1 : ME.onGround ? 0.6 : sw < 1.5 ? 0.5 : 0;
  // the winch only has so much power: whirling round fast on a short chain, it can barely haul (no runaway spin-ups)
  const target = BALL.reelMax * haul * Math.min(1, BALL.winch / Math.max(1e-3, vt2 / dist));
  ch.reel += Math.max(-BALL.reelAcc * dt, Math.min(BALL.reelAcc * dt, target - ch.reel));
  ch.reel = Math.max(0, Math.min(ch.reel, (ch.len - BALL.minLen) * 5)); // the winch slows down as it runs out of chain
  ch.len = Math.max(BALL.minLen, ch.len - ch.reel * dt);
  if (ME.hook.len != null) ME.hook.len = Math.max(ch.len, 0.5); // so the normal rope carries on right if the ball ends mid-swing
  if (dist < ch.len) { ch.taut = false; return; } // slack: just flying
  const radial = r0; // + = toward the anchor
  const want = ch.reel + (dist - ch.len) * 8; // reel speed + pull back any stretch
  if (radial < want) {
    let tx = v[0] - nx * radial, ty = v[1] - ny * radial, tz = v[2] - nz * radial;
    const lost = want - radial;
    if (!ch.taut && lost > 5) { // snapped tight: swing with it (but never come out faster than you went in)
      const tl = Math.hypot(tx, ty, tz), sp = Math.hypot(v[0], v[1], v[2]);
      const nt = Math.min(tl + lost * BALL.catch, Math.sqrt(Math.max(0, sp * sp - want * want)));
      if (tl > 0.5 && nt > tl) { const k = nt / tl; tx *= k; ty *= k; tz *= k; }
      sfx.chain();
    }
    v[0] = tx + nx * want; v[1] = ty + ny * want; v[2] = tz + nz * want;
  }
  ch.taut = true;
}

const r2 = (x) => Math.round(x * 100) / 100;
function slamImpact(now) {
  const p = ME.pos, v = ME.vel;
  const h = Math.max(0, BS.slamTop - p[1]), S = slamSize(h); // the server sizes it the same way from its own record
  BS.slam = false; BS.float = true; BS.top = p[1];
  BS.slamReady = now + WRECK.slamCd * 1000;
  BS.last = { h, dmg: S.dmg, r: S.r, t: now };
  net.send({ t: 'slam', p: p.map(r2) });
  // straight back up: the higher you came from, the higher you go (5 to 12 m), so slams chain
  const apex = Math.max(5, Math.min(12, h * 0.55 + 3));
  v[1] = Math.sqrt(2 * BALL.grav * BALL.floatK * (now < ME.moonUntil ? 0.45 : 1) * apex);
  ME.onGround = false; p[1] += 0.05;
  fx.slam([p[0], p[1], p[2]], S.r, S.k);
  sfx.slam(null, S.k);
  G.shake = Math.max(G.shake, 0.8 + S.k * 0.6);
  hud.msg(`${S.k > 0.6 ? 'MEGA SLAM' : 'SLAM'} · ${Math.round(h)} m`, 0.8, 'brag');
}

function ballStep(dt, inp, now) {
  const v = ME.vel, p = ME.pos;
  ME.sliding = false; ME.crouching = false; ME.sprinting = false; ME.dashing = false; ME.combo = 0;
  // grow into the ball's box as soon as there's room (you might have been in a doorway)
  if (BS.hw < BALL.hw || BS.h < BALL.h) {
    const hw = Math.min(BALL.hw, BS.hw + dt * 3), h = Math.min(BALL.h, BS.h + dt * 3);
    if (!ballOverlap(p, hw, h)) { BS.hw = hw; BS.h = h; }
  }
  const moon = now < ME.moonUntil;
  const fw = (inp.f ? 1 : 0) - (inp.b ? 1 : 0), st = (inp.r ? 1 : 0) - (inp.l ? 1 : 0);
  const s = Math.sin(ME.yaw), c = Math.cos(ME.yaw);
  let wx = -s * fw + c * st, wz = -c * fw - s * st;
  const wl = Math.hypot(wx, wz);
  if (wl) { wx /= wl; wz /= wl; }
  // jump on the chain: let go and keep the swing, with a kick up
  if (inp.jumpPressed && ME.hook) {
    ME.hook = null; BS.chain = null;
    v[0] *= 1.08; v[2] *= 1.08; v[1] = Math.max(v[1], 0) * 1.05 + 7;
    ME.onGround = false; inp.jumpPressed = false;
    sfx.chain(); hud.msg('LET GO', 0.5);
  }
  if (inp.jumpPressed) ME.jumpBuf = 0.18;
  const wantJump = ME.jumpBuf > 0 || inp.jump;
  ME.jumpBuf -= dt;
  // crouch in the air: ground slam. a press just before it's ready still counts, and holding it slams again as soon as
  // it's ready (that's how you chain them). crouch on the floor is the brake, so holding it there never slams.
  const press = !!inp.crouch && !BS.crouchWas;
  BS.crouchWas = !!inp.crouch;
  if (press && !ME.onGround) { BS.slamBuf = 0.25; BS.airPress = true; }
  if (!inp.crouch) BS.airPress = false;
  BS.slamBuf -= dt;
  if ((BS.slamBuf > 0 || BS.airPress) && !ME.onGround && !BS.slam && now >= BS.slamReady) {
    BS.slam = true; BS.float = false; BS.slamBuf = 0; BS.slamTop = BS.top; BS.snapNow = true; // (the server wants to see the dive)
    ME.hook = null; BS.chain = null;
    v[0] *= 0.15; v[2] *= 0.15; v[1] = -WRECK.slamV;
    sfx.yeet();
  }
  const hs = Math.hypot(v[0], v[2]);
  if (BS.slam) {
    const k = Math.max(0, 1 - dt * 4);
    v[0] *= k; v[2] *= k; v[1] = Math.min(v[1], -WRECK.slamV);
  } else if (ME.onGround) {
    if (wantJump && !ME.hook) {
      v[1] = BALL.hop * (moon ? 1.6 : 1); // a small hop, it's a wrecking ball
      ME.onGround = false; ME.jumpBuf = 0;
      sfx.thunk();
    } else {
      if (hs > 0) { // low rolling resistance: let go of W and it keeps rolling for a long way
        const drop = (inp.crouch ? BALL.brake : BALL.roll + hs * BALL.rollK) * dt;
        const k = Math.max(0, hs - drop) / hs;
        v[0] *= k; v[2] *= k;
      }
      if (wl) ballPush(v, wx, wz, BALL.accel, BALL.steer, dt);
    }
  } else if (wl && ME.hook && BS.chain && BS.chain.taut) ballPump(v, wx, wz, dt);
  else if (wl) ballPush(v, wx, wz, BALL.airAccel, BALL.airSteer, dt);
  v[1] -= BALL.grav * (moon ? 0.45 : 1) * (BS.float ? BALL.floatK : 1) * dt;
  if (v[1] < BALL.floatTo) BS.float = false;
  if (ME.hook && BS.slam) { ME.hook = null; BS.chain = null; }
  holeEat(dt, now); // rubber duck black holes eat the ball's momentum too, and snap its chain near the middle
  if (ME.hook) ballHookStep(dt); else BS.chain = null;
  const sp = Math.hypot(v[0], v[1], v[2]);
  if (sp > 150) { v[0] *= 150 / sp; v[1] *= 150 / sp; v[2] *= 150 / sp; }

  const was = ME.onGround;
  const res = moveBall(p, v, dt, was);
  ME.onGround = !!res.ground && v[1] <= 0.01;
  if (ME.onGround) { BS.top = p[1]; BS.float = false; } else if (p[1] > BS.top) BS.top = p[1]; // how high you've been since you left the floor (slams)
  // third-person camera pivot: above the ball (but under any ceiling), eased so bounces don't shake the view
  const up = raycast([p[0], p[1] + WRECK.r, p[2]], [0, 1, 0], BALL.eye, BOXES);
  const wantY = p[1] + (up ? Math.max(1.3, WRECK.r + up.t - 0.35) : BALL.eye);
  if (!BS.pivotY) BS.pivotY = wantY;
  BS.pivotY += (wantY - BS.pivotY) * Math.min(1, dt * 12);
  ME.eyeH = Math.max(1.2, Math.min(7, BS.pivotY - p[1]));
  // walls: clang, sparks, bounce (moveBall already flipped the velocity)
  if (res.wall > 7 && now - BS.bonkT > 120) {
    BS.bonkT = now;
    const n = res.n, k = Math.min(1, res.wall / 30);
    sfx.clang(null, 0.35 + k * 0.65);
    fx.spray([p[0] - n[0] * BS.hw, p[1] + WRECK.r, p[2] - n[2] * BS.hw], 8 + Math.round(k * 16), [0xfff2b0, 0xffb040, 0xffffff], 6 + k * 6, 0.35, 0.09, 14, 1);
    G.shake = Math.max(G.shake, 0.25 + k * 0.5);
  }
  if (ME.onGround) {
    if (!was) {
      if (BS.slam) { slamImpact(now); return; }
      if (res.landV < -14) { // heavy landing: the ball bounces
        v[1] = -res.landV * BALL.floor;
        ME.onGround = false;
        fx.dust(p, 14); sfx.clang(null, Math.min(0.6, -res.landV / 50)); sfx.land();
        G.shake = Math.max(G.shake, Math.min(0.6, -res.landV / 50));
      } else if (res.landV < -6) { fx.dust(p, 6); sfx.land(); }
      ME.airMaxFall = 0;
      ME.groundTicks = 0;
    }
    ME.groundTicks++;
    if (ME.onGround && res.ground.pad) {
      const pd = res.ground.pad;
      v[0] += pd[0]; v[1] = pd[1]; v[2] += pd[2];
      ME.onGround = false;
      sfx.pad();
      hud.msg('BOING', 0.5);
    }
  }
}
