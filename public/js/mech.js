// MECH DROP killstreak, the client (design: docs/mechs/PLAY.md, numbers: /shared/mech.js, the server judges every
// hit: server/mech.js). Here: the marker and the drop out of the sky, the mech standing there with its hatch glowing,
// you inside it (movement for both frames, the moves, a third-person camera, the HUD), everyone else's mechs (Remote
// and the replay ghosts call mechRemote), and the server's 'mech' events (impacts, callouts, sounds, the eject blast).
import * as THREE from 'three';
import { BOXES } from '/shared/map.js';
import { raycast, movePlayer } from '/shared/physics.js';
import { FLAGS } from '/shared/weapons.js';
import { MECH, MF, mechFrame, mechBoxes, energyAt, spend, newEnergy, mechClash, mechBody, mechRoom, FRAMES } from '/shared/mech.js';
import { G } from './ctx.js';
import { ME, eye, look, hspeed, releaseHook, ballOn } from './player.js';
import { W, punchCam, isFriend } from './weapons.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { fx } from './fx.js';
import { K } from './keys.js';
import { recordEv } from './replay.js';
import { rfx, rmesh } from './rigmodel.js';
import { rigOn } from './rig.js';
import { buildMech, freeMech, poseMech, mechBurst, buildCrane, GLB_ID, modelVer } from './mechmodel.js';
import { mechsfx } from './mechsfx.js';
import './mechlooksfx.js'; // (the hero clips' beats: their sounds)
import { prefetch, whenLate } from './glbkit.js';
import { WBK } from './mech_wrecking.js'; // battle island heroes: each kit's controls, moves, effects in its own file
import { TRK } from './mech_trolley.js';
import { VMK } from './mech_vending.js';

export { mechBoxes };
const PP = MECH.paperplane, NS = MECH.nightshift;
// the battle island heroes (public/js/mech_<id>.js): { help, abil, cds, start, end, key, step, update, flags, pose, remote, event, events, reset }
// (+ optional: en (the server's meter message), world (every frame, in a mech or not: things it put out in the world),
// footKey (a key on foot: the vending machine's kick); a kit that carries people: guestKey / guest / held, for you in someone else's)
const KITS = { wrecking: WBK, vending: VMK, trolley: TRK };
const r2 = (x) => Math.round(x * 100) / 100;
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const $ = (id) => document.getElementById(id);
const nameOf = (id) => (id === G.myId ? { name: G.myName || 'you', color: G.myColor || '#fff' } : G.names.get(id) || { name: '???', color: '#fff' });
const shakeNear = (at, k, r) => { const d = Math.hypot(at[0] - ME.pos[0], at[1] - ME.pos[1], at[2] - ME.pos[2]); G.shake = Math.max(G.shake, k * Math.max(0, 1 - d / r)); };
const nowMs = () => performance.now();

// ------------------------------------------------------------ state
export const MS = { on: false, f: 'paperplane', id: 0, E: newEnergy(0), hp: 0, max: 1, cd: {}, jetUntil: 0, dash: null, hover: false, hoverT0: 0, jumpHeld: 0,
  lmb: false, rmb: false, gunNext: 0, gunT: 9, gunSide: 1, combo: { i: -1, t: 0 }, swingT: 9, swingI: 0, blockT: 0, slam: null, triple: null, inst: null,
  camLen: 0, landT: 9, landK: 0, minVy: 0, stepPhase: 0, swarmT: 9, craneOut: 0, hero: null, boostT: 9 };
const FRAMEOF = new Map(); // player id -> the frame they're in (from 'in' and 'list')
const WM = new Map(); // mech id -> the mechs out in the world: falling, waiting, empty { id, o, f, p, yaw, st, until, inst, mk, t0, ms }
const DRONES = new Map(); // crane drones in the air
const MARKS = new Map(); // player id -> overtime marks over their head { n, until, el }
for (const f of FRAMES) whenLate(GLB_ID[f], () => { if (MS.inst && !MS.on) { freeMech(MS.inst); MS.inst = null; } }); // a hero model landed: rebuilt next time
export const mechOn = () => MS.on && ME.alive;
export const mechHeroOn = () => !!MS.hero && !MS.on && performance.now() - MS.hero.t0 < 1500; // (the landing shot: no gun in the picture)
export const myFrame = () => mechFrame(G.settings && G.settings.loadout && G.settings.loadout.mech);
// your loadout has the streak: get its hero model ahead of time
export function mechPrefetch(lo) { if (lo && Array.isArray(lo.streaks) && lo.streaks.includes('mechdrop')) prefetch([GLB_ID[mechFrame(lo.mech)]]); }

// ------------------------------------------------------------ calling it in (main.js deployStreak asks first)
// the same checks the server makes, so the tray keeps it when it would be refused. returns true = blocked
export function mechDeployBlock(id, at, frame) { // (frame: battle island's hero, else your loadout's)
  const inBall = ballOn(nowMs());
  if (mechClash(id, mechOn(), rigOn(), inBall, myWaiting() !== null)) {
    hud.msg(id === 'mechdrop' ? (myWaiting() ? 'your mech is already out' : 'not right now (it keeps for later)') : 'not in a mech (it keeps for later)', 1.2); mechsfx.denied(); return true;
  }
  if (id !== 'mechdrop') return false;
  const e = eye(), d = [at[0] - e[0], at[1] - e[1], at[2] - e[2]], l = Math.hypot(d[0], d[1], d[2]);
  const fl = raycast([at[0], at[1] + 0.5, at[2]], [0, -1, 0], 4.5, BOXES);
  const why = l > MECH.drop.range ? `too far (${MECH.drop.range} m max)` : !fl ? 'aim at the floor' : '';
  if (why) { hud.msg(`MECH DROP: ${why.toUpperCase()}`, 1.2); mechsfx.denied(); return true; }
  if (!mechRoom([at[0], fl.point[1], at[2]], frame ? mechFrame(frame) : myFrame(), BOXES)) { hud.msg('NO ROOM FOR IT HERE', 1.4); mechsfx.denied(); return true; } // (a roof, an overhang, a wall: the whole mech has to fit)
  return false;
}
function myWaiting() { for (const m of WM.values()) if (m.o === G.myId && m.st !== 'in') return m; return null; }

// ------------------------------------------------------------ you, in it
function startLocal(m) {
  const f = mechFrame(m.f), F = MECH[f];
  Object.assign(MS, { on: true, f, id: m.m, E: newEnergy(nowMs()), hp: m.hp, max: m.max || F.hp, cd: {}, jetUntil: 0, dash: null, hover: false, lmb: false, rmb: false, combo: { i: -1, t: 0 },
    slam: null, triple: null, camLen: 0, minVy: 0, swingT: 9, swarmT: 9, gunT: 9, craneOut: 0, landT: 0, landK: 0.6, startT: nowMs(), hero: null });
  if (Array.isArray(m.p)) { ME.pos = m.p.slice(); ME.vel = [0, 0, 0]; }
  ME.eyeH = F.eye;
  releaseHook();
  W.held = false; W.aimHeld = false; W.dashHeld = false; W.charge = 0; W.aim = 0; W.zoom = 1; W.scoped = false;
  ME.dashing = false; ME.sliding = false;
  hud.scope(false); hud.ammo(null); hud.meter(null); hud.cards(null);
  if (MS.inst && (MS.inst.frame !== f || MS.inst.v !== modelVer)) { freeMech(MS.inst); MS.inst = null; } // (another frame, or a better model landed)
  if (!MS.inst) MS.inst = buildMech(f, G.myColor);
  G.scene.add(MS.inst.root); MS.inst.root.visible = true;
  document.body.classList.add('mechin');
  mechsfx.climb(null);
  G.shake = Math.max(G.shake, 0.6);
  hud.msg(F.name + ' ONLINE', 1.6, 'brag');
  if (KITS[f]) { MS.ult = 0; KITS[f].start(MS); }
  hud.chat(null, null, KITS[f] ? `${F.name}: ${KITS[f].help()} · ${K.label('use')} hop out` : f === 'paperplane'
    ? `${F.name}: ${K.label('fire')} cannons · hold ${K.label('jump')} hover · ${K.label('sprint')} boost lunge · ${K.label('aim')} missile swarm · ${K.label('grapple')} crane drone · ${K.label('lastSlot')} jet mode · ${K.label('use')} hop out`
    : `${F.name}: ${K.label('fire')} sword combo · hold ${K.label('aim')} tower shield (let go after a block: bash) · ${K.label('sprint')} triple shift · ${K.label('lastSlot')} ground slam · ${K.label('use')} hop out`);
  panel(true);
}
function endLocal(why) {
  if (!MS.on) return;
  MS.on = false;
  W.held = false; W.aimHeld = false; W.zoom = 1; W.swap = 1; // the gun comes back up
  document.body.classList.remove('mechin');
  panel(false);
  if (G.myBody && G.myBody.k === MS.f) G.myBody = null; // (its armour bar goes with it)
  if (KITS[MS.f]) KITS[MS.f].end(why);
  if (MS.inst) { if (why === 'boom') { mechBurst(MS.inst, ME.vel); const dead = MS.inst; MS.inst = null; setTimeout(() => freeMech(dead), 7000); } else MS.inst.root.removeFromParent(); }
  MS.camLen = Math.min(MS.camLen, 3);
}

