// THE GUT CHOIR at the Choir Lung (ART_BIBLE #16, DESIGN §4.2): a few singers in the stalls either side of the aisle,
// all on one clock. They hum and sway together, sing a phrase together now and then, and when you walk in every head
// turns to you on the same frame (the hum stops dead), stares, and snaps back to the hymn together.
// The clips join actors.js's CLIPS (so a scene's 'anim' can play them too):
//   sing   a phrase, 4.8 s: a breath in (the chest up), "ahh" (the jaw), a catch, the big note (head back, the free
//          hand up and open), "mm"
//   heads  the turn: the eyes go first, then the head SNAPS round (c.turnY / c.turnX: where, from the body's front;
//          c.gazeAt: what the eyes stay on), the same tilt on everyone, held; it snaps back as it blends out
// playTogether(list, clip) starts a clip on a group on the same frame, their stop-motion steps lined up. The stance
// (the binder up, the hum's sway) is the look's own (looks.js choirLook). boot.js calls choirFrame(dt, eye) each frame
// in the slice city, before the actors update.
import * as THREE from 'three';
import { actors, spawnActor, despawnActor, play, CLIPS } from './actors.js';
import { CHOIR } from '/shared/city/cast_slice.js';
import { audioOut } from '../audio.js';
import { jankify } from '../jank.js';

const ss = (t) => (t <= 0 ? 0 : t >= 1 ? 1 : t * t * (3 - 2 * t));
const bump = (t) => (t <= 0 || t >= 1 ? 0 : Math.sin(t * Math.PI));
const win = (t, a, b, c, d) => ss((t - a) / (b - a)) * (1 - ss((t - c) / (d - c)));
const wrapA = (a) => Math.atan2(Math.sin(a), Math.cos(a));
const cl = (x, a, b) => Math.max(a, Math.min(b, x));

export const CHOIR_CLIPS = {
  sing: { len: 4.8, f(c, t, k) {
    const inh = win(t, 0.05, 0.55, 0.7, 1.0), big = win(t, 2.45, 2.75, 4.15, 4.5), all = win(t, 0.5, 0.7, 4.3, 4.7);
    const ah = win(t, 0.62, 0.78, 2.1, 2.3) * (0.42 + 0.22 * Math.abs(Math.sin((t - 0.62) * Math.PI * 2.4))); // the words of the line, a syllable at a time
    const jaw = ah + big * (0.86 + Math.sin(t * 31) * 0.05) + win(t, 2.25, 2.35, 2.42, 2.5) * 0.12; // (the held note wobbles: vibrato)
    if (c.faceRig) c.faceRig.sing = jaw * k;
    c.spine.rotation.x += (0.06 * inh + 0.035 * all + 0.06 * big) * k; c.spine.position.y += (0.014 * inh + 0.01 * big) * k; // the chest up for the breath, out for the note
    c.head.rotation.x += (0.05 * inh + 0.16 * big) * k; c.head.rotation.z -= 0.05 * big * k; // the chin up, a little lean into it
    c.arm.rotation.x += 0.42 * big * k; c.arm.rotation.z += 0.75 * big * k; c.foreR.rotation.x -= 0.85 * big * k; c.foreR.rotation.z += 0.3 * big * k; // the free hand lifts off the page and opens
    c.armL.rotation.x += 0.08 * big * k; // (the binder comes up a touch with it)
  } },
  heads: { len: 4.6, f(c, t, k) {
    const snap = ss((t - 0.3) / 0.11), over = bump((t - 0.38) / 0.3) * 0.12, tilt = ss((t - 0.95) / 0.09);
    const ty = (c.turnY ?? 0.9) * (snap + over), tx = (c.turnX ?? 0) * snap;
    c.head.rotation.y += ty * 0.84 * k; c.spine.rotation.y += ty * 0.16 * k; c.head.rotation.x += tx * k;
    c.head.rotation.z += 0.2 * tilt * k; // (everyone the same tilt, on the same frame)
    c.spine.position.y += 0.01 * snap * k; // (a little straighten: noticed)
    if (c.faceRig) { c.faceRig.gaze = t > 0.06 && k > 0.4 && c.gazeAt ? c.gazeAt : null; c.faceRig.sing = 0.1 * ss((t - 1.6) / 0.4) * k; } // the eyes first; later the lips part, as if to say something. they don't
  } },
};
Object.assign(CLIPS, CHOIR_CLIPS);

