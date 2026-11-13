// Neon and lamps light the walls and floors round them (the RAY-TRACED LOOK, part 4; the owner: "anything that would come
// from ray tracing"). The game can only afford a few real point lights (lighting.js pools 2-4 near you), so a street full of
// signs lit almost nothing. This bakes every glowing thing's light once per map instead, into two small top-down maps:
//  - how much coloured light reaches each 2 m patch (all the signs, tubes and lamps within NEON.reach metres, fading
//    with distance) and the average height it comes from
//  - which way it comes from and how far, so a wall facing the sign takes it and the back of the wall doesn't
// The map's box materials and the Blender models read both (bounce.js-style shader patch): a pink sign tints the wall
// under it and the street in front pink, a cyan tube lights the alley cyan. Stronger at night. Off: a uniform at 0.
import * as THREE from 'three';
import { lightSources } from './lighting.js';
import { G } from './ctx.js';

export const NEON = { cell: 2, reach: 10, k: 1.8, nightK: 2.6, max: 520, fall: 4.5 };
const U = { uNK: { value: 0 }, uNC: { value: null }, uND: { value: null }, uNR: { value: new THREE.Vector4(0, 0, 1, 1) } };
let bake = null, on = false, ready = false, kNow = NEON.k, tick = 0;
const patched = new WeakSet();

const FRAG = `
if ( uNK > 0.0 ) { // the neon and lamps round here (neon.js)
  vec2 nuv = ( vNW.xz - uNR.xy ) / uNR.zw;
  if ( nuv.x > 0.0 && nuv.y > 0.0 && nuv.x < 1.0 && nuv.y < 1.0 ) {
    vec4 nc = texture2D( uNC, nuv ); vec4 nd = texture2D( uND, nuv );
    vec3 col = nc.rgb * 2.0; // (stored halved: room to add up)
    float sy = nc.a * 40.0 - 8.0, hd = max( nd.b * 12.0, 0.5 ); // where the light sits: its height, how far off sideways
    vec3 L = normalize( vec3( nd.r * 2.0 - 1.0, ( sy - vNW.y ) / hd, nd.g * 2.0 - 1.0 ) );
    vec3 nW = normalize( vNN );
    float face = max( dot( nW, L ), 0.0 ) * 0.8 + 0.2, hfall = exp( -abs( vNW.y - sy ) / ${NEON.fall.toFixed(1)} );
    reflectedLight.indirectDiffuse += ( material.diffuseColor + 0.08 ) * col * face * hfall * uNK; // (+0.08: dark asphalt still shows a coloured sheen, like it would wet)
  }
}
`;
export function neonMaterial(m) {
  if (!m || patched.has(m) || m.isMeshBasicMaterial || m.isShaderMaterial) return;
  patched.add(m);
  const prev = m.onBeforeCompile, prevKey = m.customProgramCacheKey ? m.customProgramCacheKey.bind(m) : null;
  m.onBeforeCompile = function (sh, r) {
    if (prev && prev !== THREE.Material.prototype.onBeforeCompile) prev.call(this, sh, r);
    if (!sh.fragmentShader.includes('#include <lights_fragment_end>') || !sh.vertexShader.includes('#include <worldpos_vertex>')) return;
    Object.assign(sh.uniforms, U);
    sh.vertexShader = 'varying vec3 vNW; varying vec3 vNN;\n' + sh.vertexShader.replace('#include <worldpos_vertex>', `#include <worldpos_vertex>
	{ vec4 nw = vec4( transformed, 1.0 ); vec3 nn = normal;
	#ifdef USE_INSTANCING
	nw = instanceMatrix * nw; nn = mat3( instanceMatrix ) * nn;
	#endif
	vNW = ( modelMatrix * nw ).xyz; vNN = normalize( mat3( modelMatrix ) * nn ); }`);
    sh.fragmentShader = 'uniform float uNK; uniform sampler2D uNC; uniform sampler2D uND; uniform vec4 uNR; varying vec3 vNW; varying vec3 vNN;\n'
      + sh.fragmentShader.replace('#include <lights_fragment_end>', '#include <lights_fragment_end>\n' + FRAG);
  };
  m.customProgramCacheKey = () => (prevKey ? prevKey() : '') + '|neon';
  m.needsUpdate = true;
}

