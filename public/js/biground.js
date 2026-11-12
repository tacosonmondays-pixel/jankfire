// BATTLE ISLAND's ground (the look pass, after bilook.js's sky): one material for the whole island instead of a flat
// painted colour per patch. The map's paint (shared/battleisland.js relief: sand, wet sand, grass, jungle, road, rock)
// is baked into a soft "splat" texture, a metre a texel, blurred so patches melt into each other, and the shader lays
// real tiling surfaces through it: grass blades, rippled sand, darker wet sand at the waterline, a packed dirt road,
// rock projected from three sides on anything steep (the cliffs, the quarry, the crags) so it never stretches. Every
// surface has its own small detail texture (made here, in code: nothing downloaded), a bump from it, and big slow
// colour drift across the island so no tile repeats in sight. Lit by the usual lights (Lambert, shadows, fog).
// Potato: the same colours, one sample per surface, no bump, no three-sided rock, snapped like the rest (uLite).
import * as THREE from 'three';
import { jankUniforms } from './jank.js';

export const BI_GROUND = {
  grass: [0.22, 0.56, 0.10], grassDry: [0.50, 0.64, 0.18], jungle: [0.16, 0.38, 0.10],
  sand: [0.95, 0.85, 0.62], wet: [0.60, 0.52, 0.38], rock: [0.56, 0.53, 0.50], rockWarm: [0.62, 0.50, 0.40], road: [0.50, 0.36, 0.22],
  bump: 0.9, // how strongly the detail lifts the light
};

