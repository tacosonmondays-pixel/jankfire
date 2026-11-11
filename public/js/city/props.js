// City props: every chunk's prop list (chunk.js prop()) drawn as InstancedMeshes, one per model part, for all the
// chunks in the props ring at once. Models: public/models/story/s_<id>.glb (the story's Blender props), else the PvP
// prop p_<id>.glb, else a small code model built here from boxes (so a missing file still looks like the thing).
// Parts whose material name has 'paint' take the instance's colour (cars, chairs, washing).
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { jankUniforms } from '../jank.js';
import { cityUniforms, LIGHTS_GLSL, LIGHTS_HEAD } from './mats.js';

const MODELS = new Map(); // id -> { parts: [{ geo, mat, paint }], state: 'code' | 'loading' | 'glb' }
const listeners = new Set();
export const onPropModel = (fn) => listeners.add(fn);
let env = null;
export function propEnv(renderer) {
  if (env || !renderer) return env;
  const pm = new THREE.PMREMGenerator(renderer); env = pm.fromScene(new RoomEnvironment(), 0.04).texture; pm.dispose();
  return env;
}

function snap(mat) { // potato vertex snap, plus a breathing pulse for materials named *pulse* (organs, lungs)
  const pulse = /pulse|lung|flesh/.test(mat.name || '');
  mat.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, { uSnap: jankUniforms.uSnap }, cityUniforms);
    sh.vertexShader = 'uniform vec2 uSnap; uniform float uTime; uniform float uBeat;\n' + sh.vertexShader
      .replace('#include <begin_vertex>', `#include <begin_vertex>
        ${pulse ? `#ifdef USE_INSTANCING
        float ph = instanceMatrix[3].x * 0.31 + instanceMatrix[3].z * 0.17;
        #else
        float ph = 0.0;
        #endif
        transformed += objectNormal * (0.025 * sin(uTime * 2.1 + ph) + 0.035 * uBeat); // (small flesh: teeth sit 0.12 m deep, keep under that)` : ''}`)
      .replace('#include <project_vertex>', `#include <project_vertex>
        vec4 jsnap = gl_Position; jsnap.xyz /= jsnap.w; jsnap.xy = floor(jsnap.xy * uSnap + 0.5) / uSnap; jsnap.xyz *= jsnap.w; gl_Position = jsnap;`);
    if (!mat.isMeshBasicMaterial && sh.fragmentShader.includes('#include <lights_fragment_end>')) sh.fragmentShader = '#define CITY_LIGHTS\n' + LIGHTS_HEAD + sh.fragmentShader.replace('#include <lights_fragment_end>', '#include <lights_fragment_end>\n' + LIGHTS_GLSL);
  };
  mat.customProgramCacheKey = () => 'cityprop' + (pulse ? 'p' : '');
  return mat;
}

