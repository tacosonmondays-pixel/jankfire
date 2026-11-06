// City materials: one canvas atlas with a tile per family (shared/city/plan.js FAMS), sampled with world-space UVs that
// wrap inside their tile, so a whole chunk's buildings are ONE draw call. Plus flesh (wet, breathing: the vertex
// shader inflates it along the normal on a heartbeat, the fragment adds veins and a red rim), glow, glass and acid.
// All of them carry the Potato vertex snap (jank.js) and the game's fog.
import * as THREE from 'three';
import { FAMS } from '/shared/city/plan.js';
import { jankUniforms } from '../jank.js';

export const cityUniforms = { uTime: { value: 0 }, uBeat: { value: 0 }, uNight: { value: 0 } };
const T = 64, COLS = 8, ROWS = Math.ceil(FAMS.length / COLS), PAD = 0; // tiles are drawn seamless; nearest filtering, no bleed

function rnd(seed) { let s = seed; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
// each tile: greyscale-ish detail (the vertex colour is the paint), drawn wrapped so it tiles
function drawTile(g, fam, r) {
  const S = T;
  const speck = (base, vary, px = 2) => { for (let y = 0; y < S; y += px) for (let x = 0; x < S; x += px) { const k = base + (r() - 0.5) * vary; g.fillStyle = `rgb(${k},${k},${k})`; g.fillRect(x, y, px, px); } };
  const line = (c, x, y, w, h) => { g.fillStyle = c; g.fillRect(x, y, w, h); };
  switch (fam) {
    case 'dirt': speck(200, 60, 2); for (let i = 0; i < 30; i++) line('rgba(60,40,30,0.35)', r() * S, r() * S, 2, 2); break;
    case 'asphalt': speck(170, 40, 1); for (let i = 0; i < 12; i++) line('rgba(255,255,255,0.15)', r() * S, r() * S, 1, 1); line('rgba(0,0,0,0.25)', 0, (r() * S) | 0, S, 1); break;
    case 'concrete': speck(215, 26, 2); line('rgba(0,0,0,0.22)', 0, 0, S, 1); line('rgba(0,0,0,0.22)', 0, 0, 1, S); for (let i = 0; i < 4; i++) line('rgba(40,30,20,0.18)', r() * S, r() * S, 6, 1); break;
    case 'plaster': speck(236, 16, 2); for (let i = 0; i < 5; i++) { g.fillStyle = 'rgba(80,60,60,0.12)'; g.beginPath(); g.arc(r() * S, r() * S, 2 + r() * 6, 0, 6.3); g.fill(); } line('rgba(0,0,0,0.25)', 10, 30, 1, 9); line('rgba(0,0,0,0.25)', 11, 38, 6, 1); break;
    case 'brick': speck(220, 20, 2); for (let y = 0; y < S; y += 8) { line('rgba(60,40,40,0.5)', 0, y, S, 1); for (let x = (y / 8) % 2 ? 8 : 0; x < S; x += 16) line('rgba(60,40,40,0.5)', x, y, 1, 8); } break;
    case 'metal': speck(210, 14, 2); for (let x = 0; x < S; x += 16) line('rgba(255,255,255,0.25)', x, 0, 1, S); for (let i = 0; i < 6; i++) line('rgba(140,60,20,0.35)', r() * S, r() * S, 3, 5); line('rgba(0,0,0,0.3)', 3, 3, 2, 2); line('rgba(0,0,0,0.3)', 59, 3, 2, 2); break;
    case 'wood': speck(205, 18, 1); for (let y = 0; y < S; y += 8) line('rgba(70,40,20,0.45)', 0, y, S, 1); for (let i = 0; i < 4; i++) { g.strokeStyle = 'rgba(70,40,20,0.3)'; g.beginPath(); g.ellipse(r() * S, r() * S, 4, 1.5, 0, 0, 6.3); g.stroke(); } break;
    case 'tile': speck(232, 10, 4); for (let i = 0; i < S; i += 16) { line('rgba(0,0,0,0.3)', i, 0, 1, S); line('rgba(0,0,0,0.3)', 0, i, S, 1); } break;
    case 'corrug': for (let x = 0; x < S; x += 4) { line(`rgb(${x % 8 ? 240 : 190},${x % 8 ? 240 : 190},${x % 8 ? 240 : 190})`, x, 0, 4, S); } for (let i = 0; i < 8; i++) line('rgba(150,70,30,0.4)', r() * S, r() * S, 2, 6); break;
    case 'fabric': speck(226, 12, 1); for (let y = 0; y < S; y += 2) line('rgba(0,0,0,0.06)', 0, y, S, 1); break;
    case 'tiedye': { // pink / yellow / teal swirls
      const cols = ['#ff7ab0', '#ffe14d', '#4fd8c6', '#c07aff'];
      for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) { const a = Math.atan2(y - 32, x - 32), d = Math.hypot(x - 32, y - 32); g.fillStyle = cols[(((a / 6.283 + d / 14) * 4) % 4 + 4 | 0) % 4]; g.fillRect(x, y, 1, 1); }
      break;
    }
    case 'bone': speck(240, 14, 2); for (let x = 0; x < S; x += 8) line('rgba(120,90,60,0.35)', x, 0, 1, S); for (let y = 0; y < S; y += 10) line('rgba(120,90,60,0.25)', 0, y, S, 1); break;
    case 'paint': line('#fff', 0, 0, S, S); break;
    case 'rib': speck(230, 12, 2); for (let y = 0; y < S; y += 8) { line('rgba(120,20,50,0.45)', 0, y, S, 2); line('rgba(255,255,255,0.18)', 0, y + 3, S, 1); } break;
    case 'window': line('#7a6a50', 0, 0, S, S); for (let x = 2; x < S; x += 16) { line('#fff6d0', x, 6, 12, 22); line('#fff6d0', x, 38, 12, 22); line('rgba(90,60,30,0.6)', x + 5, 6, 2, 22); } break;
    case 'flesh': speck(225, 26, 2); for (let i = 0; i < 9; i++) { g.strokeStyle = 'rgba(110,10,40,0.55)'; g.lineWidth = 1.5; g.beginPath(); let x = r() * S, y = r() * S; g.moveTo(x, y); for (let k = 0; k < 5; k++) { x += (r() - 0.5) * 18; y += (r() - 0.5) * 18; g.lineTo(x, y); } g.stroke(); } break;
    case 'glass': line('#ccc', 0, 0, S, S); line('rgba(255,255,255,0.7)', 6, 6, 3, 30); line('rgba(255,255,255,0.5)', 12, 6, 1, 20); break;
    case 'glow': speck(245, 10, 4); break;
    default: speck(200, 30, 2);
  }
}

