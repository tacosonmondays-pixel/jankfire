// OVERDUE city test page (/storytest.html?city=stress&jank=3): the streamer on its own, with a walk / fly / grapple
// controller on the shared physics, a perf HUD (F3) and hooks for the Playwright fly-through (window.__city).
// Not part of the game's boot: the live game never loads this file. WP0's story shell takes the streamer from here.
import * as THREE from 'three';
import { CityStream } from './stream.js';
import { CITIES, RINGS } from '/shared/city/plan.js';
import { PH } from '/shared/physics.js';
import { jankUniforms } from '../jank.js';
import { propEnv } from './props.js';
import { stepGimmicks } from '/shared/city/gimmicks.js';
import { cityUniforms } from './mats.js';
import '/shared/city/slice.js'; // registers the slice city (The Bottom + The Gut + the Commute)

const Q = new URLSearchParams(location.search);
const city = CITIES[Q.get('city')] ? Q.get('city') : (CITIES.slice ? 'slice' : 'stress');
const SCALE = [0.22, 0.36, 0.6, 1], SNAP = [160, 220, 360, 0];
let preset = Math.max(0, Math.min(3, Number(Q.get('jank') ?? 1) | 0));

const canvas = document.getElementById('c');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, powerPreference: 'high-performance' });
renderer.setPixelRatio(1);
renderer.shadowMap.type = THREE.PCFShadowMap;
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0xc8a8c8, 100, 800);
const camera = new THREE.PerspectiveCamera(95, 1, 0.1, 2200);
camera.rotation.order = 'YXZ';
const hemi = new THREE.HemisphereLight(0xcfe8ff, 0x7a4a6a, 1.5); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xfff0dd, 1.8); sun.position.set(60, 100, -70); scene.add(sun); scene.add(sun.target);
sun.shadow.mapSize.set(2048, 2048); Object.assign(sun.shadow.camera, { left: -90, right: 90, top: 90, bottom: -90, near: 1, far: 400 }); sun.shadow.bias = -0.0006; sun.shadow.normalBias = 0.04;
propEnv(renderer);

// sky dome (vertex colours, painted from the blended district sky)
const skyGeo = new THREE.SphereGeometry(2000, 16, 10);
const sky = new THREE.Mesh(skyGeo, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide, fog: false, depthWrite: false }));
skyGeo.setAttribute('color', new THREE.Float32BufferAttribute(new Float32Array(skyGeo.attributes.position.count * 3), 3));
scene.add(sky);
function paintSky(env) {
  const pos = skyGeo.attributes.position, col = skyGeo.attributes.color, c = new THREE.Color();
  for (let i = 0; i < pos.count; i++) {
    const y = pos.getY(i) / 2000;
    if (y > 0) c.copy(env.mid).lerp(env.top, Math.min(1, y * 1.8)); else c.copy(env.mid).lerp(env.bot, Math.min(1, -y * 3));
    col.setXYZ(i, c.r, c.g, c.b);
  }
  col.needsUpdate = true;
}

const boxes = [];
const stream = new CityStream({ scene, city, preset, boxes });
if (Q.has('storm')) stream.clock = () => 20 + performance.now() / 1e6; // test knob: storm=1 holds a paper storm on
const C = CITIES[city];
// the player: feet position, like the game's
const me = { pos: [...(C.spawn || [0, 2, 0])], vel: [0, 0, 0], yaw: Q.has('yaw') ? +Q.get('yaw') : 0, pitch: Q.has('pitch') ? +Q.get('pitch') : 0, ground: false, fly: Q.get('fly') === '1', hook: null, held: 0 };
if (Q.has('at')) { const a = Q.get('at').split(',').map(Number); if (a.length >= 3 && a.every(Number.isFinite)) me.pos = a; }

function setPreset(i) {
  preset = i; stream.setPreset(i);
  renderer.shadowMap.enabled = i >= 2; sun.castShadow = i >= 2;
  jankUniforms.uSnap.value.set(SNAP[i] ? SNAP[i] * (innerWidth / innerHeight) / 2 : 1e5, SNAP[i] ? SNAP[i] / 2 : 1e5);
  resize();
  scene.traverse((o) => { if (o.material) o.material.needsUpdate = true; });
}
function resize() {
  const k = SCALE[preset] * (Q.has('res') ? Math.max(0.05, Math.min(1, +Q.get('res') || 1)) : 1); // res=: a test knob (same rings, fewer pixels)
  renderer.setSize(Math.max(80, innerWidth * k | 0), Math.max(60, innerHeight * k | 0), false);
  camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix();
}
addEventListener('resize', resize);
setPreset(preset);

