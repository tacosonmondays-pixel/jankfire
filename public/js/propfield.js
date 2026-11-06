// Blender props on the maps (round 4): every copy of a prop is one GPU instance, so a map draws each prop type in one
// call per material however many copies it has (a forest of 2500 pines included). Placements come from the map
// builder (shared/propcap.js): the client fits each model onto exactly the boxes it stands in for. Look-only: the boxes
// stay the collisions, and they're drawn instead whenever a model is missing (world.js asks drawnByModel()).
// Near copies get the full model (it casts shadows), far ones the low-poly `lod1`; copies out of view or deep in the
// fog aren't drawn. A map's prop files download when the map loads (glbkit.js LAZY) and are shared between maps.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { AUTHORED, LAZY, prefetch, whenLate } from './glbkit.js';
import { hazeUniforms } from './world.js';
import { shadowDirty } from './lighting.js';
import { G } from './ctx.js';
import { MAPS } from '/shared/map.js';

// round 1's car paints (the parked car's colours), used for car tints
const PAINT = { carred: 0xc8202c, carblue: 0x2050b0, carwhite: 0xe8e8e8, carblack: 0x26262a, cargreen: 0x2a8a4a, caryellow: 0xe8c020, burnt: 0x2a2624 };
const PATTERN = new Set(['leopard', 'camo', 'adfun']); // tints that are a picture, not a colour: their own group, the texture on
// parked cars: the traffic models (they face +z, the box car faces +x), round 1's car if those aren't there
const PARKED = ['p_car_sedan', 'p_car_hatch', 'p_car_sedan', 'p_car_hatch', 'p_car_taxi'];
const stripN = (n) => (n || '').replace(/\.\d+$/, ''); // (Blender keeps names unique in one session: lod1.001, tint.002)
const isLod1 = (o) => { for (let p = o; p; p = p.parent) if (stripN(p.name) === 'lod1') return true; return false; };

let field = null; // { group, kinds: [...], cam: {...} }
let MATS = null; // world.js's map materials (tints)
const kindCache = new Map(); // model id + variant -> { lod0, lod1, lo, hi, lod, tint }

// ---------------------------------------------------------------- which model draws a placement
const hash = (x, z) => { const s = Math.sin(x * 12.9898 + z * 78.233) * 43758.5453; return s - Math.floor(s); };
function modelFor(p) {
  if (!p.a) return AUTHORED['p_' + p.id] ? { mid: 'p_' + p.id, turn: 0 } : null; // round 1's records ({ p, r, s })
  if (p.id === 'car') {
    const k = (hash(p.a[0], p.a[2]) * PARKED.length) | 0;
    for (let i = 0; i < PARKED.length; i++) { const m = PARKED[(k + i) % PARKED.length]; if (AUTHORED[m]) return { mid: m, turn: Math.PI / 2 }; }
    return AUTHORED.p_car ? { mid: 'p_car', turn: 0 } : null;
  }
  return AUTHORED['p_' + p.id] ? { mid: 'p_' + p.id, turn: 0 } : null;
}
// world.js: does a model draw this tag's boxes? (the boxes are skipped then)
let off = false; // (tests: the box version, for side-by-side sheets: tools/blender/shots_r4.cjs)
export function propsOff(v) { off = !!v; }
export function drawnByModel(pv) {
  if (off) return false;
  if (pv === 'car') return PARKED.some((m) => AUTHORED[m]) || !!AUTHORED.p_car;
  return !!AUTHORED['p_' + pv];
}
// the files a map needs (+ the traffic models if it has traffic)
export function modelsFor(def, traffic) {
  const ids = new Set();
  for (const l of [def && def.boxes && def.boxes.props, def && def.deco && def.deco.props]) for (const p of l || []) {
    if (p.id === 'car' && p.a) { for (const m of PARKED) ids.add(m); ids.add('p_car'); } else ids.add('p_' + p.id);
  }
  if (traffic) for (const t of traffic) ids.add('p_car_' + t);
  return [...ids];
}

