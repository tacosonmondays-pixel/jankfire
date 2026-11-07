// Liquids: water that actually moves (waves sized to the surface, ripples, foam where it meets things, the sky and the
// sun glittering in it, caustics in the shallows), lava that flows under a cracking crust and burps, green goo that
// fizzes, oil with a rainbow on it, and the splashes when anything lands in them.
// world.js hands over the map's liquid boxes. this builds one mesh + one material per liquid (all animated through
// uniforms), a baked "shore map" from the map boxes (how far to the edge, how deep it is: foam, tint, caustics, waves
// calming down at the edges) and watches players, bots, gibs and grenades for splashes. all look: the only thing it
// changes is your own legs (wading slows you down a bit, movement is yours anyway)
import * as THREE from 'three';
import { G } from './ctx.js';
import { fx } from './fx.js';
import { sfx } from './audio.js';
import { ME } from './player.js';
import { flamesFromBoxes, clearMapFlames } from './flames.js';
import { LIQ, SH, SHORE, DEPTH, DROP, liquidMaterial, liquidBox, setLiquidHaze, tickLiquids, setLiquidQ as setQ } from './liquidmats.js';
export { LIQ, liquidMaterial, liquidBox };

// ------------------------------------------------------------ the map's liquids
const S = { surfs: [], meshes: [], grid: new Map(), big: [], mask: null, mw: 0, mh: 0, mr: [0, 0, 1, 1], tex: null, wr: new Map(), lavaS: [], q: 3, scene: null };
const CELL = 16;
function obbOf(b) { // footprint: centre, half extents, rotation (deco boxes can be turned)
  const cx = (b.min[0] + b.max[0]) / 2, cz = (b.min[2] + b.max[2]) / 2, hx = (b.max[0] - b.min[0]) / 2, hz = (b.max[2] - b.min[2]) / 2, r = b.rot || 0;
  const c = Math.cos(r), s = Math.sin(r), ex = Math.abs(c) * hx + Math.abs(s) * hz, ez = Math.abs(s) * hx + Math.abs(c) * hz;
  return { cx, cz, hx, hz, c, s, x0: cx - ex, x1: cx + ex, z0: cz - ez, z1: cz + ez };
}
// inside a footprint? (three's rotateY: world = (c*lx + s*lz, -s*lx + c*lz))
const inObb = (o, x, z, m = 0) => { const dx = x - o.cx, dz = z - o.cz, lx = o.c * dx - o.s * dz, lz = o.s * dx + o.c * dz; return Math.abs(lx) <= o.hx + m && Math.abs(lz) <= o.hz + m; };

function clearMap() {
  for (const m of S.meshes) { S.scene && S.scene.remove(m); m.geometry.dispose(); }
  S.meshes.length = 0; S.surfs.length = 0; S.grid.clear(); S.big.length = 0; S.lavaS.length = 0; S.wr.clear();
  S.mask = null;
  if (S.tex) { S.tex.dispose(); S.tex = null; }
  SH.uMask.value = null; SH.uMR.value.set(1e9, 1e9, 0, 0);
  clearMapFlames();
}

// world.js: every liquid box of the map (liquidBox), all the map's boxes (for the shore map), the map def
export function buildLiquids(scene, list, all, def, hazify) {
  if (hazify) setLiquidHaze(hazify);
  clearMap();
  S.scene = scene;
  const flames = [];
  for (const b of list) {
    if (DROP.has(b.mat)) continue;
    if (b.mat === 'flame') { flames.push(b); continue; }
    const L = LIQ[b.mat], o = obbOf(b);
    const s = { key: b.mat, kind: L.kind, top: b.max[1], bot: b.min[1], o, b, flat: (b.max[1] - b.min[1]) <= Math.max(0.6, Math.min(o.hx, o.hz) * 2), big: Math.max(o.hx, o.hz) > 150 };
    S.surfs.push(s);
    if (L.kind === 'lava' && s.flat) S.lavaS.push(s);
  }
  flamesFromBoxes(scene, flames);
  if (!S.surfs.length) return;
  for (const s of S.surfs) { // lookup grid (huge ones go in their own list)
    if (s.big) { S.big.push(s); continue; }
    for (let gx = Math.floor(s.o.x0 / CELL); gx <= Math.floor(s.o.x1 / CELL); gx++) for (let gz = Math.floor(s.o.z0 / CELL); gz <= Math.floor(s.o.z1 / CELL); gz++) {
      const k = gx * 65536 + gz; if (!S.grid.has(k)) S.grid.set(k, []); S.grid.get(k).push(s);
    }
  }
  bakeShore(all, def);
  // one mesh per liquid
  const by = new Map();
  for (const s of S.surfs) { if (!by.has(s.key)) by.set(s.key, []); by.get(s.key).push(s); }
  for (const [key, list2] of by) {
    const geo = surfGeo(key, list2);
    if (!geo) continue;
    const mat = liquidMaterial(key);
    if (mat.uniforms.uWR) mat.uniforms.uWR.value.copy(S.wr.get(key) || new THREE.Vector4(-1e6, -1e6, 1e6, 1e6));
    const m = new THREE.Mesh(geo, mat);
    m.renderOrder = LIQ[key].kind === 'water' ? 2 : 0;
    m.userData.noShadow = true; m.userData.liquid = key;
    scene.add(m);
    S.meshes.push(m);
  }
}