// ---------------------------------------------------------------- input
const keys = new Set();
let showPerf = Q.get('perf') !== '0';
addEventListener('keydown', (e) => {
  keys.add(e.code);
  if (e.code === 'KeyF') { me.fly = !me.fly; me.vel[1] = 0; }
  if (e.code === 'F3') { e.preventDefault(); showPerf = !showPerf; }
  if (/^Digit[1-4]$/.test(e.code)) setPreset(+e.code.slice(5) - 1);
  if (e.code === 'KeyE') me.useDown = true;
  if (e.code === 'KeyT') { me.pos = [...(C.spawn || [0, 2, 0])]; me.vel = [0, 0, 0]; }
});
addEventListener('keyup', (e) => { keys.delete(e.code); if (e.code === 'KeyE') me.hook = null; });
let jumpDown = false; addEventListener('keydown', (e) => { if (e.code === 'Space' && !e.repeat) jumpDown = true; });
canvas.addEventListener('click', () => { if (document.pointerLockElement !== canvas) canvas.requestPointerLock(); else shoot(); });
document.addEventListener('pointerlockchange', () => { document.getElementById('help').style.display = document.pointerLockElement ? 'none' : ''; });
addEventListener('mousemove', (e) => { if (document.pointerLockElement !== canvas) return; me.yaw -= e.movementX * 0.0022; me.pitch = Math.max(-1.55, Math.min(1.55, me.pitch - e.movementY * 0.0022)); });

const fwd = () => [-Math.sin(me.yaw) * Math.cos(me.pitch), Math.sin(me.pitch), -Math.cos(me.yaw) * Math.cos(me.pitch)];
const eyeP = () => [me.pos[0], me.pos[1] + PH.eye, me.pos[2]];
const sparks = [];
const sparkGeo = new THREE.BoxGeometry(0.3, 0.3, 0.3), sparkMat = new THREE.MeshBasicMaterial({ color: 0xffe14d });
function shoot() {
  const h = stream.world.raycast(eyeP(), fwd(), 300);
  if (!h) return null;
  const s = new THREE.Mesh(sparkGeo, sparkMat); s.position.set(...h.point); scene.add(s); sparks.push([s, 0.6]);
  return h;
}
function grapple() {
  const h = stream.world.raycast(eyeP(), fwd(), 140);
  me.hook = h ? h.point : null;
}
// the gimmicks' juice: callouts in the game's voice, socks raining off the washing line, a red flash in the acid
const socks = [], sockGeo = new THREE.BoxGeometry(0.25, 0.08, 0.5), sockMats = [0xffffff, 0xff7ab0, 0xffe14d, 0x4fd8c6].map((c) => new THREE.MeshLambertMaterial({ color: c }));
let lastCarry = 0, hp = 100;
function gimFx(e) {
  if (e.kind === 'zipOn') callout('ZIPLINE!');
  else if (e.kind === 'zipOff' && e.speed > 16) callout('SOCK RUN');
  else if (e.kind === 'sock') { const m = new THREE.Mesh(sockGeo, sockMats[(Math.random() * 4) | 0]); m.position.set(...e.p); m.rotation.set(Math.random() * 3, Math.random() * 3, 0); scene.add(m); socks.push([m, 2.5, (Math.random() - 0.5) * 2, (Math.random() - 0.5) * 2]); }
  else if (e.kind === 'bounce') callout(e.v > 30 ? 'BIG BREATH' : 'LUNG!');
  else if (e.kind === 'pad') callout(e.name || 'BOING');
  else if (e.kind === 'slip') { me.vel[1] = Math.max(me.vel[1], 6.5); me.vel[0] *= 1.6; me.vel[2] *= 1.6; me.ground = false; callout(e.what === 'marbles' ? 'MARBLES!' : 'PEELED'); }
  else if (e.kind === 'slide' && e.v > 18 && calloutT <= 0) callout(e.v > 26 ? 'BANISTER BURN' : 'THE BANISTER');
  else if (e.kind === 'carry' && performance.now() - lastCarry > 4000) { callout(e.name === 'PERISTALSIS' ? 'THE STREET IS DIGESTING YOU' : 'IT ONLY GOES DOWN'); lastCarry = performance.now(); }
  else if (e.kind === 'surf') callout('RIDING THE BEAT');
  else if (e.kind === 'acid') { hp -= e.dmg; if (hp <= 0) { hp = 100; me.pos = [...(C.spawn || [0, 2, 0])]; me.vel = [0, 0, 0]; callout('DIGESTED'); } else if (calloutT <= 0) callout("YOU'RE BEING DIGESTED"); }
  else if (e.kind === 'hot' && calloutT <= 0) callout('HOT ZONE: DO NOT LICK');
}
function stepSocks(dt) {
  for (let i = socks.length - 1; i >= 0; i--) {
    const s = socks[i]; s[1] -= dt; s[0].position.y -= 3 * dt; s[0].position.x += s[2] * dt; s[0].position.z += s[3] * dt; s[0].rotation.x += dt * 4;
    if (s[1] <= 0) { s[0].removeFromParent(); socks.splice(i, 1); }
  }
}
let calloutT = 0;
function callout(t) { const el = document.getElementById('callout'); el.textContent = t; el.style.opacity = 1; calloutT = 1.6; }