// ---------------------------------------------------------------- a model -> merged geometry per material, per LOD
function attrF(g, name, size, fill) { // every merged part needs the same attributes, as floats
  const a = g.getAttribute(name), n = g.getAttribute('position').count, out = new Float32Array(n * size);
  if (a) { for (let i = 0; i < n; i++) for (let c = 0; c < size; c++) out[i * size + c] = c < a.itemSize ? a.getComponent(i, c) : fill; }
  else out.fill(fill);
  g.setAttribute(name, new THREE.BufferAttribute(out, size));
}
function clean(g, m) {
  g = g.clone().applyMatrix4(m);
  for (const k of Object.keys(g.attributes)) if (!['position', 'normal', 'uv', 'color'].includes(k)) g.deleteAttribute(k);
  if (!g.getAttribute('normal')) g.computeVertexNormals();
  attrF(g, 'position', 3, 0); attrF(g, 'normal', 3, 0); attrF(g, 'uv', 2, 0); attrF(g, 'color', 3, 1);
  if (!g.index) { const n = g.getAttribute('position').count, ix = new (n > 65535 ? Uint32Array : Uint16Array)(n); for (let i = 0; i < n; i++) ix[i] = i; g.setIndex(new THREE.BufferAttribute(ix, 1)); }
  g.morphAttributes = {}; g.clearGroups();
  return g;
}
// a prop material: the model's own, plus the city haze (instancing-aware) and the potato snap it already has
function propMat(m, glow) {
  let out;
  if (glow) { // lamps, lit panels: unlit, always bright
    const c = m.emissive && m.emissive.getHex() ? m.emissive.clone() : m.color.clone();
    out = new THREE.MeshBasicMaterial({ name: m.name, color: c, map: m.emissiveMap || m.map || null });
    out.toneMapped = false;
  } else { out = m.clone(); out.vertexColors = true; }
  const prev = m.onBeforeCompile; // (jankify's vertex snap)
  out.onBeforeCompile = (sh, r) => {
    if (prev && prev !== THREE.Material.prototype.onBeforeCompile) prev(sh, r);
    sh.uniforms.uHaze = hazeUniforms.uHaze; sh.uniforms.uHazeColor = hazeUniforms.uHazeColor; sh.uniforms.uHazeK = { value: glow ? 0.45 : 1 };
    sh.vertexShader = 'varying float vHazeY;\n' + sh.vertexShader.replace('#include <fog_vertex>', `#include <fog_vertex>
	#ifdef USE_INSTANCING
	vHazeY = ( modelMatrix * instanceMatrix * vec4( transformed, 1.0 ) ).y;
	#else
	vHazeY = ( modelMatrix * vec4( transformed, 1.0 ) ).y;
	#endif`);
    sh.fragmentShader = 'uniform vec4 uHaze;\nuniform vec3 uHazeColor;\nuniform float uHazeK;\nvarying float vHazeY;\n' + sh.fragmentShader.replace('#include <fog_fragment>', HAZE_FOG);
  };
  out.customProgramCacheKey = () => 'prop' + (glow ? 'g' : '') + (prev ? 'j' : '');
  out.userData.shared = true;
  return out;
}
const HAZE_FOG = `#ifdef USE_FOG
	#ifdef FOG_EXP2
		float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	vec3 fogC = fogColor;
	if ( uHaze.x > 0.0 ) {
		float hz = clamp( ( uHaze.y - vHazeY ) / ( uHaze.y - uHaze.z ), 0.0, 1.0 );
		float hf = uHaze.x * uHazeK * hz * ( 0.35 + 0.65 * hz ) * ( 1.0 - exp( - vFogDepth / uHaze.w ) );
		fogC = mix( fogColor, uHazeColor, clamp( hf / max( 0.001, fogFactor + hf ), 0.0, 1.0 ) );
		fogFactor = 1.0 - ( 1.0 - fogFactor ) * ( 1.0 - hf );
	}
	gl_FragColor.rgb = mix( gl_FragColor.rgb, fogC, fogFactor );
#endif`;

