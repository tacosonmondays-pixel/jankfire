// Drawn effects instead of code squares (owner: "actual water ripples, smoke etc that arent like code ... draw your own
// sprites like the standard 3 layer ones"). A flipbook is one of our own sprite sheets (tools/sprites/make.cjs draws
// them: shading in R, the ink outline in G, the shape in A) played on quads: facing you (smoke, splashes) or lying
// flat (ripples). The shader tints the shading, lights it with the map's light and inks the outline. All the quads of
// one sheet are a single instanced draw. Off on Potato (the old square particles stay) and by the Settings switch.
import * as THREE from 'three';
import { G } from './ctx.js';

const VS = `attribute vec4 aPS; attribute vec4 aAR; attribute vec3 aCol;
uniform float uFlat; varying vec2 vUv; varying vec3 vCol; varying float vAge; varying float vA;
#include <fog_pars_vertex>
void main() {
  vUv = uv; vCol = aCol; vAge = aAR.x; vA = aAR.z;
  float c = cos( aAR.y ), s = sin( aAR.y );
  vec2 q = vec2( position.x * c - position.y * s, position.x * s + position.y * c ) * aPS.w;
  vec4 mvPosition;
  if ( uFlat > 0.5 ) mvPosition = viewMatrix * vec4( aPS.x + q.x, aPS.y, aPS.z + q.y, 1.0 ); // lying on the water
  else { mvPosition = viewMatrix * vec4( aPS.xyz, 1.0 ); mvPosition.xy += q + vec2( 0.0, uFlat < -0.5 ? aPS.w * 0.43 : 0.0 ); } // facing you (-1: standing on its bottom edge)
  gl_Position = projectionMatrix * mvPosition;
  #include <fog_vertex>
}`;
const FS = `uniform sampler2D uMap; uniform float uN; uniform vec3 uLit; uniform vec3 uInk; uniform float uInkK; uniform float uSoft; uniform float uRgb;
varying vec2 vUv; varying vec3 vCol; varying float vAge; varying float vA;
#include <fog_pars_fragment>
vec4 frame( float f ) { return texture2D( uMap, ( vec2( mod( f, uN ), uN - 1.0 - floor( f / uN ) ) + vUv ) / uN ); }
void main() {
  float f = clamp( vAge, 0.0, 0.999 ) * uN * uN;
  vec4 t = frame( floor( f ) ); // (no blending between frames: it should tick like a drawn animation)
  float a = vA;
  if ( uSoft > 0.5 ) { t = mix( t, frame( min( floor( f ) + 1.0, uN * uN - 1.0 ) ), fract( f ) ); a *= t.a; if ( a < 0.01 ) discard; } // the soft kind: frames melt into each other, edges fade
  else if ( t.a < 0.5 || vA < 0.02 ) discard;
  if ( uRgb > 0.5 ) { gl_FragColor = vec4( t.rgb * vCol * vA, t.a * vA ); return; } // a colour sheet that glows by itself (fire): premultiplied, unlit, no fog
  vec3 c = vCol * ( 0.42 + 0.66 * t.r ) * uLit;
  c = mix( c, uInk * uLit, t.g * uInkK );
  gl_FragColor = vec4( c, a );
  #include <colorspace_fragment>
  #include <fog_fragment>
}`;