// ------------------------------------------------------------ input (main.js pressed() / released())
const BLOCKED = ['item', 'reload', 'slot1', 'slot2', 'slot3', 'slot4', 'scythe', 'dash', 'crouch', 'spray', 'parry', 'nvgFlash'];
export function mechKey(e, down) {
  if (!G.joined) return false;
  const now = nowMs();
  if (!MS.on) { // F next to your own waiting mech: climb in
    for (const k of Object.values(KITS)) if (k.guestKey) { const r = k.guestKey(e, down, now); if (r !== undefined) return r; } // (someone else's: riding in it, or carried)
    if (!down || !ME.alive || e.repeat || !K.matches('use', e)) return false;
    for (const k of Object.values(KITS)) if (k.footKey && k.footKey(e, now)) return true; // (on foot at someone's mech: a jammed vending machine's kick)
    const m = myWaiting();
    if (!m || m.st === 'fall' || Math.hypot(m.p[0] - ME.pos[0], m.p[2] - ME.pos[2]) > MECH.reach + 0.4) return false;
    net.send({ t: 'mech', k: 'in' });
    return true;
  }
  if (!ME.alive) return false;
  const kit = KITS[MS.f];
  if (kit) { // a hero's own keys; F hops out, the rest of the game's keys do nothing in here
    const r = kit.key(e, down, now);
    if (r !== undefined) return r;
    if (!down) return false;
    if (e.repeat) return K.matches(['fire', 'aim', 'sprint', 'grapple', 'lastSlot', 'use', ...BLOCKED], e);
    if (K.matches('use', e)) { net.send({ t: 'mech', k: 'out' }); return true; }
    if (K.matches(BLOCKED, e)) { if (K.matches('item', e)) hud.msg('no items in a mech', 0.8); return true; }
    return false;
  }
  const pp = MS.f === 'paperplane';
  if (!down) {
    if (K.up('fire', e)) MS.lmb = false;
    if (K.up('aim', e) && MS.rmb) { MS.rmb = false; if (!pp && now - MS.blockT < NS.shield.bashWin * 1000) bash(now); }
    return false;
  }
  if (e.repeat) return K.matches(['fire', 'aim', 'sprint', 'grapple', 'lastSlot', 'use', ...BLOCKED], e);
  if (K.matches('fire', e)) { MS.lmb = true; if (!pp) swing(now); return true; }
  if (K.matches('aim', e)) { if (pp) swarm(now); else MS.rmb = true; return true; }
  if (K.matches('sprint', e)) { if (pp) lunge(now); else triple(now); return true; }
  if (K.matches('grapple', e)) { if (pp) crane(now); else hud.msg('no grapple in a mech', 0.8); return true; }
  if (K.matches('lastSlot', e)) { if (pp) jet(now); else slam(now); return true; }
  if (K.matches('use', e)) { net.send({ t: 'mech', k: 'out' }); return true; }
  if (K.matches(BLOCKED, e)) { if (K.matches('item', e)) hud.msg('no items in a mech', 0.8); return true; }
  return false;
}
const cdLeft = (k, now) => Math.max(0, (MS.cd[k] || 0) - now);
function denied(what, now, k) { hud.msg(`${what} ${(cdLeft(k, now) / 1000).toFixed(1)}s`, 0.6); mechsfx.denied(); }
// the enemy nearest the crosshair (cone, range, in plain sight): the lunge's and the crane's lock
function pick(range, cos) {
  const o = eye(), d = aimDir().d;
  let best = null, bs = -1;
  for (const r of G.remotes.values()) {
    if (!r.alive || isFriend(r)) continue;
    const c = centerOf(r), v = [c[0] - o[0], c[1] - o[1], c[2] - o[2]], l = Math.hypot(v[0], v[1], v[2]);
    if (l > range || l < 1) continue;
    const s = (v[0] * d[0] + v[1] * d[1] + v[2] * d[2]) / l;
    if (s < cos || s - l * 0.002 <= bs || raycast(o, [v[0] / l, v[1] / l, v[2] / l], l - 0.6, BOXES)) continue;
    bs = s - l * 0.002; best = { r, c, l };
  }
  return best;
}
const centerOf = (r) => [r.pos[0], r.pos[1] + (r.mechOn ? MECH[r.mechF].h * 0.45 : 1.0), r.pos[2]];
// ---- PAPER PLANE
function lunge(now) {
  const L = PP.lunge;
  if (MS.dash || now < MS.jetUntil) return;
  if (!spend(MS.E, L.cost, now)) { hud.msg('NO ENERGY', 0.6); mechsfx.denied(); return; }
  const t = pick(L.lock, L.cos), d = look();
  let dir = t ? [t.c[0] - ME.pos[0], t.c[1] - ME.pos[1] - 1.5, t.c[2] - ME.pos[2]] : [d[0], Math.max(0, d[1]) * 0.4, d[2]];
  const l = Math.hypot(dir[0], dir[1], dir[2]) || 1; dir = dir.map((x) => x / l);
  const dist = t ? clamp(t.l - 1.2, 3, L.dist) : L.dist;
  MS.dash = { k: 'lunge', t0: now, until: now + dist / L.speed * 1000, dir };
  net.send({ t: 'mech', k: 'lunge', to: t ? t.r.id : 0, d: aimDir().d.map(r2) });
  mechsfx.boost(null, 1); punchCam(0.03); G.shake = Math.max(G.shake, 0.4); MS.boostT = 0;
  if (t) hud.msg('LOCKED', 0.5, 'brag');
}
function crane(now) {
  const C = PP.crane;
  if (cdLeft('crane', now)) { denied('CRANE', now, 'crane'); return; }
  const t = pick(C.range, C.cos);
  if (!t) { hud.msg('CRANE: NO TARGET', 0.7); mechsfx.denied(); return; }
  MS.cd.crane = now + C.cd * 1000;
  net.send({ t: 'mech', k: 'crane', to: t.r.id });
}
function swarm(now) {
  if (now < MS.jetUntil) return;
  if (cdLeft('swarm', now)) { denied('SWARM', now, 'swarm'); return; }
  MS.cd.swarm = now + PP.swarm.cd * 1000; MS.swarmT = 0;
  net.send({ t: 'mech', k: 'swarm', d: aimDir().d.map(r2) });
  mechsfx.swarm(null); punchCam(-0.03); G.shake = Math.max(G.shake, 0.4);
  hud.msg('MISSILE SWARM', 0.9, 'brag');
}
function jet(now) {
  const J = PP.jet;
  if (now < MS.jetUntil) { MS.jetUntil = 0; net.send({ t: 'mech', k: 'jet', on: 0 }); return; }
  if (cdLeft('jet', now)) { denied('JET MODE', now, 'jet'); return; }
  MS.cd.jet = now + (J.cd + J.dur) * 1000; MS.jetUntil = now + J.dur * 1000;
  net.send({ t: 'mech', k: 'jet', on: 1 });
  mechsfx.jet(null, J.dur); G.shake = Math.max(G.shake, 0.6); punchCam(0.04);
  hud.msg('JET MODE', 1, 'brag');
}
// ---- NIGHT SHIFT
function swing(now) {
  const S = NS.sword, C = MS.combo;
  if (MS.slam || MS.triple || MS.rmb) return;
  if (C.i >= 0 && now - C.t < S.cd[C.i] * 1000 - 60) return;
  const i = C.i >= 0 && C.i < 2 && now - C.t < S.combo * 1000 + S.cd[C.i] * 1000 ? C.i + 1 : 0;
  C.i = i; C.t = now; MS.swingT = 0; MS.swingI = i;
  net.send({ t: 'mech', k: 'swing' });
  setTimeout(() => { mechsfx.whoosh(null, i === 2); G.shake = Math.max(G.shake, i === 2 ? 0.5 : 0.25); punchCam(i === 2 ? -0.05 : -0.02, i === 1 ? 0.02 : -0.02); }, 90);
}
function bash(now) {
  if (cdLeft('bash', now)) return;
  MS.cd.bash = now + NS.shield.bashCd * 1000; MS.blockT = 0; MS.bashT = now;
  net.send({ t: 'mech', k: 'bash' });
  mechsfx.bash(null); G.shake = Math.max(G.shake, 0.5); punchCam(-0.04);
  hud.msg('SHIELD BASH', 0.7, 'brag');
}
function triple(now) {
  const T = NS.triple;
  if (MS.triple || MS.slam) return;
  if (!spend(MS.E, T.cost, now)) { hud.msg('NO ENERGY', 0.6); mechsfx.denied(); return; }
  MS.triple = { t0: now, cut: -1 };
  net.send({ t: 'mech', k: 'triple' });
  hud.msg('TRIPLE SHIFT', 0.9, 'brag');
}
function slam(now) {
  if (MS.slam || MS.triple) return;
  if (cdLeft('slam', now)) { denied('SLAM', now, 'slam'); return; }
  MS.cd.slam = now + NS.slam.cd * 1000;
  MS.slam = { t0: now, ph: 1 };
  ME.vel[1] = NS.slam.up; ME.onGround = false; ME.pos[1] += 0.05;
  net.send({ t: 'mech', k: 'slam' });
  mechsfx.slamUp(null); G.shake = Math.max(G.shake, 0.4);
}

