// Lasso (secondary weapon), the client. Hold fire to spin the loop overhead, let go to throw it; the server flies the
// loop and decides who it catches. Holding someone: this client runs their body with the shared step (shared/lasso.js)
// at 120 Hz and streams it ('lh', 30 Hz), the wheel / R / F reel the rope in and out, fire lets go (they keep all
// their speed). Being held: you go where the rope says, mash jump / WASD to wriggle free, shoot (badly).
// Everyone: the ropes, the loop opening in flight, cinched waists, flailing, tumbling, YEET trails, splat dust, live and
// in killcams. Hooks into player.js / remote.js / replay.js through G (no import cycles): G.lassoStep, G.lassoPos,
// G.lassoRemote, G.lassoDispose, G.lassoReplay, G.lassoLoopGhost.
import * as THREE from 'three';
import { LASSO, holdStep, aimDir, clampLen, flingVel, throwRange } from '/shared/lasso.js';
import { FLAGS } from '/shared/weapons.js';
import { BOXES } from '/shared/map.js';
import { stepProjectile, movePlayer, raycast } from '/shared/physics.js';
import { G } from './ctx.js';
import { net } from './net.js';
import { ME, eye, look, releaseHook } from './player.js';
import { W, vmModel } from './weapons.js';
import { hud } from './hud.js';
import { fx } from './fx.js';
import { sfx, synth } from './audio.js';
import { RP, recordEv } from './replay.js';
import { Rope, sagRope, ringPoints, honda, ropeLook, vmArm, coilGroup } from './lasso_model.js';

// every key the lasso listens to, in one place (a keybinds registry can take these over)
export const LASSO_KEYS = { reelIn: 'KeyR', reelOut: 'KeyF', release: 2, wriggle: ['Space', 'KeyW', 'KeyA', 'KeyS', 'KeyD'] }; // release: a mouse button (fire always lets go too)

const r2 = (x) => Math.round(x * 100) / 100;
const ease = (x) => { x = Math.max(0, Math.min(1, x)); return x * x * (3 - 2 * x); };
const lerp = (a, b, k) => a + (b - a) * k;
const nameOf = (id) => (id === G.myId ? 'you' : (G.names.get(id) || {}).name || '???');
const skinOf = (id) => (id === G.myId ? G.equipped : (G.skins.get(id) || {})).lasso;
const S = {
  spin: 0, spinning: false, ph: 0, whup: 0, cdUntil: 0, throwT: -1e9, relT: -1e9,
  hold: null, // I hold someone: { v, L, Lt, body: { pos, vel }, st, ay, ap, sendT, t0, ... }
  held: null, // someone holds me: { by, t0, p, v, t }
  fl: null, // I'm flying after a fling: { t0, lock, sp }
  after: null, // just let go of someone: keep predicting them for a moment so they don't jump back to old snapshots
  reelIn: false, reelOut: false, wr: 0, wrT: 0,
};
const holds = new Map(); // holder id -> { v, L, t0 }: everyone's ropes (mine too)
const flung = new Map(); // victim id -> { t0, sp, ax, rate, last }: tumbling + the YEET trail
const loops = new Map(); // loop projectile id -> it, so its spoke rope can be cleaned up when it goes

// ------------------------------------------------------------ sounds (synthesized, like everything else)
const snd = {
  whup(k, pos) { synth.whoosh(0.18, 0.06 + k * 0.16, 260 + k * 420, 700 + k * 1700, 1.5, pos); }, // one turn of the loop
  throw(pos) { synth.whoosh(0.5, 0.35, 420, 2600, 1.1, pos); synth.noise(0.28, 0.12, 'highpass', 3200, 1400, pos, 0.06); },
  zip(pos) { synth.noise(0.22, 0.18, 'bandpass', 2400, 900, pos, 0, 3); }, // rope paying out
  catch(pos) { synth.tone('sawtooth', 190, 80, 0.2, 0.22, pos); synth.noise(0.24, 0.45, 'bandpass', 900, 260, pos, 0, 2.5); synth.tone('sine', 520, 1500, 0.14, 0.14, pos, 0.04); },
  creak(pos, k = 1) { const f = 85 + Math.random() * 50; synth.tone('square', f, f * 0.7, 0.14, 0.035 * k, pos); synth.noise(0.14, 0.1 * k, 'bandpass', 520, 300, pos, 0, 7); },
  crack(pos) { synth.noise(0.045, 1, 'highpass', 2600, 7000, pos); synth.tone('square', 2200, 260, 0.05, 0.18, pos); },
  splat(pos, k) { sfx.thunk(pos); sfx.crunch(pos); synth.noise(0.35, 0.3 + k * 0.5, 'lowpass', 900, 110, pos); synth.tone('sine', 140, 40, 0.3, 0.3 + k * 0.4, pos); },
  ratchet() { synth.tone('square', 1500 + Math.random() * 300, 1300, 0.018, 0.05); },
  miss(pos) { synth.noise(0.18, 0.22, 'lowpass', 900, 200, pos); },
  slide(pos) { sfx.clang ? sfx.clang(pos, 0.4) : sfx.ricochet(pos); synth.noise(0.3, 0.25, 'highpass', 1800, 900, pos); },
};

// ------------------------------------------------------------ net
net.on('lasso', (m) => {
  if (!m || typeof m.k !== 'string') return;
  if (m.k === 'hold' || m.k === 'rel' || m.k === 'splat' || m.k === 'cut' || m.k === 'slide') recordEv(m); // killcams
  if (m.k === 'loop') spawnLoop(m);
  else if (m.k === 'lu') loopUpdate(m);
  else if (m.k === 'hold') onHold(m);
  else if (m.k === 'rel') onRel(m);
  else if (m.k === 'splat') onSplat(m, false);
  else if (m.k === 'land') onLand(m);
  else if (m.k === 'cut') onCut(m);
  else if (m.k === 'slide') onSlide(m);
  else if (m.k === 'wr') { if (m.id && S.hold && S.hold.v === m.id) S.hold.wr = m.n; else if (!m.id && S.held) S.wr = Math.max(S.wr, m.n || 0); }
});
// the body we're on the end of, from whoever holds us (relayed by the server, ~30 Hz)
net.on('lh', (m) => {
  const h = S.held;
  if (!h || !Array.isArray(m.p) || !Array.isArray(m.v)) return;
  h.p = m.p; h.v = m.v; h.t = performance.now();
});