// the shore map: for every texel of the liquid area, how far it is to the nearest edge (a wall, a rock, a pier leg
// poking through, or the end of the liquid) and how deep it is down to whatever's under it. one texture per map
function bakeShore(all, def) {
  // the area: every normal sized liquid, and where the huge ones (the sea, the lake) meet something
  let x0 = Infinity, z0 = Infinity, x1 = -Infinity, z1 = -Infinity;
  const grow = (a, b, c, d) => { x0 = Math.min(x0, a); z0 = Math.min(z0, b); x1 = Math.max(x1, c); z1 = Math.max(z1, d); };
  const flat = S.surfs.filter((s) => s.flat);
  const solids = all.filter((b) => !liquidBox(b) && b.max[1] - b.min[1] > 0.01);
  for (const s of flat) {
    if (!s.big) { grow(s.o.x0 - 3, s.o.z0 - 3, s.o.x1 + 3, s.o.z1 + 3); continue; }
    for (const b of solids) {
      if (b.min[1] > s.top + 0.3 || b.max[1] < s.top - 4) continue;
      const o = obbOf(b);
      if (o.x1 < s.o.x0 || o.x0 > s.o.x1 || o.z1 < s.o.z0 || o.z0 > s.o.z1) continue;
      if (o.x1 - o.x0 > 400 && o.z1 - o.z0 > 400) continue; // a ground slab under everything isn't a shore
      grow(Math.max(o.x0, s.o.x0) - 6, Math.max(o.z0, s.o.z0) - 6, Math.min(o.x1, s.o.x1) + 6, Math.min(o.z1, s.o.z1) + 6);
    }
  }
  // a huge surface with nothing near it (the sea 150 m under the rooftops): waves round the middle of the map
  for (const s of flat) if (s.big) {
    const cx = Math.max(s.o.x0, Math.min(s.o.x1, 0)), cz = Math.max(s.o.z0, Math.min(s.o.z1, 0));
    const inside = x1 > x0 && !(x1 < s.o.x0 || x0 > s.o.x1 || z1 < s.o.z0 || z0 > s.o.z1);
    const r = inside ? [Math.max(s.o.x0, x0 - 60), Math.max(s.o.z0, z0 - 60), Math.min(s.o.x1, x1 + 60), Math.min(s.o.z1, z1 + 60)] : [Math.max(s.o.x0, cx - 260), Math.max(s.o.z0, cz - 260), Math.min(s.o.x1, cx + 260), Math.min(s.o.z1, cz + 260)];
    S.wr.set(s.key, new THREE.Vector4(...r)); s.wr = r;
  }
  if (!(x1 > x0)) return;
  // at most 640 m across (round the middle), about 0.3 m a texel
  const MAXW = 640;
  if (x1 - x0 > MAXW) { const c = Math.max(x0 + MAXW / 2, Math.min(x1 - MAXW / 2, 0)); x0 = c - MAXW / 2; x1 = c + MAXW / 2; }
  if (z1 - z0 > MAXW) { const c = Math.max(z0 + MAXW / 2, Math.min(z1 - MAXW / 2, 0)); z0 = c - MAXW / 2; z1 = c + MAXW / 2; }
  const p2 = (v) => 2 ** Math.ceil(Math.log2(v));
  const w = Math.max(64, Math.min(1024, p2((x1 - x0) / 0.3))), h = Math.max(64, Math.min(1024, p2((z1 - z0) / 0.3)));
  const tx = (x1 - x0) / w, tz = (z1 - z0) / h, n = w * h;
  const top = new Float32Array(n).fill(NaN), floor = new Float32Array(n).fill(-Infinity), wall = new Uint8Array(n);
  const span = (o, f) => { // every texel centre inside a footprint
    const i0 = Math.max(0, Math.floor((o.x0 - x0) / tx)), i1 = Math.min(w - 1, Math.ceil((o.x1 - x0) / tx)), j0 = Math.max(0, Math.floor((o.z0 - z0) / tz)), j1 = Math.min(h - 1, Math.ceil((o.z1 - z0) / tz));
    const plain = o.s === 0;
    for (let j = j0; j <= j1; j++) { const z = z0 + (j + 0.5) * tz; for (let i = i0; i <= i1; i++) { const x = x0 + (i + 0.5) * tx; if (plain ? x >= o.x0 && x <= o.x1 && z >= o.z0 && z <= o.z1 : inObb(o, x, z)) f(j * w + i); } }
  };
  for (const s of flat) span(s.o, (i) => { if (!(top[i] >= s.top)) top[i] = s.top; });
  for (const b of solids) {
    const o = obbOf(b), lo = b.min[1], hi = b.max[1];
    if (o.x1 < x0 || o.x0 > x1 || o.z1 < z0 || o.z0 > z1) continue;
    span(o, (i) => { const t = top[i]; if (t !== t) return; if (hi <= t + 0.02) { if (hi > floor[i] && hi > t - DEPTH) floor[i] = hi; } else if (lo < t + 0.05) wall[i] = 1; });
  }
  // distance to the nearest non-liquid texel (two-pass chamfer), in metres
  const d = new Float32Array(n), BIG = 1e6, tm = Math.min(tx, tz), dg = Math.hypot(tx, tz);
  for (let i = 0; i < n; i++) d[i] = top[i] === top[i] && !wall[i] ? BIG : 0;
  for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
    const k = j * w + i; let v = d[k]; if (!v) continue;
    if (i > 0) v = Math.min(v, d[k - 1] + tx); if (j > 0) { v = Math.min(v, d[k - w] + tz); if (i > 0) v = Math.min(v, d[k - w - 1] + dg); if (i < w - 1) v = Math.min(v, d[k - w + 1] + dg); }
    d[k] = v;
  }
  for (let j = h - 1; j >= 0; j--) for (let i = w - 1; i >= 0; i--) {
    const k = j * w + i; let v = d[k]; if (!v) continue;
    if (i < w - 1) v = Math.min(v, d[k + 1] + tx); if (j < h - 1) { v = Math.min(v, d[k + w] + tz); if (i < w - 1) v = Math.min(v, d[k + w + 1] + dg); if (i > 0) v = Math.min(v, d[k + w - 1] + dg); }
    d[k] = v;
  }
  void tm;
  // the depth gets a soft blur (about a metre): seabed boxes are steps, the colour shouldn't be
  const dep = new Float32Array(n), tmp = new Float32Array(n), rad = Math.max(1, Math.round(1.2 / tx));
  for (let i = 0; i < n; i++) dep[i] = top[i] !== top[i] || wall[i] ? 0 : floor[i] === -Infinity ? DEPTH : Math.min(DEPTH, top[i] - floor[i]);
  for (let j = 0; j < h; j++) { let acc = 0, c = 0; const r0 = j * w; for (let i = -rad; i < w; i++) { if (i + rad < w) { acc += dep[r0 + i + rad]; c++; } if (i - rad - 1 >= 0) { acc -= dep[r0 + i - rad - 1]; c--; } if (i >= 0) tmp[r0 + i] = acc / c; } }
  for (let i = 0; i < w; i++) { let acc = 0, c = 0; for (let j = -rad; j < h; j++) { if (j + rad < h) { acc += tmp[(j + rad) * w + i]; c++; } if (j - rad - 1 >= 0) { acc -= tmp[(j - rad - 1) * w + i]; c--; } if (j >= 0) dep[j * w + i] = acc / c; } }
  const px = new Uint8Array(n * 4);
  for (let i = 0; i < n; i++) {
    const t = top[i], liq = t === t && !wall[i];
    px[i * 4] = liq ? Math.min(255, Math.round((d[i] / SHORE) * 255)) : 0;
    px[i * 4 + 1] = !liq ? 0 : Math.min(255, Math.round((dep[i] / DEPTH) * 255));
    px[i * 4 + 2] = liq ? 255 : 0; px[i * 4 + 3] = 255;
  }
  const tex = new THREE.DataTexture(px, w, h, THREE.RGBAFormat);
  tex.magFilter = THREE.LinearFilter; tex.minFilter = THREE.LinearFilter; tex.wrapS = tex.wrapT = THREE.ClampToEdgeWrapping; tex.needsUpdate = true;
  S.tex = tex; S.mask = px; S.mw = w; S.mh = h; S.mr = [x0, z0, x1 - x0, z1 - z0];
  SH.uMask.value = tex; SH.uMR.value.set(x0, z0, 1 / (x1 - x0), 1 / (z1 - z0));
}
// the shore map on the CPU (splash heights match the waves you see): [shore 0..1, depth 0..1, liquid 0..1]
function maskAt(x, z) {
  if (!S.mask) return [1, 1, 1];
  const u = (x - S.mr[0]) / S.mr[2], v = (z - S.mr[1]) / S.mr[3];
  if (u < 0 || v < 0 || u > 1 || v > 1) return [1, 1, 1];
  const i = Math.min(S.mw - 1, (u * S.mw) | 0), j = Math.min(S.mh - 1, (v * S.mh) | 0), k = (j * S.mw + i) * 4;
  return [S.mask[k] / 255, S.mask[k + 1] / 255, S.mask[k + 2] / 255];
}

