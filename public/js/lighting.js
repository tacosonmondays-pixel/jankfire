// Lighting: real sun shadows that follow you, a per-map mood (sun angle, shadow depth, a coloured bounce light), a few
// pooled point lights by the neon and lamps, glowing light pools on the floor under them, baked corner AO on the boxes,
// and the viewmodel going dim when you stand in shade. world.js owns the scene; this just lights it.
// cost rules: the shadow camera snaps to a coarse grid (it only re-renders when it moves or something alive is near),
// light counts never change at runtime (that would recompile every shader), and nothing here allocates per frame.
import * as THREE from 'three';
import { G } from './ctx.js';

// ------------------------------------------------------------ quality
// size = shadow map, half = metres from the shadow centre to its edge, every = refresh every n frames while people move,
// pool = pooled point lights lit, near = remotes closer than this cast real shadows (the rest keep the blob), spot = your
// flashlight casts shadows too (Scary Forest)
export const SHQ = {
  low: { size: 1024, hard: true, soft: false, half: 36, every: 3, pool: 0, near: 26, spot: false },
  med: { size: 2048, soft: false, half: 50, every: 2, pool: 2, near: 40, spot: false },
  high: { size: 3072, soft: true, half: 60, every: 1, pool: 4, near: 56, spot: true },
};
const BY_PRESET = ['off', 'low', 'med', 'high']; // Potato, Crusty, Mid, Too HD
const POOL_N = 4; // point lights made once. only the preset's share is visible (a settings change recompiles shaders anyway)

// per-map mood. el = sun elevation (deg; its compass direction comes from the sun in the sky), sh = how dark shadows get,
// hk / sk = sky / sun brightness multipliers (default 0.82 / 1.14). fill = a coloured light from the other side (bounce off the sky / the room), so the shade isn't flat grey
const MOOD = {
  def: { el: 42, sh: 0.72, fill: [0x9ab8ff, 0.32] },
  crate: { el: 64, sh: 0.5, fill: [0xffc4ea, 0.3] },
  platform: { el: 50, sh: 0.6, fill: [0xb8c8e8, 0.3] },
  rooftop: { el: 38, sh: 0.7, fill: [0xff4fd8, 0.28] },
  suburb: { el: 40, sh: 0.74, fill: [0x9ab8ff, 0.34] },
  warehouse: { el: 50, sh: 0.66, fill: [0x8fb4ff, 0.32] },
  warehouse_sd: { el: 50, sh: 0.66, fill: [0x8fb4ff, 0.32] },
  desert: { el: 52, sh: 0.8, fill: [0xffd8a0, 0.22], sk: 0.95, hk: 0.86 }, // bright sand: no extra sun or it blows out
  bazaar: { el: 48, sh: 0.8, fill: [0xffe0b0, 0.24], sk: 1.0, hk: 0.86 },
  islands: { el: 30, sh: 0.72, fill: [0xff9ad8, 0.3], az: [170, -230] }, // towards the sun with a face
  skyline: { el: 26, sh: 0.74, fill: [0x7a8aff, 0.38] },
  range: { el: 46, sh: 0.7, fill: [0x9ab8ff, 0.3] },
  backrooms: { el: 78, sh: 0.42, fill: [0xfff3cc, 0.18], indoor: 1 },
  forest: { el: 52, sh: 0.85, fill: [0x4a5aa0, 0.22] }, // moonlight
  deadmall: { el: 74, sh: 0.5, fill: [0xffb070, 0.2], indoor: 1 },
  school: { el: 72, sh: 0.5, fill: [0x9ab8ff, 0.22], indoor: 1 },
  hospital: { el: 72, sh: 0.5, fill: [0xa8e0d8, 0.24], indoor: 1 },
  battleisland: { el: 52, sh: 0.5, fill: [0x7fd8ff, 0.34], sk: 1.25, hk: 0.78 }, // anime noon: a high hot sun, crisp shade, the sea's teal bouncing up (bilook.js does the sky)
  jankburg: { el: 32, sh: 0.7, fill: [0x4fd8ff, 0.3] },
};