const posOf = (id) => { if (id === G.myId) return ME.pos; const r = G.remotes.get(id); return r ? r.pos : null; };
function onHold(m) {
  const now = performance.now();
  holds.set(m.id, { v: m.v, L: m.L || 8, t0: now });
  flung.delete(m.v);
  const vp = posOf(m.v);
  snd.catch(m.v === G.myId || m.id === G.myId ? null : vp);
  if (vp) fx.dust([vp[0], vp[1] + 1, vp[2]], 6);
  if (m.id === G.myId && ME.alive) {
    S.hold = { v: m.v, L: m.L, Lt: m.L, body: { pos: m.p.slice(), vel: m.vel.slice() }, st: {}, ay: ME.yaw, ap: ME.pitch, sendT: 0, t0: now, wr: 0, creakT: 0, lastL: m.L, imp: 0 };
    S.spinning = false; S.spin = 0; W.held = false;
    hud.msg(m.rev ? `REVERSED · you've got ${nameOf(m.v)}` : `GOT ${nameOf(m.v).toUpperCase()}`, 1.1, 'brag');
    G.shake = Math.max(G.shake, 0.35);
  }
  if (m.v === G.myId && ME.alive) {
    S.held = { by: m.id, t0: now, p: m.p.slice(), v: m.vel.slice(), t: now };
    S.wr = 0; S.fl = null;
    releaseHook();
    Object.assign(W, { held: false, aimHeld: false, draw: 0, charge: 0, exhale: 0 });
    hud.msg(m.rev ? 'YOUR OWN LASSO (REVERSED)' : `LASSOED by ${nameOf(m.id)}`, 1.6, 'slip');
    G.shake = Math.max(G.shake, 0.6);
  }
}
function onRel(m) {
  const now = performance.now(), sp = Array.isArray(m.vel) ? Math.hypot(...m.vel) : 0, fling = m.why === 'fling';
  holds.delete(m.id);
  const vp = Array.isArray(m.p) ? m.p : posOf(m.v);
  if (fling && sp > 8 && m.v !== G.myId) { // they tumble off, a trail behind them if they're really going
    const v = m.vel, a = [-v[2], 0, v[0]], al = Math.hypot(a[0], a[2]) || 1;
    flung.set(m.v, { t0: now, sp, ax: [a[0] / al, 0, a[2] / al], rate: 7 + sp * 0.12, last: null, ang: 0 });
  }
  if (vp) { if (fling) snd.crack(m.id === G.myId ? null : vp); if (fling && sp >= LASSO.yeet) sfx.yeet(m.v === G.myId ? null : vp); }
  if (fling && sp >= LASSO.yeet && vp) { fx.ring([vp[0], vp[1] + 0.3, vp[2]], 3.5, 0xfff2b0, 0.35); fx.spray([vp[0], vp[1] + 1, vp[2]], 26, [0xffffff, 0xffe14d, 0xff9a3a], 9, 0.6, 0.14, 0, 2); }
  if (m.id === G.myId) {
    const h = S.hold;
    S.hold = null; S.relT = now; S.cdUntil = Math.max(S.cdUntil, now + 450);
    if (h && fling && Array.isArray(m.vel)) S.after = { v: m.v, t0: now, pos: (Array.isArray(m.p) ? m.p : h.body.pos).slice(), vel: m.vel.slice() };
    if (fling && sp >= LASSO.yeet) { hud.msg(`YEET\n${Math.round(sp)} m/s`, 1.6, 'epicbrag'); G.shake = Math.max(G.shake, 0.7); }
    else if (fling && sp > 12) hud.msg(`${Math.round(sp)} m/s`, 0.9, 'brag');
    else if (m.why === 'wriggle') hud.msg(`${nameOf(m.v)} WRIGGLED FREE`, 1.2, 'slip');
    else if (m.why === 'time') hud.msg('the rope slipped', 1, 'slip');
  }
  if (m.v === G.myId) {
    S.held = null; S.wr = 0;
    if (ME.alive && Array.isArray(m.p) && Array.isArray(m.vel)) { ME.pos = m.p.slice(); ME.vel = m.vel.slice(); ME.onGround = false; }
    if (fling && sp > 8 && ME.alive) S.fl = { t0: now, lock: 0.35, sp, landed: false };
    if (fling && sp >= LASSO.yeet) { hud.msg('YEET', 1.4, 'slip'); G.shake = 1; }
    else if (m.why === 'wriggle') hud.msg('WRIGGLED FREE', 1.2, 'brag');
  }
}
function onSplat(m, replay) {
  if (!Array.isArray(m.p)) return;
  const dup = !replay && m.by === G.myId && S.hold && S.hold.v === m.id && performance.now() - S.hold.imp < 500; // we already puffed the dust for it
  if (dup) { if (m.d) hud.msg(`SPLAT · ${m.d}`, 0.9, 'brag'); return; }
  const k = Math.min(1, (m.s - LASSO.splat[0]) / 45), p = [m.p[0], m.p[1] + (m.ax === 1 ? 0.1 : 1), m.p[2]];
  fx.dust(p, 10 + Math.round(k * 26));
  fx.impact(p, m.ax === 1 ? [0, 1, 0] : null);
  if (k > 0.3) fx.ring([m.p[0], m.p[1] + 0.2, m.p[2]], 2 + k * 3, 0xd8c39a, 0.4);
  snd.splat(m.id === G.myId ? null : m.p, k);
  if (replay) return;
  if (m.id === G.myId) { G.shake = Math.max(G.shake, 0.5 + k * 0.6); if (m.d) hud.msg(`SPLAT · ${m.s} m/s`, 0.9, 'slip'); }
  if (m.by === G.myId && m.id !== G.myId && m.d) hud.msg(`SPLAT · ${m.d}`, 0.9, 'brag');
}
function onLand(m) {
  if (m.by !== G.myId || m.id === G.myId) return;
  hud.msg(m.void ? `INTO THE VOID · ${m.d} m` : `THEY FLEW ${m.d} m`, 1.8, 'brag');
}
function onCut(m) {
  const p = m.p;
  if (Array.isArray(p)) { fx.sparks(p, null, 26, true); sfx.ting(p); }
  if (m.o === G.myId) { hud.msg('CUT', 0.9, 'slip'); S.cdUntil = performance.now() + LASSO.cd * 1000; }
  if (m.by === G.myId) hud.msg('CUT THE ROPE', 0.9, 'brag');
}
function onSlide(m) {
  if (Array.isArray(m.p)) { fx.sparks(m.p, null, 12, false); snd.slide(m.p); }
  if (G.projs.has(m.id) && G.projs.get(m.id).o === G.myId) hud.msg('TOO HEAVY', 0.9, 'slip');
}

