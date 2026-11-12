// WRECKING BALL, the client (battle island hero; kit: docs/mechs/ROSTER.md, numbers: MECH.wrecking in /shared/mech.js,
// the server judges it all: server/mech_wrecking.js). public/js/mech.js hands this kit your keys, your movement, the
// HUD row and the server's 'wb*' events. Rolling is momentum: slow to get going, faster than anything once it is, and it
// hurts whoever it rolls into. LMB revs it up on the spot and lets it go; Shift throws the chain at whatever the
// crosshair's on and swings (W pumps, jump or Shift lets go); E slams (higher = bigger); Q is the PILE DRIVER.
import * as THREE from 'three';
import { BOXES } from '/shared/map.js';
import { raycast, movePlayer } from '/shared/physics.js';
import { MECH, MF, energyAt, spend, wbRevSpeed } from '/shared/mech.js';
import { G } from './ctx.js';
import { ME, eye, look } from './player.js';
import { punchCam } from './weapons.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { K } from './keys.js';
import { rfx, rmesh } from './rigmodel.js';
import { mechsfx } from './mechsfx.js';
import { synth } from './audio.js';
import { MS, mechKitApi as A } from './mech.js';

const WB = MECH.wrecking, R = WB.r;
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const r2 = (x) => Math.round(x * 100) / 100;
const nowMs = () => performance.now();
const T = (...a) => synth.tone(...a), N = (...a) => synth.noise(...a);
// its sounds: a rev whine, a rolling rumble, the chain's clank, the launch, the pile driver's rockets
const sfx = {
  rev(pos) { T('sawtooth', 90, 520, 0.8, 0.12, pos); T('square', 180, 1040, 0.8, 0.05, pos); N(0.8, 0.25, 'bandpass', 600, 2600, pos, 0, 2); },
  launch(pos, k = 1) { T('sine', 140, 40, 0.5, 0.6 * k, pos); N(0.4, 0.7 * k, 'lowpass', 2200, 200, pos); T('square', 300, 1200, 0.15, 0.1, pos); mechsfx.boost(pos, 0.8); },
  roll(pos, k) { T('sine', 45 + k * 30, 30, 0.22, 0.25 * k, pos); N(0.2, 0.12 * k, 'lowpass', 300 + k * 500, 80, pos); },
  squeak(pos) { T('triangle', 2400, 3100, 0.07, 0.05, pos); T('triangle', 3100, 2600, 0.06, 0.04, pos, 0.07); }, // (the hamster)
  chain(pos) { for (let i = 0; i < 5; i++) T('square', 900 + Math.random() * 600, 500, 0.04, 0.06, pos, i * 0.04); N(0.25, 0.3, 'highpass', 3000, 6000, pos); },
  bite(pos) { mechsfx.clang(pos, 0.6); },
  pile(pos) { mechsfx.jet(pos, 1.2); T('sawtooth', 60, 300, 1.1, 0.15, pos); },
  dive(pos) { N(1.2, 0.6, 'bandpass', 400, 3000, pos, 0, 0.8); T('sine', 2400, 300, 1.2, 0.12, pos); },
};

// ------------------------------------------------------------ you, in it
const WS = { revT: 0, chain: null, slam: null, pile: null, launchUntil: 0, brake: false, jumpWas: false, ultWas: 0, rollT: 0, squeakT: 0, aimMk: null, minVy: 0 };
function clearState() { Object.assign(WS, { revT: 0, chain: null, slam: null, pile: null, launchUntil: 0, brake: false, minVy: 0 }); aimMark(null); }
const ballC = () => [ME.pos[0], ME.pos[1] + R, ME.pos[2]];

