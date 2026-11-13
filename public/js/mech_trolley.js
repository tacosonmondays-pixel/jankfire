// TROLLEY, the client (battle island hero; kit: docs/mechs/ROSTER.md, numbers: MECH.trolley in /shared/mech.js, the
// server judges it all: server/mech_trolley.js). public/js/mech.js hands this kit your keys, your movement, the HUD row
// and the server's 'tr*' events. It drives like a cart: quick off the mark, grippy, a bit of slide, and it always pulls a
// little left (the wonky wheel). LMB lobs tin cans; hold Shift to drift (fast enough and it builds a RAM CHARGE); E is
// the TROLLEY PUSH (the charge makes it huge); Q is CLEAN UP AISLE 5 (Q again dumps the basket). Allies press F next to
// it to ride in the child seat (the pound coin lock): this file also moves riders and the scooped (the guest hooks).
import * as THREE from 'three';
import { BOXES } from '/shared/map.js';
import { movePlayer } from '/shared/physics.js';
import { MECH, MF, trDrive, trPush, trSpot } from '/shared/mech.js';
import { G } from './ctx.js';
import { ME } from './player.js';
import { W, punchCam, isFriend } from './weapons.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { K } from './keys.js';
import { rfx, rmesh } from './rigmodel.js';
import { mechsfx } from './mechsfx.js';
import { synth } from './audio.js';
import { MS, mechKitApi as A } from './mech.js';

const TR = MECH.trolley;
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const r2 = (x) => Math.round(x * 100) / 100;
const nowMs = () => performance.now();
const T = (...a) => synth.tone(...a), N = (...a) => synth.noise(...a);
// its sounds (all synth): squeaky casters (higher the faster), the drift's squeal, cans, the till, the tannoy
const sfx = {
  squeak(pos, k = 0.5) { const f = 1500 + k * 1700; T('triangle', f, f * 1.35, 0.06, 0.05, pos); T('triangle', f * 1.3, f * 0.95, 0.07, 0.04, pos, 0.06); },
  rattle(pos, k) { N(0.09, 0.12 * k, 'highpass', 3500, 6500, pos, 0, 2); T('square', 2600 + Math.random() * 900, 2200, 0.03, 0.025 * k, pos); }, // the wire basket
  squeal(pos, k = 1) { T('sawtooth', 2350 + Math.random() * 200, 2700, 0.32, 0.035 * k, pos); T('square', 1180, 1320, 0.32, 0.02 * k, pos); N(0.32, 0.18 * k, 'bandpass', 2600, 3200, pos, 0, 6); },
  toss(pos) { mechsfx.whoosh(pos); T('triangle', 900, 1500, 0.08, 0.06, pos); },
  bonk(pos) { T('square', 640, 180, 0.12, 0.25, pos); T('sine', 1760, 1700, 0.35, 0.12, pos); T('sine', 2640, 2600, 0.25, 0.06, pos); N(0.05, 0.6, 'highpass', 2000, 6000, pos); }, // BONK + the tin ringing
  shove(pos, k = 0.5) { mechsfx.boost(pos, 0.6 + k * 0.6); mechsfx.ram(pos, k > 0.6); T('sawtooth', 160, 60 + k * 40, 0.3, 0.15 + k * 0.1, pos); },
  hit(pos, big) { mechsfx.ram(pos, big); T('square', big ? 300 : 420, 90, 0.18, 0.2, pos); if (big) mechsfx.clang(pos, 0.8); },
  kaching(pos) { T('square', 2093, 2093, 0.09, 0.09, pos, 0.1); T('square', 2637, 2637, 0.25, 0.08, pos, 0.17); T('sine', 4186, 4186, 0.5, 0.05, pos, 0.17); N(0.12, 0.6, 'lowpass', 1400, 200, pos); T('square', 120, 60, 0.1, 0.15, pos); }, // the drawer, then the bell
  tannoy(pos) { // ding-dong-ding, then a crackle like someone's about to say it
    const notes = [[784, 0], [659, 0.32], [523, 0.64]];
    for (const [f, d] of notes) { T('sine', f, f, 0.55, 0.16, pos, d); T('triangle', f * 2, f * 2, 0.3, 0.04, pos, d); }
    N(1.1, 0.12, 'bandpass', 1800, 900, pos, 0.95, 3); T('square', 220, 180, 0.9, 0.03, pos, 1.0);
  },
  dump(pos) { T('sawtooth', 300, 90, 0.45, 0.12, pos); N(0.5, 0.6, 'bandpass', 1200, 400, pos, 0.05, 1.5); for (let i = 0; i < 5; i++) T('square', 1800 + Math.random() * 1500, 900, 0.04, 0.05, pos, 0.1 + i * 0.05); },
  seat(pos) { T('square', 500, 380, 0.08, 0.1, pos); N(0.12, 0.3, 'highpass', 1500, 4000, pos); T('sine', 1318, 1318, 0.18, 0.08, pos, 0.1); }, // the flap clacks down
  charged() { T('square', 880, 880, 0.07, 0.08, null); T('square', 1320, 1320, 0.07, 0.08, null, 0.08); T('square', 1760, 1760, 0.12, 0.08, null, 0.16); },
};