// ------------------------------------------------------------ the loop in flight (main.js hands us every k === 'loop')
function spawnLoop(m) {
  if (!Array.isArray(m.p) || !Array.isArray(m.v)) return;
  const mesh = new THREE.Group();
  G.scene.add(mesh);
  const pr = { id: m.id, k: 'loop', o: m.o, p: m.p.slice(), v: m.v.slice(), r: LASSO.r, bounce: 0, mesh, spin: 0, ph: 0, s: m.s || 0, R: m.R || 20 };
  G.projs.set(m.id, pr);
  if (m.o === G.myId) S.cdUntil = Math.max(S.cdUntil, performance.now() + 300);
  else snd.throw(m.p);
}
function loopUpdate(m) {
  const pr = G.projs.get(m.id);
  if (!pr || pr.k !== 'loop') return;
  pr.ph = m.ph; pr.phT = performance.now();
  if (Array.isArray(m.p)) pr.p = m.p.slice();
  if (Array.isArray(m.v)) pr.v = m.v.slice();
  if (m.ph === 1) { snd.miss(pr.p); if (pr.o === G.myId) S.cdUntil = performance.now() + LASSO.cd * 1000; }
  if (m.ph === 2) snd.zip(pr.p);
}
// a loop's looks: the ring (opens up as it flies, closes again coming back), its knot, and the spoke back to the hand
function loopParts(pr) {
  if (pr.lz) return pr.lz;
  pr.mesh.clear(); // late joiners / welcome got a stand-in from buildProjectile: we draw it ourselves
  const look = ropeLook(skinOf(pr.o));
  const ring = new Rope(look, 30, 6), knot = honda(look, 1.3), spoke = new Rope(look, 20, 5);
  pr.mesh.position.set(0, 0, 0);
  pr.mesh.add(ring.mesh, knot);
  G.scene.add(spoke.mesh);
  pr.born = pr.born || performance.now();
  if (pr.ph == null) pr.ph = 0; // (late joiners get it from the welcome: still flying out)
  loops.set(pr.id, pr);
  return (pr.lz = { ring, knot, spoke, look, open: 0.25 });
}
const _u = [0, 0, 0], _v = [0, 0, 0];
export function loopFrame(pr, dt, now) {
  const L = loopParts(pr);
  if (pr.ph === 0) stepProjectile(pr, dt, BOXES, LASSO.grav);
  else if (pr.ph === 1) { pr.v[0] *= Math.exp(-3 * dt); pr.v[2] *= Math.exp(-3 * dt); stepProjectile(pr, dt, BOXES, 26); }
  else {
    const h = handOf(pr.o);
    if (h) {
      const to = [h[0] - pr.p[0], h[1] - pr.p[1], h[2] - pr.p[2]], d = Math.hypot(...to) || 1, sp = Math.min(d / dt, LASSO.back * 1.2);
      for (let k = 0; k < 3; k++) { pr.v[k] = (to[k] / d) * sp; pr.p[k] += pr.v[k] * dt; }
    }
  }
  const age = (now - pr.born) / 1000;
  // open: a tight coil leaving the hand, opening wide in the first quarter second; slack once it misses, closing
  // up as it gets reeled back in
  const want = pr.ph === 0 ? 0.28 + 0.52 * ease(age / 0.3) : pr.ph === 1 ? 0.62 : 0.2;
  L.open += (want - L.open) * Math.min(1, dt * 10);
  // the ring flies nearly flat, tipped back toward the thrower, so it can drop over someone
  const v = pr.v, hl = Math.hypot(v[0], v[2]) || 1, fwd = [v[0] / hl, 0, v[2] / hl];
  const tilt = pr.ph === 0 ? 0.35 : 0.9;
  _u[0] = fwd[0] * Math.cos(tilt); _u[1] = Math.sin(tilt); _u[2] = fwd[2] * Math.cos(tilt);
  _v[0] = -fwd[2]; _v[1] = 0; _v[2] = fwd[0];
  const n = [_u[1] * _v[2] - _u[2] * _v[1], _u[2] * _v[0] - _u[0] * _v[2], _u[0] * _v[1] - _u[1] * _v[0]];
  // the knot sits on the side facing the thrower (where the spoke pulls)
  ringPoints(L.ring.pts, pr.p, _u, _v, L.open, { seam: Math.PI, wob: pr.ph === 0 ? 0.06 : 0.12, wt: age * 9, nx: n[0], ny: n[1], nz: n[2] });
  L.ring.update(L.look.r * 1.25);
  const kp = L.ring.pts[0];
  L.knot.position.copy(kp);
  L.knot.lookAt(kp.x + _u[0], kp.y + _u[1], kp.z + _u[2]);
  L.knot.rotateY(Math.PI / 2);
  L.age = age;
  pr.mesh.visible = !RP.active;
}
// the spoke from a loop back to the thrower's hand: slack while it pays out, a ripple running down it (late pass)
function loopSpoke(pr) {
  const L = pr.lz, hand = handOf(pr.o), kp = L.ring.pts[0];
  if (!hand || RP.active) { L.spoke.mesh.visible = false; return; }
  const d = Math.hypot(kp.x - hand[0], kp.y - hand[1], kp.z - hand[2]);
  sagRope(L.spoke, hand, [kp.x, kp.y, kp.z], d * (pr.ph === 2 ? 1.04 : 1.07) + 0.3, { wave: Math.min(0.35, d * 0.02) * (pr.ph === 0 ? 1 : 0.5), wf: 3, wt: (L.age || 0) * 14, r: L.look.r, r1: L.look.r * 1.1 });
  L.spoke.mesh.visible = true;
}
// loops the server took away (caught, cut, back in the hand): their spoke goes too
function sweepLoops() {
  for (const [id, pr] of loops) if (G.projs.get(id) !== pr) { loops.delete(id); if (pr.lz) G.scene.remove(pr.lz.spoke.mesh); }
}

// ------------------------------------------------------------ hands: where a rope leaves someone's hand (world)
const _hv = new THREE.Vector3();
function handOf(id) {
  if (id === G.myId) return VM.handW || eye();
  const r = G.remotes.get(id);
  if (!r || !r.alive) return null;
  return r.muzzle();
}
// a viewmodel-space point drawn into the world exactly behind where it shows on screen (the two cameras' fov differ)
function vmToWorld(x, y, z) {
  const k = Math.tan((G.camera.fov * Math.PI) / 360) / Math.tan((G.vmCamera.fov * Math.PI) / 360);
  _hv.set(x * k, y * k, z);
  G.camera.updateMatrixWorld();
  G.camera.localToWorld(_hv);
  return [_hv.x, _hv.y, _hv.z];
}

// ------------------------------------------------------------ the fixed step (player.js calls this every 1/120 s)
// true = we moved you (you're on someone's rope, or tumbling out of a fling): the normal movement sits this step out
G.lassoStep = function (dt, inp, now) {
  if (S.hold) holdTick(dt, now);
  if (S.held) { heldTick(dt, now); return true; }
  if (S.fl && !S.fl.landed && now - S.fl.t0 < S.fl.lock * 1000) { tumbleTick(dt); return true; }
  return false;
};
function holdTick(dt, now) {
  const h = S.hold;
  if (!ME.alive) return;
  // reel: the held keys wind it smoothly, the wheel moves the target in steps, the rope eases to it
  if (S.reelIn) h.Lt -= LASSO.reel * dt;
  if (S.reelOut) h.Lt += LASSO.reel * dt;
  h.Lt = clampLen(h.Lt);
  h.L += Math.max(-14 * dt, Math.min(14 * dt, h.Lt - h.L));
  if (Math.abs(h.L - h.lastL) > 0.5) { h.lastL = h.L; snd.ratchet(); }
  // aim, smoothed over about a frame: mouse moves arrive once a frame, the spring wants the target to glide
  const k = 1 - Math.exp(-dt * 60);
  h.ay += (ME.yaw - h.ay) * k; h.ap += (ME.pitch - h.ap) * k;
  const r = holdStep(h.body, { eye: eye(), dir: aimDir(h.ay, h.ap), L: h.L, hv: ME.vel }, h.st, dt, BOXES);
  h.taut = r.taut; h.d = r.d;
  if (r.impact > LASSO.splat[0] && now - h.imp > 300) { h.imp = now; onSplat({ id: h.v, by: G.myId, s: Math.round(r.impact), ax: r.n, p: h.body.pos.slice() }, true); } // dust right away; the server decides the damage
  h.sendT -= dt;
  if (h.sendT <= 0) { h.sendT += 1 / LASSO.stream; if (h.sendT < 0) h.sendT = 0; net.send({ t: 'lh', p: h.body.pos.map(r2), v: h.body.vel.map(r2), L: r2(h.L) }); }
}
function heldTick(dt, now) {
  const h = S.held;
  // where the rope has us right now: the last sample, carried on by its velocity (a little, never far)
  const age = Math.min(0.12, (now - h.t) / 1000), k = 1 - Math.exp(-dt * 24);
  const cv = [0, 1, 2].map((i) => ((h.p[i] + h.v[i] * age - ME.pos[i]) * k) / dt);
  movePlayer(ME.pos, cv, dt, BOXES, false);
  ME.vel = h.v.slice();
  ME.onGround = false; ME.hook = null; ME.sliding = false; ME.crouching = false; ME.sprinting = false; ME.jumpBuf = 0;
  ME.eyeH += (1.6 - ME.eyeH) * Math.min(1, dt * 14);
  ME.airMaxFall = 0;
}
function tumbleTick(dt) {
  const v = ME.vel;
  v[1] -= 26 * dt;
  const res = movePlayer(ME.pos, v, dt, BOXES, false);
  ME.onGround = !!res.ground && v[1] <= 0.01;
  if (ME.onGround) S.fl.landed = true;
  ME.sliding = false; ME.crouching = false; ME.jumpBuf = 0;
}