function key(e, down, now) {
  const is = (k) => K.matches(k, e) || (!down && K.up(k, e));
  if (!down) {
    if (is('fire')) { revGo(now); return false; }
    if (is('aim')) { WS.brake = false; return false; }
    return undefined;
  }
  if (e.repeat) return undefined;
  if (K.matches('fire', e)) { if (WS.pile && WS.pile.ph < 3) pdrop(now); else revStart(now); return true; }
  if (K.matches('aim', e)) { WS.brake = true; return true; }
  if (K.matches('sprint', e)) { chain(now); return true; }
  if (K.matches('grapple', e)) { slam(now); return true; }
  if (K.matches('lastSlot', e)) { pile(now); return true; }
  return undefined;
}
const cdLeft = (k, now) => Math.max(0, (MS.cd[k] || 0) - now);
const no = (t) => { hud.msg(t, 0.7); mechsfx.denied(); };
// rev: hold to spin up on the spot, let go to launch the way you look
function revStart(now) {
  if (WS.pile || WS.chain || now < WS.launchUntil || WS.revT) return;
  WS.revT = now;
  net.send({ t: 'mech', k: 'rev', on: 1 });
  sfx.rev(null);
}
function revGo(now) {
  if (!WS.revT) return;
  const c = (now - WS.revT) / 1000 - 0.05; // (a hair under what the server times)
  WS.revT = 0;
  net.send({ t: 'mech', k: 'rev', on: 0 });
  if (c < WB.rev.min - 0.05) return;
  if (!spend(MS.E, WB.rev.cost, now)) { no('NO ENERGY'); return; }
  const sp = wbRevSpeed(c), d = look(), hl = Math.hypot(d[0], d[2]) || 1;
  ME.vel[0] = d[0] / hl * sp; ME.vel[2] = d[2] / hl * sp;
  WS.launchUntil = now + WB.rev.len * 1000;
  sfx.launch(null, 0.6 + c); punchCam(0.05); G.shake = Math.max(G.shake, 0.5 + c * 0.4);
  rfx.sparks([ME.pos[0], ME.pos[1] + 0.2, ME.pos[2]], 30, 10, [0xffe14d, 0xffffff, 0xff7a3d], 0.5, 0.12);
  A.dustRing(ME.pos, 3, 0.6);
  if (c >= WB.rev.charge) hud.msg('FULL REV', 0.6, 'brag');
}
// the chain: onto whatever the crosshair's on (in reach, above you, in plain sight). again: let go
function chain(now) {
  if (WS.chain) { chainOff(true); return; }
  if (WS.pile) return;
  if (cdLeft('chain', now)) { no(`CHAIN ${(cdLeft('chain', now) / 1000).toFixed(1)}s`); return; }
  const e = eye(), aim = A.aimDir().p, d = [aim[0] - e[0], aim[1] - e[1], aim[2] - e[2]], l = Math.hypot(d[0], d[1], d[2]);
  if (l > WB.chain.range) { no('CHAIN: OUT OF REACH'); return; }
  if (aim[1] < ME.pos[1] + 1) { no('CHAIN: AIM HIGHER'); return; }
  const h = l > 0.5 && raycast(e, [d[0] / l, d[1] / l, d[2] / l], l + 0.8, BOXES);
  if (!h || h.t < l - 1.2 || h.box.pad) { no('CHAIN: NOTHING TO HOOK'); return; }
  if (!spend(MS.E, WB.chain.cost, now)) { no('NO ENERGY'); return; }
  const c = ballC();
  WS.chain = { at: h.point.slice(), len: Math.max(3, Math.hypot(c[0] - h.point[0], c[1] - h.point[1], c[2] - h.point[2])), t: now };
  WS.revT = 0; WS.slam = null;
  MS.cd.chain = now + WB.chain.cd * 1000;
  net.send({ t: 'mech', k: 'chain', p: h.point.map(r2) });
  sfx.chain(null); setTimeout(() => sfx.bite(h.point), 120);
  if (ME.onGround) { ME.vel[1] = Math.max(ME.vel[1], 6); ME.onGround = false; ME.pos[1] += 0.05; } // (a little tug off the floor)
}
function chainOff(send) {
  if (!WS.chain) return;
  WS.chain = null;
  MS.cd.chain = Math.max(MS.cd.chain || 0, nowMs() + WB.chain.cd * 1000);
  if (send) net.send({ t: 'mech', k: 'chain', off: 1 });
  sfx.chain(null);
}
function slam(now) {
  if (WS.slam || WS.pile) return;
  if (cdLeft('slam', now)) { no(`SLAM ${(cdLeft('slam', now) / 1000).toFixed(1)}s`); return; }
  MS.cd.slam = now + WB.slam.cd * 1000;
  if (WS.chain) chainOff(false);
  WS.slam = { ph: ME.onGround ? 1 : 2, t0: now };
  if (ME.onGround) { ME.vel[1] = WB.slam.hop; ME.onGround = false; ME.pos[1] += 0.05; }
  net.send({ t: 'mech', k: 'slam' });
  mechsfx.slamUp(null); G.shake = Math.max(G.shake, 0.3);
}
function pile(now) {
  if (WS.pile) { if (WS.pile.ph < 3) pdrop(now); return; }
  if ((MS.ult || 0) < 100) { no(`PILE DRIVER ${Math.floor(MS.ult || 0)}%`); return; }
  if (WS.chain) chainOff(false);
  WS.slam = null; WS.revT = 0; MS.ult = 0;
  WS.pile = { ph: 1, t0: now, y0: ME.pos[1] };
  net.send({ t: 'mech', k: 'pile' });
  sfx.pile(null); G.shake = Math.max(G.shake, 0.8); punchCam(0.06);
  hud.msg('PILE DRIVER', 1.4, 'brag');
}
// where the dive lands: the same pick the server makes (along your aim, a floor in range below you, else straight down)
function pileTarget(d) {
  const e = eye(), P = WB.pile;
  if (d && d[1] < -0.15) { const h = raycast(e, d, P.range * 1.6, BOXES); if (h && !h.box.pad && Math.hypot(h.point[0] - ME.pos[0], h.point[2] - ME.pos[2]) <= P.range && h.point[1] < ME.pos[1]) return h.point.slice(); }
  const h = raycast(e, [0, -1, 0], 200, BOXES);
  return h ? h.point.slice() : [ME.pos[0], ME.pos[1] - 40, ME.pos[2]];
}
// asks the server to dive (it picks the spot the same way); the dive starts when its answer ('wbpile' down) lands, so
// both sides head for the same spot. no answer in 1.2 s: straight down
function pdrop(now, auto) {
  if (!WS.pile || WS.pile.ph === 3 || WS.pile.ask || (!auto && now - WS.pile.t0 < 300)) return;
  WS.pile.ask = now;
  if (!auto) net.send({ t: 'mech', k: 'pdrop', d: A.aimDir().d.map(r2) });
}
function dive(to, now) {
  if (!WS.pile || WS.pile.ph === 3) return;
  WS.pile.ph = 3; WS.pile.to = to; WS.pile.dT = now;
  sfx.dive(null); punchCam(-0.06); G.shake = Math.max(G.shake, 0.6);
  aimMark(null);
}

