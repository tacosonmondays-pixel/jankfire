// THE GUT'S GROUND FOG: a low red mist that hugs the floor, knee to waist high, drifting, breathing with the beat.
// Done the cheap way that suits this renderer: a few big flat sheets stacked 20 cm apart just over the ground, each a
// single quad with scrolling noise for wisps and holes. Sheets rather than height fog in the city shaders because
// they fog everything the same (ground, props, people's shins) without touching any other material, and because a
// stack of sheets can never get thicker than its layers: however flat you look along it, the cap holds.
//   - the plateau (y 40), with a hole over the Big Stomach's crater; thicker round the Big Heart's roots
//   - the border band (y 36): the spill down the cliff, thinning out to nothing before the Bottom's houses
//   - a pool in the Big Stomach's bowl, over the acid (the hollow is the thickest of all)
// It fades out round your own feet (so pickups and whoever you're fighting stay readable), where you cross a sheet,
// and into the district's distance fog. The beat: the whole layer swells and flushes on the lub, and a ring runs out
// along the ground from the heart's roots as the ripple reaches them.
// Nothing is drawn unless the camera is in or near the Gut. Layers per render preset: Potato 2 ... Too HD 5.
import * as THREE from 'three';
import { SLICE } from '/shared/city/slice.js';
import { BIG_HEART } from '/shared/city/bigheart.js';

// top: height of the highest sheet (m); cap: the most the whole stack can ever cover; gain: how much of a wisp sits on
// the cap; holes: how much clear ground between wisps (0 none .. 0.6 mostly holes); glow: how much it brightens on the
// beat; near: drawn only within this of the Gut (m)
export const GUT_FOG = { on: true, top: 1.05, cap: 0.55, gain: 1.5, holes: 0.36, glow: 0.7, color: 0xc81a30, drift: 1, near: 110 };
const LAYERS = [2, 3, 4, 5]; // per preset
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
const FS = `
uniform sampler2D uN; uniform float uT, uBeat, uK, uA, uCap, uLayer, uKind, uHoles, uGlow;
uniform vec3 uCol, uFogCol; uniform vec2 uFog; uniform vec3 uHeart; uniform vec3 uSt; uniform vec4 uRect;
varying vec3 vW;
float ghBeat(float t) { return exp(-pow((t - 0.12) / 0.045, 2.0)) + 0.6 * exp(-pow((t - 0.33) / 0.06, 2.0)); }
void main() {
  vec2 p = vW.xz;
  // two noise fields sliding over each other: slow wisps, each sheet its own
  float n = 0.62 * texture2D(uN, p * 0.019 + uT * vec2(0.010, 0.006) + uLayer * 0.37).r + 0.38 * texture2D(uN, p * 0.047 - uT * vec2(0.007, 0.012) + uLayer * 0.61).r;
  float dens = smoothstep(uHoles + 0.12 * uLayer, uHoles + 0.3, n); // wisps with clear ground between; the higher the sheet, the more holes: it thins upward
  dens *= 0.25 + 0.75 * smoothstep(0.3, 0.6, texture2D(uN, p * 0.0043 + uT * vec2(0.0021, 0.0013)).r); // and banks of it, 50 m across, wandering the district
  float dh = length(p - uHeart.xy), root = exp(-dh * dh / 420.0); // round the heart's roots it pools: thicker, no holes
  dens = mix(dens, 0.6 + 0.4 * n, root * 0.85) * (1.0 + 0.45 * root);
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
  a *= smoothstep(0.8, 3.2, dist) * smoothstep(0.02, 0.4, abs(v.y)); // clear round your feet; no sheet flashing past your eyes
  a = min(a, uCap);
  if (a < 0.004) discard;
  vec3 col = uCol * (0.75 + 0.35 * dens + uGlow * uK + 1.5 * uGlow * ring); // the thick of a wisp is the brightest; the beat lights it
  col = mix(col, uFogCol, smoothstep(uFog.x, uFog.y, dist)); // far off it melts into the district's fog
  gl_FragColor = vec4(col, a);
  #include <colorspace_fragment>
}`;

let F = null;
export function startGutFog(parent) { stopGutFog(); F = { parent, root: null, n: -1, sheets: [], tex: null, t: 0 }; }
export function stopGutFog() {
  if (!F) return;
  if (F.root) { F.root.removeFromParent(); for (const m of F.sheets) { m.geometry.dispose(); m.material.dispose(); } }
  if (F.tex) F.tex.dispose();
  F = null;
}
const SHARED = { uT: { value: 0 }, uBeat: { value: 0 }, uK: { value: 0 }, uHoles: { value: 0.36 }, uGlow: { value: 0.7 }, uCol: { value: new THREE.Color() }, uFogCol: { value: new THREE.Color() }, uFog: { value: new THREE.Vector2(30, 250) },
  uHeart: { value: new THREE.Vector3(BIG_HEART.x, BIG_HEART.z, 0) }, uSt: { value: new THREE.Vector3(ST.x, ST.z, ST.r) }, uRect: { value: new THREE.Vector4(G0[0], G0[1], G0[2], G0[3]) } };