// ------------------------------------------------------------ movement (player.js stepPlayer hands the step over)
export function mechStep(dt, inp, now) {
  if (!MS.on && ME.alive) for (const k of Object.values(KITS)) if (k.held && k.held(dt, inp, now)) return true; // carried in someone else's (the trolley's basket)
  if (!MS.on || !ME.alive) return false;
  if (KITS[MS.f]) return KITS[MS.f].step(dt, inp, now); // a hero moves its own way
  const F = MECH[MS.f], v = ME.vel, p = ME.pos, pp = MS.f === 'paperplane';
  ME.hook = null; ME.sliding = false; ME.crouching = false; ME.sprinting = false; ME.dashing = false;
  const fw = (inp.f ? 1 : 0) - (inp.b ? 1 : 0), st = (inp.r ? 1 : 0) - (inp.l ? 1 : 0);
  const s = Math.sin(ME.yaw), c = Math.cos(ME.yaw);
  let wx = -s * fw + c * st, wz = -c * fw - s * st;
  const wl = Math.hypot(wx, wz);
  if (wl) { wx /= wl; wz /= wl; }
  let top = F.speed, grav = F.grav, fixed = false;
  MS.jumpHeld = inp.jump ? MS.jumpHeld + dt : 0;
  MS.hover = false;
  if (pp && now < MS.jetUntil) { // jet mode: straight where you look, no gravity
    const d = look(); for (let i = 0; i < 3; i++) v[i] += (d[i] * PP.jet.speed - v[i]) * Math.min(1, dt * 6);
    fixed = true;
  } else if (MS.dash) { // the boost lunge
    if (now > MS.dash.until) { MS.dash = null; v[0] *= 0.3; v[2] *= 0.3; v[1] = Math.min(v[1], 3); }
    else { for (let i = 0; i < 3; i++) v[i] = MS.dash.dir[i] * PP.lunge.speed; fixed = true; }
  } else if (MS.triple) { // three dashing cuts, each a short burst the way you look
    const T = NS.triple, k = (now - MS.triple.t0) / 1000 - T.lead, n = k < 0 ? -1 : Math.floor(k / T.gap), inDash = n >= 0 && n < T.n && k - n * T.gap < T.len;
    if (n !== MS.triple.cut && n < T.n) { MS.triple.cut = n; const d = look(), hl = Math.hypot(d[0], d[2]) || 1; MS.triple.dir = [d[0] / hl, 0, d[2] / hl]; MS.swingT = 0; MS.swingI = n % 2; mechsfx.boost(null, 0.6); mechsfx.whoosh(null, n === 2); G.shake = Math.max(G.shake, 0.35); punchCam(0.02, n % 2 ? 0.03 : -0.03); }
    if (inDash) { v[0] = MS.triple.dir[0] * T.speed; v[2] = MS.triple.dir[2] * T.speed; fixed = true; grav *= 0.3; }
    else { v[0] *= Math.max(0, 1 - dt * 12); v[2] *= Math.max(0, 1 - dt * 12); }
    if (k > T.gap * (T.n - 1) + T.len + 0.08) MS.triple = null; // (cuts land on triple_shift's hit frames: shared/mech.js)
  }
  if (MS.slam) { // up, hang, then straight down
    if (MS.slam.ph === 1 && v[1] < 0) { MS.slam.ph = 2; mechsfx.boost(null, 1); }
    if (MS.slam.ph === 2) { v[1] = -NS.slam.down; grav = 0; }
    if (now - MS.slam.t0 > NS.slam.win * 1000) MS.slam = null;
    top *= 0.6;
  }
  if (pp && !fixed && !ME.onGround && inp.jump && (MS.jumpHeld > 0.15 || v[1] < 4) && energyAt(MS.E, now) > 0) { // hover
    if (!MS.hoverT0) { MS.hoverT0 = now; mechsfx.hover(null); }
    MS.hover = true;
    MS.E.v = Math.max(0, MS.E.v - PP.hover.drain * dt); MS.E.t = now;
    const want = now - MS.hoverT0 < PP.hover.rise * 1000 ? PP.hover.up : 0;
    v[1] += (want - v[1]) * Math.min(1, dt * 5); grav = 0; top = PP.hover.speed;
    if (Math.random() < dt * 8) mechsfx.hover(null);
  } else if (!inp.jump) MS.hoverT0 = 0;
  if (!pp && MS.rmb) top *= NS.shield.slow;
  if (!fixed) {
    const hs = Math.hypot(v[0], v[2]);
    if (ME.onGround || MS.hover) {
      if (hs > 0) { const ns = Math.max(0, hs - Math.max(hs, 3) * F.fric * (wl ? 0.45 : 1) * dt) / hs; v[0] *= ns; v[2] *= ns; }
      if (wl) push(v, wx, wz, top, F.accel, dt);
    } else if (wl) push(v, wx, wz, Math.min(top, F.airCap), F.accel * 0.6, dt);
    if (ME.onGround && inp.jump && MS.jumpHeld <= dt + 1e-6 && !MS.slam) { // a hop (the knight's leg boosters kick)
      v[1] = F.hop; ME.onGround = false; p[1] += 0.03; MS.boostT = 0;
      mechsfx.boost(null, 0.5); rfx.dust(p, 10, 1.2, 4);
    }
  }
  if (!fixed) v[1] -= grav * dt * 0.5;
  const was = ME.onGround;
  if (!was && v[1] < MS.minVy) MS.minVy = v[1];
  const res = movePlayer(p, v, dt, BOXES, was && !fixed, mechBody(MS.f)); // (its own big body: a door lower than it stops it)
  if (!fixed && !res.ground) v[1] -= grav * dt * 0.5;
  ME.onGround = !!res.ground && v[1] <= 0.01;
  if (res.wall && MS.dash) { MS.dash = null; v[0] *= 0.3; v[2] *= 0.3; G.shake = Math.max(G.shake, 0.5); mechsfx.ram(null); }
  if (ME.onGround && !was) land(now);
  if (ME.onGround && res.ground.pad) { const pd = res.ground.pad; v[0] += pd[0]; v[1] = pd[1]; v[2] += pd[2]; ME.onGround = false; }
  // footsteps: tons of mech, every one shakes
  const hs2 = Math.hypot(v[0], v[2]);
  if (ME.onGround && hs2 > 1.2 && !fixed) {
    const w0 = Math.floor(MS.stepPhase);
    MS.stepPhase += dt * (0.7 + hs2 * (pp ? 0.16 : 0.13));
    if (Math.floor(MS.stepPhase) !== w0) step(hs2);
  }
  ME.eyeH += (F.eye - ME.eyeH) * Math.min(1, dt * 8);
  return true;
}
function push(v, wx, wz, top, accel, dt) { const cur = v[0] * wx + v[2] * wz, add = top - cur; if (add > 0) { const a = Math.min(add, accel * top * dt); v[0] += a * wx; v[2] += a * wz; } }
function step(hs) {
  const run = clamp(hs / 14, 0, 1), heavy = MS.f === 'nightshift';
  G.shake = Math.max(G.shake, (heavy ? 0.2 : 0.12) + run * 0.12);
  punchCam(-0.006 - run * 0.008);
  mechsfx.step(null, 0.6 + run * 0.4, heavy);
  rfx.dust(ME.pos, 4 + Math.round(run * 4), 0.8, 2 + run * 2);
}
function land(now) {
  const impact = -MS.minVy;
  MS.minVy = 0;
  const k = clamp((impact - 6) / 26, 0, 1);
  MS.landT = 0; MS.landK = k;
  if (MS.slam && MS.slam.ph === 2) {
    net.send({ t: 'mech', k: 'slamland', p: ME.pos.map(r2) });
    MS.slam = null;
    quakeFx(ME.pos, NS.slam.r, true);
    return;
  }
  if (impact > 8) { dustRing(ME.pos, 2.5 + k * 4, k); mechsfx.step(null, 1.2, true); G.shake = Math.max(G.shake, 0.4 + k * 0.5); punchCam(-0.03 - k * 0.04); }
}
function dustRing(p, r, k) {
  const fl = raycast([p[0], p[1] + 0.5, p[2]], [0, -1, 0], 3, BOXES), at = [p[0], fl ? fl.point[1] : p[1], p[2]];
  rmesh.ring(at, r, 0xffffff, 0.35); rmesh.ring(at, r * 0.7, 0xffe0a8, 0.5);
  rfx.dust(at, 16 + Math.round(k * 20), r * 0.5, r * 1.2);
}
function quakeFx(p, r, mine) {
  const fl = raycast([p[0], p[1] + 0.5, p[2]], [0, -1, 0], 3, BOXES), at = [p[0], fl ? fl.point[1] : p[1], p[2]];
  rmesh.ring(at, r * 1.15, 0xffffff, 0.35); rmesh.ring(at, r * 0.85, 0xb98cff, 0.55); rmesh.ring(at, r * 1.5, 0xffe14d, 0.75);
  rfx.dust(at, 40, r * 0.6, r * 1.4); rfx.debris(at, 30, 9);
  rmesh.crater(at, 2.6); rmesh.flash([at[0], at[1] + 1, at[2]], 3, 0xd8c0ff, 0.25);
  mechsfx.quake(mine ? null : at);
  if (mine) { G.shake = Math.max(G.shake, 1.2); punchCam(-0.08); hud.impact && hud.impact(1); } else shakeNear(at, 1, 30);
}

