// Liquid materials: the shaders and one material per liquid (water, the seas, the lake, dye, oil, lava, acid, bile,
// slime, cola), every one animated through one shared set of uniforms. pure look (three + the Potato snap), so anything
// can use it: the maps (liquids.js builds their meshes and splashes), Floor Is Lava (chaos.js), the OVERDUE city's acid
// and bile (city/mats.js: liquidMaterial('acid', { city: true })). call tickLiquids(seconds) once a frame if
// liquids.js isn't running (it does it for the game)
import * as THREE from 'three';
import { jankUniforms } from './jank.js';

// ------------------------------------------------------------ the liquids (keys = map box materials)
// kind: water | lava | goo. water: deep / shal = colours, a = alpha in the shallows..deep, amp / len = wave height and
// length (m), swell = big rolling sea (whitecaps, waves calm in the shallows), foam, spark (sun glitter), refl (sky),
// sheen = oil's rainbow, caus = caustics. lava / goo: hot / mid / crust / edge colours, crustK = how much of it has a
// crust, flow speed, bub = how often it burps, glow
const W = (deep, shal, o = {}) => ({ kind: 'water', deep, shal, a: [0.5, 0.9], amp: 0.03, len: 3, swell: 0, foam: 1, spark: 1, refl: 0.5, sheen: 0, caus: 1, ...o });
export const LIQ = {
  water: W(0x0e5fd8, 0x4fe6ff, { a: [0.42, 0.88] }),
  poolwater: W(0x1296c8, 0x9cf6ff, { a: [0.32, 0.8], amp: 0.02, len: 2.4, foam: 0.7 }),
  sea: W(0x0a6cc8, 0x34f2d6, { a: [0.36, 0.95], amp: 0.34, len: 24, swell: 1, refl: 0.55 }),
  seanorth: W(0x0a2c44, 0x2a7a84, { a: [0.72, 0.97], amp: 0.62, len: 32, swell: 1, foam: 1.2, spark: 0.8, refl: 0.6, caus: 0.4 }),
  seawater: W(0x06142a, 0x1a4e6e, { a: [0.82, 0.98], amp: 0.22, len: 18, swell: 0.6, foam: 0.7, spark: 0.8, refl: 0.7, caus: 0.3 }),
  lakewater: W(0x02060e, 0x0d2638, { a: [0.78, 0.97], amp: 0.06, len: 7, foam: 0.4, spark: 1, refl: 0.8, caus: 0.25 }),
  oil: W(0x040306, 0x120e18, { a: [0.94, 0.99], amp: 0.62, len: 32, swell: 1, foam: 0, spark: 0.7, refl: 0.85, sheen: 1, caus: 0 }), // (rides the north sea's waves)
  // the Bazaar's dye vats: knee deep colour, nearly opaque
  dyemagenta: W(0xb0087e, 0xff4fd8, { a: [0.88, 0.97], amp: 0.012, len: 1.4, foam: 0.5, spark: 0.7, refl: 0.3, caus: 0.5 }),
  dyeyellow: W(0xd89a00, 0xffe14d, { a: [0.88, 0.97], amp: 0.012, len: 1.4, foam: 0.5, spark: 0.7, refl: 0.3, caus: 0.5 }),
  dyeblue: W(0x0a2ab8, 0x4f8aff, { a: [0.88, 0.97], amp: 0.012, len: 1.4, foam: 0.5, spark: 0.7, refl: 0.3, caus: 0.5 }),
  dyemint: W(0x14a070, 0x7dffc8, { a: [0.88, 0.97], amp: 0.012, len: 1.4, foam: 0.5, spark: 0.7, refl: 0.3, caus: 0.5 }),
  dyetoyred: W(0xa80818, 0xff3a3a, { a: [0.88, 0.97], amp: 0.012, len: 1.4, foam: 0.5, spark: 0.7, refl: 0.3, caus: 0.5 }),
  dyetoyteal: W(0x007a86, 0x3ff0f0, { a: [0.88, 0.97], amp: 0.012, len: 1.4, foam: 0.5, spark: 0.7, refl: 0.3, caus: 0.5 }),
  lava: { kind: 'lava', hot: 0xfff07a, mid: 0xff5a10, crust: 0x24080e, edge: 0x6a1a10, crustK: 0.62, flow: 1, bub: 0.22, glow: 1.15, amp: 0.03 },
  acid: { kind: 'goo', hot: 0xeaff6a, mid: 0x66e010, crust: 0x1f5a12, edge: 0xb8ff3a, crustK: 0.28, flow: 0.6, bub: 0.5, glow: 0.9, amp: 0.05 },
  bile: { kind: 'goo', hot: 0xf4ff8a, mid: 0x9ad82a, crust: 0x4a6a14, edge: 0xd8ff6a, crustK: 0.35, flow: 0.4, bub: 0.35, glow: 0.75, amp: 0.01 },
  slime: { kind: 'goo', hot: 0xb0ff6a, mid: 0x39ff14, crust: 0x127a24, edge: 0x7dff4f, crustK: 0.3, flow: 0.5, bub: 0.45, glow: 0.85, amp: 0.03 },
  cola: { kind: 'goo', hot: 0x8a3a14, mid: 0x3a1206, crust: 0xe8c898, edge: 0xfff0d8, crustK: 0.42, flow: 0.5, bub: 0.8, glow: 0.55, amp: 0.02 }, // the crust is the fizz
};
export const DROP = new Set(['surf', 'foam']); // old painted-on foam strips: the shore map draws real foam now
export const isLiq = (k) => Object.hasOwn(LIQ, k);
// a box is a liquid surface if it's one of ours and lies flat (thin glass walls that borrowed 'water' stay glass).
// lava and goo also come as falls (thin upright boxes): they flow down
export function liquidBox(b) {
  if (DROP.has(b.mat)) return true;
  if (b.mat === 'flame') return true;
  if (!isLiq(b.mat)) return false;
  const sx = b.max[0] - b.min[0], sy = b.max[1] - b.min[1], sz = b.max[2] - b.min[2];
  if (LIQ[b.mat].kind !== 'water') return Math.max(sx, sz) >= 0.25;
  return Math.min(sx, sz) >= 0.6 && sy <= Math.max(1.6, Math.min(sx, sz));
}

