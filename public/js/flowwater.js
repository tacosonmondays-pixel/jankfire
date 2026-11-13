// Flowing water (owner, 2026-11-13: "it just looks like a blue tube... it should have ripples and splashes"). Fountain
// jets, spouts and the basins they fall into, alive:
// - streams (*_water parts): foam streaks racing along the jet, a bright core and a soft see-through edge, a wobble
// - pools (*_pool parts): ripples drifting, caustic glints, rings spreading out where a stream lands
// - splashes: droplets thrown up where a stream lands, a little mist, spray coming off the jets (pooled, the GPU flies them)
// - box fountains (a column standing in a pool, shared/flowwater.js boxFountains) get jets of their own
// - a soft trickle when you're near one
// one shared material per type, driven by one time uniform. Potato: a plain scroll, no particles. look only.
import * as THREE from 'three';
import { jankUniforms } from './jank.js';
import { SH } from './liquidmats.js';
import { trickle, sfx } from './audio.js';
import { waterTag, landSpots, capFor, boxFountains, jetPath, DropRing } from '/shared/flowwater.js';
export { waterTag };

const U = {
  uTime: { value: 0 }, uLo: { value: 0 }, uScale: { value: 400 }, uNR: { value: 0 },
  uRings: { value: Array.from({ length: 8 }, () => new THREE.Vector4(0, 0, 0, 0)) },
};
let q = 1; // the graphics preset (0 Potato .. 3 Too HD)

const NOISE = `
float fwH(vec2 p) { p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float fwN(vec2 p) { vec2 i = floor(p), f = fract(p), u = f * f * (3.0 - 2.0 * f);
  return mix(mix(fwH(i), fwH(i + vec2(1.0, 0.0)), u.x), mix(fwH(i + vec2(0.0, 1.0)), fwH(i + vec2(1.0, 1.0)), u.x), u.y); }`;
