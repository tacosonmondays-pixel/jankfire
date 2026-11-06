// Containers in 3D: the crate, the duffel bag and the box, built from chunky boxes like everything else. On the
// CONTAINERS screen they're pictures (rendered once, cached); opening one plays it live in the roll box: it sits,
// it shakes harder and harder while the strip spins, then it bursts (the lid flies off, planks and confetti in the
// colour of what you got). Its own small renderer, drawing only while something moves.
import * as THREE from 'three';
import { M, freeTree } from './models.js';
import { objIcon } from './icons.js';

const box = (w, h, d, c, x = 0, y = 0, z = 0) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), M(c)); m.position.set(x, y, z); return m; };

// lid: the part that flies off. bits: the rest, which falls apart a little
export function buildContainer(kind) {
  const g = new THREE.Group(), lid = new THREE.Group();
  g.userData.lid = lid;
  if (kind === 'crate') { // planks, dark slats, a yellow FRAGILE-ish tag
    g.add(box(1.2, 0.8, 0.8, 0xa8743a, 0, 0.4, 0));
    for (const y of [0.18, 0.62]) for (const z of [-0.41, 0.41]) g.add(box(1.22, 0.1, 0.02, 0x6a4420, 0, y, z));
    for (const x of [-0.61, 0.61]) g.add(box(0.02, 0.8, 0.82, 0x6a4420, x, 0.4, 0));
    g.add(box(0.12, 0.82, 0.02, 0x6a4420, 0, 0.4, 0.42), box(0.34, 0.16, 0.02, 0xffe14d, 0.32, 0.5, 0.425));
    lid.add(box(1.28, 0.1, 0.88, 0x8a5a2a, 0, 0, 0), box(1.3, 0.04, 0.12, 0x5a3a18, 0, 0.06, 0));
    lid.position.y = 0.85;
  } else if (kind === 'bag') { // a green duffel: a fat cylinder on its side, round ends, a yellow stripe, handles
    const body = new THREE.Mesh(new THREE.CylinderGeometry(0.36, 0.36, 1.1, 10), M(0x3a6a2a)); body.rotation.z = Math.PI / 2; body.position.y = 0.36;
    g.add(body);
    for (const x of [-0.55, 0.55]) { const e = new THREE.Mesh(new THREE.SphereGeometry(0.36, 10, 6, 0, Math.PI * 2, 0, Math.PI / 2), M(0x2e5a20)); e.rotation.z = x > 0 ? -Math.PI / 2 : Math.PI / 2; e.scale.y = 0.35; e.position.set(x, 0.36, 0); g.add(e); }
    g.add(box(1.12, 0.06, 0.74, 0xffe14d, 0, 0.36, 0));
    lid.add(box(1.0, 0.05, 0.1, 0x111111, 0, 0, 0)); // the zip
    for (const x of [-0.22, 0.22]) { const h = new THREE.Mesh(new THREE.TorusGeometry(0.14, 0.03, 4, 8, Math.PI), M(0x1a1a1a)); h.position.set(x, 0.02, 0); lid.add(h); }
    lid.position.y = 0.72;
  } else { // a cardboard box, pink tape, four flaps
    g.add(box(1.0, 0.7, 0.8, 0xc8a46a, 0, 0.35, 0), box(0.18, 0.72, 0.82, 0xff4fd8, 0, 0.35, 0));
    for (const [x, z, w, d] of [[0, 0.2, 1.0, 0.4], [0, -0.2, 1.0, 0.4]]) lid.add(box(w, 0.04, d, 0xe0c088, x, 0, z));
    lid.add(box(0.18, 0.05, 0.82, 0xff4fd8, 0, 0.01, 0));
    lid.position.y = 0.72;
  }
  g.add(lid);
  return g;
}
// the picture on the CONTAINERS cards
export function containerPic(kind) {
  return objIcon('container:' + kind, () => { const g = buildContainer(kind); g.rotation.set(0.35, -0.6, 0); return g; });
}

