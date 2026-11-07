// MR. OVERTIME's rig on top of the story actor: his clip set (ot_*), the timing marks inside each attack (so the combat
// referee's windows and the sounds line up with the tells), his damage states, the far LOD swap, steam, sparks, ticking,
// and preview fx (staples, the slam's frozen-time ring) for rehearsal and cutscenes. no damage happens here.
//   OT.play(a, clip, {hold})  OT.dmg(a, 'plate_off' | 'cracked' | 'sparking' | 'ripped' | 'card_torn' | 'fresh')
//   OT.variant(a, 1 | 2 | 3 | 4 | 'rehire')   his look per fight (content/bosses.js overtime_* look)
//   OT.on((ev) => ...)  ev = { type: 'ot', mark, id, clip, at: [x, y, z] }   (marks: MARKS below)
import * as THREE from 'three';
import { G } from '../ctx.js';
import { synth } from '../audio.js';
import { CLIPS, actors, play as playClip } from './actors.js';

const clamp = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
const ss = (t) => { t = clamp(t); return t * t * (3 - 2 * t); };
const seg = (t, a, b) => ss((t - a) / (b - a)); // 0 -> 1 between a and b, eased
const bump = (t) => (t <= 0 || t >= 1 ? 0 : Math.sin(t * Math.PI));
const win = (t, a, b, c, d) => seg(t, a, b) * (1 - seg(t, c, d)); // in a..b, hold, out c..d

