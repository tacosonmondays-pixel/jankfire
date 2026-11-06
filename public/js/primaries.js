// The new primaries, client side: nails that stay in walls + people pinned to them (Nail Gun), predicted bouncing
// tennis balls with a THWOCK per bounce (Tennis Ball Launcher), and shopping carts: drawn, parked carts made solid,
// and riding one (Shopping Cart Cannon). The server decides every hit, pin, bounce count and plough; this draws it
// and drives the cart you're standing in (movement is the client's, like walking).
import * as THREE from 'three';
import { G } from './ctx.js';
import { ME, C } from './player.js';
import { net } from './net.js';
import { sfx, synth } from './audio.js';
import { fx } from './fx.js';
import { hud } from './hud.js';
import { BOXES } from '/shared/map.js';
import { WEAPONS } from '/shared/weapons.js';
import { raycast, resetGrid, movePlayer } from '/shared/physics.js';
import { NAILS, CART, cartBox, stepBall, yawOfV } from '/shared/primaries.js';
import { buildCart } from './models.js';
import { nailMesh } from './primmodels.js';
import { recordEv, RP, RP_HOOKS } from './replay.js';

const TW = WEAPONS.tennis;
const R2 = (x) => Math.round(x * 100) / 100;
const near = (p, d = 30) => Math.hypot(p[0] - ME.pos[0], p[1] - ME.pos[1], p[2] - ME.pos[2]) < d;

// ------------------------------------------------------------ sounds (synthesized, like everything else)
const { tone, noise } = synth;
Object.assign(sfx, {
  // pneumatic: a hiss, the driver's THUNK and a tick as the next nail feeds
  nail(pos) { noise(0.06, 0.45, 'highpass', 3500, 6500, pos); tone('square', 900, 160, 0.035, 0.32, pos); tone('sine', 140, 60, 0.05, 0.35, pos); tone('triangle', 2400, 2300, 0.012, 0.08, pos, 0.05); },
  nailWall(pos) { tone('triangle', 3200 + Math.random() * 800, 2600, 0.03, 0.06, pos); },
  pinned(pos) { for (let i = 0; i < 4; i++) { tone('square', 700, 120, 0.04, 0.3, pos, i * 0.06); noise(0.03, 0.3, 'highpass', 2500, 5000, pos, i * 0.06); } tone('sawtooth', 220, 110, 0.4, 0.1, pos, 0.26); },
  // THWOCK: a hollow felt pop, a little higher with every bounce
  thwock(pos, k = 0) { const f = 420 + k * 70; tone('sine', f * 1.6, f * 0.55, 0.09, 0.5, pos); tone('triangle', f * 3.1, f * 2, 0.03, 0.18, pos); noise(0.05, 0.35, 'bandpass', 900 + k * 200, 500, pos, 0, 1.4); },
  tennisFire(pos) { noise(0.12, 0.55, 'lowpass', 1600, 200, pos); sfx.thwock(pos, 0); tone('sine', 90, 50, 0.12, 0.4, pos); },
  // a cannon full of supermarket: the air blast, then the cart rattling out
  cartFire(pos) { noise(0.35, 0.9, 'lowpass', 1400, 60, pos); tone('sine', 85, 30, 0.35, 0.8, pos); sfx.cartRattle(pos, 1, 0.08); },
  cartRattle(pos, k = 1, delay = 0) { for (let i = 0; i < 7; i++) { const f = 1700 + Math.random() * 2600; tone('square', f, f * 0.85, 0.02, 0.05 * k, pos, delay + i * 0.03 + Math.random() * 0.02); } },
  cartCrash(pos, k = 1) { sfx.cartRattle(pos, 2.2); noise(0.25, 0.8 * k, 'bandpass', 1600, 700, pos, 0, 0.9); tone('sine', 120, 40, 0.22, 0.6 * k, pos); },
});
const gun0 = sfx.gun;
sfx.gun = (id, pos, k) => (id === 'nailgun' ? sfx.nail(pos) : gun0.call(sfx, id, pos, k));

