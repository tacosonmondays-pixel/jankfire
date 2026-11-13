// flying bits: brass casings, shotgun shells, marbles and rubble as small real meshes (Blender: x_fx_bits.glb, made by
// tools/blender/make_fx_bits.py), instead of square particles (the owner: "the bits spitting out are pretty clunky,
// its not very smooth"). Every bit moves every frame: a proper arc, a tumble, a bounce or two off the floor with a
// rattle of spin, then it shrinks away instead of popping. One instanced mesh per bit kind per scene (the world, and
// the gun's own scene for your casings): a few draws however many fly, and nothing is created per bit (no garbage, no
// new materials). Until the model file lands (or if it never does) code shapes stand in.
import * as THREE from 'three';
import { G } from './ctx.js';
import { AUTHORED, prefetch, onGlb } from './glbkit.js';
import { raycast } from '/shared/physics.js';
import { BOXES } from '/shared/map.js';

// per kind: the model's node, its radius (m, for landing on the floor), how many at once in the world / your gun
export const BITS = {
  casing: { node: 'bit_casing', r: 0.005, max: { world: 96, vm: 48 } },
  shell: { node: 'bit_shell', r: 0.01, max: { world: 48, vm: 16 } },
  marble: { node: 'bit_marble', r: 0.008, max: { world: 64, vm: 8 } },
  chunk_a: { node: 'bit_chunk_a', r: 0.03, max: { world: 96, vm: 4 } },
  chunk_b: { node: 'bit_chunk_b', r: 0.02, max: { world: 96, vm: 4 } },
  chunk_c: { node: 'bit_chunk_c', r: 0.012, max: { world: 96, vm: 4 } },
  bounce: 0.38, // how much of the fall comes back up on a bounce
  bounces: 2, // then it slides to a stop
  fade: 0.35, // seconds it takes to shrink away at the end
};
const ID = 'x_fx_bits';
const pools = new Map(); // `${kind}|${where}` -> pool
let wantModel = false;
const _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _dq = new THREE.Quaternion(), _p = new THREE.Vector3(), _s = new THREE.Vector3(), _e = new THREE.Euler(), _c = new THREE.Color(), _ax = new THREE.Vector3();

// the stand-ins (before the model lands): a brass tube, a red tube, a ball, a lump
let codeGeo = null;
function standIn(kind) {
  if (!codeGeo) codeGeo = {
    casing: [new THREE.CylinderGeometry(0.0046, 0.0046, 0.045, 8).rotateX(Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xd9a53a, metalness: 0.9, roughness: 0.3 })],
    shell: [new THREE.CylinderGeometry(0.0095, 0.0095, 0.07, 10).rotateX(Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xd02424, roughness: 0.35 })],
    marble: [new THREE.IcosahedronGeometry(0.008, 1), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.08 })],
    chunk: [new THREE.DodecahedronGeometry(0.025, 0), new THREE.MeshStandardMaterial({ color: 0xd8d2c6, roughness: 0.9, flatShading: true })],
  };
  const [g, m] = codeGeo[kind.startsWith('chunk') ? 'chunk' : kind];
  return [{ geo: g, mat: m }];
}
// the model's pieces for a kind: each mesh under its node, its geometry moved so the node's origin is the middle
function fromModel(kind) {
  const a = AUTHORED[ID];
  if (!a) return null;
  let node = null;
  a.scene.traverse((o) => { if (!node && o.name === BITS[kind].node) node = o; });
  if (!node) return null;
  const out = [];
  node.updateWorldMatrix(true, true);
  const inv = new THREE.Matrix4().copy(node.matrixWorld).invert();
  node.traverse((o) => { if (!o.isMesh) return; const g = o.geometry.clone().applyMatrix4(_m.multiplyMatrices(inv, o.matrixWorld)); out.push({ geo: g, mat: o.material }); });
  return out.length ? out : null;
}