// glowing materials (world.js / vibe.js keys) and the colour of the light they throw
const GLOW = {
  light: 0xfff2b0, lamp: 0xfff6c8, neonpink: 0xff2ad4, neoncyan: 0x19f0ff, neonyellow: 0xfff04d, neongreen: 0x5aff2a, neonred: 0xff2a3a,
  billboard: 0xffb0e8, signopen: 0xff4fd8, neonbar: 0x19f0ff, neonnoodle: 0xff4fd8, neonhotel: 0xfff04d, neonwork: 0xff2a3a,
  sitea: 0xff3a4a, siteb: 0x19e6ff, adbig1: 0xff4fd8, adstore: 0x19e6ff, adfun: 0x7aff1a, adclosed: 0xffe14d, flagcorp: 0x2a6cff,
  lantern: 0xffc46a, hazard2: 0xffa21a, lava: 0xff5a14, flame: 0xff7a1a,
  adcity1: 0x19e6ff, adcity2: 0xff2a3a, adcity3: 0x7aff1a, adcity4: 0xffe14d, adcity5: 0xff4fd8, adcity6: 0x19e6ff, tvstatic: 0xa0b0ff,
};

const L = {
  sun: null, fill: null, vmSun: null, vmBase: 1.5, sunBase: 1.8, pool: [], poolK: new Float32Array(POOL_N), poolT: new Float32Array(POOL_N),
  pref: 'auto', preset: 1, q: null, mood: MOOD.def, frame: 0, dirty: true, lx: NaN, ly: NaN, lz: NaN, passes: 0,
  spot: null, spotWant: false, cards: null, src: null, nSrc: 0, vmK: 1, vmT: 1, indoor: false, dyn: [], id: '',
};
const bx = new THREE.Vector3(), by = new THREE.Vector3(), bz = new THREE.Vector3(), dir = new THREE.Vector3(0.5, 0.6, -0.6).normalize();
const _v = new THREE.Vector3(), _fw = new THREE.Vector3(), _m = new THREE.Matrix4(), _zero = new THREE.Vector3(), _up = new THREE.Vector3(0, 1, 0);
const _c = new THREE.Color();
export const lightStats = { passes: 0, frames: 0 }; // shadow map renders (tests read it)

export function initLighting(sun, vmSun, noShadow) {
  L.sun = sun; L.vmSun = vmSun; L.vmBase = vmSun.intensity; L.sunBase = sun.intensity;
  L.vmHemi = G.vmScene.children.find((o) => o.isHemisphereLight) || null; L.vmHemiBase = L.vmHemi ? L.vmHemi.intensity : 1.8;
  const sc = G.scene;
  L.hemi = sc.children.find((o) => o.isHemisphereLight) || null;
  sc.add(sun.target);
  const s = sun.shadow;
  s.autoUpdate = false; // we say when (world.js renders every frame)
  s.camera.near = 1; s.camera.far = 420;
  s.bias = -0.0004; s.normalBias = 0.035;
  L.fill = new THREE.DirectionalLight(0x9ab8ff, 0); // after the sun: goggles.js / zombies.js take the first one as "the sun"
  sc.add(L.fill, L.fill.target);
  for (let i = 0; i < POOL_N; i++) { const p = new THREE.PointLight(0xffffff, 0, 13, 2); p.visible = false; sc.add(p); L.pool.push(p); }
  for (const o of noShadow) o.traverse((c) => { c.userData.noShadow = true; });
  G.renderer.shadowMap.type = THREE.PCFShadowMap;
  G.renderer.shadowMap.enabled = false;
  sun.castShadow = false;
}