// ---- small tileable detail textures: R = brightness, G = a second colour's share, B = height (for the bump)
function hash(i, j, s) { let h = (i * 374761393 + j * 668265263 + s * 2147483647) | 0; h = (h ^ (h >>> 13)) * 1274126177 | 0; return ((h ^ (h >>> 16)) >>> 0) / 4294967295; }
function vnoise(x, y, p, s) { // value noise that wraps every p cells (so the texture tiles)
  const i = Math.floor(x), j = Math.floor(y), fx = x - i, fy = y - j, u = fx * fx * (3 - 2 * fx), v = fy * fy * (3 - 2 * fy);
  const a = hash(((i % p) + p) % p, ((j % p) + p) % p, s), b = hash((((i + 1) % p) + p) % p, ((j % p) + p) % p, s);
  const c = hash(((i % p) + p) % p, (((j + 1) % p) + p) % p, s), d = hash((((i + 1) % p) + p) % p, (((j + 1) % p) + p) % p, s);
  return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
}
function fbm(x, y, p, s, oct = 4) { let a = 0.5, t = 0, f = 1; for (let o = 0; o < oct; o++) { t += a * vnoise(x * f, y * f, p * f, s + o); a *= 0.5; f *= 2; } return t; }
function tex(N, fn) {
  const d = new Uint8Array(N * N * 4);
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) { const [r, g, b] = fn(x / N, y / N, x, y); const k = (y * N + x) * 4; d[k] = r * 255; d[k + 1] = g * 255; d[k + 2] = b * 255; d[k + 3] = 255; }
  const t = new THREE.DataTexture(d, N, N, THREE.RGBAFormat);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearMipmapLinearFilter; t.generateMipmaps = true; t.anisotropy = 8; t.needsUpdate = true;
  return t;
}
const cl = (v) => Math.max(0, Math.min(1, v));
function makeTextures() {
  const N = 256;
  // grass: a carpet of short blades (streaks leaning various ways) over clumpy patches
  const blades = new Float32Array(N * N);
  for (let n = 0; n < 9000; n++) {
    const x0 = hash(n, 1, 7) * N, y0 = hash(n, 2, 7) * N, a = -Math.PI / 2 + (hash(n, 3, 7) - 0.5) * 1.6, L = 3 + hash(n, 4, 7) * 6, w = 0.55 + 0.45 * hash(n, 5, 7);
    for (let t = 0; t < L; t++) { const x = Math.floor(x0 + Math.cos(a) * t + N) % N, y = Math.floor(y0 + Math.sin(a) * t + N) % N; blades[y * N + x] = Math.max(blades[y * N + x], w * (0.5 + 0.5 * t / L)); }
  }
  const grass = tex(N, (u, v, x, y) => { const c = fbm(u * 6, v * 6, 6, 11), b = blades[y * N + x]; return [cl(0.45 + 0.4 * b + 0.25 * (c - 0.5)), cl(fbm(u * 4, v * 4, 4, 12) * 1.2 - 0.25), cl(0.3 + 0.7 * b)]; });
  // sand: fine grain over soft wind ripples
  const sand = tex(N, (u, v) => { const r = 0.5 + 0.5 * Math.sin((v * 6 + fbm(u * 3, v * 3, 3, 21) * 2.6) * Math.PI * 2), g = hash(Math.floor(u * N), Math.floor(v * N), 22), f = fbm(u * 8, v * 8, 8, 24); return [cl(0.76 + 0.04 * r + 0.05 * (g - 0.5) + 0.12 * (f - 0.5)), cl(fbm(u * 5, v * 5, 5, 23)), cl(0.25 * r + 0.15 * g + 0.3 * f + 0.15)]; });
  // rock: lumpy faces split by dark cracks (ridged noise)
  const rock = tex(N, (u, v) => { const f = fbm(u * 4, v * 4, 4, 31, 5), cr = 1 - Math.abs(fbm(u * 6, v * 6, 6, 32, 4) * 2 - 1), crack = Math.pow(cr, 9); return [cl(0.5 + 0.55 * (f - 0.5) - 0.55 * crack), cl(fbm(u * 3, v * 3, 3, 33) * 1.4 - 0.35), cl(f - 0.6 * crack)]; });
  // dirt road: packed earth, pebbles, two worn tyre ruts along u
  const peb = new Float32Array(N * N); // pebbles: small soft round stones
  for (let n = 0; n < 500; n++) { const cx = hash(n, 1, 44) * N, cy = hash(n, 2, 44) * N, r = 0.6 + hash(n, 3, 44) * 1.2; for (let dy = -3; dy <= 3; dy++) for (let dx = -3; dx <= 3; dx++) { const d = Math.hypot(dx, dy) / r; if (d < 1) { const x = (Math.floor(cx) + dx + N) % N, y = (Math.floor(cy) + dy + N) % N; peb[y * N + x] = Math.max(peb[y * N + x], Math.sqrt(1 - d * d)); } } }
  const dirt = tex(N, (u, v, x, y) => { const f = fbm(u * 8, v * 8, 8, 41), p = peb[y * N + x], rut = Math.exp(-Math.pow(((v * 2) % 1) - 0.5, 2) * 60); return [cl(0.64 + 0.22 * (f - 0.5) + 0.08 * p - 0.14 * rut), cl(fbm(u * 3, v * 3, 3, 43)), cl(0.4 + 0.3 * f + 0.2 * p - 0.25 * rut)]; });
  return { grass, sand, rock, dirt };
}

// ---- the splat: R grass, G jungle, B road, A rock, from the terrain's paint, a texel a metre, softened
function makeSplat(T) {
  const { nx, nz, paint, mats } = T, w = nx, h = nz, ch = { grass: 0, leaves: 1, dirtroad: 2, stone: 3 };
  let a = new Float32Array(w * h * 4);
  for (let i = 0; i < nx; i++) for (let j = 0; j < nz; j++) { const c = ch[mats[paint ? paint[i * nz + j] : 0]]; if (c != null) a[(j * w + i) * 4 + c] = 1; }
  let b = new Float32Array(a.length);
  for (let pass = 0; pass < 3; pass++) { // three 3x3 box blurs: about a 3 m soft edge
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) for (let c = 0; c < 4; c++) {
      let s = 0, n = 0;
      for (let dy = -1; dy <= 1; dy++) { const yy = y + dy; if (yy < 0 || yy >= h) continue; for (let dx = -1; dx <= 1; dx++) { const xx = x + dx; if (xx < 0 || xx >= w) continue; s += a[(yy * w + xx) * 4 + c]; n++; } }
      b[(y * w + x) * 4 + c] = s / n;
    }
    [a, b] = [b, a];
  }
  const d = new Uint8Array(a.length);
  for (let k = 0; k < a.length; k++) d[k] = Math.round(cl(a[k]) * 255);
  const t = new THREE.DataTexture(d, w, h, THREE.RGBAFormat);
  t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearFilter; t.generateMipmaps = false; t.needsUpdate = true;
  return t;
}