// ------------------------------------------------------------ input (main.js forwards these)
// fire (or the release button, unless that's your grapple) while you hold someone lets go. true = we used the click
export function lassoClick(button) {
  if (!S.hold || !ME.alive || !(button === 0 || (button === LASSO_KEYS.release && !G.settings.swapAim))) return false;
  const h = S.hold;
  net.send({ t: 'lasso', k: 'rel', p: h.body.pos.map(r2), v: h.body.vel.map(r2) });
  S.relT = performance.now();
  return true;
}
// the wheel reels while you hold someone (instead of switching weapons)
export function lassoWheel(dy) {
  if (!S.hold) return false;
  S.hold.Lt = clampLen(S.hold.Lt + (dy < 0 ? 1 : -1) * LASSO.wheel); // wheel up = let it out, down = reel in
  return true;
}
// keys: R / F reel while holding, no weapon switching while your hands are on the rope; any movement key or jump
// while you're the one held is a wriggle
export function lassoKey(e, down) {
  const c = e.code;
  if (c === LASSO_KEYS.reelIn) { S.reelIn = down && !!S.hold; if (S.hold) return true; }
  if (c === LASSO_KEYS.reelOut) { S.reelOut = down && !!S.hold; if (S.hold) return true; }
  if (!down) return false;
  if (S.hold && /^(Digit[1-4]|KeyQ|KeyX)$/.test(c)) return true;
  if (S.held && !e.repeat && LASSO_KEYS.wriggle.includes(c)) wriggle();
  return false;
}
function wriggle() {
  const now = performance.now();
  if (now - S.wrT < LASSO.wrGap) return;
  S.wrT = now;
  S.wr = Math.min(0.99, S.wr + 1 / LASSO.wriggle);
  net.send({ t: 'lasso', k: 'wr' });
  G.shake = Math.max(G.shake, 0.18);
  if (Math.random() < 0.35) snd.creak(null, 0.6);
}
export const lassoBusy = () => !!S.hold; // holding someone: both hands are on the rope

// ------------------------------------------------------------ every frame (main.js, right after updateWeapons)
export function lassoFrame(dt, now) {
  const alive = G.joined && ME.alive;
  if (!alive) { if (S.hold) S.hold = null; if (S.held) S.held = null; S.spinning = false; S.spin = 0; S.fl = null; }
  if (!G.joined) { holds.clear(); flung.clear(); }
  // spin while fire is held, throw when you let go
  const trapped = now < (ME.trapUntil || 0), ball = now < (ME.ballUntil || 0);
  const loopOut = [...G.projs.values()].some((p) => p.k === 'loop' && p.o === G.myId);
  const can = alive && W.cur === 'lasso' && !S.hold && !S.held && !trapped && !ball && !loopOut && now >= S.cdUntil && now >= (W.staggerUntil || 0);
  if (can && W.held) {
    if (!S.spinning) { S.spinning = true; S.spin = 0; }
    S.spin = Math.min(1, S.spin + dt / LASSO.spinT);
  } else if (S.spinning) {
    if (can && !W.held) throwIt(now);
    S.spinning = false;
  }
  if (S.spinning) W.flags |= FLAGS.LASSO;
  // hud
  const st = S.hold ? holdHud(now) : S.held ? heldHud(now, dt) : null;
  if (!st && S.spinning) hud.meter(S.spin, `LASSO · ${Math.round(throwRange(S.spin))} m`, '#e0b070');
  else if (!st && alive && W.cur === 'lasso' && now < S.cdUntil && !loopOut && now - S.relT > 600) hud.meter(1 - (S.cdUntil - now) / (LASSO.cd * 1000), 'COILING', '#e0b070');
  G.heldSpread = S.held && alive ? LASSO.heldSpread : 0;
  // the camera: swinging on someone's rope sways you about; tumbling out of a fling rolls you over
  if (S.held && alive) {
    const v = ME.vel, sp = Math.hypot(v[0], v[1], v[2]);
    ME.lean = (ME.lean || 0) + Math.sin(now * 0.004) * 0.06 + Math.max(-0.35, Math.min(0.35, (v[0] * Math.cos(ME.yaw) - v[2] * Math.sin(ME.yaw)) * -0.01));
    if (G.punch) { G.punch.vx += Math.sin(now * 0.011) * dt * (2 + sp * 0.1); G.punch.vz += Math.sin(now * 0.007) * dt * (2 + sp * 0.12); }
    // and your aim drifts with the swing (rockets and arrows too, not just the hipfire spread)
    const k = dt * (0.5 + Math.min(1.5, sp * 0.04));
    ME.yaw += (Math.sin(now * 0.0073) * 0.6 + Math.sin(now * 0.0131 + 1) * 0.4) * k;
    ME.pitch = Math.max(-1.55, Math.min(1.55, ME.pitch + (Math.sin(now * 0.0089 + 2) * 0.5 + Math.sin(now * 0.017) * 0.3) * k * 0.6));
  }
  if (S.fl && alive) {
    const t = (now - S.fl.t0) / 1000;
    if (S.fl.landed || t > 1.6 || ME.onGround) { if (!S.fl.landed && ME.onGround) S.fl.landed = true; if (t > 0.4) S.fl = S.fl.landed ? null : S.fl; }
    if (S.fl && !S.fl.landed) { const k = Math.max(0, 1 - t / 1.6); ME.lean = (ME.lean || 0) + Math.sin(t * 7) * 0.5 * k; if (G.punch) G.punch.vx += Math.sin(t * 9) * dt * 18 * k; }
  }
  if (S.after && now - S.after.t0 > 700) S.after = null;
  if (S.after) { const a = S.after, ddt = Math.min(dt, 0.05); a.vel[1] -= 26 * ddt; movePlayer(a.pos, a.vel, ddt, BOXES, false); }
  sweepLoops();
  vmFrame(dt, now);
  for (const [id, f] of flung) if (now - f.t0 > 6000) flung.delete(id);
}
function throwIt(now) {
  const o = eye(), d = look();
  net.send({ t: 'lasso', k: 'throw', o: o.map(r2), d: d.map(r2), s: r2(S.spin) });
  S.throwT = now; S.throwS = S.spin;
  S.cdUntil = now + 350;
  snd.throw(null);
  G.shake = Math.max(G.shake, 0.15);
}
function holdHud(now) {
  const h = S.hold, sp = Math.hypot(...h.body.vel), left = Math.max(0, LASSO.time - (now - h.t0) / 1000);
  const wr = h.wr > 0.05 ? ` · ${nameOf(h.v)} is wriggling free!` : '';
  hud.meter(left / LASSO.time, `${nameOf(h.v)} · ${h.L.toFixed(0)} m rope · ${Math.round(sp)} m/s · CLICK to let go · wheel / R / F reel${wr}`, sp >= LASSO.yeet ? '#ffe14d' : '#e0b070');
  // the rope creaks when it's working hard
  if (sp > 18 && now > h.creakT) { h.creakT = now + 350 + Math.random() * 500; snd.creak(null, Math.min(1.4, sp / 40)); }
  return true;
}
function heldHud(now, dt) {
  const h = S.held;
  hud.meter(S.wr, `LASSOED by ${nameOf(h.by)} · mash SPACE / WASD to wriggle free`, '#ff7a1a');
  if (now - S.wrT > 300) S.wr = Math.max(0, S.wr - LASSO.wrDecay * dt);
  return true;
}

