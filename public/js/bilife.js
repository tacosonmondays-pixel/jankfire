// BATTLE ISLAND's life (the look pass, after the sky, the ground and the shore): grass tufts and flowers round your
// feet that sway in the wind and shrink away with distance, the palms, ferns and bushes swaying too, gulls wheeling
// over the coast and fishing boats bobbing offshore. All looks: nothing here is solid, nothing is synced, nobody can
// hide in it (the tufts are knee high, the boats are out past where you can wade). One draw call each:
//   tufts + flowers: instanced, laid on a fixed world grid round the camera (the same tuft is in the same spot when you
//   come back), only where the ground is grass or jungle floor, flat enough, out of the water. re-laid when you've moved
//   a few metres. they fade by scaling down into the ground near the edge of their circle, so there's no line.
//   gulls: a V of two wings flapping in the vertex shader, flocks circling over the beaches.
//   boats: little low-poly fishing boats (hull, cabin, mast) bobbing and drifting in slow circles.
// Potato: a smaller circle of tufts, no flowers; gulls and boats stay. Only on Battle Island. No tufts on the roads
// (they aren't grass paint), the mechs' drop pads or the towns' flat ground (map.royale.drops / pois).
import * as THREE from 'three';
import { G } from './ctx.js';
import { BOXES } from '/shared/map.js';

export const BI_LIFE = { r: 34, rLite: 16, cell: 0.62, keep: 0.8, flowers: 0.05, relay: 3, gulls: 27, boats: 7, wind: [0.8, 0.45] };

const U = { uTime: { value: 0 }, uR: { value: 34 }, uWind: { value: new THREE.Vector2(0.8, 0.45) } };
// a material that sways (and for the field things, shrinks away at the edge of the circle)
function swayMat(base, { fade = false, amp = 0.12, h = 0.5 } = {}) {
  base.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, U);
    if (fade) sh.fragmentShader = sh.fragmentShader.replace('#include <normal_fragment_begin>', '#include <normal_fragment_begin>\n\tnormal = normalize( vNormal ); // (both faces of a blade lit as the side facing up)');
    sh.vertexShader = 'uniform float uTime; uniform float uR; uniform vec2 uWind;\n' + sh.vertexShader.replace('#include <begin_vertex>', `#include <begin_vertex>
	{ vec3 ip = vec3( 0.0 );
	#ifdef USE_INSTANCING
	ip = ( modelMatrix * instanceMatrix * vec4( 0.0, 0.0, 0.0, 1.0 ) ).xyz;
	#endif
	float k = clamp( transformed.y / ${h.toFixed(2)}, 0.0, 1.0 ); k *= k;
	float gust = 0.6 + 0.4 * sin( uTime * 0.7 + ip.x * 0.05 + ip.z * 0.04 );
	float sw = sin( uTime * 2.3 + ip.x * 0.37 + ip.z * 0.29 ) * 0.6 + sin( uTime * 3.7 + ip.x * 0.11 ) * 0.4;
	transformed.xz += ( uWind * ( 0.5 + 0.5 * gust ) + uWind.yx * vec2( -1.0, 1.0 ) * sw * 0.5 ) * k * ${amp.toFixed(3)} * gust;
	${fade ? 'float d = length( ip.xz - cameraPosition.xz ); transformed *= 1.0 - smoothstep( uR * 0.62, uR, d );' : ''} }`);
  };
  base.customProgramCacheKey = () => 'bisway' + (fade ? 'f' : '') + amp + h;
  return base;
}