// the geometry: the top of every surface is a grid (fine for pools, up to ~3 m cells on the open sea, and the sea's far
// reaches outside its wave area as a few big flat pieces), the sides plain quads. overlapping copies of the same liquid
// (the Jankburg pond is four turned boxes) drop the triangles another one already covers, so the water isn't doubled
function surfGeo(key, list) {
  const P = [], N = [], I = [];
  const done = [];
  const quad = (a, b, c, d, nx, ny, nz) => { const v = P.length / 3; P.push(...a, ...b, ...c, ...d); for (let k = 0; k < 4; k++) N.push(nx, ny, nz); I.push(v, v + 1, v + 2, v, v + 2, v + 3); };
  const covered = (x, z, s) => done.some((e) => Math.abs(e.top - s.top) < 0.04 && inObb(e.o, x, z, -0.01));
  const grid = (s, lx0, lz0, lx1, lz1, cell, maxSeg) => {
    const o = s.o, nx = Math.max(1, Math.min(maxSeg, Math.ceil((lx1 - lx0) / cell))), nz = Math.max(1, Math.min(maxSeg, Math.ceil((lz1 - lz0) / cell)));
    const v0 = P.length / 3;
    for (let j = 0; j <= nz; j++) for (let i = 0; i <= nx; i++) {
      const lx = lx0 + ((lx1 - lx0) * i) / nx, lz = lz0 + ((lz1 - lz0) * j) / nz;
      P.push(o.cx + o.c * lx + o.s * lz, s.top, o.cz - o.s * lx + o.c * lz); N.push(0, 1, 0);
    }
    const at = (i, j) => v0 + j * (nx + 1) + i;
    const px = (k) => P[k * 3], pz = (k) => P[k * 3 + 2];
    for (let j = 0; j < nz; j++) for (let i = 0; i < nx; i++) {
      const a = at(i, j), b = at(i, j + 1), c = at(i + 1, j), d = at(i + 1, j + 1);
      for (const t of [[a, b, c], [c, b, d]]) {
        if (done.length && t.every((k) => covered(px(k), pz(k), s))) continue;
        I.push(...t);
      }
    }
  };
  for (const s of list) {
    const o = s.o, hx = o.hx, hz = o.hz;
    if (!s.flat) { // a fall: all four upright faces (lava / goo running down)
      const { x0: a0, x1: a1, z0: c0, z1: c1 } = o, y0 = s.bot, y1 = s.top;
      quad([a0, y0, c1], [a1, y0, c1], [a1, y1, c1], [a0, y1, c1], 0, 0, 1); quad([a1, y0, c0], [a0, y0, c0], [a0, y1, c0], [a1, y1, c0], 0, 0, -1);
      quad([a1, y0, c1], [a1, y0, c0], [a1, y1, c0], [a1, y1, c1], 1, 0, 0); quad([a0, y0, c0], [a0, y0, c1], [a0, y1, c1], [a0, y1, c0], -1, 0, 0);
      quad([a0, y1, c1], [a1, y1, c1], [a1, y1, c0], [a0, y1, c0], 0, 1, 0);
      continue;
    }
    if (s.big && s.wr && !o.s) { // the sea: a fine grid over its wave area, four flat pieces round it
      const [wx0, wz0, wx1, wz1] = s.wr, toL = (x, z) => [x - o.cx, z - o.cz];
      const [ax, az] = toL(wx0, wz0), [bx, bz] = toL(wx1, wz1);
      grid(s, ax, az, bx, bz, Math.max(3.2, Math.max(bx - ax, bz - az) / 130), 150); // (~3 m cells: the swell is 20-30 m long)
      if (az > -hz) grid(s, -hx, -hz, hx, az, 1e9, 8); if (bz < hz) grid(s, -hx, bz, hx, hz, 1e9, 8);
      if (ax > -hx) grid(s, -hx, az, ax, bz, 1e9, 8); if (bx < hx) grid(s, bx, az, hx, bz, 1e9, 8);
    } else {
      const big = Math.max(hx, hz) * 2, cell = big < 6 ? 0.5 : big < 30 ? 0.75 : Math.max(1.5, big / 160);
      grid(s, -hx, -hz, hx, hz, cell, 200);
    }
    // the sides (only as deep as it's worth: nobody sees the bottom of the sea)
    const y1 = s.top, y0 = Math.max(s.bot, s.top - 2.5);
    if (y1 - y0 > 0.005 && !s.big) {
      const cw = (lx, lz) => [o.cx + o.c * lx + o.s * lz, o.cz - o.s * lx + o.c * lz], nr = (nx, nz) => [o.c * nx + o.s * nz, -o.s * nx + o.c * nz];
      for (const [p, q, nn] of [[[-hx, hz], [hx, hz], [0, 1]], [[hx, -hz], [-hx, -hz], [0, -1]], [[hx, hz], [hx, -hz], [1, 0]], [[-hx, -hz], [-hx, hz], [-1, 0]]]) {
        const A = cw(...p), B = cw(...q), n2 = nr(...nn);
        quad([A[0], y0, A[1]], [B[0], y0, B[1]], [B[0], y1, B[1]], [A[0], y1, A[1]], n2[0], 0, n2[1]);
      }
    }
    done.push(s);
  }
  if (!I.length) return null;
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(N, 3));
  g.setIndex(I);
  g.computeBoundingSphere();
  return g;
}

