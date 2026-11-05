// Grapple skins: what your rope and hook look like. One per player (like kill effects), everyone sees yours.
// A rope is one or two shader beams from the gun to the anchor (stripes, chain links, leaves or glow, all
// maths, no textures) plus a tiny hook model at the anchor, pointing along the rope into whatever it grabbed.
// Every rope with the same skin shares geometry + materials; moving one per frame allocates nothing.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { G } from './ctx.js';
import { COSMETICS, ownedGrapple } from '/shared/cosmetics.js';

export const myGrapple = () => ownedGrapple(G.settings.grap, G.inv);
const known = (id) => typeof id === 'string' && Object.hasOwn(COSMETICS.grapple, id);

// ------------------------------------------------------------ rope shader
const TIME = { value: 0 };
const VERT = `
uniform float uMinW;
varying vec2 vP;
varying float vAlong;
varying vec3 vN;
#include <fog_pars_vertex>
void main() {
  float th = length(modelMatrix[0].xyz), len = length(modelMatrix[2].xyz);
  vP = position.xy;
  vAlong = position.z * len;
  vec4 ax = modelViewMatrix * vec4(0.0, 0.0, position.z, 1.0);
  float k = max(1.0, -ax.z * uMinW / th); // never thinner than about a pixel, so far ropes still read
  // a touch thinner right at your own gun; glows and the vine's leaves stay small until they're out of your face
#if defined(GLOW) || defined(LEAF)
  k *= clamp(-ax.z / 4.0, 0.2, 1.0);
#else
  k *= clamp(-ax.z / 1.5, 0.5, 1.0);
#endif
#ifdef RIBBON
  // flat strip that turns round the rope's axis to face the camera (glows, chain): reads the same from any side
  vec3 dir = normalize(mat3(modelViewMatrix) * vec3(0.0, 0.0, 1.0));
  vec3 side = cross(dir, normalize(vec3(0.0, 0.0, 1e-5) - ax.xyz));
  side = dot(side, side) > 1e-10 ? normalize(side) : vec3(1.0, 0.0, 0.0);
  vec4 mvPosition = vec4(ax.xyz + side * position.x * th * k, 1.0);
  vN = vec3(0.0, 0.0, 1.0);
#else
  vec4 mvPosition = modelViewMatrix * vec4(position.xy * k, position.z, 1.0);
  vN = normalMatrix * normal;
#endif
  gl_Position = projectionMatrix * mvPosition;
#include <fog_vertex>
}`;
const FRAG = `
uniform vec3 uC1;
uniform vec3 uC2;
uniform float uF;
uniform float uTw;
uniform float uA;
uniform float uSharp;
uniform float uTime;
varying vec2 vP;
varying float vAlong;
varying vec3 vN;
#include <fog_pars_fragment>
vec3 hue(float h) { return clamp(abs(fract(h + vec3(0.0, 0.6667, 0.3333)) * 6.0 - 3.0) - 1.0, 0.0, 1.0); }
void main() {
  float lit = 0.6 + 0.5 * max(0.0, dot(normalize(vN), vec3(0.32, 0.86, 0.4)));
  vec3 col = uC1;
  float a = uA;
#if defined(TWIST)
  // strands wind round the rope: stripes in (along, around) space, smudged where they'd shimmer far away
  float s = vAlong * uF + atan(vP.y, vP.x) * uTw * 0.15915;
  float g = abs(fract(s) - 0.5) * 2.0;
  col = mix(uC1, uC2, mix(g * g, step(0.5, g), uSharp));
  col = mix(col, mix(uC1, uC2, 0.4), clamp(fwidth(vAlong * uF) * 2.0 - 0.5, 0.0, 1.0)) * lit;
#elif defined(CHAIN)
  // flat links (oval rings) take turns with edge-on ones (bars) whose ends hook into the rings' holes
  float y = abs(vP.x) * 2.0, u = vAlong / uF, f = fract(u), e = length(vec2(f * 2.0 - 1.0, y)), fw = fwidth(u);
  bool ring = mod(floor(u), 2.0) < 1.0;
  if (fw < 0.35) {
    bool onRing = ring && e < 1.0 && e > 0.58, onBar = y < 0.28 && (!ring || abs(f - 0.5) > 0.22);
    if (!onRing && !onBar) discard;
    col = mix(uC2, uC1, onRing ? 1.0 - abs(e - 0.79) * 4.5 : 0.85 - y * 2.0);
  } else if (fw < 1.0) { // links a few pixels long (your own chain, looking down it): chunky beads, light and dark
    if (!ring && y > 0.45) discard;
    col = ring ? uC1 * 0.9 : uC2 * 1.3;
  } else col = mix(uC1, uC2, 0.45); // links smaller than a pixel: just a grey line
  col *= lit;
#elif defined(LEAF)
  // two crossed strips with leaves cut out of them, alternating sides of the vine
  bool b = abs(vP.y) > abs(vP.x);
  float x = (b ? vP.y : vP.x) * 2.0;
  float u = vAlong / uF + (b ? 0.5 : 0.0);
  float fw = fwidth(u);
  float t = (x * (mod(floor(u), 2.0) < 1.0 ? 1.0 : -1.0) - 0.12) / 0.88;
  float d = fract(u) - 0.5 + t * 0.22;
  float w = sin(3.1416 * pow(clamp(t, 0.0, 1.0), 0.7)) * 0.3;
  if (t < 0.0 || abs(d) > w || fw > 0.45 || vAlong < 1.5) discard;
  col = mix(uC1, uC2, step(abs(d), 0.035)) * (0.72 + 0.4 * t);
#elif defined(GLOW)
  float x = abs(vP.x) * 2.0, pulse = 0.72 + 0.28 * sin(vAlong * 2.2 - uTime * 14.0);
#ifdef RAINBOW
  // crisp bands across the beam like a real rainbow, the colours cycling, a soft glow round the edge. premultiplied
  // alpha: the bands are solid (alpha 1) so they don't wash out on a bright sky, the glow outside them adds light
  float band = step(x, 0.7);
  vec3 c = hue(floor(clamp(vP.x / 0.7 + 0.5, 0.0, 0.999) * 6.0) * 0.14 - uTime * 0.3);
  col = c * mix((1.0 - x) * 1.3 * pulse, 0.8 + 0.2 * pulse, band);
  a = band;
#else
  // white-hot core, coloured halo, pulses running down the beam
  col = uC1 * (1.0 - x) * (1.0 - x) * pulse * 1.3 + mix(uC1, vec3(1.0), 0.75) * smoothstep(0.3, 0.06, x);
#endif
#elif defined(JELLY)
  // see-through stretchy cord with a wet shine
  float sp = pow(max(0.0, dot(normalize(vN), vec3(-0.25, 0.75, 0.6))), 8.0);
  col = uC1 * lit + vec3(sp);
  a = min(1.0, uA + sp * 0.4);
#endif
  gl_FragColor = vec4(col, a);
#include <colorspace_fragment>
#include <fog_fragment>
}`;