function makePool(kind, where) {
  const scene = where === 'vm' ? G.vmScene : G.scene;
  if (!scene) return null;
  const max = BITS[kind].max[where];
  const parts = fromModel(kind) || standIn(kind);
  const meshes = parts.map(({ geo, mat }) => {
    const im = new THREE.InstancedMesh(geo, mat, max);
    im.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    im.setColorAt(0, _c.set(0xffffff)); im.instanceColor.setUsage(THREE.DynamicDrawUsage);
    im.count = 0; im.frustumCulled = false; im.castShadow = false; im.receiveShadow = where === 'world';
    im.name = 'bits_' + kind; im.userData.noWrap = true;
    scene.add(im);
    return im;
  });
  return {
    kind, where, scene, max, n: 0, model: !!fromModel(kind), meshes,
    p: new Float32Array(max * 3), v: new Float32Array(max * 3), q: new Float32Array(max * 4), av: new Float32Array(max * 3),
    s: new Float32Array(max), life: new Float32Array(max), floor: new Float32Array(max), probe: new Float32Array(max),
    hops: new Uint8Array(max), grav: new Float32Array(max), col: new Float32Array(max * 3), r: BITS[kind].r,
  };
}
function poolOf(kind, where) {
  if (!wantModel) { wantModel = true; prefetch([ID], 1); }
  const key = kind + '|' + where;
  let P = pools.get(key);
  if (P && P.scene !== (where === 'vm' ? G.vmScene : G.scene)) { drop(P); P = null; } // (a new scene: start over)
  if (!P) { P = makePool(kind, where); if (P) pools.set(key, P); }
  return P;
}
function drop(P) { for (const im of P.meshes) { im.removeFromParent(); im.dispose(); } pools.delete(P.kind + '|' + P.where); }
// the model landed: swap the stand-ins out (whatever is flying keeps flying, in the new shape)
onGlb((id) => {
  if (id !== ID) return;
  for (const P of [...pools.values()]) {
    if (P.model) continue;
    const old = P.meshes, parts = fromModel(P.kind);
    if (!parts) continue;
    P.meshes = parts.map(({ geo, mat }) => { const im = new THREE.InstancedMesh(geo, mat, P.max); im.instanceMatrix.setUsage(THREE.DynamicDrawUsage); im.setColorAt(0, _c.set(0xffffff)); im.count = 0; im.frustumCulled = false; im.castShadow = false; im.receiveShadow = old[0].receiveShadow; im.name = old[0].name; im.userData.noWrap = true; P.scene.add(im); return im; });
    for (const im of old) { im.removeFromParent(); im.dispose(); }
    P.model = true;
  }
});