// ------------------------------------------------------------ you, in it
const TS = { drift: false, brake: false, lmb: false, ch: 0, chT: 0, srvCh: 0, push: null, aisle: 0, canNext: 0, tossT: 9, scoopT: 9, dumpT: 9, hitStop: 0,
  jumpWas: false, ultWas: 0, squeakT: 0, squealT: 0, minVy: 0, held: new Map(), full: false, hud: null, bk: 0 };
function clearState() { Object.assign(TS, { drift: false, brake: false, lmb: false, ch: 0, chT: 0, srvCh: 0, push: null, aisle: 0, tossT: 9, scoopT: 9, dumpT: 9, hitStop: 0, minVy: 0, full: false, bk: 0 }); TS.held.clear(); hudLine(false); }
const chargeNow = (now) => (now - TS.chT <= TR.drift.keep * 1000 ? TS.ch : 0);
const fwdOf = () => [-Math.sin(ME.yaw), -Math.cos(ME.yaw)];

function key(e, down, now) {
  const is = (k) => K.matches(k, e) || (!down && K.up(k, e));
  if (!down) {
    if (is('fire')) { TS.lmb = false; return false; }
    if (is('sprint')) { TS.drift = false; return false; }
    if (is('aim')) { TS.brake = false; return false; }
    return undefined;
  }
  if (e.repeat) return undefined;
  if (K.matches('fire', e)) { TS.lmb = true; return true; }
  if (K.matches('sprint', e)) { TS.drift = true; return true; }
  if (K.matches('aim', e)) { TS.brake = true; return true; }
  if (K.matches('grapple', e)) { push(now); return true; }
  if (K.matches('lastSlot', e)) { aisle(now); return true; }
  return undefined;
}
const cdLeft = (k, now) => Math.max(0, (MS.cd[k] || 0) - now);
const no = (t) => { hud.msg(t, 0.7); mechsfx.denied(); };
// the push: a lunge where it's facing, as big as the ram charge you built (the server works out the real one)
function push(now) {
  if (TS.push && now < TS.push.until) return;
  if (cdLeft('push', now)) { no(`PUSH ${(cdLeft('push', now) / 1000).toFixed(1)}s`); return; }
  const c = chargeNow(now), h = trPush(c);
  MS.cd.push = now + TR.push.cd * 1000;
  TS.ch = 0; TS.push = { t0: now, until: now + TR.push.len * 1000, v: h.v, dir: fwdOf(), k: h.k };
  net.send({ t: 'mech', k: 'push' });
  sfx.shove(null, h.k); punchCam(0.04 + h.k * 0.05); G.shake = Math.max(G.shake, 0.4 + h.k * 0.5);
  rfx.sparks([ME.pos[0], ME.pos[1] + 0.2, ME.pos[2]], 16 + h.k * 30, 9, [0xffe14d, 0xffffff, 0xff7a3d], 0.4, 0.1);
  A.dustRing(ME.pos, 2 + h.k * 2, 0.5 + h.k * 0.5);
  hud.msg(h.k >= 0.95 ? 'FULL SEND' : h.k > 0.4 ? 'SHOVE' : 'NUDGE', 0.7, h.k >= 0.95 ? 'brag' : '');
}
// CLEAN UP AISLE 5 (a full ult): 6 s at top speed; Q again dumps the basket
function aisle(now) {
  if (TS.aisle > now) { net.send({ t: 'mech', k: 'aisle', on: 0 }); return; }
  if ((MS.ult || 0) < 100) { no(`AISLE 5 ${Math.floor(MS.ult || 0)}%`); return; }
  MS.ult = 0; TS.aisle = now + TR.aisle.dur * 1000; TS.aisleT0 = now;
  net.send({ t: 'mech', k: 'aisle', on: 1 });
  sfx.tannoy(null); mechsfx.jet(null, TR.aisle.dur * 0.9);
  G.shake = Math.max(G.shake, 0.7); punchCam(0.06);
  hud.msg('CLEAN UP ON AISLE 5', 2, 'brag');
}