let atlas = null;
export function cityAtlas() {
  if (atlas) return atlas;
  const c = document.createElement('canvas');
  c.width = COLS * T; c.height = ROWS * T;
  const g = c.getContext('2d');
  FAMS.forEach((f, i) => { g.save(); g.translate((i % COLS) * T, Math.floor(i / COLS) * T); g.beginPath(); g.rect(0, 0, T, T); g.clip(); drawTile(g, f, rnd(1234 + i * 77)); g.restore(); });
  atlas = new THREE.CanvasTexture(c);
  atlas.magFilter = THREE.NearestFilter; atlas.minFilter = THREE.NearestMipmapLinearFilter; atlas.generateMipmaps = true;
  atlas.colorSpace = THREE.SRGBColorSpace;
  atlas.userData.canvas = c;
  return atlas;
}

// shared GLSL: unpack the colour attribute, pick the tile, snap verts on Potato
const VERT_HEAD = `
uniform vec2 uSnap; uniform float uTime; uniform float uBeat;
attribute vec4 cpack; attribute vec2 wuv;
varying vec3 vPaint; varying vec2 vWuv; varying float vFam; varying float vPulse; varying vec3 vWpos;
`;
const VERT_SNAP = `
vec4 jsnap = gl_Position; jsnap.xyz /= jsnap.w; jsnap.xy = floor(jsnap.xy * uSnap + 0.5) / uSnap; jsnap.xyz *= jsnap.w; gl_Position = jsnap;`;
const FRAG_HEAD = `
uniform sampler2D uAtlas; uniform float uTime; uniform float uBeat; uniform float uNight;
varying vec3 vPaint; varying vec2 vWuv; varying float vFam; varying float vPulse; varying vec3 vWpos;
vec4 atlasTex(vec2 uv, float fam) {
  vec2 cell = vec2(mod(fam, ${COLS}.0), floor(fam / ${COLS}.0));
  vec2 ts = vec2(${(1 / COLS).toFixed(6)}, ${(1 / ROWS).toFixed(6)});
  vec2 f = fract(uv);
  vec2 a = (cell + f) * ts; a.y = 1.0 - a.y;
  return textureGrad(uAtlas, a, dFdx(uv) * ts, dFdy(uv) * ts);
}
`;

