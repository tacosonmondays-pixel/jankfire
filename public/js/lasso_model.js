// Lasso models: the rope itself (a tube along a curve, rebuilt in place every frame, sagging when slack and dead
// straight when taut), the loop with its honda knot, the coil you carry, hands for the viewmodel, and the skins.
// Model space like every weapon: forward = -Z, up = +Y, the hand at the origin.
import * as THREE from 'three';
import { jankify } from './jank.js';

// ------------------------------------------------------------ what each skin's rope looks like
// twist = a three-strand hemp rope, rib = a garden hose. r = rope radius (m), knot = the honda (or the hose's nozzle)
export const ROPE_LOOK = {
  default: { kind: 'twist', c1: 0xd2a868, c2: 0x7a5228, r: 0.016, knot: 0x9a6a34, metal: null },
  lasso_hose: { kind: 'rib', c1: 0x2fa046, c2: 0x17642a, r: 0.022, knot: 0xd8a830, metal: 0xd8a830 },
};
export const ropeLook = (skin) => ROPE_LOOK[(Array.isArray(skin) && ROPE_LOOK[skin[3]]) ? skin[3] : 'default'];

const texCache = new Map();
function ropeTex(look) {
  const key = look.kind + look.c1 + look.c2;
  if (texCache.has(key)) return texCache.get(key);
  const c = document.createElement('canvas'); c.width = 32; c.height = 16;
  const x = c.getContext('2d');
  const hex = (n) => '#' + n.toString(16).padStart(6, '0');
  x.fillStyle = hex(look.c1); x.fillRect(0, 0, 32, 16);
  if (look.kind === 'twist') { // strands winding round: diagonal bands, a dark groove between each, a light ridge on each
    for (let px = 0; px < 32; px++) for (let py = 0; py < 16; py++) {
      const s = (px + py * 2) % 16;
      if (s < 2) { x.fillStyle = hex(look.c2); x.fillRect(px, py, 1, 1); } else if (s > 6 && s < 9) { x.fillStyle = 'rgba(255,240,210,0.35)'; x.fillRect(px, py, 1, 1); }
    }
  } else { // hose: ribs round it, a shiny stripe along it
    for (let px = 0; px < 32; px += 4) { x.fillStyle = hex(look.c2); x.fillRect(px, 0, 1, 16); }
    x.fillStyle = 'rgba(255,255,255,0.35)'; x.fillRect(0, 3, 32, 2);
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestFilter; t.colorSpace = THREE.SRGBColorSpace;
  texCache.set(key, t);
  return t;
}
const matCache = new Map();
export function ropeMat(look) {
  const key = look.kind + look.c1;
  if (!matCache.has(key)) matCache.set(key, jankify(new THREE.MeshLambertMaterial({ map: ropeTex(look) })));
  return matCache.get(key);
}
const flat = new Map();
function M(color) {
  if (!flat.has(color)) flat.set(color, jankify(new THREE.MeshLambertMaterial({ color, flatShading: true })));
  return flat.get(color);
}

// ------------------------------------------------------------ the rope: a tube through a list of points
// geometry is allocated once (n segments, m sides) and rewritten in place every frame
const _t = new THREE.Vector3(), _n = new THREE.Vector3(), _b = new THREE.Vector3(), _p = new THREE.Vector3(), _q = new THREE.Vector3();
export class Rope {
  constructor(look, n = 28, m = 6) {
    this.n = n; this.m = m; this.look = look;
    const verts = (n + 1) * (m + 1);
    const g = new THREE.BufferGeometry();
    this.pos = new Float32Array(verts * 3); this.nrm = new Float32Array(verts * 3); this.uv = new Float32Array(verts * 2);
    g.setAttribute('position', new THREE.BufferAttribute(this.pos, 3));
    g.setAttribute('normal', new THREE.BufferAttribute(this.nrm, 3));
    g.setAttribute('uv', new THREE.BufferAttribute(this.uv, 2));
    const idx = [];
    for (let i = 0; i < n; i++) for (let j = 0; j < m; j++) {
      const a = i * (m + 1) + j, b = a + m + 1;
      idx.push(a, b, a + 1, b, b + 1, a + 1);
    }
    g.setIndex(idx);
    this.geo = g;
    this.mesh = new THREE.Mesh(g, ropeMat(look));
    this.mesh.frustumCulled = false; // its bounds change every frame
    this.pts = Array.from({ length: n + 1 }, () => new THREE.Vector3());
  }
  setLook(look) { if (look !== this.look) { this.look = look; this.mesh.material = ropeMat(look); } }
  // pts: this.pts (n + 1 points, filled by the caller). r = radius, r1 = radius at the far end (tapers)
  update(r = this.look.r, r1 = r) {
    const { n, m, pts, pos, nrm, uv } = this;
    let s = 0;
    _n.set(0, 0, 0);
    for (let i = 0; i <= n; i++) {
      const p = pts[i];
      if (i < n) _t.subVectors(pts[i + 1], p); else _t.subVectors(p, pts[i - 1]);
      if (i > 0 && i < n) _t.add(_q.subVectors(p, pts[i - 1]));
      if (_t.lengthSq() < 1e-12) _t.set(0, 0, -1);
      _t.normalize();
      // a frame that follows the curve without twisting (parallel transport)
      if (i === 0) { _n.set(0, 1, 0); if (Math.abs(_t.y) > 0.9) _n.set(1, 0, 0); }
      _n.addScaledVector(_t, -_n.dot(_t));
      if (_n.lengthSq() < 1e-8) _n.set(_t.z, 0, -_t.x);
      _n.normalize();
      _b.crossVectors(_t, _n);
      if (i > 0) s += p.distanceTo(pts[i - 1]);
      const rr = r + (r1 - r) * (i / n);
      for (let j = 0; j <= m; j++) {
        const a = (j / m) * Math.PI * 2, ca = Math.cos(a), sa = Math.sin(a), k = (i * (m + 1) + j) * 3;
        const nx = _n.x * ca + _b.x * sa, ny = _n.y * ca + _b.y * sa, nz = _n.z * ca + _b.z * sa;
        pos[k] = p.x + nx * rr; pos[k + 1] = p.y + ny * rr; pos[k + 2] = p.z + nz * rr;
        nrm[k] = nx; nrm[k + 1] = ny; nrm[k + 2] = nz;
        const u = (i * (m + 1) + j) * 2;
        uv[u] = s * 22; uv[u + 1] = j / m;
      }
    }
    this.geo.attributes.position.needsUpdate = true;
    this.geo.attributes.normal.needsUpdate = true;
    this.geo.attributes.uv.needsUpdate = true;
    this.len = s;
  }
}

// a rope from a to b that's len long: dead straight once it's taut, otherwise it hangs in a curve (a parabola is
// close enough to a catenary at these sags). wave = a travelling ripple (a rope paying out, the whip after a fling)
export function sagRope(rope, a, b, len, o = {}) {
  const pts = rope.pts, n = rope.n;
  const dx = b[0] - a[0], dy = b[1] - a[1], dz = b[2] - a[2], d = Math.hypot(dx, dy, dz) || 1e-6;
  // sag depth for a rope len long across d: arc ~ d + 8 s^2 / (3 d)
  const s = len > d ? Math.sqrt((3 * d * (len - d)) / 8) : 0;
  // hang straight down, minus whatever of "down" runs along the rope
  const ux = dx / d, uy = dy / d, uz = dz / d;
  let gx = -ux * -uy, gy = -1 - uy * -uy, gz = -uz * -uy;
  const gl = Math.hypot(gx, gy, gz);
  if (gl > 1e-4) { gx /= gl; gy /= gl; gz /= gl; } else { gx = 0; gy = 0; gz = 0; }
  // the wave goes sideways to the rope
  let wx = -uz, wz = ux; const wl = Math.hypot(wx, wz) || 1; wx /= wl; wz /= wl;
  const wave = o.wave || 0, wf = o.wf || 3, wt = o.wt || 0, hum = o.hum || 0;
  for (let i = 0; i <= n; i++) {
    const t = i / n, bow = 4 * t * (1 - t);
    const sg = s * bow * (o.sagK ?? 1);
    const wv = wave * Math.sin(t * Math.PI * wf - wt) * Math.sin(t * Math.PI) + hum * Math.sin(t * Math.PI * 7 + wt * 3) * bow;
    pts[i].set(a[0] + dx * t + gx * sg + wx * wv, a[1] + dy * t + gy * sg + wv * 0.3, a[2] + dz * t + gz * sg + wz * wv);
  }
  rope.update(o.r, o.r1);
  return s;
}

// points round a ring: centre c, in the plane of unit vectors u + v, radius r. the last point closes it. lump = how much
// the honda end pinches in (a real loop is a teardrop), seam = angle the rope comes out at
export function ringPoints(pts, c, u, v, r, o = {}) {
  const n = pts.length - 1, a0 = o.seam ?? 0, wob = o.wob || 0, wt = o.wt || 0, tear = o.tear ?? 0.18;
  const nx = o.nx ?? 0, ny = o.ny ?? 1, nz = o.nz ?? 0;
  for (let i = 0; i <= n; i++) {
    const a = a0 + (i / n) * Math.PI * 2;
    // teardrop: pinched toward the knot (a0), round on the far side; a little wobble while it flies
    const pinch = 1 - tear * Math.pow(0.5 + 0.5 * Math.cos(a - a0), 6);
    const rr = r * pinch * (1 + wob * Math.sin(a * 3 + wt));
    const x = Math.cos(a) * rr, y = Math.sin(a) * rr, h = wob * r * 0.5 * Math.sin(a * 2 - wt * 1.3);
    pts[i].set(c[0] + u[0] * x + v[0] * y + nx * h, c[1] + u[1] * x + v[1] * y + ny * h, c[2] + u[2] * x + v[2] * y + nz * h);
  }
}

// the honda: the little knot (or the hose's brass nozzle) where the rope runs through to make the loop
export function honda(look, s = 1) {
  const g = new THREE.Group();
  if (look.metal) {
    const nz = new THREE.Mesh(new THREE.CylinderGeometry(0.018 * s, 0.026 * s, 0.07 * s, 8), M(look.metal));
    nz.rotation.z = Math.PI / 2; g.add(nz);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.024 * s, 0.006 * s, 4, 10), M(0xb08020)); ring.rotation.y = Math.PI / 2; ring.position.x = 0.03 * s; g.add(ring);
  } else {
    const k = new THREE.Mesh(new THREE.SphereGeometry(0.028 * s, 7, 5), ropeMat(look)); k.scale.set(1.5, 0.95, 0.95); g.add(k);
    const eye = new THREE.Mesh(new THREE.TorusGeometry(0.02 * s, 0.009 * s, 4, 8), ropeMat(look)); eye.position.x = 0.04 * s; eye.rotation.y = Math.PI / 2; g.add(eye);
    const wrap = new THREE.Mesh(new THREE.CylinderGeometry(0.019 * s, 0.019 * s, 0.03 * s, 6), M(look.knot)); wrap.rotation.z = Math.PI / 2; wrap.position.x = -0.02 * s; g.add(wrap);
  }
  return g;
}

