// Draws a map's Blender architecture (shared/map.js B.arch(): tools/blender/arch -> public/models/arch/<id>.glb) over its
// boxes. Visual only: the boxes stay for physics, bots and hits; world.js just stops drawing the ones tagged { av: id }
// once that model is in (a missing file = the old box look). Every placement of every model is merged into one mesh per
// material for the whole map (a street of ten houses is ~20 draw calls), with each house's paint baked into its vertex
// colours. Textures are the shared PS1 kit (public/models/arch/kit): tiny, nearest-filtered, no smoothing up close.
// ?arch=0 (or localStorage jf_arch = '0') turns it all off, for comparing.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

// the models that exist (so nothing 404s asking for one that doesn't)
export const ARCH_IDS = new Set(['home', 'store', 'tenement', 'adobe', 'kaboom', 'kaboom_sd', 'wreck', 'lighthouse', 'lighthouse_sd', 'skullrock', 'skullspine', 'rocks_desert', 'rocks_desert_sd', 'rocks_bazaar', 'rocks_bazaar_sd', 'rocks_forest', 'rocks_islands', 'rocks_islands_sd', 'fort', 'fort_sd', 'walks_islands', 'walks_islands_sd', 'spire', 'spire_sd', 'backrooms', 'stairhi', 'stairlo', 'wh_hall', 'wh_hall_sd', 'wh_staff', 'tube', 'girder', 'tenement_e', 'tenement_ne', 'office_n', 'office_w', 'office_se', 'office_sw', 'concrete_nw', 'jbh_capsule3', 'jbh_capsule4', 'jbh_noodle', 'jbh_bodega', 'jbh_walkup', 'jbh_model', 'jbh_container', 'jbh_squat', 'jbh_dorm', 'jbh_arcade', 'jbh_pastel', 'jbh_biolab', 'jbh_pawn', 'penthouse', 'penthouse_sd', 'pooldeck', 'pooldeck_sd']); // (jbh_: Jankburg's city houses, tools/blender/jankburg/make_jb_houses.py)
// map material keys -> the paint a Blender building takes on (its '@siding' / '@roof' / '@trim' parts)
const PAINT = {
  hutadobe: '#ffdcae', hutsideorange: '#ffb866', hutsidemint: '#a8ffd8', hutsidelemon: '#fff27a', // (sunlit mud plaster: the Desert's adobe huts)
  sidepink: '#ff7ec0', sidelemon: '#f2e25a', sidelilac: '#b08cff', sidemint: '#74e8b8', sideorange: '#ff9a3c', blue: '#7aa8e0', white: '#ece8dc', yellow: '#ecd27a', mint: '#98d8b4',
  roofteal: '#1aa8a4', roofpink: '#ee4a98', roof: '#a8483c', roofg: '#5a5c62', roofblue: '#3a6ab8', trim: '#f0eadb',
  tenement: '#b86a5a', brick: '#c0604a', magenta: '#e83ab8', plaster: '#e8dcc8', pink: '#ff8ac8', toyteal: '#30c8c0', toyyellow: '#ffd23a', chrome: '#c8d0dc', // (Jankburg's city houses)
  containerr: '#c04030', containerg: '#3a8a4a', containerb: '#3060b0',
  // Jankburg's city houses: candy paint, pushed bright (the kit's siding / stucco / fac_paint are light greys, x this)
  jb_sidepink: '#ff4fb8', jb_sidelemon: '#ffe600', jb_sidelilac: '#a060ff', jb_sidemint: '#2ef0a8', jb_sideorange: '#ff7a1a', jb_white: '#f6fbff',
  jb_tenement: '#ff6a4a', jb_brick: '#ff4a3a', jb_magenta: '#ff2ad0', jb_plaster: '#ffc890', jb_roofteal: '#20e8f0', jb_pink: '#ff6ac8',
  jb_toyteal: '#18e8d8', jb_toyyellow: '#ffd800', jb_chrome: '#d8e8ff', jb_office: '#7fd8ff', jb_roofpink: '#ff3aa8', jb_roofblue: '#3a8aff',
  jb_containerr: '#ff3a2a', jb_containerg: '#2ad860', jb_containerb: '#2a7aff', jb_graffiti: '#ffffff', jb_glass: '#ffffff',
};
const off = (() => { try { return /[?&]arch=0\b/.test(location.search) || localStorage.getItem('jf_arch') === '0'; } catch { return false; } })();
const models = {}; // id -> [{ geo, mat, node }]
const pending = new Map(); // id -> [callbacks]
const texCache = new Map(), matCache = new Map();
let group = null, loader = null, hazeFn = null;

