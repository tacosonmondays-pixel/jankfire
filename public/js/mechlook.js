// The mech hero kit, game side (docs/mechs/MECHS.md "hero kit"). The owner: "I want this to be higher quality than
// the base game, same with the mechs". Any mech glb that comes through buildMech gets it (PAPER PLANE, NIGHT SHIFT,
// every hero after them), nothing here knows a frame by name:
//  - an anime rim light on its metal (a hard fresnel edge in the mech's colour) and crisp ink outlines per joint
//  - glows that bloom: eyes / visors / thrusters burn hotter with the thrust, flare on cue, the blade heats up
//  - thruster contrails and heat shimmer behind the flames
//  - the rig's clip events (meta clips[].events: dust, sparks, slams, vents...) as effects + a camera-shake hook
//  - sprayOnMech(): a spray / skin projected onto one of the model's decal slots (meta decal_slots)
// mechmodel.js calls lookMech (build), lookTick (each pose), lookColor, lookFree. Potato keeps it cheap.
import * as THREE from 'three';
import { mergeGeometries, mergeVertices } from 'three/addons/utils/BufferGeometryUtils.js';
import { DecalGeometry } from 'three/addons/geometries/DecalGeometry.js';
import { G } from './ctx.js';
import { rfx, rmesh } from './rigmodel.js';
import { metaOf, nodeIn } from './glbkit.js';
import { jankify } from './jank.js';

export const mechLook = { onEvent: null }; // (a hook: (inst, ev, [x, y, z]) => {} for the sounds)
const Q = () => (G.settings && Number.isFinite(G.settings.jank) ? G.settings.jank : 2); // 0 Potato .. 3 HD
const INK = 0x120818; // (the UI's near-black purple)
const _v = new THREE.Vector3(), _w = new THREE.Vector3(), _m = new THREE.Matrix4();