// ------------------------------------------------------------ Nail Gun: nails in walls, people on walls
const nails = []; // { m, until }
function addNail(p, dir, big = 1) {
  const m = nailMesh();
  m.scale.setScalar(big);
  const out = 0.022 * big; // the head sticks out a little
  m.position.set(p[0] - dir[0] * out, p[1] - dir[1] * out, p[2] - dir[2] * out);
  m.lookAt(m.position.x - dir[0], m.position.y - dir[1], m.position.z - dir[2]); // +z away from the wall = the shank goes in
  m.rotateX((Math.random() - 0.5) * 0.35); m.rotateY((Math.random() - 0.5) * 0.35); // never quite straight
  G.scene.add(m);
  nails.push({ m, until: performance.now() + NAILS.stick * 1000 });
  while (nails.length > 160) G.scene.remove(nails.shift().m);
  return m;
}
// a burst of nail gun shots (yours or theirs): every one that ended in a wall leaves a nail there
export function nailSegs(segs) {
  for (const s of segs || []) {
    if (!Array.isArray(s) || s.length < 6) continue;
    const a = s.slice(0, 3), d = [s[3] - a[0], s[4] - a[1], s[5] - a[2]], L = Math.hypot(...d);
    if (L < 0.2) continue;
    const dir = d.map((x) => x / L), h = raycast(a, dir, L + 0.06, BOXES);
    if (!h || h.t < L - 0.12) continue; // ended on a person, not a wall
    addNail(h.point, dir);
    if (Math.random() < 0.3) sfx.nailWall(h.point);
  }
}
const pins = []; // { nails: [...], until }
function pinFx(m) {
  const n = performance.now(), p = m.p, list = [], into = m.n && m.n[1] === 0 ? [-m.n[0], 0, -m.n[2]] : [0, -1, 0];
  // big comedy nails through the sleeves, the trousers and the hood
  const spots = into[1] ? [[0.3, 0.05, 0.2], [-0.3, 0.05, -0.2], [0.2, 0.05, -0.3], [-0.2, 0.05, 0.3]] : [[0.35, 1.5, 0], [-0.35, 1.5, 0], [0.18, 0.5, 0], [-0.18, 0.5, 0], [0, 2.05, 0]];
  const side = [into[2], 0, -into[0]]; // across the wall
  for (const [s, y, f] of spots) {
    const at = into[1] ? [p[0] + s, p[1] + y, p[2] + f] : [p[0] + side[0] * s - into[0] * 0.05, p[1] + y, p[2] + side[2] * s - into[2] * 0.05];
    list.push(addNail(at, into, 2.2));
  }
  pins.push({ list, until: n + (m.dur || NAILS.dur) * 1000 + 400 });
  fx.impact([p[0], p[1] + 1.1, p[2]], into.map((x) => -x));
  fx.spray([p[0], p[1] + 1.1, p[2]], 14, [0xd8dde4, 0xff6f3c], 4, 0.5, 0.08, 8, 1);
  sfx.pinned(p);
}
net.on('pin', (m) => {
  recordEv(m);
  if (!Array.isArray(m.p)) return;
  pinFx(m);
  if (m.id === G.myId) {
    ME.pin = { p: m.p.slice(), until: performance.now() + (m.dur || 1) * 1000 };
    ME.hook = null;
    if (ME.ride) hopOff(false);
    hud.msg(m.n && m.n[1] === 0 ? 'NAILED TO THE WALL' : 'NAILED TO THE FLOOR', m.dur || 1, 'slip');
    G.shake = Math.max(G.shake, 0.6);
  } else if (m.by === G.myId) hud.msg('PINNED!', 0.9, 'brag');
});
// pinned: you hang where the nails put you (others can still shoot you, and you can still shoot back)
export function pinStep(now) {
  const p = ME.pin;
  if (!p) return false;
  if (now > p.until || !ME.alive) { ME.pin = null; return false; }
  for (let i = 0; i < 3; i++) ME.vel[i] = Math.max(-30, Math.min(30, (p.p[i] - ME.pos[i]) * 14));
  ME.onGround = false; ME.hook = null; ME.jumpBuf = 0;
  return true;
}