const SNAP = `{ vec4 js = gl_Position; js.xyz /= js.w; js.xy = floor(js.xy * uSnap + 0.5) / uSnap; js.xyz *= js.w; gl_Position = js; }`;
// world position (instanced or not), the wobble, the Potato snap, the fog
const VS = `uniform float uTime; uniform float uLo; uniform vec2 uSnap; uniform float uWob;
varying vec2 vUv; varying vec3 vN; varying vec3 vW; varying float vR;
#include <fog_pars_vertex>
void main() {
  mat4 M = modelMatrix;
  #ifdef USE_INSTANCING
  M = M * instanceMatrix;
  #endif
  vec3 wn = normalize(mat3(M) * normal);
  vec4 wp = M * vec4(position, 1.0);
  // a stream breathes along its length (color.r = the tube's radius there, so a thin trickle wobbles thin)
  float wob = sin(uv.y * 4.0 - uTime * 10.0 + uv.x * 12.566) * 0.6 + sin(uv.y * 1.7 - uTime * 6.3) * 0.4;
  wp.xyz += wn * wob * uWob * color.r * (1.0 - uLo);
  vW = wp.xyz; vN = wn; vUv = uv; vR = color.r;
  vec4 mvPosition = viewMatrix * wp;
  gl_Position = projectionMatrix * mvPosition;
  ${SNAP}
  #include <fog_vertex>
}`;
const STREAM_FS = `uniform float uTime; uniform float uLo; uniform vec3 uDeep; uniform vec3 uCore; uniform vec3 uSunC; uniform vec3 uSun; uniform float uNight;
varying vec2 vUv; varying vec3 vN; varying vec3 vW; varying float vR;
#include <fog_pars_fragment>
${NOISE}
void main() {
  vec3 V = normalize(cameraPosition - vW), N = normalize(vN);
  float f = abs(dot(N, V)); // 1 = facing you (the core), 0 = the silhouette
  float core = smoothstep(0.2, 0.92, f);
  float along = vUv.y - uTime * 3.2; // metres down the jet, racing
  float streak, glint = 0.0;
  if (uLo > 0.5) { // Potato: hard stripes sliding down it, no frills
    streak = step(0.62, fract(along * 0.9 + floor(vUv.x * 4.0) * 0.37));
  } else {
    float s1 = fwN(vec2(vUv.x * 5.0, along * 1.4)), s2 = fwN(vec2(vUv.x * 9.0 + 3.1, along * 3.1 - uTime * 0.7));
    streak = smoothstep(0.58, 0.82, s1 * 0.62 + s2 * 0.38);
    vec3 H = normalize(V + normalize(uSun));
    glint = pow(max(0.0, dot(N, H)), 40.0) * (0.6 + 0.8 * fwN(vec2(vUv.x * 14.0, along * 6.0)));
  }
  vec3 col = mix(uDeep, uCore, core);
  col = mix(col, vec3(1.0), streak * 0.8);
  col += uSunC * glint * 1.2;
  col *= mix(1.0, 0.45, uNight);
  float a = mix(0.32, 0.82, core) + streak * 0.35 + glint;
  gl_FragColor = vec4(col, clamp(a, 0.0, 1.0));
  #include <colorspace_fragment>
  #include <fog_fragment>
}`;
const POOL_FS = `uniform float uTime; uniform float uLo; uniform vec3 uDeep; uniform vec3 uShal; uniform vec3 uSkyM; uniform vec3 uSunC; uniform vec3 uSun; uniform float uNight;
uniform vec4 uRings[8]; uniform float uNR;
varying vec2 vUv; varying vec3 vN; varying vec3 vW; varying float vR;
#include <fog_pars_fragment>
${NOISE}
void main() {
  vec2 p = vW.xz; float t = uTime;
  vec3 V = normalize(cameraPosition - vW);
  vec2 q1 = p * 1.1 + vec2(t * 0.32, t * 0.21), q2 = p * 2.3 - vec2(t * 0.27, -t * 0.38);
  float n = fwN(q1) * 0.6 + fwN(q2) * 0.4;
  // rings where the streams land: spreading out, fading with distance; foam right under each one
  float ring = 0.0, foam = 0.0;
  for (int i = 0; i < 8; i++) {
    if (float(i) >= uNR) break;
    vec4 r = uRings[i];
    float d = length(p - r.xy), s = r.z;
    float ph = d * 4.2 - t * 5.5 + r.w;
    ring += smoothstep(0.72, 0.97, sin(ph)) * exp(-d / (s * 2.2 + 0.4)) * smoothstep(s * 0.4, s * 1.1, d);
    foam += smoothstep(s * 1.1, s * 0.2, d) * (0.6 + 0.4 * fwN(vec2(atan(p.y - r.y, p.x - r.x) * 3.0, d * 3.0 - t * 4.0)));
  }
  vec3 col; float a;
  if (uLo > 0.5) { // Potato: two tones sliding about, the rings in hard white
    col = mix(uDeep, uShal, step(0.5, n));
    col = mix(col, vec3(1.0), step(0.5, ring + foam));
    a = 0.7;
  } else {
    // ripple slope off the noise: the sky glances off them, the sun glitters on the crests
    float e = 0.2, nx = fwN(q1 + vec2(e, 0.0)) - fwN(q1), nz = fwN(q1 + vec2(0.0, e)) - fwN(q1);
    vec3 N = normalize(vec3(-nx * 2.2, 1.0, -nz * 2.2));
    float fres = pow(1.0 - max(0.0, dot(N, V)), 3.0);
    // caustic glints: warped crossing waves, only their bright knots
    vec2 c = p * 1.4 + vec2(fwN(p * 0.6 + t * 0.25), fwN(p * 0.6 - t * 0.22)) * 1.8;
    float ca = abs(sin(c.x * 3.1 + t * 1.3) + sin(c.y * 2.7 - t * 1.1) + sin((c.x + c.y) * 2.2 + t * 0.9));
    float caus = pow(clamp(1.0 - ca * 0.45, 0.0, 1.0), 5.0);
    float spark = pow(max(0.0, dot(reflect(-V, N), normalize(uSun))), 90.0) * step(0.55, n);
    col = mix(uDeep, uShal, smoothstep(0.25, 0.8, n));
    col += vec3(0.75, 0.95, 1.0) * caus * 0.55;
    col = mix(col, mix(uSkyM, uShal, 0.5), fres * 0.4); // (the sky in it, cooled: a pink sky shouldn't turn it purple)
    col = mix(col, vec3(1.0), clamp(ring * 0.75 + foam * 0.85, 0.0, 1.0));
    col += uSunC * spark * 1.5;
    a = 0.5 + fres * 0.35 + caus * 0.15 + ring * 0.3 + foam * 0.45;
  }
  col *= mix(1.0, 0.5, uNight);
  gl_FragColor = vec4(col, clamp(a, 0.0, 0.95));
  #include <colorspace_fragment>
  #include <fog_fragment>
}`;