const loader = new THREE.TextureLoader();
const books = [];
// flat: 1 = lying down, 0 = facing you, -1 = facing you and standing on its bottom edge
export class Flipbook {
  constructor(file, n, max, { flat = 0, ink = 0x1a1022, inkK = 0.85, sort = false, order = 4, soft = false, rgb = false } = {}) {
    this.max = max; this.n = 0; this.sort = sort; this.ready = false; this.failed = false;
    this.L = []; // live: { x, y, z, vx, vy, vz, s0, s1, rot, spin, t, life, a, r, g, b, drag }
    const tex = loader.load('/sprites/' + file, () => { this.ready = true; }, undefined, () => { this.failed = true; });
    tex.magFilter = soft ? THREE.LinearFilter : THREE.NearestFilter; tex.minFilter = THREE.LinearFilter; tex.generateMipmaps = false; tex.colorSpace = THREE.NoColorSpace;
    const geo = new THREE.PlaneGeometry(1, 1);
    this.aPS = new THREE.InstancedBufferAttribute(new Float32Array(max * 4), 4).setUsage(THREE.DynamicDrawUsage);
    this.aAR = new THREE.InstancedBufferAttribute(new Float32Array(max * 4), 4).setUsage(THREE.DynamicDrawUsage);
    this.aCol = new THREE.InstancedBufferAttribute(new Float32Array(max * 3), 3).setUsage(THREE.DynamicDrawUsage);
    geo.setAttribute('aPS', this.aPS); geo.setAttribute('aAR', this.aAR); geo.setAttribute('aCol', this.aCol);
    this.U = { ...THREE.UniformsUtils.clone(THREE.UniformsLib.fog), uMap: { value: tex }, uN: { value: n }, uFlat: { value: flat }, uLit: LIT, uInk: { value: new THREE.Color(ink) }, uInkK: { value: inkK }, uSoft: { value: soft ? 1 : 0 }, uRgb: { value: rgb ? 1 : 0 } };
    const mat = new THREE.ShaderMaterial({ uniforms: this.U, vertexShader: VS, fragmentShader: FS, fog: true, transparent: true, depthWrite: false, side: THREE.DoubleSide,
      ...(rgb ? { blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneMinusSrcAlphaFactor } : {}),
      polygonOffset: flat > 0, polygonOffsetFactor: -2, polygonOffsetUnits: -4 });
    this.mesh = new THREE.InstancedMesh(geo, mat, max);
    this.mesh.count = 0; this.mesh.frustumCulled = false; this.mesh.renderOrder = order; this.mesh.userData.noShadow = true;
    books.push(this);
  }
  // o: { p: [x, y, z], v: [vx, vy, vz], s0, s1 (metres across, start -> end), life, a (opacity), col (hex), rot, spin, drag }
  spawn(o) {
    if (this.L.length >= this.max) this.L.shift();
    const c = _c.setHex(o.col ?? 0xffffff), v = o.v || ZERO;
    this.L.push({ x: o.p[0], y: o.p[1], z: o.p[2], vx: v[0], vy: v[1], vz: v[2], s0: o.s0, s1: o.s1 ?? o.s0, rot: o.rot ?? 0, spin: o.spin ?? 0, t: 0, life: o.life, a: o.a ?? 1, r: c.r, g: c.g, b: c.b, drag: o.drag ?? 0, ride: o.ride || null, frame: o.frame ?? -1, loop: o.loop ?? 0 });
  }
  update(dt, cam) {
    const L = this.L;
    for (let i = L.length - 1; i >= 0; i--) {
      const p = L[i];
      p.t += dt;
      if (p.t >= p.life) { L.splice(i, 1); continue; }
      const dr = Math.max(0, 1 - p.drag * dt);
      p.vx *= dr; p.vy *= dr; p.vz *= dr;
      p.x += p.vx * dt; p.y += p.vy * dt; p.z += p.vz * dt; p.rot += p.spin * dt;
      if (p.ride) p.y = p.ride(p.x, p.z); // ripples ride the waves
    }
    if (!this.mesh.parent && G.scene) G.scene.add(this.mesh);
    if (!this.ready) { this.mesh.count = 0; return; }
    if (this.sort && cam) { const cx = cam.position.x, cy = cam.position.y, cz = cam.position.z; for (const p of L) p.d = (p.x - cx) ** 2 + (p.y - cy) ** 2 + (p.z - cz) ** 2; L.sort((a, b) => b.d - a.d); } // far ones first
    const PS = this.aPS.array, AR = this.aAR.array, C = this.aCol.array;
    for (let i = 0; i < L.length; i++) {
      const p = L[i], k = p.t / p.life;
      PS[i * 4] = p.x; PS[i * 4 + 1] = p.y; PS[i * 4 + 2] = p.z; PS[i * 4 + 3] = p.s0 + (p.s1 - p.s0) * Math.sqrt(k);
      AR[i * 4] = p.frame >= 0 ? p.frame : p.loop ? (p.t * p.loop) % 1 : k; AR[i * 4 + 1] = p.rot; // (loop: plays round and round, that many times a second)
      AR[i * 4 + 2] = p.a * Math.min(1, (1 - k) * 4) * (p.frame >= 0 ? Math.min(1, k * 8) : 1); // (the last quarter fades; a still picture fades in too)
      C[i * 3] = p.r; C[i * 3 + 1] = p.g; C[i * 3 + 2] = p.b;
    }
    this.mesh.count = L.length;
    if (L.length) { this.aPS.needsUpdate = true; this.aAR.needsUpdate = true; this.aCol.needsUpdate = true; }
  }
  clear() { this.L.length = 0; this.mesh.count = 0; }
}
const _c = new THREE.Color(), ZERO = [0, 0, 0];
const LIT = { value: new THREE.Color(1, 1, 1) }; // how bright the map is (a dark map gets dark smoke)