function ropeMat(kind, o = {}) {
  const glow = kind === 'GLOW', add = glow && !o.rainbow, a = o.a ?? 1, ribbon = glow || !!o.ribbon;
  const defines = { [kind]: '' };
  if (ribbon) defines.RIBBON = '';
  if (o.rainbow) defines.RAINBOW = '';
  const m = new THREE.ShaderMaterial({
    defines,
    uniforms: THREE.UniformsUtils.merge([THREE.UniformsLib.fog, {
      uC1: { value: new THREE.Color(o.c1 ?? 0xffffff) }, uC2: { value: new THREE.Color(o.c2 ?? 0x000000) },
      uF: { value: o.f ?? 1 }, uTw: { value: o.tw ?? 0 }, uA: { value: a }, uSharp: { value: o.sharp ? 1 : 0 }, uMinW: { value: 0.004 },
    }]),
    vertexShader: VERT, fragmentShader: FRAG,
    fog: !glow, transparent: glow || a < 1, depthWrite: !glow && a >= 1,
    blending: add ? THREE.AdditiveBlending : THREE.NormalBlending, premultipliedAlpha: glow && !add,
    side: kind === 'LEAF' || ribbon ? THREE.DoubleSide : THREE.FrontSide, // the ribbon's winding flips as it turns to the camera
  });
  m.uniforms.uTime = TIME; // shared: one clock for every rope
  return m;
}