// ---------------------------------------------------------------- code fallbacks: [x0, y0, z0, x1, y1, z1, colour, paint?]
const CODE = {
  car: [[-2.2, 0.3, -0.9, 2.2, 0.95, 0.9, 0xc8202c, 1], [-1.1, 0.95, -0.8, 0.9, 1.5, 0.8, 0x9fd8ff], [-1.15, 1.5, -0.82, 0.95, 1.6, 0.82, 0xc8202c, 1], [-1.8, 0, -0.95, -1.2, 0.6, 0.95, 0x222222], [1.2, 0, -0.95, 1.8, 0.6, 0.95, 0x222222]],
  streetlight: [[-0.12, 0, -0.12, 0.12, 6, 0.12, 0x707880], [0, 5.8, -0.1, 1.6, 6, 0.1, 0x707880], [1.3, 5.65, -0.2, 1.9, 5.9, 0.2, 0xfff2b0]],
  crate: [[-0.6, 0, -0.6, 0.6, 1.2, 0.6, 0xb07a4a]],
  chair: [[-0.25, 0.42, -0.25, 0.25, 0.48, 0.25, 0xffffff, 1], [-0.25, 0.48, 0.2, 0.25, 0.95, 0.25, 0xffffff, 1], [-0.24, 0, -0.24, -0.2, 0.42, -0.2, 0xdddddd], [0.2, 0, -0.24, 0.24, 0.42, -0.2, 0xdddddd], [-0.24, 0, 0.2, -0.2, 0.42, 0.24, 0xdddddd], [0.2, 0, 0.2, 0.24, 0.42, 0.24, 0xdddddd]],
  bench: [[-1, 0.42, -0.25, 1, 0.5, 0.25, 0xb07a4a], [-1, 0, -0.2, -0.9, 0.42, 0.2, 0x444444], [0.9, 0, -0.2, 1, 0.42, 0.2, 0x444444], [-1, 0.5, 0.2, 1, 0.9, 0.25, 0xb07a4a]],
  watertank: [[-1.6, 0, -1.6, 1.6, 2.2, 1.6, 0x707880], [-1.4, 2.2, -1.4, 1.4, 4.6, 1.4, 0xc0683a], [-1.0, 4.6, -1.0, 1.0, 5.2, 1.0, 0x8a4a2a]],
  barrel: [[-0.3, 0, -0.3, 0.3, 0.9, 0.3, 0x2a6aa0, 1]],
};
export function registerCodeProp(id, boxes) { CODE[id] = boxes; MODELS.delete(id); }

function codeModel(id) {
  const list = CODE[id] || [[-0.5, 0, -0.5, 0.5, 1, 0.5, 0xff00dc]];
  const groups = { 0: [], 1: [] };
  for (const [x0, y0, z0, x1, y1, z1, c, paint] of list) {
    const g = new THREE.BoxGeometry(x1 - x0, y1 - y0, z1 - z0).toNonIndexed();
    g.translate((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2);
    const col = new THREE.Color(c), n = g.attributes.position.count, a = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) { const sh = 0.75 + 0.25 * Math.min(1, (g.attributes.position.getY(i) - y0 + 0.2)); a[i * 3] = col.r * sh; a[i * 3 + 1] = col.g * sh; a[i * 3 + 2] = col.b * sh; }
    g.setAttribute('color', new THREE.BufferAttribute(a, 3));
    g.deleteAttribute('uv');
    groups[paint ? 1 : 0].push(g);
  }
  const parts = [];
  for (const k of [0, 1]) if (groups[k].length) {
    const geo = mergeGeometries(groups[k]);
    const mat = snap(new THREE.MeshLambertMaterial({ vertexColors: true, name: k ? 'paint' : 'body' }));
    parts.push({ geo, mat, paint: !!k });
  }
  return parts;
}

// a loaded glTF scene -> parts merged by material (transforms baked in), so one prop = a few draw calls
function glbParts(scene, lod1 = false) {
  scene.updateMatrixWorld(true);
  const byMat = new Map();
  // the far copy: '*_lod1' (the story props) or a bare 'lod1' node (the props lane's p_*.glb; three.js may rename 'lod1.001'
  // to 'lod1001', the original name is in userData.name)
  const LOD = /_lod1|^lod1(\.\d+|\d*)$/i, isLod = (o) => { for (let q = o; q; q = q.parent) if (LOD.test(q.userData && q.userData.name || '') || LOD.test(q.name)) return true; return false; };
  scene.traverse((o) => {
    if (!o.isMesh || /_col$/.test(o.name) || isLod(o) !== lod1) return;
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    const geo = o.geometry.clone().applyMatrix4(o.matrixWorld);
    const take = (g, m) => { if (!byMat.has(m)) byMat.set(m, []); byMat.get(m).push(g); };
    if (mats.length === 1) take(geo, mats[0]);
    else for (const gr of geo.groups) { const g = geo.clone(); g.setIndex(geo.index ? Array.from(geo.index.array.slice(gr.start, gr.start + gr.count)) : null); g.clearGroups(); take(g, mats[gr.materialIndex]); }
  });
  const parts = [];
  for (const [m, list] of byMat) {
    const norm = list.map((g) => { for (const k of Object.keys(g.attributes)) if (!['position', 'normal', 'uv', 'color'].includes(k)) g.deleteAttribute(k); return g.index ? g : g; });
    const keys = (g) => Object.keys(g.attributes).sort().join();
    const k0 = keys(norm[0]);
    const geo = norm.every((g) => keys(g) === k0) ? mergeGeometries(norm) : norm[0];
    if (!geo) continue;
    for (const t of ['map', 'emissiveMap']) if (m[t]) { m[t].magFilter = THREE.NearestFilter; m[t].minFilter = THREE.NearestMipmapNearestFilter; }
    if (env && 'envMap' in m) { m.envMap = env; m.envMapIntensity = m.metalness > 0.5 ? 0.9 : 0.3; }
    parts.push({ geo, mat: snap(m), paint: /paint/.test(m.name || '') });
  }
  return parts;
}