const mats = {};
function mk(fs, extra, wob) {
  const u = { ...THREE.UniformsUtils.clone(THREE.UniformsLib.fog), uSnap: jankUniforms.uSnap, uTime: U.uTime, uLo: U.uLo, uWob: { value: wob },
    uSun: SH.uSun, uSunC: SH.uSunC, uSkyM: SH.uSkyM, uNight: SH.uNight, uRings: U.uRings, uNR: U.uNR, ...extra };
  const m = new THREE.ShaderMaterial({ uniforms: u, vertexShader: VS, fragmentShader: fs, fog: true, transparent: true, depthWrite: false, vertexColors: true });
  m.opacity = 0.9; // (lighting.js: see-through things cast no shadow)
  m.userData.shared = true; // (never disposed with a map)
  return m;
}
// the one stream material and the one pool material everything shares
export function waterMaterial(kind) {
  if (mats[kind]) return mats[kind];
  mats[kind] = kind === 'pool'
    ? mk(POOL_FS, { uDeep: { value: new THREE.Color(0x0f8fd0) }, uShal: { value: new THREE.Color(0x7ff0ff) } }, 0)
    : mk(STREAM_FS, { uDeep: { value: new THREE.Color(0x1aa6f0) }, uCore: { value: new THREE.Color(0xc8fbff) } }, 0.22);
  if (kind === 'pool') { mats.pool.polygonOffset = true; mats.pool.polygonOffsetFactor = -1; mats.pool.polygonOffsetUnits = -2; }
  return mats[kind];
}

// a stream's geometry: color.r = the tube's radius at each vertex (the wobble's size). rings of a sweep share a v (its
// length along the jet), so each ring's radius is how far its vertices sit from their middle. anything else: a guess
export function streamRadii(geo) {
  const P = geo.getAttribute('position'), UV = geo.getAttribute('uv'), n = P.count;
  const col = new Float32Array(n * 3).fill(1);
  if (UV) {
    const rings = new Map();
    for (let i = 0; i < n; i++) { const k = Math.round(UV.getY(i) * 200); let r = rings.get(k); if (!r) rings.set(k, r = { x: 0, y: 0, z: 0, n: 0, ix: [] }); r.x += P.getX(i); r.y += P.getY(i); r.z += P.getZ(i); r.n++; r.ix.push(i); }
    for (const r of rings.values()) {
      const cx = r.x / r.n, cy = r.y / r.n, cz = r.z / r.n; let d = 0;
      for (const i of r.ix) d += Math.hypot(P.getX(i) - cx, P.getY(i) - cy, P.getZ(i) - cz);
      const rad = Math.min(0.4, d / r.n);
      for (const i of r.ix) col[i * 3] = rad;
    }
  } else col.fill(0.1);
  geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
  return geo;
}

// ---------------------------------------------------------------- where a model's water splashes (model space)
// parts = [{ tag, geo }] -> { lands: [{x, y, z, w}], spray: [[x, y, z]...] } or null
export function waterSpots(parts) {
  const st = parts.filter((p) => p.tag === 'stream'), po = parts.filter((p) => p.tag === 'pool');
  if (!st.length) return null;
  let poolTop = null;
  for (const p of po) { const a = p.geo.getAttribute('position'); for (let i = 0; i < a.count; i++) poolTop = Math.max(poolTop ?? -1e9, a.getY(i)); }
  const pos = [];
  for (const p of st) { const a = p.geo.getAttribute('position'); for (let i = 0; i < a.count; i++) pos.push(a.getX(i), a.getY(i), a.getZ(i)); }
  const lands = landSpots(pos, poolTop);
  const spray = [], step = Math.max(1, Math.floor(pos.length / 3 / 48));
  for (let i = 0; i < pos.length / 3; i += step) spray.push([pos[i * 3], pos[i * 3 + 1], pos[i * 3 + 2]]);
  return { lands, spray };
}