// unit pieces running 0..1 along +z, scaled to (thickness, thickness, length) per rope
const strip = () => new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2);
const GEO = {
  cyl: new THREE.CylinderGeometry(0.5, 0.5, 1, 6, 1, true).rotateX(Math.PI / 2).translate(0, 0, 0.5),
  ribbon: strip().translate(0, 0, 0.5),
  cross: mergeGeometries([strip(), strip().rotateZ(Math.PI / 2)]).translate(0, 0, 0.5),
};

// ------------------------------------------------------------ hook models
// hook space: +z points along the rope into the surface and the bite is at z = 0, so most of it sits behind
// (z < 0) and the tips sink into whatever it grabbed
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const UP = V(0, 1, 0);
function rod(p, q, r0, r1 = r0, seg = 6) { // round bar from p (radius r0) to q (radius r1). r1 = 0 is a spike
  const d = q.clone().sub(p), len = d.length();
  return new THREE.CylinderGeometry(r1, r0, len, seg).translate(0, len / 2, 0)
    .applyQuaternion(new THREE.Quaternion().setFromUnitVectors(UP, d.normalize())).translate(p.x, p.y, p.z);
}
const ball = (p, r, sx = 1, sy = 1, sz = 1) => new THREE.SphereGeometry(r, 7, 5).scale(sx, sy, sz).translate(p.x, p.y, p.z);
function ring(p, R, r, alongRope = false) { // torus round the rope, or (alongRope) an eye the rope ties to
  const g = new THREE.TorusGeometry(R, r, 4, 10);
  if (alongRope) g.rotateY(Math.PI / 2);
  return g.translate(p.x, p.y, p.z);
}
const tube = (pts, r, seg = 16) => new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), seg, r, 6, false);
const around = (a) => (r, z) => V(Math.cos(a) * r, Math.sin(a) * r, z); // radial helper: point r out at angle a

// bake [geometry, colour or (u, v, normalZ) => colour] pairs into one vertex-coloured mesh: one draw call per hook
function bake(parts, mat) {
  const tc = new THREE.Color();
  const geos = parts.map(([g0, c]) => {
    const g = g0.index ? g0.toNonIndexed() : g0, n = g.attributes.position.count, uv = g.attributes.uv, nm = g.attributes.normal;
    const col = new Float32Array(n * 3);
    for (let i = 0; i < n; i += 3) { // per triangle, so stripes stay crisp
      tc.setHex(typeof c === 'function' ? c((uv.getX(i) + uv.getX(i + 1) + uv.getX(i + 2)) / 3, (uv.getY(i) + uv.getY(i + 1) + uv.getY(i + 2)) / 3, nm.getZ(i)) : c);
      for (let k = i * 3; k < i * 3 + 9; k += 3) { col[k] = tc.r; col[k + 1] = tc.g; col[k + 2] = tc.b; }
    }
    g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    g.deleteAttribute('uv');
    return g;
  });
  return new THREE.Mesh(mergeGeometries(geos), mat);
}
const litMat = () => new THREE.MeshLambertMaterial({ vertexColors: true, flatShading: true });
const glowMat = (color) => new THREE.MeshBasicMaterial({ vertexColors: true, color, fog: false });
let flareTex = null;
function flare(size, color, z) { // blocky additive glow (pixels, not a smooth gradient: it's that kind of game)
  if (!flareTex) {
    const c = document.createElement('canvas'); c.width = c.height = 12;
    const g = c.getContext('2d');
    for (let y = 0; y < 12; y++) for (let x = 0; x < 12; x++) {
      const d = Math.hypot(x - 5.5, y - 5.5) / 6;
      if (d < 1) { g.fillStyle = `rgba(255,255,255,${Math.pow(1 - d, 1.6).toFixed(3)})`; g.fillRect(x, y, 1, 1); }
    }
    flareTex = new THREE.CanvasTexture(c);
    flareTex.magFilter = flareTex.minFilter = THREE.NearestFilter;
  }
  const m = new THREE.Mesh(new THREE.PlaneGeometry(size, size), new THREE.MeshBasicMaterial({
    map: flareTex, color, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: false, side: THREE.DoubleSide,
  }));
  m.position.z = z;
  return m;
}

