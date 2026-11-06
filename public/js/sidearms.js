// The plain sidearms' moving parts and viewmodel animations (the firing lives in weapons.js like every gun):
//   Plan B          the slide kicks back on every shot and locks back on empty, the hammer drops, the mag drops out
//                   and the off hand slaps a fresh one in (an empty reload ends with the thumb dropping the slide)
//   Lefty & Righty  a gun per hand: the cocking knob jumps on every shot, each hand reloads on its own (the gun
//                   flicks its mag out, dips off screen, comes back loaded and racks); stickers say L and R
//   Half a Shotgun  the hammers fall one per barrel, a reload breaks it open, both shells pop out, the off hand
//                   thumbs two fresh ones in, a flick of the wrist snaps it shut and the thumb cocks both hammers
// Parts are found by name in the code model (sidemodels.js) and by the names in a Blender model's metadata.
import * as THREE from 'three';
import { ANIMS } from './anim.js';
import { M } from './models.js';
import { G } from './ctx.js';
import { sfx } from './audio.js';

const PI2 = Math.PI * 2;
const K = (t, p = [0, 0, 0], r = [0, 0, 0], e = 'smooth', s = 1) => ({ t, p, r, e, s });

// ------------------------------------------------------------ animations (offsets on top of the weapon's pose)
// channels (sampleCh): slide 0 home..1 back, mag = m out along the mag's way out (>= 0.18 hidden), hinge 0 shut..1 open,
// shells = m each shell is pulled back out of its chamber (>= 0.15 hidden), cock 0 down..1 both hammers cocked,
// cocker 0..1 knob back, lh = the off hand [k 0 away..1 on it, what it follows: 1 the mag, 2 shell 1, 3 shell 2]
const SIDE_ANIMS = {
  // Plan B: out of the holster in a blink (it's the quick one)
  draw_pistol: { keys: [K(0, [0.05, -0.24, 0.08], [-1.15, 0.3, 0.7]), K(0.13, [0, 0.014, -0.01], [0.1, -0.02, -0.07], 'snap'), K(0.2, [0, -0.003, 0.004], [-0.03, 0, 0.015]), K(0.27)], events: [[0.12, 'click']] },
  // press check (crack the slide, peek at the brass), then turn it to admire the other side
  inspect_pistol: { keys: [
    K(0), K(0.32, [-0.06, 0.045, 0.03], [0.18, 0.62, 0.42]), K(1.0, [-0.065, 0.05, 0.03], [0.2, 0.66, 0.44]),
    K(1.35, [-0.05, 0.05, 0.02], [0.22, -0.75, -0.55]), K(1.85, [-0.05, 0.052, 0.02], [0.24, -0.78, -0.57]), K(2.2),
  ], ch: { slide: [[0.4, 0], [0.55, 0.42], [0.85, 0.42], [0.93, 0]] }, events: [[0.55, 'slideBack'], [0.93, 'slideHome']] },
  // tactical reload: tip it, drop the mag, the off hand brings a fresh one up and slaps it home
  reload_pistol: { keys: [
    K(0), K(0.16, [-0.03, 0.03, 0.03], [0.32, 0.38, 0.55]), K(0.78, [-0.03, 0.028, 0.03], [0.3, 0.38, 0.55]),
    K(0.84, [-0.03, 0.05, 0.03], [0.4, 0.38, 0.55], 'snap'), K(0.98, [-0.03, 0.03, 0.03], [0.3, 0.38, 0.52]), K(1.35),
  ], ch: { mag: [[0.16, 0], [0.2, 0.02], [0.36, 0.3], [0.5, 0.3], [0.51, 0.12], [0.84, 0]], lh: [[0.3, 0, 1], [0.5, 0.65, 1], [0.6, 1, 1], [0.86, 1, 1], [1.05, 0, 1]] },
  events: [[0.18, 'magOut'], [0.84, 'magIn']] },
  // empty: the slide is locked back the whole way, then the thumb drops it at the end
  reload_pistol_empty: { keys: [
    K(0), K(0.16, [-0.03, 0.03, 0.03], [0.32, 0.38, 0.55]), K(0.76, [-0.03, 0.028, 0.03], [0.3, 0.38, 0.55]),
    K(0.82, [-0.03, 0.05, 0.03], [0.4, 0.38, 0.55], 'snap'), K(1.02, [-0.03, 0.035, 0.03], [0.26, 0.3, 0.42]),
    K(1.08, [-0.02, 0.05, 0.02], [0.05, 0.1, 0.1], 'snap'), K(1.35),
  ], ch: { mag: [[0.16, 0], [0.2, 0.02], [0.36, 0.3], [0.48, 0.3], [0.49, 0.12], [0.82, 0]], lh: [[0.28, 0, 1], [0.48, 0.65, 1], [0.58, 1, 1], [0.84, 1, 1], [1.0, 0, 1]], slide: [[1.04, 1], [1.08, 0]] },
  events: [[0.18, 'magOut'], [0.82, 'magIn'], [1.06, 'slideHome']] },

  // Lefty & Righty: both come up crossed and snap apart (the left gun plays every key mirrored)
  draw_akimbo: { keys: [K(0, [-0.1, -0.28, 0.08], [-1.0, 0.7, 1.1]), K(0.2, [0.006, 0.012, 0], [0.08, -0.04, -0.08], 'snap'), K(0.34)], events: [[0.19, 'click']] },
  // gangster tilt: turn them flat, admire, rack both knobs
  inspect_akimbo: { keys: [
    K(0), K(0.35, [-0.03, 0.04, 0.02], [0.05, 0.12, 1.42], 'back'), K(1.15, [-0.035, 0.045, 0.02], [0.08, 0.14, 1.46]),
    K(1.4, [-0.01, 0.02, 0], [-0.25, 0.04, 0.1]), K(1.55, [-0.01, 0.03, 0.02], [-0.32, 0.04, 0.1], 'snap'), K(1.95),
  ], ch: { cocker: [[1.4, 0], [1.48, 1], [1.56, 0]] }, events: [[1.48, 'rack']] },
  // one hand's reload (each hand plays its own): flick the mag out, down off screen to grab one, back up, rack
  reload_akimbo: { keys: [
    K(0), K(0.14, [0.02, -0.02, 0.03], [0.35, -0.15, 0.55], 'snap'), K(0.3, [0.02, -0.04, 0.03], [0.3, -0.1, 0.5]),
    K(0.62, [0.05, -0.34, 0.1], [0.95, 0, 0.3], 'in'), K(0.92, [0.05, -0.36, 0.1], [1.0, 0, 0.25]),
    K(1.16, [0, 0.015, -0.005], [-0.12, 0, -0.08], 'snap'), K(1.3, [0, 0.02, 0], [-0.2, 0, -0.05]), K(1.5),
  ], ch: { mag: [[0.1, 0], [0.16, 0.06], [0.34, 0.3], [0.9, 0.3], [0.92, 0]], cocker: [[1.24, 0], [1.31, 1], [1.38, 0]] },
  events: [[0.13, 'magOut'], [1.12, 'magIn'], [1.31, 'rack']] },

  // Half a Shotgun: comes up broken open and flicks shut
  draw_sawnoff: { keys: [K(0, [0.05, -0.3, 0.12], [-0.95, 0.2, 0.55]), K(0.24, [0, 0.01, 0], [0.12, 0, 0], 'snap'), K(0.31, [0, 0.03, -0.01], [-0.16, 0, 0], 'snap'), K(0.52)],
    ch: { hinge: [[0, 1], [0.26, 1], [0.31, 0]] }, events: [[0.31, 'close']] },
  // break it, look down the chambers, flick it shut like a movie
  inspect_sawnoff: { keys: [
    K(0), K(0.4, [-0.04, 0.06, 0.04], [0.55, 0.5, 0.35]), K(1.3, [-0.045, 0.065, 0.04], [0.58, 0.52, 0.36]),
    K(1.42, [-0.01, 0.04, 0], [-0.22, 0.1, 0.05], 'snap'), K(1.6, [0, 0.01, 0], [0.05, 0, 0]), K(2.0),
  ], ch: { hinge: [[0.25, 0], [0.42, 1], [1.36, 1], [1.42, 0]], shells: [[0.42, 0, 0], [0.5, 0.012, 0.012], [1.3, 0.012, 0.012], [1.36, 0, 0]] },
  events: [[0.4, 'break'], [1.42, 'close']] },
  // the reload: break it, both shells pop out, thumb one in, thumb the other in, flick shut, cock both hammers
  reload_sawnoff: { keys: [
    K(0), K(0.22, [-0.02, 0.04, 0.02], [0.38, 0.3, 0.25]), K(0.42, [-0.02, 0.05, 0.02], [0.44, 0.3, 0.25]),
    K(0.5, [-0.02, 0.08, 0.0], [0.75, 0.3, 0.2], 'snap'), K(0.66, [-0.02, 0.04, 0.02], [0.4, 0.3, 0.25]), // toss: the shells fly
    K(1.5, [-0.02, 0.04, 0.02], [0.42, 0.32, 0.26]),
    K(1.74, [-0.01, 0.06, -0.01], [-0.26, 0.06, 0.04], 'snap'), K(1.84, [0, 0.01, 0], [0.06, 0, 0]),
    K(1.98, [0, 0.0, 0.01], [0.1, 0, 0]), K(2.3),
  ], ch: {
    hinge: [[0.1, 0], [0.24, 1], [1.68, 1], [1.74, 0]],
    shells: [[0.24, 0, 0], [0.4, 0.03, 0.03], [0.48, 0.2, 0.2], [0.72, 0.2, 0.2], [0.73, 0.075, 0.2], [0.98, 0, 0.2], [1.06, 0, 0.2], [1.07, 0, 0.075], [1.32, 0, 0]],
    lh: [[0.5, 0, 2], [0.68, 0.7, 2], [0.76, 1, 2], [0.98, 1, 2], [1.02, 0.55, 2.5], [1.06, 0.6, 3], [1.1, 1, 3], [1.32, 1, 3], [1.5, 0, 3]],
    cock: [[1.86, 0], [1.94, 0.5], [2.0, 1]],
  }, events: [[0.24, 'break'], [0.48, 'eject'], [0.98, 'thumb'], [1.32, 'thumb'], [1.74, 'close'], [1.94, 'cock'], [2.0, 'cock']] },
};
Object.assign(ANIMS, SIDE_ANIMS);
for (const k of Object.keys(SIDE_ANIMS)) { const a = ANIMS[k]; a.dur = a.keys[a.keys.length - 1].t; }
export const SIDEARMS = new Set(['pistol', 'akimbo', 'sawnoff']);
// which reload to play (an empty Plan B has its slide locked back)
export function reloadAnim(id, ammo) {
  if (id === 'pistol') return ammo <= 0 ? 'reload_pistol_empty' : 'reload_pistol';
  return ANIMS['reload_' + id] && id !== 'akimbo' ? 'reload_' + id : null;
}

