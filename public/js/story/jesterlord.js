// THE HEADLINER's rig on top of the story actor (docs/story/cast/JESTER_LORD_MODEL.md): his clip set (jl_*, key poses
// in jl_clipdata.js, written by tools/blender/cast/jl_clips.py), the marks inside each clip, the scuttle laid over
// whatever he is doing whenever he moves (run by distance, so the feet don't slide), every bell hanging straight down
// and swinging when its foot moves, the web he hangs from, the stump when a leg is off, the far LOD.
// Presentation only: nothing here does damage.
//   JL.play(a, clip)            clips: JL.clips. one clip runs into the next; a clip that ends goes back to jl_idle
//   JL.on((ev) => ...)          ev = { type: 'jl', mark, id, clip, at: [x, y, z] }
//   JL.at(a, 'eyeAt' | 'noseTip' | 'hatTipR' | 'marotteAt' | 'stumpAt' | 'femRB' | ...) -> a world point (THREE.Vector3)
// He is always in one of his clips (a spawned jester_lord with nothing playing is put into jl_idle), so the clip owns
// all of him: every joint is set to its rest turn x the clip's delta.
// Dev: ?story=1&jesterlord=1 stands him 7 m in front of you and runs the whole set on a loop with captions (no damage).
import * as THREE from 'three';
import { G } from '../ctx.js';
import { ME } from '../player.js';
import { CLIPS, actors, play as playClip, spawnActor, walkTo, dropTo } from './actors.js';
import { faceLocked } from './looks.js';
import { JL_DATA } from './jl_clipdata.js';