// world.js, after lightingMap (it finds the lights): bake this map's neon
export function neonMap(def, MAT, night) {
  ready = false; U.uNK.value = 0; kNow = night ? NEON.nightK : NEON.k;
  if (U.uNC.value) { U.uNC.value.dispose(); U.uND.value.dispose(); U.uNC.value = U.uND.value = null; }
  const { src, n } = lightSources();
  if (!def || !src || !n) return;
  try {
    for (const v of Object.values(MAT)) if (v && v.mat) neonMaterial(v.mat);
    let [x0, z0, x1, z1] = def.bounds || [-150, -150, 150, 150];
    const half = NEON.max / 2, cx = (x0 + x1) / 2, cz = (z0 + z1) / 2;
    x0 = Math.max(x0, cx - half); x1 = Math.min(x1, cx + half); z0 = Math.max(z0, cz - half); z1 = Math.min(z1, cz + half);
    const C = NEON.cell, nx = Math.ceil((x1 - x0) / C), nz = Math.ceil((z1 - z0) / C), R = NEON.reach, rc = Math.ceil(R / C);
    const col = new Float32Array(nx * nz * 3), wy = new Float32Array(nx * nz), w = new Float32Array(nx * nz), dx = new Float32Array(nx * nz), dz = new Float32Array(nx * nz), dh = new Float32Array(nx * nz);
    // only the lights round where people play: the street lamps of a city 170 m below a rooftop map would sit in the same
    // patches and drag the light's height down to the street (so the roof got none)
    const sp = (def.spawns || []).map((p) => p[1]), lo = sp.length ? Math.min(...sp) - 14 : -1e9, hi = sp.length ? Math.max(...sp) + 45 : 1e9;
    for (let s = 0; s < n; s++) {
      const o = s * 8, sx = src[o], sy = src[o + 1], sz = src[o + 2], k = 0.6 + Math.min(1, src[o + 6] / 4) * 0.6; // (bigger signs throw more)
      if (sx > 1e5 || sy < lo || sy > hi) continue;
      const ci = Math.floor((sx - x0) / C), cj = Math.floor((sz - z0) / C);
      for (let j = Math.max(0, cj - rc); j <= Math.min(nz - 1, cj + rc); j++) for (let i = Math.max(0, ci - rc); i <= Math.min(nx - 1, ci + rc); i++) {
        const px = x0 + (i + 0.5) * C, pz = z0 + (j + 0.5) * C, ex = sx - px, ez = sz - pz, d = Math.hypot(ex, ez);
        if (d > R) continue;
        const f = (1 - d / R) ** 1.5 * k, q = j * nx + i;
        col[q * 3] += src[o + 3] * f; col[q * 3 + 1] += src[o + 4] * f; col[q * 3 + 2] += src[o + 5] * f;
        w[q] += f; wy[q] += sy * f; dh[q] += d * f;
        if (d > 0.01) { dx[q] += (ex / d) * f; dz[q] += (ez / d) * f; }
      }
    }
    const c8 = new Uint8Array(nx * nz * 4), d8 = new Uint8Array(nx * nz * 4);
    for (let q = 0; q < nx * nz; q++) {
      for (let c = 0; c < 3; c++) c8[q * 4 + c] = Math.min(255, col[q * 3 + c] * 0.5 * 255);
      const y = w[q] > 0 ? wy[q] / w[q] : 0, l = Math.hypot(dx[q], dz[q]) || 1;
      c8[q * 4 + 3] = Math.max(0, Math.min(255, ((y + 8) / 40) * 255));
      d8[q * 4] = (dx[q] / l * 0.5 + 0.5) * 255; d8[q * 4 + 1] = (dz[q] / l * 0.5 + 0.5) * 255; d8[q * 4 + 2] = Math.min(255, (w[q] > 0 ? dh[q] / w[q] : 0) / 12 * 255); d8[q * 4 + 3] = 255;
    }
    const tex = (d) => { const t = new THREE.DataTexture(d, nx, nz, THREE.RGBAFormat); t.magFilter = t.minFilter = THREE.LinearFilter; t.needsUpdate = true; return t; };
    let peak = 0; for (let q = 0; q < nx * nz; q++) peak = Math.max(peak, c8[q * 4], c8[q * 4 + 1], c8[q * 4 + 2]); bake = { peak, nx, nz, x0, z0, c8 };
    U.uNC.value = tex(c8); U.uND.value = tex(d8); U.uNR.value.set(x0, z0, nx * C, nz * C);
    ready = true;
  } catch (e) { console.warn('neon light off:', e); }
}
export function setNeon(v) { on = !!v; }
// every frame (world.js): the switch, and the Blender models that landed since
export function updateNeon() {
  U.uNK.value = on && ready ? kNow : 0;
  if (on && ready && ++tick % 90 === 45 && G.scene) G.scene.traverse((o) => { if (!o.isMesh || !o.material) return; for (const m of Array.isArray(o.material) ? o.material : [o.material]) if (m && m.isMeshStandardMaterial && !patched.has(m)) neonMaterial(m); });
}
export function neonDebugK(k) { kNow = k; } // (tests: crank it to see where it lands)
export const neonInfo = (x, z) => { const i = bake && x != null ? Math.floor((x - bake.x0) / NEON.cell) + Math.floor((z - bake.z0) / NEON.cell) * bake.nx : -1; return { on, ready, k: U.uNK.value, size: U.uNR.value.toArray().slice(2).map(Math.round), peak: bake && bake.peak, at: i >= 0 && bake ? Array.from(bake.c8.slice(i * 4, i * 4 + 4)) : null }; };