function kindOf(mid, v, turn) {
  const key = mid + '|' + (v ?? '') + '|' + turn;
  if (kindCache.has(key)) return kindCache.get(key);
  const a = AUTHORED[mid];
  let root = a.scene;
  if (v !== undefined && v !== null) { // a variant: a node named like it ('bay', 'n7', ...), drawn from its own origin
    const names = [String(v), 'n' + v, 'v' + v];
    a.scene.traverse((o) => { if (root === a.scene && names.includes(o.name)) root = o; });
  }
  a.scene.updateMatrixWorld(true);
  const inv = new THREE.Matrix4().copy(root.matrixWorld).invert(), base = new THREE.Matrix4().makeRotationY(turn);
  const parts = [new Map(), new Map()], box = new THREE.Box3(), tmp = new THREE.Box3();
  root.traverse((o) => {
    if (!o.isMesh || !o.geometry) return;
    const far = isLod1(o) ? 1 : 0, mats = Array.isArray(o.material) ? o.material : [o.material];
    const m = new THREE.Matrix4().multiplyMatrices(inv, o.matrixWorld).premultiply(base);
    const geo = o.geometry, groups = Array.isArray(o.material) && geo.groups.length ? geo.groups : [{ start: 0, count: Infinity, materialIndex: 0 }];
    for (const gr of groups) {
      const mat = mats[gr.materialIndex] || mats[0];
      let g = geo;
      if (groups.length > 1) { g = geo.clone(); g.setDrawRange(0, Infinity); const ix = geo.index.array.slice(gr.start, gr.start + gr.count); g.setIndex(new THREE.BufferAttribute(ix, 1)); }
      const c = clean(g, m);
      if (!far) { c.computeBoundingBox(); tmp.copy(c.boundingBox); box.union(tmp); }
      const name = stripN(mat.name), k = name + '#' + mat.uuid;
      if (!parts[far].has(k)) parts[far].set(k, { mat, name, list: [] });
      parts[far].get(k).list.push(c);
    }
  });
  const build = (map) => [...map.values()].map(({ mat, name, list }) => {
    const geo = list.length > 1 ? mergeGeometries(list, false) : list[0];
    const glow = name === 'glow' || (mat.emissive && mat.emissive.getHex() && mat.emissiveIntensity > 0.5 && !mat.map);
    return { geo, mat: propMat(mat, glow), tint: name === 'tint' || name === 'car_paint', glow };
  }).filter((p) => p.geo);
  const meta = a.meta || {};
  const k = { lod0: build(parts[0]), lod1: build(parts[1]), lo: box.min.clone(), hi: box.max.clone(), lod: Number.isFinite(meta.lod) ? meta.lod : 55, tint: meta.tint !== false, box: null };
  const mb = meta.box; // [[x0, y0, z0], [x1, y1, z1]] in the file's space (turned like the model)
  if (Array.isArray(mb) && mb.length === 2 && mb.every((v) => Array.isArray(v) && v.length === 3 && v.every(Number.isFinite))) {
    k.box = new THREE.Box3(new THREE.Vector3(...mb[0]), new THREE.Vector3(...mb[1])).applyMatrix4(base);
  }
  if (box.isEmpty()) { k.lo.set(-0.5, 0, -0.5); k.hi.set(0.5, 1, 0.5); }
  kindCache.set(key, k);
  return k;
}

// what the model was built against: meta.box (the box version's extent at the builder's reference sizes), or, for a
// prop every copy of which has the same boxes on every map, that extent. Mapped onto each copy's extent, so details
// that stick out of the boxes keep their size. Neither: the model's own bounding box is fitted onto the boxes
let fixed = null;
function fixedExtent(id) {
  if (!fixed) {
    fixed = new Map();
    const seen = new Map();
    for (const m of Object.values(MAPS)) for (const l of [m.boxes && m.boxes.props, m.deco && m.deco.props]) for (const p of l || []) {
      if (!p.a) continue;
      const e = seen.get(p.id);
      if (!e) seen.set(p.id, { lo: p.lo, hi: p.hi, same: true });
      else if (e.same && [0, 1, 2].some((i) => Math.abs(e.lo[i] - p.lo[i]) > 0.02 || Math.abs(e.hi[i] - p.hi[i]) > 0.02)) e.same = false;
    }
    for (const [id, e] of seen) if (e.same) fixed.set(id, new THREE.Box3(new THREE.Vector3(...e.lo), new THREE.Vector3(...e.hi)));
  }
  return fixed.get(id) || null;
}
function refOf(k, id) {
  const b = k.box;
  if (b) return b;
  return fixedExtent(id) || new THREE.Box3(k.lo, k.hi);
}

