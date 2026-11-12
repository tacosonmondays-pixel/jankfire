// MECH DROP killstreak: the numbers both sides use (the design note is docs/mechs/PLAY.md). You call a mech in, it
// falls out of the sky onto a marker, you climb in and it's your body until its armour breaks. Movement is the
// client's (public/js/mech.js); the server judges the drop, every hit, energy, cooldowns and speed caps (server/mech.js).
// Every number here is a default: tune it in this one table.
import { FLAGS, WEAPONS } from './weapons.js';
import { BODY } from './bodyhp.js';

export const MECH = {
  kills: 9, // (STREAKS.mechdrop in shared/weapons.js mirrors this)
  // calling it in: how far the marker can go, how long it falls, the landing shockwave (damage at the middle -> 35% at
  // the edge, radius, knockback out / up), standing right on the marker = squashed, the headroom it needs
  drop: { hit: 0.36, range: 60, // (hit: drop_in's impact frame, played at touchdown)
    delay: 2.5, dmg: 60, r: 6, kb: 14, up: 13, squash: 1.9, sky: 7 },
  wait: 30, // s it stands waiting for you after landing (then it flies off)
  idle: 10, // s an empty mech waits after you hop out early
  reach: 4.5, // how close you have to be to climb in (F)
  // energy: the meter, refill per s, how long after the last use it starts refilling
  energy: { max: 100, regen: 30, delay: 0.8 },
  head: 1.5, // a hit on the cockpit (the mech's "head" box)
  kbTake: 0.15, // how much knockback still gets through to a mech
  // eject at 0 armour: the blast (damage, radius, credited to whoever broke it), the fling out of the cockpit (back, up)
  boom: { dmg: 40, r: 5, back: 9, up: 17 },
  // stomp: come down on someone hard enough (falling faster than vy) and they're flat
  stomp: { dmg: 50, vy: -9, flat: 1.4 },
  // ram: walking / flying into people at speed. from `min` m/s; damage per m/s over that (capped), knockback per m/s
  ram: { min: 7, dmg: 1.6, cap: 35, kb: 1.1, up: 6, cd: 0.7 },
  // speed caps the server holds you to (m/s, flat), with lag slack in metres, and the most you may rise per s
  slack: 3, rise: 32,
  paperplane: {
    name: 'PAPER PLANE', hp: 900, h: 4.9, hw: 0.8, c0: 3.1, c1: 4.15, eye: 4.4, cam: 8.5, // (box sizes: docs/mechs/MECHS.md; the cockpit is the chest band)
    speed: 14, accel: 9, fric: 5, grav: 30, hop: 12, airCap: 16,
    gun: { dmg: 14, rate: 8, range: 120, cone: 0.6 }, // twin cannons: per shot, shots a second, metres, how far off your view (cos) a shot may go
    hover: { up: 7, rise: 0.9, drain: 22, speed: 16 }, // climb speed, s of climbing before it just hangs, energy a s, flat speed
    lunge: { cost: 25, speed: 40, dist: 16, lock: 22, cos: 0.9, dmg: 30, kb: 22, kbUp: 8, heal: 0.5, r: 2.2 }, // boost lunge: locks the enemy nearest the crosshair
    crane: { cd: 9, range: 45, cos: 0.85, speed: 30, pecks: 4, dmg: 6, gap: 0.3, life: 6 }, // the origami crane drone
    swarm: { cd: 10, n: 12, kicks: [0.30, 0.52, 0.74], dmg: 9, r: 2.6, kb: 7, gap: 45, // (kicks: s into missile_salvo when the pods fire, 2 pencils a side each)
      spin: 7, wob: 0.35, cos: 0.55, seek: 70, speed: [18, 40], turn: 4.6, boost: 0.3, life: 4.5 }, // missile swarm (rig missile code + a spiral)
    jet: { dur: 6, cd: 20, speed: 45, dmg: 60, kb: 30, kbUp: 14, r: 2.6 }, // fold into a jet: fly where you look, ram
  },
  nightshift: {
    name: 'NIGHT SHIFT', hp: 1500, h: 5.7, hw: 1.2, c0: 3.3, c1: 4.6, eye: 5.3, cam: 10,
    speed: 11, accel: 7, fric: 4.5, grav: 32, hop: 14, airCap: 6,
    sword: { dmg: [40, 40, 70], hit: [0.24, 0.22, 0.42], cd: [0.38, 0.38, 0.62], // hit: s into sword_combo_N when the blade lands (the server judges it then)
      combo: 0.95, reach: 6.2, cos: 0.2, kb: [8, 8, 28], up: [4, 4, 12] }, // three swings
    shield: { bashHit: 0.22, cut: 0.85, cos: 0.35, slow: 0.45, bashWin: 0.8, bash: 30, bashR: 5, bashKb: 22, bashCd: 1.2 }, // tower shield + bash
    triple: { cost: 35, n: 3, hits: [0.20, 0.44, 0.68], lead: 0.08, gap: 0.24, speed: 28, len: 0.18, dmg: 25, r: 2.6, kb: 10 }, // TRIPLE SHIFT: three dashing cuts (dash i from lead + i x gap for len s; the triple_shift clip's cuts land at hits)
    slam: { hit: 0.56, cd: 18, up: 20, // (hit: ground_slam's impact frame. ours is the real landing: the height is physics)
      down: 42, dmg: 120, r: 8, kb: 14, kbUp: 16, win: 4 }, // ground slam
    overtime: { marks: 4, fade: 4, stun: 1, immune: 3 }, // sword hits stamp marks; the 4th CLOCKS THEM OUT (stun s, then immune s)
  },
};
export const FRAMES = ['paperplane', 'nightshift'];
export const mechFrame = (f) => (f === 'nightshift' ? 'nightshift' : 'paperplane'); // anything else is the default
export const isFrame = (f) => typeof f === 'string' && FRAMES.includes(f);

