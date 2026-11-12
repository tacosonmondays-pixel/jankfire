// Light bouncing off things (the owner: "I want lighting off the buildings, ... anything that would come from ray
// tracing"). Real bounce light would trace rays every frame; this bakes what matters once per map instead, a little at a
// time so loading isn't held up:
//  - a top-down map of the ground: what colour each 2 m patch is (its material) and whether the sun is on it. A sunlit
//    patch throws its colour up: the underside of a canopy over red tiles goes warm, a wall by green lawn goes green,
//    an overhang over a sunlit yellow plaza glows yellow. Ground in shade bounces a little too (the sky lights it).
//  - a map of the sunlit walls: each tall box's sides that face the sun throw their colour out a few metres across the
//    street, so the wall opposite a sunlit pink tower picks up pink.
// The map's box materials (world.js MAT) read both maps in their lighting (one more texture lookup each, two maps),
// faces looking down or sideways near the ground take the most. Turned on by the RAY-TRACED LOOK (fxsettings.js);
// off, it costs nothing but a uniform at 0. Potato and Crusty never get it.
import * as THREE from 'three';
import { BOXES } from '/shared/map.js';
import { sunAt, sunDir, sunBoxes } from './lighting.js';

export const BOUNCE = { cell: 2, k: 0.9, wallK: 0.7, reach: 4, blur: 2, max: 320, slice: 6000 };
const U = { uBK: { value: 0 }, uBG: { value: null }, uBW: { value: null }, uBR: { value: new THREE.Vector4(0, 0, 1, 1) }, uBY: { value: new THREE.Vector2(0, 1) } };
let on = false, ready = false, job = null, patched = new WeakSet();

// a material's colour, as the eye sees it on average (its colour times its texture's average)
const albedoCache = new Map();
function albedo(MAT, k) {
  if (albedoCache.has(k)) return albedoCache.get(k);
  const m = MAT[k] && MAT[k].mat, c = new THREE.Color(1, 1, 1);
  if (m && m.color) c.copy(m.color);
  const img = m && m.map && m.map.image;
  if (img && img.getContext) { try { const g = img.getContext('2d'), d = g.getImageData(0, 0, img.width, img.height).data; let r = 0, gg = 0, b = 0, n = 0; for (let i = 0; i < d.length; i += 16) { r += d[i]; gg += d[i + 1]; b += d[i + 2]; n++; } c.multiply(new THREE.Color(r / n / 255, gg / n / 255, b / n / 255)); } catch (e) { /* a texture we can't read: its colour alone */ } }
  if (m && m.emissive) c.add(m.emissive.clone().multiplyScalar(0.3));
  albedoCache.set(k, c);
  return c;
}

const PARS = `uniform float uBK; uniform sampler2D uBG; uniform sampler2D uBW; uniform vec4 uBR; uniform vec2 uBY; varying vec3 vBW; varying vec3 vBN;\n`;
const FRAG = `
if ( uBK > 0.0 ) { // light bounced off the ground and the sunlit walls round here (bounce.js)
  vec2 buv = ( vBW.xz - uBR.xy ) / uBR.zw;
  if ( buv.x > 0.0 && buv.y > 0.0 && buv.x < 1.0 && buv.y < 1.0 ) {
    vec4 gb = texture2D( uBG, buv ); vec3 wb = texture2D( uBW, buv ).rgb;
    float up = max( vBW.y - ( uBY.x + gb.a * uBY.y ), 0.0 );
    vec3 nW = normalize( vBN );
    vec3 b = gb.rgb * ( 0.55 - 0.45 * nW.y ) * exp( -up / 7.0 ) + wb * ( 1.0 - 0.7 * abs( nW.y ) );
    reflectedLight.indirectDiffuse += diffuseColor.rgb * b * uBK;
  }
}
`;
// give a material the bounce (once; its other patches, haze or snap, stay)
export function bounceMaterial(m) {
  if (!m || patched.has(m) || m.isMeshBasicMaterial || m.isShaderMaterial) return;
  patched.add(m);
  const prev = m.onBeforeCompile, prevKey = m.customProgramCacheKey ? m.customProgramCacheKey.bind(m) : null;
  m.onBeforeCompile = function (sh, r) {
    if (prev && prev !== THREE.Material.prototype.onBeforeCompile) prev.call(this, sh, r);
    if (!sh.fragmentShader.includes('#include <lights_fragment_end>')) return;
    Object.assign(sh.uniforms, U);
    sh.vertexShader = 'varying vec3 vBW; varying vec3 vBN;\n' + sh.vertexShader.replace('#include <worldpos_vertex>', `#include <worldpos_vertex>
	{ vec4 bw = vec4( transformed, 1.0 );
	#ifdef USE_INSTANCING
	bw = instanceMatrix * bw;
	#endif
	vBW = ( modelMatrix * bw ).xyz; vBN = normalize( mat3( modelMatrix ) * objectNormal ); }`);
    sh.fragmentShader = PARS + sh.fragmentShader.replace('#include <lights_fragment_end>', '#include <lights_fragment_end>\n' + FRAG);
  };
  m.customProgramCacheKey = () => (prevKey ? prevKey() : '') + '|bounce';
  m.needsUpdate = true;
}

