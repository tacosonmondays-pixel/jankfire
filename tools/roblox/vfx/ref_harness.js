// The reference side of the VFX pipeline (roblox/docs/VFX-PIPELINE.md): runs the WEB GAME'S OWN effect code (fx.js,
// flipbook.js, and the muzzle flash from weapons.js) on a fixed clock, so a frame "0.05 s after the shot" is the same
// frame every run. ref_capture.mjs drives this page in headless Chrome and photographs it.
//
//   REF.start(name, view, opts)  -> builds the room, puts the camera, fires the effect at t = 0
//   REF.advance(t)               -> steps the effects in fixed 1/240 s steps up to t (seconds), renders one frame
//
// Units are the web game's metres. Math.random is seeded per start(), so the same sparks fly every time.
import * as THREE from 'three';
import { fx, scaleU } from '/js/fx.js';
import { smokeCloud, updateFlipbooks, flipbooks, boomSprite, clearFlipbooks } from '/js/flipbook.js';
import { G } from '/js/ctx.js';

const W = 640, H = 360, FOV = 70, DT = 1 / 240;
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setSize(W, H);
renderer.setPixelRatio(1);
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x30343a);
const camera = new THREE.PerspectiveCamera(FOV, W / H, 0.02, 400);
G.scene = scene; G.camera = camera; G.renderer = renderer;
fx.init(scene);
fx.setScale(H / (2 * Math.tan((FOV * Math.PI) / 360)));

// a plain room, lit flat: a mid-grey floor, a lighter back wall 15 m ahead, a side wall. the critic judges the effect,
// not the room, so it stays quiet (the Roblox shots are taken against a plain wall too)
const hemi = new THREE.HemisphereLight(0xffffff, 0x555555, 1.6); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xffffff, 1.4); sun.position.set(-4, 10, 6); scene.add(sun);
const grey = (c) => new THREE.MeshLambertMaterial({ color: c });
const floor = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), grey(0x5d6066)); floor.rotation.x = -Math.PI / 2; scene.add(floor);
const back = new THREE.Mesh(new THREE.PlaneGeometry(80, 20), grey(0x8a8c90)); back.position.set(0, 10, -15); scene.add(back);
const side = new THREE.Mesh(new THREE.PlaneGeometry(80, 20), grey(0x74777c)); side.rotation.y = Math.PI / 2; side.position.set(-6, 10, 0); scene.add(side);

// seeded random (mulberry32): the effects call Math.random at spawn time
let seedState = 1;
Math.random = () => { seedState |= 0; seedState = (seedState + 0x6d2b79f5) | 0; let t = Math.imul(seedState ^ (seedState >>> 15), 1 | seedState); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };

// ---- the muzzle flash, exactly as weapons.js:114-145 draws it (the function is not exported there): a 16-point star
// on a 32 px canvas, radial gradient white -> #fff2a0 -> #ff9a1a -> clear orange, nearest filtering; a 0.24 m face +
// two 0.4 x 0.14 m side spikes, x1.6 for the big guns; shown 0.05 s (0.035 s on guns over 8 shots a second), a new
// random roll and a 0.8-1.4 size every frame
function flashTex() {
  const c = document.createElement('canvas'); c.width = c.height = 32;
  const x = c.getContext('2d');
  const g = x.createRadialGradient(16, 16, 0, 16, 16, 16);
  g.addColorStop(0, '#ffffff'); g.addColorStop(0.25, '#fff2a0'); g.addColorStop(0.6, '#ff9a1a'); g.addColorStop(1, 'rgba(255,80,0,0)');
  x.fillStyle = g; x.beginPath();
  for (let i = 0; i < 16; i++) { const a = (i / 16) * Math.PI * 2, r = i % 2 ? 6 : 16; x.lineTo(16 + Math.cos(a) * r, 16 + Math.sin(a) * r); }
  x.fill();
  const t = new THREE.CanvasTexture(c); t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestFilter;
  return t;
}
function makeFlash(big) {
  const grp = new THREE.Group();
  const mat = new THREE.MeshBasicMaterial({ map: flashTex(), transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, fog: false });
  const s = big ? 1.6 : 1;
  const face = new THREE.Mesh(new THREE.PlaneGeometry(0.24 * s, 0.24 * s), mat);
  const side1 = new THREE.Mesh(new THREE.PlaneGeometry(0.4 * s, 0.14 * s), mat); side1.rotation.y = Math.PI / 2; side1.position.z = -0.12 * s;
  const side2 = new THREE.Mesh(new THREE.PlaneGeometry(0.4 * s, 0.14 * s), mat); side2.rotation.set(-Math.PI / 2, 0, Math.PI / 2); side2.position.z = -0.12 * s;
  grp.add(face, side1, side2); grp.userData.face = face; grp.visible = false;
  return grp;
}

// ---- the views. eye: the camera at the eye, the muzzle where the Roblox viewmodel's is (camera space, metres; the
// capture passes the measured one). side: 4 m to the right of the shot, looking at its first few metres.
const EYE = new THREE.Vector3(0, 1.6, 6);
let live = null; // { t, flash, flashT, tick(dt), ... }
function aimCam(view, o) {
  const look = new THREE.Vector3(0, 1.6, -15);
  camera.fov = o.fov || FOV; camera.updateProjectionMatrix(); fx.setScale(H / (2 * Math.tan((camera.fov * Math.PI) / 360)));
  if (view === 'eye') { camera.position.copy(EYE); camera.lookAt(look); }
  else if (view === 'side') { const at = o.sideAt || new THREE.Vector3(0.2, 1.45, 4.6); camera.position.set(at.x + (o.sideDist || 4), at.y + 0.4, at.z); camera.lookAt(at); }
  else if (view === 'far') { const at = o.at; camera.position.set(at.x + o.dist * 0.75, at.y + o.dist * 0.35, at.z + o.dist * 0.6); camera.lookAt(at); }
  camera.updateMatrixWorld(true);
}
function muzzleWorld(o) {
  const m = o.muzzle || [0.22, -0.2, -0.85]; // camera-space x right, y up, -z ahead
  return new THREE.Vector3(m[0], m[1], m[2]).applyMatrix4(new THREE.Matrix4().makeRotationFromQuaternion(new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().lookAt(EYE, new THREE.Vector3(0, 1.6, -15), new THREE.Vector3(0, 1, 0))))).add(EYE);
}