// ---------------------------------------------------------------- the drops: one Points, a ring buffer the GPU flies
const DVS = `uniform float uTime; uniform float uScale; uniform vec2 uSnap;
attribute vec3 aV; attribute vec3 aT;
varying float vA; varying float vK;
#include <fog_pars_vertex>
void main() {
  float age = uTime - aT.x, life = aT.y, k = floor(aT.z / 10.0), sc = aT.z - k * 10.0;
  if (age < 0.0 || age > life) { gl_Position = vec4(2.0, 2.0, 2.0, 1.0); gl_PointSize = 0.0; vA = 0.0; vK = 0.0; return; }
  float u = age / life;
  vec3 p = position;
  if (k > 0.5 && k < 1.5) { p += aV * (1.0 - exp(-age * 2.0)) * 0.5; p.y += 0.25 * age; } // mist: drifts, slows, rises a touch
  else { p += aV * age; p.y -= 4.9 * sqrt(sc) * age * age; } // a drop: thrown, then falls (a small fountain's drops: slower, they stay near)
  float size = (k < 0.5 ? 0.07 : k < 1.5 ? 0.7 + u * 1.6 : 0.1) * sc;
  vA = k > 0.5 && k < 1.5 ? 0.42 * (1.0 - u) * smoothstep(0.0, 0.2, u) : 1.0 - u * u * u;
  vK = k;
  vec4 mvPosition = viewMatrix * vec4(p, 1.0);
  gl_Position = projectionMatrix * mvPosition;
  gl_PointSize = clamp(size * uScale / max(0.1, -mvPosition.z), 1.5, 90.0);
  ${SNAP}
  #include <fog_vertex>
}`;
const DFS = `varying float vA; varying float vK;
#include <fog_pars_fragment>
void main() {
  vec2 c = gl_PointCoord - 0.5; float d = length(c) * 2.0;
  if (d > 1.0 || vA <= 0.0) discard;
  vec3 col; float a;
  if (vK > 0.5 && vK < 1.5) { col = vec3(0.86, 0.96, 1.0); a = vA * (1.0 - d) * (1.0 - d); } // mist: soft puffs
  else { col = mix(vec3(1.0), vec3(0.45, 0.88, 1.0), smoothstep(0.0, 0.9, length(c + vec2(0.18, 0.18)) * 2.0)); a = vA * (1.0 - smoothstep(0.75, 1.0, d)); } // a drop: a white glint, a cyan body
  gl_FragColor = vec4(col, a);
  #include <colorspace_fragment>
  #include <fog_fragment>
}`;
let drops = null, ring = null;
function dropMesh(scene) {
  const cap = capFor(q);
  if (drops && ring && ring.cap === cap) { if (scene && drops.parent !== scene) scene.add(drops); return drops; }
  if (drops) { drops.parent && drops.parent.remove(drops); drops.geometry.dispose(); }
  ring = new DropRing(cap);
  if (!cap) { drops = null; return null; }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(ring.p, 3).setUsage(THREE.DynamicDrawUsage));
  g.setAttribute('aV', new THREE.BufferAttribute(ring.v, 3).setUsage(THREE.DynamicDrawUsage));
  g.setAttribute('aT', new THREE.BufferAttribute(ring.t, 3).setUsage(THREE.DynamicDrawUsage));
  const m = new THREE.ShaderMaterial({ uniforms: { ...THREE.UniformsUtils.clone(THREE.UniformsLib.fog), uTime: U.uTime, uScale: U.uScale, uSnap: jankUniforms.uSnap },
    vertexShader: DVS, fragmentShader: DFS, fog: true, transparent: true, depthWrite: false });
  drops = new THREE.Points(g, m); drops.frustumCulled = false; drops.name = 'flowdrops'; drops.renderOrder = 3; drops.userData.noCast = true;
  if (scene) scene.add(drops);
  return drops;
}