const loader = new GLTFLoader();
// which files exist: the story's own (public/models/story/index.json, written by the Blender scripts) and the PvP
// props (the server's /models/list). asked once, so a prop with no file never 404s
let have = null;
const manifest = () => have || (have = Promise.all([
  fetch('/models/story/index.json').then((r) => (r.ok ? r.json() : [])).catch(() => []),
  fetch('/models/list').then((r) => (r.ok ? r.json() : [])).catch(() => []),
]).then(([story, list]) => ({ story: new Set(Array.isArray(story) ? story : []), pvp: new Set(list.map((m) => m.id)) })));
function load(id) {
  const e = { parts: codeModel(id), state: 'loading' }; e.code = e.parts;
  MODELS.set(id, e);
  manifest().then((m) => {
    const u = m.story.has('s_' + id) ? '/models/story/s_' + id + '.glb' : m.pvp.has('p_' + id) ? '/models/p_' + id + '.glb' : null;
    if (!u) { e.state = 'code'; return; }
    loader.load(u, (gltf) => {
      const parts = glbParts(gltf.scene), lod1 = glbParts(gltf.scene, true); // full meshes, and the *_lod1 copy for mid distance
      if (parts.length) { e.parts = parts; e.lod1 = lod1.length ? lod1 : null; e.state = 'glb'; e.url = u; for (const f of listeners) f(id); } else e.state = 'code';
    }, undefined, () => { e.state = 'code'; });
  });
  return e;
}
export const propModel = (id) => MODELS.get(id) || load(id);
export const propStates = () => Object.fromEntries([...MODELS].map(([k, v]) => [k, v.state]));

// instances: [{ id, x, y, z, yaw, s, v }] -> a Group of InstancedMeshes (caller disposes the old group with freeProps)
const PAINTS = [0xc8202c, 0x2050b0, 0xe8e8e8, 0x26262a, 0x2a8a4a, 0xe8c020, 0xff7ab0, 0x5fd3c6, 0xff9a4d, 0x9a7aff];
// a variant number wraps over the first eight, as it always did (washing lines count far past 8); the colours added
// after those (container orange, container purple) are asked for from below zero: -1, -2 (shared/city/kit.js paintOf)
const paintHex = (v) => PAINTS[v < 0 ? Math.min(PAINTS.length - 1, 7 - v) : v % 8];
const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), sc = new THREE.Vector3(), ps = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0), col = new THREE.Color();
// how far out each prop keeps its full Blender model, as a share of the preset's propsHi: small things that repeat
// a thousand times go simple sooner, landmarks stay detailed further
const DETAIL = { door_bottom: 0.4, shutter: 0.35, acunit: 0.35, pchair: 0.5, laundry_a: 0.5, laundry_b: 0.5, stringlights: 0.5, wokdish: 0.45, tooth: 0.5, tooth_b: 0.5, eyeball: 0.5, crate_soup: 0.5, scooter: 0.6,
  ribarch: 3, lung: 2, machine: 4, gutgate: 4, smilesign: 2, sphincter: 1.4, lostfound_sign: 4, launderette: 3, gristlelogo: 2, choirpipe: 2, bus: 1.5 };