// ------------------------------------------------------------ movement (mech.js mechStep hands it over)
function step(dt, inp, now) {
  const v = ME.vel, p = ME.pos;
  ME.hook = null; ME.sliding = false; ME.crouching = false; ME.sprinting = false; ME.dashing = false;
  if (TS.hitStop > 0) { TS.hitStop -= dt; return true; } // the push connected: it hangs there for a beat
  const fw = (inp.f ? 1 : 0) - (inp.b ? 1 : 0), st = (inp.r ? 1 : 0) - (inp.l ? 1 : 0);
  const s = Math.sin(ME.yaw), c = Math.cos(ME.yaw);
  const wx = -s * fw + c * st, wz = -c * fw - s * st;
  const jumpNew = inp.jump && !TS.jumpWas; TS.jumpWas = !!inp.jump;
  const pushing = TS.push && now < TS.push.until, top = TS.aisle > now ? TR.aisle.speed : TR.speed;
  if (TS.push && !pushing) TS.push = null;
  if (pushing) { v[0] = TS.push.dir[0] * TS.push.v; v[2] = TS.push.dir[1] * TS.push.v; }
  else {
    const h = [v[0], v[2]], drift = TS.drift && ME.onGround;
    trDrive(h, TS.brake ? 0 : wx, TS.brake ? 0 : wz, dt, top, drift, ME.onGround, true); // (true: the wonky wheel pulls left)
    if (TS.brake && ME.onGround) { const hs = Math.hypot(h[0], h[1]), k = Math.max(0, hs - 34 * dt) / (hs || 1); h[0] *= k; h[1] *= k; if (hs > 5 && Math.random() < dt * 30) rfx.sparks([p[0], p[1] + 0.1, p[2]], 2, 4, [0xffe14d, 0xffffff], 0.25, 0.07); }
    v[0] = h[0]; v[2] = h[1];
    if (jumpNew && ME.onGround) { v[1] = TR.hop; ME.onGround = false; p[1] += 0.03; mechsfx.boost(null, 0.35); sfx.squeak(null, 1); }
  }
  // the ram charge: drifting on the floor faster than drift.min (the server times its own; this is the HUD's guess)
  const hs = Math.hypot(v[0], v[2]);
  if (TS.drift && ME.onGround && hs >= TR.drift.min && !pushing) { TS.ch = Math.min(1, chargeNow(now) + dt / TR.drift.build); TS.chT = now; }
  v[1] -= TR.grav * dt * 0.5;
  const was = ME.onGround;
  if (!was && v[1] < TS.minVy) TS.minVy = v[1];
  const res = movePlayer(p, v, dt, BOXES, was);
  if (!res.ground) v[1] -= TR.grav * dt * 0.5;
  ME.onGround = !!res.ground && v[1] <= 0.01;
  if (ME.onGround && !was) land();
  if (ME.onGround && res.ground.pad) { const pd = res.ground.pad; v[0] += pd[0]; v[1] = pd[1]; v[2] += pd[2]; ME.onGround = false; }
  if (res.wall && (hs > 12 || pushing)) { // into a wall: CLANG, and a push stops dead
    G.shake = Math.max(G.shake, pushing ? 0.8 : 0.45); mechsfx.ram(null, pushing); rfx.sparks([p[0], p[1] + 1, p[2]], 14, 8, [0xffffff, 0xffe14d], 0.3, 0.1);
    if (pushing) { TS.push.until = now; v[0] *= 0.2; v[2] *= 0.2; }
  }
  ME.eyeH += (TR.eye - ME.eyeH) * Math.min(1, dt * 8);
  return true;
}
function land() {
  const impact = -TS.minVy; TS.minVy = 0;
  const k = clamp((impact - 6) / 22, 0, 1);
  MS.landT = 0; MS.landK = k;
  if (impact > 7) { A.dustRing(ME.pos, 2 + k * 2.5, k); mechsfx.step(null, 0.9, true); G.shake = Math.max(G.shake, 0.3 + k * 0.4); punchCam(-0.03 - k * 0.03); sfx.rattle(null, 1); sfx.squeak(null, 0.9); }
}