// ---------------------------------------------------------------- step
function step(dt) {
  // replaying a swing (tools/city/swingclip.cjs feeds window.__replay = { pts: [[x, y, z, on, ax, ay, az] at 30 Hz] }
  // from tools/city/grapple.mjs --path: the real rope's flight): fly the camera along it, rope on, facing the way you go
  if (window.__replay) {
    const R = window.__replay, nowR = performance.now(); if (R.t0 == null) { R.t0 = nowR; R.wall0 = Date.now(); } R.t = (nowR - R.t0) / 1000 * (R.speed || 1); // wall clock: a slow frame drops frames, never slows the swing
    const f = R.t * 30, i = Math.floor(f);
    if (i >= R.pts.length - 1) { R.done = true; R.wall1 = Date.now(); window.__replayed = R; window.__replay = null; me.hook = null; return; }
    const a = R.pts[i], b = R.pts[i + 1], u = f - i;
    for (let k = 0; k < 3; k++) me.pos[k] = a[k] + (b[k] - a[k]) * u;
    me.hook = a[3] ? [a[4], a[5], a[6]] : null;
    const j = Math.min(R.pts.length - 1, i + 8), vx = R.pts[j][0] - a[0], vz = R.pts[j][2] - a[2];
    if (Math.hypot(vx, vz) > 0.3) { let d = Math.atan2(-vx, -vz) - me.yaw; d = Math.atan2(Math.sin(d), Math.cos(d)); me.yaw += d * Math.min(1, dt * 2.5); }
    me.pitch += ((me.hook ? 0.12 : -0.1) - me.pitch) * Math.min(1, dt * 2);
    return;
  }
  const f = [-Math.sin(me.yaw), 0, -Math.cos(me.yaw)], r = [Math.cos(me.yaw), 0, -Math.sin(me.yaw)];
  let ix = 0, iz = 0;
  if (keys.has('KeyW')) iz += 1; if (keys.has('KeyS')) iz -= 1; if (keys.has('KeyD')) ix += 1; if (keys.has('KeyA')) ix -= 1;
  if (window.__auto) { ix = window.__auto.x || 0; iz = window.__auto.z || 0; } // the fly-through drives this
  if (me.fly) {
    const sp = (keys.has('ShiftLeft') || (window.__auto && window.__auto.fast)) ? 120 : 40, d = fwd();
    for (let k = 0; k < 3; k++) me.pos[k] += (d[k] * iz + [r[0], 0, r[2]][k] * ix) * sp * dt;
    if (keys.has('Space')) me.pos[1] += sp * dt;
    return;
  }
  if (!stream.ready(me.pos[0], me.pos[2])) { me.held += dt; return; } // the ground here isn't in yet: wait for it
  // the district gimmicks: ziplines, moving streets, lungs, acid (E grabs a line if one's in reach, else grapples)
  const use = me.useDown || (window.__auto && window.__auto.use); me.useDown = false;
  const wasZip = !!me.zip;
  const ev = stepGimmicks(me, stream.triggers(), dt, { use, jump: jumpDown, face: fwd(), beat: cityUniforms.uBeat.value, sliding: keys.has('ControlLeft') });
  jumpDown = false;
  for (const e of ev) gimFx(e);
  if (me.zip) return; // riding a line: it moves you
  if (use && !wasZip && !ev.some((e) => e.kind === 'zipOn' || e.kind === 'zipOff')) grapple();
  const sp = keys.has('ShiftLeft') ? 11 : 7;
  const tx = (f[0] * iz + r[0] * ix) * sp, tz = (f[2] * iz + r[2] * ix) * sp;
  const acc = me.ground ? 60 : 14;
  me.vel[0] += Math.max(-acc * dt, Math.min(acc * dt, tx - me.vel[0]));
  me.vel[2] += Math.max(-acc * dt, Math.min(acc * dt, tz - me.vel[2]));
  me.vel[1] -= 24 * dt;
  if (me.hook) { // grapple: a stiff spring to the hook point
    const d = [me.hook[0] - me.pos[0], me.hook[1] - me.pos[1] - 1, me.hook[2] - me.pos[2]], l = Math.hypot(...d) || 1;
    for (let k = 0; k < 3; k++) me.vel[k] += (d[k] / l) * 70 * dt;
    me.vel[1] += 24 * dt * 0.6;
    if (l < 2.5) me.hook = null;
  }
  if (keys.has('Space') && me.ground) { me.vel[1] = 8.5; me.ground = false; }
  const res = stream.world.movePlayer(me.pos, me.vel, dt, me.ground);
  me.ground = !!res.ground;
  if (me.pos[1] < -60) { me.pos = [...(C.spawn || [0, 2, 0])]; me.vel = [0, 0, 0]; callout('INTO THE VOID'); }
}