// ---------------------------------------------------------------- tints: a map material's colour
const tintCache = new Map();
function tintOf(t) {
  if (tintCache.has(t)) return tintCache.get(t);
  let c = new THREE.Color(1, 1, 1);
  if (PAINT[t] !== undefined) c.setHex(PAINT[t]);
  else if (MATS && MATS[t]) {
    const m = MATS[t].mat;
    c.copy(m.color || c);
    if (m.isMeshBasicMaterial === false && m.emissive && m.emissive.getHex() > 0 && c.getHex() < 0x202020) c.copy(m.emissive);
    const img = m.map && m.map.image;
    if (img && img.width) { // the texture's average colour
      try {
        const cv = document.createElement('canvas'); cv.width = 8; cv.height = 8;
        const g = cv.getContext('2d'); g.drawImage(img, 0, 0, 8, 8);
        const d = g.getImageData(0, 0, 8, 8).data; let r = 0, gg = 0, b = 0;
        for (let i = 0; i < d.length; i += 4) { r += d[i]; gg += d[i + 1]; b += d[i + 2]; }
        const n = d.length / 4, avg = new THREE.Color().setRGB(r / n / 255, gg / n / 255, b / n / 255, THREE.SRGBColorSpace);
        c.multiply(avg);
      } catch { /* a texture we can't read: its colour alone */ }
    }
  }
  tintCache.set(t, c);
  return c;
}

// ---------------------------------------------------------------- placements -> instance matrices
const _m = new THREE.Matrix4(), _r = new THREE.Matrix4(), _s = new THREE.Matrix4(), _t = new THREE.Matrix4();
function placeMatrix(p, k, ref, out) {
  if (!p.a) { // round 1: position, quarter turns, uniform scale
    out.makeRotationY(-(p.r || 0) * Math.PI / 2).premultiply(_t.makeTranslation(p.p[0], p.p[1], p.p[2]));
    if (p.s) out.multiply(_s.makeScale(p.s, p.s, p.s));
    return;
  }
  const ml = ref.min, mh = ref.max, ex = (i) => p.hi[i] - p.lo[i], md = (i) => [mh.x - ml.x, mh.y - ml.y, mh.z - ml.z][i];
  const sc = (i) => (md(i) > 1e-3 && ex(i) > 1e-3 ? ex(i) / md(i) : 1);
  if (p.f !== undefined) { // turned on its own (trees, pots): even across, fitted up, round its own origin
    const sh = (sc(0) + sc(2)) / 2, sy = sc(1);
    out.makeTranslation(0, -ml.y, 0).premultiply(_s.makeScale(sh, sy, sh)).premultiply(_r.makeRotationY(p.y)).premultiply(_t.makeTranslation(p.a[0], p.a[1] + p.lo[1], p.a[2]));
    return;
  }
  // fitted per axis onto its boxes, in its own frame
  out.makeTranslation(-ml.x, -ml.y, -ml.z).premultiply(_s.makeScale(sc(0), sc(1), sc(2))).premultiply(_t.makeTranslation(p.lo[0], p.lo[1], p.lo[2]))
    .premultiply(_r.makeRotationY(p.y)).premultiply(_m.makeTranslation(p.a[0], p.a[1], p.a[2]));
}