export const hasArch = (id) => !off && !!models[id];
export function setArchHaze(fn) { hazeFn = fn; } // world.js hands over its fog patch (no import loop)

// one THREE texture per kit image, shared by every model that uses the kit (props too: propfield.js can import this)
export function kitTexture(name, decal = name === 'decals') { return tex(name, decal); }
function tex(name, decal) {
  if (texCache.has(name)) return texCache.get(name);
  const t = new THREE.TextureLoader().load(`/models/arch/kit/${name}.png`);
  t.colorSpace = THREE.SRGBColorSpace;
  t.magFilter = THREE.NearestFilter;
  // crunchy up close, mipmapped far away (like the world's boxes) so walls don't shimmer; the decal atlas has no mips
  // (they'd bleed one cell into the next)
  if (decal) { t.minFilter = THREE.NearestFilter; t.generateMipmaps = false; } else { t.minFilter = THREE.NearestMipmapLinearFilter; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = 4; }
  texCache.set(name, t);
  return t;
}

// the reflection for glossy parts: a night sky over a neon city, painted once on a canvas (equirect, three PMREMs it)
let skyEnvTex = null;
function skyEnv() {
  if (skyEnvTex) return skyEnvTex;
  const c = document.createElement('canvas'); c.width = 256; c.height = 128;
  const g = c.getContext('2d'), gr = g.createLinearGradient(0, 0, 0, 128);
  for (const [t, col] of [[0, '#0a0828'], [0.35, '#3a2470'], [0.48, '#c060d8'], [0.52, '#ff8ad8'], [0.56, '#40204a'], [1, '#08040c']]) gr.addColorStop(t, col);
  g.fillStyle = gr; g.fillRect(0, 0, 256, 128);
  let s = 7; const rnd = () => ((s = (s * 16807) % 2147483647) / 2147483647); // (seeded: the same city every time)
  for (let x = 0; x < 256; x += 3 + ((rnd() * 6) | 0)) { const h = 4 + rnd() * 14; g.fillStyle = '#1a0c2a'; g.fillRect(x, 66 - h, 3 + rnd() * 6, h); }
  for (let i = 0; i < 160; i++) { g.fillStyle = ['#ffe14d', '#4fd8ff', '#ff4fd8', '#ffffff'][i % 4]; g.fillRect((rnd() * 256) | 0, (52 + rnd() * 26) | 0, 1, 1); }
  skyEnvTex = new THREE.CanvasTexture(c); skyEnvTex.mapping = THREE.EquirectangularReflectionMapping; skyEnvTex.colorSpace = THREE.SRGBColorSpace;
  return skyEnvTex;
}

function material(name, x) { // one shared material per Blender material name
  if (matCache.has(name)) return matCache.get(name);
  const decal = x.tex === 'decals';
  const opt = { map: tex(x.tex, decal), vertexColors: true, color: x.paint ? 0xffffff : new THREE.Color(x.col || '#ffffff') };
  // x.gloss (0..1, x.metal): glass, chrome and candy paint shine, reflecting a small night sky (the penthouse's)
  const m = x.gloss ? new THREE.MeshStandardMaterial({ ...opt, roughness: 1 - x.gloss * 0.8, metalness: x.metal ? 0.85 : 0, envMap: skyEnv(), envMapIntensity: x.metal ? 1.1 : 0.7 }) : new THREE.MeshLambertMaterial(opt);
  if (x.alpha) { m.alphaTest = 0.5; m.side = THREE.DoubleSide; }
  if (decal || x.decal) { m.polygonOffset = true; m.polygonOffsetFactor = -2; m.polygonOffsetUnits = -2; }
  if (x.glow) { m.emissiveMap = m.map; m.emissive = new THREE.Color(x.glowcol || 0xffffff); } // (glowcol: a lava orange, say; white = the texture's own light)
  if (x.glowmap) { m.emissiveMap = tex(x.glowmap); m.emissive = new THREE.Color(x.glowcol || 0xffd890); } // lit windows (facades; glowcol: warmer ones)
  if (x.fade > 0 && x.fade < 1) { m.transparent = true; m.opacity = x.fade; m.depthWrite = false; } // see-through (a volcano's smoke): never hides anything behind it
  m.name = 'arch_' + name;
  m.userData.arch = true;
  if (hazeFn) hazeFn(m);
  matCache.set(name, m);
  return m;
}