// ------------------------------------------------------------ Tennis Ball Launcher
// the client flies balls with the same bounce step as the server; 'pu' corrects them after every real bounce
const BOUNCE_COLS = [0xd4ff3a, 0xffe14d, 0xffb31a, 0xff7a1a, 0xff3b3b, 0xff00dc];
export function tennisStep(pr, dt) {
  pr.b ||= 0;
  const st = stepBall(pr, dt, BOXES, TW.grav, TW.minBounce, TW.bounce);
  if (st.n) {
    pr.lb = (pr.lb || 0) + st.n;
    sfx.thwock(st.hit.p, Math.max(pr.b, pr.lb));
    fx.spray(st.hit.p, 6, [0xd4ff3a, 0xf4f4f0], 2.5, 0.35, 0.05, 6, 1); // fuzz
  }
  const sp = Math.hypot(...pr.v);
  pr.spin = (pr.spin || 0) + sp * dt * 9;
  pr.mesh.position.set(pr.p[0], pr.p[1], pr.p[2]);
  pr.mesh.rotation.set(pr.spin, pr.spin * 0.3, 0);
  const k = Math.max(pr.b, pr.lb || 0);
  pr.mesh.scale.setScalar(1 + Math.min(5, k) * 0.07); // a bit bigger (and redder trail) every bounce: it hits harder
  if (!RP.active && pr.lastP && sp > 6) fx.tracer(pr.lastP, pr.p.slice(), BOUNCE_COLS[Math.min(5, k)], 0.03 + k * 0.006, 0.12);
  pr.lastP = pr.p.slice();
}
// the server ended a ball: h = it hit someone, tb = how many times it had bounced
export function tennisEnd(pr, m) {
  fx.spray(m.p, 10, [0xd4ff3a, 0xf4f4f0], 3.5, 0.45, 0.06, 6, 1);
  if (m.h) sfx.thwock(m.p, (m.tb || 0) + 2);
  if (m.h && pr.o === G.myId && m.tb > 0) hud.msg(m.tb >= 3 ? `TRICK SHOT x${m.tb}` : `BANK SHOT x${m.tb}`, 1.1, 'brag');
}

