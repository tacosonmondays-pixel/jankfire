// Flames: real moving fire for everything that burns (the rig's flare, burning cars, wrecks, anything that asks).
// upright cards that turn to face you with a flame shader on them: tongues licking up out of noise, cartoon bands
// (an inky red rim, orange, yellow, a white-hot core) and a soft glow round them, all in ONE instanced draw (premultiplied
// alpha: the flame is solid, its glow adds). big ones puff smoke and spit embers, and the pooled lights near them
// flicker (lighting.js). Cars and the like call flameAt() every frame they're burning; one that stops asking goes out
import * as THREE from 'three';
import { G } from './ctx.js';
import { jankUniforms } from './jank.js';
import { fx } from './fx.js';
import { sfx } from './audio.js';
import { dynLight } from './lighting.js';
import { spritesOn, firePuff } from './flipbook.js';

const MAX = 256;
const U = { uTime: { value: 0 }, uSnap: jankUniforms.uSnap };
const VS = `
uniform float uTime; uniform vec2 uSnap;
attribute vec4 aP; attribute vec4 aS;
varying vec2 vUv; varying vec4 vS; varying float vSeed;
#include <fog_pars_vertex>
void main() {
  vec3 c = aP.xyz;
  vec3 fwd = cameraPosition - c; fwd.y *= 0.35; fwd = normalize(fwd + vec3(1e-4, 0.0, 0.0));
  vec3 right = normalize(cross(vec3(0.0, 1.0, 0.0), fwd));
  vec3 up = normalize(mix(vec3(0.0, 1.0, 0.0), cross(fwd, right), 0.3));
  vec2 q = position.xy; // x -0.5..0.5, y 0..1
  vec2 uv = vec2(q.x * 1.7, q.y * 1.3 - 0.15); // the card is a bit bigger than the flame: room for the glow
  vec3 wp = c + right * uv.x * aS.x + up * uv.y * aS.y;
  wp += right * sin(uTime * 2.1 + aP.w * 6.0) * 0.09 * aS.y * max(uv.y, 0.0) * max(uv.y, 0.0); // the top sways
  vUv = uv; vS = aS; vSeed = aP.w;
  vec4 mvPosition = viewMatrix * vec4(wp, 1.0);
  gl_Position = projectionMatrix * mvPosition;
  { vec4 js = gl_Position; js.xyz /= js.w; js.xy = floor(js.xy * uSnap + 0.5) / uSnap; js.xyz *= js.w; gl_Position = js; }
  #include <fog_vertex>
}`;
const FS = `
uniform float uTime;
varying vec2 vUv; varying vec4 vS; varying float vSeed;
#include <fog_pars_fragment>
float fH(vec2 p) { p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float fN(vec2 p) { vec2 i = floor(p), f = fract(p), u = f * f * (3.0 - 2.0 * f);
  return mix(mix(fH(i), fH(i + vec2(1.0, 0.0)), u.x), mix(fH(i + vec2(0.0, 1.0)), fH(i + vec2(1.0, 1.0)), u.x), u.y); }
void main() {
  float x = vUv.x, y = vUv.y, t = uTime * (1.3 + vS.z * 0.5) + vSeed * 13.0;
  float n = fN(vec2(x * 3.1 + vSeed * 7.0, y * 2.4 - t * 2.3)) * 0.62 + fN(vec2(x * 6.8 - vSeed * 3.0, y * 5.2 - t * 4.2)) * 0.38;
  float yy = clamp(y, 0.0, 1.0);
  float w = 0.5 * pow(1.0 - yy, 0.7) * smoothstep(-0.15, 0.06, y) + 0.001; // fat at the bottom, a point at the top
  float xs = x + (n - 0.5) * 0.5 * yy;                                     // licking sideways higher up
  float d = abs(xs) / w;
  float heat = (1.0 - d) * 1.3 - yy * 0.55 + (n - 0.5) * 0.95 - pow(max(0.0, -y) * 6.0, 2.0);
  heat *= vS.w;
  // cartoon bands: an inky rim, red, orange, yellow, the white-hot core
  vec3 col = vec3(0.62, 0.05, 0.02);
  col = mix(col, vec3(1.0, 0.18, 0.05), step(0.14, heat));
  col = mix(col, vec3(1.0, 0.5, 0.06), step(0.36, heat));
  col = mix(col, vec3(1.0, 0.85, 0.22), step(0.62, heat));
  col = mix(col, vec3(1.0, 0.98, 0.78), step(0.9, heat));
  float body = step(0.06, heat);
  float glow = exp(-length(vec2(x * 1.15, (y - 0.32) * 0.85)) * 3.2) * 0.6 * vS.w;
  glow *= smoothstep(0.85, 0.45, abs(x)) * smoothstep(1.15, 0.8, y) * smoothstep(-0.15, 0.05, y); // to nothing at the card's edges
  float fogK = 0.0;
#ifdef USE_FOG
  fogK = smoothstep(fogNear, fogFar, vFogDepth);
#endif
  if (body < 0.5) {
    if (glow < 0.012) discard;
    gl_FragColor = vec4(vec3(1.0, 0.42, 0.08) * glow * (1.0 - fogK), 0.0); // adds
  } else {
    col = pow(col, vec3(2.2)); // (written in sRGB)
#ifdef USE_FOG
    col = mix(col, fogColor, fogK);
#endif
    gl_FragColor = vec4(col, 1.0);
  }
  #include <colorspace_fragment>
}`;