const clamp = (x, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
const ss = (t) => { t = clamp(t); return t * t * (3 - 2 * t); };
const lerp = (a, b, k) => a + (b - a) * k;
const EASE = { ss, lin: (u) => u, in: (u) => u * u, out: (u) => 1 - (1 - u) * (1 - u), snap: (u) => 1 - (1 - u) ** 3, back: (u) => 1 + 2.70158 * (u - 1) ** 3 + 1.70158 * (u - 1) ** 2 };
const XF = 0.3; // one clip into the next: this long, from wherever the last one had him

// ---------------------------------------------------------------- the clips (the same sums as jl_clips.py evaluate())
const D = JL_DATA.clips, LAG = JL_DATA.lag || [], BELLS = new Set(JL_DATA.bells);
const RIG = JL_DATA.rig.map(([n, par, p, r]) => ({ n, par, p: new THREE.Vector3(...p), q: new THREE.Quaternion().setFromEuler(new THREE.Euler(...r)) }));
const LEG_OFF = JL_DATA.legOff.joints[0]; // (the leg the clip set takes off: femRB)
function poseAt(C, t, out) {
  const K = C.keys;
  if (C.loop) t = ((t % C.loop) + C.loop) % C.loop;
  if (t < 0) t = 0;
  let i = 0; while (i < K.length - 2 && t >= K[i + 1].t) i++;
  const a = K[i], b = K[Math.min(i + 1, K.length - 1)];
  const u = EASE[b.e || 'ss'](b.t > a.t ? clamp((t - a.t) / (b.t - a.t)) : 1);
  for (const ch in a.p) out[ch] = a.p[ch] + ((b.p[ch] ?? 0) - a.p[ch]) * u;
  for (const ch in b.p) if (!(ch in a.p)) out[ch] = b.p[ch] * u;
  return out;
}
export function evalClip(name, t, out = {}) {
  const C = D[name]; poseAt(C, t, out);
  if (!C.nolag) for (const [pre, lag] of LAG) {
    if (!(lag > 0)) continue;
    let late = null;
    for (const ch in out) if (ch.startsWith(pre)) { late ||= poseAt(C, t - lag, {}); out[ch] = late[ch] ?? 0; }
  }
  for (const [ch, amp, f, ph] of C.osc) out[ch] = (out[ch] ?? 0) + amp * Math.sin(t * f + ph);
  return out;
}
export const durationOf = (name) => D[name].len || D[name].loop || D[name].keys[D[name].keys.length - 1].t;
const ends = (name) => !!D[name].len;
const NEXT = { jl_leg_back: 'jl_idle', jl_drop: 'jl_idle' };
// what the scuttle owns when he moves (the legs and the body's bob), and what it only adds to
const WALK_SET = new Set(['body.py', 'body.z', 'body.x', ...JL_DATA.rig.filter((e) => /^(fem|tib|foot)[RL][A-D]$/.test(e[0])).flatMap((e) => ['.x', '.y', '.z'].map((a) => e[0] + a))]);
const WALK_ADD = ['abdo.x', 'abdo.y', 'spine.z', 'head.z', 'hatR.x', 'hatL.x', 'hatRb.x', 'hatLb.x', 'collar.x', 'marotte.x'];

const rigs = new Map(), byCh = new WeakMap(), listeners = new Set();
const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const e3 = new THREE.Euler(), q3 = new THREE.Quaternion(), q4 = new THREE.Quaternion(), v3 = new THREE.Vector3();
function rigOf(a) {
  let r = rigs.get(a.id);
  if (r && r.a === a) return r;
  r = makeRig(a); rigs.set(a.id, r); byCh.set(a.ch, r); kick(); return r;
}
function makeRig(a) {
  const L = a.L, c = a.ch;
  if (L.blender && L.face) { // (the model has his own eyes, lids, brows and dummy jaw: the code face goes)
    for (const e of L.face.eyes) e.piv.visible = false;
    for (const l of L.face.lids) if (l) { l.top.visible = false; l.bot.visible = false; }
    if (L.face.mouth) L.face.mouth.visible = false;
    for (const b of L.face.brows || []) if (b) b.visible = false;
  }
  const r = { a, c, name: null, t: 0, out: null, from: null, fromT: 0, markI: 0, faceI: -1, gaitK: 0, walkT: 0, last: null, now: 0, far: null, bells: {}, web: null, stumpOn: false };
  r.at = (name) => { const m = L.parts && L.parts[name]; return m ? m.getWorldPosition(V()) : c[name] ? c[name].getWorldPosition(V()) : c.head.getWorldPosition(V()); };
  r.vis = (far) => {
    if (r.far === far || !L.blender) return; r.far = far;
    for (const { n } of RIG) {
      const J = c[n]; if (!J) continue;
      for (const ch of J.children) {
        if (ch.name === 'ot_lod') ch.visible = far;
        else if ((ch.isMesh && !(L.face && ch === L.face.root)) || ch.userData.blender) ch.visible = !far;
      }
    }
    if (L.face) L.face.root.visible = !far;
    stump(r, r.stumpOn);
  };
  return r;
}
function stump(r, on) {
  r.stumpOn = on; const s = r.a.L.parts && r.a.L.parts.dmgStump;
  if (s) s.visible = on && !r.far;
}
function apply(r, P) {
  const c = r.c;
  for (const { n, p, q } of RIG) {
    const o = c[n]; if (!o) continue;
    e3.set(P[n + '.x'] ?? 0, P[n + '.y'] ?? 0, P[n + '.z'] ?? 0);
    o.quaternion.copy(q).multiply(q3.setFromEuler(e3));
    o.position.set(p.x + (P[n + '.px'] ?? 0), p.y + (P[n + '.py'] ?? 0), p.z + (P[n + '.pz'] ?? 0));
  }
}
// every bell hangs straight down from its spot and swings when the spot is shoved about (a damped pendulum), plus
// what the clip gives it
function dangle(r, P, dt) {
  const c = r.c; c.root.updateMatrixWorld(true);
  for (const n of BELLS) {
    const o = c[n]; if (!o) continue;
    const s = (r.bells[n] ||= { p: null, v: V(), ax: 0, az: 0, wx: 0, wz: 0 });
    o.getWorldPosition(v3);
    if (s.p && dt > 0) {
      const v = v3.clone().sub(s.p).divideScalar(dt), acc = v.clone().sub(s.v).divideScalar(dt); s.v.copy(v);
      const tx = clamp(acc.z * 0.035, -0.9, 0.9), tz = clamp(-acc.x * 0.035, -0.9, 0.9);
      const k = 60, d = 7; // (stiff enough to settle in a second, loose enough to jingle)
      s.wx += ((tx - s.ax) * k - s.wx * d) * dt; s.wz += ((tz - s.az) * k - s.wz * d) * dt;
      s.ax = clamp(s.ax + s.wx * dt, -1.1, 1.1); s.az = clamp(s.az + s.wz * dt, -1.1, 1.1);
    }
    s.p = (s.p || V()).copy(v3);
    e3.set(s.ax + (P[n + '.x'] ?? 0), P[n + '.y'] ?? 0, s.az + (P[n + '.z'] ?? 0));
    o.parent.getWorldQuaternion(q4); q3.setFromEuler(e3);
    o.quaternion.copy(q4.invert()).multiply(q3);
  }
}
// the web he hangs from in jl_hang: silk threads 5.4 m up, spun in the root's frame (it moves with him)
function web(r, k) {
  if (!r.web) {
    const g = new THREE.Group(), m = new THREE.MeshStandardMaterial({ color: 0xf6f0ff, emissive: 0x2a2038, roughness: 0.35 });
    const thread = (a, b, rad = 0.012) => { const d = b.clone().sub(a), t = new THREE.Mesh(new THREE.CylinderGeometry(rad, rad, d.length(), 5), m); t.position.copy(a).add(b).multiplyScalar(0.5); t.quaternion.setFromUnitVectors(V(0, 1, 0), d.normalize()); g.add(t); };
    const N = 10, rings = [0.6, 1.3, 2.1, 2.9];
    for (let i = 0; i < N; i++) { const a = (i / N) * Math.PI * 2; thread(V(0, 0, 0), V(Math.cos(a) * 3.4, 0, Math.sin(a) * 3.4), 0.016); }
    for (const R of rings) for (let i = 0; i < N; i++) { const a0 = (i / N) * Math.PI * 2, a1 = ((i + 1) / N) * Math.PI * 2, s = R * (0.94 + 0.06 * Math.sin(i * 2.3)); thread(V(Math.cos(a0) * s, -0.04 * (R / 3), Math.sin(a0) * s), V(Math.cos(a1) * s, -0.04 * (R / 3), Math.sin(a1) * s)); }
    g.position.y = JL_DATA.webY; g.name = 'jl_web'; r.c.root.add(g); r.web = g;
  }
  r.web.visible = k > 0.01; r.web.scale.setScalar(Math.max(0.01, k));
}
// the pose for `name` at t, with the scuttle and the carry-over from the last clip laid in
function compose(r, name, t, dt) {
  const a = r.a;
  if (r.name !== name || t < r.t - 1e-4) { r.from = r.out && r.name ? r.out : null; r.fromName = r.name; r.fromT = t; r.name = name; r.markI = 0; r.faceI = -1; }
  r.t = t;
  const base = name === 'jl_walk' ? 'jl_idle' : name; // (the scuttle runs by distance, not by the clock)
  let P = evalClip(base, t);
  const xf = r.fromName === 'jl_leg_off' ? 0.6 : XF; // (a leg flying home needs a moment)
  if (r.from && t - r.fromT < xf) {
    const u = ss((t - r.fromT) / xf), Q = {};
    for (const ch in P) Q[ch] = lerp(r.from[ch] ?? 0, P[ch], u);
    for (const ch in r.from) if (!(ch in P)) Q[ch] = lerp(r.from[ch], 0, u);
    P = Q;
  } else r.from = null;
  r.out = { ...P };
  // ---- the scuttle: whenever his root moves, by how far it went (the feet stay planted)
  const p = a.pos || r.c.root.position.toArray();
  if (r.last && dt > 0) {
    const d = Math.hypot(p[0] - r.last[0], p[2] - r.last[2]), sp = d < 3 ? d / dt : 0;
    r.gaitK = lerp(r.gaitK, sp > 0.06 ? 1 : 0, Math.min(1, dt * (sp > 0.06 ? 6 : 4)));
    if (d < 3) r.walkT += (d / JL_DATA.stride) * D.jl_walk.loop;
  }
  r.last = [p[0], p[1], p[2]];
  if (r.gaitK > 0.002 && !/^jl_(hang|drop|leg_off|leg_back)$/.test(name)) {
    const Wk = evalClip('jl_walk', r.walkT), k = r.gaitK;
    for (const ch of WALK_SET) P[ch] = lerp(P[ch] ?? 0, Wk[ch] ?? 0, k);
    for (const ch of WALK_ADD) P[ch] = (P[ch] ?? 0) + (Wk[ch] ?? 0) * k;
  }
  // ---- talking (dialogue): the dummy jaw goes with the voice
  if (a.talking && a.voice) P['jaw.x'] = (P['jaw.x'] ?? 0) + clamp(a.voice.level || 0) * 0.32;
  // ---- the look: the game turns his head to you afterwards; x.look says how much of that he keeps
  const lk = P['x.look'] ?? 1;
  P['neck.y'] = (P['neck.y'] ?? 0) - (a.lookY || 0) * (1 - lk); P['neck.x'] = (P['neck.x'] ?? 0) - (a.lookX || 0) * (1 - lk);
  return P;
}
function marksAndFace(r, name, t) {
  const C = D[name], a = r.a;
  const tt = C.loop ? t % C.loop : t;
  if (C.loop && tt < r.lastTT - 0.3) r.markI = 0;
  r.lastTT = tt;
  while (r.markI < C.marks.length && tt >= C.marks[r.markI][0]) fire(r, C.marks[r.markI++][1], name);
  let fi = -1; for (let i = 0; i < C.face.length; i++) if (tt >= C.face[i][0]) fi = i;
  if (fi !== r.faceI && fi >= 0) { r.faceI = fi; if (a.face && a.face.set && !faceLocked(a.face)) a.face.set(C.face[fi][1]); }
}
function fire(r, mark, clip) {
  const p = /^(hit|honk|thud|stir|hop|pop)$/.test(mark) ? r.at(LEG_OFF) : /tap|step|jingle/.test(mark) ? r.at('femRA') : r.at('eyeAt');
  const ev = { type: 'jl', mark, id: r.a.id, clip, at: [p.x, p.y, p.z] };
  for (const l of listeners) { try { l(ev); } catch (e) { console.warn('jl listener', e); } }
}
const mkF = (name) => function f(c, t) {
  const r = byCh.get(c) || findRig(c);
  if (!r) return;
  const now = performance.now(), dt = r.manualDt ?? Math.min(0.1, Math.max(0, (now - (r.now || now)) / 1000)); r.now = now;
  const P = compose(r, name, t, dt);
  apply(r, P); dangle(r, P, dt);
  // the web shows from the spring up to the drop; the stump whenever the leg is away from its socket
  const w = name === 'jl_hang' ? ss((t - 1.25) / 0.45) : name === 'jl_drop' ? 1 - ss((t - 0.2) / 0.3) : 0;
  if (w > 0.01 || r.web) web(r, w);
  stump(r, Math.abs(P[LEG_OFF + '.px'] ?? 0) + Math.abs(P[LEG_OFF + '.py'] ?? 0) + Math.abs(P[LEG_OFF + '.pz'] ?? 0) > 0.03);
  marksAndFace(r, name, t);
  if (ends(name) && t >= durationOf(name)) { const nx = NEXT[name] || 'jl_idle'; r.a.clip = { name: nx, t: 0, k: 1, len: 9e9, hold: true }; }
};
function findRig(c) { for (const a of actors.values()) if (a.ch === c) return rigOf(a); return null; }
export const JL_CLIPS = {};
for (const name in D) JL_CLIPS[name] = { len: 9e9, f: mkF(name) };
export const MARKS = Object.fromEntries(Object.entries(D).map(([k, v]) => [k, v.marks]));
let registered = false;
export function jlRegister() { if (registered) return; registered = true; Object.assign(CLIPS, JL_CLIPS); kick(); } // (called when the first of him is built)

export const JL = {
  auto: true, clips: Object.keys(D), data: JL_DATA,
  on(f) { listeners.add(f); return () => listeners.delete(f); },
  play(a, clip, opts = {}) { jlRegister(); rigOf(a); playClip(a, clip, { ...opts, hold: true }); },
  at(a, name) { return rigOf(a).at(name); },
  rig: (a) => rigOf(a),
};
if (typeof window !== 'undefined') window.JF_JL = JL; // (tests and devtools)

// ---------------------------------------------------------------- every frame (the host can call jlFrame; until it does this ticks itself)
let hosted = 0, ticking = false, lastTick = 0;
export function jlFrame(dt, cam) { hosted = performance.now(); frame(dt, cam); }
function frame(dt, cam) {
  for (const a of actors.values()) {
    if (!a.L || a.L.look !== 'jester_lord') continue;
    const r = rigOf(a);
    if (!a.clip) playClip(a, 'jl_idle', { hold: true }); // (never out of a clip: the big top would stop breathing)
    if (cam && a.L.blender) { const d = Math.hypot(cam.position.x - a.pos[0], cam.position.y - a.pos[1], cam.position.z - a.pos[2]); r.vis(r.far ? d > 30 : d > 34); }
  }
  for (const [id, r] of rigs) if (!r.manual && (!actors.has(id) || actors.get(id) !== r.a)) rigs.delete(id);
  if (PREV) preview(dt);
}
function kick() {
  if (ticking || typeof requestAnimationFrame === 'undefined') return;
  ticking = true; lastTick = performance.now();
  const tick = () => {
    const now = performance.now(), dt = Math.min(0.1, (now - lastTick) / 1000); lastTick = now;
    if (JL.auto && now - hosted > 500) frame(dt, G.camera || null);
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

// ---------------------------------------------------------------- the rehearsal (?story=1&jesterlord=1)
// he stands 7 m in front of you and runs his whole set on a loop, a caption for each clip and its marks. no damage
const PREV = typeof location !== 'undefined' && /[?&]jesterlord=1\b/.test(location.search);
const PROGRAM = [
  ['jl_idle', 6, null, 'HOLDING COURT · a front foot drums tip-tap-tap'],
  ['jl_talk', 5.2, null, 'THE SHOWMAN · "ladies, gentlemen, and whatever you are"'],
  ['jl_bow', 4.0, null, 'THE BOW · the whole spider curtsies'],
  ['jl_walk', 3.0, 'walkIn', 'THE SCUTTLE · four legs at a time, like a real spider'],
  ['jl_idle', 2.6, 'walkOut', 'BACK TO HIS MARK'],
  ['jl_hang', 5.0, null, 'UP INTO THE WEB · just hanging around'],
  ['jl_drop', 3.0, null, 'AND DOWN · TA-DA'],
  ['jl_leg_off', 5.4, null, 'LEG DAY CANCELLED · his eyes open (once)'],
  ['jl_leg_back', 3.4, null, 'IT SCREWS BACK ON · he is a puppet'],
];
let PV = null, pvWait = 0;
if (PREV && typeof window !== 'undefined') kick();
function preview(dt) {
  if (!PV) {
    if (!(G.joined && G.mode === 'story' && G.scene && ME.alive)) return;
    if ((pvWait += dt) < 3) return;
    const f = [-Math.sin(ME.yaw), -Math.cos(ME.yaw)], at = [ME.pos[0] + f[0] * 7, ME.pos[1], ME.pos[2] + f[1] * 7];
    at[1] = dropTo(at, 3);
    const a = spawnActor('jl_preview', { look: 'jester_lord', voice: { kind: 'boss', pitch: 1.2, rate: 1.1 }, name: 'THE HEADLINER' }, at, Math.atan2(ME.pos[0] - at[0], ME.pos[2] - at[2]) + Math.PI);
    a.home.face = a.yaw;
    const cap = document.createElement('div'); cap.id = 'jlPrev';
    cap.style.cssText = 'position:fixed;left:24px;top:64px;transform:rotate(-2deg);z-index:60;font:900 22px var(--font,sans-serif);color:#ffe14d;background:rgba(18,8,24,.92);border:4px solid #ff4fd8;box-shadow:8px 8px 0 #4fd8ff;padding:8px 18px;pointer-events:none;max-width:60vw';
    document.body.append(cap);
    PV = { a, i: -1, t: 0, len: 0, cap, home: [...at], near: [at[0] - f[0] * 3.2, at[1], at[2] - f[1] * 3.2], marks: [] };
    JL.on((ev) => { if (ev.id !== 'jl_preview') return; PV.marks.push(ev.mark.toUpperCase()); PV.marks = PV.marks.slice(-5); pvDraw(); });
    window.JF_JLP = PV;
  }
  PV.t += dt;
  if (PV.i < 0 || PV.t >= PV.len) {
    PV.i = (PV.i + 1) % PROGRAM.length;
    const [clip, len, pre, label] = PROGRAM[PV.i];
    if (pre === 'walkIn') walkTo(PV.a, [PV.near], 1.5);
    if (pre === 'walkOut') walkTo(PV.a, [PV.home], 1.5, (a) => { a.yaw = a.home.face; });
    JL.play(PV.a, clip); PV.t = 0; PV.len = len; PV.label = label; PV.marks = []; pvDraw();
  }
}
function pvDraw() { PV.cap.innerHTML = `${PV.label}<div style="font-size:16px;color:#4fd8ff;min-height:20px">${PV.marks.join(' · ')}</div><div style="font-size:12px;color:#fff;opacity:.7">the headliner rehearsal · ${PV.i + 1}/${PROGRAM.length} · no damage</div>`; }