function load(id, done) {
  if (pending.has(id)) { pending.get(id).push(done); return; }
  pending.set(id, [done]);
  (loader || (loader = new GLTFLoader())).load(`/models/arch/${id}.glb`, (gltf) => {
    const parts = [];
    gltf.scene.updateMatrixWorld(true);
    gltf.scene.traverse((o) => {
      if (!o.isMesh) return;
      const x = o.material.userData || {};
      const g = o.geometry.clone().applyMatrix4(o.matrixWorld);
      // one vertex layout for everything (merging needs it): float rgb colours
      const c = g.getAttribute('color');
      const rgb = new Float32Array(g.getAttribute('position').count * 3).fill(1);
      if (c) for (let i = 0; i < c.count; i++) { rgb[i * 3] = c.getX(i); rgb[i * 3 + 1] = c.getY(i); rgb[i * 3 + 2] = c.getZ(i); }
      g.setAttribute('color', new THREE.BufferAttribute(rgb, 3));
      for (const k of Object.keys(g.attributes)) if (!['position', 'normal', 'uv', 'color'].includes(k)) g.deleteAttribute(k);
      const node = (o.userData && o.userData.node) || (o.parent && o.parent.userData && o.parent.userData.node) || '';
      parts.push({ geo: g, name: o.material.name, x, node });
    });
    models[id] = parts;
    for (const f of pending.get(id)) f(id);
    pending.delete(id);
  }, undefined, (e) => { console.warn('arch model failed', id, e); pending.delete(id); });
}

// ask for the map's models; onLoad() once each lands (world.js redraws the map: boxes out, model in)
export function wantArch(list, onLoad) {
  if (off || !list) return;
  for (const id of new Set(list.map((a) => a.id))) if (ARCH_IDS.has(id) && !models[id]) load(id, onLoad);
}

const _m = new THREE.Matrix4(), _c = new THREE.Color();
export function buildArch(scene, list) {
  if (group) { scene.remove(group); for (const m of group.children) m.geometry.dispose(); group = null; }
  if (off || !list || !list.length) return;
  const byMat = new Map(), nth = new Map();
  for (const a of list) {
    const parts = models[a.id];
    if (!parts) continue;
    _m.makeRotationY(-(a.r || 0) * Math.PI / 2).setPosition(a.p[0], a.p[1], a.p[2]); // quarter turns like the builder's local()
    const vk = nth.get(a.id) || 0; nth.set(a.id, vk + 1); // which set of extras this copy wears (nodes v0 / v1 / v2: one per placement)
    for (const p of parts) {
      if (p.node === 'fence' && a.fence === false) continue;
      if (p.node.length === 2 && p.node[0] === 'v' && p.node !== 'v' + (vk % 3)) continue;
      const g = p.geo.clone().applyMatrix4(_m);
      if (p.x.paint) { // this house's paint, into its vertex colours
        const key = a.paint && a.paint[p.x.paint];
        _c.set(PAINT[key] || PAINT[p.x.paint] || '#ffffff');
        if (key && key.startsWith('jb_')) _c.multiplyScalar(key === 'jb_white' ? 1.22 : 1.12); // (Jankburg's candy: past 1, so the light-grey kit comes out bright and white reads white)
        const col = g.getAttribute('color');
        for (let i = 0; i < col.count; i++) col.setXYZ(i, col.getX(i) * _c.r, col.getY(i) * _c.g, col.getZ(i) * _c.b);
      }
      if (!byMat.has(p.name)) byMat.set(p.name, { x: p.x, list: [] });
      byMat.get(p.name).list.push(g);
    }
  }
  if (!byMat.size) return;
  group = new THREE.Group(); group.name = 'arch';
  for (const [name, { x, list: gs }] of byMat) {
    const merged = mergeGeometries(gs, false);
    for (const g of gs) g.dispose();
    if (!merged) continue;
    merged.computeBoundingSphere();
    const m = new THREE.Mesh(merged, material(name, x));
    m.matrixAutoUpdate = false;
    if (x.nocast) m.userData.noCast = true; // small detail: no sun shadow (lighting.js)
    group.add(m);
  }
  scene.add(group);
}