const floorAt = (x, y, z) => { const h = raycast([x, y + 0.05, z], [0, -1, 0], 40, BOXES); return h ? y + 0.05 - h.t : -1e9; };
// one bit. where: 'world' (lands on the floor) or 'vm' (your gun's scene: no floor, it falls out of view)
// o: { life, scale, color, spin (rad/s), grav, quat (a THREE.Quaternion to start from), floor: false (no landing) }
export function spawnBit(kind, where, p, v, o = {}) {
  const P = poolOf(kind, where);
  if (!P) return;
  let i = P.n;
  if (i >= P.max) { i = 0; let lo = Infinity; for (let k = 0; k < P.max; k++) if (P.life[k] < lo) { lo = P.life[k]; i = k; } } // full: the one closest to gone makes room
  else P.n++;
  const i3 = i * 3, i4 = i * 4;
  P.p[i3] = p[0]; P.p[i3 + 1] = p[1]; P.p[i3 + 2] = p[2];
  P.v[i3] = v[0]; P.v[i3 + 1] = v[1]; P.v[i3 + 2] = v[2];
  if (o.quat) { P.q[i4] = o.quat.x; P.q[i4 + 1] = o.quat.y; P.q[i4 + 2] = o.quat.z; P.q[i4 + 3] = o.quat.w; }
  else { _q.setFromEuler(_e.set(Math.random() * 6.28, Math.random() * 6.28, Math.random() * 6.28)); P.q[i4] = _q.x; P.q[i4 + 1] = _q.y; P.q[i4 + 2] = _q.z; P.q[i4 + 3] = _q.w; }
  const sp = o.spin ?? 14;
  _ax.set(Math.random() - 0.5, Math.random() - 0.5, Math.random() - 0.5).normalize().multiplyScalar(sp * (0.6 + Math.random() * 0.8));
  P.av[i3] = _ax.x; P.av[i3 + 1] = _ax.y; P.av[i3 + 2] = _ax.z;
  P.s[i] = o.scale || 1; P.life[i] = o.life || 1.5; P.grav[i] = o.grav ?? 9.8; P.hops[i] = 0; P.probe[i] = 0;
  P.floor[i] = where === 'world' && o.floor !== false ? floorAt(p[0], p[1], p[2]) : -1e9;
  _c.set(o.color ?? 0xffffff); P.col[i3] = _c.r; P.col[i3 + 1] = _c.g; P.col[i3 + 2] = _c.b;
}
function kill(P, i) { // the last one moves into its place
  const j = --P.n; if (i === j) return;
  const i3 = i * 3, j3 = j * 3, i4 = i * 4, j4 = j * 4;
  for (const a of [P.p, P.v, P.av, P.col]) { a[i3] = a[j3]; a[i3 + 1] = a[j3 + 1]; a[i3 + 2] = a[j3 + 2]; }
  for (let k = 0; k < 4; k++) P.q[i4 + k] = P.q[j4 + k];
  P.s[i] = P.s[j]; P.life[i] = P.life[j]; P.floor[i] = P.floor[j]; P.probe[i] = P.probe[j]; P.hops[i] = P.hops[j]; P.grav[i] = P.grav[j];
}
// every frame (fx.update): move, tumble, bounce, shrink away
export function updateBits(dt) {
  if (!pools.size) return;
  dt = Math.min(dt, 0.05);
  for (const P of pools.values()) {
    if (!P.n && !P.meshes[0].count) continue;
    for (let i = 0; i < P.n; i++) {
      P.life[i] -= dt;
      if (P.life[i] <= 0) { kill(P, i); i--; continue; }
      const i3 = i * 3, i4 = i * 4;
      let vx = P.v[i3], vy = P.v[i3 + 1] - P.grav[i] * dt, vz = P.v[i3 + 2];
      let x = P.p[i3] + vx * dt, y = P.p[i3 + 1] + vy * dt, z = P.p[i3 + 2] + vz * dt;
      let spinK = 1;
      if (P.floor[i] > -1e8) {
        if ((P.probe[i] -= dt) <= 0 && (vx || vz)) { P.probe[i] = 0.2; P.floor[i] = floorAt(x, Math.max(y, P.floor[i] + P.r), z); } // (slid off a ledge? look again now and then)
        const fy = P.floor[i] + P.r;
        if (y < fy) {
          y = fy;
          if (vy < -0.8 && P.hops[i] < BITS.bounces) { vy = -vy * BITS.bounce; vx *= 0.6; vz *= 0.6; P.hops[i]++; for (let k = 0; k < 3; k++) P.av[i3 + k] *= 0.6; } // a bounce: less speed, still spinning
          else { vy = 0; const f = Math.max(0, 1 - dt * 7); vx *= f; vz *= f; for (let k = 0; k < 3; k++) P.av[i3 + k] *= f; spinK = 0.5; } // sliding to a stop
        }
      }
      P.v[i3] = vx; P.v[i3 + 1] = vy; P.v[i3 + 2] = vz; P.p[i3] = x; P.p[i3 + 1] = y; P.p[i3 + 2] = z;
      // tumble: turn by the spin for this frame
      const ax = P.av[i3] * dt * spinK, ay = P.av[i3 + 1] * dt * spinK, az = P.av[i3 + 2] * dt * spinK, ang = Math.hypot(ax, ay, az);
      _q.set(P.q[i4], P.q[i4 + 1], P.q[i4 + 2], P.q[i4 + 3]);
      if (ang > 1e-6) { _dq.setFromAxisAngle(_ax.set(ax / ang, ay / ang, az / ang), ang); _q.premultiply(_dq); P.q[i4] = _q.x; P.q[i4 + 1] = _q.y; P.q[i4 + 2] = _q.z; P.q[i4 + 3] = _q.w; }
      const k = P.life[i] < BITS.fade ? P.life[i] / BITS.fade : 1, sc = P.s[i] * k * (2 - k); // (ease out: shrinks smoothly to nothing)
      _m.compose(_p.set(x, y, z), _q, _s.set(sc, sc, sc));
      for (const im of P.meshes) { im.setMatrixAt(i, _m); im.instanceColor.setXYZ(i, P.col[i3], P.col[i3 + 1], P.col[i3 + 2]); }
    }
    for (const im of P.meshes) { im.count = P.n; im.instanceMatrix.needsUpdate = true; if (im.instanceColor) im.instanceColor.needsUpdate = true; }
  }
}
export const bitsInfo = () => [...pools.values()].map((P) => ({ kind: P.kind, where: P.where, n: P.n, model: P.model }));
export function clearBits() { for (const P of pools.values()) { P.n = 0; for (const im of P.meshes) im.count = 0; } }