// ---------------------------------------------------------------- build the field for a map
export function buildPropField(scene, def, mats) {
  MATS = mats || MATS;
  if (field) { scene.remove(field.group); for (const k of field.kinds) for (const m of k.meshes) m.dispose(); field = null; }
  const lists = off ? [] : [def && def.boxes && def.boxes.props, def && def.deco && def.deco.props];
  const groups = new Map();
  for (const l of lists) for (const p of l || []) {
    const mf = modelFor(p);
    if (!mf) continue;
    const t = p.a ? p.t : p.color, pat = t && PATTERN.has(t) ? t : '';
    const key = mf.mid + '|' + (p.v ?? '') + '|' + mf.turn + '|' + pat;
    if (!groups.has(key)) groups.set(key, { mf, v: p.v, pat, list: [] });
    groups.get(key).list.push(p);
  }
  if (!groups.size) return;
  const group = new THREE.Group(); group.name = 'propfield';
  const kinds = [];
  for (const { mf, v, pat, list } of groups.values()) {
    const k = kindOf(mf.mid, v, mf.turn), n = list.length, ref = list[0].a ? refOf(k, list[0].id) : null;
    const mats = new Float32Array(n * 16), cols = new Float32Array(n * 3), ctr = new Float32Array(n * 4);
    const c = new THREE.Vector3(), mid = new THREE.Vector3().addVectors(k.lo, k.hi).multiplyScalar(0.5), rad = k.hi.distanceTo(k.lo) / 2;
    for (let i = 0; i < n; i++) {
      const p = list[i];
      placeMatrix(p, k, ref, _m);
      _m.toArray(mats, i * 16);
      c.copy(mid).applyMatrix4(_m); ctr[i * 4] = c.x; ctr[i * 4 + 1] = c.y; ctr[i * 4 + 2] = c.z; ctr[i * 4 + 3] = rad * Math.max(_m.getMaxScaleOnAxis(), 0.2);
      const t = p.a ? p.t : p.color, col = k.tint && t && !pat ? tintOf(t) : WHITE;
      cols[i * 3] = col.r; cols[i * 3 + 1] = col.g; cols[i * 3 + 2] = col.b;
    }
    const kind = { k, n, mats, cols, ctr, meshes: [], lods: [] };
    for (const [li, parts] of [[0, k.lod0], [1, k.lod1.length ? k.lod1 : null]]) {
      if (!parts) { kind.lods.push(null); continue; }
      const im = new THREE.InstancedBufferAttribute(new Float32Array(n * 16), 16); im.setUsage(THREE.DynamicDrawUsage);
      const ic = new THREE.InstancedBufferAttribute(new Float32Array(n * 3), 3); ic.setUsage(THREE.DynamicDrawUsage);
      const meshes = [];
      for (const part of parts) {
        let mat = part.mat;
        if (pat && part.tint) { mat = part.mat.clone(); mat.onBeforeCompile = part.mat.onBeforeCompile; mat.customProgramCacheKey = part.mat.customProgramCacheKey; const src = MATS && MATS[pat] && MATS[pat].mat; if (src) { mat.map = src.map; mat.color.copy(src.color); } mat.userData.shared = true; }
        const mesh = new THREE.InstancedMesh(part.geo, mat, n);
        mesh.instanceMatrix = im;
        if (part.tint && !pat) mesh.instanceColor = ic;
        mesh.count = 0; mesh.visible = false; mesh.frustumCulled = false; // (each copy is culled here, not the whole lot)
        mesh.matrixAutoUpdate = false;
        if (li === 1) mesh.userData.noCast = true; // far copies cast no shadow
        mesh.name = 'prop:' + mf.mid + (li ? ':lod1' : '');
        group.add(mesh); meshes.push(mesh); kind.meshes.push(mesh);
      }
      kind.lods.push({ im, ic, meshes, idx: new Int32Array(n), count: 0 });
    }
    kinds.push(kind);
  }
  scene.add(group);
  field = { group, kinds, cam: { x: NaN, y: 0, z: 0, dx: 0, dy: 0, dz: 0, f: 0, sum: -1, lastDirty: -99 } };
  updatePropField(G.camera, true);
}
const WHITE = new THREE.Color(1, 1, 1);