// ------------------------------------------------------------ shared uniforms (one set: every liquid material points at them)
export const SH = {
  uTime: { value: 0 }, uQ: { value: 3 },
  uMask: { value: null }, uMR: { value: new THREE.Vector4(1e9, 1e9, 0, 0) }, // shore map: rect x0, z0, 1/w, 1/h
  uSun: { value: new THREE.Vector3(0.5, 0.6, -0.6).normalize() }, uSunC: { value: new THREE.Color(0xfff6d8) },
  uSkyT: { value: new THREE.Color(0x6ab8ff) }, uSkyM: { value: new THREE.Color(0xcfe8ff) }, uNight: { value: 0 },
};
export const SHORE = 8, DEPTH = 6; // metres the shore map's distance and depth channels cover

const NOISE = `
float lqH(vec2 p) { p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
vec3 lqN(vec2 p) { // value noise + its gradient
  vec2 i = floor(p), f = fract(p), u = f * f * (3.0 - 2.0 * f), du = 6.0 * f * (1.0 - f);
  float a = lqH(i), b = lqH(i + vec2(1.0, 0.0)), c = lqH(i + vec2(0.0, 1.0)), d = lqH(i + vec2(1.0, 1.0));
  return vec3(a + (b - a) * u.x + (c - a) * u.y + (a - b - c + d) * u.x * u.y, du * (vec2(b - a, c - a) + (a - b - c + d) * u.yx));
}
float lqF(vec2 p) { return lqN(p).x * 0.55 + lqN(p * 2.03 + 7.1).x * 0.3 + lqN(p * 4.1 - 3.7).x * 0.15; }
vec4 lqMask(vec2 xz) { // r = shore distance, g = depth, b = is liquid (outside the baked rect: open, deep water)
  vec2 mu = (xz - uMR.xy) * uMR.zw;
  if (mu.x < 0.0 || mu.y < 0.0 || mu.x > 1.0 || mu.y > 1.0) return vec4(1.0);
  return texture2D(uMask, mu);
}`;
// four travelling waves (height + gradient). sharpened crests read as a chunky cartoon swell
const WAVES = `
vec3 lqWaves(vec2 p, float t) {
  vec3 r = vec3(0.0);
  for (int i = 0; i < 4; i++) {
    float fi = float(i), a = 0.6 + fi * 2.13, L = uLen * pow(0.6, fi), k = 6.2832 / L, w = sqrt(9.8 * k) * 0.55, A = pow(0.55, fi);
    vec2 d = vec2(cos(a), sin(a));
    float ph = dot(d, p) * k - w * t + fi * 1.7, s = sin(ph) * 0.5 + 0.5;
    r.x += A * (s * s * 2.0 - 0.6); // pointy tops, flat troughs
    r.yz += A * 2.0 * s * cos(ph) * k * d;
  }
  return r / 2.02;
}`;
const SNAP = `
  { vec4 js = gl_Position; js.xyz /= js.w; js.xy = floor(js.xy * uSnap + 0.5) / uSnap; js.xyz *= js.w; gl_Position = js; }`;