// ------------------------------------------------------------ queries (splashes, wading)
// the wave height at a point, the same sum the shader does
function waveH(s, x, z) {
  const L = LIQ[s.key];
  if (!L.amp || !s.flat) return 0;
  const mk = maskAt(x, z), wr = s.wr;
  const edge = wr ? Math.min(x - wr[0], wr[2] - x, z - wr[1], wr[3] - z) : 1e6;
  const sm = (a, b, v) => { const k = Math.max(0, Math.min(1, (v - a) / (b - a))); return k * k * (3 - 2 * k); };
  const damp = sm(0, 0.32, mk[0]) * mk[2] * Math.max(0, Math.min(1, edge / 30)) * (1 + ((L.swell || 0) * (sm(0, 0.35, mk[1]) - 1)));
  if (damp <= 0) return 0;
  const t = SH.uTime.value, len = L.len || 4;
  let r = 0;
  for (let i = 0; i < 4; i++) {
    const a = 0.6 + i * 2.13, Ln = len * 0.6 ** i, k = 6.2832 / Ln, w = Math.sqrt(9.8 * k) * 0.55, A = 0.55 ** i;
    const ph = (Math.cos(a) * x + Math.sin(a) * z) * k - w * t + i * 1.7, sn = Math.sin(ph) * 0.5 + 0.5;
    r += A * (sn * sn * 2 - 0.6);
  }
  return (r / 2.02) * L.amp * damp;
}
// the liquid surface over (x, z) whose top is within [y - below, y + above] (null if none). returns the surface
export function liquidAt(x, y, z, below = 3, above = 0.6) {
  if (!S.surfs.length) return null;
  let best = null;
  const test = (s) => {
    if (!s.flat || y < s.top - below - (s.big ? 1e4 : 0) || y > s.top + above) return;
    if (!inObb(s.o, x, z)) return;
    if (!best || s.top > best.top) best = s;
  };
  const c = S.grid.get(Math.floor(x / CELL) * 65536 + Math.floor(z / CELL));
  if (c) for (const s of c) test(s);
  for (const s of S.big) test(s);
  return best;
}
export const surfaceY = (s, x, z) => s.top + waveH(s, x, z);
export const liquidDepth = (x, z) => maskAt(x, z)[1] * DEPTH; // (to the floor under it)