// ---------------------------------------------------------------- the clip set
// conventions (actors.js): arm/fore .x + = raise forward / bend the elbow, spine.x - = bend forward, head.x + = look up,
// arm.z + (right) / armL.z - (left) = out to the side; leg.x + = thigh forward, knee.x - = shin back. body = the hips
// (in his own units: the root is x2.5, so 0.1 here is 25 cm). every clip is additive on the walk pose
export const OT_CLIPS = {
  // standing menace: a little hunched over you, staplers half up, the head ticking side to side, the odd clack
  ot_idle: { len: 9e9, f(c, t, k) {
    const br = Math.sin(t * 1.3);
    c.spine.rotation.x -= (0.08 + br * 0.015) * k;
    c.arm.rotation.x += (0.3 + br * 0.03) * k; c.armL.rotation.x += (0.24 - br * 0.03) * k;
    c.foreR.rotation.x += 0.55 * k; c.foreL.rotation.x += 0.5 * k; c.arm.rotation.z += 0.12 * k; c.armL.rotation.z -= 0.12 * k;
    c.head.rotation.z += Math.round(Math.sin(t * 0.5) * 3) / 3 * 0.09 * k; // (ticks between positions, like a second hand)
    const cl = (t % 3.3) / 3.3; c.foreR.rotation.x += bump((cl - 0.9) / 0.05) * 0.35 * k; // clack
  } },
  // stalking you: leaning in, both staplers up and pointed, head level and fixed on you
  ot_stalk: { len: 9e9, f(c, t, k) {
    c.spine.rotation.x -= 0.2 * k; c.head.rotation.x += 0.16 * k;
    c.arm.rotation.x += (0.75 + Math.sin(t * 3.1) * 0.05) * k; c.armL.rotation.x += (0.6 - Math.sin(t * 3.1) * 0.05) * k;
    c.foreR.rotation.x += 0.45 * k; c.foreL.rotation.x += 0.6 * k;
    c.body.rotation.z += Math.sin(t * 3.1) * 0.03 * k;
  } },
  // Staple Gun: raise the right stapler, clack, clack (the tip glows), FIRE, the recoil throws the arm up
  ot_staple: { len: 1.5, f(c, t, k) {
    const up = seg(t, 0, 0.28);
    c.arm.rotation.x += (1.45 * up - 0.5 * bump((t - 0.85) / 0.35)) * k; c.foreR.rotation.x -= 0.15 * up * k;
    c.arm.rotation.z -= 0.15 * up * k; c.spine.rotation.y -= 0.25 * up * k; c.spine.rotation.x += 0.12 * bump((t - 0.85) / 0.4) * k;
    for (const m of [0.35, 0.7]) c.foreR.rotation.z += bump((t - m) / 0.08) * 0.12 * k; // the clacks
    c.armL.rotation.x += 0.4 * up * k; c.foreL.rotation.x += 0.9 * up * k; // the other arm braces
    c.body.position.z += 0.04 * bump((t - 0.85) / 0.35) * k; // knocked back a step
  } },
  // Staple Fan: both arms straight up, ten clacks, then they chop down and fan five staples
  ot_fan: { len: 2.1, f(c, t, k) {
    const up = win(t, 0, 0.35, 1.45, 1.65), chop = win(t, 1.45, 1.65, 1.9, 2.1);
    c.arm.rotation.x += (2.7 * up + 1.3 * chop) * k; c.armL.rotation.x += (2.7 * up + 1.3 * chop) * k;
    c.arm.rotation.z += (0.25 * up + 0.5 * chop) * k; c.armL.rotation.z -= (0.25 * up + 0.5 * chop) * k;
    c.foreR.rotation.x += 0.1 * k; c.foreL.rotation.x += 0.1 * k;
    for (let i = 0; i < 10; i++) { const m = 0.4 + i * 0.1; c.foreR.rotation.z += bump((t - m) / 0.05) * 0.1 * k; c.foreL.rotation.z -= bump((t - m - 0.05) / 0.05) * 0.1 * k; }
    c.spine.rotation.x += (0.15 * up - 0.3 * chop) * k; c.head.rotation.x += 0.3 * up * k;
  } },
  // Overtime Slam: checks his watch, crouches (steam from the collar), jumps, slams down with both fists, gets up
  ot_slam: { len: 2.4, f(c, t, k) {
    const watch = win(t, 0, 0.2, 0.5, 0.65), crouch = win(t, 0.55, 0.85, 0.85, 0.95), air = win(t, 0.9, 1.15, 1.25, 1.42);
    const land = win(t, 1.4, 1.46, 1.8, 2.3);
    c.armL.rotation.x += 1.35 * watch * k; c.foreL.rotation.x += 1.7 * watch * k; c.armL.rotation.z += 0.35 * watch * k; c.head.rotation.x -= 0.45 * watch * k;
    c.body.position.y += (-0.12 * crouch + 0.62 * air - 0.16 * land) * k;
    c.legL.rotation.x += (0.75 * crouch + 0.5 * air + 0.9 * land) * k; c.legR.rotation.x += (0.75 * crouch + 0.3 * air + 0.9 * land) * k;
    c.kneeL.rotation.x -= (1.3 * crouch + 0.9 * air + 1.4 * land) * k; c.kneeR.rotation.x -= (1.3 * crouch + 1.1 * air + 1.4 * land) * k;
    c.spine.rotation.x -= (0.35 * crouch - 0.2 * air + 0.55 * land) * k;
    c.arm.rotation.x += (-0.5 * crouch + 2.9 * air + 1.0 * land) * k; c.armL.rotation.x += (-0.5 * crouch + 2.9 * air + 1.0 * land) * k;
    c.foreR.rotation.x += (0.4 * air + 0.2 * land) * k; c.foreL.rotation.x += (0.4 * air + 0.2 * land) * k;
    c.head.rotation.x += (0.3 * air - 0.2 * land) * k;
  } },
  // Punch In: arms thrown wide, the slot whirs open, a lunge and a bear-hug sweep, hold, let go
  ot_punchin: { len: 2.6, f(c, t, k) {
    const open = win(t, 0, 0.45, 0.9, 1.1), hug = win(t, 0.9, 1.15, 2.0, 2.5);
    c.arm.rotation.z += (1.3 * open - 0.2 * hug) * k; c.armL.rotation.z -= (1.3 * open - 0.2 * hug) * k;
    c.arm.rotation.x += (0.6 * open + 1.4 * hug) * k; c.armL.rotation.x += (0.6 * open + 1.4 * hug) * k;
    c.foreR.rotation.x += 0.9 * hug * k; c.foreL.rotation.x += 0.9 * hug * k;
    c.spine.rotation.x += (0.18 * open - 0.4 * hug) * k; c.head.rotation.x += 0.25 * open * k;
    c.body.position.z -= 0.12 * hug * k; c.legR.rotation.x += 0.5 * hug * k; c.kneeR.rotation.x -= 0.5 * hug * k;
  } },
  // Coffee Break: he sits down where he is, pours from a flask, sips, sighs. (held until the phase ends)
  ot_coffee: { len: 9e9, f(c, t, k) {
    const sit = seg(t, 0, 1.0) * k, sip = (Math.sin(t * 0.9) > 0.55 ? 1 : 0) * seg(t, 1.6, 2.2);
    c.body.position.y -= 0.42 * sit; c.body.position.z += 0.12 * sit;
    c.legL.rotation.x += 1.45 * sit; c.legR.rotation.x += 1.45 * sit; c.kneeL.rotation.x -= 1.45 * sit; c.kneeR.rotation.x -= 1.45 * sit;
    c.legL.rotation.z -= 0.15 * sit; c.legR.rotation.z += 0.15 * sit;
    c.spine.rotation.x -= 0.18 * sit;
    c.arm.rotation.x += (0.7 + 0.55 * sip) * sit; c.foreR.rotation.x += (1.2 + 0.5 * sip) * sit; c.arm.rotation.z -= 0.25 * sit; // the cup
    c.armL.rotation.x += 0.5 * sit; c.foreL.rotation.x += 1.0 * sit; c.armL.rotation.z += 0.2 * sit; // the flask
    c.head.rotation.x += 0.3 * sip * sit;
  } },
  // the phase change: back arches, arms out, head up, everything shakes, steam out of every seam
  ot_roar: { len: 2.2, f(c, t, k) {
    const r = win(t, 0, 0.35, 1.5, 2.1) * k, sh = Math.sin(t * 38) * 0.05 * r;
    c.spine.rotation.x += 0.38 * r + sh; c.head.rotation.x += 0.55 * r;
    c.arm.rotation.z += 1.0 * r; c.armL.rotation.z -= 1.0 * r; c.arm.rotation.x += 0.7 * r + sh; c.armL.rotation.x += 0.7 * r - sh;
    c.foreR.rotation.x += 0.6 * r; c.foreL.rotation.x += 0.6 * r;
    c.legL.rotation.z -= 0.12 * r; c.legR.rotation.z += 0.12 * r; c.body.position.y -= 0.05 * r;
  } },
  // a crit: the whole frame jolts back, head snaps, arms jerk out
  ot_flinch: { len: 0.7, f(c, t, k) {
    const b = bump(t / 0.7) * k, j = bump(t / 0.18) * k;
    c.spine.rotation.x += 0.32 * b; c.head.rotation.x += 0.35 * j; c.head.rotation.z += 0.2 * j;
    c.arm.rotation.z += 0.5 * j; c.armL.rotation.z -= 0.5 * j; c.body.position.z += 0.06 * b;
  } },
  // the plate comes off: a big stagger back, arms flail, then both stapler arms come in to cover the heart
  ot_plate_rip: { len: 1.9, f(c, t, k) {
    const st = win(t, 0, 0.12, 0.6, 1.0) * k, cover = win(t, 0.7, 1.1, 1.6, 1.9) * k;
    c.spine.rotation.x += 0.5 * st - 0.25 * cover; c.head.rotation.x += 0.4 * st - 0.45 * cover;
    c.arm.rotation.x += -0.5 * st + 1.15 * cover; c.armL.rotation.x += -0.4 * st + 1.15 * cover;
    c.arm.rotation.z += 0.9 * st - 0.35 * cover; c.armL.rotation.z -= 0.9 * st - 0.35 * cover;
    c.foreR.rotation.x += 0.3 * st + 1.7 * cover; c.foreL.rotation.x += 0.3 * st + 1.7 * cover;
    c.body.position.z += 0.1 * st; c.legL.rotation.x -= 0.3 * st; c.kneeL.rotation.x -= 0.4 * st;
  } },
  // on one knee, steam pouring from his chest (fight 1's 'rescheduled' talk). held
  ot_kneel: { len: 9e9, f(c, t, k) {
    const d = seg(t, 0, 0.8) * k;
    c.body.position.y -= 0.3 * d; c.legR.rotation.x += 1.5 * d; c.kneeR.rotation.x -= 1.5 * d; c.legL.rotation.x -= 0.2 * d; c.kneeL.rotation.x -= 2.0 * d;
    c.spine.rotation.x -= (0.35 + Math.sin(t * 1.4) * 0.03) * d; c.head.rotation.x += 0.25 * d;
    c.arm.rotation.x += 0.9 * d; c.foreR.rotation.x += 0.9 * d; // a hand on the knee
    c.armL.rotation.x += 1.2 * d; c.foreL.rotation.x += 1.8 * d; c.armL.rotation.z += 0.35 * d; // looking at the watch
  } },
  // walking away after fight 1: lopsided, one stapler pressed over the hole in his chest, the head tilted, a hitch in
  // every other step (the clock ticks with a limp)
  ot_limp: { len: 9e9, f(c, t, k) {
    const hitch = Math.max(0, Math.sin(t * 3.2)) ** 6;
    c.body.rotation.z += (0.1 + hitch * 0.06) * k; c.spine.rotation.z -= 0.08 * k; c.spine.rotation.x -= 0.12 * k;
    c.armL.rotation.x += 1.05 * k; c.foreL.rotation.x += 1.65 * k; c.armL.rotation.z += 0.3 * k;
    c.arm.rotation.x -= 0.1 * k; c.arm.rotation.z += 0.05 * k; c.head.rotation.z -= (0.16 + hitch * 0.08) * k; c.head.rotation.x -= 0.1 * k;
    c.body.position.y -= hitch * 0.03 * k;
  } },
  // clocking out: checks the watch one last time, the knees go, he kneels, then folds forward from the waist until his
  // staplers are on the floor and his little head hangs between them. held
  ot_clockout: { len: 9e9, f(c, t, k) {
    const watch = win(t, 0, 0.4, 1.1, 1.4), knees = seg(t, 1.2, 2.0), fold = seg(t, 2.4, 3.4), tick = Math.sin(t * 6.3) > 0.98 ? 1 : 0;
    c.armL.rotation.x += 1.35 * watch * k; c.foreL.rotation.x += 1.7 * watch * k; c.armL.rotation.z += 0.35 * watch * k; c.head.rotation.x -= 0.4 * watch * k;
    c.body.position.y -= (0.42 * knees + 0.04 * fold) * k; c.body.position.z += 0.05 * fold * k;
    c.legL.rotation.x += 0.1 * knees * k; c.legR.rotation.x += 0.1 * knees * k;
    c.kneeL.rotation.x -= 1.9 * knees * k; c.kneeR.rotation.x -= 1.9 * knees * k;
    c.body.rotation.x -= 0.2 * fold * k;
    c.spine.rotation.x -= (0.25 * knees + 0.95 * fold) * k; c.head.rotation.x -= (0.3 * knees + 0.35 * fold + tick * 0.05) * k;
    c.arm.rotation.x += (0.15 * knees + 0.75 * fold) * k; c.armL.rotation.x += (0.15 * knees + 0.75 * fold) * k;
    c.arm.rotation.z += 0.25 * fold * k; c.armL.rotation.z -= 0.25 * fold * k; c.foreR.rotation.x += 0.15 * fold * k; c.foreL.rotation.x += 0.15 * fold * k;
  } },
};
OT_CLIPS.staple_shot = OT_CLIPS.ot_staple; // (the script's name for it, c4)
Object.assign(CLIPS, OT_CLIPS);

