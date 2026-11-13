// MECH DROP killstreak: the numbers both sides use (the design note is docs/mechs/PLAY.md). You call a mech in, it
// falls out of the sky onto a marker, you climb in and it's your body until its armour breaks. Movement is the
// client's (public/js/mech.js); the server judges the drop, every hit, energy, cooldowns and speed caps (server/mech.js).
// Every number here is a default: tune it in this one table.
import { FLAGS, WEAPONS } from './weapons.js';
import { BODY } from './bodyhp.js';
import { raycast, query } from './physics.js';

export const MECH = {
  kills: 9, // (STREAKS.mechdrop in shared/weapons.js mirrors this)
  // calling it in: how far the marker can go, how long it falls, the landing shockwave (damage at the middle -> 35% at
  // the edge, radius, knockback out / up), standing right on the marker = squashed, the headroom it needs
  drop: { hit: 0.36, range: 60, // (hit: drop_in's impact frame, played at touchdown)
    delay: 2.5, dmg: 60, r: 6, kb: 14, up: 13, squash: 1.9, sky: 7, open: 40 }, // (open: m of nothing straight over the marker: it falls from the sky, not through a roof)
  // your own mech (or your side's) on you: BEEP BEEP, a fixed shove off the circle toward clear floor d m away + a hop
  // (never a squash), so you land right next to it to climb in
  bonk: { r: 2.3, d: 3, kb: 6.5, up: 7 },
  wait: 30, // s it stands waiting for you after landing (then it flies off)
  idle: 10, // s an empty mech waits after you hop out early
  reach: 4.5, // how close you have to be to climb in (F)
  out: 2.2, // how far off its side you climb down when you hop out
  // its walking body (collision): the legs' footprint (x the frame's hw), the most it steps up without a hop, the slack
  // a floor adds to the hop's rise budget
  body: { foot: 0.75, step: 1, climb: 1.5, knee: 0.3, thin: 0.6, small: 3.5, slab: 2.5 }, // (knee: x h. above it, mechPlough's clutter (thinner than thin, no longer than small, or a slab no deeper than slab) doesn't stop it)
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
  // ---- battle island heroes (docs/mechs/ROSTER.md). they all have an ULTIMATE on Q that charges from what they deal
  // (ult.dmg dealt = full) plus a slow trickle (ult.time s from empty), and their kits are judged in server/mech_<id>.js
  // WRECKING BALL (dive tank): a 4 m steel ball with a hamster cage inside. (frame id 'wrecking': 'wreckingball' is the
  // killstreak's armour pool)
  wrecking: {
    name: 'WRECKING BALL', hp: 1400, h: 4.0, hw: 1.9, c0: 2.3, c1: 3.1, eye: 3.4, cam: 9.5, tip: '4 m dive tank ball · 1400 armour',
    speed: 22, accel: 1.6, fric: 0.9, grav: 30, hop: 11, airCap: 22, r: 2, // rolls: slow to get going, slow to stop
    ram: { min: 6, mul: 2.6, base: 8, cap: 70, kb: 1.05, up: 7, cd: 0.6 }, // the main weapon: rolling into people (by the speed the server measures)
    rev: { charge: 0.8, min: 0.25, cost: 20, speed: [26, 36], len: 0.55 }, // LMB hold: spin up on the spot; let go: launch (charge s for full)
    chain: { range: 42, cost: 10, cd: 0.7, life: 7, speed: 38, pump: 10, snap: 4 }, // Shift: the chain grapple. speed = the swing's cap, snap = m past its length before it breaks
    slam: { cd: 6, hop: 13, dive: 46, h0: 1.5, h1: 22, dmg: [35, 130], r: [4, 9], kb: [12, 30], up: [8, 19], win: 4 }, // E: dive down; higher = bigger
    pile: { rise: 30, up: 28, hang: 2.5, range: 55, dive: 70, min: 10, dmg: 200, edge: 0.3, r: 9, kb: 30, up2: 20, life: 9, slow: 1 }, // Q: PILE DRIVER (rise m at up m/s, hang s to aim, then dive)
    ult: { dmg: 650, time: 110 }, shrug: 3, // passive: no knockback while rolling faster than shrug m/s
    sized: ['r', 'chain.snap', 'slam.r.0', 'slam.r.1', 'pile.r'], // (lengths that grow with MECH.scale: the ball's radius, its blasts)
  },
  // VENDING MACHINE (support): a 5 m snack machine on stubby legs. the coin slot is its face (the cockpit band)
  vending: {
    name: 'VENDING MACHINE', hp: 1100, h: 5.0, hw: 1.15, c0: 3.5, c1: 4.4, eye: 4.6, cam: 9.5, tip: '5 m support snack machine · 1100 armour',
    speed: 12, accel: 7, fric: 4.5, grav: 32, hop: 10, airCap: 6, // a waddling walker (night shift's kind of step)
    coin: { dmg: 9, rate: 10, range: 90, cone: 0.6 }, // LMB hold: the coin turret (server hitscan from the coin slot)
    cola: { charges: 3, every: 8, gap: 0.35, life: 20, max: 6, hp: 40, armour: 40, boost: 3, reach: 1.8, toss: 6, mine: 0.9 }, // Shift: dispense (toss = how far you can lob it, mine = s before you can drink your own)
    wall: { hp: 600, w: 8, h: 4.5, at: 3.5, life: 10, cd: 12 }, // E: OUT OF ORDER, slammed down `at` m in front, facing you
    restock: { r: 15, armour: 250, hp: 150, hold: 1 }, // Q: RESTOCK (hp: on foot outside the armour modes, overheal up to this)
    stuck: 0.1, jam: { p: 0.06, lock: 4, reach: 4.5 }, // passive STUCK (x2), jank JAMMED (kick it within reach to unstick it)
    ult: { dmg: 800, time: 120 }, // (healing counts like damage)
    sized: ['wall.w', 'wall.h', 'wall.at', 'cola.reach', 'cola.toss', 'restock.r', 'jam.reach'], // (lengths that grow with MECH.scale)
  },
  // TROLLEY (speed): a 4 m shopping trolley mech with a tiny pilot pushing it from the handle. the fastest thing on the
  // island; drifting builds a ram charge, the push spends it, CLEAN UP AISLE 5 scoops people into the basket
  trolley: {
    name: 'TROLLEY', hp: 800, h: 2.6, hw: 1.3, c0: 1.7, c1: 2.6, eye: 2.9, cam: 8.5, tip: '4 m speed trolley · 800 armour',
    speed: 26, accel: 2.6, fric: 1.6, grip: 7, grav: 30, hop: 8, airCap: 26, pull: 0.07, // grip: how fast sideways speed goes (1/s); pull: the wonky wheel's left steer (rad/s at top speed)
    ram: { min: 9, base: 6, mul: 1.4, cap: 35, kb: 0.8, up: 5, cd: 0.7 }, // driving into people (the speed the server measures)
    can: { dmg: 22, r: 0.24, rate: 3, speed: 26, up: 6, cone: 0.55, bounces: 3, minB: 2.5, e: 0.55, kb: 6, kbUp: 3, life: 3.5 }, // LMB: tin-can toss (bounces off things up to `bounces` times, bonks the first enemy)
    drift: { grip: 1.1, min: 12, build: 1.5, keep: 3, caster: 35 }, // Shift: drifting faster than min m/s fills the ram charge in `build` s; it keeps `keep` s
    push: { len: 0.4, v: [30, 40], dmg: [30, 80], kb: [20, 35], up: 6, r: 1.7, cd: 4 }, // E: a lunge forward: speed, damage, knockback by charge (0 -> 1)
    aisle: { dur: 6, speed: 34, max: 3, reach: 2.2, dps: 8, dmg: 35, fling: 24, up: 14, min: 4 }, // Q: CLEAN UP AISLE 5. top speed, scoop up to max (moving faster than min m/s), 8/s in the basket, the dump
    ride: { reach: 3, max: 1, hop: 7 }, // jank: the pound coin lock. an ally within reach m of its sides rides in the child seat
    // where people go (local: x right, y up, +z back toward the handle): the child seat, the basket's three spots
    seat: [-0.2, 1.05, 0.05], scoop: [[0, 1.05, -0.95], [-0.5, 1.05, -0.4], [0.5, 1.05, -0.4]], muzzle: [0.55, 2.55, 1.25],
    ult: { dmg: 550, time: 100 },
    sized: ['push.r', 'aisle.reach', 'ride.reach', 'can.r', 'seat.0', 'seat.1', 'seat.2', 'muzzle.0', 'muzzle.1', 'muzzle.2', // (lengths that grow with MECH.scale)
      ...[0, 1, 2].flatMap((i) => [0, 1, 2].map((k) => `scoop.${i}.${k}`))],
  },
};
export const FRAMES = ['paperplane', 'nightshift', 'wrecking', 'vending', 'trolley'];
export const HERO_FRAMES = FRAMES.filter((f) => MECH[f].ult); // (the ones with an ultimate meter: the island heroes)
export const mechFrame = (f) => (isFrame(f) ? f : 'paperplane'); // anything else is the default
export function isFrame(f) { return typeof f === 'string' && FRAMES.includes(f); }

