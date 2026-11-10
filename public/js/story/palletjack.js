// PALLET JACK's rig on top of the story actor (docs/story/train/PALLET_JACK_MODEL.md): his clip set (pj_*, key poses in
// pj_clipdata.js, written by tools/blender/cast/pj_clips.py), the marks inside each clip (sounds, fx and the scene's
// cues hang off them), the machine in him (shin locks, stacks and their rain caps, the cocking collar, the gauge), his
// damage states, the vest coming off, the far LOD, steam. Presentation only: no damage happens here.
//   PJ.play(a, clip, { hold })                 clips: PJ.clips. one clip runs into the next without dropping to a stand
//   PJ.dmg(a, 'run_through' | 'armour_broken' | 'marrow_taken' | 'fresh')
//   PJ.vest(a, on)   PJ.arm(a, on) (the length of arm through him, when the scene wants its own)
//   PJ.set(a, { rig, cock, flap, vent, needle })   the machine by hand, 0..1 each (clips drive these while they play)
//   PJ.on((ev) => ...)   ev = { type: 'pj', mark, id, clip, at: [x, y, z] }
//   PJ.at(a, 'chest' | 'palmL' | 'fistAt' | 'ventAt' | 'stackTipL' | ...)  -> a world point (THREE.Vector3)
// The host can call pjFrame(dt, cam) every frame (like otFrame); until it does, this file ticks itself.
import * as THREE from 'three';
import { G } from '../ctx.js';
import { synth } from '../audio.js';
import { CLIPS, actors, play as playClip } from './actors.js';
import { faceLocked } from './looks.js';
import { PJ_DATA } from './pj_clipdata.js';

const clamp = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
const ss = (t) => { t = clamp(t); return t * t * (3 - 2 * t); };
const seg = (t, a, b) => ss((t - a) / (b - a));
const lerp = (a, b, k) => a + (b - a) * k;
const EASE = { ss, lin: (u) => u, in: (u) => u * u, out: (u) => 1 - (1 - u) * (1 - u), snap: (u) => 1 - (1 - u) ** 3 };
const XF = 0.22; // one pj clip into the next: this long, from wherever the last one had him

// ---------------------------------------------------------------- the clips
const D = PJ_DATA.clips, REST = PJ_DATA.rest;
const isAbs = (ch) => PJ_DATA.abs.some((p) => ch.startsWith(p));
// the channels a clip owns outright, always written (arms and hands are where the clip says, not where the walk left them)
const ABS_CH = ['arm', 'armL', 'foreR', 'foreL', 'handR', 'handL', 'neck'].flatMap((j) => ['x', 'y', 'z'].map((a) => j + '.' + a)).concat(['head.z', 'handR.py']);
const STICKY = (ch) => /^(handR|handL|neck)\.|^head\.z$/.test(ch); // nothing else resets these each frame: set them from their rest
const AXI = { x: 0, y: 1, z: 2 };
export function evalClip(name, t, out = {}) {
  const C = D[name], K = C.keys;
  if (C.loop) t %= C.loop;
  let i = 0; while (i < K.length - 2 && t >= K[i + 1].t) i++;
  const a = K[i], b = K[Math.min(i + 1, K.length - 1)];
  const u = EASE[b.e || 'ss'](b.t > a.t ? clamp((t - a.t) / (b.t - a.t)) : 1);
  for (const ch in a.p) out[ch] = a.p[ch] + ((b.p[ch] ?? 0) - a.p[ch]) * u;
  for (const ch in b.p) if (!(ch in a.p)) out[ch] = b.p[ch] * u;
  for (const [ch, amp, f, ph] of C.osc) out[ch] = (out[ch] ?? 0) + amp * Math.sin(t * f + ph);
  return out;
}
const stateOf = (c) => (c._pj ||= { name: null, t: 0, out: null, from: null, when: -1e9,
  rest: { 'head.z': c.head.rotation.z, neck: c.neck.rotation.clone(), handR: c.handR.rotation.clone(), handL: c.handL.rotation.clone(), handRy: c.handR.position.y } });