// ---- geometry
function tuftGeo() { // seven blades, a triangle each, leaning out: dark at the root, light at the tip
  const pos = [], col = [], nrm = [];
  for (let b = 0; b < 7; b++) {
    const a = (b / 7) * Math.PI * 2 + b * 0.7, lean = 0.1 + 0.14 * ((b * 37) % 7) / 7, h = 0.36 + 0.34 * ((b * 53) % 5) / 5, w = 0.05;
    const cx = Math.cos(a), cz = Math.sin(a), px = -cz * w, pz = cx * w;
    pos.push(-px, 0, -pz, px, 0, pz, cx * lean, h, cz * lean);
    col.push(0.12, 0.34, 0.05, 0.12, 0.34, 0.05, 0.42, 0.78, 0.18);
    for (let i = 0; i < 3; i++) nrm.push(0, 1, 0); // (lit like the ground under them)
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3)); g.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
  return g;
}
function flowerGeo() { // a stem and a head of four petals (crossed quads), the head tinted per flower (instanceColor)
  const pos = [], col = [], nrm = [], H = 0.42, P = 0.12;
  const tri = (a, b, c, ca, cb, cc) => { pos.push(...a, ...b, ...c); col.push(...ca, ...cb, ...cc); for (let i = 0; i < 3; i++) nrm.push(0, 1, 0); };
  const stem = [0.25, 0.45, 0.15], head = [1, 1, 1], eye = [1.0, 0.9, 0.35];
  tri([-0.01, 0, 0], [0.01, 0, 0], [0, H, 0], stem, stem, stem);
  for (let k = 0; k < 4; k++) { const a = (k / 4) * Math.PI * 2, c = Math.cos(a) * P, s = Math.sin(a) * P; tri([0, H, 0], [c - s * 0.6, H + 0.015, s + c * 0.6], [c + s * 0.6, H + 0.015, s - c * 0.6], eye, head, head); }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3)); g.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
  return g;
}
function gullGeo() { // a body and two wings; the wings' tips are marked (flap = 1) so the shader flaps them
  const g = new THREE.BufferGeometry();
  const P = [0, 0, -0.25, 0, 0.04, 0.3, 0, -0.04, 0.3, /* left wing */ 0, 0, -0.1, -0.9, 0, 0.05, 0, 0, 0.2, /* right */ 0, 0, -0.1, 0, 0, 0.2, 0.9, 0, 0.05];
  const FL = [0, 0, 0, 0, 1, 0, 0, 0, 1];
  g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3)); g.setAttribute('flap', new THREE.Float32BufferAttribute(FL, 1));
  g.computeVertexNormals();
  return g;
}
function boatGeo() { // a little fishing boat: a tapered hull, a red stripe, a white cabin with a blue roof, a mast
  const parts = [];
  const box = (sx, sy, sz, x, y, z, c, taper = 0) => {
    const b = new THREE.BoxGeometry(sx, sy, sz).toNonIndexed(); const p = b.attributes.position;
    for (let i = 0; i < p.count; i++) { if (taper && p.getZ(i) > 0) p.setX(i, p.getX(i) * (1 - taper * (p.getZ(i) / (sz / 2)))); if (taper && p.getY(i) < 0) p.setX(i, p.getX(i) * 0.7); }
    b.translate(x, y, z); const n = b.attributes.position.count, cc = new Float32Array(n * 3); for (let i = 0; i < n; i++) cc.set(c, i * 3); b.setAttribute('color', new THREE.BufferAttribute(cc, 3)); b.deleteAttribute('uv'); b.computeVertexNormals(); parts.push(b);
  };
  box(2.2, 0.8, 6.4, 0, 0.1, 0, [0.95, 0.95, 0.92], 0.85); // hull
  box(2.24, 0.18, 6.44, 0, 0.42, 0, [0.85, 0.15, 0.15], 0.85); // stripe
  box(1.4, 1.1, 1.6, 0, 1.0, -0.9, [0.97, 0.97, 0.95]); // cabin
  box(1.6, 0.14, 1.8, 0, 1.6, -0.9, [0.15, 0.4, 0.85]); // roof
  box(0.1, 3.2, 0.1, 0, 2.0, 1.2, [0.35, 0.3, 0.25]); // mast
  const out = new THREE.BufferGeometry(); // (merged by hand: three's mergeGeometries isn't needed for five boxes)
  const n = parts.reduce((t, b) => t + b.attributes.position.count, 0), P = new Float32Array(n * 3), N = new Float32Array(n * 3), C = new Float32Array(n * 3);
  let o = 0; for (const b of parts) { P.set(b.attributes.position.array, o * 3); N.set(b.attributes.normal.array, o * 3); C.set(b.attributes.color.array, o * 3); o += b.attributes.position.count; b.dispose(); }
  out.setAttribute('position', new THREE.BufferAttribute(P, 3)); out.setAttribute('normal', new THREE.BufferAttribute(N, 3)); out.setAttribute('color', new THREE.BufferAttribute(C, 3));
  return out;
}

