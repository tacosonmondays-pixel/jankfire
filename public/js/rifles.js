// The rifle pack, client half: the Hat Trick's bursts, the Belt Sander's heat + belt, the Yeehaw's lever and spin-cock,
// the mags, charging handles and feed cover moving in the reload / draw / inspect animations, and the callouts the
// server sends back (BURST!, the lever's damage ramp, quick-scopes). Damage is all the server's (server/rifles.js).
import * as THREE from 'three';
import { WEAPONS } from '/shared/weapons.js';
import { ANIMS, sampleCh } from './anim.js';
import { sfx } from './audio.js';
import { hud } from './hud.js';
import { net } from './net.js';
import { G } from './ctx.js';

export const RIFLES = new Set(['burst', 'lmg', 'dmr', 'lever', 'autoshot']);
export const RF = { heat: 0, lastShot: 0, bLeft: 0, ramp: 0, rampT: 0 };

// viewmodel placement, recoil springs, and where the fist goes (bullpup grip is forward, the lever hand sits in the loop)
export const RIFLE_VM = {
  burst: { p: [0.2, -0.205, -0.37], r: [0, 0.04, 0], s: 0.72, hand: [0.004, -0.05, -0.05] },
  lmg: { p: [0.215, -0.235, -0.4], r: [0, 0.035, 0], s: 0.64, hand: [0.004, -0.05, 0.055] },
  dmr: { p: [0.2, -0.2, -0.38], r: [0, 0.035, 0], s: 0.6, hand: [0.004, -0.045, 0.06] },
  lever: { p: [0.19, -0.19, -0.36], r: [0, 0.045, 0], s: 0.72, hand: [0.004, -0.06, 0.055] },
  autoshot: { p: [0.2, -0.2, -0.37], r: [0, 0.04, 0], s: 0.7, hand: [0.004, -0.05, 0.075] },
};
export const RIFLE_RECOIL = {
  burst: { back: 0.7, up: 2.2, roll: 1.1, side: 0.12, punch: 0.01 },
  lmg: { back: 0.55, up: 1.6, roll: 1.3, side: 0.3, punch: 0.008 },
  dmr: { back: 2.2, up: 8, roll: 1.8, side: 0.2, punch: 0.05 },
  lever: { back: 1.8, up: 9, roll: 1.6, side: 0.2, punch: 0.045 },
  autoshot: { back: 1.9, up: 6.5, roll: 2.4, side: 0.35, punch: 0.04 },
};
export const RIFLE_SHELLS = new Set(['burst', 'lmg', 'dmr', 'autoshot']); // the lever throws its own at the top of the stroke

// ------------------------------------------------------------ animations
// K like anim.js. extra channels (sampleCh): mag [dy, dz, rx] off its seat, charge [dz], lever [rx], lhammer [rx],
// cover [rx], twirl [rx] (the whole gun round the lever loop), belt [0..1 shown]
const K = (t, p = [0, 0, 0], r = [0, 0, 0], e = 'smooth', s = 1) => ({ t, p, r, e, s });
const PI2 = Math.PI * 2;
const magSwap = (t0, drop = 0.34, rock = 0) => [ // out, gone, a fresh one comes up, seated with a slap
  [0, 0, 0, 0], [t0, 0, 0, 0], [t0 + 0.12, -0.05, 0.01, rock * 0.5], [t0 + 0.3, -drop, 0.06, rock], [t0 + 0.62, -drop, 0, rock],
  [t0 + 0.92, -0.045, 0, rock * 0.5], [t0 + 1.0, 0.006, 0, 0], [t0 + 1.06, 0, 0, 0]];