// each skin: rope layers (geo, thickness, material), where the rope ties on (tail, back from the bite),
// the hook, and an optional per-frame tick for the shiny ones. built the first time someone needs it
const DEFS = {
  rope: () => {
    const parts = [[rod(V(0, 0, -0.45), V(0, 0, -0.03), 0.024), 0x5b5f68], [ring(V(0, 0, -0.49), 0.045, 0.014, true), 0x70747d], [ball(V(0, 0, -0.045), 0.043), 0x44474f]];
    for (let i = 0; i < 3; i++) { // three prongs that flare out and curl back toward the rope, like a real grappling hook
      const R = around(Math.PI / 2 + (i * Math.PI * 2) / 3);
      parts.push([rod(R(0, -0.05), R(0.16, -0.1), 0.02, 0.017), 0x4d5058], [rod(R(0.16, -0.1), R(0.22, -0.22), 0.017, 0.015), 0x4d5058], [rod(R(0.22, -0.22), R(0.19, -0.32), 0.016, 0), 0xa2a8b2]);
    }
    return { tail: 0.5, beams: [['cyl', 0.05, ropeMat('TWIST', { c1: 0x8f6a3e, c2: 0x3d2914, f: 9, tw: 3 })]], hook: bake(parts, litMat()) };
  },
  chain: () => {
    const parts = [[rod(V(0, 0, -0.27), V(0, 0, -0.1), 0.06), 0x8d939d], [ring(V(0, 0, -0.3), 0.05, 0.016, true), 0xb0b6c0], [rod(V(0, 0, -0.13), V(0, 0, -0.07), 0.1, 0.1, 8), 0x5a5f69]];
    for (let i = 0; i < 4; i++) { // four claw fingers that bite in
      const R = around(Math.PI / 4 + (i * Math.PI) / 2);
      parts.push([ball(R(0.095, -0.09), 0.032), 0x3a3e46], [rod(R(0.095, -0.09), R(0.2, -0.01), 0.024, 0.02), 0x8a909a],
        [rod(R(0.2, -0.01), R(0.13, 0.07), 0.02, 0.015), 0x8a909a], [rod(R(0.13, 0.07), R(0.07, 0.11), 0.015, 0), 0xe0e4ea]);
    }
    return { tail: 0.32, beams: [['ribbon', 0.09, ropeMat('CHAIN', { c1: 0xd2d7df, c2: 0x464a52, f: 0.11, ribbon: true })]], hook: bake(parts, litMat()) };
  },
  candy: () => { // the crook of the cane is the hook
    const pts = [V(0, 0, -0.56), V(0, 0, -0.34), V(0, 0, -0.15)];
    for (let i = 1; i <= 8; i++) { const f = (i / 8) * 3.6; pts.push(V(0, 0.09 - Math.cos(f) * 0.09, -0.12 + Math.sin(f) * 0.09)); }
    const stripes = (u, v) => (Math.floor(u * 22 + v * 2) % 2 ? 0xffffff : 0xe8202a);
    return {
      tail: 0.56, beams: [['cyl', 0.058, ropeMat('TWIST', { c1: 0xf01828, c2: 0xffffff, f: 5, tw: 2, sharp: 1 })]],
      hook: bake([[tube(pts, 0.028, 40), stripes], [ball(pts[0], 0.028), 0xffffff], [ball(pts[pts.length - 1], 0.028), 0xe8202a]], litMat()),
    };
  },
  plunger: () => { // stuck on by suction, the handle points back at you
    const cup = new THREE.CylinderGeometry(0.05, 0.145, 0.12, 10, 1, true).rotateX(-Math.PI / 2).translate(0, 0, -0.06);
    const parts = [[rod(V(0, 0, -0.62), V(0, 0, -0.1), 0.022), 0xb57f45], [ball(V(0, 0, -0.62), 0.032), 0x7a4a22], [cup, 0xc4141f],
      [rod(V(0, 0, -0.135), V(0, 0, -0.11), 0.05, 0.05, 10), 0x8a0c14], [ring(V(0, 0, -0.01), 0.145, 0.017), 0x8a0c14]];
    const hook = bake(parts, litMat());
    hook.geometry.translate(0, 0, -0.05); // sat a little off the face, or the cup vanishes into the wall from your own view
    return { tail: 0.67, beams: [['cyl', 0.042, ropeMat('TWIST', { c1: 0xe8dcc0, c2: 0x9c8a62, f: 12, tw: 3 })]], hook };
  },
  vine: () => { // wooden hook lashed together with vine, plus a couple of leaves
    const parts = [[rod(V(0, 0, -0.47), V(0, 0, -0.06), 0.03), 0x7a4a22], [ball(V(0, 0, -0.06), 0.042), 0x6a3e1a],
      [ring(V(0, 0, -0.39), 0.034, 0.012), 0x3f7a2a], [ring(V(0, 0, -0.34), 0.034, 0.012), 0x3f7a2a],
      [ball(V(0.055, 0.03, -0.37), 0.05, 1, 0.25, 1.8), 0x4caf50], [ball(V(-0.05, -0.035, -0.31), 0.045, 1, 0.25, 1.6), 0x388e3c]];
    for (const sy of [1, -1]) {
      const pts = [V(0, 0, -0.07), V(0, sy * 0.1, -0.05), V(0, sy * 0.17, -0.1), V(0, sy * 0.2, -0.2), V(0, sy * 0.17, -0.27)];
      parts.push([tube(pts, 0.021, 12), 0x8a5a2a], [rod(pts[4], V(0, sy * 0.12, -0.34), 0.021, 0), 0xb08250]);
    }
    return {
      tail: 0.47, hook: bake(parts, litMat()),
      beams: [['cyl', 0.06, ropeMat('TWIST', { c1: 0x4f9a33, c2: 0x23501a, f: 3, tw: 2 })], ['cross', 0.46, ropeMat('LEAF', { c1: 0x5cc04a, c2: 0x2e7d32, f: 0.34 })]],
    };
  },
  laser: () => { // emitter: a gadget with a glowing ring that holds on with light
    const parts = [[rod(V(0, 0, -0.27), V(0, 0, -0.09), 0.055, 0.055, 8), 0x2c313c], [rod(V(0, 0, -0.1), V(0, 0, -0.05), 0.076, 0.07, 8), 0x1a1d24]];
    for (let i = 0; i < 3; i++) {
      const R = around(Math.PI / 2 + (i * Math.PI * 2) / 3);
      parts.push([rod(R(0.05, -0.25), R(0.12, -0.28), 0.013), 0x3d4350], [rod(R(0.065, -0.06), R(0.1, 0.01), 0.014, 0.008), 0x3d4350]);
    }
    const hook = new THREE.Group(), fl = flare(0.55, 0x39e8ff, -0.012);
    hook.add(bake(parts, litMat()), bake([[ring(V(0, 0, -0.045), 0.068, 0.017), 0xffffff], [ball(V(0, 0, -0.275), 0.03), 0xffffff]], glowMat(0x6ff6ff)), fl);
    return {
      tail: 0.27, hook, beams: [['ribbon', 0.24, ropeMat('GLOW', { c1: 0x22d8ff })]],
      tick: (u, t) => { fl.material.opacity = 0.7 + 0.3 * Math.sin(t * 31); },
    };
  },
  sticky: () => { // the vending machine sticky hand, slapped on whatever it hit. a thin cord and a big hand, like the toy
    const parts = [[rod(V(0, 0, -0.045), V(0, 0, -0.005), 0.125, 0.13, 12).scale(0.9, 1.05, 1), 0xff4fa8], [ball(V(0, -0.02, -0.065), 0.058, 1, 1.2, 0.7), 0xff6bbb]];
    for (const [a, L] of [[-0.85, 0.13], [-0.3, 0.17], [0.22, 0.165], [0.72, 0.13], [1.95, 0.11]]) { // four fingers + a thumb
      const d = V(Math.sin(a), Math.cos(a), 0), p = d.clone().multiplyScalar(0.09).setZ(-0.025), q = d.clone().multiplyScalar(0.09 + L).setZ(-0.025);
      parts.push([rod(p, q, 0.033, 0.028), 0xff4fa8], [ball(q, 0.032), 0xff80c8]);
    }
    const mat = new THREE.MeshPhongMaterial({ vertexColors: true, transparent: true, opacity: 0.88, shininess: 90, specular: 0xffffff, emissive: 0x4a0a30 });
    const hand = bake(parts, mat);
    hand.geometry.rotateY(0.7).translate(0, 0, -0.17); // landed at a slant, pulled back off the face so it reads from the side and from your own view
    return { tail: 0.19, stretch: true, beams: [['cyl', 0.045, ropeMat('JELLY', { c1: 0xff4fa8, a: 0.72 })]], hook: hand };
  },
  rainbow: () => { // a glowing star that spins on the end of a rainbow
    const s = new THREE.Shape();
    for (let i = 0; i < 10; i++) { const a = (i / 10) * Math.PI * 2, r = i % 2 ? 0.085 : 0.2; if (i) s.lineTo(Math.sin(a) * r, Math.cos(a) * r); else s.moveTo(0, r); }
    s.closePath();
    const geo = new THREE.ExtrudeGeometry(s, { depth: 0.05, bevelEnabled: false }).translate(0, 0, -0.065);
    const mat = glowMat(0xffffff), star = bake([[geo, (u, v, nz) => (Math.abs(nz) > 0.5 ? 0xffffff : 0xb0b0b0)]], mat), fl = flare(0.85, 0xffffff, -0.04);
    const hook = new THREE.Group();
    hook.add(star, fl);
    return {
      tail: 0.06, hook, beams: [['ribbon', 0.3, ropeMat('GLOW', { rainbow: true })]],
      tick: (u, t) => { mat.color.setHSL((t * 0.45) % 1, 1, 0.62); fl.material.color.copy(mat.color); u.hook.rotation.z = t * 1.7; },
    };
  },
};
const styles = {};
function style(id) {
  if (!styles[id]) styles[id] = DEFS[id]();
  return styles[id];
}