function applyPose(c, P, K, st) {
  for (const ch of ABS_CH) {
    const v = P[ch] ?? REST[ch] ?? 0, [j, a] = ch.split('.');
    if (ch === 'handR.py') { c.handR.position.y = st.rest.handRy + v * K; continue; }
    if (ch === 'head.z') { c.head.rotation.z = st.rest['head.z'] + v * K; continue; }
    if (STICKY(ch)) c[j].rotation[a] = st.rest[j][a] + v * K;
    else c[j].rotation[a] = lerp(c[j].rotation[a], v, K);
  }
  for (const ch in P) {
    if (isAbs(ch) || ch.startsWith('x.')) continue;
    const [j, a] = ch.split('.'), v = P[ch] * K;
    if (a.length === 2) c[j].position[a[1]] += v; else c[j].rotation[a] += v;
  }
}
const mkF = (name) => function f(c, t, k) {
  const st = stateOf(c), now = performance.now();
  if (st.name !== name || t < st.t - 1e-4) { st.from = st.out && now - st.when < 500 && st.name ? st.out : null; st.name = name; } // a new play: carry on from the last pj pose
  st.t = t; st.when = now;
  let P = evalClip(name, t), K = k;
  if (st.from && t < XF) {
    const u = ss(t / XF), Q = {};
    for (const ch in P) Q[ch] = lerp(st.from[ch] ?? REST[ch] ?? 0, P[ch], u);
    for (const ch in st.from) if (!(ch in P)) Q[ch] = lerp(st.from[ch], REST[ch] ?? 0, u);
    P = Q; K = 1;
  } else st.from = null;
  st.out = P; st.k = K;
  applyPose(c, P, K, st);
};
export const PJ_CLIPS = {};
for (const name in D) PJ_CLIPS[name] = { len: D[name].len ?? 9e9, f: mkF(name) };
export const MARKS = Object.fromEntries(Object.entries(D).map(([k, v]) => [k, v.marks]));
// what follows a clip that ends on its own (a punch, a stagger): back to the stance he was in
const NEXT = { pj_rocket_punch: 'pj_fight_idle', pj_stagger: 'pj_fight_idle' };
let registered = false;
export function pjRegister() { if (registered) return; registered = true; Object.assign(CLIPS, PJ_CLIPS); } // (called when the first Jack is built: actors.js is ready by then)

// ---------------------------------------------------------------- what the states show (the model's meta says the same)
const STATES = {
  fresh: { on: [], off: [] },
  run_through: { on: ['dmgWound', 'dmgArm', 'dmgBoilerSplit'], off: [] },
  armour_broken: { on: ['dmgWound', 'dmgArm', 'dmgBoilerSplit', 'dmgCollar', 'dmgLockL', 'dmgLockR', 'dmgStackL', 'dmgStackR'], off: ['collar', 'lockL', 'lockR', 'stackL', 'stackR', 'flapL', 'flapR'] },
  marrow_taken: { on: ['dmgWound', 'dmgArm', 'dmgMarrow', 'dmgCollar', 'dmgLockL', 'dmgLockR', 'dmgStackL', 'dmgStackR'], off: ['boiler', 'fire', 'collar', 'lockL', 'lockR', 'stackL', 'stackR', 'flapL', 'flapR'] },
};
// the moving pieces: pivot and axis in their joint's frame. these are the model's own numbers (c_pallet_jack.parts.json
// `moving`), copied here so nothing waits on a fetch; the file is read too and wins if the model has changed
const MOVING = {
  stackL: { axis: [-0.128, 0.979, 0.159] }, stackR: { axis: [0.128, 0.979, 0.159] }, flapL: { axis: [0.99, 0.13, 0] }, flapR: { axis: [0.99, -0.13, 0] },
  lockL: { axis: [0, 0, 1], shut: -2.1916 }, lockR: { axis: [0, 0, 1], shut: 2.1916 }, cock: { axis: [0, 1, 0] }, needle: { axis: [0, -0.5, -0.86] }, valve: { axis: [0, 1, 0] },
};
const RIG = { stackRise: 0.07, flapOpen: 1.2, cockPull: 0.04, punchReach: 0.24 };
let META = null;
fetch('/models/cast/c_pallet_jack.parts.json').then((r) => (r.ok ? r.json() : null)).then((j) => {
  if (!j) return; META = j;
  for (const k in j.moving || {}) { MOVING[k] ||= {}; if (j.moving[k].axis) MOVING[k].axis = j.moving[k].axis; if (j.moving[k].shut != null) MOVING[k].shut = j.moving[k].shut; }
  Object.assign(RIG, j.rig || {});
}).catch(() => {});