// ---- real fire (owner, 2026-11-11: "I want actual effects"): the same cards, but playing a fire flipbook baked in
// Blender (tools/sprites/blender/fire_flipbook.py: a noise volume rendered in Cycles, 36 looping frames) instead of the
// cartoon shader. Same single draw. Potato, or "drawn smoke + splashes" switched off, keeps the shader flame.
const FS_REAL = `
uniform float uTime; uniform sampler2D uFire;
varying vec2 vUv; varying vec4 vS; varying float vSeed;
#include <fog_pars_fragment>
vec4 cell(float f, vec2 uv) { return texture2D(uFire, (vec2(mod(f, 6.0), 5.0 - floor(f / 6.0)) + uv) / 6.0); }
void main() {
  // the card is 1.7 x 1.3 flame sizes; the picture's flame fills about 0.55 of a cell's width and all its height
  vec2 uv = vec2(vUv.x / 1.7 * 0.94 + 0.5, (vUv.y + 0.15) / 1.3 * 1.12 - 0.02);
  float fogK = 0.0;
#ifdef USE_FOG
  fogK = smoothstep(fogNear, fogFar, vFogDepth);
#endif
  vec4 c = vec4(0.0);
  if (uv.x > 0.01 && uv.x < 0.99 && uv.y > 0.01 && uv.y < 0.99) {
    float f = fract(uTime * (0.38 + vS.z * 0.08) + vSeed * 7.31) * 36.0, f0 = floor(f);
    c = mix(cell(f0, uv), cell(mod(f0 + 1.0, 36.0), uv), f - f0); // frames melt into each other: smooth at any frame rate
    // its foot: not a ruler line where the card meets the ground. the base thins out raggedly over the first tenth
    // or two of its height, licking differently along its width and in time
    float fn = 0.5 + 0.5 * sin(vUv.x * 9.0 + vSeed * 20.0 + uTime * 3.1) * sin(vUv.x * 23.0 - uTime * 5.3 + vSeed * 7.0);
    c *= min(1.0, vS.w) * smoothstep(-0.02, 0.07 + 0.16 * fn, vUv.y); // (premultiplied; also fades in as it catches)
  }
  float glow = exp(-length(vec2(vUv.x * 1.15, (vUv.y - 0.32) * 0.85)) * 3.2) * 0.42 * vS.w;
  glow *= smoothstep(0.85, 0.45, abs(vUv.x)) * smoothstep(1.15, 0.8, vUv.y) * smoothstep(-0.15, 0.05, vUv.y);
  // hotter where the flame is thick and low (a white-yellow heart), deep red at its thin edges and tips: the bake is
  // one orange, the heat comes from how much flame there is
  float heat = smoothstep(0.25, 0.95, c.a) * (1.0 - 0.55 * smoothstep(0.35, 1.0, uv.y));
  vec3 tint = mix(vec3(0.95, 0.3, 0.12), vec3(1.25, 0.95, 0.5), heat); tint = mix(tint, vec3(1.5, 1.4, 1.1), smoothstep(0.75, 1.0, heat));
  float a = min(1.0, c.a * 1.5); // solid enough to read against a bright sky and bright sand
  vec3 col = c.rgb * tint * (a / max(c.a, 0.001)) + vec3(1.0, 0.42, 0.08) * glow * (1.0 - a); // + a warm halo that only adds
  if (a + glow < 0.012) discard;
  gl_FragColor = vec4(col * (1.0 - fogK), a * 0.92 * (1.0 - fogK));
}`;
let realMat = null, toonMat = null, fireTex = null, fireState = 0; // 0 not asked, 1 loading, 2 ready, 3 failed
function realFire() {
  const S = G.settings || {};
  if (S.jank === 0 || S.fxSprites === false || fireState === 3) return false;
  if (!fireState) { fireState = 1; fireTex = new THREE.TextureLoader().load('/sprites/fire.png', () => { fireState = 2; }, undefined, () => { fireState = 3; }); fireTex.colorSpace = THREE.NoColorSpace; fireTex.generateMipmaps = false; fireTex.minFilter = THREE.LinearFilter; }
  return fireState === 2;
}
let mesh = null, aP = null, aS = null;
function build() {
  if (mesh) return mesh;
  const base = new THREE.PlaneGeometry(1, 1).translate(0, 0.5, 0);
  const geo = new THREE.InstancedBufferGeometry();
  geo.index = base.index; geo.setAttribute('position', base.attributes.position); geo.setAttribute('uv', base.attributes.uv);
  aP = new THREE.InstancedBufferAttribute(new Float32Array(MAX * 4), 4).setUsage(THREE.DynamicDrawUsage);
  aS = new THREE.InstancedBufferAttribute(new Float32Array(MAX * 4), 4).setUsage(THREE.DynamicDrawUsage);
  geo.setAttribute('aP', aP); geo.setAttribute('aS', aS);
  geo.instanceCount = 0;
  const mat = new THREE.ShaderMaterial({ uniforms: { ...THREE.UniformsUtils.clone(THREE.UniformsLib.fog), ...U }, vertexShader: VS, fragmentShader: FS, fog: true,
    transparent: true, depthWrite: false, blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneMinusSrcAlphaFactor, side: THREE.DoubleSide });
  toonMat = mat;
  realMat = new THREE.ShaderMaterial({ uniforms: { ...THREE.UniformsUtils.clone(THREE.UniformsLib.fog), ...U, uFire: { value: null } }, vertexShader: VS, fragmentShader: FS_REAL, fog: true,
    transparent: true, depthWrite: false, blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneMinusSrcAlphaFactor, side: THREE.DoubleSide });
  mesh = new THREE.Mesh(geo, mat);
  mesh.frustumCulled = false; mesh.renderOrder = 4; mesh.userData.noShadow = true;
  return mesh;
}

