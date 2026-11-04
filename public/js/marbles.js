// Marbles from the Marble Shotgun. Damage is hitscan (decided when you fire); these are the visible marbles:
// they fly out along the pellet paths, bounce off whatever they hit, then rattle and roll round the floor for a few seconds.
import * as THREE from 'three';
import { raycast } from '/shared/physics.js';
import { BOXES } from '/shared/map.js';
import { jankify } from './jank.js';
import { sfx } from './audio.js';

const MAX = 520, RAD = 0.026, SPEED = 70, GRAV = 22;
const PALETTES = {
  glass: [0x2f7bff, 0x19c37d, 0xff4f4f, 0xffd23b, 0xb07dff, 0xff8a1a, 0xe8f6ff, 0x37d6ff, 0x9aff4f],
  gumball: [0xff2e63, 0xffd400, 0x00c2ff, 0x7dff4f, 0xff7a1a, 0xffffff, 0xb07dff, 0xff4fd8],
};
const P = new Float32Array(MAX * 3), V = new Float32Array(MAX * 3); // position, velocity
const A = new Float32Array(MAX * 3), D = new Float32Array(MAX * 3), N = new Float32Array(MAX * 3); // flight start, direction, hit normal
const flyT = new Float32Array(MAX), flyLen = new Float32Array(MAX), life = new Float32Array(MAX), floorY = new Float32Array(MAX);
const probe = new Float32Array(MAX * 2), spin = new Float32Array(MAX);
const state = new Uint8Array(MAX), hitKind = new Uint8Array(MAX); // state: 0 off, 1 flying, 2 bouncing, 3 rolling. hit: 0 air, 1 wall, 2 player
let mesh = null, next = 0, live = 0, clackT = 0;
const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), sc = new THREE.Vector3(), pv = new THREE.Vector3(), col = new THREE.Color();
const axis = new THREE.Vector3();

function floorUnder(x, y, z) {
  const h = raycast([x, y + 0.25, z], [0, -1, 0], 80, BOXES);
  return h ? y + 0.25 - h.t : -1e4;
}