// ------------------------------------------------------------ rim light: a hard fresnel edge added to the emissive
// (on top of the game's vertex snap: a clone loses its onBeforeCompile, so the snap goes back on here too)
function rimify(m, U) {
  jankify(m);
  const snap = m.onBeforeCompile;
  m.onBeforeCompile = (sh, r) => {
    snap(sh, r);
    sh.uniforms.uRimC = U.c; sh.uniforms.uRimK = U.k;
    sh.fragmentShader = 'uniform vec3 uRimC; uniform float uRimK;\n' + sh.fragmentShader.replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
      { float jfF = 1.0 - clamp(dot(normalize(normal), normalize(vViewPosition)), 0.0, 1.0);
        totalEmissiveRadiance += uRimC * uRimK * smoothstep(0.5, 0.8, jfF) * (0.4 + 0.6 * clamp(normal.y + 0.6, 0.0, 1.0)); }`);
  };
  m.customProgramCacheKey = () => 'jf-mech-rim-1';
  m.needsUpdate = true;
}

// ------------------------------------------------------------ outlines: one smooth hull per joint (inverted hull)
const OUT_VS = `uniform float uThick; void main() { vec4 mv = modelViewMatrix * vec4(position, 1.0);
  float k = uThick * clamp(-mv.z * 0.045, 1.0, 3.5); // (thicker far away: stays a line, not a hairline)
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position + normal * k, 1.0); }`;
const OUT_FS = 'uniform vec3 uColor; void main() { gl_FragColor = vec4(uColor, 1.0); }';
const HULLS = new WeakMap(); // source glb scene -> { joint name: hull geometry } (shared by every mech built from it)
function hullsOf(src, glb, joints) {
  if (HULLS.has(src)) return HULLS.get(src);
  const out = {}, isJoint = new Set(joints);
  glb.updateMatrixWorld(true);
  for (const jn of joints) {
    const J = nodeIn(glb, jn); if (!J) continue;
    const inv = _m.copy(J.matrixWorld).invert(), parts = [];
    const walk = (o) => { for (const c of o.children) { if (isJoint.has(c.name)) continue; if (c.isMesh && c.geometry && c.material && !/decal|glass/.test(c.material.name || '') && c.material.isMeshStandardMaterial) { const g = c.geometry.clone(); for (const k of Object.keys(g.attributes)) if (k !== 'position') g.deleteAttribute(k); g.applyMatrix4(new THREE.Matrix4().multiplyMatrices(inv, c.matrixWorld)); parts.push(g.index ? g : mergeVertices(g, 1e-4)); } walk(c); } };
    walk(J);
    if (!parts.length) continue;
    const h = mergeVertices(mergeGeometries(parts, false), 2e-3);
    for (const g of parts) g.dispose();
    h.computeVertexNormals(); h.userData.shared = true;
    out[jn] = h;
  }
  HULLS.set(src, out);
  return out;
}

// ------------------------------------------------------------ thruster contrails (camera-facing ribbons) + shimmer
const TRAIL_N = 22;
const TRAIL_VS = `attribute vec3 aT; attribute vec2 aS; uniform float uW; varying float vA;
void main() { vec3 sd = cross(aT, normalize(cameraPosition - position)); float l = length(sd); sd = l > 1e-4 ? sd / l : vec3(0.0, 1.0, 0.0);
  vA = aS.y; gl_Position = projectionMatrix * viewMatrix * vec4(position + sd * aS.x * uW * (0.2 + 0.8 * aS.y), 1.0); }`;
const TRAIL_FS = 'uniform vec3 uC; uniform float uO; varying float vA; void main() { gl_FragColor = vec4(mix(uC, vec3(1.0), vA * vA * 0.7), vA * vA * uO); }';
function makeTrail(col) {
  const g = new THREE.BufferGeometry(), n = TRAIL_N * 2;
  g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(n * 3), 3).setUsage(THREE.DynamicDrawUsage));
  g.setAttribute('aT', new THREE.BufferAttribute(new Float32Array(n * 3), 3).setUsage(THREE.DynamicDrawUsage));
  g.setAttribute('aS', new THREE.BufferAttribute(new Float32Array(n * 2), 2).setUsage(THREE.DynamicDrawUsage));
  const idx = []; for (let i = 0; i < TRAIL_N - 1; i++) { const a = i * 2; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
  g.setIndex(idx);
  const m = new THREE.ShaderMaterial({ uniforms: { uC: { value: new THREE.Color(col) }, uO: { value: 0.55 }, uW: { value: 0.32 } }, vertexShader: TRAIL_VS, fragmentShader: TRAIL_FS,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide });
  const t = new THREE.Mesh(g, m); t.frustumCulled = false; t.renderOrder = 8; t.visible = false; t.userData.pts = [];
  return t;
}
function updateTrail(t, p, on) {
  const P = t.userData.pts;
  if (on) {
    const h = P[0];
    if (h && Math.hypot(p[0] - h[0], p[1] - h[1], p[2] - h[2]) < 0.35) { h[0] = p[0]; h[1] = p[1]; h[2] = p[2]; } // (sits still: no trail, just the flame)
    else P.unshift([p[0], p[1], p[2]]);
  } else if (P.length) P.pop();
  while (P.length > TRAIL_N) P.pop();
  t.visible = P.length > 2;
  if (!t.visible) return;
  const pos = t.geometry.attributes.position.array, tan = t.geometry.attributes.aT.array, s = t.geometry.attributes.aS.array;
  for (let i = 0; i < TRAIL_N; i++) {
    const a = P[Math.min(i, P.length - 1)], b = P[Math.min(i + 1, P.length - 1)], c = i + 1 < P.length ? b : P[Math.max(0, P.length - 2)];
    const tx = i + 1 < P.length ? a[0] - b[0] : c[0] - a[0], ty = i + 1 < P.length ? a[1] - b[1] : c[1] - a[1], tz = i + 1 < P.length ? a[2] - b[2] : c[2] - a[2];
    const al = Math.max(0, 1 - i / (P.length - 1));
    for (let k = 0; k < 2; k++) { const v = i * 2 + k; pos.set(a, v * 3); tan[v * 3] = tx; tan[v * 3 + 1] = ty; tan[v * 3 + 2] = tz; s[v * 2] = k ? 1 : -1; s[v * 2 + 1] = al; }
  }
  for (const k of ['position', 'aT', 'aS']) t.geometry.attributes[k].needsUpdate = true;
}
const SHIM_VS = `uniform float uSize; uniform float uOff; varying vec2 vUv; void main() { vUv = uv; vec4 mv = modelViewMatrix * vec4(0.0, uOff, 0.0, 1.0); mv.xy += position.xy * uSize; gl_Position = projectionMatrix * mv; }`;
const SHIM_FS = `uniform float uT; uniform vec3 uC; varying vec2 vUv;
void main() { vec2 c = vUv * 2.0 - 1.0; float r = length(c); if (r > 1.0) discard;
  float w = sin(c.y * 18.0 - uT * 26.0 + sin(c.x * 9.0 + uT * 11.0) * 2.4) * 0.5 + 0.5;
  gl_FragColor = vec4(uC, w * w * (1.0 - r) * 0.22); }`;
const SHIM_GEO = new THREE.PlaneGeometry(2, 2);

// ------------------------------------------------------------ build / colour / free
export function lookMech(inst, glb, color, src = glb) { // (src: the loaded scene glb was cloned from: the hulls are cached on it)
  if (!glb || inst.look) return;
  const meta = metaOf(glb) || {};
  const col = new THREE.Color(color || '#ff4fd8');
  const U = { c: { value: new THREE.Color(0xffffff).lerp(col, 0.35) }, k: { value: 1.1 } }; // (mostly white, a hint of your colour)
  const L = inst.look = { U, mats: [], glows: [], blade: null, flare: 0, heat: 0, outline: [], outMat: null, trails: [], shims: [], events: {}, nodes: {}, lastAct: null, lastT: 0, slots: Array.isArray(meta.decal_slots) ? meta.decal_slots : [], sprays: [] };
  const owned = new Set(Object.values(inst.own)), made = new Map();
  glb.traverse((o) => {
    if (!o.isMesh || Array.isArray(o.material)) return;
    const m = o.material;
    if (!m.isMeshStandardMaterial || m.blending === THREE.AdditiveBlending) return; // (flames, flashes: already light)
    if (owned.has(m)) { if (!m.userData.jfRim) { rimify(m, U); m.userData.jfRim = 1; } return; } // (the paint: cloned per mech by buildMech)
    if (!made.has(m)) {
      const c = m.clone(); c.userData = { ...m.userData };
      if (m.toneMapped === false && m.emissive && m.emissive.getHex()) { L.glows.push({ m: c, base: m.emissiveIntensity }); jankify(c); } // (glows: no rim, they burn)
      else { rimify(c, U); if (/blade/.test(m.name)) L.blade = c; }
      made.set(m, c); L.mats.push(c);
    }
    o.material = made.get(m);
  });
  // ink outlines, one hull per joint (cached per model): Potato skips them
  const joints = meta.joints ? Object.keys(meta.joints).filter((k) => k !== 'root') : [];
  const H = hullsOf(src, glb, joints);
  L.outMat = new THREE.ShaderMaterial({ uniforms: { uThick: { value: 0.022 }, uColor: { value: new THREE.Color(INK) } }, vertexShader: OUT_VS, fragmentShader: OUT_FS, side: THREE.BackSide });
  for (const [jn, h] of Object.entries(H)) { const J = nodeIn(glb, jn); if (!J) continue; const o = new THREE.Mesh(h, L.outMat); o.name = jn + '_ink'; o.userData.noWrap = true; J.add(o); L.outline.push(o); }
  // thrusters: a contrail each (in the world) and a heat shimmer behind each flame
  const hot = inst.frame === 'nightshift' ? 0xffb43a : 0x5ff0ff;
  L.shimMat = new THREE.ShaderMaterial({ uniforms: { uT: { value: 0 }, uC: { value: new THREE.Color(0xfff0d8) }, uSize: { value: 0.9 }, uOff: { value: 1.9 } }, vertexShader: SHIM_VS, fragmentShader: SHIM_FS,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending });
  for (const f of inst.flames) {
    const s = new THREE.Mesh(SHIM_GEO, L.shimMat); s.frustumCulled = false; s.renderOrder = 9; f.add(s); L.shims.push(s);
    const t = makeTrail(hot); L.trails.push({ t, at: f.parent });
  }
  // the clip events (rig meta): clip name -> [{t, fx, at, shake, ground, k}]
  const list = Array.isArray(meta.clips) ? meta.clips : [];
  for (const c of list) if (c && typeof c.name === 'string' && Array.isArray(c.events)) L.events[c.name] = c.events.filter((e) => e && Number.isFinite(e.t) && typeof e.fx === 'string' && typeof e.at === 'string');
  L.glb = glb;
}
export function lookColor(inst, color) {
  if (!inst.look) return;
  inst.look.U.c.value.set(0xffffff).lerp(new THREE.Color(color), 0.35);
}
export function lookFree(inst) {
  const L = inst.look;
  if (!L) return;
  for (const m of L.mats) m.dispose();
  L.outMat.dispose(); L.shimMat.dispose();
  for (const { t } of L.trails) { t.removeFromParent(); t.geometry.dispose(); t.material.dispose(); }
  for (const s of L.sprays) { s.geometry.dispose(); s.material.dispose(); }
  inst.look = null;
}

// ------------------------------------------------------------ every pose: burn, glows, trails, events
export function lookTick(inst, s, dt) {
  const L = inst.look;
  if (!L) return;
  const q = Q(), T = inst.t;
  L.U.k.value = q === 0 ? 0.7 : 1.1;
  for (const o of L.outline) o.visible = q > 0;
  const burn = Math.max(s.jet || 0, s.hover ? 0.7 : 0, s.dash ? 1 : 0, s.boost || 0);
  L.heat += ((s.slashing ? 1 : 0) - L.heat) * Math.min(1, dt * (s.slashing ? 18 : 3));
  L.flare = Math.max(0, L.flare - dt * 2.5);
  for (const g of L.glows) g.m.emissiveIntensity = g.base * (1 + burn * 0.7 + L.flare * 2.2 + Math.sin(T * 3.1) * 0.06); // (a slow breath; hotter with the thrust)
  if (L.blade) L.blade.emissive.setRGB(1, 0.55, 0.12).multiplyScalar(L.heat * 0.55);
  L.shimMat.uniforms.uT.value = T;
  const show = inst.root.visible && q > 0;
  for (const tr of L.trails) {
    if (!tr.t.parent && G.scene) G.scene.add(tr.t);
    tr.at.getWorldPosition(_v);
    updateTrail(tr.t, [_v.x, _v.y, _v.z], show && burn > 0.35);
  }
  if (inst.act) clipEvents(inst, L);
}
function clipEvents(inst, L) {
  const act = inst.act, name = inst.clip, evs = L.events[name];
  const t = act.time, loop = act.loop === THREE.LoopRepeat; // (held on its last frame: t stops, nothing fires again)
  if (act !== L.lastAct || name !== L.lastName || (!loop && t < L.lastT - 1e-4)) { L.lastAct = act; L.lastName = name; L.lastT = -1e-3; } // (a new clip, or the same swing again)
  const t0 = L.lastT; L.lastT = t;
  if (!evs || !evs.length || t === t0) return;
  for (const e of evs) if (t >= t0 ? e.t > t0 && e.t <= t : e.t > t0 || e.t <= t) fire(inst, L, e); // (a loop wrapped: both ends)
}
function nodeOf(inst, L, n) { return L.nodes[n] ??= (inst.att[n] || inst.j[n] || nodeIn(L.glb, n) || null); }
function fire(inst, L, e) {
  const n = nodeOf(inst, L, e.at);
  if (!n || !inst.root.visible) return;
  inst.root.updateMatrixWorld(true);
  n.getWorldPosition(_v);
  const p = [_v.x, e.ground ? inst.root.getWorldPosition(_w).y : _v.y, _v.z], k = (Number.isFinite(e.k) ? e.k : 1) * (Q() === 0 ? 0.5 : 1);
  const hot = inst.frame === 'nightshift' ? 0xffb43a : 0x5ff0ff;
  switch (e.fx) {
    case 'dust': rfx.dust(p, Math.round(10 * k), 1.3, 3.2); break;
    case 'step': rfx.dust(p, Math.round(6 * k), 0.7, 2.2); break;
    case 'slam': rfx.dust(p, Math.round(18 * k), 2.4, 5.5); rfx.debris(p, Math.round(10 * k), 6); rfx.sparks(p, Math.round(18 * k), 9, [0xfff2b0, 0xffb43a, 0xffe14d], 0.45, 0.1, [0, 1, 0]); rmesh.ring(p, 4.5, 0xffe8c0, 0.45); rmesh.crater(p, 1.5, [0, 1, 0], 5); break;
    case 'spark': rfx.sparks(p, Math.round(26 * k), 10, [0xfff2b0, 0xffd23a, 0xff8a3a], 0.4, 0.1); rmesh.flash(p, 1.1, 0xfff2c0, 0.12); break;
    case 'glint': rmesh.flash(p, 0.8, 0xffffff, 0.1); rfx.sparks(p, Math.round(6 * k), 6, [0xffffff, 0xfff2b0], 0.25, 0.08); break;
    case 'burst': rmesh.flash(p, 1.3, hot, 0.16); rfx.smoke(p, Math.round(4 * k), 0xd8dce0, 0.5, 0.4, 0.7, 0.2); break;
    case 'vent': rfx.smoke(p, Math.round(6 * k), 0xe8ecf0, 0.45, 1.6, 0.9, 0.15); break;
    case 'flare': L.flare = 1; rmesh.flash(p, 0.9, hot, 0.2); break;
    case 'pop': rfx.sparks(p, Math.round(20 * k), 8, [0xfff2b0, 0xff8a3a], 0.4, 0.1); rfx.smoke(p, Math.round(8 * k), 0x8a8e94, 0.7, 1.2, 1.1, 0.3); break;
  }
  if (Number.isFinite(e.shake) && e.shake > 0 && G.camera) { // (only if the camera is near it)
    const near = Math.max(0, 1 - G.camera.position.distanceTo(_v) / 45);
    if (near > 0) G.shake = Math.max(G.shake || 0, Math.min(1, e.shake) * near);
  }
  if (mechLook.onEvent) mechLook.onEvent(inst, e, p);
}

// ------------------------------------------------------------ sprays / skins on a decal slot
// k = the slot (0 = the chest plate, 1 = a shoulder / thigh), map = a texture (a spray canvas). Returns the mesh.
export function sprayOnMech(inst, k, map) {
  const L = inst && inst.look, sl = L && L.slots[k];
  if (!sl || !map || !Array.isArray(sl.at) || !Array.isArray(sl.dir)) return null;
  const J = nodeIn(L.glb, sl.joint), meta = metaOf(L.glb) || {}, ja = meta.joints && meta.joints[sl.joint] && meta.joints[sl.joint].at;
  if (!J || !Array.isArray(ja)) return null;
  // all in the joint's own rest frame (rest frames are the world axes): the patch rides the joint from then on
  const at = new THREE.Vector3(sl.at[0] - ja[0], sl.at[1] - ja[1], sl.at[2] - ja[2]), dir = new THREE.Vector3().fromArray(sl.dir).normalize();
  const up = new THREE.Vector3().fromArray(Array.isArray(sl.up) ? sl.up : [0, 1, 0]);
  const rot = new THREE.Euler().setFromRotationMatrix(new THREE.Matrix4().lookAt(at.clone().add(dir), at, up));
  const size = Number.isFinite(sl.size) ? sl.size : 0.6, geos = [];
  J.updateMatrixWorld(true);
  const inv = new THREE.Matrix4().copy(J.matrixWorld).invert();
  for (const c of J.children) {
    if (meta.joints && Object.hasOwn(meta.joints, c.name)) continue; // (its own pieces, not the next joint down)
    c.traverse((o) => {
      if (!o.isMesh || o.material === L.outMat || !o.material.isMeshStandardMaterial || /decal/.test(o.material.name || '')) return;
      const tmp = new THREE.Mesh(o.geometry); tmp.matrixWorld.multiplyMatrices(inv, o.matrixWorld);
      const g = new DecalGeometry(tmp, at, rot, new THREE.Vector3(size, size, 0.5));
      if (g.attributes.position.count) geos.push(g); else g.dispose();
    });
  }
  if (!geos.length) return null;
  const g = geos.length > 1 ? mergeGeometries(geos, false) : geos[0];
  if (geos.length > 1) for (const x of geos) x.dispose();
  const m = jankify(new THREE.MeshStandardMaterial({ map, transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -4, roughness: 0.5, metalness: 0.1 }));
  const d = new THREE.Mesh(g, m); d.name = 'spray_' + k; d.renderOrder = 2; d.userData.noWrap = true;
  J.add(d); L.sprays.push(d);
  return d;
}