// ------------------------------------------------------------ the live one in the roll box
let R = null;
function setup(canvas) {
  if (R && R.canvas === canvas) return R;
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: true });
  renderer.setPixelRatio(1);
  const scene = new THREE.Scene();
  scene.add(new THREE.HemisphereLight(0xffffff, 0x6a3a6a, 2.6));
  const sun = new THREE.DirectionalLight(0xffffff, 2.2); sun.position.set(1, 2, 1.5); scene.add(sun);
  const cam = new THREE.PerspectiveCamera(38, 2, 0.1, 50);
  cam.position.set(0, 1.5, 4.0); cam.lookAt(0, 0.55, 0);
  R = { canvas, renderer, scene, cam, obj: null, bits: [], t: 0, dur: 4.6, burst: false, raf: 0, last: 0, color: 0xffffff, res: 1 };
  return R;
}
function size() {
  const w = R.canvas.clientWidth || 360, h = R.canvas.clientHeight || 180;
  R.renderer.setSize(Math.max(40, Math.floor(w * R.res)), Math.max(30, Math.floor(h * R.res)), false);
  R.cam.aspect = w / h; R.cam.updateProjectionMatrix();
}
// play: kind, the rarity colour of what's inside (hex string), how long the shake lasts (s), res (potato renders smaller)
export function playContainer(canvas, kind, color, dur = 4.6, res = 1) {
  setup(canvas);
  stopContainer();
  R.res = res; size(); requestAnimationFrame(() => R && size()); // (the box was just shown: measure again once it has a size)
  R.obj = buildContainer(kind);
  R.scene.add(R.obj);
  R.t = 0; R.dur = dur; R.burst = false; R.color = new THREE.Color(color || '#ffffff').getHex();
  R.last = performance.now();
  R.raf = requestAnimationFrame(frame);
}
export function stopContainer() {
  if (!R) return;
  cancelAnimationFrame(R.raf); R.raf = 0;
  for (const b of R.bits) { R.scene.remove(b.m); freeTree(b.m); }
  R.bits = [];
  if (R.obj) { R.scene.remove(R.obj); freeTree(R.obj); R.obj = null; }
}
function burst() {
  R.burst = true;
  const lid = R.obj.userData.lid;
  lid.userData.v = new THREE.Vector3((Math.random() - 0.5) * 2, 5.5, (Math.random() - 0.5) * 2); lid.userData.w = new THREE.Vector3(6, 2, 4);
  const conf = [R.color, R.color, 0xffe14d, 0xff4fd8, 0x4fd8ff, 0xffffff];
  for (let i = 0; i < 60; i++) { // confetti + a few planks
    const big = i < 6;
    const m = new THREE.Mesh(new THREE.BoxGeometry(big ? 0.5 : 0.11, big ? 0.06 : 0.11, big ? 0.12 : 0.03), M(big ? 0x8a5a2a : conf[i % conf.length]));
    m.position.set((Math.random() - 0.5) * 0.6, 0.7, (Math.random() - 0.5) * 0.4);
    R.scene.add(m);
    const a = Math.random() * Math.PI * 2, s = big ? 2 : 1.5 + Math.random() * 3;
    R.bits.push({ m, v: new THREE.Vector3(Math.cos(a) * s * 0.7, 2 + Math.random() * 3, Math.sin(a) * s * 0.4), w: new THREE.Vector3(Math.random() * 9, Math.random() * 9, 0), life: 2.2 });
  }
}
function frame(now) {
  if (!R || !R.obj) return;
  const dt = Math.min(0.05, (now - R.last) / 1000); R.last = now;
  R.t += dt;
  const o = R.obj, k = Math.min(1, R.t / R.dur);
  if (!R.burst) {
    const amp = 0.01 + k * k * 0.09, f = 20 + k * 30; // a rattle that grows
    o.rotation.set(Math.sin(R.t * f) * amp, Math.sin(R.t * 1.3) * 0.4 + 0.5, Math.sin(R.t * f * 1.3 + 1) * amp);
    o.position.y = Math.abs(Math.sin(R.t * f * 0.5)) * amp * 0.8;
    o.scale.setScalar(1 + k * 0.08);
    if (R.t >= R.dur) burst();
  } else {
    const lid = o.userData.lid, v = lid.userData.v;
    v.y -= 9.8 * dt; lid.position.addScaledVector(v, dt); lid.rotation.x += lid.userData.w.x * dt; lid.rotation.z += lid.userData.w.z * dt;
    o.scale.setScalar(Math.max(0.9, o.scale.x - dt * 0.4));
    for (const b of R.bits) { b.v.y -= 3.2 * dt; b.v.multiplyScalar(1 - dt * 0.8); b.m.position.addScaledVector(b.v, dt); b.m.rotation.x += b.w.x * dt; b.m.rotation.y += b.w.y * dt; b.life -= dt; b.m.visible = b.life > 0; }
  }
  R.renderer.render(R.scene, R.cam);
  if (R.burst && R.t > R.dur + 2.4) return; // it's done: the last frame stays, nothing more is drawn
  R.raf = requestAnimationFrame(frame);
}