// ---------------------------------------------------------------- per frame: which copies, which LOD
const frus = new THREE.Frustum(), pm = new THREE.Matrix4(), wide = new THREE.PerspectiveCamera(), sph = new THREE.Sphere(), fw = new THREE.Vector3();
export let propStats = { kinds: 0, near: 0, far: 0 };
export function updatePropField(cam, force) {
  if (!field || !cam) return;
  const s = field.cam, p = cam.position;
  cam.getWorldDirection(fw);
  s.f++;
  const moved = (p.x - s.x) ** 2 + (p.y - s.y) ** 2 + (p.z - s.z) ** 2 > 2.25, turned = fw.x * s.dx + fw.y * s.dy + fw.z * s.dz < 0.994;
  if (!force && !moved && !turned && s.f % 30) return;
  s.x = p.x; s.y = p.y; s.z = p.z; s.dx = fw.x; s.dy = fw.y; s.dz = fw.z;
  // a frustum a good bit wider than the camera's (it's only redone after a turn or a step)
  wide.fov = Math.min(150, cam.fov + 26); wide.aspect = cam.aspect * 1.2; wide.near = 0.1; wide.far = (G.scene.fog ? G.scene.fog.far : 400) + 60;
  wide.position.copy(p); wide.quaternion.copy(cam.quaternion); wide.updateMatrixWorld(); wide.updateProjectionMatrix();
  frus.setFromProjectionMatrix(pm.multiplyMatrices(wide.projectionMatrix, wide.matrixWorldInverse));
  const far = wide.far, q = G.settings && G.settings.jank, lodK = q === 0 ? 0.6 : q === 1 ? 0.8 : q === 3 ? 1.25 : 1;
  let nN = 0, nF = 0, sum = 0;
  for (const kind of field.kinds) {
    const { ctr, mats, cols, n } = kind, L0 = kind.lods[0], L1 = kind.lods[1];
    const r0 = Math.min(far, kind.k.lod * lodK), r02 = r0 * r0, near2 = 24 * 24, far2 = far * far;
    let c0 = 0, c1 = 0;
    for (let i = 0; i < n; i++) {
      const x = ctr[i * 4] - p.x, y = ctr[i * 4 + 1] - p.y, z = ctr[i * 4 + 2] - p.z, rr = ctr[i * 4 + 3], d2 = x * x + y * y + z * z;
      if (d2 > far2 + 2 * far * rr + rr * rr) continue; // past the fog
      const close = d2 < near2 + 48 * rr + rr * rr;
      sph.center.set(ctr[i * 4], ctr[i * 4 + 1], ctr[i * 4 + 2]); sph.radius = rr;
      if (!close && !frus.intersectsSphere(sph)) continue;
      if (d2 < r02 || !L1) L0.idx[c0++] = i; else L1.idx[c1++] = i;
    }
    for (const [L, c] of [[L0, c0], [L1, c1]]) {
      if (!L) continue;
      const im = L.im.array, ic = L.ic.array;
      for (let j = 0; j < c; j++) { const i = L.idx[j]; im.set(mats.subarray(i * 16, i * 16 + 16), j * 16); ic[j * 3] = cols[i * 3]; ic[j * 3 + 1] = cols[i * 3 + 1]; ic[j * 3 + 2] = cols[i * 3 + 2]; }
      if (L === L0) for (let j = 0; j < c; j++) sum = (sum + (L.idx[j] + 1) * 2654435761) % 4294967291;
      L.count = c;
      L.im.clearUpdateRanges(); L.im.addUpdateRange(0, c * 16); L.im.needsUpdate = true;
      L.ic.clearUpdateRanges(); L.ic.addUpdateRange(0, c * 3); L.ic.needsUpdate = true;
      for (const m of L.meshes) { m.count = c; m.visible = c > 0; }
    }
    nN += c0; nF += c1;
  }
  propStats = { kinds: field.kinds.length, near: nN, far: nF };
  // the near copies cast the shadows: a new set means a new shadow map (not more than every 20 frames while walking)
  if (sum !== s.sum && (force || s.f - s.lastDirty >= 20)) { s.sum = sum; s.lastDirty = s.f; shadowDirty(); }
}

// ---------------------------------------------------------------- per-map downloads
let want = null; // the map whose props are on their way
const asked = new Set();
export function fetchMapProps(def, id, traffic, onReady) {
  want = id;
  const ids = modelsFor(def, traffic).filter((m) => !AUTHORED[m] && (LAZY.has(m) || asked.has(m))); // (not there yet, and has a file)
  if (!ids.length) return;
  let left = ids.length, t = 0;
  const done = () => { clearTimeout(t); t = setTimeout(() => { if (want === id) onReady(); }, left ? 900 : 60); }; // (one rebuild for a burst of files)
  for (const m of ids) { asked.add(m); whenLate(m, () => { left--; done(); }); }
  prefetch(ids);
}
export const propInfo = () => ({ ...propStats, cached: kindCache.size });