// start a clip on several actors on the same frame: the same clip clock, the same stop-motion steps
export function playTogether(list, name, opts = {}) {
  const acc = Math.max(0, ...list.map((a) => a.stepAcc || 0));
  for (const a of list) { play(a, name, opts); a.stepAcc = acc; }
}
// end a held clip on several actors at once (it blends out over its last 0.25 s: a snap back)
export function releaseTogether(list, name) {
  for (const a of list) if (a.clip && a.clip.name === name) { a.clip.hold = false; a.clip.len = a.clip.t + 0.3; }
}

// ------------------------------------------------------------ the director at the Choir Lung
const D = { on: false, list: [], next: 7, stareT: -1, cool: 0, wasIn: false, hum: null };
export const choirState = () => D; // (tools and tests: who's out, when they sing next, whether they're staring)
const LUNG = { x: -268, z: -218, rx: 21, rz: 19, y: 40 }; // (shared/city/gut.js choir(): the colonnade's ring)
const v3 = new THREE.Vector3();
const ahead = (a, dist, up) => { a.ch.head.getWorldPosition(v3); return [a.pos[0] - Math.sin(a.yaw) * dist, v3.y + up, a.pos[2] - Math.cos(a.yaw) * dist]; };

function spawn() {
  D.list = CHOIR.map((s, i) => spawnActor('choir_' + i, { look: s.look, voice: { kind: 'choir', pitch: s.look === 'choir' ? 0.8 : 1.15 }, idle: 'idle' }, s.p, s.face));
  const t0 = Math.random() * 10;
  for (const a of D.list) { a.t = t0; a.stepAcc = 1; a.choir = true; a.ch.gazeAt = new THREE.Vector3(); a.lookAt = null; glow(a); } // one clock for all of them
  D.on = true; D.next = 5 + Math.random() * 3; D.stareT = -1; D.wasIn = false;
  humStart();
}
function despawn() { for (const a of D.list) { if (actors.get(a.id) === a) despawnActor(a.id); for (const m of a.lifted || []) m.dispose(); } D.list = []; D.on = false; humStop(); }
// the lung is dark (the Gut's grade, the lung's own shadow over them): the singers carry a little light of their own,
// their colours lifted from inside (an emissive copy of each texture). no lamp: a light would rebuild every shader in
// the city on the way in and again on the way out. the model's materials are shared by every singer (done once); the
// face rig's are shared with the whole cast, so each singer gets copies of those (dropped when they go)
const LIFT = 0.26, WHITE = new THREE.Color(1, 1, 1);
function glow(a) {
  a.lifted = [];
  a.ch.root.traverse((o) => {
    if (!o.isMesh) return;
    const out = [].concat(o.material).map((m) => {
      if (/^choir/.test(m.name)) { if (!m.userData.lift) { m.userData.lift = true; if (m.map) m.emissiveMap = m.map; m.emissive.copy(m.map ? WHITE : m.color).multiplyScalar(LIFT); m.needsUpdate = true; } return m; }
      if (!m.isMeshStandardMaterial) return m;
      const c = jankify(m.clone()); c.emissive.copy(m.color).multiplyScalar(LIFT); a.lifted.push(c); return c;
    });
    o.material = Array.isArray(o.material) ? out : out[0];
  });
}

