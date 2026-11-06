// Particles (square, because circles cost extra), tracers, ropes, explosions.
import * as THREE from 'three';
import { marbles } from './marbles.js';

const VS = `
attribute float aSize; attribute float aAlpha; attribute vec3 aColor; attribute float aTile;
varying vec3 vC; varying float vA; varying float vTile; uniform float uScale;
void main() {
  vC = aColor; vA = aAlpha; vTile = aTile;
  vec4 mv = modelViewMatrix * vec4(position, 1.0);
  gl_PointSize = aSize * uScale / max(0.1, -mv.z);
  gl_Position = projectionMatrix * mv;
}`;
const FS = `
varying vec3 vC; varying float vA;
void main() { if (vA <= 0.02) discard; gl_FragColor = vec4(vC, vA); }`;
// textured variant: picks a tile out of a horizontal icon atlas (hearts, notes, $...)
const FS_TEX = `
uniform sampler2D uMap; uniform float uTiles;
varying vec3 vC; varying float vA; varying float vTile;
void main() {
  vec2 uv = vec2((gl_PointCoord.x + vTile) / uTiles, 1.0 - gl_PointCoord.y);
  vec4 t = texture2D(uMap, uv);
  if (t.a < 0.5 || vA <= 0.02) discard;
  gl_FragColor = vec4(vC * t.rgb, vA);
}`;

export const scaleU = { value: 300 };
const tmpC = new THREE.Color();

export class PSys {
  constructor(max, blending, opts = {}) {
    this.max = max; this.n = 0;
    this.p = new Float32Array(max * 3); this.v = new Float32Array(max * 3);
    this.c0 = new Float32Array(max * 3); this.c1 = new Float32Array(max * 3);
    this.life = new Float32Array(max); this.ml = new Float32Array(max);
    this.s0 = new Float32Array(max); this.s1 = new Float32Array(max);
    this.a0 = new Float32Array(max); this.g = new Float32Array(max); this.drag = new Float32Array(max);
    this.col = new Float32Array(max * 3); this.alpha = new Float32Array(max); this.size = new Float32Array(max);
    this.tile = new Float32Array(max);
    const geo = new THREE.BufferGeometry();
    this.posAttr = new THREE.BufferAttribute(this.p, 3).setUsage(THREE.DynamicDrawUsage);
    this.colAttr = new THREE.BufferAttribute(this.col, 3).setUsage(THREE.DynamicDrawUsage);
    this.aAttr = new THREE.BufferAttribute(this.alpha, 1).setUsage(THREE.DynamicDrawUsage);
    this.sAttr = new THREE.BufferAttribute(this.size, 1).setUsage(THREE.DynamicDrawUsage);
    geo.setAttribute('position', this.posAttr);
    geo.setAttribute('aColor', this.colAttr);
    geo.setAttribute('aAlpha', this.aAttr);
    geo.setAttribute('aSize', this.sAttr);
    this.tAttr = new THREE.BufferAttribute(this.tile, 1).setUsage(THREE.DynamicDrawUsage);
    geo.setAttribute('aTile', this.tAttr);
    geo.setDrawRange(0, 0);
    this.geo = geo;
    const uniforms = { uScale: opts.scale || scaleU };
    if (opts.map) { uniforms.uMap = { value: opts.map }; uniforms.uTiles = { value: opts.tiles || 1 }; }
    const mat = new THREE.ShaderMaterial({
      uniforms, vertexShader: VS, fragmentShader: opts.map ? FS_TEX : FS,
      transparent: true, depthWrite: false, blending,
    });
    this.points = new THREE.Points(geo, mat);
    this.points.frustumCulled = false;
  }
  spawn(x, y, z, vx, vy, vz, life, s0, s1, c0, c1, a0 = 1, g = 0, drag = 0, tile = 0) {
    let i = this.n;
    if (i >= this.max) i = Math.floor(Math.random() * this.max); else this.n++;
    const i3 = i * 3;
    this.p[i3] = x; this.p[i3 + 1] = y; this.p[i3 + 2] = z;
    this.v[i3] = vx; this.v[i3 + 1] = vy; this.v[i3 + 2] = vz;
    tmpC.setHex(c0); this.c0[i3] = tmpC.r; this.c0[i3 + 1] = tmpC.g; this.c0[i3 + 2] = tmpC.b;
    tmpC.setHex(c1); this.c1[i3] = tmpC.r; this.c1[i3 + 1] = tmpC.g; this.c1[i3 + 2] = tmpC.b;
    this.life[i] = life; this.ml[i] = life; this.s0[i] = s0; this.s1[i] = s1;
    this.a0[i] = a0; this.g[i] = g; this.drag[i] = drag; this.tile[i] = tile;
  }
  copy(from, to) {
    const f3 = from * 3, t3 = to * 3;
    for (const arr of [this.p, this.v, this.c0, this.c1]) { arr[t3] = arr[f3]; arr[t3 + 1] = arr[f3 + 1]; arr[t3 + 2] = arr[f3 + 2]; }
    for (const arr of [this.life, this.ml, this.s0, this.s1, this.a0, this.g, this.drag, this.tile]) arr[to] = arr[from];
  }
  update(dt) {
    for (let i = 0; i < this.n; i++) {
      this.life[i] -= dt;
      if (this.life[i] <= 0) { this.n--; if (i !== this.n) this.copy(this.n, i); i--; continue; }
      const i3 = i * 3;
      const dr = Math.max(0, 1 - this.drag[i] * dt);
      this.v[i3] *= dr; this.v[i3 + 1] = (this.v[i3 + 1] - this.g[i] * dt) * dr; this.v[i3 + 2] *= dr;
      this.p[i3] += this.v[i3] * dt; this.p[i3 + 1] += this.v[i3 + 1] * dt; this.p[i3 + 2] += this.v[i3 + 2] * dt;
      const t = 1 - this.life[i] / this.ml[i];
      this.col[i3] = this.c0[i3] + (this.c1[i3] - this.c0[i3]) * t;
      this.col[i3 + 1] = this.c0[i3 + 1] + (this.c1[i3 + 1] - this.c0[i3 + 1]) * t;
      this.col[i3 + 2] = this.c0[i3 + 2] + (this.c1[i3 + 2] - this.c0[i3 + 2]) * t;
      this.size[i] = this.s0[i] + (this.s1[i] - this.s0[i]) * t;
      this.alpha[i] = this.a0[i] * (1 - t * t);
    }
    this.geo.setDrawRange(0, this.n);
    this.posAttr.needsUpdate = true; this.colAttr.needsUpdate = true;
    this.aAttr.needsUpdate = true; this.sAttr.needsUpdate = true; this.tAttr.needsUpdate = true;
  }
}

