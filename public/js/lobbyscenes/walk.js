// the walkable lobbies (BATTLE ISLAND's garage, ZOMBIES' warehouse): you in third person. WASD (your bindings) walks
// where the camera looks, SHIFT runs, SPACE jumps (onto crates too), drag the mouse to look round, the wheel zooms,
// E / F uses what you stand next to, Z does an emote. a scene can hand you a ride (the garage's mech): then the keys
// drive that. your spot goes to your party ~10 times a second (party.js relays it); theirs come back and they walk
// too. offline, the bots wander about. all in the scene's own box: x / z within its bounds, nothing is sent outside it.
import * as THREE from 'three';
import { K } from '../keys.js';
import { locoPose } from '../loco.js';

const GRAV = 26, JUMP = 8.6, WALK = 5.2, RUN = 8.4, R = 0.42; // m/s², m/s, the body's radius
const cl = (v, a, b) => (v < a ? a : v > b ? b : v);
const typing = () => { const a = document.activeElement; return !!a && /^(INPUT|SELECT|TEXTAREA)$/.test(a.tagName); };

// push a circle (x, z, r) at height y out of the scene's solid boxes; returns the floor under it
// solids: [x0, z0, x1, z1, top]. something you're above (or nearly: a step) is a floor, not a wall
export function collide(S, p, r, prevY) {
  let floor = 0;
  for (const b of S) {
    const nx = cl(p[0], b[0], b[2]), nz = cl(p[2], b[1], b[3]), dx = p[0] - nx, dz = p[2] - nz, d2 = dx * dx + dz * dz;
    if (d2 >= r * r) continue;
    if (prevY >= b[4] - 0.35) { floor = Math.max(floor, b[4]); continue; } // on top of it (or stepping up)
    if (d2 > 1e-8) { const d = Math.sqrt(d2), k = (r - d) / d; p[0] += dx * k; p[2] += dz * k; }
    else { // centre inside the box: out the nearest side
      const o = [p[0] - b[0], b[2] - p[0], p[2] - b[1], b[3] - p[2]], m = Math.min(...o), i = o.indexOf(m);
      if (i === 0) p[0] = b[0] - r; else if (i === 1) p[0] = b[2] + r; else if (i === 2) p[2] = b[1] - r; else p[2] = b[3] + r;
    }
  }
  return floor;
}
export function clampIn(B, p, r) { p[0] = cl(p[0], B[0] + r, B[2] - r); p[2] = cl(p[2], B[1] + r, B[3] - r); }

// a body that walks: you, a party member (from the relay) or a bot. drives the mannequin with the game's own loco
export function walker(ch, gun, at) {
  return { ch, pos: [at[0], 0, at[2]], vel: [0, 0, 0], yaw: at[3] || 0, f: 0, gy: 0, buf: null, frozenUntil: 0, w: gun || null, weaponMeshL: null, air: false, tgt: null, emo: 0, hidden: false };
}
export function poseWalker(r, dt, now) {
  r.ch.root.position.set(0, 0, 0);
  locoPose(r, dt, now);
  const free = !r.w;
  if (r.emo > 0) { // the wave: the gun arm up and waving, a little bounce
    r.emo = Math.max(0, r.emo - dt);
    r.ch.arm.rotation.set(2.6 + Math.sin(r.emo * 18) * 0.35, 0, 0.35); return;
  }
  const a = -0.35 + Math.sin(now * 0.0013 + r.pos[0]) * 0.03; // low ready
  r.ch.arm.rotation.set(a, 0, 0);
  if (!free) r.ch.armL.rotation.set(a, 0.5, 0);
}

