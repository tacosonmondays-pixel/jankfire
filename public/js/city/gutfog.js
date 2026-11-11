// THE GUT'S GROUND FOG: a low pale-red mist you wade through, ankle to waist, drifting in wisps and banks, breathing
// with the beat. The owner: "thicker and be on the ground and a bit more visible around you".
// Two cheap parts, because neither reads as fog alone in this renderer:
//   - PUFFS: a couple of hundred soft upright cards round the camera (one instanced draw), each a wisp 3 to 7 m wide and
//     up to waist high, fat at the floor and thinning to nothing at the top, edges eaten by noise. They stand at fixed
//     spots in the world (wrapped round you, so the same wisps are there when you come back), drift slowly, and slide
//     past each other as you move: that parallax and their height is what makes it fog and not paint. They stand in
//     front of things a few metres off (a lamp's foot, somebody's shins) and you look over them.
//   - SHEETS: two or three big flat quads just over the ground with scrolling noise, a thin patchy haze. They carry the
//     fog past the puffs' reach, are what you see from above (cards are edge-on from there), fill the Big Stomach's
//     bowl over the acid, and spill down the cliff into the border band.
// It is paler and mistier than the Gut's dark red floor, and flushes hot red on the lub; a ring of light runs out
// through it from the Big Heart's roots as the ripple reaches them. Round the roots it pools thicker.
// What keeps a fight readable: it stops at about a metre (heads, chests and guns are over it), one puff is never
// more than GUT_FOG.puff opaque and the sheets together never more than GUT_FOG.cap, a wisp fades as you walk into
// it, and it is all drawn before every other see-through thing (sparks, glass, tracers and outlines stay on top).
// Only in the Gut and its border band; nothing is drawn unless the camera is in or near the Gut.
import * as THREE from 'three';
import { SLICE } from '/shared/city/slice.js';
import { BIG_HEART } from '/shared/city/bigheart.js';

// top: how high the tallest wisps stand (m); puff: the most one wisp covers; cap: the most the sheets cover together;
// reach: how far round you the wisps stand (m); holes: how patchy the sheets are (0 none .. 0.6 mostly holes);
// color / hot: the mist at rest and what it flushes toward on the beat; glow: how hard it flushes; drift: wind;
// near: drawn only within this of the Gut (m)
export const GUT_FOG = { on: true, top: 1.1, puff: 0.38, cap: 0.45, reach: 42, holes: 0.34, glow: 0.8, color: 0xe88a98, hot: 0xff3448, drift: 1, near: 110 };
const LAYERS = [2, 2, 3, 3], PUFFS = [70, 120, 170, 230]; // sheets, wisps: per preset (Potato .. Too HD)
const G0 = SLICE.gut.rect, GY = SLICE.gut.y, BY = SLICE.border.y, ST = SLICE.stomach;

// tileable value noise, two octaves, one channel: the wisps
function noiseTex(n = 128) {
  const d = new Uint8Array(n * n), rnd = (s) => { let x = Math.imul(s ^ 0x9e3779b9, 0x85ebca6b); x ^= x >>> 13; x = Math.imul(x, 0xc2b2ae35); return ((x ^ (x >>> 16)) >>> 0) / 4294967296; };
  const lat = (x, y, per, s) => rnd(((x % per) + per) % per + (((y % per) + per) % per) * 131 + s * 7919);
  const val = (x, y, per, s) => { const xi = Math.floor(x), yi = Math.floor(y), fx = x - xi, fy = y - yi, u = fx * fx * (3 - 2 * fx), v = fy * fy * (3 - 2 * fy);
    return (lat(xi, yi, per, s) * (1 - u) + lat(xi + 1, yi, per, s) * u) * (1 - v) + (lat(xi, yi + 1, per, s) * (1 - u) + lat(xi + 1, yi + 1, per, s) * u) * v; };
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) d[y * n + x] = Math.round(255 * (0.6 * val(x / n * 5, y / n * 5, 5, 1) + 0.28 * val(x / n * 11, y / n * 11, 11, 2) + 0.12 * val(x / n * 23, y / n * 23, 23, 3)));
  const t = new THREE.DataTexture(d, n, n, THREE.RedFormat);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearMipmapLinearFilter; t.generateMipmaps = true; t.needsUpdate = true;
  return t;
}

