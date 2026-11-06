// The shredder pit (the Warehouse, by the west door), the client side. Two toothed drums turn in toward each other a
// few metres down the pit: cutter discs with hooked teeth, the two drums' discs interleaved, stripper fingers off the
// walls between them, bearing plates at the ends, a red glow and a light under it all, a grind you hear from 30 m.
// When someone goes in (the kill says pit: 1, shared/shredpit.js) the drums jam on them for a beat, crunch, spit blood,
// sparks and bits of whoever it was back up the pit, the teeth glow hot, and it revs back up angry.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { G } from './ctx.js';
import { fx } from './fx.js';
import { synth } from './audio.js';
import { jankify } from './jank.js';
import { PIT } from '/shared/shredpit.js';

let pits = [], group = null, mats = null, light = null;
const R = (s = 1) => (Math.random() - 0.5) * 2 * s;

function makeMats(MAT) {
  const lam = (c, o = {}) => jankify(new THREE.MeshLambertMaterial({ color: c, ...o }));
  return {
    disc: lam(0x8f99a4), core: lam(0x3a3f47), teeth: lam(0xd9dfe7, { emissive: 0x000000 }), dark: lam(0x24272c), comb: lam(0x5a4636),
    hazard: (MAT && MAT.hazard && MAT.hazard.mat) || lam(0xffd000),
    glow: new THREE.MeshBasicMaterial({ color: 0xff2a10, transparent: true, opacity: 0.85, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }),
  };
}

// one drum, built round its own axis (local z), so turning it is just rotation.z. off = where its first disc sits
function drum(len, off, dir) {
  const discs = [], teeth = [], core = new THREE.CylinderGeometry(0.4, 0.4, len, 8).rotateX(Math.PI / 2);
  for (let z = -len / 2 + off, i = 0; z < len / 2 - 0.1; z += 0.4, i++) {
    discs.push(new THREE.CylinderGeometry(0.62, 0.62, 0.15, 12).rotateX(Math.PI / 2).translate(0, 0, z));
    for (let k = 0; k < 4; k++) { // four hooked teeth per disc, the next disc's set turned a bit further (a helix)
      const a = k * Math.PI / 2 + i * 0.45;
      const t = new THREE.BoxGeometry(0.22, 0.3, 0.15).translate(0, 0.72, 0); // the claw
      const h = new THREE.BoxGeometry(0.13, 0.14, 0.15).translate(dir * 0.09, 0.88, 0); // its hook, leaning the way it turns
      teeth.push(t.rotateZ(a).translate(0, 0, z), h.rotateZ(a).translate(0, 0, z));
    }
  }
  const g = new THREE.Group();
  g.add(new THREE.Mesh(core, mats.core), new THREE.Mesh(mergeGeometries(discs), mats.disc), new THREE.Mesh(mergeGeometries(teeth), mats.teeth));
  return g;
}