const listeners = new Set();
export const PJ = {
  fx: true, auto: true, clips: Object.keys(D), data: PJ_DATA,
  on(f) { listeners.add(f); return () => listeners.delete(f); },
  play(a, clip, opts = {}) { pjRegister(); playClip(a, clip, opts); },
  dmg(a, state) { rigOf(a).dmg(state); },
  vest(a, on) { const r = rigOf(a); r.vestOn = !!on; r.vis(); },
  arm(a, on) { const r = rigOf(a); r.armOn = !!on; r.vis(); },
  set(a, v) { const r = rigOf(a); Object.assign(r.x, v); r.pin = { ...(r.pin || {}), ...v }; r.machine(0); },
  at(a, name) { const r = rigOf(a); return r.at(name); },
  rig: (a) => rigOf(a),
  meta: () => META,
};
if (typeof window !== 'undefined') window.JF_PJ = PJ; // (tests and the scene's devtools)

// ---------------------------------------------------------------- steam and sparks (one small pool)
const FX = [];
const geoBall = new THREE.SphereGeometry(1, 8, 6), geoBox = new THREE.BoxGeometry(1, 1, 1);
const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const tv = V(), tq = new THREE.Quaternion(), tq2 = new THREE.Quaternion();
function puff(p, v, size = 0.3, life = 1.2, color = 0xf4f4f8, op = 0.5) {
  if (!G.scene) return;
  const m = new THREE.Mesh(geoBall, new THREE.MeshBasicMaterial({ color, transparent: true, opacity: op, depthWrite: false })); m.position.copy(p); m.scale.setScalar(size * 0.4); G.scene.add(m);
  FX.push({ m, v: v.clone(), life, t: 0, kind: 'steam', size, op });
}
const sparkMat = new THREE.MeshBasicMaterial({ color: 0xffb040 });
function spark(p, v, life = 0.45) { if (!G.scene) return; const m = new THREE.Mesh(geoBox, sparkMat); m.position.copy(p); m.scale.set(0.03, 0.03, 0.12); G.scene.add(m); FX.push({ m, v: v.clone(), life, t: 0, kind: 'spark' }); }
function fxFrame(dt) {
  for (let i = FX.length - 1; i >= 0; i--) {
    const f = FX[i]; f.t += dt; const u = f.t / f.life;
    if (u >= 1) { f.m.removeFromParent(); if (f.kind === 'steam') f.m.material.dispose(); FX.splice(i, 1); continue; }
    f.m.position.addScaledVector(f.v, dt);
    if (f.kind === 'steam') { f.v.multiplyScalar(1 - dt * 1.4); f.v.y += dt * 0.7; f.m.scale.setScalar(f.size * (0.4 + u * 1.5)); f.m.material.opacity = f.op * (1 - u); }
    else { f.v.y -= 12 * dt; f.m.lookAt(tv.copy(f.m.position).add(f.v)); }
  }
}
const RED = 0xff5a4a;