// ------------------------------------------------------------ Shopping carts
const carts = new Map(); // id -> { id, p, v, yaw, st, o, r, s, mesh, box, at, sp }
G.carts = carts;
function cartMesh() {
  const m = buildCart();
  const wheels = [];
  m.traverse((o) => { if (o.userData.wheel || /wheel/i.test(o.name)) wheels.push(o); });
  m.userData.wheels = wheels;
  G.scene.add(m);
  return m;
}
function solid(c, on, p, yaw) {
  if (c.box) { const i = BOXES.indexOf(c.box); if (i >= 0) BOXES.splice(i, 1); c.box = null; resetGrid(BOXES); }
  if (!on) return;
  const b = cartBox({ p, yaw }); b.mat = 'metal'; b.cart = c.id;
  BOXES.push(b); c.box = b; resetGrid(BOXES);
}
function upsert(m) {
  if (!Number.isInteger(m.id) || !Array.isArray(m.p)) return null;
  let c = carts.get(m.id);
  if (!c) { c = { id: m.id, p: m.p.slice(), v: [0, 0, 0], yaw: m.y || 0, mesh: cartMesh(), box: null, wob: Math.random() * 6 }; carts.set(m.id, c); }
  const mine = ME.ride === c.id;
  c.st = m.st; c.o = m.o; c.r = m.r || 0;
  if (!(mine && c.r === G.myId)) { c.tp = m.p.slice(); c.v = (m.v || [0, 0, 0]).slice(); c.ty = m.y || 0; c.at = performance.now(); }
  if (mine && c.r === G.myId) c.ok = true; // the server agreed: you're riding it
  if (!!m.s !== !!c.box) solid(c, !!m.s, m.p, m.y || 0);
  return c;
}
function dropCart(id, poof) {
  const c = carts.get(id);
  if (!c) return;
  solid(c, false);
  G.scene.remove(c.mesh);
  carts.delete(id);
  if (ME.ride === id) endRide();
  if (poof && !RP.active) { fx.smoke([c.p[0], c.p[1] + 0.5, c.p[2]], 6, 0.5); sfx.pop(c.p); }
}
net.on('cart', (m) => {
  if (m.k === 'x') { dropCart(m.id, true); return; }
  const c = upsert(m);
  if (c && m.k === 's') {
    sfx.cartFire(m.p);
    if (!RP.active) fx.smoke([m.p[0], m.p[1] + 0.6, m.p[2]], 4, 0.3);
  }
});
net.on('carts', (m) => {
  const seen = new Set();
  for (const it of Array.isArray(m.l) ? m.l : []) { const c = upsert(it); if (c) seen.add(c.id); }
  for (const id of [...carts.keys()]) if (!seen.has(id)) dropCart(id, false);
});
export function clearPrims() {
  for (const id of [...carts.keys()]) dropCart(id, false);
  for (const n of nails) G.scene.remove(n.m);
  nails.length = 0; pins.length = 0;
  ME.pin = null; ME.ride = 0;
}
// the play of the round / killcam: carts go into the recording like projectiles (6th slot = the yaw)
G.cartRec = () => [...carts.values()].map((c) => ['c' + c.id, 'cartp', R2(c.p[0]), R2(c.p[1]), R2(c.p[2]), R2(c.yaw)]);
// the server's fx for a cart running someone over
export function primFx(m) {
  if (m.k === 'shot' && m.w === 'nailgun') { nailSegs(m.s); return false; } // the normal tracer still draws
  if (m.k !== 'plough' || !Array.isArray(m.p)) return false;
  recordEv(m);
  sfx.cartCrash(m.p, Math.min(1.5, (m.s || 8) / 12));
  fx.spray(m.p, 16, [0xc8ccd4, 0xe0202a, 0x9b5cff], 6, 0.6, 0.1, 12, 1);
  fx.impact(m.p, [0, 1, 0]);
  if (near(m.p, 12)) G.shake = Math.max(G.shake, 0.5);
  return true;
}