const rack = (t0) => [[0, 0], [t0, 0], [t0 + 0.08, 0.075], [t0 + 0.13, 0.075], [t0 + 0.18, 0]];
Object.assign(ANIMS, {
  // ---- reloads (as long as the gun's reload time)
  reload_burst: { keys: [ // tip it up and roll it so you see the mag behind the grip, swap, slap, yank the handle
    K(0), K(0.24, [-0.03, 0.03, 0.05], [0.32, -0.25, 0.55]), K(0.9, [-0.035, 0.025, 0.05], [0.3, -0.25, 0.6]),
    K(1.32, [-0.03, 0.045, 0.04], [0.36, -0.22, 0.5], 'snap'), K(1.42, [-0.03, 0.03, 0.05], [0.3, -0.25, 0.55]),
    K(1.62, [0.01, 0.02, 0.03], [0.1, 0.15, -0.35]), K(1.78, [0.01, 0.02, 0.045], [0.1, 0.15, -0.35], 'snap'), K(2.0),
  ], ch: { mag: magSwap(0.3, 0.36), charge: rack(1.62) }, events: [[0.36, 'magOut'], [1.32, 'magIn'], [1.68, 'chargeBack'], [1.8, 'chargeHome']] },
  reload_lmg: { keys: [ // flip the cover, rip the box off, a fresh one + lay the belt, slam the cover, charge it
    K(0), K(0.35, [-0.05, 0.05, 0.04], [0.38, 0.3, 0.42]), K(0.7, [-0.055, 0.055, 0.04], [0.4, 0.32, 0.44]),
    K(1.1, [-0.04, 0.02, 0.03], [0.15, 0.25, 0.7]), K(2.4, [-0.04, 0.02, 0.03], [0.16, 0.25, 0.72]),
    K(2.7, [-0.05, 0.055, 0.04], [0.4, 0.32, 0.44]), K(3.3, [-0.05, 0.055, 0.04], [0.42, 0.3, 0.44]),
    K(3.42, [-0.05, 0.03, 0.04], [0.32, 0.3, 0.44], 'snap'), K(3.7, [0.01, 0.0, 0.05], [0.08, 0.1, -0.3]),
    K(3.85, [0.01, 0.0, 0.08], [0.08, 0.1, -0.32], 'snap'), K(4.2),
  ], ch: { cover: [[0, 0], [0.45, 0], [0.62, 1.25], [3.28, 1.25], [3.42, 0]], mag: magSwap(1.05, 0.42, -0.2), belt: [[0, 1], [0.8, 1], [0.95, 0], [2.6, 0], [2.95, 1]] },
  events: [[0.55, 'coverUp'], [1.12, 'magOut'], [2.08, 'magIn'], [2.7, 'belt'], [3.4, 'coverSlam'], [3.8, 'chargeBack']] },
  reload_dmr: { keys: [
    K(0), K(0.25, [-0.03, 0.03, 0.04], [0.28, -0.2, 0.5]), K(1.0, [-0.035, 0.03, 0.04], [0.28, -0.22, 0.52]),
    K(1.35, [-0.03, 0.05, 0.035], [0.34, -0.2, 0.46], 'snap'), K(1.45, [-0.03, 0.03, 0.04], [0.28, -0.2, 0.5]),
    K(1.68, [0.01, 0.015, 0.03], [0.08, 0.2, -0.4]), K(1.86, [0.01, 0.015, 0.05], [0.08, 0.2, -0.42], 'snap'), K(2.1),
  ], ch: { mag: magSwap(0.32, 0.32, 0.5), charge: rack(1.7) }, events: [[0.4, 'magOut'], [1.35, 'magIn'], [1.76, 'chargeBack'], [1.88, 'chargeHome']] },
  // Yeehaw: roll it over, thumb rounds in through the loading gate, then a spin-cock round the lever loop
  reload_lever: { keys: [
    K(0), K(0.25, [-0.04, 0.03, 0.03], [0.22, -0.3, 0.9]),
    ...[0, 1, 2, 3, 4].flatMap((i) => [K(0.42 + i * 0.27, [-0.04, 0.03, 0.04], [0.24, -0.3, 0.92], 'snap'), K(0.55 + i * 0.27, [-0.04, 0.03, 0.03], [0.22, -0.3, 0.9])]),
    K(1.85, [0, 0.03, 0.01], [0.05, 0, 0]), K(2.35, [0, 0.05, 0.0], [0.05, 0, 0], 'linear'), K(2.6),
  ], ch: { twirl: [[0, 0], [1.9, 0], [2.42, -PI2]], lever: [[0, 0], [1.9, 0], [2.02, 0.95], [2.3, 0.95], [2.44, 0]], lhammer: [[0, 0.75], [2.1, 0.75], [2.22, 0.95], [2.4, 0.75]] },
  events: [[0.42, 'shellIn'], [0.69, 'shellIn'], [0.96, 'shellIn'], [1.23, 'shellIn'], [1.5, 'shellIn'], [1.92, 'whoosh'], [2.43, 'leverClack']] },
  reload_autoshot: { keys: [
    K(0), K(0.25, [-0.03, 0.025, 0.05], [0.3, -0.2, 0.55]), K(1.05, [-0.035, 0.025, 0.05], [0.3, -0.22, 0.58]),
    K(1.42, [-0.03, 0.05, 0.04], [0.36, -0.2, 0.5], 'snap'), K(1.52, [-0.03, 0.03, 0.05], [0.3, -0.2, 0.55]),
    K(1.85, [0.01, 0.015, 0.03], [0.1, 0.2, -0.45]), K(2.03, [0.015, 0.015, 0.06], [0.1, 0.2, -0.47], 'snap'), K(2.4),
  ], ch: { mag: magSwap(0.38, 0.38, 0.55), charge: rack(1.88) }, events: [[0.45, 'magOut'], [1.42, 'magIn'], [1.94, 'chargeBack'], [2.06, 'chargeHome']] },

  // ---- after every Yeehaw shot: throw the lever (spent case flies out the top), cock the hammer, back on target
  lever_cycle: { keys: [K(0), K(0.1, [0, -0.025, 0.035], [0.14, 0, -0.14]), K(0.2, [0, -0.012, 0.015], [0.07, 0, -0.06], 'snap'), K(0.34)],
    ch: { lever: [[0, 0], [0.1, 0.95], [0.19, 0]], lhammer: [[0, 0], [0.08, 0.95], [0.17, 0.75]] }, events: [[0.1, 'shellUp'], [0.19, 'leverClack']] },

  // ---- draws
  draw_burst: { keys: [K(0, [0.03, -0.26, 0.06], [-0.9, 0.35, 0.45]), K(0.2, [0, 0.012, 0], [0.09, -0.03, -0.06], 'snap'), K(0.3, [0.005, 0.005, 0.01], [0.04, 0.05, -0.15]), K(0.45)],
    ch: { charge: rack(0.24) }, events: [[0.19, 'click'], [0.3, 'chargeBack'], [0.42, 'chargeHome']] },
  draw_dmr: { keys: [K(0, [0.03, -0.28, 0.06], [-0.85, 0.3, 0.45]), K(0.24, [0, 0.012, 0], [0.09, -0.03, -0.06], 'snap'), K(0.34, [0.008, 0.005, 0.02], [0.05, 0.12, -0.3]), K(0.5)],
    ch: { charge: rack(0.28) }, events: [[0.22, 'click'], [0.34, 'chargeBack'], [0.46, 'chargeHome']] },
  draw_autoshot: { keys: [K(0, [0.05, -0.32, 0.1], [-0.75, 0.3, 0.6]), K(0.26, [0, 0.015, 0], [0.1, 0, -0.05], 'snap'), K(0.36, [0.008, 0.005, 0.02], [0.05, 0.12, -0.32]), K(0.52)],
    ch: { charge: rack(0.3) }, events: [[0.25, 'clunk'], [0.36, 'chargeBack'], [0.48, 'chargeHome']] },
  draw_lmg: { keys: [K(0, [0.07, -0.42, 0.14], [-0.7, 0.25, 0.7]), K(0.34, [0, 0.025, 0], [0.12, 0, -0.06], 'snap'), K(0.44, [0, -0.008, 0], [-0.04, 0, 0.02]), K(0.6)],
    events: [[0.32, 'clunk'], [0.36, 'belt']] },
  draw_lever: { keys: [K(0, [0.02, -0.24, 0.04], [-0.8, 0.3, 0.3]), K(0.16, [0, 0.03, 0], [0.06, 0, 0], 'snap'), K(0.52, [0, 0.04, 0], [0.04, 0, 0], 'linear'), K(0.66)], // one-handed spin-cock
    ch: { twirl: [[0, 0], [0.14, 0], [0.5, -PI2]], lever: [[0, 0], [0.14, 0], [0.22, 0.95], [0.42, 0.95], [0.52, 0]] }, events: [[0.16, 'whoosh'], [0.51, 'leverClack']] },

  // ---- inspects
  inspect_burst: { keys: [ // look down the side, flip it to check the carry handle, smack the mag
    K(0), K(0.4, [-0.07, 0.05, 0.04], [0.15, 0.95, 0.5]), K(1.0, [-0.08, 0.055, 0.04], [0.18, 1.0, 0.55]),
    K(1.4, [-0.05, 0.07, 0.03], [0.55, -0.4, -0.7]), K(1.85, [-0.05, 0.075, 0.03], [0.58, -0.42, -0.72]),
    K(2.0, [-0.05, 0.09, 0.03], [0.62, -0.42, -0.7], 'snap'), K(2.12, [-0.05, 0.075, 0.03], [0.58, -0.42, -0.72]), K(2.5),
  ], ch: { mag: [[0, 0, 0, 0], [1.98, 0, 0, 0], [2.0, 0.012, 0, 0], [2.1, 0, 0, 0]] }, events: [[2.0, 'magIn']] },
  inspect_lmg: { keys: [ // pop the cover, look at the belt, pat it, slam it
    K(0), K(0.45, [-0.06, 0.06, 0.04], [0.42, 0.35, 0.4]), K(1.6, [-0.065, 0.065, 0.04], [0.45, 0.38, 0.42]),
    K(1.75, [-0.065, 0.05, 0.04], [0.38, 0.38, 0.42], 'snap'), K(2.0, [-0.04, 0.03, 0.02], [-0.05, -0.3, -0.25]), K(2.6),
  ], ch: { cover: [[0, 0], [0.5, 0], [0.68, 1.2], [1.6, 1.2], [1.74, 0]] }, events: [[0.6, 'coverUp'], [1.1, 'belt'], [1.74, 'coverSlam']] },
  inspect_dmr: { keys: [ // turn the scope to your face, breathe on the lens, wipe, back
    K(0), K(0.45, [-0.1, 0.06, 0.1], [0.12, 1.25, 0.25]), K(1.1, [-0.12, 0.06, 0.13], [0.12, 1.3, 0.25]),
    K(1.4, [-0.11, 0.065, 0.12], [0.1, 1.2, 0.35]), K(1.6, [-0.11, 0.065, 0.12], [0.1, 1.3, 0.15]), K(2.3),
  ], events: [[0.9, 'blow']] },
  inspect_lever: { keys: [ // two spin-cocks and a lever flick, yeehaw
    K(0), K(0.2, [0, 0.03, 0], [0.06, 0, 0]), K(1.3, [0, 0.05, 0], [0.06, 0, 0], 'linear'),
    K(1.55, [-0.05, 0.05, 0.03], [0.2, 0.6, 0.3], 'back'), K(1.95, [-0.05, 0.05, 0.03], [0.22, 0.62, 0.3]), K(2.4),
  ], ch: { twirl: [[0, 0], [0.2, 0], [0.7, -PI2], [1.25, -PI2 * 2]], lever: [[0, 0], [0.22, 0.95], [1.2, 0.95], [1.3, 0], [1.7, 0], [1.78, 0.95], [1.88, 0]] },
  events: [[0.22, 'whoosh'], [0.72, 'whoosh'], [1.29, 'leverClack'], [1.6, 'yeehaw'], [1.87, 'leverClack']] },
  inspect_autoshot: { keys: [ // yank the pull cord like a mower (it's not that kind of mower), rack it twice
    K(0), K(0.3, [-0.05, 0.04, 0.03], [0.2, 0.5, 0.35]), K(0.5, [-0.08, 0.08, 0.05], [0.3, 0.7, 0.5], 'snap'),
    K(0.75, [-0.05, 0.04, 0.03], [0.2, 0.5, 0.35]), K(1.1, [0.01, 0.015, 0.03], [0.1, 0.2, -0.45]),
    K(1.8, [0.01, 0.015, 0.03], [0.1, 0.2, -0.45]), K(2.3),
  ], ch: { charge: [...rack(1.15), ...rack(1.5).slice(2)] }, events: [[0.5, 'mower'], [1.22, 'chargeBack'], [1.33, 'chargeHome'], [1.57, 'chargeBack'], [1.68, 'chargeHome']] },
});
for (const k of Object.keys(ANIMS)) if (!ANIMS[k].dur) ANIMS[k].dur = ANIMS[k].keys[ANIMS[k].keys.length - 1].t;