// (re)build the stack for this preset's layer count
function build(n) {
  if (F.root) { F.root.removeFromParent(); for (const m of F.sheets) { m.geometry.dispose(); m.material.dispose(); } }
  F.tex = F.tex || noiseTex();
  F.root = new THREE.Group(); F.root.name = 'gutfog'; F.sheets = []; F.n = n;
  const sheet = (kind, i, cnt, geo, x, y0, z, h) => {
    const mat = new THREE.ShaderMaterial({ vertexShader: VS, fragmentShader: FS, transparent: true, depthWrite: false, side: THREE.DoubleSide, fog: false,
      uniforms: { ...SHARED, uN: { value: F.tex }, uA: { value: 0 }, uCap: { value: 0 }, uLayer: { value: cnt > 1 ? i / (cnt - 1) : 0 }, uKind: { value: kind } } });
    const m = new THREE.Mesh(geo, mat);
    m.rotation.x = -Math.PI / 2; m.position.set(x, y0, z); m.userData = { y0, h, kind, noShadow: true };
    m.frustumCulled = false; m.renderOrder = kind === 2 ? 3 : -1; // before every other see-through thing (sparks, glass and tracers stay on top); the pool goes over the acid
    F.root.add(m); F.sheets.push(m);
  };
  const w = G0[2] - G0[0], d = -46 - G0[1], gq = new THREE.PlaneGeometry(w, d), bq = new THREE.PlaneGeometry(w, 48), pool = new THREE.CircleGeometry(32, 20);
  for (let i = 0; i < n; i++) sheet(0, i, n, gq, (G0[0] + G0[2]) / 2, GY, G0[1] + d / 2, 0.22 + (GUT_FOG.top - 0.22) * (n > 1 ? i / (n - 1) : 0.5));
  const nb = Math.max(2, n - 1); for (let i = 0; i < nb; i++) sheet(1, i, nb, bq, (G0[0] + G0[2]) / 2, BY, -24, 0.22 + (GUT_FOG.top - 0.3) * i / (nb - 1));
  const np = Math.min(3, n); for (let i = 0; i < np; i++) sheet(2, i, np, pool, ST.x, ST.acid, ST.z, 0.5 + 0.75 * i);
  F.parent.add(F.root);
}

// once a frame (bigheart.js): b is the Gut's clock (gutbeat.js)
export function updateGutFog(dt, S, camera, b) {
  if (!F) return;
  const p = camera.position, dGut = Math.hypot(Math.max(G0[0] - p.x, 0, p.x - G0[2]), Math.max(G0[1] - p.z, 0, p.z - G0[3]));
  const on = GUT_FOG.on && dGut < GUT_FOG.near;
  if (!on) { if (F.root) F.root.visible = false; return; }
  const n = LAYERS[S.preset] ?? 3;
  if (n !== F.n) build(n);
  F.root.visible = true;
  F.t += dt * GUT_FOG.drift;
  SHARED.uT.value = F.t; SHARED.uBeat.value = b.t % 64; SHARED.uK.value = b.k; SHARED.uCol.value.setHex(GUT_FOG.color); SHARED.uHoles.value = GUT_FOG.holes; SHARED.uGlow.value = GUT_FOG.glow;
  const cap = 1 - Math.pow(1 - Math.min(0.9, GUT_FOG.cap), 1 / n); // per sheet, so the whole stack tops out at GUT_FOG.cap
  const e = S.env; if (e) { SHARED.uFogCol.value.copy(e.fog); SHARED.uFog.value.set(e.near, e.far); }
  const swell = 1 + 0.16 * b.k; // it rises a little on the beat
  const seeBorder = p.z > -150, seePool = Math.hypot(p.x - ST.x, p.z - ST.z) < 150; // (the far ones aren't worth their pixels)
  for (const m of F.sheets) { const u = m.material.uniforms, kind = m.userData.kind, k = kind === 2 ? 1.4 : 1; // (the pool in the Big Stomach is the thickest)
    m.visible = kind === 0 || (kind === 1 ? seeBorder : seePool);
    m.position.y = m.userData.y0 + m.userData.h * swell; u.uCap.value = cap * k; u.uA.value = cap * k * GUT_FOG.gain; }
}
export const gutFogState = () => (F ? { on: !!(F.root && F.root.visible), layers: F.n, sheets: F.sheets.length } : null);