// ------------------------------------------------------------ every frame (main.js, after the camera is set)
export function updateMech(dt, now, cam, replaying) {
  updateWorld(dt, now, replaying);
  for (const k of Object.values(KITS)) if (k.world) k.world(dt, now, replaying); // (colas, walls: a kit's things out in the world)
  updateDrones(dt);
  updateMarks(now, cam);
  prompt(now);
  if (MS.on && (!G.joined || !ME.alive)) endLocal('dead');
  for (const k of Object.values(KITS)) if (k.guest) k.guest(dt, now); // (someone else's: the hop-in prompt, riding)
  if (!MS.on) return;
  for (const k of ['gunT', 'swingT', 'swarmT', 'landT', 'boostT']) MS[k] += dt;
  const pp = MS.f === 'paperplane', jet = now < MS.jetUntil;
  // cannons: held fire, 8 a second, alternating barrels. your tracer right away; the server says what it hit
  if (pp && MS.lmb && !jet && now >= MS.gunNext) {
    MS.gunNext = now + 1000 / PP.gun.rate; MS.gunT = 0; MS.gunSide = -MS.gunSide;
    const A = aimDir(), d = A.d;
    net.send({ t: 'mech', k: 'gun', d: d.map(r2) });
    const e = eye(), h = raycast(e, d, PP.gun.range, BOXES), end = h && h.t < Math.hypot(A.p[0] - e[0], A.p[1] - e[1], A.p[2] - e[2]) ? h.point : A.p;
    const mz = MS.inst && MS.inst.att['mk_muzzle_' + (MS.gunSide > 0 ? 'R' : 'L')];
    const from = mz ? mz.getWorldPosition(new THREE.Vector3()).toArray() : e;
    fx.tracer(from, end, 0x4fd8ff, 0.14, 0.2);
    rfx.sparks(end, 6, 6, [0xffffff, 0x4fd8ff], 0.3, 0.1); rfx.sparks(from, 5, 4, [0xfff2a0, 0xffffff], 0.15, 0.1);
    mechsfx.gun(null, 0.8); punchCam(-0.006, (Math.random() - 0.5) * 0.004); G.shake = Math.max(G.shake, 0.08);
  }
  // your mech, in third person
  const inst = MS.inst, kit = KITS[MS.f];
  if (kit) kit.update(dt, now, inst);
  if (inst) {
    inst.root.position.set(ME.pos[0], ME.pos[1], ME.pos[2]);
    inst.root.rotation.set(0, ME.yaw, 0);
    inst.root.visible = !replaying && MS.camLen > 2.2;
    const s = Math.sin(ME.yaw), c = Math.cos(ME.yaw);
    poseMech(inst, {
      spd: ME.onGround ? hspeed() : 0, fwd: -(ME.vel[0] * s + ME.vel[2] * c), side: ME.vel[0] * c - ME.vel[2] * s, air: !ME.onGround, vy: ME.vel[1],
      hover: MS.hover, jet: jet ? 1 : 0, dash: !!MS.dash || !!(MS.triple && MS.triple.dir && (now - MS.triple.t0) / 1000 - NS.triple.lead >= 0 && ((now - MS.triple.t0) / 1000 - NS.triple.lead) % NS.triple.gap < NS.triple.len), shield: MS.rmb,
      swingT: MS.swingT, swingI: MS.swingI, slam: MS.slam ? MS.slam.ph : 0, gunT: MS.gunT, gunSide: MS.gunSide, swarmT: MS.swarmT, craneOut: MS.craneOut > now,
      landT: MS.landT, landK: MS.landK, pitch: ME.pitch, boost: MS.boostT < 0.3 ? 1 - MS.boostT / 0.3 : 0, slashing: MS.swingT > 0.08 && MS.swingT < 0.32 || !!MS.triple || (MS.slam && MS.slam.ph === 2),
      ...(kit ? kit.pose(now) : null),
    }, dt);
    if (jet && Math.random() < dt * 40) rfx.smoke([ME.pos[0], ME.pos[1] + 2.5, ME.pos[2]], 1, 0xdfe4ea, 0.8, 0.2, 0.7, 0.3);
  }
  panelUpdate(now);
}
// weapons.js updateWeapons hands over the viewmodel while you're in a mech: no gun, the snapshot flags
export function mechVM(dt, now, vmRoot) {
  if (!MS.on || !ME.alive) return false;
  if (vmRoot) vmRoot.visible = false;
  const pp = MS.f === 'paperplane';
  W.flags = KITS[MS.f] ? FLAGS.MECH | KITS[MS.f].flags(now) : FLAGS.MECH | (pp ? (MS.hover ? MF.HOVER : 0) | (now < MS.jetUntil ? MF.JET : 0) | (MS.dash ? MF.DASH : 0)
    : (MS.rmb ? MF.SHIELD : 0) | (MS.slam ? MF.SLAM : 0) | (MS.triple ? MF.SLASH : 0));
  W.aim = 0; W.scoped = false; W.held = false; W.aimHeld = false;
  W.zoom = now < MS.jetUntil ? 1.35 : 1; // (the speed's fov kick would make the jet a speck)
  ME.speedMul = 1;
  hud.ammo(null); hud.meter(null);
  const P = G.punch; // the camera's punch spring (weapons.js steps it, but not while we have the viewmodel)
  if (P) { const n = Math.min(40, Math.max(1, Math.ceil(dt * 240))), h = dt / n; for (let i = 0; i < n; i++) for (const a of ['x', 'y', 'z']) { P['v' + a] += (-160 * P[a] - 18 * P['v' + a]) * h; P[a] += P['v' + a] * h; } }
  return true;
}
// third person: a boom straight back from a pivot over the cockpit along your view (so the crosshair is exactly where
// the server aims from). pulls out at speed / in jet mode, never through a wall. and the heroic low shot when your
// mech lands near you
export function mechCam(cam, dt) {
  const now = nowMs();
  if (MS.hero && !MS.on) {
    const H = MS.hero, k = (now - H.t0) / 1000;
    if (k < 1.5 && ME.alive && G.joined) {
      const u = clamp(k / 1.5, 0, 1), a = H.a + 0.55 + u * 0.4, d = [Math.sin(a), 0.04, Math.cos(a)]; // low, off to the side, slowly orbiting
      const sc = MECH.scale, c0 = [H.p[0], H.p[1] + 0.6 * sc, H.p[2]], hit = raycast(c0, d, 7 * sc, BOXES), R = Math.max(2.5, Math.min((6.5 - u * 1.2) * sc, hit ? hit.t - 0.6 : 99)); // (never inside a wall; it backs off as far as the mech grew)
      cam.position.set(c0[0] + d[0] * R, c0[1] + d[1] * R, c0[2] + d[2] * R);
      cam.lookAt(H.p[0], H.p[1] + 3.9 * sc, H.p[2]);
      const sh = (G.shake || 0) * (G.shake || 0) * 0.08; if (sh) cam.rotation.set(cam.rotation.x + (Math.random() - 0.5) * sh, cam.rotation.y + (Math.random() - 0.5) * sh, cam.rotation.z); // (the landing still shakes)
      return;
    }
    MS.hero = null;
  }
  if (!G.joined || !ME.alive || !MS.on) { MS.camLen = 0; return; }
  const F = MECH[MS.f], d = look(), e0 = eye();
  // over the right shoulder (a step right and up from the cockpit), so the mech isn't in the way of the crosshair
  const sh = SHOULDER[MS.f].map((x) => x * MECH.scale), rt = [Math.cos(ME.yaw), 0, -Math.sin(ME.yaw)], side = raycast(e0, rt, sh[0] + 0.4, BOXES); // (the shoulder grows with the mech)
  const sx = side ? Math.max(0, side.t - 0.4) : sh[0], e = [e0[0] + rt[0] * sx, e0[1] + sh[1], e0[2] + rt[2] * sx];
  const want = F.cam * 0.8 + Math.min(3, hspeed() * 0.06) + (now < MS.jetUntil ? 2 : 0);
  const hit = raycast(e, [-d[0], -d[1], -d[2]], want + 0.5, BOXES);
  const ax = hit && hit.axis >= 0 ? Math.abs(d[hit.axis]) : 1;
  const free = hit ? Math.max(0.15, Math.min(want, hit.t - Math.min(1, 0.3 / Math.max(0.3, ax)))) : want;
  if (MS.camLen > free) MS.camLen = free;
  MS.camLen += (free - MS.camLen) * Math.min(1, dt * (free > MS.camLen ? 2.5 : 10));
  cam.position.set(e[0] - d[0] * MS.camLen, e[1] - d[1] * MS.camLen, e[2] - d[2] * MS.camLen);
}

const SHOULDER = { paperplane: [1.7, 0.5], nightshift: [2.1, 0.6], wrecking: [1.2, 1.4], vending: [1.9, 0.5], trolley: [1.1, 1.0] }; // the camera's step right + up
// where the crosshair really points (the camera sits off to the side): the direction from the cockpit to whatever the
// screen centre is on, so shots and locks go where you aim
export function aimDir() {
  const c = G.camera.position, d = look(), from = [c.x, c.y, c.z], h = raycast(from, d, 220, BOXES);
  let far = h ? h.t : 220;
  for (const r of G.remotes.values()) { if (!r.alive || !r.hitboxes) continue; for (const b of r.hitboxes()) { const t = rayAabb(from, d, b); if (t != null && t < far) far = t; } }
  const p = [from[0] + d[0] * far, from[1] + d[1] * far, from[2] + d[2] * far], e = eye(), v = [p[0] - e[0], p[1] - e[1], p[2] - e[2]], l = Math.hypot(v[0], v[1], v[2]);
  return { d: l > 2 ? v.map((x) => x / l) : d, p };
}
function rayAabb(o, d, b) {
  let t0 = 0, t1 = 1e9;
  for (let i = 0; i < 3; i++) {
    if (Math.abs(d[i]) < 1e-9) { if (o[i] < b.min[i] || o[i] > b.max[i]) return null; continue; }
    let a = (b.min[i] - o[i]) / d[i], c = (b.max[i] - o[i]) / d[i];
    if (a > c) [a, c] = [c, a];
    t0 = Math.max(t0, a); t1 = Math.min(t1, c);
    if (t0 > t1) return null;
  }
  return t0 > 0.5 ? t0 : null;
}