const VS = `varying vec3 vW; void main() { vec4 w = modelMatrix * vec4(position, 1.0); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`;
const HEAD = `
uniform sampler2D uN; uniform float uT, uBeat, uK, uGlow;
uniform vec3 uCol, uHot, uFogCol; uniform vec2 uFog; uniform vec3 uHeart;
float ghBeat(float t) { return exp(-pow((t - 0.12) / 0.045, 2.0)) + 0.6 * exp(-pow((t - 0.33) / 0.06, 2.0)); }
// the mist's colour: pale at rest, hot on the lub and where the ring from the heart's roots is passing; far off it
// melts into the district's fog
vec3 mist(float body, float ring, float dist) {
  vec3 c = mix(uCol, uHot, clamp(uGlow * (0.45 * uK + 0.9 * ring), 0.0, 1.0)) * (0.8 + 0.3 * body + 0.25 * uGlow * uK);
  return mix(c, uFogCol, smoothstep(uFog.x, uFog.y, dist));
}`;
const FS = HEAD + `
uniform float uA, uCap, uLayer, uKind, uHoles; uniform vec3 uSt; uniform vec4 uRect;
varying vec3 vW;
void main() {
  vec2 p = vW.xz;
  // noise fields sliding over each other; each sheet reads its own patch, so they slide past each other as you move
  float n = 0.45 * texture2D(uN, p * 0.019 + uT * vec2(0.010, 0.006) + uLayer * 0.37).r + 0.3 * texture2D(uN, p * 0.047 - uT * vec2(0.007, 0.012) + uLayer * 0.61).r
    + 0.25 * texture2D(uN, p * 0.15 + uT * vec2(-0.021, 0.027) + uLayer * 0.83).r;
  float lo = uHoles + 0.1 * uLayer, dens = smoothstep(lo, lo + 0.22, n); // patches with clear ground between; thinner higher up
  dens *= 0.4 + 0.6 * smoothstep(0.3, 0.6, texture2D(uN, p * 0.0043 + uT * vec2(0.0021, 0.0013)).r); // banks, 50 m across, wandering the district
  float dh = length(p - uHeart.xy), root = exp(-dh * dh / 420.0); // round the heart's roots it pools
  dens = mix(dens, 0.55 + 0.45 * n, root * 0.8) * (1.0 + 0.4 * root);
  float ring = ghBeat(fract(uBeat - 0.9 - dh / 80.0)) * exp(-dh / 55.0); // the ripple leaves the roots and runs out through the fog
  float mask;
  if (uKind < 0.5) { // the plateau: inside the Gut, a hole over the crater, a soft east edge
    mask = smoothstep(uSt.z - 2.0, uSt.z + 9.0, length(p - uSt.xy)) * (1.0 - smoothstep(uRect.z - 26.0, uRect.z, p.x));
  } else if (uKind < 1.5) { // the border band: all gone 40 m down from the cliff
    mask = (1.0 - smoothstep(-44.0, -6.0, p.y)) * 0.75 * (1.0 - smoothstep(uRect.z - 26.0, uRect.z, p.x));
  } else { // the pool in the Big Stomach
    mask = (1.0 - smoothstep(17.0, 31.0, length(p - uSt.xy))) * 1.5; dens = 0.5 + 0.5 * n;
  }
  vec3 v = vW - cameraPosition; float dist = length(v);
  float a = uA * dens * mask * (0.85 + 0.3 * uK + 0.6 * ring);
  a *= smoothstep(0.4, 1.4, dist) * smoothstep(0.02, 0.3, abs(v.y)); // a sheet fades as it passes your eyes
  a = min(a, uCap);
  if (a < 0.004) discard;
  gl_FragColor = vec4(mist(dens, ring, dist), a);
  #include <colorspace_fragment>
}`;
// a wisp: an upright card that turns to face you, standing on the ground at a fixed spot (wrapped round the camera)
const PVS = `
attribute vec4 aSeed; uniform sampler2D uN; uniform float uT, uK, uR, uTop; uniform vec3 uSt; uniform vec4 uRect; uniform vec2 uY;
varying vec2 vUv; varying vec3 vW; varying vec4 vS; varying float vA;
void main() {
  vec2 home = aSeed.xy * 2.0 * uR + uT * (vec2(0.3, 0.17) + (aSeed.zw - 0.5) * 0.4); // its spot, and the wind
  vec2 rel = mod(home - cameraPosition.xz + uR, 2.0 * uR) - uR, wp = cameraPosition.xz + rel;
  float m = 1.0 - smoothstep(0.7 * uR, uR, max(abs(rel.x), abs(rel.y))); // fades in at the edge of the reach: no popping
  float gut = step(wp.y, -47.0); // on the plateau, or down in the border band
  m *= (1.0 - smoothstep(uRect.z - 26.0, uRect.z, wp.x)) * step(uRect.x + 5.0, wp.x) * step(uRect.y + 5.0, wp.y);
  m *= mix(1.0 - smoothstep(-44.0, -8.0, wp.y), 1.0, gut) * smoothstep(0.5, 3.5, abs(wp.y + 47.0)); // thins out across the border; none straddling the cliff
  m *= smoothstep(uSt.z + 1.0, uSt.z + 8.0, length(wp - uSt.xy)); // none hanging over the crater
  m *= 0.45 + 0.55 * smoothstep(0.3, 0.6, texture2D(uN, wp * 0.0043 + uT * vec2(0.0021, 0.0013)).r); // the same banks as the sheets
  float w = mix(3.0, 7.5, aSeed.z), h = uTop * mix(0.5, 1.15, aSeed.w) * (1.0 + 0.18 * uK); // it rises a little on the beat
  vec3 right = normalize(vec3(viewMatrix[0][0], 0.0, viewMatrix[2][0]));
  vec3 world = vec3(wp.x, mix(uY.y, uY.x, gut) + 0.03, wp.y) + right * (position.x * w) + vec3(0.0, position.y * h, 0.0);
  vUv = vec2(position.x + 0.5, position.y); vW = world; vS = aSeed; vA = m;
  gl_Position = projectionMatrix * viewMatrix * vec4(world, 1.0);
}`;
const PFS = HEAD + `
uniform float uA;
varying vec2 vUv; varying vec3 vW; varying vec4 vS; varying float vA;
void main() {
  float n = 0.6 * texture2D(uN, vUv * vec2(0.42, 0.2) + vS.xy * 9.0 + uT * vec2(0.013, 0.004)).r + 0.4 * texture2D(uN, vUv * vec2(1.3, 0.55) + vS.zw * 5.0 - uT * vec2(0.02, 0.007)).r;
  float fx = 1.0 - smoothstep(0.15, 1.0, abs(vUv.x - 0.5) * 2.0);
  float fy = smoothstep(0.0, 0.2, vUv.y) * (1.0 - smoothstep(0.42, 1.0, vUv.y)); // fattest at shin height, thinning to nothing at the top, soft where it meets the floor
  float body = smoothstep(0.08, 0.6, fx * fy * (0.35 + 1.3 * n)); // the noise eats its edges: a wisp, not an oval
  vec3 v = vW - cameraPosition; float dist = length(v);
  float dh = length(vW.xz - uHeart.xy), root = exp(-dh * dh / 420.0);
  float ring = ghBeat(fract(uBeat - 0.9 - dh / 80.0)) * exp(-dh / 55.0);
  float a = uA * body * vA * (0.85 + 0.3 * uK + 0.5 * ring) * (1.0 + 0.5 * root) * smoothstep(0.5, 2.0, dist); // it thins as you walk into it
  a *= 1.0 - smoothstep(0.3, 0.65, abs(v.y) / dist); // a card looked down on is a pane of glass: from above the sheets are the fog
  if (a < 0.004) discard;
  gl_FragColor = vec4(mist(body, ring, dist), min(a, 0.6));
  #include <colorspace_fragment>
}`;

