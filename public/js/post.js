// Optional shaders on top of the frame (owner: "give shaders to the game with options like subsurface scattering, bloom
// fidelity etc!"). Bloom and a colour punch here; the soft skin look is softskin.js. Rules it keeps:
//   - everything off = the old path exactly (world.js draws straight to the canvas, nothing here runs)
//   - it all happens at the game's own render size, before the canvas is blown up, so Potato and Crusty stay chunky
//   - the frame is kept the way the screen would show it (not linear light), so smoke, glass and glows blend as before
//   - the HUD is HTML on top: untouched
// bloom cost doesn't grow with resolution: the glow is blurred in small fixed-height buffers (BLOOM[..].h)
import * as THREE from 'three';

const BLOOM = [null,
  { h: 180, n: 1, k: 0.4, th: 0.82 },  // low: one small soft glow
  { h: 270, n: 2, k: 0.42, th: 0.8 },  // medium: a wider second layer
  { h: 360, n: 3, k: 0.46, th: 0.78 }, // high: three layers, the neon bleeds
];
const P = { bloom: 0, punch: false, rt: null, lv: [], w: 0, h: 0, bh: 0, cam: new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1), mesh: null, mats: null, size: new THREE.Vector2() };
export const postStats = { passes: 0 };
// ---- the way out. this pass has only ever been seen on software GL, and Mid / Too HD run it by default: if anything
// about it goes wrong on a real GPU (a throw, a buffer the GPU won't complete, a lost context, a black result while
// the scene isn't black) it switches itself OFF for the session and the game draws the plain way, as it always did
const SAFE = { dead: false, why: '', checks: 0, ok: 0, black: 0, onFail: null, test: '' };
function fail(why) {
  if (SAFE.dead) return;
  SAFE.dead = true; SAFE.why = why;
  console.warn('[gfx] shaders switched off for this session:', why);
  try { if (SAFE.onFail) SAFE.onFail(why); } catch (e) { /* the toast must never be the problem */ }
}
export function setPostFail(fn) { SAFE.onFail = fn; }
export function postTest(kind) { SAFE.test = kind; SAFE.checks = 0; } // tests: force a failure ('throw', 'fb', 'lost', 'black', 'blackin')
const CHECKS = 4, PTS = [[0.5, 0.5], [0.2, 0.25], [0.8, 0.25], [0.2, 0.8], [0.8, 0.8], [0.5, 0.92], [0.5, 0.1], [0.35, 0.6], [0.65, 0.4]];
const px = new Uint8Array(4);
// a handful of pixels of the first few finished frames: black on screen while the scene in the buffer isn't = broken
function sanity(r) {
  const gl = r.getContext(), w = P.w, h = P.h;
  let outLit = 0, inLit = 0;
  for (const [u, v] of PTS) {
    const x = Math.min(w - 1, Math.floor(u * w)), y = Math.min(h - 1, Math.floor(v * h));
    gl.readPixels(x, y, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px); if (px[0] + px[1] + px[2] > 0) outLit++;
    r.readRenderTargetPixels(P.rt, x, y, 1, 1, px); if (px[0] + px[1] + px[2] > 0) inLit++;
  }
  SAFE.checks++;
  if (!outLit && inLit) { fail('the finished frame came out black'); return false; }
  if (!inLit) { if (++SAFE.black >= 3) { fail('the frame buffer stayed black'); return false; } } else { SAFE.black = 0; SAFE.ok++; }
  return true;
}