export function makeWalk(c, L, spec, me0) {
  let me = me0;
  const W = { keys: new Set(), camYaw: spec.spawn[3] || 0, camPitch: 0.28, dist: spec.dist || 5.6, drag: null, dragged: false, near: null, ride: null, sent: 0, t: 0 };
  const cam = c.cam, tgt = new THREE.Vector3(), want = new THREE.Vector3(), camPos = new THREE.Vector3(), _v = new THREE.Vector3();
  let camInit = false;
  const prompt = L.tag('ls-use', '<kbd>E</kbd><b></b>'); prompt.style.display = 'none';
  const scr = document.getElementById('scr-hubby');
  const onScene = (e) => { const el = e.target; return el && (el.id === 'scr-hubby' || el.id === 'hubStage' || el.id === 'preview' || el.id === 'lsTags' || el.closest('#hubFrame')); };
  // keys: only while the lobby is the screen and you aren't typing. what we use doesn't reach the hub's own keys
  const MOVE = ['forward', 'back', 'left', 'right', 'jump', 'sprint'];
  const down = (e) => {
    if (typing() || !c.visible()) return;
    if (e.code === 'Escape' && !c.panels) { c.setPanels(true); e.preventDefault(); e.stopImmediatePropagation(); return; } // (Esc: the full lobby first, then out)
    if (e.code === 'Tab') { c.setPanels(!c.panels); e.preventDefault(); e.stopImmediatePropagation(); return; }
    let hit = false;
    for (const a of MOVE) if (K.matches(a, e)) { W.keys.add(a); hit = true; }
    if (e.code === 'KeyE' || K.matches('use', e)) { if (!e.repeat) use(); hit = true; }
    if (e.code === 'KeyZ' || K.matches('spray', e)) { if (!e.repeat && !W.ride) { me.emo = 1.4; L.sfx.tone('square', 660, 990, 0.08, 0.05); } hit = true; }
    if (hit) { e.preventDefault(); e.stopImmediatePropagation(); if (document.activeElement && document.activeElement !== document.body) document.activeElement.blur(); }
  };
  const up = (e) => { for (const a of MOVE) if (K.matches(a, e)) W.keys.delete(a); };
  const blur = () => W.keys.clear();
  addEventListener('keydown', down, true); addEventListener('keyup', up, true); addEventListener('blur', blur);
  c.ls.push([window, 'keydown', down, true], [window, 'keyup', up, true], [window, 'blur', blur]);
  // mouse: drag the scene to look round (a click without a drag still clicks things), the wheel zooms
  const pd = (e) => { if (!onScene(e) || e.button > 2) return; W.drag = [e.clientX, e.clientY]; W.dragged = false; };
  const pm = (e) => {
    if (!W.drag || !(e.buttons & 7)) { W.drag = null; return; }
    const dx = e.clientX - W.drag[0], dy = e.clientY - W.drag[1];
    if (!W.dragged && Math.hypot(dx, dy) < 5) return;
    W.dragged = true; W.drag = [e.clientX, e.clientY];
    W.camYaw -= dx * 0.006; W.camPitch = cl(W.camPitch + dy * 0.005, -0.15, 1.15);
  };
  const pu = () => { W.drag = null; };
  const wh = (e) => { if (!onScene(e)) return; W.dist = cl(W.dist * (e.deltaY > 0 ? 1.1 : 0.9), 3, 11); };
  for (const [el, ty, fn] of [[scr, 'pointerdown', pd], [window, 'pointermove', pm], [window, 'pointerup', pu], [scr, 'wheel', wh]]) { el.addEventListener(ty, fn, { passive: true }); c.ls.push([el, ty, fn]); }

  function use() {
    if (W.ride) { W.ride.exit(); return; }
    if (W.near) W.near.act();
  }
  // the body the keys move: you, or your ride
  function step(dt) {
    const B = W.ride ? W.ride : me, sp = W.ride ? W.ride.speed : W.keys.has('sprint') ? RUN : WALK;
    let fx = 0, fz = 0;
    if (W.keys.has('forward')) fz -= 1; if (W.keys.has('back')) fz += 1; if (W.keys.has('left')) fx -= 1; if (W.keys.has('right')) fx += 1;
    const n = Math.hypot(fx, fz), cy = Math.cos(W.camYaw), sy = Math.sin(W.camYaw);
    let wx = 0, wz = 0;
    if (n) { fx /= n; fz /= n; wx = (fx * cy + fz * sy) * sp; wz = (-fx * sy + fz * cy) * sp; }
    const acc = B.air ? 4 : 14;
    B.vel[0] += (wx - B.vel[0]) * Math.min(1, acc * dt); B.vel[2] += (wz - B.vel[2]) * Math.min(1, acc * dt);
    if (W.keys.has('jump') && !B.air && !W.ride) { B.vel[1] = JUMP; B.air = true; L.sfx.tone('sine', 300, 520, 0.08, 0.04); }
    B.vel[1] -= GRAV * dt;
    const py = B.pos[1];
    B.pos[0] += B.vel[0] * dt; B.pos[1] += B.vel[1] * dt; B.pos[2] += B.vel[2] * dt;
    const rr = W.ride ? W.ride.r : R;
    const fl = collide(W.ride ? W.ride.solids : spec.solids, B.pos, rr, py);
    clampIn(W.ride ? W.ride.bounds : spec.bounds, B.pos, rr);
    if (B.pos[1] <= fl) { if (B.air && B.vel[1] < -6) L.shake = Math.max(L.shake, W.ride ? 0.3 : 0); B.pos[1] = fl; B.vel[1] = 0; B.air = false; }
    else if (B.pos[1] > fl + 0.05) B.air = true;
    B.gy = fl;
    const hs = Math.hypot(B.vel[0], B.vel[2]);
    if (hs > 0.4) { const yw = Math.atan2(-B.vel[0], -B.vel[2]); let d = yw - B.yaw; d = Math.atan2(Math.sin(d), Math.cos(d)); B.yaw += d * Math.min(1, dt * (W.ride ? 5 : 12)); }
    if (W.ride) W.ride.moved(dt, hs);
  }
  // what's in reach: the nearest thing that says it can be used, with its label over it
  function near() {
    let best = null, bd = 1e9;
    const p = W.ride ? W.ride.pos : me.pos;
    for (const it of spec.use || []) {
      if (it.show && !it.show()) continue;
      const d = Math.hypot(it.at[0] - p[0], it.at[2] - p[2]);
      if (d < (it.r || 2) && d < bd) { bd = d; best = it; }
    }
    if (W.ride) best = { at: [W.ride.pos[0], W.ride.h, W.ride.pos[2]], label: () => 'HOP OUT', act: () => W.ride.exit() };
    W.near = best;
    if (!best) { prompt.style.display = 'none'; return; }
    prompt.querySelector('b').textContent = best.label();
    prompt.style.display = '';
    _v.set(best.at[0], best.at[1] + 0.3, best.at[2]); L.at(prompt, _v);
  }
  // the camera: behind and above whoever you drive, pulled in if it would leave the room
  function camFrame(dt) {
    const B = W.ride || me, h = W.ride ? W.ride.camH : 1.65;
    let dist = W.ride ? W.ride.camDist : W.dist;
    tgt.set(B.pos[0], B.pos[1] + h, B.pos[2]);
    const F = c.camFocus; // a scene's big moment (the crane swap): the camera looks over at it for a beat, then comes back
    if (F) { F.t += dt; const k = Math.max(0, Math.min(1, F.t / 0.35, (F.dur - F.t) / 0.45)); const e = k * k * (3 - 2 * k); tgt.lerp(_v.set(F.at[0], F.at[1], F.at[2]), e * 0.8); dist += e * (F.back || 4); if (F.t >= F.dur) c.camFocus = null; }
    const cp = Math.cos(W.camPitch);
    want.set(tgt.x + Math.sin(W.camYaw) * cp * dist, tgt.y + Math.sin(W.camPitch) * dist + 0.3, tgt.z + Math.cos(W.camYaw) * cp * dist);
    const C = spec.camBox; if (C) { want.x = cl(want.x, C[0], C[3]); want.y = cl(want.y, C[1], C[4]); want.z = cl(want.z, C[2], C[5]); }
    if (!camInit) { camPos.copy(want); camInit = true; } else camPos.lerp(want, Math.min(1, dt * 8));
    cam.position.copy(camPos);
    if (L.shake > 0) { const k = L.shake * L.shake * 0.3; cam.position.x += (Math.random() - 0.5) * k; cam.position.y += (Math.random() - 0.5) * k; L.shake = Math.max(0, L.shake - dt * 1.6); }
    cam.lookAt(tgt);
    cam.fov = 55; cam.aspect = innerWidth / innerHeight; cam.clearViewOffset(); cam.updateProjectionMatrix();
  }
  return {
    W, get me() { return me; }, set me(r) { me = r; },
    reMe(r) { me = r; },
    frame(dt, now) {
      W.t += dt;
      if (!typing() && c.visible()) step(dt); else { W.keys.clear(); step(dt); }
      near();
      camFrame(dt);
      if (c.party && c.party.sendLobbyPos && c.party.inParty && c.party.inParty()) { const B = W.ride || me; c.party.sendLobbyPos([+B.pos[0].toFixed(2), +B.pos[1].toFixed(2), +B.pos[2].toFixed(2)], +B.yaw.toFixed(3), W.ride ? 1 : me.emo > 0 ? 2 : 0); }
      void now;
    },
    setRide(r) { W.ride = r; if (r) { r.vel = r.vel || [0, 0, 0]; r.air = false; } },
    dragged: () => W.dragged,
  };
}