// ------------------------------------------------------------ every frame
function update(dt, now) {
  const v = ME.vel, hs = Math.hypot(v[0], v[2]), k = clamp(hs / TR.speed, 0, 1.4);
  for (const x of ['tossT', 'scoopT', 'dumpT']) TS[x] += dt;
  // tin cans: hold fire, 3 a second, along where the crosshair really points
  if (TS.lmb && now >= TS.canNext) {
    TS.canNext = now + 1000 / TR.can.rate;
    const d = A.aimDir().d;
    net.send({ t: 'mech', k: 'can', d: d.map(r2) });
    TS.tossT = 0; sfx.toss(null); punchCam(-0.008);
  }
  // squeaky wheels (faster = higher, more often), the basket rattling
  if (ME.onGround && hs > 1.5) {
    TS.squeakT -= dt * (0.6 + hs / 6);
    if (TS.squeakT <= 0) { TS.squeakT = 1 + Math.random() * 0.8; sfx.squeak(null, k); if (hs > 10) sfx.rattle(null, k); }
    G.shake = Math.max(G.shake, 0.02 + k * 0.05);
  }
  // drifting: the squeal, sparks off the casters, smoke; the HUD says when the charge is full
  const drifting = TS.drift && ME.onGround && hs >= TR.drift.min;
  if (drifting) {
    TS.squealT -= dt;
    if (TS.squealT <= 0) { TS.squealT = 0.28; sfx.squeal(null, 0.6 + chargeNow(now) * 0.6); }
    const inst = MS.inst;
    if (inst && Math.random() < dt * 40) for (const c of ['FL', 'FR', 'BL', 'BR']) { const w = inst.j['wheel_' + c]; if (!w) continue; const q = w.getWorldPosition(new THREE.Vector3()); rfx.sparks([q.x, q.y - 0.25, q.z], 2, 5, chargeNow(now) >= 1 ? [0xff4fd8, 0xffe14d, 0xffffff] : [0xffe14d, 0xffffff, 0xff7a3d], 0.3, 0.07); }
    if (Math.random() < dt * 14) rfx.smoke([ME.pos[0], ME.pos[1] + 0.2, ME.pos[2]], 1, 0xd8dde2, 0.7, 0.4, 0.9, 0.6);
    G.shake = Math.max(G.shake, 0.08 + chargeNow(now) * 0.12);
  }
  const ch = chargeNow(now);
  if (ch >= 1 && !TS.full) { TS.full = true; hud.msg('RAM CHARGED', 0.9, 'brag'); sfx.charged(); }
  if (ch < 1) TS.full = false;
  // AISLE 5: the boosters roar, speed lines of smoke
  if (TS.aisle > now && Math.random() < dt * 40) { const inst = MS.inst; for (const s of ['L', 'R']) { const mk = inst && inst.att['mk_thrust_' + s]; if (mk) { const q = mk.getWorldPosition(new THREE.Vector3()); rfx.smoke([q.x, q.y, q.z], 1, 0xdfe4ea, 0.6, 0.2, 0.6, 0.15); } } }
  if (TS.aisle && TS.aisle <= now) TS.aisle = 0;
  const u = Math.floor(MS.ult || 0);
  if (u >= 100 && TS.ultWas < 100) { hud.msg(`AISLE 5 READY · ${K.label('lastSlot')}`, 1.6, 'brag'); sfx.tannoy(null); }
  TS.ultWas = u;
  hudLine(true, now, ch);
  carryRemotes();
}
// the pilot's own HUD line: the ram charge, AISLE 5's clock and the basket
function hudLine(on, now = 0, ch = 0) {
  if (!on) { if (TS.hud) TS.hud.style.display = 'none'; return; }
  if (!TS.hud) {
    const el = document.createElement('div');
    el.style.cssText = 'position:absolute;left:50%;top:64%;transform:translateX(-50%) rotate(-1.5deg);padding:3px 12px;font-family:var(--font);font-weight:bold;font-size:16px;color:#fff;background:rgba(18,8,24,.92);border:3px solid #ff4fd8;box-shadow:5px 5px 0 #4fd8ff;pointer-events:none;white-space:nowrap';
    (document.getElementById('hud') || document.body).append(el); TS.hud = el;
  }
  const al = TS.aisle > now ? (TS.aisle - now) / 1000 : 0, n = TS.bk;
  const show = ch > 0.02 || al > 0;
  TS.hud.style.display = show ? 'block' : 'none';
  if (!show) return;
  const bars = Math.round(ch * 8), key = `${bars}|${al.toFixed(1)}|${n}`;
  if (TS.hud.dataset.k === key) return;
  TS.hud.dataset.k = key;
  TS.hud.innerHTML = (al > 0 ? `<span style="color:#4fd8ff">AISLE 5 ${al.toFixed(1)}s</span> · BASKET ${n}/${TR.aisle.max}${ch > 0.02 ? ' · ' : ''}` : '')
    + (ch > 0.02 ? `RAM <span style="color:${ch >= 1 ? '#ff4fd8' : '#ffe14d'}">${'▮'.repeat(bars)}${'▯'.repeat(8 - bars)}</span>` : '');
}
function flags(now) { return (TS.drift ? MF.DRIFT : 0) | (TS.aisle > now ? MF.AISLE : 0) | (TS.push && now < TS.push.until ? MF.PUSH : 0); }
function pose(now) {
  return { drift: TS.drift && ME.onGround && Math.hypot(ME.vel[0], ME.vel[2]) > 4 ? 1 : 0, push: TS.push && now < TS.push.until ? (now - TS.push.t0) / (TS.push.until - TS.push.t0) : 0,
    aisle: TS.aisle > now ? 1 : 0, boost: TS.aisle > now ? 1 : 0, rider: [...TS.held.values()].some((h) => h.s === 'ride') ? 1 : 0, scoopT: TS.scoopT, dumpT: TS.dumpT, tossT: TS.tossT, n: TS.bk, brake: TS.brake ? 1 : 0 };
}
// the people in your basket are where your trolley (your own, ahead of the network) has them, not a beat behind
const _v = new THREE.Vector3();
function carryRemotes() {
  const inst = MS.inst;
  if (!inst || !TS.held.size) return;
  inst.root.updateMatrixWorld(true);
  for (const [id, h] of TS.held) {
    const r = G.remotes.get(id);
    if (!r || !r.ch || !r.alive) continue;
    const l = h.s === 'ride' ? TR.seat : TR.scoop[h.i] || TR.scoop[0];
    const w = trSpot(ME.pos, ME.yaw, l);
    if (inst.att.mk_scoop && h.s !== 'ride') { inst.att.mk_scoop.getWorldPosition(_v); w[1] = _v.y; } // (it rides the tipping basket)
    r.ch.root.position.set(w[0], w[1], w[2]);
  }
}

