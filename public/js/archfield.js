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
export const ARCH_IDS = new Set(['home', 'store', 'tenement', 'adobe', 'kaboom', 'kaboom_sd', 'wreck', 'lighthouse', 'lighthouse_sd', 'skullrock', 'skullspine', 'rocks_desert', 'rocks_desert_sd', 'rocks_bazaar', 'rocks_bazaar_sd', 'rocks_forest', 'rocks_islands', 'rocks_islands_sd', 'fort', 'fort_sd', 'walks_islands', 'walks_islands_sd', 'spire', 'spire_sd']);
// map material keys -> the paint a Blender building takes on (its '@siding' / '@roof' / '@trim' parts)
const PAINT = {
  hutadobe: '#ffdcae', hutsideorange: '#ffb866', hutsidemint: '#a8ffd8', hutsidelemon: '#fff27a', // (sunlit mud plaster: the Desert's adobe huts)
  sidepink: '#ff7ec0', sidelemon: '#f2e25a', sidelilac: '#b08cff', sidemint: '#74e8b8', sideorange: '#ff9a3c', blue: '#7aa8e0', white: '#ece8dc', yellow: '#ecd27a', mint: '#98d8b4',
  roofteal: '#1aa8a4', roofpink: '#ee4a98', roof: '#a8483c', roofg: '#5a5c62', roofblue: '#3a6ab8', trim: '#f0eadb',
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

function material(name, x) { // one shared material per Blender material name
  if (matCache.has(name)) return matCache.get(name);
  const decal = x.tex === 'decals';
  const m = new THREE.MeshLambertMaterial({ map: tex(x.tex, decal), vertexColors: true, color: x.paint ? 0xffffff : new THREE.Color(x.col || '#ffffff') });
  if (x.alpha) { m.alphaTest = 0.5; m.side = THREE.DoubleSide; }
  if (decal) { m.polygonOffset = true; m.polygonOffsetFactor = -2; m.polygonOffsetUnits = -2; }
  if (x.glow) { m.emissiveMap = m.map; m.emissive = new THREE.Color(x.glowcol || 0xffffff); } // (glowcol: a lava orange, say; white = the texture's own light)
  if (x.glowmap) { m.emissiveMap = tex(x.glowmap); m.emissive = new THREE.Color(0xffd890); } // lit windows (facades)
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