// ---------------------------------------------------------------- what's on this map
// sources: { lands, spray, mats (instance matrices, flat), n, near () -> indices drawn up close }
const SRC = [];
let codeJets = null; // the box fountains' jets (one mesh)
// propfield.js: the prop kinds with water in them (their instance matrices; near() = the copies drawn in full right now)
export function setWaterProps(list) {
  for (let i = SRC.length - 1; i >= 0; i--) if (SRC[i].prop) SRC.splice(i, 1);
  for (const s of list) SRC.push({ ...s, prop: true });
}
const ID = new Float32Array([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]), ALL = { idx: [0], count: 1 };
// world.js: a map's box fountains get jets (built once per map)
export function buildWaterMap(scene, def) {
  if (codeJets) { codeJets.parent && codeJets.parent.remove(codeJets); codeJets.geometry.dispose(); codeJets = null; }
  for (let i = SRC.length - 1; i >= 0; i--) if (!SRC[i].prop) SRC.splice(i, 1);
  let boxes = [];
  try { boxes = def && def.boxes ? [...def.boxes, ...(def.deco || [])] : []; } catch { boxes = []; }
  const jets = boxFountains(boxes);
  dropMesh(scene);
  if (!jets.length) return;
  const geos = [];
  for (const j of jets) {
    const pts = jetPath(j.from, j.to, j.lift, 10).map((p) => new THREE.Vector3(...p));
    geos.push(tubeGeo(pts, j.r[0], j.r[1], 8));
  }
  const geo = mergeTubes(geos);
  codeJets = new THREE.Mesh(geo, waterMaterial('stream')); codeJets.name = 'flowjets'; codeJets.userData.noCast = true; codeJets.renderOrder = 2;
  scene.add(codeJets);
  SRC.push({ lands: jets.map((j) => ({ x: j.to[0], y: j.to[1], z: j.to[2], w: 0.45, s: 0.45 })), spray: jets.flatMap((j) => jetPath(j.from, j.to, j.lift, 6)), mats: ID, n: 1, near: () => ALL });
}
// a tube along a path with radius r0 -> r1, UVs: u round it, v = metres along it (the streaks' scroll)
function tubeGeo(pts, r0, r1, seg) {
  const n = pts.length, pos = [], uv = [], idx = [];
  let len = 0; const up = new THREE.Vector3(0, 1, 0), T = new THREE.Vector3(), N = new THREE.Vector3(), B = new THREE.Vector3(), v = new THREE.Vector3();
  for (let i = 0; i < n; i++) {
    if (i) len += pts[i].distanceTo(pts[i - 1]);
    T.subVectors(pts[Math.min(n - 1, i + 1)], pts[Math.max(0, i - 1)]).normalize();
    N.crossVectors(T, up); if (N.lengthSq() < 1e-6) N.set(1, 0, 0); N.normalize(); B.crossVectors(N, T).normalize();
    const r = r0 + (r1 - r0) * Math.pow(i / (n - 1), 1.5);
    for (let k = 0; k <= seg; k++) {
      const a = (k / seg) * Math.PI * 2;
      v.copy(pts[i]).addScaledVector(N, Math.cos(a) * r).addScaledVector(B, Math.sin(a) * r);
      pos.push(v.x, v.y, v.z); uv.push(k / seg, len);
    }
  }
  for (let i = 0; i < n - 1; i++) for (let k = 0; k < seg; k++) { const a = i * (seg + 1) + k, b = a + seg + 1; idx.push(a, b, a + 1, a + 1, b, b + 1); }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); g.setIndex(idx);
  g.computeVertexNormals();
  return streamRadii(g);
}
function mergeTubes(list) {
  let nv = 0, ni = 0; for (const g of list) { nv += g.attributes.position.count; ni += g.index.count; }
  const P = new Float32Array(nv * 3), Nn = new Float32Array(nv * 3), UV = new Float32Array(nv * 2), C = new Float32Array(nv * 3), I = new Uint32Array(ni);
  let ov = 0, oi = 0;
  for (const g of list) {
    P.set(g.attributes.position.array, ov * 3); Nn.set(g.attributes.normal.array, ov * 3); UV.set(g.attributes.uv.array, ov * 2); C.set(g.attributes.color.array, ov * 3);
    const ix = g.index.array; for (let i = 0; i < ix.length; i++) I[oi + i] = ix[i] + ov;
    ov += g.attributes.position.count; oi += ix.length; g.dispose();
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(P, 3)); g.setAttribute('normal', new THREE.BufferAttribute(Nn, 3)); g.setAttribute('uv', new THREE.BufferAttribute(UV, 2)); g.setAttribute('color', new THREE.BufferAttribute(C, 3)); g.setIndex(new THREE.BufferAttribute(I, 1));
  return g;
}