const VERT = 'varying vec2 vUv;\nvoid main() { vUv = uv; gl_Position = vec4( position.xy, 0.0, 1.0 ); }';
const mat = (frag, uniforms) => new THREE.ShaderMaterial({ vertexShader: VERT, fragmentShader: frag, uniforms, depthTest: false, depthWrite: false, toneMapped: false });
function build() {
  const tri = new THREE.BufferGeometry(); // one big triangle over the screen
  tri.setAttribute('position', new THREE.Float32BufferAttribute([-1, -1, 0, 3, -1, 0, -1, 3, 0], 3));
  tri.setAttribute('uv', new THREE.Float32BufferAttribute([0, 0, 2, 0, 0, 2], 2));
  P.mesh = new THREE.Mesh(tri, null); P.mesh.frustumCulled = false;
  P.mats = {
    // what glows: the bright and the loud (neon, lava, muzzle flashes, the sun), shrunk into the first small buffer
    bright: mat(`uniform sampler2D tSrc; uniform vec2 uPx; uniform float uTh; varying vec2 vUv;
void main() {
  vec3 c = vec3( 0.0 );
  for ( int i = 0; i < 4; i ++ ) {
    vec2 o = vec2( i == 0 || i == 3 ? -1.0 : 1.0, i < 2 ? -1.0 : 1.0 ) * uPx;
    vec3 s = texture2D( tSrc, vUv + o ).rgb;
    float hi = max( s.r, max( s.g, s.b ) ), lo = min( s.r, min( s.g, s.b ) );
    float sat = hi > 0.001 ? ( hi - lo ) / hi : 0.0;
    c += s * smoothstep( uTh, 1.0, hi + sat * 0.1 ) * ( 0.7 + 0.5 * sat ); // pale bright sand glows less than a pink sign
  }
  gl_FragColor = vec4( c * 0.25, 1.0 );
}`, { tSrc: { value: null }, uPx: { value: new THREE.Vector2() }, uTh: { value: 0.8 } }),
    blur: mat(`uniform sampler2D tSrc; uniform vec2 uDir; varying vec2 vUv;
void main() {
  vec3 c = texture2D( tSrc, vUv ).rgb * 0.227027;
  c += ( texture2D( tSrc, vUv + uDir * 1.384615 ).rgb + texture2D( tSrc, vUv - uDir * 1.384615 ).rgb ) * 0.316216;
  c += ( texture2D( tSrc, vUv + uDir * 3.230769 ).rgb + texture2D( tSrc, vUv - uDir * 3.230769 ).rgb ) * 0.070270;
  gl_FragColor = vec4( c, 1.0 );
}`, { tSrc: { value: null }, uDir: { value: new THREE.Vector2() } }),
    final: mat(`uniform sampler2D tScene; uniform sampler2D tB0; uniform sampler2D tB1; uniform sampler2D tB2; uniform vec3 uW; uniform float uPunch; uniform float uKill; uniform vec4 uGrade; uniform float uAA; uniform vec2 uPx; uniform vec2 uFilm; uniform sampler2D tAO; uniform sampler2D tDepth; uniform float uAOk; uniform float uAODbg; uniform sampler2D tSSR; uniform float uSSRk; varying vec2 vUv;
// smoothing jaggies (Mid and up): where the brightness steps across a pixel, blend toward the neighbours along the edge
vec3 aaScene( vec2 uv ) {
  vec3 m = texture2D( tScene, uv ).rgb;
  if ( uAA < 0.5 ) return m;
  vec3 n = texture2D( tScene, uv + vec2( 0.0, uPx.y ) ).rgb, s = texture2D( tScene, uv - vec2( 0.0, uPx.y ) ).rgb;
  vec3 e = texture2D( tScene, uv + vec2( uPx.x, 0.0 ) ).rgb, w = texture2D( tScene, uv - vec2( uPx.x, 0.0 ) ).rgb;
  vec3 W = vec3( 0.299, 0.587, 0.114 );
  float lm = dot( m, W ), ln = dot( n, W ), ls = dot( s, W ), le = dot( e, W ), lw = dot( w, W );
  float range = max( max( max( ln, ls ), max( le, lw ) ), lm ) - min( min( min( ln, ls ), min( le, lw ) ), lm );
  if ( range < max( 0.06, lm * 0.15 ) ) return m; // flat: leave it sharp
  float hz = abs( ln + ls - 2.0 * lm ), vt = abs( le + lw - 2.0 * lm );
  vec3 along = hz > vt ? ( n + s ) * 0.5 : ( e + w ) * 0.5; // a horizontal edge blends up / down, a vertical one left / right
  return mix( m, along, clamp( range * 1.6, 0.0, 0.5 ) );
}
vec3 acesFit( vec3 x ) { return clamp( ( x * ( 2.51 * x + 0.03 ) ) / ( x * ( 2.43 * x + 0.59 ) + 0.14 ), 0.0, 1.0 ); }
void main() {
  vec3 c = aaScene( vUv );
  if ( uAOk > 0.0 && texture2D( tDepth, vUv ).x > 0.99999 ) c *= mix( 1.0, texture2D( tAO, vUv ).r, uAOk ); // contact shadows (the world only: where the gun was drawn the depth isn't the cleared 1.0)
  if ( uSSRk > 0.0 && texture2D( tDepth, vUv ).x > 0.99999 ) { vec4 m = texture2D( tSSR, vUv ); c = mix( c, m.rgb, m.a * uSSRk ); } // floor mirrors (the world only, not the gun)
  vec3 b = texture2D( tB0, vUv ).rgb * uW.x;
  if ( uW.y > 0.0 ) b += texture2D( tB1, vUv ).rgb * uW.y;
  if ( uW.z > 0.0 ) b += texture2D( tB2, vUv ).rgb * uW.z;
  c = 1.0 - ( 1.0 - c ) * ( 1.0 - min( b, vec3( 1.0 ) ) ); // screen, not add: bright things glow without going flat white
  if ( uPunch > 0.0 ) {
    float l = dot( c, vec3( 0.299, 0.587, 0.114 ) );
    vec3 p = mix( vec3( l ), c, 1.16 ); // louder colours
    p = mix( p, p * p * ( 3.0 - 2.0 * p ), 0.22 ); // a bit more contrast
    vec2 v = vUv - 0.5;
    p *= 1.0 - 0.5 * pow( dot( v, v ) * 1.9, 1.6 ); // dark comic-panel corners
    c = mix( c, clamp( p, 0.0, 1.0 ), uPunch );
  }
  if ( uFilm.x > 0.0 ) { // a filmic curve (soft shoulder: bright things don't clip flat) and vibrance (dull colours lifted more than loud ones)
    c = mix( c, acesFit( c * 1.25 ), uFilm.x );
    float l = dot( c, vec3( 0.299, 0.587, 0.114 ) ), sat = max( c.r, max( c.g, c.b ) ) - min( c.r, min( c.g, c.b ) );
    c = clamp( mix( vec3( l ), c, 1.0 + uFilm.y * ( 1.0 - sat ) ), 0.0, 1.0 );
  }
  if ( uGrade.w > 0.0 ) { // one map's own colour grade (setGrade: Battle Island's bilook.js): saturation, warmth, contrast
    float l = dot( c, vec3( 0.299, 0.587, 0.114 ) );
    vec3 g = mix( vec3( l ), c, uGrade.x ) + vec3( uGrade.y, uGrade.y * 0.35, -uGrade.y * 0.6 );
    g = ( g - 0.5 ) * uGrade.z + 0.5;
    c = clamp( mix( c, g, uGrade.w ), 0.0, 1.0 );
  }
  if ( uAODbg > 1.5 ) c = vec3( texture2D( tSSR, vUv ).a, 1.0 - texture2D( tScene, vUv ).a, 0.0 ); // (tests: red the floor mirror's strength, green the floors marked shiny)
  else if ( uAODbg > 0.5 ) c = texture2D( tAO, vUv ).rgb; // (/gfx ao: the contact shadows on their own)
  gl_FragColor = vec4( c * ( 1.0 - uKill ), 1.0 ); // (uKill: tests only, forces a black frame)
}`, { uKill: { value: 0 }, tScene: { value: null }, tB0: { value: null }, tB1: { value: null }, tB2: { value: null }, uW: { value: new THREE.Vector3() }, uPunch: { value: 0 }, uGrade: { value: new THREE.Vector4() }, uAA: { value: 0 }, uPx: { value: new THREE.Vector2() }, uFilm: { value: new THREE.Vector2() }, tAO: { value: null }, tDepth: { value: null }, uAOk: { value: 0 }, uAODbg: { value: 0 }, tSSR: { value: null }, uSSRk: { value: 0 } }),
    // contact shadows (screen-space ambient occlusion): from the depth of the world as drawn, how much of the half-sphere
    // over each point is shut in by things right next to it: corners, where a crate meets the floor, under a car
    ao: mat(`uniform sampler2D tDepth; uniform float uNear; uniform float uFar; uniform vec2 uTan; uniform float uR; uniform vec2 uPx; varying vec2 vUv;
float vz( vec2 uv ) { float d = texture2D( tDepth, uv ).x; return ( uNear * uFar ) / ( ( uFar - uNear ) * d - uFar ); } // (negative: view space looks down -z)
vec3 vp( vec2 uv ) { float z = vz( uv ); return vec3( ( uv * 2.0 - 1.0 ) * uTan * -z, z ); }
void main() {
  float d0 = texture2D( tDepth, vUv ).x;
  if ( d0 > 0.99999 ) { gl_FragColor = vec4( 1.0 ); return; } // the sky
  vec3 p = vp( vUv );
  vec3 r1 = vp( vUv + vec2( uPx.x, 0.0 ) ) - p, l1 = p - vp( vUv - vec2( uPx.x, 0.0 ) ), u1 = vp( vUv + vec2( 0.0, uPx.y ) ) - p, d1 = p - vp( vUv - vec2( 0.0, uPx.y ) );
  vec3 n = normalize( cross( abs( r1.z ) < abs( l1.z ) ? r1 : l1, abs( u1.z ) < abs( d1.z ) ? u1 : d1 ) ); // (the smoother side each way: no false edges at silhouettes)
  float r = uR / ( -p.z * 2.0 * uTan.y ), occ = 0.0, a0 = fract( sin( dot( gl_FragCoord.xy, vec2( 12.9898, 78.233 ) ) ) * 43758.5453 ) * 6.2832;
  for ( int i = 0; i < 12; i++ ) {
    float fi = float( i ), a = a0 + fi * 2.39996, t = ( fi + 0.5 ) / 12.0;
    vec2 uv = vUv + vec2( cos( a ) * uTan.y / uTan.x, sin( a ) ) * r * t;
    if ( uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0 ) continue;
    vec3 v = vp( uv ) - p; float l = length( v );
    occ += max( 0.0, dot( n, v / max( l, 1e-4 ) ) - 0.3 ) * ( 1.0 - smoothstep( 0.0, uR, l ) ) * step( 0.02 + 0.002 * -p.z, l ); // (a flat floor doesn't shade itself)
  }
  occ *= 1.0 - smoothstep( 25.0, 60.0, -p.z ); // close up only: far off the depth is too coarse to trust, and contacts are too small to see
  gl_FragColor = vec4( vec3( pow( clamp( 1.0 - occ / 12.0 * 5.5, 0.0, 1.0 ), 1.3 ) ), 1.0 );
}`, { tDepth: { value: null }, uNear: { value: 0.1 }, uFar: { value: 1500 }, uTan: { value: new THREE.Vector2(1, 1) }, uR: { value: 1.2 }, uPx: { value: new THREE.Vector2() } }),
    // floor mirrors (screen-space reflections): from each shiny floor pixel (the map's materials mark them in the frame's
    // alpha, reflect.js), a ray bounces off the floor and steps through the depth of the world as drawn until it goes
    // behind something: that's what the floor shows there. it can only mirror what's on screen, so it fades out toward
    // the screen's edges and with distance, and where it finds nothing the floor keeps the 360-snapshot reflection
    ssr: mat(`uniform sampler2D tScene; uniform sampler2D tDepth; uniform float uNear; uniform float uFar; uniform vec2 uTan; uniform vec2 uPx; uniform mat4 uProj; varying vec2 vUv;
float vz( vec2 uv ) { float d = texture2D( tDepth, uv ).x; return ( uNear * uFar ) / ( ( uFar - uNear ) * d - uFar ); }
vec3 vp( vec2 uv ) { float z = vz( uv ); return vec3( ( uv * 2.0 - 1.0 ) * uTan * -z, z ); }
vec2 sp( vec3 q ) { vec4 c = uProj * vec4( q, 1.0 ); return c.xy / c.w * 0.5 + 0.5; }
void main() {
  float mk = 1.0 - texture2D( tScene, vUv ).a;
  if ( mk < 0.02 || texture2D( tDepth, vUv ).x > 0.99999 ) { gl_FragColor = vec4( 0.0 ); return; }
  vec3 p = vp( vUv );
  vec3 r1 = vp( vUv + vec2( uPx.x, 0.0 ) ) - p, l1 = p - vp( vUv - vec2( uPx.x, 0.0 ) ), u1 = vp( vUv + vec2( 0.0, uPx.y ) ) - p, d1 = p - vp( vUv - vec2( 0.0, uPx.y ) );
  vec3 n = normalize( cross( abs( r1.z ) < abs( l1.z ) ? r1 : l1, abs( u1.z ) < abs( d1.z ) ? u1 : d1 ) );
  vec3 rd = reflect( normalize( p ), n );
  if ( rd.z > 0.6 ) { gl_FragColor = vec4( 0.0 ); return; } // (bouncing back at the camera: nothing on screen to show)
  float t = 0.3 + 0.004 * -p.z, jit = fract( sin( dot( gl_FragCoord.xy, vec2( 12.9898, 78.233 ) ) ) * 43758.5453 );
  vec3 q = p; vec2 uv = vUv; float hit = 0.0, prev = 0.0;
  for ( int i = 0; i < 28; i++ ) {
    float st = t * ( 1.0 + jit * 0.5 ); q = p + rd * ( prev + st ); uv = sp( q );
    if ( uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0 || q.z > -uNear ) break;
    float sz = vz( uv ), dz = sz - q.z;
    if ( dz > 0.0 && dz < 0.6 + st * 1.5 ) { // went behind a surface (not far behind: that's a different thing in front)
      float a = prev, b = prev + st;
      for ( int j = 0; j < 5; j++ ) { float m = ( a + b ) * 0.5; vec3 qm = p + rd * m; if ( vz( sp( qm ) ) - qm.z > 0.0 ) b = m; else a = m; }
      uv = sp( p + rd * b ); hit = 1.0 - smoothstep( 0.55, 1.0, float( i ) / 28.0 ); break;
    }
    prev += st; t *= 1.22;
  }
  if ( hit <= 0.0 || texture2D( tDepth, uv ).x > 0.99999 ) { gl_FragColor = vec4( 0.0 ); return; } // (the sky: the 360 snapshot shows it already)
  vec2 e = smoothstep( 0.0, 0.12, uv ) * smoothstep( 0.0, 0.12, 1.0 - uv );
  float f = mk * hit * e.x * e.y * ( 1.0 - smoothstep( 40.0, 90.0, -p.z ) );
  gl_FragColor = vec4( texture2D( tScene, uv ).rgb, clamp( f, 0.0, 1.0 ) );
}`, { tScene: { value: null }, tDepth: { value: null }, uNear: { value: 0.1 }, uFar: { value: 1500 }, uTan: { value: new THREE.Vector2(1, 1) }, uPx: { value: new THREE.Vector2() }, uProj: { value: new THREE.Matrix4() } }),
  };
}
const target = (w, h, depth, filter) => {
  const t = new THREE.WebGLRenderTarget(w, h, { depthBuffer: depth, minFilter: filter, magFilter: filter, generateMipmaps: false });
  // three only writes screen-ready (sRGB) colour into a target that says it's an XR one (0.170). that is what we want:
  // the frame in here is exactly what the canvas would have got, so transparent things blend the same as with shaders off
  t.isXRRenderTarget = true; t.texture.colorSpace = THREE.SRGBColorSpace;
  return t;
};
function fit(r) {
  r.getDrawingBufferSize(P.size);
  const w = P.size.x, h = P.size.y, B = BLOOM[P.bloom], bh = B ? Math.min(B.h, Math.max(8, h >> 1)) : 0;
  if (P.rt && P.w === w && P.h === h && P.bh === bh && P.lv.length === (B ? B.n : 0) && !!P.rt.depthTexture === !!(P.ao || P.ssr) && !!P.ssrA === !!P.ssr) return;
  if (P.aoA) { P.aoA.dispose(); P.aoB.dispose(); P.aoA = P.aoB = null; }
  if (P.ssrA) { P.ssrA.dispose(); P.ssrA = null; }
  if (P.rt) P.rt.dispose();
  for (const l of P.lv) { l.a.dispose(); l.b.dispose(); }
  P.lv = []; P.w = w; P.h = h; P.bh = bh;
  P.rt = target(w, h, true, THREE.NearestFilter);
  if (P.ao || P.ssr) { P.rt.depthTexture = new THREE.DepthTexture(w, h); P.rt.depthTexture.minFilter = P.rt.depthTexture.magFilter = THREE.NearestFilter; } // (contact shadows and floor mirrors read the world's depth)
  if (P.ssr) { P.ssrW = Math.max(8, w >> 1); P.ssrH = Math.max(8, h >> 1); P.ssrA = new THREE.WebGLRenderTarget(P.ssrW, P.ssrH, { depthBuffer: false, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, generateMipmaps: false }); } // (linear: it's colour already decoded)
  if (P.ao) { // contact shadows need two half-size buffers to work in
    const aw = Math.max(8, w >> 1), ah = Math.max(8, h >> 1); P.aoA = target(aw, ah, false, THREE.LinearFilter); P.aoB = target(aw, ah, false, THREE.LinearFilter); P.aoW = aw; P.aoH = ah;
  }
  for (let i = 0; B && i < B.n; i++) {
    const lh = Math.max(4, bh >> i), lw = Math.max(4, Math.round((lh * w) / h));
    P.lv.push({ w: lw, h: lh, a: target(lw, lh, false, THREE.LinearFilter), b: target(lw, lh, false, THREE.LinearFilter) });
  }
}
function pass(r, m, to) { P.mesh.material = m; r.setRenderTarget(to); r.render(P.mesh, P.cam); postStats.passes++; }