// ------------------------------------------------------------ first person: your hands, the coil, the loop
const VM = { root: null, key: '', handW: null };
// viewmodel poses: wrist (w) and elbow (e) in camera space, metres (x right, y up, -z ahead)
const POSE = {
  idleR: { w: [0.19, -0.15, -0.42], e: [0.29, -0.36, -0.22] },
  spinR: { w: [0.15, 0.13, -0.42], e: [0.31, -0.1, -0.26] },
  throwR: { w: [0.09, 0.03, -0.62], e: [0.22, -0.15, -0.38] },
  haulR: { w: [0.07, -0.13, -0.5], e: [0.18, -0.3, -0.27] },
  idleL: { w: [-0.2, -0.18, -0.42], e: [-0.3, -0.38, -0.22] },
  haulL: { w: [-0.03, -0.21, -0.37], e: [-0.15, -0.37, -0.16] },
};
function buildVM() {
  const sk = skinOf(G.myId), lk = G.settings.look || {}, look = ropeLook(sk);
  const key = JSON.stringify(sk || '') + (lk.skin || '') + (lk.topColor || '') + G.myColor;
  if (VM.root && VM.key === key) return VM;
  if (VM.root) G.vmScene.remove(VM.root);
  const skin = new THREE.Color(lk.skin || '#e6cba2').getHex(), sleeve = new THREE.Color(lk.topColor || G.myColor || '#3a5aa0').getHex();
  const root = new THREE.Group();
  const armR = vmArm(skin, sleeve), armL = vmArm(skin, sleeve);
  armL.scale.x = -1; // mirrored left hand
  const coil = coilGroup(look, { R: 0.1, loops: 5 });
  coil.scale.setScalar(0.85);
  coil.position.set(0, -0.01, -0.07);
  coil.rotation.set(0.25, Math.PI / 2 - 0.5, 0); // the coils face you (at an angle), hanging off the fist
  armL.add(coil);
  const loop = new Rope(look, 32, 6), spoke = new Rope(look, 12, 5), haul = new Rope(look, 10, 5), tail = new Rope(look, 12, 5);
  const knot = honda(look, 0.9);
  root.add(armR, armL, loop.mesh, spoke.mesh, haul.mesh, tail.mesh, knot);
  for (const o of [loop.mesh, spoke.mesh, haul.mesh, tail.mesh]) o.renderOrder = 1;
  G.vmScene.add(root);
  Object.assign(VM, { root, key, armR, armL, coil, loop, spoke, haul, tail, knot, look, ph: 0, spinK: 0, haulK: 0, open: 0.16, rec: 0, sway: [0, 0] });
  return VM;
}
const _a = new THREE.Vector3(), _b = new THREE.Vector3(), _c = new THREE.Vector3(), _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _up = new THREE.Vector3(0, 1, 0);
// point an arm group at a camera-space target (its grip sits at -z, the forearm runs back along +z)
function aimArm(arm, at, roll = 0) {
  _a.copy(arm.position); _b.copy(at);
  _m.lookAt(_a, _b, _up);
  arm.quaternion.setFromRotationMatrix(_m);
  if (roll) arm.rotateZ(roll);
}
function vmFrame(dt, now) {
  const show = G.joined && ME.alive && !RP.active && (W.cur === 'lasso' || !!S.hold) && !(now < (ME.ballUntil || 0)) && !W.scoped;
  const gm = vmModel('lasso');
  if (gm) gm.wrap.visible = false; // we draw our own
  if (!show) { if (VM.root) VM.root.visible = false; VM.grip = null; VM.handW = null; return; }
  const V = buildVM();
  V.root.visible = true;
  if (S.hold) { const m = vmModel(W.cur); if (m && W.cur !== 'lasso') m.wrap.visible = false; } // reversed onto you with a gun out: it goes away while you hold the rope
  const spinning = S.spinning, holding = !!S.hold;
  V.spinK += ((spinning ? 1 : 0) - V.spinK) * Math.min(1, dt * 9);
  V.haulK += ((holding ? 1 : 0) - V.haulK) * Math.min(1, dt * 12);
  const tT = (now - S.throwT) / 1000, rT = (now - S.relT) / 1000;
  const throwK = tT < 0.45 ? Math.sin(Math.min(1, tT / 0.45) * Math.PI) : 0;
  const recoilK = rT < 0.5 ? Math.sin(Math.min(1, rT / 0.5) * Math.PI) * (1 - rT) : 0;
  const draw = W.swap || 0, bob = Math.sin(W.bob) * (ME.onGround ? Math.min(1, Math.hypot(ME.vel[0], ME.vel[2]) / 10) : 0);
  const sx = W.swayX || 0, sy = W.swayY || 0;
  // spin speed: turns a second, and one whup of air each turn
  const rps = 1.1 + 2.4 * S.spin;
  if (spinning) {
    V.ph += rps * Math.PI * 2 * dt;
    if (V.ph > (S.whup + 1) * Math.PI * 2) { S.whup = Math.floor(V.ph / (Math.PI * 2)); snd.whup(S.spin, null); }
  } else if (V.spinK < 0.02) { V.ph = 0; S.whup = 0; } // the next spin starts from the loop hanging still
  // ---- the hands. each pose is a wrist and an elbow (the forearm runs between them, off the bottom of the screen),
  // camera space. right: the loop hand (hanging the loop at your side, up and circling while it spins, thrust out on
  // the throw, on the rope while you hold someone). left: the coil hand (behind the right one on the rope when you haul)
  const blend = (a, b, k) => [lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k)];
  const cr = 0.03 + 0.02 * S.spin, circ = [Math.cos(V.ph) * cr, Math.sin(V.ph) * cr * 0.5, Math.sin(V.ph) * cr];
  let wR = blend(POSE.idleR.w, POSE.spinR.w.map((x, i) => x + circ[i]), V.spinK), eR = blend(POSE.idleR.e, POSE.spinR.e, V.spinK);
  wR = blend(wR, POSE.haulR.w, V.haulK); eR = blend(eR, POSE.haulR.e, V.haulK);
  wR = blend(wR, POSE.throwR.w, throwK); eR = blend(eR, POSE.throwR.e, throwK);
  let wL = blend(POSE.idleL.w, POSE.haulL.w, V.haulK), eL = blend(POSE.idleL.e, POSE.haulL.e, V.haulK);
  // everything on top: look lag, walk bob, drawing it, the release jerk
  const off = [sx * 0.2 + Math.sin(W.bob) * 0.008 * bob, -draw * 0.3 - sy * 0.12 + Math.abs(Math.cos(W.bob)) * 0.01 * bob + recoilK * 0.06, recoilK * 0.1];
  for (const v of [wR, eR, wL, eL]) for (let i = 0; i < 3; i++) v[i] += off[i];
  // the rope tugs your hands toward them when it's working hard (and jitters with it)
  const hb = S.hold && S.hold.body, tug = hb ? Math.min(1, Math.hypot(...hb.vel) / 50) : 0;
  if (holding && S.hold.taut) { const j = (Math.random() - 0.5) * 0.008 * tug; wR[2] -= 0.03 * tug; wR[0] += j; wR[1] += j; wL[2] -= 0.02 * tug; }
  V.armR.position.set(wR[0], wR[1], wR[2]);
  V.armL.position.set(wL[0], wL[1], wL[2]);
  if (holding) { // both hands point down the rope at them (never back past your shoulders)
    const w = [hb.pos[0], hb.pos[1] + LASSO.waist, hb.pos[2]];
    _c.set(w[0], w[1], w[2]); G.camera.updateMatrixWorld(); G.camera.worldToLocal(_c);
    const k = Math.tan((G.vmCamera.fov * Math.PI) / 360) / Math.tan((G.camera.fov * Math.PI) / 360);
    _c.set(_c.x * k, _c.y * k, Math.min(_c.z, -0.3)).normalize();
    const pull = [lerp(wR[0] - eR[0], _c.x, V.haulK), lerp(wR[1] - eR[1], _c.y, V.haulK), lerp(wR[2] - eR[2], _c.z, V.haulK)];
    aimArm(V.armR, _b.set(wR[0] + pull[0], wR[1] + pull[1], wR[2] + pull[2]), -0.5);
    aimArm(V.armL, _b.set(wL[0] + (wR[0] - wL[0]) * 2 + pull[0] * 0.3, wL[1] + (wR[1] - wL[1]) * 2 + pull[1] * 0.3, wL[2] + (wR[2] - wL[2]) * 2 + pull[2] * 0.3), 0.5);
  } else {
    aimArm(V.armR, _b.set(wR[0] * 2 - eR[0], wR[1] * 2 - eR[1], wR[2] * 2 - eR[2]), -0.6 + V.spinK * 0.9);
    aimArm(V.armL, _b.set(wL[0] * 2 - eL[0], wL[1] * 2 - eL[1], wL[2] * 2 - eL[2]), 0.6);
  }
  V.root.updateMatrixWorld(true);
  const gR = V.armR.localToWorld(V.armR.userData.grip.clone()), gL = V.armL.localToWorld(V.armL.userData.grip.clone());
  // ---- the loop: hanging under the hand at rest, circling overhead while it spins, gone once it's thrown
  const thrown = tT < 0.6 || rT < 0.35 || [...G.projs.values()].some((p) => p.k === 'loop' && p.o === G.myId);
  V.loop.mesh.visible = !holding && !thrown; V.knot.visible = V.loop.mesh.visible;
  V.spoke.mesh.visible = V.loop.mesh.visible;
  if (V.loop.mesh.visible) {
    const openTo = lerp(0.12, 0.36 + 0.14 * S.spin, V.spinK);
    V.open += (openTo - V.open) * Math.min(1, dt * 8);
    // spin plane: overhead and in front, tipped toward you so the near side dips into view at the top of the screen
    const cHang = [gR.x - 0.01, gR.y - 0.15, gR.z - 0.03], cSpin = [0.05, 0.27, -0.72];
    const c = cHang.map((x, i) => lerp(x, cSpin[i], V.spinK));
    const tip = lerp(1.45, 0.42, V.spinK); // hanging: the ring's nearly vertical; spinning: tipped toward you
    const u = [Math.cos(V.ph), 0, Math.sin(V.ph)], vv = [-Math.sin(V.ph), 0, Math.cos(V.ph)];
    // tip the whole ring about the camera's x axis
    const rot = (p) => [p[0], p[1] * Math.cos(tip) - p[2] * Math.sin(tip), p[1] * Math.sin(tip) + p[2] * Math.cos(tip)];
    const uu = rot(u), vw = rot(vv);
    const swing = Math.sin(now * 0.003) * 0.2 * (1 - V.spinK) + sx * 2 * (1 - V.spinK);
    const uS = [uu[0] * Math.cos(swing) - uu[1] * Math.sin(swing), uu[0] * Math.sin(swing) + uu[1] * Math.cos(swing), uu[2]];
    const n = [uS[1] * vw[2] - uS[2] * vw[1], uS[2] * vw[0] - uS[0] * vw[2], uS[0] * vw[1] - uS[1] * vw[0]];
    ringPoints(V.loop.pts, c, uS, vw, V.open, { seam: lerp(Math.PI / 2, Math.PI, V.spinK), wob: 0.04 + V.spinK * 0.05, wt: now * 0.01, nx: n[0], ny: n[1], nz: n[2], tear: 0.22 });
    V.loop.update(V.look.r * 0.9);
    const kp = V.loop.pts[0];
    V.knot.position.copy(kp);
    // the spoke: hand to knot, a little slack
    const d = gR.distanceTo(kp);
    sagRope(V.spoke, [gR.x, gR.y, gR.z], [kp.x, kp.y, kp.z], d * 1.03, { r: V.look.r * 0.9 });
  }
  // ---- hauling: the rope runs from the left hand through the right one; the tail drops off to the coil
  V.haul.mesh.visible = V.haulK > 0.3;
  V.tail.mesh.visible = true;
  if (V.haul.mesh.visible) sagRope(V.haul, [gL.x, gL.y, gL.z], [gR.x, gR.y, gR.z], gL.distanceTo(gR) * (S.hold && S.hold.taut ? 1.0 : 1.08), { r: V.look.r * 0.9 });
  const cw = V.coil.localToWorld(_a.set(0, -0.08, 0));
  sagRope(V.tail, [gL.x, gL.y, gL.z], [cw.x, cw.y, cw.z], gL.distanceTo(cw) * 1.25, { r: V.look.r * 0.85 });
  VM.grip = [gR.x, gR.y, gR.z]; // the world end of your rope starts exactly behind it on screen (worked out in lassoLate)
}