// ---- state
const S = { on: false, group: null, tufts: null, flowers: null, gulls: null, boats: null, lx: NaN, lz: NaN, lite: false, flocks: [], boatList: [], swayed: new WeakSet() };
const hash = (i, j, s) => { let h = (i * 374761393 + j * 668265263 + s * 2147483647) | 0; h = (h ^ (h >>> 13)) * 1274126177 | 0; return ((h ^ (h >>> 16)) >>> 0) / 4294967295; };
const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), v = new THREE.Vector3(), sc = new THREE.Vector3(), col = new THREE.Color();
const FLOWER_COLS = [0xff6fb5, 0xffe14d, 0xffffff, 0xff5a4f, 0xc58cff];

function build() {
  const grp = new THREE.Group(); grp.name = 'biLife';
  const tm = swayMat(new THREE.MeshLambertMaterial({ vertexColors: true, side: THREE.DoubleSide }), { fade: true, amp: 0.1, h: 0.55 });
  S.tufts = new THREE.InstancedMesh(tuftGeo(), tm, 10000); S.tufts.count = 0; S.tufts.frustumCulled = false; S.tufts.userData.noCast = true;
  const fm = swayMat(new THREE.MeshLambertMaterial({ vertexColors: true, side: THREE.DoubleSide }), { fade: true, amp: 0.08, h: 0.35 });
  S.flowers = new THREE.InstancedMesh(flowerGeo(), fm, 600); S.flowers.count = 0; S.flowers.frustumCulled = false; S.flowers.userData.noCast = true;
  S.flowers.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(600 * 3), 3);
  const gm = new THREE.MeshLambertMaterial({ color: 0xf4f6f8, side: THREE.DoubleSide });
  gm.onBeforeCompile = (sh) => { Object.assign(sh.uniforms, U); sh.vertexShader = 'uniform float uTime;\nattribute float flap;\n' + sh.vertexShader.replace('#include <begin_vertex>', `#include <begin_vertex>
	{ vec3 ip = ( instanceMatrix * vec4( 0.0, 0.0, 0.0, 1.0 ) ).xyz; float f = sin( uTime * 7.0 + ip.x * 1.3 + ip.z * 0.7 ); transformed.y += flap * f * 0.45 * ( 0.4 + 0.6 * step( 0.0, sin( uTime * 0.6 + ip.x ) ) ); }`); }; // (now and then they glide, wings still)
  gm.customProgramCacheKey = () => 'bigull';
  S.gulls = new THREE.InstancedMesh(gullGeo(), gm, BI_LIFE.gulls); S.gulls.frustumCulled = false; S.gulls.userData.noCast = true;
  S.boats = new THREE.InstancedMesh(boatGeo(), new THREE.MeshLambertMaterial({ vertexColors: true }), BI_LIFE.boats); S.boats.frustumCulled = false;
  grp.add(S.tufts, S.flowers, S.gulls, S.boats);
  return grp;
}