const HEAD = `uniform float uTime; uniform float uQ; uniform sampler2D uMask; uniform vec4 uMR; uniform vec2 uSnap;
uniform float uAmp; uniform float uLen; uniform float uSwell; uniform vec4 uWR;
varying vec3 vW; varying vec3 vNw; varying vec4 vMk; varying float vH;
`;

// the vertex shader for all of them: waves on the top faces (calm at the edges and in the shallows, fading out at the
// edge of the wave area), the Potato snap, the fog (+ the city maps' haze: world.js hazify patches these includes)
const VS = HEAD + NOISE + WAVES + `
#ifdef LQ_CITY
attribute vec4 cpack;
#endif
#include <fog_pars_vertex>
void main() {
  vec3 transformed = position;
  vec3 wp = (modelMatrix * vec4(position, 1.0)).xyz;
  vec3 nw = normalize(mat3(modelMatrix) * normal);
  vec4 mk = lqMask(wp.xz);
  float top = step(0.5, nw.y);
  float edge = min(min(wp.x - uWR.x, uWR.z - wp.x), min(wp.z - uWR.y, uWR.w - wp.z));
  float damp = top * smoothstep(0.0, 0.32, mk.r) * mk.b * clamp(edge / 30.0, 0.0, 1.0) * mix(1.0, smoothstep(0.0, 0.35, mk.g), uSwell);
  vec3 wv = lqWaves(wp.xz, uTime);
  float h = wv.x * uAmp * damp;
  transformed.y += h; wp.y += h;
  vH = wv.x * damp;
  vNw = top > 0.5 ? normalize(vec3(-wv.y * uAmp * damp, 1.0, -wv.z * uAmp * damp)) : nw;
  vW = wp; vMk = mk;
  vec4 mvPosition = viewMatrix * vec4(wp, 1.0);
  gl_Position = projectionMatrix * mvPosition;` + SNAP + `
  #include <fog_vertex>
}`;