// ------------------------------------------------------------ splashes: droplets, a crown, rings on the surface
const RINGS = 64;
let rings = null;
const ringList = []; // { x, y, z, s, r, t, life, c }
const RING_VS = `attribute float aA; varying vec2 vUv; varying float vA;
#include <fog_pars_vertex>
void main() { vUv = uv; vA = aA; vec4 mvPosition = modelViewMatrix * instanceMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mvPosition;
#include <fog_vertex>
}`;
const RING_FS = `varying vec2 vUv; varying float vA;
#include <fog_pars_fragment>
void main() {
  float r = length(vUv - 0.5) * 2.0;
  float a = step(abs(r - 0.86), 0.07) + step(abs(r - 0.55), 0.04) * 0.6; // a ring and a fainter one inside it
  a *= vA; if (a < 0.02) discard;
  vec3 c = vec3(1.0);
#ifdef USE_INSTANCING_COLOR
  c = vColor;
#endif
  gl_FragColor = vec4(c, a);
  #include <colorspace_fragment>
  #include <fog_fragment>
}`;
function ringMesh() {
  if (rings) return rings;
  const geo = new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2);
  geo.setAttribute('aA', new THREE.InstancedBufferAttribute(new Float32Array(RINGS), 1).setUsage(THREE.DynamicDrawUsage));
  const mat = new THREE.ShaderMaterial({ uniforms: THREE.UniformsUtils.clone(THREE.UniformsLib.fog), vertexShader: '#define USE_INSTANCING_COLOR\nvarying vec3 vColor;\n' + RING_VS.replace('vA = aA;', 'vA = aA; vColor = instanceColor;'), fragmentShader: '#define USE_INSTANCING_COLOR\nvarying vec3 vColor;\n' + RING_FS,
    fog: true, transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -4 });
  rings = new THREE.InstancedMesh(geo, mat, RINGS);
  rings.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(RINGS * 3), 3);
  rings.count = 0; rings.frustumCulled = false; rings.renderOrder = 3; rings.userData.noShadow = true;
  return rings;
}
const RC = { water: 0xffffff, lava: 0xffd040, goo: 0xd8ff6a };
function addRing(s, x, z, size, life = 0.9) {
  if (ringList.length >= RINGS) ringList.shift();
  ringList.push({ s, x, z, size, t: 0, life, c: s.key === 'oil' ? 0x9a8aff : RC[s.kind] });
}
const R = (k = 1) => (Math.random() * 2 - 1) * k;
// something hit the surface s at (x, z). k: how big (0.1 = a bullet, 0.3 = a step, 1 = a player belly flop, 2 = a boom)
export function splash(s, x, z, k = 1, quiet = false) {
  if (!s) return;
  const y = surfaceY(s, x, z), P = fx.parts && fx.parts(), L = LIQ[s.key];
  addRing(s, x, z, 0.6 + k * 2.2, 0.6 + k * 0.5);
  if (k > 0.5) addRing(s, x, z, 1.2 + k * 3.4, 1.1 + k * 0.5);
  if (!P) return;
  const n = Math.min(80, Math.round(6 + k * 34));
  if (s.kind === 'water') {
    const c0 = s.key === 'oil' ? 0x1a1420 : s.key.startsWith('dye') ? L.shal : 0xffffff, c1 = s.key === 'oil' ? 0x000000 : s.key.startsWith('dye') ? L.deep : L.shal;
    for (let i = 0; i < n; i++) { const a = Math.random() * 6.2832, sp = (1 + Math.random() * 3) * (0.6 + k * 0.5), up = (2.5 + Math.random() * 5) * (0.5 + k * 0.6);
      P.misc.spawn(x + R(0.2), y + 0.05, z + R(0.2), Math.cos(a) * sp, up, Math.sin(a) * sp, 0.5 + Math.random() * 0.5, 0.07 + Math.random() * 0.08 * (0.5 + k), 0.03, c0, c1, 1, 16, 0.4); }
    // the crown: a column of white chunks thrown straight up
    if (k > 0.45) for (let i = 0; i < Math.round(8 + k * 14); i++) { const a = (i / 10) * 6.2832, r = 0.25 + k * 0.25;
      P.smoke.spawn(x + Math.cos(a) * r, y + 0.1, z + Math.sin(a) * r, Math.cos(a) * 1.2, 3 + k * 4 + Math.random() * 3, Math.sin(a) * 1.2, 0.5 + Math.random() * 0.4, 0.35 + k * 0.25, 0.12, c0, c1, 0.9, 14, 0.8); }
    if (!quiet) sfx.liqSplash([x, y, z], k);
  } else {
    const hot = s.kind === 'lava';
    for (let i = 0; i < n; i++) { const a = Math.random() * 6.2832, sp = (1 + Math.random() * 2.5) * (0.6 + k * 0.4);
      (hot ? P.fire : P.misc).spawn(x + R(0.2), y + 0.05, z + R(0.2), Math.cos(a) * sp, (2 + Math.random() * 4) * (0.5 + k * 0.5), Math.sin(a) * sp, 0.5 + Math.random() * 0.5, 0.09 + Math.random() * 0.09, 0.03, L.hot, L.mid, 1, 14, 0.5); }
    if (hot) for (let i = 0; i < 4 + k * 6; i++) P.smoke.spawn(x + R(0.5), y + 0.2, z + R(0.5), R(0.4), 1 + Math.random() * 1.5, R(0.4), 1.2 + Math.random(), 0.3, 1.6, 0x5a4a4a, 0x2a2222, 0.5, -0.3, 0.5);
    if (!quiet) (hot ? sfx.sizzle : sfx.gloop)([x, y, z], k);
  }
}
// a bullet's path a -> b: if it went through a liquid on the way, a little plip where it went in
function tracerHit(a, b) {
  if (!S.surfs.length || Math.abs(a[1] - b[1]) < 1e-4) return;
  let best = null, bt = 2;
  for (const s of S.surfs) {
    if (!s.flat) continue;
    const t = (s.top - a[1]) / (b[1] - a[1]);
    if (!(t > 0 && t < 1) || t >= bt) continue;
    const x = a[0] + (b[0] - a[0]) * t, z = a[2] + (b[2] - a[2]) * t;
    if (!inObb(s.o, x, z)) continue;
    best = [s, x, z]; bt = t;
  }
  if (!best) return;
  splash(best[0], best[1], best[2], 0.14, true);
  sfx.plip([best[1], best[0].top, best[2]]);
}
// a bang right on (or just under) a surface: a big column of it
function boomHit(p) {
  const s = liquidAt(p[0], p[1], p[2], 2.5, 2);
  if (s) splash(s, p[0], p[2], 2.2);
}
fx.onTracer = tracerHit;
fx.onBoom = boomHit;