const EFFECTS = {
  // the shot: flash + tracer from the muzzle to the back wall (the eye's ray). opts: big, fast, color, thick
  shot(o) {
    const mz = muzzleWorld(o);
    const end = new THREE.Vector3(o.endX ?? 0.4, o.endY ?? 1.5, -15);
    const fast = !!o.fast;
    const flash = makeFlash(!!o.big);
    flash.position.copy(mz); flash.lookAt(mz.clone().add(end.clone().sub(mz).normalize().multiplyScalar(-1)));
    scene.add(flash);
    const color = o.color ?? 0xfff0a0, th = o.thick || (fast ? 0.03 : 0.045), life = fast ? 0.07 : 0.2;
    // pellets: each tracer to its own spot in a disc of radius spread x distance (weapons.js spreadDir)
    const ends = [];
    for (let i = 0; i < (o.pellets || 1); i++) {
      const a = Math.random() * 6.2832, m = Math.sqrt(Math.random()) * (o.spread || 0) * 21;
      ends.push(new THREE.Vector3(end.x + Math.cos(a) * m, end.y + Math.sin(a) * m, end.z));
    }
    if (!o.noTracer) for (const e of ends) fx.tracer(mz.toArray(), e.toArray(), color, th, life);
    return { flash, flashT: fast ? 0.035 : 0.05, extra: () => { for (const e of ends.slice(0, 6)) fx.impact(e.toArray(), [0, 0, 1]); } };
  },
  // a bullet hitting the wall: fx.impact (10 grey squares off the normal) at a spot 3 m in front of the camera
  impact(o) { fx.impact([0, 1.5, o.wallZ ?? -15], [0, 0, 1]); return {}; },
  // sparks off metal (bullets on cars), and the katana parry's hot ones
  sparks(o) { fx.sparks([0, 1.5, -15], [0, 0, -1], o.n || 20, !!o.hot); return {}; },
  // the frag: fx.explosion at radius 7.5 m (it calls the boom.png flipbook, the white pop, sparks and feathers)
  explosion(o) { fx.explosion([0, o.y ?? 1, -6], o.r ?? 7.5); return {}; },
  // the smoke bomb: smokeCloud every frame for dur seconds, r 6.5 m (main.js:2181)
  smoke(o) { const s = { p: [0, 0, -8], r: o.r ?? 6.5 }; return { cloud: s, until: o.dur ?? 10 }; },
};

// effects that wait with setTimeout (the explosion's after-smoke at 650 ms) wait on the fixed clock instead
const realSetTimeout = window.setTimeout.bind(window);
let simTimers = [];
window.setTimeout = (fn, ms = 0, ...a) => (live ? (simTimers.push({ at: live.t + ms / 1000, fn: () => fn(...a) }), 0) : realSetTimeout(fn, ms, ...a));

window.REF = {
  ready: false,
  start(name, view, o = {}) {
    // flush whatever the last shot left (its tracers, squares and sheets would still be in this frame)
    live = null; simTimers = [];
    for (let i = 0; i < 400; i++) fx.update(0.05);
    clearFlipbooks();
    for (const o2 of scene.children.slice()) if (o2.userData && o2.userData.face) scene.remove(o2);
    seedState = o.seed ?? 7;
    if (o.muzzle) o.muzzle = o.muzzle.slice();
    if (o.at) o.at = new THREE.Vector3(...o.at);
    if (o.sideAt) o.sideAt = new THREE.Vector3(...o.sideAt);
    aimCam(view, o);
    live = { t: 0 }; // (first, so timers the effect sets count from its t = 0)
    Object.assign(live, EFFECTS[name](o));
    if (live.extra) live.extra();
    return true;
  },
  advance(t) {
    const L = live;
    while (L.t + DT <= t + 1e-9) {
      L.t += DT;
      for (const tm of simTimers.filter((x) => x.at <= L.t)) { simTimers.splice(simTimers.indexOf(tm), 1); tm.fn(); }
      if (L.cloud && L.t <= L.until) {
        // smokeCloud paces itself by performance.now(): feed it our clock instead
        const realNow = performance.now; L.cloud.fbT = L.cloud.fbT ?? 0; const fake = L.t * 1000;
        performance.now = () => fake; smokeCloud(L.cloud, DT); performance.now = realNow;
      }
      fx.update(DT); updateFlipbooks(DT);
      if (L.flash) L.flashT -= DT;
    }
    if (L.flash) {
      L.flash.visible = L.flashT > 0;
      if (L.flash.visible) { L.flash.userData.face.rotation.z = Math.random() * 6.28; L.flash.scale.setScalar(0.8 + Math.random() * 0.6); }
    }
    renderer.render(scene, camera);
    return L.t;
  },
};

// load the flipbook sheets before the first capture (boom.png, puffsoft.png): spawn one of each far away, wait, clear
(async () => {
  boomSprite([0, -500, 0], 1);
  const fb = flipbooks();
  for (let i = 0; i < 200 && !(fb.boom && fb.boom.ready && fb.soft.ready); i++) await new Promise((r) => setTimeout(r, 50));
  for (const k in fb) fb[k].clear();
  window.REF.ready = true;
})();