// ------------------------------------------------------------ everyone else's (and the replay's ghosts)
function remote(r, st, dt, now) {
  const S = st.tr || (st.tr = { held: new Map(), scoopT: 9, dumpT: 9, tossT: 9, squeakT: 0, squealT: 0, pushT: 9 });
  for (const x of ['scoopT', 'dumpT', 'tossT', 'pushT']) S[x] += dt;
  const fl = r.f, hs = Math.hypot(r.vel[0], r.vel[2]), drift = !!(fl & MF.DRIFT) && hs > 4, aisleOn = !!(fl & MF.AISLE), pushing = !!(fl & MF.PUSH);
  if (!r.ghost && hs > 1.5 && Math.abs(r.vel[1]) < 2) { S.squeakT -= dt * (0.6 + hs / 6); if (S.squeakT <= 0) { S.squeakT = 1.2 + Math.random(); sfx.squeak(r.pos, clamp(hs / TR.speed, 0, 1.3)); } }
  if (drift) {
    if (!r.ghost) { S.squealT -= dt; if (S.squealT <= 0) { S.squealT = 0.3; sfx.squeal(r.pos, 0.8); } }
    if (Math.random() < dt * 30) rfx.sparks([r.pos[0] + (Math.random() - 0.5) * 2, r.pos[1] + 0.05, r.pos[2] + (Math.random() - 0.5) * 2], 3, 5, [0xffe14d, 0xffffff, 0xff7a3d], 0.3, 0.07);
  }
  if (pushing && S.pushT > 0.5) S.pushT = 0;
  return { drift: drift ? 1 : 0, push: pushing ? Math.min(0.99, S.pushT / TR.push.len) : 0, aisle: aisleOn ? 1 : 0, boost: aisleOn ? 1 : 0,
    rider: [...S.held.values()].some((h) => h.s === 'ride') ? 1 : 0, scoopT: S.scoopT, dumpT: S.dumpT, tossT: S.tossT, n: [...S.held.values()].filter((h) => h.s === 'scoop').length };
}