function patch(mat, opts = {}) {
  const tex = cityAtlas();
  mat.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, { uSnap: jankUniforms.uSnap, uAtlas: { value: tex } }, cityUniforms);
    let vs = VERT_HEAD + sh.vertexShader;
    vs = vs.replace('#include <begin_vertex>', `#include <begin_vertex>
      vPaint = cpack.rgb; float pk = floor(cpack.a * 255.0 + 0.5); vFam = mod(pk, 32.0); vPulse = floor(pk / 32.0) / 7.0;
      vWuv = wuv;
      ${opts.pulse ? `{ vec3 wp = (modelMatrix * vec4(position, 1.0)).xyz;
        float wave = sin(uTime * 1.7 + wp.x * 0.35 + wp.z * 0.27) * 0.5 + 0.5;
        transformed += objectNormal * vPulse * (0.12 * wave + 0.22 * uBeat); }` : ''}`);
    vs = vs.replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\n vWpos = (modelMatrix * vec4(transformed, 1.0)).xyz;');
    vs = vs.replace('#include <project_vertex>', '#include <project_vertex>' + VERT_SNAP);
    sh.vertexShader = vs;
    let fs = FRAG_HEAD + sh.fragmentShader;
    fs = fs.replace('#include <map_fragment>', `
      vec4 tx = atlasTex(vWuv, vFam);
      diffuseColor.rgb *= vPaint * tx.rgb;
      ${opts.flesh ? `
      float veins = smoothstep(0.55, 0.0, abs(sin(vWpos.x * 1.3 + sin(vWpos.y * 2.1 + uTime * 0.3) * 1.5 + vWpos.z * 0.9)));
      diffuseColor.rgb = mix(diffuseColor.rgb, diffuseColor.rgb * vec3(0.55, 0.12, 0.25), veins * 0.45);
      diffuseColor.rgb *= 0.92 + 0.16 * uBeat;` : ''}
      ${opts.glowWin ? 'diffuseColor.rgb *= mix(0.55, 1.15, uNight);' : ''}`);
    if (opts.flesh) fs = fs.replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
      { float rim = pow(1.0 - abs(dot(normalize(vViewPosition), normal)), 2.5);
        totalEmissiveRadiance += vec3(0.9, 0.12, 0.2) * rim * 0.55 * (0.7 + 0.5 * uBeat); }`);
    sh.fragmentShader = fs;
  };
  mat.customProgramCacheKey = () => 'city:' + JSON.stringify(opts);
  return mat;
}

let MATS = null;
export function cityMaterials() {
  if (MATS) return MATS;
  const solid = patch(new THREE.MeshLambertMaterial({ color: 0xffffff }));
  const flesh = patch(new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.22, metalness: 0.0 }), { flesh: true, pulse: true });
  const glow = patch(new THREE.MeshBasicMaterial({ color: 0xffffff }), { glowWin: true });
  const glass = patch(new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.05, metalness: 0.2, transparent: true, opacity: 0.45, depthWrite: false }));
  const acid = patch(new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.1, emissive: 0x2a5a00, emissiveIntensity: 1 }), { pulse: true });
  // the far impostor: vertex colour + a procedural window grid, no texture
  const far = new THREE.MeshLambertMaterial({ vertexColors: true });
  far.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, { uSnap: jankUniforms.uSnap }, cityUniforms);
    sh.vertexShader = 'uniform vec2 uSnap;\nvarying vec3 vFw; varying vec3 vFn;\n' + sh.vertexShader.replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\n vFw = (modelMatrix * vec4(transformed, 1.0)).xyz; vFn = normal;').replace('#include <project_vertex>', '#include <project_vertex>' + VERT_SNAP);
    sh.fragmentShader = 'uniform float uNight;\nvarying vec3 vFw; varying vec3 vFn;\n' + sh.fragmentShader.replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
      if (abs(vFn.y) < 0.5) { vec2 q = vec2(abs(vFn.x) > 0.5 ? vFw.z : vFw.x, vFw.y);
        float win = step(0.45, fract(q.x / 3.0)) * step(0.5, fract(q.y / 4.0)) * step(0.35, fract(sin(floor(q.x / 3.0) * 12.9 + floor(q.y / 4.0) * 78.2) * 43758.5));
        totalEmissiveRadiance += vec3(1.0, 0.85, 0.5) * win * (0.15 + 0.6 * uNight); }`);
  };
  far.customProgramCacheKey = () => 'cityfar';
  MATS = { solid, flesh, glow, glass, acid, far };
  return MATS;
}