// a bot in an offline lobby: strolls from one spot to another, stands about, strolls on
export function wander(r, dt, spec, rnd) {
  if (!r.wd) r.wd = { to: null, wait: 1 + rnd() * 3 };
  const w = r.wd;
  if (!w.to) { w.wait -= dt; if (w.wait <= 0) { const P = spec.wander; const q = P[Math.floor(rnd() * P.length)]; w.to = [q[0] + (rnd() - 0.5) * 2, q[1] + (rnd() - 0.5) * 2]; } }
  let wx = 0, wz = 0;
  if (w.to) {
    const dx = w.to[0] - r.pos[0], dz = w.to[1] - r.pos[2], d = Math.hypot(dx, dz);
    if (d < 0.6) { w.to = null; w.wait = 2 + rnd() * 5; } else { wx = (dx / d) * 2.6; wz = (dz / d) * 2.6; }
  }
  r.vel[0] += (wx - r.vel[0]) * Math.min(1, 6 * dt); r.vel[2] += (wz - r.vel[2]) * Math.min(1, 6 * dt);
  const py = r.pos[1];
  r.pos[0] += r.vel[0] * dt; r.pos[2] += r.vel[2] * dt;
  r.gy = r.pos[1] = collide(spec.solids, r.pos, R, py);
  clampIn(spec.bounds, r.pos, R);
  if (w.to && Math.hypot(r.vel[0], r.vel[2]) < 0.3 && rnd() < dt * 0.8) w.to = null; // stuck on something: give up, pick another
  const hs = Math.hypot(r.vel[0], r.vel[2]);
  if (hs > 0.3) { const yw = Math.atan2(-r.vel[0], -r.vel[2]); let d = yw - r.yaw; d = Math.atan2(Math.sin(d), Math.cos(d)); r.yaw += d * Math.min(1, dt * 6); }
}
// a party member's spot from the relay: slide toward it (updates come ~10 a second)
export function follow(r, dt) {
  if (!r.tgt) return;
  const k = Math.min(1, dt * 10);
  const dx = r.tgt[0] - r.pos[0], dz = r.tgt[2] - r.pos[2];
  if (dx * dx + dz * dz > 100) { r.pos[0] = r.tgt[0]; r.pos[2] = r.tgt[2]; } // (a jump across the room: no sliding)
  r.pos[0] += dx * k; r.pos[1] += (r.tgt[1] - r.pos[1]) * k; r.pos[2] += dz * k;
  let d = r.tyaw - r.yaw; d = Math.atan2(Math.sin(d), Math.cos(d)); r.yaw += d * k;
  r.gy = r.pos[1] > 0.3 ? r.pos[1] : 0;
}