// bloom: 0 off, 1 low, 2 medium, 3 high. punch: louder colours + dark corners
export function setPost(bloom, punch) {
  P.bloom = BLOOM[bloom] ? bloom : 0; P.punch = !!punch;
  if (!wanted() && P.rt) { P.rt.dispose(); P.rt = null; for (const l of P.lv) { l.a.dispose(); l.b.dispose(); } P.lv = []; } // off: give the memory back
}
// a map's own colour grade, [saturation, warmth, contrast, amount] or null (bilook.js). only while shaders are on
export function setGrade(g, film) { P.grade = g ? g.slice() : null; P.film = film ? film.slice() : null; } // film: [filmic curve 0..1, vibrance]
export function setPostAA(on) { P.aa = !!on; }
export function postAODebug(on) { P.aoDbg = on === 2 ? 2 : !!on; } // (tests, /gfx: show the contact-shadow buffer)
export const postSSROn = () => !!P.ssr && !P.ssrDead;
export function setPostSSR(on) { P.ssr = !!on && !P.ssrDead; } // floor mirrors (fxsettings.js: the ray-traced look, Too HD)
export function setPostAO(on) { P.ao = !!on && !P.aoDead; } // contact shadows (fxsettings.js: the ray-traced look) // world.js: Mid and Too HD smooth their edges (Potato and Crusty stay crunchy)
export const postOn = () => !SAFE.dead && (P.bloom > 0 || P.punch);
const wanted = () => P.bloom > 0 || P.punch;
export const postInfo = () => ({ ao: !!P.ao, aoDead: !!P.aoDead, ssr: !!P.ssr, ssrDead: !!P.ssrDead, bloom: P.bloom, punch: P.punch, size: [P.w, P.h], glow: P.lv.map((l) => [l.w, l.h]), on: postOn(), dead: SAFE.dead, why: SAFE.why, checks: SAFE.checks, ok: SAFE.ok });