// ------------------------------------------------------------ firing
// a shot just went off (weapons.js fireHitscan). returns the follow-up animation to queue, if any
export function rifleShot(id, w, W, now) {
  RF.lastShot = now;
  if (w.heatUp) RF.heat = Math.min(1, RF.heat + w.heatUp / w.rate);
  if (w.burst && w.kind === 'hitscan') {
    if (RF.bLeft <= 0) RF.bLeft = w.burst;
    RF.bLeft--;
    if (RF.bLeft <= 0) W.cd[id] += w.burstGap * 1000; // the burst is done: a breath before the next one
  }
  if (id === 'lever') W.cycle = { name: 'lever_cycle', t: 0.04 };
}
export const bursting = (w) => !!w.burst && w.kind === 'hitscan' && RF.bLeft > 0; // a tap fires the whole burst
export function rifleReset() { RF.bLeft = 0; }
export const quickScoped = (w, W, now) => !!w.quick && W.scoped && now - W.scopedAt <= w.quick * 1000;

// someone else's gun: how hot their Belt Sander is from the shots we've heard (for the sound)
const remHeat = new Map();
export function remoteK(pid, wid) {
  const w = WEAPONS[wid];
  if (!w || !w.heatUp) return 0;
  const n = performance.now(), h = remHeat.get(pid) || { h: 0, t: n };
  const gap = (n - h.t) / 1000;
  h.h = Math.min(1, Math.max(0, h.h - Math.max(0, gap - 0.25) * w.heatDown) + w.heatUp / w.rate); h.t = n;
  remHeat.set(pid, h);
  return h.h;
}