// ------------------------------------------------------------ movement (mech.js mechStep hands it over)
function step(dt, inp, now) {
  const v = ME.vel, p = ME.pos;
  ME.hook = null; ME.sliding = false; ME.crouching = false; ME.sprinting = false; ME.dashing = false;
  const fw = (inp.f ? 1 : 0) - (inp.b ? 1 : 0), st = (inp.r ? 1 : 0) - (inp.l ? 1 : 0);
  const s = Math.sin(ME.yaw), c = Math.cos(ME.yaw);
  let wx = -s * fw + c * st, wz = -c * fw - s * st;
  const wl = Math.hypot(wx, wz);
  if (wl) { wx /= wl; wz /= wl; }
  const jumpNew = inp.jump && !WS.jumpWas; WS.jumpWas = !!inp.jump;
  let grav = WB.grav, fixed = false;
  const P = WB.pile, Wp = WS.pile;
  if (Wp) {
    if (Wp.ph === 1) { // straight up on the rockets
      v[0] *= 0.9; v[2] *= 0.9; v[1] = P.up; fixed = true;
      if (p[1] - Wp.y0 >= P.rise || now - Wp.t0 > P.rise / P.up * 1000 + 400) { Wp.ph = 2; Wp.hT = now; v[1] = 0; }
    } else if (Wp.ph === 2) { // hanging up there, aiming
      v[0] = v[1] = v[2] = 0; fixed = true;
      if (now - Wp.hT > P.hang * 1000) pdrop(now, true); // (the server drops it too)
      if (Wp.ask && now - Wp.ask > 1200) dive(pileTarget(null), now);
    } else { // the dive
      const to = Wp.to, d = [to[0] - p[0], to[1] - p[1], to[2] - p[2]], l = Math.hypot(d[0], d[1], d[2]) || 1;
      for (let i = 0; i < 3; i++) v[i] = d[i] / l * P.dive;
      fixed = true;
      if (now - Wp.dT > 3200) WS.pile = null; // (stuck on something)
    }
  } else if (WS.chain) { // the swing: a pendulum on the chain. W pumps it, A / D steer, jump lets go
    v[1] -= grav * dt;
    const hs = Math.hypot(v[0], v[2]);
    if (inp.f && hs > 1) { v[0] += v[0] / hs * WB.chain.pump * dt; v[2] += v[2] / hs * WB.chain.pump * dt; }
    else if (inp.f) { const d = look(), hl = Math.hypot(d[0], d[2]) || 1; v[0] += d[0] / hl * WB.chain.pump * dt; v[2] += d[2] / hl * WB.chain.pump * dt; }
    if (st) { v[0] += c * st * 5 * dt; v[2] += -s * st * 5 * dt; }
    if (jumpNew) chainOff(true);
    fixed = true; // (gravity done above)
  } else {
    const hs = Math.hypot(v[0], v[2]), launch = now < WS.launchUntil;
    if (ME.onGround) {
      if (hs > WB.speed && !launch) { const k = Math.max(0, hs - 16 * dt) / hs; v[0] *= k; v[2] *= k; } // (over top speed: it bleeds off fast)
      else if (hs > 0) { const k = Math.max(0, hs - Math.max(hs, 3) * WB.fric * (wl ? 0.45 : 1) * dt) / hs; v[0] *= k; v[2] *= k; }
      if (WS.revT) { v[0] *= Math.max(0, 1 - dt * 6); v[2] *= Math.max(0, 1 - dt * 6); } // revving: it stops to spin up
      else if (WS.brake) { const k = Math.max(0, hs - 30 * dt) / (hs || 1); v[0] *= k; v[2] *= k; if (hs > 6 && Math.random() < dt * 30) rfx.sparks([p[0], p[1] + 0.1, p[2]], 3, 5, [0xffe14d, 0xffffff], 0.3, 0.08); }
      else if (wl) push(v, wx, wz, WB.speed, WB.accel, dt);
      if (jumpNew && !WS.slam) { v[1] = WB.hop; ME.onGround = false; p[1] += 0.03; mechsfx.boost(null, 0.4); sfx.squeak(null); }
    } else {
      if (hs > WB.speed && !launch) { const k = Math.max(0, hs - 9 * dt) / hs; v[0] *= k; v[2] *= k; }
      if (wl) push(v, wx, wz, Math.min(WB.speed, WB.airCap), WB.accel * 0.3, dt);
    }
    if (WS.slam) {
      if (WS.slam.ph === 1 && v[1] < 4) WS.slam.ph = 2;
      if (WS.slam.ph === 2) { v[1] = -WB.slam.dive; grav = 0; }
      if (now - WS.slam.t0 > WB.slam.win * 1000) WS.slam = null;
    }
  }
  if (!fixed) v[1] -= grav * dt * 0.5;
  const was = ME.onGround;
  if (!was && v[1] < WS.minVy) WS.minVy = v[1];
  const res = movePlayer(p, v, dt, BOXES, was && !fixed && !WS.chain);
  if (!fixed && !res.ground) v[1] -= grav * dt * 0.5;
  // the chain holds the ball's middle on its sphere (the outward part of the speed goes; the swing keeps the rest)
  if (WS.chain) {
    const a = WS.chain.at, cc = ballC(), d = [cc[0] - a[0], cc[1] - a[1], cc[2] - a[2]], l = Math.hypot(d[0], d[1], d[2]);
    if (l > WS.chain.len) {
      const u = d.map((x) => x / l), k = WS.chain.len / l;
      p[0] = a[0] + d[0] * k; p[1] = a[1] + d[1] * k - R; p[2] = a[2] + d[2] * k;
      const out = v[0] * u[0] + v[1] * u[1] + v[2] * u[2];
      if (out > 0) for (let i = 0; i < 3; i++) v[i] -= u[i] * out;
    }
    const sp = Math.hypot(v[0], v[1], v[2]);
    if (sp > WB.chain.speed) for (let i = 0; i < 3; i++) v[i] *= WB.chain.speed / sp;
    if (now - WS.chain.t > WB.chain.life * 1000) chainOff(true);
  }
  ME.onGround = !!res.ground && v[1] <= 0.01;
  if (ME.onGround && !was) land(now);
  if (ME.onGround && res.ground.pad) { const pd = res.ground.pad; v[0] += pd[0]; v[1] = pd[1]; v[2] += pd[2]; ME.onGround = false; }
  if (res.wall) { const hs = Math.hypot(v[0], v[2]); if (hs > 12 || now < WS.launchUntil) { G.shake = Math.max(G.shake, 0.5); mechsfx.ram(null); rfx.sparks([p[0], p[1] + R, p[2]], 14, 8, [0xffffff, 0xffe14d], 0.3, 0.1); } }
  ME.eyeH += (WB.eye - ME.eyeH) * Math.min(1, dt * 8);
  return true;
}
function push(v, wx, wz, top, accel, dt) { const cur = v[0] * wx + v[2] * wz, add = top - cur; if (add > 0) { const a = Math.min(add, accel * top * dt); v[0] += a * wx; v[2] += a * wz; } }
function land(now) {
  const impact = -WS.minVy; WS.minVy = 0;
  const k = clamp((impact - 6) / 26, 0, 1);
  MS.landT = 0; MS.landK = k;
  if (WS.slam && WS.slam.ph === 2) { WS.slam = null; return; } // (the server's 'wbquake' does the big one)
  if (WS.pile && WS.pile.ph === 3) { WS.pile = null; return; }
  if (impact > 8) { A.dustRing(ME.pos, 2.5 + k * 3, k); mechsfx.step(null, 1.1, true); G.shake = Math.max(G.shake, 0.35 + k * 0.4); punchCam(-0.03 - k * 0.03); sfx.squeak(null); }
}

