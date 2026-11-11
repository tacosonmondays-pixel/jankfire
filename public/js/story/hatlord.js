// MADAM CHAIR's rig on top of the story actor (docs/story/cast/HAT_LORD_MODEL.md): her clip set (hl_*, key poses in
// hl_clipdata.js, written by tools/blender/cast/hl_clips.py), the marks inside each clip, the hat's look (it turns to
// put HER eyes, the brown pair on the hat, on whoever she looks at, while her face stays level), her walk laid over
// whatever she is doing whenever she moves, the far LOD. Presentation only: nothing here does damage.
//   HL.play(a, clip)            clips: HL.clips. one clip runs into the next; a clip that ends goes back to hl_idle
//   HL.look(a, [x, y, z] | null) what the hat looks at (default: a.lookAt, else the camera when it is within 12 m)
//   HL.on((ev) => ...)          ev = { type: 'hl', mark, id, clip, at: [x, y, z] }
//   HL.at(a, 'eyeAt' | 'socketAt' | 'palmR' | 'hatMouthAt' | 'weakA' | ...)  -> a world point (THREE.Vector3)
// She is always in one of her clips (a spawned hat_lord with nothing playing is put into hl_idle), so the clip owns
// the whole of her: the cast's joints are set outright, her own (hatlook.js EXTRA) turn from their rest.
// Dev: ?story=1&hatlord=1 stands her in front of you and runs the whole set on a loop with captions (no damage).
import * as THREE from 'three';
import { G } from '../ctx.js';
import { ME } from '../player.js';
import { CLIPS, actors, play as playClip, spawnActor, walkTo, dropTo } from './actors.js';
import { faceLocked } from './looks.js';
import { HL_DATA } from './hl_clipdata.js';