// ------------------------------------------------------------ HUD: the mech panel + the climb-in prompt
let styleOn = false;
function css() {
  if (styleOn) return; styleOn = true;
  const s = document.createElement('style');
  s.textContent = `#mechHud{display:none;position:absolute;left:18px;bottom:64px;transform:rotate(-1deg);width:360px;padding:7px 13px 9px;font-family:var(--font);font-size:13px;font-weight:bold;color:#fff;background:rgba(18,8,24,.92);border:4px solid #ff4fd8;box-shadow:8px 8px 0 #4fd8ff;pointer-events:none}
#mechHud .mh-top{display:flex;justify-content:space-between;align-items:baseline}#mechHud .mh-top b{color:#ffe14d;font-size:19px;letter-spacing:2px}#mechHud .mh-top span{font-size:20px;color:#4fd8ff}
#mechHud .mh-row{display:flex;align-items:center;gap:8px;margin:4px 0}#mechHud .mh-row>span{width:62px}#mechHud .mh-row em{width:44px;text-align:right;font-style:normal}
#mechHud .mh-bar{position:relative;flex:1;height:12px;background:rgba(255,255,255,.1);border:2px solid #000}#mechHud .mh-bar i{position:absolute;left:0;top:0;bottom:0;display:block}
#mechHud .mh-ar i{background:repeating-linear-gradient(60deg,#ff4fd8 0 6px,#c0279f 6px 9px)}#mechHud .mh-en i{background:#39ff14}#mechHud.low .mh-ar i{background:#ff3030}
#mechHud .mh-ab{display:flex;gap:6px;margin-top:6px}#mechHud .mh-ab>div{flex:1;text-align:center;padding:3px 0;border:2px solid #fff;background:#000;opacity:.55;font-size:11px;line-height:1.15}
#mechHud .mh-ab>div.ready{opacity:1;border-color:#ffe14d;color:#ffe14d;box-shadow:3px 3px 0 #ff4fd8}#mechHud .mh-ab kbd{display:block;font-family:inherit;color:#4fd8ff}
#mechHud .mh-ab em{display:block;font-style:normal;color:#fff}#mechHud .mh-ab>div.ult{background:#ff4fd8;color:#000;border-color:#000;animation:mhUlt .5s steps(2) infinite}#mechHud .mh-ab>div.ult em,#mechHud .mh-ab>div.ult kbd{color:#000}@keyframes mhUlt{50%{transform:rotate(-3deg) scale(1.06)}}#mechPrompt{display:none;position:absolute;left:50%;top:62%;transform:translateX(-50%) rotate(-2deg);padding:6px 14px;font-family:var(--font);font-weight:bold;font-size:20px;background:#ffe14d;color:#000;border:3px solid #000;box-shadow:5px 5px 0 #ff4fd8;pointer-events:none}
.mechMark{position:absolute;transform:translate(-50%,-100%);font-family:var(--font);font-weight:bold;font-size:15px;color:#ffe14d;background:rgba(18,8,24,.85);border:2px solid #ff4fd8;padding:0 5px;pointer-events:none;white-space:nowrap}
.mechMark.out{color:#000;background:#ffe14d;font-size:18px;border-color:#000;box-shadow:4px 4px 0 #ff4fd8}`;
  document.head.append(s);
}
let el = null;
const ABIL = { paperplane: [['sprint', 'LUNGE', 'lunge'], ['aim', 'SWARM', 'swarm'], ['grapple', 'CRANE', 'crane'], ['lastSlot', 'JET', 'jet']], nightshift: [['aim', 'SHIELD', ''], ['sprint', 'TRIPLE', 'triple'], ['lastSlot', 'SLAM', 'slam'], ['use', 'HOP OUT', '']] };
for (const [f, k] of Object.entries(KITS)) ABIL[f] = k.abil; // (a hero's: [key, NAME, cooldown key, energy cost]; 'ult' = its ultimate)
function panel(on) {
  css();
  if (!el) { el = document.createElement('div'); el.id = 'mechHud'; $('hud').append(el); }
  el.style.display = on ? 'block' : 'none';
  if (!on) return;
  el.innerHTML = `<div class="mh-top"><b>${MECH[MS.f].name}</b><span class="mh-n"></span></div><div class="mh-row mh-ar"><span>ARMOUR</span><div class="mh-bar"><i></i></div><em></em></div>`
    + `<div class="mh-row mh-en"><span>ENERGY</span><div class="mh-bar"><i></i></div><em></em></div><div class="mh-ab">${ABIL[MS.f].map(([k, n, c]) => `<div data-c="${c}"><kbd>${K.label(k)}</kbd>${n}<em></em></div>`).join('')}</div>`;
  el.dataset.key = '';
}
function panelUpdate(now) {
  if (!el) return;
  const b = G.myBody && G.myBody.k === MS.f ? G.myBody : null;
  if (b) { MS.hp = b.hp; MS.max = b.max; }
  const en = energyAt(MS.E, now), jet = Math.max(0, MS.jetUntil - now);
  const key = [Math.round(MS.hp), Math.round(en), ...ABIL[MS.f].map(([, , c]) => Math.ceil(cdLeft(c, now) / 100)), Math.ceil(jet / 100), MS.rmb ? 1 : 0, Math.floor(MS.ult || 0)].join('|');
  if (el.dataset.key === key) return;
  el.dataset.key = key;
  el.querySelector('.mh-n').textContent = `${Math.max(0, Math.round(MS.hp))} / ${MS.max}`;
  el.querySelector('.mh-ar i').style.width = clamp(MS.hp / MS.max, 0, 1) * 100 + '%';
  el.querySelector('.mh-ar em').textContent = Math.round(MS.hp);
  el.querySelector('.mh-en i').style.width = en + '%';
  el.querySelector('.mh-en em').textContent = Math.round(en);
  el.classList.toggle('low', MS.hp < MS.max * 0.25);
  [...el.querySelectorAll('.mh-ab > div')].forEach((d) => {
    const c = d.dataset.c, left = c ? cdLeft(c, now) : 0, em = d.querySelector('em');
    const live = c === 'jet' && jet > 0;
    const ab = KITS[MS.f] && ABIL[MS.f].find((a) => a[2] === c);
    if (ab) { // a hero's: cooldown, energy cost, or the ultimate's charge
      const u = Math.floor(MS.ult || 0), ready = c === 'ult' ? u >= 100 : left <= 0 && (!ab[3] || en >= ab[3]);
      em.textContent = c === 'ult' ? (u >= 100 ? 'READY' : u + '%') : left > 0 ? (left / 1000).toFixed(1) + 's' : ab[3] ? `${ab[3]}E` : 'READY';
      d.classList.toggle('ready', ready); d.classList.toggle('ult', c === 'ult' && u >= 100);
      return;
    }
    em.textContent = live ? (jet / 1000).toFixed(1) + 's' : left > 0 ? (left / 1000).toFixed(1) + 's' : c === 'lunge' ? `${PP.lunge.cost}E` : c === 'triple' ? `${NS.triple.cost}E` : d.textContent.includes('SHIELD') && MS.rmb ? 'UP' : 'READY';
    d.classList.toggle('ready', live || (left <= 0 && (c === 'lunge' ? en >= PP.lunge.cost : c === 'triple' ? en >= NS.triple.cost : true)));
  });
}
let pr = null;
function prompt(now) {
  const m = !MS.on && ME.alive && G.joined ? myWaiting() : null;
  const near = m && m.st !== 'fall' && Math.hypot(m.p[0] - ME.pos[0], m.p[2] - ME.pos[2]) < MECH.reach + 4;
  if (!pr && !near) return;
  css();
  if (!pr) { pr = document.createElement('div'); pr.id = 'mechPrompt'; $('hud').append(pr); }
  pr.style.display = near ? 'block' : 'none';
  if (near) pr.textContent = `${K.label('use')} · CLIMB IN (${Math.max(0, Math.ceil((m.until - now) / 1000))}s)`;
}