// world.js renderFrame: draw the frame into our buffer instead of the canvas (false = shaders off, draw as always)
export function postBegin(r) {
  if (!postOn()) return false;
  try {
    const gl = r.getContext();
    if (gl.isContextLost() || SAFE.test === 'lost') { fail('the graphics context was lost'); return false; }
    if (!P.mesh) build();
    const fresh = !P.rt; fit(r);
    r.setRenderTarget(P.rt);
    if (fresh || SAFE.checks < CHECKS) { // (new buffers: ask the GPU once whether it will draw into them)
      const st = gl.checkFramebufferStatus(gl.FRAMEBUFFER);
      if (st !== gl.FRAMEBUFFER_COMPLETE || SAFE.test === 'fb') { r.setRenderTarget(null); fail('the frame buffer is not complete (' + st + ')'); return false; }
    }
    return true;
  } catch (e) {
    try { r.setRenderTarget(null); } catch (e2) { /* nothing left to try */ }
    fail('begin threw: ' + (e && e.message)); return false;
  }
}
// world.js, between the world and your gun: the contact shadows, from the world's depth alone (the gun is drawn after,
// so it never gets them). if this ever throws, contact shadows switch off and the rest of the shaders carry on
export function postMid(r, cam) {
  if (P.ssr) ssrPass(r, cam);
  if (!P.ao || !P.aoA || !P.rt || !P.rt.depthTexture) return;
  try {
    const M = P.mats, A = M.ao.uniforms;
    A.tDepth.value = P.rt.depthTexture; A.uNear.value = cam.near; A.uFar.value = cam.far;
    const th = Math.tan((cam.fov * Math.PI) / 360); A.uTan.value.set(th * cam.aspect, th); A.uPx.value.set(1 / P.w, 1 / P.h); A.uR.value = 2.4;
    pass(r, M.ao, P.aoA);
    M.blur.uniforms.tSrc.value = P.aoA.texture; M.blur.uniforms.uDir.value.set(1 / P.aoW, 0); pass(r, M.blur, P.aoB);
    M.blur.uniforms.tSrc.value = P.aoB.texture; M.blur.uniforms.uDir.value.set(0, 1 / P.aoH); pass(r, M.blur, P.aoA);
    P.aoDone = true;
  } catch (e) { P.aoDead = true; P.ao = false; console.warn('[gfx] contact shadows off:', e && e.message); }
  r.setRenderTarget(P.rt);
}
// floor mirrors: before the gun is drawn (it never shows in the floor), from the world as drawn so far
function ssrPass(r, cam) {
  if (!P.ssrA || !P.rt || !P.rt.depthTexture) return;
  try {
    const S = P.mats.ssr.uniforms;
    S.tScene.value = P.rt.texture; S.tDepth.value = P.rt.depthTexture; S.uNear.value = cam.near; S.uFar.value = cam.far;
    const th = Math.tan((cam.fov * Math.PI) / 360); S.uTan.value.set(th * cam.aspect, th); S.uPx.value.set(1 / P.w, 1 / P.h); S.uProj.value.copy(cam.projectionMatrix);
    pass(r, P.mats.ssr, P.ssrA); P.ssrDone = true;
  } catch (e) { P.ssrDead = true; P.ssr = false; console.warn('[gfx] floor mirrors off:', e && e.message); }
  r.setRenderTarget(P.rt);
}
// ...then glow + grade it onto the canvas. false = it failed: the caller draws this frame again the plain way
export function postEnd(r) {
  try {
    if (SAFE.test === 'throw') throw new Error('forced');
    compose(r);
    if (SAFE.checks < CHECKS && !sanity(r)) return false;
    return true;
  } catch (e) {
    try { r.setRenderTarget(null); } catch (e2) { /* nothing left to try */ }
    fail('end threw: ' + (e && e.message)); return false;
  }
}
function compose(r) {
  const M = P.mats, B = BLOOM[P.bloom], L = P.lv;
  postStats.passes = 0;
  if (B) {
    M.bright.uniforms.tSrc.value = P.rt.texture; M.bright.uniforms.uTh.value = B.th;
    M.bright.uniforms.uPx.value.set(0.5 / L[0].w, 0.5 / L[0].h); // four taps spread over the source pixels one small pixel covers
    pass(r, M.bright, L[0].a);
    for (let i = 0; i < L.length; i++) {
      const l = L[i], src = i ? L[i - 1].a : l.a;
      M.blur.uniforms.tSrc.value = src.texture; M.blur.uniforms.uDir.value.set(1 / l.w, 0); pass(r, M.blur, l.b); // (a smaller layer blurs the one above it down into itself)
      M.blur.uniforms.tSrc.value = l.b.texture; M.blur.uniforms.uDir.value.set(0, 1 / l.h); pass(r, M.blur, l.a);
    }
  }
  const F = M.final.uniforms;
  F.tScene.value = P.rt.texture;
  F.tB0.value = L[0] ? L[0].a.texture : null; F.tB1.value = L[1] ? L[1].a.texture : null; F.tB2.value = L[2] ? L[2].a.texture : null;
  const k = B ? B.k : 0;
  F.uW.value.set(L[0] ? k * (L[1] ? 0.6 : 1) : 0, L[1] ? k * 0.8 : 0, L[2] ? k : 0); // more layers: a wide soft halo, not a brighter middle (signs stay readable)
  F.uPunch.value = P.punch ? 1 : 0; if (P.grade) F.uGrade.value.fromArray(P.grade); else F.uGrade.value.set(1, 0, 1, 0);
  F.uAOk.value = P.ao && P.aoDone ? 1 : 0; F.tAO.value = P.aoA ? P.aoA.texture : null; F.tDepth.value = P.rt.depthTexture || null; F.uAODbg.value = P.aoDbg === 2 ? 2 : P.aoDbg && P.aoDone ? 1 : 0; P.aoDone = false;
  F.uSSRk.value = P.ssr && P.ssrDone ? 1 : 0; F.tSSR.value = P.ssrA ? P.ssrA.texture : null; P.ssrDone = false;
  F.uAA.value = P.aa ? 1 : 0; F.uPx.value.set(1 / P.w, 1 / P.h); if (P.film) F.uFilm.value.fromArray(P.film); else F.uFilm.value.set(0, 0); F.uKill.value = SAFE.test === 'black' ? 1 : 0;
  if (SAFE.test === 'blackin') { r.setRenderTarget(P.rt); r.setClearColor(0x000000, 1); r.clear(); } // (tests: an empty frame buffer)
  pass(r, M.final, null);
}