const clamp = (x, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
const ss = (t) => { t = clamp(t); return t * t * (3 - 2 * t); };
const lerp = (a, b, k) => a + (b - a) * k;
const wrapA = (a) => Math.atan2(Math.sin(a), Math.cos(a));
const EASE = { ss, lin: (u) => u, in: (u) => u * u, out: (u) => 1 - (1 - u) * (1 - u), snap: (u) => 1 - (1 - u) ** 3, back: (u) => 1 + 2.70158 * (u - 1) ** 3 + 1.70158 * (u - 1) ** 2 };
const XF = 0.3; // one clip into the next: this long, from wherever the last one had her

// ---------------------------------------------------------------- the clips (the same sums as hl_clips.py evaluate())
const D = HL_DATA.clips, REST = HL_DATA.rest, STD = HL_DATA.std, LAG = HL_DATA.lag || [];
const def = (ch) => REST[ch] ?? 0;
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
const blinkW = (u) => (u < 0 || u >= 1 ? 0 : u < 0.32 ? ss(u / 0.32) : u < 0.5 ? 1 : 1 - ss((u - 0.5) / 0.5));
export function evalClip(name, t, out = {}) {
  const C = D[name]; poseAt(C, t, out);
  if (!C.nolag) for (const [pre, lag] of LAG) {
    let late = null;
    for (const ch in out) if (ch.startsWith(pre)) { late ||= poseAt(C, t - lag, {}); out[ch] = late[ch] ?? 0; }
  }
  for (const [ch, amp, f, ph] of C.osc) out[ch] = (out[ch] ?? 0) + amp * Math.sin(t * f + ph);
  for (const [t0, lids, d, depth] of C.blinks || []) {
    const dt = C.loop ? (((t - t0) % C.loop) + C.loop) % C.loop : t - t0, w = blinkW(dt / d);
    if (w) for (const l of lids) out[l + '.x'] = (out[l + '.x'] ?? 0) + depth * w;
  }
  return out;
}
export const durationOf = (name) => D[name].len || D[name].loop || D[name].keys[D[name].keys.length - 1].t;
const ends = (name) => !!D[name].len; // (a clip with a length ends by itself; a loop or a held pose does not)
const NEXT = { hl_reveal_end: 'hl_idle' };
// what the walk owns when she moves, and what it only adds to (the hat keeps doing what the clip has it doing)
const WALK_SET = ['legL.x', 'legR.x', 'kneeL.x', 'kneeR.x', 'body.py', 'body.z', 'body.y'];
const WALK_ADD = ['spine.z', 'spine.y', 'head.z', 'arm.x', 'armL.x', 'hatNeck.z', 'hat.z', 'hat.x', 'hatNeck.y', 'brimR.z', 'brimRb.z', 'brimL.z', 'brimLb.z', 'brimF.x', 'brimB.x', 'feeler.z', 'feelerB.z', 'feeler.y', 'growthA.z', 'growthB.x', 'growthC.z'];
const HAT_ONLY = (ch) => !STD.some((j) => ch.startsWith(j + '.')) && !ch.startsWith('x.') && !/^(idx|fin|thumb)/.test(ch);

const rigs = new Map(), byCh = new WeakMap(), listeners = new Set();
const e3 = new THREE.Euler(), q3 = new THREE.Quaternion(), V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
function rigOf(a) {
  let r = rigs.get(a.id);
  if (r && r.a === a) return r;
  r = makeRig(a); rigs.set(a.id, r); byCh.set(a.ch, r); kick(); return r;
}
function makeRig(a) {
  const L = a.L, c = a.ch, own = (L.extra || []).filter((j) => c[j]);
  const r = { a, c, own, rest: {}, name: null, t: 0, out: null, from: null, fromT: 0, markI: 0, faceI: -1, lookTo: undefined, aimY: 0, aimX: 0, eyeY: 0, eyeX: 0, gaitK: 0, walkT: 0, last: null, now: 0, far: null };
  for (const j of own) r.rest[j] = { q: c[j].quaternion.clone(), p: c[j].position.clone() };
  r.at = (name) => { const m = L.parts && L.parts[name]; return m ? m.getWorldPosition(V()) : c[name] ? c[name].getWorldPosition(V()) : c.head.getWorldPosition(V()); };
  r.vis = (far) => {
    if (r.far === far || !L.blender) return; r.far = far;
    for (const jn of STD.concat(own)) {
      const J = c[jn]; if (!J) continue;
      for (const ch of J.children) {
        if (ch.name === 'ot_lod') ch.visible = far;
        else if ((ch.isMesh && !(L.face && ch === L.face.root)) || ch.userData.blender) ch.visible = !far;
      }
    }
    if (L.face) L.face.root.visible = !far;
  };
  return r;
}
function apply(r, P) {
  const c = r.c;
  for (const j of STD) c[j].rotation.set(P[j + '.x'] ?? def(j + '.x'), P[j + '.y'] ?? def(j + '.y'), P[j + '.z'] ?? def(j + '.z'));
  c.body.position.set(P['body.px'] ?? 0, P['body.py'] ?? 0, P['body.pz'] ?? 0);
  applyOwn(r, P);
}
function applyOwn(r, P, only) {
  const c = r.c;
  for (const j of r.own) {
    if (only && !only(j)) continue;
    const o = c[j], R = r.rest[j];
    e3.set(P[j + '.x'] ?? def(j + '.x'), P[j + '.y'] ?? def(j + '.y'), P[j + '.z'] ?? def(j + '.z'));
    o.quaternion.copy(R.q).multiply(q3.setFromEuler(e3));
    o.position.set(R.p.x + (P[j + '.px'] ?? 0), R.p.y + (P[j + '.py'] ?? 0), R.p.z + (P[j + '.pz'] ?? 0));
  }
}
// the pose for `name` at t, with the walk, the look and the carry-over from the last clip laid in
function compose(r, name, t, dt) {
  const a = r.a;
  if (r.name !== name || t < r.t - 1e-4) { // a new play: carry on from the last pose
    r.from = r.out && r.name ? r.out : null; r.fromT = t; r.name = name; r.markI = 0; r.faceI = -1;
  }
  r.t = t;
  const base = name === 'hl_walk' ? 'hl_idle' : name; // (the walk is the stance plus the legs below: it runs by distance, not by the clock)
  let P = evalClip(base, t);
  if (r.from && t - r.fromT < XF) {
    const u = ss((t - r.fromT) / XF), Q = {};
    for (const ch in P) Q[ch] = lerp(r.from[ch] ?? def(ch), P[ch], u);
    for (const ch in r.from) if (!(ch in P)) Q[ch] = lerp(r.from[ch], def(ch), u);
    P = Q;
  } else r.from = null;
  r.out = { ...P };
  // ---- her walk: whenever her root is moving, by how far it has gone (feet do not slide)
  const p = a.pos || r.c.root.position.toArray();
  if (r.last && dt > 0) {
    const d = Math.hypot(p[0] - r.last[0], p[2] - r.last[2]), sp = d < 3 ? d / dt : 0;
    r.gaitK = lerp(r.gaitK, sp > 0.06 ? 1 : 0, Math.min(1, dt * (sp > 0.06 ? 5 : 3.5)));
    if (d < 3) r.walkT += (d / HL_DATA.stride) * D.hl_walk.loop;
  }
  r.last = [p[0], p[1], p[2]];
  if (r.gaitK > 0.002) {
    const W = evalClip('hl_walk', r.walkT), k = r.gaitK;
    for (const ch of WALK_SET) P[ch] = lerp(P[ch] ?? def(ch), W[ch] ?? def(ch), k);
    for (const ch of WALK_ADD) P[ch] = (P[ch] ?? def(ch)) + ((W[ch] ?? def(ch)) - def(ch)) * k;
    P['spine.x'] = (P['spine.x'] ?? 0) + (W['spine.x'] ?? 0) * k;
  }
  // ---- the look: the hat turns to put her eyes on it. the eyes get there first, the hat follows; her face stays level
  const lk = P['x.look'] ?? 0;
  const tgt = r.lookTo !== undefined ? r.lookTo : a.lookAt || (G.camera && Math.hypot(G.camera.position.x - p[0], G.camera.position.z - p[2]) < 12 ? G.camera.position.toArray() : null);
  let wy = 0, wx = 0;
  if (tgt && lk > 0.01) {
    const S = r.c.root.scale.y, hy = p[1] + 2.95 * S, dx = tgt[0] - p[0], dz = tgt[2] - p[2];
    wy = clamp(wrapA(Math.atan2(-dx, -dz) - (a.yaw ?? r.c.root.rotation.y)) - (P['spine.y'] ?? 0) - (P['body.y'] ?? 0), -1.5, 1.5) * lk;
    wx = clamp(-(Math.atan2(hy - tgt[1], Math.hypot(dx, dz)) - 0.24), -0.6, 0.3) * lk; // (the hat sits tipped 0.24 down already)
  }
  const kh = Math.min(1, dt * 2.6), ke = Math.min(1, dt * 12);
  r.aimY = lerp(r.aimY, clamp(wy, -1.15, 1.15), kh); r.aimX = lerp(r.aimX, wx, kh);
  r.eyeY = lerp(r.eyeY, clamp(wy - r.aimY, -0.42, 0.42), ke); r.eyeX = lerp(r.eyeX, clamp(wx - r.aimX, -0.3, 0.3), ke);
  P['hatNeck.y'] = (P['hatNeck.y'] ?? 0) + r.aimY; P['hat.x'] = (P['hat.x'] ?? 0) + r.aimX;
  for (const e of ['eyeHR', 'eyeHL']) { P[e + '.y'] = (P[e + '.y'] ?? 0) + r.eyeY; P[e + '.x'] = (P[e + '.x'] ?? 0) + r.eyeX; }
  // (the game turns her head to look after this: the neck takes most of that back out, so her face stays level)
  P['neck.y'] = (P['neck.y'] ?? 0) - (a.lookY || 0) * 0.85; P['neck.x'] = (P['neck.x'] ?? 0) - (a.lookX || 0) * 0.85;
  return P;
}
function marksAndFace(r, name, t) {
  const C = D[name], a = r.a;
  const tt = C.loop ? t % C.loop : t;
  if (C.loop && tt < r.lastTT - 0.5) r.markI = 0;
  r.lastTT = tt;
  while (r.markI < C.marks.length && tt >= C.marks[r.markI][0]) fire(r, C.marks[r.markI++][1], name);
  let fi = -1; for (let i = 0; i < C.face.length; i++) if (tt >= C.face[i][0]) fi = i;
  if (fi !== r.faceI && fi >= 0) { r.faceI = fi; if (a.face && a.face.set && !faceLocked(a.face)) a.face.set(C.face[fi][1]); }
}
function fire(r, mark, clip) {
  const p = r.at(mark === 'aye' || mark === 'stop' || mark === 'hit' ? 'hatMouthAt' : 'eyeAt');
  const ev = { type: 'hl', mark, id: r.a.id, clip, at: [p.x, p.y, p.z] };
  for (const l of listeners) { try { l(ev); } catch (e) { console.warn('hl listener', e); } }
}
const mkF = (name) => function f(c, t) {
  const r = byCh.get(c) || findRig(c);
  if (!r) return;
  const now = performance.now(), dt = r.manualDt ?? Math.min(0.1, Math.max(0, (now - (r.now || now)) / 1000)); r.now = now;
  apply(r, compose(r, name, t, dt));
  marksAndFace(r, name, t);
  if (ends(name) && t >= durationOf(name)) { const nx = NEXT[name] || 'hl_idle'; r.a.clip = { name: nx, t: 0, k: 1, len: 9e9, hold: true }; } // (hands over without a frame of the stock pose)
};
function findRig(c) { for (const a of actors.values()) if (a.ch === c) return rigOf(a); return null; }
export const HL_CLIPS = {};
for (const name in D) HL_CLIPS[name] = { len: 9e9, f: mkF(name) };
export const MARKS = Object.fromEntries(Object.entries(D).map(([k, v]) => [k, v.marks]));
let registered = false;
export function hlRegister() { if (registered) return; registered = true; Object.assign(CLIPS, HL_CLIPS); kick(); } // (called when the first of her is built)

export const HL = {
  auto: true, clips: Object.keys(D), data: HL_DATA,
  on(f) { listeners.add(f); return () => listeners.delete(f); },
  play(a, clip, opts = {}) { hlRegister(); rigOf(a); playClip(a, clip, { ...opts, hold: true }); },
  look(a, to) { rigOf(a).lookTo = to === undefined ? undefined : to; },
  at(a, name) { return rigOf(a).at(name); },
  rig: (a) => rigOf(a),
};
if (typeof window !== 'undefined') window.JF_HL = HL; // (tests and the scene's devtools)

// ---------------------------------------------------------------- every frame (the host can call hlFrame; until it does this ticks itself)
let hosted = 0, ticking = false, lastTick = 0;
export function hlFrame(dt, cam) { hosted = performance.now(); frame(dt, cam); }
function frame(dt, cam) {
  for (const a of actors.values()) {
    if (!a.L || a.L.look !== 'hat_lord') continue;
    const r = rigOf(a);
    if (!a.clip) playClip(a, 'hl_idle', { hold: true }); // (she is never out of a clip: the hat would stop breathing)
    else if (!D[a.clip.name]) { // a stock gesture has her body: keep the hat alive under it
      r.t2 = (r.t2 || 0) + dt; const P = evalClip('hl_idle', r.t2); applyOwn(r, P, (j) => HAT_ONLY(j + '.'));
    }
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
    if (HL.auto && now - hosted > 500) frame(dt, G.camera || null);
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

// ---------------------------------------------------------------- the rehearsal (?story=1&hatlord=1)
// she stands in front of you and runs her whole set on a loop, a caption for each clip and its marks. no damage
const PREV = typeof location !== 'undefined' && /[?&]hatlord=1\b/.test(location.search);
const PROGRAM = [
  ['hl_idle', 6, null, 'IDLE · she barely moves. the hat breathes'],
  ['hl_talk', 6, null, 'TALK · the hat aims her eyes at you. her face stays level'],
  ['hl_offer', 4.5, null, 'THE OFFER · one long hand, palm up'],
  ['hl_bow', 3, null, 'A SMALL BOW · the hat does not bow'],
  ['hl_lunge', 5.2, null, 'THE HAT LUNGES · one finger. "not carried."'],
  ['hl_reveal', 5, null, 'THE REVEAL · no eyes'], ['hl_reveal_end', 2.4, null, 'ITS FINGERS LACE BACK OVER'],
  ['hl_walk', 5, 'walkIn', 'THE STALK'], ['hl_duck', 5, null, 'UNDER A DOORWAY · the hat goes through on edge'],
  ['hl_idle', 1, 'walkOut', 'BACK TO HER MARK'],
  ['hl_attack_tell', 1.7, null, 'ATTACK TELL · it rears up to her left'], ['hl_strike', 1.8, null, 'STRIKE · three metres of wing'],
  ['hl_stagger', 1.8, null, 'STAGGER · every eye shuts'], ['hl_hat_off', 7, null, 'THE HAT COMES OFF'],
];
let PV = null, pvWait = 0;
if (PREV && typeof window !== 'undefined') kick(); // (the tick finds the moment you are in the story and spawns her)
function preview(dt) {
  if (!PV) {
    if (!(G.joined && G.mode === 'story' && G.scene && ME.alive)) return;
    if ((pvWait += dt) < 3) return;
    const f = [-Math.sin(ME.yaw), -Math.cos(ME.yaw)], at = [ME.pos[0] + f[0] * 7, ME.pos[1], ME.pos[2] + f[1] * 7];
    at[1] = dropTo(at, 3);
    const a = spawnActor('hl_preview', { look: 'hat_lord', voice: { kind: 'choir', pitch: 0.8, rate: 0.8 }, name: 'MADAM CHAIR' }, at, Math.atan2(ME.pos[0] - at[0], ME.pos[2] - at[2]) + Math.PI);
    a.home.face = a.yaw;
    const cap = document.createElement('div'); cap.id = 'hlPrev';
    cap.style.cssText = 'position:fixed;left:24px;top:64px;transform:rotate(-2deg);z-index:60;font:900 22px var(--font,sans-serif);color:#ffe14d;background:rgba(18,8,24,.92);border:4px solid #ff4fd8;box-shadow:8px 8px 0 #4fd8ff;padding:8px 18px;pointer-events:none;max-width:60vw';
    document.body.append(cap);
    PV = { a, i: -1, t: 0, len: 0, cap, home: [...at], near: [at[0] - f[0] * 3.2, at[1], at[2] - f[1] * 3.2], marks: [] };
    HL.on((ev) => { if (ev.id !== 'hl_preview') return; PV.marks.push(ev.mark.toUpperCase()); PV.marks = PV.marks.slice(-5); pvDraw(); });
    window.JF_HLP = PV;
  }
  PV.t += dt;
  if (PV.i < 0 || PV.t >= PV.len) {
    PV.i = (PV.i + 1) % PROGRAM.length;
    const [clip, len, pre, label] = PROGRAM[PV.i];
    if (pre === 'walkIn') walkTo(PV.a, [PV.near], 0.8);
    if (pre === 'walkOut') walkTo(PV.a, [PV.home], 0.9, (a) => { a.yaw = a.home.face; });
    HL.play(PV.a, clip); PV.t = 0; PV.len = len; PV.label = label; PV.marks = []; pvDraw();
  }
}
function pvDraw() { PV.cap.innerHTML = `${PV.label}<div style="font-size:16px;color:#4fd8ff;min-height:20px">${PV.marks.join(' · ')}</div><div style="font-size:12px;color:#fff;opacity:.7">madam chair rehearsal · ${PV.i + 1}/${PROGRAM.length} · no damage</div>`; }