export function choirFrame(dt, eye) {
  if (!eye || !CHOIR.length) { if (D.on) despawn(); return; } // (out of the story, or not in the city)
  const cx = CHOIR.reduce((s, c) => s + c.p[0], 0) / CHOIR.length, cz = CHOIR.reduce((s, c) => s + c.p[2], 0) / CHOIR.length;
  const d = Math.hypot(eye[0] - cx, eye[2] - cz);
  if (D.on && D.list.some((a) => actors.get(a.id) !== a)) despawn(); // (someone cleared the stage: a map change)
  if (!D.on && d < 38) spawn(); else if (D.on && d > 48) despawn();
  if (!D.on) return;
  const L = D.list, stare = D.stareT >= 0;
  const inLung = Math.hypot((eye[0] - LUNG.x) / LUNG.rx, (eye[2] - LUNG.z) / LUNG.rz) < 1 && Math.abs(eye[1] - LUNG.y - 1.6) < 5;
  const near = Math.min(...L.map((a) => Math.hypot(eye[0] - a.pos[0], eye[2] - a.pos[2])));
  D.cool -= dt;
  // the stare: when you come in through the door, or walk right up to them
  if (!stare && D.cool <= 0 && ((inLung && !D.wasIn) || near < 4.5)) {
    if (L.some((a) => a.clip && a.clip.name === 'sing')) for (const a of L) a.clip = null; // (cut off mid-note)
    D.stareT = 0; playTogether(L, 'heads', { hold: true });
  }
  D.wasIn = inLung;
  if (D.stareT >= 0) {
    D.stareT += dt;
    for (const a of L) { // every head on you, wherever you go (from the body's front: their heads turn, not their feet)
      const hp = a.ch.head.getWorldPosition(v3), yaw = Math.atan2(-(eye[0] - hp.x), -(eye[2] - hp.z));
      a.ch.turnY = cl(wrapA(yaw - a.yaw), -1.75, 1.75); a.ch.turnX = cl(Math.atan2(eye[1] - hp.y, Math.hypot(eye[0] - hp.x, eye[2] - hp.z)), -0.5, 0.5);
      a.ch.gazeAt.set(eye[0], eye[1], eye[2]); a.lookAt = ahead(a, 2, 0); // (the head's own look straight ahead: the clip does the turning)
    }
    if (D.stareT > 3.6 && (near > 6.5 || D.stareT > 14)) { releaseTogether(L, 'heads'); D.stareT = -1; D.cool = 9; D.next = 1.2; } // all back to the hymn at once
  } else {
    D.next -= dt;
    const singing = L.some((a) => a.clip && a.clip.name === 'sing');
    for (const a of L) a.lookAt = singing ? ahead(a, 2.4, 0.5) : ahead(a, 1.6, -0.45); // (sing out, chin up; between, eyes on the hymns)
    if (D.next <= 0) { playTogether(L, 'sing'); D.next = 9 + Math.random() * 5; }
  }
  humFrame(dt, d, D.stareT >= 0, L.some((a) => a.clip && a.clip.name === 'sing'));
}

// ------------------------------------------------------------ the sound: one chord, hummed, sung out, stopped dead
function humStart() {
  const o = audioOut(); if (!o || D.hum) return;
  const { ac, master } = o, out = ac.createGain(), flt = ac.createBiquadFilter();
  out.gain.value = 0; flt.type = 'lowpass'; flt.frequency.value = 420; flt.Q.value = 2; flt.connect(out); out.connect(master);
  const oscs = [130.8, 164.8, 196, 261.6].map((f, i) => { const os = ac.createOscillator(); os.type = i % 2 ? 'triangle' : 'sawtooth'; os.frequency.value = f; os.detune.value = (i - 1.5) * 6; os.connect(flt); os.start(); return os; });
  const lfo = ac.createOscillator(), lg = ac.createGain(); lfo.frequency.value = 5.2; lg.gain.value = 3; lfo.connect(lg); for (const os of oscs) lg.connect(os.detune); lfo.start();
  D.hum = { ac, out, flt, oscs: [...oscs, lfo] };
}
function humStop() { const h = D.hum; if (!h) return; const t = h.ac.currentTime; h.out.gain.setTargetAtTime(0, t, 0.05); for (const o of h.oscs) o.stop(t + 0.4); D.hum = null; }
function humFrame(dt, d, stare, singing) {
  if (!D.hum) humStart(); // (the audio wakes on the first click: until then there's nothing to hum into)
  const h = D.hum; if (!h) return;
  const t = h.ac.currentTime, near = 1 / (1 + Math.max(0, d - 4) / 6);
  h.out.gain.setTargetAtTime(stare ? 0 : (singing ? 0.08 : 0.03) * near, t, stare ? 0.015 : 0.25); // (the stare: silence, at once)
  h.flt.frequency.setTargetAtTime(singing ? 1500 : 420, t, 0.2); // ("mmm" to "ahh")
}