// ---------------- riding: F on a cart (or land on one with some speed) and you're in. W pushes, look steers,
// space jumps out (the cart keeps rolling: aim it at someone), F hops out
function cartUnder(tol = 0.45) {
  let best = null, bd = Infinity;
  for (const c of carts.values()) {
    if (c.st === 'fly' || (c.r && c.r !== G.myId)) continue;
    const top = c.p[1] + CART.top, d = Math.hypot(ME.pos[0] - c.p[0], ME.pos[2] - c.p[2]);
    if (Math.abs(ME.pos[1] - top) < tol && d < CART.ride.reach && d < bd) { best = c; bd = d; }
  }
  return best;
}
function startRide(c) {
  ME.ride = c.id; ME.rideAsk = performance.now(); ME.rideYaw = c.yaw; ME.rideGround = true; ME.rideFall = 0;
  c.r = G.myId; c.ok = false;
  solid(c, false);
  ME.pos = [c.p[0], c.p[1] + CART.top, c.p[2]];
  ME.hook = null;
  net.send({ t: 'cart', k: 'ride', id: c.id });
  sfx.cartRattle(null, 1.4);
  hud.msg('CART SURFING', 1, 'brag');
}
function endRide() { ME.ride = 0; ME.rideAsk = 0; }
function hopOff(jump) {
  const c = carts.get(ME.ride);
  const v = ME.vel.slice();
  if (jump) ME.vel[1] = CART.ride.jump;
  endRide();
  if (c) { c.r = 0; c.st = 'roll'; c.v = [v[0], 0, v[2]]; c.tp = c.p.slice(); c.at = performance.now(); }
  net.send({ t: 'cart', k: 'off', v: v.map(R2) });
}
export function cartKey() {
  if (!ME.alive) return false;
  if (ME.ride) { hopOff(false); return true; }
  const c = cartUnder();
  if (!c || ME.pin) return false;
  startRide(c);
  return true;
}
const wrapA = (a) => { while (a > Math.PI) a -= Math.PI * 2; while (a < -Math.PI) a += Math.PI * 2; return a; };
// called from stepPlayer every frame: true = you're in a cart and it moved you
export function rideStep(dt, inp, now) {
  if (!ME.ride) return false;
  const c = carts.get(ME.ride);
  if (!c || !ME.alive || ME.pin || now < (ME.trapUntil || 0) || now < (ME.ballUntil || 0) || ME.dashing) { if (c) hopOff(false); else endRide(); return false; }
  if (!c.ok && now - ME.rideAsk > 800) { endRide(); return false; } // the server said no
  const R = CART.ride, v = ME.vel, top = CART.top;
  if (inp.jumpPressed) { inp.jumpPressed = false; hopOff(true); sfx.jump(); return false; }
  // steer: the cart turns toward where you look; its speed follows the heading (castors don't skid much)
  ME.rideYaw += Math.max(-R.turn * dt, Math.min(R.turn * dt, wrapA(ME.yaw - ME.rideYaw)));
  const fx0 = -Math.sin(ME.rideYaw), fz0 = -Math.cos(ME.rideYaw);
  let along = v[0] * fx0 + v[2] * fz0, side = v[0] * -fz0 + v[2] * fx0;
  side *= Math.exp(-7 * dt);
  if (ME.rideGround) {
    const fw = (inp.f ? 1 : 0) - (inp.b ? 1 : 0);
    if (fw > 0 && along < R.top) along = Math.min(R.top, along + R.acc * dt); // kick along like a scooter
    if (fw < 0) along = Math.max(-3, along - R.acc * 1.3 * dt); // feet down: brake, then roll back
    if (!fw) along -= Math.sign(along) * Math.min(Math.abs(along), R.fric * dt);
  }
  v[0] = fx0 * along - fz0 * side; v[2] = fz0 * along + fx0 * side;
  v[1] -= C.grav * dt;
  const cp = [ME.pos[0], ME.pos[1] - top, ME.pos[2]], v0 = v.slice();
  const res = movePlayer(cp, v, dt, BOXES, ME.rideGround);
  if (res.wall) {
    const hit = Math.hypot(v0[0] - v[0], v0[2] - v[2]);
    for (const ax of [0, 2]) if (v[ax] === 0 && v0[ax]) v[ax] = -v0[ax] * CART.wallBounce;
    if (hit > 6) { sfx.cartCrash([cp[0], cp[1] + 0.5, cp[2]], hit / 14); G.shake = Math.max(G.shake, Math.min(0.8, hit / 20)); }
  }
  const ground = !!res.ground && v[1] <= 0.01;
  if (ground && !ME.rideGround && ME.rideFall < -6) { // down a drop or a flight of stairs: the fall becomes speed
    const k = -ME.rideFall * CART.dropBoost; v[0] += fx0 * k; v[2] += fz0 * k;
    sfx.cartRattle(null, 2); fx.dust(cp, 8);
    if (ME.rideFall < -12) hud.msg('CLEAN UP ON AISLE 5', 0.9, 'brag');
  }
  ME.rideFall = ground ? 0 : Math.min(ME.rideFall || 0, v[1]);
  ME.rideGround = ground;
  ME.pos = [cp[0], cp[1] + top, cp[2]];
  ME.onGround = false; ME.sliding = false; ME.crouching = false; ME.sprinting = false; ME.hook = null;
  ME.eyeH += (C.standEye - ME.eyeH) * Math.min(1, dt * 14);
  c.p = cp; c.yaw = ME.rideYaw; c.v = v.slice();
  return true;
}