// water: fresnel from the shallow tint to the deep one, the sky reflected, ripples scrolling over the waves, hard white
// sun sparkles, foam hugging every edge and rolling in towards it, whitecaps on the swell, caustics in the shallows
// (the light dancing on the floor, seen through the water), oil's rainbow. toon-banded so it sits with the boxes
const WATER_FS = HEAD + NOISE + `
uniform vec3 uDeep; uniform vec3 uShal; uniform vec2 uA; uniform float uFoam; uniform float uSpark; uniform float uRefl; uniform float uSheen; uniform float uCaus;
uniform vec3 uSun; uniform vec3 uSunC; uniform vec3 uSkyT; uniform vec3 uSkyM; uniform float uNight;
#include <fog_pars_fragment>
float lqCaus(vec2 p, float t) { // the old "water turbulence" trick: three warped passes make a web of bright lines
  vec2 i = p; float c = 1.0;
  for (int n = 0; n < 3; n++) {
    float tt = t * (1.0 - 3.5 / float(n + 1));
    i = p + vec2(cos(tt - i.x) + sin(tt + i.y), sin(tt - i.y) + cos(tt + i.x));
    c += 1.0 / length(vec2(p.x / (sin(i.x + tt) / 0.006), p.y / (cos(i.y + tt) / 0.006)));
  }
  c /= 3.0; c = 1.17 - pow(c, 1.4);
  return pow(abs(c), 8.0);
}
void main() {
  vec3 V = normalize(cameraPosition - vW);
  float top = step(0.5, vNw.y);
  float depth = vMk.g * ${DEPTH}.0, shore = vMk.r * ${SHORE}.0, t = uTime;
  // ripples: two noise layers drifting different ways (one on Potato)
  vec2 g = lqN(vW.xz * 0.9 + vec2(t * 0.23, t * 0.11)).yz * 0.9;
  if (uQ > 0.5) g += lqN(vW.xz * 2.3 - vec2(t * 0.19, -t * 0.27)).yz * 0.55;
  vec3 N = normalize(vNw + vec3(-g.x, 0.0, -g.y) * 0.06 * top);
  float ndv = max(dot(N, V), 0.0), fr = 0.03 + 0.97 * pow(1.0 - ndv, 5.0);
  float dk = smoothstep(0.0, 2.6, depth);
  vec3 col = mix(uShal, uDeep, clamp(max(dk, fr * 0.8), 0.0, 1.0));
  // light on the wave faces: a lit band toward the sun (2 steps)
  float l = dot(N, uSun);
  col *= 0.9 + 0.18 * step(0.5, l + g.x * 0.12) * (1.0 - uNight * 0.7);
  // the sky in it
  vec3 R = reflect(-V, N);
  vec3 sky = mix(uSkyM, uSkyT, smoothstep(0.0, 0.55, R.y));
  col = mix(col, sky, fr * uRefl * top);
  // oil: a rainbow sliding over it with the ripples
  if (uSheen > 0.0) { float hn = lqF(vW.xz * 0.35 + t * 0.05) + fr * 1.5 + g.x * 0.6; col += uSheen * (0.5 + 0.5 * cos(6.2832 * (vec3(0.0, 0.33, 0.67) + hn * 1.3))) * 0.22 * (0.4 + fr); }
  // caustics: only where it's shallow and you're looking into it
  if (uQ > 1.5 && uCaus > 0.0) {
    float sk = (1.0 - smoothstep(0.08, 2.4, depth)) * (1.0 - fr) * top * uCaus;
    if (sk > 0.01) col += mix(uShal, vec3(1.0), 0.6) * step(0.45, lqCaus(vW.xz * 0.55, t * 0.45)) * 0.38 * sk;
  }
  // foam: a bright line on every edge, lines of it rolling in, whitecaps on the swell. noise breaks it up
  float fn = lqN(vW.xz * 1.4 + vec2(t * 0.35, -t * 0.22)).x;
  float foam = step(0.62, 1.0 - shore / (0.45 + 0.4 * uFoam) + fn * 0.45);
  foam = max(foam, step(0.72, sin(shore * 2.6 - t * 2.3 + fn * 2.5)) * step(0.4, fn) * (1.0 - smoothstep(0.6, 2.8 * uFoam, shore)));
  float chunk = lqN(vW.xz * 3.1 - t * 0.4).x;
  foam = max(foam, uSwell * step(1.0, vH * 0.95 + fn * 0.3 + chunk * 0.25)) * step(0.01, uFoam) * top; // whitecaps, only on the tallest crests
  // the sun glinting off it: hard cartoon sparkles that twinkle
  float sp = pow(max(dot(R, uSun), 0.0), 90.0) * 2.2 + pow(max(dot(R, uSun), 0.0), 12.0) * 0.18;
  float tw = lqH(floor(vW.xz * 3.0) + floor(t * 5.0));
  float spark = step(0.75, sp * (0.4 + tw)) * uSpark * top;
  if (uQ > 0.5) spark = max(spark, step(0.985, tw) * step(0.6, l) * step(0.3, fr) * uSpark * 0.8 * top * (1.0 - uNight * 0.5));
  col = mix(col, vec3(1.0), clamp(foam * 0.85, 0.0, 1.0));
  col = mix(col, uSunC * 1.2 + 0.25, clamp(spark, 0.0, 1.0));
  float a = mix(uA.x, uA.y, dk);
  a = top > 0.5 ? clamp(max(max(a, fr * 0.95), max(foam, spark)), 0.0, 1.0) : uA.y;
  gl_FragColor = vec4(col, a);
  #include <colorspace_fragment>
  #include <fog_fragment>
}`;