let F = null;
export function startGutFog(parent) { stopGutFog(); F = { parent, root: null, n: -1, np: -1, sheets: [], puffs: null, tex: null, t: 0 }; }
function clear() {
  if (!F.root) return;
  F.root.removeFromParent();
  for (const m of F.sheets) { m.geometry.dispose(); m.material.dispose(); }
  if (F.puffs) { F.puffs.geometry.dispose(); F.puffs.material.dispose(); }
  F.root = null; F.sheets = []; F.puffs = null;
}
export function stopGutFog() { if (!F) return; clear(); if (F.tex) F.tex.dispose(); F = null; }
const SHARED = { uT: { value: 0 }, uBeat: { value: 0 }, uK: { value: 0 }, uHoles: { value: 0.34 }, uGlow: { value: 0.8 }, uCol: { value: new THREE.Color() }, uHot: { value: new THREE.Color() }, uFogCol: { value: new THREE.Color() }, uFog: { value: new THREE.Vector2(26, 205) },
  uHeart: { value: new THREE.Vector3(BIG_HEART.x, BIG_HEART.z, 0) }, uSt: { value: new THREE.Vector3(ST.x, ST.z, ST.r) }, uRect: { value: new THREE.Vector4(G0[0], G0[1], G0[2], G0[3]) } };