const BEAM_GEO = new THREE.BoxGeometry(1, 1, 1).translate(0, 0, 0.5);
const SPHERE_GEO = new THREE.IcosahedronGeometry(1, 1);
const RING_GEO = new THREE.RingGeometry(0.86, 1, 40).rotateX(-Math.PI / 2); // flat on the floor
const tmpV = new THREE.Vector3();

export function makeBeam(color, opacity = 1) {
  const m = new THREE.Mesh(BEAM_GEO, new THREE.MeshBasicMaterial({ color, transparent: opacity < 1, opacity }));
  m.frustumCulled = false;
  return m;
}

export function setBeam(m, a, b, th) {
  m.position.set(a[0], a[1], a[2]);
  const len = Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]);
  m.lookAt(tmpV.set(b[0], b[1], b[2]));
  m.scale.set(th, th, Math.max(0.001, len));
}

const R = (s = 1) => (Math.random() * 2 - 1) * s;
let fire, smoke, misc, blood, scene;
const timed = []; // {mesh, life, ml, kind, r}
const DECAL_GEO = new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2);
const decals = [];

export const fx = {
  init(sc) {
    scene = sc;
    fire = new PSys(4000, THREE.AdditiveBlending);
    smoke = new PSys(2500, THREE.NormalBlending);
    misc = new PSys(2500, THREE.NormalBlending);
    blood = new PSys(1500, THREE.NormalBlending);
    sc.add(smoke.points, misc.points, fire.points, blood.points);
    marbles.init(sc);
  },
  // square pixel blood. dir = which way it sprays. floorY = where decals land (or null)
  blood(p, dir, amount, floorY) {
    const n = Math.min(60, 6 + amount * 0.8);
    for (let i = 0; i < n; i++) {
      const s = 2 + Math.random() * 6;
      blood.spawn(p[0] + R(0.2), p[1] + R(0.3), p[2] + R(0.2),
        dir[0] * s + R(2.5), dir[1] * s + 1.5 + Math.random() * 3, dir[2] * s + R(2.5),
        0.5 + Math.random() * 0.5, 0.07 + Math.random() * 0.09, 0.05, Math.random() < 0.3 ? 0xd01010 : 0x8a0000, 0x3a0000, 1, 18, 0.5);
    }
    if (floorY == null) return;
    for (let i = 0; i < Math.min(5, 1 + amount / 12); i++) {
      let m = decals.length >= 80 ? decals.shift() : null;
      if (!m) { m = new THREE.Mesh(DECAL_GEO, new THREE.MeshBasicMaterial({ color: 0x6a0000, transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -3 })); scene.add(m); }
      const sz = 0.15 + Math.random() * 0.35;
      m.scale.set(sz, 1, sz);
      m.rotation.y = Math.random() * 6.28;
      m.position.set(p[0] + dir[0] * Math.random() * 1.5 + R(0.6), floorY + 0.02 + Math.random() * 0.01, p[2] + dir[2] * Math.random() * 1.5 + R(0.6));
      m.material.opacity = 0.9;
      m.userData.life = 6;
      decals.push(m);
    }
  },
  setScale(s) { scaleU.value = s; },
  parts() { return { fire, smoke, misc }; }, // the raw particle systems, for effects built elsewhere (traffic.js)
  smoke(p, n = 1, spread = 0.05) {
    for (let i = 0; i < n; i++) {
      smoke.spawn(p[0] + R(spread), p[1] + R(spread), p[2] + R(spread), R(0.3), 0.6 + Math.random() * 0.6, R(0.3),
        1.2 + Math.random(), 0.08, 0.9, 0xdddddd, 0x8a8a8a, 0.55, -0.3, 0.6);
    }
  },
  fireCone(o, d, base, n = 6) {
    for (let i = 0; i < n; i++) {
      const s = 19 + Math.random() * 6;
      fire.spawn(o[0], o[1], o[2],
        d[0] * s + R(4) + base[0] * 0.8, d[1] * s + R(4) + base[1] * 0.8, d[2] * s + R(4) + base[2] * 0.8,
        0.4 + Math.random() * 0.25, 0.2, 1.4, Math.random() < 0.5 ? 0xffee88 : 0xffaa33, 0xcc1100, 1, -4, 2.2);
    }
    if (Math.random() < 0.3) smoke.spawn(o[0] + d[0] * 6, o[1] + d[1] * 6 + 0.5, o[2] + d[2] * 6, d[0] * 3, 1.5, d[2] * 3, 1.2, 0.5, 2, 0x555555, 0x222222, 0.4, -1, 0.5);
  },
  leaves(o, d, base) {
    const cols = [0x4caf50, 0x8bc34a, 0xff9800, 0xc0602a, 0xffd54f];
    for (let i = 0; i < 4; i++) {
      const s = 14 + Math.random() * 6;
      misc.spawn(o[0], o[1], o[2], d[0] * s + R(3) + base[0], d[1] * s + R(3) + base[1], d[2] * s + R(3) + base[2],
        0.6 + Math.random() * 0.4, 0.14, 0.14, cols[(Math.random() * cols.length) | 0], 0x553311, 1, 3, 1.2);
    }
    smoke.spawn(o[0], o[1], o[2], d[0] * 10 + R(2), d[1] * 10 + R(2), d[2] * 10 + R(2), 0.4, 0.2, 1.2, 0xeeeeee, 0xffffff, 0.25, 0, 2);
  },
  suck(o, d) {
    for (let i = 0; i < 3; i++) {
      const k = 3 + Math.random() * 14;
      const sp = k * 0.35;
      const x = o[0] + d[0] * k + R(sp), y = o[1] + d[1] * k + R(sp), z = o[2] + d[2] * k + R(sp);
      const life = 0.35 + Math.random() * 0.25;
      misc.spawn(x, y, z, (o[0] - x) / life, (o[1] - y) / life, (o[2] - z) / life, life, 0.12, 0.05,
        Math.random() < 0.5 ? 0xbbaa99 : 0x777777, 0x333333, 1, 0, 0);
    }
  },
  // shredder suction: dust, leaves, grit and air swirls pulled out of a cone into the intake o. each one is aimed
  // to reach o as it dies (base = the shooter's velocity, so they keep up when you move). k = how spun up it is,
  // dt = frame time: the amount is per second, so a slow frame doesn't mean thin suction
  vacuum(o, d, base, range, cone, k = 1, dt = 1 / 60) {
    const up = Math.abs(d[1]) < 0.95 ? [0, 1, 0] : [1, 0, 0];
    let ux = d[1] * up[2] - d[2] * up[1], uy = d[2] * up[0] - d[0] * up[2], uz = d[0] * up[1] - d[1] * up[0];
    const ul = Math.hypot(ux, uy, uz) || 1; ux /= ul; uy /= ul; uz /= ul;
    const vx = d[1] * uz - d[2] * uy, vy = d[2] * ux - d[0] * uz, vz = d[0] * uy - d[1] * ux;
    const tc = Math.tan(cone), n = Math.min(80, Math.floor((240 + 420 * k) * dt + Math.random()));
    const leaves = [0x4caf50, 0x8bc34a, 0xff9800, 0xc0602a, 0xffd54f];
    for (let i = 0; i < n; i++) {
      const kind = Math.random(), swirl = kind < 0.3;
      // swirls stay close to the mouth and spin round the axis: a little tornado going in
      const dist = swirl ? 0.4 + Math.random() * 2.6 : 1.2 + Math.random() * range * (0.45 + 0.45 * k);
      const a = Math.random() * Math.PI * 2, r = dist * tc * Math.sqrt(Math.random()) * (swirl ? 0.6 : 0.9);
      const ca = Math.cos(a), sa = Math.sin(a);
      const x = o[0] + d[0] * dist + (ux * ca + vx * sa) * r, y = o[1] + d[1] * dist + (uy * ca + vy * sa) * r, z = o[2] + d[2] * dist + (uz * ca + vz * sa) * r;
      const life = (swirl ? 0.12 : 0.22) + dist / (14 + 14 * k) + Math.random() * 0.08;
      let px = (o[0] - x) / life + base[0], py = (o[1] - y) / life + base[1], pz = (o[2] - z) / life + base[2];
      if (swirl) {
        const sw = 2.5 + 4 * k;
        px += (vx * ca - ux * sa) * sw; py += (vy * ca - uy * sa) * sw; pz += (vz * ca - uz * sa) * sw;
        misc.spawn(x, y, z, px, py, pz, life, 0.11, 0.03, 0xe8f6ff, 0xffffff, 0.6, 0, 0);
      } else if (kind < 0.5) smoke.spawn(x, y, z, px, py, pz, life, 0.5, 0.08, 0xc8b898, 0x8a7a66, 0.35, 0, 0);
      else if (kind < 0.78) misc.spawn(x, y, z, px, py, pz, life, 0.15, 0.04, leaves[(Math.random() * leaves.length) | 0], 0x553311, 1, 0, 0);
      else misc.spawn(x, y, z, px, py, pz, life, 0.08, 0.03, Math.random() < 0.5 ? 0x555555 : 0x8a6a4a, 0x333333, 1, 0, 0);
    }
  },
  // a stream of blood from p into to (a shredder's intake), each drop landing on it
  bloodTo(p, to, n = 8, base = [0, 0, 0]) {
    for (let i = 0; i < n; i++) {
      const x = p[0] + R(0.3), y = p[1] + R(0.45), z = p[2] + R(0.3), life = 0.14 + Math.random() * 0.16;
      blood.spawn(x, y, z, (to[0] - x) / life + base[0], (to[1] - y) / life + base[1], (to[2] - z) / life + base[2],
        life, 0.08 + Math.random() * 0.08, 0.025, Math.random() < 0.3 ? 0xd01010 : 0x8a0000, 0x3a0000, 1, 0, 0);
    }
  },
  // a burst shot out of a chute along d: blood if gore is on, confetti if party is
  chute(o, d, base, n = 20, gore = true, party = true) {
    const cols = [0xff4fd8, 0x4fd8ff, 0xffe14d, 0x7dff4f, 0xff7a1a, 0xffffff];
    for (let i = 0; i < n; i++) {
      const s = 5 + Math.random() * 7;
      if (party) misc.spawn(o[0], o[1], o[2], d[0] * s + R(2.5) + base[0], d[1] * s + R(2.5) + base[1], d[2] * s + R(2.5) + base[2],
        0.9 + Math.random() * 0.9, 0.1, 0.1, cols[(Math.random() * cols.length) | 0], 0xffffff, 1, 6, 1.6);
      if (gore) blood.spawn(o[0], o[1], o[2], d[0] * s * 0.8 + R(2) + base[0], d[1] * s * 0.8 + R(2) + base[1], d[2] * s * 0.8 + R(2) + base[2],
        0.5 + Math.random() * 0.5, 0.08 + Math.random() * 0.08, 0.05, Math.random() < 0.3 ? 0xd01010 : 0x8a0000, 0x3a0000, 1, 18, 0.5);
    }
  },
  explosion(p, radius) {
    const m = new THREE.Mesh(SPHERE_GEO, new THREE.MeshBasicMaterial({ color: 0xffcc33, transparent: true, opacity: 1 }));
    m.position.set(p[0], p[1], p[2]);
    scene.add(m);
    timed.push({ mesh: m, life: 0.28, ml: 0.28, kind: 'flash', r: radius });
    for (let i = 0; i < 70; i++) {
      const s = 4 + Math.random() * 14;
      const a = [R(), R(), R()], l = Math.hypot(...a) || 1;
      fire.spawn(p[0], p[1], p[2], a[0] / l * s, a[1] / l * s, a[2] / l * s, 0.4 + Math.random() * 0.4, 0.6, 2.5, 0xffffaa, 0xff3300, 1, -2, 3);
    }
    for (let i = 0; i < 25; i++) smoke.spawn(p[0] + R(2), p[1] + R(2), p[2] + R(2), R(3), 2 + Math.random() * 2, R(3), 1.5 + Math.random(), 1, 3.5, 0x444444, 0x222222, 0.6, -0.5, 1);
    this.feathers(p, 25);
  },
  feathers(p, n) {
    for (let i = 0; i < n; i++) misc.spawn(p[0], p[1], p[2], R(9), 3 + Math.random() * 8, R(9), 1.2 + Math.random() * 1.2, 0.18, 0.15, 0xffffff, 0xffeeaa, 1, 4, 2.5);
  },
  tracer(a, b, color = 0xffffff, th = 0.06, life = 0.35) {
    const m = makeBeam(color, 0.99);
    setBeam(m, a, b, th);
    scene.add(m);
    timed.push({ mesh: m, life, ml: life, kind: 'beam' });
  },
  rope(a, b, life = 0.12) {
    const m = makeBeam(0x3a2a1a, 0.99);
    setBeam(m, a, b, 0.04);
    scene.add(m);
    timed.push({ mesh: m, life, ml: life, kind: 'beam' });
  },
  impact(p, n) {
    const nn = n || [0, 1, 0];
    for (let i = 0; i < 10; i++) misc.spawn(p[0], p[1], p[2], nn[0] * 4 + R(3), nn[1] * 4 + R(3), nn[2] * 4 + R(3), 0.5, 0.15, 0.08, 0x999988, 0x444444, 1, 12, 1);
  },
  // katana parry: hot sparks off the blade and a tiny white pop. dir = the way the hit came from: sparks spray out
  // sideways and up off the edge, only a little back along it (straight back would be into a swordsman's face)
  sparks(p, dir, n = 20, hot = false) {
    const d = dir || [0, 0, 0], sx = -d[2], sz = d[0];
    for (let i = 0; i < n; i++) {
      const s = 2.5 + Math.random() * (hot ? 7 : 5), side = R(1), back = Math.random() * 0.35;
      const a = [sx * side + d[0] * back + R(0.3), 0.25 + Math.random() * 0.9, sz * side + d[2] * back + R(0.3)], l = Math.hypot(...a) || 1;
      fire.spawn(p[0], p[1], p[2], a[0] / l * s, a[1] / l * s, a[2] / l * s, 0.1 + Math.random() * 0.2, hot ? 0.11 : 0.085, 0.02,
        Math.random() < 0.5 ? 0xffffff : 0xfff2b0, 0xff7a10, 1, 14, 2);
    }
    const m = new THREE.Mesh(SPHERE_GEO, new THREE.MeshBasicMaterial({ color: hot ? 0xfff6c0 : 0xffffff, transparent: true, opacity: 1 }));
    m.position.set(p[0], p[1], p[2]);
    m.scale.setScalar(hot ? 0.22 : 0.15);
    scene.add(m);
    timed.push({ mesh: m, life: hot ? 0.16 : 0.1, ml: hot ? 0.16 : 0.1, kind: 'pop' }); // just fades, no growing
  },
  burn(p) {
    fire.spawn(p[0] + R(0.4), p[1] + Math.random() * 1.8, p[2] + R(0.4), R(0.5), 2 + Math.random() * 2, R(0.5), 0.4, 0.35, 0.05, 0xffcc44, 0xff2200, 1, -2, 0);
  },
  splat(p) {
    for (let i = 0; i < 16; i++) misc.spawn(p[0], p[1], p[2], R(5), 2 + Math.random() * 5, R(5), 0.7, 0.16, 0.1, 0xffe135, 0xbb9900, 1, 15, 0.5);
  },
  confetti(o, d, base) {
    const cols = [0xff4fd8, 0x4fd8ff, 0xffe14d, 0x7dff4f, 0xff7a1a, 0xffffff];
    for (let i = 0; i < 70; i++) {
      const s = 8 + Math.random() * 16;
      misc.spawn(o[0], o[1], o[2], d[0] * s + R(5) + base[0], d[1] * s + R(5) + base[1], d[2] * s + R(5) + base[2],
        1 + Math.random() * 1.2, 0.12, 0.12, cols[(Math.random() * cols.length) | 0], 0xffffff, 1, 5, 2.5);
    }
  },
  vortex(p, r) {
    for (let i = 0; i < 4; i++) {
      const a = Math.random() * Math.PI * 2, k = r * (0.4 + Math.random() * 0.6);
      const x = p[0] + Math.cos(a) * k, y = p[1] + R(k * 0.4), z = p[2] + Math.sin(a) * k;
      const life = 0.6 + Math.random() * 0.4;
      // spiral in: tangential + radial
      const tx = -Math.sin(a) * k * 2, tz = Math.cos(a) * k * 2;
      misc.spawn(x, y, z, (p[0] - x) / life + tx * 0.3, (p[1] - y) / life, (p[2] - z) / life + tz * 0.3, life, 0.18, 0.05,
        Math.random() < 0.5 ? 0xb07dff : 0xff7aff, 0x220044, 1, 0, 0);
    }
  },
  blast(p, radius, c0 = 0xd9a3ff, c1 = 0x5a00aa) {
    const m = new THREE.Mesh(SPHERE_GEO, new THREE.MeshBasicMaterial({ color: c0, transparent: true, opacity: 1 }));
    m.position.set(p[0], p[1], p[2]);
    scene.add(m);
    timed.push({ mesh: m, life: 0.3, ml: 0.3, kind: 'flash', r: radius });
    for (let i = 0; i < 60; i++) {
      const s = 5 + Math.random() * 14;
      const a = [R(), R(), R()], l = Math.hypot(...a) || 1;
      fire.spawn(p[0], p[1], p[2], a[0] / l * s, a[1] / l * s, a[2] / l * s, 0.5 + Math.random() * 0.4, 0.6, 2.2, c0, c1, 1, 0, 3);
    }
  },
  // glitch dash body: a cloud of missing-texture pixels
  glitch(p, vel, n = 5) {
    for (let i = 0; i < n; i++) {
      misc.spawn(p[0] + R(0.45), p[1] + 0.2 + Math.random() * 1.6, p[2] + R(0.45), -vel[0] * 0.15 + R(1.5), R(1.5), -vel[2] * 0.15 + R(1.5),
        0.25 + Math.random() * 0.35, 0.14 + Math.random() * 0.12, 0.05, Math.random() < 0.5 ? 0xff00dc : 0x000000, 0x220022, 1, 0, 2);
    }
  },
  // generic burst of coloured squares (kill effects use it)
  spray(p, n, colors, speed = 8, life = 1.5, size = 0.18, grav = 6, drag = 1) {
    for (let i = 0; i < n; i++) {
      const a = [R(), Math.random() * 0.8 + 0.2, R()], l = Math.hypot(...a) || 1, sp = speed * (0.4 + Math.random() * 0.6);
      misc.spawn(p[0], p[1], p[2], a[0] / l * sp, a[1] / l * sp, a[2] / l * sp, life * (0.6 + Math.random() * 0.6), size, size * 0.7,
        colors[(Math.random() * colors.length) | 0], 0xffffff, 1, grav, drag);
    }
  },
  // a soap bubble (radius r) pops: droplets fly off its whole surface, then rain down
  droplets(p, r, n = 40) {
    const cols = [0xffffff, 0xd8f6ff, 0xffd6f4, 0xfff4b8, 0xc8ffe8];
    for (let i = 0; i < n; i++) {
      const a = [R(), R(), R()], l = Math.hypot(...a) || 1, s = 1.5 + Math.random() * 4.5;
      misc.spawn(p[0] + (a[0] / l) * r, p[1] + (a[1] / l) * r, p[2] + (a[2] / l) * r, (a[0] / l) * s, (a[1] / l) * s + 1.5, (a[2] / l) * s,
        0.45 + Math.random() * 0.5, 0.05 + Math.random() * 0.07, 0.02, cols[(Math.random() * cols.length) | 0], 0xbfe8ff, 0.9, 14, 1.5);
    }
  },
  dust(p, n = 8) {
    for (let i = 0; i < n; i++) smoke.spawn(p[0] + R(0.4), p[1] + 0.05, p[2] + R(0.4), R(3), 0.5 + Math.random(), R(3), 0.5, 0.2, 0.7, 0xc8b89a, 0xa89878, 0.5, 0, 3);
  },
  // a flat ring racing out along the floor (shockwaves)
  ring(p, radius, color = 0xffffff, life = 0.45) {
    const m = new THREE.Mesh(RING_GEO, new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 1, depthWrite: false, side: THREE.DoubleSide }));
    m.position.set(p[0], p[1] + 0.12, p[2]);
    scene.add(m);
    timed.push({ mesh: m, life, ml: life, kind: 'flash', r: radius });
  },
  // wrecking ball ground slam: shockwave rings, a wall of dust rolling outward, chunks of floor, sparks.
  // radius = how far it hurts, k = how big a slam it was (0 = off a hop, 1 = from way up)
  slam(p, radius, k = 0.5) {
    this.ring(p, radius * 1.1, 0xffffff, 0.3 + k * 0.15);
    this.ring(p, radius * 0.8, 0xd8c39a, 0.55 + k * 0.25);
    if (k > 0.5) this.ring(p, radius * 1.35, 0xfff2b0, 0.7);
    const nd = 24 + Math.round(k * 40), sp = radius * 1.4;
    for (let i = 0; i < nd; i++) {
      const a = (i / nd) * Math.PI * 2 + R(0.1), s = sp * (0.6 + Math.random() * 0.7);
      smoke.spawn(p[0] + Math.cos(a) * 0.9, p[1] + 0.2 + Math.random() * 0.5, p[2] + Math.sin(a) * 0.9, Math.cos(a) * s, 0.6 + Math.random() * (1 + k * 2), Math.sin(a) * s,
        0.7 + Math.random() * 0.6 + k * 0.4, 0.6 + k * 0.4, 2 + k * 1.6, 0xd6c6a6, 0x9a8a6a, 0.75, 0, 2.6);
    }
    for (let i = 0; i < 16 + k * 30; i++) {
      const a = Math.random() * Math.PI * 2, s = 3 + Math.random() * (5 + k * 8);
      misc.spawn(p[0] + R(0.8), p[1] + 0.2, p[2] + R(0.8), Math.cos(a) * s, 5 + Math.random() * (6 + k * 9), Math.sin(a) * s,
        1 + Math.random() * 0.8, 0.14 + Math.random() * 0.12 + k * 0.08, 0.12, Math.random() < 0.5 ? 0x8a7e6a : 0x5e554a, 0x3a342c, 1, 26, 0.3);
    }
    for (let i = 0; i < 12 + k * 20; i++) fire.spawn(p[0] + R(0.5), p[1] + 0.3, p[2] + R(0.5), R(11), 2 + Math.random() * 7, R(11), 0.25 + Math.random() * 0.2, 0.14, 0.04, 0xfff2b0, 0xff7a1a, 1, 18, 1);
  },
  update(dt) {
    fire.update(dt); smoke.update(dt); misc.update(dt); blood.update(dt);
    marbles.update(dt);
    for (let i = decals.length - 1; i >= 0; i--) {
      const m = decals[i];
      m.userData.life -= dt;
      if (m.userData.life < 1.5) m.material.opacity = Math.max(0, m.userData.life / 1.5) * 0.9;
      if (m.userData.life <= 0) { scene.remove(m); m.material.dispose(); decals.splice(i, 1); }
    }
    for (let i = timed.length - 1; i >= 0; i--) {
      const t = timed[i];
      t.life -= dt;
      const k = Math.max(0, t.life / t.ml);
      if (t.kind === 'flash') t.mesh.scale.setScalar(0.5 + (1 - k) * t.r);
      t.mesh.material.opacity = k;
      if (t.life <= 0) { scene.remove(t.mesh); t.mesh.material.dispose(); timed.splice(i, 1); }
    }
  },
};