// ------------------------------------------------------------ every frame
function update(dt, now) {
  const hs = Math.hypot(ME.vel[0], ME.vel[2]);
  // jank: the pilot's in a hamster wheel. the camera shakes with every roll
  if (ME.onGround && hs > 4) {
    G.shake = Math.max(G.shake, 0.03 + hs / WB.speed * 0.09);
    WS.rollT -= dt * (0.4 + hs / 8);
    if (WS.rollT <= 0) { WS.rollT = 1; sfx.roll(null, clamp(hs / WB.speed, 0.2, 1.4)); }
    if (hs > 14 && Math.random() < dt * 20) rfx.dust([ME.pos[0], ME.pos[1], ME.pos[2]], 2, 0.8, 2);
    WS.squeakT -= dt; if (WS.squeakT < 0) { WS.squeakT = 3 + Math.random() * 5; sfx.squeak(null); }
  }
  if (WS.revT) { // spinning up: sparks off the floor, a rising whine, the screen buzzes
    const k = clamp((now - WS.revT) / 1000 / WB.rev.charge, 0, 1);
    G.shake = Math.max(G.shake, 0.1 + k * 0.25);
    if (Math.random() < dt * (20 + k * 60)) rfx.sparks([ME.pos[0] + (Math.random() - 0.5), ME.pos[1] + 0.1, ME.pos[2] + (Math.random() - 0.5)], 3, 6 + k * 6, [0xffe14d, 0xffffff, 0xff7a3d], 0.3, 0.09, [0, 1, 0]);
    if (k >= 1 && !WS.revFull) { WS.revFull = 1; hud.msg('REVVED', 0.5, 'brag'); T('square', 1600, 1600, 0.06, 0.08, null); }
  } else WS.revFull = 0;
  if (WS.pile && WS.pile.ph === 1 && Math.random() < dt * 50) rfx.smoke([ME.pos[0], ME.pos[1] - 0.3, ME.pos[2]], 2, 0xdfe4ea, 1, -2, 1.4, 0.5);
  if (WS.pile && WS.pile.ph === 2) aimMark(pileTarget(A.aimDir().d), now); // where it'll land
  if (WS.pile && WS.pile.ph === 3 && Math.random() < dt * 60) rfx.sparks([ME.pos[0], ME.pos[1] + R, ME.pos[2]], 2, 4, [0xffe14d, 0xff4fd8], 0.25, 0.1);
  const u = Math.floor(MS.ult || 0);
  if (u >= 100 && WS.ultWas < 100) { hud.msg(`PILE DRIVER READY · ${K.label('lastSlot')}`, 1.6, 'brag'); T('square', 880, 1320, 0.12, 0.1, null); T('square', 1320, 1760, 0.12, 0.1, null, 0.12); }
  WS.ultWas = u;
}
// the pile driver's target ring on the floor (yours, while you hang there aiming)
function aimMark(p, now = 0) {
  if (!p) { if (WS.aimMk) WS.aimMk.visible = false; return; }
  if (!WS.aimMk) {
    const g = new THREE.Group();
    g.add(new THREE.Mesh(new THREE.RingGeometry(WB.pile.r - 0.5, WB.pile.r, 40).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0xff3030, transparent: true, opacity: 0.6, depthWrite: false, side: THREE.DoubleSide })));
    g.add(new THREE.Mesh(new THREE.RingGeometry(0.4, 1.0, 20).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0xffe14d, transparent: true, opacity: 0.9, depthWrite: false, side: THREE.DoubleSide })));
    WS.aimMk = g; G.scene.add(g);
  }
  WS.aimMk.visible = true; WS.aimMk.position.set(p[0], p[1] + 0.08, p[2]);
  WS.aimMk.scale.setScalar(1 + Math.sin(now * 0.02) * 0.04);
}
function flags(now) { return (WS.chain ? MF.CHAIN : 0) | (WS.pile || WS.slam ? MF.PILE : 0) | (now < WS.launchUntil ? MF.REV : 0); }
function pose(now) {
  return { rev: WS.revT ? 1 : 0, chain: WS.chain ? WS.chain.at : null, chainT: WS.chain ? (now - WS.chain.t) / 1000 : 9, slam: WS.slam ? WS.slam.ph : 0, pile: WS.pile ? WS.pile.ph : 0,
    boost: (WS.pile && WS.pile.ph === 1) || now < WS.launchUntil ? 1 : 0 };
}