// ------------------------------------------------------------ parts
const CODE = { // the code models' node names (sidemodels.js); a Blender model's metadata names its own
  pistol: { slide: { node: 'slide', travel: 0.038 }, mag: { node: 'mag', dir: [0, -1, 0] }, hammers: ['hammer'] },
  akimbo: { cocker: { node: 'cocker', travel: 0.03 }, mag: { node: 'mag', dir: [0, -1, 0] }, tags: { L: 'tagL', R: 'tagR' } },
  sawnoff: { hinge: { node: 'hinge', open: 0.7 }, shells: ['shell1', 'shell2'], hammers: ['hammerR', 'hammerL'] },
};
const find = (g, n) => { let r = null; if (n) g.traverse((o) => { if (!r && o.name === n) r = o; }); return r; };
// bind once per model: g = a weapon from buildWeapon (Blender metadata in g.userData.jf, else the code names)
export function sideParts(g, id) {
  if (g.userData.sp !== undefined) return g.userData.sp;
  const mt = g.userData.glb === 'blender' && g.userData.jf ? g.userData.jf : CODE[id] || {}, p = {};
  if (mt.slide && (p.slide = find(g, mt.slide.node))) { p.slide0 = p.slide.position.z; p.travel = mt.slide.travel || 0.038; }
  if (mt.cocker && (p.cocker = find(g, mt.cocker.node))) { p.cock0 = p.cocker.position.z; p.ctravel = mt.cocker.travel || 0.03; }
  if (mt.mag && (p.mag = find(g, mt.mag.node))) { p.mag0 = p.mag.position.clone(); p.magDir = new THREE.Vector3(...(mt.mag.dir || [0, -1, 0])).normalize(); }
  p.hammers = (mt.hammers || []).map((n) => find(g, n)).filter(Boolean).map((o) => ({ o, rx: o.rotation.x }));
  if (mt.hinge && (p.hinge = find(g, mt.hinge.node))) {
    p.hinge0 = p.hinge.rotation.x; p.open = mt.hinge.open || 0.7;
    g.updateMatrixWorld(true);
    for (const n of mt.hinge.rides || []) { const o = find(g, n); if (o && o.parent !== p.hinge) p.hinge.attach(o); } // forend + shells swing with the barrels
  }
  p.shells = (mt.shells || []).map((n) => find(g, n)).filter(Boolean).map((o) => ({ o, z: o.position.z }));
  if (mt.tags) p.tags = { L: find(g, mt.tags.L), R: find(g, mt.tags.R) };
  p.kick = 1; p.hamT = 1;
  g.userData.sp = p;
  return p;
}
// which hand this gun is in (the akimbo stickers)
export function sideHand(g, id, hand) { const p = sideParts(g, id); if (p.tags) for (const k of ['L', 'R']) if (p.tags[k]) p.tags[k].visible = k === hand; }
// a shot: the slide / knob kicks back, the hammer drops
export function sideShot(g, id) { const p = sideParts(g, id); p.kick = 0; p.hamT = 0; }
// every frame. an = the animation playing (or null) at time at; st = { empty (pistol: ammo 0), fired (sawed-off:
// barrels fired since the reload) }
export function sideStep(g, id, dt, an, at, st, sampleCh) {
  const p = sideParts(g, id), ch = (n) => (an ? sampleCh(an, n, at) : null);
  p.kick = Math.min(1, p.kick + dt); p.hamT = Math.min(1, p.hamT + dt);
  const kick = (t) => (t < 0.022 ? t / 0.022 : t < 0.075 ? 1 - (t - 0.022) / 0.053 : 0); // back fast, home a bit slower
  if (p.slide) { const c = ch('slide'); const k = c ? c[0] : st.empty ? 1 : kick(p.kick); p.slide.position.z = p.slide0 + k * p.travel; }
  if (p.cocker) { const c = ch('cocker'); p.cocker.position.z = p.cock0 + (c ? c[0] : kick(p.kick * 1.4)) * p.ctravel; }
  if (p.mag) { const c = ch('mag'), d = c ? c[0] : 0; p.mag.position.copy(p.mag0).addScaledVector(p.magDir, d); p.mag.visible = d < 0.18; }
  if (p.hinge) { const c = ch('hinge'); p.hinge.rotation.x = p.hinge0 - (c ? c[0] : 0) * p.open; }
  if (p.shells.length) { const c = ch('shells'); p.shells.forEach((s, i) => { const d = c ? c[i] : 0; s.o.position.z = s.z + d; s.o.visible = d < 0.15; }); }
  if (p.hammers.length) {
    const c = ch('cock');
    p.hammers.forEach((h, i) => {
      let down; // 0 cocked .. 1 fallen
      if (id === 'pistol') down = st.empty ? 0 : p.hamT < 0.02 ? p.hamT / 0.02 : p.hamT < 0.06 ? 1 - (p.hamT - 0.02) / 0.04 : 0; // the slide recocks it
      else down = c ? (i < st.fired ? 1 - c[0] : 0) : i < st.fired ? 1 : 0;
      h.o.rotation.x = h.rx - down * 0.75;
    });
  }
  return p;
}