// ------------------------------------------------------------ ropes between two people (a late pass: main.js calls
// lassoLate after everyone has moved this frame, replays after their ghosts have, so a fast victim never drags a
// frame behind their rope)
const mine = { rope: null, cinch: null };
const _ru = [0, 0, 0], _rv = [0, 0, 0];
const SC = (r) => 1.2 * (r.distScale || 1); // remotes are drawn 1.2x (more far away)
const WAIST_V = 1.08; // where the loop cinches on a mannequin (its own units, before that scale)
// the loop pulled tight round someone's waist (w), its knot facing the rope (toward `from`). s = how big they're
// drawn. returns the knot
function cinchRing(rope, w, from, s) {
  let dx = from[0] - w[0], dz = from[2] - w[2];
  const dl = Math.hypot(dx, dz) || 1; dx /= dl; dz /= dl;
  _ru[0] = dx; _ru[1] = 0; _ru[2] = dz; _rv[0] = -dz; _rv[1] = 0; _rv[2] = dx;
  ringPoints(rope.pts, w, _ru, _rv, 0.2 * s, { seam: 0, tear: 0.25, nx: 0, ny: 1, nz: 0 });
  rope.update(rope.look.r * 1.05 * s);
  rope.mesh.visible = true;
  const p = rope.pts[0];
  return [p.x, p.y, p.z];
}
function partsOf(r) { // the ropes a remote (or replay ghost) owns
  let z = r.lzv;
  if (!z) {
    z = r.lzv = {};
    for (const k of ['rope', 'cinch', 'over', 'spoke']) { z[k] = new Rope(ropeLook(r.skins && r.skins.lasso), k === 'rope' ? 30 : 22, 5); z[k].mesh.visible = false; G.scene.add(z[k].mesh); }
  }
  const look = ropeLook(r.skins && r.skins.lasso);
  if (z.rope.look !== look) for (const k of ['rope', 'cinch', 'over', 'spoke']) z[k].setLook(look);
  return z;
}
function mineParts() {
  const look = ropeLook(skinOf(G.myId));
  if (!mine.rope) { mine.rope = new Rope(look, 32, 6); mine.cinch = new Rope(look, 22, 5); G.scene.add(mine.rope.mesh, mine.cinch.mesh); }
  mine.rope.setLook(look); mine.cinch.setLook(look);
  return mine;
}
// one holder -> victim pair: the cinch round the victim, the rope from the holder's hand to its knot
function drawPair(hand, rope, vw, vs, cinch, L, o) {
  const knot = cinchRing(cinch, vw, hand, vs);
  sagRope(rope, hand, knot, Math.max(0.5, L - 0.4), o);
  rope.mesh.visible = true;
}
export function lassoLate(dt, now, ghosts) {
  const mp = mineParts();
  if (!ghosts) { VM.handW = VM.grip ? vmToWorld(VM.grip[0], VM.grip[1], VM.grip[2]) : null; for (const pr of loops.values()) if (pr.lz && G.projs.get(pr.id) === pr) loopSpoke(pr); }
  const used = new Set();
  const use = (rp) => used.add(rp);
  if (ghosts) { // a replay: the ghosts carry who holds who
    for (const g of ghosts.values()) {
      const v = g.lzHold;
      if (!v || !g.alive || !v.alive || !g.ch.root.visible || !v.buf.length) continue;
      const z = partsOf(g), zv = partsOf(v), s = SC(v);
      drawPair(g.muzzle(), z.rope, [v.pos[0], v.pos[1] + WAIST_V * s, v.pos[2]], s, zv.cinch, g.lzHoldL || 8, { r: z.rope.look.r * 1.15 });
      use(z.rope); use(zv.cinch);
    }
  } else if (G.joined && !RP.active) {
    for (const [hid, h] of holds) {
      const hr = hid === G.myId ? null : G.remotes.get(hid);
      if (hid !== G.myId && (!hr || !hr.alive || !hr.ch.root.visible)) continue;
      const hand = hid === G.myId ? VM.handW : hr.muzzle();
      if (!hand) continue;
      let vw, vs, cinch;
      if (h.v === G.myId) { if (!ME.alive) continue; vw = [ME.pos[0], ME.pos[1] + LASSO.waist, ME.pos[2]]; vs = 1; cinch = mp.cinch; }
      else { const vr = G.remotes.get(h.v); if (!vr || !vr.alive || !vr.buf.length) continue; vs = SC(vr); vw = [vr.pos[0], vr.pos[1] + WAIST_V * vs, vr.pos[2]]; cinch = partsOf(vr).cinch; }
      const rope = hid === G.myId ? mp.rope : partsOf(hr).rope;
      const L = hid === G.myId && S.hold ? S.hold.L : h.L;
      const sp = hid === G.myId && S.hold ? Math.hypot(...S.hold.body.vel) : 0;
      drawPair(hand, rope, vw, vs, cinch, L, { r: rope.look.r * (hid === G.myId ? 1 : 1.15), hum: hid === G.myId && S.hold && S.hold.taut ? Math.min(0.04, sp * 0.0008) : 0, wt: now * 0.05 });
      use(rope); use(cinch);
    }
    // just let go: your rope whips back to your hand
    const rT = (now - S.relT) / 1000, a = S.after;
    if (!S.hold && a && rT < 0.35 && VM.handW) {
      const k = ease(rT / 0.35), w = [a.pos[0], a.pos[1] + LASSO.waist, a.pos[2]];
      const end = w.map((x, i) => lerp(x, VM.handW[i], k));
      sagRope(mp.rope, VM.handW, end, Math.hypot(...end.map((x, i) => x - VM.handW[i])) * 1.15 + 0.2, { r: mp.rope.look.r, wave: 0.6 * (1 - k), wf: 4, wt: rT * 40 });
      mp.rope.mesh.visible = true; use(mp.rope);
    }
  }
  // everything nobody drew this frame goes away (all of the live ones while a replay has the screen)
  if (!used.has(mp.rope)) mp.rope.mesh.visible = false;
  if (!used.has(mp.cinch)) mp.cinch.mesh.visible = false;
  for (const r of ghosts ? ghosts.values() : G.remotes.values()) {
    const z = r.lzv;
    if (!z) continue;
    if (!used.has(z.rope)) z.rope.mesh.visible = false;
    if (!used.has(z.cinch)) z.cinch.mesh.visible = false;
    if (!ghosts && RP.active) { z.over.mesh.visible = false; z.spoke.mesh.visible = false; }
  }
}
G.lassoLate = lassoLate; // replay.js draws its ghosts' ropes with it