// lava (and goo): molten noise flowing under drifting crust plates that crack apart and glow in the cracks, bubbles
// that swell and pop with a ring, falls on the upright faces running down. fully lit by itself
const LAVA_FS = HEAD + NOISE + `
uniform vec3 uHot; uniform vec3 uMid; uniform vec3 uCrust; uniform vec3 uEdge; uniform float uCrustK; uniform float uFlow; uniform float uBub; uniform float uGlow;
#include <fog_pars_fragment>
vec3 lqVor(vec2 p) { // F1, F2, cell id hash
  vec2 i = floor(p), f = fract(p); float d1 = 8.0, d2 = 8.0, id = 0.0;
  for (int y = -1; y <= 1; y++) for (int x = -1; x <= 1; x++) {
    vec2 c = vec2(float(x), float(y)), h = vec2(lqH(i + c), lqH(i + c + 17.3));
    vec2 o = c + 0.5 + 0.38 * sin(uTime * 0.25 * uFlow + 6.2832 * h) - f;
    float d = dot(o, o);
    if (d < d1) { d2 = d1; d1 = d; id = lqH(i + c + 3.1); } else if (d < d2) d2 = d;
  }
  return vec3(sqrt(d1), sqrt(d2), id);
}
void main() {
  float t = uTime * uFlow;
  vec3 n = normalize(vNw);
  bool flat_ = abs(n.y) > 0.5;
  vec2 p = flat_ ? vW.xz : vec2((abs(n.x) > 0.5 ? vW.z : vW.x) * 1.4, (vW.y + uTime * 1.6 * uFlow) * 0.5); // falls run down
  // molten: domain-warped noise, slowly flowing
  vec2 q = p * 0.42 + vec2(t * 0.06, t * 0.035);
  vec2 w = vec2(lqF(q), lqF(q + 5.2 - t * 0.03));
  float m = lqF(q * 1.7 + w * 1.9);
  vec3 col = mix(uMid * 0.75, uMid, smoothstep(0.3, 0.5, m));
  col = mix(col, uHot, step(0.6, m + 0.06 * sin(t * 1.3 + p.x)));
  // the crust: plates drifting with the flow (fewer on the falls), cracks between them glowing hot
  vec3 v = lqVor(p * 0.85 + w * 0.5 + vec2(t * 0.05, 0.0));
  float crack = v.y - v.x;
  float cov = step(v.z, uCrustK * (flat_ ? 1.0 : 0.45) * (0.6 + 0.8 * lqN(p * 0.12 + t * 0.02).x) + (1.0 - vMk.r) * 0.35);
  float plate = step(0.07 + 0.04 * (1.0 - uCrustK), crack);
  vec3 cr = mix(uEdge, uCrust, step(0.16, crack));
  cr *= 0.85 + 0.3 * lqN(p * 3.0).x; // crusty speckle
  col = mix(col, cr, plate * cov);
  col = mix(col, uHot * 1.1, cov * (1.0 - plate) * step(0.0, crack)); // glowing cracks
  // bubbles: one per cell now and then, swelling then popping with a ring
  if (flat_ && uQ > 0.5) {
    vec2 bp = p * 0.7, bc = floor(bp), bf = fract(bp) - 0.5;
    float ph = fract(uTime * (0.18 + 0.2 * lqH(bc + 9.0)) * max(0.4, uFlow) + lqH(bc) * 7.0), on = step(lqH(bc + 3.0), uBub);
    vec2 o = (vec2(lqH(bc + 1.0), lqH(bc + 2.0)) - 0.5) * 0.45;
    float r = length(bf - o), br = ph * 0.34;
    float dome = on * step(ph, 0.86) * step(r, br);
    float hi = dome * step(r, br * 0.5) * step(0.0, (bf - o).x + (bf - o).y);
    float ring = on * step(0.86, ph) * step(abs(r - 0.3 - (ph - 0.86) * 1.8), 0.025);
    col = mix(col, uHot, dome * 0.85); col = mix(col, vec3(1.0, 0.98, 0.85), hi * 0.6 + ring);
  }
  col *= uGlow * (0.93 + 0.07 * sin(uTime * 2.2 + p.x * 0.3 + p.y * 0.2));
  gl_FragColor = vec4(col, 1.0);
  #include <colorspace_fragment>
  #include <fog_fragment>
}`;