export const propDetail = (id) => DETAIL[id] || 1;
DETAIL.smilesign = 1; DETAIL.tarp = 0.6; DETAIL.lostpile = 0.5; DETAIL.sofa = 0.6; DETAIL.fridge = 0.6;
// small things that repeat by the thousand aren't drawn at all past this (x the preset's props radius / 224): the
// house's own far box carries its look out there
const FAR = { door_bottom: 70, shutter: 60, acunit: 60, laundry_a: 90, laundry_b: 90, pchair: 70, stringlights: 80, wokdish: 70, crate_soup: 60, scooter: 70, tooth: 60, tooth_b: 60, eyeball: 70, cone: 70, skeleton_lanyard: 70, paperdrift: 90, lostpile: 90, tarp: 90, sofa: 90, fridge: 90, smilesign: 160, filecab: 100, rubble_a: 120, rubble_b: 120, tirestack: 100 };
// the Bottom's house kit and the Long Stairs pieces: there are hundreds a chunk, so they drop to their far model early and stop being drawn past a street or two
Object.assign(DETAIL, { cube_eave: 0.5, cube_window_a: 0.4, cube_window_b: 0.4, cube_window_c: 0.4, cube_corner: 0.4, stair_step: 0.4, stair_post: 0.4, container_doors: 0.6, longstep_a: 0.6, longstep_b: 0.6, longrail: 0.6, longplaque_a: 0.3, longplaque_b: 0.3 });
Object.assign(DETAIL, { cube_corner_b: 0.4, cube_eave_b: 0.5, cube_eave4: 0.5, cube_eave6: 0.5, cube_eave6_b: 0.5, longrail_b: 0.6 }); // (the kit's second pass)
Object.assign(FAR, { cube_eave: 90, container_rib: 90, cube_window_a: 70, cube_window_b: 70, cube_window_c: 70, cube_corner: 70, stair_step: 70, stair_post: 70, container_doors: 120, cube_roofjunk_a: 120, cube_roofjunk_b: 120, longplaque_a: 40, longplaque_b: 40 });
Object.assign(FAR, { cube_corner_b: 70, cube_eave_b: 90, cube_eave4: 90, cube_eave6: 90, cube_eave6_b: 90, container_rib_half: 90 });
export const propFar = (id) => FAR[id] || Infinity;
// hiR: instances closer than this (x the prop's DETAIL) to `at` get the full Blender model, the rest its _lod1 meshes
// (or the code model when the file has none)
export function buildPropGroup(list, hiR = 1e9, at = null, farK = 1) {
  const byId = new Map();
  for (const p of list) {
    if (at && Math.hypot(p.x - at.x, p.z - at.z) > propFar(p.id) * farK) continue;
    const m = propModel(p.id), glb = m.parts !== m.code, hi = glb && (!at || Math.hypot(p.x - at.x, p.z - at.z) < hiR * propDetail(p.id));
    const parts = hi ? m.parts : (glb && m.lod1) || m.code, k = p.id + (hi ? '' : parts === m.code ? '~' : '_lod1');
    if (!byId.has(k)) byId.set(k, { parts, list: [] });
    byId.get(k).list.push(p);
  }
  const g = new THREE.Group(); g.name = 'cityprops';
  for (const [id, { parts, list: ps0 }] of byId) {
    for (const part of parts) {
      const im = new THREE.InstancedMesh(part.geo, part.mat, ps0.length);
      ps0.forEach((p, i) => {
        q.setFromAxisAngle(up, p.yaw); sc.setScalar(p.s || 1); ps.set(p.x, p.y, p.z);
        im.setMatrixAt(i, m4.compose(ps, q, sc));
        if (part.paint) im.setColorAt(i, col.setHex(paintHex(p.v | 0)));
      });
      im.instanceMatrix.needsUpdate = true;
      im.computeBoundingSphere();
      im.userData.propId = id;
      g.add(im);
    }
  }
  return g;
}
export function freeProps(g) { if (!g) return; g.removeFromParent(); for (const c of g.children) c.dispose(); }