// ------------------------------------------------------------ everyone else's (and the replay's ghosts)
function remote(r, st, dt, now) {
  const W = st.wb || (st.wb = { chain: null, rev: 0, pile: 0, rollT: 0 });
  const fl = r.f, hs = Math.hypot(r.vel[0], r.vel[2]);
  if (!(fl & MF.CHAIN)) W.chain = null;
  if (!(fl & MF.PILE)) W.pile = 0;
  if (hs > 4 && !W.chain && Math.abs(r.vel[1]) < 2) { W.rollT -= dt * (0.4 + hs / 8); if (W.rollT <= 0) { W.rollT = 1; if (!r.ghost) sfx.roll(r.pos, clamp(hs / WB.speed, 0.2, 1.2)); } }
  if (W.rev && Math.random() < dt * 40) rfx.sparks([r.pos[0], r.pos[1] + 0.1, r.pos[2]], 2, 7, [0xffe14d, 0xffffff], 0.3, 0.09, [0, 1, 0]);
  return { rev: W.rev, chain: W.chain, chainT: W.chain ? (now - (W.chainT0 || 0)) / 1000 : 9, pile: W.pile, slam: !W.pile && fl & MF.PILE ? (r.vel[1] < 0 ? 2 : 1) : 0, boost: W.pile === 1 || fl & MF.REV ? 1 : 0 };
}