// ------------------------------------------------------------ riding / scooped (you, in someone else's trolley)
const GS = { held: null, near: 0, pr: null, jumpWas: true, warnT: 0 };
const remoteTrolley = (id) => { const r = G.remotes.get(id); return r && r.alive && r.mechOn && r.mechF === 'trolley' ? r : null; };
// your movement while carried: wherever the carrier's trolley (as you see it) puts you. the server does the same
// with its own copy of it and ignores what your client says
function held(dt, inp, now) {
  const H = GS.held;
  if (!H || !ME.alive) return false;
  const r = remoteTrolley(H.by);
  if (!r) { if (now - H.t0 > 2500) GS.held = null; return true; } // (a moment for the 'let go' to arrive)
  const l = H.s === 'ride' ? TR.seat : TR.scoop[H.i] || TR.scoop[0];
  const w = trSpot(r.pos, r.yaw, l);
  ME.pos = w; ME.vel = r.vel.slice(); ME.onGround = true; ME.hook = null; ME.sliding = false; ME.dashing = false;
  const jumpNew = inp.jump && !GS.jumpWas; GS.jumpWas = !!inp.jump;
  if (H.s === 'ride' && jumpNew) unride();
  if (H.s === 'scoop' && (inp.jump || inp.f || inp.b || inp.l || inp.r) && now > GS.warnT) { GS.warnT = now + 2500; hud.msg('YOU\'RE IN THE BASKET', 1.2, 'slip'); }
  return true;
}
function unride() { if (GS.held && GS.held.s === 'ride') net.send({ t: 'mech', k: 'unride' }); }
// keys while you're not in a mech: F next to an ally's trolley rides it; carried, the basket has your hands
const SCOOP_STOP = ['fire', 'aim', 'grapple', 'item', 'dash', 'crouch', 'spray', 'reload', 'streak1', 'streak2', 'streak3', 'slot1', 'slot2', 'slot3', 'slot4', 'lastSlot', 'scythe', 'parry', 'use'];
const RIDE_STOP = ['grapple', 'dash', 'crouch', 'streak1', 'streak2', 'streak3', 'scythe'];
function guestKey(e, down, now) {
  const H = GS.held;
  if (H) {
    if (!down) return undefined;
    if (H.s === 'ride') { if (!e.repeat && K.matches('use', e)) { unride(); return true; } return K.matches(RIDE_STOP, e) ? true : undefined; }
    return K.matches(SCOOP_STOP, e) ? true : undefined;
  }
  if (!down || e.repeat || !ME.alive || !K.matches('use', e) || !GS.near) return undefined;
  net.send({ t: 'mech', k: 'ride', to: GS.near });
  return true;
}
// every frame, not in a mech: the "hop in" prompt next to an ally's trolley, and the carrier drawn round you
function guest(dt, now) {
  GS.near = 0;
  if (!MS.on && !GS.held && ME.alive && G.joined) {
    for (const r of G.remotes.values()) {
      if (!r.alive || !r.mechOn || r.mechF !== 'trolley' || !isFriend(r)) continue;
      if (Math.hypot(r.pos[0] - ME.pos[0], r.pos[2] - ME.pos[2]) <= TR.ride.reach + TR.hw - 0.2 && Math.abs(r.pos[1] - ME.pos[1]) < 2.5) { GS.near = r.id; break; }
    }
  }
  const H = GS.held, txt = GS.near ? `${K.label('use')} · HOP IN THE BASKET` : H && H.s === 'ride' ? `${K.label('use')} / ${K.label('jump')} · HOP OUT` : '';
  if (txt || GS.pr) {
    if (!GS.pr) { GS.pr = document.createElement('div'); GS.pr.style.cssText = 'position:absolute;left:50%;top:62%;transform:translateX(-50%) rotate(-2deg);padding:6px 14px;font-family:var(--font);font-weight:bold;font-size:20px;background:#ffe14d;color:#000;border:3px solid #000;box-shadow:5px 5px 0 #ff4fd8;pointer-events:none;display:none'; (document.getElementById('hud') || document.body).append(GS.pr); }
    GS.pr.style.display = txt ? 'block' : 'none';
    if (txt && GS.pr.textContent !== txt) GS.pr.textContent = txt;
  }
  // carried: the trolley's drawn where you are (your view of it is a beat behind; you're where it is now)
  if (H && ME.alive) {
    const r = remoteTrolley(H.by);
    if (r && r.ch) { const l = H.s === 'ride' ? TR.seat : TR.scoop[H.i] || TR.scoop[0], o = trSpot([0, 0, 0], r.yaw, l); r.ch.root.position.set(ME.pos[0] - o[0], ME.pos[1] - o[1], ME.pos[2] - o[2]); }
  }
  if (H && !ME.alive) GS.held = null;
}