// where the gulls circle and the boats float: over the beaches, out on the sea
function placeLife(def) {
  const T = BOXES.terrain, sea = def.seaY ?? -0.25, rnd = ((s) => () => (s = (s * 16807) % 2147483647) / 2147483647)(1234);
  S.flocks = []; S.boatList = [];
  // kept clear of grass and flowers (the map session's ask): the mechs' drop pads, and the towns' flat ground
  const R = def.royale || {};
  S.clear = [...(R.drops || []).map((d) => [d[0], d[2], (d[3] || 8) + 1.5]), ...(R.pois || []).map((p) => [p.c[0], p.c[1], (p.flat || p.r || 0) * 0.85])];
  const C = S.cfg, NF = C.gulls ?? 0, NB = C.boats ?? 0, span = C.span || 260, sea0 = def.sea || def.seaY != null;
  for (let tries = 0; tries < 4000 && T && sea0 && (S.flocks.length < NF || S.boatList.length < NB); tries++) {
    const a = rnd() * Math.PI * 2, r = span * (0.75 + rnd()), x = Math.cos(a) * r * 1.2, z = Math.sin(a) * r, g = T ? T.at(x, z) : null;
    if (S.flocks.length < NF && g != null && g > sea - 0.5 && g < sea + 2) S.flocks.push({ x, z, y: 22 + rnd() * 18, r: 18 + rnd() * 20, w: (rnd() < 0.5 ? -1 : 1) * (0.12 + rnd() * 0.1), n: 9 });
    const far = r + span * 0.45;
    const bx = Math.cos(a) * far * 1.15, bz = Math.sin(a) * far, bg = T ? T.at(bx, bz) : null;
    if (S.boatList.length < NB && (bg == null || bg < sea - 4) && Math.hypot(bx, bz) < span * 2.4 && !S.boatList.some((b) => Math.hypot(b.x - bx, b.z - bz) < 60)) S.boatList.push({ x: bx, z: bz, r: 10 + rnd() * 25, w: (rnd() < 0.5 ? -1 : 1) * (0.02 + rnd() * 0.03), p: rnd() * 6.28, y: sea });
  }
  // no coast to find (a map of boxes): the flocks circle over the spawns, well up
  const sp = def.spawns || [];
  for (let k = 0; S.flocks.length < NF && sp.length && k < 20; k++) { const p = sp[Math.floor(rnd() * sp.length)]; S.flocks.push({ x: p[0] + (rnd() - 0.5) * 60, z: p[2] + (rnd() - 0.5) * 60, y: p[1] + 22 + rnd() * 14, r: 16 + rnd() * 18, w: (rnd() < 0.5 ? -1 : 1) * (0.12 + rnd() * 0.1), n: 9 }); }
  if (C.boxGrass) buildGrid(def, C.boxGrass);
  else S.grid = null;
}
// maps built of boxes: a 1 m grid of the highest box top over each cell, flagged where that top is grass (or lawn...)
function buildGrid(def, mats) {
  const want = new Set(mats), all = [...BOXES.filter((b) => !b.ter), ...(def.deco || []).filter((b) => !b.ter)];
  let [x0, z0, x1, z1] = def.bounds || [-200, -200, 200, 200];
  x0 = Math.max(-320, Math.floor(x0)); z0 = Math.max(-320, Math.floor(z0)); x1 = Math.min(320, Math.ceil(x1)); z1 = Math.min(320, Math.ceil(z1));
  const nx = x1 - x0, nz = z1 - z0, top = new Float32Array(nx * nz).fill(-1e9), ok = new Uint8Array(nx * nz);
  for (const b of all) {
    if (b.max[1] - b.min[1] > 60 || LIQ_SKIP.test(b.mat || '')) continue; // (skyboxes, the sea: not ground)
    const i0 = Math.max(0, Math.floor(b.min[0] - x0)), i1 = Math.min(nx, Math.ceil(b.max[0] - x0)), j0 = Math.max(0, Math.floor(b.min[2] - z0)), j1 = Math.min(nz, Math.ceil(b.max[2] - z0)), y = b.max[1], g = want.has(b.mat) ? 1 : 0;
    for (let i = i0; i < i1; i++) for (let j = j0; j < j1; j++) { const k = i * nz + j; if (y > top[k] + 0.01) { top[k] = y; ok[k] = g; } }
  }
  const T = BOXES.terrain; // shaped ground under it all (Suburb's lawns): grass where the terrain is a grass paint and nothing's on top
  if (T) { const gi = new Set([...want].map((m) => T.mats.indexOf(m)).filter((k) => k >= 0));
    for (let i = 0; i < nx; i++) for (let j = 0; j < nz; j++) { const x = x0 + i + 0.5, z = z0 + j + 0.5, ti = Math.floor(x - T.x0), tj = Math.floor(z - T.z0); if (ti < 0 || tj < 0 || ti >= T.nx || tj >= T.nz || !T.ok[ti * T.nz + tj]) continue; const y = T.at(x, z); const k = i * nz + j; if (y != null && y > top[k] + 0.01) { top[k] = y; ok[k] = gi.has(T.paint[ti * T.nz + tj]) ? 1 : 0; } } }
  S.grid = { x0, z0, nx, nz, top, ok };
}
const LIQ_SKIP = /water|sea|lava|oil|acid|slime|cola|dye|bile/;