// (re)build for this preset: n sheets a stack, np wisps
function build(n, np) {
  clear();
  F.tex = F.tex || noiseTex();
  F.root = new THREE.Group(); F.root.name = 'gutfog'; F.n = n; F.np = np;
  const sheet = (kind, i, cnt, geo, x, y0, z, h) => {
    const mat = new THREE.ShaderMaterial({ vertexShader: VS, fragmentShader: FS, transparent: true, depthWrite: false, side: THREE.DoubleSide, fog: false,
      uniforms: { ...SHARED, uN: { value: F.tex }, uA: { value: 0 }, uCap: { value: 0 }, uLayer: { value: cnt > 1 ? i / (cnt - 1) : 0 }, uKind: { value: kind } } });
    const m = new THREE.Mesh(geo, mat);
    m.rotation.x = -Math.PI / 2; m.position.set(x, y0, z); m.userData = { y0, h, kind, noShadow: true };
    m.frustumCulled = false; m.renderOrder = kind === 2 ? 3 : -1; // before every other see-through thing (sparks, glass and tracers stay on top); the pool goes over the acid
    F.root.add(m); F.sheets.push(m);
  };
  const w = G0[2] - G0[0], d = -46 - G0[1], gq = new THREE.PlaneGeometry(w, d), bq = new THREE.PlaneGeometry(w, 48), pool = new THREE.CircleGeometry(32, 20);
  for (let i = 0; i < n; i++) sheet(0, i, n, gq, (G0[0] + G0[2]) / 2, GY, G0[1] + d / 2, 0.16 + 0.5 * (n > 1 ? i / (n - 1) : 0.5));
  for (let i = 0; i < 2; i++) sheet(1, i, 2, bq, (G0[0] + G0[2]) / 2, BY, -24, 0.16 + 0.4 * i);
  for (let i = 0; i < 3; i++) sheet(2, i, 3, pool, ST.x, ST.acid, ST.z, 0.5 + 0.75 * i);
  // the wisps: one quad (x -0.5..0.5, y 0..1), np instances, each a seed
  const g = new THREE.InstancedBufferGeometry(), seed = new Float32Array(np * 4);
  g.setAttribute('position', new THREE.BufferAttribute(new Float32Array([-0.5, 0, 0, 0.5, 0, 0, 0.5, 1, 0, -0.5, 1, 0]), 3)); g.setIndex([0, 1, 2, 0, 2, 3]);
  let r = 0x9e3779b9; const rnd = () => { r = Math.imul(r ^ (r >>> 15), 0x2c1b3c6d) + 0x297a2d39 | 0; return ((r ^ (r >>> 13)) >>> 0) / 4294967296; };
  for (let i = 0; i < seed.length; i++) seed[i] = rnd();
  g.setAttribute('aSeed', new THREE.InstancedBufferAttribute(seed, 4)); g.instanceCount = np;
  const pm = new THREE.ShaderMaterial({ vertexShader: PVS, fragmentShader: PFS, transparent: true, depthWrite: false, side: THREE.DoubleSide, fog: false,
    uniforms: { ...SHARED, uN: { value: F.tex }, uA: { value: 0 }, uR: { value: 42 }, uTop: { value: 1 }, uY: { value: new THREE.Vector2(GY, BY) } } });
  F.puffs = new THREE.Mesh(g, pm); F.puffs.frustumCulled = false; F.puffs.renderOrder = -1; F.puffs.userData.noShadow = true;
  F.root.add(F.puffs);
  F.parent.add(F.root);
}