// ------------------------------------------------------------ the watcher: who went in, who's wading
const seen = new WeakMap(); // thing -> { y, sx, sz, step }
function watch(obj, x, y, z, vy, kind, me) {
  let w = seen.get(obj);
  const s = liquidAt(x, y, z, 3, 1.2);
  if (!w) { w = { y, step: 0, px: x, pz: z, inT: 0 }; seen.set(obj, w); }
  if (s) {
    const top = surfaceY(s, x, z);
    if (w.y > top + 0.02 && y <= top + 0.02) { // went in
      const k = kind === 'proj' ? 0.35 + Math.min(0.6, Math.abs(vy) / 30) : kind === 'gib' ? 0.25 : Math.min(2, 0.35 + Math.abs(vy) / 14);
      splash(s, x, z, k, kind === 'gib' && Math.random() < 0.6);
      if (me && k > 0.9) G.shake = Math.max(G.shake || 0, Math.min(0.5, k * 0.25));
    }
    // wading: walking along the bottom with the surface round your legs
    if (kind === 'body' && y < top && y > top - 1.7 && y > s.top - (s.big ? 1e4 : 2)) {
      const dx = x - w.px, dz = z - w.pz, d = Math.hypot(dx, dz);
      w.step += d;
      w.inT += 1;
      if (w.step > 1.25 && d < 2) { // a step
        w.step = 0;
        const deep = Math.min(1, (top - y) / 0.8);
        splash(s, x, z, 0.12 + deep * 0.2, true);
        if (s.kind === 'water') sfx.wade([x, top, z], deep, me); else if (s.kind === 'lava') sfx.sizzle([x, top, z]); else sfx.gloop([x, top, z], 0.2);
      } else if (d > 0.02 && Math.random() < 0.15) addRing(s, x, z, 0.8, 0.7); // a wake behind you
      if (me) ME.wadeMul = 1 - (0.12 + 0.33 * Math.min(1, (top - y) / 0.8));
    } else if (me) ME.wadeMul = 1;
  } else if (me) ME.wadeMul = 1;
  w.y = y; w.px = x; w.pz = z;
}