// the field round the camera: tufts and flowers on grass and jungle floor
function layField(cx, cz) {
  const T = BOXES.terrain, Gd = S.grid; if (!T && !Gd) return;
  const R = S.lite ? BI_LIFE.rLite : BI_LIFE.r, C = BI_LIFE.cell, sea = S.sea, vz = T ? T.nz + 1 : 0, FL = S.cfg.flowers ?? BI_LIFE.flowers;
  const gi = T ? new Set((S.cfg.grass || ['grass', 'leaves']).map((m) => T.mats.indexOf(m)).filter((k) => k >= 0)) : null;
  let nt = 0, nf = 0;
  const clr = (S.clear || []).filter((k) => Math.hypot(k[0] - cx, k[1] - cz) < R + k[2]); // (only the ones that reach this patch)
  const i0 = Math.floor((cx - R) / C), i1 = Math.ceil((cx + R) / C), j0 = Math.floor((cz - R) / C), j1 = Math.ceil((cz + R) / C);
  for (let i = i0; i <= i1; i++) for (let j = j0; j <= j1; j++) {
    const x = (i + hash(i, j, 1)) * C, z = (j + hash(i, j, 2)) * C;
    if ((x - cx) * (x - cx) + (z - cz) * (z - cz) > R * R) continue;
    if (clr.length && clr.some((k) => (x - k[0]) * (x - k[0]) + (z - k[1]) * (z - k[1]) < k[2] * k[2])) continue;
    let y;
    if (Gd) { const gx = Math.floor(x - Gd.x0), gz = Math.floor(z - Gd.z0); if (gx < 0 || gz < 0 || gx >= Gd.nx || gz >= Gd.nz || !Gd.ok[gx * Gd.nz + gz]) continue; y = Gd.top[gx * Gd.nz + gz]; }
    else {
      const ti = Math.floor(x - T.x0), tj = Math.floor(z - T.z0);
      if (ti < 1 || tj < 1 || ti >= T.nx - 1 || tj >= T.nz - 1 || !T.ok[ti * T.nz + tj] || !gi.has(T.paint[ti * T.nz + tj])) continue;
      y = T.at(x, z); if (y == null) continue;
      const sl = Math.abs(T.H[(ti + 1) * vz + tj] - T.H[(ti - 1) * vz + tj]) + Math.abs(T.H[ti * vz + tj + 1] - T.H[ti * vz + tj - 1]);
      if (sl > 1.4) continue; // (steep: that's rock)
    }
    if (sea != null && y < sea + 0.25) continue;
    const hr = hash(i, j, 3);
    if (!S.lite && hr < FL && nf < 600) {
      e.set(0, hash(i, j, 4) * 6.28, 0); q.setFromEuler(e); const s = 1.0 + hash(i, j, 5) * 0.7; sc.set(s, s, s);
      S.flowers.setMatrixAt(nf, m4.compose(v.set(x, y - 0.02, z), q, sc)); S.flowers.setColorAt(nf, col.setHex(FLOWER_COLS[Math.floor(hash(i, j, 6) * FLOWER_COLS.length)])); nf++;
    } else if (hr < BI_LIFE.keep && nt < 10000) {
      e.set((hash(i, j, 7) - 0.5) * 0.3, hash(i, j, 4) * 6.28, (hash(i, j, 8) - 0.5) * 0.3); q.setFromEuler(e); const s = 0.7 + hash(i, j, 5) * 0.8; sc.set(s, s * (0.8 + hash(i, j, 9) * 0.5), s);
      S.tufts.setMatrixAt(nt++, m4.compose(v.set(x, y - 0.03, z), q, sc));
    }
  }
  S.tufts.count = nt; S.tufts.instanceMatrix.needsUpdate = true;
  S.flowers.count = nf; S.flowers.instanceMatrix.needsUpdate = true; if (S.flowers.instanceColor) S.flowers.instanceColor.needsUpdate = true;
  S.lx = cx; S.lz = cz;
}

// the palms, ferns and bushes (propfield.js's instanced Blender props) get the sway too
function swayProps() {
  G.scene.traverse((o) => {
    if (!o.isInstancedMesh || !S.swayRe.test(o.name)) return;
    for (const m of [].concat(o.material)) {
      if (S.swayed.has(m)) continue;
      S.swayed.add(m);
      if (!o.geometry.boundingBox) o.geometry.computeBoundingBox();
      const palm = /palm/.test(o.name), h = Math.max(0.2, o.geometry.boundingBox.max.y), prev = m.onBeforeCompile, prevKey = m.customProgramCacheKey ? m.customProgramCacheKey.bind(m) : null;
      const tmp = swayMat(new THREE.MeshBasicMaterial(), { amp: h * (palm ? 0.05 : 0.07), h }); // (in the model's own size: the tip moves about 5% of its height)
      m.onBeforeCompile = (sh, r) => { if (prev && prev !== THREE.Material.prototype.onBeforeCompile) prev.call(m, sh, r); tmp.onBeforeCompile(sh, r); };
      m.customProgramCacheKey = () => (prevKey ? prevKey() : '') + '|' + tmp.customProgramCacheKey();
      m.needsUpdate = true;
    }
  });
}