// world.js, after the map is lit (the sun's direction is known): start baking, a slice a frame
export function bounceMap(def, MAT) {
  ready = false; U.uBK.value = 0; job = null;
  if (U.uBG.value) { U.uBG.value.dispose(); U.uBW.value.dispose(); U.uBG.value = U.uBW.value = null; }
  const boxes = sunBoxes();
  if (!def || !boxes || !boxes.length || def.sealed) return; // (indoors: the sun bounce makes no sense)
  for (const v of Object.values(MAT)) if (v && v.mat) bounceMaterial(v.mat);
  // the area: the map's bounds, or round the boxes, at most BOUNCE.max across
  let [x0, z0, x1, z1] = def.bounds || [-150, -150, 150, 150];
  const half = BOUNCE.max / 2, cxm = (x0 + x1) / 2, czm = (z0 + z1) / 2;
  x0 = Math.max(x0, cxm - half); x1 = Math.min(x1, cxm + half); z0 = Math.max(z0, czm - half); z1 = Math.min(z1, czm + half);
  const C = BOUNCE.cell, nx = Math.ceil((x1 - x0) / C), nz = Math.ceil((z1 - z0) / C);
  // the top of everything over each cell, and what it's made of
  const top = new Float32Array(nx * nz).fill(-1e9), mat = new Array(nx * nz).fill(null);
  for (const b of boxes) {
    if (!b || b.rot || b.max[1] - b.min[1] > 400 || /water|sea|lava|oil|acid|slime|cola|bile|dye/.test(b.mat || '')) continue;
    const i0 = Math.max(0, Math.floor((b.min[0] - x0) / C)), i1 = Math.min(nx, Math.ceil((b.max[0] - x0) / C)), j0 = Math.max(0, Math.floor((b.min[2] - z0) / C)), j1 = Math.min(nz, Math.ceil((b.max[2] - z0) / C));
    for (let i = i0; i < i1; i++) for (let j = j0; j < j1; j++) { const k = j * nx + i; if (b.max[1] > top[k]) { top[k] = b.max[1]; mat[k] = b.mat; } }
  }
  const T = BOXES.terrain;
  if (T) for (let i = 0; i < nx; i++) for (let j = 0; j < nz; j++) { const x = x0 + (i + 0.5) * C, z = z0 + (j + 0.5) * C, y = T.at(x, z); if (y != null && y > top[j * nx + i]) { top[j * nx + i] = y; const ti = Math.floor(x - T.x0), tj = Math.floor(z - T.z0); mat[j * nx + i] = T.mats[T.paint ? T.paint[ti * T.nz + tj] : 0] || T.mat; } }
  let ylo = 1e9, yhi = -1e9; for (const y of top) if (y > -1e8) { ylo = Math.min(ylo, y); yhi = Math.max(yhi, y); }
  if (ylo > yhi) return;
  const G = new Float32Array(nx * nz * 3), W = new Float32Array(nx * nz * 3), tall = boxes.filter((b) => b && !b.rot && b.max[1] - b.min[1] > 2.5 && b.max[0] - b.min[0] < 200 && b.max[2] - b.min[2] < 200);
  job = { def, MAT, x0, z0, nx, nz, C, top, mat, ylo, yhi, G, W, tall, i: 0, w: 0 };
}
function stepJob() {
  const J = job, n = J.nx * J.nz, end = Math.min(n, J.i + BOUNCE.slice);
  for (let k = J.i; k < end; k++) { // the ground: its colour, full in the sun, a third in the shade
    if (J.top[k] < -1e8 || !J.mat[k]) continue;
    const i = k % J.nx, j = (k / J.nx) | 0, x = J.x0 + (i + 0.5) * J.C, z = J.z0 + (j + 0.5) * J.C, a = albedo(J.MAT, J.mat[k]), s = sunAt(x, J.top[k] + 0.2, z) ? 1 : 0.32;
    J.G[k * 3] = a.r * s; J.G[k * 3 + 1] = a.g * s; J.G[k * 3 + 2] = a.b * s;
  }
  J.i = end;
  if (J.i < n) return false;
  const d = sunDir(), R = BOUNCE.reach;
  for (let w = J.w; w < Math.min(J.tall.length, J.w + 400); w++) { // the walls that face the sun throw their colour across the street
    const b = J.tall[w], a = albedo(J.MAT, b.mat), my = (b.min[1] + Math.min(b.max[1], b.min[1] + 12)) / 2;
    for (const [nx_, nz_] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const f = nx_ * d.x + nz_ * d.z; if (f < 0.15) continue;
      const fx = nx_ > 0 ? b.max[0] : nx_ < 0 ? b.min[0] : (b.min[0] + b.max[0]) / 2, fz = nz_ > 0 ? b.max[2] : nz_ < 0 ? b.min[2] : (b.min[2] + b.max[2]) / 2;
      if (!sunAt(fx + nx_ * 0.3, my, fz + nz_ * 0.3)) continue;
      const span = nx_ ? [b.min[2], b.max[2]] : [b.min[0], b.max[0]];
      for (let t = span[0]; t <= span[1]; t += J.C) for (let r = 0.5; r < R; r += J.C) {
        const x = nx_ ? fx + nx_ * r : t, z = nz_ ? fz + nz_ * r : t, i = Math.floor((x - J.x0) / J.C), j = Math.floor((z - J.z0) / J.C);
        if (i < 0 || j < 0 || i >= J.nx || j >= J.nz) continue;
        const k = j * J.nx + i, s = f * (1 - r / R) * BOUNCE.wallK;
        J.W[k * 3] += a.r * s; J.W[k * 3 + 1] += a.g * s; J.W[k * 3 + 2] += a.b * s;
      }
    }
  }
  J.w = Math.min(J.tall.length, J.w + 400);
  if (J.w < J.tall.length) return false;
  finish(J);
  return true;
}
function blur(A, nx, nz, r) {
  const B = new Float32Array(A.length);
  for (let pass = 0; pass < 2; pass++) {
    const src = pass ? B.slice() : A, dst = pass ? A : B;
    for (let j = 0; j < nz; j++) for (let i = 0; i < nx; i++) for (let c = 0; c < 3; c++) {
      let s = 0, n = 0;
      for (let o = -r; o <= r; o++) { const ii = pass ? i : i + o, jj = pass ? j + o : j; if (ii < 0 || jj < 0 || ii >= nx || jj >= nz) continue; s += src[(jj * nx + ii) * 3 + c]; n++; }
      dst[(j * nx + i) * 3 + c] = s / n;
    }
  }
  return A;
}
function finish(J) {
  const { nx, nz } = J;
  blur(J.G, nx, nz, BOUNCE.blur); blur(J.W, nx, nz, 1);
  const g = new Uint8Array(nx * nz * 4), w = new Uint8Array(nx * nz * 4), span = Math.max(0.01, J.yhi - J.ylo);
  for (let k = 0; k < nx * nz; k++) {
    for (let c = 0; c < 3; c++) { g[k * 4 + c] = Math.min(255, J.G[k * 3 + c] * 255); w[k * 4 + c] = Math.min(255, J.W[k * 3 + c] * 255); }
    g[k * 4 + 3] = J.top[k] > -1e8 ? Math.round(((J.top[k] - J.ylo) / span) * 255) : 0; w[k * 4 + 3] = 255;
  }
  const tex = (d) => { const t = new THREE.DataTexture(d, nx, nz, THREE.RGBAFormat); t.magFilter = t.minFilter = THREE.LinearFilter; t.needsUpdate = true; return t; };
  U.uBG.value = tex(g); U.uBW.value = tex(w);
  U.uBR.value.set(J.x0, J.z0, nx * J.C, nz * J.C); U.uBY.value.set(J.ylo, span);
  ready = true; job = null;
  U.uBK.value = on ? BOUNCE.k : 0;
}
// every frame (world.js): bake a slice, and the switch
export function updateBounce() { if (job) stepJob(); U.uBK.value = on && ready ? BOUNCE.k : 0; }
export function setBounce(v) { on = !!v; }
export const bounceInfo = () => ({ on, ready, baking: !!job, size: U.uBR.value.toArray().slice(2).map(Math.round) });