// the moments inside each clip (seconds): sounds, fx and the referee's windows hang off these
export const MARKS = {
  ot_idle: [], ot_stalk: [], staple_shot: [[0.35, 'clack'], [0.7, 'clack'], [0.85, 'fire']],
  ot_staple: [[0.35, 'clack'], [0.7, 'clack'], [0.85, 'fire']],
  ot_fan: [...Array.from({ length: 10 }, (_, i) => [0.4 + i * 0.1, 'clack']), [1.6, 'fan']],
  ot_slam: [[0.3, 'watch'], [0.7, 'steam'], [0.92, 'jump'], [1.42, 'land']],
  ot_punchin: [[0.35, 'slotOpen'], [1.1, 'grab'], [2.3, 'slotClose']],
  ot_coffee: [[0.9, 'sit'], [1.8, 'pour'], [3.0, 'sip']],
  ot_roar: [[0.25, 'roar']],
  ot_flinch: [[0, 'flinch']],
  ot_plate_rip: [[0.02, 'plate']],
  ot_kneel: [[0.7, 'thud']], ot_limp: [],
  ot_clockout: [[0.4, 'watch'], [1.9, 'thud'], [3.2, 'thud']],
};

const listeners = new Set();
export const OT = {
  fx: true, // the preview fx (staples, ring, fines). the referee can turn them off and draw its own
  on(f) { listeners.add(f); return () => listeners.delete(f); },
  play(a, clip, opts = {}) { playClip(a, clip, opts); },
  dmg(a, state) { rigOf(a).dmg(state); },
  variant(a, v) { rigOf(a).variant(v); }, // 1 (pristine), 2 (patched, fight 2), 3 (scorched, glitching), 4 (fully billable), 'rehire'
  rig: (a) => rigOf(a),
};
window.JF_OT = OT; // (tests and the referee's devtools)