function build(s) {
  const [x0, z0, x1, z1] = s.box, cx = (x0 + x1) / 2, cz = (z0 + z1) / 2, alongZ = s.axis !== 'x';
  const W = alongZ ? x1 - x0 : z1 - z0, Lp = alongZ ? z1 - z0 : x1 - x0; // across the drums, along them
  const yc = s.y - 0.92, len = Lp - 0.5; // the drums' axis height (the teeth reach up to s.y), their length between the plates
  const root = new THREE.Group(); root.position.set(cx, 0, cz); if (!alongZ) root.rotation.y = Math.PI / 2;
  const sep = 0.75, A = drum(len, 0.2, 1), B = drum(len, 0.4, -1); // B's discs sit between A's
  A.position.set(-sep, yc, 0); B.position.set(sep, yc, 0);
  root.add(A, B);
  const box = (sx, sy, sz, m, x, y, z) => { const o = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), m); o.position.set(x, y, z); root.add(o); return o; };
  for (const e of [-1, 1]) { // the end plates, a hazard stripe along the top, the bearings
    box(W, 2.6, 0.25, mats.dark, 0, yc - 0.3, e * (len / 2 + 0.125));
    box(W, 0.12, 0.27, mats.hazard, 0, yc + 1.06, e * (len / 2 + 0.125));
    for (const x of [-sep, sep]) { const b = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.16, 6).rotateX(Math.PI / 2), mats.core); b.position.set(x, yc, e * (len / 2 - 0.08)); root.add(b); }
  }
  // stripper fingers off the long walls, between each drum's discs (nothing falls past the drums)
  const fingers = [];
  for (const [side, off] of [[-1, 0.4], [1, 0.2]]) for (let z = -len / 2 + off; z < len / 2 - 0.1; z += 0.4) fingers.push(new THREE.BoxGeometry(W / 2 - sep - 0.35, 0.22, 0.13).translate(side * (W / 2 - (W / 2 - sep - 0.35) / 2), yc + 0.1, z));
  root.add(new THREE.Mesh(mergeGeometries(fingers), mats.comb));
  box(W, 0.6, len, mats.dark, 0, yc - 1.5, 0); // the throat under it all (hides the shaft)
  const glow = box(W - 0.3, 0.02, len - 0.3, mats.glow, 0, yc - 1.18, 0);
  G.scene.add(root);
  return { s, root, A, B, glow, c: [cx, s.y, cz], alongZ, spin: 0, jam: 0, rev: 0, chew: 0, heat: 0, spitT: 0, clankT: 0 };
}

// called by world.js whenever the map changes
export function shredMap(map, MAT) {
  if (group) { for (const p of pits) G.scene.remove(p.root); pits = []; group = null; }
  if (light) { G.scene.remove(light); light = null; }
  const list = map && map.shredders;
  if (!list || !list.length || !G.scene) { level(0); return; }
  if (!mats) mats = makeMats(MAT);
  group = true;
  pits = list.map(build);
  light = new THREE.PointLight(0xff2a10, 6, 10, 1.2); light.position.set(pits[0].c[0], pits[0].s.y - 2.2, pits[0].c[2]);
  G.scene.add(light);
}

// ---------------------------------------------------------------- the grind (its own little synth: a motor + chopped grit)
let au = null;
function audio() {
  const ac = synth.ac;
  if (au || !ac || !synth.out) return au;
  const out = ac.createGain(); out.gain.value = 0;
  const pan = ac.createStereoPanner ? ac.createStereoPanner() : null;
  if (pan) { out.connect(pan); pan.connect(synth.out); } else out.connect(synth.out);
  const lp = ac.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 420; lp.connect(out);
  const mg = ac.createGain(); mg.gain.value = 0.3; mg.connect(lp);
  const o1 = ac.createOscillator(); o1.type = 'sawtooth'; o1.frequency.value = 41; o1.connect(mg); o1.start();
  const o2 = ac.createOscillator(); o2.type = 'square'; o2.frequency.value = 82.5; const o2g = ac.createGain(); o2g.gain.value = 0.35; o2.connect(o2g); o2g.connect(mg); o2.start();
  const nb = ac.createBuffer(1, ac.sampleRate * 2, ac.sampleRate), d = nb.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
  const ns = ac.createBufferSource(); ns.buffer = nb; ns.loop = true;
  const bp = ac.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = 1100; bp.Q.value = 0.9;
  const ng = ac.createGain(); ng.gain.value = 0.16;
  ns.connect(bp); bp.connect(ng); ng.connect(out); ns.start();
  const lfo = ac.createOscillator(); lfo.type = 'square'; lfo.frequency.value = 7.5; const lg = ac.createGain(); lg.gain.value = 0.12; lfo.connect(lg); lg.connect(ng.gain); lfo.start(); // the teeth coming round
  au = { out, pan, o1, o2, bp, lfo, k: -1 };
  return au;
}
function level(k, pan = 0) {
  const a = k > 0 ? audio() : au;
  if (!a) return;
  const t = synth.ac.currentTime;
  if (Math.abs(a.k - k) > 0.01) { a.out.gain.setTargetAtTime(k * 0.5, t, 0.12); a.k = k; }
  if (a.pan) a.pan.pan.setTargetAtTime(pan, t, 0.1);
}
function motor(f, tc) { // the motor's pitch: bogs down on a body, screams after
  if (!au) return;
  const t = synth.ac.currentTime;
  au.o1.frequency.setTargetAtTime(f, t, tc); au.o2.frequency.setTargetAtTime(f * 2.01, t, tc); au.lfo.frequency.setTargetAtTime(f * 0.18, t, tc); au.bp.frequency.setTargetAtTime(f * 27, t, tc);
}
function chewSound(p) {
  const { tone, noise } = synth;
  noise(0.5, 0.9, 'lowpass', 900, 110, p); tone('sine', 120, 36, 0.6, 0.8, p); // the crunch, the thud
  for (let i = 0; i < 10; i++) noise(0.04 + Math.random() * 0.06, 0.5, 'bandpass', 700 + Math.random() * 2600, 300, p, 0.06 + i * 0.07, 2); // bones
  for (let i = 0; i < 5; i++) noise(0.12, 0.32, 'bandpass', 380 + Math.random() * 600, 160, p, 0.45 + i * 0.13, 1.4); // wet bits landing
  tone('square', 150, 70, 0.4, 0.1, p, 0.04); // the motor bogging down
}