// ------------------------------------------------------------ ropes
// a rope is a Group you add to a scene; show/hide it with .visible
export function makeRope(id) {
  const r = new THREE.Group();
  r.userData = { id: null, beams: [], hook: null };
  setRopeSkin(r, id);
  return r;
}

export function setRopeSkin(r, id) {
  if (!known(id)) id = 'rope';
  const u = r.userData;
  if (u.id === id) return;
  const st = style(id);
  u.id = id;
  for (const m of u.beams) r.remove(m);
  if (u.hook) r.remove(u.hook);
  u.beams = st.beams.map(([geo, th, mat]) => {
    const m = new THREE.Mesh(GEO[geo], mat);
    m.frustumCulled = false; // the shader widens far ropes, so the bounding box lies
    m.userData.th = th;
    r.add(m);
    return m;
  });
  u.hook = st.hook.clone();
  r.add(u.hook);
}

const tmpV = new THREE.Vector3(), camV = new THREE.Vector3();
// from a (the gun) to b (the anchor). far hooks get drawn bigger so you can still tell what it is
export function setRope(r, a, b, cam = G.camera) {
  const u = r.userData, st = style(u.id);
  const len = Math.max(0.001, Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]));
  r.position.set(a[0], a[1], a[2]);
  r.lookAt(tmpV.set(b[0], b[1], b[2]));
  camV.setFromMatrixPosition(cam.matrixWorld);
  const s = 1 + Math.max(0, Math.min(2.2, (camV.distanceTo(tmpV) - 6) / 22));
  const t = st.tick || st.stretch ? (performance.now() / 1000) % 3600 : 0; // only the moving ones need a clock
  if (st.tick) TIME.value = t;
  u.hook.position.z = len;
  u.hook.scale.setScalar(s);
  // sticky: the longer it stretches the thinner it gets, and it wobbles
  const k = st.stretch ? Math.max(0.4, Math.min(1.5, Math.sqrt(5 / len))) * (1 + Math.sin(t * 9) * 0.06) : 1;
  const L = Math.max(0.001, len - st.tail * s);
  for (const m of u.beams) m.scale.set(m.userData.th * k, m.userData.th * k, L);
  if (st.tick) st.tick(u, t);
}