// ---------------------------------------------------------------- particles (one pool for every overtime)
const FX = [];
const geoBall = new THREE.SphereGeometry(1, 8, 6), geoBox = new THREE.BoxGeometry(1, 1, 1);
const steamMat = () => new THREE.MeshBasicMaterial({ color: 0xf4f4f8, transparent: true, opacity: 0.55, depthWrite: false });
const sparkMat = new THREE.MeshBasicMaterial({ color: 0xffe14d });
function puff(p, v, size = 0.4, life = 1.4) {
  const m = new THREE.Mesh(geoBall, steamMat()); m.position.copy(p); m.scale.setScalar(size * 0.4); G.scene.add(m);
  FX.push({ m, v: v.clone(), life, t: 0, kind: 'steam', size });
}
function spark(p, v, life = 0.5) {
  const m = new THREE.Mesh(geoBox, sparkMat); m.position.copy(p); m.scale.set(0.05, 0.05, 0.16); G.scene.add(m);
  FX.push({ m, v: v.clone(), life, t: 0, kind: 'spark' });
}
function stapleShot(p, dir) {
  const g = new THREE.Group(), mt = new THREE.MeshStandardMaterial({ color: 0xffe14d, emissive: 0xffa020, emissiveIntensity: 0.8, metalness: 0.6, roughness: 0.3 });
  for (const [w, h, x, y] of [[0.9, 0.12, 0, 0], [0.12, 0.5, -0.4, -0.22], [0.12, 0.5, 0.4, -0.22]]) { const b = new THREE.Mesh(geoBox, mt); b.scale.set(w, h, 0.12); b.position.set(x, y, 0); g.add(b); }
  g.position.copy(p); g.lookAt(p.clone().add(dir)); G.scene.add(g);
  FX.push({ m: g, v: dir.clone().multiplyScalar(38), life: 0.9, t: 0, kind: 'staple' });
}
function ring(p) { // the frozen-time ring: a cyan band racing out over the floor
  const m = new THREE.Mesh(new THREE.RingGeometry(0.85, 1, 48), new THREE.MeshBasicMaterial({ color: 0x4fd8ff, transparent: true, opacity: 0.85, side: THREE.DoubleSide, depthWrite: false }));
  m.rotation.x = -Math.PI / 2; m.position.copy(p); m.position.y += 0.06; G.scene.add(m);
  FX.push({ m, v: new THREE.Vector3(), life: 0.9, t: 0, kind: 'ring' });
}
function fxFrame(dt) {
  for (let i = FX.length - 1; i >= 0; i--) {
    const f = FX[i]; f.t += dt; const u = f.t / f.life;
    if (u >= 1) { G.scene.remove(f.m); if (f.kind === 'steam' || f.kind === 'ring') f.m.material.dispose(); FX.splice(i, 1); continue; }
    f.m.position.addScaledVector(f.v, dt);
    if (f.kind === 'steam') { f.v.multiplyScalar(1 - dt * 1.2); f.v.y += dt * 0.8; f.m.scale.setScalar(f.size * (0.4 + u * 1.4)); f.m.material.opacity = 0.55 * (1 - u); }
    else if (f.kind === 'spark') { f.v.y -= 14 * dt; f.m.lookAt(f.m.position.clone().add(f.v)); }
    else if (f.kind === 'ring') { const r = 1 + ss(u) * 11; f.m.scale.set(r, r, 1); f.m.material.opacity = 0.85 * (1 - u * u); }
  }
}