// ------------------------------------------------------------ settings
// phones + tablets (touchboot.js): 'auto' is one step cheaper there (Crusty = blobs, Mid = low, Too HD = medium). picking a level yourself still wins
const TOUCH_STEP = typeof window !== 'undefined' && window.JF_TOUCH ? 1 : 0;
export function shadowLevel() { return L.pref === 'auto' ? BY_PRESET[Math.max(0, L.preset - TOUCH_STEP)] || 'low' : L.pref; }
export function setShadowPref(p) { L.pref = p === 'off' || SHQ[p] ? p : 'auto'; apply(); }
export function setLightPreset(i) { L.preset = i; apply(); }
function apply() {
  if (!L.sun) return;
  const r = G.renderer, lv = shadowLevel(), q = SHQ[lv] || null, was = L.q;
  L.q = q;
  const type = q && q.soft ? THREE.PCFSoftShadowMap : q && q.hard ? THREE.BasicShadowMap : THREE.PCFShadowMap; // low: one crunchy hard sample
  const typeChanged = r.shadowMap.type !== type, onChanged = !!was !== !!q;
  r.shadowMap.enabled = !!q; r.shadowMap.type = type;
  L.sun.castShadow = !!q;
  G.realShadows = !!q;
  if (q && (!was || was.size !== q.size)) {
    const s = L.sun.shadow;
    if (s.map) { s.map.dispose(); s.map = null; }
    s.mapSize.set(q.size, q.size);
    const h = q.half; Object.assign(s.camera, { left: -h, right: h, top: h, bottom: -h }); s.camera.updateProjectionMatrix();
    s.normalBias = 0.02 + (2 * h / q.size) * 0.7; // about a texel: no acne on the box faces, no floating feet
  }
  spotShadow();
  const np = q ? q.pool : 0; // every visible light costs every pixel, lit or not
  for (let i = 0; i < POOL_N; i++) L.pool[i].visible = i < np;
  if (typeChanged || onChanged) G.scene.traverse((o) => { const m = o.material; if (!m) return; if (Array.isArray(m)) for (const x of m) x.needsUpdate = true; else m.needsUpdate = true; }); // new shader variant
  L.dirty = true; L.lx = NaN;
}
function spotShadow() {
  const want = !!(L.q && L.q.spot && L.spot);
  if (L.spot) {
    if (L.spot.castShadow !== want) { L.spot.castShadow = want; L.spot.shadow.mapSize.set(512, 512); L.spot.shadow.bias = -0.0008; L.spot.shadow.normalBias = 0.04; L.spot.shadow.camera.near = 0.3; }
  }
}

// ------------------------------------------------------------ map changed (world.js, after the map, scenery, props are in)
export function lightingMap(def, id, night, sunMesh) {
  if (!L.sun) return;
  L.id = id;
  const md = MOOD[id] || (def && def.base && MOOD[def.base]) || MOOD.def; // an S&D version (<id>_sd) takes its map's mood
  L.mood = md; L.indoor = !!(md.indoor || (def && (def.sealed || def.zm)));
  // compass from the sun (or moon) cube in the sky, height from the mood
  let hx = sunMesh.position.x, hz = sunMesh.position.z;
  if (md.az) [hx, hz] = md.az;
  const hl = Math.hypot(hx, hz) || 1, el = (md.el * Math.PI) / 180;
  dir.set((hx / hl) * Math.cos(el), Math.sin(el), (hz / hl) * Math.cos(el)).normalize();
  _m.lookAt(dir, _zero, _up); _m.extractBasis(bx, by, bz);
  L.sun.shadow.intensity = Math.min(1, md.sh + 0.12);
  // a bit less flat sky light, a bit more sun, so the sunny side and the shade read apart (world.js mapLight reset both
  // just before this, so it never stacks up)
  const hemi = L.hemi;
  if (hemi) hemi.intensity *= md.hk ?? 0.82;
  L.hemiRef = 1.6 * (md.hk ?? 0.82); // what a normal sunny map's sky light is after the balance
  // your hands and gun (their own scene) take the map's sky colours, so they sit in the same light as the world
  if (L.vmHemi && hemi) { L.vmHemi.color.copy(hemi.color).lerp(_c.setHex(0xffffff), 0.35); L.vmHemi.groundColor.copy(hemi.groundColor).lerp(_c.setHex(0x7a4a6a), 0.35); }
  if (L.vmSun) L.vmSun.color.copy(L.sun.color).lerp(_c.setHex(0xffffff), 0.3);
  L.sun.intensity *= md.sk ?? 1.14;
  L.sunBase = L.sun.intensity;
  L.fill.color.setHex(md.fill[0]);
  L.fill.position.set(-dir.x, 0.35, -dir.z); L.fill.target.position.set(0, 0, 0);
  // flashlight (forest.js makes it; the first SpotLight in the scene is yours)
  L.spot = null;
  G.scene.traverse((o) => { if (!L.spot && o.isSpotLight && o.userData.mine) L.spot = o; });
  spotShadow();
  findSources(def);
  markStatic();
  L.dirty = true; L.lx = NaN;
}
export function lightingRefresh() { markStatic(); L.dirty = true; }
export function shadowDirty() { L.dirty = true; } // (the instanced props' near set changed: propfield.js)