// static flames (the map's 'flame' boxes: touching boxes are one fire) and live ones (flameAt)
const stat = []; // { x, y, z, w, h, heat, k, seed, smoke }
const live = new Map(); // key -> { x, y, z, w, h, heat, k, seed, seen, slot }
const R = (k = 1) => (Math.random() * 2 - 1) * k;
export function clearMapFlames() { stat.length = 0; }
export function flamesFromBoxes(scene, boxes) {
  if (scene && !build().parent) scene.add(mesh);
  if (!boxes.length) return;
  // group touching boxes (the flare is five boxes stacked into a flame shape)
  const grp = boxes.map((b, i) => i);
  const find = (i) => (grp[i] === i ? i : (grp[i] = find(grp[i])));
  const near = (a, b) => a.min[0] <= b.max[0] + 0.3 && b.min[0] <= a.max[0] + 0.3 && a.min[1] <= b.max[1] + 0.3 && b.min[1] <= a.max[1] + 0.3 && a.min[2] <= b.max[2] + 0.3 && b.min[2] <= a.max[2] + 0.3;
  for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) if (near(boxes[i], boxes[j])) grp[find(i)] = find(j);
  const sets = new Map();
  boxes.forEach((b, i) => { const r = find(i); if (!sets.has(r)) sets.set(r, [Infinity, Infinity, Infinity, -Infinity, -Infinity, -Infinity]); const a = sets.get(r); for (let k = 0; k < 3; k++) { a[k] = Math.min(a[k], b.min[k]); a[k + 3] = Math.max(a[k + 3], b.max[k]); } });
  for (const a of sets.values()) {
    const cx = (a[0] + a[3]) / 2, cz = (a[2] + a[5]) / 2, w = Math.max(a[3] - a[0], a[5] - a[2]), h = a[4] - a[1];
    stat.push({ x: cx, y: a[1] - h * 0.05, z: cz, w: w * 1.25, h: h * 1.35, heat: 1, k: 1, seed: Math.random(), smoke: h > 2.5 });
    // a couple of smaller tongues round the big ones, so it isn't one card
    if (h > 2) for (let i = 0; i < 2; i++) stat.push({ x: cx + R(w * 0.25), y: a[1], z: cz + R(w * 0.25), w: w * 0.7, h: h * (0.6 + Math.random() * 0.25), heat: 1.2, k: 1, seed: Math.random(), smoke: false });
  }
}
// a fire that lasts while you keep asking for it: key (one per thing burning), p = where its base is, w / h its size
export function flameAt(key, p, w = 1, h = 1.6, heat = 1) {
  let f = live.get(key);
  if (!f) { f = { seed: Math.random(), k: 0, slot: -1 }; live.set(key, f); }
  f.x = p[0]; f.y = p[1]; f.z = p[2]; f.w = w; f.h = h; f.heat = heat; f.seen = performance.now();
}