// ---------------------------------------------------------------- one overtime
const rigs = new Map();
const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const tv = V(), tv2 = V();
function rigOf(a) {
  let r = rigs.get(a.id);
  if (r && r.a === a) return r;
  r = makeRig(a); rigs.set(a.id, r); return r;
}
function makeRig(a) {
  const L = a.L, c = a.ch;
  const r = { a, last: null, lastT: -1, far: null, show: { dmgCrack: false, dmgRip: false, dmgCardTorn: false }, plateOff: false, sparking: false, steamT: 0, tickT: 0, anger: 0, debris: [] };
  const local = (joint, x, y, z) => c[joint].localToWorld(tv.set(x, y, z)).clone();
  const S = c.root.scale.x;
  r.at = {
    stack: (sx) => local('spine', sx * 0.13, 0.93, 0.22),
    heart: () => local('spine', 0, 0.42, -0.4),
    collar: () => local('spine', 0, 0.78, 0),
    muzzle: (s) => { const m = L.parts && L.parts['muzzle' + s]; return m ? m.getWorldPosition(V()) : local(s === 'R' ? 'handR' : 'handL', 0, -0.05, -0.04); },
    feet: () => V(a.pos[0], a.pos[1], a.pos[2]),
  };
  r.fwd = () => V(-Math.sin(a.yaw), 0, -Math.cos(a.yaw));
  // visibility: far LOD vs the full model, the damage pieces, the plate
  r.vis = () => {
    const far = !!r.far, all = L.partsAll || {};
    if (L.blender) for (const jn of ['body', 'legL', 'legR', 'kneeL', 'kneeR', 'spine', 'neck', 'head', 'armL', 'arm', 'foreL', 'foreR', 'handL', 'handR']) {
      const J = c[jn]; if (!J) continue;
      for (const ch of J.children) {
        if (ch.name === 'ot_lod') ch.visible = far;
        else if (ch.isMesh && !(L.face && ch === L.face.root)) ch.visible = !far;
      }
    }
    for (const [k, gs] of Object.entries(all)) {
      if (k === 'lod' || k.startsWith('muzzle') || k === 'tieEnd' || k === 'headJoint') continue;
      const on = !far && (k.startsWith('dmg') ? r.show[k] : k === 'plate' ? !r.plateOff : k === 'card' ? !r.show.dmgCardTorn : true);
      for (const gp of gs) gp.visible = on;
    }
    if (L.face) L.face.root.visible = !far;
  };
  r.dmg = (state) => {
    if (state === 'fresh') { r.show.dmgCrack = r.show.dmgRip = r.show.dmgCardTorn = false; r.sparking = false; r.restorePlate(); }
    if (state === 'plate_off' && !r.plateOff) r.dropPlate();
    if (state === 'cracked') { r.show.dmgCrack = true; burst(r, 12); synth.noise(0.3, 0.6, 'highpass', 3000, 6000, r.at.heart().toArray()); }
    if (state === 'sparking') { r.show.dmgCrack = true; r.sparking = true; }
    if (state === 'ripped') { r.show.dmgCrack = true; r.show.dmgRip = true; r.sparking = true; r.anger = 1; }
    if (state === 'card_torn') r.show.dmgCardTorn = true;
    r.vis();
  };
  // the plate: off the chest, tumbling to the floor, left lying there (for the scene; the referee owns the real one)
  r.dropPlate = () => {
    r.plateOff = true;
    for (const gp of (L.partsAll || {}).plate || []) {
      const d = gp.clone(true); gp.getWorldPosition(tv); gp.updateWorldMatrix(true, false); d.matrix.copy(gp.matrixWorld); d.matrix.decompose(d.position, d.quaternion, d.scale);
      d.visible = true; G.scene.add(d); const f = r.fwd();
      r.debris.push({ m: d, v: V(f.x * 4 + (Math.random() - 0.5) * 2, 5, f.z * 4), w: V(4 + Math.random() * 3, Math.random() * 2, 2), y0: a.pos[1], rest: false });
    }
    burst(r, 26); for (let i = 0; i < 6; i++) puff(r.at.heart(), V((Math.random() - 0.5) * 2, 1.5, (Math.random() - 0.5) * 2), 0.6, 1.6);
    synth.tone('sawtooth', 300, 60, 0.35, 0.4); synth.noise(0.5, 0.7, 'lowpass', 2500, 300);
    r.vis();
  };
  r.restorePlate = () => { for (const d of r.debris) G.scene.remove(d.m); r.debris.length = 0; r.plateOff = false; };
  // the coffee break's props: a mug in the right stapler's jaw, the flask in the left (code meshes, only while sitting)
  r.props = null;
  const propsOn = (on) => {
    if (on && !r.props) {
      const mug = new THREE.Group(), flask = new THREE.Group();
      const m1 = new THREE.MeshStandardMaterial({ color: 0xf4f4f0, roughness: 0.4 }), m2 = new THREE.MeshStandardMaterial({ color: 0x2a6a4a, roughness: 0.3, metalness: 0.4 }), m3 = new THREE.MeshStandardMaterial({ color: 0x3a1a0a, roughness: 0.2 });
      const cup = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.06, 0.13, 14), m1); mug.add(cup);
      const tea = new THREE.Mesh(new THREE.CircleGeometry(0.062, 14), m3); tea.rotation.x = -Math.PI / 2; tea.position.y = 0.055; mug.add(tea);
      const hd = new THREE.Mesh(new THREE.TorusGeometry(0.04, 0.012, 6, 12), m1); hd.position.x = 0.08; mug.add(hd);
      const bt = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.32, 14), m2); flask.add(bt);
      const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.065, 0.065, 0.07, 14), m1); cap.position.y = 0.19; flask.add(cap);
      mug.position.set(0, -0.08, -0.06); flask.position.set(0, -0.12, -0.05);
      c.handR.add(mug); c.handL.add(flask); r.props = [mug, flask];
    } else if (!on && r.props) { for (const p of r.props) p.removeFromParent(); r.props = null; }
  };
  // his look per fight: the same model with the damage pieces, a tinted suit and a few code extras
  r.extras = [];
  r.variant = (v) => {
    for (const e of r.extras) e.removeFromParent(); r.extras = [];
    r.dmg('fresh'); r.stutter = false; r.glitch = false;
    tint(1); const heart = (L.partsAll || {}).heart || []; for (const h of heart) h.scale.setScalar(1), h.position.set(0, 0, 0);
    if (v === 2) { // a steel patch welded over the fight-1 wound, the porthole plated over
      const m = new THREE.MeshStandardMaterial({ color: 0x6a7078, metalness: 0.8, roughness: 0.45 }), wb = new THREE.MeshStandardMaterial({ color: 0x8a6a4a, metalness: 0.5, roughness: 0.6 });
      const p = new THREE.Mesh(new THREE.CylinderGeometry(0.135, 0.14, 0.025, 10), m); p.rotation.x = Math.PI / 2; p.position.set(0.01, 0.45, -0.405); p.rotation.y = 0.2;
      const w = new THREE.Mesh(new THREE.TorusGeometry(0.135, 0.012, 5, 18), wb); w.position.set(0.01, 0.45, -0.418);
      c.spine.add(p, w); r.extras.push(p, w);
    }
    if (v === 3) { tint(0.55, 0x3a2a20); r.dmg('card_torn'); r.stutter = true; r.glitch = true; }
    if (v === 4) { // in tatters, plugged into the Master Clock: plate gone, the clock huge and cracked, cables out of his back
      tint(0.45, 0x2a1a14); r.dmg('plate_off'); r.dmg('cracked'); r.sparking = true; r.glitch = true;
      for (const h of heart) { h.scale.set(1.45, 1.45, 1.2); h.position.set(0, -0.19, 0.08); }
      const cm = new THREE.MeshStandardMaterial({ color: 0x2a2a30, roughness: 0.5 });
      for (let i = 0; i < 4; i++) {
        const curve = new THREE.CatmullRomCurve3([new THREE.Vector3((i - 1.5) * 0.06, 0.6, 0.28), new THREE.Vector3((i - 1.5) * 0.3, 1.4, 1.2), new THREE.Vector3((i - 1.5) * 0.8, 3.4, 2.6)]);
        const t = new THREE.Mesh(new THREE.TubeGeometry(curve, 16, 0.03, 6), cm); c.spine.add(t); r.extras.push(t);
      }
    }
    if (v === 'rehire') { // fresh from the spares: a REHIRED sticker on the lapel
      const cv = document.createElement('canvas'); cv.width = 64; cv.height = 32; const g = cv.getContext('2d');
      g.fillStyle = '#ffe14d'; g.fillRect(0, 0, 64, 32); g.fillStyle = '#ff3030'; g.font = 'bold 13px sans-serif'; g.fillText('REHIRED', 3, 21); g.strokeStyle = '#ff3030'; g.lineWidth = 3; g.strokeRect(1, 1, 62, 30);
      const tx = new THREE.CanvasTexture(cv); tx.colorSpace = THREE.SRGBColorSpace;
      const st = new THREE.Mesh(new THREE.PlaneGeometry(0.16, 0.08), new THREE.MeshStandardMaterial({ map: tx, roughness: 0.5 }));
      st.position.set(-0.2, 0.62, -0.31); st.rotation.set(0, Math.PI + 0.35, -0.15); c.spine.add(st); r.extras.push(st);
    }
    r.vis();
  };
  // the suit's colour per fight (his materials are cloned the first time, so other overtimes keep theirs)
  let own = false;
  const tint = (k, toward = 0x000000) => {
    if (!own) { if (k === 1) return; c.root.traverse((o) => { if (o.isMesh && o.material && /suit|pinstripe/i.test([].concat(o.material)[0].name || '')) { o.material = o.material.clone(); o.material.userData.c0 = o.material.color.clone(); } }); own = true; }
    c.root.traverse((o) => { if (o.isMesh && o.material && o.material.userData.c0) o.material.color.copy(o.material.userData.c0).lerp(new THREE.Color(toward), 1 - k); });
  };
  r.update = (dt, cam) => {
    // fight 3: he stutters like a skipping tape (the pose freezes for a beat), the visor crackles with static
    if (r.stutter && Math.random() < dt * 1.6) a.stepAcc = -(0.08 + Math.random() * 0.22);
    if (r.glitch && L.parts && L.parts.head) L.parts.head.traverse((o) => { if (o.isMesh && o.material && o.material.emissive && o.material.emissiveIntensity > 0.5) o.material.emissiveIntensity = Math.random() < 0.25 ? 0.2 : 4; });
    propsOn(!!(a.clip && a.clip.name === 'ot_coffee'));
    // marks inside the current clip
    const cl = a.clip;
    if (!cl || cl !== r.last) { r.last = cl; r.lastT = -1e-6; }
    if (cl && MARKS[cl.name]) { for (const [mt, mk] of MARKS[cl.name]) if (r.lastT < mt && cl.t >= mt) mark(r, mk, cl.name); r.lastT = cl.t; }
    // LOD
    if (cam && L.blender) { const far = cam.position.distanceTo(c.root.position) > 45 * (S / 2.5); if (far !== r.far) { r.far = far; r.vis(); } }
    else if (r.far == null) { r.far = false; r.vis(); }
    // steam: idle wisps, more when angry; the heart sparks when broken; the clock ticks
    r.anger = Math.max(0, r.anger - dt * 0.15);
    r.steamT -= dt;
    if (r.steamT <= 0 && !r.far) { r.steamT = 0.9 - r.anger * 0.6 + Math.random() * 0.5; for (const sx of [-1, 1]) puff(r.at.stack(sx), V(sx * 0.3, 2.2 + r.anger * 2, 0.4), 0.35 + r.anger * 0.3, 1.3); }
    if (r.sparking && Math.random() < dt * 9) burst(r, 3);
    if (r.show.dmgRip && Math.random() < dt * 4) puff(r.at.heart(), r.fwd().multiplyScalar(1.2).add(V(0, 1, 0)), 0.3, 1.0);
    r.tickT -= dt;
    if (r.tickT <= 0) { r.tickT = r.show.dmgRip ? 0.85 + Math.random() * 0.5 : 1.0; if (cam && cam.position.distanceTo(c.root.position) < 30) synth.tone('square', 2400, 1900, 0.025, 0.05, r.at.heart().toArray()); }
    for (const d of r.debris) if (!d.rest) {
      d.v.y -= 18 * dt; d.m.position.addScaledVector(d.v, dt); d.m.rotation.x += d.w.x * dt; d.m.rotation.z += d.w.z * dt;
      if (d.m.position.y <= d.y0 + 0.1) { d.m.position.y = d.y0 + 0.1; d.m.rotation.set(-Math.PI / 2, d.m.rotation.y, 0); d.rest = true; G.shake = Math.max(G.shake || 0, 0.5); synth.tone('square', 120, 50, 0.25, 0.4); }
    }
  };
  return r;
}
function burst(r, n) { const h = r.at.heart(), f = r.fwd(); for (let i = 0; i < n; i++) spark(h, V(f.x * 4 + (Math.random() - 0.5) * 5, 2 + Math.random() * 4, f.z * 4 + (Math.random() - 0.5) * 5)); }