// ------------------------------------------------------------ the coiled lasso (hotbar, third person, your off hand)
// a hank of rope: loose loops in the YZ plane hanging off the hand (the top of every loop is in the fist, at the
// origin), each a bit bigger or smaller than the last and fanned out a little at the bottom, a few turns of the
// tail wrapped round where the hand holds them. o.R = loop size, o.rk = rope thickness (x the skin's), o.loops
export function coilGroup(look, o = {}) {
  const g = new THREE.Group(), mat = ropeMat(look), r = look.r * (o.rk ?? 1.1);
  const R = o.R || 0.13, loops = o.loops || 5;
  for (let i = 0; i < loops; i++) {
    const k = i - (loops - 1) / 2, Ri = R * (1 + 0.09 * Math.sin(i * 2.4 + 0.7));
    const piv = new THREE.Group(); // pivots at the fist: bunched up there, fanned out a little at the bottom
    piv.rotation.set(k * 0.13 + 0.04 * Math.sin(i * 3.1), 0, k * 0.09);
    const t = new THREE.Mesh(new THREE.TorusGeometry(Ri, r, 5, 20), mat);
    t.rotation.y = Math.PI / 2; // ring in the YZ plane
    t.scale.set(1, 1.2, 1); // loops hang long
    t.position.set(k * r * 2.05, -Ri * 1.2, 0);
    piv.add(t);
    g.add(piv);
  }
  // two turns of the tail round the bundle, either side of where the hand holds it
  const hw = ((loops - 1) * r * 2.05) / 2 + r * 1.4;
  for (const z of [-0.3, 0.3]) {
    const wrap = new THREE.Mesh(new THREE.TorusGeometry(hw, r * 0.75, 4, 12), mat);
    wrap.scale.set(1, Math.max(0.3, (r * 2) / hw), 1); wrap.position.set(0, 0, z * R);
    g.add(wrap);
  }
  return g;
}
export function buildLassoModel(g, look) {
  const coil = coilGroup(look, { loops: 4, rk: 1 });
  g.add(coil);
  const kn = lassoLoop(g, look);
  if (look.metal) { const cup = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.05, 8), M(look.metal)); cup.position.set(-0.08, -0.02, 0.02); cup.rotation.z = 0.4; g.add(cup); } // the hose's tap end
  // wrap zones (wrapzones.js): the rope is A (normal wraps paint it), the knot / brass nozzle + tap are B (reverse)
  g.traverse((o) => { if (o.isMesh) o.userData.wz = 'a'; });
  kn.traverse((o) => { if (o.isMesh) o.userData.wz = 'b'; });
  if (look.metal) g.children[g.children.length - 1].userData.wz = 'b';
  g.userData.muzzle = new THREE.Vector3(0.03, -0.03, -0.04); // the working end leaves the fist here
  g.userData.len = 0.4;
  g.userData.faceOn = false;
  return g;
}
// the loop hanging down beside the coil, its knot at the top, the spoke up to the fist: simulated rope, so the Blender
// coil keeps this one too. returns the knot (wrap zone B); sets userData.loopParts (hidden while the loop is out)
export function lassoLoop(g, look) {
  const X = 0.075, rope = new Rope(look, 22, 6);
  ringPoints(rope.pts, [X, -0.27, -0.06], [0, 1, 0], [0, 0, 1], 0.12, { seam: Math.PI / 2, nx: 1, ny: 0, nz: 0 });
  rope.update(look.r * 1.1);
  rope.mesh.frustumCulled = true; rope.geo.computeBoundingSphere();
  g.add(rope.mesh);
  const kn = honda(look, 1.1); kn.position.set(X, -0.15, -0.06); kn.rotation.z = Math.PI / 2; g.add(kn);
  const sp = new Rope(look, 6, 6);
  for (let i = 0; i <= 6; i++) { const t = i / 6; sp.pts[i].set(X + (0.02 - X) * t, -0.15 + 0.14 * t, -0.06 * (1 - t)); }
  sp.update(look.r * 1.1); sp.mesh.frustumCulled = true; sp.geo.computeBoundingSphere();
  g.add(sp.mesh);
  rope.mesh.userData.wz = 'a'; sp.mesh.userData.wz = 'a';
  kn.traverse((o) => { if (o.isMesh) o.userData.wz = 'b'; });
  g.userData.loopParts = [rope.mesh, kn, sp.mesh]; // hidden while the loop is out (spinning, flying, round someone)
  return kn;
}
// weapon builders + skins (models.js registers these like the blades)
export const LASSO_MODELS = {
  lasso: { build: (g) => buildLassoModel(g, ROPE_LOOK.default), hatAt: [[0, 0.04, 0], 0.07] },
  lasso_hose: { build: (g) => buildLassoModel(g, ROPE_LOOK.lasso_hose), hatAt: [[0, 0.05, 0], 0.07] },
};