// everything in the scene now is the map (static). anything added later is "dynamic": it makes the shadows refresh
function markStatic() {
  for (const c of G.scene.children) c.userData.lsStatic = true;
  sweep();
}

// ------------------------------------------------------------ who casts / receives (one pass every 20 frames)
// rules: solid things cast; lit materials receive (all meshes using one material must agree, or three swaps shaders)
let castOK = true, castAny = false;
// crumbs (bolts, trims, tiny prop parts) aren't worth a draw call each in the shadow pass
function big(o) {
  const g = o.geometry;
  if (!g) return false;
  if (!g.boundingSphere) g.computeBoundingSphere();
  return g.boundingSphere.radius * Math.max(o.scale.x, o.scale.y, o.scale.z) > 0.18 || o.isInstancedMesh;
}
function mark(o) {
  if (!o.isMesh) return;
  const m = Array.isArray(o.material) ? o.material[0] : o.material;
  if (!m) return;
  const see = !(m.transparent && m.opacity < 0.95) && m.blending === THREE.NormalBlending && m.side !== THREE.BackSide && m.depthWrite !== false && m.colorWrite !== false;
  o.castShadow = castOK && see && !o.userData.noShadow && !o.userData.noCast && (castAny || big(o));
  o.receiveShadow = see && !o.userData.noShadow && !m.isMeshBasicMaterial && !m.isShaderMaterial && !m.isMeshNormalMaterial;
}
function sweep() {
  const dyn = L.dyn; dyn.length = 0;
  for (const c of G.scene.children) {
    const r = c.userData.lsRemote;
    castOK = r ? r._lsCast !== false : true; castAny = !!r; // players keep every part (hands, guns)
    if (!c.userData.lsStatic && !r && (c.isMesh || c.isGroup || c.type === 'Object3D')) dyn.push(c);
    c.traverse(mark);
  }
  castOK = true; castAny = false;
}

// ------------------------------------------------------------ light sources: the neon, the lamps, the signs
// a flat list [x, y, z, r, g, b, size, floorY], merged per 3 m cell so a row of neon tubes is one light
function findSources(def) {
  const boxes = def ? (def.deco ? def.boxes.concat(def.deco) : def.boxes) : [];
  const cell = new Map();
  for (const b of boxes) {
    const hex = GLOW[b.mat];
    if (hex == null) continue;
    const x = (b.min[0] + b.max[0]) / 2, y = (b.min[1] + b.max[1]) / 2, z = (b.min[2] + b.max[2]) / 2;
    const k = Math.floor(x / 3) * 73856 + Math.floor(y / 3) * 19349 + Math.floor(z / 3);
    const sz = Math.max(b.max[0] - b.min[0], b.max[1] - b.min[1], b.max[2] - b.min[2]);
    const e = cell.get(k);
    if (e) { e.n++; e.x += x; e.y += y; e.z += z; e.s = Math.max(e.s, sz); } else cell.set(k, { n: 1, x, y, z, s: sz, hex, minY: b.min[1] });
  }
  const list = [...cell.values()];
  const src = (L.src = new Float32Array((list.length + DYN_N) * 8));
  L.flick = new Uint8Array(list.length + DYN_N); // fire and lava lights flicker (and the dynamic slots are fires too)
  let n = 0;
  for (const e of list) {
    L.flick[n] = e.hex === GLOW.flame || e.hex === GLOW.lava ? 1 : 0;
    const x = e.x / e.n, y = e.y / e.n, z = e.z / e.n;
    _c.setHex(e.hex);
    const f = floorUnder(boxes, x, e.minY, z);
    src.set([x, y, z, _c.r, _c.g, _c.b, Math.min(12, e.s), f], n * 8); n++;
  }
  L.nSrc = n;
  for (let k = 0; k < DYN_N; k++) { src[(n + k) * 8] = 1e6; src[(n + k) * 8 + 1] = 1e6; L.flick[n + k] = 1; } // spare: off until a fire takes one
  buildCards();
}
// a light that moves (a burning car, flames.js): slot 0..DYN_N-1, p = [x, y, z] (null = off), hex colour, k = how bright
const DYN_N = 4;
export function dynLight(slot, p, hex = 0xff7a1a, k = 1) {
  if (!L.src || slot < 0 || slot >= DYN_N) return;
  const i = (L.nSrc + slot) * 8;
  if (!p) { L.src[i] = 1e6; L.src[i + 1] = 1e6; return; }
  _c.setHex(hex);
  L.src.set([p[0], p[1], p[2], _c.r * k, _c.g * k, _c.b * k, 4, NaN], i);
}
// the top of the highest box under a point (within 14 m), or NaN
function floorUnder(boxes, x, y, z) {
  let best = -Infinity;
  for (const b of boxes) {
    if (x < b.min[0] || x > b.max[0] || z < b.min[2] || z > b.max[2]) continue;
    const t = b.max[1];
    if (t <= y + 0.01 && t > best && y - t < 14) best = t;
  }
  return best === -Infinity ? NaN : best;
}