// ---------------------------------------------------------------- someone went in
// m = the kill message (pos = where they were). throws their bits back up the pit (m.vel: the body breakApart uses it)
export function pitKill(m, color) {
  if (!pits.length || !m.pos) return false;
  const p = pits.reduce((a, b) => (Math.hypot(b.c[0] - m.pos[0], b.c[2] - m.pos[2]) < Math.hypot(a.c[0] - m.pos[0], a.c[2] - m.pos[2]) ? b : a));
  const [x0, z0, x1, z1] = p.s.box, at = [Math.min(x1 - 0.4, Math.max(x0 + 0.4, m.pos[0])), p.s.y, Math.min(z1 - 0.4, Math.max(z0 + 0.4, m.pos[2]))];
  if (p.alongZ) at[0] = p.c[0]; else at[2] = p.c[2]; // the nip between the drums, along from where they dropped
  p.jam = PIT.jam; p.chew = PIT.chew; p.heat = 1; p.rev = 0; p.at = at;
  p.col = typeof color === 'string' ? parseInt(color.replace('#', ''), 16) || 0xff4fd8 : color || 0xff4fd8;
  m.vel = [R(3), 13 + Math.random() * 4, R(3)]; // the bits come back up out of the pit
  // the geyser: blood, sparks, bits of them (their colour) and shop confetti up out of the pit, a red shock ring, dust
  for (let i = 0; i < 3; i++) fx.blood([at[0] + R(0.5), at[1], at[2] + R(0.8)], [R(0.25), 1, R(0.25)], 60, null);
  fx.chute(at, [0, 1, 0], [0, 2, 0], 44, true, true);
  fx.spray(at, 46, [p.col, p.col, p.col, 0xffffff, 0x8a0000], 15, 2.2, 0.38, 9, 0.5);
  const { smoke } = fx.parts(); // a red mist hanging over the pit
  for (let i = 0; i < 16; i++) smoke.spawn(at[0] + R(1.2), at[1] + Math.random() * 1.5, at[2] + R(1.6), R(0.8), 2 + Math.random() * 3.5, R(0.8), 0.9 + Math.random() * 0.8, 0.45, 1.3 + Math.random() * 0.8, Math.random() < 0.5 ? 0xb01414 : 0x8a0a0a, 0x3a0606, 0.5, -0.4, 1.4);
  fx.sparks(at, [0, 1, 0], 30, true); fx.sparks([at[0], at[1], at[2] + R(1)], [0, 1, 0], 24, true);
  fx.ring([at[0], at[1] + 1.9, at[2]], 3.2, 0xff3a1a, 0.45);
  fx.smoke(at, 12, 0.7);
  chewSound(at); motor(26, 0.05);
  const cam = G.camera && G.camera.position, d = cam ? Math.hypot(cam.x - at[0], cam.y - at[1], cam.z - at[2]) : 99;
  G.shake = Math.max(G.shake || 0, Math.max(0, 1 - d / 22));
  return true;
}