export const marbles = {
  init(scene) {
    const mat = jankify(new THREE.MeshPhongMaterial({ color: 0xffffff, shininess: 90, specular: 0x666666, flatShading: true }));
    mesh = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(RAD, 1), mat, MAX);
    mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    mesh.frustumCulled = false;
    m4.makeScale(0, 0, 0);
    for (let i = 0; i < MAX; i++) { mesh.setMatrixAt(i, m4); mesh.setColorAt(i, col.setHex(0xffffff)); }
    scene.add(mesh);
  },
  // shots: [{ a: [x,y,z] from, b: [x,y,z] to, n: wall normal or null, player: bool }]
  shoot(shots, palette = 'glass') {
    if (!mesh) return;
    const pal = PALETTES[palette] || PALETTES.glass;
    for (const s of shots) {
      const i = next; next = (next + 1) % MAX;
      if (!state[i]) live++;
      const dx = s.b[0] - s.a[0], dy = s.b[1] - s.a[1], dz = s.b[2] - s.a[2], L = Math.hypot(dx, dy, dz) || 1e-3;
      const i3 = i * 3;
      A[i3] = s.a[0]; A[i3 + 1] = s.a[1]; A[i3 + 2] = s.a[2];
      D[i3] = dx / L; D[i3 + 1] = dy / L; D[i3 + 2] = dz / L;
      P[i3] = s.a[0]; P[i3 + 1] = s.a[1]; P[i3 + 2] = s.a[2];
      const n = s.n || [0, 1, 0];
      N[i3] = n[0]; N[i3 + 1] = n[1]; N[i3 + 2] = n[2];
      hitKind[i] = s.player ? 2 : s.n ? 1 : 0;
      flyT[i] = -Math.random() * 0.04 * SPEED; // a ragged cloud, not a flat disc
      flyLen[i] = L; state[i] = 1;
      life[i] = 3.5 + Math.random() * 2.5; spin[i] = 0;
      mesh.setColorAt(i, col.setHex(pal[(Math.random() * pal.length) | 0]));
    }
    mesh.instanceColor.needsUpdate = true;
  },
  // other players / replays only send a dozen pellet paths: find the walls they ended on and spray extra marbles round them
  shootSegs(segs, muzzle, palette, extra = 3) {
    const shots = [];
    for (const s of segs || []) {
      if (!Array.isArray(s) || s.length < 6) continue;
      const a = muzzle || s.slice(0, 3);
      for (let k = 0; k <= extra; k++) {
        let b = s.slice(3, 6);
        if (k) { const L = Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]), j = 0.06 * L; b = [b[0] + (Math.random() - 0.5) * j, b[1] + (Math.random() - 0.5) * j, b[2] + (Math.random() - 0.5) * j]; }
        const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], L = Math.hypot(...d) || 1;
        const h = raycast(a, d.map((x) => x / L), L + 0.3, BOXES);
        if (h) {
          const n = [0, 0, 0]; n[h.axis] = h.sign;
          shots.push({ a, b: a.map((v, j) => v + (d[j] / L) * h.t), n });
        } else shots.push({ a, b, n: null, player: L < 29 });
      }
    }
    marbles.shoot(shots, palette);
  },
  clear() {
    if (!mesh) return;
    state.fill(0); live = 0;
    m4.makeScale(0, 0, 0);
    for (let i = 0; i < MAX; i++) mesh.setMatrixAt(i, m4);
    mesh.instanceMatrix.needsUpdate = true;
  },
  update(dt, camPos) {
    if (!mesh || !live) return;
    dt = Math.min(dt, 0.05);
    clackT -= dt;
    let alive = 0;
    for (let i = 0; i < MAX; i++) {
      const st = state[i];
      if (!st) continue;
      const i3 = i * 3;
      life[i] -= dt;
      if (life[i] <= 0) { state[i] = 0; m4.makeScale(0, 0, 0); mesh.setMatrixAt(i, m4); continue; }
      alive++;
      if (st === 1) { // flying out along its pellet path
        flyT[i] += dt * SPEED;
        const t = Math.max(0, Math.min(flyLen[i], flyT[i]));
        P[i3] = A[i3] + D[i3] * t; P[i3 + 1] = A[i3 + 1] + D[i3 + 1] * t; P[i3 + 2] = A[i3 + 2] + D[i3 + 2] * t;
        if (flyT[i] >= flyLen[i]) {
          const hk = hitKind[i];
          if (hk === 1) { // bounce off the wall/floor it hit
            const nx = N[i3], ny = N[i3 + 1], nz = N[i3 + 2], dn = D[i3] * nx + D[i3 + 1] * ny + D[i3 + 2] * nz;
            const sp = SPEED * (0.12 + Math.random() * 0.14);
            V[i3] = (D[i3] - 2 * dn * nx) * sp + (Math.random() - 0.5) * 2;
            V[i3 + 1] = (D[i3 + 1] - 2 * dn * ny) * sp + Math.random() * 2;
            V[i3 + 2] = (D[i3 + 2] - 2 * dn * nz) * sp + (Math.random() - 0.5) * 2;
            P[i3] += nx * RAD; P[i3 + 1] += ny * RAD; P[i3 + 2] += nz * RAD;
            if (clackT <= 0 && Math.random() < 0.25) { sfx.marble([P[i3], P[i3 + 1], P[i3 + 2]]); clackT = 0.035; }
          } else if (hk === 2) { // hit someone: drop off them
            V[i3] = -D[i3] * 2.5 + (Math.random() - 0.5) * 2; V[i3 + 1] = 1 + Math.random() * 2; V[i3 + 2] = -D[i3 + 2] * 2.5 + (Math.random() - 0.5) * 2;
          } else { V[i3] = D[i3] * SPEED * 0.2; V[i3 + 1] = D[i3 + 1] * SPEED * 0.2; V[i3 + 2] = D[i3 + 2] * SPEED * 0.2; }
          floorY[i] = floorUnder(P[i3], P[i3 + 1], P[i3 + 2]);
          probe[i * 2] = P[i3]; probe[i * 2 + 1] = P[i3 + 2];
          state[i] = 2;
        }
      } else { // bouncing / rolling on the floor
        const hs = Math.hypot(V[i3], V[i3 + 2]);
        if (hs > 2.5) { // fast enough to matter: don't roll through walls
          const step = hs * dt + RAD;
          const h = raycast([P[i3], P[i3 + 1], P[i3 + 2]], [V[i3] / hs, 0, V[i3 + 2] / hs], step, BOXES);
          if (h && h.axis !== 1) { if (h.axis === 0) V[i3] *= -0.5; else V[i3 + 2] *= -0.5; }
        }
        if (st === 2) V[i3 + 1] -= GRAV * dt;
        P[i3] += V[i3] * dt; P[i3 + 1] += V[i3 + 1] * dt; P[i3 + 2] += V[i3 + 2] * dt;
        // moved far enough to be over different ground? look again
        if (Math.abs(P[i3] - probe[i * 2]) + Math.abs(P[i3 + 2] - probe[i * 2 + 1]) > 0.4) {
          floorY[i] = floorUnder(P[i3], P[i3 + 1], P[i3 + 2]);
          probe[i * 2] = P[i3]; probe[i * 2 + 1] = P[i3 + 2];
          if (st === 3 && floorY[i] < P[i3 + 1] - RAD - 0.03) state[i] = 2; // rolled off an edge
        }
        if (P[i3 + 1] - RAD <= floorY[i]) {
          P[i3 + 1] = floorY[i] + RAD;
          if (V[i3 + 1] < -1.4) {
            V[i3 + 1] = -V[i3 + 1] * 0.42; V[i3] *= 0.82; V[i3 + 2] *= 0.82;
            if (clackT <= 0 && Math.random() < 0.3) { sfx.marble([P[i3], P[i3 + 1], P[i3 + 2]]); clackT = 0.03; }
          } else { V[i3 + 1] = 0; state[i] = 3; }
        }
        if (state[i] === 3) { const f = Math.max(0, 1 - 1.8 * dt); V[i3] *= f; V[i3 + 2] *= f; }
        spin[i] += (hs / RAD) * dt;
        if (P[i3 + 1] < -200) life[i] = 0;
      }
      // roll round the axis across the direction of travel
      const hs2 = Math.hypot(V[i3], V[i3 + 2]);
      if (hs2 > 1e-3) axis.set(V[i3 + 2] / hs2, 0, -V[i3] / hs2); else axis.set(1, 0, 0);
      q.setFromAxisAngle(axis, spin[i]);
      const s = life[i] < 0.5 ? life[i] / 0.5 : 1;
      sc.set(s, s, s);
      pv.set(P[i3], P[i3 + 1], P[i3 + 2]);
      m4.compose(pv, q, sc);
      mesh.setMatrixAt(i, m4);
    }
    live = alive;
    mesh.instanceMatrix.needsUpdate = true;
  },
};