let smokeT = 0, crackT = 0;
const LIGHT_SLOTS = 4;
const slots = new Array(LIGHT_SLOTS).fill(null);
export function updateFlames(dt) {
  if (!mesh) return;
  const now = performance.now();
  U.uTime.value = (now / 1000) % 3600;
  { const want = realFire() ? realMat : toonMat; if (want === realMat) realMat.uniforms.uFire.value = fireTex; if (mesh.material !== want) mesh.material = want; } // real fire or the cartoon shader (Potato / switched off / still loading)
  const cam = G.camera && G.camera.position, P = fx.parts && fx.parts();
  let n = 0, nearD = 1e9;
  const put = (f, k) => {
    if (n >= MAX) return;
    aP.array.set([f.x, f.y, f.z, f.seed], n * 4);
    const fl = 0.92 + 0.08 * Math.sin(now * 0.013 + f.seed * 40) + 0.05 * Math.sin(now * 0.031 + f.seed * 9); // a flicker in its size
    aS.array.set([f.w * (0.6 + 0.4 * k), f.h * k * fl, f.heat, Math.min(1, k * 1.4)], n * 4);
    n++;
    if (cam) nearD = Math.min(nearD, Math.hypot(f.x - cam.x, f.y - cam.y, f.z - cam.z) - f.h);
  };
  for (const f of stat) put(f, 1);
  for (const [key, f] of live) {
    const on = now - f.seen < 450; // (generous: a slow frame mustn't put it out)
    f.k += ((on ? 1 : 0) - f.k) * Math.min(1, dt * (on ? 4 : 2.5)); // grows in, dies down
    if (!on && f.k < 0.03) { if (f.slot >= 0) { dynLight(f.slot, null); slots[f.slot] = null; } live.delete(key); continue; }
    put(f, f.k);
  }
  aP.needsUpdate = true; aS.needsUpdate = true;
  mesh.geometry.instanceCount = n;
  // live fires get a flickering light (the lighting pool's spare slots), nearest ones first
  if (live.size) {
    for (const f of live.values()) if (f.slot < 0) { const i = slots.indexOf(null); if (i >= 0) { slots[i] = f; f.slot = i; } }
    for (const f of live.values()) if (f.slot >= 0) dynLight(f.slot, [f.x, f.y + f.h * 0.4, f.z], 0xff7a1a, Math.min(1, f.k) * (0.8 + 0.2 * Math.sin(now * 0.02 + f.seed * 30)));
  }
  // smoke off the big ones, embers off all of them, a crackle when you're close
  smokeT -= dt;
  if (P && smokeT <= 0) {
    smokeT = 0.07;
    const soft = spritesOn(); // real smoke off the fire (flipbook.js) instead of dark squares, half as many puffs
    if (soft) {
      for (const f of stat) if (f.smoke && cam && Math.hypot(f.x - cam.x, f.z - cam.z) < 260 && Math.random() < 0.5) firePuff(f.x + R(f.w * 0.2), f.y + f.h * 0.9, f.z + R(f.w * 0.2), R(0.6), 2 + Math.random() * 1.5, R(0.6), 3 + Math.random() * 2, f.w * 0.5, f.w * 1.5);
      for (const f of live.values()) if (f.k > 0.3 && Math.random() < 0.25) firePuff(f.x + R(0.3), f.y + f.h, f.z + R(0.3), R(0.4), 1.6 + Math.random(), R(0.4), 2.2 + Math.random(), 0.6, f.w * 2.4);
    }
    for (const f of stat) if (!soft && f.smoke && cam && Math.hypot(f.x - cam.x, f.z - cam.z) < 260) P.smoke.spawn(f.x + R(f.w * 0.2), f.y + f.h * 0.9, f.z + R(f.w * 0.2), R(0.6), 2 + Math.random() * 1.5, R(0.6), 3 + Math.random() * 2, f.w * 0.35, f.w * 1.1, 0x3a3434, 0x1a1616, 0.4, -0.35, 0.3);
    for (const f of live.values()) if (!soft && f.k > 0.3 && Math.random() < 0.5) P.smoke.spawn(f.x + R(0.3), f.y + f.h, f.z + R(0.3), R(0.4), 1.6 + Math.random(), R(0.4), 2.2 + Math.random(), 0.4, f.w * 2.2, 0x2a2626, 0x0e0c0c, 0.55, -0.4, 0.4);
    const all = stat.length + live.size;
    if (all) for (let i = 0; i < 2; i++) {
      const f = Math.random() * all < stat.length ? stat[(Math.random() * stat.length) | 0] : [...live.values()][(Math.random() * live.size) | 0];
      if (f && cam && Math.hypot(f.x - cam.x, f.z - cam.z) < 80) P.fire.spawn(f.x + R(f.w * 0.3), f.y + f.h * 0.5, f.z + R(f.w * 0.3), R(1), 2 + Math.random() * 3, R(1), 0.6 + Math.random() * 0.6, 0.08, 0.02, 0xfff2b0, 0xff3a00, 1, -1, 0.5);
    }
  }
  crackT -= dt;
  if (crackT <= 0 && nearD < 9) { crackT = 0.08 + Math.random() * 0.25; sfx.crackle(null, Math.max(0.15, 1 - nearD / 9)); }
}
export function flameInfo() { return { stat: stat.length, live: live.size, drawn: mesh ? mesh.geometry.instanceCount : 0, real: !!(mesh && mesh.material === realMat), sheet: fireState }; }