// ------------------------------------------------------------ per frame: heat, belt, moving parts
const cDark = new THREE.Color(0x2a2a2c), cRed = new THREE.Color(0x9a1a06), cOr = new THREE.Color(0xff6a10), cHot = new THREE.Color(0xfff0b0);
function heatColor(c, k) {
  if (k < 0.45) c.copy(cDark).lerp(cRed, k / 0.45);
  else if (k < 0.8) c.copy(cRed).lerp(cOr, (k - 0.45) / 0.35);
  else c.copy(cOr).lerp(cHot, (k - 0.8) / 0.2);
}
const restOf = (o) => o.userData.rest || (o.userData.rest = { p: o.position.clone(), r: o.rotation.clone() });
function moveCh(o, an, ch, at, fn) {
  if (!o) return;
  const v = an ? sampleCh(an, ch, at) : null, r = restOf(o);
  o.position.copy(r.p); o.rotation.copy(r.r);
  if (v) fn(o, v, r);
}
const piv = new THREE.Vector3();
const HAM_COCKED = 0.75;
const pv = new THREE.Vector3();
function heatPuff(g, k) {
  const sys = G.skinFxVM, mz = g.userData.muzzle;
  if (!sys || !mz || !g.visible) return;
  g.updateMatrixWorld(true);
  pv.set((Math.random() - 0.5) * 0.02, mz.y + 0.02, mz.z * (0.35 + Math.random() * 0.55)); g.localToWorld(pv);
  const R = (x) => (Math.random() - 0.5) * x;
  sys.norm.spawn(pv.x, pv.y, pv.z, R(0.06), 0.12 + Math.random() * 0.12, R(0.06), 0.9, 0.012, 0.06 + k * 0.05, 0xd8d8d8, 0x8a8a8a, 0.35 + k * 0.2, -0.08, 0.8);
}
export function rifleStep(id, m, dt, now, W) {
  const w = WEAPONS[id], ud = m.g.userData;
  const an = W.anim && W.anim.name, at = W.anim ? W.anim.t : 0;
  // Belt Sander heat: up while it fires (rifleShot), back down once you let go for a moment
  if (now - RF.lastShot > 250) RF.heat = Math.max(0, RF.heat - (WEAPONS.lmg.heatDown) * dt);
  if (ud.heat) {
    const flick = id === 'lmg' && now - RF.lastShot < 120 ? Math.random() * 0.05 : 0;
    heatColor(ud.heat.color, id === 'lmg' ? Math.min(1, RF.heat + flick) : 0);
    if (id === 'lmg' && RF.heat > 0.55 && Math.random() < dt * 14 * RF.heat) heatPuff(m.g, RF.heat); // smoke off the hot barrel
  }
  if (ud.belt) { // links from the feed tray down into the box: they go from the box end as it empties
    const b = an ? sampleCh(an, 'belt', at) : null, ammo = W.ammo[id] ?? w.mag;
    const show = b ? (b[0] > 0.5 ? ud.belt.length : 0) : W.reloadId === id ? 0 : Math.min(ud.belt.length, ammo);
    ud.belt.forEach((l, i) => { l.visible = i < show; });
  }
  moveCh(ud.mag, an, 'mag', at, (o, v) => { o.position.y += v[0]; o.position.z += v[1]; o.rotation.x += v[2]; o.visible = v[0] > -0.33; });
  if (ud.mag && !(an && sampleCh(an, 'mag', at))) ud.mag.visible = true;
  moveCh(ud.charge, an, 'charge', at, (o, v) => { o.position.z += v[0]; });
  moveCh(ud.lever, an, 'lever', at, (o, v) => { o.rotation.x += v[0]; }); // + = thrown down and forward
  if (ud.hammer) { // the model rests with the hammer down (+ cocks it back). between shots it sits cocked; lhammer keys are absolute
    const v = an ? sampleCh(an, 'lhammer', at) : null;
    ud.hammer.rotation.x = restOf(ud.hammer).r.x + (v ? v[0] : HAM_COCKED);
  }
  moveCh(ud.cover, an, 'cover', at, (o, v) => { o.rotation.x += v[0]; });
  // the spin-cock: the whole gun turns round the lever loop (where your fist is)
  const tw = an ? sampleCh(an, 'twirl', at) : null, a = tw ? tw[0] : 0;
  const c = m.cfg.hand || [0, 0, 0]; piv.set(0, c[1], c[2]);
  m.g.rotation.x = a;
  m.g.position.set(0, piv.y - (piv.y * Math.cos(a) - piv.z * Math.sin(a)), piv.z - (piv.y * Math.sin(a) + piv.z * Math.cos(a)));
}