// ------------------------------------------------------------ the off hand (reloads): a fist that follows the mag / a shell
const OFF = new THREE.Vector3(-0.1, -0.3, 0.14); // where it waits, out of view (wrap space)
const tA = new THREE.Vector3(), tB = new THREE.Vector3();
export function offHand(m) {
  if (m.off) return m.off;
  const h = new THREE.Group();
  const fist = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.06, 0.085), M(0xf1c27d));
  const thumb = new THREE.Mesh(new THREE.BoxGeometry(0.018, 0.02, 0.05), M(0xe0b06d)); thumb.position.set(0.028, 0.02, -0.02);
  h.add(fist, thumb); h.visible = false;
  m.wrap.add(h);
  return (m.off = h);
}
// lh channel: [k, follow]. follow 1 = palm under the mag's base pad, 2 / 3 = the thumb behind shell 1 / 2
export function stepOffHand(m, id, an, at, sampleCh) {
  const h = offHand(m), c = an ? sampleCh(an, 'lh', at) : null;
  if (!c || c[0] <= 0.001 || !m.wrap.visible) { h.visible = false; return; }
  const p = sideParts(m.g, id), f = Math.round(c[1]);
  m.wrap.updateMatrixWorld(true);
  let tgt = null;
  if (f === 1 && p.mag) { p.mag.getWorldPosition(tA); m.wrap.worldToLocal(tA); tgt = tA.add(tB.set(0.004, -0.035, 0.012)); h.rotation.set(-0.35, 0, 0.15); }
  else if ((f === 2 || f === 3) && p.shells[f - 2]) {
    const s = p.shells[f - 2].o; s.getWorldPosition(tA); m.wrap.worldToLocal(tA);
    tB.set(0, -0.012, 0.05); if (p.hinge) tB.applyQuaternion(p.hinge.quaternion); // behind the rim, along the barrel
    tgt = tA.add(tB); h.rotation.set(-0.5 - (p.hinge ? p.hinge0 - p.hinge.rotation.x : 0), 0.2, 0.3);
  }
  if (!tgt) { h.visible = false; return; }
  h.position.copy(OFF).lerp(tgt, c[0]);
  h.visible = true;
}