// ------------------------------------------------------------ every frame
let lastT = 0, emberT = 0;
const _m = new THREE.Matrix4(), _c = new THREE.Color(), _q = new THREE.Quaternion(), _sc = new THREE.Vector3(), _p = new THREE.Vector3();
export function updateLiquids(dt) {
  const now = performance.now();
  tickLiquids(now / 1000);
  void lastT;
  if (!S.surfs.length) { if (rings) rings.count = 0; return; }
  // splashes
  if (G.joined) {
    if (ME.alive) watch(ME, ME.pos[0], ME.pos[1], ME.pos[2], ME.vel[1], 'body', true); else ME.wadeMul = 1;
    for (const r of G.remotes.values()) if (r.alive && r.pos && (!r.ch || !r.ch.root || r.ch.root.visible !== false)) watch(r, r.pos[0], r.pos[1], r.pos[2], r.vel ? r.vel[1] : 0, 'body', false);
    for (const pr of G.projs.values()) if (pr.p) watch(pr, pr.p[0], pr.p[1], pr.p[2], pr.v ? pr.v[1] : 0, 'proj', false);
    for (const g of G.gibs) if (g.m) watch(g, g.m.position.x, g.m.position.y, g.m.position.z, g.v ? g.v[1] : 0, 'gib', false);
  }
  // lava: embers spitting off it near you, the odd bubble burst
  emberT -= dt;
  if (S.lavaS.length && emberT <= 0 && G.camera) {
    emberT = S.q >= 2 ? 0.05 : 0.15;
    const P = fx.parts && fx.parts(), cam = G.camera.position;
    for (const s of S.lavaS) {
      const cx = Math.max(s.o.x0, Math.min(s.o.x1, cam.x)), cz = Math.max(s.o.z0, Math.min(s.o.z1, cam.z));
      if (Math.hypot(cx - cam.x, s.top - cam.y, cz - cam.z) > 45 || !P) continue;
      const x = s.o.x0 + Math.random() * (s.o.x1 - s.o.x0), z = s.o.z0 + Math.random() * (s.o.z1 - s.o.z0);
      if (Math.random() < 0.35) P.fire.spawn(x, s.top + 0.05, z, R(0.6), 1.5 + Math.random() * 2.5, R(0.6), 0.8 + Math.random() * 0.8, 0.1, 0.02, 0xffe070, 0xff2200, 1, -0.5, 0.4);
      if (Math.random() < 0.04) { for (let k = 0; k < 6; k++) P.fire.spawn(x, s.top + 0.05, z, R(1.2), 2 + Math.random() * 3, R(1.2), 0.5 + Math.random() * 0.5, 0.12, 0.03, 0xfff2b0, 0xff3a00, 1, 9, 0.3); sfx.blorp([x, s.top, z]); }
    }
  }
  // rings: grow and fade, riding the waves
  const rm = ringMesh();
  if (!rm.parent && G.scene) G.scene.add(rm);
  let n = 0;
  const aA = rm.geometry.attributes.aA;
  for (let i = ringList.length - 1; i >= 0; i--) {
    const r = ringList[i];
    r.t += dt;
    if (r.t >= r.life) { ringList.splice(i, 1); continue; }
    const k = r.t / r.life, sz = r.size * (0.25 + 0.75 * Math.sqrt(k));
    _p.set(r.x, surfaceY(r.s, r.x, r.z) + 0.03, r.z); _sc.set(sz, 1, sz);
    rm.setMatrixAt(n, _m.compose(_p, _q, _sc));
    rm.setColorAt(n, _c.setHex(r.c));
    aA.array[n] = (1 - k) * (1 - k) * 0.85;
    n++;
  }
  rm.count = n;
  if (n) { rm.instanceMatrix.needsUpdate = true; rm.instanceColor.needsUpdate = true; aA.needsUpdate = true; }
}

// world.js: the map's sky + sun (what the water reflects and glitters with), the graphics preset
export function liquidsMap(def, sky, sunPos, night) {
  SH.uSkyT.value.setHex(sky.top); SH.uSkyM.value.setHex(sky.mid);
  if (sunPos) SH.uSun.value.copy(sunPos).normalize();
  SH.uSunC.value.setHex(night ? 0xc8d8ff : 0xfff2c8);
  SH.uNight.value = night ? 1 : 0;
}
export function setLiquidQ(i) { S.q = i; setQ(i); }
export function liquidInfo() { return { surfs: S.surfs.length, meshes: S.meshes.length, mask: S.mask ? [S.mw, S.mh, S.mr.map((v) => Math.round(v))] : null, rings: ringList.length, keys: [...new Set(S.surfs.map((s) => s.key))] }; }