// ---------------------------------------------------------------- one jack
const rigs = new Map();
function rigOf(a) {
  let r = rigs.get(a.id);
  if (r && r.a === a) return r;
  r = makeRig(a); rigs.set(a.id, r); kick(); return r;
}
function makeRig(a) {
  const L = a.L, c = a.ch, S = c.root.scale.x;
  const r = { a, last: null, lastT: -1, far: null, state: 'fresh', show: {}, hide: {}, vestOn: true, armOn: true, x: { rig: 0, cock: 0, flap: 0, vent: 0, needle: 0.3 }, pin: null,
    steamT: 0, ventT: 0, t: 0, mov: {}, props: {}, faceI: -1 };
  // the moving pieces: each tagged group's meshes sit at their pivot (the model's node origin). hang them off a pivot
  // group so they turn and slide about it, in their joint's frame
  for (const tag of Object.keys(MOVING)) {
    const tg = L.parts && L.parts[tag];
    if (!tg || !tg.userData.blender || !tg.children.length) continue;
    const m0 = tg.children[0], piv = new THREE.Group(); piv.name = 'pj_piv_' + tag;
    piv.position.copy(m0.position); piv.quaternion.copy(m0.quaternion); piv.scale.copy(m0.scale);
    for (const m of [...tg.children]) { m.position.set(0, 0, 0); m.quaternion.identity(); m.scale.set(1, 1, 1); piv.add(m); }
    tg.add(piv); r.mov[tag] = { piv, p0: piv.position.clone(), q0: piv.quaternion.clone() };
  }
  const turn = (tag, ang) => { const m = r.mov[tag]; if (!m) return; const ax = MOVING[tag].axis; m.piv.quaternion.copy(tq.setFromAxisAngle(tv.set(ax[0], ax[1], ax[2]).normalize(), ang)).multiply(m.q0); };
  const slide = (tag, d) => { const m = r.mov[tag]; if (!m) return; const ax = MOVING[tag].axis; m.piv.position.copy(m.p0).addScaledVector(tv.set(ax[0], ax[1], ax[2]).normalize(), d); };
  // world spots: the markers the look carries (joint space), or a joint
  r.at = (name) => { const m = L.parts && L.parts[name]; return m ? m.getWorldPosition(V()) : c[name] ? c[name].getWorldPosition(V()) : c.spine.getWorldPosition(V()); };
  r.fwd = () => V(-Math.sin(a.yaw || 0), 0, -Math.cos(a.yaw || 0));
  // ---- what shows: far LOD or the model, the damage pieces, the vest
  r.vis = () => {
    const far = !!r.far, all = L.partsAll || {};
    if (L.blender) for (const jn of ['body', 'legL', 'legR', 'kneeL', 'kneeR', 'spine', 'neck', 'head', 'armL', 'arm', 'foreL', 'foreR', 'handL', 'handR']) {
      const J = c[jn]; if (!J) continue;
      for (const ch of J.children) {
        if (ch.name === 'ot_lod') ch.visible = far;
        else if (ch.isMesh && !(L.face && ch === L.face.root)) ch.visible = !far;
      }
    }
    const st = STATES[r.state] || STATES.fresh;
    for (const [k, gs] of Object.entries(all)) {
      if (k === 'lod' || k === 'headJoint' || !gs[0] || (!gs[0].userData.blender && !gs[0].userData.codeOnly)) continue; // (markers have nothing to show)
      let on;
      if (k === 'dmgVestFar') on = far && r.vestOn;
      else if (k.startsWith('dmg')) on = !far && st.on.includes(k) && (k !== 'dmgArm' || r.armOn);
      else if (k === 'vest') on = !far && r.vestOn;
      else on = !far && !st.off.includes(k);
      for (const gp of gs) gp.visible = on;
    }
    if (L.face) L.face.root.visible = !far;
  };
  r.dmg = (state) => {
    if (!STATES[state]) return;
    const was = r.state; r.state = state;
    if (state !== was && PJ.fx && G.scene) {
      if (state === 'run_through') { for (let i = 0; i < 14; i++) puff(r.at('ventAt'), r.fwd().multiplyScalar(-1.5 - Math.random() * 2).add(V((Math.random() - 0.5) * 2, 1 + Math.random() * 2, 0)), 0.5, 1.4, RED, 0.6); }
      if (state === 'armour_broken') { for (const k of ['weldAt', 'stackTipL', 'stackTipR']) for (let i = 0; i < 8; i++) spark(r.at(k), V((Math.random() - 0.5) * 5, 1 + Math.random() * 4, (Math.random() - 0.5) * 5)); }
    }
    if (state === 'armour_broken' || state === 'marrow_taken') { r.x.rig = 0; r.x.flap = 0; r.pin = null; }
    glow(); r.vis();
  };
  // ---- the lit bits: his own copies of the glow materials (fire door, level glass, cracks), driven by the boiler's state
  let lit = null;
  const glow = () => {
    if (!L.blender) return;
    if (!lit) { lit = []; c.root.traverse((o) => { if (o.isMesh && o.material && /pj_(glow|marrow|core)/.test(o.material.name || '')) { o.material = o.material.clone(); o.material.userData.e0 = o.material.emissiveIntensity; lit.push(o.material); } }); }
  };
  r.lights = (t) => {
    if (!lit) glow();
    if (!lit) return;
    const hurt = r.state === 'run_through' || r.state === 'armour_broken', dead = r.state === 'marrow_taken';
    for (const m of lit) {
      const e0 = m.userData.e0 ?? 1;
      if (/pj_glow/.test(m.name)) m.emissiveIntensity = dead ? 0.05 : e0 * (hurt ? 0.5 + 0.5 * Math.abs(Math.sin(t * 9) * Math.sin(t * 2.3)) : 0.75 + 0.25 * Math.sin(t * 2.1) + r.x.rig * 0.6);
      else if (/pj_core/.test(m.name)) m.emissiveIntensity = dead ? 0.1 : e0 * (0.6 + 0.4 * Math.sin(t * 13) * Math.sin(t * 3.1));
      else m.emissiveIntensity = e0 * (dead ? 0.55 + 0.25 * Math.sin(t * 1.3) : 1);
    }
  };
  // ---- the machine: shin locks, stacks and caps, the cocking collar, the gauge needle
  r.machine = (t) => {
    const x = r.x;
    turn('lockL', (MOVING.lockL.shut ?? -2.19) * seg(x.rig, 0.02, 0.35)); turn('lockR', (MOVING.lockR.shut ?? 2.19) * seg(x.rig, 0.36, 0.7));
    const up = seg(x.rig, 0.7, 1) * RIG.stackRise; slide('stackL', up); slide('stackR', up);
    for (const s of ['L', 'R']) {
      const m = r.mov['flap' + s]; if (!m) continue;
      const open = RIG.flapOpen * Math.max(x.flap, 0) + (x.vent > 0.05 ? Math.abs(Math.sin(t * 31 + (s === 'L' ? 0 : 1.3))) * 0.25 * x.vent : 0) + (x.flap < 0.05 && r.puffK > 0 ? r.puffK * 0.5 : 0);
      const ax = MOVING['flap' + s].axis, sm = r.mov['stack' + s];
      m.piv.quaternion.copy(tq.setFromAxisAngle(tv.set(ax[0], ax[1], ax[2]).normalize(), open)).multiply(m.q0);
      m.piv.position.copy(m.p0); if (sm) m.piv.position.add(tv.copy(sm.piv.position).sub(sm.p0)); // (the cap rides up with its stack)
    }
    slide('cock', RIG.cockPull * x.cock);
    const hurt = r.state !== 'fresh';
    turn('needle', lerp(-1.9, 1.9, clamp(x.needle + x.rig * 0.3 + (hurt && r.state !== 'marrow_taken' ? 0.38 + Math.sin(t * 23) * 0.03 : 0) - (r.state === 'marrow_taken' ? 1 : 0))));
  };
  // ---- props he only has for one clip: the pan and spoon, the vest in his hands
  const propsOn = (key, on, make) => { if (on && !r.props[key]) r.props[key] = make(); else if (!on && r.props[key]) { for (const p of r.props[key]) p.removeFromParent(); delete r.props[key]; } };
  const mkPan = () => {
    const steel = new THREE.MeshStandardMaterial({ color: 0x8a9098, roughness: 0.4, metalness: 0.5, side: THREE.DoubleSide }), soup = new THREE.MeshStandardMaterial({ color: 0xd8862a, roughness: 0.3 }), dark = new THREE.MeshStandardMaterial({ color: 0x1e1e22, roughness: 0.6 });
    const pan = new THREE.Group(); pan.name = 'pj_pan';
    pan.add(new THREE.Mesh(new THREE.LatheGeometry([[0, 0], [0.085, 0], [0.1, 0.015], [0.108, 0.075], [0.112, 0.078]].map(([x, y]) => new THREE.Vector2(x, y)), 14), steel));
    const top = new THREE.Mesh(new THREE.CircleGeometry(0.101, 14), soup); top.rotation.x = -Math.PI / 2; top.position.y = 0.05; pan.add(top);
    const hd = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.2, 6), dark); hd.rotation.z = Math.PI / 2; hd.position.set(0.2, 0.068, 0); pan.add(hd);
    c.handR.add(pan);
    const spoon = new THREE.Group(); spoon.name = 'pj_spoon';
    const sh = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.007, 0.2, 6), steel); sh.position.y = -0.22; spoon.add(sh);
    const bowl = new THREE.Mesh(new THREE.SphereGeometry(0.026, 8, 6), steel); bowl.scale.set(1, 1.3, 0.35); bowl.position.y = -0.335; spoon.add(bowl);
    const drop = new THREE.Mesh(new THREE.SphereGeometry(0.02, 8, 6), soup); drop.scale.set(1, 1.2, 0.3); drop.position.set(0, -0.335, 0.006); spoon.add(drop); spoon.userData.drop = drop;
    spoon.position.set(0, 0, 0.035); c.handL.add(spoon);
    return [pan, spoon];
  };
  const mkVest = () => {
    const g = new THREE.Group(); g.name = 'pj_vest_held';
    const y = new THREE.MeshStandardMaterial({ color: 0xd6ee2a, roughness: 0.85 }), s = new THREE.MeshStandardMaterial({ color: 0xc4cad0, roughness: 0.4 });
    const b = new THREE.Mesh(new THREE.BoxGeometry(0.52, 0.46, 0.05), y); g.add(b);
    for (const yy of [-0.06, -0.15]) { const st = new THREE.Mesh(new THREE.BoxGeometry(0.53, 0.04, 0.055), s); st.position.y = yy; g.add(st); }
    c.spine.add(g); return [g];
  };
  r.update = (dt, cam) => {
    r.t += dt;
    const cl = a.clip, pj = cl && D[cl.name] ? cl : null;
    // nothing of his playing: put back what only his clips move (hands, neck, the head's tilt)
    if (!pj && c._pj && c._pj.name) { const st = c._pj; c.handR.rotation.copy(st.rest.handR); c.handL.rotation.copy(st.rest.handL); c.neck.rotation.copy(st.rest.neck); c.head.rotation.z = st.rest['head.z']; c.handR.position.y = st.rest.handRy; if (performance.now() - st.when > 500) st.name = null; }
    // marks and faces inside the clip
    if (cl !== r.last) { r.last = cl; r.lastT = -1e-6; r.faceI = -1; }
    if (pj) {
      const C = D[cl.name], t = C.loop ? cl.t % C.loop : cl.t;
      if (C.loop && t < r.lastT) r.lastT = -1e-6; // (round again)
      for (const [mt, mk] of C.marks) if (r.lastT < mt && t >= mt) mark(r, mk, cl.name);
      r.lastT = t;
      if (a.face && !faceLocked(a.face)) { let fi = -1; for (let i = 0; i < C.face.length; i++) if (cl.t >= C.face[i][0]) fi = i; if (fi !== r.faceI && fi >= 0) { r.faceI = fi; a.face.set(C.face[fi][1]); } }
      // the machine follows the clip (eased, so a cut between clips doesn't snap a stack)
      const P = evalClip(cl.name, cl.t), kk = dt > 0 ? Math.min(1, dt * 18) : 1;
      for (const k of ['rig', 'cock', 'flap', 'vent']) { const tgt = (P['x.' + k] ?? 0); r.x[k] = r.pin && k in r.pin ? r.pin[k] : lerp(r.x[k], tgt, kk); }
      // a clip that ends on its own hands over before it fades (back to the stance, the hurt one if he's hurt)
      if (cl.len < 1e8 && NEXT[cl.name] && cl.t >= cl.len - 0.27) PJ.play(a, r.state === 'fresh' ? NEXT[cl.name] : 'pj_fight_idle_hurt');
    }
    r.puffK = Math.max(0, (r.puffK || 0) - dt * 3);
    r.machine(r.t); r.lights(r.t);
    propsOn('pan', !!(pj && cl.name === 'pj_idle_eating'), mkPan);
    propsOn('vest', !!(pj && cl.name === 'pj_kneel_vest' && cl.t >= 1.75 && cl.t < 3.7), mkVest);
    if (r.props.pan) { // the pan stays level in his fist; the spoon's load comes and goes
      const [pan, spoon] = r.props.pan; c.handR.getWorldQuaternion(tq).invert(); c.root.getWorldQuaternion(tq2); pan.quaternion.copy(tq).multiply(tq2);
      pan.position.set(0, -0.125, 0.03).add(tv.set(-0.2, -0.068, 0).applyQuaternion(pan.quaternion));
      const t = cl.t % D.pj_idle_eating.loop; spoon.userData.drop.visible = t > 0.7 && t < 1.95;
      spoon.rotation.set(-0.5, 0, 0);
    }
    if (r.props.vest) { // bunched between his hands while it's off him and not yet on the child
      const [g] = r.props.vest, pa = c.handR.getWorldPosition(V()), pb = c.handL.getWorldPosition(tv);
      pa.add(pb).multiplyScalar(0.5); pa.y -= 0.12 * S; c.spine.worldToLocal(pa); g.position.copy(pa);
      c.spine.getWorldQuaternion(tq).invert(); c.root.getWorldQuaternion(tq2); g.quaternion.copy(tq).multiply(tq2);
    }
    // LOD
    if (cam && L.blender) { const far = cam.position.distanceTo(c.root.position) > 28 * (S / 1.18); if (far !== r.far) { r.far = far; r.vis(); } }
    else if (r.far == null) { r.far = false; r.vis(); }
    if (!PJ.fx || r.far || !G.scene || dt <= 0) return;
    // steam: the boiler ticks over (a wisp, a cap lifts); it works harder with the rig up; run through, it vents red
    const hurt = r.state === 'run_through' || r.state === 'armour_broken';
    r.steamT -= dt;
    if (r.steamT <= 0 && r.state !== 'marrow_taken') {
      r.steamT = (hurt ? 0.35 : 1.6 - r.x.rig * 1.1) + Math.random() * 0.5; r.puffK = 1;
      const bent = r.state === 'armour_broken';
      for (const s of ['L', 'R']) { const p = r.at((bent ? 'stackTipBent' : 'stackTip') + s); puff(p, V((s === 'L' ? -0.2 : 0.2), 1.2 + r.x.rig, 0.3), (0.18 + r.x.rig * 0.14) * S, 1.1, hurt ? RED : 0xf4f4f8, hurt ? 0.4 : 0.42); }
    }
    r.ventT -= dt;
    const vent = Math.max(r.x.vent, hurt ? 0.45 : 0);
    if (vent > 0.02 && r.ventT <= 0) {
      r.ventT = 0.16 - vent * 0.1;
      const from = r.state === 'fresh' ? r.at('elbowAt') : r.at('ventAt'), dir = r.state === 'fresh' ? V(0, 1.5, 0).addScaledVector(r.fwd(), -2.5) : r.fwd().multiplyScalar(-2 - Math.random() * 2).add(V((Math.random() - 0.5) * 1.5, 0.8 + Math.random(), 0));
      puff(from, dir, (0.2 + vent * 0.25) * S, 0.9, r.state === 'fresh' ? 0xf4f4f8 : RED, 0.5);
    }
  };
  r.vis(); r.machine(0);
  return r;
}