// ---- the sheets in use (made on first use: Potato never downloads them)
let FB = null;
function get() {
  if (!FB) FB = {
    soft: new Flipbook('puffsoft.png', 6, SOFT_MAX, { sort: true, soft: true, inkK: 0 }), // the default smoke (owner's pick, 2026-11-10)
    splash: new Flipbook('splash.png', 4, 48, { flat: -1, ink: 0x1a4a8a, inkK: 0.7 }),
    ripple: new Flipbook('ripple.png', 4, 64, { flat: 1, ink: 0x9adcff, inkK: 0.5, order: 3 }),
  };
  return FB;
}
// the other smoke styles load only when picked (they're bigger files)
const SOFT_MAX = 240; // soft puffs alive at once, all smokes together (each is a see-through quad: this is the cost)
const STYLE = { kenney: 'puffkenney.png', unity: 'puffunity.png' }; // Kenney's white puffs (CC0) / Unity Labs' simulated wispy smoke (CC0)
function styleBook(st) {
  const f = get();
  if (!f[st]) f[st] = st === 'puff' ? new Flipbook('puff.png', 6, 260, { sort: true }) : new Flipbook(STYLE[st], 6, SOFT_MAX, { sort: true, soft: true, inkK: 0 });
  return f[st];
}
// drawn effects on? (Settings > video; never on Potato; off again if a sheet failed to load)
export function spritesOn() {
  const S = G.settings || {};
  if (S.jank === 0 || S.fxSprites === false) return false;
  return !(FB && Object.values(FB).some((f) => f.failed));
}
// (tests / the old-vs-new clips: is everything loaded)
export const spritesReady = () => Object.values(get()).every((f) => f.ready);