// ------------------------------------------------------------ materials (one per liquid, made once, shared by every map)
const MATS = new Map();
let HAZE = null; // world.js hazify (the city maps' height haze), handed over by liquids.js
export function setLiquidHaze(f) { HAZE = f; }
const col3 = (hex) => new THREE.Color(hex);
export function liquidMaterial(key, opts = {}) {
  const ck = key + (opts.city ? ':city' : '');
  if (MATS.has(ck)) return MATS.get(ck);
  const L = LIQ[key] || LIQ.water;
  const U = { ...THREE.UniformsUtils.clone(THREE.UniformsLib.fog), uSnap: jankUniforms.uSnap, ...SH,
    uAmp: { value: L.amp }, uLen: { value: L.len || 4 }, uSwell: { value: L.swell || 0 }, uWR: { value: new THREE.Vector4(-1e6, -1e6, 1e6, 1e6) } };
  let fs;
  if (L.kind === 'water') {
    fs = WATER_FS;
    Object.assign(U, { uDeep: { value: col3(L.deep) }, uShal: { value: col3(L.shal) }, uA: { value: new THREE.Vector2(...L.a) }, uFoam: { value: L.foam },
      uSpark: { value: L.spark }, uRefl: { value: L.refl }, uSheen: { value: L.sheen }, uCaus: { value: L.caus } });
  } else {
    fs = LAVA_FS;
    Object.assign(U, { uHot: { value: col3(L.hot) }, uMid: { value: col3(L.mid) }, uCrust: { value: col3(L.crust) }, uEdge: { value: col3(L.edge) },
      uCrustK: { value: L.crustK }, uFlow: { value: L.flow }, uBub: { value: L.bub }, uGlow: { value: L.glow } });
  }
  const water = L.kind === 'water';
  const m = new THREE.ShaderMaterial({ uniforms: U, vertexShader: (opts.city ? '#define LQ_CITY\n' : '') + VS, fragmentShader: fs, fog: true,
    transparent: water, depthWrite: true, opacity: water ? 0.9 : 1 }); // (opacity < 0.95: lighting.js never makes it cast shadows)
  if (!water) { m.polygonOffset = true; m.polygonOffsetFactor = -2; m.polygonOffsetUnits = -4; } // sits on top of a floor it's painted onto (floor is lava)
  if (key === 'oil') { m.polygonOffset = true; m.polygonOffsetFactor = -3; m.polygonOffsetUnits = -6; }
  m.userData.liquid = key;
  if (HAZE && !opts.city) HAZE(m, water ? 0.6 : 0.45);
  MATS.set(ck, m);
  return m;
}


export function tickLiquids(sec) { SH.uTime.value = sec % 3600; }
export function setLiquidQ(i) { SH.uQ.value = i; }