// snapshot flags. bits 22, 23, 30 and 31 were the last free ones, so a frame's moves share them (the frame comes from
// the server's 'mech' events): MECH = in one; A = hover / shield; B = jet / slam; C = lunge / triple shift
Object.assign(FLAGS, { MECH: 1 << 22, MECH_A: 1 << 23, MECH_B: 1 << 30, MECH_C: 1 << 31 });
// (the per-frame names live here, not in FLAGS: room.js checks that every FLAGS entry is its own bit)
export const MF = { HOVER: FLAGS.MECH_A, SHIELD: FLAGS.MECH_A, JET: FLAGS.MECH_B, SLAM: FLAGS.MECH_B, DASH: FLAGS.MECH_C, SLASH: FLAGS.MECH_C,
  CHAIN: FLAGS.MECH_A, PILE: FLAGS.MECH_B, REV: FLAGS.MECH_C, // (wrecking ball: on the chain, slam / pile driver, rev launch)
  VJAM: FLAGS.MECH_A, VSTOCK: FLAGS.MECH_B, VCOIN: FLAGS.MECH_C, // (vending machine: jammed, restocking, coin turret going)
  DRIFT: FLAGS.MECH_A, AISLE: FLAGS.MECH_B, PUSH: FLAGS.MECH_C }; // (trolley: drifting, CLEAN UP AISLE 5, the push)
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
  wbram: { slot: null, kind: 'mech', name: 'Wrecking Ball', color: '#ffd23a' },
  wbslam: { slot: null, kind: 'mech', name: 'Ball Slam', color: '#ffb000' },
  wbpile: { slot: null, kind: 'mech', name: 'Pile Driver', color: '#ff3030' },
  vmcoin: { slot: null, kind: 'mech', name: 'Coin Turret', color: '#ffd23a' },
  trram: { slot: null, kind: 'mech', name: 'Trolley', color: '#ff3a3a' },
  trpush: { slot: null, kind: 'mech', name: 'Trolley Push', color: '#ffe14d' },
  trscoop: { slot: null, kind: 'mech', name: 'Clean Up Aisle 5', color: '#4fd8ff' },
  trdump: { slot: null, kind: 'mech', name: 'Clean Up Aisle 5', color: '#4fd8ff' },
  trcan: { slot: 'hidden', kind: 'proj', name: 'Tin Can', color: '#c8d2dc', grav: 22, r: 0.24, bounce: 0.55, life: 3.5, kit: 'trolley' }, // (kit: the trolley's server code steps it)
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
  if (frame === 'wrecking') { // A = on the chain, B = slam / pile driver, C = a rev launch
    if (f & MF.CHAIN) return F.chain.speed;
    if (f & MF.PILE) return Math.max(F.pile.dive, F.speed);
    if (f & MF.REV) return F.rev.speed[1];
    return F.speed;
  }
  if (frame === 'vending') return F.speed; // (a cola's sugar rush: server/mech_vending.js raises it while it lasts)
  if (frame === 'trolley') { // B = CLEAN UP AISLE 5, C = the push (drifting is no faster)
    if (f & MF.PUSH) return F.push.v[1];
    if (f & MF.AISLE) return F.aisle.speed;
    return F.speed;
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

// SIZE (the owner, 2026-11-13: "can the mechs be larger"): one number every mech grows by. the tables above are the
// size-1 mechs (PAPER PLANE 4.9 m, NIGHT SHIFT 5.7 m); mechScale(s) multiplies their lengths once (boxes, cockpit band,
// eye, camera, reaches and radii, step, the drop's room checks) from a copy of the size-1 numbers, so calling it again
// is safe. the server's JF_MECH_SCALE test knob sets it (0.5 - 2) and the welcome tells the client. speeds stay. a new
// frame's own attack lengths go in its row as sized: ['lunge.r', ...]
const SIZED = ['drop.r', 'drop.squash', 'drop.sky', 'bonk.r', 'bonk.d', 'reach', 'out', 'boom.r', 'body.step', 'body.climb',
  'paperplane.lunge.r', 'paperplane.jet.r', 'nightshift.sword.reach', 'nightshift.shield.bashR', 'nightshift.triple.r', 'nightshift.slam.r'];
const FRAME_SIZED = ['h', 'hw', 'c0', 'c1', 'eye', 'cam'];
const BASE = new Map(); // path -> its size-1 number
export const SCALE = { def: 1.35, min: 0.5, max: 2 };
export function mechScale(s) {
  s = Number(s);
  if (!Number.isFinite(s)) return MECH.scale;
  s = Math.min(SCALE.max, Math.max(SCALE.min, s));
  const paths = SIZED.concat(...FRAMES.map((f) => FRAME_SIZED.concat(Array.isArray(MECH[f].sized) ? MECH[f].sized : []).map((k) => f + '.' + k)));
  for (const path of paths) {
    const ks = path.split('.'), last = ks.pop();
    let o = MECH;
    for (const k of ks) o = o && Object.hasOwn(o, k) ? o[k] : null;
    if (!o || typeof o[last] !== 'number') continue;
    if (!BASE.has(path)) BASE.set(path, o[last]);
    o[last] = Math.round(BASE.get(path) * s * 1e4) / 1e4;
  }
  MECH.scale = s;
  return s;
}
// the walking body (movePlayer's S): the legs' footprint, its height, its step, and what it ploughs through
export function mechBody(frame) {
  const F = MECH[mechFrame(frame)], knee = F.h * MECH.body.knee;
  return { hw: Math.max(0.4, F.hw * MECH.body.foot), h: F.h, step: MECH.body.step, skip: (b, y) => b.min[1] > y + knee && mechPlough(b) };
}
// clutter a mech walks through once it's over its knees: foliage, and anything thin and small or a thin slab that
// isn't roof-sized (palm fronds, lamp arms, signs, awnings, billboard grids). roofs, floors and walls (lintels
// included: a door's wall goes on into the roof) still stop it
const FOLIAGE = new Set(['leaves', 'leaves2', 'bush', 'thatch', 'grid']);
export function mechPlough(b) {
  const dx = b.max[0] - b.min[0], dy = b.max[1] - b.min[1], dz = b.max[2] - b.min[2], lo = Math.min(dx, dz), hi = Math.max(dx, dz);
  if (FOLIAGE.has(b.mat)) return true;
  if (Math.min(lo, dy) < MECH.body.thin && hi <= MECH.body.small) return true; // (a pole's arm, a lamp, a sign, a frond)
  return dy < MECH.body.thin && lo <= MECH.body.slab; // (an awning, a canopy)
}
// room to land at g (the floor under the marker): open sky straight up (nothing for drop.open m), the legs' footprint (mechBody) clear from a
// step over the floor up to the sky check, and its full width clear from the knees up (a crate by its feet is fine, a
// wall, a roof or an overhang it would land in isn't). on shaped ground a slope under its feet is fine, a hill isn't
export function mechRoom(g, frame, boxes) {
  const F = MECH[mechFrame(frame)], B = mechBody(frame), top = g[1] + Math.max(MECH.drop.sky, F.h + 0.3);
  if (raycast([g[0], g[1] + 0.2, g[2]], [0, 1, 0], Math.max(MECH.drop.open, top - g[1]), boxes)) return false;
  const col = (w, lo) => { // anything solid in the column w either side of the marker, from lo up to the top
    for (const b of query(boxes, g[0] - w, g[2] - w, g[0] + w, g[2] + w, [])) if (!b.ter && !(b.min[1] > g[1] + F.h * MECH.body.knee && mechPlough(b)) && b.max[1] > lo && b.min[1] < top && b.max[0] > g[0] - w && b.min[0] < g[0] + w && b.max[2] > g[2] - w && b.min[2] < g[2] + w) return true; // (shaped ground's steps: the heightfield below says it)
    return false;
  };
  if (col(B.hw, g[1] + B.step) || col(F.hw, g[1] + F.h * 0.3)) return false;
  const T = boxes.terrain, w = B.hw;
  if (T) for (const [dx, dz] of [[-w, -w], [w, -w], [-w, w], [w, w], [0, -w], [0, w], [-w, 0], [w, 0]]) { const y = T.at(g[0] + dx, g[2] + dz); if (y != null && y > g[1] + MECH.body.climb) return false; }
  return true;
}
// ---- WRECKING BALL
// ramming someone at hs m/s (null below the threshold): damage climbs with speed up to the cap, knockback with it
export function wbRam(hs) {
  const R = MECH.wrecking.ram;
  if (!(hs >= R.min)) return null;
  return { dmg: Math.min(R.cap, R.base + (hs - R.min) * R.mul), kb: hs * R.kb, up: R.up + hs * 0.15 };
}
// how big a slam from h metres up is (k: 0 = off a hop, 1 = from h1 up or more), and what it does at distance d
export function wbSlam(h) {
  const S = MECH.wrecking.slam, k = Math.max(0, Math.min(1, (h - S.h0) / (S.h1 - S.h0))), at = (a) => a[0] + (a[1] - a[0]) * k;
  return { k, dmg: at(S.dmg), r: at(S.r), kb: at(S.kb), up: at(S.up) };
}
// the pile driver's blast at distance d (null outside): full at the middle, edge x at the rim
export function wbPile(d) {
  const P = MECH.wrecking.pile;
  if (!(d <= P.r)) return null;
  const f = 1 - d / P.r;
  return { dmg: P.dmg * (P.edge + (1 - P.edge) * f), kb: P.kb * (0.4 + 0.6 * f), up: P.up2 * (0.5 + 0.5 * f) };
}
// the rev launch's speed for a charge held c s
export const wbRevSpeed = (c) => { const R = MECH.wrecking.rev, k = Math.max(0, Math.min(1, c / R.charge)); return R.speed[0] + (R.speed[1] - R.speed[0]) * k; };

// ---- VENDING MACHINE
// cola charges ({ n, t }): one comes back every `every` s (t = when the next started counting), up to `charges`
export function vmCharges(c, n) {
  const C = MECH.vending.cola, ms = C.every * 1000;
  if (c.n >= C.charges) { c.n = C.charges; c.t = n; return c.n; }
  while (c.n < C.charges && n - c.t >= ms) { c.n++; c.t += ms; }
  if (c.n >= C.charges) c.t = n;
  return c.n;
}
// the OUT OF ORDER wall standing at p (its foot, the middle) facing yaw: where the segment a-b goes through it, as a
// fraction of a-b (null: it misses the panel). the panel is a flat sign w wide, h tall
export function vmWallCross(wall, a, b) {
  const W = MECH.vending.wall, w = wall.w || W.w, h = wall.h || W.h, fx = -Math.sin(wall.yaw), fz = -Math.cos(wall.yaw);
  const da = (a[0] - wall.p[0]) * fx + (a[2] - wall.p[2]) * fz, db = (b[0] - wall.p[0]) * fx + (b[2] - wall.p[2]) * fz;
  if ((da > 0) === (db > 0) || da === db) return null;
  const s = da / (da - db), q = [a[0] + (b[0] - a[0]) * s, a[1] + (b[1] - a[1]) * s, a[2] + (b[2] - a[2]) * s];
  const side = (q[0] - wall.p[0]) * -fz + (q[2] - wall.p[2]) * fx, up = q[1] - wall.p[1];
  if (side > (wall.wr ?? w / 2) || side < -(wall.wl ?? w / 2) || up < -0.2 || up > h) return null; // (wl / wr: each half, clipped where a building stops it)
  return { s, at: q };
}
// ---- TROLLEY
// a spot on the trolley (l: local, x right, +z back) in the world, for a trolley at pos facing yaw
export const trSpot = (pos, yaw, l) => { const c = Math.cos(yaw), s = Math.sin(yaw); return [pos[0] + l[0] * c + l[2] * s, pos[1] + l[1], pos[2] - l[0] * s + l[2] * c]; };
// the push with a ram charge c (0..1): its speed, damage, knockback
export function trPush(c) {
  const P = MECH.trolley.push, k = Math.max(0, Math.min(1, c || 0)), at = (a) => a[0] + (a[1] - a[0]) * k;
  return { v: at(P.v), dmg: at(P.dmg), kb: at(P.kb), up: P.up, k };
}
// driving into someone at hs m/s (null below the threshold)
export function trRam(hs) {
  const R = MECH.trolley.ram;
  if (!(hs >= R.min)) return null;
  return { dmg: Math.min(R.cap, R.base + (hs - R.min) * R.mul), kb: hs * R.kb, up: R.up };
}
// one step of the trolley's driving on its flat speed h = [vx, vz] (changed in place): sideways grip relative to the way
// it's being pushed (hardly any while drifting), a quick shove up to top, rolling to a stop with nothing held, a fast
// bleed over the top speed, and the wonky wheel's pull to the left (pull: the client's own step; bots drive straight)
export function trDrive(h, wx, wz, dt, top, drift, ground, pull) {
  const F = MECH.trolley, wl = Math.hypot(wx, wz);
  if (wl) { wx /= wl; wz /= wl; }
  let hs = Math.hypot(h[0], h[1]);
  if (ground) {
    if (wl) {
      const al = h[0] * wx + h[1] * wz, g = Math.exp(-(drift ? F.drift.grip : F.grip) * dt);
      h[0] = al * wx + (h[0] - al * wx) * g; h[1] = al * wz + (h[1] - al * wz) * g;
      const side = Math.hypot(h[0] - al * wx, h[1] - al * wz), room = Math.sqrt(Math.max(0, top * top - side * side)); // (the slide counts: a drift never goes faster than top)
      if (al < room) { const a = Math.min(room - al, F.accel * top * dt); h[0] += a * wx; h[1] += a * wz; }
    } else if (hs > 0) { const k = Math.max(0, hs - Math.max(hs, 3) * F.fric * (drift ? 0.4 : 1) * dt) / hs; h[0] *= k; h[1] *= k; }
    hs = Math.hypot(h[0], h[1]);
    if (hs > top) { const k = Math.max(top, hs - 16 * dt) / hs; h[0] *= k; h[1] *= k; }
  } else {
    if (wl) { const al = h[0] * wx + h[1] * wz; if (al < Math.min(top, F.airCap)) { const a = F.accel * 0.25 * top * dt; h[0] += a * wx; h[1] += a * wz; } }
    hs = Math.hypot(h[0], h[1]);
    if (hs > top) { const k = Math.max(top, hs - 16 * dt) / hs; h[0] *= k; h[1] *= k; } // (the same bleed as on the floor: the server's cap comes down this fast)
  }
  hs = Math.hypot(h[0], h[1]);
  if (pull && ground && hs > 1) { const a = F.pull * Math.min(1, hs / F.speed) * dt, c = Math.cos(a), s = Math.sin(a); const x = h[0]; h[0] = x * c + h[1] * s; h[1] = h[1] * c - x * s; }
  return hs;
}

mechScale(SCALE.def); // (after every frame's helpers: the heroes' rows are in FRAMES by now)