// light pools: a soft glowing disc on the floor under each light, all of them in one instanced draw (every preset)
let cardMat = null;
const cardGeo = new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2);
function cardMaterial() {
  if (cardMat) return cardMat;
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d'), gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, 'rgba(255,255,255,0.85)'); gr.addColorStop(0.45, 'rgba(255,255,255,0.3)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  cardMat = new THREE.MeshBasicMaterial({ map: t, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
  // additive + fog would brighten towards the fog colour: fade the pool out with the fog instead
  cardMat.onBeforeCompile = (sh) => {
    sh.fragmentShader = sh.fragmentShader.replace('#include <fog_fragment>', `#ifdef USE_FOG
  #ifdef FOG_EXP2
    float lsF = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
  #else
    float lsF = smoothstep( fogNear, fogFar, vFogDepth );
  #endif
  gl_FragColor.rgb *= 1.0 - lsF;
#endif`);
  };
  cardMat.customProgramCacheKey = () => 'lspool';
  return cardMat;
}
function buildCards() {
  if (L.cards) { G.scene.remove(L.cards); L.cards.dispose(); L.cards = null; }
  const src = L.src, idx = [];
  for (let i = 0; i < L.nSrc; i++) if (Number.isFinite(src[i * 8 + 7]) && src[i * 8 + 1] - src[i * 8 + 7] < 12) idx.push(i);
  if (!idx.length) return;
  const n = Math.min(600, idx.length), im = new THREE.InstancedMesh(cardGeo, cardMaterial(), n), o = new THREE.Object3D();
  for (let j = 0; j < n; j++) {
    const i = idx[j] * 8, h = src[i + 1] - src[i + 7], s = Math.min(10, 2.6 + src[i + 6] * 0.6 + h * 0.5);
    o.position.set(src[i], src[i + 7] + 0.025, src[i + 2]); o.scale.set(s, 1, s); o.updateMatrix();
    im.setMatrixAt(j, o.matrix);
    const k = Math.max(0.25, 0.75 - h * 0.05); // higher lights throw a dimmer pool
    im.setColorAt(j, _c.setRGB(src[i + 3] * k, src[i + 4] * k, src[i + 5] * k));
  }
  im.userData.noShadow = true; im.frustumCulled = false; im.renderOrder = 1;
  L.cards = im;
  G.scene.add(im);
}

// ------------------------------------------------------------ every frame (world.js renderFrame, right before drawing)
const best = new Int32Array(POOL_N), bestD = new Float32Array(POOL_N), poolSrc = new Int32Array(POOL_N).fill(-1);
function pickPool() {
  const want = L.q ? L.q.pool : 0;
  best.fill(-1); bestD.fill(1e9);
  const cam = G.camera.position, src = L.src;
  for (let i = 0; i < L.nSrc + (L.src ? DYN_N : 0) && want; i++) {
    const dx = src[i * 8] - cam.x, dy = src[i * 8 + 1] - cam.y, dz = src[i * 8 + 2] - cam.z, d = dx * dx + dy * dy + dz * dz;
    if (d > 900) continue; // 30 m
    for (let k = 0; k < want; k++) if (d < bestD[k]) { for (let j = want - 1; j > k; j--) { bestD[j] = bestD[j - 1]; best[j] = best[j - 1]; } bestD[k] = d; best[k] = i; break; }
  }
  // keep a light on the source it already has (no hopping), give the rest the new ones
  for (let k = 0; k < POOL_N; k++) {
    const cur = poolSrc[k];
    let keep = false;
    for (let j = 0; j < POOL_N; j++) if (best[j] === cur && cur >= 0) { best[j] = -2; keep = true; }
    if (!keep) poolSrc[k] = -1;
  }
  for (let j = 0; j < POOL_N; j++) {
    if (best[j] < 0) continue;
    for (let k = 0; k < want; k++) if (poolSrc[k] === -1 && L.poolK[k] < 0.02) { poolSrc[k] = best[j]; const i = best[j] * 8, p = L.pool[k]; p.position.set(src[i], src[i + 1] - 0.5, src[i + 2]); p.color.setRGB(src[i + 3], src[i + 4], src[i + 5]); break; }
  }
  for (let k = 0; k < POOL_N; k++) L.poolT[k] = poolSrc[k] >= 0 ? 1 : 0;
}

// is the camera in the sun? walk towards the sun through the boxes (only every few frames, no allocations)
let boxesRef = null;
export function setSunBoxes(b) { boxesRef = b; }
function inSun() {
  const b = boxesRef;
  if (!b || !b.length) return true;
  const p = G.camera.position;
  for (let t = 0.6; t < 50; t += 0.7) {
    const x = p.x + dir.x * t, y = p.y + dir.y * t, z = p.z + dir.z * t;
    if (aoHit(x, y, z, true)) return false;
  }
  return true;
}

// any point: is it in the sun (bounce.js bakes with this). dir is the map's sun, set by lightingMap
export function sunAt(x, y, z, maxT = 40) {
  for (let t = 0.3; t < maxT; t += 0.8) if (aoHit(x + dir.x * t, y + dir.y * t, z + dir.z * t, true)) return false;
  return true;
}
export const sunDir = () => dir;
export const sunBoxes = () => boxesRef;
export const lightSources = () => ({ src: L.src, n: L.nSrc }); // neon.js: [x, y, z, r, g, b, size, floorY] per light

const tmpW = new THREE.Vector3();
const rq = { near2: 0, half2: 0, dyn: false, cx: 0, cz: 0, px: 0, pz: 0 };
function remoteShadow(r) {
  const root = r.ch && r.ch.root;
  if (!root) return;
  root.userData.lsRemote = r;
  const dx = root.position.x - rq.px, dz = root.position.z - rq.pz, cast = dx * dx + dz * dz < rq.near2;
  if (r._lsCast !== cast) { r._lsCast = cast; castOK = cast; castAny = true; root.traverse(mark); castOK = true; castAny = false; }
  const cx = root.position.x - rq.cx, cz = root.position.z - rq.cz;
  if (cast && root.visible && cx * cx + cz * cz < rq.half2) { rq.dyn = true; if (r.shadow) r.shadow.visible = false; }
}
export function updateLighting(dt) {
  if (!L.sun) return;
  const f = ++L.frame;
  lightStats.frames++;
  // the bounce light follows the sun's brightness (zombies power, night vision don't need to know about it)
  L.fill.intensity = L.mood.fill[1] * (L.sun.intensity / (L.sunBase || 1));
  // pooled lights fade in and out (never pop)
  if (f % 12 === 0) pickPool();
  const k = Math.min(1, dt * 4);
  for (let i = 0; i < POOL_N; i++) {
    L.poolK[i] += (L.poolT[i] - L.poolK[i]) * k;
    const si = poolSrc[i], fl = si >= 0 && L.flick && L.flick[si] ? 0.78 + 0.14 * Math.sin(f * 0.37 + i * 2.1) + 0.08 * Math.sin(f * 1.13 + i) : 1; // fire flickers
    if (si >= L.nSrc && L.src) { const j = si * 8; L.pool[i].position.set(L.src[j], L.src[j + 1], L.src[j + 2]); L.pool[i].color.setRGB(L.src[j + 3], L.src[j + 4], L.src[j + 5]); } // a moving fire: follow it
    L.pool[i].intensity = L.poolK[i] * 14 * fl;
  }
  // the gun in your hands darkens in the shade
  if (f % 5 === 0) L.vmT = inSun() ? 1 : 0.5;
  L.vmK += (L.vmT - L.vmK) * Math.min(1, dt * 6);
  // ...and follows how bright the map is right now (night, the mall's power going off, a flicker), never too dark to read
  const lit = L.hemi && L.hemiRef ? Math.min(1.1, Math.max(0.5, L.hemi.intensity / L.hemiRef)) : 1;
  if (L.vmSun) L.vmSun.intensity = L.vmBase * L.vmK * Math.min(1.1, Math.max(0.35, L.sun.intensity / (L.sunBase || 1)));
  if (L.vmHemi) L.vmHemi.intensity = L.vmHemiBase * lit;
  if (f % 20 === 0) sweep();
  const q = L.q;
  if (!q) return;
  // the shadow centre: a bit ahead of where you look, snapped to a coarse grid in light space (whole texels: no swimming)
  const cam = G.camera;
  cam.getWorldDirection(_fw); _fw.y = 0;
  if (_fw.lengthSq() > 1e-6) _fw.normalize();
  _v.copy(cam.position).addScaledVector(_fw, q.half * 0.4);
  const texel = (2 * q.half) / q.size, step = texel * Math.max(1, Math.round(q.half / 7 / texel));
  const x = Math.round(_v.dot(bx) / step) * step, y = Math.round(_v.dot(by) / step) * step, z = Math.round(_v.dot(bz) / 8) * 8;
  let need = L.dirty;
  if (x !== L.lx || y !== L.ly || z !== L.lz) {
    L.lx = x; L.ly = y; L.lz = z; need = true;
    tmpW.set(0, 0, 0).addScaledVector(bx, x).addScaledVector(by, y).addScaledVector(bz, z);
    L.sun.target.position.copy(tmpW);
    L.sun.position.copy(tmpW).addScaledVector(dir, 200);
    L.sun.target.updateMatrixWorld(); L.sun.updateMatrixWorld();
  }
  const ctr = L.sun.target.position;
  // remotes: real shadows close up (blob far away), and they make the map refresh
  rq.near2 = q.near * q.near; rq.half2 = q.half * q.half * 0.8; rq.dyn = false; rq.cx = ctr.x; rq.cz = ctr.z; rq.px = cam.position.x; rq.pz = cam.position.z;
  G.remotes.forEach(remoteShadow);
  let dyn = rq.dyn;
  for (let i = 0; i < L.dyn.length && !dyn; i++) {
    const o = L.dyn[i];
    if (!o.visible || !o.parent) continue;
    const dx = o.position.x - ctr.x, dz = o.position.z - ctr.z;
    if (dx * dx + dz * dz < rq.half2) dyn = true;
  }
  if (need || (dyn && f % q.every === 0)) { L.sun.shadow.needsUpdate = true; L.dirty = false; lightStats.passes++; }
}

// ------------------------------------------------------------ baked AO (world.js calls these while building the map)
// a hash grid of every map box (walls, floors, deco). a vertex gets darker for every box just off its face: corners,
// where walls meet floors, under shelves and overhangs. drawn into the vertex colours, so even Potato gets the depth
const AO_CELL = 4;
let aoBoxes = null, aoGrid = null, aoNc = null;
export function aoBegin(boxes, noCast) {
  const n = boxes.length;
  aoBoxes = new Float32Array(n * 6); aoNc = new Uint8Array(n); aoGrid = new Map();
  for (let i = 0; i < n; i++) {
    const b = boxes[i];
    if (b.rot) { aoBoxes[i * 6] = 1e9; continue; } // turned boxes (render-only streets) don't occlude
    aoBoxes.set([b.min[0], b.min[1], b.min[2], b.max[0], b.max[1], b.max[2]], i * 6);
    aoNc[i] = noCast && noCast(b) ? 1 : 0;
    const x0 = Math.floor(b.min[0] / AO_CELL), x1 = Math.floor(b.max[0] / AO_CELL), z0 = Math.floor(b.min[2] / AO_CELL), z1 = Math.floor(b.max[2] / AO_CELL);
    if ((x1 - x0 + 1) * (z1 - z0 + 1) > 2500) continue; // huge (a sea, a lawn to the horizon): only the floor test below
    for (let x = x0; x <= x1; x++) for (let z = z0; z <= z1; z++) {
      const k = x * 100003 + z, c = aoGrid.get(k);
      if (c) c.push(i); else aoGrid.set(k, [i]);
    }
  }
}
function aoHit(x, y, z, skipNc) {
  if (!aoGrid) return false;
  const c = aoGrid.get(Math.floor(x / AO_CELL) * 100003 + Math.floor(z / AO_CELL));
  if (!c) return false;
  const B = aoBoxes;
  for (let j = 0; j < c.length; j++) {
    const i = c[j], o = i * 6;
    if (x > B[o] && x < B[o + 3] && y > B[o + 1] && y < B[o + 4] && z > B[o + 2] && z < B[o + 5] && !(skipNc && aoNc[i])) return true;
  }
  return false;
}
// geo: a box already in world space. writes a 'color' attribute
export function aoBake(geo, small) {
  const pos = geo.attributes.position, nrm = geo.attributes.normal, n = pos.count, col = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    let a = 1;
    if (!small) {
      const px = pos.getX(i), py = pos.getY(i), pz = pos.getZ(i), nx = nrm.getX(i), ny = nrm.getY(i), nz = nrm.getZ(i);
      // two directions along the face
      let tx, ty, tz;
      if (Math.abs(ny) > 0.5) { tx = 1; ty = 0; tz = 0; } else { tx = 0; ty = 1; tz = 0; }
      const ux = ny * tz - nz * ty, uy = nz * tx - nx * tz, uz = nx * ty - ny * tx;
      const qx = px + nx * 0.22, qy = py + ny * 0.22, qz = pz + nz * 0.22, R = 0.55;
      let occ = 0;
      if (aoHit(qx + tx * R, qy + ty * R, qz + tz * R)) occ++;
      if (aoHit(qx - tx * R, qy - ty * R, qz - tz * R)) occ++;
      if (aoHit(qx + ux * R, qy + uy * R, qz + uz * R)) occ++;
      if (aoHit(qx - ux * R, qy - uy * R, qz - uz * R)) occ++;
      if (aoHit(px + nx * 0.9, py + ny * 0.9, pz + nz * 0.9)) occ += 1.5;
      if (ny > 0.5) { if (aoHit(px, py + 2.2, pz, true)) occ += 1; if (aoHit(px, py + 4.5, pz, true)) occ += 0.8; } // under an overhang
      a = Math.max(0.42, 1 - occ * 0.17);
    }
    col[i * 3] = col[i * 3 + 1] = col[i * 3 + 2] = a;
  }
  geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
  return geo;
}
export function aoEnd() { /* the grid stays: inSun() walks it */ }

// lit map materials multiply in the AO colours (unlit glowing ones ignore them)
export function aoMaterials(out) {
  for (const v of Object.values(out)) { const m = v.mat; if (!m.isMeshBasicMaterial) m.vertexColors = true; }
}

// renderer.info for tests: draw calls and triangles for one frame, both scenes and the shadow pass
export function lightInfo() { return { level: shadowLevel(), passes: lightStats.passes, frames: lightStats.frames, pool: L.pool.filter((p) => p.intensity > 0.05).length, srcs: L.nSrc, cards: L.cards ? L.cards.count : 0 }; }