function mark(r, mk, clip) {
  const a = r.a, f = r.fwd(), at = r.at.feet();
  const pos = at.toArray();
  if (mk === 'clack') { synth.tone('square', 900, 260, 0.05, 0.22, pos); synth.noise(0.04, 0.3, 'highpass', 2500, 4000, pos); }
  if (mk === 'fire') { const m = r.at.muzzle('R'); if (OT.fx) stapleShot(m, f.clone().add(V(0, -0.02, 0)).normalize()); synth.noise(0.25, 0.9, 'lowpass', 4000, 300, pos); synth.tone('sawtooth', 300, 80, 0.2, 0.4, pos); G.shake = Math.max(G.shake || 0, 0.35); }
  if (mk === 'fan') { const m = r.at.muzzle('R'); if (OT.fx) for (let i = -2; i <= 2; i++) stapleShot(m, f.clone().applyAxisAngle(V(0, 1, 0), i * 0.25).normalize()); synth.noise(0.4, 1, 'lowpass', 4000, 200, pos); }
  if (mk === 'watch' || mk === 'sip') synth.tone('sine', mk === 'watch' ? 2000 : 500, mk === 'watch' ? 2000 : 300, 0.05, 0.12, pos);
  if (mk === 'steam' || mk === 'roar') { r.anger = 1; for (const sx of [-1, 1]) for (let i = 0; i < 4; i++) puff(r.at.stack(sx), V(sx * (0.5 + Math.random()), 4 + Math.random() * 2, 0.5), 0.7, 1.8); for (let i = 0; i < 6; i++) puff(r.at.collar(), V((Math.random() - 0.5) * 3, 2, (Math.random() - 0.5) * 3), 0.6, 1.4); synth.noise(1.2, 0.7, 'bandpass', 1200, 3000, pos); }
  if (mk === 'roar') { synth.tone('sawtooth', 160, 55, 1.4, 0.55, pos); synth.tone('square', 2400, 2400, 0.6, 0.06, pos); G.shake = Math.max(G.shake || 0, 1.2); }
  if (mk === 'jump') synth.whoosh(0.5, 0.4, 300, 1200);
  if (mk === 'land' || mk === 'thud') { if (mk === 'land' && OT.fx) ring(at); synth.noise(0.9, 1, 'lowpass', 1500, 40, pos); synth.tone('sine', 90, 25, 0.8, 0.9, pos); G.shake = Math.max(G.shake || 0, mk === 'land' ? 1.6 : 0.8); for (let i = 0; i < 10; i++) puff(at.clone().add(V((Math.random() - 0.5) * 3, 0.2, (Math.random() - 0.5) * 3)), V((Math.random() - 0.5) * 6, 0.6, (Math.random() - 0.5) * 6), 0.7, 1.2); }
  if (mk === 'slotOpen' || mk === 'slotClose') synth.tone('sawtooth', mk === 'slotOpen' ? 80 : 300, mk === 'slotOpen' ? 300 : 80, 0.5, 0.25, pos);
  if (mk === 'grab') { synth.tone('square', 200, 1200, 0.15, 0.3, pos); synth.tone('square', 1200, 1200, 0.08, 0.3, pos, 0.18); } // ka-CHUNK: punched in
  if (mk === 'pour') synth.noise(1.2, 0.25, 'bandpass', 800, 1400, pos);
  if (mk === 'flinch') { synth.tone('square', 600, 200, 0.12, 0.3, pos); burst(r, 6); }
  if (mk === 'plate') r.dmg('plate_off');
  const ev = { type: 'ot', mark: mk, id: a.id, clip, at: pos };
  for (const l of listeners) { try { l(ev); } catch (e) { console.warn('ot listener', e); } }
}

// called every frame by the story host
export function otFrame(dt, cam) {
  for (const a of actors.values()) if (a.L && a.L.look === 'overtime') rigOf(a).update(dt, cam);
  for (const [id, r] of rigs) if (!actors.has(id) || actors.get(id) !== r.a) { r.restorePlate(); rigs.delete(id); }
  fxFrame(dt);
}