// ------------------------------------------------------------ the server's events
const EVENTS = new Set(['wbrev', 'wbchain', 'wbslam', 'wbpile', 'wbquake']);
function event(m, getR, live, me, r, st) {
  const P = (x) => (Array.isArray(x) && x.length === 3 && x.every(Number.isFinite) ? x : null);
  const W = st ? st.wb || (st.wb = { chain: null, rev: 0, pile: 0, rollT: 0 }) : null, pos = A.posOf(m.id, getR);
  switch (m.k) {
    case 'wbrev':
      if (W) W.rev = m.on === 1 ? 1 : 0;
      if (m.on === 1 && pos && !me) sfx.rev(pos);
      if (m.on === 2 && pos && !me) { sfx.launch(pos, 1); rfx.sparks([pos[0], pos[1] + 0.2, pos[2]], 24, 9, [0xffe14d, 0xffffff, 0xff7a3d], 0.45, 0.12); A.dustRing(pos, 3, 0.6); }
      break;
    case 'wbchain': {
      const p = P(m.p);
      if (W) { W.chain = m.off ? null : p; if (!m.off) W.chainT0 = nowMs(); }
      if (me) { if (m.off) WS.chain = null; else if (p && WS.chain) { WS.chain.at = p; if (Number.isFinite(m.len)) WS.chain.len = m.len; } }
      if (pos && !me) { if (m.off) sfx.chain(pos); else { sfx.chain(pos); if (p) setTimeout(() => sfx.bite(p), 120); } }
      if (p && !m.off) rfx.sparks(p, 10, 6, [0xffffff, 0xffe14d], 0.3, 0.08);
      break;
    }
    case 'wbslam': if (pos && !me) mechsfx.slamUp(pos); break;
    case 'wbpile': {
      if (W) W.pile = m.ph === 'up' ? 1 : m.ph === 'down' ? 3 : 0;
      const to = P(m.to);
      if (m.ph === 'up' && pos && !me) { sfx.pile(pos); A.shakeNear(pos, 0.6, 30); rfx.smoke([pos[0], pos[1], pos[2]], 20, 0xdfe4ea, 1.8, 1, 2, 0.8); }
      if (m.ph === 'down') {
        if (me && WS.pile && to) { if (WS.pile.ph === 3) WS.pile.to = to; else dive(to, nowMs()); }
        if (to) { rmesh.ring(to, WB.pile.r, 0xff3030, 1.1); rmesh.ring(to, WB.pile.r * 0.5, 0xffe14d, 1.1); } // INCOMING: everyone sees where it's coming down
        if (live && to && !me && Math.hypot(to[0] - ME.pos[0], to[2] - ME.pos[2]) < WB.pile.r + 2) hud.msg('INCOMING BALL. MOVE', 1.2, 'slip');
        if (pos && !me) sfx.dive(pos);
      }
      if (m.ph === 'off' && me) { WS.pile = null; aimMark(null); }
      break;
    }
    case 'wbquake': { // a slam / the pile driver hits the floor
      const p = P(m.p), big = !!m.big, rr = Number.isFinite(m.r) ? clamp(m.r, 1, 12) : 6, k = Number.isFinite(m.sz) ? clamp(m.sz, 0, 1) : 0.5;
      if (me) { WS.slam = null; if (WS.pile) WS.pile = null; aimMark(null); }
      if (W) W.pile = 0;
      if (!p) break;
      const fl = raycast([p[0], p[1] + 0.5, p[2]], [0, -1, 0], 3, BOXES), at = [p[0], fl ? fl.point[1] : p[1], p[2]];
      rmesh.ring(at, rr * 1.15, 0xffffff, 0.35); rmesh.ring(at, rr * 0.85, 0xffd23a, 0.55); rmesh.ring(at, rr * 1.5, big ? 0xff3030 : 0xff4fd8, 0.75);
      rfx.dust(at, 30 + k * 30 + (big ? 40 : 0), rr * 0.6, rr * 1.4); rfx.debris(at, 20 + (big ? 40 : 0), 9 + k * 4);
      rmesh.crater(at, big ? 4.5 : 2 + k * 2); rmesh.flash([at[0], at[1] + 1, at[2]], big ? 6 : 3, 0xfff0b0, 0.25);
      mechsfx.quake(me ? null : at);
      if (big) mechsfx.boom(me ? null : at);
      if (me) { G.shake = Math.max(G.shake, big ? 1.6 : 0.8 + k * 0.6); punchCam(big ? -0.12 : -0.07); if (hud.impact) hud.impact(big ? 1 : 0.6); hud.msg(big ? 'PILE DRIVER' : k > 0.6 ? 'BIG SLAM' : 'BALL SLAM', big ? 1.4 : 0.8, 'brag'); }
      else if (live) A.shakeNear(at, big ? 1.6 : 0.9, big ? 50 : 30);
      break;
    }
  }
}

export const WBK = {
  abil: [['fire', 'REV', '', WB.rev.cost], ['sprint', 'CHAIN', 'chain', WB.chain.cost], ['grapple', 'SLAM', 'slam'], ['lastSlot', 'PILE DRIVER', 'ult']],
  cds: ['chain', 'slam'],
  events: EVENTS,
  help: () => `roll into people · hold ${K.label('fire')} rev, let go to launch · ${K.label('sprint')} chain (W pumps, ${K.label('jump')} lets go) · ${K.label('grapple')} ground slam · ${K.label('aim')} brake · ${K.label('lastSlot')} PILE DRIVER`,
  start() { clearState(); WS.ultWas = 0; },
  end() { clearState(); },
  reset() { clearState(); },
  denied(why) { if (/^chain|no energy/.test(why)) { WS.chain = null; WS.launchUntil = 0; } if (/ultimate/.test(why)) WS.pile = null; },
  key, step, update, flags, pose, remote, event,
};