// grappled at nothing: the rope flies out to max range and snaps back
let flash = null, flashT = 0;
export function flashRope(a, b, life = 0.1) {
  if (!flash) { flash = makeRope('rope'); G.scene.add(flash); }
  setRopeSkin(flash, myGrapple());
  flash.visible = true;
  setRope(flash, a, b);
  clearTimeout(flashT);
  flashT = setTimeout(() => { flash.visible = false; }, life * 1000);
}

// ------------------------------------------------------------ cosmetics screen: live preview + card thumbnails
let pv = null;
const AT = [0.62, 0.06, 0]; // where the hook bites: the face of a block

export function initGrapplePreview(canvas) {
  if (pv || !canvas) return !!pv;
  try {
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: false });
    renderer.setPixelRatio(1);
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x24122f);
    scene.add(new THREE.HemisphereLight(0xcfe8ff, 0x7a4a6a, 1.8));
    const sun = new THREE.DirectionalLight(0xffffff, 1.4);
    sun.position.set(-0.6, 1, 0.8);
    scene.add(sun);
    const block = new THREE.Mesh(new THREE.BoxGeometry(0.6, 2.2, 1.6), new THREE.MeshLambertMaterial({ color: 0x8a7a9a }));
    block.position.set(AT[0] + 0.3, 0, 0);
    const rope = makeRope('rope');
    scene.add(block, rope);
    pv = { renderer, scene, cam: new THREE.PerspectiveCamera(38, 1.6, 0.05, 40), rope, id: 'rope', t: 0, thumbs: new Map() };
  } catch (e) { console.warn('grapple preview', e); }
  return !!pv;
}