// animation events the rifles add (weapons.js animEvent hands us anything it doesn't know)
export function rifleEvent(ev, g, eject) {
  switch (ev) {
    case 'magOut': sfx.rifle('magOut'); break;
    case 'magIn': sfx.rifle('magIn'); break;
    case 'chargeBack': sfx.rifle('chargeBack'); break;
    case 'chargeHome': sfx.rifle('chargeHome'); break;
    case 'coverUp': sfx.rifle('coverUp'); break;
    case 'coverSlam': sfx.rifle('coverSlam'); break;
    case 'belt': sfx.rifle('belt'); break;
    case 'shellIn': sfx.rifle('shellIn'); break;
    case 'shellUp': eject(g, 0xd9a53a, false, true); sfx.rifle('leverOpen'); break;
    case 'leverClack': sfx.rifle('leverClack'); break;
    case 'yeehaw': sfx.rifle('yeehaw'); break;
    case 'mower': sfx.rifle('mower'); break;
    default: return false;
  }
  return true;
}

// ------------------------------------------------------------ what the server tells the shooter
net.on('rfx', (m) => {
  if (!m || typeof m.k !== 'string') return;
  if (m.k === 'burst') { hud.msg('BURST!', 0.9, 'burst'); sfx.rifle('burst', m.hs ? 1 : 0); G.shake = Math.max(G.shake || 0, 0.25); }
  else if (m.k === 'lever') {
    const n = Math.max(1, Math.min(3, m.n | 0));
    RF.ramp = n; RF.rampT = performance.now();
    hud.msg(`YEEHAW x${(1 + WEAPONS.lever.ramp * n).toFixed(2)}`, 0.8, 'lever');
    sfx.rifle('ramp', n);
  } else if (m.k === 'qs') { hud.msg('QUICK SCOPE', 0.9, 'qscope'); sfx.rifle('qs'); }
});