// ---------------------------------------------------------------- every frame
const _v = new THREE.Vector3(), _m = new THREE.Matrix4();
let acc = 0, plipT = 0, nearest = 1e9, stats = { lands: 0, rings: 0, spawned: 0, live: 0 };
const R = (k) => (Math.random() * 2 - 1) * k;
export function setFlowQ(i) { q = i; U.uLo.value = i === 0 ? 1 : 0; dropMesh(drops && drops.parent); }
export function updateFlowWater(dt, cam, renderer, scene) {
  dt = Math.min(0.1, Math.max(0, dt || 0));
  U.uTime.value = (U.uTime.value + dt) % 3600;
  const now = U.uTime.value;
  if (!cam) return;
  if (renderer && cam.isPerspectiveCamera) U.uScale.value = renderer.domElement.height / (2 * Math.tan(cam.fov * Math.PI / 360));
  // the landing spots near you: the pool's rings (nearest 8), the splashes, the sound
  const lands = [];
  for (const s of SRC) {
    const { idx, count } = s.near();
    for (let j = 0; j < count; j++) {
      _m.fromArray(s.mats, idx[j] * 16);
      const sc = Math.cbrt(Math.abs(_m.determinant())) || 1;
      for (const l of s.lands) {
        _v.set(l.x, l.y, l.z).applyMatrix4(_m);
        const d = _v.distanceTo(cam.position);
        if (d < 90) lands.push({ x: _v.x, y: _v.y, z: _v.z, w: l.w, sz: (l.s ?? 1) * sc, d, s, m: idx[j] * 16 });
      }
    }
  }
  lands.sort((a, b) => a.d - b.d);
  const nr = Math.min(8, lands.length);
  for (let i = 0; i < nr; i++) U.uRings.value[i].set(lands[i].x, lands[i].z, (0.35 + lands[i].w * 0.35) * Math.min(1, lands[i].sz * 1.5), i * 1.7);
  U.uNR.value = nr;
  nearest = lands.length ? lands[0].d : 1e9;
  const loud = nearest < 30 ? Math.min(1, (30 - nearest) / 24) : 0;
  trickle(loud);
  plipT -= dt; if (loud > 0.25 && plipT <= 0) { plipT = 0.12 + Math.random() * 0.5; sfx.fountainDrip(loud); } // the odd drop on top
  stats.lands = lands.length; stats.rings = nr;
  if (!ring || !ring.cap || !drops) return;
  // splashes: a budget per frame spread over the close ones (the far ones get fewer)
  acc += dt;
  const steps = Math.min(4, Math.floor(acc / (1 / 60))); acc -= steps / 60;
  for (let st = 0; st < steps; st++) for (let i = 0; i < Math.min(lands.length, 10); i++) {
    const l = lands[i], near = l.d < 40 ? 1 : 0.4, w = l.w, z = l.sz, zv = Math.sqrt(z);
    const r = (0.25 + w * 0.3) * z;
    // the crown: drops thrown up and out where it lands
    for (let k = 0; k < (Math.random() < 0.9 * w * near ? 3 : 1); k++) {
      const a = Math.random() * 6.283, sp = (0.6 + Math.random() * 1.4 * w) * zv;
      ring.spawn(l.x + Math.cos(a) * r * 0.6, l.y + 0.02, l.z + Math.sin(a) * r * 0.6, Math.cos(a) * sp, (1.8 + Math.random() * 3.2 * w) * zv, Math.sin(a) * sp, now, 0.5 + Math.random() * 0.4, 2, z);
    }
    // a little mist hanging over it
    if (Math.random() < 0.2 * w * near) ring.spawn(l.x + R(r), l.y + 0.1 * z, l.z + R(r), R(0.5) * zv, 0.3 * zv, R(0.5) * zv, now, 1.4 + Math.random(), 1, z);
    // spray off the stream itself
    if (l.s.spray.length && Math.random() < 0.35 * near) {
      const p = l.s.spray[(Math.random() * l.s.spray.length) | 0];
      _m.fromArray(l.s.mats, l.m); _v.set(p[0], p[1], p[2]).applyMatrix4(_m);
      ring.spawn(_v.x, _v.y, _v.z, R(0.9) * zv, (0.2 + Math.random() * 1.0) * zv, R(0.9) * zv, now, 0.5 + Math.random() * 0.4, 0, z);
    }
  }
  if (ring.dirty) { for (const k of ['position', 'aV', 'aT']) drops.geometry.attributes[k].needsUpdate = true; ring.dirty = false; }
  stats.spawned = ring.spawned;
}
export function flowWaterInfo() { return { ...stats, cap: ring ? ring.cap : 0, live: ring ? ring.live(U.uTime.value) : 0, srcs: SRC.length, jets: codeJets ? 1 : 0, nearest: Math.round(nearest), q }; }