// ------------------------------------------------------------ the mechs out in the world (falling, waiting, empty)
function wmSet(id, o, f, p, yaw, st, ms) {
  let m = WM.get(id);
  if (!m) { m = { id, o, f, p, yaw, st, t0: nowMs(), until: nowMs() + (ms || 0), inst: null }; WM.set(id, m); }
  Object.assign(m, { o, f, p, yaw, st });
  if (ms != null) m.until = nowMs() + ms;
  return m;
}
function wmDrop(m) {
  if (m.inst) { freeMech(m.inst); m.inst = null; }
  if (m.mk) { m.mk.removeFromParent(); m.mk.traverse((o) => { if (o.isMesh) { o.geometry.dispose(); o.material.dispose(); } }); m.mk = null; }
  WM.delete(m.id);
}
// the marker: a red ring and a beam up into the sky, pulsing faster as it falls
function marker(p) {
  const g = new THREE.Group();
  const ring = new THREE.Mesh(new THREE.RingGeometry(1.6, 2.2, 32).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0xff3030, transparent: true, opacity: 0.85, side: THREE.DoubleSide, depthWrite: false }));
  ring.position.y = 0.06;
  const cross = new THREE.Mesh(new THREE.RingGeometry(0.15, 0.4, 16).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0xffe14d, side: THREE.DoubleSide }));
  cross.position.y = 0.07;
  const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.35, 120, 8, 1, true).translate(0, 60, 0), new THREE.MeshBasicMaterial({ color: 0xff3030, transparent: true, opacity: 0.22, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
  g.add(ring, cross, beam);
  g.position.set(p[0], p[1], p[2]);
  g.userData = { ring, beam };
  G.scene.add(g);
  return g;
}
function updateWorld(dt, now, replaying) {
  for (const m of WM.values()) {
    if (m.st === 'in') { if (m.inst) m.inst.root.visible = false; if (m.mk) m.mk.visible = false; continue; }
    if (m.inst && m.inst.v !== modelVer) { freeMech(m.inst); m.inst = null; } // a better model landed
    if (!m.inst) { m.inst = buildMech(m.f, (nameOf(m.o) || {}).color); G.scene.add(m.inst.root); }
    const inst = m.inst;
    inst.root.visible = !replaying;
    let y = m.p[1], fall = 0;
    if (m.st === 'fall') {
      if (!m.mk) m.mk = marker(m.p);
      const k = clamp(1 - (m.until - now) / (m.ms || 2500), 0, 1);
      fall = 1 - k;
      y = m.p[1] + 140 * fall * fall;
      const pulse = 0.5 + 0.5 * Math.sin(now * (0.01 + k * 0.04));
      m.mk.userData.ring.material.opacity = 0.5 + pulse * 0.5; m.mk.userData.ring.scale.setScalar((1.4 - k * 0.5 + pulse * 0.1) * MECH.scale); // (the red circle is the squash circle: it grows with the mech)
      m.mk.userData.beam.material.opacity = 0.12 + pulse * 0.2;
      if (Math.random() < dt * 60) rfx.smoke([m.p[0], y + 3, m.p[2]], 2, 0xd8dde2, 1.3, 0.4, 1.6, 0.6); // a streak of smoke behind it
      if (Math.random() < dt * 30) rfx.sparks([m.p[0], y + 1, m.p[2]], 3, 6, [0xffe14d, 0xff7a3d], 0.3, 0.1, [0, 1, 0]);
    } else if (m.mk) { m.mk.removeFromParent(); m.mk = null; }
    if (m.st === 'leave') { const k = (now - m.t0) / 1500; y = m.p[1] + 60 * k * k; if (k > 1) { wmDrop(m); continue; } if (Math.random() < dt * 40) rfx.smoke([m.p[0], y + 1, m.p[2]], 2, 0xd8dde2, 1, -0.5, 1.2, 0.5); }
    inst.root.position.set(m.p[0], y, m.p[2]);
    inst.root.rotation.set(0, m.yaw, 0);
    poseMech(inst, { spd: 0, fwd: 0, side: 0, air: fall > 0.02 || m.st === 'leave', vy: 0, landT: (now - (m.landT || 0)) / 1000, landK: 1, pitch: 0, empty: m.st === 'wait' || m.st === 'idle', intro: !!m.landT, falling: m.st === 'fall', boost: m.st === 'leave' || fall > 0 ? 1 : 0, swingT: 9, gunT: 9, swarmT: 9 }, dt);
  }
}
function updateDrones(dt) {
  for (const d of DRONES.values()) {
    const k = Math.min(1, dt * 12);
    for (let i = 0; i < 3; i++) d.p[i] += (d.to[i] - d.p[i]) * k;
    const v = [d.to[0] - d.p[0], d.to[2] - d.p[2]];
    if (Math.hypot(v[0], v[1]) > 0.05) d.g.rotation.y = Math.atan2(-v[0], -v[1]);
    d.g.position.set(d.p[0], d.p[1] + Math.sin(nowMs() * 0.01) * 0.1, d.p[2]);
    const fl = Math.sin(nowMs() * 0.04) * 0.6;
    d.g.userData.wings[0].rotation.y = fl; d.g.userData.wings[1].rotation.y = -fl;
  }
}
const _v = new THREE.Vector3();
function updateMarks(now, cam) {
  for (const [id, mk] of MARKS) {
    const r = G.remotes.get(id), alive = id === G.myId ? ME.alive : r && r.alive;
    if (now > mk.until || !alive) { mk.el.remove(); MARKS.delete(id); continue; }
    const p = id === G.myId ? ME.pos : r.pos, h = id === G.myId ? (MS.on ? MECH[MS.f].h : 2.3) : r.mechOn ? MECH[r.mechF].h : 2.4;
    _v.set(p[0], p[1] + h + 0.6, p[2]).project(cam);
    const vis = _v.z < 1 && id !== G.myId;
    mk.el.style.display = vis ? 'block' : 'none';
    if (vis) { mk.el.style.left = (_v.x * 0.5 + 0.5) * innerWidth + 'px'; mk.el.style.top = (-_v.y * 0.5 + 0.5) * innerHeight + 'px'; }
  }
}
function setMark(id, n, ms, out) {
  css();
  let mk = MARKS.get(id);
  if (!mk) { mk = { el: document.createElement('div') }; mk.el.className = 'mechMark'; $('hud').append(mk.el); MARKS.set(id, mk); }
  mk.until = nowMs() + ms; mk.el.classList.toggle('out', !!out);
  mk.el.textContent = out ? 'CLOCKED OUT' : `OVERTIME ${'▮'.repeat(n)}${'▯'.repeat(Math.max(0, NS.overtime.marks - n))}`;
}

// ------------------------------------------------------------ everyone else (and replay ghosts): Remote.update calls this
export function mechRemote(r, dt, now) {
  const on = !!(r.f & FLAGS.MECH) && r.alive;
  let st = r.mech;
  if (!on) { if (st && st.on) remoteOff(r, st); r.mechOn = false; return; }
  const f = FRAMEOF.get(r.id) || 'paperplane', F = MECH[f];
  if (!st || st.f !== f || st.color !== r.color || st.root !== r.ch.root || st.inst.v !== modelVer) {
    if (st) freeMech(st.inst);
    st = r.mech = { inst: buildMech(f, r.color), f, color: r.color, root: r.ch.root, on: false, swingT: 9, swingI: 0, gunT: 9, gunSide: 1, swarmT: 9, landT: 9, landK: 0, minVy: 0, wasAir: false, craneOut: 0, bashT: 9 };
    st.inst.root.scale.setScalar(MECH.scale / 1.2); // (the mannequin's root is scaled up 1.2: the mech is its real size, plus the far-away scale)
    r.ch.root.add(st.inst.root);
  }
  if (!st.on) { st.on = true; if (r.buf.length > 2 && !r.ghost) mechsfx.climb(r.pos); }
  r.mechOn = true; r.mechF = f;
  st.inst.root.visible = true;
  r.ch.body.visible = false; r.rope.visible = false;
  if (r.weaponMesh) r.weaponMesh.visible = false;
  r.marker.position.y = (F.h + 0.8) / 1.2;
  r.tag.position.y += (F.h - 1.9) / 1.2;
  for (const k of ['swingT', 'gunT', 'swarmT', 'landT', 'bashT']) st[k] += dt;
  const fl = r.f, s = Math.sin(r.yaw), c = Math.cos(r.yaw), vx = r.vel[0], vz = r.vel[2];
  const air = Math.abs(r.vel[1]) > 1.5 && !(r.gy > -1e8 && r.pos[1] - r.gy < 0.3);
  if (air) st.minVy = Math.min(st.minVy, r.vel[1]);
  else if (st.wasAir) { if (st.minVy < -8) { st.landT = 0; st.landK = Math.min(1, -st.minVy / 30); dustRing(r.pos, 3 + st.landK * 3, st.landK); mechsfx.step(r.pos, 1.2, true); if (!r.ghost) shakeNear(r.pos, 0.5, 25); } st.minVy = 0; }
  st.wasAir = air;
  const pp = f === 'paperplane', hs = Math.hypot(vx, vz);
  if (KITS[f]) { // a hero: its own sounds and pose
    poseMech(st.inst, { spd: air ? 0 : hs, fwd: -(vx * s + vz * c), side: vx * c - vz * s, air, vy: r.vel[1], landT: st.landT, landK: st.landK, pitch: r.pitch, swingT: 9, gunT: 9, swarmT: 9, ...KITS[f].remote(r, st, dt, now) }, dt);
    r.shadow.scale.setScalar(2.8 * (r.distScale || 1));
    return;
  }
  // footsteps you hear (and feel) as they walk past
  if (!air && hs > 1.2) { const w0 = Math.floor(st.ph || 0); st.ph = (st.ph || 0) + dt * (0.7 + hs * (pp ? 0.16 : 0.13)); if (Math.floor(st.ph) !== w0) { mechsfx.step(r.pos, 0.5, !pp); if (!r.ghost) shakeNear(r.pos, 0.15, 18); } }
  poseMech(st.inst, {
    spd: air ? 0 : hs, fwd: -(vx * s + vz * c), side: vx * c - vz * s, air, vy: r.vel[1], hover: pp && !!(fl & MF.HOVER), jet: pp && (fl & MF.JET) ? 1 : 0,
    dash: !!(fl & MF.DASH), shield: !pp && !!(fl & MF.SHIELD), slam: !pp && (fl & MF.SLAM) ? (r.vel[1] < 0 ? 2 : 1) : 0, swingT: st.swingT, swingI: st.swingI,
    gunT: st.gunT, gunSide: st.gunSide, swarmT: st.swarmT, craneOut: st.craneOut > now, landT: st.landT, landK: st.landK, pitch: r.pitch,
    slashing: !pp && ((st.swingT > 0.08 && st.swingT < 0.32) || !!(fl & MF.SLASH)),
  }, dt);
  if (pp && (fl & MF.JET) && Math.random() < dt * 30) rfx.smoke([r.pos[0], r.pos[1] + 2.5, r.pos[2]], 1, 0xdfe4ea, 0.8, 0.2, 0.7, 0.3);
  r.shadow.scale.setScalar((pp ? 2.6 : 3.2) * MECH.scale * (r.distScale || 1));
}
function remoteOff(r, st) {
  st.on = false; st.inst.root.visible = false;
  r.ch.body.visible = true; r.marker.position.y = 2.75; r.shadow.scale.setScalar(1);
  if (r.weaponMesh) r.weaponMesh.visible = true;
}
export function mechDispose(r) { if (r.mech) { freeMech(r.mech.inst); r.mech = null; } }
// the remote's mech model for effects (null when they're not in one)
const instOf = (id, getR) => (id === G.myId ? (MS.on ? MS.inst : null) : (getR(id) && getR(id).mech && getR(id).mech.on ? getR(id).mech.inst : null));
const posOf = (id, getR) => (id === G.myId ? ME.pos : getR(id) ? getR(id).pos : null);

// ------------------------------------------------------------ server events: { t: 'mech', k }
// live (net) or in a killcam / play of the round (replay.js hands them over with its ghosts: live = false)
function mechEvent(m, getR, live) {
  const me = live && m.id === G.myId, r = getR(m.id), st = r && r.mech;
  for (const k of Object.values(KITS)) if (k.events.has(m.k)) { k.event(m, getR, live, me, r, st); return; } // a hero's own events
  const P = (x) => (Array.isArray(x) && x.length === 3 && x.every(Number.isFinite) ? x : null);
  switch (m.k) {
    case 'gun': {
      const b = P(m.b), inst = instOf(m.id, getR);
      if (!b || me) break;
      if (st) { st.gunT = 0; st.gunSide = m.s > 0 ? 1 : -1; }
      const mz = inst && inst.att['mk_muzzle_' + (m.s > 0 ? 'R' : 'L')], from = mz ? mz.getWorldPosition(new THREE.Vector3()).toArray() : r ? [r.pos[0], r.pos[1] + 4 * MECH.scale, r.pos[2]] : null;
      if (from) { fx.tracer(from, b, 0x4fd8ff, 0.09, 0.12); mechsfx.gun(from, 0.7); }
      if (m.h) rfx.sparks(b, 6, 6, [0xffffff, 0x4fd8ff], 0.25, 0.08);
      break;
    }
    case 'cut': { // a sword / lunge / bash hit lands: a glowing slash, sparks, a hit-stop for whoever swung it
      const p = P(m.p);
      if (!p) break;
      const big = m.w === 'mechbash' || m.w === 'mechlunge';
      rfx.sparks(p, big ? 40 : 26, big ? 14 : 11, m.w === 'mechlunge' ? [0xffffff, 0xff4fd8, 0x4fd8ff] : [0xffffff, 0xd8c0ff, 0xb98cff, 0xffe14d], 0.5, 0.14);
      rmesh.flash(p, big ? 2.4 : 1.8, 0xe8d8ff, 0.12);
      const pos = posOf(m.id, getR);
      if (pos) { const d = [p[0] - pos[0], 0, p[2] - pos[2]], l = Math.hypot(d[0], d[2]) || 1; rmesh.vring(p, [d[0] / l, 0, d[2] / l], 2.2, m.w === 'mechlunge' ? 0xff4fd8 : 0xb98cff, 0.25); }
      if (m.w === 'mechbash') mechsfx.bash(me ? null : p); else mechsfx.slash(me ? null : p);
      if (me) { G.shake = Math.max(G.shake, big ? 0.7 : 0.5); punchCam(-0.04, 0, (Math.random() - 0.5) * 0.04); hud.hit(false); }
      else if (live) shakeNear(p, 0.4, 20);
      if (live && m.to === G.myId) { G.shake = 1; hud.flash && hud.flash(0.35, 0.12); }
      break;
    }
    case 'heal': if (me) hud.msg(`+${m.a} ARMOUR`, 0.7, 'brag'); break;
    case 'lunge': { const pos = posOf(m.id, getR); if (pos && !me) { mechsfx.boost(pos, 1); rfx.sparks([pos[0], pos[1] + 2.5, pos[2]], 14, 8, [0xff4fd8, 0xffffff], 0.3, 0.1); } break; }
    case 'crane': {
      const p = P(m.p);
      if (!p) break;
      const g = buildCrane((nameOf(m.id) || {}).color); g.scale.setScalar(1.6); G.scene.add(g);
      DRONES.set(m.d, { g, p: p.slice(), to: p.slice(), owner: m.id });
      if (st) st.craneOut = nowMs() + 6000;
      if (me) { MS.craneOut = nowMs() + 6000; hud.msg('CRANE AWAY', 0.7, 'brag'); }
      mechsfx.crane(me ? null : p);
      break;
    }
    case 'cp': { const d = DRONES.get(m.d), p = P(m.p); if (d && p) d.to = p; break; }
    case 'peck': { const p = P(m.p), d = DRONES.get(m.d); if (p) { rfx.sparks([p[0], p[1] - 1, p[2]], 8, 5, [0xffffff, 0xff4fd8], 0.25, 0.08); mechsfx.peck(p); if (d) d.g.rotation.x = 0.8; setTimeout(() => { if (d) d.g.rotation.x = 0; }, 90); } break; }
    case 'cranex': { const d = DRONES.get(m.d); if (d) { d.g.removeFromParent(); DRONES.delete(m.d); if (d.owner === G.myId) MS.craneOut = 0; const o = getR(d.owner); if (o && o.mech) o.mech.craneOut = 0; if (!m.home) rfx.smoke(d.p, 4, 0xffffff, 0.4, 0.5, 0.6, 0.2); } break; }
    case 'swarm': { if (st) st.swarmT = 0; const pos = posOf(m.id, getR); if (pos && !me) mechsfx.swarm(pos); break; }
    case 'jet': { const pos = posOf(m.id, getR); if (m.on && pos && !me) { mechsfx.jet(pos, (m.ms || 6000) / 1000); rmesh.ring([pos[0], pos[1] + 0.2, pos[2]], 5, 0x4fd8ff, 0.4); } if (me && !m.on) MS.jetUntil = 0; break; }
    case 'swing': { if (st && !me) { st.swingT = 0; st.swingI = m.i | 0; const pos = posOf(m.id, getR); if (pos) mechsfx.whoosh(pos, m.i === 2); } break; }
    case 'bash': if (st && !me) st.bashT = 0; break;
    case 'triple': { const pos = posOf(m.id, getR); if (pos && !me) mechsfx.boost(pos, 0.8); break; }
    case 'slam': { const pos = posOf(m.id, getR); if (pos && !me) mechsfx.slamUp(pos); break; }
    case 'quake': { const p = P(m.p); if (p && !me) quakeFx(p, m.r || NS.slam.r, false); if (live && me) hud.msg('GROUND SLAM', 0.8, 'brag'); break; }
    case 'blk': { // the tower shield takes it: a clang and sparks off the shield face
      const inst = instOf(m.id, getR), sh = inst && inst.att.mk_shield_face;
      const at = sh ? sh.getWorldPosition(new THREE.Vector3()).toArray() : posOf(m.id, getR);
      if (at) { rfx.sparks(at, 14, 8, [0xffffff, 0xffe14d, 0x4fd8ff], 0.35, 0.1); mechsfx.clang(me ? null : at, Math.min(1.3, 0.5 + (m.a || 10) / 30)); }
      if (me) { MS.blockT = nowMs(); G.shake = Math.max(G.shake, 0.25); }
      break;
    }
    case 'stomp': {
      const p = P(m.p);
      if (!p) break;
      mechsfx.stomp(p); rfx.debris(p, 16, 6); rmesh.ring(p, 3, 0xffe14d, 0.4);
      if (live && m.to === G.myId) { hud.msg('STOMPED', 1.6, 'slip'); G.shake = 1.2; }
      if (me) hud.msg('STOMPED', 1.2, 'brag');
      const v = getR(m.to);
      if (v && v.ch && !v.mechOn) { v.ch.root.scale.y *= 0.3; v.stompT = nowMs(); setTimeout(() => { if (v.ch) v.ch.root.scale.y = v.ch.root.scale.x; }, m.ms || 1400); } // flat as a pancake
      break;
    }
    case 'ram': {
      const p = P(m.p);
      if (!p) break;
      mechsfx.ram(p, !!m.big); rfx.sparks(p, m.big ? 36 : 18, m.big ? 14 : 9, [0xffffff, 0xffb040, 0xff4fd8], 0.4, 0.12); rmesh.flash(p, m.big ? 2.5 : 1.5, 0xffd9a0, 0.12);
      if (me) { G.shake = Math.max(G.shake, m.big ? 0.8 : 0.4); hud.msg(m.big ? 'JET RAM' : 'RAMMED', 0.7, 'brag'); }
      if (live && m.to === G.myId) G.shake = 1;
      break;
    }
    case 'mark': { setMark(m.to, m.n, m.ms || 4000); const pos = posOf(m.to, getR); if (pos) mechsfx.mark(pos, m.n); break; }
    case 'clock': {
      setMark(m.to, 0, m.ms || 1000, true);
      const pos = posOf(m.to, getR); if (pos) mechsfx.clock(pos);
      if (me) hud.msg('CLOCKED OUT', 1.4, 'brag');
      if (live && m.to === G.myId) hud.msg('CLOCKED OUT', 1.6, 'slip');
      break;
    }
    case 'squash': {
      if (live && m.to === G.myId) hud.msg('A MECH LANDED ON YOU', 1.8, 'slip');
      if (me) hud.msg('DROPPED A MECH ON THEM', 1.8, 'brag');
      const p = P(m.p); if (p) rfx.sparks([p[0], p[1] + 0.5, p[2]], 30, 9, [0xff3030, 0xffffff], 0.5, 0.15);
      break;
    }
    case 'bonk': { // your own mech landed on you (or a mate): no squash, a BEEP BEEP and a shove off the circle
      const p = P(m.p); if (p) { mechsfx.beep(p); rfx.sparks([p[0], p[1] + 1, p[2]], 16, 6, [0xffe14d, 0xffffff], 0.35, 0.1); rmesh.ring([p[0], p[1] + 0.1, p[2]], MECH.bonk.r, 0xffe14d, 0.35); }
      if (live && m.to === G.myId) { hud.msg(m.id === G.myId ? 'BEEP BEEP! MECH PARKING' : 'BEEP BEEP! MATE PARKING', 1.8, 'brag'); G.shake = Math.max(G.shake, 0.6); }
      break;
    }
    case 'down': { // MECH DOWN: the mech flashes and blows up in a big jank pop, the pilot's flung out
      const p = P(m.p), inst = instOf(m.id, getR);
      if (m.e) { const w = live && WM.get(m.m); if (w && w.inst) { const dead = w.inst; w.inst = null; mechBurst(dead); setTimeout(() => freeMech(dead), 7000); } if (me) hud.msg('YOUR EMPTY MECH GOT WRECKED', 2, 'slip'); } // nobody inside (mechempty.js)
      else if (me) { endLocal('boom'); mechsfx.eject(null); hud.msg('EJECT! EJECT!', 2, 'slip'); G.shake = 1.4; }
      else if (inst) { mechBurst(inst, r ? r.vel : [0, 0, 0]); if (r && r.mech) { const dead = r.mech.inst; r.mech = null; r.ch.body.visible = true; setTimeout(() => freeMech(dead), 7000); } }
      if (p) {
        mechsfx.boom(me ? null : p);
        rmesh.flash([p[0], p[1] + 2.5, p[2]], MECH.boom.r * 1.4, 0xff8a3a, 0.35); rmesh.ring(p, MECH.boom.r * 1.6, 0xffe14d, 0.5);
        rfx.smoke([p[0], p[1] + 2, p[2]], 30, 0x2c2c30, 1.6, 2.5, 2.4, 1.2); rfx.debris(p, 30, 10);
        if (live && !me) shakeNear(p, 1.2, 35);
      }
      if (live) {
        const who = nameOf(m.id), by = m.by ? nameOf(m.by) : null, fname = MECH[mechFrame(m.f)].name;
        if (by) hud.feed([[by.name, by.color], ['  MECH DOWN  ', '#ffe14d'], [`${who.name}'s ${fname}`, who.color]]);
        else hud.feed([[`${who.name}'s ${fname}`, who.color], ['  blew up', '#aaa']]);
        if (m.by === G.myId) hud.msg('MECH DOWN', 2, 'brag');
        WM.forEach((w) => { if (w.id === m.m) wmDrop(w); });
      }
      FRAMEOF.delete(m.id);
      break;
    }
  }
}
net.on('mech', (m) => {
  if (!m || typeof m.k !== 'string') return;
  const now = nowMs(), P = (x) => (Array.isArray(x) && x.length === 3 && x.every(Number.isFinite) ? x : null);
  switch (m.k) {
    case 'call': {
      const p = P(m.p);
      if (!p) return;
      const w = wmSet(m.id, m.o, mechFrame(m.f), p, Number(m.yaw) || 0, 'fall', m.ms || 2500); w.ms = m.ms || 2500;
      mechsfx.call(m.o === G.myId ? null : p, w.ms);
      if (m.o === G.myId) { hud.msg('MECH DROP', 2, 'brag'); G.shake = Math.max(G.shake, 0.3); }
      else hud.chat(null, null, `${nameOf(m.o).name} called in a MECH DROP: look up`);
      return;
    }
    case 'land': {
      const p = P(m.p);
      if (!p) return;
      const w = wmSet(m.id, m.o, mechFrame(m.f), p, Number(m.yaw) || 0, 'wait', MECH.wait * 1000); w.landT = now;
      mechsfx.land(p); quakeFx(p, MECH.drop.r, false);
      rmesh.flash([p[0], p[1] + 1, p[2]], 4, 0xffe8c0, 0.3);
      shakeNear(p, 1.4, 45);
      if (m.o === G.myId && ME.alive && !MS.on && Math.hypot(p[0] - ME.pos[0], p[2] - ME.pos[2]) < 45) { // the heroic low shot
        MS.hero = { t0: now, p, a: Math.atan2(ME.pos[0] - p[0], ME.pos[2] - p[2]) - 0.2 };
        hud.msg(`${K.label('use')} TO CLIMB IN`, 2, 'brag');
      }
      return;
    }
    case 'list': {
      if (!Array.isArray(m.m)) return;
      const seen = new Set();
      for (const e of m.m) {
        if (!Array.isArray(e) || e.length < 9) continue;
        const [id, o, f, x, y, z, yaw, st, left] = e, p = P([x, y, z]);
        if (!p || typeof st !== 'string') continue;
        seen.add(id);
        if (st === 'in') { FRAMEOF.set(o, mechFrame(f)); const w = WM.get(id); if (w) w.st = 'in'; continue; }
        const w = WM.get(id);
        if (!w || w.st !== st) wmSet(id, o, mechFrame(f), p, Number(yaw) || 0, st, st === 'fall' ? Math.max(0, left) : left).ms = 2500;
        else if (st !== 'fall') w.until = now + (Number(left) || 0); // (a fall keeps the clock its 'call' started)
      }
      for (const w of [...WM.values()]) if (!seen.has(w.id) && w.st !== 'leave' && now - w.t0 > 2000) wmDrop(w);
      return;
    }
    case 'in': {
      FRAMEOF.set(m.id, mechFrame(m.f));
      const w = WM.get(m.m); if (w) w.st = 'in';
      if (m.id === G.myId) startLocal(m);
      else { const r = G.remotes.get(m.id), p = P(m.p); if (p) mechsfx.climb(p); if (r) hud.chat(null, null, `${r.name || nameOf(m.id).name} climbed into ${MECH[mechFrame(m.f)].name}`); }
      return;
    }
    case 'out': {
      const p = P(m.p);
      if (m.why === 'hop' && p) { const w = wmSet(m.m, m.id, FRAMEOF.get(m.id) || 'paperplane', p, Number(m.yaw) || 0, 'idle', m.ms || MECH.idle * 1000); mechsfx.hatch(p); w.landT = 0; }
      else { const w = WM.get(m.m); if (w) wmDrop(w); }
      if (m.id === G.myId) { endLocal(m.why); if (m.why === 'hop') hud.msg(`HOPPED OUT · ${K.label('use')} TO GET BACK IN (${MECH.idle}s)`, 1.6); }
      FRAMEOF.delete(m.id);
      return;
    }
    case 'gone': { const w = WM.get(m.m); if (w) { if (m.why === 'leave' && w.st !== 'fall' && w.inst) { w.st = 'leave'; w.t0 = now; mechsfx.leave(w.p); } else wmDrop(w); } return; }
    case 'pos': { const p = P(m.p), v = P(m.v); if (p) ME.pos = p.slice(); if (v) { ME.vel = v.slice(); ME.onGround = false; } return; }
    case 'fix': { const p = P(m.p); if (p && MS.on) { ME.pos = p.slice(); ME.vel = [0, 0, 0]; MS.dash = null; } return; }
    case 'en': {
      if (!MS.on) return;
      if (Number.isFinite(m.v)) { MS.E.v = m.v; MS.E.at = now; }
      if (Number.isFinite(m.u)) MS.ult = m.u;
      if (m.cd && typeof m.cd === 'object') for (const k of ['lunge', 'crane', 'swarm', 'jet', 'slam', 'bash', ...(KITS[MS.f] ? KITS[MS.f].cds : [])]) MS.cd[k] = Number.isFinite(m.cd[k]) ? now + m.cd[k] : Math.min(MS.cd[k] || 0, now);
      if (Number.isFinite(m.jet)) MS.jetUntil = m.jet > 0 ? now + m.jet : Math.min(MS.jetUntil, now);
      if (KITS[MS.f] && KITS[MS.f].en) KITS[MS.f].en(m, now); // (a hero's own meters: the vending machine's cans, its jam; the trolley's charge)
      return;
    }
    case 'no': { if (typeof m.why === 'string') { hud.msg(m.why.toUpperCase().slice(0, 40), 1.1); mechsfx.denied(); } if (m.why === 'no energy') { MS.dash = null; MS.triple = null; } if (KITS[MS.f] && MS.on) KITS[MS.f].denied(m.why); return; }
  }
  recordEv(m);
  mechEvent(m, (id) => G.remotes.get(id), true);
});
// replay.js: a recorded mech event, with the replay's ghosts standing in for the players
const FX = new Set(['gun', 'cut', 'lunge', 'crane', 'cp', 'peck', 'cranex', 'swarm', 'jet', 'swing', 'bash', 'triple', 'slam', 'quake', 'blk', 'stomp', 'ram', 'mark', 'clock', 'squash', 'bonk', 'down']);
for (const k of Object.values(KITS)) for (const e of k.events) FX.add(e);
export function mechFx(m, ghosts) { if (m && FX.has(m.k)) mechEvent(m, (id) => ghosts.get(id), false); }
// a new round / mode / you left: no mechs left lying around
export function mechReset() {
  for (const w of [...WM.values()]) wmDrop(w);
  for (const d of DRONES.values()) d.g.removeFromParent();
  DRONES.clear(); FRAMEOF.clear();
  for (const mk of MARKS.values()) mk.el.remove();
  MARKS.clear();
  for (const k of Object.values(KITS)) k.reset();
  endLocal('quiet');
}
// the loadout's frame pick (main.js buildLoadoutUI): two buttons under the killstreaks
export function mechFrameRow(cur, onPick) {
  const row = document.createElement('div');
  row.className = 'mechFrames';
  row.style.cssText = 'display:flex;gap:6px;align-items:center;width:100%;margin-top:4px;font-weight:bold';
  const t = document.createElement('span'); t.textContent = 'MECH DROP FRAME:'; row.append(t);
  for (const [f, tip] of [['paperplane', 'nimble 5 m flyer · 900 armour'], ['nightshift', '6 m knight · 1500 armour'], ...Object.keys(KITS).map((k) => [k, MECH[k].tip])]) {
    const b = document.createElement('button');
    b.className = 'kpick' + (mechFrame(cur) === f ? ' on' : '');
    b.textContent = MECH[f].name; b.title = tip;
    b.addEventListener('click', () => onPick(f));
    row.append(b);
  }
  return row;
}
// (tests + screenshots: the mechs out in the world)
export const mechKitApi = { aimDir, dustRing: (p, r, k) => dustRing(p, r, k), shakeNear: (a, k, r) => shakeNear(a, k, r), centerOf: (r) => centerOf(r), nameOf: (id) => nameOf(id), instOf: (id, getR) => instOf(id, getR), posOf: (id, getR) => posOf(id, getR) }; // (the heroes' kits: helpers they share)
export const mechWorld = () => [...WM.values()].map((m) => ({ id: m.id, o: m.o, f: m.f, p: m.p, st: m.st, yaw: m.yaw }));
export const mechDebug = () => ({ WM, MS, DRONES }); // (screenshot scripts: hold a fall mid-air)