// a smoke grenade's cloud: called every frame while it's out. s = { p, r }, dt-paced so it's the same cloud at any fps
export function smokeCloud(s, dt) {
  { const now = performance.now(); dt = Math.min(1, (now - (s.fbT || now)) / 1000); s.fbT = now; } // by the clock, not the (capped) frame step: a slow machine gets the same thick cloud, not a thin one
  const st = (G.settings || {}).fxSmoke;
  if (st !== 'comic') { softCloud(s, dt, st === 'kenney' || st === 'unity' ? st : 'soft'); return; }
  const F = styleBook('puff');
  s.fbAcc = (s.fbAcc || 0) + dt * 26;
  const first = !s.fbOn; s.fbOn = true;
  let n = Math.floor(s.fbAcc) + (first ? 26 : 0); s.fbAcc -= Math.floor(s.fbAcc); // (it arrives as a burst, then keeps boiling)
  while (n-- > 0) {
    const a = Math.random() * 6.2832, rr = Math.sqrt(Math.random()) * s.r, h = Math.random();
    const g = 0.78 + Math.random() * 0.22;
    F.spawn({ p: [s.p[0] + Math.cos(a) * rr, s.p[1] + 0.3 + h * h * 3.4, s.p[2] + Math.sin(a) * rr], v: [Math.cos(a) * 0.35, 0.25 + Math.random() * 0.4, Math.sin(a) * 0.35],
      s0: 2.4, s1: 4.4 + Math.random() * 1.4, life: 2.8 + Math.random() * 1.4, a: 1, col: _c.setRGB(g, g, g * 1.02).getHex(), rot: (Math.random() - 0.5) * 0.7, spin: (Math.random() - 0.5) * 0.25 });
  }
}
// option B: the same cloud out of soft see-through puffs (more of them, each one half there)
function softCloud(s, dt, st = 'soft') {
  const F = styleBook(st), still = st === 'kenney'; // (Kenney's are separate shapes, not an animation: each puff keeps one)
  s.fbAcc = (s.fbAcc || 0) + dt * 24;
  const first = !s.fbOn; s.fbOn = true;
  let n = Math.floor(s.fbAcc) + (first ? 26 : 0); s.fbAcc -= Math.floor(s.fbAcc);
  while (n-- > 0) {
    const a = Math.random() * 6.2832, rr = Math.sqrt(Math.random()) * s.r, h = Math.random(), g = 0.7 + Math.random() * 0.25;
    F.spawn({ p: [s.p[0] + Math.cos(a) * rr, s.p[1] + 0.4 + h * h * 3.4, s.p[2] + Math.sin(a) * rr], v: [Math.cos(a) * 0.3, 0.2 + Math.random() * 0.45, Math.sin(a) * 0.3],
      s0: 3.3, s1: 6 + Math.random() * 1.6, life: 3 + Math.random() * 1.5, a: 0.9, col: _c.setRGB(g, g, g * 1.03).getHex(), rot: Math.random() * 6.28, spin: (Math.random() - 0.5) * 0.3, frame: still ? Math.floor(Math.random() * 36) / 36 + 0.001 : -1 });
  }
}
// something landed in water: rings on the surface + a crown standing up out of it. k as in liquids.js splash()
export function waterSplash(x, y, z, k, ride, tint = 0xffffff) {
  const F = get();
  F.ripple.spawn({ p: [x, y + 0.04, z], s0: 0.8 + k * 1.6, s1: 2.2 + k * 5, life: 0.9 + k * 0.7, a: 0.95, col: tint, rot: Math.random() * 6.28, ride });
  if (k > 0.5) F.ripple.spawn({ p: [x, y + 0.04, z], s0: 1.2 + k * 2, s1: 3.4 + k * 7.5, life: 1.5 + k * 0.7, a: 0.7, col: tint, rot: Math.random() * 6.28, ride });
  if (k > 0.2) F.splash.spawn({ p: [x, y, z], s0: 0.9 + k * 1.5, s1: 1.2 + k * 2.1, life: 0.55 + k * 0.3, a: 1, col: tint });
}
// ---- real explosions + muzzle smoke (owner, 2026-11-11: "I want actual effects")
// an explosion: the fireball flipbook baked in Blender (tools/sprites/blender/explosion_flipbook.py: bursts white-hot,
// cools to red, leaves rolling smoke), one big in the middle and a few smaller ones off-centre a beat later
function boomBook() { const f = get(); if (!f.boom) f.boom = new Flipbook('boom.png', 8, 40, { sort: true, soft: true, rgb: true, inkK: 0 }); return f.boom; }
export function boomSprite(p, radius = 4) {
  const F = boomBook(), R = (k) => (Math.random() * 2 - 1) * k, s = Math.max(2.5, radius * 1.9);
  F.spawn({ p: [p[0], p[1] + s * 0.12, p[2]], v: [0, 0.5, 0], s0: s * 0.9, s1: s * 1.25, life: 1.5, a: 1, rot: R(3.14) });
  for (let i = 0; i < 3; i++) F.spawn({ p: [p[0] + R(radius * 0.4), p[1] + Math.abs(R(radius * 0.35)), p[2] + R(radius * 0.4)], v: [R(0.6), 0.6 + Math.random() * 0.6, R(0.6)], s0: s * 0.45, s1: s * 0.8, life: 1.25 + Math.random() * 0.5, a: 0.95, rot: R(3.14), spin: R(0.2) });
}
// a shot: a small grey puff off the muzzle (the soft smoke sheet). not for your own gun (it would sit in your face),
// and no more than one every 60 ms from about the same place, so an automatic doesn't lay a wall of it
let lastPuff = 0, lastPx = 1e9, lastPz = 1e9;
export function muzzlePuff(a, b) {
  const now = performance.now(), cam = G.camera && G.camera.position;
  if (!cam || Math.hypot(a[0] - cam.x, a[1] - cam.y, a[2] - cam.z) < 1.3) return;
  if (now - lastPuff < 60 && Math.abs(a[0] - lastPx) + Math.abs(a[2] - lastPz) < 0.6) return;
  lastPuff = now; lastPx = a[0]; lastPz = a[2];
  const dx = b[0] - a[0], dy = b[1] - a[1], dz = b[2] - a[2], l = Math.hypot(dx, dy, dz) || 1, g = 0.72 + Math.random() * 0.2;
  get().soft.spawn({ p: [a[0] + dx / l * 0.15, a[1] + dy / l * 0.15, a[2] + dz / l * 0.15], v: [dx / l * 1.6, dy / l * 1.6 + 0.35, dz / l * 1.6], s0: 0.22, s1: 0.85, life: 0.55 + Math.random() * 0.25, a: 0.5, col: _c.setRGB(g, g, g).getHex(), rot: Math.random() * 6.28, spin: (Math.random() - 0.5) * 2, drag: 3.5 });
}
// main.js, every frame (also keeps the smoke's light in step with the map)
export function updateFlipbooks(dt) {
  if (!FB) return;
  const hemi = G.scene && G.scene.children.find((o) => o.isHemisphereLight);
  const l = hemi && Number.isFinite(hemi.intensity) ? Math.min(1.08, Math.max(0.3, 0.34 + hemi.intensity * 0.52)) : 1;
  LIT.value.setRGB(l, l, l);
  for (const k in FB) FB[k].update(dt, G.camera);
}
export const flipbooks = () => get(); // (tests: the live sheets)
export function clearFlipbooks() { if (FB) for (const k in FB) FB[k].clear(); }