// ------------------------------------------------------------ the server's events
const EVENTS = new Set(['trtoss', 'trbonk', 'trpush', 'trhit', 'traisle', 'trhold', 'mheld']);
function event(m, getR, live, me, r, st) {
  const P = (x) => (Array.isArray(x) && x.length === 3 && x.every(Number.isFinite) ? x : null);
  const S = st ? st.tr || (st.tr = { held: new Map(), scoopT: 9, dumpT: 9, tossT: 9, squeakT: 0, squealT: 0, pushT: 9 }) : null, pos = A.posOf(m.id, getR);
  switch (m.k) {
    case 'trtoss': if (S) S.tossT = 0; if (pos && !me) sfx.toss(pos); break;
    case 'trbonk': { // a can found someone
      const p = P(m.p);
      if (!p) break;
      sfx.bonk(me ? null : p);
      rfx.sparks(p, 12, 6, [0xffffff, 0xc8d2dc, 0xe8262e], 0.35, 0.09);
      if (live && m.to === G.myId) { hud.msg('BONK', 0.6, 'slip'); G.shake = Math.max(G.shake, 0.3); }
      else if (me) hud.msg('BONK', 0.45, 'brag');
      break;
    }
    case 'trpush':
      if (S) S.pushT = 0;
      if (me && TS.push && Number.isFinite(m.v)) TS.push.v = m.v; // (the server's: what your charge really was)
      if (pos && !me) { sfx.shove(pos, Number(m.c) || 0); A.dustRing(pos, 2.5, 0.6); }
      break;
    case 'trhit': { // the push connected: hit-stop, sparks, a red impact frame for a big one
      const p = P(m.p), big = !!m.big;
      if (p) { sfx.hit(me ? null : p, big); rfx.sparks(p, big ? 40 : 18, big ? 12 : 8, [0xffffff, 0xffe14d, 0xff3030], 0.45, 0.12); rmesh.flash(p, big ? 3 : 1.6, 0xfff0b0, 0.15); }
      if (me) { TS.hitStop = big ? 0.09 : 0.05; G.shake = Math.max(G.shake, big ? 1 : 0.6); punchCam(-0.05); if (big && hud.impact) hud.impact(0.8); hud.msg(big ? "TROLLEY'D" : 'SHOVED', 0.8, 'brag'); }
      else if (live && m.to === G.myId) { G.shake = Math.max(G.shake, 0.9); if (big && hud.impact) hud.impact(0.6); }
      break;
    }
    case 'traisle':
      if (m.on === 1) { if (pos && !me) { sfx.tannoy(pos); mechsfx.jet(pos, 4); } if (live && !me && pos && Math.hypot(pos[0] - ME.pos[0], pos[2] - ME.pos[2]) < 40) hud.msg('CLEAN UP ON AISLE 5', 1.4, 'slip'); }
      else {
        if (S) S.dumpT = 0;
        if (me) { TS.aisle = 0; TS.dumpT = 0; if (m.n > 0) { hud.msg(m.n >= 3 ? 'CLEAN UP COMPLETE' : 'DUMPED', 1.2, 'brag'); G.shake = Math.max(G.shake, 0.7); } }
        if (pos && (m.n > 0)) { sfx.dump(me ? null : pos); rfx.debris([pos[0], pos[1] + 1.5, pos[2]], 14, 6, [0xc8d2dc, 0xe8262e, 0xffe14d]); }
      }
      break;
    case 'trhold': case 'mheld': {
      const on = m.on === 1, s = m.s === 'ride' ? 'ride' : 'scoop', i = Number.isInteger(m.i) ? clamp(m.i, 0, TR.scoop.length - 1) : 0;
      if (S) { if (on) S.held.set(m.v, { s, i }); else S.held.delete(m.v); if (on && s === 'scoop') S.scoopT = 0; }
      if (me && live) { if (on) TS.held.set(m.v, { s, i }); else TS.held.delete(m.v); if (Number.isFinite(m.n)) TS.bk = m.n; else TS.bk = [...TS.held.values()].filter((h) => h.s === 'scoop').length; if (on && s === 'scoop') TS.scoopT = 0; }
      const vp = A.posOf(m.v, getR) || pos;
      if (on && s === 'scoop' && vp) { sfx.kaching(live && m.v === G.myId ? null : vp); rfx.sparks([vp[0], vp[1] + 1, vp[2]], 14, 6, [0x4fd8ff, 0xffffff, 0xffe14d], 0.4, 0.1); }
      if (on && s === 'ride' && vp) sfx.seat(live && (me || m.v === G.myId) ? null : vp);
      if (me && on) hud.msg(s === 'scoop' ? 'SCOOPED' : `${A.nameOf(m.v).name.toUpperCase()} HOPPED IN`, 0.8, 'brag');
      if (live && m.v === G.myId) { // you
        if (on) {
          const fresh = !GS.held || GS.held.by !== m.id;
          GS.held = { by: m.id, s, i, t0: nowMs() }; GS.jumpWas = true;
          if (fresh) {
            W.held = false; W.aimHeld = false;
            if (s === 'scoop') { hud.msg("YOU'VE BEEN SCOOPED", 1.6, 'slip'); if (hud.impact) hud.impact(0.7); G.shake = Math.max(G.shake, 0.8); }
            else hud.msg('POUND COIN ACCEPTED · YOU\'RE THE GUNNER', 1.6, 'brag');
          }
        } else if (GS.held && GS.held.by === m.id) {
          GS.held = null;
          if (m.why === 'dump') hud.msg('DUMPED', 1, 'slip');
          else if (m.why === 'break') hud.msg('THE TROLLEY BROKE', 1, 'slip');
        }
      }
      break;
    }
  }
}