// once a frame (bigheart.js): b is the Gut's clock (gutbeat.js)
export function updateGutFog(dt, S, camera, b) {
  if (!F) return;
  const p = camera.position, dGut = Math.hypot(Math.max(G0[0] - p.x, 0, p.x - G0[2]), Math.max(G0[1] - p.z, 0, p.z - G0[3]));
  const on = GUT_FOG.on && dGut < GUT_FOG.near;
  if (!on) { if (F.root) F.root.visible = false; return; }
  const n = LAYERS[S.preset] ?? 2, np = PUFFS[S.preset] ?? 120;
  if (n !== F.n || np !== F.np) build(n, np);
  F.root.visible = true;
  F.t += dt * GUT_FOG.drift;
  SHARED.uT.value = F.t; SHARED.uBeat.value = b.t % 64; SHARED.uK.value = b.k; SHARED.uHoles.value = GUT_FOG.holes; SHARED.uGlow.value = GUT_FOG.glow;
  SHARED.uCol.value.setHex(GUT_FOG.color); SHARED.uHot.value.setHex(GUT_FOG.hot);
  const cap = 1 - Math.pow(1 - Math.min(0.9, GUT_FOG.cap), 1 / n); // per sheet, so a stack tops out at GUT_FOG.cap
  const e = S.env; if (e) { SHARED.uFogCol.value.copy(e.fog); SHARED.uFog.value.set(e.near, e.far); }
  const swell = 1 + 0.16 * b.k; // it rises a little on the beat
  const seeBorder = p.z > -150, seePool = Math.hypot(p.x - ST.x, p.z - ST.z) < 150; // (the far ones aren't worth their pixels)
  for (const m of F.sheets) { const u = m.material.uniforms, kind = m.userData.kind, k = kind === 2 ? 1.5 : 1; // (the pool in the Big Stomach is the thickest)
    m.visible = kind === 0 || (kind === 1 ? seeBorder : seePool);
    m.position.y = m.userData.y0 + m.userData.h * swell; u.uCap.value = cap * k; u.uA.value = cap * k * 1.3; }
  const pu = F.puffs.material.uniforms; pu.uA.value = GUT_FOG.puff; pu.uR.value = GUT_FOG.reach; pu.uTop.value = GUT_FOG.top;
}
export const gutFogState = () => (F ? { on: !!(F.root && F.root.visible), layers: F.n, sheets: F.sheets.length, puffs: F.np } : null);