// the rope: a yellow cord from your hand to the hook point
const rope = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.05, 1), new THREE.MeshBasicMaterial({ color: 0xffe14d })); rope.visible = false; scene.add(rope);
const ropeA = new THREE.Vector3(), ropeB = new THREE.Vector3();
function drawRope() {
  rope.visible = !!me.hook;
  if (!me.hook) return;
  const f = fwd(), rx = Math.cos(me.yaw), rz = -Math.sin(me.yaw);
  ropeA.set(me.pos[0] + f[0] * 0.6 + rx * 0.35, me.pos[1] + 1.25, me.pos[2] + f[2] * 0.6 + rz * 0.35); ropeB.set(...me.hook);
  rope.position.copy(ropeA).lerp(ropeB, 0.5); rope.scale.set(1, 1, ropeA.distanceTo(ropeB)); rope.lookAt(ropeB);
}
// ---------------------------------------------------------------- loop
const perf = document.getElementById('perf');
let last = performance.now(), fps = 60, frameMax = 0, frames = 0;
const fogC = new THREE.Color();
function frame() {
  const now = performance.now(), dt = Math.min(0.05, (now - last) / 1000); last = now;
  fps = fps * 0.95 + (1 / Math.max(1e-3, dt)) * 0.05; frames++;
  if (frames > 30) frameMax = Math.max(frameMax, dt * 1000);
  step(dt); stepSocks(dt);
  drawRope();
  camera.position.set(...eyeP()); camera.rotation.set(me.pitch, me.yaw, 0);
  stream.update(camera, dt);
  const env = stream.env;
  if (stream.weather.started) callout('PAPER STORM');
  if (env) {
    scene.fog.color.copy(env.fog); scene.fog.near = env.near; scene.fog.far = env.far;
    paintSky(env); renderer.setClearColor(env.fog);
    hemi.color.copy(env.hemi[0]); hemi.groundColor.copy(env.hemi[1]); hemi.intensity = env.hemi[2];
    sun.color.copy(env.sun[0]); sun.intensity = env.sun[1];
  }
  sky.position.copy(camera.position);
  sun.target.position.set(me.pos[0], me.pos[1], me.pos[2]); sun.position.set(me.pos[0] + 60, me.pos[1] + 100, me.pos[2] - 70);
  for (let i = sparks.length - 1; i >= 0; i--) { sparks[i][1] -= dt; if (sparks[i][1] <= 0) { sparks[i][0].removeFromParent(); sparks.splice(i, 1); } }
  if (calloutT > 0 && (calloutT -= dt) <= 0) document.getElementById('callout').style.opacity = 0;
  renderer.render(scene, camera);
  if (showPerf && frames % 10 === 0) {
    const s = stream.stats(), i = renderer.info, mem = performance.memory;
    perf.style.display = '';
    perf.innerHTML = `<b>${CITIES[city].name}</b> · ${RINGS[preset].name} · ${env && env.district ? env.district.name : ''}\n` +
      `fps ${fps.toFixed(0)}  worst ${frameMax.toFixed(0)} ms\n` +
      `draw calls <b>${i.render.calls}</b>  tris <b>${(i.render.triangles / 1000).toFixed(0)}k</b>\n` +
      `chunks ${s.chunks}  near ${s.near}  mid ${s.mid}  far ${s.far}\n` +
      `collision ${s.collision} (${s.boxes} boxes)  props ${s.props}\n` +
      `geo ${s.geoMB} MB  heap ${mem ? (mem.usedJSHeapSize / 1048576).toFixed(0) + ' MB' : '?'}\n` +
      `build avg ${s.avgBuildMs} ms max ${s.maxBuildMs}  upload max ${s.maxUploadMs}\n` +
      `pos ${me.pos.map((v) => v.toFixed(0)).join(', ')}${me.fly ? '  FLY' : ''}`;
  } else if (!showPerf) perf.style.display = 'none';
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

window.__city = { hp: () => hp, stream, scene, camera, renderer, me, setPreset, shoot, callout, city, resetWorst: () => { frameMax = 0; frames = 0; }, worst: () => frameMax, fps: () => fps };