// ------------------------------------------------------------ animation events with sounds + bits flying
export function sideEvent(ev, m, id) {
  const sys = G.skinFxVM, p = sideParts(m.g, id), R = (k) => (Math.random() - 0.5) * k;
  switch (ev) {
    case 'magOut': sfx.mech('magOut'); break;
    case 'magIn': sfx.mech('magIn'); break;
    case 'slideBack': sfx.mech('slideBack'); break;
    case 'slideHome': sfx.mech('slideHome'); break;
    case 'rack': sfx.mech('rack'); break;
    case 'break': sfx.mech('break'); break;
    case 'close': sfx.mech('close'); break;
    case 'thumb': sfx.mech('thumb'); break;
    case 'cock': sfx.mech('cock'); break;
    case 'eject': // both shells pop out and tumble away (empty red hulls, brass heads)
      sfx.mech('eject');
      if (!sys) break;
      for (const s of p.shells) {
        s.o.getWorldPosition(tA);
        for (let i = 0; i < 2; i++) sys.norm.spawn(tA.x + R(0.01), tA.y + R(0.01), tA.z + 0.02, R(0.4) + 0.25, 1.1 + Math.random() * 0.5, 0.55 + Math.random() * 0.3, 0.7, i ? 0.016 : 0.022, 0.02, i ? 0xd9a53a : 0xd02a2a, i ? 0xd9a53a : 0x8a1a1a, 1, 5, 0.3);
        for (let i = 0; i < 5; i++) sys.norm.spawn(tA.x, tA.y, tA.z + 0.02, R(0.15), 0.12 + Math.random() * 0.1, 0.1 + R(0.1), 0.6, 0.006, 0.02, 0xbbbbbb, 0x777777, 0.4, -0.05, 1.5); // a wisp of smoke
      }
      break;
  }
}