const GLSL_PARS = `uniform sampler2D uSplat; uniform vec4 uSplatR; uniform sampler2D uGrass; uniform sampler2D uSand; uniform sampler2D uRock; uniform sampler2D uDirt;
uniform vec3 cGrass; uniform vec3 cDry; uniform vec3 cJungle; uniform vec3 cSand; uniform vec3 cWet; uniform vec3 cRock; uniform vec3 cRockW; uniform vec3 cRoad;
uniform float uSea; uniform float uBump; varying vec3 vBiW; varying vec3 vBiN;
uniform float uLite; uniform float uTime;
float biH = 0.5;
// caustics: the sun focused by the waves into bright wobbling threads on the sea floor (two scrolling layers of cells)
float biCellEdge( vec2 p ) {
  vec2 i = floor( p ), f = fract( p ); float d1 = 8.0, d2 = 8.0;
  for ( int y = -1; y <= 1; y++ ) for ( int x = -1; x <= 1; x++ ) {
    vec2 o = vec2( float( x ), float( y ) ), h = fract( sin( vec2( dot( i + o, vec2( 127.1, 311.7 ) ), dot( i + o, vec2( 269.5, 183.3 ) ) ) ) * 43758.5453 );
    h = 0.5 + 0.4 * sin( uTime * 0.9 + 6.2831 * h );
    float d = length( o + h - f ); if ( d < d1 ) { d2 = d1; d1 = d; } else if ( d < d2 ) d2 = d;
  }
  return 1.0 - smoothstep( 0.0, 0.1, d2 - d1 );
}
vec3 biRock( vec3 p, vec3 n ) {
  if ( uLite > 0.5 ) return texture2D( uRock, p.xz * 0.11 + p.y * 0.07 ).rgb;
  vec3 w = pow( abs( n ), vec3( 4.0 ) ); w /= ( w.x + w.y + w.z );
  return texture2D( uRock, p.zy * 0.11 ).rgb * w.x + texture2D( uRock, p.xz * 0.11 ).rgb * w.y + texture2D( uRock, p.xy * 0.11 ).rgb * w.z;
}
vec3 biBump( vec3 surf, vec3 n, float h, float k ) {
  vec3 sx = dFdx( surf ), sy = dFdy( surf ), r1 = cross( sy, n ), r2 = cross( n, sx );
  float det = dot( sx, r1 ); vec2 dh = vec2( dFdx( h ), dFdy( h ) ) * k;
  return normalize( abs( det ) * n - sign( det ) * ( dh.x * r1 + dh.y * r2 ) );
}
`;
const GLSL_MAP = `
{
  vec3 P = vBiW, N = normalize( vBiN );
  vec4 sp = texture2D( uSplat, ( P.xz - uSplatR.xy ) / uSplatR.zw );
  vec3 mac = texture2D( uGrass, P.xz * 0.0071 ).rgb; // the island's slow colour drift (a big, blurry sample of the grass detail)
  float wob = ( mac.g - 0.5 ) * 0.5; // breaks up the splat's edges
  sp = clamp( sp + vec4( wob, -wob, wob * 0.6, 0.0 ), 0.0, 1.0 );
  float steep = smoothstep( 0.5, 0.36, N.y ); // only sheer faces override the paint (a stepped slope flickers in and out of 'steep' otherwise)
  float rk = max( smoothstep( 0.15, 0.6, sp.a ), steep );
  float wet = smoothstep( uSea + 0.35, uSea - 0.1, P.y );
  // each surface: its detail texture, its colours
  vec3 g = texture2D( uGrass, P.xz * 0.31 ).rgb;
  vec3 gc = mix( cGrass, cDry, clamp( g.g * 0.4 + mac.r * 0.55 - 0.42, 0.0, 1.0 ) ) * ( 0.58 + 0.6 * g.r );
  vec3 jc = cJungle * ( 0.6 + 0.6 * g.r ) * ( 0.85 + 0.3 * mac.b );
  vec3 s = texture2D( uSand, P.xz * 0.13 ).rgb;
  vec3 sc = mix( cSand, cWet, wet ) * ( 0.78 + 0.32 * s.r ) * ( 0.94 + 0.12 * mac.g );
  vec3 d = texture2D( uDirt, P.xz * 0.12 ).rgb;
  vec3 dc = cRoad * ( 0.62 + 0.5 * d.r ) * ( 0.9 + 0.2 * mac.b );
  vec3 r = biRock( P, N );
  float strata = 0.5 + 0.5 * sin( P.y * 2.1 + mac.r * 6.0 + r.g * 1.5 ); // layers in the rock, wavering
  vec3 rc = mix( cRock, cRockW, clamp( r.g * 0.8 + ( strata - 0.5 ) * 0.7, 0.0, 1.0 ) ) * ( 0.42 + 0.95 * r.r ) * ( 0.82 + 0.3 * strata );
  rc = mix( rc, cGrass * 0.7, smoothstep( 0.6, 0.85, N.y ) * 0.35 ); // moss on the ledges
  // lay them down: sand under everything, then grass, jungle, road, rock on top
  vec3 c = sc; float h = s.b;
  float wg = clamp( sp.r * ( 1.0 - wet ), 0.0, 1.0 ); c = mix( c, gc, wg ); h = mix( h, g.b, wg );
  c = mix( c, jc, sp.g ); h = mix( h, g.b, sp.g );
  c = mix( c, dc, sp.b ); h = mix( h, d.b, sp.b );
  c = mix( c, rc, rk ); h = mix( h, r.b, rk );
  c = mix( c, c * vec3( 0.86, 0.95, 1.0 ), wet * 0.6 ); // under the shallows: a cool, damp tint
  float depth = uSea - P.y;
  if ( depth > 0.02 && uLite < 0.5 ) { // caustics, strongest a little under the surface, fading out in the deep
    float k = smoothstep( 0.02, 0.35, depth ) * ( 1.0 - smoothstep( 1.2, 3.5, depth ) ) * ( 1.0 - rk );
    vec2 cw = P.xz * 0.55 + ( mac.rg - 0.5 ) * 2.5 + vec2( sin( P.z * 0.7 + uTime * 0.6 ), cos( P.x * 0.6 + uTime * 0.5 ) ) * 0.35; // a wobble, so the cells aren't tiles
    float ca = biCellEdge( cw + vec2( uTime * 0.08, uTime * 0.05 ) ) * 0.7 + biCellEdge( cw * 0.8 - vec2( uTime * 0.05, -uTime * 0.07 ) + 3.1 ) * 0.5;
    c = mix( c, c * 0.82 + vec3( 0.08, 0.1, 0.1 ), k * 0.7 ); // the sand's grain softens under water
    c += vec3( 0.7, 0.92, 1.0 ) * ca * k * 0.42;
  }
  { // the waterline: a band of foam that laps up the beach and back, broken up so it isn't a ruler line
    float lap = sin( uTime * 0.9 + mac.r * 9.0 + P.x * 0.05 ) * 0.09 + sin( uTime * 1.7 + P.z * 0.09 ) * 0.04;
    float d = P.y - ( uSea + lap );
    float band = smoothstep( -0.16, -0.03, d ) * ( 1.0 - smoothstep( 0.0, 0.06, d ) );
    float br = smoothstep( 0.35, 0.7, s.r * 0.6 + mac.g * 0.6 + 0.15 * sin( P.x * 1.3 + P.z * 1.1 + uTime * 2.0 ) );
    float wetEdge = ( 1.0 - smoothstep( 0.06, 0.4, d ) ) * step( 0.0, d ); // a darker rim of just-wet sand above it
    c *= 1.0 - 0.18 * wetEdge * ( 1.0 - rk );
    c = mix( c, vec3( 1.0 ), band * br * ( 1.0 - rk * 0.6 ) * 0.9 );
  }
  diffuseColor.rgb *= c;
  biH = h;
}
`;