// ------------------------------------------------------------ everyone else's bodies (remote.js calls these)
// after the interpolation: the one you hold is wherever your own simulation has them (no 110 ms lag), and the one
// you just flung keeps flying on your prediction for a moment, easing back onto the snapshots
G.lassoPos = function (r, now) {
  if (r.ghost) return;
  const h = S.hold;
  if (h && h.v === r.id) { r.pos[0] = h.body.pos[0]; r.pos[1] = h.body.pos[1]; r.pos[2] = h.body.pos[2]; r.vel = h.body.vel.slice(); return; }
  const a = S.after;
  if (a && a.v === r.id) { const k = 1 - Math.min(1, (now - a.t0) / 700); for (let i = 0; i < 3; i++) r.pos[i] = lerp(r.pos[i], a.pos[i], k); }
};
// who r holds right now (live: the 'hold' events; replays: the ghost carries it), and who holds r
function victimPos(r) {
  if (r.ghost) { const g = r.lzHold; return g && g.alive && g.buf.length ? g.pos : null; }
  const h = holds.get(r.id);
  if (!h) return null;
  if (h.v === G.myId) return ME.alive ? ME.pos : null;
  const v = G.remotes.get(h.v);
  return v && v.alive && v.buf.length ? v.pos : null;
}
function heldBy(r) {
  if (r.ghost) return r.lzBy && r.lzBy.alive ? r.lzBy.pos : null;
  for (const [hid, h] of holds) if (h.v === r.id) return hid === G.myId ? ME.pos : (G.remotes.get(hid) || {}).pos || null;
  return null;
}
const _lp = new THREE.Vector3(), _yq = new THREE.Quaternion(), _Y = new THREE.Vector3(0, 1, 0);
G.lassoRemote = function (r, dt, now) {
  const ch = r.ch, show = ch.root.visible && r.alive, t = now * 0.001 + r.id;
  const vp = show ? victimPos(r) : null, spun = show && !!(r.f & FLAGS.LASSO), hp = show ? heldBy(r) : null, f = r.ghost ? r.lzFl : flung.get(r.id);
  if (!r.lzv && !vp && !spun && !hp && !f && r.w !== 'lasso') return; // nothing to do with a lasso: no ropes made for them
  const z = partsOf(r);
  // ---- r holds someone: both arms reach down the rope at them
  if (vp) {
    const dx = vp[0] - r.pos[0], dy = vp[1] + 1 - (r.pos[1] + 1.6), dz = vp[2] - r.pos[2], hd = Math.hypot(dx, dz) || 1;
    let rel = Math.atan2(-dx, -dz) - r.yaw; while (rel > Math.PI) rel -= Math.PI * 2; while (rel < -Math.PI) rel += Math.PI * 2;
    const pitch = Math.atan2(dy, hd), yy = Math.max(-1.2, Math.min(1.2, rel));
    ch.arm.rotation.x = pitch; ch.arm.rotation.y = yy;
    ch.armL.rotation.x = pitch; ch.armL.rotation.y = yy * 0.8; ch.armL.rotation.z = 0;
  }
  // ---- spinning the loop overhead
  const spinning = spun && !vp;
  const lp = r.weaponMesh && r.weaponMesh.userData.loopParts; // the loop hanging off their coil goes while it's out
  if (lp) { const out = !!vp || spinning || [...G.projs.values()].some((p) => p.k === 'loop' && p.o === r.id); for (const o of lp) o.visible = !out; }
  z.over.mesh.visible = spinning; z.spoke.mesh.visible = spinning;
  if (spinning) {
    z.ph = (z.ph || 0) + dt * Math.PI * 2 * 2.6;
    const s = SC(r), c = [r.pos[0] - Math.sin(r.yaw) * 0.2 * s, r.pos[1] + 2.3 * s, r.pos[2] - Math.cos(r.yaw) * 0.2 * s];
    const tip = 0.25, u = [Math.cos(z.ph), Math.sin(z.ph) * Math.sin(tip), Math.sin(z.ph) * Math.cos(tip)], v = [-Math.sin(z.ph), Math.cos(z.ph) * Math.sin(tip), Math.cos(z.ph) * Math.cos(tip)];
    ringPoints(z.over.pts, c, u, v, 0.5 * s, { seam: 0, wob: 0.05, wt: t * 8, nx: 0, ny: 1, nz: 0 });
    z.over.update(z.over.look.r * s);
    ch.arm.rotation.x = 1.75 + Math.sin(z.ph) * 0.15; ch.arm.rotation.y = Math.cos(z.ph) * 0.25;
    ch.root.updateMatrixWorld(true);
    const hand = r.muzzle(), kp = z.over.pts[0];
    sagRope(z.spoke, hand, [kp.x, kp.y, kp.z], Math.hypot(kp.x - hand[0], kp.y - hand[1], kp.z - hand[2]) * 1.02, { r: z.spoke.look.r * s * 0.85 });
  }
  // ---- r is on the end of someone's rope: arms and legs everywhere, bent toward the rope (hanging off it by the middle)
  if (hp) {
    flail(ch, t, Math.min(1, Math.hypot(...r.vel) / 30));
    const dx = hp[0] - r.pos[0], dz = hp[2] - r.pos[2], dy = hp[1] - r.pos[1], hl = Math.hypot(dx, dz) || 1;
    const fwd = (-Math.sin(r.yaw) * dx - Math.cos(r.yaw) * dz) / hl, side = (Math.cos(r.yaw) * dx - Math.sin(r.yaw) * dz) / hl;
    const pull = Math.min(1, Math.max(0.2, 1 - dy / 12));
    ch.body.rotation.x = -fwd * 0.55 * pull; ch.body.rotation.z = -side * 0.55 * pull;
  }
  // ---- flung: head over heels until they land
  if (f && show && !hp && !f.down) {
    const age = (now - f.t0) / 1000;
    const floor = Math.abs(r.vel[1]) < 1.5 && age > 0.25 && !!raycast([r.pos[0], r.pos[1] + 0.3, r.pos[2]], [0, -1, 0], 0.6, BOXES);
    if (floor || age > 4) { f.down = now; ch.root.rotation.set(0, r.yaw, 0); }
    else {
      f.ang += dt * f.rate;
      const s = SC(r), W0 = WAIST_V * s;
      ch.root.quaternion.setFromAxisAngle(_Y, r.yaw).premultiply(_yq.setFromAxisAngle(_lp.set(f.ax[0], f.ax[1], f.ax[2]), f.ang));
      _lp.set(0, W0, 0).applyQuaternion(ch.root.quaternion); // spin round the waist, not the feet
      ch.root.position.set(r.pos[0] - _lp.x, r.pos[1] + W0 - _lp.y, r.pos[2] - _lp.z);
      flail(ch, t * 1.6, 1);
      // the YEET trail while they're really going
      const c = [r.pos[0], r.pos[1] + 1.1, r.pos[2]], sp = Math.hypot(...r.vel);
      if (f.last && sp > 22 && age < 4) {
        const k = Math.min(1, (sp - 22) / 50);
        fx.tracer(f.last, c, k > 0.6 ? 0xfff2b0 : k > 0.3 ? 0xffc04a : 0xff8a3a, 0.08 + k * 0.14, 0.45 + k * 0.3);
        if (Math.random() < dt * 30 * k) fx.spray(c, 1, [0xffffff, 0xffe14d], 2, 0.4, 0.1, 0, 3);
      }
      f.last = c;
    }
  }
};
// arms up and windmilling, legs kicking (k = how frantic)
function flail(ch, t, k) {
  ch.arm.rotation.x = 2.3 + Math.sin(t * 9) * 0.6 * (0.5 + k); ch.arm.rotation.y = Math.sin(t * 7) * 0.5;
  ch.armL.rotation.x = 2.1 + Math.sin(t * 8 + 1.3) * 0.6 * (0.5 + k); ch.armL.rotation.z = 0.6 + Math.sin(t * 6) * 0.4;
  ch.legL.rotation.x = Math.sin(t * 11) * (0.5 + 0.5 * k); ch.legR.rotation.x = -Math.sin(t * 11 + 0.4) * (0.5 + 0.5 * k);
  ch.kneeL.rotation.x = 0.5 + Math.sin(t * 11 + 1) * 0.5; ch.kneeR.rotation.x = 0.5 - Math.sin(t * 11 + 1.4) * 0.5;
  ch.head.rotation.x = Math.sin(t * 5) * 0.3;
}
G.lassoDispose = function (r) {
  const z = r.lzv;
  if (!z) return;
  for (const k of ['rope', 'cinch', 'over', 'spoke']) if (z[k]) G.scene.remove(z[k].mesh);
  r.lzv = null;
};