// snapshot flags. bits 22, 23, 30 and 31 were the last free ones, so a frame's moves share them (the frame comes from
// the server's 'mech' events): MECH = in one; A = hover / shield; B = jet / slam; C = lunge / triple shift
Object.assign(FLAGS, { MECH: 1 << 22, MECH_A: 1 << 23, MECH_B: 1 << 30, MECH_C: 1 << 31 });
// (the per-frame names live here, not in FLAGS: room.js checks that every FLAGS entry is its own bit)
export const MF = { HOVER: FLAGS.MECH_A, SHIELD: FLAGS.MECH_A, JET: FLAGS.MECH_B, SLAM: FLAGS.MECH_B, DASH: FLAGS.MECH_C, SLASH: FLAGS.MECH_C };
export const MECH_BITS = FLAGS.MECH | FLAGS.MECH_A | FLAGS.MECH_B | FLAGS.MECH_C;

// its armour is a body pool like the ball's and the rig's (server/bodyhp.js): no drain, it lasts until it breaks
for (const f of FRAMES) BODY[f] = { hp: MECH[f].hp, decay: 0, name: MECH[f].name };

// not guns: what the mech's hits are called in the kill feed
Object.assign(WEAPONS, {
  mechdrop: { slot: null, kind: 'mech', name: 'Mech Drop', color: '#ff3030' },
  mechgun: { slot: null, kind: 'mech', name: 'Twin Cannons', color: '#4fd8ff' },
  mechlunge: { slot: null, kind: 'mech', name: 'Boost Lunge', color: '#ff4fd8' },
  mechcrane: { slot: null, kind: 'mech', name: 'Crane Drone', color: '#fff3c4' },
  mechmissile: { slot: 'hidden', kind: 'proj', name: 'Missile Swarm', color: '#ff6a3d', grav: 0, r: 0.2, life: 5 },
  mechjet: { slot: null, kind: 'mech', name: 'Jet Ram', color: '#4fd8ff' },
  mechsword: { slot: null, kind: 'mech', name: 'Night Shift Sword', color: '#b07dff' },
  mechbash: { slot: null, kind: 'mech', name: 'Shield Bash', color: '#ffe14d' },
  mechtriple: { slot: null, kind: 'mech', name: 'Triple Shift', color: '#b07dff' },
  mechslam: { slot: null, kind: 'mech', name: 'Ground Slam', color: '#ffb000' },
  mechstomp: { slot: null, kind: 'mech', name: 'Stomp', color: '#ffe14d' },
  mechram: { slot: null, kind: 'mech', name: 'Mech Ram', color: '#ff7a1a' },
  mechboom: { slot: null, kind: 'mech', name: 'Mech Down', color: '#ff3030' },
});