// ---------------------------------------------------------------- every frame (world.js)
export function updateShredPit(dt) {
  if (!pits.length) return;
  const now = performance.now() / 1000, cam = G.camera;
  let near = 1e9, nearP = null;
  for (const p of pits) {
    // the drums: idle grind, stuck on a body (shuddering), then revving angry, easing back
    let w;
    if (p.jam > 0) { p.jam -= dt; w = 0; const j = R(0.05); p.A.rotation.z += j; p.B.rotation.z -= j; if (p.jam <= 0) { p.rev = 1; motor(55, 0.08); } }
    else { p.rev = Math.max(0, p.rev - dt / 2.4); w = PIT.idle * (1 + p.rev * PIT.rev); if (p.rev > 0 && p.rev < 0.02) motor(41, 0.4); }
    p.A.rotation.z -= w * dt; p.B.rotation.z += w * dt; // in toward each other over the top
    const sh = p.chew > 0 ? 0.06 : 0.006; // the whole machine judders (more with something in it)
    p.A.position.y = p.c[1] - 0.92 + R(sh); p.B.position.y = p.c[1] - 0.92 + R(sh);
    if (p.chew > 0) { // still chewing: little spurts up the pit
      p.chew -= dt; p.spitT -= dt;
      if (p.spitT <= 0 && p.at) { p.spitT = 0.06 + Math.random() * 0.06; fx.blood([p.at[0] + R(0.4), p.at[1], p.at[2] + R(0.7)], [R(0.3), 1, R(0.3)], 22, null); if (Math.random() < 0.6) fx.spray(p.at, 6, [p.col, 0x8a0000, 0xffffff], 9, 1.4, 0.2, 9, 0.6); }
    }
    p.heat = Math.max(0, p.heat - dt / PIT.heat);
    const d = cam ? Math.hypot(cam.position.x - p.c[0], cam.position.y - p.c[1], cam.position.z - p.c[2]) : 1e9;
    if (d < near) { near = d; nearP = p; }
  }
  // the teeth heat up red-orange on a body, cool back to steel; the glow + light breathe (and flare when it's fed)
  const hot = Math.max(...pits.map((p) => p.heat));
  mats.teeth.emissive.setRGB(hot * 0.95, hot * 0.27, hot * 0.04);
  const pulse = 0.5 + 0.5 * Math.sin(now * 4.1) * Math.sin(now * 1.7 + 1), fl = Math.random() < 0.06 ? 0.4 : 0;
  mats.glow.opacity = Math.min(1, 0.55 + pulse * 0.3 + hot * 0.4 - fl * 0.3);
  if (light) light.intensity = 4 + pulse * 3.5 + hot * 12 - fl * 2.5;
  // the grind: louder as you walk up, panned to where it is; a clank now and then
  const k = Math.max(0, 1 - near / PIT.hear) ** 1.6;
  let pan = 0;
  if (cam && nearP) { const yaw = cam.rotation.y, dx = nearP.c[0] - cam.position.x, dz = nearP.c[2] - cam.position.z, l = Math.hypot(dx, dz) || 1; pan = Math.max(-1, Math.min(1, (dx * Math.cos(yaw) - dz * Math.sin(yaw)) / l)) * 0.8; }
  level(G.joined ? k : 0, pan);
  if (nearP && k > 0.12 && now > nearP.clankT) { nearP.clankT = now + 0.25 + Math.random() * 0.9; synth.tone('triangle', 600 + Math.random() * 700, 260, 0.1, 0.05 * k, nearP.c); }
}