// ------------------------------------------------------------ killcams (replay.js calls these)
// the 'lasso' events replay onto the ghosts: who holds who (the rope + cinch get drawn by lassoRemote), the fling
// tumble, splat dust, the cut
G.lassoReplay = function (m, ghosts) {
  const H = ghosts.get(m.id), V = ghosts.get(m.v);
  if (m.k === 'hold') {
    if (H) { H.lzHold = V || null; H.lzHoldL = m.L; }
    if (V) V.lzBy = H || null;
  } else if (m.k === 'rel') {
    if (H) H.lzHold = null;
    if (V) { V.lzBy = null; if (m.why === 'fling' && Array.isArray(m.vel) && Math.hypot(...m.vel) > 8) ghostFling(V, m); }
    if (m.why === 'fling' && Array.isArray(m.p)) snd.crack(m.p);
  } else if (m.k === 'splat') onSplat(m, true);
  else if (m.k === 'cut' && Array.isArray(m.p)) { fx.sparks(m.p, null, 26, true); sfx.ting(m.p); }
  else if (m.k === 'slide' && Array.isArray(m.p)) fx.sparks(m.p, null, 12, false);
};
// ghosts tumble + trail like the real thing (lassoRemote reads r.lzFl on ghosts)
function ghostFling(g, m) {
  const v = m.vel, a = [-v[2], 0, v[0]], al = Math.hypot(a[0], a[2]) || 1, sp = Math.hypot(...v);
  g.lzFl = { t0: performance.now(), sp, ax: [a[0] / al, 0, a[2] / al], rate: 7 + sp * 0.12, ang: 0, last: null };
  if (sp >= LASSO.yeet) sfx.yeet(m.p);
}
// the loop flying in a replay: open ring + knot from buildProjectile, laid flat along its flight
G.lassoLoopGhost = function (mesh, vx, vy, vz) {
  const hl = Math.hypot(vx, vz);
  if (hl > 0.01) mesh.rotation.set(0, Math.atan2(vx, vz), 0);
  mesh.rotateX(-0.35);
};