// the body killstreaks fight over your body: no mech drop in the rig or the ball (or with a mech already out), and
// none of them inside a mech. a clash leaves the streak in your tray
const BODY_STREAKS = new Set(['moonboots', 'spinbot', 'wreckingball', 'overdrive', 'mechdrop']);
export const mechClash = (id, inMech, inRig, inBall, hasMech) => (inMech && BODY_STREAKS.has(id)) || (id === 'mechdrop' && (inRig || inBall || hasMech));

// what you shoot at: the frame as one tall box (MECHS.md's sizes), split at the cockpit: the chest band where the hatch
// is (the "head": 1.5x) between the legs and the shoulders / helmet. k = the far-away draw scale
export function mechBoxes(pos, frame, k = 1) {
  const F = MECH[mechFrame(frame)], [x, y, z] = pos, w = F.hw * k, a = F.c0 * k, b = F.c1 * k, t = F.h * k;
  return [
    { min: [x - w, y, z - w], max: [x + w, y + a, z + w], head: false },
    { min: [x - w, y + a, z - w], max: [x + w, y + b, z + w], head: true },
    { min: [x - w, y + b, z - w], max: [x + w, y + t, z + w], head: false },
  ];
}
export const mechEye = (frame) => MECH[mechFrame(frame)].eye;

// energy ({ v, t: last spent, at: last counted }): refills at regen/s once `delay` s have passed since it was spent.
// both sides run it with their own clock
export function energyAt(E, n) {
  const N = MECH.energy;
  const from = Math.max(E.at || n, (E.t || 0) + N.delay * 1000);
  if (n > from) E.v = Math.min(N.max, E.v + (n - from) / 1000 * N.regen);
  E.at = n;
  return E.v;
}
export function spend(E, amt, n) {
  if (energyAt(E, n) < amt) return false;
  E.v -= amt; E.t = n;
  return true;
}
export const newEnergy = (n = 0) => ({ v: MECH.energy.max, t: 0, at: n });

// the flat speed the server allows right now (m/s) for what the flags say you're doing
export function speedCap(frame, f) {
  const F = MECH[mechFrame(frame)];
  if (frame === 'paperplane') {
    if (f & MF.JET) return F.jet.speed;
    if (f & MF.DASH) return F.lunge.speed;
    if (f & MF.HOVER) return Math.max(F.speed, F.hover.speed);
    return Math.max(F.speed, F.airCap);
  }
  if (f & MF.SLASH) return F.triple.speed;
  if (f & MF.SLAM) return F.speed + 6;
  if (f & MF.SHIELD) return F.speed * F.shield.slow; // (behind the shield you trudge)
  return F.speed;
}
// sword: is the spot `at` inside the swing's arc in front of a knight at `pos` facing `yaw`? (flat, plus a height band)
export function inArc(pos, yaw, at, reach, cos, h = 6) {
  const dx = at[0] - pos[0], dz = at[2] - pos[2], l = Math.hypot(dx, dz), dy = at[1] - pos[1];
  if (l > reach || dy < -1.5 || dy > h + 0.5) return false;
  if (l < 1.2) return true; // under its feet
  return (-Math.sin(yaw) * dx - Math.cos(yaw) * dz) / l >= cos;
}
// ram: damage + knockback for running into someone at hs m/s (null below the threshold)
export function ramHit(hs) {
  const R = MECH.ram;
  if (!(hs >= R.min)) return null;
  return { dmg: Math.min(R.cap, (hs - R.min + 4) * R.dmg), kb: hs * R.kb, up: R.up };
}
// the drop's shockwave at distance d from the middle (null outside)
export function dropHit(d) {
  const D = MECH.drop;
  if (!(d <= D.r)) return null;
  const f = 1 - d / D.r;
  return { dmg: D.dmg * (0.35 + 0.65 * f), kb: D.kb * (0.4 + 0.6 * f), up: D.up * (0.5 + 0.5 * f) };
}
// overtime marks ({ n, until }): one more from a sword hit at n; returns true when it's the one that clocks them out
export function addMark(o, n) {
  const T = MECH.nightshift.overtime;
  if (n < (o.immune || 0)) return false;
  if (!(o.until > n)) o.n = 0;
  o.n++; o.until = n + T.fade * 1000;
  if (o.n < T.marks) return false;
  o.n = 0; o.until = 0; o.immune = n + (T.stun + T.immune) * 1000;
  return true;
}