export const TRK = {
  abil: [['fire', 'CANS', ''], ['sprint', 'DRIFT', ''], ['grapple', 'PUSH', 'push'], ['lastSlot', 'AISLE 5', 'ult']],
  cds: ['push'],
  events: EVENTS,
  help: () => `hold ${K.label('fire')} tin cans · hold ${K.label('sprint')} drift (fast = RAM CHARGE) · ${K.label('grapple')} trolley push · ${K.label('aim')} brake · ${K.label('lastSlot')} CLEAN UP AISLE 5 (again: dump) · allies ${K.label('use')} to ride`,
  start() { clearState(); TS.ultWas = 0; },
  end() { clearState(); },
  reset() { clearState(); GS.held = null; },
  denied(why) { if (/ultimate/.test(why)) TS.aisle = 0; },
  en(m, now) { if (Number.isFinite(m.ch)) { TS.srvCh = m.ch; if (m.ch === 0 && TS.ch > 0 && !(TS.drift && Math.hypot(ME.vel[0], ME.vel[2]) >= TR.drift.min)) TS.ch = 0; else if (m.ch > TS.ch) { TS.ch = m.ch; TS.chT = now; } } if (Number.isFinite(m.au) && (m.au > 0 || now - (TS.aisleT0 || 0) > 700)) TS.aisle = m.au > 0 ? now + m.au : 0; if (Number.isFinite(m.bk)) TS.bk = m.bk; }, // (the server's charge, clock and basket)
  key, step, update, flags, pose, remote, event,
  guestKey, guest, held,
};