function pose(id, t, aspect, dist) {
  const { cam, rope } = pv;
  const ang = 0.55 + Math.sin(t * 0.45) * 0.4; // drift round so you see the hook from a few sides
  cam.position.set(AT[0] - 0.3 - Math.sin(ang) * dist, 0.42, Math.cos(ang) * dist);
  cam.lookAt(AT[0] - 0.32, 0.04, 0);
  cam.aspect = aspect;
  cam.updateProjectionMatrix();
  cam.updateMatrixWorld();
  setRopeSkin(rope, id);
  setRope(rope, [-2.2 + Math.sin(t * 0.8) * 0.2, 1.0 + Math.sin(t * 1.1) * 0.15, 0.6 + Math.cos(t * 0.7) * 0.25], AT, cam);
}

export function showGrapple(id) { if (pv) pv.id = id; }

export function renderGrapplePreview(dt) {
  if (!pv) return;
  const c = pv.renderer.domElement, w = c.clientWidth, h = c.clientHeight;
  if (!w || !h) return;
  const rw = Math.max(40, w >> 1), rh = Math.max(30, h >> 1); // crunchy, like the weapon preview
  if (c.width !== rw || c.height !== rh) pv.renderer.setSize(rw, rh, false);
  pv.t += dt;
  pose(pv.id, pv.t, w / h, 1.5);
  pv.renderer.render(pv.scene, pv.cam);
}

// a still for the picker cards, rendered once per skin and kept as an image
export function grappleThumb(id) {
  if (!pv) return '';
  if (!pv.thumbs.has(id)) {
    const c = pv.renderer.domElement, w = c.width, h = c.height;
    pv.renderer.setSize(112, 63, false);
    pose(id, 0.9, 112 / 63, 0.95);
    pv.renderer.render(pv.scene, pv.cam);
    pv.thumbs.set(id, c.toDataURL());
    pv.renderer.setSize(w, h, false);
  }
  return pv.thumbs.get(id);
}