// ------------------------------------------------------------ every frame
let wasGround = true, rattleT = 0;
export function updatePrims(dt, now) {
  for (let i = nails.length - 1; i >= 0; i--) if (now > nails[i].until) { G.scene.remove(nails[i].m); nails.splice(i, 1); }
  for (let i = pins.length - 1; i >= 0; i--) if (now > pins[i].until) { for (const m of pins[i].list) { G.scene.remove(m); const j = nails.findIndex((n) => n.m === m); if (j >= 0) nails.splice(j, 1); } pins.splice(i, 1); }
  // jumped onto a cart with some speed: you're riding it
  if (ME.alive && !ME.ride && !ME.pin && ME.onGround && !wasGround && Math.hypot(ME.vel[0], ME.vel[2]) > 4) { const c = cartUnder(0.3); if (c && c.st !== 'fly') startRide(c); }
  else if (ME.alive && !ME.ride && ME.onGround && Math.hypot(ME.vel[0], ME.vel[2]) > CART.ride.autoSp + 5) { const c = cartUnder(0.3); if (c) startRide(c); } // sliding into one at speed
  wasGround = ME.onGround;
  rattleT -= dt;
  for (const c of carts.values()) {
    const mine = ME.ride === c.id;
    if (!mine) {
      if (c.st === 'rest' || !c.tp) { if (c.tp) c.p = c.tp.slice(); }
      else { // between updates: carry on along its velocity (100 ms of guessing at most), eased so corrections don't snap
        const t = Math.min(0.15, (now - c.at) / 1000), g = c.st === 'fly' ? 13 * t * t : 0;
        const want = [c.tp[0] + c.v[0] * t, c.tp[1] + c.v[1] * t - g, c.tp[2] + c.v[2] * t];
        const k = Math.min(1, dt * 18);
        for (let i = 0; i < 3; i++) c.p[i] += (want[i] - c.p[i]) * k;
      }
      c.yaw += wrapA((c.ty ?? c.yaw) - c.yaw) * Math.min(1, dt * 10);
    }
    const sp = Math.hypot(c.v[0], c.v[2]);
    c.wob += dt * (2 + sp);
    c.mesh.position.set(c.p[0], c.p[1], c.p[2]);
    // jank: a moving cart shimmies and leans like it has one bad wheel (it does)
    const lean = sp > 1 ? Math.sin(c.wob * 3.1) * 0.025 + Math.sin(c.wob * 7.3) * 0.012 : 0;
    c.mesh.rotation.set(c.st === 'fly' ? -0.15 : 0, c.yaw, lean, 'YXZ');
    for (const w of c.mesh.userData.wheels) w.rotation.x -= sp * dt / 0.05;
    c.mesh.visible = !RP.active;
    if (sp > 3 && c.st !== 'fly' && rattleT <= 0 && near(c.p, 25)) { rattleT = 0.18; sfx.cartRattle(c.p, Math.min(1.5, sp / 10)); }
  }
}

// replays: the pins (carts and balls come in with the projectiles)
RP_HOOKS.push({
  ev(m) {
    if (m.t === 'fx' && m.k === 'plough' && Array.isArray(m.p)) { sfx.cartCrash(m.p, 1); fx.spray(m.p, 16, [0xc8ccd4, 0xe0202a, 0x9b5cff], 6, 0.6, 0.1, 12, 1); return true; }
    if (m.t !== 'pin' || !Array.isArray(m.p)) return false;
    pinFx(m); return true;
  },
  stop() {},
});