function mark(r, mk, clip) {
  const a = r.a, pos = [a.pos ? a.pos[0] : 0, a.pos ? a.pos[1] : 0, a.pos ? a.pos[2] : 0], sh = (k) => { G.shake = Math.max(G.shake || 0, k); };
  const fx = PJ.fx && G.scene && !r.far;
  try {
    if (mk === 'lockL' || mk === 'lockR') { synth.tone('square', 700, 180, 0.06, 0.3, pos); synth.noise(0.05, 0.35, 'highpass', 2000, 5000, pos); }
    if (mk === 'stacks') { synth.noise(0.7, 0.45, 'bandpass', 900, 2600, pos); synth.tone('sawtooth', 90, 180, 0.4, 0.2, pos); if (fx) for (const s of ['L', 'R']) for (let i = 0; i < 4; i++) puff(r.at('stackTip' + s), V((Math.random() - 0.5) * 0.8, 2.5 + Math.random() * 1.5, 0.3), 0.4, 1.4); }
    if (mk === 'cock') { synth.tone('square', 240, 900, 0.07, 0.3, pos); synth.tone('square', 900, 300, 0.05, 0.3, pos, 0.09); }
    if (mk === 'fire') { synth.noise(0.35, 0.9, 'lowpass', 3500, 200, pos); synth.tone('sawtooth', 220, 50, 0.3, 0.5, pos); sh(0.5); if (fx) for (let i = 0; i < 10; i++) puff(r.at('elbowAt'), V(0, 1.5 + Math.random(), 0).addScaledVector(r.fwd(), -3 - Math.random() * 3), 0.5, 0.9); }
    if (mk === 'hit' && clip === 'pj_rocket_punch') { synth.tone('sine', 110, 40, 0.25, 0.8, pos); if (fx) for (let i = 0; i < 8; i++) spark(r.at('fistAt'), V((Math.random() - 0.5) * 6, Math.random() * 4, (Math.random() - 0.5) * 6)); }
    if (mk === 'hit' && clip !== 'pj_rocket_punch') { synth.tone('square', 300, 90, 0.14, 0.4, pos); synth.noise(0.2, 0.6, 'lowpass', 1800, 200, pos); sh(0.6); }
    if (mk === 'up') synth.tone('square', 400, 220, 0.05, 0.25, pos);
    if (mk === 'in') { synth.noise(0.5, 1, 'lowpass', 2200, 80, pos); synth.tone('sine', 70, 30, 0.6, 0.9, pos); sh(1.2); r.dmg('run_through'); }
    if (mk === 'try1') { synth.tone('sawtooth', 160, 120, 0.5, 0.3, pos); synth.noise(0.3, 0.3, 'bandpass', 500, 900, pos); }
    if (mk === 'snap') { synth.noise(0.18, 1, 'highpass', 800, 3000, pos); synth.tone('square', 520, 60, 0.2, 0.7, pos); sh(0.9); }
    if (mk === 'land' || mk === 'down') { synth.noise(0.5, 0.9, 'lowpass', 1200, 60, pos); synth.tone('sine', 80, 30, 0.5, 0.8, pos); sh(mk === 'land' ? 0.9 : 0.7); }
    if (mk === 'foot' || mk === 'knee') synth.tone('sine', 120, 60, 0.12, 0.35, pos);
    if (mk === 'armour') { synth.noise(0.9, 1, 'bandpass', 1500, 300, pos); synth.tone('sawtooth', 400, 40, 0.9, 0.6, pos); synth.tone('square', 1800, 200, 0.12, 0.4, pos); sh(1.4); r.dmg('armour_broken'); }
    if (mk === 'fridge') synth.tone('square', 140, 70, 0.18, 0.5, pos);
    if (mk === 'vent') { synth.noise(0.6, 0.25, 'bandpass', 1400, 600, pos); }
    if (mk === 'breath') synth.noise(1.6, 0.14, 'bandpass', 500, 180, pos);
    if (mk === 'hand_down') synth.tone('sine', 150, 90, 0.08, 0.2, pos);
    if (mk === 'vestOff') { r.vestOn = false; r.vis(); synth.noise(0.2, 0.12, 'highpass', 1500, 3000, pos); }
    if (mk === 'eat') synth.tone('sine', 520, 380, 0.05, 0.08, pos);
  } catch (e) { /* (no audio in a test page) */ }
  const ev = { type: 'pj', mark: mk, id: a.id, clip, at: pos };
  for (const l of listeners) { try { l(ev); } catch (e) { console.warn('pj listener', e); } }
}

// called every frame by the story host (or by this file's own tick until it is)
let hosted = 0, ticking = false, lastTick = 0;
export function pjFrame(dt, cam) { hosted = performance.now(); frame(dt, cam); }
function frame(dt, cam) {
  for (const a of actors.values()) if (a.L && a.L.look === 'pallet_jack') rigOf(a).update(dt, cam);
  for (const [id, r] of rigs) if (!r.manual && (!actors.has(id) || actors.get(id) !== r.a)) { for (const k in r.props) for (const p of r.props[k]) p.removeFromParent(); rigs.delete(id); }
  fxFrame(dt);
}
function kick() {
  if (ticking || typeof requestAnimationFrame === 'undefined') return;
  ticking = true; lastTick = performance.now();
  const tick = () => {
    const now = performance.now(), dt = Math.min(0.1, (now - lastTick) / 1000); lastTick = now;
    if (PJ.auto && now - hosted > 500) frame(dt, G.camera || null); // (the host isn't calling pjFrame: do it here)
    if (rigs.size || FX.length) requestAnimationFrame(tick); else ticking = false;
  };
  requestAnimationFrame(tick);
}