// bilook.js: the map changed
// cfg (maplooks.js, a map's life): { tufts, flowers (share of grass cells), grass (terrain paints), boxGrass (box mats),
// gulls (flocks), boats, sway (prop names that sway), tint (tufts' colour), wind, span (how far out the coast is) }
export function biLifeMap(cfg, def) {
  const on = !!cfg;
  S.on = on;
  if (S.group) S.group.visible = on;
  if (!on) return;
  S.cfg = cfg;
  if (!S.group) { S.group = build(); }
  if (S.group.parent !== G.scene) G.scene.add(S.group);
  S.sea = def.seaY ?? (def.sea ? -0.25 : null); S.lx = NaN;
  S.swayRe = new RegExp('^prop:(p_|s_)?(' + (cfg.sway || 'palm|fern|bush') + ')');
  placeLife(def);
  S.tufts.visible = cfg.tufts !== false; S.flowers.visible = cfg.tufts !== false;
  S.tufts.material.color.setHex(cfg.tint ?? 0xffffff); S.flowers.material.color.setHex(0xffffff);
  S.boats.count = S.boatList.length; S.gulls.count = Math.min(BI_LIFE.gulls, S.flocks.length * 9);
  U.uWind.value.set(...(cfg.wind || BI_LIFE.wind));
  S.propT = 0;
}
export function updateBiLife(dt) {
  if (!S.on || !S.group || !G.camera) return;
  U.uTime.value = performance.now() / 1000 % 3600;
  const lite = (G.settings && G.settings.jank) === 0;
  if (lite !== S.lite) { S.lite = lite; S.lx = NaN; }
  U.uR.value = lite ? BI_LIFE.rLite : BI_LIFE.r;
  const c = G.camera.position;
  if (S.cfg.tufts !== false && !(Math.hypot(c.x - S.lx, c.z - S.lz) < BI_LIFE.relay)) layField(c.x, c.z);
  if ((S.propT -= dt) <= 0) { S.propT = 2; swayProps(); } // (props stream in: look for new ones now and then)
  const t = U.uTime.value;
  let n = 0;
  for (const f of S.flocks) for (let k = 0; k < f.n && n < S.gulls.count; k++) { // gulls: round and round their beach, each on its own ring
    const a = t * f.w + k * 0.7, rr = f.r + (k % 3) * 4, y = f.y + Math.sin(t * 0.5 + k) * 2 + k * 0.3;
    const x = f.x + Math.cos(a) * rr, z = f.z + Math.sin(a) * rr, hd = Math.atan2(-Math.sin(a) * Math.sign(f.w), Math.cos(a) * Math.sign(f.w));
    e.set(0, hd, -Math.sign(f.w) * 0.35); q.setFromEuler(e); sc.set(1.8, 1.8, 1.8);
    S.gulls.setMatrixAt(n++, m4.compose(v.set(x, y, z), q, sc));
  }
  S.gulls.instanceMatrix.needsUpdate = true;
  let b = 0;
  for (const B of S.boatList) { // boats: a slow circle, bobbing, rolling and pitching on the swell
    const a = t * B.w + B.p, x = B.x + Math.cos(a) * B.r, z = B.z + Math.sin(a) * B.r;
    e.set(Math.sin(t * 0.9 + B.p) * 0.05, Math.atan2(-Math.sin(a) * Math.sign(B.w), Math.cos(a) * Math.sign(B.w)), Math.sin(t * 0.7 + B.p * 2) * 0.07); q.setFromEuler(e); sc.set(1.5, 1.5, 1.5);
    S.boats.setMatrixAt(b++, m4.compose(v.set(x, B.y + 0.35 + Math.sin(t * 1.1 + B.p) * 0.18, z), q, sc)); // (riding high: the waves are a metre tall out there)
  }
  S.boats.instanceMatrix.needsUpdate = true;
}
export const biLifeInfo = () => ({ on: S.on, tufts: S.tufts ? S.tufts.count : 0, flowers: S.flowers ? S.flowers.count : 0, gulls: S.gulls ? S.gulls.count : 0, boats: S.boats ? S.boats.count : 0,
  where: { boats: S.boatList.map((b) => [Math.round(b.x), Math.round(b.z)]), flocks: S.flocks.map((f) => [Math.round(f.x), Math.round(f.y), Math.round(f.z)]) } }); // (tests: where to point a camera)