// the loop in flight when nobody's animating it (replays, late joiners): an open ring + knot, facing up
export function buildLoopProjectile(g, look = ROPE_LOOK.default) {
  const rope = new Rope(look, 26, 6);
  ringPoints(rope.pts, [0, 0, 0], [1, 0, 0], [0, 0, 1], 0.55, { seam: Math.PI / 2, nx: 0, ny: 1, nz: 0 });
  rope.update(look.r * 1.4);
  g.add(rope.mesh);
  const kn = honda(look, 1.4); kn.position.set(0, 0, 0.5); kn.rotation.y = Math.PI / 2; g.add(kn);
  g.userData.loopRope = rope;
  return g;
}

// ------------------------------------------------------------ viewmodel hands
// a forearm + gloved hand gripping a rope (fingers curled round it): rope work is done in leather work gloves, a
// stitched gauntlet cuff flaring over the sleeve. sleeve = your character's top colour (rolled up, a darker turn-up)
export function vmArm(skin = 0xe6cba2, sleeve = 0x3a5aa0, glove = 0x8a5228) {
  const g = new THREE.Group();
  const dk = (c, k) => new THREE.Color(c).multiplyScalar(k).getHex();
  const fore = new THREE.Mesh(new THREE.CylinderGeometry(0.026, 0.033, 0.42, 8), M(sleeve)); // long enough to always run off the screen
  fore.rotation.x = Math.PI / 2; fore.position.z = 0.29; g.add(fore);
  const roll = new THREE.Mesh(new THREE.TorusGeometry(0.03, 0.009, 5, 10), M(dk(sleeve, 0.72))); roll.position.z = 0.085; g.add(roll); // the rolled-up sleeve
  const skinB = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.025, 0.05, 8), M(skin)); skinB.rotation.x = Math.PI / 2; skinB.position.z = 0.055; g.add(skinB); // a bit of wrist
  // the gauntlet: flares out toward the elbow, a stitched seam round its edge
  const gaunt = new THREE.Mesh(new THREE.CylinderGeometry(0.023, 0.032, 0.05, 8), M(dk(glove, 0.9))); gaunt.rotation.x = Math.PI / 2; gaunt.position.z = 0.022; g.add(gaunt);
  const seam = new THREE.Mesh(new THREE.TorusGeometry(0.031, 0.0035, 4, 12), M(0xe8c890)); seam.position.z = 0.046; g.add(seam);
  const palm = new THREE.Mesh(new THREE.BoxGeometry(0.052, 0.032, 0.062), M(glove)); palm.position.set(0, 0, -0.03); g.add(palm);
  const back = new THREE.Mesh(new THREE.BoxGeometry(0.044, 0.006, 0.04), M(dk(glove, 1.18))); back.position.set(0, 0.018, -0.028); g.add(back); // the padded back of the hand
  // four fingers curled over the top of the rope, the thumb wrapped under it, knuckles a shade lighter (worn leather)
  for (let i = 0; i < 4; i++) {
    const x = -0.019 + i * 0.0125;
    const k = new THREE.Mesh(new THREE.BoxGeometry(0.0115, 0.017, 0.016), M(dk(glove, 1.12))); k.position.set(x, 0.012, -0.058); g.add(k);
    const f = new THREE.Mesh(new THREE.BoxGeometry(0.0108, 0.016, 0.026), M(glove)); f.position.set(x, 0.01, -0.071); f.rotation.x = 0.9; g.add(f);
    const tip = new THREE.Mesh(new THREE.BoxGeometry(0.0102, 0.014, 0.02), M(dk(glove, 0.85))); tip.position.set(x, -0.006, -0.082); tip.rotation.x = 2.1; g.add(tip);
  }
  const th = new THREE.Mesh(new THREE.BoxGeometry(0.014, 0.014, 0.036), M(glove)); th.position.set(0.027, -0.012, -0.05); th.rotation.set(-0.5, -0.5, 0); g.add(th);
  g.userData.grip = new THREE.Vector3(0, 0.0, -0.07); // where the rope runs through the fist
  return g;
}