let cur = null; // the island's ground material while it's built (bilook.js flips Potato's lite mode on it)
export const biGroundLite = (on) => { if (cur) cur.userData.biGround.U.uLite.value = on ? 1 : 0; };
export const biGroundTime = (t) => { if (cur) cur.userData.biGround.U.uTime.value = t; };
export function biGroundMaterial(T, opts = {}) {
  const tx = makeTextures(), splat = makeSplat(T), C = BI_GROUND, v3 = (a) => new THREE.Vector3(...a);
  const m = new THREE.MeshLambertMaterial({ color: 0xffffff, vertexColors: true });
  const U = {
    uSplat: { value: splat }, uSplatR: { value: new THREE.Vector4(T.x0, T.z0, T.nx, T.nz) },
    uGrass: { value: tx.grass }, uSand: { value: tx.sand }, uRock: { value: tx.rock }, uDirt: { value: tx.dirt },
    cGrass: { value: v3(C.grass) }, cDry: { value: v3(C.grassDry) }, cJungle: { value: v3(C.jungle) }, cSand: { value: v3(C.sand) }, cWet: { value: v3(C.wet) },
    cRock: { value: v3(C.rock) }, cRockW: { value: v3(C.rockWarm) }, cRoad: { value: v3(C.road) },
    uSea: { value: opts.sea ?? -0.25 }, uBump: { value: C.bump }, uSnap: jankUniforms.uSnap, uLite: { value: opts.lite ? 1 : 0 }, uTime: { value: 0 },
  };
  m.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, U);
    sh.vertexShader = 'varying vec3 vBiW; varying vec3 vBiN;\nuniform vec2 uSnap;\n' + sh.vertexShader
      .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\n\tvBiW = ( modelMatrix * vec4( transformed, 1.0 ) ).xyz; vBiN = normalize( mat3( modelMatrix ) * objectNormal );')
      .replace('#include <project_vertex>', '#include <project_vertex>\n\tvec4 js = gl_Position; js.xyz /= js.w; js.xy = floor( js.xy * uSnap + 0.5 ) / uSnap; js.xyz *= js.w; gl_Position = js;'); // (the game's vertex snap: off unless the preset asks, jank.js)
    sh.fragmentShader = GLSL_PARS + sh.fragmentShader
      .replace('#include <map_fragment>', '#include <map_fragment>\n' + GLSL_MAP)
      .replace('#include <normal_fragment_maps>', '#include <normal_fragment_maps>\n\tif ( uLite < 0.5 ) normal = biBump( -vViewPosition, normal, biH, uBump );');
  };
  m.customProgramCacheKey = () => 'biground';
  m.userData.biGround = { U, tx, splat };
  cur = m;
  return m;
}
export function disposeBiGround(m) {
  if (!m || !m.userData.biGround) return;
  const { tx, splat } = m.userData.biGround;
  for (const t of Object.values(tx)) t.dispose();
  splat.dispose(); m.dispose(); if (cur === m) cur = null;
}
